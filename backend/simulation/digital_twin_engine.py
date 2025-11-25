import sys
import hashlib
import random

# --- PROVABLY FAIR SEED GENERATION ---
def get_provable_game_hash(server_seed, client_seed, nonce):
    combined_string = f"{server_seed}-{client_seed}-{nonce}"
    game_hash = hashlib.sha256(combined_string.encode()).hexdigest()
    return game_hash

# --- THE AGENT "BLUEPRINT" ---
class Agent:
    def __init__(self, name, health, attack, defense):
        self.name = name
        self.health = health
        self.attack = attack
        self.defense = defense

    def is_alive(self):
        return self.health > 0

    def take_damage(self, amount):
        # Add a bit of randomness, seeded by our hash
        damage_mod = random.uniform(0.8, 1.2)
        damage = (amount * damage_mod) - self.defense
        if damage > 0:
            self.health -= int(damage)
            return int(damage)
        return 0

# --- THE MAIN SIMULATION ---
def run_simulation(server_seed, client_seed, nonce):
    
    # 1. CREATE THE "PROVABLY FAIR" HASH
    game_hash = get_provable_game_hash(server_seed, client_seed, nonce)
    
    # 2. SEED THE RANDOMNESS
    # This is CRITICAL. It ensures our "random" battle is
    # 100% deterministic and reproducible from the seeds.
    random.seed(game_hash)
    
    # 3. GENERATE AGENT STATS FROM THE HASH
    # We use the hash to *deterministically* set stats.
    # This proves the server (you) didn't rig the stats.
    hash_as_int = int(game_hash, 16)
    
    # Agent A stats (derived from first part of hash)
    agent_a_health = 100 + (hash_as_int % 10) # Health 100-109
    agent_a_attack = 10 + (hash_as_int % 7)  # Attack 10-16
    agent_a_defense = 5 + (hash_as_int % 5)   # Defense 5-9
    
    # Agent B stats (derived from second part of hash)
    agent_b_health = 100 + ((hash_as_int // 10) % 10) # Health 100-109
    agent_b_attack = 10 + ((hash_as_int // 10) % 7)  # Attack 10-16
    agent_b_defense = 5 + ((hash_as_int // 10) % 5)   # Defense 5-9
    
    # 4. CREATE THE AGENTS
    agent_a = Agent("Agent_A", agent_a_health, agent_a_attack, agent_a_defense)
    agent_b = Agent("Agent_B", agent_b_health, agent_b_attack, agent_b_defense)

    # 5. RUN THE DUEL
    turn = 0
    while agent_a.is_alive() and agent_b.is_alive():
        if turn % 2 == 0:
            # Agent A attacks Agent B
            agent_b.take_damage(agent_a.attack)
        else:
            # Agent B attacks Agent A
            agent_a.take_damage(agent_b.attack)
        
        turn += 1
        
        # Failsafe for bugs
        if turn > 100:
            break 
            
    # 6. DETERMINE THE "TRUTH" (THE WINNER)
    if agent_a.is_alive() and not agent_b.is_alive():
        return "AGENT_A_WINS"
    elif agent_b.is_alive() and not agent_a.is_alive():
        return "AGENT_B_WINS"
    else:
        # This covers a draw or the failsafe
        return "DRAW"

# --- This part runs when called from the command line ---
if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("ERROR: Invalid arguments")
        sys.exit(1)
        
    SERVER_SEED = sys.argv[1]
    CLIENT_SEED = sys.argv[2]
    NONCE = sys.argv[3]
    
    # Run the simulation and print *only* the final result
    final_result = run_simulation(SERVER_SEED, CLIENT_SEED, NONCE)
    print(final_result)