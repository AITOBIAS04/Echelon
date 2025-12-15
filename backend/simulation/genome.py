from pydantic import BaseModel, Field
import random


class AgentGenome(BaseModel):
    # --- MATH LAYER (Simulation Logic) ---
    # These directly affect the 'if/else' or RL probability calculations
    aggression: float = Field(..., ge=0.0, le=1.0, description="Probability of attacking")
    deception: float = Field(..., ge=0.0, le=1.0, description="Probability of lying/betraying")
    risk_tolerance: float = Field(..., ge=0.0, le=1.0, description="Willingness to lose money")
    
    # --- PERSONALITY LAYER (LLM Flavor) ---
    # These are injected into the System Prompt
    archetype: str = Field(..., description="e.g., 'The Warlord', 'The Merchant', 'The Spy'")
    speech_style: str = Field(..., description="e.g., 'Formal', 'Aggressive', 'Cryptic'")
    
    # --- SECRET OBJECTIVE (The Hidden Game) ---
    secret_objective: str = Field(default="SURVIVE", description="The private win condition")

    @classmethod
    def breed(cls, parent_a: 'AgentGenome', parent_b: 'AgentGenome') -> 'AgentGenome':
        """
        Creates a child genome by mixing parents + mutation.
        """
        mutation_rate = 0.1
        
        def mix_float(a, b):
            # Average + Mutation
            val = (a + b) / 2
            mutation = random.uniform(-mutation_rate, mutation_rate)
            return max(0.0, min(1.0, val + mutation))

        return cls(
            aggression=mix_float(parent_a.aggression, parent_b.aggression),
            deception=mix_float(parent_a.deception, parent_b.deception),
            risk_tolerance=mix_float(parent_a.risk_tolerance, parent_b.risk_tolerance),
            
            # For strings, 50/50 chance from either parent
            archetype=random.choice([parent_a.archetype, parent_b.archetype]),
            speech_style=random.choice([parent_a.speech_style, parent_b.speech_style]),
            
            # Secret objective might be inherited or random
            secret_objective=random.choice([parent_a.secret_objective, parent_b.secret_objective])
        )

