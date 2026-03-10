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
from typing import Optional

from sqlalchemy import func, select
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
    config_json: Optional[dict] = None,
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

    now = datetime.utcnow()
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

    now = datetime.utcnow()
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

    Two execution paths:

    REPLAY mode:
    1. Require config_json.replay_source_run_id
    2. Copy persisted RunCheckpointResults from source run (no fresh evaluation)
    3. Source run must be COMPLETED with results

    All other modes (TRAINING, EVALUATION, CALIBRATION):
    1. Validate runnable checkpoint configs before mutating state
    2. Allocate seed via scenario_seed_manager
    3. Create ScenarioRun with seed
    4. Transition pack to ACTIVE
    5. Evaluate checkpoints via checkpoint_evaluator (sync, run inside run_sync)
    6. Emit CHECKPOINT_RESOLVED / THEATRE_SPAWNED WS events
    """
    if pack.state != "COMMITTED":
        raise ValueError(f"Cannot launch run for pack in state '{pack.state}'. Must be COMMITTED.")

    from backend.services.checkpoint_evaluator import (
        evaluate_checkpoints,
        replay_recorded_path,
        validate_template_checkpoints,
    )
    from backend.services.scenario_seed_manager import allocate_seed

    # REPLAY mode: exact recorded-path replay from a source run
    if pack.run_mode == "REPLAY":
        source_run_id = (pack.config_json or {}).get("replay_source_run_id")
        if not source_run_id:
            raise ValueError(
                "REPLAY mode requires config_json.replay_source_run_id "
                "identifying the completed run to replay."
            )

        now = datetime.utcnow()
        pack.state = "ACTIVE"
        pack.updated_at = now

        run = ScenarioRun(
            id=str(uuid.uuid4()),
            pack_id=pack.id,
            status="PENDING",
            run_mode="REPLAY",
            source_run_id=source_run_id,
            current_checkpoint_seq=0,
            created_at=now,
        )
        session.add(run)

        audit = ScenarioPackAuditEvent(
            id=str(uuid.uuid4()),
            pack_id=pack.id,
            event_type="PACK_RUN_STARTED",
            detail_json={"run_id": run.id, "source_run_id": source_run_id, "mode": "REPLAY"},
            created_at=now,
        )
        session.add(audit)
        await session.flush()

        def _replay(sync_session):
            sync_run = sync_session.get(ScenarioRun, run.id)
            if sync_run:
                replay_recorded_path(sync_session, sync_run, source_run_id)

        await session.run_sync(_replay)

        logger.info(
            "Launched REPLAY run %s for pack %s (source_run=%s)",
            run.id, pack.id, source_run_id,
        )
        return run

    # Non-REPLAY modes: validate, allocate seed, evaluate fresh
    validation_errors = await session.run_sync(
        lambda sync_session: validate_template_checkpoints(sync_session, pack.template_id)
    )
    if validation_errors:
        raise ValueError(
            "Template checkpoint configuration is invalid for launch: "
            + "; ".join(validation_errors)
        )

    prior_run_count = await session.scalar(
        select(func.count(ScenarioRun.id))
        .select_from(ScenarioRun)
        .join(ScenarioPack, ScenarioRun.pack_id == ScenarioPack.id)
        .where(
            ScenarioPack.user_id == pack.user_id,
            ScenarioPack.template_id == pack.template_id,
            ScenarioRun.run_mode == pack.run_mode,
        )
    )
    run_index = int(prior_run_count or 0)

    now = datetime.utcnow()
    seed = allocate_seed(pack.run_mode, run_index=run_index)

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

    ws_events: list = []

    def _evaluate(sync_session):
        sync_run = sync_session.get(ScenarioRun, run.id)
        if sync_run:
            evaluate_checkpoints(sync_session, sync_run, seed=seed, ws_events=ws_events)

    await session.run_sync(_evaluate)

    # Emit collected WS events now that we're back in async context
    if ws_events:
        try:
            from backend.websockets.realtime_manager import manager as ws_manager

            for evt in ws_events:
                evt_type = evt.pop("type")
                if evt_type == "CHECKPOINT_RESOLVED":
                    await ws_manager.broadcast_checkpoint_resolved(
                        pack_id=evt["pack_id"],
                        run_id=evt["run_id"],
                        checkpoint_id=evt["checkpoint_id"],
                        result={
                            "selected_branch_id": evt["selected_branch_id"],
                            "outcome_type": evt["outcome_type"],
                            "reward": evt["reward"],
                            "sequence_num": evt["sequence_num"],
                        },
                    )
                elif evt_type == "THEATRE_SPAWNED":
                    await ws_manager.broadcast_theatre_spawned(
                        pack_id=evt["pack_id"],
                        run_id=evt["run_id"],
                        theatre_id=evt["theatre_id"],
                        checkpoint_id=evt["checkpoint_id"],
                    )
        except Exception:
            logger.exception("Failed to emit scenario WS events for run %s", run.id)

    logger.info(
        "Launched run %s for pack %s (mode=%s, seed=%d)",
        run.id, pack.id, pack.run_mode, seed,
    )

    return run
