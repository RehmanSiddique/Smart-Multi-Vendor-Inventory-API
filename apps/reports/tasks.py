"""
Celery tasks for report generation.
These run in the background so they don't slow down the web app.
"""

from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from apps.accounts.models import Vendor
from .services import SalesReportService, InventoryValuationService


@shared_task
def generate_daily_reports():
    """
    Generate daily reports for all active vendors.
    Runs every day at 1 AM.
    """
    vendors = Vendor.objects.filter(is_active=True)
    
    yesterday = timezone.now().date() - timedelta(days=1)
    
    for vendor in vendors:
        generate_vendor_daily_report.delay(vendor.id, yesterday.isoformat())
    
    return f"Started daily reports for {vendors.count()} vendors"


@shared_task
def generate_vendor_daily_report(vendor_id, report_date_str):
    """Generate daily report for a single vendor."""
    from django.utils.dateparse import parse_date
    
    vendor = Vendor.objects.get(id=vendor_id)
    report_date = parse_date(report_date_str)
    
    report = SalesReportService.generate_daily_report(vendor, report_date)
    
    return f"Generated daily report for {vendor.business_name} on {report_date}"


@shared_task
def generate_weekly_reports():
    """
    Generate weekly reports (Sunday nights).
    """
    vendors = Vendor.objects.filter(is_active=True)
    
    end_date = timezone.now().date() - timedelta(days=1)  # Yesterday
    start_date = end_date - timedelta(days=6)  # 7 days ago
    
    for vendor in vendors:
        generate_vendor_weekly_report.delay(
            vendor.id, 
            start_date.isoformat(), 
            end_date.isoformat()
        )
    
    return f"Started weekly reports for {vendors.count()} vendors"


@shared_task
def generate_vendor_weekly_report(vendor_id, start_date_str, end_date_str):
    """Generate weekly report for a single vendor."""
    from django.utils.dateparse import parse_date
    
    vendor = Vendor.objects.get(id=vendor_id)
    start_date = parse_date(start_date_str)
    end_date = parse_date(end_date_str)
    
    report = SalesReportService.generate_date_range_report(
        vendor, start_date, end_date, 'weekly'
    )
    
    return f"Generated weekly report for {vendor.business_name}"


@shared_task
def generate_inventory_valuations():
    """
    Generate daily inventory valuation snapshots.
    """
    vendors = Vendor.objects.filter(is_active=True)
    today = timezone.now().date()
    
    for vendor in vendors:
        generate_vendor_valuation.delay(vendor.id, today.isoformat())
    
    return f"Started inventory valuations for {vendors.count()} vendors"


@shared_task
def generate_vendor_valuation(vendor_id, valuation_date_str):
    """Generate inventory valuation for a single vendor."""
    from django.utils.dateparse import parse_date
    
    vendor = Vendor.objects.get(id=vendor_id)
    valuation_date = parse_date(valuation_date_str)
    
    valuation = InventoryValuationService.generate_valuation(vendor, valuation_date)
    
    return f"Generated valuation for {vendor.business_name}"