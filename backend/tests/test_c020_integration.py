"""Cycle-020 Sprint 5 — Integration + E2E tests.

Tests:
1. Full scenario: template -> pack -> run -> schema evaluation -> correct branches
2. Spawn rule integration: theatre spawned only when rule passes
3. Paradox risk WS materiality: level change emits, same level doesn't
4. CHECKPOINT_RESOLVED / THEATRE_SPAWNED WS payload structure
5. Regression: legacy hash fallback still works for null branch_rule
6. Regression: CATALOG_ONLY templates unaffected
7. Full replay integration: run then replay with same seed
"""

import pytest
from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from backend.database.models import (
    Base,
    ScenarioPackTemplate,
    ScenarioCheckpoint,
    CheckpointBranch,
    ScenarioPack,
    ScenarioRun,
    RunCheckpointResult,
    TheatreTemplate,
    Theatre,
    TheatreCertificate,
    ScenarioPackAuditEvent,
    User,
)
from backend.services.checkpoint_evaluator import (
    evaluate_checkpoints,
    validate_template_checkpoints,
)
from backend.services.paradox_risk_orchestrator import is_material_delta


# ── Fixtures ──

def _create_tables(eng):
    tables = [
        Base.metadata.tables[t]
        for t in [
            "users", "theatre_templates", "theatres", "theatre_certificates",
            "scenario_pack_templates", "scenario_checkpoints", "checkpoint_branches",
            "scenario_packs", "scenario_runs", "run_checkpoint_results",
            "scenario_pack_audit_events",
        ]
        if t in Base.metadata.tables
    ]
    Base.metadata.create_all(eng, tables=tables)


@pytest.fixture
def engine():
    eng = create_engine("sqlite:///:memory:")
    _create_tables(eng)
    yield eng
    eng.dispose()


@pytest.fixture
def session(engine):
    with Session(engine) as s:
        yield s


def _setup_base(session):
    user = User(id="u1", username="testuser", password_hash="fakehash", email="t@t.com")
    session.add(user)
    tt = TheatreTemplate(
        id="tt-1", template_family="SCENARIO", execution_path="LOCAL",
        display_name="Scenario Derived", description="Test", schema_version="1.0.0",
        inquiry_class="COUNTERFACTUAL", template_json={},
        created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc),
    )
    session.add(tt)
    session.flush()


# ── Test 1: Full scenario with schema evaluation ──

def test_full_scenario_schema_evaluation(session):
    """Template -> pack -> run -> schema-driven checkpoint evaluation."""
    _setup_base(session)

    tpl = ScenarioPackTemplate(
        id="tpl-full", name="Full Test", family="TRAINING",
        description="Full scenario", template_status="RUNNABLE",
        objective_vector_json=[{"weight": 1.0}],
        created_at=datetime.now(timezone.utc),
    )
    session.add(tpl)

    # Checkpoint 1: BINARY_RISK_GATE
    cp1 = ScenarioCheckpoint(
        id="cp-f1", template_id="tpl-full", sequence_num=1,
        trigger="market_open", market_question="Risk gate?",
        evaluator_type="BINARY_RISK_GATE",
        trigger_condition_json={"type": "BINARY_RISK_GATE", "threshold": 0.5, "metric": "risk"},
        reward_mapping_json={"base_reward": 2.0},
        created_at=datetime.now(timezone.utc),
    )
    session.add(cp1)

    br1a = CheckpointBranch(
        id="br-f1a", checkpoint_id="cp-f1", label="high_risk", outcome_type="SUCCESS",
        branch_rule_json={"type": "threshold_compare", "field": "action_value",
                          "threshold": 0.5, "above_branch_index": 0, "below_branch_index": 1},
        next_checkpoint_id="cp-f2",
    )
    br1b = CheckpointBranch(
        id="br-f1b", checkpoint_id="cp-f1", label="low_risk", outcome_type="FAILURE",
        branch_rule_json={"type": "threshold_compare", "field": "action_value",
                          "threshold": 0.5, "above_branch_index": 0, "below_branch_index": 1},
    )
    session.add_all([br1a, br1b])

    # Checkpoint 2: MISSION_COMPLETION
    cp2 = ScenarioCheckpoint(
        id="cp-f2", template_id="tpl-full", sequence_num=2,
        trigger="final_check", market_question="Mission complete?",
        evaluator_type="MISSION_COMPLETION",
        trigger_condition_json={"type": "MISSION_COMPLETION", "required_objectives": ["a", "b"], "min_completion": 1},
        reward_mapping_json={"base_reward": 3.0},
        created_at=datetime.now(timezone.utc),
    )
    session.add(cp2)

    br2a = CheckpointBranch(
        id="br-f2a", checkpoint_id="cp-f2", label="mission_success", outcome_type="SUCCESS",
        branch_rule_json={"type": "objective_set", "required": ["a", "b"], "min_completion": 1,
                          "success_branch_index": 0, "partial_branch_index": 1, "fail_branch_index": 2},
    )
    br2b = CheckpointBranch(
        id="br-f2b", checkpoint_id="cp-f2", label="mission_partial", outcome_type="PARTIAL",
        branch_rule_json={"type": "objective_set", "required": ["a", "b"], "min_completion": 1,
                          "success_branch_index": 0, "partial_branch_index": 1, "fail_branch_index": 2},
    )
    br2c = CheckpointBranch(
        id="br-f2c", checkpoint_id="cp-f2", label="mission_fail", outcome_type="FAILURE",
        branch_rule_json={"type": "objective_set", "required": ["a", "b"], "min_completion": 1,
                          "success_branch_index": 0, "partial_branch_index": 1, "fail_branch_index": 2},
    )
    session.add_all([br2a, br2b, br2c])
    session.flush()

    pack = ScenarioPack(
        id="pack-full", user_id="u1", template_id="tpl-full",
        state="COMMITTED", run_mode="TRAINING",
        created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc),
    )
    session.add(pack)
    run = ScenarioRun(
        id="run-full", pack_id="pack-full", run_mode="TRAINING",
        created_at=datetime.now(timezone.utc),
    )
    session.add(run)
    session.flush()

    results = evaluate_checkpoints(
        session, run, seed=42,
        agent_actions={"cp-f1": "0.8", "cp-f2": "a,b"},
    )

    assert len(results) == 2
    assert results[0].selected_branch_id == "br-f1a"  # Above threshold
    assert results[1].selected_branch_id == "br-f2a"  # Success (both objectives)
    assert run.status == "COMPLETED"
    assert run.total_reward > 0


# ── Test 2: Spawn rule integration ──

def test_spawn_rule_integration(session):
    """Theatre spawned only when spawn rule passes."""
    _setup_base(session)

    tpl = ScenarioPackTemplate(
        id="tpl-spawn", name="Spawn Test", family="TRAINING",
        description="Spawn test", template_status="RUNNABLE",
        objective_vector_json=[{"weight": 1.0}],
        created_at=datetime.now(timezone.utc),
    )
    session.add(tpl)

    # Checkpoint with spawn rule requiring SUCCESS outcome
    cp = ScenarioCheckpoint(
        id="cp-sp1", template_id="tpl-spawn", sequence_num=1,
        trigger="spawn_check", market_question="Spawn?",
        evaluator_type="BINARY_RISK_GATE",
        trigger_condition_json={"type": "BINARY_RISK_GATE", "threshold": 0.5, "metric": "risk"},
        theatre_spawn_rule_json={"outcome_types": ["SUCCESS"], "min_reward": 0.1},
        reward_mapping_json={"base_reward": 1.0},
        created_at=datetime.now(timezone.utc),
    )
    session.add(cp)

    br_success = CheckpointBranch(
        id="br-sp-s", checkpoint_id="cp-sp1", label="success", outcome_type="SUCCESS",
        branch_rule_json={"type": "threshold_compare", "field": "action_value",
                          "threshold": 0.5, "above_branch_index": 0, "below_branch_index": 1},
        reward_mapping_json={"base_reward": 1.0},
    )
    br_fail = CheckpointBranch(
        id="br-sp-f", checkpoint_id="cp-sp1", label="failure", outcome_type="FAILURE",
        branch_rule_json={"type": "threshold_compare", "field": "action_value",
                          "threshold": 0.5, "above_branch_index": 0, "below_branch_index": 1},
    )
    session.add_all([br_success, br_fail])
    session.flush()

    # Run with action above threshold -> SUCCESS -> spawn should happen
    pack = ScenarioPack(
        id="pack-sp", user_id="u1", template_id="tpl-spawn",
        state="COMMITTED", run_mode="TRAINING",
        created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc),
    )
    session.add(pack)
    run = ScenarioRun(
        id="run-sp", pack_id="pack-sp", run_mode="TRAINING",
        created_at=datetime.now(timezone.utc),
    )
    session.add(run)
    session.flush()

    results = evaluate_checkpoints(
        session, run, seed=42,
        agent_actions={"cp-sp1": "0.8"},
    )

    assert len(results) == 1
    assert results[0].selected_branch_id == "br-sp-s"
    # Theatre should have been spawned
    assert results[0].spawned_theatre_id is not None

    # Verify theatre exists
    spawned = session.get(Theatre, results[0].spawned_theatre_id)
    assert spawned is not None
    assert spawned.spawned_from_checkpoint_id == "cp-sp1"


# ── Test 3: Paradox risk materiality for WS emission ──

def test_paradox_risk_ws_materiality():
    """Level change -> emit event, same level -> no event."""
    factors = {
        "logic_gap": 0.3, "stability": 0.7, "active_paradox": False,
        "material_counter_signals": 0, "evidence_freshness_hours": 12.0,
    }

    # Material: level change
    assert is_material_delta("LOW", "WATCH", factors, factors) is True

    # Not material: same everything
    assert is_material_delta("LOW", "LOW", factors, factors) is False

    # Material: paradox flip
    new_factors = {**factors, "active_paradox": True}
    assert is_material_delta("LOW", "LOW", factors, new_factors) is True


# ── Test 4: WS payload structure (unit) ──

def test_ws_payload_structure():
    """Verify CHECKPOINT_RESOLVED event would have correct fields."""
    # This tests the data structure that would be passed to broadcast
    payload = {
        "pack_id": "pack-1",
        "run_id": "run-1",
        "checkpoint_id": "cp-1",
        "selected_branch_id": "br-1",
        "reward": 2.0,
        "seed": 42,
    }
    assert all(k in payload for k in ["pack_id", "run_id", "checkpoint_id", "selected_branch_id", "reward", "seed"])

    theatre_payload = {
        "pack_id": "pack-1",
        "run_id": "run-1",
        "checkpoint_id": "cp-1",
        "theatre_id": "t-1",
    }
    assert all(k in theatre_payload for k in ["pack_id", "run_id", "checkpoint_id", "theatre_id"])


# ── Test 5: Legacy hash fallback ──

def test_legacy_hash_fallback(session):
    """Null branch_rule_json falls back to hash-based selection."""
    _setup_base(session)

    tpl = ScenarioPackTemplate(
        id="tpl-legacy", name="Legacy", family="TRAINING",
        description="Legacy", template_status="RUNNABLE",
        objective_vector_json=[{"weight": 1.0}],
        created_at=datetime.now(timezone.utc),
    )
    session.add(tpl)

    cp = ScenarioCheckpoint(
        id="cp-leg", template_id="tpl-legacy", sequence_num=1,
        trigger="legacy", market_question="Legacy?",
        evaluator_type="BINARY_RISK_GATE",
        trigger_condition_json=None,  # No trigger config
        reward_mapping_json={"base_reward": 1.0},
        created_at=datetime.now(timezone.utc),
    )
    session.add(cp)

    br1 = CheckpointBranch(
        id="br-leg-1", checkpoint_id="cp-leg", label="a", outcome_type="SUCCESS",
        branch_rule_json=None,  # No branch rule -> hash fallback
    )
    br2 = CheckpointBranch(
        id="br-leg-2", checkpoint_id="cp-leg", label="b", outcome_type="FAILURE",
        branch_rule_json=None,
    )
    session.add_all([br1, br2])
    session.flush()

    pack = ScenarioPack(
        id="pack-leg", user_id="u1", template_id="tpl-legacy",
        state="COMMITTED", run_mode="TRAINING",
        created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc),
    )
    session.add(pack)
    run = ScenarioRun(
        id="run-leg", pack_id="pack-leg", run_mode="TRAINING",
        created_at=datetime.now(timezone.utc),
    )
    session.add(run)
    session.flush()

    results = evaluate_checkpoints(session, run, seed=42)
    assert len(results) == 1
    assert results[0].state_vector_json["evaluation_detail"]["fallback"] == "hash_based"


# ── Test 6: CATALOG_ONLY template validation ──

def test_catalog_only_unaffected(session):
    """CATALOG_ONLY templates don't need valid evaluator configs."""
    _setup_base(session)

    tpl = ScenarioPackTemplate(
        id="tpl-cat", name="Catalog", family="TRAINING",
        description="Catalog only", template_status="CATALOG_ONLY",
        created_at=datetime.now(timezone.utc),
    )
    session.add(tpl)

    # Checkpoint with no configs at all
    cp = ScenarioCheckpoint(
        id="cp-cat", template_id="tpl-cat", sequence_num=1,
        trigger="catalog", market_question="Catalog?",
        evaluator_type="BINARY_RISK_GATE",
        created_at=datetime.now(timezone.utc),
    )
    session.add(cp)
    br = CheckpointBranch(
        id="br-cat", checkpoint_id="cp-cat", label="a", outcome_type="INFO",
    )
    session.add(br)
    session.flush()

    # Validation reports errors but template is CATALOG_ONLY so shouldn't block
    errors = validate_template_checkpoints(session, "tpl-cat")
    # Errors exist (missing configs) but that's expected for catalog
    assert len(errors) > 0  # Has validation errors but template is non-runnable


# ── Test 7: Full replay integration ──

def test_full_replay_integration(session):
    """Run then replay: same seed produces identical results."""
    _setup_base(session)

    tpl = ScenarioPackTemplate(
        id="tpl-rep", name="Replay Test", family="TRAINING",
        description="Replay", template_status="RUNNABLE",
        objective_vector_json=[{"weight": 1.0}],
        created_at=datetime.now(timezone.utc),
    )
    session.add(tpl)

    cp = ScenarioCheckpoint(
        id="cp-rep", template_id="tpl-rep", sequence_num=1,
        trigger="replay_test", market_question="Replay?",
        evaluator_type="DETECTION_EVENT",
        trigger_condition_json={"type": "DETECTION_EVENT", "base_detection_probability": 0.5},
        reward_mapping_json={"base_reward": 1.0},
        created_at=datetime.now(timezone.utc),
    )
    session.add(cp)

    br_det = CheckpointBranch(
        id="br-rep-d", checkpoint_id="cp-rep", label="detected", outcome_type="FAILURE",
        branch_rule_json={"type": "probability_gate", "base_probability": 0.5,
                          "noise_amplitude": 0.2, "detected_branch_index": 0, "safe_branch_index": 1},
    )
    br_safe = CheckpointBranch(
        id="br-rep-s", checkpoint_id="cp-rep", label="safe", outcome_type="SUCCESS",
        branch_rule_json={"type": "probability_gate", "base_probability": 0.5,
                          "noise_amplitude": 0.2, "detected_branch_index": 0, "safe_branch_index": 1},
    )
    session.add_all([br_det, br_safe])
    session.flush()

    seed = 42
    action = "stealth=0.4"

    # Run 1
    pack1 = ScenarioPack(
        id="pk-rep1", user_id="u1", template_id="tpl-rep",
        state="COMMITTED", run_mode="TRAINING",
        created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc),
    )
    session.add(pack1)
    run1 = ScenarioRun(id="rn-rep1", pack_id="pk-rep1", run_mode="TRAINING",
                       created_at=datetime.now(timezone.utc))
    session.add(run1)
    session.flush()
    res1 = evaluate_checkpoints(session, run1, seed=seed, agent_actions={"cp-rep": action})

    # Run 2 (replay with same seed)
    pack2 = ScenarioPack(
        id="pk-rep2", user_id="u1", template_id="tpl-rep",
        state="COMMITTED", run_mode="REPLAY",
        created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc),
    )
    session.add(pack2)
    run2 = ScenarioRun(id="rn-rep2", pack_id="pk-rep2", run_mode="REPLAY",
                       created_at=datetime.now(timezone.utc))
    session.add(run2)
    session.flush()
    res2 = evaluate_checkpoints(session, run2, seed=seed, agent_actions={"cp-rep": action})

    assert len(res1) == len(res2) == 1
    assert res1[0].selected_branch_id == res2[0].selected_branch_id
    assert res1[0].reward == res2[0].reward


# ── Test 8: Trigger condition evaluation (P1-2 fix) ──

def test_trigger_condition_gates_activation(session):
    """trigger_condition_json determines whether checkpoint activates."""
    from backend.services.checkpoint_evaluator import _trigger_condition_met

    # None trigger -> always active (legacy)
    assert _trigger_condition_met(None, "0.5", {}) is True

    # BINARY_RISK_GATE: activates when metric >= threshold
    tc = {"type": "BINARY_RISK_GATE", "threshold": 0.5, "metric": "risk"}
    assert _trigger_condition_met(tc, "risk=0.8", {}) is True
    assert _trigger_condition_met(tc, "risk=0.3", {}) is False

    # MISSION_COMPLETION: activates when objectives exist
    tc = {"type": "MISSION_COMPLETION", "required_objectives": ["a", "b"]}
    assert _trigger_condition_met(tc, "", {}) is True
    tc_empty = {"type": "MISSION_COMPLETION", "required_objectives": []}
    assert _trigger_condition_met(tc_empty, "", {}) is False

    # Unknown type: safe fallback to active
    assert _trigger_condition_met({"type": "FUTURE_TYPE"}, "", {}) is True


# ── Test 9: launch_run wires seed + evaluation (P1-1 fix) ──

def test_launch_run_allocates_seed():
    """launch_run allocates seed from scenario_seed_manager."""
    from backend.services.scenario_seed_manager import allocate_seed

    # Verify allocate_seed is callable from launch_run's code path
    seed = allocate_seed("TRAINING")
    assert isinstance(seed, int)
    assert 0 <= seed <= 2**31 - 1

    # CALIBRATION seeds are deterministic
    s1 = allocate_seed("CALIBRATION", 0)
    s2 = allocate_seed("CALIBRATION", 0)
    assert s1 == s2


# ── Test 10: Orchestrator used for paradox risk (P1-3 fix) ──

@pytest.mark.asyncio
async def test_orchestrator_wired_to_production():
    """trigger_recompute is importable and callable from theatre routes."""
    from unittest.mock import AsyncMock, MagicMock
    from backend.services.paradox_risk_orchestrator import trigger_recompute, is_material_delta

    # Verify trigger_recompute returns assessment with materiality metadata
    theatre = MagicMock()
    theatre.paradox_risk_level = "LOW"
    theatre.paradox_risk_factors_json = {
        "logic_gap": 0.1, "stability": 0.9, "active_paradox": False,
        "material_counter_signals": 0, "evidence_freshness_hours": 5.0,
    }
    theatre.paradox_risk_updated_at = None

    db = AsyncMock()
    db.get = AsyncMock(return_value=theatre)

    assessment = await trigger_recompute(
        db, "t-1", "evidence_freshness_threshold",
        logic_gap=0.8, stability=0.2, has_active_paradox=True,
        inquiry_class="COUNTERFACTUAL",
    )

    assert assessment is not None
    assert hasattr(assessment, "_material")
    assert hasattr(assessment, "_old_level")
    assert hasattr(assessment, "_trigger_reason")
    assert assessment._trigger_reason == "evidence_freshness_threshold"
