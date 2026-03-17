"""Cycle 024 Sprint 4 — API Routes + First Certification Run tests.

Tests:
1. Registration request schema validates correctly and rejects bad input
2. Run detail response schema contains episodes with activity fields
3. Full certification flow: register → score → certificate → soju payload
4. Artisan registration data matches committed hash
5. Certificate issued with composite score, verdict, tier, and routing hint
"""

from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError

from backend.schemas.construct_schemas import (
    ConstructRegistrationRequest,
    ConstructRegistrationResponse,
    RunDetailResponse,
    EpisodeDetail,
    EpisodeCaptureRequest,
    CertificateResponse,
)
from backend.services.construct_scorer import ConstructScorer
from backend.services.construct_certificate_builder import (
    ConstructCertificateBuilder,
    ScorerOutput,
)
from backend.services.construct_evidence_bundle import ConstructEvidenceBundleBuilder
from backend.services.test_prompt_registry import TestPromptRegistry
from backend.data.construct_rubrics.artisan_rubrics import ARTISAN_RUBRICS


class TestRegistrationSchema:
    """Test registration request/response Pydantic schemas."""

    def test_registration_request_validates(self):
        """POST /api/constructs/register schema validates correctly."""
        req = ConstructRegistrationRequest(
            slug="artisan",
            version="1.4.0",
            content_hash="sha256:0956e7a3785e48194ed98c85e1282a5cf9e89ae6f9c3dde70f4b0f910",
            skill_manifest=[
                {"command": "/distill", "domain": "Design Systems"},
                {"command": "/iterate", "domain": "Visual Refinement"},
            ],
            domain_claims=["Design Systems", "Visual Refinement"],
            test_prompts_hash="sha256:abc123",
            rubric_hash="sha256:def456",
        )

        assert req.slug == "artisan"
        assert req.version == "1.4.0"
        assert len(req.skill_manifest) == 2

    def test_registration_request_rejects_missing_fields(self):
        """Schema rejects requests with missing required fields."""
        with pytest.raises(ValidationError):
            ConstructRegistrationRequest(
                slug="artisan",
                # Missing version, content_hash, etc.
            )

    def test_registration_response_serializes(self):
        """Registration response serializes correctly."""
        resp = ConstructRegistrationResponse(
            id="reg-001",
            slug="artisan",
            version="1.4.0",
            status="REGISTERED",
            commitment_hash="sha256:commitment789",
            skill_count=14,
        )

        data = resp.model_dump()
        assert data["status"] == "REGISTERED"
        assert data["skill_count"] == 14


class TestRunDetailSchema:
    """Test run detail response schema with episode activity."""

    def test_run_detail_contains_episodes_with_activity_fields(self):
        """GET .../runs/:runNumber response has episodes with activity fields."""
        episodes = [
            EpisodeDetail(
                prompt_index=1,
                skill_command="/distill",
                domain="Design Systems",
                timing_ms=1500,
                content_hash="sha256:aaa",
                scores={"output_conformance": 0.85, "domain_accuracy": 0.90},
            ),
            EpisodeDetail(
                prompt_index=2,
                skill_command="/iterate",
                domain="Visual Refinement",
                timing_ms=2100,
                content_hash="sha256:bbb",
                scores={"output_conformance": 0.78},
            ),
        ]

        response = RunDetailResponse(
            run_number=1,
            investigation_id="inv-001",
            status="ACTIVE",
            registration={"slug": "artisan", "version": "1.4.0"},
            commitment_hash="sha256:commitment123",
            episodes=episodes,
            domain_coverage={"Design Systems": 1, "Visual Refinement": 1},
            skill_coverage={"/distill": 1, "/iterate": 1},
        )

        data = response.model_dump()
        assert len(data["episodes"]) == 2
        assert data["episodes"][0]["skill_command"] == "/distill"
        assert data["episodes"][0]["domain"] == "Design Systems"
        assert data["episodes"][0]["scores"]["output_conformance"] == 0.85
        assert data["domain_coverage"]["Design Systems"] == 1
        assert data["skill_coverage"]["/distill"] == 1


class TestFirstCertificationRun:
    """Test the first Artisan v1.4.0 certification flow end-to-end."""

    def test_artisan_registration_matches_committed_hash(self):
        """Artisan v1.4.0 test prompts hash is stable and verifiable."""
        registry = TestPromptRegistry()
        prompt_set = registry.get_prompts("artisan", "1.4.0")

        assert prompt_set is not None
        assert prompt_set.count == 12
        assert prompt_set.prompts_hash.startswith("sha256:")

        # Verify hash matches
        assert registry.verify_hash("artisan", "1.4.0", prompt_set.prompts_hash) is True

    def test_full_certification_flow(self):
        """Full flow: score episodes → build certificate → format soju payload."""
        # 1. Score episodes using rubrics
        scorer = ConstructScorer(rubrics=ARTISAN_RUBRICS)

        # Score a Design Systems episode
        ds_scores = scorer.score_episode(
            skill_command="/distill",
            domain="Design Systems",
            prompt_text="Analyze the design system tokens",
            output_text=(
                "This component uses OKLCH color tokens via CSS custom properties "
                "(--color-primary-500, --spacing-4). The component architecture follows "
                "a compound component pattern with props and children slots. "
                "The rationale is separation of concerns."
            ),
        )
        assert ds_scores["output_conformance"] > 0
        assert ds_scores["domain_accuracy"] > 0

        # 2. Aggregate
        domain_scores = {
            "Design Systems": 0.82,
            "Motion Design": 0.75,
            "Visual Refinement": 0.78,
            "Taste Compounding": 0.70,
            "Frontend Best Practices": 0.80,
        }
        composite = scorer.aggregate_composite(domain_scores)
        assert composite > 0.60

        # 3. Compute verdict + tier + routing
        skill_coverage = 0.80  # 4/5 unique skills
        verdict = scorer.compute_verdict(composite, skill_coverage)
        assert verdict == "PASS"

        tier = scorer.compute_tier(12)
        assert tier == "UNVERIFIED"

        routing = scorer.compute_routing_hint(verdict, tier)
        assert routing == "REVIEW_REQUIRED"

        # 4. Build evidence bundle
        bundle_builder = ConstructEvidenceBundleBuilder()
        items = [
            MagicMock(construct_meta_json={
                "prompt_index": i,
                "skill_command": "/distill",
                "domain": "Design Systems",
                "output_hash": f"sha256:hash{i}",
                "scores": {"output_conformance": 0.80},
                "timing_ms": 1000 + i * 100,
            })
            for i in range(1, 13)
        ]
        manifest = bundle_builder.build_manifest(items)
        bundle_hash = bundle_builder.compute_bundle_hash(manifest)
        assert bundle_hash.startswith("sha256:")

        # 5. Build certificate
        cert_builder = ConstructCertificateBuilder()
        scorer_output = ScorerOutput(
            composite_score=composite,
            domain_scores=domain_scores,
            skill_coverage=skill_coverage,
            verdict=verdict,
            tier=tier,
            routing_hint=routing,
            episode_count=12,
        )

        reg = MagicMock()
        reg.slug = "artisan"
        reg.version = "1.4.0"
        reg.content_hash = "sha256:0956e7a3785e48194ed98c85e1282a5cf9e89ae6f9c3dde70f4b0f910"
        reg.commitment_hash = "sha256:commitment123"
        reg.test_prompts_hash = "sha256:prompts456"
        reg.rubric_hash = "sha256:rubric789"

        inv = MagicMock()
        inv.stop_config_json = {"run_number": 1}

        cert = cert_builder.build(reg, inv, scorer_output, bundle_hash)
        cert_json = cert_builder.to_certificate_json(cert)

        # Validate certificate contents
        assert cert_json["construct_slug"] == "artisan"
        assert cert_json["construct_version"] == "1.4.0"
        assert cert_json["composite_score"] == composite
        assert cert_json["verdict"] == "PASS"
        assert cert_json["verification_tier"] == "UNVERIFIED"
        assert cert_json["skill_coverage"] == 0.80
        assert cert_json["episode_count"] == 12
        assert cert.certificate_id.startswith("CERT-C")

        # 6. Format Soju payload
        soju_payload = cert_builder.to_soju_payload(cert_json)
        assert soju_payload["verification_tier"] == "UNVERIFIED"
        assert "certificate_json" in soju_payload
        assert soju_payload["certificate_json"]["construct_slug"] == "artisan"

    def test_certificate_response_schema(self):
        """Certificate response schema contains all required fields."""
        resp = CertificateResponse(
            certificate_id="CERT-C1234",
            construct_slug="artisan",
            construct_version="1.4.0",
            composite_score=0.77,
            domain_scores={"Design Systems": 0.82, "Motion Design": 0.75},
            skill_coverage=0.80,
            verification_tier="UNVERIFIED",
            verdict="PASS",
            routing_decision="REVIEW_REQUIRED",
            evidence_bundle_hash="sha256:bundle123",
            episode_count=12,
        )

        data = resp.model_dump()
        assert data["certificate_id"] == "CERT-C1234"
        assert data["composite_score"] == 0.77
        assert data["verdict"] == "PASS"
        assert data["routing_decision"] == "REVIEW_REQUIRED"
