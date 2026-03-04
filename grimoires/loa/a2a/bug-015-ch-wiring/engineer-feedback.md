# Engineer Feedback — bug-015-ch-wiring

**Reviewer**: Senior Technical Lead
**Date**: 2026-03-04
**Verdict**: All good

## Summary

All 5 tasks meet acceptance criteria. Clean, surgical fixes with no over-engineering.

- **Task 1** (source_params): Minimal 3-line addition to `CollectionPlan`, 2-line extraction in `build_plan()`, 3-line merge in `_collect_with_timeout()`. `_build_request()` untouched — good separation. `request.update(extra)` is the correct merge semantic (source overrides generic on collision).
- **Task 2** (CH export): Import + `__all__` entry. Alphabetical placement.
- **Task 3** (env var fix): `.lower() in ("1", "true", "yes")` — handles case-insensitive matching correctly.
- **Task 4** (monkeypatch removal): Clean removal. The E2E test now exercises the actual `source_params` path end-to-end, which is the whole point of this bug fix.
- **Task 5** (tests): Request-capture pattern in `test_source_params_merged_into_request` is the right approach. Cross-leak test (`test_source_params_only_applied_to_matching_collector`) verifies isolation. 9 env gating tests cover the boundary cases.

## Approval

All good.
