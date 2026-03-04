"""Tests for inquiry-class-specific agent behaviour adaptation.

Cycle-014, Sprint 2 — Task 3.
"""
from __future__ import annotations

import pytest

from backend.agents.context_compiler import T0Context
from backend.agents.inquiry_behaviour import (
    DEFAULT_PROFILE,
    INQUIRY_PROFILES,
    InquiryBehaviourAdapter,
    InquiryProfile,
)
from backend.agents.rules_engine import RulesEngine, T1Decision


ARCHETYPES = ["SHARK", "SPY", "DIPLOMAT", "SABOTEUR", "WHALE", "DEGEN"]
INQUIRY_CLASSES = ["COUNTERFACTUAL", "INVESTIGATIVE", "INSPECTION", "SURVEY", "SCRUTINY"]


class TestInquiryProfile:
    """InquiryProfile is frozen dataclass with expected fields."""

    def test_fields(self):
        p = InquiryProfile(
            pattern_name_override="test",
            evidence_weight_modifier=1.5,
            momentum_weight_modifier=0.8,
            action_description="test desc",
        )
        assert p.pattern_name_override == "test"
        assert p.evidence_weight_modifier == 1.5
        assert p.momentum_weight_modifier == 0.8
        assert p.action_description == "test desc"

    def test_frozen(self):
        p = InquiryProfile(
            pattern_name_override="test",
            evidence_weight_modifier=1.0,
            momentum_weight_modifier=1.0,
            action_description="test",
        )
        with pytest.raises(AttributeError):
            p.pattern_name_override = "other"


class TestInquiryProfilesCompleteness:
    """All 30 archetype x inquiry_class combinations have profiles."""

    def test_profile_count(self):
        assert len(INQUIRY_PROFILES) == 30

    def test_all_combinations_covered(self):
        for archetype in ARCHETYPES:
            for ic in INQUIRY_CLASSES:
                key = (archetype, ic)
                assert key in INQUIRY_PROFILES, f"Missing profile for {key}"

    def test_all_modifiers_reasonable(self):
        """All modifiers are positive and within [0.1, 3.0]."""
        for key, profile in INQUIRY_PROFILES.items():
            assert 0.1 <= profile.evidence_weight_modifier <= 3.0, (
                f"{key}: evidence_weight_modifier={profile.evidence_weight_modifier}"
            )
            assert 0.1 <= profile.momentum_weight_modifier <= 3.0, (
                f"{key}: momentum_weight_modifier={profile.momentum_weight_modifier}"
            )

    def test_all_have_pattern_name(self):
        for key, profile in INQUIRY_PROFILES.items():
            assert profile.pattern_name_override, f"{key}: missing pattern_name_override"

    def test_all_have_description(self):
        for key, profile in INQUIRY_PROFILES.items():
            assert profile.action_description, f"{key}: missing action_description"


class TestInquiryBehaviourAdapter:
    """InquiryBehaviourAdapter.get_profile() works correctly."""

    def test_known_combination(self):
        profile = InquiryBehaviourAdapter.get_profile("SHARK", "INVESTIGATIVE")
        assert profile.pattern_name_override == "evidence_front_running"
        assert profile.evidence_weight_modifier == 1.5
        assert profile.momentum_weight_modifier == 0.7

    def test_counterfactual_identity_modifiers(self):
        """COUNTERFACTUAL profiles have 1.0 modifiers (backward compat)."""
        for archetype in ARCHETYPES:
            profile = InquiryBehaviourAdapter.get_profile(archetype, "COUNTERFACTUAL")
            assert profile.evidence_weight_modifier == 1.0, f"{archetype} evidence mod"
            assert profile.momentum_weight_modifier == 1.0, f"{archetype} momentum mod"

    def test_spy_scrutiny(self):
        profile = InquiryBehaviourAdapter.get_profile("SPY", "SCRUTINY")
        assert profile.pattern_name_override == "deep_verification"

    def test_default_for_unknown_archetype(self):
        profile = InquiryBehaviourAdapter.get_profile("UNKNOWN", "COUNTERFACTUAL")
        assert profile == DEFAULT_PROFILE

    def test_default_for_unknown_inquiry_class(self):
        profile = InquiryBehaviourAdapter.get_profile("SHARK", "UNKNOWN")
        assert profile == DEFAULT_PROFILE

    def test_case_insensitive(self):
        profile = InquiryBehaviourAdapter.get_profile("shark", "investigative")
        assert profile.pattern_name_override == "evidence_front_running"

    def test_whitespace_tolerant(self):
        profile = InquiryBehaviourAdapter.get_profile("  SHARK  ", "  SURVEY  ")
        assert profile.pattern_name_override == "sentiment_tracking"


def _make_ctx(archetype: str = "SHARK", inquiry_class: str = "COUNTERFACTUAL") -> T0Context:
    """Create a minimal T0Context for testing."""
    return T0Context(
        archetype=archetype,
        risk_appetite=0.7,
        evidence_sensitivity=0.8,
        time_preference=0.5,
        exploration_rate=0.3,
        position_limit=1000.0,
        sabotage_propensity=0.1,
        shield_propensity=0.3,
        patience=5,
        novelty_threshold=0.2,
        prices=(0.6, 0.4),
        phase="TRADING",
        outcome_labels=("YES", "NO"),
        n_outcomes=2,
        evidence_coverage_pct=0.5,
        current_shares=(0.0, 0.0),
        net_cashflow=0.0,
        available_balance=500.0,
        committed_sources=("wm_news",),
        resolution_date="2026-04-01",
        liquidity_b=100.0,
        max_position_pct=0.1,
        max_drawdown_pct=0.2,
        stop_loss_threshold=0.15,
        inquiry_class=inquiry_class,
    )


class TestRulesEngineInquiryIntegration:
    """RulesEngine.decide() applies inquiry modifiers."""

    def test_shark_counterfactual_produces_decision(self):
        engine = RulesEngine()
        ctx = _make_ctx("SHARK", "COUNTERFACTUAL")
        decision = engine.decide(ctx, tick=5, rng_seed=42)
        assert isinstance(decision, T1Decision)
        # Pattern name should be overridden by inquiry profile
        assert decision.pattern_name == "momentum_exploitation"

    def test_shark_investigative_changes_pattern(self):
        engine = RulesEngine()
        ctx = _make_ctx("SHARK", "INVESTIGATIVE")
        decision = engine.decide(ctx, tick=5, rng_seed=42)
        assert decision.pattern_name == "evidence_front_running"
        assert "Evidence front-running" in decision.reasoning_trace

    def test_spy_scrutiny_changes_pattern(self):
        engine = RulesEngine()
        ctx = _make_ctx("SPY", "SCRUTINY")
        decision = engine.decide(ctx, tick=5, rng_seed=42)
        assert decision.pattern_name == "deep_verification"
        assert "Deep verification" in decision.reasoning_trace

    def test_diplomat_survey_changes_pattern(self):
        engine = RulesEngine()
        ctx = _make_ctx("DIPLOMAT", "SURVEY")
        decision = engine.decide(ctx, tick=5, rng_seed=42)
        assert decision.pattern_name == "consensus_building"

    def test_modifier_affects_decision(self):
        """Different inquiry classes can produce different decisions for same market state."""
        engine = RulesEngine()
        # SHARK with COUNTERFACTUAL (momentum_weight 1.3) vs INVESTIGATIVE (0.7)
        ctx_cf = _make_ctx("SHARK", "COUNTERFACTUAL")
        ctx_inv = _make_ctx("SHARK", "INVESTIGATIVE")
        d_cf = engine.decide(ctx_cf, tick=5, rng_seed=42)
        d_inv = engine.decide(ctx_inv, tick=5, rng_seed=42)
        # Pattern names should differ
        assert d_cf.pattern_name != d_inv.pattern_name

    def test_default_counterfactual_still_works(self):
        """Without inquiry_class set, defaults to COUNTERFACTUAL."""
        engine = RulesEngine()
        ctx = _make_ctx("DEGEN", "COUNTERFACTUAL")
        decision = engine.decide(ctx, tick=5, rng_seed=42)
        assert isinstance(decision, T1Decision)
        assert decision.pattern_name == "random_exploration"

    def test_all_archetypes_all_inquiry_classes(self):
        """Every archetype + inquiry class combo produces a valid decision."""
        engine = RulesEngine()
        for archetype in ARCHETYPES:
            for ic in INQUIRY_CLASSES:
                ctx = _make_ctx(archetype, ic)
                decision = engine.decide(ctx, tick=5, rng_seed=42)
                assert isinstance(decision, T1Decision)
                assert decision.pattern_name  # non-empty
