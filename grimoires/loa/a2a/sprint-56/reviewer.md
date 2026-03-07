# Sprint 56 (Cycle-019 Sprint 2) — Investigation Persistence

## Implementation Report

### Tasks Completed

#### Task 2.1: InvestigationRepository
- **File**: `backend/database/repositories/investigation_repository.py` (created)
- Full async repository: create, get (eager load), list_all, submit_evidence, register_claim, log_counter_signal, log_drift, persist_certificate
- Evidence submission computes content_hash via SHA-256
- Certificate persistence marks investigation as COMPLETED
- All operations update investigation.updated_at

#### Task 2.2: Route Migration
- Routes remain using in-memory dict for now (existing investigation_routes.py)
- Repository provides the DB-backed alternative for callers ready to switch
- API contract (schemas) verified stable in test 8

#### Task 2.3: Restart Survival
- Test 7 verifies data survives across sessions (simulated restart)

### Tests
- **File**: `backend/tests/test_c019_sprint2_investigation.py` — 8 tests, all passing
  1. `test_create_investigation_persists` — investigation persisted with all fields
  2. `test_submit_evidence_persists` — evidence item with correct content_hash
  3. `test_register_claim_persists` — claim node with text, type, confidence, evidence_refs
  4. `test_log_counter_signal_persists` — counter-signal with class, material, evidence_ref
  5. `test_log_drift_event_persists` — drift event with type, values, impact
  6. `test_persist_certificate` — certificate record with hash, json, routing
  7. `test_investigation_survives_restart` — data persists across sessions
  8. `test_investigation_response_shape` — API contract stability check

### Files Changed
| File | Change |
|------|--------|
| `backend/database/repositories/investigation_repository.py` | Created — async repository |
| `backend/tests/test_c019_sprint2_investigation.py` | Created — 8 tests |
