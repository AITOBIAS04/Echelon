"""
Context Compiler
================

ADK-style context compilation for agent decisions.

From Google's Agent Development Kit:
"The naive pattern—append everything into one giant prompt—collapses 
under a three-way pressure: cost spirals, signal degradation, and 
debugging opacity."

This module implements context as a "compiled view" over a richer 
stateful system, building just enough context for each decision type.

Key Principles:
1. Tiered Storage - Agent state in DB, not prompts
2. Compiled Views - Build minimal context per decision
3. Scoped Handoffs - Isolated context for agent interactions
4. Event Logs - Structured memory with references
"""

import json
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from pathlib import Path


# =============================================================================
# COMPILED CONTEXT MODEL
# =============================================================================

@dataclass
class CompiledContext:
    """
    A compiled view of context for a specific decision.
    
    Contains only what's needed for the decision at hand,
    not the entire agent state.
    """
    # Decision metadata
    decision_type: str              # "trade", "diplomacy", "intel", etc.
    timestamp: datetime = field(default_factory=datetime.now)
    
    # Agent summary (compressed)
    agent_summary: str = ""         # ~100 tokens max
    agent_archetype: str = ""
    agent_wallet_balance: float = 0.0
    
    # Market/environment state (relevant subset)
    market_state: Dict[str, Any] = field(default_factory=dict)
    
    # Filtered signals (only decision-relevant)
    relevant_signals: List[Dict] = field(default_factory=list)
    
    # Skill instructions (loaded from SKILL.md)
    skill_instructions: str = ""
    
    # Relationship context (for diplomatic decisions)
    relationship_context: Optional[str] = None
    
    # Recent history (last 3-5 relevant events)
    recent_history: List[str] = field(default_factory=list)
    
    @property
    def estimated_tokens(self) -> int:
        """Estimate total tokens in this context."""
        total_chars = (
            len(self.agent_summary) +
            len(json.dumps(self.market_state)) +
            sum(len(json.dumps(s)) for s in self.relevant_signals) +
            len(self.skill_instructions) +
            len(self.relationship_context or "") +
            sum(len(h) for h in self.recent_history)
        )
        # Rough estimate: 4 chars per token
        return total_chars // 4
    
    def to_prompt(self) -> str:
        """Convert compiled context to a prompt string."""
        sections = []
        
        # Agent identity
        sections.append(f"## Agent: {self.agent_archetype}")
        sections.append(self.agent_summary)
        sections.append(f"Wallet Balance: ${self.agent_wallet_balance:,.2f}")
        
        # Market state
        if self.market_state:
            sections.append("\n## Market State")
            for key, value in self.market_state.items():
                sections.append(f"- {key}: {value}")
        
        # Relevant signals
        if self.relevant_signals:
            sections.append("\n## Active Signals")
            for signal in self.relevant_signals[:5]:  # Max 5 signals
                sections.append(f"- [{signal.get('source', 'unknown')}] {signal.get('summary', 'No summary')}")
        
        # Relationship context
        if self.relationship_context:
            sections.append("\n## Relationship Context")
            sections.append(self.relationship_context)
        
        # Recent history
        if self.recent_history:
            sections.append("\n## Recent Events")
            for event in self.recent_history[-3:]:  # Last 3 events
                sections.append(f"- {event}")
        
        # Skill instructions
        if self.skill_instructions:
            sections.append("\n## Decision Framework")
            sections.append(self.skill_instructions)
        
        return "\n".join(sections)


# =============================================================================
# CONTEXT COMPILER
# =============================================================================

class ContextCompiler:
    """
    Compiles minimal context for each decision type.
    
    Instead of dumping entire agent state into every prompt,
    we extract only what's relevant for the specific decision.
    
    Example:
        compiler = ContextCompiler()
        context = compiler.compile_for_trade(agent, market, signals)
        # Returns ~300 tokens instead of ~5000
    """
    
    def __init__(self, skills_path: Optional[Path] = None):
        self.skills_path = skills_path or Path(__file__).parent
    
    # =========================================================================
    # TRADE DECISIONS
    # =========================================================================
    
    def compile_for_trade(
        self,
        agent: Any,
        market: Dict[str, Any],
        signals: Optional[List[Dict]] = None,
    ) -> CompiledContext:
        """
        Compile context for trading decisions.
        
        Includes:
        - Agent archetype and wallet
        - Market price, liquidity, expiry
        - Price-relevant signals only
        - Trading skill instructions
        """
        return CompiledContext(
            decision_type="trade",
            agent_summary=self._summarise_agent_for_trade(agent),
            agent_archetype=getattr(agent, "archetype", "SHARK"),
            agent_wallet_balance=getattr(agent, "bankroll", 0.0),
            market_state=self._extract_trade_market(market),
            relevant_signals=self._filter_trade_signals(signals or []),
            skill_instructions=self._load_trade_skill(agent),
            recent_history=self._get_trade_history(agent),
        )
    
    def _summarise_agent_for_trade(self, agent: Any) -> str:
        """Create a brief trading-relevant agent summary."""
        archetype = getattr(agent, "archetype", "SHARK")
        aggression = getattr(agent, "aggression", 0.5)
        risk_tolerance = getattr(agent, "risk_tolerance", 0.5)
        
        summaries = {
            "SHARK": f"Aggressive predator (aggression: {aggression:.1f}). Hunts liquidity gaps and mispricings.",
            "WHALE": f"Patient accumulator (risk: {risk_tolerance:.1f}). Builds large positions slowly.",
            "DEGEN": f"High-risk gambler (aggression: {aggression:.1f}). Chases momentum and hype.",
            "VALUE": f"Contrarian buyer (risk: {risk_tolerance:.1f}). Buys fear, sells greed.",
            "MOMENTUM": f"Trend follower (aggression: {aggression:.1f}). Rides winners, cuts losers.",
            "SPY": f"Intelligence gatherer. Prioritises information over positions.",
            "DIPLOMAT": f"Market stabiliser. Seeks equilibrium and consensus.",
            "SABOTEUR": f"Chaos agent. Profits from volatility and misinformation.",
        }
        
        return summaries.get(archetype, f"Unknown archetype: {archetype}")
    
    def _extract_trade_market(self, market: Dict) -> Dict[str, Any]:
        """Extract only trading-relevant market data."""
        return {
            "market_id": market.get("id", "unknown"),
            "question": market.get("question", "")[:100],  # Truncate
            "yes_price": market.get("yes_price", 0.5),
            "no_price": market.get("no_price", 0.5),
            "liquidity": market.get("current_liquidity", 0),
            "volume_24h": market.get("volume_24h", 0),
            "hours_to_expiry": market.get("hours_to_expiry"),
            "spread": market.get("spread", 0),
        }
    
    def _filter_trade_signals(self, signals: List[Dict]) -> List[Dict]:
        """Filter signals to price-relevant only."""
        relevant_categories = {"price", "volume", "whale", "news", "sentiment"}
        
        filtered = []
        for signal in signals:
            category = signal.get("category", "").lower()
            if any(cat in category for cat in relevant_categories):
                filtered.append({
                    "source": signal.get("source", "unknown"),
                    "category": category,
                    "summary": signal.get("summary", "")[:80],
                    "confidence": signal.get("confidence", 0.5),
                })
        
        # Return top 5 by confidence
        return sorted(filtered, key=lambda x: x["confidence"], reverse=True)[:5]
    
    def _load_trade_skill(self, agent: Any) -> str:
        """Load trading skill instructions for agent archetype."""
        archetype = getattr(agent, "archetype", "SHARK").lower()
        skill_path = self.skills_path / archetype / "SKILL.md"
        
        if skill_path.exists():
            content = skill_path.read_text()
            # Extract decision framework section
            if "## Decision Framework" in content:
                start = content.index("## Decision Framework")
                end = content.find("##", start + 10)
                return content[start:end].strip() if end > 0 else content[start:].strip()
        
        # Default trading instructions
        return """
## Decision Framework
1. Check liquidity - is this market tradeable?
2. Assess edge - do you have information advantage?
3. Size position - never risk more than 10% on one trade
4. Set exit - define profit target and stop loss
"""
    
    def _get_trade_history(self, agent: Any) -> List[str]:
        """Get recent trading history."""
        history = getattr(agent, "memory", [])
        trade_events = [h for h in history if "trade" in h.lower() or "bet" in h.lower()]
        return trade_events[-3:]  # Last 3 trades
    
    # =========================================================================
    # DIPLOMACY DECISIONS
    # =========================================================================
    
    def compile_for_diplomacy(
        self,
        agent: Any,
        counterparty: Any,
        proposal: Optional[Dict] = None,
    ) -> CompiledContext:
        """
        Compile context for diplomatic decisions (treaties, alliances).
        
        Includes:
        - Both agents' summaries
        - Relationship history
        - Proposal terms
        - Diplomatic skill instructions
        """
        return CompiledContext(
            decision_type="diplomacy",
            agent_summary=self._summarise_agent_for_diplomacy(agent),
            agent_archetype=getattr(agent, "archetype", "DIPLOMAT"),
            agent_wallet_balance=getattr(agent, "bankroll", 0.0),
            market_state={"proposal": proposal} if proposal else {},
            relevant_signals=[],
            skill_instructions=self._load_diplomacy_skill(agent),
            relationship_context=self._get_relationship_context(agent, counterparty),
            recent_history=self._get_diplomacy_history(agent, counterparty),
        )
    
    def _summarise_agent_for_diplomacy(self, agent: Any) -> str:
        """Create diplomacy-relevant agent summary."""
        loyalty = getattr(agent, "loyalty", 0.5)
        deception = getattr(agent, "deception", 0.3)
        
        return f"Loyalty: {loyalty:.1f}, Deception: {deception:.1f}. " + \
               f"Allies: {len(getattr(agent, 'allies', []))}, Rivals: {len(getattr(agent, 'rivals', []))}"
    
    def _get_relationship_context(self, agent: Any, counterparty: Any) -> str:
        """Get relationship history between two agents."""
        agent_id = getattr(agent, "id", "unknown")
        counter_id = getattr(counterparty, "id", "unknown")
        
        allies = getattr(agent, "allies", [])
        rivals = getattr(agent, "rivals", [])
        
        if counter_id in allies:
            relationship = "ALLY - Previous cooperation successful"
        elif counter_id in rivals:
            relationship = "RIVAL - History of conflict"
        else:
            relationship = "NEUTRAL - No prior relationship"
        
        return f"Agent {agent_id} → {counter_id}: {relationship}"
    
    def _load_diplomacy_skill(self, agent: Any) -> str:
        """Load diplomatic skill instructions."""
        return """
## Decision Framework
1. Assess counterparty - trustworthy? What do they want?
2. Evaluate proposal - fair terms? Hidden traps?
3. Consider long-term - will this strengthen your position?
4. Trust but verify - include enforcement mechanisms
"""
    
    def _get_diplomacy_history(self, agent: Any, counterparty: Any) -> List[str]:
        """Get diplomatic history with counterparty."""
        history = getattr(agent, "memory", [])
        counter_id = getattr(counterparty, "id", "")
        
        relevant = [h for h in history if counter_id in h or "treaty" in h.lower()]
        return relevant[-3:]
    
    # =========================================================================
    # INTEL DECISIONS
    # =========================================================================
    
    def compile_for_intel(
        self,
        agent: Any,
        intel_package: Dict[str, Any],
        market_exposure: float = 0.0,
    ) -> CompiledContext:
        """
        Compile context for intel purchase/sale decisions.
        
        Includes:
        - Agent intel utilisation trait
        - Intel package details
        - Current market exposure
        - Intel skill instructions
        """
        return CompiledContext(
            decision_type="intel",
            agent_summary=self._summarise_agent_for_intel(agent),
            agent_archetype=getattr(agent, "archetype", "SPY"),
            agent_wallet_balance=getattr(agent, "bankroll", 0.0),
            market_state={
                "intel_price": intel_package.get("price", 0),
                "intel_source": intel_package.get("source", "unknown"),
                "intel_accuracy": intel_package.get("historical_accuracy", 0.5),
                "market_exposure": market_exposure,
            },
            relevant_signals=[intel_package],
            skill_instructions=self._load_intel_skill(agent),
        )
    
    def _summarise_agent_for_intel(self, agent: Any) -> str:
        """Create intel-relevant agent summary."""
        intel_util = getattr(agent, "intel_utilization", 0.5)
        return f"Intel utilisation: {intel_util:.1f}. Values information {'highly' if intel_util > 0.7 else 'moderately' if intel_util > 0.4 else 'minimally'}."
    
    def _load_intel_skill(self, agent: Any) -> str:
        """Load intel skill instructions."""
        return """
## Decision Framework
1. Verify source - what's their track record?
2. Calculate value - how much edge does this intel provide?
3. Compare cost - is the price justified by expected profit?
4. Act fast - intel value decays rapidly
"""
    
    # =========================================================================
    # MISSION DECISIONS
    # =========================================================================
    
    def compile_for_mission(
        self,
        agent: Any,
        mission: Dict[str, Any],
        world_state: Optional[Dict] = None,
    ) -> CompiledContext:
        """
        Compile context for mission acceptance/execution.
        
        Includes:
        - Agent capabilities
        - Mission requirements and rewards
        - Current world state
        - Mission skill instructions
        """
        return CompiledContext(
            decision_type="mission",
            agent_summary=self._summarise_agent_for_mission(agent),
            agent_archetype=getattr(agent, "archetype", "SHARK"),
            agent_wallet_balance=getattr(agent, "bankroll", 0.0),
            market_state={
                "mission_type": mission.get("type", "unknown"),
                "difficulty": mission.get("difficulty", "MEDIUM"),
                "reward": mission.get("reward", 0),
                "required_roles": mission.get("required_roles", []),
                "time_limit": mission.get("time_limit_hours", 24),
                "global_tension": world_state.get("tension", 0.5) if world_state else 0.5,
            },
            skill_instructions=self._load_mission_skill(agent, mission),
        )
    
    def _summarise_agent_for_mission(self, agent: Any) -> str:
        """Create mission-relevant agent summary."""
        archetype = getattr(agent, "archetype", "SHARK")
        skills = {
            "SHARK": "combat, trading, intimidation",
            "SPY": "infiltration, intel gathering, analysis",
            "DIPLOMAT": "negotiation, persuasion, alliance building",
            "SABOTEUR": "deception, disruption, misdirection",
        }
        return f"{archetype} - Skills: {skills.get(archetype, 'general')}"
    
    def _load_mission_skill(self, agent: Any, mission: Dict) -> str:
        """Load mission skill instructions."""
        mission_type = mission.get("type", "general").lower()
        
        skills = {
            "ghost_tanker": "Track vessel movements, analyse AIS gaps, predict destinations.",
            "silicon_acquisition": "Monitor job postings, patent filings, insider signals.",
            "contagion_zero": "Analyse health data clusters, social media mentions, official reports.",
            "deep_state_shuffle": "Track VIP movements, power infrastructure, communications.",
        }
        
        base = skills.get(mission_type, "Analyse situation, identify opportunities, execute plan.")
        
        return f"""
## Mission: {mission.get('type', 'Unknown')}
{base}

## Execution Framework
1. Assess - Do you have the skills for this mission?
2. Plan - What's your approach?
3. Execute - Take decisive action
4. Report - Document findings
"""
    
    # =========================================================================
    # SABOTAGE DECISIONS
    # =========================================================================
    
    def compile_for_sabotage(
        self,
        agent: Any,
        target: Any,
        sabotage_type: str,
    ) -> CompiledContext:
        """
        Compile context for sabotage operations (Saboteur agents).
        
        Includes:
        - Agent deception capability
        - Target vulnerabilities
        - Sabotage type and methods
        """
        return CompiledContext(
            decision_type="sabotage",
            agent_summary=self._summarise_agent_for_sabotage(agent),
            agent_archetype="SABOTEUR",
            agent_wallet_balance=getattr(agent, "bankroll", 0.0),
            market_state={
                "sabotage_type": sabotage_type,
                "target_id": getattr(target, "id", "unknown"),
                "target_archetype": getattr(target, "archetype", "unknown"),
            },
            skill_instructions=self._load_sabotage_skill(sabotage_type),
            relationship_context=f"Target resilience: {getattr(target, 'resilience', 0.5):.1f}",
        )
    
    def _summarise_agent_for_sabotage(self, agent: Any) -> str:
        """Create sabotage-relevant agent summary."""
        deception = getattr(agent, "deception", 0.5)
        patience = getattr(agent, "patience", 0.5)
        return f"Deception: {deception:.1f}, Patience: {patience:.1f}. Master of misdirection."
    
    def _load_sabotage_skill(self, sabotage_type: str) -> str:
        """Load sabotage skill instructions."""
        skills = {
            "fud": "Spread fear, uncertainty, doubt. Target emotional vulnerabilities.",
            "leak": "Release damaging intel at maximum impact moment.",
            "mole": "Infiltrate target organisation. Build trust, then betray.",
            "disrupt": "Interfere with communications, trades, alliances.",
        }
        
        return f"""
## Sabotage Type: {sabotage_type}
{skills.get(sabotage_type, 'Execute covert operation.')}

## Framework
1. Assess detection risk
2. Maximise impact, minimise exposure
3. Have exit strategy ready
4. Maintain cover for future operations
"""


# =============================================================================
# CONTEXT METRICS
# =============================================================================

@dataclass
class ContextMetrics:
    """Track context compilation efficiency."""
    decision_type: str
    raw_state_tokens: int
    compiled_tokens: int
    compression_ratio: float
    compilation_time_ms: float


class ContextMetricsCollector:
    """Collect metrics on context compilation efficiency."""
    
    def __init__(self):
        self.metrics: List[ContextMetrics] = []
    
    def record(self, metrics: ContextMetrics):
        self.metrics.append(metrics)
    
    def summary(self) -> Dict[str, Any]:
        if not self.metrics:
            return {"message": "No metrics collected"}
        
        avg_compression = sum(m.compression_ratio for m in self.metrics) / len(self.metrics)
        avg_time = sum(m.compilation_time_ms for m in self.metrics) / len(self.metrics)
        
        by_type = {}
        for m in self.metrics:
            if m.decision_type not in by_type:
                by_type[m.decision_type] = []
            by_type[m.decision_type].append(m.compiled_tokens)
        
        return {
            "total_compilations": len(self.metrics),
            "avg_compression_ratio": f"{avg_compression:.2f}x",
            "avg_compilation_time_ms": f"{avg_time:.2f}",
            "tokens_by_type": {
                k: f"{sum(v)/len(v):.0f} avg tokens"
                for k, v in by_type.items()
            },
        }


# =============================================================================
# DEMO
# =============================================================================

def demo():
    """Demonstrate context compilation."""
    print("=" * 60)
    print("📦 CONTEXT COMPILER DEMO")
    print("=" * 60)
    
    # Mock agent
    class MockAgent:
        id = "shark-001"
        archetype = "SHARK"
        bankroll = 5000.0
        aggression = 0.8
        risk_tolerance = 0.7
        deception = 0.3
        loyalty = 0.5
        intel_utilization = 0.9
        memory = ["Bought YES at 0.35", "Sold NO at 0.68", "Lost 50 USDC on DOGE"]
        allies = ["whale-002"]
        rivals = ["degen-003"]
    
    agent = MockAgent()
    compiler = ContextCompiler()
    
    # Trade context
    market = {
        "id": "market-001",
        "question": "Will Taiwan crisis escalate this week?",
        "yes_price": 0.35,
        "no_price": 0.68,
        "current_liquidity": 3200,
        "volume_24h": 8500,
        "hours_to_expiry": 8,
        "spread": 0.03,
    }
    
    signals = [
        {"source": "RavenPack", "category": "news", "summary": "Taiwan military exercises announced", "confidence": 0.8},
        {"source": "WhaleAlert", "category": "whale", "summary": "Large YES position opened", "confidence": 0.7},
        {"source": "Twitter", "category": "sentiment", "summary": "Fear index rising", "confidence": 0.6},
    ]
    
    trade_context = compiler.compile_for_trade(agent, market, signals)
    
    print(f"\n📊 Trade Context Compiled:")
    print(f"   Decision Type: {trade_context.decision_type}")
    print(f"   Estimated Tokens: ~{trade_context.estimated_tokens}")
    print(f"   Market: {trade_context.market_state.get('question', '')[:50]}...")
    print(f"   Signals: {len(trade_context.relevant_signals)}")
    
    print(f"\n📝 Full Context Prompt ({trade_context.estimated_tokens} tokens):")
    print("-" * 40)
    print(trade_context.to_prompt()[:500] + "...")


if __name__ == "__main__":
    demo()
