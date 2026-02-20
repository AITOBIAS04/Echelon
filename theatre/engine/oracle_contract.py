"""Oracle Invocation Contract — standardised request/response envelope.

Wraps the existing OracleAdapter with Theatre-aware invocation tracking,
retry logic, timeout handling, and structured status reporting.
"""

from __future__ import annotations

import asyncio
import time
import uuid
from datetime import datetime
from typing import Any, Callable, Literal, Protocol

from pydantic import BaseModel, Field


class OracleInvocationMetadata(BaseModel):
    """Configuration for a single oracle invocation."""

    timeout_seconds: int = 30
    retry_count: int = 2
    retry_backoff_seconds: float = 5.0
    deterministic: bool = False
    sanitise_input: bool = True


class OracleInvocationRequest(BaseModel):
    """Standardised request envelope for construct invocation."""

    invocation_id: str = Field(default_factory=lambda: uuid.uuid4().hex[:16])
    theatre_id: str
    episode_id: str
    construct_id: str
    construct_version: str
    input_data: dict[str, Any]
    metadata: OracleInvocationMetadata = Field(default_factory=OracleInvocationMetadata)


class OracleInvocationResponse(BaseModel):
    """Standardised response envelope from construct invocation."""

    invocation_id: str
    construct_id: str
    construct_version: str
    output_data: dict[str, Any] | None = None
    latency_ms: int
    status: Literal["SUCCESS", "TIMEOUT", "ERROR", "REFUSED"]
    error_detail: str | None = None
    responded_at: datetime = Field(default_factory=datetime.utcnow)


class OracleAdapter(Protocol):
    """Protocol for oracle adapters — matches existing echelon-verify contract."""

    async def invoke(self, input_data: dict[str, Any]) -> dict[str, Any]: ...


class MockOracleAdapter:
    """Mock adapter for testing. Returns configurable responses."""

    def __init__(
        self,
        responses: dict[str, dict[str, Any]] | None = None,
        default_response: dict[str, Any] | None = None,
        latency_ms: int = 10,
        fail_episodes: set[str] | None = None,
        timeout_episodes: set[str] | None = None,
        refuse_episodes: set[str] | None = None,
    ):
        self._responses = responses or {}
        self._default_response = default_response or {"result": "mock_output"}
        self._latency_ms = latency_ms
        self._fail_episodes = fail_episodes or set()
        self._timeout_episodes = timeout_episodes or set()
        self._refuse_episodes = refuse_episodes or set()

    async def invoke(self, input_data: dict[str, Any]) -> dict[str, Any]:
        episode_id = input_data.get("episode_id", "")

        if episode_id in self._timeout_episodes:
            await asyncio.sleep(100)  # Will be cancelled by timeout
            return {}

        if episode_id in self._fail_episodes:
            raise RuntimeError(f"Simulated failure for episode {episode_id}")

        if episode_id in self._refuse_episodes:
            raise PermissionError(f"Construct refused episode {episode_id}")

        if episode_id in self._responses:
            return self._responses[episode_id]

        return dict(self._default_response)


async def invoke_oracle(
    adapter: OracleAdapter,
    request: OracleInvocationRequest,
) -> OracleInvocationResponse:
    """Invoke an oracle adapter with retry and timeout handling.

    Wraps the raw adapter call with:
    - Timeout enforcement
    - Retry with exponential backoff
    - Structured status reporting (SUCCESS/TIMEOUT/ERROR/REFUSED)
    """
    last_error: str | None = None

    for attempt in range(request.metadata.retry_count + 1):
        start_time = time.monotonic()
        try:
            result = await asyncio.wait_for(
                adapter.invoke({
                    **request.input_data,
                    "episode_id": request.episode_id,
                }),
                timeout=request.metadata.timeout_seconds,
            )
            elapsed_ms = int((time.monotonic() - start_time) * 1000)
            return OracleInvocationResponse(
                invocation_id=request.invocation_id,
                construct_id=request.construct_id,
                construct_version=request.construct_version,
                output_data=result,
                latency_ms=elapsed_ms,
                status="SUCCESS",
            )

        except asyncio.TimeoutError:
            elapsed_ms = int((time.monotonic() - start_time) * 1000)
            last_error = (
                f"Timeout after {request.metadata.timeout_seconds}s "
                f"(attempt {attempt + 1}/{request.metadata.retry_count + 1})"
            )

        except PermissionError as e:
            # REFUSED — do not retry
            elapsed_ms = int((time.monotonic() - start_time) * 1000)
            return OracleInvocationResponse(
                invocation_id=request.invocation_id,
                construct_id=request.construct_id,
                construct_version=request.construct_version,
                latency_ms=elapsed_ms,
                status="REFUSED",
                error_detail=str(e),
            )

        except Exception as e:
            elapsed_ms = int((time.monotonic() - start_time) * 1000)
            last_error = f"{type(e).__name__}: {e}"

        # Backoff before retry (except on last attempt)
        if attempt < request.metadata.retry_count:
            backoff = request.metadata.retry_backoff_seconds * (2 ** attempt)
            await asyncio.sleep(backoff)

    # All retries exhausted
    elapsed_ms = int((time.monotonic() - start_time) * 1000)
    # Determine final status
    final_status: Literal["TIMEOUT", "ERROR"] = (
        "TIMEOUT" if last_error and "Timeout" in last_error else "ERROR"
    )

    return OracleInvocationResponse(
        invocation_id=request.invocation_id,
        construct_id=request.construct_id,
        construct_version=request.construct_version,
        latency_ms=elapsed_ms,
        status=final_status,
        error_detail=last_error,
    )
