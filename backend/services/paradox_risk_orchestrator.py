"""
Paradox Risk Orchestrator — Centralized recompute + persistence + event gating.

Promotes paradox risk from read-time calculation to live backend orchestration.
Recalculates from mutation paths and emits PARADOX_RISK_CHANGED only on material delta.

Evidence freshness is computed from persisted InvestigationEvidenceItem timestamps
for theatres that have linked investigations. This is the single source of truth
for the evidence_freshness_hours factor.

Trigger wiring status (Cycle 020):
- WIRED: evidence submission, counter-signal ingestion, theatre read (stale fallback)
- NOT WIRED: paradox lifecycle mutations (paradox engine is still mock-based)
- NOT WIRED: timeline stability changes (no persisted stability source yet)
"""

import logging
from datetime import datetime, timezone
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


async def compute_evidence_freshness_hours(db, theatre_id: str) -> float:
    """Compute hours since the most recent evidence submission for a theatre.

    Queries InvestigationEvidenceItem.submitted_at across all investigations
    linked to this theatre_id. Returns 0.0 if no evidence exists (no staleness).

    This is the single source of truth for evidence_freshness_hours.
    """
    from sqlalchemy import func, select
    from backend.database.models import Investigation, InvestigationEvidenceItem

    result = await db.execute(
        select(func.max(InvestigationEvidenceItem.submitted_at))
        .join(Investigation, InvestigationEvidenceItem.investigation_id == Investigation.id)
        .where(Investigation.theatre_id == theatre_id)
    )
    latest_submitted = result.scalar()

    if latest_submitted is None:
        return 0.0

    # Handle naive datetimes from DB
    if latest_submitted.tzinfo is None:
        latest_submitted = latest_submitted.replace(tzinfo=timezone.utc)

    elapsed = datetime.now(timezone.utc) - latest_submitted
    return max(0.0, elapsed.total_seconds() / 3600.0)


def _resolve_factor(
    old_factors: Optional[dict],
    key: str,
    fallback,
    override,
):
    if override is not None:
        return override
    if old_factors is None:
        return fallback
    return old_factors.get(key, fallback)


async def trigger_recompute(
    db,
    theatre_id: str,
    trigger_reason: str,
    *,
    logic_gap: Optional[float] = None,
    stability: Optional[float] = None,
    has_active_paradox: Optional[bool] = None,
    material_counter_signals: Optional[int] = None,
    evidence_freshness_hours: Optional[float] = None,
    inquiry_class: str = "COUNTERFACTUAL",
    emit_ws: bool = False,
) -> Optional[ParadoxRiskAssessment]:
    """Recompute paradox risk for a theatre.

    1. Evaluate via ParadoxRiskEvaluator
    2. Compare with persisted level
    3. Persist new assessment
    4. Emit websocket update on material change when requested
    5. Return assessment metadata for callers that need it
    """
    from backend.database.models import Theatre

    theatre = await db.get(Theatre, theatre_id)
    if theatre is None:
        logger.warning("Theatre %s not found for paradox risk recompute", theatre_id)
        return None

    old_level = theatre.paradox_risk_level
    old_factors = theatre.paradox_risk_factors_json
    resolved_logic_gap = _resolve_factor(old_factors, "logic_gap", 0.0, logic_gap)
    resolved_stability = _resolve_factor(old_factors, "stability", 1.0, stability)
    resolved_active_paradox = _resolve_factor(
        old_factors, "active_paradox", False, has_active_paradox
    )
    resolved_material_counter_signals = _resolve_factor(
        old_factors, "material_counter_signals", 0, material_counter_signals
    )
    # Evidence freshness: use caller override if provided, otherwise compute
    # from real persisted evidence timestamps (single source of truth).
    if evidence_freshness_hours is not None:
        resolved_evidence_freshness_hours = evidence_freshness_hours
    else:
        resolved_evidence_freshness_hours = await compute_evidence_freshness_hours(
            db, theatre_id
        )

    assessment = evaluate(
        logic_gap=resolved_logic_gap,
        stability=resolved_stability,
        has_active_paradox=resolved_active_paradox,
        material_counter_signals=resolved_material_counter_signals,
        evidence_freshness_hours=resolved_evidence_freshness_hours,
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

    if emit_ws and material:
        try:
            from backend.websockets.realtime_manager import manager as ws_manager

            await ws_manager.broadcast_paradox_risk_changed(
                theatre_id=theatre_id,
                old_level=old_level or "UNKNOWN",
                new_level=assessment.level,
                factors=assessment.factors,
                reason=trigger_reason,
            )
        except Exception:
            logger.exception(
                "Failed to broadcast paradox risk change for theatre %s", theatre_id
            )

    return assessment
