"""Cycle 026 Sprint 1 — Financial + Corporate Collectors tests.

Tests (12 total):
FRED: success, missing API key, invalid series_id (no observations)
Alpha Vantage: success, rate limit (Note response), invalid symbol (no time series)
OpenCorporates: success, auth failure (403), empty result set
Etherscan: success, invalid address (error response), rate limit
"""
from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest

from backend.osint.collectors.fred import FREDCollector
from backend.osint.collectors.alpha_vantage import AlphaVantageCollector
from backend.osint.collectors.opencorporates import OpenCorporatesCollector
from backend.osint.collectors.etherscan import EtherscanCollector


# ── Mock Responses ──

FRED_SUCCESS_RESPONSE = json.dumps({
    "observations": [
        {"date": "2026-03-01", "value": "2.5"}
    ]
}).encode()

ALPHA_VANTAGE_SUCCESS_RESPONSE = json.dumps({
    "Meta Data": {"2. Symbol": "AAPL"},
    "Time Series (Daily)": {
        "2026-03-17": {
            "1. open": "180.00",
            "2. high": "185.00",
            "3. low": "179.00",
            "4. close": "183.50",
            "5. volume": "50000000",
        }
    },
}).encode()

ALPHA_VANTAGE_RATE_LIMIT_RESPONSE = json.dumps({
    "Note": "Thank you for using Alpha Vantage! Our standard API rate limit is 25 requests per day."
}).encode()

OPENCORPORATES_SUCCESS_RESPONSE = json.dumps({
    "results": {
        "companies": [
            {"company": {"name": "Test Corp", "company_number": "12345678", "jurisdiction_code": "gb"}},
            {"company": {"name": "Test Inc", "company_number": "87654321", "jurisdiction_code": "us_de"}},
        ],
        "total_count": 2,
    }
}).encode()

OPENCORPORATES_EMPTY_RESPONSE = json.dumps({
    "results": {
        "companies": [],
        "total_count": 0,
    }
}).encode()

ETHERSCAN_SUCCESS_RESPONSE = json.dumps({
    "status": "1",
    "message": "OK",
    "result": "1000000000000000000",  # 1 ETH in wei
}).encode()

ETHERSCAN_INVALID_ADDRESS_RESPONSE = json.dumps({
    "status": "0",
    "message": "NOTOK",
    "result": "Error! Invalid address format",
}).encode()

ETHERSCAN_RATE_LIMIT_RESPONSE = json.dumps({
    "status": "0",
    "message": "NOTOK",
    "result": "Max rate limit reached, please use API Key for higher rate limit",
}).encode()


# ── FRED Tests ──

class TestFREDCollector:
    """Test FREDCollector."""

    @pytest.mark.asyncio
    async def test_success(self):
        """FRED success: mocked response returns valid CollectionResult."""
        collector = FREDCollector(api_key="test-key")
        with patch.object(collector, "_do_http_get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = FRED_SUCCESS_RESPONSE
            result = await collector._fetch(
                {"series_id": "GDP"},
                theatre_id="theatre-001",
            )
        assert result.success is True
        assert result.bundle is not None
        assert result.bundle.source_id == "fred_api"
        assert result.bundle.normalised_event.measure.value == 2.5
        # API key must NOT appear in receipt
        assert "test-key" not in str(result.bundle.receipt.request_parameters)

    @pytest.mark.asyncio
    async def test_missing_api_key(self):
        """FRED missing API key: returns failure immediately."""
        collector = FREDCollector(api_key="")
        result = await collector._fetch(
            {"series_id": "GDP"},
            theatre_id="theatre-001",
        )
        assert result.success is False
        assert "No API key" in result.error

    @pytest.mark.asyncio
    async def test_invalid_series_id(self):
        """FRED invalid series: no observations returns failure."""
        collector = FREDCollector(api_key="test-key")
        empty_response = json.dumps({"observations": []}).encode()
        with patch.object(collector, "_do_http_get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = empty_response
            result = await collector._fetch(
                {"series_id": "INVALID_SERIES"},
                theatre_id="theatre-001",
            )
        assert result.success is False
        assert "No observations" in result.error


# ── Alpha Vantage Tests ──

class TestAlphaVantageCollector:
    """Test AlphaVantageCollector."""

    @pytest.mark.asyncio
    async def test_success(self):
        """Alpha Vantage success: mocked response returns valid CollectionResult."""
        collector = AlphaVantageCollector(api_key="test-key")
        with patch.object(collector, "_do_http_get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = ALPHA_VANTAGE_SUCCESS_RESPONSE
            result = await collector._fetch(
                {"symbol": "AAPL"},
                theatre_id="theatre-001",
            )
        assert result.success is True
        assert result.bundle is not None
        assert result.bundle.source_id == "alpha_vantage_api"
        assert result.bundle.normalised_event.measure.value == 183.5
        assert "test-key" not in str(result.bundle.receipt.request_parameters)

    @pytest.mark.asyncio
    async def test_rate_limit(self):
        """Alpha Vantage rate limit: Note response returns failure."""
        collector = AlphaVantageCollector(api_key="test-key")
        with patch.object(collector, "_do_http_get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = ALPHA_VANTAGE_RATE_LIMIT_RESPONSE
            result = await collector._fetch(
                {"symbol": "AAPL"},
                theatre_id="theatre-001",
            )
        assert result.success is False
        assert "API limit" in result.error

    @pytest.mark.asyncio
    async def test_invalid_symbol(self):
        """Alpha Vantage invalid symbol: empty time series returns failure."""
        collector = AlphaVantageCollector(api_key="test-key")
        empty_response = json.dumps({"Error Message": "Invalid API call"}).encode()
        with patch.object(collector, "_do_http_get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = empty_response
            result = await collector._fetch(
                {"symbol": "XXXXXX"},
                theatre_id="theatre-001",
            )
        assert result.success is False
        assert "No time series" in result.error


# ── OpenCorporates Tests ──

class TestOpenCorporatesCollector:
    """Test OpenCorporatesCollector."""

    @pytest.mark.asyncio
    async def test_success(self):
        """OpenCorporates success: mocked response returns valid CollectionResult."""
        collector = OpenCorporatesCollector(api_key="test-key")
        with patch.object(collector, "_do_http_get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = OPENCORPORATES_SUCCESS_RESPONSE
            result = await collector._fetch(
                {"q": "Test Corp"},
                theatre_id="theatre-001",
            )
        assert result.success is True
        assert result.bundle is not None
        assert result.bundle.source_id == "opencorporates_api"
        assert result.bundle.normalised_event.measure.value == 2.0  # 2 companies
        assert "test-key" not in str(result.bundle.receipt.request_parameters)

    @pytest.mark.asyncio
    async def test_auth_failure(self):
        """OpenCorporates 403: returns failure."""
        import urllib.error
        collector = OpenCorporatesCollector(api_key="bad-key")
        with patch.object(collector, "_do_http_get", new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = urllib.error.HTTPError(
                url="https://api.opencorporates.com/v0.4/companies/search",
                code=403,
                msg="Forbidden",
                hdrs={},
                fp=None,
            )
            result = await collector._fetch(
                {"q": "Test Corp"},
                theatre_id="theatre-001",
            )
        assert result.success is False
        assert "403" in result.error

    @pytest.mark.asyncio
    async def test_empty_result_set(self):
        """OpenCorporates empty results: still returns success (0 companies is valid)."""
        collector = OpenCorporatesCollector(api_key="test-key")
        with patch.object(collector, "_do_http_get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = OPENCORPORATES_EMPTY_RESPONSE
            result = await collector._fetch(
                {"q": "xyznonexistent12345"},
                theatre_id="theatre-001",
            )
        assert result.success is True
        assert result.bundle.normalised_event.measure.value == 0.0


# ── Etherscan Tests ──

class TestEtherscanCollector:
    """Test EtherscanCollector."""

    @pytest.mark.asyncio
    async def test_success(self):
        """Etherscan success: balance query returns valid CollectionResult."""
        collector = EtherscanCollector(api_key="test-key")
        with patch.object(collector, "_do_http_get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = ETHERSCAN_SUCCESS_RESPONSE
            result = await collector._fetch(
                {"address": "0xde0B295669a9FD93d5F28D9Ec85E40f4cb697BAe"},
                theatre_id="theatre-001",
            )
        assert result.success is True
        assert result.bundle is not None
        assert result.bundle.source_id == "etherscan_api"
        assert result.bundle.normalised_event.measure.value == 1.0  # 1 ETH
        assert "test-key" not in str(result.bundle.receipt.request_parameters)

    @pytest.mark.asyncio
    async def test_invalid_address(self):
        """Etherscan invalid address: error response returns failure."""
        collector = EtherscanCollector(api_key="test-key")
        with patch.object(collector, "_do_http_get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = ETHERSCAN_INVALID_ADDRESS_RESPONSE
            result = await collector._fetch(
                {"address": "0xinvalid"},
                theatre_id="theatre-001",
            )
        assert result.success is False
        assert "Invalid address" in result.error

    @pytest.mark.asyncio
    async def test_rate_limit(self):
        """Etherscan rate limit: error response returns failure."""
        collector = EtherscanCollector(api_key="test-key")
        with patch.object(collector, "_do_http_get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = ETHERSCAN_RATE_LIMIT_RESPONSE
            result = await collector._fetch(
                {"address": "0xde0B295669a9FD93d5F28D9Ec85E40f4cb697BAe"},
                theatre_id="theatre-001",
            )
        assert result.success is False
        assert "rate limit" in result.error.lower() or "Max rate" in result.error
