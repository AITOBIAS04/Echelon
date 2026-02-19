"""Configuration management for the verification pipeline."""

from __future__ import annotations

import os
from typing import Literal

from pydantic import BaseModel, model_validator


class IngestionConfig(BaseModel):
    """GitHub ingestion configuration."""

    repo_url: str
    github_token: str | None = None
    limit: int = 100
    since: str | None = None  # ISO datetime string
    labels: list[str] = []
    merged_only: bool = True


class OracleConfig(BaseModel):
    """Oracle adapter configuration."""

    type: Literal["http", "python"]
    # HTTP mode
    url: str | None = None
    headers: dict[str, str] = {}
    timeout_seconds: int = 30
    # Python mode
    module: str | None = None
    callable: str | None = None

    @model_validator(mode="after")
    def validate_type_fields(self) -> "OracleConfig":
        if self.type == "http" and not self.url:
            raise ValueError("url is required when type='http'")
        if self.type == "python":
            if not self.module:
                raise ValueError("module is required when type='python'")
            if not self.callable:
                raise ValueError("callable is required when type='python'")
        return self


class ScoringConfig(BaseModel):
    """Scoring engine configuration."""

    provider: str = "anthropic"
    model: str = "claude-sonnet-4-6"
    api_key: str | None = None
    temperature: float = 0.0
    prompt_version: str = "v1"

    @model_validator(mode="after")
    def resolve_api_key(self) -> "ScoringConfig":
        if self.api_key is None:
            self.api_key = os.environ.get("ANTHROPIC_API_KEY")
        return self


class PipelineConfig(BaseModel):
    """Top-level pipeline configuration."""

    ingestion: IngestionConfig
    oracle: OracleConfig
    scoring: ScoringConfig = ScoringConfig()
    min_replays: int = 50
    composite_weights: dict[str, float] = {
        "precision": 1.0,
        "recall": 1.0,
        "reply_accuracy": 1.0,
    }
    output_dir: str = "data"
    construct_id: str = "unnamed-oracle"
