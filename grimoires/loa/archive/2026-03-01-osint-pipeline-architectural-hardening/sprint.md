# Sprint Plan: OSINT Pipeline Architectural Hardening

> **Cycle:** cycle-004
> **PRD:** `grimoires/loa/prd.md`
> **SDD:** `grimoires/loa/sdd.md`
> **Date:** 2026-03-01
> **Sprints:** 1 (global ID: 8)
> **Team:** Single AI agent
> **Target:** `~/Downloads/osint_pipeline/`

---

## Sprint 1: Architectural Concern Patches (7 tasks)

**Goal:** Implement all 6 architectural concerns + end-to-end integration test. No regressions.

**Build order:** AC-1 → AC-5 → AC-3 → AC-2 → AC-4 → AC-6 → AC-INT

**Rationale:**
- AC-1 before AC-6: timeout gap reports use GapKind.INTELLIGENCE_GAP which AC-1 defines
- AC-1 before AC-2: corroboration stage needs to distinguish real evidence bundles from gaps
- AC-3 before AC-4: scorer needs to know whether receipt met or exceeded minimum to apply the 0.95x penalty
- AC-5 is independent but ships early because everything downstream hashes evidence
- AC-INT last: validates all 6 concerns interact correctly

---

### Task 1: AC-1 — GapKind Semantics (Signal Absence vs Intelligence Gap)

**Files:**
- `collectors/base.py` — Update `to_gap_report()` to map CollectionStatus → GapKind (NOT_FOUND → SIGNAL_ABSENCE, all others → INTELLIGENCE_GAP). Update freshness mapping accordingly.

**Acceptance criteria:**
- [ ] `to_gap_report()` maps `CollectionStatus.NOT_FOUND` → `GapKind.SIGNAL_ABSENCE`
- [ ] `to_gap_report()` maps `CollectionStatus.TIMEOUT` → `GapKind.INTELLIGENCE_GAP`
- [ ] `to_gap_report()` maps `CollectionStatus.NETWORK_ERROR` → `GapKind.INTELLIGENCE_GAP`
- [ ] `to_gap_report()` maps `CollectionStatus.AUTH_FAILURE` → `GapKind.INTELLIGENCE_GAP`
- [ ] Signal absence gets `freshness=FreshnessState.NO_DATA`; intelligence gap gets `freshness=FreshnessState.ERROR`
- [ ] GapKind enum still has exactly 2 values (SIGNAL_ABSENCE, INTELLIGENCE_GAP)
- [ ] Existing tests `test_signal_absence_passes_counter_signal_check` and `test_intelligence_gap_fails_counter_signal_check` still pass

**Tests (new):**
- `test_gap_kind_enum_has_two_values`
- `test_to_gap_report_maps_not_found_to_signal_absence`
- `test_to_gap_report_maps_timeout_to_intelligence_gap`
- `test_to_gap_report_maps_network_error_to_intelligence_gap`

---

### Task 2: AC-5 — Canonical Hash Determinism (NFC + Float Precision)

**Files:**
- `engine/canonical.py` — Add `import unicodedata`. Add `_nfc_normalize_strings(obj)` recursive helper. Add `_rfc8785_float(f)` helper. Update `canonical_json()` to NFC-normalise strings and handle float precision per RFC 8785.
- `tests/test_canonical.py` — Update any affected assertions

**Acceptance criteria:**
- [ ] `canonical_json()` NFC-normalises all string values before serialisation
- [ ] Float values use shortest round-trip representation (RFC 8785 compliant)
- [ ] Combining characters (e.g., `e` + combining acute U+0301) produce same hash as precomposed (`é` U+00E9)
- [ ] `0.1 + 0.2` edge case produces deterministic output
- [ ] Known RFC 8785 test vector validates correctly
- [ ] All 12 existing canonical tests still pass

**Tests (new):**
- `test_canonical_json_nfc_normalisation`
- `test_canonical_json_float_precision`
- `test_canonical_json_rfc8785_test_vector`

---

### Task 3: AC-3 — Runner-Level Receipt Mode Enforcement

**Files:**
- `engine/collection_runner.py` — Add `registry_sources: dict[str, RegistrySource] | None = None` parameter to `__init__()`. In `run()`, before submitting to thread pool, validate each collector's `RECEIPT_MODE` against the registry source's `receipt_mode_minimum`. Collectors that fail are excluded from dispatch and produce a GapReport with `reason=CollectionStatus.SOURCE_ERROR`.

**Acceptance criteria:**
- [ ] `CollectionRunner.__init__()` accepts optional `registry_sources` parameter (defaults to `None`)
- [ ] Before dispatching to thread pool, runner checks `meets_receipt_minimum(collector.RECEIPT_MODE, registry_minimum)` for each collector with a registry source
- [ ] Collectors that fail receipt mode check are excluded from dispatch and produce a GapReport
- [ ] Collectors without a matching registry source are dispatched normally (backward compatible)
- [ ] Existing tests still pass (`registry_sources` defaults to `None`, no pre-check applied)

**Tests (new):**
- `test_runner_rejects_insufficient_receipt_mode`
- `test_runner_passes_sufficient_receipt_mode`

---

### Task 4: AC-2 — Upstream Independence Deduplication Naming

**Files:**
- `models/evidence.py` — Add `distinct_upstream_succeeded_count` as property alias on `OracleCollectionSummary`. Add test for null/empty upstream_id handling.

**Acceptance criteria:**
- [ ] `OracleCollectionSummary.distinct_upstream_succeeded_count` returns same value as `distinct_upstream_count`
- [ ] Null/empty string upstream_id values each count as distinct (no false dedup collisions)
- [ ] Existing test `test_distinct_upstream_count_deduplicates` still passes

**Tests (new):**
- `test_distinct_upstream_succeeded_count_alias`
- `test_null_upstream_id_counts_independently`

---

### Task 5: AC-4 — Confidence Capping (Move to Scorer)

**Depends on:** AC-3 (scorer needs to know whether receipt met or exceeded minimum for 0.95x penalty)

**Files:**
- `engine/scorer.py` — **NEW** `EvidenceScorer` class with penalty matrix and composite confidence
- `engine/__init__.py` — Export `EvidenceScorer`
- `collectors/base.py` — Remove `FREE_SOURCE_CONFIDENCE_CAP`, `should_cap_confidence()`, and confidence capping block from `collect()` (lines 271-274)
- `models/__init__.py` — Export any new types

**Acceptance criteria:**
- [ ] `EvidenceScorer.score_bundle(bundle, registry_source)` applies penalties multiplicatively:
  - `revision_policy=immutable` → 1.0 (no penalty)
  - `revision_policy=as_of_timestamp` → 0.95
  - `revision_policy=latest_only` → 0.80
  - `rate_limit_policy` indicating instability → 0.90
  - Receipt at minimum (not exceeding) → 0.95
- [ ] Single source cap at 0.95 (no individual source can claim 1.0)
- [ ] `composite_confidence(scored_bundles)` can exceed 0.95 with corroborated sources
- [ ] Formula: `1 - product(1 - score_i)`
- [ ] BaseCollector no longer applies confidence adjustments (`FREE_SOURCE_CONFIDENCE_CAP`, `should_cap_confidence` removed)
- [ ] Existing test `test_confidence_capped_for_latest_only` updated to use Scorer
- [ ] Existing test `test_confidence_not_capped_for_public_api_as_of_timestamp` updated

**Tests (new):**
- `test_scorer_immutable_no_penalty`
- `test_scorer_latest_only_080_penalty`
- `test_scorer_as_of_timestamp_095_penalty`
- `test_scorer_single_source_capped_095`
- `test_scorer_composite_exceeds_095`
- `test_scorer_receipt_at_minimum_penalty`
- `test_base_collector_no_confidence_cap`

---

### Task 6: AC-6 — Timeout Gap Reports (Structured Failure Classification)

**Depends on:** AC-1 (uses GapKind.INTELLIGENCE_GAP)

**Files:**
- `models/evidence.py` — Add `FailureMode` enum (7 values), `RETRIABLE_FAILURES` frozenset, `failure_mode: FailureMode | None` and `retriable: bool` fields on GapReport, `gap_count` and `gap_sources` computed properties on OracleCollectionSummary
- `models/__init__.py` — Export `FailureMode`, `RETRIABLE_FAILURES`
- `collectors/base.py` — Update `to_gap_report()` to map CollectionStatus → FailureMode and set `retriable` flag
- `engine/collection_runner.py` — Update timeout gap creation in `run()` to include `failure_mode=FailureMode.READ_TIMEOUT, retriable=True`

**Acceptance criteria:**
- [ ] `FailureMode` enum has 7 values: `connection_refused`, `dns_failure`, `tls_error`, `read_timeout`, `response_too_large`, `http_error_4xx`, `http_error_5xx`
- [ ] `RETRIABLE_FAILURES = frozenset({FailureMode.READ_TIMEOUT, FailureMode.HTTP_ERROR_5XX})`
- [ ] `GapReport` has `failure_mode: FailureMode | None` (default None, backward compatible) and `retriable: bool` (default False)
- [ ] `to_gap_report()` maps CollectionStatus → FailureMode: TIMEOUT→read_timeout, NETWORK_ERROR→connection_refused, SOURCE_ERROR→http_error_5xx, AUTH_FAILURE→http_error_4xx, RATE_LIMITED→http_error_4xx
- [ ] `retriable` set to `True` when `failure_mode in RETRIABLE_FAILURES`
- [ ] `OracleCollectionSummary.gap_count` returns `len(self.gaps)`
- [ ] `OracleCollectionSummary.gap_sources` returns `[g.source_id for g in self.gaps]`
- [ ] CollectionRunner timeout gap includes `failure_mode=FailureMode.READ_TIMEOUT, retriable=True`
- [ ] Existing test `test_timeout_produces_gap_reports` still passes
- [ ] No silent source drops: every configured source appears in output as EvidenceBundle or GapReport

**Tests (new):**
- `test_failure_mode_enum_values`
- `test_gap_report_failure_mode_and_retriable`
- `test_5xx_produces_retriable_gap`
- `test_dns_failure_not_retriable`
- `test_gap_count_and_gap_sources`
- `test_no_silent_source_drops`

---

### Task 7: AC-INT — End-to-End Pipeline Integration Test

**Depends on:** All of AC-1 through AC-6

**Files:**
- `tests/test_architectural_concerns.py` — Add `test_end_to_end_pipeline_integration`

**Test configuration:**
Configure a Theatre with 4 sources:
- **Source A** (`upstream_id="shared_reuters"`) — fast, returns success
- **Source B** (`upstream_id="shared_reuters"`) — fast, returns success (shares upstream with A)
- **Source C** — times out (simulated via `time.sleep(10)`)
- **Source D** — returns HTTP 404 (signal absence: successful query, no matching data)

Run the full 3-stage pipeline: Collection → Corroboration → Scoring.

**Acceptance criteria (all asserted in one test):**
- [ ] Upstream dedup collapses A+B to 1 logical corroborator (`distinct_upstream_succeeded_count` correct)
- [ ] Source C timeout produces a GapReport with `failure_mode=FailureMode.READ_TIMEOUT` and `retriable=True`
- [ ] Source D signal absence produces a GapReport with `gap_kind=GapKind.SIGNAL_ABSENCE` (NOT an intelligence gap)
- [ ] Receipt mode enforcement applied by runner (not only collector)
- [ ] Confidence capping applied by Scorer (not BaseCollector) — bundle confidence_score from extract() is raw (1.0)
- [ ] All evidence bundle hashes are deterministic (re-run produces identical hashes)
- [ ] No silent drops: every configured source appears in output (2 EvidenceBundles + 2 GapReports = 4 total)
- [ ] `OracleCollectionSummary.gap_count == 2` (Source C timeout + Source D signal absence gap)
- [ ] `OracleCollectionSummary.gap_sources` includes `"source_c"` and `"source_d"`
- [ ] `test_allow_gap_false_intelligence_gap_fails` — counter-signal with allow_gap=false + INTELLIGENCE_GAP fails
- [ ] `test_allow_gap_true_intelligence_gap_passes_degraded` — counter-signal with allow_gap=true + INTELLIGENCE_GAP passes

**Tests (new):**
- `test_end_to_end_pipeline_integration`
- `test_allow_gap_false_intelligence_gap_fails`
- `test_allow_gap_true_intelligence_gap_passes_degraded`

---

## Summary

| Task | Concern | Files Modified | New Tests |
|------|---------|----------------|-----------|
| T1 | AC-1 | base.py | 4 |
| T2 | AC-5 | canonical.py | 3 |
| T3 | AC-3 | collection_runner.py | 2 |
| T4 | AC-2 | evidence.py | 2 |
| T5 | AC-4 | scorer.py (new), base.py, __init__.py | 7 |
| T6 | AC-6 | evidence.py, base.py, collection_runner.py, __init__.py | 6 |
| T7 | AC-INT | test_architectural_concerns.py | 3 |
| **Total** | | **7 files (1 new)** | **27 new + 9 existing = 36** |

---

## Build Order

```
T1 (AC-1: GapKind)
 → T2 (AC-5: Canonical Hash)
   → T3 (AC-3: Receipt Enforcement)
     → T4 (AC-2: Upstream Dedup)
       → T5 (AC-4: Scorer)
         → T6 (AC-6: Timeout Gaps)
           → T7 (AC-INT: Integration)
```

**Dependency rationale:**
- T1→T6: AC-6 timeout gaps use `GapKind.INTELLIGENCE_GAP` defined in AC-1
- T1→T4: Corroboration needs to distinguish evidence bundles from gaps
- T2 early: All downstream hashing depends on canonical determinism
- T3→T5: Scorer applies 0.95x penalty based on whether receipt met or exceeded minimum (AC-3 enforcement)
- T7 last: Integration test validates all 6 concerns interact correctly
