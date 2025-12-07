import uvicorn
import json
import subprocess 
import re 
import os
import sys 
from fastapi import FastAPI, Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm 
from sqlalchemy.orm import Session
from sqlalchemy import text
from passlib.context import CryptContext
from pydantic import BaseModel, ConfigDict
from typing import Annotated 
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone

# Import CORSMiddleware
from fastapi.middleware.cors import CORSMiddleware

# --- IMPORTS ---
from backend.core.database import SessionLocal, engine, Base, User as DBUser
from backend.core.osint_registry import get_osint_registry

# Auto Uploader Config
from backend.core.autouploader import AutoUploadConfig

# Payments Router
from backend.payments.routes import router as payments_router

# Situation Room Router
try:
    from backend.api.situation_room_routes import router as situation_room_router
except ImportError:
    situation_room_router = None

# Initialize
osint = get_osint_registry()

# --- CONFIGURATION ---

Base.metadata.create_all(bind=engine)

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token") 

SECRET_KEY = "a_very_secret_key_for_jwt_replace_this"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

app = FastAPI()

# --- CORS MIDDLEWARE ---
origins = [
    "http://localhost:3000",
    "http://localhost:3001",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
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

# Include Situation Room router if available
try:
    if situation_room_router:
        app.include_router(situation_room_router)
        print("✅ Situation Room router included")
    else:
        print("⚠️ Situation Room router is None, skipping")
except Exception as e:
    print(f"❌ Failed to include Situation Room router: {e}")
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
    client_seed: str
    wager: float
    engine_name: str

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
    outcome: str
    amount: float


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
async def list_markets(
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
                    "outcome_odds": m.outcome_odds,
                    "total_volume": m.total_volume,
                    "virality_score": m.virality_score,
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
            "outcome_odds": m.outcome_odds,
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


@app.post("/markets/{market_id}/bet")
async def place_bet(
    market_id: str,
    bet: BetPlacement,
    current_user: Annotated[DBUser, Depends(get_current_user)],
    db: Session = Depends(get_db)
):
    try:
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

        odds = market.outcome_odds.get(bet.outcome, 0.5)
        potential_payout = bet.amount * (1 / odds) * 0.95

        current_user.play_money_balance -= bet.amount
        db.commit()
        db.refresh(current_user)

        market.total_volume += bet.amount
        bet_id = f"BET_{market_id}_{datetime.now().strftime('%H%M%S')}"

        return MarketBetResponse(
            success=True,
            message=f"Bet placed on {bet.outcome}",
            bet_id=bet_id,
            new_balance=current_user.play_money_balance,
            potential_payout=round(potential_payout, 2),
        )
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
        timeline = tm.get_timeline(timeline_id)

        if not timeline:
            raise HTTPException(status_code=404, detail=f"Timeline {timeline_id} not found")

        all_timelines = tm.list_timelines()
        children = [t for t in all_timelines if t.parent_id == timeline_id]

        snapshot_data = None
        try:
            snapshot_data = tm.load_snapshot(timeline_id)
        except Exception:
            snapshot_data = None

        return {
            "id": timeline.id,
            "label": timeline.label,
            "status": timeline.status.value,
            "created_at": timeline.created_at,
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
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_db)
):
    user = db.query(DBUser).filter(DBUser.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me", response_model=User)
async def read_users_me(current_user: Annotated[User, Depends(get_current_user)]):
    return current_user

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
            current_user.play_money_balance += bet.wager
            message = "You bet on White and won!"
        else:
            current_user.play_money_balance -= bet.wager
            message = f"You bet on White, but the result was {game_result}. You lost."

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


if __name__ == "__main__":
    # When running as a module (python -m backend.main), the app string needs the full path
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
