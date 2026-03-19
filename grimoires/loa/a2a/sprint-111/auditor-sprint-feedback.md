# Security Audit — Sprint 111 (API Routes + TREMOR Fixture + Regression)

**Verdict: APPROVED**

**Auditor:** Paranoid Cypherpunk Auditor
**Date:** 19 March 2026
**Sprint:** sprint-3 (global 111) — API Routes + TREMOR Fixture + Regression
**Cycle:** 038 — Cross-Theatre Paradox Detection

---

## Security Checklist

| # | Category | Verdict | Notes |
|---|----------|---------|-------|
| 1 | Secrets | PASS | No hardcoded credentials, API keys, tokens, or env var reads in any route file |
| 2 | Auth/Authz | PASS | All 7 mutation (POST) endpoints require `Depends(get_current_user)`. Read (GET) endpoints are public. Matches existing codebase auth pattern. |
| 3 | Input Validation | PASS | Pydantic schemas enforce types on all request bodies. `link_confidence` bounded `ge=0.0, le=1.0`. `ResolveParadoxRequest.note` has `min_length=1`. Pagination params bounded with `ge`/`le`. Query filter params (`severity`, `resolution_status`, `theatre_id`, `anchor_type`, `external_source`) compared via SQLAlchemy `==` (parameterized). |
| 4 | SQL Injection | PASS | All queries use SQLAlchemy 2.0 `select().where()` with parameterized expressions. Zero raw SQL. Zero string interpolation in queries. |
| 5 | Data Privacy | PASS | No PII in any field. `value_json` stores oracle data (magnitudes, Kp indices). No user-identifying data logged. |
| 6 | API Security | PASS | Proper HTTP status codes (201 on create, 404 on not found, 409 on invalid transition). Error messages are terse and domain-specific — no stack traces, no internal paths. |
| 7 | Error Handling | PASS | All endpoints catch missing resources with 404. State transition violations return 409 with safe enum-value-only message. No exception internals leaked. |
| 8 | Code Quality | PASS | Thin route handlers delegating to services. Consistent patterns across all 4 route files. Helper functions reduce duplication. |
| 9 | Log Safety | PASS | All logging uses `%s` lazy formatting. `body.note[:100]` truncation prevents unbounded log injection on resolve/dismiss. Log messages contain only IDs and truncated notes. |
| 10 | Router Registration | PASS | All 4 routers registered in `main.py` with try/except guards (lines 596-631). Pattern matches existing registrations. Import failure cannot crash the app. |

---

## Detailed Findings

### ZERO CRITICAL / HIGH / MEDIUM findings.

### LOW (Informational) — Non-blocking

**L1: N+1 query pattern in `list_fact_anchors`** (fact_anchor_routes.py:107-114)
- The list endpoint runs one `COUNT(*)` query per anchor to compute `link_count`. With `limit=200` this is 201 queries per request.
- **Risk:** Performance only, no security impact. Public endpoint with bounded pagination (`le=200`).
- **Mitigation:** Acceptable for current scale. Can be optimized to a single JOIN+GROUP BY if needed.

**L2: `evidence_json` dict spread on resolve/dismiss** (cross_theatre_paradox_routes.py:147-149, 174-176)
- `{**paradox.evidence_json, "resolution_note": body.note}` merges user-supplied `note` (validated string, `min_length=1`) into the existing evidence dict.
- **Risk:** None. The user input is a Pydantic-validated string stored as a dict value, never used as a key, SQL param, or template. The spread cannot overwrite other keys because the user controls only the value, not the key name.

**L3: `TESTNET_AUTO_AUTH` bypass in dependencies.py** (dependencies.py:142-152)
- When `TESTNET_AUTO_AUTH=true`, all mutation endpoints auto-authenticate as `USR_001 / DeepStateTrader`.
- **Risk:** Expected testnet behavior, documented in dependencies.py. Not a sprint-3 concern (pre-existing). Production must ensure this env var is not set.

---

## Files Audited

| File | Lines | Verdict |
|------|-------|---------|
| `backend/api/fact_anchor_routes.py` | 210 | PASS |
| `backend/api/coherence_group_routes.py` | 156 | PASS |
| `backend/api/cross_theatre_paradox_routes.py` | 209 | PASS |
| `backend/api/oracle_consistency_routes.py` | 103 | PASS |
| `backend/main.py` (lines 596-631) | 36 | PASS |
| `backend/tests/test_038_sprint3_routes.py` | 401 | PASS |
| `backend/schemas/fact_anchor_schemas.py` | 57 | PASS |
| `backend/schemas/coherence_group_schemas.py` | 48 | PASS |
| `backend/schemas/cross_theatre_paradox_schemas.py` | 58 | PASS |
| `backend/schemas/oracle_consistency_schemas.py` | 49 | PASS |
| `backend/dependencies.py` (auth section) | 72 | PASS |
| `backend/services/fact_anchor_service.py` | 154 | PASS |

---

## Cross-Sprint Continuity

Reviewed prior audit reports:
- **Sprint 108 (sprint-0):** Schema-only, APPROVED. Noted duplicate index (non-blocking).
- **Sprint 109 (sprint-1):** Services + schemas, APPROVED. Noted unused imports (non-blocking).
- **Sprint 110 (sprint-2):** Scanner + integration, APPROVED. Noted dedup race condition (acceptable).

Sprint 111 closes the cycle by wiring services (sprint-1) and scanner (sprint-2) to the API layer. Auth enforcement now verified end-to-end. No regressions.

---

## Test Verification

17/17 sprint-3 tests pass. 74/74 across all cycle-038 sprints. Regression suite confirms backward compatibility with pre-038 paradox engine.
