"""
Serializers for Inventory models.
Convert complex inventory models to JSON.
"""

from rest_framework import serializers
from .models import (
    Category, Product, Inventory, InventoryLog,
    Supplier, PurchaseOrder, PurchaseOrderItem,
    Sale, SaleItem, Notification
)


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
        if 'vendor' not in validated_data:
            request = self.context.get('request')
            if request and request.user.is_authenticated and hasattr(request.user, 'vendor'):
                validated_data['vendor'] = request.user.vendor
            else:
                raise serializers.ValidationError("No vendor context available")
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
    
    # Custom category field that handles vendor filtering properly  
    category = serializers.SerializerMethodField()  # Use SerializerMethodField for reads
    category_obj = serializers.SerializerMethodField(read_only=True)
    
    def get_category(self, obj):
        """Return category ID for filtering"""
        return obj.category.id if obj.category else None
    
    def get_category_obj(self, obj):
        """Return category object for read operations"""
        if obj.category:
            return {
                'id': obj.category.id,
                'name': obj.category.name
            }
        return None
    
    def to_internal_value(self, data):
        """Handle category input during create/update"""
        # Store category value for validation
        category_value = data.get('category')
        
        # Call parent to get validated data
        validated_data = super().to_internal_value(data)
        
        # Add category for validation if provided
        if category_value is not None:
            validated_data['category_input'] = category_value
            
        return validated_data
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'sku', 'barcode', 'description',
            'short_description', 'category', 'category_obj', 'category_name',
            'product_type', 'price', 'compare_at_price', 'cost',
            'is_taxable', 'is_active', 'is_featured', 'is_on_sale',
            'image', 'slug', 'profit_margin', 'profit_amount',
            'discount_percentage', 'inventory', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at', 'category_obj']
        extra_kwargs = {
            'category': {'write_only': False}  # Allow both read and write
        }
    
    def validate_category(self, value):
        """Validate category belongs to current vendor"""
        if value is None:
            return None
            
        # Handle array case from frontend
        if isinstance(value, list):
            value = value[0] if value else None
            if value is None:
                return None
        
        # Convert to integer
        try:
            category_id = int(value)
        except (ValueError, TypeError):
            raise serializers.ValidationError("Invalid category ID format")
        
        # Get vendor from request context
        request = self.context.get('request')
        if not request or not hasattr(request.user, 'vendor'):
            raise serializers.ValidationError("No vendor context available")
        
        vendor = request.user.vendor
        
        # Validate category exists for vendor
        try:
            category = Category.all_objects.get(id=category_id, vendor=vendor)
            return category_id  # Return the ID, not the object
        except Category.DoesNotExist:
            raise serializers.ValidationError(f"Category with ID {category_id} does not exist for your vendor")
    
    def validate_sku(self, value):
        """Validate SKU is unique for vendor"""
        request = self.context.get('request')
        if not request or not hasattr(request.user, 'vendor'):
            return value
        
        vendor = request.user.vendor
        
        if self.instance:
            # Updating existing product
            if Product.all_objects.filter(vendor=vendor, sku=value).exclude(pk=self.instance.pk).exists():
                raise serializers.ValidationError("A product with this SKU already exists for your vendor.")
        else:
            # Creating new product
            if Product.all_objects.filter(vendor=vendor, sku=value).exists():
                raise serializers.ValidationError("A product with this SKU already exists for your vendor.")
        
        return value
    
    def create(self, validated_data):
        """Create product with proper category assignment"""
        # Handle category ID to object conversion
        category_id = validated_data.pop('category_input', None)
        if category_id:
            try:
                category = Category.all_objects.get(id=category_id, vendor=self.context['request'].user.vendor)
                validated_data['category'] = category
            except Category.DoesNotExist:
                pass  # Already validated, shouldn't happen
        
        # Ensure vendor is set
        if 'vendor' not in validated_data:
            validated_data['vendor'] = self.context['request'].user.vendor
        
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        """Update product with proper category assignment"""
        # Handle category ID to object conversion
        category_id = validated_data.pop('category_input', None)
        if category_id is not None:
            try:
                category = Category.all_objects.get(id=category_id, vendor=self.context['request'].user.vendor)
                validated_data['category'] = category
            except Category.DoesNotExist:
                pass  # Already validated, shouldn't happen
        
        return super().update(instance, validated_data)


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
        if 'vendor' not in validated_data:
            request = self.context.get('request')
            if request and request.user.is_authenticated and hasattr(request.user, 'vendor'):
                validated_data['vendor'] = request.user.vendor
            else:
                raise serializers.ValidationError("No vendor context available")
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
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set the queryset for product field based on request context
        request = self.context.get('request') if hasattr(self, 'context') else None
        if not request and hasattr(self, '_context'):
            request = self._context.get('request')
        
        if request and hasattr(request.user, 'vendor') and request.user.vendor:
            vendor = request.user.vendor
            self.fields['product'].queryset = Product.all_objects.filter(vendor=vendor)


class PurchaseOrderSerializer(serializers.ModelSerializer):
    """
    Serializer for Purchase Orders.
    Includes nested items.
    """
    
    items = PurchaseOrderItemSerializer(many=True, read_only=False, required=False)
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
        extra_kwargs = {
            'supplier': {'required': False}  # Allow partial updates without supplier
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set the queryset for supplier field based on request context
        request = self.context.get('request')
        if request and hasattr(request.user, 'vendor') and request.user.vendor:
            vendor = request.user.vendor
            self.fields['supplier'].queryset = Supplier.all_objects.filter(vendor=vendor)
            # Set context for nested items serializer properly
            if hasattr(self.fields['items'], 'child'):
                # For ListSerializer, set context on the child serializer
                self.fields['items'].child._context = self.context
                # Also set the product queryset on the child serializer
                if hasattr(self.fields['items'].child.fields.get('product'), 'queryset'):
                    self.fields['items'].child.fields['product'].queryset = Product.all_objects.filter(vendor=vendor)
    
    def to_internal_value(self, data):
        """Override to handle supplier validation with vendor context"""
        # Get vendor from request context
        request = self.context.get('request')
        if not request or not hasattr(request.user, 'vendor'):
            raise serializers.ValidationError("No vendor context available")
        
        vendor = request.user.vendor
        
        # For updates, supplier is optional if already exists on instance
        is_update = self.instance is not None
        supplier_id = data.get('supplier')
        
        # Only validate supplier if provided or if creating new instance
        if supplier_id or not is_update:
            if supplier_id:
                try:
                    supplier = Supplier.all_objects.get(id=supplier_id, vendor=vendor)
                    if not supplier.is_active:
                        raise serializers.ValidationError({
                            'supplier': ['Cannot create purchase order with inactive supplier']
                        })
                except Supplier.DoesNotExist:
                    raise serializers.ValidationError({
                        'supplier': [f'Supplier with ID {supplier_id} does not exist for your vendor']
                    })
            elif not is_update:
                # Creating new PO without supplier - this should be caught by required validation
                pass
        
        # Validate items/products
        items_data = data.get('items', [])
        if items_data:
            for i, item_data in enumerate(items_data):
                product_id = item_data.get('product')
                if product_id:
                    try:
                        Product.all_objects.get(id=product_id, vendor=vendor)
                    except Product.DoesNotExist:
                        raise serializers.ValidationError({
                            'items': [f'Product with ID {product_id} does not exist for your vendor']
                        })
        
        return super().to_internal_value(data)
    
    def update(self, instance, validated_data):
        """Handle partial updates properly"""
        items_data = validated_data.pop('items', None)
        
        # Update the purchase order instance
        purchase_order = super().update(instance, validated_data)
        
        # Handle items if provided
        if items_data is not None:
            # Clear existing items and create new ones
            purchase_order.items.all().delete()
            for item_data in items_data:
                PurchaseOrderItem.objects.create(
                    purchase_order=purchase_order,
                    **item_data
                )
            purchase_order.calculate_totals()
        
        return purchase_order
    
    def create(self, validated_data):
        # Ensure supplier is provided for new purchase orders
        if 'supplier' not in validated_data:
            raise serializers.ValidationError({
                'supplier': ['This field is required when creating a new purchase order.']
            })
        
        if 'vendor' not in validated_data:
            request = self.context.get('request')
            if request and request.user.is_authenticated and hasattr(request.user, 'vendor'):
                validated_data['vendor'] = request.user.vendor
            else:
                raise serializers.ValidationError("No vendor context available")
        
        items_data = validated_data.pop('items', [])
        purchase_order = super().create(validated_data)
        
        for item_data in items_data:
            PurchaseOrderItem.objects.create(
                purchase_order=purchase_order,
                **item_data
            )
        
        purchase_order.calculate_totals()
        return purchase_order


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
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set the queryset for product field based on request context
        request = self.context.get('request') if hasattr(self, 'context') else None
        if not request and hasattr(self, '_context'):
            request = self._context.get('request')
        
        if request and hasattr(request.user, 'vendor') and request.user.vendor:
            vendor = request.user.vendor
            self.fields['product'].queryset = Product.all_objects.filter(vendor=vendor)


class SaleSerializer(serializers.ModelSerializer):
    """
    Serializer for Sales.
    Includes nested items.
    """
    
    items = SaleItemSerializer(many=True, read_only=False, required=False)
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
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set context for nested items serializer properly
        request = self.context.get('request')
        if request and hasattr(request.user, 'vendor') and request.user.vendor:
            vendor = request.user.vendor
            # Set context for nested items serializer
            if hasattr(self.fields['items'], 'child'):
                # For ListSerializer, set context on the child serializer
                self.fields['items'].child._context = self.context
                # Also set the product queryset on the child serializer
                if hasattr(self.fields['items'].child.fields.get('product'), 'queryset'):
                    self.fields['items'].child.fields['product'].queryset = Product.all_objects.filter(vendor=vendor)
    
    def to_internal_value(self, data):
        """Override to handle items validation with vendor context"""
        # Get vendor from request context
        request = self.context.get('request')
        if not request or not hasattr(request.user, 'vendor'):
            raise serializers.ValidationError("No vendor context available")
        
        vendor = request.user.vendor
        
        # Validate items/products
        items_data = data.get('items', [])
        if items_data:
            for i, item_data in enumerate(items_data):
                product_id = item_data.get('product')
                if product_id:
                    try:
                        Product.all_objects.get(id=product_id, vendor=vendor)
                    except Product.DoesNotExist:
                        raise serializers.ValidationError({
                            'items': [f'Product with ID {product_id} does not exist for your vendor']
                        })
        
        return super().to_internal_value(data)
    
    def create(self, validated_data):
        if 'vendor' not in validated_data:
            request = self.context.get('request')
            if request and request.user.is_authenticated and hasattr(request.user, 'vendor'):
                validated_data['vendor'] = request.user.vendor
            else:
                raise serializers.ValidationError("No vendor context available")
        
        items_data = validated_data.pop('items', [])
        sale = super().create(validated_data)
        
        # Create sale items
        for item_data in items_data:
            SaleItem.objects.create(
                sale=sale,
                **item_data
            )
        
        # Calculate totals after creating items
        sale.calculate_totals()
        return sale
    
    def update(self, instance, validated_data):
        """Handle partial updates properly"""
        items_data = validated_data.pop('items', None)
        
        # Update the sale instance
        sale = super().update(instance, validated_data)
        
        # Handle items if provided
        if items_data is not None:
            # Clear existing items and create new ones
            sale.items.all().delete()
            for item_data in items_data:
                SaleItem.objects.create(
                    sale=sale,
                    **item_data
                )
            sale.calculate_totals()
        
        return sale


class NotificationSerializer(serializers.ModelSerializer):
    """
    Serializer for Notification model.
    """
    
    notification_type_display = serializers.CharField(
        source='get_notification_type_display', read_only=True
    )
    priority_display = serializers.CharField(
        source='get_priority_display', read_only=True
    )
    time_ago = serializers.SerializerMethodField()
    
    class Meta:
        model = Notification
        fields = [
            'id', 'title', 'message', 'notification_type',
            'notification_type_display', 'priority', 'priority_display',
            'is_read', 'read_at', 'action_url', 'icon',
            'related_object_type', 'related_object_id',
            'time_ago', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'title', 'message', 'notification_type',
            'priority', 'action_url', 'icon',
            'related_object_type', 'related_object_id',
            'created_at', 'updated_at'
        ]
    
    def get_time_ago(self, obj):
        """Return human-readable time difference."""
        from django.utils import timezone
        now = timezone.now()
        diff = now - obj.created_at
        
        if diff.days > 30:
            months = diff.days // 30
            return f"{months} month{'s' if months > 1 else ''} ago"
        elif diff.days > 0:
            return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
        elif diff.seconds >= 3600:
            hours = diff.seconds // 3600
            return f"{hours} hour{'s' if hours > 1 else ''} ago"
        elif diff.seconds >= 60:
            mins = diff.seconds // 60
            return f"{mins} min{'s' if mins > 1 else ''} ago"
        else:
            return "Just now"
