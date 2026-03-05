"""Tests for stop-condition integration in resolution engine.

Cycle-014c codex remediation — F1.
"""
from __future__ import annotations

from unittest.mock import patch, MagicMock

import pytest

from backend.market.resolution import ResolutionEngine, ResolutionTrigger
from backend.services.market_theatre_bridge import MarketTheatreBridge


def _make_claim_graph(supported_count: int = 2, total_count: int = 2):
    """Build a mock ClaimGraph with controllable status summary."""
    cg = MagicMock()
    cg.claims = [MagicMock() for _ in range(total_count)]
    cg.get_status_summary.return_value = {"supported": supported_count}
    return cg


def _make_evidence_envelope():
    """Build a minimal mock EvidenceEnvelope."""
    return MagicMock()


class TestStopConditionMet:
    def test_stop_condition_met_returns_new_trigger(self):
        """EVIDENCE_THRESHOLD with sufficient claims -> STOP_CONDITION_MET."""
        cg = _make_claim_graph(supported_count=3, total_count=3)
        ee = _make_evidence_envelope()

        ready, trigger = ResolutionEngine.check_resolution_ready(
            inquiry_class="INVESTIGATIVE",
            evidence_state={},
            theatre_config={},
            stop_condition="EVIDENCE_THRESHOLD",
            stop_config={"min_supported_claims": 2, "min_corroboration_score": 0.5},
            claim_graph=cg,
            evidence_envelope=ee,
            time_remaining=3600.0,
        )

        assert ready is True
        assert trigger == ResolutionTrigger.STOP_CONDITION_MET

    def test_stop_condition_not_met_falls_through(self):
        """Evaluator returns False -> standard per-class logic applies."""
        cg = _make_claim_graph(supported_count=0, total_count=3)
        ee = _make_evidence_envelope()

        ready, trigger = ResolutionEngine.check_resolution_ready(
            inquiry_class="INVESTIGATIVE",
            evidence_state={"time_window_expired": True},
            theatre_config={},
            stop_condition="EVIDENCE_THRESHOLD",
            stop_config={"min_supported_claims": 5},
            claim_graph=cg,
            evidence_envelope=ee,
            time_remaining=3600.0,
        )

        # Stop condition not met, falls through to INVESTIGATIVE time_window logic
        assert ready is True
        assert trigger == ResolutionTrigger.TIME_WINDOW_CLOSED

    def test_stop_condition_none_preserves_behaviour(self):
        """No stop params -> unchanged behaviour."""
        ready, trigger = ResolutionEngine.check_resolution_ready(
            inquiry_class="COUNTERFACTUAL",
            evidence_state={"simulation_terminal": True},
            theatre_config={},
        )

        assert ready is True
        assert trigger == ResolutionTrigger.SIMULATION_TERMINAL

    def test_stop_condition_without_claim_graph_uses_scalar_path(self):
        """stop_condition set but claim_graph=None -> scalar evaluator runs."""
        ready, trigger = ResolutionEngine.check_resolution_ready(
            inquiry_class="INVESTIGATIVE",
            evidence_state={
                "supported_claims": 5,
                "corroboration_score": 0.8,
            },
            theatre_config={},
            stop_condition="EVIDENCE_THRESHOLD",
            stop_config={"min_supported_claims": 3, "min_corroboration_score": 0.5},
            claim_graph=None,
            evidence_envelope=_make_evidence_envelope(),
        )

        assert ready is True
        assert trigger == ResolutionTrigger.STOP_CONDITION_MET

    def test_stop_condition_without_claim_graph_unmet_falls_through(self):
        """Scalar path not met -> falls through to per-class logic."""
        ready, trigger = ResolutionEngine.check_resolution_ready(
            inquiry_class="INVESTIGATIVE",
            evidence_state={
                "time_window_expired": True,
                "supported_claims": 0,
                "corroboration_score": 0.0,
            },
            theatre_config={},
            stop_condition="EVIDENCE_THRESHOLD",
            stop_config={"min_supported_claims": 5},
            claim_graph=None,
        )

        # Scalar stop condition not met, falls through to INVESTIGATIVE time_window
        assert ready is True
        assert trigger == ResolutionTrigger.TIME_WINDOW_CLOSED


class TestScalarStopConditionEvaluation:
    """Production-path stop-condition evaluation using evidence_state scalars."""

    def test_evidence_threshold_scalar_met(self):
        """EVIDENCE_THRESHOLD via scalar evidence_state -> STOP_CONDITION_MET."""
        ready, trigger = ResolutionEngine.check_resolution_ready(
            inquiry_class="INVESTIGATIVE",
            evidence_state={
                "supported_claims": 4,
                "corroboration_score": 0.75,
            },
            theatre_config={},
            stop_condition="EVIDENCE_THRESHOLD",
            stop_config={"min_supported_claims": 3, "min_corroboration_score": 0.5},
        )

        assert ready is True
        assert trigger == ResolutionTrigger.STOP_CONDITION_MET

    def test_evidence_threshold_scalar_not_met(self):
        """Unmet scalar thresholds -> not resolved via stop-condition."""
        ready, trigger = ResolutionEngine.check_resolution_ready(
            inquiry_class="INVESTIGATIVE",
            evidence_state={
                "supported_claims": 1,
                "corroboration_score": 0.2,
            },
            theatre_config={},
            stop_condition="EVIDENCE_THRESHOLD",
            stop_config={"min_supported_claims": 3, "min_corroboration_score": 0.5},
        )

        # Stop condition not met, per-class INVESTIGATIVE logic also not met
        assert ready is False

    def test_outcome_resolution_time_expired(self):
        """OUTCOME_RESOLUTION via time_window_expired=True without object graph."""
        ready, trigger = ResolutionEngine.check_resolution_ready(
            inquiry_class="INVESTIGATIVE",
            evidence_state={"time_window_expired": True},
            theatre_config={},
            stop_condition="OUTCOME_RESOLUTION",
            stop_config={},
        )

        assert ready is True
        assert trigger == ResolutionTrigger.STOP_CONDITION_MET

    def test_outcome_resolution_time_remaining_expired(self):
        """OUTCOME_RESOLUTION via time_remaining <= 0."""
        ready, trigger = ResolutionEngine.check_resolution_ready(
            inquiry_class="INVESTIGATIVE",
            evidence_state={},
            theatre_config={},
            stop_condition="OUTCOME_RESOLUTION",
            stop_config={},
            time_remaining=-1.0,
        )

        assert ready is True
        assert trigger == ResolutionTrigger.STOP_CONDITION_MET

    def test_outcome_resolution_not_expired(self):
        """OUTCOME_RESOLUTION with time remaining -> not ready via stop-condition."""
        ready, trigger = ResolutionEngine.check_resolution_ready(
            inquiry_class="INVESTIGATIVE",
            evidence_state={},
            theatre_config={},
            stop_condition="OUTCOME_RESOLUTION",
            stop_config={},
            time_remaining=3600.0,
        )

        # Stop condition not met, per-class INVESTIGATIVE also not met
        assert ready is False

    def test_sponsor_defined_milestone_reached(self):
        """SPONSOR_DEFINED milestone in past -> STOP_CONDITION_MET."""
        ready, trigger = ResolutionEngine.check_resolution_ready(
            inquiry_class="INVESTIGATIVE",
            evidence_state={
                "current_time": "2026-06-15T00:00:00+00:00",
            },
            theatre_config={},
            stop_condition="SPONSOR_DEFINED",
            stop_config={"milestone_timestamp": "2026-06-01T00:00:00+00:00"},
        )

        assert ready is True
        assert trigger == ResolutionTrigger.STOP_CONDITION_MET

    def test_sponsor_defined_milestone_not_reached(self):
        """SPONSOR_DEFINED milestone in future -> not ready via stop-condition."""
        ready, trigger = ResolutionEngine.check_resolution_ready(
            inquiry_class="INVESTIGATIVE",
            evidence_state={
                "current_time": "2026-05-01T00:00:00+00:00",
            },
            theatre_config={},
            stop_condition="SPONSOR_DEFINED",
            stop_config={"milestone_timestamp": "2026-06-01T00:00:00+00:00"},
        )

        assert ready is False

    def test_sponsor_defined_missing_milestone(self):
        """SPONSOR_DEFINED without milestone_timestamp -> fail safely."""
        ready, trigger = ResolutionEngine.check_resolution_ready(
            inquiry_class="INVESTIGATIVE",
            evidence_state={},
            theatre_config={},
            stop_condition="SPONSOR_DEFINED",
            stop_config={},
        )

        assert ready is False

    def test_invalid_stop_condition_fails_safely(self):
        """Unknown stop_condition value on INVESTIGATIVE -> fail safely, fall through."""
        ready, trigger = ResolutionEngine.check_resolution_ready(
            inquiry_class="INVESTIGATIVE",
            evidence_state={"time_window_expired": True},
            theatre_config={},
            stop_condition="BANANA",
            stop_config={},
        )

        # Invalid stop condition fails safely, falls through to per-class
        assert ready is True
        assert trigger == ResolutionTrigger.TIME_WINDOW_CLOSED


class TestStopConditionIgnoredForNonInvestigative:
    """Non-INVESTIGATIVE classes ignore stop_condition entirely."""

    @pytest.mark.parametrize("ic,evidence,expected_trigger", [
        ("COUNTERFACTUAL", {"simulation_terminal": True}, ResolutionTrigger.SIMULATION_TERMINAL),
        ("INSPECTION", {"criteria_evaluated": 5, "criteria_total": 5}, ResolutionTrigger.CRITERIA_COMPLETE),
        ("SURVEY", {"participation_count": 20}, ResolutionTrigger.PARTICIPATION_THRESHOLD),
        ("SCRUTINY", {"claim_verdict": "verified"}, ResolutionTrigger.CLAIM_VERDICT),
    ])
    def test_stop_condition_ignored_for_non_investigative(self, ic, evidence, expected_trigger):
        """Valid stop_condition + met thresholds still ignored for non-INVESTIGATIVE."""
        ready, trigger = ResolutionEngine.check_resolution_ready(
            inquiry_class=ic,
            evidence_state={
                **evidence,
                "supported_claims": 100,
                "corroboration_score": 1.0,
            },
            theatre_config={"participation_threshold": 10},
            stop_condition="EVIDENCE_THRESHOLD",
            stop_config={"min_supported_claims": 1, "min_corroboration_score": 0.1},
        )

        assert ready is True
        assert trigger == expected_trigger
        assert trigger != ResolutionTrigger.STOP_CONDITION_MET


class TestBridgeThreadsStopParams:
    def test_bridge_threads_stop_params(self):
        """settle_market() with stop params -> passes through correctly."""
        bridge = MarketTheatreBridge()
        bridge.create_market_for_theatre(
            theatre_id="t1",
            market_id="m1",
            b=100.0,
            n_outcomes=2,
            outcome_labels=["YES", "NO"],
        )
        # Transition to TRADING first
        from backend.market.state import MarketPhase
        bridge.transition_market("t1", MarketPhase.COMMITTED)
        bridge.transition_market("t1", MarketPhase.TRADING)

        cg = _make_claim_graph(supported_count=3, total_count=3)
        ee = _make_evidence_envelope()

        report = bridge.settle_market(
            theatre_id="t1",
            winning_outcome=0,
            inquiry_class="INVESTIGATIVE",
            stop_condition="EVIDENCE_THRESHOLD",
            stop_config={"min_supported_claims": 2},
            claim_graph=cg,
            evidence_envelope=ee,
            time_remaining=3600.0,
        )

        assert report.resolution_trigger_reason == "stop_condition_met"

    def test_bridge_scalar_stop_condition_without_object_graph(self):
        """settle_market() with scalar evidence_state only -> stop_condition_met."""
        bridge = MarketTheatreBridge()
        bridge.create_market_for_theatre(
            theatre_id="t2",
            market_id="m2",
            b=100.0,
            n_outcomes=2,
            outcome_labels=["YES", "NO"],
        )
        from backend.market.state import MarketPhase
        bridge.transition_market("t2", MarketPhase.COMMITTED)
        bridge.transition_market("t2", MarketPhase.TRADING)

        report = bridge.settle_market(
            theatre_id="t2",
            winning_outcome=0,
            inquiry_class="INVESTIGATIVE",
            evidence_state={
                "supported_claims": 5,
                "corroboration_score": 0.9,
            },
            stop_condition="EVIDENCE_THRESHOLD",
            stop_config={"min_supported_claims": 3, "min_corroboration_score": 0.5},
        )

        assert report.resolution_trigger_reason == "stop_condition_met"

    def test_bridge_scalar_stop_condition_not_met_refuses(self):
        """settle_market() with unmet scalar stop condition -> refuses."""
        bridge = MarketTheatreBridge()
        bridge.create_market_for_theatre(
            theatre_id="t3",
            market_id="m3",
            b=100.0,
            n_outcomes=2,
            outcome_labels=["YES", "NO"],
        )
        from backend.market.state import MarketPhase
        bridge.transition_market("t3", MarketPhase.COMMITTED)
        bridge.transition_market("t3", MarketPhase.TRADING)

        with pytest.raises(ValueError, match="resolution not ready"):
            bridge.settle_market(
                theatre_id="t3",
                winning_outcome=0,
                inquiry_class="INVESTIGATIVE",
                evidence_state={
                    "supported_claims": 0,
                    "corroboration_score": 0.0,
                },
                stop_condition="EVIDENCE_THRESHOLD",
                stop_config={"min_supported_claims": 5, "min_corroboration_score": 0.8},
            )
