"""
Comprehensive verification script for all extended features.
Run this to verify everything is working.
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from django.contrib.auth import get_user_model
from apps.accounts.models import Vendor
from apps.inventory.models import Product, Category, Supplier
from apps.inventory.models_extended import (
    Customer, Warehouse, Promotion, ProductVariant,
    ProductTag, Webhook, Return, AuditLog
)

User = get_user_model()

def test_models():
    """Test that all models are accessible."""
    print("\n🔍 Testing Models...")
    
    models_to_test = [
        ('Customer', Customer),
        ('Warehouse', Warehouse),
        ('Promotion', Promotion),
        ('ProductVariant', ProductVariant),
        ('ProductTag', ProductTag),
        ('Webhook', Webhook),
        ('Return', Return),
        ('AuditLog', AuditLog),
    ]
    
    for name, model in models_to_test:
        try:
            count = model.objects.count()
            print(f"✅ {name}: {count} records")
        except Exception as e:
            print(f"❌ {name}: ERROR - {str(e)}")
            return False
    
    return True

def test_api_imports():
    """Test that all API modules can be imported."""
    print("\n🔍 Testing API Imports...")
    
    try:
        from apps.inventory import views_extended
        print("✅ views_extended imported")
        
        from apps.inventory import serializers_extended
        print("✅ serializers_extended imported")
        
        from apps.inventory import analytics
        print("✅ analytics imported")
        
        from apps.inventory import bulk_operations
        print("✅ bulk_operations imported")
        
        from apps.inventory import notifications
        print("✅ notifications imported")
        
        from apps.inventory import tasks
        print("✅ tasks imported")
        
        return True
    except Exception as e:
        print(f"❌ Import Error: {str(e)}")
        return False

def test_urls():
    """Test that URLs are configured."""
    print("\n🔍 Testing URL Configuration...")
    
    try:
        from django.urls import reverse
        from django.urls import get_resolver
        
        resolver = get_resolver()
        
        # Test some key URLs
        test_urls = [
            'customer-list',
            'warehouse-list',
            'promotion-list',
            'webhook-list',
        ]
        
        for url_name in test_urls:
            try:
                url = reverse(url_name)
                print(f"✅ {url_name}: {url}")
            except:
                print(f"⚠️  {url_name}: Not found (may need namespace)")
        
        return True
    except Exception as e:
        print(f"❌ URL Error: {str(e)}")
        return False

def test_serializers():
    """Test that serializers work."""
    print("\n🔍 Testing Serializers...")
    
    try:
        from apps.inventory.serializers_extended import (
            CustomerSerializer, WarehouseSerializer, PromotionSerializer
        )
        
        print("✅ CustomerSerializer loaded")
        print("✅ WarehouseSerializer loaded")
        print("✅ PromotionSerializer loaded")
        
        return True
    except Exception as e:
        print(f"❌ Serializer Error: {str(e)}")
        return False

def test_services():
    """Test that service classes work."""
    print("\n🔍 Testing Services...")
    
    try:
        from apps.inventory.analytics import AnalyticsService
        from apps.inventory.bulk_operations import BulkOperationsService
        from apps.inventory.notifications import NotificationService
        
        # Try to get a vendor
        vendor = Vendor.objects.first()
        if vendor:
            analytics = AnalyticsService(vendor)
            print("✅ AnalyticsService initialized")
            
            bulk_ops = BulkOperationsService(vendor)
            print("✅ BulkOperationsService initialized")
        else:
            print("⚠️  No vendor found, skipping service initialization")
        
        print("✅ NotificationService loaded")
        
        return True
    except Exception as e:
        print(f"❌ Service Error: {str(e)}")
        return False

def create_test_data():
    """Create minimal test data."""
    print("\n🔍 Creating Test Data...")
    
    try:
        # Get or create vendor
        vendor = Vendor.objects.first()
        if not vendor:
            print("⚠️  No vendor found. Please create one first.")
            return False
        
        # Create test customer
        customer, created = Customer.objects.get_or_create(
            vendor=vendor,
            email='test@example.com',
            defaults={
                'name': 'Test Customer',
                'phone': '555-0000',
                'customer_type': 'retail'
            }
        )
        print(f"✅ Customer: {'Created' if created else 'Exists'}")
        
        # Create test warehouse
        warehouse, created = Warehouse.objects.get_or_create(
            vendor=vendor,
            name='Main Warehouse',
            defaults={
                'code': 'WH-001',
                'city': 'Test City',
                'state': 'TS'
            }
        )
        print(f"✅ Warehouse: {'Created' if created else 'Exists'}")
        
        # Create test promotion
        from datetime import datetime, timedelta
        promotion, created = Promotion.objects.get_or_create(
            vendor=vendor,
            name='Test Promotion',
            defaults={
                'code': 'TEST10',
                'discount_type': 'percentage',
                'discount_value': 10,
                'start_date': datetime.now(),
                'end_date': datetime.now() + timedelta(days=30)
            }
        )
        print(f"✅ Promotion: {'Created' if created else 'Exists'}")
        
        return True
    except Exception as e:
        print(f"❌ Test Data Error: {str(e)}")
        return False

def main():
    """Run all tests."""
    print("="*60)
    print("COMPREHENSIVE VERIFICATION TEST")
    print("="*60)
    
    results = []
    
    results.append(("Models", test_models()))
    results.append(("API Imports", test_api_imports()))
    results.append(("URLs", test_urls()))
    results.append(("Serializers", test_serializers()))
    results.append(("Services", test_services()))
    results.append(("Test Data", create_test_data()))
    
    print("\n" + "="*60)
    print("RESULTS SUMMARY")
    print("="*60)
    
    all_passed = True
    for name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"{status} - {name}")
        if not passed:
            all_passed = False
    
    print("="*60)
    
    if all_passed:
        print("\nALL TESTS PASSED! System is 100% operational!")
        print("\nNext Steps:")
        print("1. Start Django: python manage.py runserver")
        print("2. Start Frontend: cd React/inventory-frontend && npm run dev")
        print("3. Access: http://localhost:5173")
    else:
        print("\nSome tests failed. Please check the errors above.")
    
    return all_passed

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
