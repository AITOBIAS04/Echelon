"""Cycle-020 Sprint 3 — Derived Theatre Rules + Run Integrity tests.

Tests:
1. should_spawn with outcome_types filter
2. should_spawn with min_reward filter
3. should_spawn with run_modes filter
4. Backward compat: can_spawn_theatre=True with no rule -> spawns
5. Backward compat: can_spawn_theatre=False with no rule -> no spawn
"""

import pytest
from unittest.mock import MagicMock

from backend.services.theatre_spawner import should_spawn


def _mock_branch(outcome_type="SUCCESS"):
    branch = MagicMock()
    branch.outcome_type = outcome_type
    return branch


def _mock_checkpoint(evaluator_type="BINARY_RISK_GATE", can_spawn=False):
    cp = MagicMock()
    cp.evaluator_type = evaluator_type
    cp.can_spawn_theatre = can_spawn
    return cp


def test_spawn_rule_outcome_types():
    rule = {"outcome_types": ["SUCCESS", "PARTIAL_SUCCESS"]}

    assert should_spawn(rule, _mock_branch("SUCCESS"), 1.0, "TRAINING", _mock_checkpoint()) is True
    assert should_spawn(rule, _mock_branch("FAILURE"), 1.0, "TRAINING", _mock_checkpoint()) is False
    assert should_spawn(rule, _mock_branch("PARTIAL_SUCCESS"), 1.0, "TRAINING", _mock_checkpoint()) is True


def test_spawn_rule_min_reward():
    rule = {"min_reward": 0.5}

    assert should_spawn(rule, _mock_branch(), 1.0, "TRAINING", _mock_checkpoint()) is True
    assert should_spawn(rule, _mock_branch(), 0.5, "TRAINING", _mock_checkpoint()) is True
    assert should_spawn(rule, _mock_branch(), 0.3, "TRAINING", _mock_checkpoint()) is False


def test_spawn_rule_run_modes():
    rule = {"run_modes": ["TRAINING", "EVALUATION"]}

    assert should_spawn(rule, _mock_branch(), 1.0, "TRAINING", _mock_checkpoint()) is True
    assert should_spawn(rule, _mock_branch(), 1.0, "EVALUATION", _mock_checkpoint()) is True
    assert should_spawn(rule, _mock_branch(), 1.0, "CALIBRATION", _mock_checkpoint()) is False
    assert should_spawn(rule, _mock_branch(), 1.0, "REPLAY", _mock_checkpoint()) is False


def test_backward_compat_can_spawn_true():
    """No spawn rule + can_spawn_theatre=True -> spawn unconditionally."""
    cp = _mock_checkpoint(can_spawn=True)
    assert should_spawn(None, _mock_branch(), 0.0, "TRAINING", cp) is True


def test_backward_compat_can_spawn_false():
    """No spawn rule + can_spawn_theatre=False -> no spawn."""
    cp = _mock_checkpoint(can_spawn=False)
    assert should_spawn(None, _mock_branch(), 1.0, "TRAINING", cp) is False
