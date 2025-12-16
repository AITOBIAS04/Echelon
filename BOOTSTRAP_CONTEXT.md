# Echelon Project — Bootstrap Context for New Conversations

**Last Updated:** December 16, 2025
**Domain:** playechelon.io
**Purpose:** Provide context continuity for Claude when starting new chats about Echelon

---

## 1. PROJECT OVERVIEW

**Echelon** is a counterfactual prediction market platform that forks real markets (Kalshi/Polymarket) into parallel "what if" timelines. Users bet on alternate realities powered by AI agents and real-time OSINT data.

### Core Taglines (Approved)
- **Primary:** "Kalshi/Polymarket lets you bet on what will happen. Echelon lets you bet on what could have happened."
- **Insight:** "We aren't predicting the future — we're detecting the present faster than the news."
- **Positioning:** "Users aren't just trading — they're playing geopolitics."

### Three Pillars
1. **The Butterfly Engine** — Cryptographically secured timeline divergence (Snapshot & Fork architecture)
2. **Mission-Based Trading** — OSINT-triggered scenarios with objectives, time pressure, rewards
3. **AI Agents** — Sharks, Spies, Diplomats, Saboteurs with on-chain wallets and verifiable P&L

---

## 2. CURRENT INFRASTRUCTURE STATE

### Domain & Hosting
- **Domain:** playechelon.io (to be configured)
- **DNS:** Cloudflare (pending setup)
- **Backend:** FastAPI on localhost:8000 (pending deployment)
- **Frontend:** Next.js on localhost:3000 (pending deployment)

### Blockchain (Testnet)
- **Chain:** Base Sepolia
- **Settlement Wallet:** 0xA4885D48e09D62a47Fc5c9Add7eAd130DCBd5688
- **OnchainKit API:** CHANGE_ME

### Coinbase Integration
- **Commerce API Key:** CHANGE_ME
- **Webhook Secret:** CHANGE_ME

---

## 3. TECHNICAL ARCHITECTURE

### Hierarchical Intelligence (Cost Optimisation)
- **Layer 1 (90%+ of decisions):** Rule-based heuristics (<10ms, $0 cost)
  - Tulip Strategy: Illiquid market near-expiry arbitrage
  - Blood in Water: Wide spread liquidity provision
  - Exit Rules: Take profit/stop loss/time decay
- **Layer 2 (~10% of decisions):** Fast LLM (Groq/Ollama) for novel situations
- **Layer 3 (<1% of decisions):** Quality LLM (Claude/GPT-4) for complex reasoning

### The Sandwich Architecture
- **Brain (Google ADK):** Context engine, decision logic, narrative generation
- **Body (Virtuals Protocol):** ERC-6551 wallet, x402 payments, execution

### Multi-Chain Wallet
- **Base:** Virtuals identity, ACP transactions, tokenisation
- **Polygon:** Polymarket execution (Gnosis Safe + Relayer)
- **Solana:** Kalshi execution (programmatic keypair)

---

## 4. API ENDPOINTS (Implemented)

### Operations API
- `GET /api/operations` — List active operations
- `POST /api/operations/{id}/join` — Join an operation
- `GET /api/agents` — List agents and P&L
- `POST /api/agents/hire` — Hire agent via ACP
- `GET /api/intel` — Available intel packages
- `POST /api/intel/purchase` — Buy intel
- `GET /api/game-state` — Global state for Situation Room
- `GET /api/signals` — Real-time agent signals

### Butler Webhooks
- `POST /api/butler/webhook` — Main webhook for X integration
- `POST /api/butler/test` — Local testing endpoint
- `GET /api/butler/health` — Health check

### Scheduler API
- `POST /api/scheduler/start` — Start autonomous agents
- `POST /api/scheduler/stop` — Stop scheduler
- `GET /api/scheduler/status` — Scheduler stats
- `GET /api/scheduler/agents` — List scheduled agents
- `POST /api/scheduler/run-cycle/{id}` — Manual trigger

---

## 5. APPROVED MISSIONS (Exciting Examples)

| Mission | OSINT Anomaly | Threshold Trigger |
|---------|---------------|-------------------|
| **Ghost Tanker** | Spire AIS dark fleet | >3 tankers go dark near Venezuela/Hormuz |
| **Silicon Acquisition** | Job postings + USPTO patents | Apple posts >50 AI roles in 1 week |
| **Contagion Zero** | Social keyword geo-clustering | 300% spike in "flu" mentions in city |
| **Deep State Shuffle** | NASA night lights + flight tracking | Palace dark + jets to Miami 2-4AM |
| **Cartel Crop** | Sentinel Hub satellite NDVI | Greenness spike in Sinaloa off-season |

---

## 6. BUDGET ($300K / 6 months)

| Category | Amount |
|----------|--------|
| Development | $150,000 |
| OSINT/Data Infrastructure | $100,000 |
| Infrastructure & Audit | $30,000 |
| Operations | $20,000 |

---

## 7. CONTACT

- **Email:** playechelon@gmail.com
- **X:** @playechelon
- **Domain:** playechelon.io

---

## 8. NEXT STEPS

1. ☐ Purchase playechelon.io domain
2. ☐ Configure Cloudflare DNS
3. ☐ Deploy backend to Railway/Render
4. ☐ Deploy frontend to Vercel
5. ☐ Get testnet ETH from Base Sepolia faucet
6. ☐ Deploy agent wallets
7. ☐ Register with Virtuals Butler program
8. ☐ Submit Polymarket grant application
9. ☐ Submit Kalshi grant application

---

## 9. QUICK REFERENCE — KEY QUOTES

**For Grants:**
> "Echelon utilises a 'Snapshot & Fork' architecture to generate counterfactual market realities that are mathematically impossible to manipulate."

**For Pitches:**
> "We aren't predicting the future — we're detecting the present faster than the news, and letting agents gamble on the outcome."

**For Positioning:**
> "An intelligence platform, not just a game. A competitive moat through anomaly detection. Real-world value using the same techniques as hedge funds and intelligence agencies."

---

*This document should be uploaded at the start of new conversations about Echelon to maintain context continuity.*
