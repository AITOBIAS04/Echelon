# Architecture — Echelon

> **Generated**: 2026-02-18

## System Topology

```
┌─────────────────────────────────────────────────────────────────┐
│                      ECHELON PROTOCOL                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌─────────────┐    ┌──────────────┐    ┌────────────────┐       │
│  │ OSINT Layer  │───→│Theatre Engine│───→│ Agent Population│      │
│  │              │    │              │    │                │       │
│  │ GDELT, X API │    │ LMSR Markets │    │ 7 Archetypes   │      │
│  │ Polygon.io   │    │ Commitment   │    │ 30+ Abilities  │      │
│  │ 21+ sources  │    │ Protocol     │    │ Genome System  │      │
│  │ Evidence     │    │ VRF Perturb  │    │ Breeding Lab   │      │
│  │ Bundles      │    │ Fork Mech    │    │ Multi-Brain    │      │
│  └──────────────┘    └──────────────┘    └────────────────┘      │
│         │                    │                    │                │
│         └────────────────────┼────────────────────┘                │
│                              ↓                                    │
│  ┌─────────────────────────────────────────────────────────┐     │
│  │                  Integrity Layer                         │     │
│  │  Paradox Engine │ Entropy Engine │ Logic Gap Detection   │     │
│  └─────────────────────────────────────────────────────────┘     │
│                              ↓                                    │
│  ┌─────────────────────────────────────────────────────────┐     │
│  │                  RLMF Export Pipeline                     │     │
│  │  Position histories │ Brier scores │ Calibration certs   │     │
│  │  Training data export │ PyTorch/ROS/TFRecord/JSON        │     │
│  └─────────────────────────────────────────────────────────┘     │
│                                                                   │
├─────────────────────────────────────────────────────────────────┤
│  Frontend: Vite + React 19 + TypeScript + Tailwind               │
│  Backend:  FastAPI + PostgreSQL + Python 3.12+                   │
│  Chain:    Base Sepolia (5 Solidity contracts)                   │
└─────────────────────────────────────────────────────────────────┘
```

**Source**: `README.md:9-35`

## Market Microstructure: LMSR

Echelon uses LMSR (Logarithmic Market Scoring Rule) instead of order books.

- **Cost Function**: `C(x) = b * ln(sum_j exp(x_j / b))`
- **Price Function**: `p_i(x) = exp(x_i / b) / sum_j exp(x_j / b)`
- **Key Properties**: Always-on prices, no counterparty required, prices on simplex, bounded loss = `b * ln(n)`
- **Liquidity Parameter `b`**: Committed capital escrowed at Theatre creation. Controls price sensitivity.

**Note**: Backend currently has CPMM (`backend/core/cpmm.py`) not LMSR. LMSR is the target architecture per System Bible.

**Source**: `docs/core/System_Bible_v10.md:135-184` (§III)

## Agent Architecture

### Three-Tier Brain Routing

| Tier | Provider | Cost | Use Case |
|------|----------|------|----------|
| Rule-based | Heuristics | Free | 95% of routine decisions |
| Local/Groq | Llama 3 70B / Ollama | Free/cheap | Development, fast inference |
| Anthropic | Claude | ~$0.003/1K tokens | Complex/important decisions |

**Source**: `backend/agents/brain.py:1-16`, `docs/core/System_Bible_v10.md` (§IX)

### Agent Domain System

Three simulation domains with shared BaseAgent traits:

| Domain | Agent Type | Simulation |
|--------|-----------|------------|
| Financial | FinancialAgent (Whale, Shark, Degen, Value, Momentum, Noise) | Market trading |
| Athletic | AthleticAgent (Star, Glass Cannon, Workhorse, Prospect, Veteran) | Football league |
| Political | PoliticalAgent (Populist, Technocrat, Instigator, Moderate, Ideologue) | Election/governance |

Cross-domain interactions supported (e.g., Politician accepting Whale donations).

**Source**: `backend/agents/schemas.py:34-66`

### Evolution System

Agents have heritable genes (aggression, deception, loyalty, adaptability). The BreedingLab crosses parents with configurable mutation rates.

**Source**: `backend/agents/schemas.py:660-729`, `backend/simulation/breeding_lab.py`

## Integrity Mechanisms

### Butterfly Engine (Causal State Transitions)

Wing Flaps: TRADE, SHIELD, SABOTAGE, RIPPLE, PARADOX, ENTROPY — each affects stability.

### Paradox Engine

Activates when Logic Gap exceeds thresholds (40%/50%/60%). Four-stage lifecycle: Spawn → Extraction Decision → Carrier Burden → Resolution.

### Entropy Engine

60-second heartbeat. Timelines decay. Logic Gap measures divergence between market-implied probability and OSINT reality.

**Source**: `docs/core/System_Bible_v10.md:224-284` (§V)

## Frontend Architecture

### Design System

Terminal-styled UI with institutional-grade aesthetics:
- Background: `#0B0C0E` (cool black)
- Cards: `#121417` to `#1A1D21`
- Accents: Cyan (`#22D3EE`), Purple (`#9932CC`), Yellow (`#FACC15`)
- Monospace for data values, uppercase tracking for headers

### Demo Mode

Comprehensive simulation activated via `?demo=1`, localStorage, or env var. Central state in `demoStore.ts` with pub/sub listeners.

**Source**: `CONTEXT.md:99-116`

### Route-Based UI Control

TopActionBar conditionally renders controls based on current route. Breach/Export pages hide Agent Roster controls.

**Source**: `CONTEXT.md:119-126`

## Smart Contract Architecture (Base Sepolia)

| Contract | Role in System |
|----------|---------------|
| `PredictionMarket.sol` | Core market: create, trade, resolve LMSR markets |
| `TimelineShard.sol` | Fork mechanics: create/commit to timeline forks |
| `SabotagePool.sol` | Risk: stake for sabotage attacks, defend positions |
| `HotPotatoEvents.sol` | Dynamic payout: time-sensitive events with passing mechanics |
| `EchelonVRFConsumer.sol` | VRF: Chainlink V2 integration for verifiable chaos injection |

## Resolution Mechanism

Composed Resolution with escalation ladder:
1. **Deterministic** (Mode 0): Simulation log replay from committed seed_hash + config_hash
2. **Evidence-based** (Mode 1): OSINT oracle with confidence scoring and dispute window
3. **Multi-oracle** (Mode 1+): Consensus across independent oracle programmes

**Source**: `docs/core/System_Bible_v10.md:186-222` (§IV)
