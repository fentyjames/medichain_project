# MediChain — Complete Usage Guide

> **MediChain** is a Scalable Cross-Chain Layer-2 Blockchain Framework for Privacy-Preserving and Interoperable Healthcare Data Exchange Using Zero-Knowledge Proofs.

**Author:** Fenty James Conteh — Department of Artificial Intelligence Technologies, Ankara University  
**Framework Version:** 1.0.0

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Prerequisites & Setup](#2-prerequisites--setup)
3. [Where to Input Data — All Entry Points](#3-where-to-input-data--all-entry-points)
4. [Module-by-Module Usage](#4-module-by-module-usage)
5. [API Reference](#5-api-reference)
6. [How the Blockchain Works](#6-how-the-blockchain-works)
7. [Zero-Knowledge Proofs](#7-zero-knowledge-proofs)
8. [Cross-Chain Relay](#8-cross-chain-relay)
9. [Testing](#9-testing)
10. [Production Deployment](#10-production-deployment)
11. [Troubleshooting](#11-troubleshooting)

---

## 1. Architecture Overview

MediChain is a Django-based web application with **four core modules** and a **unified API layer**:

```
┌─────────────────────────────────────────────────────┐
│                    Frontend (Templates)              │
│  base.html ← All pages extend this dark-themed UI   │
│  ├── index.html          (Main Dashboard)           │
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
│  └── api/zk-proofs/      (Proof generation)         │
├─────────────────────────────────────────────────────┤
│                    Core Modules                      │
│  ├── blockchain/          (Blocks, Txs, Rollups)    │
│  ├── healthcare/          (Patients, Records, Acls) │
│  ├── cross_chain/         (Relay service, messages) │
│  └── zk_proofs/           (ZK-SNARK/STARK proofs)   │
└─────────────────────────────────────────────────────┘
```

**Key Models:**

| Model | App | Purpose |
|-------|-----|---------|
| `Patient` | healthcare | Patient identity with public key |
| `Hospital` | healthcare | Hospital registration & identity |
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

---

## 2. Prerequisites & Setup

### System Requirements

| Software | Minimum Version | Download |
|----------|-----------------|----------|
| Python | 3.10 | [python.org](https://www.python.org/downloads/) |
| PostgreSQL | 14 | [postgresql.org](https://www.postgresql.org/download/) |
| Redis | 6.0 | [redis.io](https://redis.io/download) |
| Git | 2.40 | [git-scm.com](https://git-scm.com/downloads) |

### Quick Setup (Using the Automated Script)

```bash
# 1. Navigate to project directory
cd /path/to/medichain_project

# 2. Run the automated setup script
chmod +x setup.sh
./setup.sh

# 3. Follow prompts (creates venv, installs deps, runs migrations, optional superuser)
```

### Manual Setup

```bash
# 1. Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate          # Linux/macOS
# venv\Scripts\activate           # Windows

# 2. Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 3. Configure database (PostgreSQL)
# Create .env file in medichain_project/ directory:

# .env
DEBUG=True
SECRET_KEY=your-secure-secret-key-change-this
ALLOWED_HOSTS=localhost,127.0.0.1
DB_NAME=medichain_db
DB_USER=medichain_user
DB_PASSWORD=your_secure_password
DB_HOST=localhost
DB_PORT=5432
REDIS_URL=redis://localhost:6379/0

# 4. Create PostgreSQL database
sudo -u postgres psql
-- CREATE DATABASE medichain_db;
-- CREATE USER medichain_user WITH PASSWORD 'your_secure_password';
-- GRANT ALL PRIVILEGES ON DATABASE medichain_db TO medichain_user;
-- \q

# 5. Run migrations
python manage.py migrate --database=default
python manage.py migrate --database=blockchain

# 6. Create admin user
python manage.py createsuperuser

# 7. Collect static files
python manage.py collectstatic --noinput

# 8. Start the server
python manage.py runserver
```

**Access the application:** `http://localhost:8000/`

---

## 3. Where to Input Data — All Entry Points

### 🩺 A. Register a Patient

**UI:** Navigate to `Healthcare → Add Patient` or `http://localhost:8000/healthcare/patients/add/`

**Form Fields:**

| Field | Required | Description |
|-------|----------|-------------|
| **Public Key** | ✅ | Cryptographic public key for blockchain identity |
| **Date of Birth** | ❌ | Patient's date of birth |
| **Blood Type** | ❌ | A+, A-, B+, B-, AB+, AB-, O+, O- |
| **Allergies** | ❌ | Known allergies (free text) |
| **Emergency Contact** | ❌ | Phone number (e.g., +90-555-123-4567) |

**API:**
```bash
POST /api/healthcare/patients/
Authorization: Token YOUR_TOKEN
Content-Type: application/json

{
  "public_key": "0xPatientPublicKeyHere",
  "blood_type": "A+",
  "allergies": "Penicillin",
  "emergency_contact": "+90-555-123-4567"
}
```

**Backend Logic** (`healthcare/views.py` → `PatientViewSet.create`):
- Creates a `Patient` record with auto-generated `patient_id` (SHA-256 hash of UUID + timestamp)
- Only stores the hash on-chain, not personal data directly

---

### 🏥 B. Register a Hospital

**UI:** Navigate to `Healthcare → Add Hospital` or `http://localhost:8000/healthcare/hospitals/add/`

**Form Fields:**

| Field | Required | Description |
|-------|----------|-------------|
| **Hospital Name** | ✅ | Full name (e.g., "Ankara University Hospital") |
| **License Number** | ✅ | Government-issued license (e.g., "LIC-2025-001") |
| **Address** | ❌ | Full hospital address |
| **Public Key** | ✅ | Hospital's cryptographic public key |
| **Blockchain Network** | ❌ | Link to an active blockchain network |

**API:**
```bash
POST /api/healthcare/hospitals/
Authorization: Token YOUR_TOKEN
Content-Type: application/json

{
  "name": "Ankara University Hospital",
  "address": "Ankara, Turkey",
  "license_number": "LIC-2025-001",
  "public_key": "0xHospitalPublicKey"
}
```

**Backend Logic** (`healthcare/views.py` → `HospitalViewSet.create`):
- Auto-generates `hospital_id` as SHA-256 hash
- Can optionally link to a blockchain network for on-chain anchoring

---

### 📄 C. Create a Medical Record

**UI:** Navigate to `Healthcare → Add Record` or `http://localhost:8000/healthcare/records/add/`

**Form Fields:**

| Field | Required | Description |
|-------|----------|-------------|
| **Patient** | ✅ | Dropdown of registered patients |
| **Hospital** | ✅ | Dropdown of registered hospitals |
| **Record Type** | ✅ | DIAGNOSIS, LAB_RESULT, PRESCRIPTION, IMAGING, SURGERY, DISCHARGE, INSURANCE |
| **Title** | ✅ | Short title (e.g., "Annual Health Checkup 2025") |
| **Description** | ❌ | Detailed medical description |
| **Medical File** | ❌ | Upload PDF, JPG, PNG, or DICOM file (encrypted → IPFS) |
| **IPFS Hash** | ❌ | Pre-uploaded IPFS CID (Qm...) |
| **Digital Signature** | ✅ | ECDSA signature of record hash |

**Data Flow on Record Creation:**
1. Record metadata is collected and validated
2. SHA-256 hash is computed for integrity verification
3. File is encrypted with AES-256-GCM and uploaded to IPFS
4. Hash + IPFS CID are submitted as a blockchain transaction
5. Transaction is batched in Layer-2 rollup with ZK proof

**API:**
```bash
POST /api/healthcare/records/
Authorization: Token YOUR_TOKEN
Content-Type: application/json

{
  "patient_id": "PATIENT_ID",
  "hospital_id": "HOSPITAL_ID",
  "record_type": "DIAGNOSIS",
  "title": "Annual Health Checkup",
  "description": "Patient shows normal vital signs...",
  "ipfs_hash": "QmTestHash123",
  "signature": "ECDSA_SIGNATURE_HERE",
  "file_size": 102400
}
```

**Backend Logic** (`healthcare/views.py` → `MedicalRecordViewSet.create`):
- Creates `MedicalRecord` with auto-computed `data_hash`
- Creates a `Transaction` (tx_type='CREATE', status='PENDING')
- Creates an `AuditLog` entry for compliance

---

### 🔑 D. Grant Access Permission

**UI:** Navigate to `Healthcare → Grant Access` or `http://localhost:8000/healthcare/permissions/add/`

**Form Fields:**

| Field | Required | Description |
|-------|----------|-------------|
| **Record** | ✅ | Dropdown of medical records |
| **Patient (Grantor)** | ✅ | Patient granting the access |
| **Grantee ID** | ✅ | Hospital/Lab/Doctor ID receiving access |
| **Grantee Type** | ✅ | HOSPITAL, LAB, INSURANCE, DOCTOR |
| **Permission Type** | ✅ | READ (Read Only), WRITE (Read+Write), SHARE (Share with Others) |
| **Valid Until** | ❌ | Expiration date/time (nullable) |
| **Purpose** | ✅ | HIPAA-required purpose (e.g., "Emergency treatment") |
| **Patient Digital Signature** | ✅ | ECDSA authorization signature |

**API:**
```bash
POST /api/records/{record_id}/grant-access/
Authorization: Token YOUR_TOKEN
Content-Type: application/json

{
  "grantee": "HOSPITAL_ID",
  "grantee_type": "HOSPITAL",
  "permission_type": "READ",
  "purpose": "Second opinion consultation",
  "signature": "PATIENT_ECDSA_SIGNATURE",
  "valid_until": "2026-01-01T00:00:00Z"
}
```

**Backend Logic** (`healthcare/views.py` → `permission_add`):
- Creates `AccessPermission` linked to the record and patient
- Logs a `SHARE` action in `AuditLog`
- Access is revocable by deleting the permission record

---

### ⛓️ E. Create a Blockchain Transaction (Direct)

**UI:** Navigate to `Blockchain → Create Transaction` or `http://localhost:8000/blockchain/transactions/add/`

**Form Fields:**

| Field | Required | Description |
|-------|----------|-------------|
| **Transaction Type** | ✅ | CREATE, UPDATE, SHARE, VERIFY, ACCESS |
| **Sender ID** | ✅ | Hospital or Patient ID |
| **Receiver ID** | ❌ | Target entity ID (optional) |
| **Data Hash** | ✅ | SHA-256 hash of the data |
| **Digital Signature** | ✅ | ECDSA signature |

**API:**
```bash
POST /api/blockchain/transactions/
Authorization: Token YOUR_TOKEN
Content-Type: application/json

{
  "tx_type": "CREATE",
  "sender": "HOSPITAL_ID",
  "receiver": "PATIENT_ID",
  "data_hash": "abc123...",
  "signature": "ECDSA_SIGNATURE"
}
```

---

### 📦 F. Create a Rollup Batch

**UI:** Navigate to `Blockchain → Create Rollup` or `http://localhost:8000/blockchain/rollups/create/`

**Form Fields:**

| Field | Required | Description |
|-------|----------|-------------|
| **Blockchain Network** | ✅ | Select active network |

**How Rollup Batching Works:**
1. All pending transactions are collected (up to 50)
2. A Merkle tree is built from transaction hashes
3. A ZK-SNARK proof is generated for the batch
4. Only the Merkle root + proof are submitted on-chain
5. This reduces gas costs by ~75%

**API:**
```bash
POST /api/v1/rollup/create/
Authorization: Token YOUR_TOKEN
Content-Type: application/json

{
  "network_id": "ethereum_main"
}
```

**Backend Logic** (`blockchain/views.py` → `rollup_create`):
- Fetches all PENDING transactions not yet in a block
- Creates `RollupBatch` with calculated Merkle root
- Calls `ZKProofService.generate_proof()` on transaction hashes
- Updates transaction statuses to 'BATCHED'

---

### 🔄 G. Cross-Chain Transfer

**UI:** Navigate to `Cross-Chain → Transfer` or `http://localhost:8000/cross-chain/transfer/`

**Form Fields:**

| Field | Required | Description |
|-------|----------|-------------|
| **Source Chain** | ✅ | Dropdown of active blockchain networks |
| **Target Chain** | ✅ | Dropdown of active blockchain networks |
| **Data Hash** | ✅ | SHA-256 hash of data to transfer |
| **ZK Proof** | ✅ | JSON proof for data verification |
| **Sender ID** | ✅ | Hospital or entity ID |

**Security Verification:**
- Message signature is verified
- ZK proof is validated
- Nonce is checked for replay attack prevention
- Relay node verifies before forwarding

**API:**
```bash
POST /api/v1/cross-chain/transfer/
Authorization: Token YOUR_TOKEN
Content-Type: application/json

{
  "source_chain": "ethereum_main",
  "target_chain": "polygon",
  "data_hash": "data_hash_here",
  "proof": "zk_proof_here",
  "sender": "hospital_1"
}
```

**Backend Logic** (`cross_chain/views.py` → `crosschain_transfer`):
- Calls `CrossChainRelayService.create_message()` to build the message
- Calls `CrossChainRelayService.relay_message()` to relay it
- Stores the `CrossChainMessage` in the database with status

---

### 🔐 H. Generate a Zero-Knowledge Proof

**UI:** Navigate to `ZK Proofs → Generate` or `http://localhost:8000/zk-proofs/generate/`

**Form Fields:**

| Field | Required | Description |
|-------|----------|-------------|
| **Private Inputs** | ✅ | Transaction hashes (one per line) — never revealed |
| **Public Output** | ✅ | SHA-256 Merkle root — public commitment |
| **Proof Type** | ❌ | zk-SNARK (recommended) or zk-STARK (quantum resistant) |

**API:**
```bash
POST /api/zk-proofs/generate/
Authorization: Token YOUR_TOKEN
Content-Type: application/json

{
  "inputs": ["tx_hash_1", "tx_hash_2", "tx_hash_3"],
  "public_output": "merkle_root_hash",
  "proof_type": "zk_snark"
}
```

**Backend Logic** (`zk_proofs/views.py` → `zk_generate`):
- Creates a `ZKProofService` instance with the selected proof type
- Generates proof using `_simulate_proof()` (production would use `snarkjs`, `libsnark`, or `ZoKrates`)
- Returns JSON proof containing: proof type, timestamp, public inputs, private inputs hash, proof values, verification key

---

### ✅ I. Verify a Zero-Knowledge Proof

**UI:** Navigate to `ZK Proofs → Verify` or `http://localhost:8000/zk-proofs/verify/`

**Form Fields:**

| Field | Required | Description |
|-------|----------|-------------|
| **Proof JSON** | ✅ | Paste the ZK proof JSON |
| **Public Output (Merkle Root)** | ✅ | Expected Merkle root |
| **Expected Inputs** | ❌ | Transaction hashes to verify against |
| **Proof Type** | ❌ | zk-SNARK or zk-STARK |

**API:**
```bash
POST /api/zk-proofs/verify/
Authorization: Token YOUR_TOKEN
Content-Type: application/json

{
  "proof": "{\"proof_type\": \"zk_snark\", ...}",
  "public_output": "merkle_root_hash",
  "expected_inputs": ["tx_hash_1", "tx_hash_2"],
  "proof_type": "zk_snark"
}
```

**Verification Steps** (in `zk_proofs/zk_service.py` → `verify_proof`):
1. Verify proof type matches
2. Verify public inputs match the provided Merkle root
3. Verify input count matches expected inputs
4. Verify input hash matches computed hash of expected inputs
5. Verify proof structure has all required keys

---

### 📏 J. Generate a Range Proof

**UI:** Navigate to `ZK Proofs → Range Proof` or `http://localhost:8000/zk-proofs/range/`

**Form Fields:**

| Field | Required | Description |
|-------|----------|-------------|
| **Value** | ✅ | The value to prove (e.g., blood pressure 120) |
| **Min** | ✅ | Minimum healthy range (e.g., 90) |
| **Max** | ✅ | Maximum healthy range (e.g., 140) |

**Use Case:** Prove that a medical value (blood pressure, glucose level, etc.) falls within a healthy range **without revealing the exact value** — critical for HIPAA compliance.

**API:**
```bash
POST /api/zk-proofs/range-proof/
Authorization: Token YOUR_TOKEN
Content-Type: application/json

{
  "action": "generate",
  "value": 120,
  "min": 90,
  "max": 140
}
```

To verify:
```bash
POST /api/zk-proofs/range-proof/
Authorization: Token YOUR_TOKEN
Content-Type: application/json

{
  "action": "verify",
  "proof": "<proof_json>",
  "min": 90,
  "max": 140
}
```

---

## 4. Module-by-Module Usage

### Healthcare Module

**Dashboard** (`http://localhost:8000/healthcare/`)
- Displays counts: patients, hospitals, records, permissions
- Shows recent patients and recent records in tables
- Quick action buttons for all CRUD operations

**Patient Management:**
- **List:** `http://localhost:8000/healthcare/patients/`
- **Add:** `http://localhost:8000/healthcare/patients/add/`
- **Detail:** `http://localhost:8000/healthcare/patients/{patient_id}/`

**Hospital Management:**
- **List:** `http://localhost:8000/healthcare/hospitals/`
- **Add:** `http://localhost:8000/healthcare/hospitals/add/`
- **Detail:** `http://localhost:8000/healthcare/hospitals/{hospital_id}/`

**Medical Records:**
- **List:** `http://localhost:8000/healthcare/records/`
- **Add:** `http://localhost:8000/healthcare/records/add/`
- **Detail:** `http://localhost:8000/healthcare/records/{record_id}/` — shows permissions and audit logs

**Access Control:**
- **Grant:** `http://localhost:8000/healthcare/permissions/add/`
- Patients grant access to hospitals/labs/insurance via digital signatures
- Each permission has a type (READ/WRITE/SHARE), purpose, and optional expiration

### Blockchain Module

**Dashboard** (`http://localhost:8000/blockchain/`)
- Stats: total blocks, transactions, pending, validators
- Recent blocks table with hash, Merkle root, TX count, network, time
- Active networks list with consensus type

**Blocks:** `http://localhost:8000/blockchain/blocks/`
**Transactions:** `http://localhost:8000/blockchain/transactions/`
**Rollups:** `http://localhost:8000/blockchain/rollups/`

### Cross-Chain Module

**Dashboard** (`http://localhost:8000/cross-chain/`)
- Total messages, relayed, pending, rejected counts
- Message list with source chain, target chain, status

**Transfer:** `http://localhost:8000/cross-chain/transfer/`
**Message Detail:** `http://localhost:8000/cross-chain/{message_id}/`

### ZK Proofs Module

**Dashboard** (`http://localhost:8000/zk-proofs/`)
- Navigation to generate, verify, and range proof pages

**Generate:** `http://localhost:8000/zk-proofs/generate/`
**Verify:** `http://localhost:8000/zk-proofs/verify/`
**Range:** `http://localhost:8000/zk-proofs/range/`

---

## 5. API Reference

### Authentication

All API endpoints (except login) require **Token Authentication**.

```bash
# Get token
POST /api/v1/auth/login/
{
  "username": "admin",
  "password": "your_password"
}

# Response: {"token": "abc123...", "user_id": 1, "username": "admin"}

# Use token in subsequent requests
Authorization: Token abc123...
```

### Unified API Endpoints (`api/v1/`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/auth/login/` | POST | Authenticate and get token |
| `/api/v1/dashboard/` | GET | System-wide statistics |
| `/api/v1/networks/status/` | GET | All network health statuses |
| `/api/v1/rollup/create/` | POST | Create a Layer-2 rollup batch |
| `/api/v1/rollup/submit/` | POST | Submit rollup batch to main chain |
| `/api/v1/cross-chain/transfer/` | POST | Initiate cross-chain transfer |
| `/api/v1/zk/verify/` | POST | Verify a ZK proof |
| `/api/v1/merkle/` | POST | Build/verify Merkle tree |
| `/api/v1/patients/{id}/records/` | GET | Get patient's medical records |
| `/api/v1/records/{id}/grant-access/` | POST | Grant access to a record |
| `/api/v1/records/{id}/audit/` | GET | Get audit trail for a record |

### Healthcare API (`api/healthcare/`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/healthcare/patients/` | GET, POST | List or create patients |
| `/api/healthcare/patients/{id}/` | GET, PUT, DELETE | CRUD single patient |
| `/api/healthcare/patients/{id}/records/` | GET | Get patient's records |
| `/api/healthcare/hospitals/` | GET, POST | List or create hospitals |
| `/api/healthcare/hospitals/{id}/` | GET, PUT, DELETE | CRUD single hospital |
| `/api/healthcare/records/` | GET, POST | List or create medical records |
| `/api/healthcare/records/{id}/` | GET, PUT, DELETE | CRUD single record |
| `/api/healthcare/records/{id}/grant_access/` | POST | Grant access to record |
| `/api/healthcare/records/{id}/verify_integrity/` | POST | Verify record hash |
| `/api/healthcare/records/{id}/zk_verify/` | POST | ZK verify record |
| `/api/healthcare/audit/` | GET | List audit logs |

### Blockchain API (`api/blockchain/`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/blockchain/networks/` | GET, POST | List or create networks |
| `/api/blockchain/blocks/` | GET, POST | List or create blocks |
| `/api/blockchain/transactions/` | GET, POST | List or create transactions |
| `/api/blockchain/rollup/` | POST | Create rollup batch |
| `/api/blockchain/consensus/` | GET | Consensus info |
| `/api/blockchain/dashboard/` | GET | Blockchain-specific dashboard stats |

### Cross-Chain API (`api/cross-chain/`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/cross-chain/relay/` | POST | Relay a cross-chain message |
| `/api/cross-chain/verify/` | POST | Verify a cross-chain message |
| `/api/cross-chain/status/{message_id}/` | GET | Get relay status |
| `/api/cross-chain/stats/` | GET | Bridge statistics |

### ZK Proofs API (`api/zk-proofs/`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/zk-proofs/generate/` | POST | Generate ZK proof |
| `/api/zk-proofs/verify/` | POST | Verify ZK proof |
| `/api/zk-proofs/range-proof/` | POST | Generate/verify range proof |

---

## 6. How the Blockchain Works

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
| previous_hash | Char(64) | Hash of previous block (chain linkage) |
| merkle_root | Char(64) | Merkle root of all transactions in block |
| rollup_proof | Text | ZK-SNARK proof for the rollup batch |
| timestamp | DateTime | When block was created |
| nonce | BigInteger | Proof-of-work or consensus nonce |
| hash | Char(64) | SHA-256 hash of this block |
| transaction_count | Integer | Number of transactions in block |

---

## 7. Zero-Knowledge Proofs

### What is a ZK Proof?

A Zero-Knowledge Proof allows one party (the prover) to prove to another party (the verifier) that a statement is true **without revealing any information beyond the validity of the statement itself**.

### Use Cases in MediChain

1. **Medical Record Verification:** Prove a record exists and hasn't been tampered with without revealing the record contents.
2. **Cross-Chain Transfers:** Prove ownership of data on one chain without revealing the data when transferring to another chain.
3. **Range Proofs:** Prove that a medical value (blood pressure, glucose, etc.) is within a healthy range without revealing the exact value.

### Supported Proof Types

| Type | Strengths | Use Case |
|------|-----------|----------|
| **zk-SNARK** | Small proof size, fast verification | Default for rollups and transfers |
| **zk-STARK** | Quantum-resistant, no trusted setup | Future-proof security |
| **Range Proof** | Prove value within [min, max] | Medical value compliance |

### How Proofs are Generated

1. **Private Inputs:** Transaction hashes or data values that must remain secret
2. **Public Output:** Merkle root or committed value that can be publicly verified
3. **Proof Generation:** `ZKProofService.generate_proof(inputs, public_output)` creates a JSON proof
4. **Verification:** `ZKProofService.verify_proof(proof, public_output, expected_inputs)` returns True/False

---

## 8. Cross-Chain Relay

### Supported Networks

| Network ID | Name | Chain ID | Consensus |
|------------|------|----------|-----------|
| ethereum_main | Ethereum Mainnet | 1 | PoS |
| polygon | Polygon | 137 | PoS |
| hyperledger | Hyperledger Fabric | 999 | PBFT |

### How Cross-Chain Transfer Works

```
Source Chain                Relay Service              Target Chain
    │                            │                           │
    │  1. Create Message         │                           │
    │  ├─ data_hash             │                           │
    │  ├─ proof (ZK)            │                           │
    │  └─ sender signature      │                           │
    │                            │                           │
    │                            │  2. Verify Message         │
    │                            │  ├─ Check signature       │
    │                            │  ├─ Validate ZK proof     │
    │                            │  └─ Replay attack check   │
    │                            │                           │
    │  3. Status: RELAYED        │                           │
    │◄───────────────────────────│──────────────────────────►│
```

### Security Measures

- **Signature Verification:** Every message is signed with the sender's private key
- **ZK Proof Validation:** Proof must verify against the data hash
- **Replay Attack Prevention:** Each message has a unique nonce (checked against history)
- **Status Tracking:** Messages can be PENDING, RELAYED, or REJECTED

---

## 9. Testing

### Run All Tests

```bash
python manage.py test tests --verbosity=2
```

**Expected Output:**
```
test_generate_proof (tests.test_medichain.ZKProofServiceTest) ... ok
test_verify_proof_valid (tests.test_medichain.ZKProofServiceTest) ... ok
test_create_message (tests.test_medichain.CrossChainRelayTest) ... ok
test_dashboard_api (tests.test_medichain.APIIntegrationTest) ... ok
...
Ran 25 tests in 3.456s
OK
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
pip install coverage
coverage run --source='.' manage.py test tests
coverage html
# Open htmlcov/index.html in your browser
```

---

## 10. Production Deployment

### Security Settings (`medichain_project/settings.py`)

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

### Using Gunicorn

```bash
pip install gunicorn
gunicorn medichain_project.wsgi:application --bind 0.0.0.0:8000 --workers 4
```

### Nginx Reverse Proxy

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

### SSL/TLS with Let's Encrypt

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com
```

### Database Backup

```bash
# Backup PostgreSQL database
pg_dump -U medichain_user medichain_db > backup_$(date +%Y%m%d).sql

# Restore from backup
psql -U medichain_user medichain_db < backup_20250101.sql
```

---

## 11. Troubleshooting

### Issue: "Command not found: python"
```bash
# Use python3 instead
python3 -m venv venv
python3 manage.py runserver
```

### Issue: "psycopg2.errors.InsufficientPrivilege"
```sql
-- In psql
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO medichain_user;
ALTER USER medichain_user CREATEDB;
```

### Issue: "django.db.utils.OperationalError: could not connect to server"
```bash
# Ensure PostgreSQL is running
sudo systemctl start postgresql    # Linux
brew services start postgresql     # macOS
# Windows: Start from Services panel
```

### Issue: "ImportError: No module named 'rest_framework'"
```bash
source venv/bin/activate           # Linux/macOS
# or
venv\Scripts\activate              # Windows
pip install -r requirements.txt
```

### Issue: "Port 8000 already in use"
```bash
python manage.py runserver 8080
# or
python manage.py runserver 9000
```

### Issue: CSRF errors in API requests
```bash
# For testing, use Token Authentication in headers
Authorization: Token YOUR_TOKEN
# Token is obtained via POST /api/v1/auth/login/
```

---

## Quick Reference — All Data Input Points

| # | Action | URL (UI) | API Endpoint | Key Fields |
|---|--------|----------|--------------|------------|
| 1 | **Register Patient** | `/healthcare/patients/add/` | `POST /api/healthcare/patients/` | public_key, blood_type, allergies, emergency_contact |
| 2 | **Register Hospital** | `/healthcare/hospitals/add/` | `POST /api/healthcare/hospitals/` | name, license_number, public_key, blockchain_network |
| 3 | **Create Medical Record** | `/healthcare/records/add/` | `POST /api/healthcare/records/` | patient_id, hospital_id, record_type, title, description, ipfs_hash, signature |
| 4 | **Grant Access** | `/healthcare/permissions/add/` | `POST /api/records/{id}/grant-access/` | record_id, patient_id, grantee, grantee_type, permission_type, purpose, signature |
| 5 | **Create Transaction** | `/blockchain/transactions/add/` | `POST /api/blockchain/transactions/` | tx_type, sender, receiver, data_hash, signature |
| 6 | **Create Rollup** | `/blockchain/rollups/create/` | `POST /api/v1/rollup/create/` | network_id |
| 7 | **Cross-Chain Transfer** | `/cross-chain/transfer/` | `POST /api/v1/cross-chain/transfer/` | source_chain, target_chain, data_hash, proof, sender |
| 8 | **Generate ZK Proof** | `/zk-proofs/generate/` | `POST /api/zk-proofs/generate/` | inputs, public_output, proof_type |
| 9 | **Verify ZK Proof** | `/zk-proofs/verify/` | `POST /api/zk-proofs/verify/` | proof, public_output, expected_inputs, proof_type |
| 10 | **Range Proof** | `/zk-proofs/range/` | `POST /api/zk-proofs/range-proof/` | value, min, max |

---

## Configuration — `settings.py` MediChain Section

```python
MEDICHAIN_CONFIG = {
    'BLOCKCHAIN_NETWORKS': [
        {'id': 'ethereum_main', 'name': 'Ethereum Mainnet', 'chain_id': 1, 'rpc_url': 'https://mainnet.infura.io/v3/'},
        {'id': 'polygon', 'name': 'Polygon', 'chain_id': 137, 'rpc_url': 'https://polygon-rpc.com'},
        {'id': 'hyperledger', 'name': 'Hyperledger Fabric', 'chain_id': 999, 'rpc_url': 'http://localhost:7051'},
    ],
    'ROLLUP_BATCH_SIZE': 50,
    'ZK_PROOF_TYPE': 'zk_snark',
    'CROSS_CHAIN_RELAY_INTERVAL': 1.0,
    'IPFS_GATEWAY': 'https://ipfs.io/ipfs/',
    'ENCRYPTION_ALGORITHM': 'AES-256-GCM',
    'HASH_FUNCTION': 'SHA-256',
    'CONSENSUS_MECHANISM': 'PBFT',
    'BLOCK_TIME': 12,
}
```

---

## UI Theme Options

The application features **four built-in themes**, cycled via the moon/sun icon button in the top-right navbar:

1. **Dark Theme** (default) — Deep navy background, cyan accents
2. **Light Theme** — Clean white background, blue accents
3. **Blue-Black Theme** — Near-black with electric blue borders
4. **Warm-Dark Theme** — Brown/amber tones for reduced eye strain

The sidebar also supports **collapse/expand** via the chevron button.

---

## Summary

MediChain provides a complete framework for **privacy-preserving healthcare data exchange** using:

- **Blockchain anchoring** — SHA-256 hashes of medical records stored on-chain
- **Layer-2 Rollups** — 50 transactions batched per block with 75% gas reduction
- **Zero-Knowledge Proofs** — Verify data integrity without revealing contents
- **Cross-Chain Relay** — Interoperability between Ethereum, Polygon, and Hyperledger
- **Fine-grained Access Control** — Patient-controlled permissions with audit trails
- **HIPAA/GDPR Compliance** — No PHI stored on-chain; AES-256-GCM encryption for off-chain data

All interaction points — whether through the web UI or REST API — ultimately create, read, update, or query the core models: **Patients**, **Hospitals**, **MedicalRecords**, **Transactions**, **Blocks**, **RollupBatches**, and **CrossChainMessages**.