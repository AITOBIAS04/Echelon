"""
Scheduler API
=============

REST API endpoints for managing the agent scheduler.

Endpoints:
- GET  /api/scheduler/status     - Get scheduler status
- POST /api/scheduler/start      - Start the scheduler
- POST /api/scheduler/stop       - Stop the scheduler
- GET  /api/scheduler/agents     - List scheduled agents
- GET  /api/scheduler/agents/{id} - Get agent status
- POST /api/scheduler/agents/{id}/enable  - Enable agent
- POST /api/scheduler/agents/{id}/disable - Disable agent
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

router = APIRouter(prefix="/api/scheduler", tags=["scheduler"])

# Import scheduler
try:
    from backend.core.agent_scheduler import get_scheduler, init_default_agents
    HAS_SCHEDULER = True
except ImportError as e:
    HAS_SCHEDULER = False
    print(f"⚠️ Scheduler not available: {e}")


# =============================================================================
# MODELS
# =============================================================================

class SchedulerStatus(BaseModel):
    running: bool
    agents_registered: int
    agents_enabled: int
    total_cycles: int
    total_decisions: int
    layer1_percentage: str
    total_cost_usd: str
    budget_remaining: str
    errors: int
    last_cycle: Optional[str]


class AgentStatus(BaseModel):
    agent_id: str
    archetype: str
    state: str
    enabled: bool
    run_interval_seconds: int
    last_run: Optional[str]
    next_run: Optional[str]
    decisions_today: int
    cost_today_usd: str


class RegisterAgentRequest(BaseModel):
    agent_id: str
    archetype: str
    run_interval_seconds: int = 60
    enabled: bool = True


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.get("/status")
async def get_scheduler_status():
    """Get current scheduler status and statistics."""
    if not HAS_SCHEDULER:
        return {"error": "Scheduler not available", "running": False}
    
    scheduler = get_scheduler()
    return scheduler.get_stats()


@router.post("/start")
async def start_scheduler(background_tasks: BackgroundTasks, init_agents: bool = True):
    """Start the agent scheduler."""
    if not HAS_SCHEDULER:
        raise HTTPException(status_code=500, detail="Scheduler not available")
    
    scheduler = get_scheduler()
    
    if scheduler.running:
        return {"message": "Scheduler already running", "status": "running"}
    
    # Optionally initialise default agents
    if init_agents and len(scheduler.agents) == 0:
        init_default_agents(scheduler)
    
    # Start in background
    scheduler.start()
    
    return {
        "message": "Scheduler started",
        "status": "running",
        "agents_registered": len(scheduler.agents)
    }


@router.post("/stop")
async def stop_scheduler():
    """Stop the agent scheduler."""
    if not HAS_SCHEDULER:
        raise HTTPException(status_code=500, detail="Scheduler not available")
    
    scheduler = get_scheduler()
    scheduler.stop()
    
    return {
        "message": "Scheduler stopped",
        "status": "stopped",
        "final_stats": scheduler.get_stats()
    }


@router.get("/agents")
async def list_scheduled_agents():
    """List all registered agents and their status."""
    if not HAS_SCHEDULER:
        return {"error": "Scheduler not available", "agents": []}
    
    scheduler = get_scheduler()
    
    agents = []
    for agent_id in scheduler.agents:
        status = scheduler.get_agent_status(agent_id)
        if status:
            agents.append(status)
    
    return {
        "agents": agents,
        "total": len(agents),
        "enabled": len([a for a in agents if a.get("enabled", False)])
    }


@router.get("/agents/{agent_id}")
async def get_agent_status(agent_id: str):
    """Get status of a specific agent."""
    if not HAS_SCHEDULER:
        raise HTTPException(status_code=500, detail="Scheduler not available")
    
    scheduler = get_scheduler()
    status = scheduler.get_agent_status(agent_id)
    
    if not status:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    
    return status


@router.post("/agents")
async def register_agent(request: RegisterAgentRequest):
    """Register a new agent for scheduling."""
    if not HAS_SCHEDULER:
        raise HTTPException(status_code=500, detail="Scheduler not available")
    
    scheduler = get_scheduler()
    
    agent = scheduler.register_agent(
        agent_id=request.agent_id,
        archetype=request.archetype,
        run_interval_seconds=request.run_interval_seconds,
        enabled=request.enabled
    )
    
    return {
        "message": f"Agent {request.agent_id} registered",
        "agent": scheduler.get_agent_status(request.agent_id)
    }


@router.post("/agents/{agent_id}/enable")
async def enable_agent(agent_id: str):
    """Enable a scheduled agent."""
    if not HAS_SCHEDULER:
        raise HTTPException(status_code=500, detail="Scheduler not available")
    
    scheduler = get_scheduler()
    
    if agent_id not in scheduler.agents:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    
    scheduler.agents[agent_id].enabled = True
    
    return {
        "message": f"Agent {agent_id} enabled",
        "agent": scheduler.get_agent_status(agent_id)
    }


@router.post("/agents/{agent_id}/disable")
async def disable_agent(agent_id: str):
    """Disable a scheduled agent."""
    if not HAS_SCHEDULER:
        raise HTTPException(status_code=500, detail="Scheduler not available")
    
    scheduler = get_scheduler()
    
    if agent_id not in scheduler.agents:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    
    scheduler.agents[agent_id].enabled = False
    
    return {
        "message": f"Agent {agent_id} disabled",
        "agent": scheduler.get_agent_status(agent_id)
    }


@router.delete("/agents/{agent_id}")
async def unregister_agent(agent_id: str):
    """Remove an agent from scheduling."""
    if not HAS_SCHEDULER:
        raise HTTPException(status_code=500, detail="Scheduler not available")
    
    scheduler = get_scheduler()
    
    if agent_id not in scheduler.agents:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    
    scheduler.unregister_agent(agent_id)
    
    return {"message": f"Agent {agent_id} unregistered"}


@router.post("/run-cycle/{agent_id}")
async def run_agent_cycle(agent_id: str):
    """Manually trigger a single decision cycle for an agent."""
    if not HAS_SCHEDULER:
        raise HTTPException(status_code=500, detail="Scheduler not available")
    
    scheduler = get_scheduler()
    
    if agent_id not in scheduler.agents:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    
    agent = scheduler.agents[agent_id]
    results = await scheduler.run_agent_cycle(agent)
    
    return {
        "message": f"Cycle completed for {agent_id}",
        "results": results
    }


@router.get("/layer1-stats")
async def get_layer1_stats():
    """Get Layer 1 rules engine statistics."""
    if not HAS_SCHEDULER:
        return {"error": "Scheduler not available"}
    
    scheduler = get_scheduler()
    
    if not scheduler.has_layer1 or not scheduler.layer1_engine:
        return {"error": "Layer 1 engine not available"}
    
    return {
        "layer1_available": True,
        "engine_stats": scheduler.layer1_engine.get_stats()
    }
