"""Stop Condition Orchestrator — automatic evaluation after material mutations.

Wraps InvestigationStopConditionEvaluator with drift awareness, persistence,
and WebSocket event emission. Async service function pattern.
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import Investigation
from backend.investigation.models import ProvenanceClass
from backend.investigation.stop_conditions import InvestigationStopConditionEvaluator
from backend.investigation.claim_graph import ClaimType
from backend.investigation.commitment_monitor import DriftType
from backend.investigation.counter_signals import InvestigationCounterSignalClass
from backend.investigation.toolset import InvestigationConfig, InvestigationToolset
from backend.websockets.realtime_manager import manager as ws_manager


class StopConditionResult:
    """Immutable result of stop condition evaluation."""
    __slots__ = ("ready", "reason", "drift_material", "trigger")

    def __init__(self, ready: bool, reason: str, drift_material: bool, trigger: str):
        self.ready = ready
        self.reason = reason
        self.drift_material = drift_material
        self.trigger = trigger


def _rebuild_toolset_from_investigation(inv: Investigation) -> InvestigationToolset:
    """Rebuild an InvestigationToolset from persisted DB records.

    Same logic as _rebuild_toolset in investigation_routes.py.
    """
    config = InvestigationConfig(
        domain_filters=inv.domain_filters_json or [],
        stop_condition=inv.stop_condition or "OUTCOME_RESOLUTION",
        stop_config=inv.stop_config_json or {},
    )
    toolset = InvestigationToolset(
        config=config,
        theatre_id=inv.theatre_id,
        construct_id=inv.construct_id,
        inquiry_class=inv.inquiry_class,
    )

    for item in (inv.evidence_items or []):
        toolset.evidence_envelope.add_item_from_persisted(
            evidence_id=item.id,
            content_hash=item.content_hash,
            provenance_class=ProvenanceClass(item.provenance_class),
            submitted_at=item.submitted_at,
            content_type=item.content_type,
            source_description=item.source_description,
            references=item.references_json or [],
            source_id=item.source_id or "",
            query_determinism=item.query_determinism or "",
        )

    for node in (inv.claim_nodes or []):
        toolset.claim_graph.add_claim_from_persisted(
            claim_id=node.id,
            claim_text=node.claim_text,
            claim_type=ClaimType(node.claim_type),
            evidence_refs=node.evidence_refs_json or [],
            counter_signals=node.counter_signals_json or [],
            status=node.status,
            confidence=node.confidence,
            independence_groups=node.independence_groups_json or [],
        )

    for sig in (inv.counter_signals or []):
        toolset.counter_signal_feed.add_signal_from_persisted(
            counter_signal_id=sig.id,
            signal_class=InvestigationCounterSignalClass(sig.signal_class),
            detected_at=sig.detected_at,
            evidence_ref=sig.evidence_ref,
            material=sig.material,
            resolution_impact=sig.resolution_impact or "",
            detection_method=sig.detection_method or "human_submitted",
        )

    for evt in (inv.drift_events or []):
        toolset.commitment_monitor.add_event_from_persisted(
            drift_id=evt.id,
            drift_type=DriftType(evt.drift_type),
            detected_at=evt.detected_at,
            original_value=evt.original_value or "",
            new_value=evt.new_value or "",
            evidence_ref=evt.evidence_ref,
            impact_assessment=evt.impact_assessment or "non_material",
        )

    return toolset


async def evaluate_after_mutation(
    session: AsyncSession,
    investigation: Investigation,
    trigger: str,
    time_remaining: float | None = None,
) -> StopConditionResult:
    """Evaluate stop conditions after a material mutation.

    Args:
        session: Active async session (caller manages transaction).
        investigation: Eagerly-loaded Investigation with relationships.
        trigger: What caused this evaluation ("drift" | "evidence" | "counter_signal").
        time_remaining: Override for time-based stop conditions.

    Returns:
        StopConditionResult with ready/not-ready + reason.
    """
    if investigation.status == "COMPLETED":
        return StopConditionResult(
            ready=True,
            reason="already_ready_or_completed",
            drift_material=False,
            trigger=trigger,
        )

    toolset = _rebuild_toolset_from_investigation(investigation)

    has_drift = toolset.commitment_monitor.has_material_drift()

    if time_remaining is None:
        time_remaining = _compute_time_remaining(investigation.stop_config_json or {})

    evaluator = InvestigationStopConditionEvaluator()
    ready, reason = evaluator.evaluate(
        stop_condition=investigation.stop_condition,
        stop_config=investigation.stop_config_json or {},
        claim_graph=toolset.claim_graph,
        evidence_envelope=toolset.evidence_envelope,
        time_remaining=time_remaining,
    )

    if has_drift and trigger == "drift":
        reason = f"drift_material;{reason}"

    old_status = investigation.stop_condition_status
    investigation.stop_condition_status = "READY" if ready else "NOT_READY"
    investigation.stop_condition_reason = reason
    investigation.stop_condition_evaluated_at = datetime.utcnow()

    # READY certificates remain mutable until batch issuance: refresh the
    # pre-issued artifact so new drift/counter-signals can force review.
    certificate = investigation.certificate
    if (
        certificate is not None
        and investigation.status == "CERTIFICATE_READY"
        and certificate.certificate_status == "READY"
    ):
        rebuilt_certificate = toolset.build_certificate()
        certificate.certificate_hash = rebuilt_certificate.certificate_hash
        certificate.routing_decision = rebuilt_certificate.routing_decision
        certificate.routing_reason = rebuilt_certificate.routing_reason
        certificate.certificate_json = {
            "certificate_id": rebuilt_certificate.certificate_id,
            "theatre_id": rebuilt_certificate.theatre_id,
            "construct_id": rebuilt_certificate.construct_id,
        }

    await session.flush()

    if ready and old_status != "READY":
        await ws_manager.broadcast_global(
            "INVESTIGATION_STOP_CONDITION_MET",
            {
                "investigation_id": investigation.id,
                "reason": reason,
                "trigger": trigger,
                "drift_material": has_drift,
            },
        )

    return StopConditionResult(
        ready=ready,
        reason=reason,
        drift_material=has_drift,
        trigger=trigger,
    )


def _compute_time_remaining(stop_config: dict) -> float:
    """Compute seconds remaining from stop_config milestone or deadline."""
    milestone_str = stop_config.get("milestone_timestamp")
    if milestone_str:
        try:
            milestone = datetime.fromisoformat(milestone_str)
            if milestone.tzinfo is not None:
                milestone = milestone.replace(tzinfo=None)
            return (milestone - datetime.utcnow()).total_seconds()
        except (ValueError, TypeError):
            pass
    return 999_999.0
