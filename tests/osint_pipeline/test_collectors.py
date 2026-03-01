"""Tests for SEC EDGAR and ECB collectors.

Tests: init validation, build_request, extract, mock HTTP responses,
error mapping via BaseCollector.
"""

from __future__ import annotations

import json
from typing import Any

import httpx
import pytest

from osint_pipeline.collectors.sec_edgar import SECEdgarCollector
from osint_pipeline.collectors.ecb_sdmx import ECBDataCollector
from osint_pipeline.models.evidence import CollectionStatus


# ---------------------------------------------------------------------------
# SEC EDGAR Tests
# ---------------------------------------------------------------------------

class TestSECEdgarInit:
    """Test SEC EDGAR collector initialisation."""

    def test_requires_user_agent(self):
        with pytest.raises(ValueError, match="User-Agent"):
            SECEdgarCollector(config={})

    def test_empty_user_agent_raises(self):
        with pytest.raises(ValueError, match="User-Agent"):
            SECEdgarCollector(config={"user_agent": ""})

    def test_valid_config(self):
        c = SECEdgarCollector(config={"user_agent": "TestApp test@example.com"})
        assert c.source_id == "sec_edgar"
        assert c.jurisdiction == "US"
        assert c.source_group == "official_gov"
        assert c.resolution_role == "primary_evidence"
        assert c.independence_upstream_id == "us_sec_edgar_backend"


class TestSECEdgarBuildRequest:
    """Test SEC EDGAR request construction."""

    def test_basic_search(self):
        c = SECEdgarCollector(config={"user_agent": "App test@test.com"})
        method, url, headers, params = c.build_request({
            "search_query": "Apple Inc"
        })

        assert method == "GET"
        assert "efts.sec.gov" in url
        assert params["q"] == "Apple Inc"
        assert headers["User-Agent"] == "App test@test.com"

    def test_date_range(self):
        c = SECEdgarCollector(config={"user_agent": "App test@test.com"})
        _, _, _, params = c.build_request({
            "search_query": "Tesla",
            "date_from": "2025-01-01",
            "date_to": "2025-12-31",
        })

        assert params["dateRange"] == "custom"
        assert params["startdt"] == "2025-01-01"
        assert params["enddt"] == "2025-12-31"

    def test_form_type_filter(self):
        c = SECEdgarCollector(config={"user_agent": "App test@test.com"})
        _, _, _, params = c.build_request({
            "search_query": "AAPL",
            "form_type": "10-K",
        })

        assert params["forms"] == "10-K"

    def test_missing_search_query_raises(self):
        c = SECEdgarCollector(config={"user_agent": "App test@test.com"})
        with pytest.raises(ValueError, match="search_query"):
            c.build_request({})


class TestSECEdgarExtract:
    """Test SEC EDGAR response extraction."""

    def test_extract_with_hits(self):
        c = SECEdgarCollector(config={"user_agent": "App test@test.com"})
        response = {
            "hits": {
                "total": {"value": 42},
                "hits": [
                    {
                        "_source": {
                            "file_date": "2025-03-15",
                            "entity_name": "APPLE INC",
                            "form_type": "10-K",
                            "file_num": "0-12345",
                            "period_of_report": "2024-12-31",
                        }
                    }
                ],
            }
        }
        extract, confidence = c.extract(
            json.dumps(response).encode(), 200, {"search_query": "Apple"}
        )

        assert extract["total_hits"] == 42
        assert len(extract["filings"]) == 1
        assert extract["filings"][0]["entity_name"] == "APPLE INC"
        assert confidence == 1.0

    def test_extract_no_hits(self):
        c = SECEdgarCollector(config={"user_agent": "App test@test.com"})
        response = {"hits": {"total": {"value": 0}, "hits": []}}
        extract, confidence = c.extract(
            json.dumps(response).encode(), 200, {"search_query": "xxxxx"}
        )

        assert extract["total_hits"] == 0
        assert confidence == 0.5

    def test_extract_invalid_json(self):
        c = SECEdgarCollector(config={"user_agent": "App test@test.com"})
        extract, confidence = c.extract(b"not json", 200, {"search_query": "x"})
        assert "error" in extract
        assert confidence == 0.0

    def test_extract_non_200(self):
        c = SECEdgarCollector(config={"user_agent": "App test@test.com"})
        extract, confidence = c.extract(b"error", 500, {"search_query": "x"})
        assert confidence == 0.0


class TestSECEdgarCollect:
    """Test SEC EDGAR full collect cycle with mock HTTP."""

    def test_collect_success(self):
        response_body = json.dumps({
            "hits": {
                "total": {"value": 5},
                "hits": [{"_source": {"entity_name": "TEST"}}],
            }
        }).encode()

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, content=response_body)

        transport = httpx.MockTransport(handler)
        c = SECEdgarCollector(config={"user_agent": "App test@test.com"})
        c._client = httpx.Client(transport=transport)

        result = c.collect({"search_query": "TEST"})
        assert result.succeeded
        assert result.bundle.source_id == "sec_edgar"
        assert result.bundle.structured_extract["total_hits"] == 5

    def test_collect_rate_limited(self):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(429, content=b"rate limited")

        transport = httpx.MockTransport(handler)
        c = SECEdgarCollector(config={"user_agent": "App test@test.com"})
        c._client = httpx.Client(transport=transport)

        result = c.collect({"search_query": "TEST"})
        assert not result.succeeded
        assert result.status == CollectionStatus.RATE_LIMITED


# ---------------------------------------------------------------------------
# ECB Data API Tests
# ---------------------------------------------------------------------------

class TestECBDataInit:
    """Test ECB Data API collector initialisation."""

    def test_no_config_required(self):
        c = ECBDataCollector()
        assert c.source_id == "ecb_data_api"
        assert c.jurisdiction == "EU"
        assert c.source_group == "market_data"
        assert c.resolution_role == "primary_evidence"
        assert c.independence_upstream_id == "eu_ecb_sdw_backend"


class TestECBDataBuildRequest:
    """Test ECB Data API request construction."""

    def test_basic_request(self):
        c = ECBDataCollector()
        method, url, headers, params = c.build_request({
            "dataflow": "EXR",
            "series_key": "D.USD.EUR.SP00.A",
        })

        assert method == "GET"
        assert "data-api.ecb.europa.eu" in url
        assert "EXR/D.USD.EUR.SP00.A" in url
        assert params["format"] == "jsondata"

    def test_with_period(self):
        c = ECBDataCollector()
        _, _, _, params = c.build_request({
            "dataflow": "EXR",
            "series_key": "D.USD.EUR.SP00.A",
            "start_period": "2025-01-01",
            "end_period": "2025-12-31",
        })

        assert params["startPeriod"] == "2025-01-01"
        assert params["endPeriod"] == "2025-12-31"

    def test_missing_dataflow_raises(self):
        c = ECBDataCollector()
        with pytest.raises(ValueError, match="dataflow"):
            c.build_request({"series_key": "D.USD.EUR.SP00.A"})

    def test_missing_series_key_raises(self):
        c = ECBDataCollector()
        with pytest.raises(ValueError, match="series_key"):
            c.build_request({"dataflow": "EXR"})


class TestECBDataExtract:
    """Test ECB Data API response extraction."""

    def test_extract_with_observations(self):
        c = ECBDataCollector()
        response = {
            "dataSets": [{
                "series": {
                    "0:0:0:0:0": {
                        "observations": {
                            "0": [1.1234],
                            "1": [1.1256],
                        }
                    }
                }
            }],
            "structure": {"dimensions": {"observation": []}},
        }
        extract, confidence = c.extract(
            json.dumps(response).encode(),
            200,
            {"dataflow": "EXR", "series_key": "D.USD.EUR.SP00.A"},
        )

        assert extract["observation_count"] == 2
        assert len(extract["observations"]) == 2
        assert confidence == 1.0

    def test_extract_empty_response(self):
        c = ECBDataCollector()
        response = {"dataSets": [{"series": {}}], "structure": {}}
        extract, confidence = c.extract(
            json.dumps(response).encode(),
            200,
            {"dataflow": "EXR", "series_key": "D.USD.EUR.SP00.A"},
        )

        assert extract["observation_count"] == 0
        assert confidence == 0.5

    def test_extract_invalid_json(self):
        c = ECBDataCollector()
        extract, confidence = c.extract(
            b"not json", 200, {"dataflow": "EXR", "series_key": "x"}
        )
        assert "error" in extract
        assert confidence == 0.0


class TestECBDataCollect:
    """Test ECB Data API full collect cycle with mock HTTP."""

    def test_collect_success(self):
        response_body = json.dumps({
            "dataSets": [{
                "series": {
                    "0:0": {"observations": {"0": [1.23]}}
                }
            }],
            "structure": {"dimensions": {}},
        }).encode()

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, content=response_body)

        transport = httpx.MockTransport(handler)
        c = ECBDataCollector()
        c._client = httpx.Client(transport=transport)

        result = c.collect({"dataflow": "EXR", "series_key": "D.USD.EUR.SP00.A"})
        assert result.succeeded
        assert result.bundle.source_id == "ecb_data_api"
        assert result.bundle.structured_extract["observation_count"] == 1

    def test_collect_server_error(self):
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(500, content=b"error")

        transport = httpx.MockTransport(handler)
        c = ECBDataCollector()
        c._client = httpx.Client(transport=transport)

        result = c.collect({"dataflow": "EXR", "series_key": "x"})
        assert not result.succeeded
        assert result.status == CollectionStatus.SOURCE_ERROR


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
