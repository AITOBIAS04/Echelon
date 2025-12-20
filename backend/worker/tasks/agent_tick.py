"""
Agent Tick Task - Autonomous AI Decisions

Every tick, agents evaluate the market and decide to:
- TRADE: Buy/sell positions
- SHIELD: Protect a timeline
- SABOTAGE: Attack a timeline
- OBSERVE: Wait for better opportunity

Uses the Hierarchical Intelligence Architecture:
- Layer 1: Fast heuristic rules (90% of decisions)
- Layer 2: LLM reasoning (10% of decisions, for novel situations)
"""

import logging
import random
import uuid
from datetime import datetime, timezone
from sqlalchemy import select, and_, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import (
    Agent, Timeline, WingFlap,
    AgentArchetype, WingFlapType
)

logger = logging.getLogger('echelon.agents')


class AgentTickTask:
    """Processes autonomous agent decisions."""
    
    # How often each agent type acts (probability per tick)
    ACTION_PROBABILITY = {
        AgentArchetype.SHARK: 0.30,      # Sharks trade frequently
        AgentArchetype.SPY: 0.10,        # Spies observe mostly
        AgentArchetype.DIPLOMAT: 0.15,   # Diplomats act carefully
        AgentArchetype.SABOTEUR: 0.20,   # Saboteurs cause trouble
        AgentArchetype.WHALE: 0.05,      # Whales move rarely but big
        AgentArchetype.DEGEN: 0.25,     # Degens trade often
    }
    
    async def tick(self, session: AsyncSession) -> str:
        """
        Process agent decisions for this tick.
        
        Returns a summary string for logging.
        """
        # Get all alive agents
        result = await session.execute(
            select(Agent).where(Agent.is_alive == True)
        )
        agents = result.scalars().all()
        
        # Get active timelines
        result = await session.execute(
            select(Timeline).where(Timeline.is_active == True)
        )
        timelines = result.scalars().all()
        
        if not agents or not timelines:
            return f"Agents: {len(agents)}, Timelines: {len(timelines)}"
        
        actions_taken = 0
        
        for agent in agents:
            # Check if agent acts this tick
            action_prob = self.ACTION_PROBABILITY.get(agent.archetype, 0.1)
            
            if random.random() < action_prob:
                action = await self._agent_decision(session, agent, timelines)
                if action:
                    actions_taken += 1
        
        return f"{len(agents)} agents, {actions_taken} actions"
    
    async def _agent_decision(
        self,
        session: AsyncSession,
        agent: Agent,
        timelines: list[Timeline]
    ) -> bool:
        """
        Make a decision for a single agent.
        
        Uses Layer 1 heuristics based on archetype.
        Returns True if action was taken.
        """
        # Choose strategy based on archetype
        if agent.archetype == AgentArchetype.SHARK:
            return await self._shark_strategy(session, agent, timelines)
        elif agent.archetype == AgentArchetype.SPY:
            return await self._spy_strategy(session, agent, timelines)
        elif agent.archetype == AgentArchetype.DIPLOMAT:
            return await self._diplomat_strategy(session, agent, timelines)
        elif agent.archetype == AgentArchetype.SABOTEUR:
            return await self._saboteur_strategy(session, agent, timelines)
        elif agent.archetype == AgentArchetype.WHALE:
            return await self._whale_strategy(session, agent, timelines)
        elif agent.archetype == AgentArchetype.DEGEN:
            # Degens use similar strategy to sharks but more aggressive
            return await self._shark_strategy(session, agent, timelines)
        
        return False
    
    async def _shark_strategy(
        self,
        session: AsyncSession,
        agent: Agent,
        timelines: list[Timeline]
    ) -> bool:
        """
        Shark Strategy: Exploit mispricings aggressively.
        
        Heuristics:
        - Target high logic_gap timelines (info advantage)
        - Prefer high volume (liquidity)
        - Trade against the crowd when confident
        """
        if not timelines:
            return False
        
        # Find timeline with highest logic gap
        target = max(timelines, key=lambda t: t.logic_gap * (t.total_volume_usd or 0))
        
        # Decide direction based on OSINT alignment
        # If OSINT alignment < 50%, reality disagrees with market -> short
        side = "YES" if target.osint_alignment > 50 else "NO"
        
        # Position size based on agent genome
        aggression = agent.genome.get('aggression', 0.5) if agent.genome else 0.5
        base_size = 1000
        size = base_size * (1 + aggression)
        
        # Calculate price
        price = target.price_yes if side == "YES" else target.price_no
        contracts = int(size / price) if price > 0 else 0
        
        # Create trade
        stability_delta = size / 10000 * (1 if side == "YES" else -1)
        new_stability = max(0, min(100, target.stability + stability_delta))
        
        flap_id = f"SHARK_{agent.id}_{uuid.uuid4().hex[:8]}"
        # Convert to naive datetime for database (column is TIMESTAMP WITHOUT TIME ZONE)
        flap_timestamp = datetime.now(timezone.utc).replace(tzinfo=None)
        flap = WingFlap(
            id=flap_id,
            timeline_id=target.id,
            agent_id=agent.id,
            flap_type=WingFlapType.TRADE,
            action=f"{agent.name} bought {contracts} {side} @ ${price:.2f}",
            stability_delta=stability_delta,
            direction="ANCHOR" if stability_delta > 0 else "DESTABILISE",
            volume_usd=size,
            timeline_stability=new_stability,
            timeline_price=target.price_yes,
            timestamp=flap_timestamp,
        )
        session.add(flap)
        
        # Update agent stats
        current_trades = agent.trades_count or 0
        await session.execute(
            update(Agent)
            .where(Agent.id == agent.id)
            .values(trades_count=current_trades + 1)
        )
        
        # Update timeline
        current_volume = target.total_volume_usd or 0.0
        await session.execute(
            update(Timeline)
            .where(Timeline.id == target.id)
            .values(
                stability=new_stability,
                total_volume_usd=current_volume + size,
            )
        )
        
        return True
    
    async def _spy_strategy(
        self,
        session: AsyncSession,
        agent: Agent,
        timelines: list[Timeline]
    ) -> bool:
        """
        Spy Strategy: Gather and sell intel.
        
        Heuristics:
        - Target unstable timelines (more intel value)
        - Create intel packages about paradoxes
        - Small stabilising trades to maintain access
        """
        if not timelines:
            return False
        
        # Find most unstable timeline
        target = min(timelines, key=lambda t: t.stability)
        
        # Spy deploys recon (small stabilising action)
        stability_delta = random.uniform(1.0, 3.0)
        new_stability = min(100, target.stability + stability_delta)
        
        flap_id = f"SPY_{agent.id}_{uuid.uuid4().hex[:8]}"
        # Convert to naive datetime for database (column is TIMESTAMP WITHOUT TIME ZONE)
        flap_timestamp = datetime.now(timezone.utc).replace(tzinfo=None)
        flap = WingFlap(
            id=flap_id,
            timeline_id=target.id,
            agent_id=agent.id,
            flap_type=WingFlapType.SHIELD,
            action=f"{agent.name} deployed RECON on {target.name[:30]}...",
            stability_delta=stability_delta,
            direction="ANCHOR",
            volume_usd=0.0,
            timeline_stability=new_stability,
            timeline_price=target.price_yes,
            timestamp=flap_timestamp,
        )
        session.add(flap)
        
        # Update timeline
        await session.execute(
            update(Timeline)
            .where(Timeline.id == target.id)
            .values(
                stability=new_stability,
            )
        )
        
        return True
    
    async def _diplomat_strategy(
        self,
        session: AsyncSession,
        agent: Agent,
        timelines: list[Timeline]
    ) -> bool:
        """
        Diplomat Strategy: Stabilise and broker peace.
        
        Heuristics:
        - Target timelines with paradoxes
        - Deploy shields to reduce decay
        - Broker treaties between agents
        """
        if not timelines:
            return False
        
        # Find timeline with active paradox (highest need)
        paradox_timelines = [t for t in timelines if t.has_active_paradox]
        if not paradox_timelines:
            # No paradoxes, stabilise lowest timeline
            target = min(timelines, key=lambda t: t.stability)
        else:
            target = random.choice(paradox_timelines)
        
        # Deploy shield
        stability_delta = random.uniform(3.0, 8.0)
        new_stability = min(100, target.stability + stability_delta)
        
        flap_id = f"DIPLOMAT_{agent.id}_{uuid.uuid4().hex[:8]}"
        # Convert to naive datetime for database (column is TIMESTAMP WITHOUT TIME ZONE)
        flap_timestamp = datetime.now(timezone.utc).replace(tzinfo=None)
        flap = WingFlap(
            id=flap_id,
            timeline_id=target.id,
            agent_id=agent.id,
            flap_type=WingFlapType.SHIELD,
            action=f"{agent.name} deployed SHIELD on {target.name[:30]}...",
            stability_delta=stability_delta,
            direction="ANCHOR",
            volume_usd=0.0,
            timeline_stability=new_stability,
            timeline_price=target.price_yes,
            timestamp=flap_timestamp,
        )
        session.add(flap)
        
        # Update timeline
        await session.execute(
            update(Timeline)
            .where(Timeline.id == target.id)
            .values(
                stability=new_stability,
            )
        )
        
        return True
    
    async def _saboteur_strategy(
        self,
        session: AsyncSession,
        agent: Agent,
        timelines: list[Timeline]
    ) -> bool:
        """
        Saboteur Strategy: Create chaos for profit.
        
        Heuristics:
        - Target stable timelines (more to destroy)
        - Avoid timelines with active paradoxes (already unstable)
        - Attack then short
        """
        # Find most stable timeline without paradox
        stable_timelines = [t for t in timelines if not t.has_active_paradox]
        if not stable_timelines:
            return False
        
        target = max(stable_timelines, key=lambda t: t.stability)
        
        # Sabotage attack
        stability_delta = -random.uniform(5.0, 12.0)
        new_stability = max(0, target.stability + stability_delta)
        
        flap_id = f"SABOTEUR_{agent.id}_{uuid.uuid4().hex[:8]}"
        # Convert to naive datetime for database (column is TIMESTAMP WITHOUT TIME ZONE)
        flap_timestamp = datetime.now(timezone.utc).replace(tzinfo=None)
        flap = WingFlap(
            id=flap_id,
            timeline_id=target.id,
            agent_id=agent.id,
            flap_type=WingFlapType.SABOTAGE,
            action=f"{agent.name} launched SABOTAGE on {target.name[:30]}...",
            stability_delta=stability_delta,
            direction="DESTABILISE",
            volume_usd=0.0,
            timeline_stability=new_stability,
            timeline_price=target.price_yes,
            timestamp=flap_timestamp,
        )
        session.add(flap)
        
        # Update timeline
        await session.execute(
            update(Timeline)
            .where(Timeline.id == target.id)
            .values(
                stability=new_stability,
            )
        )
        
        # Cost sanity
        new_sanity = max(0, agent.sanity - 5)
        await session.execute(
            update(Agent)
            .where(Agent.id == agent.id)
            .values(sanity=new_sanity)
        )
        
        return True
    
    async def _whale_strategy(
        self,
        session: AsyncSession,
        agent: Agent,
        timelines: list[Timeline]
    ) -> bool:
        """
        Whale Strategy: Large, market-moving trades.
        
        Heuristics:
        - Only trade when highly confident
        - Massive position sizes
        - Prefer high liquidity
        """
        if not timelines:
            return False
        
        # Find highest liquidity timeline
        target = max(timelines, key=lambda t: t.liquidity_depth_usd or 0)
        
        # Whales only trade when logic gap is extreme
        if target.logic_gap < 0.30:
            return False
        
        # Massive trade
        side = "YES" if target.osint_alignment > 50 else "NO"
        size = random.uniform(10000, 50000)
        price = target.price_yes if side == "YES" else target.price_no
        contracts = int(size / price) if price > 0 else 0
        
        stability_delta = size / 5000 * (1 if side == "YES" else -1)
        new_stability = max(0, min(100, target.stability + stability_delta))
        
        flap_id = f"WHALE_{agent.id}_{uuid.uuid4().hex[:8]}"
        # Convert to naive datetime for database (column is TIMESTAMP WITHOUT TIME ZONE)
        flap_timestamp = datetime.now(timezone.utc).replace(tzinfo=None)
        flap = WingFlap(
            id=flap_id,
            timeline_id=target.id,
            agent_id=agent.id,
            flap_type=WingFlapType.TRADE,
            action=f"🐋 {agent.name} bought {contracts} {side} @ ${price:.2f}",
            stability_delta=stability_delta,
            direction="ANCHOR" if stability_delta > 0 else "DESTABILISE",
            volume_usd=size,
            timeline_stability=new_stability,
            timeline_price=target.price_yes,
            timestamp=flap_timestamp,
        )
        session.add(flap)
        
        # Update timeline (whale moves market)
        current_volume = target.total_volume_usd or 0.0
        await session.execute(
            update(Timeline)
            .where(Timeline.id == target.id)
            .values(
                stability=new_stability,
                total_volume_usd=current_volume + size,
            )
        )
        
        logger.info(f"🐋 WHALE ALERT: {agent.name} moved ${size:,.0f} on {target.id}")
        
        return True
