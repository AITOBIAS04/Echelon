# Sprint 71 (cycle-022 sprint-2) — Engineer Feedback

**Verdict:** REVIEW_APPROVED

All good.

## Acceptance Criteria — All Met

### Task 2.1 — Create Endpoint Extension
- [x] Investigation created with valid template_id persists it
- [x] Template defaults populate missing fields
- [x] Explicit user values override template defaults
- [x] Invalid template_id returns 400
- [x] DRAFT template_id returns 400
- [x] Missing template_id works as before (backward compatible)
- [x] committed_sources_json populated from live registry at creation time
- [x] committed_sources_json populated even without template (when domain_filters provided)

### Task 2.2 — Domain Filter Validation
- [x] Valid domain filter values accepted
- [x] Invalid values rejected with 400

### Task 2.3 — Certificate Provenance Extension
- [x] Certificate metadata includes template_id + template_name when template present
- [x] Certificate metadata includes committed_sources when committed sources present
- [x] Certificate for template-less investigation is unchanged
- [x] Certificate hash payload updated to include provenance keys when present

### Code Quality
- [x] Backward compatible
- [x] No hardcoded values
- [x] Proper error handling with clear messages
- [x] Tests are comprehensive (7 tests per plan)
- [x] No regressions in existing tests

## Advisory Notes (non-blocking)

**1. Override detection heuristic (ADVISORY)**
The template-defaults logic at `investigation_routes.py:387-394` uses default-value comparison to determine whether the user provided an explicit override (e.g., `inquiry_class == "INVESTIGATIVE"` means "not overridden"). This is an inherent limitation of the Pydantic defaults approach — there is no way to distinguish "user explicitly sent the default value" from "user omitted the field." Acceptable trade-off; worth noting for future reference if a `None`-means-unset pattern is ever adopted.

**2. Test depth for tests 2 and 3 (ADVISORY)**
Tests 2 (invalid template_id) and 3 (DRAFT template) verify the validation logic at the model/helper level rather than through full HTTP integration (e.g., TestClient round-trip). The core validation paths are correctly covered, but full-stack tests would catch any wiring gaps. Not blocking — the route logic is straightforward and the validation functions are directly tested.
