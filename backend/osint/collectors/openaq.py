"""OpenAQ collector — scaffold.

Implements BaseCollector for the OpenAQ API v2.
Auth: X-API-Key header.
Endpoint: GET /v2/measurements

API key from ECHELON_OPENAQ_API_KEY env var.
"""
from __future__ import annotations

import os

from backend.osint.collectors.base import BaseCollector
from backend.osint.models.evidence import CollectionResult, HealthStatus


class OpenAQCollector(BaseCollector):
    """OpenAQ API collector — global air quality measurements.

    Auth: API key via X-API-Key header.
    API key from ECHELON_OPENAQ_API_KEY env var.
    """

    def __init__(self, api_key: str | None = None) -> None:
        self._api_key = api_key or os.environ.get("ECHELON_OPENAQ_API_KEY", "")

    def source_id(self) -> str:
        return "openaq_api"

    async def _fetch(self, request: dict, theatre_id: str) -> CollectionResult:
        """GET /v2/measurements — placeholder."""
        raise NotImplementedError("OpenAQCollector._fetch() not yet implemented")

    async def health_check(self) -> HealthStatus:
        return HealthStatus.UNAVAILABLE
