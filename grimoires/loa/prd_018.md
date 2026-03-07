# PRD — Cycle-018: Scenario Packs Engine

**Cycle:** cycle-018
**Date:** 6 March 2026
**Predecessor:** cycle-017 (Policy Surface), cycle-016 (Results Surface), cycle-014c (Investigation Toolset), cycle-013 (Agent Runtime), cycle-010a (LMSR)
**Sprints:** 6 total (0–5)
**Design input:** `Echelon_Scenario_Packs_Library_v1.md` (Obsidian), `output/design_reference/echelon_scenario_packs_v1.html`, frontend theatre template JSON fixtures, `HANDOFF_MATRIX_ALEXANDER.md`
**Baseline:** Post-017 test count (≥1100 passed)

---

## 1. Problem Statement

The platform distinguishes two product concepts: **Theatre Templates** (market/certificate templates — inquiry class, resolution logic, evidence rules) and **Scenario Packs** (embodied RL engagement templates — objective vectors, checkpoint branching, saboteur decks, settlement rules, telemetry). Theatres resolve to one outcome via one contract. Scenario packs produce a tree of outcomes across multiple decision points.

The frontend already has:
- A `ScenarioPacksPage` shell at `/scenario-packs` with empty-state messaging and concept cards ("Branching Outcomes", "RLMF Telemetry", "Derived Theatres")
- A design reference document (`echelon_scenario_packs_v1.html`) specifying branch map visualization, launch configuration, checkpoint structure
- 4 theatre template JSON fixtures (`NEON_COURIER_V1.json`, `DISASTER_RESPONSE_V1.json`, `ORBITAL_SALVAGE_V1.json`, `BLACKSITE_HEIST_V1.json`) that already carry `forkPointSchema`, `objectiveVector`, `saboteurDeck`, `telemetrySpec`, and `settlementRules`
- Mock launchpad and replay APIs with phase/category taxonomy and fork disclosure events
- RLMF export infrastructure downstream

The backend has **nothing**:
- No `ScenarioPack` or `Checkpoint` database models
- No scenario pack API endpoints
- No pack runner or checkpoint resolution logic
- No derived theatre spawning mechanism
- No scenario-to-RLMF telemetry pipeline

The Scenario Packs Library v1 defines **18 scenario packs** across **9 template families** (NAV-UNC, SOC-NAV, MAN-FORCE, MARL-C3, 3D-INERT, LONG-HZN, PUZ-LOGIC, ADV-AIR, PREC-MAN) with a branching checkpoint model where each checkpoint is a decision point that branches the scenario into different outcome paths.

This cycle builds the **Scenario Packs Engine**: the backend schema, template catalog, pack lifecycle, checkpoint resolution, derived theatre spawning, and RLMF telemetry hooks — then wires the frontend to real data.

> Sources: Echelon_Scenario_Packs_Library_v1.md, echelon_scenario_packs_v1.html, frontend theatre template JSON fixtures, fork_manager.py

## 2. Objective

### Sprint 0: Schema Foundation + Migration

Define all scenario pack models: `ScenarioPackTemplate`, `ScenarioPack`, `ScenarioCheckpoint`, `CheckpointBranch`, `ScenarioRun`, `RunCheckpointResult`, `ScenarioPackAuditEvent`. Create the Alembic migration. Extend Pydantic schemas. No runtime logic.

### Sprint 1: Template Catalog + Seeding

Build template CRUD. Seed the 18 scenario packs from the library document as `ScenarioPackTemplate` records. List/detail API for the template catalog. Frontend: wire ScenarioPacksPage to real template data.

### Sprint 2: Pack Lifecycle

Pack creation from template, state machine (DRAFT → COMMITTED → ACTIVE → SETTLING → RESOLVED), commitment receipt generation. Mirrors the Theatre lifecycle pattern. Run configuration (run mode, agent assignment, simulation scale, objective profile).

### Sprint 3: Checkpoint Resolution + Branching

Schema-driven checkpoint evaluation engine. Checkpoints are declarative — each defines trigger condition, decision window, evaluator type, branch rules, reward mapping, and optional theatre-spawn rule. The engine auto-evaluates using reusable evaluator primitives (BINARY_RISK_GATE, RESOURCE_DEPLETION, DETECTION_EVENT, TIMING_BREACH, MISSION_COMPLETION). Branch selection is deterministic given (agent action, checkpoint state, environment seed, evaluator config). Environment randomness is explicit and seed-driven. Branch probabilities tracked. Replay output for the full episode tree.

### Sprint 4: Derived Theatre Spawning

Individual checkpoints within a scenario pack spawn separate theatres or sub-markets. The principle: "scenario packs can spawn theatres, theatres do not contain scenario packs." Spawned theatres are real Theatre records with a `spawned_from_checkpoint_id` provenance link.

### Sprint 5: RLMF Telemetry + Frontend Integration + Polish

Wire scenario run telemetry to RLMF export infrastructure. Frontend: branch map visualization, launch configuration panel, run status, checkpoint results. Polish and test.

## 3. Success Criteria

### SC-0: Schema Foundation

1. All scenario pack models present as tables in the database
2. Migration is dialect-safe (PostgreSQL + SQLite)
3. All existing tests still pass (zero regressions)
4. Pydantic response schemas extended for all new entities
5. Template API includes `template_status` field (RUNNABLE | CATALOG_ONLY)

### SC-1: Template Catalog

1. 4 JSON-fixture-backed templates seeded as RUNNABLE; 14 prose-only templates as CATALOG_ONLY
2. `GET /api/v1/scenario-pack-templates` returns paginated list with family filter and template_status
3. `GET /api/v1/scenario-pack-templates/{id}` returns full template with checkpoint schema and template_status
4. Frontend ScenarioPacksPage renders real template cards from API, distinguishing RUNNABLE vs CATALOG_ONLY
5. Template families (NAV-UNC, SOC-NAV, etc.) are filterable

### SC-2: Pack Lifecycle

1. `POST /api/v1/scenario-packs` creates a pack from a RUNNABLE template (rejects CATALOG_ONLY with 409)
2. State machine enforces valid transitions (DRAFT → COMMITTED → ACTIVE → SETTLING → RESOLVED)
3. Commitment receipt generated at commit time
4. Run configuration persisted: run_mode (TRAINING | EVALUATION | CALIBRATION | REPLAY), agent_assignment, simulation_scale, objective_profile
5. `POST /api/v1/scenario-packs/{id}/run` starts an async run with environment_seed and run_mode on the ScenarioRun

### SC-3: Checkpoint Resolution

1. CheckpointEvaluator service processes checkpoints in sequence order using declarative checkpoint schemas
2. Built-in evaluator primitives: BINARY_RISK_GATE, RESOURCE_DEPLETION, DETECTION_EVENT, TIMING_BREACH, MISSION_COMPLETION
3. Branch selection is deterministic given (agent action, checkpoint state, environment seed, evaluator config)
4. Run modes define RNG semantics: TRAINING (stochastic varying seeds), EVALUATION (controlled stochasticity from fixed seed set), CALIBRATION (canonical seed set), REPLAY (exact recorded path)
5. ScenarioSeedManager allocates seeds per run based on run_mode policy
6. Agent decisions recorded per checkpoint with environment seed
7. Branch probabilities computed across completed runnable runs
8. Full episode tree reconstructable from checkpoint results
9. Replay output for completed runs

### SC-4: Derived Theatre Spawning

1. Checkpoints with `can_spawn_theatre=true` produce real Theatre records
2. Spawned theatres carry `spawned_from_checkpoint_id` provenance with per-run uniqueness in construct_id
3. construct_id format: `scenario_{pack_id}_run_{run_id}_cp_{checkpoint_id}`
4. Spawned theatres follow normal theatre lifecycle (commit → run → settle → certificate)
5. Parent pack tracks spawned theatre count and IDs
6. API: `GET /api/v1/scenario-packs/{id}/derived-theatres` lists spawned theatres

### SC-5: RLMF Telemetry + Polish

1. Scenario run telemetry (agent decisions, state vectors, rewards, fork counts, episode duration) available to RLMF export pipeline
2. Frontend branch map renders checkpoint tree from API data
3. Launch configuration panel submits to real API
4. Run status updates via WebSocket
5. All new UI has loading, empty, error states

### SC-6: Test Gate

1. Post-017 baseline maintained (≥1100 passed)
2. Zero new test failures
3. 40 new tests across backend and frontend
4. Post-018 expected: ≥1140 passed

## 4. Codebase Grounding

### Existing Infrastructure (018 Dependencies)

| Component | Location | Relevance |
|-----------|----------|-----------|
| Theatre model + lifecycle | `backend/database/models.py`, `backend/api/theatre_routes.py` | Pattern template for pack lifecycle |
| TheatreTemplate model | `backend/database/models.py` | Pattern for ScenarioPackTemplate |
| Fork manager | `backend/fork_manager.py` | ForkType, ForkStatus, ForkPoint primitives |
| Theatre template fixtures | `frontend/dist/theatres/*.json` | Data shape: objectiveVector, forkPointSchema, saboteurDeck |
| ScenarioPacksPage | `frontend/src/pages/ScenarioPacksPage.tsx` | Empty shell, ready for API wiring |
| Design reference | `output/design_reference/echelon_scenario_packs_v1.html` | Full UI spec for branch map, launch config |
| Mock launchpad API | `frontend/src/api/launchpad.ts` | Phase/category taxonomy to replace with real API |
| Mock replay API | `frontend/src/api/replay.ts` | Fork replay shape to align with checkpoint results |
| RLMF export infrastructure | `frontend/src/api/exports.ts`, `frontend/src/pages/RLMFPage.tsx` | Downstream consumer of scenario telemetry |
| WebSocket manager | `backend/websockets/realtime_manager.py` | Extension point for run status events |
| Certificate pipeline | `backend/services/certificate_pipeline.py` | Spawned theatres use existing pipeline |
| Game loop | `backend/worker/game_loop.py` | Extension point for checkpoint evaluation cadence |

### Template Fixture Data Shape (existing)

The theatre template JSON fixtures already define the data shape for scenario packs:

```json
{
  "meta": { "name", "id", "type", "episodeLengthSec", "forkPointsPerRunRange", "settlementLatencySec" },
  "objectiveVector": [{ "component", "weight", "description" }],
  "telemetrySpec": { "snapshotHz", "estimatedSnapshotsPerEpisode", "keyStateVectors" },
  "forkPointSchema": [{ "trigger", "marketQuestion", "options", "decisionWindowSec" }],
  "saboteurDeck": [{ "card", "price", "boundedEffect", "notes" }],
  "settlementRules": { "oracle", "success", "failure", "paradoxRule" }
}
```

`forkPointSchema` entries map directly to `ScenarioCheckpoint` records. `options` within each fork point map to `CheckpointBranch` records.

## 5. Sprint Breakdown

### Sprint 0: Schema Foundation + Migration (4 tasks)

| Task | Description | Tests |
|------|-------------|-------|
| 0.1 | Model layer: ScenarioPackTemplate, ScenarioPack, ScenarioCheckpoint, CheckpointBranch, ScenarioRun, RunCheckpointResult, ScenarioPackAuditEvent | — |
| 0.2 | Alembic migration (dialect-safe, 7 new tables) | 2 |
| 0.3 | Pydantic schemas for all new entities | 2 |
| 0.4 | Regression test: existing tests pass with new tables | — |

**Sprint 0 total:** 4 tests

### Sprint 1: Template Catalog + Seeding (5 tasks)

| Task | Description | Tests |
|------|-------------|-------|
| 1.1 | Template seeder — convert 18 library entries + 4 existing fixtures to ScenarioPackTemplate records | 2 |
| 1.2 | `GET /api/v1/scenario-pack-templates` — paginated list with family filter | 2 |
| 1.3 | `GET /api/v1/scenario-pack-templates/{id}` — detail with checkpoints, objective vector, saboteur deck | 1 |
| 1.4 | Frontend: wire ScenarioPacksPage to template catalog API | 1 |
| 1.5 | Sprint 1 integration test | — |

**Sprint 1 total:** 6 tests

### Sprint 2: Pack Lifecycle (5 tasks)

| Task | Description | Tests |
|------|-------------|-------|
| 2.1 | `POST /api/v1/scenario-packs` — create pack from RUNNABLE template (reject CATALOG_ONLY) with run configuration | 3 |
| 2.2 | State machine: DRAFT → COMMITTED → ACTIVE → SETTLING → RESOLVED with transition validation | 3 |
| 2.3 | Commitment receipt generation (mirrors theatre pattern) | 1 |
| 2.4 | `POST /api/v1/scenario-packs/{id}/run` — async run launch | 2 |
| 2.5 | Frontend: launch configuration panel wired to create + run API | 1 |

**Sprint 2 total:** 10 tests

### Sprint 3: Checkpoint Resolution + Branching (5 tasks)

| Task | Description | Tests |
|------|-------------|-------|
| 3.0 | ScenarioSeedManager — run seed allocation and mode-specific RNG policy | 1 |
| 3.1 | CheckpointEvaluator service — schema-driven checkpoint automation, evaluator primitives, branch selection | 4 |
| 3.2 | RunCheckpointResult recording + branch probability tracking | 2 |
| 3.3 | Episode tree reconstruction — `GET /api/v1/scenario-packs/{id}/runs/{run_id}/tree` | 1 |
| 3.4 | Replay output for completed runs | 1 |

**Sprint 3 total:** 9 tests

### Sprint 4: Derived Theatre Spawning (4 tasks)

| Task | Description | Tests |
|------|-------------|-------|
| 4.1 | TheatreSpawner service — checkpoint → Theatre creation with provenance link | 3 |
| 4.2 | Spawned theatre lifecycle (commit → run → settle → certificate via existing pipeline) | 1 |
| 4.3 | `GET /api/v1/scenario-packs/{id}/derived-theatres` — list spawned theatres | 1 |
| 4.4 | Parent pack tracks spawned theatre count, audit events for spawn | 1 |

**Sprint 4 total:** 6 tests

### Sprint 5: RLMF Telemetry + Frontend Integration + Polish (5 tasks)

| Task | Description | Tests |
|------|-------------|-------|
| 5.1 | Scenario run telemetry → RLMF export pipeline integration | 1 |
| 5.2 | WebSocket events: SCENARIO_RUN_STATUS, CHECKPOINT_RESOLVED, THEATRE_SPAWNED | 1 |
| 5.3 | Frontend: branch map visualization from checkpoint/branch API data | 1 |
| 5.4 | Frontend: run status, checkpoint results, derived theatre links | 1 |
| 5.5 | E2E test: create pack → run → checkpoints resolve → theatre spawned → RLMF export available | 1 |

**Sprint 5 total:** 5 tests

**Grand total:** 4 + 6 + 10 + 9 + 6 + 5 = 40 new tests. Post-018 expected: ≥1140 passed.

## 6. Non-Functional Requirements

### NFR-1: Separation of Concerns

Scenario packs and theatres are distinct product concepts with separate models, routes, and schemas. Scenario packs can spawn theatres; theatres do not contain scenario packs. The `spawned_from_checkpoint_id` provenance link is the only cross-reference.

### NFR-2: Template Data Integrity

The 18 seeded templates from the library document are immutable after seeding. User-created templates are mutable in DRAFT state only. Template JSON validation enforces the existing fixture shape (objectiveVector, forkPointSchema, saboteurDeck, telemetrySpec, settlementRules).

### NFR-3: Backwards Compatibility

All new entities are additive. Existing theatre, certificate, and investigation flows are unaffected. New tables, not columns on existing tables (except `spawned_from_checkpoint_id` on Theatre).

### NFR-4: Checkpoint Ordering

Checkpoints within a template have a `sequence_num` that defines evaluation order. The checkpoint evaluator processes them strictly in sequence — no parallel evaluation in this cycle.

### NFR-5: Design Language

All new UI follows the existing kree8.studio terminal aesthetic. Branch map visualization uses the checkpoint/branch colour vocabulary from the design reference (Start = purple, Checkpoint = orange, Success = green, Failure = red, Partial = dark orange).

## 7. Out of Scope

- Parallel checkpoint evaluation (sequential only in this cycle)
- Real-time simulation rendering (checkpoint results are computed, not animated)
- Custom saboteur deck editing (use template defaults)
- Agent training loop integration (telemetry is export-ready, not consumed by agent runtime)
- Scenario pack versioning (immutable templates after seeding)
- Multi-user collaborative runs
- Scenario pack marketplace / sharing
- Alpamayo scenario pack suggestions (Alpamayo dual-direction architecture is a future cycle)
- Formalising prose-only scenario packs into runnable checkpoint graphs beyond catalog seeding
- Custom evaluator code per scenario pack beyond the v1 primitive set (BINARY_RISK_GATE, RESOURCE_DEPLETION, DETECTION_EVENT, TIMING_BREACH, MISSION_COMPLETION)

## 8. Dependencies

| Dependency | Status | Impact |
|------------|--------|--------|
| Cycle-017 (Policy Surface) | ✓ Complete | Certificate pipeline, routing, gates available for spawned theatres |
| Theatre lifecycle | ✓ Exists | Pattern for pack lifecycle; spawned theatres use existing pipeline |
| Fork manager | ✓ Exists | ForkType, ForkStatus primitives for branching logic |
| WebSocket manager | ✓ Exists | Extension point for run status events |
| RLMF export infrastructure | ✓ Exists | Downstream consumer of scenario telemetry |
| ScenarioPacksPage | ✓ Exists | Empty shell ready for API wiring |
| Design reference | ✓ Exists | Full UI spec for branch map, launch config |
| Template fixtures | ✓ Exists | Data shape for objectiveVector, forkPointSchema, etc. |

## 9. What This Unlocks

- **Branching RL environments** — agents train against decision trees, not single-outcome markets
- **Rich RLMF telemetry** — episode-level data with checkpoint decisions, branch probabilities, state vectors
- **Derived theatres** — individual checkpoints can spawn real markets, connecting simulation to prediction
- **Template catalog** — 18 curated scenario packs ready for agent training and engagement
- **Scenario-to-export pipeline** — RLMF Exports page can reference scenario runs as data sources
- **Foundation for Alpamayo** — dual-direction suggestions (theatre + scenario pack) become possible once the pack engine exists
