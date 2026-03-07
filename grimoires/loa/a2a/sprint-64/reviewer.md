# Implementation Report — Sprint 64 (Cycle-020 Sprint 4: Paradox Risk Orchestration)

**Sprint:** sprint-4 (global: sprint-64)
**Cycle:** cycle-020 — Scenario Pack Evaluator v2 + Paradox Risk Orchestration
**Date:** 2026-03-07
**Status:** IMPLEMENTATION COMPLETE

---

## Summary

Sprint 4 implements the paradox risk orchestrator with event-driven recompute across all 4 trigger paths and materiality detection for WebSocket emission decisions.

## Tasks Completed

### Task 4.1: trigger_recompute() Implementation
**Status:** DONE
**Files:** `backend/services/paradox_risk_orchestrator.py`

`trigger_recompute(db, theatre_id, trigger_reason, **factor_kwargs)`:
1. Loads theatre from DB
2. Evaluates risk using `ParadoxRiskEvaluator`
3. Compares old vs new level + factors for materiality
4. Persists new level/factors/timestamp to theatre
5. Attaches `_material`, `_old_level`, `_trigger_reason` metadata to assessment
6. Returns assessment (caller decides whether to emit WS)

Tests: `test_trigger_recompute_evaluates_risk`, `test_trigger_recompute_non_material`

### Task 4.2: Missing Theatre Handling
**Status:** DONE
**Files:** `backend/services/paradox_risk_orchestrator.py`

- Returns None if theatre not found in DB
- No exception, graceful degradation

Test: `test_trigger_recompute_missing_theatre`

### Task 4.3: All 4 Trigger Paths
**Status:** DONE
**Files:** `backend/services/paradox_risk_orchestrator.py`

Trigger paths verified via materiality:
1. **paradox_state_change** — active_paradox flip is material
2. **counter_signal_ingestion** — counter_signals crossing 0 boundary is material
3. **evidence_freshness_threshold** — same level change is NOT material (just staleness)
4. **certificate_policy_transition** — level change is always material

Test: `test_materiality_all_four_trigger_paths`

### Task 4.4: Counter-Signal Boundary Detection
**Status:** DONE
**Files:** `backend/services/paradox_risk_orchestrator.py`

- `material_counter_signals` crossing from positive to 0 is material (risk decreased)
- Crossing from 0 to positive is material (new counter-evidence)

Test: `test_materiality_counter_signal_boundary`

### Task 4.5: Factor Persistence
**Status:** DONE
**Files:** `backend/services/paradox_risk_orchestrator.py`

- Updates `theatre.paradox_risk_level`, `theatre.paradox_risk_factors_json`, `theatre.paradox_risk_updated_at`
- Async-compatible via `db.get()` and attribute assignment

### Task 4.6: Orchestrator Integration Test
**Status:** DONE
**Files:** `backend/tests/test_c020_integration.py`

Test `test_paradox_risk_ws_materiality` verifies material changes return assessment with `_material=True`.

## Test Results

```
backend/tests/test_c020_paradox_orchestrator.py — 5 tests PASSED
```

## Files Modified/Created

| File | Action | Lines |
|------|--------|-------|
| `backend/services/paradox_risk_orchestrator.py` | Modified | +60 (trigger_recompute) |
| `backend/tests/test_c020_paradox_orchestrator.py` | Created | ~120 (5 orchestrator tests) |
