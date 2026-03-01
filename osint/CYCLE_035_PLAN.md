# Cycle-035: OSINT Pipeline — Live Collection & Evidence Bundles

**Status:** Implementation  
**Date:** 2026-03-01  
**Depends on:** Cycle-034 deliverables (registry v0.4.0, fixtures, validators, WM API contract)  
**Goal:** Transition OSINT_COMPOSED_ORACLE_V1 from fixtures-only to live pipeline with deterministic receipts

---

## Scope

Build the three-stage Composed Oracle pipeline:

1. **Collection** — Fetch from free public APIs, produce HTTP Transcript Receipts
2. **Corroboration** — Cross-reference sources, deduplicate by upstream lineage, enforce minimums
3. **Scoring** — Produce confidence-weighted evidence bundle with per-criterion scores

### Out of Scope (Cycle-036+)
- Theatre Command UI / globe rendering
- Multi-agent simulation / Hounfour integration
- Paid source procurement (Polygon.io, RavenPack, Dataminr)
- Registry v0.5 expansion

---

## File Structure

```
osint_pipeline/
├── CYCLE_035_PLAN.md          # This file
├── models/
│   ├── __init__.py
│   ├── evidence.py            # EvidenceBundle, HTTPTranscriptReceipt, CollectionResult
│   ├── registry.py            # RegistrySource, RegistryLoader (reads v0.4.0 JSON)
│   └── oracle_output.py       # OracleOutput, CriterionScore, CorroborationResult
├── collectors/
│   ├── __init__.py
│   ├── base.py                # BaseCollector ABC — fetch + receipt contract
│   ├── companies_house.py     # GB: Companies House API (free, API key)
│   ├── bank_of_england.py     # GB: BoE Statistical Interactive Database
│   ├── ecb_sdmx.py            # EU: ECB Statistical Data Warehouse (SDMX)
│   ├── sec_edgar.py           # US: SEC EDGAR EFTS (free, user-agent header)
│   ├── fred.py                # US: FRED API (free, API key)
│   ├── inpi_rne.py            # EU/FR: INPI RNE (free government JSON API)
│   ├── gazette.py             # GB: London Gazette (free)
│   └── worldmonitor.py        # Self-hosted WM fork (3 domain endpoints)
├── engine/
│   ├── __init__.py
│   ├── collection_runner.py   # Stage 1: orchestrates collectors per theatre config
│   ├── corroboration.py       # Stage 2: dedup + minimum enforcement
│   ├── counter_signal.py      # Stage 2b: counter-signal class evaluation
│   ├── scorer.py              # Stage 3: confidence-weighted bundle assembly
│   └── canonical.py           # RFC 8785 canonical JSON + SHA-256 utilities
├── cli.py                     # CLI entry point: run oracle, validate, inspect
├── config.py                  # API keys, timeouts, registry path
└── tests/
    ├── test_canonical.py      # Deterministic hashing tests
    ├── test_receipt.py        # HTTP transcript receipt generation
    ├── test_corroboration.py  # Dedup + minimum enforcement
    └── test_fixtures.py       # Run pipeline against existing 10 fixtures
```

---

## Implementation Order

### Phase 1: Core Primitives (build first, test immediately)

1. **`models/evidence.py`** — Pydantic v2 models for EvidenceBundle, HTTPTranscriptReceipt, CollectionResult
2. **`engine/canonical.py`** — RFC 8785 canonical JSON + SHA-256 (already specced in Composed Oracle Spec v2 §5)
3. **`models/registry.py`** — Load and query the v0.4.0 registry JSON
4. **`collectors/base.py`** — BaseCollector ABC defining the fetch→receipt contract

### Phase 2: First Live Collector (prove the pattern works)

5. **`collectors/companies_house.py`** — GB Companies House API
   - Free, API key auth, well-documented REST, immutable revision policy
   - Settlement-eligible, `public_api` access surface
   - Best first target: simple JSON responses, stable endpoint, official government source
6. **`tests/test_receipt.py`** — Verify receipt determinism (same query → same hash)

### Phase 3: Collection Runner + Remaining Collectors

7. **`engine/collection_runner.py`** — Orchestrate multiple collectors per theatre oracle config
8. Remaining collectors in priority order:
   - `sec_edgar.py` (US, free, user-agent header only)
   - `fred.py` (US, free API key)
   - `ecb_sdmx.py` (EU, free, no auth)
   - `bank_of_england.py` (GB, free, no auth)
   - `inpi_rne.py` (EU/FR, free government API)
   - `gazette.py` (GB, free)
   - `worldmonitor.py` (self-hosted, uses WM API contract from Cycle-034)

### Phase 4: Corroboration & Counter-Signals

9. **`engine/corroboration.py`** — Independence dedup by `upstream_id`, enforce `corroboration_minimum_met`
10. **`engine/counter_signal.py`** — Evaluate 11 counter-signal classes, enforce `counter_signal_checked`
11. **`engine/scorer.py`** — Assemble confidence-weighted bundle, compute per-criterion scores

### Phase 5: CLI & Integration

12. **`cli.py`** — `echelon-oracle run --theatre <config>`, `echelon-oracle inspect --bundle <id>`
13. **`tests/test_fixtures.py`** — Run full pipeline against existing 10 fixtures (synthetic mode)

---

## Free Settlement-Eligible Sources (Day-One Targets)

| source_id | Jurisdiction | Auth | Notes |
|-----------|-------------|------|-------|
| companies_house_api | GB | API key (free registration) | Best first target |
| london_gazette | GB | None | Insolvency notices, company events |
| hmlr_price_paid | GB | None | Property transaction data |
| boe_statistics | GB | None | Interest rates, monetary policy |
| sec_edgar_efts | US | User-Agent header | Company filings, 8-K events |
| fred_api | US | API key (free) | Economic indicators |
| ny_fed_api | US | None | Treasury rates, SOMA |
| ecb_sdw | EU | None | Euro area statistics |
| fr_inpi_rne | EU/FR | None | French company register (best EU source) |

---

## Key Contracts (from Composed Oracle Spec v2)

### HTTP Transcript Canonical Form
```
method + "\n" + canonical_url + "\n" + canonical_headers + "\n" + response_status + "\n" + response_body_hash + "\n" + timestamp_ms
```
- Headers: sorted by lowercase key, values trimmed, joined with `;`
- Response body hash: SHA-256 of raw bytes
- Timestamp: UTC milliseconds (integer)
- Receipt hash: SHA-256 of the canonical form string

### Evidence Bundle Minimum Fields
```python
class EvidenceBundle:
    bundle_id: str          # UUID v4
    source_id: str          # Must match registry
    raw_payload: bytes      # Exact response body
    content_hash: str       # SHA-256 of raw_payload
    receipt: HTTPTranscriptReceipt
    structured_extract: dict
    confidence_score: float # [0.0, 1.0]
    retrieved_at: datetime  # UTC, ms precision
    theatre_id: str | None  # Which theatre(s) this serves
```

### Corroboration Rule
```
PASS when:
  count(distinct source_groups
    WHERE role=secondary_corroboration
    AND confirms_primary=true
    AND |delta_t| <= corroboration_window_seconds
  ) >= corroboration_minimum

AFTER dedup by independence_upstream_id
```

---

## Validation Checkpoint

Before shipping Cycle-035:
- [ ] All existing fixtures still validate (no regression)
- [ ] At least 3 free sources producing real evidence bundles with valid receipts
- [ ] Receipt determinism proven (same query, same hash)
- [ ] Corroboration runner correctly deduplicates by upstream_id
- [ ] Counter-signal checker evaluates at least 3 of 11 classes
- [ ] CLI can run a full oracle evaluation and output a scored bundle
- [ ] Bundle hash (SHA-256 of canonical JSON) matches certificate schema
