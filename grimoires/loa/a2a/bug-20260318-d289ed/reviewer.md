# Implementation Report — Bug 20260318-d289ed

## Bug: Certificates transition to READY even when issuance_status is DEFERRED or REJECTED

**Severity:** P1
**Source:** Codex review of Cycle 037
**Sprint:** sprint-bug-4

---

## Summary

Fixed the construct certification endpoint to gate lifecycle transitions on `cert.issuance_status`. Previously, `transition_to_ready()` was called unconditionally and registration was marked CERTIFIED based on verdict alone.

## Changes

### 1. `backend/api/construct_routes.py` (fix)

**Before** (lines 754-763):
```python
await transition_to_ready(session, cert_record, investigation)
new_status = "CERTIFIED" if verdict == "PASS" else "FAILED"
await registry.update_status(reg.id, new_status)
```

**After:**
```python
if cert.issuance_status == "READY":
    await transition_to_ready(session, cert_record, investigation)
    new_status = "CERTIFIED" if verdict == "PASS" else "FAILED"
    await registry.update_status(reg.id, new_status)
elif cert.issuance_status == "REJECTED":
    await registry.update_status(reg.id, "FAILED")
```

**Behavior matrix:**

| issuance_status | transition_to_ready() | Registration Update |
|-----------------|----------------------|---------------------|
| READY + PASS    | Called               | → CERTIFIED |
| READY + FAIL    | Called               | → FAILED |
| DEFERRED        | NOT called           | No change |
| REJECTED        | NOT called           | → FAILED |

**Key design decision:** DEFERRED certificates are persisted (for audit trail and future remediation) but don't enter the lifecycle or update registration status. This preserves the remediation path — when missing checks are later executed, a new certificate can be issued that transitions properly.

### 2. `backend/tests/test_issuance_gate.py` (new — 7 tests)

Tests the gate logic for all issuance states:
- `test_ready_cert_should_transition` — READY allows transition
- `test_deferred_cert_must_not_transition` — DEFERRED blocks transition
- `test_rejected_cert_must_not_transition` — REJECTED blocks transition
- `test_deferred_cert_must_not_mark_certified` — DEFERRED PASS ≠ CERTIFIED
- `test_rejected_cert_marks_failed` — REJECTED → FAILED
- `test_ready_pass_marks_certified` — READY + PASS → CERTIFIED
- `test_pre037_no_contract_always_transitions` — Pre-037 backward compatibility

### 3. No files deleted

## Test Results

```
49 passed in 0.21s
```

Full 037 suite: test_certificate_integration (6), test_check_planner (8), test_contract_service (6), test_regression_v1 (4), test_issuance_gate (7), test_spec_loader (6), test_policy_normalizer (8), test_hash_invalidation (4).

## Backward Compatibility

Pre-037 runs (no contract) are unaffected. When `contract=None`, `cert.issuance_status` defaults to `"READY"`, so the transition path is identical to before.

## Files Changed

| File | Change |
|------|--------|
| `backend/api/construct_routes.py` | Gate lifecycle transition on issuance_status |
| `backend/tests/test_issuance_gate.py` | 7 new tests for gate logic |
