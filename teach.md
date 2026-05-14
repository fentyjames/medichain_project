# MediChain — Complete Usage Guide

> **MediChain** is a Scalable Cross-Chain Layer-2 Blockchain Framework for Privacy-Preserving and Interoperable Healthcare Data Exchange Using Zero-Knowledge Proofs.

**Author:** Fenty James Conteh — Department of Artificial Intelligence Technologies, Ankara University  
**Framework Version:** 1.1.0

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Prerequisites & Setup](#2-prerequisites--setup)
3. [Where to Input Data — All Entry Points](#3-where-to-input-data--all-entry-points)
4. [Module-by-Module Usage](#4-module-by-module-usage)
5. [Dashboard Charts](#5-dashboard-charts)
6. [CSV Data Exports](#6-csv-data-exports)
7. [API Reference](#7-api-reference)
8. [Interactive API Documentation](#8-interactive-api-documentation)
9. [How the Blockchain Works](#9-how-the-blockchain-works)
10. [Zero-Knowledge Proofs & Proof History](#10-zero-knowledge-proofs--proof-history)
11. [Cross-Chain Relay](#11-cross-chain-relay)
12. [Testing](#12-testing)
13. [Production Deployment](#13-production-deployment)
14. [Troubleshooting](#14-troubleshooting)

---

## 1. Architecture Overview

MediChain is a Django-based web application with **four core modules** and a **unified API layer**:

```
┌─────────────────────────────────────────────────────┐
│                    Frontend (Templates)              │
│  base.html ← All pages extend this dark-themed UI   │
│  ├── index.html          (Dashboard + Chart.js)     │
│  ├── healthcare/*.html   (Patient/Record/Hospital)  │
│  ├── blockchain/*.html   (Blocks/Txs/Rollups)       │
│  ├── cross_chain/*.html  (Inter-chain transfers)    │
│  └── zk_proofs/*.html    (ZK proof generation)      │
├─────────────────────────────────────────────────────┤
│                    API Layer (DRF)                   │
│  ├── api/v1/             (Unified API endpoints)    │
│  ├── api/blockchain/     (Blockchain CRUD)          │
│  ├── api/healthcare/     (Healthcare CRUD)          │
│  ├── api/cross-chain/    (Relay endpoints)          │
│  ├── api/zk-proofs/      (Proof generation)         │
│  ├── /api/docs/          (Swagger UI)               │
│  └── /api/redoc/         (ReDoc)                    │
├─────────────────────────────────────────────────────┤
│                    Core Modules                      │
│  ├── blockchain/          (Blocks, Txs, Rollups)    │
│  ├── healthcare/          (Patients, Records, ACLs) │
│  ├── cross_chain/         (Relay service, messages) │
│  └── zk_proofs/           (ZK-SNARK/STARK + history)│
└─────────────────────────────────────────────────────┘
```

**Key Models:**

| Model | App | Purpose |
|-------|-----|---------|
| `Patient` | healthcare | Patient identity; name/email via linked `User` account |
| `Hospital` | healthcare | Hospital registration & identity |
| `Laboratory` | healthcare | Lab affiliated with a hospital |
| `InsuranceProvider` | healthcare | Insurance company |
| `MedicalRecord` | healthcare | Medical records with on-chain hash anchoring |
| `AccessPermission` | healthcare | Patient-granted access control |
| `AuditLog` | healthcare | Complete audit trail of all actions |
| `BlockchainNetwork` | blockchain | Supported chains (Ethereum, Polygon, Hyperledger) |
| `Block` | blockchain | Blocks containing batched transactions |
| `Transaction` | blockchain | Individual data operations |
| `RollupBatch` | blockchain | Layer-2 batch aggregation with ZK proofs |
| `CrossChainMessage` | blockchain | Inter-chain relay messages |
| `ValidatorNode` | blockchain | Consensus validator nodes |
| `SmartContract` | blockchain | Deployed smart contracts |
| `ZKProofRecord` | zk_proofs | Persistent history of generated/verified proofs |

---

## 2. Prerequisites & Setup

### System Requirements

| Software | Minimum Version | Download |
|----------|-----------------|----------|
| Python | 3.10 | [python.org](https://www.python.org/downloads/) |
| PostgreSQL | 14 | [postgresql.org](https://www.postgresql.org/download/) |
| Redis | 6.0 | [redis.io](https://redis.io/download) |
| Git | 2.40 | [git-scm.com](https://git-scm.com/downloads) |

### Option A — Local setup (Windows PowerShell)

```powershell
# From project root  E:\medichain_project
.\venv\Scripts\activate

pip install --upgrade pip
pip install -r requirements.txt

# Single migration command — one database only
python manage.py migrate

python manage.py createsuperuser
python manage.py runserver
```

> **Database note:** The project uses **one** PostgreSQL database (`medichain_db` on
> port 5433). Do NOT run `migrate --database=blockchain` — that alias is commented out.

### Option B — Docker Compose

```bash
docker compose up --build

# First run only
docker compose exec web python manage.py createsuperuser
```

Access the app at **http://localhost:8000/**

---

## 3. Where to Input Data — All Entry Points

### 🩺 A. Register a Patient

**UI:** `Healthcare → Add Patient` → `/healthcare/patients/add/`

| Field | Required | Notes |
|-------|----------|-------|
| Public Key | ✅ | Cryptographic identity string |
| Date of Birth | ❌ | YYYY-MM-DD |
| Blood Type | ❌ | A+, A-, B+, B-, AB+, AB-, O+, O- |
| Allergies | ❌ | Free text |
| Emergency Contact | ❌ | Phone/name |

> The patient's **display name** comes from the linked `User` account
> (`patient.user.get_full_name()`). Link via Admin Panel → Healthcare → Patients → User field.

**API:**
```bash
POST /api/healthcare/api/patients/
Authorization: Token YOUR_TOKEN
Content-Type: application/json

{"public_key": "0xPatientKey", "blood_type": "A+", "emergency_contact": "+1-555-0100"}
```

---

### 🏥 B. Register a Hospital

**UI:** `/healthcare/hospitals/add/`

| Field | Required | Notes |
|-------|----------|-------|
| Hospital Name | ✅ | Full name |
| License Number | ✅ | Must be unique |
| Address | ❌ | Free text |
| Public Key | ✅ | Cryptographic key |
| Blockchain Network | ❌ | Link to an active network |

**API:**
```bash
POST /api/healthcare/api/hospitals/
{"name": "Ankara University Hospital", "license_number": "LIC-001", "public_key": "key"}
```

---

### 🧪 C. Register a Laboratory

**UI:** `/healthcare/labs/add/`

| Field | Required | Notes |
|-------|----------|-------|
| Laboratory Name | ✅ | |
| Accreditation | ❌ | e.g. ISO 15189 |
| Public Key | ✅ | |
| Affiliated Hospital | ❌ | Select from dropdown |

---

### 🛡️ D. Register an Insurance Provider

**UI:** `/healthcare/insurance/add/`

| Field | Required | Notes |
|-------|----------|-------|
| Provider Name | ✅ | |
| License Number | ✅ | Must be unique |
| Public Key | ✅ | |

---

### 📄 E. Create a Medical Record

**UI:** `Healthcare → Add Record` → `/healthcare/records/add/`

| Field | Required | Notes |
|-------|----------|-------|
| Patient | ✅ | Dropdown |
| Hospital | ✅ | Dropdown |
| Record Type | ✅ | DIAGNOSIS, LAB_RESULT, PRESCRIPTION, IMAGING, SURGERY, DISCHARGE, INSURANCE |
| Title | ✅ | Short descriptive title |
| Description | ❌ | Clinical notes |
| IPFS Hash | ❌ | Pre-uploaded CID (Qm…) |
| Signature | ❌ | ECDSA signature |

**What happens automatically on save:**
1. Unique `record_id` is generated (SHA-256 of UUID + timestamp)
2. `data_hash` is computed for integrity verification
3. A `Transaction` of type `CREATE` is created and linked to the record
4. An `AuditLog` entry with action `CREATE` is written

**API:**
```bash
POST /api/healthcare/api/records/
{"patient": "PATIENT_ID", "hospital": "HOSPITAL_ID", "record_type": "DIAGNOSIS",
 "title": "Annual Check", "description": "All vitals normal.", "signature": "sig"}
```

---

### 🔑 F. Grant Access Permission

**UI:** `/healthcare/permissions/add/` (or **Grant Access** button on any record detail page)

| Field | Required | Notes |
|-------|----------|-------|
| Record | ✅ | Dropdown |
| Patient (Grantor) | ✅ | Patient authorising access |
| Grantee Name | ✅ | Hospital/Lab/Doctor name |
| Grantee Type | ✅ | HOSPITAL, LAB, INSURANCE, DOCTOR |
| Permission Type | ✅ | READ / WRITE / SHARE |
| Purpose | ✅ | HIPAA required explanation |
| Valid Until | ❌ | Optional expiry date |

Revoke by clicking the red **X** on the Permissions list. Revoked permissions stay in the audit trail.

---

### ⛓️ G. Create a Blockchain Transaction (Direct)

**UI:** `/blockchain/transactions/add/`

| Field | Required | Notes |
|-------|----------|-------|
| Transaction Type | ✅ | CREATE / UPDATE / SHARE / VERIFY / ACCESS |
| Sender | ✅ | Hospital or Patient ID |
| Receiver | ❌ | Target entity ID |
| Data Hash | ✅ | SHA-256 of data |
| Signature | ✅ | ECDSA signature |

Status flow: `PENDING → BATCHED → CONFIRMED`

---

### 📦 H. Create a Rollup Batch

**UI:** `/blockchain/rollups/create/`

1. Select the target **Blockchain Network**
2. Click **Generate Batch & ZK Proof**

What happens:
- All PENDING transactions (up to 50) are collected
- Merkle tree is built from transaction hashes
- ZK-SNARK proof is generated for the batch
- Transactions move `PENDING → BATCHED`

**API:**
```bash
POST /api/v1/rollup/create/
{"network_id": "ethereum_main"}
```

---

### 🔄 I. Cross-Chain Transfer

**UI:** `/cross-chain/transfer/`

| Field | Required | Notes |
|-------|----------|-------|
| Source Network | ✅ | Where the message originates |
| Target Network | ✅ | Where it is sent (must be different) |
| Data Hash | ✅ | SHA-256 hash of data being relayed |
| Signature | ✅ | Simulated ECDSA signature |
| Nonce | ❌ | Auto-generated if blank |

**API:**
```bash
POST /api/v1/cross-chain/transfer/
{"source_chain": "ethereum_main", "target_chain": "polygon",
 "data_hash": "abc123", "proof": "zk_proof_json", "sender": "hospital_1"}
```

---

### 🔐 J. Generate a Zero-Knowledge Proof

**UI:** `/zk-proofs/generate/`

| Field | Required | Notes |
|-------|----------|-------|
| Private Inputs | ✅ | Transaction hashes, one per line |
| Public Output | ✅ | SHA-256 Merkle root (public commitment) |
| Proof Type | ❌ | zk-SNARK (default) or zk-STARK |

**What happens:**
- `ZKProofService.generate_proof()` creates a JSON proof structure
- The proof is saved as a `ZKProofRecord` entry (visible in ZK Proof History)
- The generated JSON is displayed for copy-paste

**API:**
```bash
POST /api/zk-proofs/generate/
{"inputs": ["tx_hash_1", "tx_hash_2"], "public_output": "merkle_root", "proof_type": "zk_snark"}
```

---

### ✅ K. Verify a Zero-Knowledge Proof

**UI:** `/zk-proofs/verify/`

| Field | Required | Notes |
|-------|----------|-------|
| Proof JSON | ✅ | Paste the proof from the generate page |
| Public Output | ✅ | Expected Merkle root |
| Expected Inputs | ❌ | Transaction hashes for cross-check |
| Proof Type | ❌ | zk-SNARK or zk-STARK |

Each verification is also saved as a `ZKProofRecord` with `is_verified` reflecting the result.

---

### 📏 L. Generate a Range Proof

**UI:** `/zk-proofs/range/`

| Field | Required | Notes |
|-------|----------|-------|
| Value | ✅ | Secret value to prove (e.g. blood pressure 120) |
| Min | ✅ | Minimum of acceptable range (e.g. 90) |
| Max | ✅ | Maximum of acceptable range (e.g. 140) |

Use case: prove a medical value is within a healthy range without revealing the exact number — critical for HIPAA compliance.

**API:**
```bash
POST /api/zk-proofs/range-proof/
{"action": "generate", "value": 120, "min": 90, "max": 140}

# Verify
POST /api/zk-proofs/range-proof/
{"action": "verify", "proof": "<proof_json>", "min": 90, "max": 140}
```

---

## 4. Module-by-Module Usage

### Healthcare Module

**Dashboard** (`/healthcare/`)
- Counts: patients, hospitals, labs, insurance providers, records, permissions
- Recent patients and recent records tables
- Quick action buttons for all CRUD operations

**Patient Management:**
- **List:** `/healthcare/patients/` — search by name, email, ID, blood type; paginated
- **Add:** `/healthcare/patients/add/`
- **Detail:** `/healthcare/patients/{patient_id}/` — records, permissions, audit trail
- **Edit:** `/healthcare/patients/{patient_id}/edit/`
- **CSV export:** `/healthcare/patients/export/csv/`

**Hospital Management:**
- **List:** `/healthcare/hospitals/`
- **Add:** `/healthcare/hospitals/add/`
- **Detail:** `/healthcare/hospitals/{hospital_id}/`

**Laboratory Management:**
- **List:** `/healthcare/labs/`
- **Add:** `/healthcare/labs/add/`
- **Detail:** `/healthcare/labs/{lab_id}/`

**Insurance Providers:**
- **List:** `/healthcare/insurance/`
- **Add:** `/healthcare/insurance/add/`
- **Detail:** `/healthcare/insurance/{ins_id}/`

**Medical Records:**
- **List:** `/healthcare/records/` — search by title, type, patient
- **Add:** `/healthcare/records/add/`
- **Detail:** `/healthcare/records/{record_id}/` — integrity hashes, permissions, audit trail
- **Edit:** `/healthcare/records/{record_id}/edit/`
- **CSV export:** `/healthcare/records/export/csv/`

**Access Permissions:**
- **List:** `/healthcare/permissions/`
- **Grant:** `/healthcare/permissions/add/`

**Audit Log:**
- **List:** `/healthcare/audit/` — filter by action and actor type; paginated
- **CSV export:** `/healthcare/audit/export/csv/`

**Reports:**
- **Hub:** `/healthcare/reports/`
- **System Overview:** `/healthcare/reports/overview/`
- **Audit & Compliance:** `/healthcare/reports/audit/`
- Per-entity reports via **Report** button on detail pages

---

### Blockchain Module

**Dashboard** (`/blockchain/`)
- Stats: total blocks, transactions, pending, validators
- Recent blocks table (hash, Merkle root, TX count, network, time)
- Active networks with consensus type

**Blocks:** `/blockchain/blocks/` → detail: `/blockchain/blocks/{block_number}/`
**Transactions:** `/blockchain/transactions/`
- CSV export: `/blockchain/transactions/export/csv/`

**Rollup Batches:** `/blockchain/rollups/`
- Create: `/blockchain/rollups/create/`
- Detail: `/blockchain/rollups/{batch_id}/`

---

### Cross-Chain Module

**Dashboard** (`/cross-chain/`)
- Counts: total messages, relayed, pending, rejected
- Recent message list with source/target chain and status

**New Transfer:** `/cross-chain/transfer/`
**Message Detail:** `/cross-chain/{message_id}/`

---

### ZK Proofs Module

**Dashboard** (`/zk-proofs/`)
- Summary cards: total proofs generated and verified
- **Proof History** table — all `ZKProofRecord` entries (type, inputs, output, verified, time)

**Generate:** `/zk-proofs/generate/`
**Verify:** `/zk-proofs/verify/`
**Range Proof:** `/zk-proofs/range/`

---

## 5. Dashboard Charts

The main dashboard (`/dashboard/`) contains three live charts rendered with **Chart.js 4.4**:

### Transaction Volume (7-day bar chart)
- Shows the number of blockchain transactions per day for the last 7 days
- Data is computed server-side with `TruncDate` + `Count` and passed as JSON

### Record Type Distribution (doughnut chart)
- Shows the breakdown of active `MedicalRecord` records by `record_type`
- Types: DIAGNOSIS, LAB_RESULT, PRESCRIPTION, IMAGING, SURGERY, DISCHARGE, INSURANCE

### Audit Activity (horizontal bar chart)
- Shows the 10 most common `AuditLog` actions over the last 30 days
- Useful for compliance monitoring at a glance

Charts are responsive and update on every page load. They gracefully render empty when there is no data yet.

---

## 6. CSV Data Exports

Every major list view includes a **CSV** download button. Exports are served as file downloads with appropriate `Content-Disposition` headers. Up to 10 000 rows are exported per request.

| Export | URL | Columns |
|--------|-----|---------|
| Patients | `/healthcare/patients/export/csv/` | Patient ID, Name, Email, DOB, Blood Type, Emergency Contact, Status, Registered |
| Medical Records | `/healthcare/records/export/csv/` | Record ID, Title, Type, Patient, Hospital, IPFS Hash, On-chain TX, Active, Created |
| Audit Log | `/healthcare/audit/export/csv/` | Action, Actor, Actor Type, Record ID, Details, IP Address, Timestamp |
| Transactions | `/blockchain/transactions/export/csv/` | TX Hash, Type, Status, Sender, Receiver, Gas Used, Block, Timestamp |

### How to use

1. Navigate to the list page (e.g. `/healthcare/patients/`)
2. Click the **CSV** button in the top-right corner
3. Your browser downloads the file immediately

All exports require login. Unauthenticated requests redirect to `/accounts/login/`.

---

## 7. API Reference

### Authentication

All API endpoints (except login) require **Token Authentication**.

```bash
# Get token
POST /api/v1/auth/login/
{"username": "admin", "password": "your_password"}
# → {"token": "abc123...", "user_id": 1, "username": "admin"}

# Use in all subsequent requests
Authorization: Token abc123...
```

### Unified API (`/api/v1/`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/auth/login/` | POST | Authenticate and get token |
| `/api/v1/dashboard/` | GET | System-wide statistics |
| `/api/v1/networks/status/` | GET | All network health statuses |
| `/api/v1/rollup/create/` | POST | Create Layer-2 rollup batch |
| `/api/v1/rollup/submit/` | POST | Submit rollup to main chain |
| `/api/v1/cross-chain/transfer/` | POST | Initiate cross-chain transfer |
| `/api/v1/zk/verify/` | POST | Verify a ZK proof |
| `/api/v1/merkle/` | POST | Build/verify Merkle tree |
| `/api/v1/patients/{id}/records/` | GET | Get patient's medical records |
| `/api/v1/records/{id}/grant-access/` | POST | Grant access to a record |
| `/api/v1/records/{id}/audit/` | GET | Get audit trail for a record |

### Healthcare API (`/api/healthcare/api/`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/healthcare/api/patients/` | GET, POST | List or create patients |
| `/api/healthcare/api/patients/{id}/` | GET, PUT, DELETE | CRUD single patient |
| `/api/healthcare/api/hospitals/` | GET, POST | List or create hospitals |
| `/api/healthcare/api/records/` | GET, POST | List or create medical records |
| `/api/healthcare/api/records/{id}/` | GET, PUT, DELETE | CRUD single record |
| `/api/healthcare/api/records/{id}/grant_access/` | POST | Grant access |
| `/api/healthcare/api/records/{id}/verify_integrity/` | POST | Verify record hash |
| `/api/healthcare/api/audit/` | GET | List audit logs |

### Blockchain API (`/api/blockchain/api/`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/blockchain/api/networks/` | GET, POST | List or create networks |
| `/api/blockchain/api/blocks/` | GET, POST | List or create blocks |
| `/api/blockchain/api/transactions/` | GET, POST | List or create transactions |
| `/api/blockchain/api/rollup/` | POST | Create rollup batch |
| `/api/blockchain/api/dashboard/` | GET | Blockchain-specific stats |

### Cross-Chain API (`/api/cross-chain/`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/cross-chain/relay/` | POST | Relay a cross-chain message |
| `/api/cross-chain/verify/` | POST | Verify a message |
| `/api/cross-chain/status/{id}/` | GET | Get relay status |
| `/api/cross-chain/stats/` | GET | Bridge statistics |

### ZK Proofs API (`/api/zk-proofs/`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/zk-proofs/generate/` | POST | Generate ZK proof |
| `/api/zk-proofs/verify/` | POST | Verify ZK proof |
| `/api/zk-proofs/range-proof/` | POST | Generate/verify range proof |

---

## 8. Interactive API Documentation

MediChain ships with **drf-spectacular** providing auto-generated, interactive API docs:

| URL | Interface | Description |
|-----|-----------|-------------|
| `/api/docs/` | Swagger UI | Explore and test endpoints in-browser |
| `/api/redoc/` | ReDoc | Clean read-only API reference |
| `/api/schema/` | OpenAPI JSON | Raw schema for import into Postman, Insomnia, etc. |

### Using Swagger UI

1. Go to **http://127.0.0.1:8000/api/docs/**
2. Click **Authorize** and enter `Token YOUR_TOKEN` to authenticate
3. Browse endpoints by tag (Healthcare, Blockchain, ZK Proofs, etc.)
4. Click any endpoint → **Try it out** → fill parameters → **Execute**

### Importing into Postman

1. Go to `/api/schema/` and save the JSON response
2. In Postman: **Import → Raw text** → paste the JSON
3. All endpoints are imported with their request schemas

---

## 9. How the Blockchain Works

### Transaction Lifecycle

```
1. CREATE  → Patient/Hospital/Record created → Transaction status: PENDING
2. BATCH   → Rollup batch collects up to 50 pending transactions
3. PROOF   → ZK-SNARK proof generated for the batch
4. BLOCK   → New block created with Merkle root + ZK proof
5. CONFIRM → Transaction status updated to CONFIRMED
```

### Data Anchoring Strategy

- **Off-chain:** Full medical data is encrypted (AES-256-GCM) and stored in IPFS
- **On-chain:** Only the SHA-256 hash of the record metadata is stored in the blockchain
- **Privacy:** No personal health information is ever written to the blockchain
- **Verification:** Anyone with the original data can recompute the hash and verify integrity

### Block Structure

| Field | Type | Description |
|-------|------|-------------|
| block_number | BigInteger | Sequential block number |
| previous_hash | Char(64) | Hash of previous block |
| merkle_root | Char(64) | Merkle root of all transactions in block |
| rollup_proof | Text | ZK-SNARK proof payload |
| timestamp | DateTime | When block was created |
| hash | Char(64) | SHA-256 of this block |
| transaction_count | Integer | Number of transactions |

### Layer-2 Rollup

Rollup batches reduce the cost of on-chain storage:
1. Collect up to `ROLLUP_BATCH_SIZE` (default 50) pending transactions
2. Compute a Merkle tree — `RollupBatch.calculate_merkle_root()`
3. Generate a ZK-SNARK proof — `ZKProofService.generate_proof()`
4. Store only the Merkle root and proof on-chain (not all transaction data)
5. This reduces storage by ~75% compared to posting each transaction individually

---

## 10. Zero-Knowledge Proofs & Proof History

### What is a ZK Proof?

A Zero-Knowledge Proof allows a prover to demonstrate a statement is true without
revealing any information beyond the validity of the statement.

### Use Cases in MediChain

1. **Record verification:** Prove a record exists and hasn't been tampered with
2. **Cross-chain transfers:** Prove data ownership when relaying between chains
3. **Range proofs:** Prove a medical value is within a healthy range without revealing it

### Supported Types

| Type | Strengths | Use Case |
|------|-----------|----------|
| **zk-SNARK** | Small proof, fast verification | Default for rollups |
| **zk-STARK** | Quantum-resistant, no trusted setup | Future-proof security |
| **Range Proof** | Prove value ∈ [min, max] | Medical value compliance |

> **Implementation note:** MediChain's proofs are SHA-256-based simulations, not real
> cryptographic ZK circuits. `ZKProofService.verify_proof()` re-hashes the inputs and
> compares structure. Production use would require `snarkjs`, `libsnark`, or `ZoKrates`.

### ZK Proof History (`ZKProofRecord`)

Every generate and verify action through the UI is persisted in the `ZKProofRecord`
model (table `zk_proof_records`). Fields:

| Field | Description |
|-------|-------------|
| `proof_type` | zk_snark / zk_stark / range |
| `inputs` | JSON array of private inputs |
| `public_output` | Merkle root or committed value |
| `proof_payload` | Full JSON proof structure |
| `generated_by` | Username or IP of requester |
| `is_verified` | True if verification passed |
| `created_at` | Timestamp |

The **ZK Dashboard** (`/zk-proofs/`) displays the last 20 entries in the Proof History
table with colour-coded verification status badges.

---

## 11. Cross-Chain Relay

### How It Works

```
Source Chain          Relay Service           Target Chain
    │                      │                       │
    │  1. Create Message    │                       │
    │  ├─ data_hash        │                       │
    │  └─ ZK proof         │                       │
    │                      │  2. Verify            │
    │                      │  ├─ ZK proof check    │
    │                      │  └─ Nonce check       │
    │                      │                       │
    │  3. Status: RELAYED  │──────────────────────►│
```

### Security Measures

- **ZK Proof Validation:** `CrossChainRelayService` calls `ZKProofService.verify_proof()` before relaying
- **Nonce Replay Prevention:** Stubs in place (`_is_nonce_used` / `_mark_nonce_used`) — full implementation TODO
- **Status Tracking:** Messages are `PENDING → RELAYED → VERIFIED` or `REJECTED`

---

## 12. Testing

### Run Tests

```powershell
# Full suite
python manage.py test tests --verbosity=2

# Single class
python manage.py test tests.test_medichain.ZKProofServiceTest

# Single test
python manage.py test tests.test_medichain.APIIntegrationTest.test_dashboard_api

# Skip the slow PerformanceTest during iteration
python manage.py test tests.test_medichain.ZKProofServiceTest tests.test_medichain.CrossChainRelayTest tests.test_medichain.APIIntegrationTest
```

### Coverage Report

```powershell
coverage run --source='.' manage.py test tests
coverage html
# Open htmlcov/index.html in browser
```

### Test Classes

| Class | What it covers |
|-------|---------------|
| `ZKProofServiceTest` | ZK-SNARK/STARK generation and verification |
| `MerkleTreeTest` | Merkle tree construction and root computation |
| `CrossChainRelayTest` | Message creation, relay, and status updates |
| `BlockchainModelTest` | Block and Transaction SHA-256 hash auto-computation |
| `HealthcareModelTest` | Patient, Hospital, MedicalRecord model save hooks |
| `APIIntegrationTest` | DRF endpoint authentication and response status |
| `PerformanceTest` | Bulk transaction and rollup throughput (slow — skip when iterating) |

---

## 13. Production Deployment

### Docker Compose (recommended)

```bash
# Edit settings.py first: DEBUG=False, strong SECRET_KEY
docker compose up -d
```

### Gunicorn + Nginx

```bash
gunicorn medichain_project.wsgi:application --bind 0.0.0.0:8000 --workers 4 --timeout 120
```

Nginx snippet:
```nginx
location / { proxy_pass http://127.0.0.1:8000; proxy_set_header Host $host; }
location /static/ { alias /app/staticfiles/; }
location /media/ { alias /app/media/; }
```

### Security checklist

```python
DEBUG = False
ALLOWED_HOSTS = ['yourdomain.com']
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_CONTENT_TYPE_NOSNIFF = True
```

### Database backup

```bash
pg_dump -U postgres -p 5433 medichain_db > backup_$(date +%Y%m%d).sql
```

---

## 14. Troubleshooting

### "could not connect to server" (PostgreSQL)

Check PostgreSQL is running on port 5433 and `medichain_db` exists.

### Django `{{ block.xxx }}` renders empty

Any context variable named `block` is silently overridden by Django's template engine
(conflict with `{% block %}` tag). Rename the view context variable to something else
(e.g. `blk`) and update all template references.

### "export" URL captured as a hash/ID

Static paths (`.../export/csv/`) must appear **before** parameterized paths
(`.../\<str:tx_hash\>/`) in `urlpatterns`. Django matches top-to-bottom.

### Charts not rendering

Verify Chart.js is loading via CDN. The dashboard uses `{% block extra_scripts %}` in
`base.html` — not `{% block extra_js %}`. If you override `base.html`, preserve that block.

### CSV download returns 302 (redirect to login)

All CSV export views require authentication. Log in first, or include a valid session cookie.

---

*MediChain Framework v1.1 — Department of Artificial Intelligence Technologies, Ankara University*
