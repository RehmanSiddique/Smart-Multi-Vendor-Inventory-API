"""
Celery tasks for automated inventory operations.
"""

from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from .models import Product, Inventory, PurchaseOrder
from .models_extended import Customer
from .notifications import NotificationService
from apps.accounts.models import Vendor


@shared_task
def check_low_stock_alerts():
    """Check for low stock and send alerts."""
    vendors = Vendor.objects.filter(is_active=True)
    
    for vendor in vendors:
        low_stock_products = Product.objects.filter(
            vendor=vendor,
            is_active=True,
            inventory__quantity__lte=models.F('inventory__reorder_level')
        ).select_related('inventory')
        
        for product in low_stock_products:
            NotificationService.send_low_stock_alert(product, vendor)


@shared_task
def auto_create_purchase_orders():
    """Automatically create POs for low stock items."""
    from .models import Supplier
    
    vendors = Vendor.objects.filter(is_active=True)
    
    for vendor in vendors:
        low_stock = Product.objects.filter(
            vendor=vendor,
            is_active=True,
            inventory__quantity__lte=models.F('inventory__reorder_level'),
            inventory__reorder_quantity__gt=0
        ).select_related('inventory')
        
        # Group by supplier (simplified - assumes product has supplier field)
        # In real implementation, you'd need a product-supplier relationship
        for product in low_stock:
            # Create PO logic here
            pass


@shared_task
def update_customer_metrics():
    """Update customer total_spent and total_orders."""
    from .models import Sale
    from django.db.models import Sum, Count
    
    customers = Customer.objects.all()
    
    for customer in customers:
        sales = Sale.objects.filter(
            vendor=customer.vendor,
            customer_email=customer.email,
            status='completed'
        )
        
        metrics = sales.aggregate(
            total_spent=Sum('total'),
            total_orders=Count('id')
        )
        
        customer.total_spent = metrics['total_spent'] or 0
        customer.total_orders = metrics['total_orders'] or 0
        customer.save()


@shared_task
def generate_daily_reports():
    """Generate daily sales reports."""
    from apps.reports.models import SalesReport
    from django.db.models import Sum, Count, Avg
    from decimal import Decimal
    
    yesterday = timezone.now().date() - timedelta(days=1)
    vendors = Vendor.objects.filter(is_active=True)
    
    for vendor in vendors:
        from .models import Sale
        
        sales = Sale.objects.filter(
            vendor=vendor,
            sale_date__date=yesterday,
            status='completed'
        )
        
        metrics = sales.aggregate(
            total_sales=Count('id'),
            total_revenue=Sum('total'),
            avg_order=Avg('total')
        )
        
        SalesReport.objects.update_or_create(
            vendor=vendor,
            period='daily',
            start_date=yesterday,
            end_date=yesterday,
            defaults={
                'total_sales': metrics['total_sales'] or 0,
                'total_revenue': metrics['total_revenue'] or Decimal('0'),
                'average_order_value': metrics['avg_order'] or Decimal('0'),
                'is_final': True
            }
        )


@shared_task
def cleanup_old_audit_logs(days=90):
    """Delete audit logs older than specified days."""
    from .models_extended import AuditLog
    
    cutoff_date = timezone.now() - timedelta(days=days)
    deleted = AuditLog.objects.filter(timestamp__lt=cutoff_date).delete()
    
    return f"Deleted {deleted[0]} old audit logs"


@shared_task
def send_scheduled_reports():
    """Send scheduled reports to users."""
    from apps.reports.models import ReportSchedule
    
    now = timezone.now()
    
    schedules = ReportSchedule.objects.filter(
        is_active=True,
        next_send__lte=now
    )
    
    for schedule in schedules:
        # Generate and send report
        # Implementation depends on report type
        
        # Update next_send based on frequency
        if schedule.frequency == 'daily':
            schedule.next_send = now + timedelta(days=1)
        elif schedule.frequency == 'weekly':
            schedule.next_send = now + timedelta(weeks=1)
        elif schedule.frequency == 'monthly':
            schedule.next_send = now + timedelta(days=30)
        
        schedule.last_sent = now
        schedule.save()


from django.db import models
