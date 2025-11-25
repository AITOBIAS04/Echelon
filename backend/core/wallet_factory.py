import os
from eth_account import Account
from eth_utils import keccak


class WalletFactory:
    def __init__(self, master_secret: str):
        """
        master_secret: A strong random string from your .env (e.g. "MY_SUPER_SECRET_MASTER_KEY_v1")
        """
        self.master_secret = master_secret

    def get_agent_wallet(self, agent_id: str):
        """
        Deterministically generates a private key for a specific agent.
        """
        # 1. Create a unique seed for this agent
        # We combine the master secret with the agent's unique ID
        unique_string = f"{self.master_secret}_{agent_id}"
        
        # 2. Hash it to get 32 bytes (valid private key format)
        private_key_bytes = keccak(text=unique_string)
        
        # 3. Generate the Account object
        account = Account.from_key(private_key_bytes)
        
        return {
            "address": account.address,
            "private_key": account.key.hex()  # This is what Virtuals SDK needs
        }


# --- USAGE EXAMPLE ---
if __name__ == "__main__":
    # Test it out
    factory = WalletFactory("TEST_SECRET_DO_NOT_USE_IN_PROD")
    
    agent1 = factory.get_agent_wallet("Sim_Diplomat_US")
    print(f"Agent 1 Address: {agent1['address']}")
    
    agent2 = factory.get_agent_wallet("Sim_Spy_Russia")
    print(f"Agent 2 Address: {agent2['address']}")
    
    # Proof it's deterministic: Run it again, you get the EXACT same keys.
    agent1_again = factory.get_agent_wallet("Sim_Diplomat_US")
    assert agent1['address'] == agent1_again['address']
    print("✅ Deterministic generation verified.")

