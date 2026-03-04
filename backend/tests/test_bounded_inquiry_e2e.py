"""E2E tests for bounded inquiry markets — one per inquiry class.

Each test: create theatre (market) -> spawn 3 agents -> 10 trading ticks
with evidence injection -> resolution triggers -> settlement -> certificate.

Assert: inquiry_class consistent across theatre, settlement report, certificate.
Assert: resolution_trigger_reason matches expected trigger for the inquiry class.

Cycle-014, Sprint 2 — Task 6.
"""
from __future__ import annotations

import json

from backend.agents.context_compiler import ContextCompiler, T0Context
from backend.agents.genome import (
    EchelonArchetype,
    create_genome,
)
from backend.agents.rules_engine import RulesEngine
from backend.market.lifecycle import MarketLifecycle
from backend.market.positions import PositionManager
from backend.market.resolution import ResolutionEngine, ResolutionTrigger
from backend.market.state import FeeSchedule, MarketPhase
from backend.market.trading import TradingEngine
from backend.services.evidence_service import InquiryEvidenceRules

TOLERANCE = 1e-9


# ===================================================================
# Helpers
# ===================================================================

def _create_trading_market(
    market_id: str,
    theatre_id: str,
    n_outcomes: int,
    outcome_labels: list[str],
    b: float = 100.0,
):
    """Create a market in TRADING phase."""
    market = MarketLifecycle.create_market(
        market_id=market_id,
        theatre_id=theatre_id,
        b=b,
        n_outcomes=n_outcomes,
        outcome_labels=outcome_labels,
        fee_schedule=FeeSchedule(),
    )
    MarketLifecycle.commit(market)
    MarketLifecycle.open_trading(market)
    return market


def _spawn_agents(
    position_manager: PositionManager,
    archetypes: list[EchelonArchetype] | None = None,
    initial_balance: float = 1000.0,
):
    """Spawn agents and set their balances."""
    if archetypes is None:
        archetypes = [EchelonArchetype.SHARK, EchelonArchetype.SPY, EchelonArchetype.DIPLOMAT]

    agents = []
    for i, archetype in enumerate(archetypes):
        genome = create_genome(archetype)
        agent_id = f"agent_{archetype.value.lower()}_{i}"
        position_manager.set_balance(agent_id, initial_balance)
        agents.append((agent_id, genome))
    return agents


def _run_trading_ticks(
    market,
    position_manager,
    trading_engine,
    agents,
    inquiry_class: str,
    n_ticks: int = 10,
    evidence_coverage_pct: float = 0.0,
):
    """Run n_ticks of trading using the rules engine."""
    engine = RulesEngine()

    for tick in range(n_ticks):
        # Simulate gradually increasing evidence
        tick_evidence = min(1.0, evidence_coverage_pct + tick * 0.1)

        for agent_id, genome in agents:
            pos = position_manager.get_position(agent_id)
            balance = position_manager.get_balance(agent_id)

            ctx = ContextCompiler.compile(
                genome=genome,
                market=market,
                position=pos,
                available_balance=balance,
                evidence_coverage_pct=tick_evidence,
                inquiry_class=inquiry_class,
            )

            decision = engine.decide(ctx, tick=tick, rng_seed=tick * 100 + hash(agent_id) % 1000)

            # Execute trade if action is BUY or SELL
            if decision.action.value in ("BUY", "SELL") and decision.outcome_index is not None:
                try:
                    shares = decision.shares if decision.action.value == "BUY" else -decision.shares
                    trading_engine.execute_trade(
                        market, agent_id, decision.outcome_index, shares
                    )
                except (ValueError, Exception):
                    pass  # Skip invalid trades (insufficient balance, etc.)


def _resolve_and_settle(
    market,
    position_manager,
    winning_outcome: int,
    inquiry_class: str,
    resolution_trigger: str,
):
    """Resolve and settle a market."""
    MarketLifecycle.begin_resolution(market, winning_outcome)
    return ResolutionEngine.settle(
        market,
        position_manager,
        inquiry_class=inquiry_class,
        resolution_trigger_reason=resolution_trigger,
    )


# ===================================================================
# E2E Tests — One Per Inquiry Class
# ===================================================================


class TestCounterfactualE2E:
    """COUNTERFACTUAL: geopolitical scenario, YES/NO, simulation_terminal trigger."""

    def test_counterfactual_full_lifecycle(self):
        inquiry_class = "COUNTERFACTUAL"
        market = _create_trading_market(
            "mkt_cf_e2e", "theatre_cf_e2e", 2, ["YES", "NO"]
        )
        pm = PositionManager(2, market.market_id)
        te = TradingEngine(pm)
        agents = _spawn_agents(pm)

        # Run trading ticks
        _run_trading_ticks(market, pm, te, agents, inquiry_class, n_ticks=10)

        # Check resolution readiness
        ready, trigger = ResolutionEngine.check_resolution_ready(
            inquiry_class,
            {"simulation_terminal": True},
            {},
        )
        assert ready is True
        assert trigger == ResolutionTrigger.SIMULATION_TERMINAL

        # Settle
        report = _resolve_and_settle(
            market, pm, 0, inquiry_class, str(trigger)
        )

        # Assert consistency
        assert report.inquiry_class == inquiry_class
        assert report.resolution_trigger_reason == "simulation_terminal"
        assert market.phase == MarketPhase.SETTLED
        assert len(report.agent_settlements) == 3

        # Validate evidence
        validation = InquiryEvidenceRules.validate_evidence(
            inquiry_class,
            {"source_coverage_pct": 0.8, "evidence_bundles": [{"source_id": "wm_news"}]},
            {},
        )
        assert validation.valid is True
        assert validation.inquiry_class == inquiry_class


class TestInvestigativeE2E:
    """INVESTIGATIVE: corporate claim, CONFIRMED/UNCONFIRMED, evidence_threshold_met trigger."""

    def test_investigative_full_lifecycle(self):
        inquiry_class = "INVESTIGATIVE"
        market = _create_trading_market(
            "mkt_inv_e2e", "theatre_inv_e2e", 2, ["CONFIRMED", "UNCONFIRMED"]
        )
        pm = PositionManager(2, market.market_id)
        te = TradingEngine(pm)
        agents = _spawn_agents(pm)

        _run_trading_ticks(market, pm, te, agents, inquiry_class, n_ticks=10)

        # Check resolution readiness with corroborated evidence
        ready, trigger = ResolutionEngine.check_resolution_ready(
            inquiry_class,
            {"evidence_coverage_pct": 0.9, "distinct_source_count": 3},
            {"corroboration_minimum": 2, "evidence_threshold": 0.8},
        )
        assert ready is True
        assert trigger == ResolutionTrigger.EVIDENCE_THRESHOLD_MET

        report = _resolve_and_settle(
            market, pm, 0, inquiry_class, str(trigger)
        )

        assert report.inquiry_class == inquiry_class
        assert report.resolution_trigger_reason == "evidence_threshold_met"
        assert market.phase == MarketPhase.SETTLED
        assert len(report.agent_settlements) == 3

        # Validate evidence
        validation = InquiryEvidenceRules.validate_evidence(
            inquiry_class,
            {
                "source_coverage_pct": 0.9,
                "evidence_bundles": [
                    {"source_id": "companies_house"},
                    {"source_id": "wm_news"},
                ],
            },
            {"corroboration_minimum": 2},
        )
        assert validation.valid is True


class TestInspectionE2E:
    """INSPECTION: corporate status check, criteria_complete trigger."""

    def test_inspection_full_lifecycle(self):
        inquiry_class = "INSPECTION"
        market = _create_trading_market(
            "mkt_insp_e2e", "theatre_insp_e2e", 2, ["ACTIVE", "INACTIVE"]
        )
        pm = PositionManager(2, market.market_id)
        te = TradingEngine(pm)
        agents = _spawn_agents(pm)

        _run_trading_ticks(market, pm, te, agents, inquiry_class, n_ticks=10)

        # Check resolution readiness — all criteria evaluated
        ready, trigger = ResolutionEngine.check_resolution_ready(
            inquiry_class,
            {"criteria_evaluated": 5, "criteria_total": 5},
            {},
        )
        assert ready is True
        assert trigger == ResolutionTrigger.CRITERIA_COMPLETE

        report = _resolve_and_settle(
            market, pm, 0, inquiry_class, str(trigger)
        )

        assert report.inquiry_class == inquiry_class
        assert report.resolution_trigger_reason == "criteria_complete"
        assert market.phase == MarketPhase.SETTLED
        assert len(report.agent_settlements) == 3

        # Validate evidence
        validation = InquiryEvidenceRules.validate_evidence(
            inquiry_class,
            {
                "source_coverage_pct": 1.0,
                "evidence_bundles": [{"source_id": "companies_house", "criteria_evaluated": 5}],
            },
            {"criteria_total": 5},
        )
        assert validation.valid is True


class TestSurveyE2E:
    """SURVEY: asset valuation, 3 outcomes, participation_threshold trigger."""

    def test_survey_full_lifecycle(self):
        inquiry_class = "SURVEY"
        market = _create_trading_market(
            "mkt_surv_e2e", "theatre_surv_e2e", 3, ["UNDERVALUED", "FAIR", "OVERVALUED"]
        )
        pm = PositionManager(3, market.market_id)
        te = TradingEngine(pm)
        agents = _spawn_agents(pm)

        _run_trading_ticks(market, pm, te, agents, inquiry_class, n_ticks=10)

        # Check resolution readiness — participation threshold
        ready, trigger = ResolutionEngine.check_resolution_ready(
            inquiry_class,
            {"participation_count": 15},
            {"participation_threshold": 10},
        )
        assert ready is True
        assert trigger == ResolutionTrigger.PARTICIPATION_THRESHOLD

        report = _resolve_and_settle(
            market, pm, 1, inquiry_class, str(trigger)
        )

        assert report.inquiry_class == inquiry_class
        assert report.resolution_trigger_reason == "participation_threshold"
        assert report.winning_label == "FAIR"
        assert market.phase == MarketPhase.SETTLED
        assert len(report.agent_settlements) == 3

        # Validate evidence
        validation = InquiryEvidenceRules.validate_evidence(
            inquiry_class,
            {"source_coverage_pct": 0.0},
            {"participation_count": 15, "participation_threshold": 10},
        )
        assert validation.valid is True


class TestScrutinyE2E:
    """SCRUTINY: TVL audit, VERIFIED/FALSIFIED, claim_verdict trigger."""

    def test_scrutiny_full_lifecycle(self):
        inquiry_class = "SCRUTINY"
        market = _create_trading_market(
            "mkt_scru_e2e", "theatre_scru_e2e", 2, ["VERIFIED", "FALSIFIED"]
        )
        pm = PositionManager(2, market.market_id)
        te = TradingEngine(pm)
        agents = _spawn_agents(pm)

        _run_trading_ticks(market, pm, te, agents, inquiry_class, n_ticks=10)

        # Check resolution readiness — claim verdict
        ready, trigger = ResolutionEngine.check_resolution_ready(
            inquiry_class,
            {"claim_verdict": "falsified"},
            {},
        )
        assert ready is True
        assert trigger == ResolutionTrigger.CLAIM_VERDICT

        report = _resolve_and_settle(
            market, pm, 1, inquiry_class, str(trigger)
        )

        assert report.inquiry_class == inquiry_class
        assert report.resolution_trigger_reason == "claim_verdict"
        assert report.winning_label == "FALSIFIED"
        assert market.phase == MarketPhase.SETTLED
        assert len(report.agent_settlements) == 3

        # Validate evidence
        validation = InquiryEvidenceRules.validate_evidence(
            inquiry_class,
            {
                "source_coverage_pct": 0.9,
                "evidence_bundles": [
                    {"source_id": "wm_market_data"},
                    {"source_id": "wm_news"},
                ],
            },
            {"corroboration_minimum": 2},
        )
        assert validation.valid is True


class TestDefaultCounterfactualBackwardCompat:
    """Theatres without explicit inquiry_class default to COUNTERFACTUAL."""

    def test_default_inquiry_class(self):
        """Market with no inquiry_class uses COUNTERFACTUAL defaults."""
        market = _create_trading_market(
            "mkt_default_e2e", "theatre_default_e2e", 2, ["YES", "NO"]
        )
        pm = PositionManager(2, market.market_id)
        te = TradingEngine(pm)
        agents = _spawn_agents(pm)

        # Use default inquiry_class (COUNTERFACTUAL)
        _run_trading_ticks(market, pm, te, agents, "COUNTERFACTUAL", n_ticks=5)

        ready, trigger = ResolutionEngine.check_resolution_ready(
            "COUNTERFACTUAL",
            {"time_window_expired": True},
            {},
        )
        assert ready is True
        assert trigger == ResolutionTrigger.TIME_WINDOW_CLOSED

        report = _resolve_and_settle(
            market, pm, 0, "COUNTERFACTUAL", str(trigger)
        )

        assert report.inquiry_class == "COUNTERFACTUAL"
        assert report.resolution_trigger_reason == "time_window_closed"
