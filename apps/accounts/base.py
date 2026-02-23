"""
Base models for tenant-aware models.
All models that belong to a vendor should inherit from these.
"""

from django.db import models
from .managers import VendorAwareManager


class TenantAwareModel(models.Model):
    """
    Abstract base model for all tenant-aware models.
    
    Provides:
    - vendor ForeignKey
    - created_at/updated_at timestamps
    - Auto-filtering manager
    """
    
    vendor = models.ForeignKey(
        'Vendor',
        on_delete=models.CASCADE,
        related_name='%(class)s_set',  # Dynamic related name
        help_text="The vendor that owns this record"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Auto-filtering manager
    objects = VendorAwareManager()
    all_objects = models.Manager()  # Unfiltered for admin use
    
    class Meta:
        abstract = True
        ordering = ['-created_at']
    
    def save(self, *args, **kwargs):
        """
        Ensure vendor is set before saving.
        
        If vendor is not set and we have a current vendor in context,
        automatically assign it.
        """
        from .middleware import get_current_vendor
        
        if not self.vendor_id:
            vendor = get_current_vendor()
            if vendor:
                self.vendor = vendor
        
        super().save(*args, **kwargs)