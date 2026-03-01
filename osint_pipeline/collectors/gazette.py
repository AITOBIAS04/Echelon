"""London Gazette (Official Notices) collector.

Queries The Gazette data API for insolvency notices, corporate events,
and other official publications. Functions as a counter-signal source.
No authentication required.

Registry source_id: uk_gazette
Registry upstream: uk_tso_gazette_backend
"""

from __future__ import annotations

import json
from typing import Any

from osint_pipeline.collectors.base import BaseCollector
from osint_pipeline.models.evidence import FreshnessState


class GazetteCollector(BaseCollector):
    """London Gazette collector for official notices.

    No authentication required. Primarily used as a counter-signal
    source for insolvency and corporate event detection.

    Config keys:
        - ``edition``: Gazette edition (default ``"london"``).
    """

    BASE_URL = "https://www.thegazette.co.uk"

    @property
    def source_id(self) -> str:
        return "uk_gazette"

    @property
    def source_group(self) -> str:
        return "official_gov"

    @property
    def independence_upstream_id(self) -> str:
        return "uk_tso_gazette_backend"

    @property
    def resolution_role(self) -> str:
        return "primary_evidence"

    @property
    def jurisdiction(self) -> str:
        return "GB"

    def build_request(
        self, query_context: dict[str, Any]
    ) -> tuple[str, str, dict[str, str], dict[str, Any] | None]:
        """Build Gazette search request.

        query_context keys:
            - ``search_term``: Free-text search (required).
            - ``notice_type``: Filter by type, e.g. ``"insolvency"`` (optional).
            - ``edition``: ``"london"``, ``"edinburgh"``, ``"belfast"`` (optional).
            - ``published_date_from``: ``YYYY-MM-DD`` (optional).
            - ``published_date_to``: ``YYYY-MM-DD`` (optional).
        """
        search_term = query_context.get("search_term", "")
        if not search_term:
            raise ValueError("query_context must include 'search_term'")

        edition = query_context.get(
            "edition", self.config.get("edition", "london")
        )
        url = f"{self.BASE_URL}/data/search"

        params: dict[str, Any] = {
            "q": search_term,
            "edition": edition,
            "results-page-size": 10,
        }

        notice_type = query_context.get("notice_type")
        if notice_type:
            params["categorycode"] = notice_type

        date_from = query_context.get("published_date_from")
        if date_from:
            params["publisheddate-from"] = date_from

        date_to = query_context.get("published_date_to")
        if date_to:
            params["publisheddate-to"] = date_to

        headers = {"Accept": "application/json"}
        return "GET", url, headers, params

    def extract(
        self,
        raw_body: bytes,
        status_code: int,
        query_context: dict[str, Any],
    ) -> tuple[dict[str, Any], float]:
        """Parse Gazette search response."""
        if status_code != 200:
            return {"error": f"HTTP {status_code}"}, 0.0

        try:
            data = json.loads(raw_body)
        except (json.JSONDecodeError, ValueError):
            return {"error": "Invalid JSON response"}, 0.0

        # Gazette returns a results object
        results = data.get("results", data.get("notices", []))
        total = data.get("total", len(results) if isinstance(results, list) else 0)

        notices: list[dict[str, Any]] = []
        if isinstance(results, list):
            for notice in results[:10]:
                notices.append({
                    "notice_id": notice.get("id", notice.get("notice-id")),
                    "title": notice.get("title"),
                    "notice_type": notice.get("notice-type", notice.get("category")),
                    "published_date": notice.get("published-date", notice.get("date")),
                    "edition": notice.get("edition"),
                })

        # Check for counter-signal indicators
        has_insolvency = any(
            "insolvency" in (n.get("notice_type") or "").lower()
            for n in notices
        )

        extract = {
            "total_results": total,
            "notices": notices,
            "search_term": query_context.get("search_term", ""),
            "counter_signal_detected": has_insolvency,
            "counter_signal_detail": (
                "Insolvency notice found" if has_insolvency else None
            ),
        }

        confidence = 1.0 if total > 0 else 0.5
        return extract, confidence

    def assess_freshness(
        self, structured_extract: dict[str, Any], retrieved_at: Any
    ) -> FreshnessState:
        if structured_extract.get("error"):
            return FreshnessState.ERROR
        if structured_extract.get("total_results", 0) == 0:
            return FreshnessState.NO_DATA
        return FreshnessState.FRESH
