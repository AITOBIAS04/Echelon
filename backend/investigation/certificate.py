"""Investigation Certificate — frozen model + builder for investigation-class inquiries.

The certificate is the terminal artefact of an investigation. It records every hash,
every counter-signal summary, drift events, provenance breakdown, and a routing hint
that determines whether the result flows to ALLOWED or REVIEW_REQUIRED.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from backend.utils.canonical_json import canonical_json

from backend.investigation.claim_graph import ClaimGraph
from backend.investigation.commitment_monitor import CommitmentMonitor, DriftImpact
from backend.investigation.counter_signals import InvestigationCounterSignalFeed
from backend.investigation.evidence_envelope import EvidenceEnvelope


class StopCondition(str, Enum):
    """Stop condition types for investigation-class inquiries."""

    OUTCOME_RESOLUTION = "OUTCOME_RESOLUTION"
    EVIDENCE_THRESHOLD = "EVIDENCE_THRESHOLD"
    SPONSOR_DEFINED = "SPONSOR_DEFINED"
    CONSTRUCT_EVALUATION = "CONSTRUCT_EVALUATION"


class RoutingDecision(str, Enum):
    """Routing hint for the investigation certificate."""

    ALLOWED = "ALLOWED"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"


class InvestigationCertificate(BaseModel):
    """Immutable investigation certificate — terminal artefact of an investigation.

    30+ fields capturing the complete investigation state at resolution time.
    """

    model_config = {"frozen": True}

    # Identity
    certificate_id: str
    theatre_id: str
    construct_id: str
    inquiry_class: str

    # Stop condition
    stop_condition: str
    stop_config: dict = Field(default_factory=dict)

    # Timestamps
    investigation_started_at: datetime
    investigation_completed_at: datetime

    # Evidence envelope summary
    evidence_item_count: int
    evidence_redaction_count: int
    evidence_envelope_hash: str
    provenance_summary: dict

    # Claim graph summary
    claim_count: int
    claim_status_summary: dict
    claim_graph_root_hash: str

    # Counter-signal summary
    counter_signals_checked: int
    counter_signals_gaps: int
    counter_signals_material: int
    counter_signal_detail: list[dict] = Field(default_factory=list)

    # Drift summary
    drift_event_count: int
    has_material_drift: bool
    drift_events: list[dict] = Field(default_factory=list)

    # Routing
    routing_decision: str  # ALLOWED or REVIEW_REQUIRED
    routing_reason: str

    # Certificate hash (SHA-256 of canonical JSON of certificate payload)
    certificate_hash: str

    # Anchoring
    anchoring_status: str = "pending"  # pending | anchored
    anchoring_tx_hash: Optional[str] = None

    # Metadata
    issued_at: datetime
    methodology_version: str = "1.0.0"
    toolset_version: str = "0.1.0"


class InvestigationCertificateBuilder:
    """Assembles an InvestigationCertificate from all toolset artefacts.

    Routing logic (priority order):
    1. Material drift         -> REVIEW_REQUIRED ("drift_event_material")
    2. Material counter-signal -> REVIEW_REQUIRED ("counter_signal_material")
    3. Single provenance class -> REVIEW_REQUIRED ("single_provenance_class")
    4. Otherwise              -> ALLOWED ("all_checks_passed")

    Note: Anchoring status is set post-build and is not part of the routing cascade.
    """

    def build(
        self,
        theatre_id: str,
        construct_id: str,
        inquiry_class: str,
        stop_condition: str,
        stop_config: dict,
        evidence_envelope: EvidenceEnvelope,
        claim_graph: ClaimGraph,
        counter_signal_feed: InvestigationCounterSignalFeed,
        commitment_monitor: CommitmentMonitor,
        investigation_started_at: datetime | None = None,
        template_id: str | None = None,
        template_name: str | None = None,
        committed_sources: list | None = None,
    ) -> InvestigationCertificate:
        """Build a frozen InvestigationCertificate from all toolset state."""
        now = datetime.utcnow()
        started = investigation_started_at or now
        certificate_id = f"INV-{theatre_id[:8]}"

        # Evidence envelope summary
        envelope_hash = evidence_envelope.compute_envelope_hash()
        provenance_summary = evidence_envelope.provenance_summary

        # Claim graph summary
        root_hash = claim_graph.compute_root_hash()
        status_summary = claim_graph.get_status_summary()

        # Counter-signal summary
        cs_summary = counter_signal_feed.get_summary()
        cs_detail = counter_signal_feed.get_detail()

        # Drift summary
        drift_events_list = [
            {
                "drift_id": e.drift_id,
                "drift_type": e.drift_type.value,
                "detected_at": e.detected_at.isoformat(),
                "original_value": e.original_value,
                "new_value": e.new_value,
                "evidence_ref": e.evidence_ref,
                "impact_assessment": e.impact_assessment.value,
            }
            for e in commitment_monitor.events
        ]

        # Routing decision
        routing_decision, routing_reason = self._compute_routing(
            commitment_monitor=commitment_monitor,
            cs_summary=cs_summary,
            provenance_summary=provenance_summary,
        )

        # Build hash payload (excludes certificate_hash itself and anchoring fields)
        hash_payload = {
            "certificate_id": certificate_id,
            "theatre_id": theatre_id,
            "construct_id": construct_id,
            "inquiry_class": inquiry_class,
            "stop_condition": stop_condition,
            "stop_config": stop_config,
            "evidence_envelope_hash": envelope_hash,
            "provenance_summary": provenance_summary,
            "claim_graph_root_hash": root_hash,
            "claim_status_summary": status_summary,
            "counter_signals_checked": cs_summary["checked"],
            "counter_signals_gaps": cs_summary["gaps"],
            "counter_signals_material": cs_summary["material_contradictions"],
            "drift_event_count": len(drift_events_list),
            "has_material_drift": commitment_monitor.has_material_drift(),
            "routing_decision": routing_decision,
            "routing_reason": routing_reason,
        }

        # Template and source provenance (cycle-022)
        if template_id is not None:
            hash_payload["template_id"] = template_id
            hash_payload["template_name"] = template_name
        if committed_sources is not None:
            hash_payload["committed_sources"] = committed_sources

        certificate_hash = hashlib.sha256(
            canonical_json(hash_payload).encode()
        ).hexdigest()

        return InvestigationCertificate(
            certificate_id=certificate_id,
            theatre_id=theatre_id,
            construct_id=construct_id,
            inquiry_class=inquiry_class,
            stop_condition=stop_condition,
            stop_config=stop_config,
            investigation_started_at=started,
            investigation_completed_at=now,
            issued_at=now,
            evidence_item_count=len(evidence_envelope.items),
            evidence_redaction_count=len(evidence_envelope.redactions),
            evidence_envelope_hash=envelope_hash,
            provenance_summary=provenance_summary,
            claim_count=len(claim_graph.claims),
            claim_status_summary=status_summary,
            claim_graph_root_hash=root_hash,
            counter_signals_checked=cs_summary["checked"],
            counter_signals_gaps=cs_summary["gaps"],
            counter_signals_material=cs_summary["material_contradictions"],
            counter_signal_detail=cs_detail,
            drift_event_count=len(drift_events_list),
            has_material_drift=commitment_monitor.has_material_drift(),
            drift_events=drift_events_list,
            routing_decision=routing_decision,
            routing_reason=routing_reason,
            certificate_hash=certificate_hash,
        )

    def _compute_routing(
        self,
        commitment_monitor: CommitmentMonitor,
        cs_summary: dict,
        provenance_summary: dict,
    ) -> tuple[str, str]:
        """Compute routing decision with priority cascade.

        Returns (decision, reason) tuple.
        """
        # Priority 1: Material drift
        if commitment_monitor.has_material_drift():
            return RoutingDecision.REVIEW_REQUIRED.value, "drift_event_material"

        # Priority 2: Material counter-signal
        if cs_summary.get("material_contradictions", 0) > 0:
            return RoutingDecision.REVIEW_REQUIRED.value, "counter_signal_material"

        # Priority 3: Single provenance class
        if len(provenance_summary) == 1 and sum(provenance_summary.values()) > 0:
            return RoutingDecision.REVIEW_REQUIRED.value, "single_provenance_class"

        # Anchoring is applied post-build by the persistence layer, so it is
        # never evaluated as a routing criterion here.

        # Default: ALLOWED
        return RoutingDecision.ALLOWED.value, "all_checks_passed"
