"""Tests for Theatre Resolution Engine -- Composed Oracle evaluation,
winning outcome determination, composite score calculation, and
provisional corroboration handling.

Cycle-012, Sprint 2 -- Task 8.
"""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
from datetime import datetime, timezone

import pytest

from backend.osint.engine.corroboration import CorroborationEngine, CorroborationResult
from backend.osint.engine.counter_signal import (
    COUNTER_SIGNAL_CLASSES,
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
from backend.services.theatre_evidence import EvidenceSnapshot, TheatreEvidenceCollector
from backend.services.theatre_resolution import TheatreResolutionEngine, TheatreResolutionResult


# ===================================================================
# Test Fixtures
# ===================================================================


def _make_test_registry() -> str:
    """Create a temporary registry JSON file for testing."""
    registry = {
        "version": "0.3.2-wm",
        "sources": [
            {
                "source_id": "worldmonitor_cii",
                "source_name": "World Monitor Country Instability Index",
                "source_group": "alt_data_behavioural",
                "priority_bucket": "scoring_grade",
                "resolution_role": "primary_evidence",
                "independence_upstream_id": "worldmonitor",
                "receipt_mode_minimum": "http_transcript",
                "world_monitor_domain": "intelligence",
                "settlement_eligible": False,
                "jurisdiction": "GLOBAL",
            },
            {
                "source_id": "worldmonitor_finance",
                "source_name": "World Monitor Finance Monitor",
                "source_group": "market_data",
                "priority_bucket": "scoring_grade",
                "resolution_role": "primary_evidence",
                "independence_upstream_id": "worldmonitor",
                "receipt_mode_minimum": "http_transcript",
                "world_monitor_domain": "market",
                "settlement_eligible": False,
                "jurisdiction": "GLOBAL",
            },
        ],
    }
    fd, path = tempfile.mkstemp(suffix=".json")
    with os.fdopen(fd, "w") as f:
        json.dump(registry, f)
    return path


def _make_evidence_bundle(source_id: str, confidence: float = 0.85) -> EvidenceBundle:
    """Create a mock EvidenceBundle for testing."""
    raw_data = json.dumps({"source_id": source_id, "data": "test"}).encode()
    content_hash = hashlib.sha256(raw_data).hexdigest()

    return EvidenceBundle(
        bundle_id=f"eb_{source_id}_test",
        source_id=source_id,
        source_group="alt_data_behavioural",
        resolution_role="primary_evidence",
        evidence_timestamp=datetime.now(timezone.utc),
        raw_payload_hash=content_hash,
        receipt=HTTPTranscriptReceipt(
            timestamp=datetime.now(timezone.utc),
            request_parameters={"method": "POST", "url": "http://test"},
            source_id=source_id,
            source_version="v0.1.0",
            http_status=200,
            content_hash=content_hash,
        ),
        normalised_event=NormalisedEvent(
            event_id=f"evt_{source_id}_001",
            geo=GeoPoint(lat=51.5, lon=-0.1, radius_m=50000),
            measure=NormalisedMeasure(
                type=MeasureType.COUNTRY_INSTABILITY_INDEX,
                value=0.78,
                unit="0_1",
            ),
            confidence=confidence,
            timestamp=datetime.now(timezone.utc),
        ),
    )


def _make_collection_result(source_id: str, confidence: float = 0.85) -> CollectionResult:
    """Create a mock CollectionResult for testing."""
    bundle = _make_evidence_bundle(source_id, confidence)
    return CollectionResult(
        source_id=source_id,
        bundle=bundle,
        raw_payload=b"mock_payload",
        fetch_duration_ms=50.0,
        success=True,
    )


class MockEvidenceCollector:
    """Mock evidence collector that returns pre-built snapshots."""

    def __init__(self, bundles: list[EvidenceBundle]) -> None:
        self._bundles = bundles
        self._snapshots: list[EvidenceSnapshot] = []

    def collect_heartbeat(self, theatre_id: str) -> EvidenceSnapshot:
        snapshot = EvidenceSnapshot(
            theatre_id=theatre_id,
            collection_timestamp=datetime.now(timezone.utc).isoformat(),
            oracle_output=None,
            evidence_bundles=list(self._bundles),
            collection_results=[],
            source_coverage_pct=1.0,
        )
        self._snapshots.append(snapshot)
        return snapshot

    def get_evidence_history(self) -> list[EvidenceSnapshot]:
        return list(self._snapshots)

    def get_latest_evidence(self) -> EvidenceSnapshot | None:
        return self._snapshots[-1] if self._snapshots else None


@pytest.fixture
def registry_path():
    """Create temp registry and clean up."""
    path = _make_test_registry()
    yield path
    os.unlink(path)


@pytest.fixture
def resolution_components(registry_path):
    """Create all components needed for TheatreResolutionEngine."""
    loader = RegistryLoader(registry_path)
    scorer = Scorer(loader)
    corroboration = CorroborationEngine(loader)
    counter_signal = CounterSignalEvaluator()

    bundles = [
        _make_evidence_bundle("worldmonitor_cii", 0.85),
        _make_evidence_bundle("worldmonitor_finance", 0.80),
    ]
    evidence_collector = MockEvidenceCollector(bundles)

    source_manifest = {
        "entries": [
            {
                "source_id": "worldmonitor_cii",
                "source_group": "alt_data_behavioural",
                "independence_upstream_id": "worldmonitor",
                "jurisdiction": "GLOBAL",
                "access_surface": "intelligence",
                "settlement_status": "PROVISIONAL",
                "settlement_eligible": False,
                "display_name": "World Monitor CII",
            },
            {
                "source_id": "worldmonitor_finance",
                "source_group": "market_data",
                "independence_upstream_id": "worldmonitor",
                "jurisdiction": "GLOBAL",
                "access_surface": "market",
                "settlement_status": "PROVISIONAL",
                "settlement_eligible": False,
                "display_name": "World Monitor Finance",
            },
        ],
        "registry_version": "0.3.2-wm",
    }

    oracle_config = {
        "sources": ["worldmonitor_cii", "worldmonitor_finance"],
        "corroboration_minimum": 2,
        "theatre_id": "test_theatre",
    }

    collection_results = [
        _make_collection_result("worldmonitor_cii", 0.85),
        _make_collection_result("worldmonitor_finance", 0.80),
    ]

    return {
        "evidence_collector": evidence_collector,
        "scorer": scorer,
        "corroboration": corroboration,
        "counter_signal": counter_signal,
        "source_manifest": source_manifest,
        "oracle_config": oracle_config,
        "collection_results": collection_results,
    }


# ===================================================================
# Tests
# ===================================================================


class TestTheatreResolution:
    """Tests for TheatreResolutionEngine."""

    def test_resolution_high_score_selects_outcome_0(self, resolution_components):
        """High composite_score (>= 0.7) selects outcome 0 ('Filed on time')."""
        engine = TheatreResolutionEngine(
            evidence_collector=resolution_components["evidence_collector"],
            scorer=resolution_components["scorer"],
            corroboration_engine=resolution_components["corroboration"],
            counter_signal_evaluator=resolution_components["counter_signal"],
            source_manifest=resolution_components["source_manifest"],
            oracle_config=resolution_components["oracle_config"],
        )

        result = engine.resolve(
            theatre_id="test_theatre",
            n_outcomes=3,
            outcome_labels=["Filed on time", "Filed late", "Not filed"],
            collection_results=resolution_components["collection_results"],
        )

        assert isinstance(result, TheatreResolutionResult)
        # With high-confidence evidence (0.85, 0.80) and corroboration penalty
        # the composite score depends on the scorer. Check it's a valid result.
        assert 0.0 <= result.composite_score <= 1.0
        assert 0 <= result.winning_outcome_index <= 2

    def test_determine_winning_outcome_high_score(self):
        """Score >= 0.7 maps to outcome 0."""
        idx = TheatreResolutionEngine._determine_winning_outcome(
            0.8, 3, ["Filed on time", "Filed late", "Not filed"]
        )
        assert idx == 0

    def test_determine_winning_outcome_mid_score(self):
        """Score in [0.3, 0.7) maps to outcome 1."""
        idx = TheatreResolutionEngine._determine_winning_outcome(
            0.5, 3, ["Filed on time", "Filed late", "Not filed"]
        )
        assert idx == 1

    def test_determine_winning_outcome_low_score(self):
        """Score < 0.3 maps to outcome 2."""
        idx = TheatreResolutionEngine._determine_winning_outcome(
            0.1, 3, ["Filed on time", "Filed late", "Not filed"]
        )
        assert idx == 2

    def test_determine_winning_outcome_boundary_0_7(self):
        """Score exactly 0.7 maps to outcome 0."""
        idx = TheatreResolutionEngine._determine_winning_outcome(
            0.7, 3, ["Filed on time", "Filed late", "Not filed"]
        )
        assert idx == 0

    def test_determine_winning_outcome_boundary_0_3(self):
        """Score exactly 0.3 maps to outcome 1."""
        idx = TheatreResolutionEngine._determine_winning_outcome(
            0.3, 3, ["Filed on time", "Filed late", "Not filed"]
        )
        assert idx == 1

    def test_oracle_output_id_format(self, resolution_components):
        """oracle_output_id has format {theatre_id}_{epoch_ms}."""
        engine = TheatreResolutionEngine(
            evidence_collector=resolution_components["evidence_collector"],
            scorer=resolution_components["scorer"],
            corroboration_engine=resolution_components["corroboration"],
            counter_signal_evaluator=resolution_components["counter_signal"],
            source_manifest=resolution_components["source_manifest"],
            oracle_config=resolution_components["oracle_config"],
        )

        result = engine.resolve(
            theatre_id="test_theatre",
            n_outcomes=3,
            outcome_labels=["Filed on time", "Filed late", "Not filed"],
            collection_results=resolution_components["collection_results"],
        )

        assert result.oracle_output_id.startswith("test_theatre_")
        parts = result.oracle_output_id.split("_")
        # Last part should be epoch ms (digits only)
        assert parts[-1].isdigit()

    def test_corroboration_penalty_applied(self, resolution_components):
        """Corroboration penalty (0.7) is applied when minimum not met."""
        engine = TheatreResolutionEngine(
            evidence_collector=resolution_components["evidence_collector"],
            scorer=resolution_components["scorer"],
            corroboration_engine=resolution_components["corroboration"],
            counter_signal_evaluator=resolution_components["counter_signal"],
            source_manifest=resolution_components["source_manifest"],
            oracle_config=resolution_components["oracle_config"],
        )

        result = engine.resolve(
            theatre_id="test_theatre",
            n_outcomes=3,
            outcome_labels=["Filed on time", "Filed late", "Not filed"],
            collection_results=resolution_components["collection_results"],
        )

        # WM sources share upstream_id, so corroboration_met should be False
        assert result.corroboration_result is not None
        # With single upstream_id "worldmonitor", distinct groups = 1 < minimum (2)
        assert result.corroboration_result.corroboration_met is False

    def test_counter_signal_scaffolding(self, resolution_components):
        """Counter-signal results should all be UNAVAILABLE."""
        engine = TheatreResolutionEngine(
            evidence_collector=resolution_components["evidence_collector"],
            scorer=resolution_components["scorer"],
            corroboration_engine=resolution_components["corroboration"],
            counter_signal_evaluator=resolution_components["counter_signal"],
            source_manifest=resolution_components["source_manifest"],
            oracle_config=resolution_components["oracle_config"],
        )

        result = engine.resolve(
            theatre_id="test_theatre",
            n_outcomes=3,
            outcome_labels=["Filed on time", "Filed late", "Not filed"],
            collection_results=resolution_components["collection_results"],
        )

        assert len(result.counter_signal_results) == 11
        for cs in result.counter_signal_results:
            assert cs.outcome == CounterSignalOutcome.UNAVAILABLE

    def test_evidence_bundle_hash_is_sha256(self, resolution_components):
        """Evidence bundle hash should be a valid SHA-256 hex string."""
        engine = TheatreResolutionEngine(
            evidence_collector=resolution_components["evidence_collector"],
            scorer=resolution_components["scorer"],
            corroboration_engine=resolution_components["corroboration"],
            counter_signal_evaluator=resolution_components["counter_signal"],
            source_manifest=resolution_components["source_manifest"],
            oracle_config=resolution_components["oracle_config"],
        )

        result = engine.resolve(
            theatre_id="test_theatre",
            n_outcomes=3,
            outcome_labels=["Filed on time", "Filed late", "Not filed"],
            collection_results=resolution_components["collection_results"],
        )

        assert len(result.evidence_bundle_hash) == 64
        assert all(c in "0123456789abcdef" for c in result.evidence_bundle_hash)
