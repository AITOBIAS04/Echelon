"""
Echelon Markets API
===================

FastAPI router providing market endpoints for the Betting Markets page.

Endpoints:
- /api/markets - List all markets
- /api/markets/fetch - Fetch news and create markets
- /api/markets/{id} - Get specific market
- /api/markets/{id}/bet - Place a bet

Author: Echelon Protocol
Version: 1.0.0
"""

import asyncio
import random
from datetime import datetime, timedelta
from typing import Optional
from enum import Enum

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/markets", tags=["Markets"])


# =============================================================================
# MODELS
# =============================================================================

class MarketCategory(str, Enum):
    FINANCE = "finance"
    CRYPTO = "crypto"
    SPORTS = "sports"
    POLITICS = "politics"
    GEOPOLITICS = "geopolitics"


class MarketStatus(str, Enum):
    OPEN = "open"
    CLOSED = "closed"
    SETTLED = "settled"


class MarketDuration(str, Enum):
    H24 = "24h"
    D7 = "7d"
    D30 = "30d+"


class Market(BaseModel):
    id: str
    title: str
    description: str
    category: MarketCategory
    status: MarketStatus
    
    # Prices
    yes_price: float = Field(ge=0, le=1)
    no_price: float = Field(ge=0, le=1)
    
    # Volume
    volume_24h: float
    total_volume: float
    
    # Timing
    created_at: datetime
    end_date: datetime
    duration: MarketDuration
    
    # Source
    source: Optional[str] = None
    source_url: Optional[str] = None
    
    # Resolution
    resolution: Optional[str] = None  # "yes", "no", None if unresolved


class BetRequest(BaseModel):
    market_id: str
    side: str  # "yes" or "no"
    amount: float
    price: Optional[float] = None  # For limit orders


class BetResponse(BaseModel):
    bet_id: str
    market_id: str
    side: str
    amount: float
    price: float
    status: str
    created_at: datetime


# =============================================================================
# IN-MEMORY STATE
# =============================================================================

class MarketsState:
    """Manages markets state."""
    
    def __init__(self):
        self.markets: dict[str, Market] = {}
        self.last_fetch: Optional[datetime] = None
        self._seed_markets()
    
    def _seed_markets(self):
        """Seed initial markets."""
        now = datetime.utcnow()
        
        initial_markets = [
            {
                "id": "btc_100k_dec",
                "title": "Bitcoin > $100k?",
                "description": "Will Bitcoin exceed $100,000 USD before December 31, 2025?",
                "category": MarketCategory.CRYPTO,
                "yes_price": 0.65,
                "volume_24h": 12000,
                "total_volume": 450000,
                "end_date": datetime(2025, 12, 31),
                "duration": MarketDuration.D30,
            },
            {
                "id": "fed_rate_dec",
                "title": "Fed Cuts Rates in December?",
                "description": "Will the Federal Reserve cut interest rates at their December 2025 meeting?",
                "category": MarketCategory.FINANCE,
                "yes_price": 0.45,
                "volume_24h": 8500,
                "total_volume": 280000,
                "end_date": datetime(2025, 12, 18),
                "duration": MarketDuration.D7,
            },
            {
                "id": "eth_5k",
                "title": "ETH > $5,000?",
                "description": "Will Ethereum exceed $5,000 USD before January 1, 2026?",
                "category": MarketCategory.CRYPTO,
                "yes_price": 0.38,
                "volume_24h": 6200,
                "total_volume": 180000,
                "end_date": datetime(2026, 1, 1),
                "duration": MarketDuration.D30,
            },
            {
                "id": "ukraine_ceasefire",
                "title": "Ukraine Ceasefire by Q1 2026?",
                "description": "Will there be an official ceasefire agreement in Ukraine before April 1, 2026?",
                "category": MarketCategory.GEOPOLITICS,
                "yes_price": 0.22,
                "volume_24h": 15000,
                "total_volume": 520000,
                "end_date": datetime(2026, 4, 1),
                "duration": MarketDuration.D30,
            },
            {
                "id": "trump_executive_order",
                "title": "Trump Signs Crypto Executive Order?",
                "description": "Will President Trump sign an executive order related to cryptocurrency in his first 100 days?",
                "category": MarketCategory.POLITICS,
                "yes_price": 0.78,
                "volume_24h": 22000,
                "total_volume": 680000,
                "end_date": datetime(2025, 4, 30),
                "duration": MarketDuration.D30,
            },
            {
                "id": "apple_ai_acquisition",
                "title": "Apple Acquires AI Company?",
                "description": "Will Apple announce the acquisition of a major AI company (>$1B) before March 2026?",
                "category": MarketCategory.FINANCE,
                "yes_price": 0.42,
                "volume_24h": 4500,
                "total_volume": 95000,
                "end_date": datetime(2026, 3, 1),
                "duration": MarketDuration.D30,
            },
        ]
        
        for m in initial_markets:
            market = Market(
                id=m["id"],
                title=m["title"],
                description=m["description"],
                category=m["category"],
                status=MarketStatus.OPEN,
                yes_price=m["yes_price"],
                no_price=round(1 - m["yes_price"], 2),
                volume_24h=m["volume_24h"],
                total_volume=m["total_volume"],
                created_at=now - timedelta(days=random.randint(1, 30)),
                end_date=m["end_date"],
                duration=m["duration"],
            )
            self.markets[market.id] = market
    
    def add_market_from_news(self, news_item: dict) -> Market:
        """Create a market from a news item."""
        now = datetime.utcnow()
        
        # Generate market from news
        market_id = f"news_{int(now.timestamp())}"
        
        market = Market(
            id=market_id,
            title=news_item.get("title", "News Event Market"),
            description=news_item.get("description", ""),
            category=MarketCategory(news_item.get("category", "finance")),
            status=MarketStatus.OPEN,
            yes_price=0.50,  # Start at 50/50
            no_price=0.50,
            volume_24h=0,
            total_volume=0,
            created_at=now,
            end_date=now + timedelta(days=7),  # Default 7 day market
            duration=MarketDuration.D7,
            source=news_item.get("source"),
            source_url=news_item.get("url"),
        )
        
        self.markets[market_id] = market
        return market


# Global state
state = MarketsState()


# =============================================================================
# MOCK NEWS GENERATOR
# =============================================================================

def generate_mock_news() -> list[dict]:
    """Generate mock news items for market creation."""
    templates = [
        {
            "title": "Will {company} announce layoffs this week?",
            "description": "Reports suggest {company} is planning workforce reductions amid {reason}.",
            "category": "finance",
            "companies": ["Meta", "Google", "Amazon", "Microsoft", "Tesla"],
            "reasons": ["cost cutting measures", "AI restructuring", "market conditions"]
        },
        {
            "title": "Will {crypto} hit ${price} by end of week?",
            "description": "Technical analysis suggests {crypto} could {direction} significantly.",
            "category": "crypto",
            "cryptos": ["Bitcoin", "Ethereum", "Solana", "XRP"],
            "directions": ["rally", "correct", "break out"]
        },
        {
            "title": "Will {leader} meet with {other_leader} this month?",
            "description": "Diplomatic sources indicate potential {event_type} summit.",
            "category": "geopolitics",
            "leaders": ["Biden", "Xi", "Putin", "Macron", "Modi"],
            "event_types": ["emergency", "trade", "security"]
        },
        {
            "title": "Will {team} win against {opponent}?",
            "description": "Upcoming match between {team} and {opponent} on {day}.",
            "category": "sports",
            "teams": ["Manchester United", "Lakers", "Patriots", "Yankees"],
            "days": ["Saturday", "Sunday", "Monday Night"]
        },
    ]
    
    news_items = []
    for _ in range(5):  # Generate 5 news items
        template = random.choice(templates)
        
        if template["category"] == "finance":
            company = random.choice(template["companies"])
            reason = random.choice(template["reasons"])
            item = {
                "title": template["title"].format(company=company),
                "description": template["description"].format(company=company, reason=reason),
                "category": template["category"],
                "source": random.choice(["Reuters", "Bloomberg", "WSJ", "CNBC"])
            }
        elif template["category"] == "crypto":
            crypto = random.choice(template["cryptos"])
            price = random.choice([100000, 5000, 200, 1])
            direction = random.choice(template["directions"])
            item = {
                "title": template["title"].format(crypto=crypto, price=price),
                "description": template["description"].format(crypto=crypto, direction=direction),
                "category": template["category"],
                "source": random.choice(["CoinDesk", "CoinTelegraph", "The Block"])
            }
        elif template["category"] == "geopolitics":
            leaders = random.sample(template["leaders"], 2)
            event_type = random.choice(template["event_types"])
            item = {
                "title": template["title"].format(leader=leaders[0], other_leader=leaders[1]),
                "description": template["description"].format(event_type=event_type),
                "category": template["category"],
                "source": random.choice(["AP", "Reuters", "BBC", "Al Jazeera"])
            }
        else:  # sports
            teams = random.sample(template["teams"], 2)
            day = random.choice(template["days"])
            item = {
                "title": template["title"].format(team=teams[0], opponent=teams[1]),
                "description": template["description"].format(team=teams[0], opponent=teams[1], day=day),
                "category": template["category"],
                "source": random.choice(["ESPN", "Sky Sports", "BBC Sport"])
            }
        
        news_items.append(item)
    
    return news_items


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.get("", response_model=list[Market])
async def get_markets(
    category: Optional[MarketCategory] = None,
    status: Optional[MarketStatus] = None,
    duration: Optional[MarketDuration] = None,
    limit: int = Query(50, le=100),
):
    """Get all markets with optional filters."""
    markets = list(state.markets.values())
    
    if category:
        markets = [m for m in markets if m.category == category]
    if status:
        markets = [m for m in markets if m.status == status]
    if duration:
        markets = [m for m in markets if m.duration == duration]
    
    # Sort by volume
    markets.sort(key=lambda m: m.volume_24h, reverse=True)
    
    return markets[:limit]


@router.get("/fetch")
async def fetch_markets():
    """Fetch news and create new markets."""
    # Generate mock news (replace with real API calls when keys available)
    news_items = generate_mock_news()
    
    created_markets = []
    for news in news_items:
        market = state.add_market_from_news(news)
        created_markets.append(market)
    
    state.last_fetch = datetime.utcnow()
    
    return {
        "status": "success",
        "markets_created": len(created_markets),
        "markets": created_markets,
        "last_fetch": state.last_fetch.isoformat()
    }


@router.post("/refresh")
async def refresh_markets():
    """Alias for fetch - refresh markets from news."""
    return await fetch_markets()


@router.get("/{market_id}", response_model=Market)
async def get_market(market_id: str):
    """Get a specific market by ID."""
    if market_id not in state.markets:
        raise HTTPException(status_code=404, detail="Market not found")
    return state.markets[market_id]


@router.post("/{market_id}/bet", response_model=BetResponse)
async def place_bet(market_id: str, bet: BetRequest):
    """Place a bet on a market."""
    if market_id not in state.markets:
        raise HTTPException(status_code=404, detail="Market not found")
    
    market = state.markets[market_id]
    
    if market.status != MarketStatus.OPEN:
        raise HTTPException(status_code=400, detail="Market is not open for betting")
    
    # Calculate price
    price = bet.price or (market.yes_price if bet.side == "yes" else market.no_price)
    
    # Update market volume
    market.volume_24h += bet.amount
    market.total_volume += bet.amount
    
    # Slight price movement based on bet
    if bet.side == "yes":
        market.yes_price = min(0.99, market.yes_price + 0.001)
        market.no_price = max(0.01, 1 - market.yes_price)
    else:
        market.no_price = min(0.99, market.no_price + 0.001)
        market.yes_price = max(0.01, 1 - market.no_price)
    
    return BetResponse(
        bet_id=f"bet_{int(datetime.utcnow().timestamp())}",
        market_id=market_id,
        side=bet.side,
        amount=bet.amount,
        price=price,
        status="confirmed",
        created_at=datetime.utcnow()
    )


@router.get("/{market_id}/orderbook")
async def get_orderbook(market_id: str):
    """Get the order book for a market."""
    if market_id not in state.markets:
        raise HTTPException(status_code=404, detail="Market not found")
    
    market = state.markets[market_id]
    
    # Generate mock orderbook
    return {
        "market_id": market_id,
        "bids": [
            {"price": round(market.yes_price - 0.01 * i, 2), "size": random.randint(100, 1000)}
            for i in range(5)
        ],
        "asks": [
            {"price": round(market.yes_price + 0.01 * i, 2), "size": random.randint(100, 1000)}
            for i in range(1, 6)
        ],
        "last_updated": datetime.utcnow().isoformat()
    }



