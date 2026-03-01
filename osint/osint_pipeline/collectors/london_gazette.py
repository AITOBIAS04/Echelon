"""
London Gazette collector.

UK official government publication — public search API, no auth required,
immutable revision policy, settlement-eligible.

The Gazette publishes insolvency notices, company changes, winding-up
petitions, and striking-off actions. Absence of such notices for a
company IS evidence (signal absence, not intelligence gap).

API: https://www.thegazette.co.uk/
Auth: None required for notice search
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from osint_pipeline.collectors.base import BaseCollector
from osint_pipeline.models.evidence import FreshnessState


# London Gazette notice category codes for corporate insolvency.
INSOLVENCY_CATEGORY = "G205000000"
# Winding-up/dissolution notices.
WINDING_UP_CATEGORY = "G206000000"
# All corporate notices (broader search).
ALL_CORPORATE_CATEGORY = "G200000000"

# Category mapping for query convenience.
NOTICE_TYPE_CATEGORIES: dict[str, str] = {
    "insolvency": INSOLVENCY_CATEGORY,
    "winding_up": WINDING_UP_CATEGORY,
    "all_corporate": ALL_CORPORATE_CATEGORY,
}


class LondonGazetteCollector(BaseCollector):
    """
    Collector for the London Gazette notice search.

    Query contexts:
    - {"company_name": "TESCO PLC"} — search insolvency notices (default)
    - {"company_name": "TESCO PLC", "notice_type": "winding_up"} — winding-up
    - {"company_name": "TESCO PLC", "notice_type": "all_corporate"} — all corporate
    """

    BASE_URL = "https://www.thegazette.co.uk"

    @property
    def source_id(self) -> str:
        return "london_gazette_api"

    @property
    def source_group(self) -> str:
        return "official_gov"

    @property
    def independence_upstream_id(self) -> str:
        return "gb_london_gazette"

    @property
    def resolution_role(self) -> str:
        return "secondary_corroboration"

    @property
    def jurisdiction(self) -> str:
        return "GB"

    def build_request(
        self, query_context: dict[str, Any]
    ) -> tuple[str, str, dict[str, str], dict[str, Any] | None]:
        company_name = query_context.get("company_name", "")
        if not company_name:
            raise ValueError("query_context must include 'company_name'")

        notice_type = query_context.get("notice_type", "insolvency")
        category_code = NOTICE_TYPE_CATEGORIES.get(notice_type, INSOLVENCY_CATEGORY)

        url = f"{self.BASE_URL}/notice"
        headers = {
            "Accept": "application/json",
            "User-Agent": "EchelonPipeline/1.0",
        }
        params = {
            "categorycode": category_code,
            "company-name": company_name,
        }

        return ("GET", url, headers, params)

    def extract(
        self, raw_body: bytes, status_code: int, query_context: dict[str, Any]
    ) -> tuple[dict[str, Any], float]:
        """
        Parse London Gazette search results.

        Confidence scoring:
        - 1.0 for 200 responses (official government source)
        - 0.0 for non-200 or unparseable responses

        Counter-signal semantics:
        - counter_signal_detected = True if insolvency/winding-up notices found
        - counter_signal_detected = False if no such notices (signal absence = evidence)
        """
        import json

        if status_code != 200:
            return {
                "error": f"HTTP {status_code}",
                "raw_size": len(raw_body),
                "counter_signal_detected": False,
                "counter_signal_class": "corporate_event",
            }, 0.0

        try:
            data = json.loads(raw_body)
        except (json.JSONDecodeError, UnicodeDecodeError):
            # London Gazette may return HTML instead of JSON in some cases.
            # Treat as parseable failure — still produce a bundle.
            return {
                "error": "Response not valid JSON (possibly HTML)",
                "raw_size": len(raw_body),
                "counter_signal_detected": False,
                "counter_signal_class": "corporate_event",
            }, 0.0

        # Extract notice results.
        # The Gazette API response structure varies; handle common formats.
        notices = []
        total_results = 0

        if isinstance(data, dict):
            # Standard search response
            results = data.get("results", data.get("items", []))
            if isinstance(results, list):
                notices = results
                total_results = data.get("total", data.get("total_results", len(results)))
            elif "notice" in data:
                # Single notice or notice list
                notice_data = data["notice"]
                if isinstance(notice_data, list):
                    notices = notice_data
                    total_results = len(notice_data)
                elif isinstance(notice_data, dict):
                    notices = [notice_data]
                    total_results = 1

        # Check for counter-signal: any insolvency/winding-up/strike-off notice
        counter_signal_detected = total_results > 0

        extract = {
            "total_results": total_results,
            "notices_returned": len(notices[:20]),  # Cap at 20 for extract
            "notices": [
                {
                    "title": n.get("title", n.get("notice-title", "")),
                    "date": n.get("date", n.get("publication-date", "")),
                    "category": n.get("category", n.get("notice-category", "")),
                    "url": n.get("url", n.get("links", {}).get("self", "")),
                }
                for n in notices[:20]
            ],
            "counter_signal_detected": counter_signal_detected,
            "counter_signal_class": "corporate_event",
            "counter_signal_detail": (
                f"{total_results} notice(s) found"
                if counter_signal_detected
                else "No notices found (signal absence)"
            ),
        }

        return extract, 1.0

    def assess_freshness(
        self, structured_extract: dict[str, Any], retrieved_at: datetime
    ) -> FreshnessState:
        """
        London Gazette data is always FRESH on successful retrieval.

        The Gazette is the system of record for official notices.
        """
        if "error" in structured_extract:
            return FreshnessState.ERROR
        return FreshnessState.FRESH
