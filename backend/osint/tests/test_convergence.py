"""Tests for ConvergenceDetector — cell binning, alert threshold, Theatre matching.

All tests use synthetic data — no real HTTP calls.
"""
from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone

import pytest

from backend.osint.engine.convergence import (
    ConvergenceAlert,
    ConvergenceCell,
    ConvergenceDetector,
)
from backend.osint.models.evidence import (
    EvidenceBundle,
    GeoPoint,
    HTTPTranscriptReceipt,
    MeasureType,
    NormalisedEvent,
    NormalisedMeasure,
)


# ── Helpers ────────────────────────────────────────────────────────


def _make_bundle(
    source_id: str,
    source_group: str,
    lat: float,
    lon: float,
    confidence: float = 0.80,
    timestamp: datetime | None = None,
    bundle_id: str | None = None,
) -> EvidenceBundle:
    """Create a minimal EvidenceBundle at a specific location."""
    ts = timestamp or datetime.now(timezone.utc)
    return EvidenceBundle(
        bundle_id=bundle_id or f"eb_{source_id}_{int(ts.timestamp())}",
        source_id=source_id,
        source_group=source_group,
        resolution_role="primary_evidence",
        evidence_timestamp=ts,
        raw_payload_hash="a" * 64,
        receipt=HTTPTranscriptReceipt(
            timestamp=ts,
            request_parameters={"method": "POST", "url": "http://localhost/test"},
            source_id=source_id,
            source_version="v0.1.0",
            http_status=200,
            content_hash="a" * 64,
        ),
        normalised_event=NormalisedEvent(
            event_id=f"evt_{source_id}_001",
            geo=GeoPoint(lat=lat, lon=lon, radius_m=50000),
            measure=NormalisedMeasure(
                type=MeasureType.COUNTRY_INSTABILITY_INDEX,
                value=0.7,
                unit="0_1",
            ),
            confidence=confidence,
            timestamp=ts,
        ),
    )


# ── Tests ──────────────────────────────────────────────────────────


class TestConvergenceDetector:
    """Tests for ConvergenceDetector."""

    def test_cell_binning(self) -> None:
        """Events at (51.5, -0.1) bin to cell (51, -1)."""
        detector = ConvergenceDetector()
        cell_key = detector._cell_key(51.5, -0.1)
        assert cell_key == (51, -1)

    def test_cell_binning_positive(self) -> None:
        """Events at (32.4, 53.7) bin to cell (32, 53)."""
        detector = ConvergenceDetector()
        cell_key = detector._cell_key(32.4, 53.7)
        assert cell_key == (32, 53)

    def test_cell_binning_negative(self) -> None:
        """Events at (-33.9, -70.2) bin to cell (-34, -71)."""
        detector = ConvergenceDetector()
        cell_key = detector._cell_key(-33.9, -70.2)
        assert cell_key == (-34, -71)

    def test_alert_threshold_3_types(self) -> None:
        """Alert fires when 3+ distinct source_group types in cell."""
        detector = ConvergenceDetector(min_event_types=3)
        now = datetime.now(timezone.utc)

        bundles = [
            _make_bundle("cii", "alt_data_behavioural", 32.4, 53.7, timestamp=now, bundle_id="eb_1"),
            _make_bundle("fin", "market_data", 32.5, 53.8, timestamp=now, bundle_id="eb_2"),
            _make_bundle("mar", "maritime_ais", 32.6, 53.9, timestamp=now, bundle_id="eb_3"),
        ]

        alerts = detector.detect(bundles)
        assert len(alerts) == 1
        assert len(alerts[0].cell.event_types) == 3

    def test_no_alert_below_threshold(self) -> None:
        """2 domain types does not fire alert (threshold=3)."""
        detector = ConvergenceDetector(min_event_types=3)
        now = datetime.now(timezone.utc)

        bundles = [
            _make_bundle("cii", "alt_data_behavioural", 32.4, 53.7, timestamp=now, bundle_id="eb_1"),
            _make_bundle("fin", "market_data", 32.5, 53.8, timestamp=now, bundle_id="eb_2"),
        ]

        alerts = detector.detect(bundles)
        assert len(alerts) == 0

    def test_single_domain_no_alert(self) -> None:
        """1 domain type does not fire alert."""
        detector = ConvergenceDetector(min_event_types=3)
        now = datetime.now(timezone.utc)

        bundles = [
            _make_bundle("cii_1", "alt_data_behavioural", 32.4, 53.7, timestamp=now, bundle_id="eb_1"),
            _make_bundle("cii_2", "alt_data_behavioural", 32.5, 53.8, timestamp=now, bundle_id="eb_2"),
            _make_bundle("cii_3", "alt_data_behavioural", 32.6, 53.9, timestamp=now, bundle_id="eb_3"),
        ]

        alerts = detector.detect(bundles)
        assert len(alerts) == 0

    def test_empty_bundles_no_alerts(self) -> None:
        """Empty bundle list produces no alerts."""
        detector = ConvergenceDetector()
        alerts = detector.detect([])
        assert len(alerts) == 0

    def test_theatre_matching(self) -> None:
        """Theatre geo within cell bounds matches alert."""
        detector = ConvergenceDetector(min_event_types=3)
        now = datetime.now(timezone.utc)

        bundles = [
            _make_bundle("cii", "alt_data_behavioural", 32.4, 53.7, timestamp=now, bundle_id="eb_1"),
            _make_bundle("fin", "market_data", 32.5, 53.8, timestamp=now, bundle_id="eb_2"),
            _make_bundle("mar", "maritime_ais", 32.6, 53.9, timestamp=now, bundle_id="eb_3"),
        ]

        alerts = detector.detect(bundles)
        assert len(alerts) == 1

        # Theatre at (32.5, 53.5) is within cell (32, 53)
        theatres = [{"theatre_id": "iran_strait", "geo": {"lat": 32.5, "lon": 53.5}}]
        matched = detector.match_theatres(alerts, theatres)
        assert matched[0].theatre_id == "iran_strait"

    def test_theatre_no_match(self) -> None:
        """Theatre geo outside cell bounds does not match."""
        detector = ConvergenceDetector(min_event_types=3)
        now = datetime.now(timezone.utc)

        bundles = [
            _make_bundle("cii", "alt_data_behavioural", 32.4, 53.7, timestamp=now, bundle_id="eb_1"),
            _make_bundle("fin", "market_data", 32.5, 53.8, timestamp=now, bundle_id="eb_2"),
            _make_bundle("mar", "maritime_ais", 32.6, 53.9, timestamp=now, bundle_id="eb_3"),
        ]

        alerts = detector.detect(bundles)
        assert len(alerts) == 1

        # Theatre at (50.0, -0.1) is in a completely different cell
        theatres = [{"theatre_id": "london", "geo": {"lat": 50.0, "lon": -0.1}}]
        matched = detector.match_theatres(alerts, theatres)
        assert matched[0].theatre_id is None

    def test_convergence_score(self) -> None:
        """Convergence score rewards type diversity and event density."""
        detector = ConvergenceDetector(min_event_types=3)
        now = datetime.now(timezone.utc)

        bundles = [
            _make_bundle("cii", "alt_data_behavioural", 32.4, 53.7, timestamp=now, bundle_id="eb_1"),
            _make_bundle("fin", "market_data", 32.5, 53.8, timestamp=now, bundle_id="eb_2"),
            _make_bundle("mar", "maritime_ais", 32.6, 53.9, timestamp=now, bundle_id="eb_3"),
        ]

        alerts = detector.detect(bundles)
        assert len(alerts) == 1

        score = alerts[0].cell.convergence_score
        # (3/3) * (1 + log2(3)) = 1.0 * (1 + 1.585) ≈ 2.585
        expected = (3.0 / 3.0) * (1.0 + math.log2(3))
        assert abs(score - expected) < 0.01

    def test_time_window_filtering(self) -> None:
        """Events outside 24-hour window excluded."""
        detector = ConvergenceDetector(min_event_types=3, window_hours=24.0)
        now = datetime.now(timezone.utc)
        old = now - timedelta(hours=48)  # 2 days ago, outside window

        bundles = [
            _make_bundle("cii", "alt_data_behavioural", 32.4, 53.7, timestamp=now, bundle_id="eb_1"),
            _make_bundle("fin", "market_data", 32.5, 53.8, timestamp=now, bundle_id="eb_2"),
            # This one is outside the window
            _make_bundle("mar", "maritime_ais", 32.6, 53.9, timestamp=old, bundle_id="eb_3"),
        ]

        alerts = detector.detect(bundles)
        # Only 2 events within window, threshold=3 -> no alert
        assert len(alerts) == 0

    def test_multiple_cells(self) -> None:
        """Events in different cells produce separate alerts."""
        detector = ConvergenceDetector(min_event_types=2)  # Lower threshold for test
        now = datetime.now(timezone.utc)

        bundles = [
            # Cell (32, 53)
            _make_bundle("cii", "alt_data_behavioural", 32.4, 53.7, timestamp=now, bundle_id="eb_1"),
            _make_bundle("fin", "market_data", 32.5, 53.8, timestamp=now, bundle_id="eb_2"),
            # Cell (51, -1)
            _make_bundle("mar", "maritime_ais", 51.5, -0.1, timestamp=now, bundle_id="eb_3"),
            _make_bundle("sat", "satellite_imagery", 51.6, -0.2, timestamp=now, bundle_id="eb_4"),
        ]

        alerts = detector.detect(bundles)
        assert len(alerts) == 2

    def test_alert_has_provenance(self) -> None:
        """All events in convergence alerts carry full provenance."""
        detector = ConvergenceDetector(min_event_types=3)
        now = datetime.now(timezone.utc)

        bundles = [
            _make_bundle("cii", "alt_data_behavioural", 32.4, 53.7, timestamp=now, bundle_id="eb_1"),
            _make_bundle("fin", "market_data", 32.5, 53.8, timestamp=now, bundle_id="eb_2"),
            _make_bundle("mar", "maritime_ais", 32.6, 53.9, timestamp=now, bundle_id="eb_3"),
        ]

        alerts = detector.detect(bundles)
        assert len(alerts) == 1

        cell = alerts[0].cell
        # Every event should have geo data (provenance from bundles)
        for event in cell.events:
            assert event.geo is not None
            assert event.geo.lat != 0.0 or event.geo.lon != 0.0
