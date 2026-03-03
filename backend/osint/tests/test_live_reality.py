"""Tests for LiveOSINTRealityProvider — full pipeline E2E with mocks.

All tests use mock data — no real HTTP calls.
"""
from __future__ import annotations

import json
import tempfile
import time
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.engines.reality_signal import LiveOSINTRealityProvider, RealitySignal
from backend.osint.engine.collection_runner import CollectionPlan, CollectionRunner
from backend.osint.engine.corroboration import CorroborationEngine, CorroborationResult
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


def _make_registry_file() -> str:
    """Write a temporary registry JSON file and return its path."""
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


def _make_bundle(confidence: float = 0.80) -> EvidenceBundle:
    """Create a minimal EvidenceBundle for testing."""
    now = datetime.now(timezone.utc)
    return EvidenceBundle(
        bundle_id="eb_wm_cii_test",
        source_id="worldmonitor_cii",
        source_group="alt_data_behavioural",
        resolution_role="primary_evidence",
        evidence_timestamp=now,
        raw_payload_hash="a" * 64,
        receipt=HTTPTranscriptReceipt(
            timestamp=now,
            request_parameters={"method": "POST", "url": "http://localhost/test"},
            source_id="worldmonitor_cii",
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


def _make_oracle_output(
    composite_score: float = 0.56,
    evidence_completeness: float = 1.0,
    bundle_hash: str = "b" * 64,
) -> OracleOutput:
    """Create an OracleOutput for testing."""
    now = datetime.now(timezone.utc)
    bundle = _make_bundle()
    return OracleOutput(
        theatre_id="test_theatre",
        composite_score=composite_score,
        criterion_scores=[
            CriterionScore("corroboration_minimum_met", False, 0.7, "test"),
            CriterionScore("counter_signal_checked", True, 1.0, "test"),
        ],
        evidence_bundles=[bundle],
        corroboration_result=CorroborationResult(
            theatre_id="test_theatre",
            primary_bundles=[bundle],
            corroborating_bundles=[],
            distinct_source_groups=1,
            corroboration_minimum=2,
            corroboration_met=False,
        ),
        counter_signal_results=[],
        evidence_completeness=evidence_completeness,
        bundle_hash=bundle_hash,
        scored_at=now,
    )


def _build_live_provider(
    oracle_output: OracleOutput | None = None,
) -> LiveOSINTRealityProvider:
    """Build a LiveOSINTRealityProvider with mocked components."""
    path = _make_registry_file()
    loader = RegistryLoader(path)

    # Mock CollectionRunner
    runner = MagicMock(spec=CollectionRunner)
    plan = CollectionPlan(
        theatre_id="test_theatre",
        sources=["worldmonitor_cii"],
        evaluation_window=(datetime.now(timezone.utc), datetime.now(timezone.utc)),
    )
    runner.build_plan.return_value = plan

    # Mock the async collect to return a coroutine-like object
    bundle = _make_bundle()
    mock_result = CollectionResult(
        source_id="worldmonitor_cii",
        bundle=bundle,
        raw_payload=b'{"test": true}',
        fetch_duration_ms=50.0,
        success=True,
        retrieved_at=datetime.now(timezone.utc),
    )
    runner.collect = AsyncMock(return_value=[mock_result])

    # Real corroboration engine
    corr_engine = CorroborationEngine(loader)

    # Real counter-signal evaluator
    cs_evaluator = CounterSignalEvaluator()

    # Mock scorer to return controlled output
    scorer = MagicMock(spec=Scorer)
    output = oracle_output or _make_oracle_output()
    scorer.score.return_value = output

    oracle_config = {
        "theatre_id": "test_theatre",
        "sources": ["worldmonitor_cii"],
        "corroboration_minimum": 2,
    }

    return LiveOSINTRealityProvider(
        collection_runner=runner,
        corroboration_engine=corr_engine,
        counter_signal_evaluator=cs_evaluator,
        scorer=scorer,
        oracle_config=oracle_config,
        max_staleness_s=300.0,
        provider_version="011.1",
    )


# ── Tests ──────────────────────────────────────────────────────────


class TestLiveOSINTRealityProvider:
    """Tests for LiveOSINTRealityProvider."""

    def test_get_signal_returns_reality_signal(self) -> None:
        """Full pipeline produces a valid RealitySignal."""
        provider = _build_live_provider()
        signal = provider.get_signal("test_theatre")

        assert isinstance(signal, RealitySignal)
        assert signal.source_type == "osint"

    def test_p_reality_equals_composite_score(self) -> None:
        """RealitySignal.p_reality matches OracleOutput.composite_score."""
        output = _make_oracle_output(composite_score=0.56)
        provider = _build_live_provider(output)
        signal = provider.get_signal("test_theatre")

        assert signal.p_reality == 0.56

    def test_evidence_bundle_hash_matches(self) -> None:
        """RealitySignal.evidence_bundle_hash matches OracleOutput.bundle_hash."""
        output = _make_oracle_output(bundle_hash="c" * 64)
        provider = _build_live_provider(output)
        signal = provider.get_signal("test_theatre")

        assert signal.evidence_bundle_hash == "c" * 64

    def test_staleness_returns_none_p_reality(self) -> None:
        """Stale evidence produces p_reality=None."""
        provider = _build_live_provider()

        # First call — gets fresh data
        signal = provider.get_signal("test_theatre")
        assert signal.p_reality is not None

        # Simulate staleness by setting last output time far in the past
        provider._last_output_time["test_theatre"] = time.monotonic() - 600

        # Now collection runner should be called again.
        # But let's force the runner to fail to test stale fallback
        provider._runner.collect = AsyncMock(side_effect=Exception("network down"))

        signal_stale = provider.get_signal("test_theatre")
        assert signal_stale.p_reality is None

    def test_oracle_output_id_format(self) -> None:
        """oracle_output_id format: "{theatre_id}_{scored_at_ms}"."""
        now = datetime.now(timezone.utc)
        output = _make_oracle_output()
        output.scored_at = now
        provider = _build_live_provider(output)

        signal = provider.get_signal("test_theatre")

        expected_ms = int(now.timestamp() * 1000)
        assert signal.certificate_id == f"test_theatre_{expected_ms}"

    def test_provider_version(self) -> None:
        """RealitySignal.provider_version == "011.1"."""
        provider = _build_live_provider()
        signal = provider.get_signal("test_theatre")

        assert signal.provider_version == "011.1"

    def test_evidence_completeness_propagated(self) -> None:
        """evidence_completeness from OracleOutput present in RealitySignal."""
        output = _make_oracle_output(evidence_completeness=0.67)
        provider = _build_live_provider(output)
        signal = provider.get_signal("test_theatre")

        assert signal.evidence_completeness == 0.67

    def test_fresh_cache_reused(self) -> None:
        """If cached output is fresh, pipeline is NOT re-run."""
        provider = _build_live_provider()

        # First call — runs pipeline
        signal1 = provider.get_signal("test_theatre")
        assert signal1.p_reality is not None

        # Second call — should reuse cache (no staleness)
        # Reset the mock to track if it's called again
        provider._runner.collect.reset_mock()
        signal2 = provider.get_signal("test_theatre")

        # Runner should NOT have been called again
        provider._runner.collect.assert_not_called()
        assert signal2.p_reality == signal1.p_reality
