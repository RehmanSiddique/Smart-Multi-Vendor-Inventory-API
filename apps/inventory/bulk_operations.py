"""
Bulk operations service for import/export and batch processing.
"""

import csv
import io
from decimal import Decimal
from django.db import transaction
from .models import Product, Category, Inventory, Supplier
from .models_extended import Customer


class BulkOperationsService:
    """Service for bulk operations."""
    
    def __init__(self, vendor):
        self.vendor = vendor
    
    def import_products_csv(self, csv_file):
        """Import products from CSV file."""
        results = {'success': 0, 'errors': []}
        
        try:
            decoded_file = csv_file.read().decode('utf-8')
            csv_reader = csv.DictReader(io.StringIO(decoded_file))
            
            with transaction.atomic():
                for row_num, row in enumerate(csv_reader, start=2):
                    try:
                        # Get or create category
                        category = None
                        if row.get('category'):
                            category, _ = Category.objects.get_or_create(
                                vendor=self.vendor,
                                name=row['category']
                            )
                        
                        # Create product
                        product = Product.objects.create(
                            vendor=self.vendor,
                            name=row['name'],
                            sku=row['sku'],
                            barcode=row.get('barcode', ''),
                            description=row.get('description', ''),
                            category=category,
                            price=Decimal(row['price']),
                            cost=Decimal(row.get('cost', 0)),
                            is_active=row.get('is_active', 'true').lower() == 'true'
                        )
                        
                        # Create inventory
                        Inventory.objects.create(
                            product=product,
                            quantity=int(row.get('quantity', 0)),
                            reorder_level=int(row.get('reorder_level', 10))
                        )
                        
                        results['success'] += 1
                    except Exception as e:
                        results['errors'].append(f"Row {row_num}: {str(e)}")
        
        except Exception as e:
            results['errors'].append(f"File error: {str(e)}")
        
        return results
    
    def export_products_csv(self):
        """Export products to CSV."""
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow([
            'SKU', 'Name', 'Category', 'Price', 'Cost', 'Quantity',
            'Reorder Level', 'Barcode', 'Is Active'
        ])
        
        # Data
        products = Product.objects.filter(vendor=self.vendor).select_related('category', 'inventory')
        
        for product in products:
            try:
                inventory = product.inventory
                quantity = inventory.quantity
                reorder_level = inventory.reorder_level
            except Inventory.DoesNotExist:
                quantity = 0
                reorder_level = 0
            
            writer.writerow([
                product.sku,
                product.name,
                product.category.name if product.category else '',
                product.price,
                product.cost or 0,
                quantity,
                reorder_level,
                product.barcode,
                'Yes' if product.is_active else 'No'
            ])
        
        return output.getvalue()
    
    def bulk_update_prices(self, updates):
        """
        Bulk update product prices.
        updates: [{'id': 1, 'price': 99.99, 'cost': 50.00}, ...]
        """
        results = {'success': 0, 'errors': []}
        
        with transaction.atomic():
            for update in updates:
                try:
                    product = Product.objects.get(
                        id=update['id'],
                        vendor=self.vendor
                    )
                    
                    if 'price' in update:
                        product.price = Decimal(str(update['price']))
                    if 'cost' in update:
                        product.cost = Decimal(str(update['cost']))
                    
                    product.save()
                    results['success'] += 1
                except Product.DoesNotExist:
                    results['errors'].append(f"Product {update['id']} not found")
                except Exception as e:
                    results['errors'].append(f"Product {update['id']}: {str(e)}")
        
        return results
    
    def bulk_adjust_inventory(self, adjustments):
        """
        Bulk inventory adjustments.
        adjustments: [{'product_id': 1, 'quantity': 10, 'reason': 'restock'}, ...]
        """
        results = {'success': 0, 'errors': []}
        
        with transaction.atomic():
            for adj in adjustments:
                try:
                    product = Product.objects.get(
                        id=adj['product_id'],
                        vendor=self.vendor
                    )
                    
                    inventory = product.inventory
                    inventory.adjust_inventory(
                        quantity_change=adj['quantity'],
                        reason=adj.get('reason', 'adjustment'),
                        notes=adj.get('notes', ''),
                        user=None
                    )
                    
                    results['success'] += 1
                except Product.DoesNotExist:
                    results['errors'].append(f"Product {adj['product_id']} not found")
                except Inventory.DoesNotExist:
                    results['errors'].append(f"No inventory for product {adj['product_id']}")
                except Exception as e:
                    results['errors'].append(f"Product {adj['product_id']}: {str(e)}")
        
        return results
    
    def export_sales_csv(self, start_date, end_date):
        """Export sales to CSV."""
        from .models import Sale
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow([
            'Sale Number', 'Date', 'Customer', 'Status', 'Subtotal',
            'Tax', 'Shipping', 'Discount', 'Total', 'Payment Method'
        ])
        
        # Data
        sales = Sale.objects.filter(
            vendor=self.vendor,
            sale_date__gte=start_date,
            sale_date__lte=end_date
        ).order_by('-sale_date')
        
        for sale in sales:
            writer.writerow([
                sale.sale_number,
                sale.sale_date.strftime('%Y-%m-%d %H:%M'),
                sale.customer_name,
                sale.get_status_display(),
                sale.subtotal,
                sale.tax,
                sale.shipping,
                sale.discount,
                sale.total,
                sale.get_payment_method_display()
            ])
        
        return output.getvalue()
    
    def import_customers_csv(self, csv_file):
        """Import customers from CSV."""
        results = {'success': 0, 'errors': []}
        
        try:
            decoded_file = csv_file.read().decode('utf-8')
            csv_reader = csv.DictReader(io.StringIO(decoded_file))
            
            with transaction.atomic():
                for row_num, row in enumerate(csv_reader, start=2):
                    try:
                        Customer.objects.create(
                            vendor=self.vendor,
                            name=row['name'],
                            email=row.get('email', ''),
                            phone=row.get('phone', ''),
                            customer_type=row.get('customer_type', 'retail'),
                            address_line1=row.get('address_line1', ''),
                            city=row.get('city', ''),
                            state=row.get('state', ''),
                            postal_code=row.get('postal_code', ''),
                            country=row.get('country', 'USA')
                        )
                        results['success'] += 1
                    except Exception as e:
                        results['errors'].append(f"Row {row_num}: {str(e)}")
        
        except Exception as e:
            results['errors'].append(f"File error: {str(e)}")
        
        return results
