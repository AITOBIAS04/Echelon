# SDD — Cycle-016: Results Surface

**Cycle:** cycle-016
**Date:** 5 March 2026
**PRD:** grimoires/loa/prd.md
**Design input:** `echelon_cycle_016.md`, `Echelon_Butterfly_Entropy_Coherence_Review_v1.md` (v1.2.1)

---

## 1. Architecture Overview

Cycle-016 spans two layers: (0) a backend engine coherence lock that unifies stability scale and flap contracts across all runtime paths, and (1–5) a full production frontend that replaces the mock presentation layer with real API-wired views.

### 1.1 Sprint-0: Engine Coherence Lock (COMPLETE)

Sprint-0 resolved the three-implementation problem identified in the coherence review. The codebase had three overlapping Butterfly/Entropy implementations (`engines/`, `mechanics/`, `worker/tasks/`) that diverged in scale, constants, and flap coverage. Sprint-0 unified them:

```
┌─────────────────────────┐
│  engines/ (spec layer)  │ ← 0–1 scale, full enum, FlapDirection
│  ButterflyEngine        │    compute_fork_divergence(), LogicGapReading
│  EntropyEngine          │    Pattern A: decay_multiplier only
└─────────┬───────────────┘
          │ contract parity
┌─────────▼───────────────┐
│  worker/tasks/ (runtime) │ ← 0–1 scale, FlapDirection.value, SYSTEM entity
│  agent_tick.py           │    5 strategies: uniform(0.01,0.03) not (1.0,3.0)
│  entropy.py              │    timeline.decay_multiplier, anchor skip
│  paradox.py              │    decay_multiplier write only, DETONATION type
│  market_sync.py          │    MIRROR_TRADE, is_anchor=True, MAX_ACTIVE_MARKETS=10
│  genesis.py              │    FORK_SPAWN type, 0–1 templates, SYSTEM agent
│  kalshi_sync.py          │    0–1 clamp, FlapDirection enum
└─────────┬───────────────┘
          │ _as_percent() at API boundary
┌─────────▼───────────────┐
│  mechanics/ (API layer)  │ ← 0–100 for frontend consumption
│  butterfly_engine.py     │    _as_percent() static method on serialisation
└─────────────────────────┘
```

**Key data contracts:**

- **Stability:** `0.0–1.0` in DB and all runtime code. `_as_percent()` × 100 at API serialisation boundary.
- **Direction:** `FlapDirection.STABILISE.value | DESTABILISE.value | NEUTRAL.value` — no bare string literals.
- **Decay:** Paradox writes `decay_multiplier` on Timeline. Entropy reads `base_rate × decay_multiplier` once. No hardcoded `2.0`.
- **Anchor model:** `is_anchor=True` for Polymarket timelines. `anchor_timeline_id` FK for forks. Anchors don't decay (entropy filter: `Timeline.is_anchor == False`).
- **WingFlapType:** 17 values total (7 original + 10 new 016 types). All synced between `engines/butterfly.py`, `database/models.py`, and `schemas/butterfly_schemas.py`.

### 1.2 Sprints 1–5: Frontend Architecture

Frontend stack: React 19 + Vite 7 + Tailwind + TanStack Query (React Query v5).

```
frontend/src/
├── api/              ← API clients (replace mock generators)
├── components/
│   ├── investigation/ ← NEW: 20+ components for investigation views
│   ├── convergence/   ← NEW: convergence map
│   ├── agents/        ← Enhanced: performance analytics
│   ├── layout/        ← Modified: navigation redesign
│   └── ...            ← Existing components (updated for real data)
├── hooks/            ← TanStack Query hooks (replace mock stores)
├── pages/            ← Page components (wired to real APIs)
├── types/            ← TypeScript types (aligned to Pydantic schemas)
└── router.tsx        ← Updated routes
```

Data flow for API wiring pattern:

```
Backend (Pydantic schema)
  → FastAPI endpoint (JSON response)
    → frontend/src/api/ (fetch client)
      → frontend/src/hooks/ (TanStack Query hook with cache key)
        → frontend/src/pages/ (page component)
          → frontend/src/components/ (rendered UI)
```

WebSocket integration (Sprint 5):

```
Backend WS event (wing_flap | price_update | paradox_spawn | investigation_event)
  → frontend/src/hooks/useWebSocket.ts
    → identify query keys
      → queryClient.invalidateQueries()
        → auto-refetch via TanStack Query
```

---

## 2. Sprint-0 — Engine Coherence Lock (COMPLETE)

### 2.1 Models Layer

**Modified:** `backend/database/models.py`

```python
class FlapDirection(str, enum.Enum):
    STABILISE = "STABILISE"
    DESTABILISE = "DESTABILISE"
    NEUTRAL = "NEUTRAL"

class WingFlapType(str, enum.Enum):
    # 7 original + 10 new
    TRADE = "TRADE"
    SHIELD = "SHIELD"
    SABOTAGE = "SABOTAGE"
    RIPPLE = "RIPPLE"
    PARADOX = "PARADOX"
    FOUNDER_YIELD = "FOUNDER_YIELD"
    ENTROPY = "ENTROPY"
    MIRROR_SYNC = "MIRROR_SYNC"
    MIRROR_TRADE = "MIRROR_TRADE"
    EVIDENCE = "EVIDENCE"
    CLAIM = "CLAIM"
    COUNTER_SIGNAL = "COUNTER_SIGNAL"
    CORROBORATION = "CORROBORATION"
    DETONATION = "DETONATION"
    FORK_SPAWN = "FORK_SPAWN"
    STOP_CONDITION = "STOP_CONDITION"
    CERTIFICATE = "CERTIFICATE"
```

Timeline anchor/fork fields:

```python
# Timeline model additions
is_anchor: Mapped[bool] = mapped_column(Boolean, default=False)
anchor_timeline_id: Mapped[Optional[str]] = mapped_column(
    String(50), ForeignKey("timelines.id"), nullable=True)
fork_divergence: Mapped[float] = mapped_column(Float, default=0.0)
last_sync_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
```

### 2.2 Migration

**New:** `backend/alembic/versions/c016_engine_coherence.py`

Dialect-safe migration:
1. Extends WingFlapType enum (PostgreSQL: `ALTER TYPE ... ADD VALUE`, SQLite: no-op)
2. Adds anchor/fork columns to timelines
3. Normalises stability/surface_tension/osint_alignment: `SET col = col / 100.0 WHERE col > 1.0`
4. Migrates direction data: `UPDATE wing_flaps SET direction = 'STABILISE' WHERE direction = 'ANCHOR'`

### 2.3 Pattern A Decay Fix

**Before (buggy):**
```
paradox.py: timeline.decay_rate_per_hour = base * (severity + 1)  ← MUTATES rate
             timeline.decay_multiplier = severity + 1
entropy.py: effective = timeline.decay_rate_per_hour * 2.0         ← hardcoded 2×
Result: base × (sev+1) × 2.0 = double-application
```

**After (fixed):**
```
paradox.py: timeline.decay_multiplier = severity + 1               ← ONLY writes multiplier
entropy.py: effective = base_rate × timeline.decay_multiplier      ← reads multiplier, applies once
Result: base × (sev+1) = correct single-application
```

### 2.4 Shared SYSTEM Entity

**New:** `backend/worker/tasks/_system_entity.py`

```python
async def ensure_system_entities(session: AsyncSession) -> tuple[User, Agent]:
    """Returns (system_user, system_agent), creating if absent."""
```

Eliminates ~30 lines of identical boilerplate in entropy.py, paradox.py, market_sync.py. Note: `kalshi_sync.py` still duplicates this boilerplate (cleanup deferred).

### 2.5 Scale Conversion Reference

| Context | Old | New |
|---------|-----|-----|
| `_shark_strategy` delta | `size / 10000` (~0.1–0.15) | `size / 1_000_000` (~0.001–0.002) |
| `_spy_strategy` delta | `uniform(1.0, 3.0)` | `uniform(0.01, 0.03)` |
| `_diplomat_strategy` delta | `uniform(3.0, 8.0)` | `uniform(0.03, 0.08)` |
| `_saboteur_strategy` delta | `-uniform(5.0, 12.0)` | `-uniform(0.05, 0.12)` |
| `_whale_strategy` threshold | `osint_alignment > 50` | `> 0.5` |
| `_whale_strategy` delta | `size / 5000` (~2–10) | `size / 1_000_000` (~0.01–0.05) |
| Genesis base_stability | `45.0–82.0` | `0.45–0.82` |
| Genesis surface_tension | `uniform(40, 70)` | `uniform(0.40, 0.70)` |
| Genesis osint_alignment | `price_yes * 100` | `price_yes` (already 0–1) |
| Genesis gravity_score | `uniform(50, 80)` | `uniform(0.50, 0.80)` |
| Genesis decay_rate | `1.0` | `0.01` |
| Genesis flap_type | `"GENESIS"` (invalid) | `WingFlapType.FORK_SPAWN` |
| Genesis Timeline.status | `"ACTIVE"` (no such column) | `is_active=True` |
| Kalshi stability cap | `min(5.0)` | `min(0.05)` |
| Kalshi clamp | `max(0, min(100, ...))` | `max(0.0, min(1.0, ...))` |
| Market sync delta cap | `5.0` | `0.05` |

---

## 3. Sprint 1 — Mock Purge + Real API Wiring

### 3.1 TypeScript Type Alignment

**Files:** `frontend/src/types/*.ts`

Rewrite all type files to match backend Pydantic schemas. Key alignments:
- `types/portfolio.ts` → `UserPosition`, `PortfolioSummary` from `backend/schemas/user_schemas.py`
- `types/agents.ts` → `Agent` from `backend/database/models.py`
- `types/marketplace.ts` → Timeline schema from `backend/schemas/butterfly_schemas.py`
- `types/breach.ts` → `Paradox` from `backend/schemas/paradox_schemas.py`
- New: `types/investigation.ts` — all investigation toolset response types
- New: `types/theatre.ts` — `TheatreResponse`, `TheatreCertificateResponse`

### 3.2 Portfolio Wiring

Replace `usePortfolio.ts` mock with TanStack Query calling:
- `GET /api/v1/user/positions` — individual positions
- `GET /api/v1/user/portfolio/summary` — aggregate P&L

Field mapping: `unrealizedPnL` → `unrealised_pnl_usd` (camelCase→snake_case in response transform)

### 3.3 Marketplace Wiring

**The relationship:** Polymarket = base reality. Echelon mirrors markets as `TL_PM_*` timelines, then forks.

Backend tasks:
- Verify `MarketSyncTask.tick()` runs on 10s cadence
- Add `GET /api/v1/timelines/trending` — returns timelines sorted by volume

Frontend: Replace mock market generator with TanStack Query fetching timelines with `TL_PM_*` prefix.

### 3.4 Agents Wiring

Remove `USE_MOCKS=true` default in `backend/api/agents_routes.py`. Frontend hook fetches from `GET /api/v1/agents/`. Display: archetype, P&L, win rate, sanity, is_alive. Accept that genealogy/lineage is out of scope.

### 3.5 Paradox/Breach + Watchlist Wiring

Replace `useDemoBreaches()` with TanStack Query calling `/api/v1/paradoxes/active`. Replace watchlist mock with `/api/v1/user/watchlist`.

---

## 4. Sprint 2 — Investigation Dashboard + Certificate Explorer

### 4.1 Investigation API Routes

**New:** `backend/api/investigation_routes.py`

```
GET  /api/v1/investigations/                       — list active investigations
GET  /api/v1/investigations/{id}                   — investigation detail
GET  /api/v1/investigations/{id}/evidence          — evidence envelope manifest
GET  /api/v1/investigations/{id}/claims            — claim graph + status summary
GET  /api/v1/investigations/{id}/counter-signals   — counter-signal feed
GET  /api/v1/investigations/{id}/drift             — drift events
GET  /api/v1/investigations/{id}/certificate       — investigation certificate
GET  /api/v1/investigations/{id}/scanner           — latest DeltaBrief
POST /api/v1/investigations/                       — create investigation
POST /api/v1/investigations/{id}/evidence          — submit evidence item
POST /api/v1/investigations/{id}/claims            — register claim
```

**New:** `backend/schemas/investigation.py` — Pydantic request/response models

All endpoints delegate to existing `backend/investigation/` service layer from cycle-014c. Routes are thin wrappers.

### 4.2 Investigation Dashboard Component Tree

```
InvestigationPage.tsx
├── InvestigationHeader (routing hint badge, inquiry question, dates)
├── TabNavigation (Overview | Evidence | Claims | Signals | Drift)
├── EvidenceEnvelopePanel.tsx
│   ├── EnvelopeHashDisplay
│   ├── ProvenanceSummaryBar
│   └── EvidenceItemCard.tsx × N
│       └── ProvenanceBadge.tsx
├── ClaimGraphPanel.tsx
│   ├── MerkleRootDisplay
│   ├── ClaimStatusSummary
│   └── ClaimNodeCard.tsx × N
│       ├── ClaimStatusBadge.tsx
│       └── EvidenceRefLinks
├── CounterSignalPanel.tsx
├── DeltaBriefPanel.tsx
├── DriftEventsPanel.tsx
├── EntityProfilePanel.tsx
└── InvestigationCertificateView.tsx
    ├── CertificateFieldGroup.tsx × 8
    └── RoutingHintBadge.tsx
```

### 4.3 Design Tokens (Investigation)

```css
/* Provenance class badges */
--provenance-public-primary: #4ADE80;    /* emerald */
--provenance-public-secondary: #3B82F6;  /* blue */
--provenance-private-leak: #F59E0B;      /* amber */
--provenance-analyst-derived: #8B5CF6;   /* purple */
--provenance-third-party: #6B7280;       /* grey */

/* Claim status badges */
--claim-supported: #4ADE80;
--claim-partially: #FACC15;
--claim-unconfirmed: #6B7280;
--claim-contradicted: #FB7185;

/* Routing/anchoring */
--routing-allowed: #4ADE80;
--routing-review: #F59E0B;
--anchor-unanchored: #6B7280;
--anchor-anchored: #4ADE80;
```

---

## 5. Sprint 3 — OpsBoard + Analytics + RLMF

### 5.1 OpsBoard Aggregation

The OpsBoard is rebuilt as a pure aggregation dashboard — no new backend endpoints. Consumes:

| Widget | Source Endpoint |
|--------|----------------|
| Active Theatres count | `GET /api/v1/theatres` filtered by state |
| Active Paradoxes count | `GET /api/v1/paradoxes/active` |
| Active Investigations count | `GET /api/v1/investigations/` |
| Agent count | `GET /api/v1/agents/` |
| Recent Wing Flaps | `GET /api/v1/butterfly/wing-flaps/recent` |
| Timeline Health | `GET /api/v1/butterfly/timelines/health` |

Layout: 4 summary cards + activity feed + quick-access panels.

### 5.2 Analytics from Real Data

Analytics v1 renders what exists:
- Theatre history → resolved theatres with scores from `/api/v1/theatres` + `/api/v1/certificates`
- Agent leaderboard → from `/api/v1/agents/` sorted by P&L
- OSINT timeline → from `/api/v1/osint/signals`
- "Coming Soon" placeholders for features needing new endpoints (heatmap, correlation matrix, depth chart)

### 5.3 RLMF Export Viewer

Redesign from demo to viewer: RLMF export status per Theatre, export manifest (format, record count, schema version), sample records, download link.

---

## 6. Sprint 4 — Investigation Lifecycle + Navigation

### 6.1 Investigation Creation Wizard

5-step wizard: inquiry question → template selection → domain filters (9 categories) → stop condition config → review & commit.

Stop condition types: OUTCOME_RESOLUTION, EVIDENCE_THRESHOLD, SPONSOR_DEFINED.

Immutability warning on commit step — once committed, stop conditions cannot be changed.

### 6.2 Navigation Structure

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

Remove: `/vrf` from main nav (move to info page), `/agents/export` (fold into RLMF).

---

## 7. Sprint 5 — Convergence Map + WebSocket + Polish

### 7.1 Convergence Map

2D grid: 1° × 1° cells. Colour gradient: grey (no activity) → amber (moderate convergence) → red (high convergence). Click for detail: event types, sources, matched theatres.

Data source: `ConvergenceDetector` service from existing backend.

### 7.2 WebSocket Cache Invalidation

Pattern:
```typescript
// useWebSocket.ts
ws.onmessage = (event) => {
  const { type, payload } = JSON.parse(event.data);
  switch (type) {
    case 'wing_flap':
      queryClient.invalidateQueries({ queryKey: ['timelines', 'health'] });
      break;
    case 'price_update':
      queryClient.invalidateQueries({ queryKey: ['timelines', payload.id] });
      break;
    case 'paradox_spawn':
      queryClient.invalidateQueries({ queryKey: ['paradoxes'] });
      break;
    case 'investigation_event':
      queryClient.invalidateQueries({ queryKey: ['investigations', payload.id] });
      break;
  }
};
```

### 7.3 Polish Checklist

- Responsive breakpoints (stack on narrow viewports)
- Loading skeletons (Tailwind animation tokens)
- Empty states for all panels
- Error states with retry buttons
- Consistent `terminal-*` token usage
- Keyboard navigation for tab panels
- Zero remaining mock data imports (final grep audit)
