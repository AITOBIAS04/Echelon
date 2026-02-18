# Echelon Protocol

**Counterfactual prediction markets powered by AI agents and real-time OSINT.**

Echelon lets you bet on alternate realities. While Kalshi/Polymarket let you bet on what *will* happen, Echelon lets you bet on what *could have* happened. We fork real-world events into parallel "what if" timelines, powered by autonomous AI agents (Sharks, Spies, Diplomats, Saboteurs) with on-chain wallets and verifiable P&L. Users aren't just trading—they're playing geopolitics.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         ECHELON PROTOCOL                         │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│   FRONTEND    │    │    BACKEND    │    │   CONTRACTS   │
│               │    │               │    │               │
│ Vite + React  │◄──►│ FastAPI + PG  │◄──►│  Solidity     │
│  TypeScript   │    │  Python 3.12+ │    │  Base Sepolia │
│               │    │               │    │               │
│ - War Room    │    │ - Agents      │    │ - Timeline    │
│ - Field Kit   │    │ - Timelines   │    │   Shards      │
│ - SIGINT      │    │ - Paradoxes   │    │ - Settlement  │
│ - Blackbox    │    │ - OSINT       │    │ - VRF Oracle  │
└───────────────┘    └───────────────┘    └───────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │   POSTGRESQL     │
                    │   (Railway)      │
                    └─────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    THREE PILLARS                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  1. BUTTERFLY ENGINE                                             │
│     Cryptographically secured timeline divergence                │
│     (Snapshot & Fork architecture)                               │
│                                                                   │
│  2. MISSION-BASED TRADING                                        │
│     OSINT-triggered scenarios with objectives,                    │
│     time pressure, and rewards                                   │
│                                                                   │
│  3. AI AGENTS                                                    │
│     Sharks, Spies, Diplomats, Saboteurs                          │
│     with on-chain wallets and verifiable P&L                     │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start (5 Commands)

```bash
# 1. Install dependencies
cd backend && pip install -r requirements.txt
cd ../frontend && pnpm install

# 2. Set up database (SQLite for dev)
export DATABASE_URL="sqlite:///./dev.db"
cd backend && alembic upgrade head

# 3. Seed database
cd .. && python -m backend.scripts.seed_database --force

# 4. Start backend (Terminal 1)
cd backend && python -m uvicorn main:app --reload

# 5. Start frontend (Terminal 2)
cd frontend && pnpm dev
```

**Access:**
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

## 📁 Project Structure

```
echelon/
├── frontend/              # Vite + React + TypeScript
│   ├── src/
│   │   ├── components/    # War Room, Field Kit, SIGINT, Blackbox
│   │   ├── api/          # API client
│   │   └── hooks/        # React hooks for data
│   └── package.json
│
├── backend/               # FastAPI + PostgreSQL
│   ├── api/              # REST endpoints
│   ├── agents/           # AI agent logic (Sharks, Spies, etc.)
│   ├── database/         # Models, migrations, connection
│   ├── skills/            # Agent skills architecture
│   ├── simulation/        # Game engines
│   ├── core/             # Core business logic
│   └── scripts/           # Seed database, utilities
│
├── smart-contracts/       # Solidity contracts
│   ├── contracts/        # TimelineShard, SabotagePool, VRF
│   └── test/             # Contract tests
│
├── docs/
│   ├── dev/              # Architecture, integration guides
│   └── ops/              # Deployment, troubleshooting
│
├── scripts/               # Utility scripts
├── data/seed/            # Database seed fixtures (deterministic)
└── archive/              # Legacy code (Next.js frontend)
```

---

## 🧠 Core Concepts

### Timelines
**Counterfactual "what if" scenarios** forked from real-world events. Each timeline represents an alternate reality where something happened differently (e.g., "What if Iran closed the Strait of Hormuz for 72 hours?"). Timelines have:
- **Stability** (0-100): How likely the timeline is to resolve YES
- **Surface Tension**: Market volatility indicator
- **Paradoxes**: Logical inconsistencies that threaten timeline stability

### Agents
**Autonomous AI traders** with distinct archetypes and strategies:

| Archetype | Role | Strategy |
|-----------|------|----------|
| **SHARK** | Aggressive trader | Exploit illiquid markets, front-run |
| **SPY** | Intelligence gatherer | Early info access, intel accuracy |
| **DIPLOMAT** | Stabilizer | Create treaties, reduce volatility |
| **SABOTEUR** | Chaos agent | Spread FUD, attack timelines |
| **WHALE** | Market mover | Large positions, market impact |
| **DEGEN** | High-risk gambler | YOLO trades, luck factor |

Each agent has:
- On-chain wallet (ERC-6551 via Virtuals Protocol)
- Verifiable P&L
- Sanity meter (can go insane and die)
- Genome (genetic traits affecting behavior)

### Markets & Settlement
- **Timeline Shards**: ERC-1155 tokens representing positions in timelines
- **Bonding Curves**: `price = basePrice × (1 + supply/scaleFactor)²`
- **Settlement**: Chainlink VRF + OSINT oracles determine outcomes
- **Paradox Resolution**: Agents can extract paradoxes for rewards

### Wing Flaps
**Trading events** that affect timeline stability:
- **TRADE**: Agent opens/closes position
- **SHIELD**: Agent stabilizes timeline
- **SABOTAGE**: Agent attacks timeline
- **RIPPLE**: Cascade effects from other timelines
- **ENTROPY**: Natural decay over time

---

## 🔗 Key Documentation

### Getting Started
- **[Quick Start Guide](#-quick-start-5-commands)** - Get running in 5 commands
- **[Database Seeding](docs/ops/DATABASE_SEEDING.md)** - Set up deterministic seed data
- **[Deployment Checklist](docs/ops/DEPLOYMENT_CHECKLIST.md)** - Deploy to Railway/Vercel

### Architecture & Design
- **[Project Structure](docs/dev/PROJECT_STRUCTURE.md)** - Detailed file structure
- **[Bootstrap Context](docs/dev/BOOTSTRAP_CONTEXT.md)** - Project vision and context
- **[Agent Skills Architecture](backend/skills/ARCHITECTURE.md)** - How agents make decisions
- **[Platform Integrations](docs/dev/PLATFORM_INTEGRATIONS.md)** - Kalshi, Polymarket, Virtuals

### Operations
- **[Security Audit](docs/ops/SECURITY_AUDIT.md)** - Security practices
- **[Railway Setup](docs/ops/RAILWAY_SETUP.md)** - Backend deployment
- **[Vercel Deployment](docs/ops/VERCEL_DEPLOYMENT.md)** - Frontend deployment

### Core Systems
- **[Market Systems](docs/dev/MARKET_SYSTEMS_EXPLAINED.md)** - How markets work
- **[Market Endpoints](docs/dev/MARKET_ENDPOINTS_EXPLAINED.md)** - API reference
- **[Echelon Complete](docs/dev/ECHELON_COMPLETE.md)** - Full system overview

---

## 🛠️ Development

### Prerequisites
- **Python 3.12+** (backend)
- **Node.js 18+** (frontend)
- **PostgreSQL** (production) or **SQLite** (development)
- **pnpm** or **npm** (package manager)

### Environment Variables

Create `.env` from `.env.example`:

```bash
# Database
DATABASE_URL=sqlite:///./dev.db  # or postgresql://...

# AI Providers (at least one required)
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
GROQ_API_KEY=xai-...

# JWT Secret
JWT_SECRET_KEY=generate_with_python_secrets
```

### Common Commands

```bash
# Root level
pnpm dev              # Start frontend
pnpm dev:backend      # Start backend
pnpm build            # Build frontend

# Backend
cd backend
alembic upgrade head                    # Run migrations
python -m backend.scripts.seed_database # Seed database
python -m uvicorn main:app --reload     # Dev server

# Frontend
cd frontend
pnpm dev      # Dev server (http://localhost:5173)
pnpm build    # Production build
pnpm lint     # Lint code
```

---

## 🎯 Vision: Echelon + RLMF

Echelon spans multiple domains:

- **Prediction Markets**: Betting on counterfactual outcomes
- **AI Agents**: Autonomous traders with on-chain identities
- **OSINT Integration**: Real-world data triggers missions
- **Blockchain Settlement**: Provably fair outcomes via VRF
- **Geopolitical Gaming**: Users play intelligence operations

This README is your entry point. For deeper dives, see the [documentation](#-key-documentation) links above.

---

## 📄 License

[Add your license here]

## 🤝 Contributing

[Add contribution guidelines here]

---

**Built with:** FastAPI • React • TypeScript • PostgreSQL • Solidity • Chainlink VRF • Virtuals Protocol
