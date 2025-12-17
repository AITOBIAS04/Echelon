"""
brain_router.py

Three-Tier Intelligence Router for Echelon Agents
Routes tasks to optimal cost/quality layer based on complexity

Layer 1:   Heuristics (<10ms, $0)     - Trading decisions
Layer 1.5: Mistral Small (~300ms, $$$) - Personality/narrative
Layer 2:   Claude/GPT-4 (~1.5s, $$$$) - Complex reasoning
"""

from typing import Dict, Any, Literal
from dataclasses import dataclass
import anthropic
from mistralai import Mistral
import os


@dataclass
class TaskContext:
    """Context bundle for routing decisions"""
    agent_id: str
    agent_archetype: Literal["SHARK", "SPY", "DIPLOMAT", "SABOTEUR", "WHALE", "MOMENTUM"]
    raw_data: Dict[str, Any]
    persona_prompt: str
    task_metadata: Dict[str, Any] = None


class BrainRouter:
    """
    Routes agent tasks to the most cost-effective intelligence layer.
    
    Architecture:
    - Layer 1:   Pure heuristics (no LLM)
    - Layer 1.5: Mistral Small Creative (personality, narrative)
    - Layer 2:   Claude Sonnet 4 (complex reasoning, novel situations)
    """
    
    def __init__(self):
        # Initialize clients
        self.mistral_client = Mistral(api_key=os.getenv("MISTRAL_API_KEY"))
        self.claude_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        
        # Heuristics engine (placeholder - replace with actual implementation)
        self.heuristics_engine = HeuristicsEngine()
        
        # Temperature settings
        self.CREATIVE_TEMP = 0.9  # High temp for personality
        self.REASONING_TEMP = 0.3  # Low temp for logic
        
        # Model strings
        # Try mistral-small-creative first (Labs model, may require special access)
        # Fallback to mistral-small-latest if creative model unavailable
        self.MISTRAL_MODEL = "mistral-small-creative"  # Labs v25.12 - creative writing optimized
        self.MISTRAL_MODEL_FALLBACK = "mistral-small-latest"  # Fallback if creative unavailable
        self.CLAUDE_MODEL = "claude-sonnet-4-20250514"
        
    
    async def route_task(self, task_type: str, context: TaskContext) -> Dict[str, Any]:
        """
        Main routing logic. Determines which layer handles the task.
        
        Args:
            task_type: Type of task (trade_decision, intel_format, social_post, etc.)
            context: TaskContext with all necessary data
            
        Returns:
            Dict containing response and metadata (layer_used, cost, latency)
        """
        
        # LAYER 1: HEURISTICS (Trading Decisions)
        if task_type == "trade_decision":
            return await self._layer1_heuristics(context)
        
        # LAYER 1.5: PERSONALITY (Creative Writing)
        elif task_type in [
            "intel_format",      # Spy reports (START HERE - lower risk)
            "mission_narrative", # Mission Factory flavor text
            "social_post",       # Shark broadcasts (test after intel)
            "agent_reasoning",   # "Why did I make this trade?"
            "treaty_draft",      # Diplomat treaty templates
        ]:
            return await self._layer15_personality(task_type, context)
        
        # LAYER 2: REASONING (Complex Logic)
        elif task_type in [
            "diplomacy_negotiation",  # Multi-agent treaty negotiation
            "strategy_pivot",         # Adapting to black swan events
            "novel_situation",        # Unprecedented market conditions
            "coalition_formation",    # Diplomat alliance logic
        ]:
            return await self._layer2_reasoning(task_type, context)
        
        else:
            raise ValueError(f"Unknown task_type: {task_type}")
    
    
    async def _layer1_heuristics(self, context: TaskContext) -> Dict[str, Any]:
        """
        Layer 1: Pure heuristics for trading decisions.
        No LLM calls. <10ms latency. $0 cost.
        """
        market_data = context.raw_data
        
        # Example heuristic: Tulip Strategy
        if market_data.get("liquidity") < 5000 and market_data.get("expiry_hours") < 24:
            decision = self.heuristics_engine.tulip_strategy(market_data)
        
        # Example heuristic: Blood in Water
        elif market_data.get("spread") > 0.05:
            decision = self.heuristics_engine.blood_in_water(market_data)
        
        else:
            decision = {"action": "HOLD", "reason": "No heuristic triggered"}
        
        return {
            "response": decision,
            "layer_used": "Layer 1 (Heuristics)",
            "latency_ms": decision.get("latency", 5),
            "cost_usd": 0.0
        }
    
    
    async def _layer15_personality(self, task_type: str, context: TaskContext) -> Dict[str, Any]:
        """
        Layer 1.5: Mistral Small Creative for personality and narrative.
        ~300ms latency. ~$0.000095 per call.
        
        USE CASES (in order of risk):
        1. intel_format      - Spy reports (internal, low risk)
        2. mission_narrative - Mission Factory text (internal)
        3. social_post       - Shark broadcasts (public, test after intel)
        4. agent_reasoning   - Trade explanations
        """
        
        # Build prompt based on task type
        system_prompt = self._build_personality_prompt(task_type, context)
        user_prompt = self._format_raw_data(task_type, context.raw_data)
        
        # Call Mistral Small Creative (with fallback)
        try:
            response = await self.mistral_client.chat.complete_async(
                model=self.MISTRAL_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=self.CREATIVE_TEMP,
                max_tokens=300  # Keep outputs concise
            )
        except Exception as e:
            # Fallback to mistral-small-latest if creative model unavailable
            if "invalid_model" in str(e).lower() or "mistral-small-creative" in str(e).lower():
                response = await self.mistral_client.chat.complete_async(
                    model=self.MISTRAL_MODEL_FALLBACK,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=self.CREATIVE_TEMP,
                    max_tokens=300
                )
            else:
                raise
        
        content = response.choices[0].message.content
        
        # Calculate cost (approximate)
        input_tokens = response.usage.prompt_tokens
        output_tokens = response.usage.completion_tokens
        cost = (input_tokens * 0.10 / 1_000_000) + (output_tokens * 0.30 / 1_000_000)
        
        return {
            "response": content,
            "layer_used": "Layer 1.5 (Mistral Small Creative)",
            "latency_ms": 300,  # Approximate
            "cost_usd": cost,
            "tokens_used": {"input": input_tokens, "output": output_tokens}
        }
    
    
    async def _layer2_reasoning(self, task_type: str, context: TaskContext) -> Dict[str, Any]:
        """
        Layer 2: Claude Sonnet 4 for complex reasoning.
        ~1.5s latency. ~$0.01-0.10 per call.
        
        USE CASES:
        - Novel situations (black swans)
        - Diplomacy negotiation (multi-agent treaties)
        - Strategy pivots (paradigm shifts)
        """
        
        system_prompt = self._build_reasoning_prompt(task_type, context)
        user_prompt = self._format_raw_data(task_type, context.raw_data)
        
        # Call Claude Sonnet 4
        response = await self.claude_client.messages.create(
            model=self.CLAUDE_MODEL,
            max_tokens=1024,
            temperature=self.REASONING_TEMP,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_prompt}
            ]
        )
        
        content = response.content[0].text
        
        # Calculate cost
        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens
        cost = (input_tokens * 3.0 / 1_000_000) + (output_tokens * 15.0 / 1_000_000)
        
        return {
            "response": content,
            "layer_used": "Layer 2 (Claude Sonnet 4)",
            "latency_ms": 1500,  # Approximate
            "cost_usd": cost,
            "tokens_used": {"input": input_tokens, "output": output_tokens}
        }
    
    
    def _build_personality_prompt(self, task_type: str, context: TaskContext) -> str:
        """Build system prompt for Layer 1.5 personality tasks"""
        
        archetype = context.agent_archetype
        
        # Archetype-specific personality prompts
        personalities = {
            "SHARK": "You are a ruthless, aggressive trader. Cocky, urgent, front-run-or-follow energy. Use shark metaphors.",
            "SPY": "You are a shadowy intelligence broker. Professional, secretive, information is currency. Write like classified intel.",
            "DIPLOMAT": "You are a smooth negotiator. Diplomatic, measured, coalition-builder. Treaties are your weapon.",
            "SABOTEUR": "You are a chaos agent. Sly, misdirecting, planting doubt. Misinformation is your art.",
            "WHALE": "You are an institutional heavyweight. Calm, market-moving, deliberate. Your size is your advantage.",
            "MOMENTUM": "You are a trend-following algorithm. Amplify moves, ride momentum, cascade volatility.",
        }
        
        base_personality = personalities.get(archetype, "You are an AI agent.")
        
        # Task-specific additions
        if task_type == "intel_format":
            return f"{base_personality}\n\nFormat this raw OSINT data into a professional intelligence report. Be concise, factual, and actionable."
        
        elif task_type == "mission_narrative":
            return f"{base_personality}\n\nConvert this anomaly data into a compelling mission brief. Make it engaging and urgent."
        
        elif task_type == "social_post":
            return f"{base_personality}\n\nWrite a 60-second early broadcast about this trade. Stay in character. Max 2 sentences."
        
        elif task_type == "agent_reasoning":
            return f"{base_personality}\n\nExplain why you made this trade decision. Stay in character but be clear."
        
        else:
            return base_personality
    
    
    def _build_reasoning_prompt(self, task_type: str, context: TaskContext) -> str:
        """Build system prompt for Layer 2 reasoning tasks"""
        
        if task_type == "diplomacy_negotiation":
            return "You are a strategic negotiator. Analyse all parties' incentives and propose mutually beneficial treaty terms."
        
        elif task_type == "strategy_pivot":
            return "You are a strategic advisor. Analyse this unprecedented situation and recommend an adaptive strategy."
        
        elif task_type == "novel_situation":
            return "You are facing an unprecedented market event. Apply first principles reasoning to navigate this situation."
        
        else:
            return "You are a strategic reasoning engine."
    
    
    def _format_raw_data(self, task_type: str, raw_data: Dict[str, Any]) -> str:
        """Format raw data into appropriate prompt for each task type"""
        
        if task_type == "intel_format":
            return f"""
Raw OSINT Data:
Source: {raw_data.get('source')}
Event: {raw_data.get('event')}
Confidence: {raw_data.get('confidence')}
Timeframe: {raw_data.get('timeframe')}

Additional Context:
{raw_data.get('context', 'None')}
"""
        
        elif task_type == "mission_narrative":
            return f"""
Anomaly Detected:
{raw_data.get('anomaly_description')}

Trigger Threshold: {raw_data.get('threshold')}
Current Reading: {raw_data.get('current_value')}
"""
        
        elif task_type == "social_post":
            return f"""
Trade Details:
Direction: {raw_data.get('direction')}
Size: {raw_data.get('size')}
Market: {raw_data.get('market')}
Confidence: {raw_data.get('confidence')}
"""
        
        else:
            # Generic formatting
            return str(raw_data)


class HeuristicsEngine:
    """
    Placeholder for Layer 1 heuristics.
    Replace with actual Tulip, Blood in Water, etc. strategies.
    """
    
    def tulip_strategy(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Tulip arbitrage strategy"""
        return {
            "action": "LONG",
            "size": 1000,
            "reason": "Tulip arb opportunity detected",
            "latency": 5
        }
    
    def blood_in_water(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Blood in Water liquidity provision strategy"""
        return {
            "action": "PROVIDE_LIQUIDITY",
            "size": 5000,
            "reason": "Wide spread detected",
            "latency": 8
        }


# Example usage
async def example_usage():
    """Example of routing different task types"""
    
    router = BrainRouter()
    
    # Example 1: Layer 1 (Heuristics) - Trading decision
    trade_context = TaskContext(
        agent_id="MEGALODON_001",
        agent_archetype="SHARK",
        raw_data={
            "liquidity": 3000,
            "expiry_hours": 12,
            "spread": 0.03
        },
        persona_prompt=""
    )
    
    trade_result = await router.route_task("trade_decision", trade_context)
    print(f"Trade Decision: {trade_result}")
    
    
    # Example 2: Layer 1.5 (Personality) - Intel formatting
    intel_context = TaskContext(
        agent_id="CARDINAL_001",
        agent_archetype="SPY",
        raw_data={
            "source": "Spire AIS",
            "event": "3 tankers dark near Hormuz",
            "confidence": 0.78,
            "timeframe": "24h",
            "context": "Historical pattern: 65% correlation with sanctions evasion"
        },
        persona_prompt=""
    )
    
    intel_result = await router.route_task("intel_format", intel_context)
    print(f"Intel Report: {intel_result}")
    
    
    # Example 3: Layer 2 (Reasoning) - Novel situation
    reasoning_context = TaskContext(
        agent_id="AMBASSADOR_001",
        agent_archetype="DIPLOMAT",
        raw_data={
            "situation": "Fed announced unexpected 75bps emergency cut",
            "market_reaction": "VIX spiked to 45, treasury yields inverted",
            "parties": ["MEGALODON", "LEVIATHAN", "PHOENIX"]
        },
        persona_prompt=""
    )
    
    reasoning_result = await router.route_task("strategy_pivot", reasoning_context)
    print(f"Strategic Pivot: {reasoning_result}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(example_usage())
