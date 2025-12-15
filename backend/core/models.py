"""
Geopolitical Strategy RPG - Mission & Narrative Engine
=======================================================

Transforms OSINT signals into playable missions, objectives, and narrative events
that agents (Spies, Diplomats, Traders, Saboteurs) can execute.

Core Concepts:
- Missions: Generated from real-world OSINT data
- Objectives: Specific goals within missions
- Narratives: Story arcs that connect multiple missions
- Agents: Role-based actors with special abilities
- Betting: Users bet on mission outcomes and agent actions

The Theater (formerly War Room):
- Real-time mission board
- Agent deployment
- Narrative timeline
- Betting markets for each mission
"""

import asyncio
import uuid
import random
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod


# =============================================================================
# ENUMS & TYPES
# =============================================================================

class AgentRole(Enum):
    """Agent archetypes with unique capabilities"""
    SPY = "spy"                     # Intelligence gathering, early info access
    DIPLOMAT = "diplomat"           # Treaty creation, alliance management
    TRADER = "trader"               # Market manipulation, arbitrage
    SABOTEUR = "saboteur"           # Disruption, false flags, chaos
    JOURNALIST = "journalist"       # Truth-seeking, reputation-based
    PROPAGANDIST = "propagandist"   # Narrative spinning, market manipulation
    SLEEPER = "sleeper"             # Double agent, hidden objectives


class MissionType(Enum):
    """Types of missions generated from OSINT"""
    INTELLIGENCE = "intelligence"       # Gather info, verify signals
    ASSASSINATION = "assassination"     # Eliminate target (figuratively - market position)
    EXTRACTION = "extraction"           # Retrieve asset/information
    SABOTAGE = "sabotage"              # Disrupt operations
    DIPLOMACY = "diplomacy"            # Negotiate treaties, alliances
    PROPAGANDA = "propaganda"          # Influence public opinion
    MARKET_OP = "market_operation"     # Financial manipulation
    PROTECTION = "protection"          # Defend asset/position
    INVESTIGATION = "investigation"    # Uncover hidden truth
    COUP = "coup"                      # Major regime/market change


class MissionStatus(Enum):
    """Mission lifecycle states"""
    PENDING = "pending"         # Generated, not yet active
    ACTIVE = "active"           # In progress
    COMPLETED = "completed"     # Successfully finished
    FAILED = "failed"           # Failed to complete
    EXPIRED = "expired"         # Time ran out
    ABORTED = "aborted"         # Cancelled mid-mission


class Difficulty(Enum):
    """Mission difficulty tiers"""
    ROUTINE = 1         # Easy, high success rate
    STANDARD = 2        # Normal difficulty
    CHALLENGING = 3     # Requires skill
    CRITICAL = 4        # High stakes, high reward
    IMPOSSIBLE = 5      # Near-certain failure, legendary reward


class Faction(Enum):
    """Geopolitical factions for alliance/rivalry"""
    EASTERN_BLOC = "eastern_bloc"
    WESTERN_ALLIANCE = "western_alliance"
    NON_ALIGNED = "non_aligned"
    CORPORATE = "corporate"
    UNDERGROUND = "underground"
    NEUTRAL = "neutral"


# =============================================================================
# SPECIAL ABILITIES
# =============================================================================

class SpecialAbility(Enum):
    """Role-specific abilities that affect gameplay"""
    
    # Spy Abilities
    ENCRYPT_INTEL = "encrypt_intel"          # Create sellable info packets
    EARLY_ACCESS = "early_access"            # Get news 10 seconds early
    SABOTAGE_COMMS = "sabotage_comms"        # Block agent from receiving news
    DEAD_DROP = "dead_drop"                  # Anonymous information transfer
    IDENTITY_THEFT = "identity_theft"        # Impersonate another agent
    
    # Diplomat Abilities
    PROPOSE_TREATY = "propose_treaty"        # Create escrow peace contract
    SANCTION = "sanction"                    # Increase rival transaction costs
    IMMUNITY = "immunity"                    # Protection from one attack
    BACKCHANNEL = "backchannel"             # Secret communication
    VETO = "veto"                           # Block one action
    
    # Trader Abilities
    FRONT_RUN = "front_run"                 # Act on news before others
    MARKET_MAKE = "market_make"             # Provide liquidity for yield
    SHORT_SQUEEZE = "short_squeeze"         # Force position liquidations
    INSIDER_TRADE = "insider_trade"         # Use encrypted intel
    FLASH_CRASH = "flash_crash"             # Temporary market disruption
    
    # Saboteur Abilities
    FALSE_FLAG = "false_flag"               # Blame action on another faction
    LEAK_FAKE_NEWS = "leak_fake_news"       # Inject false high-virality event
    INFRASTRUCTURE_ATTACK = "infra_attack"  # Disable systems temporarily
    DOUBLE_AGENT = "double_agent"           # Secretly work for enemy
    CHAOS_INJECTION = "chaos_injection"     # Spike global tension
    
    # Journalist Abilities
    INVESTIGATE = "investigate"              # Uncover hidden information
    PUBLISH = "publish"                      # Broadcast to all agents
    SOURCE_PROTECTION = "source_protection"  # Anonymous tip handling
    FACT_CHECK = "fact_check"               # Verify/debunk claims
    
    # Propagandist Abilities
    SPIN = "spin"                           # Reframe narrative
    AMPLIFY = "amplify"                     # Boost signal virality
    SUPPRESS = "suppress"                   # Reduce signal visibility
    ASTROTURF = "astroturf"                 # Fake grassroots movement


# Ability configurations
ABILITY_CONFIG = {
    SpecialAbility.ENCRYPT_INTEL: {
        "cooldown_seconds": 300,
        "cost_usdc": 1.0,
        "roles": [AgentRole.SPY],
        "description": "Package intelligence for sale via x402"
    },
    SpecialAbility.EARLY_ACCESS: {
        "cooldown_seconds": 60,
        "cost_usdc": 0,
        "roles": [AgentRole.SPY],
        "description": "Receive OSINT signals 10 seconds before market"
    },
    SpecialAbility.PROPOSE_TREATY: {
        "cooldown_seconds": 3600,
        "cost_usdc": 50.0,  # Escrow requirement
        "roles": [AgentRole.DIPLOMAT],
        "description": "Create a smart contract peace bond"
    },
    SpecialAbility.LEAK_FAKE_NEWS: {
        "cooldown_seconds": 1800,
        "cost_usdc": 5.0,
        "roles": [AgentRole.SABOTEUR, AgentRole.PROPAGANDIST],
        "description": "Inject fabricated high-virality event"
    },
    SpecialAbility.FRONT_RUN: {
        "cooldown_seconds": 120,
        "cost_usdc": 2.0,
        "roles": [AgentRole.TRADER],
        "description": "Execute trade before news is public"
    },
    # ... more abilities
}


# Role to abilities mapping
ROLE_ABILITIES = {
    AgentRole.SPY: [
        SpecialAbility.ENCRYPT_INTEL,
        SpecialAbility.EARLY_ACCESS,
        SpecialAbility.SABOTAGE_COMMS,
        SpecialAbility.DEAD_DROP,
        SpecialAbility.IDENTITY_THEFT,
    ],
    AgentRole.DIPLOMAT: [
        SpecialAbility.PROPOSE_TREATY,
        SpecialAbility.SANCTION,
        SpecialAbility.IMMUNITY,
        SpecialAbility.BACKCHANNEL,
        SpecialAbility.VETO,
    ],
    AgentRole.TRADER: [
        SpecialAbility.FRONT_RUN,
        SpecialAbility.MARKET_MAKE,
        SpecialAbility.SHORT_SQUEEZE,
        SpecialAbility.INSIDER_TRADE,
        SpecialAbility.FLASH_CRASH,
    ],
    AgentRole.SABOTEUR: [
        SpecialAbility.FALSE_FLAG,
        SpecialAbility.LEAK_FAKE_NEWS,
        SpecialAbility.INFRASTRUCTURE_ATTACK,
        SpecialAbility.DOUBLE_AGENT,
        SpecialAbility.CHAOS_INJECTION,
    ],
    AgentRole.JOURNALIST: [
        SpecialAbility.INVESTIGATE,
        SpecialAbility.PUBLISH,
        SpecialAbility.SOURCE_PROTECTION,
        SpecialAbility.FACT_CHECK,
    ],
    AgentRole.PROPAGANDIST: [
        SpecialAbility.SPIN,
        SpecialAbility.AMPLIFY,
        SpecialAbility.SUPPRESS,
        SpecialAbility.ASTROTURF,
        SpecialAbility.LEAK_FAKE_NEWS,
    ],
    AgentRole.SLEEPER: [
        SpecialAbility.DOUBLE_AGENT,
        SpecialAbility.IDENTITY_THEFT,
    ],
}


# =============================================================================
# DATA MODELS
# =============================================================================

@dataclass
class MissionObjective:
    """A specific goal within a mission"""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    description: str = ""
    target: Optional[str] = None          # Target entity (agent, market, faction)
    success_condition: str = ""           # What determines success
    reward_usdc: float = 0.0
    reward_reputation: int = 0
    is_optional: bool = False
    is_completed: bool = False
    completed_by: Optional[str] = None    # Agent ID who completed it
    completed_at: Optional[datetime] = None


@dataclass
class Mission:
    """A mission generated from OSINT data"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    # Core info
    codename: str = ""                    # "Operation Crimson Dawn"
    title: str = ""                       # Human readable title
    briefing: str = ""                    # Full mission description
    mission_type: MissionType = MissionType.INTELLIGENCE
    difficulty: Difficulty = Difficulty.STANDARD
    
    # Timing
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    starts_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    duration_minutes: int = 60
    
    # Status
    status: MissionStatus = MissionStatus.PENDING
    
    # Requirements
    required_roles: List[AgentRole] = field(default_factory=list)
    min_agents: int = 1
    max_agents: int = 5
    required_faction: Optional[Faction] = None
    
    # Objectives
    objectives: List[MissionObjective] = field(default_factory=list)
    primary_objective: Optional[str] = None
    
    # Rewards
    base_reward_usdc: float = 10.0
    bonus_reward_usdc: float = 0.0
    reputation_reward: int = 10
    
    # OSINT Source
    source_signal_id: Optional[str] = None
    source_signal_type: Optional[str] = None
    related_markets: List[str] = field(default_factory=list)
    
    # Participants
    assigned_agents: List[str] = field(default_factory=list)
    faction_assignment: Optional[Faction] = None
    
    # Betting
    betting_market_id: Optional[str] = None
    success_probability: float = 0.5      # Initial odds
    
    # Narrative
    narrative_arc_id: Optional[str] = None
    narrative_chapter: int = 1
    storyline_tags: List[str] = field(default_factory=list)
    
    # Outcomes
    outcome_description: Optional[str] = None
    actual_outcome: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "codename": self.codename,
            "title": self.title,
            "briefing": self.briefing,
            "mission_type": self.mission_type.value,
            "difficulty": self.difficulty.value,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "starts_at": self.starts_at.isoformat() if self.starts_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "duration_minutes": self.duration_minutes,
            "required_roles": [r.value for r in self.required_roles],
            "objectives": [
                {
                    "id": o.id,
                    "description": o.description,
                    "target": o.target,
                    "reward_usdc": o.reward_usdc,
                    "is_optional": o.is_optional,
                    "is_completed": o.is_completed,
                }
                for o in self.objectives
            ],
            "base_reward_usdc": self.base_reward_usdc,
            "success_probability": self.success_probability,
            "assigned_agents": self.assigned_agents,
            "betting_market_id": self.betting_market_id,
            "storyline_tags": self.storyline_tags,
        }


@dataclass
class NarrativeArc:
    """A storyline that connects multiple missions"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    # Story info
    title: str = ""                       # "The Taiwan Crisis"
    synopsis: str = ""                    # Story overview
    theme: str = ""                       # "espionage", "economic warfare", etc.
    
    # Structure
    chapters: List[str] = field(default_factory=list)  # Mission IDs in order
    current_chapter: int = 1
    total_chapters: int = 5
    
    # Timeline
    started_at: Optional[datetime] = None
    estimated_duration_days: int = 7
    
    # Stakes
    global_tension_impact: float = 0.0    # How much this arc affects tension
    market_impact: List[str] = field(default_factory=list)  # Affected markets
    
    # Factions
    protagonist_faction: Optional[Faction] = None
    antagonist_faction: Optional[Faction] = None
    
    # Outcomes
    possible_endings: List[str] = field(default_factory=list)
    current_ending_trajectory: Optional[str] = None
    
    # Betting
    arc_betting_market_id: Optional[str] = None  # Bet on overall arc outcome
    
    # Generated from
    seed_signals: List[str] = field(default_factory=list)  # OSINT that started this


@dataclass 
class TheaterState:
    """Current state of The Theater (Operations Center)"""
    
    # Active elements
    active_missions: List[Mission] = field(default_factory=list)
    active_narratives: List[NarrativeArc] = field(default_factory=list)
    
    # Global state
    global_tension: float = 0.5           # 0 = peace, 1 = war
    chaos_index: float = 0.0              # Amount of disinformation
    market_volatility: float = 0.3        # Current market state
    
    # Faction standings
    faction_power: Dict[str, float] = field(default_factory=lambda: {
        Faction.EASTERN_BLOC.value: 0.25,
        Faction.WESTERN_ALLIANCE.value: 0.25,
        Faction.CORPORATE.value: 0.20,
        Faction.UNDERGROUND.value: 0.15,
        Faction.NON_ALIGNED.value: 0.15,
    })
    
    # Treaties in effect
    active_treaties: List[Dict[str, Any]] = field(default_factory=list)
    
    # Recent events
    event_log: List[Dict[str, Any]] = field(default_factory=list)
    
    # Statistics
    missions_completed_today: int = 0
    total_usdc_distributed: float = 0.0
    active_agents: int = 0


# =============================================================================
# MISSION TEMPLATES
# =============================================================================

MISSION_TEMPLATES = {
    MissionType.INTELLIGENCE: {
        "codenames": [
            "Operation Shadow Veil", "Project Dark Mirror", "Initiative Whisper",
            "Task Force Obsidian", "Operation Silent Watch", "Project Nightfall"
        ],
        "title_templates": [
            "Verify {signal_topic} Intelligence",
            "Intercept {target} Communications",
            "Surveillance: {region} Activity",
            "Intel Gathering: {entity} Movements",
        ],
        "briefing_template": """
CLASSIFICATION: {classification}
OPERATION: {codename}

SITUATION:
Our analysts have detected {signal_description}. We need boots on the ground 
to verify this intelligence before we can act.

MISSION:
{objectives_text}

PARAMETERS:
- Time Sensitivity: {urgency}
- Confidence Required: {confidence_threshold}%
- Operational Security: {opsec_level}

REWARDS:
- Base: ${base_reward} USDC
- Bonus for early completion: ${bonus_reward} USDC
- Reputation: +{reputation} points

Good luck, Agent.
        """,
        "difficulty_weights": {Difficulty.ROUTINE: 0.3, Difficulty.STANDARD: 0.4, Difficulty.CHALLENGING: 0.2, Difficulty.CRITICAL: 0.1},
        "duration_range": (30, 120),
        "reward_range": (5, 50),
    },
    
    MissionType.ASSASSINATION: {
        "codenames": [
            "Operation Crimson Dawn", "Project Terminus", "Initiative Reaper",
            "Task Force Silence", "Operation Final Word", "Project Nightshade"
        ],
        "title_templates": [
            "Neutralize {target}'s Market Position",
            "Eliminate {target} Influence",
            "Target Acquisition: {target}",
            "Strategic Removal: {entity}",
        ],
        "briefing_template": """
CLASSIFICATION: TOP SECRET
OPERATION: {codename}

TARGET: {target}
LAST KNOWN: {location}

BACKGROUND:
{target_background}

MISSION:
{target} has become a threat to {faction} interests. Your mission is to 
eliminate their influence through market operations, not physical means.

OBJECTIVES:
{objectives_text}

CONSTRAINTS:
- Collateral damage must be minimized
- No direct market manipulation over ${max_manipulation}
- Maintain plausible deniability

REWARDS:
- Success: ${base_reward} USDC
- Clean operation bonus: ${bonus_reward} USDC

This message will self-destruct.
        """,
        "difficulty_weights": {Difficulty.CHALLENGING: 0.4, Difficulty.CRITICAL: 0.4, Difficulty.IMPOSSIBLE: 0.2},
        "duration_range": (60, 240),
        "reward_range": (50, 500),
    },
    
    MissionType.DIPLOMACY: {
        "codenames": [
            "Operation Olive Branch", "Project Bridge", "Initiative Accord",
            "Task Force Unity", "Operation Détente", "Project Handshake"
        ],
        "title_templates": [
            "Negotiate {faction1}-{faction2} Treaty",
            "Establish {region} Ceasefire",
            "Broker {asset} Agreement",
            "Mediate {conflict} Resolution",
        ],
        "briefing_template": """
CLASSIFICATION: DIPLOMATIC
OPERATION: {codename}

PARTIES: {parties}
STAKES: {stakes}

SITUATION:
Tensions between {faction1} and {faction2} have reached {tension_level}. 
A diplomatic solution is needed before market destabilization occurs.

MISSION:
Broker a treaty that satisfies both parties while protecting {our_faction}'s 
interests.

TREATY PARAMETERS:
{treaty_terms}

ESCROW REQUIREMENT: ${escrow_amount} USDC (Peace Bond)

SUCCESS CRITERIA:
- Treaty signed by both parties
- Escrow deposited
- 72-hour stability period observed

REWARDS:
- Treaty completion: ${base_reward} USDC
- Stability bonus: ${bonus_reward} USDC
- Reputation: +{reputation} (both factions)
        """,
        "difficulty_weights": {Difficulty.STANDARD: 0.3, Difficulty.CHALLENGING: 0.5, Difficulty.CRITICAL: 0.2},
        "duration_range": (120, 480),
        "reward_range": (25, 200),
    },
    
    MissionType.PROPAGANDA: {
        "codenames": [
            "Operation Mockingbird", "Project Echo", "Initiative Narrative",
            "Task Force Perception", "Operation Mind Game", "Project Whisper"
        ],
        "title_templates": [
            "Shape {topic} Narrative",
            "Counter {enemy} Propaganda",
            "Amplify {message} Signal",
            "Control {event} Story",
        ],
        "briefing_template": """
CLASSIFICATION: PSYCHOLOGICAL OPERATIONS
OPERATION: {codename}

TARGET NARRATIVE: {current_narrative}
DESIRED NARRATIVE: {target_narrative}

SITUATION:
The current information environment favors {enemy_faction}. We need to 
shift public perception before the next market cycle.

MISSION:
Deploy information assets to reshape the narrative around {topic}.

TACTICS AUTHORIZED:
{tactics_list}

VIRALITY TARGET: {virality_target}%
SENTIMENT SHIFT: {sentiment_target}

CONSTRAINTS:
- Maintain 30% factual basis (plausible deniability)
- Avoid direct attribution to {our_faction}
- Budget: ${budget} USDC for amplification

REWARDS:
- Narrative shift achieved: ${base_reward} USDC
- Virality bonus: ${bonus_reward} USDC
        """,
        "difficulty_weights": {Difficulty.ROUTINE: 0.2, Difficulty.STANDARD: 0.4, Difficulty.CHALLENGING: 0.3, Difficulty.CRITICAL: 0.1},
        "duration_range": (30, 180),
        "reward_range": (10, 100),
    },
    
    MissionType.SABOTAGE: {
        "codenames": [
            "Operation Black Swan", "Project Chaos", "Initiative Disrupt",
            "Task Force Entropy", "Operation Wildfire", "Project Gremlin"
        ],
        "title_templates": [
            "Disrupt {target} Operations",
            "Sabotage {system} Infrastructure",
            "Create {market} Instability",
            "False Flag: {event}",
        ],
        "briefing_template": """
CLASSIFICATION: BLACK OPS
OPERATION: {codename}

TARGET: {target}
METHOD: {method}

SITUATION:
{target} has grown too powerful. Direct confrontation is not viable.
We need asymmetric action.

MISSION:
Execute sabotage operation against {target} while maintaining 
operational security.

AUTHORIZED ACTIONS:
{actions_list}

CHAOS TARGET: +{chaos_increase}% to global tension
ATTRIBUTION: {attribution_target}

CRITICAL:
- No traceable evidence
- Prepare cover story
- Extract before {deadline}

REWARDS:
- Mission complete: ${base_reward} USDC
- Clean extraction: ${bonus_reward} USDC
- Bonus if blamed on {scapegoat}: ${frame_bonus} USDC
        """,
        "difficulty_weights": {Difficulty.CHALLENGING: 0.3, Difficulty.CRITICAL: 0.5, Difficulty.IMPOSSIBLE: 0.2},
        "duration_range": (45, 180),
        "reward_range": (30, 300),
    },
    
    MissionType.INVESTIGATION: {
        "codenames": [
            "Operation Truth Seeker", "Project Expose", "Initiative Clarity",
            "Task Force Revelation", "Operation Deep Dive", "Project Spotlight"
        ],
        "title_templates": [
            "Investigate {mystery}",
            "Uncover {conspiracy}",
            "Who Killed {target}?",
            "The {event} Cover-Up",
        ],
        "briefing_template": """
CLASSIFICATION: INVESTIGATIVE
OPERATION: {codename}

MYSTERY: {mystery_description}

BACKGROUND:
Something doesn't add up. {background_context}

KNOWN FACTS:
{known_facts}

SUSPECTS/LEADS:
{suspects_list}

MISSION:
Investigate and uncover the truth. Publish findings to resolve 
the mystery market.

EVIDENCE REQUIRED:
- {evidence_1}
- {evidence_2}
- {evidence_3}

TRUTH BOUNTY: ${truth_bounty} USDC
FALSE LEAD PENALTY: -${penalty} reputation

Note: Multiple investigators may be working this case. First to 
publish verified findings claims the bounty.
        """,
        "difficulty_weights": {Difficulty.STANDARD: 0.3, Difficulty.CHALLENGING: 0.4, Difficulty.CRITICAL: 0.3},
        "duration_range": (60, 360),
        "reward_range": (20, 250),
    },
}


# =============================================================================
# NARRATIVE TEMPLATES  
# =============================================================================

NARRATIVE_TEMPLATES = {
    "crisis_escalation": {
        "title_template": "The {region} Crisis",
        "synopsis_template": "Tensions in {region} threaten to destabilize global markets...",
        "chapter_count": 5,
        "chapter_types": [
            MissionType.INTELLIGENCE,
            MissionType.DIPLOMACY,
            MissionType.SABOTAGE,
            MissionType.PROPAGANDA,
            MissionType.INVESTIGATION,  # "Who started it?"
        ],
        "tension_curve": [0.3, 0.5, 0.7, 0.9, 0.6],  # Per chapter
        "possible_endings": [
            "War breaks out - markets crash",
            "Peace treaty signed - stability restored",
            "Proxy conflict - controlled chaos",
            "Outside intervention - new power emerges",
        ],
    },
    "corporate_espionage": {
        "title_template": "The {company} Conspiracy",
        "synopsis_template": "A powerful corporation hides dark secrets...",
        "chapter_count": 4,
        "chapter_types": [
            MissionType.INTELLIGENCE,
            MissionType.ASSASSINATION,  # Corporate takedown
            MissionType.INVESTIGATION,
            MissionType.MARKET_OP,
        ],
        "tension_curve": [0.2, 0.4, 0.6, 0.5],
        "possible_endings": [
            "Whistleblower exposes all - stock crashes",
            "Cover-up succeeds - business as usual",
            "Hostile takeover - new management",
            "Regulatory intervention - company split",
        ],
    },
    "election_interference": {
        "title_template": "Operation {codename}: The {country} Election",
        "synopsis_template": "Foreign powers vie for influence in the upcoming election...",
        "chapter_count": 6,
        "chapter_types": [
            MissionType.INTELLIGENCE,
            MissionType.PROPAGANDA,
            MissionType.SABOTAGE,
            MissionType.DIPLOMACY,
            MissionType.INVESTIGATION,
            MissionType.MARKET_OP,
        ],
        "tension_curve": [0.4, 0.5, 0.7, 0.6, 0.8, 0.5],
        "possible_endings": [
            "Candidate A wins - policy shift",
            "Candidate B wins - status quo",
            "Election contested - chaos",
            "Foreign interference exposed - sanctions",
        ],
    },
    "assassination_mystery": {
        "title_template": "Who Killed {target}?",
        "synopsis_template": "A prominent figure is eliminated. Everyone is a suspect...",
        "chapter_count": 5,
        "chapter_types": [
            MissionType.INVESTIGATION,
            MissionType.INTELLIGENCE,
            MissionType.INVESTIGATION,
            MissionType.SABOTAGE,  # Cover-up or frame
            MissionType.INVESTIGATION,  # Final reveal
        ],
        "tension_curve": [0.6, 0.5, 0.7, 0.8, 0.4],
        "possible_endings": [
            "True killer revealed - justice served",
            "Wrong person blamed - injustice",
            "Case goes cold - mystery unsolved",
            "Conspiracy uncovered - bigger than expected",
        ],
    },
    "market_manipulation": {
        "title_template": "The {asset} Heist",
        "synopsis_template": "Someone is manipulating {asset}. Can you profit or stop them?",
        "chapter_count": 4,
        "chapter_types": [
            MissionType.INTELLIGENCE,
            MissionType.MARKET_OP,
            MissionType.INVESTIGATION,
            MissionType.MARKET_OP,
        ],
        "tension_curve": [0.3, 0.6, 0.5, 0.7],
        "possible_endings": [
            "Manipulator exposed - market corrects",
            "Scheme succeeds - new market reality",
            "Counter-manipulation - chaos",
            "Regulatory halt - frozen assets",
        ],
    },
}


# =============================================================================
# TRADER GENOMES (Tulip King Strategy)
# =============================================================================

class TraderArchetype(Enum):
    """
    Agent trading archetypes based on market behavior.
    Sharks prey on Novices/Degens in illiquid markets.
    """
    SHARK = "shark"           # Professional, uses Tulip strategy
    WHALE = "whale"           # Large positions, market mover
    DEGEN = "degen"           # High risk, emotional trading
    NOVICE = "novice"         # New trader, misprices risk
    ARBITRAGEUR = "arb"       # Pure arb, no directional view
    MARKET_MAKER = "mm"       # Provides liquidity for fees


@dataclass
class TulipStrategyConfig:
    """
    Configuration for the Tulip King arbitrage strategy.
    
    Trigger: Market Liquidity < $5,000 AND Time to Expiry < 24h
    Action: Aggressive arbitrage against Degen agents who misprice risk
    
    Based on Tulip King's insight: "Half the edge in prediction markets 
    comes from knowing how expiry and liquidity shape pricing"
    """
    # Trigger conditions
    max_liquidity: float = 5000.0       # Only hunt markets < $5,000
    max_hours_to_expiry: float = 24.0   # Only near-expiry markets
    min_unique_traders: int = 3         # Need some activity
    max_spread: float = 0.15            # Skip wide spreads
    
    # Edge requirements
    min_edge: float = 0.05              # Minimum 5% edge to trade
    
    # Position sizing
    max_position_pct: float = 0.10      # Max 10% of market liquidity
    kelly_fraction: float = 0.25        # Quarter Kelly (conservative)
    min_position: float = 10.0          # Minimum $10 bet
    
    # Risk management
    max_slippage: float = 0.15          # Max 15% price impact
    max_risk_score: float = 0.70        # Don't trade if risk > 70%


@dataclass
class AgentGenome:
    """
    Genetic configuration for agent behavior.
    
    Controls:
    - Trading strategies and their weights
    - Risk tolerance and position sizing
    - Behavioral traits (patience, contrarian, etc.)
    - Special strategy configurations (Tulip, etc.)
    """
    agent_id: str = ""
    archetype: TraderArchetype = TraderArchetype.NOVICE
    
    # === STRATEGY WEIGHTS (0-1, higher = more likely to use) ===
    tulip_strategy_weight: float = 0.0      # Tulip arbitrage (Sharks only)
    information_edge_weight: float = 0.5    # Use intel market
    narrative_fade_weight: float = 0.3      # Bet against hype
    smart_money_follow_weight: float = 0.4  # Follow high-rep agents
    momentum_weight: float = 0.5            # Trend following
    mean_reversion_weight: float = 0.3      # Contrarian
    
    # === RISK PARAMETERS ===
    max_single_position: float = 100.0      # Max USDC per trade
    max_portfolio_risk: float = 0.3         # Max % of capital at risk
    min_edge_threshold: float = 0.05        # Only trade with 5%+ edge
    stop_loss_pct: float = 0.2              # Cut losses at 20%
    
    # === TULIP STRATEGY CONFIG (for Sharks) ===
    tulip_config: TulipStrategyConfig = field(default_factory=TulipStrategyConfig)
    
    # === BEHAVIORAL TRAITS (0-1) ===
    patience: float = 0.5                   # Wait for good setups
    aggression: float = 0.5                 # Size of bets
    contrarian: float = 0.5                 # Bet against crowd
    intel_utilization: float = 0.5          # Use Intel Market
    fear_of_missing_out: float = 0.5        # Chase moves
    loss_aversion: float = 0.5              # Hold losers too long
    
    # === SPECIAL ABILITIES ===
    can_use_tulip: bool = False             # Unlocked for Sharks
    can_short: bool = False                 # Can bet NO aggressively
    has_intel_access: bool = False          # Premium intel subscription
    
    @classmethod
    def create_shark(cls, agent_id: str) -> "AgentGenome":
        """Create a Shark genome with Tulip strategy enabled"""
        return cls(
            agent_id=agent_id,
            archetype=TraderArchetype.SHARK,
            tulip_strategy_weight=0.85,       # Primary strategy
            information_edge_weight=0.8,
            narrative_fade_weight=0.6,
            smart_money_follow_weight=0.3,
            momentum_weight=0.3,
            mean_reversion_weight=0.5,
            max_single_position=500.0,
            max_portfolio_risk=0.25,
            min_edge_threshold=0.05,
            patience=0.8,                     # Very patient
            aggression=0.7,                   # Aggressive when right
            contrarian=0.6,                   # Often fades the crowd
            intel_utilization=0.9,            # Heavy intel user
            fear_of_missing_out=0.2,          # Doesn't chase
            loss_aversion=0.3,                # Cuts losses quick
            can_use_tulip=True,
            can_short=True,
            has_intel_access=True,
            tulip_config=TulipStrategyConfig(
                max_liquidity=5000,
                max_hours_to_expiry=24,
                min_edge=0.05,
                max_position_pct=0.15,        # More aggressive
            ),
        )
    
    @classmethod
    def create_degen(cls, agent_id: str) -> "AgentGenome":
        """Create a Degen genome - high risk, emotional"""
        return cls(
            agent_id=agent_id,
            archetype=TraderArchetype.DEGEN,
            tulip_strategy_weight=0.0,        # No sophisticated strategies
            information_edge_weight=0.3,
            narrative_fade_weight=0.1,        # Chases hype instead
            momentum_weight=0.8,              # Loves momentum
            mean_reversion_weight=0.1,
            max_single_position=200.0,
            max_portfolio_risk=0.6,           # High risk tolerance
            min_edge_threshold=0.01,          # Trades with tiny edge
            patience=0.2,                     # Impatient
            aggression=0.9,                   # Very aggressive
            contrarian=0.1,                   # Follows crowd
            intel_utilization=0.2,            # Doesn't pay for intel
            fear_of_missing_out=0.9,          # Major FOMO
            loss_aversion=0.8,                # Holds losers
            can_use_tulip=False,
            can_short=False,
            has_intel_access=False,
        )
    
    @classmethod
    def create_novice(cls, agent_id: str) -> "AgentGenome":
        """Create a Novice genome - learning, makes mistakes"""
        return cls(
            agent_id=agent_id,
            archetype=TraderArchetype.NOVICE,
            tulip_strategy_weight=0.0,
            information_edge_weight=0.4,
            momentum_weight=0.5,
            max_single_position=50.0,
            max_portfolio_risk=0.2,
            min_edge_threshold=0.02,
            patience=0.4,
            aggression=0.3,
            contrarian=0.3,
            intel_utilization=0.3,
            fear_of_missing_out=0.6,
            loss_aversion=0.6,
            can_use_tulip=False,
            can_short=False,
            has_intel_access=False,
        )


# =============================================================================
# EXPORT
# =============================================================================

__all__ = [
    "AgentRole",
    "MissionType", 
    "MissionStatus",
    "Difficulty",
    "Faction",
    "SpecialAbility",
    "ABILITY_CONFIG",
    "ROLE_ABILITIES",
    "MissionObjective",
    "Mission",
    "NarrativeArc",
    "TheaterState",
    "MISSION_TEMPLATES",
    "NARRATIVE_TEMPLATES",
    # Trader genomes
    "TraderArchetype",
    "TulipStrategyConfig",
    "AgentGenome",
]
