"""OpenCorporates collector — scaffold.

Implements BaseCollector for the OpenCorporates API v0.4.
Auth: API token via query parameter.
Endpoint: GET /companies/search

API key from ECHELON_OPENCORPORATES_API_KEY env var.
"""
from __future__ import annotations

import os

from backend.osint.collectors.base import BaseCollector
from backend.osint.models.evidence import CollectionResult, HealthStatus


class OpenCorporatesCollector(BaseCollector):
    """OpenCorporates API collector — global company search.

    Auth: API token as query parameter (api_token).
    API key from ECHELON_OPENCORPORATES_API_KEY env var.
    """

    def __init__(self, api_key: str | None = None) -> None:
        self._api_key = api_key or os.environ.get("ECHELON_OPENCORPORATES_API_KEY", "")

    def source_id(self) -> str:
        return "opencorporates_api"

    async def _fetch(self, request: dict, theatre_id: str) -> CollectionResult:
        """GET /companies/search — placeholder."""
        raise NotImplementedError("OpenCorporatesCollector._fetch() not yet implemented")

    async def health_check(self) -> HealthStatus:
        return HealthStatus.UNAVAILABLE
