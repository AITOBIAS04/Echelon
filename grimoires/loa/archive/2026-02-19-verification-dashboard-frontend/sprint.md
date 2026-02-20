# Sprint Plan: Verification Dashboard — Frontend

> Cycle: cycle-029 | PRD: `grimoires/loa/prd.md` | SDD: `grimoires/loa/sdd.md`
> Team: 1 AI engineer | Sprint cadence: continuous
> Global sprint offset: 22 (previous cycle ended at 21)

## Sprint Overview

3 sprints decomposing the frontend bottom-up — data layer + navigation first, UI components second, demo mode third.

| Sprint | Label | Key Deliverables |
|--------|-------|--------------------|
| 1 | Data Layer + Navigation Shell | Types, API functions, hooks, router, sidebar, TopActionBar, VerifyPage shell |
| 2 | UI Components | Runs list, run detail drawer, certificates list, cert detail drawer, start verification modal |
| 3 | Demo Mode + Integration | Demo store slice, DemoEngine tick loop, demo run creation, end-to-end verification |

---

## Sprint 1 — Data Layer + Navigation Shell

**Goal**: Establish the data foundation (types, API client, hooks) and wire up navigation so `/verify` renders a tabbed shell with working tab switching. No real content yet — just the skeleton.

### Tasks

#### 1.1 — Create TypeScript types for verification

Create `frontend/src/types/verification.ts` with all interfaces matching backend schemas.

**Acceptance Criteria**:
- [x] `VerificationRunStatus` type union with all 7 states
- [x] `VerificationRun` interface matching `VerificationRunResponse` schema
- [x] `VerificationRunListResponse` with `runs`, `total`, `limit`, `offset`
- [x] `VerificationRunCreateRequest` with all form fields
- [x] `ReplayScore` interface with all per-replay fields
- [x] `Certificate` interface with `replay_scores: ReplayScore[]`
- [x] `CertificateSummary` interface (list view, no replay_scores)
- [x] `CertificateListResponse` with `certificates`, `total`, `limit`, `offset`
- [x] All types exported

#### 1.2 — Create API functions for verification

Create `frontend/src/api/verification.ts` using existing `apiClient`.

**Acceptance Criteria**:
- [x] `fetchVerificationRuns(params)` → `GET /api/v1/verification/runs` with query params
- [x] `fetchVerificationRun(runId)` → `GET /api/v1/verification/runs/{runId}`
- [x] `createVerificationRun(body)` → `POST /api/v1/verification/runs`
- [x] `fetchCertificates(params)` → `GET /api/v1/verification/certificates` with sort/filter params
- [x] `fetchCertificate(certId)` → `GET /api/v1/verification/certificates/{certId}`
- [x] All functions use `apiClient` from `src/api/client.ts`
- [x] Proper TypeScript return types using types from 1.1

#### 1.3 — Create React Query hooks

Create `frontend/src/hooks/useVerificationRuns.ts` and `frontend/src/hooks/useCertificates.ts`.

**Acceptance Criteria**:
- [x] `useVerificationRuns(filters)` returns `{ runs, total, isLoading, error, createRun, isCreating }`
- [x] Conditional polling: `refetchInterval` returns 3000 when active runs exist, `false` otherwise
- [x] `staleTime: 5000` for runs
- [x] `useCertificates(filters)` returns `{ certificates, total, isLoading, error }`
- [x] `staleTime: 30000` for certificates
- [x] `useCertificateDetail(certId)` returns `{ certificate, isLoading, error }`
- [x] `createRun` uses `useMutation` and invalidates `['verificationRuns']` on success
- [x] Demo mode branching stubs (return empty data in demo mode for now — full demo wiring in Sprint 3)

**Testing**: Hooks return correct shape; polling logic is testable

#### 1.4 — Create VerifyUiContext

Create `frontend/src/contexts/VerifyUiContext.tsx` following `AgentsUiContext` pattern.

**Acceptance Criteria**:
- [x] `VerifyUiContextValue` with `activeTab: 'runs' | 'certificates'` and `setActiveTab`
- [x] `VerifyUiProvider` component with default tab `'runs'`
- [x] `useVerifyUi()` hook that throws if used outside provider
- [x] Provider added to `AppLayout` (alongside existing context providers)

#### 1.5 — Add /verify route with lazy loading

Update `frontend/src/router.tsx` to add the `/verify` route.

**Acceptance Criteria**:
- [x] `VerifyPage` loaded via `React.lazy` + `Suspense`
- [x] Route added after VRF in the children array
- [x] Wrapped in `<ErrorBoundary>`
- [x] Suspense fallback matches terminal aesthetic: `"Loading..."` in `p-6 text-terminal-text-muted`
- [x] No changes to existing routes

#### 1.6 — Add "Verify" to Sidebar

Update `frontend/src/components/layout/Sidebar.tsx`.

**Acceptance Criteria**:
- [x] New item in `NAV_ITEMS`: `{ path: '/verify', label: 'Verify', icon: ShieldCheck }`
- [x] Positioned after VRF item
- [x] `ShieldCheck` imported from `lucide-react`
- [x] Active state highlight works (cyan border-l)
- [x] No changes to existing nav items

#### 1.7 — Add Verify config to TopActionBar

Update `frontend/src/components/layout/TopActionBar.tsx`.

**Acceptance Criteria**:
- [x] New entry in `TOP_ACTIONS`: `/verify` with tab buttons + "Start Verification" action
- [x] Tab buttons: "My Runs" (List icon) and "Certificates" (Award icon)
- [x] "Start Verification" button: Plus icon, `kind: 'primary'`
- [x] Tab button rendering logic: reads `activeTab` from `VerifyUiContext`
- [x] `isVerifyPage` detection from `location.pathname`
- [x] Tab click calls `setActiveTab` from context
- [x] Action button triggers `startVerification` handler via `actionsRef`

#### 1.8 — Create VerifyPage shell

Create `frontend/src/pages/VerifyPage.tsx` with tab switching and empty content areas.

**Acceptance Criteria**:
- [x] Reads `activeTab` from `VerifyUiContext`
- [x] Registers TopActionBar actions via `useRegisterTopActionBarActions`
- [x] `startVerification` action registered (sets state to show modal — modal itself in Sprint 2)
- [x] Renders section header with ShieldCheck icon + "Verification Runs" / "Certificates" based on tab
- [x] Section header uses `section-title-accented` pattern (uppercase, tracking-wider)
- [x] Tab content area: placeholder `terminal-panel` with "Coming in Sprint 2" text
- [x] `page-enter` animation class on mount container
- [x] `max-w-7xl mx-auto p-6 space-y-6` layout matching VRFPage
- [x] Named export `VerifyPage` + default export for lazy loading

**Testing**: ~4 tests — page renders, tabs switch, correct section headers

---

## Sprint 2 — UI Components

**Goal**: Build all 5 UI components — runs list, run detail drawer, certificates list, certificate detail drawer, and start verification modal. All wired to the hooks from Sprint 1. Works with live API when backend is available.

**Depends on**: Sprint 1 (types, hooks, navigation shell)

### Tasks

#### 2.1 — RunsListView component

Create `frontend/src/components/verify/RunsListView.tsx`.

**Acceptance Criteria**:
- [x] Table with columns: Construct ID, Status, Progress, Created At, Actions
- [x] Status chips: `chip-neutral` (PENDING), `chip-info animate-pulse` (active states), `chip-success` (COMPLETED), `chip-danger` (FAILED)
- [x] Progress bar: `h-1.5 w-24` bar with `bg-echelon-cyan` fill + `font-mono text-[10px] tabular-nums` label showing `progress/total`
- [x] Progress bar hidden for PENDING and FAILED states
- [x] Filter bar: status dropdown (`<select>`) + construct_id text input (`terminal-input`)
- [x] Clear filters button when filters active
- [x] Pagination: prev/next buttons + "Showing X–Y of Z" label
- [x] Click row calls `onSelectRun(run_id)` prop
- [x] Empty state: terminal-panel with ShieldCheck icon + "No verification runs yet"
- [x] Loading state: skeleton rows or spinner
- [x] Table uses `terminal-table` styling patterns (sticky thead, hover rows)
- [x] Created At column shows relative time (e.g. "2 min ago")

**Testing**: ~4 tests — renders runs, chips correct, filters work, empty state

#### 2.2 — RunDetailDrawer component

Create `frontend/src/components/verify/RunDetailDrawer.tsx`.

**Acceptance Criteria**:
- [x] Slide-in drawer: fixed right, 420px width, z-[310], bg-terminal-overlay
- [x] Backdrop: fixed inset-0 bg-black/50 z-[300], click to close
- [x] Header: construct_id + status chip + close button (✕)
- [x] Details section: repo_url, created_at, updated_at as data-label/data-value pairs
- [x] Progress section (active runs): progress bar + "X / Y replays completed"
- [x] Error section (FAILED): chip-danger styled block with error text
- [x] Certificate link (COMPLETED): btn-cyan "View Certificate" button
- [x] "View Certificate" calls `onViewCertificate(certificate_id)` prop
- [x] Escape key closes drawer
- [x] Render null when `runId` prop is null
- [x] Uses `section-header` pattern for drawer header

**Testing**: ~3 tests — renders details, shows error for failed, shows cert link for completed

#### 2.3 — CertificatesListView component

Create `frontend/src/components/verify/CertificatesListView.tsx`.

**Acceptance Criteria**:
- [x] Table with columns: Construct ID, Composite Score, Brier Score, Replay Count, Created At
- [x] Composite Score colour-coded: `text-status-success` (>0.7), `text-status-warning` (>0.4), `text-status-danger` (≤0.4)
- [x] Brier Score colour-coded: `text-status-success` (<0.15), `text-status-warning` (<0.3), `text-status-danger` (≥0.3)
- [x] Sort toggle: Brier ascending (default) or Created At descending
- [x] Sort indicator: arrow icon on active sort column
- [x] Filter: construct_id text input
- [x] Pagination: prev/next + count label
- [x] Click row calls `onSelectCert(cert_id)` prop
- [x] All scores use `font-mono tabular-nums` for alignment
- [x] Empty state: "No certificates found"

**Testing**: ~3 tests — renders certs, sort toggles work, colour coding correct

#### 2.4 — CertDetailDrawer component

Create `frontend/src/components/verify/CertDetailDrawer.tsx`.

**Acceptance Criteria**:
- [x] Same drawer pattern as RunDetailDrawer (420px, z-[310], backdrop)
- [x] Header: construct_id + domain chip + close button
- [x] Score cards grid: 2×3 on lg, stacked on mobile
  - Precision, Recall, Reply Accuracy, Composite Score (echelon-cyan highlight), Brier Score, Replay Count
  - Each card: `bg-terminal-panel border rounded-xl p-4` with `data-label` + `text-2xl font-mono font-bold`
- [x] Methodology section: terminal-card with Version, Scoring Model, Ground Truth Source, Commit Range
- [x] Replay Scores table: all columns from `ReplayScore` type
  - Sortable by precision (descending) or latency (ascending) — local sort
  - Scrollable: `max-h-[300px] overflow-y-auto`
  - Latency formatted as `Xms`
- [x] Uses `useCertificateDetail(certId)` hook
- [x] Loading state while fetching full certificate

**Testing**: ~3 tests — renders scores, replay table sorts, methodology section present

#### 2.5 — StartVerificationModal component

Create `frontend/src/components/verify/StartVerificationModal.tsx`.

**Acceptance Criteria**:
- [x] Modal overlay: bg-black/50 z-[300], click backdrop to close
- [x] Modal container: max-w-lg, bg-terminal-overlay, rounded-xl, shadow-elevation-3
- [x] Header: section-header with "Start Verification" title + close button
- [x] Fields:
  - repo_url: `terminal-input`, required, placeholder "https://github.com/org/repo"
  - construct_id: `terminal-input`, required
  - oracle_type: `<select>` with "HTTP" / "Python" options
  - oracle_url: `terminal-input`, shown when type=HTTP, required conditionally
  - oracle_module: `terminal-input`, shown when type=Python
  - oracle_callable: `terminal-input`, shown when type=Python
  - github_token: `terminal-input type=password` with eye toggle
  - limit: `terminal-input type=number`, default 100
  - min_replays: `terminal-input type=number`, default 50
- [x] Client-side validation:
  - repo_url: non-empty, max 500 chars
  - construct_id: non-empty, max 255 chars
  - oracle_url required when type=HTTP
  - oracle_module + oracle_callable required when type=Python
  - limit: 1–1000
  - min_replays: 1–500
- [x] Invalid fields: `border-status-danger` + error text below field
- [x] Submit button: `btn-cyan` "Start Verification", disabled while submitting
- [x] Submit calls `createRun` from `useVerificationRuns` hook
- [x] On success: `demoStore.pushToast("Verification started")`, close modal
- [x] On error: `demoStore.pushToast(error.message)` with error detail
- [x] Escape key closes modal
- [x] `aria-modal="true"` on modal container

**Testing**: ~4 tests — validates required fields, conditional oracle fields, submits, handles error

#### 2.6 — Wire components into VerifyPage

Update `frontend/src/pages/VerifyPage.tsx` to replace Sprint 1 placeholders.

**Acceptance Criteria**:
- [x] Runs tab renders `<RunsListView>` with run selection state
- [x] Selected run opens `<RunDetailDrawer>`
- [x] "View Certificate" in run drawer switches to certificates tab and opens cert drawer
- [x] Certificates tab renders `<CertificatesListView>` with cert selection state
- [x] Selected cert opens `<CertDetailDrawer>`
- [x] `startVerification` action opens `<StartVerificationModal>`
- [x] Modal `onSuccess` refreshes runs list (invalidate query)
- [x] Drawer close handlers clear selection state
- [x] Tab switch clears any open drawers

**Testing**: ~4 tests — tab content renders, drawers open/close, modal flow

---

## Sprint 3 — Demo Mode + Integration

**Goal**: Full demo mode support. Mock verification data seeded on load, running mock run progresses through states, form creates mock runs. All views work without a backend.

**Depends on**: Sprint 2 (all UI components)

### Tasks

#### 3.1 — Add verification slice to demoStore

Update `frontend/src/demo/demoStore.ts` with verification state.

**Acceptance Criteria**:
- [x] `DemoVerificationRun` type added (matching SDD §5.2)
- [x] `DemoCertificate` type added with `DemoReplayScore[]`
- [x] `verificationRuns: DemoVerificationRun[]` added to `StoreState`
- [x] `certificates: DemoCertificate[]` added to `StoreState`
- [x] `verificationListeners` listener set created
- [x] `getVerificationRuns()` method
- [x] `getCertificates()` method
- [x] `addVerificationRun(run)` method — adds to front of array, emits
- [x] `updateVerificationRun(id, updater)` method — updates in place, emits
- [x] `addCertificate(cert)` method — adds to front, caps at 10
- [x] `subscribeVerification(listener)` method — returns unsubscribe function
- [x] No changes to existing slices

#### 3.2 — Add verification seed data and tick loop to DemoEngine

Update `frontend/src/demo/DemoEngine.tsx` with verification simulation.

**Acceptance Criteria**:
- [x] `seedVerification()` function:
  - Seeds 5 runs: 2 COMPLETED, 1 SCORING (progress 47/90), 1 FAILED, 1 PENDING
  - Seeds 3 certificates linked to completed runs with realistic scores
  - Each certificate has 3-5 replay scores
  - Only seeds if `demoStore.getVerificationRuns().length === 0`
- [x] `tickVerification()` function:
  - PENDING → INGESTING (set total to random 60-120)
  - INGESTING → SCORING (increment progress by 3-8, transition at 30% of total)
  - SCORING → CERTIFYING (increment progress by 2-5, transition at 90% of total)
  - CERTIFYING → COMPLETED (generate mock certificate, link to run)
- [x] `scheduleVerification()` timer: 2-3s interval (same setTimeout recursion pattern)
- [x] Timer added to `timers.current.verification`
- [x] Timer cleared on unmount
- [x] Uses seeded RNG `r` (same `mulberry32(1337)` as other loops)

**Testing**: ~3 tests — seed data appears, tick progresses runs, completed run gets certificate

#### 3.3 — Wire demo mode into hooks

Update `useVerificationRuns.ts` and `useCertificates.ts` to branch on demo mode.

**Acceptance Criteria**:
- [x] `useVerificationRuns`: when `isDemoModeEnabled()`:
  - Subscribes to `demoStore.subscribeVerification`
  - Returns demo runs filtered by status/construct_id params
  - `createRun` creates a `DemoVerificationRun` with PENDING status via `demoStore.addVerificationRun`
  - `isLoading` always false in demo mode
  - React Query disabled (`enabled: false`)
- [x] `useCertificates`: when `isDemoModeEnabled()`:
  - Subscribes to `demoStore.subscribeVerification`
  - Returns demo certificates sorted by filter params
  - React Query disabled
- [x] `useCertificateDetail`: when `isDemoModeEnabled()`:
  - Finds certificate in `demoStore.getCertificates()` by ID
  - React Query disabled
- [x] Pagination: client-side slice of demo data with correct offset/limit
- [x] Toast on demo run creation: `demoStore.pushToast("Verification started")`

**Testing**: ~3 tests — demo hooks return seeded data, filter works, create adds run

#### 3.4 — Integration verification

Full end-to-end verification with demo mode active.

**Acceptance Criteria**:
- [x] Navigate to `/verify` — runs tab shows 5 seeded runs with correct status chips
- [x] Running run (SCORING) shows animated progress bar updating every 2-3s
- [x] Click a completed run — drawer shows details + "View Certificate" button
- [x] Click "View Certificate" — switches to Certificates tab, opens cert drawer
- [x] Certificates tab shows 3 seeded certificates sorted by Brier score
- [x] Click certificate — drawer shows score cards + replay scores table
- [x] Click "Start Verification" — modal opens with form
- [x] Submit form — new PENDING run appears in list, toast shown
- [x] New run progresses through INGESTING → SCORING → CERTIFYING → COMPLETED
- [x] Completed run generates a certificate that appears in Certificates tab
- [x] Filter by status works (e.g. "COMPLETED" shows only 2 initially)
- [x] Filter by construct_id works
- [x] Pagination prev/next works with >20 items
- [x] All status chips render with correct colours and pulse animation
- [x] Page-enter animation fires on mount
- [x] Responsive: mobile stacks score cards, table scrolls horizontally

---

## Risk Mitigation

| Risk | Sprint | Mitigation |
|------|--------|------------|
| TopActionBar tab pattern is new (isVerifyTab) | 1 | Copy exact pattern from AgentsUiContext/isTab |
| Drawer z-index conflicts | 2 | Use z-[300]/z-[310] — same as VRFPage |
| Demo tick creates too many certificates | 3 | Cap at 10 in demoStore; check for existing cert before creating |
| Form validation drift from backend | 2 | Match Pydantic constraints exactly |
| Lazy loading breaks in dev | 1 | Test with both `npm run dev` and `npm run build` |

## Definition of Done

Each sprint is complete when:
1. All acceptance criteria checked
2. Tests pass
3. No linting errors
4. Code reviewed and audited
