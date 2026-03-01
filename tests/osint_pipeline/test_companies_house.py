"""Tests for Companies House collector.

T1.7: build_request for each endpoint, extract for profile JSON,
auth header, freshness assessment. Uses httpx.MockTransport.
"""

from __future__ import annotations

import base64
import json

import httpx
import pytest

from osint_pipeline.collectors.companies_house import CompaniesHouseCollector
from osint_pipeline.models.evidence import CollectionStatus, FreshnessState

from conftest import SAMPLE_COMPANY_PROFILE


def _mock_transport(status: int = 200, body: dict | None = None) -> httpx.MockTransport:
    """Create a mock transport returning the given status and body."""
    body = body if body is not None else SAMPLE_COMPANY_PROFILE
    body_bytes = json.dumps(body).encode("utf-8")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code=status, content=body_bytes)

    return httpx.MockTransport(handler)


def _collector(**kwargs) -> CompaniesHouseCollector:
    """Create a collector with a test API key."""
    config = {"api_key": "test_key_12345"}
    config.update(kwargs)
    return CompaniesHouseCollector(config=config)


class TestCompaniesHouseInit:
    """Initialisation tests."""

    def test_requires_api_key(self):
        """Raises ValueError if API key is empty."""
        with pytest.raises(ValueError, match="API key required"):
            CompaniesHouseCollector(config={"api_key": ""})

    def test_requires_api_key_missing(self):
        """Raises ValueError if API key not in config."""
        with pytest.raises(ValueError, match="API key required"):
            CompaniesHouseCollector(config={})

    def test_properties(self):
        """Verify collector properties match registry."""
        c = _collector()
        assert c.source_id == "companies_house_api"
        assert c.source_group == "official_gov"
        assert c.jurisdiction == "GB"
        assert c.resolution_role == "primary_evidence"
        # K-6 fix
        assert c.independence_upstream_id == "uk_companies_house_backend"


class TestBuildRequest:
    """build_request tests for each endpoint type."""

    def test_profile_endpoint(self):
        """Default endpoint is company profile."""
        c = _collector()
        method, url, headers, params = c.build_request({"company_number": "12345678"})
        assert method == "GET"
        assert url.endswith("/company/12345678")
        assert "Authorization" in headers
        assert params is None

    def test_filing_history_endpoint(self):
        """Filing history endpoint."""
        c = _collector()
        _, url, _, _ = c.build_request(
            {"company_number": "12345678", "endpoint": "filing-history"}
        )
        assert url.endswith("/company/12345678/filing-history")

    def test_officers_endpoint(self):
        """Officers endpoint."""
        c = _collector()
        _, url, _, _ = c.build_request(
            {"company_number": "12345678", "endpoint": "officers"}
        )
        assert url.endswith("/company/12345678/officers")

    def test_psc_endpoint(self):
        """Persons with significant control endpoint."""
        c = _collector()
        _, url, _, _ = c.build_request(
            {"company_number": "12345678", "endpoint": "persons-with-significant-control"}
        )
        assert url.endswith("/company/12345678/persons-with-significant-control")

    def test_charges_endpoint(self):
        """Charges endpoint."""
        c = _collector()
        _, url, _, _ = c.build_request(
            {"company_number": "12345678", "endpoint": "charges"}
        )
        assert url.endswith("/company/12345678/charges")

    def test_insolvency_endpoint(self):
        """Insolvency endpoint."""
        c = _collector()
        _, url, _, _ = c.build_request(
            {"company_number": "12345678", "endpoint": "insolvency"}
        )
        assert url.endswith("/company/12345678/insolvency")

    def test_search_endpoint(self):
        """Company search endpoint."""
        c = _collector()
        method, url, headers, params = c.build_request({"search_term": "Acme Ltd"})
        assert method == "GET"
        assert "/search/companies" in url
        assert params["q"] == "Acme Ltd"

    def test_unknown_endpoint_raises(self):
        """Unknown endpoint raises ValueError."""
        c = _collector()
        with pytest.raises(ValueError, match="Unknown endpoint"):
            c.build_request({"company_number": "12345678", "endpoint": "unknown"})

    def test_missing_company_number_raises(self):
        """Missing company_number raises ValueError."""
        c = _collector()
        with pytest.raises(ValueError, match="company_number"):
            c.build_request({})

    def test_auth_header_format(self):
        """Auth header is HTTP Basic with API key as username."""
        c = _collector()
        _, _, headers, _ = c.build_request({"company_number": "12345678"})
        auth = headers["Authorization"]
        assert auth.startswith("Basic ")
        decoded = base64.b64decode(auth.split(" ")[1]).decode("utf-8")
        assert decoded == "test_key_12345:"


class TestExtract:
    """extract() tests."""

    def test_profile_extract(self):
        """Profile extraction returns key fields."""
        c = _collector()
        extract, confidence = c.extract(
            json.dumps(SAMPLE_COMPANY_PROFILE).encode(),
            200,
            {"company_number": "12345678"},
        )
        assert extract["company_number"] == "12345678"
        assert extract["company_name"] == "Test Company Ltd"
        assert confidence == 1.0

    def test_non_200_returns_zero_confidence(self):
        """Non-200 responses get zero confidence."""
        c = _collector()
        extract, confidence = c.extract(b"error", 500, {"company_number": "12345678"})
        assert confidence == 0.0
        assert "error" in extract

    def test_invalid_json_returns_zero_confidence(self):
        """Invalid JSON gets zero confidence."""
        c = _collector()
        extract, confidence = c.extract(b"not json", 200, {"company_number": "12345678"})
        assert confidence == 0.0
        assert "error" in extract


class TestCollect:
    """Full collect() integration tests with mock HTTP."""

    def test_successful_collection(self):
        """Successful collection produces valid bundle."""
        c = _collector()
        c._client = httpx.Client(transport=_mock_transport())

        result = c.collect({"company_number": "12345678"})
        assert result.succeeded
        assert result.bundle is not None
        assert result.bundle.source_id == "companies_house_api"
        assert result.bundle.confidence_score == 1.0
        assert len(result.bundle.receipt.receipt_hash) == 64

        c.close()

    def test_404_returns_not_found(self):
        """404 response produces NOT_FOUND status."""
        c = _collector()
        c._client = httpx.Client(transport=_mock_transport(status=404))

        result = c.collect({"company_number": "99999999"})
        assert not result.succeeded
        assert result.status == CollectionStatus.NOT_FOUND

        c.close()

    def test_401_returns_auth_failure(self):
        """401 response produces AUTH_FAILURE status."""
        c = _collector()
        c._client = httpx.Client(transport=_mock_transport(status=401))

        result = c.collect({"company_number": "12345678"})
        assert not result.succeeded
        assert result.status == CollectionStatus.AUTH_FAILURE

        c.close()

    def test_429_returns_rate_limited(self):
        """429 response produces RATE_LIMITED status."""
        c = _collector()
        c._client = httpx.Client(transport=_mock_transport(status=429))

        result = c.collect({"company_number": "12345678"})
        assert not result.succeeded
        assert result.status == CollectionStatus.RATE_LIMITED

        c.close()

    def test_500_returns_source_error(self):
        """500 response produces SOURCE_ERROR status."""
        c = _collector()
        c._client = httpx.Client(transport=_mock_transport(status=500))

        result = c.collect({"company_number": "12345678"})
        assert not result.succeeded
        assert result.status == CollectionStatus.SOURCE_ERROR

        c.close()


class TestFreshness:
    """Freshness assessment tests."""

    def test_fresh_on_success(self):
        """Successful retrieval -> FRESH."""
        c = _collector()
        from datetime import datetime, timezone
        result = c.assess_freshness(
            {"company_number": "12345678"}, datetime.now(timezone.utc)
        )
        assert result == FreshnessState.FRESH

    def test_error_on_error_extract(self):
        """Error in extract -> ERROR freshness."""
        c = _collector()
        from datetime import datetime, timezone
        result = c.assess_freshness(
            {"error": "HTTP 500"}, datetime.now(timezone.utc)
        )
        assert result == FreshnessState.ERROR
