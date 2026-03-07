# PRD — Cycle-020: Scenario Pack Evaluator v2 + Paradox Risk Orchestration

**Cycle:** cycle-020
**Date:** 7 March 2026
**Depends on:** Cycle-019 (Agent Deployment + Investigation Persistence + Paradox Risk), Cycle-018 (Scenario Packs Engine), Cycle-017 (Policy Surface)
**Sprints:** 6 (0-5)
**Builder:** Loa (backend/runtime only -- Alexander handles frontend scenario lifecycle UI)

---

## 1. Problem Statement

Two backend systems shipped in honest-but-staged posture need hardening before release:

### 1.1 Checkpoint Evaluator Is Hash-Based, Not Schema-Driven

Cycle-018 shipped the Scenario Packs engine with a checkpoint evaluator (`backend/services/checkpoint_evaluator.py`) that uses deterministic hash-based branch selection. The schema columns exist (`trigger_condition_json`, `branch_rule_json`, `evaluator_type`, `theatre_spawn_rule_json`, `reward_mapping_json`) but are STAGED -- the runtime ignores them and selects branches via `_deterministic_branch_index()`.

This was acceptable for the initial shipping posture. It is not acceptable for release:

- `RUNNABLE` templates cannot claim schema-driven evaluation while using hash branching
- Branch resolution depends only on checkpoint ID hash, not agent action, environment seed, or evaluator config
- Theatre spawning uses `can_spawn_theatre` boolean only, ignoring `theatre_spawn_rule_json`
- No environment randomness contract -- agents and environment share the same implicit randomness

### 1.2 Paradox Risk Is Passive, Not Orchestrated

Cycle-019 shipped paradox risk as a computed field on theatre detail reads. The `ParadoxRiskEvaluator` (`backend/services/paradox_risk_evaluator.py`) computes risk and `persist_risk_to_theatre()` saves it, but:

- Recomputation only happens on-read when the cached value is missing or stale (>1 hour)
- No backend mutation triggers recalculation -- risk drifts silently between reads
- `PARADOX_RISK_CHANGED` WebSocket event contract exists in `realtime_manager.py` but is never emitted from live mutation paths
- No orchestrator service centralizes recalculation decisions

> Source: echelon_cycle_020.md, codebase grounding (checkpoint_evaluator.py, paradox_risk_evaluator.py, theatre_spawner.py, scenario_seed_manager.py, models.py)

---

## 2. Product Contracts

### 2.1 Scenario Packs Are Real Runtime Surfaces

For `RUNNABLE` templates, the engine must execute the stored checkpoint graph as the source of truth:

- No bespoke Python per pack
- No hash-only branch selection pretending to be schema-driven
- No agent-driven randomness
- No hidden divergence between stored checkpoint config and runtime behavior

### 2.2 Checkpoint Evaluation Contract

Every runnable checkpoint must be executable from stored configuration:

- `trigger_condition_json`
- `decision_window_sec`
- `evaluator_type`
- `branch_rule_json`
- `reward_mapping_json`
- Optional `theatre_spawn_rule_json`

Branch resolution must be deterministic given: (agent action, checkpoint state, environment seed, evaluator config).

### 2.3 Environment Randomness Contract

Agents provide actions, policies, and strategy. They do NOT provide randomness.

Randomness comes from the environment via explicit seeded RNG:
- Event rolls
- Hidden state variation
- Saboteur deck draws
- Bounded uncertainty / noise sampling

Run modes:
- `TRAINING`: stochastic, varying seeds
- `EVALUATION`: controlled stochasticity from a fixed seed set (shares TRAINING code path with pinned seeds)
- `CALIBRATION`: canonical seed set for comparability (shares TRAINING code path with canonical seeds)
- `REPLAY`: exact recorded path, no fresh randomness

`ScenarioSeedManager` already exists with `allocate_seed()` supporting all 4 modes. CALIBRATION_SEEDS = [42, 137, 256, 512, 1024]. EVALUATION_SEEDS = [7, 13, 23, 31, 47, 59, 67, 73, 89, 97].

### 2.4 Paradox Risk Contract

Paradox risk is a live policy signal, not a static field.

It must:
- Recalculate from real theatre/investigation/paradox mutations
- Persist the latest assessed state for efficient reads
- Emit `PARADOX_RISK_CHANGED` only on material delta
- Remain inquiry-class-aware

Theatre language: `LOW`, `WATCH`, `HIGH`.

Explanations: Evidence weak, Counter-signals rising, Logic gap widening, Stale investigation, Paradox active.

---

## 3. Functional Requirements

### FR-1: Schema-Driven Checkpoint Evaluation

Replace hash-only branching with true evaluator-driven resolution.

`CheckpointEvaluator` must consume `trigger_condition_json`, `branch_rule_json`, `reward_mapping_json`, and `theatre_spawn_rule_json` from stored checkpoint configuration.

Branch selection must evaluate checkpoint state + agent action + seed + primitive config. Invalid/malformed runnable checkpoint configs must fail fast with explicit error states. `CATALOG_ONLY` templates remain non-runnable.

### FR-2: Five Evaluator Primitives

All 5 primitives ship as full set (4 runnable packs need all 5):

| Primitive | Purpose | Key Branch Logic |
|-----------|---------|-----------------|
| `BINARY_RISK_GATE` | Yes/no risk threshold | Action crosses configured threshold -> branch A, else branch B |
| `RESOURCE_DEPLETION` | Resource management under constraint | Remaining resources vs depletion curve determine branch |
| `DETECTION_EVENT` | Stealth/detection scenario | Detection probability from action + noise -> caught or safe |
| `TIMING_BREACH` | Time-critical decisions | Action timing vs deadline + drift -> on-time or breach |
| `MISSION_COMPLETION` | Multi-objective completion | Objective completion set vs required set -> success branches |

Each primitive defines its own `trigger_condition_json` and `branch_rule_json` contract.

### FR-3: Environment RNG + Mode Semantics

Introduce explicit environment randomness separation.

- `ScenarioSeedManager` (already exists) becomes the canonical seed allocator
- Environment stochasticity uses seeded RNG from `ScenarioSeedManager`
- Agent action selection is separate from environment randomness
- TRAINING = random seeds, EVALUATION = pinned seed set (same code path), CALIBRATION = canonical seed set (same code path), REPLAY = recorded seed, no fresh randomness
- Persist enough state to replay branch outcomes exactly

### FR-4: Schema-Driven Theatre Spawning

Replace `can_spawn_theatre` boolean with evaluation of `theatre_spawn_rule_json`.

Spawn guards:
- Branch outcome type
- Minimum reward threshold
- Checkpoint class
- Run mode restrictions

Persist spawn provenance with run-scoped uniqueness.

### FR-5: Paradox Risk Orchestration

Promote paradox risk from read-time calculation to live backend orchestration.

Recalculate after:
1. Paradox task updates theatre/timeline stability or active paradox state
2. Material counter-signal ingestion
3. Investigation evidence freshness crossing configured threshold bands
4. Certificate/policy transitions that materially affect deployability interpretation

New service: `ParadoxRiskOrchestrator` (`backend/services/paradox_risk_orchestrator.py`) to centralize recalculation + persistence + event gating.

Keep on-read recompute as fallback only when missing/stale.

### FR-6: WebSocket Event Emission

Wire the release-ready runtime surfaces into live events:

| Event Type | Trigger | Payload |
|------------|---------|---------|
| `CHECKPOINT_RESOLVED` | Checkpoint resolves from schema evaluation | pack_id, run_id, checkpoint_id, selected_branch_id, reward, seed |
| `THEATRE_SPAWNED` | Derived theatre from checkpoint spawn rule | pack_id, run_id, checkpoint_id, theatre_id |
| `PARADOX_RISK_CHANGED` | Material risk delta after orchestrated recompute | theatre_id, old_level, new_level, factors, reason |

---

## 4. Scope Summary

| Area | What Ships | What Doesn't |
|------|-----------|--------------|
| Checkpoint Evaluator | Schema-driven evaluation, 5 primitives, branch rule contracts | New template families |
| Environment RNG | Seed separation, mode semantics, replay determinism | New run modes beyond the 4 |
| Theatre Spawning | Schema-driven spawn rules from `theatre_spawn_rule_json` | Rich spawn analytics |
| Paradox Risk | Live orchestration, 4 trigger paths, material WS emission | Historical risk charting, new inquiry classes |
| WebSocket | CHECKPOINT_RESOLVED, THEATRE_SPAWNED, PARADOX_RISK_CHANGED | Frontend event handling |
| Frontend | Nothing (backend only) | All UI work deferred to Alexander |

---

## 5. Success Criteria

### Sprint 0: Runtime Contract Tightening
- [ ] All checkpoint schema fields verified present and typed consistently
- [ ] Evaluator primitive set frozen: BINARY_RISK_GATE, RESOURCE_DEPLETION, DETECTION_EVENT, TIMING_BREACH, MISSION_COMPLETION
- [ ] `branch_rule_json` contract defined per primitive
- [ ] `trigger_condition_json` contract defined per primitive
- [ ] `theatre_spawn_rule_json` contract defined
- [ ] `PARADOX_RISK_CHANGED` materiality rule defined
- [ ] Stale-cache policy for paradox risk persistence locked

### Sprint 1: Schema-Driven Checkpoint Evaluation
- [ ] `CheckpointEvaluator` consumes trigger_condition_json, branch_rule_json, reward_mapping_json, theatre_spawn_rule_json
- [ ] Branch selection evaluates checkpoint state + agent action + seed + primitive config
- [ ] Determinism holds for identical (run config, agent actions, seed, checkpoint graph)
- [ ] Invalid/malformed runnable checkpoint configs fail fast with explicit error states
- [ ] CATALOG_ONLY templates remain non-runnable

### Sprint 2: Environment RNG + Mode Semantics
- [ ] ScenarioSeedManager is canonical seed allocator for all run paths
- [ ] Agent action selection separated from environment stochasticity
- [ ] Saboteur draws, hidden state, uncertainty sampling use seeded RNG
- [ ] Enough state persisted to replay branch outcomes exactly
- [ ] Parity tests: repeated runs with same seed, varying seeds in training, canonical seeds in calibration, exact replay

### Sprint 3: Derived Theatre Rules + Run Integrity
- [ ] `can_spawn_theatre` boolean replaced with `theatre_spawn_rule_json` evaluation
- [ ] Spawn guards: branch outcome type, minimum reward threshold, checkpoint class, run mode restrictions
- [ ] Spawn provenance persisted with run-scoped uniqueness
- [ ] Derived theatres scoped to originating pack/run lineage

### Sprint 4: Paradox Risk Orchestration
- [ ] `ParadoxRiskOrchestrator` service created
- [ ] Risk recalculates after: paradox state change, material counter-signal, evidence freshness threshold, certificate/policy transition
- [ ] Persisted risk snapshot on theatre updated
- [ ] On-read recompute kept as fallback only
- [ ] Material delta detection prevents event spam

### Sprint 5: WebSocket Emission + Integration + E2E
- [ ] `CHECKPOINT_RESOLVED` emitted on schema-driven evaluation
- [ ] `THEATRE_SPAWNED` emitted on derived theatre creation
- [ ] `PARADOX_RISK_CHANGED` emitted on material delta only
- [ ] Integration: runnable template -> create pack -> commit -> run with fixed seed -> checkpoint resolves from schema -> derived theatre spawns when rule passes -> replay reproduces exact path
- [ ] Integration: theatre/investigation mutation -> paradox risk updates -> material change emits WS event -> non-material recompute does not spam
- [ ] Regression against Cycle-019 APIs and Cycle-018 template catalog

---

## 6. Codebase Grounding

### Existing Infrastructure

| Component | Location | Current State |
|-----------|----------|---------------|
| Checkpoint evaluator | `backend/services/checkpoint_evaluator.py` | Hash-based branching, STAGED schema fields |
| ScenarioSeedManager | `backend/services/scenario_seed_manager.py` | Present, allocate_seed() with 4 modes |
| Theatre spawner | `backend/services/theatre_spawner.py` | Uses `can_spawn_theatre` boolean only |
| ParadoxRiskEvaluator | `backend/services/paradox_risk_evaluator.py` | 5 inquiry-class configs, on-read only |
| ScenarioCheckpoint model | `backend/database/models.py` (line ~795) | trigger_condition_json, theatre_spawn_rule_json, evaluator_type present |
| CheckpointBranch model | `backend/database/models.py` (line ~826) | branch_rule_json, outcome_type present |
| ScenarioRun model | `backend/database/models.py` (line ~886) | environment_seed, run_mode present |
| RunCheckpointResult model | `backend/database/models.py` (line ~918) | state_vector_json, spawned_theatre_id present |
| WS broadcast_checkpoint_resolved | `backend/websockets/realtime_manager.py` (line ~207) | Exists, not wired from live paths |
| WS broadcast_paradox_risk_changed | `backend/websockets/realtime_manager.py` (line ~252) | Exists, not wired from live paths |
| Scenario pack routes | `backend/api/scenario_pack_routes.py` | Template catalog, pack lifecycle, run/replay endpoints |
| Pack lifecycle service | `backend/services/scenario_pack_lifecycle.py` | Present |
| Theatre model | `backend/database/models.py` | paradox_risk_level, paradox_risk_factors_json, paradox_risk_updated_at present |

### EVALUATOR_PRIMITIVES (Already Defined)

```python
EVALUATOR_PRIMITIVES = {
    "BINARY_RISK_GATE",
    "RESOURCE_DEPLETION",
    "DETECTION_EVENT",
    "TIMING_BREACH",
    "MISSION_COMPLETION",
}
```

---

## 7. New / Updated Backend Services

| Service | File | Purpose |
|---------|------|---------|
| CheckpointEvaluator | `backend/services/checkpoint_evaluator.py` | Upgrade to true schema-driven checkpoint execution |
| ScenarioRunStateBuilder | `backend/services/scenario_run_state_builder.py` | Normalize checkpoint state vector input for evaluators |
| ParadoxRiskOrchestrator | `backend/services/paradox_risk_orchestrator.py` | Centralized recompute + persistence + event gating |

`ScenarioSeedManager` already exists and needs no structural changes.

---

## 8. API / Runtime Changes

### Scenario Packs

- `POST /api/v1/scenario-packs` remains restricted to `RUNNABLE` templates
- `POST /api/v1/scenario-packs/{id}/run` must fail if template checkpoint graph is not executable under v2 schema contract
- `GET /api/v1/scenario-packs/{id}/runs/{run_id}/tree` must reflect rule-evaluated branches
- `GET /api/v1/scenario-packs/{id}/runs/{run_id}/replay` must replay exact recorded path and environment outcomes

### Theatre / Paradox Risk

- `GET /api/v1/theatres/{id}` returns paradox risk from persisted orchestrated state (on-read fallback only)
- Theatre list/detail responses may expose freshness metadata for debugging

---

## 9. WebSocket Event Additions

| Event Type | Trigger | Payload |
|------------|---------|---------|
| `CHECKPOINT_RESOLVED` | Checkpoint resolves from schema-driven evaluation | pack_id, run_id, checkpoint_id, selected_branch_id, reward, seed |
| `THEATRE_SPAWNED` | Derived theatre created from checkpoint spawn rule | pack_id, run_id, checkpoint_id, theatre_id |
| `PARADOX_RISK_CHANGED` | Material risk delta after orchestrated recompute | theatre_id, old_level, new_level, factors, reason |

---

## 10. Test Targets

Release-hardening cycle, not small polish pass.

| Sprint | Tests | Focus |
|--------|-------|-------|
| 0 | 4 | Schema contract verification, primitive definitions, JSON contracts |
| 1 | 7 | Schema-driven evaluation, determinism, fail-fast, primitive branch logic |
| 2 | 6 | Seed reproducibility, mode semantics, replay parity |
| 3 | 5 | Spawn rule gating, provenance, mode restrictions |
| 4 | 6 | Paradox risk triggers, materiality, orchestrator service |
| 5 | 7 | WS emission, integration tests, regression |

Target: ~35 new tests. Post-020 expected: existing baseline + 35.

---

## 11. NFRs

1. **Determinism**: Identical (run config, agent actions, seed, checkpoint graph) must always produce identical branch outcomes.
2. **Fail-fast**: Invalid/malformed runnable checkpoint configs must produce explicit error states, not silent fallbacks.
3. **Performance**: Paradox risk recompute must not block API response paths. Orchestrator calls are fire-and-forget or background.
4. **Backward compatibility**: CATALOG_ONLY templates unaffected. Existing pack lifecycle endpoints unchanged. Existing theatre API responses unchanged (additive only).
5. **Material emission**: `PARADOX_RISK_CHANGED` emits only on material risk-level or material-factor delta, not every recompute.
6. **Separation**: Environment randomness from `ScenarioSeedManager`, not agent-provided. Agent actions are deterministic inputs, not randomness sources.

---

## 12. Release Decisions Frozen In This Cycle

1. `RUNNABLE` Scenario Pack templates must use true schema-driven evaluation.
2. Hash-only branch selection is no longer an acceptable shipping posture for runnable templates.
3. `CATALOG_ONLY` templates remain browseable but cannot run.
4. Paradox risk recomputation must be event-driven from backend mutation paths, not only on theatre detail reads.
5. `PARADOX_RISK_CHANGED` emits only on material risk-level or material-factor delta, not every recompute.

---

## 13. Out of Scope

- Frontend Scenario Pack lifecycle UI beyond what Alexander is implementing
- New Scenario Pack template families
- Agent breeding / genealogy work
- Rich visual family-tree or replay visualizer frontend work
- New inquiry classes
- Historical paradox-risk charting beyond current event/persistence needs
- Any frontend work (Alexander brief handles UI)
