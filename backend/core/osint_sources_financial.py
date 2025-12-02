"""
OSINT Signal Sources - Part 2: Financial Markets ("The Alpha")
===============================================================
Alternative data signals for financial market predictions.

Sources:
- Satellite Supply Chain (parking lots, oil tanks)
- Job Postings (hiring/layoff signals)
- App Store Rankings (consumer trends)
- Corporate Jet Tracking (M&A, deal-making)

These signals give "Shark" agents an edge, simulating how real
hedge funds trade on alternative data.
"""
import os
import random
import asyncio
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum

# Optional imports
try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False

# Import base classes
try:
    from backend.core.signal_detector import (
        BaseSignalSource, Signal, SignalSource, RegionOfInterest
    )
except ImportError:
    from core.signal_detector import (
        BaseSignalSource, Signal, SignalSource, RegionOfInterest
    )

# =============================================================================
# SATELLITE SUPPLY CHAIN - "Counting cars and oil tanks"
# =============================================================================

@dataclass
class RetailLocation:
    """A retail location we monitor via satellite."""
    company: str
    ticker: str
    location_name: str
    lat: float
    lng: float
    parking_capacity: int
    baseline_occupancy: float  # 0-1

@dataclass
class OilStorage:
    """An oil storage facility we monitor."""
    name: str
    region: str
    capacity_barrels: int
    lat: float
    lng: float

class SatelliteSupplyChainSource(BaseSignalSource):
    """
    Satellite-Based Supply Chain Intelligence
    
    Monitors:
    - Retail parking lot occupancy (earnings predictor)
    - Oil tank floating lid levels (inventory indicator)
    - Factory/port activity (manufacturing trends)
    - Tesla Fremont parking lot (delivery estimates)
    
    Real API: Planet, Sentinel Hub, Orbital Insight
    """
    
    # Retail locations to monitor
    RETAIL_TARGETS = [
        RetailLocation("Walmart", "WMT", "Bentonville HQ", 36.3729, -94.2088, 5000, 0.65),
        RetailLocation("Target", "TGT", "Minneapolis HQ", 44.9537, -93.2650, 3000, 0.60),
        RetailLocation("Costco", "COST", "Issaquah HQ", 47.5301, -122.0326, 2000, 0.70),
        RetailLocation("Home Depot", "HD", "Atlanta HQ", 33.7490, -84.3880, 4000, 0.55),
        RetailLocation("Tesla", "TSLA", "Fremont Factory", 37.4942, -121.9440, 8000, 0.50),
        RetailLocation("Amazon", "AMZN", "Seattle Fulfillment", 47.6062, -122.3321, 6000, 0.75),
    ]
    
    # Oil storage facilities
    OIL_STORAGE = [
        OilStorage("Cushing Oklahoma Hub", "USA", 80_000_000, 35.9849, -96.7678),
        OilStorage("Rotterdam Tank Farm", "Europe", 40_000_000, 51.9244, 4.4777),
        OilStorage("Fujairah Storage", "UAE", 50_000_000, 25.1288, 56.3265),
        OilStorage("Singapore Tank Farm", "Asia", 35_000_000, 1.2644, 103.8228),
    ]
    
    async def scan(self, region: RegionOfInterest) -> List[Signal]:
        signals = []
        now = datetime.now(timezone.utc)
        
        # Only scan for financial regions
        if region in [RegionOfInterest.WASHINGTON_DC]:
            # Scan retail locations (US-centric)
            signals.extend(await self._scan_retail(now))
            
        # Oil storage is global
        signals.extend(await self._scan_oil_storage(region, now))
        
        return signals
    
    async def _scan_retail(self, now: datetime) -> List[Signal]:
        """Scan retail parking lots for occupancy signals."""
        signals = []
        
        for location in self.RETAIL_TARGETS:
            # 12% chance of notable signal per location
            if random.random() < 0.12:
                # Simulate occupancy reading
                deviation = random.uniform(-0.4, 0.4)
                current_occupancy = max(0.1, min(1.0, location.baseline_occupancy + deviation))
                
                change_pct = ((current_occupancy - location.baseline_occupancy) / location.baseline_occupancy) * 100
                
                # Only signal on significant changes
                if abs(change_pct) > 15:
                    if change_pct > 0:
                        sentiment = "bullish"
                        desc = f"High traffic at {location.company} ({location.ticker}): {change_pct:.0f}% above normal"
                        implication = "Potential earnings beat"
                    else:
                        sentiment = "bearish"
                        desc = f"Low traffic at {location.company} ({location.ticker}): {abs(change_pct):.0f}% below normal"
                        implication = "Potential earnings miss"
                    
                    level = min(1.0, abs(change_pct) / 50)
                    
                    signals.append(Signal(
                        id=self._generate_signal_id("satellite", location.ticker),
                        source=SignalSource.SATELLITE_PROXY,
                        region=RegionOfInterest.WASHINGTON_DC,  # US markets
                        level=level,
                        confidence=0.7,
                        description=f"🛰️ {desc}. {implication}",
                        raw_data={
                            "company": location.company,
                            "ticker": location.ticker,
                            "location": location.location_name,
                            "baseline_occupancy": location.baseline_occupancy,
                            "current_occupancy": round(current_occupancy, 3),
                            "change_pct": round(change_pct, 1),
                            "sentiment": sentiment,
                            "source": "simulated_satellite",
                        },
                        timestamp=now,
                        expires_at=now + timedelta(hours=24),
                    ))
        
        return signals
    
    async def _scan_oil_storage(self, region: RegionOfInterest, now: datetime) -> List[Signal]:
        """Scan oil storage facilities for inventory signals."""
        signals = []
        
        # 8% chance of oil storage signal
        if random.random() < 0.08:
            facility = random.choice(self.OIL_STORAGE)
            
            # Simulate fill level (floating roof tanks)
            baseline_fill = 0.60  # Normal is 60% full
            current_fill = random.uniform(0.3, 0.95)
            change = current_fill - baseline_fill
            
            if abs(change) > 0.1:  # >10% deviation
                if change > 0:
                    desc = f"Oil tanks filling up at {facility.name}: {current_fill*100:.0f}% full"
                    implication = "Oversupply signal - bearish for oil prices"
                    sentiment = "bearish"
                else:
                    desc = f"Oil tanks draining at {facility.name}: {current_fill*100:.0f}% full"
                    implication = "Supply tightening - bullish for oil prices"
                    sentiment = "bullish"
                
                signals.append(Signal(
                    id=self._generate_signal_id("oil", facility.name),
                    source=SignalSource.SATELLITE_PROXY,
                    region=RegionOfInterest.STRAIT_HORMUZ,  # Oil-related
                    level=min(1.0, abs(change) * 2),
                    confidence=0.75,
                    description=f"🛢️ {desc}. {implication}",
                    raw_data={
                        "facility": facility.name,
                        "region": facility.region,
                        "capacity_barrels": facility.capacity_barrels,
                        "fill_level": round(current_fill, 3),
                        "baseline_fill": baseline_fill,
                        "sentiment": sentiment,
                        "source": "simulated_satellite",
                    },
                    timestamp=now,
                    expires_at=now + timedelta(hours=48),
                ))
        
        return signals

# =============================================================================
# JOB POSTINGS - "Are they hiring or firing?"
# =============================================================================

@dataclass
class CompanyJobData:
    """Job posting data for a company."""
    company: str
    ticker: str
    baseline_openings: int
    sectors: List[str]

class JobPostingsSource(BaseSignalSource):
    """
    Job Posting Intelligence
    
    Monitors:
    - Total job openings (growth vs contraction)
    - New role types (product launches)
    - Mass posting removals (layoffs incoming)
    - Geographic expansion (new markets)
    
    Real API: LinkUp, Indeed API, or scraping career pages
    """
    
    # Companies to track
    TRACKED_COMPANIES = [
        CompanyJobData("Apple", "AAPL", 5000, ["engineering", "retail", "AI/ML"]),
        CompanyJobData("Google", "GOOGL", 8000, ["engineering", "cloud", "AI/ML"]),
        CompanyJobData("Meta", "META", 4000, ["engineering", "VR/AR", "AI/ML"]),
        CompanyJobData("Amazon", "AMZN", 15000, ["logistics", "engineering", "AWS"]),
        CompanyJobData("Microsoft", "MSFT", 7000, ["engineering", "cloud", "gaming"]),
        CompanyJobData("Tesla", "TSLA", 3000, ["engineering", "manufacturing", "energy"]),
        CompanyJobData("NVIDIA", "NVDA", 2000, ["engineering", "AI/ML", "hardware"]),
        CompanyJobData("Netflix", "NFLX", 1500, ["engineering", "content", "gaming"]),
        CompanyJobData("Salesforce", "CRM", 4000, ["engineering", "sales", "AI"]),
        CompanyJobData("Goldman Sachs", "GS", 3500, ["finance", "technology", "trading"]),
    ]
    
    async def scan(self, region: RegionOfInterest) -> List[Signal]:
        signals = []
        now = datetime.now(timezone.utc)
        
        # Job signals are US market focused
        if region != RegionOfInterest.WASHINGTON_DC:
            return signals
        
        for company in self.TRACKED_COMPANIES:
            # 10% chance of notable change per company
            if random.random() < 0.10:
                signals.extend(await self._analyze_company_jobs(company, now))
        
        return signals
    
    async def _analyze_company_jobs(self, company: CompanyJobData, now: datetime) -> List[Signal]:
        """Analyze job postings for a company."""
        signals = []
        
        # Simulate job posting changes
        change_type = random.choice(["surge", "decline", "new_sector", "mass_removal"])
        
        if change_type == "surge":
            change_pct = random.uniform(20, 80)
            current = int(company.baseline_openings * (1 + change_pct/100))
            desc = f"{company.company} ({company.ticker}) job postings surge: +{change_pct:.0f}% ({current} openings)"
            implication = "Aggressive expansion - bullish signal"
            level = min(1.0, change_pct / 100)
            sentiment = "bullish"
            
        elif change_type == "decline":
            change_pct = random.uniform(20, 60)
            current = int(company.baseline_openings * (1 - change_pct/100))
            desc = f"{company.company} ({company.ticker}) job postings decline: -{change_pct:.0f}% ({current} openings)"
            implication = "Hiring freeze or restructuring - cautious signal"
            level = min(1.0, change_pct / 100)
            sentiment = "bearish"
            
        elif change_type == "new_sector":
            new_sector = random.choice(["quantum computing", "robotics", "autonomous vehicles", "blockchain", "AR/VR"])
            count = random.randint(50, 200)
            desc = f"{company.company} ({company.ticker}) posting {count} new {new_sector} roles"
            implication = f"Potential pivot into {new_sector} - watch for announcements"
            level = 0.6
            sentiment = "bullish"
            
        else:  # mass_removal
            removed = random.randint(500, 2000)
            desc = f"{company.company} ({company.ticker}) removed {removed} job postings in 24h"
            implication = "Possible layoffs or hiring freeze imminent"
            level = 0.85
            sentiment = "bearish"
        
        signals.append(Signal(
            id=self._generate_signal_id("jobs", company.ticker),
            source=SignalSource.SOCIAL_CHATTER,  # Using as proxy
            region=RegionOfInterest.WASHINGTON_DC,
            level=level,
            confidence=0.65,
            description=f"💼 {desc}. {implication}",
            raw_data={
                "company": company.company,
                "ticker": company.ticker,
                "baseline_openings": company.baseline_openings,
                "change_type": change_type,
                "sentiment": sentiment,
                "sectors": company.sectors,
                "source": "simulated_jobs",
            },
            timestamp=now,
            expires_at=now + timedelta(hours=72),
        ))
        
        return signals

# =============================================================================
# APP STORE RANKINGS - "Is the app dying?"
# =============================================================================

@dataclass
class TrackedApp:
    """An app we track in app stores."""
    name: str
    company: str
    ticker: str
    category: str
    baseline_rank: int  # Lower = better

class AppStoreSource(BaseSignalSource):
    """
    App Store Rankings Intelligence
    
    Monitors:
    - Rank changes (user acquisition trends)
    - Review sentiment shifts
    - Download velocity
    - Category movements
    
    Real API: Data.ai (App Annie), Sensor Tower, or scraping
    """
    
    TRACKED_APPS = [
        TrackedApp("Netflix", "Netflix", "NFLX", "Entertainment", 5),
        TrackedApp("Disney+", "Disney", "DIS", "Entertainment", 8),
        TrackedApp("Spotify", "Spotify", "SPOT", "Music", 3),
        TrackedApp("TikTok", "ByteDance", "PRIVATE", "Social", 1),
        TrackedApp("Instagram", "Meta", "META", "Social", 2),
        TrackedApp("Uber", "Uber", "UBER", "Travel", 4),
        TrackedApp("DoorDash", "DoorDash", "DASH", "Food & Drink", 3),
        TrackedApp("Robinhood", "Robinhood", "HOOD", "Finance", 15),
        TrackedApp("Coinbase", "Coinbase", "COIN", "Finance", 20),
        TrackedApp("Peloton", "Peloton", "PTON", "Health & Fitness", 25),
        TrackedApp("Zoom", "Zoom", "ZM", "Business", 10),
        TrackedApp("Slack", "Salesforce", "CRM", "Business", 12),
    ]
    
    async def scan(self, region: RegionOfInterest) -> List[Signal]:
        signals = []
        now = datetime.now(timezone.utc)
        
        # App signals are US market focused
        if region != RegionOfInterest.WASHINGTON_DC:
            return signals
        
        for app in self.TRACKED_APPS:
            # 8% chance of notable ranking change
            if random.random() < 0.08:
                signals.extend(await self._analyze_app_ranking(app, now))
        
        return signals
    
    async def _analyze_app_ranking(self, app: TrackedApp, now: datetime) -> List[Signal]:
        """Analyze app store ranking changes."""
        signals = []
        
        # Simulate ranking change
        direction = random.choice(["improved", "declined"])
        
        if direction == "improved":
            new_rank = max(1, app.baseline_rank - random.randint(5, 20))
            change = app.baseline_rank - new_rank
            desc = f"{app.name} ({app.ticker}) climbed {change} spots to #{new_rank} in {app.category}"
            implication = "Increased user acquisition - potential revenue beat"
            sentiment = "bullish"
            level = min(1.0, change / 30)
        else:
            new_rank = app.baseline_rank + random.randint(10, 50)
            change = new_rank - app.baseline_rank
            desc = f"{app.name} ({app.ticker}) dropped {change} spots to #{new_rank} in {app.category}"
            implication = "User engagement declining - potential subscriber miss"
            sentiment = "bearish"
            level = min(1.0, change / 50)
        
        # Add review sentiment
        review_sentiment = random.choice(["positive", "negative", "mixed"])
        if review_sentiment == "negative":
            desc += ". Recent reviews trending negative"
            level = min(1.0, level + 0.2)
        
        signals.append(Signal(
            id=self._generate_signal_id("appstore", app.ticker),
            source=SignalSource.SOCIAL_CHATTER,
            region=RegionOfInterest.WASHINGTON_DC,
            level=level,
            confidence=0.6,
            description=f"📱 {desc}. {implication}",
            raw_data={
                "app": app.name,
                "company": app.company,
                "ticker": app.ticker,
                "category": app.category,
                "baseline_rank": app.baseline_rank,
                "new_rank": new_rank,
                "direction": direction,
                "review_sentiment": review_sentiment,
                "sentiment": sentiment,
                "source": "simulated_appstore",
            },
            timestamp=now,
            expires_at=now + timedelta(hours=48),
        ))
        
        return signals

# =============================================================================
# CORPORATE JET TRACKING - "Where is the CEO going?"
# =============================================================================

@dataclass
class CorporateJet:
    """A corporate jet we track."""
    registration: str
    owner: str
    ticker: str
    jet_type: str

class CorporateJetSource(BaseSignalSource):
    """
    Corporate Jet Tracking
    
    Monitors:
    - CEO jets visiting competitors (M&A?)
    - Jets at Warren Buffett's Omaha (investment?)
    - Multiple exec jets at same location (board meeting?)
    - Unusual international destinations
    
    Real API: ADS-B Exchange, JetNet
    """
    
    # Known corporate jets
    CORPORATE_JETS = [
        CorporateJet("N1TS", "Elon Musk/Tesla", "TSLA", "Gulfstream G650"),
        CorporateJet("N886QS", "Warren Buffett", "BRK.B", "NetJets Fleet"),
        CorporateJet("N789JB", "Jeff Bezos", "AMZN", "Gulfstream G650"),
        CorporateJet("N421AL", "Larry Ellison", "ORCL", "Gulfstream G650"),
        CorporateJet("N513QS", "Bill Gates", "MSFT", "Bombardier BD-700"),
        CorporateJet("N212TT", "Mark Zuckerberg", "META", "Gulfstream G650"),
        CorporateJet("N5MV", "Michael Dell", "DELL", "Gulfstream G550"),
    ]
    
    # Significant destinations
    SIGNIFICANT_LOCATIONS = {
        "omaha": {"name": "Omaha, NE", "significance": "Warren Buffett - potential investment"},
        "cupertino": {"name": "Cupertino, CA", "significance": "Apple HQ"},
        "seattle": {"name": "Seattle, WA", "significance": "Amazon/Microsoft HQ"},
        "detroit": {"name": "Detroit, MI", "significance": "Auto industry deals"},
        "menlo_park": {"name": "Menlo Park, CA", "significance": "Meta/VC hub"},
        "austin": {"name": "Austin, TX", "significance": "Tesla/Tech hub"},
        "washington_dc": {"name": "Washington, DC", "significance": "Regulatory/Political meetings"},
        "davos": {"name": "Davos, Switzerland", "significance": "World Economic Forum"},
        "sun_valley": {"name": "Sun Valley, ID", "significance": "Allen & Co. conference - M&A"},
    }
    
    async def scan(self, region: RegionOfInterest) -> List[Signal]:
        signals = []
        now = datetime.now(timezone.utc)
        
        # Only US-focused
        if region != RegionOfInterest.WASHINGTON_DC:
            return signals
        
        # 7% chance of notable jet movement
        if random.random() < 0.07:
            signals.extend(await self._track_jet_movement(now))
        
        return signals
    
    async def _track_jet_movement(self, now: datetime) -> List[Signal]:
        """Track and analyze corporate jet movements."""
        signals = []
        
        jet = random.choice(self.CORPORATE_JETS)
        destination = random.choice(list(self.SIGNIFICANT_LOCATIONS.values()))
        
        # Generate scenario
        scenarios = [
            {
                "desc": f"{jet.owner}'s jet ({jet.registration}) spotted landing in {destination['name']}",
                "implication": f"Possible high-level meeting. {destination['significance']}",
                "level": 0.7,
            },
            {
                "desc": f"Multiple executive jets converging on {destination['name']} including {jet.registration}",
                "implication": "Potential M&A discussions or major announcement",
                "level": 0.85,
            },
            {
                "desc": f"{jet.owner}'s jet made unexpected stop at competitor facility",
                "implication": "Acquisition talks or partnership negotiations?",
                "level": 0.8,
            },
        ]
        
        scenario = random.choice(scenarios)
        
        signals.append(Signal(
            id=self._generate_signal_id("corpjet", jet.registration),
            source=SignalSource.FLIGHT_RADAR,
            region=RegionOfInterest.WASHINGTON_DC,
            level=scenario["level"],
            confidence=0.75,
            description=f"✈️ {scenario['desc']}. {scenario['implication']}",
            raw_data={
                "registration": jet.registration,
                "owner": jet.owner,
                "ticker": jet.ticker,
                "jet_type": jet.jet_type,
                "destination": destination["name"],
                "destination_significance": destination["significance"],
                "source": "simulated_adsb",
            },
            timestamp=now,
            expires_at=now + timedelta(hours=12),
        ))
        
        return signals

# =============================================================================
# EXPORT ALL FINANCIAL SOURCES
# =============================================================================

FINANCIAL_SOURCES = [
    SatelliteSupplyChainSource,
    JobPostingsSource,
    AppStoreSource,
    CorporateJetSource,
]

def get_financial_sources() -> List[BaseSignalSource]:
    """Get instances of all Financial (Alpha) signal sources."""
    return [source() for source in FINANCIAL_SOURCES]

# =============================================================================
# TESTING
# =============================================================================

if __name__ == "__main__":
    async def test():
        print("=" * 60)
        print("💰 FINANCIAL ALPHA SIGNAL SOURCES - Test")
        print("=" * 60)
        
        sources = get_financial_sources()
        
        for source in sources:
            print(f"\n📡 Testing {source.__class__.__name__}...")
            
            # Financial sources focus on US markets
            signals = await source.scan(RegionOfInterest.WASHINGTON_DC)
            
            if signals:
                for sig in signals:
                    print(f"  [{sig.severity}] {sig.description[:70]}...")
            else:
                print("  No signals detected this scan")
        
        print("\n" + "=" * 60)
    
    asyncio.run(test())
