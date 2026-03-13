"""
Extended models for SMVIA - Customer, Warehouse, Promotion, etc.
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal

from apps.accounts.models import Vendor
from .base import TenantAwareModel


class Customer(TenantAwareModel):
    """Customer model for tracking buyers."""
    
    CUSTOMER_TYPES = (
        ('retail', 'Retail'),
        ('wholesale', 'Wholesale'),
        ('vip', 'VIP'),
    )
    
    name = models.CharField(max_length=200, db_index=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    customer_type = models.CharField(max_length=20, choices=CUSTOMER_TYPES, default='retail')
    
    # Address
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, blank=True, default='USA')
    
    # Business
    company = models.CharField(max_length=200, blank=True)
    tax_id = models.CharField(max_length=50, blank=True)
    
    # Loyalty
    loyalty_points = models.IntegerField(default=0)
    total_spent = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    
    class Meta(TenantAwareModel.Meta):
        db_table = 'inventory_customer'
        ordering = ['name']
        unique_together = ['vendor', 'email']
    
    def __str__(self):
        return self.name


class Warehouse(TenantAwareModel):
    """Warehouse/location model for inventory management."""
    
    name = models.CharField(max_length=200, db_index=True)
    code = models.CharField(max_length=50, blank=True)
    
    # Location
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, blank=True, default='USA')
    
    # Contact
    manager = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    
    class Meta(TenantAwareModel.Meta):
        db_table = 'inventory_warehouse'
        ordering = ['name']
        unique_together = ['vendor', 'code']
    
    def __str__(self):
        return self.name


class Promotion(TenantAwareModel):
    """Promotion/discount model."""
    
    DISCOUNT_TYPES = (
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed Amount'),
        ('bogo', 'Buy One Get One'),
    )
    
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=50, blank=True)
    description = models.TextField(blank=True)
    
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPES, default='percentage')
    discount_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    
    # Validity
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    
    # Limits
    minimum_purchase = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)]
    )
    usage_limit = models.IntegerField(null=True, blank=True)
    usage_count = models.IntegerField(default=0)
    
    is_active = models.BooleanField(default=True)
    
    class Meta(TenantAwareModel.Meta):
        db_table = 'inventory_promotion'
        ordering = ['-start_date']
        unique_together = ['vendor', 'code']
    
    def __str__(self):
        return self.name
    
    def is_valid(self):
        """Check if promotion is currently valid."""
        now = timezone.now()
        if not self.is_active:
            return False
        if now < self.start_date or now > self.end_date:
            return False
        if self.usage_limit and self.usage_count >= self.usage_limit:
            return False
        return True
