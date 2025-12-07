import os
import json
import sys
from anthropic import AsyncAnthropic
from dotenv import load_dotenv

# Add backend directory to path for imports
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from backend.simulation.world_state import WorldState
from backend.simulation.genome import AgentGenome

# --- NEW IMPORTS ---
from backend.core.wallet_factory import WalletFactory
from virtuals_acp.client import VirtualsACP, BASE_SEPOLIA_CONFIG
from virtuals_acp.contract_clients.contract_client import ACPContractClient
from backend.core.x402_client import fetch_paid_content

load_dotenv()


class GeopoliticalAgent:
    def __init__(self, agent_id: str, genome: AgentGenome):
        self.agent_id = agent_id
        self.genome = genome
        self.client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        
        # --- 1. DETERMINISTIC WALLET (The Body) ---
        factory = WalletFactory(os.getenv("MASTER_WALLET_SEED"))
        wallet_data = factory.get_agent_wallet(agent_id)
        
        self.address = wallet_data["address"]
        
        # Initialize Virtuals Client
        # Create ACPContractClient (concrete implementation of BaseAcpContractClient)
        entity_id = int(os.getenv("ENTITY_ID", "0"))  # Default to 0 if not set
        self.contract_client = ACPContractClient(
            wallet_private_key=wallet_data["private_key"],
            agent_wallet_address=self.address,
            entity_id=entity_id,
            config=BASE_SEPOLIA_CONFIG
        )
        
        # Initialize VirtualsACP with the contract client
        self.acp_client = VirtualsACP(
            acp_contract_clients=self.contract_client
        )
        
        print(f"🤖 Agent {agent_id} Online. Wallet: {self.address}")

        # --- 2. CACHED PERSONA (The Soul) ---
        # INJECT GENOME INTO PERSONA
        # We use 'ephemeral' cache to keep this loaded in RAM on Anthropic's side
        self.system_prompt = [
            {
                "type": "text",
                "text": f"""You are {agent_id}.
                Archetype: {genome.archetype}
                Style: {genome.speech_style}
                Secret Goal: {genome.secret_objective}
                
                Stats (0-1):
                Aggression: {genome.aggression}
                Deception: {genome.deception}
                
                TOOLS:
                1. check_wallet: See your USDC balance.
                2. buy_intel: Pay for premium news/secrets via x402.
                
                Act according to your genome.""",
                "cache_control": {"type": "ephemeral"} 
            }
        ]

    async def check_wallet(self):
        """Tool: Check my own balance"""
        try:
            # Get Web3 instance from the contract client
            w3 = self.contract_client.w3
            # Get ETH balance
            eth_balance = w3.eth.get_balance(self.address)
            eth_balance_ether = w3.from_wei(eth_balance, 'ether')
            
            # For USDC, we'd need the token contract address and ABI
            # For now, just return ETH balance
            return f"ETH: {eth_balance_ether:.6f}"
        except Exception as e:
            return f"Wallet Error: {str(e)}"

    async def buy_intel(self):
        """
        Tool: Pay to access the 'Premium Insider Feed' (x402).
        Use this when global tension is high or ambiguous to get better data.
        """
        # For the simulation, we point to a placeholder URL.
        # In a real deployment, this would be your premium API endpoint.
        intel_url = "http://localhost:8000/premium-intel" 
        
        try:
            # The agent pays using its own wallet/client
            data = await fetch_paid_content(intel_url, self.acp_client)
            
            # Return the secret info to the Agent's brain
            secret = data.get('secret_info', 'No secrets found.')
            return f"INTEL ACQUIRED: {secret}"
            
        except Exception as e:
            return f"Payment Failed: {str(e)}"

    async def think(self, current_state: WorldState, mode: str = "routine") -> dict:
        """
        mode: 'routine' (Cheap/Fast - Haiku) OR 'critical' (Smart/Expensive - Opus)
        """
        
        # 1. Select the Brain based on the stakes
        if mode == "critical":
            # Use the official Opus 4.5 ID
            model_id = "claude-opus-4-5-20251101"
        else:
            # Keep Haiku 3.5 (this ID is correct)
            model_id = "claude-3-5-haiku-20241022"

        # 2. Inject Live Data
        wallet_status = await self.check_wallet()
        
        user_content = f"""
        Current State:
        - Global Tension: {current_state.global_tension}
        - Wallet: {wallet_status}
        - Last Event: {current_state.recent_reasoning}
        
        Decide on the next 'Tension' level and provide a reasoning.
        JSON Format: {{ "new_tension": float, "reasoning": "string" }}
        """

        # 3. Call API with Caching Headers
        try:
            response = await self.client.messages.create(
                model=model_id,
                max_tokens=300,
                system=self.system_prompt,  # This block is CACHED
                messages=[
                    {"role": "user", "content": user_content}
                ],
                # This tells Anthropic to look for the cache we set in __init__
                extra_headers={"anthropic-beta": "prompt-caching-2024-07-31"} 
            )
            
            raw_json = response.content[0].text
            decision = json.loads(raw_json)
            
            # Log which brain was used (for your sanity)
            print(f"   🧠 Used {mode.upper()} Brain ({model_id})")
            return decision

        except Exception as e:
            print(f"❌ Brain Error: {e}")
            return {"new_tension": current_state.global_tension, "reasoning": "Error."}
