# Sprint Plan: WorldMonitor OSINT Integration — Live Evidence Pipeline + Convergence Signals

**Cycle**: 011
**Sprints**: 2 (global: 21, 22)
**Date**: 2026-03-03
**PRD**: `grimoires/loa/prd.md` (v1.0)
**SDD**: `grimoires/loa/sdd.md` (v1.0)
**Depends on**: Cycle-010b (Engines + Heartbeat + VRF + Base Sepolia) — COMPLETED

---

## Cycle Overview

**Objective**: Connect WorldMonitor's three OSINT domain endpoints to Echelon's verification pipeline via a three-stage evidence architecture (Collection, Corroboration, Scoring). After Cycle-011, `p_reality` in the Paradox Engine's Logic Gap equation shifts from a stub value to a confidence-weighted composite score derived from real-world evidence with full provenance (HTTP transcript receipts).

**Team**: 1 AI engineer (Claude Code + Loa)

**Key Constraints**:
- WorldMonitor is NOT running locally — all tests use mock HTTP responses only
- In-memory only — no database persistence (continues 010a/010b pattern)
- Zero modifications to `backend/market/` modules
- Zero modifications to `backend/engines/paradox.py` — provider swap only
- `backend/engines/reality_signal.py` is the only file modified outside `backend/osint/`
- Python 3.9.6 compatibility (`from __future__ import annotations` for PEP 604)
- No new runtime dependencies (all stdlib: `dataclasses`, `hashlib`, `json`, `asyncio`, `enum`, `abc`)
- API contract (`worldmonitor_api_contract.py`) is single source of truth — no model duplication

---

## Sprint 1 — Evidence Pipeline Core + WorldMonitor Collector

**Global ID**: 21
**Goal**: Deliver the evidence collection layer. BaseCollector ABC with hash invariant enforcement, WorldMonitor three-domain collector, registry loader, collection runner with concurrent execution, and mock fixtures for all tests.
**Deliverables**: 10 source files + 5 test files + 4 fixture files + 1 conftest = 20 files
**Test target**: 20+ new tests, all existing tests unbroken
**New dependency**: None (httpx mocked only via unittest.mock or respx)

---

### Task 1: Evidence models

**File**: `backend/osint/models/evidence.py`

**Description**: `CollectionResult` dataclass wrapping the Pydantic `EvidenceBundle` in a stdlib dataclass for pipeline-internal use. Re-export all bundle shapes from the API contract (single source of truth). No model duplication.

**Implementation**:
- `CollectionResult` dataclass: `source_id` (str), `bundle` (EvidenceBundle | None), `raw_payload` (bytes), `fetch_duration_ms` (float), `success` (bool), `error` (str | None), `retrieved_at` (datetime | None)
- Re-exports from `worldmonitor_api_contract.py`: `EvidenceBundle`, `HTTPTranscriptReceipt`, `NormalisedEvent`, `NormalisedMeasure`, `GeoPoint`, `WMDomain`, `MeasureType`, `HealthStatus`
- `backend/osint/models/__init__.py` subpackage init

**Acceptance criteria**:
- [x] `CollectionResult` has all 7 fields with correct types
- [x] All 8 API contract types re-exported from `models/evidence.py`
- [x] `raw_payload` is `bytes` (not `dict`) for hash verification against exact wire bytes
- [x] Uses `from __future__ import annotations` for Python 3.9.6 compatibility

**Dependencies**: None

---

### Task 2: Canonical hashing

**File**: `backend/osint/canonical.py`

**Description**: Echelon Canonical JSON v0 (NOT RFC 8785) with SHA-256 content hashing. Two re-exports from API contract plus one new bytes-based content hash function.

**Implementation**:
- `canonical_json(obj)` — re-export from `worldmonitor_api_contract.py`, labelled as Echelon Canonical JSON v0 (sorted keys, compact separators, no ASCII escape)
- `compute_content_hash(raw_payload: bytes) -> str` — SHA-256 of raw response bytes. Intentionally different from API contract's dict-hashing version.
- `compute_receipt_hash(method, url, query, headers, body_hash) -> str` — re-export from API contract

**Acceptance criteria**:
- [x] `canonical_json()` produces sorted keys, compact separators, no ASCII escape
- [x] `compute_content_hash()` takes `bytes` and returns SHA-256 hex digest
- [x] `compute_receipt_hash()` re-export matches API contract original exactly
- [x] Echelon Canonical JSON v0 label documented in docstrings (not RFC 8785)

**Dependencies**: None

---

### Task 3: BaseCollector ABC

**File**: `backend/osint/collectors/base.py`

**Description**: Abstract base class defining the fetch-to-receipt contract. Two hash invariants enforced at the base class level. Subclasses implement `_fetch()` — the base class wraps it with integrity verification.

**Implementation** (per SDD SS4.3):
- `HashInvariantViolation(Exception)` — raised on hash mismatch
- `BaseCollector(ABC)`:
  - `source_id() -> str` — abstract, registry source_id
  - `_fetch(request, theatre_id) -> CollectionResult` — abstract, internal fetch
  - `fetch(request, theatre_id) -> CollectionResult` — public fetch with hash invariant enforcement
  - `_enforce_hash_invariants(result)` — verifies content_hash == SHA256(raw_payload) and receipt_hash
  - `health_check() -> HealthStatus` — abstract, returns HEALTHY/DEGRADED/UNAVAILABLE
- `backend/osint/collectors/__init__.py` subpackage init

**Acceptance criteria**:
- [x] Invariant 1: `receipt.content_hash == SHA256(raw_payload)` enforced
- [x] Invariant 2: `receipt.receipt_hash` verified against canonical transcript
- [x] Failed invariant converts result to `success=False` with descriptive error (no raise)
- [x] `_fetch()` is abstract — subclasses implement HTTP call + bundle construction
- [x] `health_check()` is abstract with `HealthStatus` return type

**Dependencies**: Tasks 1, 2

---

### Task 4: WorldMonitor collector

**File**: `backend/osint/collectors/worldmonitor.py`

**Description**: Three-domain collector implementing `BaseCollector`. One instance per WM domain per Theatre. HTTP POST to WM endpoints with retry logic and error handling.

**Implementation** (per SDD SS4.4):
- `WorldMonitorConfig` dataclass: `base_url` ("http://localhost:8080"), `timeout_s` (30.0), `version` ("v0.1.0"), `retry_count` (2), `retry_delay_s` (1.0)
- `_DOMAIN_ENDPOINTS` dict: INTELLIGENCE -> `/api/v1/intelligence/cii`, MARKET -> `/api/v1/market/snapshot`, MARITIME -> `/api/v1/maritime/anomaly`
- `_DOMAIN_SOURCE_IDS` dict: INTELLIGENCE -> `worldmonitor_cii`, MARKET -> `worldmonitor_finance`, MARITIME -> `worldmonitor_maritime`
- `_DOMAIN_SOURCE_GROUPS` dict: INTELLIGENCE -> `alt_data_behavioural`, MARKET -> `market_data`, MARITIME -> `maritime_ais`
- `WorldMonitorCollector(BaseCollector)`:
  - `__init__(domain, config)` — stores domain, config, endpoint, source_id, source_group
  - `source_id() -> str` — returns domain-specific source_id
  - `_fetch(request, theatre_id) -> CollectionResult` — HTTP POST with retry, builds EvidenceBundle + HTTPTranscriptReceipt
  - `health_check() -> HealthStatus` — GET /health, extract per-domain status

**Failure mode pinning**:
- HTTP 200: Normal `CollectionResult(success=True)`
- HTTP 5xx: Retry up to `retry_count`, all fail: `success=False`
- Connection refused / DNS: Same retry, health_check -> UNAVAILABLE
- Timeout: Single attempt timeout, then retry
- All WM down: All 3 `success=False`, `evidence_completeness=0.0`, Paradox dormant

**Acceptance criteria**:
- [x] Calls correct endpoint per domain (CII, market, maritime)
- [x] Produces valid `EvidenceBundle` with `HTTPTranscriptReceipt`
- [x] Handles timeout, HTTP errors, and malformed responses gracefully (no raise)
- [x] Retries on transient failure with configurable count and delay
- [x] Health check maps WM `HealthStatus` correctly
- [x] `WorldMonitorConfig` has all 5 fields with correct defaults

**Dependencies**: Tasks 1, 2, 3

---

### Task 5: Registry loader

**File**: `backend/osint/models/registry.py`

**Description**: Loads and queries the OSINT source registry JSON. Stateless — loads from disk on init. Structural validation for enum membership and invariant checks.

**Implementation** (per SDD SS4.5):
- `RegistrySource` dataclass: `source_id`, `display_name`, `source_group`, `resolution_role`, `independence_upstream_id`, `receipt_mode_minimum`, `world_monitor_domain` (optional), `priority_bucket` (default 1), `settlement_eligible` (default False), `jurisdiction` (optional)
- `RegistryLoader`:
  - `__init__(registry_path)` — loads JSON on init
  - `get_source(source_id) -> RegistrySource | None`
  - `get_sources_by_group(source_group) -> list[RegistrySource]`
  - `get_sources_by_domain(wm_domain) -> list[RegistrySource]`
  - `get_settlement_eligible() -> list[RegistrySource]`
  - `validate() -> list[str]` — checks enum membership, resolution_role validity, receipt_mode validity, settlement invariants, non-empty independence_upstream_id

**Acceptance criteria**:
- [x] Loads registry v0.3.2 JSON and populates RegistrySource instances
- [x] `get_source()` returns correct source by source_id
- [x] `get_sources_by_group()` filters by source_group enum value
- [x] `get_sources_by_domain()` filters by world_monitor_domain
- [x] `get_settlement_eligible()` returns settlement-eligible sources
- [x] `validate()` catches enum violations and settlement invariant breaches
- [x] `RegistrySource` has all 10 fields with correct types and defaults

**Dependencies**: None

---

### Task 6: Registry alignment check

**Description**: Verify the 3 WorldMonitor source entries in registry v0.3.2 carry the correct field values. Patch if misaligned.

**Alignment requirements**:

| source_id | source_group | resolution_role | world_monitor_domain | independence_upstream_id | receipt_mode_minimum |
|-----------|-------------|----------------|---------------------|------------------------|---------------------|
| `worldmonitor_cii` | `alt_data_behavioural` | `primary_evidence` | `intelligence` | `worldmonitor` | `http_transcript` |
| `worldmonitor_finance` | `market_data` | `primary_evidence` | `market` | `worldmonitor` | `http_transcript` |
| `worldmonitor_maritime` | `maritime_ais` | `primary_evidence` | `maritime` | `worldmonitor` | `http_transcript` |

**Critical**: All 3 share `independence_upstream_id: worldmonitor` because WorldMonitor is a single aggregator. Despite distinct `source_group` values, they are not independent corroborators.

**Acceptance criteria**:
- [x] All 3 WM source entries verified aligned with API contract
- [x] `independence_upstream_id` is `worldmonitor` for all 3 entries
- [x] `resolution_role` is `primary_evidence` for all 3 entries
- [x] `receipt_mode_minimum` is `http_transcript` for all 3 entries
- [x] Registry JSON patched if any field is misaligned

**Dependencies**: Task 5

---

### Task 7: Collection runner

**File**: `backend/osint/engine/collection_runner.py`

**Description**: Orchestrates concurrent collector execution per Theatre `oracle_config`. Uses `asyncio.gather()` with per-collector timeout. Handles partial failure gracefully.

**Implementation** (per SDD SS4.6):
- `CollectionPlan` dataclass: `theatre_id`, `sources` (list of source_ids), `evaluation_window` (tuple[datetime, datetime]), `geo` (GeoPoint | None), `timeout_s` (30.0)
- `CollectionRunner`:
  - `__init__(collectors: dict[str, BaseCollector])` — source_id to collector mapping
  - `build_plan(oracle_config, theatre_id) -> CollectionPlan` — derives plan from Theatre config, filters to WM sources only in 011
  - `collect(plan) -> list[CollectionResult]` — `asyncio.gather()` with `return_exceptions=False`, each collector wrapped in `asyncio.wait_for(timeout_s)`
  - `_collect_with_timeout(collector, plan) -> CollectionResult` — wraps fetch with timeout, returns failure result on TimeoutError
  - `_build_request(plan) -> dict` — builds request dict from CollectionPlan fields
  - `_missing_collector_result(source_id) -> CollectionResult` — failure result for unregistered source
- `backend/osint/engine/__init__.py` subpackage init

**Acceptance criteria**:
- [x] Collectors run concurrently via `asyncio.gather()`
- [x] Per-collector timeout via `asyncio.wait_for()` — one timeout does not cancel others
- [x] Partial failure: 1 of 3 fails, other 2 succeed — all 3 results returned
- [x] Timeout produces `CollectionResult(success=False, error="Timeout after Xs")`
- [x] No leaked asyncio tasks on collection failure
- [x] `build_plan()` correctly derives plan from Theatre `oracle_config`
- [x] Missing collector produces failure result (not raise)

**Dependencies**: Tasks 1, 3, 4

---

### Task 8: Mock WM response fixtures

**Files**:
- `backend/osint/tests/fixtures/wm_cii_response.json`
- `backend/osint/tests/fixtures/wm_market_response.json`
- `backend/osint/tests/fixtures/wm_maritime_response.json`
- `backend/osint/tests/fixtures/wm_error_responses.json`
- `backend/osint/tests/__init__.py`
- `backend/osint/tests/conftest.py`

**Description**: Generate mock JSON fixtures from Pydantic v2 schemas in `worldmonitor_api_contract.py`. Fixtures exercise normal and edge-case payloads. Shared conftest with fixture loaders and common test utilities.

**Implementation**:
- `wm_cii_response.json` — valid CII endpoint response from `CIIResponse` schema
- `wm_market_response.json` — valid market snapshot response from `MarketSnapshotResponse` schema
- `wm_maritime_response.json` — valid maritime anomaly response from `MaritimeAnomalyResponse` schema
- `wm_error_responses.json` — error responses: HTTP 500, HTTP 503, timeout simulation, malformed JSON
- `conftest.py` — pytest fixtures for loading mock responses, creating WorldMonitorConfig, creating test collectors

**Acceptance criteria**:
- [x] All 3 normal response fixtures are valid against Pydantic v2 schemas
- [x] Error response fixture covers 5xx, timeout, and malformed JSON
- [x] Fixtures include `NormalisedEvent`, `EvidenceBundle`, `HTTPTranscriptReceipt` with realistic data
- [x] `conftest.py` provides shared fixtures for all Sprint 1 test files
- [x] All tests consume fixtures via mock — no real HTTP calls

**Dependencies**: Tasks 1, 4

---

### Task 9: Canonical hashing tests

**File**: `backend/osint/tests/test_canonical.py`

**Description**: Unit tests for canonical hashing determinism, edge cases, and cross-verification against API contract utility functions.

**Tests** (~5+):
1. `test_canonical_json_deterministic` — same input dict produces same output string
2. `test_canonical_json_sorted_keys` — keys sorted alphabetically
3. `test_canonical_json_compact_separators` — no spaces after `:` or `,`
4. `test_canonical_json_unicode` — Unicode preserved (no ASCII escape)
5. `test_canonical_json_nested` — nested dicts and lists sorted correctly
6. `test_content_hash_deterministic` — same bytes produce same hash
7. `test_content_hash_different_bytes` — different bytes produce different hash
8. `test_cross_verification_canonical_json` — output matches API contract `canonical_json()` exactly
9. `test_cross_verification_receipt_hash` — output matches API contract `compute_receipt_hash()` exactly

**Acceptance criteria**:
- [x] Determinism verified for `canonical_json()`, `compute_content_hash()`, `compute_receipt_hash()`
- [x] Edge cases: empty object, nested objects, Unicode characters
- [x] Cross-verification: re-exported wrappers produce identical output to API contract originals
- [x] `compute_content_hash(bytes)` is intentionally different from API contract's dict-based version — no equality assertion

**Dependencies**: Task 2

---

### Task 10: Receipt tests

**File**: `backend/osint/tests/test_receipt.py`

**Description**: Unit tests for HTTP transcript receipt generation, hash verification, and content hash verification against raw bytes.

**Tests** (~4+):
1. `test_receipt_hash_deterministic` — same HTTP transcript parameters produce same hash
2. `test_receipt_hash_different_inputs` — different parameters produce different hash
3. `test_content_hash_matches_raw_bytes` — `compute_content_hash(raw_bytes)` matches receipt content_hash
4. `test_content_hash_bytes_vs_dict_distinction` — bytes-based hash differs from dict-based API contract hash
5. `test_receipt_canonical_form` — receipt hash uses canonical HTTP transcript format

**Acceptance criteria**:
- [x] Receipt hash deterministic (same inputs, same hash)
- [x] Content hash verifiable against raw response bytes
- [x] Bytes-based content hash is distinct from dict-based API contract version
- [x] HTTP transcript canonical form follows spec v1.0

**Dependencies**: Tasks 2, 3

---

### Task 11: Collector tests

**File**: `backend/osint/tests/test_worldmonitor.py`

**Description**: Unit tests for WorldMonitor collector across all three domains against mock fixtures. Error scenarios, retry behaviour, health check.

**Tests** (~6+):
1. `test_fetch_cii_domain` — CII domain calls correct endpoint, produces valid EvidenceBundle
2. `test_fetch_market_domain` — market domain calls correct endpoint, produces valid EvidenceBundle
3. `test_fetch_maritime_domain` — maritime domain calls correct endpoint, produces valid EvidenceBundle
4. `test_fetch_timeout_handling` — timeout produces `CollectionResult(success=False)`, no raise
5. `test_fetch_http_500_error` — HTTP 500 retries and fails gracefully
6. `test_fetch_retry_behaviour` — retries configured count times with configured delay
7. `test_fetch_malformed_response` — malformed JSON produces `success=False`
8. `test_health_check_healthy` — health check returns HEALTHY for healthy WM
9. `test_health_check_unavailable` — connection error returns UNAVAILABLE
10. `test_source_id_per_domain` — correct source_id for each WM domain

**Acceptance criteria**:
- [x] All 3 domains (CII, market, maritime) tested against mock fixtures
- [x] Timeout, HTTP errors, and malformed responses handled without raise
- [x] Retry behaviour validated (correct count and delay)
- [x] Health check maps WM status correctly
- [x] All tests use mock HTTP — no real WM calls

**Dependencies**: Tasks 3, 4, 8

---

### Task 12: Collection runner tests

**File**: `backend/osint/tests/test_collection_runner.py`

**Description**: Async unit tests for CollectionRunner — concurrent execution, timeout enforcement, partial failure, and plan derivation.

**Tests** (~5+):
1. `test_concurrent_execution` — 3 collectors run concurrently (timing check)
2. `test_per_collector_timeout` — one collector times out, others succeed
3. `test_partial_failure` — 1 of 3 fails, 2 succeed — all 3 results returned
4. `test_plan_derivation` — `build_plan()` extracts sources, geo, timeout from oracle_config
5. `test_missing_collector` — unregistered source_id produces failure result
6. `test_all_collectors_fail` — all 3 fail, returns 3 failure results (no raise)
7. `test_no_leaked_tasks` — asyncio tasks properly cleaned up after completion

**Acceptance criteria**:
- [x] Concurrent execution verified via timing or mock ordering
- [x] Timeout isolation confirmed (one timeout does not cancel others)
- [x] Partial failure produces mixed success/failure results
- [x] Plan derivation from oracle_config correct
- [x] All tests use `pytest-asyncio` and mock collectors

**Dependencies**: Tasks 7, 8

---

### Task 13: Registry loader tests + package init

**Files**: `backend/osint/tests/test_registry_loader.py`, `backend/osint/__init__.py`

**Description**: Unit tests for RegistryLoader and package-level exports.

**Registry tests** (~4+):
1. `test_load_registry_json` — loads registry v0.3.2 JSON successfully
2. `test_get_source_by_id` — returns correct RegistrySource for valid source_id
3. `test_get_source_not_found` — returns None for invalid source_id
4. `test_get_sources_by_group` — filters by source_group correctly
5. `test_get_sources_by_domain` — filters by world_monitor_domain
6. `test_get_settlement_eligible` — returns only settlement-eligible sources
7. `test_validate_catches_enum_violation` — invalid source_group caught
8. `test_validate_catches_settlement_invariant` — settlement-eligible without http_transcript caught
9. `test_wm_entry_alignment` — 3 WM entries have correct fields (integration with Task 6)

**`__init__.py` exports**: All public symbols from all Sprint 1 modules.

**Acceptance criteria**:
- [x] Registry loads from JSON and populates RegistrySource instances
- [x] All query methods return correct results
- [x] Validation catches enum violations and settlement invariant breaches
- [x] WM entry alignment verified
- [x] `backend/osint/__init__.py` exports all public types
- [x] No modifications to `backend/market/` or `backend/engines/` modules

**Dependencies**: Tasks 5, 6, 8

---

## Task Dependency Graph (Sprint 1)

```
Task 1 (evidence models) ─────────┐
Task 2 (canonical hashing) ────────┤
                                    ├── Task 3 (BaseCollector) ── Task 4 (WM collector) ──┐
Task 5 (registry loader) ──────────┤                                                       │
                                    │                                                       │
Task 6 (registry alignment) ◀── Task 5                                                    │
                                    │                                                       │
Task 8 (fixtures + conftest) ◀── Tasks 1, 4                                               │
                                    │                                                       │
Task 7 (collection runner) ◀── Tasks 1, 3, 4                                              │
                                    │                                                       │
Task 9 (canonical tests) ◀── Task 2                                                       │
Task 10 (receipt tests) ◀── Tasks 2, 3                                                    │
Task 11 (collector tests) ◀── Tasks 3, 4, 8                                               │
Task 12 (runner tests) ◀── Tasks 7, 8                                                     │
Task 13 (registry tests + init) ◀── Tasks 5, 6, 8 ────────────────────────────────────────┘
```

---

## Implementation Order (Sprint 1)

| Order | Task | Why This Order |
|-------|------|----------------|
| 1 | Task 1: Evidence models | Foundation dataclass, re-exports needed by everything |
| 2 | Task 2: Canonical hashing | Hashing utilities needed by BaseCollector |
| 3 | Task 5: Registry loader | Independent from collector chain, needed for alignment |
| 4 | Task 3: BaseCollector ABC | Defines collector contract, depends on models + hashing |
| 5 | Task 4: WorldMonitor collector | Implements BaseCollector for WM domains |
| 6 | Task 6: Registry alignment | Verifies WM entries, depends on registry loader |
| 7 | Task 7: Collection runner | Orchestration layer, depends on collectors |
| 8 | Task 8: Mock fixtures + conftest | Test infrastructure for all test files |
| 9 | Task 9: Canonical hashing tests | Validates Task 2 |
| 10 | Task 10: Receipt tests | Validates Tasks 2, 3 |
| 11 | Task 11: Collector tests | Validates Tasks 3, 4 |
| 12 | Task 12: Collection runner tests | Validates Task 7 |
| 13 | Task 13: Registry tests + init | Validates Tasks 5, 6, final exports |

---

## Sprint 1 Success Criteria

From PRD SS10a:

- [ ] `canonical_json()` produces deterministic output (sorted keys, compact separators, no ASCII escape)
- [ ] `compute_content_hash()` and `compute_receipt_hash()` re-exports match API contract originals exactly
- [ ] `BaseCollector` enforces receipt invariants (content_hash = SHA-256 of raw response bytes, receipt_hash = SHA-256 of canonical transcript)
- [ ] WorldMonitor collector calls correct endpoint per domain (CII, market, maritime)
- [ ] WorldMonitor collector produces valid `EvidenceBundle` with `HTTPTranscriptReceipt`
- [ ] WorldMonitor collector handles timeout, HTTP errors, and malformed responses gracefully (no raise)
- [ ] WorldMonitor collector retries on transient failure (configurable count and delay)
- [ ] WorldMonitor health check maps WM `HealthStatus` correctly
- [ ] Registry loader loads v0.3.2 JSON and queries by source_id, source_group, WM domain
- [ ] Registry validation catches enum violations and settlement invariant breaches
- [ ] Collection runner executes collectors concurrently with per-collector timeout
- [ ] Collection runner handles partial failure (1 of 3 fails, other 2 succeed)
- [ ] Collection plan correctly derived from Theatre `oracle_config`
- [ ] 3 WM registry source entries verified aligned with API contract
- [ ] Mock WM response fixtures generated from Pydantic v2 schemas (CII, market, maritime, errors)
- [ ] All tests use mock HTTP responses only — no real WM endpoint calls
- [ ] No modifications to `backend/market/` or `backend/engines/` modules
- [ ] Scoped regression: all tests in `backend/market/`, `backend/engines/`, `backend/scoring/`, `backend/osint/` pass
- [ ] Pre-existing `theatre/` collection errors (29 import failures) excluded from regression baseline
- [ ] 20+ new Sprint 1 tests pass

---

## Sprint 2 — Corroboration + Scoring + Paradox Wiring + Convergence

**Global ID**: 22
**Goal**: Deliver the evidence quality layer and live Paradox wiring. Corroboration engine deduplicates by `independence_upstream_id` and enforces `corroboration_minimum_met` (always false in 011 with WM-only). Scorer produces `composite_score` that the Paradox Engine reads as `p_reality`. Geographic convergence detection aggregates multi-domain signals into auditable alerts. The integrity loop closes.
**Deliverables**: 4 source files + 6 test files + 2 modified files = 12 files
**Test target**: 20+ new tests
**Depends on**: Sprint 1 (Evidence Pipeline Core + WorldMonitor Collector)

---

### Task 1: Corroboration engine

**File**: `backend/osint/engine/corroboration.py`

**Description**: Stage 2 of the pipeline. Separates primary from secondary evidence by `resolution_role`, deduplicates by `independence_upstream_id`, counts distinct `source_groups`, evaluates `corroboration_minimum_met`. Produces audit trail of dedup decisions.

**Implementation** (per SDD SS4.7):
- `CorroborationResult` dataclass: `theatre_id`, `primary_bundles`, `corroborating_bundles` (deduplicated), `distinct_source_groups`, `corroboration_minimum`, `corroboration_met`, `dedup_log` (audit trail)
- `CorroborationEngine`:
  - `__init__(registry_loader)` — stores registry for metadata lookup
  - `evaluate(results, oracle_config) -> CorroborationResult` — full corroboration evaluation
  - `deduplicate_by_upstream_id(bundles) -> tuple[list[EvidenceBundle], list[str]]` — collapses bundles sharing `independence_upstream_id`, keeps strongest-confidence entry

**011 constraint — provisional corroboration**: All 3 WM endpoints share `independence_upstream_id: worldmonitor`. After dedup, only 1 entry remains. `corroboration_met` is always false. Scorer applies 0.7 factor.

**Acceptance criteria**:
- [x] Primary/secondary separation by `resolution_role` correct
- [x] Deduplication by `independence_upstream_id` collapses WM entries (3 -> 1)
- [x] Keeps strongest-confidence entry per upstream_id
- [x] `distinct_source_groups` counted after dedup
- [x] `corroboration_met = distinct_source_groups >= corroboration_minimum`
- [x] Dedup log records every dedup decision for audit trail
- [x] Provisional corroboration: WM-only = always `corroboration_met=false`

**Dependencies**: Sprint 1 complete

---

### Task 2: Counter-signal evaluator

**File**: `backend/osint/engine/counter_signal.py`

**Description**: Stage 2b — scaffolding-only in 011. Full interface and discount rule engine implemented, but all 11 counter-signal classes return `UNAVAILABLE` with `allow_gap=true` (no independent sources connected).

**Implementation** (per SDD SS4.8):
- `CounterSignalOutcome(str, Enum)`: ABSENT, PRESENT_DISCOUNTED, PRESENT_UNEXPLAINED, UNAVAILABLE
- `CounterSignalResult` dataclass: `signal_class`, `outcome`, `source_id` (optional), `detail`, `allow_gap` (default True)
- `COUNTER_SIGNAL_CLASSES` — list of 11 class names
- `CounterSignalEvaluator`:
  - `evaluate(collection_results, oracle_config) -> list[CounterSignalResult]` — returns 11 UNAVAILABLE results in 011
  - `check_criterion(results) -> tuple[bool, str]` — PASS if no PRESENT_UNEXPLAINED and all UNAVAILABLE have allow_gap=True

**011 scope**: UNAVAILABLE classified as INTELLIGENCE_GAP (not ABSENT). Criterion passes honestly under gap tolerance. Three classes documented as first targets for future sources: `infrastructure_outage`, `weather`, `financial_distress`.

**Acceptance criteria**:
- [x] `CounterSignalOutcome` enum has all 4 members
- [x] All 11 counter-signal classes defined
- [x] All 11 classes return UNAVAILABLE in 011
- [x] `check_criterion()`: UNAVAILABLE with `allow_gap=true` -> criterion PASS
- [x] `check_criterion()`: UNAVAILABLE with `allow_gap=false` -> criterion FAIL
- [x] `check_criterion()`: PRESENT_UNEXPLAINED -> criterion FAIL
- [x] UNAVAILABLE is INTELLIGENCE_GAP, not ABSENT

**Dependencies**: Sprint 1 complete

---

### Task 3: Scorer

**File**: `backend/osint/engine/scorer.py`

**Description**: Stage 3 — produces `composite_score` that becomes `p_reality` in the Paradox Engine. Per-criterion evaluation, confidence-weighted average, corroboration bonus, counter-signal penalty, evidence completeness factor, bundle hash via manifest pattern.

**Implementation** (per SDD SS4.9):
- `CriterionScore` dataclass: `criterion`, `passed`, `score`, `detail`
- `OracleOutput` dataclass: `theatre_id`, `composite_score` (0.0-1.0), `criterion_scores`, `evidence_bundles`, `corroboration_result`, `counter_signal_results`, `evidence_completeness`, `bundle_hash`, `scored_at`
- `Scorer`:
  - `CORROBORATION_MET_FACTOR = 1.0`, `CORROBORATION_UNMET_FACTOR = 0.7`
  - `COUNTER_SIGNAL_PASS_FACTOR = 1.0`, `COUNTER_SIGNAL_FAIL_FACTOR = 0.5`
  - `__init__(registry_loader)` — for priority_bucket weights
  - `score(corroboration, counter_signals, collection_results, oracle_config, theatre_id) -> OracleOutput`
  - `compute_composite(bundles, corroboration_met, counter_signal_pass, evidence_completeness) -> float`
  - `compute_bundle_hash(bundles) -> str` — manifest pattern: `{bundle_id: raw_payload_hash}`, sorted by bundle_id, `SHA256(canonical_json(manifest))`

**Composite score formula**:
```
composite_score = weighted_mean(confidence for primary bundles)
                x corroboration_factor (1.0 if met, 0.7 if not)
                x counter_signal_factor (1.0 if pass, 0.5 if fail)
                x evidence_completeness
```
Result clamped to [0.0, 1.0]. Weights from registry `priority_bucket`.

**Acceptance criteria**:
- [x] `composite_score` is confidence-weighted, clamped to [0.0, 1.0]
- [x] Corroboration factor: 1.0 when met, 0.7 when not met
- [x] Counter-signal factor: 1.0 when pass, 0.5 when fail
- [x] `evidence_completeness` = count(successful) / count(required)
- [x] Empty bundles or zero completeness -> score 0.0
- [x] Bundle hash: manifest pattern, deterministic regardless of insertion order
- [x] `OracleOutput` has all 9 fields with correct types
- [x] `CriterionScore` produced for corroboration_minimum_met, counter_signal_checked

**Dependencies**: Tasks 1, 2

---

### Task 4: LiveOSINTRealityProvider

**File**: `backend/engines/reality_signal.py` (MODIFIED)

**Description**: Extends existing `reality_signal.py` with `LiveOSINTRealityProvider`. Full pipeline orchestration: collect -> corroborate -> evaluate counter-signals -> score -> return `RealitySignal`. Replaces 010b's stub for `osint` Theatres.

**Implementation** (per SDD SS4.10):
- Extend `RealitySignal` dataclass with optional `provider_version: str | None = None` and `evidence_completeness: float | None = None`
- `LiveOSINTRealityProvider(RealitySignalProvider)`:
  - `__init__(collection_runner, corroboration_engine, counter_signal_evaluator, scorer, oracle_config, max_staleness_s=300.0, provider_version="011.1")`
  - `get_signal(theatre_id) -> RealitySignal` — full pipeline execution, returns `RealitySignal` with:
    - `p_reality = composite_score` (or None if stale)
    - `evidence_bundle_hash = bundle_hash` from OracleOutput
    - `certificate_id` repurposed as `oracle_output_id = "{theatre_id}_{scored_at_ms}"`
    - `source_type = "osint"`
    - `provider_version = "011.1"`
    - `evidence_completeness` from OracleOutput
  - `_check_staleness(theatre_id) -> bool` — True if most recent output is older than `max_staleness_s`
  - `_build_oracle_output_id(theatre_id, scored_at) -> str`
  - `_last_output: dict[str, OracleOutput]` — per-theatre cache, overwritten each run

**Staleness protection**: If evidence older than `max_staleness_s` (default 300s), `p_reality=None`, Paradox skips scan.

**Acceptance criteria**:
- [x] `get_signal()` returns `RealitySignal` with `p_reality = composite_score`
- [x] `evidence_bundle_hash` matches `OracleOutput.bundle_hash`
- [x] `oracle_output_id` format: `"{theatre_id}_{scored_at_ms}"`
- [x] `source_type = "osint"`, `provider_version = "011.1"`
- [x] Staleness protection: `p_reality = None` when evidence stale
- [x] `RealitySignal` extended with `provider_version` and `evidence_completeness` (None defaults, backward compatible)
- [x] Existing providers (StubRealityProvider, DeterministicRealityProvider, OsintRealityProvider) unchanged

**Dependencies**: Tasks 1, 2, 3

---

### Task 5: Paradox wiring

**Description**: Inject `LiveOSINTRealityProvider` into Theatres with `logic_gap_source: "osint"`. Verify activation gate reads `evidence_completeness` from `RealitySignal`. No modification to `backend/engines/paradox.py`.

**Implementation**:
- Activation gate wiring: The `min_evidence_completeness` activation gate in `ParadoxConfig` reads `evidence_completeness` from `RealitySignal` (new optional field)
- Provider injection: Factory/configuration code creates `LiveOSINTRealityProvider` for osint Theatres
- Update `backend/engines/__init__.py` to export `LiveOSINTRealityProvider`

**Acceptance criteria**:
- [x] Paradox Engine receives live `p_reality` from `LiveOSINTRealityProvider` without `paradox.py` changes
- [x] Activation gate fires when `evidence_completeness >= min_evidence_completeness` threshold
- [x] Logic Gap = `abs(p_market - p_reality)` computed correctly with live `composite_score`
- [x] Provider swap only — no Paradox Engine code changes
- [x] `LiveOSINTRealityProvider` exported from `backend.engines`

**Dependencies**: Task 4

---

### Task 6: Convergence detector

**File**: `backend/osint/engine/convergence.py`

**Description**: Multi-domain signal co-location detection in 1 deg x 1 deg geographic cells. Bins NormalisedEvents, counts distinct WMDomain values per cell, fires alerts when threshold met within time window.

**Implementation** (per SDD SS4.11):
- `ConvergenceCell` dataclass: `lat_bin` (int), `lon_bin` (int), `event_types` (set of WMDomain strings), `events` (NormalisedEvent list), `convergence_score` (float)
- `ConvergenceAlert` dataclass: `alert_id`, `cell`, `theatre_id` (optional), `triggered_at`
- `ConvergenceDetector`:
  - `__init__(min_event_types=3, window_hours=24.0)`
  - `detect(bundles) -> list[ConvergenceAlert]` — bin by `(floor(lat), floor(lon))`, filter within window, fire when distinct types >= threshold
  - `match_theatres(alerts, active_theatres) -> list[ConvergenceAlert]` — match by geographic overlap
  - `_cell_key(lat, lon) -> tuple[int, int]` — `(floor(lat), floor(lon))`
  - `_compute_convergence_score(cell) -> float` — `(distinct_types / 3) x (1 + log2(event_count))`

**011 scope**: Alerts logged in-process only. No persistence, no MCP surface. No automatic Theatre creation. State lost on restart.

**Acceptance criteria**:
- [x] Events binned by 1 deg x 1 deg cell (`floor(lat)`, `floor(lon)`)
- [x] Alert fires when 3+ distinct WMDomain types co-locate within 24-hour window
- [x] Convergence score rewards type diversity and event density
- [x] Theatre matching identifies geographic overlap correctly
- [x] Single-domain or two-domain cells do not fire alerts
- [x] Empty bundle list produces no alerts
- [x] All events in convergence alerts carry full provenance (HTTP transcript receipt)

**Dependencies**: Sprint 1 complete

---

### Task 7: Corroboration tests

**File**: `backend/osint/tests/test_corroboration.py`

**Description**: Unit tests for CorroborationEngine — dedup correctness, minimum enforcement, provisional corroboration, audit trail.

**Tests** (~5+):
1. `test_dedup_same_upstream_id` — 3 WM bundles with `independence_upstream_id=worldmonitor` collapse to 1
2. `test_dedup_keeps_strongest_confidence` — highest-confidence entry retained
3. `test_corroboration_minimum_boundary` — minimum-1 = FAIL, minimum = PASS
4. `test_provisional_corroboration_wm_only` — WM-only = 1 distinct upstream, `corroboration_met=false`
5. `test_corroboration_with_independent_source` — synthetic non-WM bundle injected, `corroboration_met=true`
6. `test_dedup_log_audit_trail` — dedup decisions recorded
7. `test_primary_secondary_separation` — correct separation by `resolution_role`

**Acceptance criteria**:
- [x] Dedup correctness: all 3 WM endpoints collapse to 1 entry
- [x] Minimum enforcement at exact boundary
- [x] Provisional corroboration confirmed (WM-only = always false)
- [x] Audit trail records dedup decisions

**Dependencies**: Task 1

---

### Task 8: Counter-signal tests

**File**: `backend/osint/tests/test_counter_signal.py`

**Description**: Unit tests for CounterSignalEvaluator — all four outcome types, allow_gap toggle, INTELLIGENCE_GAP classification.

**Tests** (~4+):
1. `test_all_unavailable_in_011` — all 11 classes return UNAVAILABLE
2. `test_unavailable_allow_gap_true_passes` — criterion PASS when all UNAVAILABLE with allow_gap=true
3. `test_unavailable_allow_gap_false_fails` — criterion FAIL when any UNAVAILABLE with allow_gap=false
4. `test_present_unexplained_fails` — criterion FAIL when any PRESENT_UNEXPLAINED
5. `test_absent_passes` — ABSENT outcome passes criterion
6. `test_present_discounted_passes` — PRESENT_DISCOUNTED outcome passes criterion
7. `test_intelligence_gap_classification` — UNAVAILABLE classified as INTELLIGENCE_GAP, not ABSENT

**Acceptance criteria**:
- [x] All 4 outcome types tested via synthetic fixtures
- [x] `allow_gap` toggle behaviour validated (true=PASS, false=FAIL)
- [x] All 11 classes confirmed UNAVAILABLE in 011
- [x] INTELLIGENCE_GAP classification verified

**Dependencies**: Task 2

---

### Task 9: Scorer tests

**File**: `backend/osint/tests/test_scorer.py`

**Description**: Unit tests for Scorer — composite score formula, corroboration penalty, counter-signal penalty, evidence completeness, bundle hash determinism.

**Tests** (~5+):
1. `test_composite_score_formula` — correct computation with known inputs
2. `test_corroboration_penalty` — score x 0.7 when `corroboration_met=false`
3. `test_counter_signal_penalty` — score x 0.5 when counter-signal fails
4. `test_evidence_completeness_zero` — `evidence_completeness=0.0` -> `composite_score=0.0`
5. `test_evidence_completeness_partial` — partial completeness reduces score proportionally
6. `test_composite_score_clamped` — result always in [0.0, 1.0]
7. `test_bundle_hash_deterministic` — same bundles (any order) produce same hash
8. `test_bundle_hash_different_bundles` — different bundles produce different hash
9. `test_weighted_mean_by_priority_bucket` — higher priority_bucket sources weighted more

**Acceptance criteria**:
- [x] Composite score formula verified with known inputs
- [x] Corroboration penalty (0.7) and counter-signal penalty (0.5) applied correctly
- [x] Zero completeness produces zero score
- [x] Bundle hash deterministic and order-independent
- [x] Score always clamped to [0.0, 1.0]

**Dependencies**: Task 3

---

### Task 10: Live reality tests

**File**: `backend/osint/tests/test_live_reality.py`

**Description**: End-to-end tests for `LiveOSINTRealityProvider` — mock WM responses through full pipeline to RealitySignal output.

**Tests** (~4+):
1. `test_get_signal_returns_reality_signal` — full pipeline: mock WM -> collect -> corroborate -> score -> RealitySignal
2. `test_p_reality_equals_composite_score` — `RealitySignal.p_reality` matches `OracleOutput.composite_score`
3. `test_evidence_bundle_hash_matches` — `RealitySignal.evidence_bundle_hash` matches `OracleOutput.bundle_hash`
4. `test_staleness_returns_none_p_reality` — stale evidence produces `p_reality=None`
5. `test_oracle_output_id_format` — format: `"{theatre_id}_{scored_at_ms}"`
6. `test_provider_version` — `RealitySignal.provider_version == "011.1"`
7. `test_evidence_completeness_propagated` — `evidence_completeness` from OracleOutput present in RealitySignal

**Acceptance criteria**:
- [x] End-to-end pipeline produces valid RealitySignal
- [x] p_reality matches composite_score
- [x] evidence_bundle_hash matches bundle_hash
- [x] Staleness protection works (p_reality=None when stale)
- [x] oracle_output_id and provider_version correct

**Dependencies**: Tasks 1, 2, 3, 4

---

### Task 11: Paradox wiring tests

**File**: `backend/osint/tests/test_paradox_wiring.py`

**Description**: Tests verifying Paradox Engine works with live `p_reality` from `LiveOSINTRealityProvider`. Activation gate, Logic Gap computation, circuit breaker interaction.

**Tests** (~4+):
1. `test_paradox_with_live_p_reality` — Paradox Engine scan with `LiveOSINTRealityProvider` produces valid LogicGapReading
2. `test_activation_gate_evidence_completeness` — gate fires when completeness crosses `min_evidence_completeness`
3. `test_activation_gate_below_threshold` — gate does not fire when completeness below threshold
4. `test_logic_gap_computed_correctly` — `abs(p_market - p_reality)` with live composite_score
5. `test_no_paradox_code_changes` — verify `paradox.py` is unmodified (hash check or import test)
6. `test_circuit_breaker_with_live_evidence` — divergent composite_score triggers appropriate action

**Acceptance criteria**:
- [x] Paradox Engine with LiveOSINTRealityProvider produces valid results
- [x] Activation gate fires at evidence_completeness threshold
- [x] Logic Gap computed correctly with live composite_score
- [x] No modifications to `paradox.py`
- [x] Circuit breaker actions deterministic with live evidence

**Dependencies**: Tasks 4, 5

---

### Task 12: Convergence tests

**File**: `backend/osint/tests/test_convergence.py`

**Description**: Unit tests for ConvergenceDetector — cell binning, domain counting, alert threshold, Theatre matching.

**Tests** (~4+):
1. `test_cell_binning` — events at (51.5, -0.1) bin to cell (51, -1)
2. `test_alert_threshold_3_types` — alert fires when 3+ distinct WMDomain types in cell
3. `test_no_alert_below_threshold` — 2 domain types does not fire alert
4. `test_single_domain_no_alert` — 1 domain type does not fire alert
5. `test_empty_bundles_no_alerts` — empty bundle list produces no alerts
6. `test_theatre_matching` — Theatre geo within cell bounds matches
7. `test_theatre_no_match` — Theatre geo outside cell bounds does not match
8. `test_convergence_score` — score rewards type diversity and event density
9. `test_time_window_filtering` — events outside 24-hour window excluded

**Acceptance criteria**:
- [x] Cell binning by `floor(lat)`, `floor(lon)` correct
- [x] Alert fires at exactly 3 distinct WMDomain types
- [x] Below-threshold cells do not fire alerts
- [x] Theatre matching by geographic overlap correct
- [x] Time window filtering excludes old events

**Dependencies**: Task 6

---

### Task 13: Integration test — full loop

**File**: `backend/osint/tests/test_paradox_wiring.py` (appended) or separate integration test

**Description**: End-to-end integration test: WM fetch -> evidence bundle -> corroboration -> scoring -> composite_score -> Paradox Logic Gap -> threshold evaluation -> Wing Flap recorded.

**Tests** (~2+):
1. `test_full_pipeline_to_paradox_wing_flap` — mock WM responses -> full pipeline -> Paradox scan -> Logic Gap reading -> threshold evaluation -> PARADOX Wing Flap if threshold crossed
2. `test_full_pipeline_wm_down` — all WM endpoints down -> `evidence_completeness=0.0` -> Paradox activation gate does not fire -> no spurious circuit breakers

**Acceptance criteria**:
- [x] Full loop: WM fetch through to Paradox Wing Flap
- [x] WM-down scenario: Paradox dormant, no spurious circuit breakers
- [x] No modifications to `backend/engines/paradox.py`
- [x] No modifications to `backend/market/` modules
- [x] All tests use mock HTTP responses only
- [x] Scoped regression: all tests in `backend/market/`, `backend/engines/`, `backend/scoring/`, `backend/osint/` pass
- [x] Pre-existing `theatre/` collection errors excluded from regression baseline
- [x] 20+ new Sprint 2 tests pass

**Dependencies**: All Sprint 2 tasks

---

## Task Dependency Graph (Sprint 2)

```
Sprint 1 (complete) ─────────────────────────────────────────────────┐
                                                                      │
Task 1 (corroboration) ──────────────────────────────────────────────┤
Task 2 (counter-signal) ─────────────────────────────────────────────┤
                                                                      ├── Task 3 (scorer) ── Task 4 (LiveOSINT) ── Task 5 (wiring)
Task 6 (convergence) ────────────────────────────────────────────────┤
                                                                      │
Task 7 (corroboration tests) ◀── Task 1                              │
Task 8 (counter-signal tests) ◀── Task 2                             │
Task 9 (scorer tests) ◀── Task 3                                     │
Task 10 (live reality tests) ◀── Tasks 1, 2, 3, 4                   │
Task 11 (paradox wiring tests) ◀── Tasks 4, 5                       │
Task 12 (convergence tests) ◀── Task 6                              │
Task 13 (integration test) ◀── All Sprint 2 tasks ──────────────────┘
```

---

## Implementation Order (Sprint 2)

| Order | Task | Why This Order |
|-------|------|----------------|
| 1 | Task 1: Corroboration engine | Foundation for scoring — dedup and minimum enforcement |
| 2 | Task 2: Counter-signal evaluator | Parallel with corroboration, feeds scorer |
| 3 | Task 6: Convergence detector | Independent — can be built in parallel |
| 4 | Task 3: Scorer | Depends on corroboration + counter-signal outputs |
| 5 | Task 4: LiveOSINTRealityProvider | Orchestrates full pipeline, depends on scorer |
| 6 | Task 5: Paradox wiring | Provider injection and activation gate wiring |
| 7 | Task 7: Corroboration tests | Validates Task 1 |
| 8 | Task 8: Counter-signal tests | Validates Task 2 |
| 9 | Task 9: Scorer tests | Validates Task 3 |
| 10 | Task 12: Convergence tests | Validates Task 6 |
| 11 | Task 10: Live reality tests | E2E pipeline validation |
| 12 | Task 11: Paradox wiring tests | Validates provider swap and activation gate |
| 13 | Task 13: Integration test | Full loop validation |

---

## Sprint 2 Success Criteria

From PRD SS10b:

- [x] Corroboration deduplicates by `independence_upstream_id` correctly (all 3 WM endpoints collapse to 1 entry)
- [x] `corroboration_minimum_met` evaluates at exact boundary (minimum - 1 = FAIL, minimum = PASS)
- [x] Provisional corroboration: WM-only = 1 distinct upstream, `corroboration_met=false`, 0.7 penalty applied
- [x] Counter-signal evaluator returns UNAVAILABLE for all 11 classes in 011 (scaffolding-only)
- [x] Counter-signal `UNAVAILABLE` with `allow_gap=true` does not cause criterion FAIL
- [x] Counter-signal `UNAVAILABLE` with `allow_gap=false` causes criterion FAIL
- [x] UNAVAILABLE classified as INTELLIGENCE_GAP (not ABSENT) per AC-1 GapKind semantics
- [x] `composite_score` is confidence-weighted, clamped to [0.0, 1.0]
- [x] Corroboration bonus and counter-signal penalty apply correctly
- [x] `evidence_completeness` = count(successful sources) / count(required sources)
- [x] Bundle hash uses manifest pattern, deterministic regardless of insertion order
- [x] `LiveOSINTRealityProvider.get_signal()` returns `RealitySignal` with `p_reality = composite_score`
- [x] `RealitySignal.evidence_bundle_hash` matches `OracleOutput.bundle_hash`
- [x] Paradox Engine receives live `p_reality` without code changes (provider swap only)
- [x] Activation gate fires when `evidence_completeness` crosses `min_evidence_completeness` threshold
- [x] Logic Gap = `abs(p_market - p_reality)` computed correctly with live `composite_score`
- [x] Staleness protection: `max_staleness_s` causes `p_reality = None` when evidence is stale
- [x] Convergence detector fires alert when 3+ event types co-locate in 1 deg x 1 deg cell within 24 hours
- [x] Convergence alerts carry full provenance (every event has HTTP transcript receipt)
- [x] Convergence Theatre matching correctly identifies geographic overlap
- [x] No modifications to `backend/engines/paradox.py` (provider interface unchanged from 010b)
- [x] No modifications to `backend/market/` modules
- [x] All tests use mock HTTP responses only
- [x] Scoped regression: all tests in `backend/market/`, `backend/engines/`, `backend/scoring/`, `backend/osint/` pass
- [x] Pre-existing `theatre/` collection errors excluded from regression baseline
- [x] 20+ new Sprint 2 tests pass

---

## Regression Targets

Scoped to four module paths:

```bash
python3 -m pytest backend/market/ backend/engines/ backend/scoring/ backend/osint/ -v
```

| Scope | Expected | Notes |
|-------|----------|-------|
| `backend/market/` | All pass | Zero modifications — 010a tests unchanged |
| `backend/engines/` | All pass | Only `reality_signal.py` modified — `LiveOSINTRealityProvider` added, `RealitySignal` extended with optional fields (backward compatible) |
| `backend/scoring/` | All pass | No modifications (if directory exists) |
| `backend/osint/` | 40+ new tests pass | New package — all new tests |
| `theatre/` (29 errors) | EXCLUDED | Pre-existing import failures from Cycles 031-033, not this cycle's concern |

---

## Risk Assessment

From SDD SS11:

| Risk | Impact | Mitigation |
|------|--------|-----------|
| `httpx` import issues | Sprint 1 blocked | Fallback to `urllib3` or `aiohttp`. HTTP client internal to WorldMonitorCollector — swappable. |
| `asyncio.gather()` task leaks on timeout | Leaked tasks accumulate | `asyncio.wait_for()` per collector with proper cancellation handling |
| Pydantic v2 schema drift | API contract models diverge | Single source of truth in `worldmonitor_api_contract.py` — all models re-exported, never duplicated |
| `RealitySignal` dataclass extension | Breaks 010b test expectations | New fields have `None` defaults — backward compatible. 010b tests unchanged. |
| Registry JSON format changes | `RegistryLoader` fails to parse | `validate()` method catches structural errors. Schema version checked on load. |
| Composite score edge cases | Division by zero, NaN | Guard clauses: empty bundles -> 0.0, zero weight -> 0.0, result clamped to [0.0, 1.0] |
| Convergence detector memory | Unbounded event accumulation | In-memory only, per-call scope. Each `detect()` call processes a finite bundle list. |
| `max_staleness_s` false negatives | Stale evidence treated as valid | Default 300s conservative. Configurable per Theatre. |

---

## Dependencies — What 010b Delivers That We Consume

| API | Purpose | Modification in 011 |
|-----|---------|---------------------|
| `RealitySignalProvider` (interface) | Abstract provider base — `get_signal()` contract | None (implemented by LiveOSINTRealityProvider) |
| `RealitySignal` (dataclass) | Return type from `get_signal()` | Extended: `provider_version`, `evidence_completeness` (optional, backward compatible) |
| `ParadoxEngine` (class) | Receives provider via constructor injection | None — provider swap only |
| `ParadoxConfig.activation_gate` | `min_evidence_completeness` gate | Reads `evidence_completeness` from RealitySignal |
| `LogicGapCalculator.compute()` | Receives live `p_reality` from composite_score | None |
| `ButterflyEngine` | Records PARADOX Wing Flaps | None |
| `EntropyEngine` | Logic Gap-scaled decay rates | None |
| `HeartbeatScheduler` | PARADOX scan at 30s cadence drives pipeline | None |
| Existing tests (447+ pipeline, 45+ market, 153+ engine) | Regression baseline | Must all pass |

---

## Verification Commands

```bash
# Sprint 1 OSINT tests only
python3 -m pytest backend/osint/tests/ -v

# Sprint 2 OSINT + wiring tests
python3 -m pytest backend/osint/tests/ -v

# Engine regression (010b tests must still pass)
python3 -m pytest backend/engines/tests/ -v

# Market regression (010a tests must still pass)
python3 -m pytest backend/market/tests/ -q

# Scoped regression (full)
python3 -m pytest backend/market/ backend/engines/ backend/scoring/ backend/osint/ -v

# Full test suite
python3 -m pytest -q
```

---

## File Manifest Summary

### Sprint 1 — 21 files

| File | Status | Purpose |
|------|--------|---------|
| `backend/osint/__init__.py` | NEW | Package exports |
| `backend/osint/canonical.py` | NEW | Echelon Canonical JSON v0, hashing |
| `backend/osint/models/__init__.py` | NEW | Models subpackage |
| `backend/osint/models/evidence.py` | NEW | CollectionResult, re-exports |
| `backend/osint/models/registry.py` | NEW | RegistryLoader, RegistrySource |
| `backend/osint/collectors/__init__.py` | NEW | Collectors subpackage |
| `backend/osint/collectors/base.py` | NEW | BaseCollector ABC |
| `backend/osint/collectors/worldmonitor.py` | NEW | WorldMonitorCollector (3 domains) |
| `backend/osint/engine/__init__.py` | NEW | Engine subpackage |
| `backend/osint/engine/collection_runner.py` | NEW | CollectionRunner |
| `backend/osint/tests/__init__.py` | NEW | Tests package |
| `backend/osint/tests/conftest.py` | NEW | Shared fixtures |
| `backend/osint/tests/fixtures/wm_cii_response.json` | NEW | Mock CII response |
| `backend/osint/tests/fixtures/wm_market_response.json` | NEW | Mock market response |
| `backend/osint/tests/fixtures/wm_maritime_response.json` | NEW | Mock maritime response |
| `backend/osint/tests/fixtures/wm_error_responses.json` | NEW | Mock error responses |
| `backend/osint/tests/test_canonical.py` | NEW | Hashing tests |
| `backend/osint/tests/test_receipt.py` | NEW | Receipt tests |
| `backend/osint/tests/test_worldmonitor.py` | NEW | Collector tests |
| `backend/osint/tests/test_collection_runner.py` | NEW | Runner tests |
| `backend/osint/tests/test_registry_loader.py` | NEW | Registry tests |

### Sprint 2 — 12 files

| File | Status | Purpose |
|------|--------|---------|
| `backend/osint/engine/corroboration.py` | NEW | CorroborationEngine |
| `backend/osint/engine/counter_signal.py` | NEW | CounterSignalEvaluator |
| `backend/osint/engine/scorer.py` | NEW | Scorer, OracleOutput |
| `backend/osint/engine/convergence.py` | NEW | ConvergenceDetector |
| `backend/osint/tests/test_corroboration.py` | NEW | Corroboration tests |
| `backend/osint/tests/test_counter_signal.py` | NEW | Counter-signal tests |
| `backend/osint/tests/test_scorer.py` | NEW | Scorer tests |
| `backend/osint/tests/test_convergence.py` | NEW | Convergence tests |
| `backend/osint/tests/test_live_reality.py` | NEW | LiveOSINTRealityProvider E2E tests |
| `backend/osint/tests/test_paradox_wiring.py` | NEW | Paradox wiring + integration tests |
| `backend/engines/reality_signal.py` | MODIFIED | LiveOSINTRealityProvider, RealitySignal extended |
| `backend/engines/__init__.py` | MODIFIED | LiveOSINTRealityProvider export |
