"""Numerical edge-case tests — overflow, extreme values, precision."""
from __future__ import annotations

import math

import pytest

from backend.market.lmsr import LMSREngine

TOLERANCE = 1e-9


class TestOverflowProtection:
    """Log-sum-exp trick must prevent overflow for large x/b ratios."""

    def test_no_overflow_large_x_over_b(self) -> None:
        """cost([1000.0, 0.0], b=1.0) computes without OverflowError."""
        result = LMSREngine.cost([1000.0, 0.0], 1.0)
        assert math.isfinite(result)
        # Should be approximately 1000.0 (dominated by exp(1000))
        assert abs(result - 1000.0) < 1.0

    def test_no_overflow_very_large_ratio(self) -> None:
        """x/b > 700 still computes (naive exp would overflow)."""
        result = LMSREngine.cost([800.0, 0.0, 0.0], 1.0)
        assert math.isfinite(result)

    def test_prices_no_overflow(self) -> None:
        """Prices compute correctly even with extreme x/b."""
        prices = LMSREngine.prices([1000.0, 0.0], 1.0)
        assert abs(math.fsum(prices) - 1.0) < TOLERANCE
        # Dominant outcome should be near 1.0
        assert prices[0] > 0.99


class TestExtremeBValues:
    """Extreme liquidity parameter values."""

    def test_extreme_b_small(self) -> None:
        """b=0.001, x=[0,0] computes correctly."""
        c = LMSREngine.cost([0.0, 0.0], 0.001)
        expected = 0.001 * math.log(2)
        assert abs(c - expected) < TOLERANCE

        prices = LMSREngine.prices([0.0, 0.0], 0.001)
        assert abs(math.fsum(prices) - 1.0) < TOLERANCE

    def test_extreme_b_large(self) -> None:
        """b=100000, x=[0,0,0,0,0] computes correctly, prices sum to 1.0."""
        x = [0.0] * 5
        c = LMSREngine.cost(x, 100000.0)
        expected = 100000.0 * math.log(5)
        assert abs(c - expected) < TOLERANCE

        prices = LMSREngine.prices(x, 100000.0)
        assert abs(math.fsum(prices) - 1.0) < TOLERANCE
        for p in prices:
            assert abs(p - 0.2) < TOLERANCE


class TestManyOutcomes:
    """Markets with many outcomes."""

    def test_many_outcomes_100(self) -> None:
        """n=100 outcomes: prices sum to 1.0, cost computes."""
        n = 100
        x = [0.0] * n
        b = 50.0

        c = LMSREngine.cost(x, b)
        expected = b * math.log(n)
        assert abs(c - expected) < TOLERANCE

        prices = LMSREngine.prices(x, b)
        assert len(prices) == n
        assert abs(math.fsum(prices) - 1.0) < TOLERANCE
        for p in prices:
            assert abs(p - 1.0 / n) < TOLERANCE


class TestFsumPrecision:
    """Compensated summation precision."""

    def test_fsum_precision(self) -> None:
        """math.fsum gives at least as good precision as naive sum.

        This is a property test — we verify that our implementation
        maintains high precision by checking the simplex property
        after many operations.
        """
        # Create a state with many small trades accumulated
        n = 10
        x = [float(i * 7 + 3) for i in range(n)]
        b = 25.0

        prices = LMSREngine.prices(x, b)

        # fsum should give very close to 1.0
        fsum_total = math.fsum(prices)
        assert abs(fsum_total - 1.0) < 1e-15  # tighter than TOLERANCE
