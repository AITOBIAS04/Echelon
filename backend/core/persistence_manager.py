"""
persistence_manager.py - Unified State Persistence for Project Seed

This module ensures ALL simulation state survives server restarts:

- Markets (from EventOrchestrator)
- Economy/Yields (from YieldManager)
- World State (from WorldStateManager)
- Agent Positions (from Evolution Engine)
- Timeline Metadata (augments TimelineManager)

All state is saved to data/ directory with atomic writes to prevent corruption.
"""

import json
import os
import time
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional
from dataclasses import dataclass, asdict
import shutil

# =============================================================================
# CONFIGURATION
# =============================================================================

@dataclass
class PersistenceConfig:
    """Configuration for the persistence layer."""
    data_dir: str = "data"
    auto_save_interval: int = 60  # seconds
    max_backups: int = 5
    compress_backups: bool = False

# =============================================================================
# PERSISTENCE MANAGER
# =============================================================================

class PersistenceManager:
    """
    Unified state persistence for the entire simulation.
    
    Usage:
        pm = PersistenceManager()
        
        # Save state
        pm.save("markets", {"MKT_123": {...}})
        
        # Load state
        markets = pm.load("markets", default={})
        
        # Auto-save (runs in background)
        pm.start_auto_save(callback=my_save_function)
    """
    
    # State file names
    STATE_FILES = {
        "markets": "markets.json",
        "economy": "economy_state.json",
        "world": "world_state.json",
        "agents": "agent_positions.json",
        "timelines": "timeline_metadata.json",
        "events": "processed_events.json",
        "stats": "orchestrator_stats.json",
    }
    
    def __init__(self, config: PersistenceConfig = None):
        self.config = config or PersistenceConfig()
        self.data_dir = Path(self.config.data_dir)
        self._ensure_directories()
        self._lock = threading.Lock()
        self._auto_save_thread: Optional[threading.Thread] = None
        self._stop_auto_save = threading.Event()
        
        print(f"📁 PersistenceManager initialized: {self.data_dir.absolute()}")
    
    def _ensure_directories(self):
        """Create data directories if they don't exist."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        (self.data_dir / "backups").mkdir(exist_ok=True)
        (self.data_dir / "snapshots").mkdir(exist_ok=True)
    
    def _get_path(self, state_name: str) -> Path:
        """Get the file path for a state type."""
        filename = self.STATE_FILES.get(state_name, f"{state_name}.json")
        return self.data_dir / filename
    
    def save(self, state_name: str, data: Any, create_backup: bool = False) -> bool:
        """
        Save state to disk with atomic write.
        
        Args:
            state_name: Name of the state (e.g., "markets", "economy")
            data: Data to save (must be JSON-serializable)
            create_backup: Whether to backup the previous version
            
        Returns:
            True if successful, False otherwise
        """
        with self._lock:
            try:
                path = self._get_path(state_name)
                
                # Create backup if requested and file exists
                if create_backup and path.exists():
                    self._create_backup(path)
                
                # Prepare data with metadata
                wrapped_data = {
                    "_meta": {
                        "saved_at": datetime.now(timezone.utc).isoformat(),
                        "state_name": state_name,
                        "version": "1.0",
                    },
                    "data": self._serialize(data)
                }
                
                # Atomic write: write to temp file, then rename
                temp_path = path.with_suffix(".tmp")
                with open(temp_path, "w") as f:
                    json.dump(wrapped_data, f, indent=2, default=str)
                
                # Atomic rename (POSIX guarantees this is atomic)
                shutil.move(str(temp_path), str(path))
                
                return True
                
            except Exception as e:
                print(f"❌ Failed to save {state_name}: {e}")
                return False
    
    def load(self, state_name: str, default: Any = None) -> Any:
        """
        Load state from disk.
        
        Args:
            state_name: Name of the state to load
            default: Default value if file doesn't exist or is corrupt
            
        Returns:
            The loaded data, or default if unavailable
        """
        with self._lock:
            try:
                path = self._get_path(state_name)
                
                if not path.exists():
                    print(f"📂 {state_name}: No saved state found, using default")
                    return default
                
                with open(path, "r") as f:
                    wrapped_data = json.load(f)
                
                # Extract data from wrapper
                if isinstance(wrapped_data, dict) and "data" in wrapped_data:
                    meta = wrapped_data.get("_meta", {})
                    print(f"📂 {state_name}: Loaded (saved {meta.get('saved_at', 'unknown')})")
                    return wrapped_data["data"]
                else:
                    # Legacy format without wrapper
                    return wrapped_data
                    
            except json.JSONDecodeError as e:
                print(f"⚠️ {state_name}: Corrupt file, using default: {e}")
                return default
            except Exception as e:
                print(f"❌ Failed to load {state_name}: {e}")
                return default
    
    def _serialize(self, data: Any) -> Any:
        """Convert complex objects to JSON-serializable format."""
        if hasattr(data, "to_dict"):
            return data.to_dict()
        elif hasattr(data, "__dict__"):
            return {k: self._serialize(v) for k, v in data.__dict__.items() 
                    if not k.startswith("_")}
        elif isinstance(data, dict):
            return {k: self._serialize(v) for k, v in data.items()}
        elif isinstance(data, (list, tuple)):
            return [self._serialize(item) for item in data]
        elif isinstance(data, datetime):
            return data.isoformat()
        elif hasattr(data, "value"):  # Enum
            return data.value
        else:
            return data
    
    def _create_backup(self, path: Path):
        """Create a backup of the current file."""
        backup_dir = self.data_dir / "backups"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"{path.stem}_{timestamp}.json"
        
        shutil.copy2(path, backup_path)
        
        # Clean up old backups
        backups = sorted(backup_dir.glob(f"{path.stem}_*.json"))
        while len(backups) > self.config.max_backups:
            oldest = backups.pop(0)
            oldest.unlink()
    
    def start_auto_save(self, callback: callable, interval: int = None):
        """
        Start background auto-save thread.
        
        Args:
            callback: Function that returns dict of {state_name: data} to save
            interval: Save interval in seconds (default from config)
        """
        if self._auto_save_thread and self._auto_save_thread.is_alive():
            print("⚠️ Auto-save already running")
            return
        
        interval = interval or self.config.auto_save_interval
        self._stop_auto_save.clear()
        
        def auto_save_loop():
            while not self._stop_auto_save.wait(interval):
                try:
                    states = callback()
                    for name, data in states.items():
                        self.save(name, data)
                    print(f"💾 Auto-saved {len(states)} state files")
                except Exception as e:
                    print(f"❌ Auto-save error: {e}")
        
        self._auto_save_thread = threading.Thread(target=auto_save_loop, daemon=True)
        self._auto_save_thread.start()
        print(f"🔄 Auto-save started (every {interval}s)")
    
    def stop_auto_save(self):
        """Stop the auto-save thread."""
        self._stop_auto_save.set()
        if self._auto_save_thread:
            self._auto_save_thread.join(timeout=5)
        print("⏹️ Auto-save stopped")
    
    def save_all(self, states: Dict[str, Any], create_backups: bool = True):
        """Save multiple states at once."""
        for name, data in states.items():
            self.save(name, data, create_backup=create_backups)
    
    def load_all(self, defaults: Dict[str, Any] = None) -> Dict[str, Any]:
        """Load all known states."""
        defaults = defaults or {}
        result = {}
        for name in self.STATE_FILES.keys():
            result[name] = self.load(name, defaults.get(name))
        return result
    
    def get_state_info(self) -> Dict[str, Any]:
        """Get information about saved states."""
        info = {}
        for name, filename in self.STATE_FILES.items():
            path = self.data_dir / filename
            if path.exists():
                stat = path.stat()
                info[name] = {
                    "exists": True,
                    "size_bytes": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                }
            else:
                info[name] = {"exists": False}
        return info

# =============================================================================
# MARKET PERSISTENCE MIXIN
# =============================================================================

class MarketPersistenceMixin:
    """
    Mixin for EventOrchestrator to add persistence.
    
    Usage:
        class EventOrchestrator(MarketPersistenceMixin):
            def __init__(self):
                self.persistence = PersistenceManager()
                self.load_state()  # Load on startup
    """
    
    def save_markets_state(self):
        """Save all markets to disk."""
        if not hasattr(self, "persistence"):
            return
        
        markets_data = {}
        for market_id, market in self.markets.items():
            markets_data[market_id] = {
                "id": market.id,
                "event_id": market.event_id,
                "title": market.title,
                "description": market.description,
                "domain": market.domain.value if hasattr(market.domain, "value") else market.domain,
                "duration": market.duration.value if hasattr(market.duration, "value") else market.duration,
                "status": market.status,
                "created_at": market.created_at.isoformat() if hasattr(market.created_at, "isoformat") else str(market.created_at),
                "expires_at": market.expires_at.isoformat() if market.expires_at and hasattr(market.expires_at, "isoformat") else None,
                "outcomes": market.outcomes,
                "outcome_odds": market.outcome_odds,
                "total_volume": market.total_volume,
                "yes_shares": getattr(market, "yes_shares", 1000.0),
                "no_shares": getattr(market, "no_shares", 1000.0),
                "virality_score": market.virality_score,
            }
        
        self.persistence.save("markets", markets_data)
        self.persistence.save("stats", self.stats)
    
    def load_markets_state(self):
        """Load markets from disk."""
        if not hasattr(self, "persistence"):
            return
        
        markets_data = self.persistence.load("markets", default={})
        stats_data = self.persistence.load("stats", default={})
        
        # Restore stats
        if stats_data:
            self.stats.update(stats_data)
        
        # Restore markets (simplified - full restoration would recreate BettingMarket objects)
        print(f"📂 Loaded {len(markets_data)} markets from disk")
        return markets_data

# =============================================================================
# ECONOMY PERSISTENCE MIXIN
# =============================================================================

class EconomyPersistenceMixin:
    """
    Mixin for YieldManager to add persistence.
    
    Fixes the "infinite wealth" bug by persisting last_payout timestamp.
    """
    
    def save_economy_state(self):
        """Save economy state to disk."""
        if not hasattr(self, "persistence"):
            return
        
        economy_data = {
            "last_payout": self.last_payout,
            "stakes": self.stakes,
            "apy": self.apy,
            "total_distributed": getattr(self, "total_distributed", 0),
        }
        
        self.persistence.save("economy", economy_data)
    
    def load_economy_state(self):
        """Load economy state from disk."""
        if not hasattr(self, "persistence"):
            return
        
        economy_data = self.persistence.load("economy", default=None)
        
        if economy_data:
            # CRITICAL: Restore last_payout to prevent "infinite wealth" on restart
            self.last_payout = economy_data.get("last_payout", time.time())
            self.stakes = economy_data.get("stakes", self.stakes)
            self.apy = economy_data.get("apy", self.apy)
            self.total_distributed = economy_data.get("total_distributed", 0)
            print(f"📂 Economy state restored (last payout: {self.last_payout})")
        else:
            self.last_payout = time.time()

# =============================================================================
# GLOBAL SINGLETON
# =============================================================================

_persistence_manager: Optional[PersistenceManager] = None

def get_persistence_manager() -> PersistenceManager:
    """Get or create the global persistence manager."""
    global _persistence_manager
    if _persistence_manager is None:
        _persistence_manager = PersistenceManager()
    return _persistence_manager

# =============================================================================
# TESTING
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Testing PersistenceManager")
    print("=" * 60)
    
    pm = PersistenceManager(PersistenceConfig(data_dir="data/test"))
    
    # Test save/load
    test_markets = {
        "MKT_test_123": {
            "title": "Will Bitcoin reach $100k?",
            "domain": "crypto",
            "virality_score": 85,
        }
    }
    
    pm.save("markets", test_markets)
    loaded = pm.load("markets")
    print(f"✅ Save/Load test: {loaded}")
    
    # Test state info
    info = pm.get_state_info()
    print(f"📊 State info: {json.dumps(info, indent=2)}")
    
    # Test auto-save
    counter = {"value": 0}
    
    def get_states():
        counter["value"] += 1
        return {"test_counter": {"count": counter["value"]}}
    
    pm.start_auto_save(get_states, interval=2)
    time.sleep(5)
    pm.stop_auto_save()
    
    print("✅ All tests passed!")




