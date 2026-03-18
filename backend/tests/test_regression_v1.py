"""V1 regression tests — ensures pre-037 flows remain unchanged.

Cycle 037: Contract-Backed Verification Infrastructure.

Tests the pure-logic regression guarantees without DB/asyncpg dependency.
Validates backward compatibility of ConstructCertificateBuilder, schemas,
and the hash chain when no contract is present.
"""

from backend.services.construct_certificate_builder import (
    ConstructCertificateBuilder,
    ScorerOutput,
)
from backend.schemas.construct_schemas import (
    ConstructRegistrationRequest,
    ConstructRegistrationResponse,
    ConstructRegistrationListItem,
    CertificateResponse,
)


def _make_scorer_output():
    return ScorerOutput(
        composite_score=0.82,
        domain_scores={"Design Systems": 0.85, "Motion Design": 0.79},
        skill_coverage=1.0,
        verdict="PASS",
        tier="BACKTESTED",
        routing_hint="ALLOWED",
        episode_count=5,
    )


def _make_mock_registration():
    class MockReg:
        pass
    r = MockReg()
    r.slug = "artisan"
    r.version = "1.4.0"
    r.content_hash = "sha256:v1content"
    r.commitment_hash = "sha256:v1commit"
    r.test_prompts_hash = "sha256:v1prompts"
    r.rubric_hash = "sha256:v1rubrics"
    return r


def _make_mock_investigation():
    class MockInv:
        pass
    inv = MockInv()
    inv.stop_config_json = {"run_number": 1, "construct_slug": "artisan", "construct_version": "1.4.0"}
    inv.contract_hash = None  # Pre-037 — no contract
    return inv


class TestV1Regression:
    def test_registration_schema_unchanged(self):
        """V1 registration request/response schemas still validate correctly."""
        # Request
        req = ConstructRegistrationRequest(
            slug="artisan",
            version="1.4.0",
            content_hash="sha256:abc",
            skill_manifest=[{"command": "/inscribe", "domain": "Design Systems"}],
            domain_claims=["Design Systems"],
            test_prompts_hash="sha256:prompts",
            rubric_hash="sha256:rubrics",
        )
        assert req.slug == "artisan"
        assert len(req.skill_manifest) == 1

        # Response
        resp = ConstructRegistrationResponse(
            id="reg-001",
            slug="artisan",
            version="1.4.0",
            status="REGISTERED",
            commitment_hash="sha256:commit",
            skill_count=1,
        )
        assert resp.status == "REGISTERED"

        # List item
        item = ConstructRegistrationListItem(
            slug="artisan",
            version="1.4.0",
            status="REGISTERED",
            skill_count=1,
            commitment_hash="sha256:commit",
        )
        assert item.commitment_hash == "sha256:commit"

    def test_certificate_builder_no_contract(self):
        """V1 certificate flow: build without contract → existing fields present, new fields null."""
        builder = ConstructCertificateBuilder()
        scorer = _make_scorer_output()
        reg = _make_mock_registration()
        inv = _make_mock_investigation()

        cert = builder.build(reg, inv, scorer, "sha256:v1bundle")

        # V1 fields present
        assert cert.certificate_id.startswith("CERT-C")
        assert cert.construct_slug == "artisan"
        assert cert.construct_version == "1.4.0"
        assert cert.composite_score == 0.82
        assert cert.verdict == "PASS"
        assert cert.verification_tier == "BACKTESTED"
        assert cert.evidence_bundle_hash == "sha256:v1bundle"
        assert cert.episode_count == 5

        # New contract fields null/default
        assert cert.contract_hash is None
        assert cert.spec_hash is None
        assert cert.check_plan is None
        assert cert.remediation is None
        assert cert.issuance_status == "READY"

    def test_certificate_json_backward_compat(self):
        """Pre-037 certificate JSON excludes contract fields entirely."""
        builder = ConstructCertificateBuilder()
        scorer = _make_scorer_output()
        reg = _make_mock_registration()
        inv = _make_mock_investigation()

        cert = builder.build(reg, inv, scorer, "sha256:v1bundle")
        cert_json = builder.to_certificate_json(cert)

        # V1 fields present
        assert "certificate_id" in cert_json
        assert "construct_slug" in cert_json
        assert "composite_score" in cert_json
        assert "domain_scores" in cert_json
        assert "verdict" in cert_json
        assert "evidence_bundle_hash" in cert_json
        assert "reproducibility_pins" in cert_json

        # Contract fields NOT present (pre-037)
        assert "contract_hash" not in cert_json
        assert "spec_hash" not in cert_json
        assert "check_plan" not in cert_json
        assert "remediation" not in cert_json

    def test_certificate_response_schema_backward_compat(self):
        """CertificateResponse schema: new fields are Optional with defaults."""
        # V1 response (no contract fields)
        resp = CertificateResponse(
            certificate_id="CERT-CABCD",
            construct_slug="artisan",
            construct_version="1.4.0",
            composite_score=0.82,
            domain_scores={"Design Systems": 0.85},
            skill_coverage=1.0,
            verification_tier="BACKTESTED",
            verdict="PASS",
            routing_decision="ALLOWED",
            evidence_bundle_hash="sha256:bundle",
            episode_count=5,
        )

        # V1 fields correct
        assert resp.certificate_id == "CERT-CABCD"
        assert resp.verdict == "PASS"
        assert resp.composite_score == 0.82

        # New fields have defaults (backward compat)
        assert resp.contract_hash is None
        assert resp.spec_hash is None
        assert resp.issuance_status == "READY"
        assert resp.check_plan is None
        assert resp.remediation is None
