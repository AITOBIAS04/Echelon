# Sprint Plan — Cycle-020: Scenario Pack Evaluator v2 + Paradox Risk Orchestration

**Cycle:** cycle-020
**Date:** 7 March 2026
**PRD:** grimoires/loa/prd_020.md
**SDD:** grimoires/loa/sdd_020.md
**Sprints:** 6 (0–5)
**Total new tests:** 36
**Builder:** Loa (backend/runtime only)

---

## Sprint 0: Runtime Contract Tightening (5 tests)

Freeze the runtime contract and verify upstream dependency health before changing execution semantics.

### Task 0.1 — Dependency Health Check

**Files:**
- `grimoires/loa/context/echelon_cycle_020.md` (reference)
- `grimoires/loa/prd_020.md` (reference)
- `grimoires/loa/sdd_020.md` (reference)
- current Cycle 017/018/019 implementation files

**Work:**
- Verify live dependency surfaces used by 020 are present and green:
  - Cycle 017 policy/routing/coherence surfaces
  - Cycle 018 scenario-pack tables/routes/replay/derived-theatre surfaces
  - Cycle 019 investigation persistence + paradox-risk theatre fields
- Record any live code/doc drift that would block 020 implementation
- Freeze the regression baseline from the current post-019 suite before making runtime changes

**Acceptance criteria:**
- [ ] Dependency-health note recorded in cycle docs or implementation notes
- [ ] No unresolved blocking drift remains on active 017/018/019 dependency surfaces
- [ ] Post-019 regression baseline recorded

### Task 0.2 — Evaluator Primitive Contract Spec

**Files:**
- `backend/services/checkpoint_evaluator.py` (to be rewritten in Sprint 1)
- `backend/database/models.py` (reference only unless field typing needs cleanup)

**Work:**
- Freeze the v1 primitive set:
  - `BINARY_RISK_GATE`
  - `RESOURCE_DEPLETION`
  - `DETECTION_EVENT`
  - `TIMING_BREACH`
  - `MISSION_COMPLETION`
- Define the accepted config shape for:
  - `trigger_condition_json`
  - `branch_rule_json`
  - `reward_mapping_json`
  - `theatre_spawn_rule_json`
- Define required state inputs per primitive

**Acceptance criteria:**
- [ ] Each primitive has an explicit config contract
- [ ] Runnable checkpoint validation rules are documented in code/tests
- [ ] No primitive relies on pack-specific bespoke logic

### Task 0.3 — Paradox Risk Materiality Contract

**Files:**
- `backend/services/paradox_risk_evaluator.py`
- `backend/websockets/realtime_manager.py`

**Work:**
- Freeze the material-delta rule for `PARADOX_RISK_CHANGED`
- Define factor bands and emission thresholds
- Define stale-cache fallback policy for read-time recomputation

**Acceptance criteria:**
- [ ] Materiality rule is explicit and testable
- [ ] Read-time fallback policy is explicit
- [ ] WS emission contract is stable before Sprint 4/5

### Tests (5)

| # | Test | Type |
|---|------|------|
| 1 | Dependency-health verification for active 017/018/019 surfaces | Regression |
| 2 | Evaluator primitive config schema validation | Unit |
| 3 | Invalid runnable trigger config rejected | Unit |
| 4 | Invalid runnable branch config rejected | Unit |
| 5 | Paradox-risk materiality comparator behaves as specified | Unit |

---

## Sprint 1: Schema-Driven Checkpoint Evaluation (7 tests)

Replace hash-only branching with actual schema-driven evaluation for runnable templates.

### Task 1.1 — Rewrite CheckpointEvaluator

**Files:**
- `backend/services/checkpoint_evaluator.py`

**Work:**
- Remove hash-index branch selection as the primary runtime
- Build evaluation context from:
  - checkpoint config
  - agent action
  - normalized checkpoint state
  - environment seed
- Resolve branches by evaluating `branch_rule_json`
- Gate checkpoint resolution by `trigger_condition_json`
- Compute reward from branch/checkpoint reward mappings

**Acceptance criteria:**
- [ ] `CheckpointEvaluator` consumes `trigger_condition_json`
- [ ] `CheckpointEvaluator` consumes `branch_rule_json`
- [ ] `CheckpointEvaluator` consumes `reward_mapping_json`
- [ ] Same action + state + seed resolves the same branch deterministically

### Task 1.2 — Runnable Config Validation

**Files:**
- `backend/api/scenario_pack_routes.py`
- `backend/services/checkpoint_evaluator.py`

**Work:**
- Add validation path for runnable checkpoint graphs at run launch
- Fail fast on malformed config with explicit error messages
- Keep `CATALOG_ONLY` templates non-runnable

**Acceptance criteria:**
- [ ] Invalid runnable templates fail at run launch
- [ ] Error responses identify invalid trigger/branch/spawn config class
- [ ] `CATALOG_ONLY` launch guard remains intact

### Task 1.3 — State Vector Recording

**Files:**
- `backend/services/checkpoint_evaluator.py`
- `backend/database/models.py` (only if result schema needs additive fields)

**Work:**
- Persist evaluator state vector in `RunCheckpointResult.state_vector_json`
- Include enough context for deterministic replay and debugging

**Acceptance criteria:**
- [ ] Result records contain normalized state vectors
- [ ] State vectors are sufficient for replay diagnostics

### Tests (7)

| # | Test | Type |
|---|------|------|
| 1 | Trigger condition gates checkpoint resolution | Unit |
| 2 | Threshold branch rule selects expected branch | Unit |
| 3 | Categorical branch rule selects expected branch | Unit |
| 4 | Reward precedence branch > checkpoint > default works | Unit |
| 5 | Same seed + same state + same action gives same branch | Unit |
| 6 | Invalid runnable checkpoint config fails fast at run launch | Integration |
| 7 | RunCheckpointResult stores normalized state_vector_json | Integration |

---

## Sprint 2: Environment RNG + Mode Semantics (6 tests)

Make randomness explicit, mode-aware, and replay-safe.

### Task 2.1 — ScenarioSeedManager

**Files:**
- `backend/services/scenario_seed_manager.py` (new)
- `backend/api/scenario_pack_routes.py`
- `backend/services/scenario_pack_lifecycle.py`

**Work:**
- Implement canonical seed allocation per run mode
- Support:
  - fresh varying seeds for `TRAINING`
  - fixed seed sets for `EVALUATION`
  - canonical seed sets for `CALIBRATION`
  - persisted/reused seed for `REPLAY`

**Acceptance criteria:**
- [ ] Seed allocation is deterministic where required
- [ ] Run records persist environment seed correctly
- [ ] Replay does not allocate a fresh seed

### Task 2.2 — ScenarioRunStateBuilder

**Files:**
- `backend/services/scenario_run_state_builder.py` (new)
- `backend/services/checkpoint_evaluator.py`

**Work:**
- Build normalized checkpoint state from run + prior results
- Separate:
  - agent decisions
  - environment stochasticity
  - prior branch history

**Acceptance criteria:**
- [ ] State builder output is deterministic for same run history
- [ ] Evaluators no longer assemble ad hoc state internally

### Task 2.3 — Replay Integrity

**Files:**
- `backend/api/scenario_pack_routes.py`

**Work:**
- Ensure replay endpoints use recorded results and seed context
- Prevent replay from re-rolling environment uncertainty

**Acceptance criteria:**
- [ ] Replay reproduces exact stored path
- [ ] No fresh randomness appears during replay

### Tests (6)

| # | Test | Type |
|---|------|------|
| 1 | TRAINING mode allocates varying seeds | Unit |
| 2 | EVALUATION mode uses fixed seed set | Unit |
| 3 | CALIBRATION mode uses canonical seed set | Unit |
| 4 | REPLAY mode reuses persisted seed/path | Integration |
| 5 | State builder produces deterministic checkpoint state | Unit |
| 6 | Replay endpoint reproduces exact recorded branch path | Integration |

---

## Sprint 3: Derived Theatre Rules + Run Integrity (5 tests)

Move theatre spawning from coarse boolean behavior to explicit spawn-rule evaluation.

### Task 3.1 — Spawn Rule Evaluation

**Files:**
- `backend/services/checkpoint_evaluator.py`
- `backend/services/theatre_spawner.py`

**Work:**
- Evaluate `theatre_spawn_rule_json` before theatre creation
- Support rule gates such as:
  - required outcome type
  - minimum reward
  - run mode restriction
  - checkpoint class restriction

**Acceptance criteria:**
- [ ] Spawn only occurs when spawn rule passes
- [ ] Legacy `can_spawn_theatre` does not override a failing spawn rule

### Task 3.2 — Provenance Integrity

**Files:**
- `backend/services/theatre_spawner.py`
- `backend/api/scenario_pack_routes.py`

**Work:**
- Persist full spawn provenance:
  - pack id
  - run id
  - checkpoint id
  - selected branch id
  - seed / reward snapshot as needed
- Keep derived-theatre queries scoped to originating pack/run

**Acceptance criteria:**
- [ ] Spawned theatre construct ids remain run-scoped
- [ ] Derived-theatre query never leaks across packs using the same template

### Tests (5)

| # | Test | Type |
|---|------|------|
| 1 | Spawn rule blocks theatre creation when reward threshold fails | Integration |
| 2 | Spawn rule blocks theatre creation for disallowed run mode | Integration |
| 3 | Spawn rule allows theatre creation when conditions pass | Integration |
| 4 | Spawned theatre provenance fields are persisted correctly | Integration |
| 5 | Derived-theatre query remains pack-scoped after spawn-rule upgrade | Integration |

---

## Sprint 4: Paradox Risk Orchestration (6 tests)

Promote paradox risk from read-time fallback to live mutation-driven orchestration.

### Task 4.1 — ParadoxRiskOrchestrator

**Files:**
- `backend/services/paradox_risk_orchestrator.py` (new)
- `backend/services/paradox_risk_evaluator.py`

**Work:**
- Implement centralized recompute service
- Load theatre context, evaluate risk, compare old/new, persist snapshot
- Return structured material-delta result

**Acceptance criteria:**
- [ ] Orchestrator persists updated risk snapshot
- [ ] Material delta calculation is reusable by mutation paths and WS events

### Task 4.2 — Mutation Path Hooks

**Files:**
- `backend/worker/tasks/paradox.py`
- `backend/api/investigation_routes.py`
- any evidence freshness / counter-signal mutation path touched in current implementation

**Work:**
- Trigger orchestrator after:
  - paradox-state updates
  - material counter-signal ingestion
  - evidence freshness threshold crossings
- Keep theatre detail read as fallback only

**Acceptance criteria:**
- [ ] At least the three committed mutation paths call the orchestrator
- [ ] Theatre detail path no longer carries the primary update burden

### Task 4.3 — Theatre Read Fallback Cleanup

**Files:**
- `backend/api/theatre_routes.py`

**Work:**
- Retain fallback recompute only if risk snapshot is missing/stale
- Avoid duplicate recompute when orchestration has already updated current state

**Acceptance criteria:**
- [ ] Theatre reads still return valid risk if orchestration missed an update
- [ ] Fallback path does not spam writes unnecessarily

### Tests (6)

| # | Test | Type |
|---|------|------|
| 1 | Orchestrator persists updated risk level/factors | Integration |
| 2 | Material counter-signal ingestion triggers recompute | Integration |
| 3 | Paradox-state update triggers recompute | Integration |
| 4 | Evidence freshness threshold crossing triggers recompute | Integration |
| 5 | Theatre detail read recomputes only when snapshot missing/stale | Integration |
| 6 | Inquiry-class weighting remains intact through orchestrated recompute | Unit |

---

## Sprint 5: WebSocket Emission + Integration + E2E (7 tests)

Expose the hardened runtime as a coherent live backend surface.

### Task 5.1 — Scenario Runtime Events

**Files:**
- `backend/websockets/realtime_manager.py`
- `backend/services/checkpoint_evaluator.py`
- `backend/services/theatre_spawner.py`

**Work:**
- Emit:
  - `CHECKPOINT_RESOLVED`
  - `THEATRE_SPAWNED`
- Ensure payloads reflect true schema-driven outcomes

**Acceptance criteria:**
- [ ] Scenario events contain correct pack/run/checkpoint identifiers
- [ ] Event payloads match recorded results, not inferred placeholders

### Task 5.2 — Paradox Risk Material WS Emission

**Files:**
- `backend/websockets/realtime_manager.py`
- `backend/services/paradox_risk_orchestrator.py`

**Work:**
- Emit `PARADOX_RISK_CHANGED` only when material delta comparator says so
- Include reason + factors in payload

**Acceptance criteria:**
- [ ] Material change emits one event
- [ ] Non-material recompute emits no event

### Task 5.3 — Integration / E2E

**Work:**
- Add full integration path:
  - create pack
  - commit
  - run with fixed seed
  - schema-driven checkpoints resolve
  - spawn rule creates theatre only when allowed
  - replay reproduces exact path
- Add risk path:
  - mutation triggers recompute
  - persisted risk updates
  - material WS event emitted once

**Acceptance criteria:**
- [ ] Scenario run lifecycle passes end to end
- [ ] Risk lifecycle passes end to end
- [ ] Full regression suite remains green

### Tests (7)

| # | Test | Type |
|---|------|------|
| 1 | CHECKPOINT_RESOLVED WS payload matches recorded result | Integration |
| 2 | THEATRE_SPAWNED WS payload matches spawned theatre provenance | Integration |
| 3 | PARADOX_RISK_CHANGED emits on material delta | Integration |
| 4 | PARADOX_RISK_CHANGED does not emit on non-material recompute | Integration |
| 5 | End-to-end scenario run resolves from schema and replays exactly | E2E |
| 6 | End-to-end spawn rule creates theatre only when allowed | E2E |
| 7 | End-to-end risk mutation path persists update and emits one WS event | E2E |

---

## Cycle 020 Summary Target

- **36 tests**
- **2 new core services + 2 new support services**
- Scenario Packs upgraded from staged hash-branching to real schema-driven execution
- Paradox risk upgraded from passive field to live orchestration + material WS signal
- Existing route/API shapes preserved where possible
- Regression suite green against the post-019 baseline
