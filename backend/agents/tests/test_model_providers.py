"""Tests for Model Providers -- BaseModelProvider, Ollama, Mistral, Anthropic.

All tests use mocked providers. No live API calls in default test suite.
Live integration tests marked with @pytest.mark.requires_ollama,
@pytest.mark.requires_mistral, @pytest.mark.requires_anthropic.

Cycle-013, Sprint 2 -- Task 7.
"""
from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.agents.model_providers import BaseModelProvider, ProviderConfig
from backend.agents.model_providers.ollama_provider import OllamaProvider
from backend.agents.model_providers.mistral_provider import MistralProvider
from backend.agents.model_providers.anthropic_provider import AnthropicProvider


# ===================================================================
# Helpers
# ===================================================================


def _mock_async_client(
    post_response: MagicMock = None,
    get_response: MagicMock = None,
    get_side_effect: Exception = None,
) -> MagicMock:
    """Create a mock httpx.AsyncClient context manager.

    Returns a MagicMock that, when used as `async with`, returns a client
    with configurable post() and get() AsyncMock methods.
    """
    mock_client = AsyncMock()
    if post_response is not None:
        mock_client.post = AsyncMock(return_value=post_response)
    if get_response is not None:
        mock_client.get = AsyncMock(return_value=get_response)
    if get_side_effect is not None:
        mock_client.get = AsyncMock(side_effect=get_side_effect)

    # Make the mock work as an async context manager
    mock_cm = MagicMock()
    mock_cm.__aenter__ = AsyncMock(return_value=mock_client)
    mock_cm.__aexit__ = AsyncMock(return_value=None)
    return mock_cm


# ===================================================================
# BaseModelProvider ABC Tests
# ===================================================================


class TestBaseModelProvider:
    """Verify BaseModelProvider interface enforcement."""

    def test_cannot_instantiate_abc(self) -> None:
        """BaseModelProvider is abstract and cannot be instantiated."""
        with pytest.raises(TypeError):
            BaseModelProvider(ProviderConfig())  # type: ignore

    def test_provider_config_defaults(self) -> None:
        """ProviderConfig has sensible defaults."""
        cfg = ProviderConfig()
        assert cfg.api_key is None
        assert cfg.base_url == ""
        assert cfg.model_name == ""
        assert cfg.timeout_s == 30.0
        assert cfg.max_retries == 2

    def test_provider_config_custom(self) -> None:
        """ProviderConfig accepts custom values."""
        cfg = ProviderConfig(
            api_key="test-key",
            base_url="http://localhost:8080",
            model_name="test-model",
            timeout_s=10.0,
            max_retries=5,
        )
        assert cfg.api_key == "test-key"
        assert cfg.base_url == "http://localhost:8080"
        assert cfg.model_name == "test-model"
        assert cfg.timeout_s == 10.0
        assert cfg.max_retries == 5


# ===================================================================
# OllamaProvider Tests (Mocked)
# ===================================================================


class TestOllamaProvider:
    """Verify OllamaProvider with mocked HTTP calls."""

    def test_default_config(self) -> None:
        """OllamaProvider uses localhost:11434 and qwen3.5:4b by default."""
        provider = OllamaProvider()
        assert provider._config.base_url == "http://localhost:11434"
        assert provider._config.model_name == "qwen3.5:4b"
        assert provider.is_available() is False  # No health check yet

    def test_custom_config(self) -> None:
        """OllamaProvider accepts custom ProviderConfig."""
        cfg = ProviderConfig(
            base_url="http://custom:5000",
            model_name="qwen3.5:9b",
        )
        provider = OllamaProvider(config=cfg)
        assert provider._config.base_url == "http://custom:5000"
        assert provider._config.model_name == "qwen3.5:9b"

    @pytest.mark.asyncio
    async def test_generate_mocked(self) -> None:
        """generate() returns parsed JSON from Ollama response."""
        provider = OllamaProvider()
        expected_response = {"action": "BUY", "confidence": 0.8}

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "response": json.dumps(expected_response)
        }

        mock_cm = _mock_async_client(post_response=mock_response)
        with patch("backend.agents.model_providers.ollama_provider.httpx.AsyncClient", return_value=mock_cm):
            result = await provider.generate(
                system_prompt="test system",
                user_prompt="test user",
            )
        assert result == expected_response

    @pytest.mark.asyncio
    async def test_health_check_success(self) -> None:
        """health_check() returns True when model is loaded."""
        provider = OllamaProvider()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "models": [{"name": "qwen3.5:4b"}]
        }

        mock_cm = _mock_async_client(get_response=mock_response)
        with patch("backend.agents.model_providers.ollama_provider.httpx.AsyncClient", return_value=mock_cm):
            result = await provider.health_check()
        assert result is True
        assert provider.is_available() is True

    @pytest.mark.asyncio
    async def test_health_check_model_not_loaded(self) -> None:
        """health_check() returns False when model is not in the list."""
        provider = OllamaProvider()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "models": [{"name": "llama3:7b"}]
        }

        mock_cm = _mock_async_client(get_response=mock_response)
        with patch("backend.agents.model_providers.ollama_provider.httpx.AsyncClient", return_value=mock_cm):
            result = await provider.health_check()
        assert result is False
        assert provider.is_available() is False

    @pytest.mark.asyncio
    async def test_health_check_connection_refused(self) -> None:
        """health_check() returns False when Ollama is not running."""
        provider = OllamaProvider()

        mock_cm = _mock_async_client(
            get_side_effect=ConnectionError("refused")
        )
        with patch("backend.agents.model_providers.ollama_provider.httpx.AsyncClient", return_value=mock_cm):
            result = await provider.health_check()
        assert result is False
        assert provider.is_available() is False

    @pytest.mark.asyncio
    async def test_is_available_reflects_health(self) -> None:
        """is_available() reflects the result of the last health_check()."""
        provider = OllamaProvider()
        assert provider.is_available() is False

        # Simulate successful health check
        provider._last_health = True
        assert provider.is_available() is True


# ===================================================================
# MistralProvider Tests (Mocked)
# ===================================================================


class TestMistralProvider:
    """Verify MistralProvider with mocked HTTP calls."""

    def test_default_config(self) -> None:
        """MistralProvider uses api.mistral.ai and mistral-small-latest."""
        provider = MistralProvider()
        assert provider._config.base_url == "https://api.mistral.ai/v1"
        assert provider._config.model_name == "mistral-small-latest"
        assert provider.is_available() is False

    @pytest.mark.asyncio
    async def test_generate_mocked(self) -> None:
        """generate() returns rationale and commentary from Mistral response."""
        cfg = ProviderConfig(
            api_key="test-key",
            base_url="https://api.mistral.ai/v1",
            model_name="mistral-small-latest",
        )
        provider = MistralProvider(config=cfg)

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "choices": [
                {"message": {"content": "Blood in the water. We strike."}}
            ]
        }

        mock_cm = _mock_async_client(post_response=mock_response)
        with patch("backend.agents.model_providers.mistral_provider.httpx.AsyncClient", return_value=mock_cm):
            result = await provider.generate(
                system_prompt="You are a shark trader",
                user_prompt="Action: BUY, Confidence: 80%",
            )
        assert result["rationale"] == "Blood in the water. We strike."
        assert result["commentary"] == ""

    @pytest.mark.asyncio
    async def test_health_check_no_api_key(self) -> None:
        """health_check() returns False when API key is missing."""
        provider = MistralProvider()  # No API key
        result = await provider.health_check()
        assert result is False
        assert provider.is_available() is False

    @pytest.mark.asyncio
    async def test_health_check_success(self) -> None:
        """health_check() returns True when API responds 200."""
        cfg = ProviderConfig(
            api_key="test-key",
            base_url="https://api.mistral.ai/v1",
        )
        provider = MistralProvider(config=cfg)

        mock_response = MagicMock()
        mock_response.status_code = 200

        mock_cm = _mock_async_client(get_response=mock_response)
        with patch("backend.agents.model_providers.mistral_provider.httpx.AsyncClient", return_value=mock_cm):
            result = await provider.health_check()
        assert result is True
        assert provider.is_available() is True

    @pytest.mark.asyncio
    async def test_health_check_connection_error(self) -> None:
        """health_check() returns False on connection error."""
        cfg = ProviderConfig(
            api_key="test-key",
            base_url="https://api.mistral.ai/v1",
        )
        provider = MistralProvider(config=cfg)

        mock_cm = _mock_async_client(
            get_side_effect=ConnectionError("refused")
        )
        with patch("backend.agents.model_providers.mistral_provider.httpx.AsyncClient", return_value=mock_cm):
            result = await provider.health_check()
        assert result is False


# ===================================================================
# AnthropicProvider Tests (Mocked)
# ===================================================================


class TestAnthropicProvider:
    """Verify AnthropicProvider with mocked HTTP calls."""

    def test_default_config(self) -> None:
        """AnthropicProvider uses api.anthropic.com and claude-sonnet."""
        provider = AnthropicProvider()
        assert provider._config.base_url == "https://api.anthropic.com/v1"
        assert "claude" in provider._config.model_name
        assert provider.is_available() is False

    @pytest.mark.asyncio
    async def test_generate_structured_json(self) -> None:
        """generate() returns parsed structured JSON from Anthropic response."""
        cfg = ProviderConfig(
            api_key="test-key",
            base_url="https://api.anthropic.com/v1",
            model_name="claude-sonnet-4-5-20241022",
        )
        provider = AnthropicProvider(config=cfg)

        structured_response = {
            "action": "BUY",
            "outcome_index": 0,
            "shares": 100.0,
            "confidence": 0.85,
            "reasoning_summary": "Strong evidence for outcome 0",
            "evidence_refs": ["bundle_001"],
            "pattern_name": "deep_analysis",
        }

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "content": [{"text": json.dumps(structured_response)}]
        }

        mock_cm = _mock_async_client(post_response=mock_response)
        with patch("backend.agents.model_providers.anthropic_provider.httpx.AsyncClient", return_value=mock_cm):
            result = await provider.generate(
                system_prompt="Deep reasoning",
                user_prompt="Analyse this market",
            )
        assert result["action"] == "BUY"
        assert result["confidence"] == 0.85
        assert result["evidence_refs"] == ["bundle_001"]

    @pytest.mark.asyncio
    async def test_generate_json_parse_failure_fallback(self) -> None:
        """generate() falls back to HOLD when response is not valid JSON."""
        cfg = ProviderConfig(
            api_key="test-key",
            base_url="https://api.anthropic.com/v1",
            model_name="claude-sonnet-4-5-20241022",
        )
        provider = AnthropicProvider(config=cfg)

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "content": [{"text": "I think you should hold this position because..."}]
        }

        mock_cm = _mock_async_client(post_response=mock_response)
        with patch("backend.agents.model_providers.anthropic_provider.httpx.AsyncClient", return_value=mock_cm):
            result = await provider.generate(
                system_prompt="Deep reasoning",
                user_prompt="Analyse this market",
            )
        assert result["action"] == "HOLD"
        assert result["confidence"] == 0.5
        assert "hold this position" in result["reasoning_summary"]
        assert result["evidence_refs"] == []
        assert result["pattern_name"] == "deep_analysis"

    @pytest.mark.asyncio
    async def test_health_check_no_api_key(self) -> None:
        """health_check() returns False when API key is missing."""
        provider = AnthropicProvider()
        result = await provider.health_check()
        assert result is False
        assert provider.is_available() is False

    @pytest.mark.asyncio
    async def test_health_check_with_api_key(self) -> None:
        """health_check() returns True when API key is configured."""
        cfg = ProviderConfig(api_key="test-key")
        provider = AnthropicProvider(config=cfg)
        result = await provider.health_check()
        assert result is True
        assert provider.is_available() is True
