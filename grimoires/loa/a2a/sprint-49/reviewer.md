# Sprint 1 Implementation Report — Template Catalog + Seeding

**Sprint:** sprint-1 (global: sprint-49)
**Date:** 2026-03-07

## Tasks Completed

### Task 1.1: Template Seeder Service
- **New file:** `backend/services/scenario_template_seeder.py`
- Seeds all 18 templates from Echelon Scenario Packs Library v1
- 4 templates with JSON fixtures (Neon Courier, Disaster Response, Orbital Salvage, Blacksite Heist) → `RUNNABLE` with structured checkpoints from `forkPointSchema`
- 14 templates without fixtures → `CATALOG_ONLY` with prose-based checkpoint stubs
- Idempotent: re-seeding skips existing templates
- Reads fixture files from `data/theatres/` directory

### Task 1.2: Template List API
- **New file:** `backend/api/scenario_pack_routes.py`
- `GET /api/v1/scenario-pack-templates` — paginated list with family/status filters
- Case-insensitive family filter
- Returns `TemplateListResponse` with checkpoint counts

### Task 1.3: Template Detail API
- `GET /api/v1/scenario-pack-templates/{template_id}` — full detail
- Includes checkpoints with branch counts, objective vector, saboteur deck
- Returns `ScenarioPackTemplateResponse` with computed `checkpoint_count`

### Task 1.4: Frontend — ScenarioPacksPage Wired to API
- **Modified:** `frontend/src/pages/ScenarioPacksPage.tsx`
- **New file:** `frontend/src/api/scenarioPacks.ts`
- Replaced empty shell with real API-driven template grid
- Family filter tabs, loading/error states
- RUNNABLE vs CATALOG_ONLY badge on each card
- Shows checkpoint count and fork range

### Router Registration
- **Modified:** `backend/main.py` — registered `scenario_templates_router`

## Files Changed
| File | Action |
|------|--------|
| `backend/services/scenario_template_seeder.py` | Created |
| `backend/api/scenario_pack_routes.py` | Created |
| `backend/main.py` | Modified (router registration) |
| `frontend/src/api/scenarioPacks.ts` | Created |
| `frontend/src/pages/ScenarioPacksPage.tsx` | Modified |
| `backend/tests/test_c018_sprint1_catalog.py` | Created |

## Tests
6/6 passing:
1. `test_seed_creates_18_templates` — 18 templates, correct families
2. `test_reseed_is_idempotent` — 0 new on re-seed
3. `test_list_all_templates` — all queryable with names/families
4. `test_filter_by_family` — NAV_UNC → 4 templates
5. `test_neon_courier_detail` — full fixture data + 8 checkpoints
6. `test_runnable_templates_have_checkpoints` — 4 RUNNABLE with checkpoints, 14 CATALOG_ONLY
