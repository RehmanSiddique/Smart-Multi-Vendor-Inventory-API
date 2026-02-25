from django.contrib import admin
from .models import Category, Product, Inventory, InventoryLog,Supplier, PurchaseOrder, PurchaseOrderItem, Sale, SaleItem

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
    
    def has_delete_permission(self, request, obj=None):
        return False

class PurchaseOrderItemInline(admin.TabularInline):
    model = PurchaseOrderItem
    extra = 1
    fields = ['product', 'quantity', 'unit_price', 'quantity_received']

class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 1
    fields = ['product', 'quantity', 'unit_price', 'discount']

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ['name', 'vendor', 'contact_person', 'email', 'phone', 'is_preferred']
    list_filter = ['vendor', 'is_active', 'is_preferred', 'country']
    search_fields = ['name', 'contact_person', 'email']
    list_editable = ['is_preferred']

@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'vendor', 'supplier', 'order_date', 'status', 'total_amount']
    list_filter = ['vendor', 'status', 'order_date']
    search_fields = ['order_number', 'supplier__name']
    inlines = [PurchaseOrderItemInline]
    readonly_fields = ['subtotal', 'total_amount']
    fieldsets = (
        ('Order Information', {
            'fields': ('vendor', 'order_number', 'supplier', 'order_date', 'expected_date')
        }),
        ('Status', {
            'fields': ('status', 'received_date', 'received_by')
        }),
        ('Financial', {
            'fields': ('subtotal', 'tax', 'shipping_cost', 'total_amount')
        }),
        ('Tracking', {
            'fields': ('tracking_number', 'carrier')
        }),
        ('Notes', {
            'fields': ('notes', 'internal_notes')
        }),
    )

@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ['sale_number', 'vendor', 'sale_date', 'customer_name', 'total', 'status']
    list_filter = ['vendor', 'status', 'payment_method', 'sale_date']
    search_fields = ['sale_number', 'customer_name', 'customer_email']
    inlines = [SaleItemInline]
    readonly_fields = ['subtotal', 'total']
    fieldsets = (
        ('Sale Information', {
            'fields': ('vendor', 'sale_number', 'sale_date', 'status')
        }),
        ('Customer', {
            'fields': ('customer_name', 'customer_email', 'customer_phone')
        }),
        ('Financial', {
            'fields': ('subtotal', 'tax', 'shipping', 'discount', 'total')
        }),
        ('Payment', {
            'fields': ('payment_method', 'payment_reference')
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
    )