
"""
Inventory models for SMVIA.
Includes Category, Product, Inventory, Supplier, Sale, and PurchaseOrder.
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.text import slugify
from django.utils import timezone

from apps.accounts.models import Vendor
from .base import TenantAwareModel


class Category(TenantAwareModel):
    """
    Product categories with hierarchical structure.
    
    Categories can have parent categories, allowing for nested organization:
    - Electronics
      └── Computers
          └── Laptops
              └── Gaming Laptops
    
    Each category belongs to a vendor and is isolated from other vendors.
    """
    
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120, blank=True, help_text="URL-friendly name")
    description = models.TextField(blank=True)
    
    # Self-referential foreign key for parent/child relationships
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        help_text="Parent category (null for top-level categories)"
    )
    
    # Optional image for category
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    
    # For ordering categories in lists
    sort_order = models.IntegerField(default=0)
    
    # Meta fields
    is_active = models.BooleanField(default=True)
    
    class Meta(TenantAwareModel.Meta):
        db_table = 'inventory_category'
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'
        ordering = ['sort_order', 'name']
        unique_together = ['vendor', 'slug']  # Slug unique per vendor
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        """Generate slug from name if not provided."""
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def get_full_path(self):
        """
        Get the full category path (e.g., "Electronics > Computers > Laptops")
        """
        if self.parent:
            return f"{self.parent.get_full_path()} > {self.name}"
        return self.name
    
    def get_all_products(self):
        """
        Get all products in this category and all subcategories.
        """
        from .models import Product  # Import here to avoid circular imports
        categories = [self] + list(self.get_descendants())
        return Product.objects.filter(category__in=categories)
    
    def get_descendants(self):
        """
        Get all child categories recursively.
        """
        descendants = []
        for child in self.children.all():
            descendants.append(child)
            descendants.extend(child.get_descendants())
        return descendants
    
    @property
    def level(self):
        """Get the depth level of this category (0 for top-level)."""
        level = 0
        parent = self.parent
        while parent:
            level += 1
            parent = parent.parent
        return level
    
    @property
    def product_count(self):
        """Count products in this category."""
        from .models import Product
        return Product.objects.filter(category=self).count()


# We'll add Product model in the next step

class Product(TenantAwareModel):
    """
    Product model for inventory management.
    
    Each product belongs to a vendor and can be assigned to a category.
    Products have SKU (unique per vendor), price, and other attributes.
    """
    
    # Product type choices
    PRODUCT_TYPES = (
        ('physical', 'Physical Product'),
        ('digital', 'Digital Download'),
        ('service', 'Service'),
        ('bundled', 'Bundled Product'),
    )
    
    # Basic Information
    name = models.CharField(max_length=200, db_index=True)
    sku = models.CharField(
        max_length=50,
        db_index=True,
        help_text="Stock Keeping Unit - unique per vendor"
    )
    barcode = models.CharField(
        max_length=100,
        blank=True,
        help_text="UPC, EAN, or ISBN barcode"
    )
    description = models.TextField(blank=True)
    short_description = models.CharField(max_length=255, blank=True)
    
    # Categorization
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products'
    )
    
    # Product Type
    product_type = models.CharField(
        max_length=20,
        choices=PRODUCT_TYPES,
        default='physical'
    )
    
    # Pricing (using DecimalField for precision)
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Selling price"
    )
    compare_at_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Original price for showing discounts"
    )
    cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Your cost (for profit calculations)"
    )
    
    # Tax settings
    is_taxable = models.BooleanField(default=True)
    tax_class = models.CharField(max_length=50, blank=True, default='standard')
    
    # Status flags
    is_active = models.BooleanField(default=True, db_index=True)
    is_featured = models.BooleanField(default=False)
    is_on_sale = models.BooleanField(default=False)
    
    # Media
    image = models.ImageField(
        upload_to='products/',
        blank=True,
        null=True,
        help_text="Main product image"
    )
    
    # SEO
    meta_title = models.CharField(max_length=255, blank=True)
    meta_description = models.TextField(blank=True)
    slug = models.SlugField(max_length=250, blank=True, db_index=True)
    
    # Tracking
    created_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='products_created'
    )
    updated_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='products_updated'
    )
    
    class Meta(TenantAwareModel.Meta):
        db_table = 'inventory_product'
        verbose_name = 'Product'
        verbose_name_plural = 'Products'
        unique_together = ['vendor', 'sku']  # SKU unique per vendor
        indexes = [
            models.Index(fields=['vendor', 'sku']),
            models.Index(fields=['vendor', 'is_active']),
            models.Index(fields=['vendor', 'category']),
            models.Index(fields=['name']),
        ]
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.sku})"
    
    def save(self, *args, **kwargs):
        """Generate slug and handle other pre-save logic."""
        if not self.slug and self.name:
            self.slug = slugify(self.name)
        
        # Auto-set is_on_sale based on compare_at_price
        if self.compare_at_price and self.compare_at_price > self.price:
            self.is_on_sale = True
        else:
            self.is_on_sale = False
        
        super().save(*args, **kwargs)
    
    @property
    def profit_margin(self):
        """Calculate profit margin percentage."""
        if self.cost and self.price > 0:
            profit = self.price - self.cost
            margin = (profit / self.price) * 100
            return round(margin, 2)
        return None
    
    @property
    def profit_amount(self):
        """Calculate absolute profit."""
        if self.cost:
            return self.price - self.cost
        return None
    
    @property
    def discount_percentage(self):
        """Calculate discount percentage if on sale."""
        if self.compare_at_price and self.compare_at_price > self.price:
            discount = ((self.compare_at_price - self.price) / self.compare_at_price) * 100
            return round(discount)
        return None
    
    def get_absolute_url(self):
        """Get URL for product (for future frontend)."""
        from django.urls import reverse
        return reverse('product-detail', kwargs={'slug': self.slug})
    
class Inventory(models.Model):
    """
    Inventory tracking for products.
    
    Each product has exactly one inventory record.
    Tracks quantity, reorder levels, and location.
    """
    
    product = models.OneToOneField(
        Product,
        on_delete=models.CASCADE,
        related_name='inventory',
        primary_key=True  # This makes product_id the primary key
    )
    
    # Stock levels
    quantity = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Current stock quantity"
    )
    reserved_quantity = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Quantity reserved for pending orders"
    )
    
    @property
    def available_quantity(self):
        """Get quantity available for sale."""
        return self.quantity - self.reserved_quantity
    
    # Reorder settings
    reorder_level = models.IntegerField(
        default=10,
        validators=[MinValueValidator(0)],
        help_text="Quantity at which to reorder"
    )
    reorder_quantity = models.IntegerField(
        default=0,
        help_text="Quantity to order when reordering"
    )
    
    # Location
    location = models.CharField(
        max_length=100,
        blank=True,
        help_text="Warehouse/shelf/bin location"
    )
    
    # Tracking
    last_restocked = models.DateTimeField(null=True, blank=True)
    last_counted = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'inventory_inventory'
        verbose_name = 'Inventory'
        verbose_name_plural = 'Inventories'
        indexes = [
            models.Index(fields=['quantity', 'reorder_level']),
        ]
    
    def __str__(self):
        return f"{self.product.name}: {self.quantity} units"
    
    def adjust_inventory(self, quantity_change, reason, notes="", user=None):
        """
        Adjust inventory quantity and create audit log.
        
        Args:
            quantity_change: Integer (positive for increase, negative for decrease)
            reason: String reason for change
            notes: Optional notes
            user: User making the change
        """
        from .models import InventoryLog  # Import here to avoid circular imports
        
        old_quantity = self.quantity
        new_quantity = old_quantity + quantity_change
        
        # Validate sufficient inventory for reductions
        if quantity_change < 0 and new_quantity < 0:
            raise ValueError(
                f"Insufficient inventory. Available: {old_quantity}, "
                f"Requested: {abs(quantity_change)}"
            )
        
        # Update inventory
        self.quantity = new_quantity
        if quantity_change > 0:
            self.last_restocked = timezone.now()
        self.save()
        
        # Create audit log
        InventoryLog.objects.create(
            product=self.product,
            old_quantity=old_quantity,
            new_quantity=new_quantity,
            change=quantity_change,
            reason=reason,
            notes=notes,
            created_by=user
        )
        
        # Check if we need to trigger reorder alert
        if self.available_quantity <= self.reorder_level:
            self.trigger_reorder_alert()
    
    def reserve_quantity(self, quantity):
        """Reserve quantity for an order."""
        if quantity > self.available_quantity:
            raise ValueError(f"Cannot reserve {quantity} units. Only {self.available_quantity} available.")
        self.reserved_quantity += quantity
        self.save()
    
    def release_reserved(self, quantity):
        """Release reserved quantity (e.g., order cancelled)."""
        self.reserved_quantity = max(0, self.reserved_quantity - quantity)
        self.save()
    
    def fulfill_reserved(self, quantity):
        """Fulfill reserved quantity (actual sale)."""
        if quantity > self.reserved_quantity:
            raise ValueError(f"Cannot fulfill {quantity} units. Only {self.reserved_quantity} reserved.")
        self.reserved_quantity -= quantity
        self.quantity -= quantity
        self.save()
    
    def trigger_reorder_alert(self):
        """Trigger a reorder alert (can be connected to notifications)."""
        # This could send email, create notification, etc.
        # We'll implement this later with Celery
        print(f"⚠️ LOW STOCK ALERT: {self.product.name} - Only {self.available_quantity} left!")
        return True
    
class InventoryLog(models.Model):
    """
    Audit log for all inventory changes.
    
    Tracks every adjustment to inventory for accountability.
    """
    
    REASON_CHOICES = (
        ('sale', 'Sale'),
        ('purchase', 'Purchase Order'),
        ('adjustment', 'Manual Adjustment'),
        ('return', 'Customer Return'),
        ('damage', 'Damage/Loss'),
        ('count', 'Inventory Count'),
        ('transfer', 'Stock Transfer'),
    )
    
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='inventory_logs'
    )
    
    old_quantity = models.IntegerField()
    new_quantity = models.IntegerField()
    change = models.IntegerField()
    
    reason = models.CharField(max_length=20, choices=REASON_CHOICES)
    notes = models.TextField(blank=True)
    
    # Who made the change
    created_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True
    )
    
    # When
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'inventory_inventory_log'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['product', 'created_at']),
            models.Index(fields=['reason']),
            models.Index(fields=['created_by']),
        ]
    
    def __str__(self):
        return f"{self.product.name}: {self.change} ({self.reason})"
    
    
class Supplier(TenantAwareModel):
    """
    Supplier/Vendor model for tracking product sources.
    
    Each supplier provides products and has contact information,
    payment terms, and lead times.
    """
    
    # Basic Information
    name = models.CharField(max_length=200, db_index=True)
    code = models.CharField(
        max_length=50, 
        blank=True,
        help_text="Internal supplier code"
    )
    
    # Contact Information
    contact_person = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    website = models.URLField(blank=True)
    
    # Address
    address_line1 = models.CharField(max_length=255, blank=True)
    address_line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, blank=True, default='USA')
    
    # Business Details
    tax_id = models.CharField(max_length=50, blank=True)
    payment_terms = models.CharField(
        max_length=100, 
        blank=True,
        default='Net 30',
        help_text="e.g., Net 30, Due on receipt"
    )
    
    # Lead time in days
    lead_time_days = models.IntegerField(
        default=7,
        validators=[MinValueValidator(0), MaxValueValidator(365)],
        help_text="Average days from order to delivery"
    )
    
    # Minimum order value/quantity
    minimum_order_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)]
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    is_preferred = models.BooleanField(
        default=False,
        help_text="Preferred supplier"
    )
    
    # Notes
    notes = models.TextField(blank=True)
    
    class Meta(TenantAwareModel.Meta):
        db_table = 'inventory_supplier'
        verbose_name = 'Supplier'
        verbose_name_plural = 'Suppliers'
        ordering = ['name']
        unique_together = ['vendor', 'name']  # Name unique per vendor
        indexes = [
            models.Index(fields=['vendor', 'is_active']),
            models.Index(fields=['vendor', 'is_preferred']),
        ]
    
    def __str__(self):
        return self.name
    
    @property
    def full_address(self):
        """Return formatted address."""
        parts = [
            self.address_line1,
            self.address_line2,
            f"{self.city}, {self.state} {self.postal_code}",
            self.country
        ]
        return ', '.join(filter(None, parts))
    
    @property
    def total_purchase_orders(self):
        """Get total number of purchase orders."""
        return self.purchase_orders.count()
    
    @property
    def total_spent(self):
        """Calculate total amount spent with this supplier."""
        from django.db.models import Sum
        total = self.purchase_orders.filter(
            status='received'
        ).aggregate(
            total=Sum('total_amount')
        )['total']
        return total or 0
class PurchaseOrder(TenantAwareModel):
    """
    Purchase Order model for restocking inventory.
    
    Tracks orders placed with suppliers, including status,
    expected delivery, and received items.
    """
    
    # Status choices
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('sent', 'Sent to Supplier'),
        ('confirmed', 'Confirmed by Supplier'),
        ('shipped', 'Shipped'),
        ('partial', 'Partially Received'),
        ('received', 'Fully Received'),
        ('cancelled', 'Cancelled'),
        ('on_hold', 'On Hold'),
    )
    
    # Order Information
    order_number = models.CharField(
        max_length=50,
        unique=True,
        help_text="Unique purchase order number"
    )
    
    # Relationships
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.PROTECT,  # Can't delete supplier with POs
        related_name='purchase_orders'
    )
    
    # Order Details
    order_date = models.DateTimeField(default=timezone.now)
    expected_date = models.DateTimeField(null=True, blank=True)
    received_date = models.DateTimeField(null=True, blank=True)
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        db_index=True
    )
    
    # Financial
    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )
    tax = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )
    shipping_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )
    
    # Tracking
    tracking_number = models.CharField(max_length=100, blank=True)
    carrier = models.CharField(max_length=100, blank=True)
    
    # Notes
    notes = models.TextField(blank=True)
    internal_notes = models.TextField(blank=True)
    
    # Who created/received
    created_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='purchase_orders_created'
    )
    received_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='purchase_orders_received'
    )
    
    class Meta(TenantAwareModel.Meta):
        db_table = 'inventory_purchaseorder'
        verbose_name = 'Purchase Order'
        verbose_name_plural = 'Purchase Orders'
        ordering = ['-order_date']
        indexes = [
            models.Index(fields=['vendor', 'order_number']),
            models.Index(fields=['vendor', 'status']),
            models.Index(fields=['vendor', 'supplier', 'order_date']),
        ]
    
    def __str__(self):
        return f"PO-{self.order_number} ({self.get_status_display()})"
    
    def save(self, *args, **kwargs):
        """Generate order number if not provided."""
        if not self.order_number:
            # Generate PO number: PO-YYYYMMDD-XXXX
            import random
            date_str = timezone.now().strftime('%Y%m%d')
            random_part = random.randint(1000, 9999)
            self.order_number = f"PO-{date_str}-{random_part}"
        super().save(*args, **kwargs)
    
    def calculate_totals(self):
        """Calculate subtotal and total from items."""
        from django.db.models import Sum
        from decimal import Decimal
    
        # Sum the 'total' field from all items (not 'subtotal')
        items_total = self.items.aggregate(total=Sum('total'))['total'] or Decimal('0')
        self.subtotal = items_total
    
        # Convert tax and shipping_cost to Decimal if they're strings/floats
        tax = Decimal(str(self.tax)) if self.tax else Decimal('0')
        shipping = Decimal(str(self.shipping_cost)) if self.shipping_cost else Decimal('0')
    
        self.total_amount = self.subtotal + tax + shipping
        self.save(update_fields=['subtotal', 'total_amount'])
    
    @property
    def is_fully_received(self):
        """Check if all items are received."""
        for item in self.items.all():
            if item.quantity_received < item.quantity:
                return False
        return True
    
    def receive_items(self, received_by=None):
        """Process receiving all items."""
        for item in self.items.all():
            item.receive(item.quantity)
        self.status = 'received'
        self.received_date = timezone.now()
        self.received_by = received_by
        self.save()


class PurchaseOrderItem(models.Model):
    """
    Line items for purchase orders.
    
    Tracks individual products in a purchase order,
    including quantities and prices.
    """
    
    purchase_order = models.ForeignKey(
        PurchaseOrder,
        on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name='purchase_order_items'
    )
    
    # Quantities
    quantity = models.IntegerField(validators=[MinValueValidator(1)])
    quantity_received = models.IntegerField(default=0)
    
    # Pricing
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        editable=False,
        default=0
    )
    
    class Meta:
        db_table = 'inventory_purchaseorderitem'
        unique_together = ['purchase_order', 'product']
    
    def save(self, *args, **kwargs):
        """Calculate total before saving."""
        from decimal import Decimal
        
        # Convert to Decimal for precise calculation
        quantity = Decimal(str(self.quantity))
        unit_price = Decimal(str(self.unit_price)) if self.unit_price else Decimal('0')
        
        # Calculate total
        self.total = quantity * unit_price
        
        # Save the item
        super().save(*args, **kwargs)
        
        # Update purchase order totals
        self.purchase_order.calculate_totals()
    
    def receive(self, quantity):
        """
        Receive items and update inventory.
        
        Args:
            quantity: Number of items received
        """
        if quantity > (self.quantity - self.quantity_received):
            raise ValueError(f"Cannot receive {quantity} items. Only {self.quantity - self.quantity_received} remaining.")
        
        self.quantity_received += quantity
        self.save()
        
        # Update inventory
        inventory, created = Inventory.objects.get_or_create(
            product=self.product
        )
        inventory.adjust_inventory(
            quantity,
            'purchase',
            notes=f"From PO: {self.purchase_order.order_number}",
            user=None
        )
        
        # Update PO status if needed
        po = self.purchase_order
        if po.is_fully_received:
            po.status = 'received'
            po.save()
        elif po.items.filter(quantity_received__gt=0).exists():
            po.status = 'partial'
            po.save()
    
    def __str__(self):
        return f"{self.product.name} x{self.quantity}"
    
class Sale(TenantAwareModel):
    """
    Sale transaction model.
    
    Records each sale, updates inventory, and tracks revenue.
    """
    
    # Sale status
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    )
    
    # Sale Information
    sale_number = models.CharField(
        max_length=50,
        unique=True,
        help_text="Unique sale/invoice number"
    )
    sale_date = models.DateTimeField(default=timezone.now)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='completed'
    )
    
    # Customer Information
    customer_name = models.CharField(max_length=200, blank=True)
    customer_email = models.EmailField(blank=True)
    customer_phone = models.CharField(max_length=20, blank=True)
    
    # Financial
    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )
    tax = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )
    shipping = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )
    discount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )
    total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )
    
    # Payment
    PAYMENT_METHODS = (
        ('cash', 'Cash'),
        ('card', 'Credit/Debit Card'),
        ('bank', 'Bank Transfer'),
        ('check', 'Check'),
        ('other', 'Other'),
    )
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHODS,
        default='cash'
    )
    payment_reference = models.CharField(max_length=100, blank=True)
    
    # Notes
    notes = models.TextField(blank=True)
    
    # Who processed the sale
    processed_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='sales_processed'
    )
    
    class Meta(TenantAwareModel.Meta):
        db_table = 'inventory_sale'
        verbose_name = 'Sale'
        verbose_name_plural = 'Sales'
        ordering = ['-sale_date']
        indexes = [
            models.Index(fields=['vendor', 'sale_number']),
            models.Index(fields=['vendor', 'sale_date']),
            models.Index(fields=['vendor', 'status']),
            models.Index(fields=['customer_email']),
        ]
    
    def __str__(self):
        return f"Sale-{self.sale_number} (${self.total})"
    
    def save(self, *args, **kwargs):
        """Generate sale number if not provided."""
        if not self.sale_number:
            import random
            date_str = timezone.now().strftime('%Y%m%d')
            random_part = random.randint(1000, 9999)
            self.sale_number = f"SALE-{date_str}-{random_part}"
        super().save(*args, **kwargs)
    
    def calculate_totals(self):
        """Calculate totals from items."""
        from decimal import Decimal
        from django.db.models import Sum
    
        items_total = self.items.aggregate(total=Sum('subtotal'))['total'] or Decimal('0')
        self.subtotal = items_total
    
        # Convert all to Decimal
        tax = Decimal(str(self.tax)) if self.tax else Decimal('0')
        shipping = Decimal(str(self.shipping)) if self.shipping else Decimal('0')
        discount = Decimal(str(self.discount)) if self.discount else Decimal('0')
    
        self.total = self.subtotal + tax + shipping - discount
        self.save(update_fields=['subtotal', 'total'])


class SaleItem(models.Model):
    """
    Line items for sales.
    
    Tracks individual products sold in a transaction.
    """
    
    sale = models.ForeignKey(
        Sale,
        on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name='sale_items'
    )
    
    # Quantity and pricing
    quantity = models.IntegerField(validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    discount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)]
    )
    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        editable=False,
        default=0
    )
    
    class Meta:
        db_table = 'inventory_saleitem'
    
    def save(self, *args, **kwargs):
        """Calculate subtotal before saving."""
        self.subtotal = (self.quantity * self.unit_price) - self.discount
        super().save(*args, **kwargs)
        
        # Update sale totals
        self.sale.calculate_totals()
        
        # Update inventory
        if self.sale.status == 'completed':
            inventory = self.product.inventory
            inventory.adjust_inventory(
                -self.quantity,
                'sale',
                notes=f"From sale: {self.sale.sale_number}",
                user=None
            )
    
    def __str__(self):
        
        return f"{self.product.name} x{self.quantity}"