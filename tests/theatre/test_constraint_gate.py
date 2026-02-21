"""Tests for Constraint Yielding Gate — review preference resolution."""

import pytest

from theatre.engine.constraint_gate import ConstraintYieldingGate


class TestConstraintYieldingGate:
    def test_unverified_skip_becomes_full(self):
        result = ConstraintYieldingGate.resolve_review_preference("UNVERIFIED", "skip")
        assert result == "full"

    def test_unverified_full_stays_full(self):
        result = ConstraintYieldingGate.resolve_review_preference("UNVERIFIED", "full")
        assert result == "full"

    def test_backtested_skip_stays_skip(self):
        result = ConstraintYieldingGate.resolve_review_preference("BACKTESTED", "skip")
        assert result == "skip"

    def test_backtested_full_stays_full(self):
        result = ConstraintYieldingGate.resolve_review_preference("BACKTESTED", "full")
        assert result == "full"

    def test_proven_skip_stays_skip(self):
        result = ConstraintYieldingGate.resolve_review_preference("PROVEN", "skip")
        assert result == "skip"

    def test_proven_full_stays_full(self):
        result = ConstraintYieldingGate.resolve_review_preference("PROVEN", "full")
        assert result == "full"
