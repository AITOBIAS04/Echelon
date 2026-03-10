"""
Paradox Risk Evaluator (Cycle 019).

Computes paradox risk surface for theatres based on inquiry-class-specific
thresholds. Risk is a COMPUTED SURFACE with cached persistence,
NOT operator-authored.

Risk levels: LOW | WATCH | HIGH
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class ParadoxRiskAssessment:
    """Result of paradox risk evaluation."""
    level: str  # LOW | WATCH | HIGH
    factors: dict
    explanation: str


# Inquiry-class-specific thresholds
# Each class weights different factors
THRESHOLDS = {
    "COUNTERFACTUAL": {
        "logic_gap_watch": 0.4,
        "logic_gap_high": 0.7,
        "stability_watch": 0.5,
        "stability_high": 0.3,
        "evidence_freshness_weight": 0.3,
        "counter_signal_weight": 0.5,
    },
    "INVESTIGATIVE": {
        "logic_gap_watch": 0.35,
        "logic_gap_high": 0.65,
        "stability_watch": 0.5,
        "stability_high": 0.3,
        "evidence_freshness_weight": 0.7,  # Weighs evidence freshness more
        "counter_signal_weight": 0.5,
    },
    "INSPECTION": {
        "logic_gap_watch": 0.45,
        "logic_gap_high": 0.75,
        "stability_watch": 0.45,
        "stability_high": 0.25,
        "evidence_freshness_weight": 0.4,
        "counter_signal_weight": 0.5,
    },
    "SURVEY": {
        "logic_gap_watch": 0.5,
        "logic_gap_high": 0.8,
        "stability_watch": 0.4,
        "stability_high": 0.2,
        "evidence_freshness_weight": 0.3,
        "counter_signal_weight": 0.4,
    },
    "SCRUTINY": {
        "logic_gap_watch": 0.3,
        "logic_gap_high": 0.6,
        "stability_watch": 0.55,
        "stability_high": 0.35,
        "evidence_freshness_weight": 0.4,
        "counter_signal_weight": 0.8,  # Weighs counter-signals more
    },
}

DEFAULT_THRESHOLDS = THRESHOLDS["COUNTERFACTUAL"]


def evaluate(
    logic_gap: float = 0.0,
    stability: float = 1.0,
    has_active_paradox: bool = False,
    material_counter_signals: int = 0,
    evidence_freshness_hours: float = 0.0,
    inquiry_class: str = "COUNTERFACTUAL",
) -> ParadoxRiskAssessment:
    """
    Evaluate paradox risk for a theatre.

    Args:
        logic_gap: 0-1, higher = more risk
        stability: 0-1, lower = more risk
        has_active_paradox: whether timeline has active paradox
        material_counter_signals: count of material counter-signals
        evidence_freshness_hours: hours since last evidence submission
        inquiry_class: one of 5 inquiry classes

    Returns:
        ParadoxRiskAssessment with level, factors, explanation
    """
    thresholds = THRESHOLDS.get(inquiry_class, DEFAULT_THRESHOLDS)

    factors = {
        "logic_gap": round(logic_gap, 3),
        "stability": round(stability, 3),
        "active_paradox": has_active_paradox,
        "material_counter_signals": material_counter_signals,
        "evidence_freshness_hours": round(evidence_freshness_hours, 1),
    }

    explanations = []

    # HIGH conditions
    if has_active_paradox:
        explanations.append("Paradox active")
        return ParadoxRiskAssessment(
            level="HIGH",
            factors=factors,
            explanation="; ".join(explanations),
        )

    if logic_gap > thresholds["logic_gap_high"]:
        explanations.append("Logic gap widening")

    if stability < thresholds["stability_high"]:
        explanations.append("Evidence weak")

    if explanations:
        return ParadoxRiskAssessment(
            level="HIGH",
            factors=factors,
            explanation="; ".join(explanations),
        )

    # WATCH conditions
    if logic_gap > thresholds["logic_gap_watch"]:
        explanations.append("Logic gap widening")

    if stability < thresholds["stability_watch"]:
        explanations.append("Evidence weak")

    if material_counter_signals > 0:
        weight = thresholds["counter_signal_weight"]
        if weight >= 0.7:
            explanations.append("Counter-signals rising")
        else:
            explanations.append("Counter-signals detected")

    freshness_weight = thresholds["evidence_freshness_weight"]
    freshness_threshold = 72.0 / freshness_weight  # More weight = lower threshold
    if evidence_freshness_hours > freshness_threshold:
        explanations.append("Stale investigation")

    if explanations:
        return ParadoxRiskAssessment(
            level="WATCH",
            factors=factors,
            explanation="; ".join(explanations),
        )

    # LOW
    return ParadoxRiskAssessment(
        level="LOW",
        factors=factors,
        explanation="Risk within acceptable bounds",
    )


def persist_risk_to_theatre(theatre, assessment: ParadoxRiskAssessment):
    """Update theatre model with computed risk (for ORM flush)."""
    theatre.paradox_risk_level = assessment.level
    theatre.paradox_risk_factors_json = assessment.factors
    theatre.paradox_risk_updated_at = datetime.utcnow()
