"""
Signal Detector (The 'Pizzint' Engine)
=======================================
Alternative Data Intelligence System for Predictive Geopolitics

Monitors non-traditional signals to detect geopolitical events BEFORE headlines:

- Pentagon Pizza Index (late-night food deliveries)
- Flight Anomalies (airspace closures, military movements)
- Hospital Traffic (crisis preparation indicators)
- Social Sentiment (early warning chatter)
- Shipping Patterns (supply chain disruptions)
- Satellite Indicators (light patterns, parking lots)

The Theory:
-----------
Major operations require logistics. Before any military action:
1. Staff work late (pizza orders spike)
2. Airspace clears (flight diversions)
3. Hospitals prepare (unusual supply orders)
4. Chatter increases (social media anomalies)

These signals appear 6-48 hours BEFORE official announcements.

Usage:
    from backend.core.signal_detector import SignalDetector, DEFCONLevel
    
    detector = SignalDetector()
    signals = await detector.scan_all_sources()
    
    if detector.defcon_level <= 2:
        mission = detector.generate_mission(signals[0])
        # Create betting market for the mission
"""

import os
import json
import random
import asyncio
import hashlib
from math import cos, radians
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod

# Optional imports for real APIs
try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False

try:
    from pytrends.request import TrendReq
    HAS_PYTRENDS = True
except ImportError:
    HAS_PYTRENDS = False


# =============================================================================
# CONFIGURATION
# =============================================================================

class DEFCONLevel(Enum):
    """
    Defense Readiness Condition - adapted for our signal system.
    
    DEFCON 5: Normal peacetime readiness
    DEFCON 4: Increased intelligence watch
    DEFCON 3: Increase in force readiness
    DEFCON 2: Further increase, less than maximum
    DEFCON 1: Maximum readiness (nuclear war imminent)
    
    For our system:
    - DEFCON 5: No anomalies detected
    - DEFCON 4: Minor signal (1 weak indicator)
    - DEFCON 3: Moderate signal (2+ indicators OR 1 strong)
    - DEFCON 2: High alert (3+ indicators, correlation detected)
    - DEFCON 1: Critical (overwhelming signal confluence)
    """
    DEFCON_5 = 5  # Normal
    DEFCON_4 = 4  # Watch
    DEFCON_3 = 3  # Alert
    DEFCON_2 = 2  # High Alert - MISSION TRIGGER
    DEFCON_1 = 1  # Critical - MAJOR MISSION


class SignalSource(Enum):
    """Categories of alternative data signals."""
    PIZZA_INDEX = "pizza_index"           # Late night food delivery patterns
    FLIGHT_RADAR = "flight_radar"         # Airspace anomalies
    HOSPITAL_TRAFFIC = "hospital_traffic" # Medical preparation indicators
    SOCIAL_CHATTER = "social_chatter"     # Twitter/social sentiment
    SHIPPING_PATTERN = "shipping_pattern" # Maritime/cargo movements
    SATELLITE_PROXY = "satellite_proxy"   # Parking lots, light patterns
    GOOGLE_TRENDS = "google_trends"       # Search interest spikes
    POWER_GRID = "power_grid"             # Unusual consumption patterns


class RegionOfInterest(Enum):
    """Geographic areas we monitor for signals."""
    WASHINGTON_DC = "washington_dc"
    MOSCOW = "moscow"
    BEIJING = "beijing"
    TEHRAN = "tehran"
    PYONGYANG = "pyongyang"
    TAIPEI = "taipei"
    JERUSALEM = "jerusalem"
    KYIV = "kyiv"
    BRUSSELS = "brussels"      # NATO HQ
    GENEVA = "geneva"          # UN/Diplomatic
    STRAIT_HORMUZ = "strait_hormuz"
    SOUTH_CHINA_SEA = "south_china_sea"
    BALTIC_SEA = "baltic_sea"


@dataclass
class Signal:
    """A detected anomaly from an alternative data source."""

    id: str
    source: SignalSource
    region: RegionOfInterest
    level: float                    # 0.0 (baseline) to 1.0 (critical)
    confidence: float               # How confident we are in this signal
    description: str
    raw_data: Dict[str, Any]        # Original data for transparency
    timestamp: datetime
    expires_at: datetime            # Signals decay over time
    correlated_signals: List[str] = field(default_factory=list)
    
    @property
    def is_expired(self) -> bool:
        return datetime.now(timezone.utc) > self.expires_at
    
    @property
    def severity(self) -> str:
        if self.level >= 0.9:
            return "CRITICAL"
        elif self.level >= 0.75:
            return "HIGH"
        elif self.level >= 0.5:
            return "MODERATE"
        elif self.level >= 0.25:
            return "LOW"
        return "MINIMAL"
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "source": self.source.value,
            "region": self.region.value,
            "level": self.level,
            "confidence": self.confidence,
            "severity": self.severity,
            "description": self.description,
            "timestamp": self.timestamp.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "correlated_signals": self.correlated_signals,
        }


@dataclass
class Mission:
    """
    A short-term, high-stakes betting opportunity generated from signals.
    
    Missions are different from regular markets:
    - Very short duration (4-24 hours)
    - High risk/reward
    - May require "intel clearance" to view (x402 paywall)
    - Spawns specialized agents (Spy, Analyst, Operator)
    """
    id: str
    codename: str                   # "OPERATION NIGHTFALL"
    title: str                      # "Covert Operation Detected - Success?"
    description: str
    source_signals: List[str]       # Signal IDs that triggered this
    region: RegionOfInterest
    mission_type: str               # "extraction", "reconnaissance", etc.
    
    # Timing
    created_at: datetime
    expires_at: datetime
    duration_hours: int
    
    # Betting
    outcomes: List[str]             # ["SUCCESS", "FAILURE", "INCONCLUSIVE"]
    initial_odds: Dict[str, float]
    virality_score: int
    
    # Access control
    intel_required: bool = False    # Requires x402 payment to view
    intel_cost_usd: float = 0.0
    
    # Resolution
    status: str = "ACTIVE"          # ACTIVE, RESOLVED, EXPIRED
    outcome: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "codename": self.codename,
            "title": self.title,
            "description": self.description,
            "source_signals": self.source_signals,
            "region": self.region.value,
            "mission_type": self.mission_type,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "duration_hours": self.duration_hours,
            "outcomes": self.outcomes,
            "initial_odds": self.initial_odds,
            "virality_score": self.virality_score,
            "intel_required": self.intel_required,
            "intel_cost_usd": self.intel_cost_usd,
            "status": self.status,
            "outcome": self.outcome,
        }


# =============================================================================
# SIGNAL SOURCES (Abstract + Implementations)
# =============================================================================

class BaseSignalSource(ABC):
    """Base class for all signal sources."""
    
    @abstractmethod
    async def scan(self, region: RegionOfInterest) -> List[Signal]:
        """Scan this source for anomalies in the specified region."""
        pass
    
    def _generate_signal_id(self, source: str, region: str) -> str:
        """Generate unique signal ID."""
        timestamp = datetime.now(timezone.utc).isoformat()
        raw = f"{source}:{region}:{timestamp}:{random.random()}"
        return hashlib.md5(raw.encode()).hexdigest()[:12]


class PizzaIndexSource(BaseSignalSource):
    """
    The Pentagon Pizza Index
    
    Theory: Late-night food delivery spikes near government buildings
    indicate staff working overtime, often before major operations.
    
    Real implementation would use:
    - Google Maps Popular Times API
    - Delivery app order volumes (if accessible)
    - Traffic cameras near known facilities
    
    For now: Simulated with realistic patterns
    """
    
    # Known facilities to monitor
    FACILITIES = {
        RegionOfInterest.WASHINGTON_DC: [
            {"name": "Pentagon", "baseline_orders": 50, "lat": 38.8719, "lng": -77.0563},
            {"name": "State Department", "baseline_orders": 30, "lat": 38.8951, "lng": -77.0485},
            {"name": "CIA Langley", "baseline_orders": 40, "lat": 38.9510, "lng": -77.1465},
            {"name": "NSA Fort Meade", "baseline_orders": 35, "lat": 39.1086, "lng": -76.7711},
        ],
        RegionOfInterest.MOSCOW: [
            {"name": "Kremlin", "baseline_orders": 20, "lat": 55.7520, "lng": 37.6175},
            {"name": "GRU HQ", "baseline_orders": 15, "lat": 55.7833, "lng": 37.5833},
        ],
        RegionOfInterest.BEIJING: [
            {"name": "Zhongnanhai", "baseline_orders": 25, "lat": 39.9139, "lng": 116.3861},
            {"name": "PLA HQ", "baseline_orders": 20, "lat": 39.9042, "lng": 116.4074},
        ],
    }
    
    async def scan(self, region: RegionOfInterest) -> List[Signal]:
        signals = []
        
        facilities = self.FACILITIES.get(region, [])
        if not facilities:
            return signals
        
        now = datetime.now(timezone.utc)
        hour = now.hour
        
        # Late night (10 PM - 6 AM) is when anomalies matter most
        is_late_night = hour >= 22 or hour <= 6
        
        for facility in facilities:
            # Simulate order volume (with some randomness)
            baseline = facility["baseline_orders"]
            
            # Normal variation: ±30%
            normal_variation = random.uniform(0.7, 1.3)
            
            # Anomaly injection (10% chance of significant spike)
            if random.random() < 0.10:
                anomaly_multiplier = random.uniform(2.0, 4.0)
            else:
                anomaly_multiplier = 1.0
            
            current_orders = int(baseline * normal_variation * anomaly_multiplier)
            deviation = (current_orders - baseline) / baseline
            
            # Only flag if significant deviation AND late night
            if deviation > 0.5 and is_late_night:
                level = min(1.0, deviation / 2)  # Cap at 1.0
                
                signals.append(Signal(
                    id=self._generate_signal_id("pizza", region.value),
                    source=SignalSource.PIZZA_INDEX,
                    region=region,
                    level=level,
                    confidence=0.7 if is_late_night else 0.4,
                    description=f"Unusual food delivery activity at {facility['name']}: "
                               f"{int(deviation*100)}% above baseline at {hour:02d}:00 UTC",
                    raw_data={
                        "facility": facility["name"],
                        "baseline_orders": baseline,
                        "current_orders": current_orders,
                        "deviation_pct": round(deviation * 100, 1),
                        "hour_utc": hour,
                        "is_late_night": is_late_night,
                    },
                    timestamp=now,
                    expires_at=now + timedelta(hours=6),
                ))
        
        return signals


class FlightRadarSource(BaseSignalSource):
    """
    Flight Radar Anomaly Detection
    
    Monitors for:
    - Sudden drops in commercial flights over regions
    - Military aircraft transponder activity
    - Unusual flight diversions
    
    Real implementation: OpenSky Network API (free)
    https://opensky-network.org/apidoc/
    """
    
    AIRSPACE_ZONES = {
        RegionOfInterest.KYIV: {"lat": 50.4501, "lng": 30.5234, "radius_km": 200},
        RegionOfInterest.TAIPEI: {"lat": 25.0330, "lng": 121.5654, "radius_km": 150},
        RegionOfInterest.STRAIT_HORMUZ: {"lat": 26.5667, "lng": 56.2500, "radius_km": 100},
        RegionOfInterest.SOUTH_CHINA_SEA: {"lat": 15.0, "lng": 115.0, "radius_km": 500},
        RegionOfInterest.BALTIC_SEA: {"lat": 58.0, "lng": 20.0, "radius_km": 300},
    }
    
    # Baseline flight counts (simulated)
    BASELINE_FLIGHTS = {
        RegionOfInterest.KYIV: 45,
        RegionOfInterest.TAIPEI: 120,
        RegionOfInterest.STRAIT_HORMUZ: 80,
        RegionOfInterest.SOUTH_CHINA_SEA: 200,
        RegionOfInterest.BALTIC_SEA: 90,
    }
    
    async def scan(self, region: RegionOfInterest) -> List[Signal]:
        signals = []
        
        zone = self.AIRSPACE_ZONES.get(region)
        baseline = self.BASELINE_FLIGHTS.get(region)
        
        if not zone or not baseline:
            return signals
        
        now = datetime.now(timezone.utc)
        
        # Try real OpenSky API first
        real_data = await self._fetch_opensky_data(zone)
        
        if real_data:
            current_flights = real_data["flight_count"]
        else:
            # Simulated fallback
            normal_variation = random.uniform(0.8, 1.2)
            
            # 8% chance of significant drop (anomaly)
            if random.random() < 0.08:
                anomaly_factor = random.uniform(0.2, 0.5)  # 50-80% drop
            else:
                anomaly_factor = 1.0
            
            current_flights = int(baseline * normal_variation * anomaly_factor)
        
        # Calculate deviation (we care about DROPS, not increases)
        deviation = (baseline - current_flights) / baseline
        
        if deviation > 0.3:  # 30%+ drop is significant
            level = min(1.0, deviation)
            
            signals.append(Signal(
                id=self._generate_signal_id("flight", region.value),
                source=SignalSource.FLIGHT_RADAR,
                region=region,
                level=level,
                confidence=0.85,
                description=f"Significant drop in commercial air traffic over {region.value}: "
                           f"{int(deviation*100)}% below normal ({current_flights} vs {baseline} baseline)",
                raw_data={
                    "zone": zone,
                    "baseline_flights": baseline,
                    "current_flights": current_flights,
                    "deviation_pct": round(deviation * 100, 1),
                    "source": "opensky" if real_data else "simulated",
                },
                timestamp=now,
                expires_at=now + timedelta(hours=4),
            ))
        
        return signals
    
    async def _fetch_opensky_data(self, zone: Dict) -> Optional[Dict]:
        """Fetch real flight data from OpenSky Network."""
        if not HAS_HTTPX:
            return None
        
        try:
            # OpenSky API endpoint
            lat, lng, radius = zone["lat"], zone["lng"], zone["radius_km"]
            
            # Convert radius to bounding box
            lat_delta = radius / 111  # ~111km per degree latitude
            lng_delta = radius / (111 * abs(cos(radians(lat))))
            
            url = "https://opensky-network.org/api/states/all"
            params = {
                "lamin": lat - lat_delta,
                "lamax": lat + lat_delta,
                "lomin": lng - lng_delta,
                "lomax": lng + lng_delta,
            }
            
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(url, params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    if data is None:
                        return None
                    states = data.get("states")
                    if states is None:
                        states = []
                    return {"flight_count": len(states) if isinstance(states, list) else 0, "raw": data}
        except Exception as e:
            print(f"⚠️ OpenSky API error: {e}")
        
        return None


class GoogleTrendsSource(BaseSignalSource):
    """
    Google Trends Monitoring
    
    Watches for spikes in searches related to:
    - Military terms ("mobilization", "draft", "bunker")
    - Crisis terms ("evacuation", "emergency", "martial law")
    - Region-specific terms ("Taiwan invasion", "Ukraine war")
    
    Real implementation: pytrends library
    """
    
    KEYWORDS = {
        RegionOfInterest.WASHINGTON_DC: ["pentagon alert", "military mobilization", "defcon"],
        RegionOfInterest.TAIPEI: ["taiwan invasion", "china taiwan war", "taiwan emergency"],
        RegionOfInterest.KYIV: ["ukraine war", "russia attack", "kyiv bombing"],
        RegionOfInterest.TEHRAN: ["iran attack", "iran war", "strait of hormuz"],
        RegionOfInterest.JERUSALEM: ["israel war", "gaza invasion", "iron dome"],
    }
    
    async def scan(self, region: RegionOfInterest) -> List[Signal]:
        signals = []
        
        keywords = self.KEYWORDS.get(region, [])
        if not keywords:
            return signals
        
        now = datetime.now(timezone.utc)
        
        # Try real Google Trends
        real_data = await self._fetch_trends_data(keywords)
        
        if real_data:
            for keyword, trend_level in real_data.items():
                if trend_level > 50:  # Above 50 = elevated interest
                    level = min(1.0, trend_level / 100)
                    
                    signals.append(Signal(
                        id=self._generate_signal_id("trends", region.value),
                        source=SignalSource.GOOGLE_TRENDS,
                        region=region,
                        level=level,
                        confidence=0.6,
                        description=f"Elevated search interest for '{keyword}': "
                                   f"trend level {trend_level}/100",
                        raw_data={
                            "keyword": keyword,
                            "trend_level": trend_level,
                            "source": "google_trends",
                        },
                        timestamp=now,
                        expires_at=now + timedelta(hours=12),
                    ))
        else:
            # Simulated fallback
            for keyword in keywords:
                # 15% chance of elevated trend
                if random.random() < 0.15:
                    trend_level = random.randint(55, 100)
                    level = min(1.0, trend_level / 100)
                    
                    signals.append(Signal(
                        id=self._generate_signal_id("trends", region.value),
                        source=SignalSource.GOOGLE_TRENDS,
                        region=region,
                        level=level,
                        confidence=0.6,
                        description=f"Simulated spike in search interest for '{keyword}': "
                                   f"trend level {trend_level}/100",
                        raw_data={
                            "keyword": keyword,
                            "trend_level": trend_level,
                            "source": "simulated",
                        },
                        timestamp=now,
                        expires_at=now + timedelta(hours=12),
                    ))
        
        return signals
    
    async def _fetch_trends_data(self, keywords: List[str]) -> Optional[Dict[str, int]]:
        """Fetch real Google Trends data."""
        if not HAS_PYTRENDS:
            return None
        
        try:
            pytrends = TrendReq(hl='en-US', tz=0)
            pytrends.build_payload(keywords[:5], timeframe='now 1-d')
            
            interest = pytrends.interest_over_time()
            if not interest.empty:
                # Get most recent values
                latest = interest.iloc[-1]
                return {kw: int(latest[kw]) for kw in keywords if kw in latest}
        except Exception as e:
            print(f"⚠️ Google Trends error: {e}")
        
        return None


class SocialChatterSource(BaseSignalSource):
    """
    Social Media Sentiment Analysis
    
    Monitors Twitter/X, Reddit, Telegram for:
    - Unusual spikes in military/conflict keywords
    - Verified account activity (journalists, officials)
    - Geographic clustering of posts
    
    Real implementation would use:
    - Twitter API v2
    - Reddit API
    - Telegram API
    """
    
    KEYWORDS = {
        "military": ["troops deployed", "military convoy", "aircraft spotted", "naval movement"],
        "crisis": ["breaking", "urgent", "alert", "developing situation"],
        "conflict": ["attack", "strike", "explosion", "casualties"],
    }
    
    async def scan(self, region: RegionOfInterest) -> List[Signal]:
        signals = []
        now = datetime.now(timezone.utc)
        
        # Simulated social sentiment (would be real API in production)
        for category, keywords in self.KEYWORDS.items():
            # 12% chance of elevated chatter
            if random.random() < 0.12:
                volume_spike = random.uniform(2.0, 10.0)
                sentiment = random.uniform(-1.0, 0.2)  # Usually negative during crises
                
                level = min(1.0, volume_spike / 10)
                
                signals.append(Signal(
                    id=self._generate_signal_id("social", region.value),
                    source=SignalSource.SOCIAL_CHATTER,
                    region=region,
                    level=level,
                    confidence=0.5,  # Social media is noisy
                    description=f"Elevated {category} chatter detected for {region.value}: "
                               f"{volume_spike:.1f}x normal volume, sentiment {sentiment:.2f}",
                    raw_data={
                        "category": category,
                        "keywords_matched": random.sample(keywords, min(2, len(keywords))),
                        "volume_multiplier": round(volume_spike, 2),
                        "sentiment_score": round(sentiment, 2),
                        "source": "simulated",
                    },
                    timestamp=now,
                    expires_at=now + timedelta(hours=3),
                ))
        
        return signals


class ShippingPatternSource(BaseSignalSource):
    """
    Maritime Traffic Analysis
    
    Monitors for:
    - Tanker diversions around strategic chokepoints
    - Military vessel movements
    - Unusual port activity
    
    Real implementation: MarineTraffic API, VesselFinder
    """
    
    CHOKEPOINTS = {
        RegionOfInterest.STRAIT_HORMUZ: {"name": "Strait of Hormuz", "daily_tankers": 20},
        RegionOfInterest.SOUTH_CHINA_SEA: {"name": "South China Sea", "daily_tankers": 50},
        RegionOfInterest.BALTIC_SEA: {"name": "Baltic Sea", "daily_tankers": 30},
    }
    
    async def scan(self, region: RegionOfInterest) -> List[Signal]:
        signals = []
        
        chokepoint = self.CHOKEPOINTS.get(region)
        if not chokepoint:
            return signals
        
        now = datetime.now(timezone.utc)
        baseline = chokepoint["daily_tankers"]
        
        # Simulate traffic (10% chance of anomaly)
        if random.random() < 0.10:
            # Either spike (military buildup) or drop (avoidance)
            if random.random() < 0.5:
                multiplier = random.uniform(0.3, 0.6)  # Drop
                description = "ships avoiding"
            else:
                multiplier = random.uniform(1.5, 2.5)  # Spike
                description = "unusual concentration"
        else:
            multiplier = random.uniform(0.85, 1.15)
            description = None
        
        current = int(baseline * multiplier)
        deviation = abs(current - baseline) / baseline
        
        if deviation > 0.25 and description:
            level = min(1.0, deviation)
            
            signals.append(Signal(
                id=self._generate_signal_id("shipping", region.value),
                source=SignalSource.SHIPPING_PATTERN,
                region=region,
                level=level,
                confidence=0.75,
                description=f"Maritime anomaly at {chokepoint['name']}: "
                           f"{description} ({current} vs {baseline} baseline)",
                raw_data={
                    "chokepoint": chokepoint["name"],
                    "baseline_daily": baseline,
                    "current_count": current,
                    "deviation_pct": round(deviation * 100, 1),
                    "source": "simulated",
                },
                timestamp=now,
                expires_at=now + timedelta(hours=8),
            ))
        
        return signals


# =============================================================================
# MAIN SIGNAL DETECTOR
# =============================================================================

class SignalDetector:
    """
    The main Pizzint Engine - orchestrates all signal sources.
    
    Features:
    - Multi-source scanning
    - Signal correlation (multiple sources = higher confidence)
    - DEFCON calculation
    - Mission generation
    """
    
    def __init__(self):
        # Initialize all signal sources
        self.sources: List[BaseSignalSource] = [
            PizzaIndexSource(),
            FlightRadarSource(),
            GoogleTrendsSource(),
            SocialChatterSource(),
            ShippingPatternSource(),
        ]
        
        # Regions to monitor
        self.monitored_regions = [
            RegionOfInterest.WASHINGTON_DC,
            RegionOfInterest.MOSCOW,
            RegionOfInterest.BEIJING,
            RegionOfInterest.TAIPEI,
            RegionOfInterest.KYIV,
            RegionOfInterest.TEHRAN,
            RegionOfInterest.STRAIT_HORMUZ,
            RegionOfInterest.SOUTH_CHINA_SEA,
        ]
        
        # Active signals (decays over time)
        self.active_signals: List[Signal] = []
        
        # Current DEFCON level
        self._defcon_level = DEFCONLevel.DEFCON_5
        
        # Mission templates
        self.mission_templates = self._load_mission_templates()
    
    @property
    def defcon_level(self) -> DEFCONLevel:
        """Current threat level."""
        return self._defcon_level
    
    async def scan_all_sources(self) -> List[Signal]:
        """
        Scan all sources across all monitored regions.
        Returns list of detected signals.
        """
        all_signals = []
        
        for region in self.monitored_regions:
            for source in self.sources:
                try:
                    signals = await source.scan(region)
                    all_signals.extend(signals)
                except Exception as e:
                    print(f"⚠️ Error scanning {source.__class__.__name__} for {region}: {e}")
        
        # Update active signals (remove expired)
        self._cleanup_expired_signals()
        
        # Add new signals
        for signal in all_signals:
            if signal.id not in [s.id for s in self.active_signals]:
                self.active_signals.append(signal)
        
        # Correlate signals
        self._correlate_signals()
        
        # Update DEFCON
        self._calculate_defcon()
        
        return all_signals
    
    def scan_region(self, region: RegionOfInterest) -> List[Signal]:
        """Scan all sources for a specific region (sync wrapper)."""
        return asyncio.run(self._scan_region_async(region))
    
    async def _scan_region_async(self, region: RegionOfInterest) -> List[Signal]:
        """Async scan for a specific region."""
        signals = []
        for source in self.sources:
            try:
                region_signals = await source.scan(region)
                signals.extend(region_signals)
            except Exception as e:
                print(f"⚠️ Error: {e}")
        return signals
    
    def _cleanup_expired_signals(self):
        """Remove expired signals."""
        now = datetime.now(timezone.utc)
        self.active_signals = [s for s in self.active_signals if s.expires_at > now]
    
    def _correlate_signals(self):
        """
        Find correlated signals (multiple sources pointing to same region).
        Correlated signals increase confidence and DEFCON impact.
        """
        # Group by region
        by_region: Dict[RegionOfInterest, List[Signal]] = {}
        for signal in self.active_signals:
            if signal.region not in by_region:
                by_region[signal.region] = []
            by_region[signal.region].append(signal)
        
        # Mark correlations
        for region, signals in by_region.items():
            if len(signals) >= 2:
                # These signals are correlated
                signal_ids = [s.id for s in signals]
                for signal in signals:
                    signal.correlated_signals = [sid for sid in signal_ids if sid != signal.id]
                    # Boost confidence for correlated signals
                    signal.confidence = min(1.0, signal.confidence * 1.3)
    
    def _calculate_defcon(self):
        """
        Calculate current DEFCON level based on active signals.
        """
        if not self.active_signals:
            self._defcon_level = DEFCONLevel.DEFCON_5
            return
        
        # Calculate threat score
        threat_score = 0
        
        for signal in self.active_signals:
            base_score = signal.level * signal.confidence
            
            # Boost for correlated signals
            if signal.correlated_signals:
                correlation_boost = 1 + (len(signal.correlated_signals) * 0.3)
                base_score *= correlation_boost
            
            threat_score += base_score
        
        # Map to DEFCON
        if threat_score >= 5.0:
            self._defcon_level = DEFCONLevel.DEFCON_1
        elif threat_score >= 3.0:
            self._defcon_level = DEFCONLevel.DEFCON_2
        elif threat_score >= 1.5:
            self._defcon_level = DEFCONLevel.DEFCON_3
        elif threat_score >= 0.5:
            self._defcon_level = DEFCONLevel.DEFCON_4
        else:
            self._defcon_level = DEFCONLevel.DEFCON_5
    
    def _load_mission_templates(self) -> Dict[str, Dict]:
        """Load mission templates for different signal types."""
        return {
            SignalSource.PIZZA_INDEX.value: {
                "types": ["Covert Operation", "Crisis Response", "Emergency Mobilization"],
                "codename_prefixes": ["NIGHT", "SHADOW", "SILENT", "RAPID"],
            },
            SignalSource.FLIGHT_RADAR.value: {
                "types": ["No-Fly Zone Enforcement", "Air Superiority Mission", "Evacuation Operation"],
                "codename_prefixes": ["SKY", "FALCON", "EAGLE", "THUNDER"],
            },
            SignalSource.SHIPPING_PATTERN.value: {
                "types": ["Naval Escort Mission", "Maritime Interdiction", "Freedom of Navigation"],
                "codename_prefixes": ["TRIDENT", "NEPTUNE", "ANCHOR", "WAVE"],
            },
            SignalSource.SOCIAL_CHATTER.value: {
                "types": ["Information Operation", "Civil Unrest Response", "Diplomatic Incident"],
                "codename_prefixes": ["WHISPER", "ECHO", "SIGNAL", "BROADCAST"],
            },
            SignalSource.GOOGLE_TRENDS.value: {
                "types": ["Public Alert Assessment", "Crisis Escalation", "Mass Mobilization"],
                "codename_prefixes": ["PULSE", "TREND", "WAVE", "SURGE"],
            },
        }
    
    def generate_mission(self, signal: Signal) -> Mission:
        """
        Convert a detected signal into a betting Mission.
        """
        template = self.mission_templates.get(
            signal.source.value,
            {"types": ["Special Operation"], "codename_prefixes": ["OMEGA"]}
        )
        
        mission_type = random.choice(template["types"])
        codename_prefix = random.choice(template["codename_prefixes"])
        codename_suffix = random.choice(["DAWN", "FURY", "STORM", "STRIKE", "HAMMER", "SPEAR"])
        codename = f"OPERATION {codename_prefix} {codename_suffix}"
        
        now = datetime.now(timezone.utc)
        
        # Duration based on signal level
        if signal.level >= 0.8:
            duration_hours = 4  # Critical = very short
        elif signal.level >= 0.5:
            duration_hours = 8
        else:
            duration_hours = 12
        
        # Generate mission ID
        mission_id = f"mission_{signal.region.value}_{int(now.timestamp())}"
        
        # Calculate initial odds based on historical patterns
        # Higher signals = more uncertainty = closer to 50/50
        base_success_odds = 0.6 - (signal.level * 0.2)  # 40-60%
        
        mission = Mission(
            id=mission_id,
            codename=codename,
            title=f"{mission_type} Detected - Will It Succeed?",
            description=f"Intel Source: {signal.source.value}. {signal.description}. "
                       f"Confidence: {signal.confidence:.0%}. "
                       f"Will this operation achieve its objectives within {duration_hours} hours?",
            source_signals=[signal.id],
            region=signal.region,
            mission_type=mission_type,
            created_at=now,
            expires_at=now + timedelta(hours=duration_hours),
            duration_hours=duration_hours,
            outcomes=["SUCCESS", "FAILURE", "INCONCLUSIVE"],
            initial_odds={
                "SUCCESS": round(base_success_odds, 2),
                "FAILURE": round(1 - base_success_odds - 0.1, 2),
                "INCONCLUSIVE": 0.1,
            },
            virality_score=int(signal.level * 100),
            intel_required=signal.level >= 0.8,  # High-level signals require payment
            intel_cost_usd=0.50 if signal.level >= 0.8 else 0.0,
        )
        
        return mission
    
    def generate_missions_from_defcon(self) -> List[Mission]:
        """
        Generate missions based on current DEFCON level.
        Only generates missions at DEFCON 2 or 1.
        """
        missions = []
        
        if self._defcon_level.value > 2:
            return missions  # No missions at DEFCON 3-5
        
        # Group signals by region for correlated missions
        by_region: Dict[RegionOfInterest, List[Signal]] = {}
        for signal in self.active_signals:
            if signal.region not in by_region:
                by_region[signal.region] = []
            by_region[signal.region].append(signal)
        
        for region, signals in by_region.items():
            if len(signals) >= 2:
                # Correlated signals = compound mission
                primary_signal = max(signals, key=lambda s: s.level * s.confidence)
                mission = self.generate_mission(primary_signal)
                
                # Add all signal IDs
                mission.source_signals = [s.id for s in signals]
                
                # Boost virality for correlated
                mission.virality_score = min(100, mission.virality_score + 20)
                
                missions.append(mission)
            elif signals and signals[0].level >= 0.7:
                # Single high-level signal
                missions.append(self.generate_mission(signals[0]))
        
        return missions
    
    def get_status(self) -> Dict:
        """Get current detector status."""
        return {
            "defcon_level": self._defcon_level.value,
            "defcon_name": self._defcon_level.name,
            "active_signals": len(self.active_signals),
            "signals_by_region": self._count_by_region(),
            "signals_by_source": self._count_by_source(),
            "top_signals": [s.to_dict() for s in sorted(
                self.active_signals,
                key=lambda s: s.level * s.confidence,
                reverse=True
            )[:5]],
        }
    
    def _count_by_region(self) -> Dict[str, int]:
        counts = {}
        for signal in self.active_signals:
            key = signal.region.value
            counts[key] = counts.get(key, 0) + 1
        return counts
    
    def _count_by_source(self) -> Dict[str, int]:
        counts = {}
        for signal in self.active_signals:
            key = signal.source.value
            counts[key] = counts.get(key, 0) + 1
        return counts


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

# Global instance
_detector_instance: Optional[SignalDetector] = None


def get_detector() -> SignalDetector:
    """Get or create global detector instance."""
    global _detector_instance
    if _detector_instance is None:
        _detector_instance = SignalDetector()
    return _detector_instance


async def scan_for_missions() -> Tuple[List[Signal], List[Mission]]:
    """
    Quick helper to scan and generate any triggered missions.
    """
    detector = get_detector()
    signals = await detector.scan_all_sources()
    missions = detector.generate_missions_from_defcon()
    return signals, missions


# =============================================================================
# TESTING
# =============================================================================

if __name__ == "__main__":
    async def demo():
        print("=" * 70)
        print("🕵️ SIGNAL DETECTOR (Pizzint Engine) - Demo")
        print("=" * 70)
        
        detector = SignalDetector()
        
        # Run multiple scans to accumulate signals
        print("\n📡 Scanning all sources...")
        for i in range(3):
            signals = await detector.scan_all_sources()
            print(f"  Scan {i+1}: Found {len(signals)} new signals")
        
        # Show status
        status = detector.get_status()
        print(f"\n🚨 DEFCON Level: {status['defcon_level']} ({status['defcon_name']})")
        print(f"📊 Active Signals: {status['active_signals']}")
        
        if status['signals_by_region']:
            print("\n📍 Signals by Region:")
            for region, count in status['signals_by_region'].items():
                print(f"   {region}: {count}")
        
        if status['signals_by_source']:
            print("\n🔍 Signals by Source:")
            for source, count in status['signals_by_source'].items():
                print(f"   {source}: {count}")
        
        if status['top_signals']:
            print("\n⚠️ Top Signals:")
            for sig in status['top_signals']:
                print(f"   [{sig['severity']}] {sig['source']} @ {sig['region']}")
                print(f"      {sig['description'][:70]}...")
        
        # Generate missions if DEFCON is low enough
        missions = detector.generate_missions_from_defcon()
        if missions:
            print(f"\n🎯 MISSIONS GENERATED: {len(missions)}")
            for mission in missions:
                print(f"\n   {mission.codename}")
                print(f"   Type: {mission.mission_type}")
                print(f"   Region: {mission.region.value}")
                print(f"   Duration: {mission.duration_hours}h")
                print(f"   Virality: {mission.virality_score}")
                print(f"   Intel Required: {mission.intel_required}")
        else:
            print("\n✅ No missions triggered (DEFCON not critical enough)")
        
        print("\n" + "=" * 70)
    
    asyncio.run(demo())




