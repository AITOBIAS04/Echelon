"""Cycle-018 Sprint 3 — Checkpoint Resolution + Branching tests.

9 tests:
1. Seed manager: each run_mode produces correct seed behaviour
2. Sequential evaluation through 3 checkpoints → 3 results in order
3. Branch selection deterministic given (agent action, seed, evaluator type)
4. Reward computation from objective vector weights
5. Run completes when no more checkpoints → status COMPLETED
6. Branch probabilities sum to 1.0 per checkpoint after runs
7. Branch probabilities null with zero runs
8. Episode tree has correct node structure
9. Replay output includes checkpoint decisions as disclosure events
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
    User,
    TheatreTemplate,
    TheatreCertificate,
    Theatre,
)
from backend.services.scenario_seed_manager import (
    allocate_seed,
    CALIBRATION_SEEDS,
    EVALUATION_SEEDS,
)
from backend.services.checkpoint_evaluator import (
    evaluate_checkpoints,
    compute_branch_probabilities,
    build_episode_tree,
    build_replay_output,
)


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


def _create_test_template_with_checkpoints(session, template_id="test_template", num_checkpoints=3):
    """Create a RUNNABLE template with linked checkpoints and branches."""
    now = datetime.now(timezone.utc)

    template = ScenarioPackTemplate(
        id=template_id,
        name="Test Template",
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
    for seq in range(1, num_checkpoints + 1):
        cp = ScenarioCheckpoint(
            id=f"{template_id}_cp_{seq}",
            template_id=template_id,
            sequence_num=seq,
            trigger=f"trigger_{seq}",
            market_question=f"Question at checkpoint {seq}?",
            decision_window_sec=30,
            can_spawn_theatre=False,
            evaluator_type="BINARY_RISK_GATE",
            reward_mapping_json={"base_reward": 1.0},
            created_at=now,
        )
        session.add(cp)
        checkpoints.append(cp)

    session.flush()

    # Link checkpoints: branch 0 of cp_N → cp_N+1
    for seq in range(1, num_checkpoints + 1):
        cp = checkpoints[seq - 1]
        next_cp_id = f"{template_id}_cp_{seq + 1}" if seq < num_checkpoints else None

        for opt_idx in range(2):
            branch = CheckpointBranch(
                id=f"{template_id}_cp_{seq}_br_{opt_idx}",
                checkpoint_id=cp.id,
                label=f"Option {opt_idx}",
                outcome_type="continue",
                next_checkpoint_id=next_cp_id,
                reward_mapping_json={"base_reward": 1.0 + opt_idx * 0.5},
            )
            session.add(branch)

    session.flush()
    return template


def _create_pack_and_run(session, template_id="test_template"):
    """Create a pack and run ready for evaluation."""
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


# ── Test 1: Seed manager ──

def test_seed_manager_modes(session):
    """Each run_mode produces correct seed behaviour."""
    # TRAINING: random, varies across calls
    seeds = {allocate_seed("TRAINING") for _ in range(10)}
    assert len(seeds) > 1, "TRAINING should produce varying seeds"

    # CALIBRATION: deterministic canonical set
    for i in range(5):
        assert allocate_seed("CALIBRATION", run_index=i) == CALIBRATION_SEEDS[i]

    # CALIBRATION wraps around
    assert allocate_seed("CALIBRATION", run_index=5) == CALIBRATION_SEEDS[0]

    # EVALUATION: deterministic from evaluation pool
    for i in range(3):
        assert allocate_seed("EVALUATION", run_index=i) == EVALUATION_SEEDS[i]

    # REPLAY: reuses stored seed
    assert allocate_seed("REPLAY", replay_seed=999) == 999

    # REPLAY without seed raises
    with pytest.raises(ValueError, match="replay_seed"):
        allocate_seed("REPLAY")


# ── Test 2: Sequential evaluation ──

def test_sequential_evaluation_three_checkpoints(session):
    """Sequential evaluation through 3 checkpoints produces 3 results in order."""
    _create_test_template_with_checkpoints(session, num_checkpoints=3)
    pack, run = _create_pack_and_run(session)

    results = evaluate_checkpoints(session, run, seed=42)
    session.commit()

    assert len(results) == 3
    # Check sequence order
    for i, result in enumerate(results):
        assert result.checkpoint_id == f"test_template_cp_{i + 1}"


# ── Test 3: Deterministic branch selection ──

def test_branch_selection_deterministic(session):
    """Branch selection is deterministic given same inputs."""
    _create_test_template_with_checkpoints(session, "det_template", num_checkpoints=1)
    pack1, run1 = _create_pack_and_run(session, "det_template")
    pack2, run2 = _create_pack_and_run(session, "det_template")

    results1 = evaluate_checkpoints(session, run1, seed=42, agent_actions={"det_template_cp_1": "go_left"})
    results2 = evaluate_checkpoints(session, run2, seed=42, agent_actions={"det_template_cp_1": "go_left"})
    session.commit()

    assert len(results1) == 1
    assert len(results2) == 1
    assert results1[0].selected_branch_id == results2[0].selected_branch_id

    # Different seed or action → potentially different branch
    pack3, run3 = _create_pack_and_run(session, "det_template")
    results3 = evaluate_checkpoints(session, run3, seed=9999, agent_actions={"det_template_cp_1": "go_right"})
    session.commit()

    # At minimum, the mechanism is deterministic (same inputs → same output)
    pack4, run4 = _create_pack_and_run(session, "det_template")
    results4 = evaluate_checkpoints(session, run4, seed=9999, agent_actions={"det_template_cp_1": "go_right"})
    session.commit()

    assert results3[0].selected_branch_id == results4[0].selected_branch_id


# ── Test 4: Reward computation ──

def test_reward_computation_with_objective_vector(session):
    """Rewards computed from objective vector weights and reward mapping."""
    _create_test_template_with_checkpoints(session, "reward_template", num_checkpoints=1)
    pack, run = _create_pack_and_run(session, "reward_template")

    results = evaluate_checkpoints(session, run, seed=42)
    session.commit()

    assert len(results) == 1
    # Reward should be base_reward * total_weight (0.6 + 0.4 = 1.0)
    # base_reward depends on which branch was selected (1.0 or 1.5)
    assert results[0].reward > 0
    assert run.total_reward > 0


# ── Test 5: Run completes ──

def test_run_completes_status(session):
    """Run status transitions to COMPLETED when all checkpoints resolved."""
    _create_test_template_with_checkpoints(session, "complete_template", num_checkpoints=2)
    pack, run = _create_pack_and_run(session, "complete_template")

    evaluate_checkpoints(session, run, seed=42)
    session.commit()

    assert run.status == "COMPLETED"
    assert run.completed_at is not None
    assert run.started_at is not None
    assert run.environment_seed == 42


# ── Test 6: Branch probabilities sum to 1.0 ──

def test_branch_probabilities_sum_to_one(session):
    """After multiple runs, branch probabilities sum to 1.0 per checkpoint."""
    _create_test_template_with_checkpoints(session, "prob_template", num_checkpoints=2)

    # Run 10 evaluations with different seeds
    for i in range(10):
        pack, run = _create_pack_and_run(session, "prob_template")
        evaluate_checkpoints(session, run, seed=i * 100)

    session.commit()

    probs = compute_branch_probabilities(session, "prob_template")

    for cp_id, branch_probs in probs.items():
        if branch_probs is not None:
            total = sum(branch_probs.values())
            assert abs(total - 1.0) < 0.001, f"Probabilities for {cp_id} sum to {total}"


def test_branch_probabilities_exclude_replay_runs(session):
    """Replay copies must not count as fresh observations in branch analytics."""
    _create_test_template_with_checkpoints(session, "prob_replay_template", num_checkpoints=1)
    now = datetime.now(timezone.utc)

    cp_id = "prob_replay_template_cp_1"
    branch_a = "prob_replay_template_cp_1_br_0"
    branch_b = "prob_replay_template_cp_1_br_1"

    training_pack_a = ScenarioPack(
        id=str(uuid.uuid4()),
        user_id="test-user",
        template_id="prob_replay_template",
        state="ACTIVE",
        run_mode="TRAINING",
        created_at=now,
        updated_at=now,
    )
    training_pack_b = ScenarioPack(
        id=str(uuid.uuid4()),
        user_id="test-user",
        template_id="prob_replay_template",
        state="ACTIVE",
        run_mode="TRAINING",
        created_at=now,
        updated_at=now,
    )
    replay_pack = ScenarioPack(
        id=str(uuid.uuid4()),
        user_id="test-user",
        template_id="prob_replay_template",
        state="ACTIVE",
        run_mode="REPLAY",
        created_at=now,
        updated_at=now,
    )
    session.add_all([training_pack_a, training_pack_b, replay_pack])
    session.flush()

    training_run_a = ScenarioRun(
        id=str(uuid.uuid4()),
        pack_id=training_pack_a.id,
        status="COMPLETED",
        run_mode="TRAINING",
        created_at=now,
    )
    training_run_b = ScenarioRun(
        id=str(uuid.uuid4()),
        pack_id=training_pack_b.id,
        status="COMPLETED",
        run_mode="TRAINING",
        created_at=now,
    )
    replay_run = ScenarioRun(
        id=str(uuid.uuid4()),
        pack_id=replay_pack.id,
        status="COMPLETED",
        run_mode="REPLAY",
        created_at=now,
    )
    session.add_all([training_run_a, training_run_b, replay_run])
    session.flush()

    session.add_all([
        RunCheckpointResult(
            id=str(uuid.uuid4()),
            run_id=training_run_a.id,
            checkpoint_id=cp_id,
            selected_branch_id=branch_a,
            reward=1.0,
            state_vector_json={},
            resolved_at=now,
        ),
        RunCheckpointResult(
            id=str(uuid.uuid4()),
            run_id=training_run_b.id,
            checkpoint_id=cp_id,
            selected_branch_id=branch_b,
            reward=1.0,
            state_vector_json={},
            resolved_at=now,
        ),
        RunCheckpointResult(
            id=str(uuid.uuid4()),
            run_id=replay_run.id,
            checkpoint_id=cp_id,
            selected_branch_id=branch_a,
            reward=1.0,
            state_vector_json={"replay_source_run_id": training_run_a.id},
            resolved_at=now,
        ),
    ])
    session.commit()

    probs = compute_branch_probabilities(session, "prob_replay_template")

    assert probs[cp_id] == {
        branch_a: 0.5,
        branch_b: 0.5,
    }


# ── Test 7: Branch probabilities null with zero runs ──

def test_branch_probabilities_null_no_runs(session):
    """With zero runs, all probabilities are null."""
    _create_test_template_with_checkpoints(session, "empty_template", num_checkpoints=2)
    session.commit()

    probs = compute_branch_probabilities(session, "empty_template")

    for cp_id, branch_probs in probs.items():
        assert branch_probs is None


# ── Test 8: Episode tree structure ──

def test_episode_tree_structure(session):
    """Completed run produces tree with correct node structure and rewards."""
    _create_test_template_with_checkpoints(session, "tree_template", num_checkpoints=3)
    pack, run = _create_pack_and_run(session, "tree_template")

    evaluate_checkpoints(session, run, seed=42)
    session.commit()

    nodes = build_episode_tree(session, run)

    assert len(nodes) == 3
    for i, node in enumerate(nodes):
        assert node["checkpoint_id"] == f"tree_template_cp_{i + 1}"
        assert node["sequence_num"] == i + 1
        assert node["trigger"] == f"trigger_{i + 1}"
        assert node["selected_branch"] is not None
        assert node["reward"] is not None


# ── Test 9: Replay output ──

def test_replay_output_disclosure_events(session):
    """Replay output includes checkpoint decisions as disclosure events."""
    _create_test_template_with_checkpoints(session, "replay_template", num_checkpoints=3)
    pack, run = _create_pack_and_run(session, "replay_template")

    evaluate_checkpoints(session, run, seed=42)
    session.commit()

    replay = build_replay_output(session, run)

    assert replay["timelineId"] == f"scenario_{pack.id}"
    assert replay["forkId"] == run.id
    assert replay["forkQuestion"] == "Test Template"
    assert len(replay["disclosureEvents"]) == 3
    assert len(replay["options"]) == 3

    # Verify disclosure events are evidence_flip type
    for event in replay["disclosureEvents"]:
        assert event["type"] == "evidence_flip"
        assert "Checkpoint" in event["label"]

    # Verify options have price paths
    for option in replay["options"]:
        assert len(option["pricePath"]) == 2
        assert option["label"] is not None

    assert replay["settledAt"] is not None
    assert "Seed: 42" in replay["notes"]
