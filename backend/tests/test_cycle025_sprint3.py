"""
Cycle 025 Sprint 3 Tests — Integration + Regression
"""
import ast
import os
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from backend.database.models import OsintSignal
from backend.services.convergence_scorer import ConvergenceScorer


# ── Sprint 3 Task 1: Path 2 regression ──────────────────────


class TestPath2Regression:
    """Verify Path 2 (synthetic SignalDetector / OSINTRegistry) is untouched."""

    def test_live_response_model_unchanged(self):
        """WorldMonitorLiveResponse still has expected shape."""
        from backend.api.world_monitor_routes import WorldMonitorLiveResponse
        fields = set(WorldMonitorLiveResponse.model_fields.keys())
        expected = {
            "updated_at", "summary", "category_counts", "severity_counts",
            "source_counts", "signals", "convergence_cells", "missions",
            "intel", "live_feed",
        }
        assert expected.issubset(fields), f"Missing fields: {expected - fields}"

    def test_no_path2_imports_in_cycle025_files(self):
        """No Cycle 025 file imports from signal_detector or osint_registry."""
        cycle025_files = [
            "backend/api/osint_routes.py",
            "backend/services/signal_persistence.py",
            "backend/services/convergence_scorer.py",
            "backend/schemas/osint_schemas.py",
        ]
        forbidden = {"signal_detector", "osint_registry"}

        for filepath in cycle025_files:
            full_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                filepath,
            )
            if not os.path.exists(full_path):
                continue
            with open(full_path, "r") as f:
                tree = ast.parse(f.read(), filename=filepath)
            for node in ast.walk(tree):
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    module = ""
                    if isinstance(node, ast.ImportFrom) and node.module:
                        module = node.module
                    elif isinstance(node, ast.Import):
                        module = ".".join(a.name for a in node.names)
                    for name in forbidden:
                        assert name not in module, (
                            f"{filepath} imports from '{module}' which contains '{name}'"
                        )


# ── Sprint 3 Task 2: Integration sweep ──────────────────────


class TestIntegration:
    """End-to-end integration: POST → persist → GET → convergence."""

    @pytest.mark.asyncio
    async def test_post_persist_then_get_retrieves(self):
        """POST endpoint persists signals that GET signals can retrieve."""
        from backend.services.signal_persistence import persist_signal
        from backend.api.osint_routes import get_signals
        from backend.osint.models.evidence import (
            CollectionResult, EvidenceBundle, GeoPoint,
            HTTPTranscriptReceipt, NormalisedEvent, NormalisedMeasure,
            MeasureType, WMDomain,
        )

        now = datetime.utcnow()

        # Build a collection result
        geo = GeoPoint(lat=26.5, lon=56.2)
        measure = NormalisedMeasure(
            type=MeasureType.COUNTRY_INSTABILITY_INDEX, value=0.78, unit="0_1",
        )
        event = NormalisedEvent(
            event_id="evt_integration_test",
            geo=geo, measure=measure, confidence=0.8, timestamp=now,
        )
        receipt = HTTPTranscriptReceipt(
            timestamp=now, request_parameters={},
            source_id="worldmonitor_cii", source_version="v0.1.0",
            http_status=200, content_hash="b" * 64,
        )
        bundle = EvidenceBundle(
            bundle_id="eb_integration_test",
            source_id="worldmonitor_cii",
            source_group="alt_data_behavioural",
            resolution_role="primary_evidence",
            evidence_timestamp=now,
            raw_payload_hash="b" * 64,
            receipt=receipt,
            normalised_event=event,
        )
        result = CollectionResult(
            source_id="worldmonitor_cii",
            bundle=bundle,
            raw_payload=b"{}",
            fetch_duration_ms=100.0,
            success=True,
            error=None,
            retrieved_at=now,
        )

        # Mock session for persist
        mock_session = AsyncMock()
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

        # Mock GET session that returns the persisted signal
        mock_get_session = AsyncMock()
        mock_get_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [signal]
        mock_get_result.scalars.return_value = mock_scalars
        mock_get_session.execute.return_value = mock_get_result

        resp = await get_signals(
            source_group="alt_data_behavioural",
            investigation_id=None,
            since=None,
            limit=50,
            offset=0,
            session=mock_get_session,
        )
        assert len(resp.signals) == 1
        assert resp.signals[0].source_id == "worldmonitor_cii"

    @pytest.mark.asyncio
    async def test_convergence_scorer_processes_persisted_signals(self):
        """ConvergenceScorer correctly processes signals from different domains."""
        from backend.services.signal_persistence import persist_signal
        from backend.osint.models.evidence import (
            CollectionResult, EvidenceBundle, GeoPoint,
            HTTPTranscriptReceipt, NormalisedEvent, NormalisedMeasure,
            MeasureType, WMDomain,
        )

        now = datetime.utcnow()

        def _build_result(domain, source_id, source_group, measure_type):
            geo = GeoPoint(lat=26.5, lon=56.2)
            measure = NormalisedMeasure(type=measure_type, value=0.78, unit="0_1")
            event = NormalisedEvent(
                event_id=f"evt_{source_id}", geo=geo, measure=measure,
                confidence=0.8, timestamp=now,
            )
            receipt = HTTPTranscriptReceipt(
                timestamp=now, request_parameters={},
                source_id=source_id, source_version="v0.1.0",
                http_status=200, content_hash="c" * 64,
            )
            bundle = EvidenceBundle(
                bundle_id=f"eb_{source_id}",
                source_id=source_id,
                source_group=source_group,
                resolution_role="primary_evidence",
                evidence_timestamp=now,
                raw_payload_hash="c" * 64,
                receipt=receipt,
                normalised_event=event,
            )
            return CollectionResult(
                source_id=source_id, bundle=bundle, raw_payload=b"{}",
                fetch_duration_ms=100.0, success=True, error=None, retrieved_at=now,
            )

        results = [
            _build_result(WMDomain.INTELLIGENCE, "worldmonitor_cii", "alt_data_behavioural", MeasureType.COUNTRY_INSTABILITY_INDEX),
            _build_result(WMDomain.MARKET, "worldmonitor_finance", "market_data", MeasureType.SECTOR_RISK_SCORE),
        ]

        # Persist both signals
        signals = []
        for r in results:
            mock_session = AsyncMock()
            mock_exec = MagicMock()
            mock_exec.scalar_one_or_none.return_value = None
            mock_session.execute.return_value = mock_exec

            sig = await persist_signal(
                session=mock_session,
                result=r,
                source_id=r.source_id,
                source_group=r.bundle.source_group,
            )
            assert sig is not None
            signals.append(sig)

        # Score convergence
        scorer = ConvergenceScorer(time_window_minutes=60)
        cells = scorer.score(signals)
        assert len(cells) == 1
        assert len(cells[0].domains) == 2
        assert cells[0].convergence_score > 0
