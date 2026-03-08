# Sprint Plan — Cycle-018: Scenario Packs Engine

**Cycle:** cycle-018
**Date:** 6 March 2026
**PRD:** grimoires/loa/prd_018.md
**SDD:** grimoires/loa/sdd_018.md
**Sprints:** 6 (0–5)
**Baseline:** Post-017 (≥1100 passed)

---

## Sprint 0: Schema Foundation + Migration

Define all 7 new tables and extend Theatre with provenance column. No runtime logic.

### Task 0.1: Model Layer — All Scenario Pack Models

**Files modified:**
- `backend/database/models.py` — add 7 new model classes + extend Theatre

**New models:**
1. `ScenarioPackTemplate` — immutable template definition (id, name, family, template_status: RUNNABLE | CATALOG_ONLY, JSON blobs for objective_vector, fork_points, saboteurs, telemetry, settlement)
2. `ScenarioCheckpoint` — decision point within a template (template_id FK, sequence_num, trigger, trigger_condition_json, market_question, decision_window_sec, can_spawn_theatre, evaluator_type, theatre_spawn_rule_json)
3. `CheckpointBranch` — outcome path from checkpoint (checkpoint_id FK, label, branch_rule_json, outcome_type, reward_mapping_json, next_checkpoint_id)
4. `ScenarioPack` — user instance (user_id, template_id FK, state, run config fields, commitment_hash)
5. `ScenarioRun` — execution instance (pack_id FK, agent_id, status, environment_seed, run_mode: TRAINING | EVALUATION | CALIBRATION | REPLAY, telemetry_json)
6. `RunCheckpointResult` — outcome at checkpoint during run (run_id FK, checkpoint_id FK, branch_id FK, reward, spawned_theatre_id)
7. `ScenarioPackAuditEvent` — audit trail (pack_id FK, event_type, detail_json)

**Theatre extension:**
- Add `spawned_from_checkpoint_id` (nullable FK → scenario_checkpoints.id)

**Acceptance Criteria:**
- [ ] All 7 new models defined with correct relationships (back_populates)
- [ ] Theatre model has spawned_from_checkpoint_id column
- [ ] All FKs and indexes defined
- [ ] Existing model tests pass unchanged

### Task 0.2: Alembic Migration

**New file:** `backend/alembic/versions/c018_scenario_packs.py`

Dialect-safe migration creating 7 tables + 1 column:

1. Create `scenario_pack_templates` (PK: id String(100))
2. Create `scenario_checkpoints` (FK → templates)
3. Create `checkpoint_branches` (FK → checkpoints, self-FK → checkpoints for next_checkpoint_id)
4. Create `scenario_packs` (FK → templates)
5. Create `scenario_runs` (FK → packs)
6. Create `run_checkpoint_results` (FK → runs, checkpoints, branches, theatres)
7. Create `scenario_pack_audit_events` (FK → packs)
8. Add `spawned_from_checkpoint_id` to `theatres`
9. Create indexes: `ix_scenario_packs_state`, `ix_scenario_packs_template_id`, `ix_scenario_pack_templates_family`, `ix_scenario_runs_pack_id`, `ix_scenario_checkpoints_template_id`

2 tests:
1. Upgrade/downgrade round-trip
2. Verify all tables and columns exist after upgrade

**Acceptance Criteria:**
- [ ] Migration runs clean on PostgreSQL
- [ ] Migration runs clean on SQLite (dialect-safe)
- [ ] Downgrade removes all new tables/columns
- [ ] Both tests pass

### Task 0.3: Pydantic Schema Extensions

**New file:** `backend/schemas/scenario_packs.py`

Schema classes:
- `ObjectiveVectorComponent`, `ForkPointSchema`, `SaboteurCard` — nested components
- `ScenarioPackTemplateResponse`, `ScenarioPackTemplateSummaryResponse`, `TemplateListResponse`
- `ScenarioPackCreate`, `ScenarioPackResponse`
- `ScenarioRunResponse`
- `CheckpointResultResponse`
- `EpisodeTreeNode`, `EpisodeTreeResponse`

2 tests:
1. Template response serialises from model with computed checkpoint_count
2. Pack create validates template_id exists

**Acceptance Criteria:**
- [ ] All schemas use ConfigDict(from_attributes=True) for model conversion
- [ ] Computed fields (checkpoint_count) work via model_validator
- [ ] Both tests pass

### Task 0.4: Regression Check

Run full test suite. Confirm zero regressions from new tables.

**Acceptance Criteria:**
- [ ] All existing ≥1100 tests pass
- [ ] No new failures

### Sprint 0 Summary Target

- **4 tests**
- **2 new files, 1 modified**
- All scenario pack tables exist and are queryable
- Zero regressions

---

## Sprint 1: Template Catalog + Seeding

Seed the 18 scenario packs from the library. Build template catalog API. Wire frontend.

### Task 1.1: Template Seeder Service

**New file:** `backend/services/scenario_template_seeder.py`

Seed all 18 templates from `Echelon_Scenario_Packs_Library_v1.md`:

| Family | Templates |
|--------|-----------|
| NAV_UNC | Neon Courier, Midnight Exchange, Runway Intercept, Last Mile Hospital |
| SOC_NAV | Velvet Rope |
| MAN_FORCE | Skybridge Assembly, High-Rise Steel |
| MARL_C3 | Disaster Response, Cooling Plant, Reactor Protocol, Heist Echelon, Blacksite Heist |
| 3D_INERT | Orbital Salvage, Orbital Docking Court |
| LONG_HZN | Icebreaker Convoy |
| PUZ_LOGIC | Escape Room |
| ADV_AIR | Dogfight Echelon |
| PREC_MAN | Cleanroom Microsurgery |

For 4 templates with existing JSON fixtures (Neon Courier, Disaster Response, Orbital Salvage, Blacksite Heist): read `forkPointSchema` → create `ScenarioCheckpoint` + `CheckpointBranch` records from the structured JSON. Mark these as `template_status=RUNNABLE`.

For 14 templates without fixtures: create checkpoints from `Fork points` description and branches from listed options. Mark these as `template_status=CATALOG_ONLY`.

All seeded templates get `is_seeded=True`.

2 tests:
1. Seed all 18 → verify count and families
2. Re-seed is idempotent (no duplicates)

**Acceptance Criteria:**
- [ ] 18 templates created with correct families
- [ ] 4 JSON-fixture templates marked template_status=RUNNABLE with structured checkpoints from JSON
- [ ] 14 prose-only templates marked template_status=CATALOG_ONLY with checkpoints from library descriptions
- [ ] Idempotent re-seed
- [ ] Both tests pass

### Task 1.2: Template List API

**New file:** `backend/api/scenario_pack_routes.py`

```python
GET /api/v1/scenario-pack-templates?family=NAV_UNC&limit=20&offset=0
```

Returns `TemplateListResponse` with paginated summaries. Family filter is case-insensitive.

2 tests:
1. List all templates → 18 returned
2. Filter by family NAV_UNC → 4 returned

**Acceptance Criteria:**
- [ ] Pagination works (limit/offset)
- [ ] Family filter returns correct subset
- [ ] Both tests pass

### Task 1.3: Template Detail API

```python
GET /api/v1/scenario-pack-templates/{template_id}
```

Returns `ScenarioPackTemplateResponse` with full objective_vector, fork_points, saboteur_deck, and computed checkpoint_count.

1 test:
1. Get Neon Courier template → all fields present, checkpoint_count matches

**Acceptance Criteria:**
- [ ] Full template returned with all JSON blobs
- [ ] checkpoint_count computed from related checkpoints
- [ ] Test passes

### Task 1.4: Frontend — Wire ScenarioPacksPage to Catalog API

**Files modified:**
- `frontend/src/pages/ScenarioPacksPage.tsx` — replace empty shell with template grid
- New or existing hook for template catalog API call

Replace the concept cards and empty state with a real template grid from `/api/v1/scenario-pack-templates`. Each card shows: name, family badge, checkpoint count, fork range, episode length.

1 test:
1. Template cards render from API data with correct family badges

**Acceptance Criteria:**
- [ ] Cards render from real API data
- [ ] Family filter tabs work
- [ ] Loading/error states present
- [ ] Test passes

### Sprint 1 Summary Target

- **6 tests**
- **2 new files, 1 modified**
- 18 templates seeded, catalog API serves them, frontend renders cards

---

## Sprint 2: Pack Lifecycle

Create, commit, and run packs. State machine with run configuration.

### Task 2.1: Create Pack API

```python
POST /api/v1/scenario-packs
```

Creates `ScenarioPack` in DRAFT state from a RUNNABLE template_id. Rejects CATALOG_ONLY templates with 409 (or 422). Persists run configuration (run_mode, agent_assignment, simulation_scale, objective_profile). Auth required.

3 tests:
1. Create pack from RUNNABLE template → DRAFT state, correct template association
2. Create with invalid template_id → 404
3. Create from CATALOG_ONLY template → 409 rejection

**Acceptance Criteria:**
- [ ] Pack created in DRAFT with run config from RUNNABLE template
- [ ] CATALOG_ONLY template rejected with 409
- [ ] ScenarioPackAuditEvent(PACK_CREATED) logged
- [ ] All 3 tests pass

### Task 2.2: State Machine Transitions

**New file:** `backend/services/scenario_pack_lifecycle.py`

Valid transitions: DRAFT → COMMITTED, COMMITTED → ACTIVE, ACTIVE → SETTLING, SETTLING → RESOLVED.

Endpoints:
- `POST /api/v1/scenario-packs/{id}/commit` (DRAFT → COMMITTED)
- State transitions via lifecycle service (ACTIVE, SETTLING, RESOLVED are automatic)

3 tests:
1. Commit: DRAFT → COMMITTED with commitment_hash
2. Invalid transition: ACTIVE → COMMITTED → 409 Conflict
3. Get pack shows correct state after each transition

**Acceptance Criteria:**
- [ ] Only valid transitions succeed
- [ ] Invalid transitions return 409
- [ ] Audit events logged for each transition
- [ ] All 3 tests pass

### Task 2.3: Commitment Receipt

**Files modified:**
- `backend/services/scenario_pack_lifecycle.py` — generate commitment hash at commit time

Mirror theatre pattern: hash template_id + config + timestamp.

1 test:
1. Commit generates deterministic hash from pack contents

**Acceptance Criteria:**
- [ ] commitment_hash populated at commit
- [ ] committed_at timestamp set
- [ ] Test passes

### Task 2.4: Run Launch API

```python
POST /api/v1/scenario-packs/{id}/run
```

Transitions COMMITTED → ACTIVE, creates `ScenarioRun` in PENDING status. Returns run_id. Actual checkpoint evaluation happens async.

2 tests:
1. Launch run → ScenarioRun created, pack state ACTIVE
2. Launch on non-COMMITTED pack → 409

**Acceptance Criteria:**
- [ ] Run created with correct associations
- [ ] Pack transitions to ACTIVE
- [ ] Audit event PACK_RUN_STARTED logged
- [ ] Both tests pass

### Task 2.5: Frontend — Launch Configuration Panel

**Files modified:**
- `frontend/src/pages/ScenarioPacksPage.tsx` or new ScenarioPackDetailPage
- Hook for pack create + run API calls

Wire the launch config panel (Run Mode, Agent Assignment, Simulation Scale, Objective Profile dropdowns) to `POST /api/v1/scenario-packs` + `POST /api/v1/scenario-packs/{id}/run`.

1 test:
1. Launch Run button creates pack and starts run

**Acceptance Criteria:**
- [ ] Dropdowns submit correct config values
- [ ] Launch Run creates pack + commits + starts run
- [ ] Test passes

### Sprint 2 Summary Target

- **10 tests**
- **1 new file, 2 modified**
- Pack lifecycle works: create → commit → run
- CATALOG_ONLY templates rejected at pack creation

---

## Sprint 3: Checkpoint Resolution + Branching

Evaluate checkpoints sequentially. Record results. Build episode tree.

### Task 3.0: ScenarioSeedManager Service

**New file:** `backend/services/scenario_seed_manager.py`

Allocate environment seeds based on run_mode policy:
- `TRAINING` = random seed per run (stochastic, varying)
- `EVALUATION` = controlled stochasticity from a fixed seed set
- `CALIBRATION` = canonical seed set (e.g., [42, 137, 256, 512, 1024]) for cross-run comparability
- `REPLAY` = exact recorded seed from previous run, no fresh randomness

1 test:
1. Each run_mode produces correct seed behaviour (TRAINING varies, CALIBRATION uses canonical set, REPLAY reuses stored seed)

**Acceptance Criteria:**
- [ ] Seed allocation deterministic for CALIBRATION and REPLAY modes
- [ ] TRAINING mode produces distinct seeds across runs
- [ ] Test passes

### Task 3.1: CheckpointEvaluator Service

**New files:** `backend/services/checkpoint_evaluator.py`

Schema-driven checkpoint automation. Process checkpoints in `sequence_num` order using declarative checkpoint schemas. At each checkpoint:
1. Evaluate trigger_condition_json against current run state
2. Execute evaluator_type primitive (BINARY_RISK_GATE | RESOURCE_DEPLETION | DETECTION_EVENT | TIMING_BREACH | MISSION_COMPLETION)
3. Select branch via branch_rule_json, deterministically given (agent action, checkpoint state, environment seed, evaluator config)
4. Compute reward from reward_mapping_json + objective vector component weights
5. If theatre_spawn_rule_json present + can_spawn_theatre, flag for Theatre Spawner (Sprint 4)
6. Create RunCheckpointResult
7. Advance to next checkpoint via `branch.next_checkpoint_id`

4 tests:
1. Sequential evaluation through 3 checkpoints with seed → 3 results in order, deterministic
2. Branch selection based on agent decision + seed → correct branch chosen
3. Reward computation from objective vector weights
4. Run completes when no more checkpoints → status COMPLETED

**Acceptance Criteria:**
- [ ] Checkpoints evaluated in sequence_num order
- [ ] Branch selection is deterministic given (agent action, checkpoint state, environment seed, evaluator config)
- [ ] evaluator_type field used in selection logic
- [ ] trigger_condition_json, branch_rule_json, and reward_mapping_json are consumed by evaluator
- [ ] Seed parameter accepted and stored in run
- [ ] Rewards computed correctly
- [ ] theatre_spawn_rule_json is available for spawn decisions
- [ ] Run status transitions to COMPLETED when done
- [ ] All 4 tests pass

### Task 3.2: Result Recording + Branch Probabilities

**Files modified:**
- `backend/services/checkpoint_evaluator.py` — persist results
- `backend/api/scenario_pack_routes.py` — branch probability endpoint

```python
GET /api/v1/scenario-pack-templates/{template_id}/branch-probabilities
```

Returns `{checkpoint_id: {branch_id: probability}}` computed from completed runs.

2 tests:
1. After 10 runs, branch probabilities sum to 1.0 per checkpoint
2. With zero runs, all probabilities are null

**Acceptance Criteria:**
- [ ] Results persisted with correct foreign keys
- [ ] Branch probabilities computed from run history
- [ ] Both tests pass

### Task 3.3: Episode Tree API

```python
GET /api/v1/scenario-packs/{pack_id}/runs/{run_id}/tree
```

Returns `EpisodeTreeResponse` — the full tree structure showing which checkpoints were visited, which branches were taken, rewards at each node, and any spawned theatres.

1 test:
1. Completed run → tree has correct node structure and rewards

**Acceptance Criteria:**
- [ ] Tree structure matches checkpoint sequence
- [ ] Selected branches and rewards present at each node
- [ ] Test passes

### Task 3.4: Replay Output

```python
GET /api/v1/scenario-packs/{pack_id}/runs/{run_id}/replay
```

Returns a replay-compatible output (matching the existing `ForkReplay` shape from `frontend/src/types/replay.ts`) so the frontend replay components can render scenario results.

1 test:
1. Replay output includes checkpoint decisions as disclosure events

**Acceptance Criteria:**
- [ ] Output matches ForkReplay shape
- [ ] Checkpoint decisions map to disclosure events
- [ ] Test passes

### Sprint 3 Summary Target

- **9 tests** (1 seed manager + 4 evaluator + 2 probabilities + 1 tree + 1 replay)
- **2 new files, 1 modified**
- Seeds allocated by mode; checkpoints resolve; branches selected; results recorded; tree reconstructable

---

## Sprint 4: Derived Theatre Spawning

Checkpoints spawn real theatres with provenance. Spawned theatres use the existing pipeline.

### Task 4.1: TheatreSpawner Service

**New file:** `backend/services/theatre_spawner.py`

When a checkpoint with `can_spawn_theatre=True` resolves:
1. Create a Theatre record with `spawned_from_checkpoint_id` set
2. Use checkpoint's `market_question` as the theatre inquiry
3. Generate `construct_id` as `scenario_{pack_id}_run_{run_id}_cp_{checkpoint_id}` (includes run_id for per-run uniqueness)
4. Log `ScenarioPackAuditEvent(THEATRE_SPAWNED)`
5. Store `spawned_theatre_id` on the RunCheckpointResult

3 tests:
1. Checkpoint with can_spawn_theatre=True → Theatre created with provenance link and run_id in construct_id
2. Checkpoint with can_spawn_theatre=False → no theatre spawned
3. Spawned theatre has correct construct_id (including run_id) and spawned_from_checkpoint_id

**Acceptance Criteria:**
- [ ] Theatre created with correct provenance FK
- [ ] construct_id includes run_id: scenario_{pack_id}_run_{run_id}_cp_{checkpoint_id}
- [ ] Non-spawning checkpoints don't create theatres
- [ ] Audit event logged with theatre_id, checkpoint_id
- [ ] All 3 tests pass

### Task 4.2: Spawned Theatre Lifecycle

**Files modified:**
- `backend/services/theatre_spawner.py` — auto-commit spawned theatre

Spawned theatres enter the existing theatre lifecycle:
- Created in DRAFT → auto-committed → available for `/run`, `/settle`, `/certificate`
- Uses existing `CertificatePipeline` (including 017 routing + gates)

1 test:
1. Spawned theatre → commit → run → settle → certificate issued with routing hint

**Acceptance Criteria:**
- [ ] Spawned theatre follows normal lifecycle
- [ ] Certificate pipeline applies policy surface (017)
- [ ] Test passes

### Task 4.3: Derived Theatre API

```python
GET /api/v1/scenario-packs/{pack_id}/derived-theatres
```

Returns list of theatres where `spawned_from_checkpoint_id` belongs to this pack's template checkpoints.

1 test:
1. Pack with 2 spawning checkpoints → 2 theatres listed

**Acceptance Criteria:**
- [ ] Returns only theatres derived from this pack's checkpoints
- [ ] Includes theatre state and certificate status
- [ ] Test passes

### Task 4.4: Parent Pack Tracking + Audit Events

**Files modified:**
- `backend/services/checkpoint_evaluator.py` — call TheatreSpawner during evaluation
- Audit events: THEATRE_SPAWNED with detail_json containing theatre_id, checkpoint_id, market_question

1 test:
1. Audit trail shows THEATRE_SPAWNED events with correct detail

**Acceptance Criteria:**
- [ ] Audit events have full context
- [ ] Test passes

### Sprint 4 Summary Target

- **6 tests**
- **1 new file, 2 modified**
- Checkpoints spawn real theatres; provenance tracked; existing pipeline applies

---

## Sprint 5: RLMF Telemetry + Frontend Integration + Polish

Wire telemetry to exports. Frontend branch map + run status. E2E test.

### Task 5.1: RLMF Telemetry Export Integration

**New file:** `backend/services/scenario_telemetry_exporter.py`

Convert ScenarioRun + RunCheckpointResults into RLMF-compatible export records matching the existing `ExportFilter` shape:

```python
{
    "episode_id": run.id,
    "scenario_pack_id": run.pack_id,
    "template_id": template.id,
    "agent_id": run.agent_id,
    "actions": [checkpoint decisions...],
    "rewards": [per-checkpoint rewards...],
    "state_features": {aggregated state vectors},
    "fork_count": len(checkpoint_results),
    "episode_duration_sec": run.episode_duration_sec,
    "branch_path": [branch labels in order],
    "spawned_theatre_ids": [theatre ids],
}
```

1 test:
1. Completed run → export record has correct shape and all fields

**Acceptance Criteria:**
- [ ] Export record matches RLMF training data shape
- [ ] Test passes

### Task 5.2: WebSocket Events

**Files modified:**
- `backend/websockets/realtime_manager.py` — 3 new broadcast methods

New events:
- `SCENARIO_RUN_STATUS` — run status change (PENDING → RUNNING → COMPLETED)
- `CHECKPOINT_RESOLVED` — checkpoint resolved during a run
- `THEATRE_SPAWNED` — derived theatre created from checkpoint

Hook broadcasts into:
- `checkpoint_evaluator.py` → CHECKPOINT_RESOLVED
- `scenario_pack_lifecycle.py` → SCENARIO_RUN_STATUS
- `theatre_spawner.py` → THEATRE_SPAWNED

1 test:
1. Run completion triggers SCENARIO_RUN_STATUS(COMPLETED) WS event

**Acceptance Criteria:**
- [ ] All 3 event types broadcast correctly
- [ ] Test passes

### Task 5.3: Frontend — Branch Map Visualization

**Files modified:**
- `frontend/src/pages/ScenarioPacksPage.tsx` or new detail page component
- New component: branch map tree renderer

Render from `/runs/{id}/tree` API. Colour vocabulary:
- Start: purple (#8B5CF6)
- Checkpoint: orange (#F59E0B)
- Success: green (#10B981)
- Failure: red (#EF4444)
- Partial: dark orange (#D97706)
- Main path edges: purple
- Success branches: green
- Failure branches: red

1 test:
1. Branch map renders correct node count and colours from tree data

**Acceptance Criteria:**
- [ ] Tree structure renders from API data
- [ ] Correct colour vocabulary
- [ ] Test passes

### Task 5.4: Frontend — Run Status + Checkpoint Results + Derived Theatres

**Files modified:**
- Frontend scenario pack detail components
- WS subscription for SCENARIO_RUN_STATUS, CHECKPOINT_RESOLVED events

Show:
- Active run status with progress (checkpoint N of M)
- Resolved checkpoint results with branch taken, reward
- Derived theatre links (clickable to theatre detail page)

1 test:
1. Run status updates live via WS, checkpoint results display correctly

**Acceptance Criteria:**
- [ ] Run progress visible
- [ ] Checkpoint results display
- [ ] Derived theatre links work
- [ ] Test passes

### Task 5.5: E2E Test — Full Scenario Pack Lifecycle

1 test:
1. Create pack from Neon Courier template → commit → run → all checkpoints resolve → at least 1 theatre spawned → spawned theatre can be committed/run/settled → RLMF export record available

**Acceptance Criteria:**
- [ ] Full lifecycle works end-to-end
- [ ] All intermediate states correct
- [ ] Test passes

### Sprint 5 Summary Target

- **5 tests**
- **2 new files, multiple modified**
- RLMF telemetry wired; WS events live; branch map renders; E2E verified

---

## Test Summary

| Sprint | New Tests | Cumulative |
|--------|-----------|------------|
| 0 | 4 | 4 |
| 1 | 6 | 10 |
| 2 | 10 | 20 |
| 3 | 9 | 29 |
| 4 | 6 | 35 |
| 5 | 5 | 40 |

**Post-018 expected:** ≥1140 passed (1100 baseline + 40 new).

---

## Risk Register

| Risk | Mitigation |
|------|------------|
| 18 templates need manual seeding from prose descriptions | 4 have structured JSON fixtures; remaining 14 use library doc fork points/options |
| Checkpoint evaluation may be slow for complex trees | Sequential processing with async DB writes; index on run_id + checkpoint_id |
| Theatre spawning creates cross-entity dependencies | spawned_from_checkpoint_id is the only cross-reference; spawned theatres are fully independent after creation |
| ForkReplay shape may not perfectly match checkpoint results | Replay output adapter transforms checkpoint results to existing ForkReplay interface |
| RLMF export shape may evolve | Telemetry exporter is a separate service; shape changes are isolated |
