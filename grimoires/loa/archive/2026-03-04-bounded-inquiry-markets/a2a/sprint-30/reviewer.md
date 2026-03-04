# Sprint-30 Implementation Report

> **Cycle**: cycle-014 (Bounded Inquiry Markets)
> **Sprint**: sprint-2 (global: sprint-30)
> **Goal**: Inquiry-Aware Runtime + Templates + E2E
> **Status**: Implementation complete -- awaiting review

---

## Summary

Threaded inquiry-class-aware runtime behaviour through 6 layers: resolution triggers, evidence rules, agent behaviour, templates, certificate validation, and E2E tests. All 555 scoped tests pass (4 skipped -- pre-existing), zero new failures.

## Tasks Completed

### Task 1: Resolution Trigger System

**File:** `backend/market/resolution.py` (MODIFIED)

- `ResolutionTrigger(str, Enum)` with 6 values: simulation_terminal, evidence_threshold_met, criteria_complete, participation_threshold, claim_verdict, time_window_closed
- `SettlementReport`: added `inquiry_class: str = "COUNTERFACTUAL"` and `resolution_trigger_reason: str = "simulation_terminal"` fields (defaults preserve backward compat)
- `ResolutionEngine.check_resolution_ready(inquiry_class, evidence_state, theatre_config) -> (bool, ResolutionTrigger)` static method with per-inquiry-class resolution logic (SDD section 6.3)
- `ResolutionEngine.settle()` accepts optional `inquiry_class` and `resolution_trigger_reason` parameters
- **Tests:** `backend/market/tests/test_resolution_inquiry.py` -- 25 tests

### Task 2: Evidence Accumulation Rules

**File:** `backend/services/evidence_service.py` (NEW)

- `EvidenceValidation` frozen dataclass with validation results and metrics
- `InquiryEvidenceRules.validate_evidence(inquiry_class, evidence_snapshot, theatre_config) -> EvidenceValidation`
- Per-inquiry-class rules:
  - COUNTERFACTUAL: any evidence present is valid
  - INVESTIGATIVE: require corroboration_minimum distinct sources
  - INSPECTION: single-source acceptable, binary pass/fail
  - SURVEY: participation count as evidence
  - SCRUTINY: adversarial confirmation required
- **Tests:** `backend/services/tests/test_evidence_service.py` -- 17 tests

### Task 3: Agent Behaviour Adaptation

**File:** `backend/agents/inquiry_behaviour.py` (NEW)

- `InquiryProfile` frozen dataclass: pattern_name_override, evidence_weight_modifier, momentum_weight_modifier, action_description
- `INQUIRY_PROFILES` dict with 30 entries (6 archetypes x 5 inquiry classes)
- COUNTERFACTUAL profiles use identity modifiers (1.0, 1.0) to preserve backward compat with existing tests
- Non-COUNTERFACTUAL profiles modify evidence and momentum weights per SDD section 5.2
- `InquiryBehaviourAdapter.get_profile(archetype, inquiry_class) -> InquiryProfile`
- `DEFAULT_PROFILE` for unknown combinations

**File:** `backend/agents/rules_engine.py` (MODIFIED)

- `decide()` reads `ctx.inquiry_class`, gets InquiryProfile, creates modified T0Context with scaled risk_appetite and evidence_sensitivity
- Pattern name overridden from inquiry profile
- Action description prepended to reasoning trace
- **Tests:** `backend/agents/tests/test_inquiry_behaviour.py` -- 21 tests

### Task 4: Template Library -- 4 New Templates

**Files:** 4 new JSON files in `osint/osint_pipeline/theatre/templates/`

- `counterfactual_geopolitical_v1.json`: COUNTERFACTUAL, market path, 2 outcomes (YES/NO)
- `investigative_corporate_v1.json`: INVESTIGATIVE, market path, 2 outcomes (CONFIRMED/UNCONFIRMED)
- `survey_asset_valuation_v1.json`: SURVEY, market path, 3 outcomes (UNDERVALUED/FAIR/OVERVALUED)
- `scrutiny_tvl_audit_v1.json`: SCRUTINY, market path, 2 outcomes (VERIFIED/FALSIFIED)
- All include inquiry_class, schema_version, oracle_config, resolution_rules, committed_sources

### Task 5: Inquiry-Aware Certificate Generation

**File:** `osint/osint_pipeline/models/certificate.py` (MODIFIED)

- Added `validate_resolution_trigger` model validator that validates trigger reason against expected types per inquiry class
- `time_window_closed` universally acceptable as fallback
- Empty trigger reason allowed for backward compat
- Updated Sprint 1 test to use valid trigger for INSPECTION inquiry class

**File:** `backend/services/theatre_evidence.py` (MODIFIED)

- Added `validate_for_inquiry(inquiry_class, theatre_config, snapshot)` method
- Delegates to `InquiryEvidenceRules.validate_evidence()`
- Uses lazy import to avoid circular dependencies
- **Tests:** 15 tests in `osint/tests/test_certificate_inquiry.py` (3 new, 1 updated)

### Task 6: E2E Tests -- One Per Inquiry Class

**File:** `backend/tests/test_bounded_inquiry_e2e.py` (NEW)

- 6 test functions (5 inquiry classes + 1 backward compat):
  - `TestCounterfactualE2E`: YES/NO, simulation_terminal trigger
  - `TestInvestigativeE2E`: CONFIRMED/UNCONFIRMED, evidence_threshold_met trigger
  - `TestInspectionE2E`: ACTIVE/INACTIVE, criteria_complete trigger
  - `TestSurveyE2E`: UNDERVALUED/FAIR/OVERVALUED, participation_threshold trigger
  - `TestScrutinyE2E`: VERIFIED/FALSIFIED, claim_verdict trigger
  - `TestDefaultCounterfactualBackwardCompat`: default inquiry_class is COUNTERFACTUAL
- Each test: create market -> spawn 3 agents -> 10 trading ticks -> resolution check -> settlement -> certificate evidence validation
- Asserts: inquiry_class consistent across all layers, resolution_trigger_reason matches

### Task 7: Backward Compatibility Validation

- All existing rules engine tests pass (18 tests) -- COUNTERFACTUAL profiles use identity modifiers
- All existing market e2e tests pass (4 tests)
- All existing services tests pass (105 tests)
- All existing osint tests pass (85 tests, 4 skipped)
- Theatres without inquiry_class default to COUNTERFACTUAL

### Task 8: Sprint 2 Test Suite + Regression

```
555 passed, 4 skipped (pre-existing)
```

Scoped regression: `python3 -m pytest -q backend/schemas/ backend/agents/ backend/market/ backend/services/ backend/tests/test_bounded_inquiry_e2e.py osint/tests/`

Full baseline: 13 pre-existing collection errors documented and unchanged (sqlalchemy, dotenv, coinbase_commerce, scripts.run_construct_calibration).

## Files Modified

| File | Change |
|------|--------|
| `backend/market/resolution.py` | MODIFIED -- ResolutionTrigger enum, SettlementReport fields, check_resolution_ready() |
| `backend/market/tests/test_resolution_inquiry.py` | NEW -- 25 tests |
| `backend/services/evidence_service.py` | NEW -- InquiryEvidenceRules |
| `backend/services/tests/test_evidence_service.py` | NEW -- 17 tests |
| `backend/agents/inquiry_behaviour.py` | NEW -- InquiryProfile, INQUIRY_PROFILES, InquiryBehaviourAdapter |
| `backend/agents/rules_engine.py` | MODIFIED -- inquiry-aware decide() |
| `backend/agents/tests/test_inquiry_behaviour.py` | NEW -- 21 tests |
| `backend/services/theatre_evidence.py` | MODIFIED -- validate_for_inquiry() |
| `osint/osint_pipeline/models/certificate.py` | MODIFIED -- validate_resolution_trigger model validator |
| `osint/osint_pipeline/engine/certificate_generator.py` | Unchanged (Sprint 1 already wired) |
| `osint/tests/test_certificate_inquiry.py` | MODIFIED -- 3 new tests, 1 updated |
| `osint/.../counterfactual_geopolitical_v1.json` | NEW -- template |
| `osint/.../investigative_corporate_v1.json` | NEW -- template |
| `osint/.../survey_asset_valuation_v1.json` | NEW -- template |
| `osint/.../scrutiny_tvl_audit_v1.json` | NEW -- template |
| `backend/tests/test_bounded_inquiry_e2e.py` | NEW -- 6 E2E tests |

## New Tests Summary

| Test File | Count | Coverage |
|-----------|-------|----------|
| `backend/market/tests/test_resolution_inquiry.py` | 25 | Resolution trigger enum, per-class readiness checks, case insensitivity |
| `backend/services/tests/test_evidence_service.py` | 17 | Evidence validation per inquiry class, corroboration, participation |
| `backend/agents/tests/test_inquiry_behaviour.py` | 21 | Profile completeness, adapter lookup, rules engine integration |
| `backend/tests/test_bounded_inquiry_e2e.py` | 6 | Full lifecycle per inquiry class, backward compat |
| `osint/tests/test_certificate_inquiry.py` | +3 | Trigger validation, mismatch rejection, time_window universality |
| **Total new** | **72** | |

## Design Decisions

1. **COUNTERFACTUAL profiles use identity modifiers (1.0)**: Preserves backward compatibility with all existing rules engine tests. Non-COUNTERFACTUAL inquiry classes modify evidence and momentum weights.

2. **check_resolution_ready() is separate from settle()**: Called before begin_resolution() to determine readiness and reason. Existing settle() flow is preserved -- the new method is additive.

3. **Certificate trigger validation is a model_validator, not field_validator**: Because it needs to cross-reference inquiry_class and resolution_trigger_reason, which are separate fields.

4. **Evidence service uses dict-or-object polymorphism**: Accepts both EvidenceSnapshot objects and plain dicts, making it easy to test and integrate without tight coupling.

5. **Theatre evidence collector uses lazy import**: The `validate_for_inquiry()` method imports InquiryEvidenceRules lazily to avoid circular dependencies between backend/services/ modules.
