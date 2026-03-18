"""UK Carbon Intensity collector.

Implements BaseCollector for the Carbon Intensity API.
Auth: None required (public API).
Endpoint: GET /intensity/{from}/{to}

No auth required. Operated by National Grid ESO.
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

BASE_URL = "https://api.carbonintensity.org.uk"

# UK centroid
_UK_GEO = GeoPoint(lat=54.0, lon=-2.0, radius_m=500000)


class CarbonIntensityCollector(BaseCollector):
    """UK Carbon Intensity API collector — grid carbon intensity data.

    No auth required. Operated by National Grid ESO.
    """

    def __init__(self, base_url: str | None = None) -> None:
        self._base_url = base_url or BASE_URL

    def source_id(self) -> str:
        return "carbon_intensity_api"

    async def _fetch(self, request: dict, theatre_id: str) -> CollectionResult:
        """GET /intensity/{from}/{to} for date range."""
        now = datetime.utcnow()

        date_from = request.get("date_from", request.get("evaluation_window_start", ""))
        date_to = request.get("date_to", request.get("evaluation_window_end", ""))

        if not date_from or not date_to:
            from datetime import timedelta
            date_to = now.strftime("%Y-%m-%dT%H:%MZ")
            date_from = (now - timedelta(hours=24)).strftime("%Y-%m-%dT%H:%MZ")

        url = f"{self._base_url}/intensity/{date_from}/{date_to}"
        query = f"from={date_from}&to={date_to}"
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
        """Parse Carbon Intensity response and build EvidenceBundle."""
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

        intensity_data = data.get("data", [])
        if intensity_data:
            latest = intensity_data[-1]
            intensity = latest.get("intensity", {})
            actual = intensity.get("actual", intensity.get("forecast", 0))
            index = intensity.get("index", "unknown")
        else:
            actual = 0
            index = "no_data"

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
            value=float(actual) if actual else 0.0,
            unit="gCO2/kWh",
            metadata={"index": index, "data_points": len(intensity_data)},
        )

        event = NormalisedEvent(
            event_id=f"evt_ci_{int(now.timestamp())}",
            geo=_UK_GEO,
            measure=measure,
            confidence=0.95,
            timestamp=now,
        )

        bundle = EvidenceBundle(
            bundle_id=f"eb_ci_{int(now.timestamp())}",
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
        """Fetch current intensity as health probe."""
        try:
            url = f"{self._base_url}/intensity"
            await self._do_http_get(url)
            return HealthStatus.HEALTHY
        except Exception:
            return HealthStatus.UNAVAILABLE
