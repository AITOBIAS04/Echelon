"""Cycle-020 runtime remediation tests for live run-launch behavior."""

from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from backend.database.models import (
    Base,
    CheckpointBranch,
    RunCheckpointResult,
    ScenarioCheckpoint,
    ScenarioPack,
    ScenarioPackAuditEvent,
    ScenarioPackTemplate,
    ScenarioRun,
    Theatre,
    TheatreTemplate,
    User,
)
from backend.services.scenario_pack_lifecycle import launch_run
from backend.services.scenario_seed_manager import EVALUATION_SEEDS


TABLES = [
    User.__table__,
    TheatreTemplate.__table__,
    Theatre.__table__,
    ScenarioPackTemplate.__table__,
    ScenarioCheckpoint.__table__,
    CheckpointBranch.__table__,
    ScenarioPack.__table__,
    ScenarioRun.__table__,
    RunCheckpointResult.__table__,
    ScenarioPackAuditEvent.__table__,
]


class AsyncSessionAdapter:
    """Small adapter so async lifecycle helpers can run against a sync Session."""

    def __init__(self, session: Session):
        self._session = session

    async def scalar(self, statement):
        return self._session.scalar(statement)

    def add(self, instance):
        self._session.add(instance)

    async def flush(self):
        self._session.flush()

    async def run_sync(self, fn):
        return fn(self._session)


@pytest.fixture
def session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine, tables=TABLES)
    with Session(engine) as sync_session:
        yield sync_session


async def _seed_valid_runtime_template(session: Session, template_id: str = "tpl-runtime") -> None:
    now = datetime.now(timezone.utc)
    session.add(User(id="u1", username="runtime", email="runtime@test.com", password_hash="x"))
    session.add(
        TheatreTemplate(
            id="tt-runtime",
            template_family="SCENARIO",
            execution_path="LOCAL",
            display_name="Scenario Derived",
            description="Runtime test",
            schema_version="1.0.0",
            inquiry_class="COUNTERFACTUAL",
            template_json={},
            created_at=now,
            updated_at=now,
        )
    )
    session.add(
        ScenarioPackTemplate(
            id=template_id,
            name="Runtime Template",
            family="TRAINING",
            description="Runtime Template",
            template_status="RUNNABLE",
            objective_vector_json=[{"weight": 1.0}],
            created_at=now,
        )
    )
    session.add(
        ScenarioCheckpoint(
            id="cp-runtime",
            template_id=template_id,
            sequence_num=1,
            trigger="runtime",
            trigger_condition_json={"type": "BINARY_RISK_GATE", "threshold": 0.5, "metric": "risk"},
            market_question="Runtime?",
            decision_window_sec=30,
            evaluator_type="BINARY_RISK_GATE",
            reward_mapping_json={"base_reward": 1.0},
            created_at=now,
        )
    )
    rule = {
        "type": "threshold_compare",
        "field": "action_value",
        "threshold": 0.5,
        "above_branch_index": 0,
        "below_branch_index": 1,
    }
    session.add_all(
        [
            CheckpointBranch(
                id="br-runtime-a",
                checkpoint_id="cp-runtime",
                label="a",
                outcome_type="SUCCESS",
                branch_rule_json=rule,
            ),
            CheckpointBranch(
                id="br-runtime-b",
                checkpoint_id="cp-runtime",
                label="b",
                outcome_type="FAILURE",
                branch_rule_json=rule,
            ),
        ]
    )
    session.commit()


@pytest.mark.asyncio
async def test_launch_run_fails_fast_on_invalid_checkpoint_config(session):
    async_session = AsyncSessionAdapter(session)
    now = datetime.now(timezone.utc)
    session.add(
        ScenarioPackTemplate(
            id="tpl-invalid",
            name="Invalid Runtime Template",
            family="TRAINING",
            description="Invalid Runtime Template",
            template_status="RUNNABLE",
            objective_vector_json=[{"weight": 1.0}],
            created_at=now,
        )
    )
    session.add(
        ScenarioCheckpoint(
            id="cp-invalid",
            template_id="tpl-invalid",
            sequence_num=1,
            trigger="invalid",
            trigger_condition_json={"type": "BINARY_RISK_GATE", "threshold": 0.5, "metric": "risk"},
            market_question="Invalid?",
            decision_window_sec=30,
            evaluator_type="BINARY_RISK_GATE",
            created_at=now,
        )
    )
    session.add(
        CheckpointBranch(
            id="br-invalid-a",
            checkpoint_id="cp-invalid",
            label="a",
            outcome_type="SUCCESS",
            branch_rule_json=None,
        )
    )
    pack = ScenarioPack(
        id="pack-invalid",
        user_id="u1",
        template_id="tpl-invalid",
        state="COMMITTED",
        run_mode="TRAINING",
        created_at=now,
        updated_at=now,
    )
    session.add(pack)
    session.commit()

    with pytest.raises(ValueError, match="Template checkpoint configuration is invalid"):
        await launch_run(async_session, pack)

    persisted_pack = session.get(ScenarioPack, "pack-invalid")
    run_count = session.scalar(select(func.count(ScenarioRun.id)))

    assert persisted_pack is not None
    assert persisted_pack.state == "COMMITTED"
    assert run_count == 0


@pytest.mark.asyncio
async def test_launch_run_uses_seed_policy_inputs(session):
    async_session = AsyncSessionAdapter(session)
    await _seed_valid_runtime_template(session, template_id="tpl-seeds")

    now = datetime.now(timezone.utc)
    eval_pack_1 = ScenarioPack(
        id="pack-eval-1",
        user_id="u1",
        template_id="tpl-seeds",
        state="COMMITTED",
        run_mode="EVALUATION",
        created_at=now,
        updated_at=now,
    )
    eval_pack_2 = ScenarioPack(
        id="pack-eval-2",
        user_id="u1",
        template_id="tpl-seeds",
        state="COMMITTED",
        run_mode="EVALUATION",
        created_at=now,
        updated_at=now,
    )
    session.add_all([eval_pack_1, eval_pack_2])
    session.commit()

    run_1 = await launch_run(async_session, eval_pack_1)
    session.commit()
    run_2 = await launch_run(async_session, eval_pack_2)
    session.commit()

    assert run_1.environment_seed == EVALUATION_SEEDS[0]
    assert run_2.environment_seed == EVALUATION_SEEDS[1]


# ── Priority 1: Exact REPLAY tests ──


@pytest.mark.asyncio
async def test_replay_copies_recorded_path_exactly(session):
    """REPLAY must copy persisted results from source run, not re-evaluate."""
    async_session = AsyncSessionAdapter(session)
    await _seed_valid_runtime_template(session, template_id="tpl-replay")

    now = datetime.now(timezone.utc)

    # Create and launch a source TRAINING run
    source_pack = ScenarioPack(
        id="pack-source",
        user_id="u1",
        template_id="tpl-replay",
        state="COMMITTED",
        run_mode="TRAINING",
        created_at=now,
        updated_at=now,
    )
    session.add(source_pack)
    session.commit()

    source_run = await launch_run(async_session, source_pack)
    session.commit()

    assert source_run.status == "COMPLETED"
    source_results = session.execute(
        select(RunCheckpointResult).where(RunCheckpointResult.run_id == source_run.id)
    ).scalars().all()
    assert len(source_results) > 0

    # Now replay it
    replay_pack = ScenarioPack(
        id="pack-replay",
        user_id="u1",
        template_id="tpl-replay",
        state="COMMITTED",
        run_mode="REPLAY",
        config_json={"replay_source_run_id": source_run.id},
        created_at=now,
        updated_at=now,
    )
    session.add(replay_pack)
    session.commit()

    replay_run = await launch_run(async_session, replay_pack)
    session.commit()

    assert replay_run.status == "COMPLETED"
    assert replay_run.source_run_id == source_run.id
    assert replay_run.environment_seed == source_run.environment_seed

    replay_results = session.execute(
        select(RunCheckpointResult).where(RunCheckpointResult.run_id == replay_run.id)
    ).scalars().all()

    # Same number of results, same branch selections and rewards
    assert len(replay_results) == len(source_results)
    for src, rep in zip(source_results, replay_results):
        assert rep.checkpoint_id == src.checkpoint_id
        assert rep.selected_branch_id == src.selected_branch_id
        assert rep.reward == src.reward
        # Replay state vector should reference the source
        assert rep.state_vector_json["replay_source_run_id"] == source_run.id


@pytest.mark.asyncio
async def test_replay_rejects_missing_source_run_id(session):
    """REPLAY without replay_source_run_id must fail immediately."""
    async_session = AsyncSessionAdapter(session)
    now = datetime.now(timezone.utc)

    pack = ScenarioPack(
        id="pack-no-source",
        user_id="u1",
        template_id="tpl-whatever",
        state="COMMITTED",
        run_mode="REPLAY",
        config_json={},
        created_at=now,
        updated_at=now,
    )
    session.add(pack)
    session.commit()

    with pytest.raises(ValueError, match="replay_source_run_id"):
        await launch_run(async_session, pack)


@pytest.mark.asyncio
async def test_replay_rejects_incomplete_source_run(session):
    """REPLAY must reject source runs that aren't COMPLETED."""
    async_session = AsyncSessionAdapter(session)
    await _seed_valid_runtime_template(session, template_id="tpl-replay2")
    now = datetime.now(timezone.utc)

    # Create an incomplete source run (PENDING, no results)
    source_pack = ScenarioPack(
        id="pack-incomplete-src",
        user_id="u1",
        template_id="tpl-replay2",
        state="ACTIVE",
        run_mode="TRAINING",
        created_at=now,
        updated_at=now,
    )
    session.add(source_pack)
    incomplete_run = ScenarioRun(
        id="run-incomplete",
        pack_id="pack-incomplete-src",
        status="RUNNING",
        run_mode="TRAINING",
        created_at=now,
    )
    session.add(incomplete_run)
    session.commit()

    replay_pack = ScenarioPack(
        id="pack-replay-incomplete",
        user_id="u1",
        template_id="tpl-replay2",
        state="COMMITTED",
        run_mode="REPLAY",
        config_json={"replay_source_run_id": "run-incomplete"},
        created_at=now,
        updated_at=now,
    )
    session.add(replay_pack)
    session.commit()

    with pytest.raises(ValueError, match="not COMPLETED"):
        await launch_run(async_session, replay_pack)


@pytest.mark.asyncio
async def test_replay_rejects_source_from_different_user(session):
    """REPLAY must reject source runs owned by a different user."""
    async_session = AsyncSessionAdapter(session)
    await _seed_valid_runtime_template(session, template_id="tpl-replay-user")
    now = datetime.now(timezone.utc)

    # Add a second user
    session.add(User(id="u2", username="other", email="other@test.com", password_hash="x"))

    # Source run owned by u1
    source_pack = ScenarioPack(
        id="pack-src-u1",
        user_id="u1",
        template_id="tpl-replay-user",
        state="COMMITTED",
        run_mode="TRAINING",
        created_at=now,
        updated_at=now,
    )
    session.add(source_pack)
    session.commit()

    source_run = await launch_run(async_session, source_pack)
    session.commit()
    assert source_run.status == "COMPLETED"

    # Replay pack owned by u2 — should be rejected
    replay_pack = ScenarioPack(
        id="pack-replay-u2",
        user_id="u2",
        template_id="tpl-replay-user",
        state="COMMITTED",
        run_mode="REPLAY",
        config_json={"replay_source_run_id": source_run.id},
        created_at=now,
        updated_at=now,
    )
    session.add(replay_pack)
    session.commit()

    with pytest.raises(ValueError, match="same user"):
        await launch_run(async_session, replay_pack)


@pytest.mark.asyncio
async def test_replay_rejects_source_from_different_template(session):
    """REPLAY must reject source runs from a different template."""
    async_session = AsyncSessionAdapter(session)
    await _seed_valid_runtime_template(session, template_id="tpl-replay-t1")
    now = datetime.now(timezone.utc)

    # Create a second template
    session.add(ScenarioPackTemplate(
        id="tpl-replay-t2",
        name="Other Template",
        family="TRAINING",
        description="Other",
        template_status="RUNNABLE",
        objective_vector_json=[{"weight": 1.0}],
        created_at=now,
    ))
    session.commit()

    # Source run from tpl-replay-t1
    source_pack = ScenarioPack(
        id="pack-src-t1",
        user_id="u1",
        template_id="tpl-replay-t1",
        state="COMMITTED",
        run_mode="TRAINING",
        created_at=now,
        updated_at=now,
    )
    session.add(source_pack)
    session.commit()

    source_run = await launch_run(async_session, source_pack)
    session.commit()
    assert source_run.status == "COMPLETED"

    # Replay pack using tpl-replay-t2 — should be rejected
    replay_pack = ScenarioPack(
        id="pack-replay-t2",
        user_id="u1",
        template_id="tpl-replay-t2",
        state="COMMITTED",
        run_mode="REPLAY",
        config_json={"replay_source_run_id": source_run.id},
        created_at=now,
        updated_at=now,
    )
    session.add(replay_pack)
    session.commit()

    with pytest.raises(ValueError, match="same template"):
        await launch_run(async_session, replay_pack)


@pytest.mark.asyncio
async def test_replay_does_not_misattribute_spawned_theatres(session):
    """Replay results must NOT set spawned_theatre_id — source theatre refs go in metadata only."""
    from backend.services.checkpoint_evaluator import replay_recorded_path

    await _seed_valid_runtime_template(session, template_id="tpl-replay-theatre")
    now = datetime.now(timezone.utc)

    # Create a source run with a result that has spawned_theatre_id
    source_pack = ScenarioPack(
        id="pack-theatre-src",
        user_id="u1",
        template_id="tpl-replay-theatre",
        state="ACTIVE",
        run_mode="TRAINING",
        created_at=now,
        updated_at=now,
    )
    session.add(source_pack)

    source_run = ScenarioRun(
        id="run-theatre-src",
        pack_id="pack-theatre-src",
        status="COMPLETED",
        run_mode="TRAINING",
        environment_seed=42,
        created_at=now,
        completed_at=now,
    )
    session.add(source_run)

    # Create a fake theatre for the source result to reference
    session.add(Theatre(
        id="theatre-spawned-src",
        user_id="u1",
        template_id="tt-runtime",
        construct_id="construct-1",
        state="ACTIVE",
        created_at=now,
    ))

    source_result = RunCheckpointResult(
        id="result-src-1",
        run_id="run-theatre-src",
        checkpoint_id="cp-runtime",
        selected_branch_id="br-runtime-a",
        reward=1.0,
        state_vector_json={"sequence_num": 1},
        spawned_theatre_id="theatre-spawned-src",
        resolved_at=now,
    )
    session.add(source_result)

    # Create replay run
    replay_pack = ScenarioPack(
        id="pack-theatre-replay",
        user_id="u1",
        template_id="tpl-replay-theatre",
        state="ACTIVE",
        run_mode="REPLAY",
        created_at=now,
        updated_at=now,
    )
    session.add(replay_pack)

    replay_run = ScenarioRun(
        id="run-theatre-replay",
        pack_id="pack-theatre-replay",
        status="PENDING",
        run_mode="REPLAY",
        source_run_id="run-theatre-src",
        created_at=now,
    )
    session.add(replay_run)
    session.commit()

    results = replay_recorded_path(session, replay_run, "run-theatre-src")

    assert len(results) == 1

    # spawned_theatre_id must NOT be set on replay results
    assert results[0].spawned_theatre_id is None

    # But the source theatre ref should be in state_vector metadata
    assert results[0].state_vector_json["replay_source_spawned_theatre_id"] == "theatre-spawned-src"


@pytest.mark.asyncio
async def test_replay_succeeds_for_valid_same_user_same_template(session):
    """REPLAY succeeds when source run has same user and same template."""
    async_session = AsyncSessionAdapter(session)
    await _seed_valid_runtime_template(session, template_id="tpl-replay-valid")
    now = datetime.now(timezone.utc)

    # Create and launch source run
    source_pack = ScenarioPack(
        id="pack-valid-src",
        user_id="u1",
        template_id="tpl-replay-valid",
        state="COMMITTED",
        run_mode="TRAINING",
        created_at=now,
        updated_at=now,
    )
    session.add(source_pack)
    session.commit()

    source_run = await launch_run(async_session, source_pack)
    session.commit()
    assert source_run.status == "COMPLETED"

    # Replay with same user (u1) and same template (tpl-replay-valid)
    replay_pack = ScenarioPack(
        id="pack-valid-replay",
        user_id="u1",
        template_id="tpl-replay-valid",
        state="COMMITTED",
        run_mode="REPLAY",
        config_json={"replay_source_run_id": source_run.id},
        created_at=now,
        updated_at=now,
    )
    session.add(replay_pack)
    session.commit()

    replay_run = await launch_run(async_session, replay_pack)
    session.commit()

    assert replay_run.status == "COMPLETED"
    assert replay_run.source_run_id == source_run.id

    # Verify results copied correctly
    replay_results = session.execute(
        select(RunCheckpointResult).where(RunCheckpointResult.run_id == replay_run.id)
    ).scalars().all()
    source_results = session.execute(
        select(RunCheckpointResult).where(RunCheckpointResult.run_id == source_run.id)
    ).scalars().all()

    assert len(replay_results) == len(source_results)
    for src, rep in zip(source_results, replay_results):
        assert rep.checkpoint_id == src.checkpoint_id
        assert rep.selected_branch_id == src.selected_branch_id
        assert rep.reward == src.reward


# ── Priority 2: Real trigger condition contract tests ──


def test_trigger_condition_field_operator_threshold():
    """trigger_condition_json with field/operator/threshold gates correctly."""
    from backend.services.checkpoint_evaluator import _trigger_condition_met

    # gte: 0.6 >= 0.5 -> True
    assert _trigger_condition_met(
        {"type": "BINARY_RISK_GATE", "threshold": 0.5, "metric": "risk",
         "field": "risk", "operator": "gte"},
        "0.6",
        {},
    ) is True

    # gte: 0.3 >= 0.5 -> False (gated)
    assert _trigger_condition_met(
        {"type": "BINARY_RISK_GATE", "threshold": 0.5, "metric": "risk",
         "field": "risk", "operator": "gte"},
        "0.3",
        {},
    ) is False

    # lt: 0.3 < 0.5 -> True
    assert _trigger_condition_met(
        {"type": "test", "threshold": 0.5,
         "field": "value", "operator": "lt"},
        "0.3",
        {},
    ) is True


def test_trigger_condition_state_vector_priority():
    """state_vector takes priority over agent_action for trigger fields."""
    from backend.services.checkpoint_evaluator import _trigger_condition_met

    # state_vector has risk=0.8, agent_action has 0.1
    # state_vector should win: 0.8 >= 0.5 -> True
    assert _trigger_condition_met(
        {"type": "test", "threshold": 0.5, "field": "risk", "operator": "gte"},
        "0.1",
        {"risk": 0.8},
    ) is True


def test_trigger_condition_unsupported_operator_fails():
    """Unsupported trigger operators must raise ValueError at runtime."""
    from backend.services.checkpoint_evaluator import _trigger_condition_met

    with pytest.raises(ValueError, match="Unsupported trigger operator"):
        _trigger_condition_met(
            {"type": "test", "threshold": 0.5, "field": "x", "operator": "contains"},
            "0.5",
            {},
        )


def test_trigger_condition_legacy_no_field_activates():
    """Legacy trigger_condition_json without field/operator/threshold activates."""
    from backend.services.checkpoint_evaluator import _trigger_condition_met

    # Has type + primitive metadata but no field/operator/threshold
    assert _trigger_condition_met(
        {"type": "BINARY_RISK_GATE", "threshold": 0.5, "metric": "risk"},
        "0.3",
        {},
    ) is True


def test_trigger_validation_partial_contract_errors():
    """Partial field/operator/threshold in trigger_condition_json must error."""
    from backend.services.checkpoint_evaluator import validate_trigger_condition_json

    errors = validate_trigger_condition_json(
        "BINARY_RISK_GATE",
        {"type": "BINARY_RISK_GATE", "threshold": 0.5, "metric": "risk",
         "field": "risk"},  # missing operator
    )
    assert any("missing" in e.lower() for e in errors)


def test_trigger_validation_bad_operator_errors():
    """Invalid operator in trigger_condition_json must error at validation."""
    from backend.services.checkpoint_evaluator import validate_trigger_condition_json

    errors = validate_trigger_condition_json(
        "BINARY_RISK_GATE",
        {"type": "BINARY_RISK_GATE", "threshold": 0.5, "metric": "risk",
         "field": "risk", "operator": "regex"},
    )
    assert any("unsupported" in e.lower() for e in errors)


# ── Priority 5: WS events collection test ──


def test_evaluate_checkpoints_collects_ws_events(session):
    """evaluate_checkpoints with ws_events list collects CHECKPOINT_RESOLVED events."""
    from backend.services.checkpoint_evaluator import evaluate_checkpoints

    now = datetime.now(timezone.utc)
    session.add(User(id="u-ws", username="ws", email="ws@test.com", password_hash="x"))
    session.add(TheatreTemplate(
        id="tt-ws", template_family="SCENARIO", execution_path="LOCAL",
        display_name="WS", description="", schema_version="1.0.0",
        inquiry_class="COUNTERFACTUAL", template_json={}, created_at=now, updated_at=now,
    ))
    session.add(ScenarioPackTemplate(
        id="tpl-ws", name="WS", family="TRAINING", description="",
        template_status="RUNNABLE", objective_vector_json=[{"weight": 1.0}], created_at=now,
    ))
    session.add(ScenarioCheckpoint(
        id="cp-ws", template_id="tpl-ws", sequence_num=1, trigger="ws",
        trigger_condition_json={"type": "BINARY_RISK_GATE", "threshold": 0.5, "metric": "risk"},
        market_question="WS?", decision_window_sec=30,
        evaluator_type="BINARY_RISK_GATE", reward_mapping_json={"base_reward": 1.0},
        created_at=now,
    ))
    rule = {"type": "threshold_compare", "field": "action_value", "threshold": 0.5,
            "above_branch_index": 0, "below_branch_index": 1}
    session.add_all([
        CheckpointBranch(id="br-ws-a", checkpoint_id="cp-ws", label="a",
                         outcome_type="SUCCESS", branch_rule_json=rule),
        CheckpointBranch(id="br-ws-b", checkpoint_id="cp-ws", label="b",
                         outcome_type="FAILURE", branch_rule_json=rule),
    ])
    pack = ScenarioPack(
        id="pack-ws", user_id="u-ws", template_id="tpl-ws",
        state="ACTIVE", run_mode="TRAINING", created_at=now, updated_at=now,
    )
    session.add(pack)
    run = ScenarioRun(
        id="run-ws", pack_id="pack-ws", status="PENDING",
        run_mode="TRAINING", created_at=now,
    )
    session.add(run)
    session.commit()

    ws_events = []
    evaluate_checkpoints(session, run, seed=42, ws_events=ws_events)

    assert len(ws_events) >= 1
    checkpoint_events = [e for e in ws_events if e["type"] == "CHECKPOINT_RESOLVED"]
    assert len(checkpoint_events) == 1
    assert checkpoint_events[0]["pack_id"] == "pack-ws"
    assert checkpoint_events[0]["run_id"] == "run-ws"
    assert checkpoint_events[0]["checkpoint_id"] == "cp-ws"
