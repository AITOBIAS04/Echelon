"""OpenSky Network collector — scaffold.

Implements BaseCollector for the OpenSky Network API.
Auth: None required (public API).
Endpoint: GET /states/all with bounding box

No auth required.
"""
from __future__ import annotations

from backend.osint.collectors.base import BaseCollector
from backend.osint.models.evidence import CollectionResult, HealthStatus


class OpenSkyCollector(BaseCollector):
    """OpenSky Network API collector — live flight tracking.

    No auth required. Public API with rate limiting (~100 req/day).
    """

    def source_id(self) -> str:
        return "opensky_api"

    async def _fetch(self, request: dict, theatre_id: str) -> CollectionResult:
        """GET /states/all — placeholder."""
        raise NotImplementedError("OpenSkyCollector._fetch() not yet implemented")

    async def health_check(self) -> HealthStatus:
        return HealthStatus.UNAVAILABLE
