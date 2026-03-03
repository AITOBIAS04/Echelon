"""Evidence model tests — CollectionResult creation, bundle assembly, receipt fields."""
from __future__ import annotations

from datetime import datetime, timezone

from backend.osint.models.evidence import (
    CollectionResult,
    EvidenceBundle,
    GeoPoint,
    HTTPTranscriptReceipt,
    HealthStatus,
    MeasureType,
    NormalisedEvent,
    NormalisedMeasure,
    WMDomain,
)


class TestCollectionResult:
    """CollectionResult dataclass field validation."""

    def test_success_result_has_all_fields(self) -> None:
        """Successful CollectionResult has all 7 fields with correct types."""
        now = datetime.now(timezone.utc)
        geo = GeoPoint(lat=32.0, lon=53.0, radius_m=50000)
        measure = NormalisedMeasure(
            type=MeasureType.COUNTRY_INSTABILITY_INDEX, value=0.78, unit="0_1"
        )
        event = NormalisedEvent(
            event_id="evt_test_001", geo=geo, measure=measure,
            confidence=0.85, timestamp=now,
        )
        receipt = HTTPTranscriptReceipt(
            timestamp=now,
            request_parameters={"method": "POST", "url": "http://localhost/api"},
            source_id="worldmonitor_cii",
            source_version="v0.1.0",
            http_status=200,
            content_hash="a" * 64,
        )
        bundle = EvidenceBundle(
            bundle_id="eb_test_001",
            source_id="worldmonitor_cii",
            source_group="alt_data_behavioural",
            resolution_role="primary_evidence",
            evidence_timestamp=now,
            raw_payload_hash="a" * 64,
            receipt=receipt,
            normalised_event=event,
        )

        result = CollectionResult(
            source_id="worldmonitor_cii",
            bundle=bundle,
            raw_payload=b'{"test": true}',
            fetch_duration_ms=150.5,
            success=True,
            error=None,
            retrieved_at=now,
        )

        assert result.source_id == "worldmonitor_cii"
        assert result.bundle is not None
        assert result.bundle.bundle_id == "eb_test_001"
        assert isinstance(result.raw_payload, bytes)
        assert result.fetch_duration_ms == 150.5
        assert result.success is True
        assert result.error is None
        assert result.retrieved_at == now

    def test_failure_result_has_none_bundle(self) -> None:
        """Failed CollectionResult has bundle=None and error set."""
        result = CollectionResult(
            source_id="worldmonitor_cii",
            bundle=None,
            raw_payload=b"",
            fetch_duration_ms=5000.0,
            success=False,
            error="Timeout after 5.0s",
        )

        assert result.bundle is None
        assert result.success is False
        assert result.error == "Timeout after 5.0s"
        assert result.retrieved_at is None  # Default

    def test_raw_payload_is_bytes(self) -> None:
        """raw_payload field is bytes, not dict."""
        result = CollectionResult(
            source_id="test",
            bundle=None,
            raw_payload=b'{"json": "data"}',
            fetch_duration_ms=0.0,
            success=False,
        )
        assert isinstance(result.raw_payload, bytes)

    def test_default_optional_fields(self) -> None:
        """Optional fields default to None."""
        result = CollectionResult(
            source_id="test",
            bundle=None,
            raw_payload=b"",
            fetch_duration_ms=0.0,
            success=False,
        )
        assert result.error is None
        assert result.retrieved_at is None


class TestReExportedTypes:
    """Verify API contract types are properly re-exported."""

    def test_wm_domain_enum(self) -> None:
        """WMDomain enum has all three values."""
        assert WMDomain.INTELLIGENCE.value == "intelligence"
        assert WMDomain.MARKET.value == "market"
        assert WMDomain.MARITIME.value == "maritime"

    def test_health_status_enum(self) -> None:
        """HealthStatus enum has all three values."""
        assert HealthStatus.HEALTHY.value == "healthy"
        assert HealthStatus.DEGRADED.value == "degraded"
        assert HealthStatus.UNAVAILABLE.value == "unavailable"

    def test_measure_type_enum(self) -> None:
        """MeasureType enum includes key domain measures."""
        assert MeasureType.COUNTRY_INSTABILITY_INDEX.value == "country_instability_index"
        assert MeasureType.FX_VOLATILITY.value == "fx_volatility"
        assert MeasureType.VESSEL_DENSITY_ANOMALY.value == "vessel_density_anomaly"

    def test_evidence_bundle_creation(self) -> None:
        """EvidenceBundle can be instantiated with valid data."""
        now = datetime.now(timezone.utc)
        geo = GeoPoint(lat=26.5667, lon=56.25, radius_m=50000)
        measure = NormalisedMeasure(
            type=MeasureType.COUNTRY_INSTABILITY_INDEX, value=0.78, unit="0_1"
        )
        event = NormalisedEvent(
            event_id="evt_test_001", geo=geo, measure=measure,
            confidence=0.85, timestamp=now,
        )
        receipt = HTTPTranscriptReceipt(
            timestamp=now,
            request_parameters={"country": "IRN"},
            source_id="worldmonitor_cii",
            source_version="v0.1.0",
            http_status=200,
            content_hash="a" * 64,
        )
        bundle = EvidenceBundle(
            bundle_id="eb_test_001",
            source_id="worldmonitor_cii",
            source_group="alt_data_behavioural",
            resolution_role="primary_evidence",
            evidence_timestamp=now,
            raw_payload_hash="a" * 64,
            receipt=receipt,
            normalised_event=event,
        )
        assert bundle.source_id == "worldmonitor_cii"
        assert bundle.receipt.content_hash == "a" * 64
        assert bundle.normalised_event.confidence == 0.85
