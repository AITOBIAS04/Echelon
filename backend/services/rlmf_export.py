"""RLMF Export Generator -- training data export from Theatre lifecycle.

Produces RLMF training data conforming to schema v2.0.1. Captures
probability distributions at each market epoch, agent decision traces,
calibration metrics (Brier score, ECE), and per-agent P&L.

Cycle-012, Sprint 2 -- Task 4.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

from backend.market.resolution import SettlementReport
from backend.services.theatre_resolution import TheatreResolutionResult


@dataclass
class MarketEpoch:
    """Single tick of market state for RLMF export."""

    tick: int
    timestamp: str
    prices: list[float]
    x_vector: list[float]
    total_trades: int
    trade_count_this_tick: int


@dataclass
class AgentTrace:
    """Per-agent trading trace for RLMF export."""

    agent_id: str
    archetype: str
    initial_balance: float
    final_balance: float
    total_trades: int
    total_pnl: float
    decision_traces: list[dict[str, Any]]


@dataclass
class CalibrationMetrics:
    """Calibration quality metrics for the RLMF export."""

    brier_score: float
    expected_calibration_error: float
    resolution: float
    reliability: float


@dataclass
class RLMFExport:
    """RLMF training data export (schema v2.0.1)."""

    schema_version: str
    oracle_output_id: str
    theatre_id: str
    question: str
    outcome_labels: list[str]
    winning_outcome: int
    winning_outcome_label: str
    epochs: list[dict[str, Any]]
    agent_traces: list[dict[str, Any]]
    calibration: dict[str, Any]
    agent_pnl: dict[str, float]
    composite_score: float
    evidence_bundle_hash: str
    settlement_hash: str
    exported_at: str


class RLMFExportGenerator:
    """Generates RLMF training data exports from Theatre lifecycle data.

    SCHEMA_VERSION = "2.0.1"
    """

    SCHEMA_VERSION = "2.0.1"

    def generate(
        self,
        theatre_id: str,
        question: str,
        outcome_labels: list[str],
        winning_outcome: int,
        oracle_output_id: str,
        epochs: list[MarketEpoch],
        agent_traces: list[AgentTrace],
        settlement_report: SettlementReport,
        resolution_result: TheatreResolutionResult,
    ) -> RLMFExport:
        """Generate an RLMF export from Theatre lifecycle data."""
        # Compute calibration metrics
        final_prices = epochs[-1].prices if epochs else [1.0 / len(outcome_labels)] * len(outcome_labels)
        brier = self.compute_brier_score(final_prices, winning_outcome)
        ece = self.compute_ece(epochs, winning_outcome)

        calibration = CalibrationMetrics(
            brier_score=brier,
            expected_calibration_error=ece,
            resolution=1.0 - brier,  # Resolution = 1 - Brier (simplified)
            reliability=max(0.0, 1.0 - ece),
        )

        # Build per-agent P&L dict from settlement report
        agent_pnl: dict[str, float] = {}
        for settlement in settlement_report.agent_settlements:
            agent_pnl[settlement.agent_id] = settlement.realised_pnl

        # Serialise epochs
        epoch_dicts = [
            {
                "tick": e.tick,
                "timestamp": e.timestamp,
                "prices": e.prices,
                "x_vector": e.x_vector,
                "total_trades": e.total_trades,
                "trade_count_this_tick": e.trade_count_this_tick,
            }
            for e in epochs
        ]

        # Serialise agent traces
        trace_dicts = [
            {
                "agent_id": t.agent_id,
                "archetype": t.archetype,
                "initial_balance": t.initial_balance,
                "final_balance": t.final_balance,
                "total_trades": t.total_trades,
                "total_pnl": t.total_pnl,
                "decision_traces": t.decision_traces,
            }
            for t in agent_traces
        ]

        return RLMFExport(
            schema_version=self.SCHEMA_VERSION,
            oracle_output_id=oracle_output_id,
            theatre_id=theatre_id,
            question=question,
            outcome_labels=outcome_labels,
            winning_outcome=winning_outcome,
            winning_outcome_label=outcome_labels[winning_outcome],
            epochs=epoch_dicts,
            agent_traces=trace_dicts,
            calibration={
                "brier_score": calibration.brier_score,
                "expected_calibration_error": calibration.expected_calibration_error,
                "resolution": calibration.resolution,
                "reliability": calibration.reliability,
            },
            agent_pnl=agent_pnl,
            composite_score=resolution_result.composite_score,
            evidence_bundle_hash=resolution_result.evidence_bundle_hash,
            settlement_hash=settlement_report.settlement_hash,
            exported_at=datetime.now(timezone.utc).isoformat(),
        )

    @staticmethod
    def compute_brier_score(final_prices: list[float], winning_outcome: int) -> float:
        """Compute Brier score: (1/n) * sum((p_i - o_i)^2).

        Where o_i = 1 if i == winning_outcome else 0.
        Lower is better. Perfect = 0.0, worst = 1.0.
        """
        n = len(final_prices)
        if n == 0:
            return 1.0

        total = 0.0
        for i, p in enumerate(final_prices):
            o = 1.0 if i == winning_outcome else 0.0
            total += (p - o) ** 2

        return total / n

    @staticmethod
    def compute_ece(
        epochs: list[MarketEpoch],
        winning_outcome: int,
        n_bins: int = 10,
    ) -> float:
        """Compute Expected Calibration Error across probability bins.

        Groups price observations for the winning outcome into bins,
        computes the average predicted probability and actual frequency
        per bin, then takes weighted average of |avg_p - actual_freq|.
        """
        if not epochs:
            return 0.0

        # Collect all price observations for the winning outcome
        bin_counts: list[int] = [0] * n_bins
        bin_sum_p: list[float] = [0.0] * n_bins
        # For ECE, the "actual" is 1 for all observations since winning_outcome is known
        total_observations = 0

        for epoch in epochs:
            if winning_outcome < len(epoch.prices):
                p = epoch.prices[winning_outcome]
                bin_idx = min(int(p * n_bins), n_bins - 1)
                bin_counts[bin_idx] += 1
                bin_sum_p[bin_idx] += p
                total_observations += 1

        if total_observations == 0:
            return 0.0

        # ECE = sum over bins of (count/total) * |avg_p - actual_freq|
        # For a resolved market, actual_freq per bin is the proportion
        # of observations in that bin where the outcome occurred (= 1 always)
        ece = 0.0
        for i in range(n_bins):
            if bin_counts[i] == 0:
                continue
            avg_p = bin_sum_p[i] / bin_counts[i]
            actual_freq = 1.0  # The winning outcome occurred
            weight = bin_counts[i] / total_observations
            ece += weight * abs(avg_p - actual_freq)

        return ece
