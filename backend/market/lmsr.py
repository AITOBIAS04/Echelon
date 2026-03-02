"""Logarithmic Market Scoring Rule — pure cost-function market maker.

All functions are static and pure: no side effects, no state mutation, no I/O.
Uses log-sum-exp trick for numerical stability.

Specification (Echelon System Bible v13, Section III):
    Cost function:  C(x) = b * ln(sum_j exp(x_j / b))
    Price function: p_i(x) = exp(x_i / b) / sum_j exp(x_j / b)
    Trade cost:     cost(delta | x) = C(x + delta) - C(x)
    Worst-case:     L(b, n) = b * ln(n)
"""
from __future__ import annotations

import math


class LMSREngine:
    """Pure LMSR cost-function market maker."""

    @staticmethod
    def cost(x: list[float], b: float) -> float:
        """C(x) = b * ln(sum_j exp(x_j / b))

        Uses log-sum-exp trick: C(x) = b * (m + ln(sum_j exp(x_j/b - m)))
        where m = max(x_j / b). Prevents overflow for large x_j/b.
        """
        scaled = [xi / b for xi in x]
        m = max(scaled)
        log_sum = m + math.log(math.fsum(math.exp(s - m) for s in scaled))
        return b * log_sum

    @staticmethod
    def prices(x: list[float], b: float) -> list[float]:
        """p_i(x) = exp(x_i / b) / sum_j exp(x_j / b)

        Equivalent to softmax(x / b). Uses log-sum-exp for stability.
        Returns list of len(x) probabilities summing to 1.0.
        """
        scaled = [xi / b for xi in x]
        m = max(scaled)
        exps = [math.exp(s - m) for s in scaled]
        total = math.fsum(exps)
        return [e / total for e in exps]

    @staticmethod
    def trade_cost(x: list[float], delta: list[float], b: float) -> float:
        """cost(delta | x) = C(x + delta) - C(x)

        The amount the trader pays (positive) or receives (negative).
        """
        x_new = [xi + di for xi, di in zip(x, delta)]
        return LMSREngine.cost(x_new, b) - LMSREngine.cost(x, b)

    @staticmethod
    def worst_case_loss(b: float, n_outcomes: int) -> float:
        """Maximum market maker loss = b * ln(n)."""
        return b * math.log(n_outcomes)

    @staticmethod
    def validate_prices(prices: list[float], tolerance: float = 1e-9) -> bool:
        """Verify: all prices in [0,1], sum = 1.0 within tolerance."""
        if not all(0.0 <= p <= 1.0 for p in prices):
            return False
        return abs(math.fsum(prices) - 1.0) <= tolerance
