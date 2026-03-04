# PRD: OSINT Pipeline — Live Collection & Evidence Bundles (Cycle-035)

> **Version:** 1.0
> **Date:** 2026-03-01
> **Status:** DRAFT
> **Depends on:** Cycle-034 deliverables (registry v0.4.0, 10 fixtures, validators, WM API contract)
> **Source:** `~/Downloads/osint_pipeline/CYCLE_035_PLAN.md`, skeleton files, codebase reality

---

## 1. Problem Statement

Echelon's OSINT Composed Oracle template (OSINT_COMPOSED_ORACLE_V1) currently operates exclusively against static fixture data. The 10-record dataset (6 pass / 4 fail) validates the commitment criteria and certificate flow, but no live data collection exists. The pipeline cannot fetch from real government registries, wire services, or market data APIs, meaning:

- Evidence bundles lack HTTP Transcript Receipts from actual network calls.
- Corroboration logic has never been exercised against independent sources with distinct upstream lineage.
- Counter-signal checking has never evaluated real-time calendars, outage feeds, or sanctions lists.
- Settlement eligibility remains theoretical — no source has produced a deterministic, replayable receipt.

Without a live pipeline, the platform cannot progress from "demo that shows the lifecycle" (Cycle-034) to "system that actually verifies claims against reality" (Cycle-035).

> Sources: `CYCLE_035_PLAN.md:1-7`, `echelon_osint_source_registry_v0_4_0.json` (57 sources, 9 free settlement-eligible), `osint_composed_oracle_fixtures_10.json` (static only)

---

## 2. Vision & Mission

**Vision:** A working three-stage Composed Oracle pipeline that fetches live data from free public APIs, produces deterministic HTTP Transcript Receipts, cross-references sources for corroboration, and outputs confidence-weighted evidence bundles suitable for calibration certificate generation.

**Mission:** Build the `osint_pipeline/` package as a standalone Python library within the monorepo, integrating with the existing theatre engine (`theatre/engine/canonical_json.py`), registry fixtures, and worldmonitor API contract (`backend/schemas/worldmonitor_api_contract.py`).

---

## 3. Goals & Success Criteria

| Goal | Success Criterion | Measurement |
|------|-------------------|-------------|
| Live collection | At least 3 free sources producing real evidence bundles with valid receipts | Companies House (GB), SEC EDGAR (US), ECB SDW (EU) all return bundles |
| Receipt determinism | Same query parameters + same response body = same receipt hash | Tests prove `http_transcript_hash(**params) == http_transcript_hash(**params)` |
| Corroboration | Dedup by `independence_upstream_id`, count distinct `source_groups` | Test with 2 sources sharing upstream vs 2 truly independent sources |
| Counter-signals | Evaluate at least 3 of 11 committed classes | `calendar_holiday`, `outage_reported`, `policy_rule_change` checked |
| Scoring | Confidence-weighted per-criterion scores assembled into `OracleOutput` | Full pipeline run produces valid `OracleOutput` with `bundle_hash` |
| No regression | Existing 37 canonical JSON tests + fixture validators pass | `pytest tests/theatre/test_canonical_json.py` green; `validate_osint_registry.py` + `validate_osint_fixtures.py` green |
| CLI | End-to-end oracle run from command line | `python -m osint_pipeline run --theatre OSINT_COMPOSED_ORACLE_V1` |

---

## 4. User & Stakeholder Context

**Primary user:** Echelon's verification pipeline (automated). The pipeline consumes evidence bundles during theatre resolution.

**Secondary user:** Developer running the CLI to inspect bundles, debug collection failures, or validate a new source integration.

**Stakeholder:** Soju (platform operator) — needs confidence that settlement decisions are grounded in real, provenance-tracked evidence rather than synthetic fixtures.

---

## 5. Functional Requirements

### FR-1: Evidence Models (Pydantic v2)

All models use Pydantic v2 (`BaseModel`, `Field`, `field_validator`). Models must align with:
- `backend/schemas/worldmonitor_api_contract.py` — shared `HTTPTranscriptReceipt` shape
- `theatre/fixtures/.../echelon_osint_source_registry_v0_4_0.json` — `source_group_enum`, `resolution_role_enum`, `priority_bucket_enum`
- `theatre/fixtures/.../osint_composed_oracle_fixtures_10.json` — fixture structure

Key models:
- `EvidenceBundle` — immutable artefact with SHA-256 provenance chain
- `HTTPTranscriptReceipt` — deterministic receipt following canonical form spec
- `CollectionResult` — wraps bundle or failure with duration and status
- `GapReport` — "show what you cannot see" for failed collections
- `OracleCollectionSummary` — Stage 1 output aggregating bundles + gaps

### FR-2: Registry Loader

Parse `echelon_osint_source_registry_v0_4_0.json` into queryable `RegistrySource` models. Provide:
- `get(source_id)` — single source lookup
- `settlement_eligible()` — filter by `settlement_eligible: true`
- `by_jurisdiction(code)` — filter by ISO jurisdiction code
- `free_public_sources()` — filter by `cost_model: "free"` AND `settlement_eligible: true`
- `upstream_groups()` — group by `independence_upstream_id` for dedup

### FR-3: Canonical Hashing (RFC 8785 + HTTP Transcript)

**Critical alignment requirement**: The pipeline's canonical JSON implementation MUST delegate to or be compatible with the existing `theatre/engine/canonical_json.py` (63 lines, full RFC 8785 with float normalisation, NaN/Infinity rejection, bool/int distinction).

HTTP Transcript Canonical Form (6-field, from Composed Oracle Spec v2 section 5):
```
method + "\n" + canonical_url + "\n" + canonical_headers + "\n" + response_status + "\n" + response_body_hash + "\n" + timestamp_ms
```

**Note on worldmonitor_api_contract.py divergence**: The WM contract uses a 5-field form (`method + url + query + headers + body_hash`) without `response_status` and `timestamp_ms`. The pipeline's 6-field form is authoritative — the WM contract will be updated to align in a future cycle.

### FR-4: BaseCollector Abstract

Abstract base class defining the fetch-receipt contract:
- `build_request()` — returns (method, url, headers, params) tuple
- `extract()` — parses raw response body into structured extract + confidence score
- `collect()` — orchestrates: build request, HTTP fetch, receipt generation, bundle assembly
- Uses `httpx.Client` with lazy initialisation and context manager support
- Each collector declares: `source_id`, `source_group`, `independence_upstream_id`, `resolution_role`, `jurisdiction`

### FR-5: Concrete Collectors (9 Free Sources)

Priority order for implementation:

| Priority | source_id | Jurisdiction | Auth | Reason |
|----------|-----------|-------------|------|--------|
| 1 | `companies_house_api` | GB | API key (free) | Best first target: simple REST, immutable data, settlement-eligible |
| 2 | `sec_edgar_efts` | US | User-Agent header | Free, well-documented, primary evidence for US entities |
| 3 | `ecb_sdw` | EU | None | Free, SDMX format, secondary corroboration |
| 4 | `fred_api` | US | API key (free) | Economic indicators, secondary corroboration |
| 5 | `boe_statistics` | GB | None | Interest rates, monetary policy |
| 6 | `fr_inpi_rne` | EU/FR | None | French company register |
| 7 | `london_gazette` | GB | None | Insolvency notices, counter-signal source |
| 8 | `ny_fed_api` | US | None | Treasury rates |
| 9 | `worldmonitor` | Self | WM API | Self-hosted, uses worldmonitor_api_contract.py |

**Minimum viable:** Collectors 1-3 must work for Cycle-035 completion.

### FR-6: Collection Runner (Stage 1)

Orchestrate collectors per theatre oracle configuration:
- Parallel execution via `ThreadPoolExecutor` with configurable `max_workers`
- Timeout budget (default 60s) across all collections
- Required source IDs filtering
- Allowable gap specification
- Gap reporting for failed or timed-out sources
- Sequential mode for debugging

### FR-7: Corroboration Engine (Stage 2)

Per the corroboration rule:
1. Exclude primary bundle from candidates
2. Filter by `resolution_role` in (`secondary_corroboration`, `primary_evidence`)
3. Deduplicate by `independence_upstream_id` — keep first seen per upstream
4. Exclude candidates sharing upstream with primary
5. Check time window: `|delta_t| <= corroboration_window_seconds * 1000` (milliseconds)
6. Count distinct `source_groups` among remaining candidates
7. Pass when `distinct_groups >= corroboration_minimum` (default 2)

### FR-8: Counter-Signal Checker (Stage 2b)

Evaluate 11 committed counter-signal classes:
1. `calendar_holiday` — public holidays explaining signal absence
2. `calendar_trading_halt` — exchange/market closures
3. `outage_reported` — known infrastructure outages
4. `policy_rule_change` — regulatory or policy changes
5. `regulatory_status_change` — entity regulatory status change
6. `legal_dispute_active` — active legal proceedings
7. `sanctions_designation` — sanctions list presence
8. `corporate_event` — M&A, restructuring, insolvency
9. `force_majeure` — natural disaster, conflict, pandemic
10. `data_revision_notice` — source issued revision notice
11. `seasonal_pattern` — known seasonal variation

Pass criterion: `checked=True AND (signal_found=False OR allow_gap=True)`.

### FR-9: Scorer (Stage 3)

Assemble `OracleOutput` from Stages 1-2:
- Compute per-criterion scores from evidence bundles
- Weighted composite score across all criteria
- Bundle hash: SHA-256 of canonical JSON of all evidence bundles
- Coverage percentage: `(sources_with_receipts / required_sources) * 100`
- Counter-signal summary counts

### FR-10: CLI Entry Point

Command-line interface for:
- `run` — execute full oracle pipeline for a given theatre configuration
- `inspect` — display details of a specific evidence bundle
- `validate` — check registry alignment and source health
- `collect` — run a single collector for debugging

---

## 6. Technical Constraints

### TC-1: Pydantic v2 Alignment

All models use Pydantic v2. Field validators use `@field_validator`. No Pydantic v1 patterns (`validator`, `Config` class).

### TC-2: Existing Theatre Engine Compatibility

The pipeline MUST NOT duplicate the canonical JSON implementation. Options:
- **Option A (preferred):** Import from `theatre.engine.canonical_json` directly
- **Option B:** Copy the 63-line implementation and add HTTP transcript functions

The existing 37 tests in `tests/theatre/test_canonical_json.py` must continue to pass.

### TC-3: Registry v0.4.0 Schema

The `RegistryLoader` must parse the exact schema at `theatre/fixtures/two_rail_theatres_v0_1/datasets/echelon_osint_source_registry_v0_4_0.json`. Key fields per source entry: `source_id`, `source_name`, `source_group`, `priority_bucket`, `resolution_role`, `replayability`, `legal_risk`, `cost_model`, `rate_limit_notes`, `gap_policy_default`, `world_monitor_domain`, `evidence_capture`, `settlement_eligible`, `notes`, `theatre_families`, `auth_methods`, `jurisdiction`.

### TC-4: No Paid APIs

Cycle-035 uses only free, publicly available APIs. Paid sources (Polygon.io, RavenPack, Dataminr, Refinitiv) are Cycle-036+.

### TC-5: British Spelling

All documentation and user-facing strings use British spelling throughout (e.g. "normalised", "serialisation", "behaviour").

---

## 7. Known Issues in Skeleton Files

Issues identified during review of `~/Downloads/osint_pipeline/` drafts:

| File | Issue | Fix Required |
|------|-------|-------------|
| `models/registry.py` | `free_public_sources()` has operator precedence bug in filter condition | Fix parenthesisation in `and`/`or` logic |
| `engine/canonical.py` | Missing RFC 8785 float normalisation (NaN/Inf rejection, whole-float-to-int) that exists in `theatre/engine/canonical_json.py` | Delegate to existing implementation or port float normalisation |
| `engine/scorer.py` | File does not exist in skeleton | Must be created from scratch |
| `tests/test_canonical.py:168` | Typo: `AssertionError` should be `AssertionError` | Fix exception class name on line 169 |
| `collectors/base.py` | `collect()` stores entire `raw_body` in `raw_payload` field but `EvidenceBundle` model expects `raw_payload_hash` (hash, not raw bytes) | Verify alignment — skeleton evidence.py uses `raw_payload_hash` (correct), base.py computes hash |
| `worldmonitor_api_contract.py` | 5-field HTTP transcript form diverges from pipeline's 6-field form | Document divergence, defer contract update to future cycle |

---

## 8. Scope & Prioritisation

### MVP (must have for Cycle-035)
- Models: `evidence.py`, `registry.py`, `oracle_output.py`
- Engine: `canonical.py` (aligned with theatre engine), `collection_runner.py`, `corroboration.py`, `counter_signal.py`, `scorer.py`
- Collectors: `companies_house.py` + 2 more free sources
- Tests: canonical hashing, receipt determinism, corroboration dedup, fixture validation
- CLI: basic `run` and `inspect` commands

### Should have
- All 9 free collectors
- Counter-signal evaluation against live calendar/outage feeds
- Gap reporting with allowable gap configuration

### Could have (Cycle-036+)
- Paid source integration
- World Monitor self-hosted collector
- Theatre Command UI integration
- Multi-theatre parallel evaluation

---

## 9. Risks & Dependencies

| Risk | Mitigation |
|------|-----------|
| Companies House API key registration takes time | Use mock/fixture mode as fallback during development |
| SEC EDGAR rate limiting (10 req/sec) | Respect User-Agent header contract, implement backoff |
| ECB SDMX format complexity | Start with JSON format endpoint, defer XML/SDMX parsing |
| Registry v0.4.0 schema drift | RegistryLoader validates version field on load |
| Canonical hash mismatch between pipeline and theatre engine | Delegate to single implementation, test round-trip |

---

## 10. Out of Scope

- Theatre Command globe rendering
- Multi-agent simulation / Hounfour integration
- Paid source procurement
- Registry v0.5 expansion
- World Monitor deployment (separate cycle)
- Certificate generation (already working from Cycle-034)
- Frontend changes to the Bounded Inquiry Console
