"""Anthropic Provider -- wraps Anthropic API for deep reasoning (T3).

Sonnet 4.5 / Opus for complex multi-step reasoning.
Structured output: reasoning_summary, evidence_refs, decision_trace.
Rate limiting handled at engine level (DeepReasoningEngine).
Fallback: router falls back to T1.

Cycle-013, Sprint 2 -- Task 6.
"""
from __future__ import annotations

import json
from typing import Optional

import httpx

from backend.agents.model_providers import BaseModelProvider, ProviderConfig


class AnthropicProvider(BaseModelProvider):
    """Wraps Anthropic API for deep reasoning (Sonnet 4.5 / Opus).

    Used by DeepReasoningEngine (T3) for escalated decisions.
    Rate limiting managed externally by T3RateLimiter.
    Fallback: router falls back to T1 when unavailable.
    """

    DEFAULT_URL = "https://api.anthropic.com/v1"
    DEFAULT_MODEL = "claude-sonnet-4-5-20241022"

    def __init__(self, config: Optional[ProviderConfig] = None) -> None:
        cfg = config or ProviderConfig(
            base_url=self.DEFAULT_URL,
            model_name=self.DEFAULT_MODEL,
        )
        super().__init__(cfg)
        self._last_health: bool = False

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        response_schema: Optional[dict] = None,
    ) -> dict:
        """Call Anthropic /messages API.

        Attempts to parse structured JSON from response content.
        Falls back to HOLD with reasoning_summary if JSON parsing fails.

        Args:
            system_prompt: System instructions for deep reasoning.
            user_prompt: Full context prompt with market state and evidence.
            response_schema: Unused (Anthropic uses natural language structured output).

        Returns:
            Parsed dict with action, confidence, reasoning_summary, evidence_refs.

        Raises:
            httpx.HTTPStatusError: On non-2xx response.
        """
        headers = {
            "x-api-key": self._config.api_key or "",
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self._config.model_name,
            "max_tokens": 1024,
            "system": system_prompt,
            "messages": [
                {"role": "user", "content": user_prompt},
            ],
        }
        async with httpx.AsyncClient(timeout=self._config.timeout_s) as client:
            resp = await client.post(
                f"{self._config.base_url}/messages",
                headers=headers,
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            content = data["content"][0]["text"]
            # Attempt to parse structured JSON from response
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                return {
                    "action": "HOLD",
                    "confidence": 0.5,
                    "reasoning_summary": content,
                    "evidence_refs": [],
                    "pattern_name": "deep_analysis",
                }

    async def health_check(self) -> bool:
        """Light health check -- verify API key is configured.

        Does not make a probe call to avoid burning tokens.
        Full validation occurs on first generate() call.

        Returns:
            True if api_key is configured.
        """
        if not self._config.api_key:
            self._last_health = False
            return False
        # Trust the key is valid without a probe call
        self._last_health = True
        return True

    def is_available(self) -> bool:
        """Return cached health check result.

        Returns:
            True if the last health check passed.
        """
        return self._last_health
