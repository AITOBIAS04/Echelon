"""OpenSky Network collector.

Implements BaseCollector for the OpenSky Network API.
Auth: None required (public API).
Endpoint: GET /api/states/all with bounding box

No auth required. ~100 req/day.
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

BASE_URL = "https://opensky-network.org/api"


class OpenSkyCollector(BaseCollector):
    """OpenSky Network API collector — live flight tracking.

    No auth required. Public API with rate limiting (~100 req/day).
    """

    def __init__(self, base_url: str | None = None) -> None:
        self._base_url = base_url or BASE_URL

    def source_id(self) -> str:
        return "opensky_api"

    async def _fetch(self, request: dict, theatre_id: str) -> CollectionResult:
        """GET /states/all with bounding box params."""
        now = datetime.utcnow()

        # Extract bounding box from request or geo
        geo = request.get("geo", {})
        lamin = request.get("lamin", geo.get("lat", 45.0) - 5.0)
        lamax = request.get("lamax", geo.get("lat", 45.0) + 5.0)
        lomin = request.get("lomin", geo.get("lon", 10.0) - 5.0)
        lomax = request.get("lomax", geo.get("lon", 10.0) + 5.0)

        query = f"lamin={lamin}&lamax={lamax}&lomin={lomin}&lomax={lomax}"
        url = f"{self._base_url}/states/all?{query}"
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
                lamin=lamin,
                lamax=lamax,
                lomin=lomin,
                lomax=lomax,
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
        lamin: float,
        lamax: float,
        lomin: float,
        lomax: float,
    ) -> CollectionResult:
        """Parse OpenSky response and build EvidenceBundle."""
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

        states = data.get("states") or []
        aircraft_count = len(states)

        # Centre of bounding box as geo
        center_lat = (lamin + lamax) / 2
        center_lon = (lomin + lomax) / 2
        geo = GeoPoint(lat=center_lat, lon=center_lon, radius_m=500000)

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
            type=MeasureType.VESSEL_DENSITY_ANOMALY,
            value=float(aircraft_count),
            unit="aircraft_count",
            metadata={"bounding_box": {"lamin": lamin, "lamax": lamax, "lomin": lomin, "lomax": lomax}},
        )

        event = NormalisedEvent(
            event_id=f"evt_osky_{int(now.timestamp())}",
            geo=geo,
            measure=measure,
            confidence=0.85,
            timestamp=now,
        )

        bundle = EvidenceBundle(
            bundle_id=f"eb_osky_{int(now.timestamp())}",
            source_id=self.source_id(),
            source_group="geospatial",
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
        """Fetch small bounding box as health probe."""
        try:
            url = f"{self._base_url}/states/all?lamin=47&lamax=48&lomin=8&lomax=9"
            await self._do_http_get(url)
            return HealthStatus.HEALTHY
        except Exception:
            return HealthStatus.UNAVAILABLE
