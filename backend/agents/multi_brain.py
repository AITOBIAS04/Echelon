"""
Multi-Provider Agent Brain
===========================
Cost-optimized agent decision system with multiple backends:

1. RULE_BASED (Free) - Fast heuristic decisions
2. LOCAL_LLM (Free) - Ollama/LM Studio for development
3. GROQ (Free tier) - Llama 3 70B, very fast
4. OPENAI (Cheap) - GPT-4o-mini, cheap & fast
5. ANTHROPIC (Best) - Claude, highest quality

Strategy:
- Use RULE_BASED for 90-95% of routine decisions
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
    OPENAI = "openai"              # GPT-4o-mini, cheap & fast
    ANTHROPIC = "anthropic"        # ~$0.003/1K tokens
    HYBRID = "hybrid"              # Smart routing

@dataclass
class BrainConfig:
    provider: BrainProvider = BrainProvider.HYBRID
    
    # API Keys (from env)
    anthropic_api_key: str = field(default_factory=lambda: os.getenv("ANTHROPIC_API_KEY", ""))
    groq_api_key: str = field(default_factory=lambda: os.getenv("GROQ_API_KEY", ""))
    openai_api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    
    # Local LLM settings
    ollama_url: str = field(default_factory=lambda: os.getenv("OLLAMA_URL", "http://localhost:11434"))
    ollama_model: str = field(default_factory=lambda: os.getenv("OLLAMA_MODEL", "llama3:8b"))
    
    # OpenAI settings
    openai_model: str = field(default_factory=lambda: os.getenv("OPENAI_MODEL", "gpt-4o-mini"))
    
    # Hybrid settings
    llm_probability: float = 0.05  # 5% of decisions use LLM
    important_threshold: float = 0.8  # Sentiment above this always uses LLM

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
    """
    Fast, free rule-based decisions based on archetypes.
    Handles 90-95% of all decisions at zero cost.
    """
    
    # Archetype behavior profiles
    PROFILES = {
        "SHARK": {"aggression": 0.8, "risk_tolerance": 0.7, "follow_trend": True},
        "WHALE": {"aggression": 0.3, "risk_tolerance": 0.4, "follow_trend": False},
        "DEGEN": {"aggression": 0.95, "risk_tolerance": 0.95, "follow_trend": True},
        "VALUE": {"aggression": 0.2, "risk_tolerance": 0.3, "follow_trend": False},
        "MOMENTUM": {"aggression": 0.6, "risk_tolerance": 0.6, "follow_trend": True},
        "CONTRARIAN": {"aggression": 0.5, "risk_tolerance": 0.5, "follow_trend": False},
    }
    
    async def decide(self, context: Dict) -> Decision:
        start = time.time()
        
        archetype = context.get("archetype", "SHARK")
        sentiment = context.get("sentiment", 0)
        trend = context.get("trend", 0)
        price = context.get("price", 100)
        
        profile = self.PROFILES.get(archetype, self.PROFILES["SHARK"])
        
        # Decision logic
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
                
        elif archetype == "VALUE":
            # Contrarian - buy fear, sell greed
            if sentiment < -0.3 and trend < 0:
                action = "BUY"
                confidence = 0.7
                reasoning = "Value emerging in the fear."
            elif sentiment > 0.4:
                action = "SELL"
                confidence = 0.6
                reasoning = "Overextended. Taking profits."
                
        elif archetype == "MOMENTUM":
            # Follow the trend
            if trend > 0.03:
                action = "BUY"
                confidence = 0.75
                reasoning = "Strong uptrend. Riding momentum."
            elif trend < -0.03:
                action = "SELL"
                confidence = 0.75
                reasoning = "Downtrend confirmed. Exiting."
                
        elif archetype == "CONTRARIAN":
            # Always bet against the crowd
            if sentiment > 0.4:
                action = "SELL"
                confidence = 0.65
                reasoning = "Too much euphoria. Fading the crowd."
            elif sentiment < -0.4:
                action = "BUY"
                confidence = 0.65
                reasoning = "Extreme pessimism. Buying the blood."

        return Decision(
            action=action,
            confidence=confidence,
            reasoning=reasoning,
            provider_used="rule_based",
            latency_ms=(time.time() - start) * 1000
        )

class OllamaBrain(BaseBrainProvider):
    """
    Use local Ollama for free inference.
    Requires: ollama serve running locally with llama3:8b pulled.
    """
    
    def __init__(self, url: str = "http://localhost:11434", model: str = "llama3:8b"):
        self.url = url
        self.model = model
    
    async def decide(self, context: Dict) -> Decision:
        start = time.time()
        
        prompt = self._build_prompt(context)
        
        try:
            if HAS_HTTPX:
                async with httpx.AsyncClient(timeout=30) as client:
                    response = await client.post(
                        f"{self.url}/api/generate",
                        json={
                            "model": self.model,
                            "prompt": prompt,
                            "stream": False,
                            "options": {"temperature": 0.7, "num_predict": 50}
                        }
                    )
                    
                    if response.status_code != 200:
                        raise Exception(f"Ollama returned {response.status_code}")
                    
                    text = response.json().get("response", "")
                    action, reasoning = self._parse_response(text)
                    
                    return Decision(
                        action=action,
                        confidence=0.85,
                        reasoning=reasoning,
                        provider_used="ollama",
                        latency_ms=(time.time() - start) * 1000
                    )
        except Exception as e:
            print(f"⚠️ Ollama Error: {e}")
            
        # Fallback to rules
        return await RuleBasedBrain().decide(context)
    
    def _build_prompt(self, context: Dict) -> str:
        return f"""You are a {context.get('archetype', 'SHARK')} trader.
Market Sentiment: {context.get('sentiment', 0):.2f}
Price Trend: {context.get('trend', 0):.2f}
Decide: BUY, SELL, or HOLD.
Respond in EXACTLY this format:
ACTION | Short reasoning (under 10 words)
Example: BUY | Momentum strong, riding the wave."""
    
    def _parse_response(self, text: str) -> tuple[str, str]:
        """Parse 'ACTION | reasoning' format."""
        parts = text.strip().split("|")
        action = parts[0].strip().upper()
        reason = parts[1].strip() if len(parts) > 1 else "AI decision"
        
        # Sanitize action
        if "BUY" in action:
            action = "BUY"
        elif "SELL" in action:
            action = "SELL"
        else:
            action = "HOLD"
        
        return action, reason[:100]  # Limit reasoning length

class GroqBrain(BaseBrainProvider):
    """
    Use Groq for fast, cheap inference.
    Free tier: 14,400 requests/day - basically unlimited for our use case.
    """
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.url = "https://api.groq.com/openai/v1/chat/completions"
    
    async def decide(self, context: Dict) -> Decision:
        start = time.time()
        
        prompt = f"""You are a {context.get('archetype', 'SHARK')} trader.
Market Sentiment: {context.get('sentiment', 0):.2f}
Price Trend: {context.get('trend', 0):.2f}
Decide: BUY, SELL, or HOLD.
Provide a short reasoning (under 10 words).
Format: ACTION | REASONING"""
        
        try:
            if HAS_HTTPX and self.api_key:
                async with httpx.AsyncClient(timeout=10) as client:
                    response = await client.post(
                        self.url,
                        headers={
                            "Authorization": f"Bearer {self.api_key}",
                            "Content-Type": "application/json"
                        },
                        json={
                            "model": "llama3-8b-8192",
                            "messages": [{"role": "user", "content": prompt}],
                            "max_tokens": 50,
                            "temperature": 0.7
                        }
                    )
                    
                    if response.status_code != 200:
                        raise Exception(f"Groq returned {response.status_code}: {response.text}")
                    
                    text = response.json()["choices"][0]["message"]["content"]
                    
                    # Parse "BUY | reasoning"
                    parts = text.split("|")
                    action = parts[0].strip().upper()
                    reason = parts[1].strip() if len(parts) > 1 else "AI decision"
                    
                    # Sanitize action
                    if "BUY" in action:
                        action = "BUY"
                    elif "SELL" in action:
                        action = "SELL"
                    else:
                        action = "HOLD"
                    
                    return Decision(
                        action=action,
                        confidence=0.9,
                        reasoning=reason[:100],
                        provider_used="groq",
                        latency_ms=(time.time() - start) * 1000
                    )
        except Exception as e:
            print(f"⚠️ Groq Error: {e}")
            
        # Fallback to rules
        return await RuleBasedBrain().decide(context)

class OpenAIBrain(BaseBrainProvider):
    """
    Use OpenAI GPT-4o-mini for fast, affordable inference.
    Cost: ~$0.15/1M input tokens, $0.60/1M output tokens
    Very cost-effective for short trading decisions.
    """
    
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        self.api_key = api_key
        self.model = model
        self.url = "https://api.openai.com/v1/chat/completions"
    
    async def decide(self, context: Dict) -> Decision:
        start = time.time()
        
        prompt = f"""You are a {context.get('archetype', 'SHARK')} trader in a prediction market simulation.
Market Sentiment: {context.get('sentiment', 0):.2f} (-1 bearish to +1 bullish)
Price Trend: {context.get('trend', 0):.2f} (negative=falling, positive=rising)
Based on your archetype personality, decide: BUY, SELL, or HOLD.
Provide a short, punchy reasoning (under 10 words) that fits your character.
Format your response EXACTLY like this:
ACTION | REASONING
Examples:
BUY | Blood in the streets. Time to feast.
SELL | Taking profits before the dump.
HOLD | Waiting for clearer signals."""
        
        try:
            if HAS_HTTPX and self.api_key:
                async with httpx.AsyncClient(timeout=15) as client:
                    response = await client.post(
                        self.url,
                        headers={
                            "Authorization": f"Bearer {self.api_key}",
                            "Content-Type": "application/json"
                        },
                        json={
                            "model": self.model,
                            "messages": [{"role": "user", "content": prompt}],
                            "max_tokens": 50,
                            "temperature": 0.7
                        }
                    )
                    
                    if response.status_code != 200:
                        raise Exception(f"OpenAI returned {response.status_code}: {response.text}")
                    
                    text = response.json()["choices"][0]["message"]["content"]
                    
                    # Parse "BUY | reasoning"
                    parts = text.split("|")
                    action = parts[0].strip().upper()
                    reason = parts[1].strip() if len(parts) > 1 else "AI decision"
                    
                    # Sanitize action
                    if "BUY" in action:
                        action = "BUY"
                    elif "SELL" in action:
                        action = "SELL"
                    else:
                        action = "HOLD"
                    
                    return Decision(
                        action=action,
                        confidence=0.88,
                        reasoning=reason[:100],
                        provider_used="openai",
                        latency_ms=(time.time() - start) * 1000
                    )
        except Exception as e:
            print(f"⚠️ OpenAI Error: {e}")
            
        # Fallback to rules
        return await RuleBasedBrain().decide(context)

# =============================================================================
# MAIN BRAIN CLASS (HYBRID ROUTER)
# =============================================================================

class AgentBrain:
    """
    Hybrid brain that intelligently routes decisions to minimize cost.
    
    Priority:
    1. Critical decisions (high sentiment) → LLM for nuanced response
    2. Random 5-10% of decisions → LLM for "flavor" and social posts
    3. Everything else → Free rule-based logic
    
    LLM Priority:
    1. Groq (free tier, fast)
    2. OpenAI GPT-4o-mini (cheap, reliable)
    3. Ollama (local, free)
    4. Fallback to rules
    """
    
    def __init__(self, config: BrainConfig = None):
        self.config = config or BrainConfig()
        
        # Initialize providers
        self.rule_brain = RuleBasedBrain()
        self.ollama_brain = OllamaBrain(
            self.config.ollama_url,
            self.config.ollama_model
        )
        self.groq_brain = GroqBrain(self.config.groq_api_key)
        self.openai_brain = OpenAIBrain(
            self.config.openai_api_key,
            self.config.openai_model
        )
        
        # Stats
        self.stats = {
            "total_decisions": 0,
            "rule_based": 0,
            "groq": 0,
            "openai": 0,
            "ollama": 0,
        }

    async def decide(self, agent_id: str, archetype: str, market_data: Dict) -> Decision:
        """
        Make a decision using the Hybrid strategy.
        
        Args:
            agent_id: Unique agent identifier
            archetype: Agent type (SHARK, WHALE, DEGEN, etc.)
            market_data: Dict with 'sentiment', 'trend', 'price', etc.
        
        Returns:
            Decision with action, confidence, reasoning, provider
        """
        self.stats["total_decisions"] += 1
        
        context = {
            "agent_id": agent_id,
            "archetype": archetype,
            **market_data
        }
        
        # 1. Check for Critical Events (Always use LLM for nuanced response)
        sentiment = market_data.get("sentiment", 0)
        is_critical = abs(sentiment) > self.config.important_threshold
        
        # 2. Random sampling for flavor (5-10% of routine trades use LLM)
        use_llm = is_critical or (random.random() < self.config.llm_probability)
        
        if use_llm:
            # Try Groq first (fast, free tier)
            if self.config.groq_api_key:
                decision = await self.groq_brain.decide(context)
                if decision.provider_used == "groq":
                    self.stats["groq"] += 1
                    return decision
            
            # Try OpenAI (cheap, reliable)
            if self.config.openai_api_key:
                decision = await self.openai_brain.decide(context)
                if decision.provider_used == "openai":
                    self.stats["openai"] += 1
                    return decision
            
            # Try Ollama (local, free)
            decision = await self.ollama_brain.decide(context)
            if decision.provider_used == "ollama":
                self.stats["ollama"] += 1
                return decision
        
        # 3. Default to Rules (Free, instant)
        self.stats["rule_based"] += 1
        return await self.rule_brain.decide(context)
    
    def get_stats(self) -> Dict:
        """Get decision routing statistics."""
        total = self.stats["total_decisions"]
        if total == 0:
            return self.stats
        
        return {
            **self.stats,
            "rule_based_pct": f"{(self.stats['rule_based'] / total) * 100:.1f}%",
            "llm_pct": f"{((self.stats['groq'] + self.stats['openai'] + self.stats['ollama']) / total) * 100:.1f}%",
        }

# =============================================================================
# CONVENIENCE
# =============================================================================

# Global instance
_brain_instance: Optional[AgentBrain] = None

def get_brain(config: BrainConfig = None) -> AgentBrain:
    """Get or create global brain instance."""
    global _brain_instance
    if _brain_instance is None:
        _brain_instance = AgentBrain(config)
    return _brain_instance

# =============================================================================
# TESTING
# =============================================================================

if __name__ == "__main__":
    async def test():
        print("=" * 60)
        print("🧠 Agent Brain Test")
        print("=" * 60)
        
        # Test with 10% LLM probability
        brain = AgentBrain(BrainConfig(llm_probability=0.1))
        
        # Simulate 20 decisions
        for i in range(20):
            market = {
                "sentiment": random.uniform(-1, 1),
                "trend": random.uniform(-0.05, 0.05),
                "price": 100 + random.uniform(-10, 10),
            }
            
            archetype = random.choice(["SHARK", "WHALE", "DEGEN", "VALUE"])
            
            decision = await brain.decide(
                agent_id=f"test_{i}",
                archetype=archetype,
                market_data=market
            )
            
            print(f"[{archetype:10}] {decision.action:4} | "
                  f"{decision.provider_used:10} | "
                  f"{decision.reasoning[:40]}...")
        
        print("\n" + "=" * 60)
        print("📊 Stats:", json.dumps(brain.get_stats(), indent=2))
    
    asyncio.run(test())
