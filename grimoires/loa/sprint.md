# Sprint Plan — Cycle-021: Investigation Certificate Lifecycle + Domain Filter Enforcement

**Cycle:** cycle-021
**Date:** 7 March 2026
**PRD:** grimoires/loa/prd.md
**SDD:** grimoires/loa/sdd.md
**Builder:** Loa (backend/runtime only)
**Sprints:** 3 (sprint-0 through sprint-2)

---

## Overview

4 narrowly-scoped items across 3 sprints. Sprint-0 lays the foundation (migration + domain filter validator). Sprint-1 adds automated stop condition evaluation. Sprint-2 completes the certificate lifecycle state machine and batch anchor.

**Dependency chain:**
```
Sprint-0: Migration + Models + DomainFilterValidator + Route Integration
    ↓
Sprint-1: StopConditionOrchestrator + Mutation Path Wiring
    ↓
Sprint-2: CertificateLifecycleService + Endpoint Refactor + Batch Anchor
```

---

## Sprint 0: Foundation — Migration + Domain Filter Enforcement

**Goal:** Database schema changes for all 4 FRs, model updates, and complete FR-1 (domain filter enforcement at ingestion).

**Global ID:** sprint-66

### Tasks

#### T0.1: Alembic Migration — 7 New Columns
**File:** `backend/alembic/versions/c021_certificate_lifecycle.py`
**Description:** Create idempotent migration adding 3 columns to `investigations` (stop_condition_status, stop_condition_reason, stop_condition_evaluated_at) and 4 columns to `investigation_certificates` (certificate_status, ready_at, anchored_at, batch_anchor_hash). Revision chain: `c020_replay_source_run_id` -> `c021_certificate_lifecycle`.
**Acceptance Criteria:**
- Migration runs without error on fresh and existing databases
- All 7 columns created with correct types, defaults, and nullability
- Idempotent: running twice produces no error
- Downgrade drops all 7 columns
**Effort:** Small

#### T0.2: Model Updates — Investigation + CertificateRecord
**File:** `backend/database/models.py`
**Description:** Add 3 new fields to `Investigation` class (stop_condition_status, stop_condition_reason, stop_condition_evaluated_at) and 4 new fields to `InvestigationCertificateRecord` class (certificate_status, ready_at, anchored_at, batch_anchor_hash). Update Investigation status comment to include `CERTIFICATE_READY`.
**Acceptance Criteria:**
- Investigation has 3 new Optional fields
- InvestigationCertificateRecord has 4 new fields (certificate_status defaults to "READY")
- All field types match migration exactly
- Existing tests still pass
**Effort:** Small
**Depends on:** T0.1

#### T0.3: DomainFilterValidator Service
**File:** `backend/services/domain_filter_validator.py`
**Description:** Implement `DomainFilterViolation` exception, `get_allowed_sources()`, `validate_evidence_source()`, and `validate_signal_source()` as pure functions per SDD section 4.1. Imports `DOMAIN_FILTER_SOURCE_GROUPS` from `signal_scanner.py`.
**Acceptance Criteria:**
- `get_allowed_sources()` expands domain filter enum values to source group sets
- `validate_evidence_source()` raises DomainFilterViolation for out-of-scope source_id
- `validate_evidence_source()` is no-op when domain_filters_json is empty
- `validate_signal_source()` rejects out-of-scope signal sources
- `validate_signal_source()` passes meta-methods (automated_osint, human_submitted, paradox_engine)
- DomainFilterViolation carries source, allowed_sources, domain_filters
**Effort:** Small

#### T0.4: Domain Filter Route Integration
**File:** `backend/api/investigation_routes.py`
**Description:** Add `validate_evidence_source()` call before evidence persistence in `POST /{id}/evidence`. Add `validate_signal_source()` call before counter-signal persistence in `POST /{id}/counter-signals`. Catch `DomainFilterViolation` and return HTTP 422.
**Acceptance Criteria:**
- Evidence from in-scope domain: accepted (existing behavior preserved)
- Evidence from out-of-scope domain: rejected with 422 and clear error message
- Evidence to investigation with empty domain filters: accepted (no enforcement)
- Counter-signal from out-of-scope domain: rejected with 422
- Existing evidence/counter-signal tests still pass
**Effort:** Small
**Depends on:** T0.3

#### T0.5: Domain Filter Tests
**File:** `backend/tests/test_c021_domain_filter_validator.py`
**Description:** 6 unit tests per SDD section 11.1: in-scope passes, out-of-scope rejected, empty filters passes all, signal out-of-scope rejected, meta-methods always pass, get_allowed_sources expands correctly.
**Acceptance Criteria:**
- All 6 tests pass
- Tests are pure (no DB, no mocks)
- Tests cover all 9 DomainFilter enum values
**Effort:** Small

---

## Sprint 1: Automated Stop Condition Evaluation

**Goal:** Complete FR-2 — drift as first-class stop condition input. Implement StopConditionOrchestrator and wire it into all mutation paths.

**Global ID:** sprint-67

### Tasks

#### T1.1: StopConditionOrchestrator Service
**File:** `backend/services/stop_condition_orchestrator.py`
**Description:** Implement `StopConditionResult` class, `evaluate_after_mutation()` async function, and `_compute_time_remaining()` helper per SDD section 4.2. Rebuilds toolset, evaluates stop conditions, persists result, emits WS event on readiness change.
**Acceptance Criteria:**
- `evaluate_after_mutation()` rebuilds toolset from investigation state
- Checks material drift via `commitment_monitor.has_material_drift()`
- Calls `InvestigationStopConditionEvaluator.evaluate()` with correct params
- Persists stop_condition_status, stop_condition_reason, stop_condition_evaluated_at
- Emits `INVESTIGATION_STOP_CONDITION_MET` WS event only on NOT_READY -> READY transition
- Drift trigger augments reason with `drift_material;` prefix
- Skips COMPLETED and CERTIFICATE_READY investigations
**Effort:** Medium

#### T1.2: Mutation Path Wiring
**File:** `backend/api/investigation_routes.py`
**Description:** Add `evaluate_after_mutation()` calls after persistence in: `POST /{id}/evidence` (trigger="evidence"), `POST /{id}/counter-signals` (trigger="counter_signal"), `POST /{id}/drift` (trigger="drift").
**Acceptance Criteria:**
- Evidence submission triggers stop condition evaluation
- Counter-signal ingestion triggers stop condition evaluation
- Drift event triggers stop condition evaluation
- Non-material drift does not force readiness (evaluation runs but result reflects evaluator output)
- Existing endpoint behavior preserved (only adds orchestrator call)
**Effort:** Small
**Depends on:** T1.1

#### T1.3: Readiness Endpoint
**File:** `backend/api/investigation_routes.py`
**Description:** Add `GET /{id}/readiness` endpoint per SDD section 6.2. Returns stop_condition_status, stop_condition_reason, stop_condition_evaluated_at, and certificate status if exists.
**Acceptance Criteria:**
- Returns 200 with readiness state for existing investigation
- Returns 404 for unknown investigation
- Includes certificate_status when certificate exists
- Returns null fields when stop condition has never been evaluated
**Effort:** Small
**Depends on:** T1.1

#### T1.4: StopConditionOrchestrator Tests
**File:** `backend/tests/test_c021_stop_condition_orchestrator.py`
**Description:** 6 tests per SDD section 11.2: persists ready status, emits WS on readiness change, no WS when already ready, drift trigger includes drift in reason, skips completed investigation, evidence trigger evaluates stop.
**Acceptance Criteria:**
- All 6 tests pass
- WS manager is mocked for event assertions
- Tests use sync Session with SQLite in-memory (existing pattern)
- Investigation state is correctly set up with evidence/claims for evaluator
**Effort:** Medium

---

## Sprint 2: Certificate Lifecycle + Batch Anchor

**Goal:** Complete FR-3 (certificate lifecycle READY -> ANCHORED -> ISSUED) and FR-4 (daily batch anchor at 00:00 UTC). Refactor certificate endpoints.

**Global ID:** sprint-68

### Tasks

#### T2.1: CertificateLifecycleService
**File:** `backend/services/certificate_lifecycle_service.py`
**Description:** Implement `transition_to_ready()` and `run_batch_anchor()` async functions per SDD section 4.3. State machine constants, valid transitions, batch anchor hash computation.
**Acceptance Criteria:**
- `transition_to_ready()` sets certificate_status=READY, ready_at, investigation=CERTIFICATE_READY
- `transition_to_ready()` does NOT set issued_at
- `transition_to_ready()` emits `INVESTIGATION_CERTIFICATE_READY` WS event
- `transition_to_ready()` raises ValueError if certificate is beyond READY
- `run_batch_anchor()` queries READY certs, computes batch hash, transitions READY->ANCHORED->ISSUED
- `run_batch_anchor()` sets issued_at = batch_timestamp (not build time)
- `run_batch_anchor()` marks investigations COMPLETED
- `run_batch_anchor()` emits `INVESTIGATION_CERTIFICATE_ISSUED` per cert
- `run_batch_anchor()` is idempotent (second call returns empty list)
**Effort:** Medium

#### T2.2: Repository — persist_certificate_as_ready
**File:** `backend/database/repositories/investigation_repository.py`
**Description:** Add `persist_certificate_as_ready()` method that creates InvestigationCertificateRecord with status=READY and ready_at set, but does NOT set investigation to COMPLETED or set issued_at.
**Acceptance Criteria:**
- Creates certificate with certificate_status="READY" and ready_at
- Does NOT set investigation.status to "COMPLETED"
- Does NOT set issued_at
- Existing `persist_certificate()` unchanged (backward compatible)
**Effort:** Small

#### T2.3: Certificate Endpoint Refactor
**File:** `backend/api/investigation_routes.py`
**Description:** Refactor `GET /{id}/certificate` to return current state without building. Add `POST /{id}/certificate/build` that builds certificate and transitions to READY. Add `POST /certificates/anchor-batch` for batch anchor trigger.
**Acceptance Criteria:**
- `GET /certificate` returns certificate state (READY/ANCHORED/ISSUED) without building
- `GET /certificate` returns 404 if no certificate exists (with helpful message)
- `POST /certificate/build` builds certificate and transitions to READY
- `POST /certificate/build` returns 409 if certificate already exists
- `POST /certificate/build` sets investigation to CERTIFICATE_READY (not COMPLETED)
- `POST /certificates/anchor-batch` processes all READY certificates
- `POST /certificates/anchor-batch` is idempotent
- Batch endpoint returns issued_count and issued_certificate_ids
**Effort:** Medium
**Depends on:** T2.1, T2.2

#### T2.4: WebSocket Broadcast Methods
**File:** `backend/websockets/realtime_manager.py`
**Description:** Add convenience broadcast methods for investigation certificate events if needed. The services already call `broadcast_global()` directly, but add typed methods for consistency with existing pattern (e.g., `broadcast_scenario_run_status`, `broadcast_routing_decision`).
**Acceptance Criteria:**
- 3 event types emitted correctly: INVESTIGATION_STOP_CONDITION_MET, INVESTIGATION_CERTIFICATE_READY, INVESTIGATION_CERTIFICATE_ISSUED
- Message format: `{type, timestamp, data}` (existing pattern)
- Events fire from correct service methods (verified by tests)
**Effort:** Small

#### T2.5: Certificate Lifecycle Tests
**File:** `backend/tests/test_c021_certificate_lifecycle.py`
**Description:** 8 tests per SDD section 11.3: transition_to_ready sets fields, no issued_at at ready, batch transitions ready to issued, batch computes hash, batch idempotent, batch sets completed, batch emits WS per cert, cannot skip to issued.
**Acceptance Criteria:**
- All 8 tests pass
- Tests cover full lifecycle: READY -> ANCHORED -> ISSUED
- Batch hash is deterministic (SHA-256 of sorted cert hashes)
- Idempotency verified (second batch call returns empty)
- WS manager mocked for event assertions
**Effort:** Medium

---

## Risk Assessment

| Risk | Sprint | Mitigation |
|------|--------|------------|
| Migration breaks existing tests | 0 | New columns are nullable/have defaults; run full test suite |
| Domain filter rejects valid evidence | 0 | Empty filters = no enforcement; meta-methods always pass |
| Stop condition evaluation latency | 1 | Lightweight pure function; toolset rebuild is fast |
| Certificate GET behavior change | 2 | GET still works (returns state); build is new POST |
| Batch anchor timing | 2 | Idempotent; timestamp is parameterizable for tests |

## Success Metrics

| Metric | Sprint | Verification |
|--------|--------|-------------|
| Zero silent out-of-scope ingestion | 0 | Domain filter tests (6 tests) |
| Drift triggers automated stop eval | 1 | Orchestrator tests (6 tests) |
| Certificate lifecycle enforced | 2 | Lifecycle tests (8 tests) |
| Batch anchor idempotent | 2 | Batch test (explicit second-call test) |
| Total test coverage | All | 20 new tests across 3 test files |
