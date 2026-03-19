# Sprint Review — Sprint 118 (Cycle-038b Sprint 2)

**Cycle:** cycle-038b — External Theatre Orchestration
**Sprint:** 2 — Orchestrator Composition
**Global ID:** 118
**Date:** 19 March 2026
**Builder:** Loa

---

## Summary

Sprint 2 delivers the orchestrator composition service that composes all existing services (037d parse + plan, 037e execute, 038a bundle + candidates, 038b-sprint-1 enriched extraction) into a single `prepare_external_theatres()` call. This is the primary deliverable of cycle 038b.

---

## Files Created

| File | Purpose |
|------|---------|
| `backend/services/external_theatre_orchestrator.py` | Composition service: 1 public function + 3 private helpers |

## Files Modified

| File | Change |
|------|--------|
| `backend/tests/test_038b_external_orchestration.py` | Added 8 sprint-2 orchestrator composition tests (26 cumulative) |

---

## Implementation Details

### `external_theatre_orchestrator.py`

**Public function:**
- `prepare_external_theatres(request) -> ExternalTheatrePreparationResult` — main entry point that iterates theatre inputs, processes each through the full pipeline, generates cross-theatre candidates from successful bundles, and produces builder feedback reports.

**Private helpers:**
- `_prepare_single_theatre()` — 5-step pipeline per theatre: parse -> extract -> plan -> execute -> bundle. Wraps each step in error handling. Returns `(TheatrePreparationEntry, Optional[TheatreConstructMeta])`.
- `_planned_checks_to_dicts()` — Bridge function converting `PlannedCheck` dataclass instances to dicts for the runner (which uses `check.get("check_type")`).
- `_build_builder_feedback()` — Generates structured feedback with 3 categories (required/optional/extraction) and derives readiness (READY/DEGRADED/BLOCKED).

### Key Design Decisions

1. **None-vs-empty list for identity keys:** When `event_keys=[]` or `scope_keys=[]`, the orchestrator passes `None` to `build_comparison_bundle()` to trigger fallback behavior (template-ID keys). This matches SDD section 2.3, decision #4.

2. **Per-theatre error isolation:** Each theatre is processed in a try/except chain. Parse failures, extraction failures, and bundle building failures are captured in `TheatrePreparationEntry.error` without aborting the batch.

3. **Synchronous/pure:** No DB, no async, no network. All composed services are already synchronous pure functions.

4. **Feedback readiness derivation:** BLOCKED if extraction failed or no templates; DEGRADED if fallbacks were used (e.g., CORONA's `oracle_threshold_defaulted`); READY if no fallbacks (e.g., TREMOR has all metadata).

---

## Test Results

8 new tests added (26 cumulative):

| # | Test | Status |
|---|------|--------|
| 19 | `test_orchestrator_single_theatre` | PASSED |
| 20 | `test_orchestrator_paired_theatres` | PASSED |
| 21 | `test_orchestrator_shared_identity_threading` | PASSED |
| 22 | `test_orchestrator_no_keys_fallback` | PASSED |
| 23 | `test_orchestrator_error_propagation` | PASSED |
| 24 | `test_orchestrator_all_failures` | PASSED |
| 25 | `test_orchestrator_certificate_id_threading` | PASSED |
| 26 | `test_orchestrator_empty_request` | PASSED |

**All 26 tests pass** (7 sprint-0 + 11 sprint-1 + 8 sprint-2).

```
python3 -m pytest backend/tests/test_038b_external_orchestration.py -v
26 passed in 0.23s
```

---

## Sprint Exit Criteria

- [x] `backend/services/external_theatre_orchestrator.py` exists with `prepare_external_theatres()` and 3 private helpers
- [x] Sprint 0+1 tests still pass (18)
- [x] Sprint 2 tests pass (8 new, 26 cumulative)
- [x] `python -m pytest backend/tests/test_038b_external_orchestration.py -v` -- 26 passed

---

## Observations

1. **PlannedCheck -> dict bridge worked cleanly.** The 3-line `_planned_checks_to_dicts()` function maps `PlannedCheck` fields to the dict keys the runner expects. No fields were lost because the runner only reads `check_type` and `check_id`.

2. **Candidate generation depends on shared keys.** With no shared event_keys or scope_keys, TREMOR and CORONA get construct-specific template-ID fallbacks that do not overlap, producing zero candidates. This is correct behavior — cross-theatre comparison requires shared real-world identity.

3. **TREMOR feedback reports READY; CORONA reports DEGRADED.** TREMOR has all optional metadata (verification_checks, settlement_tiers, explicit source IDs, brier_type on templates). CORONA lacks verification_checks and settlement_tiers, triggering `oracle_threshold_defaulted` fallback.

4. **Both constructs produce DISPUTED bundles.** The enriched extractor's odd-index fail pattern guarantees at least 2 failed SETTLEMENT_ACCURACY checks per 5-template construct, producing `settlement_state="DISPUTED"` in bundles (rather than all-passing SETTLED from the old deterministic fixture path).

---

## Readiness for Sprint 3

Sprint 3 (038 scanner compatibility + builder feedback) can proceed. The orchestrator is fully functional and all 26 tests pass. Sprint 3 adds 8 more tests validating scanner input compatibility and feedback quality.
