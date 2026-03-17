"""CoinGecko collector.

Implements BaseCollector for the CoinGecko API.
Auth: None required (public API).
Endpoint: GET /api/v3/simple/price

No auth required. Rate limited to 10-50 req/min.
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

BASE_URL = "https://api.coingecko.com/api/v3"

_GLOBAL_GEO = GeoPoint(lat=0.0, lon=0.0, radius_m=20000000)


class CoinGeckoCollector(BaseCollector):
    """CoinGecko API collector — cryptocurrency price data.

    No auth required. Public API with rate limiting.
    """

    def __init__(self, base_url: str | None = None) -> None:
        self._base_url = base_url or BASE_URL

    def source_id(self) -> str:
        return "coingecko_api"

    async def _fetch(self, request: dict, theatre_id: str) -> CollectionResult:
        """GET /simple/price with ids and vs_currencies params."""
        now = datetime.utcnow()

        coin_id = request.get("coin_id", request.get("ids", "bitcoin"))
        vs_currency = request.get("vs_currency", request.get("vs_currencies", "usd"))

        query = f"ids={coin_id}&vs_currencies={vs_currency}"
        url = f"{self._base_url}/simple/price?{query}"
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
                coin_id=coin_id,
                vs_currency=vs_currency,
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
        coin_id: str,
        vs_currency: str,
    ) -> CollectionResult:
        """Parse CoinGecko response and build EvidenceBundle."""
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

        coin_data = data.get(coin_id, {})
        if not coin_data:
            return CollectionResult(
                source_id=self.source_id(),
                bundle=None,
                raw_payload=raw_payload,
                fetch_duration_ms=duration_ms,
                success=False,
                error=f"No data for coin_id '{coin_id}'",
                retrieved_at=now,
            )

        price = float(coin_data.get(vs_currency, 0.0))

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
            source_version="v3",
            http_status=200,
            content_hash=content_hash,
            receipt_hash=receipt_hash,
        )

        measure = NormalisedMeasure(
            type=MeasureType.SECTOR_RISK_SCORE,
            value=price,
            unit=vs_currency.upper(),
            metadata={"coin_id": coin_id, "vs_currency": vs_currency},
        )

        event = NormalisedEvent(
            event_id=f"evt_cg_{coin_id}_{int(now.timestamp())}",
            geo=_GLOBAL_GEO,
            measure=measure,
            confidence=0.9,
            timestamp=now,
        )

        bundle = EvidenceBundle(
            bundle_id=f"eb_cg_{coin_id}_{int(now.timestamp())}",
            source_id=self.source_id(),
            source_group="blockchain_data",
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
        """Fetch bitcoin price as health probe."""
        try:
            url = f"{self._base_url}/simple/price?ids=bitcoin&vs_currencies=usd"
            await self._do_http_get(url)
            return HealthStatus.HEALTHY
        except Exception:
            return HealthStatus.UNAVAILABLE
