"""
Report models for storing pre-calculated analytics.
Caching report data improves performance for dashboards.
"""

from django.db import models
from django.utils import timezone
from decimal import Decimal
from apps.accounts.models import Vendor


class SalesReport(models.Model):
    """
    Pre-calculated sales report for a date range.
    Instead of calculating on every page load, we store results.
    """
    
    PERIOD_CHOICES = (
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
    )
    
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='sales_reports')
    
    # Report period
    period = models.CharField(max_length=20, choices=PERIOD_CHOICES)
    start_date = models.DateField()
    end_date = models.DateField()
    
    # Summary metrics
    total_sales = models.IntegerField(default=0, help_text="Number of transactions")
    total_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_profit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    average_order_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Product metrics
    top_products = models.JSONField(default=dict, help_text="Top selling products")
    products_sold = models.IntegerField(default=0, help_text="Total units sold")
    
    # Customer metrics
    unique_customers = models.IntegerField(default=0)
    
    # Metadata
    generated_at = models.DateTimeField(auto_now_add=True)
    is_final = models.BooleanField(default=False, help_text="Whether this is final or preliminary")
    
    class Meta:
        db_table = 'reports_sales'
        unique_together = ['vendor', 'period', 'start_date', 'end_date']
        indexes = [
            models.Index(fields=['vendor', '-start_date']),
            models.Index(fields=['vendor', 'period']),
        ]
        ordering = ['-start_date']
    
    def __str__(self):
        return f"{self.vendor.business_name} - {self.period} {self.start_date} to {self.end_date}"
    
    @property
    def profit_margin(self):
        """Calculate profit margin percentage."""
        if self.total_revenue > 0:
            return (self.total_profit / self.total_revenue) * 100
        return 0


class InventoryValuation(models.Model):
    """
    Snapshot of inventory value at a point in time.
    """
    
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='inventory_valuations')
    date = models.DateField(default=timezone.now)
    
    # Valuation by cost
    total_items = models.IntegerField(default=0, help_text="Total number of items in stock")
    total_products = models.IntegerField(default=0, help_text="Number of unique products")
    value_at_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    value_at_retail = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    potential_profit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Low stock
    low_stock_count = models.IntegerField(default=0)
    out_of_stock_count = models.IntegerField(default=0)
    
    # Category breakdown
    by_category = models.JSONField(default=dict)
    
    class Meta:
        db_table = 'reports_inventory_valuation'
        unique_together = ['vendor', 'date']
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.vendor.business_name} - Valuation {self.date}"


class ReportSchedule(models.Model):
    """
    Scheduled reports that will be emailed to users.
    """
    
    FREQUENCY_CHOICES = (
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    )
    
    REPORT_TYPES = (
        ('sales_summary', 'Sales Summary'),
        ('inventory_status', 'Inventory Status'),
        ('profit_loss', 'Profit & Loss'),
        ('low_stock', 'Low Stock Alert'),
    )
    
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='report_schedules')
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='report_schedules')
    
    name = models.CharField(max_length=100)
    report_type = models.CharField(max_length=50, choices=REPORT_TYPES)
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES)
    
    # Schedule details
    day_of_week = models.IntegerField(null=True, blank=True, help_text="0=Monday, 6=Sunday")
    day_of_month = models.IntegerField(null=True, blank=True, help_text="1-31")
    time_of_day = models.TimeField(default="09:00")
    
    # Format preferences
    format = models.CharField(max_length=10, choices=(('pdf', 'PDF'), ('csv', 'CSV')), default='pdf')
    
    # Status
    is_active = models.BooleanField(default=True)
    last_sent = models.DateTimeField(null=True, blank=True)
    next_send = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'reports_schedule'
    
    def __str__(self):
        return f"{self.name} - {self.frequency}"