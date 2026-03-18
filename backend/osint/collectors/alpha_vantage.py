"""Alpha Vantage collector.

Implements BaseCollector for the Alpha Vantage API.
Auth: API key via query parameter (apikey).
Endpoint: GET with function=TIME_SERIES_DAILY

API key from ECHELON_ALPHA_VANTAGE_API_KEY env var.
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

BASE_URL = "https://www.alphavantage.co"

# Global default for non-geographic source
_GLOBAL_GEO = GeoPoint(lat=0.0, lon=0.0, radius_m=20000000)


class AlphaVantageCollector(BaseCollector):
    """Alpha Vantage API collector — stock market time series.

    Auth: API key as query parameter (apikey).
    API key from ECHELON_ALPHA_VANTAGE_API_KEY env var.
    """

    def __init__(self, api_key: str | None = None, base_url: str | None = None) -> None:
        self._api_key = api_key or os.environ.get("ECHELON_ALPHA_VANTAGE_API_KEY", "")
        self._base_url = base_url or BASE_URL

    def source_id(self) -> str:
        return "alpha_vantage_api"

    async def _fetch(self, request: dict, theatre_id: str) -> CollectionResult:
        """GET TIME_SERIES_DAILY with apikey query param."""
        now = datetime.utcnow()

        if not self._api_key:
            return CollectionResult(
                source_id=self.source_id(),
                bundle=None,
                raw_payload=b"",
                fetch_duration_ms=0.0,
                success=False,
                error="No API key configured (ECHELON_ALPHA_VANTAGE_API_KEY)",
                retrieved_at=now,
            )

        symbol = request.get("symbol", "")
        if not symbol:
            return CollectionResult(
                source_id=self.source_id(),
                bundle=None,
                raw_payload=b"",
                fetch_duration_ms=0.0,
                success=False,
                error="No symbol in request",
                retrieved_at=now,
            )

        query = f"function=TIME_SERIES_DAILY&symbol={symbol}&apikey={self._api_key}&outputsize=compact"
        url = f"{self._base_url}/query?{query}"
        safe_query = f"function=TIME_SERIES_DAILY&symbol={symbol}&outputsize=compact"
        safe_url = f"{self._base_url}/query?{safe_query}"
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
                symbol=symbol,
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
        """Execute HTTP GET in a thread pool."""
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
        symbol: str,
    ) -> CollectionResult:
        """Parse Alpha Vantage response and build EvidenceBundle."""
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

        # Check for rate limit / error response
        if "Note" in data or "Information" in data:
            msg = data.get("Note", data.get("Information", "Rate limited"))
            return CollectionResult(
                source_id=self.source_id(),
                bundle=None,
                raw_payload=raw_payload,
                fetch_duration_ms=duration_ms,
                success=False,
                error=f"API limit: {msg}",
                retrieved_at=now,
            )

        ts_key = "Time Series (Daily)"
        time_series = data.get(ts_key, {})
        if not time_series:
            return CollectionResult(
                source_id=self.source_id(),
                bundle=None,
                raw_payload=raw_payload,
                fetch_duration_ms=duration_ms,
                success=False,
                error=f"No time series data for symbol '{symbol}'",
                retrieved_at=now,
            )

        latest_date = next(iter(time_series))
        latest = time_series[latest_date]
        close_price = float(latest.get("4. close", 0.0))

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
            value=close_price,
            unit="USD",
            metadata={"symbol": symbol, "date": latest_date},
        )

        event = NormalisedEvent(
            event_id=f"evt_av_{symbol}_{int(now.timestamp())}",
            geo=_GLOBAL_GEO,
            measure=measure,
            confidence=0.95,
            timestamp=now,
        )

        bundle = EvidenceBundle(
            bundle_id=f"eb_av_{symbol}_{int(now.timestamp())}",
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
        """Fetch IBM daily as health probe."""
        if not self._api_key:
            return HealthStatus.UNAVAILABLE
        try:
            query = f"function=TIME_SERIES_DAILY&symbol=IBM&apikey={self._api_key}&outputsize=compact"
            url = f"{self._base_url}/query?{query}"
            await self._do_http_get(url)
            return HealthStatus.HEALTHY
        except Exception:
            return HealthStatus.UNAVAILABLE
