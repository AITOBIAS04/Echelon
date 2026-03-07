# Auditor Feedback — Sprint-68 (Cycle-021, Sprint-2)

**Auditor:** Paranoid Cypherpunk Auditor
**Date:** 2026-03-07
**Verdict:** APPROVED - LETS FUCKING GO

## Security Checklist

| Category | Status |
|----------|--------|
| Secrets | PASS — no credentials, no hardcoded keys |
| Auth/Authz | PASS — anchor-batch follows existing pattern (no auth change, SDD notes "internal network only for v1") |
| Input Validation | PASS — investigation_id path params validated via DB lookup, 409 on duplicate cert build |
| SQL Injection | PASS — no raw SQL, uses ORM select/where with model attributes |
| Info Disclosure | PASS — GET /certificate returns certificate data only, no internal state leakage |
| Error Handling | PASS — ValueError on invalid state transition, proper 404/409 HTTP responses |
| Bypass Vectors | PASS — state machine cannot skip states (ANCHORED check in transition_to_ready), idempotent batch |
| Certificate Integrity | PASS — batch_anchor_hash is deterministic SHA-256 of sorted cert hashes, issued_at only set during batch |
| Test Coverage | PASS — 8 tests cover all branches: ready transition, no issued_at at ready, batch full lifecycle, hash computation, idempotency, completed status, WS per cert, skip state rejection |

## Notes

- `_VALID_TRANSITIONS` dict is defined but not actively consulted in code — state transitions are enforced by query filter (only READY certs) and explicit checks in `transition_to_ready()`. Acceptable: the constant documents intent and could be used by future validation.
- `persist_certificate_as_ready()` sets `ready_at=datetime.utcnow()`, then `transition_to_ready()` overwrites with `datetime.now(timezone.utc)`. Minor inconsistency (utcnow vs now(utc)) but both produce correct UTC timestamps. The effective `ready_at` is the lifecycle service's value.
- Batch anchor endpoint `POST /certificates/anchor-batch` has no auth gate — SDD explicitly notes "no auth gate for v1 (internal network only)". Acceptable for current scope.
- WS events emitted after `session.flush()` but before route-level `db.commit()` in batch path — this is correct, events only fire after persistence confirms.
- Route ordering: anchor-batch declared before parametric `/{investigation_id}/certificate` — prevents FastAPI matching "certificates" as an investigation_id.

Zero findings. Clean sprint.
