"""Theatre Calibration Certificate — unified certificate model.

Covers both Replay and Market Theatre outputs with full reproducibility
and trust metadata.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from theatre.engine.models import TheatreCriteria


class TheatreCalibrationCertificate(BaseModel):
    """Unified certificate covering both Replay and Market Theatre outputs."""

    # Identity
    certificate_id: str
    theatre_id: str
    template_id: str
    construct_id: str

    # Criteria
    criteria: TheatreCriteria
    scores: dict[str, float]  # criteria_id -> score (0.0-1.0)
    composite_score: float  # weighted aggregate

    # Calibration (optional per execution path)
    precision: float | None = None
    recall: float | None = None
    reply_accuracy: float | None = None
    brier_score: float | None = None
    ece: float | None = None

    # Evidence
    replay_count: int
    evidence_bundle_hash: str
    ground_truth_hash: str

    # Reproducibility
    construct_version: str
    construct_chain_versions: dict[str, str] | None = None
    scorer_version: str
    methodology_version: str
    dataset_hash: str

    # Trust
    verification_tier: Literal["UNVERIFIED", "BACKTESTED", "PROVEN"]
    commitment_hash: str

    # Timestamps
    issued_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime | None = None
    theatre_committed_at: datetime
    theatre_resolved_at: datetime

    # Integration
    ground_truth_source: str
    execution_path: Literal["replay", "market"]
