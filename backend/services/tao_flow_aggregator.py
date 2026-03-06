"""
TAO Flow Aggregator — Windowed capital flow computation for timelines.

Computes total inflow over 24h and 7d windows by summing volume_usd
from TRADE and MIRROR_TRADE wing flaps. All trades (YES and NO side)
represent capital entering the market, so volume_usd is summed as-is.
Updates Timeline model fields.

Cycle-017: Policy Surface — Sprint 2
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import Timeline, WingFlap, WingFlapType
from backend.websockets.realtime_manager import manager as ws_manager


# Trade-type flap types that represent capital flow
TRADE_FLAP_TYPES = (WingFlapType.TRADE, WingFlapType.MIRROR_TRADE)

# Threshold for TAO flow alerts (absolute net inflow in 24h)
TAO_FLOW_ALERT_THRESHOLD = 1000.0


class TaoFlowAggregator:
    """Computes windowed capital flow metrics for timelines."""

    async def compute_for_timeline(
        self,
        session: AsyncSession,
        timeline_id: str,
        now: Optional[datetime] = None,
    ) -> Tuple[float, float]:
        """Compute net inflow for a single timeline.

        Returns (net_inflow_24h, net_inflow_7d).
        """
        if now is None:
            now = datetime.now(timezone.utc)

        cutoff_24h = now - timedelta(hours=24)
        cutoff_7d = now - timedelta(days=7)

        # Sum volume_usd directly — all trades (YES and NO side) are capital
        # entering the market. Producers store positive volume_usd for both sides.
        # 7d window (includes 24h data) — single query
        stmt_7d = (
            select(
                func.coalesce(
                    func.sum(WingFlap.volume_usd),
                    0.0,
                ),
            )
            .where(
                WingFlap.timeline_id == timeline_id,
                WingFlap.flap_type.in_(TRADE_FLAP_TYPES),
                WingFlap.timestamp >= cutoff_7d,
            )
        )
        result_7d = await session.execute(stmt_7d)
        net_7d = float(result_7d.scalar_one())

        # 24h window
        stmt_24h = (
            select(
                func.coalesce(
                    func.sum(WingFlap.volume_usd),
                    0.0,
                ),
            )
            .where(
                WingFlap.timeline_id == timeline_id,
                WingFlap.flap_type.in_(TRADE_FLAP_TYPES),
                WingFlap.timestamp >= cutoff_24h,
            )
        )
        result_24h = await session.execute(stmt_24h)
        net_24h = float(result_24h.scalar_one())

        return (net_24h, net_7d)

    async def compute_all(self, session: AsyncSession) -> int:
        """Compute and persist flow metrics for all active timelines.

        Returns the number of timelines updated.
        """
        now = datetime.now(timezone.utc)

        # Get active timeline IDs
        stmt = select(Timeline.id).where(Timeline.is_active.is_(True))
        result = await session.execute(stmt)
        timeline_ids = [row[0] for row in result.all()]

        updated = 0
        for tid in timeline_ids:
            net_24h, net_7d = await self.compute_for_timeline(session, tid, now)

            # Update timeline directly
            tl_stmt = select(Timeline).where(Timeline.id == tid)
            tl_result = await session.execute(tl_stmt)
            timeline = tl_result.scalar_one_or_none()
            if timeline:
                old_24h = timeline.net_inflow_24h or 0.0
                timeline.net_inflow_24h = net_24h
                timeline.net_inflow_7d = net_7d
                timeline.flow_updated_at = now
                updated += 1

                # Broadcast TAO flow alert when threshold crossed
                if abs(net_24h) >= TAO_FLOW_ALERT_THRESHOLD and abs(old_24h) < TAO_FLOW_ALERT_THRESHOLD:
                    try:
                        await ws_manager.broadcast_tao_flow_alert(tid, {
                            "net_inflow_24h": net_24h,
                            "net_inflow_7d": net_7d,
                            "threshold": TAO_FLOW_ALERT_THRESHOLD,
                        })
                    except Exception:
                        pass

        return updated
