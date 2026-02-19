"""Python oracle adapter — invokes oracle as a local Python callable."""

from __future__ import annotations

import asyncio
import importlib
import inspect
import logging
import time
from datetime import datetime, timezone

from echelon_verify.config import OracleConfig
from echelon_verify.models import GroundTruthRecord, OracleOutput
from echelon_verify.oracle.base import OracleAdapter

logger = logging.getLogger(__name__)


class PythonOracleAdapter(OracleAdapter):
    """Invokes oracle as a local Python callable."""

    def __init__(self, config: OracleConfig) -> None:
        if not config.module or not config.callable:
            raise ValueError(
                "module and callable are required for Python oracle adapter"
            )
        self._module_path = config.module
        self._callable_name = config.callable
        self._fn = self._load_callable()

    def _load_callable(self) -> object:
        """Dynamically import and get the callable."""
        try:
            module = importlib.import_module(self._module_path)
        except ImportError as exc:
            raise ImportError(
                f"Cannot import oracle module '{self._module_path}': {exc}"
            ) from exc

        try:
            fn = getattr(module, self._callable_name)
        except AttributeError as exc:
            raise AttributeError(
                f"Module '{self._module_path}' has no attribute "
                f"'{self._callable_name}': {exc}"
            ) from exc

        return fn

    async def invoke(
        self, ground_truth: GroundTruthRecord, follow_up_question: str
    ) -> OracleOutput:
        """Call the Python oracle with PR data."""
        payload = {
            "id": ground_truth.id,
            "title": ground_truth.title,
            "description": ground_truth.description,
            "diff_content": ground_truth.diff_content,
            "files_changed": ground_truth.files_changed,
            "follow_up_question": follow_up_question,
        }

        start = time.monotonic()
        try:
            if inspect.iscoroutinefunction(self._fn):
                result = await self._fn(payload)
            else:
                result = await asyncio.to_thread(self._fn, payload)

            elapsed_ms = int((time.monotonic() - start) * 1000)

            if isinstance(result, dict):
                return OracleOutput(
                    ground_truth_id=ground_truth.id,
                    summary=result.get("summary", ""),
                    key_claims=result.get("key_claims", []),
                    follow_up_question=follow_up_question,
                    follow_up_response=result.get("follow_up_response", ""),
                    metadata=result.get("metadata", {}),
                    invoked_at=datetime.now(tz=timezone.utc),
                    latency_ms=elapsed_ms,
                )
            else:
                return OracleOutput(
                    ground_truth_id=ground_truth.id,
                    summary=str(result),
                    key_claims=[],
                    follow_up_question=follow_up_question,
                    follow_up_response="",
                    metadata={"raw_type": type(result).__name__},
                    invoked_at=datetime.now(tz=timezone.utc),
                    latency_ms=elapsed_ms,
                )

        except Exception as exc:
            elapsed_ms = int((time.monotonic() - start) * 1000)
            logger.warning(
                "Python oracle error for PR #%s: %s", ground_truth.id, exc
            )
            return OracleOutput(
                ground_truth_id=ground_truth.id,
                summary="",
                key_claims=[],
                follow_up_question=follow_up_question,
                follow_up_response="",
                metadata={"error": str(exc)},
                invoked_at=datetime.now(tz=timezone.utc),
                latency_ms=elapsed_ms,
            )
