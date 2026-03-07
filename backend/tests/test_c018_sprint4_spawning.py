"""Cycle-018 Sprint 4 — Derived Theatre Spawning tests.

6 tests:
1. Checkpoint with can_spawn_theatre=True → Theatre created with provenance
2. Checkpoint with can_spawn_theatre=False → no theatre spawned
3. Spawned theatre has correct construct_id (including run_id) and spawned_from_checkpoint_id
4. Spawned theatre follows normal lifecycle (created in DRAFT)
5. Pack with 2 spawning checkpoints → 2 derived theatres
6. Audit trail shows THEATRE_SPAWNED events with correct detail
"""

import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from backend.database.models import (
    ScenarioPackTemplate,
    ScenarioCheckpoint,
    CheckpointBranch,
    ScenarioPack,
    ScenarioRun,
    RunCheckpointResult,
    ScenarioPackAuditEvent,
    Theatre,
    TheatreTemplate,
    TheatreCertificate,
    User,
)
from backend.services.theatre_spawner import spawn_theatre, _ensure_spawned_template
from backend.services.checkpoint_evaluator import evaluate_checkpoints


# ── Fixtures ──

def _create_tables(eng):
    tables = [
        User.__table__,
        TheatreTemplate.__table__,
        TheatreCertificate.__table__,
        Theatre.__table__,
        ScenarioPackTemplate.__table__,
        ScenarioCheckpoint.__table__,
        CheckpointBranch.__table__,
        ScenarioPack.__table__,
        ScenarioRun.__table__,
        RunCheckpointResult.__table__,
        ScenarioPackAuditEvent.__table__,
    ]
    with eng.connect() as conn:
        for table in tables:
            table.create(conn, checkfirst=True)
        conn.commit()


def _create_template_with_spawning(session, template_id="spawn_template", spawn_flags=None):
    """Create a template with checkpoints, some with can_spawn_theatre=True."""
    if spawn_flags is None:
        spawn_flags = [True, False, True]  # 3 checkpoints, 1st and 3rd spawn

    now = datetime.now(timezone.utc)
    template = ScenarioPackTemplate(
        id=template_id,
        name="Spawn Test Template",
        family="TEST",
        template_status="RUNNABLE",
        is_seeded=True,
        objective_vector_json=[{"component": "test", "weight": 1.0, "description": "Test"}],
        created_at=now,
    )
    session.add(template)
    session.flush()

    checkpoints = []
    for seq, can_spawn in enumerate(spawn_flags, start=1):
        cp = ScenarioCheckpoint(
            id=f"{template_id}_cp_{seq}",
            template_id=template_id,
            sequence_num=seq,
            trigger=f"trigger_{seq}",
            market_question=f"Should we proceed at checkpoint {seq}?",
            decision_window_sec=30,
            can_spawn_theatre=can_spawn,
            evaluator_type="BINARY_RISK_GATE",
            reward_mapping_json={"base_reward": 1.0},
            created_at=now,
        )
        session.add(cp)
        checkpoints.append(cp)

    session.flush()

    # Link: each checkpoint branches to the next
    for seq in range(1, len(spawn_flags) + 1):
        next_cp_id = f"{template_id}_cp_{seq + 1}" if seq < len(spawn_flags) else None
        for opt_idx in range(2):
            branch = CheckpointBranch(
                id=f"{template_id}_cp_{seq}_br_{opt_idx}",
                checkpoint_id=f"{template_id}_cp_{seq}",
                label=f"Option {opt_idx}",
                outcome_type="continue",
                next_checkpoint_id=next_cp_id,
                reward_mapping_json={"base_reward": 1.0},
            )
            session.add(branch)

    session.flush()
    return template, checkpoints


def _create_pack_and_run(session, template_id="spawn_template"):
    now = datetime.now(timezone.utc)
    pack = ScenarioPack(
        id=str(uuid.uuid4()),
        user_id="test-user",
        template_id=template_id,
        state="ACTIVE",
        run_mode="TRAINING",
        agent_assignment="auto_assign",
        simulation_scale="single_1x",
        objective_profile="pack_default",
        created_at=now,
        updated_at=now,
    )
    session.add(pack)

    run = ScenarioRun(
        id=str(uuid.uuid4()),
        pack_id=pack.id,
        status="PENDING",
        run_mode="TRAINING",
        current_checkpoint_seq=0,
        created_at=now,
    )
    session.add(run)
    session.flush()
    return pack, run


@pytest.fixture
def engine():
    eng = create_engine("sqlite:///:memory:")
    _create_tables(eng)
    return eng


@pytest.fixture
def session(engine):
    with Session(engine) as s:
        yield s


# ── Test 1: can_spawn_theatre=True creates Theatre ──

def test_spawn_theatre_creates_with_provenance(session):
    """Checkpoint with can_spawn_theatre=True creates Theatre with provenance."""
    template, checkpoints = _create_template_with_spawning(session, spawn_flags=[True])
    pack, run = _create_pack_and_run(session)

    # Create a checkpoint result manually
    result = RunCheckpointResult(
        id=str(uuid.uuid4()),
        run_id=run.id,
        checkpoint_id=checkpoints[0].id,
        selected_branch_id=f"spawn_template_cp_1_br_0",
        reward=1.0,
        resolved_at=datetime.now(timezone.utc),
    )
    session.add(result)
    session.flush()

    theatre = spawn_theatre(session, checkpoints[0], pack, run, result)
    session.commit()

    assert theatre is not None
    assert theatre.spawned_from_checkpoint_id == checkpoints[0].id
    assert theatre.state == "DRAFT"
    assert result.spawned_theatre_id == theatre.id


# ── Test 2: can_spawn_theatre=False → no spawn ──

def test_no_spawn_when_disabled(session):
    """Checkpoint with can_spawn_theatre=False does not spawn theatre."""
    template, checkpoints = _create_template_with_spawning(session, spawn_flags=[False])
    pack, run = _create_pack_and_run(session)

    result = RunCheckpointResult(
        id=str(uuid.uuid4()),
        run_id=run.id,
        checkpoint_id=checkpoints[0].id,
        selected_branch_id=f"spawn_template_cp_1_br_0",
        reward=1.0,
        resolved_at=datetime.now(timezone.utc),
    )
    session.add(result)
    session.flush()

    theatre = spawn_theatre(session, checkpoints[0], pack, run, result)
    session.commit()

    assert theatre is None
    assert result.spawned_theatre_id is None


# ── Test 3: construct_id includes run_id ──

def test_construct_id_includes_run_id(session):
    """Spawned theatre construct_id has format scenario_{pack_id}_run_{run_id}_cp_{checkpoint_id}."""
    template, checkpoints = _create_template_with_spawning(session, "cid_template", [True])
    pack, run = _create_pack_and_run(session, "cid_template")

    result = RunCheckpointResult(
        id=str(uuid.uuid4()),
        run_id=run.id,
        checkpoint_id=checkpoints[0].id,
        selected_branch_id=f"cid_template_cp_1_br_0",
        reward=1.0,
        resolved_at=datetime.now(timezone.utc),
    )
    session.add(result)
    session.flush()

    theatre = spawn_theatre(session, checkpoints[0], pack, run, result)
    session.commit()

    expected = f"scenario_{pack.id}_run_{run.id}_cp_{checkpoints[0].id}"
    assert theatre.construct_id == expected
    assert theatre.spawned_from_checkpoint_id == checkpoints[0].id


# ── Test 4: Spawned theatre in DRAFT state (normal lifecycle) ──

def test_spawned_theatre_draft_state(session):
    """Spawned theatre is created in DRAFT state for normal lifecycle."""
    template, checkpoints = _create_template_with_spawning(session, "lc_template", [True])
    pack, run = _create_pack_and_run(session, "lc_template")

    result = RunCheckpointResult(
        id=str(uuid.uuid4()),
        run_id=run.id,
        checkpoint_id=checkpoints[0].id,
        selected_branch_id=f"lc_template_cp_1_br_0",
        reward=1.0,
        resolved_at=datetime.now(timezone.utc),
    )
    session.add(result)
    session.flush()

    theatre = spawn_theatre(session, checkpoints[0], pack, run, result)
    session.commit()

    assert theatre.state == "DRAFT"
    assert theatre.user_id == pack.user_id
    assert theatre.template_id == "scenario_derived"


# ── Test 5: Evaluator spawns theatres for spawning checkpoints ──

def test_evaluator_spawns_two_theatres(session):
    """Pack with 2 spawning checkpoints produces 2 derived theatres via evaluator."""
    _create_template_with_spawning(session, "two_spawn", [True, False, True])
    pack, run = _create_pack_and_run(session, "two_spawn")

    evaluate_checkpoints(session, run, seed=42)
    session.commit()

    # Query spawned theatres
    theatres = session.execute(
        select(Theatre).where(Theatre.spawned_from_checkpoint_id.isnot(None))
    ).scalars().all()

    assert len(theatres) == 2

    # Verify they're from checkpoints 1 and 3
    cp_ids = {t.spawned_from_checkpoint_id for t in theatres}
    assert "two_spawn_cp_1" in cp_ids
    assert "two_spawn_cp_3" in cp_ids

    # Verify results have spawned_theatre_id set
    results = session.execute(
        select(RunCheckpointResult).where(RunCheckpointResult.run_id == run.id)
    ).scalars().all()

    spawned_results = [r for r in results if r.spawned_theatre_id is not None]
    assert len(spawned_results) == 2


# ── Test 6: THEATRE_SPAWNED audit events ──

def test_theatre_spawned_audit_events(session):
    """Audit trail shows THEATRE_SPAWNED events with correct detail."""
    _create_template_with_spawning(session, "audit_spawn", [True])
    pack, run = _create_pack_and_run(session, "audit_spawn")

    evaluate_checkpoints(session, run, seed=42)
    session.commit()

    events = session.execute(
        select(ScenarioPackAuditEvent)
        .where(
            ScenarioPackAuditEvent.pack_id == pack.id,
            ScenarioPackAuditEvent.event_type == "THEATRE_SPAWNED",
        )
    ).scalars().all()

    assert len(events) == 1
    detail = events[0].detail_json
    assert "theatre_id" in detail
    assert detail["checkpoint_id"] == "audit_spawn_cp_1"
    assert "market_question" in detail
    assert "construct_id" in detail
    assert f"run_{run.id}" in detail["construct_id"]
