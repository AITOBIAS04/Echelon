import time
import random


class YieldManager:
    """
    War Bond Yield System - distributes APY to staked amounts.
    
    Now with persistence! Fixes the "infinite wealth" bug by saving
    last_payout timestamp to disk.
    """
    
    def __init__(self, apy=0.05, enable_persistence=True):
        self.apy = apy
        # Database of staked amounts per agent {agent_id: amount_usdc}
        self.stakes = {
            "Agent_Red": 5000.0, 
            "Agent_Blue": 1200.0,
            "Director_AI": 2500.0 
        }
        self.last_payout = time.time()
        self.total_distributed = 0.0
        
        # Persistence layer
        self.enable_persistence = enable_persistence
        self.persistence = None
        
        if enable_persistence:
            try:
                from backend.core.persistence_manager import get_persistence_manager
                self.persistence = get_persistence_manager()
            except ImportError:
                try:
                    from core.persistence_manager import get_persistence_manager
                    self.persistence = get_persistence_manager()
                except ImportError:
                    print("⚠️ Persistence manager not available for YieldManager")
            
            # Load saved state on startup
            if self.persistence:
                self._load_state()

    def _load_state(self):
        """Load saved economy state from disk."""
        if not self.persistence:
            return
        
        economy_data = self.persistence.load("economy", default=None)
        
        if economy_data:
            # CRITICAL: Restore last_payout to prevent "infinite wealth" on restart
            self.last_payout = economy_data.get("last_payout", time.time())
            self.stakes = economy_data.get("stakes", self.stakes)
            self.apy = economy_data.get("apy", self.apy)
            self.total_distributed = economy_data.get("total_distributed", 0)
            
            # Calculate how much time passed while server was down
            time_offline = time.time() - self.last_payout
            print(f"📂 Economy state restored:")
            print(f"   └─ Last payout: {time_offline:.1f}s ago")
            print(f"   └─ Total distributed: ${self.total_distributed:.4f}")
            print(f"   └─ Active stakes: {len(self.stakes)}")
        else:
            self.last_payout = time.time()
    
    def _save_state(self):
        """Save current economy state to disk."""
        if not self.persistence:
            return
        
        economy_data = {
            "last_payout": self.last_payout,
            "stakes": self.stakes,
            "apy": self.apy,
            "total_distributed": self.total_distributed,
        }
        
        self.persistence.save("economy", economy_data)

    def add_stake(self, agent_id: str, amount: float):
        """Call this when a user places a bet/bond"""
        if agent_id in self.stakes:
            self.stakes[agent_id] += amount
        else:
            self.stakes[agent_id] = amount
        print(f"💰 WAR BOND: Added ${amount} to {agent_id}. Total: ${self.stakes[agent_id]}")
        
        # Save after stake change
        self._save_state()

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
        tick_total = 0.0
        
        for agent_id, stake in self.stakes.items():
            # Formula: Principal * Rate * (Time / Year)
            earnings = stake * self.apy * (time_delta / seconds_in_year)
            
            # IN REALITY: This triggers an x402 or Blockchain tx
            if earnings > 0:
                # Multiply by 1000 just for the demo so you see non-zero numbers quickly
                demo_earnings = earnings * 100000 
                print(f"   💸 {agent_id}: Generated ${demo_earnings:.4f} (Real Yield: ${earnings:.8f})")
                tick_total += earnings
        
        self.last_payout = now
        self.total_distributed += tick_total
        
        # Save state after payout
        self._save_state()


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
