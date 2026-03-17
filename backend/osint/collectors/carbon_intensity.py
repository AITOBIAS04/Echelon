"""UK Carbon Intensity collector — scaffold.

Implements BaseCollector for the Carbon Intensity API.
Auth: None required (public API).
Endpoint: GET /intensity/{from}/{to}

No auth required.
"""
from __future__ import annotations

from backend.osint.collectors.base import BaseCollector
from backend.osint.models.evidence import CollectionResult, HealthStatus


class CarbonIntensityCollector(BaseCollector):
    """UK Carbon Intensity API collector — grid carbon intensity data.

    No auth required. Operated by National Grid ESO.
    """

    def source_id(self) -> str:
        return "carbon_intensity_api"

    async def _fetch(self, request: dict, theatre_id: str) -> CollectionResult:
        """GET /intensity/{from}/{to} — placeholder."""
        raise NotImplementedError("CarbonIntensityCollector._fetch() not yet implemented")

    async def health_check(self) -> HealthStatus:
        return HealthStatus.UNAVAILABLE
