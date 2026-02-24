"""
Base models for inventory app.
All inventory models inherit from these to ensure tenant isolation.
"""

from django.db import models
from apps.accounts.models import Vendor
from apps.accounts.middleware import get_current_vendor
from apps.accounts.managers import VendorAwareManager


class TenantAwareModel(models.Model):
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Add this line to ensure auto-filtering!
    objects = VendorAwareManager()
    all_objects = models.Manager()
    
    class Meta:
        abstract = True
    
    def save(self, *args, **kwargs):
        if not self.vendor_id:
            vendor = get_current_vendor()
            if vendor:
                self.vendor = vendor
            else:
                raise ValueError("Cannot save tenant-aware model without vendor")
        super().save(*args, **kwargs)
        
    def delete(self, *args, **kwargs):
        self.vendor = None
        self.save()
        super().delete(*args, **kwargs)