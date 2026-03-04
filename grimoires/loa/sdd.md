# SDD — Cycle-015: WorldMonitor Live Deployment + First Non-WM Collector

**Cycle:** cycle-015
**Date:** 4 March 2026
**PRD:** grimoires/loa/prd.md

---

## 1. Architecture Overview

Cycle-015 makes two changes to the OSINT pipeline:

```
Sprint 1 — Live path verification:

  WorldMonitorCollector (existing)
    → env var base URL config (ECHELON_WM_BASE_URL)
    → live pytest marker (@pytest.mark.live_wm)
    → parity tests (mock vs live structural equality)

Sprint 2 — Second collector + corroboration unlock:

  CompaniesHouseCollector (NEW, implements BaseCollector)
    → sources.json v0.4.0-wm-ch (4 sources)
    → CorroborationEngine (NO code changes — just data)
    → corroboration_minimum_met: true (WM + CH = 2 upstream groups)
    → scoring factor lifts 0.7 → 1.0
```

No new services, no new engines, no schema changes. The existing three-stage pipeline (collection → corroboration → scoring) processes the new collector transparently. The corroboration improvement is entirely data-driven — adding a source with a distinct `independence_upstream_id` is sufficient.

---

## 2. Sprint 1 — WM Live Path

### 2.1 Env Var Configuration

**File:** `backend/osint/collectors/worldmonitor.py`

Add `ECHELON_WM_BASE_URL` env var fallback to `WorldMonitorConfig`:

```python
@dataclass
class WorldMonitorConfig:
    base_url: str = ""  # Set in __post_init__
    timeout_s: float = 30.0
    version: str = "v0.1.0"
    retry_count: int = 2
    retry_delay_s: float = 1.0

    def __post_init__(self):
        if not self.base_url:
            self.base_url = os.environ.get(
                "ECHELON_WM_BASE_URL", "http://localhost:8080"
            )
```

Priority: constructor param > env var > default. Existing tests pass `base_url` explicitly via `wm_config` fixture, so this change is transparent.

### 2.2 Pytest Marker Registration

**File:** `backend/osint/tests/conftest.py`

Add marker registration and collection-time skip logic:

```python
def pytest_addoption(parser):
    parser.addoption("--live-wm", action="store_true", default=False,
                     help="Run live WorldMonitor tests")
    parser.addoption("--live-ch", action="store_true", default=False,
                     help="Run live Companies House tests")

def pytest_configure(config):
    config.addinivalue_line("markers", "live_wm: requires live WorldMonitor instance")
    config.addinivalue_line("markers", "live_ch: requires live Companies House API key")

def pytest_collection_modifyitems(config, items):
    skip_wm = not (config.getoption("--live-wm") or os.environ.get("ECHELON_LIVE_WM"))
    skip_ch = not (config.getoption("--live-ch") or os.environ.get("ECHELON_LIVE_CH"))
    for item in items:
        if "live_wm" in item.keywords and skip_wm:
            item.add_marker(pytest.mark.skip(reason="Need --live-wm or ECHELON_LIVE_WM=1"))
        if "live_ch" in item.keywords and skip_ch:
            item.add_marker(pytest.mark.skip(reason="Need --live-ch or ECHELON_LIVE_CH=1"))
```

### 2.3 Live WM Tests

**New file:** `backend/osint/tests/test_worldmonitor_live.py`

All tests decorated `@pytest.mark.live_wm`. Use `WorldMonitorCollector` with default config (reads `ECHELON_WM_BASE_URL`).

| Test | What It Verifies |
|------|-----------------|
| `test_live_health_check` | `GET /health` → HEALTHY or DEGRADED (UNAVAILABLE = fail) |
| `test_live_cii_collection` | POST `/api/v1/intelligence/cii` → valid `EvidenceBundle` |
| `test_live_market_collection` | POST `/api/v1/market/snapshot` → valid `EvidenceBundle` |
| `test_live_maritime_collection` | POST `/api/v1/maritime/anomaly` → valid `EvidenceBundle` |
| `test_live_hash_invariants` | `receipt.content_hash == SHA-256(raw_payload)` on live response |
| `test_live_receipt_structure` | `HTTPTranscriptReceipt` fields populated from real HTTP exchange |

Each test asserts:
- `result.success is True`
- `result.bundle is not None`
- `result.bundle.receipt is not None`
- `isinstance(result.bundle, EvidenceBundle)`

### 2.4 Mock-to-Live Parity Tests

**New file:** `backend/osint/tests/test_mock_live_parity.py`

All tests decorated `@pytest.mark.live_wm`. Run the same domain through both paths and assert structural equality:

```python
@pytest.mark.live_wm
async def test_cii_mock_live_parity(cii_response_bytes, wm_config):
    """Live and mock produce structurally identical EvidenceBundle."""
    # Mock path: patch _do_http_post to return fixture bytes
    mock_result = await mock_collector.fetch(request, theatre_id)

    # Live path: real HTTP
    live_collector = WorldMonitorCollector(WMDomain.INTELLIGENCE)
    live_result = await live_collector.fetch(request, theatre_id)

    # Structural parity (not value equality — data differs)
    assert type(mock_result.bundle) == type(live_result.bundle)
    assert set(vars(mock_result.bundle)) == set(vars(live_result.bundle))
    assert type(mock_result.bundle.receipt) == type(live_result.bundle.receipt)
    assert set(vars(mock_result.bundle.receipt)) == set(vars(live_result.bundle.receipt))
    assert type(mock_result.bundle.normalised_event) == type(live_result.bundle.normalised_event)
```

Three tests: one per WM domain (CII, Market, Maritime).

---

## 3. Sprint 2 — Companies House Collector

### 3.1 New Module: `backend/osint/collectors/companies_house.py`

Implements `BaseCollector` ABC. Uses stdlib HTTP (same pattern as WM). Profile endpoint only (`/company/{company_number}`).

```python
class CompaniesHouseCollector(BaseCollector):
    """UK Companies House API collector — profile lookup only.

    Auth: HTTP Basic (API key as username, blank password).
    API key from ECHELON_COMPANIES_HOUSE_API_KEY env var.
    """

    BASE_URL = "https://api.company-information.service.gov.uk"

    def __init__(self, api_key: str | None = None) -> None:
        self._api_key = api_key or os.environ.get("ECHELON_COMPANIES_HOUSE_API_KEY", "")

    def source_id(self) -> str:
        return "companies_house_api"

    async def _fetch(self, request: dict, theatre_id: str) -> CollectionResult:
        """GET /company/{company_number} with Basic auth."""
        ...

    async def health_check(self) -> HealthStatus:
        """GET /company/00000006 (test company) as health probe."""
        ...
```

**Key differences from legacy `osint_pipeline/` collector:**

| Aspect | Legacy (`osint_pipeline/`) | New (`backend/osint/`) |
|--------|---------------------------|------------------------|
| Base class | `osint_pipeline.collectors.base.BaseCollector` | `backend.osint.collectors.base.BaseCollector` |
| Interface | `build_request()` + `extract()` | `_fetch()` (template method) |
| Auth failure | Raises `ValueError` | Returns `CollectionResult(success=False)` |
| HTTP lib | Not shown (httpx implied) | stdlib `urllib.request` |
| Receipt | Not produced | `HTTPTranscriptReceipt` with hash invariants |
| Endpoint scope | 7 endpoints | Profile only (single endpoint) |
| `independence_upstream_id` | `gb_companies_house_register` | `uk_companies_house_backend` |

**Auth handling:**
- API key from `ECHELON_COMPANIES_HOUSE_API_KEY` env var
- HTTP Basic auth: `Authorization: Basic base64(api_key:)`
- If env var not set: `CollectionResult(success=False, error="No API key configured")` — does NOT raise

**Hash invariants:**
- `content_hash = SHA-256(raw_response_bytes)` — enforced by `BaseCollector.fetch()`
- `receipt_hash = compute_receipt_hash("GET", url, "", headers_str, content_hash)` — enforced by `BaseCollector.fetch()`

**Response parsing:**
- Parse JSON response
- Build `EvidenceBundle` with `NormalisedEvent` containing company status data
- Confidence: 1.0 (official government source)
- `source_group: "official_gov"`
- `resolution_role: "primary_evidence"`

### 3.2 Registry Update

**File:** `backend/osint/sources.json`

Bump version to `0.4.0-wm-ch`. Add Companies House entry:

```json
{
  "source_id": "companies_house_api",
  "source_name": "Companies House (UK)",
  "source_group": "official_gov",
  "priority_bucket": "scoring_grade",
  "resolution_role": "primary_evidence",
  "independence_upstream_id": "uk_companies_house_backend",
  "receipt_mode_minimum": "http_transcript",
  "world_monitor_domain": null,
  "settlement_eligible": true,
  "jurisdiction": "GB",
  "replayability": "strong",
  "legal_risk": "low",
  "cost_model": "free",
  "rate_limit_notes": "Free API key. Rate limit: 600 requests per 5 minutes.",
  "gap_policy_default": false,
  "evidence_capture": {
    "request_params": true,
    "response_headers": true,
    "payload_hash": true,
    "timestamp_precision": "second"
  },
  "theatre_families": ["OSINT_COMPOSED_ORACLE"],
  "collector_status": "active"
}
```

**Critical field:** `independence_upstream_id: "uk_companies_house_backend"` — distinct from WM's `"worldmonitor"`. This is the field that breaks the single-source corroboration trap.

### 3.3 Source Manifest Update

**File:** `backend/osint/source_manifest.py`

Update `_get_registry_version()` to read version from the loaded registry data rather than returning a hardcoded string. The existing `build()` method already handles the new source correctly — it will:
- Find CH in registry by `source_id`
- Assign `settlement_status: ELIGIBLE` (unique upstream ID + `settlement_eligible: true`)
- Include in manifest entries

### 3.4 Corroboration Engine — NO Code Changes

The existing `CorroborationEngine.evaluate()` already:
1. Groups bundles by `independence_upstream_id` (from registry lookup)
2. Deduplicates within each group (retains highest confidence)
3. Counts distinct groups against `corroboration_minimum` (default: 2)

With WM (`upstream: "worldmonitor"`) + CH (`upstream: "uk_companies_house_backend"`):
- 2 distinct upstream groups >= `corroboration_minimum` (2)
- `corroboration_met: true`
- Scoring factor: 1.0 (not 0.7)

No code changes. The improvement is purely data-driven.

### 3.5 Mock Fixture

**New file:** `backend/osint/tests/fixtures/ch_company_profile.json`

Mock response from Companies House API for company number `00000006` (test company):

```json
{
  "company_number": "00000006",
  "company_name": "MARINE AND GENERAL MUTUAL LIFE ASSURANCE SOCIETY",
  "company_status": "active",
  "type": "private-unlimited-nsc",
  "date_of_creation": "1862-10-25",
  "registered_office_address": {
    "address_line_1": "Cms Cameron Mckenna Llp Cannon Place",
    "address_line_2": "78 Cannon Street",
    "locality": "London",
    "postal_code": "EC4N 6AF"
  },
  "sic_codes": ["65110"],
  "has_insolvency_history": false,
  "has_charges": true
}
```

### 3.6 Test Files

**`backend/osint/tests/test_companies_house.py`** — Mock + live tests:

| Test | Marker | Asserts |
|------|--------|---------|
| `test_ch_collection_success` | — | Mock response → valid `EvidenceBundle`, `source_id == "companies_house_api"` |
| `test_ch_hash_invariants` | — | `content_hash == SHA-256(raw_payload)` on mock response |
| `test_ch_receipt_structure` | — | `HTTPTranscriptReceipt` fields populated (method=GET, url, content_hash) |
| `test_ch_no_api_key` | — | No env var → `CollectionResult(success=False)`, no raise |
| `test_ch_404_company` | — | Unknown company number → `success=False` |
| `test_live_ch_company_profile` | `live_ch` | Real API → valid `EvidenceBundle` |
| `test_live_ch_hash_invariants` | `live_ch` | Hash invariants on real response |

**`backend/osint/tests/test_corroboration_with_ch.py`** — Corroboration multi-source:

| Test | Asserts |
|------|---------|
| `test_wm_only_still_provisional` | 3 WM results → 1 upstream group → `corroboration_met: false` |
| `test_wm_plus_ch_meets_minimum` | 1 WM + 1 CH → 2 upstream groups → `corroboration_met: true` |
| `test_ch_only_insufficient` | 1 CH result alone → 1 group → `corroboration_met: false` |
| `test_corroboration_factor_lifts` | WM + CH → scoring composite uses 1.0 factor |

**`backend/osint/tests/test_e2e_corroboration.py`** — Full pipeline E2E:

| Test | Asserts |
|------|---------|
| `test_e2e_wm_ch_pipeline` | `CollectionRunner` → `CorroborationEngine` → `Scorer` with both WM and CH mocks. `corroboration_met: true`, factor 1.0, `p_reality` not penalised |

---

## 4. File Change Matrix

| File | Action | Sprint |
|------|--------|--------|
| `backend/osint/collectors/worldmonitor.py` | MODIFY — env var base URL | 1 |
| `backend/osint/tests/conftest.py` | MODIFY — add markers + skip logic | 1 |
| `backend/osint/tests/test_worldmonitor_live.py` | NEW — 6 live WM tests | 1 |
| `backend/osint/tests/test_mock_live_parity.py` | NEW — 3 parity tests | 1 |
| `backend/osint/collectors/companies_house.py` | NEW — CH collector | 2 |
| `backend/osint/sources.json` | MODIFY — add CH, bump v0.4.0-wm-ch | 2 |
| `backend/osint/source_manifest.py` | MODIFY — dynamic registry version | 2 |
| `backend/osint/tests/fixtures/ch_company_profile.json` | NEW — mock fixture | 2 |
| `backend/osint/tests/test_companies_house.py` | NEW — 5 mock + 2 live tests | 2 |
| `backend/osint/tests/test_corroboration_with_ch.py` | NEW — 4 corroboration tests | 2 |
| `backend/osint/tests/test_e2e_corroboration.py` | NEW — 1 E2E test | 2 |

---

## 5. Data Flow — Corroboration Unlock

### Before (Cycle-011):
```
WM CII    ─┐ upstream: "worldmonitor"
WM Market ─┤ upstream: "worldmonitor"  ──→ 1 group < 2 ──→ corroboration_met: false ──→ factor: 0.7
WM Maritime┘ upstream: "worldmonitor"
```

### After (Cycle-015):
```
WM CII    ─┐ upstream: "worldmonitor"
WM Market ─┤ upstream: "worldmonitor"
WM Maritime┘ upstream: "worldmonitor"     ──→ 2 groups >= 2 ──→ corroboration_met: true ──→ factor: 1.0
CH Profile ── upstream: "uk_companies_house_backend"
```

---

## 6. Security Considerations

- **API key storage:** `ECHELON_COMPANIES_HOUSE_API_KEY` env var only. Never committed to repo. Tests without key gracefully return `success=False`.
- **Auth header:** HTTP Basic over HTTPS only. Companies House API enforces HTTPS. `urllib.request` follows default SSL verification.
- **No credential caching:** API key read from env var on each collector instantiation. No in-memory persistence beyond the collector lifetime.

---

## 7. Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| WM local instance unstable | Live tests flaky | Tests gated behind opt-in marker; CI runs mock-only by default |
| CH API rate limit (600/5min) | Live tests blocked | Test uses single company lookup; rate limit unlikely with test volume |
| CH API response schema changes | Mock/live drift | Parity tests will catch structural mismatches |
| `source_manifest.py` hardcoded version | Stale after registry bump | Sprint 2 Task 6 fixes — read version from loaded registry |

---

## 8. Regression Target

**Baseline:** 932 passed, 4 skipped, 13 pre-existing collection errors
**Gate:** >=932 passed. Zero new failures.

Live tests: skipped by default (not counted in gate). When enabled:
- Sprint 1: +6 live WM + 3 parity = +9 (skipped without `--live-wm`)
- Sprint 2: +2 live CH = +2 (skipped without `--live-ch`)

Mock tests (always run):
- Sprint 2: +5 CH mock + 4 corroboration + 1 E2E = +10

**Post-015 expected:** >=942 passed (932 baseline + 10 new mock tests), 4 + 11 skipped (4 pre-existing + 9 live_wm + 2 live_ch)
