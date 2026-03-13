from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.accounts.models import User, Vendor
from apps.inventory.models import Product, Category, Sale, SaleItem
from datetime import datetime, timedelta

class Command(BaseCommand):
    help = 'Add sample products and sales data for testing'

    def handle(self, *args, **options):
        # Get the user
        try:
            user = User.objects.get(email='msiddique@email.com')
            vendor = user.vendor
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR('User not found'))
            return

        self.stdout.write(f'Adding sample data for vendor: {vendor.business_name}')

        # Get or create categories
        cat1 = Category.objects.filter(vendor=vendor, name='Electronics').first()
        if not cat1:
            cat1 = Category.objects.create(
                vendor=vendor,
                name='Electronics',
                description='Electronic devices'
            )
        
        cat2 = Category.objects.filter(vendor=vendor, name='Laptops').first()
        if not cat2:
            cat2 = Category.objects.create(
                vendor=vendor,
                name='Laptops',
                description='Laptop computers',
                parent=cat1
            )

        # Sample products with low stock
        products_data = [
            {
                'name': 'Dell XPS 13',
                'sku': 'DELL-XPS-13',
                'price': 999.99,
                'cost': 700.00,
                'quantity': 3,
                'reorder': 10,
                'category': cat2,
                'description': 'High-performance laptop'
            },
            {
                'name': 'MacBook Pro 16',
                'sku': 'MAC-PRO-16',
                'price': 2499.99,
                'cost': 1800.00,
                'quantity': 2,
                'reorder': 5,
                'category': cat2,
                'description': 'Professional laptop'
            },
            {
                'name': 'HP Pavilion 15',
                'sku': 'HP-PAV-15',
                'price': 599.99,
                'cost': 400.00,
                'quantity': 1,
                'reorder': 8,
                'category': cat2,
                'description': 'Budget laptop'
            },
            {
                'name': 'Lenovo ThinkPad',
                'sku': 'LENOVO-TP',
                'price': 1299.99,
                'cost': 900.00,
                'quantity': 4,
                'reorder': 6,
                'category': cat2,
                'description': 'Business laptop'
            },
            {
                'name': 'ASUS VivoBook',
                'sku': 'ASUS-VIVO',
                'price': 749.99,
                'cost': 500.00,
                'quantity': 2,
                'reorder': 7,
                'category': cat2,
                'description': 'Lightweight laptop'
            }
        ]

        created_products = []
        for prod_data in products_data:
            product, created = Product.objects.get_or_create(
                vendor=vendor,
                sku=prod_data['sku'],
                defaults={
                    'name': prod_data['name'],
                    'price': prod_data['price'],
                    'cost_price': prod_data['cost'],
                    'category': prod_data['category'],
                    'description': prod_data['description'],
                }
            )
            
            # Update or create inventory
            # Update inventory
            from apps.inventory.models import Inventory
            inv, _ = Inventory.objects.get_or_create(product=product)
            inv.quantity = prod_data['quantity']
            inv.reorder_level = prod_data['reorder']
            inv.save()
            
            created_products.append(product)
            status = 'Created' if created else 'Already exists'
            self.stdout.write(f'  ✓ {prod_data["name"]} - {status}')

        # Create sales for today
        today = timezone.now().date()
        sales_data = [
            {
                'customer_name': 'John Doe',
                'customer_email': 'john@example.com',
                'items': [
                    {'product': created_products[0], 'quantity': 1, 'price': 999.99},
                ]
            },
            {
                'customer_name': 'Jane Smith',
                'customer_email': 'jane@example.com',
                'items': [
                    {'product': created_products[1], 'quantity': 1, 'price': 2499.99},
                ]
            },
            {
                'customer_name': 'Bob Johnson',
                'customer_email': 'bob@example.com',
                'items': [
                    {'product': created_products[2], 'quantity': 2, 'price': 599.99},
                    {'product': created_products[3], 'quantity': 1, 'price': 1299.99},
                ]
            }
        ]

        for sale_data in sales_data:
            total = sum(item['quantity'] * item['price'] for item in sale_data['items'])
            
            sale, created = Sale.objects.get_or_create(
                vendor=vendor,
                customer_name=sale_data['customer_name'],
                sale_date=today,
                defaults={
                    'customer_email': sale_data['customer_email'],
                    'total': total,
                    'status': 'completed',
                }
            )
            
            if created:
                # Add sale items
                for item in sale_data['items']:
                    SaleItem.objects.create(
                        sale=sale,
                        product=item['product'],
                        quantity=item['quantity'],
                        unit_price=item['price'],
                        total=item['quantity'] * item['price']
                    )
                self.stdout.write(f'  ✓ Sale to {sale_data["customer_name"]} - ${total:.2f}')
            else:
                self.stdout.write(f'  ℹ Sale to {sale_data["customer_name"]} - Already exists')

        self.stdout.write(self.style.SUCCESS('✅ Sample data added successfully!'))
        self.stdout.write('Refresh your dashboard to see the changes.')
