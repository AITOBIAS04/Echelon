# Micro-Sprint: Bug 20260318-d289ed

**Bug:** Certificates transition to READY even when issuance_status is DEFERRED or REJECTED
**Severity:** P1
**Sprint ID:** sprint-bug-4

---

## Sprint 1 — Issuance Gate Fix

### Tasks

1. **Write failing tests first**
   - `test_deferred_cert_no_transition`: Mock `transition_to_ready`, build cert with DEFERRED issuance, verify transition NOT called and registration NOT marked CERTIFIED
   - `test_rejected_cert_no_transition`: Same pattern for REJECTED — verify transition NOT called, registration marked FAILED
   - `test_deferred_cert_registration_unchanged`: Verify registration status stays unchanged (not CERTIFIED) for DEFERRED
   - `test_ready_cert_transitions_normally`: Regression — READY + PASS still calls transition and marks CERTIFIED

2. **Fix `construct_routes.py` certification endpoint**
   - Gate `transition_to_ready()` on `cert.issuance_status == "READY"`
   - Gate registration CERTIFIED status on `cert.issuance_status == "READY"`
   - REJECTED: mark registration FAILED but don't transition
   - DEFERRED: persist cert only, no transition, no registration update

3. **Run full 037 test suite**
   - `test_certificate_integration.py` (6 existing + 4 new)
   - `test_check_planner.py`
   - `test_contract_service.py`
   - `test_regression_v1.py`

**Exit:** All tests pass. DEFERRED/REJECTED certs are persisted but not transitioned. Trust surface is coherent.
