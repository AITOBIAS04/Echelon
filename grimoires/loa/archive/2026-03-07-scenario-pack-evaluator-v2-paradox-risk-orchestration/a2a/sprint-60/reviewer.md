# Implementation Report — Sprint 60 (Cycle-020 Sprint 0: Runtime Contract Tightening)

**Sprint:** sprint-0 (global: sprint-60)
**Cycle:** cycle-020 — Scenario Pack Evaluator v2 + Paradox Risk Orchestration
**Date:** 2026-03-07
**Status:** IMPLEMENTATION COMPLETE

---

## Summary

Sprint 0 establishes the runtime contracts for all v2 evaluator primitives, spawn rule evaluation, and paradox risk materiality detection. This is the foundation sprint — no behavioral changes, only contract definitions and validation functions with comprehensive tests.

## Tasks Completed

### Task 0.1: Verify Schema Fields Present and Typed
**Status:** DONE
**Files:** `backend/database/models.py` (verified, no changes needed), `backend/tests/test_c020_contracts.py`

Verified all checkpoint schema columns exist in ORM models:
- `trigger_condition_json`, `branch_rule_json`, `evaluator_type`, `theatre_spawn_rule_json`, `reward_mapping_json` on ScenarioCheckpoint
- `branch_rule_json`, `outcome_type` on CheckpointBranch
- Test `test_checkpoint_schema_fields_present` confirms field presence

### Task 0.2: Define Primitive JSON Contracts
**Status:** DONE
**Files:** `backend/services/checkpoint_evaluator.py`, `backend/tests/test_c020_contracts.py`

Added `PRIMITIVE_CONTRACTS` dict defining `trigger_fields`, `branch_rule_fields`, and `branch_rule_type` for all 5 primitives:
- BINARY_RISK_GATE: threshold_field, comparator / threshold, branch_map
- RESOURCE_DEPLETION: resource_field / brackets
- DETECTION_EVENT: probability_field / base_probability, noise_amplitude
- TIMING_BREACH: deadline_field, clock_field / max_drift_seconds
- MISSION_COMPLETION: objective_fields / required_count, branch_map

Added `validate_checkpoint_config()` that checks required fields per primitive. Test `test_primitive_contract_validation` covers valid and invalid configs for all 5 primitives.

### Task 0.3: Define Spawn Rule Contract
**Status:** DONE
**Files:** `backend/services/checkpoint_evaluator.py`, `backend/tests/test_c020_contracts.py`

Added `validate_spawn_rule()` that validates:
- `outcome_types` is a list of strings
- `min_reward` is numeric
- `run_modes` is a list of strings
- `checkpoint_classes` is a list of strings
- Unknown keys are flagged

Test `test_spawn_rule_validation` covers valid and invalid spawn rules.

### Task 0.4: Define Paradox Risk Materiality Rule
**Status:** DONE
**Files:** `backend/services/paradox_risk_orchestrator.py` (new), `backend/tests/test_c020_contracts.py`

Added `is_material_delta(old_level, new_level, old_factors, new_factors)`:
- Material if level changed
- Material if `active_paradox` flipped
- Material if `material_counter_signals` crossed 0 boundary
- NOT material for other factor changes at same level

Test `test_paradox_risk_materiality` covers all cases.

## Test Results

```
backend/tests/test_c020_contracts.py — 4 tests PASSED
```

## Files Modified/Created

| File | Action | Lines |
|------|--------|-------|
| `backend/services/checkpoint_evaluator.py` | Modified | +80 (contracts, validation) |
| `backend/services/paradox_risk_orchestrator.py` | Created | +45 (materiality function) |
| `backend/tests/test_c020_contracts.py` | Created | ~120 (4 contract tests) |

## Risks / Notes

- No behavioral changes to existing evaluation — contract definitions only
- `PRIMITIVE_CONTRACTS` dict is used by Sprint 1 evaluators for dispatch validation
- Materiality rule is consumed by Sprint 4 orchestrator
