"""Tests for oracle adapters."""

from __future__ import annotations

import json
from datetime import datetime, timezone

import httpx
import pytest
import respx

from echelon_verify.config import OracleConfig
from echelon_verify.models import GroundTruthRecord, OracleOutput
from echelon_verify.oracle.base import OracleAdapter
from echelon_verify.oracle.http_adapter import HttpOracleAdapter
from echelon_verify.oracle.python_adapter import PythonOracleAdapter


ORACLE_RESPONSE = {
    "summary": "This PR adds rate limiting.",
    "key_claims": ["Added rate limiting", "Uses token bucket"],
    "follow_up_response": "Returns 429 when limit exceeded.",
    "metadata": {"model": "test-oracle"},
}


class TestOracleAdapterFactory:
    def test_creates_http_adapter(self) -> None:
        config = OracleConfig(type="http", url="http://localhost:8000")
        adapter = OracleAdapter.from_config(config)
        assert isinstance(adapter, HttpOracleAdapter)

    def test_creates_python_adapter(self) -> None:
        config = OracleConfig(
            type="python", module="json", callable="dumps"
        )
        adapter = OracleAdapter.from_config(config)
        assert isinstance(adapter, PythonOracleAdapter)

    def test_unknown_type_raises(self) -> None:
        config = OracleConfig.__new__(OracleConfig)
        object.__setattr__(config, "type", "unknown")
        with pytest.raises(ValueError, match="Unknown oracle type"):
            OracleAdapter.from_config(config)


class TestHttpOracleAdapter:
    @pytest.fixture
    def adapter(self) -> HttpOracleAdapter:
        config = OracleConfig(type="http", url="http://localhost:8000/oracle")
        return HttpOracleAdapter(config)

    @respx.mock
    @pytest.mark.asyncio
    async def test_successful_invocation(
        self,
        adapter: HttpOracleAdapter,
        sample_ground_truth: GroundTruthRecord,
    ) -> None:
        respx.post("http://localhost:8000/oracle").mock(
            return_value=httpx.Response(200, json=ORACLE_RESPONSE)
        )

        result = await adapter.invoke(sample_ground_truth, "What changed?")

        assert isinstance(result, OracleOutput)
        assert result.ground_truth_id == "142"
        assert result.summary == "This PR adds rate limiting."
        assert len(result.key_claims) == 2
        assert result.follow_up_response == "Returns 429 when limit exceeded."
        assert result.latency_ms >= 0
        assert "error" not in result.metadata

    @respx.mock
    @pytest.mark.asyncio
    async def test_timeout_returns_error_output(
        self,
        adapter: HttpOracleAdapter,
        sample_ground_truth: GroundTruthRecord,
    ) -> None:
        respx.post("http://localhost:8000/oracle").mock(
            side_effect=httpx.ReadTimeout("timed out")
        )

        result = await adapter.invoke(sample_ground_truth, "Question?")

        assert result.metadata.get("error") == "timeout"
        assert result.summary == ""
        assert result.key_claims == []

    @respx.mock
    @pytest.mark.asyncio
    async def test_http_error_returns_error_output(
        self,
        adapter: HttpOracleAdapter,
        sample_ground_truth: GroundTruthRecord,
    ) -> None:
        respx.post("http://localhost:8000/oracle").mock(
            return_value=httpx.Response(500, text="Internal Server Error")
        )

        result = await adapter.invoke(sample_ground_truth, "Question?")

        assert "error" in result.metadata
        assert "HTTP 500" in result.metadata["error"]

    @respx.mock
    @pytest.mark.asyncio
    async def test_malformed_json_returns_error_output(
        self,
        adapter: HttpOracleAdapter,
        sample_ground_truth: GroundTruthRecord,
    ) -> None:
        respx.post("http://localhost:8000/oracle").mock(
            return_value=httpx.Response(200, text="not json")
        )

        result = await adapter.invoke(sample_ground_truth, "Question?")

        assert "error" in result.metadata
        assert "malformed response" in result.metadata["error"]

    @respx.mock
    @pytest.mark.asyncio
    async def test_custom_headers_sent(
        self,
        sample_ground_truth: GroundTruthRecord,
    ) -> None:
        config = OracleConfig(
            type="http",
            url="http://localhost:8000/oracle",
            headers={"X-Api-Key": "secret-key"},
        )
        adapter = HttpOracleAdapter(config)

        route = respx.post("http://localhost:8000/oracle").mock(
            return_value=httpx.Response(200, json=ORACLE_RESPONSE)
        )

        await adapter.invoke(sample_ground_truth, "Question?")

        assert route.called
        request = route.calls[0].request
        assert request.headers.get("x-api-key") == "secret-key"


class TestPythonOracleAdapter:
    @pytest.mark.asyncio
    async def test_sync_callable(
        self, sample_ground_truth: GroundTruthRecord
    ) -> None:
        # Use a simple function that returns a dict
        config = OracleConfig(
            type="python",
            module="tests.test_oracle_adapters",
            callable="mock_oracle_sync",
        )
        adapter = PythonOracleAdapter(config)
        result = await adapter.invoke(sample_ground_truth, "Question?")

        assert result.summary == "Mock summary"
        assert result.key_claims == ["claim1"]
        assert "error" not in result.metadata

    def test_nonexistent_module_raises(self) -> None:
        config = OracleConfig(
            type="python",
            module="nonexistent.module.xyz",
            callable="run",
        )
        with pytest.raises(ImportError, match="Cannot import"):
            PythonOracleAdapter(config)

    def test_nonexistent_callable_raises(self) -> None:
        config = OracleConfig(
            type="python",
            module="json",
            callable="nonexistent_function_xyz",
        )
        with pytest.raises(AttributeError, match="has no attribute"):
            PythonOracleAdapter(config)

    @pytest.mark.asyncio
    async def test_runtime_error_returns_error_output(
        self, sample_ground_truth: GroundTruthRecord
    ) -> None:
        config = OracleConfig(
            type="python",
            module="tests.test_oracle_adapters",
            callable="mock_oracle_error",
        )
        adapter = PythonOracleAdapter(config)
        result = await adapter.invoke(sample_ground_truth, "Question?")

        assert "error" in result.metadata
        assert "boom" in result.metadata["error"]


# --- Test oracle callables used by PythonOracleAdapter tests ---


def mock_oracle_sync(payload: dict) -> dict:
    """A simple sync oracle for testing."""
    return {
        "summary": "Mock summary",
        "key_claims": ["claim1"],
        "follow_up_response": "Mock answer",
        "metadata": {"source": "test"},
    }


def mock_oracle_error(payload: dict) -> dict:
    """An oracle that raises an error."""
    raise RuntimeError("boom")
