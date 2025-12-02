"""
Football Data API Client for Project Seed
==========================================
Wrapper for football-data.org API to fetch real-world snapshots.

Usage:
    from core.football_data_client import FootballDataClient

    client = FootballDataClient()

    # Get Premier League standings
    standings = await client.get_standings("PL")

    # Get squad for a team
    squad = await client.get_team_squad(team_id=65)  # Manchester City

    # Take a full snapshot for a competition
    snapshot = await client.take_snapshot("PL")

Environment:
    FOOTBALL_DATA_API_KEY - Your API key from football-data.org

Rate Limits (Free Tier):
    - 10 requests per minute
    - We implement automatic rate limiting
"""

import os
import asyncio
import aiohttp
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from enum import Enum
import time

from dotenv import load_dotenv

load_dotenv()


# =============================================================================
# CONFIGURATION
# =============================================================================

class Competition(str, Enum):
    """Top 5 European leagues + extras available in free tier."""
    PREMIER_LEAGUE = "PL"
    LA_LIGA = "PD"  # Primera Division
    BUNDESLIGA = "BL1"
    SERIE_A = "SA"
    LIGUE_1 = "FL1"
    # Also available in free tier:
    CHAMPIONSHIP = "ELC"
    EREDIVISIE = "DED"
    PRIMEIRA_LIGA = "PPL"
    CHAMPIONS_LEAGUE = "CL"
    EURO = "EC"
    WORLD_CUP = "WC"
    COPA_LIBERTADORES = "CLI"


# Competition metadata
COMPETITION_INFO = {
    Competition.PREMIER_LEAGUE: {"name": "Premier League", "country": "England", "teams": 20},
    Competition.LA_LIGA: {"name": "La Liga", "country": "Spain", "teams": 20},
    Competition.BUNDESLIGA: {"name": "Bundesliga", "country": "Germany", "teams": 18},
    Competition.SERIE_A: {"name": "Serie A", "country": "Italy", "teams": 20},
    Competition.LIGUE_1: {"name": "Ligue 1", "country": "France", "teams": 18},
}


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class Player:
    """Player data from API."""
    id: int
    name: str
    position: Optional[str] = None
    date_of_birth: Optional[str] = None
    nationality: Optional[str] = None
    shirt_number: Optional[int] = None

    # Derived/estimated stats (API doesn't provide detailed stats in free tier)
    # We'll estimate these based on position and team strength
    estimated_skill: int = 70
    estimated_pace: int = 70

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class Team:
    """Team data from API."""
    id: int
    name: str
    short_name: Optional[str] = None
    tla: Optional[str] = None  # Three-letter acronym
    crest: Optional[str] = None  # Logo URL
    venue: Optional[str] = None
    founded: Optional[int] = None
    club_colors: Optional[str] = None

    # Squad
    squad: List[Player] = field(default_factory=list)

    # Current season stats (from standings)
    position: int = 0
    played: int = 0
    won: int = 0
    draw: int = 0
    lost: int = 0
    goals_for: int = 0
    goals_against: int = 0
    goal_difference: int = 0
    points: int = 0

    # Derived strength rating (0-100)
    @property
    def strength_rating(self) -> int:
        """Estimate team strength from league position and goal difference."""
        if self.position == 0:
            return 70  # Unknown

        # Top teams get higher ratings
        position_score = max(0, 100 - (self.position * 4))

        # Goal difference bonus
        gd_bonus = min(20, max(-20, self.goal_difference // 2))

        return min(99, max(50, position_score + gd_bonus))

    def to_dict(self) -> Dict:
        data = asdict(self)
        data['strength_rating'] = self.strength_rating
        return data


@dataclass
class Match:
    """Match fixture/result from API."""
    id: int
    home_team_id: int
    away_team_id: int
    home_team_name: str
    away_team_name: str
    matchday: int
    status: str  # SCHEDULED, LIVE, IN_PLAY, PAUSED, FINISHED, POSTPONED, CANCELLED
    utc_date: str

    # Score (None if not played)
    home_score: Optional[int] = None
    away_score: Optional[int] = None

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class Snapshot:
    """A complete snapshot of a competition at a point in time."""
    competition_code: str
    competition_name: str
    season: str
    snapshot_date: str
    matchday: int

    teams: List[Team] = field(default_factory=list)
    recent_matches: List[Match] = field(default_factory=list)
    upcoming_matches: List[Match] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "competition_code": self.competition_code,
            "competition_name": self.competition_name,
            "season": self.season,
            "snapshot_date": self.snapshot_date,
            "matchday": self.matchday,
            "teams": [t.to_dict() for t in self.teams],
            "recent_matches": [m.to_dict() for m in self.recent_matches],
            "upcoming_matches": [m.to_dict() for m in self.upcoming_matches],
        }

    def save(self, filepath: str) -> None:
        """Save snapshot to JSON file."""
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, filepath: str) -> 'Snapshot':
        """Load snapshot from JSON file."""
        with open(filepath, 'r') as f:
            data = json.load(f)

        teams = [Team(**{k: v for k, v in t.items() if k != 'strength_rating'})
                 for t in data.get('teams', [])]

        # Reconstruct squad for each team
        for i, team_data in enumerate(data.get('teams', [])):
            if 'squad' in team_data:
                teams[i].squad = [Player(**p) for p in team_data['squad']]

        return cls(
            competition_code=data['competition_code'],
            competition_name=data['competition_name'],
            season=data['season'],
            snapshot_date=data['snapshot_date'],
            matchday=data['matchday'],
            teams=teams,
            recent_matches=[Match(**m) for m in data.get('recent_matches', [])],
            upcoming_matches=[Match(**m) for m in data.get('upcoming_matches', [])],
        )


# =============================================================================
# API CLIENT
# =============================================================================

class FootballDataClient:
    """
    Async client for football-data.org API.

    Implements automatic rate limiting for free tier (10 req/min).
    """

    BASE_URL = "https://api.football-data.org/v4"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("FOOTBALL_DATA_API_KEY")
        if not self.api_key:
            raise ValueError(
                "FOOTBALL_DATA_API_KEY not found. "
                "Set it in your .env file or pass it to the constructor."
            )

        # Rate limiting (10 requests per minute for free tier)
        self.requests_per_minute = 10
        self.request_timestamps: List[float] = []

        # Cache to reduce API calls
        self._cache: Dict[str, Any] = {}
        self._cache_ttl = 300  # 5 minutes

    async def _rate_limit(self) -> None:
        """Enforce rate limiting."""
        now = time.time()

        # Remove timestamps older than 1 minute
        self.request_timestamps = [
            ts for ts in self.request_timestamps
            if now - ts < 60
        ]

        # If at limit, wait
        if len(self.request_timestamps) >= self.requests_per_minute:
            oldest = self.request_timestamps[0]
            wait_time = 60 - (now - oldest) + 0.5  # Add buffer
            if wait_time > 0:
                print(f"⏳ Rate limit reached. Waiting {wait_time:.1f}s...")
                await asyncio.sleep(wait_time)

        self.request_timestamps.append(time.time())

    async def _request(self, endpoint: str, params: Dict = None) -> Dict:
        """Make an authenticated request to the API."""
        await self._rate_limit()

        url = f"{self.BASE_URL}/{endpoint}"
        headers = {
            "X-Auth-Token": self.api_key,
            "Content-Type": "application/json"
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 429:
                    # Rate limited - wait and retry
                    retry_after = int(response.headers.get('Retry-After', 60))
                    print(f"⚠️ Rate limited. Retrying in {retry_after}s...")
                    await asyncio.sleep(retry_after)
                    return await self._request(endpoint, params)
                else:
                    error_text = await response.text()
                    raise Exception(f"API Error {response.status}: {error_text}")

    # -------------------------------------------------------------------------
    # Competition Endpoints
    # -------------------------------------------------------------------------

    async def get_competitions(self) -> List[Dict]:
        """Get all available competitions."""
        data = await self._request("competitions")
        return data.get("competitions", [])

    async def get_competition(self, code: str) -> Dict:
        """Get details for a specific competition."""
        return await self._request(f"competitions/{code}")

    # -------------------------------------------------------------------------
    # Standings
    # -------------------------------------------------------------------------

    async def get_standings(self, competition_code: str) -> List[Dict]:
        """
        Get current standings for a competition.

        Returns list of team standings with position, points, goals, etc.
        """
        data = await self._request(f"competitions/{competition_code}/standings")

        standings = []
        for standing_type in data.get("standings", []):
            if standing_type.get("type") == "TOTAL":
                standings = standing_type.get("table", [])
                break

        return standings

    # -------------------------------------------------------------------------
    # Teams & Squads
    # -------------------------------------------------------------------------

    async def get_teams(self, competition_code: str) -> List[Dict]:
        """Get all teams in a competition."""
        data = await self._request(f"competitions/{competition_code}/teams")
        return data.get("teams", [])

    async def get_team(self, team_id: int) -> Dict:
        """Get details for a specific team including squad."""
        return await self._request(f"teams/{team_id}")

    async def get_team_squad(self, team_id: int) -> List[Player]:
        """Get squad for a team."""
        data = await self.get_team(team_id)

        players = []
        for p in data.get("squad", []):
            players.append(Player(
                id=p.get("id"),
                name=p.get("name"),
                position=p.get("position"),
                date_of_birth=p.get("dateOfBirth"),
                nationality=p.get("nationality"),
                shirt_number=p.get("shirtNumber"),
            ))

        return players

    # -------------------------------------------------------------------------
    # Matches
    # -------------------------------------------------------------------------

    async def get_matches(self, competition_code: str,
                          matchday: Optional[int] = None,
                          status: Optional[str] = None,
                          date_from: Optional[str] = None,
                          date_to: Optional[str] = None) -> List[Match]:
        """
        Get matches for a competition.

        Args:
            competition_code: Competition code (e.g., "PL")
            matchday: Specific matchday number
            status: Filter by status (SCHEDULED, LIVE, FINISHED, etc.)
            date_from: Start date (YYYY-MM-DD)
            date_to: End date (YYYY-MM-DD)
        """
        params = {}
        if matchday:
            params["matchday"] = matchday
        if status:
            params["status"] = status
        if date_from:
            params["dateFrom"] = date_from
        if date_to:
            params["dateTo"] = date_to

        data = await self._request(f"competitions/{competition_code}/matches", params)

        matches = []
        for m in data.get("matches", []):
            home = m.get("homeTeam", {})
            away = m.get("awayTeam", {})
            score = m.get("score", {}).get("fullTime", {})

            matches.append(Match(
                id=m.get("id"),
                home_team_id=home.get("id"),
                away_team_id=away.get("id"),
                home_team_name=home.get("name", "Unknown"),
                away_team_name=away.get("name", "Unknown"),
                matchday=m.get("matchday", 0),
                status=m.get("status", "UNKNOWN"),
                utc_date=m.get("utcDate", ""),
                home_score=score.get("home"),
                away_score=score.get("away"),
            ))

        return matches

    async def get_recent_matches(self, competition_code: str,
                                  days: int = 14) -> List[Match]:
        """Get matches from the last N days."""
        date_from = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        date_to = datetime.now().strftime("%Y-%m-%d")

        return await self.get_matches(
            competition_code,
            date_from=date_from,
            date_to=date_to,
            status="FINISHED"
        )

    async def get_upcoming_matches(self, competition_code: str,
                                    days: int = 14) -> List[Match]:
        """Get matches in the next N days."""
        date_from = datetime.now().strftime("%Y-%m-%d")
        date_to = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")

        return await self.get_matches(
            competition_code,
            date_from=date_from,
            date_to=date_to,
            status="SCHEDULED"
        )

    # -------------------------------------------------------------------------
    # Scorers
    # -------------------------------------------------------------------------

    async def get_scorers(self, competition_code: str, limit: int = 10) -> List[Dict]:
        """Get top scorers for a competition."""
        params = {"limit": limit}
        data = await self._request(f"competitions/{competition_code}/scorers", params)
        return data.get("scorers", [])

    # -------------------------------------------------------------------------
    # Snapshot
    # -------------------------------------------------------------------------

    async def take_snapshot(self, competition_code: str,
                            include_squads: bool = True) -> Snapshot:
        """
        Take a complete snapshot of a competition's current state.

        This is the main method for creating a "fork point" for simulation.

        Args:
            competition_code: Competition code (e.g., "PL", "PD", "BL1")
            include_squads: Whether to fetch full squad data (more API calls)

        Returns:
            Snapshot object with teams, standings, and recent matches
        """
        print(f"📸 Taking snapshot of {competition_code}...")

        # Get competition info
        comp_data = await self.get_competition(competition_code)
        season = comp_data.get("currentSeason", {})
        current_matchday = season.get("currentMatchday", 1)
        season_id = f"{season.get('startDate', '')[:4]}/{season.get('endDate', '')[:4]}"

        # Get standings
        print(f"   📊 Fetching standings...")
        standings = await self.get_standings(competition_code)

        # Get teams with optional squad data
        print(f"   👥 Fetching teams...")
        teams_data = await self.get_teams(competition_code)

        teams = []
        for i, standing in enumerate(standings):
            team_info = standing.get("team", {})
            team_id = team_info.get("id")

            # Find full team data
            full_team = next(
                (t for t in teams_data if t.get("id") == team_id),
                {}
            )

            team = Team(
                id=team_id,
                name=team_info.get("name", "Unknown"),
                short_name=team_info.get("shortName"),
                tla=team_info.get("tla"),
                crest=team_info.get("crest"),
                venue=full_team.get("venue"),
                founded=full_team.get("founded"),
                club_colors=full_team.get("clubColors"),
                position=standing.get("position", i + 1),
                played=standing.get("playedGames", 0),
                won=standing.get("won", 0),
                draw=standing.get("draw", 0),
                lost=standing.get("lost", 0),
                goals_for=standing.get("goalsFor", 0),
                goals_against=standing.get("goalsAgainst", 0),
                goal_difference=standing.get("goalDifference", 0),
                points=standing.get("points", 0),
            )

            # Fetch squad if requested
            if include_squads and team_id:
                print(f"   🎽 Fetching squad for {team.name}...")
                try:
                    team.squad = await self.get_team_squad(team_id)
                except Exception as e:
                    print(f"      ⚠️ Could not fetch squad: {e}")

            teams.append(team)

        # Get recent and upcoming matches
        print(f"   📅 Fetching matches...")
        recent = await self.get_recent_matches(competition_code, days=14)
        upcoming = await self.get_upcoming_matches(competition_code, days=14)

        snapshot = Snapshot(
            competition_code=competition_code,
            competition_name=comp_data.get("name", "Unknown"),
            season=season_id,
            snapshot_date=datetime.now().isoformat(),
            matchday=current_matchday,
            teams=teams,
            recent_matches=recent,
            upcoming_matches=upcoming,
        )

        print(f"✅ Snapshot complete: {len(teams)} teams, {len(recent)} recent matches")

        return snapshot

    async def take_all_snapshots(self, output_dir: str = "snapshots") -> Dict[str, Snapshot]:
        """
        Take snapshots of all top 5 leagues.

        Warning: This makes many API calls. With free tier, it may take
        several minutes due to rate limiting.
        """
        os.makedirs(output_dir, exist_ok=True)

        snapshots = {}

        for comp in [Competition.PREMIER_LEAGUE, Competition.LA_LIGA,
                     Competition.BUNDESLIGA, Competition.SERIE_A, Competition.LIGUE_1]:
            try:
                print(f"\n{'='*50}")
                print(f"📸 {COMPETITION_INFO[comp]['name']}")
                print(f"{'='*50}")

                snapshot = await self.take_snapshot(comp.value, include_squads=True)
                snapshots[comp.value] = snapshot

                # Save to file
                filepath = os.path.join(output_dir, f"{comp.value}_snapshot.json")
                snapshot.save(filepath)
                print(f"💾 Saved to {filepath}")

            except Exception as e:
                print(f"❌ Error taking snapshot of {comp.value}: {e}")

        return snapshots


# =============================================================================
# CLI
# =============================================================================

async def main():
    """CLI for testing the client."""
    import argparse

    parser = argparse.ArgumentParser(description="Football Data API Client")
    parser.add_argument("action", choices=["snapshot", "standings", "matches", "test"],
                        help="Action to perform")
    parser.add_argument("--competition", "-c", default="PL",
                        help="Competition code (default: PL)")
    parser.add_argument("--output", "-o", default="snapshots",
                        help="Output directory for snapshots")
    parser.add_argument("--all", action="store_true",
                        help="Snapshot all top 5 leagues")

    args = parser.parse_args()

    try:
        client = FootballDataClient()
    except ValueError as e:
        print(f"❌ {e}")
        return

    if args.action == "test":
        print("🧪 Testing API connection...")
        comps = await client.get_competitions()
        print(f"✅ Connected! Found {len(comps)} competitions.")

    elif args.action == "standings":
        standings = await client.get_standings(args.competition)
        print(f"\n📊 {args.competition} Standings:")
        for s in standings[:10]:
            team = s.get("team", {}).get("name", "Unknown")
            print(f"   {s.get('position'):2}. {team:25} - {s.get('points')} pts")

    elif args.action == "matches":
        matches = await client.get_recent_matches(args.competition)
        print(f"\n📅 Recent {args.competition} Matches:")
        for m in matches[:10]:
            score = f"{m.home_score}-{m.away_score}" if m.home_score is not None else "vs"
            print(f"   {m.home_team_name} {score} {m.away_team_name}")

    elif args.action == "snapshot":
        if args.all:
            await client.take_all_snapshots(args.output)
        else:
            snapshot = await client.take_snapshot(args.competition)
            os.makedirs(args.output, exist_ok=True)
            filepath = os.path.join(args.output, f"{args.competition}_snapshot.json")
            snapshot.save(filepath)
            print(f"💾 Saved to {filepath}")


if __name__ == "__main__":
    asyncio.run(main())
