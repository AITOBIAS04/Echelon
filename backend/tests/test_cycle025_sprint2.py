"""
Cycle 025 Sprint 2 Tests — Read Endpoints + Convergence Scorer
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from backend.database.models import OsintSignal
from backend.schemas.osint_schemas import (
    PaginatedSignalsResponse,
    OsintHealthResponse,
    SignalSummaryResponse,
)
from backend.services.convergence_scorer import ConvergenceScorer, ConvergenceCell


# ── Helpers ──────────────────────────────────────────────────


def _make_signal(
    source_id: str = "worldmonitor_cii",
    source_group: str = "alt_data_behavioural",
    signal_type: str = "country_instability_index",
    geo_region: str | None = "26.5,56.2",
    investigation_id: str | None = None,
    collected_at: datetime | None = None,
) -> OsintSignal:
    """Build a mock OsintSignal for testing."""
    return OsintSignal(
        id="sig-test-001",
        source_id=source_id,
        source_group=source_group,
        signal_type=signal_type,
        geo_region=geo_region,
        entity_ref=None,
        content_hash="a" * 64,
        normalised_data={"test": True},
        investigation_id=investigation_id,
        collected_at=collected_at or datetime.utcnow(),
        created_at=datetime.utcnow(),
    )


# ── GET /signals tests ──────────────────────────────────────


class TestGetSignalsEndpoint:
    """Test GET /api/v1/osint/signals route logic."""

    @pytest.mark.asyncio
    async def test_unfiltered_returns_signals(self):
        """Unfiltered query returns all signals."""
        from backend.api.osint_routes import get_signals

        now = datetime.utcnow()
        sig = _make_signal(collected_at=now)

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [sig]
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        resp = await get_signals(
            source_group=None,
            investigation_id=None,
            since=None,
            limit=50,
            offset=0,
            session=mock_session,
        )
        assert isinstance(resp, PaginatedSignalsResponse)
        assert len(resp.signals) == 1
        assert resp.limit == 50
        assert resp.offset == 0

    @pytest.mark.asyncio
    async def test_source_group_filter(self):
        """source_group filter narrows results."""
        from backend.api.osint_routes import get_signals

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        resp = await get_signals(
            source_group="market_data",
            investigation_id=None,
            since=None,
            limit=50,
            offset=0,
            session=mock_session,
        )
        assert isinstance(resp, PaginatedSignalsResponse)
        assert resp.signals == []
        # Verify execute was called (query was built with filter)
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_investigation_id_filter(self):
        """investigation_id filter narrows results."""
        from backend.api.osint_routes import get_signals

        sig = _make_signal(investigation_id="inv-001")

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [sig]
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        resp = await get_signals(
            source_group=None,
            investigation_id="inv-001",
            since=None,
            limit=50,
            offset=0,
            session=mock_session,
        )
        assert len(resp.signals) == 1


# ── GET /health tests ───────────────────────────────────────


class TestGetOsintHealthEndpoint:
    """Test GET /api/v1/osint/health route logic."""

    @pytest.mark.asyncio
    async def test_healthy_state(self):
        """Health endpoint returns counts when signals exist."""
        from backend.api.osint_routes import get_osint_health

        now = datetime.utcnow()
        mock_session = AsyncMock()

        # Call 1: feeds_online (distinct source_ids with recent signals)
        feeds_online_result = MagicMock()
        feeds_online_result.scalar.return_value = 3

        # Call 2: latest signal timestamp
        latest_result = MagicMock()
        latest_result.scalar_one_or_none.return_value = now - timedelta(seconds=41)

        # Call 3: escalation count
        escalation_result = MagicMock()
        escalation_result.scalar.return_value = 2

        mock_session.execute.side_effect = [
            feeds_online_result,
            latest_result,
            escalation_result,
        ]

        with patch("backend.api.osint_routes.os.path.exists", return_value=True), \
             patch("backend.api.osint_routes.RegistryLoader") as MockLoader:
            instance = MockLoader.return_value
            instance.sources = {f"src_{i}": MagicMock() for i in range(6)}

            resp = await get_osint_health(session=mock_session)

        assert isinstance(resp, OsintHealthResponse)
        assert resp.feeds_total == 6
        assert resp.feeds_online == 3
        assert resp.signal_latency_sec is not None
        assert resp.signal_latency_sec >= 41
        assert resp.escalation_queue_depth == 2

    @pytest.mark.asyncio
    async def test_degraded_state_no_recent_signals(self):
        """Health endpoint returns 0 online when no recent signals."""
        from backend.api.osint_routes import get_osint_health

        mock_session = AsyncMock()

        # feeds_online = 0
        feeds_online_result = MagicMock()
        feeds_online_result.scalar.return_value = 0

        # No latest signal
        latest_result = MagicMock()
        latest_result.scalar_one_or_none.return_value = None

        # 0 escalations
        escalation_result = MagicMock()
        escalation_result.scalar.return_value = 0

        mock_session.execute.side_effect = [
            feeds_online_result,
            latest_result,
            escalation_result,
        ]

        with patch("backend.api.osint_routes.os.path.exists", return_value=False):
            resp = await get_osint_health(session=mock_session)

        assert resp.feeds_online == 0
        assert resp.feeds_total == 0
        assert resp.signal_latency_sec is None
        assert resp.escalation_queue_depth == 0


# ── GET /signals/summary tests ──────────────────────────────


class TestGetSignalsSummaryEndpoint:
    """Test GET /api/v1/osint/signals/summary route logic."""

    @pytest.mark.asyncio
    async def test_empty_state(self):
        """Summary with no signals returns zeros."""
        from backend.api.osint_routes import get_signals_summary

        mock_session = AsyncMock()

        # total = 0
        total_result = MagicMock()
        total_result.scalar.return_value = 0

        # by_group = empty
        by_group_result = MagicMock()
        by_group_result.all.return_value = []

        # cert candidates = 0
        cert_result = MagicMock()
        cert_result.scalar.return_value = 0

        # recent signals for convergence scorer (empty)
        recent_signals_result = MagicMock()
        recent_signals_result.scalars.return_value.all.return_value = []

        mock_session.execute.side_effect = [
            total_result,
            by_group_result,
            cert_result,
            recent_signals_result,
        ]

        with patch("backend.api.osint_routes.os.path.exists", return_value=False):
            resp = await get_signals_summary(session=mock_session)

        assert isinstance(resp, SignalSummaryResponse)
        assert resp.total_signals == 0
        assert resp.by_source_group == {}
        assert resp.counter_signals == 0
        assert resp.certificate_candidates == 0
        assert resp.convergence_cells == 0

    @pytest.mark.asyncio
    async def test_populated_state(self):
        """Summary with data returns correct aggregates."""
        from backend.api.osint_routes import get_signals_summary

        mock_session = AsyncMock()

        # total = 15
        total_result = MagicMock()
        total_result.scalar.return_value = 15

        # by_group
        by_group_result = MagicMock()
        by_group_result.all.return_value = [
            ("alt_data_behavioural", 8),
            ("market_data", 5),
            ("maritime_ais", 2),
        ]

        # counter_signals from registry
        counter_result = MagicMock()
        counter_result.scalar.return_value = 3

        # cert candidates = 1
        cert_result = MagicMock()
        cert_result.scalar.return_value = 1

        # recent signals for convergence scorer (empty — scorer tested separately)
        recent_signals_result = MagicMock()
        recent_signals_result.scalars.return_value.all.return_value = []

        mock_session.execute.side_effect = [
            total_result,
            by_group_result,
            counter_result,
            cert_result,
            recent_signals_result,
        ]

        mock_source_counter = MagicMock()
        mock_source_counter.resolution_role = "counter_signal"
        mock_source_primary = MagicMock()
        mock_source_primary.resolution_role = "primary_evidence"

        with patch("backend.api.osint_routes.os.path.exists", return_value=True), \
             patch("backend.api.osint_routes.RegistryLoader") as MockLoader:
            instance = MockLoader.return_value
            instance.sources = {
                "counter_src": mock_source_counter,
                "primary_src": mock_source_primary,
            }

            resp = await get_signals_summary(session=mock_session)

        assert resp.total_signals == 15
        assert resp.by_source_group == {
            "alt_data_behavioural": 8,
            "market_data": 5,
            "maritime_ais": 2,
        }
        assert resp.counter_signals == 3
        assert resp.certificate_candidates == 1


# ── ConvergenceScorer tests ─────────────────────────────────


class TestConvergenceScorer:
    """Test the ConvergenceScorer service."""

    def test_single_domain_no_cell(self):
        """Single domain cluster does not emit a convergence cell."""
        now = datetime.utcnow()
        signals = [
            _make_signal(source_group="alt_data_behavioural", geo_region="26.5,56.2", collected_at=now),
            _make_signal(source_group="alt_data_behavioural", geo_region="26.5,56.2", collected_at=now),
        ]
        scorer = ConvergenceScorer(time_window_minutes=60)
        cells = scorer.score(signals)
        assert cells == []

    def test_two_domains_emits_cell(self):
        """Two domain groups in same geo/time emit a convergence cell."""
        now = datetime.utcnow()
        signals = [
            _make_signal(source_group="alt_data_behavioural", geo_region="26.5,56.2", collected_at=now),
            _make_signal(source_group="market_data", geo_region="26.5,56.2", collected_at=now),
        ]
        scorer = ConvergenceScorer(time_window_minutes=60)
        cells = scorer.score(signals)
        assert len(cells) == 1
        assert cells[0].convergence_score > 0
        assert len(cells[0].domains) == 2
        assert "alt_data_behavioural" in cells[0].domains
        assert "market_data" in cells[0].domains
        assert cells[0].geo_region == "26.5,56.2"

    def test_non_geocoded_signals_excluded(self):
        """Signals without geo_region must not form false convergence cells."""
        now = datetime.utcnow()
        signals = [
            _make_signal(source_group="alt_data_behavioural", geo_region=None, collected_at=now),
            _make_signal(source_group="market_data", geo_region=None, collected_at=now),
            _make_signal(source_group="maritime_ais", geo_region=None, collected_at=now),
        ]
        scorer = ConvergenceScorer(time_window_minutes=60)
        cells = scorer.score(signals)
        assert cells == []

    def test_empty_input(self):
        """Empty signal list returns no cells."""
        scorer = ConvergenceScorer(time_window_minutes=60)
        cells = scorer.score([])
        assert cells == []
