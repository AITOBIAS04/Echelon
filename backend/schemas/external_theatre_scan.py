"""Scan result schemas for orchestrated scanner handoff.

Cycle 038c: Orchestrated Scanner Handoff.

Pydantic models representing scan request, per-candidate outcome,
individual paradox findings, and aggregate scan result. These schemas
bridge 038b orchestrator output into classification adapter results
using the same type/severity vocabulary as the real 038 scanner.
"""

from pydantic import BaseModel, Field, model_validator

from backend.schemas.theatre_comparison_bundle import (
    ComparisonCandidateSet,
    TheatreScopeKey,
)


class ParadoxFinding(BaseModel):
    """Single paradox finding from classification of a bundle pair."""

    paradox_type: str       # "SETTLEMENT_DIVERGENCE" | "ORACLE_INCONSISTENCY" |
                            # "TEMPORAL_DRIFT" | "SCOPE_OVERLAP_GAP"
    severity: str           # "INFO" | "WATCH" | "MATERIAL" | "CRITICAL"
    description: str
    evidence: dict
    construct_a_slug: str
    construct_b_slug: str


class CandidateScanOutcome(BaseModel):
    """Scan outcome for a single comparison candidate pair."""

    construct_a_slug: str
    construct_b_slug: str
    candidate_type: str             # "same_event" | "overlap_scope"
    match_strength: str             # "EXACT" | "PARTIAL" | "WEAK"
    matching_keys: list[str]
    findings: list[ParadoxFinding] = Field(default_factory=list)
    scanned: bool = True
    has_paradox: bool = False

    @model_validator(mode="after")
    def _set_has_paradox(self) -> "CandidateScanOutcome":
        self.has_paradox = len(self.findings) > 0
        return self


class ExternalTheatreScanRequest(BaseModel):
    """Input to the scan adapter — wraps orchestrator output."""

    candidates: list[ComparisonCandidateSet]
    event_keys: list[str] = Field(default_factory=list)
    scope_keys: list[TheatreScopeKey] = Field(default_factory=list)


class ExternalTheatreScanResult(BaseModel):
    """Complete scan adapter output."""

    outcomes: list[CandidateScanOutcome] = Field(default_factory=list)
    total_scanned: int = 0
    total_with_findings: int = 0
    total_clean: int = 0
