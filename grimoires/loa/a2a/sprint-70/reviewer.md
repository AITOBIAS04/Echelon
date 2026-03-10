# Sprint 70 — Reviewer Report

**Cycle:** cycle-022 (Investigation Template Infrastructure)
**Sprint:** sprint-1 (local) / sprint-70 (global)
**Label:** Seeder + API Endpoints
**Date:** 2026-03-08

---

## Summary

Implemented the investigation template seeder, read-only API endpoints, and startup integration. Four genesis templates are seeded with domain filter defaults, source group derivation from `DOMAIN_FILTER_SOURCE_GROUPS`, and policy metadata (`requires_legal_review`) derived from source group membership.

---

## Files Created/Modified

| File | Status | Lines |
|------|--------|-------|
| `backend/services/investigation_template_seeder.py` | **Created** | 156 |
| `backend/api/investigation_template_routes.py` | **Created** | 106 |
| `backend/tests/test_c022_sprint1_seeder_api.py` | **Created** | 220 |
| `backend/main.py` | **Modified** | +20 (router registration + startup seeder) |
| `grimoires/loa/ledger.json` | **Modified** | sprint-1 status → in_progress |

---

## Test Results

```
backend/tests/test_c022_sprint1_seeder_api.py::test_seeder_creates_4_templates PASSED
backend/tests/test_c022_sprint1_seeder_api.py::test_reseed_is_idempotent PASSED
backend/tests/test_c022_sprint1_seeder_api.py::test_list_returns_all_4_templates PASSED
backend/tests/test_c022_sprint1_seeder_api.py::test_filter_by_inquiry_class_inspection PASSED
backend/tests/test_c022_sprint1_seeder_api.py::test_corporate_due_diligence_detail PASSED

5 passed in 0.27s
```

Sprint-0 regression: 4/4 passed.

---

## Acceptance Criteria Checklist

### Task 1.1 — InvestigationTemplateSeeder
- [x] 4 genesis templates defined (blank, corporate_due_diligence, market_event, regulatory_action)
- [x] Domain filters mapped to source groups via `DOMAIN_FILTER_SOURCE_GROUPS`
- [x] `default_sources_json` populated from registry source group mappings
- [x] `requires_legal_review` derived from source group policy metadata (court_filing, insolvency, property_registry)
- [x] All 4 seeded as ACTIVE, is_seeded=True
- [x] Idempotent — 0 created on re-seed

### Task 1.2 — Template API Router
- [x] GET /api/v1/investigation-templates/ returns InvestigationTemplateListResponse
- [x] Filterable by inquiry_class (exact match)
- [x] Filterable by status (defaults to ACTIVE)
- [x] GET /api/v1/investigation-templates/{template_id} returns InvestigationTemplateDetail
- [x] 404 if template not found

### Task 1.3 — Seeder Integration
- [x] Seeder called on app startup via `@app.on_event("startup")`
- [x] Guarded with session/transaction (sync Session with engine)
- [x] Startup does not fail if templates already exist

---

## Design Decisions

1. **Source derivation uses source group IDs (not source object IDs):** The OSINT registry (`osint_registry.py`) contains signal detection classes without structured `source_id`/`source_group` attributes. The `DOMAIN_FILTER_SOURCE_GROUPS` mapping defines source group strings (e.g., `court_filing`, `market_data`) as the canonical identifiers. The seeder derives `default_sources_json` from these source group strings.

2. **Legal review derivation:** `requires_legal_review` is True when any source group in the template's defaults is in `{court_filing, insolvency, property_registry}` — these carry jurisdictional data protection constraints.

3. **Sync seeder pattern:** Follows the scenario_template_seeder.py pattern exactly — sync `Session`, called from tests directly and from startup via sync session on the sync engine.
