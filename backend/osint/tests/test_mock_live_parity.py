"""Mock-to-live parity verification — structural equality between mock and live paths.

All tests gated behind @pytest.mark.live_wm. Skipped by default.
Verifies that mock fixtures produce structurally identical EvidenceBundle
to live HTTP responses — same Python types, same field set, same receipt structure.
Does NOT assert value equality (live data differs from fixtures).
"""
from __future__ import annotations

from unittest.mock import patch

import pytest

from backend.osint.collectors.worldmonitor import WorldMonitorCollector, WorldMonitorConfig
from backend.osint.models.evidence import EvidenceBundle, HTTPTranscriptReceipt, WMDomain
from backend.osint.tests.conftest import _fixture_bytes


def _field_set(obj) -> set[str]:
    """Extract field names from a dataclass or Pydantic model."""
    if hasattr(obj, "__dataclass_fields__"):
        return set(obj.__dataclass_fields__.keys())
    if hasattr(obj, "model_fields"):
        return set(obj.model_fields.keys())
    return set(vars(obj).keys())


_DOMAIN_FIXTURES = {
    WMDomain.INTELLIGENCE: "wm_cii_response.json",
    WMDomain.MARKET: "wm_market_response.json",
    WMDomain.MARITIME: "wm_maritime_response.json",
}


async def _collect_mock(domain: WMDomain) -> tuple:
    """Run collector with mocked HTTP, return (result, raw_bytes)."""
    fixture_bytes = _fixture_bytes(_DOMAIN_FIXTURES[domain])
    config = WorldMonitorConfig(
        base_url="http://mock:8080", timeout_s=5.0, retry_count=0,
    )
    collector = WorldMonitorCollector(domain=domain, config=config)

    with patch.object(collector, "_do_http_post", return_value=fixture_bytes):
        result = await collector.fetch(
            request={"theatre_id": "parity-test"},
            theatre_id="parity-test",
        )
    return result


async def _collect_live(domain: WMDomain) -> tuple:
    """Run collector against live WM instance."""
    config = WorldMonitorConfig(timeout_s=15.0, retry_count=1, retry_delay_s=0.5)
    collector = WorldMonitorCollector(domain=domain, config=config)
    result = await collector.fetch(
        request={"theatre_id": "parity-test"},
        theatre_id="parity-test",
    )
    return result


@pytest.mark.live_wm
class TestMockLiveParity:
    """Verify structural parity between mock and live collection paths."""

    @pytest.mark.asyncio
    async def test_cii_mock_live_parity(self) -> None:
        """CII: mock and live produce structurally identical EvidenceBundle."""
        mock_result = await _collect_mock(WMDomain.INTELLIGENCE)
        live_result = await _collect_live(WMDomain.INTELLIGENCE)

        assert mock_result.success is True, f"Mock failed: {mock_result.error}"
        assert live_result.success is True, f"Live failed: {live_result.error}"

        # Same bundle type
        assert type(mock_result.bundle) is type(live_result.bundle)
        assert isinstance(live_result.bundle, EvidenceBundle)

        # Same field set
        assert _field_set(mock_result.bundle) == _field_set(live_result.bundle)

        # Same receipt type and field set
        assert type(mock_result.bundle.receipt) is type(live_result.bundle.receipt)
        assert isinstance(live_result.bundle.receipt, HTTPTranscriptReceipt)
        assert _field_set(mock_result.bundle.receipt) == _field_set(live_result.bundle.receipt)

        # Same normalised_event type and field set
        assert type(mock_result.bundle.normalised_event) is type(live_result.bundle.normalised_event)
        assert _field_set(mock_result.bundle.normalised_event) == _field_set(live_result.bundle.normalised_event)

    @pytest.mark.asyncio
    async def test_market_mock_live_parity(self) -> None:
        """Market: mock and live produce structurally identical EvidenceBundle."""
        mock_result = await _collect_mock(WMDomain.MARKET)
        live_result = await _collect_live(WMDomain.MARKET)

        assert mock_result.success is True, f"Mock failed: {mock_result.error}"
        assert live_result.success is True, f"Live failed: {live_result.error}"

        assert type(mock_result.bundle) is type(live_result.bundle)
        assert _field_set(mock_result.bundle) == _field_set(live_result.bundle)
        assert type(mock_result.bundle.receipt) is type(live_result.bundle.receipt)
        assert _field_set(mock_result.bundle.receipt) == _field_set(live_result.bundle.receipt)
        assert type(mock_result.bundle.normalised_event) is type(live_result.bundle.normalised_event)
        assert _field_set(mock_result.bundle.normalised_event) == _field_set(live_result.bundle.normalised_event)

    @pytest.mark.asyncio
    async def test_maritime_mock_live_parity(self) -> None:
        """Maritime: mock and live produce structurally identical EvidenceBundle."""
        mock_result = await _collect_mock(WMDomain.MARITIME)
        live_result = await _collect_live(WMDomain.MARITIME)

        assert mock_result.success is True, f"Mock failed: {mock_result.error}"
        assert live_result.success is True, f"Live failed: {live_result.error}"

        assert type(mock_result.bundle) is type(live_result.bundle)
        assert _field_set(mock_result.bundle) == _field_set(live_result.bundle)
        assert type(mock_result.bundle.receipt) is type(live_result.bundle.receipt)
        assert _field_set(mock_result.bundle.receipt) == _field_set(live_result.bundle.receipt)
        assert type(mock_result.bundle.normalised_event) is type(live_result.bundle.normalised_event)
        assert _field_set(mock_result.bundle.normalised_event) == _field_set(live_result.bundle.normalised_event)
