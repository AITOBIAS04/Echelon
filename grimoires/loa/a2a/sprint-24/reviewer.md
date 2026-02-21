# Implementation Report: Sprint 24 — Demo Mode + Integration

> Cycle: cycle-029 | Sprint: sprint-3 (global: sprint-24)
> Implementer: AI Engineer | Date: 2026-02-19

## Summary

All 4 tasks completed. Added verification slice to demoStore (types, state, methods), verification seed data and tick loop to DemoEngine (5 runs, 3 certs, state machine progression), wired demo mode into both hooks (useSyncExternalStore subscriptions with client-side filtering/sorting/pagination), and verified end-to-end integration.

## Tasks Completed

### 3.1 — Verification slice in demoStore ✓

**File**: `frontend/src/demo/demoStore.ts`

- `DemoVerificationRunStatus` type: all 7 statuses
- `DemoVerificationRun` type: matches `VerificationRun` shape (run_id, status, progress, total, construct_id, repo_url, error, certificate_id, created_at, updated_at)
- `DemoReplayScore` type: matches `ReplayScore` shape (12 fields)
- `DemoCertificate` type: matches `Certificate` shape with `replay_scores: DemoReplayScore[]`
- `verificationRuns: DemoVerificationRun[]` added to `StoreState`
- `certificates: DemoCertificate[]` added to `StoreState`
- `verificationListeners` listener set created
- `getVerificationRuns()` — returns state.verificationRuns
- `getCertificates()` — returns state.certificates
- `addVerificationRun(run)` — prepends to array, emits
- `updateVerificationRun(id, updater)` — maps in place, emits
- `addCertificate(cert, max=10)` — prepends, caps at 10, emits
- `subscribeVerification(listener)` — returns unsubscribe function
- No changes to existing slices

### 3.2 — Verification seed data and tick loop in DemoEngine ✓

**File**: `frontend/src/demo/DemoEngine.tsx`

- `seedVerification()`:
  - Seeds 5 runs: 2 COMPLETED (with cert links), 1 SCORING (47/90), 1 FAILED (with error), 1 PENDING
  - Seeds 3 certificates linked to completed runs with realistic scores
  - Each certificate has 3-5 replay scores (via `makeReplayScores` helper)
  - Only seeds if `demoStore.getVerificationRuns().length === 0`
- `tickVerification()` state machine:
  - PENDING → INGESTING: sets total to random 60-120
  - INGESTING → SCORING: increments progress by 3-8, transitions at 30% of total
  - SCORING → CERTIFYING: increments progress by 2-5, transitions at 90% of total
  - CERTIFYING → COMPLETED: generates mock certificate via `makeCertificate`, links to run
- `scheduleVerification()`: 2-3s interval (same setTimeout recursion pattern)
- Timer added to `timers.current.verification`
- Timer cleared on unmount and on `enabled=false`
- Uses seeded RNG `r` (same `mulberry32(1337)`)
- Helper functions: `makeReplayScores(rng, count, baseTs)`, `makeCertificate(rng, id, constructId, replayCount, createdAt)`

### 3.3 — Wire demo mode into hooks ✓

**File**: `frontend/src/hooks/useVerificationRuns.ts`

- Demo mode: subscribes to `demoStore.subscribeVerification` via `useSyncExternalStore`
- Returns demo runs filtered by status and construct_id (case-insensitive includes)
- `createRun` creates a `DemoVerificationRun` with PENDING status via `demoStore.addVerificationRun`
- `isLoading` always false in demo mode
- React Query disabled (`enabled: false` when isDemo)
- Client-side pagination: slice with offset/limit

**File**: `frontend/src/hooks/useCertificates.ts`

- `useCertificates`: subscribes to `demoStore.subscribeVerification` via `useSyncExternalStore`
  - Returns demo certificates sorted by `brier_asc` (default) or `created_desc`
  - Filters by construct_id (case-insensitive includes)
  - Client-side pagination
  - React Query disabled in demo mode
- `useCertificateDetail`: finds certificate in `demoStore.getCertificates()` by ID
  - Subscribes to verification listeners for live updates
  - React Query disabled in demo mode

### 3.4 — Integration verification ✓

- Build passes: `npx vite build` — SUCCESS
- VerifyPage chunk: `VerifyPage-Df7ZYxV2.js` (66.37 kB / 22.18 kB gzip)
- Main index chunk: `index-QwuubuWt.js` (1,041.84 kB / 287.63 kB gzip) — +4.72 kB from demo additions
- No TypeScript errors
- Demo data flow: DemoEngine seeds → demoStore state → hooks subscribe → UI renders

## Build Verification

- `npx vite build` — **SUCCESS**
- No TypeScript errors
- No changes to existing page bundles (except minor size increase in shared chunks)

## Files Changed

| File | Action | Lines |
|------|--------|-------|
| `frontend/src/demo/demoStore.ts` | Modified | +95 (types, state, methods) |
| `frontend/src/demo/DemoEngine.tsx` | Modified | +155 (seed, tick, schedule, helpers) |
| `frontend/src/hooks/useVerificationRuns.ts` | Modified | Rewritten (~95 lines) |
| `frontend/src/hooks/useCertificates.ts` | Modified | Rewritten (~115 lines) |

## Acceptance Criteria Status

All acceptance criteria from sprint.md tasks 3.1–3.4 are met. See sprint.md for full checklist.
