# Alexander Build — Surface B: Scenario Packs

**Date:** 7 March 2026
**Scope:** Frontend only. Wire scenario packs UI to design reference parity with Cycles 018 + 020 backend.
**Design references:** `echelon_scenario_packs_catalog_v2.html`, `echelon_scenario_pack_detail_v2.html`, `echelon_scenario_run_detail_v1.html`, `echelon_empty_states_v1.html`

---

## What Already Exists (Frontend)

| Layer | File | Status |
|-------|------|--------|
| Types | `src/types/scenarioPack.ts` | Complete — PackState, RunStatus, all response types, fork replay, derived theatres, branch probabilities |
| API client | `src/api/scenarioPacks.ts` | Complete — 10 endpoints (templates list/detail, pack create/commit/run, tree, replay, derived theatres, branch probabilities) |
| Hooks | `src/hooks/useScenarioPacks.ts` | Complete — 7 queries + 3 mutations, React Query with polling/stale config |
| BranchMap | `src/components/scenario/BranchMap.tsx` | Functional — vertical tree with color-coded nodes (purple start, orange checkpoint, green/red outcome) |
| ScenarioRunDetail | `src/components/scenario/ScenarioRunDetail.tsx` | Functional — run status, episode tree, fork replay, pack-scoped derived theatres, WebSocket integration |
| Catalog page | `src/pages/ScenarioPacksPage.tsx` | Functional — template grid with family/status filters, search, summary stats |
| Detail page | `src/pages/ScenarioPackDetailPage.tsx` | Functional — template metadata, RUNNABLE lifecycle (create→commit→run), branch probabilities, embedded run detail |
| Routes | `src/router.tsx` | `/scenario-packs`, `/scenario-packs/:templateId` |
| WebSocket | `ScenarioRunDetail.tsx` | Subscribed to `scenario_pack:{packId}` for SCENARIO_RUN_STATUS + CHECKPOINT_RESOLVED events |

**Assessment:** The wiring layer is substantially complete. The work is now visual/layout alignment plus honest treatment of the still-deferred runtime surfaces.

---

## Backend API Contract (Source of Truth)

### Scenario Pack Templates
- `GET /api/v1/scenario-pack-templates` — list with family, status filters; returns checkpoint_count, fork_points_min/max, is_seeded
- `GET /api/v1/scenario-pack-templates/{id}` — full detail with checkpoints (evaluator_type, branch_count, can_spawn_theatre), objective_vector, fork_points, saboteur_deck
- `GET /api/v1/scenario-pack-templates/{id}/branch-probabilities` — probability distributions per checkpoint per branch

### Scenario Packs
- `POST /api/v1/scenario-packs` — create from RUNNABLE template (template_id, run_mode, agent_assignment, simulation_scale, objective_profile, config_json). Rejects CATALOG_ONLY with 409.
- `GET /api/v1/scenario-packs/{id}` — pack state (DRAFT/COMMITTED/RUNNING/COMPLETED/FAILED)
- `POST /api/v1/scenario-packs/{id}/commit` — DRAFT → COMMITTED, generates commitment hash
- `POST /api/v1/scenario-packs/{id}/run` — launches a run from COMMITTED pack state and returns the run with environment_seed

### Runs
- `GET /api/v1/scenario-packs/{id}/runs/{run_id}/tree` — episode tree: checkpoint nodes with selected_branch, outcome_type, reward, spawned_theatre_id
- `GET /api/v1/scenario-packs/{id}/runs/{run_id}/replay` — ForkReplay-compatible output: options with price paths, disclosure events, settlement
- `GET /api/v1/scenario-packs/{id}/derived-theatres` — theatres spawned from checkpoint resolutions

### WebSocket Events
- `SCENARIO_RUN_STATUS` — pack_id, run_id, status (global + scenario_pack channel)
- `CHECKPOINT_RESOLVED` — pack_id, run_id, checkpoint_id, selected_branch_id, reward, seed (global + scenario_pack channel)
- `THEATRE_SPAWNED` — pack_id, run_id, theatre_id, checkpoint_id (global + scenario_pack channel)

### Pack Create Request Shape
```
{
  template_id, run_mode (TRAINING|EVALUATION|CALIBRATION|REPLAY),
  agent_assignment (auto_assign|...), simulation_scale (single_1x|...),
  objective_profile (pack_default|...), config_json?
}
```

### Run Response Shape
```
{
  id, pack_id, agent_id, status (PENDING|RUNNING|COMPLETED|FAILED),
  environment_seed, run_mode, current_checkpoint_seq,
  started_at, completed_at, episode_duration_sec, total_reward
}
```

---

## Gap Analysis: Design Reference vs Current Implementation

### Catalog Page (echelon_scenario_packs_catalog_v2.html)

| Design Reference Spec | Current Implementation | Gap |
|----------------------|----------------------|-----|
| Stats bar: total, runnable count, catalog-only count, max branch depth, telemetry events, derived theatres | Total, runnable, catalog-only counts shown | Add max branch depth if directly derivable. Telemetry events / derived theatres should only be shown if backed by real data; otherwise use an honest sparse/deferred treatment rather than invented counts |
| Card: domain/type/complexity badges | Family badge shown | Map family to domain/type/complexity if backend surfaces them, or derive from template metadata |
| Card: branch preview bar (mini SVG start→checkpoints→fork→end) | Not present | Add mini branch preview visualization per card |
| Card: output chips (telemetry, replay, labels, theatre) | Not present | Add only the output chips that can be honestly inferred from real template data (for example, theatre output when checkpoints can spawn theatres). Do not invent unsupported chip categories |
| Card: metrics strip (checkpoints, branch depth, outcomes, telemetry) | checkpoint_count, fork range, is_seeded shown | Expand metrics to match 4-column strip |
| Card: action buttons (Open Pack / Launch / Branch Map) | Link to detail page only | Add Launch shortcut for RUNNABLE templates, Branch Map action |
| Filter tabs: All / Runnable / Catalog Only with counts | Status filter present | Verify tab UI matches reference |

### Detail Page (echelon_scenario_pack_detail_v2.html)

| Design Reference Spec | Current Implementation | Gap |
|----------------------|----------------------|-----|
| Two-column layout: content left, sticky launch panel right | Single-column with lifecycle controls inline | Restructure to two-column with sticky launch panel |
| Branch Map hero section (SVG with start/checkpoint/end nodes, color-coded edges) | BranchMap component exists (vertical tree) | Verify visual alignment; may need horizontal SVG flow per reference |
| Use Tags section (Training/Evaluation/Calibration/Replay toggles) | Run mode selector exists | Verify toggle UI matches reference tags |
| Expected Outputs grid (6 telemetry output cards) | Not present as standalone section | Add expected outputs grid only where the outputs can be inferred honestly from template data; otherwise use a sparse/deferred state |
| Derived Theatres section (theatre candidates with View Theatre links) | Present in run detail, not in pack detail outside run context | Surface derived theatres at pack level via `getDerivedTheatres(packId)`, but label them clearly as pack-scoped outputs rather than run-scoped outputs |
| Launch panel: 4 dropdowns (run_mode, agent_assignment, simulation_scale, objective_profile) | Create/commit/run buttons exist; run_mode selector present | Verify all 4 configuration dropdowns exist and match reference |
| Pack Metadata sidebar (domain, type, complexity, checkpoints, branch depth, est duration, agent type, objective) | Template metadata displayed | Expand metadata grid to match 8-field reference layout |
| CATALOG_ONLY: disabled launch, disclaimer text | Catalog-only notice shown | Verify disabled state matches reference exactly (0.4 opacity, disclaimer text) |

### Run Detail (echelon_scenario_run_detail_v1.html)

| Design Reference Spec | Current Implementation | Gap |
|----------------------|----------------------|-----|
| Run Status header: badge, mode, checkpoints progress, reward, duration | Present | Verify badge styling per status/mode |
| Episode Tree: vertical checkpoint nodes with outcome reward values | BranchMap renders tree | Verify reward values displayed per node |
| Fork Replay: question, option pills, settlement, disclosure events | Present | Verify pill selection UI, settlement display |
| Derived Theatres: rows with construct_id, status badge, provenance, View Theatre link | Present with links to `/theatre/{id}` | Verify status badge colors and provenance display, and keep the section labeled as pack-scoped because the live endpoint is pack-scoped |
| REPLAY mode: cyan badge, "exact recorded-path replay" label | REPLAY badge distinguished | Verify wording and styling match reference |
| RUNNING state: empty states for tree ("Awaiting checkpoint resolutions..."), replay ("Replay available after run completes"), theatres | Empty states exist | Verify empty state text and styling match reference |
| Branch probabilities | Explicitly deferred in locked reference | Do not invent a run-detail branch-probability section in this pass |

---

## Implementation Tasks

### B1. Catalog Page — Match Design Reference Layout

**Target:** Align `ScenarioPacksPage.tsx` to `echelon_scenario_packs_catalog_v2.html`.

- Expand stats bar with additional metrics where backend supports them
- Keep unsupported metrics honest:
  - branch depth can be derived from `fork_points_max`
  - telemetry event counts must not be fabricated
  - derived-theatre counts should only be shown if backed by real data
- Enhance template cards:
  - Add only output chips that can be honestly inferred from real template data
  - Add mini branch preview bar if feasible (simplified SVG showing checkpoint count as nodes)
  - Expand metrics strip to 4 columns: checkpoints, branch depth (fork_points_max), outcomes, telemetry
  - Add action buttons per card: Open Pack (detail link), Launch (direct to detail with launch panel open, RUNNABLE only), Branch Map
- Verify filter tab styling matches reference (All / Runnable / Catalog Only with counts)
- CATALOG_ONLY cards: disabled launch action, gray status indicator

**Data available from API:** template_status, checkpoint_count, fork_points_min/max, is_seeded, family, name, description. Branch depth derivable from fork_points_max. Output types and telemetry counts are not directly available — do not invent them.

### B2. Detail Page — Two-Column Layout with Launch Panel

**Target:** Restructure `ScenarioPackDetailPage.tsx` to match `echelon_scenario_pack_detail_v2.html`.

- Two-column layout: main content left, sticky launch panel + metadata sidebar right
- Launch panel with 4 config dropdowns:
  - Run Mode: TRAINING / EVALUATION / CALIBRATION / REPLAY (already exists as selector)
  - Agent Assignment: auto_assign / courier-class / analyst-class / manual (wire to pack create request)
  - Simulation Scale: single_1x / small_batch_10x / full_sweep_100x (wire to pack create request)
  - Objective Profile: pack_default / maximize_delivery_rate / minimize_detection / balanced_risk_reward (wire to pack create request)
- Launch Run button state: enabled for RUNNABLE (DRAFT → create+commit+run), disabled for CATALOG_ONLY with disclaimer
- Pack Metadata sidebar: expand to 8-field grid matching reference
- Add Expected Outputs grid section only where the outputs can be mapped honestly from template data; otherwise use honest sparse/deferred content
- Add Use Tags section (TRAINING / EVALUATION / CALIBRATION / REPLAY mode highlights)

**Important:** The existing lifecycle flow (create → commit → run as separate steps) is correct. The launch panel should compose these into a single "Launch Run" action for the user: create pack with config, commit, then run. Show progress/errors for each step.

### B3. Branch Map — Verify Visual Alignment

**Target:** Verify `BranchMap.tsx` matches the SVG visualization in `echelon_scenario_pack_detail_v2.html`.

- Reference shows: Start node (purple) → Checkpoint nodes (orange) → End nodes (green/red/partial orange)
- Edges color-coded: main path purple, success green, failure red
- Legend below showing all node/edge types
- Current implementation: vertical tree with color-coded nodes
- Compare and align node shapes, edge colors, legend, expand button
- If reference shows horizontal flow, adapt layout

### B4. Run Detail — State Polish and Empty States

**Target:** Verify `ScenarioRunDetail.tsx` matches all 4 states from `echelon_scenario_run_detail_v1.html`.

- **COMPLETED (fresh run):** Badge, mode, checkpoints X/X, reward, duration, full tree, full replay, derived theatres (empty or populated)
- **REPLAY mode:** Cyan badge, "exact recorded-path replay" label, "Replay Trace" section rename
- **EVALUATION with derived theatres:** 3 theatre rows with construct_id, status (SETTLED/RUNNING/PENDING), provenance (checkpoint, cert), View Theatre link, labeled as pack-scoped
- **RUNNING (sparse):** RUNNING badge, checkpoints 0/N, reward "---", tree empty ("Awaiting checkpoint resolutions..."), replay empty ("Replay available after run completes"), theatres empty
- Verify disclosure event rendering (time, type badge, description)
- Verify fork replay option pill interaction
- Do not add branch probabilities to run detail in this pass; the locked reference now documents them as deferred

### B5. Derived Theatres — Surface at Pack Level

**Target:** Show derived theatres outside of run context.

- Use `useDerivedTheatres(packId)` hook to show theatres spawned from any run of this pack
- Display in detail page below run detail or as separate section
- Each row: construct_id, state badge, spawned_from_checkpoint_id, certificate_id, View Theatre link
- Empty state: "No derived theatres spawned" with hint text per reference
- Label the section as pack-scoped to match the live endpoint contract

### B6. WebSocket — Wire THEATRE_SPAWNED Event

**Current:** ScenarioRunDetail subscribes to SCENARIO_RUN_STATUS and CHECKPOINT_RESOLVED.

**Gap:** THEATRE_SPAWNED event exists in backend but is not consumed by frontend.

**Target:** Add handler for THEATRE_SPAWNED event in ScenarioRunDetail.tsx:
- Invalidate derived-theatres cache on receipt
- Optionally show a transient notification when a theatre spawns during a run

---

## Backend Limitations to Surface Honestly

1. **No telemetry event count** on template summary — catalog stats for "telemetry events" must be derived or deferred
2. **No output type categorization** on templates — output chips must be inferred conservatively or deferred; do not treat template_status alone as proof of every output type
3. **No domain/type/complexity mapping** beyond `family` — catalog card badges may be limited to family unless template metadata expands
4. **No run list endpoint** — only tree/replay/derived-theatres per run. Pack detail shows the latest run inline via ScenarioRunDetail.
5. **Simulation scale and objective profile** — backend accepts these as pack create parameters, but runtime behavior may be staged. Surface them honestly as configuration, not guarantees.
6. **Branch probabilities remain template-level only in the current locked references** — do not surface them as a run-detail feature in this pass

---

## Acceptance Criteria

1. Catalog page matches `echelon_scenario_packs_catalog_v2.html` layout with real template data
2. Detail page uses two-column layout with sticky launch panel and 4 config dropdowns
3. Launch flow composes create + commit + run into a single user action for RUNNABLE templates
4. CATALOG_ONLY templates show disabled launch with clear disclaimer
5. Branch Map visualization aligns with reference SVG style
6. Run detail handles the locked reference states: completed, replay, evaluation-with-theatres, running/sparse
7. Derived theatres surface at pack level via dedicated section and are labeled pack-scoped
8. THEATRE_SPAWNED WebSocket event consumed and derived theatres cache invalidated
9. Empty states follow `echelon_empty_states_v1.html` patterns
10. `npm run build` passes

---

## Intentionally Deferred

- Telemetry event counts per template (no backend field)
- Domain/type/complexity badges beyond family (no backend mapping)
- Run history list (no list-runs endpoint — single latest run shown inline)
- Branch probabilities in run detail (explicitly deferred in locked reference; template-level only for now)
- Simulation scale runtime behavior beyond configuration surface
- Saboteur deck visual UI (data available but no reference design for it)
- Custom evaluator code injection (explicitly out of scope per Cycle 020)

---

## Summary Format Per Pass

After each implementation pass, report:
1. What changed (files, components, hooks)
2. What remains intentionally deferred
3. Any backend limitations discovered
4. Any design reference corrections needed
5. Exact `npm run build` result
