"""LMSR invariant tests and fixture validation.

Tests the pure LMSR cost function against mathematical invariants
and known test vectors from the quant fixture suites.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

from backend.market.lmsr import LMSREngine

TOLERANCE = 1e-9

# Repo root for fixture loading
REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURES_DIR = REPO_ROOT / "theatre" / "fixtures" / "echelon_quant_v0_2"


# --- Invariant tests ---


class TestPricesSimplex:
    """Prices must always lie on the probability simplex."""

    @pytest.mark.parametrize(
        "x, b",
        [
            ([0.0, 0.0, 0.0], 10.0),
            ([50.0, 0.0, 0.0], 10.0),
            ([10.0, 20.0, 30.0], 50.0),
            ([0.0, 0.0], 1.0),
            ([100.0, -50.0, 25.0, 0.0], 80.0),
        ],
    )
    def test_prices_sum_to_one(self, x: list[float], b: float) -> None:
        prices = LMSREngine.prices(x, b)
        assert abs(math.fsum(prices) - 1.0) < TOLERANCE

    @pytest.mark.parametrize(
        "x, b",
        [
            ([0.0, 0.0, 0.0], 10.0),
            ([50.0, 0.0, 0.0], 10.0),
            ([100.0, -50.0, 25.0, 0.0], 80.0),
        ],
    )
    def test_prices_all_in_unit_interval(self, x: list[float], b: float) -> None:
        prices = LMSREngine.prices(x, b)
        for p in prices:
            assert 0.0 <= p <= 1.0

    @pytest.mark.parametrize("n", [2, 3, 5, 10])
    def test_initial_prices_uniform(self, n: int) -> None:
        x = [0.0] * n
        prices = LMSREngine.prices(x, 10.0)
        expected = 1.0 / n
        for p in prices:
            assert abs(p - expected) < TOLERANCE


class TestTradeCost:
    """Trade cost invariants."""

    @pytest.mark.parametrize(
        "x, b",
        [
            ([0.0, 0.0, 0.0], 10.0),
            ([50.0, 0.0, 0.0], 10.0),
            ([0.0, 0.0], 100.0),
        ],
    )
    def test_zero_delta_costs_zero(self, x: list[float], b: float) -> None:
        delta = [0.0] * len(x)
        assert LMSREngine.trade_cost(x, delta, b) == 0.0

    @pytest.mark.parametrize(
        "x, delta, b",
        [
            ([0.0, 0.0, 0.0], [50.0, 0.0, 0.0], 10.0),
            ([10.0, 20.0], [5.0, -3.0], 50.0),
            ([0.0, 0.0, 0.0], [10.0, -5.0, 0.0], 40.0),
        ],
    )
    def test_trade_cost_reversibility(
        self, x: list[float], delta: list[float], b: float
    ) -> None:
        forward = LMSREngine.trade_cost(x, delta, b)
        x_new = [xi + di for xi, di in zip(x, delta)]
        neg_delta = [-di for di in delta]
        reverse = LMSREngine.trade_cost(x_new, neg_delta, b)
        assert abs(forward + reverse) < TOLERANCE


class TestWorstCaseLoss:
    """Worst-case market maker loss formula."""

    @pytest.mark.parametrize(
        "b, n",
        [(10.0, 3), (20.0, 2), (100.0, 5), (1.0, 10), (160.0, 3)],
    )
    def test_worst_case_loss_formula(self, b: float, n: int) -> None:
        expected = b * math.log(n)
        actual = LMSREngine.worst_case_loss(b, n)
        assert abs(actual - expected) < TOLERANCE


class TestValidatePrices:
    """Price validation utility."""

    def test_validate_prices_valid(self) -> None:
        assert LMSREngine.validate_prices([0.5, 0.3, 0.2]) is True

    def test_validate_prices_invalid_sum(self) -> None:
        assert LMSREngine.validate_prices([0.5, 0.5, 0.5]) is False

    def test_validate_prices_negative(self) -> None:
        assert LMSREngine.validate_prices([-0.1, 0.6, 0.5]) is False

    def test_validate_prices_over_one(self) -> None:
        assert LMSREngine.validate_prices([1.1, -0.05, -0.05]) is False


# --- Fixture validation tests ---


class TestBSensitivityFixtures:
    """Validate against b-sensitivity fixture suite (5 records)."""

    @pytest.fixture()
    def fixture_data(self) -> list[dict]:
        path = (
            FIXTURES_DIR
            / "b_sensitivity_suite_v0_1"
            / "b_sensitivity_fixtures_5.json"
        )
        with open(path) as f:
            data = json.load(f)
        return data["records"]

    def test_b_sensitivity_fixture_vectors(self, fixture_data: list[dict]) -> None:
        """All 5 fixture cost_paid values match the live engine."""
        for record in fixture_data:
            inputs = record["inputs"]
            b = inputs["b"]
            trade = inputs["trade"]
            x0 = trade["x0"]
            n = trade["n_outcomes"]
            delta_shares = trade["delta"]
            j = trade["j"]

            # Build one-hot delta
            delta = [0.0] * n
            delta[j] = delta_shares

            actual_cost = LMSREngine.trade_cost(x0, delta, b)
            expected_cost = record["expected_outputs"]["execution"]["cost_paid"]
            assert abs(actual_cost - expected_cost) < TOLERANCE, (
                f"b={b}: expected {expected_cost}, got {actual_cost}"
            )

    def test_b_sensitivity_impact_monotonic(self, fixture_data: list[dict]) -> None:
        """Price impact decreases as b increases."""
        impacts = []
        for record in fixture_data:
            inputs = record["inputs"]
            b = inputs["b"]
            trade = inputs["trade"]
            x0 = trade["x0"]
            n = trade["n_outcomes"]
            delta_shares = trade["delta"]
            j = trade["j"]

            delta = [0.0] * n
            delta[j] = delta_shares

            # Impact = avg_execution_price - initial_price
            initial_prices = LMSREngine.prices(x0, b)
            x_new = [xi + di for xi, di in zip(x0, delta)]
            final_prices = LMSREngine.prices(x_new, b)
            impact = final_prices[j] - initial_prices[j]
            impacts.append((b, impact))

        # Verify monotonically decreasing impact as b increases
        for i in range(len(impacts) - 1):
            assert impacts[i][1] > impacts[i + 1][1], (
                f"Impact should decrease: b={impacts[i][0]} impact={impacts[i][1]} "
                f"vs b={impacts[i+1][0]} impact={impacts[i+1][1]}"
            )

    def test_b_sensitivity_mm_bound(self, fixture_data: list[dict]) -> None:
        """Market maker bound matches b * ln(n) for each record."""
        for record in fixture_data:
            b = record["inputs"]["b"]
            n = record["inputs"]["trade"]["n_outcomes"]
            expected = record["expected_outputs"]["execution"]["mm_bound"]
            actual = LMSREngine.worst_case_loss(b, n)
            assert abs(actual - expected) < TOLERANCE


class TestHygieneFixtures:
    """Validate against hygiene fixture suite (first record)."""

    @pytest.fixture()
    def record(self) -> dict:
        path = (
            FIXTURES_DIR
            / "quant_market_hygiene_v0_1"
            / "quant_market_hygiene_fixtures_10.json"
        )
        with open(path) as f:
            data = json.load(f)
        return data["records"][0]  # qmhy_0001

    def test_hygiene_fixture_state_after(self, record: dict) -> None:
        """Match qmhy_0001 state_after prices and C."""
        inputs = record["inputs"]
        b = inputs["market_spec"]["b"]
        x0 = inputs["state_before"]["x"]
        trade = inputs["trade"]
        outcome_idx = trade["outcome_index"]
        delta_shares = trade["delta_shares"]

        # Build one-hot delta
        n = len(x0)
        delta = [0.0] * n
        delta[outcome_idx] = delta_shares

        x_new = [xi + di for xi, di in zip(x0, delta)]

        # Verify post-trade state
        expected = record["expected_outputs"]
        assert x_new == expected["state_after"]["x"]

        actual_c = LMSREngine.cost(x_new, b)
        assert abs(actual_c - expected["state_after"]["C"]) < TOLERANCE

        actual_prices = LMSREngine.prices(x_new, b)
        expected_prices = expected["state_after"]["prices"]
        for ap, ep in zip(actual_prices, expected_prices):
            assert abs(ap - ep) < TOLERANCE

    def test_hygiene_fixture_trade_cost(self, record: dict) -> None:
        """Match qmhy_0001 cost_paid."""
        inputs = record["inputs"]
        b = inputs["market_spec"]["b"]
        x0 = inputs["state_before"]["x"]
        trade = inputs["trade"]
        outcome_idx = trade["outcome_index"]
        delta_shares = trade["delta_shares"]

        n = len(x0)
        delta = [0.0] * n
        delta[outcome_idx] = delta_shares

        actual = LMSREngine.trade_cost(x0, delta, b)
        expected = record["expected_outputs"]["execution"]["cost_paid"]
        assert abs(actual - expected) < TOLERANCE
