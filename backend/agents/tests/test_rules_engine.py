"""Tests for T1 Rules Engine.

Covers per-archetype decision correctness, confidence scoring,
escalation flagging, determinism, and options_considered population.

Cycle-013, Sprint 1 -- Task 7.
"""
from __future__ import annotations

import pytest

from backend.agents.context_compiler import T0Context
from backend.agents.rules_engine import (
    MOMENTUM_THRESHOLD,
    ActionOption,
    RulesEngine,
    T1Decision,
    TradeAction,
)


# ===================================================================
# Fixtures
# ===================================================================


def _make_t0(
    archetype: str = "SHARK",
    prices: tuple = (0.5, 0.3, 0.2),
    risk_appetite: float = 0.85,
    evidence_sensitivity: float = 0.70,
    time_preference: float = 0.95,
    exploration_rate: float = 0.15,
    position_limit: float = 10_000.0,
    sabotage_propensity: float = 0.30,
    shield_propensity: float = 0.10,
    patience: int = 30,
    novelty_threshold: float = 0.6,
    evidence_coverage_pct: float = 0.0,
    current_shares: tuple = (0.0, 0.0, 0.0),
    net_cashflow: float = 0.0,
    available_balance: float = 1000.0,
    phase: str = "TRADING",
) -> T0Context:
    """Create a T0Context for testing with sensible defaults."""
    n = len(prices)
    ctx = T0Context(
        archetype=archetype,
        risk_appetite=risk_appetite,
        evidence_sensitivity=evidence_sensitivity,
        time_preference=time_preference,
        exploration_rate=exploration_rate,
        position_limit=position_limit,
        sabotage_propensity=sabotage_propensity,
        shield_propensity=shield_propensity,
        patience=patience,
        novelty_threshold=novelty_threshold,
        prices=prices,
        phase=phase,
        outcome_labels=tuple(f"o{i}" for i in range(n)),
        n_outcomes=n,
        evidence_coverage_pct=evidence_coverage_pct,
        current_shares=current_shares,
        net_cashflow=net_cashflow,
        available_balance=available_balance,
        committed_sources=(),
        resolution_date="",
        liquidity_b=100.0,
        max_position_pct=0.10,
        max_drawdown_pct=0.20,
        stop_loss_threshold=0.15,
        context_hash="test_hash",
    )
    return ctx


# ===================================================================
# Tests
# ===================================================================


class TestRulesEngine:
    """Tests for the parameterised T1 decision engine."""

    def test_shark_momentum_buy(self) -> None:
        """Shark buys leading outcome when momentum signal present."""
        # Prices with outcome 0 leading significantly above uniform (0.333)
        ctx = _make_t0(
            archetype="SHARK",
            prices=(0.6, 0.25, 0.15),
            risk_appetite=0.85,
            available_balance=1000.0,
        )
        engine = RulesEngine()
        decision = engine.decide(ctx, tick=0, rng_seed=42)

        assert decision.action == TradeAction.BUY
        assert decision.outcome_index == 0
        assert decision.shares > 0
        assert decision.pattern_name == "momentum_exploitation"
        assert len(decision.options_considered) >= 1

    def test_shark_hold_no_momentum(self) -> None:
        """Shark holds when no momentum signal (uniform prices)."""
        ctx = _make_t0(
            archetype="SHARK",
            prices=(0.34, 0.33, 0.33),
            risk_appetite=0.85,
        )
        engine = RulesEngine()
        decision = engine.decide(ctx, tick=0, rng_seed=42)

        assert decision.action == TradeAction.HOLD
        assert decision.pattern_name == "momentum_exploitation"

    def test_spy_trades_on_evidence(self) -> None:
        """Spy trades when evidence is present and sensitivity is high."""
        ctx = _make_t0(
            archetype="SPY",
            evidence_sensitivity=0.90,
            evidence_coverage_pct=0.5,
            available_balance=1000.0,
        )
        engine = RulesEngine()
        decision = engine.decide(ctx, tick=0, rng_seed=42)

        assert decision.action == TradeAction.BUY
        assert decision.pattern_name == "intel_arbitrage"
        assert decision.confidence > 0.5

    def test_spy_holds_without_evidence(self) -> None:
        """Spy holds when no evidence available."""
        ctx = _make_t0(
            archetype="SPY",
            evidence_sensitivity=0.90,
            evidence_coverage_pct=0.0,
        )
        engine = RulesEngine()
        decision = engine.decide(ctx, tick=0, rng_seed=42)

        assert decision.action == TradeAction.HOLD
        assert decision.pattern_name == "intel_arbitrage"

    def test_diplomat_buys_trailing_on_high_spread(self) -> None:
        """Diplomat buys trailing outcome when spread exceeds threshold."""
        # High spread: 0.7 - 0.1 = 0.6
        ctx = _make_t0(
            archetype="DIPLOMAT",
            prices=(0.7, 0.2, 0.1),
            shield_propensity=0.85,
            risk_appetite=0.30,
            available_balance=1000.0,
        )
        engine = RulesEngine()
        decision = engine.decide(ctx, tick=0, rng_seed=42)

        # With shield_propensity=0.85, threshold = (1-0.85)*0.40 = 0.06
        # Spread 0.6 > 0.06, so should BUY trailing
        assert decision.action == TradeAction.BUY
        assert decision.outcome_index == 2  # trailing
        assert decision.pattern_name == "stability_maintenance"

    def test_saboteur_contrary_trade(self) -> None:
        """Saboteur makes contrary trades with high sabotage propensity."""
        ctx = _make_t0(
            archetype="SABOTEUR",
            sabotage_propensity=0.95,
            available_balance=1000.0,
        )
        engine = RulesEngine()
        decision = engine.decide(ctx, tick=0, rng_seed=42)

        # With propensity=0.95, almost always acts
        assert decision.action in (TradeAction.BUY, TradeAction.SABOTAGE)
        assert decision.pattern_name == "chaos_creation"
        # Should NOT buy the leading outcome (0 is leading)
        if decision.action == TradeAction.BUY:
            assert decision.outcome_index != 0

    def test_whale_conviction_buy(self) -> None:
        """Whale accumulates large position on strong conviction."""
        ctx = _make_t0(
            archetype="WHALE",
            prices=(0.6, 0.25, 0.15),
            evidence_sensitivity=0.55,
            position_limit=25_000,
            available_balance=5000.0,
        )
        engine = RulesEngine()
        decision = engine.decide(ctx, tick=0, rng_seed=42)

        assert decision.action == TradeAction.BUY
        assert decision.pattern_name == "conviction_accumulation"
        assert decision.shares > 0

    def test_degen_random_exploration(self) -> None:
        """Degen trades randomly with high exploration rate."""
        ctx = _make_t0(
            archetype="DEGEN",
            exploration_rate=0.95,
            available_balance=500.0,
            position_limit=1000,
        )
        engine = RulesEngine()
        decision = engine.decide(ctx, tick=0, rng_seed=42)

        # With exploration_rate=0.95, almost always explores
        assert decision.action in (TradeAction.BUY, TradeAction.SELL)
        assert decision.pattern_name == "random_exploration"

    def test_escalation_on_low_confidence(self) -> None:
        """Decisions with confidence below novelty_threshold flag for T3."""
        # Degen with low exploration rate will HOLD with low confidence
        ctx = _make_t0(
            archetype="DEGEN",
            exploration_rate=0.01,  # Very unlikely to explore
            novelty_threshold=0.5,
        )
        engine = RulesEngine()
        # Use a seed that makes the roll fail (> 0.01)
        decision = engine.decide(ctx, tick=0, rng_seed=100)

        # Degen HOLD confidence is 0.2, below threshold 0.5
        if decision.confidence < 0.5:
            assert decision.escalate_to_t3 is True

    def test_deterministic_with_fixed_seed(self) -> None:
        """Same inputs + same seed produce same decision."""
        ctx = _make_t0(archetype="SABOTEUR", sabotage_propensity=0.95)
        engine = RulesEngine()

        d1 = engine.decide(ctx, tick=5, rng_seed=12345)
        d2 = engine.decide(ctx, tick=5, rng_seed=12345)

        assert d1.action == d2.action
        assert d1.outcome_index == d2.outcome_index
        assert d1.shares == d2.shares
        assert d1.confidence == d2.confidence

    def test_options_considered_populated(self) -> None:
        """Every decision populates options_considered with at least one alternative."""
        for archetype in ["SHARK", "SPY", "DIPLOMAT", "SABOTEUR", "WHALE", "DEGEN"]:
            ctx = _make_t0(archetype=archetype, available_balance=1000.0)
            engine = RulesEngine()
            decision = engine.decide(ctx, tick=0, rng_seed=42)
            assert len(decision.options_considered) >= 1, (
                f"{archetype} decision has no options_considered"
            )

    def test_default_hold_for_unknown_archetype(self) -> None:
        """Unknown archetype defaults to HOLD with T3 escalation."""
        ctx = _make_t0(archetype="UNKNOWN")
        engine = RulesEngine()
        decision = engine.decide(ctx, tick=0, rng_seed=42)

        assert decision.action == TradeAction.HOLD
        assert decision.pattern_name == "default_hold"
        assert decision.escalate_to_t3 is True

    @pytest.mark.parametrize("archetype,pattern", [
        ("SHARK", "momentum_exploitation"),
        ("SPY", "intel_arbitrage"),
        ("DIPLOMAT", "stability_maintenance"),
        ("SABOTEUR", "chaos_creation"),
        ("WHALE", "conviction_accumulation"),
        ("DEGEN", "random_exploration"),
    ])
    def test_archetype_pattern_names(self, archetype: str, pattern: str) -> None:
        """Each archetype produces its named pattern."""
        ctx = _make_t0(archetype=archetype)
        engine = RulesEngine()
        decision = engine.decide(ctx, tick=0, rng_seed=42)
        assert decision.pattern_name == pattern
