"""Tests for CounterSignalChecker (Stage 2b).

Tests: all 11 class names, checked+not-found passes, checked+found+allow_gap
passes, checked+found+no-allow fails, unchecked fails, gap kind handling.
"""

from __future__ import annotations

import pytest

from osint_pipeline.engine.counter_signal import (
    COUNTER_SIGNAL_CLASSES,
    CounterSignalChecker,
)
from osint_pipeline.models.evidence import (
    CollectionStatus,
    GapKind,
    GapReport,
)
from tests.osint_pipeline.conftest import make_bundle


def _cs_bundle(cs_class: str, detected: bool = False, detail: str | None = None):
    """Build a counter-signal bundle."""
    extract = {"counter_signal_detected": detected}
    if detail:
        extract["counter_signal_detail"] = detail
    return make_bundle(
        source_id=f"cs_{cs_class}",
        source_group=cs_class,
        resolution_role="counter_signal",
        query_context={"counter_signal_class": cs_class},
        structured_extract=extract,
    )


def _cs_gap(
    cs_class: str,
    gap_kind: GapKind = GapKind.INTELLIGENCE_GAP,
    reason: CollectionStatus = CollectionStatus.TIMEOUT,
):
    """Build a counter-signal gap report."""
    return GapReport(
        source_id=f"cs_{cs_class}",
        source_group=cs_class,
        jurisdiction="GB",
        reason=reason,
        gap_kind=gap_kind,
    )


class TestCounterSignalClasses:
    """Verify all 11 classes are declared."""

    def test_has_11_classes(self):
        assert len(COUNTER_SIGNAL_CLASSES) == 11

    def test_known_classes(self):
        expected = {
            "calendar_holiday", "calendar_trading_halt", "outage_reported",
            "policy_rule_change", "regulatory_status_change", "legal_dispute_active",
            "sanctions_designation", "corporate_event", "force_majeure",
            "data_revision_notice", "seasonal_pattern",
        }
        assert set(COUNTER_SIGNAL_CLASSES) == expected


class TestCounterSignalCheckedNotFound:
    """checked=True, signal_found=False -> PASS."""

    def test_checked_not_found_passes(self):
        checker = CounterSignalChecker()
        bundles = [_cs_bundle("calendar_holiday", detected=False)]
        results = checker.evaluate(bundles, [], required_classes=["calendar_holiday"])

        assert len(results) == 1
        r = results[0]
        assert r.checked is True
        assert r.signal_found is False
        assert r.passed is True


class TestCounterSignalCheckedFound:
    """checked=True, signal_found=True."""

    def test_found_without_allow_gap_fails(self):
        checker = CounterSignalChecker()
        bundles = [_cs_bundle("force_majeure", detected=True, detail="Pandemic")]
        results = checker.evaluate(bundles, [], required_classes=["force_majeure"])

        r = results[0]
        assert r.checked is True
        assert r.signal_found is True
        assert r.allow_gap is False
        assert r.passed is False

    def test_found_with_allow_gap_passes(self):
        checker = CounterSignalChecker(allow_gaps={"force_majeure": True})
        bundles = [_cs_bundle("force_majeure", detected=True, detail="Pandemic")]
        results = checker.evaluate(bundles, [], required_classes=["force_majeure"])

        r = results[0]
        assert r.signal_found is True
        assert r.allow_gap is True
        assert r.passed is True


class TestCounterSignalUnchecked:
    """Unchecked (gaps or no source) -> FAIL."""

    def test_intelligence_gap_fails(self):
        """INTELLIGENCE_GAP means we couldn't check -> checked=False -> FAIL."""
        checker = CounterSignalChecker()
        gaps = [_cs_gap("outage_reported", GapKind.INTELLIGENCE_GAP)]
        results = checker.evaluate([], gaps, required_classes=["outage_reported"])

        r = results[0]
        assert r.checked is False
        assert r.passed is False

    def test_no_source_configured_fails(self):
        checker = CounterSignalChecker()
        results = checker.evaluate([], [], required_classes=["sanctions_designation"])

        r = results[0]
        assert r.checked is False
        assert r.signal_detail == "No source configured for this class"
        assert r.passed is False


class TestCounterSignalGapKind:
    """Concern 2: SIGNAL_ABSENCE vs INTELLIGENCE_GAP."""

    def test_signal_absence_passes(self):
        """SIGNAL_ABSENCE is evidence — checked=True, signal_found=False."""
        checker = CounterSignalChecker()
        gaps = [_cs_gap("data_revision_notice", GapKind.SIGNAL_ABSENCE)]
        results = checker.evaluate([], gaps, required_classes=["data_revision_notice"])

        r = results[0]
        assert r.checked is True
        assert r.signal_found is False
        assert r.passed is True
        assert "evidential absence" in r.signal_detail

    def test_intelligence_gap_fails(self):
        """INTELLIGENCE_GAP is uncertainty — checked=False."""
        checker = CounterSignalChecker()
        gaps = [_cs_gap("seasonal_pattern", GapKind.INTELLIGENCE_GAP)]
        results = checker.evaluate([], gaps, required_classes=["seasonal_pattern"])

        r = results[0]
        assert r.checked is False
        assert r.passed is False


class TestCounterSignalMultipleClasses:
    """Test evaluation across multiple classes."""

    def test_mixed_classes(self):
        checker = CounterSignalChecker(allow_gaps={"force_majeure": True})
        bundles = [
            _cs_bundle("calendar_holiday", detected=False),
            _cs_bundle("force_majeure", detected=True, detail="Earthquake"),
        ]
        gaps = [_cs_gap("outage_reported", GapKind.INTELLIGENCE_GAP)]

        results = checker.evaluate(
            bundles, gaps,
            required_classes=["calendar_holiday", "force_majeure", "outage_reported"],
        )

        by_class = {r.counter_signal_class: r for r in results}
        assert by_class["calendar_holiday"].passed is True
        assert by_class["force_majeure"].passed is True  # allow_gap
        assert by_class["outage_reported"].passed is False  # intelligence gap

    def test_auto_discover_classes(self):
        """Without required_classes, evaluates classes found in bundles/gaps."""
        checker = CounterSignalChecker()
        bundles = [_cs_bundle("calendar_holiday", detected=False)]
        gaps = [_cs_gap("outage_reported", GapKind.INTELLIGENCE_GAP)]

        results = checker.evaluate(bundles, gaps)
        classes = {r.counter_signal_class for r in results}
        assert "calendar_holiday" in classes
        assert "outage_reported" in classes


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
