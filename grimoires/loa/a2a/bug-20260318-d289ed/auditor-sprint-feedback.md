# Sprint bug-4 (bug-20260318-d289ed) — Security Audit

APPROVED - LETS FUCKING GO

## Audit Scope
Bug fix: issuance gate for construct certification lifecycle. 2 code files changed, 1 test file added.

## Security Checklist

### Secrets: PASS
No credentials, environment variables, or API keys touched.

### Auth/Authz: PASS
This fix IS an authorization fix. Previously, DEFERRED/REJECTED certs could escalate to READY status (privilege escalation on the trust surface). The gate now correctly prevents this:
- READY: full lifecycle (transition + CERTIFIED)
- DEFERRED: persist only (no transition, no status change)
- REJECTED: persist + mark FAILED (no transition)

### Input Validation: PASS
`issuance_status` is always computed by `compute_issuance_status()` from internal state (verdict, check_plan, tier_cap). No user-controlled path can set it directly.

### Data Privacy: PASS

### API Security: PASS
Response correctly surfaces `issuance_status` at line 806, so API consumers see DEFERRED/REJECTED status. No information leak — this is the intended contract.

### Error Handling: PASS
DEFERRED is a silent no-op on the transition path (correct behavior — cert is persisted for future remediation). No exception swallowing.

### Code Quality: PASS
- Both code paths (construct_routes.py, run_evaluation.py) have identical gate pattern
- Review caught the run_evaluation.py twin and both were fixed
- 7 new tests covering all issuance states + pre-037 backward compat
- 49/49 tests pass

## Findings Summary
No findings. Clean fix for a real trust violation.
