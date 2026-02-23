"""
Django management command to create test vendors and users.
Run with: python manage.py create_test_vendors
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.accounts.models import Vendor
from django.utils import timezone

User = get_user_model()

class Command(BaseCommand):
    help = 'Creates test vendors and users for development'
    
    def handle(self, *args, **options):
        self.stdout.write('Creating test vendors...')
        
        # First, create vendors without users
        vendor1 = Vendor.objects.create(
            business_name='Acme Corporation',
            subdomain='acme',
            tier='professional',
            is_active=True
        )
        
        vendor2 = Vendor.objects.create(
            business_name='Beta Industries',
            subdomain='beta',
            tier='basic',
            is_active=True
        )
        
        self.stdout.write(self.style.SUCCESS(f'Created vendor: {vendor1.business_name}'))
        self.stdout.write(self.style.SUCCESS(f'Created vendor: {vendor2.business_name}'))
        
        # Now create users and link them to vendors
        # Note: We're not setting vendor context, so User.objects.create_user 
        # will work without tenant filtering
        
        # Create admin for Acme
        acme_admin = User.objects.create_user(
            email='admin@acme.com',
            password='testpass123',
            first_name='Acme',
            last_name='Admin',
            role='vendor_admin',
            is_active=True,
            email_verified_at=timezone.now()
        )
        acme_admin.vendor = vendor1
        acme_admin.save()
        self.stdout.write(self.style.SUCCESS(f'Created user: {acme_admin.email}'))
        
        # Create staff for Acme
        acme_staff = User.objects.create_user(
            email='staff@acme.com',
            password='testpass123',
            first_name='Acme',
            last_name='Staff',
            role='vendor_staff',
            is_active=True,
            email_verified_at=timezone.now()
        )
        acme_staff.vendor = vendor1
        acme_staff.save()
        self.stdout.write(self.style.SUCCESS(f'Created user: {acme_staff.email}'))
        
        # Create admin for Beta
        beta_admin = User.objects.create_user(
            email='admin@beta.com',
            password='testpass123',
            first_name='Beta',
            last_name='Admin',
            role='vendor_admin',
            is_active=True,
            email_verified_at=timezone.now()
        )
        beta_admin.vendor = vendor2
        beta_admin.save()
        self.stdout.write(self.style.SUCCESS(f'Created user: {beta_admin.email}'))
        
        # Create a platform admin (superuser)
        platform_admin = User.objects.create_superuser(
            email='platform@smvia.com',
            password='admin123',
            first_name='Platform',
            last_name='Admin',
            role='platform_admin'
        )
        self.stdout.write(self.style.SUCCESS(f'Created platform admin: {platform_admin.email}'))
        
        self.stdout.write(self.style.SUCCESS('=' * 50))
        self.stdout.write(self.style.SUCCESS('Test data created successfully!'))
        self.stdout.write(self.style.SUCCESS('=' * 50))
        
        # Summary
        self.stdout.write(f'Vendors created: 2')
        self.stdout.write(f'Users created: 4')
        self.stdout.write('\nLogin credentials:')
        self.stdout.write('  admin@acme.com / testpass123 (Acme Admin)')
        self.stdout.write('  staff@acme.com / testpass123 (Acme Staff)')
        self.stdout.write('  admin@beta.com / testpass123 (Beta Admin)')
        self.stdout.write('  platform@smvia.com / admin123 (Platform Admin)')