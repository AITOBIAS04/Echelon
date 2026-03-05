"""Best-effort WebSocket broadcast helpers for game loop tasks.

Wraps ConnectionManager calls in try/except so broadcast failures
never crash the game loop.  All functions are async and return None.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from backend.database.models import WingFlap

logger = logging.getLogger("echelon.ws_broadcast")


async def broadcast_flap(flap: "WingFlap") -> None:
    """Broadcast wing flap event via WebSocket. Best-effort, never raises."""
    try:
        from backend.websockets.realtime_manager import manager

        await manager.broadcast_wing_flap({
            "id": flap.id,
            "timeline_id": flap.timeline_id,
            "agent_id": flap.agent_id,
            "flap_type": flap.flap_type.value if hasattr(flap.flap_type, "value") else str(flap.flap_type),
            "action": flap.action,
            "stability_delta": flap.stability_delta,
            "volume_usd": flap.volume_usd,
            "timeline_stability": flap.timeline_stability,
            "timeline_price": flap.timeline_price,
        })
    except Exception as exc:
        logger.debug("WS broadcast_flap failed: %s", exc)


async def broadcast_paradox_spawn(
    paradox_id: str,
    timeline_id: str,
    severity: str,
    logic_gap: float,
    detonation_time,
) -> None:
    """Broadcast paradox spawn event. Best-effort, never raises."""
    try:
        from backend.websockets.realtime_manager import manager

        await manager.broadcast_paradox_spawn({
            "id": paradox_id,
            "timeline_id": timeline_id,
            "severity_class": severity,
            "logic_gap": logic_gap,
            "detonation_time": detonation_time.isoformat() if detonation_time else None,
        })
    except Exception as exc:
        logger.debug("WS broadcast_paradox_spawn failed: %s", exc)


async def broadcast_detonation_event(
    paradox_id: str,
    timeline_id: str,
) -> None:
    """Broadcast paradox detonation event. Best-effort, never raises."""
    try:
        from backend.websockets.realtime_manager import manager

        await manager.broadcast_detonation({
            "paradox_id": paradox_id,
            "timeline_id": timeline_id,
        })
    except Exception as exc:
        logger.debug("WS broadcast_detonation failed: %s", exc)
