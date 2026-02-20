"""Tests for Oracle Invocation Contract — request/response, retry, timeout."""

import asyncio

import pytest

from theatre.engine.oracle_contract import (
    MockOracleAdapter,
    OracleInvocationMetadata,
    OracleInvocationRequest,
    OracleInvocationResponse,
    invoke_oracle,
)


class TestOracleInvocationModels:
    def test_request_has_auto_invocation_id(self):
        req = OracleInvocationRequest(
            theatre_id="t1",
            episode_id="ep1",
            construct_id="observer",
            construct_version="abc123",
            input_data={"key": "value"},
        )
        assert len(req.invocation_id) == 16

    def test_request_custom_metadata(self):
        meta = OracleInvocationMetadata(timeout_seconds=60, retry_count=5)
        req = OracleInvocationRequest(
            theatre_id="t1",
            episode_id="ep1",
            construct_id="observer",
            construct_version="abc123",
            input_data={},
            metadata=meta,
        )
        assert req.metadata.timeout_seconds == 60
        assert req.metadata.retry_count == 5

    def test_response_serialisation(self):
        resp = OracleInvocationResponse(
            invocation_id="inv1",
            construct_id="observer",
            construct_version="abc123",
            output_data={"result": "ok"},
            latency_ms=50,
            status="SUCCESS",
        )
        data = resp.model_dump()
        assert data["status"] == "SUCCESS"
        assert data["latency_ms"] == 50

    def test_default_metadata(self):
        meta = OracleInvocationMetadata()
        assert meta.timeout_seconds == 30
        assert meta.retry_count == 2
        assert meta.retry_backoff_seconds == 5.0
        assert meta.deterministic is False
        assert meta.sanitise_input is True


class TestMockOracleAdapter:
    @pytest.mark.asyncio
    async def test_default_response(self):
        adapter = MockOracleAdapter()
        result = await adapter.invoke({"episode_id": "ep1"})
        assert result == {"result": "mock_output"}

    @pytest.mark.asyncio
    async def test_custom_responses(self):
        adapter = MockOracleAdapter(
            responses={"ep1": {"custom": "response"}}
        )
        result = await adapter.invoke({"episode_id": "ep1"})
        assert result == {"custom": "response"}

    @pytest.mark.asyncio
    async def test_fail_episodes(self):
        adapter = MockOracleAdapter(fail_episodes={"ep1"})
        with pytest.raises(RuntimeError, match="Simulated failure"):
            await adapter.invoke({"episode_id": "ep1"})

    @pytest.mark.asyncio
    async def test_refuse_episodes(self):
        adapter = MockOracleAdapter(refuse_episodes={"ep1"})
        with pytest.raises(PermissionError, match="refused"):
            await adapter.invoke({"episode_id": "ep1"})


class TestInvokeOracle:
    def _make_request(self, **overrides) -> OracleInvocationRequest:
        defaults = {
            "theatre_id": "t1",
            "episode_id": "ep1",
            "construct_id": "observer",
            "construct_version": "abc123",
            "input_data": {"key": "value"},
        }
        defaults.update(overrides)
        return OracleInvocationRequest(**defaults)

    @pytest.mark.asyncio
    async def test_successful_invocation(self):
        adapter = MockOracleAdapter()
        req = self._make_request()
        resp = await invoke_oracle(adapter, req)
        assert resp.status == "SUCCESS"
        assert resp.output_data == {"result": "mock_output"}
        assert resp.latency_ms >= 0

    @pytest.mark.asyncio
    async def test_error_invocation_with_retries(self):
        adapter = MockOracleAdapter(fail_episodes={"ep1"})
        req = self._make_request(
            metadata=OracleInvocationMetadata(
                retry_count=1,
                retry_backoff_seconds=0.01,
            ),
        )
        resp = await invoke_oracle(adapter, req)
        assert resp.status == "ERROR"
        assert "RuntimeError" in resp.error_detail

    @pytest.mark.asyncio
    async def test_timeout_invocation(self):
        adapter = MockOracleAdapter(timeout_episodes={"ep1"})
        req = self._make_request(
            metadata=OracleInvocationMetadata(
                timeout_seconds=1,
                retry_count=0,
            ),
        )
        resp = await invoke_oracle(adapter, req)
        assert resp.status == "TIMEOUT"
        assert "Timeout" in resp.error_detail

    @pytest.mark.asyncio
    async def test_refused_invocation_no_retry(self):
        adapter = MockOracleAdapter(refuse_episodes={"ep1"})
        req = self._make_request(
            metadata=OracleInvocationMetadata(retry_count=3),
        )
        resp = await invoke_oracle(adapter, req)
        assert resp.status == "REFUSED"
        assert "refused" in resp.error_detail

    @pytest.mark.asyncio
    async def test_retry_succeeds_on_second_attempt(self):
        call_count = 0

        class FlakeyAdapter:
            async def invoke(self, input_data):
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    raise RuntimeError("Transient failure")
                return {"result": "ok"}

        req = self._make_request(
            metadata=OracleInvocationMetadata(
                retry_count=2,
                retry_backoff_seconds=0.01,
            ),
        )
        resp = await invoke_oracle(FlakeyAdapter(), req)
        assert resp.status == "SUCCESS"
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_response_includes_construct_info(self):
        adapter = MockOracleAdapter()
        req = self._make_request()
        resp = await invoke_oracle(adapter, req)
        assert resp.construct_id == "observer"
        assert resp.construct_version == "abc123"
        assert resp.invocation_id == req.invocation_id
