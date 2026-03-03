"""Tests for Novelty Threshold Router.

Verifies routing logic: high-confidence -> T1, low-confidence -> T3 escalation,
rate-limited fallback to T1, T2 expression, tier recording, and pure T1 mode.
All tests use mocked providers.

Cycle-013, Sprint 2 -- Task 7.
"""
from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from backend.agents.context_compiler import T0Context
from backend.agents.decision_router import DecisionRouter, RoutedDecision
from backend.agents.deep_reasoning import T3Decision
from backend.agents.personality_engine import PersonalityEngine, T2Output
from backend.agents.rules_engine import T1Decision, TradeAction


# ===================================================================
# Fixtures
# ===================================================================


def _make_t0_context(
    archetype: str = "SHARK",
    novelty_threshold: float = 0.6,
) -> T0Context:
    """Create a minimal T0Context for testing."""
    return T0Context(
        archetype=archetype,
        risk_appetite=0.85,
        evidence_sensitivity=0.70,
        time_preference=0.95,
        exploration_rate=0.15,
        position_limit=10_000,
        sabotage_propensity=0.30,
        shield_propensity=0.10,
        patience=30,
        novelty_threshold=novelty_threshold,
        prices=(0.4, 0.35, 0.25),
        phase="TRADING",
        outcome_labels=("Yes", "No", "Maybe"),
        n_outcomes=3,
        evidence_coverage_pct=0.5,
        current_shares=(0.0, 0.0, 0.0),
        net_cashflow=0.0,
        available_balance=10_000.0,
        committed_sources=(),
        resolution_date="2026-04-01",
        liquidity_b=100.0,
        max_position_pct=0.10,
        max_drawdown_pct=0.20,
        stop_loss_threshold=0.15,
        context_hash="test_hash",
    )


def _make_t1_high_confidence() -> T1Decision:
    """Create a high-confidence T1Decision (no escalation needed)."""
    return T1Decision(
        action=TradeAction.BUY,
        outcome_index=0,
        shares=100.0,
        confidence=0.85,
        reasoning_trace="Strong momentum signal, buying",
        pattern_name="momentum_exploitation",
        escalate_to_t3=False,
    )


def _make_t1_low_confidence() -> T1Decision:
    """Create a low-confidence T1Decision (should escalate to T3)."""
    return T1Decision(
        action=TradeAction.HOLD,
        outcome_index=None,
        shares=0.0,
        confidence=0.35,
        reasoning_trace="No clear signal, low confidence",
        pattern_name="momentum_exploitation",
        escalate_to_t3=True,
    )


def _make_mock_deep_reasoning(
    t3_result: T3Decision = None,
    return_none: bool = False,
) -> AsyncMock:
    """Create a mock DeepReasoningEngine."""
    engine = AsyncMock()
    if return_none:
        engine.reason = AsyncMock(return_value=None)
    else:
        engine.reason = AsyncMock(
            return_value=t3_result
            or T3Decision(
                action=TradeAction.BUY,
                outcome_index=0,
                shares=200.0,
                confidence=0.90,
                reasoning_summary="Deep analysis confirms buy",
                evidence_refs=["bundle_001"],
                pattern_name="deep_analysis",
            )
        )
    return engine


def _make_mock_personality() -> AsyncMock:
    """Create a mock PersonalityEngine."""
    engine = AsyncMock(spec=PersonalityEngine)
    engine.express = AsyncMock(
        return_value=T2Output(
            coloured_rationale="Blood in the water.",
            market_commentary="Time to feast.",
        )
    )
    return engine


# ===================================================================
# DecisionRouter Tests
# ===================================================================


class TestDecisionRouter:
    """Verify DecisionRouter routing logic."""

    @pytest.mark.asyncio
    async def test_high_confidence_routes_to_t1(self) -> None:
        """High-confidence T1 decision uses T1 directly (no T3)."""
        router = DecisionRouter(enable_t2=False)
        ctx = _make_t0_context(novelty_threshold=0.6)
        t1 = _make_t1_high_confidence()  # confidence=0.85

        result = await router.route(
            t0_context=ctx,
            t1_decision=t1,
            agent_id="test_agent",
            tick=0,
        )

        assert isinstance(result, RoutedDecision)
        assert result.tier_used == "T1-RULES"
        assert result.action == TradeAction.BUY
        assert result.confidence == 0.85
        assert result.escalated_to_t3 is False
        assert result.t3_rate_limited is False

    @pytest.mark.asyncio
    async def test_low_confidence_escalates_to_t3(self) -> None:
        """Low-confidence T1 decision escalates to T3."""
        mock_t3 = _make_mock_deep_reasoning()
        router = DecisionRouter(
            deep_reasoning=mock_t3, enable_t2=False
        )
        ctx = _make_t0_context(novelty_threshold=0.6)
        t1 = _make_t1_low_confidence()  # confidence=0.35

        result = await router.route(
            t0_context=ctx,
            t1_decision=t1,
            agent_id="test_agent",
            tick=0,
        )

        assert result.tier_used == "T3"
        assert result.action == TradeAction.BUY
        assert result.confidence == 0.90
        assert result.escalated_to_t3 is True
        assert result.t3_rate_limited is False
        assert result.evidence_refs == ["bundle_001"]
        assert result.pattern_name == "deep_analysis"

    @pytest.mark.asyncio
    async def test_t3_replaces_t1_decision(self) -> None:
        """When T3 succeeds, its decision replaces T1 completely."""
        t3_decision = T3Decision(
            action=TradeAction.SELL,
            outcome_index=1,
            shares=500.0,
            confidence=0.92,
            reasoning_summary="Contrary evidence found",
            evidence_refs=["ev_001", "ev_002"],
            pattern_name="evidence_reversal",
        )
        mock_t3 = _make_mock_deep_reasoning(t3_result=t3_decision)
        router = DecisionRouter(
            deep_reasoning=mock_t3, enable_t2=False
        )
        ctx = _make_t0_context(novelty_threshold=0.6)
        t1 = _make_t1_low_confidence()

        result = await router.route(
            t0_context=ctx,
            t1_decision=t1,
            agent_id="test_agent",
            tick=0,
        )

        assert result.action == TradeAction.SELL
        assert result.outcome_index == 1
        assert result.shares == 500.0
        assert result.confidence == 0.92
        assert result.reasoning_summary == "Contrary evidence found"
        assert result.tier_used == "T3"

    @pytest.mark.asyncio
    async def test_t3_rate_limited_fallback_to_t1(self) -> None:
        """When T3 is rate-limited (returns None), falls back to T1."""
        mock_t3 = _make_mock_deep_reasoning(return_none=True)
        router = DecisionRouter(
            deep_reasoning=mock_t3, enable_t2=False
        )
        ctx = _make_t0_context(novelty_threshold=0.6)
        t1 = _make_t1_low_confidence()

        result = await router.route(
            t0_context=ctx,
            t1_decision=t1,
            agent_id="test_agent",
            tick=0,
        )

        assert result.tier_used == "T1-RULES"
        assert result.action == TradeAction.HOLD  # Original T1 action
        assert result.confidence == 0.35  # Original T1 confidence
        assert result.escalated_to_t3 is False
        assert result.t3_rate_limited is True

    @pytest.mark.asyncio
    async def test_t2_runs_when_enabled(self) -> None:
        """T2 expression runs when enabled and provider available."""
        mock_personality = _make_mock_personality()
        router = DecisionRouter(
            personality_engine=mock_personality,
            enable_t2=True,
        )
        ctx = _make_t0_context()
        t1 = _make_t1_high_confidence()

        result = await router.route(
            t0_context=ctx,
            t1_decision=t1,
            agent_id="test_agent",
            tick=0,
        )

        assert result.t2_output is not None
        assert isinstance(result.t2_output, T2Output)
        assert result.t2_output.coloured_rationale == "Blood in the water."

    @pytest.mark.asyncio
    async def test_t2_disabled(self) -> None:
        """T2 does not run when disabled."""
        mock_personality = _make_mock_personality()
        router = DecisionRouter(
            personality_engine=mock_personality,
            enable_t2=False,
        )
        ctx = _make_t0_context()
        t1 = _make_t1_high_confidence()

        result = await router.route(
            t0_context=ctx,
            t1_decision=t1,
            agent_id="test_agent",
            tick=0,
        )

        assert result.t2_output is None

    @pytest.mark.asyncio
    async def test_t2_failure_non_fatal(self) -> None:
        """T2 failure is non-fatal -- decision still returned."""
        mock_personality = AsyncMock(spec=PersonalityEngine)
        mock_personality.express = AsyncMock(
            side_effect=Exception("Mistral error")
        )
        router = DecisionRouter(
            personality_engine=mock_personality,
            enable_t2=True,
        )
        ctx = _make_t0_context()
        t1 = _make_t1_high_confidence()

        result = await router.route(
            t0_context=ctx,
            t1_decision=t1,
            agent_id="test_agent",
            tick=0,
        )

        assert result is not None
        assert result.tier_used == "T1-RULES"
        assert result.action == TradeAction.BUY
        assert result.t2_output is None

    @pytest.mark.asyncio
    async def test_pure_t1_mode(self) -> None:
        """Router works with None personality_engine and None deep_reasoning."""
        router = DecisionRouter(
            personality_engine=None,
            deep_reasoning=None,
            enable_t2=True,
        )
        ctx = _make_t0_context()
        t1 = _make_t1_low_confidence()

        result = await router.route(
            t0_context=ctx,
            t1_decision=t1,
            agent_id="test_agent",
            tick=0,
        )

        assert result.tier_used == "T1-RULES"
        assert result.action == t1.action
        assert result.t2_output is None
        assert result.escalated_to_t3 is False

    @pytest.mark.asyncio
    async def test_tier_used_records_t3(self) -> None:
        """Decision traces record tier_used='T3' after successful escalation."""
        mock_t3 = _make_mock_deep_reasoning()
        router = DecisionRouter(
            deep_reasoning=mock_t3, enable_t2=False
        )
        ctx = _make_t0_context(novelty_threshold=0.6)
        t1 = _make_t1_low_confidence()

        result = await router.route(
            t0_context=ctx,
            t1_decision=t1,
            agent_id="test_agent",
            tick=0,
        )

        assert result.tier_used == "T3"

    @pytest.mark.asyncio
    async def test_escalation_flag_from_t1(self) -> None:
        """T1's escalate_to_t3 flag triggers T3 even if confidence is high."""
        t1 = T1Decision(
            action=TradeAction.HOLD,
            outcome_index=None,
            shares=0.0,
            confidence=0.95,  # High confidence, but flag set
            reasoning_trace="Unknown pattern, requesting deep analysis",
            pattern_name="default_hold",
            escalate_to_t3=True,
        )
        mock_t3 = _make_mock_deep_reasoning()
        router = DecisionRouter(
            deep_reasoning=mock_t3, enable_t2=False
        )
        ctx = _make_t0_context(novelty_threshold=0.6)

        result = await router.route(
            t0_context=ctx,
            t1_decision=t1,
            agent_id="test_agent",
            tick=0,
        )

        assert result.tier_used == "T3"
        assert result.escalated_to_t3 is True

    @pytest.mark.asyncio
    async def test_routed_decision_evidence_refs_default_empty(self) -> None:
        """RoutedDecision defaults evidence_refs to empty list."""
        router = DecisionRouter(enable_t2=False)
        ctx = _make_t0_context()
        t1 = _make_t1_high_confidence()

        result = await router.route(
            t0_context=ctx,
            t1_decision=t1,
            agent_id="test_agent",
            tick=0,
        )

        assert result.evidence_refs == []
