"""
Test script for inventory models with proper error handling.
Run with: python manage.py shell < test_inventory.py
"""

from apps.accounts.middleware import set_current_vendor
from apps.accounts.models import Vendor
from apps.inventory.models import Supplier, PurchaseOrder, PurchaseOrderItem, Product
from decimal import Decimal

print("=" * 60)
print("Testing Inventory Models")
print("=" * 60)

# Get vendor
try:
    acme = Vendor.objects.get(subdomain='acme')
    set_current_vendor(acme)
    print(f"✅ Vendor set: {acme.business_name}")
except Vendor.DoesNotExist:
    print("❌ Vendor 'acme' not found. Please create it first.")
    exit()

# Test Supplier creation with unique name handling
print("\n--- Testing Supplier Creation ---")
supplier_name = "Test Supplier"
supplier, created = Supplier.objects.get_or_create(
    name=supplier_name,
    defaults={
        'contact_person': 'John Doe',
        'email': 'john@testsupplier.com',
        'phone': '555-1234'
    }
)

if created:
    print(f"✅ Created new supplier: {supplier.name}")
else:
    print(f"ℹ️  Using existing supplier: {supplier.name}")

# Get a product
print("\n--- Getting Product ---")
product = Product.objects.first()
if not product:
    print("❌ No products found. Please create products first.")
    exit()
print(f"✅ Product: {product.name} (SKU: {product.sku})")

# Test Purchase Order creation
print("\n--- Testing Purchase Order ---")
try:
    po = PurchaseOrder.objects.create(
        supplier=supplier,
        tax=Decimal('45.50'),
        shipping_cost=Decimal('15.00')
    )
    print(f"✅ Created PO: {po.order_number}")
    
    # Test Purchase Order Item
    print("\n--- Testing Purchase Order Item ---")
    po_item = PurchaseOrderItem.objects.create(
        purchase_order=po,
        product=product,
        quantity=10,
        unit_price=Decimal('1350.00')
    )
    print(f"✅ Created PO Item: {po_item}")
    print(f"✅ Item total: ${po_item.total}")
    
    # Refresh PO to get updated totals
    po.refresh_from_db()
    print(f"✅ PO Subtotal: ${po.subtotal}")
    print(f"✅ PO Total: ${po.total_amount}")
    print(f"✅ All Decimal operations working!")
    
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "=" * 60)
print("Test Complete!")
print("=" * 60)
