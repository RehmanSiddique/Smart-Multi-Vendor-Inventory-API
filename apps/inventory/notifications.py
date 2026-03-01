"""
Notification service for alerts and webhooks.
"""

import requests
import hashlib
import hmac
from django.core.mail import send_mail
from django.conf import settings
from .models_extended import Webhook


class NotificationService:
    """Service for sending notifications."""
    
    @staticmethod
    def send_low_stock_alert(product, vendor):
        """Send low stock alert email."""
        subject = f"Low Stock Alert: {product.name}"
        message = f"""
        Product: {product.name}
        SKU: {product.sku}
        Current Stock: {product.inventory.quantity}
        Reorder Level: {product.inventory.reorder_level}
        
        Please reorder this product soon.
        """
        
        # Get vendor admin emails
        admin_emails = vendor.users.filter(
            role__in=['admin', 'manager']
        ).values_list('email', flat=True)
        
        if admin_emails:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                list(admin_emails),
                fail_silently=True
            )
    
    @staticmethod
    def send_sale_notification(sale):
        """Send sale confirmation email."""
        if not sale.customer_email:
            return
        
        subject = f"Order Confirmation - {sale.sale_number}"
        message = f"""
        Thank you for your order!
        
        Order Number: {sale.sale_number}
        Date: {sale.sale_date.strftime('%Y-%m-%d %H:%M')}
        Total: ${sale.total}
        
        Your order has been received and is being processed.
        """
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [sale.customer_email],
            fail_silently=True
        )
    
    @staticmethod
    def trigger_webhooks(event_type, data, vendor):
        """Trigger webhooks for an event."""
        webhooks = Webhook.objects.filter(
            vendor=vendor,
            is_active=True
        )
        
        for webhook in webhooks:
            if event_type in webhook.events:
                try:
                    # Create signature
                    signature = ''
                    if webhook.secret:
                        signature = hmac.new(
                            webhook.secret.encode(),
                            str(data).encode(),
                            hashlib.sha256
                        ).hexdigest()
                    
                    # Send webhook
                    headers = {
                        'Content-Type': 'application/json',
                        'X-Webhook-Signature': signature,
                        'X-Event-Type': event_type
                    }
                    
                    response = requests.post(
                        webhook.url,
                        json=data,
                        headers=headers,
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        webhook.success_count += 1
                    else:
                        webhook.failure_count += 1
                    
                    webhook.last_triggered = timezone.now()
                    webhook.save()
                
                except Exception as e:
                    webhook.failure_count += 1
                    webhook.save()
    
    @staticmethod
    def send_purchase_order_email(purchase_order):
        """Send PO to supplier."""
        if not purchase_order.supplier.email:
            return
        
        subject = f"Purchase Order - {purchase_order.order_number}"
        message = f"""
        Purchase Order: {purchase_order.order_number}
        Date: {purchase_order.order_date.strftime('%Y-%m-%d')}
        Expected Delivery: {purchase_order.expected_date.strftime('%Y-%m-%d') if purchase_order.expected_date else 'TBD'}
        
        Total Amount: ${purchase_order.total_amount}
        
        Please confirm receipt of this order.
        """
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [purchase_order.supplier.email],
            fail_silently=True
        )


from django.utils import timezone
