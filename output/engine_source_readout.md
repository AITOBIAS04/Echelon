# Engine Source Readout

## /Users/tobiasharber/Developer/prediction-market-monorepo.nosync/backend/mechanics/butterfly_engine.py
```python
from datetime import datetime, timedelta
from typing import Optional, List, Tuple
import random
import math
from ..schemas.butterfly_schemas import (
    WingFlap, WingFlapType, StabilityDirection, AgentArchetype,
    TimelineHealth, GravityBreakdown, Ripple
)

class ButterflyEngine:
    """
    The Butterfly Engine calculates causality effects.
    
    Core principle: Every agent action creates a "Wing Flap" that affects
    timeline stability. Large flaps may spawn "Ripples" (forks).
    """
    
    # Thresholds
    RIPPLE_THRESHOLD = 15.0  # |Stability Δ| > 15% spawns a fork
    LOGIC_GAP_PARADOX_THRESHOLD = 0.3  # Gap > 30% may spawn paradox
    
    # Decay rates
    BASE_DECAY_PER_HOUR = 1.0  # 1% per hour
    PARADOX_DECAY_MULTIPLIER = 5.0  # 5x during paradox
    
    def __init__(self, timeline_repo, agent_repo, osint_service):
        self.timeline_repo = timeline_repo
        self.agent_repo = agent_repo
        self.osint_service = osint_service
    
    # =========================================
    # WING FLAP CREATION
    # =========================================
    
    def create_wing_flap(
        self,
        timeline_id: str,
        agent_id: str,
        action_type: WingFlapType,
        volume_usd: float,
        raw_action: str  # "bought 500 YES @ $0.67"
    ) -> WingFlap:
        """
        Create a Wing Flap from an agent action.
        
        Returns the flap with calculated stability delta.
        """
        timeline = self.timeline_repo.get(timeline_id)
        agent = self.agent_repo.get(agent_id)
        
        # Calculate stability delta based on action
        stability_delta = self._calculate_stability_delta(
            timeline=timeline,
            agent=agent,
            action_type=action_type,
            volume_usd=volume_usd
        )
        
        # Determine direction
        direction = (
            StabilityDirection.ANCHOR if stability_delta > 0 
            else StabilityDirection.DESTABILISE
        )
        
        # Apply delta to timeline
        new_stability = max(0, min(100, timeline.stability + stability_delta))
        self.timeline_repo.update_stability(timeline_id, new_stability)
        
        # Check for ripple (fork)
        spawned_ripple = False
        ripple_timeline_id = None
        if abs(stability_delta) > self.RIPPLE_THRESHOLD:
            ripple = self._spawn_ripple(timeline, agent, stability_delta)
            spawned_ripple = True
            ripple_timeline_id = ripple.child_timeline_id
        
        # Calculate founder yield (if applicable)
        founder_yield = self._calculate_founder_yield(timeline, stability_delta)
        
        # Create the flap
        flap = WingFlap(
            id=f"FLAP_{timeline_id}_{int(datetime.now().timestamp() * 1000)}",
            timestamp=datetime.now(),
            timeline_id=timeline_id,
            timeline_name=timeline.name,
            agent_id=agent_id,
            agent_name=agent.name,
            agent_archetype=agent.archetype,
            flap_type=action_type,
            action=f"{agent.name} {raw_action}",
            stability_delta=stability_delta,
            direction=direction,
            volume_usd=volume_usd,
            timeline_stability=new_stability,
            timeline_price=timeline.price_yes,
            spawned_ripple=spawned_ripple,
            ripple_timeline_id=ripple_timeline_id,
            founder_id=timeline.founder_id,
            founder_yield_earned=founder_yield
        )
        
        # Persist and broadcast
        self._persist_flap(flap)
        self._broadcast_flap(flap)
        
        return flap
    
    def _calculate_stability_delta(
        self,
        timeline,
        agent,
        action_type: WingFlapType,
        volume_usd: float
    ) -> float:
        """
        Calculate how much an action affects stability.
        
        Formula incorporates:
        - Volume (larger trades = larger impact)
        - Agent archetype (Sharks destabilise, Diplomats stabilise)
        - Action type (Shields stabilise, Sabotage destabilises)
        - Liquidity (thin markets are more volatile)
        """
        # Base impact from volume (logarithmic)
        base_impact = math.log10(max(100, volume_usd)) * 2  # $1000 = 6, $10000 = 8
        
        # Archetype modifier
        archetype_modifiers = {
            AgentArchetype.SHARK: -1.2,      # Destabilising
            AgentArchetype.SPY: -0.5,        # Slightly destabilising
            AgentArchetype.DIPLOMAT: 1.5,    # Stabilising
            AgentArchetype.SABOTEUR: -2.0,   # Very destabilising
            AgentArchetype.WHALE: -0.8,      # Destabilising (moves markets)
            AgentArchetype.DEGEN: -0.3,      # Slightly destabilising (noise)
        }
        archetype_mod = archetype_modifiers.get(agent.archetype, 0)
        
        # Action type modifier
        action_modifiers = {
            WingFlapType.TRADE: 1.0,
            WingFlapType.SHIELD: 2.0,       # Shields are stabilising
            WingFlapType.SABOTAGE: -2.5,    # Sabotage is destabilising
            WingFlapType.RIPPLE: 0,         # Ripples don't affect parent
            WingFlapType.PARADOX: -5.0,     # Paradoxes are very destabilising
            WingFlapType.FOUNDER_YIELD: 0,  # Yields don't affect stability
        }
        action_mod = action_modifiers.get(action_type, 1.0)
        
        # Liquidity modifier (thin markets are more volatile)
        liquidity_depth = timeline.liquidity_depth_usd or 10000
        liquidity_mod = 10000 / max(1000, liquidity_depth)  # 1.0 at $10k, 10.0 at $1k
        
        # Final calculation
        delta = base_impact * archetype_mod * action_mod * liquidity_mod
        
        # Clamp to reasonable range
        return max(-50, min(50, delta))
    
    # =========================================
    # RIPPLE (FORK) SPAWNING
    # =========================================
    
    def _spawn_ripple(self, timeline, agent, stability_delta: float) -> Ripple:
        """
        Spawn a new timeline fork when stability delta exceeds threshold.
        """
        # Generate fork narrative
        narrative = self._generate_fork_narrative(timeline, stability_delta)
        
        # Create child timeline
        child_timeline = self.timeline_repo.create_fork(
            parent_id=timeline.id,
            narrative=narrative,
            initial_stability=50.0,  # Forks start at 50%
            founder_id=agent.owner_id  # Agent's owner becomes founder
        )
        
        ripple = Ripple(
            id=f"RIPPLE_{child_timeline.id}",
            parent_timeline_id=timeline.id,
            child_timeline_id=child_timeline.id,
            spawned_at=datetime.now(),
            trigger_flap_id="",  # Will be set by caller
            trigger_agent_id=agent.id,
            trigger_stability_delta=stability_delta,
            fork_narrative=narrative,
            initial_stability=50.0,
            founder_id=agent.owner_id,
            founder_stake_usd=0  # Will be set when founder stakes
        )
        
        return ripple
    
    def _generate_fork_narrative(self, timeline, stability_delta: float) -> str:
        """Generate a narrative for the new fork."""
        # In production, this would use LLM
        # For now, simple template
        if stability_delta > 0:
            return f"What if {timeline.name} stabilises further?"
        else:
            return f"What if {timeline.name} collapses?"
    
    # =========================================
    # FOUNDER YIELD
    # =========================================
    
    def _calculate_founder_yield(self, timeline, stability_delta: float) -> Optional[float]:
        """
        Calculate yield for the timeline founder.
        
        Founders earn yield when stability INCREASES (their timeline is healthy).
        """
        if not timeline.founder_id:
            return None
        
        if stability_delta <= 0:
            return None  # No yield for destabilisation
        
        # Yield rate: 0.1% of delta as USDC
        yield_rate = 0.001
        yield_amount = abs(stability_delta) * yield_rate * timeline.total_volume_usd
        
        # Pay the founder
        self._pay_founder_yield(timeline.founder_id, yield_amount)
        
        return yield_amount
    
    def _pay_founder_yield(self, founder_id: str, amount: float):
        """Credit yield to founder's account."""
        # Implementation depends on your payment system
        pass
    
    # =========================================
    # GRAVITY CALCULATION
    # =========================================
    
    def _calculate_gravity_from_timeline(self, timeline) -> GravityBreakdown:
        """
        Calculate gravity from a timeline object (synchronous, no DB call).
        
        Used when we already have the timeline object from a query.
        """
        # Component 1: Volume (0-25)
        volume_score = min(25, (timeline.total_volume_usd / 100000) * 25)
        
        # Component 2: Agent Activity (0-25)
        agent_count = timeline.active_agent_count
        agent_score = min(25, (agent_count / 20) * 25)
        
        # Component 3: Volatility (0-25)
        # Use logic_gap as a proxy for volatility (high gap = volatile)
        volatility_score = min(25, timeline.logic_gap * 83.33)  # 0.3 gap = 25 points
        
        # Component 4: Narrative Relevance (0-25)
        # Use OSINT alignment as proxy
        narrative_score = min(25, (timeline.osint_alignment / 100) * 25)
        
        total_gravity = volume_score + agent_score + volatility_score + narrative_score
        
        return GravityBreakdown(
            timeline_id=timeline.id,
            total_gravity=total_gravity,
            volume_score=volume_score,
            agent_activity_score=agent_score,
            volatility_score=volatility_score,
            narrative_relevance_score=narrative_score,
            related_keywords=timeline.keywords or [],
            osint_sources=[str(s) if not isinstance(s, str) else s for s in (getattr(self.osint_service, 'all_sources', [])[:5] if hasattr(self.osint_service, 'all_sources') else [])],
            trending_rank=None
        )
    
    def calculate_gravity(self, timeline_id: str) -> GravityBreakdown:
        """
        Calculate the "Gravity" score for a timeline.
        
        Gravity determines importance/visibility in the UI.
        High gravity = shown prominently in SIGINT.
        """
        timeline = self.timeline_repo.get(timeline_id)
        
        # For sync version, try to get timeline (may fail if repo is async)
        if hasattr(self.timeline_repo, 'get'):
            try:
                # If it's async, this will fail - use the _calculate_gravity_from_timeline instead
                timeline = self.timeline_repo.get(timeline_id)
                if hasattr(timeline, '__await__'):
                    # It's a coroutine, can't use sync method
                    raise RuntimeError("Cannot use sync calculate_gravity with async repository")
                return self._calculate_gravity_from_timeline(timeline)
            except (AttributeError, RuntimeError):
                # Fallback: return basic gravity from stored score
                return GravityBreakdown(
                    timeline_id=timeline_id,
                    total_gravity=0.0,
                    volume_score=0.0,
                    agent_activity_score=0.0,
                    volatility_score=0.0,
                    narrative_relevance_score=0.0,
                    related_keywords=[],
                    osint_sources=[],
                    trending_rank=None
                )
        
        # Fallback
        return GravityBreakdown(
            timeline_id=timeline_id,
            total_gravity=0.0,
            volume_score=0.0,
            agent_activity_score=0.0,
            volatility_score=0.0,
            narrative_relevance_score=0.0,
            related_keywords=[],
            osint_sources=[],
            trending_rank=None
        )
    
    def _get_recent_stability_delta(self, timeline_id: str, hours: int) -> float:
        """Get sum of stability changes in recent hours."""
        # Query recent flaps
        cutoff = datetime.now() - timedelta(hours=hours)
        flaps = self.timeline_repo.get_flaps_since(timeline_id, cutoff)
        return sum(f.stability_delta for f in flaps)
    
    # =========================================
    # LOGIC GAP (Paradox Detection)
    # =========================================
    
    def calculate_logic_gap(self, timeline_id: str) -> float:
        """
        Calculate the gap between market price and OSINT reality.
        
        High gap = market is mispriced = paradox risk.
        """
        timeline = self.timeline_repo.get(timeline_id)
        
        # Market says this price
        market_confidence = timeline.price_yes  # 0.0 - 1.0
        
        # OSINT says this probability
        osint_probability = self.osint_service.get_reality_score(
            timeline.keywords,
            timeline.narrative
        ) / 100  # Convert to 0.0 - 1.0
        
        # The gap
        logic_gap = abs(market_confidence - osint_probability)
        
        # Update timeline
        self.timeline_repo.update_logic_gap(timeline_id, logic_gap)
        
        return logic_gap
    
    # =========================================
    # PERSISTENCE & BROADCAST
    # =========================================
    
    def _persist_flap(self, flap: WingFlap):
        """Save flap to database."""
        # Store in memory for now (replace with DB in production)
        if not hasattr(self, '_stored_flaps'):
            self._stored_flaps = []
        self._stored_flaps.append(flap)
    
    def _broadcast_flap(self, flap: WingFlap):
        """Broadcast flap via WebSocket to connected clients."""
        # Implementation in websockets/realtime_manager.py
        pass
    
    # =========================================
    # API METHODS (Query Interface)
    # =========================================
    
    async def get_flaps_async(
        self,
        timeline_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        min_delta: float = 0,
        min_volume: float = 0,
        flap_types: Optional[List[str]] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[WingFlap]:
        """Get filtered wing flaps (async version for database queries)."""
        # Check if repository has async get_flaps method (real database)
        if hasattr(self.timeline_repo, 'get_flaps'):
            try:
                db_flaps = await self.timeline_repo.get_flaps(
                    timeline_id=timeline_id,
                    agent_id=agent_id,
                    min_delta=min_delta,
                    min_volume=min_volume,
                    flap_types=flap_types,
                    limit=limit,
                    offset=offset
                )
                # Convert database models to Pydantic schemas
                return [self._db_flap_to_schema(f) for f in db_flaps]
            except Exception as e:
                # Fall back to in-memory if async call fails
                print(f"⚠️ Failed to query database flaps: {e}, using in-memory")
                import traceback
                traceback.print_exc()
        
        # Fallback: use in-memory storage
        flaps = getattr(self, '_stored_flaps', [])
        
        # Filter
        if timeline_id:
            flaps = [f for f in flaps if f.timeline_id == timeline_id]
        if agent_id:
            flaps = [f for f in flaps if f.agent_id == agent_id]
        if min_delta > 0:
            flaps = [f for f in flaps if abs(f.stability_delta) >= min_delta]
        if min_volume > 0:
            flaps = [f for f in flaps if f.volume_usd >= min_volume]
        if flap_types:
            flaps = [f for f in flaps if f.flap_type.value in flap_types]
        
        # Sort by timestamp descending
        flaps.sort(key=lambda f: f.timestamp, reverse=True)
        
        # Paginate
        return flaps[offset:offset + limit]
    
    async def count_flaps_async(
        self,
        timeline_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        min_delta: float = 0,
        min_volume: float = 0,
        flap_types: Optional[List[str]] = None
    ) -> int:
        """Count filtered wing flaps (async version for database queries)."""
        # Check if repository has async count_flaps method (real database)
        if hasattr(self.timeline_repo, 'count_flaps'):
            try:
                return await self.timeline_repo.count_flaps(
                    timeline_id=timeline_id,
                    agent_id=agent_id,
                    min_delta=min_delta,
                    min_volume=min_volume,
                    flap_types=flap_types
                )
            except Exception as e:
                print(f"⚠️ Failed to count database flaps: {e}, using in-memory")
                import traceback
                traceback.print_exc()
        
        # Fallback: use in-memory storage
        flaps = getattr(self, '_stored_flaps', [])
        
        # Apply same filters as get_flaps
        if timeline_id:
            flaps = [f for f in flaps if f.timeline_id == timeline_id]
        if agent_id:
            flaps = [f for f in flaps if f.agent_id == agent_id]
        if min_delta > 0:
            flaps = [f for f in flaps if abs(f.stability_delta) >= min_delta]
        if min_volume > 0:
            flaps = [f for f in flaps if f.volume_usd >= min_volume]
        if flap_types:
            flaps = [f for f in flaps if f.flap_type.value in flap_types]
        
        return len(flaps)
    
    def get_flaps(
        self,
        timeline_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        min_delta: float = 0,
        min_volume: float = 0,
        flap_types: Optional[List[str]] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[WingFlap]:
        """Get filtered wing flaps (sync version, falls back to in-memory)."""
        # Fallback: use in-memory storage
        flaps = getattr(self, '_stored_flaps', [])
        
        # Filter
        if timeline_id:
            flaps = [f for f in flaps if f.timeline_id == timeline_id]
        if agent_id:
            flaps = [f for f in flaps if f.agent_id == agent_id]
        if min_delta > 0:
            flaps = [f for f in flaps if abs(f.stability_delta) >= min_delta]
        if min_volume > 0:
            flaps = [f for f in flaps if f.volume_usd >= min_volume]
        if flap_types:
            flaps = [f for f in flaps if f.flap_type.value in flap_types]
        
        # Sort by timestamp descending
        flaps.sort(key=lambda f: f.timestamp, reverse=True)
        
        # Paginate
        return flaps[offset:offset + limit]
    
    def _db_flap_to_schema(self, db_flap) -> WingFlap:
        """Convert database WingFlap model to Pydantic schema."""
        from ..database.models import WingFlap as DBWingFlap
        from ..schemas.butterfly_schemas import AgentArchetype
        
        # Get timeline and agent names
        timeline_name = db_flap.timeline.name if db_flap.timeline else f"Timeline {db_flap.timeline_id[:8]}"
        agent_name = db_flap.agent.name if db_flap.agent else db_flap.agent_id
        
        # Convert agent archetype
        agent_archetype = AgentArchetype.SHARK  # Default
        if db_flap.agent and hasattr(db_flap.agent, 'archetype'):
            try:
                # Handle both enum and string values
                archetype_value = db_flap.agent.archetype
                if hasattr(archetype_value, 'value'):
                    archetype_value = archetype_value.value
                agent_archetype = AgentArchetype[archetype_value]
            except (KeyError, AttributeError):
                pass
        
        # Convert direction enum
        from ..schemas.butterfly_schemas import StabilityDirection
        direction_enum = StabilityDirection.ANCHOR  # Default
        if hasattr(db_flap, 'direction'):
            try:
                direction_value = db_flap.direction
                if hasattr(direction_value, 'value'):
                    direction_value = direction_value.value
                direction_enum = StabilityDirection[direction_value] if direction_value in StabilityDirection.__members__ else StabilityDirection.ANCHOR
            except (KeyError, AttributeError):
                pass
        
        # Clamp values to schema constraints
        # Stability can exceed 100% in edge cases, but schema requires <= 100
        clamped_stability = min(100.0, max(0.0, db_flap.timeline_stability or 0.0))
        # Price must be between 0 and 1
        clamped_price = min(1.0, max(0.0, db_flap.timeline_price or 0.0))
        
        return WingFlap(
            id=db_flap.id,
            timestamp=db_flap.timestamp,
            timeline_id=db_flap.timeline_id,
            timeline_name=timeline_name,
            agent_id=db_flap.agent_id,
            agent_name=agent_name,
            agent_archetype=agent_archetype,
            flap_type=db_flap.flap_type,
            action=db_flap.action,
            stability_delta=db_flap.stability_delta,
            direction=direction_enum,
            volume_usd=db_flap.volume_usd,
            timeline_stability=clamped_stability,
            timeline_price=clamped_price,
            spawned_ripple=db_flap.spawned_ripple,
            ripple_timeline_id=db_flap.ripple_timeline_id,
            founder_id=None,  # Will be populated from timeline if needed
            founder_yield_earned=db_flap.founder_yield_earned
        )
    
    def count_flaps(
        self,
        timeline_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        min_delta: float = 0,
        min_volume: float = 0,
        flap_types: Optional[List[str]] = None
    ) -> int:
        """Count filtered wing flaps."""
        # Check if repository has async count_flaps method (real database)
        if hasattr(self.timeline_repo, 'count_flaps'):
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    import nest_asyncio
                    nest_asyncio.apply()
                return asyncio.run(
                    self.timeline_repo.count_flaps(
                        timeline_id=timeline_id,
                        agent_id=agent_id,
                        min_delta=min_delta,
                        min_volume=min_volume,
                        flap_types=flap_types
                    )
                )
            except Exception as e:
                print(f"⚠️ Failed to count database flaps: {e}, using in-memory")
        
        # Fallback: use in-memory storage
        flaps = getattr(self, '_stored_flaps', [])
        
        # Apply same filters as get_flaps
        if timeline_id:
            flaps = [f for f in flaps if f.timeline_id == timeline_id]
        if agent_id:
            flaps = [f for f in flaps if f.agent_id == agent_id]
        if min_delta > 0:
            flaps = [f for f in flaps if abs(f.stability_delta) >= min_delta]
        if min_volume > 0:
            flaps = [f for f in flaps if f.volume_usd >= min_volume]
        if flap_types:
            flaps = [f for f in flaps if f.flap_type.value in flap_types]
        
        return len(flaps)
    
    def get_recent_high_impact_flaps(self, since: datetime, limit: int = 20) -> List[WingFlap]:
        """Get recent high-impact flaps."""
        flaps = getattr(self, '_stored_flaps', [])
        flaps = [f for f in flaps if f.timestamp >= since]
        flaps.sort(key=lambda f: abs(f.stability_delta), reverse=True)
        return flaps[:limit]
    
    async def get_timeline_health_async(
        self,
        sort_by: str = "gravity_score",
        sort_order: str = "desc",
        min_gravity: float = 0,
        paradox_only: bool = False,
        limit: int = 20
    ) -> List[TimelineHealth]:
        """Get timeline health metrics (async version for database queries)."""
        # Check if repository has async methods (real database)
        if hasattr(self.timeline_repo, 'get_all_active') or hasattr(self.timeline_repo, 'get_by_gravity'):
            try:
                # Query timelines from database
                if paradox_only:
                    db_timelines = await self.timeline_repo.get_with_paradox()
                elif min_gravity > 0:
                    db_timelines = await self.timeline_repo.get_by_gravity(min_gravity=min_gravity, limit=limit)
                else:
                    db_timelines = await self.timeline_repo.get_all_active()
                
                # Convert to TimelineHealth schemas
                health_list = []
                for timeline in db_timelines[:limit]:
                    try:
                        # Calculate gravity using the timeline object directly (avoid async get call)
                        gravity = self._calculate_gravity_from_timeline(timeline)
                        gravity_score = gravity.total_gravity if hasattr(gravity, 'total_gravity') else (timeline.gravity_score or 0)
                        
                        health = TimelineHealth(
                            id=timeline.id,
                            name=timeline.name,
                            stability=timeline.stability,
                            surface_tension=timeline.surface_tension or 50.0,
                            price_yes=timeline.price_yes,
                            price_no=timeline.price_no,
                            osint_alignment=timeline.osint_alignment or 50.0,
                            logic_gap=timeline.logic_gap or 0.0,
                            gravity_score=gravity_score,
                            gravity_factors=getattr(gravity, 'gravity_factors', {}) if hasattr(gravity, 'gravity_factors') else {},
                            total_volume_usd=timeline.total_volume_usd or 0.0,
                            liquidity_depth_usd=timeline.liquidity_depth_usd or 0.0,
                            active_agent_count=timeline.active_agent_count or 0,
                            dominant_agent_id=None,  # TODO: Calculate from flaps
                            dominant_agent_name=None,
                            founder_id=timeline.founder_id,
                            founder_name=None,  # TODO: Load from user
                            founder_yield_rate=timeline.founder_yield_rate or 0.0,
                            decay_rate_per_hour=timeline.decay_rate_per_hour or self.BASE_DECAY_PER_HOUR,
                            hours_until_reaper=None,  # TODO: Calculate from stability/decay
                            has_active_paradox=timeline.has_active_paradox or False,
                            paradox_id=None,  # TODO: Load from paradox table
                            paradox_detonation_time=None,
                            connected_timeline_ids=timeline.connected_timeline_ids or []
                        )
                        health_list.append(health)
                    except Exception as e:
                        print(f"⚠️ Failed to convert timeline {timeline.id} to health: {e}")
                        import traceback
                        traceback.print_exc()
                        continue
                
                # Sort
                reverse = (sort_order == "desc")
                if sort_by == "gravity_score":
                    health_list.sort(key=lambda h: h.gravity_score, reverse=reverse)
                elif sort_by == "stability":
                    health_list.sort(key=lambda h: h.stability_score, reverse=reverse)
                
                return health_list[:limit]
            except Exception as e:
                print(f"⚠️ Failed to query timeline health: {e}")
                import traceback
                traceback.print_exc()
        
        # Fallback: return empty list
        return []
    
    def get_timeline_health(
        self,
        sort_by: str = "gravity_score",
        sort_order: str = "desc",
        min_gravity: float = 0,
        paradox_only: bool = False,
        limit: int = 20
    ) -> List[TimelineHealth]:
        """Get timeline health metrics (sync version, stub)."""
        return []
    
    async def count_timelines_async(
        self,
        min_gravity: float = 0,
        paradox_only: bool = False
    ) -> int:
        """Count timelines matching criteria (async version)."""
        if hasattr(self.timeline_repo, 'count'):
            try:
                if paradox_only:
                    timelines = await self.timeline_repo.get_with_paradox()
                    return len(timelines)
                else:
                    return await self.timeline_repo.count(min_gravity=min_gravity)
            except Exception as e:
                print(f"⚠️ Failed to count timelines: {e}")
        return 0
    
    def count_timelines(self, min_gravity: float = 0, paradox_only: bool = False) -> int:
        """Count timelines matching criteria (sync version, stub)."""
        return 0
    
    def get_timeline_health_by_id(self, timeline_id: str) -> Optional[TimelineHealth]:
        """Get health for a single timeline."""
        timeline = self.timeline_repo.get(timeline_id)
        gravity = self.calculate_gravity(timeline_id)
        
        return TimelineHealth(
            timeline_id=timeline_id,
            timeline_name=timeline.name,
            stability_score=timeline.stability,
            gravity_score=gravity.total_gravity,
            decay_rate_per_hour=self.BASE_DECAY_PER_HOUR,
            has_active_paradox=False,
            hours_until_reaper=None
        )
    
    def get_trending_timelines(self, limit: int = 10) -> List[GravityBreakdown]:
        """Get timelines with highest gravity."""
        return []
    
    def get_ripples(
        self,
        parent_id: Optional[str] = None,
        since: datetime = None,
        limit: int = 20
    ) -> List[Ripple]:
        """Get ripple events (forks spawned)."""
        # Stub: return empty list
        return []
    
    def count_ripples_since(self, since: datetime) -> int:
        """Count ripples since timestamp."""
        return 0
    
    def count_all_ripples(self) -> int:
        """Count all ripples ever."""
        return 0
    
    def get_fork_tree(self, timeline_id: str, depth: int = 3) -> dict:
        """Get fork tree structure."""
        return {"timeline_id": timeline_id, "children": [], "depth": depth}

```

## /Users/tobiasharber/Developer/prediction-market-monorepo.nosync/backend/engines/butterfly.py
```python
"""Butterfly Engine — causal state transition recording via Wing Flaps.

Every action that modifies market state passes through the Butterfly Engine.
Stability is clamped at write time: post_stability = clamp(pre + impact, 0, 1).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class WingFlapType(str, Enum):
    """Types of causal state transitions."""

    TRADE = "TRADE"
    SHIELD = "SHIELD"
    SABOTAGE = "SABOTAGE"
    RIPPLE = "RIPPLE"  # schema only — no source in 010b
    PARADOX = "PARADOX"
    ENTROPY = "ENTROPY"


@dataclass
class WingFlap:
    """Record of a single causal state transition."""

    flap_id: str
    theatre_id: str
    flap_type: WingFlapType
    agent_id: str | None  # None for system flaps (ENTROPY, RIPPLE)
    stability_impact: float  # signed: positive = stabilising
    pre_stability: float
    post_stability: float
    trigger_detail: dict
    timestamp: str


@dataclass
class TimelineState:
    """Mutable per-Theatre timeline state."""

    theatre_id: str
    stability: float = 1.0  # 0.0–1.0, starts at 1.0
    volume: float = 0.0  # cumulative trade volume (abs cost)
    flap_count: int = 0
    founders_yield_accrued: float = 0.0


def _clamp(value: float, lo: float, hi: float) -> float:
    """Clamp value to [lo, hi]."""
    return max(lo, min(hi, value))


class ButterflyEngine:
    """Records causal state transitions. Tracks TimelineState per Theatre."""

    def __init__(self) -> None:
        self._timelines: dict[str, TimelineState] = {}
        self._flaps: dict[str, list[WingFlap]] = {}
        self._flap_counter: int = 0

    def record_flap(
        self,
        flap_type: WingFlapType,
        theatre_id: str,
        agent_id: str | None,
        impact: float,
        trigger_detail: dict,
    ) -> WingFlap:
        """Record a Wing Flap. Updates TimelineState. Returns the flap."""
        timeline = self._get_or_create_timeline(theatre_id)

        pre_stability = timeline.stability
        post_stability = _clamp(pre_stability + impact, 0.0, 1.0)

        timeline.stability = post_stability
        timeline.flap_count += 1

        # Track trade volume
        if flap_type == WingFlapType.TRADE and "cost" in trigger_detail:
            timeline.volume += abs(trigger_detail["cost"])

        self._flap_counter += 1
        flap = WingFlap(
            flap_id=f"flp_{self._flap_counter:06d}",
            theatre_id=theatre_id,
            flap_type=flap_type,
            agent_id=agent_id,
            stability_impact=impact,
            pre_stability=pre_stability,
            post_stability=post_stability,
            trigger_detail=trigger_detail,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

        if theatre_id not in self._flaps:
            self._flaps[theatre_id] = []
        self._flaps[theatre_id].append(flap)

        return flap

    def get_timeline_state(self, theatre_id: str) -> TimelineState:
        """Get timeline state for a Theatre. Creates default if not exists."""
        return self._get_or_create_timeline(theatre_id)

    def get_flaps(self, theatre_id: str) -> list[WingFlap]:
        """Get all Wing Flaps for a Theatre (audit trail)."""
        return list(self._flaps.get(theatre_id, []))

    def compute_founders_yield(self, theatre_id: str) -> float:
        """Founder's Yield = stability × volume × 0.005."""
        timeline = self._get_or_create_timeline(theatre_id)
        return timeline.stability * timeline.volume * 0.005

    def _get_or_create_timeline(self, theatre_id: str) -> TimelineState:
        """Get existing timeline or create default."""
        if theatre_id not in self._timelines:
            self._timelines[theatre_id] = TimelineState(theatre_id=theatre_id)
        return self._timelines[theatre_id]
```

## /Users/tobiasharber/Developer/prediction-market-monorepo.nosync/backend/engines/entropy.py
```python
"""Entropy Engine — temporal decay of timeline stability.

Runs on ENTROPY heartbeat tick (60s cadence). Decay rate scales with
Logic Gap status. Sprint 1 defaults to "healthy".
"""
from __future__ import annotations

from backend.engines.butterfly import ButterflyEngine, WingFlap, WingFlapType
from backend.engines.config import EntropyConfig

_MULTIPLIERS = {
    "healthy": 1.0,
    "stressed": None,  # filled from config
    "danger": None,
    "critical": None,
}


class EntropyEngine:
    """Temporal decay of timeline stability."""

    def __init__(self, config: EntropyConfig, butterfly: ButterflyEngine) -> None:
        self._config = config
        self._butterfly = butterfly

    def tick(
        self, theatre_id: str, logic_gap_status: str = "healthy"
    ) -> WingFlap:
        """Apply decay to timeline stability. Returns ENTROPY WingFlap."""
        rate = self.get_effective_decay_rate(logic_gap_status)
        impact = -rate  # always negative — decay is destabilising

        return self._butterfly.record_flap(
            flap_type=WingFlapType.ENTROPY,
            theatre_id=theatre_id,
            agent_id=None,
            impact=impact,
            trigger_detail={
                "logic_gap_status": logic_gap_status,
                "effective_decay_rate": rate,
            },
        )

    def get_effective_decay_rate(self, logic_gap_status: str) -> float:
        """Compute decay rate scaled by Logic Gap status."""
        base = self._config.base_decay_rate
        status = logic_gap_status.lower()

        if status == "healthy":
            return base
        if status == "stressed":
            return base * self._config.stressed_multiplier
        if status == "danger":
            return base * self._config.danger_multiplier
        if status == "critical":
            return base * self._config.critical_multiplier

        # Unknown status — defensive default
        return base
```

## /Users/tobiasharber/Developer/prediction-market-monorepo.nosync/backend/worker/tasks/entropy.py
```python
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
```

## /Users/tobiasharber/Developer/prediction-market-monorepo.nosync/backend/worker/game_loop.py
```python
"""
Echelon Game Loop - The Heartbeat of the Simulation

This runs continuously, ticking game mechanics:
- Entropy (stability decay)
- Paradox detection
- Polymarket market sync
- OSINT polling
- Agent decisions

Run with: python -m backend.worker.game_loop
"""

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from backend.database.connection import async_session_maker, init_db
from backend.worker.tasks.entropy import EntropyTask
from backend.worker.tasks.paradox import ParadoxTask
from backend.worker.tasks.market_sync import MarketSyncTask
from backend.worker.tasks.agent_tick import AgentTickTask
from backend.worker.tasks.genesis import run_genesis_task

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger('echelon.gameloop')


class GameLoop:
    """
    The heartbeat of Echelon.
    
    Runs multiple tasks at different intervals:
    - Entropy: Every 60 seconds
    - Paradox scan: Every 30 seconds
    - Market sync: Every 10 seconds
    - Agent tick: Every 5 seconds
    """
    
    def __init__(self):
        self.running = False
        self.tick_count = 0
        self.start_time: Optional[datetime] = None
        
        # Task instances
        self.entropy_task = EntropyTask()
        self.paradox_task = ParadoxTask()
        self.market_task = MarketSyncTask()
        self.agent_task = AgentTickTask()
        
        # Task intervals (in seconds)
        self.intervals = {
            'entropy': 60,      # Decay stability every minute
            'paradox': 30,      # Check for breaches every 30s
            'market': 10,       # Sync prices every 10s
            'agent': 5,         # Agent decisions every 5s
            'genesis': 300,     # Phoenix protocol every 5 minutes
        }
        
        # Last run times (timezone-aware)
        # Use epoch start instead of datetime.min to avoid timezone issues
        min_time = datetime(1970, 1, 1, tzinfo=timezone.utc)
        self.last_run = {
            'entropy': min_time,
            'paradox': min_time,
            'market': min_time,
            'agent': min_time,
            'genesis': min_time,
        }
    
    async def start(self):
        """Start the game loop."""
        logger.info("=" * 60)
        logger.info("ECHELON GAME LOOP STARTING")
        logger.info("=" * 60)
        
        # Initialise database
        await init_db()
        logger.info("Database connection established")
        
        self.running = True
        self.start_time = datetime.now(timezone.utc)
        
        logger.info(f"Task intervals: {self.intervals}")
        logger.info("Game loop active. Press Ctrl+C to stop.")
        logger.info("-" * 60)
        
        try:
            await self._run_loop()
        except asyncio.CancelledError:
            logger.info("Game loop cancelled")
        except Exception as e:
            logger.error(f"Game loop error: {e}", exc_info=True)
        finally:
            self.running = False
            logger.info("Game loop stopped")
    
    async def _run_loop(self):
        """Main loop - runs forever until cancelled."""
        while self.running:
            self.tick_count += 1
            now = datetime.now(timezone.utc)
            
            # Create database session for this tick
            async with async_session_maker() as session:
                try:
                    # Run tasks that are due
                    await self._run_due_tasks(session, now)
                    await session.commit()
                except Exception as e:
                    logger.error(f"Tick {self.tick_count} error: {e}")
                    await session.rollback()
            
            # Sleep until next tick (1 second resolution)
            await asyncio.sleep(1)
    
    async def _run_due_tasks(self, session, now: datetime):
        """Run any tasks that are due based on their intervals."""
        
        # Entropy decay
        if self._is_due('entropy', now):
            await self._run_task('entropy', self.entropy_task.tick, session)
        
        # Paradox detection
        if self._is_due('paradox', now):
            await self._run_task('paradox', self.paradox_task.tick, session)
        
        # Market sync (Polymarket)
        if self._is_due('market', now):
            await self._run_task('market', self.market_task.tick, session)
        
        # Agent decisions
        if self._is_due('agent', now):
            await self._run_task('agent', self.agent_task.tick, session)

        # Phoenix protocol (genesis)
        if self._is_due('genesis', now):
            await self._run_task('genesis', self._genesis_task, session)
    
    def _is_due(self, task_name: str, now: datetime) -> bool:
        """Check if a task is due to run."""
        interval = timedelta(seconds=self.intervals[task_name])
        return now - self.last_run[task_name] >= interval
    
    async def _run_task(self, task_name: str, task_fn, session):
        """Run a task and update its last run time."""
        try:
            start = datetime.now(timezone.utc)
            result = await task_fn(session)
            elapsed = (datetime.now(timezone.utc) - start).total_seconds()
            
            self.last_run[task_name] = datetime.now(timezone.utc)
            
            if result:
                logger.info(f"[{task_name.upper():8}] {result} ({elapsed:.2f}s)")
            
        except Exception as e:
            logger.error(f"[{task_name.upper():8}] Failed: {e}")

    async def _genesis_task(self, session):
        """Phoenix Protocol - ensure minimum timelines exist."""
        try:
            result = await run_genesis_task()
            # Only log if we spawned timelines
            if result and result.get("spawned", 0) > 0:
                logger.info(f"Genesis: Spawned {result['spawned']} timelines")
            return result
        except Exception as e:
            logger.error(f"Genesis task error: {e}")
            raise
    
    def stop(self):
        """Stop the game loop."""
        self.running = False


async def main():
    """Entry point for the game loop."""
    loop = GameLoop()
    
    try:
        await loop.start()
    except KeyboardInterrupt:
        logger.info("Shutdown requested")
        loop.stop()


if __name__ == "__main__":
    asyncio.run(main())

```

## /Users/tobiasharber/Developer/prediction-market-monorepo.nosync/backend/database/models.py (WingFlapType + WingFlap section)
```python
"""
SQLAlchemy Models for Echelon
==============================

All database models for the Echelon prediction market platform.
Uses SQLAlchemy 2.0 async-compatible syntax.
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    String, Integer, Float, Boolean, DateTime, Text, JSON,
    ForeignKey, Enum as SQLEnum, Index
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import ARRAY
import enum
import uuid

from .connection import Base

# ============================================
# ENUMS
# ============================================

class AgentArchetype(str, enum.Enum):
    SHARK = "SHARK"
    SPY = "SPY"
    DIPLOMAT = "DIPLOMAT"
    SABOTEUR = "SABOTEUR"
    WHALE = "WHALE"
    DEGEN = "DEGEN"

class WingFlapType(str, enum.Enum):
    TRADE = "TRADE"
    SHIELD = "SHIELD"
    SABOTAGE = "SABOTAGE"
    RIPPLE = "RIPPLE"
    PARADOX = "PARADOX"
    FOUNDER_YIELD = "FOUNDER_YIELD"
    ENTROPY = "ENTROPY"  # System-generated stability decay

class ParadoxStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    EXTRACTING = "EXTRACTING"
    DETONATED = "DETONATED"
    RESOLVED = "RESOLVED"

class SeverityClass(str, enum.Enum):
    CLASS_1_CRITICAL = "CLASS_1_CRITICAL"
    CLASS_2_SEVERE = "CLASS_2_SEVERE"
    CLASS_3_MODERATE = "CLASS_3_MODERATE"
    CLASS_4_MINOR = "CLASS_4_MINOR"

# ============================================
# USER
# ============================================

class User(Base):
    __tablename__ = "users"
    
    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    tier: Mapped[str] = mapped_column(String(20), default="free")
    balance_usdc: Mapped[float] = mapped_column(Float, default=0.0)
    balance_echelon: Mapped[int] = mapped_column(Integer, default=0)
    wallet_address: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    agents: Mapped[List["Agent"]] = relationship(back_populates="owner")
    positions: Mapped[List["UserPosition"]] = relationship(back_populates="user")
    watchlist_items: Mapped[List["WatchlistItem"]] = relationship(back_populates="user")
    private_forks: Mapped[List["PrivateFork"]] = relationship(back_populates="user")

# ============================================
# TIMELINE
# ============================================

class Timeline(Base):
    __tablename__ = "timelines"
    
    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    narrative: Mapped[str] = mapped_column(Text)
    keywords: Mapped[List[str]] = mapped_column(ARRAY(String), default=[])
    
    # Core metrics
    stability: Mapped[float] = mapped_column(Float, default=50.0)
    surface_tension: Mapped[float] = mapped_column(Float, default=50.0)
    price_yes: Mapped[float] = mapped_column(Float, default=0.5)
    price_no: Mapped[float] = mapped_column(Float, default=0.5)
    
    # OSINT alignment
    osint_alignment: Mapped[float] = mapped_column(Float, default=50.0)
    logic_gap: Mapped[float] = mapped_column(Float, default=0.0)
    
    # Gravity
    gravity_score: Mapped[float] = mapped_column(Float, default=0.0)
    gravity_factors: Mapped[dict] = mapped_column(JSON, default={})
    
    # Liquidity
    total_volume_usd: Mapped[float] = mapped_column(Float, default=0.0)
    liquidity_depth_usd: Mapped[float] = mapped_column(Float, default=0.0)
    active_agent_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Decay
    decay_rate_per_hour: Mapped[float] = mapped_column(Float, default=1.0)
    decay_multiplier: Mapped[float] = mapped_column(Float, default=1.0)
    
    # Founder
    founder_id: Mapped[Optional[str]] = mapped_column(String(50), ForeignKey("users.id"), nullable=True)
    founder_yield_rate: Mapped[float] = mapped_column(Float, default=0.001)
    
    # Relationships
    parent_timeline_id: Mapped[Optional[str]] = mapped_column(String(50), ForeignKey("timelines.id"), nullable=True)
    connected_timeline_ids: Mapped[List[str]] = mapped_column(ARRAY(String), default=[])
    
    # Status
    has_active_paradox: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Relationships
    wing_flaps: Mapped[List["WingFlap"]] = relationship(back_populates="timeline")
    paradoxes: Mapped[List["Paradox"]] = relationship(back_populates="timeline")
    
    # Indexes
    __table_args__ = (
        Index("ix_timelines_gravity", "gravity_score"),
        Index("ix_timelines_stability", "stability"),
        Index("ix_timelines_active", "is_active"),
    )

# ============================================
# AGENT
# ============================================

class Agent(Base):
    __tablename__ = "agents"
    
    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    archetype: Mapped[AgentArchetype] = mapped_column(SQLEnum(AgentArchetype))
    tier: Mapped[int] = mapped_column(Integer, default=1)
    level: Mapped[int] = mapped_column(Integer, default=1)
    
    # Status
    sanity: Mapped[int] = mapped_column(Integer, default=100)
    max_sanity: Mapped[int] = mapped_column(Integer, default=100)
    is_alive: Mapped[bool] = mapped_column(Boolean, default=True)
    death_cause: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Owner
    owner_id: Mapped[str] = mapped_column(String(50), ForeignKey("users.id"))
    owner: Mapped["User"] = relationship(back_populates="agents")
    
    # Wallet
    wallet_address: Mapped[str] = mapped_column(String(100))
    
    # Performance
    total_pnl_usd: Mapped[float] = mapped_column(Float, default=0.0)
    win_rate: Mapped[float] = mapped_column(Float, default=0.0)
    trades_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Genome (for breeding/evolution)
    genome: Mapped[dict] = mapped_column(JSON, default={})
    
    # Lineage
    parent_agent_ids: Mapped[List[str]] = mapped_column(ARRAY(String), default=[])
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    wing_flaps: Mapped[List["WingFlap"]] = relationship(back_populates="agent")
    
    # Indexes
    __table_args__ = (
        Index("ix_agents_owner", "owner_id"),
        Index("ix_agents_archetype", "archetype"),
        Index("ix_agents_alive", "is_alive"),
    )

# ============================================
# WING FLAP (Causality Event)
# ============================================

# Helper function for WingFlap default timestamp (must be defined outside class)
def _wingflap_default_timestamp() -> datetime:
    """Return a naive UTC datetime for database compatibility."""
    return datetime.utcnow().replace(tzinfo=None)

class WingFlap(Base):
    __tablename__ = "wing_flaps"
    
    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    # Default timestamp (naive datetime for TIMESTAMP WITHOUT TIME ZONE)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=_wingflap_default_timestamp, index=True)
    
    # Timeline
    timeline_id: Mapped[str] = mapped_column(String(50), ForeignKey("timelines.id"), index=True)
    timeline: Mapped["Timeline"] = relationship(back_populates="wing_flaps")
    
    # Agent
    agent_id: Mapped[str] = mapped_column(String(50), ForeignKey("agents.id"), index=True)
    agent: Mapped["Agent"] = relationship(back_populates="wing_flaps")
    
    # Event details
    flap_type: Mapped[WingFlapType] = mapped_column(SQLEnum(WingFlapType))
    action: Mapped[str] = mapped_column(Text)
    
    # Impact
    stability_delta: Mapped[float] = mapped_column(Float)
    direction: Mapped[str] = mapped_column(String(20))  # ANCHOR or DESTABILISE
    volume_usd: Mapped[float] = mapped_column(Float)
    
    # State after flap
    timeline_stability: Mapped[float] = mapped_column(Float)
    timeline_price: Mapped[float] = mapped_column(Float)
    
    # Ripple
    spawned_ripple: Mapped[bool] = mapped_column(Boolean, default=False)
    ripple_timeline_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Founder yield
    founder_yield_earned: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Indexes
    __table_args__ = (
        Index("ix_wing_flaps_timeline_time", "timeline_id", "timestamp"),
        Index("ix_wing_flaps_agent_time", "agent_id", "timestamp"),
        Index("ix_wing_flaps_type", "flap_type"),
    )

# ============================================
# PARADOX (Containment Breach)
# ============================================

class Paradox(Base):
    __tablename__ = "paradoxes"
    
    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    
    # Timeline
    timeline_id: Mapped[str] = mapped_column(String(50), ForeignKey("timelines.id"), index=True)
    timeline: Mapped["Timeline"] = relationship(back_populates="paradoxes")
    
    # Status
    status: Mapped[ParadoxStatus] = mapped_column(SQLEnum(ParadoxStatus), default=ParadoxStatus.ACTIVE)
    severity_class: Mapped[SeverityClass] = mapped_column(SQLEnum(SeverityClass))
    logic_gap: Mapped[float] = mapped_column(Float)
    
    # Timing
    spawned_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    detonation_time: Mapped[datetime] = mapped_column(DateTime)
    
    # Decay
    decay_multiplier: Mapped[float] = mapped_column(Float, default=5.0)
    
    # Costs
    extraction_cost_usdc: Mapped[float] = mapped_column(Float)
    extraction_cost_echelon: Mapped[int] = mapped_column(Integer)
    carrier_sanity_cost: Mapped[int] = mapped_column(Integer)
    
    # Carrier
    carrier_agent_id: Mapped[Optional[str]] = mapped_column(String(50), ForeignKey("agents.id"), nullable=True)
    
    # Resolution
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    resolution_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Indexes
    __table_args__ = (
        Index("ix_paradoxes_status", "status"),
```
