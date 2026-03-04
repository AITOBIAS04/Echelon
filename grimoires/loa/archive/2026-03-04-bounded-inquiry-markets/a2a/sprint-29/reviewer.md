# Sprint-29 Implementation Report

> **Cycle**: cycle-014 (Bounded Inquiry Markets)
> **Sprint**: sprint-1 (global: sprint-29)
> **Goal**: Canonical Taxonomy + Schema Alignment
> **Status**: Implementation complete — awaiting review (feedback addressed)

---

## Summary

Threaded the canonical `InquiryClass` taxonomy through every layer: enum, schemas, database, API, agent context, and certificate. All 395 tests pass (4 skipped — pre-existing).

## Feedback Addressed

### Issue 1 (FIXED): NULL → "COUNTERFACTUAL" coalescing in response schemas

**Feedback**: `TheatreResponse`, `TheatreCertificateResponse`, and `TemplateResponse` returned `null` for pre-014 rows instead of `"COUNTERFACTUAL"`.

**Fix**: Added `model_validator(mode="after")` to all three response schemas that coalesces `None` → `"COUNTERFACTUAL"`. Updated existing test from `assert r.inquiry_class is None` to `assert r.inquiry_class == "COUNTERFACTUAL"`. Added 2 new coalescing tests (certificate + template).

**Files changed**:
- `backend/schemas/theatre.py` — 3 validators added (TemplateResponse, TheatreResponse, TheatreCertificateResponse)
- `backend/schemas/tests/test_theatre_inquiry.py` — 1 test updated, 2 tests added (14 total, was 12)

### Issue 2 (Advisory — No fix): Pydantic 422 vs explicit 400

Accepted as standard FastAPI behaviour.

### Issue 3 (Advisory — No fix): Missing docstring arg

Cosmetic, accepted.

## Tasks Completed

### Task 1: Canonical InquiryClass Enum ✓

**File:** `backend/schemas/inquiry.py` (NEW)

- `InquiryClass(str, Enum)` with 5 values: COUNTERFACTUAL, INVESTIGATIVE, INSPECTION, SURVEY, SCRUTINY
- Uses `str, Enum` (not StrEnum) for Python 3.9 compatibility
- `INQUIRY_CLASS_ALIASES` map: INVESTIGATION → INVESTIGATIVE, AUDIT → SCRUTINY
- `resolve_inquiry_class(raw)` — case-insensitive, whitespace-stripping, alias-aware, raises ValueError on unknown
- **Tests:** `backend/schemas/tests/test_inquiry.py` — 26 tests

### Task 2: Schema Alignment — Theatre Schemas ✓

**File:** `backend/schemas/theatre.py` (MODIFIED)

- `TheatreCreate`: added `inquiry_class: Optional[str]` with model_validator extracting from `template_json`, validates via `resolve_inquiry_class()`
- `TheatreResponse`: added `inquiry_class: Optional[str] = None` with NULL → "COUNTERFACTUAL" coalescing
- `TheatreCertificateResponse`: added `inquiry_class: Optional[str] = None` with NULL → "COUNTERFACTUAL" coalescing
- `TemplateResponse`: added `inquiry_class: Optional[str] = None` with NULL → "COUNTERFACTUAL" coalescing
- **Tests:** `backend/schemas/tests/test_theatre_inquiry.py` — 14 tests

### Task 3: Schema Alignment — Database Models ✓

**File:** `backend/database/models.py` (MODIFIED)

- `TheatreTemplate`: added `inquiry_class: Mapped[Optional[str]]` column, indexed
- `Theatre`: added `inquiry_class: Mapped[Optional[str]]` column, indexed
- `TheatreCertificate`: added `inquiry_class: Mapped[Optional[str]]` column
- All nullable for backward compatibility

### Task 4: API Alignment — Theatre Routes ✓

**File:** `backend/api/theatre_routes.py` (MODIFIED)

- `create_theatre()`: passes `inquiry_class=body.inquiry_class` to TheatreTemplate and Theatre creation
- GET endpoints return "COUNTERFACTUAL" for pre-014 rows (via response schema coalescing)

### Task 5: Agent T0 Context ✓

**File:** `backend/agents/context_compiler.py` (MODIFIED)

- `T0Context`: added `inquiry_class: str = "COUNTERFACTUAL"` field
- `ContextCompiler.compile()`: accepts `inquiry_class` parameter, passes through
- `compute_hash()`: includes `inquiry_class` in hashable dict
- **Tests:** `backend/agents/tests/test_context_compiler_inquiry.py` — 6 tests (hash changes, same hash, frozen)

### Task 6: Certificate Alignment ✓

**Files:** `osint/osint_pipeline/models/certificate.py`, `osint/osint_pipeline/engine/certificate_generator.py` (MODIFIED)

- Certificate model: updated `inquiry_class` description to canonical 5 values
- Certificate model: added standalone `validate_inquiry_class` field_validator (avoids cross-package import)
- Certificate model: added `resolution_trigger_reason: str` field (default empty)
- Certificate generator: accepts `resolution_trigger_reason` parameter
- **Tests:** `osint/tests/test_certificate_inquiry.py` — 12 tests (canonical values, rejection of stale values)

### Task 7: Stale Enum Cleanup ✓

- Certificate model description: updated (Task 6)
- Certificate generator docstring: updated (Task 6)
- Grep verification: zero stale `INVESTIGATION`/`AUDIT` references as inquiry class values in non-test Python/JSON files

### Task 8: Sprint 1 Test Suite ✓

```
395 passed, 4 skipped (pre-existing)
```

Scoped regression: `python3 -m pytest -q backend/schemas/ backend/agents/ backend/market/ osint/tests/`

## Files Modified

| File | Change |
|------|--------|
| `backend/schemas/inquiry.py` | NEW — Canonical InquiryClass enum + aliases + resolver |
| `backend/schemas/tests/test_inquiry.py` | NEW — 26 tests |
| `backend/schemas/theatre.py` | MODIFIED — inquiry_class on 4 schemas + 3 coalescing validators |
| `backend/schemas/tests/test_theatre_inquiry.py` | NEW — 14 tests |
| `backend/database/models.py` | MODIFIED — 3 inquiry_class columns |
| `backend/api/theatre_routes.py` | MODIFIED — inquiry_class pass-through |
| `backend/agents/context_compiler.py` | MODIFIED — T0Context + compile + hash |
| `backend/agents/tests/test_context_compiler_inquiry.py` | NEW — 6 tests |
| `osint/osint_pipeline/models/certificate.py` | MODIFIED — description, validator, resolution_trigger_reason |
| `osint/osint_pipeline/engine/certificate_generator.py` | MODIFIED — resolution_trigger_reason param |
| `osint/tests/test_certificate_inquiry.py` | NEW — 12 tests |

## New Tests Summary

| Test File | Count | Coverage |
|-----------|-------|----------|
| `backend/schemas/tests/test_inquiry.py` | 26 | Enum values, aliases, case insensitivity, error messages |
| `backend/schemas/tests/test_theatre_inquiry.py` | 14 | TheatreCreate, response coalescing, certificate, template |
| `backend/agents/tests/test_context_compiler_inquiry.py` | 6 | T0Context inquiry_class, hash determinism |
| `osint/tests/test_certificate_inquiry.py` | 12 | Certificate validation, stale value rejection |
| **Total** | **58** | |
