# OSINT_COMPOSED_ORACLE_V1

## Reserved Criteria Semantics, Source Independence Taxonomy & OSINT Source Registry Architecture

**Template #10 — Theatre Template Library Extension**

| Property | Value |
|----------|-------|
| Version | 2.0 |
| Status | RESERVED (fixtures-only, no live pipeline dependency) |
| Date | 25 February 2026 |
| Supersedes | Echelon_OSINT_Composed_Oracle_Spec_v1.docx (24 Feb 2026) |
| Registry Version | 0.3.2 (51 sources, 7 jurisdictions) |
| Dependencies | None. Synthetic fixtures only. Live pipeline deferred to Cycle-035. |
| Dataset Hash | `188dacfa...eadacd` (10 records: 6 PASS / 4 FAIL) |

---

## 1. Purpose

This document defines the verification criteria, source independence taxonomy, and OSINT source registry architecture for the Echelon Theatre Template Library. It extends the deterministic verification framework to support composed OSINT oracle outputs where multiple independent sources must be evaluated, counter-signals checked, and market rule integrity monitored.

The criteria are **reserved** in the current release: semantics are pinned, fixtures exercise all pass/fail paths, but no live data pipeline is connected. This prevents semantic drift before the World Monitor integration in Cycle-035.

Version 2.0 adds the full OSINT Source Registry specification (v0.3.2), including structural primitives for provenance integrity, five schema enforcement rules, the HTTP transcript canonical specification for deterministic receipt hashing, and a jurisdictional readiness assessment for settlement-grade operations.

---

## 2. Reserved Criteria Definitions

Three new criteria types extend the existing six-criteria template. Each is fully exercised by the 10-record fixture set with explicit pass and fail paths.

### 2.1 corroboration_minimum_met

Requires the primary claim to be independently confirmed by at least N sources from distinct source_groups within a declared time window. Sources from the same source_group count as one corroborator regardless of quantity.

| Property | Value |
|----------|-------|
| Pass condition | `count(distinct source_groups WHERE role=secondary_corroboration AND confirms_primary=true AND \|delta_t\| <= corroboration_window_seconds) >= corroboration_minimum` |
| Parameters | `corroboration_minimum` (integer, default 2); `corroboration_window_seconds` (integer, default 3600) |
| Fail modes | Fewer than N distinct groups confirm; corroborating sources outside time window; same-group sources counted as distinct (scorer bug) |
| Fixture coverage | osint_0007: FAIL — only 1 of 2 required groups within window (Polymarket 1 second late) |
| Registry interaction | Runner MUST deduplicate by `independence_upstream_id` before counting distinct source_groups (see Section 6.5) |

### 2.2 counter_signal_checked

Requires explicit evaluation of at least one counter-signal stream. The evaluation must produce one of four outcomes:

| Outcome | Meaning | Effect | Criterion |
|---------|---------|--------|-----------|
| absent | Counter-signal checked, not present | Supports primary signal | PASS |
| present_discounted | Present but explained by precommitted discount rule | Weakly supports | PASS |
| present_unexplained | Present, no applicable discount rule | Potential false positive | FAIL |
| unavailable | Source unreachable (HTTP error, timeout) | Configurable via allow_gap | Depends |

> **Critical design note:** Counter-signal absence and counter-signal unavailability are distinct states. Absence means the verifier checked and found no alternative explanation. Unavailability means the verifier could not check. The first is evidence; the second is an intelligence gap. Conflating them undermines audit integrity.

| Property | Value |
|----------|-------|
| Discount rules | Must be precommitted at oracle creation. Each rule has a `rule_id`, condition (e.g. `HOLIDAY_CALENDAR`, `SPORTING_EVENT`, `FESTIVAL`), and `committed_at` timestamp. Rules added after oracle creation do not apply retroactively. |
| Counter-signal classes | `calendar`, `infrastructure_outage`, `transport_disruption`, `financial_distress`, `weather`, `civic_event`, `policy_change`, `regulatory_status_change`, `legal_dispute_active`, `payment_rail_anomaly`, `identity_mismatch` (11 classes, expanded from 4 in v1) |
| Fixture coverage | osint_0002: PASS (present_discounted via HOLIDAY_CALENDAR); osint_0005: PASS (unavailable, allow_gap=true); osint_0008: FAIL (present_unexplained, z-score 2.8); osint_0010: FAIL (unavailable, allow_gap=false) |

### 2.3 rule_change_monitored

Commits the market resolution rules text hash at market open and monitors for changes. Any modification to resolution criteria mid-market is logged as a `rule_diff_event` and triggers the configured policy response. This criterion directly addresses the ISW/Polyglobe class of oracle compromise where resolution criteria are silently altered to change settlement outcomes.

| Property | Value |
|----------|-------|
| Pass condition | `sha256(canonical(current_rules)) == committed_rules_hash` OR (diff detected AND policy == 'warn') OR (diff detected AND policy == 'freeze') |
| Policy options | `fail` — any rule change causes criterion FAIL (default, strictest); `warn` — change logged, criterion PASS; `freeze` — change halts settlement until manual review |
| Committed artefact | `market_rules_hash` (SHA-256 of canonical JSON of rules text) committed at market open with `committed_at` timestamp |
| Fixture coverage | osint_0009: FAIL — resolution criteria weakened from 'at least two independent providers' to 'at least one provider' (the ISW/Myrnohrad pattern) |

---

## 3. Source Independence Taxonomy

The `source_group` field is a committed enumeration, not a free-text field. Corroboration requires distinct groups. This prevents gaming (ten mirrors of the same wire service do not constitute ten independent corroborators).

| source_group | Description | Example Sources |
|-------------|-------------|-----------------|
| official_gov | Government publications, press briefings, regulatory filings | State Dept, MoD, IAEA, Companies House |
| wire_service | Wire services and structured event databases | GDELT, ACLED, Reuters Wire |
| national_media | Major national/international news outlets | Reuters, BBC, Al Jazeera |
| local_media | Regional and local news sources | Kyiv Post, Daily Star |
| social_platform | Social media posts and narrative velocity | X/Twitter, Telegram |
| satellite_imagery | Satellite and aerial imagery providers | Planet, Maxar, Sentinel |
| maritime_ais | Automatic Identification System vessel tracking | MarineTraffic, Spire |
| aviation_adsb | ADS-B aircraft transponder tracking | OpenSky, FlightRadar24 |
| market_data | Financial market data and pricing feeds | Polygon.io, Bloomberg |
| prediction_market | Prediction market platforms and CLOB feeds | Polymarket, Kalshi |
| academic_research | Peer-reviewed publications, research institution outputs | ISW, CSIS, SIPRI |
| alt_data_behavioural | Alternative data: foot traffic, mobility, commuter indices | World Monitor CII, SafeGraph |
| cyber_threat_intel | Cyber threat intelligence and vulnerability feeds | Recorded Future, CISA |

**Extension policy:** New source_group values may be added via template version increment. Existing values are never removed or renamed. Each addition requires at least one fixture exercising the new group in both pass and fail paths.

### 3.1 Proposed Extensions

Two source_group values are proposed but not yet committed. Each requires at least one fixture exercising the new group in both pass and fail paths before committing in template v1.1.

| Proposed Value | Rationale | Requires |
|---------------|-----------|----------|
| judicial_record | Gazette insolvency notices are functionally distinct from Companies House regulatory filings. Mixing them in official_gov conflates entity existence with legal distress. | Template v1.1 + 2 fixtures |
| calendar_counter_signal | Prevents mixing primary evidence sources with counter-signal feeds (TfL, Nager.Date, Abstract Holidays) in the same group. | Template v1.1 + 2 fixtures |

---

## 4. OSINT Source Registry Architecture

The OSINT Source Registry (v0.3.2) is the authoritative catalogue of all data sources available to composed oracle evaluations. It defines per-source metadata, access characteristics, provenance requirements, and independence relationships. The registry is a JSON document validated by a standalone CLI tool (`validate_osint_registry.py`).

### 4.1 Registry Summary

| Property | Value |
|----------|-------|
| Version | 0.3.2 |
| Total Sources | 51 |
| Jurisdictions | AE (9), AU (2), CA (1), EU (4), GB (10), GLOBAL (18), US (7) |
| Settlement-Eligible | 12 sources across 5 jurisdictions |
| Counter-Signal Sources | 8 |
| World Monitor Endpoints | 3 (self-hosted fork) |
| World Monitor Upstream Sources | 5 (direct integration preferred) |
| Controlled Enums | 9 (source_group, resolution_role, priority_bucket, auth_methods, timestamp_precision, counter_signal_class, access_surface, revision_policy, receipt_mode) |
| Schema Enforcement Rules | 5 |

### 4.2 Per-Source Structural Fields

Each source in the registry carries the following fields. Fields marked v0.3+ were added during the registry evolution from v0.1 to v0.3.2 and represent structural primitives for provenance integrity.

| Field | Type | Description |
|-------|------|-------------|
| source_id | string | Unique identifier for this source (e.g. `companies_house_api`) |
| source_group | enum | Committed source independence group (see Section 3) |
| resolution_role | enum | `primary_evidence` \| `secondary_corroboration` \| `counter_signal` \| `triage_only` |
| priority_bucket | enum | `settlement_grade` \| `scoring_grade` |
| settlement_eligible | boolean | Whether this source can participate in settlement-grade evaluations |
| jurisdiction | string | ISO 3166-1 alpha-2 or `GLOBAL` |
| auth_methods | enum[] | `none`, `api_key`, `basic`, `oauth2`, `user_agent_header`, `registration`, `membership` |
| api_url | string\|null | Callable API endpoint (null for self-hosted sources with repo_url) |
| ui_url | string\|null | Human-browsable search/portal URL |
| repo_url | string\|null | Git repository for self-hosted sources (World Monitor) |
| independence_upstream_id | string (v0.3+) | System-of-record identifier for corroboration deduplication |
| access_surface | enum (v0.3+) | `public_api` \| `partner_api` \| `portal_scrape` \| `paid_gateway` \| `manual_attestation` |
| access_surface_confirmed | bool (v0.3+) | Whether access_proof has been verified |
| access_proof | object (v0.3.1+) | `{ doc_url, auth_method_expected, verified, proof_type }` |
| revision_policy | enum (v0.3+) | `immutable` \| `as_of_timestamp` \| `latest_only` \| `forbid_settlement` |
| receipt_mode_minimum | enum (v0.3+) | `none` \| `http_transcript` \| `cryptographic_transcript` \| `signed_receipt` \| `witness_quorum` |
| counter_signal_class | enum (conditional) | Required when `resolution_role=counter_signal` (11 classes) |
| world_monitor_domain | string\|null | Set only for self-hosted World Monitor fork endpoints |
| world_monitor_upstream_domain | string\|null | Set for sources WM consumes but should be integrated directly |

### 4.3 Structural Primitives (v0.3+)

Three structural primitives were introduced in registry v0.3 to address provenance integrity gaps identified during the Gemini strategic architecture review.

#### 4.3.1 independence_upstream_id

Prevents fake corroboration. Multiple datasets published through the same API gateway (e.g. Dubai Pulse) may be backed by the same system of record (e.g. `ae_dld_tabu`). The upstream_id identifies the actual data origin, not the publication layer. The verifier deduplicates by upstream_id before evaluating `corroboration_minimum_met`.

**Naming convention:** `{jurisdiction}_{agency}_{system}` (e.g. `ae_dld_tabu`, `gb_companies_house_register`, `us_sec_edgar_efts`)

#### 4.3.2 access_surface

Honest classification of how a source is actually accessible, independent of data quality. Portal-scrape sources cannot be settlement-grade regardless of data quality because scraped content has no cryptographic receipt chain.

| Value | Description |
|-------|-------------|
| public_api | Documented REST/GraphQL API accessible without special agreements |
| partner_api | API requiring signed data-sharing agreement or trade licence |
| portal_scrape | Web portal with no API; data extracted by scraping HTML |
| paid_gateway | Commercial API requiring subscription or per-query payment |
| manual_attestation | Data obtained through manual process (notarised documents, physical inspection) |

#### 4.3.3 revision_policy

Declares the engine's stance when an issuer revises previously published data. This determines whether a source can participate in settlement without compensating provenance controls.

| Value | Description |
|-------|-------------|
| immutable | Once published, data never changes. Safe for settlement. |
| as_of_timestamp | API supports point-in-time queries. Re-fetch at same timestamp returns identical data. Safe for settlement. |
| latest_only | API always returns current state. Previous values overwritten. NOT safe for settlement unless compensated by `witness_quorum` or `signed_receipt`. |
| forbid_settlement | Explicitly excluded from settlement. Used for sources with known mutability and no compensating controls. |

#### 4.3.4 receipt_mode_minimum

Specifies the minimum provenance standard required for evidence bundles from this source.

| Value | Description |
|-------|-------------|
| none | No receipt required. Acceptable for triage_only sources. |
| http_transcript | Canonical HTTP request/response hash (see Section 5). Standard for public APIs. |
| cryptographic_transcript | TLS session transcript or signed API response. Stronger than http_transcript. |
| signed_receipt | Source issues a cryptographically signed receipt for each query. Compensates `latest_only` revision_policy. |
| witness_quorum | Multiple independent fetchers must produce matching receipts. Strongest compensating control for mutable sources. |

---

## 5. HTTP Transcript Canonical Specification

Defines how fetchers must normalise HTTP requests before hashing to ensure deterministic receipt computation. Two independent fetchers querying the same endpoint with the same parameters must produce identical receipt hashes regardless of HTTP library, header ordering, or default user-agent strings.

| Property | Value |
|----------|-------|
| Version | 1.0 |
| Hash Algorithm | SHA-256 |
| Method | UPPERCASE (`GET`, `POST`, etc.) |
| URL | scheme + host + path (no query string) |
| Query Parameters | Sorted by key (RFC 3986), then by value for duplicate keys |
| Headers | Allowlist only, case-insensitive key sort. Excluded: `User-Agent`, `Date`, `Cookie`, `X-Request-Id`, `Authorization` |
| Body | Exact bytes (empty string if no body) |
| Hash Input | `canonical_method + '\n' + canonical_url + '\n' + canonical_query + '\n' + canonical_headers + '\n' + body_hash` |
| Canonical JSON | `json.dumps(obj, sort_keys=True, separators=(",",":"), ensure_ascii=False)` |

---

## 6. Schema Enforcement Rules

Five enforcement rules are committed in the registry and validated by the standalone CLI validator. Rules 6.1–6.2 are validator-enforced. Rules 6.3–6.5 require template runner integration for full enforcement.

### 6.1 proposed_source_group_guard

If `proposed_source_group` is present and template `schema_version < 1.1`, the runner MUST ignore it. In strict mode (`--strict` flag on validator), the presence of `proposed_source_group` causes validation failure. Sources with `proposed_source_group` are treated as their current `source_group` until the extension is committed.

### 6.2 revision_policy_settlement_guard

If `revision_policy` is `latest_only`, `settlement_eligible` MUST be `false` UNLESS `receipt_mode_minimum` is `witness_quorum` or `signed_receipt`. Mutable data cannot settle without compensating provenance. The validator enforces this invariant; sources violating it fail validation immediately.

### 6.3 access_surface_independence

Two sources with the same `independence_upstream_id` MUST NOT both count towards `corroboration_minimum_met`. The verifier deduplicates by upstream_id before checking distinct source_groups. This is a runner-level enforcement requirement.

### 6.4 dubai_pulse_publication_layer

Dubai Pulse (`api.dubaipulse.gov.ae`) is a publication layer, not a system of record. Multiple Dubai Pulse datasets may expose different views of the same backend system. The `independence_upstream_id` must reference the system of record (e.g. `ae_dld_tabu` for DLD data), not `dubai_pulse`. Two Dubai Pulse datasets backed by the same system of record MUST NOT corroborate each other.

**Affected sources:** `dld_open_data`, `dubai_municipality_bps`, `difc_public_register`

### 6.5 independence_upstream_dedupe_runner

Template runners MUST deduplicate sources by `independence_upstream_id` BEFORE evaluating `corroboration_minimum_met`. At corroboration evaluation time: group evidence bundles by `independence_upstream_id`, collapse duplicates to single strongest-confidence entry, then count distinct source_groups from the collapsed set.

**Enforcement:** Runner-level. Registry validator checks for settlement-eligible upstream_id collisions as a warning. Full enforcement requires template runner integration.

---

## 7. Jurisdictional Readiness Assessment

Settlement-grade operations require at least one settlement-eligible source per jurisdiction with confirmed API access, immutable or `as_of_timestamp` revision policy, and `http_transcript` or stronger receipt mode.

| Jurisdiction | Status | Settlement Sources | Gaps | Action Required |
|-------------|--------|-------------------|------|-----------------|
| GB | Settlement-ready | Companies House, Gazette, HMLR, Bank of England | None critical | None |
| US | Mostly ready | SEC EDGAR, NY Fed Markets, US Treasury FiscalData | PACER (paid gateway) | PACER subscription for judicial records |
| AE | Partner-required | DLD Open Data, Dubai Municipality BPS (public APIs via Dubai Pulse) | NER requires trade licence; ADGM/VARA portal scrape only; RDC unverified | Partner API agreements for NER, Ejari; confirm RDC access |
| AU | Workable | AFSA NPII (insolvency) | Need ASIC (entity verification) + RBA (rates) | Add ASIC + RBA sources in registry v0.4 |
| EU | Macro only | ECB Data API | BRIS partial; no entity-level verification | Add national registries (Handelsregister, Registre du Commerce) |
| CA | Partial | None settlement-eligible yet | Corporations Canada is scoring-grade only | Evaluate PPSA provincial registries |
| GLOBAL | Supporting | UN Comtrade | Cross-border sources support but do not anchor settlement | N/A |

---

## 8. Fixture Summary

10 records across 7 geographic regions. Each FAIL exercises exactly one primary failure mode. The fourth FAIL (osint_0010) tests compound failure under partial information — the real-world condition for OSINT.

| Record | Geo Region | Result | Key Feature |
|--------|-----------|--------|-------------|
| osint_0001 | Strait of Hormuz | PASS | Clean run. All 6 criteria pass. 3 corroborators, counter-signal absent. |
| osint_0002 | Eastern Med | PASS | Counter-signal present but discounted via precommitted HOLIDAY_CALENDAR rule. |
| osint_0003 | South China Sea | PASS | High-risk convergence. 3 corroborators. Strongest composite score (0.8865). |
| osint_0004 | Black Sea West | PASS | Low-risk baseline. Exactly 2 corroborators (minimum-viable pass). |
| osint_0005 | Gulf of Aden | PASS | Counter-signal unavailable but allow_gap=true override committed. |
| osint_0006 | Taiwan Strait | PASS | High-confidence scenario. All sources confirm at high confidence. |
| osint_0007 | Strait of Hormuz | FAIL | corroboration_minimum_met: Polymarket 1 second outside window. |
| osint_0008 | Eastern Med | FAIL | counter_signal_checked: z-score 2.8, no discount rule. Potential false positive. |
| osint_0009 | Strait of Hormuz | FAIL | rule_change_monitored: Rules weakened mid-market (ISW/Polyglobe pattern). |
| osint_0010 | Baltic Sea | FAIL | Compound: counter-signal unavailable (allow_gap=false) + marginal corroboration. |

---

## 9. Integration with Existing Templates

The three reserved criteria types generalise across the Theatre Template Library:

| Template | corroboration_minimum_met | counter_signal_checked | rule_change_monitored |
|----------|--------------------------|------------------------|-----------------------|
| ESCROW_MILESTONE_RELEASE_V1 | Multiple signer roles satisfy pattern. Extend to require N independent inspector reports. | Contradictory attestation, conflicting inspector report, or timing mismatch. | Escrow terms hash committed at contract creation. Any amendment logged. |
| DISTRIBUTION_WATERFALL_V1 | Cap table consistency cross-checks. Extend to require independent auditor confirmation. | Bank reversal, duplicate reference, or off-cycle credit. | Waterfall policy hash committed at fund creation. |
| LEDGER_RECONCILIATION_V1 | Multiple ledger sources cross-referenced. | Disputed transaction or pending reversal. | Reconciliation rules hash committed at period open. |
| ARREARS_RESOLUTION_V1 | Payment confirmation from bank + borrower attestation. | Active dispute, payment plan, or grace period clock. | Arrears policy hash committed at loan origination. |

---

## 10. Validator Tool

A standalone Python CLI validator (`validate_osint_registry.py`) enforces all enum memberships, structural invariants, and cross-source consistency checks. It requires no external dependencies beyond Python 3.10+ and the standard library.

| Property | Value |
|----------|-------|
| Location | `tools/validate_osint_registry.py` |
| Usage | `python3 validate_osint_registry.py <registry.json>` |
| Strict mode | `python3 validate_osint_registry.py --strict <registry.json>` |
| Exit codes | 0 = pass, 1 = fail, 2 = usage error |

**Validation checks:**

| Check Category | Details |
|---------------|---------|
| Enum membership | source_group, resolution_role, priority_bucket, auth_methods, timestamp_precision, counter_signal_class, access_surface, revision_policy, receipt_mode_minimum |
| Structural invariants | settlement_grade ⇒ settlement_eligible; counter_signal ⇒ counter_signal_class required; settlement_grade ⇒ resolution_role ≠ triage_only |
| World Monitor boundary | world_monitor_domain and world_monitor_upstream_domain mutually exclusive; domain ⇒ repo_url references WM fork allowlist |
| Provenance guards | revision_policy latest_only ⇒ settlement_eligible=false unless receipt_mode compensates; access_surface_confirmed ⇒ access_proof.verified + doc_url |
| Cross-source deduplication | Settlement-eligible sources sharing independence_upstream_id flagged as corroboration collision |
| Summary consistency | total_sources, by_priority_bucket, by_source_group, settlement_eligible_count, counter_signal_sources, world_monitor_endpoints all recomputed and checked |
| Strict mode | Rejects any source carrying proposed_source_group (enforces v1.1+ committed-only) |
| Proposed value guard | proposed_source_group value must exist in source_group_enum.proposed_extensions (catches typos) |

---

## 11. Build Sequence

| Phase | Cycle | Scope |
|-------|-------|-------|
| Criteria + Registry | Cycle-034 (current) | Reserved criteria semantics pinned. Template + 10 fixtures shipped. Source independence enum committed. Registry v0.3.2 (51 sources). Validator passing. No live dependencies. |
| OSINT Pipeline | Cycle-035 | World Monitor API integration. Evidence bundle ingestion from live sources. Counter-signal sources connected. Template transitions from fixtures-only to live replay. |
| Theatre Command UI | Cycle-036 | GeoEvent index rendered on globe surface. Evidence-grade markers (only bundles with provenance). Certificate status badges on theatre regions. |
| Multi-Agent Simulation | Cycle-037 | Hounfour agent integration for X narrative extraction. Rule-change monitoring as live market integrity service. Counter-signal agents as autonomous verifiers. |
| Registry v0.4 | Cycle-038+ | ASIC + RBA (AU), national EU registries, PACER (US judicial), Lean/Tarabut open banking (AE/MENA deferred). Template v1.1 with committed judicial_record + calendar_counter_signal enums. |

---

## 12. Deliverables

| File | Description | Status |
|------|-------------|--------|
| `OSINT_COMPOSED_ORACLE_V1_template.json` | Template with 6 criteria, source config, resolution programme | Complete |
| `osint_composed_oracle_fixtures_10.json` | 10 fixtures (6 PASS / 4 FAIL) with synthetic evidence bundles | Complete |
| `echelon_osint_source_registry_v0_3_2.json` | 51-source registry with 9 controlled enums, 5 enforcement rules, HTTP transcript spec | Complete |
| `validate_osint_registry.py` | Standalone CLI validator with --strict mode | Complete |
| `Echelon_OSINT_Composed_Oracle_Spec_v2.docx` | This document (docx version): criteria semantics, taxonomy, registry architecture, jurisdictional readiness | Complete |
| `Echelon_OSINT_Composed_Oracle_Spec_v2.md` | This document (markdown version): identical content, GitHub-native rendering | Complete |

---

## 13. Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 24 February 2026 | Initial release. 3 reserved criteria, 13 source_group enum, 10 fixtures, build sequence. |
| 2.0 | 25 February 2026 | Added: OSINT Source Registry v0.3.2 architecture (51 sources, 7 jurisdictions). 5 structural primitives (independence_upstream_id, access_surface, revision_policy, receipt_mode_minimum, access_proof). 5 schema enforcement rules. HTTP transcript canonical spec. Counter-signal class taxonomy expanded from 4 to 11. API URL split (api_url + ui_url). Validator tool specification. Jurisdictional readiness assessment. Proposed extensions (judicial_record, calendar_counter_signal). Updated build sequence through Cycle-038+. |
