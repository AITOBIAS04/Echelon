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

# --- SKILLS SYSTEM (Multi-Provider Intelligence) ---
from backend.skills import SkillRouter, ContextCompiler

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
        
        # --- SKILLS SYSTEM INITIALIZATION ---
        # Multi-provider decision routing (Layer 1: Rules, Layer 2: Groq/Devstral, Layer 3: Claude)
        self.skill_router = SkillRouter()
        self.context_compiler = ContextCompiler()
        
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
        Multi-provider decision routing via Skills System.
        
        The SkillRouter automatically:
        - Routes 90%+ decisions to Layer 1 (rules) - free, instant
        - Routes 8% to Layer 2 (Groq/Devstral) - fast, cheap
        - Routes 2% to Layer 3 (Claude) - slower, expensive
        
        mode: 'routine' (prefer cheaper providers) OR 'critical' (force Layer 3/Claude)
        """
        
        # 1. Compile minimal context for this decision
        wallet_status = await self.check_wallet()
        
        # Map genome archetype to skills archetype
        archetype_map = {
            "SHARK": "shark",
            "SPY": "spy",
            "DIPLOMAT": "diplomat",
            "SABOTEUR": "saboteur",
        }
        skills_archetype = archetype_map.get(self.genome.archetype, "core")
        
        # Parse wallet balance safely
        try:
            wallet_balance = float(wallet_status.split(":")[-1].strip().split()[0]) if ":" in wallet_status else 0.0
        except:
            wallet_balance = 0.0
        
        # Create simple agent object with required attributes for context compiler
        class AgentProxy:
            def __init__(self, agent_id, archetype, aggression, risk_tolerance, bankroll):
                self.id = agent_id
                self.archetype = archetype
                self.aggression = aggression
                self.risk_tolerance = risk_tolerance
                self.bankroll = bankroll
                self.loyalty = 0.5  # Default for diplomacy
                self.deception = 1.0 - risk_tolerance
                self.allies = []
                self.rivals = []
                self.memory = []
        
        agent_proxy = AgentProxy(
            agent_id=self.agent_id,
            archetype=skills_archetype.upper(),
            aggression=self.genome.aggression,
            risk_tolerance=1.0 - self.genome.deception,
            bankroll=wallet_balance
        )
        
        # Create counterparty proxy (world state)
        class CounterpartyProxy:
            def __init__(self):
                self.id = "world_state"
                self.archetype = "SYSTEM"
        
        counterparty_proxy = CounterpartyProxy()
        
        # Compile context for geopolitical decision
        context = self.context_compiler.compile_for_diplomacy(
            agent=agent_proxy,
            counterparty=counterparty_proxy,
            proposal={"tension": current_state.global_tension, "reasoning": current_state.recent_reasoning},
        )
        
        # Set decision type and importance
        context.decision_type = "diplomacy"
        if mode == "critical":
            # Force Layer 3 for critical decisions
            context.market_state["importance"] = 1.0
        else:
            context.market_state["importance"] = 0.3
        
        # 2. Route decision through Skills System
        try:
            # Force Layer 3 for critical decisions, otherwise let router decide
            from backend.skills.skill_router import DecisionLayer
            force_layer = DecisionLayer.LAYER_3_CLOUD if mode == "critical" else None
            
            decision = await self.skill_router.route(
                context=context,
                force_layer=force_layer,
            )
            
            # Parse reasoning to extract tension value
            # The router returns action, confidence, reasoning
            # We need to extract JSON from reasoning or use action
            try:
                # Try to parse JSON from reasoning
                import re
                json_match = re.search(r'\{[^}]+\}', decision.reasoning)
                if json_match:
                    parsed = json.loads(json_match.group())
                    new_tension = parsed.get("new_tension", current_state.global_tension)
                    reasoning = parsed.get("reasoning", decision.reasoning)
                else:
                    # Fallback: use action/confidence to adjust tension
                    tension_delta = 0.0
                    if "INCREASE" in decision.action.upper() or "RAISE" in decision.action.upper():
                        tension_delta = 0.1 * decision.confidence
                    elif "DECREASE" in decision.action.upper() or "LOWER" in decision.action.upper():
                        tension_delta = -0.1 * decision.confidence
                    
                    new_tension = max(0.0, min(1.0, current_state.global_tension + tension_delta))
                    reasoning = decision.reasoning
            except:
                # Ultimate fallback
                new_tension = current_state.global_tension
                reasoning = decision.reasoning
            
            # Log which layer was used
            layer_name = decision.layer_used.name if hasattr(decision, 'layer_used') else "UNKNOWN"
            provider_name = decision.provider_name if hasattr(decision, 'provider_name') else "unknown"
            cost = decision.cost_usd if hasattr(decision, 'cost_usd') else 0.0
            print(f"   🧠 Skills System: {layer_name} via {provider_name} (${cost:.6f})")
            
            return {
                "new_tension": new_tension,
                "reasoning": reasoning,
            }
            
        except Exception as e:
            print(f"❌ Skills Router Error: {e}")
            # Fallback to direct Anthropic call if skills system fails
            return await self._fallback_think(current_state, mode)
    
    async def _fallback_think(self, current_state: WorldState, mode: str = "routine") -> dict:
        """Fallback to direct Anthropic API if skills system fails."""
        if mode == "critical":
            model_id = "claude-opus-4-5-20251101"
        else:
            model_id = "claude-3-5-haiku-20241022"
        
        wallet_status = await self.check_wallet()
        user_content = f"""
        Current State:
        - Global Tension: {current_state.global_tension}
        - Wallet: {wallet_status}
        - Last Event: {current_state.recent_reasoning}
        
        Decide on the next 'Tension' level and provide a reasoning.
        JSON Format: {{ "new_tension": float, "reasoning": "string" }}
        """
        
        try:
            response = await self.client.messages.create(
                model=model_id,
                max_tokens=300,
                system=self.system_prompt,
                messages=[{"role": "user", "content": user_content}],
                extra_headers={"anthropic-beta": "prompt-caching-2024-07-31"}
            )
            raw_json = response.content[0].text
            decision = json.loads(raw_json)
            print(f"   🧠 Fallback: {mode.upper()} Brain ({model_id})")
            return decision
        except Exception as e:
            print(f"❌ Fallback Error: {e}")
            return {"new_tension": current_state.global_tension, "reasoning": "Error."}
