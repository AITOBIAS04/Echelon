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
from datetime import datetime, timezone
import uuid

from backend.database.models import Timeline, WingFlap, WingFlapType

logger = logging.getLogger('echelon.entropy')


class EntropyTask:
    """Applies entropy (stability decay) to all active timelines."""
    
    # Base decay per minute (will be divided by 60 for per-minute rate)
    BASE_DECAY_PER_HOUR = 1.0  # 1% per hour baseline
    
    # Minimum stability before timeline becomes critical
    CRITICAL_THRESHOLD = 20.0
    
    # Maximum decay rate (even with paradox multiplier)
    MAX_DECAY_RATE = 10.0
    
    async def tick(self, session: AsyncSession) -> str:
        """
        Apply entropy decay to all active timelines.
        
        Returns a summary string for logging.
        """
        # Get all active timelines
        result = await session.execute(
            select(Timeline).where(Timeline.is_active == True)
        )
        timelines = result.scalars().all()
        
        if not timelines:
            return "No active timelines"
        
        decayed_count = 0
        critical_count = 0
        total_decay = 0.0
        
        for timeline in timelines:
            # Calculate decay for this timeline
            decay = self._calculate_decay(timeline)
            
            # Apply decay
            old_stability = timeline.stability
            new_stability = max(0.0, timeline.stability - decay)
            
            # Update timeline
            # Note: updated_at is auto-updated by SQLAlchemy, so we don't need to set it
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
            
            # Log significant decays
            if decay > 0.5:
                logger.debug(
                    f"  {timeline.id}: {old_stability:.1f}% -> {new_stability:.1f}% "
                    f"(decay: {decay:.2f}%)"
                )
            
            # Create wing flap for entropy event (if decay is significant)
            if decay > 0.1:
                # Generate a unique ID for the flap
                flap_id = f"ENTROPY_{timeline.id}_{uuid.uuid4().hex[:8]}"
                
                # Get or create SYSTEM agent for entropy events
                from backend.database.models import Agent, AgentArchetype, User
                from sqlalchemy import select as sql_select
                
                # First check for SYSTEM user
                system_user_result = await session.execute(
                    sql_select(User).where(User.id == "SYSTEM")
                )
                system_user = system_user_result.scalar_one_or_none()
                
                if not system_user:
                    # Create SYSTEM user if it doesn't exist
                    from backend.auth.password import hash_password
                    system_user = User(
                        id="SYSTEM",
                        username="SYSTEM",
                        email="system@echelon.io",
                        password_hash=hash_password("system"),  # Placeholder password
                        tier="system",
                    )
                    session.add(system_user)
                    await session.flush()
                
                # Then check for SYSTEM agent
                system_agent_result = await session.execute(
                    sql_select(Agent).where(Agent.id == "SYSTEM")
                )
                system_agent = system_agent_result.scalar_one_or_none()
                
                if not system_agent:
                    # Create SYSTEM agent if it doesn't exist
                    system_agent = Agent(
                        id="SYSTEM",
                        name="SYSTEM",
                        archetype=AgentArchetype.DEGEN,  # Placeholder archetype
                        owner_id="SYSTEM",
                        wallet_address="0x0000000000000000000000000000000000000000",
                        is_alive=True,
                    )
                    session.add(system_agent)
                    await session.flush()
                
                # Convert to naive datetime for database (column is TIMESTAMP WITHOUT TIME ZONE)
                flap_timestamp = datetime.now(timezone.utc).replace(tzinfo=None)
                entropy_flap = WingFlap(
                    id=flap_id,
                    timeline_id=timeline.id,
                    agent_id="SYSTEM",
                    flap_type=WingFlapType.ENTROPY,
                    action=f"Entropy decay: -{decay:.2f}% stability",
                    stability_delta=-decay,
                    direction="DESTABILISE",
                    volume_usd=0.0,
                    timeline_stability=new_stability,
                    timeline_price=timeline.price_yes,
                    timestamp=flap_timestamp,
                )
                session.add(entropy_flap)
        
        avg_decay = total_decay / decayed_count if decayed_count > 0 else 0
        
        return (
            f"Decayed {decayed_count} timelines "
            f"(avg: {avg_decay:.2f}%, critical: {critical_count})"
        )
    
    def _calculate_decay(self, timeline: Timeline) -> float:
        """
        Calculate decay rate for a timeline.
        
        Factors:
        - Base rate: 1% per hour
        - Paradox multiplier: up to 5x if breach active
        - Activity bonus: less decay if high volume
        - Per-minute rate: divide hourly by 60
        """
        # Start with base rate (per minute)
        decay_per_minute = (timeline.decay_rate_per_hour or self.BASE_DECAY_PER_HOUR) / 60.0
        
        # Apply paradox multiplier if active
        if timeline.has_active_paradox:
            # Paradox timelines decay faster
            decay_per_minute *= 2.0
        
        # Activity bonus: high volume timelines decay slower
        # $100K+ volume = 50% decay reduction
        if timeline.total_volume_usd > 100000:
            decay_per_minute *= 0.5
        elif timeline.total_volume_usd > 50000:
            decay_per_minute *= 0.7
        elif timeline.total_volume_usd > 10000:
            decay_per_minute *= 0.9
        
        # Cap maximum decay
        decay_per_minute = min(decay_per_minute, self.MAX_DECAY_RATE / 60.0)
        
        return decay_per_minute
