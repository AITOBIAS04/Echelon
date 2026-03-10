"""
Scenario Pack API Routes — Template catalog and pack management endpoints.

Sprint 1: Template catalog (list + detail).
Sprint 2: Pack lifecycle (create, commit, run).
Sprint 3: Checkpoint resolution, branch probabilities, episode tree, replay.
Sprint 4: Derived theatre spawning.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.database.models import (
    ScenarioPackTemplate,
    ScenarioCheckpoint,
    ScenarioPack,
    ScenarioRun,
    RunCheckpointResult,
    Theatre,
)
from backend.schemas.scenario_packs import (
    ScenarioPackTemplateResponse,
    ScenarioPackTemplateSummaryResponse,
    TemplateListResponse,
    ScenarioPackCreate,
    ScenarioPackResponse,
    ScenarioRunResponse,
    BranchProbabilitiesResponse,
    EpisodeTreeResponse,
    EpisodeTreeNode,
    ForkReplayResponse,
    DerivedTheatreResponse,
)
from backend.dependencies import get_db, get_current_user
from backend.auth.jwt import TokenData

logger = logging.getLogger(__name__)

templates_router = APIRouter(
    prefix="/api/v1/scenario-pack-templates",
    tags=["scenario-pack-templates"],
)


@templates_router.get("/", response_model=TemplateListResponse)
async def list_templates(
    family: Optional[str] = Query(None, description="Filter by template family (case-insensitive)"),
    status: Optional[str] = Query(None, description="Filter by template_status (RUNNABLE or CATALOG_ONLY)"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_db),
):
    """List scenario pack templates with optional family and status filters."""
    try:
        query = select(ScenarioPackTemplate)
        count_query = select(func.count()).select_from(ScenarioPackTemplate)

        if family:
            family_upper = family.upper()
            query = query.where(ScenarioPackTemplate.family == family_upper)
            count_query = count_query.where(ScenarioPackTemplate.family == family_upper)

        if status:
            status_upper = status.upper()
            query = query.where(ScenarioPackTemplate.template_status == status_upper)
            count_query = count_query.where(ScenarioPackTemplate.template_status == status_upper)

        # Get total count
        total_result = await session.execute(count_query)
        total = total_result.scalar() or 0

        # Get paginated results with checkpoint count
        query = query.order_by(ScenarioPackTemplate.family, ScenarioPackTemplate.name)
        query = query.offset(offset).limit(limit)
        result = await session.execute(query)
        templates = result.scalars().all()

        # Build summaries with checkpoint counts
        summaries = []
        for t in templates:
            cp_count_result = await session.execute(
                select(func.count()).select_from(ScenarioCheckpoint)
                .where(ScenarioCheckpoint.template_id == t.id)
            )
            cp_count = cp_count_result.scalar() or 0

            summaries.append(ScenarioPackTemplateSummaryResponse(
                id=t.id,
                name=t.name,
                family=t.family,
                description=t.description,
                template_status=t.template_status,
                checkpoint_count=cp_count,
                fork_points_min=t.fork_points_min,
                fork_points_max=t.fork_points_max,
                is_seeded=t.is_seeded,
            ))

        return TemplateListResponse(
            templates=summaries,
            total=total,
            limit=limit,
            offset=offset,
        )
    except Exception as e:
        logger.error(f"❌ list_templates failed: {type(e).__name__}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Scenario pack query failed: {type(e).__name__}: {e}")


@templates_router.get("/{template_id}", response_model=ScenarioPackTemplateResponse)
async def get_template(
    template_id: str,
    session: AsyncSession = Depends(get_db),
):
    """Get a single template with full detail including checkpoints."""
    result = await session.execute(
        select(ScenarioPackTemplate)
        .options(selectinload(ScenarioPackTemplate.checkpoints))
        .where(ScenarioPackTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()

    if not template:
        raise HTTPException(status_code=404, detail=f"Template '{template_id}' not found")

    # Build checkpoint responses
    checkpoint_responses = []
    for cp in template.checkpoints:
        # Count branches for this checkpoint
        branch_count_result = await session.execute(
            select(func.count()).select_from(
                select(ScenarioCheckpoint).where(ScenarioCheckpoint.id == cp.id).subquery()
            )
        )
        from backend.database.models import CheckpointBranch
        branch_count_result = await session.execute(
            select(func.count()).select_from(CheckpointBranch)
            .where(CheckpointBranch.checkpoint_id == cp.id)
        )
        branch_count = branch_count_result.scalar() or 0

        from backend.schemas.scenario_packs import CheckpointResponse
        checkpoint_responses.append(CheckpointResponse(
            id=cp.id,
            sequence_num=cp.sequence_num,
            trigger=cp.trigger,
            market_question=cp.market_question,
            decision_window_sec=cp.decision_window_sec,
            can_spawn_theatre=cp.can_spawn_theatre,
            evaluator_type=cp.evaluator_type,
            branch_count=branch_count,
        ))

    return ScenarioPackTemplateResponse(
        id=template.id,
        name=template.name,
        description=template.description,
        family=template.family,
        fantasy=template.fantasy,
        training_primitives=template.training_primitives,
        template_status=template.template_status,
        objective_vector=template.objective_vector_json or [],
        fork_points=template.fork_point_schema_json or [],
        saboteur_deck=template.saboteur_deck_json or [],
        episode_length_sec=template.episode_length_sec,
        fork_points_min=template.fork_points_min,
        fork_points_max=template.fork_points_max,
        is_seeded=template.is_seeded,
        checkpoint_count=len(template.checkpoints),
        checkpoints=checkpoint_responses,
        created_at=template.created_at,
    )


# ── Pack Endpoints (Sprint 2) ──────────────────────────────────────────────

packs_router = APIRouter(
    prefix="/api/v1/scenario-packs",
    tags=["scenario-packs"],
)


@packs_router.post("/", response_model=ScenarioPackResponse, status_code=201)
async def create_pack(
    body: ScenarioPackCreate,
    user: TokenData = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """Create a new scenario pack from a RUNNABLE template."""
    from backend.services.scenario_pack_lifecycle import create_pack as _create_pack

    try:
        pack = await _create_pack(
            session=session,
            user_id=user.user_id,
            template_id=body.template_id,
            run_mode=body.run_mode,
            agent_assignment=body.agent_assignment,
            simulation_scale=body.simulation_scale,
            objective_profile=body.objective_profile,
            config_json=body.config_json,
        )
        await session.commit()
        return pack
    except LookupError:
        raise HTTPException(status_code=404, detail=f"Template '{body.template_id}' not found")
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@packs_router.get("/{pack_id}", response_model=ScenarioPackResponse)
async def get_pack(
    pack_id: str,
    user: TokenData = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """Get a scenario pack (owner only)."""
    result = await session.execute(
        select(ScenarioPack).where(ScenarioPack.id == pack_id)
    )
    pack = result.scalar_one_or_none()

    if not pack:
        raise HTTPException(status_code=404, detail="Pack not found")
    if pack.user_id != user.user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    return pack


@packs_router.post("/{pack_id}/commit", response_model=ScenarioPackResponse)
async def commit_pack(
    pack_id: str,
    user: TokenData = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """Commit a pack (DRAFT → COMMITTED). Generates commitment hash."""
    from backend.services.scenario_pack_lifecycle import commit_pack as _commit_pack

    result = await session.execute(
        select(ScenarioPack).where(ScenarioPack.id == pack_id)
    )
    pack = result.scalar_one_or_none()

    if not pack:
        raise HTTPException(status_code=404, detail="Pack not found")
    if pack.user_id != user.user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    try:
        pack = await _commit_pack(session, pack)
        await session.commit()
        return pack
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@packs_router.post("/{pack_id}/run", response_model=ScenarioRunResponse, status_code=202)
async def run_pack(
    pack_id: str,
    user: TokenData = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """Launch a run (COMMITTED → ACTIVE). Returns the created run."""
    from backend.services.scenario_pack_lifecycle import launch_run

    result = await session.execute(
        select(ScenarioPack).where(ScenarioPack.id == pack_id)
    )
    pack = result.scalar_one_or_none()

    if not pack:
        raise HTTPException(status_code=404, detail="Pack not found")
    if pack.user_id != user.user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    try:
        run = await launch_run(session, pack)
        await session.commit()
        return run
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


# ── Sprint 3: Branch Probabilities ──────────────────────────────────────────

@templates_router.get(
    "/{template_id}/branch-probabilities",
    response_model=BranchProbabilitiesResponse,
)
async def get_branch_probabilities(
    template_id: str,
    session: AsyncSession = Depends(get_db),
):
    """Get branch selection probabilities computed from fresh completed runs."""
    result = await session.execute(
        select(ScenarioPackTemplate).where(ScenarioPackTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail=f"Template '{template_id}' not found")

    from backend.services.checkpoint_evaluator import compute_branch_probabilities
    probabilities = await session.run_sync(
        lambda sync_session: compute_branch_probabilities(sync_session, template_id)
    )

    return BranchProbabilitiesResponse(
        template_id=template_id,
        probabilities=probabilities,
    )


# ── Sprint 3: Episode Tree ──────────────────────────────────────────────────

@packs_router.get(
    "/{pack_id}/runs/{run_id}/tree",
    response_model=EpisodeTreeResponse,
)
async def get_episode_tree(
    pack_id: str,
    run_id: str,
    user: TokenData = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """Get the episode tree for a completed run."""
    pack_result = await session.execute(
        select(ScenarioPack).where(ScenarioPack.id == pack_id)
    )
    pack = pack_result.scalar_one_or_none()
    if not pack:
        raise HTTPException(status_code=404, detail="Pack not found")
    if pack.user_id != user.user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    run_result = await session.execute(
        select(ScenarioRun).where(
            ScenarioRun.id == run_id,
            ScenarioRun.pack_id == pack_id,
        )
    )
    run = run_result.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    template_result = await session.execute(
        select(ScenarioPackTemplate).where(ScenarioPackTemplate.id == pack.template_id)
    )
    template = template_result.scalar_one_or_none()

    from backend.database.models import RunCheckpointResult, CheckpointBranch
    cp_results = (await session.execute(
        select(RunCheckpointResult)
        .where(RunCheckpointResult.run_id == run_id)
        .order_by(RunCheckpointResult.resolved_at)
    )).scalars().all()

    nodes = []
    for cr in cp_results:
        cp = (await session.execute(
            select(ScenarioCheckpoint).where(ScenarioCheckpoint.id == cr.checkpoint_id)
        )).scalar_one_or_none()
        br = (await session.execute(
            select(CheckpointBranch).where(CheckpointBranch.id == cr.selected_branch_id)
        )).scalar_one_or_none()

        if cp and br:
            nodes.append(EpisodeTreeNode(
                checkpoint_id=cp.id,
                sequence_num=cp.sequence_num,
                trigger=cp.trigger,
                market_question=cp.market_question,
                selected_branch=br.label,
                outcome_type=br.outcome_type,
                reward=cr.reward,
                spawned_theatre_id=cr.spawned_theatre_id,
            ))

    return EpisodeTreeResponse(
        run_id=run.id,
        pack_id=pack.id,
        template_name=template.name if template else "Unknown",
        status=run.status,
        nodes=nodes,
        total_reward=run.total_reward,
        episode_duration_sec=run.episode_duration_sec,
    )


# ── Sprint 3: Replay Output ─────────────────────────────────────────────────

@packs_router.get(
    "/{pack_id}/runs/{run_id}/replay",
    response_model=ForkReplayResponse,
)
async def get_replay(
    pack_id: str,
    run_id: str,
    user: TokenData = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """Get ForkReplay-compatible output for a run."""
    pack_result = await session.execute(
        select(ScenarioPack).where(ScenarioPack.id == pack_id)
    )
    pack = pack_result.scalar_one_or_none()
    if not pack:
        raise HTTPException(status_code=404, detail="Pack not found")
    if pack.user_id != user.user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    run_result = await session.execute(
        select(ScenarioRun).where(
            ScenarioRun.id == run_id,
            ScenarioRun.pack_id == pack_id,
        )
    )
    run = run_result.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    template_result = await session.execute(
        select(ScenarioPackTemplate).where(ScenarioPackTemplate.id == pack.template_id)
    )
    template = template_result.scalar_one_or_none()

    from backend.database.models import RunCheckpointResult, CheckpointBranch
    cp_results = (await session.execute(
        select(RunCheckpointResult)
        .where(RunCheckpointResult.run_id == run_id)
        .order_by(RunCheckpointResult.resolved_at)
    )).scalars().all()

    disclosure_events = []
    options = []
    time_offset = 0

    for cr in cp_results:
        cp = (await session.execute(
            select(ScenarioCheckpoint).where(ScenarioCheckpoint.id == cr.checkpoint_id)
        )).scalar_one_or_none()
        br = (await session.execute(
            select(CheckpointBranch).where(CheckpointBranch.id == cr.selected_branch_id)
        )).scalar_one_or_none()

        if not cp or not br:
            continue

        disclosure_events.append({
            "tMs": time_offset,
            "type": "evidence_flip",
            "label": f"Checkpoint {cp.sequence_num}: {br.label}",
        })

        options.append({
            "label": br.label,
            "pricePath": [
                {"tMs": time_offset, "price": 0.5},
                {"tMs": time_offset + cp.decision_window_sec * 1000,
                 "price": 1.0 if cr.reward > 0 else 0.0},
            ],
        })

        time_offset += cp.decision_window_sec * 1000

    opened_at = run.started_at.isoformat() if run.started_at else run.created_at.isoformat()
    settled_at = run.completed_at.isoformat() if run.completed_at else None

    return ForkReplayResponse(
        timelineId=f"scenario_{pack.id}",
        forkId=run.id,
        forkQuestion=template.name if template else "Scenario Run",
        options=options,
        openedAt=opened_at,
        settledAt=settled_at,
        chosenOption=options[-1]["label"] if options else None,
        outcomeLabel=f"Total reward: {run.total_reward}",
        disclosureEvents=disclosure_events,
        notes=f"Seed: {run.environment_seed}, Mode: {run.run_mode}",
    )


# ── Sprint 4: Derived Theatres ───────────────────────────────────────────────

@packs_router.get(
    "/{pack_id}/derived-theatres",
    response_model=list[DerivedTheatreResponse],
)
async def get_derived_theatres(
    pack_id: str,
    user: TokenData = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """Get theatres derived from this pack's checkpoint resolutions."""
    pack_result = await session.execute(
        select(ScenarioPack).where(ScenarioPack.id == pack_id)
    )
    pack = pack_result.scalar_one_or_none()
    if not pack:
        raise HTTPException(status_code=404, detail="Pack not found")
    if pack.user_id != user.user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Scope through RunCheckpointResult → ScenarioRun to ensure theatres
    # belong to runs of THIS pack, not just any pack sharing the same template.
    spawned_theatre_ids = (await session.execute(
        select(RunCheckpointResult.spawned_theatre_id)
        .join(ScenarioRun, RunCheckpointResult.run_id == ScenarioRun.id)
        .where(
            ScenarioRun.pack_id == pack_id,
            RunCheckpointResult.spawned_theatre_id.isnot(None),
        )
    )).scalars().all()

    if not spawned_theatre_ids:
        return []

    theatres = (await session.execute(
        select(Theatre)
        .where(Theatre.id.in_(spawned_theatre_ids))
        .order_by(Theatre.created_at)
    )).scalars().all()

    return [
        DerivedTheatreResponse(
            id=t.id,
            construct_id=t.construct_id,
            state=t.state,
            spawned_from_checkpoint_id=t.spawned_from_checkpoint_id,
            certificate_id=t.certificate_id,
            created_at=t.created_at,
        )
        for t in theatres
    ]
