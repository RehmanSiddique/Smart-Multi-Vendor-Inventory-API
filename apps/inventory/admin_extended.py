"""
Admin registration for extended inventory models.
"""

from django.contrib import admin
from .models_extended import (
    Customer, ProductVariant, Warehouse, WarehouseInventory,
    Promotion, Return, ReturnItem, Webhook, ProductImage,
    ProductTag, AuditLog
)


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'customer_type', 'total_spent', 'total_orders', 'loyalty_points']
    list_filter = ['customer_type', 'is_active']
    search_fields = ['name', 'email', 'phone']


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ['product', 'name', 'sku', 'price', 'quantity', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'sku', 'product__name']


@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'city', 'state', 'manager_name', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'code', 'city']


@admin.register(Promotion)
class PromotionAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'discount_type', 'discount_value', 'start_date', 'end_date', 'is_active']
    list_filter = ['discount_type', 'is_active']
    search_fields = ['name', 'code']


@admin.register(Return)
class ReturnAdmin(admin.ModelAdmin):
    list_display = ['return_number', 'sale', 'return_date', 'status', 'refund_amount', 'restocked']
    list_filter = ['status', 'restocked']
    search_fields = ['return_number']


@admin.register(Webhook)
class WebhookAdmin(admin.ModelAdmin):
    list_display = ['name', 'url', 'is_active', 'success_count', 'failure_count', 'last_triggered']
    list_filter = ['is_active']
    search_fields = ['name', 'url']


@admin.register(ProductTag)
class ProductTagAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'vendor']
    search_fields = ['name', 'slug']


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['action', 'model_name', 'object_id', 'user', 'timestamp']
    list_filter = ['action', 'model_name', 'timestamp']
    search_fields = ['model_name', 'user__email']
    readonly_fields = ['action', 'model_name', 'object_id', 'changes', 'user', 'timestamp']
