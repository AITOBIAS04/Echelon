# Alexander Build — Surface A: Agent Deployment Flow

**Date:** 7 March 2026
**Scope:** Frontend only. Wire deployment UI to backend parity with Cycles 017–021.
**Design references:** `echelon_fleet_v1.html`, `echelon_deploy_agent_modal_v1.html`, `echelon_theatre_detail_v1.html`, `echelon_empty_states_v1.html`

---

## What Already Exists (Frontend)

| Layer | File | Status |
|-------|------|--------|
| Types | `src/types/agentDeployment.ts` | Complete — DeploymentStatus, StrategyProfile, all response types |
| API client | `src/api/agentDeployments.ts` | Complete — 7 endpoints wired (create, list, detail, withdraw, pause, resume, strategy) |
| Hooks | `src/hooks/useAgentDeployments.ts` | Complete — 7 React Query hooks |
| Deploy modal | `src/components/agents/DeployAgentModal.tsx` | Functional — agent select, strategy select, guard error display, success state |
| Fleet page | `src/components/agents/AgentRoster.tsx` | Partial — roster tab uses real API; Global Intelligence tab is mock data |
| Agent detail | `src/components/agents/AgentDetail.tsx` | Minimal — no deployment info shown |
| Routes | `src/router.tsx` | Complete — `/fleet`, `/fleet/:agentId`, redirects from `/agents`, `/agent/:agentId` |
| Theatre API | `src/api/theatres.ts` | No list endpoint — explicitly documented |

---

## What the Design Reference Specifies (echelon_fleet_v1.html)

### Fleet page must show:

**Attention strip** (state-driven):
- Critical: red, "1 agent failed — requires intervention" + degraded count
- Healthy: green, "All N agents healthy — scheduler nominal"
- Empty: info, "No agents provisioned — deploy your first agent to begin"

**5 KPI cards:**
1. Total — roster count + breakdown (active · decommissioned)
2. Alive — responding to heartbeat, % alive
3. Deployed — assigned to theatres, breakdown (healthy · degraded)
4. Idle — alive but unassigned
5. Failed — crashed/unresponsive, intervention count

**Roster table columns:**
- Status (dot + label: Failed / Degraded / Healthy / Idle)
- Name (link to `/fleet/:agentId`)
- Archetype (badge)
- Deployed to (theatre name tag)
- Last Action (event text + relative timestamp)
- P&L (colored)
- Actions (state-based: Restart/Decommission for Failed; View for Degraded; View/Recall for Healthy deployed; Deploy for Idle)

Implementation truth:
- The design reference action set is broader than the current backend support.
- Idle-row `Deploy` from the Fleet page is not a fully live happy path yet because there is no theatre list endpoint for target selection.
- Treat Fleet-page deploy as constrained:
  - honest unavailable modal state is acceptable, or
  - route the operator into a theatre-context deployment path where the theatre is already known

**Filter bar:**
- Search, Status dropdown, Archetype dropdown, Theatre dropdown
- Count label

**Right rail (3 panels):**
- Scheduler Status (key/value)
- Archetype Distribution (stacked bar)
- Recent Events Feed (timestamped, colored dots)

**Empty states:**
- Zero: centered CTA "Deploy Agent"
- All Clear: green strip
- Quiet Monitoring: ghost structure behind overlay

### Deploy modal (echelon_deploy_agent_modal_v1.html):

**5 states:** Unavailable, Normal, Guard Error, Generic Error, Success

**Key detail:** Theatre dropdown currently shows "No list endpoint available" info banner. This is the correct honest state — **do not fake a theatre list**. The modal correctly handles this with the info banner and disabled deploy button.

### Theatre detail (echelon_theatre_detail_v1.html):

**Deployed Agents section** in right rail — shows agents deployed to this theatre with status, last action, P&L. "Deploy Agent" CTA to add agent from theatre context.

Important product truth:
- Theatre-detail deployment is the viable live deployment path even without a theatre list endpoint, because the theatre context already provides `theatre_id`.
- Do not treat Fleet-page deployment and Theatre-detail deployment as equivalent capabilities.

---

## Backend API Contract (Source of Truth)

### Agents
- `GET /api/v1/agents` — list with `active_deployments_count` per agent
- `GET /api/v1/agents/{id}` — detail with `active_deployments_count`

### Deployments
- `POST /api/v1/agent-deployments` — create (agent_id, theatre_id, strategy_profile, config_json)
- `GET /api/v1/agent-deployments` — list with filters (agent_id, theatre_id, status, limit, offset)
- `GET /api/v1/agent-deployments/{id}` — detail with audit trail
- `POST /api/v1/agent-deployments/{id}/withdraw`
- `POST /api/v1/agent-deployments/{id}/pause`
- `POST /api/v1/agent-deployments/{id}/resume`
- `POST /api/v1/agent-deployments/{id}/strategy` — change strategy profile

### Theatres (relevant to deployment)
- `GET /api/v1/theatres/{id}` — single theatre detail (no list endpoint)
- Paradox risk computed on read if stale (>1h)

### WebSocket Events
- `AGENT_DEPLOYED` — global + theatre + agent channels
- `AGENT_WITHDRAWN` — global + theatre + agent channels
- `PARADOX_RISK_CHANGED` — global + theatre channel
- `DEPLOYMENT_STATUS_CHANGED` — global (Cycle 021)
- `DEPLOYMENT_INTERVENTION_REQUIRED` — global (Cycle 021)

### Deployment Response Shape
```
{
  id, agent_id, theatre_id, status (ACTIVE|PAUSED|WITHDRAWN),
  strategy_profile (AGGRESSIVE|BALANCED|DEFENSIVE),
  deployed_by, deployed_at, paused_at, withdrawn_at,
  routing_hint_snapshot, coherence_gate_status_snapshot,
  config_json, created_at, updated_at
}
```

### Guard Errors (422)
5-layer guards: alive, sanity≥15, no duplicate, theatre deployable, uncertified rejected. Error message in `detail` field.

---

## Implementation Tasks

### A1. Fleet Page — Replace Mock Intelligence with Real Deployment Data

**Current state:** Global Intelligence tab shows mock heat map, mock movement feed, mock strategy clusters.

**Target:** Wire the Global Intelligence tab to real deployment data from `GET /api/v1/agent-deployments`.

- Use `useDeploymentList()` hook (already exists) to populate deployment views
- KPI cards should derive from real agent list data:
  - Total = agents.length
  - Alive = agents where is_alive === true
  - Deployed = agents where active_deployments_count > 0
  - Idle = alive but active_deployments_count === 0
  - Failed = agents where is_alive === false
- Attention strip derives from the same data
- If heat map / movement feed / strategy clusters cannot be populated from real data, show Sparse Data empty state (per `echelon_empty_states_v1.html`) rather than mock data

**Rule:** No fake data. If a widget cannot be real, show an honest empty/sparse state.

### A2. Fleet Roster Table — Match Design Reference

**Current state:** Agent cards in a grid layout.

**Target:** Match `echelon_fleet_v1.html` roster table specification.

- Table columns: Status, Name, Archetype, Deployed to, Last Action, P&L, Actions
- Status dot + label derived from: is_alive, active_deployments_count, and deployment status
  - Failed = !is_alive
  - Deployed Healthy = is_alive && active_deployments_count > 0 (and no degraded signal)
  - Idle = is_alive && active_deployments_count === 0
  - Degraded = derive from deployment or agent state if backend surfaces it
- "Deployed to" column: fetch from `GET /api/v1/agent-deployments?agent_id={id}&status=ACTIVE` or batch from list
- Row actions per state:
  - Failed → Restart/Decommission only if real endpoints exist; otherwise defer honestly
  - Degraded → View
  - Healthy deployed → View/Recall
  - Idle → do not present a fake live deploy path from Fleet if no theatre target can be selected; use the honest unavailable modal state or route to theatre-context deployment
- Filter bar: search, status, archetype, theatre dropdowns

**Backend limitation:** No theatre list endpoint. Theatre filter dropdown should either:
- Derive theatre names from active deployments already fetched, OR
- Show as deferred/disabled with honest empty state

**Note on "Recall":** This maps to the withdraw endpoint (`POST /agent-deployments/{id}/withdraw`). Label it "Recall" in UI per design reference.

### A3. Agent Detail Page — Show Deployment Info

**Current state:** Minimal page, no deployment data.

**Target:** Show deployment details for the agent.

- Use `useDeploymentList({ agent_id: agentId })` to fetch this agent's deployments
- Show active deployments with: theatre name/id, status, strategy, deployed_at
- Show deployment history (WITHDRAWN deployments)
- Actions: Pause/Resume/Withdraw for ACTIVE deployments, strategy change
- If no deployments, show Zero State empty per design reference

### A4. Deploy Modal — Preserve Current Honest State

**Current state:** Modal correctly shows theatre dropdown as unavailable with info banner.

**Target:** Keep the current Fleet-page modal honest, and distinguish it from theatre-context deployment. The current Fleet-page behavior is correct:
- Agent dropdown from real API ✓
- Theatre dropdown disabled with info banner ✓
- Strategy selection works ✓
- Guard error display works ✓
- Success state works ✓

**If launched from Fleet page:** Keep the unavailable state until a theatre list endpoint exists.

**If launched from Theatre detail page:** Prefill/lock the known `theatre_id` from route context and allow deployment because target selection is no longer blocked.

**If a theatre list becomes available later:** Enable the Fleet-page theatre dropdown and populate from API. Until then, keep the honest unavailable state there.

### A5. Right Rail Panels — Wire Real Data

**Per design reference:**
- Scheduler Status: key/value panel. If no scheduler API exists, show as deferred.
- Archetype Distribution: derive from agent list (group by archetype, count). This is real data — implement it.
- Recent Events Feed: can derive from deployment audit events via `useDeploymentDetail()` or from WebSocket events. If WS infra exists in frontend, wire `AGENT_DEPLOYED` and `AGENT_WITHDRAWN` events into feed. Otherwise, poll deployment list.

### A6. WebSocket Integration (if frontend WS infra exists)

**Check:** Does the frontend already have WebSocket connection infrastructure?

If yes:
- Subscribe to `AGENT_DEPLOYED`, `AGENT_WITHDRAWN` events
- Use them to invalidate/update React Query caches for deployment lists
- Wire into Recent Events Feed on fleet page

If no:
- The 15s polling already configured on `useDeploymentList` is acceptable
- WebSocket integration is deferred to a later pass

---

## Backend Limitations to Surface Honestly

1. **No `GET /api/v1/theatres` list endpoint** — theatre dropdown in modal stays disabled; theatre filter on fleet derives from deployment data only
2. **Fleet-page deployment is target-constrained** — without a theatre list, a generic idle-agent deploy action cannot complete from Fleet alone
3. **No heartbeat/scheduler API** — Scheduler Status panel shows deferred state
4. **No "degraded" status in deployment model** — status is ACTIVE/PAUSED/WITHDRAWN only. "Degraded" from design reference may need to map to a future signal or be deferred
5. **No "restart" or "decommission" endpoints** — Failed row actions may need to be deferred or mapped to existing actions
6. **`DEPLOYMENT_STATUS_CHANGED` and `DEPLOYMENT_INTERVENTION_REQUIRED` WS events** exist in backend but have no frontend consumer yet

---

## Acceptance Criteria

1. Fleet page shows real agent data with deployment counts — no mock data
2. KPI cards derive from real agent/deployment API responses
3. Roster table matches design reference column structure where backend supports it
4. Agent detail shows deployment history from real API
5. Deploy modal preserves current honest unavailable state for theatre dropdown
6. Theatre-context deployment is treated as the viable live path when `theatre_id` is already known
7. Guard errors from backend are displayed clearly in modal
8. Withdraw (Recall) action works from roster table and agent detail
9. Pause/Resume actions work from agent detail deployment cards
10. Empty states follow `echelon_empty_states_v1.html` patterns
11. `npm run build` passes

---

## Intentionally Deferred

- Theatre list endpoint (backend gap — do not fake)
- Scheduler Status panel (no API)
- Degraded agent state detection (no backend signal yet)
- Restart/Decommission actions (no backend endpoints)
- Full WebSocket event integration (acceptable to defer if no frontend WS infra)
- Deployment telemetry summaries from Cycle 021 (surface only if naturally exposed in API responses)

---

## Summary Format Per Pass

After each implementation pass, report:
1. What changed (files, components, hooks)
2. What remains intentionally deferred
3. Any backend limitations discovered
4. Any design reference corrections needed
5. Exact `npm run build` result
