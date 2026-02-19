"""HTTP oracle adapter — invokes oracle via HTTP POST endpoint."""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone

import httpx

from echelon_verify.config import OracleConfig
from echelon_verify.models import GroundTruthRecord, OracleOutput
from echelon_verify.oracle.base import OracleAdapter

logger = logging.getLogger(__name__)


class HttpOracleAdapter(OracleAdapter):
    """Invokes oracle via HTTP POST endpoint."""

    def __init__(self, config: OracleConfig) -> None:
        if not config.url:
            raise ValueError("url is required for HTTP oracle adapter")
        self._url = config.url
        self._headers = dict(config.headers)
        self._timeout = config.timeout_seconds

    async def invoke(
        self, ground_truth: GroundTruthRecord, follow_up_question: str
    ) -> OracleOutput:
        """POST PR data to oracle endpoint and parse response."""
        payload = {
            "pr": {
                "id": ground_truth.id,
                "title": ground_truth.title,
                "description": ground_truth.description,
                "diff_content": ground_truth.diff_content,
                "files_changed": ground_truth.files_changed,
            },
            "follow_up_question": follow_up_question,
        }

        start = time.monotonic()
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.post(
                    self._url,
                    json=payload,
                    headers=self._headers,
                )
                elapsed_ms = int((time.monotonic() - start) * 1000)

                if resp.status_code >= 400:
                    logger.warning(
                        "Oracle HTTP %d for PR #%s: %s",
                        resp.status_code,
                        ground_truth.id,
                        resp.text[:200],
                    )
                    return self._error_output(
                        ground_truth.id,
                        follow_up_question,
                        elapsed_ms,
                        f"HTTP {resp.status_code}",
                    )

                data = resp.json()
                return OracleOutput(
                    ground_truth_id=ground_truth.id,
                    summary=data.get("summary", ""),
                    key_claims=data.get("key_claims", []),
                    follow_up_question=follow_up_question,
                    follow_up_response=data.get("follow_up_response", ""),
                    metadata=data.get("metadata", {}),
                    invoked_at=datetime.now(tz=timezone.utc),
                    latency_ms=elapsed_ms,
                )

        except httpx.TimeoutException:
            elapsed_ms = int((time.monotonic() - start) * 1000)
            logger.warning("Oracle timeout for PR #%s", ground_truth.id)
            return self._error_output(
                ground_truth.id, follow_up_question, elapsed_ms, "timeout"
            )
        except httpx.HTTPError as exc:
            elapsed_ms = int((time.monotonic() - start) * 1000)
            logger.warning("Oracle HTTP error for PR #%s: %s", ground_truth.id, exc)
            return self._error_output(
                ground_truth.id,
                follow_up_question,
                elapsed_ms,
                str(exc),
            )
        except (ValueError, KeyError) as exc:
            elapsed_ms = int((time.monotonic() - start) * 1000)
            logger.warning(
                "Oracle malformed response for PR #%s: %s",
                ground_truth.id,
                exc,
            )
            return self._error_output(
                ground_truth.id,
                follow_up_question,
                elapsed_ms,
                f"malformed response: {exc}",
            )

    @staticmethod
    def _error_output(
        gt_id: str, follow_up: str, latency_ms: int, error: str
    ) -> OracleOutput:
        return OracleOutput(
            ground_truth_id=gt_id,
            summary="",
            key_claims=[],
            follow_up_question=follow_up,
            follow_up_response="",
            metadata={"error": error},
            invoked_at=datetime.now(tz=timezone.utc),
            latency_ms=latency_ms,
        )
