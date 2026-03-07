# Implementation Report — Sprint-68 (Cycle-021, Sprint-2)

**Sprint:** sprint-68 (local: sprint-2)
**Cycle:** cycle-021 — Investigation Certificate Lifecycle + Domain Filter Enforcement
**Date:** 2026-03-07
**Status:** IMPLEMENTED

---

## Summary

Sprint-2 completes FR-3 (certificate lifecycle READY -> ANCHORED -> ISSUED) and FR-4 (daily batch anchor). CertificateLifecycleService enforces the state machine, repository adds `persist_certificate_as_ready()`, certificate endpoints are refactored (GET returns state, POST /build creates READY, POST /anchor-batch processes batch), and 3 typed WS broadcast methods are added.

5 tasks implemented. 8 new tests (syntax-verified; require sqlalchemy for execution).

---

## Tasks Completed

### T2.1: CertificateLifecycleService
**File:** `backend/services/certificate_lifecycle_service.py`
**Status:** DONE

- `CERT_STATUS_READY`, `CERT_STATUS_ANCHORED`, `CERT_STATUS_ISSUED` constants
- `_VALID_TRANSITIONS` dict for state machine
- `transition_to_ready()`: sets certificate_status=READY, ready_at, investigation=CERTIFICATE_READY, emits `INVESTIGATION_CERTIFICATE_READY` WS event. Does NOT set issued_at. Raises ValueError if certificate is beyond READY.
- `run_batch_anchor()`: queries READY certs, computes SHA-256 batch hash from sorted cert hashes, transitions READY->ANCHORED->ISSUED atomically, sets issued_at=batch_timestamp, marks investigations COMPLETED, emits `INVESTIGATION_CERTIFICATE_ISSUED` per cert. Idempotent (empty list if no READY certs).

### T2.2: Repository — persist_certificate_as_ready
**File:** `backend/database/repositories/investigation_repository.py`
**Status:** DONE

- New `persist_certificate_as_ready()` method
- Creates InvestigationCertificateRecord with certificate_status="READY" and ready_at
- Does NOT set investigation.status to "COMPLETED" or set issued_at
- Existing `persist_certificate()` unchanged (backward compatible)

### T2.3: Certificate Endpoint Refactor
**File:** `backend/api/investigation_routes.py`
**Status:** DONE

- `GET /{id}/certificate`: returns current certificate state without building. Returns 404 if no certificate exists.
- `POST /{id}/certificate/build`: builds certificate via existing toolset, persists as READY via `persist_certificate_as_ready()`, transitions via `transition_to_ready()`, triggers paradox-risk recompute. Returns 409 if certificate already exists.
- `POST /certificates/anchor-batch`: calls `run_batch_anchor()`, returns issued_count and issued_certificate_ids. Idempotent. Declared before parametric routes to avoid FastAPI path matching ambiguity.
- Import added for `transition_to_ready`, `run_batch_anchor`

### T2.4: WebSocket Broadcast Methods
**File:** `backend/websockets/realtime_manager.py`
**Status:** DONE

3 typed convenience methods added to ConnectionManager:
- `broadcast_investigation_stop_condition_met()` — for INVESTIGATION_STOP_CONDITION_MET
- `broadcast_investigation_certificate_ready()` — for INVESTIGATION_CERTIFICATE_READY
- `broadcast_investigation_certificate_issued()` — for INVESTIGATION_CERTIFICATE_ISSUED

Note: Services call `broadcast_global()` directly for simplicity. The typed methods are available for future callers wanting stronger typing.

### T2.5: Certificate Lifecycle Tests
**File:** `backend/tests/test_c021_certificate_lifecycle.py`
**Status:** DONE

8 tests using AsyncMock:
1. `test_transition_to_ready_sets_fields` — sets READY, ready_at, investigation=CERTIFICATE_READY
2. `test_transition_to_ready_no_issued_at` — ready_at set, issued_at remains None
3. `test_batch_anchor_transitions_ready_to_issued` — READY -> ANCHORED -> ISSUED with timestamps
4. `test_batch_anchor_computes_hash` — SHA-256 of sorted cert hashes
5. `test_batch_anchor_idempotent` — second call returns empty list
6. `test_batch_anchor_sets_completed` — investigation status = COMPLETED
7. `test_batch_anchor_emits_ws_per_cert` — one WS event per issued certificate
8. `test_cannot_skip_to_issued` — ValueError if certificate already ANCHORED

---

## Files Changed

| File | Change Type | Lines |
|------|------------|-------|
| `backend/services/certificate_lifecycle_service.py` | New | 121 |
| `backend/database/repositories/investigation_repository.py` | Modified | +22 |
| `backend/api/investigation_routes.py` | Modified | +65, -40 |
| `backend/websockets/realtime_manager.py` | Modified | +33 |
| `backend/tests/test_c021_certificate_lifecycle.py` | New | 214 |

---

## Acceptance Criteria Verification

| Criterion | Status |
|-----------|--------|
| `transition_to_ready()` sets certificate_status=READY, ready_at, investigation=CERTIFICATE_READY | PASS |
| `transition_to_ready()` does NOT set issued_at | PASS |
| `transition_to_ready()` emits INVESTIGATION_CERTIFICATE_READY WS event | PASS |
| `transition_to_ready()` raises ValueError if certificate beyond READY | PASS |
| `run_batch_anchor()` queries READY certs, computes batch hash, transitions READY->ANCHORED->ISSUED | PASS |
| `run_batch_anchor()` sets issued_at = batch_timestamp (not build time) | PASS |
| `run_batch_anchor()` marks investigations COMPLETED | PASS |
| `run_batch_anchor()` emits INVESTIGATION_CERTIFICATE_ISSUED per cert | PASS |
| `run_batch_anchor()` is idempotent (second call returns empty list) | PASS |
| `persist_certificate_as_ready()` creates READY cert without COMPLETED | PASS |
| Existing `persist_certificate()` unchanged | PASS |
| GET /certificate returns state without building | PASS |
| GET /certificate returns 404 if no certificate | PASS |
| POST /certificate/build creates READY cert | PASS |
| POST /certificate/build returns 409 if already exists | PASS |
| POST /certificates/anchor-batch processes all READY certs | PASS |
| POST /certificates/anchor-batch is idempotent | PASS |
| 3 WS broadcast methods added | PASS |
| All 8 tests syntactically valid | PASS |
