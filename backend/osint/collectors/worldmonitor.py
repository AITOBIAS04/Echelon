"""WorldMonitor three-domain collector — CII, Market, Maritime.

One collector instance per WM domain per Theatre. Produces EvidenceBundle
with HTTPTranscriptReceipt per the canonical spec. Uses stdlib HTTP
(urllib.request) to avoid new runtime dependencies. All HTTP calls are
mocked in tests — WorldMonitor is NOT running locally.

Failure mode pinning:
  HTTP 200  -> CollectionResult(success=True) with valid bundle
  HTTP 5xx  -> Retry up to retry_count, then success=False
  Timeout   -> Single attempt timeout, then retry
  ConnError -> Same as 5xx; health_check -> UNAVAILABLE
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone

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
    WMDomain,
)


@dataclass
class WorldMonitorConfig:
    """Configuration for WorldMonitor HTTP client."""

    base_url: str = "http://localhost:8080"
    timeout_s: float = 30.0
    version: str = "v0.1.0"
    retry_count: int = 2
    retry_delay_s: float = 1.0


# Domain -> endpoint mapping
_DOMAIN_ENDPOINTS: dict[WMDomain, str] = {
    WMDomain.INTELLIGENCE: "/api/v1/intelligence/cii",
    WMDomain.MARKET: "/api/v1/market/snapshot",
    WMDomain.MARITIME: "/api/v1/maritime/anomaly",
}

# Domain -> source_id mapping
_DOMAIN_SOURCE_IDS: dict[WMDomain, str] = {
    WMDomain.INTELLIGENCE: "worldmonitor_cii",
    WMDomain.MARKET: "worldmonitor_finance",
    WMDomain.MARITIME: "worldmonitor_maritime",
}

# Domain -> source_group mapping
_DOMAIN_SOURCE_GROUPS: dict[WMDomain, str] = {
    WMDomain.INTELLIGENCE: "alt_data_behavioural",
    WMDomain.MARKET: "market_data",
    WMDomain.MARITIME: "maritime_ais",
}

# Domain -> default measure type mapping
_DOMAIN_MEASURE_TYPES: dict[WMDomain, MeasureType] = {
    WMDomain.INTELLIGENCE: MeasureType.COUNTRY_INSTABILITY_INDEX,
    WMDomain.MARKET: MeasureType.SECTOR_RISK_SCORE,
    WMDomain.MARITIME: MeasureType.VESSEL_DENSITY_ANOMALY,
}


class WorldMonitorCollector(BaseCollector):
    """Three-domain collector for WorldMonitor endpoints.

    One instance per WM domain per Theatre. Produces EvidenceBundle
    with HTTPTranscriptReceipt per the canonical spec.
    """

    def __init__(
        self, domain: WMDomain, config: WorldMonitorConfig | None = None
    ) -> None:
        self._domain = domain
        self._config = config or WorldMonitorConfig()
        self._endpoint = _DOMAIN_ENDPOINTS[domain]
        self._source_id_value = _DOMAIN_SOURCE_IDS[domain]
        self._source_group = _DOMAIN_SOURCE_GROUPS[domain]

    def source_id(self) -> str:
        """Registry source_id for this domain."""
        return self._source_id_value

    @property
    def domain(self) -> WMDomain:
        """The WM domain this collector handles."""
        return self._domain

    @property
    def config(self) -> WorldMonitorConfig:
        """Collector configuration."""
        return self._config

    async def _fetch(self, request: dict, theatre_id: str) -> CollectionResult:
        """HTTP POST to WM endpoint with retry logic.

        1. Build request URL from config.base_url + endpoint
        2. POST with timeout_s
        3. On success: parse response, build EvidenceBundle + HTTPTranscriptReceipt
        4. On failure: retry up to retry_count with retry_delay_s
        5. All retries exhausted: return CollectionResult(success=False)
        """
        url = f"{self._config.base_url}{self._endpoint}"
        last_error: str | None = None
        attempts = 1 + self._config.retry_count  # initial + retries

        for attempt in range(attempts):
            start_ms = time.monotonic() * 1000
            try:
                raw_payload = await self._do_http_post(url, request)
                duration_ms = time.monotonic() * 1000 - start_ms
                return self._build_success_result(
                    raw_payload=raw_payload,
                    url=url,
                    request=request,
                    theatre_id=theatre_id,
                    duration_ms=duration_ms,
                )
            except asyncio.TimeoutError:
                duration_ms = time.monotonic() * 1000 - start_ms
                last_error = f"Timeout after {self._config.timeout_s}s (attempt {attempt + 1}/{attempts})"
            except urllib.error.HTTPError as exc:
                duration_ms = time.monotonic() * 1000 - start_ms
                last_error = f"HTTP {exc.code}: {exc.reason} (attempt {attempt + 1}/{attempts})"
            except (urllib.error.URLError, OSError, ConnectionError) as exc:
                duration_ms = time.monotonic() * 1000 - start_ms
                last_error = f"Connection error: {exc} (attempt {attempt + 1}/{attempts})"
            except Exception as exc:
                duration_ms = time.monotonic() * 1000 - start_ms
                last_error = f"Unexpected error: {exc} (attempt {attempt + 1}/{attempts})"

            # Retry delay (skip on last attempt)
            if attempt < attempts - 1:
                await asyncio.sleep(self._config.retry_delay_s)

        # All retries exhausted
        return CollectionResult(
            source_id=self._source_id_value,
            bundle=None,
            raw_payload=b"",
            fetch_duration_ms=duration_ms,
            success=False,
            error=last_error,
            retrieved_at=datetime.now(timezone.utc),
        )

    async def _do_http_post(self, url: str, request: dict) -> bytes:
        """Execute synchronous HTTP POST in a thread pool with timeout.

        Returns the raw response bytes. Raises on HTTP error, timeout,
        or connection failure.
        """
        loop = asyncio.get_event_loop()

        def _sync_post() -> bytes:
            req_data = json.dumps(request).encode("utf-8")
            req = urllib.request.Request(
                url,
                data=req_data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=self._config.timeout_s) as resp:
                return resp.read()

        return await asyncio.wait_for(
            loop.run_in_executor(None, _sync_post),
            timeout=self._config.timeout_s,
        )

    def _build_success_result(
        self,
        raw_payload: bytes,
        url: str,
        request: dict,
        theatre_id: str,
        duration_ms: float,
    ) -> CollectionResult:
        """Parse response bytes and build EvidenceBundle + receipt."""
        now = datetime.now(timezone.utc)
        try:
            data = json.loads(raw_payload)
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            return CollectionResult(
                source_id=self._source_id_value,
                bundle=None,
                raw_payload=raw_payload,
                fetch_duration_ms=duration_ms,
                success=False,
                error=f"Malformed response: {exc}",
                retrieved_at=now,
            )

        content_hash = compute_content_hash(raw_payload)
        query_str = json.dumps(request, sort_keys=True, separators=(",", ":"))
        receipt_hash = compute_receipt_hash(
            method="POST",
            url=url,
            query=query_str,
            headers="content-type:application/json",
            body_hash=content_hash,
        )

        receipt = HTTPTranscriptReceipt(
            timestamp=now,
            request_parameters={
                "method": "POST",
                "url": url,
                "query": query_str,
                "headers": "content-type:application/json",
            },
            source_id=self._source_id_value,
            source_version=self._config.version,
            http_status=200,
            content_hash=content_hash,
            receipt_hash=receipt_hash,
        )

        # Extract bundle from response if present, otherwise build from raw
        bundle_data = data.get("bundle", data)
        bundle = self._build_bundle(bundle_data, receipt, now, content_hash)

        return CollectionResult(
            source_id=self._source_id_value,
            bundle=bundle,
            raw_payload=raw_payload,
            fetch_duration_ms=duration_ms,
            success=True,
            error=None,
            retrieved_at=now,
        )

    def _build_bundle(
        self,
        data: dict,
        receipt: HTTPTranscriptReceipt,
        timestamp: datetime,
        content_hash: str,
    ) -> EvidenceBundle:
        """Construct EvidenceBundle from parsed response data."""
        # Try to extract nested structures from the response
        event_data = data.get("normalised_event", {})
        geo_data = event_data.get("geo", data.get("geo", {}))
        measure_data = event_data.get("measure", data.get("measure", {}))

        geo = GeoPoint(
            lat=geo_data.get("lat", 0.0),
            lon=geo_data.get("lon", 0.0),
            radius_m=geo_data.get("radius_m", 50000),
        )

        # Determine measure type from domain or data
        measure_type_str = measure_data.get("type", _DOMAIN_MEASURE_TYPES[self._domain].value)
        try:
            measure_type = MeasureType(measure_type_str)
        except ValueError:
            measure_type = _DOMAIN_MEASURE_TYPES[self._domain]

        measure = NormalisedMeasure(
            type=measure_type,
            value=measure_data.get("value", 0.0),
            unit=measure_data.get("unit", "0_1"),
            metadata=measure_data.get("metadata"),
        )

        event = NormalisedEvent(
            event_id=event_data.get("event_id", f"evt_{self._source_id_value}_{int(timestamp.timestamp())}"),
            geo=geo,
            measure=measure,
            confidence=event_data.get("confidence", 0.5),
            timestamp=timestamp,
        )

        return EvidenceBundle(
            bundle_id=data.get("bundle_id", f"eb_{self._source_id_value}_{int(timestamp.timestamp())}"),
            source_id=self._source_id_value,
            source_group=self._source_group,
            resolution_role="primary_evidence",
            evidence_timestamp=timestamp,
            raw_payload_hash=content_hash,
            receipt=receipt,
            normalised_event=event,
        )

    async def health_check(self) -> HealthStatus:
        """GET /health, extract per-domain status.

        Returns HEALTHY, DEGRADED, or UNAVAILABLE.
        Connection errors -> UNAVAILABLE.
        """
        url = f"{self._config.base_url}/health"
        try:
            loop = asyncio.get_event_loop()

            def _sync_get() -> bytes:
                req = urllib.request.Request(url, method="GET")
                with urllib.request.urlopen(req, timeout=self._config.timeout_s) as resp:
                    return resp.read()

            raw = await asyncio.wait_for(
                loop.run_in_executor(None, _sync_get),
                timeout=self._config.timeout_s,
            )
            data = json.loads(raw)
            domains = data.get("domains", {})
            domain_key = self._domain.value
            domain_status = domains.get(domain_key, data.get("status", "unavailable"))
            try:
                return HealthStatus(domain_status)
            except ValueError:
                return HealthStatus.UNAVAILABLE
        except Exception:
            return HealthStatus.UNAVAILABLE
