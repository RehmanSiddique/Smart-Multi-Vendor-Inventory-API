"""
Analytics service for dashboard metrics and business intelligence.
"""

from django.db.models import Sum, Count, Avg, F, Q
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from .models import Product, Sale, SaleItem, Inventory, PurchaseOrder
from .models_extended import Customer


class AnalyticsService:
    """Service for calculating business metrics."""
    
    def __init__(self, vendor):
        self.vendor = vendor
    
    def get_dashboard_metrics(self, days=30):
        """Get key metrics for dashboard."""
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        # Sales metrics
        sales = Sale.objects.filter(
            vendor=self.vendor,
            sale_date__gte=start_date,
            status='completed'
        )
        
        total_revenue = sales.aggregate(total=Sum('total'))['total'] or Decimal('0')
        total_orders = sales.count()
        avg_order_value = total_revenue / total_orders if total_orders > 0 else Decimal('0')
        
        # Calculate profit
        sale_items = SaleItem.objects.filter(
            sale__vendor=self.vendor,
            sale__sale_date__gte=start_date,
            sale__status='completed'
        ).select_related('product')
        
        total_cost = sum(
            (item.product.cost or Decimal('0')) * item.quantity 
            for item in sale_items
        )
        total_profit = total_revenue - total_cost
        
        # Inventory metrics
        low_stock = Inventory.objects.filter(
            product__vendor=self.vendor,
            quantity__lte=F('reorder_level')
        ).count()
        
        out_of_stock = Inventory.objects.filter(
            product__vendor=self.vendor,
            quantity=0
        ).count()
        
        # Top products
        top_products = SaleItem.objects.filter(
            sale__vendor=self.vendor,
            sale__sale_date__gte=start_date,
            sale__status='completed'
        ).values('product__name').annotate(
            total_sold=Sum('quantity'),
            revenue=Sum(F('quantity') * F('unit_price'))
        ).order_by('-revenue')[:5]
        
        return {
            'period_days': days,
            'total_revenue': float(total_revenue),
            'total_orders': total_orders,
            'avg_order_value': float(avg_order_value),
            'total_profit': float(total_profit),
            'profit_margin': float((total_profit / total_revenue * 100) if total_revenue > 0 else 0),
            'low_stock_count': low_stock,
            'out_of_stock_count': out_of_stock,
            'top_products': list(top_products)
        }
    
    def get_sales_trend(self, days=30):
        """Get daily sales trend."""
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        sales = Sale.objects.filter(
            vendor=self.vendor,
            sale_date__gte=start_date,
            status='completed'
        ).extra(
            select={'day': 'DATE(sale_date)'}
        ).values('day').annotate(
            revenue=Sum('total'),
            orders=Count('id')
        ).order_by('day')
        
        return list(sales)
    
    def get_top_customers(self, limit=10):
        """Get top customers by spending."""
        customers = Customer.objects.filter(
            vendor=self.vendor,
            is_active=True
        ).order_by('-total_spent')[:limit]
        
        return [{
            'id': c.id,
            'name': c.name,
            'email': c.email,
            'total_spent': float(c.total_spent),
            'total_orders': c.total_orders,
            'loyalty_points': c.loyalty_points
        } for c in customers]
    
    def get_inventory_valuation(self):
        """Calculate total inventory value."""
        products = Product.objects.filter(
            vendor=self.vendor,
            is_active=True
        ).select_related('inventory')
        
        total_items = 0
        value_at_cost = Decimal('0')
        value_at_retail = Decimal('0')
        
        for product in products:
            try:
                qty = product.inventory.quantity
                total_items += qty
                value_at_cost += (product.cost or Decimal('0')) * qty
                value_at_retail += product.price * qty
            except Inventory.DoesNotExist:
                pass
        
        return {
            'total_items': total_items,
            'total_products': products.count(),
            'value_at_cost': float(value_at_cost),
            'value_at_retail': float(value_at_retail),
            'potential_profit': float(value_at_retail - value_at_cost)
        }
    
    def get_category_performance(self, days=30):
        """Sales performance by category."""
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        category_sales = SaleItem.objects.filter(
            sale__vendor=self.vendor,
            sale__sale_date__gte=start_date,
            sale__status='completed',
            product__category__isnull=False
        ).values('product__category__name').annotate(
            revenue=Sum(F('quantity') * F('unit_price')),
            units_sold=Sum('quantity')
        ).order_by('-revenue')
        
        return list(category_sales)
    
    def get_supplier_performance(self):
        """Supplier performance metrics."""
        from .models import Supplier
        
        suppliers = Supplier.objects.filter(
            vendor=self.vendor,
            is_active=True
        ).annotate(
            total_pos=Count('purchase_orders'),
            total_spent=Sum('purchase_orders__total_amount', filter=Q(purchase_orders__status='received'))
        ).order_by('-total_spent')
        
        return [{
            'id': s.id,
            'name': s.name,
            'total_purchase_orders': s.total_pos,
            'total_spent': float(s.total_spent or 0),
            'lead_time_days': s.lead_time_days
        } for s in suppliers]
