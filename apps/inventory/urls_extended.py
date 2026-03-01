"""
Extended URL routes for advanced features.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views_extended

router = DefaultRouter()
router.register(r'customers', views_extended.CustomerViewSet, basename='customer')
router.register(r'variants', views_extended.ProductVariantViewSet, basename='variant')
router.register(r'warehouses', views_extended.WarehouseViewSet, basename='warehouse')
router.register(r'promotions', views_extended.PromotionViewSet, basename='promotion')
router.register(r'returns', views_extended.ReturnViewSet, basename='return')
router.register(r'webhooks', views_extended.WebhookViewSet, basename='webhook')
router.register(r'tags', views_extended.ProductTagViewSet, basename='tag')
router.register(r'audit-logs', views_extended.AuditLogViewSet, basename='audit-log')

urlpatterns = [
    # Router URLs
    path('', include(router.urls)),
    
    # Analytics endpoints
    path('analytics/dashboard/', views_extended.dashboard_metrics, name='dashboard-metrics'),
    path('analytics/sales-trend/', views_extended.sales_trend, name='sales-trend'),
    path('analytics/top-customers/', views_extended.top_customers, name='top-customers'),
    path('analytics/inventory-valuation/', views_extended.inventory_valuation, name='inventory-valuation'),
    path('analytics/category-performance/', views_extended.category_performance, name='category-performance'),
    path('analytics/supplier-performance/', views_extended.supplier_performance, name='supplier-performance'),
    
    # Bulk operations endpoints
    path('bulk/import-products/', views_extended.import_products, name='import-products'),
    path('bulk/export-products/', views_extended.export_products, name='export-products'),
    path('bulk/update-prices/', views_extended.bulk_update_prices, name='bulk-update-prices'),
    path('bulk/adjust-inventory/', views_extended.bulk_adjust_inventory, name='bulk-adjust-inventory'),
    path('bulk/export-sales/', views_extended.export_sales, name='export-sales'),
    path('bulk/import-customers/', views_extended.import_customers, name='import-customers'),
    
    # Utility endpoints
    path('utils/generate-barcode/', views_extended.generate_barcode, name='generate-barcode'),
]
