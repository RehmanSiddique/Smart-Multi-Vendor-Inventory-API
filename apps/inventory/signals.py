"""
Django Signals for real-time alerts and notifications.
Signals trigger automatically when models change.
"""

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from .models import Inventory, Sale, PurchaseOrder


@receiver(post_save, sender=Inventory)
def check_low_stock(sender, instance, created, **kwargs):
    """
    When inventory is updated, check if stock is low.
    If yes, trigger an alert.
    """
    if instance.quantity <= instance.reorder_level:
        # This is a low stock situation
        product = instance.product
        vendor = product.vendor
        
        # Get vendor admin emails
        admin_emails = vendor.users.filter(
            role__in=['vendor_admin', 'vendor_staff']
        ).values_list('email', flat=True)
        
        if admin_emails:
            # In a real app, you'd use Celery for this
            # For now, we'll just print
            print(f"🔔 LOW STOCK ALERT: {product.name} only has {instance.quantity} units!")
            
            # You could send email here
            # send_mail(
            #     subject=f"Low Stock Alert: {product.name}",
            #     message=f"Only {instance.quantity} units remaining. Reorder level is {instance.reorder_level}.",
            #     from_email=settings.DEFAULT_FROM_EMAIL,
            #     recipient_list=list(admin_emails),
            #     fail_silently=True,
            # )


@receiver(post_save, sender=Sale)
def sale_created(sender, instance, created, **kwargs):
    """
    When a new sale is created, log it and maybe send notification.
    """
    if created:
        print(f"💰 New sale: {instance.sale_number} for ${instance.total}")
        
        # Check if this is a large sale (e.g., > $1000)
        if instance.total > 1000:
            print(f"🎉 LARGE SALE ALERT: ${instance.total}!")


@receiver(post_save, sender=PurchaseOrder)
def purchase_order_status_changed(sender, instance, created, **kwargs):
    """
    Notify when purchase order status changes.
    """
    if not created and instance.tracker.has_changed('status'):
        old_status = instance.tracker.previous('status')
        new_status = instance.status
        
        print(f"📦 PO {instance.order_number} changed from {old_status} to {new_status}")
        
        # If received, celebrate!
        if new_status == 'received':
            print(f"✅ PO {instance.order_number} fully received!")