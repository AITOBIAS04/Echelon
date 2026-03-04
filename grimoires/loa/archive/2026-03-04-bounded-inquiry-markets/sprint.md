# Sprint Plan — Cycle-014: Bounded Inquiry Markets

**Cycle:** cycle-014
**Date:** 4 March 2026
**PRD:** grimoires/loa/prd.md
**SDD:** grimoires/loa/sdd.md
**Sprints:** 2
**Baseline:** 741 passed, 13 pre-existing failures

---

## Sprint 1 — Canonical Taxonomy + Schema Alignment ✅ REVIEW_APPROVED

**Global ID:** 29
**Tasks:** 8
**Focus:** Single source of truth enum, threaded through every layer

### Task 1: Canonical InquiryClass Enum ✅

**File:** `backend/schemas/inquiry.py` (NEW)
**Acceptance:**
- ✅ `InquiryClass` StrEnum with exactly 5 values: COUNTERFACTUAL, INVESTIGATIVE, INSPECTION, SURVEY, SCRUTINY
- ✅ `INQUIRY_CLASS_ALIASES` map: INVESTIGATION → INVESTIGATIVE, AUDIT → SCRUTINY
- ✅ `resolve_inquiry_class(raw: str) -> InquiryClass` accepts canonical values, aliases (case-insensitive), raises ValueError on unknown
- ✅ Unit tests in `backend/schemas/tests/test_inquiry.py`

### Task 2: Schema Alignment — Theatre Schemas ✅

**File:** `backend/schemas/theatre.py` (MODIFY)
**Acceptance:**
- ✅ `TheatreCreate`: add `inquiry_class: Optional[str]` field. Model validator extracts from `template_json` if not provided, validates via `resolve_inquiry_class()`
- ✅ `TheatreResponse`: add `inquiry_class: Optional[str]`
- ✅ `TheatreCertificateResponse`: add `inquiry_class: Optional[str]`
- ✅ `TemplateResponse`: add `inquiry_class: Optional[str]`
- ✅ Unit tests in `backend/schemas/tests/test_theatre_inquiry.py`

### Task 3: Schema Alignment — Database Models ✅

**File:** `backend/database/models.py` (MODIFY)
**Acceptance:**
- ✅ `TheatreTemplate`: add `inquiry_class: Mapped[Optional[str]]` column with index
- ✅ `Theatre`: add `inquiry_class: Mapped[Optional[str]]` column with index
- ✅ `TheatreCertificate`: add `inquiry_class: Mapped[Optional[str]]` column
- ✅ All nullable for backward compatibility (existing rows get NULL)
- ✅ No migration script needed (SQLite auto-adds nullable columns)

### Task 4: API Alignment — Theatre Routes ✅

**File:** `backend/api/theatre_routes.py` (MODIFY)
**Acceptance:**
- ✅ `create_theatre()`: extract `inquiry_class` from request body or `template_json`, resolve via `resolve_inquiry_class()`, store on Theatre and TheatreTemplate
- ✅ All GET endpoints include `inquiry_class` in response (NULL → "COUNTERFACTUAL" in serialisation)
- ✅ Validation: reject unknown inquiry classes (after alias resolution) with 400 response
- ✅ Test with alias input: `INVESTIGATION` → stored as `INVESTIGATIVE`

### Task 5: Agent T0 Context ✅

**File:** `backend/agents/context_compiler.py` (MODIFY)
**Acceptance:**
- ✅ `T0Context` dataclass: add `inquiry_class: str = "COUNTERFACTUAL"` field
- ✅ `ContextCompiler.compile()`: accept `inquiry_class` parameter, pass through
- ✅ `compute_hash()`: include `inquiry_class` in hashable dict
- ✅ Unit test: T0Context hash changes when inquiry_class changes
- ✅ Test in `backend/agents/tests/test_context_compiler_inquiry.py`

### Task 6: Certificate Alignment ✅

**Files:** `osint/osint_pipeline/models/certificate.py`, `osint/osint_pipeline/engine/certificate_generator.py` (MODIFY)
**Acceptance:**
- ✅ Certificate model: update `inquiry_class` field description to canonical 5 values
- ✅ Certificate model: add `resolution_trigger_reason: str` field (default empty)
- ✅ Certificate generator: accept `resolution_trigger_reason` parameter
- ✅ Validate inquiry_class in certificate model using standalone validator (avoids cross-package import)
- ✅ Test in `osint/tests/test_certificate_inquiry.py`

### Task 7: Stale Enum Cleanup ✅

**Files:** Sweep all files referencing INVESTIGATION or AUDIT as inquiry class values
**Acceptance:**
- ✅ `osint/osint_pipeline/models/certificate.py`: description updated (done in Task 6)
- ✅ `osint/osint_pipeline/engine/certificate_generator.py`: docstring updated (done in Task 6)
- ✅ No remaining references to `INVESTIGATION` or `AUDIT` as inquiry class values in the codebase
- ✅ Grep verification: zero hits for stale values in non-test, non-context Python/JSON files

### Task 8: Sprint 1 Test Suite ✅

**Acceptance:**
- ✅ All new tests pass
- Scoped regression: `python3 -m pytest -q backend/ osint/ mcp/` — zero new failures
- Tests cover: enum values, alias resolution, schema validation, T0Context, certificate field

---

## Sprint 2 — Inquiry-Aware Runtime + Templates + E2E ✅ REVIEW_APPROVED

**Global ID:** 30
**Tasks:** 8
**Focus:** Inquiry class influences runtime behaviour

### Task 1: Resolution Trigger System ✅

**File:** `backend/market/resolution.py` (MODIFY)
**Acceptance:**
- ✅ `ResolutionTrigger` enum with 6 values (simulation_terminal, evidence_threshold_met, criteria_complete, participation_threshold, claim_verdict, time_window_closed)
- ✅ `SettlementReport`: add `inquiry_class` and `resolution_trigger_reason` fields
- ✅ `ResolutionEngine.check_resolution_ready(inquiry_class, evidence_state, theatre_config) -> (bool, ResolutionTrigger)` static method
- ✅ Each inquiry class has distinct resolution logic (see SDD §6.3)
- ✅ Tests in `backend/market/tests/test_resolution_inquiry.py`

### Task 2: Evidence Accumulation Rules ✅

**File:** `backend/services/evidence_service.py` (NEW)
**Acceptance:**
- ✅ `InquiryEvidenceRules.validate_evidence(inquiry_class, evidence_snapshot, theatre_config) -> EvidenceValidation`
- ✅ Rules differ per inquiry class (see SDD §7)
- ✅ Investigative/Scrutiny: corroboration_minimum enforcement
- ✅ Inspection: single-source acceptable
- ✅ Survey: position distribution as evidence
- ✅ Tests in `backend/services/tests/test_evidence_service.py`

### Task 3: Agent Behaviour Adaptation ✅

**File:** `backend/agents/inquiry_behaviour.py` (NEW)
**Acceptance:**
- ✅ `InquiryProfile` dataclass: pattern_name_override, evidence_weight_modifier, momentum_weight_modifier, action_description
- ✅ `INQUIRY_PROFILES` dict with 30 entries (6 archetypes x 5 classes)
- ✅ `InquiryBehaviourAdapter.get_profile(archetype, inquiry_class) -> InquiryProfile`
- ✅ Default profile for unknown combinations

**File:** `backend/agents/rules_engine.py` (MODIFY)
- ✅ `decide()` reads `ctx.inquiry_class`, gets profile, applies modifiers before archetype dispatch
- ✅ Tests in `backend/agents/tests/test_inquiry_behaviour.py`

### Task 4: Template Library — 4 New Templates ✅

**Files:** 4 new JSON files in `osint/osint_pipeline/theatre/templates/`
**Acceptance:**
- ✅ `counterfactual_geopolitical_v1.json`: COUNTERFACTUAL, market path, 2 outcomes (YES/NO)
- ✅ `investigative_corporate_v1.json`: INVESTIGATIVE, market path, 2 outcomes (CONFIRMED/UNCONFIRMED)
- ✅ `survey_asset_valuation_v1.json`: SURVEY, market path, 3 outcomes (UNDERVALUED/FAIR/OVERVALUED)
- ✅ `scrutiny_tvl_audit_v1.json`: SCRUTINY, market path, 2 outcomes (VERIFIED/FALSIFIED)
- ✅ All include `inquiry_class` field, valid schema_version, outcomes, committed_sources

### Task 5: Inquiry-Aware Certificate Generation ✅

**File:** `osint/osint_pipeline/engine/certificate_generator.py` (MODIFY)
**Acceptance:**
- ✅ Certificate includes `inquiry_class` from theatre config
- ✅ Certificate includes `resolution_trigger_reason` from settlement
- ✅ Certificate verifier validates trigger matches expected type for inquiry class
- ✅ Wire `theatre_evidence.py` to `InquiryEvidenceRules` for validation

### Task 6: E2E Tests — One Per Inquiry Class ✅

**File:** `backend/tests/test_bounded_inquiry_e2e.py` (NEW)
**Acceptance:**
- ✅ 5 test functions (one per inquiry class)
- ✅ Each test: create theatre with template → spawn 3 agents → run 10 trading ticks with evidence injection → resolution triggers → settlement → certificate
- ✅ Assert: inquiry_class consistent across theatre, settlement report, and certificate
- ✅ Assert: resolution_trigger_reason matches expected trigger for the inquiry class
- ✅ Mock evidence, short scenarios, 3 agents minimum

### Task 7: Backward Compatibility Validation ✅

**Acceptance:**
- ✅ Existing theatre tests (012 Sponsored Theatre E2E) pass unchanged
- ✅ Existing agent tests (013 Agent Runtime) pass unchanged
- ✅ Existing certificate tests pass (aliases resolve correctly)
- ✅ Theatres without inquiry_class default to COUNTERFACTUAL

### Task 8: Sprint 2 Test Suite + Regression ✅

**Acceptance:**
- ✅ All new tests pass
- ✅ Full regression: `python3 -m pytest -q backend/ osint/ mcp/` — zero new failures vs baseline
- ✅ Pre-existing 13 failures documented and unchanged

---

## Sprint Registry

| Sprint | Local ID | Global ID | Tasks |
|--------|----------|-----------|-------|
| Sprint 1 | sprint-1 | 29 | 8 |
| Sprint 2 | sprint-2 | 30 | 8 |
