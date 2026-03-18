# PRD — Cycle-027: OSINT Registry Expansion — Batch 2

**Cycle:** cycle-027
**Date:** 17 March 2026
**Depends on:** Cycle-026 (OSINT Registry Expansion Batch 1 — 10 collectors, `build_collector_map()`, persist_signal integration proven)
**Sprints:** 3 (0–2)
**Builder:** Loa (backend only — Alexander handles frontend after this cycle ships)
**Planning source:** `worldmonitor_osint_expansion_draft.md` Section 6 / Appendix A.21 Batch 2

---

## 1. Problem Statement

### 1.1 The Registry Is US/GB/GLOBAL-Centric — 5 Jurisdictions Are Missing

After Cycle 026 ships, the registry has 16 sources across 5 jurisdictions (US, GB, GLOBAL, EU, ETH). The expansion audit identified 8+ additional jurisdictions needed for multi-regional investigation coverage. Bounded inquiries involving European procurement, Asian regulatory filings, or cross-jurisdiction corporate analysis cannot be resolved without sources in those jurisdictions.

### 1.2 European Procurement Is A High-Value Corroboration Source

Five EU member states plus Ukraine publish public procurement data through standardised APIs. Procurement data is immutable (once published), settlement-eligible, and directly relevant to investigation classes involving government contracts, corruption risk, and cross-border financial flows. These are primary_evidence sources — not enrichment.

### 1.3 Government Open Data Portals Enable Multi-Jurisdiction Entity Resolution

OpenCorporates (Batch 1) provides corporate entity data, but government-published datasets from FR, DE, SG, IN, and TW provide complementary official data that strengthens corroboration scores. German Bundestag DIP adds legislative proceedings as an immutable, settlement-eligible source — unique in the registry.

### 1.4 Convergence Scorer Needs Jurisdiction Diversity

The `CROSS_DOMAIN_CONVERGENCE` measure (Cycle 025) scores signal convergence across domains. Jurisdiction diversity strengthens convergence — a signal from `fr_open_gov` + `global_opencorporates` + `us_fred_api` referencing the same entity produces higher confidence than three US-only sources.

---

## 2. Product Contracts

### 2.1 Eleven New Sources In Registry v0.6.0

Expand `sources.json` from 16 → 27 entries. Version bump to `0.6.0`.

**Government open data portals — 6 sources:**

| # | source_id | Name | jurisdiction | source_group | auth | settlement_eligible | resolution_role |
|---|---|---|---|---|---|---|---|
| 1 | fr_open_gov | French Open Data | FR | official_gov | apiKey | false | secondary_corroboration |
| 2 | de_open_gov | German Open Data | DE | official_gov | none | false | secondary_corroboration |
| 3 | de_bundestag_dip | German Bundestag DIP | DE | official_gov | apiKey | true | primary_evidence |
| 4 | sg_open_gov | Singapore Open Data | SG | official_gov | none | false | secondary_corroboration |
| 5 | in_open_gov | Indian Open Data | IN | official_gov | apiKey | false | secondary_corroboration |
| 6 | tw_open_gov | Taiwan Open Data | TW | official_gov | none | false | secondary_corroboration |

**European procurement APIs — 5 sources:**

| # | source_id | Name | jurisdiction | source_group | auth | settlement_eligible | resolution_role |
|---|---|---|---|---|---|---|---|
| 7 | hu_tenders | Hungarian Procurement | HU | official_gov | none | true | primary_evidence |
| 8 | pl_tenders | Polish Procurement | PL | official_gov | none | true | primary_evidence |
| 9 | ro_tenders | Romanian Procurement | RO | official_gov | none | true | primary_evidence |
| 10 | es_tenders | Spanish Procurement | ES | official_gov | none | true | primary_evidence |
| 11 | ua_tenders | Ukrainian Procurement (Prozorro) | UA | official_gov | none | true | primary_evidence |

### 2.2 No New source_group Values Needed

All 11 sources map to `official_gov` — already in `_VALID_SOURCE_GROUPS`. No enum extension required.

### 2.3 Eleven New BaseCollector Subclasses

Each collector follows the established contract from Cycle 026:
- Extends `BaseCollector`
- Implements `source_id() -> str`, `_fetch()`, `health_check()`, `_do_http_get()` (per-collector private)
- Returns `CollectionResult` with `EvidenceBundle` on success
- Hash invariant enforcement via `BaseCollector.fetch()` wrapper

**Collector architecture:**

| Collector class | File | API base URL | Auth pattern |
|---|---|---|---|
| FrenchOpenGovCollector | `backend/osint/collectors/fr_open_gov.py` | `https://www.data.gouv.fr/api/1` | apiKey header |
| GermanOpenGovCollector | `backend/osint/collectors/de_open_gov.py` | `https://www.govdata.de/ckan/api/3` | none |
| BundestagDIPCollector | `backend/osint/collectors/bundestag_dip.py` | `https://search.dip.bundestag.de/api/v1` | apiKey header |
| SingaporeOpenGovCollector | `backend/osint/collectors/sg_open_gov.py` | `https://data.gov.sg/api/action` | none |
| IndianOpenGovCollector | `backend/osint/collectors/in_open_gov.py` | `https://data.gov.in/api/datastore` | apiKey query param |
| TaiwanOpenGovCollector | `backend/osint/collectors/tw_open_gov.py` | `https://data.gov.tw/api/v2` | none |
| HungarianTendersCollector | `backend/osint/collectors/hu_tenders.py` | `https://kozbeszerzes.hu/api` | none |
| PolishTendersCollector | `backend/osint/collectors/pl_tenders.py` | `https://api.uzp.gov.pl/api` | none |
| RomanianTendersCollector | `backend/osint/collectors/ro_tenders.py` | `https://data.anap.gov.ro/api` | none |
| SpanishTendersCollector | `backend/osint/collectors/es_tenders.py` | `https://contrataciondelestado.es/sindicacion` | none |
| UkrainianTendersCollector | `backend/osint/collectors/ua_tenders.py` | `https://public-api.prozorro.gov.ua/api` | none |

### 2.4 API Key Configuration

| Env var | Source | Free tier |
|---|---|---|
| `ECHELON_FR_OPEN_GOV_API_KEY` | French Open Data | Generous (CKAN standard) |
| `ECHELON_BUNDESTAG_DIP_API_KEY` | Bundestag DIP | Generous |
| `ECHELON_IN_OPEN_GOV_API_KEY` | Indian Open Data | Moderate |

Sources without API keys (DE, SG, TW, HU, PL, RO, ES, UA) need no env vars.

### 2.5 CollectionRunner Registration

Wire all 11 new collectors into `build_collector_map()`. Total collectors after wiring: 24 (3 WM + 10 Batch 1 + 11 Batch 2).

---

## 3. What This Cycle Does NOT Do

- **Does NOT build Batch 3/4 collectors.** Signal Scanner enrichment (GNews, MarketAux, counter-signals) is Cycle 028+.
- **Does NOT add new source_group values.** All sources use existing `official_gov`.
- **Does NOT add new MeasureType values.** Uses existing 14 MeasureType values.
- **Does NOT touch the osint_signals table schema.** Uses table and `persist_signal` as-is.
- **Does NOT modify POST endpoints.** WorldMonitor routes remain unchanged.
- **Does NOT touch frontend.** Alexander wires signal layer after backend parity.
- **Does NOT touch Path 2** (synthetic SignalDetector).

---

## 4. Acceptance Criteria

1. `sources.json` has 27 entries, version `0.6.0`
2. All 11 new collectors instantiate, pass health_check (mocked in CI), and produce valid `CollectionResult`
3. All 11 collectors are registered in CollectionRunner at app startup
4. Each collector produces an `EvidenceBundle` with valid `HTTPTranscriptReceipt` (hash invariants pass)
5. Signals from all 11 collectors persist to `osint_signals` table via `persist_signal`
6. `GET /api/v1/osint/signals?jurisdiction=DE` returns signals from de_open_gov and de_bundestag_dip
7. `GET /api/v1/osint/signals?jurisdiction=UA` returns signals from ua_tenders
8. API keys load from env vars; missing key → collector returns `CollectionResult(success=False)` with descriptive error
9. No-auth collectors work without any env var
10. Registry covers 9 jurisdictions: US, GB, GLOBAL, EU, ETH, FR, DE, SG, IN, TW, HU, PL, RO, ES, UA (15 unique, mapped to 9 canonical jurisdictions via ISO grouping)
11. ≥24 new tests pass
12. `npm run build` continues to pass (no frontend changes)

---

## 5. Test Plan

| Area | Tests | Coverage |
|---|---|---|
| sources.json validation | 2 | 27 entries load, RegistryLoader.validate() passes |
| FrenchOpenGovCollector | 2 | Success (mocked), auth failure |
| GermanOpenGovCollector | 2 | Success, empty dataset |
| BundestagDIPCollector | 2 | Success, invalid Drucksache ID |
| SingaporeOpenGovCollector | 2 | Success, no datasets matching query |
| IndianOpenGovCollector | 2 | Success, auth failure |
| TaiwanOpenGovCollector | 2 | Success, empty response |
| HungarianTendersCollector | 2 | Success, no tenders in window |
| PolishTendersCollector | 2 | Success, no tenders in window |
| RomanianTendersCollector | 2 | Success, malformed response |
| SpanishTendersCollector | 2 | Success, XML parse error |
| UkrainianTendersCollector | 2 | Success (Prozorro JSON), no tenders |
| CollectionRunner wiring | 1 | All 24 collectors registered |
| persist_signal integration | 1 | Batch 2 signals written and queryable by jurisdiction |
| **Total** | **~26** | |
