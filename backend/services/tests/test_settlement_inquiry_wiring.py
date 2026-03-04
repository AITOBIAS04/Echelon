"""Tests for F2 — Settlement wiring of inquiry_class.

Verifies: settle_market() calls check_resolution_ready() to determine
the trigger reason, then passes inquiry_class and trigger through to
SettlementReport.
"""
from __future__ import annotations

import pytest

from backend.market.lifecycle import MarketLifecycle
from backend.market.positions import PositionManager
from backend.market.resolution import ResolutionTrigger
from backend.market.trading import TradingEngine
from backend.services.market_theatre_bridge import MarketTheatreBridge


def _create_and_trade(bridge: MarketTheatreBridge, theatre_id: str = "t1") -> None:
    """Create a market, open trading, and execute one trade."""
    state = bridge.create_market_for_theatre(
        theatre_id=theatre_id,
        market_id="m1",
        b=100.0,
        n_outcomes=2,
        outcome_labels=["YES", "NO"],
    )
    MarketLifecycle.commit(state.market)
    MarketLifecycle.open_trading(state.market)
    state.position_manager.set_balance("agent-1", 1000.0)
    state.trading_engine.execute_trade(
        market=state.market, agent_id="agent-1", outcome_index=0, shares=10.0,
    )


class TestSettlementCallsCheckResolutionReady:
    """settle_market() routes through check_resolution_ready()."""

    def test_default_counterfactual_time_expired(self) -> None:
        """Default evidence_state has time_window_expired=True → time_window_closed trigger."""
        bridge = MarketTheatreBridge()
        _create_and_trade(bridge)
        report = bridge.settle_market("t1", winning_outcome=0)
        assert report.inquiry_class == "COUNTERFACTUAL"
        assert report.resolution_trigger_reason == "time_window_closed"

    def test_counterfactual_simulation_terminal(self) -> None:
        """Explicit simulation_terminal evidence → simulation_terminal trigger."""
        bridge = MarketTheatreBridge()
        _create_and_trade(bridge)
        report = bridge.settle_market(
            "t1",
            winning_outcome=0,
            inquiry_class="COUNTERFACTUAL",
            evidence_state={"simulation_terminal": True},
        )
        assert report.inquiry_class == "COUNTERFACTUAL"
        assert report.resolution_trigger_reason == "simulation_terminal"

    def test_inspection_criteria_complete(self) -> None:
        """INSPECTION with all criteria met → criteria_complete trigger."""
        bridge = MarketTheatreBridge()
        _create_and_trade(bridge)
        report = bridge.settle_market(
            "t1",
            winning_outcome=0,
            inquiry_class="INSPECTION",
            evidence_state={"criteria_evaluated": 5, "criteria_total": 5},
        )
        assert report.inquiry_class == "INSPECTION"
        assert report.resolution_trigger_reason == "criteria_complete"

    def test_scrutiny_claim_verdict(self) -> None:
        """SCRUTINY with verdict → claim_verdict trigger."""
        bridge = MarketTheatreBridge()
        _create_and_trade(bridge)
        report = bridge.settle_market(
            "t1",
            winning_outcome=1,
            inquiry_class="SCRUTINY",
            evidence_state={"claim_verdict": "verified"},
        )
        assert report.inquiry_class == "SCRUTINY"
        assert report.resolution_trigger_reason == "claim_verdict"
        assert report.winning_label == "NO"

    def test_investigative_evidence_threshold(self) -> None:
        """INVESTIGATIVE with corroboration + coverage → evidence_threshold_met."""
        bridge = MarketTheatreBridge()
        _create_and_trade(bridge)
        report = bridge.settle_market(
            "t1",
            winning_outcome=0,
            inquiry_class="INVESTIGATIVE",
            evidence_state={
                "distinct_source_count": 3,
                "evidence_coverage_pct": 0.9,
            },
            theatre_config={"corroboration_minimum": 2, "evidence_threshold": 0.8},
        )
        assert report.inquiry_class == "INVESTIGATIVE"
        assert report.resolution_trigger_reason == "evidence_threshold_met"

    def test_survey_participation_threshold(self) -> None:
        """SURVEY with enough participation → participation_threshold trigger."""
        bridge = MarketTheatreBridge()
        _create_and_trade(bridge)
        report = bridge.settle_market(
            "t1",
            winning_outcome=0,
            inquiry_class="SURVEY",
            evidence_state={"participation_count": 15},
            theatre_config={"participation_threshold": 10},
        )
        assert report.inquiry_class == "SURVEY"
        assert report.resolution_trigger_reason == "participation_threshold"

    def test_fallback_time_window_when_evidence_insufficient(self) -> None:
        """When evidence insufficient but time expired, settles with time_window_closed."""
        bridge = MarketTheatreBridge()
        _create_and_trade(bridge)
        report = bridge.settle_market(
            "t1",
            winning_outcome=0,
            inquiry_class="INVESTIGATIVE",
            evidence_state={
                "distinct_source_count": 0,
                "evidence_coverage_pct": 0.1,
                "time_window_expired": True,
            },
        )
        assert report.inquiry_class == "INVESTIGATIVE"
        assert report.resolution_trigger_reason == "time_window_closed"

    def test_investigative_refuses_before_evidence_threshold(self) -> None:
        """INVESTIGATIVE theatre without evidence threshold → settlement refused."""
        bridge = MarketTheatreBridge()
        _create_and_trade(bridge)
        with pytest.raises(ValueError, match="Settlement refused.*not ready"):
            bridge.settle_market(
                "t1",
                winning_outcome=0,
                inquiry_class="INVESTIGATIVE",
                evidence_state={
                    "distinct_source_count": 0,
                    "evidence_coverage_pct": 0.1,
                    # time_window_expired NOT set → not ready
                },
            )

    def test_force_overrides_readiness_check(self) -> None:
        """force=True allows settlement even when not ready."""
        bridge = MarketTheatreBridge()
        _create_and_trade(bridge)
        report = bridge.settle_market(
            "t1",
            winning_outcome=0,
            inquiry_class="INVESTIGATIVE",
            evidence_state={
                "distinct_source_count": 0,
                "evidence_coverage_pct": 0.1,
            },
            force=True,
        )
        assert report.inquiry_class == "INVESTIGATIVE"
        assert report.resolution_trigger_reason == "time_window_closed"
