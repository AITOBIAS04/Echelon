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
    # Contract-backed fields (cycle-037+, None for pre-037 runs)
    contract_hash: Optional[str] = None
    spec_hash: Optional[str] = None
    issuance_status: str = "READY"
    check_plan: Optional[dict] = None
    remediation: Optional[dict] = None


class ConstructCertificateBuilder:
    """Builds and persists construct verification certificates."""

    def build(
        self,
        registration,
        investigation,
        scorer_output: ScorerOutput,
        evidence_bundle_hash: str,
        contract=None,
    ) -> ConstructCertificate:
        """Build a ConstructCertificate from registration, investigation, and scorer output.

        Certificate ID format: CERT-CXXXX (C prefix for construct certificates).

        Args:
            registration: ConstructRegistration row.
            investigation: Investigation row.
            scorer_output: Aggregated scorer output.
            evidence_bundle_hash: Evidence bundle hash.
            contract: Optional EvaluationContract (cycle-037+). When provided,
                populates contract_hash, spec_hash, check_plan, and issuance_status.
        """
        cert_id = f"CERT-C{str(uuid4())[:4].upper()}"

        config = investigation.stop_config_json or {}

        # Contract-backed fields (cycle-037+)
        contract_hash = None
        spec_hash = None
        check_plan = None
        issuance_status = "READY"
        remediation = None

        if contract is not None:
            contract_hash = contract.contract_hash
            spec_hash = contract.spec_hash
            check_plan = self._build_check_plan(contract, scorer_output)
            issuance_status = self.compute_issuance_status(
                scorer_output.verdict, check_plan, contract.tier_cap
            )
            if issuance_status == "DEFERRED":
                remediation = self._build_remediation(check_plan)

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
            contract_hash=contract_hash,
            spec_hash=spec_hash,
            issuance_status=issuance_status,
            check_plan=check_plan,
            remediation=remediation,
        )

        logger.info(
            "Built certificate %s for %s:%s (verdict=%s, tier=%s, issuance=%s)",
            cert_id, registration.slug, registration.version,
            scorer_output.verdict, scorer_output.tier, issuance_status,
        )
        return cert

    def to_certificate_json(self, cert: ConstructCertificate) -> dict:
        """Convert ConstructCertificate to the certificate_json dict for persistence.

        This dict is stored in InvestigationCertificateRecord.certificate_json.
        Contract-backed fields are included only when present (cycle-037+).
        """
        result = {
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
        # Contract-backed fields (cycle-037+)
        if cert.contract_hash is not None:
            result["contract_hash"] = cert.contract_hash
            result["spec_hash"] = cert.spec_hash
            result["issuance_status"] = cert.issuance_status
            result["check_plan"] = cert.check_plan
            if cert.remediation is not None:
                result["remediation"] = cert.remediation
        return result

    @staticmethod
    def compute_issuance_status(
        verdict: str,
        check_plan: Optional[dict],
        tier_cap: Optional[str] = None,
    ) -> str:
        """Compute issuance status from verdict, check plan, and tier cap.

        Returns:
            READY: All checks executed and verdict is PASS.
            DEFERRED: Some checks not executed but verdict is PASS.
            REJECTED: Verdict is not PASS.
        """
        if verdict != "PASS":
            return "REJECTED"

        if tier_cap is not None:
            return "DEFERRED"

        if check_plan is not None:
            executed = check_plan.get("total_executed", 0)
            planned = check_plan.get("total_planned", 0)
            if planned > 0 and executed < planned:
                return "DEFERRED"

        return "READY"

    @staticmethod
    def _build_check_plan(contract, scorer_output: ScorerOutput) -> dict:
        """Build planned-vs-executed check plan from contract and scorer output.

        Checks are marked EXECUTED if the scorer has a domain score for the check's
        domain, NOT_EXECUTED otherwise.
        """
        planned_checks = contract.planned_checks or []
        scored_domains = set(scorer_output.domain_scores.keys())

        entries = []
        executed_count = 0

        for check in planned_checks:
            check_domain = check.get("domain", "")
            check_type = check.get("check_type", "")

            # RUBRIC checks are EXECUTED if domain was scored
            # ANCHOR checks are always EXECUTED (they're structural)
            # BENCHMARK checks are EXECUTED if domain was scored
            if check_type == "ANCHOR":
                status = "EXECUTED"
            elif check_domain in scored_domains:
                status = "EXECUTED"
            else:
                status = "NOT_EXECUTED"

            if status == "EXECUTED":
                executed_count += 1

            score = scorer_output.domain_scores.get(check_domain) if check_domain != "*" else None

            entries.append({
                "id": check.get("check_id", ""),
                "type": check_type,
                "status": status,
                "score": score,
                "reason": None if status == "EXECUTED" else "domain_not_scored",
            })

        return {
            "total_planned": len(planned_checks),
            "total_executed": executed_count,
            "checks": entries,
        }

    @staticmethod
    def _build_remediation(check_plan: dict) -> dict:
        """Build remediation payload for DEFERRED certificates."""
        missing = [
            {"check_id": c["id"], "type": c["type"], "reason": c.get("reason", "not_executed")}
            for c in check_plan.get("checks", [])
            if c["status"] == "NOT_EXECUTED"
        ]

        planned = check_plan.get("total_planned", 0)
        executed = check_plan.get("total_executed", 0)

        return {
            "status": "DEFERRED",
            "reason": f"{len(missing)} of {planned} checks not executed",
            "missing_checks": missing,
            "executed_count": executed,
            "planned_count": planned,
            "recommendation": "Re-run with all required assets available to achieve READY status.",
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
