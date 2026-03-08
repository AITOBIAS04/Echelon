# Implementation Report — Sprint 63 (Cycle-020 Sprint 3: Derived Theatre Rules + Run Integrity)

**Sprint:** sprint-3 (global: sprint-63)
**Cycle:** cycle-020 — Scenario Pack Evaluator v2 + Paradox Risk Orchestration
**Date:** 2026-03-07
**Status:** IMPLEMENTATION COMPLETE

---

## Summary

Sprint 3 replaces the boolean `can_spawn_theatre` with rule-based `theatre_spawn_rule_json` evaluation via `should_spawn()`, with full backward compatibility.

## Tasks Completed

### Task 3.1: Implement should_spawn() Rule Evaluator
**Status:** DONE
**Files:** `backend/services/theatre_spawner.py`

`should_spawn(spawn_rule, branch, reward, run_mode, checkpoint)` evaluates:
- `outcome_types` filter: branch.outcome_type must be in list
- `min_reward` filter: reward must meet minimum
- `run_modes` filter: run_mode must be in list
- `checkpoint_classes` filter: checkpoint.evaluator_type must be in list
- All filters are optional; missing = no restriction
- Returns True only if all present filters pass

Tests: `test_spawn_rule_outcome_types`, `test_spawn_rule_min_reward`, `test_spawn_rule_run_modes`

### Task 3.2: Backward Compatibility
**Status:** DONE
**Files:** `backend/services/theatre_spawner.py`

Fallback when `spawn_rule` is None:
- `can_spawn_theatre=True` -> spawn unconditionally
- `can_spawn_theatre=False` -> don't spawn

`spawn_theatre()` also has a legacy guard: returns None if neither `can_spawn_theatre` nor `theatre_spawn_rule_json` is set (protects C018 regression).

Tests: `test_backward_compat_can_spawn_true`, `test_backward_compat_can_spawn_false`

### Task 3.3: evaluate_checkpoints() Integration
**Status:** DONE
**Files:** `backend/services/checkpoint_evaluator.py`

- `evaluate_checkpoints()` calls `should_spawn()` before `spawn_theatre()`
- Passes branch outcome_type, computed reward, run_mode, and checkpoint

### Task 3.4: Spawn Rule Integration Test
**Status:** DONE
**Files:** `backend/tests/test_c020_integration.py`

Test `test_spawn_rule_integration` verifies full flow: checkpoint with spawn rule -> evaluation -> theatre spawned with correct audit event.

### Task 3.5: Run Integrity Checks
**Status:** DONE
**Files:** `backend/services/checkpoint_evaluator.py`

- State vector accumulated across checkpoints ensures consistent run state
- `validate_template_checkpoints()` catches invalid configs before run starts

## Test Results

```
backend/tests/test_c020_spawning.py — 5 tests PASSED
backend/tests/test_c020_integration.py (spawn test) — 1 test PASSED
```

## Regression

C018 spawning tests verified passing (backward compat guard in `spawn_theatre()`).

## Files Modified/Created

| File | Action | Lines |
|------|--------|-------|
| `backend/services/theatre_spawner.py` | Modified | +50 (should_spawn, backward compat) |
| `backend/tests/test_c020_spawning.py` | Created | ~65 (5 spawn rule tests) |
