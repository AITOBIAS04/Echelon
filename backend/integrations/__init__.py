"""
Echelon Platform Integrations
=============================

Unified interface for Polymarket and Kalshi integration.

Modules:
- polymarket_client: Polymarket CLOB API client
- kalshi_client: Kalshi DFlow API client  
- builder_attribution: Builder Code tracking and metrics
- platform_manager: Unified multi-platform manager
"""

from .polymarket_client import (
    PolymarketClient,
    PolymarketConfig,
    get_polymarket_client,
)
# Alias for backward compatibility
PolymarketCLOBClient = PolymarketClient

from .kalshi_client import (
    KalshiClient,
    KalshiMarket,
    KalshiEvent,
    KalshiOrder,
    KalshiConfig,
    KalshiAPIError,
    KalshiWebSocket,
    OrderSide as KalshiOrderSide,
    OrderAction as KalshiOrderAction,
    OrderType as KalshiOrderType,
    OrderStatus as KalshiOrderStatus,
)

from .builder_attribution import (
    BuilderAttributionManager,
    BuilderConfig,
    TradeAttribution,
    VolumeMetrics,
    LeaderboardEntry,
    AgentPerformance,
    Platform,
    TimeRange,
)

__all__ = [
    # Polymarket
    "PolymarketClient",
    "PolymarketCLOBClient",  # Alias
    "PolymarketConfig",
    "get_polymarket_client",
    
    # Kalshi
    "KalshiClient",
    "KalshiMarket",
    "KalshiEvent",
    "KalshiOrder",
    "KalshiConfig",
    "KalshiAPIError",
    "KalshiWebSocket",
    "KalshiOrderSide",
    "KalshiOrderAction",
    "KalshiOrderType",
    "KalshiOrderStatus",
    
    # Attribution
    "BuilderAttributionManager",
    "BuilderConfig",
    "TradeAttribution",
    "VolumeMetrics",
    "LeaderboardEntry",
    "AgentPerformance",
    "Platform",
    "TimeRange",
]
