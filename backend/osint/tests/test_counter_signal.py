"""Tests for CounterSignalEvaluator — outcome types, allow_gap, classification.

All tests use synthetic data — no real HTTP calls.
"""
from __future__ import annotations

import pytest

from backend.osint.engine.counter_signal import (
    COUNTER_SIGNAL_CLASSES,
    CounterSignalEvaluator,
    CounterSignalOutcome,
    CounterSignalResult,
)


class TestCounterSignalEvaluator:
    """Tests for CounterSignalEvaluator."""

    def test_all_unavailable_in_011(self) -> None:
        """All 11 counter-signal classes return UNAVAILABLE in Cycle-011."""
        evaluator = CounterSignalEvaluator()
        results = evaluator.evaluate([], {})

        assert len(results) == 11
        assert len(results) == len(COUNTER_SIGNAL_CLASSES)
        for result in results:
            assert result.outcome == CounterSignalOutcome.UNAVAILABLE

    def test_unavailable_allow_gap_true_passes(self) -> None:
        """Criterion PASS when all UNAVAILABLE with allow_gap=True."""
        evaluator = CounterSignalEvaluator()
        results = evaluator.evaluate([], {})

        # All should have allow_gap=True by default
        for result in results:
            assert result.allow_gap is True

        passed, detail = CounterSignalEvaluator.check_criterion(results)
        assert passed is True
        assert "PASS" in detail

    def test_unavailable_allow_gap_false_fails(self) -> None:
        """Criterion FAIL when any UNAVAILABLE with allow_gap=False."""
        results = [
            CounterSignalResult(
                signal_class="infrastructure_outage",
                outcome=CounterSignalOutcome.UNAVAILABLE,
                source_id=None,
                detail="test",
                allow_gap=False,  # Hard requirement
            ),
        ]

        passed, detail = CounterSignalEvaluator.check_criterion(results)
        assert passed is False
        assert "FAIL" in detail
        assert "allow_gap=False" in detail

    def test_present_unexplained_fails(self) -> None:
        """Criterion FAIL when any PRESENT_UNEXPLAINED."""
        results = [
            CounterSignalResult(
                signal_class="weather",
                outcome=CounterSignalOutcome.PRESENT_UNEXPLAINED,
                source_id="weather_service",
                detail="Hurricane approaching target area",
                allow_gap=True,
            ),
        ]

        passed, detail = CounterSignalEvaluator.check_criterion(results)
        assert passed is False
        assert "FAIL" in detail
        assert "PRESENT_UNEXPLAINED" in detail

    def test_absent_passes(self) -> None:
        """ABSENT outcome passes criterion (signal checked, not present)."""
        results = [
            CounterSignalResult(
                signal_class="weather",
                outcome=CounterSignalOutcome.ABSENT,
                source_id="weather_service",
                detail="No adverse weather",
                allow_gap=True,
            ),
        ]

        passed, _ = CounterSignalEvaluator.check_criterion(results)
        assert passed is True

    def test_present_discounted_passes(self) -> None:
        """PRESENT_DISCOUNTED outcome passes criterion (signal explained)."""
        results = [
            CounterSignalResult(
                signal_class="financial_distress",
                outcome=CounterSignalOutcome.PRESENT_DISCOUNTED,
                source_id="credit_agency",
                detail="Downgrade explained by policy change",
                allow_gap=True,
            ),
        ]

        passed, _ = CounterSignalEvaluator.check_criterion(results)
        assert passed is True

    def test_intelligence_gap_classification(self) -> None:
        """UNAVAILABLE is INTELLIGENCE_GAP, not ABSENT.

        The detail text should indicate INTELLIGENCE_GAP, confirming
        that UNAVAILABLE is semantically distinct from ABSENT.
        """
        evaluator = CounterSignalEvaluator()
        results = evaluator.evaluate([], {})

        for result in results:
            assert result.outcome == CounterSignalOutcome.UNAVAILABLE
            assert result.outcome != CounterSignalOutcome.ABSENT
            assert "INTELLIGENCE_GAP" in result.detail

    def test_counter_signal_classes_count(self) -> None:
        """Exactly 11 counter-signal classes defined."""
        assert len(COUNTER_SIGNAL_CLASSES) == 11

    def test_counter_signal_class_names(self) -> None:
        """All expected class names are present."""
        expected = {
            "infrastructure_outage",
            "weather",
            "financial_distress",
            "political_transition",
            "sanctions_change",
            "military_mobilisation",
            "cyber_attack",
            "pandemic_outbreak",
            "natural_disaster",
            "social_unrest",
            "regulatory_change",
        }
        assert set(COUNTER_SIGNAL_CLASSES) == expected

    def test_mixed_outcomes_with_unexplained_fails(self) -> None:
        """Mixed outcomes where one is PRESENT_UNEXPLAINED causes FAIL."""
        results = [
            CounterSignalResult(
                signal_class="weather",
                outcome=CounterSignalOutcome.ABSENT,
                source_id="weather_svc",
                detail="Clear",
            ),
            CounterSignalResult(
                signal_class="financial_distress",
                outcome=CounterSignalOutcome.PRESENT_DISCOUNTED,
                source_id="credit_svc",
                detail="Explained",
            ),
            CounterSignalResult(
                signal_class="cyber_attack",
                outcome=CounterSignalOutcome.PRESENT_UNEXPLAINED,
                source_id="cyber_svc",
                detail="Active DDoS",
            ),
        ]

        passed, detail = CounterSignalEvaluator.check_criterion(results)
        assert passed is False
