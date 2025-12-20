"""
Paradox Task - Containment Breach Detection

Scans all timelines for conditions that spawn paradoxes:
- Logic gap > 40% (OSINT contradicts market price)
- Stability < 30% (timeline becoming unstable)
- Price divergence > 50% from connected timelines

When detected, spawns a new paradox with countdown timer.
"""

import logging
from datetime import datetime, timedelta, timezone
from sqlalchemy import select, and_, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import (
    Timeline, Paradox, WingFlap,
    ParadoxStatus, SeverityClass, WingFlapType
)

logger = logging.getLogger('echelon.paradox')


class ParadoxTask:
    """Detects and spawns containment breaches."""
    
    # Thresholds for paradox spawning
    LOGIC_GAP_THRESHOLD = 0.40      # 40% logic gap triggers breach
    STABILITY_THRESHOLD = 30.0       # Below 30% stability is dangerous
    PRICE_DIVERGENCE_THRESHOLD = 0.50  # 50% price difference from connected
    
    # Cooldown: don't spawn new paradox if one resolved recently
    SPAWN_COOLDOWN_MINUTES = 30
    
    async def tick(self, session: AsyncSession) -> str:
        """
        Scan timelines and spawn paradoxes where conditions are met.
        
        Returns a summary string for logging.
        """
        # Get timelines without active paradoxes
        result = await session.execute(
            select(Timeline).where(
                and_(
                    Timeline.is_active == True,
                    Timeline.has_active_paradox == False
                )
            )
        )
        timelines = result.scalars().all()
        
        spawned = 0
        checked = len(timelines)
        
        for timeline in timelines:
            should_spawn, reason, severity = self._check_spawn_conditions(timeline)
            
            if should_spawn:
                await self._spawn_paradox(session, timeline, reason, severity)
                spawned += 1
                logger.warning(
                    f"PARADOX SPAWNED: {timeline.id} - {reason} "
                    f"(Severity: {severity.value})"
                )
        
        # Also check for paradox detonations
        detonated = await self._check_detonations(session)
        
        result_parts = [f"Checked {checked} timelines"]
        if spawned > 0:
            result_parts.append(f"spawned {spawned}")
        if detonated > 0:
            result_parts.append(f"DETONATED {detonated}")
        
        return ", ".join(result_parts)
    
    def _check_spawn_conditions(
        self, 
        timeline: Timeline
    ) -> tuple[bool, str, SeverityClass]:
        """
        Check if a timeline should spawn a paradox.
        
        Returns: (should_spawn, reason, severity)
        """
        # Check logic gap (OSINT vs market disagreement)
        if timeline.logic_gap > self.LOGIC_GAP_THRESHOLD:
            severity = (
                SeverityClass.CLASS_1_CRITICAL if timeline.logic_gap > 0.60
                else SeverityClass.CLASS_2_SEVERE if timeline.logic_gap > 0.50
                else SeverityClass.CLASS_3_MODERATE
            )
            return (
                True,
                f"Logic gap critical: {timeline.logic_gap:.0%}",
                severity
            )
        
        # Check stability collapse
        if timeline.stability < self.STABILITY_THRESHOLD:
            severity = (
                SeverityClass.CLASS_1_CRITICAL if timeline.stability < 15
                else SeverityClass.CLASS_2_SEVERE if timeline.stability < 25
                else SeverityClass.CLASS_3_MODERATE
            )
            return (
                True,
                f"Stability collapse: {timeline.stability:.1f}%",
                severity
            )
        
        # No paradox conditions met
        return (False, "", SeverityClass.CLASS_4_MINOR)
    
    async def _spawn_paradox(
        self,
        session: AsyncSession,
        timeline: Timeline,
        reason: str,
        severity: SeverityClass
    ):
        """Spawn a new paradox on a timeline."""
        now = datetime.now(timezone.utc)
        # Convert to naive datetime for database (columns are TIMESTAMP WITHOUT TIME ZONE)
        now_naive = now.replace(tzinfo=None)
        
        # Calculate detonation time based on severity
        hours_until_detonation = {
            SeverityClass.CLASS_1_CRITICAL: 2,
            SeverityClass.CLASS_2_SEVERE: 4,
            SeverityClass.CLASS_3_MODERATE: 8,
            SeverityClass.CLASS_4_MINOR: 24,
        }[severity]
        
        detonation_time = (now + timedelta(hours=hours_until_detonation)).replace(tzinfo=None)
        
        # Calculate extraction costs based on severity and timeline value
        base_cost = timeline.total_volume_usd * 0.01  # 1% of volume
        severity_multiplier = {
            SeverityClass.CLASS_1_CRITICAL: 4.0,
            SeverityClass.CLASS_2_SEVERE: 2.0,
            SeverityClass.CLASS_3_MODERATE: 1.0,
            SeverityClass.CLASS_4_MINOR: 0.5,
        }[severity]
        
        extraction_cost_usdc = min(base_cost * severity_multiplier, 10000)
        extraction_cost_echelon = int(extraction_cost_usdc * 0.3)
        carrier_sanity_cost = {
            SeverityClass.CLASS_1_CRITICAL: 50,
            SeverityClass.CLASS_2_SEVERE: 35,
            SeverityClass.CLASS_3_MODERATE: 20,
            SeverityClass.CLASS_4_MINOR: 10,
        }[severity]
        
        # Generate paradox ID
        import uuid
        paradox_id = f"PARADOX_{timeline.id}_{uuid.uuid4().hex[:8]}"
        
        # Create paradox
        paradox = Paradox(
            id=paradox_id,
            timeline_id=timeline.id,
            status=ParadoxStatus.ACTIVE,
            severity_class=severity,
            logic_gap=timeline.logic_gap,
            spawned_at=now_naive,
            detonation_time=detonation_time,
            decay_multiplier=severity_multiplier + 1,
            extraction_cost_usdc=extraction_cost_usdc,
            extraction_cost_echelon=extraction_cost_echelon,
            carrier_sanity_cost=carrier_sanity_cost,
        )
        session.add(paradox)
        
        # Update timeline - multiply existing decay rate
        current_decay_rate = timeline.decay_rate_per_hour or 1.0
        new_decay_rate = current_decay_rate * (severity_multiplier + 1)
        
        await session.execute(
            update(Timeline)
            .where(Timeline.id == timeline.id)
            .values(
                has_active_paradox=True,
                decay_rate_per_hour=new_decay_rate,
                decay_multiplier=severity_multiplier + 1
            )
        )
        
        # Get or create SYSTEM agent for wing flaps
        from backend.database.models import Agent, AgentArchetype, User
        from backend.auth.password import hash_password
        
        system_user_result = await session.execute(
            select(User).where(User.id == "SYSTEM")
        )
        system_user = system_user_result.scalar_one_or_none()
        
        if not system_user:
            system_user = User(
                id="SYSTEM",
                username="SYSTEM",
                email="system@echelon.io",
                password_hash=hash_password("system"),
                tier="system",
            )
            session.add(system_user)
            await session.flush()
        
        system_agent_result = await session.execute(
            select(Agent).where(Agent.id == "SYSTEM")
        )
        system_agent = system_agent_result.scalar_one_or_none()
        
        if not system_agent:
            system_agent = Agent(
                id="SYSTEM",
                name="SYSTEM",
                archetype=AgentArchetype.DEGEN,
                owner_id="SYSTEM",
                wallet_address="0x0000000000000000000000000000000000000000",
                is_alive=True,
            )
            session.add(system_agent)
            await session.flush()
        
        # Create wing flap for the event
        flap_id = f"PARADOX_{timeline.id}_{uuid.uuid4().hex[:8]}"
        # Use naive datetime (already converted above)
        flap = WingFlap(
            id=flap_id,
            timeline_id=timeline.id,
            agent_id="SYSTEM",
            flap_type=WingFlapType.PARADOX,
            action=f"⚠️ CONTAINMENT BREACH: {reason}",
            stability_delta=-10.0,
            direction="DESTABILISE",
            volume_usd=0.0,
            timeline_stability=timeline.stability,
            timeline_price=timeline.price_yes,
            timestamp=now_naive,
        )
        session.add(flap)
    
    async def _check_detonations(self, session: AsyncSession) -> int:
        """Check for paradoxes that have detonated."""
        now = datetime.now(timezone.utc)
        # Convert to naive datetime for database comparison (column is TIMESTAMP WITHOUT TIME ZONE)
        now_naive = now.replace(tzinfo=None)
        
        # Find paradoxes past their detonation time
        result = await session.execute(
            select(Paradox).where(
                and_(
                    Paradox.status == ParadoxStatus.ACTIVE,
                    Paradox.detonation_time <= now_naive
                )
            )
        )
        expired_paradoxes = result.scalars().all()
        
        for paradox in expired_paradoxes:
            await self._detonate_paradox(session, paradox)
        
        return len(expired_paradoxes)
    
    async def _detonate_paradox(self, session: AsyncSession, paradox: Paradox):
        """Handle paradox detonation - timeline collapse."""
        logger.error(f"💥 PARADOX DETONATED: {paradox.id} on {paradox.timeline_id}")
        
        # Update paradox status
        await session.execute(
            update(Paradox)
            .where(Paradox.id == paradox.id)
            .values(status=ParadoxStatus.DETONATED)
        )
        
        # Get the timeline
        result = await session.execute(
            select(Timeline).where(Timeline.id == paradox.timeline_id)
        )
        timeline = result.scalar_one_or_none()
        
        if timeline:
            old_stability = timeline.stability
            
            # Collapse the timeline
            await session.execute(
                update(Timeline)
                .where(Timeline.id == paradox.timeline_id)
                .values(
                    stability=0.0,
                    is_active=False,
                    has_active_paradox=False
                )
            )
            
            # Get or create SYSTEM agent for wing flaps
            from backend.database.models import Agent, AgentArchetype, User
            from backend.auth.password import hash_password
            
            system_user_result = await session.execute(
                select(User).where(User.id == "SYSTEM")
            )
            system_user = system_user_result.scalar_one_or_none()
            
            if not system_user:
                system_user = User(
                    id="SYSTEM",
                    username="SYSTEM",
                    email="system@echelon.io",
                    password_hash=hash_password("system"),
                    tier="system",
                )
                session.add(system_user)
                await session.flush()
            
            system_agent_result = await session.execute(
                select(Agent).where(Agent.id == "SYSTEM")
            )
            system_agent = system_agent_result.scalar_one_or_none()
            
            if not system_agent:
                system_agent = Agent(
                    id="SYSTEM",
                    name="SYSTEM",
                    archetype=AgentArchetype.DEGEN,
                    owner_id="SYSTEM",
                    wallet_address="0x0000000000000000000000000000000000000000",
                    is_alive=True,
                )
                session.add(system_agent)
                await session.flush()
            
            # Create dramatic wing flap
            import uuid
            flap_id = f"DETONATE_{paradox.timeline_id}_{uuid.uuid4().hex[:8]}"
            # Convert to naive datetime for database (column is TIMESTAMP WITHOUT TIME ZONE)
            flap_timestamp = datetime.now(timezone.utc).replace(tzinfo=None)
            flap = WingFlap(
                id=flap_id,
                timeline_id=paradox.timeline_id,
                agent_id="SYSTEM",
                flap_type=WingFlapType.PARADOX,
                action=f"💥 TIMELINE COLLAPSED: Paradox detonation",
                stability_delta=-old_stability,
                direction="DESTABILISE",
                volume_usd=0.0,
                timeline_stability=0.0,
                timeline_price=timeline.price_yes,
                timestamp=flap_timestamp,
            )
            session.add(flap)
