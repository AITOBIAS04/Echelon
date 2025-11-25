import sys
import hashlib
import random
import json

# --- 1. PROVABLY FAIR SEED LOGIC ---
def get_provable_game_hash(server_seed, client_seed, nonce):
    combined_string = f"{server_seed}-{client_seed}-{nonce}"
    game_hash = hashlib.sha256(combined_string.encode()).hexdigest()
    return game_hash

# --- 2. THE MARKET & AGENT BLUEPRINTS ---
class Asset:
    def __init__(self, name, starting_price):
        self.name = name
        self.price = starting_price
        self.price_history = [starting_price]

    def update_price(self, buy_pressure, sell_pressure):
        # A simple algorithm to move the price
        # More buys = price up, More sells = price down
        price_change_factor = (buy_pressure - sell_pressure) / 100
        # Add a tiny bit of seeded random volatility
        volatility = random.uniform(-0.01, 0.01)
        price_change = self.price * (price_change_factor + volatility)
        
        self.price += price_change
        # Ensure price never goes below zero
        if self.price < 1:
            self.price = 1
            
        self.price_history.append(self.price)

# --- Define Trader Agent "Personalities" ---
class BaseTrader:
    def __init__(self, cash):
        self.cash = cash
        self.shares = 0

    def decide_action(self, asset, news_sentiment):
        # Default: do nothing
        return "HOLD"

class MomentumTrader(BaseTrader):
    def decide_action(self, asset, news_sentiment):
        # "If price went up 2 turns in a row, I buy"
        if len(asset.price_history) < 3:
            return "HOLD"
        
        if asset.price_history[-1] > asset.price_history[-2] > asset.price_history[-3] and self.cash > asset.price:
            return "BUY"
        elif asset.price_history[-1] < asset.price_history[-2] < asset.price_history[-3] and self.shares > 0:
            return "SELL"
        return "HOLD"

class ValueInvestor(BaseTrader):
    def decide_action(self, asset, news_sentiment):
        # "If price is below its average, I buy"
        avg_price = sum(asset.price_history) / len(asset.price_history)
        if asset.price < (avg_price * 0.9) and self.cash > asset.price:
            return "BUY"
        elif asset.price > (avg_price * 1.1) and self.shares > 0:
            return "SELL"
        return "HOLD"

class RetailTrader(BaseTrader):
    def decide_action(self, asset, news_sentiment):
        # "I follow the news!"
        if news_sentiment > 0.5 and self.cash > asset.price:
            return "BUY"
        elif news_sentiment < -0.5 and self.shares > 0:
            return "SELL"
        return "HOLD"

# --- 3. THE MAIN SIMULATION ---
def run_simulation(server_seed, client_seed, nonce):
    
    # 1. Get provably fair "what if" seed
    game_hash = get_provable_game_hash(server_seed, client_seed, nonce)
    
    # 2. Seed all randomness
    random.seed(game_hash)
    
    # 3. Create the Asset
    # We'll simulate one asset: "Sim-Apple" (SAPL)
    sapl = Asset("SAPL", starting_price=100.0)

    # 4. Create the "Provably Fair" Event Queue
    # The seeds determine the "news" for the simulated day
    possible_events = [
        {"sentiment": 0.8, "news": "SAPL announces new product!"},
        {"sentiment": -0.7, "news": "SAPL factory shutdown."},
        {"sentiment": 0.0, "news": "Market is flat."},
        {"sentiment": 0.5, "news": "Strong economic data."},
        {"sentiment": -0.4, "news": "Interest rate fears."}
    ]
    # The 'random' module is seeded, so this shuffle is deterministic
    event_queue = random.choices(possible_events, k=100) # 100 turns

    # 5. Create the Agent Population
    # The seeds determine the starting agent mix
    agent_types = [MomentumTrader, ValueInvestor, RetailTrader]
    agents = []
    for _ in range(100):
        # The 'random' module is seeded, so this choice is deterministic
        agent_type = random.choice(agent_types)
        agents.append(agent_type(cash=1000.0))

    # 6. Run the "Market Day" (100 turns)
    starting_price = sapl.price
    
    for turn in range(100):
        # Get the "news" for this turn
        current_event = event_queue[turn]
        news_sentiment = current_event["sentiment"]
        
        buy_pressure = 0
        sell_pressure = 0
        
        # Each agent makes a decision
        for agent in agents:
            action = agent.decide_action(sapl, news_sentiment)
            if action == "BUY":
                agent.cash -= sapl.price
                agent.shares += 1
                buy_pressure += 1
            elif action == "SELL":
                agent.cash += sapl.price
                agent.shares -= 1
                sell_pressure += 1
        
        # Market maker adjusts the price
        sapl.update_price(buy_pressure, sell_pressure)

    # 7. Determine the "Truth"
    final_price = sapl.price
    
    if final_price > starting_price * 1.05: # Price up > 5%
        return "SAPL_UP"
    elif final_price < starting_price * 0.95: # Price down > 5%
        return "SAPL_DOWN"
    else:
        return "SAPL_FLAT"

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