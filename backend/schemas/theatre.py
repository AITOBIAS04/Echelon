"""Pydantic schemas for the Theatre API."""

from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from backend.schemas.inquiry import resolve_inquiry_class


# ============================================
# REQUEST SCHEMAS
# ============================================


class TheatreCreate(BaseModel):
    """Request body for POST /api/v1/theatres."""

    template_id: str = Field(..., min_length=1, max_length=100)
    construct_id: str = Field(..., min_length=1, max_length=255)
    template_json: dict = Field(..., description="Full template JSON for validation")
    inquiry_class: str = Field(
        "COUNTERFACTUAL",
        description="Inquiry class (COUNTERFACTUAL|INVESTIGATIVE|INSPECTION|SURVEY|SCRUTINY). "
        "Extracted from template_json if not provided. Cannot be null.",
    )
    version_pins: dict = Field(default_factory=dict)
    dataset_hashes: dict = Field(default_factory=dict)
    stop_condition: Optional[str] = Field(
        None,
        max_length=30,
        description="Stop condition type (OUTCOME_RESOLUTION|EVIDENCE_THRESHOLD|SPONSOR_DEFINED)",
    )
    stop_config: Optional[dict] = Field(
        None,
        description="Stop condition configuration (thresholds, milestones, etc.)",
    )

    @field_validator("stop_condition", mode="before")
    @classmethod
    def validate_stop_condition(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        normalised = v.upper().strip()
        valid = {"OUTCOME_RESOLUTION", "EVIDENCE_THRESHOLD", "SPONSOR_DEFINED"}
        if normalised not in valid:
            raise ValueError(
                f"stop_condition must be one of {sorted(valid)}, got '{v}'"
            )
        return normalised

    @model_validator(mode="before")
    @classmethod
    def reject_null_inquiry_class(cls, values: dict) -> dict:
        """Reject explicit null for inquiry_class (returns 422)."""
        if isinstance(values, dict) and "inquiry_class" in values and values["inquiry_class"] is None:
            raise ValueError("inquiry_class cannot be null")
        return values

    @model_validator(mode="after")
    def validate_template_json(self) -> "TheatreCreate":
        if "theatre_id" not in self.template_json:
            raise ValueError("template_json must contain 'theatre_id'")
        if "execution_path" not in self.template_json:
            raise ValueError("template_json must contain 'execution_path'")
        # If inquiry_class is the default, check template_json for override
        if self.inquiry_class == "COUNTERFACTUAL":
            raw = self.template_json.get("inquiry_class")
            if raw is not None:
                self.inquiry_class = str(resolve_inquiry_class(raw))
        else:
            # Explicit value — validate it
            self.inquiry_class = str(resolve_inquiry_class(self.inquiry_class))
        return self

    @model_validator(mode="after")
    def validate_stop_config_shape(self) -> "TheatreCreate":
        # Stop fields are only valid for INVESTIGATIVE inquiry class
        if (self.stop_condition is not None or self.stop_config is not None) and self.inquiry_class != "INVESTIGATIVE":
            raise ValueError(
                f"stop_condition/stop_config are only allowed for INVESTIGATIVE inquiry class, "
                f"got inquiry_class='{self.inquiry_class}'"
            )

        if self.stop_config is not None and self.stop_condition is None:
            raise ValueError("stop_config requires stop_condition to be set")

        if self.stop_condition == "SPONSOR_DEFINED":
            cfg = self.stop_config or {}
            ms = cfg.get("milestone_timestamp")
            if ms is None:
                raise ValueError(
                    "SPONSOR_DEFINED requires milestone_timestamp in stop_config"
                )
            from datetime import datetime as _dt
            try:
                # Python 3.9 fromisoformat doesn't handle 'Z' suffix
                _dt.fromisoformat(str(ms).replace("Z", "+00:00"))
            except (ValueError, TypeError):
                raise ValueError(
                    f"milestone_timestamp must be valid ISO 8601, got '{ms}'"
                )

        if self.stop_condition == "EVIDENCE_THRESHOLD" and self.stop_config:
            cfg = self.stop_config
            msc = cfg.get("min_supported_claims")
            if msc is not None:
                if not isinstance(msc, int) or msc < 1:
                    raise ValueError(
                        f"min_supported_claims must be int >= 1, got {msc!r}"
                    )
            mcs = cfg.get("min_corroboration_score")
            if mcs is not None:
                if not isinstance(mcs, (int, float)) or not (0 <= mcs <= 1):
                    raise ValueError(
                        f"min_corroboration_score must be float 0-1, got {mcs!r}"
                    )

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
    inquiry_class: Optional[str] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="after")
    def coalesce_inquiry_class(self) -> "TemplateResponse":
        if self.inquiry_class is None:
            self.inquiry_class = "COUNTERFACTUAL"
        return self


class TemplateDetailResponse(TemplateResponse):
    """Detailed template view including full template JSON."""

    template_json: dict


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
    inquiry_class: Optional[str] = None
    commitment_hash: Optional[str]
    committed_at: Optional[datetime]
    progress: int
    total_episodes: int
    failure_count: int
    error: Optional[str]
    resolved_at: Optional[datetime]
    certificate_id: Optional[str]
    stop_condition: Optional[str] = None
    stop_config: Optional[dict] = None
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="after")
    def coalesce_inquiry_class(self) -> "TheatreResponse":
        if self.inquiry_class is None:
            self.inquiry_class = "COUNTERFACTUAL"
        return self


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
    inquiry_class: Optional[str] = None
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

    # ── Cycle-017: Policy Surface ──
    routing_hint: Optional[str] = None
    review_reason_code: Optional[str] = None
    coherence_review_required: bool = False
    coherence_gate_status: Optional[str] = None
    coherence_reviewed_at: Optional[datetime] = None
    is_deployable: bool = True

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="after")
    def coalesce_inquiry_class(self) -> "TheatreCertificateResponse":
        if self.inquiry_class is None:
            self.inquiry_class = "COUNTERFACTUAL"
        return self

    @model_validator(mode="after")
    def compute_is_deployable(self) -> "TheatreCertificateResponse":
        if self.routing_hint == "BLOCKED":
            self.is_deployable = False
        elif self.coherence_review_required and self.coherence_gate_status != "PASSED":
            self.is_deployable = False
        else:
            self.is_deployable = True
        return self


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

    # ── Cycle-017: Policy Surface ──
    routing_hint: Optional[str] = None
    coherence_gate_status: Optional[str] = None
    is_deployable: bool = True

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="after")
    def compute_is_deployable(self) -> "TheatreCertificateSummaryResponse":
        if self.routing_hint == "BLOCKED":
            self.is_deployable = False
        elif self.coherence_gate_status is not None and self.coherence_gate_status != "PASSED":
            self.is_deployable = False
        else:
            self.is_deployable = True
        return self


class CertificateListResponse(BaseModel):
    """Paginated list of certificates."""

    certificates: List[TheatreCertificateSummaryResponse]
    total: int
    limit: int
    offset: int
