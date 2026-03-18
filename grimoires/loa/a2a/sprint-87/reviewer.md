# Sprint 87 (Cycle 037, Sprint 3) — Implementation Report

## Sprint: API Routes, Certificate Integration, Regression

**Status:** COMPLETE
**Tests:** 10/10 passing (42/42 cumulative)
**Files Changed:** 2 new, 2 modified

---

## Task 3.1: Contract API Endpoints

**Status:** COMPLETE

### Implementation

- **`backend/api/construct_routes.py`** — 3 new endpoints:
  - `POST /{slug}/{version}/contract` — Creates/refreshes evaluation contract from yaml_content
    - Idempotent: same spec_hash returns existing ACTIVE
    - Different spec_hash supersedes old, creates new
    - 404 if registration not found, 400 if invalid YAML
  - `GET /{slug}/{version}/contract` — Returns ACTIVE contract
    - 404 if no ACTIVE contract exists
  - `GET /{slug}/{version}/contracts` — Lists all contracts (ACTIVE + SUPERSEDED)
- **`_contract_to_response()`** helper — Converts EvaluationContract model to ContractResponse schema, handling enum-to-string coercion for status field

### Acceptance Criteria

- [x] POST creates contract from YAML content
- [x] GET returns ACTIVE contract
- [x] GET /contracts lists all contracts
- [x] 404 for missing registration
- [x] 400 for invalid YAML (delegated to ContractService → SpecLoader)

---

## Task 3.2: Modify create_run Endpoint

**Status:** COMPLETE

### Implementation

- **`backend/api/construct_routes.py`** — Modified `POST /{slug}/{version}/runs`:
  - Fetches ACTIVE contract for registration via `ContractService.get_active_contract()`
  - Returns 409 if no ACTIVE contract exists (with guidance to POST contract first)
  - Threads `contract.contract_hash` into `ConstructAdapter.create_run()`
  - Contract validation happens in adapter (raises ValueError if SUPERSEDED)

### Acceptance Criteria

- [x] Run creation requires ACTIVE contract
- [x] 409 if no ACTIVE contract
- [x] contract_hash threaded into investigation

---

## Task 3.3: Certificate Builder Extensions + Issuance Logic

**Status:** COMPLETE

### Implementation

- **`backend/services/construct_certificate_builder.py`** — Extended:
  - `ConstructCertificate` dataclass: new optional fields `contract_hash`, `spec_hash`, `issuance_status`, `check_plan`, `remediation`
  - `build()`: accepts optional `contract` parameter, computes issuance logic when present
  - `compute_issuance_status()`: READY (all checks + PASS), DEFERRED (missing checks or tier_cap), REJECTED (not PASS)
  - `_build_check_plan()`: planned-vs-executed comparison per check (RUBRIC scored by domain, ANCHOR always EXECUTED)
  - `_build_remediation()`: machine-readable payload for DEFERRED (missing check IDs, counts, recommendation)
  - `to_certificate_json()`: includes contract fields only when present (backward compat)
- **`backend/api/construct_routes.py`** — Modified `issue_certificate` and `get_certificate`:
  - `issue_certificate`: fetches contract via `investigation.contract_hash`, passes to builder
  - Response includes `check_plan`, `remediation`, `issuance_status`, `contract_hash`, `spec_hash`
  - `get_certificate`: reconstructs check_plan/remediation schemas from stored certificate_json
  - Pre-037 runs (no contract_hash): contract fields null, issuance_status defaults to READY
- **`backend/tests/test_certificate_integration.py`** — 6 tests:
  1. All checks PASS → READY
  2. Missing checks PASS → DEFERRED with remediation
  3. FAIL verdict → REJECTED
  4. Remediation payload includes missing check IDs
  5. check_plan shows EXECUTED/NOT_EXECUTED per check
  6. Pre-037 run → certificate omits contract fields

### Acceptance Criteria

- [x] All 6 tests pass
- [x] READY/DEFERRED/REJECTED paths work
- [x] check_plan in certificate shows per-check status
- [x] Remediation payload for DEFERRED
- [x] Pre-037 backward compat

---

## Task 3.4: V1 Regression Tests

**Status:** COMPLETE

### Implementation

- **`backend/tests/test_regression_v1.py`** — 4 tests:
  1. Registration schemas validate correctly (request, response, list item)
  2. Certificate builder without contract → V1 fields present, new fields null
  3. Certificate JSON excludes contract fields for pre-037 runs
  4. CertificateResponse schema: new fields Optional with defaults

### Acceptance Criteria

- [x] All 4 tests pass
- [x] No regression in V1 flow
- [x] Schema backward compatibility verified

---

## Test Results

```
42 passed in 0.19s

# Sprint 3 tests (10)
backend/tests/test_certificate_integration.py — 6 tests PASSED
backend/tests/test_regression_v1.py — 4 tests PASSED

# Sprint 2 regression (18)
backend/tests/test_check_planner.py — 8 tests PASSED
backend/tests/test_contract_service.py — 6 tests PASSED
backend/tests/test_hash_invalidation.py — 4 tests PASSED

# Sprint 1 regression (14)
backend/tests/test_spec_loader.py — 6 tests PASSED
backend/tests/test_policy_normalizer.py — 8 tests PASSED
```

---

## Files Summary

### New Files (2)
| File | Lines | Purpose |
|------|-------|---------|
| `backend/tests/test_certificate_integration.py` | 183 | 6 certificate issuance tests |
| `backend/tests/test_regression_v1.py` | 138 | 4 V1 regression tests |

### Modified Files (2)
| File | Changes |
|------|---------|
| `backend/api/construct_routes.py` | 3 contract endpoints, create_run requires ACTIVE contract, certificate includes contract fields |
| `backend/services/construct_certificate_builder.py` | 5 new fields on ConstructCertificate, build() accepts contract, issuance logic, check_plan, remediation |
