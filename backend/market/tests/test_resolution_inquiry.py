"""Tests for inquiry-class-aware resolution triggers.

Cycle-014, Sprint 2 — Task 1.
"""
from __future__ import annotations

import pytest

from backend.market.resolution import ResolutionEngine, ResolutionTrigger, SettlementReport


class TestResolutionTriggerEnum:
    """ResolutionTrigger enum has exactly 6 values."""

    def test_enum_values(self):
        assert len(ResolutionTrigger) == 6
        assert ResolutionTrigger.SIMULATION_TERMINAL.value == "simulation_terminal"
        assert ResolutionTrigger.EVIDENCE_THRESHOLD_MET.value == "evidence_threshold_met"
        assert ResolutionTrigger.CRITERIA_COMPLETE.value == "criteria_complete"
        assert ResolutionTrigger.PARTICIPATION_THRESHOLD.value == "participation_threshold"
        assert ResolutionTrigger.CLAIM_VERDICT.value == "claim_verdict"
        assert ResolutionTrigger.TIME_WINDOW_CLOSED.value == "time_window_closed"

    def test_str_serialisation(self):
        assert str(ResolutionTrigger.SIMULATION_TERMINAL) == "simulation_terminal"
        assert str(ResolutionTrigger.CLAIM_VERDICT) == "claim_verdict"


class TestSettlementReportFields:
    """SettlementReport has inquiry_class and resolution_trigger_reason fields."""

    def test_default_values(self):
        report = SettlementReport(
            market_id="test",
            winning_outcome=0,
            winning_label="YES",
            total_payout=100.0,
            market_maker_pnl=-10.0,
            agent_settlements=[],
            commitment_hash="a" * 64,
            settlement_hash="b" * 64,
        )
        assert report.inquiry_class == "COUNTERFACTUAL"
        assert report.resolution_trigger_reason == "simulation_terminal"

    def test_explicit_values(self):
        report = SettlementReport(
            market_id="test",
            winning_outcome=0,
            winning_label="YES",
            total_payout=100.0,
            market_maker_pnl=-10.0,
            agent_settlements=[],
            commitment_hash="a" * 64,
            settlement_hash="b" * 64,
            inquiry_class="SCRUTINY",
            resolution_trigger_reason="claim_verdict",
        )
        assert report.inquiry_class == "SCRUTINY"
        assert report.resolution_trigger_reason == "claim_verdict"


class TestCheckResolutionReadyCounterfactual:
    """COUNTERFACTUAL: simulation terminal or evidence threshold."""

    def test_simulation_terminal(self):
        ready, trigger = ResolutionEngine.check_resolution_ready(
            "COUNTERFACTUAL",
            {"simulation_terminal": True},
            {},
        )
        assert ready is True
        assert trigger == ResolutionTrigger.SIMULATION_TERMINAL

    def test_evidence_threshold_met(self):
        ready, trigger = ResolutionEngine.check_resolution_ready(
            "COUNTERFACTUAL",
            {"evidence_coverage_pct": 0.85},
            {"evidence_threshold": 0.8},
        )
        assert ready is True
        assert trigger == ResolutionTrigger.EVIDENCE_THRESHOLD_MET

    def test_evidence_below_threshold(self):
        ready, trigger = ResolutionEngine.check_resolution_ready(
            "COUNTERFACTUAL",
            {"evidence_coverage_pct": 0.5},
            {"evidence_threshold": 0.8},
        )
        assert ready is False

    def test_time_window_closed(self):
        ready, trigger = ResolutionEngine.check_resolution_ready(
            "COUNTERFACTUAL",
            {"evidence_coverage_pct": 0.5, "time_window_expired": True},
            {"evidence_threshold": 0.8},
        )
        assert ready is True
        assert trigger == ResolutionTrigger.TIME_WINDOW_CLOSED


class TestCheckResolutionReadyInvestigative:
    """INVESTIGATIVE: corroboration + coverage or time window."""

    def test_evidence_threshold_met(self):
        ready, trigger = ResolutionEngine.check_resolution_ready(
            "INVESTIGATIVE",
            {"evidence_coverage_pct": 0.9, "distinct_source_count": 3},
            {"corroboration_minimum": 2, "evidence_threshold": 0.8},
        )
        assert ready is True
        assert trigger == ResolutionTrigger.EVIDENCE_THRESHOLD_MET

    def test_insufficient_sources(self):
        ready, trigger = ResolutionEngine.check_resolution_ready(
            "INVESTIGATIVE",
            {"evidence_coverage_pct": 0.9, "distinct_source_count": 1},
            {"corroboration_minimum": 2, "evidence_threshold": 0.8},
        )
        assert ready is False

    def test_time_window_fallback(self):
        ready, trigger = ResolutionEngine.check_resolution_ready(
            "INVESTIGATIVE",
            {"evidence_coverage_pct": 0.3, "distinct_source_count": 1, "time_window_expired": True},
            {"corroboration_minimum": 2, "evidence_threshold": 0.8},
        )
        assert ready is True
        assert trigger == ResolutionTrigger.TIME_WINDOW_CLOSED


class TestCheckResolutionReadyInspection:
    """INSPECTION: all criteria evaluated."""

    def test_criteria_complete(self):
        ready, trigger = ResolutionEngine.check_resolution_ready(
            "INSPECTION",
            {"criteria_evaluated": 5, "criteria_total": 5},
            {},
        )
        assert ready is True
        assert trigger == ResolutionTrigger.CRITERIA_COMPLETE

    def test_criteria_incomplete(self):
        ready, trigger = ResolutionEngine.check_resolution_ready(
            "INSPECTION",
            {"criteria_evaluated": 3, "criteria_total": 5},
            {},
        )
        assert ready is False

    def test_time_window_fallback(self):
        ready, trigger = ResolutionEngine.check_resolution_ready(
            "INSPECTION",
            {"criteria_evaluated": 3, "criteria_total": 5, "time_window_expired": True},
            {},
        )
        assert ready is True
        assert trigger == ResolutionTrigger.TIME_WINDOW_CLOSED


class TestCheckResolutionReadySurvey:
    """SURVEY: participation threshold or time window."""

    def test_participation_threshold(self):
        ready, trigger = ResolutionEngine.check_resolution_ready(
            "SURVEY",
            {"participation_count": 15},
            {"participation_threshold": 10},
        )
        assert ready is True
        assert trigger == ResolutionTrigger.PARTICIPATION_THRESHOLD

    def test_below_participation(self):
        ready, trigger = ResolutionEngine.check_resolution_ready(
            "SURVEY",
            {"participation_count": 5},
            {"participation_threshold": 10},
        )
        assert ready is False

    def test_time_window_fallback(self):
        ready, trigger = ResolutionEngine.check_resolution_ready(
            "SURVEY",
            {"participation_count": 5, "time_window_expired": True},
            {"participation_threshold": 10},
        )
        assert ready is True
        assert trigger == ResolutionTrigger.TIME_WINDOW_CLOSED


class TestCheckResolutionReadyScrutiny:
    """SCRUTINY: claim verdict or time window."""

    def test_claim_verified(self):
        ready, trigger = ResolutionEngine.check_resolution_ready(
            "SCRUTINY",
            {"claim_verdict": "verified"},
            {},
        )
        assert ready is True
        assert trigger == ResolutionTrigger.CLAIM_VERDICT

    def test_claim_falsified(self):
        ready, trigger = ResolutionEngine.check_resolution_ready(
            "SCRUTINY",
            {"claim_verdict": "falsified"},
            {},
        )
        assert ready is True
        assert trigger == ResolutionTrigger.CLAIM_VERDICT

    def test_no_verdict(self):
        ready, trigger = ResolutionEngine.check_resolution_ready(
            "SCRUTINY",
            {"claim_verdict": None},
            {},
        )
        assert ready is False

    def test_time_window_fallback(self):
        ready, trigger = ResolutionEngine.check_resolution_ready(
            "SCRUTINY",
            {"claim_verdict": None, "time_window_expired": True},
            {},
        )
        assert ready is True
        assert trigger == ResolutionTrigger.TIME_WINDOW_CLOSED


class TestCheckResolutionReadyCaseInsensitive:
    """inquiry_class parameter is case-insensitive."""

    def test_lowercase(self):
        ready, trigger = ResolutionEngine.check_resolution_ready(
            "counterfactual",
            {"simulation_terminal": True},
            {},
        )
        assert ready is True

    def test_mixed_case(self):
        ready, trigger = ResolutionEngine.check_resolution_ready(
            "Survey",
            {"participation_count": 15},
            {"participation_threshold": 10},
        )
        assert ready is True


class TestCheckResolutionReadyUnknown:
    """Unknown inquiry class falls back to time_window_closed."""

    def test_unknown_not_ready(self):
        ready, trigger = ResolutionEngine.check_resolution_ready(
            "UNKNOWN_TYPE",
            {},
            {},
        )
        assert ready is False

    def test_unknown_time_expired(self):
        ready, trigger = ResolutionEngine.check_resolution_ready(
            "UNKNOWN_TYPE",
            {"time_window_expired": True},
            {},
        )
        assert ready is True
        assert trigger == ResolutionTrigger.TIME_WINDOW_CLOSED
