import time
import random


class YieldManager:
    def __init__(self, apy=0.05): # Default 5% APY
        self.apy = apy
        # Database of staked amounts per agent {agent_id: amount_usdc}
        self.stakes = {
            "Agent_Red": 5000.0, 
            "Agent_Blue": 1200.0,
            "Director_AI": 2500.0 
        }
        self.last_payout = time.time()


    def add_stake(self, agent_id: str, amount: float):
        """Call this when a user places a bet/bond"""
        if agent_id in self.stakes:
            self.stakes[agent_id] += amount
        else:
            self.stakes[agent_id] = amount
        print(f"💰 WAR BOND: Added ${amount} to {agent_id}. Total: ${self.stakes[agent_id]}")


    def distribute_yield(self):
        """
        The 'Tick' function. Calculates yield since last check and 'pays' the agents.
        """
        now = time.time()
        time_delta = now - self.last_payout
        
        # Only run if at least 1 second has passed (to avoid log spam)
        if time_delta < 1.0:
            return


        print(f"\n--- 🏦 YIELD PAYOUT ({time_delta:.2f}s elapsed) ---")
        
        seconds_in_year = 31536000
        
        for agent_id, stake in self.stakes.items():
            # Formula: Principal * Rate * (Time / Year)
            earnings = stake * self.apy * (time_delta / seconds_in_year)
            
            # IN REALITY: This triggers an x402 or Blockchain tx
            if earnings > 0:
                # Multiply by 1000 just for the demo so you see non-zero numbers quickly
                demo_earnings = earnings * 100000 
                print(f"   💸 {agent_id}: Generated ${demo_earnings:.4f} (Real Yield: ${earnings:.8f})")
        
        self.last_payout = now


# --- RUNNER ---
if __name__ == "__main__":
    print("Initializing War Bond Yield System...")
    manager = YieldManager(apy=0.10) # 10% APY
    
    # Simulate a few ticks
    for i in range(3):
        time.sleep(2)
        manager.distribute_yield()
        
    manager.add_stake("Agent_Red", 50000.0) # A Whale enters!
    
    time.sleep(2)
    manager.distribute_yield()
