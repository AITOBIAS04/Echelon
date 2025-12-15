"""
OSINT Signal Sources - Part 1: Geopolitics ("The Situation Room")
==================================================================
Advanced signal detection for geopolitical events.

Sources:
- VIP Aircraft Tracking (ADS-B)
- Marine Traffic (AIS)
- Night Lights (Satellite)
- Internet Outages

These signals help predict conflicts, troop movements, and diplomatic
crises BEFORE mainstream news reports them.
"""
import os
import random
import asyncio
import hashlib
from math import cos, radians, sin, sqrt, atan2
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

# Optional imports
try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False

# Import base classes from signal_detector
try:
    from backend.core.signal_detector import (
        BaseSignalSource, Signal, SignalSource, RegionOfInterest
    )
except ImportError:
    from backend.core.signal_detector import (
        BaseSignalSource, Signal, SignalSource, RegionOfInterest
    )

# =============================================================================
# AIRCRAFT TRACKING (ADS-B) - "Where is the Secretary of State's plane?"
# =============================================================================

class AircraftType(Enum):
    """Types of aircraft we track."""
    VIP_GOVERNMENT = "vip_government"      # Air Force One, diplomatic jets
    MILITARY_CARGO = "military_cargo"      # C-17, C-130, AN-124
    MILITARY_FIGHTER = "military_fighter"  # F-35, Su-57, etc.
    TANKER_REFUEL = "tanker_refuel"        # KC-135, aerial refueling
    SURVEILLANCE = "surveillance"           # E-3 AWACS, RC-135, drones
    EXECUTIVE = "executive"                 # Corporate jets at unusual locations

@dataclass
class TrackedAircraft:
    """An aircraft being monitored."""
    icao24: str                    # Unique transponder code
    callsign: str
    aircraft_type: AircraftType
    country: str
    lat: float
    lng: float
    altitude_ft: float
    speed_knots: float
    heading: float
    on_ground: bool
    last_seen: datetime
    
    # Derived
    origin: Optional[str] = None
    destination: Optional[str] = None
    is_unusual: bool = False
    unusual_reason: str = ""

class VIPAircraftSource(BaseSignalSource):
    """
    VIP & Military Aircraft Tracking via ADS-B
    
    Monitors for:
    - Government VIP jets in unusual locations
    - Military cargo planes (troop/equipment movement)
    - Surveillance aircraft (AWACS, reconnaissance)
    - Aerial refueling tankers (indicates extended operations)
    
    Real API: OpenSky Network, ADSBexchange
    """
    
    # Known VIP/Military aircraft to track
    TRACKED_AIRCRAFT = {
        # US Government
        "92-9000": {"name": "Air Force One (VC-25A)", "country": "USA", "type": AircraftType.VIP_GOVERNMENT},
        "98-0001": {"name": "Air Force Two (C-32A)", "country": "USA", "type": AircraftType.VIP_GOVERNMENT},
        "09-0015": {"name": "USAF C-17 Globemaster", "country": "USA", "type": AircraftType.MILITARY_CARGO},
        "09-0016": {"name": "USAF C-17 Globemaster", "country": "USA", "type": AircraftType.MILITARY_CARGO},
        
        # Russian
        "RA-96019": {"name": "Russian Presidential IL-96", "country": "RUS", "type": AircraftType.VIP_GOVERNMENT},
        "RF-78650": {"name": "Russian Military IL-76", "country": "RUS", "type": AircraftType.MILITARY_CARGO},
        
        # Chinese
        "B-2472": {"name": "Chinese Government 747", "country": "CHN", "type": AircraftType.VIP_GOVERNMENT},
        
        # Surveillance
        "AWACS": {"name": "E-3 Sentry AWACS", "country": "NATO", "type": AircraftType.SURVEILLANCE},
        "JSTARS": {"name": "E-8 Joint STARS", "country": "USA", "type": AircraftType.SURVEILLANCE},
    }
    
    # Sensitive locations that trigger alerts
    SENSITIVE_LOCATIONS = {
        "ramstein": {"lat": 49.4369, "lng": 7.6003, "name": "Ramstein Air Base", "significance": "US/NATO Europe HQ"},
        "incirlik": {"lat": 37.0011, "lng": 35.4259, "name": "Incirlik Air Base", "significance": "NATO Turkey, nuclear capable"},
        "diego_garcia": {"lat": -7.3195, "lng": 72.4229, "name": "Diego Garcia", "significance": "US Indian Ocean base"},
        "guam": {"lat": 13.4443, "lng": 144.7937, "name": "Andersen AFB Guam", "significance": "US Pacific Command"},
        "thule": {"lat": 76.5312, "lng": -68.7031, "name": "Thule Air Base", "significance": "Arctic early warning"},
        "cairo": {"lat": 30.1219, "lng": 31.4056, "name": "Cairo International", "significance": "Mideast diplomacy hub"},
        "tel_aviv": {"lat": 32.0055, "lng": 34.8854, "name": "Ben Gurion Airport", "significance": "Israel"},
        "tehran": {"lat": 35.6892, "lng": 51.3890, "name": "Tehran Mehrabad", "significance": "Iran"},
    }
    
    async def scan(self, region: RegionOfInterest) -> List[Signal]:
        signals = []
        now = datetime.now(timezone.utc)
        
        # Try real OpenSky API
        real_aircraft = await self._fetch_opensky_data(region)
        
        if real_aircraft:
            for aircraft in real_aircraft:
                if aircraft.is_unusual:
                    signals.append(self._create_signal(aircraft, region, now))
        else:
            # Simulated fallback
            signals.extend(await self._simulate_aircraft_signals(region, now))
        
        return signals
    
    async def _fetch_opensky_data(self, region: RegionOfInterest) -> List[TrackedAircraft]:
        """Fetch real aircraft data from OpenSky Network."""
        if not HAS_HTTPX:
            return []
        
        # Get bounding box for region
        bbox = self._get_region_bbox(region)
        if not bbox:
            return []
        
        try:
            url = "https://opensky-network.org/api/states/all"
            params = {
                "lamin": bbox["lat_min"],
                "lamax": bbox["lat_max"],
                "lomin": bbox["lng_min"],
                "lomax": bbox["lng_max"],
            }
            
            async with httpx.AsyncClient(timeout=15) as client:
                response = await client.get(url, params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    if data is None:
                        return []
                    return self._parse_opensky_response(data)
        except Exception as e:
            print(f"⚠️ OpenSky Aircraft API error: {e}")
        
        return []
    
    def _parse_opensky_response(self, data: Dict) -> List[TrackedAircraft]:
        """Parse OpenSky API response into TrackedAircraft objects."""
        aircraft = []
        if not data:
            return aircraft
        
        states = data.get("states")
        if states is None or not isinstance(states, list):
            return aircraft
        
        for state in states:
            if len(state) < 17:
                continue
            
            icao24 = state[0]
            callsign = (state[1] or "").strip()
            
            # Check if this is a tracked aircraft
            tracked_info = None
            for tracked_id, info in self.TRACKED_AIRCRAFT.items():
                if tracked_id in icao24 or tracked_id in callsign:
                    tracked_info = info
                    break
            
            # Also detect military by callsign patterns
            military_prefixes = ["RCH", "REACH", "EVAC", "DUKE", "BOXER", "HEAVY"]
            is_military = any(callsign.startswith(p) for p in military_prefixes)
            
            if tracked_info or is_military:
                lat = state[6]
                lng = state[5]
                
                if lat is None or lng is None:
                    continue
                
                ac = TrackedAircraft(
                    icao24=icao24,
                    callsign=callsign,
                    aircraft_type=tracked_info["type"] if tracked_info else AircraftType.MILITARY_CARGO,
                    country=tracked_info["country"] if tracked_info else "UNKNOWN",
                    lat=lat,
                    lng=lng,
                    altitude_ft=(state[7] or 0) * 3.281,  # meters to feet
                    speed_knots=(state[9] or 0) * 1.944,  # m/s to knots
                    heading=state[10] or 0,
                    on_ground=state[8] or False,
                    last_seen=datetime.now(timezone.utc),
                )
                
                # Check if near sensitive location
                for loc_id, loc_info in self.SENSITIVE_LOCATIONS.items():
                    dist = self._haversine_distance(lat, lng, loc_info["lat"], loc_info["lng"])
                    if dist < 100:  # Within 100km
                        ac.is_unusual = True
                        ac.unusual_reason = f"Near {loc_info['name']} ({loc_info['significance']})"
                        ac.destination = loc_info["name"]
                        break
                
                aircraft.append(ac)
        
        return aircraft
    
    async def _simulate_aircraft_signals(self, region: RegionOfInterest, now: datetime) -> List[Signal]:
        """Generate simulated aircraft signals for demo."""
        signals = []
        
        # 10% chance of VIP aircraft movement
        if random.random() < 0.10:
            scenarios = [
                {
                    "callsign": "SAM 38",
                    "type": "VIP Government Jet",
                    "desc": "US State Department aircraft detected landing in Cairo",
                    "significance": "Potential emergency diplomatic mission",
                },
                {
                    "callsign": "RCH 871",
                    "type": "C-17 Globemaster",
                    "desc": "USAF heavy cargo aircraft en route to Ramstein",
                    "significance": "Possible troop/equipment deployment",
                },
                {
                    "callsign": "AWACS 1",
                    "type": "E-3 Sentry",
                    "desc": "NATO AWACS orbiting over Baltic Sea",
                    "significance": "Increased surveillance activity",
                },
                {
                    "callsign": "RA-96019",
                    "type": "Russian Presidential IL-96",
                    "desc": "Russian government aircraft departed Moscow",
                    "significance": "High-level diplomatic movement",
                },
            ]
            
            scenario = random.choice(scenarios)
            level = random.uniform(0.6, 0.9)
            
            signals.append(Signal(
                id=self._generate_signal_id("aircraft", region.value),
                source=SignalSource.FLIGHT_RADAR,
                region=region,
                level=level,
                confidence=0.85,
                description=f"✈️ {scenario['type']} ({scenario['callsign']}): {scenario['desc']}. {scenario['significance']}",
                raw_data={
                    "callsign": scenario["callsign"],
                    "aircraft_type": scenario["type"],
                    "scenario": scenario["desc"],
                    "source": "simulated",
                },
                timestamp=now,
                expires_at=now + timedelta(hours=4),
            ))
        
        return signals
    
    def _create_signal(self, aircraft: TrackedAircraft, region: RegionOfInterest, now: datetime) -> Signal:
        """Create a signal from a tracked aircraft."""
        return Signal(
            id=self._generate_signal_id("aircraft", aircraft.icao24),
            source=SignalSource.FLIGHT_RADAR,
            region=region,
            level=0.75,
            confidence=0.9,
            description=f"✈️ {aircraft.aircraft_type.value} ({aircraft.callsign}): {aircraft.unusual_reason}",
            raw_data={
                "icao24": aircraft.icao24,
                "callsign": aircraft.callsign,
                "type": aircraft.aircraft_type.value,
                "country": aircraft.country,
                "lat": aircraft.lat,
                "lng": aircraft.lng,
                "altitude_ft": aircraft.altitude_ft,
                "destination": aircraft.destination,
                "source": "opensky",
            },
            timestamp=now,
            expires_at=now + timedelta(hours=4),
        )
    
    def _get_region_bbox(self, region: RegionOfInterest) -> Optional[Dict]:
        """Get bounding box for a region."""
        boxes = {
            RegionOfInterest.WASHINGTON_DC: {"lat_min": 38.0, "lat_max": 40.0, "lng_min": -78.0, "lng_max": -76.0},
            RegionOfInterest.MOSCOW: {"lat_min": 54.5, "lat_max": 56.5, "lng_min": 36.5, "lng_max": 38.5},
            RegionOfInterest.BEIJING: {"lat_min": 39.0, "lat_max": 41.0, "lng_min": 115.0, "lng_max": 118.0},
            RegionOfInterest.KYIV: {"lat_min": 49.0, "lat_max": 52.0, "lng_min": 29.0, "lng_max": 32.0},
            RegionOfInterest.TAIPEI: {"lat_min": 24.0, "lat_max": 26.0, "lng_min": 120.0, "lng_max": 122.5},
            RegionOfInterest.TEHRAN: {"lat_min": 34.5, "lat_max": 36.5, "lng_min": 50.0, "lng_max": 52.5},
            RegionOfInterest.BALTIC_SEA: {"lat_min": 54.0, "lat_max": 60.0, "lng_min": 12.0, "lng_max": 28.0},
        }
        return boxes.get(region)
    
    def _haversine_distance(self, lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """Calculate distance between two points in km."""
        R = 6371  # Earth's radius in km
        
        lat1_rad = radians(lat1)
        lat2_rad = radians(lat2)
        delta_lat = radians(lat2 - lat1)
        delta_lng = radians(lng2 - lng1)
        
        a = sin(delta_lat/2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(delta_lng/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        
        return R * c

# =============================================================================
# MARINE TRAFFIC (AIS) - "Why are tankers bunching up?"
# =============================================================================

class VesselType(Enum):
    """Types of vessels we track."""
    OIL_TANKER = "oil_tanker"
    LNG_CARRIER = "lng_carrier"
    CARGO_CONTAINER = "cargo_container"
    BULK_CARRIER = "bulk_carrier"
    NAVAL_WARSHIP = "naval_warship"
    NAVAL_SUBMARINE = "naval_submarine"  # When surfaced
    RESEARCH = "research"  # Sometimes cover for military
    DARK_VESSEL = "dark_vessel"  # Transponder off

@dataclass
class TrackedVessel:
    """A vessel being monitored."""
    mmsi: str                      # Maritime Mobile Service Identity
    name: str
    vessel_type: VesselType
    flag: str
    lat: float
    lng: float
    speed_knots: float
    heading: float
    destination: Optional[str]
    last_seen: datetime
    
    # Anomaly detection
    is_dark: bool = False          # Transponder off
    is_loitering: bool = False     # Not moving
    is_unusual_route: bool = False

class MarineTrafficSource(BaseSignalSource):
    """
    Marine Traffic Monitoring via AIS
    
    Monitors for:
    - Tanker bunching (supply shock indicators)
    - Dark vessels (transponder off = suspicious)
    - Naval fleet movements
    - Chokepoint congestion (Hormuz, Suez, Malacca)
    
    Real API: MarineTraffic, VesselFinder, AISHub
    """
    
    # Strategic maritime chokepoints
    CHOKEPOINTS = {
        "hormuz": {
            "name": "Strait of Hormuz",
            "lat": 26.5667, "lng": 56.2500,
            "daily_tankers": 21,  # ~21 million barrels/day pass through
            "significance": "20% of global oil trade",
        },
        "malacca": {
            "name": "Strait of Malacca",
            "lat": 2.5, "lng": 101.5,
            "daily_tankers": 50,
            "significance": "25% of global trade",
        },
        "suez": {
            "name": "Suez Canal",
            "lat": 30.4583, "lng": 32.3500,
            "daily_tankers": 50,
            "significance": "12% of global trade",
        },
        "bab_el_mandeb": {
            "name": "Bab el-Mandeb",
            "lat": 12.5833, "lng": 43.3333,
            "daily_tankers": 15,
            "significance": "Red Sea chokepoint",
        },
        "taiwan_strait": {
            "name": "Taiwan Strait",
            "lat": 24.5, "lng": 119.5,
            "daily_tankers": 40,
            "significance": "Major shipping lane",
        },
    }
    
    async def scan(self, region: RegionOfInterest) -> List[Signal]:
        signals = []
        now = datetime.now(timezone.utc)
        
        # Map regions to chokepoints
        region_chokepoints = {
            RegionOfInterest.STRAIT_HORMUZ: "hormuz",
            RegionOfInterest.SOUTH_CHINA_SEA: "malacca",
            RegionOfInterest.TAIPEI: "taiwan_strait",
        }
        
        chokepoint_id = region_chokepoints.get(region)
        if chokepoint_id:
            signals.extend(await self._scan_chokepoint(chokepoint_id, now))
        
        # Also scan for naval movements
        signals.extend(await self._scan_naval_activity(region, now))
        
        return signals
    
    async def _scan_chokepoint(self, chokepoint_id: str, now: datetime) -> List[Signal]:
        """Scan a chokepoint for anomalies."""
        signals = []
        chokepoint = self.CHOKEPOINTS.get(chokepoint_id)
        
        if not chokepoint:
            return signals
        
        # Simulate traffic analysis (real would use AIS API)
        baseline = chokepoint["daily_tankers"]
        
        # 8% chance of anomaly
        if random.random() < 0.08:
            anomaly_type = random.choice(["congestion", "avoidance", "dark_vessels"])
            
            if anomaly_type == "congestion":
                current = int(baseline * random.uniform(1.5, 2.5))
                desc = f"Unusual vessel congestion at {chokepoint['name']}: {current} ships vs {baseline} normal"
                level = 0.7
            elif anomaly_type == "avoidance":
                current = int(baseline * random.uniform(0.3, 0.6))
                desc = f"Vessels avoiding {chokepoint['name']}: Only {current} ships vs {baseline} normal"
                level = 0.85
            else:  # dark_vessels
                dark_count = random.randint(3, 10)
                desc = f"{dark_count} vessels went 'dark' (transponders off) near {chokepoint['name']}"
                level = 0.9
            
            # Map chokepoint to region
            region_map = {
                "hormuz": RegionOfInterest.STRAIT_HORMUZ,
                "malacca": RegionOfInterest.SOUTH_CHINA_SEA,
                "taiwan_strait": RegionOfInterest.TAIPEI,
            }
            region = region_map.get(chokepoint_id, RegionOfInterest.STRAIT_HORMUZ)
            
            signals.append(Signal(
                id=self._generate_signal_id("marine", chokepoint_id),
                source=SignalSource.SHIPPING_PATTERN,
                region=region,
                level=level,
                confidence=0.8,
                description=f"🚢 {desc}. Significance: {chokepoint['significance']}",
                raw_data={
                    "chokepoint": chokepoint["name"],
                    "anomaly_type": anomaly_type,
                    "baseline_daily": baseline,
                    "significance": chokepoint["significance"],
                    "source": "simulated",
                },
                timestamp=now,
                expires_at=now + timedelta(hours=6),
            ))
        
        return signals
    
    async def _scan_naval_activity(self, region: RegionOfInterest, now: datetime) -> List[Signal]:
        """Scan for naval fleet movements."""
        signals = []
        
        # 6% chance of naval activity signal
        if random.random() < 0.06:
            naval_scenarios = [
                {
                    "fleet": "US Carrier Strike Group",
                    "activity": "transiting South China Sea",
                    "significance": "Freedom of Navigation operation",
                    "region": RegionOfInterest.SOUTH_CHINA_SEA,
                },
                {
                    "fleet": "Russian Baltic Fleet",
                    "activity": "conducting exercises near Kaliningrad",
                    "significance": "Show of force near NATO borders",
                    "region": RegionOfInterest.BALTIC_SEA,
                },
                {
                    "fleet": "Chinese PLAN vessels",
                    "activity": "increased presence near Taiwan",
                    "significance": "Possible coercion/exercise",
                    "region": RegionOfInterest.TAIPEI,
                },
                {
                    "fleet": "Iranian Revolutionary Guard Navy",
                    "activity": "fast boats shadowing tankers",
                    "significance": "Potential interdiction threat",
                    "region": RegionOfInterest.STRAIT_HORMUZ,
                },
            ]
            
            # Filter for relevant region
            relevant = [s for s in naval_scenarios if s["region"] == region]
            
            if relevant:
                scenario = random.choice(relevant)
                
                signals.append(Signal(
                    id=self._generate_signal_id("naval", region.value),
                    source=SignalSource.SHIPPING_PATTERN,
                    region=region,
                    level=random.uniform(0.65, 0.85),
                    confidence=0.75,
                    description=f"⚓ Naval Activity: {scenario['fleet']} {scenario['activity']}. {scenario['significance']}",
                    raw_data={
                        "fleet": scenario["fleet"],
                        "activity": scenario["activity"],
                        "significance": scenario["significance"],
                        "source": "simulated",
                    },
                    timestamp=now,
                    expires_at=now + timedelta(hours=8),
                ))
        
        return signals

# =============================================================================
# NIGHT LIGHTS (Satellite Imagery) - "Why did the lights go out?"
# =============================================================================

class NightLightsSource(BaseSignalSource):
    """
    Satellite Night Lights Analysis
    
    Monitors for:
    - Sudden darkness (power grid failure, attack)
    - Sudden brightness (military mobilization, refugee camps)
    - Gradual changes (economic activity trends)
    
    Real API: NASA Black Marble, VIIRS DNB
    """
    
    # Locations to monitor
    MONITORED_LOCATIONS = {
        RegionOfInterest.KYIV: {
            "name": "Kyiv, Ukraine",
            "baseline_luminosity": 0.75,
            "significance": "Capital city, infrastructure target",
        },
        RegionOfInterest.TEHRAN: {
            "name": "Tehran, Iran",
            "baseline_luminosity": 0.70,
            "significance": "Capital, potential sanctions impact",
        },
        RegionOfInterest.PYONGYANG: {
            "name": "Pyongyang, DPRK",
            "baseline_luminosity": 0.20,  # Already very dark
            "significance": "Regime stability indicator",
        },
        RegionOfInterest.TAIPEI: {
            "name": "Taiwan",
            "baseline_luminosity": 0.85,
            "significance": "Economic activity, crisis indicator",
        },
    }
    
    async def scan(self, region: RegionOfInterest) -> List[Signal]:
        signals = []
        now = datetime.now(timezone.utc)
        
        location = self.MONITORED_LOCATIONS.get(region)
        if not location:
            return signals
        
        # Simulate luminosity reading
        baseline = location["baseline_luminosity"]
        
        # 5% chance of anomaly
        if random.random() < 0.05:
            anomaly_type = random.choice(["blackout", "surge", "gradual_decline"])
            
            if anomaly_type == "blackout":
                current = baseline * random.uniform(0.1, 0.4)
                change_pct = ((current - baseline) / baseline) * 100
                desc = f"Sudden darkness detected over {location['name']}: {abs(change_pct):.0f}% decrease in night lights"
                level = 0.9
            elif anomaly_type == "surge":
                current = baseline * random.uniform(1.3, 1.8)
                change_pct = ((current - baseline) / baseline) * 100
                desc = f"Unusual brightness over {location['name']}: {change_pct:.0f}% increase (possible military activity)"
                level = 0.75
            else:
                current = baseline * random.uniform(0.6, 0.8)
                change_pct = ((current - baseline) / baseline) * 100
                desc = f"Gradual luminosity decline in {location['name']}: {abs(change_pct):.0f}% (economic/infrastructure stress)"
                level = 0.5
            
            signals.append(Signal(
                id=self._generate_signal_id("lights", region.value),
                source=SignalSource.SATELLITE_PROXY,
                region=region,
                level=level,
                confidence=0.7,
                description=f"🛰️ {desc}. {location['significance']}",
                raw_data={
                    "location": location["name"],
                    "baseline_luminosity": baseline,
                    "current_luminosity": round(current, 3),
                    "change_pct": round(change_pct, 1),
                    "anomaly_type": anomaly_type,
                    "source": "simulated",
                },
                timestamp=now,
                expires_at=now + timedelta(hours=12),
            ))
        
        return signals

# =============================================================================
# INTERNET OUTAGES - "The digital canary"
# =============================================================================

class InternetOutageSource(BaseSignalSource):
    """
    Internet Connectivity Monitoring
    
    Monitors for:
    - Regional outages (censorship, cyberattack)
    - BGP hijacks (route manipulation)
    - Undersea cable cuts
    
    Real API: IODA, NetBlocks, Cloudflare Radar
    """
    
    # Countries/regions to monitor
    MONITORED_NETWORKS = {
        RegionOfInterest.TEHRAN: {
            "country": "Iran",
            "asns": ["AS12880", "AS44244"],  # Major Iranian ISPs
            "baseline_connectivity": 0.95,
            "censorship_prone": True,
        },
        RegionOfInterest.MOSCOW: {
            "country": "Russia",
            "asns": ["AS12389", "AS8402"],
            "baseline_connectivity": 0.98,
            "censorship_prone": True,
        },
        RegionOfInterest.BEIJING: {
            "country": "China",
            "asns": ["AS4134", "AS4837"],
            "baseline_connectivity": 0.99,
            "censorship_prone": True,
        },
        RegionOfInterest.KYIV: {
            "country": "Ukraine",
            "asns": ["AS13249", "AS6849"],
            "baseline_connectivity": 0.92,
            "censorship_prone": False,
        },
        RegionOfInterest.PYONGYANG: {
            "country": "North Korea",
            "asns": ["AS131279"],
            "baseline_connectivity": 0.30,  # Very limited internet
            "censorship_prone": True,
        },
    }
    
    async def scan(self, region: RegionOfInterest) -> List[Signal]:
        signals = []
        now = datetime.now(timezone.utc)
        
        network = self.MONITORED_NETWORKS.get(region)
        if not network:
            return signals
        
        # Try real IODA API
        real_data = await self._fetch_ioda_data(network["country"])
        
        if real_data:
            if real_data["outage_detected"]:
                signals.append(self._create_outage_signal(region, network, real_data, now))
        else:
            # Simulated fallback
            signals.extend(await self._simulate_outage(region, network, now))
        
        return signals
    
    async def _fetch_ioda_data(self, country: str) -> Optional[Dict]:
        """Fetch real outage data from IODA."""
        if not HAS_HTTPX:
            return None
        
        # IODA API endpoint (simplified)
        # Real implementation would use: https://api.ioda.inetintel.cc.gatech.edu/
        try:
            # For demo, we'll skip actual API call
            # In production, implement proper IODA integration
            pass
        except Exception as e:
            print(f"⚠️ IODA API error: {e}")
        
        return None
    
    async def _simulate_outage(self, region: RegionOfInterest, network: Dict, now: datetime) -> List[Signal]:
        """Simulate internet outage signals."""
        signals = []
        
        # Higher chance for censorship-prone countries
        outage_chance = 0.08 if network["censorship_prone"] else 0.03
        
        if random.random() < outage_chance:
            outage_types = [
                {
                    "type": "regional_blackout",
                    "desc": f"Major internet outage detected in {network['country']}",
                    "cause": random.choice(["government order", "infrastructure failure", "cyberattack"]),
                    "level": 0.9,
                },
                {
                    "type": "bgp_anomaly",
                    "desc": f"BGP routing anomaly affecting {network['country']} networks",
                    "cause": "route hijacking or misconfiguration",
                    "level": 0.7,
                },
                {
                    "type": "throttling",
                    "desc": f"Significant bandwidth throttling in {network['country']}",
                    "cause": "possible censorship of specific services",
                    "level": 0.5,
                },
            ]
            
            outage = random.choice(outage_types)
            
            # Calculate connectivity drop
            current = network["baseline_connectivity"] * random.uniform(0.1, 0.5)
            drop_pct = ((network["baseline_connectivity"] - current) / network["baseline_connectivity"]) * 100
            
            signals.append(Signal(
                id=self._generate_signal_id("internet", region.value),
                source=SignalSource.POWER_GRID,  # Using power_grid as proxy for infrastructure
                region=region,
                level=outage["level"],
                confidence=0.85,
                description=f"🌐 {outage['desc']}: {drop_pct:.0f}% connectivity drop. Likely cause: {outage['cause']}",
                raw_data={
                    "country": network["country"],
                    "outage_type": outage["type"],
                    "baseline_connectivity": network["baseline_connectivity"],
                    "current_connectivity": round(current, 3),
                    "drop_pct": round(drop_pct, 1),
                    "likely_cause": outage["cause"],
                    "censorship_prone": network["censorship_prone"],
                    "source": "simulated",
                },
                timestamp=now,
                expires_at=now + timedelta(hours=3),
            ))
        
        return signals
    
    def _create_outage_signal(self, region: RegionOfInterest, network: Dict, data: Dict, now: datetime) -> Signal:
        """Create signal from real outage data."""
        return Signal(
            id=self._generate_signal_id("internet", region.value),
            source=SignalSource.POWER_GRID,
            region=region,
            level=0.85,
            confidence=0.95,
            description=f"🌐 Internet outage in {network['country']}: {data.get('description', 'Connectivity disruption detected')}",
            raw_data={
                **data,
                "country": network["country"],
                "source": "ioda",
            },
            timestamp=now,
            expires_at=now + timedelta(hours=3),
        )

# =============================================================================
# EXPORT ALL SITUATION ROOM SOURCES
# =============================================================================

SITUATION_ROOM_SOURCES = [
    VIPAircraftSource,
    MarineTrafficSource,
    NightLightsSource,
    InternetOutageSource,
]

def get_situation_room_sources() -> List[BaseSignalSource]:
    """Get instances of all Situation Room signal sources."""
    return [source() for source in SITUATION_ROOM_SOURCES]

# Backward compatibility alias
def get_war_room_sources() -> List[BaseSignalSource]:
    """Alias for backward compatibility."""
    return get_situation_room_sources()

# =============================================================================
# TESTING
# =============================================================================

if __name__ == "__main__":
    async def test():
        print("=" * 60)
        print("🎭 SITUATION ROOM SIGNAL SOURCES - Test")
        print("=" * 60)
        
        sources = get_situation_room_sources()
        
        for source in sources:
            print(f"\n📡 Testing {source.__class__.__name__}...")
            
            for region in [RegionOfInterest.WASHINGTON_DC, RegionOfInterest.TAIPEI, 
                          RegionOfInterest.STRAIT_HORMUZ, RegionOfInterest.KYIV]:
                signals = await source.scan(region)
                if signals:
                    for sig in signals:
                        print(f"  [{sig.severity}] {sig.region.value}: {sig.description[:60]}...")
        
        print("\n" + "=" * 60)
    
    asyncio.run(test())

