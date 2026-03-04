"""Tests for inquiry_class integration in T0Context.

Cycle-014, Sprint 1 — Task 5.
"""
from __future__ import annotations

import pytest

from backend.agents.context_compiler import ContextCompiler, T0Context
from backend.agents.genome import AgentGenome, EchelonArchetype
from backend.market.state import MarketPhase, MarketState
from backend.market.positions import AgentPosition


def _make_genome(**overrides: object) -> AgentGenome:
    defaults = dict(
        archetype=EchelonArchetype.SHARK,
        risk_appetite=0.7,
        evidence_sensitivity=0.5,
        time_preference=0.5,
        exploration_rate=0.3,
        position_limit=100.0,
        sabotage_propensity=0.0,
        shield_propensity=0.3,
        patience=5,
        novelty_threshold=0.4,
        max_position_pct=0.1,
        max_drawdown_pct=0.2,
        stop_loss_threshold=0.15,
        committed_sources=["worldmonitor_cii"],
        resolution_date="2026-12-31",
    )
    defaults.update(overrides)
    return AgentGenome(**defaults)


def _make_market() -> MarketState:
    return MarketState(
        market_id="test-market",
        theatre_id="theatre-test",
        b=100.0,
        n_outcomes=2,
        outcome_labels=["YES", "NO"],
        x=[0.0, 0.0],
    )


def _make_position() -> AgentPosition:
    return AgentPosition(agent_id="agent-1", market_id="test-market", shares=[0.0, 0.0])


class TestT0ContextInquiryClass:
    """T0Context includes inquiry_class from compile()."""

    def test_default_inquiry_class(self) -> None:
        ctx = ContextCompiler.compile(
            genome=_make_genome(),
            market=_make_market(),
            position=_make_position(),
            available_balance=1000.0,
        )
        assert ctx.inquiry_class == "COUNTERFACTUAL"

    def test_explicit_inquiry_class(self) -> None:
        ctx = ContextCompiler.compile(
            genome=_make_genome(),
            market=_make_market(),
            position=_make_position(),
            available_balance=1000.0,
            inquiry_class="INVESTIGATIVE",
        )
        assert ctx.inquiry_class == "INVESTIGATIVE"

    def test_all_inquiry_classes(self) -> None:
        for ic in ["COUNTERFACTUAL", "INVESTIGATIVE", "INSPECTION", "SURVEY", "SCRUTINY"]:
            ctx = ContextCompiler.compile(
                genome=_make_genome(),
                market=_make_market(),
                position=_make_position(),
                available_balance=1000.0,
                inquiry_class=ic,
            )
            assert ctx.inquiry_class == ic

    def test_hash_changes_with_inquiry_class(self) -> None:
        ctx1 = ContextCompiler.compile(
            genome=_make_genome(),
            market=_make_market(),
            position=_make_position(),
            available_balance=1000.0,
            inquiry_class="COUNTERFACTUAL",
        )
        ctx2 = ContextCompiler.compile(
            genome=_make_genome(),
            market=_make_market(),
            position=_make_position(),
            available_balance=1000.0,
            inquiry_class="INSPECTION",
        )
        assert ctx1.context_hash != ctx2.context_hash

    def test_same_inquiry_class_same_hash(self) -> None:
        ctx1 = ContextCompiler.compile(
            genome=_make_genome(),
            market=_make_market(),
            position=_make_position(),
            available_balance=1000.0,
            inquiry_class="SURVEY",
        )
        ctx2 = ContextCompiler.compile(
            genome=_make_genome(),
            market=_make_market(),
            position=_make_position(),
            available_balance=1000.0,
            inquiry_class="SURVEY",
        )
        assert ctx1.context_hash == ctx2.context_hash

    def test_inquiry_class_in_frozen_dataclass(self) -> None:
        ctx = ContextCompiler.compile(
            genome=_make_genome(),
            market=_make_market(),
            position=_make_position(),
            available_balance=1000.0,
            inquiry_class="SCRUTINY",
        )
        with pytest.raises(AttributeError):
            ctx.inquiry_class = "COUNTERFACTUAL"
