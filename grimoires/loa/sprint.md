# Sprint Plan — Cycle-027: OSINT Registry Expansion — Batch 2

**Cycle:** cycle-027
**Date:** 17 March 2026
**Builder:** Loa
**Sprints:** 3 (0–2)

---

## Sprint 0 — Registry + Scaffold + Procurement Base

**Goal:** Expand the registry, scaffold all 11 collector files, optionally create shared procurement base class.

### Tasks

1. **Add 11 entries to `sources.json`** — version bump to `0.6.0`
   - Full field set per entry matching existing schema
   - Write 2 tests: RegistryLoader loads 27 entries, `.validate()` returns no errors

2. **Scaffold 11 collector files** in `backend/osint/collectors/`
   - Each file: class skeleton extending BaseCollector
   - `source_id()` returns correct string
   - `_fetch()` raises NotImplementedError (placeholder)
   - `health_check()` returns UNAVAILABLE (placeholder)

3. **Wire all 11 into `build_collector_map()`**
   - Write 1 test: all 24 source_ids registered in collector map

4. **(Optional) Create `BaseProcurementCollector`** — shared date-windowing, normalisation, receipt construction for the 5 procurement collectors. If time is tight, skip and implement flat.

**Exit:** 3 tests pass. Registry loads 27 sources. 11 collector files exist. `npm run build` passes.

---

## Sprint 1 — Government Open Data Portals (6 collectors)

**Goal:** Implement the 6 government open data collectors: FR, DE, Bundestag DIP, SG, IN, TW.

### Tasks

1. **Implement FrenchOpenGovCollector**
   - GET `/datasets/` with q, organization params. API key header (optional).
   - Parse CKAN response, extract dataset count and metadata
   - Write 2 tests: success (mocked), auth failure

2. **Implement GermanOpenGovCollector**
   - GET CKAN `/action/package_search` with q. No auth.
   - Write 2 tests: success, empty dataset

3. **Implement BundestagDIPCollector**
   - GET `/dokumente` or `/vorgaenge` with f.typ, date filters. API key header.
   - Parse legislative documents (Drucksache, Plenarprotokoll)
   - Write 2 tests: success, invalid Drucksache ID

4. **Implement SingaporeOpenGovCollector**
   - GET CKAN `/datastore_search` with q. No auth.
   - Write 2 tests: success, no datasets

5. **Implement IndianOpenGovCollector**
   - GET with resource_id, filters, api-key query param.
   - Write 2 tests: success, auth failure

6. **Implement TaiwanOpenGovCollector**
   - GET dataset search endpoint. No auth.
   - Write 2 tests: success, empty response

**Exit:** 12 tests pass. All 6 government collectors produce valid CollectionResult with mocked HTTP. `npm run build` passes.

---

## Sprint 2 — European Procurement Collectors + Integration (5 collectors)

**Goal:** Implement the 5 procurement collectors (HU, PL, RO, ES, UA). Integration sweep. Regression.

### Tasks

1. **Implement HungarianTendersCollector**
   - GET with dateFrom, dateTo. No auth. JSON response.
   - Write 2 tests: success, no tenders in window

2. **Implement PolishTendersCollector**
   - GET with dateFrom, dateTo. No auth. JSON response.
   - Write 2 tests: success, no tenders in window

3. **Implement RomanianTendersCollector**
   - GET with dateFrom, dateTo. No auth. JSON response.
   - Write 2 tests: success, malformed response handling

4. **Implement SpanishTendersCollector**
   - GET Atom syndication. No auth. **XML response** — parse with `xml.etree.ElementTree`.
   - Write 2 tests: success, XML parse error handling

5. **Implement UkrainianTendersCollector**
   - GET Prozorro API v2.5 `/tenders` with offset pagination. No auth. JSON response.
   - Write 2 tests: success (Prozorro JSON), no tenders in window

6. **Integration sweep**
   - Verify CollectionRunner executes all 24 collectors concurrently
   - Verify persist_signal writes from Batch 2 collectors to osint_signals table
   - Verify GET /api/v1/osint/signals returns signals filterable by jurisdiction
   - Write 1 integration test

7. **Path 2 regression test**
   - Verify `GET /api/v1/world-monitor/live` still returns synthetic signals
   - Confirm no imports from Path 2 files in any Cycle 027 file

8. **Final `npm run build` + full test run**

**Exit:** All ~26 tests pass. All 11 collectors produce valid results. Registry validates. `npm run build` passes.

---

## Sprint Summary

| Sprint | Focus | Tests |
|---|---|---|
| 0 | Registry + scaffold + wiring + optional procurement base | 3 |
| 1 | Government open data portals (FR, DE, Bundestag, SG, IN, TW) | 12 |
| 2 | European procurement (HU, PL, RO, ES, UA) + integration + regression | 11 |
| **Total** | | **~26** |
