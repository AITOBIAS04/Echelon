"""Observer Scoring Function — implements Theatre ScoringFunction protocol.

Uses Anthropic to evaluate oracle outputs against ground truth PRs.
Supports three criteria: precision, recall, reply_accuracy.
Uses the scoring prompts from echelon_verify/scoring/prompts/v1/.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Prompt template directory
_PROMPT_DIR = Path(__file__).resolve().parents[2] / (
    "verification/src/echelon_verify/scoring/prompts/v1"
)

_VALID_CRITERIA = frozenset({"precision", "recall", "reply_accuracy"})


class ObserverScoringFunction:
    """ScoringFunction implementation for Observer verification.

    Calls Anthropic to evaluate oracle outputs using the three Observer
    criteria: precision, recall, and reply_accuracy.

    Conforms to the Theatre ScoringFunction protocol:
        async def score(
            self, criteria_id: str, ground_truth: dict, oracle_output: dict
        ) -> float
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
        self._prompts: dict[str, str] = {}
        self._load_prompts()

    def _load_prompts(self) -> None:
        """Load scoring prompt templates from disk."""
        for name in ("precision", "recall", "reply_accuracy", "follow_up_question"):
            path = _PROMPT_DIR / f"{name}.txt"
            if path.exists():
                self._prompts[name] = path.read_text()
            else:
                logger.warning("Scoring prompt not found: %s", path)

    async def score(
        self,
        criteria_id: str,
        ground_truth: dict[str, Any],
        oracle_output: dict[str, Any],
    ) -> float:
        """Score a single criterion for one episode.

        Args:
            criteria_id: One of "precision", "recall", "reply_accuracy".
            ground_truth: Dict with input_data, expected_output, labels, metadata
                          (as packed by TheatreScoringProvider.score_episode).
            oracle_output: Dict with summary, key_claims, follow_up_response, etc.

        Returns:
            Float score in [0.0, 1.0].
        """
        if criteria_id not in _VALID_CRITERIA:
            logger.warning("Unknown criteria_id: %s, returning 0.0", criteria_id)
            return 0.0

        input_data = ground_truth.get("input_data", {})
        title = input_data.get("title", "")
        description = input_data.get("description", "")
        diff_content = input_data.get("diff_content", "")

        try:
            if criteria_id == "precision":
                return await self._score_precision(
                    title=title,
                    description=description,
                    diff_content=diff_content,
                    key_claims=oracle_output.get("key_claims", []),
                )
            elif criteria_id == "recall":
                return await self._score_recall(
                    title=title,
                    description=description,
                    diff_content=diff_content,
                    summary=oracle_output.get("summary", ""),
                )
            elif criteria_id == "reply_accuracy":
                return await self._score_reply_accuracy(
                    title=title,
                    description=description,
                    diff_content=diff_content,
                    follow_up_question=input_data.get("follow_up_question", ""),
                    follow_up_response=oracle_output.get("follow_up_response", ""),
                )
        except Exception:
            logger.exception(
                "Scoring failed for criteria_id=%s, returning 0.0", criteria_id
            )
            return 0.0

        return 0.0  # unreachable but satisfies type checker

    async def _score_precision(
        self,
        title: str,
        description: str,
        diff_content: str,
        key_claims: list[str],
    ) -> float:
        """Evaluate precision: what fraction of claims are factually supported."""
        if not key_claims:
            return 1.0  # No claims = vacuous precision

        prompt_template = self._prompts.get("precision", "")
        if not prompt_template:
            logger.warning("Precision prompt template not loaded")
            return 0.0

        claims_json = json.dumps(key_claims, indent=2)
        prompt = prompt_template.format(
            title=title,
            description=description,
            diff_content=_truncate(diff_content, 60_000),
            claims_json=claims_json,
        )

        raw = await self._call_anthropic(prompt)
        result = _parse_json_response(raw)
        return float(result.get("precision", 0.0))

    async def _score_recall(
        self,
        title: str,
        description: str,
        diff_content: str,
        summary: str,
    ) -> float:
        """Evaluate recall: what fraction of important changes are surfaced."""
        if not summary:
            return 0.0

        prompt_template = self._prompts.get("recall", "")
        if not prompt_template:
            logger.warning("Recall prompt template not loaded")
            return 0.0

        prompt = prompt_template.format(
            title=title,
            description=description,
            diff_content=_truncate(diff_content, 60_000),
            summary=summary,
        )

        raw = await self._call_anthropic(prompt)
        result = _parse_json_response(raw)
        return float(result.get("recall", 0.0))

    async def _score_reply_accuracy(
        self,
        title: str,
        description: str,
        diff_content: str,
        follow_up_question: str,
        follow_up_response: str,
    ) -> float:
        """Evaluate reply accuracy: how grounded is the follow-up response."""
        if not follow_up_question or not follow_up_response:
            return 0.0  # Cannot score without both Q and A

        prompt_template = self._prompts.get("reply_accuracy", "")
        if not prompt_template:
            logger.warning("Reply accuracy prompt template not loaded")
            return 0.0

        prompt = prompt_template.format(
            title=title,
            description=description,
            diff_content=_truncate(diff_content, 60_000),
            follow_up_question=follow_up_question,
            follow_up_response=follow_up_response,
        )

        raw = await self._call_anthropic(prompt)
        result = _parse_json_response(raw)
        return float(result.get("accuracy", 0.0))

    async def generate_follow_up_question(
        self,
        title: str,
        description: str,
        diff_content: str,
    ) -> str:
        """Generate a follow-up question for a PR.

        Not part of the ScoringFunction protocol, but used by the runner
        before scoring to prepare follow-up questions.
        """
        prompt_template = self._prompts.get("follow_up_question", "")
        if not prompt_template:
            return ""

        prompt = prompt_template.format(
            title=title,
            description=description,
            diff_content=_truncate(diff_content, 60_000),
        )

        return await self._call_anthropic(prompt)

    async def _call_anthropic(self, user_prompt: str) -> str:
        """Make a single Anthropic API call."""
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
            messages=[{"role": "user", "content": user_prompt}],
        )

        return response.content[0].text


def _truncate(text: str, max_chars: int) -> str:
    """Truncate text to max_chars with indicator."""
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n\n[... truncated ...]"


def _parse_json_response(raw: str) -> dict[str, Any]:
    """Parse JSON from LLM response."""
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
        logger.warning("Failed to parse scoring JSON response")
        return {}
