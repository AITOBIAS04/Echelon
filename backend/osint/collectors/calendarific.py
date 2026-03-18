"""Calendarific collector.

Implements BaseCollector for the Calendarific API.
Auth: API key via query parameter (api_key).
Endpoint: GET /api/v2/holidays

API key from ECHELON_CALENDARIFIC_API_KEY env var.
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

BASE_URL = "https://calendarific.com/api/v2"

_GLOBAL_GEO = GeoPoint(lat=0.0, lon=0.0, radius_m=20000000)


class CalendarificCollector(BaseCollector):
    """Calendarific API collector — global holiday calendar.

    Auth: API key as query parameter (api_key).
    API key from ECHELON_CALENDARIFIC_API_KEY env var.
    Resolution role: counter_signal.
    """

    def __init__(self, api_key: str | None = None, base_url: str | None = None) -> None:
        self._api_key = api_key or os.environ.get("ECHELON_CALENDARIFIC_API_KEY", "")
        self._base_url = base_url or BASE_URL

    def source_id(self) -> str:
        return "calendarific_api"

    async def _fetch(self, request: dict, theatre_id: str) -> CollectionResult:
        """GET /holidays with api_key, country, year params."""
        now = datetime.utcnow()

        if not self._api_key:
            return CollectionResult(
                source_id=self.source_id(),
                bundle=None,
                raw_payload=b"",
                fetch_duration_ms=0.0,
                success=False,
                error="No API key configured (ECHELON_CALENDARIFIC_API_KEY)",
                retrieved_at=now,
            )

        country = request.get("country", "US")
        year = request.get("year", str(now.year))
        month = request.get("month", "")
        day = request.get("day", "")

        query_parts = [f"api_key={self._api_key}", f"country={country}", f"year={year}"]
        if month:
            query_parts.append(f"month={month}")
        if day:
            query_parts.append(f"day={day}")
        query = "&".join(query_parts)
        url = f"{self._base_url}/holidays?{query}"

        # Redacted query for receipt
        safe_parts = [f"country={country}", f"year={year}"]
        if month:
            safe_parts.append(f"month={month}")
        if day:
            safe_parts.append(f"day={day}")
        safe_query = "&".join(safe_parts)
        safe_url = f"{self._base_url}/holidays?{safe_query}"
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
                country=country,
                year=year,
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
        country: str,
        year: str,
    ) -> CollectionResult:
        """Parse Calendarific response and build EvidenceBundle."""
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

        response = data.get("response", {})
        holidays = response.get("holidays", [])
        holiday_count = len(holidays)

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
            source_version="v2",
            http_status=200,
            content_hash=content_hash,
            receipt_hash=receipt_hash,
        )

        measure = NormalisedMeasure(
            type=MeasureType.SECTOR_RISK_SCORE,
            value=float(holiday_count),
            unit="holiday_count",
            metadata={
                "country": country,
                "year": year,
                "holidays": [h.get("name", "") for h in holidays[:5]],
            },
        )

        event = NormalisedEvent(
            event_id=f"evt_cal_{country}_{year}_{int(now.timestamp())}",
            geo=_GLOBAL_GEO,
            measure=measure,
            confidence=1.0,
            timestamp=now,
        )

        bundle = EvidenceBundle(
            bundle_id=f"eb_cal_{country}_{year}_{int(now.timestamp())}",
            source_id=self.source_id(),
            source_group="calendar_counter_signal",
            resolution_role="counter_signal",
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
        """Fetch US holidays for current year as health probe."""
        if not self._api_key:
            return HealthStatus.UNAVAILABLE
        try:
            year = datetime.utcnow().year
            url = f"{self._base_url}/holidays?api_key={self._api_key}&country=US&year={year}"
            await self._do_http_get(url)
            return HealthStatus.HEALTHY
        except Exception:
            return HealthStatus.UNAVAILABLE
