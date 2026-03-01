# API Testing Guide

## Prerequisites
1. Get your authentication token
2. Replace `YOUR_TOKEN` in commands below
3. Ensure all services are running

## Get Authentication Token
```bash
curl -X POST http://localhost:8000/api/v1/accounts/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@acme.com", "password": "your-password"}'
```

Save the `access` token from response.

---

## 1. Test Analytics Dashboard

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8000/api/v1/inventory/extended/analytics/dashboard/?days=30"
```

**Expected:** JSON with revenue, orders, profit, top products

---

## 2. Test Sales Trend

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8000/api/v1/inventory/extended/analytics/sales-trend/?days=7"
```

**Expected:** Array of daily sales data

---

## 3. Test Inventory Valuation

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8000/api/v1/inventory/extended/analytics/inventory-valuation/"
```

**Expected:** Total inventory value at cost and retail

---

## 4. Create Customer

```bash
curl -X POST http://localhost:8000/api/v1/inventory/extended/customers/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Jane Smith",
    "email": "jane@example.com",
    "phone": "555-5678",
    "customer_type": "retail",
    "address_line1": "456 Oak Ave",
    "city": "Los Angeles",
    "state": "CA",
    "postal_code": "90001",
    "country": "USA"
  }'
```

**Expected:** Customer object with ID

---

## 5. List Customers

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8000/api/v1/inventory/extended/customers/"
```

**Expected:** Paginated list of customers

---

## 6. Create Promotion

```bash
curl -X POST http://localhost:8000/api/v1/inventory/extended/promotions/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Black Friday Sale",
    "code": "BLACKFRIDAY",
    "discount_type": "percentage",
    "discount_value": 25,
    "start_date": "2024-11-29T00:00:00Z",
    "end_date": "2024-11-30T23:59:59Z",
    "is_active": true
  }'
```

**Expected:** Promotion object with ID

---

## 7. Get Active Promotions

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8000/api/v1/inventory/extended/promotions/active/"
```

**Expected:** List of currently active promotions

---

## 8. Create Warehouse

```bash
curl -X POST http://localhost:8000/api/v1/inventory/extended/warehouses/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Main Warehouse",
    "code": "WH-001",
    "address_line1": "789 Industrial Blvd",
    "city": "Chicago",
    "state": "IL",
    "country": "USA",
    "manager_name": "Bob Johnson",
    "phone": "555-9999",
    "is_active": true
  }'
```

**Expected:** Warehouse object with ID

---

## 9. Export Products to CSV

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8000/api/v1/inventory/extended/bulk/export-products/" \
  -o products_export.csv
```

**Expected:** CSV file downloaded

---

## 10. Bulk Update Prices

```bash
curl -X POST http://localhost:8000/api/v1/inventory/extended/bulk/update-prices/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "updates": [
      {"id": 1, "price": 99.99, "cost": 50.00},
      {"id": 2, "price": 149.99, "cost": 75.00}
    ]
  }'
```

**Expected:** Success count and any errors

---

## 11. Bulk Adjust Inventory

```bash
curl -X POST http://localhost:8000/api/v1/inventory/extended/bulk/adjust-inventory/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "adjustments": [
      {"product_id": 1, "quantity": 50, "reason": "restock", "notes": "Weekly delivery"},
      {"product_id": 2, "quantity": -10, "reason": "damage", "notes": "Water damage"}
    ]
  }'
```

**Expected:** Success count and any errors

---

## 12. Create Webhook

```bash
curl -X POST http://localhost:8000/api/v1/inventory/extended/webhooks/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Slack Notifications",
    "url": "https://hooks.slack.com/services/YOUR/WEBHOOK/URL",
    "events": ["sale.created", "inventory.low"],
    "is_active": true,
    "secret": "my-secret-key"
  }'
```

**Expected:** Webhook object with ID

---

## 13. Test Webhook

```bash
curl -X POST http://localhost:8000/api/v1/inventory/extended/webhooks/1/test/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Expected:** Test webhook sent confirmation

---

## 14. Create Product Tag

```bash
curl -X POST http://localhost:8000/api/v1/inventory/extended/tags/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Best Seller",
    "slug": "best-seller"
  }'
```

**Expected:** Tag object with ID

---

## 15. View Audit Logs

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8000/api/v1/inventory/extended/audit-logs/"
```

**Expected:** List of recent changes

---

## 16. Generate Barcode

```bash
curl -X POST http://localhost:8000/api/v1/inventory/extended/utils/generate-barcode/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "123456789012",
    "type": "code128"
  }' \
  -o barcode.png
```

**Expected:** PNG barcode image downloaded

---

## 17. Create Product Variant

```bash
curl -X POST http://localhost:8000/api/v1/inventory/extended/variants/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "product": 1,
    "name": "Large Red",
    "sku": "PROD-001-LG-RED",
    "attributes": {"size": "Large", "color": "Red"},
    "price": 29.99,
    "cost": 15.00,
    "quantity": 100,
    "is_active": true
  }'
```

**Expected:** Variant object with ID

---

## 18. Create Return

```bash
curl -X POST http://localhost:8000/api/v1/inventory/extended/returns/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "sale": 1,
    "reason": "Product defective",
    "refund_amount": 99.99,
    "status": "pending"
  }'
```

**Expected:** Return object with return_number

---

## 19. Approve Return

```bash
curl -X POST http://localhost:8000/api/v1/inventory/extended/returns/1/approve/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"restock": true}'
```

**Expected:** Status approved confirmation

---

## 20. Get Top Customers

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8000/api/v1/inventory/extended/analytics/top-customers/?limit=5"
```

**Expected:** Top 5 customers by spending

---

## 21. Get Category Performance

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8000/api/v1/inventory/extended/analytics/category-performance/?days=30"
```

**Expected:** Sales by category

---

## 22. Get Supplier Performance

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8000/api/v1/inventory/extended/analytics/supplier-performance/"
```

**Expected:** Supplier metrics

---

## 23. Export Sales

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8000/api/v1/inventory/extended/bulk/export-sales/?start_date=2024-01-01&end_date=2024-12-31" \
  -o sales_export.csv
```

**Expected:** CSV file with sales data

---

## Import Tests

### Prepare CSV Files

**products.csv:**
```csv
name,sku,category,price,cost,quantity,reorder_level,barcode,is_active
Test Product 1,TEST-001,Electronics,99.99,50.00,100,10,1234567890,true
Test Product 2,TEST-002,Electronics,149.99,75.00,50,5,0987654321,true
```

**customers.csv:**
```csv
name,email,phone,customer_type,address_line1,city,state,postal_code,country
Test Customer 1,test1@example.com,555-0001,retail,123 Test St,New York,NY,10001,USA
Test Customer 2,test2@example.com,555-0002,wholesale,456 Test Ave,Boston,MA,02101,USA
```

### Import Products

```bash
curl -X POST http://localhost:8000/api/v1/inventory/extended/bulk/import-products/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@products.csv"
```

**Expected:** Success count and any errors

### Import Customers

```bash
curl -X POST http://localhost:8000/api/v1/inventory/extended/bulk/import-customers/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@customers.csv"
```

**Expected:** Success count and any errors

---

## Verification Checklist

- [ ] Dashboard metrics load successfully
- [ ] Sales trend shows data
- [ ] Can create and list customers
- [ ] Can create promotions
- [ ] Can create warehouses
- [ ] Can export products to CSV
- [ ] Can import products from CSV
- [ ] Bulk price update works
- [ ] Bulk inventory adjustment works
- [ ] Can create webhooks
- [ ] Can generate barcodes
- [ ] Can create product variants
- [ ] Can create and approve returns
- [ ] Audit logs are being created
- [ ] All analytics endpoints return data

---

## Troubleshooting

**401 Unauthorized:**
- Check your token is valid
- Token format: `Bearer YOUR_TOKEN`

**404 Not Found:**
- Ensure URL is correct
- Check service is running

**400 Bad Request:**
- Verify JSON format
- Check required fields

**500 Server Error:**
- Check Django logs
- Verify database migrations ran
- Ensure Redis is running

---

## Performance Testing

Test with larger datasets:

```bash
# Create 100 customers
for i in {1..100}; do
  curl -X POST http://localhost:8000/api/v1/inventory/extended/customers/ \
    -H "Authorization: Bearer YOUR_TOKEN" \
    -H "Content-Type: application/json" \
    -d "{\"name\": \"Customer $i\", \"email\": \"customer$i@test.com\"}"
done
```

---

## Success Criteria

All tests should:
1. Return 200/201 status codes
2. Return valid JSON (except CSV exports)
3. Complete in < 2 seconds
4. Show data in database
5. Create audit log entries

---

## Next Steps After Testing

1. Configure email settings for notifications
2. Set up real webhook URLs
3. Import production data
4. Configure Celery beat schedule
5. Set up monitoring and alerts
