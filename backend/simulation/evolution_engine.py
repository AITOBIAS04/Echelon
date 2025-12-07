"""
Unified Evolution Engine for Project Seed
==========================================
Genetic algorithm system for breeding and evolving agents across all domains.

This implements the "Genealogy" system from the spec:
- Natural selection based on fitness scores
- Crossover breeding with mutation
- Entertainment parameter to prevent boring strategies
- Transfer learning between domains (aggressive trader -> aggressive debater)

Features:
- Domain-specific fitness functions (P&L for traders, goals for athletes, votes for politicians)
- Elitism (champions survive unchanged)
- Configurable mutation rates
- Season-based evolution cycles
- Persistent lineage tracking

Usage:
    from backend.simulation.evolution_engine import EvolutionEngine, EvolutionConfig
    
    # Create engine for financial agents
    engine = EvolutionEngine(
        domain="financial",
        config=EvolutionConfig(population_size=50)
    )
    
    # Initialize population
    engine.genesis()
    
    # Run a season (agents compete, then breed)
    results = engine.run_season(simulation_func)
    
    # Get the evolved population
    champions = engine.get_top_agents(5)
"""

import os
import sys
import json
import random
import hashlib
from datetime import datetime
from typing import List, Dict, Any, Optional, Callable, Union, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
from abc import ABC, abstractmethod

# Add parent directory for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.agents.schemas import (
    BaseAgent,
    FinancialAgent,
    AthleticAgent, 
    PoliticalAgent,
    FinancialArchetype,
    AthleticArchetype,
    PoliticalArchetype,
    AgentDomain,
    AgentStatus,
    create_random_financial_agent,
    create_random_athletic_agent,
    create_random_political_agent,
    breed_agents,
)


# =============================================================================
# CONFIGURATION
# =============================================================================

@dataclass
class EvolutionConfig:
    """Configuration for the evolution engine."""
    
    # Population
    population_size: int = 50
    elite_count: int = 5  # Top N agents survive unchanged
    
    # Selection
    survival_rate: float = 0.5  # Top 50% survive to breed
    tournament_size: int = 3  # For tournament selection
    
    # Mutation
    mutation_rate: float = 0.1  # Probability of mutation per gene
    mutation_magnitude: float = 0.15  # Max change when mutating
    
    # Fitness weights (domain-specific defaults set in FitnessEvaluator)
    performance_weight: float = 0.6  # Primary metric (P&L, goals, votes)
    entertainment_weight: float = 0.25  # Activity, drama, engagement
    survival_weight: float = 0.15  # Did they survive the season?
    
    # Season
    season_length: int = 100  # Ticks/matches per season
    
    # Persistence
    save_history: bool = True
    history_file: str = "evolution_history.json"


# =============================================================================
# FITNESS EVALUATORS
# =============================================================================

class FitnessEvaluator(ABC):
    """Base class for domain-specific fitness evaluation."""
    
    @abstractmethod
    def evaluate(self, agent: BaseAgent, season_stats: Dict[str, Any]) -> float:
        """
        Calculate fitness score for an agent.
        
        Args:
            agent: The agent to evaluate
            season_stats: Performance data from the simulation
            
        Returns:
            Fitness score (higher is better)
        """
        pass
    
    @abstractmethod
    def calculate_entertainment(self, agent: BaseAgent, season_stats: Dict[str, Any]) -> float:
        """
        Calculate entertainment value.
        
        This prevents evolution toward "boring campers" - agents that
        survive by doing nothing interesting.
        """
        pass


class FinancialFitnessEvaluator(FitnessEvaluator):
    """Fitness evaluation for financial agents (traders)."""
    
    def evaluate(self, agent: FinancialAgent, season_stats: Dict[str, Any]) -> float:
        """
        Financial fitness based on:
        - P&L (primary)
        - Trade activity (entertainment)
        - Survival (didn't go bankrupt)
        """
        score = 0.0
        
        # 1. Performance: Profit/Loss
        pnl = season_stats.get("pnl", 0)
        pnl_pct = season_stats.get("pnl_pct", 0)
        
        # Normalize P&L to 0-100 scale
        # +50% P&L = 100 points, -50% = 0 points
        performance_score = max(0, min(100, 50 + pnl_pct))
        score += performance_score * 0.6
        
        # 2. Entertainment: Trading activity
        entertainment = self.calculate_entertainment(agent, season_stats)
        score += entertainment * 0.25
        
        # 3. Survival bonus
        if agent.status == AgentStatus.ACTIVE and agent.bankroll > 0:
            score += 15
        
        # 4. Archetype synergy bonus
        # Reward agents that embody their archetype well
        if agent.archetype == FinancialArchetype.SHARK:
            # Sharks should be profitable and active
            if pnl_pct > 10 and season_stats.get("trades", 0) > 20:
                score += 10
        elif agent.archetype == FinancialArchetype.WHALE:
            # Whales should move markets
            if season_stats.get("market_impact", 0) > 0.5:
                score += 10
        elif agent.archetype == FinancialArchetype.VALUE:
            # Value investors should have low turnover but good returns
            if pnl_pct > 5 and season_stats.get("trades", 0) < 10:
                score += 10
        
        return score
    
    def calculate_entertainment(self, agent: FinancialAgent, 
                                 season_stats: Dict[str, Any]) -> float:
        """
        Entertainment for traders:
        - Number of trades (activity)
        - Big wins/losses (drama)
        - Unique strategies
        """
        score = 0.0
        
        # Trade count (activity)
        trades = season_stats.get("trades", 0)
        score += min(30, trades * 1.5)  # Cap at 30 points
        
        # Volatility of returns (drama)
        return_volatility = season_stats.get("return_volatility", 0)
        score += min(40, return_volatility * 100)
        
        # Big moves (memorable moments)
        big_wins = season_stats.get("big_wins", 0)
        big_losses = season_stats.get("big_losses", 0)
        score += (big_wins + big_losses) * 5
        
        return min(100, score)


class AthleticFitnessEvaluator(FitnessEvaluator):
    """Fitness evaluation for athletic agents (football players)."""
    
    def evaluate(self, agent: AthleticAgent, season_stats: Dict[str, Any]) -> float:
        """
        Athletic fitness based on:
        - Goals/Assists (primary for attackers)
        - Clean sheets (for defenders/GK)
        - Match ratings
        - Entertainment value
        """
        score = 0.0
        
        # 1. Position-weighted performance
        goals = season_stats.get("goals", agent.goals)
        assists = season_stats.get("assists", agent.assists)
        appearances = season_stats.get("appearances", agent.appearances)
        avg_rating = season_stats.get("avg_rating", 6.5)
        
        if agent.position == "FWD":
            # Strikers judged on goals
            performance = (goals * 10) + (assists * 5) + ((avg_rating - 6) * 10)
        elif agent.position == "MID":
            # Midfielders balanced
            performance = (goals * 7) + (assists * 8) + ((avg_rating - 6) * 15)
        elif agent.position == "DEF":
            # Defenders on clean sheets and rating
            clean_sheets = season_stats.get("clean_sheets", 0)
            performance = (clean_sheets * 5) + (goals * 5) + (assists * 3) + ((avg_rating - 6) * 20)
        else:  # GK
            clean_sheets = season_stats.get("clean_sheets", 0)
            saves = season_stats.get("saves", 0)
            performance = (clean_sheets * 8) + (saves * 0.5) + ((avg_rating - 6) * 25)
        
        score += min(60, performance)
        
        # 2. Entertainment
        entertainment = self.calculate_entertainment(agent, season_stats)
        score += entertainment * 0.25
        
        # 3. Availability (didn't miss too many games)
        if appearances > 0:
            availability = min(1.0, appearances / season_stats.get("max_appearances", 38))
            score += availability * 15
        
        return score
    
    def calculate_entertainment(self, agent: AthleticAgent,
                                 season_stats: Dict[str, Any]) -> float:
        """
        Entertainment for athletes:
        - Goals scored (exciting)
        - Cards (drama)
        - Key moments (late goals, winners)
        """
        score = 0.0
        
        # Goals are entertaining
        goals = season_stats.get("goals", agent.goals)
        score += goals * 8
        
        # Assists show creativity
        assists = season_stats.get("assists", agent.assists)
        score += assists * 4
        
        # Cards add drama (but not too many)
        yellows = season_stats.get("yellow_cards", agent.yellow_cards)
        reds = season_stats.get("red_cards", agent.red_cards)
        score += min(20, yellows * 3 + reds * 8)
        
        # Key moments
        winning_goals = season_stats.get("winning_goals", 0)
        late_goals = season_stats.get("late_goals", 0)  # After 85'
        score += winning_goals * 10 + late_goals * 5
        
        return min(100, score)


class PoliticalFitnessEvaluator(FitnessEvaluator):
    """Fitness evaluation for political agents."""
    
    def evaluate(self, agent: PoliticalAgent, season_stats: Dict[str, Any]) -> float:
        """
        Political fitness based on:
        - Vote share / approval rating
        - Policy success
        - Entertainment (scandals survived, debates won)
        """
        score = 0.0
        
        # 1. Performance: Vote share or approval
        vote_share = season_stats.get("vote_share", agent.public_favor)
        score += vote_share * 60  # 0-60 points
        
        # 2. Policy adoption
        policies_passed = season_stats.get("policies_passed", 0)
        score += min(20, policies_passed * 5)
        
        # 3. Entertainment
        entertainment = self.calculate_entertainment(agent, season_stats)
        score += entertainment * 0.2
        
        # 4. Survival
        if agent.status == AgentStatus.ACTIVE:
            score += 10
        
        # 5. Archetype bonuses
        if agent.archetype == PoliticalArchetype.POPULIST:
            # Populists should have high public engagement
            engagement = season_stats.get("public_engagement", 0)
            if engagement > 0.7:
                score += 10
        elif agent.archetype == PoliticalArchetype.INSTIGATOR:
            # Instigators should cause chaos
            scandals_caused = season_stats.get("scandals_caused", 0)
            if scandals_caused > 2:
                score += 10
        
        return score
    
    def calculate_entertainment(self, agent: PoliticalAgent,
                                 season_stats: Dict[str, Any]) -> float:
        """
        Entertainment for politicians:
        - Scandals (survived or caused)
        - Debate performances
        - Viral moments
        """
        score = 0.0
        
        # Scandals are entertaining
        scandals_survived = season_stats.get("scandals_survived", agent.scandals_survived)
        scandals_caused = season_stats.get("scandals_caused", 0)
        score += scandals_survived * 15 + scandals_caused * 10
        
        # Debates
        debates_won = season_stats.get("debates_won", 0)
        score += debates_won * 8
        
        # Public engagement
        viral_moments = season_stats.get("viral_moments", 0)
        score += viral_moments * 5
        
        # Controversial statements (risky but entertaining)
        controversies = season_stats.get("controversies", 0)
        score += min(20, controversies * 4)
        
        return min(100, score)


# =============================================================================
# EVOLUTION ENGINE
# =============================================================================

@dataclass
class EvolutionRecord:
    """Record of one generation's evolution."""
    generation: int
    timestamp: str
    population_size: int
    champion_id: str
    champion_fitness: float
    average_fitness: float
    top_archetypes: List[str]
    mutations_applied: int
    
    def to_dict(self) -> Dict:
        return asdict(self)


class EvolutionEngine:
    """
    Unified evolution engine for all agent types.
    
    Implements genetic algorithm with:
    - Tournament selection
    - Crossover breeding
    - Mutation
    - Elitism
    """
    
    def __init__(self, domain: str, config: EvolutionConfig = None,
                 seed: str = None):
        """
        Initialize evolution engine.
        
        Args:
            domain: "financial", "athletic", or "political"
            config: Evolution configuration
            seed: Random seed for reproducibility
        """
        self.domain = AgentDomain(domain)
        self.config = config or EvolutionConfig()
        
        # Seed randomness
        if seed:
            random.seed(seed)
            self.seed = seed
        else:
            self.seed = hashlib.sha256(str(datetime.now()).encode()).hexdigest()[:16]
        
        # Population
        self.population: List[BaseAgent] = []
        self.generation = 0
        
        # History
        self.history: List[EvolutionRecord] = []
        self.lineage: Dict[str, List[str]] = {}  # agent_id -> [parent_ids]
        
        # Fitness evaluator
        self._init_evaluator()
    
    def _init_evaluator(self):
        """Initialize domain-specific fitness evaluator."""
        if self.domain == AgentDomain.FINANCIAL:
            self.evaluator = FinancialFitnessEvaluator()
            self.agent_factory = create_random_financial_agent
        elif self.domain == AgentDomain.ATHLETIC:
            self.evaluator = AthleticFitnessEvaluator()
            self.agent_factory = create_random_athletic_agent
        elif self.domain == AgentDomain.POLITICAL:
            self.evaluator = PoliticalFitnessEvaluator()
            self.agent_factory = create_random_political_agent
        else:
            raise ValueError(f"Unknown domain: {self.domain}")
    
    def genesis(self, archetypes: List[Any] = None) -> List[BaseAgent]:
        """
        Create initial population.
        
        Args:
            archetypes: Optional list of archetypes to use (otherwise random)
        """
        print(f"🧬 GENESIS: Creating Generation 1 ({self.domain.value})")
        
        self.population = []
        self.generation = 1
        
        for i in range(self.config.population_size):
            if archetypes:
                archetype = random.choice(archetypes)
                agent = self.agent_factory(archetype=archetype)
            else:
                agent = self.agent_factory()
            
            self.population.append(agent)
            self.lineage[agent.id] = []  # No parents
        
        print(f"   ✨ Created {len(self.population)} agents")
        
        return self.population
    
    def evaluate_population(self, 
                            season_results: Dict[str, Dict[str, Any]]) -> List[Tuple[BaseAgent, float]]:
        """
        Evaluate fitness for all agents.
        
        Args:
            season_results: Dict mapping agent_id -> performance stats
            
        Returns:
            List of (agent, fitness) tuples, sorted by fitness descending
        """
        scored = []
        
        for agent in self.population:
            stats = season_results.get(agent.id, {})
            fitness = self.evaluator.evaluate(agent, stats)
            agent.fitness_score = fitness
            scored.append((agent, fitness))
        
        # Sort by fitness
        scored.sort(key=lambda x: x[1], reverse=True)
        
        return scored
    
    def select_parents(self, scored_population: List[Tuple[BaseAgent, float]]) -> List[BaseAgent]:
        """
        Select agents for breeding using tournament selection.
        """
        survivors_count = int(len(self.population) * self.config.survival_rate)
        survivors = []
        
        # Elites pass through automatically
        for agent, fitness in scored_population[:self.config.elite_count]:
            survivors.append(agent)
        
        # Tournament selection for the rest
        remaining_pool = [a for a, f in scored_population[self.config.elite_count:]]
        
        while len(survivors) < survivors_count and remaining_pool:
            # Tournament
            tournament = random.sample(
                remaining_pool, 
                min(self.config.tournament_size, len(remaining_pool))
            )
            winner = max(tournament, key=lambda a: a.fitness_score)
            survivors.append(winner)
            remaining_pool.remove(winner)
        
        return survivors
    
    def breed_next_generation(self, parents: List[BaseAgent]) -> List[BaseAgent]:
        """
        Create next generation through breeding.
        """
        next_gen = []
        mutations_count = 0
        
        # Elites survive unchanged
        for agent in parents[:self.config.elite_count]:
            next_gen.append(agent)
        
        # Breed to fill population
        while len(next_gen) < self.config.population_size:
            # Select two parents
            parent_a = random.choice(parents)
            parent_b = random.choice(parents)
            
            # Avoid self-breeding if possible
            attempts = 0
            while parent_a.id == parent_b.id and len(parents) > 1 and attempts < 10:
                parent_b = random.choice(parents)
                attempts += 1
            
            # Breed
            try:
                child = breed_agents(parent_a, parent_b, self.config.mutation_rate)
                
                # Track lineage
                self.lineage[child.id] = [parent_a.id, parent_b.id]
                
                # Count if mutation occurred (simplified check)
                if random.random() < self.config.mutation_rate:
                    mutations_count += 1
                
                next_gen.append(child)
                
            except Exception as e:
                print(f"   ⚠️ Breeding failed: {e}")
                # Create random agent as fallback
                next_gen.append(self.agent_factory())
        
        return next_gen, mutations_count
    
    def run_generation(self, 
                       season_results: Dict[str, Dict[str, Any]],
                       verbose: bool = True) -> EvolutionRecord:
        """
        Run one generation of evolution.
        
        Args:
            season_results: Performance data from simulation
            verbose: Print progress
            
        Returns:
            Record of this generation
        """
        if verbose:
            print(f"\n⚔️ GENERATION {self.generation} - Natural Selection")
        
        # 1. Evaluate fitness
        scored = self.evaluate_population(season_results)
        
        # 2. Record stats
        champion = scored[0][0]
        champion_fitness = scored[0][1]
        avg_fitness = sum(f for _, f in scored) / len(scored)
        
        # Count archetypes in top 10
        top_archetypes = {}
        for agent, _ in scored[:10]:
            arch = getattr(agent, 'archetype', 'unknown')
            arch_name = arch.value if hasattr(arch, 'value') else str(arch)
            top_archetypes[arch_name] = top_archetypes.get(arch_name, 0) + 1
        
        if verbose:
            print(f"   🏆 Champion: {champion.name} (Fitness: {champion_fitness:.1f})")
            print(f"   📊 Average Fitness: {avg_fitness:.1f}")
        
        # 3. Select parents
        parents = self.select_parents(scored)
        
        if verbose:
            print(f"   🧬 {len(parents)} agents selected for breeding")
        
        # 4. Breed next generation
        self.population, mutations = self.breed_next_generation(parents)
        
        if verbose:
            print(f"   🔄 {mutations} mutations applied")
            print(f"   ✅ Generation {self.generation} complete")
        
        # 5. Record history
        record = EvolutionRecord(
            generation=self.generation,
            timestamp=datetime.now().isoformat(),
            population_size=len(self.population),
            champion_id=champion.id,
            champion_fitness=champion_fitness,
            average_fitness=avg_fitness,
            top_archetypes=list(top_archetypes.keys()),
            mutations_applied=mutations,
        )
        
        self.history.append(record)
        self.generation += 1
        
        return record
    
    def run_season(self, 
                   simulation_func: Callable[[List[BaseAgent]], Dict[str, Dict[str, Any]]],
                   verbose: bool = True) -> Dict[str, Any]:
        """
        Run a complete season: simulate competition, then evolve.
        
        Args:
            simulation_func: Function that takes agents and returns season results
                             Dict mapping agent_id -> {"pnl": 100, "trades": 50, ...}
            verbose: Print progress
            
        Returns:
            Season summary including champion and fitness improvement
        """
        if verbose:
            print(f"\n{'='*50}")
            print(f"🏁 SEASON {self.generation} ({self.domain.value})")
            print(f"{'='*50}")
        
        # 1. Run simulation
        if verbose:
            print(f"\n📊 Running simulation with {len(self.population)} agents...")
        
        season_results = simulation_func(self.population)
        
        # 2. Evolve
        record = self.run_generation(season_results, verbose)
        
        # 3. Summary
        improvement = 0
        if len(self.history) > 1:
            prev_avg = self.history[-2].average_fitness
            improvement = record.average_fitness - prev_avg
        
        return {
            "generation": record.generation,
            "champion_id": record.champion_id,
            "champion_fitness": record.champion_fitness,
            "average_fitness": record.average_fitness,
            "fitness_improvement": improvement,
            "top_archetypes": record.top_archetypes,
        }
    
    def get_top_agents(self, n: int = 5) -> List[BaseAgent]:
        """Get top N agents by fitness."""
        sorted_pop = sorted(self.population, key=lambda a: a.fitness_score, reverse=True)
        return sorted_pop[:n]
    
    def get_agent_lineage(self, agent_id: str, depth: int = 3) -> Dict[str, Any]:
        """Get ancestry of an agent."""
        def trace(aid, d):
            if d == 0 or aid not in self.lineage:
                return {"id": aid, "parents": []}
            
            parents = self.lineage.get(aid, [])
            return {
                "id": aid,
                "parents": [trace(p, d-1) for p in parents]
            }
        
        return trace(agent_id, depth)
    
    def save_state(self, filepath: str) -> None:
        """Save evolution state to file."""
        state = {
            "domain": self.domain.value,
            "generation": self.generation,
            "seed": self.seed,
            "config": asdict(self.config),
            "history": [r.to_dict() for r in self.history],
            "population": [a.model_dump() for a in self.population],
            "lineage": self.lineage,
        }
        
        with open(filepath, 'w') as f:
            json.dump(state, f, indent=2, default=str)
        
        print(f"💾 Saved evolution state to {filepath}")
    
    def load_state(self, filepath: str) -> None:
        """Load evolution state from file."""
        with open(filepath, 'r') as f:
            state = json.load(f)
        
        self.domain = AgentDomain(state["domain"])
        self.generation = state["generation"]
        self.seed = state["seed"]
        self.config = EvolutionConfig(**state["config"])
        self.history = [EvolutionRecord(**r) for r in state["history"]]
        self.lineage = state["lineage"]
        
        # Reconstruct population based on domain
        self._init_evaluator()
        
        self.population = []
        for agent_data in state["population"]:
            if self.domain == AgentDomain.FINANCIAL:
                self.population.append(FinancialAgent(**agent_data))
            elif self.domain == AgentDomain.ATHLETIC:
                self.population.append(AthleticAgent(**agent_data))
            elif self.domain == AgentDomain.POLITICAL:
                self.population.append(PoliticalAgent(**agent_data))
        
        print(f"📂 Loaded evolution state: Gen {self.generation}, {len(self.population)} agents")


# =============================================================================
# MOCK SIMULATION FOR TESTING
# =============================================================================

def mock_financial_simulation(agents: List[FinancialAgent]) -> Dict[str, Dict[str, Any]]:
    """Mock simulation for testing financial agent evolution."""
    results = {}
    
    for agent in agents:
        # Simulate P&L based on agent traits
        base_pnl = random.uniform(-20, 20)
        
        # Risk tolerance affects variance
        variance = agent.risk_tolerance * 30
        pnl_pct = base_pnl + random.uniform(-variance, variance)
        
        # Sharks tend to do better
        if agent.archetype == FinancialArchetype.SHARK:
            pnl_pct += 5
        
        # Activity based on risk tolerance
        trades = int(10 + agent.risk_tolerance * 40 + random.randint(0, 20))
        
        results[agent.id] = {
            "pnl": pnl_pct * 100,
            "pnl_pct": pnl_pct,
            "trades": trades,
            "big_wins": random.randint(0, 3) if pnl_pct > 10 else 0,
            "big_losses": random.randint(0, 2) if pnl_pct < -10 else 0,
            "return_volatility": agent.risk_tolerance * 0.3,
            "market_impact": agent.influence * random.random(),
        }
    
    return results


def mock_athletic_simulation(agents: List[AthleticAgent]) -> Dict[str, Dict[str, Any]]:
    """Mock simulation for testing athletic agent evolution."""
    results = {}
    
    for agent in agents:
        # Appearances based on fitness and injury proneness
        max_appearances = 38
        injury_factor = 1 - (agent.injury_proneness * random.random())
        appearances = int(max_appearances * injury_factor * 0.8)
        
        # Goals based on position and skill
        if agent.position == "FWD":
            goals = int(agent.skill / 10 * random.uniform(0.5, 1.5))
        elif agent.position == "MID":
            goals = int(agent.skill / 20 * random.uniform(0.3, 1.0))
        else:
            goals = random.randint(0, 2)
        
        assists = int(goals * random.uniform(0.3, 0.8))
        
        results[agent.id] = {
            "goals": goals,
            "assists": assists,
            "appearances": appearances,
            "max_appearances": max_appearances,
            "avg_rating": 6.0 + (agent.skill / 50) + random.uniform(-0.5, 0.5),
            "clean_sheets": random.randint(0, 15) if agent.position in ["GK", "DEF"] else 0,
            "yellow_cards": int(agent.aggression * 5 * random.random()),
            "red_cards": 1 if random.random() < agent.aggression * 0.1 else 0,
            "winning_goals": random.randint(0, 3) if goals > 5 else 0,
            "late_goals": random.randint(0, 2) if goals > 3 else 0,
        }
    
    return results


def mock_political_simulation(agents: List[PoliticalAgent]) -> Dict[str, Dict[str, Any]]:
    """Mock simulation for testing political agent evolution."""
    results = {}
    
    for agent in agents:
        # Vote share based on charisma and public favor
        base_votes = agent.public_favor * 50 + agent.charisma * 30
        vote_share = min(1.0, max(0.0, (base_votes + random.uniform(-20, 20)) / 100))
        
        results[agent.id] = {
            "vote_share": vote_share,
            "policies_passed": int(agent.policy_depth * 5 * random.random()),
            "scandals_survived": agent.scandals_survived,
            "scandals_caused": random.randint(0, 2) if agent.deception > 0.7 else 0,
            "debates_won": int(agent.charisma * 3 * random.random()),
            "viral_moments": random.randint(0, 5),
            "controversies": int(agent.aggression * 3 * random.random()),
            "public_engagement": agent.charisma * random.uniform(0.5, 1.0),
        }
    
    return results


# =============================================================================
# CLI
# =============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Evolution Engine")
    parser.add_argument("domain", choices=["financial", "athletic", "political"],
                        help="Agent domain")
    parser.add_argument("--generations", "-g", type=int, default=5,
                        help="Number of generations to run")
    parser.add_argument("--population", "-p", type=int, default=20,
                        help="Population size")
    parser.add_argument("--seed", "-s", help="Random seed")
    parser.add_argument("--save", help="Save final state to file")
    parser.add_argument("--load", help="Load state from file")
    
    args = parser.parse_args()
    
    # Create config
    config = EvolutionConfig(population_size=args.population)
    
    # Create engine
    engine = EvolutionEngine(args.domain, config, seed=args.seed)
    
    # Load or genesis
    if args.load and os.path.exists(args.load):
        engine.load_state(args.load)
    else:
        engine.genesis()
    
    # Select mock simulation
    if args.domain == "financial":
        sim_func = mock_financial_simulation
    elif args.domain == "athletic":
        sim_func = mock_athletic_simulation
    else:
        sim_func = mock_political_simulation
    
    # Run evolution
    print(f"\n🧬 Starting Evolution: {args.domain}")
    print(f"   Population: {args.population}")
    print(f"   Generations: {args.generations}")
    
    for _ in range(args.generations):
        summary = engine.run_season(sim_func)
    
    # Results
    print(f"\n{'='*50}")
    print("🏁 EVOLUTION COMPLETE")
    print(f"{'='*50}")
    
    champions = engine.get_top_agents(3)
    print("\n🏆 Top 3 Agents:")
    for i, champ in enumerate(champions):
        arch = getattr(champ, 'archetype', 'unknown')
        arch_name = arch.value if hasattr(arch, 'value') else str(arch)
        print(f"   {i+1}. {champ.name} ({arch_name}) - Fitness: {champ.fitness_score:.1f}")
    
    # Save if requested
    if args.save:
        engine.save_state(args.save)




