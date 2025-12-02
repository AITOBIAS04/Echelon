"""
Event Orchestration System for Project Seed
=============================================
Manages the full lifecycle of betting events:

1. Event Ingestion (from news APIs)
2. Virality Scoring (filter boring events)
3. Bet Duration Classification (Micro/Narrative/Macro)
4. Market Creation (auto-create betting markets)
5. Agent Dispatch (wake up relevant agents)

The Three-Tier Pulse:
- MICRO (24h): High-frequency volatility - Daily price closes, fantasy points
- NARRATIVE (7d): Developing stories - Poll shifts, weekly match results
- MACRO (30-90d): Major shifts - Earnings, elections, league champions

Integrated APIs:
- News: GNews, NewsAPI, NewsData, TheNewsAPI, Marketaux
- Finance: Alpha Vantage, CryptoCompare
- Sports: API-Sports, TheSportsDB, Football-Data

Usage:
    from core.event_orchestrator import EventOrchestrator
    
    orchestrator = EventOrchestrator()
    events = orchestrator.ingest_all()
    hot_events = orchestrator.filter_by_virality(events, min_score=50)
"""

import os
import sys
import json
import asyncio
import requests
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
import hashlib
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Sentiment analysis
try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
except ImportError:
    SentimentIntensityAnalyzer = None

# Path setup for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from backend.agents.schemas import (
        AgentDomain,
        FinancialArchetype,
        AthleticArchetype,
        PoliticalArchetype,
        FinancialAgent,
        AthleticAgent,
        PoliticalAgent,
        create_random_financial_agent,
        create_random_athletic_agent,
        create_random_political_agent,
    )
except ImportError:
    try:
        from agents.schemas import (
            AgentDomain,
            FinancialArchetype,
            AthleticArchetype,
            PoliticalArchetype,
            FinancialAgent,
            AthleticAgent,
            PoliticalAgent,
            create_random_financial_agent,
            create_random_athletic_agent,
            create_random_political_agent,
        )
    except ImportError:
        # Fallback if schemas not available
        AgentDomain = None
        FinancialArchetype = None




# =============================================================================
# API CONFIGURATION - All Keys from .env
# =============================================================================

class APIConfig:
    """
    Centralized API configuration - loads from environment variables.
    
    All API keys should be stored in backend/.env
    """
    
    # --- NEWS APIs ---
    GNEWS_API_KEY = os.getenv("GNEWS_API_KEY", "")
    NEWSAPI_API_KEY = os.getenv("NEWSAPI_API_KEY", "")
    NEWSDATA_API_KEY = os.getenv("NEWSDATA_API_KEY", "")
    THENEWSAPI_API_KEY = os.getenv("THENEWSAPI_API_KEY", "")
    MARKETAUX_API_KEY = os.getenv("MARKETAUX_API_KEY", "")
    
    # --- FINANCIAL APIs ---
    ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY", "")
    CRYPTOCOMPARE_API_KEY = os.getenv("CRYPTOCOMPARE_API_KEY", "")
    
    # --- SPORTS APIs ---
    FOOTBALL_DATA_API_KEY = os.getenv("FOOTBALL_DATA_API_KEY", "")
    API_SPORTS_API_KEY = os.getenv("API_SPORTS_API_KEY", "")
    THESPORTSDB_API_KEY = os.getenv("THESPORTSDB_API_KEY", "3")  # Free key is "3"
    
    # --- AI ---
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    
    @classmethod
    def print_status(cls):
        """Print which APIs are configured."""
        print("\n📊 API Configuration Status:")
        print("=" * 50)
        
        apis = {
            "GNews": cls.GNEWS_API_KEY,
            "NewsAPI": cls.NEWSAPI_API_KEY,
            "NewsData": cls.NEWSDATA_API_KEY,
            "TheNewsAPI": cls.THENEWSAPI_API_KEY,
            "Marketaux": cls.MARKETAUX_API_KEY,
            "Alpha Vantage": cls.ALPHA_VANTAGE_API_KEY,
            "CryptoCompare": cls.CRYPTOCOMPARE_API_KEY,
            "Football-Data": cls.FOOTBALL_DATA_API_KEY,
            "API-Sports": cls.API_SPORTS_API_KEY,
            "TheSportsDB": cls.THESPORTSDB_API_KEY,
        }
        
        for name, key in apis.items():
            status = "✅" if key else "❌"
            masked = f"{key[:8]}..." if key and len(key) > 8 else key or "Not set"
            print(f"   {status} {name}: {masked}")
        
        print("=" * 50)




class ViralityConfig:
    """Virality scoring thresholds."""
    AUTO_MARKET_THRESHOLD = 80   # Auto-create betting market
    AGENT_REACT_THRESHOLD = 50   # Log for agents to react
    IGNORE_THRESHOLD = 50        # Below this = noise
    
    SOCIAL_VOLUME_WEIGHT = 0.5
    NEWS_VELOCITY_WEIGHT = 0.3
    MARKET_VOLATILITY_WEIGHT = 0.2
    
    HOURLY_DECAY = 0.95




# =============================================================================
# ENUMS AND DATA STRUCTURES
# =============================================================================

class BetDuration(str, Enum):
    """The Three-Tier Pulse."""
    MICRO = "micro"         # 24 hours
    NARRATIVE = "narrative" # 7 days
    MACRO = "macro"         # 30-90 days




class EventDomain(str, Enum):
    """Domain classification for events."""
    FINANCE = "finance"
    SPORTS = "sports"
    POLITICS = "politics"
    CRYPTO = "crypto"
    GEOPOLITICS = "geopolitics"
    ENTERTAINMENT = "entertainment"
    UNKNOWN = "unknown"




@dataclass
class RawEvent:
    """A raw event from news/API sources."""
    id: str
    title: str
    description: str
    source: str
    url: str
    published_at: datetime
    domain: EventDomain = EventDomain.UNKNOWN
    
    # Enrichment data
    sentiment: float = 0.0
    social_volume: int = 0
    news_velocity: int = 1
    related_asset: Optional[str] = None
    asset_volatility: float = 0.0
    
    # Computed
    virality_score: float = 0.0
    
    # Optional metadata
    entities: List[str] = field(default_factory=list)
    categories: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            **asdict(self),
            "published_at": self.published_at.isoformat(),
        }




@dataclass
class BettingMarket:
    """A betting market created from an event."""
    id: str
    event_id: str
    title: str
    description: str
    domain: EventDomain
    duration: BetDuration
    
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    
    status: str = "OPEN"
    total_volume: float = 0.0
    
    outcomes: List[str] = field(default_factory=list)
    outcome_odds: Dict[str, float] = field(default_factory=dict)
    
    winning_outcome: Optional[str] = None
    virality_score: float = 0.0
    source_event: Optional[RawEvent] = None
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "event_id": self.event_id,
            "title": self.title,
            "description": self.description,
            "domain": self.domain.value,
            "duration": self.duration.value,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "status": self.status,
            "total_volume": self.total_volume,
            "outcomes": self.outcomes,
            "outcome_odds": self.outcome_odds,
            "virality_score": self.virality_score,
        }




# =============================================================================
# DOMAIN CLASSIFICATION
# =============================================================================

DOMAIN_KEYWORDS = {
    EventDomain.FINANCE: [
        "stock", "market", "earnings", "revenue", "profit", "loss",
        "nasdaq", "dow", "s&p", "fed", "interest rate", "inflation",
        "trading", "investor", "shares", "dividend", "ipo", "merger",
        "acquisition", "quarterly", "fiscal", "gdp", "economy"
    ],
    EventDomain.CRYPTO: [
        "bitcoin", "btc", "ethereum", "eth", "crypto", "blockchain",
        "defi", "nft", "token", "wallet", "exchange", "binance",
        "coinbase", "altcoin", "mining", "staking", "web3"
    ],
    EventDomain.SPORTS: [
        "football", "soccer", "nba", "nfl", "premier league", "la liga",
        "champions league", "world cup", "match", "game", "score",
        "player", "team", "coach", "transfer", "injury", "goal",
        "championship", "playoff", "tournament", "season"
    ],
    EventDomain.POLITICS: [
        "election", "vote", "poll", "president", "congress", "senate",
        "democrat", "republican", "campaign", "candidate", "party",
        "legislation", "policy", "governor", "mayor", "ballot"
    ],
    EventDomain.GEOPOLITICS: [
        "war", "conflict", "military", "sanctions", "treaty", "alliance",
        "nato", "un", "diplomacy", "tension", "crisis", "nuclear",
        "invasion", "territory", "border", "refugee"
    ],
}




def classify_domain(text: str) -> EventDomain:
    """Classify text into a domain based on keywords."""
    text_lower = text.lower()
    
    scores = {}
    for domain, keywords in DOMAIN_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text_lower)
        scores[domain] = score
    
    if max(scores.values()) == 0:
        return EventDomain.UNKNOWN
    
    return max(scores, key=scores.get)




def classify_duration(event: RawEvent) -> BetDuration:
    """Classify event into bet duration tier."""
    text = (event.title + " " + event.description).lower()
    
    macro_keywords = [
        "quarterly", "earnings", "election", "championship", "season",
        "annual", "fiscal year", "world cup", "super bowl"
    ]
    if any(kw in text for kw in macro_keywords):
        return BetDuration.MACRO
    
    micro_keywords = [
        "breaking", "just in", "today", "tonight", "now", "live",
        "price", "trading", "intraday", "hourly"
    ]
    if any(kw in text for kw in micro_keywords):
        return BetDuration.MICRO
    
    if event.virality_score > 80:
        return BetDuration.MICRO
    
    return BetDuration.NARRATIVE




# =============================================================================
# VIRALITY CALCULATOR
# =============================================================================

class ViralityCalculator:
    """Calculate virality score for events."""
    
    def __init__(self, config: ViralityConfig = None):
        self.config = config or ViralityConfig()
    
    def calculate(self, event: RawEvent) -> float:
        """Calculate virality score (0-100)."""
        
        social_score = min(100, event.social_volume / 10)
        velocity_score = min(100, event.news_velocity * 5)
        volatility_score = min(100, event.asset_volatility * 2000)
        sentiment_bonus = abs(event.sentiment) * 20
        
        raw_score = (
            social_score * self.config.SOCIAL_VOLUME_WEIGHT +
            velocity_score * self.config.NEWS_VELOCITY_WEIGHT +
            volatility_score * self.config.MARKET_VOLATILITY_WEIGHT +
            sentiment_bonus
        )
        
        hours_old = (datetime.now(timezone.utc) - event.published_at.replace(tzinfo=timezone.utc)).total_seconds() / 3600
        decay = self.config.HOURLY_DECAY ** hours_old
        
        final_score = raw_score * decay
        
        return round(min(100, max(0, final_score)), 1)




# =============================================================================
# NEWS API CLIENTS
# =============================================================================

class NewsIngester:
    """
    Fetches and processes news from multiple sources.
    
    Supported APIs:
    - GNews (gnews.io)
    - NewsAPI (newsapi.org)
    - NewsData (newsdata.io)
    - TheNewsAPI (thenewsapi.com)
    - Marketaux (marketaux.com) - Financial news with entity detection
    """
    
    def __init__(self, config: APIConfig = None):
        self.config = config or APIConfig()
        self.analyzer = SentimentIntensityAnalyzer() if SentimentIntensityAnalyzer else None
        self.virality_calc = ViralityCalculator()
    
    def _analyze_sentiment(self, text: str) -> float:
        """Analyze sentiment of text. Returns -1 to +1."""
        if not self.analyzer:
            return 0.0
        return self.analyzer.polarity_scores(text)['compound']
    
    def _parse_date(self, date_str: str) -> datetime:
        """Parse various date formats."""
        if not date_str:
            return datetime.now(timezone.utc)
        
        try:
            if "T" in date_str:
                return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            else:
                return datetime.now(timezone.utc)
        except:
            return datetime.now(timezone.utc)
    
    def _generate_id(self, title: str, url: str) -> str:
        """Generate unique ID for an event."""
        return hashlib.md5(f"{title}{url}".encode()).hexdigest()[:12]
    
    # -------------------------------------------------------------------------
    # GNews (gnews.io)
    # -------------------------------------------------------------------------
    def fetch_gnews(self, query: str, max_results: int = 10) -> List[RawEvent]:
        """Fetch from GNews API."""
        if not self.config.GNEWS_API_KEY:
            return []
        
        events = []
        try:
            url = "https://gnews.io/api/v4/search"
            params = {
                "q": query,
                "lang": "en",
                "max": max_results,
                "apikey": self.config.GNEWS_API_KEY
            }
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                for article in data.get("articles", []):
                    if article.get("title"):
                        event = RawEvent(
                            id=self._generate_id(article["title"], article.get("url", "")),
                            title=article["title"],
                            description=article.get("description", "")[:500],
                            source="GNews",
                            url=article.get("url", ""),
                            published_at=self._parse_date(article.get("publishedAt")),
                        )
                        event.sentiment = self._analyze_sentiment(f"{event.title} {event.description}")
                        event.domain = classify_domain(f"{event.title} {event.description}")
                        events.append(event)
                print(f"✅ GNews: {len(events)} articles")
            else:
                print(f"⚠️ GNews Error {response.status_code}")
        except Exception as e:
            print(f"❌ GNews Exception: {e}")
        
        return events
    
    # -------------------------------------------------------------------------
    # NewsAPI (newsapi.org)
    # -------------------------------------------------------------------------
    def fetch_newsapi(self, query: str, max_results: int = 10) -> List[RawEvent]:
        """Fetch from NewsAPI.org."""
        if not self.config.NEWSAPI_API_KEY:
            return []
        
        events = []
        try:
            url = "https://newsapi.org/v2/everything"
            params = {
                "q": query,
                "language": "en",
                "pageSize": max_results,
                "sortBy": "publishedAt",
                "apiKey": self.config.NEWSAPI_API_KEY
            }
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                for article in data.get("articles", []):
                    if article.get("title"):
                        event = RawEvent(
                            id=self._generate_id(article["title"], article.get("url", "")),
                            title=article["title"],
                            description=article.get("description", "")[:500],
                            source="NewsAPI",
                            url=article.get("url", ""),
                            published_at=self._parse_date(article.get("publishedAt")),
                        )
                        event.sentiment = self._analyze_sentiment(f"{event.title} {event.description}")
                        event.domain = classify_domain(f"{event.title} {event.description}")
                        events.append(event)
                print(f"✅ NewsAPI: {len(events)} articles")
            elif "developer" in response.text.lower():
                print("⚠️ NewsAPI: Free tier limit reached")
            else:
                print(f"⚠️ NewsAPI Error {response.status_code}")
        except Exception as e:
            print(f"❌ NewsAPI Exception: {e}")
        
        return events
    
    # -------------------------------------------------------------------------
    # NewsData (newsdata.io)
    # -------------------------------------------------------------------------
    def fetch_newsdata(self, query: str, max_results: int = 10) -> List[RawEvent]:
        """Fetch from NewsData.io."""
        if not self.config.NEWSDATA_API_KEY:
            return []
        
        events = []
        try:
            url = "https://newsdata.io/api/1/latest"
            params = {
                "apikey": self.config.NEWSDATA_API_KEY,
                "q": query,
                "language": "en"
            }
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                for article in data.get("results", []):
                    if article.get("title"):
                        event = RawEvent(
                            id=self._generate_id(article["title"], article.get("link", "")),
                            title=article["title"],
                            description=article.get("description", "")[:500] if article.get("description") else "",
                            source="NewsData",
                            url=article.get("link", ""),
                            published_at=self._parse_date(article.get("pubDate")),
                            categories=article.get("category", []),
                        )
                        event.sentiment = self._analyze_sentiment(f"{event.title} {event.description}")
                        event.domain = classify_domain(f"{event.title} {event.description}")
                        events.append(event)
                print(f"✅ NewsData: {len(events)} articles")
            else:
                print(f"⚠️ NewsData Error {response.status_code}")
        except Exception as e:
            print(f"❌ NewsData Exception: {e}")
        
        return events
    
    # -------------------------------------------------------------------------
    # TheNewsAPI (thenewsapi.com)
    # -------------------------------------------------------------------------
    def fetch_thenewsapi(self, query: str, max_results: int = 10) -> List[RawEvent]:
        """Fetch from TheNewsAPI.com."""
        if not self.config.THENEWSAPI_API_KEY:
            return []
        
        events = []
        try:
            url = "https://api.thenewsapi.com/v1/news/all"
            params = {
                "api_token": self.config.THENEWSAPI_API_KEY,
                "search": query,
                "language": "en",
                "limit": max_results,
            }
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                for article in data.get("data", []):
                    if article.get("title"):
                        event = RawEvent(
                            id=self._generate_id(article["title"], article.get("url", "")),
                            title=article["title"],
                            description=article.get("description", "")[:500] if article.get("description") else "",
                            source="TheNewsAPI",
                            url=article.get("url", ""),
                            published_at=self._parse_date(article.get("published_at")),
                            categories=article.get("categories", []),
                        )
                        event.sentiment = self._analyze_sentiment(f"{event.title} {event.description}")
                        event.domain = classify_domain(f"{event.title} {event.description}")
                        events.append(event)
                print(f"✅ TheNewsAPI: {len(events)} articles")
            else:
                print(f"⚠️ TheNewsAPI Error {response.status_code}")
        except Exception as e:
            print(f"❌ TheNewsAPI Exception: {e}")
        
        return events
    
    # -------------------------------------------------------------------------
    # Marketaux (marketaux.com) - Financial News with Entity Detection
    # -------------------------------------------------------------------------
    def fetch_marketaux(self, symbols: str = None, max_results: int = 10) -> List[RawEvent]:
        """
        Fetch from Marketaux - specialized for financial news.
        
        Features:
        - Entity detection (stocks, ETFs, crypto)
        - Sentiment scores per entity
        - Relevance scoring
        """
        if not self.config.MARKETAUX_API_KEY:
            return []
        
        events = []
        try:
            url = "https://api.marketaux.com/v1/news/all"
            params = {
                "api_token": self.config.MARKETAUX_API_KEY,
                "language": "en",
                "limit": max_results,
            }
            if symbols:
                params["symbols"] = symbols  # e.g., "AAPL,TSLA,MSFT"
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                for article in data.get("data", []):
                    if article.get("title"):
                        # Extract entities (stocks mentioned)
                        entities = []
                        entity_sentiment = 0.0
                        for entity in article.get("entities", []):
                            entities.append(entity.get("symbol", ""))
                            if entity.get("sentiment_score"):
                                entity_sentiment = entity["sentiment_score"]
                        
                        event = RawEvent(
                            id=self._generate_id(article["title"], article.get("url", "")),
                            title=article["title"],
                            description=article.get("description", "")[:500] if article.get("description") else "",
                            source="Marketaux",
                            url=article.get("url", ""),
                            published_at=self._parse_date(article.get("published_at")),
                            entities=entities,
                            related_asset=entities[0] if entities else None,
                        )
                        # Use entity sentiment if available, otherwise analyze
                        event.sentiment = entity_sentiment if entity_sentiment else self._analyze_sentiment(f"{event.title} {event.description}")
                        event.domain = EventDomain.FINANCE if entities else classify_domain(f"{event.title} {event.description}")
                        events.append(event)
                print(f"✅ Marketaux: {len(events)} articles")
            else:
                print(f"⚠️ Marketaux Error {response.status_code}")
        except Exception as e:
            print(f"❌ Marketaux Exception: {e}")
        
        return events
    
    # -------------------------------------------------------------------------
    # Combined Fetch
    # -------------------------------------------------------------------------
    def fetch_all(self, queries: List[str] = None) -> List[RawEvent]:
        """Fetch events from all news sources."""
        if queries is None:
            queries = [
                "stock market",
                "cryptocurrency bitcoin",
                "premier league football",
                "election polls",
                "geopolitics conflict"
            ]
        
        all_events = []
        seen_ids = set()
        
        for query in queries:
            print(f"\n📰 Fetching: {query}")
            
            # Fetch from all sources
            for event in self.fetch_gnews(query, 5):
                if event.id not in seen_ids:
                    all_events.append(event)
                    seen_ids.add(event.id)
            
            for event in self.fetch_newsapi(query, 5):
                if event.id not in seen_ids:
                    all_events.append(event)
                    seen_ids.add(event.id)
            
            for event in self.fetch_newsdata(query, 5):
                if event.id not in seen_ids:
                    all_events.append(event)
                    seen_ids.add(event.id)
            
            for event in self.fetch_thenewsapi(query, 5):
                if event.id not in seen_ids:
                    all_events.append(event)
                    seen_ids.add(event.id)
        
        # Also fetch financial news from Marketaux
        for event in self.fetch_marketaux("AAPL,TSLA,MSFT,GOOGL,AMZN", 10):
            if event.id not in seen_ids:
                all_events.append(event)
                seen_ids.add(event.id)
        
        # Calculate virality and news velocity
        for event in all_events:
            similar_count = sum(
                1 for e in all_events 
                if e.id != event.id and e.domain == event.domain
            )
            event.news_velocity = similar_count + 1
            event.virality_score = self.virality_calc.calculate(event)
        
        all_events.sort(key=lambda e: e.virality_score, reverse=True)
        
        print(f"\n✅ Total: {len(all_events)} unique events")
        
        return all_events




# =============================================================================
# FINANCIAL DATA CLIENTS
# =============================================================================

class FinancialDataClient:
    """
    Fetch financial market data for volatility calculation.
    
    APIs:
    - Alpha Vantage: Stock prices, forex, crypto
    - CryptoCompare: Cryptocurrency prices and news
    """
    
    def __init__(self, config: APIConfig = None):
        self.config = config or APIConfig()
    
    def get_stock_quote(self, symbol: str) -> Dict:
        """Get stock quote from Alpha Vantage."""
        if not self.config.ALPHA_VANTAGE_API_KEY:
            return {}
        
        try:
            url = "https://www.alphavantage.co/query"
            params = {
                "function": "GLOBAL_QUOTE",
                "symbol": symbol,
                "apikey": self.config.ALPHA_VANTAGE_API_KEY
            }
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                quote = data.get("Global Quote", {})
                return {
                    "symbol": quote.get("01. symbol"),
                    "price": float(quote.get("05. price", 0)),
                    "change": float(quote.get("09. change", 0)),
                    "change_percent": quote.get("10. change percent", "0%"),
                }
        except Exception as e:
            print(f"❌ Alpha Vantage Exception: {e}")
        
        return {}
    
    def get_market_news(self, tickers: str = None) -> List[Dict]:
        """Get market news from Alpha Vantage."""
        if not self.config.ALPHA_VANTAGE_API_KEY:
            return []
        
        try:
            url = "https://www.alphavantage.co/query"
            params = {
                "function": "NEWS_SENTIMENT",
                "apikey": self.config.ALPHA_VANTAGE_API_KEY
            }
            if tickers:
                params["tickers"] = tickers
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return data.get("feed", [])
        except Exception as e:
            print(f"❌ Alpha Vantage News Exception: {e}")
        
        return []
    
    def get_crypto_price(self, symbol: str = "BTC") -> Dict:
        """Get crypto price from CryptoCompare."""
        if not self.config.CRYPTOCOMPARE_API_KEY:
            return {}
        
        try:
            url = "https://min-api.cryptocompare.com/data/price"
            params = {
                "fsym": symbol,
                "tsyms": "USD,EUR,GBP",
            }
            headers = {
                "authorization": f"Apikey {self.config.CRYPTOCOMPARE_API_KEY}"
            }
            response = requests.get(url, params=params, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "symbol": symbol,
                    "price_usd": data.get("USD"),
                    "price_eur": data.get("EUR"),
                    "price_gbp": data.get("GBP"),
                }
        except Exception as e:
            print(f"❌ CryptoCompare Exception: {e}")
        
        return {}
    
    def get_crypto_news(self) -> List[Dict]:
        """Get crypto news from CryptoCompare."""
        if not self.config.CRYPTOCOMPARE_API_KEY:
            return []
        
        try:
            url = "https://min-api.cryptocompare.com/data/v2/news/"
            params = {"lang": "EN"}
            headers = {
                "authorization": f"Apikey {self.config.CRYPTOCOMPARE_API_KEY}"
            }
            response = requests.get(url, params=params, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return data.get("Data", [])
        except Exception as e:
            print(f"❌ CryptoCompare News Exception: {e}")
        
        return []




# =============================================================================
# SPORTS DATA CLIENTS
# =============================================================================

class SportsDataClient:
    """
    Fetch sports data for event creation.
    
    APIs:
    - API-Sports: Football, NBA, NFL, F1, MMA (100 req/day free)
    - TheSportsDB: Free, crowdsourced sports database
    - Football-Data: Premier League, Champions League
    """
    
    def __init__(self, config: APIConfig = None):
        self.config = config or APIConfig()
    
    # -------------------------------------------------------------------------
    # API-Sports (api-sports.io)
    # -------------------------------------------------------------------------
    def get_football_fixtures(self, league_id: int = 39, season: int = 2024) -> List[Dict]:
        """
        Get football fixtures from API-Sports.
        
        League IDs:
        - 39: Premier League
        - 140: La Liga
        - 135: Serie A
        - 78: Bundesliga
        - 61: Ligue 1
        """
        if not self.config.API_SPORTS_API_KEY:
            return []
        
        try:
            url = "https://v3.football.api-sports.io/fixtures"
            params = {
                "league": league_id,
                "season": season,
                "next": 10,  # Next 10 fixtures
            }
            headers = {
                "x-apisports-key": self.config.API_SPORTS_API_KEY
            }
            response = requests.get(url, params=params, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                fixtures = data.get("response", [])
                print(f"✅ API-Sports: {len(fixtures)} fixtures")
                return fixtures
        except Exception as e:
            print(f"❌ API-Sports Exception: {e}")
        
        return []
    
    def get_live_scores(self, league_id: int = 39) -> List[Dict]:
        """Get live football scores."""
        if not self.config.API_SPORTS_API_KEY:
            return []
        
        try:
            url = "https://v3.football.api-sports.io/fixtures"
            params = {"live": "all"}
            if league_id:
                params["league"] = league_id
            
            headers = {
                "x-apisports-key": self.config.API_SPORTS_API_KEY
            }
            response = requests.get(url, params=params, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return data.get("response", [])
        except Exception as e:
            print(f"❌ API-Sports Live Exception: {e}")
        
        return []
    
    # -------------------------------------------------------------------------
    # TheSportsDB (thesportsdb.com) - FREE
    # -------------------------------------------------------------------------
    def get_sportsdb_events(self, league_id: str = "4328") -> List[Dict]:
        """
        Get events from TheSportsDB.
        
        League IDs:
        - 4328: English Premier League
        - 4331: German Bundesliga
        - 4335: Spanish La Liga
        - 4332: Italian Serie A
        """
        try:
            url = f"https://www.thesportsdb.com/api/v1/json/{self.config.THESPORTSDB_API_KEY}/eventsnextleague.php"
            params = {"id": league_id}
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                events = data.get("events", []) or []
                print(f"✅ TheSportsDB: {len(events)} events")
                return events
        except Exception as e:
            print(f"❌ TheSportsDB Exception: {e}")
        
        return []
    
    def get_sportsdb_livescores(self, sport: str = "Soccer") -> List[Dict]:
        """Get live scores from TheSportsDB."""
        try:
            url = f"https://www.thesportsdb.com/api/v1/json/{self.config.THESPORTSDB_API_KEY}/livescore.php"
            params = {"s": sport}
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return data.get("events", []) or []
        except Exception as e:
            print(f"❌ TheSportsDB Live Exception: {e}")
        
        return []
    
    # -------------------------------------------------------------------------
    # Football-Data.org
    # -------------------------------------------------------------------------
    def get_footballdata_matches(self, competition: str = "PL") -> List[Dict]:
        """
        Get matches from Football-Data.org.
        
        Competitions:
        - PL: Premier League
        - CL: Champions League
        - BL1: Bundesliga
        - SA: Serie A
        - PD: La Liga
        """
        if not self.config.FOOTBALL_DATA_API_KEY:
            return []
        
        try:
            url = f"https://api.football-data.org/v4/competitions/{competition}/matches"
            params = {"status": "SCHEDULED"}
            headers = {
                "X-Auth-Token": self.config.FOOTBALL_DATA_API_KEY
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                matches = data.get("matches", [])
                print(f"✅ Football-Data: {len(matches)} matches")
                return matches
        except Exception as e:
            print(f"❌ Football-Data Exception: {e}")
        
        return []




# =============================================================================
# AGENT DISPATCHER
# =============================================================================

class AgentDispatcher:
    """Dispatches relevant agents to betting markets."""
    
    DOMAIN_AGENTS = {
        EventDomain.FINANCE: {
            "primary": ["whale", "shark", "value"],
            "secondary": ["momentum", "degen"],
            "chaos": ["noise"],
        },
        EventDomain.CRYPTO: {
            "primary": ["shark", "degen"],
            "secondary": ["momentum"],
            "chaos": ["noise"],
        },
        EventDomain.SPORTS: {
            "primary": ["star", "veteran"],
            "secondary": ["workhorse"],
            "chaos": ["glass"],
        },
        EventDomain.POLITICS: {
            "primary": ["populist", "technocrat"],
            "secondary": ["moderate", "ideologue"],
            "chaos": ["instigator"],
        },
    }
    
    DURATION_POOL_SIZE = {
        BetDuration.MICRO: {"primary": 5, "secondary": 10, "chaos": 3},
        BetDuration.NARRATIVE: {"primary": 10, "secondary": 15, "chaos": 2},
        BetDuration.MACRO: {"primary": 20, "secondary": 10, "chaos": 1},
    }
    
    def __init__(self):
        self.active_agents: Dict[str, List] = {}
    
    def spawn_agents(self, market: BettingMarket) -> List:
        """Spawn agents appropriate for this market."""
        domain = market.domain
        duration = market.duration
        
        archetypes = self.DOMAIN_AGENTS.get(domain, self.DOMAIN_AGENTS[EventDomain.FINANCE])
        pool_sizes = self.DURATION_POOL_SIZE[duration]
        
        agents = []
        
        # Simplified agent spawning (uses schemas if available)
        total_agents = (
            pool_sizes["primary"] + 
            pool_sizes["secondary"] + 
            pool_sizes["chaos"]
        )
        
        for i in range(total_agents):
            agent = {
                "id": f"agent_{market.id}_{i}",
                "domain": domain.value,
                "role": "primary" if i < pool_sizes["primary"] else "secondary" if i < pool_sizes["primary"] + pool_sizes["secondary"] else "chaos",
            }
            agents.append(agent)
        
        self.active_agents[market.id] = agents
        print(f"🤖 Dispatched {len(agents)} agents to market {market.id}")
        
        return agents
    
    def retire_agents(self, market_id: str) -> None:
        """Remove agents when market closes."""
        if market_id in self.active_agents:
            count = len(self.active_agents[market_id])
            del self.active_agents[market_id]
            print(f"🔚 Retired {count} agents from market {market_id}")




# =============================================================================
# EVENT ORCHESTRATOR (Main Interface)
# =============================================================================

class EventOrchestrator:
    """
    The main interface for event orchestration.
    
    Combines news ingestion, virality scoring, market creation, and agent dispatch.
    Now with persistence - markets survive server restarts!
    """
    
    def __init__(self):
        self.ingester = NewsIngester()
        self.financial_client = FinancialDataClient()
        self.sports_client = SportsDataClient()
        self.virality_calc = ViralityCalculator()
        self.dispatcher = AgentDispatcher()
        
        self.events: List[RawEvent] = []
        self.markets: Dict[str, BettingMarket] = {}
        
        self.stats = {
            "events_processed": 0,
            "markets_created": 0,
            "markets_auto_created": 0,
        }
        
        # Initialize persistence
        try:
            from backend.core.persistence_manager import get_persistence_manager
            self.persistence = get_persistence_manager()
        except ImportError:
            try:
                from core.persistence_manager import get_persistence_manager
                self.persistence = get_persistence_manager()
            except ImportError:
                self.persistence = None
                print("⚠️ Persistence manager not available for EventOrchestrator")
        
        # Load saved markets on startup
        if self.persistence:
            self._load_markets_state()
    
    def ingest_events(self, queries: List[str] = None) -> List[RawEvent]:
        """Fetch and process events from news sources."""
        self.events = self.ingester.fetch_all(queries)
        self.stats["events_processed"] += len(self.events)
        return self.events
    
    def ingest_sports_events(self) -> List[RawEvent]:
        """Fetch sports fixtures and convert to events."""
        sports_events = []
        
        # TheSportsDB (free)
        for match in self.sports_client.get_sportsdb_events("4328"):  # Premier League
            event = RawEvent(
                id=f"sport_{match.get('idEvent', '')}",
                title=f"{match.get('strEvent', 'Unknown Match')}",
                description=f"{match.get('strHomeTeam')} vs {match.get('strAwayTeam')} - {match.get('strLeague')}",
                source="TheSportsDB",
                url=f"https://www.thesportsdb.com/event/{match.get('idEvent')}",
                published_at=self._parse_date(match.get('dateEvent')),
                domain=EventDomain.SPORTS,
            )
            event.virality_score = 60  # Base virality for scheduled matches
            sports_events.append(event)
        
        # Football-Data.org
        for match in self.sports_client.get_footballdata_matches("PL"):
            event = RawEvent(
                id=f"fd_{match.get('id', '')}",
                title=f"{match.get('homeTeam', {}).get('name')} vs {match.get('awayTeam', {}).get('name')}",
                description=f"Premier League Matchday {match.get('matchday')}",
                source="Football-Data",
                url="https://www.football-data.org/",
                published_at=self._parse_date(match.get('utcDate')),
                domain=EventDomain.SPORTS,
            )
            event.virality_score = 65
            sports_events.append(event)
        
        return sports_events
    
    def _parse_date(self, date_str: str) -> datetime:
        """Parse various date formats."""
        if not date_str:
            return datetime.now(timezone.utc)
        try:
            if "T" in str(date_str):
                return datetime.fromisoformat(str(date_str).replace("Z", "+00:00"))
            else:
                return datetime.strptime(str(date_str), "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except:
            return datetime.now(timezone.utc)
    
    def filter_by_virality(self, events: List[RawEvent] = None, 
                           min_score: float = 50) -> List[RawEvent]:
        """Filter events by minimum virality score."""
        events = events or self.events
        return [e for e in events if e.virality_score >= min_score]
    
    def create_market(self, event: RawEvent) -> BettingMarket:
        """Create a betting market from an event."""
        duration = classify_duration(event)
        
        duration_hours = {
            BetDuration.MICRO: 24,
            BetDuration.NARRATIVE: 168,
            BetDuration.MACRO: 720,
        }
        expires_at = datetime.now() + timedelta(hours=duration_hours[duration])
        
        market_id = f"MKT_{event.id}_{duration.value}"
        
        market = BettingMarket(
            id=market_id,
            event_id=event.id,
            title=event.title[:100],
            description=event.description[:200],
            domain=event.domain,
            duration=duration,
            expires_at=expires_at,
            outcomes=["YES", "NO"],
            outcome_odds={"YES": 0.5, "NO": 0.5},
            virality_score=event.virality_score,
            source_event=event,
        )
        
        self.markets[market_id] = market
        self.stats["markets_created"] += 1
        
        # Save markets state after creation
        self._save_markets_state()
        
        print(f"📊 Created market: {market_id} ({duration.value})")
        
        return market
    
    def dispatch_agents(self, market: BettingMarket) -> List:
        """Spawn and dispatch agents to a market."""
        return self.dispatcher.spawn_agents(market)
    
    def process_all(self) -> Dict[str, Any]:
        """Full pipeline: ingest -> filter -> create markets -> dispatch."""
        # News events
        events = self.ingest_events()
        
        # Sports events
        sports_events = self.ingest_sports_events()
        events.extend(sports_events)
        
        # Filter and create markets
        auto_market_events = self.filter_by_virality(events, ViralityConfig.AUTO_MARKET_THRESHOLD)
        
        created_markets = []
        for event in auto_market_events:
            market = self.create_market(event)
            self.dispatch_agents(market)
            created_markets.append(market)
            self.stats["markets_auto_created"] += 1
        
        return {
            "events_ingested": len(events),
            "high_virality_events": len(auto_market_events),
            "markets_created": len(created_markets),
            "stats": self.stats,
        }
    
    def get_markets_by_duration(self, duration: BetDuration) -> List[BettingMarket]:
        """Get all markets of a specific duration tier."""
        return [m for m in self.markets.values() if m.duration == duration]
    
    def get_active_markets(self) -> List[BettingMarket]:
        """Get all open markets."""
        return [m for m in self.markets.values() if m.status == "OPEN"]
    
    def _save_markets_state(self):
        """Save all markets to disk."""
        if not self.persistence:
            return
        
        markets_data = {}
        for market_id, market in self.markets.items():
            markets_data[market_id] = {
                "id": market.id,
                "event_id": market.event_id,
                "title": market.title,
                "description": market.description,
                "domain": market.domain.value if hasattr(market.domain, "value") else market.domain,
                "duration": market.duration.value if hasattr(market.duration, "value") else market.duration,
                "status": market.status,
                "created_at": market.created_at.isoformat() if hasattr(market.created_at, "isoformat") else str(market.created_at),
                "expires_at": market.expires_at.isoformat() if market.expires_at and hasattr(market.expires_at, "isoformat") else None,
                "outcomes": market.outcomes,
                "outcome_odds": market.outcome_odds,
                "total_volume": market.total_volume,
                "virality_score": market.virality_score,
            }
        
        self.persistence.save("markets", markets_data)
        self.persistence.save("stats", self.stats)
    
    def _load_markets_state(self):
        """Load markets from disk and restore BettingMarket objects."""
        if not self.persistence:
            return
        
        markets_data = self.persistence.load("markets", default={})
        stats_data = self.persistence.load("stats", default={})
        
        # Restore stats
        if stats_data:
            self.stats.update(stats_data)
        
        # Restore BettingMarket objects from saved data
        for market_id, market_dict in markets_data.items():
            try:
                # Reconstruct BettingMarket from saved data
                market = BettingMarket(
                    id=market_dict["id"],
                    event_id=market_dict.get("event_id", market_id),
                    title=market_dict["title"],
                    description=market_dict.get("description", ""),
                    domain=EventDomain(market_dict["domain"]) if isinstance(market_dict["domain"], str) else market_dict["domain"],
                    duration=BetDuration(market_dict["duration"]) if isinstance(market_dict["duration"], str) else market_dict["duration"],
                    status=market_dict.get("status", "OPEN"),
                    created_at=datetime.fromisoformat(market_dict["created_at"]) if isinstance(market_dict["created_at"], str) else market_dict["created_at"],
                    expires_at=datetime.fromisoformat(market_dict["expires_at"]) if market_dict.get("expires_at") and isinstance(market_dict["expires_at"], str) else market_dict.get("expires_at"),
                    outcomes=market_dict.get("outcomes", ["YES", "NO"]),
                    outcome_odds=market_dict.get("outcome_odds", {"YES": 0.5, "NO": 0.5}),
                    total_volume=market_dict.get("total_volume", 0.0),
                    virality_score=market_dict.get("virality_score", 0.0),
                    source_event=None,  # Source event not saved, can be None
                )
                self.markets[market_id] = market
            except Exception as e:
                print(f"⚠️ Failed to restore market {market_id}: {e}")
                continue
        
        print(f"📂 Loaded {len(self.markets)} markets from disk")




# =============================================================================
# CLI
# =============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Event Orchestrator")
    parser.add_argument("action", choices=["status", "ingest", "sports", "finance", "process", "test"],
                        help="Action to perform")
    parser.add_argument("--query", "-q", help="Custom search query")
    parser.add_argument("--min-virality", "-v", type=float, default=50,
                        help="Minimum virality score")
    
    args = parser.parse_args()
    
    if args.action == "status":
        APIConfig.print_status()
    
    elif args.action == "test":
        print("🧪 Testing Event Orchestrator\n")
        APIConfig.print_status()
        
        # Test mock events
        mock_events = [
            RawEvent(
                id="test1",
                title="Breaking: Apple Stock Surges 5% on AI Announcement",
                description="Apple reveals new AI features",
                source="Test",
                url="http://test.com/1",
                published_at=datetime.now(timezone.utc),
                sentiment=0.8,
                social_volume=500,
                news_velocity=10,
                asset_volatility=0.05,
            ),
        ]
        
        orchestrator = EventOrchestrator()
        for event in mock_events:
            event.domain = classify_domain(event.title)
            event.virality_score = orchestrator.virality_calc.calculate(event)
        
        print(f"\n📊 Mock Event: [{mock_events[0].virality_score:.0f}] {mock_events[0].title[:50]}...")
        
        market = orchestrator.create_market(mock_events[0])
        agents = orchestrator.dispatch_agents(market)
        print(f"   Created market with {len(agents)} agents")
    
    elif args.action == "ingest":
        orchestrator = EventOrchestrator()
        queries = [args.query] if args.query else None
        events = orchestrator.ingest_events(queries)
        
        print(f"\n📰 Events (virality >= {args.min_virality}):")
        for event in events:
            if event.virality_score >= args.min_virality:
                print(f"   [{event.virality_score:.0f}] {event.domain.value}: {event.title[:60]}...")
    
    elif args.action == "sports":
        print("⚽ Fetching Sports Data\n")
        APIConfig.print_status()
        
        client = SportsDataClient()
        
        # TheSportsDB
        events = client.get_sportsdb_events("4328")
        for event in events[:5]:
            print(f"   📅 {event.get('strEvent')} - {event.get('dateEvent')}")
        
        # Football-Data
        matches = client.get_footballdata_matches("PL")
        for match in matches[:5]:
            print(f"   ⚽ {match.get('homeTeam', {}).get('name')} vs {match.get('awayTeam', {}).get('name')}")
    
    elif args.action == "finance":
        print("💹 Fetching Financial Data\n")
        APIConfig.print_status()
        
        client = FinancialDataClient()
        
        # Stock quote
        quote = client.get_stock_quote("AAPL")
        if quote:
            print(f"   📈 AAPL: ${quote.get('price')} ({quote.get('change_percent')})")
        
        # Crypto
        btc = client.get_crypto_price("BTC")
        if btc:
            print(f"   ₿ BTC: ${btc.get('price_usd')}")
    
    elif args.action == "process":
        orchestrator = EventOrchestrator()
        summary = orchestrator.process_all()
        
        print("\n📊 Processing Summary:")
        print(f"   Events ingested: {summary['events_ingested']}")
        print(f"   High virality: {summary['high_virality_events']}")
        print(f"   Markets created: {summary['markets_created']}")
