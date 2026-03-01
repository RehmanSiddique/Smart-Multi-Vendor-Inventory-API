from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Remove unique constraint from supplier table'

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            try:
                # Get table info
                cursor.execute("PRAGMA table_info(inventory_supplier);")
                columns = cursor.fetchall()
                self.stdout.write(f"Current table structure: {columns}")
                
                # Get indexes
                cursor.execute("PRAGMA index_list(inventory_supplier);")
                indexes = cursor.fetchall()
                self.stdout.write(f"Current indexes: {indexes}")
                
                # Try to drop the unique constraint by recreating table
                cursor.execute("""
                    CREATE TABLE inventory_supplier_temp AS 
                    SELECT * FROM inventory_supplier;
                """)
                
                cursor.execute("DROP TABLE inventory_supplier;")
                
                cursor.execute("""
                    CREATE TABLE inventory_supplier (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name VARCHAR(200) NOT NULL,
                        code VARCHAR(50) NOT NULL DEFAULT '',
                        contact_person VARCHAR(100) NOT NULL DEFAULT '',
                        email VARCHAR(254) NOT NULL DEFAULT '',
                        phone VARCHAR(20) NOT NULL DEFAULT '',
                        website VARCHAR(200) NOT NULL DEFAULT '',
                        address_line1 VARCHAR(255) NOT NULL DEFAULT '',
                        address_line2 VARCHAR(255) NOT NULL DEFAULT '',
                        city VARCHAR(100) NOT NULL DEFAULT '',
                        state VARCHAR(100) NOT NULL DEFAULT '',
                        postal_code VARCHAR(20) NOT NULL DEFAULT '',
                        country VARCHAR(100) NOT NULL DEFAULT 'USA',
                        tax_id VARCHAR(50) NOT NULL DEFAULT '',
                        payment_terms VARCHAR(100) NOT NULL DEFAULT 'Net 30',
                        lead_time_days INTEGER NOT NULL DEFAULT 7,
                        minimum_order_value DECIMAL(10, 2) NULL,
                        is_active BOOLEAN NOT NULL DEFAULT 1,
                        is_preferred BOOLEAN NOT NULL DEFAULT 0,
                        notes TEXT NOT NULL DEFAULT '',
                        vendor_id INTEGER NOT NULL,
                        created_at DATETIME NOT NULL,
                        updated_at DATETIME NOT NULL,
                        FOREIGN KEY (vendor_id) REFERENCES accounts_vendor (id)
                    );
                """)
                
                cursor.execute("""
                    INSERT INTO inventory_supplier 
                    SELECT * FROM inventory_supplier_temp;
                """)
                
                cursor.execute("DROP TABLE inventory_supplier_temp;")
                
                # Create indexes (without unique constraint)
                cursor.execute("""
                    CREATE INDEX inventory_supplier_vendor_id_is_active_idx 
                    ON inventory_supplier (vendor_id, is_active);
                """)
                
                cursor.execute("""
                    CREATE INDEX inventory_supplier_vendor_id_is_preferred_idx 
                    ON inventory_supplier (vendor_id, is_preferred);
                """)
                
                self.stdout.write(self.style.SUCCESS('Successfully removed unique constraint from supplier table'))
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error: {e}'))