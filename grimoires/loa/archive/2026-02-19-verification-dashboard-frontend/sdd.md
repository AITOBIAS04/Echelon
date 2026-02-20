# SDD: Verification Dashboard — Frontend

> Cycle: cycle-029 | PRD: `grimoires/loa/prd.md`
> Status: Draft | Date: 2026-02-19

## 1. Executive Summary

Frontend verification dashboard for the Echelon platform. Adds a `/verify` route with two tabbed views (My Runs, Certificates), a start-verification form, and full demo mode support. Built entirely with existing patterns — React Query hooks, Axios client, demoStore pub-sub, DemoEngine timers, terminal design tokens.

No new dependencies. No new design tokens. No new state management patterns.

## 2. System Architecture

```
┌──────────────────────────────────────────────────┐
│                    AppLayout                      │
│ ┌──────────┐ ┌─────────────────────────────────┐ │
│ │ Sidebar  │ │  TopActionBar (/verify config)   │ │
│ │ + Verify │ │  [My Runs] [Certificates] [+New] │ │
│ │   item   │ ├─────────────────────────────────┤ │
│ │          │ │  <Outlet /> → VerifyPage         │ │
│ │          │ │    ├─ RunsListView (default tab) │ │
│ │          │ │    │    └─ RunDetailDrawer        │ │
│ │          │ │    ├─ CertificatesListView        │ │
│ │          │ │    │    └─ CertDetailDrawer       │ │
│ │          │ │    └─ StartVerificationModal      │ │
│ └──────────┘ └─────────────────────────────────┘ │
└──────────────────────────────────────────────────┘

Data Flow:
  VerifyPage → useVerificationRuns() → apiClient (live) / demoStore (demo)
  VerifyPage → useCertificates()     → apiClient (live) / demoStore (demo)
  DemoEngine → tickVerification()    → demoStore.updateVerificationRun()
```

## 3. Technology Stack

All existing — no additions:

| Layer | Technology | Justification |
|-------|-----------|---------------|
| UI Framework | React 19 + TypeScript | Existing |
| Routing | React Router v7 | Existing pattern in `router.tsx` |
| Data Fetching | TanStack React Query v5 | Existing — `useBreaches`, `useExports` |
| HTTP Client | Axios (`src/api/client.ts`) | Existing — has Bearer interceptor |
| State (demo) | demoStore pub-sub | Existing — `demoStore.ts` |
| Styling | Tailwind CSS v3 + terminal tokens | Existing — `index.css` |
| Icons | Lucide React | Existing |

## 4. Component Design

### 4.1 File Structure

```
frontend/src/
├── pages/
│   └── VerifyPage.tsx              # Top-level page (tab state, layout)
├── components/
│   └── verify/
│       ├── RunsListView.tsx        # Runs table with filters, pagination
│       ├── RunDetailDrawer.tsx     # Slide-in drawer for run details
│       ├── CertificatesListView.tsx # Certificates table with sort, pagination
│       ├── CertDetailDrawer.tsx    # Slide-in drawer for certificate details
│       └── StartVerificationModal.tsx # Form modal for creating runs
├── hooks/
│   ├── useVerificationRuns.ts      # React Query hook for runs API
│   └── useCertificates.ts         # React Query hook for certificates API
├── api/
│   └── verification.ts            # Axios API functions
└── types/
    └── verification.ts            # TypeScript interfaces
```

### 4.2 VerifyPage.tsx

Top-level page component managing tab state and layout.

```
State:
  activeTab: 'runs' | 'certificates'   — URL search param ?tab=certificates
  showNewRunModal: boolean

Behaviour:
  - Reads ?tab= from URL to set initial tab (default: 'runs')
  - Registers TopActionBar actions: tab toggles + "Start Verification" button
  - Renders active tab view + modal when open
  - page-enter animation on mount (existing CSS class)
```

Registers with TopActionBar via `useRegisterTopActionBarActions`:
- Tab buttons: "My Runs" / "Certificates" (same pattern as Agents tab buttons)
- Action button: "Start Verification" → opens modal

### 4.3 RunsListView.tsx

Table view of the user's verification runs.

```
Props: { onSelectRun: (runId: string) => void }

Data: useVerificationRuns(filters) — React Query hook
  - Filters: status (dropdown), construct_id (text input)
  - Pagination: limit=20, offset managed by prev/next buttons

Columns:
  Construct ID   | font-mono text-echelon-cyan
  Status         | chip-neutral / chip-info / chip-success / chip-danger
  Progress       | progress bar (bg-echelon-cyan/20, fill bg-echelon-cyan)
  Created        | font-mono text-terminal-text-muted, relative time
  Actions        | "Details" button → onSelectRun(id)

Active run states (INGESTING, INVOKING, SCORING, CERTIFYING):
  - chip-info with "animate-pulse" class
  - Progress bar visible

Empty state:
  terminal-panel with centered text + icon
  "No verification runs yet. Start one below."
```

### 4.4 RunDetailDrawer.tsx

Slide-in drawer showing full run details — same pattern as VRFPage audit drawer.

```
Props: { runId: string | null; onClose: () => void }

Data: useVerificationRuns() single-run query (or from cached list data)

Sections:
  1. Header: Construct ID + Status chip
  2. Details grid: repo_url, created_at, updated_at
  3. Progress section (if active): progress bar + "X / Y replays"
  4. Error block (if FAILED): chip-danger background with error text
  5. Certificate link (if COMPLETED): btn-cyan "View Certificate" → switches to cert tab

Layout: Fixed right-side overlay (same as VRFPage drawer)
  - 420px width, z-[310]
  - bg-terminal-overlay, border-terminal-border
  - Escape key to close
  - Click backdrop to close
```

### 4.5 CertificatesListView.tsx

Public certificate browser with sort and filter.

```
Props: { onSelectCert: (certId: string) => void }

Data: useCertificates(filters) — React Query hook
  - Filters: construct_id (text input)
  - Sort: 'brier_asc' (default) | 'created_desc'
  - Pagination: limit=20, offset

Columns:
  Construct ID      | font-mono text-echelon-cyan
  Composite Score   | font-mono tabular-nums, colour-coded (green >0.7, amber >0.4, red ≤0.4)
  Brier Score       | font-mono tabular-nums, colour-coded (green <0.15, amber <0.3, red ≥0.3)
  Replay Count      | font-mono
  Created           | font-mono text-terminal-text-muted

Sort toggle: column header buttons (ascending arrow for Brier, descending for Created)
```

### 4.6 CertDetailDrawer.tsx

Certificate detail drawer with score cards and replay scores table.

```
Props: { certId: string | null; onClose: () => void }

Data: useCertificates() single-cert query (includes replay_scores)

Sections:
  1. Header: Construct ID + Domain chip
  2. Score cards grid (2×3 on lg, 1×6 on mobile):
     - Precision      | metric-block pattern
     - Recall         | metric-block pattern
     - Reply Accuracy | metric-block pattern
     - Composite      | metric-block pattern (highlighted, echelon-cyan)
     - Brier Score    | metric-block pattern (highlighted)
     - Replay Count   | metric-block pattern
  3. Methodology info: terminal-card with data-label/data-value rows
     - Version, Scoring Model, Ground Truth Source, Commit Range
  4. Replay Scores table: terminal-table with all per-replay columns
     - Sortable by precision or latency (local sort)
     - Scrollable (max-h-[300px] overflow-y-auto)

Layout: Same drawer pattern as RunDetailDrawer
```

### 4.7 StartVerificationModal.tsx

Modal form for creating a new verification run.

```
Props: { open: boolean; onClose: () => void; onSuccess: () => void }

Form state: React useState (no form library needed — 8 simple fields)

Fields:
  repo_url        | terminal-input, required, placeholder "https://github.com/..."
  construct_id    | terminal-input, required
  oracle_type     | <select> "HTTP" / "Python"
  oracle_url      | terminal-input, shown when type=HTTP, required conditionally
  oracle_module   | terminal-input, shown when type=Python
  oracle_callable | terminal-input, shown when type=Python
  github_token    | terminal-input type=password with visibility toggle
  limit           | terminal-input type=number, default 100
  min_replays     | terminal-input type=number, default 50

Submit: btn-cyan "Start Verification"
  - Client-side validation matching Pydantic rules
  - useMutation → POST /api/v1/verification/runs
  - On success: demoStore.pushToast("Verification started"), onSuccess(), onClose()
  - On error: demoStore.pushToast(error.message) with danger styling

Layout: Fixed overlay modal (similar to VRF drawer but centered)
  - max-w-lg, bg-terminal-overlay, rounded-xl
  - Escape to close, backdrop click to close
```

## 5. Data Architecture

### 5.1 TypeScript Types (`types/verification.ts`)

```typescript
// Matches backend VerificationRunStatus enum
type VerificationRunStatus =
  | 'PENDING' | 'INGESTING' | 'INVOKING'
  | 'SCORING' | 'CERTIFYING' | 'COMPLETED' | 'FAILED';

interface VerificationRun {
  run_id: string;
  status: VerificationRunStatus;
  progress: number;
  total: number;
  construct_id: string;
  repo_url: string;
  error: string | null;
  certificate_id: string | null;
  created_at: string;   // ISO datetime
  updated_at: string;
}

interface VerificationRunListResponse {
  runs: VerificationRun[];
  total: number;
  limit: number;
  offset: number;
}

interface VerificationRunCreateRequest {
  repo_url: string;
  construct_id: string;
  oracle_type: 'http' | 'python';
  oracle_url?: string;
  oracle_module?: string;
  oracle_callable?: string;
  github_token?: string;
  limit: number;
  min_replays: number;
}

interface ReplayScore {
  id: string;
  ground_truth_id: string;
  precision: number;
  recall: number;
  reply_accuracy: number;
  claims_total: number;
  claims_supported: number;
  changes_total: number;
  changes_surfaced: number;
  scoring_model: string;
  scoring_latency_ms: number;
  scored_at: string;
}

interface Certificate {
  id: string;
  construct_id: string;
  domain: string;
  replay_count: number;
  precision: number;
  recall: number;
  reply_accuracy: number;
  composite_score: number;
  brier: number;
  sample_size: number;
  ground_truth_source: string;
  methodology_version: string;
  scoring_model: string;
  created_at: string;
  replay_scores: ReplayScore[];
}

interface CertificateSummary {
  id: string;
  construct_id: string;
  domain: string;
  replay_count: number;
  composite_score: number;
  brier: number;
  created_at: string;
}

interface CertificateListResponse {
  certificates: CertificateSummary[];
  total: number;
  limit: number;
  offset: number;
}
```

### 5.2 Demo Store Slice

New slice added to `demoStore.ts`:

```typescript
// New types
type DemoVerificationRun = {
  run_id: string;
  status: VerificationRunStatus;
  progress: number;
  total: number;
  construct_id: string;
  repo_url: string;
  error: string | null;
  certificate_id: string | null;
  created_at: number;
  updated_at: number;
};

type DemoCertificate = {
  id: string;
  construct_id: string;
  domain: string;
  replay_count: number;
  precision: number;
  recall: number;
  reply_accuracy: number;
  composite_score: number;
  brier: number;
  sample_size: number;
  ground_truth_source: string;
  methodology_version: string;
  scoring_model: string;
  created_at: number;
  replay_scores: DemoReplayScore[];
};

type DemoReplayScore = {
  id: string;
  ground_truth_id: string;
  precision: number;
  recall: number;
  reply_accuracy: number;
  claims_total: number;
  claims_supported: number;
  changes_total: number;
  changes_surfaced: number;
  scoring_model: string;
  scoring_latency_ms: number;
  scored_at: number;
};

// Added to StoreState:
verificationRuns: DemoVerificationRun[];
certificates: DemoCertificate[];

// New listener set:
verificationListeners: Set<Listener>;

// New demoStore methods:
getVerificationRuns(): DemoVerificationRun[]
getCertificates(): DemoCertificate[]
addVerificationRun(run: DemoVerificationRun): void
updateVerificationRun(id: string, updater: (r) => r): void
subscribeVerification(listener: Listener): () => void
```

## 6. API Integration

### 6.1 API Functions (`api/verification.ts`)

All functions use `apiClient` from `src/api/client.ts` (inherits Bearer token interceptor).

```typescript
// Runs (authenticated)
fetchVerificationRuns(params: {
  status?: string;
  construct_id?: string;
  limit?: number;
  offset?: number;
}): Promise<VerificationRunListResponse>
// GET /api/v1/verification/runs?status=X&construct_id=Y&limit=20&offset=0

fetchVerificationRun(runId: string): Promise<VerificationRun>
// GET /api/v1/verification/runs/{runId}

createVerificationRun(body: VerificationRunCreateRequest): Promise<VerificationRun>
// POST /api/v1/verification/runs

// Certificates (public — no auth needed)
fetchCertificates(params: {
  construct_id?: string;
  sort?: 'brier_asc' | 'created_desc';
  limit?: number;
  offset?: number;
}): Promise<CertificateListResponse>
// GET /api/v1/verification/certificates?sort=brier_asc&limit=20&offset=0

fetchCertificate(certId: string): Promise<Certificate>
// GET /api/v1/verification/certificates/{certId}
```

### 6.2 React Query Hooks

#### `useVerificationRuns.ts`

```typescript
function useVerificationRuns(filters: RunFilters) {
  const isDemo = isDemoModeEnabled();

  // Live mode: React Query with polling
  const query = useQuery({
    queryKey: ['verificationRuns', filters],
    queryFn: () => fetchVerificationRuns(filters),
    enabled: !isDemo,
    staleTime: 5000,
    refetchInterval: (query) => {
      // Poll every 3s if any run is in an active state
      const runs = query.state.data?.runs ?? [];
      const hasActive = runs.some(r =>
        !['COMPLETED', 'FAILED'].includes(r.status)
      );
      return hasActive ? 3000 : false;
    },
  });

  // Demo mode: subscribe to demoStore
  const [demoRuns, setDemoRuns] = useState<DemoVerificationRun[]>([]);
  useEffect(() => {
    if (!isDemo) return;
    setDemoRuns(demoStore.getVerificationRuns());
    return demoStore.subscribeVerification(() => {
      setDemoRuns(demoStore.getVerificationRuns());
    });
  }, [isDemo]);

  // Create mutation
  const createMutation = useMutation({
    mutationFn: isDemo ? demoCreateRun : createVerificationRun,
    onSuccess: () => queryClient.invalidateQueries(['verificationRuns']),
  });

  return {
    runs: isDemo ? filterDemoRuns(demoRuns, filters) : (query.data?.runs ?? []),
    total: isDemo ? demoRuns.length : (query.data?.total ?? 0),
    isLoading: isDemo ? false : query.isLoading,
    error: isDemo ? null : query.error,
    createRun: createMutation.mutateAsync,
    isCreating: createMutation.isPending,
  };
}
```

#### `useCertificates.ts`

```typescript
function useCertificates(filters: CertFilters) {
  const isDemo = isDemoModeEnabled();

  const listQuery = useQuery({
    queryKey: ['certificates', filters],
    queryFn: () => fetchCertificates(filters),
    enabled: !isDemo,
    staleTime: 30000,  // Certificates change infrequently
  });

  // Demo mode: from demoStore
  const [demoCerts, setDemoCerts] = useState<DemoCertificate[]>([]);
  useEffect(() => {
    if (!isDemo) return;
    setDemoCerts(demoStore.getCertificates());
    return demoStore.subscribeVerification(() => {
      setDemoCerts(demoStore.getCertificates());
    });
  }, [isDemo]);

  return {
    certificates: isDemo ? sortDemoCerts(demoCerts, filters) : (listQuery.data?.certificates ?? []),
    total: isDemo ? demoCerts.length : (listQuery.data?.total ?? 0),
    isLoading: isDemo ? false : listQuery.isLoading,
    error: isDemo ? null : listQuery.error,
  };
}

function useCertificateDetail(certId: string | null) {
  const isDemo = isDemoModeEnabled();

  const query = useQuery({
    queryKey: ['certificate', certId],
    queryFn: () => fetchCertificate(certId!),
    enabled: !isDemo && !!certId,
  });

  // Demo mode: find in demoStore
  const demoCert = isDemo && certId
    ? demoStore.getCertificates().find(c => c.id === certId)
    : undefined;

  return {
    certificate: isDemo ? demoCert : query.data,
    isLoading: isDemo ? false : query.isLoading,
    error: isDemo ? null : query.error,
  };
}
```

### 6.3 Conditional Polling Strategy

Active runs poll every 3 seconds via React Query's `refetchInterval` callback. Polling stops automatically when all runs reach terminal status (COMPLETED or FAILED). In demo mode, the DemoEngine timer handles progress updates — no API polling occurs.

## 7. Demo Mode Integration

### 7.1 Seed Data

Added to DemoEngine's `useEffect` on mount:

**Runs** (4 seeded):
| run_id | construct_id | status | progress/total |
|--------|-------------|--------|---------------|
| `vr_demo_1` | `osint-oracle-v3` | COMPLETED | 85/85 |
| `vr_demo_2` | `market-sentinel` | COMPLETED | 120/120 |
| `vr_demo_3` | `risk-auditor-v2` | SCORING | 47/90 |
| `vr_demo_4` | `signal-relay` | FAILED | 12/75 |
| `vr_demo_5` | `data-validator` | PENDING | 0/0 |

**Certificates** (3 seeded, linked to completed runs):
| cert_id | construct_id | composite | brier | replays |
|---------|-------------|-----------|-------|---------|
| `vc_demo_1` | `osint-oracle-v3` | 0.847 | 0.098 | 85 |
| `vc_demo_2` | `market-sentinel` | 0.721 | 0.183 | 120 |
| `vc_demo_3` | `risk-auditor-v1` | 0.634 | 0.241 | 62 |

Each certificate includes 3-5 seeded replay scores with realistic values.

### 7.2 Tick Loop

New `scheduleVerification` timer in DemoEngine (2-3s interval):

```
tickVerification():
  for each run where status is not terminal:
    if PENDING: transition to INGESTING, set total to random 60-120
    if INGESTING: increment progress by 3-8, transition to SCORING at 30%
    if SCORING: increment progress by 2-5, transition to CERTIFYING at 90%
    if CERTIFYING: transition to COMPLETED, generate mock certificate
```

### 7.3 Demo Run Creation

When user submits the form in demo mode:
1. Create a new `DemoVerificationRun` with status=PENDING
2. Add to demoStore
3. The tick loop picks it up and progresses it through states
4. On COMPLETED, a mock certificate is generated and added to certificates list

## 8. Router & Navigation Integration

### 8.1 Router Changes (`router.tsx`)

Add lazy-loaded route:

```typescript
import { lazy, Suspense } from 'react';
const VerifyPage = lazy(() => import('./pages/VerifyPage').then(m => ({ default: m.VerifyPage })));

// In children array, after VRF:
{
  path: 'verify',
  element: (
    <ErrorBoundary>
      <Suspense fallback={<div className="p-6 text-terminal-text-muted">Loading...</div>}>
        <VerifyPage />
      </Suspense>
    </ErrorBoundary>
  ),
},
```

### 8.2 Sidebar Changes (`Sidebar.tsx`)

Add to `NAV_ITEMS` array after VRF:

```typescript
{ path: '/verify', label: 'Verify', icon: ShieldCheck },
```

Uses `ShieldCheck` from lucide-react (distinct from `Shield` used by VRF).

### 8.3 TopActionBar Changes (`TopActionBar.tsx`)

Add to `TOP_ACTIONS` config:

```typescript
'/verify': {
  name: 'Verify',
  buttons: [
    { label: 'My Runs', icon: List, isVerifyTab: true, verifyTabValue: 'runs' },
    { label: 'Certificates', icon: Award, isVerifyTab: true, verifyTabValue: 'certificates' },
    { label: 'Start Verification', icon: Plus, kind: 'primary', action: 'startVerification' },
  ],
},
```

Tab handling follows the same pattern as Agents (`isTab` + `tabValue`) and RLMF (`isRlmfViewTab`). A new `VerifyUiContext` provides `activeTab` and `setActiveTab` — matching the `AgentsUiContext` pattern.

### 8.4 VerifyUiContext (`contexts/VerifyUiContext.tsx`)

Minimal context for tab state shared between TopActionBar and VerifyPage:

```typescript
interface VerifyUiContextValue {
  activeTab: 'runs' | 'certificates';
  setActiveTab: (tab: 'runs' | 'certificates') => void;
}
```

Provider wraps children in AppLayout (alongside existing context providers). Initial tab read from URL `?tab=` search param.

## 9. Design Specification

### 9.1 Page Layout

```
┌─ max-w-7xl mx-auto p-6 space-y-6 ──────────────┐
│                                                   │
│  [Section Header: Verification Runs / Certificates]
│  section-title-accented + icon                    │
│                                                   │
│  ┌─ Filter Bar: terminal-panel rounded-lg ──────┐ │
│  │ [Status ▼] [construct_id ___] [Clear]        │ │
│  └──────────────────────────────────────────────┘ │
│                                                   │
│  ┌─ Table: terminal-table pattern ──────────────┐ │
│  │ thead: sticky, bg-terminal-bg, uppercase      │ │
│  │ tbody: hover:bg-terminal-bg/50                │ │
│  │ Status chips: chip-neutral/info/success/danger│ │
│  │ Progress: inline bar with % label             │ │
│  └──────────────────────────────────────────────┘ │
│                                                   │
│  ┌─ Pagination: flex justify-between ───────────┐ │
│  │ "Showing X–Y of Z"    [← Prev] [Next →]     │ │
│  └──────────────────────────────────────────────┘ │
│                                                   │
└───────────────────────────────────────────────────┘
```

### 9.2 Status Chip Mapping

| Status | CSS Class | Extra |
|--------|-----------|-------|
| PENDING | `chip chip-neutral` | — |
| INGESTING | `chip chip-info animate-pulse` | — |
| INVOKING | `chip chip-info animate-pulse` | — |
| SCORING | `chip chip-info animate-pulse` | — |
| CERTIFYING | `chip chip-info animate-pulse` | — |
| COMPLETED | `chip chip-success` | — |
| FAILED | `chip chip-danger` | — |

### 9.3 Progress Bar

Inline within the runs table, using existing colour tokens:

```html
<div class="h-1.5 w-24 bg-terminal-border/30 rounded-full overflow-hidden">
  <div class="h-full bg-echelon-cyan rounded-full transition-all duration-500"
       style="width: {progress/total * 100}%" />
</div>
<span class="font-mono text-[10px] text-terminal-text-muted tabular-nums">
  {progress}/{total}
</span>
```

### 9.4 Score Cards (Certificate Detail)

Using the `metric-block` pattern from existing pages:

```html
<div class="bg-terminal-panel border border-terminal-border rounded-xl p-4">
  <div class="text-xs text-terminal-text-muted uppercase tracking-wider font-semibold mb-2">
    Composite Score
  </div>
  <div class="text-2xl font-mono font-bold text-echelon-cyan">0.847</div>
  <div class="text-xs text-terminal-text-muted mt-1">Weighted average</div>
</div>
```

### 9.5 Modal Styling

```
Fixed overlay: bg-black/50 z-[300]
Modal: max-w-lg mx-auto mt-[10vh]
  bg-terminal-overlay border border-terminal-border rounded-xl
  shadow-elevation-3

Header: section-header pattern (px-4 py-3 bg-terminal-bg/50 border-b)
Body: p-4 space-y-4
  Inputs: terminal-input class
  Labels: data-label class
  Submit: btn-cyan w-full
Footer: px-4 py-3 border-t border-terminal-border
  Cancel: text button
```

## 10. Error Handling

| Scenario | Behaviour |
|----------|-----------|
| API returns error | `demoStore.pushToast(message)` — uses existing toast system |
| API unreachable | Show inline "Backend unavailable" message in terminal-panel; fall back to demo data if demo mode |
| 401 Unauthorized | Existing interceptor clears tokens; runs tab shows "Sign in to view runs" |
| 404 on run/cert detail | Drawer shows "Not found" message, auto-closes after 3s |
| Form validation failure | Red border on invalid field + inline error text below |
| Network timeout | React Query retries (3x default); error state shown after final failure |

## 11. Accessibility

| Element | A11y Implementation |
|---------|-------------------|
| Tab buttons (TopActionBar) | `role="tab"`, `aria-selected`, `aria-controls` |
| Status chips | Includes text (not icon-only), screen reader reads status |
| Progress bar | `role="progressbar"`, `aria-valuenow`, `aria-valuemin=0`, `aria-valuemax={total}` |
| Drawer | `role="dialog"`, `aria-labelledby`, focus trap on open, return focus on close |
| Modal | `role="dialog"`, `aria-modal="true"`, focus trap |
| Table | `<table>` with semantic `<thead>/<tbody>`, sortable columns have `aria-sort` |
| Filter dropdowns | Native `<select>` elements (inherently accessible) |
| Icons | Decorative icons have `aria-hidden="true"`, meaningful icons have `aria-label` |
| Keyboard | Escape closes drawers/modals, Tab navigates, Enter activates |

## 12. Performance

| Technique | Implementation |
|-----------|---------------|
| Lazy loading | `React.lazy` + `Suspense` for VerifyPage in router |
| Conditional polling | `refetchInterval` callback — only polls when active runs exist |
| Query caching | React Query `staleTime: 5000` for runs, `30000` for certificates |
| Pagination | Server-side limit/offset — never load all runs/certs at once |
| Memoization | `useMemo` for filtered/sorted lists in table components |
| Demo engine | `setTimeout` recursion (not `setInterval`) — no stacking on slow renders |

## 13. Testing Strategy

Tests will use the existing testing patterns in the project.

| Test Type | Scope | Count |
|-----------|-------|-------|
| Component | VerifyPage renders with tabs, switches between views | ~4 |
| Component | RunsListView renders runs, shows correct chips | ~4 |
| Component | CertificatesListView renders, sorts by Brier | ~3 |
| Component | StartVerificationModal validates form, submits | ~4 |
| Hook | useVerificationRuns returns data, handles polling | ~3 |
| Hook | useCertificates returns sorted data | ~2 |
| Integration | Demo mode: seed data appears, tick updates progress | ~3 |
| Integration | Demo mode: form creates mock run that progresses | ~2 |

~25 tests total.

## 14. Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Tab state in TopActionBar requires new context | Medium | Follow exact AgentsUiContext pattern — minimal code |
| Polling many active runs causes network load | Low | Only polls when non-terminal runs exist; demo mode has no API calls |
| Drawer z-index conflicts with TopActionBar | Low | Use z-[300]/z-[310] — same as VRFPage drawer |
| Demo tick creates too many certificates | Low | Cap certificates at 10 in demo store; completed runs check for existing cert |
| Form validation drift from backend schemas | Medium | Match Pydantic constraints exactly in client-side validation |

## 15. Out of Scope

- Cancel/retry runs (future cycle)
- WebSocket updates (polling sufficient)
- Certificate comparison view
- Export certificate as PDF/image
- Admin view
- New CSS design tokens or colour palette
