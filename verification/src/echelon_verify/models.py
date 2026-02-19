"""Pydantic v2 data models for the verification pipeline."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Core models
# ---------------------------------------------------------------------------

class GroundTruthRecord(BaseModel):
    """A single PR/commit extracted from GitHub."""

    id: str
    title: str
    description: str = ""
    diff_content: str
    files_changed: list[str]
    timestamp: datetime
    labels: list[str] = []
    author: str
    url: str
    repo: str  # owner/repo format


class OracleOutput(BaseModel):
    """Output captured from oracle construct invocation."""

    ground_truth_id: str
    summary: str
    key_claims: list[str]
    follow_up_question: str
    follow_up_response: str
    metadata: dict[str, Any] = {}
    invoked_at: datetime
    latency_ms: int


class ReplayScore(BaseModel):
    """Per-replay verification score."""

    ground_truth_id: str
    precision: float = Field(ge=0.0, le=1.0)
    recall: float = Field(ge=0.0, le=1.0)
    reply_accuracy: float = Field(ge=0.0, le=1.0)
    claims_total: int = Field(ge=0)
    claims_supported: int = Field(ge=0)
    changes_total: int = Field(ge=0)
    changes_surfaced: int = Field(ge=0)
    scoring_model: str
    scoring_latency_ms: int
    scored_at: datetime
    raw_scoring_output: dict[str, Any] = {}


class CalibrationCertificate(BaseModel):
    """Aggregate verification certificate."""

    schema_version: str = "1.0.0"
    certificate_id: str = Field(default_factory=lambda: str(uuid4()))
    construct_id: str
    domain: Literal["community_oracle"] = "community_oracle"
    replay_count: int = Field(ge=1)
    precision: float = Field(ge=0.0, le=1.0)
    recall: float = Field(ge=0.0, le=1.0)
    reply_accuracy: float = Field(ge=0.0, le=1.0)
    composite_score: float = Field(ge=0.0, le=1.0)
    brier: float = Field(ge=0.0, le=0.5)
    sample_size: int = Field(ge=1)
    timestamp: datetime
    ground_truth_source: str
    commit_range: str
    methodology_version: str
    scoring_model: str
    individual_scores: list[ReplayScore] = []


# ---------------------------------------------------------------------------
# API models
# ---------------------------------------------------------------------------

class VerificationRunRequest(BaseModel):
    """Request to start a verification run via API."""

    repo_url: str
    construct: "OracleConfig"
    scoring: "ScoringConfig" = None  # type: ignore[assignment]
    min_replays: int = 50
    construct_id: str = "unnamed-oracle"
    github_token: str | None = None
    limit: int = 100

    def model_post_init(self, __context: Any) -> None:
        if self.scoring is None:
            from echelon_verify.config import ScoringConfig

            self.scoring = ScoringConfig()


class VerificationRunStatus(BaseModel):
    """Status of an in-progress verification run."""

    job_id: str
    status: Literal[
        "pending",
        "ingesting",
        "invoking",
        "scoring",
        "certifying",
        "completed",
        "failed",
    ]
    progress: int = 0
    total: int = 0
    started_at: datetime
    error: str | None = None


class VerificationRunResult(BaseModel):
    """Result of a completed verification run."""

    job_id: str
    certificate: CalibrationCertificate
    completed_at: datetime


# Deferred import resolution
from echelon_verify.config import OracleConfig, ScoringConfig  # noqa: E402

VerificationRunRequest.model_rebuild()
