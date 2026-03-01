"""
Test script to verify API and add test categories
"""

from apps.accounts.models import User, Vendor
from apps.inventory.models import Category
from rest_framework.test import APIClient

# Get user and vendor
user = User.objects.get(email='admin@acme.com')
vendor = user.vendor

print(f"User: {user.email}")
print(f"Vendor: {vendor.business_name if vendor else 'None'}")

# Check existing categories
existing = Category.objects.filter(vendor=vendor).count()
print(f"Existing categories: {existing}")

# Create test categories if none exist
if existing == 0:
    print("\nCreating test categories...")
    
    electronics = Category.objects.create(
        vendor=vendor,
        name="Electronics",
        description="Electronic items"
    )
    print(f"✅ Created: {electronics.name}")
    
    computers = Category.objects.create(
        vendor=vendor,
        name="Computers",
        description="Computer hardware",
        parent=electronics
    )
    print(f"✅ Created: {computers.name}")
    
    laptops = Category.objects.create(
        vendor=vendor,
        name="Laptops",
        description="Laptop computers",
        parent=computers
    )
    print(f"✅ Created: {laptops.name}")

# Test API
print("\n" + "="*50)
print("Testing API...")
print("="*50)

client = APIClient()
client.force_authenticate(user=user)

response = client.get('/api/v1/inventory/categories/')
print(f"\nStatus: {response.status_code}")
print(f"Count: {response.json()['count']}")
print(f"Results: {len(response.json()['results'])} categories")

if response.json()['results']:
    print("\nCategories:")
    for cat in response.json()['results']:
        print(f"  - {cat['name']}")
else:
    print("\n⚠️ No categories returned!")
    print("This means the API is working but filtering by vendor correctly.")
    print("Categories exist in DB but API returns empty - checking why...")
    
    # Debug
    print(f"\nDirect DB query: {Category.objects.filter(vendor=vendor).count()} categories")
    print(f"User has vendor: {hasattr(user, 'vendor') and user.vendor is not None}")
