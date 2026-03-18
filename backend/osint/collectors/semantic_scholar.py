"""Semantic Scholar collector.

Implements BaseCollector for the Semantic Scholar Academic Graph API.
Auth: API key via x-api-key header (optional — unauthenticated requests are rate-limited).
Endpoint: GET /paper/{paper_id} (Graph API v1)

API key from ECHELON_SEMANTIC_SCHOLAR_API_KEY env var.
No key -> still works (lower rate limit), but logs advisory.
"""
from __future__ import annotations

import asyncio
import json
import os
import time
import urllib.error
import urllib.request
from datetime import datetime
from typing import Optional

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

BASE_URL = "https://api.semanticscholar.org/graph/v1"

# Requested fields — enough for citation-based evidence without bulk download.
_FIELDS = "title,year,citationCount,influentialCitationCount,tldr,authors"

# Global default for non-geographic source
_GLOBAL_GEO = GeoPoint(lat=0.0, lon=0.0, radius_m=20000000)


class SemanticScholarCollector(BaseCollector):
    """Semantic Scholar Academic Graph API collector — paper metadata + citations.

    Auth: x-api-key header (optional). API key from ECHELON_SEMANTIC_SCHOLAR_API_KEY env var.
    Unauthenticated requests work but with lower rate limits (~100 req/5min).
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ) -> None:
        self._api_key = api_key or os.environ.get("ECHELON_SEMANTIC_SCHOLAR_API_KEY", "")
        self._base_url = base_url or BASE_URL

    def source_id(self) -> str:
        return "semantic_scholar_api"

    async def _fetch(self, request: dict, theatre_id: str) -> CollectionResult:
        """GET /paper/{paper_id}?fields=..."""
        now = datetime.utcnow()

        paper_id = request.get("paper_id", "")
        if not paper_id:
            return CollectionResult(
                source_id=self.source_id(),
                bundle=None,
                raw_payload=b"",
                fetch_duration_ms=0.0,
                success=False,
                error="No paper_id in request",
                retrieved_at=now,
            )

        query = f"fields={_FIELDS}"
        url = f"{self._base_url}/paper/{paper_id}?{query}"
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
                paper_id=paper_id,
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
        api_key = self._api_key

        def _sync_get() -> bytes:
            headers = {"Accept": "application/json"}
            if api_key:
                headers["x-api-key"] = api_key
            req = urllib.request.Request(url, headers=headers, method="GET")
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
        paper_id: str,
    ) -> CollectionResult:
        """Parse Semantic Scholar response and build EvidenceBundle."""
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

        # Semantic Scholar returns {"error": "..."} on lookup failure
        if "error" in data:
            return CollectionResult(
                source_id=self.source_id(),
                bundle=None,
                raw_payload=raw_payload,
                fetch_duration_ms=duration_ms,
                success=False,
                error=f"API error: {data['error']}",
                retrieved_at=now,
            )

        title = data.get("title", "")
        citation_count = data.get("citationCount", 0)
        influential_count = data.get("influentialCitationCount", 0)

        content_hash = compute_content_hash(raw_payload)

        # Redact API key from headers for receipt provenance
        safe_headers = "accept:application/json"
        receipt_hash = compute_receipt_hash(
            method="GET",
            url=url,
            query=query,
            headers=safe_headers,
            body_hash=content_hash,
        )

        receipt = HTTPTranscriptReceipt(
            timestamp=now,
            request_parameters={
                "method": "GET",
                "url": url,
                "query": query,
                "headers": safe_headers,
            },
            source_id=self.source_id(),
            source_version="v1.0",
            http_status=200,
            content_hash=content_hash,
            receipt_hash=receipt_hash,
        )

        measure = NormalisedMeasure(
            type=MeasureType.SECTOR_RISK_SCORE,
            value=float(citation_count),
            unit="citations",
            metadata={
                "paper_id": paper_id,
                "title": title,
                "influential_citations": influential_count,
            },
        )

        event = NormalisedEvent(
            event_id=f"evt_ss_{paper_id}_{int(now.timestamp())}",
            geo=_GLOBAL_GEO,
            measure=measure,
            confidence=0.90,
            timestamp=now,
        )

        bundle = EvidenceBundle(
            bundle_id=f"eb_ss_{paper_id}_{int(now.timestamp())}",
            source_id=self.source_id(),
            source_group="research_evidence",
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
        """Fetch a well-known paper (Attention Is All You Need) as health probe."""
        try:
            url = f"{self._base_url}/paper/204e3073870fae3d05bcbc2f6a8e263d9b72e776?fields=title"
            await self._do_http_get(url)
            return HealthStatus.HEALTHY
        except Exception:
            return HealthStatus.UNAVAILABLE
