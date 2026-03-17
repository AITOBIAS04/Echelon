"""CoinGecko collector — scaffold.

Implements BaseCollector for the CoinGecko API.
Auth: None required (public API).
Endpoint: GET /simple/price

No auth required.
"""
from __future__ import annotations

from backend.osint.collectors.base import BaseCollector
from backend.osint.models.evidence import CollectionResult, HealthStatus


class CoinGeckoCollector(BaseCollector):
    """CoinGecko API collector — cryptocurrency price data.

    No auth required. Public API with rate limiting.
    """

    def source_id(self) -> str:
        return "coingecko_api"

    async def _fetch(self, request: dict, theatre_id: str) -> CollectionResult:
        """GET /simple/price — placeholder."""
        raise NotImplementedError("CoinGeckoCollector._fetch() not yet implemented")

    async def health_check(self) -> HealthStatus:
        return HealthStatus.UNAVAILABLE
