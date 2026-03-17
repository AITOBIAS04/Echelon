"""Construct Certificate Builder — certificate issuance for construct verification.

Wraps InvestigationCertificateBuilder, injects construct-specific fields,
persists to InvestigationCertificateRecord, and produces Soju-compatible payloads.
"""

import hashlib
import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

logger = logging.getLogger(__name__)


@dataclass
class ScorerOutput:
    """Output from ConstructScorer aggregation."""
    composite_score: float
    domain_scores: dict[str, float]
    skill_coverage: float
    verdict: str
    tier: str
    routing_hint: str
    episode_count: int


@dataclass
class ConstructCertificate:
    """Construct-specific certificate data before persistence."""
    certificate_id: str
    construct_slug: str
    construct_version: str
    content_hash: str
    commitment_hash: str
    composite_score: float
    domain_scores: dict[str, float]
    skill_coverage: float
    verification_tier: str
    verdict: str
    routing_hint: str
    evidence_bundle_hash: str
    episode_count: int
    reproducibility_pins: dict


class ConstructCertificateBuilder:
    """Builds and persists construct verification certificates."""

    def build(
        self,
        registration,
        investigation,
        scorer_output: ScorerOutput,
        evidence_bundle_hash: str,
    ) -> ConstructCertificate:
        """Build a ConstructCertificate from registration, investigation, and scorer output.

        Certificate ID format: CERT-CXXXX (C prefix for construct certificates).
        """
        cert_id = f"CERT-C{str(uuid4())[:4].upper()}"

        config = investigation.stop_config_json or {}

        cert = ConstructCertificate(
            certificate_id=cert_id,
            construct_slug=registration.slug,
            construct_version=registration.version,
            content_hash=registration.content_hash,
            commitment_hash=registration.commitment_hash,
            composite_score=scorer_output.composite_score,
            domain_scores=scorer_output.domain_scores,
            skill_coverage=scorer_output.skill_coverage,
            verification_tier=scorer_output.tier,
            verdict=scorer_output.verdict,
            routing_hint=scorer_output.routing_hint,
            evidence_bundle_hash=evidence_bundle_hash,
            episode_count=scorer_output.episode_count,
            reproducibility_pins={
                "test_prompts_hash": registration.test_prompts_hash,
                "rubric_hash": registration.rubric_hash,
                "run_number": config.get("run_number", 0),
            },
        )

        logger.info(
            "Built certificate %s for %s:%s (verdict=%s, tier=%s)",
            cert_id, registration.slug, registration.version,
            scorer_output.verdict, scorer_output.tier,
        )
        return cert

    def to_certificate_json(self, cert: ConstructCertificate) -> dict:
        """Convert ConstructCertificate to the certificate_json dict for persistence.

        This dict is stored in InvestigationCertificateRecord.certificate_json.
        """
        return {
            "certificate_id": cert.certificate_id,
            "construct_slug": cert.construct_slug,
            "construct_version": cert.construct_version,
            "content_hash": cert.content_hash,
            "commitment_hash": cert.commitment_hash,
            "composite_score": cert.composite_score,
            "domain_scores": cert.domain_scores,
            "skill_coverage": cert.skill_coverage,
            "verification_tier": cert.verification_tier,
            "verdict": cert.verdict,
            "evidence_bundle_hash": cert.evidence_bundle_hash,
            "episode_count": cert.episode_count,
            "reproducibility_pins": cert.reproducibility_pins,
        }

    def to_soju_payload(self, certificate_json: dict) -> dict:
        """Format certificate for Soju's POST /v1/packs/:slug/verification endpoint.

        Returns { verification_tier, certificate_json }.
        """
        return {
            "verification_tier": certificate_json.get("verification_tier", "UNVERIFIED"),
            "certificate_json": certificate_json,
        }

    def compute_routing_decision(self, scorer_output: ScorerOutput) -> tuple[str, str]:
        """Compute routing_decision and routing_reason for InvestigationCertificateRecord.

        Returns (routing_decision, routing_reason).
        """
        if scorer_output.verdict == "PASS":
            if scorer_output.tier == "BACKTESTED":
                return "ALLOWED", "construct_verified_backtested"
            return "REVIEW_REQUIRED", "construct_verified_unverified_tier"
        return "REVIEW_REQUIRED", "construct_verification_failed"
