# Cycle-020: Scenario Pack Evaluator v2 + Paradox Risk Orchestration

**Date:** 7 March 2026
**Depends on:** Cycle-019 (Agent Deployment + Investigation Persistence + Paradox Risk), Cycle-018 (Scenario Packs Engine), Cycle-017 (Policy Surface)
**Sprints:** 6 (0–5)
**Builder:** Loa (backend/runtime only — Alexander handles frontend scenario lifecycle UI)
**Scope:** Convert Scenario Packs from the current staged deterministic runtime into a release-ready schema-driven checkpoint engine, and convert paradox risk from passive/on-read computation into an event-driven live policy signal with material WebSocket emission.

---

## Why This Cycle Exists

Cycle 018 shipped the Scenario Packs backend, but its runtime posture is intentionally downgraded: checkpoints are persisted with schema fields, yet branch selection is still hash-based rather than rule-driven. That was acceptable as an honest staged implementation while Scenario Packs were still emerging.

That is no longer enough.

The product is moving beyond demo/catalog posture and into real testing and release preparation. Once Scenario Packs are treated as real training, evaluation, calibration, and replay environments, the backend must honor the actual checkpoint contract:

- checkpoints must be evaluated from declarative schema
- branch selection must depend on action, state, seed, and evaluator config
- theatre spawning must follow explicit spawn rules
- run semantics must be reproducible across modes

Cycle 019 also shipped paradox risk on theatre detail reads, but that is still a partial implementation. Risk exists as a field, not yet as a live operational signal. For release posture, paradox risk must recalculate from real mutation paths and emit events when materially changed.

Cycle 020 is the hardening cycle that closes both gaps.

---

## Product Contracts

### Scenario Packs Are Real Runtime Surfaces

Scenario Packs are no longer treated as catalog/demo-only backend artifacts. For `RUNNABLE` templates, the engine must execute the stored checkpoint graph as the source of truth.

This means:

- no bespoke Python per pack
- no hash-only branch selection pretending to be schema-driven
- no agent-driven randomness
- no hidden divergence between stored checkpoint config and runtime behavior

### Checkpoint Evaluation Contract

Every runnable checkpoint must be executable from stored configuration:

- `trigger_condition_json`
- `decision_window_sec`
- `evaluator_type`
- `branch_rule_json`
- `reward_mapping_json`
- optional `theatre_spawn_rule_json`

Branch resolution must be deterministic given:

- agent action
- checkpoint state
- environment seed
- evaluator config

### Environment Randomness Contract

Agents provide actions, policies, and strategy. They do **not** provide randomness.

Randomness comes from the environment via explicit seeded RNG:

- event rolls
- hidden state variation
- saboteur deck draws
- bounded uncertainty / noise sampling

Run modes remain:

- `TRAINING`: stochastic, varying seeds
- `EVALUATION`: controlled stochasticity from a fixed seed set
- `CALIBRATION`: canonical seed set for comparability
- `REPLAY`: exact recorded path, no fresh randomness

### Paradox Risk Contract

Paradox risk is a live policy signal, not a static field and not a read-only decoration.

It must:

- recalculate from real theatre/investigation/paradox mutations
- persist the latest assessed state for efficient reads
- emit `PARADOX_RISK_CHANGED` only on material delta
- remain inquiry-class-aware

Theatre language remains:

- `LOW`
- `WATCH`
- `HIGH`

Explanations use:

- Evidence weak
- Counter-signals rising
- Logic gap widening
- Stale investigation
- Paradox active

---

## What Already Exists

### Scenario Pack Runtime (Current State)

| Component | Location | Current State |
|-----------|----------|---------------|
| Scenario pack models | `backend/database/models.py` | Present |
| Template catalog + seeding | `backend/api/scenario_pack_routes.py`, seeder services | Present |
| Pack lifecycle | `backend/services/scenario_pack_lifecycle.py` | Present |
| Checkpoint evaluator | `backend/services/checkpoint_evaluator.py` | Staged: deterministic hash-based branching |
| Theatre spawning | `backend/services/theatre_spawner.py` | Present |
| Replay/tree endpoints | `backend/api/scenario_pack_routes.py` | Present |
| Frontend catalog | `frontend/src/pages/ScenarioPacksPage.tsx` | Template browsing only |

### Paradox Risk (Current State)

| Component | Location | Current State |
|-----------|----------|---------------|
| ParadoxRiskEvaluator | `backend/services/paradox_risk_evaluator.py` | Present |
| Theatre fields | `backend/database/models.py` | `paradox_risk_level`, `paradox_risk_factors_json`, `paradox_risk_updated_at` present |
| Theatre detail read path | `backend/api/theatre_routes.py` | Computes on read if missing/stale |
| WebSocket event type | `backend/websockets/realtime_manager.py` | Contract exists / may be partially wired |
| Trigger orchestration | mutation paths | Not complete |

---

## Release Decisions Frozen In This Cycle

1. `RUNNABLE` Scenario Pack templates must use true schema-driven evaluation.
2. Hash-only branch selection is no longer an acceptable shipping posture for runnable templates.
3. `CATALOG_ONLY` templates remain browseable but cannot run.
4. Paradox risk recomputation must be event-driven from backend mutation paths, not only on theatre detail reads.
5. `PARADOX_RISK_CHANGED` emits only on material risk-level or material-factor delta, not every recompute.

---

## Sprint Plan

### Sprint 0: Runtime Contract Tightening

Freeze the runtime contract and align models/services/tests to it before deeper implementation.

- Verify all checkpoint schema fields required by runtime are present and typed consistently
- Confirm evaluator primitive set for v1:
  - `BINARY_RISK_GATE`
  - `RESOURCE_DEPLETION`
  - `DETECTION_EVENT`
  - `TIMING_BREACH`
  - `MISSION_COMPLETION`
- Define `branch_rule_json` contract per primitive
- Define `trigger_condition_json` contract per primitive
- Define `theatre_spawn_rule_json` contract for derived theatre creation
- Define `PARADOX_RISK_CHANGED` materiality rule
- Lock exact stale-cache policy for paradox risk persistence

### Sprint 1: Schema-Driven Checkpoint Evaluation

Replace hash-only branching with true evaluator-driven resolution.

- `CheckpointEvaluator` must consume:
  - `trigger_condition_json`
  - `branch_rule_json`
  - `reward_mapping_json`
  - `theatre_spawn_rule_json`
- Branch selection must evaluate checkpoint state + agent action + seed + primitive config
- Determinism must hold for identical `(run config, agent actions, seed, checkpoint graph)`
- Invalid/malformed runnable checkpoint configs must fail fast with explicit error states
- `CATALOG_ONLY` templates remain non-runnable

### Sprint 2: Environment RNG + Mode Semantics

Make randomness explicit and reproducible across run modes.

- Introduce `ScenarioSeedManager` as the canonical seed allocator
- Separate:
  - agent action selection
  - environment stochasticity
  - replayed historical path
- Ensure saboteur draws, hidden state, and uncertainty sampling use seeded RNG
- Persist enough state to replay branch outcomes exactly
- Add parity tests across:
  - repeated runs with same seed
  - varying seeds in training
  - canonical seed sets in calibration
  - exact replay without new randomness

### Sprint 3: Derived Theatre Rules + Run Integrity

Make derived theatre spawning follow checkpoint schema rather than a coarse boolean.

- Replace `can_spawn_theatre`-only behavior with evaluation of `theatre_spawn_rule_json`
- Support spawn guards such as:
  - branch outcome type
  - minimum reward threshold
  - checkpoint class
  - run mode restrictions
- Persist spawn provenance with run-scoped uniqueness
- Ensure derived theatres are always scoped to originating pack/run lineage in queries and audit

### Sprint 4: Paradox Risk Orchestration

Promote paradox risk from read-time calculation to live backend orchestration.

- Recalculate paradox risk after:
  - paradox task updates theatre/timeline stability or active paradox state
  - material counter-signal ingestion
  - investigation evidence freshness crossing configured threshold bands
  - certificate/policy transitions that materially affect deployability interpretation, if applicable
- Persist updated risk snapshot on theatre
- Keep on-read recompute as fallback only when missing/stale
- Add a service/orchestrator to centralize recalculation calls

### Sprint 5: WebSocket Emission + Integration + E2E

Wire the release-ready runtime surfaces into live events and regression coverage.

- Emit `PARADOX_RISK_CHANGED` on material delta only
- Ensure Scenario Pack run events reflect real checkpoint evaluation results, not hash-only placeholder semantics
- Integration test:
  - runnable template
  - create pack
  - commit
  - run with fixed seed
  - checkpoint graph resolves from schema
  - derived theatre spawns only when spawn rule passes
  - replay reproduces exact path
- Integration test:
  - theatre / investigation mutation updates paradox risk
  - material change emits one WS event
  - non-material recompute does not spam events

---

## New / Updated Backend Services

| Service | File | Purpose |
|---------|------|---------|
| CheckpointEvaluator | `backend/services/checkpoint_evaluator.py` | Upgrade to true schema-driven checkpoint execution |
| ScenarioSeedManager | `backend/services/scenario_seed_manager.py` | Canonical run seed allocation and RNG policy |
| ScenarioRunStateBuilder | `backend/services/scenario_run_state_builder.py` | Normalize checkpoint state vector input for evaluators |
| ParadoxRiskOrchestrator | `backend/services/paradox_risk_orchestrator.py` | Centralized recompute + persistence + event gating |

---

## API / Runtime Changes

### Scenario Packs

- `POST /api/v1/scenario-packs` remains restricted to `RUNNABLE` templates
- `POST /api/v1/scenario-packs/{id}/run` must fail if template checkpoint graph is not executable under the v2 schema contract
- `GET /api/v1/scenario-packs/{id}/runs/{run_id}/tree` must reflect rule-evaluated branches
- `GET /api/v1/scenario-packs/{id}/runs/{run_id}/replay` must replay exact recorded path and environment outcomes

### Theatre / Paradox Risk

- `GET /api/v1/theatres/{id}` still returns paradox risk, but now primarily from persisted orchestrated state
- theatre list/detail responses may expose freshness metadata if needed for debugging or admin visibility

---

## WebSocket Event Requirements

| Event Type | Trigger | Payload |
|------------|---------|---------|
| `CHECKPOINT_RESOLVED` | Checkpoint resolves from schema-driven evaluation | pack_id, run_id, checkpoint_id, selected_branch_id, reward, seed |
| `THEATRE_SPAWNED` | Derived theatre created from checkpoint spawn rule | pack_id, run_id, checkpoint_id, theatre_id |
| `PARADOX_RISK_CHANGED` | Material risk delta after orchestrated recompute | theatre_id, old_level, new_level, factors, reason |

---

## Test Targets

Target this cycle as release-hardening, not just feature addition.

- schema contract tests for each evaluator primitive
- deterministic replay tests
- seed reproducibility tests
- malformed checkpoint config rejection tests
- spawn-rule gating tests
- paradox-risk trigger tests
- websocket materiality tests
- full integration tests for scenario runs and paradox updates

Exact test count can be set in PRD/SDD after discovery, but this cycle should be treated as a substantive backend hardening cycle rather than a small polish pass.

---

## Out of Scope

- Frontend Scenario Pack lifecycle UI beyond what Alexander is implementing
- New Scenario Pack template families
- Agent breeding / genealogy work
- Rich visual family-tree or replay visualizer frontend work
- New inquiry classes
- Historical paradox-risk charting beyond current event/persistence needs

---

## Relationship to Alexander

Alexander handles the frontend Scenario Pack lifecycle surfaces and any frontend deployment flow updates. This cycle gives him a release-ready backend:

- real checkpoint resolution semantics
- deterministic run/replay behavior
- derived theatre spawn rules that match product semantics
- live paradox risk behavior instead of passive read-time decoration

Cycle 020 should be complete before frontend release polish is considered final.
