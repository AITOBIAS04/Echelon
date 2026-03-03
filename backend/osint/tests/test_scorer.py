"""Tests for Scorer — composite score formula, penalties, bundle hash.

All tests use synthetic data — no real HTTP calls.
"""
from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone

import pytest

from backend.osint.engine.corroboration import CorroborationResult
from backend.osint.engine.counter_signal import (
    CounterSignalEvaluator,
    CounterSignalOutcome,
    CounterSignalResult,
)
from backend.osint.engine.scorer import CriterionScore, OracleOutput, Scorer
from backend.osint.models.evidence import (
    CollectionResult,
    EvidenceBundle,
    GeoPoint,
    HTTPTranscriptReceipt,
    MeasureType,
    NormalisedEvent,
    NormalisedMeasure,
)
from backend.osint.models.registry import RegistryLoader


# ── Helpers ────────────────────────────────────────────────────────


def _make_registry_file(sources: list[dict] | None = None) -> str:
    """Write a temporary registry JSON file and return its path."""
    if sources is None:
        sources = [
            {
                "source_id": "worldmonitor_cii",
                "source_name": "WM CII",
                "source_group": "alt_data_behavioural",
                "resolution_role": "primary_evidence",
                "independence_upstream_id": "worldmonitor",
                "receipt_mode_minimum": "http_transcript",
                "priority_bucket": "scoring_grade",
            },
        ]
    data = {"sources": sources}
    f = tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, encoding="utf-8"
    )
    json.dump(data, f)
    f.close()
    return f.name


def _make_bundle(
    source_id: str = "worldmonitor_cii",
    source_group: str = "alt_data_behavioural",
    confidence: float = 0.80,
    bundle_id: str = "eb_test_001",
    raw_hash: str = "a" * 64,
) -> EvidenceBundle:
    """Create a minimal EvidenceBundle for testing."""
    now = datetime.now(timezone.utc)
    return EvidenceBundle(
        bundle_id=bundle_id,
        source_id=source_id,
        source_group=source_group,
        resolution_role="primary_evidence",
        evidence_timestamp=now,
        raw_payload_hash=raw_hash,
        receipt=HTTPTranscriptReceipt(
            timestamp=now,
            request_parameters={"method": "POST", "url": "http://localhost/test"},
            source_id=source_id,
            source_version="v0.1.0",
            http_status=200,
            content_hash="a" * 64,
        ),
        normalised_event=NormalisedEvent(
            event_id="evt_test_001",
            geo=GeoPoint(lat=32.0, lon=53.0, radius_m=50000),
            measure=NormalisedMeasure(
                type=MeasureType.COUNTRY_INSTABILITY_INDEX,
                value=0.7,
                unit="0_1",
            ),
            confidence=confidence,
            timestamp=now,
        ),
    )


def _make_corroboration(
    bundles: list[EvidenceBundle],
    corroboration_met: bool = False,
    distinct_source_groups: int = 1,
) -> CorroborationResult:
    """Create a CorroborationResult for testing."""
    return CorroborationResult(
        theatre_id="test_theatre",
        primary_bundles=bundles,
        corroborating_bundles=[],
        distinct_source_groups=distinct_source_groups,
        corroboration_minimum=2,
        corroboration_met=corroboration_met,
        dedup_log=[],
    )


def _make_counter_signals_pass() -> list[CounterSignalResult]:
    """All UNAVAILABLE with allow_gap=True -> criterion PASS."""
    return [
        CounterSignalResult(
            signal_class=f"class_{i}",
            outcome=CounterSignalOutcome.UNAVAILABLE,
            source_id=None,
            detail="INTELLIGENCE_GAP",
            allow_gap=True,
        )
        for i in range(11)
    ]


def _make_counter_signals_fail() -> list[CounterSignalResult]:
    """One PRESENT_UNEXPLAINED -> criterion FAIL."""
    signals = _make_counter_signals_pass()
    signals[0] = CounterSignalResult(
        signal_class="weather",
        outcome=CounterSignalOutcome.PRESENT_UNEXPLAINED,
        source_id="weather_svc",
        detail="Hurricane",
        allow_gap=True,
    )
    return signals


def _make_collection_results(count: int = 3, all_success: bool = True) -> list[CollectionResult]:
    """Create a list of CollectionResult for testing."""
    results = []
    for i in range(count):
        results.append(
            CollectionResult(
                source_id=f"source_{i}",
                bundle=_make_bundle(bundle_id=f"eb_{i}") if all_success else None,
                raw_payload=b'{"test": true}',
                fetch_duration_ms=50.0,
                success=all_success,
                retrieved_at=datetime.now(timezone.utc),
            )
        )
    return results


# ── Tests ──────────────────────────────────────────────────────────


class TestScorer:
    """Tests for the Scorer class."""

    def test_composite_score_formula(self) -> None:
        """Composite score computed correctly with known inputs.

        confidence=0.80, corroboration_met=False (0.7), counter_signal_pass=True (1.0),
        evidence_completeness=1.0
        Expected: 0.80 * 0.7 * 1.0 * 1.0 = 0.56
        """
        path = _make_registry_file()
        loader = RegistryLoader(path)
        scorer = Scorer(loader)

        bundle = _make_bundle(confidence=0.80)
        corr = _make_corroboration([bundle], corroboration_met=False)
        cs = _make_counter_signals_pass()
        coll_results = [
            CollectionResult(
                source_id="worldmonitor_cii",
                bundle=bundle,
                raw_payload=b"test",
                fetch_duration_ms=50.0,
                success=True,
                retrieved_at=datetime.now(timezone.utc),
            ),
        ]

        output = scorer.score(corr, cs, coll_results, {"sources": ["worldmonitor_cii"]}, "t")

        assert abs(output.composite_score - 0.56) < 0.01

    def test_corroboration_penalty(self) -> None:
        """Score x 0.7 when corroboration_met=false."""
        path = _make_registry_file()
        loader = RegistryLoader(path)
        scorer = Scorer(loader)

        bundle = _make_bundle(confidence=1.0)  # Perfect confidence for clean math
        corr_unmet = _make_corroboration([bundle], corroboration_met=False)
        corr_met = _make_corroboration([bundle], corroboration_met=True, distinct_source_groups=2)
        cs = _make_counter_signals_pass()
        coll_results = [
            CollectionResult(
                source_id="worldmonitor_cii", bundle=bundle,
                raw_payload=b"t", fetch_duration_ms=1.0, success=True,
                retrieved_at=datetime.now(timezone.utc),
            ),
        ]

        out_unmet = scorer.score(corr_unmet, cs, coll_results, {"sources": ["worldmonitor_cii"]}, "t")
        out_met = scorer.score(corr_met, cs, coll_results, {"sources": ["worldmonitor_cii"]}, "t")

        # corr_unmet: 1.0 * 0.7 * 1.0 * 1.0 = 0.7
        # corr_met:   1.0 * 1.0 * 1.0 * 1.0 = 1.0
        assert abs(out_unmet.composite_score - 0.7) < 0.01
        assert abs(out_met.composite_score - 1.0) < 0.01

    def test_counter_signal_penalty(self) -> None:
        """Score x 0.5 when counter-signal fails."""
        path = _make_registry_file()
        loader = RegistryLoader(path)
        scorer = Scorer(loader)

        bundle = _make_bundle(confidence=1.0)
        corr = _make_corroboration([bundle], corroboration_met=True, distinct_source_groups=2)
        cs_fail = _make_counter_signals_fail()
        coll_results = [
            CollectionResult(
                source_id="worldmonitor_cii", bundle=bundle,
                raw_payload=b"t", fetch_duration_ms=1.0, success=True,
                retrieved_at=datetime.now(timezone.utc),
            ),
        ]

        output = scorer.score(corr, cs_fail, coll_results, {"sources": ["worldmonitor_cii"]}, "t")

        # 1.0 * 1.0 * 0.5 * 1.0 = 0.5
        assert abs(output.composite_score - 0.5) < 0.01

    def test_evidence_completeness_zero(self) -> None:
        """evidence_completeness=0.0 -> composite_score=0.0."""
        path = _make_registry_file()
        loader = RegistryLoader(path)
        scorer = Scorer(loader)

        bundle = _make_bundle(confidence=0.9)
        corr = _make_corroboration([bundle], corroboration_met=True)
        cs = _make_counter_signals_pass()
        # All failed results -> completeness = 0
        coll_results = [
            CollectionResult(
                source_id="worldmonitor_cii", bundle=None,
                raw_payload=b"", fetch_duration_ms=1.0, success=False,
                error="timeout", retrieved_at=datetime.now(timezone.utc),
            ),
        ]

        output = scorer.score(corr, cs, coll_results, {"sources": ["worldmonitor_cii"]}, "t")

        assert output.composite_score == 0.0
        assert output.evidence_completeness == 0.0

    def test_evidence_completeness_partial(self) -> None:
        """Partial completeness reduces score proportionally."""
        path = _make_registry_file()
        loader = RegistryLoader(path)
        scorer = Scorer(loader)

        bundle = _make_bundle(confidence=1.0)
        corr = _make_corroboration([bundle], corroboration_met=True, distinct_source_groups=2)
        cs = _make_counter_signals_pass()

        # 1 of 3 sources succeeded
        coll_results = [
            CollectionResult(
                source_id="s0", bundle=bundle, raw_payload=b"t",
                fetch_duration_ms=1.0, success=True,
                retrieved_at=datetime.now(timezone.utc),
            ),
            CollectionResult(
                source_id="s1", bundle=None, raw_payload=b"",
                fetch_duration_ms=1.0, success=False, error="fail",
                retrieved_at=datetime.now(timezone.utc),
            ),
            CollectionResult(
                source_id="s2", bundle=None, raw_payload=b"",
                fetch_duration_ms=1.0, success=False, error="fail",
                retrieved_at=datetime.now(timezone.utc),
            ),
        ]

        output = scorer.score(
            corr, cs, coll_results,
            {"sources": ["s0", "s1", "s2"]}, "t",
        )

        # evidence_completeness = 1/3
        assert abs(output.evidence_completeness - (1.0 / 3.0)) < 0.01
        # composite = 1.0 * 1.0 * 1.0 * (1/3) ≈ 0.333
        assert abs(output.composite_score - (1.0 / 3.0)) < 0.01

    def test_composite_score_clamped(self) -> None:
        """Composite score always in [0.0, 1.0]."""
        path = _make_registry_file()
        loader = RegistryLoader(path)
        scorer = Scorer(loader)

        # Even with high confidence, result should be <= 1.0
        bundle = _make_bundle(confidence=1.0)
        corr = _make_corroboration([bundle], corroboration_met=True, distinct_source_groups=2)
        cs = _make_counter_signals_pass()

        result = scorer.compute_composite(
            bundles=[bundle],
            corroboration_met=True,
            counter_signal_pass=True,
            evidence_completeness=1.0,
        )
        assert 0.0 <= result <= 1.0

    def test_bundle_hash_deterministic(self) -> None:
        """Same bundles (any order) produce same hash."""
        b1 = _make_bundle(bundle_id="eb_001", raw_hash="a" * 64)
        b2 = _make_bundle(bundle_id="eb_002", raw_hash="b" * 64)

        hash_ab = Scorer.compute_bundle_hash([b1, b2])
        hash_ba = Scorer.compute_bundle_hash([b2, b1])

        assert hash_ab == hash_ba
        assert len(hash_ab) == 64  # SHA-256 hex

    def test_bundle_hash_different_bundles(self) -> None:
        """Different bundles produce different hashes."""
        b1 = _make_bundle(bundle_id="eb_001", raw_hash="a" * 64)
        b2 = _make_bundle(bundle_id="eb_001", raw_hash="b" * 64)

        hash1 = Scorer.compute_bundle_hash([b1])
        hash2 = Scorer.compute_bundle_hash([b2])

        assert hash1 != hash2

    def test_empty_bundles_score_zero(self) -> None:
        """Empty bundle list produces composite_score=0.0."""
        path = _make_registry_file()
        loader = RegistryLoader(path)
        scorer = Scorer(loader)

        result = scorer.compute_composite(
            bundles=[],
            corroboration_met=True,
            counter_signal_pass=True,
            evidence_completeness=1.0,
        )
        assert result == 0.0

    def test_oracle_output_has_all_fields(self) -> None:
        """OracleOutput has all 9 required fields with correct types."""
        path = _make_registry_file()
        loader = RegistryLoader(path)
        scorer = Scorer(loader)

        bundle = _make_bundle(confidence=0.8)
        corr = _make_corroboration([bundle])
        cs = _make_counter_signals_pass()
        coll_results = [
            CollectionResult(
                source_id="worldmonitor_cii", bundle=bundle,
                raw_payload=b"t", fetch_duration_ms=1.0, success=True,
                retrieved_at=datetime.now(timezone.utc),
            ),
        ]

        output = scorer.score(corr, cs, coll_results, {"sources": ["worldmonitor_cii"]}, "t")

        assert isinstance(output.theatre_id, str)
        assert isinstance(output.composite_score, float)
        assert isinstance(output.criterion_scores, list)
        assert isinstance(output.evidence_bundles, list)
        assert isinstance(output.corroboration_result, CorroborationResult)
        assert isinstance(output.counter_signal_results, list)
        assert isinstance(output.evidence_completeness, float)
        assert isinstance(output.bundle_hash, str)
        assert isinstance(output.scored_at, datetime)

    def test_weighted_mean_by_priority_bucket(self) -> None:
        """Higher priority_bucket sources are weighted more heavily."""
        sources = [
            {
                "source_id": "settlement_src",
                "source_name": "Settlement",
                "source_group": "wire_service",
                "resolution_role": "primary_evidence",
                "independence_upstream_id": "settlement_src",
                "receipt_mode_minimum": "http_transcript",
                "priority_bucket": "settlement_grade",  # weight 3.0
            },
            {
                "source_id": "triage_src",
                "source_name": "Triage",
                "source_group": "social_platform",
                "resolution_role": "primary_evidence",
                "independence_upstream_id": "triage_src",
                "receipt_mode_minimum": "http_transcript",
                "priority_bucket": "triage_only",  # weight 1.0
            },
        ]
        path = _make_registry_file(sources)
        loader = RegistryLoader(path)
        scorer = Scorer(loader)

        # settlement_grade: confidence=1.0, weight=3.0
        # triage_only: confidence=0.0, weight=1.0
        # weighted mean = (1.0*3.0 + 0.0*1.0) / (3.0+1.0) = 0.75
        b_settlement = _make_bundle(
            source_id="settlement_src", source_group="wire_service",
            confidence=1.0, bundle_id="eb_s",
        )
        b_triage = _make_bundle(
            source_id="triage_src", source_group="social_platform",
            confidence=0.0, bundle_id="eb_t",
        )

        result = scorer.compute_composite(
            bundles=[b_settlement, b_triage],
            corroboration_met=True,
            counter_signal_pass=True,
            evidence_completeness=1.0,
        )

        assert abs(result - 0.75) < 0.01
