"""
Django Signals for real-time alerts and notifications.
Signals trigger automatically when models change and create
Notification records in the database.
"""

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.conf import settings
from .models import Inventory, Sale, PurchaseOrder, Product, Notification


def create_notification(vendor, title, message, notification_type='info',
                        priority='medium', user=None, action_url='',
                        icon='🔔', related_type='', related_id=None):
    """Helper to create a notification record."""
    try:
        Notification.all_objects.create(
            vendor=vendor,
            title=title,
            message=message,
            notification_type=notification_type,
            priority=priority,
            user=user,
            action_url=action_url,
            icon=icon,
            related_object_type=related_type,
            related_object_id=related_id,
        )
    except Exception as e:
        print(f"[NOTIFICATION ERROR] Failed to create notification: {e}")


@receiver(post_save, sender=Inventory)
def check_low_stock(sender, instance, created, **kwargs):
    """
    When inventory is updated, check if stock is low.
    If yes, create a low stock notification.
    """
    if instance.quantity <= instance.reorder_level:
        product = instance.product
        vendor = product.vendor
        
        # Avoid duplicate notifications for the same product in the last hour
        from django.utils import timezone
        from datetime import timedelta
        one_hour_ago = timezone.now() - timedelta(hours=1)
        
        existing = Notification.all_objects.filter(
            vendor=vendor,
            notification_type='low_stock',
            related_object_type='product',
            related_object_id=product.id,
            created_at__gte=one_hour_ago
        ).exists()
        
        if not existing:
            create_notification(
                vendor=vendor,
                title=f"Low stock alert: {product.sku}",
                message=f"{product.name} only has {instance.quantity} units remaining. Reorder level is {instance.reorder_level}.",
                notification_type='low_stock',
                priority='high',
                action_url='/inventory',
                icon='⚠️',
                related_type='product',
                related_id=product.id,
            )


@receiver(post_save, sender=Sale)
def sale_created(sender, instance, created, **kwargs):
    """
    When a new sale is created, create a notification.
    """
    if created:
        vendor = instance.vendor
        
        # Large sale alert
        if instance.total and instance.total > 1000:
            create_notification(
                vendor=vendor,
                title=f"Large sale: ${instance.total}",
                message=f"Sale {instance.sale_number} completed for ${instance.total} via {instance.get_payment_method_display()}.",
                notification_type='sale_large',
                priority='high',
                action_url='/sales',
                icon='💰',
                related_type='sale',
                related_id=instance.id,
            )
        else:
            create_notification(
                vendor=vendor,
                title=f"Sale {instance.sale_number} completed",
                message=f"New sale of ${instance.total} recorded{' for ' + instance.customer_name if instance.customer_name else ''}.",
                notification_type='sale_created',
                priority='low',
                action_url='/sales',
                icon='🛒',
                related_type='sale',
                related_id=instance.id,
            )


@receiver(post_save, sender=PurchaseOrder)
def purchase_order_status_changed(sender, instance, created, **kwargs):
    """
    Notify when purchase order is created or status changes.
    """
    vendor = instance.vendor
    
    if created:
        create_notification(
            vendor=vendor,
            title=f"PO {instance.order_number} created",
            message=f"New purchase order created for supplier {instance.supplier.name if instance.supplier else 'Unknown'}.",
            notification_type='po_created',
            priority='medium',
            action_url='/purchase-orders',
            icon='📋',
            related_type='purchase_order',
            related_id=instance.id,
        )
    else:
        if instance.status == 'received':
            create_notification(
                vendor=vendor,
                title=f"PO {instance.order_number} received",
                message=f"Purchase order {instance.order_number} has been fully received.",
                notification_type='po_received',
                priority='medium',
                action_url='/purchase-orders',
                icon='📦',
                related_type='purchase_order',
                related_id=instance.id,
            )
        elif instance.status == 'shipped':
            create_notification(
                vendor=vendor,
                title=f"PO {instance.order_number} shipped",
                message=f"Purchase order {instance.order_number} has been shipped by the supplier.",
                notification_type='po_status',
                priority='medium',
                action_url='/purchase-orders',
                icon='🚚',
                related_type='purchase_order',
                related_id=instance.id,
            )


@receiver(post_save, sender=Product)
def product_created(sender, instance, created, **kwargs):
    """
    Notify when a new product is created.
    """
    if created:
        vendor = instance.vendor
        create_notification(
            vendor=vendor,
            title=f"New product: {instance.name}",
            message=f"Product '{instance.name}' (SKU: {instance.sku}) has been added to the catalog.",
            notification_type='product_created',
            priority='low',
            action_url='/products',
            icon='📦',
            related_type='product',
            related_id=instance.id,
        )