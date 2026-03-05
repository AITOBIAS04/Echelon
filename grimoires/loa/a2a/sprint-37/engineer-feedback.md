# Sprint 37 (Sprint-1) Engineer Review -- Senior Technical Lead (RE-REVIEW)

**Reviewer:** Senior Technical Lead
**Date:** 2026-03-05
**Branch:** feature/cycle-016-results-surface
**Sprint:** Mock Purge + Real API Wiring
**Review Round:** 2 (re-review after fixes)

---

## Verdict: APPROVED

All 6 bugs and 2 issues from Round 1 are verified as resolved. Zero TSC errors (`npx tsc -b --noEmit` clean). All 19 tests pass (`npx vitest run` -- 5 files, 19 tests, 817ms). No new issues introduced by the fixes.

---

## Verification of Round 1 Findings

### BUG-1: `t.slug` does not exist on `Timeline` type -- RESOLVED

**File:** `frontend/src/hooks/useWatchlist.ts`, line 34
**Verified:** `slug: t.name.toLowerCase().replace(/[^a-z0-9]+/g, '-')` -- derives slug from name as recommended.

### BUG-2: `usePortfolioSummary` test uses wrong field names -- RESOLVED

**File:** `frontend/src/hooks/__tests__/usePortfolio.test.ts`, lines 104-126
**Verified:** Mock data now uses correct fields: `total_value_usd`, `active_position_count`, `active_founder_positions`, `total_founder_yield_earned_usd`. Assertions on lines 124-125 access `total_value_usd` and `active_founder_positions` which match the `PortfolioSummary` interface.

### BUG-3: Consumer components broken by Sprint-1 type changes -- RESOLVED

Verified each sub-item:

- **`AgentRoster.tsx:277`** -- Now uses `agent.actions || 0` (line 277). `EnrichedAgent` interface in `useAgents.ts:101` defines `actions: number` mapped from `agent.trades_count` (line 121). Correct.
- **`WingFlapFeed.tsx:84,86`** -- Comparison is now `flap.direction === 'STABILISE'` (line 84). No reference to `"ANCHOR"` anywhere in the file. `StabilityDirection` type is `'STABILISE' | 'DESTABILISE' | 'NEUTRAL'`. Correct.
- **`WatchlistFilterBar.tsx:18`** -- `FILTER_CONFIG` now includes all 8 `WatchlistFilter` values: `'all'`, `'timelines'`, `'agents'`, `'at-risk'`, `'brittle'`, `'paradox-watch'`, `'high-entropy'`, `'under-attack'`. Correct.
- **`Watchlist.tsx:118-127`** -- `counts` record now includes all `WatchlistFilter` keys: `'all'`, `'timelines'`, `'agents'`, `'at-risk'`, `'brittle'`, `'paradox-watch'`, `'high-entropy'`, `'under-attack'`. Correct.
- **`AgentsPage.tsx`** -- `useTheatres()` returns `TheatreView[]`, `useMovements()` returns `MovementView[]`, `useStrategyClusters()` returns `StrategyClusterView[]`, `useConflicts()` returns `ConflictView[]`. All four view interfaces are defined in `useAgents.ts` (lines 50-87) with the correct properties accessed by `AgentsPage.tsx`. Returns empty arrays (no backend endpoint yet) but typed correctly so `.map()` compiles without error.
- **`AgentsPage.tsx:51`** -- `formatTime` signature updated to `(date: string | Date)` handling both cases. Correct.
- **`useAgents.ts:174`** -- `useArchetypeDistribution()` now returns `emoji` field in each entry (line 174). Correct.

### BUG-4: `type-alignment.test.ts` uses Node APIs not available in tsconfig -- RESOLVED

**Files:** `frontend/tsconfig.app.json`, `frontend/vite.config.ts`
**Verified:** `tsconfig.app.json` line 28 excludes test files: `"exclude": ["src/**/*.test.ts", "src/**/*.test.tsx", "src/test"]`. This is the standard Vite+Vitest pattern -- test files run under Vitest's own TypeScript context (with Node types), not the app's tsconfig. `vite.config.ts` line 1 adds `/// <reference types="vitest/config" />` for proper test config typing.

### BUG-5: `agents_routes.py` returns empty list when `is_alive=false` -- RESOLVED

**Files:** `backend/api/agents_routes.py:100-103`, `backend/database/repositories/agent_repository.py:35-40`
**Verified:** Route now calls `repo.get_all_dead()` when `is_alive` is `False` (line 103). `AgentRepository.get_all_dead()` queries `Agent.is_alive == False` with proper SQLAlchemy filter. Correct.

### BUG-6: Unused import `UserPosition` in `usePortfolio.ts` -- RESOLVED

**File:** `frontend/src/hooks/usePortfolio.ts`, line 8-13
**Verified:** Import statement includes only `UserPositionsResponse`, `PortfolioSummary`, `ChartTimeframe`, `EquityDataPoint`. No `UserPosition` in the import. Correct.

### ISSUE-1: Duplicate `Paradox` interface in `useBreaches.ts` -- RESOLVED

**File:** `frontend/src/hooks/useBreaches.ts`, lines 7-8
**Verified:** `Paradox` is imported from `'../types'` (line 7) and re-exported (line 8). No local interface definition exists in the file. The single source of truth is `frontend/src/types/index.ts` which re-exports from the canonical `Paradox` interface (lines 130-148).

### ISSUE-2: Duplicate `AgentArchetype` type definition -- RESOLVED

**File:** `frontend/src/types/index.ts`, line 5
**Verified:** Line 5 reads `import type { AgentArchetype } from './agents';` -- imports rather than redefines. Line 203 re-exports: `export type { AgentArchetype, ... } from './agents';`. Single source of truth is `frontend/src/types/agents.ts:4`.

---

## Bonus Fixes Verified

- **`CertificatesListView.tsx`** -- Unused `useState` import removed. Line 5 now imports only needed icons.
- **`RunsListView.tsx`** -- Unused `clsx` import removed. Line 6 imports only needed icons.
- **`vite.config.ts:1`** -- Added `/// <reference types="vitest/config" />` for proper `test` property typing.

---

## Build Verification

| Check | Result |
|-------|--------|
| `npx tsc -b --noEmit` | Zero errors |
| `npx vitest run` | 19/19 passed (5 files, 817ms) |

---

## New Issues Introduced

None detected. All fixes are clean and minimal.

---

## What Was Done Well (Repeated from Round 1, Still Applies)

- Adapter pattern for API-to-presentation type bridging
- TanStack Query with appropriate refetchIntervals
- Type alignment tests against actual backend Python files
- Mock purge audit test as regression guard
- Defensive `getattr` defaults in `_agent_to_response()`
- Dual-hook pattern in `useBreaches.ts`

---

## Summary

All 8 findings from Round 1 verified as resolved with correct implementations. Zero new regressions. TypeScript compiler and test suite both clean. Sprint 1 is ready for audit.
