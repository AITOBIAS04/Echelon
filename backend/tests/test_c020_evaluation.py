"""Cycle-020 Sprint 1-2 — Schema-Driven Checkpoint Evaluation + RNG tests.

Tests:
1. BINARY_RISK_GATE branch selection (above/below threshold)
2. RESOURCE_DEPLETION bracket mapping
3. DETECTION_EVENT probability gate with seeded noise determinism
4. TIMING_BREACH deadline with seeded drift determinism
5. MISSION_COMPLETION objective set evaluation
6. select_branch dispatch + unknown evaluator error
7. Fail-fast: invalid config raises ValueError
8. Seeded RNG determinism: same seed+checkpoint = same result
9. Seeded RNG variation: different checkpoints = different noise
10. Full evaluate_checkpoints with schema-driven branches
11. Replay: same seed reproduces exact branch sequence
12. Seed parity: CALIBRATION seeds produce consistent results
13. State vector accumulation across checkpoints
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
    User,
    Theatre,
    TheatreCertificate,
    ScenarioPackAuditEvent,
)
from backend.services.checkpoint_evaluator import (
    evaluate_binary_risk_gate,
    evaluate_resource_depletion,
    evaluate_detection_event,
    evaluate_timing_breach,
    evaluate_mission_completion,
    select_branch,
    _seeded_rng,
    evaluate_checkpoints,
    validate_template_checkpoints,
)
from backend.services.scenario_seed_manager import allocate_seed, CALIBRATION_SEEDS


# ── Fixtures ──

def _create_tables(eng):
    tables = [
        Base.metadata.tables[t]
        for t in [
            "users",
            "theatre_templates",
            "theatres",
            "theatre_certificates",
            "scenario_pack_templates",
            "scenario_checkpoints",
            "checkpoint_branches",
            "scenario_packs",
            "scenario_runs",
            "run_checkpoint_results",
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


def _make_template(session, template_id="tpl-1", status="RUNNABLE"):
    user = User(id="u1", username="testuser", password_hash="fakehash", email="t@t.com")
    session.add(user)
    session.flush()

    tt = TheatreTemplate(
        id="tt-1", template_family="STANDARD", execution_path="LOCAL",
        display_name="Test", description="Test", schema_version="1.0.0",
        inquiry_class="COUNTERFACTUAL", template_json={},
        created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc),
    )
    session.add(tt)

    tpl = ScenarioPackTemplate(
        id=template_id, name="Test Template", family="TRAINING",
        description="Test", template_status=status,
        objective_vector_json=[{"weight": 1.0}],
        created_at=datetime.now(timezone.utc),
    )
    session.add(tpl)
    session.flush()
    return tpl


def _make_checkpoint(session, template_id, seq, evaluator_type, trigger_json, spawn_rule=None):
    cp = ScenarioCheckpoint(
        id=f"cp-{seq}",
        template_id=template_id,
        sequence_num=seq,
        trigger=f"trigger_{seq}",
        trigger_condition_json=trigger_json,
        market_question=f"Question {seq}?",
        decision_window_sec=30,
        evaluator_type=evaluator_type,
        can_spawn_theatre=False,
        theatre_spawn_rule_json=spawn_rule,
        reward_mapping_json={"base_reward": 1.0},
        created_at=datetime.now(timezone.utc),
    )
    session.add(cp)
    session.flush()
    return cp


def _make_branch(session, checkpoint_id, label, outcome_type, branch_rule, next_cp_id=None, reward_map=None):
    br = CheckpointBranch(
        id=f"br-{checkpoint_id}-{label}",
        checkpoint_id=checkpoint_id,
        label=label,
        branch_rule_json=branch_rule,
        outcome_type=outcome_type,
        reward_mapping_json=reward_map,
        next_checkpoint_id=next_cp_id,
    )
    session.add(br)
    session.flush()
    return br


def _make_pack_and_run(session, template_id, run_mode="TRAINING"):
    pack = ScenarioPack(
        id="pack-1", user_id="u1", template_id=template_id,
        state="COMMITTED", run_mode=run_mode,
        created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc),
    )
    session.add(pack)
    session.flush()

    run = ScenarioRun(
        id="run-1", pack_id=pack.id, run_mode=run_mode,
        created_at=datetime.now(timezone.utc),
    )
    session.add(run)
    session.flush()
    return pack, run


# ── Test 1: BINARY_RISK_GATE ──

def test_binary_risk_gate():
    rule = {
        "type": "threshold_compare",
        "field": "action_value",
        "threshold": 0.65,
        "above_branch_index": 0,
        "below_branch_index": 1,
    }
    # Above threshold
    idx, detail = evaluate_binary_risk_gate(rule, "0.8", 42, {})
    assert idx == 0
    assert detail["result"] == "above"

    # Below threshold
    idx, detail = evaluate_binary_risk_gate(rule, "0.3", 42, {})
    assert idx == 1
    assert detail["result"] == "below"

    # Exactly at threshold
    idx, detail = evaluate_binary_risk_gate(rule, "0.65", 42, {})
    assert idx == 0
    assert detail["result"] == "above"


# ── Test 2: RESOURCE_DEPLETION ──

def test_resource_depletion():
    rule = {
        "type": "resource_bracket",
        "brackets": [
            {"min": 0.0, "max": 0.3, "branch_index": 0},
            {"min": 0.3, "max": 0.7, "branch_index": 1},
            {"min": 0.7, "max": 1.0, "branch_index": 2},
        ],
        "field": "remaining_fraction",
    }
    idx, detail = evaluate_resource_depletion(rule, "0.15", 42, {})
    assert idx == 0

    idx, detail = evaluate_resource_depletion(rule, "0.5", 42, {})
    assert idx == 1

    idx, detail = evaluate_resource_depletion(rule, "0.85", 42, {})
    assert idx == 2


# ── Test 3: DETECTION_EVENT determinism ──

def test_detection_event_determinism():
    rule = {
        "type": "probability_gate",
        "base_probability": 0.3,
        "noise_amplitude": 0.1,
        "detected_branch_index": 0,
        "safe_branch_index": 1,
    }
    state = {"checkpoint_id": "cp-1"}

    # Same inputs always produce same result
    results = [evaluate_detection_event(rule, "stealth=0.5", 42, state) for _ in range(10)]
    assert all(r[0] == results[0][0] for r in results)
    assert all(r[1]["noise"] == results[0][1]["noise"] for r in results)


# ── Test 4: TIMING_BREACH determinism ──

def test_timing_breach_determinism():
    rule = {
        "type": "deadline_compare",
        "deadline_sec": 300,
        "drift_range": 30,
        "on_time_branch_index": 0,
        "breach_branch_index": 1,
    }
    state = {"checkpoint_id": "cp-1"}

    results = [evaluate_timing_breach(rule, "time=280", 42, state) for _ in range(10)]
    assert all(r[0] == results[0][0] for r in results)
    assert all(r[1]["drift"] == results[0][1]["drift"] for r in results)


# ── Test 5: MISSION_COMPLETION ──

def test_mission_completion():
    rule = {
        "type": "objective_set",
        "required": ["obj_a", "obj_b", "obj_c"],
        "min_completion": 2,
        "success_branch_index": 0,
        "partial_branch_index": 1,
        "fail_branch_index": 2,
    }
    # Success: 2+ objectives
    idx, detail = evaluate_mission_completion(rule, "obj_a,obj_b", 42, {})
    assert idx == 0
    assert detail["result"] == "success"

    # Partial: 1 objective
    idx, detail = evaluate_mission_completion(rule, "obj_a", 42, {})
    assert idx == 1
    assert detail["result"] == "partial"

    # Fail: 0 objectives
    idx, detail = evaluate_mission_completion(rule, "none", 42, {})
    assert idx == 2
    assert detail["result"] == "fail"


# ── Test 6: select_branch dispatch ──

def test_select_branch_dispatch(session):
    _make_template(session)
    cp = _make_checkpoint(session, "tpl-1", 1, "BINARY_RISK_GATE",
                          {"type": "BINARY_RISK_GATE", "threshold": 0.5, "metric": "risk"})
    br_above = _make_branch(session, cp.id, "above", "SUCCESS",
                            {"type": "threshold_compare", "field": "action_value", "threshold": 0.5,
                             "above_branch_index": 0, "below_branch_index": 1})
    br_below = _make_branch(session, cp.id, "below", "FAILURE",
                            {"type": "threshold_compare", "field": "action_value", "threshold": 0.5,
                             "above_branch_index": 0, "below_branch_index": 1})

    branches = [br_above, br_below]
    selected, detail = select_branch(
        "BINARY_RISK_GATE", branches,
        branches[0].branch_rule_json, "0.8", 42, {}
    )
    assert selected.id == br_above.id

    # Unknown evaluator
    with pytest.raises(ValueError, match="Unknown evaluator primitive"):
        select_branch("UNKNOWN", branches, {}, "0.5", 42, {})

    # Empty branches
    with pytest.raises(ValueError, match="No branches"):
        select_branch("BINARY_RISK_GATE", [], {}, "0.5", 42, {})


# ── Test 7: Fail-fast validation ──

def test_fail_fast_invalid_config(session):
    tpl = _make_template(session)
    cp = _make_checkpoint(session, "tpl-1", 1, "BINARY_RISK_GATE", None)  # Missing trigger_condition
    _make_branch(session, cp.id, "a", "SUCCESS", None)  # Missing branch_rule

    errors = validate_template_checkpoints(session, "tpl-1")
    assert len(errors) >= 2  # At least trigger + branch_rule errors


# ── Test 8: Seeded RNG determinism ──

def test_seeded_rng_determinism():
    rng1 = _seeded_rng(42, "cp-1")
    rng2 = _seeded_rng(42, "cp-1")
    assert rng1.random() == rng2.random()


# ── Test 9: Seeded RNG variation ──

def test_seeded_rng_variation():
    rng1 = _seeded_rng(42, "cp-1")
    rng2 = _seeded_rng(42, "cp-2")
    # Different checkpoints should produce different values
    assert rng1.random() != rng2.random()


# ── Test 10: Full evaluate_checkpoints with schema-driven branches ──

def test_evaluate_checkpoints_schema_driven(session):
    tpl = _make_template(session)

    cp1 = _make_checkpoint(session, "tpl-1", 1, "BINARY_RISK_GATE",
                           {"type": "BINARY_RISK_GATE", "threshold": 0.5, "metric": "risk"})
    br1_above = _make_branch(session, cp1.id, "above", "SUCCESS",
                             {"type": "threshold_compare", "field": "action_value", "threshold": 0.5,
                              "above_branch_index": 0, "below_branch_index": 1},
                             reward_map={"base_reward": 2.0})
    br1_below = _make_branch(session, cp1.id, "below", "FAILURE",
                             {"type": "threshold_compare", "field": "action_value", "threshold": 0.5,
                              "above_branch_index": 0, "below_branch_index": 1},
                             reward_map={"base_reward": 0.5})

    pack, run = _make_pack_and_run(session, "tpl-1")

    results = evaluate_checkpoints(
        session, run, seed=42,
        agent_actions={"cp-1": "0.8"},
    )

    assert len(results) == 1
    assert results[0].selected_branch_id == br1_above.id
    assert run.status == "COMPLETED"
    # State vector should contain evaluation_detail
    assert "evaluation_detail" in results[0].state_vector_json
    assert results[0].state_vector_json["evaluation_detail"]["result"] == "above"


# ── Test 11: Replay determinism ──

def test_replay_determinism(session):
    """Same seed + same actions -> same branch selections."""
    tpl = _make_template(session)

    cp1 = _make_checkpoint(session, "tpl-1", 1, "DETECTION_EVENT",
                           {"type": "DETECTION_EVENT", "base_detection_probability": 0.3})
    br_detected = _make_branch(session, cp1.id, "detected", "FAILURE",
                               {"type": "probability_gate", "base_probability": 0.3, "noise_amplitude": 0.1,
                                "detected_branch_index": 0, "safe_branch_index": 1})
    br_safe = _make_branch(session, cp1.id, "safe", "SUCCESS",
                           {"type": "probability_gate", "base_probability": 0.3, "noise_amplitude": 0.1,
                            "detected_branch_index": 0, "safe_branch_index": 1})

    # First run
    pack1 = ScenarioPack(
        id="pack-r1", user_id="u1", template_id="tpl-1",
        state="COMMITTED", run_mode="TRAINING",
        created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc),
    )
    session.add(pack1)
    session.flush()
    run1 = ScenarioRun(id="run-r1", pack_id="pack-r1", run_mode="TRAINING",
                       created_at=datetime.now(timezone.utc))
    session.add(run1)
    session.flush()

    results1 = evaluate_checkpoints(session, run1, seed=42, agent_actions={"cp-1": "stealth=0.5"})

    # Second run with same seed
    pack2 = ScenarioPack(
        id="pack-r2", user_id="u1", template_id="tpl-1",
        state="COMMITTED", run_mode="TRAINING",
        created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc),
    )
    session.add(pack2)
    session.flush()
    run2 = ScenarioRun(id="run-r2", pack_id="pack-r2", run_mode="TRAINING",
                       created_at=datetime.now(timezone.utc))
    session.add(run2)
    session.flush()

    results2 = evaluate_checkpoints(session, run2, seed=42, agent_actions={"cp-1": "stealth=0.5"})

    assert len(results1) == len(results2) == 1
    assert results1[0].selected_branch_id == results2[0].selected_branch_id


# ── Test 12: CALIBRATION seed consistency ──

def test_calibration_seed_consistency():
    """CALIBRATION seeds always produce same value for same index."""
    for i in range(5):
        s1 = allocate_seed("CALIBRATION", i)
        s2 = allocate_seed("CALIBRATION", i)
        assert s1 == s2 == CALIBRATION_SEEDS[i]


# ── Test 13: State vector accumulation ──

def test_state_vector_accumulation(session):
    """State vector accumulates reward and outcomes across checkpoints."""
    tpl = _make_template(session)

    cp1 = _make_checkpoint(session, "tpl-1", 1, "BINARY_RISK_GATE",
                           {"type": "BINARY_RISK_GATE", "threshold": 0.5, "metric": "risk"})
    br1 = _make_branch(session, cp1.id, "above", "SUCCESS",
                       {"type": "threshold_compare", "field": "action_value", "threshold": 0.5,
                        "above_branch_index": 0, "below_branch_index": 1},
                       next_cp_id="cp-2",
                       reward_map={"base_reward": 3.0})
    _make_branch(session, cp1.id, "below", "FAILURE",
                 {"type": "threshold_compare", "field": "action_value", "threshold": 0.5,
                  "above_branch_index": 0, "below_branch_index": 1})

    cp2 = _make_checkpoint(session, "tpl-1", 2, "BINARY_RISK_GATE",
                           {"type": "BINARY_RISK_GATE", "threshold": 0.3, "metric": "risk"})
    _make_branch(session, cp2.id, "above2", "SUCCESS",
                 {"type": "threshold_compare", "field": "action_value", "threshold": 0.3,
                  "above_branch_index": 0, "below_branch_index": 1},
                 reward_map={"base_reward": 2.0})
    _make_branch(session, cp2.id, "below2", "FAILURE",
                 {"type": "threshold_compare", "field": "action_value", "threshold": 0.3,
                  "above_branch_index": 0, "below_branch_index": 1})

    pack, run = _make_pack_and_run(session, "tpl-1")

    results = evaluate_checkpoints(
        session, run, seed=42,
        agent_actions={"cp-1": "0.8", "cp-2": "0.5"},
    )

    assert len(results) == 2
    # Second checkpoint should have cumulative state
    sv2 = results[1].state_vector_json
    assert sv2["cumulative_reward"] == 3.0  # from first checkpoint
    assert "SUCCESS" in sv2["previous_branch_outcomes"]
