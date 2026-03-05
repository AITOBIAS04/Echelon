"""Investigation API routes — REST endpoints for investigation lifecycle.

Manages investigations via in-memory InvestigationToolset instances.

PERSISTENCE: DEFERRED (014c scope)
    Investigations are stored in a process-local dict. State is lost on
    restart. This is an explicit design choice matching ConvergenceDetector's
    011-scope pattern — the investigation toolset (claim graph, evidence
    envelope, counter-signal feed, commitment monitor) is a runtime object
    graph not yet backed by a database model.

    Full persistence requires:
    - Database model (Investigation table)
    - Serialisation of InvestigationToolset sub-objects
    - Alembic migration
    - Service-layer refactor of _investigations dict → repository

    The REST API contract (request/response schemas) is stable and will
    not change when persistence is added.
"""

from __future__ import annotations

import base64
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from backend.investigation.claim_graph import ClaimType
from backend.investigation.commitment_monitor import DriftImpact, DriftType
from backend.investigation.counter_signals import InvestigationCounterSignalClass
from backend.investigation.models import ProvenanceClass
from backend.investigation.toolset import InvestigationConfig, InvestigationToolset
from backend.schemas.investigation_schemas import (
    CertificateResponse,
    ClaimCreateRequest,
    ClaimGraphResponse,
    ClaimNodeResponse,
    CounterSignalCreateRequest,
    CounterSignalFeedResponse,
    CounterSignalResponse,
    DriftEventResponse,
    DriftFeedResponse,
    EvidenceEnvelopeResponse,
    EvidenceItemResponse,
    EvidenceSubmitRequest,
    InvestigationCreateRequest,
    InvestigationDetailResponse,
    InvestigationListResponse,
    InvestigationSummaryResponse,
    RedactionEventResponse,
)

router = APIRouter(prefix="/api/v1/investigations", tags=["Investigations"])

# In-memory investigation store (toolset instances keyed by investigation ID).
# DEFERRED: Replace with database-backed repository when persistence is prioritised.
# API contract (schemas) is stable and decoupled from storage mechanism.
_investigations: dict[str, dict] = {}


def _get_investigation(investigation_id: str) -> dict:
    """Get investigation entry or raise 404."""
    entry = _investigations.get(investigation_id)
    if not entry:
        raise HTTPException(status_code=404, detail=f"Investigation {investigation_id} not found")
    return entry


def _build_evidence_response(toolset: InvestigationToolset) -> EvidenceEnvelopeResponse:
    """Build evidence envelope response from toolset."""
    envelope = toolset.evidence_envelope
    return EvidenceEnvelopeResponse(
        items=[
            EvidenceItemResponse(
                evidence_id=item.evidence_id,
                content_hash=item.content_hash,
                provenance_class=item.provenance_class.value,
                submitted_at=item.submitted_at,
                content_type=item.content_type,
                source_description=item.source_description,
                references=list(item.references),
            )
            for item in envelope.items
        ],
        redactions=[
            RedactionEventResponse(
                redaction_id=r.redaction_id,
                evidence_id=r.evidence_id,
                reason_class=r.reason_class,
                redacted_at=r.redacted_at,
            )
            for r in envelope.redactions
        ],
        provenance_summary=envelope.provenance_summary,
        envelope_hash=envelope.compute_envelope_hash(),
    )


def _build_claims_response(toolset: InvestigationToolset) -> ClaimGraphResponse:
    """Build claim graph response from toolset."""
    cg = toolset.claim_graph
    return ClaimGraphResponse(
        claims=[
            ClaimNodeResponse(
                claim_id=c.claim_id,
                claim_text=c.claim_text,
                claim_type=c.claim_type.value,
                evidence_refs=list(c.evidence_refs),
                counter_signals=list(c.counter_signals),
                status=c.status.value,
                confidence=c.confidence,
                independence_groups=list(c.independence_groups),
            )
            for c in cg.claims
        ],
        root_hash=cg.compute_root_hash(),
        status_summary=cg.get_status_summary(),
    )


def _build_counter_signals_response(toolset: InvestigationToolset) -> CounterSignalFeedResponse:
    """Build counter-signal feed response from toolset."""
    feed = toolset.counter_signal_feed
    return CounterSignalFeedResponse(
        signals=[
            CounterSignalResponse(
                counter_signal_id=s.counter_signal_id,
                signal_class=s.signal_class.value,
                detected_at=s.detected_at,
                evidence_ref=s.evidence_ref,
                material=s.material,
                resolution_impact=s.resolution_impact,
                detection_method=s.detection_method,
            )
            for s in feed.signals
        ],
        summary=feed.get_summary(),
    )


def _build_drift_response(toolset: InvestigationToolset) -> DriftFeedResponse:
    """Build drift events response from toolset."""
    monitor = toolset.commitment_monitor
    return DriftFeedResponse(
        events=[
            DriftEventResponse(
                drift_id=e.drift_id,
                drift_type=e.drift_type.value,
                detected_at=e.detected_at,
                original_value=e.original_value,
                new_value=e.new_value,
                evidence_ref=e.evidence_ref,
                impact_assessment=e.impact_assessment.value,
            )
            for e in monitor.events
        ],
        has_material_drift=monitor.has_material_drift(),
    )


def _build_summary(investigation_id: str, entry: dict) -> InvestigationSummaryResponse:
    """Build investigation summary from entry."""
    toolset: InvestigationToolset = entry["toolset"]
    return InvestigationSummaryResponse(
        id=investigation_id,
        theatre_id=entry["theatre_id"],
        construct_id=entry["construct_id"],
        inquiry_class=entry["inquiry_class"],
        status=entry["status"],
        evidence_count=len(toolset.evidence_envelope.items),
        claim_count=len(toolset.claim_graph.claims),
        counter_signal_count=len(toolset.counter_signal_feed.signals),
        drift_event_count=len(toolset.commitment_monitor.events),
        created_at=entry["created_at"],
        updated_at=entry.get("updated_at", entry["created_at"]),
    )


# ============================================
# ENDPOINTS
# ============================================


@router.get("/", response_model=InvestigationListResponse)
async def list_investigations():
    """List all active investigations."""
    summaries = [
        _build_summary(inv_id, entry)
        for inv_id, entry in _investigations.items()
    ]
    return InvestigationListResponse(investigations=summaries, total=len(summaries))


@router.post("/", response_model=InvestigationSummaryResponse, status_code=201)
async def create_investigation(request: InvestigationCreateRequest):
    """Create a new investigation."""
    investigation_id = f"INV-{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc)

    config = InvestigationConfig(
        domain_filters=request.domain_filters,
        stop_condition=request.stop_condition,
        stop_config=request.stop_config,
    )

    toolset = InvestigationToolset(
        config=config,
        theatre_id=request.theatre_id,
        construct_id=request.construct_id,
        inquiry_class=request.inquiry_class,
    )

    entry = {
        "toolset": toolset,
        "theatre_id": request.theatre_id,
        "construct_id": request.construct_id,
        "inquiry_class": request.inquiry_class,
        "status": "active",
        "created_at": now,
        "updated_at": now,
    }
    _investigations[investigation_id] = entry

    return _build_summary(investigation_id, entry)


@router.get("/{investigation_id}", response_model=InvestigationDetailResponse)
async def get_investigation(investigation_id: str):
    """Get full investigation detail."""
    entry = _get_investigation(investigation_id)
    toolset: InvestigationToolset = entry["toolset"]

    return InvestigationDetailResponse(
        id=investigation_id,
        theatre_id=entry["theatre_id"],
        construct_id=entry["construct_id"],
        inquiry_class=entry["inquiry_class"],
        status=entry["status"],
        stop_condition=toolset._config.stop_condition,
        stop_config=toolset._config.stop_config,
        created_at=entry["created_at"],
        updated_at=entry.get("updated_at", entry["created_at"]),
        evidence=_build_evidence_response(toolset),
        claims=_build_claims_response(toolset),
        counter_signals=_build_counter_signals_response(toolset),
        drift=_build_drift_response(toolset),
    )


@router.get("/{investigation_id}/evidence", response_model=EvidenceEnvelopeResponse)
async def get_evidence(investigation_id: str):
    """Get evidence envelope for an investigation."""
    entry = _get_investigation(investigation_id)
    return _build_evidence_response(entry["toolset"])


@router.post("/{investigation_id}/evidence", response_model=EvidenceItemResponse, status_code=201)
async def submit_evidence(investigation_id: str, request: EvidenceSubmitRequest):
    """Submit evidence to an investigation."""
    entry = _get_investigation(investigation_id)
    toolset: InvestigationToolset = entry["toolset"]

    content = base64.b64decode(request.content_base64)
    provenance = ProvenanceClass(request.provenance_class)

    item = toolset.submit_evidence(
        content=content,
        provenance_class=provenance,
        content_type=request.content_type,
        source_description=request.source_description,
        references=request.references,
    )
    entry["updated_at"] = datetime.now(timezone.utc)

    return EvidenceItemResponse(
        evidence_id=item.evidence_id,
        content_hash=item.content_hash,
        provenance_class=item.provenance_class.value,
        submitted_at=item.submitted_at,
        content_type=item.content_type,
        source_description=item.source_description,
        references=list(item.references),
    )


@router.get("/{investigation_id}/claims", response_model=ClaimGraphResponse)
async def get_claims(investigation_id: str):
    """Get claim graph for an investigation."""
    entry = _get_investigation(investigation_id)
    return _build_claims_response(entry["toolset"])


@router.post("/{investigation_id}/claims", response_model=ClaimNodeResponse, status_code=201)
async def register_claim(investigation_id: str, request: ClaimCreateRequest):
    """Register a claim in the investigation's claim graph."""
    entry = _get_investigation(investigation_id)
    toolset: InvestigationToolset = entry["toolset"]

    claim_type = ClaimType(request.claim_type)
    node = toolset.register_claim(
        claim_text=request.claim_text,
        claim_type=claim_type,
        evidence_refs=request.evidence_refs,
    )
    entry["updated_at"] = datetime.now(timezone.utc)

    return ClaimNodeResponse(
        claim_id=node.claim_id,
        claim_text=node.claim_text,
        claim_type=node.claim_type.value,
        evidence_refs=list(node.evidence_refs),
        counter_signals=list(node.counter_signals),
        status=node.status.value,
        confidence=node.confidence,
        independence_groups=list(node.independence_groups),
    )


@router.get("/{investigation_id}/counter-signals", response_model=CounterSignalFeedResponse)
async def get_counter_signals(investigation_id: str):
    """Get counter-signals for an investigation."""
    entry = _get_investigation(investigation_id)
    return _build_counter_signals_response(entry["toolset"])


@router.post("/{investigation_id}/counter-signals", response_model=CounterSignalResponse, status_code=201)
async def log_counter_signal(investigation_id: str, request: CounterSignalCreateRequest):
    """Log a counter-signal for an investigation."""
    entry = _get_investigation(investigation_id)
    toolset: InvestigationToolset = entry["toolset"]

    signal_class = InvestigationCounterSignalClass(request.signal_class)
    signal = toolset.log_counter_signal(
        signal_class=signal_class,
        material=request.material,
        resolution_impact=request.resolution_impact,
        detection_method=request.detection_method,
        evidence_ref=request.evidence_ref,
    )
    entry["updated_at"] = datetime.now(timezone.utc)

    return CounterSignalResponse(
        counter_signal_id=signal.counter_signal_id,
        signal_class=signal.signal_class.value,
        detected_at=signal.detected_at,
        evidence_ref=signal.evidence_ref,
        material=signal.material,
        resolution_impact=signal.resolution_impact,
        detection_method=signal.detection_method,
    )


@router.get("/{investigation_id}/drift", response_model=DriftFeedResponse)
async def get_drift(investigation_id: str):
    """Get drift events for an investigation."""
    entry = _get_investigation(investigation_id)
    return _build_drift_response(entry["toolset"])


@router.get("/{investigation_id}/certificate", response_model=CertificateResponse)
async def get_certificate(investigation_id: str):
    """Build and return the investigation certificate."""
    entry = _get_investigation(investigation_id)
    toolset: InvestigationToolset = entry["toolset"]

    cert = toolset.build_certificate()
    entry["status"] = "completed"
    entry["updated_at"] = datetime.now(timezone.utc)

    return CertificateResponse(
        certificate_id=cert.certificate_id,
        theatre_id=cert.theatre_id,
        construct_id=cert.construct_id,
        inquiry_class=cert.inquiry_class,
        stop_condition=cert.stop_condition,
        stop_config=cert.stop_config,
        investigation_started_at=cert.investigation_started_at,
        investigation_completed_at=cert.investigation_completed_at,
        evidence_item_count=cert.evidence_item_count,
        evidence_redaction_count=cert.evidence_redaction_count,
        evidence_envelope_hash=cert.evidence_envelope_hash,
        provenance_summary=cert.provenance_summary,
        claim_count=cert.claim_count,
        claim_status_summary=cert.claim_status_summary,
        claim_graph_root_hash=cert.claim_graph_root_hash,
        counter_signals_checked=cert.counter_signals_checked,
        counter_signals_gaps=cert.counter_signals_gaps,
        counter_signals_material=cert.counter_signals_material,
        counter_signal_detail=cert.counter_signal_detail,
        drift_event_count=cert.drift_event_count,
        has_material_drift=cert.has_material_drift,
        drift_events=cert.drift_events,
        routing_decision=cert.routing_decision,
        routing_reason=cert.routing_reason,
        certificate_hash=cert.certificate_hash,
        anchoring_status=cert.anchoring_status,
        anchoring_tx_hash=cert.anchoring_tx_hash,
        issued_at=cert.issued_at,
        methodology_version=cert.methodology_version,
        toolset_version=cert.toolset_version,
    )
