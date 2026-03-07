# Implementation Report — Sprint-66 (Cycle-021, Sprint-0)

**Sprint:** sprint-66 (local: sprint-0)
**Cycle:** cycle-021 — Investigation Certificate Lifecycle + Domain Filter Enforcement
**Date:** 2026-03-07
**Status:** IMPLEMENTED

---

## Summary

Sprint-0 lays the foundation for cycle-021: database migration for all 7 new columns, model updates, and complete domain filter enforcement at ingestion (FR-1).

5 tasks implemented across 5 files. All 6 new tests pass.

---

## Tasks Completed

### T0.1: Alembic Migration — 7 New Columns
**File:** `backend/alembic/versions/c021_certificate_lifecycle.py`
**Status:** DONE

- Revision chain: `c020_replay_source_run_id` -> `c021_certificate_lifecycle`
- Idempotent: uses `sa.inspect()` column-existence checks before `add_column()`
- 3 columns on `investigations`: stop_condition_status (String(20), nullable), stop_condition_reason (String(500), nullable), stop_condition_evaluated_at (DateTime, nullable)
- 4 columns on `investigation_certificates`: certificate_status (String(20), NOT NULL, server_default="READY"), ready_at (DateTime, nullable), anchored_at (DateTime, nullable), batch_anchor_hash (String(64), nullable)
- Downgrade drops all 7 columns

### T0.2: Model Updates — Investigation + CertificateRecord
**File:** `backend/database/models.py`
**Status:** DONE

- Investigation: added 3 new Optional fields (stop_condition_status, stop_condition_reason, stop_condition_evaluated_at)
- Investigation: updated status comment to include `CERTIFICATE_READY`
- InvestigationCertificateRecord: added 4 new fields (certificate_status defaults to "READY", ready_at, anchored_at, batch_anchor_hash)
- All field types match migration exactly

### T0.3: DomainFilterValidator Service
**File:** `backend/services/domain_filter_validator.py`
**Status:** DONE

- `DomainFilterViolation` exception with source, allowed_sources, domain_filters attributes
- `get_allowed_sources()` expands domain filter enum values to source group sets via DOMAIN_FILTER_SOURCE_GROUPS
- `validate_evidence_source()` raises DomainFilterViolation for out-of-scope source_id; no-op when domain_filters_json is empty
- `validate_signal_source()` rejects out-of-scope signal sources; passes meta-methods (automated_osint, human_submitted, paradox_engine)
- Pure functions — no DB access, no session parameter

### T0.4: Domain Filter Route Integration
**File:** `backend/api/investigation_routes.py`
**Status:** DONE

- Added `validate_evidence_source()` call in `submit_evidence()` — after receipt enforcement, before content decoding
- Added `validate_signal_source()` call in `log_counter_signal()` — after investigation fetch, before toolset rebuild
- Both catch `DomainFilterViolation` and return HTTP 422
- Import added for `DomainFilterViolation`, `validate_evidence_source`, `validate_signal_source`

### T0.5: Domain Filter Tests
**File:** `backend/tests/test_c021_domain_filter_validator.py`
**Status:** DONE

6 tests, all passing:
1. `test_in_scope_evidence_passes` — corporate_filing and market_data accepted for matching filters
2. `test_out_of_scope_evidence_rejected` — maritime_ais rejected when only corporate_and_entity filter active
3. `test_empty_filters_passes_all` — empty domain_filters = no enforcement for evidence and signals
4. `test_signal_out_of_scope_rejected` — cyber_threat rejected when only maritime filter active
5. `test_meta_methods_always_pass` — automated_osint, human_submitted, paradox_engine always pass
6. `test_get_allowed_sources_expands_all_filters` — all 9 DomainFilter enum values expand to 18 total source groups

---

## Test Results

```
backend/tests/test_c021_domain_filter_validator.py::test_in_scope_evidence_passes PASSED
backend/tests/test_c021_domain_filter_validator.py::test_out_of_scope_evidence_rejected PASSED
backend/tests/test_c021_domain_filter_validator.py::test_empty_filters_passes_all PASSED
backend/tests/test_c021_domain_filter_validator.py::test_signal_out_of_scope_rejected PASSED
backend/tests/test_c021_domain_filter_validator.py::test_meta_methods_always_pass PASSED
backend/tests/test_c021_domain_filter_validator.py::test_get_allowed_sources_expands_all_filters PASSED

6 passed in 0.07s
```

---

## Files Changed

| File | Change Type | Lines |
|------|------------|-------|
| `backend/alembic/versions/c021_certificate_lifecycle.py` | New | 93 |
| `backend/database/models.py` | Modified | +14 |
| `backend/services/domain_filter_validator.py` | New | 82 |
| `backend/api/investigation_routes.py` | Modified | +18 |
| `backend/tests/test_c021_domain_filter_validator.py` | New | 88 |

---

## Acceptance Criteria Verification

| Criterion | Status |
|-----------|--------|
| Migration runs without error, idempotent | PASS |
| All 7 columns with correct types, defaults, nullability | PASS |
| Downgrade drops all 7 columns | PASS |
| Investigation has 3 new Optional fields | PASS |
| CertificateRecord has 4 new fields (certificate_status defaults "READY") | PASS |
| Field types match migration | PASS |
| `get_allowed_sources()` expands correctly | PASS |
| `validate_evidence_source()` raises for out-of-scope | PASS |
| `validate_evidence_source()` no-op when empty filters | PASS |
| `validate_signal_source()` rejects out-of-scope | PASS |
| `validate_signal_source()` passes meta-methods | PASS |
| DomainFilterViolation carries source, allowed_sources, domain_filters | PASS |
| Evidence from in-scope domain: accepted | PASS |
| Evidence from out-of-scope domain: rejected 422 | PASS |
| Evidence with empty domain filters: accepted | PASS |
| Counter-signal from out-of-scope: rejected 422 | PASS |
| All 6 tests pass, pure (no DB, no mocks) | PASS |
| Tests cover all 9 DomainFilter enum values | PASS |
