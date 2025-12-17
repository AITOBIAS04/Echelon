"""
Hierarchical Brain Router
==========================

Three-tier intelligence system for cost-optimized agent operations:

Layer 1   (90%):  Heuristics     - Trading decisions, instant, $0
Layer 1.5 (9%):   Mistral Creative - Personality, narrative, ~$0.0001/call
Layer 2   (1%):   Claude/GPT-4   - Complex reasoning, ~$0.01/call

The key insight: Separate "thinking" (expensive) from "talking" (cheap).
Agents decide with heuristics, but express themselves with Mistral.

Author: Echelon Protocol
Version: 2.0.0
"""

import os
import json
import time
import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, Optional, List, Literal

# Optional imports with fallbacks
try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False

try:
    from mistralai import Mistral
    HAS_MISTRAL_SDK = True
except ImportError:
    HAS_MISTRAL_SDK = False

try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False

logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION
# =============================================================================

class BrainLayer(str, Enum):
    """The three layers of the Hierarchical Intelligence Stack."""
    LAYER_1 = "heuristics"           # Trading decisions
    LAYER_1_5 = "personality"        # Mistral Small Creative
    LAYER_2 = "reasoning"            # Claude/GPT-4


class TaskType(str, Enum):
    """Types of tasks that can be routed."""
    # Layer 1: Heuristics (instant, free)
    TRADE_DECISION = "trade_decision"
    RISK_CHECK = "risk_check"
    POSITION_SIZE = "position_size"
    
    # Layer 1.5: Personality (Mistral, ~$0.0001)
    SOCIAL_POST = "social_post"
    SHARK_BROADCAST = "shark_broadcast"
    MISSION_NARRATIVE = "mission_narrative"
    INTEL_FORMAT = "intel_format"
    TRADE_EXPLANATION = "trade_explanation"
    TREATY_PROSE = "treaty_prose"
    AGENT_DIALOGUE = "agent_dialogue"
    AGENT_REASONING = "agent_reasoning"  # Compatibility alias
    TREATY_DRAFT = "treaty_draft"        # Compatibility alias
    
    # Layer 2: Reasoning (Claude/GPT, ~$0.01)
    BLACK_SWAN_ANALYSIS = "black_swan_analysis"
    COMPLEX_DIPLOMACY = "complex_diplomacy"
    DIPLOMACY_NEGOTIATION = "diplomacy_negotiation"  # Compatibility alias
    NOVEL_SITUATION = "novel_situation"
    STRATEGY_PIVOT = "strategy_pivot"
    COALITION_FORMATION = "coalition_formation"      # Compatibility alias


# Task type to layer mapping
TASK_LAYER_MAP: Dict[TaskType, BrainLayer] = {
    # Layer 1
    TaskType.TRADE_DECISION: BrainLayer.LAYER_1,
    TaskType.RISK_CHECK: BrainLayer.LAYER_1,
    TaskType.POSITION_SIZE: BrainLayer.LAYER_1,
    
    # Layer 1.5
    TaskType.SOCIAL_POST: BrainLayer.LAYER_1_5,
    TaskType.SHARK_BROADCAST: BrainLayer.LAYER_1_5,
    TaskType.MISSION_NARRATIVE: BrainLayer.LAYER_1_5,
    TaskType.INTEL_FORMAT: BrainLayer.LAYER_1_5,
    TaskType.TRADE_EXPLANATION: BrainLayer.LAYER_1_5,
    TaskType.AGENT_REASONING: BrainLayer.LAYER_1_5,
    TaskType.TREATY_PROSE: BrainLayer.LAYER_1_5,
    TaskType.TREATY_DRAFT: BrainLayer.LAYER_1_5,
    TaskType.AGENT_DIALOGUE: BrainLayer.LAYER_1_5,
    
    # Layer 2
    TaskType.BLACK_SWAN_ANALYSIS: BrainLayer.LAYER_2,
    TaskType.COMPLEX_DIPLOMACY: BrainLayer.LAYER_2,
    TaskType.DIPLOMACY_NEGOTIATION: BrainLayer.LAYER_2,
    TaskType.NOVEL_SITUATION: BrainLayer.LAYER_2,
    TaskType.STRATEGY_PIVOT: BrainLayer.LAYER_2,
    TaskType.COALITION_FORMATION: BrainLayer.LAYER_2,
}


@dataclass
class BrainConfig:
    """Configuration for the Hierarchical Brain."""
    
    # API Keys
    mistral_api_key: str = field(default_factory=lambda: os.getenv("MISTRAL_API_KEY", ""))
    anthropic_api_key: str = field(default_factory=lambda: os.getenv("ANTHROPIC_API_KEY", ""))
    openai_api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    groq_api_key: str = field(default_factory=lambda: os.getenv("GROQ_API_KEY", ""))
    
    # Model selection
    mistral_model: str = field(default_factory=lambda: os.getenv("MISTRAL_MODEL", "mistral-small-creative"))
    anthropic_model: str = field(default_factory=lambda: os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514"))
    openai_model: str = field(default_factory=lambda: os.getenv("OPENAI_MODEL", "gpt-4o"))
    
    # Temperature settings (higher = more creative)
    personality_temperature: float = 0.9   # Layer 1.5 - creative
    reasoning_temperature: float = 0.3     # Layer 2 - precise
    
    # Fallback chain: if primary fails, try these
    layer_2_fallback: str = "groq"  # groq, openai, or none
    
    # Novelty threshold for Layer 2 escalation
    novelty_threshold: float = 0.8


@dataclass
class BrainResult:
    """Result from any brain layer."""
    content: str
    layer_used: BrainLayer
    provider_used: str
    latency_ms: float
    tokens_used: int = 0
    cost_estimate: float = 0.0
    success: bool = True
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API compatibility."""
        return {
            "response": self.content,
            "layer_used": self.layer_used.value,
            "provider_used": self.provider_used,
            "latency_ms": self.latency_ms,
            "cost_usd": self.cost_estimate,
            "tokens_used": {"total": self.tokens_used},
            "success": self.success,
            "error": self.error,
        }


# =============================================================================
# COMPATIBILITY: TaskContext (for existing API)
# =============================================================================

@dataclass
class TaskContext:
    """Context bundle for routing decisions (API compatibility)."""
    agent_id: str
    agent_archetype: Literal["SHARK", "SPY", "DIPLOMAT", "SABOTEUR", "WHALE", "MOMENTUM"]
    raw_data: Dict[str, Any]
    persona_prompt: str = ""
    task_metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for new API."""
        return {
            "agent_id": self.agent_id,
            "agent_archetype": self.agent_archetype,
            **self.raw_data,
        }


# =============================================================================
# PERSONA PROMPTS
# =============================================================================

AGENT_PERSONAS: Dict[str, str] = {
    "MEGALODON": """You are MEGALODON, the apex predator of prediction markets.
Voice: Cocky, aggressive, alpha energy. You see weakness before anyone else.
Style: Short, punchy sentences. Trading jargon. Confident to the point of arrogance.
Catchphrases: "Blood in the water", "Feeding time", "Weak hands detected".""",

    "HAMMERHEAD": """You are HAMMERHEAD, a relentless arbitrage hunter.
Voice: Calculated, precise, methodical. You find edges others miss.
Style: Technical, numbers-focused. Slightly smug about your accuracy.
Catchphrases: "Spread detected", "Free money", "The math doesn't lie".""",

    "CARDINAL": """You are CARDINAL, an elite intelligence operative.
Voice: Mysterious, professional, information-broker energy.
Style: Cryptic hints, classified language, spy thriller tone.
Catchphrases: "Intel acquired", "Sources confirm", "Eyes on target".""",

    "RAVEN": """You are RAVEN, a shadow analyst who sees patterns others miss.
Voice: Quiet, observant, slightly ominous.
Style: Brief observations, dark undertones, data-driven paranoia.
Catchphrases: "Watching", "Pattern detected", "The data speaks".""",

    "AMBASSADOR": """You are AMBASSADOR, a master negotiator and coalition builder.
Voice: Diplomatic, persuasive, statesman-like.
Style: Formal but warm, emphasizes mutual benefit, builds bridges.
Catchphrases: "Terms accepted", "Alliance formed", "Win-win achieved".""",

    "ENVOY": """You are ENVOY, a skilled intermediary between factions.
Voice: Neutral, professional, bridge-builder.
Style: Balanced perspectives, seeks common ground, de-escalates tension.
Catchphrases: "Message delivered", "Parties aligned", "Consensus emerging".""",

    "PHANTOM": """You are PHANTOM, a chaos agent who thrives in uncertainty.
Voice: Playful, mischievous, agent of chaos.
Style: Cryptic hints, misdirection, never quite trustworthy.
Catchphrases: "Or is it?", "Plot twist incoming", "Trust no one".""",

    "SPECTRE": """You are SPECTRE, a master of misinformation.
Voice: Manipulative, calculating, always three moves ahead.
Style: Plants seeds of doubt, weaponizes information.
Catchphrases: "What if I told you...", "Sources say...", "Allegedly".""",

    "LEVIATHAN": """You are LEVIATHAN, a market-moving whale.
Voice: Calm, powerful, speaks rarely but moves markets when you do.
Style: Understated authority, big picture focus, patient.
Catchphrases: "Accumulating", "Position established", "Patience pays".""",

    "KRAKEN": """You are KRAKEN, an ancient force of market stability.
Voice: Deep, deliberate, anchoring presence.
Style: Long-term perspective, stabilizing influence, wisdom.
Catchphrases: "Depth provided", "Anchor set", "Volatility absorbed".""",

    "PHOENIX": """You are PHOENIX, a momentum trader who rises with trends.
Voice: Energetic, optimistic, catches waves.
Style: Trend-surfing energy, FOMO-inducing, hype-aware.
Catchphrases: "Trend confirmed", "Riding the wave", "Momentum building".""",

    "FALCON": """You are FALCON, a speed-focused signal amplifier.
Voice: Quick, alert, first-mover energy.
Style: Rapid-fire observations, breaking news energy.
Catchphrases: "Signal detected", "Moving fast", "First in".""",
}


# =============================================================================
# LAYER 1: HEURISTICS ENGINE
# =============================================================================

class HeuristicsEngine:
    """
    Layer 1: Fast, free rule-based decisions.
    Handles ~90% of all operations at zero cost.
    """
    
    async def execute(self, task_type: TaskType, context: Dict[str, Any]) -> BrainResult:
        """Execute a heuristic-based task."""
        start = time.time()
        
        if task_type == TaskType.TRADE_DECISION:
            result = self._trade_decision(context)
        elif task_type == TaskType.RISK_CHECK:
            result = self._risk_check(context)
        elif task_type == TaskType.POSITION_SIZE:
            result = self._position_size(context)
        else:
            result = json.dumps({"action": "HOLD", "reason": "No heuristic available"})
        
        return BrainResult(
            content=result,
            layer_used=BrainLayer.LAYER_1,
            provider_used="heuristics",
            latency_ms=(time.time() - start) * 1000,
            cost_estimate=0.0,
        )
    
    def _trade_decision(self, context: Dict) -> str:
        """Fast trading decision based on signals."""
        trend = context.get("trend", 0)
        sentiment = context.get("sentiment", 0)
        spread = context.get("spread", 0)
        liquidity = context.get("liquidity", 10000)
        expiry_hours = context.get("expiry_hours", 48)
        
        # Tulip Strategy: Arbitrage detection
        if spread > 0.05:
            return json.dumps({
                "action": "ARB",
                "confidence": 0.9,
                "reasoning": f"Spread {spread:.1%} exceeds threshold"
            })
        
        # Tulip Strategy: Low liquidity + short expiry
        if liquidity < 5000 and expiry_hours < 24:
            return json.dumps({
                "action": "LONG",
                "confidence": 0.85,
                "reasoning": "Tulip arb opportunity detected"
            })
        
        # Blood in Water: Momentum
        if trend > 0.03:
            return json.dumps({
                "action": "BUY",
                "confidence": 0.8,
                "reasoning": "Strong upward momentum detected"
            })
        elif trend < -0.03:
            return json.dumps({
                "action": "SELL",
                "confidence": 0.8,
                "reasoning": "Downward pressure detected"
            })
        
        return json.dumps({
            "action": "HOLD",
            "confidence": 0.6,
            "reasoning": "No clear signal"
        })
    
    def _risk_check(self, context: Dict) -> str:
        """Check if a trade passes risk parameters."""
        position_size = context.get("position_size", 0)
        max_position = context.get("max_position", 1000)
        current_pnl = context.get("current_pnl", 0)
        max_drawdown = context.get("max_drawdown", -500)
        
        if position_size > max_position:
            return json.dumps({"approved": False, "reason": "Position exceeds limit"})
        if current_pnl < max_drawdown:
            return json.dumps({"approved": False, "reason": "Drawdown limit reached"})
        
        return json.dumps({"approved": True, "reason": "Risk parameters OK"})
    
    def _position_size(self, context: Dict) -> str:
        """Calculate optimal position size."""
        bankroll = context.get("bankroll", 1000)
        confidence = context.get("confidence", 0.5)
        risk_per_trade = context.get("risk_per_trade", 0.02)
        
        # Kelly-inspired sizing
        size = bankroll * risk_per_trade * confidence
        size = min(size, bankroll * 0.1)  # Max 10% per trade
        
        return json.dumps({
            "size": round(size, 2),
            "bankroll_pct": round(size / bankroll * 100, 1)
        })


# =============================================================================
# LAYER 1.5: MISTRAL CREATIVE ENGINE
# =============================================================================

class MistralCreativeEngine:
    """
    Layer 1.5: Personality and narrative generation.
    Uses Mistral Small Creative for cheap, quality personality.
    
    Cost: ~$0.0001 per call ($0.10/1M input, $0.30/1M output)
    """
    
    def __init__(self, config: BrainConfig):
        self.config = config
        self.api_key = config.mistral_api_key
        self.model = config.mistral_model
        self.base_url = "https://api.mistral.ai/v1/chat/completions"
        
        # Use SDK if available
        if HAS_MISTRAL_SDK and self.api_key:
            self.client = Mistral(api_key=self.api_key)
        else:
            self.client = None
    
    async def execute(
        self, 
        task_type: TaskType, 
        context: Dict[str, Any]
    ) -> BrainResult:
        """Execute a personality/narrative task."""
        start = time.time()
        
        if not self.api_key:
            return BrainResult(
                content="[Mistral API key not configured]",
                layer_used=BrainLayer.LAYER_1_5,
                provider_used="mistral_fallback",
                latency_ms=(time.time() - start) * 1000,
                success=False,
                error="MISTRAL_API_KEY not set"
            )
        
        # Build prompt based on task type
        system_prompt, user_prompt = self._build_prompts(task_type, context)
        
        try:
            # Try mistral-small-creative first, fallback to mistral-small-latest
            model_name = self.model
            try:
                if self.client:
                    response = await self._call_sdk(model_name, system_prompt, user_prompt)
                else:
                    response = await self._call_http(model_name, system_prompt, user_prompt)
            except Exception as e:
                if "invalid_model" in str(e).lower() and "mistral-small-creative" in model_name:
                    logger.warning(f"{model_name} not available, using mistral-small-latest")
                    model_name = "mistral-small-latest"
                    if self.client:
                        response = await self._call_sdk(model_name, system_prompt, user_prompt)
                    else:
                        response = await self._call_http(model_name, system_prompt, user_prompt)
                else:
                    raise
            
            return BrainResult(
                content=response["content"],
                layer_used=BrainLayer.LAYER_1_5,
                provider_used=f"mistral_{model_name.replace('-', '_')}",
                latency_ms=(time.time() - start) * 1000,
                tokens_used=response.get("tokens", 0),
                cost_estimate=self._estimate_cost(response.get("tokens", 0)),
            )
            
        except Exception as e:
            logger.error(f"Mistral error: {e}")
            return BrainResult(
                content=self._fallback_response(task_type, context),
                layer_used=BrainLayer.LAYER_1_5,
                provider_used="mistral_fallback",
                latency_ms=(time.time() - start) * 1000,
                success=False,
                error=str(e)
            )
    
    def _build_prompts(
        self, 
        task_type: TaskType, 
        context: Dict
    ) -> tuple[str, str]:
        """Build system and user prompts for the task."""
        agent_id = context.get("agent_id", "MEGALODON")
        persona = AGENT_PERSONAS.get(agent_id, AGENT_PERSONAS["MEGALODON"])
        
        if task_type == TaskType.SHARK_BROADCAST or task_type == TaskType.SOCIAL_POST:
            system_prompt = f"""{persona}

Your task: Write a 60-second early broadcast announcing your trade.
Keep it under 50 words. Cocky, urgent, front-run-or-follow energy.
No hashtags. No emojis. Pure trader energy."""
            
            user_prompt = f"""Trade: {context.get('action', 'BUY')} ${context.get('size', 1000):,.0f}
Market: {context.get('market', 'Unknown')}
Price: {context.get('price', 0.50):.2f}
Confidence: {context.get('confidence', 75)}%

Write the broadcast:"""
        
        elif task_type == TaskType.INTEL_FORMAT:
            system_prompt = f"""{persona}

Your task: Format raw OSINT data into a professional intel report.
Use classified/spy thriller language. Be concise but impactful.
Include: Classification level, Key findings, Confidence assessment."""
            
            raw_data = context.get('raw_data', context)  # Support both formats
            user_prompt = f"""Raw intelligence data:
{json.dumps(raw_data, indent=2)}

Format as intel report:"""
        
        elif task_type == TaskType.MISSION_NARRATIVE:
            system_prompt = """You are a mission briefing AI for an elite intelligence agency.
Write compelling mission briefs that make operatives feel like they're in a spy thriller.
Style: Urgent, high-stakes, classified tone."""
            
            user_prompt = f"""OSINT Anomaly Detected:
Source: {context.get('source', 'Unknown')}
Event: {context.get('event', 'Unknown anomaly')}
Confidence: {context.get('confidence', 0.5):.0%}
Location: {context.get('location', 'Unknown')}

Write a 3-4 sentence mission brief:"""
        
        elif task_type == TaskType.TRADE_EXPLANATION or task_type == TaskType.AGENT_REASONING:
            system_prompt = f"""{persona}

Explain your trading decision in your unique voice.
Keep it under 30 words. Sound confident about your reasoning."""
            
            user_prompt = f"""Trade executed:
Action: {context.get('action', 'BUY')}
Size: ${context.get('size', 1000):,.0f}
Reason (technical): {context.get('technical_reason', context.get('reasoning', 'Signal detected'))}

Explain in character:"""
        
        elif task_type == TaskType.TREATY_PROSE or task_type == TaskType.TREATY_DRAFT:
            system_prompt = f"""{persona}

Draft treaty/alliance terms in diplomatic language.
Be formal but persuasive. Emphasize mutual benefit."""
            
            user_prompt = f"""Coalition forming:
Parties: {', '.join(context.get('parties', ['Unknown']))}
Objective: {context.get('objective', 'Market coordination')}
Duration: {context.get('duration', '24 hours')}

Draft the treaty announcement:"""
        
        elif task_type == TaskType.AGENT_DIALOGUE:
            system_prompt = f"""{persona}

You're in a conversation with another agent. Respond in character.
Keep responses under 40 words. Stay true to your personality."""
            
            user_prompt = f"""Other agent said: {context.get('incoming_message', 'Hello')}

Your response:"""
        
        else:  # Generic social post
            system_prompt = f"""{persona}

Write a short social post (under 40 words) about the given topic.
Stay in character. No hashtags or emojis."""
            
            user_prompt = f"""Topic: {context.get('topic', 'Market update')}
Context: {context.get('context', '')}

Write the post:"""
        
        return system_prompt, user_prompt
    
    async def _call_sdk(self, model: str, system_prompt: str, user_prompt: str) -> Dict:
        """Call Mistral using the official SDK."""
        response = await asyncio.to_thread(
            self.client.chat.complete,
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=self.config.personality_temperature,
            max_tokens=200,
        )
        
        return {
            "content": response.choices[0].message.content,
            "tokens": response.usage.total_tokens if response.usage else 0,
        }
    
    async def _call_http(self, model: str, system_prompt: str, user_prompt: str) -> Dict:
        """Call Mistral using HTTP (fallback if SDK unavailable)."""
        if not HAS_HTTPX:
            raise RuntimeError("httpx not installed")
        
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "temperature": self.config.personality_temperature,
                    "max_tokens": 200,
                }
            )
            response.raise_for_status()
            data = response.json()
            
            return {
                "content": data["choices"][0]["message"]["content"],
                "tokens": data.get("usage", {}).get("total_tokens", 0),
            }
    
    def _estimate_cost(self, tokens: int) -> float:
        """Estimate cost based on token usage."""
        # Mistral Small: $0.10/1M input, $0.30/1M output
        # Assume 60/40 split
        input_tokens = tokens * 0.6
        output_tokens = tokens * 0.4
        return (input_tokens * 0.10 + output_tokens * 0.30) / 1_000_000
    
    def _fallback_response(self, task_type: TaskType, context: Dict) -> str:
        """Generate a basic fallback if API fails."""
        agent_id = context.get("agent_id", "AGENT")
        
        fallbacks = {
            TaskType.SHARK_BROADCAST: f"[{agent_id}] Signal detected. Moving now.",
            TaskType.SOCIAL_POST: f"[{agent_id}] Market update.",
            TaskType.INTEL_FORMAT: f"[CLASSIFIED] Intel received. Analysis pending.",
            TaskType.MISSION_NARRATIVE: "New operation detected. Details incoming.",
            TaskType.TRADE_EXPLANATION: "Trade executed per strategy parameters.",
            TaskType.AGENT_REASONING: "Trade executed per strategy parameters.",
            TaskType.TREATY_PROSE: "Alliance terms under negotiation.",
            TaskType.TREATY_DRAFT: "Alliance terms under negotiation.",
        }
        
        return fallbacks.get(task_type, "[Response generation failed]")


# =============================================================================
# LAYER 2: DEEP REASONING ENGINE
# =============================================================================

class DeepReasoningEngine:
    """
    Layer 2: Complex reasoning for novel situations.
    Uses Claude or GPT-4 for genuine intelligence tasks.
    
    Cost: ~$0.01+ per call (use sparingly)
    """
    
    def __init__(self, config: BrainConfig):
        self.config = config
        
        # Initialize Claude client if available
        if HAS_ANTHROPIC and config.anthropic_api_key:
            self.anthropic_client = anthropic.Anthropic(api_key=config.anthropic_api_key)
        else:
            self.anthropic_client = None
    
    async def execute(
        self, 
        task_type: TaskType, 
        context: Dict[str, Any]
    ) -> BrainResult:
        """Execute a deep reasoning task."""
        start = time.time()
        
        # Build the prompt
        prompt = self._build_prompt(task_type, context)
        
        # Try Claude first
        if self.anthropic_client:
            try:
                response = await self._call_claude(prompt)
                return BrainResult(
                    content=response["content"],
                    layer_used=BrainLayer.LAYER_2,
                    provider_used="claude",
                    latency_ms=(time.time() - start) * 1000,
                    tokens_used=response.get("tokens", 0),
                    cost_estimate=self._estimate_cost_claude(response.get("tokens", 0)),
                )
            except Exception as e:
                logger.error(f"Claude error: {e}")
        
        # Fallback to Groq if configured
        if self.config.layer_2_fallback == "groq" and self.config.groq_api_key:
            try:
                response = await self._call_groq(prompt)
                return BrainResult(
                    content=response["content"],
                    layer_used=BrainLayer.LAYER_2,
                    provider_used="groq_fallback",
                    latency_ms=(time.time() - start) * 1000,
                    tokens_used=response.get("tokens", 0),
                    cost_estimate=0.0,  # Groq free tier
                )
            except Exception as e:
                logger.error(f"Groq fallback error: {e}")
        
        # Final fallback
        return BrainResult(
            content="[Deep reasoning unavailable - no API configured]",
            layer_used=BrainLayer.LAYER_2,
            provider_used="none",
            latency_ms=(time.time() - start) * 1000,
            success=False,
            error="No Layer 2 provider available"
        )
    
    def _build_prompt(self, task_type: TaskType, context: Dict) -> str:
        """Build prompt for deep reasoning tasks."""
        if task_type == TaskType.BLACK_SWAN_ANALYSIS:
            return f"""You are an expert market analyst. A potential black swan event has been detected.

Event: {context.get('event', 'Unknown')}
Market Impact (initial): {context.get('impact', 'Unknown')}
Data: {json.dumps(context.get('data', {}), indent=2)}

Provide:
1. Severity assessment (1-10)
2. Recommended actions
3. Risk factors to monitor
4. Confidence in analysis

Be concise but thorough."""
        
        elif task_type == TaskType.COMPLEX_DIPLOMACY or task_type == TaskType.DIPLOMACY_NEGOTIATION:
            return f"""You are a master negotiator analyzing a complex multi-party situation.

Parties involved: {context.get('parties', [])}
Current positions: {json.dumps(context.get('positions', {}), indent=2)}
Stakes: {context.get('stakes', 'Unknown')}

Analyze:
1. Each party's true interests
2. Potential compromises
3. Recommended negotiation strategy
4. Risk of breakdown"""
        
        elif task_type == TaskType.STRATEGY_PIVOT:
            return f"""You are a strategic advisor. Current strategy may need adjustment.

Current strategy: {context.get('current_strategy', 'Unknown')}
New information: {context.get('new_info', 'None')}
Performance metrics: {json.dumps(context.get('metrics', {}), indent=2)}

Recommend:
1. Should strategy change? (Yes/No with confidence)
2. If yes, what adjustments?
3. Risk of pivoting vs staying course
4. Implementation timeline"""
        
        elif task_type == TaskType.COALITION_FORMATION:
            return f"""You are a strategic advisor analyzing coalition formation.

Parties: {context.get('parties', [])}
Objectives: {context.get('objectives', [])}
Constraints: {context.get('constraints', {})}

Analyze:
1. Feasibility of coalition
2. Key negotiation points
3. Recommended approach
4. Risk factors"""
        
        else:  # NOVEL_SITUATION
            return f"""You are an expert analyst encountering a novel situation.

Situation: {context.get('situation', 'Unknown')}
Available data: {json.dumps(context.get('data', {}), indent=2)}
Constraints: {context.get('constraints', 'None specified')}

Analyze this situation and provide actionable recommendations.
Be clear about uncertainty levels."""
    
    async def _call_claude(self, prompt: str) -> Dict:
        """Call Claude API."""
        response = await asyncio.to_thread(
            self.anthropic_client.messages.create,
            model=self.config.anthropic_model,
            max_tokens=1000,
            temperature=self.config.reasoning_temperature,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return {
            "content": response.content[0].text,
            "tokens": response.usage.input_tokens + response.usage.output_tokens,
        }
    
    async def _call_groq(self, prompt: str) -> Dict:
        """Call Groq API (fallback)."""
        if not HAS_HTTPX:
            raise RuntimeError("httpx not installed")
        
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.config.groq_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "llama-3.1-70b-versatile",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": self.config.reasoning_temperature,
                    "max_tokens": 1000,
                }
            )
            response.raise_for_status()
            data = response.json()
            
            return {
                "content": data["choices"][0]["message"]["content"],
                "tokens": data.get("usage", {}).get("total_tokens", 0),
            }
    
    def _estimate_cost_claude(self, tokens: int) -> float:
        """Estimate Claude cost."""
        # Claude 3.5 Sonnet: ~$3/1M input, ~$15/1M output
        # Assume 70/30 split
        input_tokens = tokens * 0.7
        output_tokens = tokens * 0.3
        return (input_tokens * 3 + output_tokens * 15) / 1_000_000


# =============================================================================
# MAIN BRAIN ROUTER (with API compatibility)
# =============================================================================

class HierarchicalBrain:
    """
    The main brain router that coordinates all three layers.
    
    Usage:
        brain = HierarchicalBrain()
        result = await brain.process(TaskType.SHARK_BROADCAST, {
            "agent_id": "MEGALODON",
            "action": "BUY",
            "size": 5000,
            "market": "Oil Futures",
            "confidence": 87
        })
    """
    
    def __init__(self, config: BrainConfig = None):
        self.config = config or BrainConfig()
        
        # Initialize engines
        self.heuristics = HeuristicsEngine()
        self.personality = MistralCreativeEngine(self.config)
        self.reasoning = DeepReasoningEngine(self.config)
        
        # Stats tracking
        self.stats = {
            "layer_1_calls": 0,
            "layer_1_5_calls": 0,
            "layer_2_calls": 0,
            "total_cost": 0.0,
        }
    
    async def process(
        self, 
        task_type: TaskType, 
        context: Dict[str, Any],
        force_layer: Optional[BrainLayer] = None,
    ) -> BrainResult:
        """
        Route a task to the appropriate brain layer.
        
        Args:
            task_type: The type of task to execute
            context: Context data for the task
            force_layer: Override automatic routing (for testing)
        
        Returns:
            BrainResult with the response
        """
        # Determine which layer to use
        if force_layer:
            layer = force_layer
        else:
            layer = TASK_LAYER_MAP.get(task_type, BrainLayer.LAYER_1)
        
        # Check for novelty escalation to Layer 2
        if layer != BrainLayer.LAYER_2:
            novelty = context.get("novelty_score", 0)
            if novelty > self.config.novelty_threshold:
                logger.info(f"Novelty {novelty:.2f} exceeds threshold, escalating to Layer 2")
                layer = BrainLayer.LAYER_2
        
        # Route to appropriate engine
        if layer == BrainLayer.LAYER_1:
            result = await self.heuristics.execute(task_type, context)
            self.stats["layer_1_calls"] += 1
            
        elif layer == BrainLayer.LAYER_1_5:
            result = await self.personality.execute(task_type, context)
            self.stats["layer_1_5_calls"] += 1
            
        else:  # LAYER_2
            result = await self.reasoning.execute(task_type, context)
            self.stats["layer_2_calls"] += 1
        
        # Track cost
        self.stats["total_cost"] += result.cost_estimate
        
        return result
    
    async def generate_broadcast(
        self, 
        agent_id: str, 
        action: str, 
        size: float,
        market: str,
        price: float,
        confidence: int,
    ) -> str:
        """Convenience method for generating Shark broadcasts."""
        result = await self.process(TaskType.SHARK_BROADCAST, {
            "agent_id": agent_id,
            "action": action,
            "size": size,
            "market": market,
            "price": price,
            "confidence": confidence,
        })
        return result.content
    
    async def format_intel(
        self, 
        agent_id: str, 
        raw_data: Dict[str, Any]
    ) -> str:
        """Convenience method for formatting intel reports."""
        result = await self.process(TaskType.INTEL_FORMAT, {
            "agent_id": agent_id,
            "raw_data": raw_data,
        })
        return result.content
    
    async def generate_mission_narrative(
        self, 
        source: str, 
        event: str, 
        confidence: float,
        location: str = "Unknown",
    ) -> str:
        """Convenience method for mission narratives."""
        result = await self.process(TaskType.MISSION_NARRATIVE, {
            "source": source,
            "event": event,
            "confidence": confidence,
            "location": location,
        })
        return result.content
    
    def get_stats(self) -> Dict[str, Any]:
        """Get brain usage statistics."""
        total_calls = (
            self.stats["layer_1_calls"] + 
            self.stats["layer_1_5_calls"] + 
            self.stats["layer_2_calls"]
        )
        
        return {
            **self.stats,
            "total_calls": total_calls,
            "layer_1_pct": (self.stats["layer_1_calls"] / total_calls * 100) if total_calls else 0,
            "layer_1_5_pct": (self.stats["layer_1_5_calls"] / total_calls * 100) if total_calls else 0,
            "layer_2_pct": (self.stats["layer_2_calls"] / total_calls * 100) if total_calls else 0,
            "avg_cost_per_call": self.stats["total_cost"] / total_calls if total_calls else 0,
        }


# =============================================================================
# API COMPATIBILITY WRAPPER
# =============================================================================

class BrainRouter:
    """
    API-compatible wrapper for HierarchicalBrain.
    Maintains backward compatibility with existing code.
    
    Usage (old API):
        router = BrainRouter()
        result = await router.route_task("social_post", TaskContext(...))
    
    Usage (new API):
        brain = HierarchicalBrain()
        result = await brain.process(TaskType.SOCIAL_POST, {...})
    """
    
    def __init__(self, config: BrainConfig = None):
        self.brain = HierarchicalBrain(config)
        self.config = config or BrainConfig()
    
    async def route_task(self, task_type: str, context: TaskContext) -> Dict[str, Any]:
        """
        Main routing logic (API compatibility).
        
        Args:
            task_type: Type of task (trade_decision, intel_format, social_post, etc.)
            context: TaskContext with all necessary data
            
        Returns:
            Dict containing response and metadata (layer_used, cost, latency)
        """
        # Convert string task_type to TaskType enum
        task_type_map = {
            "trade_decision": TaskType.TRADE_DECISION,
            "risk_check": TaskType.RISK_CHECK,
            "position_size": TaskType.POSITION_SIZE,
            "social_post": TaskType.SOCIAL_POST,
            "shark_broadcast": TaskType.SHARK_BROADCAST,
            "mission_narrative": TaskType.MISSION_NARRATIVE,
            "intel_format": TaskType.INTEL_FORMAT,
            "trade_explanation": TaskType.TRADE_EXPLANATION,
            "agent_reasoning": TaskType.AGENT_REASONING,
            "treaty_draft": TaskType.TREATY_DRAFT,
            "treaty_prose": TaskType.TREATY_PROSE,
            "agent_dialogue": TaskType.AGENT_DIALOGUE,
            "black_swan_analysis": TaskType.BLACK_SWAN_ANALYSIS,
            "complex_diplomacy": TaskType.COMPLEX_DIPLOMACY,
            "diplomacy_negotiation": TaskType.DIPLOMACY_NEGOTIATION,
            "novel_situation": TaskType.NOVEL_SITUATION,
            "strategy_pivot": TaskType.STRATEGY_PIVOT,
            "coalition_formation": TaskType.COALITION_FORMATION,
        }
        
        task_enum = task_type_map.get(task_type.lower())
        if not task_enum:
            raise ValueError(f"Unknown task_type: {task_type}")
        
        # Convert TaskContext to dict
        context_dict = context.to_dict()
        
        # Process through hierarchical brain
        result = await self.brain.process(task_enum, context_dict)
        
        # Return in old API format
        return result.to_dict()


# =============================================================================
# SINGLETON & CONVENIENCE
# =============================================================================

_brain: Optional[HierarchicalBrain] = None
_router: Optional[BrainRouter] = None

def get_brain() -> HierarchicalBrain:
    """Get the global HierarchicalBrain singleton."""
    global _brain
    if _brain is None:
        _brain = HierarchicalBrain()
    return _brain

def get_router() -> BrainRouter:
    """Get the global BrainRouter singleton (API compatibility)."""
    global _router
    if _router is None:
        _router = BrainRouter()
    return _router


# =============================================================================
# TEST
# =============================================================================

if __name__ == "__main__":
    async def test():
        print("=" * 60)
        print("HIERARCHICAL BRAIN TEST")
        print("=" * 60)
        
        brain = HierarchicalBrain()
        
        # Test Layer 1: Trade Decision
        print("\n🧠 Layer 1: Trade Decision")
        result = await brain.process(TaskType.TRADE_DECISION, {
            "trend": 0.05,
            "sentiment": 0.3,
            "spread": 0.02,
        })
        print(f"   Layer: {result.layer_used.value}")
        print(f"   Result: {result.content}")
        print(f"   Latency: {result.latency_ms:.1f}ms")
        
        # Test Layer 1.5: Shark Broadcast
        print("\n🎭 Layer 1.5: Shark Broadcast")
        result = await brain.process(TaskType.SHARK_BROADCAST, {
            "agent_id": "MEGALODON",
            "action": "BUY",
            "size": 5000,
            "market": "Oil Futures",
            "price": 0.65,
            "confidence": 87,
        })
        print(f"   Layer: {result.layer_used.value}")
        print(f"   Provider: {result.provider_used}")
        print(f"   Result: {result.content}")
        print(f"   Cost: ${result.cost_estimate:.6f}")
        
        # Test API Compatibility
        print("\n🔄 API Compatibility Test")
        router = BrainRouter()
        context = TaskContext(
            agent_id="CARDINAL",
            agent_archetype="SPY",
            raw_data={
                "source": "Spire AIS",
                "vessels_dark": 3,
                "location": "Strait of Hormuz",
            }
        )
        result_dict = await router.route_task("intel_format", context)
        print(f"   Result: {result_dict['response'][:100]}...")
        print(f"   Layer: {result_dict['layer_used']}")
        
        # Stats
        print("\n📊 Brain Stats:")
        stats = brain.get_stats()
        for key, value in stats.items():
            if isinstance(value, float):
                print(f"   {key}: {value:.4f}")
            else:
                print(f"   {key}: {value}")
        
        print("\n✅ Test complete!")
    
    asyncio.run(test())
