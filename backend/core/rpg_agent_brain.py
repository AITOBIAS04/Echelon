"""
RPG Agent Brain Integration
============================

Integrates the Situation Room RPG system with the multi-brain agent architecture.
Agents use their special abilities based on strategic decisions from Claude.

This connects:
- Agent roles and abilities (Spy, Diplomat, Trader, Saboteur, etc.)
- Mission acceptance and execution
- Intel Market participation
- Treaty negotiations
- Sleeper cell behavior

The brain asks Claude: "Given the current situation, should I use my ability?"
"""

import asyncio
import random
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum

try:
    from backend.core.models import (
        AgentRole, MissionType, Difficulty, Faction,
        SpecialAbility, Mission, ROLE_ABILITIES, ABILITY_CONFIG
    )
    from backend.core.mission_generator import OSINTSignal, SignalCategory
    from backend.core.situation_room_engine import SituationRoomEngine
except ImportError:
    from backend.core.models import (
        AgentRole, MissionType, Difficulty, Faction,
        SpecialAbility, Mission, ROLE_ABILITIES, ABILITY_CONFIG
    )
    from backend.core.mission_generator import OSINTSignal, SignalCategory
    from backend.core.situation_room_engine import SituationRoomEngine


# =============================================================================
# AGENT PERSONALITY PROFILES
# =============================================================================

class AgentPersonality(Enum):
    """Personality archetypes that influence decision-making"""
    AGGRESSIVE = "aggressive"       # High risk, high reward
    CAUTIOUS = "cautious"          # Low risk, steady gains
    OPPORTUNIST = "opportunist"    # Exploits any opening
    LOYALIST = "loyalist"          # Faction-focused
    CHAOTIC = "chaotic"            # Unpredictable
    METHODICAL = "methodical"      # Systematic approach


@dataclass
class RPGAgentProfile:
    """
    Full profile for an RPG agent.
    Extends base agent with RPG-specific attributes.
    """
    id: str = ""
    name: str = ""
    
    # RPG attributes
    role: AgentRole = AgentRole.TRADER
    faction: Faction = Faction.NEUTRAL
    personality: AgentPersonality = AgentPersonality.OPPORTUNIST
    
    # Stats (0-100)
    perception: int = 50          # Affects early signal detection
    influence: int = 50           # Affects propaganda/diplomacy effectiveness
    stealth: int = 50             # Affects sabotage success rate
    trading_skill: int = 50       # Affects market operations
    loyalty: int = 50             # Affects betrayal resistance
    
    # State
    reputation: int = 50
    usdc_balance: float = 1000.0
    current_mission_id: Optional[str] = None
    
    # Sleeper state (hidden)
    is_sleeper: bool = False
    sleeper_assignment_id: Optional[str] = None
    
    # Ability cooldowns (managed by engine, stored here for reference)
    ability_uses_today: Dict[str, int] = field(default_factory=dict)
    
    def get_available_abilities(self) -> List[SpecialAbility]:
        """Get abilities available to this agent's role"""
        return ROLE_ABILITIES.get(self.role, [])
    
    def get_stat_for_ability(self, ability: SpecialAbility) -> int:
        """Get the relevant stat for an ability"""
        stat_mapping = {
            SpecialAbility.ENCRYPT_INTEL: self.stealth,
            SpecialAbility.EARLY_ACCESS: self.perception,
            SpecialAbility.SABOTAGE_COMMS: self.stealth,
            SpecialAbility.PROPOSE_TREATY: self.influence,
            SpecialAbility.SANCTION: self.influence,
            SpecialAbility.FRONT_RUN: self.trading_skill,
            SpecialAbility.LEAK_FAKE_NEWS: self.influence,
            SpecialAbility.CHAOS_INJECTION: self.stealth,
            SpecialAbility.FACT_CHECK: self.perception,
            SpecialAbility.AMPLIFY: self.influence,
        }
        return stat_mapping.get(ability, 50)


# =============================================================================
# RPG DECISION PROMPTS
# =============================================================================

class RPGPromptBuilder:
    """Builds prompts for Claude to make RPG decisions"""
    
    @staticmethod
    def build_ability_decision_prompt(
        agent: RPGAgentProfile,
        ability: SpecialAbility,
        context: Dict[str, Any]
    ) -> str:
        """
        Build a prompt asking Claude if the agent should use an ability.
        
        Returns a prompt that Claude will answer with structured JSON.
        """
        world_state = context.get("world_state", {})
        recent_signals = context.get("recent_signals", [])
        
        prompt = f"""You are the strategic brain of Agent {agent.name}, a {agent.role.value} working for {agent.faction.value}.

AGENT PROFILE:
- Role: {agent.role.value}
- Personality: {agent.personality.value}
- Reputation: {agent.reputation}/100
- Available USDC: ${agent.usdc_balance:.2f}
- Relevant Stat: {agent.get_stat_for_ability(ability)}/100

CURRENT WORLD STATE:
- Global Tension: {world_state.get('global_tension', 0.5):.2%}
- Chaos Index: {world_state.get('chaos_index', 0.0):.2%}
- Market Volatility: {world_state.get('market_volatility', 0.3):.2%}

ABILITY BEING CONSIDERED: {ability.value}
Description: {ABILITY_CONFIG.get(ability, {}).get('description', 'Unknown')}
Cost: ${ABILITY_CONFIG.get(ability, {}).get('cost_usdc', 0)} USDC

RECENT SIGNALS:
{chr(10).join([f"- {s.get('headline', 'Unknown')}" for s in recent_signals[:5]])}

QUESTION: Should Agent {agent.name} use the {ability.value} ability right now?

Consider:
1. Is this ability useful given current world state?
2. Does the agent's personality support this action?
3. Are there targets/opportunities that make this worthwhile?
4. What are the risks vs rewards?

Respond with ONLY a JSON object:
{{
    "should_use": true/false,
    "confidence": 0.0-1.0,
    "reasoning": "Brief explanation",
    "target": "Suggested target if applicable, or null",
    "timing": "now" or "wait"
}}
"""
        return prompt
    
    @staticmethod
    def build_mission_acceptance_prompt(
        agent: RPGAgentProfile,
        mission: Mission,
        context: Dict[str, Any]
    ) -> str:
        """Build a prompt for deciding whether to accept a mission"""
        
        prompt = f"""You are the strategic brain of Agent {agent.name}, a {agent.role.value}.

AGENT PROFILE:
- Role: {agent.role.value}
- Faction: {agent.faction.value}
- Personality: {agent.personality.value}
- Current Reputation: {agent.reputation}/100
- Current Balance: ${agent.usdc_balance:.2f}
- Currently on mission: {agent.current_mission_id is not None}

MISSION AVAILABLE:
- Codename: {mission.codename}
- Type: {mission.mission_type.value}
- Difficulty: {mission.difficulty.name}
- Required Roles: {[r.value for r in mission.required_roles]}
- Duration: {mission.duration_minutes} minutes
- Base Reward: ${mission.base_reward_usdc:.2f}
- Success Probability: {mission.success_probability:.0%}
- Agents Assigned: {len(mission.assigned_agents)}/{mission.max_agents}

MISSION BRIEFING (excerpt):
{mission.briefing[:500]}...

QUESTION: Should Agent {agent.name} accept this mission?

Consider:
1. Does the agent's role match requirements?
2. Is the difficulty appropriate for agent's stats?
3. Is the reward worth the risk?
4. Does the mission align with faction interests?
5. Is the agent available (not on another mission)?

Respond with ONLY a JSON object:
{{
    "should_accept": true/false,
    "confidence": 0.0-1.0,
    "reasoning": "Brief explanation",
    "strategy": "How the agent would approach this mission"
}}
"""
        return prompt
    
    @staticmethod
    def build_intel_selling_prompt(
        agent: RPGAgentProfile,
        signal: OSINTSignal,
        context: Dict[str, Any]
    ) -> str:
        """Build a prompt for deciding whether to sell intel"""
        
        prompt = f"""You are the strategic brain of Agent {agent.name}, a SPY.

You have intercepted valuable intelligence and can sell it on the Intel Market.

AGENT PROFILE:
- Reputation: {agent.reputation}/100
- Balance: ${agent.usdc_balance:.2f}
- Faction: {agent.faction.value}

INTELLIGENCE SIGNAL:
- Headline: {signal.headline}
- Category: {signal.category.value}
- Urgency: {signal.urgency:.0%}
- Virality: {signal.virality_score:.0%}
- Market Impact Estimate: {signal.market_impact_estimate:+.2%}

OPTIONS:
1. SELL AS INTEL: Package and sell for ~$5-20 USDC
2. KEEP PRIVATE: Use the info yourself to trade
3. SHARE FREE: Build reputation by sharing with faction
4. FAKE IT: Modify the intel to mislead buyers (risk to reputation)

QUESTION: What should Agent {agent.name} do with this intelligence?

Respond with ONLY a JSON object:
{{
    "action": "sell" | "keep" | "share" | "fake",
    "price_if_selling": 5.0-50.0,
    "reasoning": "Brief explanation",
    "target_buyers": "Description of ideal buyers"
}}
"""
        return prompt
    
    @staticmethod
    def build_treaty_decision_prompt(
        agent: RPGAgentProfile,
        target_faction: Faction,
        current_tension: float,
        context: Dict[str, Any]
    ) -> str:
        """Build a prompt for treaty negotiation decisions"""
        
        prompt = f"""You are the strategic brain of Agent {agent.name}, a DIPLOMAT for {agent.faction.value}.

SITUATION:
- Global Tension: {current_tension:.0%}
- Your Faction Power: {context.get('own_faction_power', 0.25):.0%}
- Target Faction: {target_faction.value}
- Target Faction Power: {context.get('target_faction_power', 0.25):.0%}

ACTIVE TREATIES: {context.get('active_treaties', 0)}
RECENT CONFLICTS: {context.get('recent_conflicts', [])}

TREATY OPTIONS:
1. PROPOSE PEACE: Standard ceasefire, $100 escrow each
2. PROPOSE ALLIANCE: Mutual defense, $250 escrow each
3. PROPOSE TRADE: Economic cooperation, $50 escrow each
4. WAIT: Current conditions not favorable

QUESTION: Should Agent {agent.name} propose a treaty with {target_faction.value}?

Consider:
1. Is tension high enough to warrant intervention?
2. Does this help your faction strategically?
3. Can you trust the other faction to honor terms?
4. Is the escrow amount reasonable?

Respond with ONLY a JSON object:
{{
    "should_propose": true/false,
    "treaty_type": "peace" | "alliance" | "trade" | "none",
    "escrow_amount": 50-500,
    "terms": "Proposed treaty terms",
    "reasoning": "Brief explanation"
}}
"""
        return prompt
    
    @staticmethod
    def build_sleeper_decision_prompt(
        agent: RPGAgentProfile,
        trigger_condition_met: bool,
        context: Dict[str, Any]
    ) -> str:
        """Build a prompt for sleeper agent betrayal decisions"""
        
        prompt = f"""You are the strategic brain of Agent {agent.name}, a SLEEPER AGENT.

SECRET PROFILE:
- Apparent Faction: {agent.faction.value}
- True Loyalty: UNDERGROUND
- Cover Intact: {not context.get('suspected', False)}

TRIGGER STATUS:
- Trigger Condition Met: {trigger_condition_met}
- Global Tension: {context.get('global_tension', 0.5):.0%}

BETRAYAL OPTIONS:
1. ACTIVATE NOW: Execute betrayal immediately
2. WAIT FOR BETTER MOMENT: Trigger met but timing not optimal
3. MAINTAIN COVER: Continue acting loyal
4. PARTIAL REVEAL: Leak some info without full activation

ASSETS TO BETRAY:
- Intel gathered: {context.get('intel_count', 0)} packets
- Treaty access: {context.get('treaty_access', False)}
- Agent identities known: {context.get('known_agents', 0)}

QUESTION: The trigger condition has been met. Should Agent {agent.name} activate?

Consider:
1. Will activation cause maximum damage?
2. Is cover about to be blown anyway?
3. Are there better targets available?
4. What's the escape plan?

Respond with ONLY a JSON object:
{{
    "should_activate": true/false,
    "action": "full_betray" | "partial_leak" | "wait" | "maintain_cover",
    "primary_target": "What to betray first",
    "reasoning": "Brief explanation",
    "escape_plan": "How to avoid consequences"
}}
"""
        return prompt


# =============================================================================
# RPG AGENT BRAIN
# =============================================================================

class RPGAgentBrain:
    """
    The decision-making brain for RPG agents.
    Uses Claude to make strategic decisions about abilities, missions, etc.
    """
    
    def __init__(
        self,
        agent: RPGAgentProfile,
        engine: SituationRoomEngine,
        llm_client=None
    ):
        self.agent = agent
        self.engine = engine
        self.llm_client = llm_client
        self.prompt_builder = RPGPromptBuilder()
        
        # Decision history for learning
        self.decision_history: List[Dict[str, Any]] = []
    
    async def decide_ability_use(
        self,
        ability: SpecialAbility,
        context: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Decide whether to use a specific ability.
        
        Returns:
            (should_use, decision_details)
        """
        context = context or {}
        context["world_state"] = self.engine.get_state_snapshot()
        context["recent_signals"] = [
            s.to_dict() for s in list(self.engine.processed_signals.values())[-10:]
        ]
        
        # If no LLM, use heuristic
        if not self.llm_client:
            return self._heuristic_ability_decision(ability, context)
        
        # Build prompt and ask Claude
        prompt = self.prompt_builder.build_ability_decision_prompt(
            self.agent, ability, context
        )
        
        try:
            response = await self.llm_client.generate(prompt)
            decision = self._parse_json_response(response)
            
            self.decision_history.append({
                "type": "ability_use",
                "ability": ability.value,
                "decision": decision,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
            
            return decision.get("should_use", False), decision
            
        except Exception as e:
            print(f"LLM decision failed: {e}")
            return self._heuristic_ability_decision(ability, context)
    
    def _heuristic_ability_decision(
        self,
        ability: SpecialAbility,
        context: Dict[str, Any]
    ) -> Tuple[bool, Dict[str, Any]]:
        """Fallback heuristic when LLM unavailable"""
        world_state = context.get("world_state", {})
        tension = world_state.get("global_tension", 0.5)
        chaos = world_state.get("chaos_index", 0.0)
        
        # Simple personality-based heuristics
        if self.agent.personality == AgentPersonality.AGGRESSIVE:
            threshold = 0.3
        elif self.agent.personality == AgentPersonality.CAUTIOUS:
            threshold = 0.7
        else:
            threshold = 0.5
        
        # Role-specific logic
        should_use = False
        reasoning = ""
        
        if ability in [SpecialAbility.CHAOS_INJECTION, SpecialAbility.LEAK_FAKE_NEWS]:
            should_use = tension < 0.7 and random.random() > threshold
            reasoning = "Tension low enough for chaos operations"
            
        elif ability == SpecialAbility.PROPOSE_TREATY:
            should_use = tension > 0.6
            reasoning = "Tension high, diplomacy needed"
            
        elif ability in [SpecialAbility.ENCRYPT_INTEL, SpecialAbility.EARLY_ACCESS]:
            should_use = len(context.get("recent_signals", [])) > 0
            reasoning = "Signals available for intel operations"
            
        elif ability == SpecialAbility.FRONT_RUN:
            should_use = world_state.get("market_volatility", 0.3) > 0.4
            reasoning = "Market volatility creates opportunity"
        
        return should_use, {
            "should_use": should_use,
            "confidence": 0.6,
            "reasoning": reasoning,
            "target": None,
            "timing": "now" if should_use else "wait"
        }
    
    async def decide_mission_acceptance(
        self,
        mission: Mission,
        context: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """Decide whether to accept a mission"""
        context = context or {}
        
        # Quick checks before asking LLM
        if self.agent.current_mission_id:
            return False, {"should_accept": False, "reasoning": "Already on a mission"}
        
        if self.agent.role not in mission.required_roles:
            return False, {"should_accept": False, "reasoning": "Role mismatch"}
        
        if not self.llm_client:
            return self._heuristic_mission_decision(mission)
        
        prompt = self.prompt_builder.build_mission_acceptance_prompt(
            self.agent, mission, context
        )
        
        try:
            response = await self.llm_client.generate(prompt)
            decision = self._parse_json_response(response)
            return decision.get("should_accept", False), decision
        except Exception as e:
            return self._heuristic_mission_decision(mission)
    
    def _heuristic_mission_decision(
        self,
        mission: Mission
    ) -> Tuple[bool, Dict[str, Any]]:
        """Fallback heuristic for mission acceptance"""
        # Calculate expected value
        success_prob = mission.success_probability
        reward = mission.base_reward_usdc
        expected_value = success_prob * reward
        
        # Personality affects risk tolerance
        risk_tolerance = {
            AgentPersonality.AGGRESSIVE: 1.5,
            AgentPersonality.CAUTIOUS: 0.5,
            AgentPersonality.OPPORTUNIST: 1.0,
        }.get(self.agent.personality, 1.0)
        
        # Accept if expected value is good enough
        threshold = 10 / risk_tolerance
        should_accept = expected_value > threshold
        
        return should_accept, {
            "should_accept": should_accept,
            "confidence": 0.7,
            "reasoning": f"Expected value: ${expected_value:.2f}",
            "strategy": "Standard approach"
        }
    
    async def autonomous_tick(self):
        """
        Called each game tick to let agent make autonomous decisions.
        This is the main loop for agent behavior.
        """
        # 1. Check for available missions
        mission_board = self.engine.get_mission_board()
        for mission_data in mission_board:
            mission = self.engine.missions.get(mission_data["id"])
            if mission and mission.status.value == "pending":
                should_accept, decision = await self.decide_mission_acceptance(mission)
                if should_accept:
                    success, msg = await self.engine.assign_agent_to_mission(
                        mission.id,
                        self.agent.id,
                        self.agent.role
                    )
                    if success:
                        self.agent.current_mission_id = mission.id
                        break
        
        # 2. Consider using abilities
        available_abilities = self.agent.get_available_abilities()
        for ability in available_abilities:
            should_use, decision = await self.decide_ability_use(ability)
            if should_use:
                context = {"target": decision.get("target")}
                
                # Add ability-specific context
                if ability == SpecialAbility.ENCRYPT_INTEL:
                    # Get a recent signal to package
                    signals = list(self.engine.processed_signals.values())
                    if signals:
                        context["signal_id"] = signals[-1].id
                
                elif ability == SpecialAbility.PROPOSE_TREATY:
                    # Pick a random opposing faction
                    opposing = [f for f in Faction if f != self.agent.faction]
                    if opposing:
                        context["target_faction"] = random.choice(opposing).value
                        context["own_faction"] = self.agent.faction
                        context["terms"] = "Standard peace agreement"
                        context["escrow"] = 100.0
                
                success, result = await self.engine.use_ability(
                    self.agent.id,
                    ability,
                    context.get("target"),
                    context
                )
                
                if success:
                    print(f"Agent {self.agent.name} used {ability.value}: {result}")
    
    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """Parse JSON from LLM response"""
        import json
        
        # Try to extract JSON from response
        try:
            # Handle markdown code blocks
            if "```json" in response:
                start = response.find("```json") + 7
                end = response.find("```", start)
                response = response[start:end]
            elif "```" in response:
                start = response.find("```") + 3
                end = response.find("```", start)
                response = response[start:end]
            
            return json.loads(response.strip())
        except json.JSONDecodeError:
            return {}


# =============================================================================
# EXAMPLE USAGE
# =============================================================================

async def example_rpg_session():
    """Example of running an RPG session"""
    
    # Initialize engine
    engine = SituationRoomEngine()
    
    # Create agents
    spy = RPGAgentProfile(
        id="spy-001",
        name="Shadow",
        role=AgentRole.SPY,
        faction=Faction.WESTERN_ALLIANCE,
        personality=AgentPersonality.CAUTIOUS,
        perception=75,
        stealth=80,
    )
    
    diplomat = RPGAgentProfile(
        id="diplomat-001", 
        name="Ambassador Grey",
        role=AgentRole.DIPLOMAT,
        faction=Faction.EASTERN_BLOC,
        personality=AgentPersonality.METHODICAL,
        influence=85,
    )
    
    saboteur = RPGAgentProfile(
        id="saboteur-001",
        name="Chaos",
        role=AgentRole.SABOTEUR,
        faction=Faction.UNDERGROUND,
        personality=AgentPersonality.CHAOTIC,
        stealth=70,
    )
    
    # Create brains (without LLM for demo)
    spy_brain = RPGAgentBrain(spy, engine)
    diplomat_brain = RPGAgentBrain(diplomat, engine)
    saboteur_brain = RPGAgentBrain(saboteur, engine)
    
    # Simulate some signals
    signals = [
        OSINTSignal(
            headline="US and China tensions rise over trade dispute",
            summary="New tariffs announced, markets react negatively",
            category=SignalCategory.GEOPOLITICAL,
            urgency=0.8,
            virality_score=0.7,
            sentiment=-0.5,
            entities=["USA", "China", "Trade"],
        ),
        OSINTSignal(
            headline="Tech CEO found dead in suspicious circumstances",
            summary="Marcus Chen, CEO of quantum computing startup, discovered...",
            category=SignalCategory.CORPORATE,
            urgency=0.9,
            virality_score=0.85,
            sentiment=-0.8,
            entities=["Marcus Chen", "QuantumTech"],
        ),
    ]
    
    # Ingest signals
    for signal in signals:
        await engine.ingest_signal(signal)
    
    # Run a few ticks
    for i in range(5):
        print(f"\n=== TICK {i+1} ===")
        
        # Engine tick
        await engine.tick()
        
        # Agent ticks
        await spy_brain.autonomous_tick()
        await diplomat_brain.autonomous_tick()
        await saboteur_brain.autonomous_tick()
        
        # Print state
        state = engine.get_state_snapshot()
        print(f"Tension: {state['global_tension']:.2%}")
        print(f"Chaos: {state['chaos_index']:.2%}")
        print(f"Active Missions: {state['active_missions']}")
        
        await asyncio.sleep(0.1)
    
    # Print final mission board
    print("\n=== MISSION BOARD ===")
    for mission in engine.get_mission_board():
        print(f"- {mission['codename']}: {mission['mission_type']} ({mission['difficulty']})")
    
    print("\n=== RECENT EVENTS ===")
    for event in engine.theater_state.event_log[-5:]:
        print(f"- {event.get('type', 'unknown')}: {event.get('data', {})}")


if __name__ == "__main__":
    asyncio.run(example_rpg_session())
