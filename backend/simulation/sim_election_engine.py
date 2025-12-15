import sys
import hashlib
import random

# --- 1. PROVABLY FAIR SEED LOGIC ---
def get_provable_game_hash(server_seed, client_seed, nonce):
    combined_string = f"{server_seed}-{client_seed}-{nonce}"
    game_hash = hashlib.sha256(combined_string.encode()).hexdigest()
    return game_hash

# --- 2. THE AGENT BLUEPRINTS ---
class VoterAgent:
    def __init__(self, position):
        # Position is a float from -1.0 (Left) to 1.0 (Right)
        self.position = position
        
    def shift_position(self, event_effect):
        self.position += event_effect
        # Clamp position between -1.0 and 1.0
        if self.position > 1.0: self.position = 1.0
        if self.position < -1.0: self.position = -1.0

class CandidateAgent:
    def __init__(self, name, platform_position):
        self.name = name
        self.platform = platform_position

# --- 3. THE MAIN SIMULATION ---
def run_simulation(server_seed, client_seed, nonce):
    
    # 1. Get provably fair "what if" seed
    game_hash = get_provable_game_hash(server_seed, client_seed, nonce)
    
    # 2. Seed all randomness
    random.seed(game_hash)
    
    # 3. Create Candidates
    # Their platforms are deterministically generated
    cand_a_platform = random.uniform(-0.8, -0.2) # Left-leaning
    cand_b_platform = random.uniform(0.2, 0.8)  # Right-leaning
    
    candidate_a = CandidateAgent("Candidate_A", cand_a_platform)
    candidate_b = CandidateAgent("Candidate_B", cand_b_platform)

    # 4. Create "Provably Fair" Voter Population (1001 voters for no ties)
    voters = []
    for _ in range(1001):
        # The entire political landscape is generated from the seed
        voter_pos = random.uniform(-1.0, 1.0)
        voters.append(VoterAgent(voter_pos))

    # 5. Create "Provably Fair" Event Queue (30 "Days" of campaign)
    possible_events = [
        {"name": "Scandal hits Candidate A", "effect": 0.1}, # Voters move right
        {"name": "Scandal hits Candidate B", "effect": -0.1},# Voters move left
        {"name": "Good Economic News", "effect": -0.05}, # Helps incumbent (A)
        {"name": "Bad Economic News", "effect": 0.05},  # Hurts incumbent (A)
        {"name": "Candidate A Gaffe", "effect": 0.05},
        {"name": "Candidate B Gaffe", "effect": -0.05}
    ]
    # The entire 30-day news cycle is seeded and deterministic
    event_queue = random.choices(possible_events, k=30)
    
    # 6. Run the 30-Day Campaign
    for event in event_queue:
        event_effect = event["effect"]
        for voter in voters:
            voter.shift_position(event_effect)

    # 7. "Election Day": Tally the votes
    votes_a = 0
    votes_b = 0
    
    for voter in voters:
        # Voters pick the candidate "closest" to their final position
        dist_a = abs(voter.position - candidate_a.platform)
        dist_b = abs(voter.position - candidate_b.platform)
        
        if dist_a < dist_b:
            votes_a += 1
        else:
            votes_b += 1
            
    # 8. Determine the "Truth"
    if votes_a > votes_b:
        return "CANDIDATE_A_WINS"
    else:
        return "CANDIDATE_B_WINS"

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
    