import sys
import os
from datetime import datetime, timezone

# Setup imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.event_orchestrator import EventOrchestrator, RawEvent, EventDomain

def seed_markets():
    print("🌱 Seeding 'God Mode' Markets...")
    
    # Initialize Orchestrator
    orchestrator = EventOrchestrator()
    
    # Define 10 diverse "Polymarket-style" events
    mock_events = [
        # CRYPTO
        ("Bitcoin > $100k by Dec 31?", EventDomain.CRYPTO, 95),
        ("Ethereum ETF Approval Date?", EventDomain.CRYPTO, 85),
        ("Solana Flip Ethereum Market Cap?", EventDomain.CRYPTO, 60),
        
        # POLITICS
        ("2028 Election: Newsom vs DeSantis?", EventDomain.POLITICS, 88),
        ("Will the Fed cut rates in Q4?", EventDomain.POLITICS, 92),
        
        # SPORTS
        ("Man City to win Premier League?", EventDomain.SPORTS, 75),
        ("Super Bowl LIX: Chiefs vs 49ers?", EventDomain.SPORTS, 80),
        ("Mbappe Top Scorer 2025?", EventDomain.SPORTS, 65),
        
        # FINANCE
        ("NVIDIA to hit $4T Market Cap?", EventDomain.FINANCE, 90),
        ("Oil prices > $100/barrel?", EventDomain.GEOPOLITICS, 82),
    ]
    count = 0
    for title, domain, virality in mock_events:
        # Create a fake "Raw Event"
        event = RawEvent(
            id=f"seed_{count}",
            title=title,
            description=f"Market simulation for: {title}. Betting ends soon.",
            source="God Mode Seed",
            url="http://localhost",
            published_at=datetime.now(timezone.utc),
            domain=domain,
            virality_score=virality,
            sentiment=0.0
        )
        
        # Force create the market
        market = orchestrator.create_market(event)
        
        # Force dispatch agents so it looks active
        agents = orchestrator.dispatch_agents(market)
        
        print(f"✅ Created: {title} ({len(agents)} agents active)")
        count += 1
    print(f"\n🚀 Successfully seeded {count} markets!")
    print("Refresh your frontend to see the active platform.")

if __name__ == "__main__":
    seed_markets()

