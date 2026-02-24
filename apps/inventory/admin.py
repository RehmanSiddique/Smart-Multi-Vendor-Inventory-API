from django.contrib import admin
from .models import Category, Product, Inventory, InventoryLog

class InventoryInline(admin.StackedInline):
    model = Inventory
    can_delete = False

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'vendor', 'parent', 'level', 'product_count', 'is_active']
    list_filter = ['vendor', 'is_active', 'parent']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    raw_id_fields = ['parent']
    
    def get_queryset(self, request):
        """Show categories with proper filtering"""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        # For staff, show only their vendor's categories
        if hasattr(request.user, 'vendor'):
            return qs.filter(vendor=request.user.vendor)
        return qs.none()

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'sku', 'vendor', 'category', 'price', 'is_active']
    list_filter = ['vendor', 'category', 'is_active', 'is_featured']
    search_fields = ['name', 'sku', 'description']
    prepopulated_fields = {'slug': ('name',)}
    inlines = [InventoryInline]
    fieldsets = (
        ('Basic Information', {
            'fields': ('vendor', 'name', 'sku', 'barcode', 'category')
        }),
        ('Description', {
            'fields': ('short_description', 'description')
        }),
        ('Pricing', {
            'fields': ('price', 'compare_at_price', 'cost', 'is_taxable')
        }),
        ('Status', {
            'fields': ('product_type', 'is_active', 'is_featured')
        }),
        ('Media & SEO', {
            'fields': ('image', 'slug', 'meta_title', 'meta_description'),
            'classes': ('collapse',)
        }),
        ('Tracking', {
            'fields': ('created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # If creating new object
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(InventoryLog)
class InventoryLogAdmin(admin.ModelAdmin):
    list_display = ['product', 'change', 'reason', 'created_by', 'created_at']
    list_filter = ['reason', 'created_at']
    search_fields = ['product__name', 'notes']
    readonly_fields = ['product', 'old_quantity', 'new_quantity', 'change', 
                      'reason', 'notes', 'created_by', 'created_at']
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False