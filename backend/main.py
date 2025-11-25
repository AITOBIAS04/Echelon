import uvicorn
import json
import subprocess 
import re 
import os
import sys 
from fastapi import FastAPI, Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm 
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from pydantic import BaseModel, ConfigDict
from typing import Annotated 
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone

# Import CORSMiddleware
from fastapi.middleware.cors import CORSMiddleware

from core.database import SessionLocal, engine, Base, User as DBUser

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

@app.get("/world-state")
async def get_world_state():
    """
    Returns the current 'Mind' of the AI Agent.
    """
    try:
        with open("simulation/world_state.json", "r") as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        return {"error": "Agent has not run yet."}
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
        engine_script = "simulation/sim_geopolitics_engine.py"
    elif bet.engine_name == "market":
        engine_script = "simulation/sim_market_engine.py"
    elif bet.engine_name == "election":
        engine_script = "simulation/sim_election_engine.py"
    elif bet.engine_name == "duel":
        engine_script = "simulation/digital_twin_engine.py"
    elif bet.engine_name == "chess":
        engine_script = "simulation/engine.py"
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

    # Final Database Update (Only happens once now!)
    db.commit()
    db.refresh(current_user)
    
    return MatchResult(
        message=message,
        new_balance=current_user.play_money_balance,
        server_seed=server_seed,
        game_result=game_result
    )

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)