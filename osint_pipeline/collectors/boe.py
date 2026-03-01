"""Bank of England Statistical Interactive Database collector.

Queries the BoE statistics API for interest rates and economic data.
No authentication required.

Registry source_id: boe_rates
Registry upstream: uk_boe_statistics_backend
"""

from __future__ import annotations

import json
from typing import Any

from osint_pipeline.collectors.base import BaseCollector
from osint_pipeline.models.evidence import FreshnessState


class BoECollector(BaseCollector):
    """Bank of England rates collector.

    No authentication required. Queries the BoE statistical database
    for interest rates, monetary aggregates, and other economic data.

    Config keys:
        - ``format``: Response format (default ``"json"``).
    """

    BASE_URL = "https://www.bankofengland.co.uk/boeapps/database"

    @property
    def source_id(self) -> str:
        return "boe_rates"

    @property
    def source_group(self) -> str:
        return "market_data"

    @property
    def independence_upstream_id(self) -> str:
        return "uk_boe_statistics_backend"

    @property
    def resolution_role(self) -> str:
        return "primary_evidence"

    @property
    def jurisdiction(self) -> str:
        return "GB"

    def build_request(
        self, query_context: dict[str, Any]
    ) -> tuple[str, str, dict[str, str], dict[str, Any] | None]:
        """Build BoE statistics request.

        query_context keys:
            - ``series_code``: BoE series code, e.g. ``"IUDBEDR"`` (required).
            - ``from_date``: Start date ``DD/Mon/YYYY``, e.g. ``"01/Jan/2025"`` (optional).
            - ``to_date``: End date ``DD/Mon/YYYY`` (optional).
        """
        series_code = query_context.get("series_code", "")
        if not series_code:
            raise ValueError("query_context must include 'series_code'")

        url = f"{self.BASE_URL}/{series_code}.json"

        params: dict[str, Any] = {}
        from_date = query_context.get("from_date")
        if from_date:
            params["from"] = from_date

        to_date = query_context.get("to_date")
        if to_date:
            params["to"] = to_date

        headers = {"Accept": "application/json"}
        return "GET", url, headers, params

    def extract(
        self,
        raw_body: bytes,
        status_code: int,
        query_context: dict[str, Any],
    ) -> tuple[dict[str, Any], float]:
        """Parse BoE statistics JSON response."""
        if status_code != 200:
            return {"error": f"HTTP {status_code}"}, 0.0

        try:
            data = json.loads(raw_body)
        except (json.JSONDecodeError, ValueError):
            return {"error": "Invalid JSON response"}, 0.0

        # BoE returns datasets with observations
        datasets = data.get("datasets", [])
        observations: list[dict[str, Any]] = []

        if datasets:
            for dataset in datasets:
                for obs in dataset.get("observations", []):
                    observations.append({
                        "date": obs.get("date"),
                        "value": obs.get("value"),
                        "status": obs.get("status"),
                    })

        extract = {
            "series_code": query_context.get("series_code", ""),
            "observation_count": len(observations),
            "observations": observations[:20],
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
