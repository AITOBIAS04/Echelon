# WorldMonitor -> Echelon OSINT Integration Log

**Status:** Active operating log
**Purpose:** Track WorldMonitor feature/layer updates for batch integration into Echelon's OSINT registry and collector surfaces.
**Rule:** Log immediately on notable WorldMonitor release. Implement in batch during an OSINT registry expansion cycle or dedicated collector cycle.
**Canonical companion note:** `grimoires/loa/context/osint_registry_expansion_research_notes.md`

---

## Operating Rules

1. Log the WorldMonitor update on the day it ships.
2. Map it to an Echelon source group and domain filter immediately.
3. Mark whether it is:
   - `NEW_SOURCE`
   - `ENHANCEMENT`
   - `NEEDS_UPSTREAM_REVIEW`
4. Do not implement ad hoc in the middle of an unrelated cycle unless it is explicitly pulled into scope.
5. Do not use `backend/core/synthetic_osint.py` for live integration planning. Synthetic OSINT is test/mock support only.
6. If a layer is only an enhancement to an existing upstream, update the existing registry entry or collector notes instead of inventing a duplicate source.

---

## Pending

| Date Logged | WM Feature | Echelon Source Group | Domain Filter | Type | Status | Notes |
|---|---|---|---|---|---|---|
| 2026-03-08 | Stocks analysis suite | `market_data` | Finance and Markets | NEW_SOURCE | Pending registry entry | Extends finance/markets coverage. Add when API surface and independence characteristics are stable. |
| 2026-03-08 | Orbital surveillance (satellite data) | `satellite_imagery` | Satellite and Earth Observation | NEW_SOURCE | Pending registry entry | High value for maritime, geopolitical, and infrastructure investigations. Candidate for theatre, investigation, and world monitor enrichment. |
| 2026-03-08 | Improved military/civilian airlines layer | `flight_tracking` | Airspace | ENHANCEMENT | Check upstream independence | Could be a processing improvement over existing ADS-B/OpenSky coverage rather than a new independent source. Verify before adding a new registry row. |
| 2026-03-08 | GPS jamming layer | `signals_intelligence` | Airspace / Geopolitical and Conflict | NEW_SOURCE | Pending registry entry | No current direct registry equivalent. Determine whether it belongs under a new source group or an extension of the flight-tracking/intel stack. |

---

## Integrated

| Date Logged | Date Integrated | WM Feature | Registry Entry / Collector Change | Cycle / Batch | Notes |
|---|---|---|---|---|---|
| — | — | — | — | — | — |

---

## Source Group Mapping Reference

| WM Layer Category | Echelon Source Group | Primary Domain Filter |
|---|---|---|
| Geopolitics / conflicts | `conflict_event` | Geopolitical and Conflict |
| Military flights / civilian air activity | `flight_tracking` | Airspace |
| Naval / AIS | `maritime_ais` | Maritime |
| Earth observation / orbital / satellite | `satellite_imagery` | Satellite and Earth Observation |
| Financial / equities / macro signals | `market_data` | Finance and Markets |
| Cyber / interference / GPS jamming | `signals_intelligence` | Airspace or Geopolitical and Conflict |
| News / GDELT / media monitoring | `news_event` | Geopolitical and Conflict |

---

## Batch Review Checklist

Use this checklist when a registry-expansion or collector cycle picks up pending items:

- Is this a new independent upstream or only an enhancement to an existing one?
- Which `source_group` should own it?
- Which `DomainFilter` values should consume it?
- Does it require a new collector, or only a registry/source-manifest addition?
- What is its `independence_upstream_id`?
- Does it imply `requires_legal_review`, `query_determinism`, or `receipt_body_required` changes?
- Should it enrich World Monitor only, Investigation ingestion only, or both?

