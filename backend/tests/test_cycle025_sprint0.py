"""
Cycle 025 Sprint 0 Tests — Schema + Migration + Response Models
"""
import pytest
from datetime import datetime


class TestMeasureTypeEnum:
    """Verify MeasureType has all 14 values."""

    def test_all_14_values_present(self):
        from backend.schemas.worldmonitor_api_contract import MeasureType
        expected = {
            "country_instability_index",
            "sector_risk_score",
            "fx_volatility",
            "commodity_anomaly",
            "vessel_density_anomaly",
            "ais_gap_detected",
            "dark_fleet_probability",
            # Cycle-025 additions
            "forecast_score",
            "forecast_weight",
            "corridor_risk",
            "shipping_rate_index",
            "supply_chain_severity",
            "sanctions_exposure",
            "cross_domain_convergence",
        }
        actual = {m.value for m in MeasureType}
        assert actual == expected
        assert len(MeasureType) == 14

    def test_string_serialisation_roundtrip(self):
        from backend.schemas.worldmonitor_api_contract import MeasureType
        for m in MeasureType:
            assert MeasureType(m.value) == m
            assert isinstance(m.value, str)


class TestResponseSchemaAdditions:
    """Verify new nullable fields on response models."""

    def _make_bundle(self):
        from backend.schemas.worldmonitor_api_contract import (
            EvidenceBundle, NormalisedEvent, NormalisedMeasure,
            GeoPoint, HTTPTranscriptReceipt, MeasureType,
        )
        now = datetime.utcnow()
        geo = GeoPoint(lat=26.5, lon=56.2)
        measure = NormalisedMeasure(type=MeasureType.COUNTRY_INSTABILITY_INDEX, value=0.7, unit="0_1")
        event = NormalisedEvent(event_id="evt_t_001", geo=geo, measure=measure, confidence=0.8, timestamp=now)
        receipt = HTTPTranscriptReceipt(
            timestamp=now, request_parameters={}, source_id="test",
            source_version="v0.1", http_status=200, content_hash="a" * 64,
        )
        return EvidenceBundle(
            bundle_id="eb_t", source_id="test", source_group="test_group",
            resolution_role="primary_evidence", evidence_timestamp=now,
            raw_payload_hash="a" * 64, receipt=receipt, normalised_event=event,
        )

    def test_backward_compat_old_payloads_parse(self):
        """Old payloads without new fields still parse (fields default to None)."""
        from backend.schemas.worldmonitor_api_contract import CIIResponse
        bundle = self._make_bundle()
        resp = CIIResponse(bundle=bundle)
        assert resp.forecast_score is None
        assert resp.forecast_weight is None
        assert resp.sanctions_exposure is None

    def test_new_fields_serialize_with_values(self):
        """New fields serialize when populated."""
        from backend.schemas.worldmonitor_api_contract import (
            CIIResponse, MarketSnapshotResponse, MaritimeAnomalyResponse,
        )
        bundle = self._make_bundle()

        cii = CIIResponse(bundle=bundle, forecast_score=0.85, sanctions_exposure=0.3)
        data = cii.model_dump()
        assert data["forecast_score"] == 0.85
        assert data["sanctions_exposure"] == 0.3

        mkt = MarketSnapshotResponse(bundle=bundle, supply_chain_severity=0.6)
        assert mkt.model_dump()["supply_chain_severity"] == 0.6

        mar = MaritimeAnomalyResponse(bundle=bundle, corridor="strait_hormuz", corridor_risk=0.9)
        d = mar.model_dump()
        assert d["corridor"] == "strait_hormuz"
        assert d["corridor_risk"] == 0.9

    def test_new_fields_serialize_as_null(self):
        """New fields serialize as null when not provided."""
        from backend.schemas.worldmonitor_api_contract import MaritimeAnomalyResponse
        bundle = self._make_bundle()
        resp = MaritimeAnomalyResponse(bundle=bundle)
        data = resp.model_dump()
        assert data["corridor"] is None
        assert data["corridor_risk"] is None
        assert data["shipping_rate_index"] is None


class TestOsintSignalModel:
    """Verify OsintSignal model can be instantiated."""

    def test_model_instantiation(self):
        from backend.database.models import OsintSignal
        assert OsintSignal.__tablename__ == "osint_signals"
        # Verify column names exist
        columns = {c.name for c in OsintSignal.__table__.columns}
        expected = {
            "id", "source_id", "source_group", "signal_type",
            "geo_region", "entity_ref", "content_hash", "normalised_data",
            "investigation_id", "collected_at", "created_at",
        }
        assert expected.issubset(columns)


class TestOsintResponseSchemas:
    """Verify response schema models."""

    def test_paginated_signals_response(self):
        from backend.schemas.osint_schemas import PaginatedSignalsResponse
        resp = PaginatedSignalsResponse(signals=[], limit=50, offset=0)
        assert resp.limit == 50

    def test_health_response(self):
        from backend.schemas.osint_schemas import OsintHealthResponse
        resp = OsintHealthResponse(
            feeds_online=6, feeds_total=6, signal_latency_sec=41,
            escalation_queue_depth=0, replay_workers_active=0,
        )
        assert resp.feeds_online == 6

    def test_summary_response(self):
        from backend.schemas.osint_schemas import SignalSummaryResponse
        resp = SignalSummaryResponse(
            total_signals=0, by_source_group={},
            counter_signals=0, certificate_candidates=0, convergence_cells=0,
        )
        assert resp.total_signals == 0
