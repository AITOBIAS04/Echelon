"""
Agent Brain for Project Seed
=============================
LLM-powered personality layer for agents.

Cost Optimization Strategy:
- ROUTINE tasks (tweets, reactions): claude-3-5-haiku (cheap, fast)
- CRITICAL tasks (crises, manifestos): claude-sonnet-4-5 (smart, expensive)

Features:
- Automatic model selection based on event importance
- Prompt caching for 90% cost reduction on repeated personas
- Fire-and-forget async for non-blocking reactions
- Rate limiting to prevent API spam

Usage:
    from agents.brain import AgentBrain
    
    brain = AgentBrain()
    
    reaction = await brain.generate_reaction(
        agent,
        event="BOUGHT AAPL",
        context={"price": 150, "quantity": 10}
    )
"""

import os
import json
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime

from anthropic import AsyncAnthropic
from dotenv import load_dotenv

# Import schemas
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.agents.schemas import (
    BaseAgent, 
    FinancialAgent, 
    AthleticAgent, 
    PoliticalAgent,
    AgentDomain,
)

load_dotenv()




# =============================================================================
# CONFIGURATION
# =============================================================================

class BrainConfig:
    """Configuration for the Agent Brain."""
    
    # Model selection
    # Note: Using Haiku for both to keep costs low during development
    # Upgrade CRITICAL_MODEL to claude-3-5-sonnet or claude-3-opus when in production
    ROUTINE_MODEL = "claude-3-5-haiku-20241022"  # Fast & cheap
    CRITICAL_MODEL = "claude-3-5-haiku-20241022"  # Using Haiku for now (upgrade in prod)
    
    # Token limits (keep responses short to save money)
    MAX_TOKENS_ROUTINE = 100
    MAX_TOKENS_CRITICAL = 300
    
    # Rate limiting
    MIN_INTERVAL_SECONDS = 2  # Minimum time between API calls
    
    # Critical event triggers
    CRITICAL_KEYWORDS = [
        "CRASH", "WAR", "SCANDAL", "BANKRUPT", "INJURY",
        "CHAMPION", "ELIMINATED", "EMERGENCY", "CRISIS"
    ]
    
    # Domain-specific critical thresholds
    FINANCIAL_CRITICAL_PNL = -20  # Trigger critical mode if P&L < -20%
    ATHLETIC_CRITICAL_INJURY = True  # Trigger on any injury
    POLITICAL_CRITICAL_SCANDAL = True  # Trigger on scandal




# =============================================================================
# SPEECH STYLES (Since schema doesn't include it)
# =============================================================================

ARCHETYPE_SPEECH_STYLES = {
    # Financial
    "whale": "Calm, measured, institutional. Speaks like a pension fund manager.",
    "shark": "Aggressive, Wall Street slang. 'Diamond hands', 'to the moon'.",
    "degen": "Chaotic, meme-heavy, FOMO-driven. Uses emojis liberally.",
    "value": "Patient, Warren Buffett quotes, long-term focus.",
    "momentum": "Excited about trends, technical analysis jargon.",
    "noise": "Random, unpredictable, sometimes nonsensical.",
    
    # Athletic
    "star": "Confident, media-trained, speaks in third person sometimes.",
    "glass": "Anxious about injuries, superstitious.",
    "workhorse": "Humble, team-first, clichés about 'giving 110%'.",
    "prospect": "Eager, wants to prove themselves, grateful.",
    "veteran": "Wise, mentoring tone, 'back in my day' stories.",
    
    # Political
    "populist": "Fiery, us-vs-them rhetoric, appeals to emotion.",
    "technocrat": "Data-driven, policy-focused, dry humor.",
    "instigator": "Provocative, inflammatory, thrives on controversy.",
    "moderate": "Measured, both-sides, coalition-building language.",
    "ideologue": "Passionate, uncompromising, true believer.",
}


def get_speech_style(agent: BaseAgent) -> str:
    """Get speech style for an agent based on archetype."""
    archetype = getattr(agent, 'archetype', None)
    if archetype:
        archetype_key = archetype.value if hasattr(archetype, 'value') else str(archetype)
        return ARCHETYPE_SPEECH_STYLES.get(archetype_key, "Standard professional tone.")
    return "Standard professional tone."




# =============================================================================
# AGENT BRAIN
# =============================================================================

class AgentBrain:
    """
    LLM-powered brain for agent personalities.
    
    Handles all Claude API interactions with cost optimization.
    """
    
    def __init__(self, config: BrainConfig = None):
        self.config = config or BrainConfig()
        
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not set in environment")
        
        self.client = AsyncAnthropic(api_key=api_key)
        
        # Rate limiting
        self.last_call_time = 0
        
        # Cache headers for prompt caching (saves ~90% on repeated system prompts)
        self.cache_headers = {"anthropic-beta": "prompt-caching-2024-07-31"}
    
    def _get_system_prompt(self, agent: BaseAgent) -> List[Dict]:
        """
        Construct the system prompt based on agent genome.
        Uses ephemeral caching to reduce costs.
        """
        archetype = getattr(agent, 'archetype', 'Unknown')
        archetype_name = archetype.value if hasattr(archetype, 'value') else str(archetype)
        speech_style = get_speech_style(agent)
        
        # Build persona from Pydantic schema
        persona = f"""You are {agent.name}.
Role: {agent.domain.value.title()} Agent
Archetype: {archetype_name.title()}

Personality Traits (scale 0.0 - 1.0):
- Aggression: {agent.aggression:.2f}
- Deception: {agent.deception:.2f}
- Loyalty: {agent.loyalty:.2f}
- Resilience: {agent.resilience:.2f}

Speaking Style: {speech_style}

Recent Memory: {'; '.join(agent.memory[-3:]) if agent.memory else 'None'}

Directives:
1. Speak strictly in character
2. Keep responses under 280 characters (Twitter-length)
3. Never break the fourth wall
4. React authentically based on your personality traits
5. If aggression is high, be more combative
6. If deception is high, be evasive or misleading"""

        return [
            {
                "type": "text",
                "text": persona,
                "cache_control": {"type": "ephemeral"}  # CACHE THIS BLOCK
            }
        ]
    
    def _is_critical_event(self, event: str, context: Dict[str, Any], 
                           agent: BaseAgent) -> bool:
        """Determine if this event warrants the expensive model."""
        
        # Check keywords
        event_upper = event.upper()
        for keyword in self.config.CRITICAL_KEYWORDS:
            if keyword in event_upper:
                return True
        
        # Domain-specific checks
        if isinstance(agent, FinancialAgent):
            pnl = context.get("pnl_pct", 0)
            if pnl < self.config.FINANCIAL_CRITICAL_PNL:
                return True
        
        elif isinstance(agent, AthleticAgent):
            if context.get("injury") and self.config.ATHLETIC_CRITICAL_INJURY:
                return True
        
        elif isinstance(agent, PoliticalAgent):
            if context.get("scandal") and self.config.POLITICAL_CRITICAL_SCANDAL:
                return True
        
        return False
    
    async def _rate_limit(self) -> None:
        """Enforce rate limiting between API calls."""
        now = asyncio.get_event_loop().time()
        elapsed = now - self.last_call_time
        
        if elapsed < self.config.MIN_INTERVAL_SECONDS:
            await asyncio.sleep(self.config.MIN_INTERVAL_SECONDS - elapsed)
        
        self.last_call_time = asyncio.get_event_loop().time()
    
    async def generate_reaction(self, agent: BaseAgent, event: str,
                                 context: Dict[str, Any] = None) -> str:
        """
        Generate a reaction to an event.
        
        Automatically selects cheap vs. expensive model based on event importance.
        
        Args:
            agent: The agent reacting
            event: What happened (e.g., "BOUGHT AAPL", "SCORED GOAL")
            context: Additional context (prices, scores, etc.)
            
        Returns:
            The agent's reaction (tweet-length)
        """
        context = context or {}
        
        # Rate limiting
        await self._rate_limit()
        
        # Determine model
        is_critical = self._is_critical_event(event, context, agent)
        model = self.config.CRITICAL_MODEL if is_critical else self.config.ROUTINE_MODEL
        max_tokens = self.config.MAX_TOKENS_CRITICAL if is_critical else self.config.MAX_TOKENS_ROUTINE
        
        # Build user prompt
        user_content = f"""EVENT: {event}
CONTEXT: {json.dumps(context, default=str)}

React to this event as yourself. Be authentic to your personality.
Keep your response under 280 characters."""

        try:
            response = await self.client.messages.create(
                model=model,
                max_tokens=max_tokens,
                system=self._get_system_prompt(agent),
                messages=[
                    {"role": "user", "content": user_content}
                ],
                extra_headers=self.cache_headers
            )
            
            thought = response.content[0].text
            
            # Log which model was used
            model_tag = "🧠 CRITICAL" if is_critical else "💭 routine"
            print(f"   {model_tag} [{agent.name}]: {thought[:50]}...")
            
            # Add to agent memory
            agent.add_memory(f"Said: {thought[:50]}...")
            
            return thought
            
        except Exception as e:
            error_msg = str(e)
            if "529" in error_msg or "overloaded" in error_msg.lower():
                print(f"   ⏳ API overloaded, skipping reaction for {agent.name}")
                return "..."
            
            print(f"   ❌ Brain error for {agent.name}: {e}")
            return "..."
    
    async def generate_commentary(self, event_type: str, 
                                   details: Dict[str, Any]) -> str:
        """
        Generate shoutcaster-style commentary for an event.
        
        Used for the AI Broadcaster feature.
        """
        await self._rate_limit()
        
        system_prompt = [{
            "type": "text",
            "text": """You are an enthusiastic sports/market commentator.
Your style is energetic, dramatic, and engaging.
Keep commentary under 200 characters.
Use appropriate emojis sparingly.
Build excitement and tension.""",
            "cache_control": {"type": "ephemeral"}
        }]
        
        user_content = f"""EVENT TYPE: {event_type}
DETAILS: {json.dumps(details, default=str)}

Provide exciting live commentary for this moment."""

        try:
            response = await self.client.messages.create(
                model=self.config.ROUTINE_MODEL,  # Commentary is always routine
                max_tokens=100,
                system=system_prompt,
                messages=[{"role": "user", "content": user_content}],
                extra_headers=self.cache_headers
            )
            
            return response.content[0].text
            
        except Exception as e:
            print(f"   ❌ Commentary error: {e}")
            return f"🎙️ {event_type}!"
    
    async def generate_analysis(self, agent: BaseAgent,
                                 situation: str,
                                 options: List[str]) -> Dict[str, Any]:
        """
        Generate strategic analysis for decision-making.
        
        Returns structured JSON with reasoning and choice.
        """
        await self._rate_limit()
        
        user_content = f"""SITUATION: {situation}

OPTIONS:
{chr(10).join(f'{i+1}. {opt}' for i, opt in enumerate(options))}

Analyze this situation and choose the best option.
Respond with JSON only:
{{"reasoning": "brief explanation", "choice": 1, "confidence": 0.8}}"""

        try:
            response = await self.client.messages.create(
                model=self.config.CRITICAL_MODEL,  # Analysis is always critical
                max_tokens=200,
                system=self._get_system_prompt(agent),
                messages=[{"role": "user", "content": user_content}],
                extra_headers=self.cache_headers
            )
            
            text = response.content[0].text
            
            # Parse JSON from response
            try:
                # Handle potential markdown code blocks
                if "```" in text:
                    text = text.split("```")[1]
                    if text.startswith("json"):
                        text = text[4:]
                
                return json.loads(text.strip())
            except json.JSONDecodeError:
                return {
                    "reasoning": text[:100],
                    "choice": 1,
                    "confidence": 0.5
                }
                
        except Exception as e:
            print(f"   ❌ Analysis error: {e}")
            return {
                "reasoning": "Error occurred",
                "choice": 1,
                "confidence": 0.0
            }




# =============================================================================
# TEST
# =============================================================================

if __name__ == "__main__":
    from backend.agents.schemas import create_random_financial_agent, FinancialArchetype
    
    async def test_brain():
        print("🧪 Testing Agent Brain\n")
        
        try:
            brain = AgentBrain()
        except ValueError as e:
            print(f"❌ {e}")
            return
        
        # Create a test agent
        shark = create_random_financial_agent(FinancialArchetype.SHARK)
        print(f"🦈 Agent: {shark.name}")
        print(f"   Archetype: {shark.archetype.value}")
        print(f"   Aggression: {shark.aggression:.2f}")
        print(f"   Speech Style: {get_speech_style(shark)[:50]}...")
        
        # Test 1: Routine event
        print("\n--- Test 1: Routine Trade ---")
        reaction = await brain.generate_reaction(
            shark,
            "BOUGHT SAPL",
            {"price": 150, "quantity": 10}
        )
        print(f"💬 {reaction}")
        
        # Test 2: Critical event
        print("\n--- Test 2: Market Crash ---")
        reaction2 = await brain.generate_reaction(
            shark,
            "MARKET CRASH DETECTED",
            {"pnl_pct": -25, "panic_index": 0.9}
        )
        print(f"💬 {reaction2}")
        
        print("\n✅ Brain test complete!")
    
    asyncio.run(test_brain())
