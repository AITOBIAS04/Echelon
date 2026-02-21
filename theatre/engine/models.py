"""Theatre engine domain models — Pydantic v2."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


class TheatreCriteria(BaseModel):
    """Structured, hash-stable evaluation criteria.

    criteria_ids are domain-specific keys (e.g. source_fidelity, hex_grid_accuracy).
    weights keys must be a subset of criteria_ids and values must sum to 1.0.
    """

    criteria_ids: list[str] = Field(..., min_length=1)
    criteria_human: str
    weights: dict[str, float] = {}

    @model_validator(mode="after")
    def validate_weights(self) -> "TheatreCriteria":
        if self.weights:
            extra = set(self.weights.keys()) - set(self.criteria_ids)
            if extra:
                raise ValueError(f"Weight keys not in criteria_ids: {extra}")
            total = sum(self.weights.values())
            if abs(total - 1.0) > 1e-6:
                raise ValueError(f"Weights must sum to 1.0, got {total}")
        return self


class GroundTruthEpisode(BaseModel):
    """A single ground truth record for replay scoring."""

    episode_id: str
    input_data: dict[str, Any]
    expected_output: dict[str, Any] | None = None
    labels: dict[str, Any] | None = None
    metadata: dict[str, Any] = {}


class AuditEvent(BaseModel):
    """Timestamped event in the Theatre audit trail."""

    event_type: str
    from_state: str | None = None
    to_state: str | None = None
    detail: dict[str, Any] | None = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class BundleManifest(BaseModel):
    """Evidence bundle manifest metadata."""

    theatre_id: str
    template_id: str
    construct_id: str
    execution_path: Literal["replay", "market"]
    commitment_hash: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    file_inventory: dict[str, str] = {}  # filename → SHA-256 hash
