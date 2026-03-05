# Sprint 35 (Cycle-014c Sprint 3) — Implementation Report

**Cycle:** cycle-014c
**Sprint:** 3 of 3 (global: sprint-35)
**Date:** 2026-03-05
**Status:** COMPLETE

---

## Summary

Sprint 3 completes the Investigation Toolset Implementation cycle by adding:
- Stop Condition Schema + Persistence + Commitment Hash integration
- Investigation Certificate model (30 fields, frozen) and Builder with routing logic
- Stop Condition Evaluator (3 condition types)
- Investigation Toolset Orchestrator (wires all 8 tools)
- Deterministic Artefact Writers (canonical JSON + SHA-256)
- 25 new tests across 5 test files

All 67 investigation toolset tests pass. Full suite: 955 passed, 15 skipped, 0 failures.

---

## Tasks Completed

### Task 3.1: Stop Condition Schema + Persistence + Commitment Hash

**Modified files:**
- `backend/schemas/theatre.py` — added `stop_condition: Optional[str]` and `stop_config: Optional[dict]` to `TheatreCreate` and `TheatreResponse`
- `backend/database/models.py` — added `stop_condition = Column(String(30), nullable=True)` and `stop_config = Column(JSON, nullable=True)` to `Theatre`
- `backend/api/theatre_routes.py` — stores stop fields on create, includes in commitment hash (extends hash with stop fields JSON), returns stop fields in create response
- `backend/alembic/versions/c014c_add_stop_condition_columns.py` — new migration adding both columns

**Design decisions:**
- Commitment hash extension: when stop fields are present, the base commitment hash is extended by hashing `base_hash + json.dumps(stop_fields)`. This preserves backward compatibility (no stop fields = same hash).
- Immutability post-COMMITTED: enforced by design — no endpoint exists to mutate stop fields after creation, and the commitment hash seals the values.

### Task 3.2: Investigation Certificate + Builder

**New file:** `backend/investigation/certificate.py`

**Key types:**
- `StopCondition` enum (OUTCOME_RESOLUTION, EVIDENCE_THRESHOLD, SPONSOR_DEFINED)
- `RoutingDecision` enum (ALLOWED, REVIEW_REQUIRED)
- `InvestigationCertificate` — 30-field frozen Pydantic model
- `InvestigationCertificateBuilder` — assembles certificate from all tool state

**Routing logic (priority cascade):**
1. Material drift → REVIEW_REQUIRED ("drift_event_material")
2. Material counter-signal → REVIEW_REQUIRED ("counter_signal_material")
3. Single provenance class → REVIEW_REQUIRED ("single_provenance_class")
4. Default → ALLOWED ("all_checks_passed")

**Certificate hash:** SHA-256 of canonical_json(hash_payload) where hash_payload contains all identity, hash, summary, and routing fields.

### Task 3.3: Stop Condition Evaluator

**New file:** `backend/investigation/stop_conditions.py`

**Key class:** `InvestigationStopConditionEvaluator`
- `OUTCOME_RESOLUTION`: ready when `time_remaining <= 0`
- `EVIDENCE_THRESHOLD`: ready when `min_supported_claims` and `min_corroboration_score` thresholds met
- `SPONSOR_DEFINED`: ready when `milestone_timestamp` reached

Only reads committed stop_config keys. No runtime override mechanism.

### Task 3.4: Investigation Toolset Orchestrator

**New file:** `backend/investigation/toolset.py`

**Key types:**
- `InvestigationConfig` — domain_filters, stop_condition, stop_config
- `InvestigationToolset` — instantiates all 8 tools, provides delegation methods

Delegation methods: `submit_evidence`, `register_claim`, `log_counter_signal`, `log_drift`, `run_scan`, `resolve_entity`. Plus `build_certificate()` for terminal artefact assembly.

### Task 3.5: Deterministic Artefact Writers

**New file:** `backend/investigation/artifacts.py`

**Key function:** `write_artifact(name, data) → (json_string, sha256_hash)`
- Uses `canonical_json()` for deterministic serialisation
- Validates artefact type against 9 supported types
- Same inputs → byte-identical output guaranteed

### Task 3.6: Sprint 3 Tests (25 tests)

| Test File | Tests | Status |
|-----------|-------|--------|
| `test_certificate.py` | 8 | PASS |
| `test_stop_conditions.py` | 5 | PASS |
| `test_stop_condition_commitment.py` | 4 | PASS |
| `test_artifacts.py` | 5 | PASS |
| `test_toolset_e2e.py` | 3 | PASS |
| **Total** | **25** | **ALL PASS** |

---

## Test Results

### Investigation Toolset Tests (67 total across 3 sprints)

| Sprint | Tests | Status |
|--------|-------|--------|
| Sprint 1 (Evidence + Claims) | 17 | PASS |
| Sprint 2 (CS + Monitor + Scanner + Resolver + Checker) | 25 | PASS |
| Sprint 3 (Certificate + Stop + Artifacts + E2E) | 25 | PASS |
| **Total** | **67** | **ALL PASS** |

### Full Suite Regression

```
955 passed, 15 skipped, 0 failures
```

Gate rule: >=942 passed, 15 skipped — SATISFIED.

---

## Files Created/Modified

| File | Action |
|------|--------|
| `backend/schemas/theatre.py` | MODIFIED — added stop_condition, stop_config fields |
| `backend/database/models.py` | MODIFIED — added stop_condition, stop_config columns |
| `backend/api/theatre_routes.py` | MODIFIED — store/include stop fields, commitment hash extension |
| `backend/alembic/versions/c014c_add_stop_condition_columns.py` | NEW — migration |
| `backend/investigation/certificate.py` | NEW — certificate model + builder |
| `backend/investigation/stop_conditions.py` | NEW — stop condition evaluator |
| `backend/investigation/toolset.py` | NEW — orchestrator |
| `backend/investigation/artifacts.py` | NEW — deterministic artefact writers |
| `backend/investigation/tests/test_certificate.py` | NEW — 8 tests |
| `backend/investigation/tests/test_stop_conditions.py` | NEW — 5 tests |
| `backend/investigation/tests/test_stop_condition_commitment.py` | NEW — 4 tests |
| `backend/investigation/tests/test_artifacts.py` | NEW — 5 tests |
| `backend/investigation/tests/test_toolset_e2e.py` | NEW — 3 tests |

---

## Patterns Followed

- All models use `model_config = {"frozen": True}` for immutability
- Sequential IDs maintained (E001, C001, CS001, D001, DB001, ENT001, SRC001, INV-*)
- SHA-256 hashing via `hashlib.sha256()`
- `canonical_json()` from `theatre.engine.canonical_json` for deterministic serialisation
- Properties return copies via `list()`
- No delete methods on service classes (append-only)
- Alembic migration follows existing naming/revision chain pattern
