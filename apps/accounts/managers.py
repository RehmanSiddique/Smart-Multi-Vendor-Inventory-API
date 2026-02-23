# """
# Custom model managers for multi-tenancy support.
# These managers automatically scope queries to the current vendor.
# """

# from django.db import models
# from .middleware import get_current_vendor


# class VendorAwareManager(models.Manager):
#     """
#     Manager that automatically filters all queries by the current vendor.
    
#     This is the core of our multi-tenancy implementation.
#     Any model that belongs to a vendor should use this manager.
    
#     Example:
#         class Product(models.Model):
#             vendor = models.ForeignKey(Vendor)
#             name = models.CharField(max_length=100)
            
#             objects = VendorAwareManager()  # Auto-filtered
#             all_objects = models.Manager()  # Unfiltered (admin only)
#     """
    
#     def get_queryset(self):
#         """
#         Get the base queryset, filtered by current vendor.
        
#         This method is called for every query: .all(), .filter(), .get(), etc.
#         """
#         qs = super().get_queryset()
        
#         # Get the current vendor from thread-local storage
#         vendor = get_current_vendor()
        
#         if vendor:
#             # Filter by vendor - assumes model has a 'vendor' ForeignKey
#             return qs.filter(vendor=vendor)
        
#         # No vendor context - return empty queryset for safety
#         # This prevents accidental cross-tenant data access
#         # For example, if someone runs Product.objects.all() without tenant context
#         return qs.none()
    
#     def all_without_tenant(self):
#         """
#         Bypass tenant filtering.
        
#         This should ONLY be used by platform admins or in specific circumstances.
#         Regular code should never call this.
#         """
#         return super().get_queryset()


# class VendorManager(models.Manager):
#     """
#     Special manager for the Vendor model itself.
    
#     Since Vendor is the tenant, we don't filter it by tenant.
#     Instead, we provide helper methods for vendor lookup.
#     """
    
#     def get_by_subdomain(self, subdomain):
#         """
#         Get vendor by subdomain with caching.
        
#         This is used by the tenant middleware.
#         """
#         return self.get_queryset().filter(subdomain=subdomain, is_active=True).first()
    
#     def get_by_request(self, request):
#         """
#         Extract vendor from request using multiple methods.
        
#         This consolidates the logic from middleware for use elsewhere.
#         """
#         # Try subdomain first
#         host = request.get_host().split(':')[0]
#         parts = host.split('.')
        
#         if len(parts) >= 2 and parts[0] not in ['www', 'api', 'localhost', '127']:
#             vendor = self.get_by_subdomain(parts[0])
#             if vendor:
#                 return vendor
        
#         # Try header
#         vendor_id = request.headers.get('X-Tenant-ID')
#         if vendor_id:
#             try:
#                 return self.get_queryset().filter(id=int(vendor_id), is_active=True).first()
#             except (ValueError, TypeError):
#                 pass
        
#         return None
    
#     def get_active_vendors(self):
#         """Get all active vendors."""
#         return self.get_queryset().filter(is_active=True)


# class TenantAwareManager(models.Manager):
#     """
#     Abstract base manager for tenant-aware models.
    
#     This can be used for models that have a tenant but use a different
#     field name (e.g., 'tenant' instead of 'vendor').
#     """
    
#     def __init__(self, tenant_field='vendor'):
#         self.tenant_field = tenant_field
#         super().__init__()
    
#     def get_queryset(self):
#         qs = super().get_queryset()
#         vendor = get_current_vendor()
        
#         if vendor:
#             # Use the specified field name for filtering
#             filter_kwargs = {self.tenant_field: vendor}
#             return qs.filter(**filter_kwargs)
        
#         return qs.none()


"""
Custom model managers for multi-tenancy support.
These managers automatically scope queries to the current vendor.
"""

from django.db import models
from django.contrib.auth.models import BaseUserManager
from .middleware import get_current_vendor


class UserManager(BaseUserManager, models.Manager):
    """
    Custom manager for the User model.
    
    This manager:
    1. Provides create_user and create_superuser methods
    2. Auto-filters by vendor when needed
    3. Handles our custom User fields
    """
    
    def get_queryset(self):
        """
        Auto-filter by current vendor, except for platform admins.
        """
        qs = super().get_queryset()
        vendor = get_current_vendor()
        
        if vendor:
            # Filter by vendor - but don't filter platform admins out
            # Platform admins might need to see all users
            return qs.filter(vendor=vendor)
        
        # No vendor context - return all (for platform admin use)
        return qs
    
    def create_user(self, email, password=None, **extra_fields):
        """
        Create and save a regular user.
        
        This method is required by Django's authentication system.
        """
        if not email:
            raise ValueError('The Email field must be set')
        
        # Normalize email (convert to lowercase)
        email = self.normalize_email(email)
        
        # Set default values for regular users
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        extra_fields.setdefault('is_active', True)  # We'll change this after email verification
        
        # Create the user
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        """
        Create and save a superuser (platform admin).
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('role', 'platform_admin')
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(email, password, **extra_fields)
    
    def all_without_tenant(self):
        """
        Bypass tenant filtering for admin operations.
        """
        return super().get_queryset()


class VendorAwareManager(models.Manager):
    """
    Manager that automatically filters all queries by the current vendor.
    
    This is the core of our multi-tenancy implementation.
    Any model that belongs to a vendor should use this manager.
    
    Example:
        class Product(models.Model):
            vendor = models.ForeignKey(Vendor)
            name = models.CharField(max_length=100)
            
            objects = VendorAwareManager()  # Auto-filtered
            all_objects = models.Manager()  # Unfiltered (admin only)
    """
    
    def get_queryset(self):
        """
        Get the base queryset, filtered by current vendor.
        
        This method is called for every query: .all(), .filter(), .get(), etc.
        """
        qs = super().get_queryset()
        
        # Get the current vendor from thread-local storage
        vendor = get_current_vendor()
        
        if vendor:
            # Filter by vendor - assumes model has a 'vendor' ForeignKey
            return qs.filter(vendor=vendor)
        
        # No vendor context - return empty queryset for safety
        # This prevents accidental cross-tenant data access
        # For example, if someone runs Product.objects.all() without tenant context
        return qs.none()
    
    def all_without_tenant(self):
        """
        Bypass tenant filtering.
        
        This should ONLY be used by platform admins or in specific circumstances.
        Regular code should never call this.
        """
        return super().get_queryset()


class VendorManager(models.Manager):
    """
    Special manager for the Vendor model itself.
    
    Since Vendor is the tenant, we don't filter it by tenant.
    Instead, we provide helper methods for vendor lookup.
    """
    
    def get_by_subdomain(self, subdomain):
        """
        Get vendor by subdomain with caching.
        
        This is used by the tenant middleware.
        """
        return self.get_queryset().filter(subdomain=subdomain, is_active=True).first()
    
    def get_by_request(self, request):
        """
        Extract vendor from request using multiple methods.
        
        This consolidates the logic from middleware for use elsewhere.
        """
        # Try subdomain first
        host = request.get_host().split(':')[0]
        parts = host.split('.')
        
        if len(parts) >= 2 and parts[0] not in ['www', 'api', 'localhost', '127']:
            vendor = self.get_by_subdomain(parts[0])
            if vendor:
                return vendor
        
        # Try header
        vendor_id = request.headers.get('X-Tenant-ID')
        if vendor_id:
            try:
                return self.get_queryset().filter(id=int(vendor_id), is_active=True).first()
            except (ValueError, TypeError):
                pass
        
        return None
    
    def get_active_vendors(self):
        """Get all active vendors."""
        return self.get_queryset().filter(is_active=True)


class TenantAwareManager(models.Manager):
    """
    Abstract base manager for tenant-aware models.
    
    This can be used for models that have a tenant but use a different
    field name (e.g., 'tenant' instead of 'vendor').
    """
    
    def __init__(self, tenant_field='vendor'):
        self.tenant_field = tenant_field
        super().__init__()
    
    def get_queryset(self):
        qs = super().get_queryset()
        vendor = get_current_vendor()
        
        if vendor:
            # Use the specified field name for filtering
            filter_kwargs = {self.tenant_field: vendor}
            return qs.filter(**filter_kwargs)
        
        return qs.none()