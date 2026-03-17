"""OpenAQ collector.

Implements BaseCollector for the OpenAQ API v2.
Auth: X-API-Key header.
Endpoint: GET /v2/measurements

API key from ECHELON_OPENAQ_API_KEY env var.
No key -> CollectionResult(success=False), does NOT raise.
"""
from __future__ import annotations

import asyncio
import json
import os
import time
import urllib.error
import urllib.request
from datetime import datetime

from backend.osint.canonical import compute_content_hash, compute_receipt_hash
from backend.osint.collectors.base import BaseCollector
from backend.osint.models.evidence import (
    CollectionResult,
    EvidenceBundle,
    GeoPoint,
    HTTPTranscriptReceipt,
    HealthStatus,
    MeasureType,
    NormalisedEvent,
    NormalisedMeasure,
)

BASE_URL = "https://api.openaq.org"

_GLOBAL_GEO = GeoPoint(lat=0.0, lon=0.0, radius_m=20000000)


class OpenAQCollector(BaseCollector):
    """OpenAQ API collector — global air quality measurements.

    Auth: API key via X-API-Key header.
    API key from ECHELON_OPENAQ_API_KEY env var.
    """

    def __init__(self, api_key: str | None = None, base_url: str | None = None) -> None:
        self._api_key = api_key or os.environ.get("ECHELON_OPENAQ_API_KEY", "")
        self._base_url = base_url or BASE_URL

    def source_id(self) -> str:
        return "openaq_api"

    async def _fetch(self, request: dict, theatre_id: str) -> CollectionResult:
        """GET /v2/measurements with X-API-Key header."""
        now = datetime.utcnow()

        if not self._api_key:
            return CollectionResult(
                source_id=self.source_id(),
                bundle=None,
                raw_payload=b"",
                fetch_duration_ms=0.0,
                success=False,
                error="No API key configured (ECHELON_OPENAQ_API_KEY)",
                retrieved_at=now,
            )

        country = request.get("country", "US")
        parameter = request.get("parameter", "pm25")
        date_from = request.get("date_from", request.get("evaluation_window_start", ""))
        date_to = request.get("date_to", request.get("evaluation_window_end", ""))

        query_parts = [f"country={country}", f"parameter={parameter}", "limit=10"]
        if date_from:
            query_parts.append(f"date_from={date_from}")
        if date_to:
            query_parts.append(f"date_to={date_to}")
        query = "&".join(query_parts)
        url = f"{self._base_url}/v2/measurements?{query}"
        start_ms = time.monotonic() * 1000

        try:
            raw_payload = await self._do_http_get(url)
            duration_ms = time.monotonic() * 1000 - start_ms
            return self._build_success_result(
                raw_payload=raw_payload,
                url=url,
                query=query,
                theatre_id=theatre_id,
                duration_ms=duration_ms,
                country=country,
                parameter=parameter,
            )
        except urllib.error.HTTPError as exc:
            duration_ms = time.monotonic() * 1000 - start_ms
            return CollectionResult(
                source_id=self.source_id(),
                bundle=None,
                raw_payload=b"",
                fetch_duration_ms=duration_ms,
                success=False,
                error=f"HTTP {exc.code}: {exc.reason}",
                retrieved_at=now,
            )
        except (urllib.error.URLError, OSError, ConnectionError) as exc:
            duration_ms = time.monotonic() * 1000 - start_ms
            return CollectionResult(
                source_id=self.source_id(),
                bundle=None,
                raw_payload=b"",
                fetch_duration_ms=duration_ms,
                success=False,
                error=f"Connection error: {exc}",
                retrieved_at=now,
            )

    async def _do_http_get(self, url: str) -> bytes:
        """Execute HTTP GET with X-API-Key header in a thread pool."""
        loop = asyncio.get_event_loop()
        api_key = self._api_key

        def _sync_get() -> bytes:
            req = urllib.request.Request(
                url,
                headers={
                    "Accept": "application/json",
                    "X-API-Key": api_key,
                },
                method="GET",
            )
            with urllib.request.urlopen(req, timeout=30.0) as resp:
                return resp.read()

        return await asyncio.wait_for(
            loop.run_in_executor(None, _sync_get),
            timeout=30.0,
        )

    def _build_success_result(
        self,
        raw_payload: bytes,
        url: str,
        query: str,
        theatre_id: str,
        duration_ms: float,
        country: str,
        parameter: str,
    ) -> CollectionResult:
        """Parse OpenAQ response and build EvidenceBundle."""
        now = datetime.utcnow()

        try:
            data = json.loads(raw_payload)
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            return CollectionResult(
                source_id=self.source_id(),
                bundle=None,
                raw_payload=raw_payload,
                fetch_duration_ms=duration_ms,
                success=False,
                error=f"Malformed response: {exc}",
                retrieved_at=now,
            )

        results = data.get("results", [])

        # Use first measurement's coordinates for geo, or default
        if results:
            coords = results[0].get("coordinates", {})
            lat = coords.get("latitude", 0.0)
            lon = coords.get("longitude", 0.0)
            geo = GeoPoint(lat=lat, lon=lon, radius_m=50000)
            avg_value = sum(r.get("value", 0) for r in results) / len(results)
        else:
            geo = _GLOBAL_GEO
            avg_value = 0.0

        content_hash = compute_content_hash(raw_payload)
        # Redact API key from headers in receipt
        headers_str = "accept:application/json"
        receipt_hash = compute_receipt_hash(
            method="GET", url=url, query=query,
            headers=headers_str, body_hash=content_hash,
        )

        receipt = HTTPTranscriptReceipt(
            timestamp=now,
            request_parameters={
                "method": "GET", "url": url,
                "query": query, "headers": headers_str,
            },
            source_id=self.source_id(),
            source_version="v2",
            http_status=200,
            content_hash=content_hash,
            receipt_hash=receipt_hash,
        )

        measure = NormalisedMeasure(
            type=MeasureType.SECTOR_RISK_SCORE,
            value=avg_value,
            unit=parameter,
            metadata={"country": country, "parameter": parameter, "measurement_count": len(results)},
        )

        event = NormalisedEvent(
            event_id=f"evt_oaq_{country}_{int(now.timestamp())}",
            geo=geo,
            measure=measure,
            confidence=0.85,
            timestamp=now,
        )

        bundle = EvidenceBundle(
            bundle_id=f"eb_oaq_{country}_{int(now.timestamp())}",
            source_id=self.source_id(),
            source_group="environmental",
            resolution_role="secondary_corroboration",
            evidence_timestamp=now,
            raw_payload_hash=content_hash,
            receipt=receipt,
            normalised_event=event,
        )

        return CollectionResult(
            source_id=self.source_id(),
            bundle=bundle,
            raw_payload=raw_payload,
            fetch_duration_ms=duration_ms,
            success=True,
            error=None,
            retrieved_at=now,
        )

    async def health_check(self) -> HealthStatus:
        """Fetch US PM2.5 as health probe."""
        if not self._api_key:
            return HealthStatus.UNAVAILABLE
        try:
            url = f"{self._base_url}/v2/measurements?country=US&parameter=pm25&limit=1"
            await self._do_http_get(url)
            return HealthStatus.HEALTHY
        except Exception:
            return HealthStatus.UNAVAILABLE
