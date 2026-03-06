# Sprint 37 (Sprint-1, Cycle-016) Implementation Report

**Sprint:** Mock Purge + Real API Wiring
**Branch:** `feature/cycle-016-results-surface`
**Date:** 2026-03-05

---

## Summary

All 7 tasks completed. Frontend hooks rewritten from mock data to real backend API calls using TanStack Query. Test framework (Vitest) installed and 19 tests pass. Zero TSC errors (`tsc -b --noEmit` clean).

### Review Feedback Addressed (Round 1)

All 6 bugs and 2 issues from engineer-feedback resolved:

- **BUG-1**: `useWatchlist.ts` — `t.slug` → derived from `t.name` via `toLowerCase().replace()`
- **BUG-2**: `usePortfolio.test.ts` — Fixed field names to match `PortfolioSummary` interface (`total_value_usd`, `active_position_count`, `active_founder_positions`, etc.)
- **BUG-3**: Consumer component breakage — Fixed `AgentRoster` (`actions_count`→`actions`), `WingFlapFeed` (`ANCHOR`→`STABILISE`), `WatchlistFilterBar` (added missing filter configs), `Watchlist.tsx` (added filter count entries), `AgentsPage.tsx` (typed legacy hooks, added `emoji` to archetype distribution, fixed `formatTime` signature)
- **BUG-4**: `type-alignment.test.ts` — Excluded test files from `tsconfig.app.json` (standard Vite+Vitest pattern); added `/// <reference types="vitest/config" />` to `vite.config.ts`
- **BUG-5**: `agents_routes.py` — Added `get_all_dead()` to `AgentRepository`, wired `is_alive=false` to query dead agents
- **BUG-6**: `usePortfolio.ts` — Removed unused `UserPosition` import
- **ISSUE-1**: Duplicate `Paradox` interface — Removed from `useBreaches.ts`, now imports from `types/index.ts`
- **ISSUE-2**: Duplicate `AgentArchetype` type — Removed from `types/index.ts`, now imports/re-exports from `types/agents.ts`
- **Bonus**: Removed unused `useState` import from `CertificatesListView.tsx`, unused `clsx` import from `RunsListView.tsx`

---

## Task 1.1: TypeScript Type Alignment — COMPLETED

**Files modified:**
- `frontend/src/types/portfolio.ts` — Rewrote `UserPosition`, `PortfolioSummary` to match `backend/schemas/user_schemas.py`
- `frontend/src/types/agents.ts` — Rewrote `Agent` to match backend ORM model (snake_case fields)
- `frontend/src/types/marketplace.ts` — Cleaned up, kept legacy types for backwards compat
- `frontend/src/types/watchlist.ts` — Rewrote `WatchlistItem` to match backend, kept legacy `WatchlistTimeline`
- `frontend/src/types/index.ts` — Updated `WingFlapType` (+11 types), `StabilityDirection`, `Timeline` fields

**Files created:**
- `frontend/src/types/investigation.ts` — Full investigation toolset types (30+ types, zero `any`)
- `frontend/src/types/theatre.ts` — Full theatre types (11 types)

**Pattern:** API response types use snake_case matching raw JSON from backend. Legacy presentation types preserved at bottom with clear comments.

## Task 1.2: Portfolio Page — Wire to Real API — COMPLETED

**Files modified:**
- `frontend/src/hooks/usePortfolio.ts` — Rewrote from ~210 lines mock data to TanStack Query (`/api/v1/user/positions`, `/api/v1/user/portfolio/summary`). 30s refetch intervals.
- `frontend/src/pages/PortfolioPage.tsx` — Rewrote to use new API types. Added loading/empty/error states.

**Removed:** `useRiskMetrics`, `useAllocation`, `useCorrelations`, `useRiskItems`, `useRecommendations`, `useGhostForks`, `usePortfolioAgents`, `useForkDetails`, `useYieldBreakdown` (all mock-only hooks).

## Task 1.3: Marketplace Page — Wire to Real API — COMPLETED

**Files modified:**
- `frontend/src/hooks/useMarketplace.ts` — Rewrote from ~360 lines mock data to TanStack Query (`/api/v1/butterfly/timelines/health`, `/api/v1/butterfly/flaps`). Adapter pattern: `timelineToMarket()` transforms `Timeline` → `Market` so MarketCard/CompareSidebar unchanged.

## Task 1.4: Agents Page — Wire to Real API — COMPLETED

**Files modified:**
- `backend/api/agents_routes.py` — Enhanced `AgentResponse` from 5 fields to 18 fields (full model). Added `_agent_to_response()` helper with safe `getattr` defaults.
- `frontend/src/hooks/useAgents.ts` — Rewrote to TanStack Query (`/api/v1/agents`). Added `EnrichedAgent` interface + `enrichAgent()` function mapping API fields to presentation fields (emoji, color, sanityLevel, generation, lineage, etc.).

## Task 1.5: Paradox/Breach — Wire to Real API — COMPLETED

**Files modified:**
- `frontend/src/hooks/useBreaches.ts` — Rewrote from mock `getMockBreaches()` to TanStack Query (`/api/v1/paradox/active`). Two hooks: `useBreaches()` returns adapted `Breach[]` for BreachesPanel/OverviewTab; `useParadoxes()` returns raw `Paradox[]` for BreachConsolePage.
- `frontend/src/pages/BreachConsolePage.tsx` — Rewrote from `useDemoBreaches`/`demoStore`/`STATIC_ACTIVE`/`STATIC_HISTORY` to real paradox data. Action buttons disabled (extraction/abandonment endpoints not fully wired). History shows placeholder.

**Adapter:** `paradoxToBreach()` maps backend `Paradox` → legacy `Breach` type (severity class → severity level, status mapping, affected timeline construction).

## Task 1.6: Watchlist — Wire to Real API — COMPLETED

**Files modified:**
- `frontend/src/types/watchlist.ts` — Added legacy filter values back to `WatchlistFilter` type (component still uses 'brittle', 'paradox-watch', etc.)
- `frontend/src/hooks/useWatchlist.ts` — Rewrote from mock `getMockWatchlist()` to dual-fetch: `/api/v1/user/watchlist` + `/api/v1/butterfly/timelines/health`. Joins watchlist items with timeline health data via `timelineToWatchlistTimeline()` adapter.

**Pattern:** Backend watchlist returns item IDs; timeline health provides the rich data. Join produces `WatchlistTimeline[]` matching existing component expectations.

## Task 1.7: Sprint 1 Tests — COMPLETED

**Dependencies installed:** `vitest`, `@testing-library/react`, `@testing-library/jest-dom`, `jsdom`

**Configuration:**
- `frontend/vite.config.ts` — Added `test` config block (globals, jsdom, setup file)
- `frontend/package.json` — Added `test` and `test:watch` scripts
- `frontend/src/test/setup.ts` — Imports `@testing-library/jest-dom`

**Test files created (5 files, 19 tests):**

| File | Tests | Coverage |
|------|-------|----------|
| `usePortfolio.test.ts` | 3 | API call, response transform, empty state |
| `useMarketplace.test.ts` | 3 | Timeline→Market adapter, stability status, empty state, stats derivation |
| `useAgents.test.ts` | 3 | Agent enrichment (genesis/child), empty list, archetype distribution |
| `BreachConsolePage.test.tsx` | 4 | Paradox rendering, empty state, extracting badge, disabled buttons |
| `type-alignment.test.ts` | 6 | FE/BE field alignment (Portfolio, Agents, Paradox, Timeline), mock purge audit (hooks + BreachConsolePage) |

**Result:** 19/19 passed, 794ms total.

---

## Acceptance Criteria

- [x] All 5 test files pass (19 tests total)
- [x] Zero mock data imports in Sprint 1 hooks (`usePortfolio`, `useMarketplace`, `useAgents`, `useBreaches`, `useWatchlist`)
- [x] Zero demo imports in `BreachConsolePage` (no `demoStore`, `useDemoBreaches`, `STATIC_ACTIVE`, `STATIC_HISTORY`)
- [x] Zero TSC errors (`npx tsc -b --noEmit` clean — build mode)
- [x] All review feedback bugs (BUG-1 through BUG-6) and issues (ISSUE-1, ISSUE-2) resolved

---

## Files Changed Summary

| File | Action | Task |
|------|--------|------|
| `frontend/src/types/portfolio.ts` | REWRITE | 1.1 |
| `frontend/src/types/agents.ts` | REWRITE | 1.1 |
| `frontend/src/types/marketplace.ts` | REWRITE | 1.1 |
| `frontend/src/types/watchlist.ts` | REWRITE + EDIT | 1.1, 1.6 |
| `frontend/src/types/index.ts` | REWRITE | 1.1 |
| `frontend/src/types/investigation.ts` | NEW | 1.1 |
| `frontend/src/types/theatre.ts` | NEW | 1.1 |
| `frontend/src/hooks/usePortfolio.ts` | REWRITE | 1.2 |
| `frontend/src/pages/PortfolioPage.tsx` | REWRITE | 1.2 |
| `frontend/src/hooks/useMarketplace.ts` | REWRITE | 1.3 |
| `backend/api/agents_routes.py` | REWRITE | 1.4 |
| `frontend/src/hooks/useAgents.ts` | REWRITE | 1.4 |
| `frontend/src/hooks/useBreaches.ts` | REWRITE | 1.5 |
| `frontend/src/pages/BreachConsolePage.tsx` | REWRITE | 1.5 |
| `frontend/src/hooks/useWatchlist.ts` | REWRITE | 1.6 |
| `frontend/vite.config.ts` | EDIT | 1.7 |
| `frontend/package.json` | EDIT | 1.7 |
| `frontend/src/test/setup.ts` | NEW | 1.7 |
| `frontend/src/hooks/__tests__/usePortfolio.test.ts` | NEW | 1.7 |
| `frontend/src/hooks/__tests__/useMarketplace.test.ts` | NEW | 1.7 |
| `frontend/src/hooks/__tests__/useAgents.test.ts` | NEW | 1.7 |
| `frontend/src/pages/__tests__/BreachConsolePage.test.tsx` | NEW | 1.7 |
| `frontend/src/test/type-alignment.test.ts` | NEW + EDIT | 1.7, feedback |
| `frontend/src/components/agents/AgentRoster.tsx` | EDIT | feedback |
| `frontend/src/components/sigint/WingFlapFeed.tsx` | EDIT | feedback |
| `frontend/src/components/fieldkit/WatchlistFilterBar.tsx` | EDIT | feedback |
| `frontend/src/components/fieldkit/Watchlist.tsx` | EDIT | feedback |
| `frontend/src/pages/AgentsPage.tsx` | EDIT | feedback |
| `frontend/src/components/verify/CertificatesListView.tsx` | EDIT | feedback |
| `frontend/src/components/verify/RunsListView.tsx` | EDIT | feedback |
| `frontend/tsconfig.app.json` | EDIT | feedback |
| `backend/database/repositories/agent_repository.py` | EDIT | feedback |

**Total:** 33 files (25 modified, 8 new)
