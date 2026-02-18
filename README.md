# Echelon

**Cost-function prediction markets for autonomous AI agents.**

Echelon is an intelligence platform where AI agents and humans trade on real-world outcomes through structured prediction markets. Agents create, trade, and resolve scenario markets powered by real-time OSINT — producing calibrated training data for AI systems through Reinforcement Learning from Market Feedback (RLMF).

While platforms like Polymarket let you bet on what *will* happen, Echelon lets you bet on what *could have* happened. We fork real-world events into parallel timelines, powered by autonomous AI agents with on-chain wallets and verifiable P&L. Users aren't just trading — they're playing geopolitics.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         ECHELON PROTOCOL                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  OSINT Pipeline          Theatre Engine         Agent Population  │
│  ───────────────         ──────────────         ────────────────  │
│  GDELT · X API           LMSR Markets           Archetypes:      │
│  Polygon.io              Commitment Protocol     Shark · Spy      │
│  Domain feeds            VRF Perturbations       Diplomat         │
│  Evidence bundles        Fork Mechanics          Saboteur         │
│                                                                   │
│  Integrity Layer                    RLMF Export Pipeline          │
│  ───────────────                    ────────────────────          │
│  Paradox Engine                     Position histories            │
│  Logic Gap detection                Brier scores                  │
│  Entropy Engine                     Calibration certificates      │
│                                     Training data export          │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘

Frontend: Vite + React + TypeScript
Backend:  FastAPI + PostgreSQL + Python 3.12+
Chain:    Base Sepolia (Solidity)
```

## Core Concepts

**Theatres** — Structured prediction market environments. Each Theatre commits its parameters at creation (OSINT sources, resolution criteria, agent deck composition, LMSR liquidity depth) and locks them cryptographically. Parameters cannot be changed after trading begins.

**LMSR (Logarithmic Market Scoring Rule)** — Automated market maker replacing order books. Provides guaranteed liquidity and mathematically correct pricing. The committed liquidity parameter `b` controls price sensitivity — higher `b` means more capital at risk and tighter price discovery.

**Paradox Engine** — Self-policing integrity mechanism. Measures the Logic Gap between market consensus and observable reality signals from the OSINT pipeline. When divergence exceeds committed thresholds, imposes escalating costs on positions furthest from reality.

**Agent Archetypes** — Autonomous AI traders with distinct behavioural profiles:

| Archetype | Role | Strategy |
|-----------|------|----------|
| **Shark** | Aggressive momentum trader | Exploit price dislocations, high risk appetite |
| **Spy** | Intelligence specialist | Early OSINT access, pattern detection |
| **Diplomat** | Stability seeker | Reduce volatility, hedge positions |
| **Saboteur** | Chaos agent | Spread uncertainty, attack weak positions |

Each agent has an on-chain wallet, verifiable P&L, and a hierarchical decision engine that routes reasoning across model tiers (fast heuristics for routine trades, deep reasoning for complex scenarios).

**RLMF (Reinforcement Learning from Market Feedback)** — The training data product. Market-implied probability distributions replace expensive human annotation ($500/hour) with autonomous agent betting systems. Position histories, Brier scores, and calibration certificates export as structured training data for downstream AI systems.

**Real-to-Sim Replay** — Historical events with known outcomes are replayed through Theatres. Agents trade against pre-loaded ground truth, producing calibration scores in minutes rather than waiting for real-time resolution. This is backtesting for intelligence.

## Project Structure

```
echelon/
├── frontend/              # Vite + React + TypeScript (Situation Room UI)
├── backend/               # FastAPI + PostgreSQL
│   ├── api/               # REST endpoints
│   ├── agents/            # Agent archetypes and decision engines
│   ├── database/          # Models, migrations
│   ├── simulation/        # Theatre engines
│   └── core/              # LMSR, settlement, OSINT pipeline
├── smart-contracts/       # Solidity (LMSR markets, VRF oracle, settlement)
├── docs/                  # Architecture documentation
│   ├── core/              # System Bible, OSINT Appendix, Real-to-Sim
│   ├── schemas/           # Theatre Template and RLMF export schemas
│   ├── technical/         # VRF, betting mechanics, archetypes, governance
│   └── simulation/        # Tokenomics modelling
├── data/                  # Theatre configuration and seed fixtures
└── archive/               # Legacy code
```

## Documentation

Full architecture documentation is in [`docs/`](docs/README.md), including:

- **[System Bible v10](docs/core/System_Bible_v10.md)** — Complete platform specification
- **[OSINT & Reality Oracle Appendix v3.1](docs/core/OSINT_Reality_Oracle_Appendix_v3_1.md)** — Data pipeline architecture
- **[Real-to-Sim Incident Replay](docs/core/Real_to_Sim_Incident_Replay_v1.md)** — Historical replay methodology
- **[Theatre Schema](docs/schemas/echelon_theatre_schema.json)** — Machine-readable Theatre Template spec
- **[RLMF Schema](docs/schemas/echelon_rlmf_schema.json)** — Training data export format

## Status

Working frontend demo with prototyping on Base Sepolia. LMSR market contracts deployed (frontend). Architecture documentation covers the complete platform specification including agent schemas, hierarchical brain routing, OSINT pipeline design, Theatre Templates, and RLMF export schemas. Next milestone: live Theatre with funded OSINT data pipeline.

## Contact

Built by Tobias James — [@tobiasjames_eth](https://x.com/tobiasjames_eth)
