"""Live WorldMonitor collector tests — require running WM instance.

All tests gated behind @pytest.mark.live_wm. Skipped by default.
Run with: pytest --live-wm  or  ECHELON_LIVE_WM=1 pytest
"""
from __future__ import annotations

import hashlib

import pytest

from backend.osint.collectors.worldmonitor import WorldMonitorCollector, WorldMonitorConfig
from backend.osint.models.evidence import (
    EvidenceBundle,
    HTTPTranscriptReceipt,
    HealthStatus,
    WMDomain,
)


@pytest.fixture
def live_config() -> WorldMonitorConfig:
    """Config using env var or default base URL."""
    return WorldMonitorConfig(timeout_s=15.0, retry_count=1, retry_delay_s=0.5)


@pytest.mark.live_wm
class TestLiveWorldMonitor:
    """Live tests against a running WorldMonitor instance."""

    @pytest.mark.asyncio
    async def test_live_health_check(self, live_config: WorldMonitorConfig) -> None:
        """GET /health returns HEALTHY or DEGRADED (not UNAVAILABLE)."""
        collector = WorldMonitorCollector(domain=WMDomain.INTELLIGENCE, config=live_config)
        status = await collector.health_check()
        assert status in (HealthStatus.HEALTHY, HealthStatus.DEGRADED), (
            f"Expected HEALTHY or DEGRADED, got {status}"
        )

    @pytest.mark.asyncio
    async def test_live_cii_collection(self, live_config: WorldMonitorConfig) -> None:
        """POST /api/v1/intelligence/cii produces valid EvidenceBundle."""
        collector = WorldMonitorCollector(domain=WMDomain.INTELLIGENCE, config=live_config)
        result = await collector.fetch(
            request={"theatre_id": "test-live", "query": "global"},
            theatre_id="test-live",
        )
        assert result.success is True
        assert result.bundle is not None
        assert isinstance(result.bundle, EvidenceBundle)
        assert result.bundle.source_id == "worldmonitor_cii"

    @pytest.mark.asyncio
    async def test_live_market_collection(self, live_config: WorldMonitorConfig) -> None:
        """POST /api/v1/market/snapshot produces valid EvidenceBundle."""
        collector = WorldMonitorCollector(domain=WMDomain.MARKET, config=live_config)
        result = await collector.fetch(
            request={"theatre_id": "test-live", "query": "global"},
            theatre_id="test-live",
        )
        assert result.success is True
        assert result.bundle is not None
        assert isinstance(result.bundle, EvidenceBundle)
        assert result.bundle.source_id == "worldmonitor_finance"

    @pytest.mark.asyncio
    async def test_live_maritime_collection(self, live_config: WorldMonitorConfig) -> None:
        """POST /api/v1/maritime/anomaly produces valid EvidenceBundle."""
        collector = WorldMonitorCollector(domain=WMDomain.MARITIME, config=live_config)
        result = await collector.fetch(
            request={"theatre_id": "test-live", "query": "global"},
            theatre_id="test-live",
        )
        assert result.success is True
        assert result.bundle is not None
        assert isinstance(result.bundle, EvidenceBundle)
        assert result.bundle.source_id == "worldmonitor_maritime"

    @pytest.mark.asyncio
    async def test_live_hash_invariants(self, live_config: WorldMonitorConfig) -> None:
        """Hash invariants hold on live response: content_hash == SHA-256(raw_payload)."""
        collector = WorldMonitorCollector(domain=WMDomain.INTELLIGENCE, config=live_config)
        result = await collector.fetch(
            request={"theatre_id": "test-live", "query": "global"},
            theatre_id="test-live",
        )
        assert result.success is True
        assert result.bundle is not None

        expected_hash = hashlib.sha256(result.raw_payload).hexdigest()
        assert result.bundle.receipt.content_hash == expected_hash

    @pytest.mark.asyncio
    async def test_live_receipt_structure(self, live_config: WorldMonitorConfig) -> None:
        """HTTPTranscriptReceipt fields populated from real HTTP exchange."""
        collector = WorldMonitorCollector(domain=WMDomain.INTELLIGENCE, config=live_config)
        result = await collector.fetch(
            request={"theatre_id": "test-live", "query": "global"},
            theatre_id="test-live",
        )
        assert result.success is True
        assert result.bundle is not None

        receipt = result.bundle.receipt
        assert isinstance(receipt, HTTPTranscriptReceipt)
        assert receipt.content_hash, "content_hash must be non-empty"
        assert receipt.receipt_hash, "receipt_hash must be non-empty"
        assert receipt.request_parameters.get("method") == "POST"
        assert "/api/v1/intelligence/cii" in receipt.request_parameters.get("url", "")
        assert receipt.http_status == 200
