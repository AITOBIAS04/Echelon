# Echelon Platform Integrations

## Phase 3: Platform Integration (Weeks 5-6)

This module provides unified integration with Polymarket and Kalshi prediction markets, including Builder Code attribution for volume tracking and revenue share.

---

## Overview

| Module | Purpose |
|--------|---------|
| `polymarket_client.py` | Polymarket CLOB API client |
| `kalshi_client.py` | Kalshi DFlow API client |
| `builder_attribution.py` | Volume tracking & metrics |
| `__init__.py` | Package exports |

---

## Polymarket Integration

### Features
- Full CLOB API support (orders, markets, trades)
- Gamma Markets API for event structure
- WebSocket streaming for real-time data
- Builder Code attribution on every order
- Rate limiting and error handling

### Key Endpoints
```python
from backend.integrations import PolymarketCLOBClient

async with PolymarketCLOBClient(
    api_key="your_key",
    api_secret="your_secret",
    builder_code="ECHELON"
) as client:
    # Search markets
    markets = await client.search_markets("election")
    
    # Get order book
    book = await client.get_order_book(token_id)
    
    # Place order (with builder attribution)
    order = await client.create_order(order)
```

### Configuration
```python
class PolymarketConfig:
    CLOB_BASE_URL = "https://clob.polymarket.com"
    GAMMA_BASE_URL = "https://gamma-api.polymarket.com"
    USDC_ADDRESS = "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"
    BUILDER_CODE = "ECHELON"
```

---

## Kalshi Integration

### Features
- Full DFlow API support
- Event and market queries
- Order management
- Position tracking
- WebSocket for real-time updates
- Builder Code attribution

### Key Endpoints
```python
from backend.integrations import KalshiClient

async with KalshiClient(
    email="your_email",
    password="your_password",
    builder_code="ECHELON"
) as client:
    # Get events
    events, _ = await client.get_events()
    
    # Get market
    market = await client.get_market("INXD-23DEC31-T4500")
    
    # Place order
    order = await client.create_order(order)
    
    # Get positions
    positions = await client.get_positions()
```

### Configuration
```python
class KalshiConfig:
    API_BASE_URL = "https://trading-api.kalshi.com/trade-api/v2"
    DEMO_API_URL = "https://demo-api.kalshi.co/trade-api/v2"
    BUILDER_CODE = "ECHELON"
```

---

## Builder Code Attribution

The attribution manager tracks all trades and calculates volume metrics.

### Recording Trades
```python
from backend.integrations import BuilderAttributionManager, Platform

manager = BuilderAttributionManager(
    polymarket_code="ECHELON",
    kalshi_code="ECHELON"
)

# Record Polymarket trade
await manager.record_polymarket_trade(
    trade_id="pm_001",
    market_id="0x123abc",
    side="BUY",
    size=Decimal("100"),
    price=Decimal("0.65"),
    agent_id="SHARK_001"
)

# Record Kalshi trade
await manager.record_kalshi_trade(
    trade_id="kl_001",
    ticker="INXD-23DEC31-T4500",
    action="buy",
    side="yes",
    count=50,
    price_cents=45,
    agent_id="SPY_001"
)
```

### Getting Metrics
```python
from backend.integrations import TimeRange

# Volume metrics
metrics = await manager.get_volume_metrics(
    platform=Platform.POLYMARKET,
    time_range=TimeRange.DAY
)

print(f"24h Volume: ${metrics.total_volume_usd}")
print(f"Trade Count: {metrics.trade_count}")
print(f"Revenue Share: ${metrics.revenue_share}")

# Agent leaderboard
agents = await manager.get_agent_leaderboard(TimeRange.WEEK)
for agent in agents:
    print(f"{agent.agent_id}: ${agent.total_volume}")

# Full report
report = await manager.generate_report(TimeRange.MONTH)
```

---

## Data Models

### Unified Market
```python
class UnifiedMarket:
    platform: UnifiedPlatform
    market_id: str
    question: str
    outcomes: list[str]
    outcome_prices: dict[str, Decimal]
    volume: Decimal
    spread: Optional[Decimal]
    is_active: bool
```

### Unified Order
```python
class UnifiedOrder:
    platform: UnifiedPlatform
    order_id: Optional[str]
    market_id: str
    side: str  # "buy" or "sell"
    outcome: str
    price: Decimal
    size: Decimal
    status: str
    agent_id: Optional[str]
    builder_code: Optional[str]
```

---

## Rate Limits

| Platform | Requests | Window |
|----------|----------|--------|
| Polymarket | 100 | 60 sec |
| Kalshi | 10 | 1 sec |

Both clients implement automatic rate limiting with token bucket algorithms.

---

## Error Handling

```python
from backend.integrations import PolymarketAPIError, KalshiAPIError

try:
    order = await client.create_order(order)
except PolymarketAPIError as e:
    print(f"Polymarket error [{e.status}]: {e.message}")
except KalshiAPIError as e:
    print(f"Kalshi error [{e.status}]: {e.message}")
```

---

## WebSocket Streaming

### Polymarket
```python
ws = PolymarketWebSocket()
await ws.connect()

async def on_book_update(data):
    print(f"Book update: {data}")

await ws.subscribe(token_id, on_book_update)
await ws.listen()
```

### Kalshi
```python
ws = KalshiWebSocket()
await ws.connect(auth_token)

await ws.subscribe_orderbook(ticker, callback)
await ws.subscribe_trade(ticker, callback)
await ws.listen()
```

---

## Environment Variables

```bash
# Polymarket
POLYMARKET_API_KEY=your_key
POLYMARKET_API_SECRET=your_secret

# Kalshi
KALSHI_EMAIL=your_email
KALSHI_PASSWORD=your_password

# Builder Code
ECHELON_BUILDER_CODE=ECHELON

# Network
USE_TESTNET=true
```

---

## Integration with Agent System

The platform clients integrate with the agent system:

```python
# Agent places order through platform client
async def agent_trade(agent_id: str, decision: TradeDecision):
    order = UnifiedOrder(
        platform=decision.platform,
        market_id=decision.market_id,
        side=decision.side,
        outcome=decision.outcome,
        price=decision.price,
        size=decision.size,
        agent_id=agent_id,  # Attribution!
        builder_code="ECHELON"
    )
    
    result = await platform_manager.place_order(order)
    
    # Trade is automatically attributed to agent
    # and counted toward builder volume
```

---

## Revenue Share

Builder Codes earn revenue share from platform fees:

| Platform | Revenue Share |
|----------|---------------|
| Polymarket | ~1% of fees |
| Kalshi | Variable |

Revenue is calculated automatically by the attribution manager and can be queried for reporting.

---

## Next Steps

- [ ] Implement unified position tracking
- [ ] Add historical trade export
- [ ] Create dashboard for builder metrics
- [ ] Implement cross-platform arbitrage detection

---

## Contact

- **Email:** playechelon@gmail.com
- **X:** @playechelon
- **GitHub:** github.com/AITOBIAS04/prediction-market-monorepo
