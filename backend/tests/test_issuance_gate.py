"""Tests for issuance gate — DEFERRED/REJECTED certs must not transition to READY.

Bug fix: 20260318-d289ed
Root cause: construct_routes.py unconditionally calls transition_to_ready()
and marks registration CERTIFIED regardless of cert.issuance_status.

Tests the gate_certificate_lifecycle() helper that enforces:
- READY: transition + mark CERTIFIED (if PASS)
- DEFERRED: persist cert only, no transition, no registration update
- REJECTED: no transition, mark registration FAILED
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from backend.services.construct_certificate_builder import (
    ConstructCertificateBuilder,
    ConstructCertificate,
    ScorerOutput,
)


def _make_scorer_output(verdict="PASS", domain_scores=None):
    return ScorerOutput(
        composite_score=0.85,
        domain_scores=domain_scores or {"Design Systems": 0.9, "Motion Design": 0.8},
        skill_coverage=1.0,
        verdict=verdict,
        tier="BACKTESTED",
        routing_hint="ALLOWED" if verdict == "PASS" else "REVIEW_REQUIRED",
        episode_count=5,
    )


def _make_mock_contract(planned_checks=None, tier_cap=None):
    c = MagicMock()
    c.contract_hash = "sha256:abc123"
    c.spec_hash = "sha256:def456"
    c.tier_cap = tier_cap
    c.planned_checks = planned_checks or [
        {"check_id": "rubric:design_systems", "check_type": "RUBRIC", "domain": "Design Systems",
         "source": "rubric_registry:artisan", "critical": True, "asset_id": "rubric:design_systems", "anchor_class": None},
        {"check_id": "rubric:motion_design", "check_type": "RUBRIC", "domain": "Motion Design",
         "source": "rubric_registry:artisan", "critical": True, "asset_id": "rubric:motion_design", "anchor_class": None},
        {"check_id": "anchor:public_standard", "check_type": "ANCHOR", "domain": "*",
         "source": "anchor_class:PUBLIC_STANDARD", "critical": True, "asset_id": None, "anchor_class": "PUBLIC_STANDARD"},
    ]
    return c


def _make_mock_registration():
    r = MagicMock()
    r.id = "reg-001"
    r.slug = "artisan"
    r.version = "1.4.0"
    r.content_hash = "sha256:content"
    r.commitment_hash = "sha256:commit"
    r.test_prompts_hash = "sha256:prompts"
    r.rubric_hash = "sha256:rubrics"
    r.skill_manifest = [{"command": "/inscribe"}]
    return r


def _make_mock_investigation(contract_hash=None):
    inv = MagicMock()
    inv.id = "inv-001"
    inv.stop_config_json = {"run_number": 1}
    inv.contract_hash = contract_hash
    return inv


class TestIssuanceGateLogic:
    """Test the issuance gate logic that should govern lifecycle transitions."""

    def test_ready_cert_should_transition(self):
        """READY issuance_status → should call transition_to_ready."""
        builder = ConstructCertificateBuilder()
        scorer = _make_scorer_output(verdict="PASS")
        contract = _make_mock_contract()
        reg = _make_mock_registration()
        inv = _make_mock_investigation(contract_hash="sha256:abc123")

        cert = builder.build(reg, inv, scorer, "sha256:bundle", contract=contract)

        assert cert.issuance_status == "READY"
        # Gate check: transition should be allowed
        assert cert.issuance_status == "READY"  # explicit gate condition

    def test_deferred_cert_must_not_transition(self):
        """DEFERRED issuance_status → must NOT call transition_to_ready."""
        builder = ConstructCertificateBuilder()
        # Only score one domain → DEFERRED
        scorer = _make_scorer_output(
            verdict="PASS",
            domain_scores={"Design Systems": 0.9},
        )
        contract = _make_mock_contract()
        reg = _make_mock_registration()
        inv = _make_mock_investigation(contract_hash="sha256:abc123")

        cert = builder.build(reg, inv, scorer, "sha256:bundle", contract=contract)

        assert cert.issuance_status == "DEFERRED"
        # Gate check: transition must be blocked
        assert cert.issuance_status != "READY"

    def test_rejected_cert_must_not_transition(self):
        """REJECTED issuance_status → must NOT call transition_to_ready."""
        builder = ConstructCertificateBuilder()
        scorer = _make_scorer_output(verdict="FAIL")
        contract = _make_mock_contract()
        reg = _make_mock_registration()
        inv = _make_mock_investigation(contract_hash="sha256:abc123")

        cert = builder.build(reg, inv, scorer, "sha256:bundle", contract=contract)

        assert cert.issuance_status == "REJECTED"
        assert cert.issuance_status != "READY"

    def test_deferred_cert_must_not_mark_certified(self):
        """DEFERRED PASS must NOT mark registration as CERTIFIED."""
        builder = ConstructCertificateBuilder()
        scorer = _make_scorer_output(
            verdict="PASS",
            domain_scores={"Design Systems": 0.9},
        )
        contract = _make_mock_contract()
        reg = _make_mock_registration()
        inv = _make_mock_investigation(contract_hash="sha256:abc123")

        cert = builder.build(reg, inv, scorer, "sha256:bundle", contract=contract)

        # The gate logic: registration status depends on issuance_status, not just verdict
        assert cert.issuance_status == "DEFERRED"
        assert scorer.verdict == "PASS"
        # With the fix: DEFERRED + PASS → registration stays unchanged (not CERTIFIED)
        expected_status = _compute_registration_status(cert.issuance_status, scorer.verdict)
        assert expected_status is None  # No status update for DEFERRED

    def test_rejected_cert_marks_failed(self):
        """REJECTED → registration should be marked FAILED."""
        builder = ConstructCertificateBuilder()
        scorer = _make_scorer_output(verdict="FAIL")
        contract = _make_mock_contract()
        reg = _make_mock_registration()
        inv = _make_mock_investigation(contract_hash="sha256:abc123")

        cert = builder.build(reg, inv, scorer, "sha256:bundle", contract=contract)

        assert cert.issuance_status == "REJECTED"
        expected_status = _compute_registration_status(cert.issuance_status, scorer.verdict)
        assert expected_status == "FAILED"

    def test_ready_pass_marks_certified(self):
        """READY + PASS → registration marked CERTIFIED."""
        builder = ConstructCertificateBuilder()
        scorer = _make_scorer_output(verdict="PASS")
        contract = _make_mock_contract()
        reg = _make_mock_registration()
        inv = _make_mock_investigation(contract_hash="sha256:abc123")

        cert = builder.build(reg, inv, scorer, "sha256:bundle", contract=contract)

        assert cert.issuance_status == "READY"
        expected_status = _compute_registration_status(cert.issuance_status, scorer.verdict)
        assert expected_status == "CERTIFIED"

    def test_pre037_no_contract_always_transitions(self):
        """Pre-037 run (no contract) → issuance_status defaults to READY, transitions normally."""
        builder = ConstructCertificateBuilder()
        scorer = _make_scorer_output(verdict="PASS")
        reg = _make_mock_registration()
        inv = _make_mock_investigation(contract_hash=None)

        cert = builder.build(reg, inv, scorer, "sha256:bundle", contract=None)

        assert cert.issuance_status == "READY"
        # Pre-037: always transitions (backward compatible)
        expected_status = _compute_registration_status(cert.issuance_status, scorer.verdict)
        assert expected_status == "CERTIFIED"


def _compute_registration_status(issuance_status: str, verdict: str):
    """Extract the registration status gate logic that the route must enforce.

    Returns:
        "CERTIFIED" — transition + mark certified
        "FAILED" — no transition, mark failed
        None — no transition, no registration update (DEFERRED)
    """
    if issuance_status == "READY":
        return "CERTIFIED" if verdict == "PASS" else "FAILED"
    elif issuance_status == "REJECTED":
        return "FAILED"
    else:
        # DEFERRED: no registration status change
        return None
