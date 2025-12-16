"""
Butler Webhook API
==================

Webhook endpoints for Virtuals Butler integration.

Butler calls these endpoints when users interact via X:
- @VirtualsButler fork the Fed decision market
- @VirtualsButler hire CARDINAL to analyse tanker movements
- @VirtualsButler show my positions

These endpoints translate Butler commands into Echelon actions.
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

router = APIRouter(prefix="/api/butler", tags=["butler"])

# Configuration
BUTLER_WEBHOOK_SECRET = os.getenv("BUTLER_WEBHOOK_SECRET", "dev-secret-change-me")


# =============================================================================
# MODELS
# =============================================================================

class ButlerCommandType(str, Enum):
    FORK_MARKET = "fork_market"
    HIRE_AGENT = "hire_agent"
    SHOW_POSITIONS = "show_positions"
    BUY_INTEL = "buy_intel"
    CHECK_BALANCE = "check_balance"
    LIST_AGENTS = "list_agents"
    LIST_OPERATIONS = "list_operations"
    UNKNOWN = "unknown"


class ButlerUser(BaseModel):
    """User info from Butler."""
    x_user_id: str
    x_username: str
    wallet_address: Optional[str] = None
    display_name: Optional[str] = None


class ButlerWebhookPayload(BaseModel):
    """Incoming webhook from Butler."""
    event_id: str
    event_type: str  # "command", "mention", "dm"
    timestamp: datetime
    user: ButlerUser
    raw_message: str
    parsed_command: Optional[str] = None
    parsed_args: Optional[Dict[str, Any]] = None
    conversation_id: Optional[str] = None
    reply_to_tweet_id: Optional[str] = None


class ButlerResponse(BaseModel):
    """Response to send back to Butler for posting."""
    success: bool
    message: str
    tweet_text: Optional[str] = None  # Text to post as reply
    card_data: Optional[Dict[str, Any]] = None  # Rich card data
    action_url: Optional[str] = None  # Link to Situation Room
    error: Optional[str] = None


class ForkRequest(BaseModel):
    """Request to fork a market."""
    source_platform: str = "polymarket"
    source_market_id: str
    scenarios: List[Dict[str, Any]]
    duration_hours: int = 24
    agent_config: Dict[str, int] = Field(default_factory=lambda: {
        "sharks": 2,
        "spies": 1,
        "diplomats": 1,
        "saboteurs": 1
    })


class HireAgentRequest(BaseModel):
    """Request to hire an agent."""
    agent_id: str
    task_type: str
    task_params: Dict[str, Any]
    max_budget_usdc: float = 50.0


# =============================================================================
# COMMAND PARSING
# =============================================================================

def parse_butler_command(raw_message: str) -> tuple[ButlerCommandType, Dict[str, Any]]:
    """
    Parse a Butler command from raw message text.
    
    Examples:
    - "fork the Fed decision market" -> (FORK_MARKET, {market: "fed-decision"})
    - "hire CARDINAL to analyse tankers" -> (HIRE_AGENT, {agent: "CARDINAL", task: "analyse tankers"})
    - "show my positions" -> (SHOW_POSITIONS, {})
    """
    message = raw_message.lower().strip()
    args = {}
    
    # Fork market command
    if "fork" in message:
        # Extract market name/ID
        if "fed" in message:
            args["market_id"] = "fed-rate-decision"
            args["market_name"] = "Fed Rate Decision"
        elif "election" in message:
            args["market_id"] = "us-election-2024"
            args["market_name"] = "US Election"
        elif "tanker" in message or "oil" in message:
            args["market_id"] = "oil-tanker-crisis"
            args["market_name"] = "Oil Tanker Crisis"
        else:
            # Try to extract market ID from message
            args["market_id"] = "custom-" + message.replace(" ", "-")[:20]
            args["market_name"] = "Custom Market"
        return (ButlerCommandType.FORK_MARKET, args)
    
    # Hire agent command
    if "hire" in message:
        agents = ["cardinal", "hammerhead", "sentinel", "ambassador", "phantom", "phoenix", "raven"]
        for agent in agents:
            if agent in message:
                args["agent_id"] = agent.upper()
                break
        
        # Extract task
        if "analyse" in message or "analyze" in message:
            task_start = message.find("analyse") if "analyse" in message else message.find("analyze")
            args["task"] = message[task_start:].strip()
        elif "investigate" in message:
            task_start = message.find("investigate")
            args["task"] = message[task_start:].strip()
        else:
            args["task"] = "general analysis"
        
        return (ButlerCommandType.HIRE_AGENT, args)
    
    # Show positions
    if "position" in message or "portfolio" in message:
        return (ButlerCommandType.SHOW_POSITIONS, args)
    
    # Check balance
    if "balance" in message or "wallet" in message:
        return (ButlerCommandType.CHECK_BALANCE, args)
    
    # Buy intel
    if "intel" in message and ("buy" in message or "purchase" in message):
        return (ButlerCommandType.BUY_INTEL, args)
    
    # List agents
    if "agent" in message and ("list" in message or "show" in message or "available" in message):
        return (ButlerCommandType.LIST_AGENTS, args)
    
    # List operations
    if "operation" in message or "mission" in message:
        return (ButlerCommandType.LIST_OPERATIONS, args)
    
    return (ButlerCommandType.UNKNOWN, args)


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

async def handle_fork_market(user: ButlerUser, args: Dict[str, Any]) -> ButlerResponse:
    """Handle fork market command."""
    market_id = args.get("market_id", "unknown")
    market_name = args.get("market_name", "Unknown Market")
    
    # Create fork
    fork_id = f"FORK_{uuid.uuid4().hex[:8].upper()}"
    
    # Generate scenarios
    scenarios = [
        {"name": "Bullish", "description": f"{market_name} resolves YES", "probability": 0.6},
        {"name": "Bearish", "description": f"{market_name} resolves NO", "probability": 0.4},
    ]
    
    tweet_text = f"""🔀 TIMELINE FORKED

Market: {market_name}
Fork ID: {fork_id}
Scenarios: {len(scenarios)}
Agents: 5 deployed

⏱️ Expires in 24h

🎯 Trade now: echelon.io/fork/{fork_id}

@{user.x_username}"""

    return ButlerResponse(
        success=True,
        message=f"Created fork {fork_id} for {market_name}",
        tweet_text=tweet_text,
        action_url=f"https://echelon.io/fork/{fork_id}",
        card_data={
            "fork_id": fork_id,
            "market_name": market_name,
            "scenarios": scenarios,
            "agents_deployed": 5
        }
    )


async def handle_hire_agent(user: ButlerUser, args: Dict[str, Any]) -> ButlerResponse:
    """Handle hire agent command."""
    agent_id = args.get("agent_id", "CARDINAL")
    task = args.get("task", "analysis")
    
    # Create ACP job
    job_id = f"ACP_JOB_{uuid.uuid4().hex[:12].upper()}"
    
    # Estimate cost based on agent and task
    cost_estimate = 25.0  # Base cost
    if "comprehensive" in task.lower():
        cost_estimate = 50.0
    
    tweet_text = f"""🕵️ AGENT HIRED

Agent: {agent_id}
Task: {task[:50]}...
Job ID: {job_id}
Est. Cost: ${cost_estimate:.2f} USDC

⏳ ETA: 30 minutes

📊 Track: echelon.io/jobs/{job_id}

@{user.x_username}"""

    return ButlerResponse(
        success=True,
        message=f"Hired {agent_id} for {task}",
        tweet_text=tweet_text,
        action_url=f"https://echelon.io/jobs/{job_id}",
        card_data={
            "job_id": job_id,
            "agent_id": agent_id,
            "task": task,
            "cost_estimate": cost_estimate
        }
    )


async def handle_show_positions(user: ButlerUser, args: Dict[str, Any]) -> ButlerResponse:
    """Handle show positions command."""
    # Mock positions for now
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

🎯 Manage: echelon.io/portfolio

@{user.x_username}"""

    return ButlerResponse(
        success=True,
        message=f"Found {len(positions)} positions",
        tweet_text=tweet_text,
        action_url="https://echelon.io/portfolio",
        card_data={"positions": positions, "total_pnl": total_pnl}
    )


async def handle_check_balance(user: ButlerUser, args: Dict[str, Any]) -> ButlerResponse:
    """Handle check balance command."""
    # Mock balance
    balance = {
        "usdc": 1250.00,
        "eth": 0.05,
        "echelon_points": 500
    }
    
    tweet_text = f"""💰 WALLET BALANCE

USDC: ${balance['usdc']:,.2f}
ETH: {balance['eth']:.4f}
ECHELON Points: {balance['echelon_points']}

🔗 Deposit: echelon.io/wallet

@{user.x_username}"""

    return ButlerResponse(
        success=True,
        message="Balance retrieved",
        tweet_text=tweet_text,
        action_url="https://echelon.io/wallet",
        card_data=balance
    )


async def handle_list_agents(user: ButlerUser, args: Dict[str, Any]) -> ButlerResponse:
    """Handle list agents command."""
    agents = [
        {"id": "HAMMERHEAD", "type": "🦈 Shark", "win_rate": 68, "available": True},
        {"id": "CARDINAL", "type": "🕵️ Spy", "win_rate": 74, "available": True},
        {"id": "AMBASSADOR", "type": "🤝 Diplomat", "win_rate": 61, "available": False},
        {"id": "PHANTOM", "type": "👻 Saboteur", "win_rate": 42, "available": True},
    ]
    
    available = [a for a in agents if a["available"]]
    
    agents_text = "\n".join([
        f"• {a['id']} {a['type']} - {a['win_rate']}% WR {'✅' if a['available'] else '🔒'}"
        for a in agents[:4]
    ])
    
    tweet_text = f"""🤖 AVAILABLE AGENTS

{agents_text}

📋 {len(available)}/{len(agents)} available

Hire: "@VirtualsButler hire [AGENT] to [TASK]"

@{user.x_username}"""

    return ButlerResponse(
        success=True,
        message=f"Listed {len(agents)} agents",
        tweet_text=tweet_text,
        action_url="https://echelon.io/agents",
        card_data={"agents": agents}
    )


async def handle_list_operations(user: ButlerUser, args: Dict[str, Any]) -> ButlerResponse:
    """Handle list operations command."""
    operations = [
        {"codename": "GHOST TANKER", "difficulty": 72, "time_left": "4h"},
        {"codename": "SILICON ACQUISITION", "difficulty": 58, "time_left": "8h"},
        {"codename": "CONTAGION ZERO", "difficulty": 85, "time_left": "2h"},
    ]
    
    ops_text = "\n".join([
        f"• {op['codename']} - {op['difficulty']}% 🕐{op['time_left']}"
        for op in operations
    ])
    
    tweet_text = f"""🎯 ACTIVE OPERATIONS

{ops_text}

Join: echelon.io/operations

@{user.x_username}"""

    return ButlerResponse(
        success=True,
        message=f"Listed {len(operations)} operations",
        tweet_text=tweet_text,
        action_url="https://echelon.io/operations",
        card_data={"operations": operations}
    )


async def handle_unknown(user: ButlerUser, raw_message: str) -> ButlerResponse:
    """Handle unknown command."""
    tweet_text = f"""🤔 I didn't understand that command.

Try:
• "fork the [market] market"
• "hire [AGENT] to [task]"
• "show my positions"
• "list agents"
• "list operations"

📚 Help: echelon.io/help

@{user.x_username}"""

    return ButlerResponse(
        success=False,
        message="Unknown command",
        tweet_text=tweet_text,
        action_url="https://echelon.io/help",
        error="Command not recognised"
    )


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.post("/webhook", response_model=ButlerResponse)
async def butler_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_butler_signature: Optional[str] = Header(None, alias="X-Butler-Signature")
):
    """
    Main webhook endpoint for Butler.
    
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
    
    # Parse command
    command_type, args = parse_butler_command(payload.raw_message)
    
    # Route to handler
    if command_type == ButlerCommandType.FORK_MARKET:
        response = await handle_fork_market(payload.user, args)
    elif command_type == ButlerCommandType.HIRE_AGENT:
        response = await handle_hire_agent(payload.user, args)
    elif command_type == ButlerCommandType.SHOW_POSITIONS:
        response = await handle_show_positions(payload.user, args)
    elif command_type == ButlerCommandType.CHECK_BALANCE:
        response = await handle_check_balance(payload.user, args)
    elif command_type == ButlerCommandType.LIST_AGENTS:
        response = await handle_list_agents(payload.user, args)
    elif command_type == ButlerCommandType.LIST_OPERATIONS:
        response = await handle_list_operations(payload.user, args)
    else:
        response = await handle_unknown(payload.user, payload.raw_message)
    
    return response


@router.get("/health")
async def butler_health():
    """Health check endpoint for Butler."""
    return {
        "status": "healthy",
        "service": "echelon-butler-api",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "commands_supported": [cmd.value for cmd in ButlerCommandType if cmd != ButlerCommandType.UNKNOWN]
    }


@router.post("/test")
async def butler_test(raw_message: str):
    """
    Test endpoint to simulate Butler commands locally.
    
    Usage: POST /api/butler/test?raw_message=fork the fed market
    """
    mock_user = ButlerUser(
        x_user_id="123456",
        x_username="testuser",
        wallet_address="0x1234...5678"
    )
    
    command_type, args = parse_butler_command(raw_message)
    
    if command_type == ButlerCommandType.FORK_MARKET:
        response = await handle_fork_market(mock_user, args)
    elif command_type == ButlerCommandType.HIRE_AGENT:
        response = await handle_hire_agent(mock_user, args)
    elif command_type == ButlerCommandType.SHOW_POSITIONS:
        response = await handle_show_positions(mock_user, args)
    elif command_type == ButlerCommandType.CHECK_BALANCE:
        response = await handle_check_balance(mock_user, args)
    elif command_type == ButlerCommandType.LIST_AGENTS:
        response = await handle_list_agents(mock_user, args)
    elif command_type == ButlerCommandType.LIST_OPERATIONS:
        response = await handle_list_operations(mock_user, args)
    else:
        response = await handle_unknown(mock_user, raw_message)
    
    return {
        "parsed_command": command_type.value,
        "parsed_args": args,
        "response": response
    }
