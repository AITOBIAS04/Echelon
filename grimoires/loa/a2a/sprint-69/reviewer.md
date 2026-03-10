# Sprint-69 (Cycle-022 Sprint-0) — Reviewer Handoff

## Summary

Investigation Template Infrastructure: new `InvestigationTemplate` model, `Investigation` model extension with `template_id` FK and `committed_sources_json`, Alembic migration, and Pydantic response schemas.

## Files Changed

### New Files
- `backend/schemas/investigation_template_schemas.py` — 3 Pydantic response schemas (ListItem, ListResponse, Detail)
- `backend/alembic/versions/c022_investigation_templates.py` — Migration: creates `investigation_templates` table, adds 2 columns to `investigations`
- `backend/tests/test_c022_sprint0_schema.py` — 4 tests covering model, extension, migration, schemas

### Modified Files
- `backend/database/models.py` — Added `InvestigationTemplate` model (13 columns), added `template_id` + `committed_sources_json` + `template` relationship to `Investigation`

## Tasks Completed

| Task | Status | Notes |
|------|--------|-------|
| 0.1 InvestigationTemplate Model | Done | All 13 fields, relationship to Investigation |
| 0.2 Investigation Model Extension | Done | template_id FK (nullable, indexed), committed_sources_json (nullable JSON) |
| 0.3 Alembic Migration | Done | Idempotent upgrade, clean downgrade |
| 0.4 Response Schema Contract | Done | 3 schemas matching SDD spec |

## Test Results

4/4 tests passing. No regressions in existing test suites (c019, c021 verified).

## Review Notes

- Migration follows existing idempotent pattern (inspector-based column checks)
- `InvestigationTemplate` placed before `Investigation` in models.py to satisfy FK dependency order
- `template_id` is nullable to preserve backward compatibility with existing investigations
- `committed_sources_json` is nullable (only populated when investigation commits to template sources)
- Schema field names use snake_case without `_json` suffix (matching existing convention in investigation_schemas.py)

## Engineer Feedback Remediation (2026-03-08)

All 4 issues from `engineer-feedback.md` addressed:

### Issue 1 (BLOCKING) — Schema field naming: `id` -> `template_id`
- **Fixed** in `backend/schemas/investigation_template_schemas.py`: renamed `id` to `template_id` in both `InvestigationTemplateListItem` and `InvestigationTemplateDetail`

### Issue 2 (BLOCKING) — ListItem schema structure aligned to SDD
- **Fixed** in `backend/schemas/investigation_template_schemas.py`:
  - Added `description: Optional[str] = None`
  - Replaced `domain_filters: list[str]` with `domain_filter_count: int = 0`
  - Removed `default_stop_condition`, `is_seeded`, `created_at` (Detail-only fields)

### Issue 3 (SHOULD-FIX) — Model `name` column length: `String(200)` -> `String(255)`
- **Fixed** in `backend/database/models.py` (InvestigationTemplate.name)
- **Fixed** in `backend/alembic/versions/c022_investigation_templates.py` (name column)

### Issue 4 (ADVISORY) — ARCHIVED status removed from comments
- **Fixed** in `backend/database/models.py`: template_status comment now reads `ACTIVE | DRAFT`
- **Fixed** in `backend/alembic/versions/c022_investigation_templates.py`: same

### Tests updated
- `backend/tests/test_c022_sprint0_schema.py` Test 4 rewritten to use `template_id`, `description`, `domain_filter_count` in ListItem assertions and `template_id` in Detail assertions. Added default-values coverage for ListItem.
- All 4 tests pass.
