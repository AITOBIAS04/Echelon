import sys
import os
import hashlib
import random
import json

# --- 1. PROVABLY FAIR SEED LOGIC ---
def get_provable_game_hash(server_seed, client_seed, nonce):
    combined_string = f"{server_seed}-{client_seed}-{nonce}"
    game_hash = hashlib.sha256(combined_string.encode()).hexdigest()
    return game_hash

# --- 2. LOAD REAL-WORLD DATA ---
def get_world_state():
    # Try multiple possible paths for world_state.json
    possible_paths = [
        "simulation/world_state.json",  # When called from backend root
        "world_state.json",  # When called from backend.simulation folder
        os.path.join(os.path.dirname(__file__), "world_state.json")  # Relative to this file
    ]
    
    for path in possible_paths:
        try:
            with open(path, 'r') as f:
                state = json.load(f)
                # We use abs() in case sentiment is negative
                return state.get("global_tension_score", 0.1)
        except FileNotFoundError:
            continue
        except Exception:
            continue
    
    # Fallback if file not found in any location
    return 0.1

# --- 3. THE "NATION AGENT" BLUEPRINT ---
class NationAgent:
    def __init__(self, name, aggression_propensity):
        self.name = name
        # This is the "real-world" stat
        self.aggression = aggression_propensity
        self.military_strength = 100

    def decide_action(self):
        # The AI's decision is based on its real-world aggression
        # BUT the outcome is determined by the provably fair dice roll.
        
        # random.random() is 100% determined by our game_hash
        dice_roll = random.random() 
        
        if dice_roll < self.aggression:
            return "DECLARE_WAR"
        else:
            return "MAINTAIN_PEACE"

# --- 4. THE MAIN SIMULATION ---
def run_simulation(server_seed, client_seed, nonce):
    
    # 1. Get real-world data
    # This is the "initial condition"
    base_aggression = get_world_state()
    
    # 2. Get provably fair "what if" seed
    game_hash = get_provable_game_hash(server_seed, client_seed, nonce)
    
    # 3. Seed the simulation's randomness
    # This makes the "what if" part 100% deterministic
    random.seed(game_hash)
    
    # 4. Create the agents
    # Their starting aggression is based on the real-world news!
    red_nation = NationAgent("Red_Nation", base_aggression)
    blue_nation = NationAgent("Blue_Nation", 0.1) # A passive nation
    
    # 5. Run the "10-turn" (e.g., 10 "days") simulation
    for turn in range(10):
        action = red_nation.decide_action()
        
        if action == "DECLARE_WAR":
            # Simulation stops, a result is found
            return "WAR_DECLARED"
    
    # 6. If no war after 10 turns, peace is maintained
    return "PEACE_MAINTAINED"

# --- This runs when called from the command line ---
if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("ERROR: Invalid arguments")
        sys.exit(1)
        
    SERVER_SEED = sys.argv[1]
    CLIENT_SEED = sys.argv[2]
    NONCE = sys.argv[3]
    
    final_result = run_simulation(SERVER_SEED, CLIENT_SEED, NONCE)
    print(final_result)