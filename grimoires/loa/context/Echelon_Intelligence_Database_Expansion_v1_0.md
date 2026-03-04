# Echelon Intelligence Database Expansion v1.0.0

**Version:** 1.0.0
**Date:** 1 March 2026
**Status:** Normative — supersedes settlement-only registry framing (v0.6.0)
**Supersedes:** OSINT Source Registry v0.6.0 (Cycle-003, shipped and archived)
**Classification:** Internal architecture + grant collateral
**Registry target:** v1.0.0 (160+ sources, 30 source groups, 7 consumption surfaces)

**What changed from v0.6.0:** Reframed from settlement-only catalogue to full-platform intelligence database. Added consumption_surfaces taxonomy (7 surfaces), access_tier classification (A/B/C/paid), per-source API endpoints, 17 new source groups (incl. intellectual_property, entity_resolution, geospatial_verification), SitDeck 14-category parity mapping, WorldMonitor Layer 0 integration strategy, and build priority by surface coverage count. Total sources expanded from 77 to 160+.

---

## 1. Governing Principle

The OSINT Source Registry (v0.6.0, 77 sources, Cycle-003) was designed to answer one question: can this source settle a Theatre? That framing served the verification engine but left six other product surfaces starved of intelligence. Echelon is a prediction market platform, an intelligence platform, and a verification platform. Every surface consumes data differently, and every source has value beyond settlement.

This specification reframes the registry from a settlement catalogue into a full-platform intelligence database. It merges the architectural framework (consumption surfaces taxonomy, schema additions, build priority logic) with a granular collector manifest (actual API endpoints, authentication requirements, rate limits, and access tier classifications).

### 1.1 Access Tier Classification

Every source is classified into one of three access tiers. This classification determines build order — a Tier A source can have a working collector in 20 minutes; a Tier C source needs rate limit handling, retry logic, and quota monitoring.

| Tier | Definition | Build Effort | Examples |
|------|-----------|-------------|----------|
| Tier A | No auth required (may have rate limits). Just curl. | 20 minutes | USGS, GDACS, UK Case Law, Wikidata SPARQL |
| Tier B | Free with registration. API key from a free account. No cost, fair use limits. | 1 hour | NASA FIRMS, ACLED, Met Office, EIA |
| Tier C | Free tier with genuine limits. Rate-limited but usable at low volume. | 2-4 hours | OpenCorporates (50 req/day anon), Alpha Vantage (5 req/min) |

---

## 2. Seven Consumption Surfaces

Every intelligence source serves one or more consumption surfaces. Each surface has distinct quality requirements, latency tolerances, and provenance obligations. Sources are ranked by the number of surfaces they serve, not solely by settlement eligibility.

| Surface | Quality Tier | Latency | Provenance | Purpose |
|---------|-------------|---------|-----------|---------|
| Theatre Settlement | Settlement-grade | Minutes | Full chain | Deterministic resolution of prediction markets against committed evidence bundles with cryptographic receipts, corroboration minimums, and source independence enforcement. |
| Mission Factory | Anomaly-detection | Minutes | Source ID only | Detect world events worth creating prediction markets about. Breadth over depth. Engagement Score evaluates narrative strength, timeliness, OSINT richness, volume potential, ripple potential. |
| Bounded Inquiries | Investigation-grade | Seconds | Source metadata | Signal feed for the five-class inquiry system. Every visible signal is a potential inquiry trigger. Richer feeds mean more inquiries, more certificates, more RLMF data. |
| DeltaBrief / Novelty | Change-detection | Minutes | Baseline hash | Compare current state against pinned baselines. Flag what is new. Requires broadest observation surface. |
| Agent Context | Reasoning-grade | Seconds | Attribution | Contextual intelligence for agents trading in Theatres. Sanctions, weather, litigation, macro shifts, supply chain disruptions. |
| Consumer Dashboard | Display-grade | Real-time | Source label | PizzINT-style consumer surface. User acquisition channel — people come for the dashboard, discover verification. |
| Sponsored Theatre | Commercial-grade | Minutes | Full chain | Enrichment layer for commissioned prediction markets. Cross-references disruptions, planning, weather, litigation, materials prices. |

---

## 3. Expanded Registry Schema

The existing 19-field per-source schema (v0.6.0) is preserved in full. This specification adds new fields. The schema remains backwards-compatible.

### 3.1 New Field: consumption_surfaces

Array of objects. Each: `{ "surface": enum, "quality_tier": enum, "update_interval_seconds": integer|null, "notes": string|null }`

Surface enum values: `theatre_settlement`, `mission_factory`, `bounded_inquiry`, `delta_brief`, `agent_context`, `consumer_dashboard`, `sponsored_theatre`.

**Note:** This document is the collector manifest and architectural specification. The actual populated consumption_surfaces arrays per source live in the registry JSON (`echelon_osint_source_registry_v1_0_0.json`), not here. The collector manifest tables below show surface counts (e.g. "5/7") as a build priority indicator. One worked example follows.

#### 3.1.1 Worked Example: OFAC SDN

```json
{
  "source_id": "ofac_sdn_api",
  "consumption_surfaces": [
    { "surface": "theatre_settlement", "quality_tier": "settlement_grade", "update_interval_seconds": 86400, "notes": "Daily SDN list update" },
    { "surface": "mission_factory", "quality_tier": "anomaly_detection", "update_interval_seconds": 86400 },
    { "surface": "bounded_inquiry", "quality_tier": "investigation_grade" },
    { "surface": "delta_brief", "quality_tier": "change_detection", "update_interval_seconds": 86400 },
    { "surface": "agent_context", "quality_tier": "reasoning_grade" },
    { "surface": "consumer_dashboard", "quality_tier": "display_grade" },
    { "surface": "sponsored_theatre", "quality_tier": "settlement_grade" }
  ]
}
```

### 3.2 New Field: access_tier

Enum: `"tier_a"` | `"tier_b"` | `"tier_c"` | `"paid"`. Replaces the informal free/paid distinction with the three-tier classification. Paid sources are excluded from the free-first build strategy.

### 3.3 New Field: api_endpoint

String or null. The actual callable API URL (base path). Distinct from the existing `api_url` field which stores the documented root. This field stores the specific endpoint path used by the collector. Must be a base URL (scheme + host + optional base path, no query strings or fragments).

### 3.4 New Source Group Enums (30 Total)

The 13 existing committed groups are joined by 17 new groups. Total: 30 source groups.

| New Group | Description | Example Sources |
|-----------|-----------|----------------|
| intellectual_property | Patent grants, trademark registrations, IP ownership records | USPTO PatentsView, EPO OPS, WIPO |
| entity_resolution | Corporate entity identification, LEI lookup, beneficial ownership | GLEIF, OpenCorporates, Open Ownership |
| geospatial_verification | Building footprints, geocoding, planning data, physical verification | Overpass API, Nominatim, UK Planning Data, Google Open Buildings |
| geophysical_hazard | Earthquake, volcano, tsunami, geological hazard monitoring | USGS, GDACS, EMSC, NOAA Tsunami |
| fire_emissions | Active fire detection, emissions, air quality | NASA FIRMS, EPA AirNow, Copernicus CAMS |
| space_weather | Solar activity, geomagnetic storms, GPS constellation, satellites | NOAA SWPC, CelesTrak, Space-Track.org |
| infrastructure_critical | Undersea cables, pipelines, power grids, telecoms | TeleGeography, GridStatus.io, ENTSO-E |
| sanctions_compliance | Sanctions designations, export controls, compliance lists | OFAC SDN, EU Consolidated, UK OFSI, UN SC, OpenSanctions |
| health_biosecurity | Disease outbreaks, pandemic surveillance, biosecurity alerts | WHO DON, ProMED, CDC NNDSS |
| election_governance | Election results, legislative votes, governance transitions | Wikidata Elections, UK Parliament, US Congress |
| energy_commodities | Energy production, commodity prices, strategic reserves | EIA, OPEC MOMR, IEA |
| climate_weather | Weather forecasting, climate anomalies, severe weather | Open-Meteo, Met Office, NOAA NWS, ECMWF |
| demographic_economic | Census, population, economic indicators, statistics offices | ONS, Eurostat, BLS, ABS, Destatis, World Bank |
| nuclear_wmd | Nuclear facility monitoring, WMD treaty compliance | IAEA PRIS, CTBTO, SIPRI |
| protest_unrest | Civil unrest, protest activity, political instability | ACLED, GDELT, WorldMonitor CII |
| calendar_counter_signal | Public holidays, scheduled events, counter-signal discounting | Nager.Date, Abstract Holidays, TfL |
| judicial_record | Court filings, insolvency notices, legal proceedings | UK Case Law (TNA), CourtListener, London Gazette |

---

## 4. Collector Manifest by Domain

Every source below includes its actual API endpoint, access tier, authentication requirement, and the number of consumption surfaces it serves. Sources marked EXISTING are already in registry v0.6.0. Sources marked NEW are proposed additions.

### 4.1 Theatre Settlement — Registry Gaps

These are genuinely free, settlement-eligible sources missing from the current 77-source registry. Note: SEC XBRL CompanyFacts is also settlement-eligible but its canonical home is Section 4.3 (AUDIT Class) to avoid duplicate source_id entries.

| source_id | API Endpoint | Tier | Auth | Surfaces | Notes |
|-----------|-------------|------|------|----------|-------|
| uk_caselaw_tna | caselaw.nationalarchives.gov.uk/api/ | A | None | 5/7 | NEW. Every High Court+ judgment. LegalDocML. Immutable. judicial_record group. |
| uk_legislation_gov | legislation.gov.uk/developer/formats + SPARQL | A | None | 4/7 | NEW. All UK Acts. RDF/XML/JSON-LD. Versioned amendments. |
| uk_parliament_bills | bills-api.parliament.uk/api/v1/ | A | None | 4/7 | NEW. Bill progress, stages, Royal Assent dates. Immutable milestones. |
| usa_spending_api | api.usaspending.gov/api/v2/ | A | None | 4/7 | NEW. Federal contracts, grants. Permanent award IDs. Procurement Theatres. |
| nih_reporter_api | api.reporter.nih.gov/v2/projects/search | A | None | 3/7 | NEW. Grant dates, funding, PIs. POST body. Research funding claims. |
| imf_sdmx_api | dataservices.imf.org/REST/SDMX_JSON.svc/ | A | None | 5/7 | NEW. GDP, BoP, FX reserves. 190 countries. Macroeconomic claims. |
| eurostat_api | ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/ | A | None | 5/7 | NEW. EU economic/social/demographic stats. Permanent dataset codes. |
| ofac_sdn_api | sanctionssearch.ofac.treas.gov/api/ + bulk XML | A | None | 7/7 | NEW. US Treasury SDN list. Daily updated. Sanctions Theatres. |
| uk_ofsi_list | assets.publishing.service.gov.uk (CSV/XML) | A | None | 6/7 | NEW. UK sanctions consolidated list. Settlement-eligible. |
| eu_sanctions_list | data.europa.eu/euodp/ (XML/CSV) | A | None | 6/7 | NEW. EU restrictive measures consolidated list. |
| patent_view_api | api.patentsview.org/patents/query | A | None | 4/7 | NEW. Every US patent since 1976. IP ownership Theatres. |
| epo_ops_api | ops.epo.org/3.2/rest-services/ | B | OAuth2 | 4/7 | NEW. European Patent Office. EP/PCT/national data. |
| planning_data_uk | planning.data.gov.uk/api/ | A | None | 5/7 | NEW. UK planning applications, decisions, listed buildings. Property Theatres. |
| wikidata_sparql | query.wikidata.org/sparql | A | None | 5/7 | NEW. Election results, heads of state, structured facts. Governance Theatres. |
| sam_gov_api | api.sam.gov/opportunities/v2/search | B | API key | 5/7 | NEW. US federal awards, entities, exclusions. Procurement verification. |

### 4.2 Mission Factory / Timeline Spawning

Theatre creation triggers. False positives are cheap; missed signals are expensive. Widest net.

| source_id | API Endpoint | Tier | Auth | Surfaces | Notes |
|-----------|-------------|------|------|----------|-------|
| usgs_earthquake_api | earthquake.usgs.gov/fdsnws/event/1/query | A | None | 5/7 | EXISTING. Real-time global seismic. GeoJSON. Updates every minute. |
| gdacs_rss | gdacs.org/xml/rss.xml + REST | A | None | 6/7 | EXISTING. UN disaster alerts with severity scoring. |
| nasa_eonet_api | eonet.gsfc.nasa.gov/api/v3/events | A | None | 5/7 | NEW. Earth Observatory Natural Events. Fires, storms, volcanos, floods. |
| nasa_firms_api | firms.modaps.eosdis.nasa.gov/api/ | B | MAP_KEY | 6/7 | EXISTING. Active fire detection. MODIS/VIIRS satellites. |
| noaa_swpc_api | services.swpc.noaa.gov/json/ | A | None | 5/7 | NEW. Space weather: K-index, solar flares, aurora. Infra disruption trigger. |
| acled_api | api.acleddata.com/acled/read/ | B | API key | 5/7 | EXISTING. Armed conflict and protests. Weekly update. Geolocation. |
| gdelt_doc_api | api.gdeltproject.org/api/v2/doc/doc | A | None | 4/7 | EXISTING. 65 languages, 15-min cycle. Broad but noisy. Signal detection only. |
| opensky_network_api | opensky-network.org/api/ | A | None | 5/7 | EXISTING. Live ADS-B. Airspace closures as geopolitical signal. |
| aisstream_io | aisstream.io (WebSocket) | B | API key | 5/7 | NEW. Real-time global AIS vessel positions. Better than polling MarineTraffic. |
| who_disease_outbreak | who.int/emergencies/disease-outbreak-news/ RSS | A | None | 6/7 | NEW. Every formal WHO outbreak notification. Biosecurity trigger. |
| promed_rss | promedmail.org/rss/ | A | None | 5/7 | NEW. Early disease detection. 7-14 days ahead of WHO. Informal but fast. |
| cdc_wonder_api | wonder.cdc.gov/controller/datarequest/ | A | None | 3/7 | NEW. US mortality, disease surveillance. Slow-moving but reliable. |
| emsc_earthquake_api | seismicportal.eu/fdsnws/event/1/query | A | None | 4/7 | NEW. European seismology. Independent of USGS receiver network. |
| reliefweb_api | api.reliefweb.int/v1/reports | A | None | 5/7 | EXISTING. OCHA humanitarian reports, funding, displacement. |

### 4.3 Bounded Inquiries — Per Inquiry Class

Each of the five inquiry classes needs specific source types to populate the signal feed.

**INVESTIGATION Class (Entity-Level)**

| source_id | API Endpoint | Tier | Auth | Surfaces | Notes |
|-----------|-------------|------|------|----------|-------|
| opencorporates_api | api.opencorporates.com/v0.4/companies/search | C | None/Key | 4/7 | NEW. 164M companies, 129 jurisdictions. 50 req/day anon, 500 registered. |
| gleif_api | api.gleif.org/api/v1/lei-records/ | A | None | 5/7 | NEW. Legal Entity Identifiers. All institutional counterparties. Immutable. |
| open_ownership_api | api.openownership.org/ | A | None | 4/7 | NEW. Beneficial ownership. Aggregated from national registers. |

**INSPECTION Class (Regulatory Status)**

| source_id | API Endpoint | Tier | Auth | Surfaces | Notes |
|-----------|-------------|------|------|----------|-------|
| fca_register | register.fca.org.uk (JSON discoverable) | A | None | 4/7 | NEW. UK FCA firm register. Authorisation status, permissions. |
| sec_edgar_efts | efts.sec.gov/LATEST/search-index | A | None | 4/7 | NEW. Full-text search across all SEC filings. Real-time alerts. |
| finra_brokercheck | api.brokercheck.finra.org/search/ | A | None | 3/7 | NEW. US broker registration status, disclosures, exam history. |

**AUDIT Class (Financial Flows)**

| source_id | API Endpoint | Tier | Auth | Surfaces | Notes |
|-----------|-------------|------|------|----------|-------|
| sec_xbrl_companyfacts | data.sec.gov/api/xbrl/companyfacts/{CIK}.json | A | None | 4/7 | NEW. Every XBRL-tagged financial fact per SEC registrant. Canonical home for this source (also referenced in settlement layer). Balance sheets, P&L, cash flow. |
| simfin_api | simfin.com/api/v2/ | C | API key | 3/7 | NEW. Standardised financials for 4,000+ companies. 500 req/day free. |
| bis_statistics | stats.bis.org/api/v1/data/ | A | None | 4/7 | NEW. BIS: cross-border banking, OTC derivatives, property prices, credit. |

**SURVEY Class (Geospatial/Property)**

| source_id | API Endpoint | Tier | Auth | Surfaces | Notes |
|-----------|-------------|------|------|----------|-------|
| overpass_api | overpass-api.de/api/interpreter | A | None | 4/7 | NEW. OpenStreetMap queries. Building footprints, amenities, infrastructure. |
| nominatim_api | nominatim.openstreetmap.org/search | A | None | 4/7 | NEW. Geocoding/reverse geocoding. Address to coordinates for all spatial verification. |
| google_open_buildings | sites.research.google/open-buildings/ (GCS) | A | None | 3/7 | NEW. 1.8B building footprints. Africa, S/SE Asia, Latin America. |
| hm_land_registry_ppd | landregistry.data.gov.uk/app/ppd/ (SPARQL + CSV) | A | None | 4/7 | NEW. Every residential sale in England/Wales since 1995. Complements HMLR. |

**SCRUTINY Class (Judicial/Adversarial)**

| source_id | API Endpoint | Tier | Auth | Surfaces | Notes |
|-----------|-------------|------|------|----------|-------|
| courtlistener_api | courtlistener.com/api/rest/v4/ | A | None | 4/7 | NEW. PACER mirror (RECAP). 200M+ docs. upstream_id must ref PACER to prevent double-count. |
| un_sanctions_sc | scsanctions.un.org/search/ (XML) | A | None | 5/7 | NEW. UN Security Council consolidated list. Independent of US/EU/UK. |
| opensanctions_api | opensanctions.org/ (bulk download) | A | None | 6/7 | NEW. Aggregated sanctions + PEP data. Bulk download is Tier A (free forever, no auth). REST API (api.opensanctions.org) is Tier B (free with registration, richer entity model for PEP queries). Collector should target REST API for entity lookups, bulk for baseline sync. |

### 4.4 DeltaBrief / Novelty Detection

These need stable baselines so novelty can be detected algorithmically. Broad observation surface is paramount.

| source_id | API Endpoint | Tier | Auth | Surfaces | Notes |
|-----------|-------------|------|------|----------|-------|
| world_bank_api | api.worldbank.org/v2/country/{iso}/indicator/{code} | A | None | 5/7 | EXISTING. 1,600+ development indicators. 200+ countries. Annual baseline. |
| oecd_api | stats.oecd.org/SDMX-JSON/data/ | A | None | 4/7 | NEW. 38 OECD countries: trade, labour, health, education, environment. |
| bis_statistics | stats.bis.org/api/v1/data/ | A | None | 4/7 | NEW. Cross-border banking flows, property prices, credit. Financial anomaly. |
| iea_api | api.iea.org/ | B | Registration | 4/7 | NEW. Energy supply/demand, prices, CO2. Energy market baselines. |
| eia_api | api.eia.gov/v2/ | B | API key | 5/7 | NEW. US energy: oil, gas, electricity, coal. Weekly/daily cadence. |
| un_comtrade_api | comtradeapi.un.org/data/v1/ | B | API key | 3/7 | NEW. Bilateral trade flows by HS code. 200+ countries. 100 req/hour. |
| celestrak_gp | celestrak.org/SOCRATES/ + satcat/ | A | None | 4/7 | NEW. Every tracked object in orbit. Novelty = unexpected manoeuvres. |
| who_gho_api | ghoapi.azureedge.net/api/ | A | None | 4/7 | NEW. 2,000+ health indicators. 194 countries. Disease burden baselines. |
| world_inequality_db | wid.world/data/ (bulk CSV) | A | None | 3/7 | NEW. Income/wealth inequality. 100+ countries. Structural baseline. |

### 4.5 Agent Context

Feed the Shark, Spy, Diplomat, and Saboteur archetypes with context for Theatre trading decisions.

| source_id | API Endpoint | Tier | Auth | Surfaces | Notes |
|-----------|-------------|------|------|----------|-------|
| openmeteo_api | api.open-meteo.com/v1/forecast | A | None | 5/7 | NEW. Weather for any coordinate. No key, no limits. Historical to 1940. Essential for physical-world Theatres. |
| met_office_datapoint | api.metoffice.gov.uk/public/data/ | B | API key | 4/7 | NEW. UK Met Office. More granular UK weather than Open-Meteo. |
| nager_date_api | date.nager.at/api/v3/PublicHolidays/{year}/{code} | A | None | 5/7 | NEW. Public holidays by country. Counter-signal for timing anomalies. |
| global_fishing_watch | globalfishingwatch.org API | B | API key | 3/7 | NEW. Vessel activity from AIS. Maritime and environmental Theatres. |
| wto_stats_api | stats-api.wto.org/api/v1/ | A | None | 3/7 | NEW. WTO tariff and trade statistics. Trade dispute Theatres. |
| alpha_vantage | alphavantage.co/query | C | API key | 3/7 | NEW. Stocks, FX, crypto, earnings. 500 req/day, 5 req/min. Display-grade. |
| cryptocompare_api | min-api.cryptocompare.com/data/ | C | None | 3/7 | NEW. Crypto prices with exchange breakdown. 100k calls/month. |
| port_of_rotterdam | portofrotterdam.com/en/api | A | None | 3/7 | NEW. Port congestion, schedules, throughput. European trade context. |
| port_of_singapore | data.gov.sg/dataset/port-vessels-arrival-departure | A | None | 3/7 | NEW. Singapore MPA vessel data. Key chokepoint context. |

### 4.6 Consumer Dashboard — Display-Grade Sources

These populate the PizzINT-style dashboard. Widest aperture. Every interesting real-world signal.

| source_id | API Endpoint | Tier | Auth | Surfaces | Notes |
|-----------|-------------|------|------|----------|-------|
| iss_location_api | api.wheretheiss.at/v1/satellites/25544 | A | None | 1/7 | NEW. ISS real-time position. Dashboard widget. |
| n2yo_api | api.n2yo.com/rest/v1/satellite/ | B | API key | 2/7 | NEW. Any satellite by NORAD ID. Starlink constellation. 1,000 req/hour. |
| celestrak_satcat | celestrak.org/satcat/satcat.csv | A | None | 3/7 | NEW. All tracked space objects catalogue. |
| telegeography_cables | github.com/telegeography/submarinecablemap (GeoJSON) | A | None | 2/7 | NEW. Submarine cable routes. Static but authoritative. Map layer. |
| spacelaunchnow_api | ll.thespacedevs.com/2.2.0/launch/ | B | None | 3/7 | NEW. Scheduled/historical rocket launches. Launch tracker widget. |
| iaea_news_rss | iaea.org/newscenter/news RSS | A | None | 3/7 | NEW. IAEA official news: safeguards, safety events, inspector reports. |
| openaq_api | api.openaq.org/v3/ | A | None | 3/7 | NEW. Air quality from 30,000+ stations globally. Environmental widget. |
| copernicus_cams | cds.climate.copernicus.eu/api/v2/ | B | Registration | 3/7 | NEW. EU atmosphere data. Air quality, greenhouse gases. |
| volcano_discovery_rss | volcanodiscovery.com/worldwide/news.rss | A | None | 2/7 | NEW. Real-time volcanic activity reports. |

### 4.7 Sponsored Theatre Context — Enrichment Sources

Context that makes certificates comprehensive and commercially defensible for paying sponsors.

| source_id | API Endpoint | Tier | Auth | Surfaces | Notes |
|-----------|-------------|------|------|----------|-------|
| planning_data_uk | planning.data.gov.uk/api/ | A | None | 5/7 | NEW. UK planning applications, decisions, listed buildings, conservation areas. Property Theatres. |
| ons_api | api.beta.ons.gov.uk/v1/ | A | None | 4/7 | NEW. UK ONS: house prices, construction output, rental index, population. |
| hm_land_registry_ppd | landregistry.data.gov.uk/app/ppd/ (SPARQL + CSV) | A | None | 4/7 | NEW. Every residential sale in England/Wales since 1995. Complements HMLR. |
| govuk_planning_insp | acp.planninginspectorate.gov.uk/projects/ | A | None | 3/7 | NEW. National Infrastructure Planning decisions. Major UK infra enrichment. |
| de_destatis_api | www-genesis.destatis.de/genesisWS/rest/2020/ | B | Registration | 3/7 | NEW. German Federal Statistics. Construction permits, real estate, labour. |
| abs_api | api.data.abs.gov.au/ | A | None | 3/7 | NEW. Australian Bureau of Statistics. Property prices, construction, employment. |
| world_bank_climate | climateknowledgeportal.worldbank.org/api/ | A | None | 3/7 | NEW. Projected climate risk by country/region. AE/AU property enrichment. |

---

## 5. SitDeck 14-Category Parity

SitDeck's 14 deck categories represent the consumer's mental model of world intelligence. At v1.0.0 with 160+ sources, every category is populated with 4+ feeds.

| SitDeck Category | Sources | Key Feeds |
|-----------------|---------|-----------|
| Command Centre | 15+ | USGS, GDACS, NOAA NWS, NASA FIRMS, ACLED, OpenSky, MarineTraffic, Polymarket, CoinGecko, CISA KEV, ReliefWeb, WorldMonitor |
| War and Conflict | 10+ | ACLED, GDELT, SIPRI, USNI Fleet Tracker, OpenSky (military), ADS-B Exchange, ReliefWeb, WorldMonitor CII, GLEIF (entity ID) |
| Nuclear and WMD | 6+ | IAEA PRIS, IAEA News, CTBTO, NTI, NOAA SWPC (radiation proxy), SIPRI Arms Database |
| Aviation and Space | 8+ | OpenSky, ADS-B Exchange, CelesTrak, Space-Track, Launch Library 2, SpaceLaunchNow, N2YO, ISS Location |
| Maritime and Trade | 8+ | MarineTraffic, Spire, AISStream, Global Fishing Watch, USAspending, UN Comtrade, Port of Rotterdam, Port of Singapore |
| Markets and Finance | 12+ | Polygon.io, ECB, FRED, BoE, BLS, CoinGecko, Polymarket, Kalshi, World Bank, IMF SDMX, Alpha Vantage, CryptoCompare |
| Environment and Climate | 8+ | USGS, NOAA NWS, Met Office, Open-Meteo, NASA FIRMS, EPA AirNow, ECMWF/Copernicus, OpenAQ, GDACS |
| Cyber and Technology | 5+ | CISA KEV, AlienVault OTX, OpenSanctions (PEP), GDELT tech cluster, WorldMonitor tech variant |
| Health and Biosecurity | 7+ | WHO DON, ProMED, CDC NNDSS/WONDER, NIH RePORTER, NPI Registry, WHO GHO, GISAID |
| Elections and Politics | 6+ | Wikidata Elections, UK Parliament, US Congress, ACLED protests, GDELT political, OpenSanctions PEP |
| Legal and Regulatory | 10+ | UK Case Law, UK Legislation, PACER, CourtListener, London Gazette, Companies House, SEC EDGAR, INPI RNE, FCA Register, FINRA |
| Demographics and Society | 7+ | World Bank, BLS, ONS, Eurostat, ABS, Destatis, USAspending, World Inequality Database |
| Energy and Resources | 7+ | EIA, IEA, ENTSO-E, OPEC MOMR, GridStatus.io, Copernicus CDS, Met Office |
| OSINT and Social | 5+ | GDELT, WorldMonitor, X API (enterprise), Telegram OSINT (manual), ReliefWeb, Internet Archive CDX |

---

## 6. WorldMonitor Integration Strategy

WorldMonitor operates at Layer 0 (signal fusion) below the OSINT pipeline at Layer 1 (structured collection). Its local LLM (Llama 3.1 on Ollama) performs focal point detection — identifying multi-signal correlations that no single collector would flag independently.

**WorldMonitor feeds into:** Mission Factory anomaly triggers (timeline spawning), DeltaBrief novelty candidates (multi-domain change detection), Consumer Dashboard composite alerts (country instability index, strategic risk overview).

**WorldMonitor does NOT replace:** Direct API collectors for settlement-eligible sources. Correlation outputs are scoring-grade, not settlement-grade. Settlement always requires the direct collector path with cryptographic receipts.

**Registry representation:** Single meta-source with consumption_surfaces excluding theatre_settlement. worldmonitor_domain links to self-hosted fork. Upstream sources retain independent registry entries with direct collector paths.

**Implementation:** Wired in Cycle-035 after first live OSINT-settled certificate proves the direct collector path. Focal point detection API consumed as a Mission Factory signal source.

---

## 7. Build Priority

Sources ranked by surface coverage count. Tier A sources that serve 5+ surfaces are the immediate build targets. These can have working collectors in under an hour each.

### 7.1 Priority 1 — Immediate (5+ Surfaces, Tier A)

| source_id | Surfaces | Tier | Rationale |
|-----------|----------|------|-----------|
| ofac_sdn_api | 7/7 | A | Serves every surface. Sanctions settlement + Mission Factory trigger + agent context + dashboard + DeltaBrief + Bounded Inquiry + Sponsored Theatre. |
| eu_sanctions_list | 6/7 | A | EU sanctions settlement. Independent of OFAC for corroboration. |
| uk_ofsi_list | 6/7 | A | UK sanctions settlement. Third independent sanctions source. |
| opensanctions_api | 6/7 | A | Aggregated PEP + sanctions. Community-maintained. Bulk download. |
| who_disease_outbreak | 6/7 | A | Every WHO outbreak notification. Mission Factory + DeltaBrief + Dashboard. |
| usgs_earthquake_api | 5/7 | A | EXISTING. Already built. Verify consumption_surfaces field. |
| gdacs_rss | 6/7 | A | EXISTING. Already built. Add to consumer dashboard surface. |
| wikidata_sparql | 5/7 | A | Elections, governance, structured facts. Governance Theatres. |
| openmeteo_api | 5/7 | A | Weather for any coordinate. No limits. Physical-world Theatres. |
| planning_data_uk | 5/7 | A | UK planning data. Core property vertical enrichment. |
| gleif_api | 5/7 | A | Entity resolution infrastructure. Every surface needs entity ID. |
| imf_sdmx_api | 5/7 | A | Macroeconomic settlement. 190 countries. |
| nager_date_api | 5/7 | A | Calendar counter-signal. Settlement timing discounting. |
| reliefweb_api | 5/7 | A | EXISTING. Humanitarian reports. Add consumption_surfaces. |
| eurostat_api | 5/7 | A | EU jurisdiction statistics. Settlement-eligible. |
| world_bank_api | 5/7 | A | EXISTING. Development indicators baseline. Add consumption_surfaces. |
| eia_api | 5/7 | B | US energy data. Weekly cadence. Energy Theatres. |
| sam_gov_api | 5/7 | B | US procurement verification. Settlement-eligible. |

### 7.2 Priority 2 — Next Quarter (4 Surfaces)

Includes: ACLED (existing), OpenSky (existing), NASA FIRMS (existing), AISStream, UK Case Law, ONS, Met Office DataPoint, CelesTrak, BIS Statistics, OECD, Overpass API, Nominatim, HM Land Registry PPD, IEA, NOAA SWPC, EMSC, CourtListener, Open Ownership, FCA Register, NOAA NWS, UK Parliament Bills, OpenCorporates, SIPRI, SEC XBRL CompanyFacts, PatentsView.

### 7.3 Priority 3 — Enumerate Now, Build When Needed (1-3 Surfaces)

Includes: ISS Location, N2YO, TeleGeography Cables, Volcano Discovery RSS, Space-Track.org, GPS.gov, CTBTO, NTI Nuclear, TfL Unified, GISAID, WTO Stats, Janes (paid), OPEC MOMR, FlightRadar24 (paid), ECMWF, Google Open Buildings, Port of Rotterdam, Port of Singapore, Abstract Holidays, SimFin, Alpha Vantage, CryptoCompare, Destatis, ABS, CDC WONDER, Manifold Markets (api.manifold.markets, Tier A, no auth — calibrated probability distributions distinct from Polymarket CLOB structure), Metaculus (metaculus.com/api2, Tier A, no auth — institutional forecasters, strengthens DeltaBrief baseline for geopolitical Theatres).

---

## 8. Registry Expansion Summary

| Metric | v0.6.0 (Shipped) | v1.0.0 (Target) |
|--------|------------------|-----------------|
| Total sources | 77 | 160+ |
| Source groups | 13 committed + 2 proposed | 30 |
| Consumption surfaces tracked | 0 (settlement-only framing) | 7 |
| Jurisdictions | 7 | 9+ (adding DE, SG, HK expansion) |
| Settlement-eligible sources | 13 | 29 |
| Tier A (no auth, may have rate limits) | ~40 | ~95 |
| Tier B (free key) | ~25 | ~45 |
| Tier C (free with limits) | ~5 | ~12 |
| Paid/enterprise | ~7 | ~10 |
| SitDeck category coverage | 8/14 | 14/14 (100%) |
| Sources serving 5+ surfaces | 0 tracked | 18 |
| Sources serving 4 surfaces | 0 tracked | 25+ |
| New source groups added | n/a | 17 (incl. intellectual_property, entity_resolution, geospatial_verification) |

---

## 9. Version History

| Version | Date | Changes |
|---------|------|---------|
| 0.1.0 | Jan 2026 | Initial registry. 13 source groups. Settlement-only framing. |
| 0.3.2 | Feb 2026 | 51 sources. 5 structural primitives. HTTP transcript spec. Validator tool. |
| 0.4.0 | Feb 2026 | 57 sources. 7 jurisdictions. Independence architecture hardened. |
| 0.5.0 | Feb 2026 | 68 sources. 11 new sources: geophysical, conflict, cyber, humanitarian, maritime. |
| 0.6.0 | 1 Mar 2026 | 77 sources. Rate limit documentation. Automation feasibility. Cycle-003 shipped and archived. |
| 1.0.0 | 1 Mar 2026 | 160+ sources (from 77). 7 consumption surfaces. 30 source groups (13 existing + 17 new incl. intellectual_property, entity_resolution, geospatial_verification). SitDeck 14-category parity. WorldMonitor as Layer 0 signal fusion. Merged collector manifest with per-source API endpoints and Tier A/B/C access classification. Build priority by surface coverage count, not settlement eligibility alone. |
