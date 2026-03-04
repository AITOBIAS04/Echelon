"""Companies House collector tests — mock and live.

Mock tests always run. Live tests gated behind @pytest.mark.live_ch.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from backend.osint.collectors.companies_house import CompaniesHouseCollector
from backend.osint.models.evidence import EvidenceBundle, HTTPTranscriptReceipt, HealthStatus

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _ch_fixture_bytes() -> bytes:
    """Load Companies House mock response as raw bytes."""
    with open(FIXTURES_DIR / "ch_company_profile.json", "rb") as f:
        return f.read()


@pytest.fixture
def ch_collector() -> CompaniesHouseCollector:
    """CH collector with test API key."""
    return CompaniesHouseCollector(api_key="test-api-key")


class TestCompaniesHouseMock:
    """Mock tests — always run, no API key required."""

    @pytest.mark.asyncio
    async def test_ch_collection_success(self, ch_collector: CompaniesHouseCollector) -> None:
        """Mock response produces valid EvidenceBundle."""
        fixture_bytes = _ch_fixture_bytes()

        with patch.object(ch_collector, "_do_http_get", return_value=fixture_bytes):
            result = await ch_collector.fetch(
                request={"company_number": "00000006"},
                theatre_id="test-theatre",
            )

        assert result.success is True
        assert result.bundle is not None
        assert isinstance(result.bundle, EvidenceBundle)
        assert result.bundle.source_id == "companies_house_api"
        assert result.bundle.source_group == "official_gov"
        assert result.bundle.resolution_role == "primary_evidence"
        assert result.bundle.normalised_event.confidence == 1.0

    @pytest.mark.asyncio
    async def test_ch_hash_invariants(self, ch_collector: CompaniesHouseCollector) -> None:
        """content_hash == SHA-256(raw_payload) on mock response."""
        fixture_bytes = _ch_fixture_bytes()

        with patch.object(ch_collector, "_do_http_get", return_value=fixture_bytes):
            result = await ch_collector.fetch(
                request={"company_number": "00000006"},
                theatre_id="test-theatre",
            )

        assert result.success is True
        expected_hash = hashlib.sha256(fixture_bytes).hexdigest()
        assert result.bundle.receipt.content_hash == expected_hash

    @pytest.mark.asyncio
    async def test_ch_receipt_structure(self, ch_collector: CompaniesHouseCollector) -> None:
        """HTTPTranscriptReceipt fields populated correctly."""
        fixture_bytes = _ch_fixture_bytes()

        with patch.object(ch_collector, "_do_http_get", return_value=fixture_bytes):
            result = await ch_collector.fetch(
                request={"company_number": "00000006"},
                theatre_id="test-theatre",
            )

        assert result.success is True
        receipt = result.bundle.receipt
        assert isinstance(receipt, HTTPTranscriptReceipt)
        assert receipt.request_parameters["method"] == "GET"
        assert "/company/00000006" in receipt.request_parameters["url"]
        assert receipt.content_hash, "content_hash must be non-empty"
        assert receipt.receipt_hash, "receipt_hash must be non-empty"
        assert receipt.http_status == 200

    @pytest.mark.asyncio
    async def test_ch_no_api_key(self) -> None:
        """No API key produces success=False without raising."""
        collector = CompaniesHouseCollector(api_key="")
        result = await collector.fetch(
            request={"company_number": "00000006"},
            theatre_id="test-theatre",
        )
        assert result.success is False
        assert "No API key" in result.error

    @pytest.mark.asyncio
    async def test_ch_404_company(self, ch_collector: CompaniesHouseCollector) -> None:
        """Unknown company number produces success=False."""
        import urllib.error

        with patch.object(
            ch_collector,
            "_do_http_get",
            side_effect=urllib.error.HTTPError(
                url="https://api.company-information.service.gov.uk/company/99999999",
                code=404,
                msg="Not Found",
                hdrs=None,
                fp=None,
            ),
        ):
            result = await ch_collector.fetch(
                request={"company_number": "99999999"},
                theatre_id="test-theatre",
            )

        assert result.success is False
        assert "404" in result.error


@pytest.mark.live_ch
class TestCompaniesHouseLive:
    """Live tests — require API key and --live-ch flag."""

    @pytest.mark.asyncio
    async def test_live_ch_company_profile(self) -> None:
        """Real API returns valid EvidenceBundle for known company."""
        collector = CompaniesHouseCollector()  # Uses env var
        result = await collector.fetch(
            request={"company_number": "00000006"},
            theatre_id="test-live",
        )
        assert result.success is True, f"Live CH failed: {result.error}"
        assert result.bundle is not None
        assert isinstance(result.bundle, EvidenceBundle)
        assert result.bundle.source_id == "companies_house_api"

    @pytest.mark.asyncio
    async def test_live_ch_hash_invariants(self) -> None:
        """Hash invariants on real response."""
        collector = CompaniesHouseCollector()
        result = await collector.fetch(
            request={"company_number": "00000006"},
            theatre_id="test-live",
        )
        assert result.success is True, f"Live CH failed: {result.error}"
        expected_hash = hashlib.sha256(result.raw_payload).hexdigest()
        assert result.bundle.receipt.content_hash == expected_hash
