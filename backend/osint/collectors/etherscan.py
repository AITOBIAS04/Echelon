"""Etherscan collector — scaffold.

Implements BaseCollector for the Etherscan API.
Auth: API key via query parameter.
Endpoint: GET with module=account, action=txlist or action=balance

API key from ECHELON_ETHERSCAN_API_KEY env var.
"""
from __future__ import annotations

import os

from backend.osint.collectors.base import BaseCollector
from backend.osint.models.evidence import CollectionResult, HealthStatus


class EtherscanCollector(BaseCollector):
    """Etherscan API collector — Ethereum on-chain data.

    Auth: API key as query parameter (apikey).
    API key from ECHELON_ETHERSCAN_API_KEY env var.
    """

    def __init__(self, api_key: str | None = None) -> None:
        self._api_key = api_key or os.environ.get("ECHELON_ETHERSCAN_API_KEY", "")

    def source_id(self) -> str:
        return "etherscan_api"

    async def _fetch(self, request: dict, theatre_id: str) -> CollectionResult:
        """GET module=account — placeholder."""
        raise NotImplementedError("EtherscanCollector._fetch() not yet implemented")

    async def health_check(self) -> HealthStatus:
        return HealthStatus.UNAVAILABLE
