"""Tests for FRED, BoE, and Gazette collectors.

Tests: init validation, build_request, extract, mock HTTP responses,
error mapping via BaseCollector.
"""

from __future__ import annotations

import json
from typing import Any

import httpx
import pytest

from osint_pipeline.collectors.fred import FREDCollector
from osint_pipeline.collectors.boe import BoECollector
from osint_pipeline.collectors.gazette import GazetteCollector
from osint_pipeline.models.evidence import CollectionStatus


# ---------------------------------------------------------------------------
# FRED Tests
# ---------------------------------------------------------------------------

class TestFREDInit:
    """Test FRED collector initialisation."""

    def test_requires_api_key(self):
        with pytest.raises(ValueError, match="API key"):
            FREDCollector(config={})

    def test_empty_api_key_raises(self):
        with pytest.raises(ValueError, match="API key"):
            FREDCollector(config={"api_key": ""})

    def test_valid_config(self):
        c = FREDCollector(config={"api_key": "test_key_123"})
        assert c.source_id == "fred_api"
        assert c.jurisdiction == "US"
        assert c.source_group == "market_data"
        assert c.resolution_role == "secondary_corroboration"
        assert c.independence_upstream_id == "us_stlouisfed_fred_backend"


class TestFREDBuildRequest:
    """Test FRED request construction."""

    def test_basic_request(self):
        c = FREDCollector(config={"api_key": "key123"})
        method, url, headers, params = c.build_request({"series_id": "GDP"})
        assert method == "GET"
        assert "stlouisfed.org" in url
        assert params["series_id"] == "GDP"
        assert params["api_key"] == "key123"
        assert params["file_type"] == "json"

    def test_with_date_range(self):
        c = FREDCollector(config={"api_key": "key123"})
        _, _, _, params = c.build_request({
            "series_id": "GDP",
            "observation_start": "2025-01-01",
            "observation_end": "2025-12-31",
        })
        assert params["observation_start"] == "2025-01-01"
        assert params["observation_end"] == "2025-12-31"

    def test_missing_series_id_raises(self):
        c = FREDCollector(config={"api_key": "key123"})
        with pytest.raises(ValueError, match="series_id"):
            c.build_request({})


class TestFREDExtract:
    """Test FRED response extraction."""

    def test_extract_with_observations(self):
        c = FREDCollector(config={"api_key": "key123"})
        response = {
            "count": 3,
            "observations": [
                {"date": "2025-01-01", "value": "22000.0",
                 "realtime_start": "2025-01-15", "realtime_end": "2025-01-15"},
                {"date": "2024-10-01", "value": "21500.0",
                 "realtime_start": "2025-01-15", "realtime_end": "2025-01-15"},
            ],
        }
        extract, confidence = c.extract(
            json.dumps(response).encode(), 200, {"series_id": "GDP"}
        )
        assert extract["total_observations"] == 3
        assert len(extract["observations"]) == 2
        assert confidence == 1.0

    def test_extract_empty(self):
        c = FREDCollector(config={"api_key": "key123"})
        response = {"count": 0, "observations": []}
        extract, confidence = c.extract(
            json.dumps(response).encode(), 200, {"series_id": "GDP"}
        )
        assert extract["total_observations"] == 0
        assert confidence == 0.5

    def test_extract_non_200(self):
        c = FREDCollector(config={"api_key": "key123"})
        extract, confidence = c.extract(b"error", 401, {"series_id": "GDP"})
        assert confidence == 0.0


class TestFREDCollect:
    """Test FRED full collect cycle with mock HTTP."""

    def test_collect_success(self):
        response_body = json.dumps({
            "count": 2,
            "observations": [
                {"date": "2025-01-01", "value": "22000.0"},
            ],
        }).encode()

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, content=response_body)

        c = FREDCollector(config={"api_key": "key123"})
        c._client = httpx.Client(transport=httpx.MockTransport(handler))
        result = c.collect({"series_id": "GDP"})
        assert result.succeeded
        assert result.bundle.source_id == "fred_api"

    def test_collect_auth_failure(self):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(401, content=b"bad key")

        c = FREDCollector(config={"api_key": "bad_key"})
        c._client = httpx.Client(transport=httpx.MockTransport(handler))
        result = c.collect({"series_id": "GDP"})
        assert not result.succeeded
        assert result.status == CollectionStatus.AUTH_FAILURE


# ---------------------------------------------------------------------------
# BoE Tests
# ---------------------------------------------------------------------------

class TestBoEInit:
    """Test BoE collector initialisation."""

    def test_no_config_required(self):
        c = BoECollector()
        assert c.source_id == "boe_rates"
        assert c.jurisdiction == "GB"
        assert c.source_group == "market_data"
        assert c.resolution_role == "primary_evidence"
        assert c.independence_upstream_id == "uk_boe_statistics_backend"


class TestBoEBuildRequest:
    """Test BoE request construction."""

    def test_basic_request(self):
        c = BoECollector()
        method, url, headers, params = c.build_request({
            "series_code": "IUDBEDR",
        })
        assert method == "GET"
        assert "bankofengland.co.uk" in url
        assert "IUDBEDR.json" in url

    def test_with_date_range(self):
        c = BoECollector()
        _, _, _, params = c.build_request({
            "series_code": "IUDBEDR",
            "from_date": "01/Jan/2025",
            "to_date": "31/Dec/2025",
        })
        assert params["from"] == "01/Jan/2025"
        assert params["to"] == "31/Dec/2025"

    def test_missing_series_code_raises(self):
        c = BoECollector()
        with pytest.raises(ValueError, match="series_code"):
            c.build_request({})


class TestBoEExtract:
    """Test BoE response extraction."""

    def test_extract_with_observations(self):
        c = BoECollector()
        response = {
            "datasets": [{
                "observations": [
                    {"date": "2025-01-01", "value": "4.75", "status": "A"},
                    {"date": "2025-02-01", "value": "4.50", "status": "A"},
                ],
            }],
        }
        extract, confidence = c.extract(
            json.dumps(response).encode(), 200, {"series_code": "IUDBEDR"}
        )
        assert extract["observation_count"] == 2
        assert confidence == 1.0

    def test_extract_empty(self):
        c = BoECollector()
        response = {"datasets": [{"observations": []}]}
        extract, confidence = c.extract(
            json.dumps(response).encode(), 200, {"series_code": "X"}
        )
        assert extract["observation_count"] == 0
        assert confidence == 0.5


class TestBoECollect:
    """Test BoE full collect cycle with mock HTTP."""

    def test_collect_success(self):
        response_body = json.dumps({
            "datasets": [{
                "observations": [{"date": "2025-01-01", "value": "4.75"}],
            }],
        }).encode()

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, content=response_body)

        c = BoECollector()
        c._client = httpx.Client(transport=httpx.MockTransport(handler))
        result = c.collect({"series_code": "IUDBEDR"})
        assert result.succeeded
        assert result.bundle.source_id == "boe_rates"

    def test_collect_server_error(self):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(500, content=b"error")

        c = BoECollector()
        c._client = httpx.Client(transport=httpx.MockTransport(handler))
        result = c.collect({"series_code": "X"})
        assert not result.succeeded
        assert result.status == CollectionStatus.SOURCE_ERROR


# ---------------------------------------------------------------------------
# Gazette Tests
# ---------------------------------------------------------------------------

class TestGazetteInit:
    """Test Gazette collector initialisation."""

    def test_no_config_required(self):
        c = GazetteCollector()
        assert c.source_id == "uk_gazette"
        assert c.jurisdiction == "GB"
        assert c.source_group == "official_gov"
        assert c.resolution_role == "primary_evidence"
        assert c.independence_upstream_id == "uk_tso_gazette_backend"


class TestGazetteBuildRequest:
    """Test Gazette request construction."""

    def test_basic_request(self):
        c = GazetteCollector()
        method, url, headers, params = c.build_request({
            "search_term": "ACME Corp",
        })
        assert method == "GET"
        assert "thegazette.co.uk" in url
        assert params["q"] == "ACME Corp"
        assert params["edition"] == "london"

    def test_with_notice_type(self):
        c = GazetteCollector()
        _, _, _, params = c.build_request({
            "search_term": "ACME",
            "notice_type": "insolvency",
        })
        assert params["categorycode"] == "insolvency"

    def test_custom_edition(self):
        c = GazetteCollector()
        _, _, _, params = c.build_request({
            "search_term": "test",
            "edition": "edinburgh",
        })
        assert params["edition"] == "edinburgh"

    def test_missing_search_term_raises(self):
        c = GazetteCollector()
        with pytest.raises(ValueError, match="search_term"):
            c.build_request({})


class TestGazetteExtract:
    """Test Gazette response extraction."""

    def test_extract_with_notices(self):
        c = GazetteCollector()
        response = {
            "total": 3,
            "results": [
                {
                    "id": "12345",
                    "title": "ACME Corp",
                    "notice-type": "corporate",
                    "published-date": "2025-03-01",
                    "edition": "london",
                },
            ],
        }
        extract, confidence = c.extract(
            json.dumps(response).encode(), 200, {"search_term": "ACME"}
        )
        assert extract["total_results"] == 3
        assert len(extract["notices"]) == 1
        assert confidence == 1.0

    def test_extract_with_insolvency_notice(self):
        c = GazetteCollector()
        response = {
            "total": 1,
            "results": [
                {
                    "id": "99999",
                    "title": "Winding Up",
                    "notice-type": "insolvency",
                    "published-date": "2025-03-01",
                },
            ],
        }
        extract, confidence = c.extract(
            json.dumps(response).encode(), 200, {"search_term": "test"}
        )
        assert extract["counter_signal_detected"] is True
        assert "Insolvency" in extract["counter_signal_detail"]

    def test_extract_no_results(self):
        c = GazetteCollector()
        response = {"total": 0, "results": []}
        extract, confidence = c.extract(
            json.dumps(response).encode(), 200, {"search_term": "xxxxx"}
        )
        assert extract["total_results"] == 0
        assert confidence == 0.5

    def test_extract_invalid_json(self):
        c = GazetteCollector()
        extract, confidence = c.extract(
            b"not json", 200, {"search_term": "x"}
        )
        assert "error" in extract
        assert confidence == 0.0


class TestGazetteCollect:
    """Test Gazette full collect cycle with mock HTTP."""

    def test_collect_success(self):
        response_body = json.dumps({
            "total": 2,
            "results": [{"id": "1", "title": "Test Notice"}],
        }).encode()

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, content=response_body)

        c = GazetteCollector()
        c._client = httpx.Client(transport=httpx.MockTransport(handler))
        result = c.collect({"search_term": "test"})
        assert result.succeeded
        assert result.bundle.source_id == "uk_gazette"

    def test_collect_not_found(self):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(404, content=b"not found")

        c = GazetteCollector()
        c._client = httpx.Client(transport=httpx.MockTransport(handler))
        result = c.collect({"search_term": "xxx"})
        assert not result.succeeded
        assert result.status == CollectionStatus.NOT_FOUND


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
