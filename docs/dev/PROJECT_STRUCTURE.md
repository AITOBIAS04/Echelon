# Prediction Market Monorepo - File Structure

## Project Overview
A full-stack prediction market platform with provably fair game engines, agent-based simulations, and a Next.js frontend.

---

## Root Structure

```
prediction-market-monorepo/
├── backend/                    # Python FastAPI backend
├── frontend/                   # Next.js React frontend
├── smart-contracts/           # Hardhat Ethereum contracts
├── .gitignore
├── README.md
└── validate_situation_room_corrected.sh
```

---

## Backend Structure (`backend/`)

### Core Directory (`backend/core/`)
**Purpose:** Core business logic, data models, and engines

```
backend/core/
├── models.py                          # SQLAlchemy models + Pydantic schemas
│                                      # - User, Bet, Game models
│                                      # - AgentGenome for agent evolution
│                                      # - TulipStrategyConfig for Shark strategies
│
├── database.py                        # Database connection & session management
├── auth.py                           # OAuth2 authentication logic
│
├── situation_room_engine.py          # Main Situation Room RPG engine
│                                      # - Event orchestration
│                                      # - Timeline management
│                                      # - Shark brain integration
│
├── football_data_client.py           # Async client for football-data.org API
│                                      # - Fetches real-world league data
│                                      # - Rate limiting (10 req/min)
│                                      # - Snapshot creation
│
├── synthetic_osint.py                # Generates synthetic OSINT for events
├── narrative_war.py                  # Narrative warfare simulation
│
├── osint_registry.py                 # Central OSINT source registry
├── osint_sources_situation_room.py   # OSINT for Situation Room
├── osint_sources_financial.py        # Financial market OSINT
├── osint_sources_sports.py           # Sports betting OSINT
└── osint_sources_extended.py         # Extended OSINT sources
```

### API Directory (`backend/api/`)
**Purpose:** FastAPI route handlers

```
backend/api/
├── auth_routes.py                    # Login, register, token refresh
├── betting_routes.py                 # Place bets, view history
├── game_routes.py                    # Game creation, settlement
├── situation_room_routes.py          # Situation Room endpoints
└── __init__.py
```

### Agents Directory (`backend/agents/`)
**Purpose:** Universal agent schema system

```
backend/agents/
├── schemas.py                        # Agent schema definitions
│                                      # - BaseAgent (universal base)
│                                      # - FinancialAgent (trading)
│                                      # - AthleticAgent (sports)
│                                      # - PoliticalAgent (elections)
│                                      # - Breeding & evolution system
│
└── shark_strategies.py               # Shark trading strategies
                                       # - TulipBubbleStrategy
                                       # - SharkBrain for decision-making
```

### Simulation Directory (`backend/simulation/`)
**Purpose:** Game simulation engines

```
backend/simulation/
├── sim_football_engine.py            # Football match & league simulator
│                                      # - Full 90-minute match simulation
│                                      # - League table management
│                                      # - Snapshot fork capability
│                                      # - CLI: --mode, --matchday, --snapshot
│
├── sim_market_engine.py              # Financial market simulator
│                                      # - Uses FinancialAgent archetypes
│                                      # - Whale, Shark, Degen, Value, etc.
│                                      # - Multiple asset markets
│
├── sim_geopolitics_engine.py         # Geopolitical event simulation
├── sim_election_engine.py            # Election simulation
├── digital_twin_engine.py            # Digital twin duels
├── engine.py                         # Chess engine
│
└── situation-room/
    └── scheduler.py                  # Event scheduler for Situation Room
```

### Main Files (`backend/`)

```
backend/
├── main.py                           # FastAPI app entry point
│                                      # - Route registration
│                                      # - CORS configuration
│                                      # - Engine routing for bets
│
├── .env                              # Environment variables
│                                      # - DATABASE_URL
│                                      # - SECRET_KEY
│                                      # - FOOTBALL_DATA_API_KEY
│
├── requirements.txt                  # Python dependencies
└── .venv/                           # Virtual environment (excluded from git)
```

---

## Frontend Structure (`frontend/`)

### App Directory (`frontend/app/`)
**Purpose:** Next.js 13+ app router pages

```
frontend/app/
├── page.jsx                          # Homepage
├── layout.jsx                        # Root layout
│
├── login/
│   └── page.jsx                      # Login page
│
├── register/
│   └── page.jsx                      # Registration page
│
├── dashboard/
│   └── page.jsx                      # User dashboard
│
├── betting/
│   └── page.jsx                      # Betting interface
│
├── situation-room/
│   └── page.jsx                      # Situation Room RPG UI
│                                      # - Event viewer
│                                      # - Action selection
│                                      # - Timeline display
│
├── market/
│   └── page.jsx                      # Market betting page
│
├── geopolitics/
│   └── page.jsx                      # Geopolitics betting
│
├── election/
│   └── page.jsx                      # Election betting
│
├── duel/
│   └── page.jsx                      # Digital twin duels
│
└── chess/
    └── page.jsx                      # Chess betting
```

### Components Directory (`frontend/components/`)

```
frontend/components/
├── Header.jsx                        # Navigation header
│                                      # - Links to all pages
│                                      # - Situation Room link
│
├── BettingCard.jsx                   # Bet display card
├── GameHistory.jsx                   # Game history display
└── [other UI components]
```

### Config Files (`frontend/`)

```
frontend/
├── package.json                      # Node.js dependencies
├── next.config.js                    # Next.js configuration
├── tailwind.config.js                # Tailwind CSS config
└── node_modules/                     # Dependencies (excluded from git)
```

---

## Smart Contracts Structure (`smart-contracts/`)

```
smart-contracts/
├── contracts/                        # Solidity contracts
│   └── [contract files]
│
├── scripts/                          # Deployment scripts
├── test/                            # Contract tests
├── hardhat.config.js                # Hardhat configuration
└── package.json                     # Node.js dependencies
```

---

## Key Integration Points

### 1. **Betting Flow**
```
Frontend (betting page)
    ↓ POST /api/bets/
Backend API (betting_routes.py)
    ↓ Subprocess call
Simulation Engine (sim_*_engine.py)
    ↓ Uses agents from
Agent Schema (agents/schemas.py)
    ↓ Returns outcome
Backend (main.py) - Settlement
    ↓ Updates
Database (core/models.py)
```

### 2. **Situation Room Flow**
```
Frontend (situation-room/page.jsx)
    ↓ GET/POST /api/situation-room/
Backend API (situation_room_routes.py)
    ↓ Uses
Situation Room Engine (core/situation_room_engine.py)
    ↓ Integrates
- Shark Strategies (agents/shark_strategies.py)
- Synthetic OSINT (core/synthetic_osint.py)
- Narrative War (core/narrative_war.py)
- Scheduler (simulation/situation-room/scheduler.py)
```

### 3. **Football Simulation Flow**
```
CLI or API call
    ↓
Football Engine (sim_football_engine.py)
    ↓ Can load snapshots from
Football Data Client (core/football_data_client.py)
    ↓ Uses agents from
Athletic Agent Schema (agents/schemas.py)
    ↓ Returns
Match Result (HOME_WIN/AWAY_WIN/DRAW)
```

---

## Environment Variables

### Backend (`.env`)
```bash
# Database
DATABASE_URL=sqlite:///./test.db

# Auth
SECRET_KEY=your-secret-key-here

# External APIs
FOOTBALL_DATA_API_KEY=b8a9dbf21ab241a4b5d257288569bf3f
```

---

## Git Exclusions (`.gitignore`)

```
# Python
.venv/
venv/
env/
__pycache__/
*.py[cod]
*.so
*.db

# Node
node_modules/
.next/
out/

# Environment
.env
.env.local

# OS
.DS_Store
```

---

## Key Technologies

### Backend
- **FastAPI** - Web framework
- **SQLAlchemy** - ORM
- **Pydantic** - Data validation
- **aiohttp** - Async HTTP client
- **python-jose** - JWT tokens
- **passlib** - Password hashing

### Frontend
- **Next.js 13+** - React framework with App Router
- **Tailwind CSS** - Styling
- **Axios/Fetch** - API calls

### Smart Contracts
- **Hardhat** - Ethereum development
- **Solidity** - Smart contract language

---

## Running the Project

### Backend
```bash
cd backend
source .venv/bin/activate  # or: . .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Test Football Engine
```bash
cd backend
source .venv/bin/activate
python simulation/sim_football_engine.py test client 1 --mode matchday --matchday 1 -v
```

### Fetch Real Football Data (Optional)
```bash
cd backend
source .venv/bin/activate
python -m core.football_data_client snapshot --competition PL --output snapshots
```

---

## Recent Additions

### Latest Updates
1. ✅ **Football Engine** - Full league simulation with CLI
2. ✅ **Situation Room** - RPG-style betting with Shark strategies
3. ✅ **Agent Schema System** - Universal agent architecture
4. ✅ **OSINT Integration** - Synthetic intelligence generation
5. ✅ **Narrative Warfare** - Story-driven market manipulation

---

## Repository
- **GitHub**: https://github.com/AITOBIAS04/prediction-market-monorepo
- **Visibility**: Private
- **Owner**: AITOBIAS04

---

*Generated: December 2, 2025*
