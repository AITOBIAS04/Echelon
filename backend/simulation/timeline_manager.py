"""
Timeline Manager for Project Seed
==================================
Git-like version control for simulation state.

Enables "Snapshot & Fork" counterfactual simulation:
- Take snapshots of reality at key moments
- Fork into divergent timelines
- Run parallel "what-if" scenarios
- Track lineage of simulations

Usage:
    from backend.simulation.timeline_manager import TimelineManager
    
    tm = TimelineManager()
    
    # Snapshot current state
    snap_id = tm.create_snapshot("PRE_EARNINGS_Q1")
    
    # Fork into alternative timelines
    bull_fork = tm.fork_timeline(snap_id, "BULL_CASE")
    bear_fork = tm.fork_timeline(snap_id, "BEAR_CASE")
    
    # Run simulations on each fork independently
"""

import os
import sys
import json
import shutil
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum

# Path setup
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SNAPSHOTS_DIR = os.path.join(BASE_DIR, "../../data/snapshots")
WORLD_STATE_FILE = os.path.join(BASE_DIR, "world_state.json")




class TimelineStatus(str, Enum):
    """Status of a timeline."""
    ACTIVE = "active"          # Currently running
    COMPLETED = "completed"    # Simulation finished
    ARCHIVED = "archived"      # Stored for reference
    MASTER = "master"          # The "reality" branch




@dataclass
class TimelineMetadata:
    """Metadata for a snapshot or fork."""
    id: str
    label: str
    status: TimelineStatus
    created_at: str
    parent_id: Optional[str] = None  # For forks
    fork_reason: Optional[str] = None
    matchday: Optional[int] = None   # For sports
    tick: Optional[int] = None       # For markets
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'TimelineMetadata':
        data['status'] = TimelineStatus(data['status'])
        return cls(**data)




class TimelineManager:
    """
    Manages simulation timelines with Git-like branching.
    
    Architecture:
    - MASTER: The "reality" timeline fed by live APIs
    - Snapshots: Frozen states at specific moments
    - Forks: Divergent simulations from snapshots
    """
    
    def __init__(self, snapshots_dir: str = None):
        self.snapshots_dir = snapshots_dir or SNAPSHOTS_DIR
        os.makedirs(self.snapshots_dir, exist_ok=True)
        
        # Track active timelines
        self.master_id = "REALITY"
        self.active_forks: List[str] = []
        
        # Load existing timeline index
        self.index_file = os.path.join(self.snapshots_dir, "timeline_index.json")
        self.index: Dict[str, TimelineMetadata] = self._load_index()
    
    def _load_index(self) -> Dict[str, TimelineMetadata]:
        """Load timeline index from disk."""
        if os.path.exists(self.index_file):
            try:
                with open(self.index_file, 'r') as f:
                    data = json.load(f)
                return {
                    k: TimelineMetadata.from_dict(v) 
                    for k, v in data.items()
                }
            except Exception as e:
                print(f"⚠️ Could not load timeline index: {e}")
        return {}
    
    def _save_index(self) -> None:
        """Save timeline index to disk."""
        with open(self.index_file, 'w') as f:
            json.dump(
                {k: v.to_dict() for k, v in self.index.items()},
                f, indent=2
            )
    
    def create_snapshot(self, label: str, 
                        additional_files: Dict[str, str] = None) -> str:
        """
        Capture current state and save it.
        
        Args:
            label: Human-readable label (e.g., "PRE_EARNINGS_Q1")
            additional_files: Dict of {filename: filepath} to include
            
        Returns:
            Snapshot ID
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        snapshot_id = f"{label}_{timestamp}"
        
        # Create snapshot directory
        snapshot_path = os.path.join(self.snapshots_dir, snapshot_id)
        os.makedirs(snapshot_path, exist_ok=True)
        
        # 1. Save World State (if exists)
        if os.path.exists(WORLD_STATE_FILE):
            shutil.copy2(
                WORLD_STATE_FILE, 
                os.path.join(snapshot_path, "world_state.json")
            )
        
        # 2. Save additional files (market state, football state, etc.)
        if additional_files:
            for filename, filepath in additional_files.items():
                if os.path.exists(filepath):
                    shutil.copy2(filepath, os.path.join(snapshot_path, filename))
        
        # 3. Create metadata
        metadata = TimelineMetadata(
            id=snapshot_id,
            label=label,
            status=TimelineStatus.ARCHIVED,
            created_at=datetime.now().isoformat(),
        )
        
        # Save metadata in snapshot folder
        with open(os.path.join(snapshot_path, "metadata.json"), 'w') as f:
            json.dump(metadata.to_dict(), f, indent=2)
        
        # Update index
        self.index[snapshot_id] = metadata
        self._save_index()
        
        print(f"📸 SNAPSHOT CREATED: {snapshot_id}")
        return snapshot_id
    
    def fork_timeline(self, source_id: str, fork_name: str,
                      reason: str = None) -> str:
        """
        Create a divergent timeline from a snapshot.
        
        Args:
            source_id: ID of the snapshot to fork from
            fork_name: Name for the new fork
            reason: Why this fork was created
            
        Returns:
            Fork ID
        """
        source_path = os.path.join(self.snapshots_dir, source_id)
        if not os.path.exists(source_path):
            raise ValueError(f"Snapshot '{source_id}' not found")
        
        # Create fork ID
        timestamp = datetime.now().strftime("%H%M%S")
        fork_id = f"FORK_{fork_name}_{timestamp}"
        fork_path = os.path.join(self.snapshots_dir, fork_id)
        
        # Copy snapshot data (Copy-on-Write - we duplicate the starting point)
        shutil.copytree(source_path, fork_path)
        
        # Update metadata
        metadata = TimelineMetadata(
            id=fork_id,
            label=fork_name,
            status=TimelineStatus.ACTIVE,
            created_at=datetime.now().isoformat(),
            parent_id=source_id,
            fork_reason=reason,
        )
        
        with open(os.path.join(fork_path, "metadata.json"), 'w') as f:
            json.dump(metadata.to_dict(), f, indent=2)
        
        # Update index
        self.index[fork_id] = metadata
        self.active_forks.append(fork_id)
        self._save_index()
        
        print(f"🔀 FORKED: {source_id} → {fork_id}")
        if reason:
            print(f"   Reason: {reason}")
        
        return fork_id
    
    def get_timeline_path(self, timeline_id: str) -> str:
        """Get the filesystem path for a timeline."""
        return os.path.join(self.snapshots_dir, timeline_id)
    
    def load_state(self, timeline_id: str, filename: str = "world_state.json") -> Dict:
        """Load a specific state file from a timeline."""
        filepath = os.path.join(self.snapshots_dir, timeline_id, filename)
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"State file not found: {filepath}")
        
        with open(filepath, 'r') as f:
            return json.load(f)
    
    def save_state(self, timeline_id: str, filename: str, data: Dict) -> None:
        """Save state to a specific timeline."""
        timeline_path = os.path.join(self.snapshots_dir, timeline_id)
        os.makedirs(timeline_path, exist_ok=True)
        
        filepath = os.path.join(timeline_path, filename)
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    
    def complete_timeline(self, timeline_id: str, result: Dict = None) -> None:
        """Mark a timeline as completed."""
        if timeline_id not in self.index:
            return
        
        self.index[timeline_id].status = TimelineStatus.COMPLETED
        
        # Save result if provided
        if result:
            self.save_state(timeline_id, "final_result.json", result)
        
        if timeline_id in self.active_forks:
            self.active_forks.remove(timeline_id)
        
        self._save_index()
        print(f"✅ TIMELINE COMPLETED: {timeline_id}")
    
    def get_latest_snapshot(self, label_filter: str = None) -> Optional[str]:
        """Get the most recent snapshot, optionally filtered by label."""
        matching = [
            (id, meta) for id, meta in self.index.items()
            if meta.status in [TimelineStatus.ARCHIVED, TimelineStatus.COMPLETED]
            and (label_filter is None or label_filter in meta.label)
        ]
        
        if not matching:
            return None
        
        # Sort by creation time
        matching.sort(key=lambda x: x[1].created_at, reverse=True)
        return matching[0][0]
    
    def list_timelines(self, status: TimelineStatus = None) -> List[TimelineMetadata]:
        """List all timelines, optionally filtered by status."""
        timelines = list(self.index.values())
        
        if status:
            timelines = [t for t in timelines if t.status == status]
        
        return sorted(timelines, key=lambda t: t.created_at, reverse=True)
    
    def get_lineage(self, timeline_id: str) -> List[str]:
        """Get the ancestry of a timeline (parent chain)."""
        lineage = [timeline_id]
        
        current = self.index.get(timeline_id)
        while current and current.parent_id:
            lineage.append(current.parent_id)
            current = self.index.get(current.parent_id)
        
        return lineage
    
    def cleanup_old_forks(self, max_age_days: int = 7) -> int:
        """Remove old completed forks to save space."""
        from datetime import timedelta
        
        cutoff = datetime.now() - timedelta(days=max_age_days)
        removed = 0
        
        for timeline_id, meta in list(self.index.items()):
            if meta.status == TimelineStatus.COMPLETED:
                created = datetime.fromisoformat(meta.created_at)
                if created < cutoff:
                    # Remove from disk
                    timeline_path = os.path.join(self.snapshots_dir, timeline_id)
                    if os.path.exists(timeline_path):
                        shutil.rmtree(timeline_path)
                    
                    # Remove from index
                    del self.index[timeline_id]
                    removed += 1
        
        if removed > 0:
            self._save_index()
            print(f"🗑️ Cleaned up {removed} old timelines")
        
        return removed

    # Backward compatibility: alias for fork_reality
    def fork_reality(self, source_snapshot_id: str, fork_name: str) -> str:
        """Alias for fork_timeline for backward compatibility."""
        return self.fork_timeline(source_snapshot_id, fork_name)




# =============================================================================
# CLI
# =============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Timeline Manager")
    parser.add_argument("action", choices=["snapshot", "fork", "list", "cleanup"],
                        help="Action to perform")
    parser.add_argument("--label", "-l", help="Label for snapshot")
    parser.add_argument("--source", "-s", help="Source snapshot ID for fork")
    parser.add_argument("--name", "-n", help="Name for fork")
    parser.add_argument("--reason", "-r", help="Reason for fork")
    
    args = parser.parse_args()
    
    tm = TimelineManager()
    
    if args.action == "snapshot":
        if not args.label:
            args.label = f"MANUAL_{datetime.now().strftime('%Y%m%d')}"
        tm.create_snapshot(args.label)
    
    elif args.action == "fork":
        if not args.source:
            # Use latest snapshot
            args.source = tm.get_latest_snapshot()
            if not args.source:
                print("❌ No snapshots found. Create one first.")
                sys.exit(1)
        
        if not args.name:
            args.name = "MANUAL_FORK"
        
        tm.fork_timeline(args.source, args.name, args.reason)
    
    elif args.action == "list":
        timelines = tm.list_timelines()
        print(f"\n📚 Timelines ({len(timelines)} total):")
        for t in timelines[:10]:
            status_icon = {
                TimelineStatus.ACTIVE: "🟢",
                TimelineStatus.COMPLETED: "✅",
                TimelineStatus.ARCHIVED: "📦",
                TimelineStatus.MASTER: "👑",
            }.get(t.status, "❓")
            
            parent = f" (from {t.parent_id[:20]}...)" if t.parent_id else ""
            print(f"   {status_icon} {t.id}{parent}")
    
    elif args.action == "cleanup":
        tm.cleanup_old_forks()
