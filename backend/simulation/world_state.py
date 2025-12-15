"""
World State Module
Manages the simulation world state data.
"""

import json
import os
from datetime import datetime
from typing import List
from pydantic import BaseModel, Field


class WorldState(BaseModel):
    """
    Pydantic model for world state validation.
    """
    last_updated: datetime = Field(default_factory=datetime.now)
    global_tension: float = Field(..., ge=0.0, le=1.0, description="0.0 is Peace, 1.0 is Nuclear War")
    recent_reasoning: str = Field(default="System initialized.", description="Why the agent made the last decision")
    
    # Future-proofing: A log of recent events
    event_log: List[str] = Field(default_factory=list)


class WorldStateManager:
    """
    Manages loading and saving world state to/from JSON file.
    """
    
    def __init__(self, state_file: str | None = None):
        """
        Initialize the world state manager.
        
        Args:
            state_file: Path to the JSON file storing world state. 
                       If None, defaults to world_state.json in the simulation directory.
        """
        if state_file is None:
            # Default to world_state.json in the same directory as this file
            state_file = os.path.join(os.path.dirname(__file__), "world_state.json")
        self.state_file = state_file
        self._state: WorldState | None = None
    
    def load(self) -> WorldState:
        """
        Load world state from JSON file.
        If file doesn't exist, returns a default state.
        
        Returns:
            WorldState instance
        """
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, "r") as f:
                    json_data = f.read()
                # Use Pydantic V2 model_validate_json for JSON parsing
                data = json.loads(json_data)
                # Convert last_updated string to datetime if needed
                if isinstance(data.get("last_updated"), str):
                    data["last_updated"] = datetime.fromisoformat(data["last_updated"])
                self._state = WorldState.model_validate(data)
            except (json.JSONDecodeError, ValueError, KeyError) as e:
                print(f"⚠️  Error loading world state: {e}. Using default state.")
                # Create default state with required global_tension
                self._state = WorldState(global_tension=0.0)
        else:
            # Create default state with required global_tension
            self._state = WorldState(global_tension=0.0)
        
        return self._state
    
    def save(self, state: WorldState | None = None) -> None:
        """
        Save world state to JSON file.
        
        Args:
            state: WorldState instance to save. If None, uses current state.
        """
        if state is None:
            state = self._state
        
        if state is None:
            raise ValueError("No state to save. Load or create a state first.")
        
        # Update last_updated before saving
        state.last_updated = datetime.now()
        
        try:
            # Use Pydantic V2 model_dump_json for JSON serialization
            json_data = state.model_dump_json(indent=2)
            with open(self.state_file, "w") as f:
                f.write(json_data)
        except Exception as e:
            raise IOError(f"Failed to save world state: {e}")
    
    def update(self, **kwargs) -> WorldState:
        """
        Update world state fields using Pydantic V2 model_copy.
        
        Args:
            **kwargs: Fields to update
        
        Returns:
            Updated WorldState instance
        """
        if self._state is None:
            self.load()
        
        # Update last_updated
        kwargs["last_updated"] = datetime.now()
        
        # Use Pydantic V2 model_copy with update for immutability
        self._state = self._state.model_copy(update=kwargs)
        
        return self._state
    
    def get(self) -> WorldState:
        """
        Get current world state, loading if necessary.
        
        Returns:
            WorldState instance
        """
        if self._state is None:
            self.load()
        return self._state


# Global instance for easy access
_world_state_manager: WorldStateManager | None = None


def get_world_state_manager() -> WorldStateManager:
    """
    Get or create the global world state manager instance.
    
    Returns:
        WorldStateManager instance
    """
    global _world_state_manager
    if _world_state_manager is None:
        _world_state_manager = WorldStateManager()
    return _world_state_manager


def load_world_state() -> WorldState:
    """
    Convenience function to load world state.
    
    Returns:
        WorldState instance
    """
    return get_world_state_manager().load()


def save_world_state(state: WorldState | None = None) -> None:
    """
    Convenience function to save world state.
    
    Args:
        state: WorldState instance to save. If None, uses current state.
    """
    get_world_state_manager().save(state)


def update_world_state(**kwargs) -> WorldState:
    """
    Convenience function to update world state.
    
    Args:
        **kwargs: Fields to update
    
    Returns:
        Updated WorldState instance
    """
    manager = get_world_state_manager()
    state = manager.update(**kwargs)
    manager.save()
    return state

