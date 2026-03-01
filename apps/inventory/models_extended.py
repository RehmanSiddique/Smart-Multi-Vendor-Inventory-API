"""
Extended models for advanced inventory features.
Includes: Customers, Product Variants, Warehouses, Promotions, Returns, Webhooks
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal
from apps.accounts.models import Vendor, User
from .base import TenantAwareModel
from .models import Product, Sale, Inventory


class Customer(TenantAwareModel):
    """Customer management with purchase history."""
    
    CUSTOMER_TYPES = (
        ('retail', 'Retail'),
        ('wholesale', 'Wholesale'),
        ('vip', 'VIP'),
    )
    
    name = models.CharField(max_length=200, db_index=True)
    email = models.EmailField(blank=True, db_index=True)
    phone = models.CharField(max_length=20, blank=True)
    customer_type = models.CharField(max_length=20, choices=CUSTOMER_TYPES, default='retail')
    
    # Address
    address_line1 = models.CharField(max_length=255, blank=True)
    address_line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, blank=True, default='USA')
    
    # Loyalty
    loyalty_points = models.IntegerField(default=0)
    total_spent = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_orders = models.IntegerField(default=0)
    
    # Status
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    
    class Meta(TenantAwareModel.Meta):
        db_table = 'inventory_customer'
        ordering = ['-total_spent']
        indexes = [
            models.Index(fields=['vendor', 'email']),
            models.Index(fields=['vendor', 'phone']),
        ]
    
    def __str__(self):
        return self.name


class ProductVariant(models.Model):
    """Product variants (size, color, etc.)."""
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    
    # Variant attributes
    name = models.CharField(max_length=100, help_text="e.g., 'Large Red'")
    sku = models.CharField(max_length=50, unique=True)
    barcode = models.CharField(max_length=100, blank=True)
    
    # Variant-specific pricing
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Attributes (stored as JSON)
    attributes = models.JSONField(default=dict, help_text='{"size": "L", "color": "Red"}')
    
    # Inventory
    quantity = models.IntegerField(default=0)
    
    # Status
    is_active = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'inventory_product_variant'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.product.name} - {self.name}"


class Warehouse(TenantAwareModel):
    """Multi-warehouse support."""
    
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=50, blank=True)
    
    # Address
    address_line1 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    
    # Contact
    manager_name = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    
    is_active = models.BooleanField(default=True)
    
    class Meta(TenantAwareModel.Meta):
        db_table = 'inventory_warehouse'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class WarehouseInventory(models.Model):
    """Inventory per warehouse."""
    
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='inventory_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='warehouse_inventory')
    
    quantity = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    reserved_quantity = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    location = models.CharField(max_length=100, blank=True)
    
    class Meta:
        db_table = 'inventory_warehouse_inventory'
        unique_together = ['warehouse', 'product']
    
    def __str__(self):
        return f"{self.warehouse.name} - {self.product.name}: {self.quantity}"


class Promotion(TenantAwareModel):
    """Promotions and discounts."""
    
    DISCOUNT_TYPES = (
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed Amount'),
        ('bogo', 'Buy One Get One'),
    )
    
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=50, blank=True, db_index=True)
    description = models.TextField(blank=True)
    
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPES)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Applicability
    products = models.ManyToManyField(Product, blank=True, related_name='promotions')
    min_purchase_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Validity
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    
    # Usage limits
    max_uses = models.IntegerField(null=True, blank=True)
    uses_count = models.IntegerField(default=0)
    
    is_active = models.BooleanField(default=True)
    
    class Meta(TenantAwareModel.Meta):
        db_table = 'inventory_promotion'
        ordering = ['-start_date']
    
    def __str__(self):
        return self.name
    
    def is_valid(self):
        now = timezone.now()
        return (self.is_active and 
                self.start_date <= now <= self.end_date and
                (self.max_uses is None or self.uses_count < self.max_uses))


class Return(TenantAwareModel):
    """Return/Refund management."""
    
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
    )
    
    return_number = models.CharField(max_length=50, unique=True)
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='returns')
    
    return_date = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    reason = models.TextField()
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2)
    restocked = models.BooleanField(default=False)
    
    processed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta(TenantAwareModel.Meta):
        db_table = 'inventory_return'
        ordering = ['-return_date']
    
    def __str__(self):
        return f"Return-{self.return_number}"


class ReturnItem(models.Model):
    """Items in a return."""
    
    return_order = models.ForeignKey(Return, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    
    quantity = models.IntegerField(validators=[MinValueValidator(1)])
    reason = models.CharField(max_length=200)
    
    class Meta:
        db_table = 'inventory_return_item'
    
    def __str__(self):
        return f"{self.product.name} x{self.quantity}"


class Webhook(TenantAwareModel):
    """Webhook configuration for event notifications."""
    
    EVENTS = (
        ('sale.created', 'Sale Created'),
        ('sale.completed', 'Sale Completed'),
        ('inventory.low', 'Low Stock Alert'),
        ('product.created', 'Product Created'),
        ('order.received', 'Purchase Order Received'),
    )
    
    name = models.CharField(max_length=200)
    url = models.URLField()
    events = models.JSONField(default=list, help_text='List of event types to trigger')
    
    is_active = models.BooleanField(default=True)
    secret = models.CharField(max_length=100, blank=True)
    
    # Stats
    last_triggered = models.DateTimeField(null=True, blank=True)
    success_count = models.IntegerField(default=0)
    failure_count = models.IntegerField(default=0)
    
    class Meta(TenantAwareModel.Meta):
        db_table = 'inventory_webhook'
    
    def __str__(self):
        return self.name


class ProductImage(models.Model):
    """Multiple images per product."""
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/gallery/')
    alt_text = models.CharField(max_length=200, blank=True)
    sort_order = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'inventory_product_image'
        ordering = ['sort_order']
    
    def __str__(self):
        return f"{self.product.name} - Image {self.sort_order}"


class ProductTag(TenantAwareModel):
    """Tags for products."""
    
    name = models.CharField(max_length=50)
    slug = models.SlugField(max_length=60)
    
    class Meta(TenantAwareModel.Meta):
        db_table = 'inventory_product_tag'
        unique_together = ['vendor', 'slug']
    
    def __str__(self):
        return self.name


class ProductTagRelation(models.Model):
    """Many-to-many relation for product tags."""
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='product_tags')
    tag = models.ForeignKey(ProductTag, on_delete=models.CASCADE, related_name='tagged_products')
    
    class Meta:
        db_table = 'inventory_product_tag_relation'
        unique_together = ['product', 'tag']


class AuditLog(models.Model):
    """Enhanced audit trail for all changes."""
    
    ACTION_TYPES = (
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
    )
    
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    action = models.CharField(max_length=20, choices=ACTION_TYPES)
    model_name = models.CharField(max_length=100)
    object_id = models.IntegerField()
    
    changes = models.JSONField(default=dict)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, blank=True)
    
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        db_table = 'inventory_audit_log'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['vendor', 'model_name', 'object_id']),
            models.Index(fields=['vendor', 'user', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.action} {self.model_name} by {self.user}"
