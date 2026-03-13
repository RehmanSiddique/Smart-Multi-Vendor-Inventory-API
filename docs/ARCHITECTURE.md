# System Architecture - Extended Features

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLIENT LAYER                             │
│  (React Frontend / Mobile App / Third-party Integrations)       │
└────────────────────────┬────────────────────────────────────────┘
                         │ HTTP/HTTPS (REST API)
                         │ JWT Authentication
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                      API GATEWAY LAYER                           │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Django REST Framework + JWT Auth + Rate Limiting        │  │
│  │  - Authentication & Authorization                         │  │
│  │  - Request Validation                                     │  │
│  │  - Rate Limiting (1000/hour)                             │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    APPLICATION LAYER                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │  Core Inventory │  │    Extended     │  │    Analytics    │ │
│  │    - Products   │  │   - Customers   │  │   - Dashboard   │ │
│  │    - Sales      │  │   - Variants    │  │   - Trends      │ │
│  │    - Suppliers  │  │   - Warehouses  │  │   - Reports     │ │
│  │    - POs        │  │   - Promotions  │  │   - Metrics     │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
│                                                                   │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │  Bulk Ops       │  │  Notifications  │  │    Webhooks     │ │
│  │  - Import/Export│  │  - Email        │  │  - Event Trigger│ │
│  │  - Batch Update │  │  - SMS          │  │  - HMAC Sign    │ │
│  │  - CSV Process  │  │  - Alerts       │  │  - Retry Logic  │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    BACKGROUND TASKS LAYER                        │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    Celery Workers                         │  │
│  │  ┌────────────────┐  ┌────────────────┐  ┌────────────┐ │  │
│  │  │ Low Stock      │  │ Daily Reports  │  │ Cleanup    │ │  │
│  │  │ Alerts (9 AM)  │  │ (2 AM)         │  │ (Weekly)   │ │  │
│  │  └────────────────┘  └────────────────┘  └────────────┘ │  │
│  │  ┌────────────────┐  ┌────────────────┐                 │  │
│  │  │ Customer       │  │ Scheduled      │                 │  │
│  │  │ Metrics (1 AM) │  │ Reports (30min)│                 │  │
│  │  └────────────────┘  └────────────────┘                 │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    Celery Beat Scheduler                  │  │
│  │  - Cron-based task scheduling                            │  │
│  │  - Database-backed schedule                              │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                      DATA LAYER                                  │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │   PostgreSQL    │  │     Redis       │  │   File Storage  │ │
│  │  - Core Data    │  │  - Task Queue   │  │  - Images       │ │
│  │  - Extended     │  │  - Cache        │  │  - CSV Files    │ │
│  │  - Audit Logs   │  │  - Sessions     │  │  - Barcodes     │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow Diagrams

### 1. Analytics Request Flow
```
Client Request
    │
    ▼
JWT Authentication
    │
    ▼
Vendor Isolation (Middleware)
    │
    ▼
Analytics Service
    │
    ├─► Database Aggregation Queries
    │   ├─► Sales Data
    │   ├─► Inventory Data
    │   └─► Customer Data
    │
    ▼
JSON Response
```

### 2. Bulk Import Flow
```
CSV File Upload
    │
    ▼
File Validation
    │
    ▼
Parse CSV (pandas/csv)
    │
    ▼
Database Transaction
    │
    ├─► Create Products
    ├─► Create Inventory
    ├─► Create Audit Logs
    │
    ▼
Success/Error Report
```

### 3. Low Stock Alert Flow
```
Celery Beat (9 AM Daily)
    │
    ▼
Check Low Stock Task
    │
    ├─► Query Inventory
    │   └─► WHERE quantity <= reorder_level
    │
    ├─► For Each Low Stock Product:
    │   ├─► Send Email Alert
    │   ├─► Trigger Webhook
    │   └─► Create Notification
    │
    ▼
Task Complete
```

### 4. Webhook Trigger Flow
```
Event Occurs (e.g., Sale Created)
    │
    ▼
Notification Service
    │
    ├─► Find Active Webhooks
    │   └─► Filter by event type
    │
    ├─► For Each Webhook:
    │   ├─► Generate HMAC Signature
    │   ├─► HTTP POST to URL
    │   ├─► Update Success/Failure Count
    │   └─► Log Last Triggered
    │
    ▼
Continue Processing
```

## Database Schema Overview

### Core Models (Existing)
```
Vendor (Multi-tenant root)
  ├─► User
  ├─► Category
  ├─► Product
  │   └─► Inventory
  ├─► Supplier
  ├─► PurchaseOrder
  │   └─► PurchaseOrderItem
  └─► Sale
      └─► SaleItem
```

### Extended Models (New)
```
Vendor
  ├─► Customer
  ├─► Warehouse
  │   └─► WarehouseInventory
  ├─► Promotion
  ├─► Return
  │   └─► ReturnItem
  ├─► Webhook
  ├─► ProductTag
  └─► AuditLog

Product
  ├─► ProductVariant
  ├─► ProductImage
  └─► ProductTagRelation
```

## Service Layer Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Service Layer                           │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  AnalyticsService                                     │  │
│  │  - get_dashboard_metrics()                           │  │
│  │  - get_sales_trend()                                 │  │
│  │  - get_top_customers()                               │  │
│  │  - get_inventory_valuation()                         │  │
│  │  - get_category_performance()                        │  │
│  │  - get_supplier_performance()                        │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  BulkOperationsService                                │  │
│  │  - import_products_csv()                             │  │
│  │  - export_products_csv()                             │  │
│  │  - bulk_update_prices()                              │  │
│  │  - bulk_adjust_inventory()                           │  │
│  │  - export_sales_csv()                                │  │
│  │  - import_customers_csv()                            │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  NotificationService                                  │  │
│  │  - send_low_stock_alert()                            │  │
│  │  - send_sale_notification()                          │  │
│  │  - trigger_webhooks()                                │  │
│  │  - send_purchase_order_email()                       │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## API Endpoint Organization

```
/api/v1/
├── accounts/
│   ├── login/
│   ├── register/
│   └── profile/
│
├── inventory/
│   ├── categories/
│   ├── products/
│   ├── suppliers/
│   ├── purchase-orders/
│   ├── sales/
│   │
│   └── extended/
│       ├── customers/
│       ├── variants/
│       ├── warehouses/
│       ├── promotions/
│       ├── returns/
│       ├── webhooks/
│       ├── tags/
│       ├── audit-logs/
│       │
│       ├── analytics/
│       │   ├── dashboard/
│       │   ├── sales-trend/
│       │   ├── top-customers/
│       │   ├── inventory-valuation/
│       │   ├── category-performance/
│       │   └── supplier-performance/
│       │
│       ├── bulk/
│       │   ├── import-products/
│       │   ├── export-products/
│       │   ├── update-prices/
│       │   ├── adjust-inventory/
│       │   ├── export-sales/
│       │   └── import-customers/
│       │
│       └── utils/
│           └── generate-barcode/
│
└── reports/
    └── sales-reports/
```

## Security Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Security Layers                           │
│                                                               │
│  Layer 1: Authentication                                     │
│  ┌────────────────────────────────────────────────────┐    │
│  │  JWT Token Validation                              │    │
│  │  - Access Token (1 hour)                           │    │
│  │  - Refresh Token (7 days)                          │    │
│  └────────────────────────────────────────────────────┘    │
│                                                               │
│  Layer 2: Authorization                                      │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Permission Classes                                │    │
│  │  - IsAuthenticated                                 │    │
│  │  - Role-based (Admin, Manager, Staff)             │    │
│  └────────────────────────────────────────────────────┘    │
│                                                               │
│  Layer 3: Multi-tenancy                                      │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Tenant Middleware                                 │    │
│  │  - Vendor Isolation                                │    │
│  │  - Data Segregation                                │    │
│  └────────────────────────────────────────────────────┘    │
│                                                               │
│  Layer 4: Rate Limiting                                      │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Throttling                                        │    │
│  │  - Anonymous: 100/hour                             │    │
│  │  - Authenticated: 1000/hour                        │    │
│  └────────────────────────────────────────────────────┘    │
│                                                               │
│  Layer 5: Audit Logging                                      │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Track All Changes                                 │    │
│  │  - User, IP, Timestamp                             │    │
│  │  - Before/After Values                             │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

## Scalability Considerations

### Horizontal Scaling
```
Load Balancer
    │
    ├─► Django Instance 1
    ├─► Django Instance 2
    ├─► Django Instance 3
    │
    └─► Shared:
        ├─► PostgreSQL (Primary + Replicas)
        ├─► Redis (Cluster)
        └─► File Storage (S3/CDN)
```

### Celery Scaling
```
Celery Beat (1 instance)
    │
    ▼
Redis Queue
    │
    ├─► Celery Worker 1 (General tasks)
    ├─► Celery Worker 2 (Email tasks)
    ├─► Celery Worker 3 (Heavy processing)
    └─► Celery Worker N (Auto-scale)
```

## Performance Optimizations

1. **Database Level**
   - Indexes on all foreign keys
   - Composite indexes for common queries
   - Database connection pooling

2. **Application Level**
   - Query optimization (select_related, prefetch_related)
   - Pagination on all list endpoints
   - Caching with Redis

3. **Task Level**
   - Async processing with Celery
   - Batch operations for bulk updates
   - Scheduled tasks during off-peak hours

## Monitoring & Observability

```
Application Metrics
    ├─► Request/Response Times
    ├─► Error Rates
    ├─► API Endpoint Usage
    └─► User Activity

Background Tasks
    ├─► Task Success/Failure Rates
    ├─► Queue Length
    ├─► Processing Times
    └─► Retry Counts

Business Metrics
    ├─► Sales Volume
    ├─► Inventory Levels
    ├─► Customer Activity
    └─► Supplier Performance
```

## Deployment Architecture

```
Production Environment
    │
    ├─► Web Tier (Auto-scaling)
    │   ├─► Nginx (Reverse Proxy)
    │   └─► Gunicorn + Django
    │
    ├─► Worker Tier (Auto-scaling)
    │   └─► Celery Workers
    │
    ├─► Database Tier
    │   ├─► PostgreSQL Primary
    │   └─► PostgreSQL Replicas
    │
    ├─► Cache Tier
    │   └─► Redis Cluster
    │
    └─► Storage Tier
        ├─► S3 (Media files)
        └─► CloudFront (CDN)
```

---

This architecture supports:
- ✅ High availability
- ✅ Horizontal scaling
- ✅ Multi-tenancy
- ✅ Real-time processing
- ✅ Background jobs
- ✅ Security
- ✅ Monitoring
- ✅ Performance
