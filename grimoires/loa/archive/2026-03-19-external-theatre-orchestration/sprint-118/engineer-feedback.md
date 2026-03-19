All good

# Engineer Review — Sprint 118 (Cycle-038b Sprint 2: Orchestrator Composition)

**Reviewer:** Senior Technical Lead
**Date:** 19 March 2026
**Verdict:** APPROVED

---

## 1. Composition Correctness

The orchestrator calls each service in the correct order with the correct arguments:

1. `parse_construct_json(theatre_input.construct_json)` — correct, passes raw JSON string per `theatre_policy_rules.py:89` signature.
2. `extract_enriched_fixture(slug, version, meta)` — correct, matches `external_theatre_fixture_extractor.py:27-31` signature.
3. `plan_theatre_checks(spec_slug=slug, meta=meta)` — correct, matches `theatre_check_planner.py:27-29` signature with keyword args.
4. `execute_theatre_checks(planned_checks=planned_dicts, fixture=fixture_input)` — correct, matches `theatre_check_runner.py:37-40` signature.
5. `build_comparison_bundle(execution_result, fixture_input, certificate_id, event_keys, scope_keys)` — correct, matches `theatre_comparison_bundle_builder.py:25-31` signature.
6. `generate_candidates(bundles=successful_bundles)` — correct, matches `theatre_comparison_candidates.py:18-20` signature.

The pipeline ordering is correct: parse before extract (needs meta), extract before plan (needs meta), plan before execute (needs planned checks + fixture), execute before bundle (needs execution result).

## 2. PlannedCheck to Dict Bridge

`_planned_checks_to_dicts()` at `external_theatre_orchestrator.py:215-225` produces dicts with `check_id` and `check_type` keys. The runner at `theatre_check_runner.py:55-56` reads `check.get("check_type")` and `check.get("check_id")` — these match. The runner also passes the full `check` dict to `_dispatch()` but only reads `check_type` and `check_id` from it, so no additional fields are required. Correct.

## 3. event_keys / scope_keys Threading

At `external_theatre_orchestrator.py:188-189`:
```python
event_keys=event_keys if event_keys else None,
scope_keys=scope_keys if scope_keys else None,
```

This correctly converts empty lists (`[]`) to `None` to trigger the bundle builder's fallback behavior. The bundle builder at `theatre_comparison_bundle_builder.py:69-78` uses `None` as the sentinel for "no caller-provided keys, use template-ID fallback" vs `[]` meaning "caller explicitly supplied zero keys." This matches the SDD section 2.3 decision #4. Correct.

## 4. Error Isolation

Each theatre is processed independently via `_prepare_single_theatre()`. Parse failures (`ValueError`) are caught at line 135. Extraction failures are detected via `extraction_result.success` at line 151. Planning failures are caught with a generic `Exception` at line 163. Bundle building failures are caught at line 191. In every error case, a `TheatrePreparationEntry` with the `error` field populated is returned, and the loop in `prepare_external_theatres()` continues to the next theatre. Correct.

## 5. Candidate Generation

At `external_theatre_orchestrator.py:71-72`:
```python
successful_bundles = [e.bundle for e in entries if e.bundle is not None]
candidates = generate_candidates(bundles=successful_bundles) if successful_bundles else []
```

This correctly filters to only non-None bundles and passes the list to `generate_candidates()`. The guard `if successful_bundles` avoids calling the generator with an empty list (though it would handle that gracefully). The `generate_candidates()` function at `theatre_comparison_candidates.py:18` expects `list[ExecutedTheatreComparisonBundle]` — bundles from successful entries are exactly this type. Correct.

## 6. Feedback Derivation (READY / DEGRADED / BLOCKED)

At `external_theatre_orchestrator.py:415-420`:
```python
if not extraction.success or not meta.theatre_templates:
    overall_readiness = "BLOCKED"
elif extraction.fallbacks_used:
    overall_readiness = "DEGRADED"
else:
    overall_readiness = "READY"
```

This matches SDD section 3.4 exactly:
- BLOCKED: extraction failed or no templates found
- DEGRADED: extraction succeeded but fallbacks were used (e.g., `oracle_threshold_defaulted`)
- READY: extraction succeeded with no fallbacks

Note: The feedback function is only called when `meta is not None and entry.extraction is not None` (line 77), so `extraction.success` being False here would only happen if someone calls `_build_builder_feedback` directly with a failed extraction — the guard logic is still correct for that case. Correct.

## 7. Test Coverage

All 8 sprint-2 tests are present and cover the required scenarios:

| # | Test | Coverage |
|---|------|----------|
| 19 | `test_orchestrator_single_theatre` | Single input, 1 bundle, 0 candidates |
| 20 | `test_orchestrator_paired_theatres` | Paired input with shared keys, 2 bundles, 1+ candidates |
| 21 | `test_orchestrator_shared_identity_threading` | event_keys echo and bundle propagation |
| 22 | `test_orchestrator_no_keys_fallback` | Empty keys -> template-ID fallback, no cross-candidates |
| 23 | `test_orchestrator_error_propagation` | One invalid + one valid, error isolation verified |
| 24 | `test_orchestrator_all_failures` | Both invalid, empty candidates, total_failed=2 |
| 25 | `test_orchestrator_certificate_id_threading` | certificate_id flows to bundle |
| 26 | `test_orchestrator_empty_request` | Empty theatres list, zero everything |

All acceptance criteria from the sprint plan are met. Tests exercise the full pipeline (parse -> extract -> plan -> execute -> bundle -> candidates) without mocking the composed services, which provides genuine integration coverage.

## 8. Minor Observations (Non-Blocking)

1. **`_build_builder_feedback` is imported in tests as a private function** (`from backend.services.external_theatre_orchestrator import _build_builder_feedback` at test line 607). This is fine for testing but note that sprint-3 test #33 (`test_feedback_blocked_on_missing_templates`) will call this directly. No issue, just noting the private-API test coupling.

2. **`execution_passed` / `execution_failed` are both set** at orchestrator lines 208-209. These are non-exclusive (both could theoretically be False if `has_critical_failures` is False and the entry has no error), which is the correct state for a successful execution with no critical failures.

3. **Scope key field names**: The sprint plan's prose at line 299 uses a shorthand notation (`region=`, `entity=`, `time_window=`) but the actual test correctly uses the Pydantic model fields (`scope_type=`, `scope_value=`). No mismatch.

---

**Summary:** The orchestrator correctly composes all 5 existing services, handles the PlannedCheck-to-dict bridge properly, threads shared identity keys with correct None-vs-empty semantics, isolates per-theatre errors, and derives feedback readiness per the SDD. All 8 tests cover the required scenarios. No issues found.
