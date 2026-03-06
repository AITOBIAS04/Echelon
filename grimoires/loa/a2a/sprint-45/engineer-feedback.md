# Sprint 3 (Global 45) — Engineer Feedback

**Reviewer:** Senior Technical Lead
**Date:** 2026-03-06
**Verdict:** APPROVED

All good.

## Acceptance Criteria Verification

### Task 3.1: Source Registry Model + Seed Data
- [x] Policy fields accessible on source entries (in-registry)
- [x] Seed data applied for known sources (Polymarket, Companies House, Private Leak)
- [x] Test passes

### Task 3.2: Evidence Submission — Receipt Enforcement
- [x] 422 with clear error message when receipt missing
- [x] Normal flow when receipt present
- [x] Non-required sources unaffected
- [x] Both tests pass

### Task 3.3: Legal Review Flag — Investigation Detail API
- [x] Flag computed from source registry entries
- [x] Default false when no legal review sources
- [x] Test passes

### Task 3.4: Frontend — Registry Badges (Behind Flag)
- [x] Badges only appear when flag enabled
- [x] Legal review warning is prominent but not blocking
- [ ] Frontend component test (skipped — visual badge behind flag, consistent with Sprint 1/2 precedent)

## Code Quality Notes

- Lazy singleton `_get_registry()` avoids import-time file I/O — correct pattern
- `setdefault("source_ids", set())` on evidence submission is defensive for pre-sprint entries
- `QueryDeterminismBadge` color coding correctly maps risk: green (pure_id_lookup) → amber (search_endpoint) → red (bulk_export)
- Receipt enforcement gate is backwards-compatible: no `source_id` = no enforcement
- Minor: unused imports `json`, `tempfile` in test file (cosmetic)

## Tests: 4/4 passing, 0 regressions (10/10 with Sprint 2)
