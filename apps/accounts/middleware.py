"""
Tenant Middleware for Multi-Tenancy Support.

This middleware identifies which vendor (tenant) is making the request
and makes that information available throughout the application.
"""

import threading
from django.utils.deprecation import MiddlewareMixin
from django.core.exceptions import ImproperlyConfigured

# Thread-local storage to hold the current vendor
# This allows us to access the vendor from anywhere in the code
_thread_locals = threading.local()

def get_current_vendor():
    """Get the current vendor from thread-local storage."""
    return getattr(_thread_locals, 'vendor', None)

def get_current_user():
    """Get the current user from thread-local storage."""
    return getattr(_thread_locals, 'user', None)

def set_current_vendor(vendor):
    """Set the current vendor in thread-local storage."""
    _thread_locals.vendor = vendor

def set_current_user(user):
    """Set the current user in thread-local storage."""
    _thread_locals.user = user

def clear_thread_locals():
    """Clear thread-local storage (useful for testing)."""
    _thread_locals.vendor = None
    _thread_locals.user = None


class TenantMiddleware(MiddlewareMixin):
    """
    Middleware to identify the tenant from the request.
    
    This middleware must be placed after AuthenticationMiddleware
    because it needs the authenticated user.
    """
    
    def process_request(self, request):
        """
        Process each request before it reaches the view.
        
        Steps:
        1. Try to identify vendor from subdomain
        2. If not found, try from header
        3. If still not found, try from authenticated user
        4. Store vendor in thread-local and request
        """
        # Get vendor from various sources
        vendor = self.get_tenant_from_request(request)
        
        # Store in thread-local for model managers to use
        set_current_vendor(vendor)
        
        # Also attach to request for views to use
        request.vendor = vendor
        print(f"[TenantMiddleware] vendor set to {vendor}")
        
        # Store user in thread-local if authenticated
        if hasattr(request, 'user') and request.user.is_authenticated:
            set_current_user(request.user)
    
    def process_response(self, request, response):
        """
        Clean up after the request is processed.
        This prevents vendor data from leaking to other requests.
        """
        clear_thread_locals()
        return response
    
    def get_tenant_from_request(self, request):
    # 1. Try subdomain
        vendor = self.get_tenant_from_subdomain(request)
        if vendor:
            print(f"[Tenant] from subdomain: {vendor}")
            return vendor

    # 2. Try header
        vendor = self.get_tenant_from_header(request)
        if vendor:
            print(f"[Tenant] from header: {vendor}")
            return vendor

    # 3. Try from authenticated user (with detailed logs)
        if hasattr(request, 'user'):
            print(f"[Tenant] request.user exists: {request.user}")
            if request.user.is_authenticated:
                print(f"[Tenant] User is authenticated: {request.user.email}")
                if hasattr(request.user, 'vendor'):
                    print(f"[Tenant] User has vendor attribute: {request.user.vendor}")
                    if request.user.vendor:
                        print(f"[Tenant] from user: {request.user.vendor}")
                        return request.user.vendor
                    else:
                        print("[Tenant] User vendor is None")
                else:
                    print("[Tenant] User has no 'vendor' attribute")
            else:
                print("[Tenant] User is not authenticated")
        else:
            print("[Tenant] request.user does not exist")

        print("[Tenant] No tenant found")
        return None
    
    def get_tenant_from_subdomain(self, request):
        """
        Extract tenant from subdomain.
        
        Example:
        Request to: https://acme.smvia.com/api/products/
        Subdomain = 'acme'
        """
        # Get the host (e.g., acme.smvia.com or localhost:8000)
        host = request.get_host().split(':')[0]  # Remove port
        
        # Split into parts
        parts = host.split('.')
        
        # If we have at least 2 parts, the first might be a subdomain
        if len(parts) >= 2:
            potential_subdomain = parts[0]
            
            # Skip common non-tenant subdomains
            if potential_subdomain in ['www', 'api', 'app', 'admin', 'mail', 'localhost', '127']:
                return None
            
            # Try to find vendor with this subdomain
            from .models import Vendor
            try:
                return Vendor.objects.get(subdomain=potential_subdomain, is_active=True)
            except Vendor.DoesNotExist:
                return None
        
        return None
    
    def get_tenant_from_header(self, request):
        """
        Extract tenant from X-Tenant-ID header.
        
        This is useful for API clients that can't use subdomains.
        """
        vendor_id = request.headers.get('X-Tenant-ID')
        if not vendor_id:
            return None
        
        from .models import Vendor
        try:
            # Ensure it's an integer to prevent injection
            vendor_id = int(vendor_id)
            return Vendor.objects.get(id=vendor_id, is_active=True)
        except (ValueError, Vendor.DoesNotExist):
            return None
    
    def get_tenant_from_user(self, request):
        """
        Get tenant from authenticated user.
        
        If user is authenticated and belongs to a vendor, use that.
        """
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            return None
        
        # Platform admin might not have a vendor
        if request.user.role == 'platform_admin':
            return None
        
        # Check if user has a vendor
        if hasattr(request.user, 'vendor'):
            return request.user.vendor
        
        return None