# Cycle-016: Results Surface

**Date:** 5 March 2026
**Depends on:** Cycle-014c (investigation toolset), Cycle-015 (live collectors), Cycle-012 (sponsored theatres), Cycle-013 (agent runtime)
**Sprints:** 5
**Scope:** Full production frontend — reconcile mock/presentation layer with real backend, wire all existing views to live APIs, build new investigation toolset views, redesign navigation. React 19 + Vite 7 + Tailwind stack preserved; kree8.studio visual identity applied.

---

## Why This Cycle Exists

Every backend cycle since 010a has shipped runtime models, services, and tests — but the frontend was built as a **presentation mockup** before most backend systems existed. The audit reveals:

- **Only 2 of 13 routes are properly wired** (Verification + Theatre)
- **11 routes use hardcoded mock data** or demo stores that never call real APIs
- **Backend endpoints exist but are ignored** by the frontend (portfolio, paradox, marketplace)
- **Some frontend components have no backend at all** (OpsBoard, RLMF, VRF, Analytics/Blackbox)
- **TypeScript types don't match Pydantic schemas** (field names, types, missing fields)
- **The investigation toolset (014c) has zero frontend representation**

This cycle does two things: (1) reconcile the mock frontend with the real backend, and (2) build the new investigation views that 014c enables.

---

## Current State: Frontend–Backend Alignment Audit

### ✅ Working Correctly (keep as-is)

| Component | Frontend | Backend | Notes |
|-----------|----------|---------|-------|
| Verification | Real API calls | `verification_routes.py` | Types match, CRUD works |
| Theatre | Real API calls | `theatre_routes.py` | Create, commit, run, settle, certificate |
| API Client | `client.ts` configured | `localhost:8000` | Bearer auth, error handling |

### ❌ Mock Frontend, Real Backend Exists (wire up)

| Component | Frontend Mock | Backend Endpoint | Gap |
|-----------|-------------|-----------------|-----|
| Portfolio/FieldKit | `usePortfolio.ts` hardcoded positions | `GET /api/v1/user/positions`, `/portfolio/summary` | Frontend never calls API. Type mismatch: `unrealizedPnL` vs `unrealised_pnl_usd` |
| Marketplace | 6 hardcoded markets (robotics/logistics) | `PolymarketClient` + `MarketSyncTask` → Timeline table | Full Polymarket integration exists but is dormant. `MarketSyncTask` auto-discovers markets, creates timelines, syncs prices. Frontend uses mock data instead of querying timelines table |
| Agents | 6 fake agents in `useAgents.ts` | `GET /api/v1/agents/` (returns empty, USE_MOCKS=true) | Backend underpowered. Frontend expects lineage, generation, P&L history not in schema |
| Paradox/Breach | `demoStore` with static data | `GET /api/v1/paradoxes/active` + detail endpoints | API exists but frontend uses demo store |
| Watchlist | Demo data | `GET /api/v1/user/watchlist` | API exists, frontend ignores it |

### ❌ Mock Frontend, No Backend (decide: build, stub, or defer)

| Component | Frontend | Backend | Decision |
|-----------|----------|---------|----------|
| OpsBoard (Home) | Elaborate mock generator (380 lines) | Nothing (but real data exists in Timeline, Paradox, Agent tables once MarketSyncTask runs) | **Rebuild** as aggregation dashboard from real data |
| RLMF Page | Demo/presentation only | No RLMF API endpoints | **Redesign** to show RLMF export data that exists in theatre pipeline |
| VRF Page | Simulated Chainlink demo | No VRF integration | **Defer** — move to docs/educational; VRF is post-core |
| Analytics/Blackbox | 30+ components, all mock | No analytics endpoints | **Phase** — build from real Theatre/market data in Sprint 3 |
| Exports Console | Demo store | No export API | **Stub** — show certificate/RLMF export status from existing pipeline |

### ❌ No Frontend at All (new build)

| Component | Backend Ready? | Notes |
|-----------|---------------|-------|
| Investigation Dashboard | Services exist (014c), no API routes | Need `investigation_routes.py` + full UI |
| Evidence Envelope Viewer | `EvidenceEnvelope` service | New component |
| Claim Graph Viewer | `ClaimGraph` service | New component |
| Counter-Signal Feed | `InvestigationCounterSignalFeed` | New component |
| Signal Scanner / DeltaBrief | `SignalScanner` service | New component |
| Entity Resolver View | `EntityResolver` service | New component |
| Investigation Certificate | `InvestigationCertificate` model | Extends existing Verify page |
| Commitment Monitor / Drift | `CommitmentMonitor` service | New component |
| Convergence Map | `ConvergenceDetector` service | New component (2D grid v1) |

---

## Design Language

**Primary reference:** kree8.studio (Sprrrint) — minimal, clean, dark-mode-first SaaS aesthetic.

**Existing design tokens (preserve):**
- `terminal-bg: #030305` (deep charcoal base), `terminal-card: #10141A` (card surface)
- `glass-border: rgba(255,255,255,0.1)` (razor-thin borders)
- JetBrains Mono for data/numbers, Inter for prose
- Signal colours: action `#3B82F6`, success `#10B981`, risk `#F59E0B`, danger `#EF4444`
- Agent archetype colours: shark rose, spy purple, diplomat blue, saboteur gold, whale emerald, degen orange
- Status colours: success `#4ADE80`, warning `#FACC15`, danger `#FB7185`, paradox `#8B5CF6`, entropy `#06B6D4`

**New tokens for investigation views:**
- Provenance class badges: PUBLIC_PRIMARY `#4ADE80` (emerald), PUBLIC_SECONDARY `#3B82F6` (blue), PRIVATE_LEAK `#F59E0B` (amber), ANALYST_DERIVED `#8B5CF6` (purple), THIRD_PARTY_TOOL_OUTPUT `#6B7280` (grey)
- Claim status badges: SUPPORTED `#4ADE80`, PARTIALLY_SUPPORTED `#FACC15`, UNCONFIRMED `#6B7280`, CONTRADICTED `#FB7185`
- Routing hint badges: ALLOWED `#4ADE80`, REVIEW_REQUIRED `#F59E0B`
- Anchoring state: LOCAL_UNANCHORED `#6B7280` (grey), ANCHORED `#4ADE80` (emerald)

---

## Sprint 1: Mock Purge + Real API Wiring

Strip mock data, wire to real backend, fix TypeScript types. No new features — just make existing views truthful.

> **Pre-work dependency:** `Echelon_Butterfly_Entropy_Coherence_Review_v1.md` (in Loa context). Sprint 1 must resolve the engine coherence gaps (stability scale unification, WingFlap taxonomy extension, anchor/fork model, engine unification) before wiring frontend to live data — otherwise the frontend will display incoherent stability values and missing flap types. See Gates A–G in the design note.

### Task 1.1: TypeScript Type Alignment

**Files:**
- `frontend/src/types/` — audit and rewrite all type files to match backend Pydantic schemas
- Generate types from FastAPI OpenAPI spec where possible

Key rewrites:
- `types/portfolio.ts` → match `UserPosition`, `PortfolioSummary` from `backend/schemas/user_schemas.py`
- `types/agents.ts` → match `Agent` DB model from `backend/database/models.py`
- `types/marketplace.ts` → match `Market` from `backend/api/markets.py`
- `types/breach.ts` → match `Paradox` from `backend/schemas/paradox_schemas.py`
- New: `types/investigation.ts` — types for all investigation toolset models
- New: `types/theatre.ts` — types for `TheatreResponse`, `TheatreCertificateResponse`, `CommitmentReceiptResponse`

### Task 1.2: Portfolio Page — Wire to Real API

**Files:**
- `frontend/src/hooks/usePortfolio.ts` — replace mock with TanStack Query calling `/api/v1/user/positions` and `/api/v1/user/portfolio/summary`
- `frontend/src/pages/PortfolioPage.tsx` — update to consume real data shape
- `frontend/src/components/fieldkit/MyPositions.tsx` — update field names

Remove all `mock*` constants. Handle empty state (no positions yet).

### Task 1.3: Marketplace Page — Wire to Polymarket-Backed Timelines

**Existing infrastructure (already built, needs activation):**
- `backend/integrations/polymarket_client.py` — full Polymarket CLOB + Gamma API client. Public endpoints, no auth needed. `get_trending_markets()` returns top markets sorted by 24h volume.
- `backend/worker/tasks/market_sync.py` — `MarketSyncTask` auto-discovers Polymarket markets, creates Echelon timelines (`TL_PM_*` IDs), syncs prices from token data, generates wing flaps from trades, updates volume.
- `backend/worker/game_loop.py` — already imports and instantiates `MarketSyncTask`.

**The relationship:** Polymarket is base reality. Echelon mirrors markets as timelines, then forks them — agents act, paradox intervenes, timelines can be killed. Agents are performers in a forked reality.

**Frontend files:**
- `frontend/src/api/marketplaceapi.ts` — replace mock generator with real API calls to `/api/v1/timelines/` (not `/api/markets` — timelines ARE the Polymarket-backed markets)
- `frontend/src/hooks/useMarketplace.ts` — update hook to fetch timelines with `TL_PM_*` prefix
- `frontend/src/pages/MarketplacePage.tsx` — update to consume Timeline schema (price_yes, price_no, volume, stability, etc.)
- `frontend/src/components/marketplace/` — update components

**Backend tasks:**
- Verify `MarketSyncTask.tick()` runs on schedule (check game loop interval)
- Add `/api/v1/timelines/trending` endpoint that returns timelines sorted by volume (uses existing `MarketSyncTask.client.get_trending_markets()` under the hood)
- Auto-population: scheduled job pulls top 10–20 trending Polymarket markets every N minutes and creates/updates timelines. Nothing manual.

**Trend detection (no X API needed):**
- Primary: Polymarket's own volume/activity data via `get_trending_markets()` — free, already implemented
- Supplementary (optional, deferred): Google Trends API (free tier) for topic enrichment
- Markets auto-populate from Polymarket trending → no manual curation

### Task 1.4: Agents Page — Wire to Real API + Backend Enhancement

**Frontend files:**
- `frontend/src/hooks/useAgents.ts` — replace 6 hardcoded agents with API calls
- `frontend/src/components/agents/AgentRoster.tsx` — update for real schema

**Backend enhancement needed:**
- `backend/api/agents_routes.py` — remove `USE_MOCKS=true` default, return real agent data from DB
- Ensure agent spawn (013) populates agents table so there's data to display

Accept that agent genealogy/lineage is out of scope for now — display what exists (archetype, P&L, win rate, sanity, is_alive).

### Task 1.5: Paradox/Breach — Wire to Real API

**Files:**
- `frontend/src/pages/BreachConsolePage.tsx` — replace `useDemoBreaches()` with TanStack Query hook calling `/api/v1/paradoxes/active`
- Remove demoStore dependency for breach data

### Task 1.6: Watchlist — Wire to Real API

**Files:**
- `frontend/src/components/watchlist/` — call `/api/v1/user/watchlist` instead of mock data

### Task 1.7: Sprint 1 Tests

1. `usePortfolio.test.ts` — hook calls real endpoint, transforms response correctly
2. `useMarketplace.test.ts` — hook calls real endpoint, categories match backend enum
3. `useAgents.test.ts` — hook calls real endpoint, handles empty list
4. `BreachConsolePage.test.tsx` — renders real paradox data, no demoStore usage
5. Type alignment regression: snapshot test all type files against backend OpenAPI spec

---

## Sprint 2: Investigation Dashboard + Certificate Explorer

The highest-value new views from 014c.

### Task 2.1: Investigation API Routes (Backend)

**New file:** `backend/api/investigation_routes.py`

```
GET  /api/v1/investigations/                       — list active investigations
GET  /api/v1/investigations/{id}                   — investigation detail (toolset state)
GET  /api/v1/investigations/{id}/evidence          — evidence envelope manifest
GET  /api/v1/investigations/{id}/claims            — claim graph with status summary
GET  /api/v1/investigations/{id}/counter-signals   — counter-signal feed
GET  /api/v1/investigations/{id}/drift             — drift events
GET  /api/v1/investigations/{id}/certificate       — investigation certificate
GET  /api/v1/investigations/{id}/scanner           — latest DeltaBrief
POST /api/v1/investigations/                       — create investigation
POST /api/v1/investigations/{id}/evidence          — submit evidence item
POST /api/v1/investigations/{id}/claims            — register claim
```

**New file:** `backend/schemas/investigation.py` — request/response models
**Wire into:** `backend/main.py`

### Task 2.2: Investigation Dashboard Page

**Files:**
- `frontend/src/pages/InvestigationPage.tsx`
- `frontend/src/router.tsx` (add `/investigation` route)
- `frontend/src/hooks/useInvestigation.ts` — TanStack Query hooks for all investigation endpoints

Tabbed layout: Overview | Evidence | Claims | Signals | Drift

### Task 2.3: Evidence Envelope Viewer

**Files:**
- `frontend/src/components/investigation/EvidenceEnvelopePanel.tsx`
- `frontend/src/components/investigation/EvidenceItemCard.tsx`
- `frontend/src/components/investigation/ProvenanceBadge.tsx`

Chronological evidence items with provenance class badges, content hashes, redaction indicators. Envelope hash at top. Provenance summary stacked bar.

### Task 2.4: Claim Graph Viewer

**Files:**
- `frontend/src/components/investigation/ClaimGraphPanel.tsx`
- `frontend/src/components/investigation/ClaimNodeCard.tsx`
- `frontend/src/components/investigation/ClaimStatusBadge.tsx`

Vertical card list (not network graph for v1). Claim text, type badge, status badge, confidence ring, evidence refs, counter-signal links, independence groups, Merkle root hash.

### Task 2.5: Investigation Certificate Explorer

**Files:**
- `frontend/src/components/investigation/InvestigationCertificateView.tsx`
- `frontend/src/components/investigation/CertificateFieldGroup.tsx`
- `frontend/src/components/investigation/RoutingHintBadge.tsx`

Full 30+ field display grouped into: header (routing hint, inquiry question, dates), evidence section, claims section, counter-signals section, drift section, anchoring section, hashes section, stop condition section.

### Task 2.6: Counter-Signal Feed + DeltaBrief + Drift Panels

**Files:**
- `frontend/src/components/investigation/CounterSignalPanel.tsx`
- `frontend/src/components/investigation/DeltaBriefPanel.tsx`
- `frontend/src/components/investigation/DriftEventsPanel.tsx`
- `frontend/src/components/investigation/EntityProfilePanel.tsx`

Counter-signals: 11 classes, material flags, detection method, summary counts. DeltaBrief: domain filter chips, anomaly cards, access tier display. Drift: type badge, impact assessment, original→new diff. Entity: profile fields, source queries, provenance.

### Task 2.7: Sprint 2 Tests

1. Investigation API routes: 8 endpoint tests (list, detail, evidence, claims, counter-signals, drift, certificate, scanner)
2. `InvestigationPage.test.tsx` — renders with mock data, tab navigation
3. `EvidenceEnvelopePanel.test.tsx` — provenance badges, redaction indicators
4. `ClaimGraphPanel.test.tsx` — status badges match status values
5. `InvestigationCertificateView.test.tsx` — all field groups render, routing hint correct
6. `CounterSignalPanel.test.tsx` — summary counts, material flag display
7. `DeltaBriefPanel.test.tsx` — domain filter chips, access tier enforcement display

---

## Sprint 3: OpsBoard Rebuild + Analytics Foundation + RLMF Redesign

Rebuild the mock-heavy pages with real data sources.

### Task 3.1: OpsBoard — Rebuild as Aggregation Dashboard

**Files:**
- `frontend/src/api/opsBoard.ts` — delete mock generator, build real aggregation from existing endpoints
- `frontend/src/pages/HomePage.tsx` — redesign

The OpsBoard should aggregate from data that already exists:
- **Active Theatres** → `GET /api/v1/theatres` filtered by state
- **Active Paradoxes** → `GET /api/v1/paradoxes/active`
- **Active Investigations** → `GET /api/v1/investigations/`
- **Recent Wing Flaps** → `GET /api/v1/butterfly/wing-flaps/recent`
- **Timeline Health Summary** → `GET /api/v1/butterfly/timelines/health`

No new backend endpoints needed — aggregate existing ones.

Layout: 4 summary cards at top (active theatres, active investigations, paradox count, agent count) + activity feed + quick-access panels.

### Task 3.2: Analytics Page — Build from Real Data

**Files:**
- `frontend/src/pages/BlackboxPage.tsx` — redesign
- `frontend/src/components/blackbox/` — replace mock components with real data views

Analytics v1 (minimal viable):
- **Theatre history** — resolved theatres with scores (from `/api/v1/theatres` + `/api/v1/certificates`)
- **Agent leaderboard** — from `/api/v1/agents/` sorted by P&L
- **OSINT evidence timeline** — from `/api/v1/osint/signals`
- **Market prices** — from existing LMSR market data

Remove all mock chart data. Accept that some visualisations (heatmap, correlation matrix, depth chart) need backend endpoints that don't exist yet — show "Coming Soon" placeholders for those.

### Task 3.3: RLMF Page — Redesign as Export Viewer

**Files:**
- `frontend/src/pages/RLMFPage.tsx` — complete rewrite

The current page is a demo mockup of "what RLMF training looks like." The real RLMF pipeline already exists in the backend — it exports market-derived probability distributions from resolved Theatres. Redesign to show:

- **RLMF export status** — which Theatres have produced RLMF export data
- **Export manifest** — format, record count, schema version
- **Sample records** — preview of exported probability distributions
- **Download/access** — link to export files

This is a viewer for existing pipeline output, not a training interface.

### Task 3.4: VRF Page — Convert to Documentation/Roadmap

**Files:**
- `frontend/src/pages/VRFPage.tsx` — replace simulation with info page

VRF (Chainlink Verifiable Random Function) is not implemented and is post-core scope. Replace the simulated demo with:
- Explanation of VRF's role in Echelon (perturbation injection per System Bible §VII)
- Roadmap status (not yet implemented)
- Link to System Bible §VII

### Task 3.5: Sprint 3 Tests

1. `HomePage.test.tsx` — renders aggregation cards from real data, no mock generator
2. `BlackboxPage.test.tsx` — renders available data, shows placeholders for missing
3. `RLMFPage.test.tsx` — renders export viewer with real export data
4. Zero remaining mock data imports across Sprint 3 components

---

## Sprint 4: Investigation Lifecycle Console + Navigation Redesign

### Task 4.1: Investigation Creation Wizard

**Files:**
- `frontend/src/components/investigation/CreateInvestigationWizard.tsx`
- `frontend/src/components/investigation/DomainFilterSelector.tsx`
- `frontend/src/components/investigation/StopConditionConfigurator.tsx`

Multi-step wizard:
1. Inquiry question (text input)
2. Template selection (investigation-capable templates)
3. Domain filters (9 categories with source group preview, access tier display)
4. Stop condition (outcome/evidence threshold/sponsor-defined) with parameter config
5. Review & commit (summary, commitment hash preview, immutability warning)

Stop condition immutability clearly communicated — once committed, no changes.

### Task 4.2: Investigation Progress Tracker

**Files:**
- `frontend/src/components/investigation/InvestigationProgressBar.tsx`
- `frontend/src/components/investigation/StopConditionProgress.tsx`

Live progress: stop condition progress bar, evidence count, claim status distribution, counter-signal count, corroboration indicator.

### Task 4.3: Navigation Redesign

**Files:**
- `frontend/src/components/layout/AppLayout.tsx` (modify)
- `frontend/src/components/layout/Sidebar.tsx` (modify or create)
- `frontend/src/router.tsx` (modify)

New navigation structure:
```
Dashboard (was OpsBoard/Home)
Marketplace
Investigations
  └─ Active Investigations
  └─ Signal Feed
  └─ Create Investigation
Theatres (list + detail)
Analytics (was Blackbox)
Agents
Portfolio
Certificates
  └─ Calibration Certificates
  └─ Investigation Certificates
RLMF Exports
```

Remove: `/vrf` from main nav (move to info page), `/agents/export` (fold into RLMF), legacy redirects cleaned up.

### Task 4.4: Signal Feed Migration

**Files:**
- `frontend/src/components/investigation/SignalFeedPanel.tsx`
- `frontend/src/components/investigation/SignalCard.tsx`

Migrate inquiry console's Signal Feed into main app. Source-badged signal cards with click-through to "Create Investigation from Signal" (pre-fills wizard).

### Task 4.5: Sprint 4 Tests

1. `CreateInvestigationWizard.test.tsx` — wizard navigation, immutability warning
2. `InvestigationProgressBar.test.tsx` — progress for each stop condition type
3. Navigation test — all routes accessible, no dead links
4. `SignalFeedPanel.test.tsx` — signals render with correct source badges

---

## Sprint 5: Convergence Map + Agent Analytics + WebSocket + Polish

### Task 5.1: Convergence Map

**Files:**
- `frontend/src/components/convergence/ConvergenceMap.tsx`
- `frontend/src/components/convergence/ConvergenceCell.tsx`

2D grid showing 1° × 1° cells with convergence scores (grey → amber → red). Click for detail: event types, sources, matched theatres. No 3D globe — functional 2D first.

### Task 5.2: Agent Performance Analytics

**Files:**
- `frontend/src/components/agents/AgentPerformanceDashboard.tsx`
- `frontend/src/components/agents/ArchetypeComparison.tsx`
- `frontend/src/components/agents/TradeHistory.tsx`
- `frontend/src/components/agents/GenomeViewer.tsx`

Deep analytics on agent detail page: trade history, archetype comparison radar chart, P&L sparklines, genome viewer (read-only YAML display), inquiry affinity.

### Task 5.3: WebSocket Integration

**Files:**
- `frontend/src/hooks/useWebSocket.ts`
- `frontend/src/hooks/useRealtimeInvestigation.ts`

Wire TanStack Query cache invalidation to WebSocket events:
- Wing flap → invalidate timeline health
- Price update → invalidate market prices
- Paradox spawn → invalidate paradox list
- Investigation events → invalidate investigation detail
- Position update → invalidate user positions

Pattern: WS event → identify query keys → `queryClient.invalidateQueries()` → auto-refetch.

### Task 5.4: Responsive Layout + Loading States + Polish

Polish pass across all views:
- Responsive breakpoints (stack on narrow viewports)
- Loading skeletons (Tailwind animation tokens)
- Empty states for all panels
- Error states with retry buttons
- Consistent `terminal-*` token usage
- Keyboard navigation for tab panels
- Remove any remaining mock data imports (zero tolerance)

### Task 5.5: Sprint 5 Tests + Final Audit

1. `ConvergenceMap.test.tsx` — cells render, click expands
2. `AgentPerformanceDashboard.test.tsx` — trade history renders
3. `useWebSocket.test.ts` — WS events trigger correct invalidation
4. **Final mock purge audit** — grep entire frontend for `mock`, `MOCK`, `demo`, `hardcoded`, `fake` — zero remaining in production code paths
5. **E2E test:** Create investigation → view evidence → inspect claims → check certificate → verify in certificate explorer

---

## Gate Rule

≥1009 passed (post-014c baseline). All new frontend tests pass (Vitest). All new backend API route tests pass (pytest). Zero mock data in production code paths. Post-016 expected: ≥1060 passed (50+ new tests across frontend and backend).

---

## What This Unlocks

- **Echelon's thesis becomes visible** — markets, evidence, claims, certificates, agents, all rendered from real data
- **Mock presentation layer retired** — every view shows actual backend state
- **Investigation workflow is end-to-end** — create inquiry → collect evidence → structure claims → monitor counter-signals → resolve → inspect certificate
- **Foundation for demos** — the Results Surface is what you show to Soju, investors, early adopters
- **Inquiry console retired** — separate Cloudflare app superseded

---

## Out of Scope

- 3D globe / Spatial Intelligence "God mode" (deferred — cost and complexity)
- Google Photorealistic 3D Tiles integration
- Real Chainlink VRF integration (post-core; page becomes informational)
- Real-time collaborative investigation (multi-user editing)
- Mobile native app (responsive web only)
- Chain anchoring UI beyond status display
- Agent breeding/genealogy UI (genome is read-only display)
- $ECHELON token/wallet integration
- Social trading / leaderboard features
- Paid OSINT source activation from UI
- Analytics features requiring new backend endpoints (heatmap, correlation matrix, depth chart) — show placeholders, build backend in future cycle
