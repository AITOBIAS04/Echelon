"""Tests for Cycle 037b Sprint 3 — Route / Certificate Integration + Regression.

Validates:
- Full orchestration pipeline (filter → orchestrate → converge → outcome)
- Certificate JSON enrichment with evaluator provenance
- Final issuance status logic (DEFERRED preserved, BLOCKED for divergent)
- Regression: existing construct path without orchestration
"""

import pytest

from backend.schemas.evaluator_orchestration import (
    EvaluatorOutcome,
    EvaluatorScoreRecord,
    RunConvergenceSummary,
)
from backend.services.construct_certificate_builder import (
    ConstructCertificateBuilder,
    ScorerOutput,
)
from backend.services.convergence_policy import (
    build_orchestration_persistence,
    compute_dimension_convergence,
    compute_run_convergence,
)
from backend.services.evaluator_integration import (
    compute_final_issuance_status,
    enrich_certificate_json,
    run_evaluator_orchestration,
)
from backend.services.residual_dimension_filter import ResidualDimension


# ═══════════════════════════════════════════════════════════
# Mock Scorers for Integration Tests
# ═══════════════════════════════════════════════════════════


class PassScorer:
    def __init__(self, evaluator_id: str, score: float = 0.85):
        self._evaluator_id = evaluator_id
        self._score = score

    @property
    def evaluator_id(self) -> str:
        return self._evaluator_id

    async def score_dimensions(self, *, dimensions, episode_payload):
        return [
            EvaluatorScoreRecord(
                evaluator_id=self._evaluator_id,
                dimension=d.dimension,
                verdict="PASS",
                score=self._score,
                rationale=f"{self._evaluator_id}: pass",
            )
            for d in dimensions
        ]


class SplitScorer:
    """Returns FAIL for all dimensions — used to create divergence."""
    def __init__(self, evaluator_id: str):
        self._evaluator_id = evaluator_id

    @property
    def evaluator_id(self) -> str:
        return self._evaluator_id

    async def score_dimensions(self, *, dimensions, episode_payload):
        return [
            EvaluatorScoreRecord(
                evaluator_id=self._evaluator_id,
                dimension=d.dimension,
                verdict="FAIL",
                score=0.20,
                rationale=f"{self._evaluator_id}: fail",
            )
            for d in dimensions
        ]


class PartialScorer:
    """Scores only dimensions matching a whitelist — omits the rest."""
    def __init__(self, evaluator_id: str, only_dimensions: set[str]):
        self._evaluator_id = evaluator_id
        self._only = only_dimensions

    @property
    def evaluator_id(self) -> str:
        return self._evaluator_id

    async def score_dimensions(self, *, dimensions, episode_payload):
        return [
            EvaluatorScoreRecord(
                evaluator_id=self._evaluator_id,
                dimension=d.dimension,
                verdict="PASS",
                score=0.85,
                rationale=f"{self._evaluator_id}: pass",
            )
            for d in dimensions
            if d.dimension in self._only
        ]


# ═══════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════


def _check(check_id, check_type, domain, critical=False, **kwargs):
    return {
        "check_id": check_id,
        "check_type": check_type,
        "domain": domain,
        "source": f"test:{check_id}",
        "critical": critical,
        **kwargs,
    }


TYPICAL_PLAN = [
    _check("anchor:public_standard", "ANCHOR", "*", critical=True),
    _check("anchor:deterministic_check", "ANCHOR", "*"),
    _check("rubric:artisan:design_systems", "RUBRIC", "design_systems", critical=True),
    _check("rubric:artisan:code_generation", "RUBRIC", "code_generation", critical=True),
]

EPISODE = {"construct_slug": "test-construct", "version": "1.0.0"}


# ═══════════════════════════════════════════════════════════
# Full Pipeline Integration Tests
# ═══════════════════════════════════════════════════════════


class TestFullPipeline:
    @pytest.mark.asyncio
    async def test_convergent_pipeline(self):
        """3 scorers all PASS → eligible, no escalation."""
        outcome = await run_evaluator_orchestration(
            planned_checks=TYPICAL_PLAN,
            executed_results={},
            scorers=[PassScorer("a"), PassScorer("b"), PassScorer("c")],
            episode_payload=EPISODE,
            rubric_version="v1.0.0",
        )
        assert outcome is not None
        assert outcome.issuance_eligible is True
        assert outcome.block_reason is None
        assert outcome.convergence_summary.converged_pass == 2
        assert outcome.convergence_summary.divergent == 0
        assert outcome.convergence_summary.escalation_required is False

    @pytest.mark.asyncio
    async def test_divergent_pipeline(self):
        """2 PASS + 1 FAIL per dimension → still converged (2/3), but with LOWER."""
        outcome = await run_evaluator_orchestration(
            planned_checks=TYPICAL_PLAN,
            executed_results={},
            scorers=[PassScorer("a"), PassScorer("b"), SplitScorer("c")],
            episode_payload=EPISODE,
        )
        assert outcome is not None
        assert outcome.issuance_eligible is True
        # 2/3 PASS → CONVERGED_PASS with LOWER confidence
        assert outcome.convergence_summary.converged_pass == 2

    @pytest.mark.asyncio
    async def test_converged_fail_blocks_issuance(self):
        """1 PASS + 2 FAIL → CONVERGED_FAIL (2/3 supermajority) → issuance blocked."""
        outcome = await run_evaluator_orchestration(
            planned_checks=TYPICAL_PLAN,
            executed_results={},
            scorers=[PassScorer("a"), SplitScorer("b"), SplitScorer("c")],
            episode_payload=EPISODE,
        )
        assert outcome is not None
        assert outcome.issuance_eligible is False
        assert outcome.block_reason is not None
        assert "blocked" in outcome.block_reason.lower()
        # 2/3 FAIL → CONVERGED_FAIL, not DIVERGENT
        assert outcome.convergence_summary.converged_fail == 2

    @pytest.mark.asyncio
    async def test_all_deterministic_returns_none(self):
        """All checks are ANCHOR/BENCHMARK → no residuals → None outcome."""
        all_deterministic = [
            _check("anchor:public_standard", "ANCHOR", "*", critical=True),
            _check("benchmark:humaneval", "BENCHMARK", "code_generation"),
        ]
        outcome = await run_evaluator_orchestration(
            planned_checks=all_deterministic,
            executed_results={"code_generation": 0.92},
            scorers=[PassScorer("a")],
            episode_payload=EPISODE,
        )
        assert outcome is None


# ═══════════════════════════════════════════════════════════
# Certificate Enrichment Tests
# ═══════════════════════════════════════════════════════════


class TestCertificateEnrichment:
    def test_enriches_cert_json(self):
        """Certificate JSON should include evaluator_orchestration block."""
        records = [
            EvaluatorScoreRecord(evaluator_id="a", dimension="design", verdict="PASS", score=0.85),
            EvaluatorScoreRecord(evaluator_id="b", dimension="design", verdict="PASS", score=0.82),
        ]
        dim = compute_dimension_convergence("design", records)
        summary = compute_run_convergence([dim], ["a", "b"], rubric_version="v1.0.0")
        outcome = EvaluatorOutcome(
            convergence_summary=summary,
            evaluator_scores=records,
            issuance_eligible=True,
        )

        cert_json = {"certificate_id": "CERT-C1234", "verdict": "PASS"}
        enriched = enrich_certificate_json(cert_json, outcome, records, summary)

        assert "evaluator_orchestration" in enriched
        assert enriched["evaluator_issuance_eligible"] is True
        assert "evaluator_block_reason" not in enriched
        assert enriched["evaluator_orchestration"]["rubric_version"] == "v1.0.0"

    def test_enrichment_includes_block_reason(self):
        """Blocked outcome should include block_reason in enriched cert."""
        records = [
            EvaluatorScoreRecord(evaluator_id="a", dimension="design", verdict="PASS", score=0.85),
            EvaluatorScoreRecord(evaluator_id="b", dimension="design", verdict="FAIL", score=0.30),
        ]
        dim = compute_dimension_convergence("design", records)
        summary = compute_run_convergence([dim], ["a", "b"])
        outcome = EvaluatorOutcome(
            convergence_summary=summary,
            evaluator_scores=records,
            issuance_eligible=False,
            block_reason="Critical dimensions divergent: design",
        )

        cert_json = {"certificate_id": "CERT-C5678"}
        enriched = enrich_certificate_json(cert_json, outcome, records, summary)

        assert enriched["evaluator_issuance_eligible"] is False
        assert enriched["evaluator_block_reason"] == "Critical dimensions divergent: design"

    def test_persisted_cert_json_reflects_final_issuance(self):
        """P1: cert_json.issuance_status must match final_issuance, not base status.

        Reproduces the trust-surface mismatch where base READY gets overridden
        to BLOCKED by evaluator orchestration but the persisted cert_json still
        says READY.
        """
        # Simulate the route's cert_json with base issuance_status = READY
        cert_json = {
            "certificate_id": "CERT-C9999",
            "verdict": "PASS",
            "issuance_status": "READY",
        }

        # Evaluator outcome says ineligible → final_issuance = BLOCKED
        records = [
            EvaluatorScoreRecord(evaluator_id="a", dimension="design", verdict="PASS", score=0.85),
            EvaluatorScoreRecord(evaluator_id="b", dimension="design", verdict="FAIL", score=0.30),
        ]
        dim = compute_dimension_convergence("design", records)
        summary = compute_run_convergence([dim], ["a", "b"])
        outcome = EvaluatorOutcome(
            convergence_summary=summary,
            evaluator_scores=records,
            issuance_eligible=False,
            block_reason="Critical dimensions blocked: design",
        )

        # Step 1: enrich (as the route does)
        enriched = enrich_certificate_json(cert_json, outcome, records, summary)

        # Step 2: compute final issuance (as the route does)
        base_status = "READY"
        final_issuance = compute_final_issuance_status(base_status, outcome)
        assert final_issuance == "BLOCKED"

        # Step 3: write-back (the fix — mirrors the route's new line)
        if final_issuance != base_status:
            enriched["issuance_status"] = final_issuance

        # Verify: persisted cert_json now says BLOCKED, not READY
        assert enriched["issuance_status"] == "BLOCKED"
        assert enriched["evaluator_issuance_eligible"] is False
        assert enriched["evaluator_block_reason"] == "Critical dimensions blocked: design"

    def test_persisted_cert_json_unchanged_when_status_matches(self):
        """When final_issuance == base status, cert_json.issuance_status is untouched."""
        cert_json = {
            "certificate_id": "CERT-C8888",
            "issuance_status": "READY",
        }

        outcome = EvaluatorOutcome(
            convergence_summary=RunConvergenceSummary(evaluator_ids=["a"], total_dimensions=1),
            issuance_eligible=True,
        )

        final_issuance = compute_final_issuance_status("READY", outcome)
        assert final_issuance == "READY"

        # No write-back needed
        if final_issuance != "READY":
            cert_json["issuance_status"] = final_issuance

        assert cert_json["issuance_status"] == "READY"


# ═══════════════════════════════════════════════════════════
# Final Issuance Status Tests
# ═══════════════════════════════════════════════════════════


class TestFinalIssuanceStatus:
    def test_rejected_stays_rejected(self):
        """REJECTED base status is never overridden by evaluator outcome."""
        outcome = EvaluatorOutcome(
            convergence_summary=RunConvergenceSummary(evaluator_ids=[], total_dimensions=0),
            issuance_eligible=True,
        )
        assert compute_final_issuance_status("REJECTED", outcome) == "REJECTED"

    def test_deferred_stays_deferred(self):
        """DEFERRED base status (missing coverage) is never overridden."""
        outcome = EvaluatorOutcome(
            convergence_summary=RunConvergenceSummary(evaluator_ids=[], total_dimensions=0),
            issuance_eligible=True,
        )
        assert compute_final_issuance_status("DEFERRED", outcome) == "DEFERRED"

    def test_ready_plus_eligible_stays_ready(self):
        """READY + evaluator eligible → READY."""
        outcome = EvaluatorOutcome(
            convergence_summary=RunConvergenceSummary(evaluator_ids=["a", "b"], total_dimensions=2),
            issuance_eligible=True,
        )
        assert compute_final_issuance_status("READY", outcome) == "READY"

    def test_ready_plus_ineligible_becomes_blocked(self):
        """READY + evaluator ineligible (divergent) → BLOCKED."""
        outcome = EvaluatorOutcome(
            convergence_summary=RunConvergenceSummary(evaluator_ids=["a", "b"], total_dimensions=2, divergent=2),
            issuance_eligible=False,
            block_reason="Critical dimensions divergent",
        )
        assert compute_final_issuance_status("READY", outcome) == "BLOCKED"

    def test_ready_plus_no_outcome_stays_ready(self):
        """READY + no evaluator outcome (all deterministic) → READY."""
        assert compute_final_issuance_status("READY", None) == "READY"


# ═══════════════════════════════════════════════════════════
# Regression Tests — Old Construct Path
# ═══════════════════════════════════════════════════════════


class TestRegressionOldPath:
    def test_certificate_builder_without_contract(self):
        """Pre-037 path: certificate builder works without contract."""
        builder = ConstructCertificateBuilder()
        scorer_output = ScorerOutput(
            composite_score=0.82,
            domain_scores={"design_systems": 0.85, "code_generation": 0.80},
            skill_coverage=1.0,
            verdict="PASS",
            tier="BACKTESTED",
            routing_hint="ALLOWED",
            episode_count=10,
        )

        # Mock registration and investigation
        class MockReg:
            slug = "test"
            version = "1.0.0"
            content_hash = "sha256:abc"
            commitment_hash = "sha256:def"
            test_prompts_hash = "sha256:ghi"
            rubric_hash = "sha256:jkl"

        class MockInv:
            stop_config_json = {"run_number": 1}

        cert = builder.build(MockReg(), MockInv(), scorer_output, "sha256:bundle")
        assert cert.issuance_status == "READY"
        assert cert.contract_hash is None
        assert cert.check_plan is None

    def test_issuance_status_pass_no_contract(self):
        """Pre-037 path: PASS verdict with no contract → READY."""
        status = ConstructCertificateBuilder.compute_issuance_status("PASS", None, None)
        assert status == "READY"

    def test_issuance_status_fail_is_rejected(self):
        """Both old and new: FAIL verdict → REJECTED."""
        status = ConstructCertificateBuilder.compute_issuance_status("FAIL", None, None)
        assert status == "REJECTED"

    def test_issuance_status_deferred_for_missing_checks(self):
        """037 path: PASS but incomplete checks → DEFERRED."""
        check_plan = {"total_planned": 5, "total_executed": 3, "checks": []}
        status = ConstructCertificateBuilder.compute_issuance_status("PASS", check_plan, None)
        assert status == "DEFERRED"

    def test_issuance_status_deferred_for_tier_cap(self):
        """037 path: PASS with tier_cap → DEFERRED."""
        status = ConstructCertificateBuilder.compute_issuance_status("PASS", None, "BACKTESTED")
        assert status == "DEFERRED"

    def test_final_status_without_orchestration(self):
        """037b: No evaluator outcome → base status unchanged."""
        assert compute_final_issuance_status("READY", None) == "READY"
        assert compute_final_issuance_status("DEFERRED", None) == "DEFERRED"
        assert compute_final_issuance_status("REJECTED", None) == "REJECTED"


# ═══════════════════════════════════════════════════════════
# P1 Fix: Missing Dimension → SKIPPED Coverage
# ═══════════════════════════════════════════════════════════


class TestMissingDimensionSkipped:
    """P1: Scorers that omit critical dimensions must trigger SKIPPED → blocked."""

    @pytest.mark.asyncio
    async def test_omitted_critical_dimension_blocks_issuance(self):
        """All scorers omit a critical dimension → SKIPPED → issuance blocked."""
        # All 3 scorers only score design_systems, omitting code_generation
        scorers = [
            PartialScorer("a", {"design_systems"}),
            PartialScorer("b", {"design_systems"}),
            PartialScorer("c", {"design_systems"}),
        ]
        outcome = await run_evaluator_orchestration(
            planned_checks=TYPICAL_PLAN,
            executed_results={},
            scorers=scorers,
            episode_payload=EPISODE,
        )
        assert outcome is not None
        assert outcome.issuance_eligible is False
        assert outcome.block_reason is not None
        assert "code_generation" in outcome.block_reason
        # Both dimensions should be in the summary
        assert outcome.convergence_summary.total_dimensions == 2

    @pytest.mark.asyncio
    async def test_omitted_noncritical_dimension_stays_eligible(self):
        """Omitted non-critical dimension → SKIPPED but doesn't block."""
        # Plan with one critical rubric + one non-critical rubric
        plan = [
            _check("anchor:public_standard", "ANCHOR", "*", critical=True),
            _check("rubric:design", "RUBRIC", "design_systems", critical=True),
            _check("rubric:docs", "RUBRIC", "documentation", critical=False),
        ]
        # Scorers only score design_systems, omit documentation
        scorers = [
            PartialScorer("a", {"design_systems"}),
            PartialScorer("b", {"design_systems"}),
            PartialScorer("c", {"design_systems"}),
        ]
        outcome = await run_evaluator_orchestration(
            planned_checks=plan,
            executed_results={},
            scorers=scorers,
            episode_payload=EPISODE,
        )
        assert outcome is not None
        # Non-critical SKIPPED doesn't block
        assert outcome.issuance_eligible is True
        assert outcome.block_reason is None
        # Both dimensions are tracked
        assert outcome.convergence_summary.total_dimensions == 2

    @pytest.mark.asyncio
    async def test_all_dimensions_covered_no_skipped(self):
        """When all scorers cover all dimensions, no SKIPPED entries appear."""
        scorers = [PassScorer("a"), PassScorer("b"), PassScorer("c")]
        outcome = await run_evaluator_orchestration(
            planned_checks=TYPICAL_PLAN,
            executed_results={},
            scorers=scorers,
            episode_payload=EPISODE,
        )
        assert outcome is not None
        assert outcome.issuance_eligible is True
        # No SKIPPED in the summary
        assert outcome.convergence_summary.skipped == 0
        assert outcome.convergence_summary.total_dimensions == 2


