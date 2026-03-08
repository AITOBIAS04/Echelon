# Echelon Frontend Handoff Matrix — Alexander

**Date:** 2026-03-06
**Scope:** Current frontend contract for the renamed IA surfaces and linked detail flows. This document freezes the product split, empty-state copy/CTA contracts, canonical routes, and current implementation truth. It does not assume Cycle 017 backend unlocks.
**Build status:** Frontend build passes.

---

## 1. Empty State Matrix

Design reference: `output/design_reference/echelon_empty_states_v1.html`
Shared component: `frontend/src/components/empty-states/EmptyState.tsx`

This table is the handoff contract. Some rows are already wired in code; others are contract-only and should be implemented to this spec when the page is touched.

| Page | Route | State Type | Title | CTA(s) | Status |
|------|-------|------------|-------|--------|--------|
| Theatres | `/theatres` | ZERO_STATE | No theatres yet | **Create Theatre** | Contract only |
| Fleet | `/fleet` | ZERO_STATE | No agents deployed | **Deploy Agent** | Contract only |
| Investigations | `/investigation` | ZERO_STATE | No investigations yet | **New Investigation** | Contract only |
| Positions | `/portfolio` | ZERO_STATE | No open positions | **Browse Theatres** | Contract only |
| Scenario Packs | `/scenario-packs` | ZERO_STATE | No scenario packs yet | **Browse Starter Packs** | Wired |
| World Monitor | `/world-monitor` | ZERO_STATE | No timelines yet | **Create Theatre** | Wired |
| World Monitor | `/world-monitor` | QUIET_MONITORING | Monitoring active | — | Wired |
| Signal Map | `/signal-map` | QUIET_MONITORING | Low signal density | — | Wired |
| Mission Control | `/home` | ALL_CLEAR | All systems nominal | — | Contract only |
| Paradox Console | `/paradox-console` | ALL_CLEAR | No active contradictions | — | Contract only |
| Analytics | `/analytics` | SPARSE_DATA | Limited data | — | Contract only |
| RLMF Exports | `/rlmf` | NOT_YET_GENERATED | No exports generated | **Generate First Export** | Contract only |
| Certificates | `/certificates` | NOT_YET_GENERATED | No certificates yet | **Browse Theatres** + _Verify a Certificate_ | Wired |
| Any filtered list | Inline only | NO_RESULTS | — | **Clear Filters** | Shared component ready |

**Bold** = primary CTA. _Italic_ = secondary CTA.

---

## 2. Canonical Routes

These are the routes relevant to the current handoff. Older routes remain as redirects for compatibility.

### Canonical

| Label | Route | Notes |
|------|-------|-------|
| Mission Control | `/home` | Dashboard / ops board |
| Theatres | `/theatres` | Primary theatre index |
| Create Theatre | `/theatres/create` | Template path functional; blank deferred |
| Theatre Detail | `/theatre/:theatreId` | Current canonical detail path |
| Fleet | `/fleet` | Agent roster |
| Fleet Detail | `/fleet/:agentId` | Replaces old `/agent/:agentId` |
| Investigations | `/investigation` | Investigation list |
| Create Investigation | `/investigation/create` | Existing create flow |
| Paradox Console | `/paradox-console` | Replaces old breach route |
| World Monitor | `/world-monitor` | New page |
| Signal Map | `/signal-map` | New page |
| Positions | `/portfolio` | Existing portfolio page |
| Analytics | `/analytics` | Existing blackbox page under new IA |
| Certificates | `/certificates` | New page |
| RLMF Exports | `/rlmf` | Existing exports page under new label |
| Verify | `/verify` | Existing verification dashboard |
| Scenario Packs | `/scenario-packs` | Empty-state shell only; no backend yet |

### Legacy Redirects

| Old Route | Redirects To |
|----------|--------------|
| `/marketplace` | `/theatres` |
| `/agents` | `/fleet` |
| `/agent/:agentId` | `/fleet/:agentId` |
| `/agents/breach` | `/paradox-console` |
| `/agents/export` | `/rlmf` |
| `/investigation/signals` | `/signal-map` |
| `/fieldkit` | `/portfolio` |
| `/blackbox` | `/analytics` |
| `/timeline/:timelineId` | Backward-compatible detail route |

### Out of Scope for This Handoff

`/vrf`, `/convergence`, and `/launchpad*` exist in the router but are not part of the current renamed-IA / empty-state handoff.

---

## 3. Product Contract

### Locked

| Item | Contract |
|------|----------|
| Theatre Templates | Live market / certificate templates |
| Scenario Packs / Alpamayo Studio | Branching RL / telemetry environments |
| Alpamayo in Create Theatre | Recommendation layer for live theatre templates only |
| RLMF Exports | Data-product catalog |
| Agent redirect | `/agent/:agentId` must resolve to `/fleet/:agentId` |

### Current Truth in Code

| Surface | Status | Notes |
|--------|--------|-------|
| Create Theatre | Partial but honest | Template path works against real template detail; blank path is explicitly deferred; Alpamayo remains staged shell |
| Agent Deployment | Staged only | Fleet zero-state CTA opens `DeployAgentModal`, but the modal still uses mock theatre data and does not execute a real deployment |
| Scenario Packs | Deferred | Empty-state/catalog shell only; no mock-rich page committed |
| Certificates | Partial | Page exists and empty state is wired; broader certificate UX may still need review |
| Routes / IA | Transitional but stable | Redirects are in place; `/theatre/:theatreId` remains current detail route |

### Open Decisions

These are the actual open decisions still relevant to Alexander's implementation work:

| # | Decision | Current Safe Default |
|---|----------|----------------------|
| 1 | Alpamayo path: keep staged shell or build full recommendation-backed flow now? | Keep staged shell until backend support exists |
| 2 | Scenario Packs: build rich mock/stub catalog now or leave explicitly deferred? | Leave explicitly deferred |
| 3 | Agent deployment: keep the current staged modal or implement a real deploy flow now? | Keep the current staged modal until backend deployability support exists |
| 4 | Certificates: is the current empty-state page sufficient for handoff, or does the page need another design/integration pass? | Hand off current page, mark broader enhancements separately |
| 5 | Route normalization: keep `/theatre/:theatreId` for now or normalize later to `/theatres/:theatreId`? | Keep current route; normalize later if desired |
| 6 | Create Theatre editorial fields: keep visible as staged UI or hide until persistence support exists? | Keep visible with staged-state callouts |

---

## 4. Feature Flags

File: `frontend/src/lib/featureFlags.ts`

Resolution order:
1. localStorage override: `ff_<lowercase_flag_name>`
2. env var: `VITE_FF_<FLAG>`
3. default `false`

| Flag | Current Intent |
|------|----------------|
| `CYCLE_017_DEPLOYABILITY_ROUTING` | Gate deployability / routing-hint related UI |
| `CYCLE_017_TAO_FLOW` | Gate TAO / Alpamayo-related staged behaviors and 017 timeline fields |
| `CYCLE_017_REGISTRY_SCHEMA` | Gate 017 registry metadata fields |
| `CYCLE_017_COHERENCE_GATES` | Gate post-routing / coherence policy UI |
| `WEBSOCKET_REALTIME` | Gate live update surfaces after REST is stable |

Do not implement speculative UI behind these flags unless the code already has a real field contract.

---

## 5. Create Theatre — Current Truth

Path: `/theatres/create`

| Path | Status | What Works | What Does Not |
|------|--------|------------|---------------|
| Template | Functional | Catalog loads, selected template detail is fetched, real `template_json` is submitted to `POST /api/v1/theatres` | Editorial fields are still staged UI and do not persist |
| Blank | Deferred | Page shape is visible and explains deferral | Cannot author or submit a valid theatre from scratch yet |
| Alpamayo | Staged shell | Empty-state contract is present and uses the right product language | No backend suggestions yet |

Implementation note: blank/custom theatre authoring is not backend-valid today because create requires a full schema-valid template payload.

---

## 6. Archetype Mapping

File: `frontend/src/lib/archetypeMapping.ts`

Backend identity names are still normalized to frontend archetype buckets until taxonomy unification lands.

Examples:

| Backend Identity | Frontend Archetype |
|------------------|--------------------|
| `MEGALODON` | `SHARK` |
| `CARDINAL` | `SPY` |
| `AMBASSADOR` | `DIPLOMAT` |
| `VIPER` | `SABOTEUR` |
| `LEVIATHAN` | `WHALE` |
| unknown | `DEGEN` |

---

## 7. Implementation Notes

1. The shared `EmptyState` component is ready. Page-level detection remains local to each page or hook.
2. Theme migration to raw OKLCH tokens is not required before implementation handoff. Current code still uses semantic `terminal-*` / `status-*` tokens.
3. Do not invent Cycle 017 behavior in the frontend. Prefer empty, sparse, or feature-flagged states with explicit copy.
4. If a page is not yet wired, implement the empty-state contract first before adding richer mock structure.
5. Treat the route list above as canonical for implementation. Redirect cleanup can happen later.
6. Fleet's `Deploy Agent` CTA is not a real deployment backend flow yet. It currently opens a staged modal only.
