"""Mistral Provider -- wraps Mistral API for creative personality generation (T2).

Prompt templates per archetype for personality-flavoured output.
Health check validates API key via models endpoint.
Fallback: generic template string (decision unaffected).

Cycle-013, Sprint 2 -- Task 5.
"""
from __future__ import annotations

from typing import Optional

import httpx

from backend.agents.model_providers import BaseModelProvider, ProviderConfig


class MistralProvider(BaseModelProvider):
    """Wraps Mistral API for creative personality generation.

    Used by PersonalityEngine (T2) to add archetype-specific voice to decisions.
    Fallback: generic template string when API unavailable.
    """

    DEFAULT_URL = "https://api.mistral.ai/v1"
    DEFAULT_MODEL = "mistral-small-latest"

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
        """Call Mistral /chat/completions endpoint.

        Args:
            system_prompt: System instructions (archetype personality prompt).
            user_prompt: Trading decision context.
            response_schema: Unused for Mistral (creative generation).

        Returns:
            Dict with 'rationale' and 'commentary' keys.

        Raises:
            httpx.HTTPStatusError: On non-2xx response.
        """
        headers = {
            "Authorization": f"Bearer {self._config.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self._config.model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "max_tokens": 200,
        }
        async with httpx.AsyncClient(timeout=self._config.timeout_s) as client:
            resp = await client.post(
                f"{self._config.base_url}/chat/completions",
                headers=headers,
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            return {"rationale": content, "commentary": ""}

    async def health_check(self) -> bool:
        """Check API key validity via /models endpoint.

        Returns:
            True if the API key is configured and the models endpoint responds.
        """
        if not self._config.api_key:
            self._last_health = False
            return False

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(
                    f"{self._config.base_url}/models",
                    headers={
                        "Authorization": f"Bearer {self._config.api_key}"
                    },
                )
                self._last_health = resp.status_code == 200
                return self._last_health
        except Exception:
            self._last_health = False
            return False

    def is_available(self) -> bool:
        """Return cached health check result.

        Returns:
            True if the last health check passed.
        """
        return self._last_health
