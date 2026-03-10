# Sprint 4 Implementation Report — Derived Theatre Spawning

**Sprint:** sprint-4 (global: sprint-52)
**Cycle:** cycle-018 (Scenario Packs Engine)
**Date:** 2026-03-07

## Summary

Implemented theatre spawning from checkpoint resolutions with provenance tracking, derived theatre API, and evaluator integration. 6 tests, all passing.

## Tasks Completed

### Task 4.1: TheatreSpawner Service

**New file:** `backend/services/theatre_spawner.py`

- `spawn_theatre(session, checkpoint, pack, run, result)`:
  - Creates Theatre in DRAFT state when `can_spawn_theatre=True`
  - Sets `spawned_from_checkpoint_id` for provenance
  - Generates `construct_id` as `scenario_{pack_id}_run_{run_id}_cp_{checkpoint_id}`
  - Stores `spawned_theatre_id` on the RunCheckpointResult
  - Logs `THEATRE_SPAWNED` audit event with full context
- `_ensure_spawned_template()`: creates `scenario_derived` TheatreTemplate if not exists
- Returns None for non-spawning checkpoints
- 3 tests: provenance, no-spawn, construct_id format

### Task 4.2: Spawned Theatre Lifecycle

- Spawned theatres created in DRAFT state with `scenario_derived` template
- Ready for existing lifecycle: DRAFT → commit → run → settle → certificate
- 1 test: DRAFT state verified

### Task 4.3: Derived Theatre API

**Modified:** `backend/api/scenario_pack_routes.py`, `backend/schemas/scenario_packs.py`

- `GET /api/v1/scenario-packs/{pack_id}/derived-theatres`
- Returns theatres where `spawned_from_checkpoint_id` matches pack template checkpoints
- Auth-gated (owner only)
- `DerivedTheatreResponse` schema with state, construct_id, certificate_id
- 1 test: 2 spawning checkpoints → 2 theatres

### Task 4.4: Evaluator Integration + Audit Events

**Modified:** `backend/services/checkpoint_evaluator.py`

- Added `spawn_theatre()` call during `evaluate_checkpoints()` when `can_spawn_theatre=True`
- Audit events contain theatre_id, checkpoint_id, market_question, construct_id
- 1 test: THEATRE_SPAWNED event with correct detail_json

## Files Changed

| File | Action | Lines |
|------|--------|-------|
| `backend/services/theatre_spawner.py` | Created | 105 |
| `backend/services/checkpoint_evaluator.py` | Modified | +4 |
| `backend/api/scenario_pack_routes.py` | Modified | +45 |
| `backend/schemas/scenario_packs.py` | Modified | +10 |
| `backend/tests/test_c018_sprint4_spawning.py` | Created | 225 |

## Test Results

```
6 passed in 0.24s
```

All 35 cycle-018 tests passing (4 + 6 + 10 + 9 + 6).

## Acceptance Criteria

- [x] Theatre created with correct provenance FK
- [x] construct_id includes run_id: scenario_{pack_id}_run_{run_id}_cp_{checkpoint_id}
- [x] Non-spawning checkpoints don't create theatres
- [x] Audit event logged with theatre_id, checkpoint_id
- [x] Spawned theatre follows normal lifecycle (DRAFT state)
- [x] Derived theatres API returns only this pack's spawned theatres
- [x] All 6 tests pass
