# Prediction Market Monorepo - Complete Overview

**Repository:** https://github.com/AITOBIAS04/prediction-market-monorepo  
**Type:** Private  
**Last Updated:** December 2024  
**Project Codename:** Seed (AI Simulation Engine)

---

## 📋 Table of Contents
1. [Project Architecture](#project-architecture)
2. [Backend Structure](#backend-structure)
3. [Frontend Structure](#frontend-structure)
4. [Key Systems](#key-systems)
5. [Recent Updates](#recent-updates)
6. [Setup & Running](#setup--running)
7. [API Reference](#api-reference)

---

## 🏗️ Project Architecture

### Technology Stack

**Backend:**
- FastAPI (Python web framework)
- SQLAlchemy (ORM)
- Pydantic (data validation)
- aiohttp (async HTTP client)
- Anthropic Claude Agent SDK (claude-agent-sdk)
- JWT authentication

**Frontend:**
- Next.js 14.2.3 (React 18.2.0 with App Router)
- Tailwind CSS 3.3.0 (stable v3)
- react-globe.gl 2.27.2 (3D globe visualization)
- three.js 0.160.0 (3D graphics)
- OnchainKit (wallet integration)
- SWR (data fetching)

**Blockchain:**
- Hardhat (Ethereum development)
- Base network integration
- Chainlink VRF (randomness)

---

## 🐍 Backend Structure

### Core Modules (`backend/core/`)

#### **Situation Room RPG System** 🎭
- `situation_room_engine.py` - **Main RPG engine**
  - Manages missions, agents, intel markets, treaties
  - Global tension & chaos index tracking
  - Narrative arc management
  - Sleeper cell system
  - Financial market integration (Shark strategies)
  
- `mission_generator.py` - Converts OSINT signals to missions
- `narrative_war.py` - Narrative warfare system (truth vs. propaganda)
- `rpg_agent_brain.py` - LLM-powered agent decision-making
- `autouploader.py` - Auto mission uploader service

#### **OSINT Intelligence System** 📡
- `osint_registry.py` - **Central OSINT registry**
  - Multi-source aggregation
  - Signal persistence
  - DEFCON threat levels
  - Statistics tracking (including "extended" category)
  
- `osint_sources_situation_room.py` - Geopolitical OSINT sources
  - VIP Aircraft Tracking
  - Marine Traffic
  - Night Lights
  - Internet Outages
  
- `osint_sources_financial.py` - Financial market OSINT
- `osint_sources_sports.py` - Sports betting OSINT
- `osint_sources_extended.py` - Extended sources
- `synthetic_osint.py` - Synthetic OSINT generator (testing/demo)

#### **Event & Market Systems**
- `event_orchestrator.py` - Coordinates events across systems
- `signal_detector.py` - Market signal detection
- `models.py` - Data models (Mission, AgentRole, NarrativeArc, etc.)

#### **External Integrations**
- `football_data_client.py` - football-data.org API client
- `news_scraper.py` - Web scraping for real data
- `x402_client.py` - X402 protocol client

#### **Blockchain & Payments**
- `blockchain_manager.py` - Ethereum/Base interaction
- `wallet_factory.py` - Wallet generation
- `persistence_manager.py` - State persistence layer

#### **Utilities**
- `database.py` - SQLAlchemy session management
- `mock_data_generator.py` - Test data generation

### Agent System (`backend/agents/`)

#### **Agent Brains**
- `brain.py` - Base agent brain
- `multi_brain.py` - Multi-agent coordination (Hybrid Brain)
- `rpg_agent_brain.py` - RPG-style decision making with LLM
- `autonomous_agent.py` - Autonomous behavior

#### **Trading Strategies**
- `shark_strategies.py` - **Shark trading strategies**
  - Tulip Strategy (illiquid market exploitation)
  - SharkGenome & SharkBrain classes
  - MarketState analysis

#### **Schemas**
- `schemas.py` - BaseAgent, FinancialAgent, AthleticAgent, PoliticalAgent
  - Genetic algorithms (breeding, mutation)
  - Memory and relationship systems
  - Fitness evaluation

### Simulation Engines (`backend/simulation/`)

#### **Game Engines**
- `sim_football_engine.py` - **Football league simulator**
  - 90-minute match simulation
  - League table management
  - Snapshot fork capability
  - CLI: `--mode match|matchday|season`
  
- `sim_market_engine.py` - Financial market simulator
- `sim_election_engine.py` - Election simulation
- `sim_geopolitics_engine.py` - Geopolitical events
- `digital_twin_engine.py` - Digital twin duels
- `engine.py` - Chess simulation

#### **Supporting Systems**
- `scheduler.py` - **Main 3-tier scheduler**
  - Micro tick (10s): Yields
  - Narrative tick (60s): News & OSINT scans
  - Macro tick (300s): Evolution
  - Tension clamping (prevents overflow)
  
- `situation-room/scheduler.py` - **Situation Room game loop**
  - Initializes SituationRoomEngine
  - Connects OSINT sensors
  - Feeds signals into engine
  - Runs game logic (agents, missions, treaties)
  
- `brain_integration.py` - Brain-engine integration
- `breeding_lab.py` - Agent breeding experiments
- `evolution_engine.py` - Evolutionary algorithms
- `genome.py` - Genetic representation
- `world_state.py` - Global state management
- `yield_manager.py` - Reward distribution
- `timeline_manager.py` - Timeline management

### API Routes (`backend/api/`)
- `situation_room_routes.py` - Situation Room API endpoints
  - `/api/situation-room/state` - Game state
  - `/api/situation-room/missions` - Mission board
  - `/api/situation-room/intel` - Intel market
  - `/api/situation-room/treaties` - Treaty monitor
  - `/api/situation-room/narratives` - Narrative arcs
  - `/api/situation-room/test/inject-signal` - Test signal injection

### Main Application
- `main.py` - FastAPI entry point
  - Robust imports with try/except blocks
  - Route registration
  - CORS configuration
  - Situation Room router integration

---

## ⚛️ Frontend Structure

### Pages (`frontend/app/`)

#### **Core Pages**
- `page.js` - Homepage
- `layout.js` - Root layout with providers
- `globals.css` - **Global styles (Tailwind v3)**
  - Standard v3 directives (@tailwind base/components/utilities)
  - CSS variables for theming
  - Utility classes (nebula-bg, glass-panel, glow-text)

#### **Authentication**
- `login/page.jsx` - Login page
- `signup/page.jsx` - Registration page

#### **Main Features**
- `dashboard/page.jsx` - User dashboard
- `markets/page.jsx` - Market overview
- `betting/page.jsx` - Betting interface
- `wallet/page.jsx` - Wallet management
- `lobby/page.jsx` - Game lobby
- `timelines/page.jsx` - Timeline viewer

#### **Situation Room** 🎭
- `situation-room/page.jsx` - **Situation Room RPG dashboard**
  - Global tension gauge
  - Mission board (auto-uploaded from OSINT)
  - Intel market
  - Treaty monitor
  - Narrative timeline
  - "Who's the Mole?" mystery market
  - 3D globe visualization (Polyglobe component)
  - Real-time OSINT signal display

### Components (`frontend/components/`)

#### **UI Components**
- `Header.jsx` - Navigation
  - Situation Room link (red color, 🎭 icon)
  
- `Polyglobe.jsx` - **3D globe visualization**
  - Uses react-globe.gl
  - Displays OSINT signals as colored points/rings
  - Dynamic resizing
  - Auto-rotation
  - Region mapping (Washington DC, Moscow, Beijing, etc.)
  
- `TensionGauge.jsx` - Tension meter
- `EvolutionStatus.jsx` - Agent evolution display

#### **Timeline Components**
- `PersonalTimeline.jsx` - User's personal timeline
- `TimelineFork.jsx` - Timeline branching visualization

#### **Wallet Components**
- `wallet/WalletComponents.jsx` - Wallet UI
- `wallet/CheckoutComponents.jsx` - Payment checkout

### Configuration Files

#### **Package Management**
- `package.json` - **Dependencies locked to stable versions**
  - Next.js: 14.2.3 (locked)
  - React: 18.2.0 (locked)
  - Tailwind CSS: ^3.3.0
  - three.js: 0.160.0 (locked via overrides)
  - react-globe.gl: 2.27.2
  - Wallet packages: @coinbase/onchainkit, viem, wagmi, @tanstack/react-query

#### **Build Configuration**
- `next.config.mjs` - **Next.js configuration**
  - Webpack aliases to ignore react-native modules
  - Standalone output for Docker
  
- `postcss.config.js` - **PostCSS configuration (Tailwind v3)**
  - Standard v3 plugins (tailwindcss, autoprefixer)
  
- `tailwind.config.js` - **Tailwind configuration**
  - Content paths: app/, pages/, components/
  - Theme extensions ready

---

## 🔑 Key Systems

### 1. **Situation Room RPG** 🎭
A geopolitical strategy RPG where:
- OSINT signals generate missions automatically
- Agents (spies, diplomats, traders, etc.) execute missions
- Intel markets allow buying/selling information
- Treaties between factions can be violated
- Narrative arcs create storylines
- Sleeper cells can be activated
- Financial markets integrate with Shark strategies
- Global tension & chaos index track world state

**Key Files:**
- `backend/core/situation_room_engine.py` - Main engine
- `backend/core/mission_generator.py` - Mission generation
- `backend/core/narrative_war.py` - Narrative warfare
- `backend/simulation/situation-room/scheduler.py` - Game loop
- `frontend/app/situation-room/page.jsx` - UI dashboard

### 2. **OSINT Intelligence System** 📡
Multi-source intelligence aggregation:
- Real-time signal scanning
- DEFCON threat level calculation
- Signal persistence to disk
- Domain-specific sources (geopolitical, financial, sports)
- Synthetic OSINT for testing

**Key Files:**
- `backend/core/osint_registry.py` - Central registry
- `backend/core/osint_sources_situation_room.py` - Geopolitical sources
- `backend/core/synthetic_osint.py` - Synthetic generator

### 3. **Shark Trading Strategies** 🦈
Advanced trading strategies for prediction markets:
- Tulip Strategy: Exploits illiquid markets near expiry
- MarketState analysis
- Genome-based strategy configuration

**Key Files:**
- `backend/agents/shark_strategies.py` - Strategy implementation
- Integrated into `situation_room_engine.py` via `_process_financial_markets()`

### 4. **Agent Evolution System** 🧬
- Universal BaseAgent schema
- Genetic breeding with mutation
- Fitness-based selection
- Domain-specific agents (Financial, Athletic, Political)
- LLM-powered decision-making (RPG agents)

### 5. **Football Simulation** ⚽
- Full league simulation
- 90-minute match engine
- Real-world data integration (football-data.org)
- Snapshot fork for "what if" scenarios

### 6. **Provably Fair Gaming** 🎲
All simulations use deterministic seeding:
```python
game_hash = sha256(f"{server_seed}-{client_seed}-{nonce}")
random.seed(game_hash)
```

---

## 🔄 Recent Updates (December 2024)

### Migration: War Room → Situation Room
- ✅ Deleted `frontend/app/war-room/page.jsx`
- ✅ Created `frontend/app/situation-room/page.jsx`
- ✅ Renamed `osint_sources_warroom.py` → `osint_sources_situation_room.py`
- ✅ Updated `Header.jsx` with Situation Room link (red color)

### New Core Systems
- ✅ `situation_room_engine.py` - Full RPG engine implementation
- ✅ `narrative_war.py` - Narrative warfare system
- ✅ `synthetic_osint.py` - Synthetic OSINT generator
- ✅ `autouploader.py` - Auto mission uploader
- ✅ `rpg_agent_brain.py` - LLM-powered agent decisions
- ✅ `shark_strategies.py` - Shark trading strategies

### Frontend Stabilization
- ✅ Locked Next.js to 14.2.3 (stable)
- ✅ Locked React to 18.2.0
- ✅ Migrated Tailwind from v4 to v3.3.0
- ✅ Added webpack aliases for react-native modules
- ✅ Updated `globals.css` to v3 syntax
- ✅ Created `tailwind.config.js` with content paths
- ✅ Updated `postcss.config.js` to v3 standard

### Backend Improvements
- ✅ Added robust imports (try/except) in `main.py`
- ✅ Added tension clamping in `scheduler.py`
- ✅ Enhanced `load_state()` with error handling
- ✅ Added "extended" category to OSINT stats
- ✅ Integrated Shark strategies into Situation Room engine

### API Updates
- ✅ Situation Room API routes with JSON body support
- ✅ Signal injection endpoint for testing
- ✅ State snapshot includes `recent_signals`

---

## 🚀 Setup & Running

### Backend Setup
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Set environment variables
echo "DATABASE_URL=sqlite:///./database.db" > .env
echo "SECRET_KEY=your-secret-key" >> .env
echo "ANTHROPIC_API_KEY=your-key" >> .env

# Run server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup
```bash
cd frontend
rm -rf node_modules package-lock.json .next  # Clean install
npm install
npm run dev
```

### Situation Room Scheduler
```bash
cd backend
source .venv/bin/activate
python3 simulation/situation-room/scheduler.py
```

### Test Signal Injection
```bash
curl -X POST http://localhost:8000/api/situation-room/test/inject-signal \
  -H "Content-Type: application/json" \
  -d '{"category": "geopolitical", "high_urgency": true}'
```

---

## 📡 API Reference

### Situation Room Endpoints
- `GET /api/situation-room/state` - Current game state (includes recent_signals)
- `GET /api/situation-room/missions` - Active missions
- `GET /api/situation-room/intel` - Intel market
- `GET /api/situation-room/treaties` - Active treaties
- `GET /api/situation-room/narratives` - Narrative arcs
- `POST /api/situation-room/missions/{id}/accept` - Accept mission
- `POST /api/situation-room/intel/{id}/purchase` - Purchase intel
- `POST /api/situation-room/test/inject-signal` - Inject test signal (JSON body)

### Authentication
- `POST /auth/register` - Create account
- `POST /auth/login` - Get JWT token
- `POST /auth/refresh` - Refresh token

### Markets
- `GET /api/markets` - List markets
- `POST /bets/` - Place bet
- `GET /bets/history` - User's bet history

---

## 🗄️ Database Models

### Core Models
- **User** - username, email, hashed_password, play_money_balance
- **Bet** - user_id, engine_name, wager, outcome, settled
- **Game** - engine_name, server_seed, client_seed, nonce, result
- **AgentGenome** - Genetic data for agent breeding
- **TulipStrategyConfig** - Shark strategy configuration

### Situation Room Models (Pydantic)
- **Mission** - mission_type, difficulty, reward, required_roles
- **AgentRole** - spy, diplomat, trader, saboteur, journalist, propagandist, sleeper
- **NarrativeArc** - title, synopsis, chapters, progress
- **TheaterState** - faction_power, global_tension, chaos_index

---

## 📦 Dependencies

### Backend (requirements.txt)
- fastapi
- uvicorn
- sqlalchemy
- pydantic
- python-jose[cryptography]
- passlib[bcrypt]
- python-multipart
- aiohttp
- python-dotenv
- claude-agent-sdk (Anthropic)

### Frontend (package.json)
- next: 14.2.3 (locked)
- react: 18.2.0 (locked)
- react-dom: 18.2.0 (locked)
- tailwindcss: ^3.3.0
- three: 0.160.0 (locked)
- react-globe.gl: 2.27.2
- three-globe: 2.30.0 (locked)
- @coinbase/onchainkit: latest
- viem: latest
- wagmi: latest
- @tanstack/react-query: latest
- swr: ^2.2.4
- lucide-react: ^0.263.1
- react-hot-toast: ^2.4.1

---

## 🔐 Environment Variables

### Backend (.env)
```bash
DATABASE_URL=sqlite:///./database.db
SECRET_KEY=your-secret-key-here
ANTHROPIC_API_KEY=your-anthropic-key
FOOTBALL_DATA_API_KEY=your-football-data-key
```

### Frontend (.env.local)
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## 🎯 Current Status

### ✅ Completed Features
1. Situation Room RPG with full game loop
2. OSINT intelligence system with multi-source aggregation
3. Shark trading strategies integrated
4. Narrative warfare system
5. Auto mission uploader
6. Synthetic OSINT generator
7. Frontend stabilized (Tailwind v3, Next.js 14.2.3)
8. 3D globe visualization with OSINT signals
9. Robust error handling and state persistence
10. Multiple betting engines (football, market, election, geopolitics, chess)

### 🔄 Recent Fixes
- ✅ Tension clamping prevents overflow (1.05 → 1.0)
- ✅ State loading with error handling
- ✅ OSINT stats include "extended" category
- ✅ Frontend dependencies locked to stable versions
- ✅ Webpack aliases prevent react-native conflicts
- ✅ Tailwind migrated to stable v3

---

## 📚 Additional Documentation

- `ACTUAL_FILE_TREE.txt` - Complete file listing
- `PROJECT_STRUCTURE.md` - Detailed structure
- `IMPORT_GUIDE.md` - Import troubleshooting
- `SECURITY_AUDIT.md` - Security review
- `HOW_TO_ADD_NEW_FILES.md` - File addition guide

---

## 🎮 Quick Start Guide

1. **Clone & Setup**
   ```bash
   git clone https://github.com/AITOBIAS04/prediction-market-monorepo.git
   cd prediction-market-monorepo
   ```

2. **Backend**
   ```bash
   cd backend
   python -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   cp .env.example .env  # Edit with your keys
   uvicorn main:app --reload
   ```

3. **Frontend**
   ```bash
   cd frontend
   rm -rf node_modules .next
   npm install
   npm run dev
   ```

4. **Situation Room Scheduler**
   ```bash
   cd backend
   source .venv/bin/activate
   python3 simulation/situation-room/scheduler.py
   ```

5. **Access**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs
   - Situation Room: http://localhost:3000/situation-room

---

*Last Updated: December 2024*  
*Maintained by: AITOBIAS04*  
*Project Codename: Seed (AI Simulation Engine)*
