"""
Mock Data Generator for Project Seed
=====================================
Generates realistic fake data for development and testing
when API limits are a concern.

Enable with: MOCK_MODE=true in .env

Features:
- Realistic headlines across all domains
- Time-varying sentiment and virality
- Consistent market IDs for testing
- Sports fixtures with real team names
- Financial data with realistic movements
"""

import os
import random
import hashlib
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

# Check environment
MOCK_MODE = os.getenv("MOCK_MODE", "false").lower() == "true"

# =============================================================================
# HEADLINE TEMPLATES
# =============================================================================

HEADLINE_TEMPLATES = {
    "finance": [
        "{company} stock {direction} {percent}% on {reason}",
        "Breaking: {company} announces {event}",
        "{company} beats earnings expectations by {percent}%",
        "Analysts {sentiment} on {company} after {event}",
        "{company} CEO says {quote}",
        "Market Watch: {company} faces {challenge}",
        "{company} partners with {partner} for {initiative}",
    ],
    "crypto": [
        "Bitcoin {direction} ${amount} as {reason}",
        "{crypto} surges {percent}% after {event}",
        "Whale alert: {amount} {crypto} moved to {destination}",
        "{exchange} announces {feature} for {crypto}",
        "DeFi protocol {protocol} reaches ${tvl} TVL",
        "{country} considers {action} on cryptocurrency",
        "ETF {sentiment}: {crypto} institutional adoption {direction}",
    ],
    "sports": [
        "{team1} vs {team2}: {event}",
        "{player} {action} ahead of {match}",
        "Transfer news: {player} linked to {team}",
        "{team} manager discusses {topic}",
        "Injury update: {player} {status} for {match}",
        "{league} standings update after matchday {day}",
    ],
    "politics": [
        "{leader} announces {policy} affecting {sector}",
        "Election update: {candidate} {direction} in polls",
        "{country} and {country2} reach {agreement}",
        "Congress debates {bill} with {outcome} expected",
        "{official} resigns amid {controversy}",
        "New regulations proposed for {industry}",
    ],
    "geopolitics": [
        "Tensions rise between {country1} and {country2} over {issue}",
        "{organization} imposes {action} on {country}",
        "{country} military {action} near {region}",
        "Trade dispute: {country1} tariffs on {country2} {goods}",
        "{summit} concludes with {outcome}",
        "Energy crisis: {country} {action} on {resource}",
    ],
}

# Fill-in data
COMPANIES = ["Apple", "Tesla", "NVIDIA", "Google", "Microsoft", "Amazon", "Meta", "Netflix"]
CRYPTOS = ["Bitcoin", "Ethereum", "Solana", "XRP", "Cardano", "Dogecoin"]
TEAMS = ["Manchester United", "Liverpool", "Arsenal", "Chelsea", "Man City", "Tottenham"]
PLAYERS = ["Haaland", "Salah", "Saka", "Palmer", "Foden", "Son"]
COUNTRIES = ["USA", "China", "Russia", "UK", "Germany", "France", "Japan", "India"]
LEADERS = ["Biden", "Xi", "Putin", "Starmer", "Macron", "Scholz"]

# =============================================================================
# MOCK EVENT GENERATOR
# =============================================================================

@dataclass
class MockEvent:
    id: str
    title: str
    description: str
    source: str
    domain: str
    published_at: datetime
    sentiment: float
    virality_score: float

def generate_headline(domain: str) -> tuple[str, str]:
    """Generate a realistic headline for a domain."""
    templates = HEADLINE_TEMPLATES.get(domain, HEADLINE_TEMPLATES["finance"])
    template = random.choice(templates)
    
    # Fill in template
    headline = template.format(
        company=random.choice(COMPANIES),
        crypto=random.choice(CRYPTOS),
        team=random.choice(TEAMS),
        team1=random.choice(TEAMS),
        team2=random.choice([t for t in TEAMS if t != random.choice(TEAMS)]),
        player=random.choice(PLAYERS),
        country=random.choice(COUNTRIES),
        country1=random.choice(COUNTRIES),
        country2=random.choice([c for c in COUNTRIES if c != random.choice(COUNTRIES)]),
        leader=random.choice(LEADERS),
        direction=random.choice(["surges", "drops", "climbs", "falls", "jumps"]),
        percent=random.randint(1, 15),
        amount=random.randint(1000, 50000),
        reason=random.choice(["earnings report", "Fed decision", "market sentiment", "breaking news"]),
        event=random.choice(["major acquisition", "product launch", "leadership change", "strategic pivot"]),
        sentiment=random.choice(["bullish", "bearish", "cautious", "optimistic"]),
        challenge=random.choice(["regulatory scrutiny", "competition", "supply chain issues"]),
        partner=random.choice(COMPANIES),
        initiative=random.choice(["AI development", "cloud services", "sustainability"]),
        exchange=random.choice(["Coinbase", "Binance", "Kraken"]),
        feature=random.choice(["staking", "futures", "spot trading"]),
        destination=random.choice(["cold storage", "exchange", "unknown wallet"]),
        protocol=random.choice(["Uniswap", "Aave", "Compound"]),
        tvl=random.randint(100, 5000),
        action=random.choice(["injured", "fit", "doubtful", "training"]),
        match=random.choice(["weekend fixture", "cup final", "derby match"]),
        topic=random.choice(["tactics", "transfers", "injuries"]),
        status=random.choice(["ruled out", "cleared", "uncertain"]),
        league=random.choice(["Premier League", "Champions League", "FA Cup"]),
        day=random.randint(1, 38),
        policy=random.choice(["tax reform", "infrastructure bill", "trade deal"]),
        sector=random.choice(["tech", "energy", "healthcare", "finance"]),
        candidate=random.choice(["incumbent", "challenger", "third-party"]),
        agreement=random.choice(["trade deal", "peace accord", "climate pact"]),
        bill=random.choice(["spending bill", "reform act", "emergency measure"]),
        outcome=random.choice(["passage", "defeat", "amendment"]),
        official=random.choice(["minister", "secretary", "advisor"]),
        controversy=random.choice(["scandal", "investigation", "allegations"]),
        industry=random.choice(["AI", "crypto", "social media", "banking"]),
        issue=random.choice(["territory", "trade", "resources", "security"]),
        organization=random.choice(["UN", "EU", "NATO", "WTO"]),
        region=random.choice(["Taiwan Strait", "Eastern Europe", "Middle East"]),
        goods=random.choice(["steel", "semiconductors", "agricultural products"]),
        summit=random.choice(["G7 Summit", "Climate Conference", "Trade Talks"]),
        resource=random.choice(["oil", "gas", "rare earths"]),
        quote=random.choice([
            "'AI will transform our business'",
            "'We're just getting started'",
            "'This is a pivotal moment'",
        ]),
    )
    
    description = f"Market simulation for: {headline}. Betting ends soon."
    return headline, description

def generate_mock_events(count: int = 10, domain: str = None) -> List[MockEvent]:
    """Generate a list of mock events."""
    events = []
    domains = [domain] if domain else list(HEADLINE_TEMPLATES.keys())
    
    for i in range(count):
        event_domain = random.choice(domains)
        title, description = generate_headline(event_domain)
        
        # Generate consistent ID based on title
        event_id = hashlib.md5(f"{title}{i}".encode()).hexdigest()[:12]
        
        # Time-varying sentiment (-1 to +1)
        hour = datetime.now().hour
        base_sentiment = random.uniform(-0.5, 0.5)
        # Markets more volatile during trading hours
        if 9 <= hour <= 16:
            base_sentiment *= 1.5
        sentiment = max(-1, min(1, base_sentiment))
        
        # Virality score (0-100)
        # Higher for breaking news, crypto, geopolitics
        base_virality = random.uniform(40, 90)
        if event_domain in ["crypto", "geopolitics"]:
            base_virality += 10
        if "Breaking" in title or "surge" in title.lower():
            base_virality += 15
        virality = min(100, base_virality)
        
        events.append(MockEvent(
            id=f"mock_{event_id}",
            title=title,
            description=description,
            source=f"MockNews_{event_domain.upper()}",
            domain=event_domain,
            published_at=datetime.now(timezone.utc) - timedelta(minutes=random.randint(5, 120)),
            sentiment=round(sentiment, 3),
            virality_score=round(virality, 1),
        ))
    
    return events

def generate_mock_sports_fixtures(count: int = 5) -> List[Dict]:
    """Generate mock sports fixtures."""
    fixtures = []
    
    for i in range(count):
        home = random.choice(TEAMS)
        away = random.choice([t for t in TEAMS if t != home])
        
        fixtures.append({
            "id": f"mock_fixture_{i}",
            "home_team": home,
            "away_team": away,
            "date": (datetime.now() + timedelta(days=random.randint(1, 14))).isoformat(),
            "competition": "Premier League",
            "matchday": random.randint(1, 38),
        })
    
    return fixtures

def generate_mock_crypto_prices() -> Dict[str, float]:
    """Generate mock crypto prices with slight variations."""
    base_prices = {
        "BTC": 95000,
        "ETH": 3500,
        "SOL": 180,
        "XRP": 1.20,
        "ADA": 0.80,
        "DOGE": 0.35,
    }
    
    return {
        symbol: price * random.uniform(0.98, 1.02)
        for symbol, price in base_prices.items()
    }

def generate_mock_stock_quote(symbol: str) -> Dict:
    """Generate mock stock quote."""
    base_prices = {
        "AAPL": 230,
        "TSLA": 350,
        "NVDA": 140,
        "GOOGL": 175,
        "MSFT": 430,
        "AMZN": 200,
        "META": 580,
    }
    
    price = base_prices.get(symbol.upper(), 100) * random.uniform(0.97, 1.03)
    change = random.uniform(-5, 5)
    
    return {
        "symbol": symbol.upper(),
        "price": round(price, 2),
        "change": round(change, 2),
        "change_percent": round(change / price * 100, 2),
        "volume": random.randint(1000000, 50000000),
    }

# =============================================================================
# MOCK MODE DECORATOR
# =============================================================================

def mock_if_enabled(mock_func):
    """Decorator that returns mock data if MOCK_MODE is enabled."""
    def decorator(real_func):
        def wrapper(*args, **kwargs):
            if MOCK_MODE:
                print(f"🎭 MOCK MODE: Using fake data for {real_func.__name__}")
                return mock_func(*args, **kwargs)
            return real_func(*args, **kwargs)
        return wrapper
    return decorator

# =============================================================================
# TESTING
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Mock Data Generator Test")
    print("=" * 60)
    print(f"MOCK_MODE: {MOCK_MODE}")
    print()
    
    # Generate sample events
    events = generate_mock_events(5)
    print("📰 Sample Headlines:")
    for e in events:
        print(f"  [{e.domain:10}] {e.title[:60]}...")
        print(f"              Sentiment: {e.sentiment:+.2f} | Virality: {e.virality_score:.0f}")
    
    print()
    print("⚽ Sample Fixtures:")
    for f in generate_mock_sports_fixtures(3):
        print(f"  {f['home_team']} vs {f['away_team']} - Matchday {f['matchday']}")
    
    print()
    print("💰 Crypto Prices:")
    for symbol, price in generate_mock_crypto_prices().items():
        print(f"  {symbol}: ${price:,.2f}")
    
    print()
    print("📈 Stock Quote:")
    quote = generate_mock_stock_quote("AAPL")
    print(f"  {quote['symbol']}: ${quote['price']} ({quote['change_percent']:+.2f}%)")




