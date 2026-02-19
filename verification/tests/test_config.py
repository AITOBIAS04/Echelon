"""Unit tests for configuration models."""

from __future__ import annotations

import os

import pytest
from pydantic import ValidationError

from echelon_verify.config import (
    IngestionConfig,
    OracleConfig,
    PipelineConfig,
    ScoringConfig,
)


class TestOracleConfig:
    def test_http_requires_url(self) -> None:
        with pytest.raises(ValidationError, match="url is required"):
            OracleConfig(type="http")

    def test_http_valid(self) -> None:
        cfg = OracleConfig(type="http", url="http://localhost:8000/summarize")
        assert cfg.url == "http://localhost:8000/summarize"
        assert cfg.timeout_seconds == 30

    def test_python_requires_module_and_callable(self) -> None:
        with pytest.raises(ValidationError, match="module is required"):
            OracleConfig(type="python")

        with pytest.raises(ValidationError, match="callable is required"):
            OracleConfig(type="python", module="my_oracle")

    def test_python_valid(self) -> None:
        cfg = OracleConfig(
            type="python", module="my_oracle.engine", callable="run"
        )
        assert cfg.module == "my_oracle.engine"
        assert cfg.callable == "run"


class TestScoringConfig:
    def test_defaults(self) -> None:
        cfg = ScoringConfig()
        assert cfg.provider == "anthropic"
        assert cfg.model == "claude-sonnet-4-6"
        assert cfg.temperature == 0.0
        assert cfg.prompt_version == "v1"

    def test_api_key_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-123")
        cfg = ScoringConfig()
        assert cfg.api_key == "sk-test-123"

    def test_explicit_api_key_overrides_env(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-from-env")
        cfg = ScoringConfig(api_key="sk-explicit")
        assert cfg.api_key == "sk-explicit"


class TestPipelineConfig:
    def test_default_composite_weights(self) -> None:
        cfg = PipelineConfig(
            ingestion=IngestionConfig(repo_url="https://github.com/o/r"),
            oracle=OracleConfig(type="http", url="http://localhost:8000"),
        )
        assert cfg.composite_weights == {
            "precision": 1.0,
            "recall": 1.0,
            "reply_accuracy": 1.0,
        }
        assert cfg.min_replays == 50
        assert cfg.construct_id == "unnamed-oracle"
