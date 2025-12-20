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
            timeline_stability=db_flap.timeline_stability,
            timeline_price=db_flap.timeline_price,
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

