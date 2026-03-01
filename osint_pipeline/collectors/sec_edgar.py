"""SEC EDGAR full-text search collector.

Queries the SEC EDGAR EFTS (full-text search) API for US company filings.
Authentication is via User-Agent header (SEC requires an email address).

Registry source_id: sec_edgar
Registry upstream: us_sec_edgar_backend
"""

from __future__ import annotations

import json
from typing import Any

from osint_pipeline.collectors.base import BaseCollector
from osint_pipeline.models.evidence import FreshnessState


class SECEdgarCollector(BaseCollector):
    """SEC EDGAR full-text search collector.

    SEC requires a User-Agent header containing a company name and
    contact email, e.g. ``"MyApp admin@example.com"``.

    Config keys:
        - ``user_agent``: Required. User-Agent string with contact email.
    """

    BASE_URL = "https://efts.sec.gov/LATEST/search-index"

    @property
    def source_id(self) -> str:
        return "sec_edgar"

    @property
    def source_group(self) -> str:
        return "official_gov"

    @property
    def independence_upstream_id(self) -> str:
        return "us_sec_edgar_backend"

    @property
    def resolution_role(self) -> str:
        return "primary_evidence"

    @property
    def jurisdiction(self) -> str:
        return "US"

    def __init__(self, config: dict[str, Any] | None = None):
        super().__init__(config)
        user_agent = self.config.get("user_agent", "")
        if not user_agent:
            raise ValueError(
                "SEC EDGAR requires a User-Agent with contact email. "
                "Set config['user_agent'] = 'AppName admin@example.com'"
            )

    def build_request(
        self, query_context: dict[str, Any]
    ) -> tuple[str, str, dict[str, str], dict[str, Any] | None]:
        """Build EDGAR EFTS search request.

        query_context keys:
            - ``search_query``: Free-text search query (required).
            - ``date_from``: Start date ``YYYY-MM-DD`` (optional).
            - ``date_to``: End date ``YYYY-MM-DD`` (optional).
            - ``form_type``: SEC form type filter, e.g. ``"10-K"`` (optional).
            - ``entity_name``: Company name filter (optional).
        """
        search_query = query_context.get("search_query", "")
        if not search_query:
            raise ValueError("query_context must include 'search_query'")

        params: dict[str, Any] = {"q": search_query}

        date_from = query_context.get("date_from")
        date_to = query_context.get("date_to")
        if date_from or date_to:
            params["dateRange"] = "custom"
            if date_from:
                params["startdt"] = date_from
            if date_to:
                params["enddt"] = date_to

        form_type = query_context.get("form_type")
        if form_type:
            params["forms"] = form_type

        entity_name = query_context.get("entity_name")
        if entity_name:
            params["entityName"] = entity_name

        headers = {
            "Accept": "application/json",
            "User-Agent": self.config["user_agent"],
        }

        return "GET", self.BASE_URL, headers, params

    def extract(
        self,
        raw_body: bytes,
        status_code: int,
        query_context: dict[str, Any],
    ) -> tuple[dict[str, Any], float]:
        """Parse EDGAR EFTS search response.

        Returns structured extract with filing hits and metadata.
        """
        if status_code != 200:
            return {"error": f"HTTP {status_code}"}, 0.0

        try:
            data = json.loads(raw_body)
        except (json.JSONDecodeError, ValueError):
            return {"error": "Invalid JSON response"}, 0.0

        hits = data.get("hits", {})
        total = hits.get("total", {})
        total_hits = total.get("value", 0) if isinstance(total, dict) else total

        filings = []
        for hit in hits.get("hits", [])[:10]:
            source = hit.get("_source", {})
            filings.append({
                "file_date": source.get("file_date"),
                "entity_name": source.get("entity_name"),
                "form_type": source.get("form_type"),
                "file_number": source.get("file_num"),
                "period_of_report": source.get("period_of_report"),
            })

        extract = {
            "total_hits": total_hits,
            "filings": filings,
            "search_query": query_context.get("search_query", ""),
        }

        confidence = 1.0 if total_hits > 0 else 0.5
        return extract, confidence

    def assess_freshness(
        self, structured_extract: dict[str, Any], retrieved_at: Any
    ) -> FreshnessState:
        if structured_extract.get("error"):
            return FreshnessState.ERROR
        if structured_extract.get("total_hits", 0) == 0:
            return FreshnessState.NO_DATA
        return FreshnessState.FRESH
