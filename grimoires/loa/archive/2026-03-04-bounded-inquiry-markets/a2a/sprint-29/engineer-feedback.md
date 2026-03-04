# Sprint-29 Review — Engineer Feedback

> **Reviewer**: Senior Technical Lead
> **Sprint**: sprint-1 (global: sprint-29)
> **Cycle**: cycle-014 (Bounded Inquiry Markets)
> **Verdict**: **APPROVED**

---

## Previous Feedback Resolution

### Issue 1 (FIXED): NULL → "COUNTERFACTUAL" coalescing ✓

Verified in `backend/schemas/theatre.py`:
- `TemplateResponse.coalesce_inquiry_class` (line 85-89) ✓
- `TheatreResponse.coalesce_inquiry_class` (line 133-137) ✓
- `TheatreCertificateResponse.coalesce_inquiry_class` (line 182-186) ✓

Tests verified in `backend/schemas/tests/test_theatre_inquiry.py`:
- `test_response_null_coalesces_to_counterfactual` (line 115) ✓
- `test_certificate_null_coalesces_to_counterfactual` (line 155) ✓
- `test_template_null_coalesces_to_counterfactual` (line 174) ✓

All good.

## Acceptance Criteria Checklist

| Task | Criterion | Status |
|------|-----------|--------|
| T1 | InquiryClass enum with 5 values | ✓ |
| T1 | INQUIRY_CLASS_ALIASES map | ✓ |
| T1 | resolve_inquiry_class() with case-insensitive, alias-aware resolution | ✓ |
| T1 | Unit tests (26) | ✓ |
| T2 | TheatreCreate inquiry_class with template_json extraction | ✓ |
| T2 | TheatreResponse/CertificateResponse/TemplateResponse inquiry_class | ✓ |
| T2 | NULL → "COUNTERFACTUAL" coalescing in response schemas | ✓ |
| T2 | Unit tests (14) | ✓ |
| T3 | TheatreTemplate inquiry_class column with index | ✓ |
| T3 | Theatre inquiry_class column with index | ✓ |
| T3 | TheatreCertificate inquiry_class column | ✓ |
| T3 | All nullable for backward compatibility | ✓ |
| T4 | create_theatre() passes inquiry_class to template and theatre | ✓ |
| T4 | GET endpoints return "COUNTERFACTUAL" for NULL rows | ✓ |
| T5 | T0Context inquiry_class field | ✓ |
| T5 | ContextCompiler.compile() inquiry_class parameter | ✓ |
| T5 | compute_hash() includes inquiry_class | ✓ |
| T5 | Hash determinism tests (6) | ✓ |
| T6 | Certificate description updated to canonical 5 values | ✓ |
| T6 | Standalone validate_inquiry_class validator | ✓ |
| T6 | resolution_trigger_reason field + generator param | ✓ |
| T6 | Unit tests (12) | ✓ |
| T7 | No stale INVESTIGATION/AUDIT references | ✓ |
| T8 | 395 passed, 4 skipped, 0 new failures | ✓ |

## Test Results

```
395 passed, 4 skipped
```
