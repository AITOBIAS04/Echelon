"""Cycle 026b Sprint 2 — Semantic Scholar Live Collector tests.

Tests:
1. Collector source_id and registration
2. Missing paper_id returns failure
3. Successful fetch builds correct bundle shape
4. API key redaction in receipt provenance
5. Error response handling (API error, HTTP error, malformed JSON)
6. Policy confirms semantic-scholar remains live-only
7. Collector map includes semantic_scholar_api
"""
from __future__ import annotations

import json
from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest

from backend.osint.collectors.semantic_scholar import (
    SemanticScholarCollector,
    _FIELDS,
)
from backend.osint.models.evidence import HealthStatus
from backend.services.eval_asset_policy import AssetDisposition, classify_asset, is_r2_eligible


# ── Fixtures ─────────────────────────────────────────────────────────

def _make_paper_response(
    paper_id: str = "abc123",
    title: str = "Test Paper",
    year: int = 2024,
    citation_count: int = 42,
    influential_count: int = 5,
) -> bytes:
    """Build a realistic Semantic Scholar paper response."""
    return json.dumps({
        "paperId": paper_id,
        "title": title,
        "year": year,
        "citationCount": citation_count,
        "influentialCitationCount": influential_count,
        "tldr": {"model": "tldr@v2", "text": "A test paper about testing."},
        "authors": [{"authorId": "1", "name": "Test Author"}],
    }).encode()


def _make_error_response(msg: str = "Paper not found") -> bytes:
    """Build a Semantic Scholar error response."""
    return json.dumps({"error": msg}).encode()


# ── Tests ────────────────────────────────────────────────────────────

class TestCollectorIdentity:
    """Test 1: source_id and basic construction."""

    def test_source_id(self):
        collector = SemanticScholarCollector(api_key="test-key")
        assert collector.source_id() == "semantic_scholar_api"

    def test_no_api_key_still_constructs(self):
        """Collector works without API key (lower rate limit)."""
        collector = SemanticScholarCollector(api_key="")
        assert collector.source_id() == "semantic_scholar_api"


class TestMissingPaperId:
    """Test 2: missing paper_id returns failure."""

    @pytest.mark.asyncio
    async def test_missing_paper_id(self):
        collector = SemanticScholarCollector(api_key="test-key")
        result = await collector._fetch({}, "theatre-1")
        assert result.success is False
        assert "paper_id" in result.error

    @pytest.mark.asyncio
    async def test_empty_paper_id(self):
        collector = SemanticScholarCollector(api_key="test-key")
        result = await collector._fetch({"paper_id": ""}, "theatre-1")
        assert result.success is False
        assert "paper_id" in result.error


class TestSuccessfulFetch:
    """Test 3: successful fetch builds correct bundle shape."""

    @pytest.mark.asyncio
    async def test_successful_fetch_bundle_shape(self):
        raw = _make_paper_response(
            paper_id="abc123", title="Attention Is All You Need",
            citation_count=100000, influential_count=5000,
        )
        collector = SemanticScholarCollector(api_key="test-key")

        with patch.object(collector, "_do_http_get", new_callable=AsyncMock, return_value=raw):
            result = await collector.fetch({"paper_id": "abc123"}, "theatre-1")

        assert result.success is True
        assert result.bundle is not None
        assert result.bundle.source_id == "semantic_scholar_api"
        assert result.bundle.source_group == "research_evidence"
        assert result.bundle.normalised_event is not None

        event = result.bundle.normalised_event
        assert event.measure.value == 100000.0
        assert event.measure.unit == "citations"
        assert event.measure.metadata["paper_id"] == "abc123"
        assert event.measure.metadata["title"] == "Attention Is All You Need"
        assert event.measure.metadata["influential_citations"] == 5000

    @pytest.mark.asyncio
    async def test_content_hash_present(self):
        raw = _make_paper_response()
        collector = SemanticScholarCollector(api_key="test-key")

        with patch.object(collector, "_do_http_get", new_callable=AsyncMock, return_value=raw):
            result = await collector.fetch({"paper_id": "abc123"}, "theatre-1")

        assert result.success is True
        assert len(result.bundle.receipt.content_hash) == 64
        assert result.bundle.receipt.receipt_hash is not None

    @pytest.mark.asyncio
    async def test_event_id_contains_paper_id(self):
        raw = _make_paper_response()
        collector = SemanticScholarCollector(api_key="test-key")

        with patch.object(collector, "_do_http_get", new_callable=AsyncMock, return_value=raw):
            result = await collector.fetch({"paper_id": "abc123"}, "theatre-1")

        assert "abc123" in result.bundle.normalised_event.event_id


class TestApiKeyRedaction:
    """Test 4: API key is redacted in receipt provenance."""

    @pytest.mark.asyncio
    async def test_api_key_not_in_receipt(self):
        """The API key must never appear in the receipt's request parameters."""
        raw = _make_paper_response()
        secret_key = "super-secret-s2-key-12345"
        collector = SemanticScholarCollector(api_key=secret_key)

        with patch.object(collector, "_do_http_get", new_callable=AsyncMock, return_value=raw):
            result = await collector.fetch({"paper_id": "abc123"}, "theatre-1")

        assert result.success is True
        receipt = result.bundle.receipt
        params = receipt.request_parameters

        # Key must not appear in any parameter field
        for key, value in params.items():
            assert secret_key not in str(value), f"API key leaked in receipt.{key}"

    @pytest.mark.asyncio
    async def test_receipt_headers_safe(self):
        """Receipt headers should be redacted (accept only, no x-api-key)."""
        raw = _make_paper_response()
        collector = SemanticScholarCollector(api_key="test-key")

        with patch.object(collector, "_do_http_get", new_callable=AsyncMock, return_value=raw):
            result = await collector.fetch({"paper_id": "abc123"}, "theatre-1")

        headers_str = result.bundle.receipt.request_parameters["headers"]
        assert "x-api-key" not in headers_str
        assert "accept:application/json" in headers_str


class TestErrorHandling:
    """Test 5: error response handling."""

    @pytest.mark.asyncio
    async def test_api_error_response(self):
        """Semantic Scholar error JSON is handled gracefully."""
        raw = _make_error_response("Paper not found")
        collector = SemanticScholarCollector(api_key="test-key")

        with patch.object(collector, "_do_http_get", new_callable=AsyncMock, return_value=raw):
            result = await collector.fetch({"paper_id": "bad-id"}, "theatre-1")

        assert result.success is False
        assert "Paper not found" in result.error

    @pytest.mark.asyncio
    async def test_malformed_json_response(self):
        """Non-JSON response is handled gracefully."""
        collector = SemanticScholarCollector(api_key="test-key")

        with patch.object(
            collector, "_do_http_get",
            new_callable=AsyncMock,
            return_value=b"<html>Not Found</html>",
        ):
            result = await collector.fetch({"paper_id": "abc123"}, "theatre-1")

        assert result.success is False
        assert "Malformed" in result.error

    @pytest.mark.asyncio
    async def test_http_error(self):
        """HTTP errors are caught and surfaced."""
        import urllib.error
        collector = SemanticScholarCollector(api_key="test-key")

        async def raise_http_error(url):
            raise urllib.error.HTTPError(url, 429, "Too Many Requests", {}, None)

        with patch.object(collector, "_do_http_get", side_effect=raise_http_error):
            result = await collector.fetch({"paper_id": "abc123"}, "theatre-1")

        assert result.success is False
        assert "429" in result.error


class TestPolicyCompliance:
    """Test 6: policy confirms semantic-scholar remains live-only."""

    def test_semantic_scholar_is_live_only(self):
        assert classify_asset("semantic-scholar") == AssetDisposition.LIVE

    def test_semantic_scholar_not_r2_eligible(self):
        assert is_r2_eligible("semantic-scholar") is False


class TestCollectorMapRegistration:
    """Test 7: collector map includes semantic_scholar_api."""

    def test_semantic_scholar_in_collector_map(self):
        from backend.osint.collectors.collector_map import build_collector_map
        cmap = build_collector_map()
        assert "semantic_scholar_api" in cmap

    def test_collector_map_count_increased(self):
        """Collector map now has 15 entries (14 original + semantic_scholar)."""
        from backend.osint.collectors.collector_map import build_collector_map
        cmap = build_collector_map()
        assert len(cmap) >= 15


class TestRegistrySourceOfTruth:
    """Test 8: semantic_scholar_api exists in sources.json and validates."""

    def test_registry_loader_finds_semantic_scholar(self):
        """RegistryLoader can resolve semantic_scholar_api from sources.json."""
        from pathlib import Path
        from backend.osint.models.registry import RegistryLoader

        sources_path = Path(__file__).resolve().parents[1] / "osint" / "sources.json"
        loader = RegistryLoader(str(sources_path))
        source = loader.get_source("semantic_scholar_api")

        assert source is not None
        assert source.source_id == "semantic_scholar_api"
        assert source.source_group == "research_evidence"
        assert source.resolution_role == "primary_evidence"
        assert source.independence_upstream_id == "semantic_scholar"
        assert source.receipt_mode_minimum == "http_transcript"

    def test_registry_validates_with_semantic_scholar(self):
        """Full registry validation passes with research_evidence group."""
        from pathlib import Path
        from backend.osint.models.registry import RegistryLoader

        sources_path = Path(__file__).resolve().parents[1] / "osint" / "sources.json"
        loader = RegistryLoader(str(sources_path))
        errors = loader.validate()
        assert errors == [], f"Registry validation errors: {errors}"

    def test_research_evidence_in_valid_groups(self):
        """research_evidence is in _VALID_SOURCE_GROUPS."""
        from backend.osint.models.registry import _VALID_SOURCE_GROUPS
        assert "research_evidence" in _VALID_SOURCE_GROUPS

    def test_sources_json_has_17_entries(self):
        """sources.json now has 17 entries (16 original + semantic_scholar)."""
        from pathlib import Path
        from backend.osint.models.registry import RegistryLoader

        sources_path = Path(__file__).resolve().parents[1] / "osint" / "sources.json"
        loader = RegistryLoader(str(sources_path))
        assert len(loader.sources) >= 17
