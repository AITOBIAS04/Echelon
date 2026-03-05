# PRD — Cycle-016: Results Surface

**Cycle:** cycle-016
**Date:** 5 March 2026
**Predecessor:** cycle-014c (Investigation Toolset), cycle-015 (Live Collectors), cycle-013 (Agent Runtime), cycle-012 (Sponsored Theatres), cycle-010a (LMSR)
**Sprints:** 6 total (0–5); Sprint-0 complete, Sprints 1–5 ahead
**Design input:** `echelon_cycle_016.md`, `Echelon_Butterfly_Entropy_Coherence_Review_v1.md` (v1.2.1)
**Baseline:** ≥1009 passed (post-014c), 15 skipped, 13 pre-existing collection errors

---

## 1. Problem Statement

Every backend cycle since 010a has shipped runtime models, services, and tests — but the frontend was built as a **presentation mockup** before most backend systems existed. The audit reveals:

- **Only 2 of 13 routes are properly wired** (Verification + Theatre)
- **11 routes use hardcoded mock data** or demo stores that never call real APIs
- **Backend endpoints exist but are ignored** by the frontend (portfolio, paradox, marketplace)
- **Some frontend components have no backend at all** (OpsBoard, RLMF, VRF, Analytics/Blackbox)
- **TypeScript types don't match Pydantic schemas** (field names, types, missing fields)
- **The investigation toolset (014c) has zero frontend representation**
- **Engine coherence gaps** — three parallel Butterfly/Entropy implementations diverge in stability scale (0–100 vs 0–1), decay constants, and flap type coverage

This cycle does three things: (0) lock engine coherence so the backend emits sane values, (1) reconcile the mock frontend with the real backend, and (2) build the new investigation views that 014c enables.

> Sources: echelon_cycle_016.md:1-22, Echelon_Butterfly_Entropy_Coherence_Review_v1.md:§1-§2

## 2. Objective

### Sprint-0: Engine Coherence Lock (COMPLETE)

Resolve all coherence gaps identified in `Echelon_Butterfly_Entropy_Coherence_Review_v1.md` so that the backend emits correct 0–1 stability values, canonical flap directions, and consistent decay behaviour before any frontend wiring begins. Gates A–G acceptance criteria defined in the coherence review.

### Sprints 1–5: Results Surface

Build the production frontend — reconcile mock/presentation layer with real backend, wire all existing views to live APIs, build new investigation toolset views, redesign navigation. React 19 + Vite 7 + Tailwind stack preserved; kree8.studio visual identity applied.

## 3. Success Criteria

### SC-0: Engine Coherence Lock (COMPLETE ✓)

| Gate | Description | Status |
|------|-------------|--------|
| A | Enum parity: `engines/butterfly.py` and `models.py` WingFlapType enums identical | ✓ |
| B | 0–1 stability storage everywhere: DB default 0.5, all worker tasks use 0–1 clamps, API boundary via `_as_percent()` | ✓ |
| C | FlapDirection enum: STABILISE, DESTABILISE, NEUTRAL — all backend writers (worker/tasks + admin_routes) use `FlapDirection.*.value`, no bare string literals | ✓ |
| D | LogicGapReading dataclass: structured input for EntropyEngine.tick() with backwards compat | ✓ |
| E | Pattern A decay fix: paradox writes `decay_multiplier` only, entropy applies once | ✓ |
| F | Fork divergence: `compute_fork_divergence()` method on ButterflyEngine | ✓ |
| G | Anchor/fork model: `is_anchor`, `anchor_timeline_id`, `fork_divergence` on Timeline | ✓ |

### SC-1: Mock Purge + API Wiring

1. Portfolio page wired to `/api/v1/user/positions` + `/api/v1/user/portfolio/summary`
2. Marketplace wired to Polymarket-backed timelines via `/api/v1/timelines/`
3. Agents page wired to `/api/v1/agents/` with real data (no USE_MOCKS)
4. Paradox/Breach wired to `/api/v1/paradoxes/active`
5. Watchlist wired to `/api/v1/user/watchlist`
6. TypeScript types aligned to backend Pydantic schemas

### SC-2: Investigation Dashboard + Certificate Explorer

1. `investigation_routes.py` — 11 REST endpoints (list, detail, evidence, claims, counter-signals, drift, certificate, scanner, create, submit evidence, register claim)
2. Investigation dashboard with tabbed layout (Overview | Evidence | Claims | Signals | Drift)
3. Evidence Envelope viewer with provenance badges and hash display
4. Claim Graph viewer with status badges, confidence, evidence refs
5. Investigation Certificate explorer (30+ fields grouped)
6. Counter-signal, DeltaBrief, drift, and entity profile panels

### SC-3: OpsBoard + Analytics + RLMF

1. OpsBoard rebuilt as aggregation dashboard from real endpoints (theatres, paradoxes, investigations, flaps, timeline health)
2. Analytics page built from real Theatre/market data (agent leaderboard, theatre history, OSINT timeline)
3. RLMF page redesigned as export viewer
4. VRF page converted to documentation/roadmap page

### SC-4: Investigation Lifecycle Console + Navigation

1. Multi-step investigation creation wizard (inquiry → template → domain filters → stop condition → commit)
2. Investigation progress tracker with stop condition progress
3. Navigation redesigned: Dashboard, Marketplace, Investigations, Theatres, Analytics, Agents, Portfolio, Certificates, RLMF Exports
4. Signal feed migrated from inquiry console to main app

### SC-5: Convergence Map + Agent Analytics + WebSocket + Polish

1. 2D convergence map (1° × 1° cells, grey→amber→red)
2. Agent performance analytics (trade history, archetype radar, genome viewer)
3. WebSocket-driven TanStack Query cache invalidation
4. Responsive layout, loading skeletons, empty states, error states
5. Zero mock data in production code paths

### SC-6: Test Gate

1. ≥1009 passed (post-014c baseline maintained)
2. Zero new test failures
3. 50+ new tests across frontend and backend
4. Post-016 expected: ≥1060 passed

## 4. Codebase Grounding

### Sprint-0 Files Modified/Created (Engine Coherence Lock)

| File | Change |
|------|--------|
| `backend/database/models.py` | Extended WingFlapType (10 new), added FlapDirection enum, 0.5 defaults, anchor/fork fields |
| `backend/alembic/versions/c016_engine_coherence.py` | Migration: enum extension, anchor/fork columns, 0–100→0–1 normalisation, ANCHOR→STABILISE |
| `backend/worker/tasks/_system_entity.py` | NEW: shared SYSTEM entity helper (eliminates ~30-line boilerplate × 3 files) |
| `backend/worker/tasks/entropy.py` | Pattern A fix (uses `decay_multiplier`), anchor skip, 0–1 constants, FlapDirection |
| `backend/worker/tasks/paradox.py` | Writes `decay_multiplier` only, DETONATION flap type, 0–1 thresholds |
| `backend/worker/tasks/market_sync.py` | MIRROR_TRADE type, `is_anchor=True`, 0–1 scale, MAX_ACTIVE_MARKETS=10, `last_sync_at` on every sync |
| `backend/worker/tasks/agent_tick.py` | All 5 strategies: 0–1 thresholds/clamps, FlapDirection enum values |
| `backend/worker/tasks/genesis.py` | 0–1 templates, `is_active`, FORK_SPAWN type, SYSTEM agent, valid WingFlap fields |
| `backend/worker/tasks/kalshi_sync.py` | 0–1 stability, FlapDirection enum |
| `backend/engines/butterfly.py` | Enum sync, FlapDirection, auto-direction, `compute_fork_divergence()` |
| `backend/engines/entropy.py` | LogicGapReading dataclass, backwards-compat `tick()` |
| `backend/worker/game_loop.py` | Evidence (120s) and divergence (60s) cadence stubs |
| `backend/schemas/butterfly_schemas.py` | Extended enums, anchor/fork fields, STABILISE/NEUTRAL |
| `backend/mechanics/butterfly_engine.py` | `_as_percent()` API boundary, direction enums |
| `backend/engines/tests/test_coherence_016.py` | NEW: 22 tests covering Gates A–G |
| `backend/api/admin_routes.py` | 0–1 scale, FlapDirection, WingFlapType enums, valid WingFlap fields |
| `backend/scripts/seed_database.py` | ANCHOR → STABILISE |

### Existing Infrastructure (Sprint 1+ Dependencies)

| Component | Location | Relevance |
|-----------|----------|-----------|
| Polymarket Client | `backend/integrations/polymarket_client.py` | Market auto-discovery, `get_trending_markets()` |
| MarketSyncTask | `backend/worker/tasks/market_sync.py` | Creates `TL_PM_*` timelines, syncs prices |
| Investigation Toolset | `backend/investigation/` | 8 tools, services, 67+ tests |
| Theatre State Machine | `theatre/engine/state_machine.py` | DRAFT → COMMITTED → ACTIVE → SETTLING → RESOLVED → ARCHIVED |
| Certificate Pipeline | `backend/services/certificate_pipeline.py` | CalibrationCertificate + InvestigationCertificate |
| LMSR Market Engine | `backend/market/` | Investigation markets |
| Agent Runtime | `backend/worker/tasks/agent_tick.py` | 6 archetypes, live at 5s cadence |
| API Client | `frontend/src/api/client.ts` | Bearer auth, error handling, `localhost:8000` |

### Frontend–Backend Alignment Audit

**Working correctly (keep):** Verification (`verification_routes.py`), Theatre (`theatre_routes.py`), API Client

**Mock frontend, real backend exists (wire up):** Portfolio, Marketplace, Agents, Paradox/Breach, Watchlist

**Mock frontend, no backend (decide):** OpsBoard → Rebuild as aggregation. RLMF → Redesign as export viewer. VRF → Defer to docs. Analytics → Phase from real data. Exports Console → Stub from pipeline.

**No frontend at all (new build):** Investigation Dashboard, Evidence Envelope Viewer, Claim Graph Viewer, Counter-Signal Feed, Signal Scanner/DeltaBrief, Entity Resolver View, Investigation Certificate, Commitment Monitor/Drift, Convergence Map

## 5. Sprint Breakdown

### Sprint 0: Engine Coherence Lock ✓ COMPLETE

Pre-work dependency resolved. All Gates A–G pass. 22 new tests. 213 passing (engines+schemas). Zero 0–100 leaks in live runtime paths.

### Sprint 1: Mock Purge + Real API Wiring (7 tasks)

Strip mock data, wire to real backend, fix TypeScript types. No new features — just make existing views truthful.

| Task | Description | Tests |
|------|-------------|-------|
| 1.1 | TypeScript type alignment (audit + rewrite all type files) | — |
| 1.2 | Portfolio page → real API | 1 |
| 1.3 | Marketplace → Polymarket-backed timelines + trending endpoint | 1 |
| 1.4 | Agents page → real API + backend enhancement | 1 |
| 1.5 | Paradox/Breach → real API | 1 |
| 1.6 | Watchlist → real API | — |
| 1.7 | Type alignment regression snapshot test | 1 |

**Sprint 1 total:** 5 tests

### Sprint 2: Investigation Dashboard + Certificate Explorer (7 tasks)

| Task | Description | Tests |
|------|-------------|-------|
| 2.1 | Investigation API routes (backend, 11 endpoints) | 8 |
| 2.2 | Investigation dashboard page (tabbed layout) | 1 |
| 2.3 | Evidence Envelope viewer | 1 |
| 2.4 | Claim Graph viewer | 1 |
| 2.5 | Investigation Certificate explorer | 1 |
| 2.6 | Counter-signal + DeltaBrief + drift + entity panels | 2 |
| 2.7 | Sprint 2 integration tests | — |

**Sprint 2 total:** 14 tests

### Sprint 3: OpsBoard Rebuild + Analytics + RLMF Redesign (5 tasks)

| Task | Description | Tests |
|------|-------------|-------|
| 3.1 | OpsBoard → aggregation dashboard | 1 |
| 3.2 | Analytics → build from real data | 1 |
| 3.3 | RLMF → export viewer | 1 |
| 3.4 | VRF → documentation/roadmap page | — |
| 3.5 | Sprint 3 mock purge audit | 1 |

**Sprint 3 total:** 4 tests

### Sprint 4: Investigation Lifecycle Console + Navigation (5 tasks)

| Task | Description | Tests |
|------|-------------|-------|
| 4.1 | Investigation creation wizard | 1 |
| 4.2 | Investigation progress tracker | 1 |
| 4.3 | Navigation redesign | 1 |
| 4.4 | Signal feed migration | 1 |
| 4.5 | Sprint 4 integration tests | — |

**Sprint 4 total:** 4 tests

### Sprint 5: Convergence Map + Agent Analytics + WebSocket + Polish (5 tasks)

| Task | Description | Tests |
|------|-------------|-------|
| 5.1 | Convergence map (2D grid) | 1 |
| 5.2 | Agent performance analytics | 1 |
| 5.3 | WebSocket cache invalidation | 1 |
| 5.4 | Responsive layout + loading states + polish | — |
| 5.5 | E2E test + final mock purge audit | 2 |

**Sprint 5 total:** 5 tests

**Grand total:** 22 (Sprint-0) + 32 (Sprints 1–5) = 54 new tests. Post-016 expected: ≥1060 passed.

## 6. Non-Functional Requirements

### NFR-1: Scale Coherence
All stability values stored on 0.0–1.0 scale internally. API boundary converts to 0–100 via `_as_percent()` for frontend consumption. No mixed-scale values anywhere in the pipeline.

### NFR-2: Design Language
kree8.studio visual identity: `terminal-bg: #030305`, `terminal-card: #10141A`, `glass-border: rgba(255,255,255,0.1)`. JetBrains Mono for data, Inter for prose. Signal colours: action `#3B82F6`, success `#10B981`, risk `#F59E0B`, danger `#EF4444`. New investigation tokens for provenance badges, claim status badges, routing hints, anchoring state.

### NFR-3: Zero Mock Data
Post-016, zero mock data constants remain in production frontend code paths. Every component renders from real API data or displays an honest empty/loading state.

### NFR-4: Backward Compatibility
Sprint-0 engine changes preserve all existing test contracts. Sprint 1+ frontend changes do not modify backend API contracts — only consume them correctly.

## 7. Out of Scope

- 3D globe / Spatial Intelligence "God mode" (deferred — cost and complexity)
- Real Chainlink VRF integration (page becomes informational)
- Real-time collaborative investigation (multi-user editing)
- Mobile native app (responsive web only)
- Chain anchoring UI beyond status display
- Agent breeding/genealogy UI (genome is read-only display)
- $ECHELON token/wallet integration
- Social trading / leaderboard features
- Paid OSINT source activation from UI
- Analytics features requiring new backend endpoints (heatmap, correlation matrix, depth chart) — show placeholders
- `mechanics/butterfly_engine.py` full rewrite (deferred; `_as_percent()` boundary sufficient for now)

## 8. Dependencies

| Dependency | Status | Impact |
|------------|--------|--------|
| Cycle-014c (Investigation Toolset) | ✓ Complete | 8 tools, services, models for investigation views |
| Cycle-015 (Live Collectors) | ✓ Complete | WM + Companies House adapters for scanner/resolver |
| Cycle-013 (Agent Runtime) | ✓ Complete | 6 archetypes in live game loop |
| Cycle-012 (Sponsored Theatres) | ✓ Complete | Theatre creation/commitment lifecycle |
| Cycle-010a (LMSR) | ✓ Complete | Market engine for all timelines |
| Coherence Review v1.2.1 | ✓ Resolved (Sprint-0) | Gates A–G locked |
| Polymarket Client | ✓ Exists | Auto-discovery, sync, trending |

## 9. What This Unlocks

- **Echelon's thesis becomes visible** — markets, evidence, claims, certificates, agents, all rendered from real data
- **Mock presentation layer retired** — every view shows actual backend state
- **Investigation workflow is end-to-end** — create inquiry → collect evidence → structure claims → monitor counter-signals → resolve → inspect certificate
- **Foundation for demos** — the Results Surface is what you show to Soju, investors, early adopters
- **Inquiry console retired** — separate Cloudflare app superseded
