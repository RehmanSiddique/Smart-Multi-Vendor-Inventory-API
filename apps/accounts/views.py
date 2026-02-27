"""
API Views for Account models.
"""

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import get_user_model

# Import models - these are safe
from .models import Vendor, User

# Import serializers
from .serializers import UserSerializer, UserCreateSerializer, VendorSerializer

# Import middleware - safe
from apps.accounts.middleware import get_current_vendor

# DO NOT import from urls.py here!

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for User model.
    Provides CRUD operations for users.
    """
    
    queryset = User.objects.all()
    serializer_class = UserSerializer
    
    def get_queryset(self):
        """Filter users based on vendor context."""
        vendor = get_current_vendor()
        if vendor:
            return User.objects.filter(vendor=vendor)
        return User.objects.none()
    
    def get_serializer_class(self):
        """Use different serializer for create operation."""
        if self.action == 'create':
            return UserCreateSerializer
        return UserSerializer
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get current user profile."""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)


class VendorViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Vendor model.
    Only accessible by platform admins.
    """
    
    queryset = Vendor.objects.all()
    serializer_class = VendorSerializer
    permission_classes = [permissions.IsAdminUser]
    
    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """Get vendor statistics."""
        vendor = self.get_object()
        data = {
            'users': vendor.users.count(),
            'products': vendor.products.count(),
            'categories': vendor.categories.count(),
            'suppliers': vendor.suppliers.count(),
            'sales': vendor.sales.count(),
            'purchase_orders': vendor.purchase_orders.count(),
        }
        return Response(data)