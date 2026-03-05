"""Tests for Commitment Monitor — drift detection with impact assessment."""

from backend.investigation.commitment_monitor import (
    CommitmentMonitor,
    DriftEvent,
    DriftImpact,
    DriftType,
)


class TestLogDriftEvent:
    def test_log_drift_event(self):
        monitor = CommitmentMonitor()
        event = monitor.log_drift(
            drift_type=DriftType.ENTITY_RESTRUCTURE,
            original_value="Company A Ltd",
            new_value="Company A Holdings PLC",
            impact_assessment=DriftImpact.MATERIAL,
            evidence_ref="E005",
        )

        assert event.drift_id == "D001"
        assert event.drift_type == DriftType.ENTITY_RESTRUCTURE
        assert event.original_value == "Company A Ltd"
        assert event.new_value == "Company A Holdings PLC"
        assert event.impact_assessment == DriftImpact.MATERIAL
        assert event.evidence_ref == "E005"
        assert len(monitor.events) == 1


class TestHasMaterialDrift:
    def test_has_material_drift_false(self):
        monitor = CommitmentMonitor()
        monitor.log_drift(
            drift_type=DriftType.CONTRACT_AMENDMENT,
            original_value="v1",
            new_value="v1.1",
            impact_assessment=DriftImpact.NON_MATERIAL,
        )

        assert monitor.has_material_drift() is False

    def test_has_material_drift_true(self):
        monitor = CommitmentMonitor()
        monitor.log_drift(
            drift_type=DriftType.MARKET_RULE_CHANGE,
            original_value="Rule A",
            new_value="Rule B",
            impact_assessment=DriftImpact.MATERIAL,
        )

        assert monitor.has_material_drift() is True


class TestDriftEventFields:
    def test_drift_event_fields(self):
        monitor = CommitmentMonitor()
        event = monitor.log_drift(
            drift_type=DriftType.REGULATORY_STATUS_CHANGE,
            original_value="authorized",
            new_value="suspended",
            impact_assessment=DriftImpact.MATERIAL,
            evidence_ref="E010",
        )

        assert isinstance(event, DriftEvent)
        assert event.drift_type == DriftType.REGULATORY_STATUS_CHANGE
        assert event.detected_at is not None
        assert event.evidence_ref == "E010"


class TestMultipleDriftEvents:
    def test_multiple_drift_events(self):
        monitor = CommitmentMonitor()
        monitor.log_drift(
            drift_type=DriftType.CONTRACT_AMENDMENT,
            original_value="v1",
            new_value="v2",
            impact_assessment=DriftImpact.NON_MATERIAL,
        )
        monitor.log_drift(
            drift_type=DriftType.JURISDICTION_CHANGE,
            original_value="UK",
            new_value="Cayman Islands",
            impact_assessment=DriftImpact.MATERIAL,
        )
        monitor.log_drift(
            drift_type=DriftType.ENTITY_RESTRUCTURE,
            original_value="LLC",
            new_value="PLC",
            impact_assessment=DriftImpact.NON_MATERIAL,
        )

        assert len(monitor.events) == 3
        assert monitor.events[0].drift_id == "D001"
        assert monitor.events[1].drift_id == "D002"
        assert monitor.events[2].drift_id == "D003"
        assert monitor.has_material_drift() is True
