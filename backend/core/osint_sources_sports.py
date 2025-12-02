"""
OSINT Signal Sources - Part 3: Sports ("The Edge")
===================================================
Alternative data signals for sports betting predictions.

Sources:
- Hyper-Local Weather (stadium conditions)
- Player Social Sentiment (injury/drama signals)
- Training Camp Intelligence (lineup hints)
- Team Travel Patterns (fatigue indicators)

These signals give sports bettors an edge beyond basic statistics.
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
# CUSTOM SIGNAL SOURCE FOR SPORTS
# =============================================================================

class SportsSignalSource(Enum):
    """Sports-specific signal sources."""
    WEATHER = "weather"
    SOCIAL_SENTIMENT = "social_sentiment"
    TRAINING_INTEL = "training_intel"
    TRAVEL_FATIGUE = "travel_fatigue"
    INJURY_RUMORS = "injury_rumors"
    LINEUP_HINTS = "lineup_hints"

# =============================================================================
# STADIUM DATA
# =============================================================================

@dataclass
class Stadium:
    """A stadium with its location and sport."""
    name: str
    team: str
    sport: str  # NFL, NBA, MLB, Soccer
    city: str
    lat: float
    lng: float
    is_outdoor: bool
    capacity: int

# Major stadiums database
STADIUMS = [
    # NFL (Outdoor matters a lot)
    Stadium("Soldier Field", "Chicago Bears", "NFL", "Chicago", 41.8623, -87.6167, True, 61500),
    Stadium("Lambeau Field", "Green Bay Packers", "NFL", "Green Bay", 44.5013, -88.0622, True, 81441),
    Stadium("Arrowhead Stadium", "Kansas City Chiefs", "NFL", "Kansas City", 39.0489, -94.4839, True, 76416),
    Stadium("Highmark Stadium", "Buffalo Bills", "NFL", "Buffalo", 42.7738, -78.7870, True, 71608),
    Stadium("MetLife Stadium", "NY Giants/Jets", "NFL", "East Rutherford", 40.8128, -74.0742, True, 82500),
    
    # NBA (Indoor - less weather impact)
    Stadium("Madison Square Garden", "NY Knicks", "NBA", "New York", 40.7505, -73.9934, False, 19812),
    Stadium("United Center", "Chicago Bulls", "NBA", "Chicago", 41.8807, -87.6742, False, 20917),
    Stadium("Chase Center", "Golden State Warriors", "NBA", "San Francisco", 37.7680, -122.3878, False, 18064),
    
    # MLB (Weather critical for hitting/pitching)
    Stadium("Wrigley Field", "Chicago Cubs", "MLB", "Chicago", 41.9484, -87.6553, True, 41649),
    Stadium("Fenway Park", "Boston Red Sox", "MLB", "Boston", 42.3467, -71.0972, True, 37755),
    Stadium("Coors Field", "Colorado Rockies", "MLB", "Denver", 39.7559, -104.9942, True, 50144),  # Altitude!
    
    # Soccer (Premier League)
    Stadium("Old Trafford", "Manchester United", "Soccer", "Manchester", 53.4631, -2.2913, True, 74310),
    Stadium("Anfield", "Liverpool", "Soccer", "Liverpool", 53.4308, -2.9609, True, 53394),
    Stadium("Emirates Stadium", "Arsenal", "Soccer", "London", 51.5549, -0.1084, True, 60704),
    Stadium("Stamford Bridge", "Chelsea", "Soccer", "London", 51.4817, -0.1910, True, 40343),
    Stadium("Etihad Stadium", "Manchester City", "Soccer", "Manchester", 53.4831, -2.2004, True, 53400),
]

# =============================================================================
# HYPER-LOCAL WEATHER - "Wind at the stadium"
# =============================================================================

@dataclass
class StadiumWeather:
    """Weather conditions at a specific stadium."""
    stadium: str
    temperature_f: float
    wind_speed_mph: float
    wind_direction: str
    precipitation_chance: float  # 0-1
    humidity: float  # 0-1
    conditions: str  # "Clear", "Rain", "Snow", etc.

class StadiumWeatherSource(BaseSignalSource):
    """
    Hyper-Local Stadium Weather Intelligence
    
    Monitors:
    - Wind speed/direction (affects passing, field goals, hitting)
    - Temperature extremes (player performance)
    - Precipitation (ball handling, field conditions)
    - Humidity (pitcher grip, endurance)
    
    Real API: OpenWeatherMap, Weather.gov
    """
    
    async def scan(self, region: RegionOfInterest) -> List[Signal]:
        signals = []
        now = datetime.now(timezone.utc)
        
        # Sports signals are not region-specific in our system
        # We'll check a random selection of stadiums
        
        # Select 3 random outdoor stadiums to check
        outdoor_stadiums = [s for s in STADIUMS if s.is_outdoor]
        check_stadiums = random.sample(outdoor_stadiums, min(3, len(outdoor_stadiums)))
        
        for stadium in check_stadiums:
            weather = await self._get_stadium_weather(stadium)
            signal = self._analyze_weather_impact(stadium, weather, now)
            if signal:
                signals.append(signal)
        
        return signals
    
    async def _get_stadium_weather(self, stadium: Stadium) -> StadiumWeather:
        """Get weather for a stadium (real API or simulated)."""
        
        # Try real OpenWeatherMap API
        real_weather = await self._fetch_openweather(stadium.lat, stadium.lng)
        
        if real_weather:
            return StadiumWeather(
                stadium=stadium.name,
                temperature_f=real_weather.get("temp_f", 60),
                wind_speed_mph=real_weather.get("wind_mph", 5),
                wind_direction=real_weather.get("wind_dir", "N"),
                precipitation_chance=real_weather.get("precip_chance", 0),
                humidity=real_weather.get("humidity", 0.5),
                conditions=real_weather.get("conditions", "Clear"),
            )
        
        # Simulated fallback
        return StadiumWeather(
            stadium=stadium.name,
            temperature_f=random.uniform(20, 95),
            wind_speed_mph=random.uniform(0, 35),
            wind_direction=random.choice(["N", "NE", "E", "SE", "S", "SW", "W", "NW"]),
            precipitation_chance=random.uniform(0, 0.8),
            humidity=random.uniform(0.3, 0.9),
            conditions=random.choice(["Clear", "Cloudy", "Rain", "Snow", "Windy"]),
        )
    
    async def _fetch_openweather(self, lat: float, lng: float) -> Optional[Dict]:
        """Fetch real weather from OpenWeatherMap."""
        if not HAS_HTTPX:
            return None
        
        api_key = os.getenv("OPENWEATHER_API_KEY")
        if not api_key:
            return None
        
        try:
            url = "https://api.openweathermap.org/data/2.5/weather"
            params = {
                "lat": lat,
                "lon": lng,
                "appid": api_key,
                "units": "imperial",
            }
            
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(url, params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "temp_f": data.get("main", {}).get("temp", 60),
                        "wind_mph": data.get("wind", {}).get("speed", 5),
                        "wind_dir": self._degrees_to_direction(data.get("wind", {}).get("deg", 0)),
                        "humidity": data.get("main", {}).get("humidity", 50) / 100,
                        "conditions": data.get("weather", [{}])[0].get("main", "Clear"),
                        "precip_chance": 0.5 if "Rain" in str(data.get("weather", [])) else 0,
                    }
        except Exception as e:
            print(f"⚠️ OpenWeather API error: {e}")
        
        return None
    
    def _degrees_to_direction(self, degrees: float) -> str:
        """Convert wind degrees to cardinal direction."""
        directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
        index = round(degrees / 45) % 8
        return directions[index]
    
    def _analyze_weather_impact(self, stadium: Stadium, weather: StadiumWeather, now: datetime) -> Optional[Signal]:
        """Analyze weather impact on game outcomes."""
        
        impacts = []
        level = 0
        
        # High wind (>15 mph) - significant for NFL/MLB
        if weather.wind_speed_mph > 15 and stadium.sport in ["NFL", "MLB"]:
            if stadium.sport == "NFL":
                impacts.append(f"High winds ({weather.wind_speed_mph:.0f} mph) will affect passing game and field goals")
                level = max(level, 0.7)
            else:
                impacts.append(f"High winds ({weather.wind_speed_mph:.0f} mph) favor pitchers, reduce home runs")
                level = max(level, 0.6)
        
        # Extreme cold (<32°F)
        if weather.temperature_f < 32 and stadium.sport == "NFL":
            impacts.append(f"Freezing temps ({weather.temperature_f:.0f}°F) affect ball handling and player performance")
            level = max(level, 0.65)
        
        # Extreme heat (>90°F)
        if weather.temperature_f > 90:
            impacts.append(f"High heat ({weather.temperature_f:.0f}°F) increases fatigue and injury risk")
            level = max(level, 0.5)
        
        # Rain/Snow
        if weather.precipitation_chance > 0.5:
            precip_type = "Snow" if weather.temperature_f < 35 else "Rain"
            impacts.append(f"{precip_type} likely ({weather.precipitation_chance*100:.0f}% chance) - affects ball handling")
            level = max(level, 0.6)
        
        # Coors Field altitude (always notable for MLB)
        if "Coors" in stadium.name and stadium.sport == "MLB":
            impacts.append("High altitude at Coors Field - expect more offense, ball carries further")
            level = max(level, 0.5)
        
        # Only return signal if there's notable impact
        if not impacts or level < 0.5:
            return None
        
        return Signal(
            id=self._generate_signal_id("weather", stadium.name.replace(" ", "_")),
            source=SignalSource.SATELLITE_PROXY,  # Weather data often from satellite
            region=RegionOfInterest.WASHINGTON_DC,  # Sports are US-centric
            level=level,
            confidence=0.8,
            description=f"🌤️ {stadium.name} ({stadium.team}): {'. '.join(impacts)}",
            raw_data={
                "stadium": stadium.name,
                "team": stadium.team,
                "sport": stadium.sport,
                "temperature_f": weather.temperature_f,
                "wind_speed_mph": weather.wind_speed_mph,
                "wind_direction": weather.wind_direction,
                "precipitation_chance": weather.precipitation_chance,
                "conditions": weather.conditions,
                "impacts": impacts,
                "source": "weather_api",
            },
            timestamp=now,
            expires_at=now + timedelta(hours=6),
        )

# =============================================================================
# PLAYER SOCIAL SENTIMENT - "Is he injured?"
# =============================================================================

@dataclass
class PlayerSentiment:
    """Sentiment analysis for a player."""
    player_name: str
    team: str
    sport: str
    sentiment_score: float  # -1 to 1
    volume_spike: float     # Multiplier vs baseline
    key_topics: List[str]

class PlayerSentimentSource(BaseSignalSource):
    """
    Player Social Media Sentiment Analysis
    
    Monitors:
    - Injury keywords before official announcements
    - Locker room drama signals
    - Personal issues affecting performance
    - Trade/transfer rumors
    
    Real API: Twitter/X API, Reddit API
    """
    
    # High-profile players to track
    TRACKED_PLAYERS = [
        {"name": "Patrick Mahomes", "team": "Kansas City Chiefs", "sport": "NFL"},
        {"name": "Josh Allen", "team": "Buffalo Bills", "sport": "NFL"},
        {"name": "Travis Kelce", "team": "Kansas City Chiefs", "sport": "NFL"},
        {"name": "LeBron James", "team": "LA Lakers", "sport": "NBA"},
        {"name": "Stephen Curry", "team": "Golden State Warriors", "sport": "NBA"},
        {"name": "Shohei Ohtani", "team": "LA Dodgers", "sport": "MLB"},
        {"name": "Aaron Judge", "team": "NY Yankees", "sport": "MLB"},
        {"name": "Erling Haaland", "team": "Manchester City", "sport": "Soccer"},
        {"name": "Kylian Mbappé", "team": "Real Madrid", "sport": "Soccer"},
        {"name": "Mohamed Salah", "team": "Liverpool", "sport": "Soccer"},
    ]
    
    # Concerning keywords
    INJURY_KEYWORDS = ["injury", "hurt", "questionable", "doubtful", "out", "DNP", "limited", "pain", "surgery"]
    DRAMA_KEYWORDS = ["unhappy", "trade", "conflict", "benched", "argument", "suspension", "investigation"]
    
    async def scan(self, region: RegionOfInterest) -> List[Signal]:
        signals = []
        now = datetime.now(timezone.utc)
        
        # Check random selection of players
        check_players = random.sample(self.TRACKED_PLAYERS, min(5, len(self.TRACKED_PLAYERS)))
        
        for player_data in check_players:
            sentiment = await self._analyze_player_sentiment(player_data)
            
            # Only signal on notable findings
            if sentiment and (sentiment.sentiment_score < -0.3 or sentiment.volume_spike > 2.0):
                signal = self._create_sentiment_signal(sentiment, now)
                if signal:
                    signals.append(signal)
        
        return signals
    
    async def _analyze_player_sentiment(self, player_data: Dict) -> Optional[PlayerSentiment]:
        """Analyze social sentiment for a player."""
        
        # Simulated sentiment analysis
        # Real implementation would use Twitter API + NLP
        
        # 15% chance of notable sentiment
        if random.random() > 0.15:
            return None
        
        scenario = random.choice(["injury_rumor", "drama", "positive_hype", "trade_talk"])
        
        if scenario == "injury_rumor":
            return PlayerSentiment(
                player_name=player_data["name"],
                team=player_data["team"],
                sport=player_data["sport"],
                sentiment_score=random.uniform(-0.8, -0.4),
                volume_spike=random.uniform(3.0, 8.0),
                key_topics=random.sample(self.INJURY_KEYWORDS, 3),
            )
        elif scenario == "drama":
            return PlayerSentiment(
                player_name=player_data["name"],
                team=player_data["team"],
                sport=player_data["sport"],
                sentiment_score=random.uniform(-0.6, -0.2),
                volume_spike=random.uniform(2.5, 6.0),
                key_topics=random.sample(self.DRAMA_KEYWORDS, 2),
            )
        elif scenario == "positive_hype":
            return PlayerSentiment(
                player_name=player_data["name"],
                team=player_data["team"],
                sport=player_data["sport"],
                sentiment_score=random.uniform(0.4, 0.8),
                volume_spike=random.uniform(2.0, 4.0),
                key_topics=["MVP", "beast mode", "unstoppable"],
            )
        else:  # trade_talk
            return PlayerSentiment(
                player_name=player_data["name"],
                team=player_data["team"],
                sport=player_data["sport"],
                sentiment_score=random.uniform(-0.3, 0.1),
                volume_spike=random.uniform(4.0, 10.0),
                key_topics=["trade", "rumors", "moving"],
            )
    
    def _create_sentiment_signal(self, sentiment: PlayerSentiment, now: datetime) -> Optional[Signal]:
        """Create signal from sentiment analysis."""
        
        # Determine signal type
        if any(kw in self.INJURY_KEYWORDS for kw in sentiment.key_topics):
            signal_type = "injury"
            desc = f"🚨 Injury buzz around {sentiment.player_name} ({sentiment.team})"
            implication = "Possible undisclosed injury - check lineup closer to game"
            level = 0.85
        elif any(kw in self.DRAMA_KEYWORDS for kw in sentiment.key_topics):
            signal_type = "drama"
            desc = f"⚠️ Negative chatter about {sentiment.player_name} ({sentiment.team})"
            implication = "Team chemistry or personal issues may affect performance"
            level = 0.65
        elif sentiment.sentiment_score > 0.3:
            signal_type = "hype"
            desc = f"📈 Positive momentum for {sentiment.player_name} ({sentiment.team})"
            implication = "Player confidence high - could exceed expectations"
            level = 0.5
        else:
            signal_type = "trade"
            desc = f"📢 Trade rumors swirling around {sentiment.player_name} ({sentiment.team})"
            implication = "Player distraction possible - monitor closely"
            level = 0.55
        
        return Signal(
            id=self._generate_signal_id("sentiment", sentiment.player_name.replace(" ", "_")),
            source=SignalSource.SOCIAL_CHATTER,
            region=RegionOfInterest.WASHINGTON_DC,
            level=level,
            confidence=0.6,
            description=f"{desc}. Keywords: {', '.join(sentiment.key_topics)}. {implication}",
            raw_data={
                "player": sentiment.player_name,
                "team": sentiment.team,
                "sport": sentiment.sport,
                "sentiment_score": round(sentiment.sentiment_score, 2),
                "volume_spike": round(sentiment.volume_spike, 1),
                "key_topics": sentiment.key_topics,
                "signal_type": signal_type,
                "source": "simulated_social",
            },
            timestamp=now,
            expires_at=now + timedelta(hours=24),
        )

# =============================================================================
# TEAM TRAVEL & FATIGUE - "Back-to-back on the road"
# =============================================================================

class TeamTravelSource(BaseSignalSource):
    """
    Team Travel & Fatigue Analysis
    
    Monitors:
    - Back-to-back games (NBA especially)
    - West-to-East travel (circadian disadvantage)
    - Extended road trips
    - Altitude changes
    
    Real API: Team schedules + flight tracking
    """
    
    # Teams with notable travel disadvantages
    WEST_COAST_TEAMS = ["LA Lakers", "Golden State Warriors", "Portland Trail Blazers", 
                        "LA Clippers", "Sacramento Kings", "Seattle Seahawks", 
                        "San Francisco 49ers", "LA Dodgers", "LA Angels"]
    
    MOUNTAIN_TEAMS = ["Denver Nuggets", "Utah Jazz", "Denver Broncos", "Colorado Rockies"]
    
    async def scan(self, region: RegionOfInterest) -> List[Signal]:
        signals = []
        now = datetime.now(timezone.utc)
        
        # 10% chance of notable travel signal
        if random.random() < 0.10:
            signals.extend(await self._analyze_travel_fatigue(now))
        
        return signals
    
    async def _analyze_travel_fatigue(self, now: datetime) -> List[Signal]:
        """Analyze team travel and fatigue factors."""
        signals = []
        
        scenarios = [
            {
                "team": random.choice(self.WEST_COAST_TEAMS),
                "situation": "playing early East Coast game",
                "disadvantage": "Body clock 3 hours behind, expect slow start",
                "impact": "fatigue",
                "level": 0.65,
            },
            {
                "team": "Denver Nuggets",
                "situation": "hosting sea-level team",
                "disadvantage": "Altitude advantage for Denver - visitors tire in 4th quarter",
                "impact": "altitude_advantage",
                "level": 0.6,
            },
            {
                "team": random.choice(["Chicago Bulls", "Boston Celtics", "NY Knicks"]),
                "situation": "4th game in 5 nights",
                "disadvantage": "Severe fatigue expected - watch for load management",
                "impact": "schedule_loss",
                "level": 0.75,
            },
            {
                "team": random.choice(["Golden State Warriors", "LA Lakers"]),
                "situation": "back-to-back after cross-country flight",
                "disadvantage": "Travel fatigue + B2B = significant handicap",
                "impact": "b2b_road",
                "level": 0.7,
            },
        ]
        
        scenario = random.choice(scenarios)
        
        signals.append(Signal(
            id=self._generate_signal_id("travel", scenario["team"].replace(" ", "_")),
            source=SignalSource.FLIGHT_RADAR,  # Using flight radar as proxy
            region=RegionOfInterest.WASHINGTON_DC,
            level=scenario["level"],
            confidence=0.75,
            description=f"✈️ {scenario['team']} {scenario['situation']}. {scenario['disadvantage']}",
            raw_data={
                "team": scenario["team"],
                "situation": scenario["situation"],
                "impact_type": scenario["impact"],
                "disadvantage": scenario["disadvantage"],
                "source": "schedule_analysis",
            },
            timestamp=now,
            expires_at=now + timedelta(hours=12),
        ))
        
        return signals

# =============================================================================
# LINEUP INTELLIGENCE - "Who's actually playing?"
# =============================================================================

class LineupIntelSource(BaseSignalSource):
    """
    Pre-Game Lineup Intelligence
    
    Monitors:
    - Late scratches (injury or rest)
    - Lineup changes from training
    - Rotation adjustments
    - Weather-related changes
    
    Real API: Team beat reporters on Twitter, official injury reports
    """
    
    async def scan(self, region: RegionOfInterest) -> List[Signal]:
        signals = []
        now = datetime.now(timezone.utc)
        
        # 8% chance of lineup intel
        if random.random() < 0.08:
            signals.extend(await self._check_lineup_changes(now))
        
        return signals
    
    async def _check_lineup_changes(self, now: datetime) -> List[Signal]:
        """Check for late lineup changes."""
        signals = []
        
        scenarios = [
            {
                "player": "Star QB",
                "team": "Kansas City Chiefs",
                "sport": "NFL",
                "change": "Listed as questionable, seen limping at practice",
                "impact": "If out, backup QB significantly worse - line should move",
                "level": 0.9,
            },
            {
                "player": "Starting PG",
                "team": "LA Lakers",
                "sport": "NBA",
                "change": "DNP-Rest listed for tonight's game",
                "impact": "Load management - second unit will see more minutes",
                "level": 0.7,
            },
            {
                "player": "Ace pitcher",
                "team": "NY Yankees",
                "sport": "MLB",
                "change": "Scratched from start, bullpen game instead",
                "impact": "Major edge loss - total should drop significantly",
                "level": 0.85,
            },
            {
                "player": "Key midfielder",
                "team": "Manchester City",
                "sport": "Soccer",
                "change": "Not in traveling squad for Champions League",
                "impact": "Injury or rotation - affects team's pressing ability",
                "level": 0.65,
            },
        ]
        
        scenario = random.choice(scenarios)
        
        signals.append(Signal(
            id=self._generate_signal_id("lineup", scenario["team"].replace(" ", "_")),
            source=SignalSource.SOCIAL_CHATTER,  # Beat reporters are key source
            region=RegionOfInterest.WASHINGTON_DC,
            level=scenario["level"],
            confidence=0.7,
            description=f"📋 LINEUP INTEL: {scenario['team']} - {scenario['change']}. {scenario['impact']}",
            raw_data={
                "player_role": scenario["player"],
                "team": scenario["team"],
                "sport": scenario["sport"],
                "change": scenario["change"],
                "betting_impact": scenario["impact"],
                "source": "simulated_beat_reporter",
            },
            timestamp=now,
            expires_at=now + timedelta(hours=6),
        ))
        
        return signals

# =============================================================================
# EXPORT ALL SPORTS SOURCES
# =============================================================================

SPORTS_SOURCES = [
    StadiumWeatherSource,
    PlayerSentimentSource,
    TeamTravelSource,
    LineupIntelSource,
]

def get_sports_sources() -> List[BaseSignalSource]:
    """Get instances of all Sports (Edge) signal sources."""
    return [source() for source in SPORTS_SOURCES]

# =============================================================================
# TESTING
# =============================================================================

if __name__ == "__main__":
    async def test():
        print("=" * 60)
        print("🏈 SPORTS EDGE SIGNAL SOURCES - Test")
        print("=" * 60)
        
        sources = get_sports_sources()
        
        for source in sources:
            print(f"\n📡 Testing {source.__class__.__name__}...")
            
            signals = await source.scan(RegionOfInterest.WASHINGTON_DC)
            
            if signals:
                for sig in signals:
                    print(f"  [{sig.severity}] {sig.description[:70]}...")
            else:
                print("  No signals detected this scan")
        
        print("\n" + "=" * 60)
    
    asyncio.run(test())
