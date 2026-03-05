"""Tests for Stop Condition Evaluator — 5 tests."""

from datetime import datetime, timezone, timedelta

from backend.investigation.stop_conditions import InvestigationStopConditionEvaluator
from backend.investigation.claim_graph import ClaimGraph, ClaimType, ClaimStatus
from backend.investigation.evidence_envelope import EvidenceEnvelope
from backend.investigation.models import ProvenanceClass


def _make_evaluator() -> InvestigationStopConditionEvaluator:
    return InvestigationStopConditionEvaluator()


def _make_envelope() -> EvidenceEnvelope:
    envelope = EvidenceEnvelope()
    envelope.submit(b"doc", ProvenanceClass.PUBLIC_PRIMARY, "text/plain", "src")
    return envelope


class TestOutcomeResolution:
    def test_outcome_resolution_time_expired(self):
        """Ready when time runs out (time_remaining <= 0)."""
        evaluator = _make_evaluator()
        cg = ClaimGraph()
        envelope = _make_envelope()

        ready, reason = evaluator.evaluate(
            stop_condition="OUTCOME_RESOLUTION",
            stop_config={},
            claim_graph=cg,
            evidence_envelope=envelope,
            time_remaining=-1.0,
        )

        assert ready is True
        assert reason == "time_window_expired"

    def test_outcome_resolution_time_remaining(self):
        """Not ready while time left (time_remaining > 0)."""
        evaluator = _make_evaluator()
        cg = ClaimGraph()
        envelope = _make_envelope()

        ready, reason = evaluator.evaluate(
            stop_condition="OUTCOME_RESOLUTION",
            stop_config={},
            claim_graph=cg,
            evidence_envelope=envelope,
            time_remaining=3600.0,
        )

        assert ready is False
        assert "3600" in reason


class TestEvidenceThreshold:
    def test_evidence_threshold_met(self):
        """N SUPPORTED claims -> ready."""
        evaluator = _make_evaluator()
        envelope = _make_envelope()

        cg = ClaimGraph()
        c1 = cg.add_claim("Claim 1", ClaimType.FACT, ["E001"])
        c2 = cg.add_claim("Claim 2", ClaimType.FACT, ["E001"])
        cg.update_claim_status(
            c1.claim_id, ClaimStatus.SUPPORTED, 0.9, ["group_a", "group_b"]
        )
        cg.update_claim_status(
            c2.claim_id, ClaimStatus.SUPPORTED, 0.8, ["group_a", "group_b"]
        )

        ready, reason = evaluator.evaluate(
            stop_condition="EVIDENCE_THRESHOLD",
            stop_config={"min_supported_claims": 2, "min_corroboration_score": 0.5},
            claim_graph=cg,
            evidence_envelope=envelope,
            time_remaining=3600.0,
        )

        assert ready is True
        assert reason == "evidence_threshold_met"

    def test_evidence_threshold_not_met(self):
        """Insufficient SUPPORTED claims -> not ready."""
        evaluator = _make_evaluator()
        envelope = _make_envelope()

        cg = ClaimGraph()
        c1 = cg.add_claim("Claim 1", ClaimType.FACT, ["E001"])
        # Only 1 SUPPORTED, but we require 3
        cg.update_claim_status(
            c1.claim_id, ClaimStatus.SUPPORTED, 0.9, ["group_a", "group_b"]
        )

        ready, reason = evaluator.evaluate(
            stop_condition="EVIDENCE_THRESHOLD",
            stop_config={"min_supported_claims": 3},
            claim_graph=cg,
            evidence_envelope=envelope,
            time_remaining=3600.0,
        )

        assert ready is False
        assert "1/3" in reason


class TestSponsorDefined:
    def test_sponsor_defined_milestone(self):
        """Milestone reached -> ready."""
        evaluator = _make_evaluator()
        cg = ClaimGraph()
        envelope = _make_envelope()

        # Set milestone in the past
        past = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()

        ready, reason = evaluator.evaluate(
            stop_condition="SPONSOR_DEFINED",
            stop_config={"milestone_timestamp": past},
            claim_graph=cg,
            evidence_envelope=envelope,
            time_remaining=3600.0,
        )

        assert ready is True
        assert reason == "milestone_reached"
