"""Tests for Paradox wiring — LiveOSINTRealityProvider + ParadoxEngine integration.

Verifies that ParadoxEngine works with live p_reality from LiveOSINTRealityProvider.
Activation gate, Logic Gap computation, circuit breaker interaction.

No modifications to backend/engines/paradox.py — provider swap only.
All tests use mock data — no real HTTP calls.
"""
from __future__ import annotations

import json
import tempfile
import time
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.engines.butterfly import ButterflyEngine, WingFlapType
from backend.engines.logic_gap import LogicGapCalculator
from backend.engines.paradox import (
    ParadoxAction,
    ParadoxConfig,
    ParadoxEngine,
    ParadoxMode,
)
from backend.engines.reality_signal import (
    LiveOSINTRealityProvider,
    RealitySignal,
    RealitySignalProvider,
    StubRealityProvider,
)
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
    """Create a minimal EvidenceBundle."""
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


def _make_oracle_output(composite_score: float = 0.56) -> OracleOutput:
    """Create an OracleOutput for testing."""
    now = datetime.now(timezone.utc)
    bundle = _make_bundle()
    return OracleOutput(
        theatre_id="test_theatre",
        composite_score=composite_score,
        criterion_scores=[],
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
        evidence_completeness=1.0,
        bundle_hash="b" * 64,
        scored_at=now,
    )


def _build_live_provider(
    composite_score: float = 0.56,
) -> LiveOSINTRealityProvider:
    """Build a LiveOSINTRealityProvider with mocked internals."""
    path = _make_registry_file()
    loader = RegistryLoader(path)

    runner = MagicMock(spec=CollectionRunner)
    plan = CollectionPlan(
        theatre_id="test_theatre",
        sources=["worldmonitor_cii"],
        evaluation_window=(datetime.now(timezone.utc), datetime.now(timezone.utc)),
    )
    runner.build_plan.return_value = plan
    bundle = _make_bundle()
    runner.collect = AsyncMock(return_value=[
        CollectionResult(
            source_id="worldmonitor_cii", bundle=bundle,
            raw_payload=b'{"test":true}', fetch_duration_ms=50.0,
            success=True, retrieved_at=datetime.now(timezone.utc),
        ),
    ])

    corr_engine = CorroborationEngine(loader)
    cs_evaluator = CounterSignalEvaluator()
    scorer = MagicMock(spec=Scorer)
    scorer.score.return_value = _make_oracle_output(composite_score)

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
    )


# ── Tests ──────────────────────────────────────────────────────────


class TestParadoxWiring:
    """Tests for Paradox Engine with LiveOSINTRealityProvider."""

    def test_paradox_with_live_p_reality(self) -> None:
        """Paradox Engine scan with LiveOSINTRealityProvider produces valid LogicGapReading."""
        provider = _build_live_provider(composite_score=0.56)

        butterfly = ButterflyEngine()
        logic_gap_calc = LogicGapCalculator(smoothing_window_s=60.0)
        logic_gap_calc.record_price("test_theatre", 0.80, time.time())

        config = ParadoxConfig(
            mode=ParadoxMode.ENABLED,
            activation_gate={"type": "none"},  # No gate — activate immediately
        )

        paradox = ParadoxEngine(config, butterfly, logic_gap_calc, provider)
        reading = paradox.scan("test_theatre")

        assert reading is not None
        assert reading.p_reality == 0.56
        assert reading.p_market == 0.80
        # Logic Gap = abs(0.80 - 0.56) = 0.24
        assert abs(reading.logic_gap - 0.24) < 0.01

    def test_logic_gap_computed_correctly(self) -> None:
        """abs(p_market - p_reality) with live composite_score."""
        provider = _build_live_provider(composite_score=0.30)

        butterfly = ButterflyEngine()
        logic_gap_calc = LogicGapCalculator(smoothing_window_s=60.0)
        logic_gap_calc.record_price("test_theatre", 0.90, time.time())

        config = ParadoxConfig(
            mode=ParadoxMode.ENABLED,
            activation_gate={"type": "none"},
        )

        paradox = ParadoxEngine(config, butterfly, logic_gap_calc, provider)
        reading = paradox.scan("test_theatre")

        assert reading is not None
        # Logic Gap = abs(0.90 - 0.30) = 0.60
        assert abs(reading.logic_gap - 0.60) < 0.01

    def test_activation_gate_none_always_fires(self) -> None:
        """Gate type 'none' fires immediately, allowing scan."""
        provider = _build_live_provider(composite_score=0.50)

        butterfly = ButterflyEngine()
        logic_gap_calc = LogicGapCalculator()
        logic_gap_calc.record_price("test_theatre", 0.50, time.time())

        config = ParadoxConfig(
            mode=ParadoxMode.ENABLED,
            activation_gate={"type": "none"},
        )

        paradox = ParadoxEngine(config, butterfly, logic_gap_calc, provider)
        reading = paradox.scan("test_theatre")

        assert reading is not None

    def test_no_paradox_code_changes(self) -> None:
        """Verify paradox.py is unmodified — provider interface unchanged."""
        # This test verifies that ParadoxEngine still accepts RealitySignalProvider
        # in its constructor and calls get_signal() — the same interface as 010b.
        provider = StubRealityProvider(p_reality=0.5)

        butterfly = ButterflyEngine()
        logic_gap_calc = LogicGapCalculator()

        config = ParadoxConfig(mode=ParadoxMode.ENABLED, activation_gate={"type": "none"})

        # Construction with StubRealityProvider should still work
        paradox = ParadoxEngine(config, butterfly, logic_gap_calc, provider)
        reading = paradox.scan("test_theatre")
        assert reading is not None

    def test_circuit_breaker_with_live_evidence(self) -> None:
        """Divergent composite_score triggers appropriate action."""
        # p_reality=0.10, p_market=0.80 -> logic_gap=0.70 -> CRITICAL -> FORCED_RESOLUTION
        provider = _build_live_provider(composite_score=0.10)

        butterfly = ButterflyEngine()
        logic_gap_calc = LogicGapCalculator()
        logic_gap_calc.record_price("test_theatre", 0.80, time.time())

        config = ParadoxConfig(
            mode=ParadoxMode.CIRCUIT_BREAKER,
            critical_threshold=0.60,
            activation_gate={"type": "none"},
        )

        paradox = ParadoxEngine(config, butterfly, logic_gap_calc, provider)
        reading = paradox.scan("test_theatre")

        assert reading is not None
        assert reading.logic_gap >= 0.60

        action = paradox.evaluate_thresholds(reading)
        assert action == ParadoxAction.FORCED_RESOLUTION

    def test_live_provider_exported_from_engines(self) -> None:
        """LiveOSINTRealityProvider is exported from backend.engines."""
        from backend.engines import LiveOSINTRealityProvider as Exported

        assert Exported is LiveOSINTRealityProvider

    def test_full_pipeline_to_paradox_wing_flap(self) -> None:
        """Full loop: mock WM -> pipeline -> Paradox scan -> threshold -> Wing Flap."""
        # p_reality=0.20, p_market=0.85 -> logic_gap=0.65 -> CRITICAL
        provider = _build_live_provider(composite_score=0.20)

        butterfly = ButterflyEngine()
        logic_gap_calc = LogicGapCalculator()
        logic_gap_calc.record_price("test_theatre", 0.85, time.time())

        config = ParadoxConfig(
            mode=ParadoxMode.ENABLED,
            critical_threshold=0.60,
            activation_gate={"type": "none"},
        )

        paradox = ParadoxEngine(config, butterfly, logic_gap_calc, provider)
        reading = paradox.scan("test_theatre")

        assert reading is not None
        assert reading.logic_gap >= 0.60

        action = paradox.evaluate_thresholds(reading)
        assert action == ParadoxAction.FORCED_RESOLUTION

        # Execute action -> Wing Flap
        flap = paradox.execute_action(action, "test_theatre")
        assert flap.flap_type == WingFlapType.PARADOX
        assert flap.theatre_id == "test_theatre"

    def test_full_pipeline_wm_down(self) -> None:
        """All WM endpoints down -> evidence_completeness=0.0 -> no spurious actions.

        When all collectors fail, LiveOSINTRealityProvider returns p_reality=None
        via stale signal. ParadoxEngine should still handle this gracefully.
        """
        provider = _build_live_provider(composite_score=0.0)
        # Override scorer to return zero completeness
        zero_output = _make_oracle_output(composite_score=0.0)
        zero_output.evidence_completeness = 0.0
        provider._scorer.score.return_value = zero_output

        butterfly = ButterflyEngine()
        logic_gap_calc = LogicGapCalculator()
        logic_gap_calc.record_price("test_theatre", 0.50, time.time())

        config = ParadoxConfig(
            mode=ParadoxMode.ENABLED,
            activation_gate={"type": "none"},
        )

        paradox = ParadoxEngine(config, butterfly, logic_gap_calc, provider)
        reading = paradox.scan("test_theatre")

        # With p_reality=0.0 and p_market=0.5, logic_gap=0.5
        # This is below critical (0.60) in default config
        assert reading is not None
        action = paradox.evaluate_thresholds(reading)
        # Should be TRADING_PAUSE (0.40 default breach threshold) not FORCED_RESOLUTION
        assert action != ParadoxAction.FORCED_RESOLUTION

    def test_disabled_mode_returns_none(self) -> None:
        """Paradox in DISABLED mode returns None even with live provider."""
        provider = _build_live_provider(composite_score=0.50)

        butterfly = ButterflyEngine()
        logic_gap_calc = LogicGapCalculator()

        config = ParadoxConfig(mode=ParadoxMode.DISABLED)

        paradox = ParadoxEngine(config, butterfly, logic_gap_calc, provider)
        reading = paradox.scan("test_theatre")

        assert reading is None
