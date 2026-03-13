"""
Extended API views for advanced features.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.http import HttpResponse
from django.utils import timezone
from datetime import timedelta

from .models_extended import (
    Customer, ProductVariant, Warehouse, WarehouseInventory,
    Promotion, Return, ReturnItem, Webhook, ProductImage,
    ProductTag, AuditLog
)
from .serializers_extended import (
    CustomerSerializer, ProductVariantSerializer, WarehouseSerializer,
    WarehouseInventorySerializer, PromotionSerializer, ReturnSerializer,
    WebhookSerializer, ProductImageSerializer, ProductTagSerializer,
    AuditLogSerializer
)
from .analytics import AnalyticsService
from .bulk_operations import BulkOperationsService


class CustomerViewSet(viewsets.ModelViewSet):
    serializer_class = CustomerSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated and hasattr(user, 'vendor') and user.vendor:
            return Customer.all_objects.filter(vendor=user.vendor)
        return Customer.all_objects.none()
    
    @action(detail=True, methods=['get'])
    def purchase_history(self, request, pk=None):
        """Get customer purchase history."""
        from .models import Sale
        from .serializers import SaleSerializer
        
        customer = self.get_object()
        sales = Sale.objects.filter(
            vendor=customer.vendor,
            customer_email=customer.email
        ).order_by('-sale_date')
        
        serializer = SaleSerializer(sales, many=True)
        return Response(serializer.data)


class ProductVariantViewSet(viewsets.ModelViewSet):
    serializer_class = ProductVariantSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated and hasattr(user, 'vendor') and user.vendor:
            return ProductVariant.objects.filter(product__vendor=user.vendor)
        return ProductVariant.objects.none()


class WarehouseViewSet(viewsets.ModelViewSet):
    serializer_class = WarehouseSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated and hasattr(user, 'vendor') and user.vendor:
            return Warehouse.all_objects.filter(vendor=user.vendor)
        return Warehouse.all_objects.none()
    
    @action(detail=True, methods=['get'])
    def inventory(self, request, pk=None):
        """Get all inventory in this warehouse."""
        warehouse = self.get_object()
        inventory = WarehouseInventory.objects.filter(warehouse=warehouse)
        serializer = WarehouseInventorySerializer(inventory, many=True)
        return Response(serializer.data)


class PromotionViewSet(viewsets.ModelViewSet):
    serializer_class = PromotionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated and hasattr(user, 'vendor') and user.vendor:
            return Promotion.all_objects.filter(vendor=user.vendor)
        return Promotion.all_objects.none()
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get all active promotions."""
        now = timezone.now()
        promotions = self.get_queryset().filter(
            is_active=True,
            start_date__lte=now,
            end_date__gte=now
        )
        serializer = self.get_serializer(promotions, many=True)
        return Response(serializer.data)


class ReturnViewSet(viewsets.ModelViewSet):
    serializer_class = ReturnSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated and hasattr(user, 'vendor') and user.vendor:
            return Return.all_objects.filter(vendor=user.vendor)
        return Return.all_objects.none()
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve a return and restock inventory."""
        return_order = self.get_object()
        
        if return_order.status != 'pending':
            return Response(
                {'error': 'Only pending returns can be approved'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return_order.status = 'approved'
        return_order.processed_by = request.user
        return_order.save()
        
        # Restock items if requested
        if request.data.get('restock', False):
            for item in return_order.items.all():
                inventory = item.product.inventory
                inventory.adjust_inventory(
                    item.quantity,
                    'return',
                    notes=f"Return {return_order.return_number}",
                    user=request.user
                )
            return_order.restocked = True
            return_order.save()
        
        return Response({'status': 'approved'})


class WebhookViewSet(viewsets.ModelViewSet):
    serializer_class = WebhookSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated and hasattr(user, 'vendor') and user.vendor:
            return Webhook.all_objects.filter(vendor=user.vendor)
        return Webhook.all_objects.none()
    
    @action(detail=True, methods=['post'])
    def test(self, request, pk=None):
        """Test webhook by sending a test payload."""
        from .notifications import NotificationService
        
        webhook = self.get_object()
        test_data = {'event': 'test', 'message': 'This is a test webhook'}
        
        NotificationService.trigger_webhooks('test', test_data, webhook.vendor)
        
        return Response({'status': 'test webhook sent'})


class ProductTagViewSet(viewsets.ModelViewSet):
    serializer_class = ProductTagSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated and hasattr(user, 'vendor') and user.vendor:
            return ProductTag.all_objects.filter(vendor=user.vendor)
        return ProductTag.all_objects.none()


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AuditLogSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated and hasattr(user, 'vendor') and user.vendor:
            return AuditLog.all_objects.filter(vendor=user.vendor)
        return AuditLog.all_objects.none()


# Analytics endpoints
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_metrics(request):
    """Get dashboard analytics."""
    days = int(request.query_params.get('days', 30))
    
    analytics = AnalyticsService(request.user.vendor)
    metrics = analytics.get_dashboard_metrics(days)
    
    return Response(metrics)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def sales_trend(request):
    """Get sales trend data."""
    days = int(request.query_params.get('days', 30))
    
    analytics = AnalyticsService(request.user.vendor)
    trend = analytics.get_sales_trend(days)
    
    return Response(trend)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def top_customers(request):
    """Get top customers."""
    limit = int(request.query_params.get('limit', 10))
    
    analytics = AnalyticsService(request.user.vendor)
    customers = analytics.get_top_customers(limit)
    
    return Response(customers)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def inventory_valuation(request):
    """Get inventory valuation."""
    analytics = AnalyticsService(request.user.vendor)
    valuation = analytics.get_inventory_valuation()
    
    return Response(valuation)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def category_performance(request):
    """Get category performance."""
    days = int(request.query_params.get('days', 30))
    
    analytics = AnalyticsService(request.user.vendor)
    performance = analytics.get_category_performance(days)
    
    return Response(performance)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def supplier_performance(request):
    """Get supplier performance."""
    analytics = AnalyticsService(request.user.vendor)
    performance = analytics.get_supplier_performance()
    
    return Response(performance)


# Bulk operations endpoints
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def import_products(request):
    """Import products from CSV."""
    if 'file' not in request.FILES:
        return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)
    
    bulk_ops = BulkOperationsService(request.user.vendor)
    results = bulk_ops.import_products_csv(request.FILES['file'])
    
    return Response(results)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def export_products(request):
    """Export products to CSV."""
    bulk_ops = BulkOperationsService(request.user.vendor)
    csv_data = bulk_ops.export_products_csv()
    
    response = HttpResponse(csv_data, content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="products.csv"'
    
    return response


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def bulk_update_prices(request):
    """Bulk update product prices."""
    updates = request.data.get('updates', [])
    
    bulk_ops = BulkOperationsService(request.user.vendor)
    results = bulk_ops.bulk_update_prices(updates)
    
    return Response(results)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def bulk_adjust_inventory(request):
    """Bulk adjust inventory."""
    adjustments = request.data.get('adjustments', [])
    
    bulk_ops = BulkOperationsService(request.user.vendor)
    results = bulk_ops.bulk_adjust_inventory(adjustments)
    
    return Response(results)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def export_sales(request):
    """Export sales to CSV."""
    start_date = request.query_params.get('start_date')
    end_date = request.query_params.get('end_date')
    
    if not start_date or not end_date:
        return Response(
            {'error': 'start_date and end_date required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    bulk_ops = BulkOperationsService(request.user.vendor)
    csv_data = bulk_ops.export_sales_csv(start_date, end_date)
    
    response = HttpResponse(csv_data, content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="sales.csv"'
    
    return response


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def import_customers(request):
    """Import customers from CSV."""
    if 'file' not in request.FILES:
        return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)
    
    bulk_ops = BulkOperationsService(request.user.vendor)
    results = bulk_ops.import_customers_csv(request.FILES['file'])
    
    return Response(results)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_barcode(request):
    """Generate barcode for product."""
    import barcode
    from barcode.writer import ImageWriter
    from io import BytesIO
    
    code = request.data.get('code')
    barcode_type = request.data.get('type', 'code128')
    
    if not code:
        return Response({'error': 'Code required'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Generate barcode
        barcode_class = barcode.get_barcode_class(barcode_type)
        barcode_instance = barcode_class(code, writer=ImageWriter())
        
        buffer = BytesIO()
        barcode_instance.write(buffer)
        
        response = HttpResponse(buffer.getvalue(), content_type='image/png')
        response['Content-Disposition'] = f'attachment; filename="{code}.png"'
        
        return response
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
