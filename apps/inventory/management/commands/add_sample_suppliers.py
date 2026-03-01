from django.core.management.base import BaseCommand
from apps.inventory.models import Supplier
from apps.accounts.models import Vendor


class Command(BaseCommand):
    help = 'Add sample suppliers to the database'

    def handle(self, *args, **options):
        # Get the first vendor (you can modify this to target specific vendor)
        try:
            vendor = Vendor.objects.first()
            if not vendor:
                self.stdout.write(self.style.ERROR('No vendor found. Please create a vendor first.'))
                return
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error finding vendor: {e}'))
            return

        suppliers_data = [
            {
                'name': 'TechParts Solutions',
                'contact_person': 'John Smith',
                'email': 'john@techparts.com',
                'phone': '+1-555-0123',
                'address_line1': '123 Technology Drive, Silicon Valley, CA 94025',
                'website': 'https://techparts.com',
                'tax_id': '12-3456789',
                'payment_terms': 'Net 30',
                'lead_time_days': 5,
                'notes': 'Reliable supplier for electronic components and computer parts',
                'is_active': True,
            },
            {
                'name': 'Office Depot Pro',
                'contact_person': 'Sarah Johnson',
                'email': 'sarah.j@officedepot.com',
                'phone': '+1-555-0456',
                'address_line1': '456 Business Park, New York, NY 10001',
                'website': 'https://officedepot.com',
                'tax_id': '98-7654321',
                'payment_terms': 'Net 15',
                'lead_time_days': 3,
                'notes': 'Fast delivery for office supplies and stationery',
                'is_active': True,
            },
            {
                'name': 'Global Manufacturing Inc',
                'contact_person': 'Mike Chen',
                'email': 'mike@globalmanuf.com',
                'phone': '+1-555-0789',
                'address_line1': '789 Industrial Blvd, Detroit, MI 48201',
                'website': 'https://globalmanuf.com',
                'tax_id': '55-1122334',
                'payment_terms': 'Net 45',
                'lead_time_days': 14,
                'notes': 'Large scale manufacturing partner for custom products',
                'is_active': True,
            },
            {
                'name': 'Local Supplies Co',
                'contact_person': 'Emma Davis',
                'email': 'emma@localsupplies.com',
                'phone': '+1-555-0321',
                'address_line1': '321 Main Street, Anytown, TX 75001',
                'website': '',
                'tax_id': '77-9988776',
                'payment_terms': 'Due on receipt',
                'lead_time_days': 2,
                'notes': 'Quick local supplier for urgent needs',
                'is_active': True,
            }
        ]

        created_count = 0
        for supplier_data in suppliers_data:
            supplier_data['vendor'] = vendor
            
            # Check if supplier already exists
            if not Supplier.objects.filter(vendor=vendor, name=supplier_data['name']).exists():
                Supplier.objects.create(**supplier_data)
                created_count += 1
                self.stdout.write(f"Created supplier: {supplier_data['name']}")
            else:
                self.stdout.write(f"Supplier already exists: {supplier_data['name']}")

        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {created_count} suppliers for vendor: {vendor.business_name}')
        )