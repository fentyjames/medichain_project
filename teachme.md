# MediChain — Step-by-Step Usage Guide

MediChain is a simulated healthcare blockchain platform built with Django. It manages patients,
hospitals, medical records, and access permissions — anchored to a simulated Layer-2 blockchain
with ZK proofs and cross-chain messaging.

---

## Table of Contents

1. [Start the Server](#1-start-the-server)
2. [Create a Superuser Account](#2-create-a-superuser-account)
3. [Log In](#3-log-in)
4. [Set Up a Blockchain Network (Admin Panel)](#4-set-up-a-blockchain-network-admin-panel)
5. [Add a Hospital](#5-add-a-hospital)
6. [Add a Laboratory](#6-add-a-laboratory)
7. [Add an Insurance Provider](#7-add-an-insurance-provider)
8. [Register a Patient](#8-register-a-patient)
9. [Create a Medical Record](#9-create-a-medical-record)
10. [Grant Access to a Record](#10-grant-access-to-a-record)
11. [Create a Blockchain Transaction](#11-create-a-blockchain-transaction)
12. [Create a Rollup Batch (Layer-2)](#12-create-a-rollup-batch-layer-2)
13. [Send a Cross-Chain Message](#13-send-a-cross-chain-message)
14. [Use ZK Proofs](#14-use-zk-proofs)
15. [View Reports](#15-view-reports)
16. [Read the Audit Log](#16-read-the-audit-log)
17. [Edit and Delete Records](#17-edit-and-delete-records)
18. [Using the Admin Panel](#18-using-the-admin-panel)
19. [Full Workflow Example (End to End)](#19-full-workflow-example-end-to-end)

---

## 1. Start the Server

Open a terminal in the project root folder (`E:\medichain_project`) and run:

```powershell
# Activate the virtual environment (Windows PowerShell)
.\venv\Scripts\activate

# Apply any pending database migrations
python manage.py migrate

# Start the development server
python manage.py runserver
```

The application will be available at: **http://127.0.0.1:8000/**

> **Note:** The server auto-reloads when you change template or Python files.
> Stop it with `Ctrl+C`.

---

## 2. Create a Superuser Account

You only need to do this once. Stop the server (or open a second terminal), then run:

```powershell
.\venv\Scripts\activate
python manage.py createsuperuser
```

You will be prompted for:
- **Username** — e.g. `admin`
- **Email address** — e.g. `admin@medichain.com`
- **Password** — choose something you will remember (min 8 chars)

Example:
```
Username: admin
Email: admin@medichain.com
Password: ••••••••
Password (again): ••••••••
Superuser created successfully.
```

> The superuser can access both the main app and the Django Admin Panel at `/admin/`.

---

## 3. Log In

1. Go to **http://127.0.0.1:8000/**
2. Click **Sign In** in the top-right corner (or go to `/accounts/login/`)
3. Enter your username and password
4. You will land on the **main dashboard** at `/dashboard/`

The sidebar on the left gives you access to every section of the application.

---

## 4. Set Up a Blockchain Network (Admin Panel)

> **Why:** Hospitals, rollup batches, blocks, and cross-chain messages all require a
> Blockchain Network to exist first. This is the foundation everything else builds on.
> Blockchain Networks are managed through the Django Admin Panel because they are
> infrastructure-level configuration, not day-to-day data entry.

### Steps

1. Go to **http://127.0.0.1:8000/admin/**
2. Log in with your superuser credentials
3. In the left panel under **BLOCKCHAIN**, click **Blockchain networks**
4. Click **ADD BLOCKCHAIN NETWORK** (top right)
5. Fill in the form:

| Field | Example Value | Notes |
|---|---|---|
| Network ID | `medichain-mainnet` | Unique identifier, no spaces |
| Name | `MediChain Mainnet` | Display name |
| Chain ID | `1001` | Any integer, must be unique per network |
| RPC URL | `http://localhost:8545` | Simulated — can be any valid URL format |
| Consensus type | `PBFT` | Options: `PBFT`, `PoS`, `PoW` |
| Is active | ✓ checked | Must be checked for it to appear in dropdowns |

6. Click **SAVE**

> **Tip:** Create at least **two** networks (e.g. `MediChain Mainnet` and `MediChain Testnet`)
> so you can use the cross-chain messaging feature later.

---

## 5. Add a Hospital

Hospitals are required before you can create medical records — every record must be
linked to the hospital where it was created.

### Steps

1. In the sidebar click **Hospitals**, or go to `/healthcare/hospitals/`
2. Click the **+ Add Hospital** button (top right)
3. Fill in the form:

| Field | Example Value | Notes |
|---|---|---|
| Hospital Name | `Ankara University Hospital` | Required |
| Address | `06100 Sıhhiye, Ankara` | Optional but recommended |
| License Number | `HOSP-TR-2024-001` | Required, must be unique |
| Public Key | `MIIBIjANBgkq...` | Cryptographic key — paste any text for simulation |
| Blockchain Network | `MediChain Mainnet` | Select from dropdown (must exist — see Step 4) |

4. Click **Register Hospital**
5. You will be redirected to the Hospital list

> **Tip:** After creation, click the hospital name to open its detail page.
> You will see its records, a "Verified" / "Pending" badge, and buttons to Edit or generate a Report.
> To mark a hospital as Verified, click **Edit** and check the "Verified hospital" checkbox.

---

## 6. Add a Laboratory

Laboratories are affiliated with hospitals and can be granted access to lab result records.

### Steps

1. In the sidebar click **Laboratories**, or go to `/healthcare/labs/`
2. Click **+ Add Laboratory**
3. Fill in the form:

| Field | Example Value | Notes |
|---|---|---|
| Laboratory Name | `Central Pathology Lab` | Required |
| Accreditation | `ISO 15189` | Certification standard |
| Public Key | `MIIBIjANBgkq...` | Any text for simulation |
| Affiliated Hospital | `Ankara University Hospital` | Select from dropdown — optional |

4. Click **Register Laboratory**

> The lab's detail page shows a Quick Actions sidebar with Edit, Create Lab Result,
> Report, and Print buttons.

---

## 7. Add an Insurance Provider

Insurance providers can be granted access to insurance claim records.

### Steps

1. In the sidebar click **Insurance**, or go to `/healthcare/insurance/`
2. Click **+ Add Provider**
3. Fill in the form:

| Field | Example Value | Notes |
|---|---|---|
| Provider Name | `National Health Insurance` | Required |
| License Number | `INS-TR-2024-001` | Required |
| Public Key | `MIIBIjANBgkq...` | Any text for simulation |

4. Click **Register Provider**

---

## 8. Register a Patient

Patients are the central entity — all medical records, permissions, and audit events
connect back to a patient.

### Steps

1. In the sidebar click **Patients**, or go to `/healthcare/patients/`
2. Click **+ Register Patient**
3. Fill in the form:

| Field | Example Value | Notes |
|---|---|---|
| Public Key | `MIIBIjANBgkq...` | Required — patient's cryptographic identity |
| Date of Birth | `1985-03-15` | Optional |
| Blood Type | `A+` | Select from dropdown |
| Known Allergies | `Penicillin` | Optional, free text |
| Emergency Contact | `Ali Yılmaz — 0532 xxx xx xx` | Optional |

4. Click **Register Patient**

> **Linking a patient to a user account:**
> The `Patient` model has an optional `user` foreign key. To link a patient to a login account,
> go to the **Admin Panel → Healthcare → Patients**, open the patient record, and set the `User` field.
> Once linked, the patient's full name and email will appear throughout the app.

---

## 9. Create a Medical Record

Medical records are the core data of the system. Each record is cryptographically hashed
and optionally anchored to a blockchain transaction.

### Steps

1. In the sidebar click **Records**, or go to `/healthcare/records/`
2. Click **+ Create Record**
3. Fill in the form:

| Field | Example Value | Notes |
|---|---|---|
| Patient | `Ali Yılmaz` | Select from dropdown — must exist |
| Hospital | `Ankara University Hospital` | Select from dropdown — must exist |
| Record Type | `Diagnosis` | See types below |
| Title | `Type 2 Diabetes Initial Assessment` | Required |
| Description | `Patient presents with...` | Clinical notes, free text |
| IPFS Hash | *(leave blank)* | Optional — reference to off-chain storage |
| Signature | *(leave blank)* | Optional cryptographic signature |

4. Click **Create Record**

### Record Types

| Type | When to use |
|---|---|
| **Diagnosis** | Initial or follow-up diagnosis notes |
| **Laboratory Result** | Blood tests, urinalysis, biopsies |
| **Prescription** | Medication orders |
| **Medical Imaging** | X-ray, MRI, CT scan results |
| **Surgery Report** | Pre/post operative notes |
| **Discharge Summary** | End-of-stay summary |
| **Insurance Claim** | Insurance billing records |

### What happens automatically

When you save a record, the system automatically:
- Generates a unique `record_id` (SHA-256 hash)
- Computes a `data_hash` of the record content for integrity verification
- Creates a blockchain **Transaction** of type `CREATE` and links it to the record
- Writes an **Audit Log** entry with action `CREATE`

### After creation

The record detail page (`/healthcare/records/<id>/`) shows:
- Clinical Notes (description)
- Cryptographic integrity section (data hash, metadata hash, IPFS hash, blockchain TX)
- Patient info panel
- Linked access permissions
- Full audit trail

---

## 10. Grant Access to a Record

By default only the creating hospital can see a record. Use permissions to share access
with other hospitals, labs, insurance providers, or doctors.

### Steps

1. Open any record's detail page and click **Grant Access** (or go to `/healthcare/permissions/add/`)
2. Fill in the form:

| Field | Example Value | Notes |
|---|---|---|
| Record | *(select the record)* | Choose from dropdown |
| Patient (Grantor) | *(select the patient)* | The patient authorising the access |
| Grantee Name | `Central Pathology Lab` | Name of who receives access |
| Grantee Type | `Laboratory` | Hospital / Lab / Insurance / Doctor |
| Permission Type | `READ` | READ / WRITE / SHARE |
| Purpose | `Lab result analysis` | Required — explains why access is needed |
| Valid Until | `2025-12-31` | Optional expiry date |

3. Click **Grant Permission**
4. You are redirected back to the record's detail page

> **Revoking access:** Go to **Permissions** in the sidebar. Find the permission row and click
> the red **X** button in the Actions column. The permission status changes to "Revoked".
> Revoked permissions remain in the audit trail but are no longer considered active.

---

## 11. Create a Blockchain Transaction

Transactions are normally created automatically when you create a medical record.
You can also create them manually to simulate custom on-chain events.

### Steps

1. Go to **Blockchain → Transactions** or click the **Transactions** link in the sidebar
2. Click **+ New Transaction**
3. Fill in the form:

| Field | Example Value | Notes |
|---|---|---|
| Transaction Type | `CREATE` | CREATE / UPDATE / SHARE / VERIFY / ACCESS |
| Sender | `Ankara University Hospital` | Who is sending — any identifier string |
| Receiver | `Central Pathology Lab` | Optional |
| Data Hash | `a3f5...` | SHA-256 hash of the data being transacted |
| Signature | *(any text)* | Simulated digital signature |

4. Click **Submit Transaction**

> The transaction starts with status **PENDING**. It moves to **BATCHED** when included
> in a rollup batch (Step 12), and to **CONFIRMED** if included in a block.

---

## 12. Create a Rollup Batch (Layer-2)

Rollup batches aggregate multiple PENDING transactions into one proof — the core of the
Layer-2 simulation.

### Steps

1. Go to **Blockchain → Rollup Batches** or `/blockchain/rollups/`
2. Click **+ Create Batch**
3. Choose the **Target Network** from the list (only active networks appear)
4. The form shows how many pending transactions are queued
5. Click **Generate Batch & ZK Proof**

### What happens

- All PENDING transactions (up to 50) are grouped into the batch
- A **Merkle tree** is computed over all transaction hashes
- A **ZK-SNARK proof** is generated (simulated JSON structure)
- All included transactions move from `PENDING` → `BATCHED`
- The batch is saved with status `BATCHED`

> View the batch detail page to see the full Merkle root, ZK proof payload, and every
> transaction included in the batch.

---

## 13. Send a Cross-Chain Message

Cross-chain messaging simulates relaying a verified message from one blockchain network
to another — for example, sharing a record hash across two separate chains.

### Steps

1. Go to **Cross-Chain** in the top navbar or `/cross-chain/`
2. Click **+ New Transfer**
3. Fill in the form:

| Field | Example Value | Notes |
|---|---|---|
| Source Network | `MediChain Mainnet` | Where the message originates |
| Target Network | `MediChain Testnet` | Where it is being sent |
| Data Hash | `a3f5...` | The data being relayed (e.g. a record hash) |
| Signature | *(any text)* | Simulated signature |
| Nonce | *(leave blank or any value)* | Auto-generated if blank |

4. Click **Send Transfer**

> The message starts as `PENDING`. The relay service validates it using the ZK proof
> middleware before marking it `RELAYED` then `VERIFIED`.
> Click a message row in the dashboard to open its **Detail** page showing status history.

---

## 14. Use ZK Proofs

The ZK Proofs section simulates zero-knowledge proof generation and verification.
These are SHA-256-based simulations — not real cryptographic ZK proofs.

### Generate a Proof

1. Go to **ZK Proofs** in the navbar or `/zk-proofs/`
2. Click **Generate Proof** (or go to `/zk-proofs/generate/`)
3. Enter:
   - **Secret inputs** — comma-separated values (e.g. `record_id,patient_id`)
   - **Public statement** — the data_hash of a record
4. Click **Generate** — the page returns a proof JSON object

### Verify a Proof

1. Go to `/zk-proofs/verify/`
2. Paste the proof JSON generated above
3. Enter the same public statement (data_hash)
4. Click **Verify** — the page returns `valid: true` or `valid: false`

### Range Proof

1. Go to `/zk-proofs/range/`
2. Enter a secret value (e.g. a patient's age) and a range (min / max)
3. The proof confirms the value is within the range without revealing the actual value

---

## 15. View Reports

Reports give you printable summaries of every entity and the whole platform.

### How to access

- **Reports Hub** — sidebar → **Reports**, or `/healthcare/reports/`
- From there, click any report card or use the quick links

### Available reports

| Report | URL | What it shows |
|---|---|---|
| System Overview | `/healthcare/reports/overview/` | Platform-wide counts, record breakdown, recent activity |
| Audit & Compliance | `/healthcare/reports/audit/` | All audit events with filters by date and actor type |
| Patient Report | Patient detail → **Report** button | All records, permissions, audit trail for one patient |
| Hospital Report | Hospital detail → **Report** button | All records and labs for one hospital |
| Laboratory Report | Lab detail → **Report** button | Lab results and linked permissions |
| Insurance Report | Insurance detail → **Report** button | Permissions and insurance claims |
| Record Report | Record detail → **Report** button | Single record with full integrity data and audit trail |

### Print any report

Every report page has a **Print** button. Clicking it opens a standalone browser window
with a clean print-optimised document. Your browser's print dialog opens automatically.

> Filters on the Audit & Compliance report: use the **Date From / Date To** inputs to
> narrow the date range, and the **Actor Type** dropdown to filter by DOCTOR, HOSPITAL,
> LAB, PATIENT, or ADMIN.

---

## 16. Read the Audit Log

Every CREATE, READ, UPDATE, SHARE, and DELETE action on a medical record is automatically
logged. The audit log cannot be edited or deleted — even admins cannot modify it.

### Steps

1. Sidebar → **Audit Log**, or go to `/healthcare/audit/`
2. Use the filter dropdowns:
   - **Action** — CREATE / READ / UPDATE / SHARE / DELETE / ACCESS_DENIED
   - **Actor Type** — DOCTOR / HOSPITAL / LAB / PATIENT / ADMIN
3. Use pagination to browse older entries

### Reading a log entry

Each row shows:
- **Action** — what was done (colour-coded badge)
- **Actor** — who did it (hospital ID, username, or patient ID)
- **Actor Type** — their role
- **Record** — which record was affected (click to open it)
- **Details** — extra JSON metadata (e.g. record type, title)
- **IP Address** — originating request IP
- **Timestamp** — exact date and time

> The audit trail is also visible on each individual **Record Detail** page at the bottom
> of the page, filtered to that record only.

---

## 17. Edit and Delete Records

### Edit a Patient
1. Open the patient's detail page
2. Click **Edit** (top right)
3. Update: Date of Birth, Blood Type, Allergies, Emergency Contact, Active status
4. Click **Save Changes**

### Delete a Patient
1. From the patient's Edit page, click **Delete** (top right, red button)
2. A confirmation screen asks you to confirm
3. Click **Yes, Delete** — all associated records and permissions are also deleted

### Edit a Medical Record
1. Open the record's detail page
2. Click **Edit**
3. Update: Title, Record Type, Description, IPFS Hash
4. Click **Save Changes** — an `UPDATE` audit log entry is written automatically

### Archive a Medical Record
Archiving hides a record from active lists but keeps it in the audit trail.
1. Open the record's detail page
2. Click **Archive**
3. Confirm — the record's status changes to "Archived" and disappears from filtered active lists

### Edit a Hospital
1. Hospital detail → **Edit**
2. Update: Name, License Number, Network, Address, Verified status

### Edit / Delete a Laboratory
1. Lab detail → **Edit** (in the Quick Actions sidebar)
2. Update: Name, Accreditation, Affiliated Hospital
3. To delete, click **Delete** in the edit form header

### Edit / Delete an Insurance Provider
1. Insurance detail → **Edit**
2. Update: Name, License Number
3. To delete, click **Delete** in the edit form header

---

## 18. Using the Admin Panel

The Django Admin Panel at **http://127.0.0.1:8000/admin/** gives you direct database access.
Use it for tasks the main UI doesn't support.

### What you can do in Admin

| Section | What to manage |
|---|---|
| **Blockchain Networks** | Create / edit networks (required before using the app) |
| **Blocks** | View auto-created blocks, hash is read-only |
| **Transactions** | View all transactions, filter by type and status |
| **Rollup Batches** | View batch Merkle roots, ZK proofs, and included transactions |
| **Cross-Chain Messages** | View relay status, source/target chain details |
| **Validator Nodes** | Add simulated consensus validators |
| **Smart Contracts** | Register simulated contract addresses |
| **Patients** | View all patients, link a patient to a User account |
| **Hospitals** | View / edit hospitals, toggle verified status |
| **Medical Records** | Read-only view of hashes and integrity data |
| **Access Permissions** | Full view of who has access to what |
| **Audit Logs** | Read-only — cannot be added or changed, even by admin |
| **Users** | Manage user accounts, reset passwords, set staff/superuser flags |

### Linking a Patient to a User account

By default, patients created through the web form are not linked to a login account.
To link them:

1. Admin Panel → **Authentication → Users** → create a new user (or use existing)
2. Admin Panel → **Healthcare → Patients** → open the patient record
3. In the **User** field, select the login account
4. Click **Save**

Once linked, the patient's full name and email appear throughout the app.

---

## 19. Full Workflow Example (End to End)

This walkthrough creates one complete patient journey from setup to report.

### Step 1 — Infrastructure setup (Admin Panel)
1. Go to `/admin/` → **Blockchain Networks** → Add:
   - **MediChain Mainnet** (Chain ID: 1001, Consensus: PBFT)
   - **MediChain Testnet** (Chain ID: 1002, Consensus: PBFT)

### Step 2 — Register a hospital
1. `/healthcare/hospitals/add/`
2. Name: `City General Hospital`, License: `CGH-001`, Network: `MediChain Mainnet`
3. After saving, go to Edit → check **Verified hospital** → Save

### Step 3 — Register a laboratory
1. `/healthcare/labs/add/`
2. Name: `City General Pathology`, Accreditation: `ISO 15189`, Hospital: `City General Hospital`

### Step 4 — Register an insurance provider
1. `/healthcare/insurance/add/`
2. Name: `BlueCross Health`, License: `INS-001`

### Step 5 — Register a patient
1. `/healthcare/patients/add/`
2. Public Key: `patientpublickey123`, DOB: `1990-06-15`, Blood Type: `O+`
3. After saving, note the patient ID

### Step 6 — Create a medical record
1. `/healthcare/records/add/`
2. Patient: *(select the one you just created)*
3. Hospital: `City General Hospital`
4. Type: `Diagnosis`, Title: `Annual Health Check`, Description: `All vitals normal.`
5. Click **Create Record**
6. Note: a blockchain transaction was automatically created with status `PENDING`

### Step 7 — Grant lab access to the record
1. On the record detail page, click **Grant Access**
2. Record: *(auto-selected)*, Grantor: *(the patient)*, Grantee: `City General Pathology`
3. Grantee Type: `Laboratory`, Permission: `READ`, Purpose: `Lab analysis`
4. Click **Grant Permission** — you return to the record detail page

### Step 8 — Create a rollup batch
1. `/blockchain/rollups/create/`
2. Select `MediChain Mainnet`
3. Click **Generate Batch & ZK Proof**
4. Your `PENDING` transaction moves to `BATCHED`

### Step 9 — Send a cross-chain message
1. `/cross-chain/transfer/`
2. Source: `MediChain Mainnet`, Target: `MediChain Testnet`
3. Data Hash: *(paste the record's data_hash from the record detail page)*
4. Click **Send Transfer**

### Step 10 — Generate a ZK proof
1. `/zk-proofs/generate/`
2. Secret inputs: *(the record_id)*, Public statement: *(the data_hash)*
3. Click **Generate** — copy the proof output

### Step 11 — View the patient report
1. Patient detail page → **Report** button
2. The report shows all records, permissions, audit entries, and record-type breakdown
3. Click **Print** to open the print-ready document

### Step 12 — Check the audit trail
1. Sidebar → **Audit Log**
2. You will see CREATE and SHARE entries for the record you just created
3. Filter by **Action: SHARE** to see only the permission grant events

---

## Quick Reference

### URL map

| Page | URL |
|---|---|
| Landing | `/` |
| Main Dashboard | `/dashboard/` |
| Healthcare Dashboard | `/healthcare/` |
| Patients | `/healthcare/patients/` |
| Hospitals | `/healthcare/hospitals/` |
| Records | `/healthcare/records/` |
| Laboratories | `/healthcare/labs/` |
| Insurance | `/healthcare/insurance/` |
| Permissions | `/healthcare/permissions/` |
| Audit Log | `/healthcare/audit/` |
| Reports Hub | `/healthcare/reports/` |
| Blockchain Dashboard | `/blockchain/` |
| Blocks | `/blockchain/blocks/` |
| Transactions | `/blockchain/transactions/` |
| Rollup Batches | `/blockchain/rollups/` |
| Cross-Chain | `/cross-chain/` |
| ZK Proofs | `/zk-proofs/` |
| Admin Panel | `/admin/` |
| Profile / Settings | `/accounts/profile/` |

### Record type colour codes

| Type | Colour |
|---|---|
| Diagnosis | Blue (`#38bdf8`) |
| Laboratory Result | Purple (`#a78bfa`) |
| Prescription | Green (`#22c55e`) |
| Medical Imaging | Orange (`#fb923c`) |
| Surgery Report | Red (`#f87171`) |
| Discharge Summary | Yellow (`#facc15`) |
| Insurance Claim | Violet (`#c084fc`) |

### Transaction status flow

```
PENDING  →  (added to rollup)  →  BATCHED  →  (confirmed on chain)  →  CONFIRMED
```

### Permission lifecycle

```
Active  →  (click Revoke)  →  Revoked
```

Revoked permissions are kept for audit purposes but no longer grant access.

---

*MediChain Framework v1.0 — Department of Artificial Intelligence Technologies, Ankara University*
