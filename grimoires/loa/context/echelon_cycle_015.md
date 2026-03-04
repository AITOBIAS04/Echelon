# Cycle-015: WorldMonitor Live Deployment + First Non-WM Collector

**Date:** 4 March 2026
**Depends on:** Cycle-011 (WM pipeline, mock-only), Cycle-014 (bounded inquiry taxonomy)
**Sprints:** 2
**Scope:** Mock-to-live WM transition + Companies House collector integration

---

## Why This Cycle Exists

Cycle-011 built the full three-stage OSINT pipeline (collection → corroboration → scoring) but everything runs against mock fixtures. No live HTTP calls, no real evidence, no independent corroboration. The corroboration engine always returns `PROVISIONAL` (0.7 penalty) because all three WM sources share the same `independence_upstream_id: "worldmonitor"`.

This cycle does two things:
1. **Sprint 1:** Deploy WorldMonitor locally, flip tests to live, verify the mock-to-live code path is identical
2. **Sprint 2:** Add Companies House as the first non-WM collector, breaking the single-source corroboration limitation

After this cycle: `WM + Companies House = 2 distinct upstream groups ≥ corroboration_minimum (2) → corroboration_minimum_met: true` for UK corporate Theatres. The 0.7 penalty lifts to 1.0.

---

## Current State

### Three-Stage Pipeline (`backend/osint/`)

**Stage 1 — Collection** (`engine/collection_runner.py`):
- `CollectionRunner.build_plan()` → `CollectionRunner.collect()`
- Returns `CollectionResult` per source (bundle, raw payload, content hash, receipt hash)
- Hash invariants enforced at `BaseCollector.fetch()`:
  - `receipt.content_hash == SHA-256(raw_payload)` (exact response bytes)
  - `receipt.receipt_hash == compute_receipt_hash(method, url, query, headers, body_hash)`

**Stage 2 — Corroboration** (`engine/corroboration.py`):
- Deduplicates by `independence_upstream_id` (keeps highest confidence)
- Counts distinct upstream groups
- Compares against `corroboration_minimum` (default: 2)
- Current state: all 3 WM sources collapse to 1 group → always `PROVISIONAL`

**Stage 3 — Scoring** (`engine/scorer.py`):
- `composite = weighted_mean × corroboration_factor × counter_signal_factor × evidence_completeness`
- Corroboration factor: 1.0 if met, 0.7 if not
- Counter-signal factor: 1.0 if pass, 0.5 if fail (all UNAVAILABLE in 011, passes with `allow_gap=True`)

### WorldMonitor Collector (`collectors/worldmonitor.py`)

Three domain endpoints:
- `/api/v1/intelligence/cii` — Composite Intelligence Index
- `/api/v1/market/snapshot` — Market data snapshot
- `/api/v1/maritime/anomaly` — Maritime anomaly detection

Health check: `GET /health` → `HEALTHY | DEGRADED | UNAVAILABLE`

All tests use JSON fixtures from `backend/osint/tests/fixtures/`. No `@pytest.mark.live_wm` decorator exists yet.

### Companies House Collector (pre-implemented in `osint_pipeline/`)

**File:** `osint_pipeline/collectors/companies_house.py`
**Tests:** `tests/osint_pipeline/test_companies_house.py`
**Registry entry:** v0.6.0 registry (`osint_pipeline/models/registry.py`)

```
source_id: "companies_house_api"
source_group: "official_gov"
independence_upstream_id: "uk_companies_house_backend"
jurisdiction: "GB"
resolution_role: "primary_evidence"
settlement_eligible: true
receipt_mode_minimum: "http_transcript"
```

Endpoints: `/company/{number}`, `/company/{number}/filing-history`, `/company/{number}/officers`, `/company/{number}/persons-with-significant-control`, `/company/{number}/charges`, `/company/{number}/insolvency`, `/search/companies`

Auth: HTTP Basic (API key as username, blank password). Free registration.

**NOT yet wired** to `backend/osint/` pipeline. Lives in the standalone `osint_pipeline/` package from Cycles 002-006.

### Runtime Registry (`backend/osint/sources.json`)

Version 0.3.2-wm. Three sources only. All share `independence_upstream_id: "worldmonitor"`. None are settlement-eligible.

**Registry lineage note:** Two registries coexist with different scopes:
- **Runtime registry** (`backend/osint/sources.json`) — v0.3.2-wm, 3 WM sources. This is what the pipeline loads. Sprint 2 bumps it to v0.4.0-wm-ch (4 sources).
- **Intelligence DB / archive registry** (Obsidian `implement/`) — v0.6.0 (77 sources) and v1.0.0 target (160+ sources). These are planning/reference documents, not loaded at runtime. The broader source catalogue is deferred to Cycle-017.

For this cycle, only the runtime registry matters. Reference docs use higher version numbers because they track the full catalogue, not the runtime subset.

### Paradox Wiring

`LiveOSINTRealityProvider` implements `RealitySignalProvider` interface (from 010b). Runs the full pipeline, returns `RealitySignal(p_reality=composite_score)`. Staleness protection: if `scored_at > max_staleness_s` (300s), `p_reality = None` and Paradox Engine skips scan.

### Counter-Signals (scaffolding only)

11 classes defined, all return `UNAVAILABLE` with `allow_gap=True`. Not addressed in this cycle.

### Convergence Detection

Geographic binning (1° × 1° cells), alerts when ≥3 source groups converge within 24h window. In-process logging only, no persistence. Not addressed in this cycle.

---

## Sprint 1: WorldMonitor Live Deployment

### Task 1.1: WM local deployment setup

Document the WM deployment process. This is NOT a code task — it's operational:
1. Clone `AITOBIAS04/worldmonitor` fork
2. Document local deployment steps (docker-compose or direct run)
3. Verify `GET /health` returns per-domain status
4. Record the base URL (expected: `http://localhost:8080`)

**Deliverable:** A `WM_LOCAL_SETUP.md` in `grimoires/loa/context/` or `docs/` with reproducible setup steps.

### Task 1.2: Add `@pytest.mark.live_wm` marker

**File:** `backend/osint/tests/conftest.py`

Register a `live_wm` pytest marker. Tests decorated with `@pytest.mark.live_wm` are skipped by default and only run when `--live-wm` flag is passed or `ECHELON_LIVE_WM=1` env var is set.

```python
def pytest_addoption(parser):
    parser.addoption("--live-wm", action="store_true", default=False, help="Run live WorldMonitor tests")

def pytest_configure(config):
    config.addinivalue_line("markers", "live_wm: requires live WorldMonitor instance")

def pytest_collection_modifyitems(config, items):
    if not config.getoption("--live-wm") and not os.environ.get("ECHELON_LIVE_WM"):
        skip_live = pytest.mark.skip(reason="Need --live-wm flag or ECHELON_LIVE_WM=1")
        for item in items:
            if "live_wm" in item.keywords:
                item.add_marker(skip_live)
```

### Task 1.3: Live WM tests

**New file:** `backend/osint/tests/test_worldmonitor_live.py`

All tests decorated with `@pytest.mark.live_wm`. Mirror the existing mock tests but hit the real endpoint:

1. `test_live_cii_collection` — collect from `/api/v1/intelligence/cii` → assert valid `EvidenceBundle` with real `content_hash`
2. `test_live_market_collection` — same for market domain
3. `test_live_maritime_collection` — same for maritime domain
4. `test_live_health_check` — `GET /health` → assert `HEALTHY` or `DEGRADED` (local WM may run with partial domain coverage; `UNAVAILABLE` is the only failure)
5. `test_live_hash_invariants` — verify `receipt.content_hash == SHA-256(raw_payload)` on live response
6. `test_live_receipt_structure` — verify `HTTPTranscriptReceipt` fields populated from real HTTP exchange

**Critical constraint:** These tests must verify that the live code path produces structurally identical output to the mock path. Same `EvidenceBundle` shape, same hash invariant, same receipt structure. The only difference is the actual data values.

### Task 1.4: WM base URL configuration

**File:** `backend/osint/collectors/worldmonitor.py`

Currently the base URL is likely hardcoded or in a config. Ensure it's configurable via:
- Constructor parameter: `WorldMonitorCollector(base_url="http://localhost:8080")`
- Environment variable fallback: `ECHELON_WM_BASE_URL`
- Default: `http://localhost:8080`

### Task 1.5: Mock-to-live parity verification

**New test:** `test_mock_live_parity.py` (decorated `@pytest.mark.live_wm`)

Collect from the same domain using both mock fixtures and live endpoint. Assert:
- Same Python types returned
- Same field set on `EvidenceBundle`
- Same hash computation method (SHA-256 of raw bytes)
- Receipt structure matches

This is the formal verification that the mock-to-live transition is seamless.

---

## Sprint 2: Companies House Collector Integration

### Task 2.1: Port Companies House collector to `backend/osint/`

**From:** `osint_pipeline/collectors/companies_house.py`
**To:** `backend/osint/collectors/companies_house.py`

Port the existing collector to the Cycle-011 `BaseCollector` interface. Must implement:
- `async def _fetch(self, request: dict, theatre_id: str) -> CollectionResult` (override the template method; `BaseCollector.fetch()` is the public entry point and handles hash invariant enforcement)
- `HTTPTranscriptReceipt` generation from the real HTTP exchange

Auth: Read API key from `ECHELON_COMPANIES_HOUSE_API_KEY` env var. If not set, collector returns `CollectionResult(success=False, error="No API key configured")`.

The default endpoint is `/company/{company_number}` (profile lookup). Additional endpoints (filing-history, officers, PSC, charges, insolvency) are available but only wire the profile endpoint for now. Others can be added in 017.

### Task 2.2: Update runtime registry

**File:** `backend/osint/sources.json`

Add Companies House to the registry. Bump version to `0.4.0-wm-ch`:

```json
{
  "source_id": "companies_house_api",
  "source_group": "official_gov",
  "independence_upstream_id": "uk_companies_house_backend",
  "jurisdiction": "GB",
  "resolution_role": "primary_evidence",
  "settlement_eligible": true,
  "receipt_mode_minimum": "http_transcript",
  "display_name": "Companies House (UK)",
  "world_monitor_domain": null
}
```

**Key field:** `independence_upstream_id: "uk_companies_house_backend"` — distinct from `"worldmonitor"`. This is what breaks the single-source corroboration limitation.

### Task 2.3: Corroboration engine verification

**File:** `backend/osint/engine/corroboration.py` — should require NO code changes.

The corroboration engine already deduplicates by `independence_upstream_id` and counts distinct groups. Adding a source with a different upstream ID should automatically produce `corroboration_minimum_met: true` when both WM and Companies House return results.

**Test:** `test_corroboration_with_companies_house.py`
1. `test_wm_only_still_provisional` — 3 WM results → 1 upstream group → `corroboration_minimum_met: false`
2. `test_wm_plus_ch_meets_minimum` — 1 WM result + 1 CH result → 2 upstream groups → `corroboration_minimum_met: true`
3. `test_ch_only_insufficient` — 1 CH result alone → 1 upstream group → `corroboration_minimum_met: false`
4. `test_corroboration_factor_lifts` — with WM+CH, scoring composite uses 1.0 factor instead of 0.7

### Task 2.4: Companies House mock fixtures

**New file:** `backend/osint/tests/fixtures/ch_company_profile.json`

Mock response from Companies House API for a known UK company (e.g. company number `00000006` — a test company). Used for non-live tests.

### Task 2.5: Companies House tests (mock + live)

**New file:** `backend/osint/tests/test_companies_house.py`

Mock tests (always run):
1. `test_ch_collection_success` — mock response → valid `EvidenceBundle`
2. `test_ch_hash_invariants` — `content_hash == SHA-256(raw_payload)`
3. `test_ch_receipt_structure` — `HTTPTranscriptReceipt` populated correctly
4. `test_ch_no_api_key` — no env var → graceful failure with error message
5. `test_ch_404_company` — unknown company number → `success=False`

Live tests (decorated `@pytest.mark.live_ch`, same pattern as `live_wm`):
6. `test_live_ch_company_profile` — hit real API → valid bundle
7. `test_live_ch_hash_invariants` — verify on real response

Add `live_ch` marker alongside `live_wm` in conftest.

### Task 2.6: Source manifest update

**File:** `backend/osint/source_manifest.py`

Verify that `build_manifest()` correctly picks up the new Companies House source and assigns `settlement_status: ELIGIBLE` (since it has a unique upstream ID and `settlement_eligible: true`).

### Task 2.7: E2E pipeline test with corroboration

**New test:** `test_e2e_corroboration.py`

Full pipeline run with both WM (mock) and Companies House (mock) sources:
1. `CollectionRunner.collect()` with an oracle config that includes both source groups
2. `CorroborationEngine.evaluate()` → assert `corroboration_minimum_met: true`
3. `Scorer.compute_composite()` → assert corroboration factor is 1.0 (not 0.7)
4. Full `LiveOSINTRealityProvider.get_signal()` → assert `p_reality` is not penalised

---

## Gate Rule

≥932 passed (current baseline), 4 skipped, 13 pre-existing (same node IDs). Zero new failures. All new WM live tests skipped by default (require `--live-wm` flag). All new CH mock tests pass. Existing OSINT pipeline tests unchanged.

---

## What This Unlocks

- **Real evidence flowing into Theatres** — first time the pipeline processes live HTTP responses, not fixtures
- **Independent corroboration** — WM + Companies House produces genuine multi-source corroboration for UK corporate Theatres
- **Settlement-eligible evidence** — Companies House is `settlement_eligible: true`, meaning its evidence can drive resolution
- **Foundation for 017 (Registry Expansion)** — proves the pattern for adding non-WM collectors. Next candidates: SEC EDGAR, UK Gazette, Bank of England
- **Confidence in mock fidelity** — formal parity tests prove the mocks accurately represent live behaviour

---

## Out of Scope

- Counter-signal wiring (future cycle — needs independent counter-signal sources)
- Convergence persistence (future cycle — needs database layer)
- Additional Companies House endpoints beyond profile (017)
- Other non-WM collectors beyond Companies House (017)
- WM production deployment (this cycle is local only)
- Consumption surface count reconciliation (Intelligence DB says 7 surfaces; research notes reference an 8th `deployability_routing` surface — reconcile during 017 schema additions, not here)
