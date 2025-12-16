"""
Skills-Based Brain Wrapper
==========================

Wraps the Skills System (SkillRouter + ContextCompiler) to provide
a drop-in replacement for AgentBrain in market simulations.

This provides:
- Multi-provider routing (Layer 1: Rules, Layer 2: Groq/Devstral, Layer 3: Claude)
- Cost optimization (90%+ decisions use free rules)
- Automatic context compilation
"""

import asyncio
from typing import Dict, Any, Optional
from dataclasses import dataclass

from backend.skills import SkillRouter, ContextCompiler
from backend.skills.skill_router import DecisionLayer


@dataclass
class Decision:
    """Decision result compatible with AgentBrain interface."""
    action: str  # "BUY", "SELL", "HOLD"
    confidence: float  # 0-1
    reasoning: str
    provider_used: str
    latency_ms: float


class SkillsBrain:
    """
    Skills-based brain that uses the multi-provider routing system.
    
    Drop-in replacement for AgentBrain with automatic cost optimization.
    """
    
    def __init__(self, force_layer: Optional[DecisionLayer] = None):
        """
        Initialize skills-based brain.
        
        Args:
            force_layer: Force a specific layer (None = auto-route)
        """
        self.skill_router = SkillRouter()
        self.context_compiler = ContextCompiler()
        self.force_layer = force_layer
    
    async def decide(
        self,
        agent_id: str,
        archetype: str,
        market_data: Dict[str, Any],
    ) -> Decision:
        """
        Make a trading decision using the Skills System.
        
        Args:
            agent_id: Agent identifier
            archetype: Agent archetype (SHARK, WHALE, etc.)
            market_data: Market context (sentiment, trend, price)
        
        Returns:
            Decision object with action, confidence, reasoning
        """
        # Create agent proxy for context compiler
        class AgentProxy:
            def __init__(self, agent_id, archetype, market_data):
                self.id = agent_id
                self.archetype = archetype
                self.bankroll = market_data.get("bankroll", 1000.0)
                self.aggression = 0.7 if archetype == "SHARK" else 0.5
                self.risk_tolerance = 0.7 if archetype == "SHARK" else 0.5
        
        agent = AgentProxy(agent_id, archetype, market_data)
        
        # Compile context for trade decision
        market = {
            "id": f"market_{agent_id}",
            "yes_price": 0.5 + (market_data.get("sentiment", 0) * 0.3),
            "no_price": 0.5 - (market_data.get("sentiment", 0) * 0.3),
            "current_liquidity": 10000,
            "volume_24h": 5000,
            "hours_to_expiry": 24,
            "spread": 0.02,
        }
        
        context = self.context_compiler.compile_for_trade(
            agent=agent,
            market=market,
            signals=[],
        )
        
        # Route decision through Skills System
        routing_decision = await self.skill_router.route(
            context=context,
            force_layer=self.force_layer,
        )
        
        # Convert RoutingDecision to Decision format
        return Decision(
            action=routing_decision.action,
            confidence=routing_decision.confidence,
            reasoning=routing_decision.reasoning,
            provider_used=routing_decision.provider_name,
            latency_ms=routing_decision.latency_ms,
        )





