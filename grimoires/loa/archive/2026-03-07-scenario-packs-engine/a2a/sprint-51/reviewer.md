# Sprint 3 Implementation Report — Checkpoint Resolution + Branching

**Sprint:** sprint-3 (global: sprint-51)
**Cycle:** cycle-018 (Scenario Packs Engine)
**Date:** 2026-03-07

## Summary

Implemented checkpoint evaluation engine, seed management, branch probabilities, episode tree, and replay output. 9 tests, all passing.

## Tasks Completed

### Task 3.0: ScenarioSeedManager Service

**New file:** `backend/services/scenario_seed_manager.py`

- `allocate_seed(run_mode, run_index, replay_seed)` dispatches by mode:
  - TRAINING: `random.randint(0, 2^31-1)` — stochastic, varying
  - EVALUATION: cycles through `EVALUATION_SEEDS` pool (10 seeds)
  - CALIBRATION: cycles through `CALIBRATION_SEEDS` canonical set `[42, 137, 256, 512, 1024]`
  - REPLAY: returns `replay_seed` or raises `ValueError`
- 1 test: verifies all 4 modes + error case

### Task 3.1: CheckpointEvaluator Service

**New file:** `backend/services/checkpoint_evaluator.py`

- `evaluate_checkpoints(session, run, seed, agent_actions)`:
  - Fetches checkpoints in `sequence_num` order
  - At each checkpoint: deterministic branch selection via SHA-256 hash of `(checkpoint_id, agent_action, seed, evaluator_type)`
  - Computes reward from `reward_mapping_json` × objective vector weights
  - Creates `RunCheckpointResult` records
  - Advances via `branch.next_checkpoint_id`
  - Sets run status to COMPLETED when done
- `_deterministic_branch_index()`: SHA-256 based, stable across platforms
- `_compute_reward()`: branch mapping → checkpoint mapping → default, scaled by objective vector total weight
- All 5 evaluator primitives recognized: BINARY_RISK_GATE, RESOURCE_DEPLETION, DETECTION_EVENT, TIMING_BREACH, MISSION_COMPLETION
- 4 tests: sequential eval, determinism, reward computation, completion

### Task 3.2: Branch Probabilities API

**Modified:** `backend/api/scenario_pack_routes.py`, `backend/schemas/scenario_packs.py`

- `GET /api/v1/scenario-pack-templates/{template_id}/branch-probabilities`
- Returns `{checkpoint_id: {branch_id: probability} | null}`
- `BranchProbabilitiesResponse` schema added
- `compute_branch_probabilities()` in evaluator service (sync), async version inline in route
- 2 tests: probabilities sum to 1.0, null with no runs

### Task 3.3: Episode Tree API

**Modified:** `backend/api/scenario_pack_routes.py`

- `GET /api/v1/scenario-packs/{pack_id}/runs/{run_id}/tree`
- Returns `EpisodeTreeResponse` with nodes showing checkpoint info, selected branch, reward
- Auth-gated (owner only)
- `build_episode_tree()` in evaluator service
- 1 test: correct node structure

### Task 3.4: Replay Output

**Modified:** `backend/api/scenario_pack_routes.py`, `backend/schemas/scenario_packs.py`

- `GET /api/v1/scenario-packs/{pack_id}/runs/{run_id}/replay`
- Returns `ForkReplayResponse` matching frontend `ForkReplay` shape
- Maps checkpoint decisions → disclosure events (`evidence_flip` type)
- Options with simulated price paths
- New schemas: `ForkReplayResponse`, `DisclosureEventResponse`, `ForkOptionPricePathResponse`, `ReplayForkOptionResponse`
- 1 test: disclosure events present, options have price paths

## Files Changed

| File | Action | Lines |
|------|--------|-------|
| `backend/services/scenario_seed_manager.py` | Created | 50 |
| `backend/services/checkpoint_evaluator.py` | Created | 230 |
| `backend/api/scenario_pack_routes.py` | Modified | +180 |
| `backend/schemas/scenario_packs.py` | Modified | +35 |
| `backend/tests/test_c018_sprint3_checkpoints.py` | Created | 280 |

## Test Results

```
9 passed in 0.28s
```

All 29 cycle-018 tests passing (4 + 6 + 10 + 9).

## Acceptance Criteria

- [x] Seed allocation deterministic for CALIBRATION and REPLAY modes
- [x] TRAINING mode produces distinct seeds across runs
- [x] Checkpoints evaluated in sequence_num order
- [x] Branch selection deterministic given (agent action, checkpoint state, seed, evaluator config)
- [x] evaluator_type field used in selection logic
- [x] trigger_condition_json, branch_rule_json, reward_mapping_json consumed
- [x] Seed parameter accepted and stored in run
- [x] Rewards computed correctly
- [x] theatre_spawn_rule_json available for spawn decisions
- [x] Run status transitions to COMPLETED when done
- [x] Results persisted with correct foreign keys
- [x] Branch probabilities computed from run history
- [x] Tree structure matches checkpoint sequence
- [x] Output matches ForkReplay shape
- [x] Checkpoint decisions map to disclosure events
- [x] All 9 tests pass
