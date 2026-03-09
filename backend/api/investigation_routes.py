"""Investigation API routes — REST endpoints for investigation lifecycle.

Manages investigations via DB-backed InvestigationRepository with in-memory
InvestigationToolset for runtime operations (hashing, certificate building).

Persistence: LIVE (Cycle 019)
    Investigations are persisted to the database via InvestigationRepository.
    The in-memory InvestigationToolset is rebuilt from DB records on access
    for operations that need it (certificate building, hash computation).
    Data survives server restart.

    The REST API contract (request/response schemas) is stable and unchanged
    from the original in-memory implementation.
"""

from __future__ import annotations

import base64
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select as sa_select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import (
    Investigation,
    InvestigationEvidenceItem,
    InvestigationClaimNode,
    InvestigationCounterSignal,
    InvestigationDriftEvent,
    InvestigationCertificateRecord,
    InvestigationTemplate,
)
from backend.database.repositories.investigation_repository import InvestigationRepository
from backend.dependencies import get_db
from backend.investigation.claim_graph import ClaimType
from backend.investigation.commitment_monitor import DriftType
from backend.investigation.counter_signals import InvestigationCounterSignalClass
from backend.investigation.models import ProvenanceClass
from backend.investigation.toolset import InvestigationConfig, InvestigationToolset
from backend.osint.models.registry import RegistryLoader
from backend.investigation.signal_scanner import (
    DomainFilter,
    DOMAIN_FILTER_SOURCE_GROUPS,
)
from backend.services.domain_filter_validator import (
    DomainFilterViolation,
    validate_evidence_source,
    validate_signal_source,
)
from backend.services.stop_condition_orchestrator import evaluate_after_mutation
from backend.services.certificate_lifecycle_service import transition_to_ready, run_batch_anchor
from backend.websockets.realtime_manager import manager as ws_manager
from backend.schemas.investigation_schemas import (
    CertificateResponse,
    ClaimCreateRequest,
    ClaimGraphResponse,
    ClaimNodeResponse,
    CounterSignalCreateRequest,
    CounterSignalFeedResponse,
    CounterSignalResponse,
    DriftCreateRequest,
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

# Registry loader for policy enforcement (receipt_body_required, requires_legal_review).
# Loaded lazily on first use to avoid import-time file I/O.
_registry_loader: RegistryLoader | None = None


def _get_registry() -> RegistryLoader:
    """Get or create the singleton RegistryLoader."""
    global _registry_loader
    if _registry_loader is None:
        import os
        registry_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "osint", "sources.json",
        )
        _registry_loader = RegistryLoader(registry_path)
    return _registry_loader


def _rebuild_toolset(inv: Investigation) -> InvestigationToolset:
    """Rebuild an InvestigationToolset from persisted DB records.

    Replays evidence submissions, claim registrations, counter-signals,
    and drift events into a fresh toolset instance so that certificate
    building and hash computation work correctly.
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

    # Replay evidence items
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

    # Replay claims
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

    # Replay counter-signals
    for sig in (inv.counter_signals or []):
        signal_class = InvestigationCounterSignalClass(sig.signal_class)
        toolset.counter_signal_feed.add_signal_from_persisted(
            counter_signal_id=sig.id,
            signal_class=signal_class,
            detected_at=sig.detected_at,
            evidence_ref=sig.evidence_ref,
            material=sig.material,
            resolution_impact=sig.resolution_impact or "",
            detection_method=sig.detection_method or "human_submitted",
        )

    # Replay drift events
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
                source_id=item.source_id,
                query_determinism=item.query_determinism,
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


def _build_summary_from_db(inv: Investigation) -> InvestigationSummaryResponse:
    """Build investigation summary from DB model."""
    return InvestigationSummaryResponse(
        id=inv.id,
        theatre_id=inv.theatre_id,
        construct_id=inv.construct_id,
        inquiry_class=inv.inquiry_class,
        status=inv.status.lower(),
        evidence_count=len(inv.evidence_items) if inv.evidence_items else 0,
        claim_count=len(inv.claim_nodes) if inv.claim_nodes else 0,
        counter_signal_count=len(inv.counter_signals) if inv.counter_signals else 0,
        drift_event_count=len(inv.drift_events) if inv.drift_events else 0,
        created_at=inv.created_at,
        updated_at=inv.updated_at,
    )


async def _recompute_theatre_paradox_risk(
    db: AsyncSession,
    theatre_id: str | None,
    inquiry_class: str | None,
    trigger_reason: str,
    **overrides,
) -> None:
    """Best-effort paradox-risk recompute for live investigation mutations."""
    if not theatre_id:
        return

    from backend.services.paradox_risk_orchestrator import trigger_recompute

    assessment = await trigger_recompute(
        db,
        theatre_id,
        trigger_reason,
        inquiry_class=inquiry_class or "COUNTERFACTUAL",
        emit_ws=True,
        **overrides,
    )
    if assessment is not None:
        await db.commit()


# ============================================
# ENDPOINTS
# ============================================


@router.get("/", response_model=InvestigationListResponse)
async def list_investigations(db: AsyncSession = Depends(get_db)):
    """List all active investigations."""
    repo = InvestigationRepository(db)
    investigations = await repo.list_all()
    summaries = [_build_summary_from_db(inv) for inv in investigations]
    return InvestigationListResponse(investigations=summaries, total=len(summaries))


def _resolve_committed_sources(domain_filters: list[str]) -> list[str]:
    """Resolve actual source_ids from domain filters via the live OSINT registry.

    Chain: domain_filter → source_groups (DOMAIN_FILTER_SOURCE_GROUPS) → source_ids (RegistryLoader).
    Returns sorted, deduplicated source_id values from sources.json.
    """
    # Step 1: domain filters → source group names
    source_groups: set[str] = set()
    for df_str in domain_filters:
        try:
            df = DomainFilter(df_str)
        except ValueError:
            continue
        groups = DOMAIN_FILTER_SOURCE_GROUPS.get(df, [])
        source_groups.update(groups)

    if not source_groups:
        return []

    # Step 2: source groups → actual source_ids from registry
    registry = _get_registry()
    source_ids: set[str] = set()
    for group in source_groups:
        for source in registry.get_sources_by_group(group):
            source_ids.add(source.source_id)

    return sorted(source_ids)


def _validate_domain_filters(domain_filters: list[str]) -> None:
    """Validate all domain filter values against the backend DomainFilter enum.

    Raises HTTPException(400) if any value is invalid.
    """
    valid_values = {df.value for df in DomainFilter}
    for df in domain_filters:
        if df not in valid_values:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid domain filter: '{df}'. Valid values: {sorted(valid_values)}",
            )


@router.post("/", response_model=InvestigationSummaryResponse, status_code=201)
async def create_investigation(
    request: InvestigationCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Create a new investigation."""
    # Resolve template defaults if template_id provided
    template = None
    template_id = request.template_id

    inquiry_class = request.inquiry_class
    domain_filters = request.domain_filters
    stop_condition = request.stop_condition
    stop_config = request.stop_config

    if template_id is not None:
        # Validate template exists and is ACTIVE
        result = await db.execute(
            sa_select(InvestigationTemplate)
            .where(InvestigationTemplate.id == template_id)
        )
        template = result.scalar_one_or_none()
        if template is None:
            raise HTTPException(
                status_code=400,
                detail=f"Investigation template '{template_id}' not found",
            )
        if template.template_status != "ACTIVE":
            raise HTTPException(
                status_code=400,
                detail=f"Investigation template '{template_id}' is not ACTIVE (status={template.template_status})",
            )

        # Apply template defaults for fields the user did NOT explicitly provide.
        # Use model_fields_set to distinguish "user sent INVESTIGATIVE" from "Pydantic default."
        explicitly_set = request.model_fields_set
        if "inquiry_class" not in explicitly_set:
            inquiry_class = template.inquiry_class
        if "domain_filters" not in explicitly_set:
            domain_filters = template.domain_filters_json or []
        if "stop_condition" not in explicitly_set:
            stop_condition = template.default_stop_condition
        if "stop_config" not in explicitly_set:
            if template.default_time_window_days is not None:
                stop_config = {"time_window_days": template.default_time_window_days}

    # Validate domain filters against backend enum
    if domain_filters:
        _validate_domain_filters(domain_filters)

    # Resolve committed sources from live registry for the final domain_filters
    committed_sources = None
    if domain_filters:
        committed_sources = _resolve_committed_sources(domain_filters)

    repo = InvestigationRepository(db)
    inv = await repo.create(
        theatre_id=request.theatre_id,
        construct_id=request.construct_id,
        inquiry_class=inquiry_class,
        domain_filters=domain_filters,
        stop_condition=stop_condition,
        stop_config=stop_config,
        template_id=template_id,
        committed_sources=committed_sources,
    )
    await db.commit()
    await db.refresh(inv, attribute_names=[
        "evidence_items", "claim_nodes", "counter_signals", "drift_events",
    ])
    return _build_summary_from_db(inv)


@router.get("/{investigation_id}", response_model=InvestigationDetailResponse)
async def get_investigation(
    investigation_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get full investigation detail."""
    repo = InvestigationRepository(db)
    inv = await repo.get(investigation_id)
    if not inv:
        raise HTTPException(status_code=404, detail=f"Investigation {investigation_id} not found")

    toolset = _rebuild_toolset(inv)

    # Compute has_legal_review_requirement from source registry
    has_legal_review = False
    source_ids = {item.source_id for item in (inv.evidence_items or []) if item.source_id}
    if source_ids:
        registry = _get_registry()
        for sid in source_ids:
            source = registry.get_source(sid)
            if source and source.requires_legal_review:
                has_legal_review = True
                break

    return InvestigationDetailResponse(
        id=inv.id,
        theatre_id=inv.theatre_id,
        construct_id=inv.construct_id,
        inquiry_class=inv.inquiry_class,
        status=inv.status.lower(),
        stop_condition=inv.stop_condition,
        stop_config=inv.stop_config_json,
        created_at=inv.created_at,
        updated_at=inv.updated_at,
        evidence=_build_evidence_response(toolset),
        claims=_build_claims_response(toolset),
        counter_signals=_build_counter_signals_response(toolset),
        drift=_build_drift_response(toolset),
        has_legal_review_requirement=has_legal_review,
    )


@router.get("/{investigation_id}/evidence", response_model=EvidenceEnvelopeResponse)
async def get_evidence(
    investigation_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get evidence envelope for an investigation."""
    repo = InvestigationRepository(db)
    inv = await repo.get(investigation_id)
    if not inv:
        raise HTTPException(status_code=404, detail=f"Investigation {investigation_id} not found")
    toolset = _rebuild_toolset(inv)
    return _build_evidence_response(toolset)


@router.post("/{investigation_id}/evidence", response_model=EvidenceItemResponse, status_code=201)
async def submit_evidence(
    investigation_id: str,
    request: EvidenceSubmitRequest,
    db: AsyncSession = Depends(get_db),
):
    """Submit evidence to an investigation."""
    repo = InvestigationRepository(db)
    inv = await repo.get(investigation_id)
    if not inv:
        raise HTTPException(status_code=404, detail=f"Investigation {investigation_id} not found")

    # Receipt enforcement: if source requires receipt_body, reject without it
    if request.source_id:
        registry = _get_registry()
        source = registry.get_source(request.source_id)
        if source and source.receipt_body_required and not request.receipt_body:
            raise HTTPException(
                status_code=422,
                detail=f"Source '{request.source_id}' requires receipt_body but none was provided",
            )

    # Domain filter enforcement (cycle-021)
    try:
        validate_evidence_source(
            domain_filters_json=inv.domain_filters_json or [],
            source_id=request.source_id or "",
        )
    except DomainFilterViolation as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    content = base64.b64decode(request.content_base64)
    provenance = ProvenanceClass(request.provenance_class)

    # Look up query_determinism from registry if source_id provided
    query_determinism = ""
    if request.source_id:
        registry = _get_registry()
        source = registry.get_source(request.source_id)
        if source and source.query_determinism:
            query_determinism = source.query_determinism

    # Persist to DB AND feed to toolset for hash computation
    toolset = _rebuild_toolset(inv)
    item = toolset.submit_evidence(
        content=content,
        provenance_class=provenance,
        content_type=request.content_type,
        source_description=request.source_description,
        references=request.references,
        source_id=request.source_id,
        query_determinism=query_determinism,
    )

    # Persist DB record
    theatre_id = inv.theatre_id
    inquiry_class = inv.inquiry_class
    await repo.submit_evidence(
        investigation_id=investigation_id,
        content=content,
        provenance_class=request.provenance_class,
        content_type=request.content_type,
        source_description=request.source_description,
        source_id=request.source_id or "",
        query_determinism=query_determinism,
        references=request.references,
    )
    await db.commit()

    # Stop condition evaluation after evidence mutation (cycle-021)
    inv = await repo.get(investigation_id)
    if inv:
        await evaluate_after_mutation(db, inv, trigger="evidence")
        await db.commit()

    await _recompute_theatre_paradox_risk(
        db,
        theatre_id,
        inquiry_class,
        "evidence_submitted",
        evidence_freshness_hours=0.0,
    )

    return EvidenceItemResponse(
        evidence_id=item.evidence_id,
        content_hash=item.content_hash,
        provenance_class=item.provenance_class.value,
        submitted_at=item.submitted_at,
        content_type=item.content_type,
        source_description=item.source_description,
        references=list(item.references),
        source_id=item.source_id,
        query_determinism=item.query_determinism,
    )


@router.get("/{investigation_id}/claims", response_model=ClaimGraphResponse)
async def get_claims(
    investigation_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get claim graph for an investigation."""
    repo = InvestigationRepository(db)
    inv = await repo.get(investigation_id)
    if not inv:
        raise HTTPException(status_code=404, detail=f"Investigation {investigation_id} not found")
    toolset = _rebuild_toolset(inv)
    return _build_claims_response(toolset)


@router.post("/{investigation_id}/claims", response_model=ClaimNodeResponse, status_code=201)
async def register_claim(
    investigation_id: str,
    request: ClaimCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Register a claim in the investigation's claim graph."""
    repo = InvestigationRepository(db)
    inv = await repo.get(investigation_id)
    if not inv:
        raise HTTPException(status_code=404, detail=f"Investigation {investigation_id} not found")

    toolset = _rebuild_toolset(inv)
    claim_type = ClaimType(request.claim_type)
    node = toolset.register_claim(
        claim_text=request.claim_text,
        claim_type=claim_type,
        evidence_refs=request.evidence_refs,
    )

    await repo.register_claim(
        investigation_id=investigation_id,
        claim_text=request.claim_text,
        claim_type=request.claim_type,
        evidence_refs=request.evidence_refs,
        confidence=node.confidence,
    )
    await db.commit()

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
async def get_counter_signals(
    investigation_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get counter-signals for an investigation."""
    repo = InvestigationRepository(db)
    inv = await repo.get(investigation_id)
    if not inv:
        raise HTTPException(status_code=404, detail=f"Investigation {investigation_id} not found")
    toolset = _rebuild_toolset(inv)
    return _build_counter_signals_response(toolset)


@router.post("/{investigation_id}/counter-signals", response_model=CounterSignalResponse, status_code=201)
async def log_counter_signal(
    investigation_id: str,
    request: CounterSignalCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Log a counter-signal for an investigation."""
    repo = InvestigationRepository(db)
    inv = await repo.get(investigation_id)
    if not inv:
        raise HTTPException(status_code=404, detail=f"Investigation {investigation_id} not found")

    # Domain filter enforcement (cycle-021)
    # Resolve evidence item's source_id — evidence_ref is an internal record ID,
    # not a source group identifier.
    resolved_source = ""
    if request.evidence_ref and inv.evidence_items:
        for item in inv.evidence_items:
            if item.id == request.evidence_ref:
                resolved_source = item.source_id or ""
                break
    try:
        validate_signal_source(
            domain_filters_json=inv.domain_filters_json or [],
            detection_method=request.detection_method or "human_submitted",
            source_ref=resolved_source,
        )
    except DomainFilterViolation as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    toolset = _rebuild_toolset(inv)
    signal_class = InvestigationCounterSignalClass(request.signal_class)
    signal = toolset.log_counter_signal(
        signal_class=signal_class,
        material=request.material,
        resolution_impact=request.resolution_impact,
        detection_method=request.detection_method,
        evidence_ref=request.evidence_ref,
    )

    theatre_id = inv.theatre_id
    inquiry_class = inv.inquiry_class
    await repo.log_counter_signal(
        investigation_id=investigation_id,
        signal_class=request.signal_class,
        material=request.material,
        resolution_impact=request.resolution_impact,
        detection_method=request.detection_method,
        evidence_ref=request.evidence_ref,
    )
    await db.commit()

    # Stop condition evaluation after counter-signal mutation (cycle-021)
    inv = await repo.get(investigation_id)
    if inv:
        await evaluate_after_mutation(db, inv, trigger="counter_signal")
        await db.commit()

    if request.material:
        summary = toolset.counter_signal_feed.get_summary()
        await _recompute_theatre_paradox_risk(
            db,
            theatre_id,
            inquiry_class,
            "material_counter_signal",
            material_counter_signals=summary["material_contradictions"],
        )

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
async def get_drift(
    investigation_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get drift events for an investigation."""
    repo = InvestigationRepository(db)
    inv = await repo.get(investigation_id)
    if not inv:
        raise HTTPException(status_code=404, detail=f"Investigation {investigation_id} not found")
    toolset = _rebuild_toolset(inv)
    return _build_drift_response(toolset)


@router.post("/{investigation_id}/drift", response_model=DriftEventResponse, status_code=201)
async def log_drift(
    investigation_id: str,
    request: DriftCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Log a drift event and trigger stop-condition evaluation."""
    repo = InvestigationRepository(db)
    inv = await repo.get(investigation_id)
    if not inv:
        raise HTTPException(status_code=404, detail=f"Investigation {investigation_id} not found")

    event = await repo.log_drift(
        investigation_id=investigation_id,
        drift_type=request.drift_type,
        original_value=request.original_value,
        new_value=request.new_value,
        impact_assessment=request.impact_assessment,
        evidence_ref=request.evidence_ref,
    )
    await db.commit()

    # Trigger stop-condition evaluation after drift mutation
    inv = await repo.get(investigation_id)
    if inv:
        await evaluate_after_mutation(db, inv, trigger="drift")
        await db.commit()

    return DriftEventResponse(
        drift_id=event.id,
        drift_type=event.drift_type,
        detected_at=event.detected_at,
        original_value=event.original_value or "",
        new_value=event.new_value or "",
        evidence_ref=event.evidence_ref,
        impact_assessment=event.impact_assessment or "non_material",
    )


@router.get("/{investigation_id}/readiness")
async def get_readiness(
    investigation_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Return current stop condition evaluation status."""
    repo = InvestigationRepository(db)
    inv = await repo.get(investigation_id)
    if not inv:
        raise HTTPException(status_code=404, detail=f"Investigation {investigation_id} not found")
    return {
        "investigation_id": inv.id,
        "status": inv.status,
        "stop_condition": inv.stop_condition,
        "stop_condition_status": inv.stop_condition_status,
        "stop_condition_reason": inv.stop_condition_reason,
        "stop_condition_evaluated_at": (
            inv.stop_condition_evaluated_at.isoformat()
            if inv.stop_condition_evaluated_at else None
        ),
        "has_certificate": inv.certificate is not None,
        "certificate_status": (
            inv.certificate.certificate_status
            if inv.certificate else None
        ),
    }


@router.post("/certificates/anchor-batch")
async def anchor_batch(db: AsyncSession = Depends(get_db)):
    """Process all READY certificates in a batch anchor.

    Transitions READY -> ANCHORED -> ISSUED atomically.
    Idempotent: second call is a no-op if no READY certificates exist.
    """
    issued_ids = await run_batch_anchor(db)
    await db.commit()
    return {
        "issued_count": len(issued_ids),
        "issued_certificate_ids": issued_ids,
    }


@router.get("/{investigation_id}/certificate")
async def get_certificate(
    investigation_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Return current certificate state (READY/ANCHORED/ISSUED) without building."""
    repo = InvestigationRepository(db)
    inv = await repo.get(investigation_id)
    if not inv:
        raise HTTPException(status_code=404, detail=f"Investigation {investigation_id} not found")
    if not inv.certificate:
        raise HTTPException(status_code=404, detail="No certificate exists. Use POST .../certificate/build.")
    cert = inv.certificate
    return {
        "certificate_id": cert.id,
        "investigation_id": cert.investigation_id,
        "certificate_status": cert.certificate_status,
        "certificate_hash": cert.certificate_hash,
        "routing_decision": cert.routing_decision,
        "routing_reason": cert.routing_reason,
        "ready_at": cert.ready_at.isoformat() if cert.ready_at else None,
        "anchored_at": cert.anchored_at.isoformat() if cert.anchored_at else None,
        "issued_at": cert.issued_at.isoformat() if cert.issued_at else None,
        "batch_anchor_hash": cert.batch_anchor_hash,
        "certificate_json": cert.certificate_json,
    }


@router.post("/{investigation_id}/certificate/build", status_code=201)
async def build_certificate(
    investigation_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Build certificate and transition to READY.

    Prerequisites: Investigation must be ACTIVE with stop conditions satisfied.
    Result: Certificate persisted with status=READY, investigation=CERTIFICATE_READY.
    """
    repo = InvestigationRepository(db)
    inv = await repo.get(investigation_id)
    if not inv:
        raise HTTPException(status_code=404, detail=f"Investigation {investigation_id} not found")
    if inv.certificate:
        raise HTTPException(status_code=409, detail="Certificate already exists")
    if inv.stop_condition_status != "READY":
        raise HTTPException(
            status_code=409,
            detail=f"Stop conditions not satisfied (status={inv.stop_condition_status})",
        )

    # Rebuild toolset and build certificate (existing logic + cycle-022 provenance)
    toolset = _rebuild_toolset(inv)
    cert = toolset.build_certificate(
        template_id=inv.template_id,
        template_name=inv.template.name if inv.template else None,
        committed_sources=inv.committed_sources_json,
    )

    # Persist certificate record in READY state (does NOT set COMPLETED)
    cert_record = await repo.persist_certificate_as_ready(
        investigation_id=investigation_id,
        certificate_hash=cert.certificate_hash,
        certificate_json={
            "certificate_id": cert.certificate_id,
            "theatre_id": cert.theatre_id,
            "construct_id": cert.construct_id,
        },
        routing_decision=cert.routing_decision,
        routing_reason=cert.routing_reason,
    )

    # Transition to READY via lifecycle service
    await transition_to_ready(db, cert_record, inv)
    await db.commit()

    # Trigger paradox-risk recompute
    await _recompute_theatre_paradox_risk(
        db,
        inv.theatre_id,
        inv.inquiry_class,
        "certificate_ready",
    )

    return {
        "certificate_id": cert_record.id,
        "certificate_status": cert_record.certificate_status,
        "certificate_hash": cert_record.certificate_hash,
        "ready_at": cert_record.ready_at.isoformat() if cert_record.ready_at else None,
        "routing_decision": cert_record.routing_decision,
    }
