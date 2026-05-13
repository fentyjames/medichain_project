# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Layout Quirk

The working directory `E:\medichain_project` contains BOTH the Django apps AND the inner config package also named `medichain_project/`. `manage.py` lives at the working-directory root, so all `python manage.py ...` commands run from `E:\medichain_project`, NOT from an inner subdirectory. The README's setup instructions tell you to `cd medichain_project` first — that is stale; ignore it for this checkout.

## Common Commands

Activate the venv first (`venv\Scripts\activate` on Windows PowerShell), then from the project root:

```powershell
python manage.py runserver               # dev server on :8000
python manage.py migrate                 # apply migrations (default DB only — see DB note)
python manage.py createsuperuser
python manage.py collectstatic --noinput

python manage.py test tests --verbosity=2                          # full suite
python manage.py test tests.test_medichain.ZKProofServiceTest      # single test class
python manage.py test tests.test_medichain.APIIntegrationTest.test_dashboard_api  # single test
```

Coverage: `coverage run --source='.' manage.py test tests && coverage html`.

Celery (optional, only if exercising async tasks): `celery -A medichain_project worker --loglevel=info` with `redis-server` running.

## Database Configuration — Important

`medichain_project/settings.py` currently defines **only the `default` PostgreSQL database** (host `localhost:5433`, user `postgres`, password `master011`, db `medichain_db`). The `blockchain` database alias and the `DATABASE_ROUTERS = ['medichain_project.db_router.BlockchainRouter']` line are commented out.

Consequences:
- Both `healthcare` and `blockchain` apps' tables now live in the same Postgres DB. Do NOT run `migrate --database=blockchain` — that alias does not exist.
- `medichain_project/db_router.py` (`BlockchainRouter`) is dormant. Re-enabling it requires uncommenting the `blockchain` DB entry AND the `DATABASE_ROUTERS` line together; otherwise migrations for the `blockchain` app will silently go to the wrong DB.
- Cross-app `ForeignKey`s like `healthcare.MedicalRecord.blockchain_tx → blockchain.Transaction` work today because everything is in one DB. If the router is re-enabled, these FKs cross databases and will break — see the commented-out `blockchain_tx_hash` / `blockchain_network_id` string fields in `healthcare/models.py`, which are the intended workaround for that mode.

The credentials in `settings.py` are checked-in defaults; there is no `.env` loading wired up despite `python-decouple` being in requirements.

## Architecture

Django 4.2 + DRF monolith implementing a *simulated* Layer-2 blockchain + ZK-proof + cross-chain relay framework for healthcare records. Nothing actually touches an external chain — `web3` is a dependency but the on-chain work is in-process simulation (hashes, JSON "proofs"). Treat the cryptography as illustrative, not production-grade.

### Apps and what each owns

- **`blockchain/`** — Core ledger primitives. Models: `BlockchainNetwork`, `Block`, `Transaction`, `RollupBatch`, `CrossChainMessage`, `ValidatorNode`, `SmartContract`. `models.Block.save()` and `Transaction.save()` auto-compute their SHA-256 hash on first save; `RollupBatch.calculate_merkle_root()` is the L2 aggregation primitive. Also exposes DRF ViewSets under `/api/blockchain/api/...`.
- **`healthcare/`** — Domain models: `Patient`, `Hospital`, `Laboratory`, `InsuranceProvider`, `MedicalRecord`, `AccessPermission`, `AuditLog`. `MedicalRecord` follows on-chain-anchor / off-chain-storage pattern: `data_hash` + `ipfs_hash` on record, encrypted blob notionally in IPFS. IDs are SHA-256(uuid + timestamp) auto-generated in `save()`.
- **`zk_proofs/`** — `ZKProofService` (zk-SNARK/STARK *simulation* — proofs are JSON dicts of hashed inputs, NOT real cryptographic proofs) and `MerkleTreeService`. `verify_proof()` re-hashes the expected inputs and compares structure; this is the verification contract every other component depends on.
- **`cross_chain/`** — `CrossChainRelayService` uses `ZKProofService` to verify messages before relaying. Nonce replay-protection methods (`_is_nonce_used` / `_mark_nonce_used`) are TODO stubs — replay protection is currently a no-op.
- **`api/`** — Aggregator app under `/api/v1/`. Token-auth login, dashboard, and orchestration endpoints that compose the other apps (e.g. `CreateRollupView` reads `Transaction`s and writes a `RollupBatch` + ZK proof in one shot).

### URL surface

`medichain_project/urls.py` mounts two distinct things on overlapping paths:
- **Template views** (server-rendered HTML dashboards) at top-level paths: `/blockchain/...`, `/healthcare/...`, `/cross-chain/...`, `/zk-proofs/...`.
- **REST APIs** under `/api/blockchain/`, `/api/healthcare/`, `/api/cross-chain/`, `/api/zk-proofs/`, and the aggregated `/api/v1/`.

App-level URL configs (e.g. `blockchain/urls.py`) re-nest under `api/` inside their include, so the full path is `/api/blockchain/api/<resource>/` — easy to get wrong when constructing URLs.

### Middleware

`blockchain/middleware.py` adds two custom middlewares loaded globally:
- `ZKProofMiddleware` — sets `request.zk_verified` based on the `X-ZK-Proof` header for `/api/healthcare/records/` requests, and stamps response security headers (`X-Frame-Options`, `X-MediChain-Version`, etc.).
- `CrossChainMiddleware` — times `/api/cross-chain/` requests via `X-Cross-Chain-Duration` response header.

Neither blocks requests; they only annotate. Endpoint handlers must consult `request.zk_verified` if they want to enforce.

### Authentication

DRF defaults to `IsAuthenticated` with `TokenAuthentication` + `SessionAuthentication`. Obtain a token via `POST /api/v1/auth/login/`. CSRF is enabled — API clients must use the token header to bypass session-CSRF, or fetch a cookie first.

### Config knobs

App-specific tunables live in `MEDICHAIN_CONFIG` in `settings.py`: `ROLLUP_BATCH_SIZE` (default 50), `ZK_PROOF_TYPE` (`zk_snark`), `CROSS_CHAIN_RELAY_INTERVAL`, and the static `BLOCKCHAIN_NETWORKS` list used to seed `BlockchainNetwork` rows.

## Testing Notes

All tests live in `tests/test_medichain.py` (one file, multiple `TestCase` classes — that's why test paths look like `tests.test_medichain.<ClassName>`). The suite mixes unit tests (ZK service, Merkle tree), model tests (which hit the test DB), API integration tests, and a `PerformanceTest` class — the last one is slow; skip it when iterating with `tests.test_medichain.<SpecificClass>`.
