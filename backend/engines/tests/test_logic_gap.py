"""Logic Gap Calculator tests — smoothing, classification, boundaries."""
from __future__ import annotations

from backend.engines.logic_gap import LogicGapCalculator, LogicGapStatus

TOLERANCE = 1e-9


class TestSmoothing:
    """Price smoothing over trailing window."""

    def test_single_price_returns_itself(self) -> None:
        calc = LogicGapCalculator(smoothing_window_s=60.0)
        calc.record_price("t1", 0.70, timestamp_s=100.0)
        assert calc.get_smoothed_p_market("t1") == 0.70

    def test_average_of_two_prices(self) -> None:
        calc = LogicGapCalculator(smoothing_window_s=60.0)
        calc.record_price("t1", 0.60, timestamp_s=100.0)
        calc.record_price("t1", 0.80, timestamp_s=110.0)
        assert abs(calc.get_smoothed_p_market("t1") - 0.70) < TOLERANCE

    def test_old_prices_pruned(self) -> None:
        calc = LogicGapCalculator(smoothing_window_s=10.0)
        calc.record_price("t1", 0.30, timestamp_s=100.0)
        calc.record_price("t1", 0.70, timestamp_s=115.0)
        # First entry (t=100) is outside window (115-10=105 cutoff)
        assert calc.get_smoothed_p_market("t1") == 0.70

    def test_no_prices_returns_midpoint(self) -> None:
        calc = LogicGapCalculator()
        assert calc.get_smoothed_p_market("t1") == 0.5

    def test_multiple_prices_within_window(self) -> None:
        calc = LogicGapCalculator(smoothing_window_s=60.0)
        calc.record_price("t1", 0.40, timestamp_s=100.0)
        calc.record_price("t1", 0.50, timestamp_s=120.0)
        calc.record_price("t1", 0.60, timestamp_s=140.0)
        expected = (0.40 + 0.50 + 0.60) / 3
        assert abs(calc.get_smoothed_p_market("t1") - expected) < TOLERANCE


class TestClassification:
    """Logic Gap status classification."""

    def test_healthy_below_20(self) -> None:
        assert LogicGapCalculator.classify(0.0) == LogicGapStatus.HEALTHY
        assert LogicGapCalculator.classify(0.10) == LogicGapStatus.HEALTHY
        assert LogicGapCalculator.classify(0.19) == LogicGapStatus.HEALTHY

    def test_stressed_20_to_40(self) -> None:
        assert LogicGapCalculator.classify(0.20) == LogicGapStatus.STRESSED
        assert LogicGapCalculator.classify(0.30) == LogicGapStatus.STRESSED
        assert LogicGapCalculator.classify(0.39) == LogicGapStatus.STRESSED

    def test_danger_40_to_60(self) -> None:
        assert LogicGapCalculator.classify(0.40) == LogicGapStatus.DANGER
        assert LogicGapCalculator.classify(0.50) == LogicGapStatus.DANGER
        assert LogicGapCalculator.classify(0.59) == LogicGapStatus.DANGER

    def test_critical_60_and_above(self) -> None:
        assert LogicGapCalculator.classify(0.60) == LogicGapStatus.CRITICAL
        assert LogicGapCalculator.classify(0.80) == LogicGapStatus.CRITICAL
        assert LogicGapCalculator.classify(1.0) == LogicGapStatus.CRITICAL


class TestCompute:
    """Full Logic Gap computation."""

    def test_logic_gap_is_abs_difference(self) -> None:
        calc = LogicGapCalculator()
        calc.record_price("t1", 0.70, timestamp_s=100.0)
        reading = calc.compute("t1", p_reality=0.40)
        assert abs(reading.logic_gap - 0.30) < TOLERANCE

    def test_gap_direction_signed(self) -> None:
        calc = LogicGapCalculator()
        calc.record_price("t1", 0.70, timestamp_s=100.0)
        reading = calc.compute("t1", p_reality=0.40)
        assert abs(reading.gap_direction - 0.30) < TOLERANCE  # market > reality

    def test_gap_direction_negative_when_reality_higher(self) -> None:
        calc = LogicGapCalculator()
        calc.record_price("t1", 0.30, timestamp_s=100.0)
        reading = calc.compute("t1", p_reality=0.70)
        assert abs(reading.gap_direction - (-0.40)) < TOLERANCE

    def test_reading_has_correct_fields(self) -> None:
        calc = LogicGapCalculator(smoothing_window_s=30.0)
        calc.record_price("t1", 0.50, timestamp_s=100.0)
        reading = calc.compute("t1", p_reality=0.50)
        assert reading.theatre_id == "t1"
        assert reading.p_market == 0.50
        assert reading.p_reality == 0.50
        assert reading.logic_gap == 0.0
        assert reading.status == LogicGapStatus.HEALTHY
        assert reading.smoothing_window_s == 30.0
        assert reading.timestamp != ""

    def test_edge_values(self) -> None:
        calc = LogicGapCalculator()
        calc.record_price("t1", 0.0, timestamp_s=100.0)
        reading = calc.compute("t1", p_reality=1.0)
        assert abs(reading.logic_gap - 1.0) < TOLERANCE
        assert reading.status == LogicGapStatus.CRITICAL
