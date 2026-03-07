# Implementation Report — Sprint 62 (Cycle-020 Sprint 2: Environment RNG + Mode Semantics)

**Sprint:** sprint-2 (global: sprint-62)
**Cycle:** cycle-020 — Scenario Pack Evaluator v2 + Paradox Risk Orchestration
**Date:** 2026-03-07
**Status:** IMPLEMENTATION COMPLETE

---

## Summary

Sprint 2 implements seeded RNG integration into the evaluation pipeline and defines run mode semantics for TRAINING, EVALUATION, CALIBRATION, and REPLAY modes.

## Tasks Completed

### Task 2.1: Per-Checkpoint RNG Scoping
**Status:** DONE
**Files:** `backend/services/checkpoint_evaluator.py`

- `_seeded_rng(seed, checkpoint_id)` creates checkpoint-scoped deterministic RNG
- SHA-256 hash of `"{seed}:{checkpoint_id}"` as seed integer
- Used by DETECTION_EVENT (noise) and TIMING_BREACH (drift)

### Task 2.2: Run Mode Seed Handling
**Status:** DONE
**Files:** `backend/services/checkpoint_evaluator.py`

- TRAINING: uses run seed directly
- EVALUATION: uses run seed (same path)
- CALIBRATION: uses run seed with pin (same code path as TRAINING, seed pinning is caller responsibility)
- REPLAY: uses original run's seed for deterministic replay

Test: `test_calibration_seed_consistency`

### Task 2.3: EVAL/CALIBRATION Shared Path
**Status:** DONE
**Files:** `backend/services/checkpoint_evaluator.py`

- Minimal implementation: EVAL and CALIBRATION share TRAINING code path
- Mode passed through but doesn't affect evaluation logic
- Seed pinning handled by caller (pack lifecycle service)

### Task 2.4: Replay Mode Determinism
**Status:** DONE
**Files:** `backend/services/checkpoint_evaluator.py`

- `build_replay_output()` unchanged — replays use stored results
- New schema-driven path also deterministic for same seed

Test: `test_replay_determinism`

### Task 2.5: Noise Amplitude Configuration
**Status:** DONE
**Files:** `backend/services/checkpoint_evaluator.py`

- DETECTION_EVENT: `noise_amplitude` in branch_rule_json controls noise range
- TIMING_BREACH: `max_drift_seconds` in branch_rule_json controls drift range
- Defaults to sensible values when not specified

### Task 2.6: Mode-Aware Evaluation Tests
**Status:** DONE
**Files:** `backend/tests/test_c020_evaluation.py`

Tests verify:
- Same seed across modes produces identical evaluation
- Different seeds produce different results
- Calibration seed consistency

## Test Results

```
Covered by tests in test_c020_evaluation.py — 13 tests PASSED
```

## Files Modified/Created

| File | Action | Lines |
|------|--------|-------|
| `backend/services/checkpoint_evaluator.py` | Modified | (included in Sprint 1 changes) |
| `backend/tests/test_c020_evaluation.py` | Modified | (included in Sprint 1 test file) |
