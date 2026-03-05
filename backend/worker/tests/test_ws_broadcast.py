"""Tests for _ws_broadcast — best-effort WebSocket broadcast helpers.

Validates:
- broadcast_flap serialises WingFlap model and calls manager
- broadcast_paradox_spawn calls manager with correct payload
- broadcast_detonation_event calls manager with correct payload
- All functions swallow exceptions silently
"""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, patch, MagicMock


@pytest.fixture
def mock_manager():
    """Create a mock ConnectionManager."""
    mgr = MagicMock()
    mgr.broadcast_wing_flap = AsyncMock()
    mgr.broadcast_paradox_spawn = AsyncMock()
    mgr.broadcast_detonation = AsyncMock()
    return mgr


def _make_flap():
    """Create a minimal WingFlap-like object."""
    flap = MagicMock()
    flap.id = "FLAP_001"
    flap.timeline_id = "TL_001"
    flap.agent_id = "AGENT_001"
    flap.flap_type = MagicMock(value="TRADE")
    flap.action = "Test trade"
    flap.stability_delta = 0.01
    flap.volume_usd = 1000.0
    flap.timeline_stability = 0.75
    flap.timeline_price = 0.65
    return flap


class TestBroadcastFlap:

    @pytest.mark.asyncio
    async def test_calls_manager(self, mock_manager):
        from backend.worker.tasks._ws_broadcast import broadcast_flap

        flap = _make_flap()
        with patch("backend.worker.tasks._ws_broadcast.manager", mock_manager, create=True):
            # Patch the lazy import
            with patch(
                "backend.websockets.realtime_manager.manager",
                mock_manager,
            ):
                await broadcast_flap(flap)

        mock_manager.broadcast_wing_flap.assert_called_once()
        payload = mock_manager.broadcast_wing_flap.call_args[0][0]
        assert payload["timeline_id"] == "TL_001"
        assert payload["flap_type"] == "TRADE"

    @pytest.mark.asyncio
    async def test_swallows_exceptions(self):
        """broadcast_flap should never raise."""
        from backend.worker.tasks._ws_broadcast import broadcast_flap

        flap = _make_flap()
        with patch(
            "backend.websockets.realtime_manager.manager",
            side_effect=RuntimeError("no connection"),
        ):
            # Should not raise
            await broadcast_flap(flap)


class TestBroadcastParadoxSpawn:

    @pytest.mark.asyncio
    async def test_calls_manager(self, mock_manager):
        from backend.worker.tasks._ws_broadcast import broadcast_paradox_spawn
        from datetime import datetime

        with patch(
            "backend.websockets.realtime_manager.manager",
            mock_manager,
        ):
            await broadcast_paradox_spawn(
                paradox_id="PARADOX_001",
                timeline_id="TL_001",
                severity="CLASS_2_SEVERE",
                logic_gap=0.45,
                detonation_time=datetime(2026, 3, 5, 12, 0),
            )

        mock_manager.broadcast_paradox_spawn.assert_called_once()
        payload = mock_manager.broadcast_paradox_spawn.call_args[0][0]
        assert payload["id"] == "PARADOX_001"
        assert payload["severity_class"] == "CLASS_2_SEVERE"


class TestBroadcastDetonation:

    @pytest.mark.asyncio
    async def test_calls_manager(self, mock_manager):
        from backend.worker.tasks._ws_broadcast import broadcast_detonation_event

        with patch(
            "backend.websockets.realtime_manager.manager",
            mock_manager,
        ):
            await broadcast_detonation_event(
                paradox_id="PARADOX_001",
                timeline_id="TL_001",
            )

        mock_manager.broadcast_detonation.assert_called_once()
        payload = mock_manager.broadcast_detonation.call_args[0][0]
        assert payload["paradox_id"] == "PARADOX_001"
        assert payload["timeline_id"] == "TL_001"
