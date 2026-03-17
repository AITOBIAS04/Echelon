"""USGS Earthquake Hazards collector — scaffold.

Implements BaseCollector for the USGS Earthquake API.
Auth: None required (public API).
Endpoint: GET /query with format=geojson

No auth required.
"""
from __future__ import annotations

from backend.osint.collectors.base import BaseCollector
from backend.osint.models.evidence import CollectionResult, HealthStatus


class USGSEarthquakeCollector(BaseCollector):
    """USGS Earthquake Hazards API collector — seismic event data.

    No auth required. GeoJSON format responses.
    """

    def source_id(self) -> str:
        return "usgs_earthquake_api"

    async def _fetch(self, request: dict, theatre_id: str) -> CollectionResult:
        """GET /query format=geojson — placeholder."""
        raise NotImplementedError("USGSEarthquakeCollector._fetch() not yet implemented")

    async def health_check(self) -> HealthStatus:
        return HealthStatus.UNAVAILABLE
