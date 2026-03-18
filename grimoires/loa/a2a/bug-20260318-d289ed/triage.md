# Bug Triage — 20260318-d289ed

## Summary

Certificates are issued and transitioned to READY even when `issuance_status` is DEFERRED or REJECTED. The construct certification route in `construct_routes.py` unconditionally calls `transition_to_ready()` and marks the registration CERTIFIED based on verdict alone, ignoring the computed `issuance_status`.

## Severity: P1

Trust violation — collapses the distinction between issuance readiness and non-issuable states, which is a core guarantee of Cycle 037.

## Root Cause

`construct_routes.py:737-763` — Two bugs in sequence:

1. **Line 757**: `transition_to_ready()` is called unconditionally after certificate persistence. Should only be called when `cert.issuance_status == "READY"`.

2. **Lines 762-763**: Registration status is computed from `verdict` alone (`CERTIFIED if verdict == "PASS"`). Should also gate on `cert.issuance_status == "READY"` — a DEFERRED PASS must not appear CERTIFIED.

## Expected Behavior

| issuance_status | transition_to_ready() | Registration Status |
|-----------------|----------------------|---------------------|
| READY           | Called               | CERTIFIED (if PASS) |
| DEFERRED        | NOT called           | Unchanged (stays EVALUATING) |
| REJECTED        | NOT called           | FAILED |

## Fix

```python
# Gate lifecycle transition on issuance status
if cert.issuance_status == "READY":
    await transition_to_ready(session, cert_record, investigation)
    new_status = "CERTIFIED" if verdict == "PASS" else "FAILED"
    await registry.update_status(reg.id, new_status)
elif cert.issuance_status == "REJECTED":
    new_status = "FAILED"
    await registry.update_status(reg.id, new_status)
# DEFERRED: persist cert but don't transition or update registration
```

## Test Plan

1. **Test DEFERRED cert does NOT call transition_to_ready** — mock transition_to_ready, verify not called when issuance_status is DEFERRED
2. **Test REJECTED cert does NOT call transition_to_ready** — same pattern, REJECTED status
3. **Test DEFERRED cert does NOT mark registration CERTIFIED** — verify registration stays unchanged
4. **Test READY cert still transitions normally** — regression: existing happy path works

## Affected Files

- `backend/api/construct_routes.py` (fix)
- `backend/tests/test_certificate_integration.py` (new tests)
