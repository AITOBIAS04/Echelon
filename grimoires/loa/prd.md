# PRD — Cycle-038: Cross-Theatre Paradox Detection

**Cycle:** cycle-038
**Date:** 19 March 2026
**Depends on:** Cycle-037d (theatre construct verification), Cycle-020 (ParadoxRiskOrchestrator), Cycle-010b (Paradox Engine)
**Sprints:** 4 (0-3)
**Builder:** Loa (backend only)
**Planning source:** context_038.md, codebase analysis of paradox engine, theatre model, evidence pipeline

> Sources: context_038.md, backend/engines/paradox.py, backend/services/paradox_risk_orchestrator.py, backend/database/models.py (Theatre, Paradox, WingFlap, Investigation)

---

## 1. Problem Statement

### 1.1 The Paradox Engine Is Theatre-Local

The current Paradox Engine (`backend/engines/paradox.py`) scans for logic gaps within a single theatre. The ParadoxRiskOrchestrator (`backend/services/paradox_risk_orchestrator.py`) computes risk per-theatre and emits `PARADOX_RISK_CHANGED` via WebSocket on materiality — but each theatre is an island. There is no mechanism to detect when two independently-operated theatres contradict each other about the same real-world event.

### 1.2 External Theatres Create Network-Level Integrity Requirements

With TREMOR (seismic) and CORONA (space weather) now verifiable via the 037d construct pipeline, Echelon has multiple independent theatre operators observing overlapping real-world domains. When TREMOR settles a magnitude-6.2 quake at a location and a second seismic theatre settles a conflicting magnitude for the same event, that is not a local logic gap — it is a network-level coherence failure that affects the credibility of every certificate downstream.

### 1.3 Same-Event Linking Is The Foundation

Cross-theatre paradox detection requires knowing when two theatres are observing the same real-world event. This is not trivial: different theatres may use different event identifiers, different temporal windows, and different oracle sources for the same underlying phenomenon. The linking quality determines the quality of every coherence signal built on top of it.

### 1.4 The Strategic Shift

The Paradox Engine becomes not just a theatre-local logic-gap detector but the **network referee across external verification environments**. This includes cross-domain overlaps: seismic activity in a region with no corresponding volcanic anomaly in an overlapping zone. The value is not domain expertise — it is that the engine can see when two independent specialists with overlapping scope diverge in a way worth escalation.

---

## 2. Product Contracts

### 2.1 Fact Anchors

A **FactAnchor** represents a real-world event or observation that one or more theatres may reference. It is the linking primitive.

| Field | Type | Description |
|---|---|---|
| `id` | UUID | Primary key |
| `anchor_type` | str | Event taxonomy (e.g., `seismic_event`, `solar_flare`, `corporate_filing`) |
| `external_id` | str | Canonical external identifier (e.g., USGS event ID `us6000abcd`) |
| `external_source` | str | Authoritative source (e.g., `usgs_neic`, `noaa_swpc`) |
| `occurred_at` | datetime | When the real-world event occurred |
| `location_json` | JSON | Optional geospatial/domain-specific location data |
| `metadata_json` | JSON | Source-specific metadata (magnitude, depth, flare class, etc.) |
| `created_at` | datetime | When the anchor was first recorded |

**FactAnchorLink** connects a theatre's settlement or evidence to a FactAnchor:

| Field | Type | Description |
|---|---|---|
| `id` | UUID | Primary key |
| `fact_anchor_id` | FK → FactAnchor | The real-world event |
| `theatre_id` | FK → Theatre | The theatre referencing this event |
| `link_type` | str | `settlement`, `evidence`, `oracle_query` |
| `link_confidence` | float | 0.0–1.0, how confident the match is |
| `linked_entity_id` | str | Polymorphic FK to the theatre-side record |
| `linked_entity_type` | str | `theatre_outcome`, `evidence_item`, `oracle_response` |
| `created_at` | datetime | When the link was established |

Design rules:
- A FactAnchor can be linked to multiple theatres (many-to-many via FactAnchorLink)
- Links can be established retroactively when new evidence arrives
- `link_confidence` enables soft matching (e.g., USGS automatic vs reviewed event IDs for the same quake)

### 2.2 Coherence Groups

A **CoherenceGroup** declares that a set of theatres should produce consistent outputs for overlapping observations. This is the structural declaration that enables cross-theatre comparison.

| Field | Type | Description |
|---|---|---|
| `id` | UUID | Primary key |
| `name` | str | Human-readable label (e.g., `seismic-pacific-ring`) |
| `group_type` | str | `domain_overlap`, `oracle_shared`, `geographic_overlap` |
| `policy_json` | JSON | Coherence thresholds and comparison rules |
| `created_at` | datetime | When the group was defined |

**CoherenceGroupMember** links theatres to groups:

| Field | Type | Description |
|---|---|---|
| `id` | UUID | Primary key |
| `coherence_group_id` | FK → CoherenceGroup | The group |
| `theatre_id` | FK → Theatre | The member theatre |
| `role` | str | `primary`, `cross_validation`, `observer` |
| `joined_at` | datetime | When the theatre joined the group |

Design rules:
- A theatre can belong to multiple coherence groups
- Groups can span domains (seismic + volcanic for geographic overlap)
- `policy_json` declares tolerance thresholds per comparison dimension

### 2.3 Cross-Theatre Paradox Records

A **CrossTheatreParadox** is the output when the engine detects a network-level coherence failure. It is distinct from the existing per-theatre Paradox model.

| Field | Type | Description |
|---|---|---|
| `id` | UUID | Primary key |
| `fact_anchor_id` | FK → FactAnchor | The real-world event at the center |
| `coherence_group_id` | FK → CoherenceGroup (nullable) | Group context, if applicable |
| `paradox_type` | str | `settlement_divergence`, `oracle_inconsistency`, `scope_overlap_gap`, `temporal_drift` |
| `severity` | str | `INFO`, `WATCH`, `MATERIAL`, `CRITICAL` |
| `theatre_a_id` | FK → Theatre | First theatre |
| `theatre_b_id` | FK → Theatre | Second theatre |
| `description` | str | Human-readable explanation |
| `evidence_json` | JSON | Structured divergence evidence (values, sources, timestamps) |
| `resolution_status` | str | `OPEN`, `ACKNOWLEDGED`, `RESOLVED`, `DISMISSED` |
| `resolved_at` | datetime (nullable) | When resolved |
| `created_at` | datetime | When detected |

Design rules:
- A CrossTheatreParadox always references exactly two theatres and (usually) one FactAnchor
- Provisional oracle revision (e.g., USGS automatic → reviewed) is `INFO` severity, not `MATERIAL` — per context_038.md rule
- Resolution preserves provenance: **why** the theatres disagreed, not just that they did

### 2.4 Cross-Theatre Paradox Scanner

Add `backend/services/cross_theatre_paradox_scanner.py`:

```
class CrossTheatreParadoxScanner:
    """Detects coherence failures across theatres sharing FactAnchors."""

    async def scan_fact_anchor(anchor_id) → list[CrossTheatreParadox]
    async def scan_coherence_group(group_id) → list[CrossTheatreParadox]
    async def evaluate_settlement_divergence(anchor, links) → Optional[CrossTheatreParadox]
    async def evaluate_oracle_inconsistency(anchor, links) → Optional[CrossTheatreParadox]
    async def evaluate_scope_overlap(group, anchors) → list[CrossTheatreParadox]
```

Detection patterns:

| Pattern | Trigger | Severity Logic |
|---|---|---|
| Settlement divergence | Two theatres settle opposite outcomes for same FactAnchor | MATERIAL if both ACTIVE, WATCH if one superseded |
| Oracle inconsistency | Same oracle source returns different values to different theatres for same event | MATERIAL if delta > threshold, INFO if within tolerance |
| Scope overlap gap | Coherence group expects correlated events but one theatre has no corresponding anchor | WATCH (absence is suspicious, not contradictory) |
| Temporal drift | Same event settled at significantly different times across theatres | INFO unless delta > settlement window |

### 2.5 Oracle Consistency Monitor

Add `backend/services/oracle_consistency_monitor.py`:

```
class OracleConsistencyMonitor:
    """Tracks oracle source responses across theatres for consistency."""

    async def record_oracle_response(theatre_id, source, event_id, value, timestamp)
    async def check_consistency(source, event_id) → ConsistencyResult
    async def get_divergence_history(source, window) → list[DivergenceRecord]
```

This service tracks when different theatres query the same oracle source for the same event and records whether the responses agree. It feeds directly into the CrossTheatreParadoxScanner's oracle inconsistency detection.

### 2.6 Integration with Existing Paradox Infrastructure

The cross-theatre scanner extends — does not replace — existing infrastructure:

- **ParadoxRiskOrchestrator** continues to compute per-theatre risk. It gains a new input: `cross_theatre_exposure` derived from open CrossTheatreParadox records affecting the theatre
- **WingFlap** gains a new type: `CROSS_THEATRE_PARADOX` to audit cross-theatre events
- **WebSocket** emission: `CROSS_THEATRE_PARADOX_DETECTED` event on new MATERIAL or CRITICAL findings
- **Material-delta gating** preserved: only emit on severity change, not on every scan

### 2.7 TREMOR As First Domain Fixture

TREMOR seismic events are the first domain fixture because they have:
- Excellent public ground truth (USGS reviewed catalog)
- High event cadence (multiple M4+ events per day globally)
- Machine-readable feeds (FDSN web services)
- Clear oracle divergence cases (USGS automatic vs reviewed, USGS vs EMSC)

The test suite uses TREMOR-style events to validate:
- FactAnchor creation from USGS event IDs
- Cross-linking when two theatres observe the same quake
- Settlement divergence detection when magnitude classifications differ
- Oracle consistency between USGS and EMSC for the same event

---

## 3. What This Cycle Does NOT Do

- **Does NOT modify the per-theatre Paradox Engine** (theatre-local logic gap scanning stays untouched)
- **Does NOT add real-time oracle polling** (oracle responses are recorded when theatres settle, not polled proactively)
- **Does NOT implement automated resolution** (cross-theatre paradoxes are detected and recorded; resolution is human-initiated or future-cycle)
- **Does NOT add settlement cascade logic** (when one theatre's paradox invalidates another's settlement — that is a separate concern)
- **Does NOT require external theatre runtime changes** (TREMOR/CORONA do not need modification; linking happens on Echelon's side)

---

## 4. Acceptance Criteria

1. `FactAnchor` and `FactAnchorLink` models created with Alembic migration
2. `CoherenceGroup` and `CoherenceGroupMember` models created with Alembic migration
3. `CrossTheatreParadox` model created with Alembic migration
4. `CrossTheatreParadoxScanner` detects settlement divergence across two theatres sharing a FactAnchor
5. `CrossTheatreParadoxScanner` detects oracle inconsistency for same-source same-event queries
6. `OracleConsistencyMonitor` records and compares oracle responses across theatres
7. Provisional oracle revision (automatic → reviewed) classified as INFO, not MATERIAL
8. WingFlap records `CROSS_THEATRE_PARADOX` events
9. WebSocket emits `CROSS_THEATRE_PARADOX_DETECTED` on MATERIAL findings (material-delta gated)
10. ParadoxRiskOrchestrator incorporates cross_theatre_exposure in per-theatre risk
11. TREMOR-based test fixtures validate all detection patterns
12. All existing paradox/theatre/contract tests pass unchanged (zero regression)
13. >= 30 new tests

---

## 5. Test Plan

| Area | Tests | Coverage |
|---|---|---|
| FactAnchor CRUD | 4 | create, link, multi-theatre link, confidence filtering |
| CoherenceGroup management | 4 | create group, add members, multi-group membership, policy validation |
| Settlement divergence detection | 5 | same anchor opposite outcomes, same outcome no paradox, superseded theatre dampening, severity classification, provenance capture |
| Oracle inconsistency detection | 4 | same source different values, within tolerance no paradox, cross-source comparison, temporal window |
| Scope overlap gap detection | 3 | expected correlated anchor missing, both present no gap, cross-domain overlap |
| Oracle consistency monitor | 4 | record response, check consistency, divergence history, stale response handling |
| Cross-theatre risk integration | 3 | exposure feeds into orchestrator, material-delta gating, WingFlap audit |
| WebSocket emission | 2 | MATERIAL triggers emission, INFO does not |
| TREMOR fixture | 4 | USGS anchor creation, two-theatre linking, magnitude divergence, USGS vs EMSC consistency |
| Regression | 3 | per-theatre paradox unchanged, contract pipeline unaffected, evidence freshness unaffected |
| **Total** | **~36** | |

---

## 6. Dependency Chain

```
010b (Paradox Engine + Logic Gap)
 └── 020 (ParadoxRiskOrchestrator + PARADOX_RISK_CHANGED WebSocket)
      └── 037d (Theatre Construct Verification)
           └── 038 (Cross-Theatre Paradox Detection) ← THIS CYCLE
                └── 039 (Settlement Cascade + Automated Resolution) [future]
```

---

## 7. Why This Matters

When TREMOR settles a magnitude-6.2 quake and a second seismic theatre settles magnitude-5.8 for the same event, that contradiction is invisible today. Every certificate issued by both theatres carries an undetected coherence risk. This cycle makes that contradiction explicit, recorded, and auditable.

The Paradox Engine evolves from "does this theatre contradict itself?" to "does this theatre contradict the network?" That is the shift from local correctness to network integrity — and it is what makes Echelon's multi-theatre architecture trustworthy at scale.
