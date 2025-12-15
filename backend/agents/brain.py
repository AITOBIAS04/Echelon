"""
Multi-Provider Agent Brain
===========================
Cost-optimized agent decision system with multiple backends:

1. RULE_BASED (Free) - Fast heuristic decisions
2. LOCAL_LLM (Free) - Ollama/LM Studio for development
3. GROQ (Free tier) - Llama 3 70B, very fast
4. OPENAI (Cheap) - GPT-4o-mini, good balance
5. ANTHROPIC (Best) - Claude, highest quality

Strategy:
- Use RULE_BASED for 95% of routine decisions
- Use LLM only for complex/important decisions
- Cache similar decisions to reduce calls
"""

import os
import json
import random
import asyncio
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import time

# Optional imports
try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False

try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False

# =============================================================================
# CONFIGURATION
# =============================================================================

class BrainProvider(Enum):
    RULE_BASED = "rule_based"      # Free, instant
    LOCAL_LLM = "local_llm"        # Free, requires Ollama
    GROQ = "groq"                  # Free tier, fast
    ANTHROPIC = "anthropic"        # ~$0.003/1K tokens
    HYBRID = "hybrid"              # Smart routing

@dataclass
class BrainConfig:
    provider: BrainProvider = BrainProvider.HYBRID
    
    # API Keys (from env)
    anthropic_api_key: str = field(default_factory=lambda: os.getenv("ANTHROPIC_API_KEY", ""))
    groq_api_key: str = field(default_factory=lambda: os.getenv("GROQ_API_KEY", ""))
    
    # Local LLM settings
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "llama3:8b"
    
    # Hybrid settings
    llm_probability: float = 0.05  # 5% of decisions use LLM
    important_threshold: float = 0.7  # Decisions above this always use LLM

@dataclass
class Decision:
    action: str  # "BUY", "SELL", "HOLD"
    confidence: float  # 0-1
    reasoning: str
    provider_used: str
    latency_ms: float

# =============================================================================
# PROVIDERS
# =============================================================================

class BaseBrainProvider(ABC):
    @abstractmethod
    async def decide(self, context: Dict) -> Decision:
        pass

class RuleBasedBrain(BaseBrainProvider):
    """Fast, free rule-based decisions based on archetypes."""
    
    async def decide(self, context: Dict) -> Decision:
        start = time.time()
        
        archetype = context.get("archetype", "SHARK")
        sentiment = context.get("sentiment", 0)
        trend = context.get("trend", 0)
        
        # Simple heuristic logic
        action = "HOLD"
        confidence = 0.5
        reasoning = "Market unclear."
        
        if archetype == "SHARK":
            if trend > 0.02:
                action = "BUY"
                confidence = 0.8
                reasoning = "Momentum detected. Hunting yield."
            elif trend < -0.02:
                action = "SELL"
                confidence = 0.8
                reasoning = "Weakness detected. Dumping."
        
        elif archetype == "WHALE":
            if sentiment < -0.5:
                action = "BUY"
                confidence = 0.9
                reasoning = "Extreme fear detected. Accumulating."
            elif sentiment > 0.5:
                action = "SELL"
                confidence = 0.7
                reasoning = "Taking profits into strength."
        elif archetype == "DEGEN":
            if sentiment > 0.2:
                action = "BUY"
                confidence = 0.4
                reasoning = "Vibes are good. Apeing in."
            else:
                action = "SELL"
                confidence = 0.4
                reasoning = "Vibes are off. Paper handing."
        
        return Decision(
            action=action,
            confidence=confidence,
            reasoning=reasoning,
            provider_used="rule_based",
            latency_ms=(time.time() - start) * 1000
        )

class GroqBrain(BaseBrainProvider):
    """Use Groq for fast, cheap inference."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.url = "https://api.groq.com/openai/v1/chat/completions"
    
    async def decide(self, context: Dict) -> Decision:
        start = time.time()
        
        prompt = f"""You are a {context.get('archetype')} trader.
Market Sentiment: {context.get('sentiment'):.2f}
Trend: {context.get('trend'):.2f}
Decide: BUY, SELL, or HOLD.
Provide a short reasoning (under 10 words).
Format: ACTION | REASONING"""
        
        try:
            if HAS_HTTPX and self.api_key:
                async with httpx.AsyncClient(timeout=10) as client:
                    response = await client.post(
                        self.url,
                        headers={"Authorization": f"Bearer {self.api_key}"},
                        json={
                            "model": "llama3-8b-8192",
                            "messages": [{"role": "user", "content": prompt}],
                            "max_tokens": 50
                        }
                    )
                    text = response.json()["choices"][0]["message"]["content"]
                    
                    # Parse "BUY | reasoning"
                    parts = text.split("|")
                    action = parts[0].strip().upper()
                    reason = parts[1].strip() if len(parts) > 1 else "AI decision"
                    
                    # Sanitize action
                    if "BUY" in action: action = "BUY"
                    elif "SELL" in action: action = "SELL"
                    else: action = "HOLD"
                    
                    return Decision(
                        action=action,
                        confidence=0.9,
                        reasoning=reason,
                        provider_used="groq",
                        latency_ms=(time.time() - start) * 1000
                    )
        except Exception as e:
            print(f"⚠️ Groq Error: {e}")
            
        # Fallback
        return await RuleBasedBrain().decide(context)

# =============================================================================
# MAIN BRAIN CLASS
# =============================================================================

class AgentBrain:
    def __init__(self, config: BrainConfig = None):
        self.config = config or BrainConfig()
        self.rule_brain = RuleBasedBrain()
        self.groq_brain = GroqBrain(self.config.groq_api_key)

    async def decide(self, agent_id: str, archetype: str, market_data: Dict) -> Decision:
        """
        Make a decision using the Hybrid strategy.
        """
        # 1. Check for Critical Events (Always use LLM)
        is_critical = abs(market_data.get("sentiment", 0)) > 0.8
        
        # 2. Random sampling for flavor (5% of routine trades use LLM)
        use_llm = is_critical or (random.random() < self.config.llm_probability)
        
        if use_llm and self.config.groq_api_key:
            return await self.groq_brain.decide({
                "archetype": archetype,
                **market_data
            })
        
        # 3. Default to Rules (Free)
        return await self.rule_brain.decide({
            "archetype": archetype,
            **market_data
        })
