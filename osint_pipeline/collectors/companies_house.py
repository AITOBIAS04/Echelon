"""Companies House API collector.

GB Government company registry -- free API key, well-documented REST,
immutable revision policy, settlement-eligible.

API docs: https://developer.company-information.service.gov.uk/
Auth: API key as HTTP Basic username (password blank)

This is the recommended first collector to test the pipeline because:
- Free registration for API key
- Simple JSON responses
- Stable, official government endpoint
- Immutable data (company records don't retroactively change)
- Settlement-eligible in the registry
"""

from __future__ import annotations

import base64
from datetime import datetime, timezone
from typing import Any

from osint_pipeline.collectors.base import BaseCollector
from osint_pipeline.models.evidence import FreshnessState


class CompaniesHouseCollector(BaseCollector):
    """Collector for the UK Companies House API.

    Query contexts:
    - {"company_number": "12345678"} -- company profile
    - {"company_number": "12345678", "endpoint": "filing-history"} -- filing history
    - {"company_number": "12345678", "endpoint": "officers"} -- officer list
    - {"company_number": "12345678", "endpoint": "persons-with-significant-control"} -- PSC
    - {"company_number": "12345678", "endpoint": "charges"} -- charges
    - {"company_number": "12345678", "endpoint": "insolvency"} -- insolvency
    - {"search_term": "Acme Ltd"} -- company search
    """

    BASE_URL = "https://api.company-information.service.gov.uk"

    @property
    def source_id(self) -> str:
        return "companies_house_api"

    @property
    def source_group(self) -> str:
        return "official_gov"

    @property
    def independence_upstream_id(self) -> str:
        # K-6 fix: must match registry value
        return "uk_companies_house_backend"

    @property
    def resolution_role(self) -> str:
        return "primary_evidence"

    @property
    def jurisdiction(self) -> str:
        return "GB"

    def __init__(self, config: dict[str, Any] | None = None):
        super().__init__(config)
        self._api_key = self.config.get("api_key", "")
        if not self._api_key:
            raise ValueError(
                "Companies House API key required. "
                "Register free at https://developer.company-information.service.gov.uk/"
            )

    def _auth_header(self) -> str:
        """Companies House uses HTTP Basic with API key as username, blank password."""
        credentials = f"{self._api_key}:"
        encoded = base64.b64encode(credentials.encode("utf-8")).decode("utf-8")
        return f"Basic {encoded}"

    def build_request(
        self, query_context: dict[str, Any]
    ) -> tuple[str, str, dict[str, str], dict[str, Any] | None]:
        headers = {
            "Authorization": self._auth_header(),
            "Accept": "application/json",
        }

        # Company search
        if "search_term" in query_context:
            url = f"{self.BASE_URL}/search/companies"
            params = {
                "q": query_context["search_term"],
                "items_per_page": str(query_context.get("items_per_page", 10)),
            }
            return ("GET", url, headers, params)

        # Company-specific endpoints
        company_number = query_context.get("company_number", "")
        if not company_number:
            raise ValueError("query_context must include 'company_number' or 'search_term'")

        endpoint = query_context.get("endpoint", "profile")
        if endpoint == "profile":
            url = f"{self.BASE_URL}/company/{company_number}"
        elif endpoint == "filing-history":
            url = f"{self.BASE_URL}/company/{company_number}/filing-history"
        elif endpoint == "officers":
            url = f"{self.BASE_URL}/company/{company_number}/officers"
        elif endpoint == "persons-with-significant-control":
            url = f"{self.BASE_URL}/company/{company_number}/persons-with-significant-control"
        elif endpoint == "charges":
            url = f"{self.BASE_URL}/company/{company_number}/charges"
        elif endpoint == "insolvency":
            url = f"{self.BASE_URL}/company/{company_number}/insolvency"
        else:
            raise ValueError(f"Unknown endpoint: {endpoint}")

        return ("GET", url, headers, None)

    def extract(
        self, raw_body: bytes, status_code: int, query_context: dict[str, Any]
    ) -> tuple[dict[str, Any], float]:
        """Parse Companies House JSON response into structured extract.

        Confidence scoring:
        - 1.0 for 200 responses with valid JSON (official government source)
        - 0.0 for non-200 or malformed responses
        """
        import json

        if status_code != 200:
            return {"error": f"HTTP {status_code}", "raw_size": len(raw_body)}, 0.0

        try:
            data = json.loads(raw_body)
        except json.JSONDecodeError:
            return {"error": "Invalid JSON", "raw_size": len(raw_body)}, 0.0

        # Extract key fields based on endpoint type
        endpoint = query_context.get("endpoint", "profile")

        if "search_term" in query_context:
            extract = self._extract_search_results(data)
        elif endpoint == "profile" or "endpoint" not in query_context:
            extract = self._extract_company_profile(data)
        elif endpoint == "filing-history":
            extract = self._extract_filing_history(data)
        elif endpoint == "officers":
            extract = self._extract_officers(data)
        else:
            extract = {"data": data}

        # Official government source with valid response = max confidence
        return extract, 1.0

    def _extract_company_profile(self, data: dict) -> dict[str, Any]:
        """Extract key fields from company profile."""
        return {
            "company_number": data.get("company_number"),
            "company_name": data.get("company_name"),
            "company_status": data.get("company_status"),
            "company_type": data.get("type"),
            "date_of_creation": data.get("date_of_creation"),
            "date_of_cessation": data.get("date_of_cessation"),
            "registered_office_address": data.get("registered_office_address", {}),
            "sic_codes": data.get("sic_codes", []),
            "has_insolvency_history": data.get("has_insolvency_history", False),
            "has_charges": data.get("has_charges", False),
            "last_full_members_list_date": data.get("last_full_members_list_date"),
            "accounts_next_due": data.get("accounts", {}).get("next_due"),
            "confirmation_statement_next_due": data.get(
                "confirmation_statement", {}
            ).get("next_due"),
        }

    def _extract_filing_history(self, data: dict) -> dict[str, Any]:
        """Extract key fields from filing history."""
        items = data.get("items", [])
        return {
            "total_count": data.get("total_count", 0),
            "items_returned": len(items),
            "recent_filings": [
                {
                    "date": item.get("date"),
                    "category": item.get("category"),
                    "description": item.get("description"),
                    "type": item.get("type"),
                }
                for item in items[:10]  # Latest 10 filings
            ],
        }

    def _extract_officers(self, data: dict) -> dict[str, Any]:
        """Extract key fields from officer list."""
        items = data.get("items", [])
        return {
            "total_results": data.get("total_results", 0),
            "active_count": data.get("active_count", 0),
            "resigned_count": data.get("resigned_count", 0),
            "officers": [
                {
                    "name": item.get("name"),
                    "officer_role": item.get("officer_role"),
                    "appointed_on": item.get("appointed_on"),
                    "resigned_on": item.get("resigned_on"),
                    "nationality": item.get("nationality"),
                }
                for item in items[:20]
            ],
        }

    def _extract_search_results(self, data: dict) -> dict[str, Any]:
        """Extract key fields from company search results."""
        items = data.get("items", [])
        return {
            "total_results": data.get("total_results", 0),
            "items_returned": len(items),
            "matches": [
                {
                    "company_number": item.get("company_number"),
                    "title": item.get("title"),
                    "company_status": item.get("company_status"),
                    "company_type": item.get("company_type"),
                    "date_of_creation": item.get("date_of_creation"),
                    "address_snippet": item.get("address_snippet"),
                }
                for item in items[:10]
            ],
        }

    def assess_freshness(
        self, structured_extract: dict[str, Any], retrieved_at: datetime
    ) -> FreshnessState:
        """Companies House data is always considered FRESH on successful retrieval.

        The register is the system of record -- whatever it returns IS
        the current state.
        """
        if "error" in structured_extract:
            return FreshnessState.ERROR
        return FreshnessState.FRESH
