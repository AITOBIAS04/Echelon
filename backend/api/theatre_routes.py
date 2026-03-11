"""
Theatre API Routes — Theatre Template Engine backend integration.

12 endpoints for managing theatres, templates, and certificates.
Auth-protected mutations, public reads for commitment/certificate/template.
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import (
    Theatre,
    TheatreTemplate,
    TheatreCertificate,
    TheatreAuditEvent,
    TheatreEpisodeScore,
    AgentDeployment,
    Agent,
)
from backend.schemas.theatre import (
    TheatreCreate,
    TheatreRunRequest,
    TheatreSettleRequest,
    TemplateResponse,
    TemplateDetailResponse,
    TemplateListResponse,
    CommitmentReceiptResponse,
    TheatreResponse,
    TheatreListResponse,
    TheatreInvestigationContextResponse,
    TheatreInvestigationContextCertificateSummary,
    TheatreInvestigationContextDeploymentSummary,
    TheatreInvestigationContextConvergenceSummary,
    TheatreCertificateResponse,
    TheatreCertificateSummaryResponse,
    CertificateListResponse,
)
from backend.dependencies import get_current_user, get_db
from backend.auth.jwt import TokenData
from backend.services.theatre_bridge import run_theatre_task, THEATRE_ENGINE_AVAILABLE
from backend.services.coherence_gate_evaluator import CoherenceGateEvaluator

logger = logging.getLogger(__name__)

# Graceful import of engine components for validation
try:
    from theatre.engine.template_validator import TemplateValidator
    from theatre.engine.commitment import CommitmentProtocol
    from theatre.engine.state_machine import TheatreState

    _SCHEMA_PATH = Path(__file__).parent.parent.parent / "docs" / "schemas" / "echelon_theatre_schema_v2.json"
    if _SCHEMA_PATH.exists():
        _VALIDATOR = TemplateValidator(schema_path=_SCHEMA_PATH)
    else:
        _VALIDATOR = None
        logger.warning("Theatre schema not found at %s", _SCHEMA_PATH)
    _ENGINE_IMPORTED = True
except ImportError:
    _ENGINE_IMPORTED = False
    _VALIDATOR = None
    logger.warning("Theatre engine not importable — validation disabled")


router = APIRouter(prefix="/api/v1/theatres", tags=["theatres"])

# Separate router for templates and certificates (different prefix)
templates_router = APIRouter(prefix="/api/v1/templates", tags=["theatre-templates"])
certificates_router = APIRouter(prefix="/api/v1/certificates", tags=["theatre-certificates"])


# ============================================
# THEATRE ENDPOINTS (auth required for mutations)
# ============================================


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_theatre(
    body: TheatreCreate,
    user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new Theatre in DRAFT state. Validates template JSON."""
    # Validate template if validator available
    if _VALIDATOR is not None:
        errors = _VALIDATOR.validate(body.template_json, is_certificate_run=False)
        if errors:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"validation_errors": errors},
            )

    # Check if template exists, create if needed
    result = await db.execute(
        select(TheatreTemplate).where(TheatreTemplate.id == body.template_id)
    )
    template = result.scalar_one_or_none()

    if template is None:
        # Auto-create template from template_json
        template = TheatreTemplate(
            id=body.template_id,
            template_family=body.template_json.get("template_family", "PRODUCT"),
            execution_path=body.template_json.get("execution_path", "replay"),
            display_name=body.template_json.get("display_name", body.template_id),
            description=body.template_json.get("description"),
            schema_version=body.template_json.get("schema_version", "2.0.1"),
            inquiry_class=body.inquiry_class,
            template_json=body.template_json,
        )
        db.add(template)
        await db.flush()

    # Create theatre
    theatre_id = str(uuid.uuid4())
    theatre = Theatre(
        id=theatre_id,
        user_id=user.user_id,
        template_id=body.template_id,
        state="DRAFT",
        construct_id=body.construct_id,
        inquiry_class=body.inquiry_class,
        stop_condition=body.stop_condition,
        stop_config=body.stop_config,
    )
    db.add(theatre)

    # Add audit event
    audit = TheatreAuditEvent(
        id=str(uuid.uuid4()),
        theatre_id=theatre_id,
        event_type="theatre_created",
        to_state="DRAFT",
        detail_json={
            "template_id": body.template_id,
            "construct_id": body.construct_id,
        },
    )
    db.add(audit)

    await db.commit()
    await db.refresh(theatre)

    response = {
        "id": theatre.id,
        "state": theatre.state,
        "template_id": theatre.template_id,
        "inquiry_class": theatre.inquiry_class or "COUNTERFACTUAL",
        "created_at": theatre.created_at,
    }
    if theatre.stop_condition is not None:
        response["stop_condition"] = theatre.stop_condition
    if theatre.stop_config is not None:
        response["stop_config"] = theatre.stop_config
    return response


@router.post("/{theatre_id}/commit", status_code=status.HTTP_200_OK)
async def commit_theatre(
    theatre_id: str,
    user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate commitment hash and transition to COMMITTED."""
    theatre = await _get_user_theatre(db, theatre_id, user.user_id)

    if theatre.state != "DRAFT":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot commit theatre in state {theatre.state} (must be DRAFT)",
        )

    # Load template
    template = await db.get(TheatreTemplate, theatre.template_id)
    if template is None:
        raise HTTPException(status_code=404, detail="Template not found")

    template_json = template.template_json

    # Extract version_pins and dataset_hashes from template
    version_pins = template_json.get("version_pins", {})
    dataset_hashes = template_json.get("dataset_hashes", {})

    # Build stop fields payload for commitment hash inclusion
    stop_fields = {}
    if theatre.stop_condition is not None:
        stop_fields["stop_condition"] = theatre.stop_condition
    if theatre.stop_config is not None:
        stop_fields["stop_config"] = theatre.stop_config

    # Compute commitment hash (includes stop fields when present)
    if _ENGINE_IMPORTED:
        commitment_hash = CommitmentProtocol.compute_hash(
            template=template_json,
            version_pins=version_pins,
            dataset_hashes=dataset_hashes,
        )
        # Extend with stop fields if present
        if stop_fields:
            import hashlib
            extended_payload = commitment_hash + json.dumps(stop_fields, sort_keys=True)
            commitment_hash = hashlib.sha256(extended_payload.encode()).hexdigest()
    else:
        # Fallback: simple hash
        import hashlib
        hash_payload = {**template_json, **stop_fields}
        commitment_hash = hashlib.sha256(
            json.dumps(hash_payload, sort_keys=True).encode()
        ).hexdigest()

    now = datetime.utcnow()
    theatre.state = "COMMITTED"
    theatre.commitment_hash = commitment_hash
    theatre.committed_at = now
    theatre.version_pins = version_pins
    theatre.dataset_hashes = dataset_hashes
    theatre.updated_at = now

    # Add audit event
    audit = TheatreAuditEvent(
        id=str(uuid.uuid4()),
        theatre_id=theatre_id,
        event_type="theatre_committed",
        from_state="DRAFT",
        to_state="COMMITTED",
        detail_json={
            "commitment_hash": commitment_hash,
        },
    )
    db.add(audit)

    await db.commit()
    await db.refresh(theatre)

    return CommitmentReceiptResponse(
        theatre_id=theatre.id,
        commitment_hash=commitment_hash,
        committed_at=now,
        version_pins=version_pins,
        dataset_hashes=dataset_hashes,
    )


@router.post("/{theatre_id}/run", status_code=status.HTTP_202_ACCEPTED)
async def run_theatre(
    theatre_id: str,
    body: TheatreRunRequest = TheatreRunRequest(),
    user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Launch background execution task. Replay path only."""
    theatre = await _get_user_theatre(db, theatre_id, user.user_id)

    if theatre.state != "COMMITTED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot run theatre in state {theatre.state} (must be COMMITTED)",
        )

    # Check execution path
    template = await db.get(TheatreTemplate, theatre.template_id)
    if template and template.execution_path == "market":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Market theatres use /settle, not /run",
        )

    # Determine adapter type from template config
    ptc = template.template_json.get("product_theatre_config", {}) if template else {}
    adapter_type = ptc.get("adapter_type", "mock")
    local_mode = adapter_type == "mock"

    # Transition to ACTIVE is handled by bridge
    await db.commit()

    # Launch background task
    asyncio.create_task(run_theatre_task(theatre_id))
    logger.info("Started theatre run %s", theatre_id)

    response = {
        "theatre_id": theatre.id,
        "status": "accepted",
        "message": "Theatre execution started",
        "adapter_type": adapter_type,
        "local_mode": local_mode,
    }
    if local_mode:
        response["local_mode_note"] = (
            "Mock adapter in use. Certificates will not be signed."
        )
    return response


@router.get("/{theatre_id}", response_model=TheatreResponse)
async def get_theatre(
    theatre_id: str,
    include: Optional[str] = Query(None),
    user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get theatre state and progress. Auth: owner only.

    Paradox risk is recomputed via orchestrator if stale or absent (Cycle 020).
    Uses trigger_recompute for materiality detection + WS emission readiness.
    """
    theatre = await _get_user_theatre(db, theatre_id, user.user_id)

    # On-read paradox risk: recompute via orchestrator if absent or stale (>1h)
    should_compute = theatre.paradox_risk_level is None
    if not should_compute and theatre.paradox_risk_updated_at:
        age_seconds = (datetime.utcnow() - theatre.paradox_risk_updated_at).total_seconds()
        should_compute = age_seconds > 3600  # stale after 1 hour

    if should_compute:
        from backend.services.paradox_risk_orchestrator import trigger_recompute
        inquiry_class = getattr(theatre, "inquiry_class", None) or "COUNTERFACTUAL"
        await trigger_recompute(
            db, theatre_id, "evidence_freshness_threshold",
            inquiry_class=inquiry_class,
            emit_ws=True,
        )
        await db.commit()

    include_fields = {part.strip() for part in (include or "").split(",") if part.strip()}
    payload = TheatreResponse.model_validate(theatre).model_dump()

    if "investigation_context" in include_fields:
        certificate_summary = None
        if theatre.certificate_id:
            cert = await db.get(TheatreCertificate, theatre.certificate_id)
            if cert is not None:
                certificate_summary = TheatreInvestigationContextCertificateSummary(
                    certificate_id=cert.id,
                    routing_hint=cert.routing_hint,
                    composite_score=cert.composite_score,
                    verification_tier=cert.verification_tier,
                    coherence_gate_status=cert.coherence_gate_status,
                    issued_at=cert.issued_at,
                )

        active_deployments_result = await db.execute(
            select(Agent.archetype, func.count())
            .select_from(AgentDeployment)
            .join(Agent, Agent.id == AgentDeployment.agent_id)
            .where(
                AgentDeployment.theatre_id == theatre.id,
                AgentDeployment.status == "ACTIVE",
            )
            .group_by(Agent.archetype)
        )
        archetype_breakdown = {
            str(archetype.value if hasattr(archetype, "value") else archetype): count
            for archetype, count in active_deployments_result.all()
        }
        active_count = sum(archetype_breakdown.values())

        from backend.api.convergence_routes import get_heatmap

        heatmap = await get_heatmap()
        matching_cells = [
            cell for cell in heatmap.cells
            if theatre.id in cell.theatres
        ]
        source_families = sorted({source for cell in matching_cells for source in cell.sources})
        nearby_signal_count = sum(cell.events for cell in matching_cells)

        payload["investigation_context"] = TheatreInvestigationContextResponse(
            certificate_summary=certificate_summary,
            deployment_summary=TheatreInvestigationContextDeploymentSummary(
                active_count=active_count,
                archetype_breakdown=archetype_breakdown,
            ),
            paradox_risk_level=theatre.paradox_risk_level,
            paradox_risk_factors_json=theatre.paradox_risk_factors_json,
            convergence_summary=TheatreInvestigationContextConvergenceSummary(
                cell_count=len(matching_cells),
                nearby_signal_count=nearby_signal_count,
                source_families=source_families,
            ),
        ).model_dump()

    return TheatreResponse(**payload)


@router.get("/{theatre_id}/commitment", response_model=CommitmentReceiptResponse)
async def get_commitment(
    theatre_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get commitment receipt. Public endpoint."""
    result = await db.execute(
        select(Theatre).where(Theatre.id == theatre_id)
    )
    theatre = result.scalar_one_or_none()
    if theatre is None:
        raise HTTPException(status_code=404, detail="Theatre not found")
    if theatre.commitment_hash is None:
        raise HTTPException(status_code=404, detail="Theatre has no commitment")

    return CommitmentReceiptResponse(
        theatre_id=theatre.id,
        commitment_hash=theatre.commitment_hash,
        committed_at=theatre.committed_at,
        version_pins=theatre.version_pins or {},
        dataset_hashes=theatre.dataset_hashes or {},
    )


@router.post("/{theatre_id}/settle", status_code=status.HTTP_200_OK)
async def settle_theatre(
    theatre_id: str,
    body: TheatreSettleRequest,
    user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Manual settlement for Market theatres.

    Normal path: calls ResolutionEngine.check_resolution_ready() to determine
    readiness and trigger reason, then transitions state.
    force=True: bypasses readiness check (admin/testing only, logged as warning).
    """
    from backend.market.resolution import ResolutionEngine

    theatre = await _get_user_theatre(db, theatre_id, user.user_id)

    # Check execution path
    template = await db.get(TheatreTemplate, theatre.template_id)
    if template and template.execution_path != "market":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only market theatres can be settled manually",
        )

    if theatre.state not in ("ACTIVE", "SETTLING"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot settle theatre in state {theatre.state}",
        )

    inquiry_class = theatre.inquiry_class or "COUNTERFACTUAL"
    force = body.settlement_data.get("force", False)

    # Route through ResolutionEngine unless force=True
    if force:
        logger.warning(
            "Theatre %s settled with force=True, bypassing ResolutionEngine",
            theatre_id,
        )
        resolution_trigger_reason = body.settlement_data.get(
            "resolution_trigger_reason", "time_window_closed"
        )
    else:
        # Build evidence state from settlement_data (caller provides evidence snapshot)
        evidence_state = body.settlement_data.get(
            "evidence_state", {"time_window_expired": True}
        )
        theatre_config = {}
        if template:
            theatre_config = template.template_json.get(
                "product_theatre_config", {}
            )

        ready, trigger = ResolutionEngine.check_resolution_ready(
            inquiry_class=inquiry_class,
            evidence_state=evidence_state,
            theatre_config=theatre_config,
            stop_condition=theatre.stop_condition,
            stop_config=theatre.stop_config,
        )
        if not ready:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Theatre not ready for resolution (trigger={trigger.value}). "
                f"Use force=True to override.",
            )
        resolution_trigger_reason = str(trigger)

    now = datetime.utcnow()
    previous_state = theatre.state
    theatre.state = "RESOLVED"
    theatre.resolved_at = now
    theatre.updated_at = now

    audit = TheatreAuditEvent(
        id=str(uuid.uuid4()),
        theatre_id=theatre_id,
        event_type="theatre_settled",
        from_state=previous_state,
        to_state="RESOLVED",
        detail_json={
            **body.settlement_data,
            "inquiry_class": inquiry_class,
            "resolution_trigger_reason": resolution_trigger_reason,
        },
    )
    db.add(audit)

    await db.commit()
    await db.refresh(theatre)

    return {
        "theatre_id": theatre.id,
        "state": theatre.state,
        "inquiry_class": inquiry_class,
        "resolution_trigger_reason": resolution_trigger_reason,
        "resolved_at": now,
    }


@router.get("/{theatre_id}/certificate", response_model=TheatreCertificateResponse)
async def get_theatre_certificate(
    theatre_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get certificate for a resolved theatre. Public endpoint."""
    from sqlalchemy import or_

    result = await db.execute(
        select(Theatre).where(
            or_(Theatre.id == theatre_id, Theatre.construct_id == theatre_id)
        )
    )
    theatre = result.scalar_one_or_none()
    if theatre is None:
        raise HTTPException(status_code=404, detail="Theatre not found")
    if theatre.certificate_id is None:
        raise HTTPException(status_code=404, detail="Theatre has no certificate")

    cert = await db.get(TheatreCertificate, theatre.certificate_id)
    if cert is None:
        raise HTTPException(status_code=404, detail="Certificate not found")

    return TheatreCertificateResponse.model_validate(cert)


@router.get("/{theatre_id}/replay")
async def get_theatre_replay(
    theatre_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get RLMF export data for a resolved theatre. Public endpoint."""
    from sqlalchemy import or_

    result = await db.execute(
        select(Theatre).where(
            or_(Theatre.id == theatre_id, Theatre.construct_id == theatre_id)
        )
    )
    theatre = result.scalar_one_or_none()
    if theatre is None:
        raise HTTPException(status_code=404, detail="Theatre not found")
    if theatre.state != "RESOLVED":
        raise HTTPException(status_code=404, detail="Theatre not resolved")

    # Load episode scores
    scores_result = await db.execute(
        select(TheatreEpisodeScore)
        .where(TheatreEpisodeScore.theatre_id == theatre_id)
        .order_by(TheatreEpisodeScore.scored_at)
    )
    scores = scores_result.scalars().all()

    return {
        "theatre_id": theatre.id,
        "construct_id": theatre.construct_id,
        "template_id": theatre.template_id,
        "episode_count": len(scores),
        "episodes": [
            {
                "episode_id": s.episode_id,
                "invocation_status": s.invocation_status,
                "scores": s.scores_json,
                "composite_score": s.composite_score,
            }
            for s in scores
        ],
    }


# ============================================
# TEMPLATE ENDPOINTS (public)
# ============================================


@templates_router.get("/", response_model=TemplateListResponse)
async def list_templates(
    db: AsyncSession = Depends(get_db),
    family: Optional[str] = Query(None),
    execution_path: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """List templates with optional filtering. Public endpoint."""
    query = select(TheatreTemplate)
    count_query = select(func.count()).select_from(TheatreTemplate)

    if family:
        query = query.where(TheatreTemplate.template_family == family)
        count_query = count_query.where(TheatreTemplate.template_family == family)
    if execution_path:
        query = query.where(TheatreTemplate.execution_path == execution_path)
        count_query = count_query.where(TheatreTemplate.execution_path == execution_path)

    query = query.order_by(TheatreTemplate.created_at.desc()).offset(offset).limit(limit)

    result = await db.execute(query)
    templates = result.scalars().all()

    count_result = await db.execute(count_query)
    total = count_result.scalar()

    return TemplateListResponse(
        templates=[TemplateResponse.model_validate(t) for t in templates],
        total=total,
        limit=limit,
        offset=offset,
    )


@templates_router.get("/{template_id}", response_model=TemplateDetailResponse)
async def get_template(
    template_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a single template. Public endpoint."""
    template = await db.get(TheatreTemplate, template_id)
    if template is None:
        raise HTTPException(status_code=404, detail="Template not found")
    return TemplateDetailResponse.model_validate(template)


# ============================================
# CERTIFICATE ENDPOINTS (public)
# ============================================


@certificates_router.get("/{certificate_id}", response_model=TheatreCertificateResponse)
async def get_certificate(
    certificate_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a single certificate by ID. Public endpoint."""
    cert = await db.get(TheatreCertificate, certificate_id)
    if cert is None:
        raise HTTPException(status_code=404, detail="Certificate not found")
    return TheatreCertificateResponse.model_validate(cert)


@certificates_router.get("/", response_model=CertificateListResponse)
async def list_certificates(
    db: AsyncSession = Depends(get_db),
    construct_id: Optional[str] = Query(None),
    verification_tier: Optional[str] = Query(None),
    routing_hint: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """List certificates with optional filtering. Public endpoint."""
    query = select(TheatreCertificate)
    count_query = select(func.count()).select_from(TheatreCertificate)

    if construct_id:
        query = query.where(TheatreCertificate.construct_id == construct_id)
        count_query = count_query.where(TheatreCertificate.construct_id == construct_id)
    if verification_tier:
        query = query.where(TheatreCertificate.verification_tier == verification_tier)
        count_query = count_query.where(TheatreCertificate.verification_tier == verification_tier)
    if routing_hint:
        query = query.where(TheatreCertificate.routing_hint == routing_hint.upper())
        count_query = count_query.where(TheatreCertificate.routing_hint == routing_hint.upper())

    query = query.order_by(TheatreCertificate.issued_at.desc()).offset(offset).limit(limit)

    result = await db.execute(query)
    certs = result.scalars().all()

    count_result = await db.execute(count_query)
    total = count_result.scalar()

    return CertificateListResponse(
        certificates=[TheatreCertificateSummaryResponse.model_validate(c) for c in certs],
        total=total,
        limit=limit,
        offset=offset,
    )


# ============================================
# GATE ENDPOINTS (on certificates router)
# ============================================


class GateResolveRequest(BaseModel):
    """Request body for POST /api/v1/certificates/{id}/gate/resolve."""

    status: str  # PASSED or FAILED


@certificates_router.get("/{certificate_id}/gate")
async def get_gate_status(
    certificate_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get coherence gate status and audit trail for a certificate."""
    cert = await db.get(TheatreCertificate, certificate_id)
    if cert is None:
        raise HTTPException(status_code=404, detail="Certificate not found")

    # Load audit events for this certificate's gate
    result = await db.execute(
        select(TheatreAuditEvent)
        .where(
            TheatreAuditEvent.theatre_id == cert.theatre_id,
            TheatreAuditEvent.event_type.in_([
                "COHERENCE_GATE_OPENED",
                "COHERENCE_GATE_RESOLVED",
            ]),
        )
        .order_by(TheatreAuditEvent.created_at)
    )
    audit_events = result.scalars().all()

    return {
        "certificate_id": certificate_id,
        "coherence_review_required": cert.coherence_review_required,
        "coherence_gate_status": cert.coherence_gate_status,
        "coherence_reviewed_at": cert.coherence_reviewed_at,
        "coherence_reviewer_id": cert.coherence_reviewer_id,
        "audit_trail": [
            {
                "event_type": e.event_type,
                "detail_json": e.detail_json,
                "created_at": e.created_at,
            }
            for e in audit_events
        ],
    }


@certificates_router.post("/{certificate_id}/gate/resolve")
async def resolve_gate(
    certificate_id: str,
    body: GateResolveRequest,
    user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Resolve a coherence gate (PASSED or FAILED). Auth required."""
    if body.status not in ("PASSED", "FAILED"):
        raise HTTPException(
            status_code=422,
            detail="status must be PASSED or FAILED",
        )

    cert = await db.get(TheatreCertificate, certificate_id)
    if cert is None:
        raise HTTPException(status_code=404, detail="Certificate not found")

    if cert.coherence_gate_status != "PENDING":
        raise HTTPException(
            status_code=400,
            detail=f"Cannot resolve gate in status '{cert.coherence_gate_status}'. Must be PENDING.",
        )

    evaluator = CoherenceGateEvaluator()
    await evaluator.resolve_gate(
        session=db,
        certificate_id=certificate_id,
        status=body.status,
        reviewer_id=user.user_id,
    )
    await db.commit()
    await db.refresh(cert)

    return {
        "certificate_id": certificate_id,
        "coherence_gate_status": cert.coherence_gate_status,
        "coherence_reviewed_at": cert.coherence_reviewed_at,
        "coherence_reviewer_id": cert.coherence_reviewer_id,
    }


# ============================================
# HELPERS
# ============================================


async def _get_user_theatre(
    db: AsyncSession, theatre_id: str, user_id: str
) -> Theatre:
    """Load a theatre belonging to the given user, or raise 404.

    Looks up by primary key first, then falls back to construct_id.
    This allows the frontend to navigate using either the UUID id or
    the human-readable construct_id (e.g. timeline IDs like TL_*).

    On testnet (TESTNET_AUTO_AUTH=true), skips user_id filter so that
    seeded theatres are always accessible regardless of owner.
    """
    import os
    from sqlalchemy import or_

    testnet_auto = os.getenv("TESTNET_AUTO_AUTH", "false").lower() == "true"

    query = select(Theatre).where(
        or_(Theatre.id == theatre_id, Theatre.construct_id == theatre_id),
    )
    if not testnet_auto:
        query = query.where(Theatre.user_id == user_id)

    result = await db.execute(query
    )
    theatre = result.scalar_one_or_none()
    if theatre is None:
        raise HTTPException(status_code=404, detail="Theatre not found")
    return theatre
