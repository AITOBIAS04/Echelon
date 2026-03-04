# SDD: OSINT Pipeline — Live Collection & Evidence Bundles (Cycle-035)

> **Version:** 1.0
> **Date:** 2026-03-01
> **Status:** DRAFT
> **Depends on:** PRD Cycle-035 v1.0, Cycle-034 deliverables
> **Source files reviewed:**
> - `theatre/engine/canonical_json.py` (63 lines, RFC 8785)
> - `backend/schemas/worldmonitor_api_contract.py` (Pydantic v2 API contract)
> - `theatre/fixtures/two_rail_theatres_v0_1/datasets/echelon_osint_source_registry_v0_4_0.json` (57 sources, 2726 lines)
> - `tests/theatre/test_canonical_json.py` (37 tests, 5 classes)
> - Skeleton files from `~/Downloads/osint_pipeline/` (13 files)

---

## 1. Architecture Overview

### 1.1 Three-Stage Pipeline

The OSINT Pipeline implements a stateless three-stage Composed Oracle:

```
Stage 1: Collection        Stage 2: Corroboration       Stage 3: Scoring
+-------------------+     +----------------------+     +------------------+
| CollectionRunner   | --> | CorroborationEngine  | --> | Scorer           |
|   ThreadPool(5)    |     |   Dedup by upstream  |     |   Per-criterion  |
|   Per-source fetch |     |   Window validation  |     |   Weighted score |
|   Receipt gen      |     | CounterSignalChecker |     |   Bundle hash    |
|   Gap reporting    |     |   11 signal classes  |     |   OracleOutput   |
+-------------------+     +----------------------+     +------------------+
```

**Input:** Theatre oracle configuration + query context (entity identifiers, time windows).

**Output:** `OracleOutput` — a JSON artefact containing all evidence bundles, corroboration results, counter-signal evaluations, per-criterion scores, and a SHA-256 bundle hash suitable for inclusion in calibration certificates.

### 1.2 Package Placement

The `osint_pipeline/` package is placed at the monorepo root, as a sibling to `backend/`, `frontend/`, and `theatre/`:

```
prediction-market-monorepo/
+-- backend/
+-- frontend/
+-- theatre/
|   +-- engine/
|   |   +-- canonical_json.py       <-- Single source of truth for RFC 8785
|   +-- fixtures/
|       +-- two_rail_theatres_v0_1/
|           +-- datasets/
|               +-- echelon_osint_source_registry_v0_4_0.json
+-- osint_pipeline/                  <-- NEW (Cycle-035)
|   +-- __init__.py
|   +-- models/
|   +-- engine/
|   +-- collectors/
|   +-- cli.py
|   +-- config.py
+-- tests/
|   +-- theatre/                     <-- Existing (37 tests preserved)
|   +-- osint_pipeline/              <-- NEW (Cycle-035)
+-- pyproject.toml                   <-- pythonpath = ["."]
```

### 1.3 Stateless Design

The pipeline has no database dependency. All inputs are JSON files (registry, theatre configuration) or HTTP responses. All outputs are JSON artefacts (`OracleOutput`, evidence bundles). This simplifies deployment, testing, and reproducibility.

### 1.4 Dependency Summary

| Dependency | Version | Purpose |
|-----------|---------|---------|
| pydantic | v2.x | All data models (BaseModel, Field, field_validator) |
| httpx | latest | HTTP client for all collectors |
| Python stdlib | 3.11+ | `concurrent.futures.ThreadPoolExecutor`, `hashlib`, `json`, `time` |

No additional third-party libraries are required for the core pipeline. The CLI uses `argparse` (stdlib).

---

## 2. Component Design

### 2.1 Models Layer (`osint_pipeline/models/`)

All models use Pydantic v2 throughout. No Pydantic v1 patterns (`validator`, `Config` class).

#### 2.1.1 `models/evidence.py`

**Enumerations:**

| Enum | Values | Purpose |
|------|--------|---------|
| `ReceiptMode` | `none`, `http_transcript`, `cryptographic_transcript`, `signed_receipt`, `witness_quorum` | Receipt strength level. Pipeline always uses `http_transcript`. |
| `CollectionStatus` | `success`, `timeout`, `auth_failure`, `rate_limited`, `source_error`, `network_error`, `not_found`, `stale` | Outcome of a single collection attempt. |
| `FreshnessState` | `fresh`, `stale`, `no_data`, `error` | Data freshness classification. |

**Models:**

| Model | Key Fields | Notes |
|-------|-----------|-------|
| `HTTPTranscriptReceipt` | `method`, `url`, `request_headers`, `response_status`, `response_body_hash`, `timestamp_ms`, `receipt_hash` | 6-field canonical form. Field validators enforce 64-char lowercase hex for hash fields. |
| `EvidenceBundle` | `bundle_id` (UUID v4), `source_id`, `source_group`, `independence_upstream_id`, `resolution_role`, `jurisdiction`, `raw_payload_hash`, `raw_payload_size_bytes`, `receipt`, `receipt_mode`, `structured_extract`, `confidence_score`, `freshness`, `retrieved_at`, `theatre_id`, `query_context` | Immutable artefact. `confidence_score` is `[0.0, 1.0]`. |
| `CollectionResult` | `source_id`, `status`, `bundle` (optional), `error_message` (optional), `duration_ms`, `attempted_at` | `.succeeded` property checks `status == SUCCESS and bundle is not None`. |
| `GapReport` | `source_id`, `source_group`, `jurisdiction`, `reason` (CollectionStatus), `error_detail`, `allow_gap`, `freshness` | "Show what you cannot see." |
| `OracleCollectionSummary` | `theatre_id`, `query_window_start/end`, `bundles`, `gaps`, `total_sources_attempted/succeeded/failed` | Stage 1 aggregate. `.coverage_ratio` property computes `succeeded / attempted`. |

**Field-level alignment with worldmonitor contract:**

| Field | Pipeline (`osint_pipeline`) | WM Contract (`worldmonitor_api_contract`) |
|-------|----------------------------|-------------------------------------------|
| `independence_upstream_id` | Present (required for dedup) | Absent |
| `jurisdiction` | Present | Absent |
| `raw_payload_size_bytes` | Present | Absent |
| `receipt_mode` | Present (enum) | Absent (implicit `http_transcript`) |
| `freshness` | Present (enum) | Absent |
| `query_context` | Present (dict) | Absent |
| `receipt.response_status` | Present (6-field form) | Absent in hash (5-field form) |
| `receipt.timestamp_ms` | Present (6-field form) | Absent in hash (5-field form) |
| `normalised_event` | Absent (pipeline is source-agnostic) | Present (WM-specific) |

The pipeline's `EvidenceBundle` is the superset. The WM contract will be updated to align in a future cycle.

#### 2.1.2 `models/registry.py`

**`RegistrySource` model fields:**

| Field | Type | Source in JSON |
|-------|------|---------------|
| `source_id` | `str` | `sources[].source_id` |
| `source_name` | `str` | `sources[].source_name` |
| `source_group` | `str` | `sources[].source_group` |
| `resolution_role` | `str` | `sources[].resolution_role` |
| `priority_bucket` | `str` | `sources[].priority_bucket` |
| `settlement_eligible` | `bool` | `sources[].settlement_eligible` |
| `jurisdiction` | `str` | `sources[].jurisdiction` |
| `auth_methods` | `list[str]` | `sources[].auth_methods` |
| `api_url` | `str \| None` | `sources[].api_url` |
| `ui_url` | `str \| None` | `sources[].ui_url` |
| `independence_upstream_id` | `str` | `sources[].independence_upstream_id` |
| `access_surface` | `str` | `sources[].access_surface` |
| `access_surface_confirmed` | `bool` | `sources[].access_surface_confirmed` |
| `access_proof` | `dict` | `sources[].access_proof` |
| `revision_policy` | `str` | `sources[].revision_policy` |
| `receipt_mode_minimum` | `str` | `sources[].receipt_mode_minimum` |
| `counter_signal_class` | `str \| None` | `sources[].counter_signal_class` |
| `cost_model` | `str` | `sources[].cost_model` |
| `world_monitor_domain` | `str \| None` | `sources[].world_monitor_domain` |
| `replayability` | `str` | `sources[].replayability` |
| `legal_risk` | `str` | `sources[].legal_risk` |
| `rate_limit_notes` | `str` | `sources[].rate_limit_notes` |
| `gap_policy_default` | `bool` | `sources[].gap_policy_default` |
| `evidence_capture` | `dict` | `sources[].evidence_capture` |
| `notes` | `str` | `sources[].notes` |
| `theatre_families` | `list[str]` | `sources[].theatre_families` |

**`RegistryLoader` interface:**

```python
class RegistryLoader:
    @classmethod
    def from_file(cls, path: str | Path) -> RegistryLoader
    def get(self, source_id: str) -> RegistrySource | None
    def exists(self, source_id: str) -> bool
    def all_sources(self) -> list[RegistrySource]
    def settlement_eligible(self) -> list[RegistrySource]
    def by_jurisdiction(self, jurisdiction: str) -> list[RegistrySource]
    def by_source_group(self, group: str) -> list[RegistrySource]
    def by_resolution_role(self, role: str) -> list[RegistrySource]
    def counter_signal_sources(self) -> list[RegistrySource]
    def free_public_sources(self) -> list[RegistrySource]
    def upstream_groups(self) -> dict[str, list[str]]
    @property version -> str
    @property total_sources -> int
```

**Version validation:** `from_file()` must validate `data["version"] == "0.4.0"`. Raise `ValueError` on mismatch.

**Bug fix required (K-1):**

```python
# BROKEN (skeleton):
if s.access_surface in ("public_api",)
    and "none" in s.auth_methods or "api_key" in s.auth_methods

# FIXED:
if (s.access_surface == "public_api"
    and s.cost_model == "free"
    and s.settlement_eligible
    and any(m in ("none", "api_key", "user_agent_header") for m in s.auth_methods))
```

#### 2.1.3 `models/oracle_output.py`

| Model | Key Fields | Notes |
|-------|-----------|-------|
| `CorroborationResult` | `claim_id`, `primary_source_id`, `primary_source_group`, `distinct_corroborating_groups`, `corroboration_minimum`, `corroboration_window_seconds`, `corroborating_sources`, `corroborating_groups`, `excluded_by_dedup`, `outside_window` | `.passed`: `distinct_corroborating_groups >= corroboration_minimum`. |
| `CounterSignalResult` | `counter_signal_class`, `source_id`, `checked`, `signal_found`, `signal_detail`, `allow_gap` | `.passed`: `checked AND (NOT signal_found OR allow_gap)`. |
| `CriterionScore` | `criterion_id`, `score` (0.0-1.0), `passed`, `detail`, `evidence_bundle_ids` | Per-criterion score from Stage 3. |
| `OracleOutput` | `oracle_id`, `theatre_id`, `evaluated_at`, `collection`, `corroboration_results`, `counter_signal_results`, `criterion_scores`, `composite_score`, `bundle_hash`, `gap_report`, `coverage_percentage`, `counter_signals_checked/found` | Final output. `bundle_hash` is SHA-256 of canonical JSON of all evidence bundles. |

---

### 2.2 Engine Layer (`osint_pipeline/engine/`)

#### 2.2.1 `engine/canonical.py` — Canonical JSON and SHA-256

**Critical decision:** Delegate RFC 8785 canonical JSON to `theatre/engine/canonical_json.py`. The skeleton's `canonical_json()` uses bare `json.dumps` without float normalisation, NaN/Infinity rejection, or bool/int distinction.

**Delegation structure:**

```python
from theatre.engine.canonical_json import canonical_json  # RFC 8785 single source of truth

def sha256_hex(data: str | bytes) -> str: ...
def canonical_hash(obj: Any) -> str: ...
def http_transcript_canonical(method, url, headers, response_status, response_body, timestamp_ms) -> str: ...
def http_transcript_hash(method, url, headers, response_status, response_body, timestamp_ms) -> str: ...
```

**HTTP Transcript Canonical Form (6-field):**

```
{METHOD}\n{canonical_url}\n{canonical_headers}\n{response_status}\n{response_body_hash}\n{timestamp_ms}
```

- **Method:** Uppercased.
- **Canonical URL:** Trailing slash stripped.
- **Canonical headers:** Sorted by lowercase key, values trimmed, joined with `;` as `key=value;key=value`.
- **Response status:** Integer as string.
- **Response body hash:** SHA-256 of raw response bytes.
- **Timestamp:** UTC milliseconds since epoch.

#### 2.2.2 `engine/collection_runner.py` — Stage 1

**Class: `CollectionRunner`**

- Parallel execution via `ThreadPoolExecutor` (`max_workers=5`, `timeout_budget_seconds=60.0`).
- `run()` — parallel with timeout. Filters by `required_source_ids`. Maps failures to `GapReport`.
- `run_sequential()` — single-threaded for debugging.
- `close_all()` — close all collector HTTP clients.

#### 2.2.3 `engine/corroboration.py` — Stage 2

**Class: `CorroborationEngine`** (`corroboration_minimum=2`, `corroboration_window_seconds=3600`)

**Algorithm:**
1. Exclude primary bundle by `bundle_id`.
2. Filter by `resolution_role` in (`secondary_corroboration`, `primary_evidence`).
3. Deduplicate by `independence_upstream_id` — first seen wins.
4. Exclude candidates sharing upstream with primary.
5. Time window check: `|delta_t| <= corroboration_window_seconds * 1000` ms.
6. Count distinct `source_groups` differing from primary's.
7. Pass when `distinct_groups >= corroboration_minimum`.

#### 2.2.4 `engine/counter_signal.py` — Stage 2b

**11 committed classes:** `calendar_holiday`, `calendar_trading_halt`, `outage_reported`, `policy_rule_change`, `regulatory_status_change`, `legal_dispute_active`, `sanctions_designation`, `corporate_event`, `force_majeure`, `data_revision_notice`, `seasonal_pattern`.

**Pass criterion per class:** `checked=True AND (signal_found=False OR allow_gap=True)`.

#### 2.2.5 `engine/scorer.py` — Stage 3 (New File)

**Class: `Scorer`**

**Criterion scoring:**

| Criterion ID | Source | Weight |
|-------------|--------|--------|
| `source_coverage` | `succeeded / attempted` | 0.20 |
| `receipt_validity` | Fraction with valid receipts | 0.15 |
| `corroboration_met` | All corroboration passed? | 0.30 |
| `counter_signal_clear` | Fraction of checked classes that passed | 0.15 |
| `confidence_weighted` | Mean `confidence_score` | 0.20 |

**Bundle hash:**
```python
bundle_dicts = sorted([b.model_dump(mode="json") for b in bundles], key=lambda d: d["bundle_id"])
bundle_hash = sha256_hex(canonical_json(bundle_dicts))
```

---

### 2.3 HTTP Transcript — 5-Field vs 6-Field Divergence

| Aspect | Pipeline (6-field, authoritative) | WM Contract (5-field, legacy) |
|--------|----------------------------------|-------------------------------|
| **Fields** | method + url + headers + response_status + body_hash + timestamp_ms | method + url + query + headers + body_hash |
| **Includes response_status** | Yes | No |
| **Includes timestamp_ms** | Yes | No |
| **Float normalisation** | Yes (delegates to theatre engine) | No |

The pipeline's 6-field form is authoritative per the Composed Oracle Spec v2 section 5.

---

### 2.4 Collectors Layer (`osint_pipeline/collectors/`)

#### 2.4.1 `collectors/base.py` — Abstract Base Collector

Abstract properties: `source_id`, `source_group`, `independence_upstream_id`, `resolution_role`, `jurisdiction`.

Abstract methods: `build_request()`, `extract()`.

Concrete methods: `collect()`, `assess_freshness()`, `to_gap_report()`, `close()`.

**HTTP client:** Lazy-initialised `httpx.Client`, timeout 30s, `follow_redirects=True`.

**Error mapping:**

| HTTP Status | CollectionStatus |
|-------------|-----------------|
| 401, 403 | `AUTH_FAILURE` |
| 429 | `RATE_LIMITED` |
| 404 | `NOT_FOUND` |
| >= 500 | `SOURCE_ERROR` |
| `httpx.TimeoutException` | `TIMEOUT` |
| `httpx.ConnectError` | `NETWORK_ERROR` |

#### 2.4.2 MVP Collectors

| Collector | source_id | Auth |
|-----------|-----------|------|
| `CompaniesHouseCollector` | `companies_house_api` | API key (HTTP Basic) |
| `SECEdgarCollector` | `sec_edgar_efts` | User-Agent header |
| `ECBSDWCollector` | `ecb_sdw` | None |

**K-6 fix:** `CompaniesHouseCollector.independence_upstream_id` must return `"uk_companies_house_backend"` (not `"gb_companies_house_register"`).

---

### 2.5 Configuration (`osint_pipeline/config.py`)

Environment variables only. No secrets in code.

| Setting | Env Var | Default |
|---------|---------|---------|
| `REGISTRY_PATH` | `OSINT_REGISTRY_PATH` | `theatre/fixtures/.../echelon_osint_source_registry_v0_4_0.json` |
| `COMPANIES_HOUSE_API_KEY` | `COMPANIES_HOUSE_API_KEY` | `""` |
| `SEC_EDGAR_USER_AGENT` | `SEC_EDGAR_USER_AGENT` | `""` |
| `FRED_API_KEY` | `FRED_API_KEY` | `""` |
| `MAX_WORKERS` | `OSINT_MAX_WORKERS` | `5` |
| `TIMEOUT_BUDGET_SECONDS` | `OSINT_TIMEOUT_BUDGET` | `60.0` |
| `COLLECTOR_TIMEOUT_SECONDS` | `OSINT_COLLECTOR_TIMEOUT` | `30.0` |

---

### 2.6 CLI (`osint_pipeline/cli.py`)

Entry point: `python -m osint_pipeline <command>`. Uses `argparse` (stdlib).

| Command | Purpose |
|---------|---------|
| `run` | Execute full three-stage pipeline |
| `inspect` | Pretty-print evidence bundle JSON |
| `validate` | Validate registry alignment |
| `collect` | Run single collector for debugging |

---

## 3. Integration Points

### 3.1 Theatre Engine

Import `canonical_json` from `theatre.engine.canonical_json`. Only import from theatre package. No changes to theatre engine required.

### 3.2 Registry Fixture

Read-only load of `echelon_osint_source_registry_v0_4_0.json` (2726 lines, 57 sources). Version-validated at startup.

### 3.3 World Monitor API Contract

No direct calls in Cycle-035. Data model alignment documented in section 2.1.1.

---

## 4. Testing Strategy

### 4.1 Existing Tests (No Regression)

`tests/theatre/test_canonical_json.py` — 37 tests. Must pass unchanged.

### 4.2 New Pipeline Tests (`tests/osint_pipeline/`)

| Test File | Coverage |
|-----------|----------|
| `test_canonical.py` | Theatre engine delegation, SHA-256, HTTP transcript, receipt determinism |
| `test_evidence_models.py` | Model instantiation, hash validation, properties |
| `test_registry.py` | Fixture loading, version check, queries, corrected filter logic |
| `test_corroboration.py` | Upstream dedup, time window, distinct groups, minimum enforcement |
| `test_counter_signal.py` | All 11 classes, pass/fail logic, gap handling |
| `test_scorer.py` | Per-criterion scores, composite, bundle hash, coverage |
| `test_collectors.py` | Mock HTTP via `httpx.MockTransport`, error mapping |
| `test_companies_house.py` | Endpoints, extract, auth header, freshness |
| `test_collection_runner.py` | Parallel execution, timeout, gaps, source filtering |
| `test_fixtures_regression.py` | Existing validator scripts pass |

All tests use `pytest`. HTTP tests use `httpx.MockTransport`.

---

## 5. Security

- API keys from environment variables only. No secrets in code.
- Rate limits respected per source. 429 returns `RATE_LIMITED` status.
- Pydantic validators enforce field constraints.
- No retry logic in Cycle-035 (Cycle-036+).

---

## 6. Known Issues and Required Fixes

| ID | File | Issue | Fix |
|----|------|-------|-----|
| K-1 | `models/registry.py` | `free_public_sources()` operator precedence bug | Fix parenthesisation, add `cost_model`/`settlement_eligible` checks |
| K-2 | `models/registry.py` | Missing `cost_model` field | Add field |
| K-3 | `engine/canonical.py` | Missing RFC 8785 float normalisation | Delegate to `theatre.engine.canonical_json` |
| K-4 | `engine/scorer.py` | File does not exist | Create from scratch |
| K-5 | `tests/test_canonical.py:168` | Typo in `__main__` exception handler | Fix class name |
| K-6 | `collectors/companies_house.py` | `independence_upstream_id` mismatch | Change to `"uk_companies_house_backend"` |
| K-7 | `models/registry.py` | No version validation in `from_file()` | Add version check |
| K-8 | `models/registry.py` | Missing registry fields | Add all fields from section 2.1.2 |

---

## 7. Implementation Sequence

### Phase 1: Core Primitives
1. Package structure + `__init__.py` files
2. `engine/canonical.py` — delegate to theatre engine
3. `models/evidence.py` — enums + models
4. `models/registry.py` — fix K-1, K-2, K-7, K-8

### Phase 2: First Live Collector
5. `collectors/base.py` — `BaseCollector` ABC
6. `collectors/companies_house.py` — fix K-6

### Phase 3: Collection Runner + More Collectors
7. `engine/collection_runner.py`
8. `collectors/sec_edgar.py`
9. `collectors/ecb_sdmx.py`

### Phase 4: Corroboration, Counter-Signals, Scoring
10. `engine/corroboration.py`
11. `engine/counter_signal.py`
12. `engine/scorer.py` (K-4)

### Phase 5: Oracle Output, Config, CLI
13. `models/oracle_output.py`
14. `config.py`
15. `cli.py`

### Phase 6: Tests
16. All test files
17. Regression check on 37 existing tests
18. End-to-end test with mock HTTP through all stages
