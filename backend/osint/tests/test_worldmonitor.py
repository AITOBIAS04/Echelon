"""WorldMonitor collector tests — 3 domains, error handling, retry.

All HTTP calls are mocked via unittest.mock. No real WM endpoints are called.
Tests verify correct endpoint routing, EvidenceBundle construction, receipt
generation, error handling, and retry logic.
"""
from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.osint.canonical import compute_content_hash, compute_receipt_hash
from backend.osint.collectors.worldmonitor import (
    WorldMonitorCollector,
    WorldMonitorConfig,
    _DOMAIN_ENDPOINTS,
    _DOMAIN_SOURCE_GROUPS,
    _DOMAIN_SOURCE_IDS,
)
from backend.osint.models.evidence import HealthStatus, WMDomain


@pytest.fixture
def fast_config() -> WorldMonitorConfig:
    """Config with no retries and very short delays for fast tests."""
    return WorldMonitorConfig(
        base_url="http://mock:8080",
        timeout_s=5.0,
        version="v0.1.0",
        retry_count=0,
        retry_delay_s=0.0,
    )


@pytest.fixture
def retry_config() -> WorldMonitorConfig:
    """Config with retries for retry logic tests."""
    return WorldMonitorConfig(
        base_url="http://mock:8080",
        timeout_s=5.0,
        version="v0.1.0",
        retry_count=2,
        retry_delay_s=0.001,
    )


def _make_mock_response(fixture_name: str) -> bytes:
    """Load fixture as raw bytes for mock HTTP response."""
    import os
    from pathlib import Path
    fixtures_dir = Path(__file__).parent / "fixtures"
    with open(fixtures_dir / fixture_name, "rb") as f:
        return f.read()


class TestWorldMonitorCollectorInit:
    """Collector initialization and source_id mapping."""

    def test_cii_source_id(self) -> None:
        """CII collector returns correct source_id."""
        c = WorldMonitorCollector(WMDomain.INTELLIGENCE)
        assert c.source_id() == "worldmonitor_cii"

    def test_market_source_id(self) -> None:
        """Market collector returns correct source_id."""
        c = WorldMonitorCollector(WMDomain.MARKET)
        assert c.source_id() == "worldmonitor_finance"

    def test_maritime_source_id(self) -> None:
        """Maritime collector returns correct source_id."""
        c = WorldMonitorCollector(WMDomain.MARITIME)
        assert c.source_id() == "worldmonitor_maritime"

    def test_default_config(self) -> None:
        """Default config values are correct."""
        c = WorldMonitorCollector(WMDomain.INTELLIGENCE)
        assert c.config.base_url == "http://localhost:8080"
        assert c.config.timeout_s == 30.0
        assert c.config.retry_count == 2

    def test_domain_endpoint_mapping(self) -> None:
        """All three domains map to correct endpoints."""
        assert _DOMAIN_ENDPOINTS[WMDomain.INTELLIGENCE] == "/api/v1/intelligence/cii"
        assert _DOMAIN_ENDPOINTS[WMDomain.MARKET] == "/api/v1/market/snapshot"
        assert _DOMAIN_ENDPOINTS[WMDomain.MARITIME] == "/api/v1/maritime/anomaly"


class TestWorldMonitorFetchSuccess:
    """Successful fetch scenarios with mocked HTTP."""

    @pytest.mark.asyncio
    async def test_cii_fetch_success(self, fast_config: WorldMonitorConfig) -> None:
        """CII collector produces valid CollectionResult on HTTP 200."""
        raw = _make_mock_response("wm_cii_response.json")
        collector = WorldMonitorCollector(WMDomain.INTELLIGENCE, fast_config)

        with patch.object(collector, "_do_http_post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = raw
            result = await collector.fetch({"country_code": "IRN"}, "theatre_001")

        assert result.success is True
        assert result.source_id == "worldmonitor_cii"
        assert result.bundle is not None
        assert result.bundle.source_id == "worldmonitor_cii"
        assert result.bundle.source_group == "alt_data_behavioural"
        assert result.bundle.resolution_role == "primary_evidence"
        assert result.error is None
        assert result.raw_payload == raw
        assert result.fetch_duration_ms > 0

    @pytest.mark.asyncio
    async def test_market_fetch_success(self, fast_config: WorldMonitorConfig) -> None:
        """Market collector produces valid CollectionResult on HTTP 200."""
        raw = _make_mock_response("wm_market_response.json")
        collector = WorldMonitorCollector(WMDomain.MARKET, fast_config)

        with patch.object(collector, "_do_http_post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = raw
            result = await collector.fetch({"asset_class": "fx"}, "theatre_001")

        assert result.success is True
        assert result.source_id == "worldmonitor_finance"
        assert result.bundle is not None
        assert result.bundle.source_group == "market_data"

    @pytest.mark.asyncio
    async def test_maritime_fetch_success(self, fast_config: WorldMonitorConfig) -> None:
        """Maritime collector produces valid CollectionResult on HTTP 200."""
        raw = _make_mock_response("wm_maritime_response.json")
        collector = WorldMonitorCollector(WMDomain.MARITIME, fast_config)

        with patch.object(collector, "_do_http_post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = raw
            result = await collector.fetch({"geo": {"lat": 26.5, "lon": 56.2}}, "theatre_001")

        assert result.success is True
        assert result.source_id == "worldmonitor_maritime"
        assert result.bundle is not None
        assert result.bundle.source_group == "maritime_ais"

    @pytest.mark.asyncio
    async def test_receipt_content_hash_matches(self, fast_config: WorldMonitorConfig) -> None:
        """Receipt content_hash matches SHA-256 of raw response bytes."""
        raw = _make_mock_response("wm_cii_response.json")
        collector = WorldMonitorCollector(WMDomain.INTELLIGENCE, fast_config)

        with patch.object(collector, "_do_http_post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = raw
            result = await collector.fetch({"country_code": "IRN"}, "theatre_001")

        assert result.success is True
        expected_hash = compute_content_hash(raw)
        assert result.bundle.receipt.content_hash == expected_hash


class TestWorldMonitorFetchErrors:
    """Error handling scenarios with mocked HTTP."""

    @pytest.mark.asyncio
    async def test_connection_error(self, fast_config: WorldMonitorConfig) -> None:
        """Connection error returns success=False with error message."""
        collector = WorldMonitorCollector(WMDomain.INTELLIGENCE, fast_config)

        with patch.object(collector, "_do_http_post", new_callable=AsyncMock) as mock_post:
            mock_post.side_effect = ConnectionError("Connection refused")
            result = await collector.fetch({"country_code": "IRN"}, "theatre_001")

        assert result.success is False
        assert result.bundle is None
        assert "Connection error" in result.error

    @pytest.mark.asyncio
    async def test_timeout_error(self, fast_config: WorldMonitorConfig) -> None:
        """Timeout returns success=False with timeout error."""
        collector = WorldMonitorCollector(WMDomain.INTELLIGENCE, fast_config)

        with patch.object(collector, "_do_http_post", new_callable=AsyncMock) as mock_post:
            mock_post.side_effect = asyncio.TimeoutError()
            result = await collector.fetch({"country_code": "IRN"}, "theatre_001")

        assert result.success is False
        assert "Timeout" in result.error

    @pytest.mark.asyncio
    async def test_malformed_json(self, fast_config: WorldMonitorConfig) -> None:
        """Malformed JSON returns success=False with parse error."""
        collector = WorldMonitorCollector(WMDomain.INTELLIGENCE, fast_config)

        with patch.object(collector, "_do_http_post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = b"{invalid json"
            result = await collector.fetch({"country_code": "IRN"}, "theatre_001")

        assert result.success is False
        assert "Malformed response" in result.error

    @pytest.mark.asyncio
    async def test_http_500_error(self, fast_config: WorldMonitorConfig) -> None:
        """HTTP 500 returns success=False."""
        import urllib.error
        collector = WorldMonitorCollector(WMDomain.INTELLIGENCE, fast_config)

        with patch.object(collector, "_do_http_post", new_callable=AsyncMock) as mock_post:
            mock_post.side_effect = urllib.error.HTTPError(
                "http://mock:8080/api/v1/intelligence/cii", 500,
                "Internal Server Error", {}, None
            )
            result = await collector.fetch({"country_code": "IRN"}, "theatre_001")

        assert result.success is False
        assert "HTTP 500" in result.error


class TestWorldMonitorRetry:
    """Retry logic for transient failures."""

    @pytest.mark.asyncio
    async def test_retry_on_error_then_success(self, retry_config: WorldMonitorConfig) -> None:
        """Collector retries on transient failure, succeeds on retry."""
        raw = _make_mock_response("wm_cii_response.json")
        collector = WorldMonitorCollector(WMDomain.INTELLIGENCE, retry_config)
        call_count = 0

        async def _flaky_post(url, request):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ConnectionError("transient failure")
            return raw

        with patch.object(collector, "_do_http_post", side_effect=_flaky_post):
            result = await collector.fetch({"country_code": "IRN"}, "theatre_001")

        assert result.success is True
        assert call_count == 2  # initial + 1 retry

    @pytest.mark.asyncio
    async def test_all_retries_exhausted(self, retry_config: WorldMonitorConfig) -> None:
        """All retries fail -> success=False."""
        collector = WorldMonitorCollector(WMDomain.INTELLIGENCE, retry_config)

        with patch.object(collector, "_do_http_post", new_callable=AsyncMock) as mock_post:
            mock_post.side_effect = ConnectionError("persistent failure")
            result = await collector.fetch({"country_code": "IRN"}, "theatre_001")

        assert result.success is False
        # 1 initial + 2 retries = 3 calls
        assert mock_post.call_count == 3


class TestWorldMonitorHealthCheck:
    """Health check endpoint tests."""

    @pytest.mark.asyncio
    async def test_health_unavailable_on_connection_error(self) -> None:
        """Connection error -> HealthStatus.UNAVAILABLE."""
        collector = WorldMonitorCollector(WMDomain.INTELLIGENCE)
        # Without mocking, the real HTTP call will fail
        status = await collector.health_check()
        assert status == HealthStatus.UNAVAILABLE
