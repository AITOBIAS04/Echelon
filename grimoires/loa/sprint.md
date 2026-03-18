# Sprint Plan — Cycle-026: OSINT Registry Expansion — Batch 1

**Cycle:** cycle-026
**Date:** 17 March 2026
**Builder:** Loa
**Sprints:** 4 (0–3)

---

## Sprint 0 — Registry + Enum + Scaffold

**Goal:** Expand the registry, add source_group values, scaffold collector files. No HTTP calls yet.

### Tasks

1. ~~**Add 4 source_group values** to `_VALID_SOURCE_GROUPS` in `backend/osint/models/registry.py`~~ ✅
   - Values: `blockchain_data`, `geospatial`, `environmental`, `event_data`
   - Write 2 tests: all 37 values present, new values in frozenset

2. ~~**Add 10 entries to `sources.json`** — version bump to `0.5.0`~~ ✅
   - Full field set per entry (matching existing entry schema)
   - Write 2 tests: RegistryLoader loads 16 entries, `.validate()` returns no errors

3. ~~**Scaffold 10 collector files** in `backend/osint/collectors/`~~ ✅
   - Each file: class skeleton extending BaseCollector
   - `source_id()` returns correct string
   - `_fetch()` raises NotImplementedError (placeholder)
   - `health_check()` returns UNAVAILABLE (placeholder)

4. ~~**Create `build_collector_map()`** function (or extend existing registration point)~~ ✅
   - Wire all 10 new collectors into CollectionRunner
   - Write 1 test: all 10 source_ids registered in collector map

**Exit:** 5 tests pass. Registry loads 16 sources. 10 collector files exist. `npm run build` passes.

---

## Sprint 1 — Financial + Corporate Collectors (4 collectors)

**Goal:** Implement the 4 collectors with API key auth: FRED, Alpha Vantage, OpenCorporates, Etherscan.

### Tasks

1. ~~**Implement FREDCollector** — `_fetch()` and `health_check()`~~ ✅
   - GET `/fred/series/observations` with series_id, api_key query param
   - Parse observations array, extract latest value
   - Write 3 tests: success (mocked response), missing API key, invalid series_id

2. ~~**Implement AlphaVantageCollector**~~ ✅
   - GET with `function=TIME_SERIES_DAILY`, `symbol`, `apikey` query params
   - Parse time series, extract latest close price
   - Write 3 tests: success, rate limit (429 response), invalid symbol

3. ~~**Implement OpenCorporatesCollector**~~ ✅
   - GET `/companies/search` with `q`, `jurisdiction_code`, `api_token` query params
   - Parse companies array, extract company metadata
   - Write 3 tests: success, auth failure (403), empty result set

4. ~~**Implement EtherscanCollector**~~ ✅
   - GET with `module=account`, `action=txlist` or `action=balance`, `address`, `apikey`
   - Parse result array, extract transaction data or balance
   - Write 3 tests: success, invalid address, rate limit

**Exit:** 12 tests pass. All 4 collectors produce valid CollectionResult with mocked HTTP. `npm run build` passes.

---

## Sprint 2 — Science + Environment + Aviation Collectors (4 collectors)

**Goal:** Implement the 4 no-auth collectors: CoinGecko, OpenSky, USGS Earthquake, UK Carbon Intensity.

### Tasks

1. ~~**Implement CoinGeckoCollector**~~ ✅
   - GET `/simple/price` with `ids`, `vs_currencies` query params. No auth.
   - Parse price map
   - Write 2 tests: success, invalid coin_id

2. ~~**Implement OpenSkyCollector**~~ ✅
   - GET `/states/all` with `lamin`, `lamax`, `lomin`, `lomax` bounding box. No auth.
   - Parse state vectors array
   - Write 2 tests: success, empty state vector (no aircraft in box)

3. ~~**Implement USGSEarthquakeCollector**~~ ✅
   - GET `/query` with `format=geojson`, `starttime`, `endtime`, `minmagnitude`. No auth.
   - Parse GeoJSON features, extract epicentre as GeoPoint
   - Write 2 tests: success, no events in window

4. ~~**Implement CarbonIntensityCollector**~~ ✅
   - GET `/intensity/{from}/{to}` date range. No auth.
   - Parse intensity data array
   - Write 2 tests: success, degraded API (partial data)

**Exit:** 8 tests pass. All 4 no-auth collectors produce valid CollectionResult. `npm run build` passes.

---

## Sprint 3 — Remaining Collectors + Integration

**Goal:** Implement OpenAQ + Calendarific. Integration sweep. Regression.

### Tasks

1. ~~**Implement OpenAQCollector**~~ ✅
   - GET `/v2/measurements` with `country`, `parameter`, `date_from`, `date_to`. Auth via `X-API-Key` header.
   - Parse measurements array
   - Write 2 tests: success, no measurements

2. ~~**Implement CalendarificCollector**~~ ✅
   - GET `/holidays` with `country`, `year`, `api_key` query param.
   - Parse holidays array. resolution_role = "counter_signal"
   - Write 2 tests: success (holidays returned), non-holiday date

3. ~~**Integration sweep**~~ ✅
   - Verify CollectionRunner executes all 14 collectors (3 WM + 1 CH + 10 Batch 1) concurrently
   - ~~Verify persist_signal writes from Batch 1 collectors to osint_signals table~~ (deferred — requires DB)
   - ~~Verify GET /api/v1/osint/signals returns signals from new source_groups~~ (deferred — requires API server)
   - Write 2 integration tests (collector_map count + CollectionRunner execution)

4. ~~**Path 2 regression test**~~ ✅
   - Confirm no imports from Path 2 files in any Cycle 026 file
   - Write 1 test

5. ~~**Final `npm run build` + full test run**~~ ✅

**Exit:** All ~31 tests pass. All 10 collectors produce valid results. Registry validates. `npm run build` passes.

---

## Sprint Summary

| Sprint | Focus | Tests |
|---|---|---|
| 0 | Registry + enum + scaffold + wiring | 5 |
| 1 | Financial + corporate collectors (FRED, AV, OC, Etherscan) | 12 |
| 2 | Science + environment + aviation (CoinGecko, OpenSky, USGS, Carbon) | 8 |
| 3 | Remaining (OpenAQ, Calendarific) + integration + regression | 6 |
| **Total** | | **~31** |
