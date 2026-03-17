# Sprint Plan — Cycle-025: WorldMonitor Intelligence Contract v2

**Cycle:** cycle-025
**Date:** 16 March 2026
**Builder:** Loa
**Sprints:** 4 (0–3)

---

## Sprint 0 — Schema + Migration

**Goal:** Extend the WorldMonitor contract and create the signals table. No new routes yet — just the foundation.

### Tasks

1. **Extend MeasureType enum** in `backend/schemas/worldmonitor_api_contract.py`
   - Add 7 new values after `DARK_FLEET_PROBABILITY` (line 54)
   - Values: FORECAST_SCORE, FORECAST_WEIGHT, CORRIDOR_RISK, SHIPPING_RATE_INDEX, SUPPLY_CHAIN_SEVERITY, SANCTIONS_EXPOSURE, CROSS_DOMAIN_CONVERGENCE
   - Write 2 tests: all 14 values present, string serialisation roundtrip

2. **Add nullable fields to response schemas** in same file
   - CIIResponse: +3 fields (forecast_score, forecast_weight, sanctions_exposure)
   - MaritimeAnomalyResponse: +3 fields (corridor, corridor_risk, shipping_rate_index)
   - MarketSnapshotResponse: +1 field (supply_chain_severity)
   - Write 3 tests: backward compat (old payloads still parse), new fields serialize as null, new fields serialize with values

3. **Add OsintSignal model** to `backend/database/models.py`
   - All columns per SDD Section 2.3
   - Three composite indexes + content_hash index

4. **Create Alembic migration** `c025_osint_signals`
   - `upgrade()`: CREATE TABLE osint_signals
   - `downgrade()`: DROP TABLE osint_signals
   - Write 1 test: migration applies cleanly (upgrade + downgrade)

5. **Create response schemas** in new file `backend/schemas/osint_schemas.py`
   - OsintSignalResponse, PaginatedSignalsResponse, OsintHealthResponse, SignalSummaryResponse

**Exit:** 6 tests pass. `alembic upgrade head` succeeds. MeasureType has 14 values. `npm run build` passes.

---

## Sprint 1 — POST Endpoints + Signal Persistence

**Goal:** Promote the three POST stubs to live endpoints. All three write signals to the new table.

### Tasks

1. **Implement `persist_signal` helper** — shared function that creates an OsintSignal row from a CollectionResult
   - Computes content_hash via SHA-256 of normalised JSON
   - Deduplicates on content_hash (skip if exists)
   - Returns the signal row

2. **Implement `POST /intelligence/cii`** in `backend/api/world_monitor_routes.py`
   - Accept CIIRequest body
   - Call WorldMonitorCollector for INTELLIGENCE domain
   - Generate HTTPTranscriptReceipt
   - Persist signal
   - Return EvidenceBundle[CIIResponse] with new nullable fields populated where available
   - Write 3 tests: success, collector failure (returns 502), invalid request (returns 422)

3. **Implement `POST /market/snapshot`** — same pattern for MARKET domain
   - Write 3 tests

4. **Implement `POST /maritime/anomaly`** — same pattern for MARITIME domain
   - Write 3 tests

**Exit:** 9 tests pass. All three POST endpoints return 200. Signals persist to osint_signals table. `npm run build` passes.

---

## Sprint 2 — Read Endpoints + Convergence

**Goal:** Activate the signals query route, add health and summary endpoints, implement convergence scoring.

### Tasks

1. **Replace signals stub** at `GET /api/v1/osint/signals` in `backend/api/osint_routes.py`
   - Query osint_signals table with source_group, investigation_id, since filters
   - Pagination via limit/offset
   - Write 3 tests: unfiltered, source_group filter, investigation_id filter

2. **Add `GET /api/v1/osint/health`** in same file
   - Count active sources from RegistryLoader
   - Compute latency from latest signal timestamp
   - Count escalated investigations (use status heuristic if no escalated column)
   - Write 2 tests: all feeds healthy, degraded state (no recent signals)

3. **Add `GET /api/v1/osint/signals/summary`** in same file
   - Total signals, group by source_group, counter-signals, certificate candidates, convergence cells
   - Write 2 tests: empty state, populated state

4. **Implement ConvergenceScorer** in new file `backend/services/convergence_scorer.py`
   - Cluster signals by (geo_region, time_window)
   - Emit ConvergenceCell for clusters with 2+ domain source_groups
   - Score = domain_count / total_domains
   - Write 3 tests: single domain (no cell), two domains (cell emitted), empty input

**Exit:** 10 tests pass. All three read endpoints return data. Convergence scorer produces cells. `npm run build` passes.

---

## Sprint 3 — Integration + Regression

**Goal:** End-to-end integration. Path 2 regression. Final cleanup.

### Tasks

1. **Path 2 regression test**
   - Verify `GET /api/v1/world-monitor/live` still returns synthetic signals from SignalDetector/OSINTRegistry
   - Confirm no imports from `backend/core/signal_detector.py` or `backend/core/osint_registry.py` were added to any Cycle 025 file
   - Write 1 test: live endpoint response shape unchanged

2. **Integration sweep**
   - Verify POST endpoints persist signals that GET endpoints can retrieve
   - Verify convergence scorer correctly processes signals written by POST endpoints
   - Verify health endpoint reflects actual registry state
   - Write 2 integration tests

3. **Update REPO_MAP** in `grimoires/loa/context/` if present
   - Add ConvergenceScorer to services list
   - Add osint_signals table to database section
   - Add new routes to API section

4. **Final `npm run build` + full test run**

**Exit:** All ~29 tests pass. All endpoints return correct responses. Migration applies cleanly. `npm run build` passes.

---

## Sprint Summary

| Sprint | Focus | Tests |
|---|---|---|
| 0 | Schema + migration + response models | 6 |
| 1 | POST endpoints + signal persistence | 9 |
| 2 | Read endpoints + convergence scorer | 10 |
| 3 | Integration + Path 2 regression | 4 |
| **Total** | | **~29** |
