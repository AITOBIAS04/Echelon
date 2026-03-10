# OSINT Registry Expansion — Research Notes + Schema Additions

**Status:** Queued (not in any active cycle) — Cycle-017 in platform roadmap
**Date:** 3 March 2026
**Sources:** Gemini research output (pre-build, ~Feb 2026), Strategic Architecture PDF (v1), Opus review (2 March 2026), Spatial Intelligence source analysis (3 March 2026)
**Current registry:** v0.4.0 (57 sources, 7 jurisdictions) — shipped Cycle-005
**Live intake queue:** `grimoires/loa/context/worldmonitor_echelon_integration_log.md`

---

## Context

WorldMonitor now ships layers independently of Echelon's cycle cadence. To prevent silent drift between WorldMonitor capabilities and Echelon's OSINT registry/collector surfaces, use `worldmonitor_echelon_integration_log.md` as the lightweight operating log:

- log notable WorldMonitor additions immediately
- map them to source groups/domain filters immediately
- integrate them in batch during registry-expansion or collector cycles

This note remains the deeper research/reference layer. The integration log is the operational queue.

Gemini conducted source research before any build cycles were implemented. The PDF ("Strategic Architecture of OSINT Data Signals for Deterministic Financial Auditing") was produced from this research. Both documents use correct Composed Oracle field names but contain one known error:

**Errata:** The PDF references "SHA-256 cryptographic hash using Canonical JSON formatting (RFC 8785)" on page 2. The pipeline uses **Echelon Canonical JSON v0**, which is explicitly not RFC 8785. This was corrected in Cycle-008 errata. Update the PDF before any external use.

The individual source assessments below are valid but need cross-referencing against what was actually built in Cycles 002-008. Some sources listed below may already be in the registry.

---

## Schema Additions (Queued)

These are structural additions to the registry schema identified during review. None are in any active cycle. Implement during a dedicated registry expansion cycle.

### 1. `query_determinism` field (NEW — highest priority)

From the PDF. Captures whether a source returns deterministic results for the same input.

```json
"query_determinism": "pure_id_lookup" | "search_endpoint" | "bulk_export"
```

**Constraint:** `settlement_eligible: true` requires `query_determinism: pure_id_lookup` or `bulk_export`. A `search_endpoint` source returns algorithmically ranked results that vary between queries for reasons unrelated to underlying data — non-deterministic by definition. Enforce in the registry validator.

**Compound rule (GPT review, 2 March 2026):** Settlement eligibility requires *both* deterministic query *and* acceptable `revision_policy` for the template's settlement mode. Specifically: `settlement_eligible: true` requires (`query_determinism ∈ {pure_id_lookup, bulk_export}`) AND (`revision_policy ∈ {immutable, as_of_timestamp}`). A source with `revision_policy: latest_only` is non-deterministic over time even if the query itself is deterministic.

**Validator error codes (implement during registry cycle):**
- `SETTLEMENT_ELIGIBLE_REQUIRES_DETERMINISTIC_QUERY` — source marked settlement-eligible but `query_determinism` is `search_endpoint`
- `SETTLEMENT_ELIGIBLE_REQUIRES_STABLE_REVISION_POLICY` — source marked settlement-eligible but `revision_policy` is `latest_only`
- `POST_RECEIPT_BODY_REQUIRED` — source uses POST/GraphQL but `receipt_body_required` is not set to `true`

### 2. GraphQL / POST-body receipt rule (NEW)

Any source with a GraphQL or POST-based query interface MUST include the request body in the receipt hash. URL alone is insufficient because the same URL returns different data depending on the POST payload.

**Promote to a registry-level rule**, not a per-source note. Applies to: OpenTargets, USA Spending, NIH RePORTER, and any future POST-based source.

Implementation: add `receipt_body_required: true` boolean to sources where `access_surface` uses POST-based queries. The evidence bundle receipt hash MUST be computed over `request_url + request_body + response_body`.

### 3. `requires_legal_review` field (NEW)

Boolean flag for sources with `access_surface: paid_gateway` that have redistribution or automated decisioning constraints in their ToS. Systematises a pattern currently tracked informally.

Applies to: DrugBank, PACER, Registry Trust, and any future paid source with ToS restrictions.

### 4. `deployability_routing` consumption surface (from earlier review)

Eighth consumption surface for post-certificate consumers (escrow controllers, credit allocators, compliance gateways). Already documented in v-next schema deltas note.

### 5. `review_reason_code` on certificate envelope (from earlier review)

Machine-readable reason for REVIEW_REQUIRED tier state. Enum: `corroboration_minimum_not_met`, `counter_signal_active`, `evidence_bundle_incomplete`, `freshness_stale`, `manual_review_requested`. Already documented in v-next schema deltas note.

### 6. Pipeline integrity criteria — visible but unweighted (from earlier review)

Four boolean gate criteria at Composed Oracle layer: `pipeline_integrity_injection_check`, `pipeline_integrity_tool_allowlist`, `pipeline_integrity_content_receipt_separation`, `pipeline_integrity_redaction_log`. Score 1.0/0.0, weight 0.0, visible in evidence bundle, invisible in composite. Already documented in v-next schema deltas note.

---

## Source Assessments by Domain

### Biopharma / Health / Clinical

| Source | source_group | access_surface | confirmed | settlement_eligible | resolution_role | Notes |
|--------|-------------|---------------|-----------|-------------------|----------------|-------|
| ChEMBL | biopharma_target | public_api | true | false | secondary_corroboration | Python client caches locally — require direct API call for evidence bundles, not cached response |
| PubChem (PUG-REST) | biopharma_target | public_api | true | false | secondary_corroboration | Async job path: evidence bundle must capture final resolved response, not job submission receipt |
| DrugBank | biopharma_target | paid_gateway | true | false | secondary_corroboration | Logs full body + IP + timestamp. `requires_legal_review: true`. ToS constraint on redistribution |
| OpenTargets | biopharma_target | public_api | true | false | secondary_corroboration | **GraphQL** — receipt must hash request body + response body. URL alone is insufficient |
| NPI Registry (NPPES v2.1) | health_provider_registry | public_api | true | **false** | secondary_corroboration | Revision policy: latest_only. CMS data updated when providers submit changes — no historical snapshots. Upgrade to settlement_eligible only if API supports point-in-time queries |
| WHO ICD-11 | health_classification | public_api | **false** (needs OAuth2 credentials) | false | secondary_corroboration | Classification data, not event data. `access_surface_confirmed: false` until credentials provisioned |

### Financial Fundamentals

| Source | source_group | access_surface | confirmed | settlement_eligible | resolution_role | Notes |
|--------|-------------|---------------|-----------|-------------------|----------------|-------|
| FMP (Income/Balance/CashFlow) | financial_aggregator | paid_gateway | true | **false** | secondary_corroboration | Aggregator. Upstream: SEC EDGAR XBRL. `independence_upstream_id: us_sec_edgar_efts`. For settlement, use EDGAR direct |
| FMP (ETF/Mutual Fund) | financial_aggregator | paid_gateway | true | false | **triage_only** | No sovereign upstream for fund holdings. 13-F filings available via EDGAR direct |
| FMP (Dividends/Earnings) | financial_aggregator | paid_gateway | true | false | secondary_corroboration | Useful for Mission Factory triggers (earnings surprise anomaly detection), not settlement |

### Public Spending and Grants

| Source | source_group | access_surface | confirmed | settlement_eligible | resolution_role | Notes |
|--------|-------------|---------------|-----------|-------------------|----------------|-------|
| USA Spending | government_spending | public_api | true | true | primary_evidence | No auth required. POST-based filtering — `receipt_body_required: true`. `receipt_mode_minimum: http_transcript` with body capture |
| NIH RePORTER (V2 API) | government_grants | public_api | true | true | primary_evidence | POST with JSON payload. Replaced bulk ExPORTER files. Confirm `revision_policy` — is historical grant data immutable or as_of_timestamp? |

### Macroeconomics / Labour / Government

| Source | source_group | jurisdiction | access_surface | confirmed | settlement_eligible | resolution_role | Notes |
|--------|-------------|-------------|---------------|-----------|-------------------|----------------|-------|
| IMF (SDMX) | macro_economic | GLOBAL | public_api | true | true | primary_evidence | Pin to SDMX 2.1 initially. 3.0 format stability unproven for settlement. `revision_policy: as_of_timestamp` |
| German Labour (BA) | demographic_economic | DE | public_api | true | **false** | secondary_corroboration | API launched Dec 2025. Too new — observe revision behaviour before settlement. `priority_bucket: scoring_grade` |
| UK Case Law (TNA) | judicial_registry | GB | public_api | true | true | primary_evidence | caselaw.nationalarchives.gov.uk. `revision_policy: immutable` — decisions not amended post-publication |
| UK Parliament API | legislative_registry | GB | public_api | true | true | primary_evidence | Royal Assent dates, bill milestones. Immutable once passed |
| UK Legislation | legislative_registry | GB | public_api | true | true | primary_evidence | legislation.gov.uk. `revision_policy: as_of_timestamp` — amendments exist but timestamped |
| Registry Trust (CCJ) | judicial_registry | GB | paid_gateway | true | **false** | secondary_corroboration | Redistribution rights pending. Assessment unchanged from existing registry entry |
| The Gazette | judicial_registry | GB | public_api | true | true | primary_evidence | **Already in registry (Cycle-006).** London/Edinburgh/Belfast. Do not re-add as duplicate |

### Transport / Maritime / Infrastructure

| Source | source_group | access_surface | confirmed | settlement_eligible | resolution_role | Notes |
|--------|-------------|---------------|-----------|-------------------|----------------|-------|
| UK Rail (NR Open Data) | transport_infrastructure | public_api | true | false | counter_signal | `counter_signal_class: infrastructure_outage`. Rail disruption as settlement timing anomaly signal |
| Spire Global (AIS) | maritime_ais | paid_gateway | true | false | secondary_corroboration | `independence_upstream_id: imo_ais_transmission`. Cannot corroborate MarineTraffic — same upstream |
| MarineTraffic (AIS) | maritime_ais | paid_gateway | true | false | secondary_corroboration | `independence_upstream_id: imo_ais_transmission`. Cannot corroborate Spire — same upstream |

### Scientific / IP

| Source | source_group | access_surface | confirmed | settlement_eligible | resolution_role | Notes |
|--------|-------------|---------------|-----------|-------------------|----------------|-------|
| CERN Open Data | scientific_registry | public_api | true | false | secondary_corroboration | Low priority unless specific Theatre vertical requires it |
| AU Patents (IP Rights B2B) | intellectual_property | partner_api | true | true (candidate) | primary_evidence | OAuth2. Patent grant dates are immutable. Fills APAC gap alongside EPO OPS (EU) and USPTO PatentsView (US) |

### UAE Jurisdiction (from PDF)

| Source | source_group | upstream_id | access_surface | confirmed | settlement_eligible | Notes |
|--------|-------------|-------------|---------------|-----------|-------------------|-------|
| NER (National Economic Register) | uae_federal_registry | uae_moe_ner | partner_api | true | true (candidate) | Requires UAE trade licence + UAE PASS via API Marketplace |
| DIFC Public Register | uae_freezone_registry_difc | salesforce_difc_client | public_api | true | true | Via Dubai Pulse |
| ADGM Public Register | uae_freezone_registry_adgm | adgm_ors | portal_scrape | **false** | false | Scrape only — non-deterministic |
| VARA Public Register | uae_dubai_regulator_vara | vara_registry | portal_scrape | **false** | false | Scrape only — non-deterministic |
| FTA TRN Verification | uae_federal_registry | fta_emaratax | portal_scrape | **false** | false | CAPTCHA protected — non-deterministic |
| DLD Open Data (Transactions) | uae_property_registry_dld | dld_tabu_system | public_api | true | true | Via Dubai Pulse. OAuth. `query_determinism: pure_id_lookup` |
| Dubai Municipality BPS | uae_property_registry_dm | dm_prt_system | public_api | true | true | Via Dubai Pulse. Building permits |
| Ejari | uae_rental_registry | dld_ejari_system | partner_api | true | true (candidate) | Formalised rental contracts |
| RDC (Rental Dispute Centre) | uae_judicial_registry | dld_rdc_system | portal_scrape | **false** | false | App/portal scrape — `counter_signal_class: legal_dispute_active` |
| UAE Insolvency Register | uae_insolvency | uae_moj_bankruptcy_register | portal_scrape | **false** | false | No API access confirmed |
| PPSR (AU) | lien_registry | afsa_ppsr | partner_api | true | true | B2G channel. Security interests register |
| UAE PASS | identity_attestation | uae_pass_system | partner_api | true | N/A | Digital signature / manual attestation bridge. Not a data source — attestation mechanism |

**Key UAE finding:** Dubai Pulse aggregates multiple upstream sources (DLD, Municipality, DIFC). The `independence_upstream_id` architecture correctly prevents Dubai Pulse datasets backed by the same system (e.g. DLD TABU) from corroborating each other.

---

## Spatial Intelligence / Aviation / Visual Sources

**Source:** Opus review of Bilawal Sidhu's Spatial Intelligence spy satellite simulator (spatialintelligence.ai), 3 March 2026. His stack: Google 3D Tiles + OpenSky + ADS-B Exchange + CelesTrak + OSM + CCTV, fused in a browser with geographic convergence. Multi-source OSINT fusion — same architectural pattern as WorldMonitor, but visual-first rather than verification-first.

### Source Assessments

| Source | source_group | access_surface | confirmed | settlement_eligible | resolution_role | Notes |
|--------|-------------|---------------|-----------|-------------------|----------------|-------|
| OpenSky Network | aviation_ais | public_api | true | false | counter_signal | Real-time ADS-B aircraft positions. No auth. `revision_policy: latest_only` (positions are ephemeral). `counter_signal_class: aviation_anomaly`. `independence_upstream_id: adsb_broadcast`. WorldMonitor already consumes aviation signals upstream — only needed as a direct collector if WM independence is required for aviation counter-signals. **Same shared-upstream trap as AIS:** OpenSky and ADS-B Exchange both receive the same ADS-B broadcast transmissions. |
| ADS-B Exchange | aviation_ais | public_api | true | false | counter_signal | Crowdsourced military flight tracking. Better military coverage than OpenSky (fewer filters on military transponders). `independence_upstream_id: adsb_broadcast` — shared with OpenSky for civilian aircraft. Military-specific tracks may be independently sourced. Not a priority while WM covers aviation. |
| CelesTrak TLE | satellite_orbital | public_api | true | false | secondary_corroboration | Satellite orbital elements (Two-Line Element sets). Maintained by US Space Force data. `revision_policy: latest_only` (orbital predictions, not verified positions). Only relevant for niche Theatres: "was satellite X in position to image location Y at time Z?" Extremely low priority. |

### Non-OSINT Sources (Rendering / Geographic Context)

These appeared in Bilawal's stack but are **not** OSINT registry candidates:

- **OpenStreetMap** — mapping dataset, not an event source. Provides geographic context for interpreting other sources. No evidence bundles, no receipts. WorldMonitor already uses geographic layers upstream. Skip.
- **Google Photorealistic 3D Tiles** — visualisation infrastructure, not a data source. Relevant to Results Surface (Cycle-016) as a rendering dependency if a globe view with convergence zones is built. Paid API with usage-based pricing. Note for 016 scope, not for registry.

### Public CCTV Cameras

The genuinely novel source from Bilawal's stack. Government transport authorities publish real-time camera feeds openly (Austin traffic cameras in his demo).

- `access_surface: public_api` (many transport authorities publish feeds openly)
- `settlement_eligible: false` (video streams, no deterministic query)
- `resolution_role: counter_signal`
- `counter_signal_class: visual_confirmation` (new class — visual corroboration of event presence)

**Value for Echelon:** if the OSINT pipeline says there's a protest at a specific location, a CCTV feed showing crowds is a visual counter-signal that confirms or contradicts. But ingesting video feeds is a fundamentally different pipeline from JSON API responses — requires frame capture, timestamp verification, and a completely different receipt model. **High complexity, low priority** relative to current roadmap. Defer until post-017 at earliest.

### Spatial Intelligence Takeaways for Echelon

1. **Results Surface visual language** — convergence alerts (multiple OSINT sources lighting up the same geographic area simultaneously) displayed on a globe view with Logic Gap heat maps and live market prices overlaid on geographic data would be Echelon's "God mode" equivalent. Note for Cycle-016 scope.
2. **WorldMonitor already covers the critical feeds** — aviation (OpenSky/ADS-B), maritime (AIS), protest/conflict (ACLED/GDELT). Direct collectors for these sources are only needed for WM independence.
3. **No missing sources that gate any settlement path** — all of Bilawal's sources are either already consumed via WM upstream, rendering infrastructure, or too complex for the current pipeline (CCTV).

---

## Corrections Needed on Source Documents

1. **PDF page 2:** "RFC 8785" → "Echelon Canonical JSON v0" (Cycle-008 errata)
2. **Gemini output:** No cycle context. All assessments are pre-build. Cross-reference against current registry v0.4.0 before adding any source to avoid duplicates
3. **NPI Registry:** Gemini lists as Priority 1 settlement-eligible. Downgraded to `false` — `revision_policy: latest_only` without historical snapshots
4. **UK sources:** Gemini merges case law and legislation under one entry. Split into 5 separate entries (Registry Trust, TNA caselaw, Parliament API, legislation.gov.uk, The Gazette — last one already in registry)
5. **AIS sources:** Gemini lists separately but doesn't flag shared upstream. Both MUST share `independence_upstream_id: imo_ais_transmission`

---

## Build Priority

None of this is in any active cycle. Registry expansion is currently Cycle-017 in the platform roadmap.

### When to Implement — Dependency Analysis (3 March 2026)

The registry expansion (017) sits at the end of the current roadmap: 012 → 013 → 014 → 015 → 016 → 017. The question is whether that's the right position.

**What 017 actually does:** adds schema fields (`query_determinism`, `receipt_body_required`, `requires_legal_review`) and Tier 2 source stubs. It makes existing Theatres more reliable but doesn't unlock new product surfaces.

**What depends on 017:** nothing in the current roadmap. No cycle between 012 and 016 requires the expanded registry. The existing registry (v0.4.0, 57 sources, 7 jurisdictions) is sufficient for all planned Theatres through 016.

**What 017 depends on:** Cycle-015 (live collectors proven). The schema additions need at least one live non-WM collector to validate against. Without 015's Companies House live collector, the new schema fields are theoretical — you can write the validator but can't test it against real evidence flow.

**Can schema additions be pulled earlier?** Partially. The three schema fields (Tier 1 work) are pure registry changes — they don't touch the market engine, agent runtime, or evidence pipeline. They could technically ship as a small patch cycle between any two cycles. But there's no urgency: no Theatre is blocked by missing `query_determinism`, and no source currently in the registry produces incorrect settlement eligibility without it. The validator would fire on zero existing sources.

**The case for keeping 017 where it is:**
- 012–016 build the product (markets, agents, inquiries, evidence, UI). 017 improves reliability of that product. Reliability work after the product exists is the right order.
- Pulling schema additions earlier creates schema churn before the pipeline is stable. Better to batch all registry changes once the evidence flow from 015 proves what the schema actually needs.
- The Tier 2 source stubs (USA Spending, UK Case Law, etc.) are meaningless without live collectors to ingest from them. 015 proves the collector pattern; 017 applies it to more sources.

**The case for pulling part of 017 earlier (between 015 and 016):**
- If the Results Surface (016) wants to display source reliability metadata (query determinism, legal review flags), those schema fields need to exist before 016 builds its UI.
- Recommendation: if 016 scope includes source-level metadata display, move Tier 1 schema additions to a 015b patch or fold them into 015's scope. Leave Tier 2–5 source stubs in 017.

**Verdict:** keep 017 where it is unless 016 scope requires source metadata display, in which case pull Tier 1 schema additions into 015.

When a registry expansion cycle is scoped:

**Tier 1 — Schema additions (do first):**
- `query_determinism` field + validator constraint
- `receipt_body_required` field (GraphQL/POST rule)
- `requires_legal_review` field

**Tier 2 — High-value source stubs:**
- USA Spending, NIH RePORTER (sovereign, settlement-eligible, no auth)
- UK Case Law (TNA), UK Parliament API, UK Legislation (sovereign, immutable/timestamped)
- AU Patents (APAC gap fill)

**Tier 3 — UAE jurisdiction (partner access required):**
- DLD, Dubai Municipality BPS, DIFC (confirmed public API via Dubai Pulse)
- NER, Ejari (partner_api, credential provisioning needed)

**Tier 4 — Scoring-grade / corroboration / counter-signal sources:**
- ChEMBL, PubChem, OpenTargets, FMP, German Labour, CERN
- OpenSky Network (`counter_signal_class: aviation_anomaly`, `independence_upstream_id: adsb_broadcast`) — only if WM-independent aviation signals needed
- These add depth to DeltaBrief and Mission Factory but don't gate any settlement path

**Tier 5 — Novel pipeline (post-017, requires new ingestion architecture):**
- Public CCTV feeds (`counter_signal_class: visual_confirmation`) — video frame capture, timestamp verification, new receipt model. High complexity.
