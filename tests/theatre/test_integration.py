"""End-to-end integration tests for Theatre Template Engine.

Tests the full lifecycle: create → commit → run → verify certificate.
Uses MockOracleAdapter with is_certificate_run=False.
"""

import hashlib
from pathlib import Path

import pytest

from theatre.engine.canonical_json import canonical_json
from theatre.engine.commitment import CommitmentProtocol, CommitmentReceipt
from theatre.engine.models import GroundTruthEpisode, TheatreCriteria
from theatre.engine.oracle_contract import MockOracleAdapter
from theatre.engine.replay import ReplayEngine, ReplayResult
from theatre.engine.resolution import (
    ResolutionContext,
    ResolutionStateMachine,
    ResolutionStep,
)
from theatre.engine.scoring import SimpleScoringFunction, TheatreScoringProvider
from theatre.engine.state_machine import (
    InvalidTransitionError,
    TheatreState,
    TheatreStateMachine,
)
from theatre.engine.template_validator import TemplateValidator
from theatre.engine.tier_assigner import TierAssigner
from theatre.engine.evidence_bundle import EvidenceBundleBuilder
from theatre.fixtures import (
    CARTOGRAPH_GROUND_TRUTH,
    CARTOGRAPH_TEMPLATE,
    EASEL_GROUND_TRUTH,
    EASEL_TEMPLATE,
    OBSERVER_GROUND_TRUTH,
    OBSERVER_TEMPLATE,
    load_ground_truth,
    load_template,
)

SCHEMA_PATH = Path(__file__).parent.parent.parent / "docs" / "schemas" / "echelon_theatre_schema_v2.json"


@pytest.fixture
def validator() -> TemplateValidator:
    return TemplateValidator(schema_path=SCHEMA_PATH)


def _compute_dataset_hash(episodes: list[GroundTruthEpisode]) -> str:
    """Compute dataset hash matching ReplayEngine's internal method."""
    serialised = canonical_json([ep.model_dump() for ep in episodes])
    return hashlib.sha256(serialised.encode("utf-8")).hexdigest()


async def _run_full_lifecycle(
    template_name: str,
    ground_truth_name: str,
    validator: TemplateValidator,
) -> tuple[ReplayResult, CommitmentReceipt, TheatreStateMachine]:
    """Execute the full Theatre lifecycle for a given fixture.

    Returns (replay_result, commitment_receipt, state_machine).
    """
    # 1. Load template and validate
    template = load_template(template_name)
    errors = validator.validate(template, is_certificate_run=False)
    assert errors == [], f"Template validation failed: {errors}"

    # 2. Load ground truth
    ground_truth = load_ground_truth(ground_truth_name)
    assert len(ground_truth) >= 5

    # 3. Extract configuration from template
    criteria = TheatreCriteria(**template["criteria"])
    version_pins = template.get("version_pins", {})
    dataset_hashes = template.get("dataset_hashes", {})
    ptc = template.get("product_theatre_config", {})
    construct_under_test = ptc.get("construct_under_test", "")
    constructs_pins = version_pins.get("constructs", {})
    construct_version = constructs_pins.get(construct_under_test, "test-v1")

    # 4. Create state machine (DRAFT)
    theatre_id = f"test-{template_name}"
    sm = TheatreStateMachine(theatre_id)
    assert sm.state == TheatreState.DRAFT

    # 5. Compute commitment hash and transition to COMMITTED
    # Use actual dataset hash (not the placeholder in the fixture)
    actual_dataset_hash = _compute_dataset_hash(ground_truth)
    # Update dataset_hashes with real value for commitment
    replay_dataset_id = ptc.get("replay_dataset_id", "")
    dataset_hashes_real = {replay_dataset_id: actual_dataset_hash}

    receipt = CommitmentProtocol.create_receipt(
        theatre_id=theatre_id,
        template=template,
        version_pins=version_pins,
        dataset_hashes=dataset_hashes_real,
    )
    assert len(receipt.commitment_hash) == 64
    sm.transition(TheatreState.COMMITTED)
    assert sm.state == TheatreState.COMMITTED

    # 6. Verify commitment hash is reproducible
    hash_again = CommitmentProtocol.compute_hash(
        template=template,
        version_pins=version_pins,
        dataset_hashes=dataset_hashes_real,
    )
    assert hash_again == receipt.commitment_hash

    # 7. Transition to ACTIVE and run replay
    sm.transition(TheatreState.ACTIVE)
    assert sm.state == TheatreState.ACTIVE

    adapter = MockOracleAdapter()
    scoring_fn = SimpleScoringFunction()
    scoring_provider = TheatreScoringProvider(
        criteria=criteria,
        scorer=scoring_fn,
    )

    engine = ReplayEngine(
        theatre_id=theatre_id,
        construct_id=construct_under_test,
        construct_version=construct_version,
        criteria=criteria,
        oracle_adapter=adapter,
        scoring_provider=scoring_provider,
        committed_dataset_hash=actual_dataset_hash,
    )

    progress_log: list[tuple[int, int]] = []

    def progress_cb(completed: int, total: int) -> None:
        progress_log.append((completed, total))

    result = await engine.run(ground_truth=ground_truth, progress_callback=progress_cb)

    # 8. Transition to SETTLING → RESOLVED
    sm.transition(TheatreState.SETTLING)
    sm.transition(TheatreState.RESOLVED)
    assert sm.state == TheatreState.RESOLVED

    # Verify progress callback was invoked
    assert len(progress_log) == len(ground_truth)

    return result, receipt, sm


# ============================================
# FULL LIFECYCLE TESTS
# ============================================


class TestObserverLifecycle:
    """End-to-end lifecycle test for Observer fixture."""

    @pytest.mark.asyncio
    async def test_full_lifecycle(self, validator: TemplateValidator):
        result, receipt, sm = await _run_full_lifecycle(
            OBSERVER_TEMPLATE, OBSERVER_GROUND_TRUTH, validator
        )

        assert result.replay_count == 5
        assert result.scored_count == 5
        assert result.failure_count == 0
        assert result.failure_rate == 0.0
        assert sm.state == TheatreState.RESOLVED

    @pytest.mark.asyncio
    async def test_certificate_fields(self, validator: TemplateValidator):
        result, receipt, _ = await _run_full_lifecycle(
            OBSERVER_TEMPLATE, OBSERVER_GROUND_TRUTH, validator
        )

        # Verify aggregate scores contain all criteria
        template = load_template(OBSERVER_TEMPLATE)
        criteria_ids = template["criteria"]["criteria_ids"]
        for cid in criteria_ids:
            assert cid in result.aggregate_scores

        # Verify composite score in [0, 1]
        assert 0.0 <= result.composite_score <= 1.0


class TestEaselLifecycle:
    """End-to-end lifecycle test for Easel fixture (compositional chain)."""

    @pytest.mark.asyncio
    async def test_full_lifecycle(self, validator: TemplateValidator):
        result, receipt, sm = await _run_full_lifecycle(
            EASEL_TEMPLATE, EASEL_GROUND_TRUTH, validator
        )

        assert result.replay_count == 5
        assert sm.state == TheatreState.RESOLVED

    @pytest.mark.asyncio
    async def test_three_version_pins_in_commitment(self, validator: TemplateValidator):
        """Easel has 3 constructs in chain — all must be pinned."""
        template = load_template(EASEL_TEMPLATE)
        constructs_pins = template["version_pins"]["constructs"]
        chain = template["product_theatre_config"]["construct_chain"]

        assert len(chain) == 3
        for construct_id in chain:
            assert construct_id in constructs_pins


class TestCartographLifecycle:
    """End-to-end lifecycle test for Cartograph fixture."""

    @pytest.mark.asyncio
    async def test_full_lifecycle(self, validator: TemplateValidator):
        result, receipt, sm = await _run_full_lifecycle(
            CARTOGRAPH_TEMPLATE, CARTOGRAPH_GROUND_TRUTH, validator
        )

        assert result.replay_count == 5
        assert sm.state == TheatreState.RESOLVED

    @pytest.mark.asyncio
    async def test_low_scores_for_stub(self, validator: TemplateValidator):
        """MockOracleAdapter returns stub data — scores should be present but not perfect."""
        result, _, _ = await _run_full_lifecycle(
            CARTOGRAPH_TEMPLATE, CARTOGRAPH_GROUND_TRUTH, validator
        )

        # Scores should exist for all episodes
        for ep in result.episode_results:
            assert ep.scores is not None
            assert ep.composite_score is not None


# ============================================
# COMMITMENT HASH REPRODUCIBILITY
# ============================================


class TestCommitmentReproducibility:
    """Verify commitment hashes are identical across independent runs."""

    def test_same_inputs_same_hash(self):
        template = load_template(OBSERVER_TEMPLATE)
        version_pins = template.get("version_pins", {})
        dataset_hashes = template.get("dataset_hashes", {})

        h1 = CommitmentProtocol.compute_hash(template, version_pins, dataset_hashes)
        h2 = CommitmentProtocol.compute_hash(template, version_pins, dataset_hashes)
        assert h1 == h2

    def test_hash_changes_with_different_version_pins(self):
        template = load_template(OBSERVER_TEMPLATE)
        version_pins_a = template.get("version_pins", {})
        version_pins_b = {**version_pins_a, "constructs": {"observer": "fffffff"}}
        dataset_hashes = template.get("dataset_hashes", {})

        h1 = CommitmentProtocol.compute_hash(template, version_pins_a, dataset_hashes)
        h2 = CommitmentProtocol.compute_hash(template, version_pins_b, dataset_hashes)
        assert h1 != h2


# ============================================
# EVIDENCE BUNDLE
# ============================================


class TestEvidenceBundle:
    """Verify evidence bundle creation after lifecycle completion."""

    @pytest.mark.asyncio
    async def test_evidence_bundle_after_lifecycle(
        self, validator: TemplateValidator, tmp_path
    ):
        result, receipt, _ = await _run_full_lifecycle(
            OBSERVER_TEMPLATE, OBSERVER_GROUND_TRUTH, validator
        )

        template = load_template(OBSERVER_TEMPLATE)
        from theatre.engine.models import BundleManifest

        # Build evidence bundle
        builder = EvidenceBundleBuilder(
            theatre_id=receipt.theatre_id,
            output_dir=tmp_path,
        )

        manifest = BundleManifest(
            theatre_id=receipt.theatre_id,
            template_id=template["theatre_id"],
            construct_id=template["product_theatre_config"]["construct_under_test"],
            execution_path="replay",
            commitment_hash=receipt.commitment_hash,
        )
        builder.write_manifest(manifest)
        builder.write_template(template)
        builder.write_commitment_receipt(receipt)
        builder.write_aggregate_scores(result.aggregate_scores)

        ground_truth = load_ground_truth(OBSERVER_GROUND_TRUTH)
        builder.write_ground_truth(
            [ep.model_dump() for ep in ground_truth], "observer_provenance.jsonl"
        )

        for ep in result.episode_results:
            builder.write_invocation(
                ep.episode_id,
                request={"episode_id": ep.episode_id},
                response=ep.model_dump(),
            )
            builder.write_episode_score({
                "episode_id": ep.episode_id,
                "scores": ep.scores or {},
                "composite_score": ep.composite_score or 0.0,
            })

        # Write certificate (needed for minimum files)
        builder.write_certificate({
            "theatre_id": receipt.theatre_id,
            "composite_score": result.composite_score,
            "verification_tier": "UNVERIFIED",
        })

        # Validate minimum files
        missing = builder.validate_minimum_files()
        assert missing == [], f"Missing evidence files: {missing}"


# ============================================
# STATE TRANSITION ENFORCEMENT
# ============================================


class TestStateTransitionEnforcement:
    """Verify invalid state transitions are rejected."""

    def test_cannot_run_before_commit(self):
        sm = TheatreStateMachine("test-theatre")
        assert sm.state == TheatreState.DRAFT
        with pytest.raises(InvalidTransitionError):
            sm.transition(TheatreState.ACTIVE)

    def test_cannot_commit_twice(self):
        sm = TheatreStateMachine("test-theatre")
        sm.transition(TheatreState.COMMITTED)
        with pytest.raises(InvalidTransitionError):
            sm.transition(TheatreState.COMMITTED)

    def test_cannot_skip_settling(self):
        sm = TheatreStateMachine("test-theatre")
        sm.transition(TheatreState.COMMITTED)
        sm.transition(TheatreState.ACTIVE)
        with pytest.raises(InvalidTransitionError):
            sm.transition(TheatreState.RESOLVED)

    def test_cannot_reverse(self):
        sm = TheatreStateMachine("test-theatre")
        sm.transition(TheatreState.COMMITTED)
        with pytest.raises(InvalidTransitionError):
            sm.transition(TheatreState.DRAFT)


# ============================================
# TIER ASSIGNMENT
# ============================================


class TestTierAssignmentIntegration:
    """Verify tier assignment integrates with replay results."""

    @pytest.mark.asyncio
    async def test_mock_run_produces_tier(self, validator: TemplateValidator):
        result, _, _ = await _run_full_lifecycle(
            OBSERVER_TEMPLATE, OBSERVER_GROUND_TRUTH, validator
        )

        tier = TierAssigner.assign(
            replay_count=result.replay_count,
            has_full_pins=True,
            has_published_scores=True,
            has_verifiable_hash=True,
            has_disputes=False,
            failure_rate=result.failure_rate,
        )
        # 5 replays < 50 minimum → UNVERIFIED
        assert tier == "UNVERIFIED"

    @pytest.mark.asyncio
    async def test_high_failure_rate_produces_unverified(self, validator: TemplateValidator):
        """Even with enough replays, >20% failure → UNVERIFIED."""
        tier = TierAssigner.assign(
            replay_count=100,
            has_full_pins=True,
            has_published_scores=True,
            has_verifiable_hash=True,
            has_disputes=False,
            failure_rate=0.25,
        )
        assert tier == "UNVERIFIED"


# ============================================
# RESOLUTION PROGRAMME
# ============================================


class TestResolutionProgrammeIntegration:
    """Verify resolution programme execution from fixture templates."""

    @pytest.mark.asyncio
    async def test_observer_resolution(self):
        """Observer has 2 steps: construct_invocation + aggregation."""
        template = load_template(OBSERVER_TEMPLATE)
        programme = template["resolution_programme"]
        version_pins = template["version_pins"]

        steps = [ResolutionStep(**s) for s in programme]
        adapter = MockOracleAdapter()
        rsm = ResolutionStateMachine(
            steps=steps,
            version_pins=version_pins,
            oracle_adapter=adapter,
        )

        context = ResolutionContext(
            theatre_id="test-observer",
            version_pins=version_pins,
        )

        result = await rsm.execute(context)
        assert result.final_status == "COMPLETED"
        assert len(result.outcomes) == 2

    @pytest.mark.asyncio
    async def test_easel_resolution_with_hitl(self):
        """Easel has 5 steps including hitl_rubric → produces PENDING_HITL."""
        template = load_template(EASEL_TEMPLATE)
        programme = template["resolution_programme"]
        version_pins = template["version_pins"]

        steps = [ResolutionStep(**s) for s in programme]
        adapter = MockOracleAdapter()
        rsm = ResolutionStateMachine(
            steps=steps,
            version_pins=version_pins,
            oracle_adapter=adapter,
        )

        context = ResolutionContext(
            theatre_id="test-easel",
            version_pins=version_pins,
        )

        result = await rsm.execute(context)
        # Has HITL step → PENDING_HITL
        assert result.final_status == "PENDING_HITL"
        hitl_outcomes = [o for o in result.outcomes if o.status == "PENDING_HITL"]
        assert len(hitl_outcomes) == 1

    @pytest.mark.asyncio
    async def test_cartograph_resolution(self):
        """Cartograph has 3 steps: construct + deterministic + aggregation."""
        template = load_template(CARTOGRAPH_TEMPLATE)
        programme = template["resolution_programme"]
        version_pins = template["version_pins"]

        steps = [ResolutionStep(**s) for s in programme]
        adapter = MockOracleAdapter()
        rsm = ResolutionStateMachine(
            steps=steps,
            version_pins=version_pins,
            oracle_adapter=adapter,
        )

        context = ResolutionContext(
            theatre_id="test-cartograph",
            version_pins=version_pins,
        )

        result = await rsm.execute(context)
        assert result.final_status == "COMPLETED"
        assert len(result.outcomes) == 3
