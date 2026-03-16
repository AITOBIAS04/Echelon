"""Construct Verification API Routes.

Registration, evaluation runs, episodes, and certificate endpoints.
All routes version-addressable via /:slug/:version. No UUID in public API.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import (
    ConstructRegistration,
    Investigation,
    InvestigationEvidenceItem,
)
from backend.dependencies import get_db
from backend.schemas.construct_schemas import (
    ConstructRegistrationRequest,
    ConstructRegistrationResponse,
    ConstructRegistrationListItem,
    CreateRunResponse,
    EpisodeCaptureRequest,
    EpisodeCaptureResponse,
    EpisodeDetail,
    RunDetailResponse,
    CertificateResponse,
)
from backend.services.construct_registry import ConstructRegistry
from backend.services.construct_adapter import ConstructAdapter
from backend.services.test_prompt_registry import TestPromptRegistry

logger = logging.getLogger(__name__)

construct_router = APIRouter(
    prefix="/api/constructs",
    tags=["constructs"],
)

# Singleton prompt registry (loaded once)
_prompt_registry = TestPromptRegistry()


# ── Registration ──


@construct_router.post("/register", response_model=ConstructRegistrationResponse, status_code=201)
async def register_construct(
    body: ConstructRegistrationRequest,
    session: AsyncSession = Depends(get_db),
):
    """Register a construct for verification."""
    registry = ConstructRegistry(session)

    try:
        reg = await registry.register(
            slug=body.slug,
            version=body.version,
            content_hash=body.content_hash,
            skill_manifest=body.skill_manifest,
            domain_claims=body.domain_claims,
            test_prompts_hash=body.test_prompts_hash,
            rubric_hash=body.rubric_hash,
        )
        await session.commit()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return ConstructRegistrationResponse(
        id=reg.id,
        slug=reg.slug,
        version=reg.version,
        status=reg.status,
        commitment_hash=reg.commitment_hash,
        skill_count=reg.skill_count,
        created_at=getattr(reg, "created_at", None),
    )


@construct_router.get("/", response_model=list[ConstructRegistrationListItem])
async def list_constructs(
    session: AsyncSession = Depends(get_db),
):
    """List all registered constructs."""
    registry = ConstructRegistry(session)
    registrations = await registry.list_registered()

    return [
        ConstructRegistrationListItem(
            slug=r.slug,
            version=r.version,
            status=r.status,
            skill_count=r.skill_count,
            commitment_hash=r.commitment_hash,
        )
        for r in registrations
    ]


@construct_router.get("/{slug}/{version}", response_model=ConstructRegistrationResponse)
async def get_construct(
    slug: str,
    version: str,
    session: AsyncSession = Depends(get_db),
):
    """Get registration details for a specific construct version."""
    registry = ConstructRegistry(session)
    reg = await registry.get(slug, version)

    if reg is None:
        raise HTTPException(status_code=404, detail=f"Construct {slug}:{version} not found")

    return ConstructRegistrationResponse(
        id=reg.id,
        slug=reg.slug,
        version=reg.version,
        status=reg.status,
        commitment_hash=reg.commitment_hash,
        skill_count=reg.skill_count,
        created_at=getattr(reg, "created_at", None),
    )


# ── Runs ──


@construct_router.post("/{slug}/{version}/runs", response_model=CreateRunResponse, status_code=201)
async def create_run(
    slug: str,
    version: str,
    session: AsyncSession = Depends(get_db),
):
    """Create a new evaluation run for a registered construct."""
    registry = ConstructRegistry(session)
    reg = await registry.get(slug, version)

    if reg is None:
        raise HTTPException(status_code=404, detail=f"Construct {slug}:{version} not found")

    adapter = ConstructAdapter(session, _prompt_registry)

    try:
        investigation = await adapter.create_run(reg)
        await session.commit()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return CreateRunResponse(
        investigation_id=investigation.id,
        run_number=investigation.run_number,
        status=investigation.status,
        construct_id=investigation.construct_id,
    )


@construct_router.get("/{slug}/{version}/runs/{run_number}", response_model=RunDetailResponse)
async def get_run_detail(
    slug: str,
    version: str,
    run_number: int,
    session: AsyncSession = Depends(get_db),
):
    """Get run details with per-episode activity."""
    construct_id = f"{slug}:{version}"

    result = await session.execute(
        select(Investigation).where(
            Investigation.construct_id == construct_id,
            Investigation.run_number == run_number,
        )
    )
    investigation = result.scalar_one_or_none()

    if investigation is None:
        raise HTTPException(status_code=404, detail=f"Run {run_number} not found for {slug}:{version}")

    # Get evidence items
    ev_result = await session.execute(
        select(InvestigationEvidenceItem).where(
            InvestigationEvidenceItem.investigation_id == investigation.id,
        ).order_by(InvestigationEvidenceItem.submitted_at)
    )
    evidence_items = list(ev_result.scalars().all())

    # Build episode list and coverage summaries
    episodes = []
    domain_coverage: dict[str, int] = {}
    skill_coverage: dict[str, int] = {}

    for item in evidence_items:
        meta = item.construct_meta_json or {}
        domain = meta.get("domain", "unknown")
        skill = meta.get("skill_command", "unknown")

        domain_coverage[domain] = domain_coverage.get(domain, 0) + 1
        skill_coverage[skill] = skill_coverage.get(skill, 0) + 1

        episodes.append(EpisodeDetail(
            prompt_index=meta.get("prompt_index", 0),
            skill_command=skill,
            domain=domain,
            timing_ms=meta.get("timing_ms", 0),
            content_hash=item.content_hash,
            scores=meta.get("scores", {}),
            submitted_at=getattr(item, "submitted_at", None),
        ))

    config = investigation.stop_config_json or {}

    return RunDetailResponse(
        run_number=investigation.run_number,
        investigation_id=investigation.id,
        status=investigation.status,
        registration={"slug": slug, "version": version},
        commitment_hash=config.get("commitment_hash", ""),
        episodes=sorted(episodes, key=lambda e: e.prompt_index),
        domain_coverage=domain_coverage,
        skill_coverage=skill_coverage,
        started_at=getattr(investigation, "created_at", None),
        completed_at=None,
    )


@construct_router.post("/{slug}/{version}/runs/{run_number}/episodes", response_model=EpisodeCaptureResponse, status_code=201)
async def capture_episode(
    slug: str,
    version: str,
    run_number: int,
    body: EpisodeCaptureRequest,
    session: AsyncSession = Depends(get_db),
):
    """Capture an episode output as evidence."""
    construct_id = f"{slug}:{version}"

    result = await session.execute(
        select(Investigation).where(
            Investigation.construct_id == construct_id,
            Investigation.run_number == run_number,
        )
    )
    investigation = result.scalar_one_or_none()

    if investigation is None:
        raise HTTPException(status_code=404, detail=f"Run {run_number} not found for {slug}:{version}")

    adapter = ConstructAdapter(session, _prompt_registry)

    try:
        evidence = await adapter.capture_episode(
            investigation_id=investigation.id,
            skill_command=body.skill_command,
            domain=body.domain,
            prompt_index=body.prompt_index,
            output_text=body.output_text,
            timing_ms=body.timing_ms,
        )
        await session.commit()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return EpisodeCaptureResponse(
        evidence_id=evidence.id,
        content_hash=evidence.content_hash,
        prompt_index=body.prompt_index,
    )


@construct_router.post("/{slug}/{version}/runs/{run_number}/complete", status_code=200)
async def complete_run(
    slug: str,
    version: str,
    run_number: int,
    session: AsyncSession = Depends(get_db),
):
    """Complete an evaluation run and trigger validation."""
    construct_id = f"{slug}:{version}"

    result = await session.execute(
        select(Investigation).where(
            Investigation.construct_id == construct_id,
            Investigation.run_number == run_number,
        )
    )
    investigation = result.scalar_one_or_none()

    if investigation is None:
        raise HTTPException(status_code=404, detail=f"Run {run_number} not found for {slug}:{version}")

    adapter = ConstructAdapter(session, _prompt_registry)

    try:
        summary = await adapter.complete_run(investigation.id)
        await session.commit()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "status": "COMPLETE",
        "episode_count": summary.episode_count,
        "domain_coverage": summary.domain_coverage,
        "skill_coverage": summary.skill_coverage,
        "skill_coverage_ratio": summary.skill_coverage_ratio,
    }
