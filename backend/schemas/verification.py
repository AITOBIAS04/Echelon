"""
Pydantic schemas for the Verification API.
"""

from pydantic import BaseModel, ConfigDict, Field, model_validator
from typing import Optional, List, Literal
from datetime import datetime


# ============================================
# REQUEST SCHEMAS
# ============================================

class VerificationRunCreate(BaseModel):
    """Request body for POST /api/v1/verification/runs."""
    repo_url: str = Field(..., min_length=1, max_length=500)
    construct_id: str = Field(..., min_length=1, max_length=255)
    oracle_type: Literal["http", "python"] = "http"
    oracle_url: Optional[str] = None
    oracle_headers: dict[str, str] = {}
    oracle_module: Optional[str] = None
    oracle_callable: Optional[str] = None
    limit: int = Field(100, ge=1, le=1000)
    min_replays: int = Field(50, ge=1, le=500)
    github_token: Optional[str] = None

    @model_validator(mode="after")
    def validate_oracle_config(self) -> "VerificationRunCreate":
        if self.oracle_type == "http" and not self.oracle_url:
            raise ValueError("oracle_url is required when oracle_type is 'http'")
        if self.oracle_type == "python":
            if not self.oracle_module or not self.oracle_callable:
                raise ValueError(
                    "oracle_module and oracle_callable are required when oracle_type is 'python'"
                )
        return self


# ============================================
# RESPONSE SCHEMAS
# ============================================

class VerificationRunResponse(BaseModel):
    """Response for a single verification run."""
    run_id: str
    status: str
    progress: int
    total: int
    construct_id: str
    repo_url: str
    error: Optional[str]
    certificate_id: Optional[str]
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class VerificationRunListResponse(BaseModel):
    """Paginated list of verification runs."""
    runs: List[VerificationRunResponse]
    total: int
    limit: int
    offset: int


class ReplayScoreResponse(BaseModel):
    """Response for a single replay score."""
    id: str
    ground_truth_id: str
    precision: float
    recall: float
    reply_accuracy: float
    claims_total: int
    claims_supported: int
    changes_total: int
    changes_surfaced: int
    scoring_model: str
    scoring_latency_ms: int
    scored_at: datetime
    model_config = ConfigDict(from_attributes=True)


class CertificateResponse(BaseModel):
    """Full certificate with replay scores."""
    id: str
    construct_id: str
    domain: str
    replay_count: int
    precision: float
    recall: float
    reply_accuracy: float
    composite_score: float
    brier: float
    sample_size: int
    ground_truth_source: str
    methodology_version: str
    scoring_model: str
    created_at: datetime
    replay_scores: List[ReplayScoreResponse] = []
    model_config = ConfigDict(from_attributes=True)


class CertificateSummaryResponse(BaseModel):
    """Certificate list view — no replay_scores."""
    id: str
    construct_id: str
    domain: str
    replay_count: int
    composite_score: float
    brier: float
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class CertificateListResponse(BaseModel):
    """Paginated list of certificates."""
    certificates: List[CertificateSummaryResponse]
    total: int
    limit: int
    offset: int
