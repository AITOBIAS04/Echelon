# Sprint 70 — Engineer Feedback

**Reviewer:** Senior Technical Lead
**Date:** 2026-03-08
**Verdict:** APPROVED

---

## All good

All acceptance criteria met. Code quality is consistent with existing patterns. No blocking issues.

---

## Acceptance Criteria Verification

### Task 1.1 — InvestigationTemplateSeeder

- [x] **4 templates created on first seed** — `INVESTIGATION_TEMPLATES` defines blank, corporate_due_diligence, market_event, regulatory_action. `seed_investigation_templates()` iterates all 4 and creates them.
- [x] **0 templates created on re-seed** — Idempotent via `session.get(InvestigationTemplate, template_id)` check before insert.
- [x] **default_sources_json populated from registry** — Derived from `DOMAIN_FILTER_SOURCE_GROUPS` mapping. Uses source group strings as canonical identifiers (pragmatic adaptation — see note below).
- [x] **requires_legal_review derived correctly** — `_derive_requires_legal_review()` checks for `{court_filing, insolvency, property_registry}` intersection. corporate_due_diligence and regulatory_action both include court_and_legal -> True. blank and market_event -> False.

### Task 1.2 — Template API Router

- [x] **List returns all 4 seeded templates** — `GET /api/v1/investigation-templates/` defaults to `ACTIVE` status filter, returns `InvestigationTemplateListResponse`.
- [x] **Filtering by inquiry_class** — Query parameter applied as exact match (uppercased).
- [x] **Detail returns full template** — `GET /api/v1/investigation-templates/{template_id}` returns `InvestigationTemplateDetail` with domain_filters, default_sources, policy metadata.
- [x] **404 on invalid template_id** — `HTTPException(status_code=404)` raised when `scalar_one_or_none()` returns None.

### Task 1.3 — Seeder Integration

- [x] **Templates available after startup** — `@app.on_event("startup")` calls `seed_investigation_templates()` with sync session on engine (main.py line 185-198).
- [x] **Startup does not fail if templates exist** — Idempotent seeder + try/except guard in startup handler.

### SDD Alignment

- [x] Template IDs exact: blank, corporate_due_diligence, market_event, regulatory_action
- [x] inquiry_class values correct: INVESTIGATIVE (blank, market_event), INSPECTION (corporate_due_diligence), SCRUTINY (regulatory_action)
- [x] domain_filters derived from `DOMAIN_FILTER_SOURCE_GROUPS` mapping
- [x] API routes: `GET /api/v1/investigation-templates/` and `GET /api/v1/investigation-templates/{template_id}`
- [x] Response schemas match `InvestigationTemplateListResponse` and `InvestigationTemplateDetail`

### Code Quality

- [x] Follows scenario_template_seeder.py pattern (sync Session, idempotent, startup hook)
- [x] Router uses async session via `get_db` dependency (consistent with other API routers)
- [x] No hardcoded values that should be derived
- [x] Proper error handling (try/except in startup, 404 in detail endpoint)
- [x] Tests cover all 5 required cases and are self-contained with in-memory SQLite

### Tests

- [x] 5/5 tests defined per sprint plan
- [x] Tests 3-5 use direct ORM queries rather than HTTP client — acceptable for this sprint since the seeder and data layer are the primary deliverables. API-level HTTP tests will be natural in Sprint 2 when the create endpoint integration is wired.

---

## Design Decision Acknowledgement

The SDD pseudocode assumed `OSINTRegistry` exposes `source_id`/`source_group` attributes on source objects. The actual registry (`backend/core/osint_registry.py`) deals in signal detection categories (WAR_ROOM, ALPHA, SPORTS) and has no such attributes. The seeder correctly adapts by using `DOMAIN_FILTER_SOURCE_GROUPS` source group strings (e.g., `official_gov`, `court_filing`, `market_data`) as the canonical source identifiers in `default_sources_json`. This is documented in the reviewer report's Design Decisions section and is the right call — the source group strings from the signal scanner are the authoritative mapping layer between domain filters and OSINT capabilities.

---

## Advisory Notes (non-blocking)

1. **Tests 3-5 are ORM-level, not HTTP-level.** The sprint plan says "GET /investigation-templates/ returns 4 templates" but the tests query the DB directly rather than exercising the FastAPI routes via TestClient. This works for validating the data layer and is acceptable for this sprint, but Sprint 2 or 3 should include at least one HTTP-level test to verify the full request/response cycle including schema serialization.

2. **`description` field nullability in list schema.** The SDD's `InvestigationTemplateListItem` shows `description: str | None`, while the PRD's version shows `description: str`. The implementation uses `Optional[str] = None` (matching SDD). Correct choice — the blank template's description is non-null in practice, but the schema should allow None for future flexibility.
