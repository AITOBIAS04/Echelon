# Sprint Plan — Cycle-016: Results Surface

**Cycle:** cycle-016
**Date:** 5 March 2026
**PRD:** grimoires/loa/prd.md
**SDD:** grimoires/loa/sdd.md
**Sprints:** 6 (Sprint-0 complete, Sprints 1–5 ahead)
**Baseline:** ≥1009 passed (post-014c), 15 skipped, 13 pre-existing collection errors

---

## Sprint 0: Engine Coherence Lock ✓ COMPLETE

Pre-work dependency from `Echelon_Butterfly_Entropy_Coherence_Review_v1.md`. All 7 acceptance gates (A–G) pass. No 0–100 scale leaks remain in live runtime paths.

### Task 0.1: Model Layer + Migration ✓

**Files modified:**
- `backend/database/models.py` — WingFlapType (10 new), FlapDirection enum, 0.5 defaults, anchor/fork fields
- `backend/alembic/versions/c016_engine_coherence.py` — NEW: dialect-safe migration

**Acceptance Criteria:**
- [x] 17 WingFlapType values in models.py
- [x] FlapDirection enum: STABILISE, DESTABILISE, NEUTRAL
- [x] Timeline defaults: stability=0.5, surface_tension=0.5, osint_alignment=0.5
- [x] Anchor/fork fields: is_anchor, anchor_timeline_id, fork_divergence, last_sync_at
- [x] Migration normalises 0–100 → 0–1, migrates ANCHOR → STABILISE

### Task 0.2: Shared SYSTEM Entity ✓

**File created:** `backend/worker/tasks/_system_entity.py`

**Acceptance Criteria:**
- [x] `ensure_system_entities()` returns `(User, Agent)` tuple
- [x] Creates SYSTEM user + agent if absent
- [x] Used by entropy.py, paradox.py, market_sync.py

### Task 0.3: Pattern A Decay Fix ✓

**Files modified:**
- `backend/worker/tasks/paradox.py` — writes `decay_multiplier` only, DETONATION flap type, 0–1 thresholds
- `backend/worker/tasks/entropy.py` — reads `decay_multiplier`, anchor skip, 0–1 constants, FlapDirection

**Acceptance Criteria:**
- [x] Paradox: writes `decay_multiplier` only, does NOT mutate `decay_rate_per_hour`
- [x] Entropy: `effective_rate = base_rate × decay_multiplier` (no hardcoded 2.0)
- [x] Entropy: skips anchor timelines (`Timeline.is_anchor == False` filter)
- [x] Both use FlapDirection enum values
- [x] Both use shared SYSTEM entity helper

### Task 0.4: Market Sync + Game Loop ✓

**Files modified:**
- `backend/worker/tasks/market_sync.py` — MIRROR_TRADE, is_anchor=True, 0–1 scale, MAX_ACTIVE_MARKETS=10
- `backend/worker/game_loop.py` — evidence (120s) and divergence (60s) cadence stubs

**Acceptance Criteria:**
- [x] New Polymarket timelines get `is_anchor=True`
- [x] MIRROR_TRADE flap type for real trades
- [x] `stability_delta` capped at 0.05 (0–1 scale)
- [x] `MAX_ACTIVE_MARKETS = 10` call-budget guardrail
- [x] `last_sync_at` updated on every sync (trade and no-trade)
- [x] Evidence and divergence stubs in game loop

### Task 0.5: Agent Tick — Full 0–1 Conversion ✓

**File modified:** `backend/worker/tasks/agent_tick.py`

**Acceptance Criteria:**
- [x] `_shark_strategy`: osint > 0.5, delta `size / 1_000_000`, clamp `max(0.0, min(1.0, ...))`
- [x] `_spy_strategy`: delta `uniform(0.01, 0.03)`, clamp `min(1.0, ...)`
- [x] `_diplomat_strategy`: delta `uniform(0.03, 0.08)`, clamp `min(1.0, ...)`
- [x] `_saboteur_strategy`: delta `-uniform(0.05, 0.12)`, clamp `max(0.0, ...)`
- [x] `_whale_strategy`: osint > 0.5, delta `size / 1_000_000`, clamp `max(0.0, min(1.0, ...))`
- [x] All 5 strategies use `FlapDirection.STABILISE.value` / `.DESTABILISE.value`

### Task 0.6: Genesis + Kalshi — Full 0–1 Conversion ✓

**Files modified:**
- `backend/worker/tasks/genesis.py` — 0–1 templates, `is_active=True`, FORK_SPAWN, SYSTEM agent, valid WingFlap
- `backend/worker/tasks/kalshi_sync.py` — 0–1 stability, FlapDirection enum, `max(0.0, min(1.0, ...))`

**Acceptance Criteria:**
- [x] Genesis templates: base_stability 0.45–0.82 (not 45–82)
- [x] Genesis Timeline: surface_tension, osint_alignment, gravity_score all 0–1
- [x] Genesis: `decay_rate_per_hour=0.01`, `is_active=True` (not `status="ACTIVE"`)
- [x] Genesis WingFlap: FORK_SPAWN type, `id`, `timestamp`, `agent_id="SYSTEM"`
- [x] Kalshi: stability delta capped at 0.05, clamp `max(0.0, min(1.0, ...))`
- [x] Kalshi: `FlapDirection.STABILISE.value` / `.DESTABILISE.value`

### Task 0.7: Engine + Schema Layer ✓

**Files modified:**
- `backend/engines/butterfly.py` — enum sync, FlapDirection, auto-direction, `compute_fork_divergence()`
- `backend/engines/entropy.py` — LogicGapReading dataclass, backwards-compat `tick()`
- `backend/schemas/butterfly_schemas.py` — extended enums, anchor/fork fields, STABILISE/NEUTRAL
- `backend/mechanics/butterfly_engine.py` — `_as_percent()` API boundary

**Acceptance Criteria:**
- [x] engines/ and models.py WingFlapType enums identical
- [x] FlapDirection enum in engines/butterfly.py
- [x] `record_flap()` auto-derives direction from impact sign
- [x] `compute_fork_divergence()` returns `abs(anchor.stability - fork.stability)`
- [x] LogicGapReading: `isinstance(reading, str)` backwards compat
- [x] `_as_percent()` converts 0–1 → 0–100 at API boundary

### Task 0.8: Coherence Tests ✓

**File created:** `backend/engines/tests/test_coherence_016.py` — 22 tests

**Acceptance Criteria:**
- [x] 22 tests covering Gates A–G
- [x] All pass (213 passed across engines + schemas)
- [x] Zero new failures (8 pre-existing async heartbeat failures unchanged)

### Sprint 0 Summary

- **22 new tests** (test_coherence_016.py)
- **16 files modified/created**
- **213 passed** (engines + schemas); all new/targeted tests pass. 8 known unrelated async heartbeat failures remain (pre-existing, no pytest-asyncio installed)
- **Zero 0–100 leaks** in live runtime paths (verified by grep)
- **Zero bare string directions** in worker/tasks/ and admin_routes (verified by grep)

---

## Sprint 1: Mock Purge + Real API Wiring ✓ COMPLETE

Strip mock data, wire to real backend, fix TypeScript types. No new features -- just make existing views truthful. 33 files changed (25 modified, 8 new). 19 tests pass. Zero TSC errors.

### Task 1.1: TypeScript Type Alignment ✓

**Files:**
- `frontend/src/types/portfolio.ts` → match `UserPosition`, `PortfolioSummary` from `backend/schemas/user_schemas.py`
- `frontend/src/types/agents.ts` → match `Agent` DB model from `backend/database/models.py`
- `frontend/src/types/marketplace.ts` → match Timeline from `backend/schemas/butterfly_schemas.py`
- `frontend/src/types/breach.ts` → match `Paradox` from `backend/schemas/paradox_schemas.py`
- New: `frontend/src/types/investigation.ts` — investigation toolset response types
- New: `frontend/src/types/theatre.ts` — `TheatreResponse`, `TheatreCertificateResponse`, `CommitmentReceiptResponse`

**Acceptance Criteria:**
- [x] All type files match backend Pydantic schemas (field names, types)
- [x] camelCase ↔ snake_case transforms documented in API client
- [x] No `any` types in investigation or theatre types

### Task 1.2: Portfolio Page — Wire to Real API ✓

**Files:**
- `frontend/src/hooks/usePortfolio.ts` — TanStack Query calling `/api/v1/user/positions` + `/api/v1/user/portfolio/summary`
- `frontend/src/pages/PortfolioPage.tsx` — consume real data shape
- `frontend/src/components/fieldkit/MyPositions.tsx` — update field names

**Acceptance Criteria:**
- [x] All `mock*` constants removed
- [x] Empty state displayed when no positions
- [x] Field mapping: `unrealizedPnL` → `unrealised_pnl_usd`

### Task 1.3: Marketplace Page — Wire to Polymarket-Backed Timelines ✓

**Backend:**
- Verify `MarketSyncTask.tick()` runs on 10s cadence
- Add `GET /api/v1/timelines/trending` — timelines sorted by volume

**Frontend:**
- `frontend/src/api/marketplaceapi.ts` — replace mock generator with `/api/v1/timelines/`
- `frontend/src/hooks/useMarketplace.ts` — fetch timelines with `TL_PM_*` prefix
- `frontend/src/pages/MarketplacePage.tsx` — consume Timeline schema

**Acceptance Criteria:**
- [x] Marketplace renders from real Polymarket-backed timelines
- [x] No hardcoded market data
- [x] Trending endpoint returns timelines sorted by volume

### Task 1.4: Agents Page — Wire to Real API ✓

**Frontend:** `frontend/src/hooks/useAgents.ts` — replace 6 hardcoded agents with API calls
**Backend:** `backend/api/agents_routes.py` — remove `USE_MOCKS=true` default

**Acceptance Criteria:**
- [x] Real agent data from DB displayed
- [x] Empty state when no agents
- [x] Archetype, P&L, win rate, sanity, is_alive fields rendered

### Task 1.5: Paradox/Breach — Wire to Real API ✓

**Files:** `frontend/src/pages/BreachConsolePage.tsx` — replace `useDemoBreaches()` with TanStack Query calling `/api/v1/paradoxes/active`

**Acceptance Criteria:**
- [x] No demoStore dependency
- [x] Real paradox data rendered

### Task 1.6: Watchlist — Wire to Real API ✓

**Files:** `frontend/src/components/watchlist/` — call `/api/v1/user/watchlist`

**Acceptance Criteria:**
- [x] No mock watchlist data

### Task 1.7: Sprint 1 Tests ✓

5 tests:
1. `usePortfolio.test.ts` — hook calls real endpoint, transforms response correctly
2. `useMarketplace.test.ts` — hook calls real endpoint, categories match backend
3. `useAgents.test.ts` — hook calls real endpoint, handles empty list
4. `BreachConsolePage.test.tsx` — renders real paradox data, no demoStore usage
5. Type alignment regression: snapshot test all type files against backend OpenAPI spec

**Acceptance Criteria:**
- [x] All 5 tests pass
- [x] Zero mock data imports in Sprint 1 components

---

## Sprint 2: Investigation Dashboard + Certificate Explorer ✓ COMPLETE

### Task 2.1: Investigation API Routes (Backend) ✓

**New files:**
- `backend/api/investigation_routes.py` — 11 REST endpoints
- `backend/schemas/investigation.py` — Pydantic request/response models
- Wire into `backend/main.py`

8 endpoint tests:
1. `test_list_investigations` — returns list
2. `test_get_investigation_detail` — returns toolset state
3. `test_get_evidence` — returns envelope manifest
4. `test_get_claims` — returns claim graph with status summary
5. `test_get_counter_signals` — returns counter-signal feed
6. `test_get_drift` — returns drift events
7. `test_get_certificate` — returns investigation certificate
8. `test_create_investigation` — creates and returns investigation

**Acceptance Criteria:**
- [x] All 11 endpoints return correct response schemas
- [x] All 8 tests pass
- [x] Routes delegate to existing `backend/investigation/` services

### Task 2.2: Investigation Dashboard Page ✓

**Files:**
- `frontend/src/pages/InvestigationPage.tsx`
- `frontend/src/router.tsx` — add `/investigation` route
- `frontend/src/hooks/useInvestigation.ts` — TanStack Query hooks

Tabbed layout: Overview | Evidence | Claims | Signals | Drift

**Acceptance Criteria:**
- [x] Page renders with real data from investigation endpoints
- [x] Tab navigation between all 5 tabs
- [x] Loading and empty states for each tab

### Task 2.3: Evidence Envelope Viewer ✓

**Files:**
- `frontend/src/components/investigation/EvidenceEnvelopePanel.tsx`
- `frontend/src/components/investigation/EvidenceItemCard.tsx`
- `frontend/src/components/investigation/ProvenanceBadge.tsx`

**Acceptance Criteria:**
- [x] Chronological evidence items with provenance class badges
- [x] Content hashes displayed (truncated)
- [x] Redaction indicators where applicable
- [x] Envelope hash at top of panel
- [x] Provenance summary stacked bar

### Task 2.4: Claim Graph Viewer ✓

**Files:**
- `frontend/src/components/investigation/ClaimGraphPanel.tsx`
- `frontend/src/components/investigation/ClaimNodeCard.tsx`
- `frontend/src/components/investigation/ClaimStatusBadge.tsx`

**Acceptance Criteria:**
- [x] Vertical card list layout
- [x] Claim text, type badge, status badge, confidence ring
- [x] Evidence refs, counter-signal links, independence groups
- [x] Merkle root hash displayed

### Task 2.5: Investigation Certificate Explorer ✓

**Files:**
- `frontend/src/components/investigation/InvestigationCertificateView.tsx`
- `frontend/src/components/investigation/CertificateFieldGroup.tsx`
- `frontend/src/components/investigation/RoutingHintBadge.tsx`

**Acceptance Criteria:**
- [x] All 30+ fields displayed, grouped by section (header, evidence, claims, counter-signals, drift, anchoring, hashes, stop condition)
- [x] Routing hint badge (ALLOWED / REVIEW_REQUIRED) with correct colours
- [x] Anchoring state badge

### Task 2.6: Counter-Signal + DeltaBrief + Drift + Entity Panels ✓

**Files:**
- `frontend/src/components/investigation/CounterSignalPanel.tsx`
- `frontend/src/components/investigation/DeltaBriefPanel.tsx`
- `frontend/src/components/investigation/DriftEventsPanel.tsx`
- `frontend/src/components/investigation/EntityProfilePanel.tsx`

2 tests:
1. `CounterSignalPanel.test.tsx` — summary counts, material flag display
2. `DeltaBriefPanel.test.tsx` — domain filter chips, access tier display

**Acceptance Criteria:**
- [x] Counter-signals: 11 classes, material flags, detection method, summary counts
- [x] DeltaBrief: domain filter chips, anomaly cards, access tier display
- [x] Drift: type badge, impact assessment, original→new diff
- [x] Entity: profile fields, source queries, provenance

### Task 2.7: Sprint 2 Integration Tests ✓

4 tests:
1. `InvestigationPage.test.tsx` — renders with mock data, tab navigation
2. `EvidenceEnvelopePanel.test.tsx` — provenance badges, redaction indicators
3. `ClaimGraphPanel.test.tsx` — status badges match status values
4. `InvestigationCertificateView.test.tsx` — all field groups render, routing hint correct

**Acceptance Criteria:**
- [x] All 14 Sprint 2 tests pass

---

## Sprint 3: OpsBoard Rebuild + Analytics + RLMF Redesign

### Task 3.1: OpsBoard — Rebuild as Aggregation Dashboard

**Files:**
- `frontend/src/api/opsBoard.ts` — delete mock generator, build real aggregation
- `frontend/src/pages/HomePage.tsx` — redesign

Sources: active theatres, paradoxes, investigations, agents, recent wing flaps, timeline health — all from existing endpoints.

Layout: 4 summary cards + activity feed + quick-access panels.

**Acceptance Criteria:**
- [x] Zero mock generator code
- [x] 4 summary cards render from real endpoints
- [x] Activity feed shows recent wing flaps

### Task 3.2: Analytics Page — Build from Real Data

**Files:**
- `frontend/src/pages/BlackboxPage.tsx` — redesign
- `frontend/src/components/blackbox/` — replace mock components

Analytics v1: theatre history, agent leaderboard, OSINT timeline, market prices. "Coming Soon" placeholders for heatmap/correlation/depth chart.

**Acceptance Criteria:**
- [x] Real data rendered for available analytics
- [x] Honest "Coming Soon" for unbuilt features
- [x] Zero mock chart data

### Task 3.3: RLMF Page — Redesign as Export Viewer

**Files:** `frontend/src/pages/RLMFPage.tsx` — complete rewrite

Show: RLMF export status per Theatre, manifest, sample records, download link.

**Acceptance Criteria:**
- [x] Viewer for real pipeline output
- [x] No demo/presentation mockup

### Task 3.4: VRF Page — Convert to Documentation/Roadmap

**Files:** `frontend/src/pages/VRFPage.tsx`

Replace simulation with: explanation of VRF's role, roadmap status, link to System Bible §VII.

**Acceptance Criteria:**
- [x] No simulated demo
- [x] Informational content only

### Task 3.5: Sprint 3 Tests

4 tests:
1. `HomePage.test.tsx` — renders aggregation cards from real data
2. `BlackboxPage.test.tsx` — renders available data, shows placeholders
3. `RLMFPage.test.tsx` — renders export viewer
4. Mock purge audit — zero mock imports in Sprint 3 components

**Acceptance Criteria:**
- [x] All 4 tests pass

---

## Sprint 4: Investigation Lifecycle Console + Navigation Redesign ✓ COMPLETE

### Task 4.1: Investigation Creation Wizard ✓

**Files:**
- `frontend/src/components/investigation/CreateInvestigationWizard.tsx`
- `frontend/src/components/investigation/DomainFilterSelector.tsx`
- `frontend/src/components/investigation/StopConditionConfigurator.tsx`

5-step wizard: inquiry question → template → domain filters (9 categories) → stop condition → review & commit.

**Acceptance Criteria:**
- [x] Wizard navigation (next/back/cancel)
- [x] Domain filter selector shows 9 categories with source group preview
- [x] Stop condition configurator supports 3 types
- [x] Immutability warning on commit step
- [x] POST to `/api/v1/investigations/` on submit

### Task 4.2: Investigation Progress Tracker ✓

**Files:**
- `frontend/src/components/investigation/InvestigationProgressBar.tsx`
- `frontend/src/components/investigation/StopConditionProgress.tsx`

**Acceptance Criteria:**
- [x] Progress bar for each stop condition type
- [x] Evidence count, claim status distribution, counter-signal count
- [x] Corroboration indicator

### Task 4.3: Navigation Redesign ✓

**Files:**
- `frontend/src/components/layout/AppLayout.tsx`
- `frontend/src/components/layout/Sidebar.tsx`
- `frontend/src/router.tsx`

New structure: Dashboard, Marketplace, Investigations (with sub-routes), Theatres, Analytics, Agents, Portfolio, Certificates, RLMF Exports.

**Acceptance Criteria:**
- [x] All routes accessible
- [x] No dead links
- [x] `/vrf` removed from main nav
- [x] Investigation sub-routes (active, signal feed, create)

### Task 4.4: Signal Feed Migration ✓

**Files:**
- `frontend/src/components/investigation/SignalFeedPanel.tsx`
- `frontend/src/components/investigation/SignalCard.tsx`

Source-badged signal cards with click-through to "Create Investigation from Signal."

**Acceptance Criteria:**
- [x] Signals render with correct source badges
- [x] Click-through pre-fills creation wizard

### Task 4.5: Sprint 4 Tests ✓

4 tests:
1. `CreateInvestigationWizard.test.tsx` — wizard navigation, immutability warning
2. `InvestigationProgressBar.test.tsx` — progress for each stop condition type
3. Navigation test — all routes accessible, no dead links
4. `SignalFeedPanel.test.tsx` — signals render with source badges

**Acceptance Criteria:**
- [x] All 4 tests pass

---

## Sprint 5: Convergence Map + Agent Analytics + WebSocket + Polish ✓ COMPLETE

### Task 5.1: Convergence Map ✓

**Files:**
- `frontend/src/components/convergence/ConvergenceMap.tsx`
- `frontend/src/components/convergence/ConvergenceCell.tsx`
- `frontend/src/pages/ConvergencePage.tsx`
- `frontend/src/router.tsx` (added /convergence route)
- `frontend/src/components/layout/Sidebar.tsx` (added Convergence nav)

2D grid: 1° × 1° cells, grey → amber → red. Click for detail.

**Acceptance Criteria:**
- [x] Grid renders with correct colour gradient
- [x] Click expands to show event types, sources, matched theatres

### Task 5.2: Agent Performance Analytics ✓

**Files:**
- `frontend/src/components/agents/AgentPerformanceDashboard.tsx`
- `frontend/src/components/agents/ArchetypeComparison.tsx`
- `frontend/src/components/agents/TradeHistory.tsx`
- `frontend/src/components/agents/GenomeViewer.tsx`
- `frontend/src/components/agents/AgentDetail.tsx` (replaced placeholder)

**Acceptance Criteria:**
- [x] Trade history renders
- [x] Archetype comparison normalised bar charts
- [x] Genome viewer (read-only YAML display)

### Task 5.3: WebSocket Integration ✓

**Files:**
- `frontend/src/hooks/useWebSocket.ts`
- `frontend/src/hooks/useRealtimeInvestigation.ts`
- `frontend/src/components/layout/AppLayout.tsx`

Pattern: WS event → normalise case → identify query keys → `queryClient.invalidateQueries()` → auto-refetch.

Events: WING_FLAP, PARADOX_SPAWN, PARADOX_MOVED, DETONATION, RIPPLE, POSITION_UPDATE, ALERT, INVESTIGATION_EVENT.

**Acceptance Criteria:**
- [x] WS events trigger correct query invalidation
- [x] No full-page reloads

### Task 5.4: Responsive Layout + Loading States + Polish ✓

**Acceptance Criteria:**
- [x] Responsive breakpoints (stack on narrow viewports)
- [x] Loading skeletons on all data panels
- [x] Empty states for all panels
- [x] Error states with retry buttons
- [x] Consistent `terminal-*` token usage
- [x] Keyboard navigation for tab panels

### Task 5.5: Final Mock Purge Audit + E2E Test ✓

5 tests:
1. `ConvergenceMap.test.tsx` — cells render, click expands
2. `AgentPerformanceDashboard.test.tsx` — trade history renders
3. `useRealtimeInvestigation.test.ts` — WS events trigger correct invalidation
4. **Final mock purge audit** — grep for `mock`, `MOCK`, `demo`, `hardcoded`, `fake` — zero in production paths
5. **E2E test** — create investigation → view evidence → inspect claims → check certificate

**Acceptance Criteria:**
- [x] All 5 tests pass
- [x] Zero mock data in production code paths

---

## Test Summary

| Sprint | New Tests | Cumulative |
|--------|-----------|------------|
| 0 ✓ | 22 | 22 |
| 1 | 5 | 27 |
| 2 | 14 | 41 |
| 3 | 4 | 45 |
| 4 | 4 | 49 |
| 5 | 5 | 54 |

**Post-016 expected:** ≥1060 passed (1009 baseline + ~54 new — allowing for some overlap/consolidation).
