"""Tests for T2 Personality Engine.

Verifies archetype-specific expression, non-interference with T1 decisions,
generic fallback when provider unavailable, and T2Output immutability.
All tests use mocked providers.

Cycle-013, Sprint 2 -- Task 7.
"""
from __future__ import annotations

from dataclasses import FrozenInstanceError
from unittest.mock import AsyncMock

import pytest

from backend.agents.context_compiler import T0Context
from backend.agents.genome import EchelonArchetype, create_genome
from backend.agents.personality_engine import (
    PERSONALITY_PROMPTS,
    PersonalityEngine,
    T2Output,
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


def _make_t1_decision(
    action: TradeAction = TradeAction.BUY,
    confidence: float = 0.75,
) -> T1Decision:
    """Create a minimal T1Decision for testing."""
    return T1Decision(
        action=action,
        outcome_index=0,
        shares=100.0,
        confidence=confidence,
        reasoning_trace="Momentum signal detected, buying leading outcome",
        pattern_name="momentum_exploitation",
    )


def _make_mock_provider(
    generate_response: dict = None,
    health_check_result: bool = True,
) -> AsyncMock:
    """Create a mock MistralProvider."""
    provider = AsyncMock()
    provider.generate = AsyncMock(
        return_value=generate_response
        or {"rationale": "The momentum is clear. We strike.", "commentary": "Market moving fast."}
    )
    provider.health_check = AsyncMock(return_value=health_check_result)
    return provider


# ===================================================================
# T2Output Tests
# ===================================================================


class TestT2Output:
    """Verify T2Output dataclass behaviour."""

    def test_t2_output_creation(self) -> None:
        """T2Output can be created with all fields."""
        output = T2Output(
            coloured_rationale="Blood in the water.",
            market_commentary="Shark is hungry.",
            diplomatic_message=None,
        )
        assert output.coloured_rationale == "Blood in the water."
        assert output.market_commentary == "Shark is hungry."
        assert output.diplomatic_message is None

    def test_t2_output_frozen(self) -> None:
        """T2Output is immutable (frozen dataclass)."""
        output = T2Output(
            coloured_rationale="Test",
            market_commentary="Test",
        )
        with pytest.raises(FrozenInstanceError):
            output.coloured_rationale = "Modified"  # type: ignore


# ===================================================================
# PersonalityEngine Tests
# ===================================================================


class TestPersonalityEngine:
    """Verify PersonalityEngine with mocked providers."""

    @pytest.mark.asyncio
    async def test_express_with_mocked_provider(self) -> None:
        """express() returns T2Output from provider response."""
        mock_provider = _make_mock_provider()
        engine = PersonalityEngine(provider=mock_provider)
        ctx = _make_t0_context("SHARK")
        decision = _make_t1_decision()

        result = await engine.express(ctx, decision)

        assert isinstance(result, T2Output)
        assert result.coloured_rationale == "The momentum is clear. We strike."
        assert result.market_commentary == "Market moving fast."

    @pytest.mark.asyncio
    async def test_non_interference_with_t1(self) -> None:
        """T2 never modifies the T1 decision. T1Decision is frozen, T2Output is string-only."""
        mock_provider = _make_mock_provider()
        engine = PersonalityEngine(provider=mock_provider)
        ctx = _make_t0_context("SHARK")
        decision = _make_t1_decision(action=TradeAction.BUY, confidence=0.8)

        # Record original T1 state
        original_action = decision.action
        original_confidence = decision.confidence
        original_shares = decision.shares
        original_outcome = decision.outcome_index

        result = await engine.express(ctx, decision)

        # T1 decision must be unchanged
        assert decision.action == original_action
        assert decision.confidence == original_confidence
        assert decision.shares == original_shares
        assert decision.outcome_index == original_outcome
        # T2 output contains only strings
        assert isinstance(result.coloured_rationale, str)
        assert isinstance(result.market_commentary, str)

    @pytest.mark.asyncio
    async def test_fallback_with_none_provider(self) -> None:
        """express() returns generic fallback when provider is None."""
        engine = PersonalityEngine(provider=None)
        ctx = _make_t0_context("SHARK")
        decision = _make_t1_decision()

        result = await engine.express(ctx, decision)

        assert isinstance(result, T2Output)
        assert "[SHARK]" in result.coloured_rationale
        assert "BUY" in result.coloured_rationale
        assert result.market_commentary == ""

    @pytest.mark.asyncio
    async def test_fallback_on_health_check_failure(self) -> None:
        """express() returns generic fallback when health check fails."""
        mock_provider = _make_mock_provider(health_check_result=False)
        engine = PersonalityEngine(provider=mock_provider)
        ctx = _make_t0_context("SPY")
        decision = _make_t1_decision()

        result = await engine.express(ctx, decision)

        assert isinstance(result, T2Output)
        assert "[SPY]" in result.coloured_rationale

    @pytest.mark.asyncio
    async def test_fallback_on_provider_exception(self) -> None:
        """express() returns generic fallback when provider.generate() raises."""
        mock_provider = AsyncMock()
        mock_provider.health_check = AsyncMock(return_value=True)
        mock_provider.generate = AsyncMock(side_effect=Exception("API error"))
        engine = PersonalityEngine(provider=mock_provider)
        ctx = _make_t0_context("DIPLOMAT")
        decision = _make_t1_decision()

        result = await engine.express(ctx, decision)

        assert isinstance(result, T2Output)
        assert "[DIPLOMAT]" in result.coloured_rationale

    @pytest.mark.asyncio
    @pytest.mark.parametrize("archetype", [
        "SHARK", "SPY", "DIPLOMAT", "SABOTEUR", "WHALE", "DEGEN",
    ])
    async def test_all_archetypes_produce_output(self, archetype: str) -> None:
        """Every archetype produces T2Output with mocked provider."""
        mock_provider = _make_mock_provider(
            generate_response={
                "rationale": f"{archetype} says: time to move.",
                "commentary": "Commentary here.",
            }
        )
        engine = PersonalityEngine(provider=mock_provider)
        ctx = _make_t0_context(archetype)
        decision = _make_t1_decision()

        result = await engine.express(ctx, decision)

        assert isinstance(result, T2Output)
        assert archetype in result.coloured_rationale

    def test_personality_prompts_all_archetypes(self) -> None:
        """PERSONALITY_PROMPTS has entries for all 6 archetypes."""
        expected_archetypes = {"SHARK", "SPY", "DIPLOMAT", "SABOTEUR", "WHALE", "DEGEN"}
        assert set(PERSONALITY_PROMPTS.keys()) == expected_archetypes

    def test_personality_prompts_are_distinct(self) -> None:
        """Each archetype has a distinct prompt template."""
        prompts = list(PERSONALITY_PROMPTS.values())
        assert len(prompts) == len(set(prompts))
