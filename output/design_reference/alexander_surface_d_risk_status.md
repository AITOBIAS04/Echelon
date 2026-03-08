# Alexander Build — Surface D: Risk / Status Surfaces

**Date:** 8 March 2026
**Scope:** Frontend only. Wire paradox risk, review-required states, and WebSocket-driven status updates to backend parity with Cycles 017–021.
**Design references:** `echelon_paradox_console_v1.html`, `echelon_certificates_v1.html`, `echelon_dashboard_v1.html`, `echelon_empty_states_v1.html`

---

## What Already Exists (Frontend)

| Layer | File | Status |
|-------|------|--------|
| Types | `src/types/index.ts` | Partial — `ParadoxStatus` (ACTIVE/EXTRACTING/DETONATED/RESOLVED), `SeverityClass` (4 levels). Full `Paradox` interface with extraction costs, decay multiplier. |
| Types | `src/types/risk.ts` | Mock-only — `TimelineRiskState` (stability, logicGap, paradoxProximity), `PositionExposure`, `PortfolioRiskSummary`. No real API backs these. |
| Types | `src/types/theatre.ts` | Complete — `RoutingHint` (ALLOWED/REVIEW_REQUIRED/BLOCKED), `GateStatus` (PENDING/PASSED/FAILED), `TheatreCertificateResponse` with routing_hint, coherence_review_required, coherence_gate_status, is_deployable |
| Types | `src/types/agentDeployment.ts` | Complete — `routing_hint_snapshot`, `coherence_gate_status_snapshot` captured at deployment time |
| API client | `src/api/paradox.ts` | Partial — real reads (`getActiveParadoxes()`, `getParadox(id)`), but extract/abandon/preview are surfaced through `useParadoxConsole.ts`, not this file |
| API client | `src/api/risk.ts` | **Mock** — `getMyPositions()`, `getTimelineRiskStates()` return hardcoded data with simulated delay |
| Hooks | `src/hooks/useParadoxes.ts` | Partial / duplicate path — direct fetch wrapper exists, but the live console still uses `src/hooks/useBreaches.ts` for paradox data |
| Hooks | `src/hooks/useBreaches.ts` | Real current baseline — `useParadoxes()` adapts `/api/v1/paradox/active` for the existing console and legacy breach surfaces |
| Hooks | `src/hooks/useParadoxConsole.ts` | Real API client for extract/abandon/preview, but not yet the console’s actual source of truth |
| WebSocket | `src/hooks/useRealtimeInvestigation.ts` | Complete — handles `PARADOX_RISK_CHANGED` → invalidates `['opsDashboard']` + `['theatre', timeline_id]`; also `PARADOX_SPAWN`, `PARADOX_MOVED`, `DETONATION` → invalidates `['paradoxes', 'active']` |
| WebSocket | `src/hooks/useWebSocket.ts` | Complete — low-level WS connection with auto-reconnect (3s delay, max 5 attempts), channel subscribe |
| Components | `src/components/paradox/ParadoxPanel.tsx` | Real API — active paradoxes list, severity badges, countdown timers, extraction/abandon modals |
| Components | `src/components/paradox/ParadoxAlert.tsx` | Real API — individual paradox alert card |
| Components | `src/components/fieldkit/ParadoxProximityBar.tsx` | Mock — thin progress bar (cyan→red gradient), receives `proximity` prop |
| Components | `src/components/timeline/ParadoxPanel.tsx` | Mock — timeline-scoped paradox display |
| Pages | `BreachConsolePage.tsx` | Partial — real paradox list, but still built on the older breach/paradox path and still renders disabled Extract/Deploy/Abandon buttons with stale “not yet connected” copy |
| Pages | `CertificatesPage.tsx` | Real API — shows `RoutingBadge()` (ALLOWED/REVIEW_REQUIRED/BLOCKED) + `GateBadge()` (PASSED/PENDING/FAILED) |
| Layout | `AppLayout.tsx` | Real — calls `useRealtimeInvalidation('platform')` globally |

---

## What the Design Reference Specifies

### Paradox Console (echelon_paradox_console_v1.html)

**Page state machine** (3 mutually exclusive states):
- `if (active_paradoxes === 0)` → CLEAR state (calm, green)
- `else if (critical + urgent >= 2)` → CRITICAL state (red, escalated)
- `else` → ACTIVE state (amber, mixed)

**Attention strip** (state-driven):
- Critical: red, "N Active Paradoxes" with severity breakdown (N Critical · N Urgent · N Watch · N detonation in <1h)
- Active: amber, "N Active Paradoxes" with breakdown (N Watch · N Assigned · N Under review)
- Clear: green, "All Clear — No active contradictions — all markets within expected parameters"

**7 KPI cards:**
1. Active — count, "now" window badge
2. Critical — count, highlighted red if > 0
3. Watch — count, amber if > 0
4. Linked Theatres — count
5. Investigations — linked count
6. Detonation Windows — count of urgent/imminent, highlighted red
7. Resolved — count, "today" window badge, green

**Layout:** `1fr 300px` grid — paradox roster + right rail.

**Paradox card structure:**
- Card border: severity-driven (critical=red left border, urgent=red outlined, watch=amber, assigned=blue)
- Header: title + ID, contradiction summary (prominent red/amber text), severity chip, countdown timer
- Countdown escalation tiers:
  - >50% remaining → normal timer
  - <50% → amber timer, subtle border
  - <25% → red timer, elevated card
  - <1h → strongest emphasis, pulsing timer
- Body (2-column grid):
  - Linked Entities: theatre chip (purple), investigation chip (orange), agent chip (gray)
  - Market vs Evidence: price/probability comparison
  - Evidence Context: evidence count, counter-signals, drift events, freshness
  - Theatre Price: probability + theatre name
- Footer: status label (Paradox Active / Under Review / Assigned), spawned timestamp, action buttons

**Action vocabulary by urgency:**
- Normal: Open · Assign · Silence · Open Investigation · Open Theatre
- Urgent: Intervene · Extract · Assign · Open Theatre
- Critical: Intervene · Extract (primary, red emphasis)

**Zero state (CLEAR):**
- Green icon + "No Active Contradictions" + description + recently resolved list (title + relative time)

**Right rail (3 panels):**
- Detonation Queue: ordered countdown list with severity chips + time remaining (critical state only)
- Severity Distribution: dot + label + count per severity level
- Agent Involvement: agent name + paradox count + status

### Theatre Risk Display

**On theatre detail response (`GET /api/v1/theatres/{id}`):**
- `paradox_risk_level`: LOW | WATCH | HIGH (recomputed on read if stale >1h)
- `paradox_risk_factors_json`: { logic_gap, stability, active_paradox, material_counter_signals, evidence_freshness_hours }
- Risk is inquiry-class-aware with 5 threshold sets: COUNTERFACTUAL, INVESTIGATIVE, INSPECTION, SURVEY, SCRUTINY

### Certificate Review-Required States

**Certificate routing (from RoutingEvaluator):**
- ALLOWED: green badge, passes all governance checks
- REVIEW_REQUIRED: amber badge + reason text, triggers coherence gate
- BLOCKED: red badge, blocked from deployment

**Coherence gate lifecycle:**
- `should_require_review()` → opens gate (PENDING)
- Manual resolve → PASSED or FAILED
- `is_deployable` computed: False if BLOCKED or (review_required AND gate NOT PASSED)

**Certificate coherence gate endpoints:**
- `GET /api/v1/certificates/{certificate_id}/gate` — status + audit trail
- `POST /api/v1/certificates/{certificate_id}/gate/resolve` — resolve as PASSED/FAILED

### WebSocket Events (Risk/Status Scope)

| Event | Payload | Triggered By |
|-------|---------|-------------|
| `PARADOX_RISK_CHANGED` | theatre_id, old_level, new_level, factors, reason | ParadoxRiskOrchestrator when material change detected (level changed, active_paradox flipped, counter_signals crossed 0 boundary) |
| `PARADOX_SPAWN` | paradox data | New paradox detected |
| `PARADOX_MOVED` | paradox data | Paradox reassigned |
| `DETONATION` | paradox data | Paradox detonated |
| `COHERENCE_GATE_TRANSITION` | certificate_id, from_status, to_status, reviewer_id | CoherenceGateEvaluator.open_gate() or resolve_gate() |

---

## Backend API Contract (Source of Truth)

### Paradox
- `GET /api/v1/paradox/active` — list active paradoxes
- `GET /api/v1/paradox/{id}` — paradox detail
- `POST /api/v1/paradox/{id}/extract` — extract paradox
- `POST /api/v1/paradox/{id}/abandon` — abandon paradox
- `GET /api/v1/paradox/{id}/extraction-preview` — extraction cost + stability gain estimate

### Paradox Risk (on Theatre)
- `GET /api/v1/theatres/{id}` — includes paradox_risk_level, paradox_risk_factors_json (recomputed if stale >1h)
- Recompute triggers: evidence submission, counter-signal ingestion (via investigation routes)
- WS broadcast: PARADOX_RISK_CHANGED with materiality gating

### Coherence Gates
- `GET /api/v1/certificates/{certificate_id}/gate` — gate status + audit trail
- `POST /api/v1/certificates/{certificate_id}/gate/resolve` — resolve gate (PASSED/FAILED)

### WebSocket
- `GET /ws` — WebSocket endpoint
- Client commands: `{"action": "subscribe", "channel": "theatre:THEATRE_ID"}`, `{"action": "unsubscribe", "channel": "..."}`, `{"action": "ping"}`
- Channel patterns: global broadcast + `theatre:{theatre_id}` for risk events

---

## Implementation Tasks

### D1. Paradox Console — Match Design Reference Layout

**Current state:** `BreachConsolePage.tsx` exists and fetches real paradox data, but the page is still partially legacy. It uses the existing paradox/breach hooks rather than the full `useParadoxConsole()` action surface, and several actions remain disabled in the current UI.

**Target:** Match `echelon_paradox_console_v1.html` specification.

- Page state machine: derive CLEAR/ACTIVE/CRITICAL from `paradoxes.length` and severity counts
- Attention strip: 3 states (red critical, amber active, green clear) with severity breakdown
- 7 KPI cards: Active, Critical, Watch, Linked Theatres, Investigations, Detonation Windows, Resolved
- Paradox roster: stacked cards with severity-driven borders, countdown timers, escalation tiers
- Card body: 2-column context grid (linked entities, market vs evidence, evidence context, theatre price)
- Card footer: status label, spawned time, urgency-appropriate action buttons
- Zero state: "No Active Contradictions" + recently resolved list
- Right rail: Detonation Queue (critical state), Severity Distribution, Agent Involvement

**Implementation truth:**
- The paradox API (`GET /api/v1/paradox/active`) returns real data. The card structure should use what the API response provides.
- Linked Theatres / Investigations KPI: derive from paradox entities if the response includes theatre_id / investigation references. If not, show only counts derivable from the active paradoxes list.
- Detonation Windows KPI: derive from paradox countdown timers if the response includes time-to-detonation or severity_window.
- Resolved count: requires resolved paradoxes endpoint or a separate query. If not available, defer or show 0.
- Action buttons:
  - `Extract` / `Abandon` should wire to existing `useParadoxConsole()` mutations where the endpoints exist
  - `Assign` / `Silence` / `Intervene` should stay disabled or omitted unless real backend support exists
- Countdown timers: compute from `created_at + severity_window` if fields are available; otherwise use whatever time data the response provides.

**Rule:** Only show data backed by real paradox API responses. Do not fabricate paradox cards or evidence context stats that the endpoint does not provide.

### D2. Paradox Risk on Theatre Detail

**Current state:** Theatre detail response includes `paradox_risk_level` and `paradox_risk_factors_json`. Frontend theatre types include these fields. `PARADOX_RISK_CHANGED` is invalidated via `useRealtimeInvalidation`, but a dedicated theatre-detail risk panel is not yet visibly implemented in the frontend.

**Target:** Display paradox risk prominently on theatre detail views.

- Risk level badge: LOW (green), WATCH (amber), HIGH (red) — styled consistently with severity chips
- Risk factors breakdown (if shown): logic_gap, stability, active_paradox, material_counter_signals, evidence_freshness_hours
- Risk updated_at timestamp (mono)
- WebSocket-driven: PARADOX_RISK_CHANGED auto-refreshes theatre query

**Implementation truth:**
- Risk is recomputed server-side on read if stale >1h. The frontend does not need to trigger recomputation; just display what the API returns.
- Risk factors are inquiry-class-aware. The frontend does not need to know the threshold model; just display the computed level and factors.
- If `paradox_risk_level` is null, show "Not evaluated" or similar honest deferred state.

### D3. Certificate Routing & Coherence Gate Display

**Current state:** `CertificatesPage.tsx` already displays `RoutingBadge()` and `GateBadge()`. Types for `RoutingHint` and `GateStatus` are complete. Deployment snapshots capture routing_hint_snapshot at deployment time. Coherence gate detail / resolve UI is not yet wired.

**Target:** Match design reference certificate routing states and wire coherence gate management.

- Routing badge: ALLOWED (green), REVIEW_REQUIRED (amber), BLOCKED (red) — already implemented
- Coherence gate panel: show gate status (PENDING/PASSED/FAILED) on certificates where `coherence_review_required === true`
- Gate resolve action: POST `/api/v1/certificates/{certificate_id}/gate/resolve` — for PENDING gates, show resolve UI (PASSED/FAILED buttons) only if the current user context is allowed to act
- Gate audit trail: fetch via `GET /api/v1/certificates/{certificate_id}/gate` — show history of gate state transitions if a detail surface is added in this pass
- is_deployable status: clearly indicate when a certificate is not deployable due to review requirement

**Implementation truth:**
- Gate resolve requires authorization. If the current user context does not have reviewer permissions, the resolve buttons should be informational-only or disabled.
- The gate API endpoints exist on the theatre certificates router (`/api/v1/certificates/{id}/gate`). Frontend needs an API client function and hook for these endpoints if not already present.
- `COHERENCE_GATE_TRANSITION` WebSocket event: ensure `useRealtimeInvalidation` handles this event to invalidate certificate queries. Check if this event is in the current EVENT_QUERY_MAP.

### D4. WebSocket Event Integration — Risk/Status Real-time Updates

**Current state:** `useRealtimeInvalidation` already handles `PARADOX_RISK_CHANGED`, `PARADOX_SPAWN`, `PARADOX_MOVED`, `DETONATION` → appropriate query invalidations. `AppLayout.tsx` calls it globally. `COHERENCE_GATE_TRANSITION` is **not** currently in the event map.

**Target:** Verify and extend WebSocket integration for all risk/status events.

- `PARADOX_RISK_CHANGED` → invalidate theatre query + ops dashboard ✓ (already wired)
- `PARADOX_SPAWN` / `PARADOX_MOVED` / `DETONATION` → invalidate paradox list ✓ (already wired)
- `COHERENCE_GATE_TRANSITION` → invalidate certificate queries + gate status. This is not currently in the frontend EVENT_QUERY_MAP and should be added if Surface D touches gate UI.
- Theatre channel subscriptions: when viewing a theatre detail page, subscribe to `theatre:{theatre_id}` for targeted risk updates

**Implementation truth:**
- Global broadcast covers most use cases. Theatre-specific channel subscriptions are an optimization — they ensure the theatre detail view gets targeted updates. If global broadcast already covers the invalidation paths, channel subscriptions are optional.
- The WebSocket endpoint supports subscribe/unsubscribe commands. The `useWebSocket` hook supports channel subscriptions.

### D5. Risk Data Cleanup — Replace Mock with Real or Defer

**Current state:** `src/api/risk.ts` contains mock implementations for `getMyPositions()` and `getTimelineRiskStates()`. `ParadoxProximityBar`, `PortfolioRiskPanel`, and timeline/fieldkit risk surfaces still rely on mock-only inputs.

**Target:** Honest treatment of mock vs real data.

- If portfolio risk endpoints exist in the backend, wire to real API. If not, mark these surfaces as explicitly deferred with empty/unavailable states rather than showing fake data.
- `ParadoxProximityBar`: if this receives a real `proximity` value from a parent that fetches real data, keep it. If the parent passes mock data, defer.
- `timeline/ParadoxPanel`: if the timeline response includes real paradox status, wire it. If mock, defer.

**Rule:** No fake data. Replace mock API calls with honest empty states or remove the mock surfaces entirely. Prefer honest "Not available" states over convincing fakes.

---

## Backend Limitations to Surface Honestly

1. **Paradox lifecycle still partially legacy** — the paradox engine has real API endpoints, but the current frontend paradox console is not yet fully switched over to the action-capable hook path, and the list may be sparse or empty in practice.
2. **No resolved paradoxes endpoint** — the "Resolved today" KPI and the recently-resolved list in the zero state may not have a data source unless `GET /api/v1/paradox/active` includes a `status` filter for resolved.
3. **Portfolio risk endpoints** — `getMyPositions()` and `getTimelineRiskStates()` are fully mock. No backend endpoints exist for portfolio risk aggregation.
4. **Evidence context per paradox** — the design reference shows evidence count, counter-signals, drift events, freshness per paradox card. Whether the paradox API response includes this data needs verification. If not, defer those context blocks.
5. **Agent involvement per paradox** — the design reference shows flagged agents. Whether the paradox response includes agent references needs verification.
6. **COHERENCE_GATE_TRANSITION event** — not currently in the frontend EVENT_QUERY_MAP. Needs explicit addition if this pass surfaces gate status transitions.
7. **Theatre price / probability on paradox cards** — requires cross-referencing paradox entities with theatre data. If not included in paradox response, defer or show theatre ID only.

---

## Acceptance Criteria

1. Paradox console shows real paradox data from `GET /api/v1/paradox/active` with correct page state (CLEAR/ACTIVE/CRITICAL)
2. Attention strip derives from real paradox severity distribution — no mock severity counts
3. KPI cards show only values derivable from real API responses
4. Paradox cards show severity-driven borders, countdown timers (where time data is available), and action buttons
5. Extract / Abandon actions wire to real mutations if touched in this pass; unsupported actions remain disabled or omitted with honest copy
6. Theatre detail shows paradox_risk_level badge (LOW/WATCH/HIGH) from real API response
7. PARADOX_RISK_CHANGED WebSocket event updates theatre risk display reactively
8. Certificate routing badges (ALLOWED/REVIEW_REQUIRED/BLOCKED) and gate status (PASSED/PENDING/FAILED) display correctly
9. Coherence gate resolve action is wired to the real endpoint if Surface D includes gate management in this pass; otherwise the gap is explicitly documented
10. Mock risk data (`src/api/risk.ts`) replaced with honest empty/deferred states — no fake portfolio data
11. COHERENCE_GATE_TRANSITION WebSocket event handled (or documented as gap)
12. Empty/zero state matches design reference: "No Active Contradictions" with recently resolved list (or honest "No resolved paradoxes" if data unavailable)
13. `npm run build` passes

---

## Intentionally Deferred

- Paradox lifecycle automation (spawn thresholds, automatic detonation) — engine not fully wired to real market dynamics
- Portfolio risk surfaces (position exposures, timeline risk states) — no backend endpoints
- Recently resolved paradox list — no resolved paradoxes endpoint confirmed
- Per-paradox evidence context (evidence count, counter-signals, drift, freshness) — depends on paradox API response shape
- Per-paradox agent involvement — depends on paradox API response shape
- Theatre price cross-reference on paradox cards — depends on paradox response including theatre entity data
- Coherence gate audit trail UI — endpoint exists but no frontend component confirmed
- Dashboard/Mission Control paradox integration — separate surface, not part of this cycle
- Theatre-detail paradox risk panel if no existing theatre detail slot can host it cleanly in this pass

---

## Summary Format Per Pass

After each implementation pass, report:
1. What changed (files, components, hooks)
2. What remains intentionally deferred
3. Any backend limitations discovered
4. Any design reference corrections needed
5. Exact `npm run build` result
