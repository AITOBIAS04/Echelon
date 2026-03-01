# Sprint Plan: OSINT Pipeline — Live Collection & Evidence Bundles

> **Cycle:** cycle-002 (OSINT Pipeline)
> **PRD:** `grimoires/loa/prd.md`
> **SDD:** `grimoires/loa/sdd.md`
> **Date:** 2026-03-01
> **Sprints:** 3 (global IDs: 4-6)
> **Team:** Single AI agent

---

## Sprint 1: Core Primitives & First Collector (global: sprint-4)

**Goal:** Establish the `osint_pipeline/` package with all models, canonical hashing (delegated to theatre engine), registry loader, and the first working collector (Companies House). All foundation code that Sprints 2-3 depend on.

### Tasks

#### T1.1: Package Structure
Create `osint_pipeline/` directory tree at monorepo root with all `__init__.py` files and `__main__.py` stub.

**Acceptance Criteria:**
- [x] `osint_pipeline/__init__.py` exists with package docstring
- [x] `osint_pipeline/models/__init__.py` re-exports all model classes
- [x] `osint_pipeline/engine/__init__.py` re-exports canonical functions
- [x] `osint_pipeline/collectors/__init__.py` exports `BaseCollector`
- [x] `tests/osint_pipeline/conftest.py` exists (no `__init__.py` — prevents namespace conflict)
- [x] `import osint_pipeline` succeeds from monorepo root

#### T1.2: `engine/canonical.py` — RFC 8785 Delegation + HTTP Transcript
Implement canonical hashing module that delegates `canonical_json` to `theatre.engine.canonical_json` and adds SHA-256 and HTTP Transcript Canonical Form functions.

**Acceptance Criteria:**
- [x] `canonical_json` imported from `theatre.engine.canonical_json` (not reimplemented)
- [x] `sha256_hex(data)` returns 64-char lowercase hex string
- [x] `canonical_hash(obj)` composes `sha256_hex(canonical_json(obj))`
- [x] `http_transcript_canonical()` builds 6-field form: method + url + headers + response_status + body_hash + timestamp_ms
- [x] `http_transcript_hash()` returns SHA-256 of canonical form
- [x] Headers sorted by lowercase key, values trimmed, joined with `;`
- [x] Trailing slash stripped from URL
- [x] Method uppercased
- [x] Fix K-3 from SDD (skeleton's bare `json.dumps` replaced with theatre engine delegation)

#### T1.3: `models/evidence.py` — Pydantic v2 Evidence Models
Implement all enumerations and models for Stage 1 evidence artefacts.

**Acceptance Criteria:**
- [x] `ReceiptMode`, `CollectionStatus`, `FreshnessState` enums defined
- [x] `HTTPTranscriptReceipt` with field validators enforcing 64-char hex for hash fields
- [x] `EvidenceBundle` with all fields from SDD section 2.1.1 (bundle_id, source_id, source_group, independence_upstream_id, resolution_role, jurisdiction, raw_payload_hash, receipt, structured_extract, confidence_score, etc.)
- [x] `CollectionResult` with `.succeeded` property
- [x] `GapReport` with allow_gap field
- [x] `OracleCollectionSummary` with `.coverage_ratio` property
- [x] All models use Pydantic v2 (`BaseModel`, `Field`, `field_validator`)
- [x] No Pydantic v1 patterns

#### T1.4: `models/registry.py` — Registry Loader
Implement `RegistrySource` model and `RegistryLoader` class that parses the v0.4.0 registry JSON.

**Acceptance Criteria:**
- [x] `RegistrySource` includes all fields from SDD section 2.1.2 (26 fields including `cost_model`, `replayability`, `legal_risk`, `evidence_capture`, etc.)
- [x] Fix K-1: `free_public_sources()` operator precedence corrected with `cost_model == "free"` and `settlement_eligible` checks
- [x] Fix K-2: `cost_model` field added to `RegistrySource`
- [x] Fix K-7: `from_file()` validates `version == "0.4.0"`
- [x] Fix K-8: All missing registry fields added
- [x] `get(source_id)` returns correct source or `None`
- [x] `settlement_eligible()` returns correct subset
- [x] `by_jurisdiction("GB")` returns GB sources only
- [x] `free_public_sources()` returns free, settlement-eligible, public API sources
- [x] `upstream_groups()` returns dict of upstream_id to source_id list
- [x] Successfully loads actual `echelon_osint_source_registry_v0_4_0.json`

#### T1.5: `models/oracle_output.py` — Oracle Output Models
Implement models for corroboration, counter-signal, scoring, and final oracle output.

**Acceptance Criteria:**
- [x] `CorroborationResult` with `.passed` property (`distinct_groups >= minimum`)
- [x] `CounterSignalResult` with `.passed` property (`checked AND (NOT signal_found OR allow_gap)`)
- [x] `CriterionScore` with score bounds `[0.0, 1.0]`
- [x] `OracleOutput` with all fields from SDD section 2.1.3
- [x] `OracleOutput.all_criteria_passed` property works correctly

#### T1.6: `collectors/base.py` — BaseCollector ABC
Implement the abstract base class defining the fetch-receipt contract.

**Acceptance Criteria:**
- [x] Abstract properties: `source_id`, `source_group`, `independence_upstream_id`, `resolution_role`, `jurisdiction`
- [x] Abstract methods: `build_request()`, `extract()`
- [x] `collect()` orchestrates: build request -> httpx fetch -> receipt generation -> extract -> bundle assembly
- [x] Error mapping: 401/403 -> AUTH_FAILURE, 429 -> RATE_LIMITED, 404 -> NOT_FOUND, 5xx -> SOURCE_ERROR
- [x] `httpx.TimeoutException` -> TIMEOUT, `httpx.ConnectError` -> NETWORK_ERROR
- [x] Lazy-initialised `httpx.Client` with 30s timeout
- [x] Context manager support (`__enter__`/`__exit__`)
- [x] `to_gap_report()` converts failed `CollectionResult` to `GapReport`

#### T1.7: `collectors/companies_house.py` — First Live Collector
Implement Companies House API collector as the reference implementation.

**Acceptance Criteria:**
- [x] Fix K-6: `independence_upstream_id` returns `"uk_companies_house_backend"` (not `"gb_companies_house_register"`)
- [x] `build_request()` handles: company profile, filing-history, officers, PSC, charges, insolvency, search
- [x] API key via HTTP Basic auth (key as username, blank password, base64-encoded)
- [x] `extract()` returns structured extract with key company fields
- [x] `confidence_score = 1.0` for successful 200 responses
- [x] `assess_freshness()` returns `FRESH` for successful responses
- [x] Raises `ValueError` if API key is empty

#### T1.8: Core Tests (Canonical + Models + Registry)
Implement tests for all Sprint 1 code.

**Acceptance Criteria:**
- [x] `tests/osint_pipeline/test_canonical.py`: delegation to theatre engine verified (same hash output), sha256 known constants, HTTP transcript form structure, receipt determinism, header order irrelevance, trailing slash normalisation, different body/timestamp yield different hashes
- [x] `tests/osint_pipeline/test_evidence_models.py`: model instantiation, hash field validation, `.succeeded` property, `.coverage_ratio`
- [x] `tests/osint_pipeline/test_registry.py`: load from actual fixture file, version validation, `get()`, `settlement_eligible()`, `free_public_sources()`, `upstream_groups()`
- [x] `tests/osint_pipeline/test_companies_house.py`: `build_request` for each endpoint, `extract` for profile JSON, auth header, freshness assessment (using `httpx.MockTransport`)
- [x] `tests/osint_pipeline/conftest.py`: shared fixtures (loaded registry, sample bundles, sample query contexts)
- [x] Fix K-5: typo in skeleton `test_canonical.py` `__main__` block
- [ ] Existing 37 tests in `tests/theatre/test_canonical_json.py` still pass (regression check)

---

## Sprint 2: Pipeline Engine (global: sprint-5)

**Goal:** Build the three-stage pipeline: Collection Runner (Stage 1), Corroboration + Counter-Signal (Stage 2/2b), and Scorer (Stage 3). Add SEC EDGAR and ECB collectors to meet the 3-source MVP requirement.

### Tasks

#### T2.1: `engine/collection_runner.py` — Stage 1 Orchestrator
Implement parallel collection orchestrator with timeout budget and gap reporting.

**Acceptance Criteria:**
- [x] `CollectionRunner.__init__` accepts list of `BaseCollector`, `max_workers`, `timeout_budget_seconds`
- [x] `run()` executes collectors in parallel via `ThreadPoolExecutor`
- [x] `required_source_ids` filtering works (only runs specified collectors)
- [x] `allow_gaps_for` propagates to `GapReport.allow_gap`
- [x] Failed/timed-out collections produce `GapReport` entries
- [x] Missing collectors (in `required_source_ids` but not configured) logged as warning + gap
- [x] `run_sequential()` mode for debugging with full logging
- [x] `close_all()` closes all collector HTTP clients
- [x] Returns `OracleCollectionSummary` with correct counts

#### T2.2: `collectors/sec_edgar.py` — SEC EDGAR EFTS Collector
Implement US SEC EDGAR full-text search collector.

**Acceptance Criteria:**
- [x] `source_id = "sec_edgar"` (registry value), `jurisdiction = "US"`, `source_group = "official_gov"`
- [x] `resolution_role = "primary_evidence"`
- [x] `independence_upstream_id` matches registry value (`us_sec_edgar_backend`)
- [x] User-Agent header set from config (SEC requires email-based User-Agent)
- [x] `build_request()` constructs EDGAR EFTS search URL with query params
- [x] `extract()` parses SEC JSON response into structured extract
- [x] Respects SEC rate limit guidance (10 req/sec)

#### T2.3: `collectors/ecb_sdmx.py` — ECB SDW Collector
Implement EU ECB Statistical Data Warehouse collector using JSON format endpoint.

**Acceptance Criteria:**
- [x] `source_id = "ecb_data_api"` (registry value), `jurisdiction = "EU"`, `source_group = "market_data"`
- [x] `resolution_role = "primary_evidence"` (registry value)
- [x] `independence_upstream_id` matches registry value (`eu_ecb_sdw_backend`)
- [x] No auth required
- [x] `build_request()` constructs ECB data API URL with series key and format params
- [x] `extract()` parses ECB JSON response into structured extract with key rates/measures
- [x] Uses JSON format endpoint (not SDMX XML)

#### T2.4: `engine/corroboration.py` — Stage 2 Corroboration Engine
Implement the corroboration evaluation algorithm per the Composed Oracle Spec v2.

**Acceptance Criteria:**
- [x] `evaluate()` excludes primary bundle by `bundle_id`
- [x] Filters candidates by `resolution_role` in (`secondary_corroboration`, `primary_evidence`)
- [x] Deduplicates by `independence_upstream_id` — first seen wins
- [x] Excludes candidates sharing `independence_upstream_id` with primary
- [x] Time window check: `|delta_t| <= corroboration_window_seconds * 1000` ms
- [x] Counts distinct `source_groups` differing from primary's
- [x] `.passed` when `distinct_groups >= corroboration_minimum`
- [x] `evaluate_all()` returns one `CorroborationResult` per primary_evidence bundle
- [x] `excluded_by_dedup` and `outside_window` lists populated correctly

#### T2.5: `engine/counter_signal.py` — Stage 2b Counter-Signal Checker
Implement counter-signal evaluation for all 11 committed classes.

**Acceptance Criteria:**
- [x] `COUNTER_SIGNAL_CLASSES` list contains all 11 classes
- [x] `evaluate()` indexes bundles by `query_context["counter_signal_class"]`
- [x] Gaps indexed by `source_group` as approximation
- [x] For each class: bundles exist -> `checked=True`, checks `structured_extract["counter_signal_detected"]`
- [x] For each class: only gaps -> GapKind-aware (Concern 2): SIGNAL_ABSENCE=checked, INTELLIGENCE_GAP=unchecked
- [x] For each class: neither -> `checked=False`, `signal_detail="No source configured"`
- [x] `allow_gap` per-class from constructor parameter
- [x] Pass: `checked=True AND (signal_found=False OR allow_gap=True)`

#### T2.6: `engine/scorer.py` — Stage 3 Scorer (New File, K-4)
Create the scoring engine that assembles `OracleOutput` from Stages 1-2.

**Acceptance Criteria:**
- [x] Accepts `OracleCollectionSummary`, list of `CorroborationResult`, list of `CounterSignalResult`
- [x] Computes 5 criterion scores: `source_coverage`, `receipt_validity`, `corroboration_met`, `counter_signal_clear`, `confidence_weighted`
- [x] Weighted composite score with default weights (0.20, 0.15, 0.30, 0.15, 0.20)
- [x] Bundle hash: SHA-256 of canonical JSON of sorted evidence bundles
- [x] Coverage percentage: `(succeeded / attempted) * 100`
- [x] Counter-signal summary: `counter_signals_checked`, `counter_signals_found`
- [x] Assembles complete `OracleOutput` with `oracle_id` (UUID), `theatre_id`, `evaluated_at`
- [x] Gap report populated from `OracleCollectionSummary.gaps`

#### T2.7: Pipeline Engine Tests
Implement tests for all Sprint 2 engine and collector code.

**Acceptance Criteria:**
- [x] `test_collection_runner.py`: parallel execution, timeout budget, gap reporting, `required_source_ids` filtering, `allow_gaps_for`, `run_sequential` mode (13 tests)
- [x] `test_corroboration.py`: dedup by upstream, shared upstream exclusion, time window enforcement, distinct group counting, pass/fail for minimum, `evaluate_all` (10 tests)
- [x] `test_counter_signal.py`: all 11 class names, checked+not-found passes, checked+found+allow_gap passes, checked+found+no-allow fails, unchecked fails (11 tests)
- [x] `test_scorer.py`: per-criterion scores, composite weighted average, bundle hash determinism, coverage percentage, `OracleOutput` assembly (16 tests)
- [x] `test_collectors.py`: SEC EDGAR + ECB mock HTTP responses, error mapping verification (17 tests)
- [x] All tests use `httpx.MockTransport` (no live API calls)

---

## Sprint 3: CLI, Config & End-to-End Integration (global: sprint-6)

**Goal:** Wire everything together with configuration loading, CLI entry point, remaining collectors, and end-to-end integration tests. Verify no regression on existing tests.

### Tasks

#### T3.1: `config.py` — Configuration Module
Implement environment variable loading for API keys, timeouts, and registry path.

**Acceptance Criteria:**
- [x] Loads `OSINT_REGISTRY_PATH` (default: `theatre/fixtures/.../echelon_osint_source_registry_v0_4_0.json`)
- [x] Loads `COMPANIES_HOUSE_API_KEY`, `SEC_EDGAR_USER_AGENT`, `FRED_API_KEY` from env
- [x] Loads `OSINT_MAX_WORKERS` (default 5), `OSINT_TIMEOUT_BUDGET` (default 60.0), `OSINT_COLLECTOR_TIMEOUT` (default 30.0)
- [x] No secrets in code or committed files
- [x] No framework dependency (no Dynaconf, no pydantic-settings)
- [x] Frozen dataclass (immutable)

#### T3.2: `cli.py` — Command-Line Interface
Implement CLI with `run`, `inspect`, `validate`, and `collect` commands.

**Acceptance Criteria:**
- [x] `python -m osint_pipeline run --theatre OSINT_COMPOSED_ORACLE_V1 --query '{"company_number": "12345678"}' --output result.json` executes full 3-stage pipeline
- [x] `python -m osint_pipeline inspect --bundle result.json` pretty-prints bundle
- [x] `python -m osint_pipeline validate --registry <path>` loads registry, reports version, source count, free sources
- [x] `python -m osint_pipeline collect --source companies_house_api --query '{"company_number": "12345678"}'` runs single collector
- [x] Uses `argparse` (stdlib)
- [x] Exit codes: 0 success, 1 error
- [x] Meaningful error messages for missing API keys

#### T3.3: Should-Have Collectors (FRED, BoE, Gazette)
Implement 3 additional free-source collectors beyond the MVP 3.

**Acceptance Criteria:**
- [x] `FREDCollector`: `fred_api`, US, API key auth, economic indicators
- [x] `BoECollector`: `boe_rates` (registry value), GB, no auth, interest rates
- [x] `GazetteCollector`: `uk_gazette` (registry value), GB, no auth, insolvency notices (counter-signal source)
- [x] All inherit from `BaseCollector` correctly
- [x] All `independence_upstream_id` values match registry
- [x] `extract()` returns sensible structured extracts

#### T3.4: `__main__.py` Module Entry Point
Create `osint_pipeline/__main__.py` to support `python -m osint_pipeline`.

**Acceptance Criteria:**
- [x] `python -m osint_pipeline --help` shows usage
- [x] Delegates to `cli.py` main function

#### T3.5: End-to-End Integration Tests
Full pipeline tests with mock HTTP through all three stages, plus regression checks.

**Acceptance Criteria:**
- [x] `test_fixtures_regression.py`: registry loads, known sources present, collector alignment verified
- [x] End-to-end test: mock 3 collectors -> CollectionRunner -> CorroborationEngine -> CounterSignalChecker -> Scorer -> OracleOutput
- [x] `OracleOutput.bundle_hash` is deterministic (same collection -> same hash)
- [x] `OracleOutput.composite_score` in [0.0, 1.0]
- [x] `OracleOutput.coverage_percentage` computed correctly
- [x] Existing 35 tests in `tests/theatre/test_canonical_json.py` still pass
- [x] All 228 new `tests/osint_pipeline/` tests pass
- [x] Full suite green (263 total)

#### T3.6: Package Metadata and `pyproject.toml` Updates
Ensure the pipeline is properly discoverable as a Python package.

**Acceptance Criteria:**
- [x] `pyproject.toml` updated with [project] metadata, `pythonpath = ["."]` verified
- [x] `pydantic` and `httpx` in dependencies
- [x] `pytest` in dev dependencies
- [x] No circular imports between `osint_pipeline` and `theatre`

---

## Summary

| Sprint | Global ID | Goal | Key Deliverables |
|--------|-----------|------|-----------------|
| 1 | sprint-4 | Core Primitives & First Collector | Package structure, canonical.py, evidence/registry/oracle models, BaseCollector, CompaniesHouse, core tests |
| 2 | sprint-5 | Pipeline Engine | CollectionRunner, SEC EDGAR + ECB collectors, Corroboration, Counter-Signal, Scorer, engine tests |
| 3 | sprint-6 | CLI & Integration | Config, CLI, 3 more collectors, end-to-end tests, regression checks |

## Risks

| Risk | Sprint | Mitigation |
|------|--------|-----------|
| `theatre.engine.canonical_json` import fails from `osint_pipeline/` | 1 | Verify `pyproject.toml` pythonpath; fallback to copying the 63-line file |
| Companies House API key not available | 1 | Tests use `httpx.MockTransport`; live testing optional |
| SEC EDGAR EFTS API shape changes | 2 | Document expected response format; mock in tests |
| ECB JSON endpoint differs from SDMX docs | 2 | Start with known working URL; mock in tests |
| Registry v0.4.0 has fields not in skeleton model | 1 | K-8 fix adds all missing fields with defaults |

## Validation Checkpoint (from PRD)

Before shipping Cycle-035:
- [ ] All existing fixtures still validate (no regression)
- [ ] At least 3 free sources producing real evidence bundles with valid receipts
- [ ] Receipt determinism proven (same query, same hash)
- [ ] Corroboration runner correctly deduplicates by upstream_id
- [ ] Counter-signal checker evaluates at least 3 of 11 classes
- [ ] CLI can run a full oracle evaluation and output a scored bundle
- [ ] Bundle hash (SHA-256 of canonical JSON) matches certificate schema
