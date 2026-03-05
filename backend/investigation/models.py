"""Core investigation models — ProvenanceClass enum and EvidenceItem."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class ProvenanceClass(str, Enum):
    """Classification of evidence provenance for settlement eligibility."""

    PUBLIC_PRIMARY = "public_primary"
    PUBLIC_SECONDARY = "public_secondary"
    PRIVATE_LEAK = "private_leak"
    ANALYST_DERIVED = "analyst_derived"
    THIRD_PARTY_TOOL_OUTPUT = "third_party_tool_output"


class EvidenceItem(BaseModel):
    """Immutable evidence item within an Evidence Envelope."""

    model_config = {"frozen": True}

    evidence_id: str
    content_hash: str
    provenance_class: ProvenanceClass
    submitted_at: datetime
    content_type: str
    source_description: str
    references: list[str] = Field(default_factory=list)
