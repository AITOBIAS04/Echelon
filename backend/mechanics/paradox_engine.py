from datetime import datetime, timedelta
from typing import Optional, List
import random
from ..schemas.paradox_schemas import (
    Paradox, SeverityClass, ParadoxStatus,
    ExtractionResult, DetonationEvent
)

class ParadoxEngine:
    """
    The Paradox Engine detects and manages Containment Breaches.
    
    Paradoxes spawn when market price diverges from OSINT reality.
    They accelerate timeline decay and must be extracted or the timeline dies.
    """
    
    # Thresholds
    LOGIC_GAP_THRESHOLD = 0.3  # 30% gap triggers paradox chance
    BASE_BREACH_PROBABILITY = 0.05  # 5% per tick at threshold
    
    # Decay
    PARADOX_DECAY_MULTIPLIER = 5.0
    
    def __init__(self, timeline_repo, agent_repo, butterfly_engine):
        self.timeline_repo = timeline_repo
        self.agent_repo = agent_repo
        self.butterfly_engine = butterfly_engine
        self.active_paradoxes: dict[str, Paradox] = {}
    
    # =========================================
    # BREACH DETECTION
    # =========================================
    
    def check_for_breach(self, timeline_id: str) -> Optional[Paradox]:
        """
        Check if a timeline should spawn a Paradox.
        
        Called every game tick (e.g., every 5 minutes).
        """
        timeline = self.timeline_repo.get(timeline_id)
        
        # Skip if already has paradox
        if timeline_id in self.active_paradoxes:
            return None
        
        # Get logic gap
        logic_gap = self.butterfly_engine.calculate_logic_gap(timeline_id)
        
        # No breach if gap is small
        if logic_gap < self.LOGIC_GAP_THRESHOLD:
            return None
        
        # Probability scales with gap
        # Gap of 0.6 = (0.6 - 0.3) * 0.05 / 0.3 = 5% chance
        excess_gap = logic_gap - self.LOGIC_GAP_THRESHOLD
        breach_probability = (excess_gap / 0.7) * self.BASE_BREACH_PROBABILITY
        
        if random.random() < breach_probability:
            return self._spawn_paradox(timeline_id, logic_gap)
        
        return None
    
    def _spawn_paradox(self, timeline_id: str, logic_gap: float) -> Paradox:
        """Create a new Paradox in the timeline."""
        timeline = self.timeline_repo.get(timeline_id)
        
        severity = self._classify_severity(logic_gap)
        hours = self._calculate_countdown(logic_gap)
        detonation_time = datetime.now() + timedelta(hours=hours)
        
        paradox = Paradox(
            id=f"PARADOX_{timeline_id}_{int(datetime.now().timestamp())}",
            timeline_id=timeline_id,
            timeline_name=timeline.name,
            status=ParadoxStatus.ACTIVE,
            severity_class=severity,
            logic_gap=logic_gap,
            spawned_at=datetime.now(),
            detonation_time=detonation_time,
            time_remaining_seconds=int(hours * 3600),
            decay_multiplier=self.PARADOX_DECAY_MULTIPLIER,
            extraction_cost_usdc=500 + (logic_gap * 1000),
            extraction_cost_echelon=100 + int(logic_gap * 400),
            carrier_sanity_cost=20 + int(logic_gap * 30),
            connected_timelines=timeline.connected_timeline_ids
        )
        
        # Store
        self.active_paradoxes[paradox.id] = paradox
        
        # Apply decay multiplier to timeline
        self.timeline_repo.set_decay_multiplier(
            timeline_id, 
            self.PARADOX_DECAY_MULTIPLIER
        )
        
        # Broadcast alert
        self._broadcast_breach_alert(paradox)
        
        return paradox
    
    def _classify_severity(self, gap: float) -> SeverityClass:
        if gap > 0.7: return SeverityClass.CLASS_1_CRITICAL
        if gap > 0.5: return SeverityClass.CLASS_2_SEVERE
        if gap > 0.4: return SeverityClass.CLASS_3_MODERATE
        return SeverityClass.CLASS_4_MINOR
    
    def _calculate_countdown(self, gap: float) -> float:
        """Higher gap = less time to react."""
        # Gap 0.3 = 6 hours, Gap 0.8 = 1 hour
        return max(1, 6 - (gap * 6))
    
    # =========================================
    # EXTRACTION
    # =========================================
    
    def attempt_extraction(
        self,
        paradox_id: str,
        agent_id: str,
        destination_timeline_id: str,
        user_id: str
    ) -> ExtractionResult:
        """
        Attempt to extract (move) a Paradox using an agent.
        
        Risk: Agent may die.
        Cost: USDC + $ECHELON + Agent Sanity
        """
        paradox = self.active_paradoxes.get(paradox_id)
        if not paradox:
            return ExtractionResult(
                success=False,
                agent_survived=True,
                message="Paradox not found or already resolved."
            )
        
        agent = self.agent_repo.get(agent_id)
        if not agent:
            return ExtractionResult(
                success=False,
                agent_survived=True,
                message="Agent not found."
            )
        
        # Validate destination
        if destination_timeline_id not in paradox.connected_timelines:
            return ExtractionResult(
                success=False,
                agent_survived=True,
                message="Invalid destination. Timeline not connected."
            )
        
        # Check agent sanity
        if agent.sanity < paradox.carrier_sanity_cost:
            return ExtractionResult(
                success=False,
                agent_survived=True,
                message=f"Agent sanity too low. Needs {paradox.carrier_sanity_cost}, has {agent.sanity}."
            )
        
        # Deduct costs
        # (In production, verify user has funds first)
        self._deduct_extraction_costs(user_id, paradox)
        
        # Deduct sanity
        agent.sanity -= paradox.carrier_sanity_cost
        self.agent_repo.update_sanity(agent_id, agent.sanity)
        
        # Calculate death risk
        death_risk = self._calculate_death_risk(agent, paradox)
        agent_died = random.random() < death_risk
        
        if agent_died:
            # Agent dies, paradox stays
            self.agent_repo.kill_agent(agent_id, cause="PARADOX_EXTRACTION_FAILURE")
            
            return ExtractionResult(
                success=False,
                agent_survived=False,
                message=f"Agent {agent.name} was lost during extraction. The Paradox remains.",
                agent_death_cause="Causality Feedback Loop - Agent consciousness fragmented."
            )
        
        # Success - move paradox
        self._move_paradox(paradox, destination_timeline_id)
        
        return ExtractionResult(
            success=True,
            agent_survived=True,
            agent_sanity_remaining=agent.sanity,
            message=f"Extraction successful. Paradox moved to {destination_timeline_id}.",
            new_timeline_id=destination_timeline_id,
            new_timeline_stability=self.timeline_repo.get(destination_timeline_id).stability
        )
    
    def _calculate_death_risk(self, agent, paradox: Paradox) -> float:
        """
        Death risk based on agent sanity and paradox severity.
        
        Low sanity + High severity = High death risk.
        """
        # Base risk from sanity (0 sanity = 100% risk)
        sanity_factor = (100 - agent.sanity) / 100
        
        # Severity multiplier
        severity_multipliers = {
            SeverityClass.CLASS_1_CRITICAL: 1.5,
            SeverityClass.CLASS_2_SEVERE: 1.2,
            SeverityClass.CLASS_3_MODERATE: 1.0,
            SeverityClass.CLASS_4_MINOR: 0.8,
        }
        severity_mod = severity_multipliers.get(paradox.severity_class, 1.0)
        
        # Agent level reduces risk
        level_mod = max(0.5, 1 - (agent.level * 0.05))  # Level 10 = 50% risk reduction
        
        # Final risk (capped at 95%)
        return min(0.95, sanity_factor * severity_mod * level_mod)
    
    def _move_paradox(self, paradox: Paradox, new_timeline_id: str):
        """Move Paradox to a new timeline."""
        old_timeline_id = paradox.timeline_id
        
        # Remove decay from old timeline
        self.timeline_repo.set_decay_multiplier(old_timeline_id, 1.0)
        
        # Update paradox
        paradox.timeline_id = new_timeline_id
        paradox.timeline_name = self.timeline_repo.get(new_timeline_id).name
        paradox.connected_timelines = self.timeline_repo.get(new_timeline_id).connected_timeline_ids
        
        # Apply decay to new timeline
        self.timeline_repo.set_decay_multiplier(new_timeline_id, self.PARADOX_DECAY_MULTIPLIER)
        
        # Broadcast move
        self._broadcast_paradox_moved(paradox, old_timeline_id)
    
    def _deduct_extraction_costs(self, user_id: str, paradox: Paradox):
        """Deduct USDC and $ECHELON from user."""
        # Implementation depends on your payment system
        pass
    
    # =========================================
    # DETONATION
    # =========================================
    
    def check_detonations(self):
        """
        Check all active paradoxes for detonation.
        
        Called every tick.
        """
        now = datetime.now()
        detonated = []
        
        for paradox_id, paradox in self.active_paradoxes.items():
            if now >= paradox.detonation_time:
                self._detonate(paradox)
                detonated.append(paradox_id)
        
        # Remove detonated
        for pid in detonated:
            del self.active_paradoxes[pid]
    
    def _detonate(self, paradox: Paradox) -> DetonationEvent:
        """
        Paradox timer hit zero. Everything burns.
        """
        timeline = self.timeline_repo.get(paradox.timeline_id)
        
        # Kill carrier agent if any
        agents_killed = []
        if paradox.carrier_agent_id:
            self.agent_repo.kill_agent(
                paradox.carrier_agent_id,
                cause="PARADOX_DETONATION"
            )
            agents_killed.append(paradox.carrier_agent_id)
        
        # Trigger Reality Reaper (burn all shards)
        burn_result = self.timeline_repo.trigger_reality_reaper(paradox.timeline_id)
        
        # Create detonation event
        event = DetonationEvent(
            paradox_id=paradox.id,
            timeline_id=paradox.timeline_id,
            detonated_at=datetime.now(),
            shards_burned=burn_result.shards_burned,
            total_value_burned_usd=burn_result.value_usd,
            agents_killed=agents_killed,
            saboteur_payouts=burn_result.saboteur_payouts
        )
        
        # Broadcast
        self._broadcast_detonation(event)
        
        return event
    
    # =========================================
    # TICK UPDATE
    # =========================================
    
    def tick(self):
        """
        Called every game tick to update all paradox timers.
        """
        now = datetime.now()
        
        for paradox in self.active_paradoxes.values():
            paradox.time_remaining_seconds = max(
                0,
                int((paradox.detonation_time - now).total_seconds())
            )
        
        # Check for detonations
        self.check_detonations()
    
    # =========================================
    # QUERIES
    # =========================================
    
    async def get_active_paradoxes_async(self) -> List[Paradox]:
        """Get all active paradoxes from database (async version)."""
        # Check if repository has async methods (real database)
        if hasattr(self.timeline_repo, 'session') and hasattr(self.timeline_repo.session, 'execute'):
            try:
                from ..database.models import Paradox as DBParadox, ParadoxStatus
                from sqlalchemy import select
                
                # Query active paradoxes from database
                query = select(DBParadox).where(DBParadox.status == ParadoxStatus.ACTIVE)
                result = await self.timeline_repo.session.execute(query)
                db_paradoxes = list(result.scalars().all())
                
                # Convert to Pydantic schemas
                paradox_list = []
                for db_paradox in db_paradoxes:
                    # Get timeline name
                    timeline = await self.timeline_repo.get(db_paradox.timeline_id)
                    timeline_name = timeline.name if timeline else f"Timeline {db_paradox.timeline_id[:8]}"
                    
                    # Calculate time remaining
                    now = datetime.now()
                    if db_paradox.detonation_time:
                        time_remaining = int((db_paradox.detonation_time - now).total_seconds())
                    else:
                        time_remaining = 0
                    
                    paradox = Paradox(
                        id=db_paradox.id,
                        timeline_id=db_paradox.timeline_id,
                        timeline_name=timeline_name,
                        status=db_paradox.status,
                        severity_class=db_paradox.severity_class,
                        logic_gap=db_paradox.logic_gap,
                        spawned_at=db_paradox.spawned_at,
                        detonation_time=db_paradox.detonation_time,
                        time_remaining_seconds=time_remaining,
                        decay_multiplier=db_paradox.decay_multiplier,
                        extraction_cost_usdc=db_paradox.extraction_cost_usdc,
                        extraction_cost_echelon=db_paradox.extraction_cost_echelon,
                        carrier_sanity_cost=db_paradox.carrier_sanity_cost,
                        carrier_agent_id=db_paradox.carrier_agent_id,
                        carrier_agent_name=None,  # TODO: Load agent name if carrier exists
                        carrier_agent_sanity=None,
                        connected_timelines=[]  # TODO: Load from timeline
                    )
                    paradox_list.append(paradox)
                
                return paradox_list
            except Exception as e:
                print(f"⚠️ Failed to query active paradoxes: {e}")
                import traceback
                traceback.print_exc()
        
        # Fallback: return in-memory paradoxes
        return list(self.active_paradoxes.values())
    
    def get_active_paradoxes(self) -> List[Paradox]:
        """Get all active paradoxes (sync version, in-memory)."""
        return list(self.active_paradoxes.values())
    
    def get_paradox(self, paradox_id: str) -> Optional[Paradox]:
        """Get a specific paradox."""
        return self.active_paradoxes.get(paradox_id)
    
    def get_paradox_for_timeline(self, timeline_id: str) -> Optional[Paradox]:
        """Get paradox affecting a specific timeline."""
        for paradox in self.active_paradoxes.values():
            if paradox.timeline_id == timeline_id:
                return paradox
        return None
    
    # =========================================
    # BROADCASTS
    # =========================================
    
    def _broadcast_breach_alert(self, paradox: Paradox):
        """Broadcast new breach to all connected clients."""
        pass
    
    def _broadcast_paradox_moved(self, paradox: Paradox, old_timeline_id: str):
        """Broadcast paradox movement."""
        pass
    
    def _broadcast_detonation(self, event: DetonationEvent):
        """Broadcast detonation event."""
        pass

