import uvicorn
import json
import subprocess 
import re 
import os
import sys 
from fastapi import FastAPI, Depends, HTTPException, status, Header, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm 
from sqlalchemy.orm import Session
from sqlalchemy import text
from passlib.context import CryptContext
from pydantic import BaseModel, ConfigDict, Field, validator
from typing import Annotated, Dict, Optional
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone

# Import CORSMiddleware
from fastapi.middleware.cors import CORSMiddleware

# Import Security utilities
from backend.core.security import (
    limiter,
    RATE_LIMITS,
    WalletAddressValidator,
    BetAmountValidator,
    StringSanitizer,
    get_client_ip,
)
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.extension import _rate_limit_exceeded_handler

# --- IMPORTS ---
from backend.core.database import SessionLocal, engine, Base, User as DBUser
from backend.core.osint_registry import get_osint_registry

# Auto Uploader Config
from backend.core.autouploader import AutoUploadConfig

# Payments Router
from backend.payments.routes import router as payments_router

# Situation Room Router (existing) - DISABLED: Using new API instead
# try:
#     from backend.api.situation_room_routes import router as situation_room_router
# except ImportError:
#     situation_room_router = None
situation_room_router = None  # Disabled - using new API

# New Situation Room API (simplified)
try:
    from backend.api.situation_room import router as situation_room_api_router
except ImportError as e:
    situation_room_api_router = None
    print(f"⚠️ Could not import Situation Room API router: {e}")

# Markets API
try:
    from backend.api.markets import router as markets_router
except ImportError:
    markets_router = None

# Operations API (Butler + Situation Room)
try:
    from backend.api.operations import router as operations_router
except ImportError as e:
    operations_router = None
    print(f"⚠️ Could not import Operations API router: {e}")

# Butterfly Engine API
try:
    from backend.api.butterfly_routes import router as butterfly_router
except ImportError as e:
    butterfly_router = None
    print(f"⚠️ Could not import Butterfly API router: {e}")

# Paradox Engine API
try:
    from backend.api.paradox_routes import router as paradox_router
except ImportError as e:
    paradox_router = None
    print(f"⚠️ Could not import Paradox API router: {e}")

# Admin/Demo API
try:
    from backend.api.admin_routes import router as admin_router
except ImportError as e:
    admin_router = None
    print(f"⚠️ Could not import Admin API router: {e}")

# Agents API
try:
    from backend.api.agents_routes import router as agents_router
except ImportError as e:
    agents_router = None
    print(f"⚠️ Could not import Agents API router: {e}")

# Positions API
try:
    from backend.api.positions_routes import router as positions_router
except ImportError as e:
    positions_router = None
    print(f"⚠️ Could not import Positions API router: {e}")

# OSINT API
try:
    from backend.api.osint_routes import router as osint_router
except ImportError as e:
    osint_router = None
    print(f"⚠️ Could not import OSINT API router: {e}")

# Initialize
osint = get_osint_registry()

# --- CONFIGURATION ---

# Ensure database tables are created
Base.metadata.create_all(bind=engine)
print("✅ Database tables initialized")

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token") 

# Security: Load JWT secret from environment variable
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not SECRET_KEY:
    # In production, this should raise an error
    SECRET_KEY = os.getenv("SECRET_KEY", "a_very_secret_key_for_jwt_replace_this")
    if SECRET_KEY == "a_very_secret_key_for_jwt_replace_this":
        # Only warn in production or if explicitly enabled
        is_production = os.getenv("ENVIRONMENT", "development").lower() == "production"
        if is_production:
            raise ValueError(
                "❌ CRITICAL: JWT_SECRET_KEY must be set in production! "
                "Generate one with: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
            )
        # In development, show a one-time warning (less verbose)
        import sys
        if not hasattr(sys, '_jwt_warning_shown'):
            print("⚠️  WARNING: Using default JWT secret key (development only).")
            print("   Set JWT_SECRET_KEY in .env for production.")
            sys._jwt_warning_shown = True

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

app = FastAPI()

# --- BACKGROUND TASKS ---
# Start game loop as background task if enabled
GAME_LOOP_ENABLED = os.getenv("ENABLE_GAME_LOOP", "true").lower() == "true"

@app.on_event("startup")
async def start_game_loop():
    """Start the game loop as a background task."""
    # Check USE_MOCKS here since it's defined later
    use_mocks = os.getenv("USE_MOCKS", "true").lower() == "true"
    if GAME_LOOP_ENABLED and not use_mocks:
        try:
            from backend.worker.game_loop import GameLoop
            import asyncio
            
            async def run_game_loop():
                loop = GameLoop()
                await loop.start()
            
            # Start game loop in background
            asyncio.create_task(run_game_loop())
            print("✅ Game loop started as background task")
        except Exception as e:
            print(f"⚠️  Could not start game loop: {e}")
            print("   Continuing without game loop...")

# --- RATE LIMITING MIDDLEWARE ---
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# --- CORS MIDDLEWARE ---
# More flexible CORS for production - allows Vercel and localhost
# Uses regex to match all Vercel preview and production deployments
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https://.*\.vercel\.app|http://localhost:.*|http://127\.0\.0\.1:.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
try:
    if payments_router:
        app.include_router(payments_router)
        print("✅ Payments router included")
    else:
        print("⚠️ Payments router is None, skipping")
except Exception as e:
    print(f"❌ Failed to include payments router: {e}")
    import traceback
    traceback.print_exc()

# Include new Situation Room API router (replaces old router)
try:
    if situation_room_api_router:
        app.include_router(situation_room_api_router)
        print("✅ Situation Room API router included")
        # Background tasks will start automatically via @router.on_event("startup")
    else:
        print("⚠️ Situation Room API router is None, skipping")
except Exception as e:
    print(f"❌ Failed to include Situation Room API router: {e}")
    import traceback
    traceback.print_exc()

# Include Markets router
try:
    if markets_router:
        app.include_router(markets_router)
        print("✅ Markets router included")
    else:
        print("⚠️ Markets router is None, skipping")
except Exception as e:
    print(f"❌ Failed to include Markets router: {e}")
    import traceback
    traceback.print_exc()

# Include Operations router (Butler + Situation Room)
try:
    if operations_router:
        app.include_router(operations_router)
        print("✅ Operations router included")
    else:
        print("⚠️ Operations router is None, skipping")
except Exception as e:
    print(f"❌ Failed to include Operations router: {e}")
    import traceback
    traceback.print_exc()

# Include Butterfly Engine router
try:
    if butterfly_router:
        app.include_router(butterfly_router)
        print("✅ Butterfly Engine router included")
    else:
        print("⚠️ Butterfly Engine router is None, skipping")
except Exception as e:
    print(f"❌ Failed to include Butterfly Engine router: {e}")
    import traceback
    traceback.print_exc()

# Include Paradox Engine router
try:
    if paradox_router:
        app.include_router(paradox_router)
        print("✅ Paradox Engine router included")
    else:
        print("⚠️ Paradox Engine router is None, skipping")
except Exception as e:
    print(f"❌ Failed to include Paradox Engine router: {e}")
    import traceback
    traceback.print_exc()

# Include Admin router
try:
    if admin_router:
        app.include_router(admin_router)
        print("✅ Admin router included")
    else:
        print("⚠️ Admin router is None, skipping")
except Exception as e:
    print(f"❌ Failed to include Admin router: {e}")
    import traceback
    traceback.print_exc()

# Include Agents router
try:
    if agents_router:
        app.include_router(agents_router)
        print("✅ Agents router included")
    else:
        print("⚠️ Agents router is None, skipping")
except Exception as e:
    print(f"❌ Failed to include Agents router: {e}")
    import traceback
    traceback.print_exc()

# Include Positions router
try:
    if positions_router:
        app.include_router(positions_router)
        print("✅ Positions router included")
    else:
        print("⚠️ Positions router is None, skipping")
except Exception as e:
    print(f"❌ Failed to include Positions router: {e}")
    import traceback
    traceback.print_exc()

# Include OSINT router
try:
    if osint_router:
        app.include_router(osint_router)
        print("✅ OSINT router included")
    else:
        print("⚠️ OSINT router is None, skipping")
except Exception as e:
    print(f"❌ Failed to include OSINT router: {e}")
    import traceback
    traceback.print_exc()

# Initialize Butterfly and Paradox Engines (for USE_MOCKS mode)
USE_MOCKS = os.getenv("USE_MOCKS", "true").lower() == "true"
GAME_LOOP_ENABLED = os.getenv("ENABLE_GAME_LOOP", "true").lower() == "true"
print(f"🔍 [Main] USE_MOCKS={USE_MOCKS} (from env: {os.getenv('USE_MOCKS', 'not set')})")
print(f"🔍 [Main] ENABLE_GAME_LOOP={GAME_LOOP_ENABLED} (from env: {os.getenv('ENABLE_GAME_LOOP', 'not set')})")
if USE_MOCKS and (butterfly_router or paradox_router):
    try:
        from backend.dependencies import init_butterfly_engine, init_paradox_engine
        from backend.mechanics.butterfly_engine import ButterflyEngine
        from backend.mechanics.paradox_engine import ParadoxEngine
        from backend.mocks.mock_data import (
            MockTimelineRepository,
            MockAgentRepository
        )
        from backend.core.osint_registry import get_osint_registry
        
        # Initialize with mock repositories
        timeline_repo = MockTimelineRepository()
        agent_repo = MockAgentRepository()
        osint_service = get_osint_registry()
        
        # Create Butterfly Engine
        butterfly_engine = ButterflyEngine(timeline_repo, agent_repo, osint_service)
        init_butterfly_engine(butterfly_engine)
        print("✅ Butterfly Engine initialized (mock mode)")
        
        # Create Paradox Engine (depends on Butterfly Engine)
        paradox_engine = ParadoxEngine(timeline_repo, agent_repo, butterfly_engine)
        init_paradox_engine(paradox_engine)
        print("✅ Paradox Engine initialized (mock mode)")
    except Exception as e:
        print(f"⚠️ Failed to initialize engines (mock mode): {e}")
        import traceback
        traceback.print_exc()

# --- DATABASE DEPENDENCY ---

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- PYDANTIC MODELS ---

class UserCreate(BaseModel):
    username: str
    password: str

class User(BaseModel):
    id: int
    username: str
    play_money_balance: float
    model_config = ConfigDict(from_attributes=True) 

class TokenData(BaseModel):
    username: str | None = None

class BetRequest(BaseModel):
    client_seed: str = Field(..., min_length=1, max_length=100)
    wager: float = Field(..., gt=0, le=100000.0)
    engine_name: str = Field(..., min_length=1, max_length=50)
    
    @validator('client_seed')
    def validate_client_seed(cls, v):
        """Validate client_seed for subprocess safety."""
        return StringSanitizer.validate_client_seed(v)
    
    @validator('wager')
    def validate_wager(cls, v):
        """Validate wager amount."""
        return BetAmountValidator.validate(v)

class MatchResult(BaseModel):
    message: str
    new_balance: float
    server_seed: str
    game_result: str

# --- SECURITY FUNCTIONS ---

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    
    user = db.query(DBUser).filter(DBUser.username == token_data.username).first()
    if user is None:
        raise credentials_exception
    return user

# --- API ENDPOINTS ---

# --- HEALTH CHECK ENDPOINT ---

@app.get("/health")
async def health_check():
    """Health check endpoint for container orchestration."""
    try:
        # Check database connection
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        db_status = "ok"
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "database": db_status,
        "version": "1.0.0",
    }

@app.get("/world-state")
async def get_world_state():
    """
    Returns the current 'Mind' of the AI Agent.
    """
    try:
        with open("backend/simulation/world_state.json", "r") as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        return {"error": "Agent has not run yet."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))




@app.get("/timelines")
async def get_timelines():
    """
    Returns all simulation timelines for the Butterfly Effect visualization.
    """
    try:
        from backend.simulation.timeline_manager import TimelineManager
        
        tm = TimelineManager()
        timelines = tm.list_timelines()
        
        return {
            "timelines": [
                {
                    "id": t.id,
                    "label": t.label,
                    "status": t.status.value,
                    "created_at": t.created_at,
                    "parent_id": t.parent_id,
                    "fork_reason": t.fork_reason,
                    "matchday": t.matchday,
                    "tick": t.tick,
                }
                for t in timelines
            ],
            "active_forks": len(tm.active_forks),
            "total": len(timelines),
        }
    except Exception as e:
        # Return mock data if timeline manager not available
        return {
            "timelines": [],
            "active_forks": 0,
            "total": 0,
            "error": str(e)
        }




@app.post("/timelines/snapshot")
async def create_snapshot(label: str = "MANUAL"):
    """
    Create a new timeline snapshot.
    """
    try:
        from backend.simulation.timeline_manager import TimelineManager
        
        tm = TimelineManager()
        snapshot_id = tm.create_snapshot(label)
        
        return {
            "success": True,
            "snapshot_id": snapshot_id,
            "message": f"Snapshot created: {snapshot_id}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))




@app.post("/timelines/fork")
async def create_fork(source_id: str, fork_name: str, reason: str = None):
    """
    Create a fork from an existing snapshot.
    """
    try:
        from backend.simulation.timeline_manager import TimelineManager
        
        tm = TimelineManager()
        fork_id = tm.fork_timeline(source_id, fork_name, reason)
        
        return {
            "success": True,
            "fork_id": fork_id,
            "message": f"Fork created: {fork_id}"
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))




# =============================================================================
# MARKETS API - Betting Markets from Event Orchestrator
# =============================================================================


class MarketCreate(BaseModel):
    title: str
    description: str
    domain: str = "finance"
    duration: str = "narrative"
    outcomes: list[str] = ["YES", "NO"]
    source_event_id: str | None = None


class MarketResponse(BaseModel):
    id: str
    title: str
    description: str
    domain: str
    duration: str
    status: str
    created_at: str
    expires_at: str | None
    outcomes: list[str]
    outcome_odds: dict
    total_volume: float
    virality_score: float


class BetPlacement(BaseModel):
    outcome: str = Field(..., min_length=1, max_length=10)
    amount: float = Field(..., gt=0, le=100000.0)
    
    @validator('outcome')
    def validate_outcome(cls, v):
        """Validate outcome is YES or NO."""
        v = v.upper().strip()
        if v not in ['YES', 'NO']:
            raise ValueError("Outcome must be 'YES' or 'NO'")
        return v
    
    @validator('amount')
    def validate_amount(cls, v):
        """Validate bet amount."""
        return BetAmountValidator.validate(v)


class MarketBetResponse(BaseModel):
    success: bool
    message: str
    bet_id: str | None = None
    new_balance: float | None = None
    potential_payout: float | None = None


_orchestrator = None


def get_orchestrator():
    global _orchestrator
    if _orchestrator is None:
        try:
            from backend.core.event_orchestrator import EventOrchestrator
            _orchestrator = EventOrchestrator()
        except ImportError:
            from backend.core.event_orchestrator import EventOrchestrator
            _orchestrator = EventOrchestrator()
    return _orchestrator


@app.get("/markets", response_model=dict)
@limiter.limit(RATE_LIMITS["general"])
async def list_markets(
    request: Request,
    status: str = None,
    domain: str = None,
    duration: str = None,
    limit: int = 50
):
    try:
        orchestrator = get_orchestrator()
        markets = list(orchestrator.markets.values())

        if status:
            markets = [m for m in markets if m.status.upper() == status.upper()]
        if domain:
            markets = [m for m in markets if m.domain.value == domain.lower()]
        if duration:
            markets = [m for m in markets if m.duration.value == duration.lower()]

        markets.sort(key=lambda m: m.virality_score, reverse=True)
        markets = markets[:limit]

        # Recalculate odds from CPMM before returning
        for m in markets:
            m.recalculate_odds_from_cpmm()
        
        # DEBUG: Log sample market's CPMM state
        if markets and len(markets) > 0:
            sample = markets[0]
            print(f"🔍 [MARKETS DEBUG] Sample market {sample.id}:")
            print(f"   yes_shares: {sample.yes_shares}")
            print(f"   no_shares: {sample.no_shares}")
            print(f"   outcome_odds: {sample.outcome_odds}")
            print(f"   total_volume: {sample.total_volume}")

        return {
            "markets": [
                {
                    "id": m.id,
                    "title": m.title,
                    "description": m.description,
                    "domain": m.domain.value,
                    "duration": m.duration.value,
                    "status": m.status,
                    "created_at": m.created_at.isoformat(),
                    "expires_at": m.expires_at.isoformat() if m.expires_at else None,
                    "outcomes": m.outcomes,
                    "outcome_odds": m.outcome_odds,  # Now recalculated from CPMM
                    "total_volume": m.total_volume,
                    "virality_score": m.virality_score,
                    # Include CPMM state for debugging
                    "yes_shares": m.yes_shares,
                    "no_shares": m.no_shares,
                }
                for m in markets
            ],
            "total": len(orchestrator.markets),
            "filtered": len(markets),
        }
    except Exception as e:
        return {
            "markets": [],
            "total": 0,
            "filtered": 0,
            "error": str(e)
        }


@app.get("/markets/trending", response_model=dict)
async def get_trending_markets(limit: int = 3):
    """
    Get trending markets sorted by 24h volume.
    Returns unique markets (no duplicates) sorted by total_volume descending.
    """
    try:
        orchestrator = get_orchestrator()
        markets = list(orchestrator.markets.values())
        
        # Filter only OPEN markets
        open_markets = [m for m in markets if m.status.upper() == "OPEN"]
        
        # Remove duplicates by market title (normalized)
        seen_titles = set()
        unique_markets = []
        for market in open_markets:
            # Normalize title for comparison (lowercase, remove special chars)
            normalized_title = market.title.lower().strip()
            if normalized_title not in seen_titles:
                seen_titles.add(normalized_title)
                unique_markets.append(market)
        
        # Sort by total_volume (descending), then by virality_score as tiebreaker
        unique_markets.sort(
            key=lambda m: (m.total_volume, m.virality_score),
            reverse=True
        )
        
        # Take top N markets
        trending = unique_markets[:limit]
        
        # Recalculate odds from CPMM before returning
        for m in trending:
            m.recalculate_odds_from_cpmm()
        
        return {
            "markets": [
                {
                    "id": m.id,
                    "title": m.title,
                    "description": m.description,
                    "domain": m.domain.value,
                    "duration": m.duration.value,
                    "status": m.status,
                    "created_at": m.created_at.isoformat(),
                    "expires_at": m.expires_at.isoformat() if m.expires_at else None,
                    "outcomes": m.outcomes,
                    "outcome_odds": m.outcome_odds,  # Now recalculated from CPMM
                    "total_volume": m.total_volume,
                    "virality_score": m.virality_score,
                    # Include CPMM state for debugging
                    "yes_shares": m.yes_shares,
                    "no_shares": m.no_shares,
                }
                for m in trending
            ],
            "total": len(trending),
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            "markets": [],
            "total": 0,
            "error": str(e)
        }


@app.get("/markets/stats")
async def get_market_stats():
    try:
        orchestrator = get_orchestrator()
        markets = list(orchestrator.markets.values())

        total_volume = sum(m.total_volume for m in markets)
        by_domain: Dict[str, int] = {}
        by_duration: Dict[str, int] = {}
        by_status: Dict[str, int] = {}

        for m in markets:
            domain = m.domain.value
            by_domain[domain] = by_domain.get(domain, 0) + 1

            duration = m.duration.value
            by_duration[duration] = by_duration.get(duration, 0) + 1

            status = m.status
            by_status[status] = by_status.get(status, 0) + 1

        return {
            "total_markets": len(markets),
            "total_volume": total_volume,
            "by_domain": by_domain,
            "by_duration": by_duration,
            "by_status": by_status,
            "orchestrator_stats": {
                "events_processed": getattr(orchestrator, "_events_processed", 0),
                "markets_auto_created": getattr(orchestrator, "_markets_created", 0),
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/markets/{market_id}")
async def get_market(market_id: str):
    try:
        orchestrator = get_orchestrator()

        if market_id not in orchestrator.markets:
            raise HTTPException(status_code=404, detail=f"Market {market_id} not found")

        m = orchestrator.markets[market_id]
        agents = orchestrator.dispatcher.active_agents.get(market_id, [])
        
        # Recalculate odds from CPMM before returning
        m.recalculate_odds_from_cpmm()

        return {
            "id": m.id,
            "event_id": m.event_id,
            "title": m.title,
            "description": m.description,
            "domain": m.domain.value,
            "duration": m.duration.value,
            "status": m.status,
            "created_at": m.created_at.isoformat(),
            "expires_at": m.expires_at.isoformat() if m.expires_at else None,
            "outcomes": m.outcomes,
            "outcome_odds": m.outcome_odds,  # Now recalculated from CPMM
            "yes_shares": m.yes_shares,
            "no_shares": m.no_shares,
            "total_volume": m.total_volume,
            "virality_score": m.virality_score,
            "active_agents": len(agents),
            "source_event": {
                "id": m.source_event.id,
                "title": m.source_event.title,
                "source": m.source_event.source,
                "sentiment": m.source_event.sentiment,
            } if m.source_event else None,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/markets")
async def create_market(market: MarketCreate):
    try:
        from backend.core.event_orchestrator import RawEvent, EventDomain, BetDuration
    except ImportError:
        from backend.core.event_orchestrator import RawEvent, EventDomain, BetDuration

    try:
        orchestrator = get_orchestrator()

        event = RawEvent(
            id=f"manual_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            title=market.title,
            description=market.description,
            source="MANUAL",
            url="",
            published_at=datetime.now(timezone.utc),
            domain=EventDomain(market.domain),
            virality_score=75,
        )

        betting_market = orchestrator.create_market(event)

        if market.outcomes and market.outcomes != ["YES", "NO"]:
            betting_market.outcomes = market.outcomes
            betting_market.outcome_odds = {
                o: 1.0 / len(market.outcomes) for o in market.outcomes
            }

        agents = orchestrator.dispatch_agents(betting_market)

        return {
            "success": True,
            "market_id": betting_market.id,
            "message": f"Market created with {len(agents)} agents",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def get_user_or_wallet(
    token: Optional[str] = Header(None, alias="Authorization"),
    wallet_address: Optional[str] = Header(None, alias="X-Wallet-Address"),
    db: Session = Depends(get_db)
):
    """Get user from JWT token OR wallet address."""
    try:
        print(f"🔍 [AUTH] get_user_or_wallet called - token: {bool(token)}, wallet: {wallet_address}")
        
        # Try JWT authentication first
        if token and token.startswith("Bearer "):
            try:
                token_value = token.replace("Bearer ", "")
                payload = jwt.decode(token_value, SECRET_KEY, algorithms=[ALGORITHM])
                username: str = payload.get("sub")
                if username:
                    user = db.query(DBUser).filter(DBUser.username == username).first()
                    if user:
                        print(f"🔍 [AUTH] Found user via JWT: {user.username}")
                        return user
            except (JWTError, Exception) as e:
                print(f"🔍 [AUTH] JWT auth failed: {e}")
                pass  # Fall through to wallet auth
        
        # Try wallet address authentication
        if wallet_address:
            wallet_addr_lower = wallet_address.lower()
            print(f"🔍 [AUTH] Looking up wallet: {wallet_addr_lower}")
            # Find or create user by wallet address
            user = db.query(DBUser).filter(DBUser.wallet_address == wallet_addr_lower).first()
            if not user:
                print(f"🔍 [AUTH] Creating new user for wallet: {wallet_addr_lower}")
                # Create a new user for this wallet address
                user = DBUser(
                    username=f"wallet_{wallet_addr_lower[:8]}",
                    email=f"{wallet_addr_lower[:8]}@wallet.local",
                    hashed_password="",  # No password for wallet users
                    wallet_address=wallet_addr_lower,
                    play_money_balance=1000.0  # Starting balance
                )
                db.add(user)
                db.commit()
                db.refresh(user)
                print(f"🔍 [AUTH] Created user: {user.username}, balance: {user.play_money_balance}")
            else:
                print(f"🔍 [AUTH] Found existing user: {user.username}, balance: {user.play_money_balance}")
            return user
        
        # No authentication provided
        print(f"🔍 [AUTH] No authentication provided")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials. Provide either JWT token or wallet address.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"❌ [AUTH ERROR] Exception in get_user_or_wallet:")
        print(f"   Error: {str(e)}")
        print(f"   Type: {type(e).__name__}")
        print(f"   Traceback:\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication error: {str(e)}",
        )

@app.post("/markets/{market_id}/bet")
async def place_bet(
    market_id: str,
    bet: BetPlacement,
    current_user: Annotated[DBUser, Depends(get_user_or_wallet)],
    db: Session = Depends(get_db)
):
    try:
        import traceback
        print(f"🔍 [BET] Starting bet placement for market {market_id}")
        print(f"🔍 [BET] User: {current_user.username}, Balance: {current_user.play_money_balance}")
        print(f"🔍 [BET] Bet: {bet.outcome} ${bet.amount}")
        
        orchestrator = get_orchestrator()

        if market_id not in orchestrator.markets:
            raise HTTPException(status_code=404, detail=f"Market {market_id} not found")

        market = orchestrator.markets[market_id]

        if market.status != "OPEN":
            raise HTTPException(status_code=400, detail=f"Market is {market.status}, not accepting bets")

        if bet.outcome not in market.outcomes:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid outcome. Choose from: {market.outcomes}"
            )

        if current_user.play_money_balance < bet.amount:
            raise HTTPException(status_code=400, detail="Insufficient balance")

        # Use CPMM for odds calculation
        from backend.core.cpmm import CPMM
        
        # Initialize CPMM with current market liquidity
        cpmm = CPMM(initial_liquidity=1.0)  # Will be overridden
        cpmm.state.yes_shares = getattr(market, 'yes_shares', 1000.0)
        cpmm.state.no_shares = getattr(market, 'no_shares', 1000.0)
        
        # DEBUG: Log shares BEFORE bet
        print(f"🔍 [BET DEBUG] Market {market_id} BEFORE bet:")
        print(f"   yes_shares: {cpmm.state.yes_shares}")
        print(f"   no_shares: {cpmm.state.no_shares}")
        print(f"   bet: {bet.outcome} ${bet.amount}")
        
        # Get current odds before trade
        current_odds = cpmm.get_current_odds()
        current_price = current_odds.get(bet.outcome, 0.5)
        
        # Execute trade through CPMM
        shares_received, price_impact, new_odds = cpmm.execute_trade(
            outcome=bet.outcome,
            amount_in=bet.amount,
            apply_fee=True
        )
        
        # Calculate potential payout (shares * final price if outcome wins)
        # For binary markets, if you win, you get: shares * (1 / final_price)
        # Simplified: payout = bet_amount * (1 / current_price) * (1 - fee)
        potential_payout = bet.amount * (1 / current_price) * 0.97  # 3% fee
        
        # Update user balance
        current_user.play_money_balance -= bet.amount
        db.commit()
        db.refresh(current_user)

        # Update market state
        market.total_volume += bet.amount
        market.yes_shares = cpmm.state.yes_shares
        market.no_shares = cpmm.state.no_shares
        market.outcome_odds = new_odds
        
        # DEBUG: Log shares AFTER bet
        print(f"🔍 [BET DEBUG] Market {market_id} AFTER bet:")
        print(f"   yes_shares: {market.yes_shares}")
        print(f"   no_shares: {market.no_shares}")
        print(f"   new_odds: {new_odds}")
        
        # CRITICAL: Save markets state after bet to persist CPMM state
        orchestrator._save_markets_state()
        
        # Verify no-arbitrage (YES + NO should ≈ 1.0)
        total_odds = sum(new_odds.values())
        if abs(total_odds - 1.0) > 0.01:
            # Normalize if slightly off due to floating point
            for outcome in new_odds:
                new_odds[outcome] = new_odds[outcome] / total_odds
            market.outcome_odds = new_odds
        
        bet_id = f"BET_{market_id}_{datetime.now().strftime('%H%M%S')}"

        return MarketBetResponse(
            success=True,
            message=f"Bet placed on {bet.outcome}. Price impact: {price_impact:.2%}",
            bet_id=bet_id,
            new_balance=current_user.play_money_balance,
            potential_payout=round(potential_payout, 2),
        )
    except HTTPException:
        raise  # Re-raise HTTP exceptions as-is
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"❌ [BET ERROR] Exception in place_bet:")
        print(f"   Error: {str(e)}")
        print(f"   Type: {type(e).__name__}")
        print(f"   Traceback:\n{error_trace}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/markets/{market_id}/quote")
@limiter.limit(RATE_LIMITS["general"])
async def get_market_quote(
    request: Request,
    market_id: str,
    outcome: str,
    amount: float
):
    """
    Get a quote for placing a bet (price impact, shares received, new odds).
    Useful for showing users what they'll get before placing the bet.
    """
    try:
        orchestrator = get_orchestrator()
        
        if market_id not in orchestrator.markets:
            raise HTTPException(status_code=404, detail=f"Market {market_id} not found")
        
        market = orchestrator.markets[market_id]
        
        if market.status != "OPEN":
            raise HTTPException(status_code=400, detail=f"Market is {market.status}")
        
        if outcome not in market.outcomes:
            raise HTTPException(status_code=400, detail=f"Invalid outcome: {outcome}")
        
        if amount <= 0:
            raise HTTPException(status_code=400, detail="Amount must be positive")
        
        # Use CPMM to calculate quote
        from backend.core.cpmm import CPMM
        
        cpmm = CPMM(initial_liquidity=1.0)
        cpmm.state.yes_shares = getattr(market, 'yes_shares', 1000.0)
        cpmm.state.no_shares = getattr(market, 'no_shares', 1000.0)
        
        # Get current odds
        current_odds = cpmm.get_current_odds()
        current_price = current_odds.get(outcome, 0.5)
        
        # Calculate what would happen if bet is placed (without executing)
        # Create a temporary CPMM to simulate the trade
        temp_cpmm = CPMM(initial_liquidity=1.0)
        temp_cpmm.state.yes_shares = cpmm.state.yes_shares
        temp_cpmm.state.no_shares = cpmm.state.no_shares
        
        shares_received, price_impact, new_odds = temp_cpmm.execute_trade(
            outcome=outcome,
            amount_in=amount,
            apply_fee=True
        )
        
        # Calculate potential payout
        potential_payout = amount * (1 / current_price) * 0.97  # 3% fee
        
        return {
            "market_id": market_id,
            "outcome": outcome,
            "amount": amount,
            "current_price": round(current_price, 4),
            "current_odds": {k: round(v, 4) for k, v in current_odds.items()},
            "shares_received": round(shares_received, 2),
            "price_impact": round(price_impact, 4),
            "new_odds": {k: round(v, 4) for k, v in new_odds.items()},
            "potential_payout": round(potential_payout, 2),
            "fee": round(amount * 0.03, 2),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/markets/refresh")
async def refresh_markets():
    try:
        orchestrator = get_orchestrator()
        summary = orchestrator.process_all()
        return {
            "success": True,
            "events_ingested": summary.get("events_ingested", 0),
            "high_virality_events": summary.get("high_virality_events", 0),
            "markets_created": summary.get("markets_created", 0),
            "total_active_markets": len(orchestrator.get_active_markets()),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# ENHANCED TIMELINES API
# =============================================================================


@app.get("/timelines/{timeline_id}")
async def get_timeline_detail(timeline_id: str):
    try:
        from backend.simulation.timeline_manager import TimelineManager
    except ImportError:
        from backend.simulation.timeline_manager import TimelineManager

    try:
        tm = TimelineManager()
        all_timelines = tm.list_timelines()
        
        # Handle special case: "REALITY" is the master timeline
        if timeline_id.upper() == "REALITY":
            # Find the master timeline (status='master' or no parent_id)
            master_timeline = None
            for t in all_timelines:
                if t.status.value == "master" or (t.parent_id is None and t.id != "REALITY"):
                    master_timeline = t
                    break
            
            # If no master found, create a mock reality timeline
            if not master_timeline:
                children = [t for t in all_timelines if t.parent_id is None]
                return {
                    "id": "REALITY",
                    "label": "Master Reality",
                    "status": "master",
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "parent_id": None,
                    "fork_reason": None,
                    "matchday": None,
                    "tick": 0,
                    "children": [
                        {
                            "id": c.id,
                            "label": c.label,
                            "status": c.status.value,
                            "fork_reason": c.fork_reason,
                        }
                        for c in children
                    ],
                    "has_snapshot_data": False,
                }
            
            timeline_id = master_timeline.id
        
        # Find timeline by ID
        timeline = None
        for t in all_timelines:
            if t.id == timeline_id:
                timeline = t
                break

        if not timeline:
            raise HTTPException(status_code=404, detail=f"Timeline {timeline_id} not found")

        children = [t for t in all_timelines if t.parent_id == timeline_id]

        snapshot_data = None
        try:
            snapshot_data = tm.load_state(timeline_id, "world_state.json")
        except Exception:
            snapshot_data = None

        # Safely serialize created_at
        created_at_str = timeline.created_at
        if not isinstance(created_at_str, str):
            if hasattr(timeline.created_at, 'isoformat'):
                created_at_str = timeline.created_at.isoformat()
            else:
                created_at_str = str(timeline.created_at)
        
        return {
            "id": timeline.id,
            "label": timeline.label,
            "status": timeline.status.value,
            "created_at": created_at_str,
            "parent_id": timeline.parent_id,
            "fork_reason": timeline.fork_reason,
            "matchday": timeline.matchday,
            "tick": timeline.tick,
            "children": [
                {
                    "id": c.id,
                    "label": c.label,
                    "status": c.status.value,
                    "fork_reason": c.fork_reason,
                }
                for c in children
            ],
            "has_snapshot_data": snapshot_data is not None,
        }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/timelines/{timeline_id}/compare/{other_id}")
async def compare_timelines(timeline_id: str, other_id: str):
    try:
        from backend.simulation.timeline_manager import TimelineManager
    except ImportError:
        from backend.simulation.timeline_manager import TimelineManager

    try:
        tm = TimelineManager()

        timeline_a = tm.get_timeline(timeline_id)
        timeline_b = tm.get_timeline(other_id)

        if not timeline_a:
            raise HTTPException(status_code=404, detail=f"Timeline {timeline_id} not found")
        if not timeline_b:
            raise HTTPException(status_code=404, detail=f"Timeline {other_id} not found")

        data_a = tm.load_snapshot(timeline_id)
        data_b = tm.load_snapshot(other_id)

        divergence = []
        if data_a and data_b:
            if "global_tension" in data_a and "global_tension" in data_b:
                tension_a = data_a["global_tension"]
                tension_b = data_b["global_tension"]
                delta = ((tension_b - tension_a) / max(tension_a, 0.01)) * 100
                divergence.append({
                    "metric": "Tension Score",
                    "timeline_a": f"{tension_a:.2f}",
                    "timeline_b": f"{tension_b:.2f}",
                    "delta": f"{delta:+.1f}%"
                })

            if "tick" in data_a and "tick" in data_b:
                divergence.append({
                    "metric": "Simulation Tick",
                    "timeline_a": str(data_a.get("tick", 0)),
                    "timeline_b": str(data_b.get("tick", 0)),
                    "delta": str(data_b.get("tick", 0) - data_a.get("tick", 0))
                })

        return {
            "timeline_a": {
                "id": timeline_a.id,
                "label": timeline_a.label,
                "status": timeline_a.status.value,
            },
            "timeline_b": {
                "id": timeline_b.id,
                "label": timeline_b.label,
                "status": timeline_b.status.value,
            },
            "divergence_metrics": divergence,
            "common_ancestor": timeline_a.parent_id if timeline_a.parent_id == timeline_b.parent_id else None,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- NEW: x402 PREMIUM CONTENT ENDPOINT ---
@app.get("/premium-intel")
async def get_premium_intel(
    authorization: Annotated[str | None, Header()] = None,
    x_payment_token: Annotated[str | None, Header(alias="X-Payment-Token")] = None
):
    """
    A Mock x402 Endpoint.
    1. First request (No Auth) -> Returns 402 Payment Required.
    2. Second request (With Auth) -> Returns Secret Data.
    """
    # SIMULATION: If no signature is provided, demand payment
    if not authorization:
        # Generate a challenge message for the agent to sign
        challenge_message = f"I authorize payment of 0.01 USDC for Intel at {datetime.now().timestamp()}"
        
        # Return 402 Error with the "Bill"
        raise HTTPException(
            status_code=402,
            detail={
                "message": challenge_message,
                "token": "session_12345_secure_token",
                "cost": "0.01 USDC"
            }
        )
    
    # SIMULATION: In a real app, we would verify the cryptographic signature here.
    # For this demo, if they sent *any* header, we assume they paid.
    print(f"💰 PAYMENT RECEIVED! Signature: {authorization[:20]}...")
    
    return {
        "secret_info": "The 'Blue Nation' is secretly running out of oil. War probability +15%."
    }

@app.get("/")
async def get_root():
    return {"message": "Welcome to the AI Marketplace API!"}

@app.post("/users/", response_model=User)
async def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(DBUser).filter(DBUser.username == user.username).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    hashed_password = get_password_hash(user.password)
    new_user = DBUser(username=user.username, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.post("/token")
@limiter.limit(RATE_LIMITS["auth"])
async def login_for_access_token(
    request: Request,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_db)
):
    print(f"🔍 [AUTH] Login attempt for username: {form_data.username}")
    
    user = db.query(DBUser).filter(DBUser.username == form_data.username).first()
    
    if not user:
        print(f"❌ [AUTH] User '{form_data.username}' not found")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user has a password (wallet users have empty hashed_password)
    if not user.hashed_password or user.hashed_password == "":
        print(f"❌ [AUTH] User '{form_data.username}' is a wallet-only user (no password set)")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="This account uses wallet authentication. Please connect your wallet instead.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify password
    if not verify_password(form_data.password, user.hashed_password):
        print(f"❌ [AUTH] Incorrect password for user '{form_data.username}'")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    print(f"✅ [AUTH] Login successful for user '{form_data.username}'")
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me", response_model=User)
async def read_users_me(current_user: Annotated[User, Depends(get_current_user)]):
    return current_user


@app.get("/users/me/simulations")
async def get_user_simulations(current_user: Annotated[DBUser, Depends(get_current_user)]):
    """Get user's active simulations/timeline forks."""
    try:
        from backend.simulation.timeline_manager import TimelineManager
        tm = TimelineManager()
        
        # Get all timelines and filter for user's forks
        # For now, return all active forks (in production, filter by user_id)
        all_timelines = tm.list_timelines()
        active_forks = [
            {
                "id": t.id,
                "label": t.label,
                "status": t.status.value,
                "created_at": t.created_at.isoformat() if hasattr(t.created_at, 'isoformat') else str(t.created_at),
                "fork_reason": t.fork_reason,
                "parent_id": t.parent_id,
            }
            for t in all_timelines
            if t.status.value == "active" and t.parent_id is not None
        ]
        
        return {
            "simulations": active_forks,
            "total": len(active_forks),
        }
    except Exception as e:
        # Return empty list on error
        return {
            "simulations": [],
            "total": 0,
            "error": str(e)
        }

@app.post("/play-match/", response_model=MatchResult)
async def play_match(
    bet: BetRequest,
    current_user: Annotated[DBUser, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    if bet.wager <= 0:
        raise HTTPException(status_code=400, detail="Wager must be positive")
    if current_user.play_money_balance < bet.wager:
        raise HTTPException(status_code=400, detail="Insufficient funds")

    server_seed = os.urandom(16).hex()
    nonce = str(datetime.now(timezone.utc).timestamp())
    
    python_executable = sys.executable
    engine_script = ""
    
    # Router for different game engines
    if bet.engine_name == "geopolitics":
        engine_script = "backend/simulation/sim_geopolitics_engine.py"
    elif bet.engine_name == "market":
        engine_script = "backend/simulation/sim_market_engine.py"
    elif bet.engine_name == "election":
        engine_script = "backend/simulation/sim_election_engine.py"
    elif bet.engine_name == "duel":
        engine_script = "backend/simulation/digital_twin_engine.py"
    elif bet.engine_name == "chess":
        engine_script = "backend/simulation/engine.py"
    elif bet.engine_name == "football":
        engine_script = "backend/simulation/sim_football_engine.py"
    else:
        raise HTTPException(status_code=400, detail="Invalid engine name")
    
    command = [
        python_executable, 
        engine_script, 
        server_seed, 
        bet.client_seed, 
        nonce
    ]
    
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True,
            timeout=30 
        )
        
        game_result = result.stdout.strip().split('\n')[-1]
        
        if "ERROR" in game_result:
            raise HTTPException(status_code=500, detail=f"Game Engine Error: {game_result}")

    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"Engine script failed: {e.stderr}")
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=500, detail="Game engine timed out")

    message = ""    
    
    # Settlement Logic based on Engine Type
    if bet.engine_name == "geopolitics":
        if game_result == "WAR_DECLARED":
            current_user.play_money_balance += bet.wager
            message = "You bet on WAR and won!"
        elif game_result == "PEACE_MAINTAINED":
            current_user.play_money_balance -= bet.wager
            message = "You bet on WAR, but peace was maintained. You lost."
        else:
            message = "The simulation was a draw."

    elif bet.engine_name == "market":
        if game_result == "SAPL_UP":
            current_user.play_money_balance += bet.wager
            message = "You bet on SAPL to go UP and won!"
        else:
            current_user.play_money_balance -= bet.wager
            message = f"You bet on SAPL UP, but the result was {game_result}. You lost."

    elif bet.engine_name == "election":
        if game_result == "CANDIDATE_A_WINS":
            current_user.play_money_balance += bet.wager
            message = "You bet on Candidate A and won!"
        else:
            current_user.play_money_balance -= bet.wager
            message = "You bet on Candidate A, but Candidate B won. You lost."
            
    elif bet.engine_name == "duel":
        if game_result == "AGENT_A_WINS":
            current_user.play_money_balance += bet.wager
            message = "You bet on Agent A and won!"
        else:
            current_user.play_money_balance -= bet.wager
            message = f"You bet on Agent A, but the result was {game_result}. You lost."

    elif bet.engine_name == "chess":
        if game_result == "1-0":
            # White wins - user wins
            current_user.play_money_balance += bet.wager
            message = "You bet on White and won!"
        elif game_result == "0-1":
            # Black wins - user loses
            current_user.play_money_balance -= bet.wager
            message = "You bet on White, but Black won. You lost."
        elif game_result == "1/2-1/2":
            # Draw - return stake (push)
            message = "The game was a draw. Your stake is returned."
        else:
            # Unknown result - return stake to be safe
            message = f"Unexpected game result: {game_result}. Your stake is returned."

    elif bet.engine_name == "football":
        # Football: HOME_WIN, AWAY_WIN, DRAW
        if game_result == "HOME_WIN":
            current_user.play_money_balance += bet.wager
            message = "You bet on HOME and won!"
        elif game_result == "AWAY_WIN":
            current_user.play_money_balance -= bet.wager
            message = "You bet on HOME, but AWAY won. You lost."
        else:  # DRAW
            current_user.play_money_balance -= bet.wager * 0.5  # Half loss on draw
            message = "The match was a DRAW. Half stake returned."

    # Final Database Update (Only happens once now!)
    db.commit()
    db.refresh(current_user)
    
    return MatchResult(
        message=message,
        new_balance=current_user.play_money_balance,
        server_seed=server_seed,
        game_result=game_result
    )


# =============================================================================
# EVOLUTION STATUS API
# =============================================================================

@app.get("/evolution/status")
async def get_evolution_status(domain: str = "financial"):
    """
    Get current evolution status for a domain.
    Used by the frontend Evolution Status widget.
    """
    import random
    
    # Try to load real data
    try:
        from backend.core.persistence_manager import get_persistence_manager
        pm = get_persistence_manager()
        
        # Load evolution history if available
        history = pm.load(f"{domain}_evolution", default=None)
        
        if history and len(history) > 0:
            latest = history[-1]
            return {
                "generation": latest.get("generation", 0),
                "population_size": latest.get("population_size", 100),
                "average_fitness": latest.get("average_fitness", 50),
                "fitness_change": latest.get("fitness_change", 0),
                "dominant_archetype": latest.get("dominant_archetype", "SHARK"),
                "dominant_percentage": latest.get("dominant_percentage", 25),
                "archetype_distribution": latest.get("archetype_distribution", {}),
                "is_learning": latest.get("is_learning", True),
                "last_evolution": latest.get("timestamp", datetime.now(timezone.utc).isoformat()),
            }
    except Exception as e:
        print(f"⚠️ Could not load evolution data: {e}")
    
    # Return mock data for demonstration
    archetypes = ["SHARK", "WHALE", "DEGEN", "VALUE", "MOMENTUM", "CONTRARIAN"]
    distribution = {}
    remaining = 100
    
    for i, arch in enumerate(archetypes):
        if i == len(archetypes) - 1:
            distribution[arch] = remaining
        else:
            val = random.randint(5, min(45, remaining - (len(archetypes) - i - 1) * 5))
            distribution[arch] = val
            remaining -= val
    
    dominant = max(distribution, key=distribution.get)
    
    return {
        "generation": random.randint(5, 50),
        "population_size": random.randint(70, 100),
        "average_fitness": round(50 + random.random() * 50, 1),
        "fitness_change": round((random.random() - 0.3) * 30, 1),
        "dominant_archetype": dominant,
        "dominant_percentage": distribution[dominant],
        "archetype_distribution": distribution,
        "is_learning": random.random() > 0.2,
        "last_evolution": datetime.now(timezone.utc).isoformat(),
    }


# =============================================================================
# OSINT API
# =============================================================================

@app.get("/osint/status")
async def osint_status():
    """Get status of the signal intelligence network."""
    return osint.get_full_status()


@app.get("/osint/scan")
async def osint_scan():
    """Force a scan of all intelligence sources."""
    signals = await osint.scan_all()
    return {"signals_found": len(signals), "status": osint.get_full_status()}


@app.get("/osint/missions/{domain}")
async def osint_missions(domain: str):
    """Get active missions for a specific domain."""
    missions = osint.generate_domain_missions(domain)
    return {"missions": [m.to_dict() for m in missions]}


# =============================================================================
# HANDLER API (AI-Assisted Trading Guidance)
# =============================================================================

class HandlerChatRequest(BaseModel):
    message: str
    handler_id: str = "control"
    wallet_address: Optional[str] = None


@app.post("/api/handler/chat")
async def handler_chat(request: HandlerChatRequest):
    """
    Chat endpoint for handler AI assistance.
    
    Args:
        request: HandlerChatRequest with message, handler_id, wallet_address
        
    Returns:
        Handler's response
    """
    try:
        from backend.agents.handler_brain import generate_handler_response
        
        # Get handler personality (for now, use default)
        # TODO: Load from database or config
        default_personality = """You are CONTROL, a senior intelligence analyst at Echelon.

TONE: Professional, measured, occasionally dry wit.
STYLE: Lead with assessment, then supporting data, then recommendation.
FORMAT: Keep responses concise (2-4 sentences). Use trading terminology.

NEVER:
- Use emojis
- Be overly casual
- Give financial advice disclaimers
- Break character

CONTEXT: You have access to the user's positions, recent signals, and market state.
Provide actionable intelligence based on this context."""
        
        # Get user context (mock for now)
        # TODO: Fetch real context from database based on wallet_address
        context = {
            "positions": [],
            "signals": [],
            "market_state": None,
            "operation": None,
        }
        
        # Generate response
        response = await generate_handler_response(
            default_personality,
            request.message,
            context
        )
        
        return {"response": response}
        
    except Exception as e:
        print(f"Error in handler chat: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Handler service error: {str(e)}"
        )


# =============================================================================
# OSINT API (with /api prefix for frontend compatibility)
# =============================================================================

@app.get("/api/osint/signals")
async def get_osint_signals():
    """Get all active OSINT signals for the frontend."""
    try:
        # Get all active signals from the registry
        signals = osint.active_signals
        
        # Convert to dict format for JSON response
        signals_data = [s.to_dict() for s in signals]
        
        return {
            "signals": signals_data,
            "total": len(signals_data),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "defcon_level": osint.base_detector.defcon_level.value,
            "defcon_name": osint.base_detector.defcon_level.name,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching OSINT signals: {str(e)}")


@app.get("/api/osint/tension")
async def get_osint_tension():
    """Get global tension index from OSINT signals."""
    try:
        detector = osint.base_detector
        status = detector.get_status()
        
        # Get tension from situation room if available, otherwise use OSINT
        try:
            from backend.api.situation_room import state as situation_room_state
            tension_index = situation_room_state.tension_index
            chaos_index = situation_room_state.chaos_index
        except:
            # Fallback to OSINT-based tension
            # Map DEFCON to tension (inverse: DEFCON 1 = high tension)
            defcon_to_tension = {
                1: 90.0,  # DEFCON 1 = Critical
                2: 75.0,  # DEFCON 2 = High Alert
                3: 50.0,  # DEFCON 3 = Alert
                4: 30.0,  # DEFCON 4 = Watch
                5: 15.0,  # DEFCON 5 = Normal
            }
            tension_index = defcon_to_tension.get(status["defcon_level"], 25.0)
            chaos_index = (100 - tension_index) * 0.3  # Rough estimate
        
        return {
            "tension_index": round(tension_index, 2),
            "tension_level": status["defcon_name"],
            "peace_percentage": round(100 - tension_index, 2),
            "chaos_index": round(chaos_index, 2),
            "trend": "rising" if status["active_signals"] > 5 else "falling",
            "defcon_level": status["defcon_level"],
            "active_signals": status["active_signals"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching tension data: {str(e)}")


if __name__ == "__main__":
    # When running as a module (python -m backend.main), the app string needs the full path
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
