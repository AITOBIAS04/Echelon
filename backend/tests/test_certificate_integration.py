"""Tests for certificate integration with contract-backed verification.

Cycle 037: Contract-Backed Verification Infrastructure.

Tests the certificate builder's issuance logic (READY/DEFERRED/REJECTED)
and check_plan generation without DB/asyncpg dependency.
"""

from backend.services.construct_certificate_builder import (
    ConstructCertificateBuilder,
    ScorerOutput,
)


def _make_scorer_output(
    verdict="PASS",
    domain_scores=None,
    composite=0.85,
    coverage=1.0,
    tier="BACKTESTED",
    episodes=5,
):
    return ScorerOutput(
        composite_score=composite,
        domain_scores=domain_scores or {"Design Systems": 0.9, "Motion Design": 0.8},
        skill_coverage=coverage,
        verdict=verdict,
        tier=tier,
        routing_hint="ALLOWED" if verdict == "PASS" else "REVIEW_REQUIRED",
        episode_count=episodes,
    )


def _make_mock_contract(
    planned_checks=None,
    tier_cap=None,
    contract_hash="sha256:abc123",
    spec_hash="sha256:def456",
):
    """Minimal contract-like object for builder tests."""

    class MockContract:
        pass

    c = MockContract()
    c.contract_hash = contract_hash
    c.spec_hash = spec_hash
    c.tier_cap = tier_cap
    c.planned_checks = planned_checks or [
        {
            "check_id": "rubric:artisan:design_systems",
            "check_type": "RUBRIC",
            "domain": "Design Systems",
            "source": "rubric_registry:artisan",
            "critical": True,
            "asset_id": "rubric:artisan:design_systems",
            "anchor_class": None,
        },
        {
            "check_id": "rubric:artisan:motion_design",
            "check_type": "RUBRIC",
            "domain": "Motion Design",
            "source": "rubric_registry:artisan",
            "critical": True,
            "asset_id": "rubric:artisan:motion_design",
            "anchor_class": None,
        },
        {
            "check_id": "anchor:public_standard",
            "check_type": "ANCHOR",
            "domain": "*",
            "source": "anchor_class:PUBLIC_STANDARD",
            "critical": True,
            "asset_id": None,
            "anchor_class": "PUBLIC_STANDARD",
        },
        {
            "check_id": "anchor:deterministic_check",
            "check_type": "ANCHOR",
            "domain": "*",
            "source": "anchor_class:DETERMINISTIC_CHECK",
            "critical": False,
            "asset_id": None,
            "anchor_class": "DETERMINISTIC_CHECK",
        },
    ]
    return c


def _make_mock_registration(slug="artisan", version="1.4.0"):
    class MockReg:
        pass

    r = MockReg()
    r.slug = slug
    r.version = version
    r.content_hash = "sha256:content"
    r.commitment_hash = "sha256:commit"
    r.test_prompts_hash = "sha256:prompts"
    r.rubric_hash = "sha256:rubrics"
    return r


def _make_mock_investigation(contract_hash=None):
    class MockInv:
        pass

    inv = MockInv()
    inv.stop_config_json = {"run_number": 1}
    inv.contract_hash = contract_hash
    return inv


class TestCertificateIssuance:
    def test_all_checks_pass_ready(self):
        """All checks executed + PASS verdict → issuance_status = READY."""
        builder = ConstructCertificateBuilder()
        scorer = _make_scorer_output(verdict="PASS")
        contract = _make_mock_contract()
        reg = _make_mock_registration()
        inv = _make_mock_investigation(contract_hash="sha256:abc123")

        cert = builder.build(reg, inv, scorer, "sha256:bundle", contract=contract)

        assert cert.issuance_status == "READY"
        assert cert.contract_hash == "sha256:abc123"
        assert cert.spec_hash == "sha256:def456"
        assert cert.check_plan is not None
        assert cert.check_plan["total_executed"] == cert.check_plan["total_planned"]
        assert cert.remediation is None

    def test_missing_checks_deferred(self):
        """Some checks not executed but PASS → DEFERRED with remediation."""
        builder = ConstructCertificateBuilder()
        # Only score one domain, leaving the other NOT_EXECUTED
        scorer = _make_scorer_output(
            verdict="PASS",
            domain_scores={"Design Systems": 0.9},
        )
        contract = _make_mock_contract()
        reg = _make_mock_registration()
        inv = _make_mock_investigation(contract_hash="sha256:abc123")

        cert = builder.build(reg, inv, scorer, "sha256:bundle", contract=contract)

        assert cert.issuance_status == "DEFERRED"
        assert cert.remediation is not None
        assert cert.remediation["status"] == "DEFERRED"
        assert len(cert.remediation["missing_checks"]) > 0

    def test_fail_verdict_rejected(self):
        """FAIL verdict → REJECTED regardless of check plan."""
        builder = ConstructCertificateBuilder()
        scorer = _make_scorer_output(verdict="FAIL")
        contract = _make_mock_contract()
        reg = _make_mock_registration()
        inv = _make_mock_investigation(contract_hash="sha256:abc123")

        cert = builder.build(reg, inv, scorer, "sha256:bundle", contract=contract)

        assert cert.issuance_status == "REJECTED"
        assert cert.remediation is None  # No remediation for REJECTED

    def test_remediation_payload_details(self):
        """Remediation payload includes missing check IDs and reasons."""
        builder = ConstructCertificateBuilder()
        scorer = _make_scorer_output(
            verdict="PASS",
            domain_scores={"Design Systems": 0.9},
        )
        contract = _make_mock_contract()
        reg = _make_mock_registration()
        inv = _make_mock_investigation(contract_hash="sha256:abc123")

        cert = builder.build(reg, inv, scorer, "sha256:bundle", contract=contract)

        assert cert.remediation is not None
        missing = cert.remediation["missing_checks"]
        missing_ids = [m["check_id"] for m in missing]
        assert "rubric:artisan:motion_design" in missing_ids
        assert cert.remediation["executed_count"] < cert.remediation["planned_count"]
        assert "recommendation" in cert.remediation

    def test_check_plan_executed_not_executed(self):
        """check_plan shows EXECUTED/NOT_EXECUTED per check."""
        builder = ConstructCertificateBuilder()
        scorer = _make_scorer_output(
            verdict="PASS",
            domain_scores={"Design Systems": 0.9},
        )
        contract = _make_mock_contract()
        reg = _make_mock_registration()
        inv = _make_mock_investigation(contract_hash="sha256:abc123")

        cert = builder.build(reg, inv, scorer, "sha256:bundle", contract=contract)

        cp = cert.check_plan
        assert cp is not None
        statuses = {c["id"]: c["status"] for c in cp["checks"]}

        # RUBRIC for Design Systems should be EXECUTED (domain scored)
        assert statuses["rubric:artisan:design_systems"] == "EXECUTED"
        # RUBRIC for Motion Design should be NOT_EXECUTED (domain not scored)
        assert statuses["rubric:artisan:motion_design"] == "NOT_EXECUTED"
        # ANCHOR checks always EXECUTED
        assert statuses["anchor:public_standard"] == "EXECUTED"
        assert statuses["anchor:deterministic_check"] == "EXECUTED"

    def test_pre037_run_no_contract_fields(self):
        """Pre-037 run (no contract_hash) → certificate omits contract fields."""
        builder = ConstructCertificateBuilder()
        scorer = _make_scorer_output(verdict="PASS")
        reg = _make_mock_registration()
        inv = _make_mock_investigation(contract_hash=None)

        # Build without contract (pre-037)
        cert = builder.build(reg, inv, scorer, "sha256:bundle", contract=None)

        assert cert.contract_hash is None
        assert cert.spec_hash is None
        assert cert.check_plan is None
        assert cert.remediation is None
        assert cert.issuance_status == "READY"  # Default

        # Verify to_certificate_json doesn't include contract fields
        cert_json = builder.to_certificate_json(cert)
        assert "contract_hash" not in cert_json
        assert "spec_hash" not in cert_json
        assert "check_plan" not in cert_json
