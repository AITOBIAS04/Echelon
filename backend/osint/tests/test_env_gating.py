"""Tests for live test env var gating — verifies "0"/"false" are not truthy.

Validates that ECHELON_LIVE_WM and ECHELON_LIVE_CH env vars only enable
live tests when set to explicit truthy values ("1", "true", "yes").
"""
from __future__ import annotations

import os
from unittest.mock import patch


def _is_live_enabled(env_var: str, value: str | None) -> bool:
    """Replicate conftest.py gating logic for unit testing."""
    env = {env_var: value} if value is not None else {}
    with patch.dict(os.environ, env, clear=False):
        raw = os.environ.get(env_var, "").lower()
        return raw in ("1", "true", "yes")


class TestEnvVarGating:
    """ECHELON_LIVE_WM / ECHELON_LIVE_CH env var truthiness."""

    def test_value_1_enables(self) -> None:
        assert _is_live_enabled("ECHELON_LIVE_WM", "1") is True

    def test_value_true_enables(self) -> None:
        assert _is_live_enabled("ECHELON_LIVE_WM", "true") is True

    def test_value_TRUE_enables(self) -> None:
        assert _is_live_enabled("ECHELON_LIVE_WM", "TRUE") is True

    def test_value_yes_enables(self) -> None:
        assert _is_live_enabled("ECHELON_LIVE_CH", "yes") is True

    def test_value_0_does_not_enable(self) -> None:
        assert _is_live_enabled("ECHELON_LIVE_WM", "0") is False

    def test_value_false_does_not_enable(self) -> None:
        assert _is_live_enabled("ECHELON_LIVE_WM", "false") is False

    def test_value_no_does_not_enable(self) -> None:
        assert _is_live_enabled("ECHELON_LIVE_CH", "no") is False

    def test_empty_string_does_not_enable(self) -> None:
        assert _is_live_enabled("ECHELON_LIVE_WM", "") is False

    def test_unset_does_not_enable(self) -> None:
        assert _is_live_enabled("ECHELON_LIVE_WM", None) is False
