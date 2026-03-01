# Sprint Plan: Intelligence Database Expansion v1.0.0

> **Cycle:** cycle-005
> **PRD:** `grimoires/loa/prd.md`
> **SDD:** `grimoires/loa/sdd.md`
> **Date:** 2026-03-02
> **Sprints:** 2 (global IDs: 9-10)
> **Team:** Single AI agent
> **Monorepo target:** `~/Developer/prediction-market-monorepo.nosync/`
> **Pipeline target:** `~/Downloads/osint_pipeline/`

---

## Sprint 1: Schema Extension + Priority 1 Sources (8 tasks)

**Goal:** Extend registry schema with 9 new fields, expand source groups to 30, backfill existing 77 sources, add 18 Priority 1 sources, harden validator. No regressions.

**Build order:** T1.1 → T1.2 → T1.3 → T1.4 → T1.5 → T1.6 → T1.7 → T1.8

**Rationale:**
- T1.1 first: schema fields + model must exist before any source can use them
- T1.2 before T1.3: new groups committed before backfilling sources into them
- T1.3 before T1.4-T1.7: backfill establishes field patterns for new entries
- T1.8 last: validator validates all previous work

---

### Task 1: T1.1 — Schema Extension: 9 New Fields + RegistrySource Model

**Files:**
- `echelon_osint_source_registry_v1_0_0.json` (NEW — copy from v0.6.0 as base) at `theatre/fixtures/two_rail_theatres_v0_1/datasets/`
- `models/registry.py` at `~/Downloads/osint_pipeline/`
- `models/__init__.py` at `~/Downloads/osint_pipeline/`

**Work:**
1. Copy `echelon_osint_source_registry_v0_6_0.json` → `echelon_osint_source_registry_v1_0_0.json`
2. Bump `"version"` to `"1.0.0"` in header
3. Add top-level enum definitions: `consumption_surface_enum`, `quality_tier_enum`, `access_tier_enum`, `collector_status_enum`
4. Add 9 new fields to `RegistrySource` Pydantic model with correct defaults
5. Add query methods to `RegistryLoader`: `by_access_tier()`, `by_collector_status()`, `by_consumption_surface()`, `active_sources()`, `settlement_sources_requiring_corroboration()`
6. Update `models/__init__.py` exports

**Acceptance criteria:**
- [x] v1.0.0 registry JSON created with version bump and top-level enums
- [x] `RegistrySource` has 9 new optional fields with correct defaults
- [x] Existing v0.6.0 sources load without error in the model (backwards compatible)
- [x] 5 new query methods on `RegistryLoader` work correctly
- [x] `consumption_surfaces` defaults to empty list
- [x] `access_tier` defaults to `"tier_a"`
- [x] `collector_status` defaults to `"planned"`
- [x] `dashboard_permitted` defaults to `true`
- [x] `settlement_latest_only_override` and `settlement_requires_corroboration` default to `false`

---

### Task 2: T1.2 — Source Group Enum Expansion: 16 → 30

**Files:**
- `echelon_osint_source_registry_v1_0_0.json` — `source_group_enum` section

**Work:**
1. Promote `judicial_record` and `calendar_counter_signal` from `proposed_extensions` to `committed_values`
2. Add 12 new committed groups: `intellectual_property`, `entity_resolution`, `geospatial_verification`, `geophysical_hazard`, `fire_emissions`, `space_weather`, `infrastructure_critical`, `sanctions_compliance`, `health_biosecurity`, `election_governance`, `energy_commodities`, `climate_weather`
3. Retain `demographic_economic`, `nuclear_wmd`, `protest_unrest` as additional committed groups (total 30+)
4. Remove `proposed_extensions` section (all promoted)

**Acceptance criteria:**
- [x] `committed_values` has 30+ entries
- [x] `proposed_extensions` is empty or removed
- [x] All 17 new groups present: `judicial_record`, `calendar_counter_signal`, `intellectual_property`, `entity_resolution`, `geospatial_verification`, `geophysical_hazard`, `fire_emissions`, `space_weather`, `infrastructure_critical`, `sanctions_compliance`, `health_biosecurity`, `election_governance`, `energy_commodities`, `climate_weather`, `demographic_economic`, `nuclear_wmd`, `protest_unrest`
- [x] Existing 16 groups unchanged

---

### Task 3: T1.3 — Backfill Existing 77 Sources with New Fields

**Files:**
- `echelon_osint_source_registry_v1_0_0.json` — all 77 existing source entries

**Work:**
For each existing source, add:
- `consumption_surfaces` array (which surfaces this source serves)
- `access_tier` (tier_a / tier_b / tier_c / paid based on auth requirements)
- `api_endpoint` (base URL, no query strings)
- `collector_status` (`"active"` for Companies House + any other Cycle-002 collectors; `"planned"` for rest)
- `rate_limit_policy` (required for active/planned; document known limits)
- `dashboard_permitted` (true for non-paid)
- `settlement_latest_only_override`, `settlement_requires_corroboration`, `independence_notes` where applicable

**Acceptance criteria:**
- [x] All 77 sources have non-empty `consumption_surfaces`
- [x] No source missing `access_tier`
- [x] Settlement-eligible sources include `theatre_settlement` surface
- [x] `api_endpoint` values are base URLs only (no `?` or `#`)
- [x] Companies House collector: `collector_status: "active"`
- [x] Paid sources: `dashboard_permitted: false` unless explicitly overridden

---

### Task 4: T1.4 — Priority 1 Sources: Sanctions Cluster (4 new)

**Files:**
- `echelon_osint_source_registry_v1_0_0.json` — add 4 entries

**Sources:** ofac_sdn_api, eu_sanctions_list, uk_ofsi_list, opensanctions_api

**Acceptance criteria:**
- [x] 4 sources added with full 28-field schema
- [x] Each has unique `independence_upstream_id`
- [x] OFAC, EU, UK: `settlement_eligible: true`, `revision_policy: "as_of_timestamp"`, `receipt_mode_minimum: "http_transcript"`
- [x] OpenSanctions: `settlement_eligible: false` (aggregator)
- [x] OFAC: `consumption_surfaces` has 7/7 surface coverage
- [x] All in `source_group: "sanctions_compliance"`
- [x] `collector_status: "planned"` for all

---

### Task 5: T1.5 — Priority 1 Sources: Geopolitical + Health (4 new)

**Files:**
- `echelon_osint_source_registry_v1_0_0.json` — add 4 entries

**Sources:** who_disease_outbreak, noaa_nws_alerts, wikidata_sparql, imf_sdmx_api

**Acceptance criteria:**
- [x] 4 sources added with full schema
- [x] Wikidata: `settlement_requires_corroboration: true`, `settlement_eligible: true`, `revision_policy: "as_of_timestamp"`
- [x] IMF: `revision_policy: "immutable"`, `settlement_eligible: true`
- [x] WHO + NOAA: `settlement_eligible: false`
- [x] Each has appropriate `source_group` and `consumption_surfaces`

---

### Task 6: T1.6 — Priority 1 Sources: Property + Entity (4 new)

**Files:**
- `echelon_osint_source_registry_v1_0_0.json` — add 4 entries

**Sources:** planning_data_uk, gleif_api, openmeteo_api, nager_date_api

**Acceptance criteria:**
- [x] 4 sources added with full schema
- [x] Planning Data UK + GLEIF: `settlement_eligible: true`
- [x] Open-Meteo + Nager.Date: `settlement_eligible: false`
- [x] Nager.Date: `resolution_role: "counter_signal"`, `counter_signal_class: "calendar_holiday"`, `source_group: "calendar_counter_signal"`
- [x] GLEIF: `source_group: "entity_resolution"`
- [x] `api_endpoint` values are base URLs only

---

### Task 7: T1.7 — Priority 1 Sources: Remaining High-Coverage (6 new)

**Files:**
- `echelon_osint_source_registry_v1_0_0.json` — add 6 entries (or backfill if existing)

**Sources:** eurostat_api, eia_api, sam_gov_api, un_sanctions_sc, promed_rss, reliefweb_api

**Acceptance criteria:**
- [x] 6 sources added or backfilled (check for existing `reliefweb_api`)
- [x] ReliefWeb: `source_group: "geophysical_hazard"` (NOT protest_unrest)
- [x] No duplicate `source_id` entries
- [x] Settlement-eligible sources pass guardrails
- [x] EIA: `access_tier: "tier_b"` (requires API key)
- [x] SAM.gov: `access_tier: "tier_b"` (requires API key)

---

### Task 8: T1.8 — Validator Update: Full v1.0.0 Enforcement

**Files:**
- `tools/validate_osint_registry.py`
- `tests/test_registry_expansion.py` (NEW) at `~/Downloads/osint_pipeline/tests/`

**Work:**
1. Bump `__version__` to `"1.0.0"`
2. Add enum validation for 9 new fields
3. Add `api_endpoint` guard (reject `?` and `#`)
4. Strengthen settlement guardrails (receipt_mode + revision_policy required)
5. Add `settlement_latest_only_override` logic
6. Add `settlement_requires_corroboration` warning
7. Add `rate_limit_policy` enforcement (required for active/planned, optional for enumerated)
8. Add source group alias resolution (`SOURCE_GROUP_ALIASES` mapping)
9. Add strict mode: reject empty `consumption_surfaces`, require `access_tier`, `collector_status`
10. Add non-strict inference + warnings
11. Add `--fix-summary` mode for auto-computing summary counts
12. Add duplicate `api_endpoint` warning
13. Update summary count validation to include new fields
14. Write 11+ new tests

**Acceptance criteria:**
- [x] Validator version `1.0.0`
- [x] `consumption_surface_enum` validation working
- [x] `quality_tier_enum` validation working
- [x] `access_tier_enum` validation working
- [x] `collector_status_enum` validation working
- [x] `api_endpoint` with `?` or `#` → error
- [x] `settlement_eligible=true` without `receipt_mode_minimum` → error
- [x] `settlement_eligible=true` without `revision_policy` → error
- [x] `latest_only` + `settlement_eligible` without override → error
- [x] `settlement_requires_corroboration=true` → warning (not error)
- [x] Active/planned source without `rate_limit_policy` → warning
- [x] `court_record` alias resolves to `judicial_record`
- [x] `--strict` rejects empty `consumption_surfaces`
- [x] `--fix-summary` computes correct counts
- [x] Summary count mismatch → error
- [x] Duplicate `api_endpoint` → warning
- [x] All existing 49 pipeline tests still pass
- [x] v0.6.0 registry passes validator in non-strict mode (backwards compat)

**Tests (new — 11+):**
- `test_backwards_compat_v060_loads`
- `test_settlement_guardrail_receipt_mode`
- `test_settlement_guardrail_latest_only_without_override`
- `test_settlement_guardrail_latest_only_with_override`
- `test_settlement_requires_corroboration_warning`
- `test_source_group_alias_resolution`
- `test_consumption_surfaces_inference_warning`
- `test_dashboard_permitted_default_paid`
- `test_api_endpoint_rejects_query_string`
- `test_rate_limit_policy_required_for_active`
- `test_summary_header_mismatch_fails`
- `test_registry_source_model_new_fields`
- `test_registry_loader_by_consumption_surface`

---

## Sprint 2: Priority 2+3 Sources + Version Bump (4 tasks)

**Goal:** Add 25 Priority 2 sources, 20+ Priority 3 enumerated sources, recompute summary, run strict validation. Registry reaches 160+ sources at v1.0.0.

**Build order:** T2.1 → T2.2 → T2.3 → T2.4

---

### Task 9: T2.1 — Priority 2 Sources: Settlement Layer Gaps (10 new)

**Files:**
- `echelon_osint_source_registry_v1_0_0.json` — add 10 entries

**Sources:** uk_caselaw_tna, uk_legislation_gov, uk_parliament_bills, usa_spending_api, patent_view_api, sec_xbrl_companyfacts, ons_api, hm_land_registry_ppd, overpass_api, nominatim_api

**Acceptance criteria:**
- [x] 10 sources added with full 28-field schema
- [x] 6 are settlement-eligible (uk_caselaw_tna, uk_legislation_gov, uk_parliament_bills, usa_spending_api, patent_view_api, sec_xbrl_companyfacts)
- [x] Rate limits documented honestly (Nominatim: `"1 req/s"`, Overpass: `"fair use ~10,000/day"`, SEC: `"10 req/s with user-agent"`)
- [x] All `collector_status: "planned"`
- [x] Settlement guardrails pass for all 6 settlement-eligible sources

---

### Task 10: T2.2 — Priority 2 Sources: Mission Factory + DeltaBrief Breadth (15 new)

**Files:**
- `echelon_osint_source_registry_v1_0_0.json` — add 15 entries

**Sources:** nasa_eonet_api, noaa_swpc_api, emsc_earthquake_api, aisstream_io, celestrak_gp, oecd_api, bis_statistics, who_gho_api, iea_api, courtlistener_api, opencorporates_api, fca_register, open_ownership_api, met_office_datapoint, spacelaunchnow_api

**Acceptance criteria:**
- [x] 15 sources added with full schema
- [x] CourtListener: `independence_upstream_id: "us_pacer_cm_ecf"`, `independence_notes` present, `resolution_role: "secondary_corroboration"`
- [x] OpenCorporates: `access_tier: "tier_c"` (50 req/day anon)
- [x] Each source has appropriate `source_group` and `consumption_surfaces`
- [x] No duplicate `source_id` entries

---

### Task 11: T2.3 — Priority 3 Sources: Enumerate Only (20+ new)

**Files:**
- `echelon_osint_source_registry_v1_0_0.json` — add 20+ entries

**Sources:** ISS Location, N2YO, TeleGeography Cables, Volcano Discovery RSS, Space-Track.org, CTBTO, SimFin, Alpha Vantage, CryptoCompare, Destatis, ABS, CDC WONDER, World Inequality DB, OPEC MOMR, OpenAQ, Copernicus CAMS, and others

**Acceptance criteria:**
- [x] 20+ sources added as `collector_status: "enumerated"` (64 enumerated)
- [x] `rate_limit_policy` optional for enumerated (no warnings)
- [x] Full metadata present (source_group, access_tier, consumption_surfaces, jurisdiction, etc.)
- [x] Validator passes

---

### Task 12: T2.4 — Registry Summary Update + Version Bump

**Files:**
- `echelon_osint_source_registry_v1_0_0.json` — summary section

**Work:**
1. Run `validate_osint_registry.py --fix-summary` to auto-compute all summary counts
2. Verify computed summary matches expected ranges:
   - `total_sources >= 160`
   - `by_access_tier.tier_a >= 90`
   - `settlement_eligible_count >= 29`
   - `source_group_count >= 30`
3. Run `--strict` to confirm all sources fully populated
4. Final version verification: `"version": "1.0.0"`

**Acceptance criteria:**
- [x] Summary section auto-computed by validator
- [x] `total_sources >= 160` (161)
- [x] `settlement_eligible_count >= 29` (40)
- [x] `source_group_count >= 30` (31)
- [x] `jurisdictions` includes at least: AE, AU, CA, DE, EU, GB, GLOBAL, HK, SG, US
- [x] Validator `--strict` passes on complete v1.0.0 registry
- [x] Validator `--fix-summary` and `--strict` both pass
- [x] All 49 existing pipeline tests pass (62/62)
- [x] All 11+ new registry tests pass (62/62)

---

## Summary

| Task | Sprint | Files Modified | New Tests |
|------|--------|----------------|-----------|
| T1.1 | 1 | registry JSON (new), models/registry.py, models/__init__.py | 2 |
| T1.2 | 1 | registry JSON | 0 |
| T1.3 | 1 | registry JSON | 0 |
| T1.4 | 1 | registry JSON | 0 |
| T1.5 | 1 | registry JSON | 0 |
| T1.6 | 1 | registry JSON | 0 |
| T1.7 | 1 | registry JSON | 0 |
| T1.8 | 1 | validate_osint_registry.py, test_registry_expansion.py (new) | 13 |
| T2.1 | 2 | registry JSON | 0 |
| T2.2 | 2 | registry JSON | 0 |
| T2.3 | 2 | registry JSON | 0 |
| T2.4 | 2 | registry JSON | 0 |
| **Total** | | **4 files (2 new)** | **13 new + 49 existing = 62** |

---

## Build Order

### Sprint 1
```
T1.1 (Schema + Model)
 → T1.2 (Source Groups)
   → T1.3 (Backfill 77)
     → T1.4 (Sanctions x4)
       → T1.5 (Geo+Health x4)
         → T1.6 (Property+Entity x4)
           → T1.7 (High-Coverage x6)
             → T1.8 (Validator + Tests)
```

### Sprint 2
```
T2.1 (P2 Settlement x10)
 → T2.2 (P2 Breadth x15)
   → T2.3 (P3 Enumerated x20+)
     → T2.4 (Summary + Version Bump)
```
