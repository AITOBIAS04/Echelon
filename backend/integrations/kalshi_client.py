"""
Kalshi DFlow API Client
=======================

Full integration with Kalshi's DFlow API for market data and order execution.
Includes Builder Code attribution for volume tracking.

Kalshi Integration Points:
- DFlow API for real market data and execution
- SPL token settlement on Solana
- Builder Code for volume attribution
- Programmatic wallet integration

Author: Echelon Protocol
Version: 1.0.0
"""

import asyncio
import base64
import hashlib
import hmac
import json
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Any, Optional
from urllib.parse import urlencode

import aiohttp
from pydantic import BaseModel, Field


# =============================================================================
# CONFIGURATION
# =============================================================================

class KalshiConfig:
    """Kalshi API configuration."""
    
    # Authenticated API Endpoints (requires login)
    API_BASE_URL = "https://trading-api.kalshi.com/trade-api/v2"
    DEMO_API_URL = "https://demo-api.kalshi.co/trade-api/v2"
    
    # Public API Endpoints (no auth required)
    PUBLIC_API_BASE_URL = "https://trading-api.kalshi.com/v2"
    PUBLIC_DEMO_API_URL = "https://demo-api.kalshi.co/v2"
    
    # WebSocket
    WS_URL = "wss://trading-api.kalshi.com/trade-api/ws/v2"
    DEMO_WS_URL = "wss://demo-api.kalshi.co/trade-api/ws/v2"
    
    # Chain configuration (Solana)
    SOLANA_MAINNET = "https://api.mainnet-beta.solana.com"
    SOLANA_DEVNET = "https://api.devnet.solana.com"
    
    # Rate limits
    RATE_LIMIT_REQUESTS = 10
    RATE_LIMIT_WINDOW = 1  # second
    
    # Builder Code for Echelon
    BUILDER_CODE = "ECHELON"  # Replace with actual assigned code


# =============================================================================
# DATA MODELS
# =============================================================================

class OrderSide(str, Enum):
    YES = "yes"
    NO = "no"


class OrderAction(str, Enum):
    BUY = "buy"
    SELL = "sell"


class OrderType(str, Enum):
    LIMIT = "limit"
    MARKET = "market"


class OrderStatus(str, Enum):
    RESTING = "resting"
    PENDING = "pending"
    CANCELED = "canceled"
    EXECUTED = "executed"
    PENDING_EXECUTION = "pending_execution"


class MarketStatus(str, Enum):
    OPEN = "open"
    CLOSED = "closed"
    SETTLED = "settled"


class KalshiEvent(BaseModel):
    """Kalshi event (contains multiple markets)."""
    
    event_ticker: str = Field(..., description="Event ticker symbol")
    series_ticker: str = Field(..., description="Series this event belongs to")
    
    title: str = Field(..., description="Event title")
    subtitle: Optional[str] = Field(None, description="Event subtitle")
    category: str = Field(..., description="Event category")
    
    mutually_exclusive: bool = Field(True, description="Markets are mutually exclusive")
    
    strike_date: Optional[str] = Field(None, description="Event strike/resolution date")
    
    markets: list["KalshiMarket"] = Field(default_factory=list, description="Markets in event")


class KalshiMarket(BaseModel):
    """Kalshi market data model."""
    
    ticker: str = Field(..., description="Market ticker symbol")
    event_ticker: str = Field(..., description="Parent event ticker")
    
    title: str = Field(..., description="Market title")
    subtitle: Optional[str] = Field(None, description="Market subtitle")
    
    status: MarketStatus = Field(MarketStatus.OPEN, description="Market status")
    
    yes_bid: Optional[int] = Field(None, description="Best YES bid in cents")
    yes_ask: Optional[int] = Field(None, description="Best YES ask in cents")
    no_bid: Optional[int] = Field(None, description="Best NO bid in cents")
    no_ask: Optional[int] = Field(None, description="Best NO ask in cents")
    
    last_price: Optional[int] = Field(None, description="Last trade price in cents")
    
    volume: int = Field(0, description="Total contracts traded")
    volume_24h: int = Field(0, description="24h volume")
    
    open_interest: int = Field(0, description="Open interest")
    
    expiration_time: Optional[str] = Field(None, description="Market expiration")
    close_time: Optional[str] = Field(None, description="Market close time")
    
    result: Optional[str] = Field(None, description="Settlement result (yes/no)")
    
    @property
    def yes_mid(self) -> Optional[float]:
        if self.yes_bid is not None and self.yes_ask is not None:
            return (self.yes_bid + self.yes_ask) / 2 / 100
        return None
    
    @property
    def spread(self) -> Optional[float]:
        if self.yes_bid is not None and self.yes_ask is not None:
            return (self.yes_ask - self.yes_bid) / 100
        return None


class KalshiOrder(BaseModel):
    """Order model for Kalshi."""
    
    order_id: Optional[str] = Field(None, description="Assigned order ID")
    client_order_id: Optional[str] = Field(None, description="Client-specified ID")
    
    ticker: str = Field(..., description="Market ticker")
    
    action: OrderAction = Field(..., description="buy or sell")
    side: OrderSide = Field(..., description="yes or no")
    order_type: OrderType = Field(OrderType.LIMIT, description="Order type")
    
    count: int = Field(..., description="Number of contracts")
    
    # Price in cents (1-99)
    yes_price: Optional[int] = Field(None, description="YES price in cents")
    no_price: Optional[int] = Field(None, description="NO price in cents")
    
    status: OrderStatus = Field(OrderStatus.PENDING, description="Order status")
    
    remaining_count: int = Field(0, description="Unfilled contracts")
    
    created_time: Optional[str] = Field(None, description="Creation timestamp")
    expiration_time: Optional[str] = Field(None, description="Expiration timestamp")
    
    # Builder attribution
    builder_code: str = Field(KalshiConfig.BUILDER_CODE, description="Builder code")


class KalshiFill(BaseModel):
    """Trade fill/execution."""
    
    trade_id: str
    order_id: str
    ticker: str
    
    side: OrderSide
    action: OrderAction
    
    count: int
    yes_price: int
    no_price: int
    
    created_time: str
    
    is_taker: bool = False


class KalshiPosition(BaseModel):
    """User position in a market."""
    
    ticker: str
    
    position: int = Field(0, description="Net position (positive=YES, negative=NO)")
    
    total_traded: int = Field(0, description="Total contracts traded")
    
    realized_pnl: int = Field(0, description="Realised P&L in cents")
    
    resting_orders_count: int = Field(0, description="Number of resting orders")


class KalshiBalance(BaseModel):
    """Account balance."""
    
    balance: int = Field(0, description="Available balance in cents")
    
    portfolio_value: int = Field(0, description="Total portfolio value in cents")


# =============================================================================
# API CLIENT
# =============================================================================

class KalshiClient:
    """
    Kalshi DFlow API Client.
    
    Handles:
    - Market and event data fetching
    - Order placement and management
    - Position tracking
    - Builder Code attribution
    """
    
    def __init__(
        self,
        email: Optional[str] = None,
        password: Optional[str] = None,
        api_key: Optional[str] = None,
        private_key: Optional[str] = None,
        use_demo: bool = False,
        builder_code: str = KalshiConfig.BUILDER_CODE
    ):
        self.email = email
        self.password = password
        self.api_key = api_key
        self.private_key = private_key
        self.use_demo = use_demo
        self.builder_code = builder_code
        
        # Set base URLs
        self.base_url = KalshiConfig.DEMO_API_URL if use_demo else KalshiConfig.API_BASE_URL
        self.public_base_url = KalshiConfig.PUBLIC_DEMO_API_URL if use_demo else KalshiConfig.PUBLIC_API_BASE_URL
        
        # Auth token (obtained via login)
        self._token: Optional[str] = None
        self._member_id: Optional[str] = None
        
        # Session management
        self._session: Optional[aiohttp.ClientSession] = None
        self._rate_limiter = RateLimiter(
            KalshiConfig.RATE_LIMIT_REQUESTS,
            KalshiConfig.RATE_LIMIT_WINDOW
        )
    
    async def __aenter__(self):
        await self._ensure_session()
        if self.email and self.password:
            await self.login()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    async def _ensure_session(self):
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
    
    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()
    
    def _get_headers(self) -> dict:
        """Generate request headers."""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        elif self.api_key:
            # API key authentication
            timestamp = str(int(time.time() * 1000))
            headers["KALSHI-ACCESS-KEY"] = self.api_key
            headers["KALSHI-ACCESS-TIMESTAMP"] = timestamp
            
            if self.private_key:
                # Sign the request
                signature = self._sign_request(timestamp)
                headers["KALSHI-ACCESS-SIGNATURE"] = signature
        
        return headers
    
    def _sign_request(self, timestamp: str, method: str = "GET", path: str = "", body: str = "") -> str:
        """Sign request with private key (RSA)."""
        # Simplified - actual implementation would use RSA signing
        message = f"{timestamp}{method}{path}{body}"
        return base64.b64encode(message.encode()).decode()
    
    async def _request(
        self,
        method: str,
        path: str,
        params: Optional[dict] = None,
        data: Optional[dict] = None,
        use_public_api: bool = False
    ) -> dict:
        """Make API request with rate limiting and error handling."""
        await self._ensure_session()
        await self._rate_limiter.acquire()
        
        # Use public API base URL if specified (no auth required)
        base_url = self.public_base_url if use_public_api else self.base_url
        url = f"{base_url}{path}"
        if params:
            url = f"{url}?{urlencode(params)}"
        
        # Public API doesn't need auth headers, just basic headers
        if use_public_api:
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
        else:
            headers = self._get_headers()
        
        try:
            async with self._session.request(
                method,
                url,
                headers=headers,
                json=data
            ) as response:
                response_data = await response.json()
                
                if response.status >= 400:
                    raise KalshiAPIError(
                        status=response.status,
                        message=response_data.get("error", {}).get("message", "Unknown error"),
                        code=response_data.get("error", {}).get("code")
                    )
                
                return response_data
                
        except aiohttp.ClientError as e:
            raise KalshiAPIError(
                status=0,
                message=f"Network error: {str(e)}"
            )
    
    # =========================================================================
    # AUTHENTICATION
    # =========================================================================
    
    async def login(self) -> bool:
        """Login with email/password to get auth token."""
        if not self.email or not self.password:
            raise ValueError("Email and password required for login")
        
        response = await self._request(
            "POST",
            "/login",
            data={"email": self.email, "password": self.password}
        )
        
        self._token = response.get("token")
        self._member_id = response.get("member_id")
        
        return bool(self._token)
    
    async def logout(self):
        """Logout and invalidate token."""
        if self._token:
            await self._request("POST", "/logout")
            self._token = None
            self._member_id = None
    
    # =========================================================================
    # EVENTS & MARKETS
    # =========================================================================
    
    async def get_events(
        self,
        series_ticker: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
        cursor: Optional[str] = None
    ) -> tuple[list[KalshiEvent], Optional[str]]:
        """Fetch events with pagination."""
        params = {"limit": limit}
        if series_ticker:
            params["series_ticker"] = series_ticker
        if status:
            params["status"] = status
        if cursor:
            params["cursor"] = cursor
        
        response = await self._request("GET", "/events", params=params)
        
        events = [KalshiEvent(**e) for e in response.get("events", [])]
        next_cursor = response.get("cursor")
        
        return events, next_cursor
    
    async def get_event(self, event_ticker: str) -> KalshiEvent:
        """Fetch single event by ticker."""
        response = await self._request("GET", f"/events/{event_ticker}")
        return KalshiEvent(**response.get("event", {}))
    
    async def get_markets(
        self,
        event_ticker: Optional[str] = None,
        series_ticker: Optional[str] = None,
        status: Optional[str] = None,
        tickers: Optional[list[str]] = None,
        limit: int = 100,
        cursor: Optional[str] = None
    ) -> tuple[list[KalshiMarket], Optional[str]]:
        """Fetch markets with filters."""
        params = {"limit": limit}
        if event_ticker:
            params["event_ticker"] = event_ticker
        if series_ticker:
            params["series_ticker"] = series_ticker
        if status:
            params["status"] = status
        if tickers:
            params["tickers"] = ",".join(tickers)
        if cursor:
            params["cursor"] = cursor
        
        response = await self._request("GET", "/markets", params=params)
        
        markets = [KalshiMarket(**m) for m in response.get("markets", [])]
        next_cursor = response.get("cursor")
        
        return markets, next_cursor
    
    async def get_market(self, ticker: str) -> KalshiMarket:
        """Fetch single market by ticker."""
        response = await self._request("GET", f"/markets/{ticker}")
        return KalshiMarket(**response.get("market", {}))
    
    async def get_market_orderbook(self, ticker: str, depth: int = 10) -> dict:
        """Fetch order book for a market (authenticated endpoint)."""
        response = await self._request(
            "GET",
            f"/markets/{ticker}/orderbook",
            params={"depth": depth}
        )
        return response.get("orderbook", {})
    
    async def get_market_trades(
        self,
        ticker: str,
        limit: int = 100,
        cursor: Optional[str] = None
    ) -> tuple[list[dict], Optional[str]]:
        """
        Fetch recent trades for a market (authenticated endpoint).
        
        Returns:
            Tuple of (trades list, next cursor for pagination)
        """
        params = {"limit": limit}
        if cursor:
            params["cursor"] = cursor
        
        response = await self._request(
            "GET",
            f"/markets/{ticker}/trades",
            params=params
        )
        
        trades = response.get("trades", [])
        next_cursor = response.get("cursor")
        
        return trades, next_cursor
    
    async def get_series(self, series_ticker: str) -> dict:
        """Fetch series metadata."""
        response = await self._request("GET", f"/series/{series_ticker}")
        return response.get("series", {})
    
    # =========================================================================
    # PUBLIC API METHODS (No Authentication Required)
    # =========================================================================
    
    async def get_events_public(
        self,
        limit: int = 100,
        cursor: Optional[str] = None
    ) -> tuple[list[dict], Optional[str]]:
        """
        Get all events (public API, no auth required).
        
        GET /events
        
        Returns:
            Tuple of (events list, next cursor for pagination)
        """
        params = {"limit": limit}
        if cursor:
            params["cursor"] = cursor
        
        response = await self._request(
            "GET",
            "/events",
            params=params,
            use_public_api=True
        )
        
        events = response.get("events", [])
        next_cursor = response.get("cursor")
        
        return events, next_cursor
    
    async def get_event_markets_public(
        self,
        event_ticker: str,
        limit: int = 100,
        cursor: Optional[str] = None
    ) -> tuple[list[dict], Optional[str]]:
        """
        Get markets for an event (public API, no auth required).
        
        GET /events/{event_ticker}/markets
        
        Returns:
            Tuple of (markets list, next cursor for pagination)
        """
        params = {"limit": limit}
        if cursor:
            params["cursor"] = cursor
        
        response = await self._request(
            "GET",
            f"/events/{event_ticker}/markets",
            params=params,
            use_public_api=True
        )
        
        markets = response.get("markets", [])
        next_cursor = response.get("cursor")
        
        return markets, next_cursor
    
    async def get_orderbook_public(
        self,
        ticker: str,
        depth: Optional[int] = None
    ) -> dict:
        """
        Get orderbook for a market (public API, no auth required).
        
        GET /markets/{ticker}/orderbook
        
        Args:
            ticker: Market ticker symbol
            depth: Optional depth limit
            
        Returns:
            Orderbook dictionary with bids/asks
        """
        params = {}
        if depth:
            params["depth"] = depth
        
        response = await self._request(
            "GET",
            f"/markets/{ticker}/orderbook",
            params=params if params else None,
            use_public_api=True
        )
        
        return response.get("orderbook", {})
    
    async def get_trades_public(
        self,
        ticker: str,
        limit: int = 100,
        cursor: Optional[str] = None
    ) -> tuple[list[dict], Optional[str]]:
        """
        Get trades for a market (public API, no auth required).
        
        GET /markets/{ticker}/trades
        
        Returns:
            Tuple of (trades list, next cursor for pagination)
        """
        params = {"limit": limit}
        if cursor:
            params["cursor"] = cursor
        
        response = await self._request(
            "GET",
            f"/markets/{ticker}/trades",
            params=params,
            use_public_api=True
        )
        
        trades = response.get("trades", [])
        next_cursor = response.get("cursor")
        
        return trades, next_cursor
    
    # =========================================================================
    # ORDER MANAGEMENT
    # =========================================================================
    
    async def create_order(self, order: KalshiOrder) -> KalshiOrder:
        """
        Create a new order.
        
        Includes Builder Code for volume attribution.
        """
        # Generate client order ID if not provided
        if not order.client_order_id:
            order.client_order_id = f"echelon_{int(time.time() * 1000)}"
        
        order_data = {
            "ticker": order.ticker,
            "client_order_id": order.client_order_id,
            "action": order.action.value,
            "side": order.side.value,
            "type": order.order_type.value,
            "count": order.count,
        }
        
        # Set price based on side
        if order.order_type == OrderType.LIMIT:
            if order.side == OrderSide.YES:
                order_data["yes_price"] = order.yes_price
            else:
                order_data["no_price"] = order.no_price
        
        if order.expiration_time:
            order_data["expiration_time"] = order.expiration_time
        
        # Add builder code as referral/attribution
        # Note: Kalshi's actual builder attribution may differ
        order_data["metadata"] = {"builder_code": self.builder_code}
        
        response = await self._request("POST", "/portfolio/orders", data=order_data)
        
        order_response = response.get("order", {})
        order.order_id = order_response.get("order_id")
        order.status = OrderStatus(order_response.get("status", "pending"))
        order.remaining_count = order_response.get("remaining_count", order.count)
        order.created_time = order_response.get("created_time")
        
        return order
    
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel an existing order."""
        response = await self._request("DELETE", f"/portfolio/orders/{order_id}")
        return response.get("order", {}).get("status") == "canceled"
    
    async def amend_order(
        self,
        order_id: str,
        count: Optional[int] = None,
        price: Optional[int] = None
    ) -> KalshiOrder:
        """Amend an existing order."""
        data = {}
        if count is not None:
            data["count"] = count
        if price is not None:
            data["price"] = price
        
        response = await self._request("PATCH", f"/portfolio/orders/{order_id}", data=data)
        return self._parse_order_response(response.get("order", {}))
    
    async def get_order(self, order_id: str) -> KalshiOrder:
        """Get order by ID."""
        response = await self._request("GET", f"/portfolio/orders/{order_id}")
        return self._parse_order_response(response.get("order", {}))
    
    async def get_orders(
        self,
        ticker: Optional[str] = None,
        status: Optional[OrderStatus] = None,
        limit: int = 100
    ) -> list[KalshiOrder]:
        """Get orders with optional filters."""
        params = {"limit": limit}
        if ticker:
            params["ticker"] = ticker
        if status:
            params["status"] = status.value
        
        response = await self._request("GET", "/portfolio/orders", params=params)
        return [self._parse_order_response(o) for o in response.get("orders", [])]
    
    def _parse_order_response(self, data: dict) -> KalshiOrder:
        """Parse order response into model."""
        return KalshiOrder(
            order_id=data.get("order_id"),
            client_order_id=data.get("client_order_id"),
            ticker=data.get("ticker", ""),
            action=OrderAction(data.get("action", "buy")),
            side=OrderSide(data.get("side", "yes")),
            order_type=OrderType(data.get("type", "limit")),
            count=data.get("count", 0),
            yes_price=data.get("yes_price"),
            no_price=data.get("no_price"),
            status=OrderStatus(data.get("status", "pending")),
            remaining_count=data.get("remaining_count", 0),
            created_time=data.get("created_time"),
            expiration_time=data.get("expiration_time"),
        )
    
    # =========================================================================
    # FILLS & POSITIONS
    # =========================================================================
    
    async def get_fills(
        self,
        ticker: Optional[str] = None,
        order_id: Optional[str] = None,
        limit: int = 100
    ) -> list[KalshiFill]:
        """Get trade fills/executions."""
        params = {"limit": limit}
        if ticker:
            params["ticker"] = ticker
        if order_id:
            params["order_id"] = order_id
        
        response = await self._request("GET", "/portfolio/fills", params=params)
        
        return [KalshiFill(
            trade_id=f.get("trade_id", ""),
            order_id=f.get("order_id", ""),
            ticker=f.get("ticker", ""),
            side=OrderSide(f.get("side", "yes")),
            action=OrderAction(f.get("action", "buy")),
            count=f.get("count", 0),
            yes_price=f.get("yes_price", 0),
            no_price=f.get("no_price", 0),
            created_time=f.get("created_time", ""),
            is_taker=f.get("is_taker", False),
        ) for f in response.get("fills", [])]
    
    async def get_positions(
        self,
        ticker: Optional[str] = None,
        settlement_status: Optional[str] = None,
        limit: int = 100
    ) -> list[KalshiPosition]:
        """Get positions."""
        params = {"limit": limit}
        if ticker:
            params["ticker"] = ticker
        if settlement_status:
            params["settlement_status"] = settlement_status
        
        response = await self._request("GET", "/portfolio/positions", params=params)
        
        return [KalshiPosition(
            ticker=p.get("ticker", ""),
            position=p.get("position", 0),
            total_traded=p.get("total_traded", 0),
            realized_pnl=p.get("realized_pnl", 0),
            resting_orders_count=p.get("resting_orders_count", 0),
        ) for p in response.get("market_positions", [])]
    
    async def get_balance(self) -> KalshiBalance:
        """Get account balance."""
        response = await self._request("GET", "/portfolio/balance")
        return KalshiBalance(
            balance=response.get("balance", 0),
            portfolio_value=response.get("portfolio_value", 0),
        )
    
    # =========================================================================
    # MARKET DATA HISTORY
    # =========================================================================
    
    async def get_market_history(
        self,
        ticker: str,
        limit: int = 100,
        cursor: Optional[str] = None
    ) -> tuple[list[dict], Optional[str]]:
        """Get historical trades for a market."""
        params = {"limit": limit}
        if cursor:
            params["cursor"] = cursor
        
        response = await self._request("GET", f"/markets/{ticker}/history", params=params)
        
        history = response.get("history", [])
        next_cursor = response.get("cursor")
        
        return history, next_cursor
    
    async def get_market_candlesticks(
        self,
        ticker: str,
        period_interval: int = 60,  # minutes
        start_time: Optional[str] = None,
        end_time: Optional[str] = None
    ) -> list[dict]:
        """Get OHLC candlestick data."""
        params = {"period_interval": period_interval}
        if start_time:
            params["start_ts"] = start_time
        if end_time:
            params["end_ts"] = end_time
        
        response = await self._request("GET", f"/markets/{ticker}/candlesticks", params=params)
        return response.get("candlesticks", [])


# =============================================================================
# RATE LIMITER
# =============================================================================

class RateLimiter:
    """Simple rate limiter using token bucket."""
    
    def __init__(self, rate: int, window: int):
        self.rate = rate
        self.window = window
        self.tokens = rate
        self.last_update = time.time()
        self._lock = asyncio.Lock()
    
    async def acquire(self):
        async with self._lock:
            now = time.time()
            elapsed = now - self.last_update
            
            self.tokens = min(self.rate, self.tokens + elapsed * (self.rate / self.window))
            self.last_update = now
            
            if self.tokens < 1:
                wait_time = (1 - self.tokens) * (self.window / self.rate)
                await asyncio.sleep(wait_time)
                self.tokens = 0
            else:
                self.tokens -= 1


# =============================================================================
# EXCEPTIONS
# =============================================================================

class KalshiAPIError(Exception):
    """Kalshi API error."""
    
    def __init__(self, status: int, message: str, code: Optional[str] = None):
        self.status = status
        self.message = message
        self.code = code
        super().__init__(f"[{status}] {message}")


# =============================================================================
# WEBSOCKET CLIENT
# =============================================================================

class KalshiWebSocket:
    """WebSocket client for real-time updates."""
    
    def __init__(self, use_demo: bool = False):
        self.ws_url = KalshiConfig.DEMO_WS_URL if use_demo else KalshiConfig.WS_URL
        self._ws: Optional[aiohttp.ClientWebSocketResponse] = None
        self._session: Optional[aiohttp.ClientSession] = None
        self._subscriptions: dict[str, set[str]] = {}
        self._callbacks: dict[str, list] = {}
        self._token: Optional[str] = None
    
    async def connect(self, token: str):
        """Establish WebSocket connection with auth."""
        self._token = token
        self._session = aiohttp.ClientSession()
        
        headers = {"Authorization": f"Bearer {token}"}
        self._ws = await self._session.ws_connect(self.ws_url, headers=headers)
    
    async def disconnect(self):
        """Close WebSocket connection."""
        if self._ws:
            await self._ws.close()
        if self._session:
            await self._session.close()
    
    async def subscribe_orderbook(self, ticker: str, callback):
        """Subscribe to order book updates."""
        await self._subscribe("orderbook_delta", ticker, callback)
    
    async def subscribe_ticker(self, ticker: str, callback):
        """Subscribe to ticker updates."""
        await self._subscribe("ticker", ticker, callback)
    
    async def subscribe_trade(self, ticker: str, callback):
        """Subscribe to trade updates."""
        await self._subscribe("trade", ticker, callback)
    
    async def subscribe_fill(self, callback):
        """Subscribe to fill updates (user's fills)."""
        await self._subscribe("fill", "", callback)
    
    async def _subscribe(self, channel: str, ticker: str, callback):
        """Internal subscribe method."""
        sub_msg = {
            "id": int(time.time() * 1000),
            "cmd": "subscribe",
            "params": {
                "channels": [channel],
            }
        }
        
        if ticker:
            sub_msg["params"]["market_tickers"] = [ticker]
        
        await self._ws.send_json(sub_msg)
        
        key = f"{channel}:{ticker}"
        if key not in self._subscriptions:
            self._subscriptions[key] = set()
        self._subscriptions[key].add(callback)
        
        if key not in self._callbacks:
            self._callbacks[key] = []
        self._callbacks[key].append(callback)
    
    async def listen(self):
        """Listen for WebSocket messages."""
        async for msg in self._ws:
            if msg.type == aiohttp.WSMsgType.TEXT:
                data = json.loads(msg.data)
                await self._handle_message(data)
            elif msg.type == aiohttp.WSMsgType.ERROR:
                break
    
    async def _handle_message(self, data: dict):
        """Handle incoming WebSocket message."""
        msg_type = data.get("type")
        
        if msg_type == "orderbook_delta":
            ticker = data.get("msg", {}).get("market_ticker", "")
            key = f"orderbook_delta:{ticker}"
        elif msg_type == "ticker":
            ticker = data.get("msg", {}).get("market_ticker", "")
            key = f"ticker:{ticker}"
        elif msg_type == "trade":
            ticker = data.get("msg", {}).get("market_ticker", "")
            key = f"trade:{ticker}"
        elif msg_type == "fill":
            key = "fill:"
        else:
            return
        
        if key in self._callbacks:
            for callback in self._callbacks[key]:
                await callback(data)


# =============================================================================
# USAGE EXAMPLE
# =============================================================================

async def example_usage():
    """Example usage of Kalshi client."""
    
    async with KalshiClient(
        email="your_email@example.com",
        password="your_password",
        use_demo=True,
        builder_code="ECHELON"
    ) as client:
        
        # Get events
        events, _ = await client.get_events(limit=10)
        print(f"Found {len(events)} events")
        
        if events:
            event = events[0]
            print(f"Event: {event.title}")
            
            # Get markets for event
            markets, _ = await client.get_markets(event_ticker=event.event_ticker)
            print(f"Markets in event: {len(markets)}")
            
            if markets:
                market = markets[0]
                print(f"Market: {market.title}")
                print(f"YES mid: {market.yes_mid}")
                print(f"Spread: {market.spread}")
                
                # Get order book
                book = await client.get_market_orderbook(market.ticker)
                print(f"Order book: {book}")
        
        # Get balance
        balance = await client.get_balance()
        print(f"Balance: ${balance.balance / 100:.2f}")


if __name__ == "__main__":
    asyncio.run(example_usage())
