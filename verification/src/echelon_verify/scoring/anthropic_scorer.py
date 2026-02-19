"""AnthropicScorer — Claude-based factual alignment scoring."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, TYPE_CHECKING

import anthropic

from echelon_verify.scoring.base import ScoringProvider

if TYPE_CHECKING:
    from echelon_verify.config import ScoringConfig
    from echelon_verify.models import GroundTruthRecord, OracleOutput

logger = logging.getLogger(__name__)


class PromptLoader:
    """Loads and fills versioned prompt templates."""

    def __init__(self, version: str = "v1") -> None:
        self._base = Path(__file__).parent / "prompts" / version
        manifest_path = self._base / "manifest.json"
        with open(manifest_path) as f:
            self._manifest: dict[str, str] = json.load(f)["prompts"]
        self._cache: dict[str, str] = {}

    def load(self, name: str, **kwargs: str) -> str:
        """Load a prompt template and fill placeholders."""
        if name not in self._cache:
            template_file = self._base / self._manifest[name]
            self._cache[name] = template_file.read_text()
        return self._cache[name].format(**kwargs)


class AnthropicScorer(ScoringProvider):
    """Claude-based verification scorer."""

    def __init__(self, config: ScoringConfig) -> None:
        self._client = anthropic.AsyncAnthropic(api_key=config.api_key)
        self._model = config.model
        self._temperature = config.temperature
        self._prompts = PromptLoader(config.prompt_version)

    async def _call_llm(self, prompt: str, retry: bool = True) -> str:
        """Call Claude and return the text response."""
        try:
            response = await self._client.messages.create(
                model=self._model,
                max_tokens=2048,
                temperature=self._temperature,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.content[0].text
        except anthropic.APIError:
            if retry:
                logger.warning("LLM call failed, retrying once")
                return await self._call_llm(prompt, retry=False)
            raise

    async def _call_llm_json(self, prompt: str) -> dict[str, Any]:
        """Call Claude and parse JSON response, with one retry on parse failure."""
        text = await self._call_llm(prompt, retry=True)
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            logger.warning("JSON parse failed, retrying with stricter prompt")
            retry_prompt = (
                prompt
                + "\n\nIMPORTANT: Your previous response was not valid JSON. "
                "Respond with ONLY valid JSON, no markdown fences or extra text."
            )
            text = await self._call_llm(retry_prompt, retry=False)
            # Strip markdown fences if present
            text = text.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[1] if "\n" in text else text[3:]
            if text.endswith("```"):
                text = text[:-3].strip()
            return json.loads(text)

    async def score_precision(
        self, ground_truth: GroundTruthRecord, oracle_output: OracleOutput
    ) -> tuple[float, int, int, dict[str, Any]]:
        prompt = self._prompts.load(
            "precision",
            title=ground_truth.title,
            description=ground_truth.description,
            diff_content=ground_truth.diff_content,
            claims_json=json.dumps(oracle_output.key_claims, indent=2),
        )
        raw = await self._call_llm_json(prompt)
        return (
            float(raw.get("precision", 0.0)),
            int(raw.get("total", 0)),
            int(raw.get("supported", 0)),
            raw,
        )

    async def score_recall(
        self, ground_truth: GroundTruthRecord, oracle_output: OracleOutput
    ) -> tuple[float, int, int, dict[str, Any]]:
        prompt = self._prompts.load(
            "recall",
            title=ground_truth.title,
            description=ground_truth.description,
            diff_content=ground_truth.diff_content,
            summary=oracle_output.summary,
        )
        raw = await self._call_llm_json(prompt)
        return (
            float(raw.get("recall", 0.0)),
            int(raw.get("total", 0)),
            int(raw.get("surfaced", 0)),
            raw,
        )

    async def score_reply_accuracy(
        self, ground_truth: GroundTruthRecord, oracle_output: OracleOutput
    ) -> tuple[float, dict[str, Any]]:
        prompt = self._prompts.load(
            "reply_accuracy",
            title=ground_truth.title,
            description=ground_truth.description,
            diff_content=ground_truth.diff_content,
            follow_up_question=oracle_output.follow_up_question,
            follow_up_response=oracle_output.follow_up_response,
        )
        raw = await self._call_llm_json(prompt)
        return float(raw.get("accuracy", 0.0)), raw

    async def generate_follow_up_question(
        self, ground_truth: GroundTruthRecord
    ) -> str:
        prompt = self._prompts.load(
            "follow_up_question",
            title=ground_truth.title,
            description=ground_truth.description,
            diff_content=ground_truth.diff_content,
        )
        return (await self._call_llm(prompt, retry=True)).strip()
