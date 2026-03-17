"""
Cycle 025 Sprint 1 Tests — POST Endpoints + Signal Persistence
"""
import hashlib
import json
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from backend.osint.models.evidence import (
    CollectionResult, EvidenceBundle, GeoPoint,
    HTTPTranscriptReceipt, NormalisedEvent, NormalisedMeasure,
    MeasureType, WMDomain,
)
from backend.services.signal_persistence import persist_signal


def _make_collection_result(domain: WMDomain, success: bool = True) -> CollectionResult:
    """Build a mock CollectionResult for testing."""
    now = datetime.utcnow()
    source_ids = {
        WMDomain.INTELLIGENCE: "worldmonitor_cii",
        WMDomain.MARKET: "worldmonitor_finance",
        WMDomain.MARITIME: "worldmonitor_maritime",
    }
    source_groups = {
        WMDomain.INTELLIGENCE: "alt_data_behavioural",
        WMDomain.MARKET: "market_data",
        WMDomain.MARITIME: "maritime_ais",
    }
    measure_types = {
        WMDomain.INTELLIGENCE: MeasureType.COUNTRY_INSTABILITY_INDEX,
        WMDomain.MARKET: MeasureType.SECTOR_RISK_SCORE,
        WMDomain.MARITIME: MeasureType.VESSEL_DENSITY_ANOMALY,
    }

    if not success:
        return CollectionResult(
            source_id=source_ids[domain],
            bundle=None,
            raw_payload=b"",
            fetch_duration_ms=100.0,
            success=False,
            error="Connection refused",
            retrieved_at=now,
        )

    geo = GeoPoint(lat=26.5, lon=56.2)
    measure = NormalisedMeasure(
        type=measure_types[domain], value=0.78, unit="0_1",
        metadata={"forecast_score": 0.85} if domain == WMDomain.INTELLIGENCE else None,
    )
    event = NormalisedEvent(
        event_id=f"evt_{source_ids[domain]}_{int(now.timestamp())}",
        geo=geo, measure=measure, confidence=0.8, timestamp=now,
    )
    receipt = HTTPTranscriptReceipt(
        timestamp=now, request_parameters={},
        source_id=source_ids[domain], source_version="v0.1.0",
        http_status=200, content_hash="a" * 64,
    )
    bundle = EvidenceBundle(
        bundle_id=f"eb_{source_ids[domain]}_{int(now.timestamp())}",
        source_id=source_ids[domain],
        source_group=source_groups[domain],
        resolution_role="primary_evidence",
        evidence_timestamp=now,
        raw_payload_hash="a" * 64,
        receipt=receipt,
        normalised_event=event,
    )
    return CollectionResult(
        source_id=source_ids[domain],
        bundle=bundle,
        raw_payload=json.dumps({"test": True}).encode(),
        fetch_duration_ms=150.0,
        success=True,
        error=None,
        retrieved_at=now,
    )


class TestPersistSignal:
    """Test the shared persist_signal helper."""

    @pytest.mark.asyncio
    async def test_persist_creates_signal_row(self):
        """persist_signal creates an OsintSignal when given a successful result."""
        from unittest.mock import MagicMock
        result = _make_collection_result(WMDomain.INTELLIGENCE)
        mock_session = AsyncMock()
        # execute() is awaited, returns a sync result object
        mock_execute_result = MagicMock()
        mock_execute_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_execute_result

        signal = await persist_signal(
            session=mock_session,
            result=result,
            source_id="worldmonitor_cii",
            source_group="alt_data_behavioural",
        )
        assert signal is not None
        assert signal.source_id == "worldmonitor_cii"
        assert signal.source_group == "alt_data_behavioural"
        assert signal.signal_type == "country_instability_index"
        mock_session.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_persist_returns_none_for_failed_result(self):
        """persist_signal returns None when result has no bundle."""
        result = _make_collection_result(WMDomain.INTELLIGENCE, success=False)
        mock_session = AsyncMock()
        signal = await persist_signal(
            session=mock_session,
            result=result,
            source_id="worldmonitor_cii",
            source_group="alt_data_behavioural",
        )
        assert signal is None

    @pytest.mark.asyncio
    async def test_persist_deduplicates_on_content_hash(self):
        """persist_signal returns None when content_hash already exists."""
        from unittest.mock import MagicMock
        result = _make_collection_result(WMDomain.INTELLIGENCE)
        mock_session = AsyncMock()
        mock_execute_result = MagicMock()
        mock_execute_result.scalar_one_or_none.return_value = "existing-id"
        mock_session.execute.return_value = mock_execute_result

        signal = await persist_signal(
            session=mock_session,
            result=result,
            source_id="worldmonitor_cii",
            source_group="alt_data_behavioural",
        )
        assert signal is None
        mock_session.add.assert_not_called()


class TestPostCIIEndpoint:
    """Test POST /intelligence/cii route logic."""

    @pytest.mark.asyncio
    async def test_cii_success_returns_bundle(self):
        """Successful collection returns CIIResponse with bundle."""
        result = _make_collection_result(WMDomain.INTELLIGENCE)
        with patch(
            "backend.api.world_monitor_routes.WorldMonitorCollector"
        ) as MockCollector:
            instance = MockCollector.return_value
            instance.fetch = AsyncMock(return_value=result)
            instance.source_id.return_value = "worldmonitor_cii"

            from backend.api.world_monitor_routes import post_cii
            from backend.schemas.worldmonitor_api_contract import CIIRequest

            body = CIIRequest(
                country_code="IRN",
                evaluation_window_start=datetime.utcnow(),
                evaluation_window_end=datetime.utcnow(),
            )
            mock_db = AsyncMock()
            mock_exec = AsyncMock()
            mock_exec.scalar_one_or_none.return_value = None
            mock_db.execute.return_value = mock_exec

            resp = await post_cii(body=body, theatre_id="t-001", db=mock_db)
            assert resp.domain == "intelligence"
            assert resp.bundle.source_id == "worldmonitor_cii"
            assert resp.forecast_score == 0.85

    @pytest.mark.asyncio
    async def test_cii_failure_returns_502(self):
        """Collector failure raises 502."""
        result = _make_collection_result(WMDomain.INTELLIGENCE, success=False)
        with patch(
            "backend.api.world_monitor_routes.WorldMonitorCollector"
        ) as MockCollector:
            instance = MockCollector.return_value
            instance.fetch = AsyncMock(return_value=result)

            from backend.api.world_monitor_routes import post_cii
            from backend.schemas.worldmonitor_api_contract import CIIRequest
            from fastapi import HTTPException

            body = CIIRequest(
                country_code="IRN",
                evaluation_window_start=datetime.utcnow(),
                evaluation_window_end=datetime.utcnow(),
            )
            mock_db = AsyncMock()
            with pytest.raises(HTTPException) as exc_info:
                await post_cii(body=body, theatre_id="t-001", db=mock_db)
            assert exc_info.value.status_code == 502


class TestPostMarketEndpoint:
    """Test POST /market/snapshot route logic."""

    @pytest.mark.asyncio
    async def test_market_success_returns_bundle(self):
        result = _make_collection_result(WMDomain.MARKET)
        with patch(
            "backend.api.world_monitor_routes.WorldMonitorCollector"
        ) as MockCollector:
            instance = MockCollector.return_value
            instance.fetch = AsyncMock(return_value=result)
            instance.source_id.return_value = "worldmonitor_finance"

            from backend.api.world_monitor_routes import post_market_snapshot
            from backend.schemas.worldmonitor_api_contract import MarketSnapshotRequest

            body = MarketSnapshotRequest(
                asset_class="fx", symbol="USDIRR",
                evaluation_window_start=datetime.utcnow(),
                evaluation_window_end=datetime.utcnow(),
            )
            mock_db = AsyncMock()
            mock_exec = AsyncMock()
            mock_exec.scalar_one_or_none.return_value = None
            mock_db.execute.return_value = mock_exec

            resp = await post_market_snapshot(body=body, theatre_id="t-001", db=mock_db)
            assert resp.domain == "market"
            assert resp.bundle.source_id == "worldmonitor_finance"


class TestPostMaritimeEndpoint:
    """Test POST /maritime/anomaly route logic."""

    @pytest.mark.asyncio
    async def test_maritime_success_returns_bundle(self):
        result = _make_collection_result(WMDomain.MARITIME)
        with patch(
            "backend.api.world_monitor_routes.WorldMonitorCollector"
        ) as MockCollector:
            instance = MockCollector.return_value
            instance.fetch = AsyncMock(return_value=result)
            instance.source_id.return_value = "worldmonitor_maritime"

            from backend.api.world_monitor_routes import post_maritime_anomaly
            from backend.schemas.worldmonitor_api_contract import MaritimeAnomalyRequest, GeoPoint

            body = MaritimeAnomalyRequest(
                geo=GeoPoint(lat=26.5, lon=56.2),
                evaluation_window_start=datetime.utcnow(),
                evaluation_window_end=datetime.utcnow(),
            )
            mock_db = AsyncMock()
            mock_exec = AsyncMock()
            mock_exec.scalar_one_or_none.return_value = None
            mock_db.execute.return_value = mock_exec

            resp = await post_maritime_anomaly(body=body, theatre_id="t-001", db=mock_db)
            assert resp.domain == "maritime"
            assert resp.bundle.source_id == "worldmonitor_maritime"

    @pytest.mark.asyncio
    async def test_maritime_failure_returns_502(self):
        result = _make_collection_result(WMDomain.MARITIME, success=False)
        with patch(
            "backend.api.world_monitor_routes.WorldMonitorCollector"
        ) as MockCollector:
            instance = MockCollector.return_value
            instance.fetch = AsyncMock(return_value=result)

            from backend.api.world_monitor_routes import post_maritime_anomaly
            from backend.schemas.worldmonitor_api_contract import MaritimeAnomalyRequest, GeoPoint
            from fastapi import HTTPException

            body = MaritimeAnomalyRequest(
                geo=GeoPoint(lat=26.5, lon=56.2),
                evaluation_window_start=datetime.utcnow(),
                evaluation_window_end=datetime.utcnow(),
            )
            mock_db = AsyncMock()
            with pytest.raises(HTTPException) as exc_info:
                await post_maritime_anomaly(body=body, theatre_id="t-001", db=mock_db)
            assert exc_info.value.status_code == 502
