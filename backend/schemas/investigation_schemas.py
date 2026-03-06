"""Investigation API schemas — Pydantic models for investigation REST endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ============================================
# REQUEST SCHEMAS
# ============================================


class InvestigationCreateRequest(BaseModel):
    """Request to create a new investigation."""

    theatre_id: str = ""
    construct_id: str = ""
    inquiry_class: str = "INVESTIGATIVE"
    domain_filters: list[str] = Field(default_factory=list)
    stop_condition: str = "OUTCOME_RESOLUTION"
    stop_config: dict = Field(default_factory=dict)


class EvidenceSubmitRequest(BaseModel):
    """Request to submit evidence to an investigation."""

    content_base64: str  # Base64-encoded content bytes
    provenance_class: str  # ProvenanceClass value
    content_type: str = "text/plain"
    source_description: str = ""
    source_id: str = ""  # OSINT registry source_id for policy enforcement
    receipt_body: str = ""  # Receipt content when receipt_body_required
    references: list[str] = Field(default_factory=list)


class ClaimCreateRequest(BaseModel):
    """Request to register a claim in the claim graph."""

    claim_text: str
    claim_type: str  # ClaimType value: fact, causal, attribution
    evidence_refs: list[str] = Field(default_factory=list)


class CounterSignalCreateRequest(BaseModel):
    """Request to log a counter-signal."""

    signal_class: str  # InvestigationCounterSignalClass value
    material: bool = False
    resolution_impact: str = ""
    detection_method: str = "human_submitted"
    evidence_ref: Optional[str] = None


# ============================================
# RESPONSE SCHEMAS
# ============================================


class EvidenceItemResponse(BaseModel):
    """Single evidence item."""

    evidence_id: str
    content_hash: str
    provenance_class: str
    submitted_at: datetime
    content_type: str
    source_description: str
    references: list[str] = Field(default_factory=list)
    source_id: str = ""
    query_determinism: str = ""


class RedactionEventResponse(BaseModel):
    """Single redaction event."""

    redaction_id: str
    evidence_id: str
    reason_class: str
    redacted_at: datetime


class EvidenceEnvelopeResponse(BaseModel):
    """Evidence envelope manifest."""

    items: list[EvidenceItemResponse] = Field(default_factory=list)
    redactions: list[RedactionEventResponse] = Field(default_factory=list)
    provenance_summary: dict = Field(default_factory=dict)
    envelope_hash: str = ""


class ClaimNodeResponse(BaseModel):
    """Single claim node."""

    claim_id: str
    claim_text: str
    claim_type: str
    evidence_refs: list[str] = Field(default_factory=list)
    counter_signals: list[str] = Field(default_factory=list)
    status: str = "unconfirmed"
    confidence: float = 0.0
    independence_groups: list[str] = Field(default_factory=list)


class ClaimGraphResponse(BaseModel):
    """Claim graph summary."""

    claims: list[ClaimNodeResponse] = Field(default_factory=list)
    root_hash: str = ""
    status_summary: dict = Field(default_factory=dict)


class CounterSignalResponse(BaseModel):
    """Single counter-signal."""

    counter_signal_id: str
    signal_class: str
    detected_at: datetime
    evidence_ref: Optional[str] = None
    material: bool
    resolution_impact: str
    detection_method: str


class CounterSignalFeedResponse(BaseModel):
    """Counter-signal feed summary."""

    signals: list[CounterSignalResponse] = Field(default_factory=list)
    summary: dict = Field(default_factory=dict)


class DriftEventResponse(BaseModel):
    """Single drift event."""

    drift_id: str
    drift_type: str
    detected_at: datetime
    original_value: str
    new_value: str
    evidence_ref: Optional[str] = None
    impact_assessment: str


class DriftFeedResponse(BaseModel):
    """Drift events summary."""

    events: list[DriftEventResponse] = Field(default_factory=list)
    has_material_drift: bool = False


class InvestigationSummaryResponse(BaseModel):
    """Summary of a single investigation."""

    id: str
    theatre_id: str
    construct_id: str
    inquiry_class: str
    status: str  # active, completed
    evidence_count: int = 0
    claim_count: int = 0
    counter_signal_count: int = 0
    drift_event_count: int = 0
    created_at: datetime
    updated_at: datetime


class InvestigationListResponse(BaseModel):
    """List of investigation summaries."""

    investigations: list[InvestigationSummaryResponse] = Field(default_factory=list)
    total: int = 0


class InvestigationDetailResponse(BaseModel):
    """Full investigation detail with all sub-components."""

    id: str
    theatre_id: str
    construct_id: str
    inquiry_class: str
    status: str
    stop_condition: str
    stop_config: dict = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime
    evidence: EvidenceEnvelopeResponse
    claims: ClaimGraphResponse
    counter_signals: CounterSignalFeedResponse
    drift: DriftFeedResponse
    has_legal_review_requirement: bool = False


class CertificateResponse(BaseModel):
    """Investigation certificate response."""

    certificate_id: str
    theatre_id: str
    construct_id: str
    inquiry_class: str
    stop_condition: str
    stop_config: dict = Field(default_factory=dict)
    investigation_started_at: datetime
    investigation_completed_at: datetime
    evidence_item_count: int
    evidence_redaction_count: int
    evidence_envelope_hash: str
    provenance_summary: dict = Field(default_factory=dict)
    claim_count: int
    claim_status_summary: dict = Field(default_factory=dict)
    claim_graph_root_hash: str
    counter_signals_checked: int
    counter_signals_gaps: int
    counter_signals_material: int
    counter_signal_detail: list[dict] = Field(default_factory=list)
    drift_event_count: int
    has_material_drift: bool
    drift_events: list[dict] = Field(default_factory=list)
    routing_decision: str
    routing_reason: str
    certificate_hash: str
    anchoring_status: str = "pending"
    anchoring_tx_hash: Optional[str] = None
    issued_at: datetime
    methodology_version: str = "1.0.0"
    toolset_version: str = "0.1.0"
