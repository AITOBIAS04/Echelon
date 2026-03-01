"""Oracle output models for the Echelon OSINT Pipeline.

These models represent the final output of the three-stage
Composed Oracle pipeline (Collection -> Corroboration -> Scoring).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field

from osint_pipeline.models.evidence import (
    EvidenceBundle,
    GapReport,
    OracleCollectionSummary,
)


class CorroborationResult(BaseModel):
    """Result of corroboration evaluation for a single claim.

    Implements the corroboration_minimum_met criterion from
    Composed Oracle Spec v2 section 2.1.
    """

    claim_id: str = Field(description="Identifier for the claim being corroborated")
    primary_source_id: str
    primary_source_group: str

    # Corroboration counts (after upstream dedup)
    distinct_corroborating_groups: int = 0
    corroboration_minimum: int = 2
    corroboration_window_seconds: int = 3600

    # Detail
    corroborating_sources: list[str] = Field(
        default_factory=list,
        description="source_ids that confirmed the primary claim (post-dedup)"
    )
    corroborating_groups: list[str] = Field(
        default_factory=list,
        description="Distinct source_groups that confirmed (post-dedup)"
    )
    excluded_by_dedup: list[str] = Field(
        default_factory=list,
        description="source_ids excluded due to shared upstream lineage"
    )
    outside_window: list[str] = Field(
        default_factory=list,
        description="source_ids that confirmed but outside time window"
    )

    @property
    def passed(self) -> bool:
        return self.distinct_corroborating_groups >= self.corroboration_minimum


class CounterSignalResult(BaseModel):
    """Result of counter-signal evaluation.

    Implements the counter_signal_checked criterion from
    Composed Oracle Spec v2 section 2.2.
    """

    counter_signal_class: str = Field(
        description="One of 11 counter-signal classes"
    )
    source_id: str
    checked: bool = True
    signal_found: bool = False
    signal_detail: str | None = None
    allow_gap: bool = False

    @property
    def passed(self) -> bool:
        """PASS when: checked=True AND (signal_found=False OR allow_gap=True).

        A found counter-signal is a FAIL unless the theatre config
        explicitly allows the gap.
        """
        if not self.checked:
            return False
        if self.signal_found and not self.allow_gap:
            return False
        return True


class CriterionScore(BaseModel):
    """Score for a single criterion in the oracle evaluation."""

    criterion_id: str
    score: float = Field(ge=0.0, le=1.0)
    passed: bool
    detail: str = ""
    evidence_bundle_ids: list[str] = Field(default_factory=list)


class OracleOutput(BaseModel):
    """Final output of the Composed Oracle pipeline.

    This is the artefact that feeds into calibration certificate generation.
    The bundle_hash is included in the certificate's evidence_bundle_hash.
    """

    oracle_id: str = Field(description="Unique identifier for this oracle run")
    theatre_id: str | None = None
    evaluated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    # Stage 1 summary
    collection: OracleCollectionSummary

    # Stage 2 results
    corroboration_results: list[CorroborationResult] = Field(default_factory=list)
    counter_signal_results: list[CounterSignalResult] = Field(default_factory=list)

    # Stage 3 scores
    criterion_scores: list[CriterionScore] = Field(default_factory=list)
    composite_score: float = Field(
        ge=0.0, le=1.0,
        description="Weighted composite across all criteria"
    )

    # Integrity
    bundle_hash: str = Field(
        default="",
        description="SHA-256 of canonical JSON of all evidence bundles"
    )

    # Gaps (credibility signal)
    gap_report: list[GapReport] = Field(default_factory=list)

    # Coverage metrics (for results surface)
    coverage_percentage: float = Field(
        ge=0.0, le=100.0,
        default=0.0,
        description="(sources queried with receipts / required sources) * 100"
    )
    counter_signals_checked: int = 0
    counter_signals_found: int = 0

    # Settlement guard: requires at least one primary_evidence bundle
    settlement_safe: bool = False

    @property
    def all_criteria_passed(self) -> bool:
        return all(cs.passed for cs in self.criterion_scores)

    @property
    def sources_with_gaps(self) -> int:
        return len(self.gap_report)
