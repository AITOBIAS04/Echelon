"""Comparison bundle schemas for cross-theatre paradox fixture layer.

Cycle 038a: Theatre Execution Fixtures For Cross-Theatre Paradox.

Normalized shapes that bridge 037e local theatre execution results
into 038 cross-theatre paradox scanner inputs.
"""

from typing import Optional

from pydantic import BaseModel, Field


class TheatreCheckSummary(BaseModel):
    """Normalized summary of a single executed theatre check."""
    check_type: str
    status: str       # PASSED | FAILED | SKIPPED
    is_critical: bool
    evidence: dict = Field(default_factory=dict)


class TheatreExecutionSummary(BaseModel):
    """Aggregate execution summary across all checks for one construct."""
    checks: list[TheatreCheckSummary] = Field(default_factory=list)
    executed_count: int = 0
    passed_count: int = 0
    failed_count: int = 0
    skipped_count: int = 0
    has_critical_failures: bool = False


class TheatreScopeKey(BaseModel):
    """Normalized scope identifier for overlap matching."""
    scope_type: str    # "region" | "entity" | "time_window" | "event"
    scope_value: str   # e.g. "us-equities", "btc-usd", "2026-q1"

    def normalized(self) -> "TheatreScopeKey":
        """Return copy with lowercase-hyphenated scope_value."""
        return TheatreScopeKey(
            scope_type=self.scope_type.lower().strip(),
            scope_value=self.scope_value.lower().strip().replace("_", "-"),
        )

    def key(self) -> str:
        """Serialized form for set operations."""
        n = self.normalized()
        return f"{n.scope_type}:{n.scope_value}"


class ExecutedTheatreComparisonBundle(BaseModel):
    """Normalized bundle representing one theatre's executed verification state.

    Bridges 037e TheatreExecutionResult into a shape the 038 paradox
    scanner can consume for cross-theatre comparison.
    """
    construct_slug: str
    construct_version: str
    certificate_id: Optional[str] = None

    template_ids: list[str] = Field(default_factory=list)
    oracle_source_ids: list[str] = Field(default_factory=list)
    event_keys: list[str] = Field(default_factory=list)
    scope_keys: list[TheatreScopeKey] = Field(default_factory=list)

    settlement_state: Optional[str] = None
    settlement_outcomes: dict = Field(default_factory=dict)
    oracle_values: dict = Field(default_factory=dict)

    execution_summary: TheatreExecutionSummary = Field(
        default_factory=TheatreExecutionSummary,
    )
    provenance_refs: list[str] = Field(default_factory=list)

    confidence_signals: dict = Field(default_factory=dict)


class ComparisonCandidateSet(BaseModel):
    """A pair of bundles identified as comparison candidates."""
    candidate_type: str   # "same_event" | "overlap_scope"
    bundle_a: ExecutedTheatreComparisonBundle
    bundle_b: ExecutedTheatreComparisonBundle
    matching_keys: list[str] = Field(default_factory=list)
    match_strength: str = "EXACT"  # "EXACT" | "PARTIAL" | "WEAK"
