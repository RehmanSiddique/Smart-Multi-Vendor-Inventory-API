# Smart Multi-Vendor Inventory System — Backend API

A production-ready, multi-tenant inventory management REST API built with **Django** and **Django REST Framework**. Supports multiple vendors with strict data isolation, JWT authentication, analytics, and bulk operations.

---

## 🚀 Tech Stack

| Layer        | Technology                     |
|--------------|-------------------------------|
| Framework    | Django 4.x + Django REST Framework |
| Auth         | JWT (SimpleJWT)               |
| Database     | SQLite (dev) / PostgreSQL (prod) |
| Multi-Tenancy| Custom Vendor middleware       |
| Task Queue   | Celery + Redis (optional)      |
| Analytics    | Custom AnalyticsService        |

---

## 📁 Project Structure

```
Backend/
├── apps/
│   ├── accounts/          # User accounts, vendor management, JWT auth
│   │   └── management/commands/   # create_test_vendors management command
│   ├── inventory/         # Core inventory: products, categories, suppliers
│   │   ├── models.py      # Core models (Product, Sale, PurchaseOrder, Inventory)
│   │   ├── models_extended.py  # Extended models (Customer, Warehouse, Promotion)
│   │   ├── views.py       # Core API views
│   │   ├── views_extended.py   # Extended API views + analytics endpoints
│   │   ├── serializers.py
│   │   ├── analytics.py   # AnalyticsService: revenue, top products, valuations
│   │   ├── bulk_operations.py  # CSV import/export
│   │   ├── notifications.py    # Webhook notifications
│   │   └── tasks.py            # Celery async tasks
│   ├── forecast/          # Demand forecasting
│   └── reports/           # Report generation
├── config/
│   └── settings/          # base.py, development.py, production.py
├── docs/                  # Technical documentation
│   ├── ARCHITECTURE.md
│   ├── API_TESTING_GUIDE.md
│   └── ...
├── requirements/
│   ├── base.txt
│   ├── development.txt
│   └── production.txt
├── manage.py
└── .env.example
```

---

## ⚡ Quick Setup

### 1. Clone and create virtual environment
```bash
git clone <repo-url>
cd Backend
python -m venv venv
venv\Scripts\activate      # Windows
source venv/bin/activate   # macOS/Linux
```

### 2. Install dependencies
```bash
pip install -r requirements/development.txt
```

### 3. Configure environment
```bash
cp .env.example .env
# Edit .env with your settings
```

### 4. Run migrations and create test data
```bash
python manage.py migrate
python manage.py create_test_vendors
```

### 5. Start the development server
```bash
python manage.py runserver
```

The API is available at `http://localhost:8000/api/v1/`

---

## 🔐 Test Credentials

| Role            | Email                  | Password     |
|-----------------|------------------------|-------------|
| Acme Admin      | admin@acme.com         | testpass123 |
| Acme Staff      | staff@acme.com         | testpass123 |
| Beta Admin      | admin@beta.com         | testpass123 |
| Platform Admin  | platform@smvia.com     | admin123    |

---

## 🌐 API Overview

### Authentication
```
POST /api/v1/auth/login/       # Get JWT tokens
POST /api/v1/auth/refresh/     # Refresh access token
POST /api/v1/auth/register/    # Register new vendor
```

### Core Inventory
```
GET/POST   /api/v1/inventory/products/
GET/POST   /api/v1/inventory/sales/
GET/POST   /api/v1/inventory/purchase-orders/
GET/POST   /api/v1/inventory/suppliers/
GET/POST   /api/v1/inventory/categories/
```

### Analytics
```
GET /api/v1/inventory/extended/analytics/dashboard/?days=30
GET /api/v1/inventory/extended/analytics/sales-trend/?days=30
GET /api/v1/inventory/extended/analytics/inventory-valuation/
GET /api/v1/inventory/extended/analytics/category-performance/
GET /api/v1/inventory/extended/analytics/top-customers/
```

### Extended Features
```
GET/POST   /api/v1/inventory/extended/customers/
GET/POST   /api/v1/inventory/extended/warehouses/
GET/POST   /api/v1/inventory/extended/promotions/
GET/POST   /api/v1/inventory/extended/returns/
```

Full API documentation is available in `docs/API_TESTING_GUIDE.md`.

---

## 🏗️ Multi-Tenancy Architecture

All data is scoped per **Vendor** using:
- A custom middleware (`apps/accounts/middleware.py`) that sets vendor context on each request.
- A `TenantManager` (`all_objects` vs `objects`) on all models to enforce isolation.
- JWT tokens embed vendor context to ensure API calls are always scoped correctly.

---

## 📄 License

MIT
