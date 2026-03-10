"""
Entropy Task - Timeline Stability Decay

Every tick, all timelines lose stability based on:
- Base decay rate (1-5% per hour depending on activity)
- Paradox multiplier (if breach active)
- Agent shield effects (can slow decay)

This creates pressure for users to actively stabilise timelines.
"""

import logging
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
import uuid

from backend.database.models import Timeline, WingFlap, WingFlapType, FlapDirection
from backend.worker.tasks._system_entity import ensure_system_entities
from backend.worker.tasks._ws_broadcast import broadcast_flap

logger = logging.getLogger('echelon.entropy')


class EntropyTask:
    """Applies entropy (stability decay) to all active timelines."""
    
    # Base decay per hour (0-1 scale: 0.01 = 1% per hour)
    BASE_DECAY_PER_HOUR = 0.01

    # Minimum stability before timeline becomes critical (0-1 scale)
    CRITICAL_THRESHOLD = 0.20

    # Maximum decay rate per hour (0-1 scale: 0.10 = 10% per hour)
    MAX_DECAY_RATE = 0.10
    
    async def tick(self, session: AsyncSession) -> str:
        """
        Apply entropy decay to all active non-anchor timelines.

        Anchor timelines (Polymarket reality feeds) are skipped — reality
        doesn't get less reliable over time.

        Returns a summary string for logging.
        """
        # Get all active timelines (skip anchors — they don't decay)
        result = await session.execute(
            select(Timeline).where(
                Timeline.is_active == True,
                Timeline.is_anchor == False,
            )
        )
        timelines = result.scalars().all()

        if not timelines:
            return "No active non-anchor timelines"

        # Ensure SYSTEM entities exist once per tick (shared helper)
        await ensure_system_entities(session)

        decayed_count = 0
        critical_count = 0
        total_decay = 0.0

        for timeline in timelines:
            # Calculate decay for this timeline
            decay = self._calculate_decay(timeline)

            # Apply decay (0-1 scale)
            old_stability = timeline.stability
            new_stability = max(0.0, timeline.stability - decay)

            # Update timeline
            await session.execute(
                update(Timeline)
                .where(Timeline.id == timeline.id)
                .values(stability=new_stability)
            )

            # Track stats
            total_decay += decay
            decayed_count += 1

            if new_stability < self.CRITICAL_THRESHOLD:
                critical_count += 1

            # Log significant decays (> 0.5% on 0-1 scale = 0.005)
            if decay > 0.005:
                logger.debug(
                    f"  {timeline.id}: {old_stability:.3f} -> {new_stability:.3f} "
                    f"(decay: {decay:.4f})"
                )

            # Create wing flap for entropy event (if decay is significant)
            if decay > 0.001:
                flap_id = f"ENTROPY_{timeline.id}_{uuid.uuid4().hex[:8]}"
                flap_timestamp = datetime.utcnow()
                entropy_flap = WingFlap(
                    id=flap_id,
                    timeline_id=timeline.id,
                    agent_id="SYSTEM",
                    flap_type=WingFlapType.ENTROPY,
                    action=f"Entropy decay: -{decay:.4f} stability",
                    stability_delta=-decay,
                    direction=FlapDirection.DESTABILISE.value,
                    volume_usd=0.0,
                    timeline_stability=new_stability,
                    timeline_price=timeline.price_yes,
                    timestamp=flap_timestamp,
                )
                session.add(entropy_flap)
                await broadcast_flap(entropy_flap)

        avg_decay = total_decay / decayed_count if decayed_count > 0 else 0

        return (
            f"Decayed {decayed_count} timelines "
            f"(avg: {avg_decay:.4f}, critical: {critical_count})"
        )
    
    def _calculate_decay(self, timeline: Timeline) -> float:
        """
        Calculate decay rate for a timeline (0-1 scale, per-minute).

        Pattern A: Paradox task writes ``decay_multiplier`` only.
        This method reads the base ``decay_rate_per_hour`` and applies
        ``decay_multiplier`` exactly once.  No hardcoded paradox factor.

        Factors:
        - Base rate from timeline (default 0.01/hr = 1%/hr)
        - ``decay_multiplier`` set by ParadoxTask (≥1.0)
        - Activity bonus: less decay if high volume
        - Per-minute conversion: hourly ÷ 60
        """
        base_rate = timeline.decay_rate_per_hour or self.BASE_DECAY_PER_HOUR

        # Apply paradox multiplier (written by ParadoxTask, default 1.0)
        multiplier = timeline.decay_multiplier if timeline.decay_multiplier else 1.0
        effective_rate = base_rate * multiplier

        # Per-minute
        decay_per_minute = effective_rate / 60.0

        # Activity bonus: high volume timelines decay slower
        if timeline.total_volume_usd > 100000:
            decay_per_minute *= 0.5
        elif timeline.total_volume_usd > 50000:
            decay_per_minute *= 0.7
        elif timeline.total_volume_usd > 10000:
            decay_per_minute *= 0.9

        # Cap maximum decay (per-minute)
        decay_per_minute = min(decay_per_minute, self.MAX_DECAY_RATE / 60.0)

        return decay_per_minute
