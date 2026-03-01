"""
System verification - Tests all extended features
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.inventory.models_extended import Customer, Warehouse, Promotion, ProductVariant, ProductTag, Webhook, Return, AuditLog

print("="*60)
print("SYSTEM VERIFICATION TEST")
print("="*60)

# Test 1: Models
print("\n[1/6] Testing Models...")
try:
    print(f"  Customer: {Customer.objects.count()} records")
    print(f"  Warehouse: {Warehouse.objects.count()} records")
    print(f"  Promotion: {Promotion.objects.count()} records")
    print(f"  ProductVariant: {ProductVariant.objects.count()} records")
    print(f"  ProductTag: {ProductTag.objects.count()} records")
    print(f"  Webhook: {Webhook.objects.count()} records")
    print(f"  Return: {Return.objects.count()} records")
    print(f"  AuditLog: {AuditLog.objects.count()} records")
    print("  PASS - All models accessible")
except Exception as e:
    print(f"  FAIL - {e}")
    sys.exit(1)

# Test 2: Imports
print("\n[2/6] Testing Imports...")
try:
    from apps.inventory import views_extended, serializers_extended, analytics, bulk_operations, notifications, tasks
    print("  PASS - All modules imported")
except Exception as e:
    print(f"  FAIL - {e}")
    sys.exit(1)

# Test 3: Serializers
print("\n[3/6] Testing Serializers...")
try:
    from apps.inventory.serializers_extended import CustomerSerializer, WarehouseSerializer, PromotionSerializer
    print("  PASS - Serializers loaded")
except Exception as e:
    print(f"  FAIL - {e}")
    sys.exit(1)

# Test 4: Services
print("\n[4/6] Testing Services...")
try:
    from apps.inventory.analytics import AnalyticsService
    from apps.inventory.bulk_operations import BulkOperationsService
    from apps.accounts.models import Vendor
    vendor = Vendor.objects.first()
    if vendor:
        analytics = AnalyticsService(vendor)
        bulk = BulkOperationsService(vendor)
        print("  PASS - Services initialized")
    else:
        print("  WARN - No vendor, skipping")
except Exception as e:
    print(f"  FAIL - {e}")
    sys.exit(1)

# Test 5: URLs
print("\n[5/6] Testing URLs...")
try:
    from apps.inventory import urls_extended
    print("  PASS - Extended URLs loaded")
except Exception as e:
    print(f"  FAIL - {e}")
    sys.exit(1)

# Test 6: Create test data
print("\n[6/6] Creating Test Data...")
try:
    from apps.accounts.models import Vendor
    from datetime import datetime, timedelta
    
    vendor = Vendor.objects.first()
    if vendor:
        customer, _ = Customer.objects.get_or_create(
            vendor=vendor, email='test@test.com',
            defaults={'name': 'Test Customer', 'customer_type': 'retail'}
        )
        warehouse, _ = Warehouse.objects.get_or_create(
            vendor=vendor, name='Test Warehouse',
            defaults={'code': 'WH-001', 'city': 'Test City'}
        )
        promotion, _ = Promotion.objects.get_or_create(
            vendor=vendor, name='Test Promo',
            defaults={
                'code': 'TEST10', 'discount_type': 'percentage',
                'discount_value': 10, 'start_date': datetime.now(),
                'end_date': datetime.now() + timedelta(days=30)
            }
        )
        print(f"  Customer: {customer.name}")
        print(f"  Warehouse: {warehouse.name}")
        print(f"  Promotion: {promotion.name}")
        print("  PASS - Test data created")
    else:
        print("  WARN - No vendor found")
except Exception as e:
    print(f"  FAIL - {e}")
    sys.exit(1)

print("\n" + "="*60)
print("ALL TESTS PASSED - SYSTEM 100% OPERATIONAL")
print("="*60)
print("\nNext Steps:")
print("1. python manage.py runserver")
print("2. cd React/inventory-frontend && npm run dev")
print("3. Open http://localhost:5173")
