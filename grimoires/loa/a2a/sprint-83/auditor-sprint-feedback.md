# Security Audit — Sprint 83 (cycle-025/sprint-2)

**Auditor:** Paranoid Cypherpunk Auditor
**Verdict:** APPROVED — LETS FUCKING GO
**Date:** 2026-03-17

---

## Checklist Results

| Category | Status | Notes |
|----------|--------|-------|
| Secrets & Credentials | PASS | No hardcoded keys, tokens, passwords, or API secrets. Registry path derived from `__file__` relative path only. |
| SQL Injection | PASS | All queries use SQLAlchemy ORM expression language. Filters applied via `.where()` with column comparison operators. `.in_()` for counter-source IDs is parameterized. Zero raw SQL. |
| Input Validation | PASS | `limit` bounded `ge=1, le=200`. `offset` bounded `ge=0`. `source_group`, `investigation_id`, `since` are optional typed Query params — FastAPI validates types before handler executes. No unbounded result sets. |
| Auth/Authz | INFO | No auth decorators on endpoints. Consistent with existing router pattern (internal intelligence API, auth not yet wired at router level). Non-blocking — same posture as all other OSINT/investigation routes. |
| Error Handling | PASS | `scalar_one_or_none()` for optional latest signal. `or 0` fallback on all `.scalar()` counts. `os.path.exists()` check before RegistryLoader construction. No stack traces or internal state leak in responses. |
| Data Integrity | PASS | Read-only endpoints — no mutations. `collected_at DESC` ordering is deterministic with the composite index. `dict(by_group.all())` correctly transforms SQLAlchemy Row tuples to dict. |
| Path 2 Boundary | PASS | Zero imports from `signal_detector.py` or `osint_registry.py` across all 4 audited files. Verified via content grep. Path 2 (synthetic SignalDetector) remains untouched. |
| Test Coverage | PASS | 10 tests covering: 3 filter paths for GET /signals, 2 states for /health (healthy + degraded), 2 states for /summary (empty + populated), 3 clustering cases for ConvergenceScorer (single domain, two domains, empty). All meaningful code paths exercised. |
| Performance | PASS | Queries use existing composite indexes (`ix_osint_signals_source_group_collected`, `ix_osint_signals_investigation_collected`, `ix_osint_signals_geo_collected`). Pagination caps at 200. No N+1 patterns. RegistryLoader disk read per-request is acceptable for current volume (noted as non-blocking observation). |

---

## Attack Surface Assessment

**Exposure:** Internal-only API. Three read-only GET endpoints plus a pure-function scorer service. No mutations, no file writes, no external HTTP calls, no user-controlled file paths.

**Bounded risk:** The only disk I/O is `RegistryLoader` reading `sources.json` from a hardcoded relative path derived from `os.path.dirname(__file__)` — not user-controllable. The `source_group` and `investigation_id` query params flow into parameterized SQLAlchemy `.where()` clauses with no string interpolation.

**DoS surface:** Pagination is capped at `limit=200`. The `/signals/summary` endpoint does one full-table COUNT, one GROUP BY, one filtered COUNT (counter-signals via `.in_()`), and one filtered COUNT (certificate candidates). All are single-pass aggregates. Convergence scorer is invoked on pre-fetched signal lists, not on unbounded queries.

**Verdict:** Minimal attack surface. No injection vectors. No disclosure vectors. Clean.

---

## Observations

| # | Finding | Severity | Blocking |
|---|---------|----------|----------|
| 1 | `datetime.utcnow()` deprecated since Python 3.12 — should use `datetime.now(datetime.UTC)`. Present in `osint_routes.py` lines 73, 87 and in test helper. Consistent with existing codebase. | LOW | No |
| 2 | Pydantic v2 `class Config` style in `OsintSignalResponse` instead of `model_config = ConfigDict(...)`. Emits deprecation warning but functions correctly. | LOW | No |
| 3 | `RegistryLoader` instantiated per-request in `/health` and `/signals/summary`. Reads `sources.json` from disk each time. Fine at current volume; consider `@lru_cache` or startup-event caching if these become hot paths. | LOW | No |
| 4 | `convergence_cells: 0` hardcoded in summary response. Acknowledged placeholder — sprint-3 integration task. | INFO | No |
| 5 | `ConvergenceScorer._cluster_signals` has a `bucket_seconds == 0` guard defaulting to 3600. Defensive but unreachable given `__init__` takes `int` and `timedelta(minutes=0).total_seconds()` = 0.0 would trigger it. Correct defensive coding. | INFO | No |
| 6 | Tests use direct function calls with mocked sessions rather than full HTTP TestClient. Tests verify business logic correctly but do not exercise FastAPI's query parameter parsing/validation layer. Acceptable for unit tests; integration tests in sprint-3 should cover the HTTP layer. | LOW | No |

---

## Files Audited

- `backend/api/osint_routes.py` — 3 GET endpoints (signals, health, summary)
- `backend/services/convergence_scorer.py` — ConvergenceScorer service
- `backend/tests/test_cycle025_sprint2.py` — 10 unit tests
- `backend/schemas/osint_schemas.py` — 4 response schemas
- `backend/database/models.py` — OsintSignal and Investigation model definitions (reference)
- `backend/osint/models/registry.py` — RegistryLoader class (reference)
- `backend/schemas/worldmonitor_api_contract.py` — WMDomain enum (reference)
- `backend/osint/models/evidence.py` — WMDomain re-export (reference)
- `backend/dependencies.py` — get_db dependency (reference)
