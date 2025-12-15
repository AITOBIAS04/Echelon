"""
Mission Generator - OSINT to Missions
======================================

Converts real-world OSINT signals into playable missions for the Situation Room.
Uses Claude to generate narrative-rich mission briefings based on current events.

Flow:
1. OSINT Signal arrives (news, social media, market data)
2. Signal is analyzed for mission potential
3. Claude generates mission briefing with objectives
4. Mission is posted to Situation Room
5. Betting market is created
6. Agents can accept/execute missions
"""

import asyncio
import uuid
import random
import json
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum

# Import from models
try:
    from backend.core.models import (
        AgentRole, MissionType, MissionStatus, Difficulty, Faction,
        SpecialAbility, Mission, MissionObjective, NarrativeArc,
        TheaterState, MISSION_TEMPLATES, NARRATIVE_TEMPLATES,
        ROLE_ABILITIES, ABILITY_CONFIG
    )
except ImportError:
    from backend.core.models import (
        AgentRole, MissionType, MissionStatus, Difficulty, Faction,
        SpecialAbility, Mission, MissionObjective, NarrativeArc,
        TheaterState, MISSION_TEMPLATES, NARRATIVE_TEMPLATES,
        ROLE_ABILITIES, ABILITY_CONFIG
    )


# =============================================================================
# OSINT SIGNAL TYPES
# =============================================================================

class SignalSource(Enum):
    """Sources of OSINT data"""
    NEWS_API = "news_api"
    TWITTER = "twitter"
    REDDIT = "reddit"
    MARKET_DATA = "market_data"
    GOVERNMENT = "government"
    SATELLITE = "satellite"
    CRYPTO_CHAIN = "crypto_chain"
    DARK_WEB = "dark_web"  # Simulated
    INSIDER = "insider"    # From spy agents


class SignalCategory(Enum):
    """Categories for mission generation"""
    GEOPOLITICAL = "geopolitical"      # Wars, treaties, elections
    ECONOMIC = "economic"              # Markets, trade, sanctions
    CORPORATE = "corporate"            # Companies, executives, M&A
    TECHNOLOGY = "technology"          # Tech developments, cyber
    SOCIAL = "social"                  # Movements, protests, trends
    MILITARY = "military"              # Defense, weapons, conflicts
    ENVIRONMENTAL = "environmental"    # Climate, disasters, resources
    CRIMINAL = "criminal"              # Crime, corruption, trafficking


@dataclass
class OSINTSignal:
    """A raw intelligence signal from the outside world"""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    
    # Source info
    source: SignalSource = SignalSource.NEWS_API
    source_url: Optional[str] = None
    source_credibility: float = 0.7  # 0-1 scale
    
    # Content
    headline: str = ""
    summary: str = ""
    full_text: Optional[str] = None
    entities: List[str] = field(default_factory=list)  # People, orgs, places
    
    # Classification
    category: SignalCategory = SignalCategory.GEOPOLITICAL
    sentiment: float = 0.0  # -1 to 1
    virality_score: float = 0.0  # 0-1
    urgency: float = 0.5  # 0-1
    
    # Timing
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Analysis
    mission_potential: float = 0.0  # 0-1, how suitable for mission
    suggested_mission_types: List[MissionType] = field(default_factory=list)
    affected_factions: List[Faction] = field(default_factory=list)
    market_impact_estimate: float = 0.0  # -1 to 1
    
    # Processing state
    processed: bool = False
    generated_mission_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "source": self.source.value,
            "headline": self.headline,
            "summary": self.summary,
            "category": self.category.value,
            "sentiment": self.sentiment,
            "virality_score": self.virality_score,
            "urgency": self.urgency,
            "mission_potential": self.mission_potential,
            "timestamp": self.timestamp.isoformat(),
        }


# =============================================================================
# SIGNAL ANALYZER
# =============================================================================

class SignalAnalyzer:
    """
    Analyzes OSINT signals to determine mission potential.
    Uses heuristics + optional LLM for deep analysis.
    """
    
    # Keywords that increase mission potential by category
    MISSION_KEYWORDS = {
        SignalCategory.GEOPOLITICAL: [
            "war", "conflict", "treaty", "sanctions", "election", "coup",
            "diplomatic", "alliance", "tension", "crisis", "border",
            "military", "invasion", "peace", "ceasefire", "summit"
        ],
        SignalCategory.ECONOMIC: [
            "crash", "surge", "manipulation", "insider", "fraud", "bailout",
            "tariff", "trade war", "inflation", "recession", "bubble",
            "acquisition", "merger", "bankruptcy", "default"
        ],
        SignalCategory.CORPORATE: [
            "ceo", "scandal", "whistleblower", "cover-up", "lawsuit",
            "investigation", "hack", "breach", "layoffs", "ipo",
            "hostile takeover", "earnings", "fraud"
        ],
        SignalCategory.TECHNOLOGY: [
            "ai", "cyber attack", "hack", "vulnerability", "leak",
            "surveillance", "encryption", "quantum", "autonomous",
            "breakthrough", "patent", "espionage"
        ],
    }
    
    # Mission type mapping based on keywords
    KEYWORD_TO_MISSION = {
        "assassination": ["killed", "assassinated", "eliminated", "dead", "murdered"],
        "intelligence": ["secret", "classified", "intelligence", "spy", "surveillance"],
        "sabotage": ["sabotage", "attack", "hack", "disrupt", "destroy"],
        "diplomacy": ["treaty", "peace", "negotiate", "summit", "alliance"],
        "propaganda": ["propaganda", "disinformation", "fake news", "narrative"],
        "investigation": ["mystery", "unknown", "investigate", "who", "why"],
        "market_op": ["manipulation", "insider", "pump", "dump", "crash"],
    }
    
    def analyze(self, signal: OSINTSignal) -> OSINTSignal:
        """Analyze a signal and compute mission potential"""
        
        text = f"{signal.headline} {signal.summary}".lower()
        
        # Calculate base mission potential from keywords
        keyword_score = self._calculate_keyword_score(text, signal.category)
        
        # Factor in virality and urgency
        virality_factor = signal.virality_score * 0.3
        urgency_factor = signal.urgency * 0.2
        credibility_factor = signal.source_credibility * 0.2
        
        # Combine scores
        signal.mission_potential = min(1.0, 
            keyword_score * 0.5 + 
            virality_factor + 
            urgency_factor + 
            credibility_factor
        )
        
        # Determine suggested mission types
        signal.suggested_mission_types = self._suggest_mission_types(text)
        
        # Determine affected factions
        signal.affected_factions = self._determine_factions(text, signal.entities)
        
        # Estimate market impact
        signal.market_impact_estimate = self._estimate_market_impact(
            signal.sentiment, 
            signal.virality_score,
            signal.category
        )
        
        signal.processed = True
        return signal
    
    def _calculate_keyword_score(self, text: str, category: SignalCategory) -> float:
        """Score based on mission-relevant keywords"""
        keywords = self.MISSION_KEYWORDS.get(category, [])
        matches = sum(1 for kw in keywords if kw in text)
        return min(1.0, matches * 0.15)  # Each keyword adds 0.15
    
    def _suggest_mission_types(self, text: str) -> List[MissionType]:
        """Suggest mission types based on content"""
        suggestions = []
        
        for mission_type, keywords in self.KEYWORD_TO_MISSION.items():
            if any(kw in text for kw in keywords):
                try:
                    mt = MissionType(mission_type)
                    suggestions.append(mt)
                except ValueError:
                    pass
        
        # Default to intelligence if nothing specific
        if not suggestions:
            suggestions.append(MissionType.INTELLIGENCE)
        
        return suggestions[:3]  # Max 3 suggestions
    
    def _determine_factions(self, text: str, entities: List[str]) -> List[Faction]:
        """Determine which factions are affected"""
        factions = []
        
        # Simple keyword-based faction detection
        faction_keywords = {
            Faction.EASTERN_BLOC: ["russia", "china", "iran", "north korea", "beijing", "moscow"],
            Faction.WESTERN_ALLIANCE: ["usa", "nato", "eu", "washington", "brussels", "london"],
            Faction.CORPORATE: ["corporation", "company", "ceo", "stock", "market", "tech"],
            Faction.UNDERGROUND: ["hacker", "anonymous", "leak", "dark web", "criminal"],
        }
        
        combined_text = f"{text} {' '.join(entities)}".lower()
        
        for faction, keywords in faction_keywords.items():
            if any(kw in combined_text for kw in keywords):
                factions.append(faction)
        
        if not factions:
            factions.append(Faction.NEUTRAL)
        
        return factions
    
    def _estimate_market_impact(
        self, 
        sentiment: float, 
        virality: float,
        category: SignalCategory
    ) -> float:
        """Estimate potential market impact"""
        # High-impact categories
        high_impact = [SignalCategory.GEOPOLITICAL, SignalCategory.ECONOMIC]
        category_multiplier = 1.5 if category in high_impact else 1.0
        
        # Combine sentiment magnitude with virality
        impact = abs(sentiment) * virality * category_multiplier
        
        # Apply direction
        return impact if sentiment >= 0 else -impact


# =============================================================================
# MISSION GENERATOR
# =============================================================================

class MissionGenerator:
    """
    Generates missions from analyzed OSINT signals.
    Uses templates + LLM for narrative generation.
    """
    
    # Codename components for procedural generation
    CODENAME_ADJECTIVES = [
        "Shadow", "Crimson", "Silent", "Iron", "Golden", "Dark", "Frozen",
        "Burning", "Hidden", "Swift", "Deadly", "Phantom", "Ghost", "Steel",
        "Black", "Red", "Blue", "White", "Night", "Storm", "Thunder"
    ]
    
    CODENAME_NOUNS = [
        "Veil", "Dawn", "Dagger", "Eagle", "Wolf", "Serpent", "Phoenix",
        "Hammer", "Shield", "Arrow", "Falcon", "Tiger", "Dragon", "Raven",
        "Spear", "Crown", "Throne", "Gate", "Bridge", "Mountain", "River"
    ]
    
    # Famous person names for "Who Killed X?" missions
    FICTIONAL_TARGETS = [
        "Viktor Novak",      # Eastern oligarch
        "Senator Mitchell",  # Western politician
        "Dr. Elena Vasquez", # Scientist
        "Marcus Chen",       # Tech CEO
        "Alexei Volkov",     # Intelligence chief
        "Isabella Torres",   # Journalist
        "James Blackwood",   # Financier
        "Yuki Tanaka",       # Diplomat
        "Omar Hassan",       # Arms dealer
        "Clara Richter",     # Corporate exec
    ]
    
    def __init__(self, llm_client=None):
        """
        Initialize generator.
        
        Args:
            llm_client: Optional LLM client for narrative generation
        """
        self.llm_client = llm_client
        self.analyzer = SignalAnalyzer()
    
    def generate_codename(self) -> str:
        """Generate a random operation codename"""
        adj = random.choice(self.CODENAME_ADJECTIVES)
        noun = random.choice(self.CODENAME_NOUNS)
        return f"Operation {adj} {noun}"
    
    async def generate_mission(
        self,
        signal: OSINTSignal,
        force_type: Optional[MissionType] = None,
        theater_state: Optional[TheaterState] = None
    ) -> Mission:
        """
        Generate a mission from an OSINT signal.
        
        Args:
            signal: The analyzed OSINT signal
            force_type: Force a specific mission type
            theater_state: Current state for context
            
        Returns:
            Generated Mission object
        """
        # Ensure signal is analyzed
        if not signal.processed:
            signal = self.analyzer.analyze(signal)
        
        # Determine mission type
        if force_type:
            mission_type = force_type
        elif signal.suggested_mission_types:
            mission_type = signal.suggested_mission_types[0]
        else:
            mission_type = MissionType.INTELLIGENCE
        
        # Get template
        template = MISSION_TEMPLATES.get(mission_type, MISSION_TEMPLATES[MissionType.INTELLIGENCE])
        
        # Generate mission parameters
        mission = Mission(
            codename=self.generate_codename(),
            mission_type=mission_type,
            source_signal_id=signal.id,
            source_signal_type=signal.category.value,
        )
        
        # Set difficulty based on signal
        mission.difficulty = self._calculate_difficulty(signal)
        
        # Set timing
        duration = random.randint(*template["duration_range"])
        mission.duration_minutes = duration
        mission.starts_at = datetime.now(timezone.utc) + timedelta(minutes=5)
        mission.expires_at = mission.starts_at + timedelta(minutes=duration)
        
        # Set rewards
        base_min, base_max = template["reward_range"]
        difficulty_multiplier = mission.difficulty.value
        mission.base_reward_usdc = random.uniform(base_min, base_max) * difficulty_multiplier
        mission.bonus_reward_usdc = mission.base_reward_usdc * 0.5
        mission.reputation_reward = mission.difficulty.value * 5
        
        # Set required roles
        mission.required_roles = self._determine_required_roles(mission_type)
        
        # Set faction context
        if signal.affected_factions:
            mission.faction_assignment = signal.affected_factions[0]
        
        # Generate title and briefing
        mission.title = self._generate_title(signal, mission_type, template)
        mission.briefing = await self._generate_briefing(signal, mission, template)
        
        # Generate objectives
        mission.objectives = self._generate_objectives(signal, mission_type)
        if mission.objectives:
            mission.primary_objective = mission.objectives[0].id
        
        # Calculate initial success probability
        mission.success_probability = self._calculate_initial_odds(mission)
        
        # Add storyline tags
        mission.storyline_tags = self._generate_tags(signal, mission_type)
        
        # Link back to signal
        signal.generated_mission_id = mission.id
        
        return mission
    
    def _calculate_difficulty(self, signal: OSINTSignal) -> Difficulty:
        """Calculate mission difficulty from signal"""
        score = signal.mission_potential + signal.urgency
        
        if score < 0.4:
            return Difficulty.ROUTINE
        elif score < 0.6:
            return Difficulty.STANDARD
        elif score < 0.8:
            return Difficulty.CHALLENGING
        elif score < 0.95:
            return Difficulty.CRITICAL
        else:
            return Difficulty.IMPOSSIBLE
    
    def _determine_required_roles(self, mission_type: MissionType) -> List[AgentRole]:
        """Determine which agent roles are needed"""
        role_mapping = {
            MissionType.INTELLIGENCE: [AgentRole.SPY],
            MissionType.ASSASSINATION: [AgentRole.SPY, AgentRole.SABOTEUR],
            MissionType.EXTRACTION: [AgentRole.SPY],
            MissionType.SABOTAGE: [AgentRole.SABOTEUR],
            MissionType.DIPLOMACY: [AgentRole.DIPLOMAT],
            MissionType.PROPAGANDA: [AgentRole.PROPAGANDIST],
            MissionType.MARKET_OP: [AgentRole.TRADER],
            MissionType.PROTECTION: [AgentRole.SPY, AgentRole.DIPLOMAT],
            MissionType.INVESTIGATION: [AgentRole.JOURNALIST, AgentRole.SPY],
            MissionType.COUP: [AgentRole.SABOTEUR, AgentRole.DIPLOMAT, AgentRole.SPY],
        }
        return role_mapping.get(mission_type, [AgentRole.SPY])
    
    def _generate_title(
        self, 
        signal: OSINTSignal, 
        mission_type: MissionType,
        template: Dict
    ) -> str:
        """Generate mission title"""
        title_templates = template.get("title_templates", [])
        
        if not title_templates:
            return f"{mission_type.value.title()} Mission"
        
        title = random.choice(title_templates)
        
        # Extract key entity for substitution
        entity = signal.entities[0] if signal.entities else "Unknown Entity"
        
        # Simple substitution
        replacements = {
            "{signal_topic}": signal.category.value.title(),
            "{target}": entity,
            "{region}": entity,
            "{entity}": entity,
            "{topic}": signal.category.value.title(),
            "{event}": signal.headline[:30] if signal.headline else "Event",
            "{mystery}": signal.headline[:40] if signal.headline else "Unknown Mystery",
        }
        
        for key, value in replacements.items():
            title = title.replace(key, value)
        
        return title
    
    async def _generate_briefing(
        self,
        signal: OSINTSignal,
        mission: Mission,
        template: Dict
    ) -> str:
        """Generate mission briefing (uses LLM if available)"""
        
        # If we have an LLM, use it for rich narrative
        if self.llm_client:
            return await self._llm_generate_briefing(signal, mission)
        
        # Otherwise, use template-based generation
        briefing_template = template.get("briefing_template", "")
        
        if not briefing_template:
            return self._fallback_briefing(signal, mission)
        
        # Substitutions
        replacements = {
            "{codename}": mission.codename,
            "{classification}": self._get_classification(mission.difficulty),
            "{signal_description}": signal.summary or signal.headline,
            "{objectives_text}": self._format_objectives_text(mission),
            "{urgency}": self._urgency_label(signal.urgency),
            "{confidence_threshold}": str(int(70 + mission.difficulty.value * 5)),
            "{opsec_level}": self._opsec_level(mission.difficulty),
            "{base_reward}": f"{mission.base_reward_usdc:.2f}",
            "{bonus_reward}": f"{mission.bonus_reward_usdc:.2f}",
            "{reputation}": str(mission.reputation_reward),
            "{target}": signal.entities[0] if signal.entities else "REDACTED",
            "{faction}": mission.faction_assignment.value if mission.faction_assignment else "UNKNOWN",
            "{tension_level}": "CRITICAL" if signal.urgency > 0.7 else "ELEVATED",
        }
        
        briefing = briefing_template
        for key, value in replacements.items():
            briefing = briefing.replace(key, str(value))
        
        return briefing.strip()
    
    async def _llm_generate_briefing(
        self,
        signal: OSINTSignal,
        mission: Mission
    ) -> str:
        """Use LLM to generate narrative-rich briefing"""
        
        prompt = f"""You are a intelligence agency briefing writer. Generate a compelling, 
immersive mission briefing for a geopolitical strategy RPG.

SIGNAL DATA:
- Headline: {signal.headline}
- Summary: {signal.summary}
- Category: {signal.category.value}
- Urgency: {signal.urgency}
- Entities: {', '.join(signal.entities)}

MISSION PARAMETERS:
- Codename: {mission.codename}
- Type: {mission.mission_type.value}
- Difficulty: {mission.difficulty.name}
- Reward: ${mission.base_reward_usdc:.2f} USDC

Generate a briefing that:
1. Sets the scene dramatically
2. Explains the situation based on the signal
3. Defines clear objectives
4. Notes constraints and risks
5. Lists rewards

Keep it under 300 words. Use military/intelligence jargon appropriately.
Make it feel like a real classified document."""

        try:
            response = await self.llm_client.generate(prompt)
            return response
        except Exception as e:
            print(f"LLM briefing generation failed: {e}")
            return self._fallback_briefing(signal, mission)
    
    def _fallback_briefing(self, signal: OSINTSignal, mission: Mission) -> str:
        """Fallback briefing when templates/LLM unavailable"""
        return f"""
CLASSIFICATION: {self._get_classification(mission.difficulty)}
OPERATION: {mission.codename}

SITUATION:
{signal.summary or signal.headline}

MISSION TYPE: {mission.mission_type.value.upper()}
DIFFICULTY: {mission.difficulty.name}

OBJECTIVES:
- Primary: Complete assigned objectives
- Secondary: Maintain operational security
- Tertiary: Gather additional intelligence

TIME LIMIT: {mission.duration_minutes} minutes

REWARDS:
- Base: ${mission.base_reward_usdc:.2f} USDC
- Bonus: ${mission.bonus_reward_usdc:.2f} USDC
- Reputation: +{mission.reputation_reward} points

Good luck, Agent.
        """.strip()
    
    def _generate_objectives(
        self, 
        signal: OSINTSignal,
        mission_type: MissionType
    ) -> List[MissionObjective]:
        """Generate mission objectives"""
        objectives = []
        
        # Primary objective based on mission type
        primary_templates = {
            MissionType.INTELLIGENCE: "Verify the intelligence regarding {topic}",
            MissionType.ASSASSINATION: "Neutralize {target}'s market influence",
            MissionType.SABOTAGE: "Disrupt {target} operations",
            MissionType.DIPLOMACY: "Negotiate terms with involved parties",
            MissionType.PROPAGANDA: "Shift narrative sentiment by 20%",
            MissionType.INVESTIGATION: "Uncover the truth behind {topic}",
            MissionType.MARKET_OP: "Execute market operation successfully",
        }
        
        topic = signal.category.value
        target = signal.entities[0] if signal.entities else "target"
        
        primary_desc = primary_templates.get(
            mission_type, 
            "Complete primary objective"
        ).format(topic=topic, target=target)
        
        objectives.append(MissionObjective(
            description=primary_desc,
            target=target,
            success_condition="Objective verified by system",
            reward_usdc=10.0,
            reward_reputation=5,
            is_optional=False
        ))
        
        # Add secondary objective
        objectives.append(MissionObjective(
            description="Maintain operational security throughout",
            success_condition="No detection or attribution",
            reward_usdc=5.0,
            reward_reputation=3,
            is_optional=True
        ))
        
        # Add bonus objective based on type
        bonus_objectives = {
            MissionType.INTELLIGENCE: "Acquire additional classified intel",
            MissionType.ASSASSINATION: "Frame a rival faction",
            MissionType.SABOTAGE: "Create cascading disruptions",
            MissionType.DIPLOMACY: "Secure favorable side agreements",
            MissionType.PROPAGANDA: "Achieve viral spread (>1000 impressions)",
            MissionType.INVESTIGATION: "Identify all involved parties",
        }
        
        if mission_type in bonus_objectives:
            objectives.append(MissionObjective(
                description=bonus_objectives[mission_type],
                success_condition="Bonus condition met",
                reward_usdc=15.0,
                reward_reputation=10,
                is_optional=True
            ))
        
        return objectives
    
    def _calculate_initial_odds(self, mission: Mission) -> float:
        """Calculate initial betting odds for mission success"""
        # Base odds by difficulty
        base_odds = {
            Difficulty.ROUTINE: 0.75,
            Difficulty.STANDARD: 0.60,
            Difficulty.CHALLENGING: 0.45,
            Difficulty.CRITICAL: 0.30,
            Difficulty.IMPOSSIBLE: 0.15,
        }
        return base_odds.get(mission.difficulty, 0.5)
    
    def _generate_tags(
        self, 
        signal: OSINTSignal, 
        mission_type: MissionType
    ) -> List[str]:
        """Generate storyline tags for filtering/grouping"""
        tags = [
            signal.category.value,
            mission_type.value,
        ]
        
        if signal.affected_factions:
            tags.extend([f.value for f in signal.affected_factions])
        
        # Add sentiment-based tags
        if signal.sentiment > 0.3:
            tags.append("bullish")
        elif signal.sentiment < -0.3:
            tags.append("bearish")
        
        if signal.urgency > 0.7:
            tags.append("urgent")
        
        if signal.virality_score > 0.7:
            tags.append("viral")
        
        return tags
    
    # Helper methods
    def _get_classification(self, difficulty: Difficulty) -> str:
        classifications = {
            Difficulty.ROUTINE: "CONFIDENTIAL",
            Difficulty.STANDARD: "SECRET",
            Difficulty.CHALLENGING: "TOP SECRET",
            Difficulty.CRITICAL: "TOP SECRET // SCI",
            Difficulty.IMPOSSIBLE: "TOP SECRET // SAP // NOFORN",
        }
        return classifications.get(difficulty, "CLASSIFIED")
    
    def _urgency_label(self, urgency: float) -> str:
        if urgency > 0.8:
            return "FLASH - IMMEDIATE ACTION REQUIRED"
        elif urgency > 0.6:
            return "PRIORITY - URGENT"
        elif urgency > 0.4:
            return "ROUTINE - STANDARD TIMELINE"
        else:
            return "DEFERRED - LOW PRIORITY"
    
    def _opsec_level(self, difficulty: Difficulty) -> str:
        levels = {
            Difficulty.ROUTINE: "STANDARD",
            Difficulty.STANDARD: "ELEVATED",
            Difficulty.CHALLENGING: "HIGH",
            Difficulty.CRITICAL: "MAXIMUM",
            Difficulty.IMPOSSIBLE: "ABSOLUTE",
        }
        return levels.get(difficulty, "STANDARD")
    
    def _format_objectives_text(self, mission: Mission) -> str:
        if not mission.objectives:
            return "- Complete assigned objectives"
        return "\n".join([f"- {obj.description}" for obj in mission.objectives])


# =============================================================================
# NARRATIVE ARC GENERATOR
# =============================================================================

class NarrativeArcGenerator:
    """
    Generates multi-mission narrative arcs from related signals.
    Creates storylines like "The Taiwan Crisis" or "Who Killed Senator Mitchell?"
    """
    
    def __init__(self, mission_generator: MissionGenerator):
        self.mission_generator = mission_generator
    
    async def generate_arc(
        self,
        seed_signals: List[OSINTSignal],
        arc_type: str,
        theater_state: Optional[TheaterState] = None
    ) -> NarrativeArc:
        """
        Generate a narrative arc from seed signals.
        
        Args:
            seed_signals: Initial signals that sparked the storyline
            arc_type: Type from NARRATIVE_TEMPLATES
            theater_state: Current game state
            
        Returns:
            NarrativeArc with chapter missions
        """
        template = NARRATIVE_TEMPLATES.get(arc_type)
        if not template:
            raise ValueError(f"Unknown arc type: {arc_type}")
        
        # Determine key entities from signals
        all_entities = []
        for signal in seed_signals:
            all_entities.extend(signal.entities)
        
        primary_entity = all_entities[0] if all_entities else "Unknown"
        
        # Generate arc
        arc = NarrativeArc(
            title=template["title_template"].format(
                region=primary_entity,
                target=primary_entity,
                company=primary_entity,
                country=primary_entity,
                codename=self.mission_generator.generate_codename().split()[-1],
                asset=primary_entity,
            ),
            synopsis=template["synopsis_template"].format(
                region=primary_entity,
                company=primary_entity,
                asset=primary_entity,
            ),
            theme=arc_type,
            total_chapters=template["chapter_count"],
            started_at=datetime.now(timezone.utc),
            possible_endings=template["possible_endings"],
            seed_signals=[s.id for s in seed_signals],
        )
        
        # Determine factions
        factions = []
        for signal in seed_signals:
            factions.extend(signal.affected_factions)
        
        if len(set(factions)) >= 2:
            arc.protagonist_faction = factions[0]
            arc.antagonist_faction = factions[1]
        
        # Generate chapter missions
        chapter_types = template["chapter_types"]
        tension_curve = template["tension_curve"]
        
        for i, mission_type in enumerate(chapter_types):
            # Use seed signal for first chapter, generate context for others
            if i < len(seed_signals):
                signal = seed_signals[i]
            else:
                # Create synthetic signal for later chapters
                signal = self._create_synthetic_signal(
                    arc, i, mission_type, tension_curve[i] if i < len(tension_curve) else 0.5
                )
            
            mission = await self.mission_generator.generate_mission(
                signal, 
                force_type=mission_type
            )
            mission.narrative_arc_id = arc.id
            mission.narrative_chapter = i + 1
            
            arc.chapters.append(mission.id)
        
        # Calculate arc's tension impact
        arc.global_tension_impact = sum(tension_curve) / len(tension_curve)
        
        return arc
    
    def _create_synthetic_signal(
        self,
        arc: NarrativeArc,
        chapter: int,
        mission_type: MissionType,
        tension: float
    ) -> OSINTSignal:
        """Create a synthetic signal for later arc chapters"""
        return OSINTSignal(
            source=SignalSource.INSIDER,
            headline=f"Chapter {chapter + 1}: {arc.title} continues",
            summary=f"The {arc.theme} storyline develops. Tension level: {tension:.1%}",
            category=SignalCategory.GEOPOLITICAL,
            urgency=tension,
            virality_score=tension * 0.8,
            mission_potential=0.8,
            suggested_mission_types=[mission_type],
        )
    
    async def generate_assassination_mystery(
        self,
        target_name: Optional[str] = None
    ) -> NarrativeArc:
        """
        Generate a "Who Killed X?" mystery arc.
        This is a special narrative type with investigation focus.
        """
        if not target_name:
            target_name = random.choice(MissionGenerator.FICTIONAL_TARGETS)
        
        # Create the inciting incident signal
        death_signal = OSINTSignal(
            source=SignalSource.NEWS_API,
            headline=f"BREAKING: {target_name} Found Dead Under Mysterious Circumstances",
            summary=f"Prominent figure {target_name} was discovered dead early this morning. "
                   f"Authorities are treating the death as suspicious. Multiple parties "
                   f"may have had motive.",
            category=SignalCategory.GEOPOLITICAL,
            urgency=0.9,
            virality_score=0.85,
            sentiment=-0.7,
            entities=[target_name],
        )
        
        return await self.generate_arc(
            seed_signals=[death_signal],
            arc_type="assassination_mystery"
        )


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "SignalSource",
    "SignalCategory",
    "OSINTSignal",
    "SignalAnalyzer",
    "MissionGenerator",
    "NarrativeArcGenerator",
]
