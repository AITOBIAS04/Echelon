"""FRED (Federal Reserve Economic Data) collector.

Implements BaseCollector for the FRED API.
Auth: API key via query parameter (api_key).
Endpoint: GET /fred/series/observations

API key from ECHELON_FRED_API_KEY env var.
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

BASE_URL = "https://api.stlouisfed.org"

# US centroid for FRED (no inherent geography)
_US_GEO = GeoPoint(lat=39.8283, lon=-98.5795, radius_m=5000000)


class FREDCollector(BaseCollector):
    """FRED API collector — economic time series observations.

    Auth: API key as query parameter.
    API key from ECHELON_FRED_API_KEY env var.
    """

    def __init__(self, api_key: str | None = None, base_url: str | None = None) -> None:
        self._api_key = api_key or os.environ.get("ECHELON_FRED_API_KEY", "")
        self._base_url = base_url or BASE_URL

    def source_id(self) -> str:
        return "fred_api"

    async def _fetch(self, request: dict, theatre_id: str) -> CollectionResult:
        """GET /fred/series/observations with api_key query param."""
        now = datetime.utcnow()

        if not self._api_key:
            return CollectionResult(
                source_id=self.source_id(),
                bundle=None,
                raw_payload=b"",
                fetch_duration_ms=0.0,
                success=False,
                error="No API key configured (ECHELON_FRED_API_KEY)",
                retrieved_at=now,
            )

        series_id = request.get("series_id", "")
        if not series_id:
            return CollectionResult(
                source_id=self.source_id(),
                bundle=None,
                raw_payload=b"",
                fetch_duration_ms=0.0,
                success=False,
                error="No series_id in request",
                retrieved_at=now,
            )

        query = f"series_id={series_id}&api_key={self._api_key}&file_type=json&sort_order=desc&limit=1"
        url = f"{self._base_url}/fred/series/observations?{query}"
        # Redacted URL for receipt (strip API key)
        safe_query = f"series_id={series_id}&file_type=json&sort_order=desc&limit=1"
        safe_url = f"{self._base_url}/fred/series/observations?{safe_query}"
        start_ms = time.monotonic() * 1000

        try:
            raw_payload = await self._do_http_get(url)
            duration_ms = time.monotonic() * 1000 - start_ms
            return self._build_success_result(
                raw_payload=raw_payload,
                url=safe_url,
                query=safe_query,
                theatre_id=theatre_id,
                duration_ms=duration_ms,
                series_id=series_id,
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
        """Execute HTTP GET in a thread pool (no auth header — key in query)."""
        loop = asyncio.get_event_loop()

        def _sync_get() -> bytes:
            req = urllib.request.Request(
                url,
                headers={"Accept": "application/json"},
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
        series_id: str,
    ) -> CollectionResult:
        """Parse FRED response and build EvidenceBundle + receipt."""
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

        observations = data.get("observations", [])
        if not observations:
            return CollectionResult(
                source_id=self.source_id(),
                bundle=None,
                raw_payload=raw_payload,
                fetch_duration_ms=duration_ms,
                success=False,
                error=f"No observations for series_id '{series_id}'",
                retrieved_at=now,
            )

        latest = observations[0]
        value_str = latest.get("value", ".")
        value = float(value_str) if value_str != "." else 0.0

        content_hash = compute_content_hash(raw_payload)
        headers_str = "accept:application/json"
        receipt_hash = compute_receipt_hash(
            method="GET", url=url, query=query,
            headers=headers_str, body_hash=content_hash,
        )

        receipt = HTTPTranscriptReceipt(
            timestamp=now,
            request_parameters={
                "method": "GET",
                "url": url,
                "query": query,
                "headers": headers_str,
            },
            source_id=self.source_id(),
            source_version="v1.0",
            http_status=200,
            content_hash=content_hash,
            receipt_hash=receipt_hash,
        )

        measure = NormalisedMeasure(
            type=MeasureType.SECTOR_RISK_SCORE,
            value=value,
            unit=series_id,
            metadata={"series_id": series_id, "date": latest.get("date", "")},
        )

        event = NormalisedEvent(
            event_id=f"evt_fred_{series_id}_{int(now.timestamp())}",
            geo=_US_GEO,
            measure=measure,
            confidence=1.0,
            timestamp=now,
        )

        bundle = EvidenceBundle(
            bundle_id=f"eb_fred_{series_id}_{int(now.timestamp())}",
            source_id=self.source_id(),
            source_group="market_data",
            resolution_role="primary_evidence",
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
        """Fetch GDP series as health probe."""
        if not self._api_key:
            return HealthStatus.UNAVAILABLE
        try:
            query = f"series_id=GDP&api_key={self._api_key}&file_type=json&limit=1"
            url = f"{self._base_url}/fred/series/observations?{query}"
            await self._do_http_get(url)
            return HealthStatus.HEALTHY
        except Exception:
            return HealthStatus.UNAVAILABLE
