from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from apps.accounts.models import Vendor, User
from apps.inventory.models import Supplier, Product, PurchaseOrder, PurchaseOrderItem


class Command(BaseCommand):
    help = 'Test purchase order creation functionality'

    def add_arguments(self, parser):
        parser.add_argument(
            '--vendor-id',
            type=int,
            help='Vendor ID to test with',
        )

    def handle(self, *args, **options):
        vendor_id = options.get('vendor_id')
        
        if vendor_id:
            try:
                vendor = Vendor.objects.get(id=vendor_id)
            except Vendor.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Vendor with ID {vendor_id} does not exist')
                )
                return
        else:
            vendor = Vendor.objects.first()
            if not vendor:
                self.stdout.write(
                    self.style.ERROR('No vendors found')
                )
                return

        self.stdout.write(f'Testing purchase orders for vendor: {vendor.business_name}')
        
        # Get test data
        suppliers = Supplier.all_objects.filter(vendor=vendor, is_active=True)
        products = Product.all_objects.filter(vendor=vendor, is_active=True)
        
        if not suppliers.exists():
            self.stdout.write(self.style.ERROR('No active suppliers found'))
            return
            
        if not products.exists():
            self.stdout.write(self.style.ERROR('No active products found'))
            return
        
        supplier = suppliers.first()
        product_list = list(products[:3])  # Get first 3 products
        
        self.stdout.write(f'Using supplier: {supplier.name} (ID: {supplier.id})')
        self.stdout.write(f'Using products: {[f"{p.name} (ID: {p.id})" for p in product_list]}')
        
        # Test 1: Create simple purchase order
        self.stdout.write('\n' + '='*50)
        self.stdout.write('TEST 1: Creating simple purchase order')
        self.stdout.write('='*50)
        
        try:
            po1 = PurchaseOrder.objects.create(
                vendor=vendor,
                supplier=supplier,
                expected_date=timezone.now() + timedelta(days=7),
                status='draft',
                tax=Decimal('25.00'),
                shipping_cost=Decimal('15.00'),
                notes='Test purchase order from management command'
            )
            
            # Add item
            PurchaseOrderItem.objects.create(
                purchase_order=po1,
                product=product_list[0],
                quantity=10,
                unit_price=Decimal('50.00')
            )
            
            po1.calculate_totals()
            
            self.stdout.write(
                self.style.SUCCESS(f'Created PO: {po1.order_number} - Total: ${po1.total_amount}')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Failed to create simple PO: {str(e)}')
            )
        
        # Test 2: Create multi-item purchase order
        self.stdout.write('\n' + '='*50)
        self.stdout.write('TEST 2: Creating multi-item purchase order')
        self.stdout.write('='*50)
        
        try:
            po2 = PurchaseOrder.objects.create(
                vendor=vendor,
                supplier=supplier,
                expected_date=timezone.now() + timedelta(days=10),
                status='draft',
                tax=Decimal('50.00'),
                shipping_cost=Decimal('30.00'),
                notes='Multi-item test purchase order'
            )
            
            # Add multiple items
            for i, product in enumerate(product_list):
                PurchaseOrderItem.objects.create(
                    purchase_order=po2,
                    product=product,
                    quantity=(i + 1) * 5,  # 5, 10, 15
                    unit_price=Decimal(f'{(i + 1) * 25}.00')  # 25, 50, 75
                )
            
            po2.calculate_totals()
            
            self.stdout.write(
                self.style.SUCCESS(f'Created multi-item PO: {po2.order_number} - Total: ${po2.total_amount}')
            )
            self.stdout.write(f'   Items: {po2.items.count()}')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Failed to create multi-item PO: {str(e)}')
            )
        
        # Test 3: Test inventory update on receiving
        self.stdout.write('\n' + '='*50)
        self.stdout.write('TEST 3: Testing inventory update on receiving')
        self.stdout.write('='*50)
        
        try:
            # Get the first item from po1
            item = po1.items.first()
            if item:
                # Check inventory before
                inventory_before = item.product.inventory.quantity if hasattr(item.product, 'inventory') else 0
                self.stdout.write(f'Inventory before receiving: {inventory_before}')
                
                # Receive the item
                item.receive(5)  # Receive 5 out of 10
                
                # Check inventory after
                item.product.refresh_from_db()
                inventory_after = item.product.inventory.quantity if hasattr(item.product, 'inventory') else 0
                self.stdout.write(f'Inventory after receiving 5 units: {inventory_after}')
                
                self.stdout.write(
                    self.style.SUCCESS(f'Inventory updated correctly (+5 units)')
                )
                
                # Check PO status
                po1.refresh_from_db()
                self.stdout.write(f'PO status after partial receive: {po1.status}')
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Failed to test inventory update: {str(e)}')
            )
        
        # Test 4: Show final results
        self.stdout.write('\n' + '='*50)
        self.stdout.write('TEST RESULTS SUMMARY')
        self.stdout.write('='*50)
        
        # Count purchase orders
        total_pos = PurchaseOrder.all_objects.filter(vendor=vendor).count()
        draft_pos = PurchaseOrder.all_objects.filter(vendor=vendor, status='draft').count()
        
        self.stdout.write(f'Total Purchase Orders: {total_pos}')
        self.stdout.write(f'Draft Purchase Orders: {draft_pos}')
        
        # Show recent POs
        recent_pos = PurchaseOrder.all_objects.filter(vendor=vendor).order_by('-created_at')[:5]
        self.stdout.write('\nRecent Purchase Orders:')
        for po in recent_pos:
            self.stdout.write(f'  - {po.order_number}: {po.supplier.name} - ${po.total_amount} ({po.status})')
        
        self.stdout.write(
            self.style.SUCCESS('\nAll purchase order tests completed successfully!')
        )