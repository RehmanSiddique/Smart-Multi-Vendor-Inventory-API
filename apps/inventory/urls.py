"""
URL configuration for Inventory API endpoints.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views  # Import the views module

router = DefaultRouter()
router.register(r'categories', views.CategoryViewSet, basename='category')
router.register(r'products', views.ProductViewSet, basename='product')
router.register(r'suppliers', views.SupplierViewSet, basename='supplier')
router.register(r'purchase-orders', views.PurchaseOrderViewSet, basename='purchaseorder')
router.register(r'sales', views.SaleViewSet, basename='sale')
router.register(r'notifications', views.NotificationViewSet, basename='notification')


urlpatterns = [
    path('', include(router.urls)),
    path('test-vendor/', views.test_vendor),
    path('seed-sample-data/', views.seed_sample_data),
    path('extended/', include('apps.inventory.urls_extended')),
]