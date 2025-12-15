import random
import time
import json
from typing import List
# Use the absolute import pattern for the monorepo
from backend.simulation.genome import AgentGenome

# --- CONFIGURATION ---
POPULATION_SIZE = 10
GENERATIONS = 5

class BreedingLab:
    def __init__(self):
        self.population: List[AgentGenome] = []
        self.generation_count = 1

    def genesis(self):
        """Create the initial random population"""
        print(f"--- 🧬 GENESIS: Generation {self.generation_count} ---")
        self.population = []

        for i in range(POPULATION_SIZE):
            # Create random genome
            genome = AgentGenome(
                aggression=random.random(),
                deception=random.random(),
                risk_tolerance=random.random(),
                archetype=random.choice(['Warlord', 'Diplomat', 'Spy', 'Merchant']),
                speech_style=random.choice(['Formal', 'Aggressive', 'Cryptic', 'Poetic']),
                secret_objective="SURVIVE"
            )
            self.population.append(genome)
            print(f"   ✨ Created Agent {i+1}: {genome.archetype} (Agg: {genome.aggression:.2f})")

    def evaluate_fitness(self, genome: AgentGenome) -> float:
        """
        MOCK SIMULATION: In the real game, this comes from actual wins/losses.
        For this test, we reward 'Balanced Aggression' and 'Calculated Risk'.
        """
        score = 0
        
        # 1. Survival Score (Randomized for demo)
        score += random.randint(0, 50)
        
        # 2. Trait Bonus: We want Aggressive but not Reckless agents
        if 0.6 < genome.aggression < 0.9:
            score += 30
        
        # 3. Synergy Bonus: High Risk + High Deception (The "Shark" Strat)
        if genome.risk_tolerance > 0.7 and genome.deception > 0.6:
            score += 40
            
        return score

    def run_generation(self):
        print(f"\n--- ⚔️ RUNNING SIMULATION (Gen {self.generation_count}) ---")
        
        # 1. Score everyone
        scored_agents = []
        for genome in self.population:
            fitness = self.evaluate_fitness(genome)
            scored_agents.append((genome, fitness))
        
        # 2. Sort by fitness (Highest first)
        scored_agents.sort(key=lambda x: x[1], reverse=True)
        
        # 3. Display results
        champion = scored_agents[0]
        print(f"🏆 CHAMPION: {champion[0].archetype} (Score: {champion[1]})")
        print(f"   Stats: Agg={champion[0].aggression:.2f}, Dec={champion[0].deception:.2f}")
        
        # 4. Natural Selection (Keep top 50%)
        survivors = [agent[0] for agent in scored_agents[:POPULATION_SIZE // 2]]
        
        # 5. Breeding Phase
        next_gen = []
        
        # Elitism: The Champion clones itself perfectly (Immortal Winner)
        next_gen.append(survivors[0]) 
        
        # Breeding Loop
        while len(next_gen) < POPULATION_SIZE:
            parent_a = random.choice(survivors)
            parent_b = random.choice(survivors)
            
            # Try not to self-breed if possible
            if parent_a == parent_b and len(survivors) > 1:
                continue
                
            # The MAGIC: Create a new agent from two parents
            child = AgentGenome.breed(parent_a, parent_b)
            next_gen.append(child)
            
        self.population = next_gen
        self.generation_count += 1
        print(f"✅ Generation Complete. Population replenished to {len(self.population)}")

# --- RUNNER ---
if __name__ == "__main__":
    lab = BreedingLab()
    lab.genesis()
    
    for _ in range(GENERATIONS):
        time.sleep(1) # Pause for dramatic effect
        lab.run_generation()
        
    print("\n🏁 EVOLUTION COMPLETE 🏁")
    print("The Ultimate Agent:")
    # Use model_dump_json for Pydantic V2
    print(lab.population[0].model_dump_json(indent=2))
