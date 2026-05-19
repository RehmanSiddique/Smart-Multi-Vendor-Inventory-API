import os
import django
import random
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.accounts.models import Vendor, User
from apps.inventory.models import Product, Sale, SaleItem, Inventory

def seed_sales():
    print("🚀 Seeding Sales data for Acme Corporation...")
    try:
        vendor = Vendor.objects.get(business_name='Acme Corporation')
        admin_user = User.objects.get(email='admin@acme.com')
    except Vendor.DoesNotExist:
        print("❌ Acme Corporation vendor not found. Run seed_acme.py first.")
        return

    products = Product.objects.filter(vendor=vendor)
    if not products.exists():
        print("❌ No products found for Acme. Run seed_acme.py first.")
        return

    # Create sales for the last 30 days
    today = timezone.now()
    
    # Customer emails/names for variety
    customers = [
        ('corp1@enterprise.com', 'Global Tech Solutions'),
        ('procure@citygov.org', 'City Government Procurement'),
        ('logistics@fastship.net', 'FastShip Logistics'),
        ('it@university.edu', 'Central States University'),
    ]

    sales_count = 0
    for i in range(25): # 25 sales
        # Spread sales over last 30 days
        sale_date = today - timedelta(days=random.randint(0, 30), hours=random.randint(0, 23))
        
        email, name = random.choice(customers)
        
        sale = Sale.objects.create(
            vendor=vendor,
            customer_name=name,
            customer_email=email,
            sale_date=sale_date,
            status='completed',
            payment_method=random.choice(['credit_card', 'bank_transfer', 'net_30']),
            total=Decimal('0') # Will calculate
        )
        
        # Add 1-4 items to each sale
        total_sale_amount = Decimal('0')
        items_to_add = random.sample(list(products), random.randint(1, min(len(products), 4)))
        
        for prod in items_to_add:
            qty = random.randint(1, 5)
            subtotal = prod.price * qty
            SaleItem.objects.create(
                sale=sale,
                product=prod,
                quantity=qty,
                unit_price=prod.price,
                subtotal=subtotal
            )
            total_sale_amount += subtotal
            
            # Adjust inventory
            try:
                inv = prod.inventory
                inv.quantity = max(0, inv.quantity - qty)
                inv.save()
            except:
                pass
                
        sale.total = total_sale_amount
        sale.save()
        sales_count += 1

    print(f"✅ Successfully seeded {sales_count} sales for Acme Corporation.")

if __name__ == "__main__":
    seed_sales()
