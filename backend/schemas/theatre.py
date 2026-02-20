"""Pydantic schemas for the Theatre API."""

from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


# ============================================
# REQUEST SCHEMAS
# ============================================


class TheatreCreate(BaseModel):
    """Request body for POST /api/v1/theatres."""

    template_id: str = Field(..., min_length=1, max_length=100)
    construct_id: str = Field(..., min_length=1, max_length=255)
    template_json: dict = Field(..., description="Full template JSON for validation")
    version_pins: dict = Field(default_factory=dict)
    dataset_hashes: dict = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_template_json(self) -> "TheatreCreate":
        if "theatre_id" not in self.template_json:
            raise ValueError("template_json must contain 'theatre_id'")
        if "execution_path" not in self.template_json:
            raise ValueError("template_json must contain 'execution_path'")
        return self


class TheatreRunRequest(BaseModel):
    """Request body for POST /api/v1/theatres/{id}/run."""

    ground_truth_path: Optional[str] = Field(
        None, max_length=500,
        description="Override path for ground truth dataset"
    )
    is_certificate_run: bool = Field(
        False, description="Whether this run produces a certificate"
    )


class TheatreSettleRequest(BaseModel):
    """Request body for POST /api/v1/theatres/{id}/settle (Market only)."""

    settlement_data: dict = Field(
        default_factory=dict,
        description="Market settlement data"
    )


# ============================================
# RESPONSE SCHEMAS
# ============================================


class TemplateResponse(BaseModel):
    """Response for a single template."""

    id: str
    template_family: str
    execution_path: str
    display_name: str
    description: Optional[str]
    schema_version: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class TemplateListResponse(BaseModel):
    """Paginated list of templates."""

    templates: List[TemplateResponse]
    total: int
    limit: int
    offset: int


class CommitmentReceiptResponse(BaseModel):
    """Public commitment receipt."""

    theatre_id: str
    commitment_hash: str
    committed_at: datetime
    version_pins: dict
    dataset_hashes: dict
    model_config = ConfigDict(from_attributes=True)


class TheatreResponse(BaseModel):
    """Full Theatre state view."""

    id: str
    user_id: str
    template_id: str
    state: str
    construct_id: str
    commitment_hash: Optional[str]
    committed_at: Optional[datetime]
    progress: int
    total_episodes: int
    failure_count: int
    error: Optional[str]
    resolved_at: Optional[datetime]
    certificate_id: Optional[str]
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class TheatreListResponse(BaseModel):
    """Paginated list of theatres."""

    theatres: List[TheatreResponse]
    total: int
    limit: int
    offset: int


class TheatreCertificateResponse(BaseModel):
    """Full certificate with all fields."""

    id: str
    theatre_id: str
    template_id: str
    construct_id: str
    criteria_json: dict
    scores_json: dict
    composite_score: float
    precision: Optional[float]
    recall: Optional[float]
    brier_score: Optional[float]
    ece: Optional[float]
    replay_count: int
    evidence_bundle_hash: str
    ground_truth_hash: str
    construct_version: str
    construct_chain_versions: Optional[dict]
    scorer_version: str
    methodology_version: str
    dataset_hash: str
    verification_tier: str
    commitment_hash: str
    issued_at: datetime
    expires_at: Optional[datetime]
    theatre_committed_at: datetime
    theatre_resolved_at: datetime
    ground_truth_source: str
    execution_path: str
    model_config = ConfigDict(from_attributes=True)


class TheatreCertificateSummaryResponse(BaseModel):
    """Certificate list view — compact."""

    id: str
    theatre_id: str
    construct_id: str
    composite_score: float
    verification_tier: str
    replay_count: int
    execution_path: str
    issued_at: datetime
    model_config = ConfigDict(from_attributes=True)


class CertificateListResponse(BaseModel):
    """Paginated list of certificates."""

    certificates: List[TheatreCertificateSummaryResponse]
    total: int
    limit: int
    offset: int
