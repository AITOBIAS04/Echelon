APPROVED - LETS FUCKING GO

# Sprint 4 (sprint-40) Security Audit — Investigation Lifecycle Console + Navigation Redesign

**Auditor:** Paranoid Cypherpunk Auditor
**Date:** 5 March 2026
**Verdict:** APPROVED — All 7 security checks PASS

---

## Pre-Flight Checks

| Check | Result |
|-------|--------|
| Engineer feedback starts with "All good" | PASS |
| `COMPLETED` marker does not exist | PASS |
| Reviewer file lists 16 files (12 source + 4 test) | PASS |

---

## Files Audited (16 total)

### Source Files (12)
1. `frontend/src/components/investigation/CreateInvestigationWizard.tsx` — 385 lines
2. `frontend/src/components/investigation/DomainFilterSelector.tsx` — 137 lines
3. `frontend/src/components/investigation/StopConditionConfigurator.tsx` — 169 lines
4. `frontend/src/hooks/useInvestigation.ts` — 163 lines
5. `frontend/src/components/investigation/InvestigationProgressBar.tsx` — 89 lines
6. `frontend/src/components/investigation/StopConditionProgress.tsx` — 127 lines
7. `frontend/src/components/layout/Sidebar.tsx` — 285 lines
8. `frontend/src/router.tsx` — 190 lines
9. `frontend/src/pages/CreateInvestigationPage.tsx` — 19 lines
10. `frontend/src/pages/SignalFeedPage.tsx` — 13 lines
11. `frontend/src/components/investigation/SignalCard.tsx` — 78 lines
12. `frontend/src/components/investigation/SignalFeedPanel.tsx` — 92 lines

### Test Files (4)
13. `frontend/src/components/investigation/__tests__/CreateInvestigationWizard.test.tsx` — 6 tests
14. `frontend/src/components/investigation/__tests__/InvestigationProgressBar.test.tsx` — 5 tests
15. `frontend/src/components/investigation/__tests__/SignalFeedPanel.test.tsx` — 2 tests
16. `frontend/src/components/layout/__tests__/Navigation.test.tsx` — 5 tests

### Supporting Files Also Verified
- `frontend/src/api/investigation.ts` — All API calls go through `apiClient`
- `frontend/src/types/investigation.ts` — Full type coverage, no `any` types

---

## Security Checklist

### 1. Secrets — PASS

No hardcoded credentials, API keys, tokens, or secrets found in any file. No `process.env` references in sprint files. No `.env` imports. Clean.

### 2. Input Validation / XSS — PASS

- **Zero instances of `dangerouslySetInnerHTML`** across all 16 files.
- **Zero instances of `innerHTML` or `document.write`**.
- All user input flows through React's standard JSX rendering (auto-escaped).
- Wizard text fields (`textarea`, `input`) are bound to state via `onChange` handlers with controlled components. Values rendered back via `{state.inquiryQuestion}` inside JSX text nodes — React auto-escapes.
- `SignalCard` renders `signal.signal_class.replace(/_/g, ' ')` as text content in a `<span>`, not as raw HTML. Safe.
- `StopConditionProgress` renders numeric/string values from API data as text content. No raw HTML injection vectors.
- `JSON.stringify(state.stopConfig, null, 2)` in the review step renders inside a `<pre>` tag as text content. React-escaped. Safe.

### 3. Injection — PASS

- **Zero instances of `eval()`** across all files.
- **Zero template literal injection vectors** — URL construction in `api/investigation.ts` uses `investigationId` parameter in template literals for API paths (`/api/v1/investigations/${investigationId}`). This is server-routed through `apiClient` (axios-based) which properly encodes URL components. The `investigationId` comes from React Query keys derived from API response data, not user-editable input.
- No SQL injection vectors (frontend-only code, all data access via REST API).
- `parseInt()` and `parseFloat()` in `StopConditionConfigurator` have fallback values (`|| 1` and `|| 0`), preventing NaN propagation.

### 4. Data Privacy — PASS

- **Zero `console.log`, `console.error`, or `console.warn`** statements in any sprint source file.
- No PII collected — wizard fields are inquiry question (business question), domain filters (category enums), stop conditions (configuration), theatre/construct IDs (system identifiers). No personal data.
- No sensitive data logged or exposed in error messages. Error rendering in wizard (line 344-346) shows `createMutation.error.message` which comes from the API layer — this is standard error display, not info disclosure.
- No `localStorage` or `sessionStorage` usage.

### 5. API Security — PASS

- **All API calls go through `apiClient`** (verified in `api/investigation.ts`). The `apiClient` is an axios instance that handles Bearer token injection and error logging per the module docstring.
- **No direct `fetch()` calls** — zero instances found in any sprint file.
- **No `XMLHttpRequest`** usage.
- Error handling present: wizard catches mutation errors (line 102-104, `setSubmitted(false)` on failure), error message displayed to user. React Query handles retry logic via `QueryClient` configuration.
- API paths are well-structured REST endpoints (`/api/v1/investigations/`, sub-resources at `/{id}/evidence`, `/{id}/claims`, etc.).

### 6. Auth/Authz — PASS

- All data fetching goes through `useQuery` hooks in `useInvestigation.ts`, which call functions from `api/investigation.ts`, which use `apiClient`. Authenticated request chain is intact.
- `createInvestigation` mutation uses `apiClient.post`. Authenticated.
- No bypass paths — no direct `fetch()`, no `axios.create()`, no unauthenticated HTTP calls.
- Route protection relies on `AppLayout` wrapping all routes in `router.tsx`. Investigation routes (`/investigation`, `/investigation/signals`, `/investigation/create`) are children of the root `AppLayout` route, inheriting authentication guards.

### 7. Code Quality — PASS

- **No obvious bugs detected.**
- **Race conditions:** `useCreateInvestigation` uses `useMutation` with `onSuccess` cache invalidation — standard TanStack Query pattern, no race conditions. The `submitted` state flag in the wizard prevents double-submission (line 84: `case 4: return !submitted`).
- **Memory leaks:** `useRef` for collapse timeout in Sidebar (line 192) uses `window.setTimeout`/`clearTimeout` correctly. The timeout is cleared on mouse re-enter. However, the timeout ref is not cleaned up on unmount — this is a negligible concern since Sidebar is mounted for the lifetime of the app layout. Not a leak in practice.
- **Type safety:** Full TypeScript coverage. `DomainFilterId` derived from `const` assertion. `StopCondition` is a union type. No `any` types in sprint code.
- **Test coverage:** 18 tests across 4 test files covering wizard navigation, step validation, domain filter rendering, stop condition configurator, progress bar variants, signal feed rendering, navigation structure, and route validation. Tests mock API layer correctly via `vi.mock`.
- **Component decomposition:** Clean separation — wizard delegates to `DomainFilterSelector` and `StopConditionConfigurator`. Progress tracking split between `InvestigationProgressBar` (composite) and `StopConditionProgress` (per-type). Signal feed split between `SignalFeedPanel` (data fetching + layout) and `SignalCard` (rendering).

---

## Automated Scans

| Pattern | Files Scanned | Matches |
|---------|--------------|---------|
| `dangerouslySetInnerHTML` | All 16 | 0 |
| `eval()` | All 16 | 0 |
| `innerHTML` / `document.write` | All 16 | 0 |
| `fetch()` / `axios.` / `XMLHttpRequest` | All 16 | 0 |
| `localStorage` / `sessionStorage` / `cookie` | All 16 | 0 |
| `console.log` / `console.error` / `console.warn` | All 16 | 0 |
| `process.env` / `REACT_APP_` / `VITE_` | All 16 | 0 |

---

## Non-Blocking Observations

1. **Sidebar timeout cleanup (LOW):** `collapseTimeoutRef` in Sidebar is not cleaned up on component unmount via `useEffect` return. Since Sidebar is a persistent layout component, this is not a practical concern, but adding cleanup would be best practice for component reuse.

2. **Signal pre-fill gap (INFO):** As noted by the engineer reviewer, `handleCreateFromSignal` navigates to `/investigation/create` without passing signal data. The `_signal` parameter is explicitly prefixed with underscore indicating intentional non-use. Acceptable for current sprint scope.

3. **`partially_supported` counting (INFO):** `StopConditionProgress` line 56 counts `partially_supported` claims toward the `supportedClaims` threshold. This is a defensible design choice (partial evidence is still evidence) but should be documented for users who may expect only fully-supported claims to count.

---

## Verdict

**APPROVED.** All 7 security checks pass. Zero critical, high, or medium findings. Code is clean, well-typed, properly authenticated, and free of injection vectors. The sprint delivers a solid investigation lifecycle UI with appropriate component decomposition and test coverage.
