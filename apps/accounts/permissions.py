"""
Custom permissions for API access.
"""

from rest_framework import permissions


class IsVendorAdmin(permissions.BasePermission):
    """
    Allow access only to vendor admins.
    """
    
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'vendor_admin'


class IsVendorStaff(permissions.BasePermission):
    """
    Allow access to vendor staff and above.
    """
    
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in [
            'vendor_admin', 'vendor_staff'
        ]


class IsOwnVendor(permissions.BasePermission):
    """
    Check if user belongs to the requested vendor.
    """
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Platform admin can access all
        if request.user.role == 'platform_admin':
            return True
        
        # Check if user has vendor
        return hasattr(request.user, 'vendor')
    
    def has_object_permission(self, request, view, obj):
        # Platform admin can access all
        if request.user.role == 'platform_admin':
            return True
        
        # Check if object belongs to user's vendor
        if hasattr(obj, 'vendor'):
            return obj.vendor == request.user.vendor
        return False