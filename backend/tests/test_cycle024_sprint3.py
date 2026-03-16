"""Cycle 024 Sprint 3 — Certificate Issuance + Evidence Bundle tests.

Tests:
1. Manifest contains correct number of invocations matching evidence items
2. Bundle hash is deterministic (same evidence items → same hash)
3. Certificate JSON contains all required construct fields
4. Soju payload format matches { verification_tier, certificate_json } contract
5. routing_decision set correctly: PASS → ALLOWED, FAIL → REVIEW_REQUIRED
6. Certificate persistence round-trip (build → to_certificate_json → fields present)
7. Registration status flow (PASS → routing_decision ALLOWED)
"""

from dataclasses import dataclass
from unittest.mock import MagicMock

import pytest

from backend.services.construct_evidence_bundle import ConstructEvidenceBundleBuilder
from backend.services.construct_certificate_builder import (
    ConstructCertificateBuilder,
    ScorerOutput,
)


def _make_evidence_item(prompt_index, skill_command, domain, output_hash, timing_ms=100, scores=None):
    """Create a mock evidence item with construct_meta_json."""
    item = MagicMock()
    item.construct_meta_json = {
        "prompt_index": prompt_index,
        "skill_command": skill_command,
        "domain": domain,
        "output_hash": output_hash,
        "scores": scores or {},
        "timing_ms": timing_ms,
    }
    return item


class TestConstructEvidenceBundleBuilder:
    """Test evidence manifest building and hashing."""

    def test_manifest_contains_correct_invocation_count(self):
        """Manifest contains correct number of invocations matching evidence items."""
        builder = ConstructEvidenceBundleBuilder()

        items = [
            _make_evidence_item(1, "/distill", "Design Systems", "sha256:aaa"),
            _make_evidence_item(2, "/distill", "Design Systems", "sha256:bbb"),
            _make_evidence_item(3, "/iterate", "Visual Refinement", "sha256:ccc"),
            _make_evidence_item(4, "/motion", "Motion Design", "sha256:ddd"),
            _make_evidence_item(5, "/synthesize", "Taste Compounding", "sha256:eee"),
        ]

        manifest = builder.build_manifest(items)

        assert len(manifest) == 5
        assert manifest[0]["prompt_index"] == 1
        assert manifest[0]["skill_command"] == "/distill"
        assert manifest[4]["prompt_index"] == 5
        assert manifest[4]["domain"] == "Taste Compounding"

    def test_bundle_hash_is_deterministic(self):
        """Bundle hash is deterministic — same evidence items → same hash."""
        builder = ConstructEvidenceBundleBuilder()

        items = [
            _make_evidence_item(1, "/distill", "Design Systems", "sha256:aaa", 150),
            _make_evidence_item(2, "/iterate", "Visual Refinement", "sha256:bbb", 200),
        ]

        manifest1 = builder.build_manifest(items)
        hash1 = builder.compute_bundle_hash(manifest1)

        manifest2 = builder.build_manifest(items)
        hash2 = builder.compute_bundle_hash(manifest2)

        assert hash1 == hash2
        assert hash1.startswith("sha256:")

        # Different items → different hash
        items_different = [
            _make_evidence_item(1, "/distill", "Design Systems", "sha256:zzz", 150),
            _make_evidence_item(2, "/iterate", "Visual Refinement", "sha256:bbb", 200),
        ]
        manifest3 = builder.build_manifest(items_different)
        hash3 = builder.compute_bundle_hash(manifest3)
        assert hash3 != hash1


class TestConstructCertificateBuilder:
    """Test certificate building, serialization, and routing."""

    def _make_registration(self):
        reg = MagicMock()
        reg.slug = "artisan"
        reg.version = "1.4.0"
        reg.content_hash = "sha256:content123"
        reg.commitment_hash = "sha256:commitment456"
        reg.test_prompts_hash = "sha256:prompts789"
        reg.rubric_hash = "sha256:rubric012"
        return reg

    def _make_investigation(self):
        inv = MagicMock()
        inv.stop_config_json = {
            "run_number": 1,
            "construct_registration_id": "reg-001",
        }
        return inv

    def _make_scorer_output(self, verdict="PASS", tier="BACKTESTED"):
        return ScorerOutput(
            composite_score=0.78,
            domain_scores={
                "Design Systems": 0.85,
                "Motion Design": 0.72,
                "Visual Refinement": 0.80,
            },
            skill_coverage=0.786,
            verdict=verdict,
            tier=tier,
            routing_hint="ALLOWED" if verdict == "PASS" and tier == "BACKTESTED" else "REVIEW_REQUIRED",
            episode_count=12,
        )

    def test_certificate_json_contains_all_required_fields(self):
        """Certificate JSON contains all required construct fields."""
        builder = ConstructCertificateBuilder()
        reg = self._make_registration()
        inv = self._make_investigation()
        scorer_output = self._make_scorer_output()

        cert = builder.build(reg, inv, scorer_output, "sha256:bundle123")
        cert_json = builder.to_certificate_json(cert)

        # Required fields per SDD
        assert cert_json["construct_slug"] == "artisan"
        assert cert_json["construct_version"] == "1.4.0"
        assert cert_json["content_hash"] == "sha256:content123"
        assert cert_json["commitment_hash"] == "sha256:commitment456"
        assert cert_json["composite_score"] == 0.78
        assert cert_json["domain_scores"]["Design Systems"] == 0.85
        assert cert_json["skill_coverage"] == 0.786
        assert cert_json["verification_tier"] == "BACKTESTED"
        assert cert_json["verdict"] == "PASS"
        assert cert_json["evidence_bundle_hash"] == "sha256:bundle123"
        assert cert_json["episode_count"] == 12

        # Reproducibility pins
        pins = cert_json["reproducibility_pins"]
        assert pins["test_prompts_hash"] == "sha256:prompts789"
        assert pins["rubric_hash"] == "sha256:rubric012"
        assert pins["run_number"] == 1

        # Certificate ID format
        assert cert.certificate_id.startswith("CERT-C")

    def test_soju_payload_format(self):
        """Soju payload format matches { verification_tier, certificate_json } contract."""
        builder = ConstructCertificateBuilder()
        reg = self._make_registration()
        inv = self._make_investigation()
        scorer_output = self._make_scorer_output()

        cert = builder.build(reg, inv, scorer_output, "sha256:bundle123")
        cert_json = builder.to_certificate_json(cert)
        payload = builder.to_soju_payload(cert_json)

        assert "verification_tier" in payload
        assert "certificate_json" in payload
        assert payload["verification_tier"] == "BACKTESTED"
        assert payload["certificate_json"]["construct_slug"] == "artisan"
        assert payload["certificate_json"]["construct_version"] == "1.4.0"

    def test_routing_decision_pass_allowed(self):
        """routing_decision: PASS + BACKTESTED → ALLOWED."""
        builder = ConstructCertificateBuilder()

        # PASS + BACKTESTED → ALLOWED
        scorer_pass = self._make_scorer_output(verdict="PASS", tier="BACKTESTED")
        decision, reason = builder.compute_routing_decision(scorer_pass)
        assert decision == "ALLOWED"
        assert "verified" in reason

    def test_routing_decision_fail_review_required(self):
        """routing_decision: FAIL → REVIEW_REQUIRED."""
        builder = ConstructCertificateBuilder()

        scorer_fail = self._make_scorer_output(verdict="FAIL", tier="BACKTESTED")
        decision, reason = builder.compute_routing_decision(scorer_fail)
        assert decision == "REVIEW_REQUIRED"
        assert "failed" in reason

    def test_routing_decision_pass_unverified_review_required(self):
        """routing_decision: PASS + UNVERIFIED → REVIEW_REQUIRED."""
        builder = ConstructCertificateBuilder()

        scorer_unverified = self._make_scorer_output(verdict="PASS", tier="UNVERIFIED")
        decision, reason = builder.compute_routing_decision(scorer_unverified)
        assert decision == "REVIEW_REQUIRED"
        assert "unverified" in reason

    def test_certificate_round_trip(self):
        """Build → to_certificate_json → all fields present and consistent."""
        builder = ConstructCertificateBuilder()
        reg = self._make_registration()
        inv = self._make_investigation()
        scorer_output = self._make_scorer_output()

        cert = builder.build(reg, inv, scorer_output, "sha256:bundle456")
        cert_json = builder.to_certificate_json(cert)

        # Round-trip check: all dataclass fields present in JSON
        assert cert_json["certificate_id"] == cert.certificate_id
        assert cert_json["composite_score"] == cert.composite_score
        assert cert_json["skill_coverage"] == cert.skill_coverage
        assert cert_json["verification_tier"] == cert.verification_tier
        assert cert_json["evidence_bundle_hash"] == cert.evidence_bundle_hash
