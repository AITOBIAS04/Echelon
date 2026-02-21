# PRD: Verification Dashboard — Frontend

> Cycle: cycle-029 | Status: Draft
> Source: User request + cycle-028 backend (echelon-verify API)

## 1. Problem Statement

Cycle-028 shipped 5 backend API endpoints for verification runs and calibration certificates (`/api/v1/verification/*`), but there is no frontend UI to interact with them. Users must use raw API calls to start verification runs, check status, or browse certificates. The existing frontend demo at echelon-v2.pages.dev has no verification section.

## 2. Goals

| # | Goal | Success Metric |
|---|------|----------------|
| G1 | Users can view verification run status with live progress | Run list renders with status chips and progress bars |
| G2 | Users can start new verification runs from the UI | Form submits to POST /runs and run appears in list |
| G3 | Users can browse and inspect calibration certificates | Certificate list with sortable Brier scores, detail view with replay scores |
| G4 | Dashboard matches existing terminal aesthetic | Same colour palette, typography, component patterns as existing pages |
| G5 | Works in demo mode with mock data | Demo engine provides simulated verification data when demo=1 |

## 3. User Personas

### Construct Builder
Builds oracle constructs and needs to verify their calibration. Starts verification runs, monitors progress, checks certificate scores. Primary user of the "Start Verification" form and run status views.

### Observer / Analyst
Browses the public certificate leaderboard to compare construct quality. Doesn't need auth — just views certificates sorted by Brier score. Uses the certificate list and detail views.

## 4. Functional Requirements

### FR-1: Verification Page (New Sidebar Item)

- New top-level sidebar item: **"Verify"** with Shield/CheckCircle icon
- Route: `/verify`
- Two tabs/views within the page:
  1. **My Runs** — authenticated user's verification runs
  2. **Certificates** — public certificate browser

### FR-2: Runs List View (`/verify` default tab)

- Table or card list showing user's verification runs
- Columns: Construct ID, Status (chip), Progress (bar), Created At, Actions
- Status chips using existing design tokens:
  - PENDING → `chip-neutral`
  - INGESTING/INVOKING/SCORING/CERTIFYING → `chip-info` with animated pulse
  - COMPLETED → `chip-success`
  - FAILED → `chip-danger`
- Progress bar showing `progress / total` during active runs
- Click row → expand or navigate to run detail
- Filter by status (dropdown)
- Filter by construct_id (text input)
- Pagination: limit/offset with prev/next controls
- Empty state: "No verification runs yet. Start one below."

### FR-3: Run Detail View

- Shows full run details: construct_id, repo_url, status, progress, error (if failed)
- If COMPLETED: links to the generated certificate
- If FAILED: shows error message in a `chip-danger` block
- Progress timeline showing state transitions (PENDING → INGESTING → SCORING → COMPLETED)

### FR-4: Start Verification Form

- Inline form or modal to create a new verification run
- Fields:
  - **Repo URL** (required) — text input
  - **Construct ID** (required) — text input
  - **Oracle Type** — dropdown: "HTTP" or "Python"
  - **Oracle URL** (shown when type=HTTP) — text input
  - **Oracle Module + Callable** (shown when type=Python) — two text inputs
  - **GitHub Token** (optional) — password input with visibility toggle
  - **Limit** — number input, default 100
  - **Min Replays** — number input, default 50
- Submit button: `btn-cyan` "Start Verification"
- On success: show toast, add run to list with PENDING status
- On error: show error toast with API message
- Client-side validation matching Pydantic schema rules

### FR-5: Certificate List View (`/verify` Certificates tab)

- Public (no auth required for API calls)
- Table showing certificates: Construct ID, Composite Score, Brier Score, Replay Count, Created At
- Sortable by Brier score (ascending = best first) or Created At (descending = newest first)
- Filter by construct_id
- Pagination
- Click row → certificate detail

### FR-6: Certificate Detail View

- Full certificate display:
  - Header: Construct ID, Domain, Created At
  - Score cards: Precision, Recall, Reply Accuracy, Composite Score, Brier Score
  - Methodology info: Version, Scoring Model, Ground Truth Source, Commit Range
- Replay Scores table:
  - Columns: Ground Truth ID, Precision, Recall, Reply Accuracy, Claims (supported/total), Changes (surfaced/total), Latency
  - Sortable by precision or latency

### FR-7: Demo Mode Integration

- When demo mode is active (`VITE_DEMO_MODE=true` or `?demo=1`):
  - Mock 4-6 verification runs in various states (2 completed, 1 running, 1 failed, 1 pending)
  - Mock 3-4 certificates with realistic scores
  - Running mock run updates progress on a 2-3s interval
  - "Start Verification" form creates a mock run that progresses through states
- Extend `demoStore.ts` with a `verification` slice
- Add verification tick loop to `DemoEngine.tsx`

## 5. Non-Functional Requirements

| # | Requirement |
|---|-------------|
| NFR-1 | **Design consistency**: Must use existing terminal design tokens — `terminal-panel`, `terminal-card`, `terminal-table`, `chip-*`, `btn-*`, `metric-block`, `status-pill` classes. No new colour palette. |
| NFR-2 | **Typography**: Follow existing hierarchy — `section-title-accented` for section headers, `data-label` + `data-value` for metrics, `font-mono tabular-nums` for scores |
| NFR-3 | **Responsive**: Mobile-first responsive grid. Cards stack on mobile (`grid-cols-1`), 2-col on `sm:`, 3-col on `lg:` |
| NFR-4 | **Data fetching**: Use Axios client (`src/api/client.ts`) with React Query for caching + auto-refetch on active runs |
| NFR-5 | **Auto-refresh**: Active runs (non-terminal status) should poll every 3-5 seconds |
| NFR-6 | **Error handling**: API errors shown as toast notifications, not crashes. Graceful fallback when backend is unavailable |
| NFR-7 | **Accessibility**: Lucide icons with aria-labels, keyboard-navigable tables, focus-visible ring on interactive elements |
| NFR-8 | **Performance**: Lazy-load the verification page via React.lazy + Suspense in router |

## 6. Out of Scope

- Cancel/retry verification runs (future cycle)
- Real-time WebSocket updates for run progress (polling is sufficient)
- Certificate comparison view (side-by-side)
- Export certificate as PDF/image
- Admin view of all users' runs
- Deployment/infrastructure changes

## 7. API Surface (from cycle-028)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/v1/verification/runs` | JWT | Create verification run |
| GET | `/api/v1/verification/runs/{run_id}` | JWT | Get run status |
| GET | `/api/v1/verification/runs` | JWT | List user's runs (paginated) |
| GET | `/api/v1/verification/certificates/{cert_id}` | Public | Get certificate + replay scores |
| GET | `/api/v1/verification/certificates` | Public | List certificates (paginated, sortable) |

## 8. Design References

The dashboard must match the existing Echelon terminal aesthetic:
- **Colour palette**: Dark terminal background (`terminal-bg`), teal/cyan accents (`echelon-cyan`), green for success, amber for warnings, rose for errors
- **Components**: `terminal-panel`, `terminal-card`, `terminal-table`, `chip-*`, `btn-cyan`, `metric-block`
- **Typography**: Inter (sans), JetBrains Mono (mono/data), uppercase tracking-wider section headers
- **Animations**: `page-enter` fade+slideUp, `hover-lift` on cards
- **Reference pages**: VRFPage (audit-grade dashboard), RLMFPage (live data feeds)
- **Use `/frontend-design` skill** during implementation for design quality

## 9. Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| API unavailable in dev | Blocks development | Demo mode provides full mock data |
| Auth token management | Runs require JWT | Reuse existing `apiClient` interceptor that adds Bearer token |
| Progress polling load | Many active runs = many requests | Poll only non-terminal runs; stop polling on COMPLETED/FAILED |
| Design drift | New page looks different | Use existing CSS classes exclusively; no new colour tokens |
