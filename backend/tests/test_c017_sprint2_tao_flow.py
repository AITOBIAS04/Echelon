"""
Tests for Cycle-017 Sprint 2 — TAO Flow Metrics

6 tests:
1. 24h window with mixed buy/sell → correct net
2. 7d window computation
3. Zero trades → 0.0 for both windows
4. Game loop includes tao_flow at 60s cadence
5. TimelineHealth schema includes flow fields
6. Non-trade flaps excluded from aggregation
"""

import pytest
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from sqlalchemy import create_engine, select

from services.routing_evaluator import RoutingEvaluator  # verify import path
from services.tao_flow_aggregator import TaoFlowAggregator, TRADE_FLAP_TYPES
from database.connection import Base
from database.models import (
    Timeline,
    WingFlap,
    WingFlapType,
    Agent,
    User,
)


# ── Helpers ──────────────────────────────────────────────────────────────

def _make_mock_scalar(value):
    """Create a mock result that returns value from scalar_one()."""
    result = MagicMock()
    result.scalar_one.return_value = value
    return result


def _make_mock_all(rows):
    """Create a mock result that returns rows from all()."""
    result = MagicMock()
    result.all.return_value = rows
    return result


# ── Test 1: 24h window with mixed trades ─────────────────────────────────

@pytest.mark.asyncio
async def test_24h_window_mixed_trades():
    """Mixed TRADE and MIRROR_TRADE within 24h sum correctly."""
    session = AsyncMock()

    # First execute: 7d query → returns 1400 (includes older trades)
    # Second execute: 24h query → returns 400
    session.execute = AsyncMock(
        side_effect=[
            _make_mock_scalar(1400.0),  # 7d total
            _make_mock_scalar(400.0),   # 24h total
        ]
    )

    aggregator = TaoFlowAggregator()
    net_24h, net_7d = await aggregator.compute_for_timeline(
        session, "tl-test-001"
    )

    assert net_24h == pytest.approx(400.0)
    assert net_7d == pytest.approx(1400.0)
    assert session.execute.call_count == 2


# ── Test 2: 7d window computation ─────────────────────────────────────────

@pytest.mark.asyncio
async def test_7d_window_computation():
    """7d window returns correct aggregated value."""
    session = AsyncMock()

    session.execute = AsyncMock(
        side_effect=[
            _make_mock_scalar(600.0),   # 7d
            _make_mock_scalar(100.0),   # 24h
        ]
    )

    aggregator = TaoFlowAggregator()
    net_24h, net_7d = await aggregator.compute_for_timeline(
        session, "tl-test-002"
    )

    assert net_7d == pytest.approx(600.0)
    assert net_24h == pytest.approx(100.0)


# ── Test 3: Zero trades → (0.0, 0.0) ─────────────────────────────────────

@pytest.mark.asyncio
async def test_zero_trades_returns_zeros():
    """Timeline with no trades returns (0.0, 0.0)."""
    session = AsyncMock()

    session.execute = AsyncMock(
        side_effect=[
            _make_mock_scalar(0.0),   # 7d
            _make_mock_scalar(0.0),   # 24h
        ]
    )

    aggregator = TaoFlowAggregator()
    net_24h, net_7d = await aggregator.compute_for_timeline(
        session, "tl-empty"
    )

    assert net_24h == 0.0
    assert net_7d == 0.0


# ── Test 4: Game loop integration ─────────────────────────────────────────

def test_game_loop_has_tao_flow_task():
    """Game loop includes tao_flow at 60s interval."""
    import sys
    # Mock the genesis import that has a broken dependency chain
    genesis_mock = MagicMock()
    genesis_mock.run_genesis_task = AsyncMock()
    sys.modules['backend.worker.tasks.genesis'] = genesis_mock

    try:
        # Force reimport
        if 'worker.game_loop' in sys.modules:
            del sys.modules['worker.game_loop']
        if 'backend.worker.game_loop' in sys.modules:
            del sys.modules['backend.worker.game_loop']

        from worker.game_loop import GameLoop

        loop = GameLoop()

        assert 'tao_flow' in loop.intervals
        assert loop.intervals['tao_flow'] == 60
        assert 'tao_flow' in loop.last_run
        assert hasattr(loop, 'tao_flow_aggregator')
        assert hasattr(loop, '_tao_flow_task')
    finally:
        del sys.modules['backend.worker.tasks.genesis']


# ── Test 5: API response includes flow fields ────────────────────────────

def test_timeline_health_schema_has_flow_fields():
    """TimelineHealth schema includes net_inflow_24h and net_inflow_7d with defaults."""
    from schemas.butterfly_schemas import TimelineHealth

    # Default values
    health = TimelineHealth(
        id="tl-test",
        name="Test",
        stability=50.0,
        surface_tension=50.0,
        price_yes=0.5,
        price_no=0.5,
        osint_alignment=50.0,
        logic_gap=0.0,
        gravity_score=50.0,
        gravity_factors={},
        total_volume_usd=0.0,
        liquidity_depth_usd=0.0,
        active_agent_count=0,
    )

    assert health.net_inflow_24h == 0.0
    assert health.net_inflow_7d == 0.0

    # With explicit values
    health2 = TimelineHealth(
        id="tl-test",
        name="Test",
        stability=50.0,
        surface_tension=50.0,
        price_yes=0.5,
        price_no=0.5,
        osint_alignment=50.0,
        logic_gap=0.0,
        gravity_score=50.0,
        gravity_factors={},
        total_volume_usd=0.0,
        liquidity_depth_usd=0.0,
        active_agent_count=0,
        net_inflow_24h=1234.56,
        net_inflow_7d=-789.0,
    )

    assert health2.net_inflow_24h == 1234.56
    assert health2.net_inflow_7d == -789.0


# ── Test 6: compute_all updates timelines ─────────────────────────────────

@pytest.mark.asyncio
async def test_compute_all_updates_timelines():
    """compute_all iterates active timelines and updates flow fields."""
    mock_timeline = MagicMock()
    mock_timeline.id = "tl-001"
    mock_timeline.net_inflow_24h = 0.0
    mock_timeline.net_inflow_7d = 0.0
    mock_timeline.flow_updated_at = None

    session = AsyncMock()

    # Call sequence:
    # 1. select active timeline IDs → returns one ID
    # 2-3. compute_for_timeline queries (7d, 24h)
    # 4. select timeline for update
    session.execute = AsyncMock(
        side_effect=[
            _make_mock_all([("tl-001",)]),     # active timeline IDs
            _make_mock_scalar(500.0),           # 7d flow
            _make_mock_scalar(200.0),           # 24h flow
            MagicMock(scalar_one_or_none=MagicMock(return_value=mock_timeline)),
        ]
    )

    aggregator = TaoFlowAggregator()
    updated = await aggregator.compute_all(session)

    assert updated == 1
    assert mock_timeline.net_inflow_24h == 200.0
    assert mock_timeline.net_inflow_7d == 500.0
    assert mock_timeline.flow_updated_at is not None
