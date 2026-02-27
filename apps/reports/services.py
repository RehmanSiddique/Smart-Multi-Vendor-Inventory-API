"""
Report generation services.
These functions calculate business metrics and create reports.
"""

from decimal import Decimal
from datetime import datetime, timedelta, date
from django.db.models import Sum, Count, Avg, Q, F
from django.utils import timezone
from apps.inventory.models import Sale, SaleItem, Product, Inventory
from .models import SalesReport, InventoryValuation


class SalesReportService:
    """Service for generating sales reports."""
    
    @staticmethod
    def generate_daily_report(vendor, report_date=None):
        """Generate report for a single day."""
        if report_date is None:
            report_date = timezone.now().date()
        
        start_datetime = timezone.make_aware(datetime.combine(report_date, datetime.min.time()))
        end_datetime = start_datetime + timedelta(days=1)
        
        # Get sales for this day
        sales = Sale.objects.filter(
            vendor=vendor,
            sale_date__gte=start_datetime,
            sale_date__lt=end_datetime,
            status='completed'
        )
        
        # Calculate metrics
        total_sales = sales.count()
        total_revenue = sales.aggregate(total=Sum('total'))['total'] or Decimal('0')
        
        # Get all sale items for these sales
        sale_items = SaleItem.objects.filter(sale__in=sales)
        
        # Calculate cost and profit
        total_cost = Decimal('0')
        products_sold = 0
        
        for item in sale_items:
            total_cost += (item.quantity * item.product.cost)
            products_sold += item.quantity
        
        total_profit = total_revenue - total_cost
        
        # Get top products
        top_products_data = (
            sale_items.values('product__name', 'product__sku')
            .annotate(
                quantity=Sum('quantity'),
                revenue=Sum('subtotal')
            )
            .order_by('-quantity')[:5]
        )
        
        top_products = []
        for item in top_products_data:
            top_products.append({
                'name': item['product__name'],
                'sku': item['product__sku'],
                'quantity': item['quantity'],
                'revenue': float(item['revenue'])
            })
        
        # Get unique customers
        unique_customers = sales.exclude(customer_email='').values('customer_email').distinct().count()
        
        # Calculate average order value
        avg_order = total_revenue / total_sales if total_sales > 0 else 0
        
        # Create or update report
        report, created = SalesReport.objects.update_or_create(
            vendor=vendor,
            period='daily',
            start_date=report_date,
            end_date=report_date,
            defaults={
                'total_sales': total_sales,
                'total_revenue': total_revenue,
                'total_cost': total_cost,
                'total_profit': total_profit,
                'average_order_value': avg_order,
                'top_products': {'items': top_products},
                'products_sold': products_sold,
                'unique_customers': unique_customers,
                'is_final': report_date < timezone.now().date(),
            }
        )
        
        return report
    
    @staticmethod
    def generate_date_range_report(vendor, start_date, end_date, period='custom'):
        """Generate report for a date range (weekly/monthly/custom)."""
        
        start_datetime = timezone.make_aware(datetime.combine(start_date, datetime.min.time()))
        end_datetime = timezone.make_aware(datetime.combine(end_date + timedelta(days=1), datetime.min.time()))
        
        # Get sales in range
        sales = Sale.objects.filter(
            vendor=vendor,
            sale_date__gte=start_datetime,
            sale_date__lt=end_datetime,
            status='completed'
        )
        
        # Calculate metrics (similar to daily but aggregated)
        total_sales = sales.count()
        total_revenue = sales.aggregate(total=Sum('total'))['total'] or Decimal('0')
        
        sale_items = SaleItem.objects.filter(sale__in=sales)
        
        total_cost = sum(item.quantity * item.product.cost for item in sale_items)
        products_sold = sale_items.aggregate(total=Sum('quantity'))['total'] or 0
        
        total_profit = total_revenue - Decimal(str(total_cost))
        
        # Group by day for trend
        daily_trend = []
        current = start_date
        while current <= end_date:
            day_start = timezone.make_aware(datetime.combine(current, datetime.min.time()))
            day_end = day_start + timedelta(days=1)
            day_sales = sales.filter(sale_date__gte=day_start, sale_date__lt=day_end)
            day_revenue = day_sales.aggregate(total=Sum('total'))['total'] or 0
            daily_trend.append({
                'date': current.strftime('%Y-%m-%d'),
                'revenue': float(day_revenue),
                'orders': day_sales.count()
            })
            current += timedelta(days=1)
        
        # Map period string
        period_map = {
            7: 'weekly',
            30: 'monthly',
            90: 'quarterly',
            365: 'yearly'
        }
        period_type = period_map.get((end_date - start_date).days, 'custom')
        
        # Create report
        report, _ = SalesReport.objects.update_or_create(
            vendor=vendor,
            period=period_type,
            start_date=start_date,
            end_date=end_date,
            defaults={
                'total_sales': total_sales,
                'total_revenue': total_revenue,
                'total_cost': Decimal(str(total_cost)),
                'total_profit': total_profit,
                'products_sold': products_sold,
                'is_final': end_date < timezone.now().date(),
            }
        )
        
        # Add trend data as JSON
        report.top_products = {'trend': daily_trend}
        report.save()
        
        return report


class InventoryValuationService:
    """Service for inventory valuation."""
    
    @staticmethod
    def generate_valuation(vendor, valuation_date=None):
        """Generate inventory valuation snapshot."""
        if valuation_date is None:
            valuation_date = timezone.now().date()
        
        # Get all active products
        products = Product.objects.filter(vendor=vendor, is_active=True)
        
        total_items = 0
        value_at_cost = Decimal('0')
        value_at_retail = Decimal('0')
        low_stock = 0
        out_of_stock = 0
        
        category_breakdown = {}
        
        for product in products:
            try:
                inventory = product.inventory
                quantity = inventory.quantity
                
                if quantity > 0:
                    total_items += quantity
                    value_at_cost += quantity * product.cost
                    value_at_retail += quantity * product.price
                    
                    # Category breakdown
                    cat_name = product.category.name if product.category else 'Uncategorized'
                    if cat_name not in category_breakdown:
                        category_breakdown[cat_name] = {
                            'items': 0,
                            'value': 0
                        }
                    category_breakdown[cat_name]['items'] += quantity
                    category_breakdown[cat_name]['value'] += float(quantity * product.price)
                
                # Stock status
                if quantity <= inventory.reorder_level:
                    low_stock += 1
                if quantity == 0:
                    out_of_stock += 1
                    
            except Inventory.DoesNotExist:
                pass
        
        potential_profit = value_at_retail - value_at_cost
        
        # Create valuation record
        valuation, _ = InventoryValuation.objects.update_or_create(
            vendor=vendor,
            date=valuation_date,
            defaults={
                'total_items': total_items,
                'total_products': products.count(),
                'value_at_cost': value_at_cost,
                'value_at_retail': value_at_retail,
                'potential_profit': potential_profit,
                'low_stock_count': low_stock,
                'out_of_stock_count': out_of_stock,
                'by_category': category_breakdown,
            }
        )
        
        return valuation