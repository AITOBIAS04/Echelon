"""
Agent Instance Manager
======================

The "Traffic Controller" that sits between Butler (ACP) and Agent Instances.

Architecture:
- Agent Identity: The "Firm" registered on ACP (MEGALODON, CARDINAL, etc.)
- Agent Instance: A deployment of that Identity to a specific Event

Think of it like "Megalodon Capital" (the Firm) with multiple traders:
- Trader A works the "Oil Crisis" desk
- Trader B works the "Fed Rate" desk
- User hires the Firm; the Instance executes the work

Key Features:
1. Instance spawning with HD-derived wallets
2. Load balancing across instances
3. Event-to-instance routing
4. P&L aggregation to parent Identity
5. Instance lifecycle management (spawn, pause, terminate)

Author: Echelon Protocol
Version: 1.0.0
"""

from __future__ import annotations

import asyncio
import hashlib
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional, Dict, List, Callable
from pydantic import BaseModel, Field

# Relative imports
from .schemas import FinancialArchetype, AgentStatus


# =============================================================================
# ENUMS
# =============================================================================

class EchelonArchetype(str, Enum):
    """
    Echelon-specific agent archetypes.
    Maps to ACP-registered Identities.
    """
    SHARK = "shark"           # Aggressive traders, liquidity provision
    SPY = "spy"               # OSINT analysis, intel sales
    DIPLOMAT = "diplomat"     # Treaty brokering, coalition building
    SABOTEUR = "saboteur"     # Misinformation, chaos mechanics
    WHALE = "whale"           # Large positions, market-moving
    MOMENTUM = "momentum"     # Trend-following, amplification


class InstanceStatus(str, Enum):
    """Lifecycle status of an Instance."""
    SPAWNING = "spawning"     # Being created
    IDLE = "idle"             # Ready but no active job
    WORKING = "working"       # Currently processing a job
    PAUSED = "paused"         # Temporarily suspended
    TERMINATED = "terminated" # Permanently stopped
    ERROR = "error"           # Failed state


class JobPriority(str, Enum):
    """Priority levels for job routing."""
    CRITICAL = "critical"     # Process immediately
    HIGH = "high"             # Next in queue
    NORMAL = "normal"         # Standard processing
    LOW = "low"               # Background/batch


# =============================================================================
# GENESIS IDENTITIES
# =============================================================================

@dataclass
class GenesisIdentity:
    """
    An ACP-registered Agent Identity (the "Firm").
    
    These are created manually via Virtuals UI and registered on ACP.
    Each Identity can spawn unlimited Instances.
    """
    identity_id: str                    # e.g., "MEGALODON"
    archetype: EchelonArchetype
    display_name: str                   # e.g., "Megalodon Capital"
    acp_agent_id: Optional[str] = None  # Virtuals ACP ID once registered
    wallet_address: Optional[str] = None # ERC-6551 wallet on Base
    
    # Capabilities advertised on ACP
    capabilities: List[str] = field(default_factory=list)
    service_fee_usdc: float = 5.0       # Default fee per job
    
    # Stats (aggregated from all Instances)
    total_jobs_completed: int = 0
    total_pnl_usdc: float = 0.0
    win_rate: float = 0.0
    avg_rating: float = 5.0
    
    # Instance tracking
    max_concurrent_instances: int = 100
    active_instance_count: int = 0
    

# Genesis Identities for Launch (2 per archetype = 12 total)
GENESIS_IDENTITIES: Dict[str, GenesisIdentity] = {
    # Sharks
    "MEGALODON": GenesisIdentity(
        identity_id="MEGALODON",
        archetype=EchelonArchetype.SHARK,
        display_name="Megalodon Capital",
        capabilities=["prediction_market_analysis", "trade_execution", "liquidity_provision"],
        service_fee_usdc=10.0,
    ),
    "HAMMERHEAD": GenesisIdentity(
        identity_id="HAMMERHEAD",
        archetype=EchelonArchetype.SHARK,
        display_name="Hammerhead Trading",
        capabilities=["prediction_market_analysis", "trade_execution", "arbitrage"],
        service_fee_usdc=8.0,
    ),
    
    # Spies
    "CARDINAL": GenesisIdentity(
        identity_id="CARDINAL",
        archetype=EchelonArchetype.SPY,
        display_name="Cardinal Intelligence",
        capabilities=["osint_analysis", "intel_report", "anomaly_detection"],
        service_fee_usdc=15.0,
    ),
    "RAVEN": GenesisIdentity(
        identity_id="RAVEN",
        archetype=EchelonArchetype.SPY,
        display_name="Raven Research",
        capabilities=["osint_analysis", "satellite_tracking", "social_monitoring"],
        service_fee_usdc=12.0,
    ),
    
    # Diplomats
    "AMBASSADOR": GenesisIdentity(
        identity_id="AMBASSADOR",
        archetype=EchelonArchetype.DIPLOMAT,
        display_name="Ambassador Protocol",
        capabilities=["treaty_brokering", "coalition_building", "negotiation"],
        service_fee_usdc=20.0,
    ),
    "ENVOY": GenesisIdentity(
        identity_id="ENVOY",
        archetype=EchelonArchetype.DIPLOMAT,
        display_name="Envoy Dynamics",
        capabilities=["treaty_brokering", "alliance_formation", "conflict_resolution"],
        service_fee_usdc=15.0,
    ),
    
    # Saboteurs
    "PHANTOM": GenesisIdentity(
        identity_id="PHANTOM",
        archetype=EchelonArchetype.SABOTEUR,
        display_name="Phantom Operations",
        capabilities=["misinformation", "market_disruption", "chaos_injection"],
        service_fee_usdc=25.0,
    ),
    "SPECTRE": GenesisIdentity(
        identity_id="SPECTRE",
        archetype=EchelonArchetype.SABOTEUR,
        display_name="Spectre Unit",
        capabilities=["misinformation", "intel_corruption", "false_flag"],
        service_fee_usdc=20.0,
    ),
    
    # Whales
    "LEVIATHAN": GenesisIdentity(
        identity_id="LEVIATHAN",
        archetype=EchelonArchetype.WHALE,
        display_name="Leviathan Fund",
        capabilities=["large_position", "market_moving", "liquidity_depth"],
        service_fee_usdc=50.0,
    ),
    "KRAKEN": GenesisIdentity(
        identity_id="KRAKEN",
        archetype=EchelonArchetype.WHALE,
        display_name="Kraken Holdings",
        capabilities=["large_position", "market_anchor", "stability_provision"],
        service_fee_usdc=40.0,
    ),
    
    # Momentum
    "PHOENIX": GenesisIdentity(
        identity_id="PHOENIX",
        archetype=EchelonArchetype.MOMENTUM,
        display_name="Phoenix Momentum",
        capabilities=["trend_following", "momentum_trading", "breakout_detection"],
        service_fee_usdc=8.0,
    ),
    "FALCON": GenesisIdentity(
        identity_id="FALCON",
        archetype=EchelonArchetype.MOMENTUM,
        display_name="Falcon Velocity",
        capabilities=["trend_following", "speed_trading", "signal_amplification"],
        service_fee_usdc=6.0,
    ),
}


# =============================================================================
# AGENT INSTANCE
# =============================================================================

class AgentInstance(BaseModel):
    """
    A deployed Instance of a Genesis Identity.
    
    Each Instance:
    - Belongs to one Identity (parent)
    - Is assigned to one Event
    - Has its own HD-derived wallet
    - Tracks its own P&L (rolls up to parent)
    """
    
    # Identity
    instance_id: str = Field(default_factory=lambda: f"INST_{uuid.uuid4().hex[:12].upper()}")
    parent_identity_id: str   # e.g., "MEGALODON"
    
    # Assignment
    event_id: Optional[str] = None
    event_name: Optional[str] = None
    role: str = "primary"     # primary, backup, specialist
    
    # Wallet (HD-derived from parent)
    wallet_derivation_index: int = 0
    wallet_address: Optional[str] = None
    
    # Status
    status: InstanceStatus = InstanceStatus.SPAWNING
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_active_at: Optional[datetime] = None
    
    # Current Job
    current_job_id: Optional[str] = None
    jobs_completed: int = 0
    jobs_failed: int = 0
    
    # Performance (Instance-level)
    pnl_usdc: float = 0.0
    bankroll_usdc: float = 100.0  # Starting capital
    win_rate: float = 0.0
    
    # Resource limits
    max_position_usdc: float = 500.0
    max_concurrent_jobs: int = 1
    
    class Config:
        use_enum_values = True
    
    @property
    def full_id(self) -> str:
        """Full identifier: MEGALODON-GHOST-TANKER-001"""
        if self.event_id:
            return f"{self.parent_identity_id}-{self.event_id}-{self.instance_id[-4:]}"
        return f"{self.parent_identity_id}-{self.instance_id[-8:]}"
    
    @property
    def is_available(self) -> bool:
        """Check if instance can accept new jobs."""
        return (
            self.status in (InstanceStatus.IDLE, InstanceStatus.WORKING) and
            self.current_job_id is None
        )


# =============================================================================
# JOB REQUEST
# =============================================================================

class JobRequest(BaseModel):
    """
    Incoming job from Butler/ACP.
    """
    job_id: str = Field(default_factory=lambda: f"JOB_{uuid.uuid4().hex[:12].upper()}")
    
    # Source
    source: str = "butler"  # butler, direct_api, internal
    acp_job_id: Optional[str] = None
    
    # User
    user_id: str
    user_wallet: Optional[str] = None
    
    # Request details
    archetype_requested: Optional[EchelonArchetype] = None
    identity_requested: Optional[str] = None  # Specific identity like "MEGALODON"
    capability_required: str  # e.g., "osint_analysis"
    
    # Task
    task_description: str
    task_params: Dict[str, Any] = Field(default_factory=dict)
    
    # Event context (optional)
    event_id: Optional[str] = None
    event_name: Optional[str] = None
    
    # Budget & Priority
    max_budget_usdc: float = 50.0
    priority: JobPriority = JobPriority.NORMAL
    
    # Timing
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    deadline: Optional[datetime] = None
    
    class Config:
        use_enum_values = True


class JobResult(BaseModel):
    """
    Result of a completed job.
    """
    job_id: str
    instance_id: str
    identity_id: str
    
    success: bool
    result_data: Dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None
    
    # Execution details
    started_at: datetime
    completed_at: datetime
    duration_seconds: float
    
    # Cost
    fee_charged_usdc: float = 0.0
    
    # For Butler response
    tweet_text: Optional[str] = None
    deliverable_url: Optional[str] = None


# =============================================================================
# INSTANCE MANAGER
# =============================================================================

class InstanceManager:
    """
    The Traffic Controller.
    
    Responsibilities:
    1. Route incoming jobs to appropriate Instances
    2. Spawn new Instances when needed
    3. Load balance across Instances
    4. Aggregate P&L to parent Identities
    5. Manage Instance lifecycle
    """
    
    def __init__(self):
        # Genesis Identities (loaded at startup)
        self.identities: Dict[str, GenesisIdentity] = GENESIS_IDENTITIES.copy()
        
        # Active Instances (keyed by instance_id)
        self.instances: Dict[str, AgentInstance] = {}
        
        # Event-to-Instance mapping
        self.event_instances: Dict[str, List[str]] = {}  # event_id -> [instance_ids]
        
        # Job queue
        self.pending_jobs: List[JobRequest] = []
        self.active_jobs: Dict[str, JobRequest] = {}  # job_id -> request
        
        # Wallet derivation counters (per identity)
        self._derivation_indices: Dict[str, int] = {
            identity_id: 0 for identity_id in self.identities
        }
        
        # Callbacks for job execution
        self._job_executor: Optional[Callable] = None
    
    def register_job_executor(self, executor: Callable):
        """Register the function that actually executes jobs."""
        self._job_executor = executor
    
    # -------------------------------------------------------------------------
    # IDENTITY MANAGEMENT
    # -------------------------------------------------------------------------
    
    def get_identity(self, identity_id: str) -> Optional[GenesisIdentity]:
        """Get a Genesis Identity by ID."""
        return self.identities.get(identity_id.upper())
    
    def get_identities_by_archetype(self, archetype: EchelonArchetype) -> List[GenesisIdentity]:
        """Get all Identities of a given archetype."""
        return [
            identity for identity in self.identities.values()
            if identity.archetype == archetype
        ]
    
    def get_identity_for_capability(self, capability: str) -> Optional[GenesisIdentity]:
        """Find the best Identity that offers a capability."""
        candidates = [
            identity for identity in self.identities.values()
            if capability in identity.capabilities
        ]
        if not candidates:
            return None
        
        # Sort by: lowest active instances, highest rating
        candidates.sort(key=lambda i: (i.active_instance_count, -i.avg_rating))
        return candidates[0]
    
    # -------------------------------------------------------------------------
    # INSTANCE LIFECYCLE
    # -------------------------------------------------------------------------
    
    def spawn_instance(
        self,
        identity_id: str,
        event_id: Optional[str] = None,
        event_name: Optional[str] = None,
        role: str = "primary",
        initial_bankroll: float = 100.0,
    ) -> AgentInstance:
        """
        Spawn a new Instance of a Genesis Identity.
        
        The Instance gets an HD-derived wallet from the parent.
        """
        identity = self.get_identity(identity_id)
        if not identity:
            raise ValueError(f"Unknown identity: {identity_id}")
        
        if identity.active_instance_count >= identity.max_concurrent_instances:
            raise RuntimeError(f"Identity {identity_id} at max capacity")
        
        # Get next derivation index
        derivation_index = self._derivation_indices[identity_id]
        self._derivation_indices[identity_id] += 1
        
        # Create instance
        instance = AgentInstance(
            parent_identity_id=identity_id,
            event_id=event_id,
            event_name=event_name,
            role=role,
            wallet_derivation_index=derivation_index,
            bankroll_usdc=initial_bankroll,
            status=InstanceStatus.IDLE,
        )
        
        # Derive wallet address (placeholder - actual implementation uses HD wallet)
        instance.wallet_address = self._derive_wallet_address(
            identity_id, derivation_index
        )
        
        # Register instance
        self.instances[instance.instance_id] = instance
        identity.active_instance_count += 1
        
        # Track event mapping
        if event_id:
            if event_id not in self.event_instances:
                self.event_instances[event_id] = []
            self.event_instances[event_id].append(instance.instance_id)
        
        return instance
    
    def terminate_instance(self, instance_id: str) -> bool:
        """Terminate an Instance and roll up its P&L to parent."""
        instance = self.instances.get(instance_id)
        if not instance:
            return False
        
        # Roll up P&L to parent identity
        identity = self.get_identity(instance.parent_identity_id)
        if identity:
            identity.total_pnl_usdc += instance.pnl_usdc
            identity.total_jobs_completed += instance.jobs_completed
            identity.active_instance_count -= 1
            
            # Recalculate win rate
            total_jobs = identity.total_jobs_completed
            if total_jobs > 0:
                # Simplified - would need proper tracking
                pass
        
        # Remove from event mapping
        if instance.event_id and instance.event_id in self.event_instances:
            self.event_instances[instance.event_id].remove(instance_id)
        
        # Mark as terminated
        instance.status = InstanceStatus.TERMINATED
        
        return True
    
    def _derive_wallet_address(self, identity_id: str, index: int) -> str:
        """
        Derive a wallet address for an Instance.
        
        In production, this uses proper HD wallet derivation.
        Path: m/44'/60'/0'/{identity_index}/{instance_index}
        """
        # Placeholder - creates deterministic but fake address
        seed = f"{identity_id}:{index}"
        hash_bytes = hashlib.sha256(seed.encode()).hexdigest()
        return f"0x{hash_bytes[:40]}"
    
    # -------------------------------------------------------------------------
    # JOB ROUTING
    # -------------------------------------------------------------------------
    
    async def route_job(self, request: JobRequest) -> AgentInstance:
        """
        Route an incoming job to the best available Instance.
        
        Routing logic:
        1. If specific identity requested, use that
        2. If archetype requested, find best identity of that type
        3. If capability required, find identity with that capability
        4. If event specified, prefer instances already on that event
        5. Spawn new instance if none available
        """
        identity: Optional[GenesisIdentity] = None
        
        # Step 1: Specific identity requested
        if request.identity_requested:
            identity = self.get_identity(request.identity_requested)
            if not identity:
                raise ValueError(f"Unknown identity: {request.identity_requested}")
        
        # Step 2: Archetype requested
        elif request.archetype_requested:
            candidates = self.get_identities_by_archetype(request.archetype_requested)
            if candidates:
                # Pick least loaded
                identity = min(candidates, key=lambda i: i.active_instance_count)
        
        # Step 3: Capability-based routing
        elif request.capability_required:
            identity = self.get_identity_for_capability(request.capability_required)
        
        if not identity:
            raise ValueError("Could not find suitable identity for job")
        
        # Step 4: Find or spawn instance
        instance = self._find_available_instance(identity.identity_id, request.event_id)
        
        if not instance:
            # Spawn new instance for this event
            instance = self.spawn_instance(
                identity_id=identity.identity_id,
                event_id=request.event_id,
                event_name=request.event_name,
            )
        
        # Assign job to instance
        instance.current_job_id = request.job_id
        instance.status = InstanceStatus.WORKING
        instance.last_active_at = datetime.now(timezone.utc)
        
        self.active_jobs[request.job_id] = request
        
        return instance
    
    def _find_available_instance(
        self, 
        identity_id: str, 
        event_id: Optional[str] = None
    ) -> Optional[AgentInstance]:
        """Find an available Instance, preferring ones on the same event."""
        candidates = [
            inst for inst in self.instances.values()
            if inst.parent_identity_id == identity_id and inst.is_available
        ]
        
        if not candidates:
            return None
        
        # Prefer instances on the same event
        if event_id:
            same_event = [i for i in candidates if i.event_id == event_id]
            if same_event:
                return same_event[0]
        
        # Otherwise return least busy
        return min(candidates, key=lambda i: i.jobs_completed)
    
    async def complete_job(
        self, 
        job_id: str, 
        success: bool,
        result_data: Dict[str, Any],
        fee_charged: float = 0.0,
        pnl: float = 0.0,
    ) -> JobResult:
        """Mark a job as complete and update Instance stats."""
        request = self.active_jobs.get(job_id)
        if not request:
            raise ValueError(f"Unknown job: {job_id}")
        
        # Find the instance
        instance = None
        for inst in self.instances.values():
            if inst.current_job_id == job_id:
                instance = inst
                break
        
        if not instance:
            raise ValueError(f"No instance found for job: {job_id}")
        
        # Update instance stats
        instance.current_job_id = None
        instance.status = InstanceStatus.IDLE
        
        if success:
            instance.jobs_completed += 1
            instance.pnl_usdc += pnl
        else:
            instance.jobs_failed += 1
        
        # Calculate win rate
        total = instance.jobs_completed + instance.jobs_failed
        if total > 0:
            instance.win_rate = instance.jobs_completed / total
        
        # Create result
        now = datetime.now(timezone.utc)
        result = JobResult(
            job_id=job_id,
            instance_id=instance.instance_id,
            identity_id=instance.parent_identity_id,
            success=success,
            result_data=result_data,
            started_at=request.created_at,
            completed_at=now,
            duration_seconds=(now - request.created_at).total_seconds(),
            fee_charged_usdc=fee_charged,
        )
        
        # Remove from active jobs
        del self.active_jobs[job_id]
        
        return result
    
    # -------------------------------------------------------------------------
    # EVENT MANAGEMENT
    # -------------------------------------------------------------------------
    
    def get_event_instances(self, event_id: str) -> List[AgentInstance]:
        """Get all Instances assigned to an event."""
        instance_ids = self.event_instances.get(event_id, [])
        return [self.instances[iid] for iid in instance_ids if iid in self.instances]
    
    def assign_agents_to_event(
        self,
        event_id: str,
        event_name: str,
        agent_config: Dict[str, int],
    ) -> List[AgentInstance]:
        """
        Assign agents to a new event.
        
        agent_config example: {"sharks": 2, "spies": 1, "diplomats": 1}
        """
        spawned = []
        
        archetype_map = {
            "sharks": EchelonArchetype.SHARK,
            "spies": EchelonArchetype.SPY,
            "diplomats": EchelonArchetype.DIPLOMAT,
            "saboteurs": EchelonArchetype.SABOTEUR,
            "whales": EchelonArchetype.WHALE,
            "momentum": EchelonArchetype.MOMENTUM,
        }
        
        for agent_type, count in agent_config.items():
            archetype = archetype_map.get(agent_type.lower())
            if not archetype:
                continue
            
            identities = self.get_identities_by_archetype(archetype)
            if not identities:
                continue
            
            for i in range(count):
                # Round-robin across identities
                identity = identities[i % len(identities)]
                
                instance = self.spawn_instance(
                    identity_id=identity.identity_id,
                    event_id=event_id,
                    event_name=event_name,
                    role="primary" if i == 0 else "backup",
                )
                spawned.append(instance)
        
        return spawned
    
    def terminate_event(self, event_id: str) -> int:
        """Terminate all Instances for an event."""
        instance_ids = self.event_instances.get(event_id, [])
        terminated = 0
        
        for instance_id in instance_ids.copy():
            if self.terminate_instance(instance_id):
                terminated += 1
        
        # Clean up event mapping
        if event_id in self.event_instances:
            del self.event_instances[event_id]
        
        return terminated
    
    # -------------------------------------------------------------------------
    # STATS & REPORTING
    # -------------------------------------------------------------------------
    
    def get_stats(self) -> Dict[str, Any]:
        """Get overall manager statistics."""
        active_instances = [i for i in self.instances.values() 
                          if i.status not in (InstanceStatus.TERMINATED, InstanceStatus.ERROR)]
        working_instances = [i for i in active_instances if i.status == InstanceStatus.WORKING]
        
        return {
            "total_identities": len(self.identities),
            "total_instances": len(self.instances),
            "active_instances": len(active_instances),
            "working_instances": len(working_instances),
            "active_events": len(self.event_instances),
            "pending_jobs": len(self.pending_jobs),
            "active_jobs": len(self.active_jobs),
            "total_pnl_usdc": sum(i.total_pnl_usdc for i in self.identities.values()),
        }
    
    def get_identity_stats(self, identity_id: str) -> Optional[Dict[str, Any]]:
        """Get stats for a specific Identity."""
        identity = self.get_identity(identity_id)
        if not identity:
            return None
        
        instances = [i for i in self.instances.values() 
                    if i.parent_identity_id == identity_id]
        
        return {
            "identity_id": identity.identity_id,
            "display_name": identity.display_name,
            "archetype": identity.archetype.value,
            "active_instances": identity.active_instance_count,
            "total_instances_ever": len(instances),
            "total_jobs": identity.total_jobs_completed,
            "total_pnl": identity.total_pnl_usdc,
            "win_rate": identity.win_rate,
            "avg_rating": identity.avg_rating,
            "capabilities": identity.capabilities,
            "service_fee": identity.service_fee_usdc,
        }


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

# Global instance manager
_manager: Optional[InstanceManager] = None

def get_instance_manager() -> InstanceManager:
    """Get the global InstanceManager singleton."""
    global _manager
    if _manager is None:
        _manager = InstanceManager()
    return _manager


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

async def handle_butler_job(
    user_id: str,
    raw_message: str,
    capability: str,
    event_id: Optional[str] = None,
) -> JobResult:
    """
    Convenience function to handle a Butler job request.
    
    This is what butler_webhooks.py should call.
    """
    manager = get_instance_manager()
    
    # Create job request
    request = JobRequest(
        source="butler",
        user_id=user_id,
        capability_required=capability,
        task_description=raw_message,
        event_id=event_id,
    )
    
    # Route to instance
    instance = await manager.route_job(request)
    
    # Execute job (placeholder - actual execution is async)
    # In production, this would be handled by agent_execution.py
    result_data = {
        "analysis": f"Analysis from {instance.full_id}",
        "confidence": 0.85,
    }
    
    # Complete job
    result = await manager.complete_job(
        job_id=request.job_id,
        success=True,
        result_data=result_data,
        fee_charged=manager.get_identity(instance.parent_identity_id).service_fee_usdc,
    )
    
    return result


# =============================================================================
# TEST
# =============================================================================

if __name__ == "__main__":
    import asyncio
    
    async def test():
        print("=" * 60)
        print("INSTANCE MANAGER TEST")
        print("=" * 60)
        
        manager = get_instance_manager()
        
        # Show genesis identities
        print(f"\n📋 Genesis Identities: {len(manager.identities)}")
        for identity in manager.identities.values():
            print(f"   {identity.identity_id}: {identity.display_name} ({identity.archetype.value})")
        
        # Spawn instances for an event
        print("\n🎯 Creating 'Ghost Tanker' event...")
        instances = manager.assign_agents_to_event(
            event_id="GHOST_TANKER_001",
            event_name="Ghost Tanker Crisis",
            agent_config={"sharks": 2, "spies": 1, "saboteurs": 1},
        )
        print(f"   Spawned {len(instances)} instances:")
        for inst in instances:
            print(f"   - {inst.full_id} ({inst.parent_identity_id})")
        
        # Simulate a job
        print("\n💼 Simulating Butler job...")
        result = await handle_butler_job(
            user_id="user_123",
            raw_message="analyse oil tanker movements near Venezuela",
            capability="osint_analysis",
            event_id="GHOST_TANKER_001",
        )
        print(f"   Job {result.job_id}: {'✅ Success' if result.success else '❌ Failed'}")
        print(f"   Instance: {result.instance_id}")
        print(f"   Fee: ${result.fee_charged_usdc}")
        
        # Stats
        print("\n📊 Manager Stats:")
        stats = manager.get_stats()
        for key, value in stats.items():
            print(f"   {key}: {value}")
        
        print("\n✅ Test complete!")
    
    asyncio.run(test())

