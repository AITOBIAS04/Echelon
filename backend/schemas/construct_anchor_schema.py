"""Pydantic schemas for Construct Anchor Mapping.

Maps evaluation dimensions to external evidence anchors.
A dimension with no recognized anchor is flagged as weakly anchored.
Used by the construct evidence anchoring pipeline (Cycle-026a).
"""

from enum import Enum

from pydantic import BaseModel, Field


class AnchorClass(str, Enum):
    """Classification of external evidence anchors."""

    DETERMINISTIC_CHECK = "deterministic_check"
    BENCHMARK_DATASET = "benchmark_dataset"
    PUBLIC_STANDARD = "public_standard"
    LIVE_EXTERNAL_EVIDENCE = "live_external_evidence"


class AnchorReference(BaseModel):
    """A reference to a specific anchor for an evaluation dimension."""

    anchor_class: AnchorClass
    anchor_id: str = Field(..., min_length=1, description="Identifier of the anchor asset or check")
    rationale: str = Field(..., min_length=1, description="Why this anchor applies")


class EvaluationDimensionAnchor(BaseModel):
    """Anchor mapping for a single evaluation dimension.

    If anchors is empty the dimension is weakly anchored and
    weakly_anchored must be True.
    """

    dimension: str = Field(..., min_length=1, description="Evaluation dimension name")
    anchors: list[AnchorReference] = Field(default_factory=list)
    weakly_anchored: bool = False
