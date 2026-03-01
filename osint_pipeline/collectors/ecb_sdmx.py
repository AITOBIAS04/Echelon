"""ECB Statistical Data Warehouse collector.

Queries the ECB Data API (JSON format) for euro area economic data.
No authentication required.

Registry source_id: ecb_data_api
Registry upstream: eu_ecb_sdw_backend
"""

from __future__ import annotations

import json
from typing import Any

from osint_pipeline.collectors.base import BaseCollector
from osint_pipeline.models.evidence import FreshnessState


class ECBDataCollector(BaseCollector):
    """ECB Data API collector.

    Uses the JSON format endpoint at ``data-api.ecb.europa.eu``.
    No authentication required.

    Config keys:
        - ``format``: Response format (default ``"jsondata"``).
    """

    BASE_URL = "https://data-api.ecb.europa.eu/service/data"

    @property
    def source_id(self) -> str:
        return "ecb_data_api"

    @property
    def source_group(self) -> str:
        return "market_data"

    @property
    def independence_upstream_id(self) -> str:
        return "eu_ecb_sdw_backend"

    @property
    def resolution_role(self) -> str:
        return "primary_evidence"

    @property
    def jurisdiction(self) -> str:
        return "EU"

    def build_request(
        self, query_context: dict[str, Any]
    ) -> tuple[str, str, dict[str, str], dict[str, Any] | None]:
        """Build ECB Data API request.

        query_context keys:
            - ``dataflow``: ECB dataflow identifier, e.g. ``"EXR"`` (required).
            - ``series_key``: SDMX series key, e.g. ``"D.USD.EUR.SP00.A"`` (required).
            - ``start_period``: Start date ``YYYY-MM-DD`` (optional).
            - ``end_period``: End date ``YYYY-MM-DD`` (optional).
        """
        dataflow = query_context.get("dataflow", "")
        series_key = query_context.get("series_key", "")
        if not dataflow or not series_key:
            raise ValueError(
                "query_context must include 'dataflow' and 'series_key'"
            )

        url = f"{self.BASE_URL}/{dataflow}/{series_key}"

        fmt = self.config.get("format", "jsondata")
        params: dict[str, Any] = {"format": fmt}

        start_period = query_context.get("start_period")
        if start_period:
            params["startPeriod"] = start_period

        end_period = query_context.get("end_period")
        if end_period:
            params["endPeriod"] = end_period

        headers = {
            "Accept": "application/json",
        }

        return "GET", url, headers, params

    def extract(
        self,
        raw_body: bytes,
        status_code: int,
        query_context: dict[str, Any],
    ) -> tuple[dict[str, Any], float]:
        """Parse ECB Data API JSON response.

        Returns structured extract with observations and metadata.
        """
        if status_code != 200:
            return {"error": f"HTTP {status_code}"}, 0.0

        try:
            data = json.loads(raw_body)
        except (json.JSONDecodeError, ValueError):
            return {"error": "Invalid JSON response"}, 0.0

        # Navigate SDMX-JSON structure
        datasets = data.get("dataSets", [])
        observations: list[dict[str, Any]] = []

        if datasets:
            series_data = datasets[0].get("series", {})
            for series_key, series_obj in series_data.items():
                obs = series_obj.get("observations", {})
                for time_idx, values in obs.items():
                    observations.append({
                        "series_key": series_key,
                        "time_index": time_idx,
                        "value": values[0] if values else None,
                    })

        # Extract dimension info if available
        structure = data.get("structure", {})
        dimensions = structure.get("dimensions", {})

        extract = {
            "dataflow": query_context.get("dataflow", ""),
            "series_key": query_context.get("series_key", ""),
            "observation_count": len(observations),
            "observations": observations[:20],
            "has_dimensions": bool(dimensions),
        }

        confidence = 1.0 if observations else 0.5
        return extract, confidence

    def assess_freshness(
        self, structured_extract: dict[str, Any], retrieved_at: Any
    ) -> FreshnessState:
        if structured_extract.get("error"):
            return FreshnessState.ERROR
        if structured_extract.get("observation_count", 0) == 0:
            return FreshnessState.NO_DATA
        return FreshnessState.FRESH
