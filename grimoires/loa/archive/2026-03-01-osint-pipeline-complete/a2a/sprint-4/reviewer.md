# Sprint 4 (Cycle-002 Sprint 1) — Implementation Report

> **Sprint:** Core Primitives & First Collector
> **Branch:** `feature/sprint-4-osint-core-primitives`
> **Date:** 2026-03-01
> **Tasks:** T1.1–T1.8 (8 tasks)
> **Test Results:** 73 passed, 0 failed (+ 35 theatre regression tests pass)

---

## Summary

Implemented the complete `osint_pipeline/` package at monorepo root with all models, canonical hashing (delegated to theatre engine), registry loader with K-fixes, BaseCollector ABC, Companies House collector, and comprehensive test suite. All 6 architectural concerns from the pre-sprint review are incorporated.

**Total:** 16 files created, 2,350 lines of code.

---

## Task Completion

### T1.1: Package Structure ✅

Created `osint_pipeline/` directory tree with all `__init__.py` files.

**Files:**
- `osint_pipeline/__init__.py` — Package docstring, `__version__ = "0.1.0"`
- `osint_pipeline/__main__.py` — Stub entry point
- `osint_pipeline/models/__init__.py` — Re-exports all model classes
- `osint_pipeline/engine/__init__.py` — Re-exports canonical functions
- `osint_pipeline/collectors/__init__.py` — Exports `BaseCollector`
- `tests/osint_pipeline/conftest.py` — Shared fixtures

**Note:** `tests/osint_pipeline/__init__.py` was initially created but **removed** to fix a namespace conflict — Python's import system treated both `./osint_pipeline/` and `./tests/osint_pipeline/` as competing packages. Without the `__init__.py`, pytest discovers conftest.py by convention.

**Acceptance criteria:** All met.

---

### T1.2: `engine/canonical.py` — RFC 8785 Delegation ✅

**File:** `osint_pipeline/engine/canonical.py` (146 lines)

**K-3 fix applied:** `canonical_json` is imported directly from `theatre.engine.canonical_json` — NOT reimplemented. The skeleton's bare `json.dumps` was replaced with a re-export:

```python
from theatre.engine.canonical_json import canonical_json  # noqa: F401
```

**Functions implemented:**
- `sha256_hex(data)` — Accepts str or bytes, returns 64-char hex
- `canonical_hash(obj)` — Composes `sha256_hex(canonical_json(obj))`
- `http_transcript_canonical()` — 6-field form: method, url, headers, status, body_hash, timestamp_ms
- `http_transcript_hash()` — SHA-256 of canonical form

**Architectural Concern 5 (Evidence Bundle Determinism) applied:**
- `CANONICAL_HEADER_ALLOWLIST = frozenset({"accept", "content-type", "user-agent"})` — volatile headers like `Authorization`, `Cookie`, `X-Request-Id` excluded
- URL query parameter normalisation: params sorted by key before reconstruction
- Trailing slash stripped from URLs

**Acceptance criteria:** All met.

---

### T1.3: `models/evidence.py` — Pydantic v2 Evidence Models ✅

**File:** `osint_pipeline/models/evidence.py` (282 lines)

**Enums:**
- `ReceiptMode` — NONE, HTTP_TRANSCRIPT, CRYPTOGRAPHIC_TRANSCRIPT, SIGNED_RECEIPT, WITNESS_QUORUM
- `CollectionStatus` — SUCCESS, TIMEOUT, NETWORK_ERROR, AUTH_FAILURE, RATE_LIMITED, NOT_FOUND, SOURCE_ERROR, PARSE_ERROR, VALIDATION_ERROR
- `FreshnessState` — FRESH, STALE, ERROR, UNKNOWN
- `GapKind` — SIGNAL_ABSENCE, INTELLIGENCE_GAP (Concern 2)

**Models:**
- `HTTPTranscriptReceipt` — Field validators enforce 64-char lowercase hex for `receipt_hash` and `response_body_hash`
- `EvidenceBundle` — All SDD fields: bundle_id (UUID auto), source_id, source_group, independence_upstream_id, resolution_role, jurisdiction, raw_payload_hash, raw_payload_size_bytes, receipt, structured_extract, confidence_score (0.0–1.0), receipt_mode, collected_at
- `CollectionResult` — `.succeeded` property (status==SUCCESS AND bundle not None)
- `GapReport` — With `gap_kind` field (default INTELLIGENCE_GAP)
- `OracleCollectionSummary` — `.coverage_ratio`, `.distinct_upstream_count`, `.upstream_dedup_map`

**Architectural concerns applied:**
- Concern 1: `distinct_upstream_count` and `upstream_dedup_map` properties
- Concern 2: `GapKind` enum with `gap_kind` field on `GapReport`
- Concern 3: `RECEIPT_MODE_ORDER` list and `meets_receipt_minimum()` function

**Acceptance criteria:** All met.

---

### T1.4: `models/registry.py` — Registry Loader ✅

**File:** `osint_pipeline/models/registry.py` (177 lines)

**K-fixes applied:**
- **K-1:** `free_public_sources()` operator precedence corrected — `cost_model == "free"` and `settlement_eligible` checks properly combined
- **K-2:** `cost_model` field added to `RegistrySource`
- **K-7:** `from_file()` validates `version == "0.4.0"`, raises `ValueError` on mismatch
- **K-8:** All 26 registry fields present: `source_name`, `replayability`, `legal_risk`, `rate_limit_notes`, `gap_policy_default`, `evidence_capture`, `notes`, `theatre_families`

**Query methods:**
- `get(source_id)` — Returns source or None
- `exists(source_id)` / `__contains__` — Membership check
- `settlement_eligible()` — Sources where `settlement_eligible == True`
- `by_jurisdiction(j)` — Filter by jurisdiction
- `free_public_sources()` — Free, settlement-eligible, public API with compatible auth
- `upstream_groups()` — Dict of upstream_id → source_id list
- `counter_signal_sources()` — Sources with `resolution_role == "counter_signal"`
- `all_sources()` — All sources as list
- `__len__` — Source count

**Verified:** Successfully loads `echelon_osint_source_registry_v0_4_0.json` (57 sources).

**Acceptance criteria:** All met.

---

### T1.5: `models/oracle_output.py` — Oracle Output Models ✅

**File:** `osint_pipeline/models/oracle_output.py` (151 lines)

**Models:**
- `CorroborationResult` — `.passed` property: `distinct_groups >= minimum_groups`
- `CounterSignalResult` — `.passed` property: `checked AND (NOT signal_found OR allow_gap)`
- `CriterionScore` — Score bounds [0.0, 1.0]
- `OracleOutput` — `all_criteria_passed`, `sources_with_gaps` properties

**Acceptance criteria:** All met.

---

### T1.6: `collectors/base.py` — BaseCollector ABC ✅

**File:** `osint_pipeline/collectors/base.py` (348 lines)

**Abstract interface:**
- Properties: `source_id`, `source_group`, `independence_upstream_id`, `resolution_role`, `jurisdiction`
- Methods: `build_request(query_context)`, `extract(raw_body, status_code, query_context)`

**Concrete `collect()` orchestration:**
1. Build request via `build_request()`
2. HTTP fetch via lazy-initialised `httpx.Client` (30s timeout)
3. Receipt generation via `http_transcript_hash()`
4. Extract via `extract()`
5. Bundle assembly

**Error mapping:**
- 401/403 → AUTH_FAILURE
- 429 → RATE_LIMITED
- 404 → NOT_FOUND
- 5xx → SOURCE_ERROR
- `httpx.TimeoutException` → TIMEOUT
- `httpx.ConnectError` → NETWORK_ERROR

**Architectural concerns applied:**
- Concern 3: `validate_receipt_mode(registry_source)` — Rejects collectors whose `RECEIPT_MODE` is below the registry minimum
- Concern 4: `should_cap_confidence()` / `FREE_SOURCE_CONFIDENCE_CAP = 0.7` — Caps confidence for `portal_scrape` or `latest_only` sources

**Other features:**
- Context manager support (`__enter__`/`__exit__`)
- `to_gap_report()` converts failed results to `GapReport`
- `close()` shuts down httpx client
- `assess_freshness()` returns FRESH on success, ERROR on error extracts

**Acceptance criteria:** All met.

---

### T1.7: `collectors/companies_house.py` — First Collector ✅

**File:** `osint_pipeline/collectors/companies_house.py` (239 lines)

**K-6 fix applied:** `independence_upstream_id` returns `"uk_companies_house_backend"` (skeleton had `"gb_companies_house_register"`).

**Properties:**
- `source_id = "companies_house_api"`
- `source_group = "official_gov"`
- `jurisdiction = "GB"`
- `resolution_role = "primary_evidence"`

**Endpoints (7):**
- Company profile (default)
- Filing history
- Officers
- Persons with significant control
- Charges
- Insolvency
- Company search

**Auth:** HTTP Basic with API key as username (empty password), encoded to Base64.

**Validation:** Raises `ValueError` if API key empty or missing from config.

**Acceptance criteria:** All met.

---

### T1.8: Core Tests ✅

**Test files (4):** 73 tests total, all passing.

| File | Tests | Coverage |
|------|-------|----------|
| `test_canonical.py` | 18 | RFC 8785 delegation, SHA-256, HTTP transcript form, determinism, header allowlist, URL param sort |
| `test_evidence_models.py` | 18 | Receipt validation, bundle creation, confidence bounds, succeeded property, gap kinds, independence dedup, receipt mode ordering |
| `test_registry.py` | 14 | Load fixture, version validation (K-7), all fields (K-8), free_public_sources (K-1), upstream groups, counter-signal |
| `test_companies_house.py` | 23 | Init validation, all 7 endpoints, auth header format, extract, collect with MockTransport (200/404/401/429/500), freshness |

**Regression verified:** 35 existing `tests/theatre/test_canonical_json.py` tests still pass.

**Acceptance criteria:** All met.

---

## Architectural Concerns Addressed

| # | Concern | Implementation |
|---|---------|---------------|
| 1 | Independence Accounting | `distinct_upstream_count` + `upstream_dedup_map` on `OracleCollectionSummary` |
| 2 | Gap vs Absence | `GapKind` enum (SIGNAL_ABSENCE / INTELLIGENCE_GAP) on `GapReport` |
| 3 | Receipt Mode Enforcement | `RECEIPT_MODE_ORDER` + `meets_receipt_minimum()` + `validate_receipt_mode()` on BaseCollector |
| 4 | Free Source Stability Guard | `FREE_SOURCE_CONFIDENCE_CAP` + `should_cap_confidence()` on BaseCollector |
| 5 | Evidence Bundle Determinism | `CANONICAL_HEADER_ALLOWLIST` + URL query param normalisation in canonical.py |
| 6 | Timeout Gap Production | Deferred to Sprint 2 (collection_runner.py not in Sprint 1 scope) |

---

## K-Fixes Applied

| K-Fix | Description | Location |
|-------|-------------|----------|
| K-1 | `free_public_sources()` operator precedence | `models/registry.py` |
| K-2 | Missing `cost_model` field | `models/registry.py` |
| K-3 | Delegate `canonical_json` to theatre engine | `engine/canonical.py` |
| K-6 | Companies House `independence_upstream_id` | `collectors/companies_house.py` |
| K-7 | Registry version validation | `models/registry.py` |
| K-8 | Missing registry fields (8 fields) | `models/registry.py` |

---

## Files Created

| File | Lines | Purpose |
|------|-------|---------|
| `osint_pipeline/__init__.py` | 7 | Package root |
| `osint_pipeline/__main__.py` | 13 | Entry point stub |
| `osint_pipeline/engine/__init__.py` | 9 | Engine re-exports |
| `osint_pipeline/engine/canonical.py` | 146 | RFC 8785 + HTTP transcript |
| `osint_pipeline/models/__init__.py` | 22 | Model re-exports |
| `osint_pipeline/models/evidence.py` | 282 | Evidence models |
| `osint_pipeline/models/registry.py` | 177 | Registry loader |
| `osint_pipeline/models/oracle_output.py` | 151 | Oracle output models |
| `osint_pipeline/collectors/__init__.py` | 3 | Collector re-exports |
| `osint_pipeline/collectors/base.py` | 348 | BaseCollector ABC |
| `osint_pipeline/collectors/companies_house.py` | 239 | Companies House collector |
| `tests/osint_pipeline/conftest.py` | 96 | Shared test fixtures |
| `tests/osint_pipeline/test_canonical.py` | 222 | Canonical hashing tests |
| `tests/osint_pipeline/test_evidence_models.py` | 209 | Evidence model tests |
| `tests/osint_pipeline/test_registry.py` | 150 | Registry loader tests |
| `tests/osint_pipeline/test_companies_house.py` | 256 | Companies House tests |
| **Total** | **2,330** | |

---

## Dependencies

- `pydantic >= 2.0` (Pydantic v2 models)
- `httpx >= 0.24` (HTTP client for collectors)
- `theatre.engine.canonical_json` (canonical JSON — already in monorepo)

Test dependencies: `pytest`, `eval_type_backport` (for Python < 3.10 Pydantic v2 compatibility).

---

## Known Limitations

1. **Concern 6 deferred:** Timeout gap production in `CollectionRunner` is Sprint 2 scope
2. **No `requirements.txt`/`pyproject.toml`:** Package metadata not yet created (Sprint 2 will establish proper packaging if needed)
3. **Python 3.9 compatibility:** `from __future__ import annotations` + `eval_type_backport` required for `str | None` syntax with Pydantic v2
