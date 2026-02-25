# Manual Test Guide for Inventory Models
# Copy and paste these commands one by one into Django shell

# 1. Setup
from apps.accounts.middleware import set_current_vendor
from apps.accounts.models import Vendor
from apps.inventory.models import Supplier, PurchaseOrder, PurchaseOrderItem, Product
from decimal import Decimal

# 2. Get and set vendor
acme = Vendor.objects.get(subdomain='acme')
set_current_vendor(acme)
print(f"Vendor: {acme.business_name}")

# 3. Get or create supplier (handles duplicate error)
try:
    supplier = Supplier.objects.get(name="Test Supplier")
    print(f"Using existing supplier: {supplier.name}")
except Supplier.DoesNotExist:
    supplier = Supplier.objects.create(
        name="Test Supplier",
        contact_person="John Doe",
        email="john@test.com"
    )
    print(f"Created new supplier: {supplier.name}")

# 4. Get a product
product = Product.objects.first()
print(f"Product: {product.name}")

# 5. Create Purchase Order
po = PurchaseOrder.objects.create(
    supplier=supplier,
    tax=Decimal('45.50'),
    shipping_cost=Decimal('15.00')
)
print(f"Created PO: {po.order_number}")

# 6. Create Purchase Order Item
po_item = PurchaseOrderItem.objects.create(
    purchase_order=po,
    product=product,
    quantity=10,
    unit_price=Decimal('1350.00')
)
print(f"Item total: ${po_item.total}")

# 7. Check totals
po.refresh_from_db()
print(f"PO Subtotal: ${po.subtotal}")
print(f"PO Total: ${po.total_amount}")
print("✅ All Decimal operations working!")
