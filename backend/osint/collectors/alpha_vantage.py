"""Alpha Vantage collector — scaffold.

Implements BaseCollector for the Alpha Vantage API.
Auth: API key via query parameter.
Endpoint: GET with function=TIME_SERIES_DAILY

API key from ECHELON_ALPHA_VANTAGE_API_KEY env var.
"""
from __future__ import annotations

import os

from backend.osint.collectors.base import BaseCollector
from backend.osint.models.evidence import CollectionResult, HealthStatus


class AlphaVantageCollector(BaseCollector):
    """Alpha Vantage API collector — stock market time series.

    Auth: API key as query parameter (apikey).
    API key from ECHELON_ALPHA_VANTAGE_API_KEY env var.
    """

    def __init__(self, api_key: str | None = None) -> None:
        self._api_key = api_key or os.environ.get("ECHELON_ALPHA_VANTAGE_API_KEY", "")

    def source_id(self) -> str:
        return "alpha_vantage_api"

    async def _fetch(self, request: dict, theatre_id: str) -> CollectionResult:
        """GET TIME_SERIES_DAILY — placeholder."""
        raise NotImplementedError("AlphaVantageCollector._fetch() not yet implemented")

    async def health_check(self) -> HealthStatus:
        return HealthStatus.UNAVAILABLE
