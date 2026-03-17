"""FRED (Federal Reserve Economic Data) collector — scaffold.

Implements BaseCollector for the FRED API.
Auth: API key via query parameter.
Endpoint: GET /fred/series/observations

API key from ECHELON_FRED_API_KEY env var.
"""
from __future__ import annotations

import os

from backend.osint.collectors.base import BaseCollector
from backend.osint.models.evidence import CollectionResult, HealthStatus


class FREDCollector(BaseCollector):
    """FRED API collector — economic time series data.

    Auth: API key as query parameter.
    API key from ECHELON_FRED_API_KEY env var.
    """

    def __init__(self, api_key: str | None = None) -> None:
        self._api_key = api_key or os.environ.get("ECHELON_FRED_API_KEY", "")

    def source_id(self) -> str:
        return "fred_api"

    async def _fetch(self, request: dict, theatre_id: str) -> CollectionResult:
        """GET /fred/series/observations — placeholder."""
        raise NotImplementedError("FREDCollector._fetch() not yet implemented")

    async def health_check(self) -> HealthStatus:
        return HealthStatus.UNAVAILABLE
