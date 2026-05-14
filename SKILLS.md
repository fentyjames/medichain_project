# MediChain — Developer Skills Reference

> Every technology, pattern, and concept applied in building the MediChain
> Scalable Cross-Chain Layer-2 Blockchain Framework for Healthcare Data Exchange.

**Author:** Fenty James Conteh  
**Institution:** Ankara University — Department of Artificial Intelligence Technologies

---

## Table of Contents

1. [Python Language](#1-python-language)
2. [Django Web Framework](#2-django-web-framework)
3. [Django REST Framework (DRF)](#3-django-rest-framework-drf)
4. [API Documentation — drf-spectacular](#4-api-documentation--drf-spectacular)
5. [PostgreSQL & Database Design](#5-postgresql--database-design)
6. [Cryptography & Hashing](#6-cryptography--hashing)
7. [Blockchain Concepts](#7-blockchain-concepts)
8. [Zero-Knowledge Proof (ZK) Simulation](#8-zero-knowledge-proof-zk-simulation)
9. [Layer-2 Rollup Architecture](#9-layer-2-rollup-architecture)
10. [Cross-Chain Relay System](#10-cross-chain-relay-system)
11. [Frontend — Django Templates](#11-frontend--django-templates)
12. [Frontend — CSS & Bootstrap 5](#12-frontend--css--bootstrap-5)
13. [Frontend — JavaScript & Chart.js](#13-frontend--javascript--chartjs)
14. [Security Engineering](#14-security-engineering)
15. [Authentication & Access Control](#15-authentication--access-control)
16. [Asynchronous Tasks — Celery & Redis](#16-asynchronous-tasks--celery--redis)
17. [Data Export & File Handling](#17-data-export--file-handling)
18. [Containerisation — Docker & Docker Compose](#18-containerisation--docker--docker-compose)
19. [Testing](#19-testing)
20. [DevOps & Version Control](#20-devops--version-control)
21. [Browser Automation — Playwright](#21-browser-automation--playwright)
22. [Software Architecture Patterns](#22-software-architecture-patterns)

---

## 1. Python Language

| Skill | Used For |
|-------|----------|
| **Python 3.12** | Primary language for the entire backend |
| **Type hints** (`list[str]`, `dict`, `Any`) | Service method signatures in `zk_service.py` |
| **f-strings & string formatting** | Hash generation, log messages, template rendering |
| `hashlib` (SHA-256) | Auto-generating `patient_id`, `record_id`, `hospital_id`, block and transaction hashes |
| `uuid` | Seeding unique IDs before hashing |
| `json` module | Serialising proof payloads, block data, and API responses |
| `csv` module | Streaming CSV file downloads |
| `datetime` / `timedelta` | Date arithmetic for dashboard chart queries and permission expiry |
| `pathlib.Path` | `BASE_DIR` construction in `settings.py` |
| `time` module | Timestamping proofs, measuring cross-chain request duration |
| `logging` | Debug and error logging in service classes |
| `os` module | Environment variable access and path construction |
| List comprehensions | Merkle tree construction, data transformation |
| Context managers | Database query grouping, file I/O in scripts |
| Exception handling (`try/except`) | Graceful view error handling and screenshot scripting |

---

## 2. Django Web Framework

### Core Framework

| Skill | Used For |
|-------|----------|
| **Django 4.2** | Full-stack web framework — routing, ORM, templates, admin |
| `manage.py` commands | `migrate`, `createsuperuser`, `collectstatic`, `runserver`, `test` |
| `settings.py` | `INSTALLED_APPS`, `MIDDLEWARE`, `DATABASES`, `TEMPLATES`, `MEDICHAIN_CONFIG` |
| Custom config dict (`MEDICHAIN_CONFIG`) | App-level tunables: batch size, ZK type, relay interval |
| `django.conf.settings` | Accessing config throughout app code |
| `python-decouple` | Reading `SECRET_KEY`, DB credentials, `DEBUG` from `.env` |

### URL Routing

| Skill | Used For |
|-------|----------|
| `urlpatterns` in `urls.py` | Mapping paths to views |
| `path()` and `include()` | Modular URL configs per Django app |
| Named URLs (`name=`) | `{% url %}` template tag and `reverse()` |
| URL parameter capture (`<str:tx_hash>`) | Detail views for blocks, transactions, patients |
| **Static-before-parameterized ordering** | Export endpoints declared before `<str:id>/` to prevent capture conflicts |
| URL namespacing | Avoiding name collisions across multiple `urls.py` files |

### Models & ORM

| Skill | Used For |
|-------|----------|
| `models.Model` subclassing | `Patient`, `Hospital`, `MedicalRecord`, `Block`, `Transaction`, etc. |
| `CharField`, `TextField`, `IntegerField`, `BigIntegerField`, `BooleanField` | Standard field types |
| `DateTimeField(auto_now_add=True)` | `created_at` audit fields |
| `DateField`, `URLField` | Patient DOB, network RPC URL |
| `JSONField` | ZK proof payloads, audit log metadata, rollup batch data |
| `ForeignKey` (with `on_delete=CASCADE`) | Record → Hospital, Block → Network, etc. |
| `OneToOneField` | `Patient.user` → `AUTH_USER_MODEL` |
| `class Meta` (`db_table`, `ordering`) | Custom table names and default queryset ordering |
| `save()` override | Auto-computing SHA-256 `patient_id`, `record_id`, `tx_hash`, `hash` on first save |
| `MinLengthValidator` | Preventing empty string IDs on `Hospital` |
| `select_related()` | Efficient FK joins (e.g. `Transaction.select_related('block')`) |
| `filter()`, `exclude()`, `order_by()` | Standard queryset operations |
| `annotate()` + `Count()` | Aggregating counts for dashboard stats and chart data |
| `TruncDate()` | Bucketing transactions by calendar day for bar charts |
| `values()` | Lightweight dict querysets for chart data |
| Django migrations | Schema versioning with `makemigrations` and `migrate` |
| Custom `AUTH_USER_MODEL` | `accounts.User` replaces `django.contrib.auth.models.User` |
| String FK references (`'blockchain.BlockchainNetwork'`) | Avoiding circular import on cross-app ForeignKeys |
| `django.apps.apps.get_model()` | Lazy model loading to prevent import cycles |

### Views

| Skill | Used For |
|-------|----------|
| Function-based views (FBVs) | All template views (list, detail, add, edit, delete) |
| `render()` | Returning template responses with context |
| `get_object_or_404()` | Clean 404 handling on detail pages |
| `redirect()` | Post-form-submit redirects |
| `HttpResponse` | CSV downloads, plain responses |
| `JsonResponse` | API-style JSON responses |
| `@login_required` decorator | Protecting all views behind authentication |
| `request.method` branching | GET/POST form handling in the same view function |
| `request.POST` / `request.GET` | Form data and query parameter reading |
| Pagination (`Paginator`, `page_obj`) | All list views with `{% include 'partials/pagination.html' %}` |
| Context dictionary | Passing all template variables from view to template |

### Templates

| Skill | Used For |
|-------|----------|
| Template inheritance (`{% extends %}`, `{% block %}`) | All pages extend `base.html` |
| `{% include %}` | `partials/pagination.html` reused across all list views |
| `{% url %}` tag | Generating URLs by name without hardcoding paths |
| `{% for %}` / `{% empty %}` | Iterating querysets with graceful empty state |
| `{% if %}` / `{% elif %}` / `{% else %}` | Conditional rendering (badges, buttons) |
| Template filters (`|date`, `|truncatechars`, `|slice`, `|pluralize`, `|default`) | Data formatting |
| `{{ variable|safe }}` | Rendering pre-serialised JSON strings for Chart.js |
| `{% block extra_scripts %}` | Injecting page-specific `<script>` tags without nesting conflicts |
| **Variable naming discipline** | Avoiding `block` as a context key — it shadows Django's template tag context |

### Admin

| Skill | Used For |
|-------|----------|
| `admin.site.register()` | Registering all models in Django Admin |
| `ModelAdmin` with `list_display`, `search_fields`, `list_filter` | Admin UX for all models |
| Read-only admin for `AuditLog` | Preventing modification of the audit trail |

### Middleware

| Skill | Used For |
|-------|----------|
| `MiddlewareMixin` subclassing | `ZKProofMiddleware`, `CrossChainMiddleware` |
| `process_request()` | Annotating `request.zk_verified`, `request.cross_chain_timestamp` |
| `process_response()` | Injecting security headers and `X-Cross-Chain-Duration` |

### Signals

| Skill | Used For |
|-------|----------|
| `post_save` signal | Auto-creating `AuditLog` entries on `MedicalRecord` save |

### Static & Media Files

| Skill | Used For |
|-------|----------|
| `STATIC_URL`, `STATIC_ROOT`, `STATICFILES_DIRS` | Static file configuration |
| `collectstatic` | Gathering static files for production |
| WhiteNoise | Serving static files in production without Nginx |
| `MEDIA_URL`, `MEDIA_ROOT` | User-uploaded file storage |

---

## 3. Django REST Framework (DRF)

| Skill | Used For |
|-------|----------|
| **DRF 3.17** | Building the REST API layer |
| `ModelSerializer` | Serialisers for `Patient`, `Hospital`, `MedicalRecord`, `Block`, `Transaction` |
| `HyperlinkedModelSerializer` | Detail URL fields in API responses |
| `ModelViewSet` | Full CRUD ViewSets for all models under `/api/blockchain/api/` and `/api/healthcare/api/` |
| `APIView` | Custom views in `api/views.py` (dashboard, login, rollup, ZK verify) |
| `@api_view` decorator | Simple function-based API endpoints |
| `TokenAuthentication` | Stateless token-based API auth |
| `SessionAuthentication` | Browser session support alongside tokens |
| `IsAuthenticated` permission | Default permission class on all endpoints |
| `PageNumberPagination` | Paginating API list responses (page size 50) |
| `Response` | DRF-aware response with content negotiation |
| `routers.DefaultRouter` | Auto-generating URL patterns for ViewSets |
| `status` module | HTTP status code constants (`HTTP_200_OK`, `HTTP_201_CREATED`, `HTTP_400_BAD_REQUEST`) |
| `@action` decorator | Custom actions on ViewSets (e.g. `grant_access`, `verify_integrity`) |
| DRF browsable API | Human-readable HTML interface for development |

---

## 4. API Documentation — drf-spectacular

| Skill | Used For |
|-------|----------|
| **drf-spectacular 0.29** | Auto-generating OpenAPI 3.0 schema from DRF code |
| `AutoSchema` | Set as `DEFAULT_SCHEMA_CLASS` in `REST_FRAMEWORK` settings |
| `SPECTACULAR_SETTINGS` | Title, description, version metadata |
| `SpectacularAPIView` | Serves the raw OpenAPI JSON at `/api/schema/` |
| `SpectacularSwaggerView` | Interactive Swagger UI at `/api/docs/` |
| `SpectacularRedocView` | Clean ReDoc reference at `/api/redoc/` |
| OpenAPI 3.0 | Industry-standard schema format importable into Postman/Insomnia |
| `SERVE_INCLUDE_SCHEMA: False` | Hiding the schema endpoint from its own docs |

---

## 5. PostgreSQL & Database Design

| Skill | Used For |
|-------|----------|
| **PostgreSQL 16** | Primary relational database |
| Schema design | Normalised tables across `blockchain`, `healthcare`, `zk_proofs` apps |
| Custom `db_table` names | `patients`, `blocks`, `transactions`, `zk_proof_records`, etc. |
| Foreign key relationships | Record → Hospital, Block → Network, Transaction → Block |
| OneToOne relationships | Patient → User, enforcing single patient per account |
| UUID-seeded SHA-256 primary IDs | Globally unique, content-addressable identifiers |
| `BigAutoField` (default) | Auto-incrementing PKs |
| Boolean flags (`is_active`, `is_verified`) | Soft-delete and status tracking |
| `JSONField` | Storing proof payloads and audit metadata without schema lock-in |
| Database router pattern | `BlockchainRouter` (dormant) — architecture for splitting DBs |
| Port mapping (5433 → 5432) | Avoiding conflict with local PostgreSQL installations |
| `pg_isready` health check | Docker Compose service dependency |
| `pg_dump` backups | Database backup command |
| Connection pooling (gunicorn workers) | Multiple Django workers share the DB connection pool |

---

## 6. Cryptography & Hashing

| Skill | Used For |
|-------|----------|
| **SHA-256** (`hashlib.sha256`) | Hashing patient/record/hospital IDs, block hashes, proof hashes |
| Content-addressable IDs | `sha256(uuid + timestamp)` for all entity primary IDs |
| **AES-256-GCM** | Symmetric encryption of medical files before IPFS upload (design) |
| `cryptography` library (48.0) | Production-grade cryptographic primitives |
| `pycryptodome` (3.23) | Additional cipher support |
| ECDSA digital signatures | Patient/hospital signing of records and permissions (simulated) |
| Hash chaining | `Block.previous_hash` links each block to its predecessor |
| Merkle root computation | `RollupBatch.calculate_merkle_root()` — pair-wise SHA-256 hashing |
| Deterministic hashing | `json.dumps(data, sort_keys=True)` before hashing to ensure consistency |
| TOTP / OTP | `pyotp` for two-factor authentication flows |
| Salt-less deterministic IDs | Reproducible IDs from UUID + timestamp without random salt |

---

## 7. Blockchain Concepts

| Skill | Used For |
|-------|----------|
| Block structure | `block_number`, `previous_hash`, `merkle_root`, `nonce`, `hash`, `timestamp` |
| Hash chaining | Each block's `previous_hash` references the prior block's `hash` |
| Transaction lifecycle | `PENDING → BATCHED → CONFIRMED` status flow |
| Transaction types | `CREATE`, `UPDATE`, `SHARE`, `VERIFY`, `ACCESS` operations |
| Consensus mechanisms | PBFT, PoS, PoW — modelled in `BlockchainNetwork.consensus_type` |
| Validator nodes | `ValidatorNode` model for consensus simulation |
| Smart contracts | `SmartContract` model for contract registry simulation |
| Gas tracking | `Transaction.gas_used` field |
| Web3.py (7.16) | Imported dependency for future real-chain integration |
| `eth-account` | Ethereum account / signing library (dependency) |
| IPFS integration | `ipfshttpclient` — off-chain content-addressed file storage |
| On-chain/off-chain split | Only `data_hash` + `ipfs_hash` stored on-chain; full data stays off-chain |
| Nonce | Replay-attack prevention field on `CrossChainMessage` |

---

## 8. Zero-Knowledge Proof (ZK) Simulation

| Skill | Used For |
|-------|----------|
| **ZK-SNARK** concept | Succinct Non-Interactive ARgument of Knowledge — small proof, fast verification |
| **ZK-STARK** concept | Scalable Transparent ARgument of Knowledge — quantum-resistant, no trusted setup |
| **Range proofs** | Proving a value lies within [min, max] without revealing the value |
| `ZKProofService` class | Proof generation and verification service in `zk_proofs/zk_service.py` |
| Proof structure | JSON with: `proof_type`, `timestamp`, `public_inputs`, `private_inputs_hash`, `proof`, `verification_key` |
| Private inputs | Transaction hashes — kept secret, only their hash is published |
| Public output | Merkle root — the public commitment anyone can verify |
| Verification logic | Re-hash inputs, compare structures and counts |
| Django cache | `cache.set()` / `cache.get()` for proof caching with 1-hour TTL |
| `ZKProofRecord` model | Persistent history of every proof generated or verified |
| ZK middleware | `ZKProofMiddleware` reads `X-ZK-Proof` header to set `request.zk_verified` |
| Production note | Real ZK proofs would use `snarkjs`, `libsnark`, or `ZoKrates` |

---

## 9. Layer-2 Rollup Architecture

| Skill | Used For |
|-------|----------|
| Rollup concept | Batching many L1 transactions into one compressed proof |
| `RollupBatch` model | Stores `merkle_root`, `zk_proof`, `transaction_count`, `status` |
| Merkle tree construction | Pair-wise SHA-256 until single root — `calculate_merkle_root()` |
| Batch size config | `MEDICHAIN_CONFIG['ROLLUP_BATCH_SIZE']` (default 50) |
| Gas cost reduction | ~75% fewer on-chain writes vs posting each transaction |
| `BATCHED` status | Transactions move from `PENDING` → `BATCHED` when included in a rollup |
| Rollup-to-block linkage | `Block.rollup_proof` stores the ZK proof for the batched set |
| `CreateRollupView` (`api/views.py`) | Orchestrates: fetch transactions → Merkle root → ZK proof → save batch |

---

## 10. Cross-Chain Relay System

| Skill | Used For |
|-------|----------|
| `CrossChainRelayService` | Service class in `cross_chain/relay_service.py` |
| `CrossChainMessage` model | `source_chain`, `target_chain`, `data_hash`, `proof`, `nonce`, `status` |
| Message status | `PENDING → RELAYED → VERIFIED` or `REJECTED` |
| ZK proof validation before relay | `relay_message()` calls `ZKProofService.verify_proof()` |
| Nonce replay protection | `_is_nonce_used()` / `_mark_nonce_used()` — stubs (TODO for production) |
| Request timing header | `X-Cross-Chain-Duration` injected by `CrossChainMiddleware` |
| Network-to-network mapping | Source and target are FK to `BlockchainNetwork` |

---

## 11. Frontend — Django Templates

| Skill | Used For |
|-------|----------|
| Template inheritance | Every page `{% extends 'base.html' %}` with defined `{% block %}` regions |
| `base.html` architecture | Sidebar nav, topbar, content area, script blocks |
| `{% block content %}` | Main page content area |
| `{% block extra_scripts %}` | Standalone `<script>` tags injected after `</script>` (avoids nesting) |
| `{% include 'partials/pagination.html' %}` | Reusable pagination component |
| `{% url 'name' arg %}` | Reverse URL resolution — no hardcoded paths in templates |
| Template context | Rich context dicts: `page_obj`, `q` (search), chart JSON, stats dicts |
| `{{ value|json_script:"id" }}` pattern | Safely passing Python objects to JavaScript |
| `{{ value|safe }}` | Rendering pre-serialised JSON without escaping |
| `{{ value|date:"d M Y" }}` | Human-readable date formatting |
| `{{ value|truncatechars:28 }}` | Truncating long strings in table cells |
| `{{ value|default:"-" }}` | Fallback for null/empty fields |
| `{% if patient.user %}` | Conditional display of linked-user data |
| 60+ HTML templates | login, register, 2FA, dashboard, patient/hospital/record CRUD, blockchain, ZK, reports, 404/500 |
| Error pages | Custom `404.html` and `500.html` |
| Print templates | Report pages with print-optimised CSS and auto-open `window.print()` |

---

## 12. Frontend — CSS & Bootstrap 5

| Skill | Used For |
|-------|----------|
| **Bootstrap 5.3** | Grid system, components, utilities — loaded via jsDelivr CDN |
| **Bootstrap Icons** | Icon set (`bi bi-people-fill`, `bi bi-download`, etc.) — CDN |
| **CSS custom properties** (`var(--accent)`, `var(--border)`, `var(--text-light)`) | Dark theme tokens defined once in `base.html` |
| Dark theme design | `background: #0a0f1e` base, `#1e293b` card surfaces, `#38bdf8` accent |
| Flexbox utilities | `d-flex`, `align-items-center`, `gap-2`, `justify-content-between` |
| Responsive grid | `col-md-3`, `col-xl-2` sidebar, `col-md-9` content |
| Badge components | Colour-coded status badges for record types, transaction status, audit actions |
| Card components | Content containers with `card`, `card-body`, `card-header` |
| Table components | `table-hover`, `table-responsive` for all data lists |
| Form components | `form-control`, `form-select`, `btn`, `btn-outline-*` |
| Navbar / sidebar | Off-canvas mobile sidebar with collapse behaviour |
| Inline styles | Targeted overrides for custom dark-theme colours where Bootstrap defaults conflict |
| `rgba()` transparency | Frosted-glass card backgrounds over dark base |
| `border-radius: 10px` | Consistent rounded corners on inputs and cards |
| Print CSS | `@media print` overrides on report pages |

---

## 13. Frontend — JavaScript & Chart.js

| Skill | Used For |
|-------|----------|
| **Vanilla JavaScript (ES6+)** | DOM manipulation, event handling, clipboard API |
| `navigator.clipboard.writeText()` | Copy-to-clipboard for hashes on list pages |
| `fetch()` API | AJAX requests from templates to REST endpoints |
| JSON parsing | `JSON.parse()` of inline context data for charts |
| **Chart.js 4.4** | Data visualisation — loaded via jsDelivr CDN |
| `new Chart(ctx, config)` | Initialising all three dashboard charts |
| Bar chart (`type: 'bar'`) | 7-day transaction volume chart |
| Doughnut chart (`type: 'doughnut'`) | Medical record type distribution chart |
| Horizontal bar chart (`indexAxis: 'y'`) | Audit activity chart |
| Chart datasets | `labels`, `data`, `backgroundColor`, `borderColor` arrays |
| Chart options | `responsive: true`, `plugins.legend`, `plugins.tooltip`, `scales` |
| `borderRadius` on bars | Rounded bar chart corners for visual polish |
| Chart colour palettes | Consistent `#38bdf8`, `#a78bfa`, `#22c55e`, `#fb923c` colour set |
| `getContext('2d')` | Canvas 2D context for chart rendering |
| `json.dumps()` in view → `{{ var\|safe }}` in template | Passing Python data to JS without extra XHR |
| `window.print()` | Auto-opening print dialog on report pages |
| `setTimeout(window.print, 500)` | Delayed print to let page render fully |
| DOM content loaded guard | `document.addEventListener('DOMContentLoaded', ...)` |

---

## 14. Security Engineering

| Skill | Used For |
|-------|----------|
| **CSRF protection** | Django's `CsrfViewMiddleware` — all forms include `{% csrf_token %}` |
| **XSS prevention** | Django's auto-escaping in templates; manual `|safe` only where JSON is pre-sanitised |
| **Content Security Policy** | Set in `ZKProofMiddleware.process_response()` — restricts script/style/image sources |
| `X-Frame-Options: DENY` | Clickjacking prevention |
| `X-Content-Type-Options: nosniff` | MIME sniffing prevention |
| `Referrer-Policy: strict-origin-when-cross-origin` | Limits referrer data leakage |
| `X-MediChain-Version` header | Custom response header for version identification |
| Token-based auth | Stateless API access — no session cookie dependency |
| Login guards | `@login_required(login_url='/accounts/login/')` on every view and CSV export |
| Password validators | Minimum length, no all-numeric, no common passwords (Django built-in) |
| Two-factor authentication | `pyotp` TOTP flows in `accounts/` app |
| Email verification | `resend_verification` view and email template |
| Admin registration code | `ADMIN_REGISTRATION_CODE` config prevents open admin account creation |
| CORS configuration | `django-cors-headers` with explicit `CORS_ALLOWED_ORIGINS` whitelist |
| `.gitignore` for `.env` | Credentials not committed to version control |
| `SECRET_KEY` from environment | Read via `python-decouple`, never hardcoded |
| SHA-256 for IDs (not secrets) | Entity IDs are hashes of UUIDs — not a security mechanism, but collision-resistant |
| `SECURE_SSL_REDIRECT`, `SECURE_BROWSER_XSS_FILTER` | Production security settings documented |

---

## 15. Authentication & Access Control

| Skill | Used For |
|-------|----------|
| Custom `User` model (`accounts.User`) | Extends `AbstractUser` — replaces default Django user |
| `OneToOneField` Patient → User | Linking a clinical record to a login account |
| `TokenAuthentication` (DRF) | API token issued at `/api/v1/auth/login/` |
| `SessionAuthentication` (DRF) | Browser-session support alongside token auth |
| `IsAuthenticated` default permission | All API endpoints require a valid user |
| `@login_required` | All template views require session login |
| `AccessPermission` model | Record-level ACL: `READ`, `WRITE`, `SHARE` by grantee type |
| Grantee types | `HOSPITAL`, `LAB`, `INSURANCE`, `DOCTOR` |
| Permission revocation | Status set to `REVOKED` (soft delete — kept in audit trail) |
| `AuditLog` model | Immutable append-only log of every action (CREATE, READ, UPDATE, SHARE, DELETE) |
| `purpose` field on permissions | HIPAA-required justification for every access grant |
| `valid_until` on permissions | Time-limited access grants |
| Django admin read-only for audit | `AuditLog` admin registered with no `add` or `change` permissions |

---

## 16. Asynchronous Tasks — Celery & Redis

| Skill | Used For |
|-------|----------|
| **Celery 5.6** | Distributed task queue for background processing |
| **Redis 7** | Message broker (`CELERY_BROKER_URL`) and result backend |
| `CELERY_BROKER_URL` | `redis://localhost:6379/0` |
| `CELERY_RESULT_BACKEND` | `redis://localhost:6379/0` |
| Django cache framework | `cache.set()` / `cache.get()` for ZK proof caching (1-hour TTL) |
| `celery -A medichain_project worker` | Starting the Celery worker process |
| Optional dependency | Application runs without Celery for synchronous use |

---

## 17. Data Export & File Handling

| Skill | Used For |
|-------|----------|
| Python `csv` module | Writing CSV rows to an HTTP response |
| `HttpResponse(content_type='text/csv')` | Streaming the CSV file to the browser |
| `Content-Disposition: attachment` header | Triggering browser download instead of inline display |
| `csv.writer` | Row-by-row CSV construction |
| Queryset slicing (`:10000`) | Capping exports to prevent memory exhaustion |
| `select_related()` on exports | Joining related models in a single query for efficiency |
| Export endpoints before parameterized paths | URL ordering discipline to prevent route capture |
| Login guard on all exports | `@login_required` — anonymous download attempts redirect to login |
| Four export types | Patients, Medical Records, Audit Log, Blockchain Transactions |
| `Pillow` (12.2) | Image processing for media file handling |

---

## 18. Containerisation — Docker & Docker Compose

| Skill | Used For |
|-------|----------|
| **Docker** | Container image for the Django application |
| `FROM python:3.12-slim` | Minimal base image |
| `ENV PYTHONDONTWRITEBYTECODE=1` | Preventing `.pyc` file generation |
| `ENV PYTHONUNBUFFERED=1` | Unbuffered stdout for container log streaming |
| `RUN apt-get install libpq-dev gcc` | Native build deps for `psycopg2` |
| `COPY requirements.txt` before `COPY .` | Docker layer caching — only reinstall deps when requirements change |
| `EXPOSE 8000` | Documenting the listening port |
| **Docker Compose** | Multi-service orchestration |
| `services:` — `db`, `redis`, `web` | Three-container stack |
| `postgres:16-alpine` | Lightweight PostgreSQL container |
| `redis:7-alpine` | Lightweight Redis container |
| `healthcheck` with `pg_isready` and `redis-cli ping` | Service startup ordering |
| `depends_on: condition: service_healthy` | Web starts only after DB and Redis are healthy |
| Named volumes (`postgres_data`, `static_volume`, `media_volume`) | Persistent data across restarts |
| Bind mount (`. → /app`) | Live code reload in development |
| `env_file: .env` | Injecting environment variables into the web container |
| `gunicorn ... --workers 3` | Production WSGI server inside container |
| `migrate && collectstatic && gunicorn` | Startup command chain in `docker-compose.yml` |
| Port mapping (`5433:5432`, `6379:6379`, `8000:8000`) | Exposing services to the host |

---

## 19. Testing

| Skill | Used For |
|-------|----------|
| **Django `TestCase`** | Database-backed unit tests with automatic rollback |
| **pytest 9.0** + **pytest-django 4.12** | Test discovery and execution |
| `coverage.py` | Measuring code coverage |
| `coverage html` | Generating browsable HTML coverage reports |
| Test class organisation | `ZKProofServiceTest`, `MerkleTreeTest`, `CrossChainRelayTest`, `BlockchainModelTest`, `HealthcareModelTest`, `APIIntegrationTest`, `PerformanceTest` |
| API integration tests | Sending requests to DRF endpoints, checking `response.status_code` |
| Model unit tests | Testing `save()` hook ID generation, hash computation |
| Service unit tests | Testing `ZKProofService.generate_proof()` and `verify_proof()` |
| Performance tests | Bulk insert benchmarks (deliberately slow — skip when iterating) |
| `--verbosity=2` | Verbose test output showing each test by name |
| Single-test targeting | `manage.py test tests.test_medichain.ClassName.method_name` |
| Test database isolation | Django creates a separate test DB, rolls back after each test |

---

## 20. DevOps & Version Control

| Skill | Used For |
|-------|----------|
| **Git** | Version control — commits, branches, push/pull |
| GitHub remote | `origin/main` — remote repository hosting |
| `.gitignore` | Excluding `venv/`, `__pycache__/`, `.env`, `*.pyc`, `staticfiles/`, `media/`, `screenshots/` |
| Commit message discipline | Feature-scoped messages with co-author attribution |
| `python-decouple` | Environment-based configuration without `.env` in version control |
| `requirements.txt` | Pinned dependency manifest for reproducible installs |
| Virtual environment (`venv`) | Isolated Python dependency environment |
| `pip install --upgrade pip` | Keeping pip current before installing deps |
| `collectstatic` | Pre-flight static file collection before deployment |
| Gunicorn (`--workers 3`, `--bind 0.0.0.0:8000`) | Production WSGI server configuration |
| WhiteNoise | Zero-config static file serving in production |
| `ALLOWED_HOSTS` | Deployment security — restrict accepted hostnames |
| `DEBUG=False` in production | Disabling debug mode and stack traces |

---

## 21. Browser Automation — Playwright

| Skill | Used For |
|-------|----------|
| **Playwright 1.59** (Python sync API) | Headless browser automation for screenshots |
| `sync_playwright()` context manager | Managing browser lifecycle |
| `p.chromium.launch(headless=True)` | Launching headless Chromium |
| `browser.new_context(viewport=...)` | Setting viewport size (1440×900) |
| `page.goto()` with `wait_until="networkidle"` | Waiting for full page load |
| `page.fill()` | Filling login form fields by CSS selector |
| `page.click()` | Clicking the submit button |
| `page.wait_for_load_state("networkidle")` | Waiting for login redirect |
| `page.screenshot(path=..., full_page=True)` | Full-page PNG screenshots |
| Exception handling per page | Continuing the loop even if individual pages fail |
| ASCII-safe output | Using `OK`/`FAIL` instead of Unicode symbols for Windows cp1254 compatibility |

---

## 22. Software Architecture Patterns

| Pattern | Where Applied |
|---------|---------------|
| **MVT (Model-View-Template)** | Django's architecture — all pages follow this pattern |
| **Repository / Service pattern** | `ZKProofService`, `CrossChainRelayService`, `MerkleTreeService` — logic separated from views |
| **On-chain/off-chain split** | Medical data in IPFS; only SHA-256 hash on the blockchain |
| **Content-addressed IDs** | SHA-256(UUID + timestamp) as entity primary identifiers |
| **Append-only audit log** | `AuditLog` is write-once — no update/delete in admin or views |
| **Middleware annotation** | Middleware adds properties to `request` (`zk_verified`, `cross_chain_timestamp`); views check them |
| **URL-before-parameterized pattern** | Static export paths declared before `<str:id>` paths |
| **Template variable discipline** | Avoiding reserved names (`block`) as context keys |
| **Context-rich views** | Each view computes and passes all needed data — no AJAX-on-load for core content |
| **Single-database simplicity** | All apps in one DB during development; router architecture present for future split |
| **Graceful empty states** | Every list template has `{% empty %}` block with helpful call-to-action |
| **Soft deletes** | `is_active` flag on Patient and MedicalRecord instead of hard deletes |
| **Layer-2 aggregation** | Rollup batch + Merkle root + ZK proof reduces on-chain writes by ~75% |
| **Separation of HTML and API** | Template views at top-level paths; DRF ViewSets under `/api/...` — same data, two interfaces |

---

## Skills Summary

| Category | Core Technologies |
|----------|-------------------|
| Language | Python 3.12 |
| Web Framework | Django 4.2, Django REST Framework 3.17 |
| API Docs | drf-spectacular 0.29, OpenAPI 3.0, Swagger UI, ReDoc |
| Database | PostgreSQL 16, Django ORM, migrations |
| Cryptography | SHA-256, AES-256-GCM, ECDSA (simulated), hashlib, cryptography, pycryptodome |
| Blockchain | Block/Transaction/Rollup/ZK model, Merkle tree, consensus simulation, web3.py |
| Frontend | Django Templates, Bootstrap 5, Bootstrap Icons, Chart.js 4.4, Vanilla JS |
| Security | CSRF, CSP, XSS prevention, token auth, 2FA (pyotp), CORS |
| Async | Celery 5.6, Redis 7, Django cache framework |
| Infrastructure | Docker, Docker Compose, Gunicorn, WhiteNoise |
| Testing | pytest, pytest-django, coverage.py, Django TestCase |
| Automation | Playwright 1.59 (headless browser) |
| DevOps | Git, GitHub, virtual environments, pip, requirements.txt |

---

*MediChain Framework v1.1 — Ankara University — May 2026*
