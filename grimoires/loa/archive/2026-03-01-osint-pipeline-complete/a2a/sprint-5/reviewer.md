# Sprint 5 (Cycle-002 Sprint 2) — Implementation Report

**Sprint:** Pipeline Engine
**Global ID:** sprint-5
**Date:** 2026-03-01
**Tests:** 150 passed (OSINT), 35 passed (theatre regression)

---

## Files Created (8)

| File | Lines | Purpose |
|------|-------|---------|
| `osint_pipeline/engine/collection_runner.py` | 207 | Stage 1 Orchestrator — parallel collection via ThreadPoolExecutor |
| `osint_pipeline/engine/corroboration.py` | 124 | Stage 2 — independence dedup, time window, group counting |
| `osint_pipeline/engine/counter_signal.py` | 178 | Stage 2b — 11 signal classes, GapKind handling |
| `osint_pipeline/engine/scorer.py` | 177 | Stage 3 — 5 criteria, weighted composite, bundle hash (K-4) |
| `osint_pipeline/collectors/sec_edgar.py` | 136 | SEC EDGAR EFTS collector (US, official_gov) |
| `osint_pipeline/collectors/ecb_sdmx.py` | 135 | ECB Data API collector (EU, market_data) |
| `tests/osint_pipeline/test_collection_runner.py` | 235 | 13 tests: parallel, timeout, filtering, gaps, sequential |
| `tests/osint_pipeline/test_corroboration.py` | 179 | 10 tests: dedup, window, groups, role filter, evaluate_all |
| `tests/osint_pipeline/test_counter_signal.py` | 175 | 11 tests: 11 classes, pass/fail, GapKind, multi-class |
| `tests/osint_pipeline/test_scorer.py` | 211 | 16 tests: criteria, composite, hash, coverage, assembly |
| `tests/osint_pipeline/test_collectors.py` | 225 | 17 tests: SEC init/build/extract/collect, ECB init/build/extract/collect |

## Files Modified (2)

| File | Change |
|------|--------|
| `osint_pipeline/engine/__init__.py` | Note about no re-export (avoids circular import) |
| `osint_pipeline/collectors/__init__.py` | Added re-exports for SEC EDGAR and ECB collectors |

---

## Task Completion

### T2.1: `engine/collection_runner.py` — Stage 1 Orchestrator
- [x] `CollectionRunner.__init__` accepts collectors, max_workers, timeout_budget_seconds
- [x] `run()` executes via ThreadPoolExecutor
- [x] `required_source_ids` filtering works
- [x] `allow_gaps_for` propagates to GapReport.allow_gap
- [x] Failed/timed-out collections produce GapReport entries (Concern 6)
- [x] Missing collectors logged + gap produced
- [x] `run_sequential()` mode for debugging
- [x] `close_all()` closes all collector clients
- [x] Returns OracleCollectionSummary with correct counts
- [x] Python 3.9 compatibility: catches both builtin and concurrent.futures TimeoutError

### T2.2: `collectors/sec_edgar.py` — SEC EDGAR EFTS Collector
- [x] `source_id = "sec_edgar"` (matches registry)
- [x] `jurisdiction = "US"`, `source_group = "official_gov"`
- [x] `resolution_role = "primary_evidence"`
- [x] `independence_upstream_id = "us_sec_edgar_backend"` (matches registry)
- [x] User-Agent header from config (SEC requires email-based User-Agent)
- [x] `build_request()` constructs EFTS search URL with date range, form type
- [x] `extract()` parses SEC JSON response with filing hits
- [x] Raises ValueError if User-Agent not configured

### T2.3: `collectors/ecb_sdmx.py` — ECB SDW Collector
- [x] `source_id = "ecb_data_api"` (matches registry)
- [x] `jurisdiction = "EU"`, `source_group = "market_data"`
- [x] `resolution_role = "primary_evidence"` (matches registry)
- [x] `independence_upstream_id = "eu_ecb_sdw_backend"` (matches registry)
- [x] No auth required
- [x] `build_request()` constructs ECB data API URL with dataflow/series_key
- [x] `extract()` parses SDMX-JSON response with observations
- [x] Uses JSON format endpoint (jsondata)

### T2.4: `engine/corroboration.py` — Stage 2 Corroboration Engine
- [x] `evaluate()` excludes primary bundle by bundle_id
- [x] Filters by resolution_role (secondary_corroboration, primary_evidence)
- [x] Deduplicates by independence_upstream_id (first seen wins)
- [x] Excludes candidates sharing upstream with primary
- [x] Time window check: |delta_t| <= window * 1000 ms
- [x] Counts distinct source_groups differing from primary's
- [x] `.passed` when distinct_groups >= corroboration_minimum
- [x] `evaluate_all()` returns one result per primary_evidence bundle
- [x] excluded_by_dedup and outside_window lists populated

### T2.5: `engine/counter_signal.py` — Stage 2b Counter-Signal Checker
- [x] COUNTER_SIGNAL_CLASSES contains all 11 classes
- [x] `evaluate()` indexes bundles by query_context["counter_signal_class"]
- [x] Gaps indexed by source_group
- [x] Bundles present: checked=True, checks structured_extract["counter_signal_detected"]
- [x] Only gaps: SIGNAL_ABSENCE -> checked=True (Concern 2), INTELLIGENCE_GAP -> checked=False
- [x] No source: checked=False, "No source configured"
- [x] allow_gap per-class from constructor parameter
- [x] Pass: checked=True AND (signal_found=False OR allow_gap=True)

### T2.6: `engine/scorer.py` — Stage 3 Scorer (K-4)
- [x] Accepts OracleCollectionSummary, CorroborationResult list, CounterSignalResult list
- [x] Computes 5 criteria: source_coverage(0.20), receipt_validity(0.15), corroboration_met(0.30), counter_signal_clear(0.15), confidence_weighted(0.20)
- [x] Weighted composite score clamped to [0.0, 1.0]
- [x] Bundle hash: SHA-256 of canonical JSON of sorted evidence bundles
- [x] Coverage percentage: (succeeded/attempted) * 100
- [x] Counter-signal summary: counter_signals_checked, counter_signals_found
- [x] Assembles complete OracleOutput with oracle_id (UUID), theatre_id, evaluated_at
- [x] Gap report populated from collection.gaps

### T2.7: Pipeline Engine Tests
- [x] test_collection_runner.py: parallel, timeout, gap reporting, source filtering, allow_gaps, sequential, close_all (13 tests)
- [x] test_corroboration.py: upstream dedup, shared upstream exclusion, time window, group counting, role filter, evaluate_all (10 tests)
- [x] test_counter_signal.py: 11 classes verified, checked+not-found, checked+found+allow_gap, intelligence_gap, signal_absence, multi-class (11 tests)
- [x] test_scorer.py: per-criterion, composite, custom weights, bundle hash determinism, coverage %, OracleOutput assembly (16 tests)
- [x] test_collectors.py: SEC EDGAR (init, build, extract, collect), ECB (init, build, extract, collect) with MockTransport (17 tests)
- [x] All tests use httpx.MockTransport (no live API calls)

---

## Registry Alignment

Sprint plan estimated source_ids differ from actual registry:
- SEC: `sec_edgar` (registry) vs `sec_edgar_efts` (sprint plan estimate)
- ECB: `ecb_data_api` (registry) vs `ecb_sdw` (sprint plan estimate)
- ECB role: `primary_evidence` (registry) vs `secondary_corroboration` (sprint plan estimate)

Implementation uses registry values as source of truth.

## Architectural Concerns Addressed

- **Concern 2 (Gap vs Absence):** CounterSignalChecker distinguishes GapKind.SIGNAL_ABSENCE (checked=True) from GapKind.INTELLIGENCE_GAP (checked=False)
- **Concern 6 (Timeout Gap Production):** CollectionRunner catches TimeoutError from as_completed, produces GapReport with INTELLIGENCE_GAP for unfinished futures

## Known Issue

- `engine/__init__.py` does NOT re-export CollectionRunner, CorroborationEngine, etc. to avoid circular import (engine -> collectors.base -> engine.canonical). Users import directly from submodules.
