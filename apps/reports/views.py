"""
Simple views for dashboard and reports.
These would be used by a frontend or API.
"""

from django.shortcuts import render
from django.utils import timezone
from django.db.models import Sum, Count
from django.http import JsonResponse
from datetime import timedelta
from apps.accounts.middleware import get_current_vendor
from apps.inventory.models import Sale, Product, Inventory
from .models import SalesReport, InventoryValuation


def dashboard_summary(request):
    """
    Return summary data for dashboard.
    This would be called via AJAX to populate charts.
    """
    vendor = get_current_vendor()
    if not vendor:
        return JsonResponse({'error': 'No vendor context'}, status=400)
    
    today = timezone.now().date()
    
    # Today's sales
    today_sales = Sale.objects.filter(
        vendor=vendor,
        sale_date__date=today,
        status='completed'
    ).aggregate(
        total=Sum('total'),
        count=Count('id')
    )
    
    # Week to date
    week_start = today - timedelta(days=today.weekday())
    week_sales = Sale.objects.filter(
        vendor=vendor,
        sale_date__date__gte=week_start,
        status='completed'
    ).aggregate(total=Sum('total'))
    
    # Month to date
    month_start = today.replace(day=1)
    month_sales = Sale.objects.filter(
        vendor=vendor,
        sale_date__date__gte=month_start,
        status='completed'
    ).aggregate(total=Sum('total'))
    
    # Inventory stats
    low_stock = Product.objects.filter(
        vendor=vendor,
        inventory__quantity__lte=F('inventory__reorder_level')
    ).count()
    
    out_of_stock = Product.objects.filter(
        vendor=vendor,
        inventory__quantity=0
    ).count()
    
    total_products = Product.objects.filter(vendor=vendor, is_active=True).count()
    
    # Top products this month
    top_products = SaleItem.objects.filter(
        sale__vendor=vendor,
        sale__sale_date__date__gte=month_start,
        sale__status='completed'
    ).values('product__name').annotate(
        total=Sum('subtotal')
    ).order_by('-total')[:5]
    
    return JsonResponse({
        'today': {
            'sales': float(today_sales['total'] or 0),
            'orders': today_sales['count'] or 0,
        },
        'week': {
            'sales': float(week_sales['total'] or 0),
        },
        'month': {
            'sales': float(month_sales['total'] or 0),
        },
        'inventory': {
            'total_products': total_products,
            'low_stock': low_stock,
            'out_of_stock': out_of_stock,
        },
        'top_products': list(top_products),
    })


def sales_chart_data(request):
    """
    Return sales data for charts (last 30 days).
    """
    vendor = get_current_vendor()
    if not vendor:
        return JsonResponse({'error': 'No vendor context'}, status=400)
    
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=29)
    
    # Get daily reports
    reports = SalesReport.objects.filter(
        vendor=vendor,
        period='daily',
        start_date__gte=start_date,
        end_date__lte=end_date
    ).order_by('start_date')
    
    labels = []
    revenue_data = []
    order_data = []
    
    for report in reports:
        labels.append(report.start_date.strftime('%b %d'))
        revenue_data.append(float(report.total_revenue))
        order_data.append(report.total_sales)
    
    return JsonResponse({
        'labels': labels,
        'revenue': revenue_data,
        'orders': order_data,
    })