# Smart Multi-Vendor Inventory System — Backend API

A multi-tenant inventory management REST API built with **Django 4.2** and **Django REST Framework**.  
Supports multiple vendors with strict data isolation, JWT authentication, analytics, and bulk operations.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | Django 4.2 + Django REST Framework |
| Auth | JWT via SimpleJWT |
| Database | SQLite (development) / PostgreSQL (production) |
| Multi-Tenancy | Custom vendor middleware |
| Task Queue | Celery + Redis (optional) |
| API Docs | Swagger (drf-yasg) |

---

## Project Structure

```
Backend/
├── apps/
│   ├── accounts/          # Users, vendors, JWT auth, middleware, permissions
│   ├── inventory/         # Products, sales, purchase orders, analytics, bulk ops
│   └── reports/           # Report generation
├── config/
│   ├── settings/
│   │   ├── base.py        # Shared settings
│   │   ├── development.py # Dev overrides (SQLite, debug toolbar, console email)
│   │   └── production.py  # Prod overrides (PostgreSQL, security headers)
│   ├── urls.py
│   ├── api_urls.py
│   └── celery.py
├── requirements/
│   ├── base.txt           # Core Django + DRF
│   ├── development.txt    # Dev tools, testing, linting
│   ├── extended.txt       # Barcode, Excel, image support
│   └── celery.txt         # Celery + Redis
├── docs/                  # API guides and architecture docs
├── manage.py
├── .env.example           # Copy this to .env and fill in your values
└── db.sqlite3             # Auto-created on first migrate
```

---

## Prerequisites

Install these on your machine before starting:

- **Python 3.10+** → https://www.python.org/downloads/
- **Git** → https://git-scm.com/
- **Redis** *(optional — only needed for Celery background tasks)* → https://redis.io/

---

## Step 1 — Clone the Repository

```bash
git clone <repo-url>
cd Backend
```

---

## Step 2 — Create and Activate a Virtual Environment

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**macOS / Linux:**
```bash
python -m venv venv
source venv/bin/activate
```

You will see `(venv)` in your terminal prompt once activated.

---

## Step 3 — Install Dependencies

```bash
pip install -r requirements/development.txt
```

Optional — barcode generation, Excel export, image support:

```bash
pip install -r requirements/extended.txt
```

Optional — Celery background tasks:

```bash
pip install -r requirements/celery.txt
```

---

## Step 4 — Configure Environment Variables

```bash
# Windows
copy .env.example .env

# macOS / Linux
cp .env.example .env
```

Open `.env` and fill in at minimum:

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
DJANGO_SETTINGS_MODULE=config.settings.development
ALLOWED_HOSTS=localhost,127.0.0.1
```

**Generate a secure SECRET_KEY:**

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

> All other variables in `.env` (email, Redis, PostgreSQL) are optional for local development.

---

## Step 5 — Run Database Migrations

```bash
python manage.py migrate
```

This creates all tables in `db.sqlite3`.

---

## Step 6 — Seed Test Vendors and Users

```bash
python manage.py create_test_vendors
```

This creates two vendors and four test users:

| Role | Email | Password |
|---|---|---|
| Acme Admin | admin@acme.com | testpass123 |
| Acme Staff | staff@acme.com | testpass123 |
| Beta Admin | admin@beta.com | testpass123 |
| Platform Admin | platform@smvia.com | admin123 |

---

## Step 7 — Start the Development Server

```bash
python manage.py runserver
```

- API: **http://localhost:8000/api/v1/**
- Swagger docs: **http://localhost:8000/swagger/**
- ReDoc: **http://localhost:8000/redoc/**

---

## Step 8 — (Optional) Celery Background Tasks

Celery handles scheduled tasks: low-stock alerts, daily reports, customer metric updates.  
Redis must be running first on port **6380**.

Open three separate terminals (with venv activated in each):

**Terminal 1 — Redis:**
```bash
redis-server --port 6380
```

**Terminal 2 — Celery Worker:**
```bash
celery -A config worker --pool=solo -l info
```

**Terminal 3 — Celery Beat (scheduler):**
```bash
celery -A config beat -l info
```

---

## How Authentication Works

1. `POST /api/v1/auth/login/` with `email` and `password`
2. Receive an `access` token (1 hour) and a `refresh` token (7 days)
3. Pass the access token in every request header:
   ```
   Authorization: Bearer <access_token>
   ```
4. When the access token expires, call `POST /api/v1/auth/refresh/` with the refresh token

---

## API Endpoints

### Authentication
```
POST   /api/v1/auth/login/        Get JWT access + refresh tokens
POST   /api/v1/auth/refresh/      Refresh access token
POST   /api/v1/auth/register/     Register a new vendor
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
GET   /api/v1/inventory/extended/analytics/dashboard/?days=30
GET   /api/v1/inventory/extended/analytics/sales-trend/?days=30
GET   /api/v1/inventory/extended/analytics/inventory-valuation/
GET   /api/v1/inventory/extended/analytics/category-performance/
GET   /api/v1/inventory/extended/analytics/top-customers/
GET   /api/v1/inventory/extended/analytics/supplier-performance/
```

### Extended Features
```
GET/POST   /api/v1/inventory/extended/customers/
GET/POST   /api/v1/inventory/extended/warehouses/
GET/POST   /api/v1/inventory/extended/promotions/
GET/POST   /api/v1/inventory/extended/returns/
GET/POST   /api/v1/inventory/extended/webhooks/
GET/POST   /api/v1/inventory/extended/tags/
GET        /api/v1/inventory/extended/audit-logs/
```

### Bulk Operations
```
POST   /api/v1/inventory/extended/bulk/import-products/
GET    /api/v1/inventory/extended/bulk/export-products/
POST   /api/v1/inventory/extended/bulk/update-prices/
POST   /api/v1/inventory/extended/bulk/adjust-inventory/
GET    /api/v1/inventory/extended/bulk/export-sales/
POST   /api/v1/inventory/extended/bulk/import-customers/
```

### API Documentation
```
GET   /swagger/    Interactive Swagger UI
GET   /redoc/      ReDoc documentation
```

---

## Common Issues

**`ModuleNotFoundError` on runserver**  
Virtual environment is not activated. Run `pip install -r requirements/development.txt`.

**`no such table` error**  
Run `python manage.py migrate` before starting the server.

**`DJANGO_SETTINGS_MODULE` not found**  
Make sure `.env` contains `DJANGO_SETTINGS_MODULE=config.settings.development`.

**Celery tasks not running**  
Redis must be running on port `6380` before starting the Celery worker.

**Migration conflicts**
```bash
python manage.py migrate --run-syncdb
```

---

## Running Tests

```bash
pytest
```

Or with Django's built-in runner:

```bash
python manage.py test
```

---

## License

MIT
