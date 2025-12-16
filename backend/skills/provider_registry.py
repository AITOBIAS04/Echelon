"""
Provider Registry
=================

Multi-provider LLM management with automatic fallback and cost tracking.

Supported Providers:
- Devstral Small 2 (Mistral) - Best for code/analysis, Apache 2.0, 24B params
- Devstral 2 (Mistral) - SOTA open model, 123B params
- Groq - Free tier, fast inference
- OpenAI - GPT-4o-mini, cheap & reliable
- Anthropic - Claude, highest quality
- Ollama - Local inference, free

Cost Efficiency Priority:
1. Rule-based (free, <10ms)
2. Local/Ollama (free, <500ms)
3. Groq (free tier, <200ms)
4. Devstral Small ($0.10/$0.30 per M tokens)
5. OpenAI GPT-4o-mini ($0.15/$0.60 per M tokens)
6. Anthropic Claude ($3/$15 per M tokens)
"""

import os
import json
import asyncio
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from enum import Enum
from datetime import datetime

try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False


# =============================================================================
# CONFIGURATION
# =============================================================================

class ProviderTier(Enum):
    """Cost/capability tiers for routing decisions."""
    FREE = "free"           # Rule-based, local
    BUDGET = "budget"       # Groq free tier, Devstral Small
    STANDARD = "standard"   # GPT-4o-mini, Devstral
    PREMIUM = "premium"     # Claude, GPT-4


@dataclass
class ProviderConfig:
    """Configuration for an LLM provider."""
    name: str
    tier: ProviderTier
    api_key_env: str
    base_url: str
    model: str
    
    # Pricing (per 1K tokens)
    input_cost_per_1k: float
    output_cost_per_1k: float
    
    # Capabilities
    max_context: int
    supports_tools: bool
    supports_vision: bool
    supports_streaming: bool
    
    # Performance
    avg_latency_ms: int
    requests_per_minute: int
    
    # Optional settings
    default_temperature: float = 0.7
    default_max_tokens: int = 1024
    
    @property
    def is_free(self) -> bool:
        return self.tier == ProviderTier.FREE
    
    @property
    def cost_per_1k_total(self) -> float:
        """Estimated total cost assuming 1:1 input:output ratio."""
        return self.input_cost_per_1k + self.output_cost_per_1k


# =============================================================================
# PROVIDER DEFINITIONS
# =============================================================================

PROVIDERS: Dict[str, ProviderConfig] = {
    # =========================================================================
    # MISTRAL / DEVSTRAL (Recommended for Echelon)
    # =========================================================================
    "devstral_small": ProviderConfig(
        name="Devstral Small 2 (24B)",
        tier=ProviderTier.BUDGET,
        api_key_env="MISTRAL_API_KEY",
        base_url="https://api.mistral.ai/v1",
        model="devstral-small-2412",
        input_cost_per_1k=0.0001,   # $0.10 per M
        output_cost_per_1k=0.0003,  # $0.30 per M
        max_context=262144,         # 256K context
        supports_tools=True,
        supports_vision=True,       # Multimodal!
        supports_streaming=True,
        avg_latency_ms=300,
        requests_per_minute=100,
        default_temperature=0.2,    # Recommended by Mistral
    ),
    
    "devstral": ProviderConfig(
        name="Devstral 2 (123B)",
        tier=ProviderTier.STANDARD,
        api_key_env="MISTRAL_API_KEY",
        base_url="https://api.mistral.ai/v1",
        model="devstral-2412",
        input_cost_per_1k=0.0004,   # $0.40 per M
        output_cost_per_1k=0.002,   # $2.00 per M
        max_context=262144,         # 256K context
        supports_tools=True,
        supports_vision=True,
        supports_streaming=True,
        avg_latency_ms=500,
        requests_per_minute=60,
        default_temperature=0.2,
    ),
    
    # =========================================================================
    # GROQ (Free Tier - Excellent for Development)
    # =========================================================================
    "groq_llama70b": ProviderConfig(
        name="Groq Llama 3.1 70B",
        tier=ProviderTier.FREE,
        api_key_env="GROQ_API_KEY",
        base_url="https://api.groq.com/openai/v1",
        model="llama-3.1-70b-versatile",
        input_cost_per_1k=0.0,      # Free tier
        output_cost_per_1k=0.0,
        max_context=131072,         # 128K context
        supports_tools=True,
        supports_vision=False,
        supports_streaming=True,
        avg_latency_ms=150,
        requests_per_minute=30,     # Free tier limit
    ),
    
    "groq_llama8b": ProviderConfig(
        name="Groq Llama 3.1 8B",
        tier=ProviderTier.FREE,
        api_key_env="GROQ_API_KEY",
        base_url="https://api.groq.com/openai/v1",
        model="llama-3.1-8b-instant",
        input_cost_per_1k=0.0,
        output_cost_per_1k=0.0,
        max_context=131072,
        supports_tools=True,
        supports_vision=False,
        supports_streaming=True,
        avg_latency_ms=80,
        requests_per_minute=30,
    ),
    
    # =========================================================================
    # OPENAI
    # =========================================================================
    "gpt4o_mini": ProviderConfig(
        name="GPT-4o Mini",
        tier=ProviderTier.BUDGET,
        api_key_env="OPENAI_API_KEY",
        base_url="https://api.openai.com/v1",
        model="gpt-4o-mini",
        input_cost_per_1k=0.00015,  # $0.15 per M
        output_cost_per_1k=0.0006,  # $0.60 per M
        max_context=128000,
        supports_tools=True,
        supports_vision=True,
        supports_streaming=True,
        avg_latency_ms=400,
        requests_per_minute=500,
    ),
    
    "gpt4o": ProviderConfig(
        name="GPT-4o",
        tier=ProviderTier.STANDARD,
        api_key_env="OPENAI_API_KEY",
        base_url="https://api.openai.com/v1",
        model="gpt-4o",
        input_cost_per_1k=0.0025,   # $2.50 per M
        output_cost_per_1k=0.01,    # $10 per M
        max_context=128000,
        supports_tools=True,
        supports_vision=True,
        supports_streaming=True,
        avg_latency_ms=600,
        requests_per_minute=500,
    ),
    
    # =========================================================================
    # ANTHROPIC
    # =========================================================================
    "claude_haiku": ProviderConfig(
        name="Claude 3.5 Haiku",
        tier=ProviderTier.BUDGET,
        api_key_env="ANTHROPIC_API_KEY",
        base_url="https://api.anthropic.com/v1",
        model="claude-3-5-haiku-latest",
        input_cost_per_1k=0.0008,   # $0.80 per M
        output_cost_per_1k=0.004,   # $4.00 per M
        max_context=200000,
        supports_tools=True,
        supports_vision=True,
        supports_streaming=True,
        avg_latency_ms=300,
        requests_per_minute=100,
    ),
    
    "claude_sonnet": ProviderConfig(
        name="Claude 4 Sonnet",
        tier=ProviderTier.STANDARD,
        api_key_env="ANTHROPIC_API_KEY",
        base_url="https://api.anthropic.com/v1",
        model="claude-sonnet-4-20250514",
        input_cost_per_1k=0.003,    # $3 per M
        output_cost_per_1k=0.015,   # $15 per M
        max_context=200000,
        supports_tools=True,
        supports_vision=True,
        supports_streaming=True,
        avg_latency_ms=500,
        requests_per_minute=50,
    ),
    
    "claude_opus": ProviderConfig(
        name="Claude Opus 4.5",
        tier=ProviderTier.PREMIUM,
        api_key_env="ANTHROPIC_API_KEY",
        base_url="https://api.anthropic.com/v1",
        model="claude-opus-4-5-20251101",
        input_cost_per_1k=0.015,    # $15 per M
        output_cost_per_1k=0.075,   # $75 per M
        max_context=200000,
        supports_tools=True,
        supports_vision=True,
        supports_streaming=True,
        avg_latency_ms=1000,
        requests_per_minute=30,
    ),
    
    # =========================================================================
    # LOCAL (Ollama)
    # =========================================================================
    "ollama_devstral": ProviderConfig(
        name="Ollama Devstral Small",
        tier=ProviderTier.FREE,
        api_key_env="",  # No API key needed
        base_url="http://localhost:11434",
        model="devstral:24b",
        input_cost_per_1k=0.0,
        output_cost_per_1k=0.0,
        max_context=131072,
        supports_tools=True,
        supports_vision=True,
        supports_streaming=True,
        avg_latency_ms=1000,  # Depends on hardware
        requests_per_minute=9999,  # Local, no limit
    ),
    
    "ollama_llama8b": ProviderConfig(
        name="Ollama Llama 3.1 8B",
        tier=ProviderTier.FREE,
        api_key_env="",
        base_url="http://localhost:11434",
        model="llama3.1:8b",
        input_cost_per_1k=0.0,
        output_cost_per_1k=0.0,
        max_context=131072,
        supports_tools=True,
        supports_vision=False,
        supports_streaming=True,
        avg_latency_ms=500,
        requests_per_minute=9999,
    ),
}


# =============================================================================
# PROVIDER REGISTRY
# =============================================================================

@dataclass
class ProviderUsage:
    """Track usage for a provider."""
    provider_name: str
    requests_today: int = 0
    tokens_today: int = 0
    cost_today_usd: float = 0.0
    last_request: Optional[datetime] = None
    errors_today: int = 0


class ProviderRegistry:
    """
    Manages LLM providers with automatic fallback and cost tracking.
    
    Example:
        registry = ProviderRegistry()
        provider = registry.get_cheapest_available(
            min_context=50000,
            require_tools=True
        )
        response = await registry.call(provider, messages)
    """
    
    def __init__(self, preferred_providers: Optional[List[str]] = None):
        self.providers = PROVIDERS
        self.usage: Dict[str, ProviderUsage] = {}
        
        # Default preference order (cost-optimised)
        self.preferred_order = preferred_providers or [
            "groq_llama8b",      # Free, fastest
            "groq_llama70b",     # Free, better quality
            "devstral_small",    # Very cheap, excellent for code
            "gpt4o_mini",        # Cheap, reliable
            "devstral",          # SOTA open model
            "claude_haiku",      # Good quality, moderate cost
            "gpt4o",             # High quality
            "claude_sonnet",     # Very high quality
            "claude_opus",       # Best quality
        ]
        
        # Initialise usage tracking
        for name in self.providers:
            self.usage[name] = ProviderUsage(provider_name=name)
    
    def get_provider(self, name: str) -> Optional[ProviderConfig]:
        """Get a specific provider by name."""
        return self.providers.get(name)
    
    def get_cheapest_available(
        self,
        min_context: int = 0,
        require_tools: bool = False,
        require_vision: bool = False,
        max_tier: ProviderTier = ProviderTier.PREMIUM,
    ) -> Optional[ProviderConfig]:
        """
        Get the cheapest provider that meets requirements.
        Checks API key availability.
        """
        tier_order = [ProviderTier.FREE, ProviderTier.BUDGET, ProviderTier.STANDARD, ProviderTier.PREMIUM]
        max_tier_index = tier_order.index(max_tier)
        
        for provider_name in self.preferred_order:
            provider = self.providers.get(provider_name)
            if not provider:
                continue
            
            # Check tier
            if tier_order.index(provider.tier) > max_tier_index:
                continue
            
            # Check capabilities
            if provider.max_context < min_context:
                continue
            if require_tools and not provider.supports_tools:
                continue
            if require_vision and not provider.supports_vision:
                continue
            
            # Check API key availability
            if provider.api_key_env:
                api_key = os.getenv(provider.api_key_env, "")
                if not api_key:
                    continue
            
            return provider
        
        return None
    
    def get_by_tier(self, tier: ProviderTier) -> List[ProviderConfig]:
        """Get all providers in a specific tier."""
        return [p for p in self.providers.values() if p.tier == tier]
    
    async def call(
        self,
        provider: ProviderConfig,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        tools: Optional[List[Dict]] = None,
    ) -> Dict[str, Any]:
        """
        Make a call to an LLM provider.
        
        Returns:
            {
                "content": str,
                "usage": {"input_tokens": int, "output_tokens": int},
                "cost_usd": float,
                "latency_ms": float,
                "provider": str,
            }
        """
        import time
        start = time.time()
        
        max_tokens = max_tokens or provider.default_max_tokens
        temperature = temperature or provider.default_temperature
        
        try:
            if provider.base_url.startswith("http://localhost:11434"):
                # Ollama
                result = await self._call_ollama(provider, messages, max_tokens, temperature)
            elif "mistral.ai" in provider.base_url:
                # Mistral/Devstral
                result = await self._call_mistral(provider, messages, max_tokens, temperature, tools)
            elif "anthropic.com" in provider.base_url:
                # Anthropic
                result = await self._call_anthropic(provider, messages, max_tokens, temperature, tools)
            else:
                # OpenAI-compatible (OpenAI, Groq)
                result = await self._call_openai_compatible(provider, messages, max_tokens, temperature, tools)
            
            latency_ms = (time.time() - start) * 1000
            
            # Calculate cost
            input_tokens = result.get("usage", {}).get("input_tokens", 0)
            output_tokens = result.get("usage", {}).get("output_tokens", 0)
            cost_usd = (
                (input_tokens / 1000) * provider.input_cost_per_1k +
                (output_tokens / 1000) * provider.output_cost_per_1k
            )
            
            # Update usage tracking
            usage = self.usage[provider.model] if provider.model in self.usage else self.usage.get(provider.name, ProviderUsage(provider_name=provider.name))
            usage.requests_today += 1
            usage.tokens_today += input_tokens + output_tokens
            usage.cost_today_usd += cost_usd
            usage.last_request = datetime.now()
            
            return {
                "content": result.get("content", ""),
                "usage": result.get("usage", {}),
                "cost_usd": cost_usd,
                "latency_ms": latency_ms,
                "provider": provider.name,
            }
            
        except Exception as e:
            # Track errors
            usage = self.usage.get(provider.name, ProviderUsage(provider_name=provider.name))
            usage.errors_today += 1
            raise e
    
    async def _call_openai_compatible(
        self,
        provider: ProviderConfig,
        messages: List[Dict],
        max_tokens: int,
        temperature: float,
        tools: Optional[List[Dict]] = None,
    ) -> Dict:
        """Call OpenAI-compatible API (OpenAI, Groq)."""
        if not HAS_HTTPX:
            raise ImportError("httpx required for API calls")
        
        api_key = os.getenv(provider.api_key_env, "")
        
        payload = {
            "model": provider.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        
        if tools and provider.supports_tools:
            payload["tools"] = tools
        
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{provider.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            
            if response.status_code != 200:
                raise Exception(f"API error: {response.status_code} - {response.text}")
            
            data = response.json()
            
            return {
                "content": data["choices"][0]["message"]["content"],
                "usage": {
                    "input_tokens": data.get("usage", {}).get("prompt_tokens", 0),
                    "output_tokens": data.get("usage", {}).get("completion_tokens", 0),
                },
            }
    
    async def _call_mistral(
        self,
        provider: ProviderConfig,
        messages: List[Dict],
        max_tokens: int,
        temperature: float,
        tools: Optional[List[Dict]] = None,
    ) -> Dict:
        """Call Mistral API (Devstral)."""
        if not HAS_HTTPX:
            raise ImportError("httpx required for API calls")
        
        api_key = os.getenv(provider.api_key_env, "")
        
        payload = {
            "model": provider.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        
        if tools and provider.supports_tools:
            payload["tools"] = tools
        
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{provider.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            
            if response.status_code != 200:
                raise Exception(f"Mistral API error: {response.status_code} - {response.text}")
            
            data = response.json()
            
            return {
                "content": data["choices"][0]["message"]["content"],
                "usage": {
                    "input_tokens": data.get("usage", {}).get("prompt_tokens", 0),
                    "output_tokens": data.get("usage", {}).get("completion_tokens", 0),
                },
            }
    
    async def _call_anthropic(
        self,
        provider: ProviderConfig,
        messages: List[Dict],
        max_tokens: int,
        temperature: float,
        tools: Optional[List[Dict]] = None,
    ) -> Dict:
        """Call Anthropic API."""
        if not HAS_HTTPX:
            raise ImportError("httpx required for API calls")
        
        api_key = os.getenv(provider.api_key_env, "")
        
        # Convert messages format for Anthropic
        system_msg = ""
        anthropic_messages = []
        
        for msg in messages:
            if msg["role"] == "system":
                system_msg = msg["content"]
            else:
                anthropic_messages.append(msg)
        
        payload = {
            "model": provider.model,
            "max_tokens": max_tokens,
            "messages": anthropic_messages,
        }
        
        if system_msg:
            payload["system"] = system_msg
        
        if tools and provider.supports_tools:
            payload["tools"] = tools
        
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{provider.base_url}/messages",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            
            if response.status_code != 200:
                raise Exception(f"Anthropic API error: {response.status_code} - {response.text}")
            
            data = response.json()
            
            content = ""
            for block in data.get("content", []):
                if block.get("type") == "text":
                    content += block.get("text", "")
            
            return {
                "content": content,
                "usage": {
                    "input_tokens": data.get("usage", {}).get("input_tokens", 0),
                    "output_tokens": data.get("usage", {}).get("output_tokens", 0),
                },
            }
    
    async def _call_ollama(
        self,
        provider: ProviderConfig,
        messages: List[Dict],
        max_tokens: int,
        temperature: float,
    ) -> Dict:
        """Call local Ollama instance."""
        if not HAS_HTTPX:
            raise ImportError("httpx required for API calls")
        
        # Convert to Ollama format
        prompt = ""
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            if role == "system":
                prompt += f"System: {content}\n\n"
            elif role == "user":
                prompt += f"User: {content}\n\n"
            elif role == "assistant":
                prompt += f"Assistant: {content}\n\n"
        prompt += "Assistant: "
        
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(
                f"{provider.base_url}/api/generate",
                json={
                    "model": provider.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": temperature,
                        "num_predict": max_tokens,
                    },
                },
            )
            
            if response.status_code != 200:
                raise Exception(f"Ollama error: {response.status_code} - {response.text}")
            
            data = response.json()
            
            return {
                "content": data.get("response", ""),
                "usage": {
                    "input_tokens": data.get("prompt_eval_count", 0),
                    "output_tokens": data.get("eval_count", 0),
                },
            }
    
    def get_usage_summary(self) -> Dict[str, Any]:
        """Get summary of provider usage."""
        total_cost = sum(u.cost_today_usd for u in self.usage.values())
        total_requests = sum(u.requests_today for u in self.usage.values())
        total_tokens = sum(u.tokens_today for u in self.usage.values())
        
        return {
            "total_cost_usd": total_cost,
            "total_requests": total_requests,
            "total_tokens": total_tokens,
            "by_provider": {
                name: {
                    "requests": u.requests_today,
                    "tokens": u.tokens_today,
                    "cost_usd": u.cost_today_usd,
                    "errors": u.errors_today,
                }
                for name, u in self.usage.items()
                if u.requests_today > 0
            },
        }
    
    def reset_daily_usage(self):
        """Reset daily usage counters (call at midnight)."""
        for usage in self.usage.values():
            usage.requests_today = 0
            usage.tokens_today = 0
            usage.cost_today_usd = 0.0
            usage.errors_today = 0


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def get_recommended_provider_for_task(task_type: str) -> str:
    """
    Get the recommended provider for a specific task type.
    
    Task types:
    - "trade": Quick trading decisions → groq_llama8b
    - "analysis": Market analysis → devstral_small
    - "diplomacy": Complex negotiations → claude_haiku
    - "narrative": Story generation → devstral
    - "code": Code generation/analysis → devstral_small
    - "critical": High-stakes decisions → claude_sonnet
    """
    recommendations = {
        "trade": "groq_llama8b",
        "analysis": "devstral_small",
        "diplomacy": "claude_haiku",
        "narrative": "devstral",
        "code": "devstral_small",
        "critical": "claude_sonnet",
    }
    return recommendations.get(task_type, "devstral_small")


# =============================================================================
# DEMO
# =============================================================================

async def demo():
    """Demonstrate provider registry."""
    print("=" * 60)
    print("🔌 PROVIDER REGISTRY DEMO")
    print("=" * 60)
    
    registry = ProviderRegistry()
    
    # Find cheapest available
    provider = registry.get_cheapest_available(
        min_context=50000,
        require_tools=True,
    )
    
    if provider:
        print(f"\n✅ Cheapest available provider: {provider.name}")
        print(f"   Model: {provider.model}")
        print(f"   Cost: ${provider.cost_per_1k_total:.4f}/1K tokens")
        print(f"   Context: {provider.max_context:,} tokens")
    else:
        print("\n❌ No provider available (check API keys)")
    
    # Show all providers by tier
    print("\n📊 Providers by tier:")
    for tier in ProviderTier:
        providers = registry.get_by_tier(tier)
        print(f"\n  {tier.value.upper()}:")
        for p in providers:
            print(f"    • {p.name}: ${p.cost_per_1k_total:.4f}/1K tokens")


if __name__ == "__main__":
    asyncio.run(demo())
