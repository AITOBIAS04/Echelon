"""USGS Earthquake Hazards collector.

Implements BaseCollector for the USGS Earthquake API.
Auth: None required (public API).
Endpoint: GET /fdsnws/event/1/query with format=geojson

No auth required. No documented rate limit.
"""
from __future__ import annotations

import asyncio
import json
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

BASE_URL = "https://earthquake.usgs.gov"


class USGSEarthquakeCollector(BaseCollector):
    """USGS Earthquake Hazards API collector — seismic event data.

    No auth required. GeoJSON format responses.
    """

    def __init__(self, base_url: str | None = None) -> None:
        self._base_url = base_url or BASE_URL

    def source_id(self) -> str:
        return "usgs_earthquake_api"

    async def _fetch(self, request: dict, theatre_id: str) -> CollectionResult:
        """GET /fdsnws/event/1/query with GeoJSON format."""
        now = datetime.utcnow()

        starttime = request.get("starttime", request.get("evaluation_window_start", ""))
        endtime = request.get("endtime", request.get("evaluation_window_end", ""))
        min_magnitude = request.get("minmagnitude", "4.0")

        if not starttime or not endtime:
            # Default to last 24 hours
            from datetime import timedelta
            endtime = now.strftime("%Y-%m-%dT%H:%M:%S")
            starttime = (now - timedelta(hours=24)).strftime("%Y-%m-%dT%H:%M:%S")

        query = f"format=geojson&starttime={starttime}&endtime={endtime}&minmagnitude={min_magnitude}"
        url = f"{self._base_url}/fdsnws/event/1/query?{query}"
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
        """Execute HTTP GET in a thread pool. No auth."""
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
    ) -> CollectionResult:
        """Parse USGS GeoJSON response and build EvidenceBundle."""
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

        features = data.get("features", [])
        event_count = len(features)

        # Use first earthquake epicentre as geo, or default global
        if features:
            coords = features[0].get("geometry", {}).get("coordinates", [0.0, 0.0])
            lon, lat = coords[0], coords[1]
            mag = features[0].get("properties", {}).get("mag", 0.0)
            place = features[0].get("properties", {}).get("place", "")
            geo = GeoPoint(lat=lat, lon=lon, radius_m=100000)
        else:
            geo = GeoPoint(lat=0.0, lon=0.0, radius_m=20000000)
            mag = 0.0
            place = ""

        content_hash = compute_content_hash(raw_payload)
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
            source_version="v1.0",
            http_status=200,
            content_hash=content_hash,
            receipt_hash=receipt_hash,
        )

        measure = NormalisedMeasure(
            type=MeasureType.SECTOR_RISK_SCORE,
            value=float(mag) if mag else 0.0,
            unit="magnitude",
            metadata={"event_count": event_count, "place": place},
        )

        event = NormalisedEvent(
            event_id=f"evt_usgs_{int(now.timestamp())}",
            geo=geo,
            measure=measure,
            confidence=1.0,
            timestamp=now,
        )

        bundle = EvidenceBundle(
            bundle_id=f"eb_usgs_{int(now.timestamp())}",
            source_id=self.source_id(),
            source_group="geophysical_hazard",
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
        """Fetch recent M5+ quakes as health probe."""
        try:
            url = f"{self._base_url}/fdsnws/event/1/query?format=geojson&limit=1&minmagnitude=5"
            await self._do_http_get(url)
            return HealthStatus.HEALTHY
        except Exception:
            return HealthStatus.UNAVAILABLE
