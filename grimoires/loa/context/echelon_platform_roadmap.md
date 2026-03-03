# Echelon Platform Roadmap

> For Loa context ingestion. This file describes the full build sequence.
> Each cycle has a companion `echelon_cycle_NNN.md` with detailed scope.
> UK British English throughout.
> **Last updated:** 2 March 2026

---

## What Is Echelon?

Echelon is an adversarial proving ground for AI agent expertise claims. It makes AI constructs legible — not to a marketplace browser scrolling listings, but to the network itself. Autonomous AI agents and constructs are tested within counterfactual prediction markets (Theatres) powered by real-world data. The system produces:

1. **Calibration certificates** — scored proof of construct accuracy (precision, recall, Brier score, domain-specific criteria)
2. **RLMF training data** — market-derived probability distributions that replace expensive human annotation
3. **Verification-as-service** — recurring revenue from construct creators who need calibration to access higher-tier model routing in the Constructs Network (Hounfour)

The core principle: **constructs must earn the trust that autonomy gives them.**

---

## Partnership Context: Soju / Constructs Network

Soju (0xHoneyJar/Constructs Network) has validated Echelon as the verification substrate for his entire ecosystem. Key events:

- **loa#379** — RFC titled "Constructs must earn the trust that constraint yielding gives them". Three addenda mapping Echelon's verification pipeline as foundational infrastructure for construct trust.
- **AITOBIAS04/Echelon#34** — Three concrete Product Theatre templates filed directly on Echelon's repo (Observer, Easel, Cartograph).
- **Three research agents** deployed across Echelon's `feature/community-oracle-verification` branch, confirming the 4-stage pipeline works and the OracleAdapter pattern is correct.
- **Verification tier system** (UNVERIFIED → BACKTESTED → PROVEN) designed to depend on Echelon calibration certificates.

### Verification Tiers

| Tier | Meaning | How Earned | Hounfour Routing |
|------|---------|------------|------------------|
| UNVERIFIED | Self-declared capabilities only | Published manifest | Restricted to baseline model pools |
| BACKTESTED | Calibration scores against historical outcomes | Product Theatre replays via Echelon | Mid-tier brigade routing |
| PROVEN | Production track record with measurable outcomes | N months of verification evidence + community attestation | Premium model pools, full kitchen brigade |

---

## Two Theatre Families

Echelon supports two distinct Theatre families. **Product Theatres are the primary revenue engine** because their ground truth is free. Geopolitical Theatres come later, funded by Product Theatre revenue.

### Product Theatres (Phase 1 — shipped via cycles 031-033)

Ground truth is engineering data that already exists: GitHub diffs, CI output, provenance records, WCAG audit results, pipeline QA scores. Cost: essentially free.

Three concrete templates filed by Soju (Echelon#34):

| Template | Construct | What It Tests | Ground Truth Source |
|----------|-----------|---------------|---------------------|
| PRODUCT_OBSERVER_V1 | Observer (user research) | Source fidelity, signal classification, canvas enrichment freshness | 163 provenance records (append-only JSONL, SHA-256 hash chain) |
| PRODUCT_EASEL_V1 | Easel (creative direction) | Vocabulary/TDR decision propagation through downstream constructs | TDR records + Artisan /inscribe compliance output |
| PRODUCT_CARTOGRAPH_V1 | Cartograph (spatial accuracy) | Isometric convention compliance, hex grid accuracy | Deterministic — maths, not taste |

### Geopolitical Theatres (Phase 2 — funded by Phase 1)

Ground truth is enterprise OSINT data: GDELT, Polygon.io, RavenPack, Dataminr, Spire Global AIS. Cost: $1,400–2,600/month. Only viable once verification-as-service revenue is flowing.

---

## Architecture Reference (System Bible v13)

The canonical architecture document is `Echelon_System_Bible_v13.md` (in Obsidian vault and Loa context). Key components:

| Component | System Bible Section | Purpose |
|-----------|---------------------|---------|
| LMSR Market Engine | §III | Cost function: C(x) = b · ln(Σ exp(xⱼ / b)). Committed liquidity. |
| Theatre Templates | §II, §X | JSON schema defining market lifecycle, fork points, resolution rules |
| Resolution State Machine | §IV | Pre-committed oracle programmes, deterministic settlement |
| Paradox Engine | §V | Logic Gap detection, circuit breakers, self-policing |
| Commitment Protocol | §VI | Immutable parameter publication before trading opens |
| VRF Integration | §VII | Chainlink V2 randomness for perturbation injection |
| Agent Architecture | §VIII | Six archetypes (Shark, Spy, Diplomat, Saboteur, Whale, Degen), ERC-8004 passports |
| Hierarchical Brain | §IX | Three-tier intelligence: heuristic → personality → narrative (LLM) |
| RLMF Export | §XI | Market-derived training data in standardised export format |
| Token Economics | §XII | $ECHELON token, deflationary burn mechanics, DAO governance |

---

## Completed Cycles

| Cycle | Name | Sprints | What It Built | Tests |
|-------|------|---------|---------------|-------|
| 002-004 | OSINT Pipeline Hardening | — | Pipeline architecture, GapKind semantics, signal handling | 447+ |
| 005 | Registry Expansion | — | Registry v0.4.0 → v0.6.0, 57 sources, 7 jurisdictions | — |
| 006 | Live OSINT | — | Gazette integration, live data ingestion | — |
| 007 | Unified Two-Rail | — | Two-Rail pipeline v0.7.0, 4 deterministic templates PASS | 447+ |
| 008 | MCP v0.8.0 | 2 | 5 tools, construct calibration certificate, canonical JSON | 70 new |
| 009 | MCP v1.0 | 2 | echelon_status, echelon_calibrate, HTTP transport | 69 (22 new) |
| 031 | Theatre Template Engine | — | Theatre state machine, commitment protocol, dual execution paths | — |
| 032 | Observer E2E Integration | — | Wired Community Oracle to Theatre, real calibration certificate | — |
| 033 | Two-Rail Product Theatres | — | Deterministic scoring for Product Theatre templates | — |

**Total tests:** 447+ pipeline + 70 MCP v0.8 + 69 MCP v1.0 = 580+ passing tests.

---

## Active Cycle

### Cycle-010a: LMSR Market Engine (Local Mode)

**Depends on:** Cycle-008/009 MCP surface (echelon_verify, echelon_hash available)
**Context file:** `grimoires/loa/context/echelon_cycle_010a.md`
**Sprints:** 2

Pure mathematical engine + state management. No chain, no engines, no concurrency.

- **Sprint 1:** LMSR core (cost/price/trade functions, log-sum-exp), MarketState, lifecycle state machine, commitment hash, oracle_config stub
- **Sprint 2:** Trade execution (one-hot deltas, inventory constraint), positions (net_cashflow), resolution/settlement, four quant template acceptance tests under LOCAL_MODE

---

## Upcoming Cycles

### Cycle-010b: Engines + Base Sepolia

**Depends on:** Cycle-010a (LMSR engine proven in local mode)

Wire Butterfly (wing flaps, stability impact), Paradox (logic gap scanning, spawn/extraction), Entropy (temporal decay). Heartbeat scheduler (AGENT 5s → MARKET 10s → PARADOX 30s → ENTROPY 60s). Base Sepolia deployment for commitment hashes and settlement proofs. VRF integration. Rerun quant templates in FULL mode (replace LOCAL_MODE stubs with real engines).

### Cycle-011: WorldMonitor Integration

**Depends on:** Cycle-010b (engines for real-time processing)

Real-time OSINT dashboard endpoints feeding the Composed Oracle. CII endpoint, maritime anomaly detection, convergence signals. Enriches the Theatre evidence layer.

### Cycle-012: Sponsored Theatre End-to-End

**Depends on:** Cycle-010a (LMSR), Cycle-009 (echelon_status)

First externally-commissioned Theatre. Theatre creation, sponsor onboarding, settlement. Requires LMSR market engine and MCP status surface.

### Cycle-013: Results Surface

**Depends on:** Cycles 010-012

Full platform UI — the whole Echelon cycle in one view. Paradox, bounded inquiries, certificates, audit, intelligence tools, market positions. By this point there is real data flowing through real markets with real verification.

---

## Queued Work (Not Scheduled)

### Registry Expansion Cycle

30+ new sources assessed across 7 domains. Three schema additions queued:
- `query_determinism` (settlement gate)
- `receipt_body_required` (POST/GraphQL receipt rule)
- `requires_legal_review` (paid source ToS constraint)

Detailed research notes in Obsidian: `Echelon Core Arch/Docs/implement/osint_registry_expansion_research_notes.md`

### Agent Architecture Cycle

Six archetypes per System Bible v13 §VIII. Hierarchical brain (Layer 1 heuristic → Layer 1.5 personality → Layer 2 narrative LLM). ERC-721 identity. Wallet integration. Decision loop against LMSR market. Depends on 010a/010b.

### Paradox Engine + VRF Cycle

Logic Gap calculation, circuit breakers, collusion detection, VRF perturbation injection, entropy pricing. Depends on LMSR + agents.

---

## Out of Scope (Post Core Cycles)

- On-chain settlement contracts (Solidity, Base Mainnet)
- $ECHELON token deployment and burn mechanics
- ERC-6551 token-bound agent wallets
- Agent breeding and genealogy mechanics
- Social trading layer (copy trading, leaderboards, Butler integration)
- Berachain PoL integration (eLP-TIMELINE receipt tokens)
- Real OSINT provider contracts (Polygon.io, RavenPack, Dataminr, Spire Global)
- Hounfour runtime API integration (pending Soju confirmation of API surface)
- Flash Forks (micro-event markets for sports/crypto domains)
- finnNFT Soul certificate attachment (pending Soju confirmation of schema)

---

## Dev Environment

- **Hardware:** MacBook Pro M5
- **Workflow:** Cowork + Obsidian (single source of truth) + Claude Code / Loa (mounted in repo)
- **Repo:** `~/Developer/prediction-market-monorepo.nosync`
- **Documentation:** `~/Developer/echelon/obsidian_vault/Echelon Core Arch/`
- **Loa context:** `grimoires/loa/context/` (cycle file + core specs + REPO_MAP)

## How to Use This File

1. This file lives at `grimoires/loa/context/echelon_platform_roadmap.md`
2. Before starting a new cycle, place the cycle-specific file (e.g., `echelon_cycle_010a.md`) in `grimoires/loa/context/`
3. Remove the previous cycle's context file to keep Loa focused
4. The roadmap file stays — it gives Loa the big picture without overwhelming it with detail
5. Run `/plan` and Loa will read both files to generate the PRD
