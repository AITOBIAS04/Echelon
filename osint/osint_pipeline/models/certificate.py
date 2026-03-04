"""
Calibration certificate model for the Echelon OSINT Pipeline.

A certificate attests that a specific verification inquiry was executed
against live OSINT sources, corroborated, scored, and the evidence
bundle is intact. The certificate's evidence_bundle_hash binds it
cryptographically to the evidence directory.

See System Bible Section 16.1 for certificate field requirements.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator

from osint_pipeline.models.oracle_output import CriterionScore


class CalibrationCertificate(BaseModel):
    """
    Immutable attestation of a completed OSINT verification.

    Once issued, the certificate is identified by its canonical JSON hash.
    """

    certificate_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique identifier (UUID v4)",
    )
    certificate_version: str = Field(
        default="1.0.0",
        description="Certificate schema version",
    )
    theatre_id: str = Field(description="Theatre template ID")
    inquiry_class: str = Field(
        description="COUNTERFACTUAL | INVESTIGATIVE | INSPECTION | SURVEY | SCRUTINY",
    )
    execution_path: str = Field(description="replay | market")
    resolution_trigger_reason: str = Field(
        default="",
        description="Why resolution was triggered (e.g. evidence_threshold_met, time_window_closed)",
    )

    # Verification result
    verification_tier: str = Field(
        description="UNVERIFIED | BACKTESTED | PROVEN",
    )
    composite_score: float = Field(
        ge=0.0, le=1.0,
        description="Weighted composite across all criteria",
    )
    all_criteria_passed: bool = Field(
        description="True if every criterion scored passed=True",
    )

    # Per-criterion scores
    criterion_scores: list[CriterionScore] = Field(default_factory=list)

    # Evidence integrity
    evidence_bundle_hash: str = Field(
        description="SHA-256 of canonical JSON manifest",
    )
    commitment_hash: str = Field(
        description="SHA-256 of theatre template canonical JSON",
    )

    # Oracle summary
    sources_queried: int = 0
    sources_succeeded: int = 0
    sources_failed: int = 0
    distinct_upstream_count: int = 0
    corroboration_met: bool = False
    counter_signals_checked: int = 0
    counter_signals_found: int = 0

    # Provenance
    issued_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )
    oracle_id: str = Field(description="OracleOutput.oracle_id reference")
    target_entity: dict[str, Any] = Field(
        default_factory=dict,
        description="Entity under verification (e.g. company_number, company_name)",
    )
    pipeline_version: str = Field(
        default="0.6.0",
        description="Pipeline software version",
    )

    @field_validator("inquiry_class")
    @classmethod
    def validate_inquiry_class(cls, v: str) -> str:
        valid = {"COUNTERFACTUAL", "INVESTIGATIVE", "INSPECTION", "SURVEY", "SCRUTINY"}
        upper = v.upper().strip()
        if upper not in valid:
            raise ValueError(
                f"Invalid inquiry_class '{v}'. Must be one of: {sorted(valid)}"
            )
        return upper

    @field_validator("evidence_bundle_hash", "commitment_hash")
    @classmethod
    def validate_hash_format(cls, v: str) -> str:
        if len(v) != 64 or not all(c in "0123456789abcdef" for c in v):
            raise ValueError(f"Hash must be 64-char lowercase hex, got: {v[:20]}...")
        return v

    @model_validator(mode="after")
    def validate_resolution_trigger(self) -> "CalibrationCertificate":
        """Validate resolution trigger matches expected types for inquiry class.

        Maps each inquiry class to its expected primary trigger types.
        time_window_closed is universally acceptable as a fallback.
        Empty trigger reason is allowed (backward compat).
        """
        if not self.resolution_trigger_reason:
            return self  # empty is allowed (backward compat)

        expected_triggers = {
            "COUNTERFACTUAL": {
                "simulation_terminal", "evidence_threshold_met", "time_window_closed",
            },
            "INVESTIGATIVE": {
                "evidence_threshold_met", "time_window_closed",
            },
            "INSPECTION": {
                "criteria_complete", "time_window_closed",
            },
            "SURVEY": {
                "participation_threshold", "time_window_closed",
            },
            "SCRUTINY": {
                "claim_verdict", "time_window_closed",
            },
        }
        valid = expected_triggers.get(self.inquiry_class, set())
        if valid and self.resolution_trigger_reason not in valid:
            raise ValueError(
                f"Resolution trigger '{self.resolution_trigger_reason}' "
                f"not valid for inquiry class '{self.inquiry_class}'. "
                f"Expected one of: {sorted(valid)}"
            )
        return self
