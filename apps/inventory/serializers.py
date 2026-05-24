"""
Serializers for Inventory models.
Convert complex inventory models to JSON.
"""

from rest_framework import serializers
from .models import (
    Category, Product, Inventory, InventoryLog,
    Supplier, PurchaseOrder, PurchaseOrderItem,
    Sale, SaleItem
)
from apps.accounts.middleware import get_current_vendor


class CategoryField(serializers.PrimaryKeyRelatedField):
    """Custom field to handle category properly."""
    
    def to_internal_value(self, data):
        print(f"[CategoryField] Input data: {data} (type: {type(data)})")
        
        # Handle array case
        if isinstance(data, list):
            if len(data) > 0:
                data = data[0]
            else:
                return None
            print(f"[CategoryField] Extracted from array: {data}")
        
        # Handle dict case
        if isinstance(data, dict) and 'id' in data:
            data = data['id']
            print(f"[CategoryField] Extracted from dict: {data}")
        
        # Handle empty string
        if data == '' or data is None:
            return None
        
        print(f"[CategoryField] Final data to process: {data}")
        return super().to_internal_value(data)
    
    def get_queryset(self):
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            return Category.objects.filter(vendor=request.user.vendor)
        return Category.objects.all()


class CategorySerializer(serializers.ModelSerializer):
    """
    Serializer for Category model.
    Handles nested categories (parent/child).
    """
    
    full_path = serializers.CharField(read_only=True)
    product_count = serializers.IntegerField(read_only=True)
    level = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Category
        fields = [
            'id', 'name', 'slug', 'description', 'parent',
            'full_path', 'level', 'product_count', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['vendor'] = request.user.vendor
        else:
            raise serializers.ValidationError("Authentication required")
        return super().create(validated_data)


class InventorySerializer(serializers.ModelSerializer):
    """
    Serializer for Inventory model.
    """
    
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    
    class Meta:
        model = Inventory
        fields = [
            'product', 'product_name', 'product_sku',
            'quantity', 'reserved_quantity', 'available_quantity',
            'reorder_level', 'reorder_quantity', 'location',
            'last_restocked', 'last_counted'
        ]
        read_only_fields = ['available_quantity']


class ProductSerializer(serializers.ModelSerializer):
    """
    Serializer for Product model.
    Includes nested category and inventory.
    """
    
    category_name = serializers.CharField(source='category.name', read_only=True)
    inventory = InventorySerializer(read_only=True)
    profit_margin = serializers.FloatField(read_only=True)
    profit_amount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    discount_percentage = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'sku', 'barcode', 'description',
            'short_description', 'category', 'category_name',
            'product_type', 'price', 'compare_at_price', 'cost',
            'is_taxable', 'is_active', 'is_featured', 'is_on_sale',
            'image', 'slug', 'profit_margin', 'profit_amount',
            'discount_percentage', 'inventory', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at']
        extra_kwargs = {
            'category': {'required': False, 'allow_null': True}
        }

    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['vendor'] = request.user.vendor
        else:
            raise serializers.ValidationError("Authentication required")
        return super().create(validated_data)

class SupplierSerializer(serializers.ModelSerializer):
    """
    Serializer for Supplier model.
    """
    
    full_address = serializers.CharField(read_only=True)
    total_purchase_orders = serializers.IntegerField(read_only=True)
    total_spent = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = Supplier
        fields = [
            'id', 'name', 'code', 'contact_person', 'email', 'phone', 'website',
            'address_line1', 'address_line2', 'city', 'state', 
            'postal_code', 'country', 'tax_id', 'payment_terms', 'lead_time_days',
            'minimum_order_value', 'is_active', 'is_preferred', 'notes',
            'full_address', 'total_purchase_orders', 'total_spent',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'full_address', 'total_purchase_orders', 'total_spent']
        extra_kwargs = {
            'website': {'required': False, 'allow_blank': True},
            'email': {'required': False, 'allow_blank': True}
        }
    
    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['vendor'] = request.user.vendor
        else:
            raise serializers.ValidationError("Authentication required")
        return super().create(validated_data)

class PurchaseOrderItemSerializer(serializers.ModelSerializer):
    """
    Serializer for Purchase Order Items.
    """
    
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    
    class Meta:
        model = PurchaseOrderItem
        fields = [
            'id', 'product', 'product_name', 'product_sku',
            'quantity', 'quantity_received', 'unit_price', 'total'
        ]
        read_only_fields = ['id', 'total']
        


class PurchaseOrderSerializer(serializers.ModelSerializer):
    """
    Serializer for Purchase Orders.
    Includes nested items.
    """
    
    items = PurchaseOrderItemSerializer(many=True, read_only=True)
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = PurchaseOrder
        fields = [
            'id', 'order_number', 'supplier', 'supplier_name',
            'order_date', 'expected_date', 'received_date',
            'status', 'status_display', 'subtotal', 'tax',
            'shipping_cost', 'total_amount', 'tracking_number',
            'carrier', 'notes', 'items', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'order_number', 'subtotal', 'total_amount', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['vendor'] = request.user.vendor
        else:
            raise serializers.ValidationError("Authentication required")
        return super().create(validated_data)


class SaleItemSerializer(serializers.ModelSerializer):
    """
    Serializer for Sale Items.
    """
    
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    
    class Meta:
        model = SaleItem
        fields = [
            'id', 'product', 'product_name', 'product_sku',
            'quantity', 'unit_price', 'discount', 'subtotal'
        ]
        read_only_fields = ['id', 'subtotal']


class SaleSerializer(serializers.ModelSerializer):
    """
    Serializer for Sales.
    Includes nested items.
    """
    
    items = SaleItemSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)
    
    class Meta:
        model = Sale
        fields = [
            'id', 'sale_number', 'sale_date', 'status', 'status_display',
            'customer_name', 'customer_email', 'customer_phone',
            'subtotal', 'tax', 'shipping', 'discount', 'total',
            'payment_method', 'payment_method_display', 'payment_reference',
            'notes', 'items', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'sale_number', 'subtotal', 'total', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['vendor'] = request.user.vendor
        else:
            raise serializers.ValidationError("Authentication required")
        return super().create(validated_data)