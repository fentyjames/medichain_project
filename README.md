# MediChain Django Framework - Setup Guide

## Scalable Cross-Chain Layer-2 Blockchain Framework for Privacy-Preserving and Interoperable Healthcare Data Exchange Using Zero-Knowledge Proofs

**Author:** Fenty James Conteh  
**Institution:** Department of Artificial Intelligence Technologies, Ankara University, Ankara, Türkiye  
**Course:** BTaSC -- Blockchain Technology and Smart Contracts (2025-2026 Fall Semester)

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Detailed Setup](#detailed-setup)
4. [Database Configuration](#database-configuration)
5. [Running the Application](#running-the-application)
6. [API Usage Examples](#api-usage-examples)
7. [Testing](#testing)
8. [Troubleshooting](#troubleshooting)
9. [Production Deployment](#production-deployment)

---

## Prerequisites

Before starting, ensure you have the following installed on your system:

| Software | Minimum Version | Recommended Version | Download Link |
|----------|----------------|---------------------|---------------|
| Python | 3.10 | 3.11+ | [python.org](https://www.python.org/downloads/) |
| pip | 23.0 | 24.0+ | Included with Python |
| PostgreSQL | 14 | 16 | [postgresql.org](https://www.postgresql.org/download/) |
| Redis | 6.0 | 7.0+ | [redis.io](https://redis.io/download) |
| Git | 2.40 | 2.43+ | [git-scm.com](https://git-scm.com/downloads) |

### Optional Dependencies

| Software | Purpose | Download |
|----------|---------|----------|
| IPFS Kubo | Off-chain file storage | [ipfs.tech](https://docs.ipfs.tech/install/command-line/) |
| Node.js | Frontend tooling (if extending UI) | [nodejs.org](https://nodejs.org/) |

### Verify Prerequisites

```bash
# Check Python version
python3 --version
# Expected: Python 3.10.x or higher

# Check pip version
pip --version
# Expected: pip 23.x or higher

# Check PostgreSQL
psql --version
# Expected: psql (PostgreSQL) 14.x or higher

# Check Redis
redis-cli --version
# Expected: redis-cli 6.x or higher
```

---

## Quick Start

For experienced developers who want to get running immediately:

```bash
# 1. Extract the ZIP file
cd /path/to/medichain_django

# 2. Run the automated setup script
chmod +x setup.sh
./setup.sh

# 3. Start the server
source venv/bin/activate
cd medichain_project
python manage.py runserver
```

Access the application at: **http://localhost:8000/**

---

## Detailed Setup

### Step 1: Extract the Project Files

```bash
# If you have the ZIP file
unzip medichain_django_framework.zip -d medichain_django
cd medichain_django

# Or if you already have the extracted folder
cd /path/to/medichain_django
```

### Step 2: Create a Virtual Environment

A virtual environment isolates the project dependencies from your system Python.

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On Linux/macOS:
source venv/bin/activate

# On Windows:
venv\Scripts\activate

# Verify activation (should show path to venv)
which python
# Expected: /path/to/medichain_django/venv/bin/python
```

**Important:** Always activate the virtual environment before running any Django commands.

### Step 3: Upgrade pip and Install Dependencies

```bash
# Upgrade pip to latest version
pip install --upgrade pip

# Install all project dependencies
pip install -r medichain_project/requirements.txt
```

This installs:
- Django 4.2+ (web framework)
- Django REST Framework (API layer)
- PostgreSQL adapter (psycopg2-binary)
- Cryptography libraries (pycryptodome, cryptography)
- Web3.py (blockchain interaction)
- Celery and Redis (background tasks)
- Testing tools (pytest, pytest-django)

**Installation Time:** ~2-5 minutes depending on your internet connection.

### Step 4: Configure Environment Variables

Create a `.env` file in the `medichain_project` directory:

```bash
cd medichain_project
touch .env
```

Add the following configuration (adjust values as needed):

```env
# Django Settings
DEBUG=True
SECRET_KEY=your-secure-secret-key-change-this-in-production
ALLOWED_HOSTS=localhost,127.0.0.1

# Database Configuration
DB_NAME=medichain_db
DB_USER=medichain_user
DB_PASSWORD=your_secure_password
DB_HOST=localhost
DB_PORT=5432

# Redis (for Celery)
REDIS_URL=redis://localhost:6379/0

# Blockchain RPC URLs (optional - for production)
ETHEREUM_RPC=https://mainnet.infura.io/v3/YOUR_INFURA_KEY
POLYGON_RPC=https://polygon-rpc.com

# IPFS (optional)
IPFS_API=http://localhost:5001
IPFS_GATEWAY=https://ipfs.io/ipfs/
```

**Security Note:** Never commit the `.env` file to version control. The `.env` file is already in `.gitignore`.

### Step 5: Create PostgreSQL Database

```bash
# Switch to postgres user (Linux/macOS)
sudo -u postgres psql

# Or on Windows, use pgAdmin or psql directly
psql -U postgres
```

In the PostgreSQL prompt:

```sql
-- Create database
CREATE DATABASE medichain_db;

-- Create user
CREATE USER medichain_user WITH PASSWORD 'your_secure_password';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE medichain_db TO medichain_user;

-- Exit
\q
```

**Alternative: Using SQLite for Development**

If you prefer not to set up PostgreSQL for initial testing, you can use SQLite:

```python
# In medichain_project/settings.py, change:
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    },
    'blockchain': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'blockchain_db.sqlite3',
    }
}
```

### Step 6: Run Database Migrations

Migrations create the database tables based on the Django models:

```bash
# Make sure you're in the medichain_project directory
# and virtual environment is activated

# Run migrations for default database
python manage.py migrate --database=default

# Run migrations for blockchain database
python manage.py migrate --database=blockchain

# Expected output:
# Operations to perform:
#   Apply all migrations: admin, auth, blockchain, contenttypes, healthcare, sessions
# Running migrations:
#   Applying contenttypes.0001_initial... OK
#   Applying auth.0001_initial... OK
#   ...
```

### Step 7: Create a Superuser

The superuser account allows you to access the Django admin interface:

```bash
python manage.py createsuperuser

# You will be prompted for:
# Username: admin
# Email address: admin@example.com
# Password: ********
# Password (again): ********
```

**Password Requirements:** Minimum 8 characters, not entirely numeric, not too common.

### Step 8: Collect Static Files

```bash
python manage.py collectstatic --noinput

# This collects all static files into the staticfiles/ directory
# Expected output:
# 132 static files copied to .../staticfiles
```

### Step 9: Start Redis Server (Optional)

If you plan to use Celery for background tasks:

```bash
# Start Redis server
redis-server

# In a separate terminal, start Celery worker
cd medichain_project
celery -A medichain_project worker --loglevel=info
```

For initial testing, Celery is optional. The application works without it.

---

## Running the Application

### Development Server

```bash
# Start the Django development server
python manage.py runserver

# Or specify a port
python manage.py runserver 8080

# Or bind to all interfaces (for network access)
python manage.py runserver 0.0.0.0:8000
```

**Access Points:**
- **Dashboard:** http://localhost:8000/
- **Admin Panel:** http://localhost:8000/admin/
- **API Root:** http://localhost:8000/api/v1/
- **API Browser:** http://localhost:8000/api/blockchain/

### Verify Installation

Open your browser and navigate to http://localhost:8000/. You should see the MediChain dashboard with:
- System status indicators
- Live statistics (networks, blocks, transactions)
- Architecture component descriptions
- API endpoint documentation

---

## API Usage Examples

### 1. Authentication

All API endpoints (except login) require authentication via Token.

```bash
# Obtain authentication token
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "your_password"}'

# Response:
# {"token": "abc123def456...", "user_id": 1, "username": "admin"}
```

Use the token in subsequent requests:

```bash
# Include token in header
curl -H "Authorization: Token abc123def456..." \
  http://localhost:8000/api/v1/dashboard/
```

### 2. Create a Blockchain Network

```bash
curl -X POST http://localhost:8000/api/blockchain/networks/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "network_id": "ethereum_main",
    "name": "Ethereum Mainnet",
    "chain_id": 1,
    "rpc_url": "https://mainnet.infura.io/v3/YOUR_KEY",
    "consensus_type": "PoS"
  }'
```

### 3. Register a Patient

```bash
curl -X POST http://localhost:8000/api/healthcare/patients/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "public_key": "patient_public_key_here",
    "blood_type": "A+",
    "allergies": "None",
    "emergency_contact": "+90-555-123-4567"
  }'
```

### 4. Create a Medical Record

```bash
curl -X POST http://localhost:8000/api/healthcare/records/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "PATIENT_ID_FROM_PREVIOUS_STEP",
    "hospital_id": "HOSPITAL_ID",
    "record_type": "DIAGNOSIS",
    "title": "Annual Health Checkup",
    "description": "Patient shows normal vital signs...",
    "ipfs_hash": "QmTestHash123",
    "signature": "signature_here"
  }'
```

### 5. Create a Rollup Batch

```bash
curl -X POST http://localhost:8000/api/v1/rollup/create/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "network_id": "ethereum_main"
  }'
```

### 6. Verify a ZK Proof

```bash
curl -X POST http://localhost:8000/api/v1/zk/verify/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "proof": "{\"proof_type\": \"zk_snark\", ...}",
    "public_output": "merkle_root_hash",
    "expected_inputs": ["tx_hash_1", "tx_hash_2"],
    "proof_type": "zk_snark"
  }'
```

### 7. Cross-Chain Transfer

```bash
curl -X POST http://localhost:8000/api/v1/cross-chain/transfer/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "source_chain": "ethereum_main",
    "target_chain": "polygon",
    "data_hash": "data_hash_here",
    "proof": "zk_proof_here",
    "sender": "hospital_1"
  }'
```

---

## Testing

### Run All Tests

```bash
# Run the complete test suite
python manage.py test tests --verbosity=2

# Expected output:
# test_generate_proof (tests.test_medichain.ZKProofServiceTest) ... ok
# test_verify_proof_valid (tests.test_medichain.ZKProofServiceTest) ... ok
# test_create_message (tests.test_medichain.CrossChainRelayTest) ... ok
# test_dashboard_api (tests.test_medichain.APIIntegrationTest) ... ok
# ...
# Ran 25 tests in 3.456s
# OK
```

### Run Specific Test Modules

```bash
# ZK Proof tests only
python manage.py test tests.test_medichain.ZKProofServiceTest

# Cross-chain relay tests
python manage.py test tests.test_medichain.CrossChainRelayTest

# API integration tests
python manage.py test tests.test_medichain.APIIntegrationTest

# Performance benchmarks
python manage.py test tests.test_medichain.PerformanceTest

# Blockchain model tests
python manage.py test tests.test_medichain.BlockchainModelTest

# Healthcare model tests
python manage.py test tests.test_medichain.HealthcareModelTest
```

### Run with Coverage Report

```bash
# Install coverage tool
pip install coverage

# Run tests with coverage
coverage run --source='.' manage.py test tests

# Generate HTML report
coverage html

# View report
# Open htmlcov/index.html in your browser
```

---

## Troubleshooting

### Issue 1: "Command not found: python"

**Solution:** Use `python3` instead of `python`:

```bash
python3 -m venv venv
python3 manage.py runserver
```

### Issue 2: "psycopg2.errors.InsufficientPrivilege"

**Solution:** Grant proper PostgreSQL permissions:

```sql
-- In psql
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO medichain_user;
ALTER USER medichain_user CREATEDB;
```

### Issue 3: "django.db.utils.OperationalError: could not connect to server"

**Solution:** Ensure PostgreSQL is running:

```bash
# Linux
sudo systemctl start postgresql

# macOS (with Homebrew)
brew services start postgresql

# Windows
# Start PostgreSQL service from Services panel
```

### Issue 4: "ImportError: No module named 'rest_framework'"

**Solution:** Ensure virtual environment is activated:

```bash
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate     # Windows

# Reinstall requirements
pip install -r requirements.txt
```

### Issue 5: "Permission denied: manage.py"

**Solution:** Make manage.py executable:

```bash
chmod +x manage.py
```

### Issue 6: "CSRF verification failed" in API requests

**Solution:** For API testing, use the `@csrf_exempt` decorator or include CSRF token:

```bash
# Get CSRF token first
curl -c cookies.txt http://localhost:8000/api/v1/auth/login/

# Use token in subsequent requests
curl -b cookies.txt -X POST http://localhost:8000/api/v1/auth/login/ ...
```

### Issue 7: Port 8000 already in use

**Solution:** Use a different port:

```bash
python manage.py runserver 8080
# or
python manage.py runserver 9000
```

---

## Production Deployment

### 1. Security Settings

Edit `medichain_project/settings.py`:

```python
DEBUG = False
ALLOWED_HOSTS = ['yourdomain.com', 'www.yourdomain.com']
SECRET_KEY = os.environ.get('SECRET_KEY')  # From environment variable

# Security middleware
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
```

### 2. Use Gunicorn

```bash
# Install gunicorn
pip install gunicorn

# Run with gunicorn
gunicorn medichain_project.wsgi:application --bind 0.0.0.0:8000 --workers 4
```

### 3. Configure Nginx (Reverse Proxy)

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /static/ {
        alias /path/to/medichain_django/medichain_project/staticfiles/;
    }

    location /media/ {
        alias /path/to/medichain_django/medichain_project/media/;
    }
}
```

### 4. SSL/TLS with Let's Encrypt

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d yourdomain.com
```

### 5. Database Backup

```bash
# Backup PostgreSQL database
pg_dump -U medichain_user medichain_db > backup_$(date +%Y%m%d).sql

# Restore from backup
psql -U medichain_user medichain_db < backup_20250101.sql
```

---

## Project Structure

```
medichain_django/
├── README.md                          # This file
├── setup.sh                           # Automated setup script
├── medichain_project/                 # Main Django project
│   ├── manage.py                      # Django management script
│   ├── requirements.txt               # Python dependencies
│   ├── .env                           # Environment variables (create this)
│   ├── medichain_project/             # Project configuration
│   │   ├── settings.py                # Django settings
│   │   ├── urls.py                    # URL routing
│   │   ├── wsgi.py                    # WSGI entry point
│   │   ├── asgi.py                    # ASGI entry point
│   │   └── db_router.py             # Database routing
│   ├── blockchain/                    # Blockchain core app
│   │   ├── models.py                  # Block, Transaction, RollupBatch models
│   │   ├── views.py                   # API ViewSets
│   │   ├── urls.py                    # App URL configuration
│   │   ├── admin.py                   # Admin interface config
│   │   ├── apps.py                    # App configuration
│   │   ├── middleware.py              # ZK and Cross-Chain middleware
│   │   ├── signals.py                 # Django signals
│   │   ├── utils.py                   # Encryption & IPFS utilities
│   │   └── templates/                 # HTML templates
│   │       └── blockchain/
│   │           └── dashboard.html     # Main dashboard
│   ├── healthcare/                    # Healthcare data app
│   │   ├── models.py                  # Patient, Hospital, MedicalRecord models
│   │   ├── views.py                   # Healthcare API endpoints
│   │   ├── urls.py                    # Healthcare URLs
│   │   └── admin.py                   # Healthcare admin
│   ├── zk_proofs/                     # Zero-Knowledge Proof app
│   │   ├── zk_service.py              # ZK proof generation/verification
│   │   ├── views.py                   # ZK API endpoints
│   │   └── urls.py                    # ZK URLs
│   ├── cross_chain/                   # Cross-Chain Relay app
│   │   ├── relay_service.py           # Cross-chain relay logic
│   │   ├── views.py                   # Relay API endpoints
│   │   └── urls.py                    # Relay URLs
│   ├── api/                           # Main API app
│   │   ├── views.py                   # Consolidated API views
│   │   ├── urls.py                    # Main API URLs
│   │   └── serializers.py           # DRF serializers
│   └── tests/                         # Test suite
│       └── test_medichain.py          # Comprehensive tests
```

---

## Support & Contact

For issues, questions, or contributions related to this academic project:

- **Author:** Fenty James Conteh
- **Institution:** Ankara University, Department of Artificial Intelligence Technologies
- **Course:** BTaSC -- Blockchain Technology and Smart Contracts

---

## License

This framework is developed for academic research and educational purposes at Ankara University. All rights reserved.

---

**Last Updated:** May 2026  
**Framework Version:** 1.0.0
