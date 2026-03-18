"""Etherscan collector.

Implements BaseCollector for the Etherscan API.
Auth: API key via query parameter (apikey).
Endpoint: GET with module=account, action=balance

API key from ECHELON_ETHERSCAN_API_KEY env var.
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

BASE_URL = "https://api.etherscan.io/api"

_GLOBAL_GEO = GeoPoint(lat=0.0, lon=0.0, radius_m=20000000)


class EtherscanCollector(BaseCollector):
    """Etherscan API collector — Ethereum on-chain data.

    Auth: API key as query parameter (apikey).
    API key from ECHELON_ETHERSCAN_API_KEY env var.
    """

    def __init__(self, api_key: str | None = None, base_url: str | None = None) -> None:
        self._api_key = api_key or os.environ.get("ECHELON_ETHERSCAN_API_KEY", "")
        self._base_url = base_url or BASE_URL

    def source_id(self) -> str:
        return "etherscan_api"

    async def _fetch(self, request: dict, theatre_id: str) -> CollectionResult:
        """GET module=account&action=balance with apikey query param."""
        now = datetime.utcnow()

        if not self._api_key:
            return CollectionResult(
                source_id=self.source_id(),
                bundle=None,
                raw_payload=b"",
                fetch_duration_ms=0.0,
                success=False,
                error="No API key configured (ECHELON_ETHERSCAN_API_KEY)",
                retrieved_at=now,
            )

        address = request.get("address", "")
        if not address:
            return CollectionResult(
                source_id=self.source_id(),
                bundle=None,
                raw_payload=b"",
                fetch_duration_ms=0.0,
                success=False,
                error="No address in request",
                retrieved_at=now,
            )

        action = request.get("action", "balance")
        query = f"module=account&action={action}&address={address}&tag=latest&apikey={self._api_key}"
        url = f"{self._base_url}?{query}"
        safe_query = f"module=account&action={action}&address={address}&tag=latest"
        safe_url = f"{self._base_url}?{safe_query}"
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
                address=address,
                action=action,
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
        address: str,
        action: str,
    ) -> CollectionResult:
        """Parse Etherscan response and build EvidenceBundle."""
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

        status = data.get("status", "0")
        result = data.get("result", "")
        message = data.get("message", "")

        if status != "1" and message != "OK":
            return CollectionResult(
                source_id=self.source_id(),
                bundle=None,
                raw_payload=raw_payload,
                fetch_duration_ms=duration_ms,
                success=False,
                error=f"Etherscan error: {message} — {result}",
                retrieved_at=now,
            )

        # Balance is returned in wei
        if action == "balance":
            value = float(result) / 1e18  # Convert wei to ETH
        else:
            value = float(len(result)) if isinstance(result, list) else 0.0

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
            unit="ETH" if action == "balance" else "tx_count",
            metadata={"address": address, "action": action},
        )

        event = NormalisedEvent(
            event_id=f"evt_eth_{address[:10]}_{int(now.timestamp())}",
            geo=_GLOBAL_GEO,
            measure=measure,
            confidence=1.0,
            timestamp=now,
        )

        bundle = EvidenceBundle(
            bundle_id=f"eb_eth_{address[:10]}_{int(now.timestamp())}",
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
        """Check Ethereum genesis address balance as health probe."""
        if not self._api_key:
            return HealthStatus.UNAVAILABLE
        try:
            url = f"{self._base_url}?module=account&action=balance&address=0x0000000000000000000000000000000000000000&tag=latest&apikey={self._api_key}"
            await self._do_http_get(url)
            return HealthStatus.HEALTHY
        except Exception:
            return HealthStatus.UNAVAILABLE
