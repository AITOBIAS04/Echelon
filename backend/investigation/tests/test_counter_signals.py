"""Tests for Investigation Counter-Signal Feed."""

from backend.investigation.counter_signals import (
    InvestigationCounterSignalClass,
    InvestigationCounterSignalFeed,
)


class TestLogCounterSignal:
    def test_log_counter_signal(self):
        feed = InvestigationCounterSignalFeed()
        cs = feed.log_counter_signal(
            signal_class=InvestigationCounterSignalClass.OFFICIAL_DENIAL,
            material=True,
            resolution_impact="May invalidate primary claim",
            detection_method="automated_osint",
            evidence_ref="E001",
        )

        assert cs.counter_signal_id == "CS001"
        assert cs.signal_class == InvestigationCounterSignalClass.OFFICIAL_DENIAL
        assert cs.material is True
        assert cs.resolution_impact == "May invalidate primary claim"
        assert cs.detection_method == "automated_osint"
        assert cs.evidence_ref == "E001"
        assert len(feed.signals) == 1

    def test_summary_counts(self):
        feed = InvestigationCounterSignalFeed()
        feed.log_counter_signal(
            signal_class=InvestigationCounterSignalClass.OFFICIAL_DENIAL,
            material=True,
            resolution_impact="impact1",
            detection_method="automated_osint",
        )
        feed.log_counter_signal(
            signal_class=InvestigationCounterSignalClass.FILING_CONTRADICTION,
            material=False,
            resolution_impact="impact2",
            detection_method="paradox_engine",
        )
        feed.log_counter_signal(
            signal_class=InvestigationCounterSignalClass.OFFICIAL_DENIAL,
            material=True,
            resolution_impact="impact3",
            detection_method="human_submitted",
        )

        summary = feed.get_summary()
        assert summary["checked"] == 2  # 2 distinct classes
        assert summary["gaps"] == 9  # 11 total - 2 checked
        assert summary["material_contradictions"] == 2  # 2 material signals


class TestEventDrivenClasses:
    def test_market_divergence_only_counted_when_logged(self):
        """MARKET_DIVERGENCE only counts toward 'checked' when explicitly logged."""
        feed = InvestigationCounterSignalFeed()

        # Before logging: MARKET_DIVERGENCE not counted
        summary_before = feed.get_summary()
        assert summary_before["checked"] == 0

        # Log a standard class
        feed.log_counter_signal(
            signal_class=InvestigationCounterSignalClass.OFFICIAL_DENIAL,
            material=False,
            resolution_impact="none",
            detection_method="automated_osint",
        )
        summary_mid = feed.get_summary()
        assert summary_mid["checked"] == 1

        # Now log MARKET_DIVERGENCE
        feed.log_counter_signal(
            signal_class=InvestigationCounterSignalClass.MARKET_DIVERGENCE,
            material=True,
            resolution_impact="market price diverged 15%",
            detection_method="automated_osint",
        )
        summary_after = feed.get_summary()
        assert summary_after["checked"] == 2  # Now counted

    def test_witness_recantation_only_counted_when_logged(self):
        """WITNESS_SOURCE_RECANTATION only counts toward 'checked' when explicitly logged."""
        feed = InvestigationCounterSignalFeed()

        summary_before = feed.get_summary()
        assert summary_before["checked"] == 0

        feed.log_counter_signal(
            signal_class=InvestigationCounterSignalClass.WITNESS_SOURCE_RECANTATION,
            material=True,
            resolution_impact="key witness retracted",
            detection_method="human_submitted",
        )
        summary_after = feed.get_summary()
        assert summary_after["checked"] == 1


class TestDetailFormat:
    def test_detail_format(self):
        feed = InvestigationCounterSignalFeed()
        feed.log_counter_signal(
            signal_class=InvestigationCounterSignalClass.REGULATORY_CLEARANCE,
            material=False,
            resolution_impact="Regulatory approval received",
            detection_method="automated_osint",
            evidence_ref="E003",
        )

        detail = feed.get_detail()
        assert len(detail) == 1
        d = detail[0]
        assert d["counter_signal_id"] == "CS001"
        assert d["signal_class"] == "regulatory_clearance"
        assert "detected_at" in d
        assert d["evidence_ref"] == "E003"
        assert d["material"] is False
        assert d["resolution_impact"] == "Regulatory approval received"
        assert d["detection_method"] == "automated_osint"


class TestMaterialTracking:
    def test_material_vs_non_material(self):
        feed = InvestigationCounterSignalFeed()
        feed.log_counter_signal(
            signal_class=InvestigationCounterSignalClass.TIMELINE_INCONSISTENCY,
            material=False,
            resolution_impact="minor discrepancy",
            detection_method="automated_osint",
        )
        feed.log_counter_signal(
            signal_class=InvestigationCounterSignalClass.FILING_CONTRADICTION,
            material=True,
            resolution_impact="contradicts primary filing",
            detection_method="paradox_engine",
        )

        summary = feed.get_summary()
        assert summary["material_contradictions"] == 1

        # Verify individual signals
        signals = feed.signals
        assert signals[0].material is False
        assert signals[1].material is True
