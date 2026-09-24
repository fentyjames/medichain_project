# MediChain Django Framework

## Scalable Cross-Chain Layer-2 Blockchain Framework for Privacy-Preserving and Interoperable Healthcare Data Exchange Using Zero-Knowledge Proofs

**Author:** Fenty James Conteh  


---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start (Local)](#quick-start-local)
3. [Docker Compose Quick Start](#docker-compose-quick-start)
4. [Detailed Setup](#detailed-setup)
5. [Database Configuration](#database-configuration)
6. [Running the Application](#running-the-application)
7. [Feature Overview](#feature-overview)
8. [API Usage Examples](#api-usage-examples)
9. [Testing](#testing)
10. [Troubleshooting](#troubleshooting)
11. [Production Deployment](#production-deployment)

---

## Prerequisites

| Software | Minimum Version | Recommended | Download |
|----------|----------------|-------------|----------|
| Python | 3.10 | 3.12 | [python.org](https://www.python.org/downloads/) |
| PostgreSQL | 14 | 16 | [postgresql.org](https://www.postgresql.org/download/) |
| Redis | 6.0 | 7.0+ | [redis.io](https://redis.io/download) |
| Git | 2.40 | 2.43+ | [git-scm.com](https://git-scm.com/downloads) |
| Docker + Compose | 24.0 | latest | [docker.com](https://www.docker.com/get-started/) |

---

## Quick Start (Local)

```powershell
# Windows PowerShell — run from the project root (E:\medichain_project)

# 1. Create and activate virtual environment
python -m venv venv
.\venv\Scripts\activate

# 2. Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 3. Apply migrations  (single database — see Database Configuration below)
python manage.py migrate

# 4. Create a superuser
python manage.py createsuperuser

# 5. Start the dev server
python manage.py runserver
```

Access the application at **http://127.0.0.1:8000/**

---

## Docker Compose Quick Start

The included `docker-compose.yml` spins up Django + PostgreSQL 16 + Redis 7 with a
single command. No local PostgreSQL or Redis installation required.

```bash
# Build images and start all services
docker compose up --build

# First-time only: create a superuser
docker compose exec web python manage.py createsuperuser
```

Services exposed:

| Service | Port |
|---------|------|
| Django (gunicorn) | http://localhost:8000 |
| PostgreSQL | localhost:5433 |
| Redis | localhost:6379 |

Stop with `docker compose down`. Add `-v` to also remove the database volume.

---

## Detailed Setup

### Step 1 — Clone or extract the project

```bash
git clone <repo-url>
cd medichain_project
```

> **Important:** `manage.py` lives at the project root (`E:\medichain_project\`).
> All `python manage.py ...` commands must be run from this directory — **not** from
> any inner subdirectory.

### Step 2 — Virtual environment

```powershell
python -m venv venv
.\venv\Scripts\activate      # Windows PowerShell
# source venv/bin/activate   # Linux / macOS
```

### Step 3 — Install dependencies

```powershell
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 4 — Configure the database

The application uses a single PostgreSQL database. The credentials are hard-coded in
`medichain_project/settings.py` as development defaults:

| Setting | Value |
|---------|-------|
| Host | localhost |
| Port | 5433 |
| Database | medichain_db |
| User | postgres |
| Password | master011 |

Create the database if it does not already exist:

```sql
-- In psql or pgAdmin
CREATE DATABASE medichain_db;
```

> **Note:** `python-decouple` is installed but `.env` loading is not wired up in the
> current settings file. Edit `settings.py` directly for any credential changes.

### Step 5 — Run migrations

```powershell
python manage.py migrate
```

> Do **not** run `migrate --database=blockchain`. The blockchain database alias is
> commented out; both healthcare and blockchain tables live in the single default DB.

### Step 6 — Create superuser

```powershell
python manage.py createsuperuser
```

### Step 7 — Collect static files (production / Docker only)

```powershell
python manage.py collectstatic --noinput
```

### Step 8 — Start the server

```powershell
python manage.py runserver
```

---

## Database Configuration

`medichain_project/settings.py` defines **only the `default` PostgreSQL database**.
The `blockchain` database alias and `DATABASE_ROUTERS` are commented out.

Consequences:
- Both `healthcare` and `blockchain` app tables are in the same Postgres DB.
- Cross-app foreign keys work because everything is co-located.
- Re-enabling the router requires uncommenting both the `blockchain` DB entry **and** the
  `DATABASE_ROUTERS` line together; doing one without the other will silently break
  migrations.

---

## Running the Application

### Development server

```powershell
python manage.py runserver           # :8000
python manage.py runserver 8080      # custom port
python manage.py runserver 0.0.0.0:8000  # accessible from network
```

### Celery (optional — background tasks)

```powershell
# Terminal 1: Redis must be running
# Terminal 2:
celery -A medichain_project worker --loglevel=info
```

---

## Feature Overview

### Application URLs

| Section | URL |
|---------|-----|
| Landing / Login | `/` |
| Main Dashboard | `/dashboard/` |
| Admin Panel | `/admin/` |
| **Healthcare** | |
| Patients | `/healthcare/patients/` |
| Hospitals | `/healthcare/hospitals/` |
| Medical Records | `/healthcare/records/` |
| Laboratories | `/healthcare/labs/` |
| Insurance Providers | `/healthcare/insurance/` |
| Access Permissions | `/healthcare/permissions/` |
| Audit Log | `/healthcare/audit/` |
| Reports Hub | `/healthcare/reports/` |
| **Blockchain** | |
| Blockchain Dashboard | `/blockchain/` |
| Blocks | `/blockchain/blocks/` |
| Transactions | `/blockchain/transactions/` |
| Rollup Batches | `/blockchain/rollups/` |
| **Cross-Chain** | |
| Cross-Chain Dashboard | `/cross-chain/` |
| New Transfer | `/cross-chain/transfer/` |
| **ZK Proofs** | |
| ZK Dashboard + History | `/zk-proofs/` |
| Generate Proof | `/zk-proofs/generate/` |
| Verify Proof | `/zk-proofs/verify/` |
| Range Proof | `/zk-proofs/range/` |
| **API & Docs** | |
| Swagger UI | `/api/docs/` |
| ReDoc | `/api/redoc/` |
| API Schema (JSON) | `/api/schema/` |

### CSV Exports

Every major list view has a **CSV** download button that exports up to 10 000 rows:

| Export | URL |
|--------|-----|
| Patients | `/healthcare/patients/export/csv/` |
| Medical Records | `/healthcare/records/export/csv/` |
| Audit Log | `/healthcare/audit/export/csv/` |
| Transactions | `/blockchain/transactions/export/csv/` |

### Dashboard Charts

The main dashboard (`/dashboard/`) renders three live Chart.js charts:
- **Transaction Volume** — 7-day bar chart of daily transaction counts
- **Record Type Distribution** — Doughnut chart of active medical record types
- **Audit Activity** — Horizontal bar chart of the 10 most common audit actions (last 30 days)

### ZK Proof History

The ZK dashboard (`/zk-proofs/`) shows a **Proof History** table of every proof generated
or verified through the UI, stored in the `ZKProofRecord` model.

---

## API Usage Examples

### Authentication

```bash
# Obtain token
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "your_password"}'
# → {"token": "abc123...", "user_id": 1, "username": "admin"}

# Use token in subsequent requests
curl -H "Authorization: Token abc123..." http://localhost:8000/api/v1/dashboard/
```

### Create a Blockchain Transaction

```bash
curl -X POST http://localhost:8000/api/blockchain/api/transactions/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"tx_type": "CREATE", "sender": "HOSPITAL_ID", "data_hash": "abc123...", "signature": "sig"}'
```

### Register a Patient

```bash
curl -X POST http://localhost:8000/api/healthcare/api/patients/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"public_key": "key_here", "blood_type": "A+", "emergency_contact": "+1-555-0100"}'
```

### Generate a ZK Proof

```bash
curl -X POST http://localhost:8000/api/zk-proofs/generate/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"inputs": ["tx_hash_1", "tx_hash_2"], "public_output": "merkle_root", "proof_type": "zk_snark"}'
```

### Create a Rollup Batch

```bash
curl -X POST http://localhost:8000/api/v1/rollup/create/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"network_id": "ethereum_main"}'
```

### Interactive API Explorer

Browse and test all endpoints at **http://localhost:8000/api/docs/** (Swagger UI)
or **http://localhost:8000/api/redoc/** (ReDoc).

---

## Testing

```powershell
# Full test suite
python manage.py test tests --verbosity=2

# Single class
python manage.py test tests.test_medichain.ZKProofServiceTest

# Single test
python manage.py test tests.test_medichain.APIIntegrationTest.test_dashboard_api

# With coverage
coverage run --source='.' manage.py test tests
coverage html
# Open htmlcov/index.html
```

> Avoid running `tests.test_medichain.PerformanceTest` during iteration — it is slow.

---

## Troubleshooting

### "could not connect to server" (PostgreSQL)

Ensure PostgreSQL is running on port 5433 and `medichain_db` exists.

```powershell
# Windows: start from Services panel or
pg_ctl start -D "C:\Program Files\PostgreSQL\16\data"
```

### "No module named 'rest_framework'"

Virtual environment is not activated:

```powershell
.\venv\Scripts\activate
pip install -r requirements.txt
```

### "CSRF verification failed"

Use `Authorization: Token <token>` header for API requests instead of session cookies.

### Port 8000 already in use

```powershell
python manage.py runserver 8080
```

### Django template `{{ block.xxx }}` renders empty

This is a known Django variable-shadowing issue: any context variable named `block`
is silently overridden by the template engine. Rename the context variable (e.g. `blk`)
in the view and all corresponding template references.

---

## Production Deployment

### Using Docker Compose (recommended)

```bash
docker compose up -d
```

Set `DEBUG=False` and a strong `SECRET_KEY` in `medichain_project/settings.py` or via
an `.env` file before deploying.

### Using Gunicorn + Nginx

```bash
# Gunicorn (already in requirements)
gunicorn medichain_project.wsgi:application --bind 0.0.0.0:8000 --workers 4

# Nginx reverse-proxy snippet
# location / { proxy_pass http://127.0.0.1:8000; }
# location /static/ { alias /app/staticfiles/; }
```

### Security checklist

```python
# settings.py — production overrides
DEBUG = False
ALLOWED_HOSTS = ['yourdomain.com']
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

### Database backup

```bash
pg_dump -U postgres -p 5433 medichain_db > backup_$(date +%Y%m%d).sql
```

---

## Project Structure

```
medichain_project/          ← project root, manage.py lives here
├── manage.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── README.md
├── teach.md                ← comprehensive usage guide
├── teachme.md              ← step-by-step walkthrough
├── medichain_project/      ← Django config package
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── db_router.py        ← BlockchainRouter (dormant — see DB Configuration)
├── blockchain/             ← core ledger models + views + API
├── healthcare/             ← patient, hospital, record, audit models + views
├── zk_proofs/              ← ZK-SNARK/STARK simulation + ZKProofRecord history
├── cross_chain/            ← cross-chain relay service + views
├── api/                    ← aggregated /api/v1/ endpoints
├── accounts/               ← login, dashboard index view, user profile
├── templates/              ← root-level HTML templates (take priority over app-level)
│   ├── base.html
│   ├── index.html          ← main dashboard with Chart.js charts
│   ├── blockchain/
│   ├── healthcare/
│   ├── cross_chain/
│   ├── zk_proofs/
│   └── partials/
└── tests/
    └── test_medichain.py
```

---

## Support & Contact

- **Author:** Fenty James Conteh


---

## License

Developed for academic research and educational purposes at Ankara University. All rights reserved.

---

**Last Updated:** May 2026 | **Framework Version:** 1.1.0
