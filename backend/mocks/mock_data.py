"""
Mock Repositories
=================

Mock implementations of repositories for development and testing.
Used when USE_MOCKS=true or database is not available.
"""

from types import SimpleNamespace
from typing import Optional, List
from datetime import datetime
import uuid


class MockTimelineRepository:
    """Mock timeline repository for development."""
    
    def __init__(self):
        self.timelines = {}
        self.flaps = []
    
    async def get(self, timeline_id: str):
        """Get a timeline (returns mock if not found)."""
        if timeline_id not in self.timelines:
            return SimpleNamespace(
                id=timeline_id,
                timeline_id=timeline_id,
                name=f"Timeline {timeline_id[:8]}",
                stability=75.0,
                price_yes=0.65,
                total_volume_usd=50000.0,
                founder_id=None,
                active_agent_count=5,
                keywords=["market", "trading"],
                narrative="Active trading timeline",
                connected_timeline_ids=[],
                total_volume=50000.0
            )
        return self.timelines[timeline_id]
    
    async def update_stability(self, timeline_id: str, stability: float):
        """Update timeline stability."""
        timeline = await self.get(timeline_id)
        timeline.stability = stability
    
    async def set_decay_multiplier(self, timeline_id: str, multiplier: float):
        """Set decay multiplier."""
        timeline = await self.get(timeline_id)
        timeline.decay_multiplier = multiplier
    
    async def get_flaps_since(self, timeline_id: str, cutoff):
        """Get flaps since cutoff time."""
        return [f for f in self.flaps if f.timeline_id == timeline_id and f.timestamp >= cutoff]
    
    async def update_logic_gap(self, timeline_id: str, gap: float):
        """Update logic gap."""
        timeline = await self.get(timeline_id)
        timeline.logic_gap = gap
    
    async def create_fork(self, parent_id: str, narrative: str, initial_stability: float, founder_id: str):
        """Create a new fork timeline."""
        fork_id = f"fork_{uuid.uuid4().hex[:8]}"
        fork = SimpleNamespace(
            id=fork_id,
            timeline_id=fork_id,
            name=f"Fork from {parent_id[:8]}",
            stability=initial_stability,
            price_yes=0.5,
            total_volume_usd=0.0,
            founder_id=founder_id,
            active_agent_count=0,
            keywords=["fork", "divergence"],
            narrative=narrative,
            connected_timeline_ids=[parent_id],
            total_volume=0.0
        )
        self.timelines[fork_id] = fork
        return fork


class MockAgentRepository:
    """Mock agent repository for development."""
    
    def __init__(self):
        self.agents = {}
    
    async def get(self, agent_id: str):
        """Get an agent (returns mock if not found)."""
        if agent_id not in self.agents:
            return SimpleNamespace(
                agent_id=agent_id,
                id=agent_id,
                name=agent_id,
                archetype="shark",
                owner_id="system"
            )
        return self.agents[agent_id]


class MockParadoxRepository:
    """Mock paradox repository for development."""
    
    def __init__(self):
        self.paradoxes = {}
    
    async def get(self, paradox_id: str):
        """Get a paradox (returns None if not found)."""
        return self.paradoxes.get(paradox_id)
    
    async def get_active(self) -> List:
        """Get all active paradoxes."""
        return list(self.paradoxes.values())
    
    async def get_by_timeline(self, timeline_id: str) -> List:
        """Get paradoxes by timeline."""
        return [p for p in self.paradoxes.values() if getattr(p, 'timeline_id', None) == timeline_id]


class MockUserRepository:
    """Mock user repository for development."""
    
    def __init__(self):
        self.users = {}
        self.positions = {}
        self.watchlists = {}
        self.private_forks = {}
    
    async def get(self, user_id: str):
        """Get a user (returns mock if not found)."""
        if user_id not in self.users:
            return SimpleNamespace(
                id=user_id,
                user_id=user_id,
                username=f"user_{user_id[:8]}",
                email=f"user_{user_id[:8]}@example.com",
                tier="free"
            )
        return self.users[user_id]
    
    async def get_by_email(self, email: str):
        """Get user by email."""
        for user in self.users.values():
            if getattr(user, 'email', None) == email:
                return user
        return None
    
    async def get_positions(self, user_id: str) -> List:
        """Get user positions."""
        return self.positions.get(user_id, [])
    
    async def get_watchlist(self, user_id: str) -> List:
        """Get user watchlist."""
        return self.watchlists.get(user_id, [])
    
    async def get_private_forks(self, user_id: str) -> List:
        """Get user private forks."""
        return self.private_forks.get(user_id, [])


