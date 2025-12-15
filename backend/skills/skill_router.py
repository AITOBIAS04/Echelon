"""
Skill Router
============

Tiered decision routing for agent intelligence.

Architecture:
- Layer 1 (Rule-Based): Free, <10ms, handles ~90% of decisions
- Layer 2 (Local/Budget LLM): <$0.10/M tokens, <500ms, handles ~8%
- Layer 3 (Cloud LLM): <$3/M tokens, <2s, handles ~2%

Routing Logic:
1. Check if decision is routine → Layer 1
2. Check novelty threshold → Layer 2 if moderate complexity
3. Check stakes/importance → Layer 3 for critical decisions
"""

import os
import time
import random
import hashlib
import json
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from enum import Enum
from datetime import datetime

from .context_compiler import CompiledContext
from .provider_registry import ProviderRegistry, ProviderConfig, ProviderTier


# =============================================================================
# DECISION MODEL
# =============================================================================

class DecisionLayer(Enum):
    """Which intelligence layer handled the decision."""
    LAYER_1_RULES = 1       # Rule-based heuristics
    LAYER_2_LOCAL = 2       # Local/budget LLM
    LAYER_3_CLOUD = 3       # Premium cloud LLM
    CACHED = 0              # Retrieved from cache


@dataclass
class RoutingDecision:
    """The output of the skill router."""
    action: str                     # "BUY", "SELL", "HOLD", "ACCEPT", "REJECT", etc.
    confidence: float               # 0-1
    reasoning: str                  # Explanation for the decision
    
    # Metadata
    layer_used: DecisionLayer
    provider_name: str
    latency_ms: float
    cost_usd: float
    tokens_used: int
    
    # Context
    decision_type: str
    agent_archetype: str
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "action": self.action,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "layer": self.layer_used.name,
            "provider": self.provider_name,
            "latency_ms": self.latency_ms,
            "cost_usd": self.cost_usd,
            "tokens": self.tokens_used,
        }


# =============================================================================
# LAYER 1: RULE-BASED HEURISTICS
# =============================================================================

class RuleEngine:
    """
    Fast, free rule-based decisions.
    Handles ~90% of routine decisions at zero cost.
    """
    
    # Archetype behaviour profiles
    PROFILES = {
        "SHARK": {
            "aggression": 0.8,
            "risk_tolerance": 0.7,
            "follow_trend": True,
            "buy_dip": False,
            "trade_illiquid": True,
        },
        "WHALE": {
            "aggression": 0.3,
            "risk_tolerance": 0.4,
            "follow_trend": False,
            "buy_dip": True,
            "trade_illiquid": False,
        },
        "DEGEN": {
            "aggression": 0.95,
            "risk_tolerance": 0.95,
            "follow_trend": True,
            "buy_dip": False,
            "trade_illiquid": True,
        },
        "VALUE": {
            "aggression": 0.2,
            "risk_tolerance": 0.3,
            "follow_trend": False,
            "buy_dip": True,
            "trade_illiquid": False,
        },
        "MOMENTUM": {
            "aggression": 0.6,
            "risk_tolerance": 0.6,
            "follow_trend": True,
            "buy_dip": False,
            "trade_illiquid": False,
        },
        "CONTRARIAN": {
            "aggression": 0.5,
            "risk_tolerance": 0.5,
            "follow_trend": False,
            "buy_dip": True,
            "trade_illiquid": True,
        },
        "SPY": {
            "aggression": 0.4,
            "risk_tolerance": 0.5,
            "follow_trend": False,
            "buy_dip": False,
            "trade_illiquid": False,
        },
        "DIPLOMAT": {
            "aggression": 0.2,
            "risk_tolerance": 0.3,
            "follow_trend": False,
            "buy_dip": False,
            "trade_illiquid": False,
        },
        "SABOTEUR": {
            "aggression": 0.7,
            "risk_tolerance": 0.8,
            "follow_trend": False,
            "buy_dip": False,
            "trade_illiquid": True,
        },
    }
    
    def can_handle(self, context: CompiledContext) -> bool:
        """Check if this decision can be handled by rules."""
        if context.decision_type == "trade":
            market = context.market_state
            liquidity = market.get("liquidity", 0)
            spread = market.get("spread", 1)
            if liquidity > 10000 and spread < 0.05:
                return True
        
        if context.decision_type == "diplomacy":
            if context.relationship_context:
                return "ALLY" in context.relationship_context or "RIVAL" in context.relationship_context
        
        return False
    
    def decide(self, context: CompiledContext) -> RoutingDecision:
        """Make a rule-based decision."""
        start = time.time()
        
        archetype = context.agent_archetype
        profile = self.PROFILES.get(archetype, self.PROFILES["SHARK"])
        
        if context.decision_type == "trade":
            decision = self._trade_decision(context, profile)
        elif context.decision_type == "diplomacy":
            decision = self._diplomacy_decision(context, profile)
        elif context.decision_type == "intel":
            decision = self._intel_decision(context, profile)
        else:
            decision = ("HOLD", 0.5, "No clear action indicated")
        
        action, confidence, reasoning = decision
        
        return RoutingDecision(
            action=action,
            confidence=confidence,
            reasoning=reasoning,
            layer_used=DecisionLayer.LAYER_1_RULES,
            provider_name="rule_engine",
            latency_ms=(time.time() - start) * 1000,
            cost_usd=0.0,
            tokens_used=0,
            decision_type=context.decision_type,
            agent_archetype=archetype,
        )
    
    def _trade_decision(self, context: CompiledContext, profile: Dict) -> tuple:
        """Rule-based trading decision."""
        market = context.market_state
        
        yes_price = market.get("yes_price", 0.5)
        liquidity = market.get("liquidity", 0)
        hours_to_expiry = market.get("hours_to_expiry", 100)
        
        if profile.get("trade_illiquid") and liquidity < 5000 and hours_to_expiry and hours_to_expiry < 24:
            if yes_price < 0.3:
                return ("BUY", 0.75, "Illiquid market, potential mispricing on YES")
            elif yes_price > 0.7:
                return ("SELL", 0.75, "Illiquid market, potential mispricing on NO")
        
        if profile.get("buy_dip") and yes_price < 0.25:
            return ("BUY", 0.7, "Extreme discount, contrarian opportunity")
        
        if profile.get("follow_trend"):
            if yes_price > 0.6:
                return ("BUY", 0.65, "Momentum: riding the trend higher")
            elif yes_price < 0.4:
                return ("SELL", 0.65, "Momentum: following downtrend")
        
        return ("HOLD", 0.5, "No clear edge identified")
    
    def _diplomacy_decision(self, context: CompiledContext, profile: Dict) -> tuple:
        """Rule-based diplomatic decision."""
        relationship = context.relationship_context or ""
        
        if "ALLY" in relationship:
            return ("ACCEPT", 0.8, "Ally relationship - maintaining cooperation")
        elif "RIVAL" in relationship:
            return ("REJECT", 0.8, "Rival relationship - maintaining opposition")
        
        if profile.get("aggression", 0.5) > 0.6:
            return ("REJECT", 0.6, "Aggressive stance - no new alliances")
        else:
            return ("ACCEPT", 0.6, "Open to new relationships")
    
    def _intel_decision(self, context: CompiledContext, profile: Dict) -> tuple:
        """Rule-based intel purchase decision."""
        market = context.market_state
        
        intel_price = market.get("intel_price", 100)
        market_exposure = market.get("market_exposure", 0)
        accuracy = market.get("intel_accuracy", 0.5)
        
        expected_value = market_exposure * accuracy * 0.1
        
        if expected_value > intel_price * 2:
            return ("BUY", 0.8, f"Intel ROI: {expected_value/intel_price:.1f}x expected value")
        
        return ("PASS", 0.6, "Intel price not justified by exposure")


# =============================================================================
# DECISION CACHE
# =============================================================================

class DecisionCache:
    """Cache similar decisions to avoid redundant LLM calls."""
    
    def __init__(self, ttl_seconds: int = 300):
        self.cache: Dict[str, RoutingDecision] = {}
        self.ttl_seconds = ttl_seconds
        self.hits = 0
        self.misses = 0
    
    def _hash_context(self, context: CompiledContext) -> str:
        key_data = {
            "type": context.decision_type,
            "archetype": context.agent_archetype,
            "market_id": context.market_state.get("market_id"),
            "price_bucket": round(context.market_state.get("yes_price", 0.5), 1),
            "liquidity_bucket": round(context.market_state.get("liquidity", 0) / 1000) * 1000,
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()[:16]
    
    def get(self, context: CompiledContext) -> Optional[RoutingDecision]:
        key = self._hash_context(context)
        
        if key in self.cache:
            cached = self.cache[key]
            age = (datetime.now() - cached.timestamp).total_seconds()
            
            if age < self.ttl_seconds:
                self.hits += 1
                return RoutingDecision(
                    action=cached.action,
                    confidence=cached.confidence,
                    reasoning=cached.reasoning + " [CACHED]",
                    layer_used=DecisionLayer.CACHED,
                    provider_name="cache",
                    latency_ms=0.1,
                    cost_usd=0.0,
                    tokens_used=0,
                    decision_type=context.decision_type,
                    agent_archetype=context.agent_archetype,
                )
        
        self.misses += 1
        return None
    
    def set(self, context: CompiledContext, decision: RoutingDecision):
        key = self._hash_context(context)
        self.cache[key] = decision
    
    def stats(self) -> Dict[str, Any]:
        total = self.hits + self.misses
        return {
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": f"{(self.hits/total*100) if total > 0 else 0:.1f}%",
            "cache_size": len(self.cache),
        }


# =============================================================================
# SKILL ROUTER
# =============================================================================

class SkillRouter:
    """
    Routes decisions to appropriate intelligence tier.
    
    Example:
        router = SkillRouter()
        decision = await router.route(compiled_context)
    """
    
    def __init__(
        self,
        provider_registry: Optional[ProviderRegistry] = None,
        enable_cache: bool = True,
        cache_ttl: int = 300,
    ):
        self.rule_engine = RuleEngine()
        self.providers = provider_registry or ProviderRegistry()
        self.cache = DecisionCache(ttl_seconds=cache_ttl) if enable_cache else None
        
        self.decisions_by_layer = {layer: 0 for layer in DecisionLayer}
        self.total_cost = 0.0
        self.total_latency_ms = 0.0
    
    async def route(
        self,
        context: CompiledContext,
        force_layer: Optional[DecisionLayer] = None,
        max_tier: ProviderTier = ProviderTier.STANDARD,
    ) -> RoutingDecision:
        """Route a decision to the appropriate intelligence layer."""
        
        # Check cache first
        if self.cache:
            cached = self.cache.get(context)
            if cached:
                self.decisions_by_layer[DecisionLayer.CACHED] += 1
                return cached
        
        # Determine appropriate layer
        if force_layer:
            layer = force_layer
        else:
            layer = self._determine_layer(context)
        
        # Execute decision at determined layer
        if layer == DecisionLayer.LAYER_1_RULES:
            decision = self.rule_engine.decide(context)
        elif layer == DecisionLayer.LAYER_2_LOCAL:
            decision = await self._layer_2_decision(context, max_tier)
        else:
            decision = await self._layer_3_decision(context, max_tier)
        
        # Update metrics
        self.decisions_by_layer[decision.layer_used] += 1
        self.total_cost += decision.cost_usd
        self.total_latency_ms += decision.latency_ms
        
        # Cache the decision
        if self.cache and decision.layer_used != DecisionLayer.CACHED:
            self.cache.set(context, decision)
        
        return decision
    
    def _determine_layer(self, context: CompiledContext) -> DecisionLayer:
        """Determine which layer should handle this decision."""
        
        if self.rule_engine.can_handle(context):
            if random.random() > 0.95:  # 5% exploration
                return DecisionLayer.LAYER_2_LOCAL
            return DecisionLayer.LAYER_1_RULES
        
        if self._is_high_stakes(context):
            return DecisionLayer.LAYER_3_CLOUD
        
        return DecisionLayer.LAYER_2_LOCAL
    
    def _is_high_stakes(self, context: CompiledContext) -> bool:
        """Determine if this is a high-stakes decision."""
        
        wallet = context.agent_wallet_balance
        if wallet > 0:
            position_size = context.market_state.get("position_size", 0)
            if position_size / wallet > 0.2:
                return True
        
        if context.decision_type in ["diplomacy", "sabotage", "mission"]:
            difficulty = context.market_state.get("difficulty", "MEDIUM")
            if difficulty in ["HARD", "EXPERT"]:
                return True
        
        liquidity = context.market_state.get("liquidity", 10000)
        if liquidity < 2000:
            return True
        
        return False
    
    async def _layer_2_decision(
        self,
        context: CompiledContext,
        max_tier: ProviderTier,
    ) -> RoutingDecision:
        """Make a decision using Layer 2 (local/budget LLM)."""
        
        provider = self.providers.get_cheapest_available(
            min_context=context.estimated_tokens * 2,
            max_tier=ProviderTier.BUDGET if max_tier.value >= ProviderTier.BUDGET.value else max_tier,
        )
        
        if not provider:
            return self.rule_engine.decide(context)
        
        return await self._llm_decision(context, provider, DecisionLayer.LAYER_2_LOCAL)
    
    async def _layer_3_decision(
        self,
        context: CompiledContext,
        max_tier: ProviderTier,
    ) -> RoutingDecision:
        """Make a decision using Layer 3 (cloud LLM)."""
        
        provider = self.providers.get_cheapest_available(
            min_context=context.estimated_tokens * 2,
            max_tier=max_tier,
        )
        
        if not provider:
            return await self._layer_2_decision(context, max_tier)
        
        return await self._llm_decision(context, provider, DecisionLayer.LAYER_3_CLOUD)
    
    async def _llm_decision(
        self,
        context: CompiledContext,
        provider: ProviderConfig,
        layer: DecisionLayer,
    ) -> RoutingDecision:
        """Make a decision using an LLM provider."""
        
        system_prompt = self._build_system_prompt(context)
        user_prompt = context.to_prompt()
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        
        try:
            result = await self.providers.call(
                provider=provider,
                messages=messages,
                max_tokens=150,
                temperature=0.3,
            )
            
            action, confidence, reasoning = self._parse_llm_response(
                result["content"],
                context.decision_type,
            )
            
            return RoutingDecision(
                action=action,
                confidence=confidence,
                reasoning=reasoning,
                layer_used=layer,
                provider_name=provider.name,
                latency_ms=result["latency_ms"],
                cost_usd=result["cost_usd"],
                tokens_used=result["usage"].get("input_tokens", 0) + result["usage"].get("output_tokens", 0),
                decision_type=context.decision_type,
                agent_archetype=context.agent_archetype,
            )
            
        except Exception as e:
            print(f"⚠️ LLM Error ({provider.name}): {e}")
            decision = self.rule_engine.decide(context)
            decision.reasoning += f" [LLM fallback: {str(e)[:30]}]"
            return decision
    
    def _build_system_prompt(self, context: CompiledContext) -> str:
        """Build system prompt for LLM decision."""
        
        prompts = {
            "trade": f"""You are a {context.agent_archetype} trading agent in a prediction market.
Make a trading decision based on the context provided.

Respond in EXACTLY this format:
ACTION | CONFIDENCE | REASONING

Where:
- ACTION is one of: BUY, SELL, HOLD
- CONFIDENCE is a number from 0.0 to 1.0
- REASONING is a brief explanation (under 20 words)

Example: BUY | 0.75 | Illiquid market near expiry, YES price undervalued""",

            "diplomacy": f"""You are a {context.agent_archetype} diplomatic agent.
Decide whether to accept or reject the proposal.

Respond in EXACTLY this format:
ACTION | CONFIDENCE | REASONING

Where:
- ACTION is one of: ACCEPT, REJECT, COUNTER
- CONFIDENCE is a number from 0.0 to 1.0
- REASONING is a brief explanation (under 20 words)""",

            "intel": f"""You are a {context.agent_archetype} intelligence agent.
Decide whether to purchase the intel package.

Respond in EXACTLY this format:
ACTION | CONFIDENCE | REASONING

Where:
- ACTION is one of: BUY, PASS
- CONFIDENCE is a number from 0.0 to 1.0
- REASONING is a brief explanation (under 20 words)""",

            "mission": f"""You are a {context.agent_archetype} operative.
Decide whether to accept the mission.

Respond in EXACTLY this format:
ACTION | CONFIDENCE | REASONING

Where:
- ACTION is one of: ACCEPT, REJECT
- CONFIDENCE is a number from 0.0 to 1.0
- REASONING is a brief explanation (under 20 words)""",

            "sabotage": f"""You are a {context.agent_archetype} covert operative.
Plan the sabotage operation.

Respond in EXACTLY this format:
ACTION | CONFIDENCE | REASONING

Where:
- ACTION is one of: EXECUTE, ABORT, DELAY
- CONFIDENCE is a number from 0.0 to 1.0
- REASONING is a brief explanation (under 20 words)""",
        }
        
        return prompts.get(
            context.decision_type,
            f"You are a {context.agent_archetype} agent. Make a decision based on context."
        )
    
    def _parse_llm_response(self, response: str, decision_type: str) -> tuple:
        """Parse LLM response into action, confidence, reasoning."""
        
        parts = response.strip().split("|")
        
        action = parts[0].strip().upper() if parts else "HOLD"
        
        valid_actions = {
            "trade": ["BUY", "SELL", "HOLD"],
            "diplomacy": ["ACCEPT", "REJECT", "COUNTER"],
            "intel": ["BUY", "PASS"],
            "mission": ["ACCEPT", "REJECT"],
            "sabotage": ["EXECUTE", "ABORT", "DELAY"],
        }
        
        allowed = valid_actions.get(decision_type, ["HOLD"])
        if action not in allowed:
            for a in allowed:
                if a in response.upper():
                    action = a
                    break
            else:
                action = allowed[0]
        
        confidence = 0.5
        if len(parts) > 1:
            try:
                conf_str = parts[1].strip()
                confidence = float(conf_str)
                confidence = max(0.0, min(1.0, confidence))
            except ValueError:
                pass
        
        reasoning = parts[2].strip() if len(parts) > 2 else "AI decision"
        reasoning = reasoning[:100]
        
        return action, confidence, reasoning
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get routing metrics."""
        total = sum(self.decisions_by_layer.values())
        
        return {
            "total_decisions": total,
            "by_layer": {
                layer.name: {
                    "count": count,
                    "percentage": f"{(count/total*100) if total > 0 else 0:.1f}%",
                }
                for layer, count in self.decisions_by_layer.items()
            },
            "total_cost_usd": f"${self.total_cost:.4f}",
            "avg_latency_ms": f"{(self.total_latency_ms/total) if total > 0 else 0:.2f}",
            "cache_stats": self.cache.stats() if self.cache else None,
            "provider_usage": self.providers.get_usage_summary(),
        }


# =============================================================================
# DEMO
# =============================================================================

async def demo():
    """Demonstrate the skill router."""
    print("=" * 60)
    print("🧠 SKILL ROUTER DEMO")
    print("=" * 60)
    
    router = SkillRouter()
    
    contexts = [
        CompiledContext(
            decision_type="trade",
            agent_archetype="SHARK",
            agent_wallet_balance=5000.0,
            market_state={
                "market_id": "market-001",
                "yes_price": 0.35,
                "liquidity": 3200,
                "hours_to_expiry": 8,
                "spread": 0.03,
            },
        ),
        CompiledContext(
            decision_type="trade",
            agent_archetype="WHALE",
            agent_wallet_balance=50000.0,
            market_state={
                "market_id": "market-002",
                "yes_price": 0.72,
                "liquidity": 45000,
                "hours_to_expiry": 120,
                "spread": 0.01,
            },
        ),
        CompiledContext(
            decision_type="diplomacy",
            agent_archetype="DIPLOMAT",
            agent_wallet_balance=10000.0,
            market_state={"proposal": "Alliance against SHARK faction"},
            relationship_context="ALLY - Previous cooperation successful",
        ),
    ]
    
    print("\n📊 Routing Decisions:\n")
    
    for i, ctx in enumerate(contexts, 1):
        decision = await router.route(ctx)
        
        print(f"{i}. {ctx.decision_type.upper()} ({ctx.agent_archetype})")
        print(f"   Action: {decision.action}")
        print(f"   Confidence: {decision.confidence:.0%}")
        print(f"   Reasoning: {decision.reasoning}")
        print(f"   Layer: {decision.layer_used.name}")
        print(f"   Latency: {decision.latency_ms:.2f}ms")
        print(f"   Cost: ${decision.cost_usd:.4f}")
        print()
    
    print("\n📈 Router Metrics:")
    metrics = router.get_metrics()
    print(f"   Total Decisions: {metrics['total_decisions']}")
    print(f"   Total Cost: {metrics['total_cost_usd']}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(demo())
