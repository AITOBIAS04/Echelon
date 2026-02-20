"""Observer Oracle Adapter — implements Theatre OracleAdapter protocol.

Calls Anthropic to summarise a PR, extract key claims, and answer follow-up
questions. Designed for the Observer verification pipeline.
"""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Prompt template paths (relative to repo root)
_PROMPT_DIR = Path(__file__).resolve().parents[2] / (
    "verification/src/echelon_verify/scoring/prompts/v1"
)
_FOLLOW_UP_PROMPT = _PROMPT_DIR / "follow_up_question.txt"

# Default system prompt for PR summarisation
_SUMMARISE_SYSTEM = (
    "You are an expert code reviewer. Summarise the PR changes factually. "
    "Respond with ONLY valid JSON."
)

_SUMMARISE_USER = """Analyse the following Pull Request and provide a factual summary.

Title: {title}
Description: {description}

Diff:
```
{diff_content}
```

Files changed: {files_changed}

Respond with ONLY valid JSON in this exact format:
{{
  "summary": "concise factual summary of the changes",
  "key_claims": ["list", "of", "specific", "factual", "claims", "about", "changes"]
}}"""

_FOLLOW_UP_SYSTEM = (
    "You are an expert code reviewer answering a follow-up question about a PR. "
    "Answer factually based only on the diff content."
)

_FOLLOW_UP_USER = """PR Details:
Title: {title}
Description: {description}

Diff:
```
{diff_content}
```

Question: {follow_up_question}

Answer the question based only on the diff content. Be specific and factual."""


class ObserverOracleAdapter:
    """OracleAdapter implementation for Observer PR verification.

    Uses Anthropic's Claude API to:
    1. Generate a factual summary + key claims for a PR
    2. Answer a follow-up question about the PR

    Conforms to the Theatre OracleAdapter protocol:
        async def invoke(self, input_data: dict[str, Any]) -> dict[str, Any]
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "claude-sonnet-4-20250514",
        max_tokens: int = 2048,
    ) -> None:
        self._api_key = api_key
        self._model = model
        self._max_tokens = max_tokens

    async def invoke(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Invoke the oracle on a single episode.

        Args:
            input_data: Dict containing PR fields (title, description,
                diff_content, files_changed, follow_up_question) plus
                episode_id injected by invoke_oracle().

        Returns:
            Dict with summary, key_claims, follow_up_question,
            follow_up_response, and metadata.
        """
        title = input_data.get("title", "")
        description = input_data.get("description", "")
        diff_content = input_data.get("diff_content", "")
        files_changed = input_data.get("files_changed", [])
        follow_up_question = input_data.get("follow_up_question", "")
        episode_id = input_data.get("episode_id", "")

        start_ms = _now_ms()

        # Step 1: Summarise the PR
        summary_result = await self._call_summarise(
            title=title,
            description=description,
            diff_content=diff_content,
            files_changed=files_changed,
        )

        summary = summary_result.get("summary", "")
        key_claims = summary_result.get("key_claims", [])

        # Step 2: Answer follow-up question (if provided)
        follow_up_response = ""
        if follow_up_question:
            follow_up_response = await self._call_follow_up(
                title=title,
                description=description,
                diff_content=diff_content,
                follow_up_question=follow_up_question,
            )

        elapsed_ms = _now_ms() - start_ms

        return {
            "summary": summary,
            "key_claims": key_claims,
            "follow_up_question": follow_up_question,
            "follow_up_response": follow_up_response,
            "episode_id": episode_id,
            "metadata": {
                "model": self._model,
                "latency_ms": elapsed_ms,
            },
        }

    async def _call_summarise(
        self,
        title: str,
        description: str,
        diff_content: str,
        files_changed: list[str],
    ) -> dict[str, Any]:
        """Call the LLM to summarise a PR."""
        user_prompt = _SUMMARISE_USER.format(
            title=title,
            description=description,
            diff_content=_truncate(diff_content, 80_000),
            files_changed=", ".join(files_changed[:50]),
        )

        raw = await self._call_anthropic(
            system=_SUMMARISE_SYSTEM,
            user=user_prompt,
        )

        return _parse_json_response(raw, fallback={"summary": raw, "key_claims": []})

    async def _call_follow_up(
        self,
        title: str,
        description: str,
        diff_content: str,
        follow_up_question: str,
    ) -> str:
        """Call the LLM to answer a follow-up question."""
        user_prompt = _FOLLOW_UP_USER.format(
            title=title,
            description=description,
            diff_content=_truncate(diff_content, 80_000),
            follow_up_question=follow_up_question,
        )

        return await self._call_anthropic(
            system=_FOLLOW_UP_SYSTEM,
            user=user_prompt,
        )

    async def _call_anthropic(self, system: str, user: str) -> str:
        """Make a single Anthropic API call. Returns the text response."""
        try:
            import anthropic
        except ImportError as e:
            raise ImportError(
                "anthropic package required: pip install anthropic"
            ) from e

        client = anthropic.AsyncAnthropic(api_key=self._api_key)
        response = await client.messages.create(
            model=self._model,
            max_tokens=self._max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )

        return response.content[0].text


def _truncate(text: str, max_chars: int) -> str:
    """Truncate text to max_chars, adding indicator if truncated."""
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n\n[... truncated ...]"


def _parse_json_response(raw: str, fallback: dict[str, Any]) -> dict[str, Any]:
    """Parse JSON from LLM response, with fallback on failure."""
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        # Try to extract JSON from markdown code block
        if "```" in raw:
            start = raw.find("```")
            end = raw.rfind("```")
            if start != end:
                inner = raw[start:end].split("\n", 1)
                if len(inner) > 1:
                    try:
                        return json.loads(inner[1])
                    except (json.JSONDecodeError, TypeError):
                        pass
        logger.warning("Failed to parse oracle JSON response, using fallback")
        return fallback


def _now_ms() -> int:
    """Current time in milliseconds."""
    return int(time.monotonic() * 1000)
