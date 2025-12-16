"""
Agent Scheduler
===============

Background task scheduler for autonomous agent operations.

This module manages:
- Periodic agent decision cycles
- OSINT listener polling
- Market opportunity scanning
- Intel publishing schedules
- ACP job monitoring

Architecture:
- Uses APScheduler for background tasks
- Agents run on configurable intervals
- Layer 1 rules handle 90%+ of decisions (cost-free)
- Novel situations escalate to LLM
"""

import asyncio
import os
import sys
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import logging
import random

# Add backend to path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("agent_scheduler")


# =============================================================================
# CONFIGURATION
# =============================================================================

class AgentState(Enum):
    IDLE = "idle"
    SCANNING = "scanning"
    TRADING = "trading"
    PUBLISHING = "publishing"
    WAITING = "waiting"


@dataclass
class ScheduledAgent:
    """Agent configuration for scheduling."""
    agent_id: str
    archetype: str
    state: AgentState = AgentState.IDLE
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    run_interval_seconds: int = 60
    decisions_today: int = 0
    cost_today_usd: float = 0.0
    enabled: bool = True
    
    # Performance tracking
    trades_executed: int = 0
    intel_published: int = 0
    total_pnl: float = 0.0


@dataclass
class SchedulerStats:
    """Scheduler statistics."""
    total_cycles: int = 0
    layer1_decisions: int = 0
    layer2_decisions: int = 0
    layer3_decisions: int = 0
    total_cost_usd: float = 0.0
    trades_executed: int = 0
    intel_published: int = 0
    errors: int = 0
    last_cycle: Optional[datetime] = None


# =============================================================================
# MOCK MARKET DATA (Replace with real API calls)
# =============================================================================

def get_mock_markets() -> List[Dict[str, Any]]:
    """Get mock market data for testing."""
    return [
        {
            "market_id": "tanker-china-48h",
            "yes_price": 0.35,
            "liquidity": 3500,
            "hours_to_expiry": 12,
            "volume_24h": 5000,
            "price_24h_change": 0.05,
        },
        {
            "market_id": "fed-rate-cut-jan",
            "yes_price": 0.72,
            "liquidity": 150000,
            "hours_to_expiry": 720,
            "volume_24h": 25000,
            "price_24h_change": -0.02,
        },
        {
            "market_id": "apple-ai-announcement",
            "yes_price": 0.45,
            "liquidity": 8000,
            "hours_to_expiry": 48,
            "volume_24h": 3000,
            "price_24h_change": 0.08,
        },
    ]


def get_mock_signals() -> List[Dict[str, Any]]:
    """Get mock OSINT signals for testing."""
    signal_types = [
        {"type": "SHIP_DARK", "source": "spire", "severity": "high"},
        {"type": "SOCIAL_SPIKE", "source": "x_api", "severity": "medium"},
        {"type": "NEWS_BREAK", "source": "dataminr", "severity": "high"},
        {"type": "PRICE_MOVE", "source": "polygon", "severity": "low"},
    ]
    return random.sample(signal_types, k=random.randint(0, 2))


# =============================================================================
# AGENT SCHEDULER
# =============================================================================

class AgentScheduler:
    """
    Manages background execution of autonomous agents.
    
    Features:
    - Configurable run intervals per agent
    - Cost tracking and budgets
    - Layer 1/2/3 decision routing
    - Health monitoring
    """
    
    def __init__(self, max_daily_budget_usd: float = 10.0):
        self.agents: Dict[str, ScheduledAgent] = {}
        self.stats = SchedulerStats()
        self.max_daily_budget_usd = max_daily_budget_usd
        self.running = False
        self._task: Optional[asyncio.Task] = None
        
        # Import Layer 1 engine
        try:
            from backend.skills.layer1_rules import (
                Layer1Engine,
                DecisionType,
                RuleResult,
                create_market_context,
                create_agent_context
            )
            self.layer1_engine = Layer1Engine()
            self.has_layer1 = True
            logger.info("✅ Layer 1 Rules Engine loaded")
        except ImportError as e:
            self.layer1_engine = None
            self.has_layer1 = False
            logger.warning(f"⚠️ Layer 1 not available: {e}")
    
    def register_agent(
        self,
        agent_id: str,
        archetype: str,
        run_interval_seconds: int = 60,
        enabled: bool = True
    ) -> ScheduledAgent:
        """Register an agent for scheduled execution."""
        agent = ScheduledAgent(
            agent_id=agent_id,
            archetype=archetype,
            run_interval_seconds=run_interval_seconds,
            enabled=enabled,
            next_run=datetime.now(timezone.utc)
        )
        self.agents[agent_id] = agent
        logger.info(f"📝 Registered agent: {agent_id} ({archetype}) - interval: {run_interval_seconds}s")
        return agent
    
    def unregister_agent(self, agent_id: str):
        """Remove an agent from scheduling."""
        if agent_id in self.agents:
            del self.agents[agent_id]
            logger.info(f"🗑️ Unregistered agent: {agent_id}")
    
    async def run_agent_cycle(self, agent: ScheduledAgent) -> Dict[str, Any]:
        """
        Run a single decision cycle for an agent.
        
        Returns decision results and stats.
        """
        agent.state = AgentState.SCANNING
        agent.last_run = datetime.now(timezone.utc)
        
        results = {
            "agent_id": agent.agent_id,
            "timestamp": agent.last_run.isoformat(),
            "decisions": [],
            "actions": [],
            "cost_usd": 0.0,
            "layer_used": "LAYER_1",
        }
        
        try:
            # Get market data
            markets = get_mock_markets()
            signals = get_mock_signals()
            
            # Check each market for opportunities
            for market in markets:
                decision = await self._evaluate_market(agent, market, signals)
                results["decisions"].append(decision)
                
                if decision.get("action"):
                    results["actions"].append(decision)
                    agent.decisions_today += 1
                    
                    # Track costs
                    cost = decision.get("cost_usd", 0.0)
                    results["cost_usd"] += cost
                    agent.cost_today_usd += cost
                    self.stats.total_cost_usd += cost
                    
                    # Track layer usage
                    layer = decision.get("layer_used", "LAYER_1")
                    if layer == "LAYER_1_RULES":
                        self.stats.layer1_decisions += 1
                    elif layer == "LAYER_2_LLM":
                        self.stats.layer2_decisions += 1
                    elif layer == "LAYER_3_CLOUD":
                        self.stats.layer3_decisions += 1
            
            agent.state = AgentState.IDLE
            
        except Exception as e:
            logger.error(f"❌ Agent {agent.agent_id} cycle error: {e}")
            agent.state = AgentState.IDLE
            self.stats.errors += 1
            results["error"] = str(e)
        
        # Schedule next run
        agent.next_run = datetime.now(timezone.utc) + timedelta(seconds=agent.run_interval_seconds)
        
        return results
    
    async def _evaluate_market(
        self,
        agent: ScheduledAgent,
        market: Dict[str, Any],
        signals: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Evaluate a market for trading opportunities."""
        
        if not self.has_layer1:
            # Fallback: random decision for testing
            return {
                "market_id": market["market_id"],
                "action": None,
                "reasoning": "Layer 1 not available",
                "layer_used": "NONE",
                "cost_usd": 0.0
            }
        
        from backend.skills.layer1_rules import (
            DecisionType,
            RuleResult,
            create_market_context,
            create_agent_context
        )
        
        # Create contexts
        market_ctx = create_market_context(
            market_id=market["market_id"],
            yes_price=market["yes_price"],
            liquidity=market["liquidity"],
            hours_to_expiry=market.get("hours_to_expiry"),
            volume_24h=market.get("volume_24h", 0),
            price_24h_change=market.get("price_24h_change", 0)
        )
        
        agent_ctx = create_agent_context(
            agent_id=agent.agent_id,
            archetype=agent.archetype,
            bankroll=1000.0,  # Mock bankroll
            aggression=0.6 if agent.archetype == "SHARK" else 0.4,
            risk_tolerance=0.5
        )
        
        # Run Layer 1 decision
        decision = self.layer1_engine.decide(
            market=market_ctx,
            agent=agent_ctx,
            decision_type=DecisionType.TRADE,
            external_probability=market["yes_price"] + random.uniform(-0.1, 0.1)  # Simulated edge
        )
        
        result = {
            "market_id": market["market_id"],
            "action": decision.action,
            "confidence": decision.confidence,
            "reasoning": decision.reasoning,
            "parameters": decision.parameters,
            "layer_used": "LAYER_1_RULES" if decision.result != RuleResult.ESCALATE else "ESCALATED",
            "cost_usd": 0.0 if decision.result != RuleResult.ESCALATE else 0.001
        }
        
        # Log interesting decisions
        if decision.action:
            logger.info(f"🎯 {agent.agent_id}: {decision.action} on {market['market_id']} - {decision.reasoning[:50]}")
        
        return result
    
    async def _scheduler_loop(self):
        """Main scheduler loop."""
        logger.info("🚀 Agent scheduler started")
        
        while self.running:
            now = datetime.now(timezone.utc)
            
            # Check daily budget
            if self.stats.total_cost_usd >= self.max_daily_budget_usd:
                logger.warning(f"⚠️ Daily budget exhausted: ${self.stats.total_cost_usd:.4f}")
                await asyncio.sleep(60)
                continue
            
            # Run due agents
            for agent in self.agents.values():
                if not agent.enabled:
                    continue
                
                if agent.next_run and now >= agent.next_run:
                    try:
                        results = await self.run_agent_cycle(agent)
                        self.stats.total_cycles += 1
                        self.stats.last_cycle = now
                        
                        # Log summary
                        actions = len(results.get("actions", []))
                        if actions > 0:
                            logger.info(
                                f"📊 {agent.agent_id}: {actions} actions, "
                                f"cost: ${results['cost_usd']:.4f}"
                            )
                    except Exception as e:
                        logger.error(f"❌ Scheduler error for {agent.agent_id}: {e}")
            
            # Short sleep between checks
            await asyncio.sleep(1)
        
        logger.info("🛑 Agent scheduler stopped")
    
    def start(self):
        """Start the scheduler."""
        if self.running:
            logger.warning("Scheduler already running")
            return
        
        self.running = True
        self._task = asyncio.create_task(self._scheduler_loop())
        logger.info("✅ Scheduler started")
    
    def stop(self):
        """Stop the scheduler."""
        self.running = False
        if self._task:
            self._task.cancel()
        logger.info("🛑 Scheduler stopped")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get scheduler statistics."""
        total_decisions = (
            self.stats.layer1_decisions +
            self.stats.layer2_decisions +
            self.stats.layer3_decisions
        )
        
        return {
            "running": self.running,
            "agents_registered": len(self.agents),
            "agents_enabled": len([a for a in self.agents.values() if a.enabled]),
            "total_cycles": self.stats.total_cycles,
            "total_decisions": total_decisions,
            "layer1_decisions": self.stats.layer1_decisions,
            "layer1_percentage": f"{(self.stats.layer1_decisions / max(total_decisions, 1)) * 100:.1f}%",
            "layer2_decisions": self.stats.layer2_decisions,
            "layer3_decisions": self.stats.layer3_decisions,
            "total_cost_usd": f"${self.stats.total_cost_usd:.4f}",
            "daily_budget_usd": f"${self.max_daily_budget_usd:.2f}",
            "budget_remaining": f"${self.max_daily_budget_usd - self.stats.total_cost_usd:.4f}",
            "errors": self.stats.errors,
            "last_cycle": self.stats.last_cycle.isoformat() if self.stats.last_cycle else None,
        }
    
    def get_agent_status(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific agent."""
        agent = self.agents.get(agent_id)
        if not agent:
            return None
        
        return {
            "agent_id": agent.agent_id,
            "archetype": agent.archetype,
            "state": agent.state.value,
            "enabled": agent.enabled,
            "run_interval_seconds": agent.run_interval_seconds,
            "last_run": agent.last_run.isoformat() if agent.last_run else None,
            "next_run": agent.next_run.isoformat() if agent.next_run else None,
            "decisions_today": agent.decisions_today,
            "cost_today_usd": f"${agent.cost_today_usd:.4f}",
            "trades_executed": agent.trades_executed,
            "intel_published": agent.intel_published,
            "total_pnl": f"${agent.total_pnl:.2f}",
        }


# =============================================================================
# GLOBAL SCHEDULER INSTANCE
# =============================================================================

_scheduler: Optional[AgentScheduler] = None


def get_scheduler() -> AgentScheduler:
    """Get or create the global scheduler instance."""
    global _scheduler
    if _scheduler is None:
        _scheduler = AgentScheduler()
    return _scheduler


def init_default_agents(scheduler: AgentScheduler):
    """Register default agents for the platform."""
    # Sharks - fast traders
    scheduler.register_agent("HAMMERHEAD", "SHARK", run_interval_seconds=30)
    scheduler.register_agent("TIGER", "SHARK", run_interval_seconds=45)
    
    # Spies - intel gatherers
    scheduler.register_agent("CARDINAL", "SPY", run_interval_seconds=60)
    scheduler.register_agent("RAVEN", "SPY", run_interval_seconds=90)
    
    # Diplomats - slower, strategic
    scheduler.register_agent("AMBASSADOR", "DIPLOMAT", run_interval_seconds=120)
    
    # Saboteurs - chaos agents
    scheduler.register_agent("PHANTOM", "SABOTEUR", run_interval_seconds=60)


# =============================================================================
# TESTING
# =============================================================================

async def test_scheduler():
    """Test the scheduler with mock agents."""
    scheduler = AgentScheduler(max_daily_budget_usd=1.0)
    
    # Register test agents
    scheduler.register_agent("TEST_SHARK", "SHARK", run_interval_seconds=5)
    scheduler.register_agent("TEST_SPY", "SPY", run_interval_seconds=10)
    
    # Start scheduler
    scheduler.start()
    
    # Run for 30 seconds
    try:
        for i in range(6):
            await asyncio.sleep(5)
            stats = scheduler.get_stats()
            print(f"\n📊 Stats after {(i+1)*5}s:")
            print(f"   Cycles: {stats['total_cycles']}")
            print(f"   Layer 1: {stats['layer1_percentage']}")
            print(f"   Cost: {stats['total_cost_usd']}")
    finally:
        scheduler.stop()
    
    # Final stats
    print("\n" + "="*50)
    print("FINAL STATS:")
    for k, v in scheduler.get_stats().items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    asyncio.run(test_scheduler())
