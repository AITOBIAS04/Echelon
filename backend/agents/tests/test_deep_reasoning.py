"""Tests for T3 Deep Reasoning Engine.

Verifies structured output, rate limiting (daily and per-tick),
fallback when provider unavailable, and prompt construction.
All tests use mocked providers.

Cycle-013, Sprint 2 -- Task 7.
"""
from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from backend.agents.context_compiler import T0Context
from backend.agents.deep_reasoning import (
    DeepReasoningEngine,
    T3Decision,
    T3RateLimiter,
)
from backend.agents.rules_engine import T1Decision, TradeAction


# ===================================================================
# Fixtures
# ===================================================================


def _make_t0_context(archetype: str = "SHARK") -> T0Context:
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
        novelty_threshold=0.6,
        prices=(0.4, 0.35, 0.25),
        phase="TRADING",
        outcome_labels=("Yes", "No", "Maybe"),
        n_outcomes=3,
        evidence_coverage_pct=0.5,
        current_shares=(100.0, 0.0, 0.0),
        net_cashflow=50.0,
        available_balance=9_950.0,
        committed_sources=("worldmonitor",),
        resolution_date="2026-04-01",
        liquidity_b=100.0,
        max_position_pct=0.10,
        max_drawdown_pct=0.20,
        stop_loss_threshold=0.15,
        context_hash="test_hash",
    )


def _make_t1_decision(confidence: float = 0.4) -> T1Decision:
    """Create a low-confidence T1Decision to trigger T3 escalation."""
    return T1Decision(
        action=TradeAction.HOLD,
        outcome_index=None,
        shares=0.0,
        confidence=confidence,
        reasoning_trace="No clear signal, confidence below threshold",
        pattern_name="momentum_exploitation",
        escalate_to_t3=True,
    )


def _make_mock_provider(
    generate_response: dict = None,
    health_check_result: bool = True,
) -> AsyncMock:
    """Create a mock AnthropicProvider."""
    provider = AsyncMock()
    provider.generate = AsyncMock(
        return_value=generate_response
        or {
            "action": "BUY",
            "outcome_index": 0,
            "shares": 200.0,
            "confidence": 0.85,
            "reasoning_summary": "Deep analysis suggests strong buy signal",
            "evidence_refs": ["bundle_001", "bundle_002"],
            "pattern_name": "deep_analysis",
        }
    )
    provider.health_check = AsyncMock(return_value=health_check_result)
    return provider


# ===================================================================
# T3RateLimiter Tests
# ===================================================================


class TestT3RateLimiter:
    """Verify T3RateLimiter behaviour."""

    def test_default_limits(self) -> None:
        """Default limits: 10 per day, 1 per tick."""
        limiter = T3RateLimiter()
        assert limiter.max_calls_per_day == 10
        assert limiter.max_calls_per_tick == 1

    def test_can_call_when_under_limit(self) -> None:
        """can_call() returns True when under both limits."""
        limiter = T3RateLimiter(max_calls_per_day=5)
        assert limiter.can_call(tick=0) is True

    def test_daily_limit_enforcement(self) -> None:
        """can_call() returns False when daily limit is reached."""
        limiter = T3RateLimiter(max_calls_per_day=2)
        # Exhaust daily limit across different ticks
        assert limiter.can_call(tick=0) is True
        limiter.record_call()
        assert limiter.can_call(tick=1) is True
        limiter.record_call()
        assert limiter.can_call(tick=2) is False

    def test_per_tick_limit_enforcement(self) -> None:
        """can_call() returns False for second call in same tick."""
        limiter = T3RateLimiter(max_calls_per_day=10, max_calls_per_tick=1)
        assert limiter.can_call(tick=0) is True
        limiter.record_call()
        # Same tick -- should be blocked
        assert limiter.can_call(tick=0) is False
        # Different tick -- should be allowed
        assert limiter.can_call(tick=1) is True

    def test_daily_count_property(self) -> None:
        """daily_count property reflects recorded calls."""
        limiter = T3RateLimiter(max_calls_per_day=10)
        assert limiter.daily_count == 0
        limiter.can_call(tick=0)
        limiter.record_call()
        assert limiter.daily_count == 1
        limiter.can_call(tick=1)
        limiter.record_call()
        assert limiter.daily_count == 2


# ===================================================================
# T3Decision Tests
# ===================================================================


class TestT3Decision:
    """Verify T3Decision dataclass."""

    def test_t3_decision_creation(self) -> None:
        """T3Decision can be created with all required fields."""
        decision = T3Decision(
            action=TradeAction.BUY,
            outcome_index=0,
            shares=200.0,
            confidence=0.85,
            reasoning_summary="Deep analysis confirmed buy",
            evidence_refs=["bundle_001"],
            pattern_name="deep_analysis",
        )
        assert decision.action == TradeAction.BUY
        assert decision.outcome_index == 0
        assert decision.shares == 200.0
        assert decision.confidence == 0.85
        assert len(decision.evidence_refs) == 1

    def test_t3_decision_frozen(self) -> None:
        """T3Decision is immutable (frozen dataclass)."""
        decision = T3Decision(
            action=TradeAction.BUY,
            outcome_index=0,
            shares=200.0,
            confidence=0.85,
            reasoning_summary="Test",
            evidence_refs=[],
            pattern_name="deep_analysis",
        )
        with pytest.raises(AttributeError):
            decision.action = TradeAction.SELL  # type: ignore


# ===================================================================
# DeepReasoningEngine Tests
# ===================================================================


class TestDeepReasoningEngine:
    """Verify DeepReasoningEngine with mocked providers."""

    @pytest.mark.asyncio
    async def test_reason_with_mocked_provider(self) -> None:
        """reason() returns T3Decision from provider response."""
        mock_provider = _make_mock_provider()
        engine = DeepReasoningEngine(
            provider=mock_provider, max_calls_per_day=10
        )
        ctx = _make_t0_context()
        t1 = _make_t1_decision()

        result = await engine.reason(
            agent_id="test_agent",
            t0_context=ctx,
            t1_decision=t1,
            market_history=[],
            evidence_chain=[],
            tick=0,
        )

        assert result is not None
        assert isinstance(result, T3Decision)
        assert result.action == TradeAction.BUY
        assert result.confidence == 0.85
        assert result.evidence_refs == ["bundle_001", "bundle_002"]
        assert result.pattern_name == "deep_analysis"

    @pytest.mark.asyncio
    async def test_reason_returns_none_when_rate_limited(self) -> None:
        """reason() returns None when daily rate limit is reached."""
        mock_provider = _make_mock_provider()
        engine = DeepReasoningEngine(
            provider=mock_provider, max_calls_per_day=1
        )
        ctx = _make_t0_context()
        t1 = _make_t1_decision()

        # First call succeeds
        result1 = await engine.reason(
            agent_id="test_agent",
            t0_context=ctx,
            t1_decision=t1,
            market_history=[],
            evidence_chain=[],
            tick=0,
        )
        assert result1 is not None

        # Second call should be rate-limited
        result2 = await engine.reason(
            agent_id="test_agent",
            t0_context=ctx,
            t1_decision=t1,
            market_history=[],
            evidence_chain=[],
            tick=1,
        )
        assert result2 is None

    @pytest.mark.asyncio
    async def test_reason_returns_none_with_none_provider(self) -> None:
        """reason() returns None when provider is None."""
        engine = DeepReasoningEngine(provider=None, max_calls_per_day=10)
        ctx = _make_t0_context()
        t1 = _make_t1_decision()

        result = await engine.reason(
            agent_id="test_agent",
            t0_context=ctx,
            t1_decision=t1,
            market_history=[],
            evidence_chain=[],
            tick=0,
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_reason_returns_none_on_health_check_failure(self) -> None:
        """reason() returns None when health check fails."""
        mock_provider = _make_mock_provider(health_check_result=False)
        engine = DeepReasoningEngine(
            provider=mock_provider, max_calls_per_day=10
        )
        ctx = _make_t0_context()
        t1 = _make_t1_decision()

        result = await engine.reason(
            agent_id="test_agent",
            t0_context=ctx,
            t1_decision=t1,
            market_history=[],
            evidence_chain=[],
            tick=0,
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_reason_returns_none_on_provider_exception(self) -> None:
        """reason() returns None when provider.generate() raises."""
        mock_provider = AsyncMock()
        mock_provider.health_check = AsyncMock(return_value=True)
        mock_provider.generate = AsyncMock(
            side_effect=Exception("API timeout")
        )
        engine = DeepReasoningEngine(
            provider=mock_provider, max_calls_per_day=10
        )
        ctx = _make_t0_context()
        t1 = _make_t1_decision()

        result = await engine.reason(
            agent_id="test_agent",
            t0_context=ctx,
            t1_decision=t1,
            market_history=[],
            evidence_chain=[],
            tick=0,
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_per_agent_rate_limiting(self) -> None:
        """Each agent gets its own rate limiter."""
        mock_provider = _make_mock_provider()
        engine = DeepReasoningEngine(
            provider=mock_provider, max_calls_per_day=1
        )
        ctx = _make_t0_context()
        t1 = _make_t1_decision()

        # Agent A exhausts its limit
        result_a = await engine.reason(
            agent_id="agent_a",
            t0_context=ctx,
            t1_decision=t1,
            market_history=[],
            evidence_chain=[],
            tick=0,
        )
        assert result_a is not None

        # Agent B should still have its own budget
        result_b = await engine.reason(
            agent_id="agent_b",
            t0_context=ctx,
            t1_decision=t1,
            market_history=[],
            evidence_chain=[],
            tick=1,
        )
        assert result_b is not None

        # Agent A should be rate-limited
        result_a2 = await engine.reason(
            agent_id="agent_a",
            t0_context=ctx,
            t1_decision=t1,
            market_history=[],
            evidence_chain=[],
            tick=2,
        )
        assert result_a2 is None

    def test_build_prompt_includes_context(self) -> None:
        """_build_prompt includes archetype, prices, position, T1 reasoning."""
        engine = DeepReasoningEngine(provider=None)
        ctx = _make_t0_context("SPY")
        t1 = _make_t1_decision()

        prompt = engine._build_prompt(
            ctx, t1, history=[{"tick": 0}], evidence=[{"id": "ev_001"}]
        )

        assert "SPY" in prompt
        assert "0.4" in prompt  # price
        assert "HOLD" in prompt  # T1 action
        assert "1 items" in prompt  # evidence count
        assert "1 ticks" in prompt  # history count
