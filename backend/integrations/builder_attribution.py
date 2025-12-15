"""
Builder Code Attribution Manager
================================

Unified tracking system for Builder Code attribution across
Polymarket and Kalshi platforms.

Tracks:
- Volume by platform and market
- Revenue share calculations
- Agent-level attribution
- Leaderboard metrics

Author: Echelon Protocol
Version: 1.0.0
"""

import asyncio
import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


# =============================================================================
# ENUMS
# =============================================================================

class Platform(str, Enum):
    POLYMARKET = "polymarket"
    KALSHI = "kalshi"


class TimeRange(str, Enum):
    HOUR = "1h"
    DAY = "24h"
    WEEK = "7d"
    MONTH = "30d"
    ALL_TIME = "all"


# =============================================================================
# DATA MODELS
# =============================================================================

class BuilderConfig(BaseModel):
    """Builder code configuration."""
    
    code: str = Field(..., description="Builder code string")
    platform: Platform = Field(..., description="Platform this code is for")
    
    # Revenue share configuration
    revenue_share_bps: int = Field(0, description="Revenue share in basis points")
    
    # Registration details
    registered_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = Field(True)
    
    # Metadata
    description: Optional[str] = Field(None)
    website: Optional[str] = Field(None)


class TradeAttribution(BaseModel):
    """Single trade with builder attribution."""
    
    trade_id: str = Field(..., description="Unique trade identifier")
    platform: Platform = Field(..., description="Trading platform")
    
    market_id: str = Field(..., description="Market identifier")
    
    builder_code: str = Field(..., description="Builder code used")
    
    # Trade details
    side: str = Field(..., description="BUY/SELL or YES/NO")
    size: Decimal = Field(..., description="Trade size")
    price: Decimal = Field(..., description="Execution price")
    volume_usd: Decimal = Field(..., description="USD volume")
    
    # Attribution
    agent_id: Optional[str] = Field(None, description="Agent that made trade")
    user_address: Optional[str] = Field(None, description="User wallet")
    
    # Timing
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Revenue
    fee_collected: Decimal = Field(Decimal("0"), description="Fee in USD")
    revenue_share: Decimal = Field(Decimal("0"), description="Builder revenue share")


class VolumeMetrics(BaseModel):
    """Volume metrics for a time period."""
    
    platform: Platform
    time_range: TimeRange
    
    # Volume
    total_volume_usd: Decimal = Field(Decimal("0"))
    trade_count: int = Field(0)
    unique_users: int = Field(0)
    unique_markets: int = Field(0)
    
    # Revenue
    total_fees: Decimal = Field(Decimal("0"))
    revenue_share: Decimal = Field(Decimal("0"))
    
    # Breakdown by market category
    volume_by_category: dict[str, Decimal] = Field(default_factory=dict)
    
    # Breakdown by agent
    volume_by_agent: dict[str, Decimal] = Field(default_factory=dict)
    
    # Time period
    start_time: datetime = Field(default_factory=datetime.utcnow)
    end_time: datetime = Field(default_factory=datetime.utcnow)


class LeaderboardEntry(BaseModel):
    """Entry in builder leaderboard."""
    
    rank: int
    builder_code: str
    
    volume_24h: Decimal = Field(Decimal("0"))
    volume_7d: Decimal = Field(Decimal("0"))
    volume_30d: Decimal = Field(Decimal("0"))
    
    trade_count_24h: int = Field(0)
    
    # Movement
    rank_change_24h: int = Field(0)
    volume_change_pct: Decimal = Field(Decimal("0"))


class AgentPerformance(BaseModel):
    """Performance metrics for a single agent."""
    
    agent_id: str
    agent_type: str  # Shark, Spy, etc.
    
    # Volume
    total_volume: Decimal = Field(Decimal("0"))
    trade_count: int = Field(0)
    
    # P&L
    realized_pnl: Decimal = Field(Decimal("0"))
    win_rate: Decimal = Field(Decimal("0"))
    
    # Attribution contribution
    volume_attributed: Decimal = Field(Decimal("0"))
    revenue_generated: Decimal = Field(Decimal("0"))
    
    # Active markets
    active_positions: int = Field(0)


# =============================================================================
# ATTRIBUTION MANAGER
# =============================================================================

class BuilderAttributionManager:
    """
    Manages Builder Code attribution across platforms.
    
    Responsibilities:
    - Track all trades with builder attribution
    - Calculate volume metrics
    - Generate leaderboard data
    - Compute revenue share
    """
    
    def __init__(
        self,
        polymarket_code: str = "ECHELON",
        kalshi_code: str = "ECHELON",
        storage_backend: Optional[Any] = None
    ):
        self.polymarket_code = polymarket_code
        self.kalshi_code = kalshi_code
        self.storage = storage_backend
        
        # In-memory caches (would be replaced with Redis/DB in production)
        self._trades: list[TradeAttribution] = []
        self._metrics_cache: dict[str, VolumeMetrics] = {}
        self._agent_performance: dict[str, AgentPerformance] = {}
        
        # Configuration
        self.configs: dict[Platform, BuilderConfig] = {
            Platform.POLYMARKET: BuilderConfig(
                code=polymarket_code,
                platform=Platform.POLYMARKET,
                revenue_share_bps=100,  # 1% revenue share
                description="Echelon Protocol - Polymarket Builder"
            ),
            Platform.KALSHI: BuilderConfig(
                code=kalshi_code,
                platform=Platform.KALSHI,
                revenue_share_bps=50,  # 0.5% revenue share
                description="Echelon Protocol - Kalshi Builder"
            )
        }
    
    # =========================================================================
    # TRADE RECORDING
    # =========================================================================
    
    async def record_trade(self, trade: TradeAttribution) -> None:
        """Record a trade with builder attribution."""
        # Calculate revenue share
        config = self.configs.get(trade.platform)
        if config:
            trade.revenue_share = (
                trade.fee_collected * Decimal(config.revenue_share_bps) / Decimal(10000)
            )
        
        # Store trade
        self._trades.append(trade)
        
        # Update agent performance if applicable
        if trade.agent_id:
            await self._update_agent_performance(trade)
        
        # Invalidate metrics cache
        self._metrics_cache.clear()
        
        # Persist to storage if available
        if self.storage:
            await self.storage.save_trade(trade)
    
    async def record_polymarket_trade(
        self,
        trade_id: str,
        market_id: str,
        side: str,
        size: Decimal,
        price: Decimal,
        agent_id: Optional[str] = None,
        user_address: Optional[str] = None,
        fee_collected: Decimal = Decimal("0")
    ) -> TradeAttribution:
        """Convenience method for recording Polymarket trades."""
        volume_usd = size * price
        
        trade = TradeAttribution(
            trade_id=trade_id,
            platform=Platform.POLYMARKET,
            market_id=market_id,
            builder_code=self.polymarket_code,
            side=side,
            size=size,
            price=price,
            volume_usd=volume_usd,
            agent_id=agent_id,
            user_address=user_address,
            fee_collected=fee_collected
        )
        
        await self.record_trade(trade)
        return trade
    
    async def record_kalshi_trade(
        self,
        trade_id: str,
        ticker: str,
        action: str,
        side: str,
        count: int,
        price_cents: int,
        agent_id: Optional[str] = None,
        user_address: Optional[str] = None,
        fee_collected: Decimal = Decimal("0")
    ) -> TradeAttribution:
        """Convenience method for recording Kalshi trades."""
        # Kalshi prices are in cents (1-99)
        price = Decimal(price_cents) / Decimal(100)
        size = Decimal(count)
        volume_usd = size * price
        
        trade = TradeAttribution(
            trade_id=trade_id,
            platform=Platform.KALSHI,
            market_id=ticker,
            builder_code=self.kalshi_code,
            side=f"{action}_{side}",
            size=size,
            price=price,
            volume_usd=volume_usd,
            agent_id=agent_id,
            user_address=user_address,
            fee_collected=fee_collected
        )
        
        await self.record_trade(trade)
        return trade
    
    async def _update_agent_performance(self, trade: TradeAttribution) -> None:
        """Update agent performance metrics."""
        agent_id = trade.agent_id
        if not agent_id:
            return
        
        if agent_id not in self._agent_performance:
            self._agent_performance[agent_id] = AgentPerformance(
                agent_id=agent_id,
                agent_type="unknown"
            )
        
        perf = self._agent_performance[agent_id]
        perf.total_volume += trade.volume_usd
        perf.trade_count += 1
        perf.volume_attributed += trade.volume_usd
        perf.revenue_generated += trade.revenue_share
    
    # =========================================================================
    # METRICS CALCULATION
    # =========================================================================
    
    async def get_volume_metrics(
        self,
        platform: Optional[Platform] = None,
        time_range: TimeRange = TimeRange.DAY
    ) -> VolumeMetrics:
        """Get volume metrics for a time range."""
        cache_key = f"{platform}:{time_range}"
        
        if cache_key in self._metrics_cache:
            return self._metrics_cache[cache_key]
        
        # Calculate time bounds
        now = datetime.utcnow()
        if time_range == TimeRange.HOUR:
            start_time = now - timedelta(hours=1)
        elif time_range == TimeRange.DAY:
            start_time = now - timedelta(days=1)
        elif time_range == TimeRange.WEEK:
            start_time = now - timedelta(weeks=1)
        elif time_range == TimeRange.MONTH:
            start_time = now - timedelta(days=30)
        else:
            start_time = datetime.min
        
        # Filter trades
        filtered_trades = [
            t for t in self._trades
            if t.timestamp >= start_time
            and (platform is None or t.platform == platform)
        ]
        
        # Calculate metrics
        total_volume = sum(t.volume_usd for t in filtered_trades)
        total_fees = sum(t.fee_collected for t in filtered_trades)
        revenue_share = sum(t.revenue_share for t in filtered_trades)
        
        unique_users = len(set(t.user_address for t in filtered_trades if t.user_address))
        unique_markets = len(set(t.market_id for t in filtered_trades))
        
        # Volume by agent
        volume_by_agent: dict[str, Decimal] = {}
        for trade in filtered_trades:
            if trade.agent_id:
                volume_by_agent[trade.agent_id] = (
                    volume_by_agent.get(trade.agent_id, Decimal("0")) + trade.volume_usd
                )
        
        metrics = VolumeMetrics(
            platform=platform or Platform.POLYMARKET,
            time_range=time_range,
            total_volume_usd=total_volume,
            trade_count=len(filtered_trades),
            unique_users=unique_users,
            unique_markets=unique_markets,
            total_fees=total_fees,
            revenue_share=revenue_share,
            volume_by_agent=volume_by_agent,
            start_time=start_time,
            end_time=now
        )
        
        self._metrics_cache[cache_key] = metrics
        return metrics
    
    async def get_combined_metrics(
        self,
        time_range: TimeRange = TimeRange.DAY
    ) -> dict[str, VolumeMetrics]:
        """Get metrics for all platforms combined."""
        return {
            "polymarket": await self.get_volume_metrics(Platform.POLYMARKET, time_range),
            "kalshi": await self.get_volume_metrics(Platform.KALSHI, time_range),
            "combined": await self.get_volume_metrics(None, time_range)
        }
    
    async def get_agent_leaderboard(
        self,
        time_range: TimeRange = TimeRange.DAY,
        limit: int = 10
    ) -> list[AgentPerformance]:
        """Get top agents by volume."""
        # Recalculate from trades for accuracy
        agent_volumes: dict[str, Decimal] = {}
        agent_trades: dict[str, int] = {}
        
        now = datetime.utcnow()
        if time_range == TimeRange.DAY:
            start_time = now - timedelta(days=1)
        elif time_range == TimeRange.WEEK:
            start_time = now - timedelta(weeks=1)
        else:
            start_time = datetime.min
        
        for trade in self._trades:
            if trade.timestamp >= start_time and trade.agent_id:
                agent_volumes[trade.agent_id] = (
                    agent_volumes.get(trade.agent_id, Decimal("0")) + trade.volume_usd
                )
                agent_trades[trade.agent_id] = agent_trades.get(trade.agent_id, 0) + 1
        
        # Sort by volume
        sorted_agents = sorted(
            agent_volumes.items(),
            key=lambda x: x[1],
            reverse=True
        )[:limit]
        
        results = []
        for agent_id, volume in sorted_agents:
            perf = self._agent_performance.get(agent_id, AgentPerformance(
                agent_id=agent_id,
                agent_type="unknown"
            ))
            perf.total_volume = volume
            perf.trade_count = agent_trades.get(agent_id, 0)
            results.append(perf)
        
        return results
    
    # =========================================================================
    # BUILDER LEADERBOARD
    # =========================================================================
    
    async def get_builder_position(
        self,
        platform: Platform
    ) -> Optional[LeaderboardEntry]:
        """
        Get our position on the builder leaderboard.
        
        Note: This would typically call the platform's API to get
        actual leaderboard data. Here we return estimated position.
        """
        metrics_24h = await self.get_volume_metrics(platform, TimeRange.DAY)
        metrics_7d = await self.get_volume_metrics(platform, TimeRange.WEEK)
        metrics_30d = await self.get_volume_metrics(platform, TimeRange.MONTH)
        
        config = self.configs.get(platform)
        
        return LeaderboardEntry(
            rank=0,  # Unknown without API call
            builder_code=config.code if config else "",
            volume_24h=metrics_24h.total_volume_usd,
            volume_7d=metrics_7d.total_volume_usd,
            volume_30d=metrics_30d.total_volume_usd,
            trade_count_24h=metrics_24h.trade_count
        )
    
    # =========================================================================
    # REVENUE CALCULATIONS
    # =========================================================================
    
    async def calculate_revenue_share(
        self,
        platform: Platform,
        time_range: TimeRange = TimeRange.MONTH
    ) -> dict[str, Decimal]:
        """Calculate revenue share for a period."""
        metrics = await self.get_volume_metrics(platform, time_range)
        config = self.configs.get(platform)
        
        return {
            "total_volume": metrics.total_volume_usd,
            "total_fees": metrics.total_fees,
            "revenue_share_bps": Decimal(config.revenue_share_bps if config else 0),
            "revenue_earned": metrics.revenue_share,
            "trade_count": Decimal(metrics.trade_count)
        }
    
    # =========================================================================
    # EXPORT & REPORTING
    # =========================================================================
    
    async def export_trades(
        self,
        platform: Optional[Platform] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> list[dict]:
        """Export trades for reporting."""
        filtered = self._trades
        
        if platform:
            filtered = [t for t in filtered if t.platform == platform]
        
        if start_date:
            filtered = [t for t in filtered if t.timestamp >= start_date]
        
        if end_date:
            filtered = [t for t in filtered if t.timestamp <= end_date]
        
        return [t.model_dump() for t in filtered]
    
    async def generate_report(
        self,
        time_range: TimeRange = TimeRange.MONTH
    ) -> dict:
        """Generate comprehensive attribution report."""
        combined = await self.get_combined_metrics(time_range)
        
        polymarket_position = await self.get_builder_position(Platform.POLYMARKET)
        kalshi_position = await self.get_builder_position(Platform.KALSHI)
        
        agent_leaderboard = await self.get_agent_leaderboard(time_range)
        
        polymarket_revenue = await self.calculate_revenue_share(Platform.POLYMARKET, time_range)
        kalshi_revenue = await self.calculate_revenue_share(Platform.KALSHI, time_range)
        
        return {
            "time_range": time_range.value,
            "generated_at": datetime.utcnow().isoformat(),
            "metrics": {
                "polymarket": combined["polymarket"].model_dump(),
                "kalshi": combined["kalshi"].model_dump(),
                "combined": combined["combined"].model_dump()
            },
            "leaderboard_positions": {
                "polymarket": polymarket_position.model_dump() if polymarket_position else None,
                "kalshi": kalshi_position.model_dump() if kalshi_position else None
            },
            "top_agents": [a.model_dump() for a in agent_leaderboard],
            "revenue": {
                "polymarket": {k: str(v) for k, v in polymarket_revenue.items()},
                "kalshi": {k: str(v) for k, v in kalshi_revenue.items()}
            }
        }


# =============================================================================
# USAGE EXAMPLE
# =============================================================================

async def example_usage():
    """Example usage of attribution manager."""
    
    manager = BuilderAttributionManager(
        polymarket_code="ECHELON",
        kalshi_code="ECHELON"
    )
    
    # Record some trades
    await manager.record_polymarket_trade(
        trade_id="pm_001",
        market_id="0x123abc",
        side="BUY",
        size=Decimal("100"),
        price=Decimal("0.65"),
        agent_id="SHARK_001",
        fee_collected=Decimal("0.65")
    )
    
    await manager.record_kalshi_trade(
        trade_id="kl_001",
        ticker="INXD-23DEC31-T4500",
        action="buy",
        side="yes",
        count=50,
        price_cents=45,
        agent_id="SPY_001",
        fee_collected=Decimal("0.23")
    )
    
    # Get metrics
    metrics = await manager.get_combined_metrics(TimeRange.DAY)
    print(f"24h Volume: ${metrics['combined'].total_volume_usd}")
    
    # Generate report
    report = await manager.generate_report(TimeRange.DAY)
    print(json.dumps(report, indent=2, default=str))


if __name__ == "__main__":
    asyncio.run(example_usage())
