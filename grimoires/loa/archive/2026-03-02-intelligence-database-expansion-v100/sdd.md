# SDD: Intelligence Database Expansion v1.0.0 (Cycle-005)

**Cycle:** 005
**Date:** 2026-03-02
**PRD:** `grimoires/loa/prd.md`

---

## 1. Overview

Registry expansion cycle — no new pipeline stages. All changes extend the existing registry JSON schema, validator, and RegistrySource model. The pipeline architecture (Collection → Corroboration → Scoring) is unchanged. Two repositories are touched: the monorepo (registry JSON + validator) and the pipeline (models + tests).

**Monorepo target:** `~/Developer/prediction-market-monorepo.nosync/`
- Registry: `theatre/fixtures/two_rail_theatres_v0_1/datasets/echelon_osint_source_registry_v1_0_0.json`
- Validator: `tools/validate_osint_registry.py`

**Pipeline target:** `~/Downloads/osint_pipeline/`
- Model: `models/registry.py`
- Tests: `tests/test_registry_expansion.py`

---

## 2. Changes

### 2.1 Registry JSON Schema Extension (T1.1)

**File:** `echelon_osint_source_registry_v1_0_0.json` (NEW — copy v0.6.0, extend)

Copy the existing v0.6.0 registry JSON as the base. Bump `"version"` to `"1.0.0"`. Add 9 new fields to each source entry. New fields are OPTIONAL — existing sources may omit them and the validator infers defaults.

**New top-level enums to add:**

```json
{
  "consumption_surface_enum": [
    "theatre_settlement", "mission_factory", "bounded_inquiry",
    "delta_brief", "agent_context", "consumer_dashboard", "sponsored_theatre"
  ],
  "quality_tier_enum": [
    "settlement_grade", "investigation_grade", "anomaly_detection",
    "change_detection", "reasoning_grade", "display_grade"
  ],
  "access_tier_enum": ["tier_a", "tier_b", "tier_c", "paid"],
  "collector_status_enum": ["active", "planned", "enumerated"]
}
```

**Per-source field additions (9 fields):**

```json
{
  "consumption_surfaces": [
    {
      "surface": "theatre_settlement",
      "quality_tier": "settlement_grade",
      "update_interval_seconds": 86400,
      "notes": null
    }
  ],
  "access_tier": "tier_a",
  "api_endpoint": "https://api.example.com/v1/",
  "collector_status": "planned",
  "rate_limit_policy": "600 req/5min",
  "dashboard_permitted": true,
  "settlement_latest_only_override": false,
  "settlement_requires_corroboration": false,
  "independence_notes": null
}
```

**api_endpoint contract:**
- MUST be a base URL: `scheme + host + optional base path`
- MUST NOT contain `?` (query string) or `#` (fragment)
- When present, collectors use `api_endpoint`; when absent, derive from `api_url`
- `api_url` remains the documentation/reference root

---

### 2.2 Source Group Expansion (T1.2)

**File:** `echelon_osint_source_registry_v1_0_0.json` — `source_group_enum` section

Replace `committed_values` with 30 entries. Remove `proposed_extensions` section (all promoted).

**New committed values (30 total):**

Existing 16:
```
official_gov, wire_service, national_media, local_media, social_platform,
satellite_imagery, maritime_ais, aviation_adsb, market_data, prediction_market,
academic_research, alt_data_behavioural, cyber_threat_intel, court_record,
financial_regulator, government_registry
```

New 14 (promoted 2 + added 12):
```
judicial_record, calendar_counter_signal,
intellectual_property, entity_resolution, geospatial_verification,
geophysical_hazard, fire_emissions, space_weather, infrastructure_critical,
sanctions_compliance, health_biosecurity, election_governance,
energy_commodities, climate_weather
```

Note: `demographic_economic`, `nuclear_wmd`, and `protest_unrest` from the context spec are additional groups that bring the total to 30+ when combined with the above. The exact count depends on whether legacy aliases (`court_record`, `government_registry`) are retained as committed values or replaced. The validator resolves aliases, so both forms are accepted.

**Alias mapping (in validator):**

```python
SOURCE_GROUP_ALIASES = {
    "court_record": "judicial_record",
    "government_registry": "official_gov",
}
```

Validator resolves aliases before checking enum membership. Both canonical and alias forms are valid in the JSON.

---

### 2.3 Source Backfill (T1.3)

**File:** `echelon_osint_source_registry_v1_0_0.json` — all 77 existing sources

For each existing source, add the 9 new fields based on the classification rules:

**Classification matrix:**

| Condition | access_tier | collector_status | dashboard_permitted |
|-----------|-------------|------------------|---------------------|
| No auth, may have rate limit | tier_a | See below | true |
| Free with registration (API key) | tier_b | See below | true |
| Free with genuine limits | tier_c | See below | true |
| Paid/enterprise | paid | See below | false (unless overridden) |

| Condition | collector_status |
|-----------|------------------|
| Has working Cycle-002/003 collector | active |
| Planned for collection this quarter | planned |
| Metadata only, no collector planned | enumerated |

**consumption_surfaces inference (validator non-strict):**
- `settlement_eligible=true` → include `theatre_settlement`
- Every free source → include `consumer_dashboard`
- Sources with anomaly detection value → include `mission_factory`
- Per-source judgement for remaining surfaces

---

### 2.4 Priority 1 Sources — Sanctions Cluster (T1.4)

**File:** `echelon_osint_source_registry_v1_0_0.json` — add 4 new entries

| source_id | source_group | access_tier | settlement_eligible | independence_upstream_id |
|-----------|-------------|-------------|---------------------|--------------------------|
| ofac_sdn_api | sanctions_compliance | tier_a | true | us_treasury_ofac |
| eu_sanctions_list | sanctions_compliance | tier_a | true | eu_council_sanctions |
| uk_ofsi_list | sanctions_compliance | tier_a | true | uk_hmt_ofsi |
| opensanctions_api | sanctions_compliance | tier_a | false | opensanctions_community |

Each has unique `independence_upstream_id`. OpenSanctions is NOT settlement-eligible (aggregator).

Settlement sources: `revision_policy: "as_of_timestamp"`, `receipt_mode_minimum: "http_transcript"`.
OFAC: `consumption_surfaces` with all 7 surfaces (7/7 coverage).

---

### 2.5 Priority 1 Sources — Geopolitical + Health (T1.5)

**File:** `echelon_osint_source_registry_v1_0_0.json` — add 4 new entries

| source_id | source_group | access_tier | settlement_eligible | Special |
|-----------|-------------|-------------|---------------------|---------|
| who_disease_outbreak | health_biosecurity | tier_a | false | — |
| noaa_nws_alerts | climate_weather | tier_a | false | — |
| wikidata_sparql | election_governance | tier_a | true | `settlement_requires_corroboration: true` |
| imf_sdmx_api | demographic_economic | tier_a | true | `revision_policy: "immutable"` |

**Wikidata constraint:** Cannot be sole settlement source. Any template settling on Wikidata must include at least one non-flagged primary source for corroboration. Validator warns when `settlement_requires_corroboration=true`.

---

### 2.6 Priority 1 Sources — Property + Entity (T1.6)

**File:** `echelon_osint_source_registry_v1_0_0.json` — add 4 new entries

| source_id | source_group | access_tier | settlement_eligible |
|-----------|-------------|-------------|---------------------|
| planning_data_uk | geospatial_verification | tier_a | true |
| gleif_api | entity_resolution | tier_a | true |
| openmeteo_api | climate_weather | tier_a | false |
| nager_date_api | calendar_counter_signal | tier_a | false |

Nager.Date: `resolution_role: "counter_signal"`, `counter_signal_class: "calendar_holiday"`.

---

### 2.7 Priority 1 Sources — Remaining High-Coverage (T1.7)

**File:** `echelon_osint_source_registry_v1_0_0.json` — add 6 new entries (or backfill)

| source_id | source_group | access_tier | settlement_eligible |
|-----------|-------------|-------------|---------------------|
| eurostat_api | demographic_economic | tier_a | true |
| eia_api | energy_commodities | tier_b | false |
| sam_gov_api | official_gov | tier_b | true |
| un_sanctions_sc | sanctions_compliance | tier_a | true |
| promed_rss | health_biosecurity | tier_a | false |
| reliefweb_api | geophysical_hazard | tier_a | false |

**ReliefWeb:** Corrected from `protest_unrest` to `geophysical_hazard`. Check for existing `source_id` — if exists, backfill new fields only; do not duplicate.

---

### 2.8 Validator Update (T1.8)

**File:** `tools/validate_osint_registry.py`

Bump `__version__` to `"1.0.0"`.

**New validation blocks:**

1. **Enum validation for new fields:**
```python
# consumption_surfaces
for cs in s.get("consumption_surfaces", []):
    if cs["surface"] not in consumption_surface_enum:
        errors.append(...)
    if cs["quality_tier"] not in quality_tier_enum:
        errors.append(...)

# access_tier
if s.get("access_tier") and s["access_tier"] not in access_tier_enum:
    errors.append(...)

# collector_status
if s.get("collector_status") and s["collector_status"] not in collector_status_enum:
    errors.append(...)
```

2. **api_endpoint guard:**
```python
ep = s.get("api_endpoint")
if ep and ("?" in ep or "#" in ep):
    errors.append(f"{sid}: api_endpoint contains query string or fragment: '{ep}'")
```

3. **Settlement guardrails (strengthened):**
```python
if s.get("settlement_eligible"):
    if not s.get("receipt_mode_minimum"):
        errors.append(f"{sid}: settlement_eligible=true but receipt_mode_minimum missing")
    if not s.get("revision_policy"):
        errors.append(f"{sid}: settlement_eligible=true but revision_policy missing")

rp = s.get("revision_policy")
if rp == "latest_only" and s.get("settlement_eligible"):
    if not s.get("settlement_latest_only_override"):
        compensating = s.get("receipt_mode_minimum") in ("witness_quorum", "signed_receipt")
        if not compensating:
            errors.append(f"{sid}: latest_only + settlement_eligible without override or compensating receipt mode")
```

4. **Rate limit policy enforcement:**
```python
cs = s.get("collector_status", "planned")
if cs in ("active", "planned") and not s.get("rate_limit_policy"):
    warnings.append(f"{sid}: active/planned source missing rate_limit_policy")
```

5. **Source group alias resolution:**
```python
SOURCE_GROUP_ALIASES = {
    "court_record": "judicial_record",
    "government_registry": "official_gov",
}
sg = s.get("source_group", "")
sg = SOURCE_GROUP_ALIASES.get(sg, sg)  # Resolve alias
if sg not in committed_groups:
    errors.append(...)
```

6. **Strict mode additions:**
```python
if strict:
    if not s.get("consumption_surfaces"):
        errors.append(f"{sid}: --strict: empty consumption_surfaces")
    if not s.get("access_tier"):
        errors.append(f"{sid}: --strict: missing access_tier")
    if not s.get("collector_status"):
        errors.append(f"{sid}: --strict: missing collector_status")
```

7. **Non-strict inference + warnings:**
```python
if not strict:
    if not s.get("consumption_surfaces"):
        if s.get("settlement_eligible"):
            warnings.append(f"{sid}: inferring theatre_settlement surface from settlement_eligible")
        else:
            warnings.append(f"{sid}: inferring consumer_dashboard surface")
```

8. **--fix-summary mode:**
```python
if fix_summary:
    computed_summary = {
        "total_sources": len(sources),
        "by_access_tier": dict(Counter(s.get("access_tier", "tier_a") for s in sources)),
        "by_collector_status": dict(Counter(s.get("collector_status", "planned") for s in sources)),
        "settlement_eligible_count": sum(1 for s in sources if s.get("settlement_eligible")),
        "source_group_count": len(set(s["source_group"] for s in sources)),
        ...
    }
    reg["summary"] = computed_summary
    # Write back
```

9. **Summary count validation (normal mode):**
```python
for key in ["by_access_tier", "by_collector_status"]:
    for k, v in computed[key].items():
        if summary.get(key, {}).get(k) != v:
            errors.append(f"summary.{key}[{k}]: expected {v}, got {summary.get(key, {}).get(k)}")
```

10. **Duplicate api_endpoint warning:**
```python
seen_endpoints = {}
for s in sources:
    ep = s.get("api_endpoint")
    if ep:
        if ep in seen_endpoints:
            warnings.append(f"{sid}: api_endpoint '{ep}' also used by {seen_endpoints[ep]}")
        seen_endpoints[ep] = sid
```

---

### 2.9 RegistrySource Model Extension (T1.1 — co-task)

**File:** `models/registry.py`

Add 9 new fields to `RegistrySource`:

```python
class RegistrySource(BaseModel):
    """Single source entry from the OSINT Source Registry."""

    # ... existing 19 fields ...

    # v1.0.0 additions
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

```python
def by_access_tier(self, tier: str) -> list[RegistrySource]:
    """Return sources with a given access tier."""
    return [s for s in self._sources.values() if s.access_tier == tier]

def by_collector_status(self, status: str) -> list[RegistrySource]:
    """Return sources with a given collector status."""
    return [s for s in self._sources.values() if s.collector_status == status]

def by_consumption_surface(self, surface: str) -> list[RegistrySource]:
    """Return sources serving a specific consumption surface."""
    return [
        s for s in self._sources.values()
        if any(cs.get("surface") == surface for cs in s.consumption_surfaces)
    ]

def active_sources(self) -> list[RegistrySource]:
    """Return sources with active collectors."""
    return self.by_collector_status("active")

def settlement_sources_requiring_corroboration(self) -> list[RegistrySource]:
    """Return settlement sources that cannot be sole anchor."""
    return [
        s for s in self._sources.values()
        if s.settlement_eligible and s.settlement_requires_corroboration
    ]
```

---

### 2.10 Priority 2 Sources — Settlement Layer (T2.1)

**File:** `echelon_osint_source_registry_v1_0_0.json` — add 10 new entries

Sources with 4 surface coverage that fill settlement layer gaps: uk_caselaw_tna, uk_legislation_gov, uk_parliament_bills, usa_spending_api, patent_view_api, sec_xbrl_companyfacts, ons_api, hm_land_registry_ppd, overpass_api, nominatim_api.

Rate limits documented honestly:
- Nominatim: `"1 req/s, strict usage policy"`
- Overpass: `"fair use, ~10,000 req/day"`
- SEC XBRL: `"10 req/s, user-agent required"`

All `collector_status: "planned"`.

---

### 2.11 Priority 2 Sources — Breadth (T2.2)

**File:** `echelon_osint_source_registry_v1_0_0.json` — add 15 new entries

Mission Factory + DeltaBrief breadth sources. CourtListener has special upstream constraints:
- `independence_upstream_id: "us_pacer_cm_ecf"`
- `independence_notes: "Shares upstream docket corpus with PACER; adds independent indexing, aggregation, and RECAP community contributions."`
- `resolution_role: "secondary_corroboration"`

---

### 2.12 Priority 3 Sources — Enumerated (T2.3)

**File:** `echelon_osint_source_registry_v1_0_0.json` — add 20+ entries

All `collector_status: "enumerated"`. `rate_limit_policy` optional. Full metadata present for future build prioritisation.

---

### 2.13 Summary Recompute + Version Bump (T2.4)

**File:** `echelon_osint_source_registry_v1_0_0.json` — summary section

Run `validate_osint_registry.py --fix-summary` to auto-compute:
- `total_sources`
- `by_access_tier` counts
- `by_collector_status` counts
- `by_consumption_surface_count` distribution
- `settlement_eligible_count`
- `source_group_count`
- `jurisdictions` list
- `sitdeck_category_coverage`

Bump `"version": "1.0.0"` in header. Run `--strict` to confirm.

---

## 3. Test Plan

**File:** `tests/test_registry_expansion.py` (NEW)

| Test | Concern | Validates |
|------|---------|-----------|
| `test_backwards_compat_v060_loads` | Compat | v0.6.0 registry validates without new fields |
| `test_settlement_guardrail_receipt_mode` | Settlement | settlement_eligible=true without receipt_mode_minimum fails |
| `test_settlement_guardrail_latest_only_without_override` | Settlement | latest_only + settlement_eligible without override fails |
| `test_settlement_guardrail_latest_only_with_override` | Settlement | latest_only + override=true passes |
| `test_settlement_requires_corroboration_warning` | Settlement | Flag emits warning |
| `test_source_group_alias_resolution` | Groups | court_record resolves to judicial_record |
| `test_consumption_surfaces_inference_warning` | Inference | Missing surfaces inferred + warned |
| `test_dashboard_permitted_default_paid` | Defaults | Paid sources default false |
| `test_api_endpoint_rejects_query_string` | Endpoint | `?` or `#` rejected |
| `test_rate_limit_policy_required_for_active` | Rate limit | Active/planned without policy warned |
| `test_summary_header_mismatch_fails` | Summary | Counts disagree = FAIL |
| `test_registry_source_model_new_fields` | Model | RegistrySource accepts 9 new fields |
| `test_registry_loader_by_consumption_surface` | Model | Query method returns correct sources |

---

## 4. Dependency Order

### Sprint 1

```
T1.1 (Schema + Model) → T1.2 (Groups) → T1.3 (Backfill) → T1.4-T1.7 (P1 Sources) → T1.8 (Validator)
```

**Rationale:**
- T1.1 first: schema fields must exist before sources can use them
- T1.2 before T1.3: new groups must be committed before backfilling sources into them
- T1.3 before T1.4-T1.7: backfill establishes patterns for new source entries
- T1.8 last: validator validates all previous work

### Sprint 2

```
T2.1 (P2 Settlement) → T2.2 (P2 Breadth) → T2.3 (P3 Enum) → T2.4 (Summary)
```

**Rationale:**
- Settlement sources first: highest value, strictest validation
- Breadth next: fills remaining surface gaps
- Enumerated last: metadata only, lowest risk
- T2.4 last: summary recompute requires all sources present
