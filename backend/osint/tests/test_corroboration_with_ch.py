"""Corroboration engine tests with Companies House — multi-source verification.

Verifies that adding a source with a distinct independence_upstream_id
breaks the single-source corroboration limitation. No code changes to
the corroboration engine — these tests verify existing behaviour with new data.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from backend.osint.engine.corroboration import CorroborationEngine
from backend.osint.engine.scorer import Scorer
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

SOURCES_PATH = str(Path(__file__).parent.parent / "sources.json")


_FAKE_HASH = "a" * 64  # Valid 64-char SHA-256 placeholder


def _make_bundle(source_id: str, source_group: str, confidence: float = 0.8) -> EvidenceBundle:
    """Create a minimal EvidenceBundle for testing."""
    now = datetime.now(timezone.utc)
    ts = int(now.timestamp())
    receipt = HTTPTranscriptReceipt(
        timestamp=now,
        request_parameters={"method": "GET", "url": "http://test", "query": "", "headers": ""},
        source_id=source_id,
        source_version="v1.0",
        http_status=200,
        content_hash=_FAKE_HASH,
        receipt_hash=_FAKE_HASH,
    )
    event = NormalisedEvent(
        event_id=f"evt_{source_id}_{ts}",
        geo=GeoPoint(lat=0.0, lon=0.0, radius_m=50000),
        measure=NormalisedMeasure(
            type=MeasureType.COUNTRY_INSTABILITY_INDEX, value=0.5, unit="0_1",
        ),
        confidence=confidence,
        timestamp=now,
    )
    return EvidenceBundle(
        bundle_id=f"eb_{source_id}_{ts}",
        source_id=source_id,
        source_group=source_group,
        resolution_role="primary_evidence",
        evidence_timestamp=now,
        raw_payload_hash=_FAKE_HASH,
        receipt=receipt,
        normalised_event=event,
    )


def _make_collection_result(bundle: EvidenceBundle) -> CollectionResult:
    """Wrap a bundle in a successful CollectionResult."""
    return CollectionResult(
        source_id=bundle.source_id,
        bundle=bundle,
        raw_payload=b'{"test": true}',
        fetch_duration_ms=10.0,
        success=True,
        retrieved_at=datetime.now(timezone.utc),
    )


class TestCorroborationWithCH:
    """Verify corroboration engine behaviour with WM + CH sources."""

    def test_wm_only_still_provisional(self) -> None:
        """3 WM results with same upstream_id -> 1 group -> corroboration_met: false."""
        registry = RegistryLoader(SOURCES_PATH)
        engine = CorroborationEngine(registry)

        results = [
            _make_collection_result(_make_bundle("worldmonitor_cii", "alt_data_behavioural", 0.8)),
            _make_collection_result(_make_bundle("worldmonitor_finance", "market_data", 0.7)),
            _make_collection_result(_make_bundle("worldmonitor_maritime", "maritime_ais", 0.6)),
        ]

        corr = engine.evaluate(results, {"theatre_id": "test", "corroboration_minimum": 2})

        assert corr.distinct_source_groups == 1
        assert corr.corroboration_met is False

    def test_wm_plus_ch_meets_minimum(self) -> None:
        """1 WM + 1 CH -> 2 upstream groups -> corroboration_met: true."""
        registry = RegistryLoader(SOURCES_PATH)
        engine = CorroborationEngine(registry)

        results = [
            _make_collection_result(_make_bundle("worldmonitor_cii", "alt_data_behavioural", 0.8)),
            _make_collection_result(_make_bundle("companies_house_api", "official_gov", 1.0)),
        ]

        corr = engine.evaluate(results, {"theatre_id": "test", "corroboration_minimum": 2})

        assert corr.distinct_source_groups == 2
        assert corr.corroboration_met is True

    def test_ch_only_insufficient(self) -> None:
        """1 CH result alone -> 1 group -> corroboration_met: false."""
        registry = RegistryLoader(SOURCES_PATH)
        engine = CorroborationEngine(registry)

        results = [
            _make_collection_result(_make_bundle("companies_house_api", "official_gov", 1.0)),
        ]

        corr = engine.evaluate(results, {"theatre_id": "test", "corroboration_minimum": 2})

        assert corr.distinct_source_groups == 1
        assert corr.corroboration_met is False

    def test_corroboration_factor_lifts(self) -> None:
        """WM + CH -> scoring composite uses 1.0 factor instead of 0.7."""
        registry = RegistryLoader(SOURCES_PATH)
        engine = CorroborationEngine(registry)
        scorer = Scorer(registry)

        # With corroboration met (WM + CH)
        results_met = [
            _make_collection_result(_make_bundle("worldmonitor_cii", "alt_data_behavioural", 0.8)),
            _make_collection_result(_make_bundle("companies_house_api", "official_gov", 1.0)),
        ]
        corr_met = engine.evaluate(results_met, {"theatre_id": "test", "corroboration_minimum": 2})
        assert corr_met.corroboration_met is True

        score_met = scorer.compute_composite(
            bundles=corr_met.primary_bundles,
            corroboration_met=True,
            counter_signal_pass=True,
            evidence_completeness=1.0,
        )

        # Without corroboration met (WM only)
        results_unmet = [
            _make_collection_result(_make_bundle("worldmonitor_cii", "alt_data_behavioural", 0.8)),
            _make_collection_result(_make_bundle("worldmonitor_finance", "market_data", 0.7)),
        ]
        corr_unmet = engine.evaluate(results_unmet, {"theatre_id": "test", "corroboration_minimum": 2})
        assert corr_unmet.corroboration_met is False

        score_unmet = scorer.compute_composite(
            bundles=corr_unmet.primary_bundles,
            corroboration_met=False,
            counter_signal_pass=True,
            evidence_completeness=1.0,
        )

        # Score with corroboration should be higher (factor 1.0 vs 0.7)
        assert score_met > score_unmet
