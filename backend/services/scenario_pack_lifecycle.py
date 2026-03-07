"""
Scenario Pack Lifecycle Service — State machine + commitment receipts.

State machine: DRAFT → COMMITTED → ACTIVE → SETTLING → RESOLVED

Valid transitions:
- DRAFT → COMMITTED: generates commitment_hash, sets committed_at
- COMMITTED → ACTIVE: on run launch (creates ScenarioRun)
- ACTIVE → SETTLING: when all checkpoints resolved (automatic)
- SETTLING → RESOLVED: when telemetry aggregated (automatic)
"""

import hashlib
import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import (
    ScenarioPack,
    ScenarioPackTemplate,
    ScenarioPackAuditEvent,
    ScenarioRun,
)

logger = logging.getLogger(__name__)

VALID_TRANSITIONS = {
    "DRAFT": ["COMMITTED"],
    "COMMITTED": ["ACTIVE"],
    "ACTIVE": ["SETTLING"],
    "SETTLING": ["RESOLVED"],
    "RESOLVED": [],
}


def _generate_commitment_hash(pack: ScenarioPack) -> str:
    """Generate a deterministic commitment hash from pack configuration."""
    data = f"{pack.template_id}|{pack.run_mode}|{pack.agent_assignment}|{pack.simulation_scale}|{pack.objective_profile}|{pack.created_at.isoformat()}"
    return hashlib.sha256(data.encode()).hexdigest()


async def create_pack(
    session: AsyncSession,
    user_id: str,
    template_id: str,
    run_mode: str = "TRAINING",
    agent_assignment: str = "auto_assign",
    simulation_scale: str = "single_1x",
    objective_profile: str = "pack_default",
    config_json: dict | None = None,
) -> ScenarioPack:
    """Create a new scenario pack from a RUNNABLE template.

    Raises ValueError if template not found or is CATALOG_ONLY.
    """
    # Verify template exists and is RUNNABLE
    result = await session.execute(
        select(ScenarioPackTemplate).where(ScenarioPackTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()

    if not template:
        raise LookupError(f"Template '{template_id}' not found")

    if template.template_status != "RUNNABLE":
        raise ValueError(
            f"Template '{template_id}' is {template.template_status}. "
            "Only RUNNABLE templates can be used to create packs."
        )

    now = datetime.now(timezone.utc)
    pack = ScenarioPack(
        id=str(uuid.uuid4()),
        user_id=user_id,
        template_id=template_id,
        state="DRAFT",
        run_mode=run_mode,
        agent_assignment=agent_assignment,
        simulation_scale=simulation_scale,
        objective_profile=objective_profile,
        config_json=config_json,
        created_at=now,
        updated_at=now,
    )
    session.add(pack)

    # Audit event
    audit = ScenarioPackAuditEvent(
        id=str(uuid.uuid4()),
        pack_id=pack.id,
        event_type="PACK_CREATED",
        detail_json={"template_id": template_id, "run_mode": run_mode},
        created_at=now,
    )
    session.add(audit)

    await session.flush()
    return pack


async def commit_pack(session: AsyncSession, pack: ScenarioPack) -> ScenarioPack:
    """Transition pack from DRAFT → COMMITTED. Generates commitment hash."""
    if pack.state != "DRAFT":
        raise ValueError(f"Cannot commit pack in state '{pack.state}'. Must be DRAFT.")

    now = datetime.now(timezone.utc)
    pack.state = "COMMITTED"
    pack.commitment_hash = _generate_commitment_hash(pack)
    pack.committed_at = now
    pack.updated_at = now

    audit = ScenarioPackAuditEvent(
        id=str(uuid.uuid4()),
        pack_id=pack.id,
        event_type="PACK_COMMITTED",
        detail_json={"commitment_hash": pack.commitment_hash},
        created_at=now,
    )
    session.add(audit)

    await session.flush()
    return pack


async def launch_run(session: AsyncSession, pack: ScenarioPack) -> ScenarioRun:
    """Launch a run from a COMMITTED pack.

    1. Allocate seed via scenario_seed_manager
    2. Create ScenarioRun with seed
    3. Transition pack to ACTIVE
    4. Evaluate checkpoints via checkpoint_evaluator (sync, run inside run_sync)
    """
    if pack.state != "COMMITTED":
        raise ValueError(f"Cannot launch run for pack in state '{pack.state}'. Must be COMMITTED.")

    from backend.services.scenario_seed_manager import allocate_seed

    now = datetime.now(timezone.utc)
    seed = allocate_seed(pack.run_mode)

    pack.state = "ACTIVE"
    pack.updated_at = now

    run = ScenarioRun(
        id=str(uuid.uuid4()),
        pack_id=pack.id,
        status="PENDING",
        run_mode=pack.run_mode,
        environment_seed=seed,
        current_checkpoint_seq=0,
        created_at=now,
    )
    session.add(run)

    audit = ScenarioPackAuditEvent(
        id=str(uuid.uuid4()),
        pack_id=pack.id,
        event_type="PACK_RUN_STARTED",
        detail_json={"run_id": run.id, "seed": seed},
        created_at=now,
    )
    session.add(audit)

    await session.flush()

    # Evaluate checkpoints synchronously via run_sync
    # evaluate_checkpoints uses sync SQLAlchemy Session internally
    from backend.services.checkpoint_evaluator import evaluate_checkpoints

    def _evaluate(sync_session):
        # Re-fetch run within sync session to avoid detached state
        from sqlalchemy import select as sync_select
        sync_run = sync_session.get(ScenarioRun, run.id)
        if sync_run:
            evaluate_checkpoints(sync_session, sync_run, seed=seed)

    await session.run_sync(_evaluate)

    logger.info(
        "Launched run %s for pack %s (mode=%s, seed=%d)",
        run.id, pack.id, pack.run_mode, seed,
    )

    return run
