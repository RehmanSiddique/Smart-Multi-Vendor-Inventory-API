"""
URL configuration for Reports API endpoints.
"""

from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard_summary, name='dashboard-summary'),
    path('sales-chart/', views.sales_chart_data, name='sales-chart'),
    path('analytics/', views.analytics_data, name='analytics'),
    path('inventory-valuation/', views.inventory_valuation, name='inventory-valuation'),
]
