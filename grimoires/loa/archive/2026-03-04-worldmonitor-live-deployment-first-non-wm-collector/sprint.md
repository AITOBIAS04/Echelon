# Sprint Plan — Cycle-015: WorldMonitor Live Deployment + First Non-WM Collector

**Cycle:** cycle-015
**Date:** 4 March 2026
**PRD:** grimoires/loa/prd.md
**SDD:** grimoires/loa/sdd.md
**Sprints:** 2
**Baseline:** 932 passed, 4 skipped, 13 pre-existing collection errors

---

## Sprint 1 — WorldMonitor Live Tests ✅

**Global ID:** 31
**Tasks:** 4
**Focus:** Env var config, pytest markers, live tests, mock-to-live parity verification
**Prerequisite:** P0 — WM instance reachable at configured base URL, `GET /health` returns not UNAVAILABLE

### Task 1: Pytest Marker Registration + Skip Logic

**Files:** `backend/osint/tests/conftest.py` (MODIFY)
**Acceptance:**
- `pytest_addoption()` adds `--live-wm` and `--live-ch` flags
- `pytest_configure()` registers `live_wm` and `live_ch` markers
- `pytest_collection_modifyitems()` skips `live_wm` tests unless `--live-wm` flag or `ECHELON_LIVE_WM=1` env var set
- Same pattern for `live_ch` / `ECHELON_LIVE_CH`
- Existing fixtures and conftest content unchanged
- Running `pytest backend/osint/` without flags: zero new failures, live tests skipped

### Task 2: WM Base URL Env Var Configuration

**File:** `backend/osint/collectors/worldmonitor.py` (MODIFY)
**Acceptance:**
- `WorldMonitorConfig.__post_init__()` reads `ECHELON_WM_BASE_URL` env var when `base_url` is empty string
- Priority: constructor param > env var > default (`http://localhost:8080`)
- Existing tests pass `base_url` explicitly via fixture — zero regressions
- `WorldMonitorConfig(base_url="http://custom:9090")` uses constructor value, ignores env var
- `WorldMonitorConfig()` with `ECHELON_WM_BASE_URL=http://remote:8080` uses env var
- `WorldMonitorConfig()` without env var uses `http://localhost:8080`

### Task 3: Live WM Tests

**File:** `backend/osint/tests/test_worldmonitor_live.py` (NEW)
**Acceptance:**
- All 6 tests decorated `@pytest.mark.live_wm`
- `test_live_health_check`: `GET /health` → HEALTHY or DEGRADED (UNAVAILABLE = fail)
- `test_live_cii_collection`: POST `/api/v1/intelligence/cii` → valid `EvidenceBundle` with `result.success is True`
- `test_live_market_collection`: POST `/api/v1/market/snapshot` → valid `EvidenceBundle`
- `test_live_maritime_collection`: POST `/api/v1/maritime/anomaly` → valid `EvidenceBundle`
- `test_live_hash_invariants`: `receipt.content_hash == SHA-256(raw_payload)` on live response
- `test_live_receipt_structure`: `HTTPTranscriptReceipt` fields populated (method, url, content_hash, receipt_hash all non-empty)
- All tests use `WorldMonitorCollector` with default config (reads `ECHELON_WM_BASE_URL`)
- Tests skipped by default — require `--live-wm` or `ECHELON_LIVE_WM=1`

### Task 4: Mock-to-Live Parity Verification

**File:** `backend/osint/tests/test_mock_live_parity.py` (NEW)
**Acceptance:**
- All 3 tests decorated `@pytest.mark.live_wm`
- `test_cii_mock_live_parity`: run CII domain through both mock and live paths, assert structural equality
- `test_market_mock_live_parity`: same for Market domain
- `test_maritime_mock_live_parity`: same for Maritime domain
- Structural equality means: same Python types returned, same field set on `EvidenceBundle`, same receipt type and field set
- Does NOT assert value equality (live data values differ from mock fixtures)
- Hash computation method identical (SHA-256 of raw bytes)
- Tests skipped by default — require `--live-wm` or `ECHELON_LIVE_WM=1`

---

## Sprint 2 — Companies House Collector Integration ✅

**Global ID:** 32
**Tasks:** 7
**Focus:** Port CH collector, update registry, verify corroboration unlock, E2E pipeline

### Task 1: Port Companies House Collector

**File:** `backend/osint/collectors/companies_house.py` (NEW)
**Acceptance:**
- `CompaniesHouseCollector` extends `BaseCollector` from `backend/osint/collectors/base.py`
- Implements `source_id() -> "companies_house_api"`
- Implements `_fetch(request, theatre_id) -> CollectionResult` — GET `/company/{company_number}` with HTTP Basic auth
- Implements `health_check() -> HealthStatus` — GET `/company/00000006` as probe
- Auth: `ECHELON_COMPANIES_HOUSE_API_KEY` env var, HTTP Basic (key as username, blank password)
- No API key → `CollectionResult(success=False, error="No API key configured")`, does NOT raise
- Uses stdlib `urllib.request` (same pattern as WM collector)
- Produces `HTTPTranscriptReceipt` with hash invariants enforced by `BaseCollector.fetch()`
- Response parsed to `EvidenceBundle` with `NormalisedEvent`, confidence 1.0
- Profile endpoint only (`/company/{company_number}`) — other endpoints deferred to Cycle-017

### Task 2: Update Runtime Registry

**File:** `backend/osint/sources.json` (MODIFY)
**Acceptance:**
- Version bumped to `0.4.0-wm-ch`
- Companies House entry added with all required fields (see SDD §3.2)
- `source_id: "companies_house_api"`
- `independence_upstream_id: "uk_companies_house_backend"` — distinct from `"worldmonitor"`
- `settlement_eligible: true`
- `jurisdiction: "GB"`
- `world_monitor_domain: null`
- `collector_status: "active"`
- Existing 3 WM entries unchanged
- Total sources: 4

### Task 3: Mock Fixtures

**File:** `backend/osint/tests/fixtures/ch_company_profile.json` (NEW)
**Acceptance:**
- Valid JSON matching Companies House API response schema for company `00000006`
- Contains: `company_number`, `company_name`, `company_status`, `type`, `date_of_creation`, `registered_office_address`, `sic_codes`
- Used by mock tests — no API key required
- Structurally representative of real API response

### Task 4: Companies House Tests (Mock + Live)

**File:** `backend/osint/tests/test_companies_house.py` (NEW)
**Acceptance:**
- 5 mock tests (always run):
  - `test_ch_collection_success`: mock response → valid `EvidenceBundle`, `source_id == "companies_house_api"`
  - `test_ch_hash_invariants`: `content_hash == SHA-256(raw_payload)` on mock response
  - `test_ch_receipt_structure`: `HTTPTranscriptReceipt` fields populated (method=GET, url, content_hash)
  - `test_ch_no_api_key`: no env var → `CollectionResult(success=False)`, no exception raised
  - `test_ch_404_company`: unknown company number → `success=False`
- 2 live tests (decorated `@pytest.mark.live_ch`):
  - `test_live_ch_company_profile`: real API → valid `EvidenceBundle`
  - `test_live_ch_hash_invariants`: hash invariants on real response
- Live tests skipped by default — require `--live-ch` or `ECHELON_LIVE_CH=1`

### Task 5: Corroboration Engine Multi-Source Verification

**File:** `backend/osint/tests/test_corroboration_with_ch.py` (NEW)
**Acceptance:**
- `test_wm_only_still_provisional`: 3 WM results → 1 upstream group → `corroboration_met: false`
- `test_wm_plus_ch_meets_minimum`: 1 WM + 1 CH → 2 upstream groups → `corroboration_met: true`
- `test_ch_only_insufficient`: 1 CH result alone → 1 group → `corroboration_met: false`
- `test_corroboration_factor_lifts`: WM + CH → scoring composite uses 1.0 factor (not 0.7)
- No changes to `backend/osint/engine/corroboration.py` — tests verify existing engine with new data
- Tests use mock `EvidenceBundle` instances with appropriate `independence_upstream_id` values

### Task 6: Source Manifest Update

**File:** `backend/osint/source_manifest.py` (MODIFY)
**Acceptance:**
- `_get_registry_version()` reads version from loaded registry data instead of returning hardcoded `"0.3.2-wm"`
- `build()` picks up CH source with `settlement_status: ELIGIBLE`
- Manifest includes 4 sources total (3 WM + 1 CH)
- Existing manifest tests pass unchanged

### Task 7: E2E Pipeline Test with Corroboration

**File:** `backend/osint/tests/test_e2e_corroboration.py` (NEW)
**Acceptance:**
- `test_e2e_wm_ch_pipeline`: full pipeline with both WM (mock) + CH (mock) sources
  - `CollectionRunner.collect()` with oracle config including both source groups
  - `CorroborationEngine.evaluate()` → `corroboration_minimum_met: true`
  - `Scorer.compute_composite()` → corroboration factor is 1.0 (not 0.7)
  - `p_reality` not penalised by corroboration
- Uses mock responses for both WM and CH — no live API calls
- Verifies the complete data path: collection → corroboration → scoring

---

## File Change Matrix

| File | Action | Sprint | Task |
|------|--------|--------|------|
| `backend/osint/tests/conftest.py` | MODIFY | 1 | 1 |
| `backend/osint/collectors/worldmonitor.py` | MODIFY | 1 | 2 |
| `backend/osint/tests/test_worldmonitor_live.py` | NEW | 1 | 3 |
| `backend/osint/tests/test_mock_live_parity.py` | NEW | 1 | 4 |
| `backend/osint/collectors/companies_house.py` | NEW | 2 | 1 |
| `backend/osint/sources.json` | MODIFY | 2 | 2 |
| `backend/osint/tests/fixtures/ch_company_profile.json` | NEW | 2 | 3 |
| `backend/osint/tests/test_companies_house.py` | NEW | 2 | 4 |
| `backend/osint/tests/test_corroboration_with_ch.py` | NEW | 2 | 5 |
| `backend/osint/source_manifest.py` | MODIFY | 2 | 6 |
| `backend/osint/tests/test_e2e_corroboration.py` | NEW | 2 | 7 |

## Gate Rule

**Baseline:** 932 passed, 4 skipped, 13 pre-existing collection errors
**Gate:** >=932 passed. Zero new failures. All live tests skipped by default.

**Post-015 expected:** >=942 passed (932 + 10 new mock tests), 15 skipped (4 pre-existing + 9 live_wm + 2 live_ch)

## Sprint Registry

| Sprint | Local ID | Global ID | Tasks |
|--------|----------|-----------|-------|
| Sprint 1 | sprint-1 | 31 | 4 |
| Sprint 2 | sprint-2 | 32 | 7 |
