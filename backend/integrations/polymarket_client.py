"""
Polymarket CLOB API Client
==========================

Full integration with Polymarket's Central Limit Order Book API.
Includes Builder Code attribution for volume tracking and revenue share.

Polymarket Integration Points:
- CLOB API for order routing and market data
- Gamma Markets API for event/market structure
- Polygon Relayer for gasless agent transactions
- Safe Wallet deployment for AI agents

Author: Echelon Protocol
Version: 1.0.0
"""

import asyncio
import hashlib
import hmac
import json
import time
from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from typing import Any, Optional
from urllib.parse import urlencode

import aiohttp
from pydantic import BaseModel, Field


# =============================================================================
# CONFIGURATION
# =============================================================================

class PolymarketConfig:
    """Polymarket API configuration."""
    
    # API Endpoints
    CLOB_BASE_URL = "https://clob.polymarket.com"
    GAMMA_BASE_URL = "https://gamma-api.polymarket.com"
    RELAYER_URL = "https://relayer.polymarket.com"
    
    # Testnet endpoints (Mumbai)
    CLOB_TESTNET_URL = "https://clob-testnet.polymarket.com"
    GAMMA_TESTNET_URL = "https://gamma-api-testnet.polymarket.com"
    
    # Chain configuration
    POLYGON_CHAIN_ID = 137
    MUMBAI_CHAIN_ID = 80001
    
    # USDC on Polygon
    USDC_ADDRESS = "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"
    USDC_DECIMALS = 6
    
    # Rate limits
    RATE_LIMIT_REQUESTS = 100
    RATE_LIMIT_WINDOW = 60  # seconds
    
    # Builder Code for Echelon (register at polymarket.com/builders)
    BUILDER_CODE = "ECHELON"  # Replace with actual assigned code


# =============================================================================
# DATA MODELS
# =============================================================================

class OrderSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderType(str, Enum):
    LIMIT = "LIMIT"
    MARKET = "MARKET"
    FOK = "FOK"  # Fill or Kill
    GTD = "GTD"  # Good Till Date


class OrderStatus(str, Enum):
    PENDING = "PENDING"
    OPEN = "OPEN"
    FILLED = "FILLED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"


class MarketStatus(str, Enum):
    ACTIVE = "active"
    CLOSED = "closed"
    RESOLVED = "resolved"


class PolymarketMarket(BaseModel):
    """Polymarket market data model."""
    
    condition_id: str = Field(..., description="Unique market condition ID")
    question_id: str = Field(..., description="Question identifier")
    question: str = Field(..., description="Market question text")
    description: Optional[str] = Field(None, description="Market description")
    
    tokens: list[dict] = Field(default_factory=list, description="Outcome tokens")
    
    market_slug: Optional[str] = Field(None, description="URL slug")
    end_date_iso: Optional[str] = Field(None, description="Resolution date")
    
    active: bool = Field(True, description="Market is active")
    closed: bool = Field(False, description="Market is closed")
    
    volume: Optional[str] = Field(None, description="Total volume")
    volume_24hr: Optional[str] = Field(None, description="24h volume")
    liquidity: Optional[str] = Field(None, description="Available liquidity")
    
    best_bid: Optional[str] = Field(None, description="Best bid price")
    best_ask: Optional[str] = Field(None, description="Best ask price")
    last_trade_price: Optional[str] = Field(None, description="Last trade price")


class PolymarketOrder(BaseModel):
    """Order model for CLOB."""
    
    order_id: Optional[str] = Field(None, description="Assigned order ID")
    market_id: str = Field(..., description="Market condition ID")
    token_id: str = Field(..., description="Outcome token ID")
    
    side: OrderSide = Field(..., description="BUY or SELL")
    order_type: OrderType = Field(OrderType.LIMIT, description="Order type")
    
    price: Decimal = Field(..., description="Price in USDC (0-1)")
    size: Decimal = Field(..., description="Size in outcome tokens")
    
    maker_address: str = Field(..., description="Maker wallet address")
    
    status: OrderStatus = Field(OrderStatus.PENDING, description="Order status")
    filled_size: Decimal = Field(Decimal("0"), description="Filled amount")
    
    expiration: Optional[int] = Field(None, description="Unix timestamp expiry")
    
    # Builder attribution
    builder_code: str = Field(PolymarketConfig.BUILDER_CODE, description="Builder code")
    
    # Signature fields
    signature: Optional[str] = Field(None, description="EIP-712 signature")
    salt: Optional[str] = Field(None, description="Order salt for uniqueness")


class OrderBookLevel(BaseModel):
    """Single level in order book."""
    
    price: Decimal
    size: Decimal
    num_orders: int = 1


class OrderBook(BaseModel):
    """Full order book snapshot."""
    
    token_id: str
    bids: list[OrderBookLevel] = Field(default_factory=list)
    asks: list[OrderBookLevel] = Field(default_factory=list)
    timestamp: int = Field(default_factory=lambda: int(time.time() * 1000))
    
    @property
    def spread(self) -> Optional[Decimal]:
        if self.bids and self.asks:
            return self.asks[0].price - self.bids[0].price
        return None
    
    @property
    def mid_price(self) -> Optional[Decimal]:
        if self.bids and self.asks:
            return (self.asks[0].price + self.bids[0].price) / 2
        return None


class TradeEvent(BaseModel):
    """Trade execution event."""
    
    trade_id: str
    market_id: str
    token_id: str
    
    price: Decimal
    size: Decimal
    side: OrderSide
    
    maker_address: str
    taker_address: str
    
    timestamp: int
    transaction_hash: Optional[str] = None
    
    # Builder attribution
    builder_code: Optional[str] = None


# =============================================================================
# API CLIENT
# =============================================================================

class PolymarketCLOBClient:
    """
    Polymarket CLOB API Client.
    
    Handles:
    - Market data fetching
    - Order placement and management
    - Order book streaming
    - Trade execution
    - Builder Code attribution
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        passphrase: Optional[str] = None,
        use_testnet: bool = False,
        builder_code: str = PolymarketConfig.BUILDER_CODE
    ):
        self.api_key = api_key
        self.api_secret = api_secret
        self.passphrase = passphrase
        self.use_testnet = use_testnet
        self.builder_code = builder_code
        
        # Set base URLs
        if use_testnet:
            self.clob_url = PolymarketConfig.CLOB_TESTNET_URL
            self.gamma_url = PolymarketConfig.GAMMA_TESTNET_URL
        else:
            self.clob_url = PolymarketConfig.CLOB_BASE_URL
            self.gamma_url = PolymarketConfig.GAMMA_BASE_URL
        
        # Session management
        self._session: Optional[aiohttp.ClientSession] = None
        self._rate_limiter = RateLimiter(
            PolymarketConfig.RATE_LIMIT_REQUESTS,
            PolymarketConfig.RATE_LIMIT_WINDOW
        )
    
    async def __aenter__(self):
        await self._ensure_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    async def _ensure_session(self):
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
    
    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()
    
    def _generate_signature(self, timestamp: str, method: str, path: str, body: str = "") -> str:
        """Generate HMAC signature for authenticated requests."""
        if not self.api_secret:
            raise ValueError("API secret required for authenticated requests")
        
        message = f"{timestamp}{method}{path}{body}"
        signature = hmac.new(
            self.api_secret.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return signature
    
    def _get_headers(self, method: str, path: str, body: str = "") -> dict:
        """Generate request headers with authentication."""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        
        if self.api_key:
            timestamp = str(int(time.time() * 1000))
            signature = self._generate_signature(timestamp, method, path, body)
            
            headers.update({
                "POLY_API_KEY": self.api_key,
                "POLY_SIGNATURE": signature,
                "POLY_TIMESTAMP": timestamp,
                "POLY_PASSPHRASE": self.passphrase or "",
            })
        
        return headers
    
    async def _request(
        self,
        method: str,
        base_url: str,
        path: str,
        params: Optional[dict] = None,
        data: Optional[dict] = None
    ) -> dict:
        """Make API request with rate limiting and error handling."""
        await self._ensure_session()
        await self._rate_limiter.acquire()
        
        url = f"{base_url}{path}"
        if params:
            url = f"{url}?{urlencode(params)}"
        
        body = json.dumps(data) if data else ""
        headers = self._get_headers(method, path, body)
        
        try:
            async with self._session.request(
                method,
                url,
                headers=headers,
                data=body if data else None
            ) as response:
                response_data = await response.json()
                
                if response.status >= 400:
                    raise PolymarketAPIError(
                        status=response.status,
                        message=response_data.get("message", "Unknown error"),
                        code=response_data.get("code")
                    )
                
                return response_data
                
        except aiohttp.ClientError as e:
            raise PolymarketAPIError(
                status=0,
                message=f"Network error: {str(e)}"
            )
    
    # =========================================================================
    # MARKET DATA
    # =========================================================================
    
    async def get_markets(
        self,
        active: bool = True,
        closed: bool = False,
        limit: int = 100,
        offset: int = 0
    ) -> list[PolymarketMarket]:
        """Fetch list of markets from Gamma API."""
        params = {
            "active": str(active).lower(),
            "closed": str(closed).lower(),
            "limit": limit,
            "offset": offset,
        }
        
        response = await self._request("GET", self.gamma_url, "/markets", params=params)
        
        return [PolymarketMarket(**market) for market in response]
    
    async def get_market(self, condition_id: str) -> PolymarketMarket:
        """Fetch single market by condition ID."""
        response = await self._request("GET", self.gamma_url, f"/markets/{condition_id}")
        return PolymarketMarket(**response)
    
    async def search_markets(self, query: str, limit: int = 20) -> list[PolymarketMarket]:
        """Search markets by query string."""
        params = {"query": query, "limit": limit}
        response = await self._request("GET", self.gamma_url, "/markets/search", params=params)
        return [PolymarketMarket(**market) for market in response]
    
    async def get_order_book(self, token_id: str) -> OrderBook:
        """Fetch order book for a token."""
        response = await self._request("GET", self.clob_url, f"/book", params={"token_id": token_id})
        
        bids = [OrderBookLevel(
            price=Decimal(level["price"]),
            size=Decimal(level["size"])
        ) for level in response.get("bids", [])]
        
        asks = [OrderBookLevel(
            price=Decimal(level["price"]),
            size=Decimal(level["size"])
        ) for level in response.get("asks", [])]
        
        return OrderBook(token_id=token_id, bids=bids, asks=asks)
    
    async def get_midpoint(self, token_id: str) -> Optional[Decimal]:
        """Get midpoint price for a token."""
        response = await self._request("GET", self.clob_url, f"/midpoint", params={"token_id": token_id})
        if response.get("mid"):
            return Decimal(response["mid"])
        return None
    
    async def get_price(self, token_id: str, side: OrderSide) -> Optional[Decimal]:
        """Get best price for a side."""
        response = await self._request(
            "GET", 
            self.clob_url, 
            f"/price",
            params={"token_id": token_id, "side": side.value}
        )
        if response.get("price"):
            return Decimal(response["price"])
        return None
    
    # =========================================================================
    # ORDER MANAGEMENT
    # =========================================================================
    
    async def create_order(self, order: PolymarketOrder) -> PolymarketOrder:
        """
        Create a new order on the CLOB.
        
        Includes Builder Code for volume attribution.
        """
        # Ensure builder code is set
        order.builder_code = self.builder_code
        
        # Generate salt for order uniqueness
        if not order.salt:
            order.salt = hashlib.sha256(
                f"{order.maker_address}{order.token_id}{time.time()}".encode()
            ).hexdigest()[:16]
        
        order_data = {
            "market": order.market_id,
            "tokenID": order.token_id,
            "side": order.side.value,
            "type": order.order_type.value,
            "price": str(order.price),
            "size": str(order.size),
            "makerAddress": order.maker_address,
            "salt": order.salt,
            "builderCode": order.builder_code,  # Builder attribution!
        }
        
        if order.expiration:
            order_data["expiration"] = order.expiration
        
        if order.signature:
            order_data["signature"] = order.signature
        
        response = await self._request("POST", self.clob_url, "/order", data=order_data)
        
        order.order_id = response.get("orderID")
        order.status = OrderStatus(response.get("status", "PENDING"))
        
        return order
    
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel an existing order."""
        response = await self._request("DELETE", self.clob_url, f"/order/{order_id}")
        return response.get("success", False)
    
    async def cancel_all_orders(self, market_id: Optional[str] = None) -> int:
        """Cancel all orders, optionally filtered by market."""
        params = {}
        if market_id:
            params["market"] = market_id
        
        response = await self._request("DELETE", self.clob_url, "/orders", params=params)
        return response.get("cancelled", 0)
    
    async def get_order(self, order_id: str) -> PolymarketOrder:
        """Get order by ID."""
        response = await self._request("GET", self.clob_url, f"/order/{order_id}")
        return self._parse_order_response(response)
    
    async def get_orders(
        self,
        market_id: Optional[str] = None,
        status: Optional[OrderStatus] = None,
        limit: int = 100
    ) -> list[PolymarketOrder]:
        """Get orders with optional filters."""
        params = {"limit": limit}
        if market_id:
            params["market"] = market_id
        if status:
            params["status"] = status.value
        
        response = await self._request("GET", self.clob_url, "/orders", params=params)
        return [self._parse_order_response(o) for o in response]
    
    def _parse_order_response(self, data: dict) -> PolymarketOrder:
        """Parse order response into model."""
        return PolymarketOrder(
            order_id=data.get("orderID"),
            market_id=data.get("market", ""),
            token_id=data.get("tokenID", ""),
            side=OrderSide(data.get("side", "BUY")),
            order_type=OrderType(data.get("type", "LIMIT")),
            price=Decimal(data.get("price", "0")),
            size=Decimal(data.get("size", "0")),
            maker_address=data.get("makerAddress", ""),
            status=OrderStatus(data.get("status", "PENDING")),
            filled_size=Decimal(data.get("filledSize", "0")),
            builder_code=data.get("builderCode"),
        )
    
    # =========================================================================
    # TRADE HISTORY
    # =========================================================================
    
    async def get_trades(
        self,
        market_id: Optional[str] = None,
        token_id: Optional[str] = None,
        limit: int = 100
    ) -> list[TradeEvent]:
        """Get recent trades."""
        params = {"limit": limit}
        if market_id:
            params["market"] = market_id
        if token_id:
            params["token_id"] = token_id
        
        response = await self._request("GET", self.clob_url, "/trades", params=params)
        
        return [TradeEvent(
            trade_id=t.get("tradeID", ""),
            market_id=t.get("market", ""),
            token_id=t.get("tokenID", ""),
            price=Decimal(t.get("price", "0")),
            size=Decimal(t.get("size", "0")),
            side=OrderSide(t.get("side", "BUY")),
            maker_address=t.get("makerAddress", ""),
            taker_address=t.get("takerAddress", ""),
            timestamp=t.get("timestamp", 0),
            transaction_hash=t.get("transactionHash"),
            builder_code=t.get("builderCode"),
        ) for t in response]
    
    # =========================================================================
    # BUILDER STATS
    # =========================================================================
    
    async def get_builder_stats(self) -> dict:
        """Get volume and stats for our builder code."""
        response = await self._request(
            "GET", 
            self.clob_url, 
            f"/builder/{self.builder_code}/stats"
        )
        return response


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
            
            # Refill tokens
            self.tokens = min(self.rate, self.tokens + elapsed * (self.rate / self.window))
            self.last_update = now
            
            if self.tokens < 1:
                # Wait for token
                wait_time = (1 - self.tokens) * (self.window / self.rate)
                await asyncio.sleep(wait_time)
                self.tokens = 0
            else:
                self.tokens -= 1


# =============================================================================
# EXCEPTIONS
# =============================================================================

class PolymarketAPIError(Exception):
    """Polymarket API error."""
    
    def __init__(self, status: int, message: str, code: Optional[str] = None):
        self.status = status
        self.message = message
        self.code = code
        super().__init__(f"[{status}] {message}")


# =============================================================================
# WEBSOCKET CLIENT (Order Book Streaming)
# =============================================================================

class PolymarketWebSocket:
    """WebSocket client for real-time order book updates."""
    
    WS_URL = "wss://ws-subscriptions-clob.polymarket.com/ws/market"
    WS_TESTNET_URL = "wss://ws-subscriptions-clob-testnet.polymarket.com/ws/market"
    
    def __init__(self, use_testnet: bool = False):
        self.ws_url = self.WS_TESTNET_URL if use_testnet else self.WS_URL
        self._ws: Optional[aiohttp.ClientWebSocketResponse] = None
        self._session: Optional[aiohttp.ClientSession] = None
        self._subscriptions: set[str] = set()
        self._callbacks: dict[str, list] = {}
    
    async def connect(self):
        """Establish WebSocket connection."""
        self._session = aiohttp.ClientSession()
        self._ws = await self._session.ws_connect(self.ws_url)
    
    async def disconnect(self):
        """Close WebSocket connection."""
        if self._ws:
            await self._ws.close()
        if self._session:
            await self._session.close()
    
    async def subscribe(self, token_id: str, callback):
        """Subscribe to order book updates for a token."""
        if token_id not in self._subscriptions:
            subscribe_msg = {
                "type": "subscribe",
                "channel": "book",
                "market": token_id
            }
            await self._ws.send_json(subscribe_msg)
            self._subscriptions.add(token_id)
        
        if token_id not in self._callbacks:
            self._callbacks[token_id] = []
        self._callbacks[token_id].append(callback)
    
    async def unsubscribe(self, token_id: str):
        """Unsubscribe from token updates."""
        if token_id in self._subscriptions:
            unsubscribe_msg = {
                "type": "unsubscribe",
                "channel": "book",
                "market": token_id
            }
            await self._ws.send_json(unsubscribe_msg)
            self._subscriptions.discard(token_id)
            self._callbacks.pop(token_id, None)
    
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
        token_id = data.get("market")
        if token_id and token_id in self._callbacks:
            for callback in self._callbacks[token_id]:
                await callback(data)


# =============================================================================
# USAGE EXAMPLE
# =============================================================================

async def example_usage():
    """Example usage of Polymarket client."""
    
    async with PolymarketCLOBClient(
        api_key="your_api_key",
        api_secret="your_api_secret",
        builder_code="ECHELON"
    ) as client:
        
        # Search for markets
        markets = await client.search_markets("presidential election")
        print(f"Found {len(markets)} markets")
        
        if markets:
            market = markets[0]
            print(f"Market: {market.question}")
            
            # Get order book for first token
            if market.tokens:
                token_id = market.tokens[0]["token_id"]
                book = await client.get_order_book(token_id)
                print(f"Spread: {book.spread}")
                print(f"Mid price: {book.mid_price}")
        
        # Get builder stats
        stats = await client.get_builder_stats()
        print(f"Builder volume: {stats}")


if __name__ == "__main__":
    asyncio.run(example_usage())
