# Engineer Feedback — Sprint 83 (cycle-025/sprint-2)

**Reviewer:** Senior Technical Lead
**Decision:** All good
**Date:** 2026-03-17

---

## Task Verification

| # | Task | Status | Notes |
|---|------|--------|-------|
| 1 | `GET /api/v1/osint/signals` — replace stub | PASS | Queries `osint_signals` with `source_group`, `investigation_id`, `since` filters. Pagination via `limit`/`offset` with correct bounds (`ge=1, le=200` / `ge=0`). Ordered by `collected_at DESC`. 3 tests. |
| 2 | `GET /api/v1/osint/health` | PASS | Loads `RegistryLoader` for `feeds_total`, queries distinct `source_id` in last hour for `feeds_online`, computes `signal_latency_sec` from latest signal, counts ACTIVE investigations for `escalation_queue_depth`. 2 tests (healthy + degraded). |
| 3 | `GET /api/v1/osint/signals/summary` | PASS | Aggregates `total_signals`, groups by `source_group`, counts counter-signals by cross-referencing registry `resolution_role`, counts `CERTIFICATE_READY` investigations. `convergence_cells` placeholder at 0 — intentional for sprint-3 wiring. 2 tests (empty + populated). |
| 4 | `ConvergenceScorer` | PASS | Clusters by `(geo_region, time_bucket)` where `time_bucket = epoch_seconds // window_seconds`. Emits `ConvergenceCell` for 2+ domain clusters. Score = `domain_count / total_domains` with `total_domains` derived from `WMDomain` enum (3). 3 tests (single domain, two domains, empty). |

**Test count:** 10/10 (matches sprint plan exit criteria)

---

## Architecture Alignment

- **Path 2 isolation confirmed:** Zero imports from `backend/core/signal_detector.py` or `backend/core/osint_registry.py` in any sprint-2 file.
- **OsintSignal model usage:** All queries correctly reference columns defined in the model (source_group, investigation_id, collected_at, source_id, geo_region). The composite indexes (`ix_osint_signals_source_group_collected`, `ix_osint_signals_investigation_collected`) align with the query patterns.
- **RegistryLoader integration:** Correctly accesses `loader.sources` (dict keyed by source_id) and `source.resolution_role` for counter-signal identification.
- **Investigation model:** Status field queried as string (`"ACTIVE"`, `"CERTIFICATE_READY"`) matching the model's comment constraint.
- **Schemas:** All four response schemas (`OsintSignalResponse`, `PaginatedSignalsResponse`, `OsintHealthResponse`, `SignalSummaryResponse`) correctly match the endpoint return types.

---

## Non-Blocking Observations

1. **`datetime.utcnow()` deprecation** — Both `osint_routes.py` (line 73, 87) and the test helper use `datetime.utcnow()`, deprecated since Python 3.12 in favor of `datetime.now(datetime.UTC)`. Consistent with existing codebase patterns. No action needed this cycle.

2. **Pydantic v2 `class Config` style** — `OsintSignalResponse` uses `class Config: from_attributes = True` rather than `model_config = ConfigDict(from_attributes=True)`. Works correctly but emits a deprecation warning. Non-blocking.

3. **RegistryLoader instantiated per request** — Both `/health` and `/signals/summary` construct a new `RegistryLoader` on each call, reading `sources.json` from disk each time. For the current request volume this is fine. If these endpoints become hot paths, consider caching the loader instance (e.g., `@lru_cache` or FastAPI startup event).

4. **`convergence_cells: 0` placeholder** — The summary endpoint hardcodes this. Acknowledged as intentional; sprint-3 integration will wire the scorer output into the summary response.

5. **ConvergenceScorer import chain** — `ConvergenceScorer` imports `WMDomain` from `backend.osint.models.evidence` which re-exports from `backend.schemas.worldmonitor_api_contract`. Valid but adds one hop of indirection. Not a problem.

6. **Test isolation** — Tests use direct function calls with mocked sessions rather than `httpx.AsyncClient` / `TestClient`. This tests the route logic correctly but does not exercise FastAPI's dependency injection or query parameter parsing. Sprint-3 integration tests should cover the full HTTP layer.
