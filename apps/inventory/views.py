"""
API Views for Inventory models.
"""

from rest_framework import viewsets, filters, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Sum, F
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from .models import (
    Category, Product, Inventory, InventoryLog,
    Supplier, PurchaseOrder, PurchaseOrderItem,
    Sale, SaleItem
)
from .serializers import (
    CategorySerializer, ProductSerializer, InventorySerializer,
    SupplierSerializer, PurchaseOrderSerializer, PurchaseOrderItemSerializer,
    SaleSerializer, SaleItemSerializer
)
from apps.accounts.middleware import get_current_vendor


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def test_vendor(request):
    user = request.user
    if user.is_authenticated and hasattr(user, 'vendor') and user.vendor:
        return Response({
            'vendor': user.vendor.business_name,
            'id': user.vendor.id,
            'subdomain': user.vendor.subdomain
        })
    return Response({'vendor': None})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def seed_sample_data(request):
    """Create sample products, suppliers, purchase orders, customers and sales for testing."""
    vendor = request.user.vendor
    if not vendor:
        return Response({'error': 'No vendor context'}, status=400)
    
    try:
        # Create sample supplier
        supplier, _ = Supplier.objects.get_or_create(
            vendor=vendor,
            name='Tech Supplies Inc',
            defaults={
                'contact_person': 'John Smith',
                'email': 'john@techsupplies.com',
                'phone': '+1-555-0123',
                'address_line1': '123 Tech Street',
                'city': 'San Francisco',
                'state': 'CA',
                'postal_code': '94105',
                'country': 'USA',
                'payment_terms': 'Net 30',
                'lead_time_days': 5,
                'is_active': True,
            }
        )
        
        # Create sample products with low stock
        products_data = [
            {'name': 'Laptop', 'sku': 'LAP-001', 'price': 999.99, 'quantity': 2, 'reorder_level': 5},
            {'name': 'Mouse', 'sku': 'MOU-001', 'price': 29.99, 'quantity': 3, 'reorder_level': 10},
            {'name': 'Keyboard', 'sku': 'KEY-001', 'price': 79.99, 'quantity': 1, 'reorder_level': 5},
            {'name': 'Monitor', 'sku': 'MON-001', 'price': 299.99, 'quantity': 0, 'reorder_level': 3},
            {'name': 'USB Cable', 'sku': 'USB-001', 'price': 9.99, 'quantity': 4, 'reorder_level': 20},
        ]
        
        created_products = []
        for prod_data in products_data:
            product, _ = Product.objects.get_or_create(
                vendor=vendor,
                sku=prod_data['sku'],
                defaults={
                    'name': prod_data['name'],
                    'price': Decimal(str(prod_data['price'])),
                    'description': f'Sample {prod_data["name"]} for testing',
                }
            )
            
            # Create or update inventory
            Inventory.objects.update_or_create(
                product=product,
                defaults={
                    'quantity': prod_data['quantity'],
                    'reorder_level': prod_data['reorder_level'],
                    'location': 'Main Warehouse'
                }
            )
            created_products.append(product)
        
        # Create sample purchase orders
        po_data = [
            {'products': [created_products[0], created_products[1]], 'quantities': [10, 50]},
            {'products': [created_products[2], created_products[3]], 'quantities': [20, 15]},
        ]
        
        created_pos = []
        for idx, po_info in enumerate(po_data):
            po = PurchaseOrder.objects.create(
                vendor=vendor,
                supplier=supplier,
                expected_date=timezone.now() + timedelta(days=7),
                notes=f'Sample purchase order {idx+1}',
                status='confirmed',
                tax=Decimal('50.00'),
                shipping_cost=Decimal('25.00')
            )
            
            # Add items to PO
            for product, qty in zip(po_info['products'], po_info['quantities']):
                PurchaseOrderItem.objects.create(
                    purchase_order=po,
                    product=product,
                    quantity=qty,
                    unit_price=product.price
                )
            
            po.calculate_totals()
            created_pos.append(po)
        
        # Create sample sales for today
        today = timezone.now()
        sales_data = [
            {'product': created_products[0], 'quantity': 1, 'price': 999.99},
            {'product': created_products[1], 'quantity': 5, 'price': 29.99},
            {'product': created_products[2], 'quantity': 2, 'price': 79.99},
        ]
        
        created_sales = []
        for sale_data in sales_data:
            total = Decimal(str(sale_data['quantity'] * sale_data['price']))
            sale = Sale.objects.create(
                vendor=vendor,
                customer_name='Sample Customer',
                customer_email='customer@example.com',
                sale_date=today,
                total=total,
                status='completed',
                payment_method='cash'
            )
            
            SaleItem.objects.create(
                sale=sale,
                product=sale_data['product'],
                quantity=sale_data['quantity'],
                unit_price=Decimal(str(sale_data['price'])),
                subtotal=total
            )
            created_sales.append(sale)
        
        return Response({
            'status': 'success',
            'message': f'Created {len(created_products)} products, {len(created_pos)} purchase orders, and {len(created_sales)} sales',
            'products': len(created_products),
            'purchase_orders': len(created_pos),
            'sales': len(created_sales),
            'supplier': supplier.name
        })
    
    except Exception as e:
        return Response({'error': str(e)}, status=400)

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'is_active', 'is_featured']
    search_fields = ['name', 'sku', 'description']
    ordering_fields = ['name', 'price', 'created_at']
    
    def get_queryset(self):
        vendor = get_current_vendor()
        if not vendor and hasattr(self.request.user, 'vendor'):
            vendor = self.request.user.vendor
        if vendor:
            return Product.all_objects.filter(vendor=vendor).select_related('category').prefetch_related('inventory')
        return Product.all_objects.none()
    
    def perform_create(self, serializer):
        vendor = get_current_vendor()
        if not vendor and hasattr(self.request.user, 'vendor'):
            vendor = self.request.user.vendor
        if not vendor:
            raise ValueError("No vendor context available")
        serializer.context['vendor'] = vendor
        serializer.save(vendor=vendor)
    
    def destroy(self, request, *args, **kwargs):
        """Custom destroy method to handle products with sale references."""
        try:
            instance = self.get_object()
            
            # Check if product has any sale items
            if instance.sale_items.exists():
                return Response({
                    'error': 'Cannot delete product that has been sold. This product appears in sales records.',
                    'detail': 'Products with sales history cannot be deleted to maintain data integrity. Consider marking it as inactive instead.',
                    'suggestion': 'Set is_active=False to hide this product from listings.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # If no sale items, proceed with normal deletion
            return super().destroy(request, *args, **kwargs)
            
        except Exception as e:
            # Handle any other database integrity errors
            return Response({
                'error': 'Cannot delete product due to database constraints.',
                'detail': str(e),
                'suggestion': 'This product may be referenced by other records. Consider marking it as inactive instead.'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def low_stock(self, request):
        """Get all low stock products."""
        products = self.get_queryset().filter(
            inventory__quantity__lte=F('inventory__reorder_level')
        )
        serializer = self.get_serializer(products, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def inventory(self, request, pk=None):
        """Get inventory for this product."""
        product = self.get_object()
        try:
            inventory = product.inventory
            serializer = InventorySerializer(inventory)
            return Response(serializer.data)
        except Inventory.DoesNotExist:
            return Response({'error': 'No inventory record'}, status=404)
    



class CategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Category model.
    Provides CRUD operations for categories.
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active', 'parent']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    
    def get_queryset(self):
        vendor = get_current_vendor()
        if not vendor and hasattr(self.request.user, 'vendor'):
            vendor = self.request.user.vendor
        if vendor:
            return Category.all_objects.filter(vendor=vendor)
        return Category.all_objects.none()
    
    def perform_create(self, serializer):
        vendor = get_current_vendor()
        if not vendor and hasattr(self.request.user, 'vendor'):
            vendor = self.request.user.vendor
        if not vendor:
            raise ValueError("No vendor context available")
        serializer.save(vendor=vendor)
    
    @action(detail=True, methods=['get'])
    def products(self, request, pk=None):
        """Get all products in this category."""
        category = self.get_object()
        products = category.products.all()
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def tree(self, request, pk=None):
        """Get category tree (with children)."""
        category = self.get_object()
        data = {
            'category': CategorySerializer(category).data,
            'children': CategorySerializer(category.children.all(), many=True).data,
        }
        return Response(data)








class SupplierViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Supplier model.
    """
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active', 'is_preferred', 'country']
    search_fields = ['name', 'contact_person', 'email']
    ordering_fields = ['name', 'created_at']
    
    def get_queryset(self):
        vendor = get_current_vendor()
        if not vendor and hasattr(self.request.user, 'vendor'):
            vendor = self.request.user.vendor
        if vendor:
            return Supplier.all_objects.filter(vendor=vendor)
        return Supplier.all_objects.none()
    
    def perform_create(self, serializer):
        vendor = get_current_vendor()
        if not vendor and hasattr(self.request.user, 'vendor'):
            vendor = self.request.user.vendor
        if not vendor:
            raise ValueError("No vendor context available")
        serializer.save(vendor=vendor)
    
    def destroy(self, request, *args, **kwargs):
        """Custom destroy method to handle suppliers with purchase order references."""
        try:
            instance = self.get_object()
            
            # Check if supplier has any purchase orders
            if instance.purchase_orders.exists():
                return Response({
                    'error': 'Cannot delete supplier that has purchase orders. This supplier appears in purchase order records.',
                    'detail': 'Suppliers with purchase order history cannot be deleted to maintain data integrity. Consider marking it as inactive instead.',
                    'suggestion': 'Set is_active=False to hide this supplier from listings.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # If no purchase orders, proceed with normal deletion
            return super().destroy(request, *args, **kwargs)
            
        except Exception as e:
            # Handle any other database integrity errors
            return Response({
                'error': 'Cannot delete supplier due to database constraints.',
                'detail': str(e),
                'suggestion': 'This supplier may be referenced by other records. Consider marking it as inactive instead.'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def purchase_orders(self, request, pk=None):
        """Get all purchase orders for this supplier."""
        supplier = self.get_object()
        pos = supplier.purchase_orders.all()
        serializer = PurchaseOrderSerializer(pos, many=True)
        return Response(serializer.data)


class PurchaseOrderViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Purchase Orders.
    """
    queryset = PurchaseOrder.objects.all()
    serializer_class = PurchaseOrderSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['supplier', 'status']
    search_fields = ['order_number', 'supplier__name']
    ordering_fields = ['order_date', 'expected_date', 'total_amount']
    
    def get_queryset(self):
        vendor = get_current_vendor()
        if not vendor and hasattr(self.request.user, 'vendor'):
            vendor = self.request.user.vendor
        if vendor:
            return PurchaseOrder.all_objects.filter(vendor=vendor).select_related('supplier')
        return PurchaseOrder.all_objects.none()
    
    def perform_create(self, serializer):
        vendor = get_current_vendor()
        if not vendor and hasattr(self.request.user, 'vendor'):
            vendor = self.request.user.vendor
        if not vendor:
            raise ValueError("No vendor context available")
        
        try:
            serializer.save(vendor=vendor)
        except Exception as e:
            from rest_framework.exceptions import ValidationError
            raise ValidationError({
                'error': 'Failed to create purchase order',
                'detail': str(e)
            })
    
    @action(detail=True, methods=['post'])
    def receive_item(self, request, pk=None):
        """Receive items for a purchase order."""
        po = self.get_object()
        item_id = request.data.get('item_id')
        quantity = request.data.get('quantity')
        
        try:
            item = po.items.get(id=item_id)
            item.receive(quantity)
            return Response({'status': 'received', 'item': PurchaseOrderItemSerializer(item).data})
        except PurchaseOrderItem.DoesNotExist:
            return Response({'error': 'Item not found'}, status=404)
        except ValueError as e:
            return Response({'error': str(e)}, status=400)
    
    @action(detail=True, methods=['post'])
    def receive_all(self, request, pk=None):
        """Receive all items for a purchase order."""
        po = self.get_object()
        for item in po.items.all():
            item.receive(item.quantity)
        po.refresh_from_db()
        return Response({'status': 'all items received', 'po': PurchaseOrderSerializer(po).data})


class SaleViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Sales.
    """
    queryset = Sale.objects.all()
    serializer_class = SaleSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'payment_method']
    search_fields = ['sale_number', 'customer_name', 'customer_email']
    ordering_fields = ['sale_date', 'total']
    
    def get_queryset(self):
        vendor = get_current_vendor()
        if not vendor and hasattr(self.request.user, 'vendor'):
            vendor = self.request.user.vendor
        if vendor:
            return Sale.all_objects.filter(vendor=vendor).prefetch_related('items')
        return Sale.all_objects.none()
    
    def perform_create(self, serializer):
        vendor = get_current_vendor()
        if not vendor and hasattr(self.request.user, 'vendor'):
            vendor = self.request.user.vendor
        if not vendor:
            raise ValueError("No vendor context available")
        serializer.save(vendor=vendor, status='completed')
    
    @action(detail=False, methods=['get'])
    def today(self, request):
        """Get today's sales."""
        today = timezone.now().date()
        sales = self.get_queryset().filter(sale_date__date=today)
        serializer = self.get_serializer(sales, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def range(self, request):
        """Get sales in date range."""
        start = request.query_params.get('start')
        end = request.query_params.get('end')
        
        if not start or not end:
            return Response({'error': 'Start and end dates required'}, status=400)
        
        sales = self.get_queryset().filter(
            sale_date__date__gte=start,
            sale_date__date__lte=end
        )
        
        # Calculate totals
        total_revenue = sales.aggregate(total=Sum('total'))['total'] or 0
        total_orders = sales.count()
        
        data = {
            'range': f"{start} to {end}",
            'total_revenue': total_revenue,
            'total_orders': total_orders,
            'sales': self.get_serializer(sales, many=True).data
        }
        return Response(data)