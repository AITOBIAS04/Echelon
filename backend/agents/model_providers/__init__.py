"""Model Providers -- abstract base and configuration for LLM providers.

Defines BaseModelProvider ABC with generate(), health_check(), is_available().
Three implementations: Ollama (T1), Mistral (T2), Anthropic (T3).
All providers have graceful fallback when unavailable.

Cycle-013, Sprint 2 -- Task 4 (partial).
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class ProviderConfig:
    """Configuration for a model provider.

    Attributes:
        api_key: API key for authenticated providers (Mistral, Anthropic).
        base_url: Base URL for the provider API.
        model_name: Model identifier to use.
        timeout_s: HTTP request timeout in seconds.
        max_retries: Maximum number of retry attempts.
    """

    api_key: Optional[str] = None
    base_url: str = ""
    model_name: str = ""
    timeout_s: float = 30.0
    max_retries: int = 2


class BaseModelProvider(ABC):
    """Abstract base class for all model providers.

    Defines the common interface: generate(), health_check(), is_available().
    Subclasses implement provider-specific logic for Ollama, Mistral, Anthropic.
    """

    def __init__(self, config: ProviderConfig) -> None:
        self._config = config

    @abstractmethod
    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        response_schema: Optional[dict] = None,
    ) -> dict:
        """Generate a response from the model.

        Args:
            system_prompt: System-level instructions for the model.
            user_prompt: User-level prompt with context.
            response_schema: Optional JSON schema for structured output.

        Returns:
            Parsed dict with model response.

        Raises:
            Exception: On provider communication failure.
        """
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the provider is available and responsive.

        Returns:
            True if the provider is healthy and ready to serve requests.
        """
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """Synchronous availability check based on last health check result.

        Returns:
            True if the last health check passed.
        """
        ...
