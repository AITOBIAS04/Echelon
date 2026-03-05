# Implementation Report — Sprint 34 (local sprint-2)

**Cycle:** cycle-014c (Investigation Toolset Implementation)
**Sprint:** Counter-Signals + Monitor + Scanner + Resolver + Checker
**Date:** 2026-03-05

## Summary

All 6 tasks implemented. 25 new tests, all passing. Zero regressions.

## Task Completion

### Task 2.1: Investigation Counter-Signal Classes + Feed ✓

**File created:** `backend/investigation/counter_signals.py`

**Details:**
- `InvestigationCounterSignalClass` enum — 11 values (separate from pipeline counter-signals)
- `InvestigationCounterSignal` frozen Pydantic model (counter_signal_id, signal_class, detected_at, evidence_ref, material, resolution_impact, detection_method)
- `InvestigationCounterSignalFeed` class:
  - `log_counter_signal()` — sequential IDs (CS001, CS002, ...)
  - `get_summary()` — {checked, gaps, material_contradictions}
  - `get_detail()` — per-signal detail for certificate
  - Property: `signals`
- `_EVENT_DRIVEN_CLASSES` set for classes 10+11 (MARKET_DIVERGENCE, WITNESS_SOURCE_RECANTATION)
- Event-driven classes only count toward `checked` when explicitly logged

### Task 2.2: Commitment Monitor ✓

**File created:** `backend/investigation/commitment_monitor.py`

**Details:**
- `DriftType` enum — 5 values (ENTITY_RESTRUCTURE, CONTRACT_AMENDMENT, MARKET_RULE_CHANGE, REGULATORY_STATUS_CHANGE, JURISDICTION_CHANGE)
- `DriftImpact` enum — MATERIAL, NON_MATERIAL
- `DriftEvent` frozen Pydantic model (drift_id, drift_type, detected_at, original_value, new_value, evidence_ref, impact_assessment)
- `CommitmentMonitor` class:
  - `log_drift()` — sequential IDs (D001, D002, ...)
  - `has_material_drift()` — True if any event has MATERIAL impact
  - Property: `events`

### Task 2.3: Signal Scanner ✓

**File created:** `backend/investigation/signal_scanner.py`

**Details:**
- `DomainFilter` enum — 9 values
- `DOMAIN_FILTER_SOURCE_GROUPS` mapping (9 filters → OSINT registry source groups)
- `SourceQuery` frozen Pydantic model (source_id, source_group, query, result_count, access_tier, skipped, skip_reason)
- `Anomaly` frozen Pydantic model
- `DeltaBrief` frozen Pydantic model with content_hash (SHA-256 of canonical JSON)
- `SignalScanner` class:
  - `scan(subject)` — mock scan returning DeltaBrief
  - `active_source_groups` property — flattened deduplicated groups
  - `_build_manifest()` — scanner manifest with requested/resolved/skipped + access_tier_policy
- Access-tier policy: tier A only; tier B (satellite_imagery, flight_tracking) and C (cyber_threat) skipped with reason

### Task 2.4: Entity Resolver ✓

**File created:** `backend/investigation/entity_resolver.py`

**Details:**
- `SourceQueryRecord` frozen Pydantic model (source_id, source_name, query_time, result_found, fields_populated)
- `EntityQuery` frozen Pydantic model (entity_name, jurisdiction, registration_number)
- `EntityProfile` frozen Pydantic model (entity_id, entity_name, jurisdiction, registration_number, incorporation_date, registered_address, directors, filing_history_summary, gazette_notices, regulatory_entries, source_queries, profile_hash)
- `EntityResolver` class:
  - `resolve(query)` — stub returning mock Companies House + London Gazette profile
  - Profile hash = SHA-256 of canonical_json(entity data dict), excluding source_queries (operation metadata with non-deterministic timestamps)
  - Unknown entity handled gracefully (CH returns no results, LG still provides gazette_notices)

### Task 2.5: Investigation Corroboration Checker ✓

**File created:** `backend/investigation/corroboration_checker.py`

**Details:**
- `InvestigationCorroborationChecker` class:
  - `evaluate_claim(claim, checks)` → `ClaimStatus`
  - Hard invariant: SUPPORTED requires ≥2 distinct upstream_group with status='confirmed'
  - Any contradicted check → CONTRADICTED
  - Single confirmed upstream group → PARTIALLY_SUPPORTED
  - No confirmed groups → UNCONFIRMED
  - No override mechanism, no admin bypass
- Uses `CorroborationCheck` from `claim_graph.py` (reuses Sprint 1 model)

### Task 2.6: Sprint 2 Tests ✓

**Files created:**
- `backend/investigation/tests/test_counter_signals.py` — 6 tests
- `backend/investigation/tests/test_commitment_monitor.py` — 5 tests
- `backend/investigation/tests/test_signal_scanner.py` — 5 tests
- `backend/investigation/tests/test_entity_resolver.py` — 4 tests
- `backend/investigation/tests/test_corroboration_checker.py` — 5 tests

Counter-signal tests (6):
1. `test_log_counter_signal` ✓
2. `test_summary_counts` ✓
3. `test_market_divergence_only_counted_when_logged` ✓
4. `test_witness_recantation_only_counted_when_logged` ✓
5. `test_detail_format` ✓
6. `test_material_vs_non_material` ✓

Commitment monitor tests (5):
1. `test_log_drift_event` ✓
2. `test_has_material_drift_false` ✓
3. `test_has_material_drift_true` ✓
4. `test_drift_event_fields` ✓
5. `test_multiple_drift_events` ✓

Signal scanner tests (5):
1. `test_domain_filter_to_source_groups` ✓
2. `test_combined_filters` ✓
3. `test_deltabrief_hash_deterministic` ✓
4. `test_scan_with_mock_sources` ✓
5. `test_scanner_manifest_format` ✓

Entity resolver tests (4):
1. `test_resolve_companies_house` ✓
2. `test_profile_hash_deterministic` ✓
3. `test_source_query_record` ✓
4. `test_unknown_entity` ✓

Corroboration checker tests (5):
1. `test_supported_requires_two_independent_upstreams` ✓
2. `test_supported_with_two_independent_upstreams` ✓
3. `test_private_leak_only_remains_unconfirmed` ✓
4. `test_partial_status_with_single_upstream` ✓
5. `test_checker_output_deterministic` ✓

## Test Results

```
42 passed in 0.06s (17 Sprint 1 + 25 Sprint 2)
```

Broader regression check (924 relevant tests): 924 passed, 15 skipped, 0 failures.

## Files Created

| File | Lines | Purpose |
|------|-------|---------|
| `backend/investigation/counter_signals.py` | 119 | InvestigationCounterSignalClass + Feed |
| `backend/investigation/commitment_monitor.py` | 82 | CommitmentMonitor + DriftType/Event |
| `backend/investigation/signal_scanner.py` | 187 | SignalScanner + DomainFilter + DeltaBrief |
| `backend/investigation/entity_resolver.py` | 127 | EntityResolver + EntityProfile |
| `backend/investigation/corroboration_checker.py` | 52 | InvestigationCorroborationChecker |
| `backend/investigation/tests/test_counter_signals.py` | 126 | 6 tests |
| `backend/investigation/tests/test_commitment_monitor.py` | 97 | 5 tests |
| `backend/investigation/tests/test_signal_scanner.py` | 96 | 5 tests |
| `backend/investigation/tests/test_entity_resolver.py` | 97 | 4 tests |
| `backend/investigation/tests/test_corroboration_checker.py` | 100 | 5 tests |
