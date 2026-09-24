# MEDICHAIN: SCALABLE CROSS-CHAIN LAYER-2 HEALTHCARE DATA PLATFORM
#### Video Demo: <https://youtu.be/pHI5sFFvB3o> or https://www.youtube.com/watch?v=pHI5sFFvB3o

#### Githun: https://github.com/fentyjames/
#### Edx.org: fentyjconteh@yahoo.com
#### City: Ankara, Turkey
#### Recorded on: September 24, 2026 

#### Hello, CS50!
Hello, world! My name is Fenty James Conteh, I am a Sierra Leonean, and recording this video from Ankara, Turkey. My GitHub username is fentyjames. This is MediChain: a scalable, cross-chain Layer-2 blockchain framework for privacy-preserving healthcare data exchange, developed for my CS50x final project.

#### Description:

MediChain is a decentralized, full-stack healthcare framework built with Django, PostgreSQL, and modern cryptographic primitives. Modern electronic health record (EHR) systems face severe trilemma trade-offs: central hospital databases remain vulnerable to single points of failure and unauthorized alteration, public blockchains reveal private patient diagnostics through open ledgers, and fragmented institutional silos prevent seamless interoperability across different healthcare providers. MediChain addresses this critical healthcare and distributed systems challenge by decoupling heavy clinical records from lightweight on-chain cryptographic proofs, simulating Layer-2 batch rollups, implementing Zero-Knowledge (ZK) validation, and offering cross-chain interoperability[cite: 1, 2].

The platform manages the end-to-end lifecycle of patient registrations, hospital accreditations, laboratory diagnostics, and insurance billing claims while ensuring every access event and mutation is immutably audited[cite: 1, 2]. Whenever clinical data is created or updated, the system computes SHA-256 integrity digests, packages state transitions into off-chain Layer-2 transaction pools, generates simulated ZK-SNARK/STARK proofs, aggregates records into Merkle trees, and commits batched rollups to an immutable ledger[cite: 1, 2]. The frontend provides real-time Chart.js interactive dashboards, one-click CSV export utilities, Swagger/ReDoc OpenAPI explorers, and automated clinical print summaries[cite: 1, 2].


#### The Problem & Architecture Overview

> "Traditional electronic health records face a fundamental trilemma: centralized systems suffer from single points of failure, public blockchains risk exposing sensitive patient diagnoses, and hospital silos block interoperability.
>
> MediChain solves this using Django, PostgreSQL, and cryptographic primitives. Heavy clinical records remain off-chain, while lightweight cryptographic proofs, Zero-Knowledge verification, and rollup batches anchor integrity to a simulated distributed ledger."

#### Core Healthcare Workflow & Immutability

> "Let's see it in action. In the Healthcare module, authorized hospital staff can create clinical entries, ranging from diagnostic reports to lab results.
>
> When I submit this record, two things happen automatically in the background: first, the backend computes a SHA-256 data hash to guarantee data integrity. Second, an uneditable Audit Log event is appended, and a pending blockchain transaction is triggered. The platform also features granular access control, allowing patients to grant or revoke time-bound permissions for labs or insurance providers."

#### Layer-2 Rollups & Zero-Knowledge Proofs

> "To prevent on-chain congestion, MediChain implements a Layer-2 rollup mechanism. By selecting our target network and initiating a batch, pending transactions are aggregated into a Merkle tree root and validated with a simulated ZK-SNARK proof, transitioning transactions from 'Pending' to 'Batched'.
>
> Over in the ZK-Proofs hub, we can verify patient attributes without exposing raw data. For example, using range proofs, a hospital or insurer can mathematically verify that a patient’s vital signs or age meet a clinical threshold—without disclosing the exact numerical value."

#### Cross-Chain Relay & Interactive APIs

> "MediChain also provides cross-chain message relaying, allowing state integrity proofs to pass securely between different simulated blockchain networks with nonce-based replay protection.
>
> For third-party integration, the entire framework exposes a fully documented RESTful API documented via Swagger and ReDoc, accompanied by instant CSV data exports and printable clinical summary reports across all modules."


### File Structure and System Architecture

The project architecture isolates specific business domains into modular Django apps and centralized config directories[cite: 1]:

- `manage.py`: The root command-line executable used for administrative commands, test suite execution, database schema migrations, and launching local development servers[cite: 1].
- `requirements.txt`: Defines all core Python dependencies, including Django, Django REST Framework (DRF), `drf-spectacular` for OpenAPI documentation, Celery, Redis, and testing libraries[cite: 1].
- `Dockerfile` & `docker-compose.yml`: Encapsulate multi-container containerization for the entire stack, spinning up Django/Gunicorn, PostgreSQL 16 on port 5433, and Redis 7 with persistent volume binding[cite: 1].
- `medichain_project/`: The primary project configuration package[cite: 1].
  - `settings.py`: Contains application configuration, installed apps, database connection profiles for PostgreSQL, authentication handlers, session security flags, and static asset definitions[cite: 1].
  - `urls.py`: The root URL routing dispatch file mapping endpoints across administrative, authentication, healthcare, blockchain, ZK proof, and REST API modules[cite: 1].
  - `wsgi.py`: WSGI entry-point configuration used for production Gunicorn/Nginx server deployments[cite: 1].
  - `db_router.py`: Contains the `BlockchainRouter` class for multi-database routing scenarios[cite: 1].
- `healthcare/`: The core patient, institutional, and clinical records management application[cite: 1].
  - `models.py`: Defines database entities including `Patient`, `Hospital`, `Laboratory`, `InsuranceProvider`, `MedicalRecord`, `AccessPermission`, and `AuditLog`[cite: 1, 2].
  - `views.py`: Implements CRUD workflows, role-based permission validation, automatic cryptographic hash computations, CSV data exporter streams, and printable diagnostic reporting controllers[cite: 1, 2].
  - `urls.py`: Exposes endpoint routes for hospital listings, record details, permission authorizations, audit trail inspections, and CSV export URLs[cite: 1].
- `blockchain/`: Manages the simulated distributed ledger and Layer-2 consensus components[cite: 1, 2].
  - `models.py`: Defines the data architecture for `BlockchainNetwork`, `Block`, `Transaction`, `RollupBatch`, `ValidatorNode`, and `SmartContract`[cite: 1, 2].
  - `views.py`: Manages the submission of transaction envelopes, state updates (PENDING to BATCHED to CONFIRMED), block explorer visualizations, and rollup execution forms[cite: 1, 2].
  - `services.py`: Implements Merkle tree computations, hashing algorithms, and batch aggregations for off-chain transactions[cite: 2].
- `zk_proofs/`: Implements privacy-preserving verification without exposing sensitive clinical attributes[cite: 1, 2].
  - `models.py`: Defines `ZKProofRecord` to log proof types (zk-SNARK, zk-STARK, Range Proof), Merkle roots, verifier inputs, verification status, and timestamps[cite: 1, 2].
  - `views.py` & `services.py`: Provide mathematical zero-knowledge proof generation and range validation routines (e.g., verifying blood pressure or age compliance without disclosing exact medical figures)[cite: 1, 2].
- `cross_chain/`: Simulates decentralized relay bridges between heterogeneous blockchain networks[cite: 1, 2].
  - `models.py` & `views.py`: Handle `CrossChainMessage` dispatching, replay protection nonces, multi-network handshakes, and relay status transitions[cite: 1, 2].
- `api/`: Centralizes the headless REST interface[cite: 1].
  - `views.py` & `serializers.py`: Provide JSON token authentication, programmatic transaction dispatching, batch submission, and schema ingestion endpoints consumed by external integrations and interactive Swagger/ReDoc interfaces[cite: 1].
- `accounts/`: Oversees authentication mechanics, user profile preferences, and the primary dashboard metrics index[cite: 1].
- `templates/`: Houses responsive Jinja/Django HTML UI components[cite: 1].
  - `base.html`: Common skeleton containing navigation sidebars, user state indicators, and script imports[cite: 1, 2].
  - `index.html`: The main analytics dashboard rendering three live Chart.js figures: 7-day transaction velocity, medical record distribution doughnuts, and rolling 30-day compliance audit action distributions[cite: 1, 2].
  - `healthcare/`, `blockchain/`, `zk_proofs/`, `cross_chain/`: Sub-folders with dedicated CRUD forms, data tables, detail views, and print-ready summary templates[cite: 1, 2].
- `tests/test_medichain.py`: Automated test suite containing unit and integration test cases covering ZK service logic, API endpoints, model lifecycle validations, and permission enforcement[cite: 1].

### Design Decisions and Engineering Trade-Offs

1. **Single PostgreSQL Database vs. Dual-Database Routers:**  
   The initial architectural plan considered routing core healthcare records to a relational database while isolating blocks and rollups into a secondary `blockchain` database[cite: 1]. However, splitting transactional boundaries across separate database connections complicates foreign key integrity and requires complex distributed transaction coordinators. To maintain referential integrity between `MedicalRecord` instances, ledger transactions, and audit entries while keeping the setup lightweight for CS50 evaluation, both domains were co-located inside a single default PostgreSQL database[cite: 1]. The `db_router.py` logic was preserved in an inactive state to document how multi-database routing could be activated for larger enterprise deployments[cite: 1].

2. **Simulated Zero-Knowledge Verification vs. Production Proving Key Compilation:**  
   Compiling production-grade Groth16 or PLONK zero-knowledge proving keys typically requires external C++ or Rust toolchains (such as Circom/SnarkJS) and extensive setup ceremonies. MediChain simulates the algebraic and hashing verification routines (verifying input leaves, Merkle paths, and range parameters) directly inside Python services[cite: 1, 2]. This design keeps the application portable, dependency-free, and cross-platform across standard virtual environments without sacrificing educational clarity[cite: 1].

3. **Tamper-Evident Immutable Audit Logging:**  
   To comply with clinical standards like HIPAA and GDPR, audit log records in MediChain are structurally append-only[cite: 2]. The Django Admin interface and application views disallow updating or deleting entries in `AuditLog`[cite: 2]. Every file read, patient query, permission revocation, and medical record alteration generates an uneditable entry recording the actor ID, originating IP address, timestamp, and metadata hash[cite: 1, 2].

4. **Django Variable Shadowing Workaround:**  
   During template design, Django's native `{% block %}` template inheritance tag collided with context variables referencing blockchain block instances named `block`[cite: 1]. To prevent the template engine from silently dropping block instance attributes, blockchain models are explicitly aliased in context dictionaries (e.g., `blk`) across detail views[cite: 1].


### Conclusion
By combining robust Django backends with Zero-Knowledge verification and Layer-2 scaling, MediChain demonstrates how modern healthcare systems can achieve privacy, scalability, and audit compliance at once.   Thank you for watching, and this was CS50!

### Getting Started

Clone the repository and set up a Python virtual environment[cite: 1]:

```bash
git clone [https://github.com/fentyjames/medichain_project.git](https://github.com/fentyjames/medichain_project.git)
cd medichain_project
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
