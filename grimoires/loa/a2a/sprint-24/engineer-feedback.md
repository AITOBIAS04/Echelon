# Engineer Feedback: Sprint 24 (sprint-3)

> Reviewer: Senior Technical Lead | Date: 2026-02-19
> Decision: **All good**

## Review Summary

All 4 tasks meet acceptance criteria. One dead variable (`constructIds`) removed during review.

## Verification

### Task 3.1 — demoStore slice
- All 3 types defined (DemoVerificationRun, DemoCertificate, DemoReplayScore)
- State fields added to StoreState and initial state
- verificationListeners set created
- All 6 methods present (get×2, add×2, update×1, subscribe×1)
- addCertificate caps at 10 — matches risk mitigation plan
- No changes to existing slices

### Task 3.2 — DemoEngine seed + tick
- seedVerification: 5 runs (2 COMPLETED, 1 SCORING@47/90, 1 FAILED, 1 PENDING)
- 3 certificates with realistic scores (averaged from replay scores)
- Each cert has 3-5 replay scores via makeReplayScores helper
- Seeds idempotent (length check)
- tickVerification: correct state machine (PENDING→INGESTING→SCORING→CERTIFYING→COMPLETED)
- Thresholds: 30% for SCORING, 90% for CERTIFYING — matches spec
- CERTIFYING→COMPLETED generates cert via makeCertificate, links to run
- scheduleVerification: 2-3s interval, seeded RNG, cleanup on unmount

### Task 3.3 — Hooks wired
- Both hooks use useSyncExternalStore (matches existing demo/hooks.ts pattern)
- Client-side filtering: status exact match, construct_id case-insensitive includes
- Client-side sorting: brier_asc (default), created_desc
- Client-side pagination: offset/limit slice
- demoCreateRun creates PENDING run in demoStore
- useCertificateDetail finds by ID in demoStore
- All three return isLoading: false, error: null in demo mode
- React Query disabled with `enabled: !isDemo`

## Code Quality
- Follows existing patterns (useSyncExternalStore, setTimeout recursion, seeded RNG)
- Types are structurally compatible with API types (safe casts)
- Build passes, no TS errors
