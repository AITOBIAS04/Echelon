# System Bible v13 — Registry Schema Expansion Notice

**Date:** 1 March 2026
**Applies to:** Echelon_System_Bible_v13.docx, Sections 15.5–15.7 (Composed Oracle, World Monitor, Schema Enforcement)
**Triggered by:** Intelligence Database Expansion v1.0.0 + Cycle-004 completion
**Status:** Normative notice — schema changes are specified, implementation is Cycle-005

---

## 1. Registry Schema Expansion: 19 → 28 Fields

The OSINT Source Registry schema (Section 15.7) currently defines 19 per-source fields. The Intelligence Database Expansion v1.0.0 adds 9 new optional fields. The schema remains backwards-compatible — parsers MUST ignore unknown fields, and the validator in non-strict mode infers defaults for missing new fields.

### New Fields Summary

| # | Field | Type | Default | Purpose |
|---|-------|------|---------|---------|
| 1 | `consumption_surfaces` | Array of objects | Inferred: `[theatre_settlement]` if `settlement_eligible`, else `[consumer_dashboard]` | Which of the 7 platform surfaces consume this source |
| 2 | `access_tier` | Enum: tier_a, tier_b, tier_c, paid | None (required for new sources) | Authentication requirement classification |
| 3 | `api_endpoint` | String or null | null | Actual callable base URL (overrides `api_url`) |
| 4 | `collector_status` | Enum: active, planned, enumerated | `planned` | Whether a working collector exists |
| 5 | `rate_limit_policy` | String or null | null (required for active/planned) | Rate limiting documentation |
| 6 | `dashboard_permitted` | Boolean | true for tier_a/b/c, false for paid | Whether source data can appear on consumer dashboard |
| 7 | `settlement_latest_only_override` | Boolean | false | Allows `settlement_eligible=true` despite `revision_policy=latest_only` |
| 8 | `settlement_requires_corroboration` | Boolean | false | Source cannot be sole settlement anchor |
| 9 | `independence_notes` | String or null | null | Free-text explaining upstream lineage decisions |

### Compatibility Contract

- Existing 19 fields are unchanged. No field removals, no type changes, no semantic changes.
- New fields are optional in non-strict mode. The validator infers defaults.
- In strict mode (v1.0.0+), all 28 fields must be present and valid.
- Parsers encountering unknown fields MUST ignore them (forward-compatibility for future expansions).

---

## 2. Source Group Expansion: 13 → 30

Section 15.7 defines 13 committed source groups. The expansion adds 17 new groups. The `source_group` field remains a committed enumeration (not free-text). An alias resolution map handles historical references (e.g., `court_record` → `judicial_record`).

### New Source Groups

| Group | Description |
|-------|-------------|
| `intellectual_property` | Patent grants, trademark registrations, IP ownership |
| `entity_resolution` | Corporate entity ID, LEI lookup, beneficial ownership |
| `geospatial_verification` | Building footprints, geocoding, planning data |
| `geophysical_hazard` | Earthquake, volcano, tsunami, geological hazards |
| `fire_emissions` | Active fire detection, emissions, air quality |
| `space_weather` | Solar activity, geomagnetic storms, GPS constellation |
| `infrastructure_critical` | Undersea cables, pipelines, power grids, telecoms |
| `sanctions_compliance` | Sanctions designations, export controls, compliance lists |
| `health_biosecurity` | Disease outbreaks, pandemic surveillance |
| `election_governance` | Election results, legislative votes, governance transitions |
| `energy_commodities` | Energy production, commodity prices, strategic reserves |
| `climate_weather` | Weather forecasting, climate anomalies, severe weather |
| `demographic_economic` | Census, population, economic indicators |
| `nuclear_wmd` | Nuclear facility monitoring, WMD treaty compliance |
| `protest_unrest` | Civil unrest, protest activity, political instability |
| `calendar_counter_signal` | Public holidays, scheduled events, counter-signal discounting |
| `judicial_record` | Court filings, insolvency notices, legal proceedings |

---

## 3. Settlement Guardrails (New Enforcement Rules)

Section 15.7 defines 5 schema enforcement rules. The following guardrails extend rules 1 and 5:

### Guardrail: revision_policy + settlement_eligible consistency

- `settlement_eligible=true` requires `receipt_mode_minimum` present.
- `settlement_eligible=true` requires `revision_policy` present.
- `revision_policy=latest_only` + `settlement_eligible=true` = **FAIL** unless `settlement_latest_only_override=true`.
- When override is active, the source receives 0.80x confidence penalty in the scorer (per AC-4).

### Guardrail: corroboration requirement enforcement

- `settlement_requires_corroboration=true` means this source cannot be the sole settlement anchor.
- At least one independent corroborating source must return an `EvidenceBundle`.
- Independence is evaluated AFTER the `independence_upstream_dedupe_runner` (rule 2).
- `GapKind.INTELLIGENCE_GAP` does not satisfy the corroboration requirement.

### Guardrail: dashboard_permitted defaults

- `access_tier` in (tier_a, tier_b, tier_c) → `dashboard_permitted` defaults to `true`.
- `access_tier=paid` → `dashboard_permitted` defaults to `false` unless explicitly set.
- This prevents paid-tier data from leaking to the consumer dashboard surface without explicit permission.

---

## 4. Cycle-004 Architectural Hardening — Completed

The OSINT pipeline (Section 15.5, Composed Oracle) has been architecturally hardened. 6 structural concerns resolved, 49 tests passing (37 architectural + 12 canonical), zero regressions.

| Concern | Resolution | Pipeline impact |
|---------|-----------|-----------------|
| AC-1: GapKind semantics | `GapKind.SIGNAL_ABSENCE` and `GapKind.INTELLIGENCE_GAP` distinguished throughout | Signal absence produces `EvidenceBundle`; intelligence gap produces `GapReport` |
| AC-2: Upstream dedup | `independence_upstream_dedupe_runner` operational | Corroboration counts `distinct_upstream_succeeded_count` |
| AC-3: Receipt enforcement | Non-bypassable in runner | Receipt below `receipt_mode_minimum` flagged as `receipt_mode_violation` |
| AC-4: Confidence capping | Moved from BaseCollector to Scorer | Penalties: immutable 1.0x, as_of_timestamp 0.95x, latest_only 0.80x. Single-source cap 0.95 |
| AC-5: Canonical hash | RFC 8785 + NFC normalisation | Deterministic across runs. Float precision and dict ordering invariant |
| AC-6: Timeout gap reports | Structured `GapReport` with `FailureMode` enum | No silent drops. Every source produces `EvidenceBundle` or `GapReport` |

### Files modified (in `~/Downloads/osint_pipeline/`)

| File | Changes |
|------|---------|
| `collectors/base.py` | GapKind mapping, FailureMode mapping, confidence cap removed |
| `engine/canonical.py` | NFC normalisation, RFC 8785 float encoder |
| `engine/collection_runner.py` | Runner-level receipt enforcement, structured timeout gaps |
| `engine/scorer.py` | **NEW.** EvidenceScorer with penalty matrix |
| `models/evidence.py` | FailureMode enum, gap_count/gap_sources, distinct_upstream_succeeded_count |
| `engine/__init__.py` | Exports |
| `models/__init__.py` | Exports |
| `tests/test_architectural_concerns.py` | 27 new + 2 updated tests |

---

## 5. Upcoming: Cycle-005 (Intelligence Database Expansion)

Registry expansion from 77 → 160+ sources. 9 new schema fields, 17 new source group enums, settlement guardrails enforced by hardened validator. Sprint plan ready. Depends on Cycle-004 completion (done).

---

## 6. Upcoming: Paradox Policy Extension

A `paradox_policy` object is proposed for the Theatre Template v-next to make the Paradox Engine inquiry-aware. Four modes (`disabled`, `enabled`, `advisory`, `circuit_breaker`), three logic gap sources (`simulation`, `osint`, `survey`), configurable thresholds, and an `activation_gate` that prevents premature Paradox firing in investigative and survey Theatres. See design note: `Echelon_Paradox_Policy_Design_Note_v1.md`. Implementation is post-Phase 3 (LMSR Market Engine).
