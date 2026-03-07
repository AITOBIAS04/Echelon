"""
Paradox Risk Orchestrator — Centralized recompute + persistence + event gating.

Promotes paradox risk from read-time calculation to live backend orchestration.
Recalculates from mutation paths and emits PARADOX_RISK_CHANGED only on material delta.
"""

import logging
from typing import Optional

from backend.services.paradox_risk_evaluator import (
    ParadoxRiskAssessment,
    evaluate,
    persist_risk_to_theatre,
)

logger = logging.getLogger(__name__)


def is_material_delta(
    old_level: Optional[str],
    new_level: str,
    old_factors: Optional[dict],
    new_factors: dict,
) -> bool:
    """Determine if risk change is material enough for WS emission.

    Material = level changed OR active_paradox flipped OR
    material_counter_signals crossed 0->positive (or positive->0).
    """
    # Level change is always material
    if old_level is None or old_level != new_level:
        return True

    if old_factors is None:
        return True

    # active_paradox flip
    old_paradox = old_factors.get("active_paradox", False)
    new_paradox = new_factors.get("active_paradox", False)
    if old_paradox != new_paradox:
        return True

    # material_counter_signals crossing 0 boundary
    old_cs = old_factors.get("material_counter_signals", 0)
    new_cs = new_factors.get("material_counter_signals", 0)
    if (old_cs == 0 and new_cs > 0) or (old_cs > 0 and new_cs == 0):
        return True

    return False


async def trigger_recompute(
    db,
    theatre_id: str,
    trigger_reason: str,
    *,
    logic_gap: float = 0.0,
    stability: float = 1.0,
    has_active_paradox: bool = False,
    material_counter_signals: int = 0,
    evidence_freshness_hours: float = 0.0,
    inquiry_class: str = "COUNTERFACTUAL",
) -> Optional[ParadoxRiskAssessment]:
    """Recompute paradox risk for a theatre.

    1. Evaluate via ParadoxRiskEvaluator
    2. Compare with persisted level
    3. Persist new assessment
    4. Return (assessment, material) tuple info via the assessment

    Note: WS emission is handled by the caller to avoid circular imports
    with the realtime_manager. The caller checks is_material_delta().
    """
    from backend.database.models import Theatre

    theatre = await db.get(Theatre, theatre_id)
    if theatre is None:
        logger.warning("Theatre %s not found for paradox risk recompute", theatre_id)
        return None

    old_level = theatre.paradox_risk_level
    old_factors = theatre.paradox_risk_factors_json

    assessment = evaluate(
        logic_gap=logic_gap,
        stability=stability,
        has_active_paradox=has_active_paradox,
        material_counter_signals=material_counter_signals,
        evidence_freshness_hours=evidence_freshness_hours,
        inquiry_class=inquiry_class,
    )

    persist_risk_to_theatre(theatre, assessment)

    material = is_material_delta(old_level, assessment.level, old_factors, assessment.factors)

    logger.info(
        "Paradox risk recomputed for theatre %s: %s -> %s (material=%s, trigger=%s)",
        theatre_id, old_level, assessment.level, material, trigger_reason,
    )

    # Attach metadata for caller to use
    assessment._material = material  # type: ignore[attr-defined]
    assessment._old_level = old_level  # type: ignore[attr-defined]
    assessment._trigger_reason = trigger_reason  # type: ignore[attr-defined]

    return assessment
