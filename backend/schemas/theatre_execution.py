"""Theatre execution models — deterministic check execution for theatre constructs.

Cycle 037e: Theatre Check Execution.
"""

from dataclasses import dataclass, field
from typing import Optional


# Execution status values (deterministic, not soft-scored)
EXECUTION_STATUSES = {"PLANNED", "SUPPORTED", "EXECUTED", "PASSED", "FAILED", "SKIPPED"}


@dataclass(frozen=True)
class TheatreCheckResult:
    """Result of executing a single theatre check."""
    check_id: str
    check_type: str           # SETTLEMENT_ACCURACY | ORACLE_CONSISTENCY | etc.
    status: str               # PASSED | FAILED | SKIPPED
    template_id: Optional[str] = None
    source_id: Optional[str] = None
    evidence: Optional[dict] = None   # execution-specific provenance
    reason: Optional[str] = None      # human-readable explanation


@dataclass
class TheatreFixtureInput:
    """Normalized fixture input for theatre check execution.

    Adapts repo-specific fixture shapes into a generic input
    that the runner consumes without repo-specific branching.
    """
    construct_slug: str
    construct_version: str
    construct_class: str       # always "theatre" for theatre constructs

    # Per-template settlement fixtures: template_id → {outcome, oracle_value, ...}
    settlement_fixtures: dict = field(default_factory=dict)

    # Cross-validation oracle fixtures: source_id → {primary_value, cross_value, ...}
    oracle_fixtures: dict = field(default_factory=dict)

    # Calibration fixtures: {predictions: [...], outcomes: [...], brier_type: ...}
    calibration_fixture: Optional[dict] = None

    # Functional correctness fixtures: template_id → {input, expected_output, ...}
    functional_fixtures: dict = field(default_factory=dict)


@dataclass
class TheatreExecutionResult:
    """Aggregate result of executing all theatre checks for a construct."""
    construct_slug: str
    check_results: list[TheatreCheckResult] = field(default_factory=list)

    @property
    def total_executed(self) -> int:
        return sum(1 for r in self.check_results if r.status in ("PASSED", "FAILED"))

    @property
    def total_passed(self) -> int:
        return sum(1 for r in self.check_results if r.status == "PASSED")

    @property
    def total_failed(self) -> int:
        return sum(1 for r in self.check_results if r.status == "FAILED")

    @property
    def total_skipped(self) -> int:
        return sum(1 for r in self.check_results if r.status == "SKIPPED")

    @property
    def has_critical_failures(self) -> bool:
        """True if any critical check type failed or was skipped."""
        critical_types = {"SETTLEMENT_ACCURACY", "ORACLE_CONSISTENCY"}
        return any(
            r.status in ("FAILED", "SKIPPED") and r.check_type in critical_types
            for r in self.check_results
        )

    def to_dict(self) -> dict:
        """Serialize for persistence in certificate JSON."""
        return {
            "construct_slug": self.construct_slug,
            "total_executed": self.total_executed,
            "total_passed": self.total_passed,
            "total_failed": self.total_failed,
            "total_skipped": self.total_skipped,
            "has_critical_failures": self.has_critical_failures,
            "checks": [
                {
                    "check_id": r.check_id,
                    "check_type": r.check_type,
                    "status": r.status,
                    "template_id": r.template_id,
                    "source_id": r.source_id,
                    "evidence": r.evidence,
                    "reason": r.reason,
                }
                for r in self.check_results
            ],
        }
