# PRD: Intelligence Database Expansion v1.0.0 (Cycle-005)

**Cycle:** 005
**Type:** Registry expansion + validator hardening
**Date:** 2026-03-02
**Predecessor:** Cycle-004 (Architectural Hardening — 6 concerns, 49 tests), Cycle-003 (Registry v0.6.0 merge — 77 sources), Cycle-002 (Pipeline skeleton — 3-stage engine)
**Location:** `~/Downloads/osint_pipeline/` (pipeline code, models, tests) + `~/Developer/prediction-market-monorepo.nosync/` (registry JSON, validator, fixtures)

---

## 1. Problem Statement

The OSINT Source Registry (v0.6.0, 77 sources, 16 source groups) was designed to answer one question: can this source settle a Theatre? That settlement-only framing starves six other product surfaces of intelligence. Echelon is a prediction market platform, an intelligence platform, and a verification platform — every surface consumes data differently, and every source has value beyond settlement.

This cycle reframes the registry from a settlement catalogue into a full-platform intelligence database:
- **77 → 160+ sources** across 30 source groups (17 new)
- **9 new schema fields** (consumption_surfaces, access_tier, api_endpoint, collector_status, rate_limit_policy, dashboard_permitted, settlement_latest_only_override, settlement_requires_corroboration, independence_notes)
- **7 consumption surfaces** (theatre_settlement, mission_factory, bounded_inquiry, delta_brief, agent_context, consumer_dashboard, sponsored_theatre)
- **Access tier classification** (Tier A/B/C/paid) replacing informal free/paid distinction
- **Settlement guardrails** preventing mutable sources from claiming settlement eligibility without compensating controls
- **Validator hardening** with strict mode, summary auto-computation, alias resolution, and backwards compatibility

> Sources: Echelon_Intelligence_Database_Expansion_v1_0.md, echelon_cycle_005_registry_expansion_plan.md

---

## 2. Goals & Success Criteria

| # | Goal | Measurement |
|---|------|-------------|
| SC-1 | Registry contains 160+ sources with full schema | `total_sources >= 160` in validator output |
| SC-2 | All 30 source_group enum values accepted | Validator passes with 30 committed values |
| SC-3 | Every source has non-empty consumption_surfaces | `--strict` mode rejects empty arrays |
| SC-4 | Every source has access_tier and collector_status | `--strict` mode enforces |
| SC-5 | Settlement guardrails enforced | `settlement_eligible=true` requires `receipt_mode_minimum` + `revision_policy`; `latest_only` blocks unless overridden |
| SC-6 | Backwards compatibility preserved | v0.6.0 registry passes validator in non-strict mode without modification |
| SC-7 | Summary header counts validator-computed | `--fix-summary` recomputes; manual counts fail validation |
| SC-8 | Source group aliases resolve correctly | `court_record` → `judicial_record`, `government_registry` → `official_gov` |
| SC-9 | api_endpoint values are base URLs only | Validator rejects `?` or `#` in api_endpoint |
| SC-10 | All existing 49 pipeline tests still pass | Zero regressions |
| SC-11 | 11+ new validator/registry tests added | Test count verified |

---

## 3. Scope

### In Scope

- 9 new optional fields on per-source schema
- 17 new source_group enum values (13 → 30 total committed)
- Source group alias resolution in validator
- Backfill existing 77 sources with new fields
- 18 Priority 1 new sources (5+ surfaces, Tier A/B)
- 25 Priority 2 new sources (4 surfaces)
- 20+ Priority 3 sources (enumerated only, no collector planned)
- Validator update: settlement guardrails, strict mode, `--fix-summary`, duplicate detection
- `RegistrySource` model extension in `models/registry.py`
- 11+ new tests

### Out of Scope

- New collectors (Cycle-006+)
- Pipeline engine changes
- CLI changes
- Frontend/deployment changes
- WorldMonitor integration (deferred to post-first-live-certificate)
- Paid/enterprise source subscriptions

---

## 4. Requirements

### 4.1 Schema Extension — 9 New Fields

**Current state:** `RegistrySource` model (`models/registry.py:17-38`) has 19 fields. Registry JSON (`echelon_osint_source_registry_v0_6_0.json`) has 77 sources with these fields.

**Required changes:**

Add 9 new OPTIONAL fields to both the registry JSON schema and the `RegistrySource` Pydantic model:

| Field | Type | Default | Purpose |
|-------|------|---------|---------|
| `consumption_surfaces` | `list[dict]` | `[]` | Array of `{surface, quality_tier, update_interval_seconds, notes}` |
| `access_tier` | `str` enum | `"tier_a"` | `tier_a` / `tier_b` / `tier_c` / `paid` |
| `api_endpoint` | `str \| None` | `None` | Base URL only (scheme+host+path). No query strings or fragments |
| `collector_status` | `str` enum | `"planned"` | `active` / `planned` / `enumerated` |
| `rate_limit_policy` | `str \| None` | `None` | Approximate rate limit description |
| `dashboard_permitted` | `bool` | inferred | `true` for free tiers, `false` for paid unless explicit |
| `settlement_latest_only_override` | `bool` | `false` | Allows `settlement_eligible=true` despite `latest_only` |
| `settlement_requires_corroboration` | `bool` | `false` | Source cannot be sole settlement anchor |
| `independence_notes` | `str \| None` | `None` | Free-text independence documentation |

**Compatibility contract:**
- Parsers MUST ignore unknown fields
- All 9 new fields are OPTIONAL — missing fields validate with safe defaults
- `consumption_surfaces` missing/empty in non-strict mode: infer from `settlement_eligible` + warn
- `collector_status` missing: assume `planned`
- `dashboard_permitted` missing: infer from `access_tier` (true unless paid)

**Acceptance criteria:**
- Existing v0.6.0 registry passes validator without modification
- New fields accepted when present
- `api_endpoint` with query strings (`?` or `#`) rejected
- `RegistrySource` model accepts all 9 new fields with correct defaults

---

### 4.2 Source Group Expansion — 13 → 30

**Current state:** `source_group_enum.committed_values` has 16 entries (including `court_record`, `financial_regulator`, `government_registry`). Two proposed extensions: `judicial_record`, `calendar_counter_signal`.

**Required changes:**

1. Promote `judicial_record` and `calendar_counter_signal` from proposed to committed
2. Add 15 new committed groups:

```
intellectual_property, entity_resolution, geospatial_verification,
geophysical_hazard, fire_emissions, space_weather, infrastructure_critical,
sanctions_compliance, health_biosecurity, election_governance,
energy_commodities, climate_weather, demographic_economic, nuclear_wmd,
protest_unrest
```

3. Add `source_group_aliases` mapping in validator:
```python
SOURCE_GROUP_ALIASES = {
    "court_record": "judicial_record",
    "government_registry": "official_gov",
}
```

**Acceptance criteria:**
- Validator accepts all 30 committed values
- Alias resolution working: `court_record` resolves to `judicial_record`
- Existing 16 values unchanged
- `proposed_extensions` section cleared (all promoted)

---

### 4.3 Backfill Existing 77 Sources

**Current state:** 77 sources with 19 fields each. No `consumption_surfaces`, `access_tier`, `api_endpoint`, or `collector_status`.

**Required changes:**

For each existing source, add:
- `consumption_surfaces` — which of the 7 surfaces it serves
- `access_tier` — classify as tier_a/tier_b/tier_c/paid
- `api_endpoint` — base URL only
- `collector_status` — `active` for sources with Cycle-002 collectors, else `planned`
- `rate_limit_policy` — required for active/planned, describe known limits honestly
- `dashboard_permitted` — true for non-paid
- Remaining fields where applicable

**Backfill rules:**
- Settlement-eligible sources MUST include `theatre_settlement` surface
- Paid sources: `dashboard_permitted: false` unless explicitly overridden
- Sources with Cycle-002/003 collectors: `collector_status: "active"`
- SEC endpoints: `rate_limit_policy: "10 req/s with user-agent required"`

**Acceptance criteria:**
- All 77 sources have non-empty `consumption_surfaces`
- No source missing `access_tier`
- Validator passes in both normal and strict mode

---

### 4.4 Priority 1 Sources — 18 New (5+ Surfaces, Tier A/B)

**Sanctions cluster (4):** ofac_sdn_api, eu_sanctions_list, uk_ofsi_list, opensanctions_api
**Geopolitical + Health (4):** who_disease_outbreak, noaa_nws_alerts, wikidata_sparql, imf_sdmx_api
**Property + Entity (4):** planning_data_uk, gleif_api, openmeteo_api, nager_date_api
**High-coverage (6):** eurostat_api, eia_api, sam_gov_api, un_sanctions_sc, promed_rss, reliefweb_api (backfill if exists)

**Key constraints:**
- Wikidata: `settlement_requires_corroboration: true` (cannot be sole settlement source)
- IMF: `revision_policy: "immutable"` (permanent quarterly datasets)
- OpenSanctions: aggregator, not settlement-eligible
- Each sanctions source has unique `independence_upstream_id`

**Acceptance criteria:**
- 18 sources added (or backfilled where existing)
- Wikidata has `settlement_requires_corroboration: true`
- Settlement guardrails pass for all settlement-eligible sources
- No duplicate `source_id`

---

### 4.5 Priority 2 Sources — 25 New (4 Surfaces)

Settlement layer gaps (10): uk_caselaw_tna, uk_legislation_gov, uk_parliament_bills, usa_spending_api, patent_view_api, sec_xbrl_companyfacts, ons_api, hm_land_registry_ppd, overpass_api, nominatim_api

Mission Factory + DeltaBrief breadth (15): nasa_eonet_api, noaa_swpc_api, emsc_earthquake_api, aisstream_io, celestrak_gp, oecd_api, bis_statistics, who_gho_api, iea_api, courtlistener_api, opencorporates_api, fca_register, open_ownership_api, met_office_datapoint, spacelaunchnow_api

**CourtListener constraint:**
- `independence_upstream_id: "us_pacer_cm_ecf"` (shared with PACER for docket core)
- `independence_notes` documenting independent indexing + RECAP contributions
- `resolution_role: "secondary_corroboration"`

**Acceptance criteria:**
- 25 sources added
- CourtListener upstream correctly linked with notes
- Rate limits documented honestly (Nominatim: "1 req/s", Overpass: "fair use ~10,000 req/day")

---

### 4.6 Priority 3 Sources — 20+ Enumerated Only

All marked `collector_status: "enumerated"`. Full metadata, no collector expected this quarter. `rate_limit_policy` optional for enumerated sources.

Include: ISS Location, N2YO, TeleGeography Cables, Volcano Discovery RSS, Space-Track.org, CTBTO, SimFin, Alpha Vantage, CryptoCompare, Destatis, ABS, CDC WONDER, World Inequality DB, OPEC MOMR, OpenAQ, Copernicus CAMS, and others.

**Acceptance criteria:**
- 20+ sources added as enumerated
- No `rate_limit_policy` warnings for enumerated sources
- Validator passes

---

### 4.7 Validator Hardening

**Current state:** Validator v0.4.0 (`tools/validate_osint_registry.py`, 248 lines) validates 19 fields, summary counts, cross-source checks, and proposed group guards.

**Required changes:**

1. **New field validation:** consumption_surfaces (surface + quality_tier enum), access_tier, collector_status, rate_limit_policy, dashboard_permitted, settlement_latest_only_override, settlement_requires_corroboration, independence_notes, api_endpoint (reject `?`/`#`)
2. **Source group updates:** Accept 30 committed values. Resolve aliases before checking.
3. **Settlement guardrails:**
   - `settlement_eligible=true` requires `receipt_mode_minimum` present
   - `settlement_eligible=true` requires `revision_policy` present
   - `revision_policy=latest_only` + `settlement_eligible=true` = FAIL unless `settlement_latest_only_override=true`
   - `settlement_requires_corroboration=true` — warn (not fail)
4. **Rate limit policy:** Required for active/planned — warn if missing. Optional for enumerated.
5. **Inference + defaults (non-strict):**
   - `consumption_surfaces` missing/empty: infer from `settlement_eligible`
   - `dashboard_permitted` missing: infer from `access_tier`
   - `collector_status` missing: assume `planned`
6. **Strict mode:** Reject empty `consumption_surfaces`. Require `access_tier`, `collector_status`, `rate_limit_policy` (for active/planned).
7. **Duplicate handling:** Unique `source_id` enforced. Duplicate `api_endpoint` warned.
8. **Summary auto-computation:** `--fix-summary` overwrites header with correct computed values. Provided counts that disagree with computed = FAIL.

**Acceptance criteria:**
- All existing validations still work
- 9 new field validations added
- Strict mode catches missing required fields
- `--fix-summary` produces correct counts
- Alias resolution tested

---

### 4.8 RegistrySource Model Extension

**Current state:** `RegistrySource` model (`models/registry.py:17-38`) has 19 fields matching v0.4.0 schema.

**Required changes:**

Add 9 new optional fields to `RegistrySource` Pydantic model:

```python
consumption_surfaces: list[dict[str, Any]] = Field(default_factory=list)
access_tier: str = "tier_a"
api_endpoint: str | None = None
collector_status: str = "planned"
rate_limit_policy: str | None = None
dashboard_permitted: bool = True
settlement_latest_only_override: bool = False
settlement_requires_corroboration: bool = False
independence_notes: str | None = None
```

Add query methods to `RegistryLoader`:
- `by_access_tier(tier: str)` — filter by tier
- `by_collector_status(status: str)` — filter by status
- `by_consumption_surface(surface: str)` — sources serving a specific surface

**Acceptance criteria:**
- Model accepts all 9 new fields with correct defaults
- Existing v0.6.0 sources load without error (backwards compatible)
- New query methods work correctly

---

## 5. Technical Constraints

- **Pipeline location:** `~/Downloads/osint_pipeline/` (models, engine, collectors, tests)
- **Registry location:** `~/Developer/prediction-market-monorepo.nosync/theatre/fixtures/two_rail_theatres_v0_1/datasets/`
- **Validator location:** `~/Developer/prediction-market-monorepo.nosync/tools/validate_osint_registry.py`
- **Python:** 3.11+
- **Dependencies:** Pydantic v2 (no new external deps)
- **British spelling throughout**
- **All tests runnable via `python3 tests/test_*.py`**
- **Existing 49 pipeline tests must not regress**

---

## 6. Files Modified

| File | Location | Changes |
|------|----------|---------|
| `echelon_osint_source_registry_v1_0_0.json` | monorepo fixtures | **NEW** — v1.0.0 registry with 160+ sources, 9 new fields, 30 groups |
| `validate_osint_registry.py` | monorepo tools | Update — 9 new field validations, 30 enums, aliases, settlement guardrails, strict mode, --fix-summary |
| `models/registry.py` | pipeline | Update — 9 new fields on RegistrySource, 3 new query methods on RegistryLoader |
| `models/__init__.py` | pipeline | Update — export any new types |
| `tests/test_registry_expansion.py` | pipeline | **NEW** — 11+ tests for registry expansion |

---

## 7. Build Order

2 sprints, 12 tasks total.

### Sprint 1: Schema Extension + Priority 1 Sources (8 tasks)

```
T1.1 (Schema Extension) → T1.2 (Source Groups) → T1.3 (Backfill) → T1.4-T1.7 (P1 Sources) → T1.8 (Validator)
```

### Sprint 2: Priority 2+3 Sources + Version Bump (4 tasks)

```
T2.1 (P2 Settlement) → T2.2 (P2 Breadth) → T2.3 (P3 Enumerated) → T2.4 (Summary + Version Bump)
```

---

## 8. Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Backfill misclassifies sources | Medium | Validator enforces settlement guardrails |
| api_endpoint semantics ambiguous | Low | Validator rejects query strings/fragments |
| Source group taxonomy drift | Low | Alias resolution + validator enforcement |
| Summary counts drift on manual edits | Low | `--fix-summary` auto-computes from source data |
| Backwards compatibility breaks | High | All new fields OPTIONAL with safe defaults; v0.6.0 must pass unmodified |
| Rate limit misrepresentation | Medium | Honest documentation; `rate_limit_policy` field required for active/planned |

---

## 9. Pre-Flight Review Issues (15 Total)

All 15 issues from three external review rounds have been incorporated into the requirements above. See echelon_cycle_005_registry_expansion_plan.md for the full issue table mapping each issue to its task and resolution.
