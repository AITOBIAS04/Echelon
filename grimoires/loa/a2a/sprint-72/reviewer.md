# Sprint 72 Review — Frontend Wire-Up + Alignment

**Cycle:** cycle-022 (Investigation Template Infrastructure)
**Sprint:** sprint-3 (local) / sprint-72 (global)
**Date:** 2026-03-08
**Builder:** Loa (frontend)

---

## Summary

Sprint 3 wires the frontend CreateInvestigationWizard to the backend investigation template API, aligns domain filter IDs to the backend DomainFilter enum, aligns inquiry class options to the backend enum, and sends `template_id` in the create investigation payload.

## Deliverables

### New Files (2)
- `frontend/src/api/investigationTemplates.ts` -- API client with `fetchInvestigationTemplates()` and `fetchInvestigationTemplate(id)`
- `frontend/src/hooks/useInvestigationTemplates.ts` -- TanStack Query hooks (`useInvestigationTemplates`, `useInvestigationTemplateDetail`) with 5-minute stale time

### Modified Files (3)
- `frontend/src/components/investigation/DomainFilterSelector.tsx` -- Replaced 9 frontend-invented domain filter IDs with backend DomainFilter enum values
- `frontend/src/components/investigation/CreateInvestigationWizard.tsx` -- Removed static TEMPLATES array, replaced with API hook; replaced inferTemplate() with signal-origin mapping against backend template list; aligned inquiry classes to 5 backend values (INVESTIGATIVE, INSPECTION, SCRUTINY, SURVEY, COUNTERFACTUAL); sends template_id in create payload; applies template defaults on selection
- `frontend/src/api/investigation.ts` -- Added `template_id` to `createInvestigation()` request body type

### Test File (1)
- `frontend/src/components/investigation/__tests__/CreateInvestigationWizard.test.tsx` -- Rewritten with 5 tests covering all sprint acceptance criteria

## Domain Filter Alignment

| Backend DomainFilter | Frontend Label | Old Frontend ID (removed) |
|---------------------|---------------|--------------------------|
| `corporate_and_entity` | Corporate & Entity | `corporate_registry` |
| `finance_and_markets` | Finance & Markets | `financial_filings` |
| `maritime` | Maritime | `supply_chain` |
| `airspace` | Airspace | (new) |
| `geopolitical_and_conflict` | Geopolitical & Conflict | `geopolitical` |
| `cyber_threat` | Cyber Threat | (new) |
| `property_and_land` | Property & Land | (was implicit) |
| `court_and_legal` | Court & Legal | `litigation` |
| `satellite_and_earth_observation` | Satellite & Earth Obs | `technical` |

Removed frontend-only IDs: `regulatory`, `media_news`, `social_sentiment`

## Inquiry Class Alignment

Replaced 3 frontend-only values (INVESTIGATIVE, MONITORING, VERIFICATION) with 5 backend enum values (INVESTIGATIVE, INSPECTION, SCRUTINY, SURVEY, COUNTERFACTUAL).

## Signal-Origin Mapping

The `inferTemplate()` function was replaced with `inferTemplateFromSignalOrigin()` which resolves against the fetched backend template list instead of hardcoded IDs. Mapping rules:
- `signal_category` containing `regulatory` or `signal_class === 'regulatory_clearance'` -> `regulatory_action`
- domain filters containing `finance_and_markets` -> `market_event`
- domain filters containing `corporate_and_entity` or `court_and_legal` -> `corporate_due_diligence`
- fallback -> `blank`

If a resolved template ID is not found in the API response (e.g., set to DRAFT), falls back to `blank`.

## Test Results

| # | Test | Status |
|---|------|--------|
| 1 | Wizard renders template list from API (mock) | PASS |
| 2 | Template selection populates wizard state with correct defaults | PASS |
| 3 | Signal-origin URL params prefill correct template from backend list | PASS |
| 4 | Domain filter IDs in create payload match backend enum values | PASS |
| 5 | `npm run build` passes with all changes | PASS |

## Build Status

`npm run build` passes clean. No TypeScript errors. No regressions in other test files (pre-existing failures unrelated to this sprint confirmed unchanged).

## Notes

- Template defaults are applied via a useEffect that fires when the template detail loads after selection. The `lastAppliedTemplateId` guard prevents re-application on re-renders.
- The wizard gracefully handles loading states (shows "Loading templates..." on step 2) and API errors (templates array falls back to empty).
- Signal-origin domain filter mappings were updated to use the new backend enum values throughout (SIGNAL_CLASS_DOMAIN_FILTERS, SIGNAL_CATEGORY_DOMAIN_FILTERS, and source-name heuristics).
