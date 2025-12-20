"""
Polymarket CLOB API Client

Public endpoints (no auth required):
- GET /markets - List all markets
- GET /book - Get orderbook
- GET /trades - Get recent trades

Authenticated endpoints (need API key):
- POST /order - Place order
- GET /orders - List your orders
"""

import os
import logging
from typing import Optional
from datetime import datetime
import httpx

logger = logging.getLogger('echelon.polymarket')


class PolymarketConfig:
    """Polymarket API configuration."""
    
    # Public endpoints (no auth)
    CLOB_BASE_URL = "https://clob.polymarket.com"
    GAMMA_BASE_URL = "https://gamma-api.polymarket.com"
    
    # Rate limits
    RATE_LIMIT_REQUESTS = 100
    RATE_LIMIT_WINDOW = 60  # seconds


class PolymarketClient:
    """
    Polymarket API client.
    
    Usage:
        client = PolymarketClient()
        
        # Public (no auth)
        markets = await client.get_markets()
        orderbook = await client.get_orderbook(token_id)
        
        # Authenticated
        client = PolymarketClient(api_key="your-key", api_secret="your-secret")
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
    ):
        self.api_key = api_key or os.getenv("POLYMARKET_API_KEY")
        self.api_secret = api_secret or os.getenv("POLYMARKET_API_SECRET")
        self.clob_url = PolymarketConfig.CLOB_BASE_URL
        self.gamma_url = PolymarketConfig.GAMMA_BASE_URL
        
        # HTTP client with timeout
        self._client = httpx.AsyncClient(timeout=30.0)
    
    async def close(self):
        """Close the HTTP client."""
        await self._client.aclose()
    
    # =========================================================================
    # PUBLIC ENDPOINTS (No Authentication Required)
    # =========================================================================
    
    async def get_markets(
        self,
        next_cursor: Optional[str] = None,
    ) -> dict:
        """
        Get all active markets.
        
        Returns:
            {
                "data": [...markets...],
                "next_cursor": "..."
            }
        """
        params = {}
        if next_cursor:
            params["next_cursor"] = next_cursor
        
        response = await self._client.get(
            f"{self.clob_url}/markets",
            params=params,
        )
        response.raise_for_status()
        return response.json()
    
    async def get_market(self, condition_id: str) -> dict:
        """
        Get a specific market by condition ID.
        
        Args:
            condition_id: The market's condition ID (not token ID)
        
        Returns:
            Market object
        """
        response = await self._client.get(
            f"{self.clob_url}/markets/{condition_id}",
        )
        response.raise_for_status()
        return response.json()
    
    async def get_orderbook(
        self,
        token_id: str,
    ) -> dict:
        """
        Get orderbook for a token.
        
        Args:
            token_id: The YES or NO token ID
        
        Returns:
            {
                "bids": [...],
                "asks": [...],
                "hash": "...",
                "timestamp": "..."
            }
        """
        response = await self._client.get(
            f"{self.clob_url}/book",
            params={"token_id": token_id},
        )
        response.raise_for_status()
        return response.json()
    
    async def get_trades(
        self,
        market: Optional[str] = None,
        maker: Optional[str] = None,
        limit: int = 100,
    ) -> list:
        """
        Get recent trades.
        
        Args:
            market: Filter by market condition ID
            maker: Filter by maker address
            limit: Max trades to return
        
        Returns:
            List of trade objects
        """
        params = {"limit": limit}
        if market:
            params["market"] = market
        if maker:
            params["maker"] = maker
        
        response = await self._client.get(
            f"{self.clob_url}/trades",
            params=params,
        )
        response.raise_for_status()
        return response.json()
    
    async def get_midpoint(self, token_id: str) -> float:
        """
        Get midpoint price for a token.
        
        Args:
            token_id: The token ID
        
        Returns:
            Midpoint price as decimal (0.0 - 1.0)
        """
        response = await self._client.get(
            f"{self.clob_url}/midpoint",
            params={"token_id": token_id},
        )
        response.raise_for_status()
        data = response.json()
        return float(data.get("mid", 0.5))
    
    async def get_price(self, token_id: str, side: str = "BUY") -> float:
        """
        Get best price for a token.
        
        Args:
            token_id: The token ID
            side: "BUY" or "SELL"
        
        Returns:
            Best price as decimal
        """
        response = await self._client.get(
            f"{self.clob_url}/price",
            params={"token_id": token_id, "side": side},
        )
        response.raise_for_status()
        data = response.json()
        return float(data.get("price", 0.5))
    
    # =========================================================================
    # GAMMA API (Event Metadata)
    # =========================================================================
    
    async def get_events(
        self,
        active: bool = True,
        closed: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> list:
        """
        Get events from Gamma API.
        
        Returns list of event objects with markets.
        """
        params = {
            "active": str(active).lower(),
            "closed": str(closed).lower(),
            "limit": limit,
            "offset": offset,
        }
        
        response = await self._client.get(
            f"{self.gamma_url}/events",
            params=params,
        )
        response.raise_for_status()
        return response.json()
    
    async def get_event(self, event_slug: str) -> dict:
        """
        Get a specific event by slug.
        
        Args:
            event_slug: The event's URL slug
        
        Returns:
            Event object with markets
        """
        response = await self._client.get(
            f"{self.gamma_url}/events/{event_slug}",
        )
        response.raise_for_status()
        return response.json()
    
    # =========================================================================
    # HELPER METHODS
    # =========================================================================
    
    async def get_trending_markets(self, limit: int = 10) -> list:
        """
        Get trending markets by volume.
        
        Returns list of market objects sorted by 24h volume.
        """
        markets_response = await self.get_markets()
        markets = markets_response.get("data", [])
        
        # Sort by volume (descending)
        sorted_markets = sorted(
            markets,
            key=lambda m: float(m.get("volume_24hr", 0) or 0),
            reverse=True,
        )
        
        return sorted_markets[:limit]
    
    async def get_market_with_prices(self, condition_id: str) -> dict:
        """
        Get market with current prices.
        
        Returns market object enriched with YES/NO prices.
        """
        market = await self.get_market(condition_id)
        
        # Get token IDs
        tokens = market.get("tokens", [])
        yes_token = next((t for t in tokens if t.get("outcome") == "Yes"), None)
        no_token = next((t for t in tokens if t.get("outcome") == "No"), None)
        
        # Get prices
        if yes_token:
            market["yes_price"] = await self.get_midpoint(yes_token["token_id"])
        if no_token:
            market["no_price"] = await self.get_midpoint(no_token["token_id"])
        
        return market


# Convenience function
async def get_polymarket_client() -> PolymarketClient:
    """Get a Polymarket client instance."""
    return PolymarketClient()
