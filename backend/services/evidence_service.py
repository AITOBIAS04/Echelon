"""Evidence accumulation rules per inquiry class.

Adds an inquiry-class-aware validation layer on top of TheatreEvidenceCollector.
Each inquiry class has distinct rules for what evidence is sufficient.

Cycle-014, Sprint 2 — Task 2.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass(frozen=True)
class EvidenceValidation:
    """Result of evidence validation against inquiry-class-specific rules."""

    valid: bool
    inquiry_class: str
    reason: str
    coverage_pct: float = 0.0
    distinct_source_count: int = 0
    criteria_evaluated: int = 0
    criteria_total: int = 0
    participation_count: int = 0


class InquiryEvidenceRules:
    """Evidence accumulation rules per inquiry class.

    Validates evidence snapshots against inquiry-class-specific rules.
    Does NOT replace TheatreEvidenceCollector -- adds a validation layer on top.
    """

    @staticmethod
    def validate_evidence(
        inquiry_class: str,
        evidence_snapshot: Any,
        theatre_config: dict,
    ) -> EvidenceValidation:
        """Validate evidence against inquiry-class-specific rules.

        Args:
            inquiry_class: One of the 5 canonical inquiry classes.
            evidence_snapshot: EvidenceSnapshot from TheatreEvidenceCollector
                (or a dict with source_coverage_pct, evidence_bundles, etc.).
            theatre_config: Theatre configuration dict with thresholds.

        Returns:
            EvidenceValidation with validation result and metrics.
        """
        ic = inquiry_class.upper().strip()

        # Extract evidence metrics from snapshot
        coverage_pct = _get_coverage(evidence_snapshot)
        distinct_sources = _get_distinct_sources(evidence_snapshot)
        bundles = _get_bundles(evidence_snapshot)

        if ic == "COUNTERFACTUAL":
            return _validate_counterfactual(
                coverage_pct, distinct_sources, theatre_config
            )

        elif ic == "INVESTIGATIVE":
            return _validate_investigative(
                coverage_pct, distinct_sources, bundles, theatre_config
            )

        elif ic == "INSPECTION":
            return _validate_inspection(
                coverage_pct, bundles, theatre_config
            )

        elif ic == "SURVEY":
            return _validate_survey(
                coverage_pct, theatre_config
            )

        elif ic == "SCRUTINY":
            return _validate_scrutiny(
                coverage_pct, distinct_sources, bundles, theatre_config
            )

        else:
            # Unknown inquiry class -- treat as counterfactual
            return _validate_counterfactual(
                coverage_pct, distinct_sources, theatre_config
            )


def _get_coverage(snapshot: Any) -> float:
    """Extract coverage percentage from snapshot."""
    if isinstance(snapshot, dict):
        return snapshot.get("source_coverage_pct", 0.0)
    return getattr(snapshot, "source_coverage_pct", 0.0)


def _get_distinct_sources(snapshot: Any) -> int:
    """Count distinct source IDs in evidence bundles."""
    bundles = _get_bundles(snapshot)
    source_ids = set()
    for b in bundles:
        if isinstance(b, dict):
            sid = b.get("source_id", "")
        else:
            sid = getattr(b, "source_id", "")
        if sid:
            source_ids.add(sid)
    return len(source_ids)


def _get_bundles(snapshot: Any) -> list:
    """Extract evidence bundles from snapshot."""
    if isinstance(snapshot, dict):
        return snapshot.get("evidence_bundles", [])
    return getattr(snapshot, "evidence_bundles", [])


def _validate_counterfactual(
    coverage_pct: float,
    distinct_sources: int,
    theatre_config: dict,
) -> EvidenceValidation:
    """COUNTERFACTUAL: Accept simulation divergence or OSINT bundles."""
    # Any evidence present is valid for counterfactual
    valid = coverage_pct > 0
    reason = (
        "Evidence present"
        if valid
        else "No evidence collected yet"
    )
    return EvidenceValidation(
        valid=valid,
        inquiry_class="COUNTERFACTUAL",
        reason=reason,
        coverage_pct=coverage_pct,
        distinct_source_count=distinct_sources,
    )


def _validate_investigative(
    coverage_pct: float,
    distinct_sources: int,
    bundles: list,
    theatre_config: dict,
) -> EvidenceValidation:
    """INVESTIGATIVE: Require corroboration_minimum distinct upstreams."""
    corroboration_min = theatre_config.get("corroboration_minimum", 2)
    valid = distinct_sources >= corroboration_min
    reason = (
        f"Corroboration met: {distinct_sources} sources >= {corroboration_min} minimum"
        if valid
        else f"Corroboration insufficient: {distinct_sources} sources < {corroboration_min} minimum"
    )
    return EvidenceValidation(
        valid=valid,
        inquiry_class="INVESTIGATIVE",
        reason=reason,
        coverage_pct=coverage_pct,
        distinct_source_count=distinct_sources,
    )


def _validate_inspection(
    coverage_pct: float,
    bundles: list,
    theatre_config: dict,
) -> EvidenceValidation:
    """INSPECTION: Single-source acceptable. Binary pass/fail per criterion."""
    criteria = theatre_config.get("criteria", [])
    criteria_total = len(criteria) if criteria else theatre_config.get("criteria_total", 0)

    # Count evaluated criteria from bundles (each bundle evaluates criteria)
    criteria_evaluated = 0
    for b in bundles:
        if isinstance(b, dict):
            evaluated = b.get("criteria_evaluated", 0)
            criteria_evaluated += evaluated if evaluated else (1 if b else 0)
        else:
            criteria_evaluated += 1

    # For inspection, any evidence from even a single source is acceptable
    valid = len(bundles) > 0
    reason = (
        f"Inspection evidence present: {len(bundles)} bundle(s), "
        f"{criteria_evaluated}/{criteria_total} criteria evaluated"
        if valid
        else "No inspection evidence collected"
    )
    return EvidenceValidation(
        valid=valid,
        inquiry_class="INSPECTION",
        reason=reason,
        coverage_pct=coverage_pct,
        distinct_source_count=1 if bundles else 0,
        criteria_evaluated=criteria_evaluated,
        criteria_total=criteria_total,
    )


def _validate_survey(
    coverage_pct: float,
    theatre_config: dict,
) -> EvidenceValidation:
    """SURVEY: No OSINT pipeline -- market position distribution is evidence."""
    participation_count = theatre_config.get("participation_count", 0)
    participation_threshold = theatre_config.get("participation_threshold", 10)
    valid = participation_count >= participation_threshold
    reason = (
        f"Participation sufficient: {participation_count} >= {participation_threshold}"
        if valid
        else f"Participation insufficient: {participation_count} < {participation_threshold}"
    )
    return EvidenceValidation(
        valid=valid,
        inquiry_class="SURVEY",
        reason=reason,
        coverage_pct=coverage_pct,
        participation_count=participation_count,
    )


def _validate_scrutiny(
    coverage_pct: float,
    distinct_sources: int,
    bundles: list,
    theatre_config: dict,
) -> EvidenceValidation:
    """SCRUTINY: Validate claim + counter-evidence. Require adversarial confirmation."""
    corroboration_min = theatre_config.get("corroboration_minimum", 2)
    # For scrutiny, we need at least one claim bundle and one verification bundle
    has_claim = len(bundles) >= 1
    has_adversarial = distinct_sources >= corroboration_min
    valid = has_claim and has_adversarial
    reason = (
        f"Scrutiny evidence valid: {distinct_sources} sources, adversarial confirmation met"
        if valid
        else f"Scrutiny evidence insufficient: claim={'present' if has_claim else 'missing'}, "
        f"adversarial={'met' if has_adversarial else 'unmet'} "
        f"({distinct_sources}/{corroboration_min} sources)"
    )
    return EvidenceValidation(
        valid=valid,
        inquiry_class="SCRUTINY",
        reason=reason,
        coverage_pct=coverage_pct,
        distinct_source_count=distinct_sources,
    )
