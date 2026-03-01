# Extended Features Documentation

## Overview
This document covers all the advanced features added to the Smart Multi-Vendor Inventory API.

## New Features

### 1. Customer Management
**Endpoints:**
- `GET/POST /api/v1/inventory/extended/customers/` - List/Create customers
- `GET/PUT/DELETE /api/v1/inventory/extended/customers/{id}/` - Retrieve/Update/Delete
- `GET /api/v1/inventory/extended/customers/{id}/purchase_history/` - Customer purchase history

**Features:**
- Customer types (Retail, Wholesale, VIP)
- Loyalty points tracking
- Total spent and order count
- Complete address management

### 2. Product Variants
**Endpoints:**
- `GET/POST /api/v1/inventory/extended/variants/` - Manage product variants

**Features:**
- Multiple variants per product (size, color, etc.)
- Separate SKU and pricing per variant
- Individual inventory tracking
- JSON attributes for flexible variant properties

### 3. Multi-Warehouse Support
**Endpoints:**
- `GET/POST /api/v1/inventory/extended/warehouses/` - Manage warehouses
- `GET /api/v1/inventory/extended/warehouses/{id}/inventory/` - Warehouse inventory

**Features:**
- Multiple warehouse locations
- Inventory tracking per warehouse
- Inter-warehouse transfers (coming soon)

### 4. Promotions & Discounts
**Endpoints:**
- `GET/POST /api/v1/inventory/extended/promotions/` - Manage promotions
- `GET /api/v1/inventory/extended/promotions/active/` - Get active promotions

**Features:**
- Percentage, fixed amount, and BOGO discounts
- Product-specific or store-wide promotions
- Time-based validity
- Usage limits and tracking

### 5. Returns & Refunds
**Endpoints:**
- `GET/POST /api/v1/inventory/extended/returns/` - Manage returns
- `POST /api/v1/inventory/extended/returns/{id}/approve/` - Approve return

**Features:**
- Return order management
- Automatic inventory restocking
- Refund tracking
- Return reason tracking

### 6. Webhooks
**Endpoints:**
- `GET/POST /api/v1/inventory/extended/webhooks/` - Manage webhooks
- `POST /api/v1/inventory/extended/webhooks/{id}/test/` - Test webhook

**Supported Events:**
- `sale.created` - New sale created
- `sale.completed` - Sale completed
- `inventory.low` - Low stock alert
- `product.created` - New product added
- `order.received` - Purchase order received

### 7. Dashboard Analytics
**Endpoints:**
- `GET /api/v1/inventory/extended/analytics/dashboard/?days=30` - Dashboard metrics
- `GET /api/v1/inventory/extended/analytics/sales-trend/?days=30` - Sales trend
- `GET /api/v1/inventory/extended/analytics/top-customers/?limit=10` - Top customers
- `GET /api/v1/inventory/extended/analytics/inventory-valuation/` - Inventory value
- `GET /api/v1/inventory/extended/analytics/category-performance/?days=30` - Category sales
- `GET /api/v1/inventory/extended/analytics/supplier-performance/` - Supplier metrics

**Metrics Provided:**
- Total revenue, orders, profit
- Average order value
- Profit margin
- Low stock and out-of-stock counts
- Top products by revenue
- Daily sales trends
- Customer lifetime value
- Inventory valuation (cost vs retail)
- Category performance
- Supplier performance

### 8. Bulk Operations
**Endpoints:**
- `POST /api/v1/inventory/extended/bulk/import-products/` - Import products CSV
- `GET /api/v1/inventory/extended/bulk/export-products/` - Export products CSV
- `POST /api/v1/inventory/extended/bulk/update-prices/` - Bulk price update
- `POST /api/v1/inventory/extended/bulk/adjust-inventory/` - Bulk inventory adjustment
- `GET /api/v1/inventory/extended/bulk/export-sales/?start_date=2024-01-01&end_date=2024-12-31` - Export sales
- `POST /api/v1/inventory/extended/bulk/import-customers/` - Import customers CSV

**CSV Formats:**

**Products Import:**
```csv
name,sku,category,price,cost,quantity,reorder_level,barcode,is_active
Widget A,WID-001,Electronics,99.99,50.00,100,10,123456789,true
```

**Customers Import:**
```csv
name,email,phone,customer_type,address_line1,city,state,postal_code,country
John Doe,john@example.com,555-1234,retail,123 Main St,New York,NY,10001,USA
```

**Bulk Price Update:**
```json
{
  "updates": [
    {"id": 1, "price": 99.99, "cost": 50.00},
    {"id": 2, "price": 149.99}
  ]
}
```

**Bulk Inventory Adjustment:**
```json
{
  "adjustments": [
    {"product_id": 1, "quantity": 10, "reason": "restock", "notes": "Weekly restock"},
    {"product_id": 2, "quantity": -5, "reason": "damage"}
  ]
}
```

### 9. Product Tags
**Endpoints:**
- `GET/POST /api/v1/inventory/extended/tags/` - Manage tags

**Features:**
- Tag products for better organization
- Search and filter by tags

### 10. Audit Logs
**Endpoints:**
- `GET /api/v1/inventory/extended/audit-logs/` - View audit trail

**Features:**
- Track all create/update/delete operations
- User and timestamp tracking
- IP address and user agent logging
- Change history in JSON format

### 11. Barcode Generation
**Endpoints:**
- `POST /api/v1/inventory/extended/utils/generate-barcode/` - Generate barcode image

**Request:**
```json
{
  "code": "123456789",
  "type": "code128"
}
```

**Supported Types:** code128, ean13, ean8, upca

### 12. Automated Tasks (Celery)
**Scheduled Tasks:**
- **Low Stock Alerts** - Daily at 9 AM
- **Customer Metrics Update** - Daily at 1 AM
- **Daily Reports Generation** - Daily at 2 AM
- **Audit Log Cleanup** - Weekly on Sunday at 3 AM
- **Scheduled Reports** - Every 30 minutes

### 13. Notifications
**Features:**
- Email notifications for low stock
- Sale confirmation emails
- Purchase order emails to suppliers
- Webhook triggers for real-time integrations

### 14. Product Images Gallery
**Features:**
- Multiple images per product
- Sort order management
- Alt text for accessibility

## Installation

1. Install new dependencies:
```bash
pip install -r requirements/extended.txt
```

2. Run migrations:
```bash
python manage.py makemigrations
python manage.py migrate --skip-checks
```

3. Update Celery beat schedule (already configured in settings)

4. Restart services:
```bash
# Django
python manage.py runserver

# Celery Worker
celery -A config worker --pool=solo -l info

# Celery Beat
celery -A config beat -l info
```

## Usage Examples

### Get Dashboard Metrics
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8000/api/v1/inventory/extended/analytics/dashboard/?days=30"
```

### Import Products
```bash
curl -X POST -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@products.csv" \
  "http://localhost:8000/api/v1/inventory/extended/bulk/import-products/"
```

### Create Promotion
```bash
curl -X POST -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Summer Sale",
    "discount_type": "percentage",
    "discount_value": 20,
    "start_date": "2024-06-01T00:00:00Z",
    "end_date": "2024-08-31T23:59:59Z",
    "is_active": true
  }' \
  "http://localhost:8000/api/v1/inventory/extended/promotions/"
```

### Bulk Update Prices
```bash
curl -X POST -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "updates": [
      {"id": 1, "price": 99.99},
      {"id": 2, "price": 149.99}
    ]
  }' \
  "http://localhost:8000/api/v1/inventory/extended/bulk/update-prices/"
```

## API Response Examples

### Dashboard Metrics Response
```json
{
  "period_days": 30,
  "total_revenue": 15420.50,
  "total_orders": 87,
  "avg_order_value": 177.25,
  "total_profit": 6890.30,
  "profit_margin": 44.68,
  "low_stock_count": 5,
  "out_of_stock_count": 2,
  "top_products": [
    {
      "product__name": "Widget A",
      "total_sold": 45,
      "revenue": 4499.55
    }
  ]
}
```

### Sales Trend Response
```json
[
  {
    "day": "2024-01-15",
    "revenue": 1250.00,
    "orders": 8
  },
  {
    "day": "2024-01-16",
    "revenue": 980.50,
    "orders": 6
  }
]
```

## Security Notes

1. All endpoints require authentication
2. Webhooks support HMAC signature verification
3. Audit logs track all changes with user and IP
4. Rate limiting applied (1000 requests/hour per user)

## Performance Tips

1. Use bulk operations for large datasets
2. Export/import via CSV for better performance
3. Analytics endpoints are optimized with database aggregations
4. Celery tasks run asynchronously to avoid blocking

## Future Enhancements

- Multi-currency support
- Advanced forecasting with ML
- Mobile app push notifications
- Real-time inventory sync
- Advanced reporting with charts
- Payment gateway integration
