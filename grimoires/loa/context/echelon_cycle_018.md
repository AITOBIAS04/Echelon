# Cycle-018: Scenario Packs Engine

**Date:** 6 March 2026
**Depends on:** Cycle-017 (Policy Surface), Cycle-016 (Results Surface), Cycle-014c (Investigation Toolset), Cycle-013 (Agent Runtime), Cycle-010a (LMSR)
**Sprints:** 6 (0–5)
**Scope:** Build the Scenario Packs Engine: backend schema (7 new tables), template catalog seeded from the Echelon Scenario Packs Library v1, runnable-vs-catalog template distinction, schema-driven checkpoint automation, seeded environment RNG for run modes, derived theatre spawning, and RLMF telemetry output. Wire the frontend to real data.

---

## Why This Cycle Exists

Cycle 017 delivered the Policy Surface — routing evaluation, TAO flow, registry schema, coherence gates, and WebSocket policy events. The frontend has a `ScenarioPacksPage` shell at `/scenario-packs` with empty-state messaging and concept cards, plus a full design reference (`echelon_scenario_packs_v1.html`) specifying branch map visualization, launch configuration, and checkpoint structure. Four theatre template JSON fixtures already carry the data shape for scenario packs (`objectiveVector`, `forkPointSchema`, `saboteurDeck`, `telemetrySpec`, `settlementRules`). But the backend has **nothing** for scenario packs:

- **No database models.** No `ScenarioPack`, `ScenarioCheckpoint`, or `CheckpointBranch` tables exist.
- **No API endpoints.** No template catalog, pack CRUD, run launch, or checkpoint resolution endpoints.
- **No pack runner or checkpoint resolution logic.** The fork manager (`backend/fork_manager.py`) has `ForkType`/`ForkStatus`/`ForkPoint` primitives but no checkpoint evaluation engine.
- **No derived theatre spawning.** Checkpoints cannot produce real Theatre records yet.
- **No scenario-to-RLMF telemetry pipeline.** Episode-level data (decisions, state vectors, rewards) has no export path.

The Echelon Scenario Packs Library v1 defines 18 scenario packs across 8+ template families with a branching checkpoint model. This cycle builds the complete engine.

---

## What Already Exists (Cycle 018 Scaffolding)

### Frontend Shell

| Component | Location | Status |
|-----------|----------|--------|
| ScenarioPacksPage | `frontend/src/pages/ScenarioPacksPage.tsx` | Empty shell with concept cards, no API calls |
| Design reference | `output/design_reference/echelon_scenario_packs_v1.html` | Full UI spec: branch map, launch config, checkpoint structure |
| Mock launchpad API | `frontend/src/api/launchpad.ts` | Mock `LaunchCard`/`LaunchpadFeed` — to be replaced |
| Mock replay API | `frontend/src/api/replay.ts` | Mock `ForkReplay`/`DisclosureEvent` — shape to align with checkpoint results |
| RLMF export infrastructure | `frontend/src/api/exports.ts`, `frontend/src/pages/RLMFPage.tsx` | Downstream consumer of scenario telemetry |

### Existing JSON Fixture Data Shape

Four theatre template fixtures define the data shape scenario packs inherit:

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

Fixtures with structured data: `NEON_COURIER_V1.json`, `DISASTER_RESPONSE_V1.json`, `ORBITAL_SALVAGE_V1.json`, `BLACKSITE_HEIST_V1.json` (in `frontend/dist/theatres/`).

### Backend Infrastructure Ready to Extend

| Component | Location | Extension Point |
|-----------|----------|-----------------|
| Theatre model + lifecycle | `backend/database/models.py`, `backend/api/theatre_routes.py` | Pattern template for pack lifecycle |
| TheatreTemplate model | `backend/database/models.py` | Pattern for ScenarioPackTemplate |
| Fork manager | `backend/fork_manager.py` | ForkType, ForkStatus, ForkPoint primitives |
| Certificate pipeline | `backend/services/certificate_pipeline.py` | Spawned theatres use existing pipeline (incl. 017 routing) |
| WebSocket manager | `backend/websockets/realtime_manager.py` | Extension point for scenario run events |
| Game loop | `backend/worker/game_loop.py` | Extension point for checkpoint evaluation cadence |
| TheatreAuditEvent | `backend/database/models.py` | Pattern for ScenarioPackAuditEvent |

---

## Product Concepts

### Theatre Templates vs Scenario Packs

**Theatre Templates** = market/certificate templates — inquiry class, resolution logic, evidence rules. A theatre resolves to one outcome via one contract.

**Scenario Packs** = embodied RL engagement templates — objective vectors, checkpoint branching, saboteur decks, settlement rules, telemetry. A scenario pack produces a tree of outcomes across multiple decision points.

### Core Principle

> Scenario packs can spawn theatres; theatres do not contain scenario packs.

The `spawned_from_checkpoint_id` provenance link on the Theatre model is the only cross-reference.

### Checkpoint Automation Principle

Scenario pack checkpoints are declarative, not bespoke code paths. Every runnable scenario pack defines an explicit checkpoint graph. Each checkpoint declares:

- `trigger_condition`
- `decision_window_sec`
- `evaluator_type`
- `branch_rules`
- `reward_mapping`
- optional `theatre_spawn_rule`

The engine auto-evaluates checkpoints when their trigger conditions are met. Pack authors define checkpoint configuration; the runtime supplies reusable evaluator primitives. This avoids one-off Python logic per scenario.

### Template Families

| Family | Code | Templates | Count |
|--------|------|-----------|-------|
| Navigation under Uncertainty | NAV_UNC | Neon Courier, Midnight Exchange, Runway Intercept, Last Mile Hospital | 4 |
| Social Navigation | SOC_NAV | Velvet Rope | 1 |
| Manual Force Control | MAN_FORCE | Skybridge Assembly, High-Rise Steel | 2 |
| Multi-Agent C3 | MARL_C3 | Disaster Response, Cooling Plant, Reactor Protocol, Heist Echelon, Blacksite Heist | 5 |
| 3D Inertial Control | 3D_INERT | Orbital Salvage, Orbital Docking Court | 2 |
| Long-Horizon Planning | LONG_HZN | Icebreaker Convoy | 1 |
| Puzzle Logic | PUZ_LOGIC | Escape Room | 1 |
| Adversarial Air | ADV_AIR | Dogfight Echelon | 1 |
| Precision Manipulation | PREC_MAN | Cleanroom Microsurgery | 1 |

**Total:** 18 scenario pack templates.

---

## Sprint Plan

### Sprint 0: Schema Foundation + Migration

Define 7 new models: `ScenarioPackTemplate`, `ScenarioCheckpoint`, `CheckpointBranch`, `ScenarioPack`, `ScenarioRun`, `RunCheckpointResult`, `ScenarioPackAuditEvent`. Extend Theatre with `spawned_from_checkpoint_id`. Alembic migration (dialect-safe). Pydantic schemas. No runtime logic.

**Key decisions:**
- ScenarioPackTemplate PK is `String(100)` (named ID like `neon_courier`)
- `ScenarioPackTemplate.template_status`: `RUNNABLE` | `CATALOG_ONLY`
- JSON blobs for `objective_vector`, `fork_points`, `saboteurs`, `telemetry`, `settlement` — matching existing fixture shape
- `ScenarioRun.environment_seed`: explicit per-run seed for environment randomness
- `ScenarioCheckpoint.sequence_num` defines evaluation order (strict sequential, no parallel)
- `ScenarioCheckpoint.evaluator_type`: reusable primitive, not arbitrary code
- `ScenarioCheckpoint.trigger_condition_json`: declarative trigger config
- `ScenarioCheckpoint.reward_mapping_json`: reward config by branch outcome
- `ScenarioCheckpoint.theatre_spawn_rule_json`: optional spawn config for derived theatres
- `CheckpointBranch.outcome_type`: success | failure | partial | continue
- `CheckpointBranch.next_checkpoint_id` self-FK enables branching paths

### Sprint 1: Template Catalog + Seeding

Seed 18 templates from the Echelon Scenario Packs Library v1. Build template catalog API. Only templates with formalised checkpoint graphs are launchable.

- Template seeder: 4 templates from JSON fixtures become `RUNNABLE` templates because they already carry structured `forkPointSchema` data. The remaining 14 library entries are seeded as `CATALOG_ONLY` templates unless and until their checkpoint graphs are formalised.
- `GET /api/v1/scenario-pack-templates` — paginated list with family filter and `template_status` (`RUNNABLE` | `CATALOG_ONLY`)
- `GET /api/v1/scenario-pack-templates/{id}` — detail with checkpoints, objective vector, saboteur deck, and template status
- Frontend: ScenarioPacksPage wired to real template data and clearly distinguishes runnable packs from catalog-only packs
- `POST /api/v1/scenario-packs` rejects `CATALOG_ONLY` templates with 409/422 and a clear error explaining that the pack is browseable but not yet runnable

### Sprint 2: Pack Lifecycle

Pack creation from template, state machine (DRAFT → COMMITTED → ACTIVE → SETTLING → RESOLVED), commitment receipt, run configuration.

- `POST /api/v1/scenario-packs` — create from template with run config (run_mode, agent_assignment, simulation_scale, objective_profile)
- `POST /api/v1/scenario-packs/{id}/commit` — DRAFT → COMMITTED, generates hash
- `POST /api/v1/scenario-packs/{id}/run` — COMMITTED → ACTIVE, creates ScenarioRun
- Auth via `Depends(get_current_user)`, `user.user_id` on pack records
- Run creation persists `environment_seed` and `run_mode`
- Run modes define RNG semantics:
  - `TRAINING` = stochastic, varying seeds
  - `EVALUATION` = controlled stochasticity from a fixed seed set
  - `CALIBRATION` = canonical seed set for comparability
  - `REPLAY` = exact recorded path, no fresh randomness
- `agent_assignment` supplies policy/strategy only; it does not define randomness

### Sprint 3: Checkpoint Resolution + Branching

CheckpointEvaluator service processes checkpoints in sequence using declarative checkpoint schemas. The evaluator executes reusable primitive types (for example: binary risk gate, resource depletion, detection event, timing breach, mission completion) against checkpoint config and current run state. Branch selection is deterministic given `(agent action, checkpoint state, environment seed, evaluator config)`.

- Checkpoints evaluated in `sequence_num` order — no parallel evaluation
- Built-in evaluator primitives for v1:
  - `BINARY_RISK_GATE`
  - `RESOURCE_DEPLETION`
  - `DETECTION_EVENT`
  - `TIMING_BREACH`
  - `MISSION_COMPLETION`
- Checkpoint triggers fire automatically from run state; no manual checkpoint resolution required for standard runs
- Agent output influences branch selection through action/policy choice, but exogenous uncertainty is resolved via seeded environment RNG
- Introduce explicit environment RNG/seed handling:
  - `TRAINING` = stochastic, varying seeds
  - `EVALUATION` = controlled stochasticity from a fixed seed set
  - `CALIBRATION` = canonical seed set for comparability
  - `REPLAY` = exact recorded path, no fresh randomness
- Reward: computed from objective vector component weights
- `GET /api/v1/scenario-packs/{id}/runs/{run_id}/tree` — episode tree
- `GET /api/v1/scenario-packs/{id}/runs/{run_id}/replay` — ForkReplay-compatible output
- `GET /api/v1/scenario-pack-templates/{id}/branch-probabilities` — computed only from completed runnable runs

### Sprint 4: Derived Theatre Spawning

TheatreSpawner service creates real Theatre records from checkpoints with `can_spawn_theatre=True`.

- Spawned theatres get `spawned_from_checkpoint_id` provenance link
- `construct_id` = `scenario_{pack_id}_run_{run_id}_cp_{checkpoint_id}` to preserve per-run uniqueness and provenance
- Spawned theatres follow normal lifecycle (DRAFT → COMMITTED → ACTIVE → RESOLVED) via existing pipeline
- Certificate pipeline applies 017 routing + gates to spawned theatres
- `GET /api/v1/scenario-packs/{id}/derived-theatres` — list spawned theatres

### Sprint 5: RLMF Telemetry + Frontend Integration + Polish

Wire scenario run telemetry to RLMF export pipeline. Frontend branch map + run status + WS events. E2E test.

- ScenarioTelemetryExporter converts runs to RLMF training records
- 3 new WS events: SCENARIO_RUN_STATUS, CHECKPOINT_RESOLVED, THEATRE_SPAWNED
- Branch map colour vocabulary: Start=purple, Checkpoint=orange, Success=green, Failure=red, Partial=dark orange
- E2E: create pack → run → checkpoints → theatre spawned → RLMF export available

---

## New Backend Services

| Service | File | Purpose |
|---------|------|---------|
| ScenarioTemplateSeeder | `backend/services/scenario_template_seeder.py` | Seed 18 templates from library doc + fixtures |
| ScenarioPackLifecycle | `backend/services/scenario_pack_lifecycle.py` | State machine + commitment receipt |
| CheckpointEvaluator | `backend/services/checkpoint_evaluator.py` | Sequential checkpoint automation, trigger evaluation, branch selection, reward computation, evaluator primitive execution |
| ScenarioSeedManager | `backend/services/scenario_seed_manager.py` | Run seed allocation and mode-specific RNG policy |
| TheatreSpawner | `backend/services/theatre_spawner.py` | Checkpoint → Theatre creation with provenance |
| ScenarioTelemetryExporter | `backend/services/scenario_telemetry_exporter.py` | Run telemetry → RLMF export records |

---

## API Changes

### New Route Files

- `backend/api/scenario_pack_routes.py` — all scenario pack endpoints

### Template Endpoints

- `GET /api/v1/scenario-pack-templates` — paginated list, family filter, `template_status`
- `GET /api/v1/scenario-pack-templates/{id}` — full detail including checkpoint graph and runnable status
- `GET /api/v1/scenario-pack-templates/{id}/branch-probabilities` — computed from runs

### Pack Endpoints

- `POST /api/v1/scenario-packs` — create from `RUNNABLE` template only
- `GET /api/v1/scenario-packs/{id}` — pack detail (auth: owner only)
- `POST /api/v1/scenario-packs/{id}/commit` — DRAFT → COMMITTED
- `POST /api/v1/scenario-packs/{id}/run` — launch run (202)
- `GET /api/v1/scenario-packs/{id}/runs/{run_id}/tree` — episode tree
- `GET /api/v1/scenario-packs/{id}/runs/{run_id}/replay` — ForkReplay output
- `GET /api/v1/scenario-packs/{id}/derived-theatres` — spawned theatres

### Extended Models

- Theatre: +`spawned_from_checkpoint_id` (nullable FK → scenario_checkpoints.id)

### Scenario Pack Runtime Contract

For a scenario pack to be runnable, each checkpoint must define:

- trigger condition
- decision window
- evaluator type
- branch rules
- reward mapping
- optional theatre-spawn rule

Library entries lacking this full checkpoint graph remain `CATALOG_ONLY`.

---

## WebSocket Event Additions

| Event Type | Trigger | Payload |
|------------|---------|---------|
| SCENARIO_RUN_STATUS | Run status change | pack_id, run_id, status |
| CHECKPOINT_RESOLVED | Checkpoint evaluated | pack_id, checkpoint_id, branch_id, reward |
| THEATRE_SPAWNED | Derived theatre created | pack_id, theatre_id, checkpoint_id |

---

## Test Targets

39 new tests across 6 sprints. Post-018 expected: ≥1139 passed.

| Sprint | Tests | Focus |
|--------|-------|-------|
| 0 | 4 | Models, migration, schemas, regression |
| 1 | 6 | Seeder, list API, detail API, frontend |
| 2 | 10 | Create (incl. CATALOG_ONLY rejection), state machine, commitment, run, frontend |
| 3 | 8 | Evaluator, branch probabilities, episode tree, replay |
| 4 | 6 | Spawner, lifecycle, derived theatre API, audit |
| 5 | 5 | RLMF, WS events, branch map, run status, E2E |

---

## Out of Scope

- Parallel checkpoint evaluation (sequential only in this cycle)
- Real-time simulation rendering (checkpoint results are computed, not animated)
- Custom saboteur deck editing (use template defaults)
- Agent training loop integration (telemetry is export-ready, not consumed by agent runtime)
- Scenario pack versioning (immutable templates after seeding)
- Multi-user collaborative runs
- Scenario pack marketplace / sharing
- Alpamayo scenario pack suggestions (future cycle)
- Auto-conversion of prose-only library entries into runnable checkpoint graphs
- Formalising prose-only scenario packs into runnable checkpoint graphs beyond catalog seeding
- Custom evaluator code per scenario pack beyond the v1 primitive set

---

## Relationship to Handoff Matrix

The handoff matrix (`output/HANDOFF_MATRIX_ALEXANDER.md`) lists Scenario Packs at `/scenario-packs` with ZERO_STATE empty state and "Browse Starter Packs" CTA. Cycle 018 replaces this shell with the full scenario pack engine. Other handoff matrix items remain unchanged:

1. Alpamayo path → keep staged shell (unchanged by 018)
2. Agent deployment → keep staged modal (unchanged by 018)
3. Certificates → enhanced by 017 routing + gates; spawned theatre certificates use same pipeline
4. Route normalization → keep current (unchanged by 018)
5. Create Theatre editorial → keep staged (unchanged by 018)

---

## Relationship to Cycle 017

Cycle 018 builds on 017's Policy Surface in two concrete ways:

1. **Spawned theatres inherit 017 policy:** Theatres created by the TheatreSpawner go through the same `CertificatePipeline` that now includes routing evaluation, coherence gates, and TAO flow. No additional 017 integration work needed.
2. **WebSocket extension:** The 3 new WS event types follow the same broadcast patterns established by 017's ROUTING_DECISION, COHERENCE_GATE_TRANSITION, and TAO_FLOW_ALERT events.

018 does **not** modify any 017 services, models, or feature flags.
