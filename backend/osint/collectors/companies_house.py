"""Companies House API collector — UK company profile lookup.

Implements BaseCollector for the Companies House REST API.
Auth: HTTP Basic (API key as username, blank password).
Single endpoint: GET /company/{company_number}.

API key from ECHELON_COMPANIES_HOUSE_API_KEY env var.
No key → CollectionResult(success=False), does NOT raise.

Uses stdlib urllib.request (same pattern as WorldMonitor collector).
"""
from __future__ import annotations

import asyncio
import base64
import hashlib
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

BASE_URL = "https://api.company-information.service.gov.uk"


class CompaniesHouseCollector(BaseCollector):
    """UK Companies House API collector — profile lookup only.

    Auth: HTTP Basic (API key as username, blank password).
    API key from ECHELON_COMPANIES_HOUSE_API_KEY env var.
    """

    def __init__(self, api_key: str | None = None, base_url: str | None = None) -> None:
        self._api_key = api_key or os.environ.get("ECHELON_COMPANIES_HOUSE_API_KEY", "")
        self._base_url = base_url or BASE_URL

    def source_id(self) -> str:
        return "companies_house_api"

    async def _fetch(self, request: dict, theatre_id: str) -> CollectionResult:
        """GET /company/{company_number} with Basic auth."""
        now = datetime.utcnow()

        if not self._api_key:
            return CollectionResult(
                source_id=self.source_id(),
                bundle=None,
                raw_payload=b"",
                fetch_duration_ms=0.0,
                success=False,
                error="No API key configured",
                retrieved_at=now,
            )

        company_number = request.get("company_number", "")
        if not company_number:
            return CollectionResult(
                source_id=self.source_id(),
                bundle=None,
                raw_payload=b"",
                fetch_duration_ms=0.0,
                success=False,
                error="No company_number in request",
                retrieved_at=now,
            )

        url = f"{self._base_url}/company/{company_number}"
        start_ms = time.monotonic() * 1000

        try:
            raw_payload = await self._do_http_get(url)
            duration_ms = time.monotonic() * 1000 - start_ms
            return self._build_success_result(
                raw_payload=raw_payload,
                url=url,
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
        except Exception as exc:
            duration_ms = time.monotonic() * 1000 - start_ms
            return CollectionResult(
                source_id=self.source_id(),
                bundle=None,
                raw_payload=b"",
                fetch_duration_ms=duration_ms,
                success=False,
                error=f"Unexpected error: {exc}",
                retrieved_at=now,
            )

    async def _do_http_get(self, url: str) -> bytes:
        """Execute HTTP GET with Basic auth in a thread pool."""
        loop = asyncio.get_event_loop()
        api_key = self._api_key

        def _sync_get() -> bytes:
            credentials = base64.b64encode(f"{api_key}:".encode()).decode()
            req = urllib.request.Request(
                url,
                headers={
                    "Authorization": f"Basic {credentials}",
                    "Accept": "application/json",
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
        theatre_id: str,
        duration_ms: float,
    ) -> CollectionResult:
        """Parse response and build EvidenceBundle + receipt."""
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

        content_hash = compute_content_hash(raw_payload)
        headers_str = "accept:application/json"
        receipt_hash = compute_receipt_hash(
            method="GET",
            url=url,
            query="",
            headers=headers_str,
            body_hash=content_hash,
        )

        receipt = HTTPTranscriptReceipt(
            timestamp=now,
            request_parameters={
                "method": "GET",
                "url": url,
                "query": "",
                "headers": headers_str,
            },
            source_id=self.source_id(),
            source_version="v1.0",
            http_status=200,
            content_hash=content_hash,
            receipt_hash=receipt_hash,
        )

        bundle = self._build_bundle(data, receipt, now, content_hash)

        return CollectionResult(
            source_id=self.source_id(),
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
        """Construct EvidenceBundle from Companies House response."""
        company_number = data.get("company_number", "unknown")
        company_status = data.get("company_status", "unknown")

        # Use registered office address for geo if available
        address = data.get("registered_office_address", {})
        geo = GeoPoint(lat=51.5074, lon=-0.1278, radius_m=50000)  # Default: London

        measure = NormalisedMeasure(
            type=MeasureType.COUNTRY_INSTABILITY_INDEX,  # Closest available type
            value=1.0 if company_status == "active" else 0.0,
            unit="binary",
            metadata={"company_status": company_status},
        )

        event = NormalisedEvent(
            event_id=f"evt_ch_{company_number}_{int(timestamp.timestamp())}",
            geo=geo,
            measure=measure,
            confidence=1.0,  # Official government source
            timestamp=timestamp,
        )

        return EvidenceBundle(
            bundle_id=f"eb_ch_{company_number}_{int(timestamp.timestamp())}",
            source_id=self.source_id(),
            source_group="official_gov",
            resolution_role="primary_evidence",
            evidence_timestamp=timestamp,
            raw_payload_hash=content_hash,
            receipt=receipt,
            normalised_event=event,
        )

    async def health_check(self) -> HealthStatus:
        """GET /company/00000006 (test company) as health probe."""
        if not self._api_key:
            return HealthStatus.UNAVAILABLE

        try:
            url = f"{self._base_url}/company/00000006"
            await self._do_http_get(url)
            return HealthStatus.HEALTHY
        except Exception:
            return HealthStatus.UNAVAILABLE
