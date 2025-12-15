"""
Football League Simulation Engine for Project Seed
===================================================
Simulates football matches and seasons using AthleticAgent schema.

Features:
- Full match simulation with goals, assists, cards, injuries
- League table management
- Team chemistry and morale effects
- Provably fair via seed-based determinism
- Snapshot fork capability for "what if" scenarios
- Rich event generation for betting markets

Usage:
    # As module
    from backend.simulation.sim_football_engine import FootballSimulation
    
    sim = FootballSimulation(game_hash)
    sim.initialize_from_snapshot("snapshots/PL_snapshot.json")
    result = sim.simulate_match(team_a_id, team_b_id)
    
    # CLI
    python sim_football_engine.py <server_seed> <client_seed> <nonce> --match HOME_ID AWAY_ID
    python sim_football_engine.py <server_seed> <client_seed> <nonce> --matchday 15
"""

import sys
import os
import hashlib
import random
import json
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
import uuid

# Add parent directory for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.agents.schemas import (
    AthleticAgent,
    AthleticArchetype,
    create_random_athletic_agent,
    AgentStatus,
)


# =============================================================================
# CONFIGURATION
# =============================================================================

class MatchConfig:
    """Match simulation parameters."""
    
    # Match structure
    MINUTES = 90
    TICKS_PER_MATCH = 90  # 1 tick = 1 minute
    
    # Base probabilities (per tick)
    BASE_GOAL_CHANCE = 0.015  # ~1.35 goals per team per match
    BASE_ASSIST_CHANCE = 0.7  # 70% of goals have assists
    BASE_CARD_CHANCE = 0.002
    BASE_INJURY_CHANCE = 0.001
    
    # Home advantage
    HOME_ADVANTAGE = 1.15  # 15% boost
    
    # Form impact
    FORM_IMPACT = 0.3  # How much form affects performance
    
    # Fatigue
    FATIGUE_PER_MATCH = 8  # Match fitness reduction


# =============================================================================
# DATA STRUCTURES
# =============================================================================

class MatchEventType(str, Enum):
    GOAL = "GOAL"
    ASSIST = "ASSIST"
    OWN_GOAL = "OWN_GOAL"
    YELLOW_CARD = "YELLOW_CARD"
    RED_CARD = "RED_CARD"
    INJURY = "INJURY"
    SUBSTITUTION = "SUB"
    PENALTY = "PENALTY"
    PENALTY_MISS = "PENALTY_MISS"
    VAR_REVIEW = "VAR"


@dataclass
class MatchEvent:
    """An event that occurred during a match."""
    minute: int
    event_type: MatchEventType
    team_id: str
    player_id: Optional[str] = None
    player_name: Optional[str] = None
    assist_player_id: Optional[str] = None
    assist_player_name: Optional[str] = None
    description: str = ""
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class MatchResult:
    """Complete result of a simulated match."""
    match_id: str
    home_team_id: str
    away_team_id: str
    home_team_name: str
    away_team_name: str
    
    home_score: int = 0
    away_score: int = 0
    
    # Detailed stats
    home_shots: int = 0
    away_shots: int = 0
    home_possession: float = 50.0
    away_possession: float = 50.0
    home_corners: int = 0
    away_corners: int = 0
    home_fouls: int = 0
    away_fouls: int = 0
    
    # Events timeline
    events: List[MatchEvent] = field(default_factory=list)
    
    # Player ratings (player_id -> rating)
    player_ratings: Dict[str, float] = field(default_factory=dict)
    
    # Man of the match
    motm_id: Optional[str] = None
    motm_name: Optional[str] = None
    
    @property
    def result_string(self) -> str:
        """Simple result string for betting."""
        if self.home_score > self.away_score:
            return "HOME_WIN"
        elif self.away_score > self.home_score:
            return "AWAY_WIN"
        return "DRAW"
    
    @property
    def total_goals(self) -> int:
        return self.home_score + self.away_score
    
    @property
    def both_teams_scored(self) -> bool:
        return self.home_score > 0 and self.away_score > 0
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        data['result_string'] = self.result_string
        data['total_goals'] = self.total_goals
        data['both_teams_scored'] = self.both_teams_scored
        return data


@dataclass
class SimulatedTeam:
    """A team in the simulation with its squad of AthleticAgents."""
    id: str
    name: str
    short_name: str = ""
    
    # Squad
    players: List[AthleticAgent] = field(default_factory=list)
    
    # Team stats
    strength_rating: int = 70
    home_strength: int = 75
    away_strength: int = 65
    
    # League position
    position: int = 0
    played: int = 0
    won: int = 0
    drawn: int = 0
    lost: int = 0
    goals_for: int = 0
    goals_against: int = 0
    points: int = 0
    
    # Morale/chemistry (0-100)
    morale: int = 70
    chemistry: int = 70
    
    @property
    def goal_difference(self) -> int:
        return self.goals_for - self.goals_against
    
    @property
    def effective_strength(self) -> float:
        """Current strength accounting for morale and chemistry."""
        base = self.strength_rating
        morale_mod = (self.morale - 50) / 100  # -0.5 to +0.5
        chemistry_mod = (self.chemistry - 50) / 200  # -0.25 to +0.25
        return base * (1 + morale_mod + chemistry_mod)
    
    def get_starting_xi(self) -> List[AthleticAgent]:
        """Select best available 11 players."""
        available = [p for p in self.players if p.status == AgentStatus.ACTIVE]
        
        # Sort by effective rating
        available.sort(key=lambda p: p.effective_rating, reverse=True)
        
        # Try to get balanced formation (1 GK, 4 DEF, 4 MID, 2 FWD)
        starting = []
        positions_needed = {"GK": 1, "DEF": 4, "MID": 4, "FWD": 2}
        
        for pos, count in positions_needed.items():
            pos_players = [p for p in available if p.position == pos and p not in starting]
            starting.extend(pos_players[:count])
        
        # Fill remaining spots with best available
        remaining = [p for p in available if p not in starting]
        while len(starting) < 11 and remaining:
            starting.append(remaining.pop(0))
        
        return starting[:11]
    
    def update_league_position(self, result: str, goals_for: int, goals_against: int):
        """Update team's league stats after a match."""
        self.played += 1
        self.goals_for += goals_for
        self.goals_against += goals_against
        
        if result == "WIN":
            self.won += 1
            self.points += 3
            self.morale = min(100, self.morale + 5)
        elif result == "DRAW":
            self.drawn += 1
            self.points += 1
        else:  # LOSS
            self.lost += 1
            self.morale = max(30, self.morale - 5)
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "short_name": self.short_name,
            "strength_rating": self.strength_rating,
            "position": self.position,
            "played": self.played,
            "won": self.won,
            "drawn": self.drawn,
            "lost": self.lost,
            "goals_for": self.goals_for,
            "goals_against": self.goals_against,
            "goal_difference": self.goal_difference,
            "points": self.points,
            "morale": self.morale,
            "squad_size": len(self.players),
        }


# =============================================================================
# MATCH SIMULATION ENGINE
# =============================================================================

class MatchSimulator:
    """
    Simulates a single football match.
    
    All randomness is seeded for provable fairness.
    """
    
    def __init__(self, match_seed: str, config: MatchConfig = MatchConfig()):
        self.seed = match_seed
        self.config = config
        random.seed(match_seed)
        
        # Derived randomness
        seed_int = int(hashlib.sha256(match_seed.encode()).hexdigest(), 16)
        self.weather_factor = 0.9 + (seed_int % 20) / 100  # 0.9-1.1
        self.referee_strictness = 0.8 + (seed_int % 40) / 100  # 0.8-1.2
    
    def simulate(self, home_team: SimulatedTeam, 
                 away_team: SimulatedTeam) -> MatchResult:
        """
        Simulate a full match between two teams.
        """
        match_id = f"SIM_{home_team.id}_{away_team.id}_{self.seed[:8]}"
        
        result = MatchResult(
            match_id=match_id,
            home_team_id=home_team.id,
            away_team_id=away_team.id,
            home_team_name=home_team.name,
            away_team_name=away_team.name,
        )
        
        # Get starting lineups
        home_xi = home_team.get_starting_xi()
        away_xi = away_team.get_starting_xi()
        
        # Calculate team strengths
        home_strength = self._calculate_team_strength(home_team, home_xi, is_home=True)
        away_strength = self._calculate_team_strength(away_team, away_xi, is_home=False)
        
        # Possession based on strength ratio
        total_strength = home_strength + away_strength
        result.home_possession = round((home_strength / total_strength) * 100, 1)
        result.away_possession = round(100 - result.home_possession, 1)
        
        # Initialize player ratings
        for player in home_xi + away_xi:
            result.player_ratings[player.id] = 6.0  # Base rating
        
        # Simulate each minute
        for minute in range(1, self.config.MINUTES + 1):
            # Check for events
            self._simulate_minute(
                minute, result,
                home_team, away_team,
                home_xi, away_xi,
                home_strength, away_strength
            )
        
        # Add stoppage time events (simplified)
        stoppage = random.randint(1, 5)
        for minute in range(91, 91 + stoppage):
            self._simulate_minute(
                minute, result,
                home_team, away_team,
                home_xi, away_xi,
                home_strength, away_strength,
                is_stoppage=True
            )
        
        # Calculate final player ratings and MOTM
        self._finalize_ratings(result, home_xi, away_xi)
        
        # Update team morale based on result
        if result.home_score > result.away_score:
            home_team.morale = min(100, home_team.morale + 5)
            away_team.morale = max(30, away_team.morale - 3)
        elif result.away_score > result.home_score:
            away_team.morale = min(100, away_team.morale + 5)
            home_team.morale = max(30, home_team.morale - 3)
        
        return result
    
    def _calculate_team_strength(self, team: SimulatedTeam, 
                                  lineup: List[AthleticAgent],
                                  is_home: bool) -> float:
        """Calculate effective team strength for this match."""
        # Base strength from players
        if lineup:
            avg_rating = sum(p.effective_rating for p in lineup) / len(lineup)
        else:
            avg_rating = 60
        
        # Team-level modifiers
        strength = avg_rating
        strength *= (team.morale / 70)  # Morale impact
        strength *= (team.chemistry / 70)  # Chemistry impact
        strength *= self.weather_factor  # Weather
        
        # Home advantage
        if is_home:
            strength *= self.config.HOME_ADVANTAGE
        
        return strength
    
    def _simulate_minute(self, minute: int, result: MatchResult,
                         home_team: SimulatedTeam, away_team: SimulatedTeam,
                         home_xi: List[AthleticAgent], away_xi: List[AthleticAgent],
                         home_strength: float, away_strength: float,
                         is_stoppage: bool = False):
        """Simulate one minute of match time."""
        
        total_strength = home_strength + away_strength
        
        # Determine which team has the ball (probabilistically)
        home_has_ball = random.random() < (home_strength / total_strength)
        
        attacking_team = home_team if home_has_ball else away_team
        defending_team = away_team if home_has_ball else home_team
        attackers = home_xi if home_has_ball else away_xi
        defenders = away_xi if home_has_ball else home_xi
        attack_strength = home_strength if home_has_ball else away_strength
        defend_strength = away_strength if home_has_ball else home_strength
        
        # Goal chance
        goal_chance = self.config.BASE_GOAL_CHANCE * (attack_strength / defend_strength)
        
        # Late game drama - slightly higher chance of goals in last 10 mins
        if minute > 80:
            goal_chance *= 1.2
        
        if random.random() < goal_chance:
            self._score_goal(
                minute, result, attacking_team, defending_team,
                attackers, home_has_ball
            )
        
        # Card chance
        card_chance = self.config.BASE_CARD_CHANCE * self.referee_strictness
        if random.random() < card_chance:
            self._give_card(minute, result, defenders, not home_has_ball)
        
        # Injury chance (reduced in stoppage time)
        if not is_stoppage:
            injury_chance = self.config.BASE_INJURY_CHANCE
            all_players = home_xi + away_xi
            for player in all_players:
                if random.random() < injury_chance * player.injury_proneness:
                    self._player_injured(minute, result, player, 
                                         player in home_xi)
    
    def _score_goal(self, minute: int, result: MatchResult,
                    attacking_team: SimulatedTeam, defending_team: SimulatedTeam,
                    attackers: List[AthleticAgent], is_home: bool):
        """Process a goal being scored."""
        
        # Select scorer (weighted by position and skill)
        scorer_weights = []
        for p in attackers:
            weight = p.effective_rating
            if p.position == "FWD":
                weight *= 3
            elif p.position == "MID":
                weight *= 1.5
            elif p.position == "DEF":
                weight *= 0.3
            else:  # GK
                weight *= 0.01
            scorer_weights.append(weight)
        
        total_weight = sum(scorer_weights)
        if total_weight == 0:
            return
        
        scorer_weights = [w / total_weight for w in scorer_weights]
        scorer = random.choices(attackers, weights=scorer_weights)[0]
        
        # Update score
        if is_home:
            result.home_score += 1
        else:
            result.away_score += 1
        
        # Record goal
        scorer.goals += 1
        result.player_ratings[scorer.id] = result.player_ratings.get(scorer.id, 6.0) + 1.0
        
        event = MatchEvent(
            minute=minute,
            event_type=MatchEventType.GOAL,
            team_id=attacking_team.id,
            player_id=scorer.id,
            player_name=scorer.name,
            description=f"⚽ GOAL! {scorer.name} ({attacking_team.short_name or attacking_team.name})"
        )
        
        # Assist
        if random.random() < self.config.BASE_ASSIST_CHANCE:
            possible_assisters = [p for p in attackers if p.id != scorer.id]
            if possible_assisters:
                # Midfielders more likely to assist
                assist_weights = []
                for p in possible_assisters:
                    weight = p.effective_rating
                    if p.position == "MID":
                        weight *= 2
                    elif p.position == "FWD":
                        weight *= 1.5
                    assist_weights.append(weight)
                
                total_w = sum(assist_weights)
                if total_w > 0:
                    assist_weights = [w / total_w for w in assist_weights]
                    assister = random.choices(possible_assisters, weights=assist_weights)[0]
                    
                    assister.assists += 1
                    result.player_ratings[assister.id] = result.player_ratings.get(assister.id, 6.0) + 0.5
                    
                    event.assist_player_id = assister.id
                    event.assist_player_name = assister.name
                    event.description += f" (assist: {assister.name})"
        
        result.events.append(event)
    
    def _give_card(self, minute: int, result: MatchResult,
                   players: List[AthleticAgent], is_home: bool):
        """Give a card to a player."""
        
        # More aggressive players more likely to get cards
        card_weights = [p.aggression + 0.1 for p in players]
        total = sum(card_weights)
        card_weights = [w / total for w in card_weights]
        
        player = random.choices(players, weights=card_weights)[0]
        
        # Usually yellow, sometimes red
        is_red = random.random() < 0.1
        
        if is_red:
            player.red_cards += 1
            event_type = MatchEventType.RED_CARD
            emoji = "🟥"
        else:
            player.yellow_cards += 1
            event_type = MatchEventType.YELLOW_CARD
            emoji = "🟨"
            
            # Second yellow = red
            if player.yellow_cards >= 2:
                player.red_cards += 1
                player.status = AgentStatus.SUSPENDED
                emoji = "🟨🟥"
        
        result.player_ratings[player.id] = result.player_ratings.get(player.id, 6.0) - 0.5
        
        team_id = result.home_team_id if is_home else result.away_team_id
        
        result.events.append(MatchEvent(
            minute=minute,
            event_type=event_type,
            team_id=team_id,
            player_id=player.id,
            player_name=player.name,
            description=f"{emoji} {player.name} booked"
        ))
    
    def _player_injured(self, minute: int, result: MatchResult,
                        player: AthleticAgent, is_home: bool):
        """Handle player injury."""
        injury = player.check_injury(match_intensity=0.7)
        
        if injury:
            team_id = result.home_team_id if is_home else result.away_team_id
            result.player_ratings[player.id] = result.player_ratings.get(player.id, 6.0) - 1.0
            
            result.events.append(MatchEvent(
                minute=minute,
                event_type=MatchEventType.INJURY,
                team_id=team_id,
                player_id=player.id,
                player_name=player.name,
                description=f"🏥 {player.name} injured ({injury})"
            ))
    
    def _finalize_ratings(self, result: MatchResult,
                          home_xi: List[AthleticAgent],
                          away_xi: List[AthleticAgent]):
        """Calculate final ratings and select MOTM."""
        
        # Add small random variation to ratings
        for player_id in result.player_ratings:
            result.player_ratings[player_id] += random.uniform(-0.3, 0.3)
            result.player_ratings[player_id] = round(
                max(4.0, min(10.0, result.player_ratings[player_id])), 1
            )
        
        # Find MOTM
        best_rating = 0
        best_player = None
        
        for player in home_xi + away_xi:
            rating = result.player_ratings.get(player.id, 6.0)
            if rating > best_rating:
                best_rating = rating
                best_player = player
        
        if best_player:
            result.motm_id = best_player.id
            result.motm_name = best_player.name


# =============================================================================
# LEAGUE SIMULATION
# =============================================================================

class FootballSimulation:
    """
    Full league simulation engine.
    
    Can be initialized from a real-world snapshot for "fork" scenarios.
    """
    
    def __init__(self, game_hash: str):
        self.game_hash = game_hash
        random.seed(game_hash)
        
        self.teams: Dict[str, SimulatedTeam] = {}
        self.match_history: List[MatchResult] = []
        self.current_matchday = 0
        
        # Fixtures (list of (home_id, away_id) tuples per matchday)
        self.fixtures: Dict[int, List[Tuple[str, str]]] = {}
    
    def initialize_from_snapshot(self, snapshot_path: str) -> None:
        """
        Initialize simulation from a real-world snapshot.
        
        This is the "fork" point for counterfactual simulation.
        """
        from backend.core.football_data_client import Snapshot
        
        snapshot = Snapshot.load(snapshot_path)
        
        print(f"📂 Loading snapshot: {snapshot.competition_name}")
        print(f"   Season: {snapshot.season}, Matchday: {snapshot.matchday}")
        
        self.current_matchday = snapshot.matchday
        
        # Create teams from snapshot
        for team_data in snapshot.teams:
            team = SimulatedTeam(
                id=str(team_data.id),
                name=team_data.name,
                short_name=team_data.tla or team_data.name[:3].upper(),
                strength_rating=team_data.strength_rating,
                position=team_data.position,
                played=team_data.played,
                won=team_data.won,
                drawn=team_data.draw,
                lost=team_data.lost,
                goals_for=team_data.goals_for,
                goals_against=team_data.goals_against,
                points=team_data.points,
            )
            
            # Create players from squad
            for player_data in team_data.squad:
                # Map API positions to our positions
                pos_map = {
                    "Goalkeeper": "GK",
                    "Defence": "DEF", "Left-Back": "DEF", "Right-Back": "DEF",
                    "Centre-Back": "DEF", "Defensive Midfield": "MID",
                    "Midfield": "MID", "Central Midfield": "MID",
                    "Attacking Midfield": "MID", "Left Winger": "FWD",
                    "Right Winger": "FWD", "Offence": "FWD",
                    "Centre-Forward": "FWD",
                }
                position = pos_map.get(player_data.position, "MID")
                
                # Estimate skill based on team strength
                base_skill = team_data.strength_rating
                skill_variance = random.randint(-10, 10)
                
                player = AthleticAgent(
                    id=str(player_data.id),
                    name=player_data.name,
                    archetype=AthleticArchetype.WORKHORSE,  # Default
                    position=position,
                    skill=max(50, min(99, base_skill + skill_variance)),
                    pace=random.randint(60, 90),
                    stamina=random.randint(65, 90),
                    strength=random.randint(55, 85),
                    team_id=team.id,
                    shirt_number=player_data.shirt_number,
                )
                
                team.players.append(player)
            
            self.teams[team.id] = team
        
        print(f"✅ Loaded {len(self.teams)} teams")
    
    def initialize_default(self, num_teams: int = 20) -> None:
        """Initialize with generated teams (no snapshot needed)."""
        
        team_names = [
            "Sim United", "Sim City", "Sim Rovers", "Sim Athletic",
            "Sim Town", "Sim FC", "Sim Wanderers", "Sim Albion",
            "Sim Villa", "Sim Palace", "Sim Forest", "Sim County",
            "Sim Hotspur", "Sim Borough", "Sim Rangers", "Sim Celtic",
            "Sim Wednesday", "Sim Argyle", "Sim Orient", "Sim Stanley"
        ]
        
        for i in range(num_teams):
            name = team_names[i] if i < len(team_names) else f"Team {i+1}"
            team_id = f"team_{i+1}"
            
            team = SimulatedTeam(
                id=team_id,
                name=name,
                short_name=name.split()[-1][:3].upper(),
                strength_rating=random.randint(60, 90),
                position=i + 1,
            )
            
            # Generate squad
            squad_structure = [
                ("GK", 2), ("DEF", 6), ("MID", 6), ("FWD", 4)
            ]
            
            for position, count in squad_structure:
                for j in range(count):
                    player = create_random_athletic_agent(position=position)
                    player.team_id = team_id
                    team.players.append(player)
            
            self.teams[team_id] = team
        
        # Generate fixtures
        self._generate_fixtures()
        
        print(f"✅ Initialized {num_teams} teams with {sum(len(t.players) for t in self.teams.values())} total players")
    
    def _generate_fixtures(self) -> None:
        """Generate a full season's fixtures using round-robin."""
        team_ids = list(self.teams.keys())
        n = len(team_ids)
        
        if n % 2 == 1:
            team_ids.append(None)  # Bye
            n += 1
        
        matchday = 1
        
        # First half of season
        for round_num in range(n - 1):
            round_fixtures = []
            for i in range(n // 2):
                home = team_ids[i]
                away = team_ids[n - 1 - i]
                
                if home and away:
                    round_fixtures.append((home, away))
            
            self.fixtures[matchday] = round_fixtures
            matchday += 1
            
            # Rotate teams (keep first team fixed)
            team_ids = [team_ids[0]] + [team_ids[-1]] + team_ids[1:-1]
        
        # Second half (reverse fixtures)
        first_half = matchday - 1
        for md in range(1, first_half + 1):
            reversed_fixtures = [(away, home) for home, away in self.fixtures[md]]
            self.fixtures[matchday] = reversed_fixtures
            matchday += 1
    
    def simulate_match(self, home_team_id: str, away_team_id: str) -> MatchResult:
        """Simulate a single match."""
        home_team = self.teams.get(home_team_id)
        away_team = self.teams.get(away_team_id)
        
        if not home_team or not away_team:
            raise ValueError(f"Team not found: {home_team_id} or {away_team_id}")
        
        # Create match-specific seed
        match_seed = hashlib.sha256(
            f"{self.game_hash}_{home_team_id}_{away_team_id}".encode()
        ).hexdigest()
        
        simulator = MatchSimulator(match_seed)
        result = simulator.simulate(home_team, away_team)
        
        # Update team stats
        if result.home_score > result.away_score:
            home_team.update_league_position("WIN", result.home_score, result.away_score)
            away_team.update_league_position("LOSS", result.away_score, result.home_score)
        elif result.away_score > result.home_score:
            away_team.update_league_position("WIN", result.away_score, result.home_score)
            home_team.update_league_position("LOSS", result.home_score, result.away_score)
        else:
            home_team.update_league_position("DRAW", result.home_score, result.away_score)
            away_team.update_league_position("DRAW", result.away_score, result.home_score)
        
        self.match_history.append(result)
        
        return result
    
    def simulate_matchday(self, matchday: int) -> List[MatchResult]:
        """Simulate all matches for a given matchday."""
        if matchday not in self.fixtures:
            raise ValueError(f"No fixtures for matchday {matchday}")
        
        results = []
        for home_id, away_id in self.fixtures[matchday]:
            result = self.simulate_match(home_id, away_id)
            results.append(result)
        
        self.current_matchday = matchday
        self._update_positions()
        
        return results
    
    def simulate_remaining_season(self) -> Dict[str, Any]:
        """Simulate all remaining matchdays."""
        start_matchday = self.current_matchday + 1
        total_matchdays = max(self.fixtures.keys()) if self.fixtures else 38
        
        all_results = []
        
        for matchday in range(start_matchday, total_matchdays + 1):
            if matchday in self.fixtures:
                results = self.simulate_matchday(matchday)
                all_results.extend(results)
        
        return {
            "matchdays_simulated": total_matchdays - start_matchday + 1,
            "matches_played": len(all_results),
            "final_standings": self.get_standings(),
            "champion": self.get_standings()[0]["name"] if self.get_standings() else None,
        }
    
    def _update_positions(self) -> None:
        """Update league positions based on points/GD."""
        sorted_teams = sorted(
            self.teams.values(),
            key=lambda t: (t.points, t.goal_difference, t.goals_for),
            reverse=True
        )
        
        for i, team in enumerate(sorted_teams):
            team.position = i + 1
    
    def get_standings(self) -> List[Dict]:
        """Get current league table."""
        self._update_positions()
        
        sorted_teams = sorted(self.teams.values(), key=lambda t: t.position)
        return [t.to_dict() for t in sorted_teams]
    
    def get_betting_outcome(self, match_result: MatchResult) -> str:
        """Get simple outcome for bet settlement."""
        return match_result.result_string


# =============================================================================
# PROVABLY FAIR WRAPPER
# =============================================================================

def get_provable_game_hash(server_seed: str, client_seed: str, nonce: str) -> str:
    """Generate deterministic hash from seeds."""
    combined = f"{server_seed}-{client_seed}-{nonce}"
    return hashlib.sha256(combined.encode()).hexdigest()


def run_simulation(server_seed: str, client_seed: str, nonce: str,
                   mode: str = "matchday", 
                   home_id: str = None, away_id: str = None,
                   matchday: int = 1,
                   snapshot_path: str = None,
                   verbose: bool = False) -> str:
    """
    Main entry point for simulation.
    
    Returns outcome string for bet settlement.
    """
    game_hash = get_provable_game_hash(server_seed, client_seed, nonce)
    
    sim = FootballSimulation(game_hash)
    
    # Initialize
    if snapshot_path and os.path.exists(snapshot_path):
        sim.initialize_from_snapshot(snapshot_path)
    else:
        sim.initialize_default(20)
    
    if mode == "match" and home_id and away_id:
        # Single match
        result = sim.simulate_match(home_id, away_id)
        
        if verbose:
            print(f"\n⚽ {result.home_team_name} {result.home_score} - {result.away_score} {result.away_team_name}")
            print(f"\nEvents:")
            for event in result.events:
                print(f"   {event.minute}' {event.description}")
            print(f"\nMOTM: {result.motm_name}")
        
        return result.result_string
    
    elif mode == "matchday":
        # Full matchday
        results = sim.simulate_matchday(matchday)
        
        if verbose:
            print(f"\n📅 Matchday {matchday} Results:")
            for r in results:
                print(f"   {r.home_team_name} {r.home_score}-{r.away_score} {r.away_team_name}")
            print(f"\n📊 Standings:")
            for s in sim.get_standings()[:5]:
                print(f"   {s['position']}. {s['name']} - {s['points']} pts")
        
        # Return first match result for simple betting
        return results[0].result_string if results else "NO_MATCH"
    
    elif mode == "season":
        # Full remaining season
        summary = sim.simulate_remaining_season()
        
        if verbose:
            print(f"\n🏆 Season Complete!")
            print(f"   Champion: {summary['champion']}")
            print(f"\n📊 Final Standings:")
            for s in summary['final_standings'][:5]:
                print(f"   {s['position']}. {s['name']} - {s['points']} pts")
        
        return f"CHAMPION_{summary['champion'].replace(' ', '_').upper()}" if summary['champion'] else "NO_CHAMPION"
    
    return "UNKNOWN"


# =============================================================================
# CLI
# =============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Football League Simulation")
    parser.add_argument("server_seed", help="Server seed")
    parser.add_argument("client_seed", help="Client seed")
    parser.add_argument("nonce", help="Nonce")
    parser.add_argument("--mode", choices=["match", "matchday", "season"], 
                        default="matchday", help="Simulation mode")
    parser.add_argument("--home", help="Home team ID (for match mode)")
    parser.add_argument("--away", help="Away team ID (for match mode)")
    parser.add_argument("--matchday", type=int, default=1, help="Matchday number")
    parser.add_argument("--snapshot", help="Path to snapshot JSON")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    result = run_simulation(
        args.server_seed,
        args.client_seed,
        args.nonce,
        mode=args.mode,
        home_id=args.home,
        away_id=args.away,
        matchday=args.matchday,
        snapshot_path=args.snapshot,
        verbose=args.verbose,
    )
    
    if not args.verbose:
        print(result)
