"""
API Views for Inventory models.
"""

from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Sum, Count, Q, F
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from rest_framework.decorators import action
from rest_framework.response import Response

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


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    
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
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active', 'parent']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    
    def get_queryset(self):
        """Filter by current vendor."""
        vendor = get_current_vendor()
        if vendor:
            return Category.objects.filter(vendor=vendor)
        return Category.objects.none()
    
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
        descendants = category.get_descendants()
        data = {
            'category': CategorySerializer(category).data,
            'descendants': CategorySerializer(descendants, many=True).data,
            'full_path': category.get_full_path(),
        }
        return Response(data)





class SupplierViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Supplier model.
    """
    
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active', 'is_preferred', 'country']
    search_fields = ['name', 'contact_person', 'email']
    ordering_fields = ['name', 'created_at']
    
    def get_queryset(self):
        """Filter by current vendor."""
        vendor = get_current_vendor()
        if vendor:
            return Supplier.objects.filter(vendor=vendor)
        return Supplier.objects.none()
    
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
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['supplier', 'status']
    search_fields = ['order_number', 'supplier__name']
    ordering_fields = ['order_date', 'expected_date', 'total_amount']
    
    def get_queryset(self):
        """Filter by current vendor."""
        vendor = get_current_vendor()
        if vendor:
            return PurchaseOrder.objects.filter(vendor=vendor).select_related('supplier')
        return PurchaseOrder.objects.none()
    
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
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'payment_method']
    search_fields = ['sale_number', 'customer_name', 'customer_email']
    ordering_fields = ['sale_date', 'total']
    
    def get_queryset(self):
        """Filter by current vendor."""
        vendor = get_current_vendor()
        if vendor:
            return Sale.objects.filter(vendor=vendor).prefetch_related('items')
        return Sale.objects.none()
    
    def perform_create(self, serializer):
        """Auto-assign vendor and set status."""
        serializer.save(
            vendor=get_current_vendor(),
            status='completed'
        )
    
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