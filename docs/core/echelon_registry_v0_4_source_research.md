# OSINT Source Registry v0.4 — Source Research

## Research Summary

Candidate sources for closing jurisdictional gaps identified in Spec v2, Section 7.

---

## 1. ASIC (Australian Securities & Investments Commission)

**Purpose:** AU entity verification (companies, business names). Closes the AU entity gap.

**Access surface:** `partner_api`

ASIC does not offer a direct public REST API for company lookups. Their M2M interface uses SOAP web services with username/password authentication issued by ASIC. Access requires registration as a Digital Service Provider (DSP). Third-party paid gateways exist (Dye & Durham/GlobalX API Connect, Vigil.sh, GetEDGE) that wrap ASIC data into REST APIs.

**Options:**
- **Direct ASIC SOAP API** — requires DSP registration, SOAP client, ASIC-issued credentials. Access surface: `partner_api`. Settlement-eligible if we get direct access.
- **Vigil.sh / Dye & Durham** — REST API wrappers over ASIC. Access surface: `paid_gateway`. NOT settlement-eligible (intermediary adds latency and mutation risk).

**Recommendation:** Register as ASIC DSP for direct SOAP access. Until then, use Vigil.sh as `scoring_grade` source.

| Field | Value |
|-------|-------|
| source_id | `asic_company_register` |
| source_group | `official_gov` |
| resolution_role | `primary_evidence` |
| priority_bucket | `scoring_grade` (upgrade to `settlement_grade` after DSP registration) |
| settlement_eligible | `false` (until direct SOAP access confirmed) |
| jurisdiction | `AU` |
| access_surface | `paid_gateway` (→ `partner_api` after DSP) |
| revision_policy | `latest_only` |
| receipt_mode_minimum | `http_transcript` |
| independence_upstream_id | `au_asic_company_register` |
| auth_methods | `["api_key"]` (Vigil) / `["basic"]` (ASIC SOAP) |
| api_url | `https://developer.vigil.sh/api/asic/company/` (interim) |
| ui_url | `https://connectonline.asic.gov.au/` |
| access_proof | `{ doc_url: "https://www.asic.gov.au/online-services/information-for-intermediaries/application-programming-interfaces-apis/", verified: false, proof_type: "official_docs" }` |

---

## 2. RBA (Reserve Bank of Australia)

**Purpose:** AU interest rates, exchange rates, macro data. Closes AU rates gap.

**Access surface:** `portal_scrape` (no official REST API)

RBA publishes statistical tables as downloadable Excel/CSV files at `rba.gov.au/statistics/tables/`. No official REST API exists. Third-party wrappers exist (readrba R package, community Lambda APIs, exchangeratesapi.com.au) but none are official.

Data is publicly available and effectively immutable once published (historical tables don't change). However, the lack of a documented API means we must scrape or download files — no cryptographic receipt chain possible from the source.

**Recommendation:** Add as `scoring_grade` only. Use the published CSV download URLs for `http_transcript` receipts. Cannot be settlement-grade due to `portal_scrape` access surface.

| Field | Value |
|-------|-------|
| source_id | `rba_statistics` |
| source_group | `market_data` |
| resolution_role | `secondary_corroboration` |
| priority_bucket | `scoring_grade` |
| settlement_eligible | `false` |
| jurisdiction | `AU` |
| access_surface | `portal_scrape` |
| revision_policy | `immutable` (published tables don't change) |
| receipt_mode_minimum | `http_transcript` |
| independence_upstream_id | `au_rba_statistics` |
| auth_methods | `["none"]` |
| api_url | `null` |
| ui_url | `https://www.rba.gov.au/statistics/tables/` |
| access_proof | `{ doc_url: "https://www.rba.gov.au/statistics/tables/", verified: true, proof_type: "official_docs" }` |
| access_surface_confirmed | `true` |
| note | "RBA publishes Excel/CSV statistical tables. No official REST API. Data accessed by downloading published files. Third-party wrappers exist but are not authoritative." |

---

## 3. PACER (Public Access to Court Electronic Records)

**Purpose:** US federal court records, bankruptcy filings, civil litigation. Closes US judicial gap.

**Access surface:** `paid_gateway`

PACER has two official REST APIs:
- **Authentication API** — username/password → token exchange
- **PCL (PACER Case Locator) API** — REST, JSON/XML, search cases and parties nationwide

Charges: $0.10/page, capped at $3.00 per document. Fees waived if quarterly total ≤ $30. Free PACER account registration available.

Alternative: **CourtListener/RECAP** (Free Law Project) provides free REST API (v4.3) with extensive PACER data, but is not the system of record.

**Recommendation:** Add PACER as `settlement_grade` with `paid_gateway` access surface. Also add CourtListener as `scoring_grade` corroboration source.

### 3a. PACER (Direct)

| Field | Value |
|-------|-------|
| source_id | `us_pacer` |
| source_group | `official_gov` |
| proposed_source_group | `judicial_record` |
| resolution_role | `primary_evidence` |
| priority_bucket | `settlement_grade` |
| settlement_eligible | `true` |
| jurisdiction | `US` |
| access_surface | `paid_gateway` |
| revision_policy | `as_of_timestamp` (docket entries are immutable once filed; new entries append) |
| receipt_mode_minimum | `http_transcript` |
| independence_upstream_id | `us_uscourts_cmecf` |
| auth_methods | `["basic"]` (username/password → token) |
| api_url | `https://pcl.uscourts.gov/pcl-public-api/rest/` |
| ui_url | `https://pacer.uscourts.gov/` |
| access_proof | `{ doc_url: "https://pacer.uscourts.gov/file-case/developer-resources", verified: true, proof_type: "official_docs" }` |
| access_surface_confirmed | `true` |
| counter_signal_class | `null` |

### 3b. CourtListener / RECAP

| Field | Value |
|-------|-------|
| source_id | `courtlistener_recap` |
| source_group | `official_gov` |
| proposed_source_group | `judicial_record` |
| resolution_role | `secondary_corroboration` |
| priority_bucket | `scoring_grade` |
| settlement_eligible | `false` |
| jurisdiction | `US` |
| access_surface | `public_api` |
| revision_policy | `latest_only` (mirror updated as documents are purchased) |
| receipt_mode_minimum | `http_transcript` |
| independence_upstream_id | `us_uscourts_cmecf` |
| auth_methods | `["api_key"]` |
| api_url | `https://www.courtlistener.com/api/rest/v4/` |
| ui_url | `https://www.courtlistener.com/` |
| access_proof | `{ doc_url: "https://www.courtlistener.com/help/api/rest/", verified: true, proof_type: "official_docs" }` |
| access_surface_confirmed | `true` |
| note | "CourtListener is a Free Law Project (501(c)(3)) mirror of PACER data. NOT the system of record. Shares independence_upstream_id with PACER — cannot corroborate each other per dedupe rule." |

**⚠ IMPORTANT:** CourtListener and PACER share `independence_upstream_id: us_uscourts_cmecf`. The dedupe runner will correctly collapse these to one corroborator. This is by design — CourtListener is a mirror, not an independent source. It provides a free fallback when PACER is unavailable, not independent corroboration.

---

## 4. Handelsregister (German Commercial Register)

**Purpose:** DE entity verification. Begins closing EU entity-level gap.

**Access surface:** `paid_gateway` (no direct government API for entity lookups)

The official portal (`handelsregister.de`) is web-only with no public REST API. Access is through third-party paid gateways:
- **handelsregister.ai** — REST API, credit-based pricing, free tier available, daily updated from official register. Munich-based (Fusionbase).
- **Apify actors** — scraping wrappers around handelsregister.de
- **OpenAPI SpA** — Company Start Germany REST API

Data quality is high (sourced from 150 Registergerichte across all 16 Bundesländer), but access is intermediated.

**Recommendation:** Add handelsregister.ai as `scoring_grade`. Cannot be settlement-grade because: (a) paid gateway intermediary, (b) `latest_only` revision policy. If Germany introduces a direct government API in future, upgrade path is clear.

| Field | Value |
|-------|-------|
| source_id | `de_handelsregister` |
| source_group | `official_gov` |
| resolution_role | `primary_evidence` |
| priority_bucket | `scoring_grade` |
| settlement_eligible | `false` |
| jurisdiction | `EU` |
| access_surface | `paid_gateway` |
| revision_policy | `latest_only` |
| receipt_mode_minimum | `http_transcript` |
| independence_upstream_id | `de_handelsregister_registergerichte` |
| auth_methods | `["api_key"]` |
| api_url | `https://api.handelsregister.ai/v2/companies/` |
| ui_url | `https://www.handelsregister.de/` |
| access_proof | `{ doc_url: "https://handelsregister.ai/en", verified: true, proof_type: "official_docs" }` |
| access_surface_confirmed | `true` |

---

## 5. INPI RNE (French National Enterprise Register)

**Purpose:** FR entity verification. Further closes EU entity-level gap.

**Access surface:** `public_api` ✓

France is the standout winner here. Since 1 January 2023, the INPI operates the Registre National des Entreprises (RNE) — a single unified digital register replacing the old RNCS. INPI provides:
- **Free JSON API** via data.inpi.fr for company data, annual accounts, and legal acts
- **SFTP bulk access** for mass data downloads
- **API Entreprise** (api.gouv.fr) — government-to-government API (restricted to administrations)
- **Annuaire des Entreprises** — public search API powered by RNE + INSEE Sirene data

The public data.inpi.fr API is open, JSON-based, free, and documented. This is a genuine government `public_api` — rare for EU entity registers.

**Recommendation:** Add as `settlement_grade`. This is the strongest EU entity source available. `public_api` access, government-operated, JSON format, documented.

| Field | Value |
|-------|-------|
| source_id | `fr_inpi_rne` |
| source_group | `official_gov` |
| resolution_role | `primary_evidence` |
| priority_bucket | `settlement_grade` |
| settlement_eligible | `true` |
| jurisdiction | `EU` |
| access_surface | `public_api` |
| revision_policy | `as_of_timestamp` (formalités API supports date-based queries) |
| receipt_mode_minimum | `http_transcript` |
| independence_upstream_id | `fr_inpi_rne` |
| auth_methods | `["registration"]` (free account required for API access) |
| api_url | `https://data.inpi.fr/api/` |
| ui_url | `https://data.inpi.fr/` |
| access_proof | `{ doc_url: "https://www.inpi.fr/ressources/formalites-dentreprises/acces-lapi-formalite-rne", verified: true, proof_type: "official_docs" }` |
| access_surface_confirmed | `true` |
| note | "Since 1 Jan 2023, INPI operates the unified Registre National des Entreprises (RNE) under the Loi Pacte. Free JSON API for public company data. This is a genuine government public_api — strongest EU entity source available." |

---

## Summary: Proposed v0.4 Additions

| source_id | Jurisdiction | Priority | Settlement | Access |
|-----------|-------------|----------|------------|--------|
| asic_company_register | AU | scoring_grade | No (pending DSP) | paid_gateway |
| rba_statistics | AU | scoring_grade | No | portal_scrape |
| us_pacer | US | settlement_grade | Yes | paid_gateway |
| courtlistener_recap | US | scoring_grade | No | public_api |
| de_handelsregister | EU | scoring_grade | No | paid_gateway |
| fr_inpi_rne | EU | settlement_grade | Yes | public_api |

**Net effect on jurisdictional readiness:**

| Jurisdiction | Before v0.4 | After v0.4 |
|-------------|-------------|------------|
| AU | 1 settlement source (AFSA) | 1 settlement + 2 scoring (ASIC, RBA) |
| US | 3 settlement sources | 4 settlement (+ PACER) + 1 scoring (CourtListener) |
| EU | 1 settlement source (ECB) | 2 settlement (+ INPI RNE) + 1 scoring (Handelsregister) |

**Registry totals after v0.4:** 57 sources, 7 jurisdictions, 14 settlement-eligible.

---

## Deferred Sources (Cycle-040+)

- **BODACC** (FR) — Bulletin Officiel Des Annonces Civiles et Commerciales. French insolvency/liquidation announcements. `judicial_record` candidate. Requires template v1.1.
- **Bundesanzeiger** (DE) — German Federal Gazette. Insolvency announcements. `judicial_record` candidate.
- **Lean / Tarabut** (AE/MENA) — Open banking APIs. Deferred per Spec v2 roadmap.
- **PPSA provincial registries** (CA) — Canadian personal property security. Requires per-province research.
- **Australian PPSR** — Already in registry (v0.3.2). No changes needed.
