# Sprint Plan — Cycle-020: Scenario Pack Evaluator v2 + Paradox Risk Orchestration

**Cycle:** cycle-020
**Date:** 7 March 2026
**PRD:** grimoires/loa/prd.md
**SDD:** grimoires/loa/sdd.md
**Sprints:** 6 (0-5)
**Builder:** Loa (single developer, backend/runtime only)

---

## Sprint 0: Runtime Contract Tightening

**Goal:** Freeze the runtime contract and align models/services/tests before deeper implementation.

### Tasks

#### Task 0.1: Verify Schema Fields Present and Typed
**Description:** Confirm that all checkpoint schema columns required by v2 runtime are present and correctly typed in the ORM models: `trigger_condition_json`, `branch_rule_json`, `evaluator_type`, `theatre_spawn_rule_json`, `reward_mapping_json` on ScenarioCheckpoint; `branch_rule_json`, `outcome_type` on CheckpointBranch.
**Acceptance Criteria:**
- All columns verified present in `backend/database/models.py`
- Test that creates a checkpoint with all JSON fields and reads them back
**File(s):** `backend/database/models.py`, `backend/tests/test_c020_contracts.py`

#### Task 0.2: Define Primitive JSON Contracts
**Description:** Create a contract definition module that specifies the expected JSON schema for each of the 5 evaluator primitives' `trigger_condition_json` and `branch_rule_json`. Include a validation function that checks a checkpoint's config against its evaluator_type.
**Acceptance Criteria:**
- Contract definitions for all 5 primitives (BINARY_RISK_GATE, RESOURCE_DEPLETION, DETECTION_EVENT, TIMING_BREACH, MISSION_COMPLETION)
- `validate_checkpoint_config(evaluator_type, trigger_json, branch_rule_json)` function returns errors or None
- Test for valid and invalid configs per primitive
**File(s):** `backend/services/checkpoint_evaluator.py`, `backend/tests/test_c020_contracts.py`

#### Task 0.3: Define Spawn Rule Contract
**Description:** Define the `theatre_spawn_rule_json` contract: `outcome_types`, `min_reward`, `checkpoint_classes`, `run_modes`. Add validation function.
**Acceptance Criteria:**
- Spawn rule JSON contract documented in code
- `validate_spawn_rule(spawn_rule_json)` function
- Test for valid/invalid spawn rules
**File(s):** `backend/services/theatre_spawner.py`, `backend/tests/test_c020_contracts.py`

#### Task 0.4: Define Paradox Risk Materiality Rule
**Description:** Define when a paradox risk change is "material" enough to emit a WebSocket event. Material = level changed OR active_paradox flipped OR material_counter_signals crossed 0->positive.
**Acceptance Criteria:**
- `_is_material_delta(old_level, new_level, old_factors, new_factors)` function
- Test cases for material and non-material deltas
**File(s):** `backend/services/paradox_risk_orchestrator.py`, `backend/tests/test_c020_contracts.py`

---

## Sprint 1: Schema-Driven Checkpoint Evaluation

**Goal:** Replace hash-based branching with true evaluator-driven resolution using 5 primitives.

### Tasks

#### Task 1.1: Implement Primitive Evaluator Functions
**Description:** Implement 5 evaluator functions that each take `(branch_rule_json, agent_action, seed, state_vector)` and return `(branch_index, evaluation_detail)`. Each follows its SDD-defined contract.
**Acceptance Criteria:**
- `evaluate_binary_risk_gate()` — threshold comparison
- `evaluate_resource_depletion()` — bracket mapping
- `evaluate_detection_event()` — probability gate with seeded noise
- `evaluate_timing_breach()` — deadline comparison with seeded drift
- `evaluate_mission_completion()` — objective set evaluation
- Each function deterministic for same inputs
**File(s):** `backend/services/checkpoint_evaluator.py`

#### Task 1.2: Implement select_branch() Dispatch
**Description:** Create the `select_branch()` function that dispatches to the appropriate primitive evaluator based on `evaluator_type`. Replace `_deterministic_branch_index()` calls in `evaluate_checkpoints()`.
**Acceptance Criteria:**
- `select_branch()` dispatches to correct primitive
- `evaluate_checkpoints()` uses `select_branch()` instead of hash-based index
- Unknown evaluator_type raises ValueError
- Branch index out of range raises ValueError
**File(s):** `backend/services/checkpoint_evaluator.py`

#### Task 1.3: Implement Seeded RNG Helper
**Description:** Create `_seeded_rng(seed, checkpoint_id)` that combines run seed with checkpoint ID for per-checkpoint determinism. Used by DETECTION_EVENT and TIMING_BREACH.
**Acceptance Criteria:**
- Same seed + same checkpoint = same RNG output
- Different checkpoints produce different noise
- Noise is bounded within configured amplitude/range
**File(s):** `backend/services/checkpoint_evaluator.py`

#### Task 1.4: Add Fail-Fast Validation on Run Start
**Description:** Before running checkpoints, validate that all checkpoints in the template have valid evaluator configs. Return 422 if any checkpoint has missing/malformed config.
**Acceptance Criteria:**
- `POST /api/v1/scenario-packs/{id}/run` validates configs before starting
- Missing `trigger_condition_json` or `branch_rule_json` on RUNNABLE template -> 422
- CATALOG_ONLY templates exempt from validation
- Clear error message identifying which checkpoint fails
**File(s):** `backend/api/scenario_pack_routes.py`, `backend/services/checkpoint_evaluator.py`

#### Task 1.5: Update Template Seeders
**Description:** Update existing RUNNABLE template seeders to include valid `trigger_condition_json`, `branch_rule_json`, and optionally `theatre_spawn_rule_json` for their checkpoints.
**Acceptance Criteria:**
- All RUNNABLE templates pass config validation
- CATALOG_ONLY templates unchanged
- Seeder creates checkpoints with valid JSON configs per primitive type
**File(s):** `backend/services/scenario_pack_lifecycle.py` or seeder files

#### Task 1.6: Determinism Tests
**Description:** Tests proving branch selection is deterministic for identical inputs and varies correctly for different inputs.
**Acceptance Criteria:**
- Same (evaluator_type, branch_rule, action, seed, state) -> same branch, every time
- Different seeds -> potentially different branches
- Different actions -> potentially different branches
- All 5 primitives tested
**File(s):** `backend/tests/test_c020_evaluation.py`

#### Task 1.7: Fail-Fast Tests
**Description:** Tests for malformed config rejection.
**Acceptance Criteria:**
- Missing required fields -> ValueError
- Invalid evaluator_type -> ValueError
- Branch index out of range -> ValueError
- Empty branch list -> ValueError
**File(s):** `backend/tests/test_c020_evaluation.py`

---

## Sprint 2: Environment RNG + Mode Semantics

**Goal:** Make randomness explicit and reproducible across run modes.

### Tasks

#### Task 2.1: Implement ScenarioRunStateBuilder
**Description:** Create `backend/services/scenario_run_state_builder.py` that builds a state vector from previous checkpoint results within a run. State vector contains cumulative_reward, completed_objectives, remaining_resources, elapsed_time_sec, previous_branch_outcomes.
**Acceptance Criteria:**
- `build_state_vector(run, checkpoint, previous_results)` returns well-structured dict
- Empty previous_results returns default state vector
- Cumulative values correctly accumulated
**File(s):** `backend/services/scenario_run_state_builder.py`

#### Task 2.2: Wire ScenarioSeedManager as Sole Seed Source
**Description:** Ensure `evaluate_checkpoints()` uses `ScenarioSeedManager.allocate_seed()` as the sole source of environment seeds. Remove any other seed generation paths.
**Acceptance Criteria:**
- `evaluate_checkpoints()` calls `allocate_seed(run_mode, run_index)`
- TRAINING gets random seed
- EVALUATION gets seed from pinned set
- CALIBRATION gets canonical seed
- REPLAY gets recorded seed from original run
**File(s):** `backend/services/checkpoint_evaluator.py`, `backend/api/scenario_pack_routes.py`

#### Task 2.3: Wire State Vector into Evaluation Loop
**Description:** In `evaluate_checkpoints()`, build state vector from previous results before each checkpoint evaluation, and pass to `select_branch()`.
**Acceptance Criteria:**
- State vector built from accumulated results
- State vector passed to primitive evaluators
- `state_vector_json` on RunCheckpointResult contains full state vector (not minimal)
**File(s):** `backend/services/checkpoint_evaluator.py`

#### Task 2.4: Replay Path Validation
**Description:** In REPLAY mode, verify that re-evaluation with recorded seed + recorded actions produces the same branch selections.
**Acceptance Criteria:**
- REPLAY mode uses recorded seed (no fresh randomness)
- Same seed + same actions -> same branch sequence
- Test: run, then replay, compare results
**File(s):** `backend/tests/test_c020_rng.py`

#### Task 2.5: Seed Parity Tests
**Description:** Cross-mode parity tests proving seed behavior.
**Acceptance Criteria:**
- Same seed in TRAINING produces same result (repeated runs)
- CALIBRATION seeds [42, 137, 256, 512, 1024] produce consistent results
- EVALUATION seeds produce consistent results per index
- Different seeds produce different results (statistical, not guaranteed per run)
**File(s):** `backend/tests/test_c020_rng.py`

#### Task 2.6: REPLAY End-to-End Test
**Description:** Full run then replay integration test.
**Acceptance Criteria:**
- Create pack, run with TRAINING mode, capture seed and results
- Replay with recorded seed -> identical branch selections and rewards
**File(s):** `backend/tests/test_c020_rng.py`

---

## Sprint 3: Derived Theatre Rules + Run Integrity

**Goal:** Replace boolean spawning with schema-driven spawn rules.

### Tasks

#### Task 3.1: Implement should_spawn() Rule Evaluator
**Description:** In `theatre_spawner.py`, implement `should_spawn()` that evaluates `theatre_spawn_rule_json` against branch outcome, reward, checkpoint class, and run mode.
**Acceptance Criteria:**
- `should_spawn(spawn_rule, branch, reward, run_mode, checkpoint)` returns bool
- Evaluates outcome_types, min_reward, checkpoint_classes, run_modes from rule
- All fields optional with sensible defaults
**File(s):** `backend/services/theatre_spawner.py`

#### Task 3.2: Backward Compat Fallback
**Description:** Maintain backward compatibility: `spawn_rule=None + can_spawn=True` -> spawn unconditionally. `spawn_rule=None + can_spawn=False` -> don't spawn.
**Acceptance Criteria:**
- Legacy templates with only `can_spawn_theatre=True` continue working
- New templates with `theatre_spawn_rule_json` use rule evaluation
- Test both paths
**File(s):** `backend/services/theatre_spawner.py`

#### Task 3.3: Wire Spawn Rule into evaluate_checkpoints
**Description:** Replace the `if checkpoint.can_spawn_theatre:` check in `evaluate_checkpoints()` with the new `should_spawn()` evaluator.
**Acceptance Criteria:**
- `evaluate_checkpoints()` calls `should_spawn()` with spawn rule, branch, reward, run_mode
- Spawn only occurs when rule passes
- Backward compat preserved
**File(s):** `backend/services/checkpoint_evaluator.py`

#### Task 3.4: Spawn Provenance with Run-Scoped Uniqueness
**Description:** Ensure spawned theatres have unique `construct_id` scoped to the originating pack/run and that duplicate spawns for the same checkpoint in the same run are prevented.
**Acceptance Criteria:**
- `construct_id` format: `scenario_{pack_id}_run_{run_id}_cp_{checkpoint_id}`
- Duplicate spawn attempt for same run+checkpoint returns existing theatre
- Derived theatres queryable by originating pack/run lineage
**File(s):** `backend/services/theatre_spawner.py`

#### Task 3.5: Spawn Rule Tests
**Description:** Tests for spawn rule evaluation.
**Acceptance Criteria:**
- Rule with outcome_types filter: only matching outcomes spawn
- Rule with min_reward: below threshold doesn't spawn
- Rule with run_modes: excluded modes don't spawn
- Empty/null rule with can_spawn=True: spawns (backward compat)
- Empty/null rule with can_spawn=False: doesn't spawn
**File(s):** `backend/tests/test_c020_spawning.py`

---

## Sprint 4: Paradox Risk Orchestration

**Goal:** Promote paradox risk from on-read to event-driven orchestration.

### Tasks

#### Task 4.1: Create ParadoxRiskOrchestrator Service
**Description:** Create `backend/services/paradox_risk_orchestrator.py` with `trigger_recompute(db, theatre_id, trigger_reason)` that loads theatre state, gathers factors, evaluates risk, persists, and conditionally emits WS event.
**Acceptance Criteria:**
- `trigger_recompute()` loads theatre, gathers factors, evaluates, persists
- Returns ParadoxRiskAssessment or None if theatre not found
- Materiality check before WS emission
**File(s):** `backend/services/paradox_risk_orchestrator.py`

#### Task 4.2: Implement Factor Gathering
**Description:** `_gather_factors()` reads live theatre/investigation state to build evaluation inputs: logic_gap, stability, active_paradox, material_counter_signals, evidence_freshness_hours.
**Acceptance Criteria:**
- Reads paradox state from theatre fields
- Reads material counter-signal count from linked investigations
- Reads evidence freshness from linked investigations
- Returns dict compatible with `evaluate()` kwargs
**File(s):** `backend/services/paradox_risk_orchestrator.py`

#### Task 4.3: Wire Trigger Path 1 — Paradox State Change
**Description:** After paradox task updates theatre state, call `orchestrator.trigger_recompute(theatre_id, "paradox_state_change")`.
**Acceptance Criteria:**
- Paradox state mutation triggers recompute
- Recompute is async / non-blocking to the mutation path
**File(s):** `backend/worker/tasks/paradox.py`

#### Task 4.4: Wire Trigger Path 2 — Counter-Signal Ingestion
**Description:** After material counter-signal is logged on an investigation linked to a theatre, trigger recompute.
**Acceptance Criteria:**
- Material counter-signal ingestion triggers recompute for linked theatre
- Non-material counter-signals do not trigger recompute
**File(s):** `backend/api/investigation_routes.py`

#### Task 4.5: Wire Trigger Paths 3 & 4 — Evidence Freshness + Certificate
**Description:** Wire evidence freshness threshold crossing and certificate/policy transitions as trigger paths.
**Acceptance Criteria:**
- Investigation evidence update that crosses freshness threshold triggers recompute
- Certificate pipeline transition triggers recompute for linked theatre
**File(s):** `backend/api/investigation_routes.py`, `backend/services/certificate_pipeline.py`

#### Task 4.6: Orchestrator Tests
**Description:** Unit and integration tests for the orchestrator.
**Acceptance Criteria:**
- Material delta detected correctly (level change, paradox flip, counter-signal threshold)
- Non-material delta: no WS event emitted
- Factor gathering returns correct values from theatre/investigation state
- Trigger from each of the 4 paths verified
**File(s):** `backend/tests/test_c020_paradox_orchestrator.py`

---

## Sprint 5: WebSocket Emission + Integration + E2E

**Goal:** Wire WebSocket events and verify full integration paths.

### Tasks

#### Task 5.1: Wire CHECKPOINT_RESOLVED Emission
**Description:** In `evaluate_checkpoints()`, emit `broadcast_checkpoint_resolved` after each checkpoint evaluation.
**Acceptance Criteria:**
- WS event emitted with pack_id, run_id, checkpoint_id, selected_branch_id, reward, seed
- Event uses existing `broadcast_checkpoint_resolved` method
**File(s):** `backend/services/checkpoint_evaluator.py`

#### Task 5.2: Wire THEATRE_SPAWNED Emission
**Description:** In `spawn_theatre()`, emit `broadcast_theatre_spawned` after theatre creation.
**Acceptance Criteria:**
- WS event emitted with pack_id, run_id, checkpoint_id, theatre_id
- Only emitted when theatre is actually spawned (not on skip)
**File(s):** `backend/services/theatre_spawner.py`

#### Task 5.3: Wire PARADOX_RISK_CHANGED Emission
**Description:** In `ParadoxRiskOrchestrator.trigger_recompute()`, emit `broadcast_paradox_risk_changed` on material delta.
**Acceptance Criteria:**
- WS event emitted with theatre_id, old_level, new_level, factors, reason
- NOT emitted on non-material delta
**File(s):** `backend/services/paradox_risk_orchestrator.py`

#### Task 5.4: Scenario Pack Integration Test
**Description:** Full integration: runnable template -> create pack -> run with fixed seed -> checkpoints resolve from schema -> derived theatre spawns when rule passes -> replay reproduces exact path.
**Acceptance Criteria:**
- Pack created from RUNNABLE template
- Run executes with all checkpoints resolving via schema-driven evaluation
- Correct branches selected per primitive logic
- Derived theatre spawned when spawn rule passes
- Replay with same seed produces identical results
**File(s):** `backend/tests/test_c020_integration.py`

#### Task 5.5: Paradox Risk Integration Test
**Description:** Full integration: theatre/investigation mutation -> paradox risk updates -> material change emits WS event -> non-material recompute does not spam.
**Acceptance Criteria:**
- Counter-signal ingestion triggers recompute
- Level change emits exactly 1 WS event
- Same-level recompute emits 0 WS events
**File(s):** `backend/tests/test_c020_integration.py`

#### Task 5.6: Regression Verification
**Description:** Verify Cycle-019 APIs and Cycle-018 template catalog behavior unchanged.
**Acceptance Criteria:**
- Existing investigation persistence tests pass
- Existing agent deployment tests pass
- Existing paradox risk read-path tests pass
- CATALOG_ONLY templates unaffected
- Existing pack lifecycle tests pass
**File(s):** `backend/tests/test_c020_integration.py`

#### Task 5.7: WebSocket Emission Tests
**Description:** Unit tests for WS event emission behavior.
**Acceptance Criteria:**
- CHECKPOINT_RESOLVED emitted per checkpoint in a run
- THEATRE_SPAWNED emitted only on actual spawn
- PARADOX_RISK_CHANGED emitted only on material delta
- All events have correct payload structure
**File(s):** `backend/tests/test_c020_integration.py`
