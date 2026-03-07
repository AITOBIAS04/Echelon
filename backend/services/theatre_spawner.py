"""
Theatre Spawner — Create derived theatres from checkpoint resolutions.

When a checkpoint with can_spawn_theatre=True resolves:
1. Create Theatre with spawned_from_checkpoint_id
2. Use checkpoint's market_question as the theatre inquiry
3. Generate construct_id as scenario_{pack_id}_run_{run_id}_cp_{checkpoint_id}
4. Log THEATRE_SPAWNED audit event
5. Store spawned_theatre_id on RunCheckpointResult
"""

import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from backend.database.models import (
    Theatre,
    TheatreTemplate,
    ScenarioCheckpoint,
    ScenarioPack,
    ScenarioRun,
    RunCheckpointResult,
    ScenarioPackAuditEvent,
)

logger = logging.getLogger(__name__)

# Default theatre template for spawned theatres
SPAWNED_THEATRE_TEMPLATE_ID = "scenario_derived"


def _ensure_spawned_template(session: Session) -> TheatreTemplate:
    """Ensure the scenario_derived theatre template exists."""
    template = session.get(TheatreTemplate, SPAWNED_THEATRE_TEMPLATE_ID)
    if not template:
        template = TheatreTemplate(
            id=SPAWNED_THEATRE_TEMPLATE_ID,
            template_family="SCENARIO",
            execution_path="LOCAL",
            display_name="Scenario-Derived Theatre",
            description="Theatre spawned from a scenario pack checkpoint resolution.",
            schema_version="1.0.0",
            inquiry_class="COUNTERFACTUAL",
            template_json={"source": "scenario_pack_checkpoint"},
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        session.add(template)
        session.flush()
    return template


def spawn_theatre(
    session: Session,
    checkpoint: ScenarioCheckpoint,
    pack: ScenarioPack,
    run: ScenarioRun,
    result: RunCheckpointResult,
) -> Theatre | None:
    """Spawn a derived theatre from a checkpoint resolution.

    Only spawns if checkpoint.can_spawn_theatre is True.

    Returns the created Theatre or None if not spawnable.
    """
    if not checkpoint.can_spawn_theatre:
        return None

    # Ensure template exists
    template = _ensure_spawned_template(session)

    now = datetime.now(timezone.utc)
    construct_id = f"scenario_{pack.id}_run_{run.id}_cp_{checkpoint.id}"

    theatre = Theatre(
        id=str(uuid.uuid4()),
        user_id=pack.user_id,
        template_id=template.id,
        state="DRAFT",
        construct_id=construct_id,
        inquiry_class="COUNTERFACTUAL",
        spawned_from_checkpoint_id=checkpoint.id,
        created_at=now,
        updated_at=now,
    )
    session.add(theatre)

    # Store on checkpoint result
    result.spawned_theatre_id = theatre.id

    # Audit event
    audit = ScenarioPackAuditEvent(
        id=str(uuid.uuid4()),
        pack_id=pack.id,
        event_type="THEATRE_SPAWNED",
        detail_json={
            "theatre_id": theatre.id,
            "checkpoint_id": checkpoint.id,
            "market_question": checkpoint.market_question,
            "construct_id": construct_id,
        },
        created_at=now,
    )
    session.add(audit)

    session.flush()
    logger.info(
        "Spawned theatre %s from checkpoint %s (pack %s, run %s)",
        theatre.id, checkpoint.id, pack.id, run.id,
    )

    return theatre
