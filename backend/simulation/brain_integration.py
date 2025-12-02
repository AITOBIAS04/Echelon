"""
Multi-Brain Integration for Market Simulation
==============================================
This module provides integration between the MarketSimulation engine
and the cost-optimized AgentBrain system.

Usage:

    # Option 1: Replace the entire run_tick method
    from simulation.brain_integration import BrainEnabledSimulation
    sim = BrainEnabledSimulation(game_hash)
    
    # Option 2: Patch existing simulation
    from simulation.brain_integration import patch_simulation_with_brain
    sim = MarketSimulation(game_hash)
    patch_simulation_with_brain(sim)
"""

import asyncio
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field

# Import brain
try:
    from backend.agents.multi_brain import AgentBrain, BrainConfig, Decision
    HAS_BRAIN = True
except ImportError:
    try:
        from agents.multi_brain import AgentBrain, BrainConfig, Decision
        HAS_BRAIN = True
    except ImportError:
        HAS_BRAIN = False
        print("⚠️ multi_brain not available, using default agent logic")

@dataclass
class SocialPost:
    """A social media post from an agent."""
    agent_name: str
    agent_archetype: str
    message: str
    action: str
    asset: str
    tick: int

class BrainIntegration:
    """
    Wrapper to integrate AgentBrain with MarketSimulation.
    
    This class handles:
    - Async/sync bridging
    - Social feed generation from LLM responses
    - Decision statistics
    """
    
    def __init__(self, llm_probability: float = 0.1):
        """
        Initialize brain integration.
        
        Args:
            llm_probability: % of decisions that use LLM (0.1 = 10%)
        """
        if HAS_BRAIN:
            self.brain = AgentBrain(BrainConfig(llm_probability=llm_probability))
        else:
            self.brain = None
        
        self.social_feed: List[SocialPost] = []
        self.stats = {
            "total_decisions": 0,
            "llm_decisions": 0,
            "rule_decisions": 0,
        }
    
    def get_decision(
        self,
        agent_id: str,
        archetype: str,
        asset_price: float,
        asset_symbol: str,
        sentiment: float,
        trend: float
    ) -> tuple[str, str]:
        """
        Get a decision from the brain (sync wrapper).
        
        Returns:
            tuple of (action, reasoning)
        """
        if not self.brain:
            # Fallback if brain not available
            return "HOLD", "Brain not available"
        
        # Build market context
        market_data = {
            "sentiment": sentiment,
            "trend": trend,
            "price": asset_price,
            "symbol": asset_symbol,
        }
        
        # Run async brain in sync context
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If we're already in an async context, create task
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        asyncio.run,
                        self.brain.decide(agent_id, archetype, market_data)
                    )
                    decision = future.result(timeout=5)
            else:
                decision = asyncio.run(
                    self.brain.decide(agent_id, archetype, market_data)
                )
        except Exception as e:
            print(f"⚠️ Brain error: {e}")
            return "HOLD", "Decision error"
        
        # Track stats
        self.stats["total_decisions"] += 1
        if decision.provider_used == "rule_based":
            self.stats["rule_decisions"] += 1
        else:
            self.stats["llm_decisions"] += 1
        
        return decision.action, decision.reasoning
    
    def record_social_post(
        self,
        agent_name: str,
        archetype: str,
        message: str,
        action: str,
        asset: str,
        tick: int
    ):
        """Record a social post from an LLM decision."""
        post = SocialPost(
            agent_name=agent_name,
            agent_archetype=archetype,
            message=message,
            action=action,
            asset=asset,
            tick=tick
        )
        self.social_feed.append(post)
        
        # Keep only last 100 posts
        if len(self.social_feed) > 100:
            self.social_feed = self.social_feed[-100:]
    
    def get_recent_posts(self, count: int = 10) -> List[Dict]:
        """Get recent social posts as dicts."""
        return [
            {
                "agent": p.agent_name,
                "archetype": p.agent_archetype,
                "message": p.message,
                "action": p.action,
                "asset": p.asset,
                "tick": p.tick,
            }
            for p in self.social_feed[-count:]
        ]
    
    def get_stats(self) -> Dict:
        """Get brain usage statistics."""
        stats = {**self.stats}
        if self.brain:
            stats["brain_stats"] = self.brain.get_stats()
        return stats

def patch_simulation_with_brain(simulation, llm_probability: float = 0.1):
    """
    Patch an existing MarketSimulation instance with brain support.
    
    Usage:
        sim = MarketSimulation(game_hash)
        sim.initialize()
        patch_simulation_with_brain(sim, llm_probability=0.1)
        sim.run_tick()  # Now uses multi_brain!
    """
    integration = BrainIntegration(llm_probability)
    simulation._brain_integration = integration
    
    # Store original run_tick
    original_run_tick = simulation.run_tick
    
    def enhanced_run_tick() -> Dict[str, Any]:
        """Enhanced run_tick with brain integration."""
        tick_summary = {
            "tick": simulation.tick,
            "news": None,
            "price_changes": {},
            "notable_trades": [],
            "market_events": [],
            "social_feed": [],  # NEW: Agent social posts
        }
        
        # Get news for this tick
        news = simulation.news_queue[simulation.tick] if simulation.tick < len(simulation.news_queue) else None
        if news:
            tick_summary["news"] = news.to_dict()
            simulation._log_event("NEWS", news.headline, news.to_dict())
        
        # Calculate sentiment for each asset
        asset_sentiment = {}
        for symbol, asset in simulation.assets.items():
            base_sentiment = simulation.market_mood - 0.5
            if news and symbol in news.affected_assets:
                base_sentiment += news.sentiment * news.magnitude
            asset_sentiment[symbol] = max(-1, min(1, base_sentiment))
        
        # Import AgentStatus
        from backend.agents.schemas import AgentStatus
        
        # Each asset gets traded
        for symbol, asset in simulation.assets.items():
            buy_pressure = 0.0
            sell_pressure = 0.0
            
            sentiment = asset_sentiment[symbol]
            trend = asset.trend
            
            # Each agent decides using BRAIN
            for agent in simulation.agents:
                if agent.status != AgentStatus.ACTIVE:
                    continue
                
                # Get decision from brain
                action, reasoning = integration.get_decision(
                    agent_id=agent.id,
                    archetype=agent.archetype.value,
                    asset_price=asset.price,
                    asset_symbol=symbol,
                    sentiment=sentiment,
                    trend=trend
                )
                
                impact = simulation._calculate_agent_impact(agent)
                trade_happened = False
                
                if action == "BUY":
                    if agent.execute_trade("BUY", symbol, asset.price, quantity=1):
                        buy_pressure += impact
                        trade_happened = True
                        
                        if impact > 1:
                            tick_summary["notable_trades"].append({
                                "agent": agent.archetype.value,
                                "action": "BUY",
                                "asset": symbol,
                                "price": asset.price
                            })
                            
                elif action == "SELL":
                    if agent.execute_trade("SELL", symbol, asset.price, quantity=1):
                        sell_pressure += impact
                        trade_happened = True
                        
                        if impact > 1:
                            tick_summary["notable_trades"].append({
                                "agent": agent.archetype.value,
                                "action": "SELL",
                                "asset": symbol,
                                "price": asset.price
                            })
                
                # If LLM was used, add to social feed
                if trade_happened and reasoning != "Market unclear." and len(reasoning) > 10:
                    integration.record_social_post(
                        agent_name=agent.name,
                        archetype=agent.archetype.value,
                        message=reasoning,
                        action=action,
                        asset=symbol,
                        tick=simulation.tick
                    )
            
            # Update price
            old_price = asset.price
            change_pct = asset.update_price(buy_pressure, sell_pressure)
            tick_summary["price_changes"][symbol] = {
                "old": round(old_price, 2),
                "new": round(asset.price, 2),
                "change_pct": round(change_pct * 100, 2),
                "buy_pressure": buy_pressure,
                "sell_pressure": sell_pressure
            }
            
            # Detect significant events
            if abs(change_pct) > 0.03:
                event_type = "PUMP" if change_pct > 0 else "DUMP"
                simulation._log_event(
                    event_type,
                    f"{symbol} moves {change_pct*100:+.1f}%",
                    {"symbol": symbol, "change": change_pct}
                )
                tick_summary["market_events"].append(f"{symbol} {event_type}")
        
        # Add social feed to summary
        tick_summary["social_feed"] = integration.get_recent_posts(5)
        
        simulation.tick += 1
        return tick_summary
    
    # Replace run_tick
    simulation.run_tick = enhanced_run_tick
    
    # Add convenience methods
    simulation.get_brain_stats = lambda: integration.get_stats()
    simulation.get_social_feed = lambda count=10: integration.get_recent_posts(count)
    
    return simulation

# =============================================================================
# ASYNC VERSION (For use in FastAPI routes)
# =============================================================================

async def run_tick_async(simulation, integration: BrainIntegration) -> Dict[str, Any]:
    """
    Async version of run_tick for use in FastAPI.
    """
    tick_summary = {
        "tick": simulation.tick,
        "news": None,
        "price_changes": {},
        "notable_trades": [],
        "market_events": [],
        "social_feed": [],
    }
    
    news = simulation.news_queue[simulation.tick] if simulation.tick < len(simulation.news_queue) else None
    if news:
        tick_summary["news"] = news.to_dict()
    
    # Calculate sentiment
    asset_sentiment = {}
    for symbol, asset in simulation.assets.items():
        base_sentiment = simulation.market_mood - 0.5
        if news and symbol in news.affected_assets:
            base_sentiment += news.sentiment * news.magnitude
        asset_sentiment[symbol] = max(-1, min(1, base_sentiment))
    
    from backend.agents.schemas import AgentStatus
    
    # Process each asset
    for symbol, asset in simulation.assets.items():
        buy_pressure = 0.0
        sell_pressure = 0.0
        
        sentiment = asset_sentiment[symbol]
        trend = asset.trend
        
        # Batch agent decisions for efficiency
        for agent in simulation.agents:
            if agent.status != AgentStatus.ACTIVE:
                continue
            
            # Async brain decision
            if integration.brain:
                market_data = {
                    "sentiment": sentiment,
                    "trend": trend,
                    "price": asset.price,
                    "symbol": symbol,
                }
                decision = await integration.brain.decide(
                    agent.id,
                    agent.archetype.value,
                    market_data
                )
                action = decision.action
                reasoning = decision.reasoning
            else:
                action = "HOLD"
                reasoning = ""
            
            impact = simulation._calculate_agent_impact(agent)
            trade_happened = False
            
            if action == "BUY":
                if agent.execute_trade("BUY", symbol, asset.price, quantity=1):
                    buy_pressure += impact
                    trade_happened = True
            elif action == "SELL":
                if agent.execute_trade("SELL", symbol, asset.price, quantity=1):
                    sell_pressure += impact
                    trade_happened = True
            
            # Social feed
            if trade_happened and reasoning and len(reasoning) > 10:
                integration.record_social_post(
                    agent.name, agent.archetype.value,
                    reasoning, action, symbol, simulation.tick
                )
        
        # Update price
        old_price = asset.price
        change_pct = asset.update_price(buy_pressure, sell_pressure)
        tick_summary["price_changes"][symbol] = {
            "old": round(old_price, 2),
            "new": round(asset.price, 2),
            "change_pct": round(change_pct * 100, 2),
        }
    
    tick_summary["social_feed"] = integration.get_recent_posts(5)
    simulation.tick += 1
    
    return tick_summary




