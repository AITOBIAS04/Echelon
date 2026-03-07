"""Cycle-020 Sprint 0 — Runtime Contract Tightening tests.

4 tests:
1. All checkpoint schema fields present and typed correctly
2. Primitive JSON contract validation (valid + invalid per primitive)
3. Spawn rule contract validation
4. Paradox risk materiality rule
"""

from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import Session

from backend.database.models import (
    Base,
    ScenarioCheckpoint,
    CheckpointBranch,
    ScenarioPackTemplate,
    TheatreTemplate,
    User,
)
from backend.services.checkpoint_evaluator import (
    EVALUATOR_PRIMITIVES,
    PRIMITIVE_CONTRACTS,
    validate_checkpoint_config,
    validate_spawn_rule,
)
from backend.services.paradox_risk_orchestrator import is_material_delta


# ── Fixtures ──

def _create_tables(eng):
    tables = [
        Base.metadata.tables[t]
        for t in [
            "users",
            "theatre_templates",
            "scenario_pack_templates",
            "scenario_checkpoints",
            "checkpoint_branches",
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


# ── Test 1: Schema Fields Present ──

def test_checkpoint_schema_fields_present(session):
    """All v2-required columns exist on ScenarioCheckpoint and CheckpointBranch."""
    insp = inspect(session.bind)

    cp_cols = {c["name"] for c in insp.get_columns("scenario_checkpoints")}
    assert "trigger_condition_json" in cp_cols
    assert "evaluator_type" in cp_cols
    assert "theatre_spawn_rule_json" in cp_cols
    assert "reward_mapping_json" in cp_cols
    assert "can_spawn_theatre" in cp_cols

    br_cols = {c["name"] for c in insp.get_columns("checkpoint_branches")}
    assert "branch_rule_json" in br_cols
    assert "outcome_type" in br_cols
    assert "reward_mapping_json" in br_cols


# ── Test 2: Primitive JSON Contract Validation ──

def test_primitive_contract_validation():
    """Validate checkpoint configs per primitive — valid and invalid cases."""
    # All 5 primitives have contracts defined
    assert EVALUATOR_PRIMITIVES == set(PRIMITIVE_CONTRACTS.keys())

    # BINARY_RISK_GATE — valid
    errors = validate_checkpoint_config(
        "BINARY_RISK_GATE",
        {"type": "BINARY_RISK_GATE", "threshold": 0.65, "metric": "risk_exposure"},
        {"type": "threshold_compare", "field": "action_value", "threshold": 0.65,
         "above_branch_index": 0, "below_branch_index": 1},
    )
    assert errors == []

    # BINARY_RISK_GATE — missing trigger fields
    errors = validate_checkpoint_config(
        "BINARY_RISK_GATE",
        {"type": "BINARY_RISK_GATE"},  # missing threshold, metric
        {"type": "threshold_compare", "field": "action_value", "threshold": 0.65,
         "above_branch_index": 0, "below_branch_index": 1},
    )
    assert len(errors) == 1
    assert "missing fields" in errors[0]

    # DETECTION_EVENT — wrong branch_rule type
    errors = validate_checkpoint_config(
        "DETECTION_EVENT",
        {"type": "DETECTION_EVENT", "base_detection_probability": 0.3},
        {"type": "wrong_type", "base_probability": 0.3, "noise_amplitude": 0.1,
         "detected_branch_index": 0, "safe_branch_index": 1},
    )
    assert any("type must be" in e for e in errors)

    # Unknown evaluator_type
    errors = validate_checkpoint_config("UNKNOWN_TYPE", {}, {})
    assert any("Unknown evaluator_type" in e for e in errors)

    # None configs
    errors = validate_checkpoint_config("TIMING_BREACH", None, None)
    assert len(errors) == 2  # both required

    # MISSION_COMPLETION — valid
    errors = validate_checkpoint_config(
        "MISSION_COMPLETION",
        {"type": "MISSION_COMPLETION", "required_objectives": ["a", "b"], "min_completion": 1},
        {"type": "objective_set", "required": ["a", "b"], "min_completion": 1,
         "success_branch_index": 0, "partial_branch_index": 1, "fail_branch_index": 2},
    )
    assert errors == []

    # RESOURCE_DEPLETION — valid
    errors = validate_checkpoint_config(
        "RESOURCE_DEPLETION",
        {"type": "RESOURCE_DEPLETION", "resource": "capital", "depletion_curve": "linear"},
        {"type": "resource_bracket", "brackets": [{"min": 0, "max": 1, "branch_index": 0}],
         "field": "remaining_fraction"},
    )
    assert errors == []


# ── Test 3: Spawn Rule Validation ──

def test_spawn_rule_validation():
    """Validate theatre_spawn_rule_json contract."""
    # None is valid (no spawn rule)
    assert validate_spawn_rule(None) == []

    # Valid rule
    assert validate_spawn_rule({
        "outcome_types": ["SUCCESS"],
        "min_reward": 0.5,
        "run_modes": ["TRAINING", "EVALUATION"],
    }) == []

    # Invalid outcome_types type
    errors = validate_spawn_rule({"outcome_types": "not_a_list"})
    assert len(errors) == 1
    assert "outcome_types must be a list" in errors[0]

    # Invalid min_reward type
    errors = validate_spawn_rule({"min_reward": "not_a_number"})
    assert len(errors) == 1
    assert "min_reward must be numeric" in errors[0]

    # Empty dict is valid (all fields optional)
    assert validate_spawn_rule({}) == []


# ── Test 4: Paradox Risk Materiality Rule ──

def test_paradox_risk_materiality():
    """Material delta detection for PARADOX_RISK_CHANGED emission."""
    base_factors = {
        "logic_gap": 0.3,
        "stability": 0.7,
        "active_paradox": False,
        "material_counter_signals": 0,
        "evidence_freshness_hours": 12.0,
    }

    # Level change is always material
    assert is_material_delta("LOW", "WATCH", base_factors, base_factors) is True
    assert is_material_delta("WATCH", "HIGH", base_factors, base_factors) is True
    assert is_material_delta("HIGH", "LOW", base_factors, base_factors) is True

    # Same level, same factors = NOT material
    assert is_material_delta("LOW", "LOW", base_factors, base_factors) is False

    # Same level, but active_paradox flipped = material
    new_factors = {**base_factors, "active_paradox": True}
    assert is_material_delta("LOW", "LOW", base_factors, new_factors) is True

    # Same level, but counter-signals crossed 0->positive = material
    new_factors = {**base_factors, "material_counter_signals": 2}
    assert is_material_delta("LOW", "LOW", base_factors, new_factors) is True

    # Same level, counter-signals positive->0 = material
    old_with_cs = {**base_factors, "material_counter_signals": 3}
    assert is_material_delta("LOW", "LOW", old_with_cs, base_factors) is True

    # Same level, counter-signals 2->5 = NOT material (both positive)
    old_cs = {**base_factors, "material_counter_signals": 2}
    new_cs = {**base_factors, "material_counter_signals": 5}
    assert is_material_delta("LOW", "LOW", old_cs, new_cs) is False

    # None old_level = always material (first computation)
    assert is_material_delta(None, "LOW", None, base_factors) is True

    # None old_factors = always material
    assert is_material_delta("LOW", "LOW", None, base_factors) is True
