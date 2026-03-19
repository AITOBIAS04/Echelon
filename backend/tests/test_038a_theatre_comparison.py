"""Tests for cycle-038a: Theatre Execution Fixtures For Cross-Theatre Paradox.

Sprint 0: Schema validation + provenance preservation (7 tests).
Sprint 1: Bundle builder (8 tests).
Sprint 2: Candidate sets (8 tests).
Sprint 3: 038 compatibility + e2e regression (7 tests).
"""

import pytest

from backend.schemas.theatre_comparison_bundle import (
    ComparisonCandidateSet,
    ExecutedTheatreComparisonBundle,
    TheatreCheckSummary,
    TheatreExecutionSummary,
    TheatreScopeKey,
)
from backend.tests.fixtures.theatre_comparison_fixtures import (
    SHARED_EVENT_KEY,
    SHARED_SCOPE_KEY,
    make_corona_bundle,
    make_corona_execution_result,
    make_corona_fixture_input,
    make_tremor_bundle,
    make_tremor_execution_result,
    make_tremor_fixture_input,
)


# ═══════════════════════════════════════════════════════════════════
# Sprint 0 — Schema Validation (4 tests)
# ═══════════════════════════════════════════════════════════════════

class TestSchemaValidation:
    """Verify all models construct and serialize correctly."""

    def test_bundle_constructs_with_minimal_fields(self):
        """ExecutedTheatreComparisonBundle accepts minimal required fields."""
        bundle = ExecutedTheatreComparisonBundle(
            construct_slug="test",
            construct_version="1.0.0",
        )
        assert bundle.construct_slug == "test"
        assert bundle.template_ids == []
        assert bundle.event_keys == []
        assert bundle.scope_keys == []
        assert bundle.settlement_state is None
        assert bundle.execution_summary.executed_count == 0

    def test_bundle_serializes_to_dict(self):
        """Bundle round-trips through model_dump."""
        bundle = make_tremor_bundle()
        d = bundle.model_dump()
        assert d["construct_slug"] == "tremor"
        assert len(d["template_ids"]) == 2
        assert len(d["execution_summary"]["checks"]) == 3
        # Round-trip
        restored = ExecutedTheatreComparisonBundle.model_validate(d)
        assert restored.construct_slug == bundle.construct_slug
        assert len(restored.execution_summary.checks) == 3

    def test_execution_summary_defaults(self):
        """TheatreExecutionSummary defaults to zero counts."""
        summary = TheatreExecutionSummary()
        assert summary.executed_count == 0
        assert summary.passed_count == 0
        assert summary.failed_count == 0
        assert summary.skipped_count == 0
        assert summary.has_critical_failures is False
        assert summary.checks == []

    def test_scope_key_normalization(self):
        """TheatreScopeKey normalizes to lowercase-hyphenated."""
        sk = TheatreScopeKey(scope_type="Region", scope_value="US_Equities")
        normalized = sk.normalized()
        assert normalized.scope_type == "region"
        assert normalized.scope_value == "us-equities"
        assert normalized.key() == "region:us-equities"

        # Already normalized stays the same
        sk2 = TheatreScopeKey(scope_type="entity", scope_value="btc-usd")
        assert sk2.key() == "entity:btc-usd"


# ═══════════════════════════════════════════════════════════════════
# Sprint 0 — Provenance Preservation (3 tests)
# ═══════════════════════════════════════════════════════════════════

class TestProvenancePreservation:
    """Verify execution provenance survives bundle projection."""

    def test_execution_summary_counts_correct(self):
        """TREMOR bundle has correct execution counts (2 passed, 1 failed)."""
        bundle = make_tremor_bundle()
        summary = bundle.execution_summary
        assert summary.executed_count == 3
        assert summary.passed_count == 2
        assert summary.failed_count == 1
        assert summary.skipped_count == 0
        assert summary.has_critical_failures is True

    def test_check_evidence_preserved_in_summary(self):
        """Individual check evidence dicts survive in TheatreCheckSummary."""
        bundle = make_corona_bundle()
        checks = bundle.execution_summary.checks
        assert len(checks) == 3

        cal_check = next(c for c in checks if c.check_type == "CALIBRATION_VALIDITY")
        assert cal_check.evidence["computed_brier"] == 0.18
        assert cal_check.is_critical is False

        settlement_check = next(
            c for c in checks if c.check_type == "SETTLEMENT_ACCURACY"
        )
        assert settlement_check.evidence["resolution"] == "CORRECT"
        assert settlement_check.is_critical is True

    def test_provenance_refs_populated(self):
        """provenance_refs captures all executed check_ids."""
        tremor = make_tremor_bundle()
        assert len(tremor.provenance_refs) == 3
        assert "theatre:SETTLEMENT_ACCURACY:tmpl-eq-001" in tremor.provenance_refs
        assert "theatre:ORACLE_CONSISTENCY:src-chainlink" in tremor.provenance_refs

        corona = make_corona_bundle()
        assert len(corona.provenance_refs) == 3
        assert "theatre:CALIBRATION_VALIDITY:brier" in corona.provenance_refs


# ═══════════════════════════════════════════════════════════════════
# Sprint 1 — TREMOR Bundle Builder (4 tests)
# ═══════════════════════════════════════════════════════════════════

from backend.services.theatre_comparison_bundle_builder import build_comparison_bundle


class TestTremorBundleBuilder:
    """Verify TREMOR execution → bundle mapping."""

    def test_identity_mapping(self):
        """Builder extracts slug from result, version from fixture."""
        result = make_tremor_execution_result()
        fixture = make_tremor_fixture_input()
        bundle = build_comparison_bundle(result, fixture, certificate_id="cert-t-001")

        assert bundle.construct_slug == "tremor"
        assert bundle.construct_version == "1.0.0"
        assert bundle.certificate_id == "cert-t-001"

    def test_settlement_outcomes_from_evidence(self):
        """Settlement outcomes extracted from SETTLEMENT_ACCURACY checks."""
        result = make_tremor_execution_result()
        fixture = make_tremor_fixture_input()
        bundle = build_comparison_bundle(result, fixture)

        assert len(bundle.settlement_outcomes) == 2
        assert bundle.settlement_outcomes["tmpl-eq-001"]["resolution"] == "CORRECT"
        assert bundle.settlement_outcomes["tmpl-eq-002"]["resolution"] == "INCORRECT"
        assert bundle.settlement_outcomes["tmpl-eq-002"]["predicted_outcome"] == "DOWN"
        assert bundle.settlement_outcomes["tmpl-eq-002"]["actual_outcome"] == "UP"

        # TREMOR has 1 FAILED settlement → DISPUTED
        assert bundle.settlement_state == "DISPUTED"

    def test_oracle_values_from_evidence(self):
        """Oracle values extracted from ORACLE_CONSISTENCY checks."""
        result = make_tremor_execution_result()
        fixture = make_tremor_fixture_input()
        bundle = build_comparison_bundle(result, fixture)

        assert len(bundle.oracle_values) == 1
        assert bundle.oracle_values["src-chainlink"]["value"] == 1.02
        assert bundle.oracle_values["src-chainlink"]["is_provisional"] is False
        assert bundle.oracle_source_ids == ["src-chainlink"]

    def test_execution_summary_projection(self):
        """Execution summary counts and checks projected from result."""
        result = make_tremor_execution_result()
        fixture = make_tremor_fixture_input()
        bundle = build_comparison_bundle(result, fixture)

        summary = bundle.execution_summary
        assert summary.executed_count == 3  # 2 PASSED + 1 FAILED
        assert summary.passed_count == 2    # tmpl-eq-001 + oracle
        assert summary.failed_count == 1    # tmpl-eq-002
        assert summary.has_critical_failures is True
        assert len(summary.checks) == 3
        assert len(bundle.provenance_refs) == 3


# ═══════════════════════════════════════════════════════════════════
# Sprint 1 — CORONA Bundle Builder (4 tests)
# ═══════════════════════════════════════════════════════════════════

class TestCoronaBundleBuilder:
    """Verify CORONA execution → bundle mapping."""

    def test_identity_mapping(self):
        """Builder extracts slug from result, version from fixture."""
        result = make_corona_execution_result()
        fixture = make_corona_fixture_input()
        bundle = build_comparison_bundle(result, fixture)

        assert bundle.construct_slug == "corona"
        assert bundle.construct_version == "2.1.0"
        assert bundle.certificate_id is None

    def test_settlement_outcomes_all_passed(self):
        """CORONA has 1 settlement check, all PASSED → SETTLED."""
        result = make_corona_execution_result()
        fixture = make_corona_fixture_input()
        bundle = build_comparison_bundle(result, fixture)

        assert len(bundle.settlement_outcomes) == 1
        assert bundle.settlement_outcomes["tmpl-pandemic-001"]["resolution"] == "CORRECT"
        assert bundle.settlement_state == "SETTLED"

    def test_oracle_values_corona(self):
        """CORONA oracle values extracted correctly."""
        result = make_corona_execution_result()
        fixture = make_corona_fixture_input()
        bundle = build_comparison_bundle(result, fixture)

        assert len(bundle.oracle_values) == 1
        assert bundle.oracle_values["src-who"]["value"] == 0.85
        assert bundle.oracle_source_ids == ["src-who"]

    def test_confidence_signals_from_calibration(self):
        """Confidence signals extracted from CALIBRATION_VALIDITY evidence."""
        result = make_corona_execution_result()
        fixture = make_corona_fixture_input()
        bundle = build_comparison_bundle(result, fixture)

        assert bundle.confidence_signals["brier_score"] == 0.18
        assert bundle.confidence_signals["calibration_valid"] is True

        # TREMOR has no calibration → empty signals
        tremor_result = make_tremor_execution_result()
        tremor_fixture = make_tremor_fixture_input()
        tremor_bundle = build_comparison_bundle(tremor_result, tremor_fixture)
        assert tremor_bundle.confidence_signals == {}


# ═══════════════════════════════════════════════════════════════════
# Sprint 2 — Same-Event Candidates (3 tests)
# ═══════════════════════════════════════════════════════════════════

from backend.services.theatre_comparison_candidates import generate_candidates


class TestSameEventCandidates:
    """Verify same-event candidate generation."""

    def test_shared_event_keys_produce_candidate(self):
        """TREMOR and CORONA share one event key → same_event candidate."""
        tremor = make_tremor_bundle()
        corona = make_corona_bundle()
        candidates = generate_candidates([tremor, corona])

        same_event = [c for c in candidates if c.candidate_type == "same_event"]
        assert len(same_event) == 1
        assert SHARED_EVENT_KEY in same_event[0].matching_keys
        assert same_event[0].bundle_a.construct_slug == "tremor"
        assert same_event[0].bundle_b.construct_slug == "corona"

    def test_no_shared_event_keys_no_same_event_candidate(self):
        """Bundles with disjoint event keys produce no same-event candidate."""
        bundle_a = make_tremor_bundle().model_copy(
            update={"event_keys": ["event-a-only"]},
        )
        bundle_b = make_corona_bundle().model_copy(
            update={"event_keys": ["event-b-only"]},
        )
        candidates = generate_candidates([bundle_a, bundle_b])
        same_event = [c for c in candidates if c.candidate_type == "same_event"]
        assert len(same_event) == 0

    def test_match_strength_exact_vs_partial(self):
        """EXACT when all events shared, PARTIAL when subset."""
        # PARTIAL: TREMOR has extra event key not in CORONA
        tremor = make_tremor_bundle()  # event_keys: [SHARED, "btc-futures-q1-2026"]
        corona = make_corona_bundle()  # event_keys: [SHARED]
        candidates = generate_candidates([tremor, corona])
        same_event = [c for c in candidates if c.candidate_type == "same_event"]
        assert same_event[0].match_strength == "PARTIAL"

        # EXACT: both bundles have identical event keys
        bundle_a = make_tremor_bundle().model_copy(
            update={"event_keys": [SHARED_EVENT_KEY]},
        )
        bundle_b = make_corona_bundle().model_copy(
            update={"event_keys": [SHARED_EVENT_KEY]},
        )
        candidates = generate_candidates([bundle_a, bundle_b])
        same_event = [c for c in candidates if c.candidate_type == "same_event"]
        assert same_event[0].match_strength == "EXACT"


# ═══════════════════════════════════════════════════════════════════
# Sprint 2 — Overlap-Scope Candidates (3 tests)
# ═══════════════════════════════════════════════════════════════════

class TestOverlapScopeCandidates:
    """Verify overlap-scope candidate generation."""

    def test_shared_scope_keys_produce_candidate(self):
        """Bundles with shared scope keys and no shared events → overlap_scope."""
        # Remove event keys to prevent same-event match
        bundle_a = make_tremor_bundle().model_copy(
            update={"event_keys": []},
        )
        bundle_b = make_corona_bundle().model_copy(
            update={"event_keys": []},
        )
        candidates = generate_candidates([bundle_a, bundle_b])

        overlap = [c for c in candidates if c.candidate_type == "overlap_scope"]
        assert len(overlap) == 1
        assert SHARED_SCOPE_KEY.key() in overlap[0].matching_keys

    def test_partial_overlap_classification(self):
        """Shared < total scope keys → PARTIAL or WEAK based on ratio."""
        # 1 shared out of 3 total unique scopes → ratio = 1/3 ≤ 50% → WEAK
        bundle_a = make_tremor_bundle().model_copy(
            update={
                "event_keys": [],
                "scope_keys": [
                    SHARED_SCOPE_KEY,
                    TheatreScopeKey(scope_type="entity", scope_value="btc-usd"),
                ],
            },
        )
        bundle_b = make_corona_bundle().model_copy(
            update={
                "event_keys": [],
                "scope_keys": [
                    SHARED_SCOPE_KEY,
                    TheatreScopeKey(scope_type="entity", scope_value="covid-variant-x"),
                ],
            },
        )
        candidates = generate_candidates([bundle_a, bundle_b])
        overlap = [c for c in candidates if c.candidate_type == "overlap_scope"]
        assert len(overlap) == 1
        # 1 shared (region:us-equities) out of 3 unique → WEAK
        assert overlap[0].match_strength == "WEAK"

    def test_scope_key_normalization_case_mismatch(self):
        """Case-mismatched scope keys still match after normalization (SDD §4.4)."""
        bundle_a = make_tremor_bundle().model_copy(
            update={
                "event_keys": [],
                "scope_keys": [TheatreScopeKey(scope_type="Region", scope_value="US_Equities")],
            },
        )
        bundle_b = make_corona_bundle().model_copy(
            update={
                "event_keys": [],
                "scope_keys": [TheatreScopeKey(scope_type="region", scope_value="us-equities")],
            },
        )
        candidates = generate_candidates([bundle_a, bundle_b])
        overlap = [c for c in candidates if c.candidate_type == "overlap_scope"]
        assert len(overlap) == 1
        assert overlap[0].match_strength == "EXACT"
        assert "region:us-equities" in overlap[0].matching_keys


# ═══════════════════════════════════════════════════════════════════
# Sprint 2 — No-Match Behavior (2 tests)
# ═══════════════════════════════════════════════════════════════════

class TestNoMatchBehavior:
    """Verify no candidates emitted when bundles don't overlap."""

    def test_zero_overlap_no_candidates(self):
        """Bundles with no shared events or scopes produce no candidates."""
        bundle_a = make_tremor_bundle().model_copy(
            update={
                "event_keys": ["event-a-only"],
                "scope_keys": [TheatreScopeKey(scope_type="region", scope_value="asia")],
            },
        )
        bundle_b = make_corona_bundle().model_copy(
            update={
                "event_keys": ["event-b-only"],
                "scope_keys": [TheatreScopeKey(scope_type="region", scope_value="europe")],
            },
        )
        candidates = generate_candidates([bundle_a, bundle_b])
        assert len(candidates) == 0

    def test_same_construct_pair_skipped(self):
        """Two bundles with the same construct_slug are never compared."""
        tremor_1 = make_tremor_bundle()
        tremor_2 = make_tremor_bundle().model_copy(
            update={"certificate_id": "cert-tremor-002"},
        )
        candidates = generate_candidates([tremor_1, tremor_2])
        assert len(candidates) == 0


# ═══════════════════════════════════════════════════════════════════
# Sprint 3 — 038 Shape Compatibility (4 tests)
# ═══════════════════════════════════════════════════════════════════

class TestShapeCompatibility:
    """Prove 038a bundles can populate 038 downstream model fields."""

    def test_settlement_outcomes_fact_anchor_link_shape(self):
        """Settlement outcomes have fields needed for FactAnchorLink population.

        FactAnchorLink requires: link_type, linked_entity_id, linked_entity_type,
        link_confidence. Bundle settlement_outcomes provide the resolution data
        that maps to these fields.
        """
        bundle = make_tremor_bundle()
        for template_id, outcome in bundle.settlement_outcomes.items():
            # Fields that map to FactAnchorLink
            link_type = "settlement"
            linked_entity_id = template_id     # maps to linked_entity_id
            linked_entity_type = "theatre_outcome"
            link_confidence = 1.0 if outcome["resolution"] == "CORRECT" else 0.0

            assert isinstance(linked_entity_id, str)
            assert len(linked_entity_id) <= 50
            assert linked_entity_type in ("theatre_outcome",)
            assert 0.0 <= link_confidence <= 1.0
            assert link_type in ("settlement", "evidence", "oracle_query")

        # TREMOR has 2 outcomes
        assert len(bundle.settlement_outcomes) == 2

    def test_oracle_values_oracle_response_shape(self):
        """Oracle values have fields needed for OracleResponse population.

        OracleResponse requires: source, event_id, value_json, queried_at,
        is_provisional. Bundle oracle_values provide the data.
        """
        bundle = make_corona_bundle()
        for source_id, oracle_val in bundle.oracle_values.items():
            # Fields that map to OracleResponse
            source = source_id                  # maps to source
            value_json = {"value": oracle_val["value"]}  # maps to value_json
            is_provisional = oracle_val["is_provisional"]

            assert isinstance(source, str)
            assert len(source) <= 100
            assert isinstance(value_json, dict)
            assert isinstance(is_provisional, bool)

        assert bundle.oracle_source_ids == ["src-who"]

    def test_scope_keys_coherence_group_shape(self):
        """Scope keys can inform CoherenceGroup membership.

        CoherenceGroup requires: name, group_type, policy_json.
        Scope keys provide the matching criteria for group membership.
        """
        bundle = make_tremor_bundle()
        for sk in bundle.scope_keys:
            # Scope key → CoherenceGroup membership fields
            group_name = f"{bundle.construct_slug}:{sk.key()}"
            group_type = "domain_overlap"

            assert isinstance(group_name, str)
            assert len(group_name) <= 200
            assert group_type in ("domain_overlap",)
            assert ":" in sk.key()  # Properly serialized

        assert len(bundle.scope_keys) == 2

    def test_candidate_pair_scanner_input_shape(self):
        """Candidate set provides the pairwise structure scanner expects.

        CrossTheatreParadoxScanner.scan_fact_anchor() compares pairs of
        theatres linked to the same FactAnchor. A ComparisonCandidateSet
        provides this pairwise structure with matching context.
        """
        tremor = make_tremor_bundle()
        corona = make_corona_bundle()
        candidates = generate_candidates([tremor, corona])

        assert len(candidates) >= 1
        candidate = candidates[0]

        # Scanner needs two distinct theatre references
        assert candidate.bundle_a.construct_slug != candidate.bundle_b.construct_slug

        # Scanner needs shared event context (what the anchor represents)
        assert len(candidate.matching_keys) >= 1

        # Both bundles must have settlement state for paradox evaluation
        assert candidate.bundle_a.settlement_state is not None
        assert candidate.bundle_b.settlement_state is not None

        # Both bundles must have oracle values for oracle consistency check
        assert len(candidate.bundle_a.oracle_values) >= 1
        assert len(candidate.bundle_b.oracle_values) >= 1


# ═══════════════════════════════════════════════════════════════════
# Sprint 3 — End-to-End TREMOR↔CORONA (3 tests)
# ═══════════════════════════════════════════════════════════════════

class TestEndToEndTremorCorona:
    """Full path: execution results → bundles → candidates → 038 shapes."""

    def test_builder_without_shared_keys_produces_no_candidates(self):
        """Builder output with default template-ID event keys cannot match.

        Template IDs are construct-specific (tmpl-eq-001 vs tmpl-pandemic-001),
        so builder output without caller-provided shared keys produces no
        cross-theatre candidates. This documents the gap that event_keys/
        scope_keys parameters exist to close.
        """
        tremor_bundle = build_comparison_bundle(
            make_tremor_execution_result(),
            make_tremor_fixture_input(),
        )
        corona_bundle = build_comparison_bundle(
            make_corona_execution_result(),
            make_corona_fixture_input(),
        )

        # Template IDs are construct-specific — no overlap
        assert set(tremor_bundle.event_keys) & set(corona_bundle.event_keys) == set()
        assert tremor_bundle.scope_keys == []
        assert corona_bundle.scope_keys == []

        candidates = generate_candidates([tremor_bundle, corona_bundle])
        assert len(candidates) == 0

    def test_builder_with_shared_event_keys_produces_candidates(self):
        """Builder output with caller-provided shared event keys produces
        same-event candidates — the real runtime path."""
        shared_event = SHARED_EVENT_KEY

        tremor_bundle = build_comparison_bundle(
            make_tremor_execution_result(),
            make_tremor_fixture_input(),
            certificate_id="cert-e2e-tremor",
            event_keys=[shared_event],
        )
        corona_bundle = build_comparison_bundle(
            make_corona_execution_result(),
            make_corona_fixture_input(),
            certificate_id="cert-e2e-corona",
            event_keys=[shared_event],
        )

        # Both bundles now share the real-world event key
        assert tremor_bundle.event_keys == [shared_event]
        assert corona_bundle.event_keys == [shared_event]

        # Execution summary integrity preserved through the full path
        assert tremor_bundle.settlement_state == "DISPUTED"
        assert corona_bundle.settlement_state == "SETTLED"
        assert tremor_bundle.execution_summary.executed_count == 3

        candidates = generate_candidates([tremor_bundle, corona_bundle])
        assert len(candidates) == 1
        assert candidates[0].candidate_type == "same_event"
        assert candidates[0].match_strength == "EXACT"
        assert shared_event in candidates[0].matching_keys

    def test_builder_with_shared_scope_keys_produces_candidates(self):
        """Builder output with caller-provided scope keys produces
        overlap-scope candidates — the real runtime path."""
        shared_scope = SHARED_SCOPE_KEY

        tremor_bundle = build_comparison_bundle(
            make_tremor_execution_result(),
            make_tremor_fixture_input(),
            scope_keys=[shared_scope],
        )
        corona_bundle = build_comparison_bundle(
            make_corona_execution_result(),
            make_corona_fixture_input(),
            scope_keys=[shared_scope],
        )

        # Template IDs still construct-specific → no same-event match
        assert set(tremor_bundle.event_keys) & set(corona_bundle.event_keys) == set()

        # But scope keys match → overlap-scope candidate
        candidates = generate_candidates([tremor_bundle, corona_bundle])
        assert len(candidates) == 1
        assert candidates[0].candidate_type == "overlap_scope"
        assert shared_scope.key() in candidates[0].matching_keys
