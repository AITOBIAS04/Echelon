# SDD — Cycle-027: OSINT Registry Expansion — Batch 2

**Cycle:** cycle-027
**Date:** 17 March 2026
**Builder:** Loa

---

## 1. Architecture Summary

### 1.1 Extending Path 1 — Same Pattern, New Jurisdictions

Cycle 027 adds 11 new collectors to **Path 1** (registry-based OSINT). The pipeline is identical to Cycle 026:

```
sources.json → RegistryLoader → CollectionRunner → BaseCollector subclass → CollectionResult → persist_signal → osint_signals table
```

Path 2 (synthetic SignalDetector) is **untouched**.

### 1.2 Change Categories

1. **Registry expansion** — `sources.json` v0.5.0 → v0.6.0, +11 entries
2. **11 new collector files** — each a `BaseCollector` subclass in `backend/osint/collectors/`
3. **Startup wiring** — add 11 collectors to `build_collector_map()`

No new source_group values. No new tables. No schema migrations. No new routes.

### 1.3 Collector Contract (Recap)

Identical to Cycle 026 SDD Section 1.3. Every collector must:
- Extend `BaseCollector`
- Implement `source_id() -> str` — returns the registry source_id string
- Implement `async _fetch(request: dict, theatre_id: str) -> CollectionResult`
- Implement `async health_check() -> HealthStatus`
- Implement `async _do_http_get(url: str) -> bytes` — **per-collector private method** (not on BaseCollector). Follow the async-over-sync pattern from `CompaniesHouseCollector._do_http_get()`: synchronous `urllib.request` in `loop.run_in_executor(None, ...)` wrapped by `asyncio.wait_for()`.
- API key fail-fast: auth-required collectors check for missing/empty API key at the top of `_fetch()` BEFORE any HTTP call.

---

## 2. File-Level Changes

### 2.1 Registry Expansion

**File: `backend/osint/sources.json`**

Add 11 new source entries after the existing 16. Version bump:

```json
{
  "version": "0.6.0",
  "title": "Echelon OSINT Source Registry — Batch 2 Jurisdiction Expansion",
  "description": "27 sources: 3 WorldMonitor + Companies House + Polymarket + Private Leak + 10 Batch 1 + 11 Batch 2 (Cycle-027)"
}
```

Each new entry includes the full field set matching existing entries.

### 2.2 Collector Implementations — Government Open Data Portals

All government open data portals follow a CKAN-like pattern (dataset search, dataset metadata, resource download). Key differences:

**Reference: `backend/osint/collectors/fr_open_gov.py`**

```python
"""French Open Data (data.gouv.fr) collector.

Fetches datasets from the French government open data portal.
Source: https://www.data.gouv.fr/api/1
Auth: API key via ECHELON_FR_OPEN_GOV_API_KEY env var (optional for read)
Rate limit: Generous (CKAN standard)
"""
from __future__ import annotations

import asyncio
import json
import os
import time
import urllib.request
from datetime import datetime

from backend.osint.canonical import compute_content_hash, compute_receipt_hash
from backend.osint.collectors.base import BaseCollector
from backend.osint.models.evidence import (
    CollectionResult, EvidenceBundle, GeoPoint, HTTPTranscriptReceipt,
    HealthStatus, MeasureType, NormalisedEvent, NormalisedMeasure,
)


class FrenchOpenGovCollector(BaseCollector):
    """Collector for French government open data portal."""

    _SOURCE_ID = "fr_open_gov"
    _SOURCE_GROUP = "official_gov"
    _BASE_URL = "https://www.data.gouv.fr/api/1"

    def __init__(self, api_key: str | None = None, timeout_s: float = 30.0) -> None:
        self._api_key = api_key or os.environ.get("ECHELON_FR_OPEN_GOV_API_KEY", "")
        self._timeout_s = timeout_s

    def source_id(self) -> str:
        return self._SOURCE_ID

    async def _fetch(self, request: dict, theatre_id: str) -> CollectionResult:
        """Fetch French open data datasets.

        Expected request keys:
        - query: str (search term)
        - organization: str (optional, org slug)
        """
        query = request.get("query", request.get("source_params", {}).get("query", ""))
        org = request.get("organization", "")

        url = f"{self._BASE_URL}/datasets/?q={query}"
        if org:
            url += f"&organization={org}"
        receipt_url = url  # No API key in URL for this source

        start_ms = time.monotonic() * 1000
        try:
            raw_payload = await self._do_http_get(url)
        except Exception as exc:
            duration_ms = time.monotonic() * 1000 - start_ms
            return CollectionResult(
                source_id=self._SOURCE_ID, bundle=None, raw_payload=b"",
                fetch_duration_ms=duration_ms, success=False,
                error=str(exc), retrieved_at=datetime.utcnow(),
            )
        duration_ms = time.monotonic() * 1000 - start_ms

        now = datetime.utcnow()
        content_hash = compute_content_hash(raw_payload)
        query_str = json.dumps(request, sort_keys=True, separators=(",", ":"))
        receipt_hash = compute_receipt_hash(
            method="GET", url=receipt_url, query=query_str,
            headers="accept:application/json", body_hash=content_hash,
        )

        data = json.loads(raw_payload)
        total = data.get("total", 0)

        receipt = HTTPTranscriptReceipt(
            timestamp=now,
            request_parameters={"method": "GET", "url": receipt_url, "query": query_str, "headers": "accept:application/json"},
            source_id=self._SOURCE_ID, source_version="v0.1.0",
            http_status=200, content_hash=content_hash, receipt_hash=receipt_hash,
        )

        bundle = EvidenceBundle(
            bundle_id=f"eb_{self._SOURCE_ID}_{int(now.timestamp())}",
            source_id=self._SOURCE_ID, source_group=self._SOURCE_GROUP,
            resolution_role="secondary_corroboration",
            evidence_timestamp=now, raw_payload_hash=content_hash,
            receipt=receipt,
            normalised_event=NormalisedEvent(
                event_id=f"evt_{self._SOURCE_ID}_{int(now.timestamp())}",
                geo=GeoPoint(lat=46.603, lon=2.346, radius_m=500000),  # France centroid
                measure=NormalisedMeasure(
                    type=MeasureType.SECTOR_RISK_SCORE,
                    value=float(total), unit="dataset_count",
                    metadata={"query": query, "total_results": total},
                ),
                confidence=0.70,  # secondary_corroboration
                timestamp=now,
            ),
        )

        return CollectionResult(
            source_id=self._SOURCE_ID, bundle=bundle,
            raw_payload=raw_payload, fetch_duration_ms=duration_ms,
            success=True, error=None, retrieved_at=now,
        )

    async def _do_http_get(self, url: str) -> bytes:
        """Execute HTTP GET in thread pool with timeout."""
        loop = asyncio.get_event_loop()
        api_key = self._api_key
        def _sync_get() -> bytes:
            req = urllib.request.Request(url, method="GET")
            if api_key:
                req.add_header("X-Fields", "*")
                req.add_header("X-API-Key", api_key)
            with urllib.request.urlopen(req, timeout=30) as resp:
                return resp.read()
        return await asyncio.wait_for(
            loop.run_in_executor(None, _sync_get),
            timeout=self._timeout_s,
        )

    async def health_check(self) -> HealthStatus:
        """Check French Open Data API availability."""
        try:
            await self._do_http_get(f"{self._BASE_URL}/datasets/?page_size=1")
            return HealthStatus.HEALTHY
        except Exception:
            return HealthStatus.UNAVAILABLE
```

### 2.3 Per-Collector Variation Notes

| Collector | API style | Auth | Key request params | Response format | Geo strategy |
|---|---|---|---|---|---|
| FrenchOpenGovCollector | CKAN REST | apiKey header (optional) | q, organization | JSON | France centroid (46.603, 2.346) |
| GermanOpenGovCollector | CKAN REST | none | q, fq | JSON | Germany centroid (51.165, 10.451) |
| BundestagDIPCollector | Custom REST | apiKey header | f.typ, f.datum.start, f.datum.end | JSON | Germany centroid |
| SingaporeOpenGovCollector | CKAN REST | none | q | JSON | Singapore (1.352, 103.820) |
| IndianOpenGovCollector | REST | apiKey query param | resource_id, filters | JSON | India centroid (20.594, 78.963) |
| TaiwanOpenGovCollector | REST | none | q | JSON | Taiwan centroid (23.698, 120.960) |
| HungarianTendersCollector | REST | none | dateFrom, dateTo | JSON | Hungary centroid (47.162, 19.503) |
| PolishTendersCollector | REST | none | dateFrom, dateTo | JSON | Poland centroid (51.919, 19.145) |
| RomanianTendersCollector | REST | none | dateFrom, dateTo | JSON | Romania centroid (45.943, 24.967) |
| SpanishTendersCollector | Atom/XML | none | dateFrom, dateTo | XML → parse to dict | Spain centroid (40.464, -3.749) |
| UkrainianTendersCollector | REST | none | dateFrom, dateTo | JSON | Ukraine centroid (48.379, 31.166) |

**Auth patterns:**
- **apiKey header**: French Open Data (`X-API-Key`), Bundestag DIP (`Authorization`)
- **apiKey query param**: Indian Open Data (`api-key`)
- **No auth**: DE, SG, TW, HU, PL, RO, ES, UA — all free, no key needed

**API key security:** Same rule as Cycle 026 — strip/redact API keys from `receipt.request_parameters`.

### 2.4 Procurement Collector Commonalities

The 5 European procurement collectors share a pattern:

1. Query by date window (`dateFrom`/`dateTo` or equivalent)
2. Return list of tender notices (publication date, contracting authority, title, value, status)
3. Normalise to `NormalisedEvent` with `SECTOR_RISK_SCORE` MeasureType
4. GeoPoint from country centroid
5. resolution_role = `primary_evidence` (procurement notices are immutable once published)
6. settlement_eligible = true

**Consider a shared base class:** `BaseProcurementCollector(BaseCollector)` with common date-windowing logic, normalisation, and receipt construction. Each concrete collector only overrides URL construction and response parsing. This is a suggestion, not a requirement — Loa may implement flat or with shared base.

### 2.5 Spanish Tenders — XML Response

`SpanishTendersCollector` is the only Batch 2 collector returning XML (Atom syndication format). Use `xml.etree.ElementTree` from stdlib to parse. Do NOT add `lxml` or other dependencies. The Atom namespace is `http://www.w3.org/2005/Atom`. Extract `entry` elements, map `title`, `updated`, `content` to normalised event fields.

### 2.6 Ukrainian Tenders — Prozorro

Prozorro (`public-api.prozorro.gov.ua`) is a well-documented JSON REST API. The Ukrainian government's e-procurement system is one of the most transparent globally. Key endpoint: `GET /api/2.5/tenders` with `offset` for pagination. The API returns tender data including `procuringEntity`, `value`, `status`, `dateModified`.

### 2.7 CollectionRunner Registration

**File: `backend/osint/collectors/__init__.py`**

Add 11 new imports and instances to `build_collector_map()`:

```python
# Batch 2 — Jurisdiction expansion (Cycle-027)
from backend.osint.collectors.fr_open_gov import FrenchOpenGovCollector
from backend.osint.collectors.de_open_gov import GermanOpenGovCollector
from backend.osint.collectors.bundestag_dip import BundestagDIPCollector
from backend.osint.collectors.sg_open_gov import SingaporeOpenGovCollector
from backend.osint.collectors.in_open_gov import IndianOpenGovCollector
from backend.osint.collectors.tw_open_gov import TaiwanOpenGovCollector
from backend.osint.collectors.hu_tenders import HungarianTendersCollector
from backend.osint.collectors.pl_tenders import PolishTendersCollector
from backend.osint.collectors.ro_tenders import RomanianTendersCollector
from backend.osint.collectors.es_tenders import SpanishTendersCollector
from backend.osint.collectors.ua_tenders import UkrainianTendersCollector

batch_2 = [
    FrenchOpenGovCollector(),
    GermanOpenGovCollector(),
    BundestagDIPCollector(),
    SingaporeOpenGovCollector(),
    IndianOpenGovCollector(),
    TaiwanOpenGovCollector(),
    HungarianTendersCollector(),
    PolishTendersCollector(),
    RomanianTendersCollector(),
    SpanishTendersCollector(),
    UkrainianTendersCollector(),
]
for collector in batch_2:
    collectors[collector.source_id()] = collector
```

### 2.8 Rate Limit Handling

Same strategy as Cycle 026 SDD Section 2.6:
- HTTP 429 → return `CollectionResult(success=False, error="Rate limited (429)")`
- HTTP 403 → return `CollectionResult(success=False, error="Auth failed (403)")`
- No retry on rate limit
- API key fail-fast for auth-required collectors

**Rate limit reference:**

| Source | Free tier limit | Strategy |
|---|---|---|
| French Open Data | Generous (CKAN standard) | No special handling |
| German Open Data | Generous (CKAN standard) | No special handling |
| Bundestag DIP | Generous | No special handling |
| Singapore Open Data | Generous | No special handling |
| Indian Open Data | Moderate | Mock in tests |
| Taiwan Open Data | Generous | No special handling |
| Hungarian Procurement | Unknown — assume generous | No special handling |
| Polish Procurement | Unknown — assume generous | No special handling |
| Romanian Procurement | Unknown — assume generous | No special handling |
| Spanish Procurement | Unknown — assume generous | No special handling |
| Ukrainian Procurement (Prozorro) | Generous (well-documented) | No special handling |

---

## 3. Dependency Graph

```
sources.json expansion (2.1) — +11 entries, version 0.6.0
    └── RegistryLoader validates all 27 entries

11 collector implementations (2.2–2.6)
    └── Each uses BaseCollector contract + canonical hash functions
    └── Each produces CollectionResult → persist_signal → osint_signals (from Cycle 025)

CollectionRunner registration (2.7)
    └── build_collector_map() includes all 11 new collectors
    └── 24 total collectors in concurrent collection
```

---

## 4. Risk Assessment

| Risk | Impact | Mitigation |
|---|---|---|
| Government APIs down or restructured | Tests fail, collector unusable | Mock all HTTP in tests. Government APIs generally stable |
| Prozorro API version change (2.5 → 3.0) | Response schema mismatch | Pin API version in URL. Monitor Prozorro changelog |
| Spanish XML format changes | Parse failures | Use stdlib XML parser. Validate Atom namespace |
| Indian API key approval delay | Collector returns auth error | Fail-fast with descriptive error. Collector still in registry as inactive |
| Low query volume from small-jurisdiction portals | Sparse signal data | Expected — sparse is better than absent for convergence |
| 24 concurrent collectors strain collection runner | Timeout pressure | CollectionRunner already handles per-collector timeout. Monitor |

---

## 5. Files Touched (Summary)

| File | Change |
|---|---|
| `backend/osint/sources.json` | +11 entries, version bump to 0.6.0 |
| `backend/osint/collectors/fr_open_gov.py` | **New** — FrenchOpenGovCollector |
| `backend/osint/collectors/de_open_gov.py` | **New** — GermanOpenGovCollector |
| `backend/osint/collectors/bundestag_dip.py` | **New** — BundestagDIPCollector |
| `backend/osint/collectors/sg_open_gov.py` | **New** — SingaporeOpenGovCollector |
| `backend/osint/collectors/in_open_gov.py` | **New** — IndianOpenGovCollector |
| `backend/osint/collectors/tw_open_gov.py` | **New** — TaiwanOpenGovCollector |
| `backend/osint/collectors/hu_tenders.py` | **New** — HungarianTendersCollector |
| `backend/osint/collectors/pl_tenders.py` | **New** — PolishTendersCollector |
| `backend/osint/collectors/ro_tenders.py` | **New** — RomanianTendersCollector |
| `backend/osint/collectors/es_tenders.py` | **New** — SpanishTendersCollector |
| `backend/osint/collectors/ua_tenders.py` | **New** — UkrainianTendersCollector |
| `backend/osint/collectors/__init__.py` | Updated — build_collector_map() includes Batch 2 |
| `backend/core/signal_detector.py` | **UNTOUCHED** — Path 2, do not modify |
| `backend/core/osint_registry.py` | **UNTOUCHED** — Path 2, do not modify |
| `backend/tests/test_cycle027_*.py` | **New** — ~26 tests |
