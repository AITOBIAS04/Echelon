"""Ollama Provider -- wraps Ollama local API for Qwen 3.5 4B/9B (T1).

Structured output mode via JSON schema enforcement.
Health check verifies Ollama is running and the model is loaded.
Fallback: T1 degrades to pure rules engine when Ollama unavailable.

Cycle-013, Sprint 2 -- Task 4.
"""
from __future__ import annotations

import json
from typing import Optional

import httpx

from backend.agents.model_providers import BaseModelProvider, ProviderConfig


class OllamaProvider(BaseModelProvider):
    """Wraps Ollama's local API for Qwen 3.5 4B/9B.

    Structured output via JSON schema enforcement.
    Fallback: T1 degrades to pure rules engine.
    """

    DEFAULT_URL = "http://localhost:11434"
    DEFAULT_MODEL = "qwen3.5:4b"

    def __init__(self, config: Optional[ProviderConfig] = None) -> None:
        super().__init__(
            config
            or ProviderConfig(
                base_url=self.DEFAULT_URL,
                model_name=self.DEFAULT_MODEL,
            )
        )
        self._last_health: bool = False

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        response_schema: Optional[dict] = None,
    ) -> dict:
        """Call Ollama /api/generate with structured output.

        Args:
            system_prompt: System instructions for the model.
            user_prompt: User prompt with trading context.
            response_schema: Optional JSON schema for structured output.

        Returns:
            Parsed dict from model response.

        Raises:
            httpx.HTTPStatusError: On non-2xx response.
            json.JSONDecodeError: If response is not valid JSON.
        """
        payload: dict = {
            "model": self._config.model_name,
            "prompt": user_prompt,
            "system": system_prompt,
            "stream": False,
        }
        if response_schema:
            payload["format"] = response_schema

        async with httpx.AsyncClient(timeout=self._config.timeout_s) as client:
            resp = await client.post(
                f"{self._config.base_url}/api/generate",
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            response_text = data.get("response", "{}")
            return json.loads(response_text)

    async def health_check(self) -> bool:
        """Verify Ollama is running and model is loaded.

        Checks /api/tags endpoint for the configured model name.

        Returns:
            True if Ollama is running and the model is available.
        """
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{self._config.base_url}/api/tags")
                if resp.status_code != 200:
                    self._last_health = False
                    return False
                models = resp.json().get("models", [])
                model_names = [m.get("name", "") for m in models]
                self._last_health = any(
                    self._config.model_name in name for name in model_names
                )
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
