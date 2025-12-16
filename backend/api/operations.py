"""
Operations API
==============

REST API endpoints for the Situation Room and Butler integration.

Endpoints:
- GET  /api/operations           - List active operations
- GET  /api/operations/{id}      - Get operation details
- POST /api/operations/{id}/join - Join an operation
- GET  /api/agents               - List agents and their status
- GET  /api/agents/{id}          - Get agent details and P&L
- POST /api/agents/hire          - Hire an agent via ACP
- GET  /api/intel                - List available intel packages
- POST /api/intel/purchase       - Purchase intel via ACP
- GET  /api/timelines            - List active timelines
- POST /api/forks                - Create a timeline fork (Butler API)
- GET  /api/signals              - Get real-time signals feed
"""

from fastapi import APIRouter, HTTPException, Query, Depends, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta
from enum import Enum
import uuid
import random

router = APIRouter(prefix="/api", tags=["operations"])


# =============================================================================
# MODELS
# =============================================================================

class OperationStatus(str, Enum):
    BRIEFING = "briefing"
    ACTIVE = "active"
    RESOLVED = "resolved"
    CANCELLED = "cancelled"


class AgentArchetype(str, Enum):
    SHARK = "SHARK"
    SPY = "SPY"
    DIPLOMAT = "DIPLOMAT"
    SABOTEUR = "SABOTEUR"


class IntelSource(BaseModel):
    id: str
    name: str
    accuracy: float = Field(ge=0, le=1)
    cost: float = Field(ge=0)
    content: Optional[str] = None


class Operation(BaseModel):
    id: str
    codename: str
    description: str
    difficulty: int = Field(ge=0, le=100)
    time_remaining: int  # seconds
    expires_at: datetime
    intel_sources: List[IntelSource]
    related_markets: List[str]
    status: OperationStatus
    participants: int = 0
    total_volume: float = 0.0
    created_at: datetime


class Agent(BaseModel):
    agent_id: str
    archetype: AgentArchetype
    wallet: str
    bankroll: float
    pnl_total: float
    pnl_24h: float
    win_rate: float
    trades_count: int
    trust_score: float
    last_action: Optional[str]
    last_action_time: Optional[datetime]
    is_available: bool = True


class IntelPackage(BaseModel):
    id: str
    topic: str
    preview: str  # Encrypted/teaser
    price_usdc: float
    confidence: float
    source_agent: str
    created_at: datetime
    expires_at: Optional[datetime] = None


class TimelineFork(BaseModel):
    fork_id: str
    source_platform: str  # polymarket, kalshi
    source_market_id: str
    scenarios: List[Dict[str, Any]]
    agents_deployed: int
    status: str
    created_at: datetime
    expires_at: datetime
    share_url: str


class Signal(BaseModel):
    id: str
    timestamp: datetime
    signal_type: str
    agent_id: str
    agent_archetype: str
    message: str
    level: str  # info, success, warning, danger
    market_id: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


class TimelineHealth(BaseModel):
    timeline_id: str
    timeline_name: str
    status: str  # STABLE, DEGRADING, CRITICAL
    time_to_collapse: int  # seconds
    reality_alignment: float
    stability_index: float
    decay_rate: float
    sabotage_pressure: float
    shield_coverage: float
    net_momentum: str  # BULLISH, BEARISH, NEUTRAL


class MarketForce(BaseModel):
    market_id: str
    market_name: str
    sabotage_amount: float
    shield_amount: float
    current_price: float
    top_saboteurs: List[Dict[str, Any]]
    top_defenders: List[Dict[str, Any]]


# =============================================================================
# REQUEST MODELS
# =============================================================================

class JoinOperationRequest(BaseModel):
    wallet_address: str
    position_type: str  # YES, NO
    amount: float = Field(gt=0)


class HireAgentRequest(BaseModel):
    agent_id: str
    task_type: str
    task_params: Dict[str, Any]
    max_budget_usdc: float = Field(gt=0, le=1000)
    requester_wallet: str
    callback_url: Optional[str] = None


class PurchaseIntelRequest(BaseModel):
    intel_id: str
    requester_wallet: str


class CreateForkRequest(BaseModel):
    source_platform: str
    source_market_id: str
    scenarios: List[Dict[str, Any]]
    agent_config: Dict[str, int]
    duration_hours: int = Field(gt=0, le=168)
    requester_wallet: Optional[str] = None


# =============================================================================
# IN-MEMORY DATA STORE (Replace with database in production)
# =============================================================================

_operations: Dict[str, Operation] = {}
_agents: Dict[str, Agent] = {}
_intel_packages: Dict[str, IntelPackage] = {}
_forks: Dict[str, TimelineFork] = {}
_signals: List[Signal] = []


def _init_mock_data():
    """Initialise with mock data for development."""
    global _operations, _agents, _intel_packages, _signals
    
    now = datetime.now(timezone.utc)
    
    # Mock operations
    _operations = {
        "op-ghost-tanker": Operation(
            id="op-ghost-tanker",
            codename="GHOST TANKER",
            description="3 oil tankers went dark near Hormuz. Sanctions evasion or routine maintenance?",
            difficulty=72,
            time_remaining=14400,
            expires_at=now + timedelta(hours=4),
            intel_sources=[
                IntelSource(id="cardinal", name="CARDINAL", accuracy=0.85, cost=25),
                IntelSource(id="sentinel", name="SENTINEL", accuracy=0.72, cost=15),
                IntelSource(id="raven", name="RAVEN", accuracy=0.68, cost=10),
            ],
            related_markets=["tanker-china-48h", "oil-price-spike-7d"],
            status=OperationStatus.ACTIVE,
            participants=47,
            total_volume=12500.0,
            created_at=now - timedelta(hours=2)
        ),
        "op-silicon-acquisition": Operation(
            id="op-silicon-acquisition",
            codename="SILICON ACQUISITION",
            description="Apple posted 50+ AI roles in one week. Project Titan II confirmed?",
            difficulty=58,
            time_remaining=28800,
            expires_at=now + timedelta(hours=8),
            intel_sources=[
                IntelSource(id="phoenix", name="PHOENIX", accuracy=0.78, cost=20),
                IntelSource(id="cardinal", name="CARDINAL", accuracy=0.85, cost=25),
            ],
            related_markets=["apple-ai-announcement-30d", "nvidia-earnings-beat"],
            status=OperationStatus.BRIEFING,
            participants=23,
            total_volume=8200.0,
            created_at=now - timedelta(hours=1)
        ),
        "op-contagion-zero": Operation(
            id="op-contagion-zero",
            codename="CONTAGION ZERO",
            description="300% spike in 'unknown flu' mentions in Mumbai. Patient zero detected?",
            difficulty=85,
            time_remaining=7200,
            expires_at=now + timedelta(hours=2),
            intel_sources=[
                IntelSource(id="sentinel", name="SENTINEL", accuracy=0.72, cost=15),
                IntelSource(id="ghost", name="GHOST", accuracy=0.65, cost=8),
            ],
            related_markets=["who-emergency-declaration", "pharma-surge-7d"],
            status=OperationStatus.ACTIVE,
            participants=89,
            total_volume=31000.0,
            created_at=now - timedelta(hours=3)
        ),
    }
    
    # Mock agents
    _agents = {
        "HAMMERHEAD": Agent(
            agent_id="HAMMERHEAD",
            archetype=AgentArchetype.SHARK,
            wallet="0x1234...5678",
            bankroll=2500.0,
            pnl_total=1250.0,
            pnl_24h=145.0,
            win_rate=0.68,
            trades_count=156,
            trust_score=0.92,
            last_action="Accumulated YES @ 0.42 in Ghost Tanker",
            last_action_time=now - timedelta(minutes=15)
        ),
        "CARDINAL": Agent(
            agent_id="CARDINAL",
            archetype=AgentArchetype.SPY,
            wallet="0x2345...6789",
            bankroll=1800.0,
            pnl_total=890.0,
            pnl_24h=75.0,
            win_rate=0.74,
            trades_count=89,
            trust_score=0.95,
            last_action="Published intel on Hormuz shipping patterns",
            last_action_time=now - timedelta(minutes=8)
        ),
        "AMBASSADOR": Agent(
            agent_id="AMBASSADOR",
            archetype=AgentArchetype.DIPLOMAT,
            wallet="0x3456...7890",
            bankroll=3200.0,
            pnl_total=650.0,
            pnl_24h=-25.0,
            win_rate=0.61,
            trades_count=45,
            trust_score=0.88,
            last_action="Proposed coalition treaty on oil markets",
            last_action_time=now - timedelta(minutes=32)
        ),
        "PHANTOM": Agent(
            agent_id="PHANTOM",
            archetype=AgentArchetype.SABOTEUR,
            wallet="0x4567...8901",
            bankroll=950.0,
            pnl_total=-120.0,
            pnl_24h=-45.0,
            win_rate=0.42,
            trades_count=67,
            trust_score=0.35,
            last_action="Planted misinformation about tanker destination",
            last_action_time=now - timedelta(minutes=5)
        ),
    }
    
    # Mock intel packages
    _intel_packages = {
        "intel-001": IntelPackage(
            id="intel-001",
            topic="Hormuz Strait Maritime Activity",
            preview="[ENCRYPTED] Analysis of dark fleet movements suggests...",
            price_usdc=25.0,
            confidence=0.85,
            source_agent="CARDINAL",
            created_at=now - timedelta(hours=1),
            expires_at=now + timedelta(hours=4)
        ),
        "intel-002": IntelPackage(
            id="intel-002",
            topic="Apple AI Hiring Patterns",
            preview="[ENCRYPTED] Cross-referencing LinkedIn and USPTO filings reveals...",
            price_usdc=20.0,
            confidence=0.78,
            source_agent="PHOENIX",
            created_at=now - timedelta(minutes=30)
        ),
    }
    
    # Mock signals
    signal_types = ["DIVERGENCE DETECTED", "ACCUMULATION ALERT", "POSITION CLOSED", "INTEL PUBLISHED"]
    agent_ids = ["HAMMERHEAD", "CARDINAL", "AMBASSADOR", "PHANTOM"]
    archetypes = ["SHARK", "SPY", "DIPLOMAT", "SABOTEUR"]
    levels = ["info", "success", "warning", "danger"]
    
    _signals = [
        Signal(
            id=f"sig-{i}",
            timestamp=now - timedelta(minutes=i * 3),
            signal_type=signal_types[i % len(signal_types)],
            agent_id=agent_ids[i % len(agent_ids)],
            agent_archetype=archetypes[i % len(archetypes)],
            message=f"Signal {i}: Market activity detected",
            level=levels[i % len(levels)],
            market_id="tanker-china-48h" if i % 2 == 0 else None,
            data=None
        )
        for i in range(20)
    ]


# Initialise mock data on module load
_init_mock_data()


# =============================================================================
# OPERATIONS ENDPOINTS
# =============================================================================

@router.get("/operations", response_model=List[Operation])
async def list_operations(
    status: Optional[OperationStatus] = None,
    limit: int = Query(default=10, le=50)
):
    """List active operations."""
    ops = list(_operations.values())
    
    if status:
        ops = [o for o in ops if o.status == status]
    
    # Update time_remaining
    now = datetime.now(timezone.utc)
    for op in ops:
        op.time_remaining = max(0, int((op.expires_at - now).total_seconds()))
    
    return sorted(ops, key=lambda x: x.created_at, reverse=True)[:limit]


@router.get("/operations/{operation_id}", response_model=Operation)
async def get_operation(operation_id: str):
    """Get operation details."""
    if operation_id not in _operations:
        raise HTTPException(status_code=404, detail="Operation not found")
    
    op = _operations[operation_id]
    now = datetime.now(timezone.utc)
    op.time_remaining = max(0, int((op.expires_at - now).total_seconds()))
    
    return op


@router.post("/operations/{operation_id}/join")
async def join_operation(operation_id: str, request: JoinOperationRequest):
    """Join an operation by taking a position."""
    if operation_id not in _operations:
        raise HTTPException(status_code=404, detail="Operation not found")
    
    op = _operations[operation_id]
    
    if op.status != OperationStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="Operation not active")
    
    # In production, this would interact with the market contract
    op.participants += 1
    op.total_volume += request.amount
    
    return {
        "success": True,
        "operation_id": operation_id,
        "position_type": request.position_type,
        "amount": request.amount,
        "tx_hash": f"0x{'0' * 64}"  # Placeholder
    }


# =============================================================================
# AGENTS ENDPOINTS
# =============================================================================

@router.get("/agents", response_model=List[Agent])
async def list_agents(
    archetype: Optional[AgentArchetype] = None,
    available_only: bool = False
):
    """List all agents and their status."""
    agents = list(_agents.values())
    
    if archetype:
        agents = [a for a in agents if a.archetype == archetype]
    
    if available_only:
        agents = [a for a in agents if a.is_available]
    
    return sorted(agents, key=lambda x: x.pnl_total, reverse=True)


@router.get("/agents/{agent_id}", response_model=Agent)
async def get_agent(agent_id: str):
    """Get agent details and P&L."""
    if agent_id not in _agents:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return _agents[agent_id]


@router.post("/agents/hire")
async def hire_agent(request: HireAgentRequest, background_tasks: BackgroundTasks):
    """Hire an agent via ACP."""
    if request.agent_id not in _agents:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    agent = _agents[request.agent_id]
    
    if not agent.is_available:
        raise HTTPException(status_code=400, detail="Agent not available")
    
    # Create ACP job (in production, this would be on-chain)
    job_id = f"ACP_JOB_{uuid.uuid4().hex[:12].upper()}"
    
    # Mark agent as busy (temporarily)
    agent.is_available = False
    
    # Simulate job completion in background
    async def complete_job():
        import asyncio
        await asyncio.sleep(5)  # Simulate work
        agent.is_available = True
    
    background_tasks.add_task(complete_job)
    
    return {
        "success": True,
        "job_id": job_id,
        "agent_id": request.agent_id,
        "status": "pending",
        "escrow_tx": f"0x{'0' * 64}",
        "estimated_completion": (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat()
    }


# =============================================================================
# INTEL ENDPOINTS
# =============================================================================

@router.get("/intel", response_model=List[IntelPackage])
async def list_intel():
    """List available intel packages."""
    return list(_intel_packages.values())


@router.post("/intel/purchase")
async def purchase_intel(request: PurchaseIntelRequest):
    """Purchase intel via ACP."""
    if request.intel_id not in _intel_packages:
        raise HTTPException(status_code=404, detail="Intel not found")
    
    intel = _intel_packages[request.intel_id]
    
    return {
        "success": True,
        "intel_id": request.intel_id,
        "topic": intel.topic,
        "content": f"[DECRYPTED] Full analysis of {intel.topic}... This would contain the actual intel content.",
        "confidence": intel.confidence,
        "source_agent": intel.source_agent,
        "price_paid": intel.price_usdc,
        "tx_hash": f"0x{'0' * 64}"
    }


# =============================================================================
# TIMELINE / FORK ENDPOINTS (Butler API)
# =============================================================================

@router.get("/timelines")
async def list_timelines():
    """List active timeline forks."""
    return list(_forks.values())


@router.post("/forks", response_model=TimelineFork)
async def create_fork(request: CreateForkRequest):
    """
    Create a timeline fork (Butler API).
    
    This is the main endpoint Butler calls to create counterfactual markets.
    """
    fork_id = f"FORK_{uuid.uuid4().hex[:8].upper()}"
    now = datetime.now(timezone.utc)
    
    # Calculate agents to deploy
    total_agents = sum(request.agent_config.values())
    
    fork = TimelineFork(
        fork_id=fork_id,
        source_platform=request.source_platform,
        source_market_id=request.source_market_id,
        scenarios=request.scenarios,
        agents_deployed=total_agents,
        status="active",
        created_at=now,
        expires_at=now + timedelta(hours=request.duration_hours),
        share_url=f"https://echelon.io/fork/{fork_id}"
    )
    
    _forks[fork_id] = fork
    
    return fork


@router.get("/forks/{fork_id}")
async def get_fork(fork_id: str):
    """Get timeline fork details."""
    if fork_id not in _forks:
        raise HTTPException(status_code=404, detail="Fork not found")
    
    return _forks[fork_id]


# =============================================================================
# SIGNALS ENDPOINTS
# =============================================================================

@router.get("/signals", response_model=List[Signal])
async def get_signals(
    limit: int = Query(default=20, le=100),
    agent_id: Optional[str] = None,
    signal_type: Optional[str] = None
):
    """Get real-time signals feed."""
    signals = _signals.copy()
    
    if agent_id:
        signals = [s for s in signals if s.agent_id == agent_id]
    
    if signal_type:
        signals = [s for s in signals if s.signal_type == signal_type]
    
    return signals[:limit]


# =============================================================================
# TIMELINE HEALTH ENDPOINTS
# =============================================================================

@router.get("/timeline-health/{timeline_id}", response_model=TimelineHealth)
async def get_timeline_health(timeline_id: str):
    """Get timeline health metrics."""
    return TimelineHealth(
        timeline_id=timeline_id,
        timeline_name="The Tanker War",
        status=random.choice(["STABLE", "DEGRADING", "CRITICAL"]),
        time_to_collapse=random.randint(3600, 86400),
        reality_alignment=random.uniform(0.6, 0.95),
        stability_index=random.uniform(0.5, 0.9),
        decay_rate=random.uniform(0.01, 0.05),
        sabotage_pressure=random.uniform(0.1, 0.4),
        shield_coverage=random.uniform(0.3, 0.7),
        net_momentum=random.choice(["BULLISH", "BEARISH", "NEUTRAL"])
    )


@router.get("/market-forces/{market_id}", response_model=MarketForce)
async def get_market_forces(market_id: str):
    """Get market forces (sabotage vs shield)."""
    return MarketForce(
        market_id=market_id,
        market_name="Tanker docks in China within 48h",
        sabotage_amount=random.uniform(500, 2000),
        shield_amount=random.uniform(300, 1500),
        current_price=random.uniform(0.3, 0.7),
        top_saboteurs=[
            {"agentName": "PHANTOM", "amount": random.uniform(100, 500)},
            {"agentName": "GHOST", "amount": random.uniform(50, 200)},
        ],
        top_defenders=[
            {"agentName": "SENTINEL", "amount": random.uniform(100, 400)},
            {"agentName": "GUARDIAN", "amount": random.uniform(50, 200)},
        ]
    )


# =============================================================================
# GAME STATE ENDPOINT (For Situation Room)
# =============================================================================

@router.get("/game-state")
async def get_game_state():
    """
    Get current game state for the Situation Room.
    
    This is the main endpoint the frontend polls for updates.
    """
    now = datetime.now(timezone.utc)
    
    # Calculate dynamic values
    global_tension = 0.45 + random.uniform(-0.1, 0.1)
    chaos_index = 0.32 + random.uniform(-0.05, 0.05)
    
    return {
        "global_tension": min(1.0, max(0.0, global_tension)),
        "chaos_index": min(1.0, max(0.0, chaos_index)),
        "faction_power": {
            "eastern_bloc": random.uniform(0.2, 0.35),
            "western_alliance": random.uniform(0.25, 0.4),
            "corporate": random.uniform(0.15, 0.25),
            "underground": random.uniform(0.05, 0.15),
            "non_aligned": random.uniform(0.05, 0.1),
        },
        "active_operations": len([o for o in _operations.values() if o.status == OperationStatus.ACTIVE]),
        "total_agents": len(_agents),
        "recent_signals": [s.dict() for s in _signals[:5]],
        "recent_events": [
            {"id": "evt-1", "timestamp": (now - timedelta(minutes=2)).isoformat(), "message": "HAMMERHEAD accumulated position in Ghost Tanker", "type": "trade"},
            {"id": "evt-2", "timestamp": (now - timedelta(minutes=5)).isoformat(), "message": "CARDINAL published new intel package", "type": "intel"},
            {"id": "evt-3", "timestamp": (now - timedelta(minutes=8)).isoformat(), "message": "Timeline stability decreased to 72%", "type": "system"},
        ],
        "server_time": now.isoformat()
    }
