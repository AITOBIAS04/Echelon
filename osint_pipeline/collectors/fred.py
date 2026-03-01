"""FRED (Federal Reserve Economic Data) collector.

Queries the FRED API for US economic indicators.
Authentication via API key (free registration required).

Registry source_id: fred_api
Registry upstream: us_stlouisfed_fred_backend
"""

from __future__ import annotations

import json
from typing import Any

from osint_pipeline.collectors.base import BaseCollector
from osint_pipeline.models.evidence import FreshnessState


class FREDCollector(BaseCollector):
    """FRED API collector for US economic data.

    Config keys:
        - ``api_key``: Required. FRED API key from https://fred.stlouisfed.org/docs/api/api_key.html
    """

    BASE_URL = "https://api.stlouisfed.org/fred/series/observations"

    @property
    def source_id(self) -> str:
        return "fred_api"

    @property
    def source_group(self) -> str:
        return "market_data"

    @property
    def independence_upstream_id(self) -> str:
        return "us_stlouisfed_fred_backend"

    @property
    def resolution_role(self) -> str:
        return "secondary_corroboration"

    @property
    def jurisdiction(self) -> str:
        return "US"

    def __init__(self, config: dict[str, Any] | None = None):
        super().__init__(config)
        api_key = self.config.get("api_key", "")
        if not api_key:
            raise ValueError(
                "FRED requires an API key. "
                "Set config['api_key'] from https://fred.stlouisfed.org"
            )

    def build_request(
        self, query_context: dict[str, Any]
    ) -> tuple[str, str, dict[str, str], dict[str, Any] | None]:
        """Build FRED API request.

        query_context keys:
            - ``series_id``: FRED series identifier, e.g. ``"GDP"`` (required).
            - ``observation_start``: Start date ``YYYY-MM-DD`` (optional).
            - ``observation_end``: End date ``YYYY-MM-DD`` (optional).
            - ``sort_order``: ``"asc"`` or ``"desc"`` (optional, default ``"desc"``).
            - ``limit``: Max observations (optional, default 10).
        """
        series_id = query_context.get("series_id", "")
        if not series_id:
            raise ValueError("query_context must include 'series_id'")

        params: dict[str, Any] = {
            "series_id": series_id,
            "api_key": self.config["api_key"],
            "file_type": "json",
            "sort_order": query_context.get("sort_order", "desc"),
            "limit": query_context.get("limit", 10),
        }

        obs_start = query_context.get("observation_start")
        if obs_start:
            params["observation_start"] = obs_start

        obs_end = query_context.get("observation_end")
        if obs_end:
            params["observation_end"] = obs_end

        headers = {"Accept": "application/json"}
        return "GET", self.BASE_URL, headers, params

    def extract(
        self,
        raw_body: bytes,
        status_code: int,
        query_context: dict[str, Any],
    ) -> tuple[dict[str, Any], float]:
        """Parse FRED API response."""
        if status_code != 200:
            return {"error": f"HTTP {status_code}"}, 0.0

        try:
            data = json.loads(raw_body)
        except (json.JSONDecodeError, ValueError):
            return {"error": "Invalid JSON response"}, 0.0

        observations = data.get("observations", [])
        count = int(data.get("count", len(observations)))

        parsed = []
        for obs in observations[:20]:
            parsed.append({
                "date": obs.get("date"),
                "value": obs.get("value"),
                "realtime_start": obs.get("realtime_start"),
                "realtime_end": obs.get("realtime_end"),
            })

        extract = {
            "series_id": query_context.get("series_id", ""),
            "total_observations": count,
            "observations": parsed,
        }

        confidence = 1.0 if count > 0 else 0.5
        return extract, confidence

    def assess_freshness(
        self, structured_extract: dict[str, Any], retrieved_at: Any
    ) -> FreshnessState:
        if structured_extract.get("error"):
            return FreshnessState.ERROR
        if structured_extract.get("total_observations", 0) == 0:
            return FreshnessState.NO_DATA
        return FreshnessState.FRESH
