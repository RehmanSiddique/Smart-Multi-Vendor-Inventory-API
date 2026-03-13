from django.core.management.base import BaseCommand
from apps.inventory.models import Supplier, PurchaseOrder
from apps.accounts.models import Vendor


class Command(BaseCommand):
    help = 'Refresh suppliers by removing orphaned references and creating fresh test data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--vendor-id',
            type=int,
            help='Vendor ID to refresh suppliers for',
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
            # Get first vendor if no ID specified
            vendor = Vendor.objects.first()
            if not vendor:
                self.stdout.write(
                    self.style.ERROR('No vendors found')
                )
                return

        self.stdout.write(f'Refreshing suppliers for vendor: {vendor.business_name}')

        # Get current supplier count
        current_suppliers = Supplier.all_objects.filter(vendor=vendor)
        self.stdout.write(f'Current suppliers: {current_suppliers.count()}')

        # Create fresh test suppliers
        suppliers_data = [
            {
                'name': 'Tech Solutions Inc',
                'code': 'TECH001',
                'contact_person': 'John Smith',
                'email': 'john@techsolutions.com',
                'phone': '+1-555-0123',
                'address_line1': '123 Tech Street',
                'city': 'San Francisco',
                'state': 'CA',
                'postal_code': '94105',
                'country': 'USA',
                'payment_terms': 'Net 30',
                'lead_time_days': 5,
                'is_active': True,
            },
            {
                'name': 'Office Supplies Co',
                'code': 'OFF001',
                'contact_person': 'Jane Doe',
                'email': 'jane@officesupplies.com',
                'phone': '+1-555-0456',
                'address_line1': '456 Office Ave',
                'city': 'New York',
                'state': 'NY',
                'postal_code': '10001',
                'country': 'USA',
                'payment_terms': 'Net 15',
                'lead_time_days': 3,
                'is_active': True,
            },
            {
                'name': 'Electronics Warehouse',
                'code': 'ELEC001',
                'contact_person': 'Mike Johnson',
                'email': 'mike@electronics.com',
                'phone': '+1-555-0789',
                'address_line1': '789 Electronics Blvd',
                'city': 'Austin',
                'state': 'TX',
                'postal_code': '73301',
                'country': 'USA',
                'payment_terms': 'Net 45',
                'lead_time_days': 7,
                'is_active': True,
            }
        ]

        created_count = 0
        for supplier_data in suppliers_data:
            supplier, created = Supplier.objects.get_or_create(
                vendor=vendor,
                name=supplier_data['name'],
                defaults=supplier_data
            )
            if created:
                created_count += 1
                self.stdout.write(f'Created supplier: {supplier.name}')
            else:
                self.stdout.write(f'Supplier already exists: {supplier.name}')

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully refreshed suppliers. Created {created_count} new suppliers.'
            )
        )

        # Show final count
        final_count = Supplier.all_objects.filter(vendor=vendor).count()
        self.stdout.write(f'Total suppliers now: {final_count}')