"""Cycle-018 Sprint 5 — RLMF Telemetry + WebSocket + E2E tests.

5 tests:
1. Completed run → RLMF export record has correct shape and all fields
2. WebSocket manager has 3 new broadcast methods callable
3. Branch map data structure matches frontend expectations
4. Run status + checkpoint results render data correct
5. E2E: create pack → commit → run → checkpoints → spawn → RLMF export
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
from backend.services.checkpoint_evaluator import (
    evaluate_checkpoints,
    build_episode_tree,
    build_replay_output,
)
from backend.services.scenario_telemetry_exporter import export_run_telemetry
from backend.websockets.realtime_manager import ConnectionManager


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


def _create_template_with_spawning(session, template_id="e2e_template", spawn_flags=None):
    """Create a RUNNABLE template with checkpoints and branches."""
    if spawn_flags is None:
        spawn_flags = [True, False, True]

    now = datetime.now(timezone.utc)
    template = ScenarioPackTemplate(
        id=template_id,
        name="E2E Test Template",
        family="TEST",
        template_status="RUNNABLE",
        is_seeded=True,
        objective_vector_json=[
            {"component": "speed", "weight": 0.6, "description": "Speed"},
            {"component": "safety", "weight": 0.4, "description": "Safety"},
        ],
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
            market_question=f"E2E checkpoint {seq}?",
            decision_window_sec=30,
            can_spawn_theatre=can_spawn,
            evaluator_type="BINARY_RISK_GATE",
            reward_mapping_json={"base_reward": 1.0},
            created_at=now,
        )
        session.add(cp)
        checkpoints.append(cp)

    session.flush()

    for seq in range(1, len(spawn_flags) + 1):
        next_cp_id = f"{template_id}_cp_{seq + 1}" if seq < len(spawn_flags) else None
        for opt_idx in range(2):
            branch = CheckpointBranch(
                id=f"{template_id}_cp_{seq}_br_{opt_idx}",
                checkpoint_id=f"{template_id}_cp_{seq}",
                label=f"Option {opt_idx}",
                outcome_type="continue",
                next_checkpoint_id=next_cp_id,
                reward_mapping_json={"base_reward": 1.0 + opt_idx * 0.5},
            )
            session.add(branch)

    session.flush()
    return template, checkpoints


def _create_pack_and_run(session, template_id="e2e_template"):
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


# ── Test 1: RLMF Telemetry Export ──

def test_telemetry_export_shape(session):
    """Completed run → export record has correct RLMF shape and all fields."""
    _create_template_with_spawning(session, "telem_template", [True, False])
    pack, run = _create_pack_and_run(session, "telem_template")

    evaluate_checkpoints(session, run, seed=42)
    session.commit()

    export = export_run_telemetry(session, run)

    # Verify all required RLMF fields
    assert export["episode_id"] == run.id
    assert export["scenario_pack_id"] == run.pack_id
    assert export["template_id"] == pack.template_id
    assert export["template_name"] == "E2E Test Template"
    assert export["run_mode"] == "TRAINING"
    assert export["status"] == "COMPLETED"
    assert export["fork_count"] == 2  # 2 checkpoints

    # Actions list matches checkpoint count
    assert len(export["actions"]) == 2
    for action in export["actions"]:
        assert "checkpoint_id" in action
        assert "selected_branch_id" in action
        assert "evaluator_type" in action

    # Rewards list matches checkpoint count
    assert len(export["rewards"]) == 2

    # Branch path
    assert len(export["branch_path"]) == 2

    # State features populated
    assert len(export["state_features"]) > 0

    # Timestamps present
    assert export["started_at"] is not None
    assert export["completed_at"] is not None

    # Total reward matches run
    assert export["total_reward"] == run.total_reward

    # Spawned theatres (first checkpoint spawns)
    assert len(export["spawned_theatre_ids"]) >= 1


# ── Test 2: WebSocket broadcast methods exist ──

def test_websocket_broadcast_methods():
    """ConnectionManager has 3 new scenario broadcast methods."""
    mgr = ConnectionManager()

    # Verify methods exist and are callable
    assert hasattr(mgr, "broadcast_scenario_run_status")
    assert hasattr(mgr, "broadcast_checkpoint_resolved")
    assert hasattr(mgr, "broadcast_theatre_spawned")

    # Verify they are coroutine functions
    import asyncio
    assert asyncio.iscoroutinefunction(mgr.broadcast_scenario_run_status)
    assert asyncio.iscoroutinefunction(mgr.broadcast_checkpoint_resolved)
    assert asyncio.iscoroutinefunction(mgr.broadcast_theatre_spawned)


# ── Test 3: Branch map data structure ──

def test_branch_map_data_structure(session):
    """Episode tree nodes have all fields needed for frontend BranchMap component."""
    _create_template_with_spawning(session, "brmap_template", [True, False, True])
    pack, run = _create_pack_and_run(session, "brmap_template")

    evaluate_checkpoints(session, run, seed=42)
    session.commit()

    nodes = build_episode_tree(session, run)

    assert len(nodes) == 3

    # Verify each node has all fields the BranchMap component needs
    required_fields = {
        "checkpoint_id", "sequence_num", "trigger",
        "market_question", "selected_branch", "outcome_type",
        "reward", "spawned_theatre_id",
    }
    for node in nodes:
        assert required_fields.issubset(node.keys()), f"Missing fields: {required_fields - node.keys()}"

    # Nodes with can_spawn_theatre=True should have spawned_theatre_id set
    assert nodes[0]["spawned_theatre_id"] is not None  # cp_1 spawns
    assert nodes[1]["spawned_theatre_id"] is None       # cp_2 doesn't
    assert nodes[2]["spawned_theatre_id"] is not None   # cp_3 spawns


# ── Test 4: Run status data correctness ──

def test_run_status_checkpoint_results(session):
    """Run status + checkpoint results are correct for frontend display."""
    _create_template_with_spawning(session, "status_template", [False, False])
    pack, run = _create_pack_and_run(session, "status_template")

    evaluate_checkpoints(session, run, seed=99)
    session.commit()

    # Run should be COMPLETED
    assert run.status == "COMPLETED"
    assert run.completed_at is not None
    assert run.total_reward > 0

    # Query results for display
    results = session.execute(
        select(RunCheckpointResult)
        .where(RunCheckpointResult.run_id == run.id)
        .order_by(RunCheckpointResult.resolved_at)
    ).scalars().all()

    assert len(results) == 2

    for result in results:
        assert result.reward is not None
        assert result.selected_branch_id is not None
        assert result.resolved_at is not None

    # Derived theatres — none expected (both can_spawn_theatre=False)
    theatres = session.execute(
        select(Theatre).where(Theatre.spawned_from_checkpoint_id.isnot(None))
    ).scalars().all()
    # Filter to this template's checkpoints
    template_cp_ids = {f"status_template_cp_{i}" for i in range(1, 3)}
    derived = [t for t in theatres if t.spawned_from_checkpoint_id in template_cp_ids]
    assert len(derived) == 0


# ── Test 5: E2E Full Lifecycle ──

def test_e2e_full_scenario_pack_lifecycle(session):
    """E2E: template → pack → run → checkpoints → spawn → RLMF export."""
    # 1. Create template with 3 checkpoints (1st and 3rd spawn theatres)
    template, checkpoints = _create_template_with_spawning(
        session, "e2e_full", [True, False, True]
    )

    # 2. Create pack in DRAFT
    now = datetime.now(timezone.utc)
    pack = ScenarioPack(
        id=str(uuid.uuid4()),
        user_id="test-user",
        template_id="e2e_full",
        state="DRAFT",
        run_mode="TRAINING",
        agent_assignment="auto_assign",
        simulation_scale="single_1x",
        objective_profile="pack_default",
        created_at=now,
        updated_at=now,
    )
    session.add(pack)
    session.flush()

    # 3. Commit pack
    import hashlib
    pack.state = "COMMITTED"
    pack.commitment_hash = hashlib.sha256(
        f"{pack.template_id}|{pack.run_mode}|{pack.created_at.isoformat()}".encode()
    ).hexdigest()
    pack.committed_at = now

    # 4. Launch run
    pack.state = "ACTIVE"
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

    # 5. Evaluate checkpoints
    results = evaluate_checkpoints(session, run, seed=42)
    session.commit()

    # Verify: 3 checkpoint results
    assert len(results) == 3
    assert run.status == "COMPLETED"

    # 6. Verify theatres spawned (checkpoints 1 and 3)
    theatres = session.execute(
        select(Theatre).where(Theatre.spawned_from_checkpoint_id.isnot(None))
    ).scalars().all()

    e2e_theatres = [t for t in theatres if t.spawned_from_checkpoint_id.startswith("e2e_full")]
    assert len(e2e_theatres) == 2

    for theatre in e2e_theatres:
        assert theatre.state == "DRAFT"
        assert theatre.user_id == "test-user"
        assert f"run_{run.id}" in theatre.construct_id

    # 7. Verify RLMF export
    export = export_run_telemetry(session, run)
    assert export["episode_id"] == run.id
    assert export["scenario_pack_id"] == pack.id
    assert export["template_id"] == "e2e_full"
    assert len(export["actions"]) == 3
    assert len(export["rewards"]) == 3
    assert len(export["branch_path"]) == 3
    assert len(export["spawned_theatre_ids"]) == 2
    assert export["status"] == "COMPLETED"
    assert export["total_reward"] == run.total_reward

    # 8. Verify audit trail
    events = session.execute(
        select(ScenarioPackAuditEvent)
        .where(ScenarioPackAuditEvent.pack_id == pack.id)
    ).scalars().all()
    spawn_events = [e for e in events if e.event_type == "THEATRE_SPAWNED"]
    assert len(spawn_events) == 2

    # 9. Verify replay output
    replay = build_replay_output(session, run)
    assert len(replay["disclosureEvents"]) == 3
    assert replay["settledAt"] is not None
