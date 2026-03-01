# Generated manually to remove unique constraint on supplier name

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0005_alter_saleitem_subtotal'),
    ]

    operations = [
        migrations.RunSQL(
            "DROP INDEX IF EXISTS inventory_supplier_vendor_id_name_unique;",
            reverse_sql="CREATE UNIQUE INDEX inventory_supplier_vendor_id_name_unique ON inventory_supplier (vendor_id, name);"
        ),
    ]