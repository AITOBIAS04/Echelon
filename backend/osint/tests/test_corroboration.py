"""Tests for CorroborationEngine — dedup, minimum enforcement, audit trail.

All tests use mock data — no real HTTP calls.
"""
from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone

import pytest

from backend.osint.engine.corroboration import CorroborationEngine, CorroborationResult
from backend.osint.models.evidence import (
    CollectionResult,
    EvidenceBundle,
    GeoPoint,
    HTTPTranscriptReceipt,
    MeasureType,
    NormalisedEvent,
    NormalisedMeasure,
    WMDomain,
)
from backend.osint.models.registry import RegistryLoader


# ── Helpers ────────────────────────────────────────────────────────


def _make_registry_file(sources: list[dict]) -> str:
    """Write a temporary registry JSON file and return its path."""
    data = {"sources": sources}
    f = tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, encoding="utf-8"
    )
    json.dump(data, f)
    f.close()
    return f.name


def _make_bundle(
    source_id: str,
    source_group: str,
    resolution_role: str = "primary_evidence",
    confidence: float = 0.8,
    bundle_id: str | None = None,
) -> EvidenceBundle:
    """Create a minimal EvidenceBundle for testing."""
    now = datetime.now(timezone.utc)
    return EvidenceBundle(
        bundle_id=bundle_id or f"eb_{source_id}_{int(now.timestamp())}",
        source_id=source_id,
        source_group=source_group,
        resolution_role=resolution_role,
        evidence_timestamp=now,
        raw_payload_hash="a" * 64,
        receipt=HTTPTranscriptReceipt(
            timestamp=now,
            request_parameters={"method": "POST", "url": "http://localhost:8080/test"},
            source_id=source_id,
            source_version="v0.1.0",
            http_status=200,
            content_hash="a" * 64,
        ),
        normalised_event=NormalisedEvent(
            event_id=f"evt_{source_id}_001",
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


def _make_collection_result(
    bundle: EvidenceBundle,
    success: bool = True,
) -> CollectionResult:
    """Wrap a bundle in a CollectionResult."""
    return CollectionResult(
        source_id=bundle.source_id,
        bundle=bundle if success else None,
        raw_payload=b'{"test": true}',
        fetch_duration_ms=50.0,
        success=success,
        error=None if success else "fetch failed",
        retrieved_at=datetime.now(timezone.utc),
    )


def _wm_registry_sources() -> list[dict]:
    """Three WM sources sharing independence_upstream_id=worldmonitor."""
    return [
        {
            "source_id": "worldmonitor_cii",
            "source_name": "WM CII",
            "source_group": "alt_data_behavioural",
            "resolution_role": "primary_evidence",
            "independence_upstream_id": "worldmonitor",
            "receipt_mode_minimum": "http_transcript",
            "priority_bucket": "scoring_grade",
        },
        {
            "source_id": "worldmonitor_finance",
            "source_name": "WM Finance",
            "source_group": "market_data",
            "resolution_role": "primary_evidence",
            "independence_upstream_id": "worldmonitor",
            "receipt_mode_minimum": "http_transcript",
            "priority_bucket": "scoring_grade",
        },
        {
            "source_id": "worldmonitor_maritime",
            "source_name": "WM Maritime",
            "source_group": "maritime_ais",
            "resolution_role": "primary_evidence",
            "independence_upstream_id": "worldmonitor",
            "receipt_mode_minimum": "http_transcript",
            "priority_bucket": "scoring_grade",
        },
    ]


# ── Tests ──────────────────────────────────────────────────────────


class TestCorroborationEngine:
    """Tests for CorroborationEngine."""

    def test_dedup_same_upstream_id(self) -> None:
        """3 WM bundles with independence_upstream_id=worldmonitor collapse to 1."""
        path = _make_registry_file(_wm_registry_sources())
        loader = RegistryLoader(path)
        engine = CorroborationEngine(loader)

        bundles = [
            _make_bundle("worldmonitor_cii", "alt_data_behavioural", confidence=0.85),
            _make_bundle("worldmonitor_finance", "market_data", confidence=0.72),
            _make_bundle("worldmonitor_maritime", "maritime_ais", confidence=0.68),
        ]
        results = [_make_collection_result(b) for b in bundles]

        corr = engine.evaluate(results, {"theatre_id": "test_theatre", "corroboration_minimum": 2})

        # All 3 collapsed to 1 (same upstream_id)
        assert len(corr.primary_bundles) == 1
        assert corr.distinct_source_groups == 1

    def test_dedup_keeps_strongest_confidence(self) -> None:
        """Dedup retains the highest-confidence entry per upstream_id group."""
        path = _make_registry_file(_wm_registry_sources())
        loader = RegistryLoader(path)
        engine = CorroborationEngine(loader)

        bundles = [
            _make_bundle("worldmonitor_cii", "alt_data_behavioural", confidence=0.60),
            _make_bundle("worldmonitor_finance", "market_data", confidence=0.95),
            _make_bundle("worldmonitor_maritime", "maritime_ais", confidence=0.40),
        ]
        results = [_make_collection_result(b) for b in bundles]

        corr = engine.evaluate(results, {"theatre_id": "t", "corroboration_minimum": 2})

        assert len(corr.primary_bundles) == 1
        # Kept the highest confidence (0.95 from worldmonitor_finance)
        assert corr.primary_bundles[0].normalised_event.confidence == 0.95

    def test_corroboration_minimum_boundary(self) -> None:
        """minimum-1 = FAIL, minimum = PASS at exact boundary."""
        # One upstream = 1 distinct group
        sources = _wm_registry_sources()
        path = _make_registry_file(sources)
        loader = RegistryLoader(path)
        engine = CorroborationEngine(loader)

        bundles = [
            _make_bundle("worldmonitor_cii", "alt_data_behavioural", confidence=0.85),
        ]
        results = [_make_collection_result(b) for b in bundles]

        # minimum=2 => 1 group < 2 => FAIL
        corr = engine.evaluate(results, {"theatre_id": "t", "corroboration_minimum": 2})
        assert not corr.corroboration_met

        # minimum=1 => 1 group >= 1 => PASS
        corr = engine.evaluate(results, {"theatre_id": "t", "corroboration_minimum": 1})
        assert corr.corroboration_met

    def test_provisional_corroboration_wm_only(self) -> None:
        """WM-only = 1 distinct upstream, corroboration_met=false (default minimum 2)."""
        path = _make_registry_file(_wm_registry_sources())
        loader = RegistryLoader(path)
        engine = CorroborationEngine(loader)

        bundles = [
            _make_bundle("worldmonitor_cii", "alt_data_behavioural"),
            _make_bundle("worldmonitor_finance", "market_data"),
            _make_bundle("worldmonitor_maritime", "maritime_ais"),
        ]
        results = [_make_collection_result(b) for b in bundles]

        corr = engine.evaluate(results, {"theatre_id": "t", "corroboration_minimum": 2})

        assert corr.distinct_source_groups == 1
        assert not corr.corroboration_met

    def test_corroboration_with_independent_source(self) -> None:
        """Synthetic non-WM bundle injected gives 2 distinct groups => corroboration_met=true."""
        sources = _wm_registry_sources() + [
            {
                "source_id": "reuters_wire",
                "source_name": "Reuters Wire",
                "source_group": "wire_service",
                "resolution_role": "secondary_corroboration",
                "independence_upstream_id": "reuters",
                "receipt_mode_minimum": "http_transcript",
                "priority_bucket": "settlement_grade",
            },
        ]
        path = _make_registry_file(sources)
        loader = RegistryLoader(path)
        engine = CorroborationEngine(loader)

        bundles = [
            _make_bundle("worldmonitor_cii", "alt_data_behavioural"),
            _make_bundle(
                "reuters_wire", "wire_service",
                resolution_role="secondary_corroboration",
            ),
        ]
        results = [_make_collection_result(b) for b in bundles]

        corr = engine.evaluate(results, {"theatre_id": "t", "corroboration_minimum": 2})

        # worldmonitor + reuters = 2 distinct upstream IDs
        assert corr.distinct_source_groups == 2
        assert corr.corroboration_met

    def test_dedup_log_audit_trail(self) -> None:
        """Dedup decisions are recorded in the audit trail."""
        path = _make_registry_file(_wm_registry_sources())
        loader = RegistryLoader(path)
        engine = CorroborationEngine(loader)

        bundles = [
            _make_bundle("worldmonitor_cii", "alt_data_behavioural", confidence=0.85),
            _make_bundle("worldmonitor_finance", "market_data", confidence=0.72),
        ]
        results = [_make_collection_result(b) for b in bundles]

        corr = engine.evaluate(results, {"theatre_id": "t", "corroboration_minimum": 2})

        # Should have at least one dedup log entry
        assert len(corr.dedup_log) >= 1
        # Log entry should mention the kept source
        assert any("kept" in entry for entry in corr.dedup_log)

    def test_primary_secondary_separation(self) -> None:
        """Primary and secondary bundles are correctly separated by resolution_role."""
        sources = _wm_registry_sources() + [
            {
                "source_id": "reuters_wire",
                "source_name": "Reuters",
                "source_group": "wire_service",
                "resolution_role": "secondary_corroboration",
                "independence_upstream_id": "reuters",
                "receipt_mode_minimum": "http_transcript",
                "priority_bucket": "scoring_grade",
            },
        ]
        path = _make_registry_file(sources)
        loader = RegistryLoader(path)
        engine = CorroborationEngine(loader)

        primary = _make_bundle("worldmonitor_cii", "alt_data_behavioural")
        secondary = _make_bundle(
            "reuters_wire", "wire_service",
            resolution_role="secondary_corroboration",
        )
        results = [
            _make_collection_result(primary),
            _make_collection_result(secondary),
        ]

        corr = engine.evaluate(results, {"theatre_id": "t", "corroboration_minimum": 2})

        # Primary bundles contain only WM
        assert all(b.source_id.startswith("worldmonitor") for b in corr.primary_bundles)
        # Corroborating bundles contain reuters
        assert all(b.source_id == "reuters_wire" for b in corr.corroborating_bundles)

    def test_failed_results_excluded(self) -> None:
        """CollectionResults with success=False are excluded from corroboration."""
        path = _make_registry_file(_wm_registry_sources())
        loader = RegistryLoader(path)
        engine = CorroborationEngine(loader)

        good = _make_bundle("worldmonitor_cii", "alt_data_behavioural")
        bad = _make_bundle("worldmonitor_finance", "market_data")

        results = [
            _make_collection_result(good, success=True),
            _make_collection_result(bad, success=False),
        ]

        corr = engine.evaluate(results, {"theatre_id": "t", "corroboration_minimum": 1})

        # Only the successful bundle should be present
        total_bundles = len(corr.primary_bundles) + len(corr.corroborating_bundles)
        assert total_bundles == 1
