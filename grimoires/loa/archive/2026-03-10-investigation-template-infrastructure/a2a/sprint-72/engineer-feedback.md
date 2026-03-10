# Engineer Feedback — Sprint 72 (cycle-022 sprint-3)

**Reviewer:** Senior Technical Lead
**Date:** 2026-03-09
**Verdict:** REVIEW_APPROVED

---

All good.

Every acceptance criterion verified against actual code and backend truth:

- **Task 3.1**: API client types match backend schemas field-for-field. Hook returns loading/error states. 5-minute stale time appropriate for seeded data.
- **Task 3.2**: Static TEMPLATES array fully removed. Wizard fetches from API via `useInvestigationTemplates()`. Template detail hook applies defaults (inquiry_class, domainFilters, stopCondition, time_window_days) via guarded useEffect. Signal-origin mapping (`inferTemplateFromSignalOrigin`) implements all 4 mapping rules exactly as specified and validates against fetched template list with blank fallback.
- **Task 3.3**: All 9 domain filter IDs verified character-for-character against backend `DomainFilter` enum in `signal_scanner.py`. Old frontend-invented IDs (`regulatory`, `media_news`, `social_sentiment`, `corporate_registry`, `financial_filings`, etc.) are gone. `DomainFilterId` type derived from `as const` array — compatible.
- **Task 3.4**: `template_id` included in `createInvestigation()` request body type and sent by wizard. Inquiry classes reduced from 3 frontend-only to 5 backend-aligned values (INVESTIGATIVE, INSPECTION, SCRUTINY, SURVEY, COUNTERFACTUAL). Build passes.
- **Tests**: 5 tests with proper API mocking covering template rendering, default population, signal-origin prefill, payload alignment, and inquiry class enumeration.

No issues found.
