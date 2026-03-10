# SDD — Cycle-020: Scenario Pack Evaluator v2 + Paradox Risk Orchestration

**Cycle:** cycle-020
**Date:** 7 March 2026
**PRD:** grimoires/loa/prd.md
**Depends on:** Cycle-019, Cycle-018, Cycle-017

---

## 1. Executive Summary

Cycle 020 upgrades two staged backend systems to release posture:

1. **Checkpoint Evaluator v2**: Replace hash-based branch selection with true schema-driven evaluation using 5 evaluator primitives, explicit environment RNG, and schema-driven theatre spawn rules.
2. **Paradox Risk Orchestrator**: Replace passive on-read risk computation with event-driven orchestration that recalculates from mutation paths and emits WebSocket events on material delta.

No new models or migrations. All schema columns already exist. This is a runtime behavior upgrade.

---

## 2. System Architecture

### 2.1 Checkpoint Evaluation Flow (v2)

```
POST /scenario-packs/{id}/run
  |
  v
ScenarioSeedManager.allocate_seed(run_mode, run_index)
  |
  v
evaluate_checkpoints(session, run, seed, agent_actions)
  |
  +---> for each checkpoint:
  |      |
  |      v
  |    PrimitiveEvaluator.evaluate(evaluator_type, trigger_condition, branch_rules, action, seed, state)
  |      |
  |      v
  |    Branch selected + reward computed
  |      |
  |      +---> SpawnRuleEvaluator.should_spawn(spawn_rule, branch, reward, run_mode)
  |      |      |
  |      |      v
  |      |    spawn_theatre() if rule passes
  |      |
  |      v
  |    RunCheckpointResult persisted
  |    WS: CHECKPOINT_RESOLVED emitted
  |
  v
Run COMPLETED
```

### 2.2 Paradox Risk Orchestration Flow

```
Mutation event (paradox state, counter-signal, evidence, certificate)
  |
  v
ParadoxRiskOrchestrator.trigger_recompute(theatre_id, trigger_reason)
  |
  v
ParadoxRiskEvaluator.evaluate(factors from theatre/investigation state)
  |
  v
Compare old_level vs new_level
  |
  +---> if material delta:
  |      persist_risk_to_theatre()
  |      WS: PARADOX_RISK_CHANGED
  |
  +---> if no material delta:
         persist_risk_to_theatre() (update timestamp only)
         no WS event
```

---

## 3. Component Design

### 3.1 Primitive Evaluator System

Replace `_deterministic_branch_index()` with evaluator-type-specific branch selection.

**Location**: `backend/services/checkpoint_evaluator.py`

Each primitive defines:
- **Trigger condition contract**: When the checkpoint activates
- **Branch rule contract**: How a branch is selected given (action, state, seed)
- **Reward mapping**: How reward is computed for the selected branch

#### 3.1.1 Primitive Contracts

**BINARY_RISK_GATE**
```json
{
  "trigger_condition_json": {
    "type": "BINARY_RISK_GATE",
    "threshold": 0.65,
    "metric": "risk_exposure"
  },
  "branch_rule_json": {
    "type": "threshold_compare",
    "field": "action_value",
    "threshold": 0.65,
    "above_branch_index": 0,
    "below_branch_index": 1
  }
}
```
Logic: `action_value >= threshold` -> branch 0, else branch 1.

**RESOURCE_DEPLETION**
```json
{
  "trigger_condition_json": {
    "type": "RESOURCE_DEPLETION",
    "resource": "capital",
    "depletion_curve": "linear"
  },
  "branch_rule_json": {
    "type": "resource_bracket",
    "brackets": [
      {"min": 0.0, "max": 0.3, "branch_index": 0},
      {"min": 0.3, "max": 0.7, "branch_index": 1},
      {"min": 0.7, "max": 1.0, "branch_index": 2}
    ],
    "field": "remaining_fraction"
  }
}
```
Logic: `remaining_fraction` mapped to bracket -> corresponding branch.

**DETECTION_EVENT**
```json
{
  "trigger_condition_json": {
    "type": "DETECTION_EVENT",
    "base_detection_probability": 0.3
  },
  "branch_rule_json": {
    "type": "probability_gate",
    "base_probability": 0.3,
    "noise_amplitude": 0.1,
    "detected_branch_index": 0,
    "safe_branch_index": 1
  }
}
```
Logic: `base_probability + noise(seed) > action_stealth_value` -> detected, else safe. Noise from seeded RNG.

**TIMING_BREACH**
```json
{
  "trigger_condition_json": {
    "type": "TIMING_BREACH",
    "deadline_sec": 300,
    "drift_range": 30
  },
  "branch_rule_json": {
    "type": "deadline_compare",
    "deadline_sec": 300,
    "drift_range": 30,
    "on_time_branch_index": 0,
    "breach_branch_index": 1
  }
}
```
Logic: `action_time + drift(seed) <= deadline` -> on-time, else breach. Drift from seeded RNG.

**MISSION_COMPLETION**
```json
{
  "trigger_condition_json": {
    "type": "MISSION_COMPLETION",
    "required_objectives": ["obj_a", "obj_b", "obj_c"],
    "min_completion": 2
  },
  "branch_rule_json": {
    "type": "objective_set",
    "required": ["obj_a", "obj_b", "obj_c"],
    "min_completion": 2,
    "success_branch_index": 0,
    "partial_branch_index": 1,
    "fail_branch_index": 2
  }
}
```
Logic: Count completed objectives from action. `>= min` -> success, `> 0` -> partial, `0` -> fail.

#### 3.1.2 Evaluator Dispatch

```python
# New in checkpoint_evaluator.py

PRIMITIVE_EVALUATORS = {
    "BINARY_RISK_GATE": evaluate_binary_risk_gate,
    "RESOURCE_DEPLETION": evaluate_resource_depletion,
    "DETECTION_EVENT": evaluate_detection_event,
    "TIMING_BREACH": evaluate_timing_breach,
    "MISSION_COMPLETION": evaluate_mission_completion,
}

def select_branch(
    evaluator_type: str,
    branches: list[CheckpointBranch],
    branch_rule_json: dict,
    agent_action: str,
    seed: int,
    state_vector: dict,
) -> tuple[CheckpointBranch, dict]:
    """Select branch via primitive evaluator.

    Returns (selected_branch, evaluation_detail).
    Raises ValueError for unknown evaluator_type or malformed config.
    """
    evaluator = PRIMITIVE_EVALUATORS.get(evaluator_type)
    if evaluator is None:
        raise ValueError(f"Unknown evaluator primitive: {evaluator_type}")

    branch_index, detail = evaluator(
        branch_rule_json=branch_rule_json,
        agent_action=agent_action,
        seed=seed,
        state_vector=state_vector,
    )

    if branch_index < 0 or branch_index >= len(branches):
        raise ValueError(
            f"Evaluator {evaluator_type} returned branch_index {branch_index} "
            f"but only {len(branches)} branches exist"
        )

    return branches[branch_index], detail
```

#### 3.1.3 Environment RNG Integration

Each primitive that uses randomness (DETECTION_EVENT, TIMING_BREACH) creates a seeded `random.Random` instance:

```python
def _seeded_rng(seed: int, checkpoint_id: str) -> random.Random:
    """Create checkpoint-scoped seeded RNG.

    Combines run seed with checkpoint_id for per-checkpoint determinism.
    """
    combined = hashlib.sha256(f"{seed}|{checkpoint_id}".encode()).hexdigest()
    return random.Random(int(combined[:8], 16))
```

This ensures:
- Same seed + same checkpoint = same noise value
- Different checkpoints within same run get different noise
- Agent actions never influence randomness

### 3.2 Scenario Run State Builder

**New file**: `backend/services/scenario_run_state_builder.py`

Normalizes checkpoint state into a state vector that evaluators consume:

```python
def build_state_vector(
    run: ScenarioRun,
    checkpoint: ScenarioCheckpoint,
    previous_results: list[RunCheckpointResult],
) -> dict:
    """Build state vector for checkpoint evaluation.

    Returns dict with:
    - cumulative_reward: float
    - completed_objectives: list[str]
    - remaining_resources: dict[str, float]
    - elapsed_time_sec: float
    - previous_branch_outcomes: list[str]
    """
```

The state vector accumulates from previous checkpoint results within the same run, providing evaluators with the run-so-far context.

### 3.3 Theatre Spawn Rule Evaluator

**Updated in**: `backend/services/theatre_spawner.py`

Replace `can_spawn_theatre` boolean with `theatre_spawn_rule_json` evaluation:

```python
def should_spawn(
    spawn_rule: dict | None,
    branch: CheckpointBranch,
    reward: float,
    run_mode: str,
    checkpoint: ScenarioCheckpoint,
) -> bool:
    """Evaluate whether to spawn a theatre from this checkpoint resolution.

    spawn_rule_json contract:
    {
        "outcome_types": ["SUCCESS", "PARTIAL_SUCCESS"],  // allowed branch outcome_types
        "min_reward": 0.5,                                 // minimum reward threshold
        "checkpoint_classes": ["CRITICAL"],                 // allowed checkpoint classes (optional)
        "run_modes": ["TRAINING", "EVALUATION"]            // allowed run modes (optional, default: all)
    }

    Returns False if spawn_rule is None (backward compat with can_spawn_theatre=False).
    Returns True for can_spawn_theatre=True with no spawn_rule (legacy fallback).
    """
```

**Fallback logic**:
- `theatre_spawn_rule_json` is set -> evaluate the rule
- `theatre_spawn_rule_json` is None AND `can_spawn_theatre` is True -> spawn unconditionally (backward compat)
- `theatre_spawn_rule_json` is None AND `can_spawn_theatre` is False -> don't spawn

### 3.4 Paradox Risk Orchestrator

**New file**: `backend/services/paradox_risk_orchestrator.py`

```python
class ParadoxRiskOrchestrator:
    """Centralized paradox risk recomputation + persistence + event gating."""

    async def trigger_recompute(
        self,
        db: AsyncSession,
        theatre_id: str,
        trigger_reason: str,
    ) -> ParadoxRiskAssessment | None:
        """Recompute paradox risk for a theatre.

        1. Load theatre + related investigation state
        2. Gather risk factors from live data
        3. Evaluate via ParadoxRiskEvaluator
        4. Compare with persisted level
        5. Persist new assessment
        6. Emit WS event if material delta

        Returns assessment or None if theatre not found.
        """

    def _is_material_delta(
        self,
        old_level: str | None,
        new_level: str,
        old_factors: dict | None,
        new_factors: dict,
    ) -> bool:
        """Determine if risk change is material enough for WS emission.

        Material = level changed OR any factor crossed a threshold boundary.
        """

    async def _gather_factors(
        self,
        db: AsyncSession,
        theatre,
    ) -> dict:
        """Gather risk computation inputs from live theatre/investigation state.

        Reads:
        - Active paradox state from theatre
        - Material counter-signal count from linked investigations
        - Evidence freshness from linked investigations
        - Logic gap / stability from theatre fields
        """
```

**Trigger integration points** (called from existing mutation paths):

| Trigger | Location | Call |
|---------|----------|------|
| Paradox state change | `backend/worker/tasks/paradox.py` | `orchestrator.trigger_recompute(theatre_id, "paradox_state_change")` |
| Material counter-signal | `backend/api/investigation_routes.py` (counter-signal endpoint) | `orchestrator.trigger_recompute(theatre_id, "counter_signal_ingested")` |
| Evidence freshness threshold | Background task or on investigation update | `orchestrator.trigger_recompute(theatre_id, "evidence_freshness_threshold")` |
| Certificate/policy transition | `backend/services/certificate_pipeline.py` | `orchestrator.trigger_recompute(theatre_id, "certificate_transition")` |

### 3.5 Materiality Rule for PARADOX_RISK_CHANGED

A delta is material when:
- `level` changes (LOW -> WATCH, WATCH -> HIGH, etc.)
- OR `active_paradox` flips (False -> True or True -> False)
- OR `material_counter_signals` crosses from 0 to >0

Non-material: factor values change within same level without crossing the above boundaries.

---

## 4. Data Architecture

No new models or migrations required. All schema columns exist from Cycle-018 and Cycle-019.

### 4.1 Existing Columns Used by v2

**ScenarioCheckpoint** (line ~795 in models.py):
- `trigger_condition_json` — JSON, currently STAGED, now consumed
- `evaluator_type` — String, already used for hash input, now dispatches to primitive
- `can_spawn_theatre` — Boolean, kept for backward compat fallback
- `theatre_spawn_rule_json` — JSON, currently STAGED, now consumed

**CheckpointBranch** (line ~826):
- `branch_rule_json` — JSON, currently STAGED, now consumed
- `outcome_type` — String, used by spawn rule evaluation
- `reward_mapping_json` — JSON, already consumed

**ScenarioRun** (line ~886):
- `environment_seed` — Integer, already set
- `run_mode` — String, already set

**RunCheckpointResult** (line ~918):
- `state_vector_json` — JSON, upgraded from minimal to full state vector
- `spawned_theatre_id` — String FK, already used

**Theatre**:
- `paradox_risk_level` — String, already persisted
- `paradox_risk_factors_json` — JSON, already persisted
- `paradox_risk_updated_at` — DateTime, already persisted

### 4.2 Template Seeder Updates

Existing scenario pack template seeders must be updated to include valid `trigger_condition_json`, `branch_rule_json`, and `theatre_spawn_rule_json` for RUNNABLE templates. CATALOG_ONLY templates can leave these as null.

---

## 5. API Design

### 5.1 Scenario Pack Endpoints (Behavior Changes Only)

**`POST /api/v1/scenario-packs/{id}/run`**
- Now validates that all checkpoints in the template have valid evaluator configs
- Returns 422 if any checkpoint has missing/malformed `trigger_condition_json` or branches lack `branch_rule_json`
- Response shape unchanged

**`GET /api/v1/scenario-packs/{id}/runs/{run_id}/tree`**
- `state_vector_json` on each node now contains full state vector (cumulative_reward, completed_objectives, etc.)
- Response shape unchanged (additive detail in existing field)

**`GET /api/v1/scenario-packs/{id}/runs/{run_id}/replay`**
- Replay now uses recorded seed + state vectors for exact reproduction
- Response shape unchanged

### 5.2 Theatre Endpoints (No Changes)

`GET /api/v1/theatres/{id}` continues returning `paradox_risk` from persisted state. On-read fallback computation remains for missing/stale values but orchestrated recompute is now the primary path.

---

## 6. WebSocket Events

### 6.1 CHECKPOINT_RESOLVED

Emitted after each checkpoint evaluation in `evaluate_checkpoints()`.

```python
await realtime_manager.broadcast_checkpoint_resolved(
    pack_id=pack.id,
    run_id=run.id,
    checkpoint_id=checkpoint.id,
    selected_branch_id=selected_branch.id,
    reward=reward,
    seed=seed,
)
```

### 6.2 THEATRE_SPAWNED

Emitted in `spawn_theatre()` after theatre creation.

```python
await realtime_manager.broadcast_theatre_spawned(
    pack_id=pack.id,
    run_id=run.id,
    checkpoint_id=checkpoint.id,
    theatre_id=theatre.id,
)
```

### 6.3 PARADOX_RISK_CHANGED

Emitted by `ParadoxRiskOrchestrator` only on material delta.

```python
await realtime_manager.broadcast_paradox_risk_changed(
    theatre_id=theatre_id,
    old_level=old_level,
    new_level=new_level,
    factors=new_factors,
    reason=trigger_reason,
)
```

---

## 7. Security Architecture

No new authentication or authorization surfaces. All endpoints retain existing auth guards.

- Scenario pack run endpoints require authenticated user who owns the pack
- Theatre paradox risk is read-only for non-owners
- WebSocket events are scoped to connected users with appropriate theatre/pack access

---

## 8. Testing Strategy

### 8.1 Unit Tests

**Primitive evaluators** (per primitive):
- Correct branch selection for known inputs
- Determinism: same inputs always produce same output
- Boundary cases: threshold edge values
- Invalid config rejection (missing fields, malformed JSON)

**Environment RNG**:
- `_seeded_rng` produces same output for same seed+checkpoint
- Different checkpoints produce different noise
- DETECTION_EVENT noise is bounded
- TIMING_BREACH drift is bounded

**Spawn rule evaluator**:
- Rule-based spawn gating
- Backward compat with `can_spawn_theatre` boolean
- Mode restriction enforcement

**Paradox risk orchestrator**:
- Materiality detection
- Factor gathering from theatre/investigation state
- No WS event on non-material delta

### 8.2 Integration Tests

- Full run: template -> pack -> run -> checkpoints resolve from schema -> correct branches selected
- Replay: same seed reproduces exact path
- Spawn: derived theatre created only when spawn rule passes
- Paradox: mutation triggers recompute, material delta emits WS event

### 8.3 Regression

- Existing Cycle-018 template catalog tests pass
- Existing Cycle-019 deployment/investigation/paradox tests pass
- CATALOG_ONLY templates unaffected

---

## 9. Implementation Plan (Sprint Mapping)

### Sprint 0: Runtime Contract Tightening
- Verify schema fields, freeze primitive contracts
- Define JSON contracts per primitive (trigger, branch_rule, spawn_rule)
- Define materiality rule
- Lock stale-cache policy

### Sprint 1: Schema-Driven Checkpoint Evaluation
- Implement 5 primitive evaluator functions
- Implement `select_branch()` dispatch
- Replace `_deterministic_branch_index()` calls in `evaluate_checkpoints()`
- Add `_seeded_rng()` for noise-using primitives
- Fail-fast validation for malformed configs
- Update template seeders with valid configs

### Sprint 2: Environment RNG + Mode Semantics
- Implement `ScenarioRunStateBuilder`
- Wire `ScenarioSeedManager` as sole seed source in evaluation path
- State vector accumulation across checkpoints
- Replay path validation (recorded seed + no fresh randomness)
- Parity tests across modes

### Sprint 3: Derived Theatre Rules + Run Integrity
- Replace `can_spawn_theatre` logic with `should_spawn()` rule evaluator
- Implement spawn rule contract evaluation
- Backward compat fallback for legacy boolean
- Spawn provenance with run-scoped uniqueness

### Sprint 4: Paradox Risk Orchestration
- Create `ParadoxRiskOrchestrator` service
- Wire 4 trigger paths into existing mutation code
- Implement materiality detection
- Factor gathering from live theatre/investigation state
- On-read fallback kept for missing/stale

### Sprint 5: WebSocket Emission + Integration + E2E
- Wire CHECKPOINT_RESOLVED emission from evaluate_checkpoints
- Wire THEATRE_SPAWNED emission from spawn_theatre
- Wire PARADOX_RISK_CHANGED emission from orchestrator
- Full integration tests
- Regression verification

---

## 10. Technical Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Existing template seeders have null JSON config fields | Runs fail with validation errors | Sprint 1 updates seeders with valid configs; CATALOG_ONLY templates exempt |
| Primitive evaluator contracts may not cover all seeded template variations | Edge case branch selection failures | Comprehensive unit tests per primitive; fail-fast with clear error messages |
| Paradox risk orchestrator adds latency to mutation paths | Slower API responses | Fire-and-forget pattern; orchestrator runs async, does not block response |
| Backward compat for `can_spawn_theatre` boolean | Legacy templates break | Explicit fallback: no spawn_rule + can_spawn=True -> spawn unconditionally |
| State vector accumulation may be expensive for long checkpoint chains | Memory/performance concern | State vector is a small dict; checkpoint chains are bounded by template design |

---

## 11. Out of Scope

- New evaluator primitives beyond the 5 defined
- New Scenario Pack template families
- Frontend changes (Alexander handles)
- Agent breeding / genealogy
- Historical paradox risk charting
- New inquiry classes
