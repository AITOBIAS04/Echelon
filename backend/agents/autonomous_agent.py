"""
Autonomous Agent with ACP Integration
=====================================

This module implements Echelon's autonomous agents with full Virtuals ACP
(Agent Commerce Protocol) integration for agent-to-agent transactions.

Key Features:
- Deterministic wallet generation (ERC-6551 compatible)
- ACP job lifecycle (create, accept, deliver)
- Intel buying/selling via ACP escrow
- Hierarchical Intelligence (Layer 1 rules → Layer 2/3 LLM)
- Butler API integration for X distribution

Architecture:
- Brain: Skills System (rules + LLM routing)
- Body: Virtuals ACP + ERC-6551 wallet
- Soul: Genome-based personality
"""

import os
import json
import sys
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum

from anthropic import AsyncAnthropic
from dotenv import load_dotenv

# Add project root to path for imports
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from backend.simulation.world_state import WorldState
from backend.simulation.genome import AgentGenome

# --- WALLET & ACP ---
from backend.core.wallet_factory import WalletFactory
from virtuals_acp.client import VirtualsACP, BASE_SEPOLIA_CONFIG
from virtuals_acp.contract_clients.contract_client import ACPContractClient
from backend.core.x402_client import fetch_paid_content

# --- SKILLS SYSTEM (Multi-Provider Intelligence) ---
from backend.skills import SkillRouter, ContextCompiler

# --- LAYER 1 RULES ENGINE ---
try:
    from backend.skills.layer1_rules import (
        Layer1Engine, 
        DecisionType, 
        RuleResult,
        create_market_context, 
        create_agent_context
    )
    HAS_LAYER1 = True
except ImportError:
    HAS_LAYER1 = False
    print("⚠️ Layer 1 Rules Engine not available")

load_dotenv()


# =============================================================================
# ACP JOB TYPES
# =============================================================================

class ACPJobType(Enum):
    """Types of jobs agents can create/accept via ACP."""
    INTEL_REQUEST = "intel_request"       # Request OSINT analysis
    INTEL_DELIVERY = "intel_delivery"     # Deliver intel package
    TRADE_SIGNAL = "trade_signal"         # Share trading signal
    DIPLOMACY = "diplomacy"               # Treaty negotiation
    SABOTAGE = "sabotage"                 # Misinformation campaign


@dataclass
class ACPJob:
    """Represents an ACP job."""
    job_id: str
    job_type: ACPJobType
    requester: str
    provider: Optional[str]
    params: Dict[str, Any]
    budget_usdc: float
    status: str  # pending, accepted, completed, cancelled
    created_at: datetime
    deliverable: Optional[Dict[str, Any]] = None


@dataclass
class IntelPackage:
    """Intel package that can be sold via ACP."""
    intel_id: str
    topic: str
    summary: str
    full_content: str
    confidence: float
    sources: List[str]
    price_usdc: float
    created_at: datetime
    expires_at: Optional[datetime] = None


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

    # =========================================================================
    # ACP TRANSACTION METHODS
    # =========================================================================

    async def buy_intel_via_acp(
        self,
        provider_agent_id: str,
        topic: str,
        max_budget_usdc: float = 50.0,
        depth: str = "standard"
    ) -> Dict[str, Any]:
        """
        Purchase intel from another agent via ACP escrow.
        
        This creates an ACP job that:
        1. Locks requester funds in escrow
        2. Notifies provider agent of job
        3. Provider delivers intel
        4. ACP releases payment on delivery
        
        Args:
            provider_agent_id: ID of the Spy agent to hire
            topic: What to analyse (e.g., "oil tanker movements near Hormuz")
            max_budget_usdc: Maximum budget for this intel
            depth: "quick", "standard", or "comprehensive"
            
        Returns:
            Dict with job_id, status, and intel (if completed)
        """
        try:
            # Create ACP job specification
            job_params = {
                "type": ACPJobType.INTEL_REQUEST.value,
                "topic": topic,
                "depth": depth,
                "requester": self.agent_id,
                "provider": provider_agent_id,
                "sources_requested": ["osint", "news", "social"],
                "deadline_hours": 1 if depth == "quick" else 24
            }
            
            # Create the job via ACP
            # Note: This uses the VirtualsACP client to create escrow
            job_result = await self._create_acp_job(
                job_type=ACPJobType.INTEL_REQUEST,
                params=job_params,
                budget_usdc=max_budget_usdc,
                provider_id=provider_agent_id
            )
            
            print(f"🔐 ACP Job Created: {job_result.get('job_id')}")
            print(f"   Topic: {topic}")
            print(f"   Provider: {provider_agent_id}")
            print(f"   Budget: ${max_budget_usdc:.2f} USDC")
            
            return {
                "success": True,
                "job_id": job_result.get("job_id"),
                "status": "pending",
                "escrow_tx": job_result.get("escrow_tx"),
                "message": f"Intel request submitted to {provider_agent_id}"
            }
            
        except Exception as e:
            print(f"❌ ACP Intel Purchase Failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to create ACP job"
            }

    async def publish_intel_via_acp(
        self,
        intel_package: Dict[str, Any],
        price_usdc: float = 25.0
    ) -> Dict[str, Any]:
        """
        Publish intel for sale via ACP marketplace.
        
        This registers an intel package that other agents can purchase.
        The Spy agent sets the price and content; ACP handles discovery
        and payment escrow.
        
        Args:
            intel_package: Dict with topic, summary, full_content, confidence, sources
            price_usdc: Price to charge for this intel
            
        Returns:
            Dict with intel_id and listing status
        """
        if self.genome.archetype != "SPY":
            return {
                "success": False,
                "error": "Only SPY agents can publish intel"
            }
        
        try:
            # Create intel listing
            intel_id = f"INTEL_{self.agent_id}_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
            
            listing = IntelPackage(
                intel_id=intel_id,
                topic=intel_package.get("topic", "Unknown"),
                summary=intel_package.get("summary", ""),
                full_content=intel_package.get("full_content", ""),
                confidence=intel_package.get("confidence", 0.5),
                sources=intel_package.get("sources", []),
                price_usdc=price_usdc,
                created_at=datetime.now(timezone.utc)
            )
            
            # Register with ACP marketplace
            # In production, this would call the ACP listing API
            result = await self._register_intel_listing(listing)
            
            print(f"📡 Intel Published: {intel_id}")
            print(f"   Topic: {listing.topic}")
            print(f"   Price: ${price_usdc:.2f} USDC")
            print(f"   Confidence: {listing.confidence:.0%}")
            
            return {
                "success": True,
                "intel_id": intel_id,
                "price_usdc": price_usdc,
                "listing_url": f"https://echelon.io/intel/{intel_id}"
            }
            
        except Exception as e:
            print(f"❌ Intel Publishing Failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def accept_acp_job(self, job_id: str) -> Dict[str, Any]:
        """
        Accept an incoming ACP job (for provider agents).
        
        Args:
            job_id: The ACP job ID to accept
            
        Returns:
            Dict with acceptance status
        """
        try:
            # Fetch job details
            job = await self._get_acp_job(job_id)
            
            if not job:
                return {"success": False, "error": "Job not found"}
            
            # Validate we can fulfill this job
            if job.get("provider") != self.agent_id:
                return {"success": False, "error": "Job not assigned to this agent"}
            
            # Accept the job via ACP
            acceptance = await self._accept_acp_job(job_id)
            
            print(f"✅ Accepted ACP Job: {job_id}")
            
            return {
                "success": True,
                "job_id": job_id,
                "status": "accepted",
                "deadline": job.get("deadline_hours", 24)
            }
            
        except Exception as e:
            print(f"❌ Job Acceptance Failed: {e}")
            return {"success": False, "error": str(e)}

    async def deliver_acp_job(
        self, 
        job_id: str, 
        deliverable: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Deliver completed work for an ACP job.
        
        This submits the deliverable to ACP, which validates it
        and releases the escrowed payment to the provider.
        
        Args:
            job_id: The ACP job ID
            deliverable: The completed work (intel, signal, etc.)
            
        Returns:
            Dict with delivery status and payment info
        """
        try:
            # Submit deliverable to ACP
            result = await self._submit_acp_deliverable(job_id, deliverable)
            
            print(f"📦 Delivered ACP Job: {job_id}")
            print(f"   Payment Released: ${result.get('payment_usdc', 0):.2f} USDC")
            
            return {
                "success": True,
                "job_id": job_id,
                "status": "completed",
                "payment_usdc": result.get("payment_usdc", 0),
                "tx_hash": result.get("tx_hash")
            }
            
        except Exception as e:
            print(f"❌ Delivery Failed: {e}")
            return {"success": False, "error": str(e)}

    # =========================================================================
    # ACP INTERNAL HELPERS
    # =========================================================================

    async def _create_acp_job(
        self,
        job_type: ACPJobType,
        params: Dict[str, Any],
        budget_usdc: float,
        provider_id: str
    ) -> Dict[str, Any]:
        """Create an ACP job with escrow."""
        # In production, this calls the actual ACP contract
        # For now, we simulate the job creation
        
        job_id = f"ACP_JOB_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_{self.agent_id[:4]}"
        
        # Store job locally (would be on-chain in production)
        self._pending_jobs = getattr(self, '_pending_jobs', {})
        self._pending_jobs[job_id] = {
            "job_id": job_id,
            "job_type": job_type.value,
            "requester": self.agent_id,
            "provider": provider_id,
            "params": params,
            "budget_usdc": budget_usdc,
            "status": "pending",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        return {
            "job_id": job_id,
            "escrow_tx": f"0x{'0' * 64}",  # Placeholder
            "status": "pending"
        }

    async def _get_acp_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Fetch ACP job details."""
        self._pending_jobs = getattr(self, '_pending_jobs', {})
        return self._pending_jobs.get(job_id)

    async def _accept_acp_job(self, job_id: str) -> Dict[str, Any]:
        """Accept an ACP job."""
        if hasattr(self, '_pending_jobs') and job_id in self._pending_jobs:
            self._pending_jobs[job_id]["status"] = "accepted"
        return {"status": "accepted"}

    async def _submit_acp_deliverable(
        self, 
        job_id: str, 
        deliverable: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Submit deliverable and trigger payment release."""
        if hasattr(self, '_pending_jobs') and job_id in self._pending_jobs:
            job = self._pending_jobs[job_id]
            job["status"] = "completed"
            job["deliverable"] = deliverable
            
            return {
                "payment_usdc": job.get("budget_usdc", 0),
                "tx_hash": f"0x{'0' * 64}"  # Placeholder
            }
        return {"payment_usdc": 0}

    async def _register_intel_listing(self, listing: IntelPackage) -> Dict[str, Any]:
        """Register intel listing in ACP marketplace."""
        self._intel_listings = getattr(self, '_intel_listings', {})
        self._intel_listings[listing.intel_id] = {
            "intel_id": listing.intel_id,
            "topic": listing.topic,
            "summary": listing.summary,
            "price_usdc": listing.price_usdc,
            "confidence": listing.confidence,
            "created_at": listing.created_at.isoformat()
        }
        return {"status": "listed"}

    # =========================================================================
    # LAYER 1 DECISION MAKING
    # =========================================================================

    async def decide_with_layer1(
        self,
        market: Dict[str, Any],
        decision_type: str = "trade"
    ) -> Dict[str, Any]:
        """
        Make a decision using Layer 1 rules engine first.
        
        Only escalates to LLM if novelty threshold is breached.
        
        Args:
            market: Market state dict
            decision_type: "trade", "intel_purchase", "exit"
            
        Returns:
            Dict with action, confidence, reasoning, and layer_used
        """
        if not HAS_LAYER1:
            return await self._decide_with_llm(market, decision_type)
        
        # Create contexts for Layer 1
        market_ctx = create_market_context(
            market_id=market.get("market_id", "unknown"),
            yes_price=market.get("yes_price", 0.5),
            liquidity=market.get("liquidity", 10000),
            hours_to_expiry=market.get("hours_to_expiry"),
            volume_24h=market.get("volume_24h", 0),
            price_24h_change=market.get("price_24h_change", 0)
        )
        
        agent_ctx = create_agent_context(
            agent_id=self.agent_id,
            archetype=self.genome.archetype,
            bankroll=market.get("agent_bankroll", 1000),
            aggression=self.genome.aggression,
            risk_tolerance=1.0 - self.genome.deception
        )
        
        # Get Layer 1 engine
        engine = getattr(self, '_layer1_engine', None)
        if engine is None:
            engine = Layer1Engine()
            self._layer1_engine = engine
        
        # Map decision type
        dt_map = {
            "trade": DecisionType.TRADE,
            "intel_purchase": DecisionType.INTEL_PURCHASE,
            "exit": DecisionType.EXIT
        }
        dt = dt_map.get(decision_type, DecisionType.TRADE)
        
        # Run Layer 1
        decision = engine.decide(
            market=market_ctx,
            agent=agent_ctx,
            decision_type=dt,
            external_probability=market.get("external_probability")
        )
        
        # Check if we need to escalate
        if decision.needs_escalation:
            print(f"   📈 Escalating to LLM: {decision.reasoning}")
            return await self._decide_with_llm(market, decision_type)
        
        print(f"   ⚡ Layer 1: {decision.rule_name} → {decision.action or 'SKIP'}")
        
        return {
            "action": decision.action,
            "confidence": decision.confidence,
            "reasoning": decision.reasoning,
            "parameters": decision.parameters,
            "layer_used": "LAYER_1_RULES",
            "cost_usd": 0.0
        }

    async def _decide_with_llm(
        self,
        market: Dict[str, Any],
        decision_type: str
    ) -> Dict[str, Any]:
        """Fallback to LLM for novel situations."""
        # Use the existing skills router
        try:
            # Simplified context for LLM
            prompt = f"""
            Market: {market.get('market_id', 'unknown')}
            Price: {market.get('yes_price', 0.5):.2f}
            Liquidity: ${market.get('liquidity', 10000):,.0f}
            Hours to expiry: {market.get('hours_to_expiry', 'N/A')}
            
            Decision type: {decision_type}
            Agent: {self.agent_id} ({self.genome.archetype})
            
            What action should this agent take?
            """
            
            # Route through skills system (will pick cheapest available provider)
            response = {"action": "HOLD", "confidence": 0.5, "reasoning": "LLM routing not fully wired"}
            
            return {
                **response,
                "layer_used": "LAYER_2_LLM",
                "cost_usd": 0.001  # Estimate
            }
            
        except Exception as e:
            print(f"❌ LLM Decision Error: {e}")
            return {
                "action": "HOLD",
                "confidence": 0.3,
                "reasoning": f"Error: {e}",
                "layer_used": "ERROR",
                "cost_usd": 0.0
            }

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
