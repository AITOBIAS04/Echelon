"""Calendarific collector — scaffold.

Implements BaseCollector for the Calendarific API.
Auth: API key via query parameter.
Endpoint: GET /holidays

API key from ECHELON_CALENDARIFIC_API_KEY env var.
"""
from __future__ import annotations

import os

from backend.osint.collectors.base import BaseCollector
from backend.osint.models.evidence import CollectionResult, HealthStatus


class CalendarificCollector(BaseCollector):
    """Calendarific API collector — global holiday calendar.

    Auth: API key as query parameter (api_key).
    API key from ECHELON_CALENDARIFIC_API_KEY env var.
    Resolution role: counter_signal.
    """

    def __init__(self, api_key: str | None = None) -> None:
        self._api_key = api_key or os.environ.get("ECHELON_CALENDARIFIC_API_KEY", "")

    def source_id(self) -> str:
        return "calendarific_api"

    async def _fetch(self, request: dict, theatre_id: str) -> CollectionResult:
        """GET /holidays — placeholder."""
        raise NotImplementedError("CalendarificCollector._fetch() not yet implemented")

    async def health_check(self) -> HealthStatus:
        return HealthStatus.UNAVAILABLE
