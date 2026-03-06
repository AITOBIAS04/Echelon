# Sprint 37 (Sprint-1, Cycle-016) Security Audit

**Auditor:** Paranoid Cypherpunk Auditor
**Date:** 2026-03-05
**Branch:** feature/cycle-016-results-surface
**Sprint:** Mock Purge + Real API Wiring
**Verdict:** APPROVED - LETS FUCKING GO

---

## Pre-Flight Verification

- Ledger: sprint-1 (cycle-016) = global sprint-37, status "pending"
- Engineer Feedback: APPROVED (Round 2 re-review, all 8 findings resolved)
- Build: Zero TSC errors, 19/19 tests pass

---

## Security Audit Results

### 1. Secrets & Credentials -- PASS

| Check | Result |
|-------|--------|
| Hardcoded API keys in source | None found |
| Hardcoded tokens/passwords | None found |
| Secrets in `vite.config.ts` | None -- only build-time metadata (timestamp, random hash) |
| `.env` files tracked in git | Neither `.env` nor `.env.local` are tracked (confirmed via `git ls-files`) |
| `.env.local` contains Vercel OIDC JWT | Local-only, gitignored, NOT a codebase issue |
| API URL in `.env` | `http://localhost:8000` -- development default only |

### 2. XSS / Cross-Site Scripting -- PASS (with pre-existing notes)

| Check | Result |
|-------|--------|
| `dangerouslySetInnerHTML` in Sprint-1 files | **None** -- zero instances in any Sprint-1 file |
| `dangerouslySetInnerHTML` pre-existing | 2 instances in files NOT touched by Sprint-1: `RLMFPage.tsx:312` (renders `agentThoughts` from local `useState`, not API data) and `CompareSidebar.tsx:181` (renders `generateMiniBars()` which builds static SVG bars with no user input). Both are pre-existing, neither accepts user/API input. Not a Sprint-1 concern. |
| Unescaped user input in JSX | **None** -- All Sprint-1 rendering uses React's default JSX escaping. `BreachConsolePage.tsx` renders `p.timeline_name`, `p.carrier_agent_name` etc. via JSX `{}` which auto-escapes. `PortfolioPage.tsx` renders `p.timeline_name`, `p.timeline_id` via JSX `{}`. All safe. |
| `innerHTML` / `document.write` / `eval` | None anywhere in Sprint-1 code |

### 3. Injection -- PASS

| Check | Result |
|-------|--------|
| SQL injection in `agent_repository.py` | **None** -- Uses SQLAlchemy ORM with parameterized `select().where()` queries. No raw SQL, no string interpolation in queries. |
| SQL injection in `agents_routes.py` | **None** -- Route uses `AgentRepository` methods only. The f-string in `HTTPException(detail=f"Agent {agent_id} not found")` is safe -- it goes to the HTTP response body, not a query. `agent_id` comes from a path parameter, and this pattern is standard FastAPI. |
| Frontend query injection | **None** -- All API calls use axios with structured params objects. No URL string interpolation with user input. |
| `eval()` / `new Function()` | None in Sprint-1 code |

### 4. Authentication & Authorization -- PASS

| Check | Result |
|-------|--------|
| API client auth | `apiClient` (axios) uses request interceptor that attaches `Bearer` token from `localStorage` on every request. Standard pattern. |
| Token handling | Tokens stored in `localStorage` (`access_token`, `refresh_token`). On 401, both are cleared. |
| Auth bypass | No endpoints skip auth on the client side. Backend route uses `Depends(get_db)` for DB sessions -- auth middleware is at the FastAPI app level (not in this file). |
| Credential leakage in URLs | No tokens or credentials in URL query strings. Auth is header-based only. |

### 5. Data Exposure -- PASS

| Check | Result |
|-------|--------|
| `console.log` in Sprint-1 hooks | **Zero** -- None of the 5 hooks (`usePortfolio`, `useMarketplace`, `useAgents`, `useBreaches`, `useWatchlist`) contain any `console.log`. |
| `console.log` in Sprint-1 pages | **Zero** -- Neither `PortfolioPage.tsx` nor `BreachConsolePage.tsx` contain `console.log`. |
| `console.log` in API client | Only in `import.meta.env.DEV` guard (lines 6-8, 32-47). Development-only logging. Warns on errors, logs API URL. Acceptable for dev mode. |
| PII in logging | No PII (user IDs, emails, tokens) logged anywhere in Sprint-1 code. |
| Stack traces exposed to users | Error states show generic messages ("Failed to load portfolio", "Check that the backend is running", "Loading paradox data..."). No stack traces. |

### 6. Error Handling -- PASS

| Check | Result |
|-------|--------|
| Failed API requests | TanStack Query handles errors via `error` property. `usePositions`, `usePortfolioSummary`, `useParadoxes`, `useMarketData`, `useRibbonEvents`, `useWatchlist` all expose `error` for UI handling. |
| Error UI | `PortfolioPage.tsx` has dedicated error state (lines 28-37) with user-friendly message. `BreachConsolePage.tsx` has loading state. |
| API client error interceptor | Catches errors, logs dev-only warnings, clears tokens on 401. Properly re-throws with `Promise.reject(error)` so callers can handle. |
| Backend error handling | 404 with sanitized message for missing agent. Pydantic validation on response models prevents leaking extra fields. |

### 7. API Security -- PASS

| Check | Result |
|-------|--------|
| Request timeout | 10 second timeout configured in API client (line 15). Prevents hanging requests. |
| Pagination limits | Backend enforces `limit: int = Query(100, ge=1, le=500)` and `offset: int = Query(0, ge=0)`. Cannot request unbounded data. |
| Input validation | FastAPI + Pydantic validates all query params and response models. `archetype` filter uses `.upper()` comparison, not raw query. |
| Rate limiting | Not in scope for Sprint-1 (API wiring). Would be at reverse proxy / middleware level. |

### 8. Build Security -- PASS

| Check | Result |
|-------|--------|
| Secrets in `vite.config.ts` | None. Only `__BUILD_ID__` (timestamp) and `__BUILD_HASH__` (random 6-char string). |
| Unsafe eval in dev | No `eval`, no dynamic imports of user input. |
| Source maps | `sourcemap: true` in production build -- this is a deliberate choice for debugging. Acceptable for this project stage. |
| Dependencies | Vitest, @testing-library/react, @testing-library/jest-dom, jsdom -- all well-known, actively maintained testing packages. No known CVEs. |

---

## Quality Audit Results

### 9. Type Safety -- PASS

| Check | Result |
|-------|--------|
| `any` in Sprint-1 hooks | **Zero** -- All 5 hooks are fully typed with zero `any` usage. |
| `any` in Sprint-1 pages | **Zero** -- `PortfolioPage.tsx` and `BreachConsolePage.tsx` have zero `any`. |
| `any` in Sprint-1 tests | `as any` used for mock typing (e.g., `mockGet.mockResolvedValueOnce({ data: ... } as any)`). Acceptable and standard practice for test mocks. |
| `any` pre-existing | Some `any` in `ExportConsolePage.tsx`, `LaunchpadPage.tsx`, `useParadoxes.ts`, `useVerificationRuns.ts` -- all pre-existing, not Sprint-1 scope. |

### 10. Null/Undefined Handling -- PASS

| Check | Result |
|-------|--------|
| `usePositions` | `data?.positions ?? []` -- safe nullish coalescing |
| `usePortfolioSummary` | `data ?? null` -- safe |
| `useMarketData` | `resp?.timelines ?? []` -- safe |
| `useRibbonEvents` | `resp?.flaps ?? []` -- safe |
| `useBreaches/useParadoxes` | `resp?.paradoxes ?? []`, `resp?.total_active ?? 0` -- safe |
| `useWatchlist` | `watchlistQuery.data?.items ?? []`, `timelinesQuery.data?.timelines ?? []` -- safe |
| `useAgentRoster` | `resp?.agents ?? []` -- safe |
| Backend `_agent_to_response` | Uses `getattr(agent, field, default)` for every field -- safe against missing ORM attributes |
| `PortfolioPage` | Guards `summary &&` before accessing summary fields. Guards `summary?.highest_risk_timeline_id` before rendering. |
| `BreachConsolePage` | Guards `p.carrier_agent_name &&` before rendering carrier info. `p.carrier_agent_sanity ?? 0` for nullable field. |

### 11. Race Conditions -- PASS

| Check | Result |
|-------|--------|
| Concurrent fetches in `useWatchlist` | Two independent queries (`watchlistQuery`, `timelinesQuery`). Join happens in `useMemo` with both as dependencies. TanStack Query handles concurrent fetching safely -- no manual promise management. |
| Interval cleanup | `usePortfolioStatus` and `useAgentsStatus` both properly `return () => clearInterval(interval)` in useEffect cleanup. |
| TanStack Query intervals | `refetchInterval` is managed by TanStack Query internally -- no manual `setInterval`. |
| State mutations | `useBetting` properly manages `isBetting` state with try/finally pattern. |

### 12. Mock Purge Verification -- PASS

| Check | Result |
|-------|--------|
| Sprint-1 hooks (5 files) | Zero `getMock*`, `MOCK_*`, `demoStore`, `useDemoBreaches`, `STATIC_ACTIVE`, `STATIC_HISTORY` imports. |
| `BreachConsolePage.tsx` | Zero demo imports. Uses `useParadoxes()` from real API. |
| `PortfolioPage.tsx` | Zero demo imports. Uses `usePositions()`, `usePortfolioSummary()` from real API. |
| Pre-existing mock references | `useTimelineDetail.ts`, `useVerificationRuns.ts`, `useCertificates.ts` still use mock/demo data -- these are NOT in Sprint-1 scope. They will be wired in later sprints. |

---

## Observations (Non-Blocking)

1. **Pre-existing `dangerouslySetInnerHTML`**: Two instances exist in files not touched by Sprint-1 (`RLMFPage.tsx`, `CompareSidebar.tsx`). Neither takes user/API input. Recommend audit when those pages are rewired.

2. **Pre-existing `console.log` scatter**: 15+ `console.log` statements exist across components not in Sprint-1 scope (Watchlist, MyAgents, SigintPanel, BreachesModal, ParadoxPanel, TimelineDetailPage, BlackboxPage). Recommend a console cleanup pass in a future sprint.

3. **`useParadoxes.ts` (legacy)**: A separate `useParadoxes.ts` hook file still exists alongside the new `useBreaches.ts` which also exports `useParadoxes()`. The legacy file uses raw `fetch()` instead of the centralized `apiClient`. Not a Sprint-1 regression (pre-existing), but recommend consolidation to avoid confusion.

4. **Source maps in production build**: `sourcemap: true` is deliberate. When deploying to production, consider conditional source maps or uploading to an error tracking service only.

---

## Verdict

**APPROVED - LETS FUCKING GO**

Sprint-1 (Mock Purge + Real API Wiring) passes all security and quality gates. The implementation is clean, well-typed, properly guarded against nulls, uses parameterized queries, auto-escapes all rendered content, exposes zero secrets, and handles errors gracefully. The mock purge is verified complete for all 5 hooks and 2 pages in scope. TanStack Query is used correctly with proper intervals and cleanup. The adapter pattern for API-to-presentation mapping is sound.

Zero blockers. Zero security findings in Sprint-1 scope. Ship it.
