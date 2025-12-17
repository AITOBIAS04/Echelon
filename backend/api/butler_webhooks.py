"""
Butler Webhook API v2
=====================

Webhook endpoints for Virtuals Butler / ACP integration.

This version integrates with the InstanceManager to route jobs
to Agent Instances rather than mock responses.

Architecture:
- Butler sends job request → Webhook receives
- Webhook routes to InstanceManager
- InstanceManager finds/spawns appropriate Instance
- Instance executes job
- Result returned to Butler for posting

Author: Echelon Protocol
Version: 2.0.0
"""

from fastapi import APIRouter, HTTPException, Request, Header, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta
from enum import Enum
import hashlib
import hmac
import os
import uuid
import logging

# Import InstanceManager
from backend.agents.instance_manager import (
    get_instance_manager,
    InstanceManager,
    JobRequest,
    JobResult,
    EchelonArchetype,
    GENESIS_IDENTITIES,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/butler", tags=["butler"])

# Configuration
BUTLER_WEBHOOK_SECRET = os.getenv("BUTLER_WEBHOOK_SECRET", "dev-secret-change-me")
ECHELON_BASE_URL = os.getenv("ECHELON_BASE_URL", "https://playechelon.io")


# =============================================================================
# MODELS
# =============================================================================

class ButlerCommandType(str, Enum):
    """Supported Butler commands."""
    FORK_MARKET = "fork_market"
    HIRE_AGENT = "hire_agent"
    SHOW_POSITIONS = "show_positions"
    BUY_INTEL = "buy_intel"
    CHECK_BALANCE = "check_balance"
    LIST_AGENTS = "list_agents"
    LIST_OPERATIONS = "list_operations"
    AGENT_STATS = "agent_stats"
    UNKNOWN = "unknown"


class ButlerUser(BaseModel):
    """User info from Butler."""
    x_user_id: str
    x_username: str
    wallet_address: Optional[str] = None
    display_name: Optional[str] = None


class ButlerWebhookPayload(BaseModel):
    """Incoming webhook from Butler/ACP."""
    event_id: str
    event_type: str  # "command", "mention", "dm", "job_request"
    timestamp: datetime
    user: ButlerUser
    raw_message: str
    parsed_command: Optional[str] = None
    parsed_args: Optional[Dict[str, Any]] = None
    conversation_id: Optional[str] = None
    reply_to_tweet_id: Optional[str] = None
    
    # ACP-specific fields
    acp_job_id: Optional[str] = None
    escrow_amount_usdc: Optional[float] = None
    capability_requested: Optional[str] = None


class ButlerResponse(BaseModel):
    """Response to send back to Butler for posting."""
    success: bool
    message: str
    tweet_text: Optional[str] = None
    card_data: Optional[Dict[str, Any]] = None
    action_url: Optional[str] = None
    error: Optional[str] = None
    
    # ACP-specific fields
    job_id: Optional[str] = None
    instance_id: Optional[str] = None
    fee_charged_usdc: Optional[float] = None
    deliverable_url: Optional[str] = None


# =============================================================================
# CAPABILITY MAPPING
# =============================================================================

# Maps natural language to capabilities defined in InstanceManager
CAPABILITY_KEYWORDS = {
    # OSINT / Analysis
    "analyse": "osint_analysis",
    "analyze": "osint_analysis",
    "research": "osint_analysis",
    "investigate": "osint_analysis",
    "intel": "intel_report",
    "report": "intel_report",
    
    # Trading
    "trade": "trade_execution",
    "buy": "trade_execution",
    "sell": "trade_execution",
    "arbitrage": "arbitrage",
    "liquidity": "liquidity_provision",
    
    # Diplomacy
    "treaty": "treaty_brokering",
    "alliance": "coalition_building",
    "negotiate": "negotiation",
    "coalition": "coalition_building",
    
    # Chaos
    "disrupt": "market_disruption",
    "chaos": "chaos_injection",
    "sabotage": "misinformation",
    
    # Tracking
    "track": "satellite_tracking",
    "satellite": "satellite_tracking",
    "flight": "satellite_tracking",
    "tanker": "satellite_tracking",
    "ship": "satellite_tracking",
    
    # Momentum
    "trend": "trend_following",
    "momentum": "momentum_trading",
    "breakout": "breakout_detection",
}

# Maps archetypes to emoji for display
ARCHETYPE_EMOJI = {
    EchelonArchetype.SHARK: "🦈",
    EchelonArchetype.SPY: "🕵️",
    EchelonArchetype.DIPLOMAT: "🤝",
    EchelonArchetype.SABOTEUR: "👻",
    EchelonArchetype.WHALE: "🐋",
    EchelonArchetype.MOMENTUM: "🚀",
}


# =============================================================================
# COMMAND PARSING
# =============================================================================

def parse_butler_command(raw_message: str) -> tuple[ButlerCommandType, Dict[str, Any]]:
    """
    Parse a Butler command from raw message text.
    
    Returns (command_type, args) where args contains parsed parameters.
    """
    message = raw_message.lower().strip()
    args = {}
    
    # Fork market command
    if "fork" in message:
        args["market_id"], args["market_name"] = _extract_market(message)
        return (ButlerCommandType.FORK_MARKET, args)
    
    # Hire agent command
    if "hire" in message:
        args["identity_id"] = _extract_agent_identity(raw_message)
        args["capability"] = _extract_capability(message)
        args["task"] = _extract_task(message)
        args["event_id"] = _extract_event(message)
        return (ButlerCommandType.HIRE_AGENT, args)
    
    # Agent stats
    if "stats" in message and "agent" in message:
        args["identity_id"] = _extract_agent_identity(raw_message)
        return (ButlerCommandType.AGENT_STATS, args)
    
    # Show positions
    if "position" in message or "portfolio" in message:
        return (ButlerCommandType.SHOW_POSITIONS, args)
    
    # Check balance
    if "balance" in message or "wallet" in message:
        return (ButlerCommandType.CHECK_BALANCE, args)
    
    # Buy intel
    if "intel" in message and ("buy" in message or "purchase" in message):
        args["identity_id"] = _extract_agent_identity(raw_message)
        return (ButlerCommandType.BUY_INTEL, args)
    
    # List agents
    if "agent" in message and ("list" in message or "show" in message or "available" in message):
        args["archetype"] = _extract_archetype(message)
        return (ButlerCommandType.LIST_AGENTS, args)
    
    # List operations
    if "operation" in message or "mission" in message or "event" in message:
        return (ButlerCommandType.LIST_OPERATIONS, args)
    
    return (ButlerCommandType.UNKNOWN, args)


def _extract_market(message: str) -> tuple[str, str]:
    """Extract market ID and name from message."""
    market_patterns = {
        "fed": ("fed-rate-decision", "Fed Rate Decision"),
        "election": ("us-election-2024", "US Election"),
        "tanker": ("oil-tanker-crisis", "Oil Tanker Crisis"),
        "oil": ("oil-tanker-crisis", "Oil Tanker Crisis"),
        "crypto": ("crypto-market", "Crypto Market"),
        "bitcoin": ("btc-price", "Bitcoin Price"),
        "eth": ("eth-price", "Ethereum Price"),
    }
    
    for keyword, (market_id, market_name) in market_patterns.items():
        if keyword in message:
            return (market_id, market_name)
    
    # Default: create custom market ID
    clean = message.replace("fork", "").replace("the", "").replace("market", "").strip()
    market_id = "custom-" + clean.replace(" ", "-")[:20]
    return (market_id, clean.title() or "Custom Market")


def _extract_agent_identity(message: str) -> Optional[str]:
    """Extract agent identity ID from message (case-preserved)."""
    # Check for exact identity matches (case-insensitive search, preserve case)
    message_upper = message.upper()
    for identity_id in GENESIS_IDENTITIES.keys():
        if identity_id in message_upper:
            return identity_id
    return None


def _extract_capability(message: str) -> str:
    """Extract capability from message keywords."""
    for keyword, capability in CAPABILITY_KEYWORDS.items():
        if keyword in message:
            return capability
    return "osint_analysis"  # Default


def _extract_task(message: str) -> str:
    """Extract task description from message."""
    # Look for task after "to" keyword
    if " to " in message:
        parts = message.split(" to ", 1)
        if len(parts) > 1:
            return parts[1].strip()[:200]
    return "general analysis"


def _extract_event(message: str) -> Optional[str]:
    """Extract event ID if mentioned."""
    # Look for event patterns like "on GHOST_TANKER" or "for oil-tanker-crisis"
    event_keywords = ["on ", "for ", "event ", "operation "]
    for keyword in event_keywords:
        if keyword in message:
            idx = message.find(keyword) + len(keyword)
            potential_event = message[idx:].split()[0] if message[idx:] else None
            if potential_event and len(potential_event) > 3:
                return potential_event.upper().replace("-", "_")
    return None


def _extract_archetype(message: str) -> Optional[EchelonArchetype]:
    """Extract archetype filter from message."""
    archetype_map = {
        "shark": EchelonArchetype.SHARK,
        "spy": EchelonArchetype.SPY,
        "spies": EchelonArchetype.SPY,
        "diplomat": EchelonArchetype.DIPLOMAT,
        "saboteur": EchelonArchetype.SABOTEUR,
        "whale": EchelonArchetype.WHALE,
        "momentum": EchelonArchetype.MOMENTUM,
    }
    for keyword, archetype in archetype_map.items():
        if keyword in message:
            return archetype
    return None


# =============================================================================
# WEBHOOK VERIFICATION
# =============================================================================

def verify_webhook_signature(payload: bytes, signature: str) -> bool:
    """Verify the webhook signature from Butler."""
    expected = hmac.new(
        BUTLER_WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)


# =============================================================================
# COMMAND HANDLERS
# =============================================================================

async def handle_fork_market(
    user: ButlerUser, 
    args: Dict[str, Any],
    manager: InstanceManager,
) -> ButlerResponse:
    """
    Handle fork market command.
    
    Creates a new timeline fork and assigns agents to it.
    """
    market_id = args.get("market_id", "unknown")
    market_name = args.get("market_name", "Unknown Market")
    
    # Generate fork ID
    fork_id = f"FORK_{uuid.uuid4().hex[:8].upper()}"
    event_id = f"{market_id.upper().replace('-', '_')}_{fork_id[-4:]}"
    
    # Assign agents to the event
    try:
        instances = manager.assign_agents_to_event(
            event_id=event_id,
            event_name=market_name,
            agent_config={
                "sharks": 2,
                "spies": 1,
                "diplomats": 1,
                "saboteurs": 1,
            }
        )
        agents_deployed = len(instances)
        agent_names = [inst.parent_identity_id for inst in instances]
    except Exception as e:
        logger.error(f"Failed to assign agents: {e}")
        agents_deployed = 0
        agent_names = []
    
    # Generate scenarios
    scenarios = [
        {"name": "Bullish", "description": f"{market_name} resolves YES", "probability": 0.6},
        {"name": "Bearish", "description": f"{market_name} resolves NO", "probability": 0.4},
    ]
    
    tweet_text = f"""🔀 TIMELINE FORKED

Market: {market_name}
Fork ID: {fork_id}
Scenarios: {len(scenarios)}
Agents: {agents_deployed} deployed ({', '.join(agent_names[:3])}{'...' if len(agent_names) > 3 else ''})

⏱️ Expires in 24h

🎯 Trade now: {ECHELON_BASE_URL}/fork/{fork_id}

@{user.x_username}"""

    return ButlerResponse(
        success=True,
        message=f"Created fork {fork_id} for {market_name}",
        tweet_text=tweet_text,
        action_url=f"{ECHELON_BASE_URL}/fork/{fork_id}",
        card_data={
            "fork_id": fork_id,
            "event_id": event_id,
            "market_name": market_name,
            "scenarios": scenarios,
            "agents_deployed": agents_deployed,
            "agent_names": agent_names,
        }
    )


async def handle_hire_agent(
    user: ButlerUser, 
    args: Dict[str, Any],
    manager: InstanceManager,
    raw_message: str,
) -> ButlerResponse:
    """
    Handle hire agent command.
    
    Routes job to InstanceManager which finds/spawns appropriate Instance.
    """
    identity_id = args.get("identity_id")
    capability = args.get("capability", "osint_analysis")
    task = args.get("task", "general analysis")
    event_id = args.get("event_id")
    
    # Create job request
    job_request = JobRequest(
        source="butler",
        user_id=user.x_user_id,
        user_wallet=user.wallet_address,
        identity_requested=identity_id,
        capability_required=capability,
        task_description=task,
        task_params={"raw_message": raw_message},
        event_id=event_id,
    )
    
    try:
        # Route to instance
        instance = await manager.route_job(job_request)
        identity = manager.get_identity(instance.parent_identity_id)
        
        # Get archetype emoji
        archetype_emoji = ARCHETYPE_EMOJI.get(identity.archetype, "🤖") if identity else "🤖"
        
        # In production, this would trigger async job execution
        # For now, we simulate immediate completion
        # TODO: Implement actual async job execution with background_tasks
        
        tweet_text = f"""{archetype_emoji} AGENT HIRED

Agent: {instance.parent_identity_id}
Instance: {instance.instance_id[-8:]}
Task: {task[:50]}{'...' if len(task) > 50 else ''}

💰 Fee: ${identity.service_fee_usdc:.2f} USDC
📋 Job ID: {job_request.job_id}

⏳ Processing... Results will be posted when ready.

🎯 Track: {ECHELON_BASE_URL}/jobs/{job_request.job_id}

@{user.x_username}"""

        return ButlerResponse(
            success=True,
            message=f"Hired {instance.parent_identity_id} for {task[:30]}",
            tweet_text=tweet_text,
            action_url=f"{ECHELON_BASE_URL}/jobs/{job_request.job_id}",
            job_id=job_request.job_id,
            instance_id=instance.instance_id,
            fee_charged_usdc=identity.service_fee_usdc if identity else 10.0,
            card_data={
                "job_id": job_request.job_id,
                "instance_id": instance.instance_id,
                "identity_id": instance.parent_identity_id,
                "task": task,
                "fee": identity.service_fee_usdc if identity else 10.0,
                "status": "processing",
            }
        )
        
    except ValueError as e:
        return ButlerResponse(
            success=False,
            message=str(e),
            tweet_text=f"""❌ HIRE FAILED

{str(e)}

Try: "hire CARDINAL to analyse oil tankers"

Available agents: {', '.join(list(GENESIS_IDENTITIES.keys())[:6])}...

@{user.x_username}""",
            error=str(e),
        )
    except Exception as e:
        logger.exception(f"Error hiring agent: {e}")
        return ButlerResponse(
            success=False,
            message="Internal error processing request",
            error=str(e),
        )


async def handle_list_agents(
    user: ButlerUser, 
    args: Dict[str, Any],
    manager: InstanceManager,
) -> ButlerResponse:
    """
    Handle list agents command.
    
    Returns available Genesis Identities from InstanceManager.
    """
    archetype_filter = args.get("archetype")
    
    # Get identities
    if archetype_filter:
        identities = manager.get_identities_by_archetype(archetype_filter)
    else:
        identities = list(manager.identities.values())
    
    # Format agent list
    agents_data = []
    agents_text_lines = []
    
    for identity in identities[:8]:  # Limit to 8 for tweet length
        emoji = ARCHETYPE_EMOJI.get(identity.archetype, "🤖")
        available = identity.active_instance_count < identity.max_concurrent_instances
        
        agents_data.append({
            "id": identity.identity_id,
            "name": identity.display_name,
            "archetype": identity.archetype.value,
            "fee": identity.service_fee_usdc,
            "win_rate": identity.win_rate,
            "available": available,
        })
        
        status = "✅" if available else "🔒"
        agents_text_lines.append(
            f"• {identity.identity_id} {emoji} ${identity.service_fee_usdc:.0f} {status}"
        )
    
    available_count = sum(1 for a in agents_data if a["available"])
    agents_text = "\n".join(agents_text_lines)
    
    tweet_text = f"""🤖 ECHELON AGENTS

{agents_text}

📋 {available_count}/{len(agents_data)} available

Hire: "@VirtualsButler hire [AGENT] to [TASK]"

@{user.x_username}"""

    return ButlerResponse(
        success=True,
        message=f"Listed {len(agents_data)} agents",
        tweet_text=tweet_text,
        action_url=f"{ECHELON_BASE_URL}/agents",
        card_data={"agents": agents_data, "total": len(identities)},
    )


async def handle_agent_stats(
    user: ButlerUser,
    args: Dict[str, Any],
    manager: InstanceManager,
) -> ButlerResponse:
    """Handle agent stats request."""
    identity_id = args.get("identity_id")
    
    if not identity_id:
        return ButlerResponse(
            success=False,
            message="Please specify an agent",
            tweet_text=f"""❓ Which agent?

Specify an agent: "stats for MEGALODON"

@{user.x_username}""",
            error="No agent specified",
        )
    
    stats = manager.get_identity_stats(identity_id)
    
    if not stats:
        return ButlerResponse(
            success=False,
            message=f"Unknown agent: {identity_id}",
            error="Agent not found",
        )
    
    emoji = ARCHETYPE_EMOJI.get(EchelonArchetype(stats["archetype"]), "🤖")
    
    tweet_text = f"""{emoji} {stats['identity_id']} STATS

{stats['display_name']}
Type: {stats['archetype'].title()}

📊 Performance:
• Jobs: {stats['total_jobs']}
• Win Rate: {stats['win_rate']:.0%}
• Total P&L: ${stats['total_pnl']:+,.2f}

💰 Fee: ${stats['service_fee']:.2f} USDC
🔧 Active Instances: {stats['active_instances']}

@{user.x_username}"""

    return ButlerResponse(
        success=True,
        message=f"Stats for {identity_id}",
        tweet_text=tweet_text,
        action_url=f"{ECHELON_BASE_URL}/agents/{identity_id}",
        card_data=stats,
    )


async def handle_show_positions(
    user: ButlerUser, 
    args: Dict[str, Any],
) -> ButlerResponse:
    """Handle show positions command."""
    # TODO: Integrate with actual position tracking
    # For now, return mock data
    positions = [
        {"market": "Ghost Tanker", "side": "YES", "size": 100, "pnl": 25.50},
        {"market": "Fed Rate Cut", "side": "NO", "size": 50, "pnl": -12.00},
    ]
    
    total_pnl = sum(p["pnl"] for p in positions)
    pnl_emoji = "📈" if total_pnl > 0 else "📉"
    
    positions_text = "\n".join([
        f"• {p['market']}: {p['side']} ${p['size']} ({'+' if p['pnl'] > 0 else ''}{p['pnl']:.2f})"
        for p in positions
    ])
    
    tweet_text = f"""📊 YOUR POSITIONS

{positions_text}

{pnl_emoji} Total P&L: ${total_pnl:+.2f}

🎯 Manage: {ECHELON_BASE_URL}/portfolio

@{user.x_username}"""

    return ButlerResponse(
        success=True,
        message=f"Found {len(positions)} positions",
        tweet_text=tweet_text,
        action_url=f"{ECHELON_BASE_URL}/portfolio",
        card_data={"positions": positions, "total_pnl": total_pnl},
    )


async def handle_check_balance(
    user: ButlerUser, 
    args: Dict[str, Any],
) -> ButlerResponse:
    """Handle check balance command."""
    # TODO: Integrate with actual wallet balance
    balance = {
        "usdc": 1250.00,
        "eth": 0.05,
        "echelon_points": 500
    }
    
    tweet_text = f"""💰 WALLET BALANCE

USDC: ${balance['usdc']:,.2f}
ETH: {balance['eth']:.4f}
ECHELON Points: {balance['echelon_points']}

🔗 Deposit: {ECHELON_BASE_URL}/wallet

@{user.x_username}"""

    return ButlerResponse(
        success=True,
        message="Balance retrieved",
        tweet_text=tweet_text,
        action_url=f"{ECHELON_BASE_URL}/wallet",
        card_data=balance,
    )


async def handle_buy_intel(
    user: ButlerUser,
    args: Dict[str, Any],
    manager: InstanceManager,
) -> ButlerResponse:
    """Handle buy intel command - hire a Spy for intel."""
    # Route to hire_agent with spy capability
    args["capability"] = "intel_report"
    if not args.get("identity_id"):
        # Default to CARDINAL for intel
        args["identity_id"] = "CARDINAL"
    args["task"] = "generate intel report"
    
    return await handle_hire_agent(user, args, manager, "buy intel report")


async def handle_list_operations(
    user: ButlerUser, 
    args: Dict[str, Any],
    manager: InstanceManager,
) -> ButlerResponse:
    """Handle list operations command."""
    # Get active events from manager
    active_events = list(manager.event_instances.keys())
    
    # Mock additional operations for demo
    operations = []
    
    for event_id in active_events[:3]:
        instances = manager.get_event_instances(event_id)
        operations.append({
            "codename": event_id.replace("_", " "),
            "agents": len(instances),
            "status": "active",
        })
    
    # Add some demo operations if none active
    if not operations:
        operations = [
            {"codename": "GHOST TANKER", "difficulty": 72, "time_left": "4h"},
            {"codename": "SILICON ACQUISITION", "difficulty": 58, "time_left": "8h"},
            {"codename": "CONTAGION ZERO", "difficulty": 85, "time_left": "2h"},
        ]
    
    ops_text = "\n".join([
        f"• {op['codename']}" + (f" ({op['agents']} agents)" if 'agents' in op else f" - {op.get('difficulty', '?')}%")
        for op in operations
    ])
    
    tweet_text = f"""🎯 ACTIVE OPERATIONS

{ops_text}

Join: {ECHELON_BASE_URL}/operations

@{user.x_username}"""

    return ButlerResponse(
        success=True,
        message=f"Listed {len(operations)} operations",
        tweet_text=tweet_text,
        action_url=f"{ECHELON_BASE_URL}/operations",
        card_data={"operations": operations},
    )


async def handle_unknown(
    user: ButlerUser, 
    raw_message: str,
) -> ButlerResponse:
    """Handle unknown command."""
    tweet_text = f"""🤔 I didn't understand that command.

Try:
• "fork the [market] market"
• "hire [AGENT] to [task]"
• "list agents"
• "stats for [AGENT]"
• "show my positions"

📚 Help: {ECHELON_BASE_URL}/help

@{user.x_username}"""

    return ButlerResponse(
        success=False,
        message="Unknown command",
        tweet_text=tweet_text,
        action_url=f"{ECHELON_BASE_URL}/help",
        error="Command not recognised",
    )


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.post("/webhook", response_model=ButlerResponse)
async def butler_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_butler_signature: Optional[str] = Header(None, alias="X-Butler-Signature"),
):
    """
    Main webhook endpoint for Butler/ACP.
    
    Butler sends POST requests here when users interact via X.
    """
    # Get raw body for signature verification
    body = await request.body()
    
    # Verify signature in production
    if x_butler_signature and BUTLER_WEBHOOK_SECRET != "dev-secret-change-me":
        if not verify_webhook_signature(body, x_butler_signature):
            raise HTTPException(status_code=401, detail="Invalid signature")
    
    # Parse payload
    try:
        payload = ButlerWebhookPayload.model_validate_json(body)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid payload: {e}")
    
    # Get instance manager
    manager = get_instance_manager()
    
    # Parse command
    command_type, args = parse_butler_command(payload.raw_message)
    
    logger.info(f"Butler command: {command_type.value} from @{payload.user.x_username}")
    
    # Route to handler
    if command_type == ButlerCommandType.FORK_MARKET:
        response = await handle_fork_market(payload.user, args, manager)
    elif command_type == ButlerCommandType.HIRE_AGENT:
        response = await handle_hire_agent(payload.user, args, manager, payload.raw_message)
    elif command_type == ButlerCommandType.LIST_AGENTS:
        response = await handle_list_agents(payload.user, args, manager)
    elif command_type == ButlerCommandType.AGENT_STATS:
        response = await handle_agent_stats(payload.user, args, manager)
    elif command_type == ButlerCommandType.SHOW_POSITIONS:
        response = await handle_show_positions(payload.user, args)
    elif command_type == ButlerCommandType.CHECK_BALANCE:
        response = await handle_check_balance(payload.user, args)
    elif command_type == ButlerCommandType.BUY_INTEL:
        response = await handle_buy_intel(payload.user, args, manager)
    elif command_type == ButlerCommandType.LIST_OPERATIONS:
        response = await handle_list_operations(payload.user, args, manager)
    else:
        response = await handle_unknown(payload.user, payload.raw_message)
    
    return response


@router.get("/health")
async def butler_health():
    """Health check endpoint for Butler."""
    manager = get_instance_manager()
    stats = manager.get_stats()
    
    return {
        "status": "healthy",
        "service": "echelon-butler-api",
        "version": "2.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "commands_supported": [cmd.value for cmd in ButlerCommandType if cmd != ButlerCommandType.UNKNOWN],
        "genesis_identities": stats["total_identities"],
        "active_instances": stats["active_instances"],
        "active_jobs": stats["active_jobs"],
    }


@router.get("/agents")
async def list_all_agents():
    """Get all available agents and their stats."""
    manager = get_instance_manager()
    
    agents = []
    for identity in manager.identities.values():
        stats = manager.get_identity_stats(identity.identity_id)
        if stats:
            stats["emoji"] = ARCHETYPE_EMOJI.get(identity.archetype, "🤖")
            agents.append(stats)
    
    return {
        "agents": agents,
        "total": len(agents),
    }


@router.get("/agents/{identity_id}")
async def get_agent(identity_id: str):
    """Get stats for a specific agent."""
    manager = get_instance_manager()
    stats = manager.get_identity_stats(identity_id.upper())
    
    if not stats:
        raise HTTPException(status_code=404, detail=f"Agent not found: {identity_id}")
    
    identity = manager.get_identity(identity_id.upper())
    if identity:
        stats["emoji"] = ARCHETYPE_EMOJI.get(identity.archetype, "🤖")
    
    return stats


@router.get("/stats")
async def get_manager_stats():
    """Get overall InstanceManager statistics."""
    manager = get_instance_manager()
    return manager.get_stats()


@router.post("/test")
async def butler_test(raw_message: str):
    """
    Test endpoint to simulate Butler commands locally.
    
    Usage: POST /api/butler/test?raw_message=hire CARDINAL to analyse tankers
    """
    mock_user = ButlerUser(
        x_user_id="test_123",
        x_username="testuser",
        wallet_address="0x1234567890abcdef1234567890abcdef12345678",
    )
    
    manager = get_instance_manager()
    command_type, args = parse_butler_command(raw_message)
    
    # Route to appropriate handler
    if command_type == ButlerCommandType.FORK_MARKET:
        response = await handle_fork_market(mock_user, args, manager)
    elif command_type == ButlerCommandType.HIRE_AGENT:
        response = await handle_hire_agent(mock_user, args, manager, raw_message)
    elif command_type == ButlerCommandType.LIST_AGENTS:
        response = await handle_list_agents(mock_user, args, manager)
    elif command_type == ButlerCommandType.AGENT_STATS:
        response = await handle_agent_stats(mock_user, args, manager)
    elif command_type == ButlerCommandType.SHOW_POSITIONS:
        response = await handle_show_positions(mock_user, args)
    elif command_type == ButlerCommandType.CHECK_BALANCE:
        response = await handle_check_balance(mock_user, args)
    elif command_type == ButlerCommandType.BUY_INTEL:
        response = await handle_buy_intel(mock_user, args, manager)
    elif command_type == ButlerCommandType.LIST_OPERATIONS:
        response = await handle_list_operations(mock_user, args, manager)
    else:
        response = await handle_unknown(mock_user, raw_message)
    
    return {
        "parsed_command": command_type.value,
        "parsed_args": args,
        "response": response,
    }


# =============================================================================
# ACP JOB LIFECYCLE ENDPOINTS
# =============================================================================

@router.post("/jobs/{job_id}/complete")
async def complete_job(
    job_id: str,
    success: bool = True,
    result_data: Dict[str, Any] = None,
    pnl: float = 0.0,
):
    """
    Mark a job as complete.
    
    Called when an agent instance finishes processing.
    """
    manager = get_instance_manager()
    
    try:
        result = await manager.complete_job(
            job_id=job_id,
            success=success,
            result_data=result_data or {},
            pnl=pnl,
        )
        return {
            "status": "completed",
            "result": result.model_dump(),
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/jobs/{job_id}")
async def get_job_status(job_id: str):
    """Get status of a job."""
    manager = get_instance_manager()
    
    # Check active jobs
    if job_id in manager.active_jobs:
        request = manager.active_jobs[job_id]
        return {
            "job_id": job_id,
            "status": "processing",
            "created_at": request.created_at.isoformat(),
            "task": request.task_description,
        }
    
    # Job not found or completed
    raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")
