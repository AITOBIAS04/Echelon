"""
Universal Agent Schema for Project Seed
========================================
This module defines the Pydantic models that enforce consistent agent behavior
across all simulation domains (Finance, Sports, Politics).

Architecture:
- BaseAgent: Universal traits shared by ALL agents
- FinancialAgent: Traders, Whales, Sharks, Degens
- AthleticAgent: Football players, with form/morale/injury mechanics
- PoliticalAgent: Politicians, Voters, Lobbyists

The schema supports:
1. Deterministic wallet generation (ERC-6551 compatible)
2. Genetic breeding/evolution via the BreedingLab
3. Fitness evaluation for natural selection
4. JSON serialization for database persistence
"""

from __future__ import annotations
import random
import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, computed_field


# =============================================================================
# ENUMS - Agent Classifications
# =============================================================================

class AgentDomain(str, Enum):
    """The simulation domain this agent operates in."""
    FINANCIAL = "financial"
    ATHLETIC = "athletic"
    POLITICAL = "political"


class FinancialArchetype(str, Enum):
    """Trader personality types for market simulation."""
    WHALE = "whale"           # High bankroll, conservative, moves markets
    SHARK = "shark"           # Aggressive hedge fund, uses ML predictions
    DEGEN = "degen"           # Retail trader, follows sentiment/news
    VALUE = "value"           # Warren Buffett style, buys undervalued
    MOMENTUM = "momentum"     # Follows trends, buys winners
    NOISE = "noise"           # Random trades, injects volatility


class AthleticArchetype(str, Enum):
    """Player personality types for sports simulation."""
    STAR = "star"             # High skill, high ego, demands spotlight
    GLASS_CANNON = "glass"    # Brilliant but injury-prone
    WORKHORSE = "workhorse"   # Consistent, reliable, low drama
    PROSPECT = "prospect"     # Young, high potential, volatile form
    VETERAN = "veteran"       # Experienced, leadership, declining physical


class PoliticalArchetype(str, Enum):
    """Political actor types for election/governance simulation."""
    POPULIST = "populist"     # High charisma, targets masses
    TECHNOCRAT = "technocrat" # Policy-focused, targets elites
    INSTIGATOR = "instigator" # Chaos agent, leaks scandals
    MODERATE = "moderate"     # Centrist, coalition builder
    IDEOLOGUE = "ideologue"   # True believer, won't compromise


class AgentStatus(str, Enum):
    """Current operational status of an agent."""
    ACTIVE = "active"
    INJURED = "injured"       # Athletic only
    SUSPENDED = "suspended"   # Banned from participation
    BANKRUPT = "bankrupt"     # Financial only - no funds
    ELIMINATED = "eliminated" # Removed from simulation
    RETIRED = "retired"


# =============================================================================
# BASE AGENT - Universal Traits
# =============================================================================

class BaseAgent(BaseModel):
    """
    Universal Agent Schema - The Root

    Every entity in the simulation shares these core traits.
    This enables cross-domain interactions (e.g., a Politician
    accepting donations from a Whale).
    """

    # --- IDENTITY ---
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = Field(..., description="Display name for the agent")
    domain: AgentDomain = Field(..., description="Which simulation domain")
    created_at: datetime = Field(default_factory=datetime.now)
    generation: int = Field(default=1, description="Evolutionary generation number")

    # --- ECONOMIC (Universal) ---
    bankroll: float = Field(default=1000.0, ge=0, description="Liquid capital (USDC)")

    # --- INFLUENCE & RESILIENCE (0.0 - 1.0) ---
    influence: float = Field(
        default=0.5, ge=0.0, le=1.0,
        description="How much their actions impact global state"
    )
    resilience: float = Field(
        default=0.5, ge=0.0, le=1.0,
        description="Resistance to chaos events (injuries, scandals, crashes)"
    )

    # --- CORE PERSONALITY GENES (Inheritable) ---
    aggression: float = Field(
        default=0.5, ge=0.0, le=1.0,
        description="Tendency toward aggressive/risky actions"
    )
    deception: float = Field(
        default=0.3, ge=0.0, le=1.0,
        description="Willingness to mislead or betray"
    )
    loyalty: float = Field(
        default=0.5, ge=0.0, le=1.0,
        description="Commitment to alliances/teams"
    )
    adaptability: float = Field(
        default=0.5, ge=0.0, le=1.0,
        description="Speed of response to changing conditions"
    )

    # --- STATUS ---
    status: AgentStatus = Field(default=AgentStatus.ACTIVE)

    # --- MEMORY (For LLM Context) ---
    memory: List[str] = Field(
        default_factory=list,
        description="Recent events/thoughts for LLM context injection"
    )

    # --- RELATIONSHIPS ---
    allies: List[str] = Field(default_factory=list, description="Agent IDs of allies")
    rivals: List[str] = Field(default_factory=list, description="Agent IDs of rivals")

    # --- FITNESS (Set by simulation, used by BreedingLab) ---
    fitness_score: float = Field(default=0.0, description="Cumulative performance score")

    @computed_field
    @property
    def is_active(self) -> bool:
        """Check if agent can participate in simulation."""
        return self.status == AgentStatus.ACTIVE

    def add_memory(self, event: str, max_memories: int = 10) -> None:
        """Add an event to memory, maintaining a sliding window."""
        timestamp = datetime.now().strftime("%H:%M")
        self.memory.append(f"[{timestamp}] {event}")
        if len(self.memory) > max_memories:
            self.memory = self.memory[-max_memories:]

    def adjust_bankroll(self, amount: float) -> bool:
        """Safely adjust bankroll. Returns False if would go negative."""
        new_balance = self.bankroll + amount
        if new_balance < 0:
            return False
        self.bankroll = new_balance
        if self.bankroll == 0:
            self.status = AgentStatus.BANKRUPT
        return True

    def to_prompt_context(self) -> str:
        """Generate a string for LLM system prompt injection."""
        return f"""Agent: {self.name} ({self.id})
Domain: {self.domain.value}
Bankroll: ${self.bankroll:,.2f}
Influence: {self.influence:.0%} | Resilience: {self.resilience:.0%}
Personality: Aggression={self.aggression:.0%}, Deception={self.deception:.0%}
Recent Memory: {'; '.join(self.memory[-3:]) if self.memory else 'None'}"""


# =============================================================================
# FINANCIAL AGENT - Traders
# =============================================================================

class FinancialAgent(BaseAgent):
    """
    Financial Agent Schema - The Market Movers

    Goal: Maximize bankroll through trading.
    Used in: sim_market_engine, digital twin stock simulations
    """

    domain: AgentDomain = Field(default=AgentDomain.FINANCIAL, frozen=True)
    archetype: FinancialArchetype = Field(..., description="Trading personality")

    # --- FINANCIAL-SPECIFIC STATS ---
    risk_tolerance: float = Field(
        default=0.5, ge=0.0, le=1.0,
        description="Willingness to take leveraged/volatile positions"
    )
    panic_threshold: float = Field(
        default=0.3, ge=0.0, le=1.0,
        description="Point at which agent panic-sells (lower = more nervous)"
    )
    time_horizon: int = Field(
        default=10, ge=1,
        description="How many ticks ahead the agent plans"
    )

    # --- PORTFOLIO STATE ---
    positions: Dict[str, float] = Field(
        default_factory=dict,
        description="Asset -> Shares held"
    )
    avg_entry_prices: Dict[str, float] = Field(
        default_factory=dict,
        description="Asset -> Average purchase price"
    )

    # --- TOOLS/CAPABILITIES ---
    has_ml_model: bool = Field(
        default=False,
        description="Can this agent use predictive models?"
    )
    insider_access: bool = Field(
        default=False,
        description="Does this agent get early news?"
    )

    def decide_action(self, asset_price: float, asset_name: str,
                      news_sentiment: float, market_trend: float) -> str:
        """
        Core decision logic based on archetype.
        Returns: "BUY", "SELL", or "HOLD"
        """
        if self.status != AgentStatus.ACTIVE:
            return "HOLD"

        # Check panic condition
        if asset_name in self.positions:
            entry = self.avg_entry_prices.get(asset_name, asset_price)
            loss_pct = (entry - asset_price) / entry if entry > 0 else 0
            if loss_pct > self.panic_threshold:
                self.add_memory(f"PANIC: {asset_name} down {loss_pct:.0%}")
                return "SELL"

        # Archetype-specific logic
        if self.archetype == FinancialArchetype.WHALE:
            # Whales buy dips, sell peaks, move slowly
            if market_trend < -0.05 and self.bankroll > asset_price * 10:
                return "BUY"
            elif market_trend > 0.1 and asset_name in self.positions:
                return "SELL"

        elif self.archetype == FinancialArchetype.SHARK:
            # Sharks follow momentum aggressively
            if market_trend > 0.02 and self.bankroll > asset_price:
                return "BUY"
            elif market_trend < -0.02 and asset_name in self.positions:
                return "SELL"

        elif self.archetype == FinancialArchetype.DEGEN:
            # Degens follow news sentiment
            if news_sentiment > 0.5 and self.bankroll > asset_price:
                return "BUY"
            elif news_sentiment < -0.5 and asset_name in self.positions:
                return "SELL"

        elif self.archetype == FinancialArchetype.VALUE:
            # Value investors buy undervalued, patient
            entry = self.avg_entry_prices.get(asset_name, asset_price * 1.2)
            if asset_price < entry * 0.8 and self.bankroll > asset_price:
                return "BUY"
            elif asset_price > entry * 1.3:
                return "SELL"

        elif self.archetype == FinancialArchetype.MOMENTUM:
            # Pure trend following
            if market_trend > 0.03:
                return "BUY" if self.bankroll > asset_price else "HOLD"
            elif market_trend < -0.03:
                return "SELL" if asset_name in self.positions else "HOLD"

        elif self.archetype == FinancialArchetype.NOISE:
            # Random noise trader - injects volatility
            roll = random.random()
            if roll < self.aggression * 0.3:
                return "BUY" if self.bankroll > asset_price else "HOLD"
            elif roll > 1 - (self.aggression * 0.3):
                return "SELL" if asset_name in self.positions else "HOLD"

        return "HOLD"

    def execute_trade(self, action: str, asset_name: str,
                      asset_price: float, quantity: int = 1) -> bool:
        """Execute a trade and update portfolio state."""
        if action == "BUY":
            cost = asset_price * quantity
            if self.bankroll >= cost:
                self.bankroll -= cost
                current = self.positions.get(asset_name, 0)
                # Update average entry price
                if current > 0:
                    old_avg = self.avg_entry_prices.get(asset_name, asset_price)
                    new_avg = ((old_avg * current) + cost) / (current + quantity)
                    self.avg_entry_prices[asset_name] = new_avg
                else:
                    self.avg_entry_prices[asset_name] = asset_price
                self.positions[asset_name] = current + quantity
                self.add_memory(f"BOUGHT {quantity} {asset_name} @ ${asset_price:.2f}")
                return True

        elif action == "SELL":
            current = self.positions.get(asset_name, 0)
            sell_qty = min(quantity, current)
            if sell_qty > 0:
                revenue = asset_price * sell_qty
                self.bankroll += revenue
                self.positions[asset_name] = current - sell_qty
                if self.positions[asset_name] == 0:
                    del self.positions[asset_name]
                    del self.avg_entry_prices[asset_name]
                self.add_memory(f"SOLD {sell_qty} {asset_name} @ ${asset_price:.2f}")
                return True

        return False


# =============================================================================
# ATHLETIC AGENT - Sports Players
# =============================================================================

class AthleticAgent(BaseAgent):
    """
    Athletic Agent Schema - The Simulated Athletes

    Goal: Maximize performance_score (goals, assists, wins).
    Used in: Football league simulation, sports betting markets
    """

    domain: AgentDomain = Field(default=AgentDomain.ATHLETIC, frozen=True)
    archetype: AthleticArchetype = Field(..., description="Player personality")

    # --- ATHLETIC-SPECIFIC STATS (0-100 scale for readability) ---
    skill: int = Field(default=70, ge=1, le=100, description="Raw technical ability")
    pace: int = Field(default=70, ge=1, le=100, description="Speed/acceleration")
    stamina: int = Field(default=70, ge=1, le=100, description="Endurance over 90 mins")
    strength: int = Field(default=70, ge=1, le=100, description="Physical power")

    # --- HIDDEN STATS (Updated by simulation) ---
    form: int = Field(
        default=70, ge=0, le=100,
        description="Current momentum/confidence (fluctuates weekly)"
    )
    morale: int = Field(
        default=70, ge=0, le=100,
        description="Mental state (affected by wins/losses/transfers)"
    )
    match_fitness: int = Field(
        default=100, ge=0, le=100,
        description="Ready to play? Degrades with injuries/fatigue"
    )

    # --- INJURY MECHANICS ---
    injury_proneness: float = Field(
        default=0.1, ge=0.0, le=1.0,
        description="Base probability of injury per match"
    )
    current_injury: Optional[str] = Field(default=None, description="Injury type if any")
    recovery_ticks: int = Field(default=0, ge=0, description="Ticks until recovery")

    # --- TEAM/POSITION ---
    team_id: Optional[str] = Field(default=None, description="Current team")
    position: str = Field(default="MID", description="GK/DEF/MID/FWD")
    shirt_number: Optional[int] = Field(default=None, ge=1, le=99)

    # --- SEASON STATS ---
    goals: int = Field(default=0, ge=0)
    assists: int = Field(default=0, ge=0)
    appearances: int = Field(default=0, ge=0)
    yellow_cards: int = Field(default=0, ge=0)
    red_cards: int = Field(default=0, ge=0)

    @computed_field
    @property
    def overall_rating(self) -> int:
        """Calculate FIFA-style overall rating."""
        # Weight by position
        if self.position == "GK":
            return int(self.skill * 0.5 + self.strength * 0.3 + self.pace * 0.2)
        elif self.position == "DEF":
            return int(self.skill * 0.3 + self.strength * 0.4 + self.pace * 0.3)
        elif self.position == "FWD":
            return int(self.skill * 0.5 + self.pace * 0.35 + self.strength * 0.15)
        else:  # MID
            return int(self.skill * 0.4 + self.stamina * 0.3 + self.pace * 0.3)

    @computed_field
    @property
    def effective_rating(self) -> float:
        """Rating adjusted for form, morale, and fitness."""
        base = self.overall_rating
        form_modifier = (self.form - 50) / 100  # -0.5 to +0.5
        morale_modifier = (self.morale - 50) / 200  # -0.25 to +0.25
        fitness_modifier = self.match_fitness / 100  # 0 to 1

        return base * (1 + form_modifier + morale_modifier) * fitness_modifier

    def check_injury(self, match_intensity: float = 0.5) -> Optional[str]:
        """
        Roll for injury based on proneness and match intensity.
        Returns injury type or None.
        """
        if self.status == AgentStatus.INJURED:
            return self.current_injury

        # Injury probability increases with:
        # - Base proneness
        # - Low fitness
        # - High aggression (reckless play)
        # - Match intensity
        injury_chance = (
            self.injury_proneness *
            (1 + (100 - self.match_fitness) / 100) *
            (1 + self.aggression * 0.5) *
            (0.5 + match_intensity)
        )

        if random.random() < injury_chance:
            injuries = [
                ("muscle_strain", 2),
                ("ankle_sprain", 3),
                ("hamstring_tear", 6),
                ("knee_ligament", 12),
                ("broken_bone", 10),
            ]
            # Worse injuries are rarer
            weights = [0.4, 0.3, 0.15, 0.1, 0.05]
            injury, duration = random.choices(injuries, weights=weights)[0]

            self.current_injury = injury
            self.recovery_ticks = duration
            self.status = AgentStatus.INJURED
            self.add_memory(f"INJURED: {injury}, out {duration} weeks")
            return injury

        return None

    def recover_tick(self) -> bool:
        """Process one tick of recovery. Returns True if fully recovered."""
        if self.status != AgentStatus.INJURED:
            return True

        self.recovery_ticks -= 1
        if self.recovery_ticks <= 0:
            self.status = AgentStatus.ACTIVE
            self.current_injury = None
            self.match_fitness = 70  # Not fully fit immediately
            self.add_memory("RECOVERED from injury")
            return True
        return False

    def update_form(self, performance_score: float) -> None:
        """
        Update form based on recent performance.
        performance_score: -1.0 (disaster) to +1.0 (excellent)
        """
        # Form is sticky but moves toward performance
        form_change = int(performance_score * 15)
        self.form = max(0, min(100, self.form + form_change))

        # Morale also affected
        morale_change = int(performance_score * 10)
        self.morale = max(0, min(100, self.morale + morale_change))

    def calculate_match_contribution(self, opponent_strength: float = 0.5) -> Dict[str, Any]:
        """
        Simulate this player's contribution to a match.
        Returns dict with goals, assists, rating, events.
        """
        if self.status != AgentStatus.ACTIVE:
            return {"goals": 0, "assists": 0, "rating": 0, "events": ["Did not play"]}

        events = []
        eff = self.effective_rating

        # Goal probability (position-weighted)
        goal_base = {
            "GK": 0.001, "DEF": 0.02, "MID": 0.08, "FWD": 0.15
        }.get(self.position, 0.05)

        goals = 0
        if random.random() < goal_base * (eff / 70) * (1 - opponent_strength):
            goals = 1
            if random.random() < 0.1:  # Small chance of brace
                goals = 2
            events.append(f"GOAL{'S' if goals > 1 else ''}: {goals}")
            self.goals += goals

        # Assist probability
        assist_base = {"GK": 0.005, "DEF": 0.03, "MID": 0.12, "FWD": 0.06}.get(self.position, 0.05)
        assists = 1 if random.random() < assist_base * (eff / 70) else 0
        if assists:
            events.append("ASSIST")
            self.assists += assists

        # Card probability (aggression increases this)
        if random.random() < self.aggression * 0.1:
            if random.random() < 0.1:
                self.red_cards += 1
                events.append("RED CARD")
            else:
                self.yellow_cards += 1
                events.append("YELLOW CARD")

        # Injury check
        injury = self.check_injury(opponent_strength)
        if injury:
            events.append(f"INJURED: {injury}")

        # Match rating (6.0 - 10.0 scale)
        base_rating = 6.0 + (eff / 100) * 2
        rating = base_rating + goals * 0.8 + assists * 0.4
        rating = min(10.0, max(4.0, rating + random.uniform(-0.5, 0.5)))

        self.appearances += 1
        self.match_fitness = max(60, self.match_fitness - 10)  # Fatigue

        return {
            "goals": goals,
            "assists": assists,
            "rating": round(rating, 1),
            "events": events
        }


# =============================================================================
# POLITICAL AGENT - Power Brokers
# =============================================================================

class PoliticalAgent(BaseAgent):
    """
    Political Agent Schema - The Power Brokers

    Goal: Maximize vote_share or policy adoption.
    Used in: Election simulation, governance prediction markets
    """

    domain: AgentDomain = Field(default=AgentDomain.POLITICAL, frozen=True)
    archetype: PoliticalArchetype = Field(..., description="Political personality")

    # --- POLITICAL-SPECIFIC STATS ---
    charisma: float = Field(
        default=0.5, ge=0.0, le=1.0,
        description="Public appeal and media presence"
    )
    policy_depth: float = Field(
        default=0.5, ge=0.0, le=1.0,
        description="Substance vs. style balance"
    )
    public_favor: float = Field(
        default=0.3, ge=0.0, le=1.0,
        description="Current polling/approval rating"
    )

    # --- VULNERABILITY ---
    scandal_vulnerability: float = Field(
        default=0.3, ge=0.0, le=1.0,
        description="Likelihood of scandal destroying career"
    )
    has_skeleton: bool = Field(
        default=False,
        description="Secret that could be leaked"
    )

    # --- RELATIONSHIPS ---
    donor_alignment: float = Field(
        default=0.5, ge=0.0, le=1.0,
        description="How aligned with wealthy donors"
    )
    party_loyalty: float = Field(
        default=0.7, ge=0.0, le=1.0,
        description="Willingness to follow party line"
    )

    # --- CAMPAIGN STATE ---
    campaign_funds: float = Field(default=0.0, ge=0)
    endorsements: List[str] = Field(default_factory=list)
    scandals_survived: int = Field(default=0)

    def calculate_vote_probability(self, voter_demographics: Dict[str, float]) -> float:
        """
        Calculate probability of winning a voter segment.
        voter_demographics: {"income": 0.5, "education": 0.7, "age": 0.3}
        """
        base = self.public_favor

        # Archetype bonuses
        if self.archetype == PoliticalArchetype.POPULIST:
            # Bonus with lower income, lower education
            base += (1 - voter_demographics.get("income", 0.5)) * 0.2
            base += (1 - voter_demographics.get("education", 0.5)) * 0.1
            base += self.charisma * 0.2

        elif self.archetype == PoliticalArchetype.TECHNOCRAT:
            # Bonus with higher education, higher income
            base += voter_demographics.get("education", 0.5) * 0.2
            base += voter_demographics.get("income", 0.5) * 0.1
            base += self.policy_depth * 0.2

        elif self.archetype == PoliticalArchetype.MODERATE:
            # Consistent across demographics
            base += 0.15  # Broad appeal bonus
            base += self.loyalty * 0.1

        # Campaign spending effect
        spending_boost = min(0.15, self.campaign_funds / 10000)
        base += spending_boost

        return max(0.0, min(1.0, base))

    def survive_scandal(self) -> bool:
        """
        Roll to see if agent survives a scandal.
        Returns True if survived.
        """
        survival_chance = self.resilience * (1 - self.scandal_vulnerability)
        survived = random.random() < survival_chance

        if survived:
            self.scandals_survived += 1
            self.public_favor = max(0, self.public_favor - 0.15)
            self.add_memory("SCANDAL survived but damaged")
        else:
            self.status = AgentStatus.ELIMINATED
            self.add_memory("SCANDAL destroyed career")

        return survived

    def leak_scandal(self, target: 'PoliticalAgent') -> bool:
        """
        Instigator action: attempt to leak a scandal about target.
        """
        if not target.has_skeleton:
            self.add_memory(f"Failed leak attempt on {target.name} - no skeleton")
            return False

        leak_success = self.deception * (1 - target.resilience)
        if random.random() < leak_success:
            target.has_skeleton = False  # Exposed
            self.add_memory(f"Successfully leaked scandal about {target.name}")
            return not target.survive_scandal()

        self.add_memory(f"Leak attempt on {target.name} failed")
        return False


# =============================================================================
# BREEDING / EVOLUTION UTILITIES
# =============================================================================

def breed_agents(parent_a: BaseAgent, parent_b: BaseAgent,
                 mutation_rate: float = 0.1) -> BaseAgent:
    """
    Create a child agent by mixing two parents' genes.
    Parents must be the same type.
    """
    if type(parent_a) != type(parent_b):
        raise ValueError("Cannot breed agents of different types")

    def mix_float(a: float, b: float) -> float:
        """Average with mutation."""
        val = (a + b) / 2
        mutation = random.uniform(-mutation_rate, mutation_rate)
        return max(0.0, min(1.0, val + mutation))

    def mix_int(a: int, b: int, min_val: int = 0, max_val: int = 100) -> int:
        """Average with mutation for integers."""
        val = (a + b) // 2
        mutation = random.randint(-int(mutation_rate * 20), int(mutation_rate * 20))
        return max(min_val, min(max_val, val + mutation))

    # Build child data from parent genes
    child_data = {
        "name": f"Gen{parent_a.generation + 1}_{uuid.uuid4().hex[:4]}",
        "generation": parent_a.generation + 1,
        "domain": parent_a.domain,
        # Core genes
        "aggression": mix_float(parent_a.aggression, parent_b.aggression),
        "deception": mix_float(parent_a.deception, parent_b.deception),
        "loyalty": mix_float(parent_a.loyalty, parent_b.loyalty),
        "adaptability": mix_float(parent_a.adaptability, parent_b.adaptability),
        "influence": mix_float(parent_a.influence, parent_b.influence),
        "resilience": mix_float(parent_a.resilience, parent_b.resilience),
    }

    # Type-specific genes
    if isinstance(parent_a, FinancialAgent):
        child_data.update({
            "archetype": random.choice([parent_a.archetype, parent_b.archetype]),
            "risk_tolerance": mix_float(parent_a.risk_tolerance, parent_b.risk_tolerance),
            "panic_threshold": mix_float(parent_a.panic_threshold, parent_b.panic_threshold),
            "time_horizon": mix_int(parent_a.time_horizon, parent_b.time_horizon, 1, 100),
        })
        return FinancialAgent(**child_data)

    elif isinstance(parent_a, AthleticAgent):
        child_data.update({
            "archetype": random.choice([parent_a.archetype, parent_b.archetype]),
            "skill": mix_int(parent_a.skill, parent_b.skill, 1, 100),
            "pace": mix_int(parent_a.pace, parent_b.pace, 1, 100),
            "stamina": mix_int(parent_a.stamina, parent_b.stamina, 1, 100),
            "strength": mix_int(parent_a.strength, parent_b.strength, 1, 100),
            "injury_proneness": mix_float(parent_a.injury_proneness, parent_b.injury_proneness),
            "position": random.choice([parent_a.position, parent_b.position]),
        })
        return AthleticAgent(**child_data)

    elif isinstance(parent_a, PoliticalAgent):
        child_data.update({
            "archetype": random.choice([parent_a.archetype, parent_b.archetype]),
            "charisma": mix_float(parent_a.charisma, parent_b.charisma),
            "policy_depth": mix_float(parent_a.policy_depth, parent_b.policy_depth),
            "scandal_vulnerability": mix_float(
                parent_a.scandal_vulnerability, parent_b.scandal_vulnerability
            ),
            "donor_alignment": mix_float(parent_a.donor_alignment, parent_b.donor_alignment),
        })
        return PoliticalAgent(**child_data)

    raise ValueError(f"Unknown agent type: {type(parent_a)}")


# =============================================================================
# FACTORY FUNCTIONS
# =============================================================================

def create_random_financial_agent(archetype: Optional[FinancialArchetype] = None,
                                   bankroll: float = 1000.0) -> FinancialAgent:
    """Create a randomized financial agent."""
    if archetype is None:
        archetype = random.choice(list(FinancialArchetype))

    # Archetype influences base stats
    presets = {
        FinancialArchetype.WHALE: {"bankroll": bankroll * 100, "risk_tolerance": 0.2, "influence": 0.9},
        FinancialArchetype.SHARK: {"risk_tolerance": 0.8, "aggression": 0.7, "has_ml_model": True},
        FinancialArchetype.DEGEN: {"risk_tolerance": 0.9, "panic_threshold": 0.5, "adaptability": 0.3},
        FinancialArchetype.VALUE: {"risk_tolerance": 0.3, "time_horizon": 50, "panic_threshold": 0.1},
        FinancialArchetype.MOMENTUM: {"risk_tolerance": 0.6, "adaptability": 0.8},
        FinancialArchetype.NOISE: {"aggression": random.random(), "deception": 0.1},
    }

    base = presets.get(archetype, {})

    return FinancialAgent(
        name=f"{archetype.value.title()}_{uuid.uuid4().hex[:4]}",
        archetype=archetype,
        bankroll=base.get("bankroll", bankroll),
        risk_tolerance=base.get("risk_tolerance", random.uniform(0.3, 0.7)),
        panic_threshold=base.get("panic_threshold", random.uniform(0.2, 0.5)),
        time_horizon=base.get("time_horizon", random.randint(5, 30)),
        aggression=base.get("aggression", random.uniform(0.2, 0.8)),
        deception=base.get("deception", random.uniform(0.1, 0.5)),
        influence=base.get("influence", random.uniform(0.1, 0.5)),
        has_ml_model=base.get("has_ml_model", False),
    )


def create_random_athletic_agent(archetype: Optional[AthleticArchetype] = None,
                                  position: Optional[str] = None) -> AthleticAgent:
    """Create a randomized athletic agent (football player)."""
    if archetype is None:
        archetype = random.choice(list(AthleticArchetype))
    if position is None:
        position = random.choice(["GK", "DEF", "DEF", "MID", "MID", "MID", "FWD", "FWD"])

    # Archetype influences base stats
    presets = {
        AthleticArchetype.STAR: {"skill": 88, "influence": 0.9, "aggression": 0.4},
        AthleticArchetype.GLASS_CANNON: {"skill": 85, "injury_proneness": 0.4, "resilience": 0.3},
        AthleticArchetype.WORKHORSE: {"skill": 72, "stamina": 90, "resilience": 0.8, "loyalty": 0.9},
        AthleticArchetype.PROSPECT: {"skill": 70, "pace": 85, "adaptability": 0.8},
        AthleticArchetype.VETERAN: {"skill": 78, "influence": 0.7, "pace": 60, "resilience": 0.7},
    }

    base = presets.get(archetype, {})

    return AthleticAgent(
        name=f"{archetype.value.title()}_{uuid.uuid4().hex[:4]}",
        archetype=archetype,
        position=position,
        skill=base.get("skill", random.randint(60, 85)),
        pace=base.get("pace", random.randint(55, 90)),
        stamina=base.get("stamina", random.randint(60, 85)),
        strength=base.get("strength", random.randint(55, 85)),
        injury_proneness=base.get("injury_proneness", random.uniform(0.05, 0.25)),
        aggression=base.get("aggression", random.uniform(0.2, 0.7)),
        loyalty=base.get("loyalty", random.uniform(0.4, 0.9)),
        influence=base.get("influence", random.uniform(0.2, 0.6)),
        resilience=base.get("resilience", random.uniform(0.4, 0.7)),
    )


def create_random_political_agent(archetype: Optional[PoliticalArchetype] = None) -> PoliticalAgent:
    """Create a randomized political agent."""
    if archetype is None:
        archetype = random.choice(list(PoliticalArchetype))

    presets = {
        PoliticalArchetype.POPULIST: {"charisma": 0.8, "policy_depth": 0.3, "influence": 0.7},
        PoliticalArchetype.TECHNOCRAT: {"charisma": 0.4, "policy_depth": 0.9, "donor_alignment": 0.8},
        PoliticalArchetype.INSTIGATOR: {"deception": 0.9, "scandal_vulnerability": 0.6},
        PoliticalArchetype.MODERATE: {"loyalty": 0.8, "resilience": 0.7, "charisma": 0.5},
        PoliticalArchetype.IDEOLOGUE: {"loyalty": 0.3, "policy_depth": 0.7, "aggression": 0.6},
    }

    base = presets.get(archetype, {})

    return PoliticalAgent(
        name=f"{archetype.value.title()}_{uuid.uuid4().hex[:4]}",
        archetype=archetype,
        charisma=base.get("charisma", random.uniform(0.3, 0.8)),
        policy_depth=base.get("policy_depth", random.uniform(0.3, 0.8)),
        scandal_vulnerability=base.get("scandal_vulnerability", random.uniform(0.2, 0.5)),
        donor_alignment=base.get("donor_alignment", random.uniform(0.3, 0.7)),
        deception=base.get("deception", random.uniform(0.2, 0.6)),
        aggression=base.get("aggression", random.uniform(0.2, 0.6)),
        influence=base.get("influence", random.uniform(0.3, 0.6)),
        loyalty=base.get("loyalty", random.uniform(0.4, 0.8)),
        resilience=base.get("resilience", random.uniform(0.4, 0.7)),
        has_skeleton=random.random() < 0.3,  # 30% have a secret
    )


# =============================================================================
# QUICK TEST
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("UNIVERSAL AGENT SCHEMA - TEST")
    print("=" * 60)

    # Create one of each type
    trader = create_random_financial_agent(FinancialArchetype.SHARK)
    player = create_random_athletic_agent(AthleticArchetype.STAR, "FWD")
    politician = create_random_political_agent(PoliticalArchetype.POPULIST)

    print(f"\n📈 FINANCIAL: {trader.name}")
    print(f"   Archetype: {trader.archetype.value}")
    print(f"   Bankroll: ${trader.bankroll:,.2f}")
    print(f"   Risk Tolerance: {trader.risk_tolerance:.0%}")

    print(f"\n⚽ ATHLETIC: {player.name}")
    print(f"   Position: {player.position} | Overall: {player.overall_rating}")
    print(f"   Effective Rating: {player.effective_rating:.1f}")
    print(f"   Skill: {player.skill} | Pace: {player.pace}")

    print(f"\n🏛️ POLITICAL: {politician.name}")
    print(f"   Archetype: {politician.archetype.value}")
    print(f"   Charisma: {politician.charisma:.0%} | Policy: {politician.policy_depth:.0%}")
    print(f"   Has Skeleton: {politician.has_skeleton}")

    # Test breeding
    print("\n" + "=" * 60)
    print("BREEDING TEST")
    print("=" * 60)

    trader2 = create_random_financial_agent(FinancialArchetype.WHALE)
    child = breed_agents(trader, trader2)

    print(f"\nParent A: {trader.name} ({trader.archetype.value})")
    print(f"Parent B: {trader2.name} ({trader2.archetype.value})")
    print(f"Child: {child.name} ({child.archetype.value})")
    print(f"   Risk: {child.risk_tolerance:.2f} (avg of {trader.risk_tolerance:.2f} & {trader2.risk_tolerance:.2f})")

    # Test match simulation
    print("\n" + "=" * 60)
    print("MATCH SIMULATION TEST")
    print("=" * 60)

    result = player.calculate_match_contribution(opponent_strength=0.6)
    print(f"\n{player.name} match result:")
    print(f"   Goals: {result['goals']} | Assists: {result['assists']}")
    print(f"   Rating: {result['rating']}")
    print(f"   Events: {result['events']}")

    print("\n✅ Schema test complete!")
