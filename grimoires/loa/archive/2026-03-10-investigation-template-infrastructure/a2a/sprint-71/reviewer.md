# Sprint 71 (cycle-022 sprint-2) — Investigation Create Integration + Certificate Provenance

**Status:** completed
**Date:** 2026-03-08

## Summary

Wired `template_id` and `committed_sources_json` into the investigation creation path and certificate provenance chain. Investigations can now be created from backend-owned templates with automatic default application, domain filter validation, source snapshot resolution, and certificate provenance recording.

## Files Modified

| File | Change | Lines |
|------|--------|-------|
| `backend/schemas/investigation_schemas.py` | Added `template_id: Optional[str]` to `InvestigationCreateRequest` | +1 |
| `backend/api/investigation_routes.py` | Template validation, domain filter validation, committed_sources resolution, template defaults application, provenance pass-through to certificate builder | +65 |
| `backend/database/repositories/investigation_repository.py` | Added `template_id` and `committed_sources` params to `create()`, added `selectinload(Investigation.template)` to `get()` | +5 |
| `backend/investigation/certificate.py` | Added `template_id`, `template_name`, `committed_sources` params to `build()`, added provenance keys to hash payload | +12 |
| `backend/investigation/toolset.py` | Added provenance params to `build_certificate()` pass-through | +8 |

## Files Created

| File | Purpose | Lines |
|------|---------|-------|
| `backend/tests/test_c022_sprint2_create_certificate.py` | 7 tests for create integration + certificate provenance | ~280 |

## Test Results

```
7 passed — sprint-2 tests
9 passed — sprint-0 + sprint-1 regression
212 passed — full backend suite (3 pre-existing failures unrelated)
```

## Acceptance Criteria

- [x] `InvestigationCreateRequest` accepts optional `template_id`
- [x] Valid `template_id` validated against template table (exists + ACTIVE)
- [x] Invalid `template_id` returns 400
- [x] DRAFT `template_id` returns 400
- [x] Template defaults applied for unset fields (inquiry_class, domain_filters, stop_condition, stop_config)
- [x] Explicit user values override template defaults
- [x] Missing `template_id` works as before (backward compatible)
- [x] Domain filters validated against backend `DomainFilter` enum (400 on invalid)
- [x] `committed_sources_json` populated from live registry via DOMAIN_FILTER_SOURCE_GROUPS
- [x] `committed_sources_json` populated even without template (when domain_filters provided)
- [x] Certificate hash payload includes `template_id`, `template_name`, `committed_sources` when present
- [x] Certificate hash changes when provenance keys are present vs absent
- [x] Certificates without template/committed sources remain unchanged
- [x] No regressions in sprint-0, sprint-1, or broader backend tests
