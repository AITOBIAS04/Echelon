# Echelon Platform Roadmap

> For Loa context ingestion. This file describes the full build sequence.
> Each cycle has a companion `echelon_cycle_NNN.md` with detailed scope.
> UK British English throughout.
> **Last updated:** 3 March 2026

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

**Total tests:** 513 passed (baseline regression, 3 March 2026).

---

## Completed Cycles (Recent)

### Cycle-010a: LMSR Market Engine (Local Mode) ✓

**Depends on:** Cycle-008/009 MCP surface (echelon_verify, echelon_hash available)
**Sprints:** 2

Pure LMSR cost function, market lifecycle state machine, trade execution, position tracking, resolution/settlement. Four quant template acceptance tests under LOCAL_MODE.

### Cycle-010b: Engines + Heartbeat ✓

**Depends on:** Cycle-010a (LMSR engine proven in local mode)

Butterfly Engine (wing flaps, stability impact), Paradox Engine (logic gap scanning, spawn/extraction, RealitySignalProvider interface), Entropy Engine (temporal decay). Heartbeat scheduler (AGENT 5s → MARKET 10s → PARADOX 30s → ENTROPY 60s).

### Cycle-011: WorldMonitor Integration ✓

**Depends on:** Cycle-010b (engines for real-time processing)

LiveOSINTRealityProvider wired to Paradox Engine. Three WM domain endpoints (CII, market snapshot, maritime anomaly). Evidence bundle collection with HTTP transcript receipts. Provisional corroboration (WM-only, 0.7 penalty). Counter-signal scaffolding (all UNAVAILABLE, INTELLIGENCE_GAP). Mock-only testing.

### Cycle-012: Sponsored Theatre End-to-End ✓

**Depends on:** Cycle-010a (LMSR), Cycle-010b (engines), Cycle-009 (echelon_status), Cycle-011 (WM pipeline)
**Sprints:** 2 (sprints 23–24) | **Tests:** 83

First externally-commissioned Theatre. Full sponsor workflow and end-to-end lifecycle in local mode: Theatre creation → commitment → trading (stub agents) → OSINT evidence → resolution → settlement → certificate delivery → RLMF export. Stub agents only — no autonomous decisions.

---

## Active Cycle

### Cycle-013: Agent Runtime (T0/T1/T2/T3 + ADK)

**Depends on:** Cycle-012 (defines agent interface via stubs)
**Context file:** `grimoires/loa/context/echelon_cycle_013.md`
**Sprints:** 3

The core agent execution loop — four-tier hierarchical intelligence replacing the three-tier model from System Bible v13 §IX. T0 (context/genome, 0ms, free) → T1 (Qwen 3.5 4B–9B via Ollama, <100ms, local) → T2 (Mistral creative, 200–500ms, personality) → T3 (Sonnet/Opus, 1–5s, deep reasoning). Google ADK for agent framework, novelty threshold routing.

- **Sprint 1:** AgentGenome model, T0 Context Compiler, T1 Rules Engine (parameterised per archetype), T1 decision logging, agent instance lifecycle, agent ↔ LMSR integration
- **Sprint 2:** T2 Personality Engine (Mistral), T3 Deep Reasoning (Sonnet/Opus), novelty threshold router, Ollama/Mistral/Anthropic model providers with graceful fallback
- **Sprint 3:** ADK Agent wrapper, first autonomous Shark agent (≥20 trades over 50 ticks, outperforms lower-skill archetype), multi-agent population (6 archetypes), Theatre integration, P&L aggregation, autonomous E2E test

**What it unlocks:** autonomous market participants producing RLMF training data. The critical gap between infrastructure and a living system.

**T1.5 exploration note:** Qwen 3.5 0.8B is worth testing during 013 as a potential layer between pure rules (T1-RULES) and full local inference (T1-LOCAL-LLM). Small enough to run on-device with near-zero latency, capable enough to handle simple classification ("is this signal anomalous?") that would otherwise need hand-written rules. If viable, agents gain more flexibility than rules at less cost than T2.

---

## Upcoming Cycles

### Cycle-014: Bounded Inquiry Markets

**Depends on:** Cycle-013 (agents) + Cycle-010a (LMSR) + Cycle-011 (evidence pipeline)
**Sprints:** 2 (estimated)

The five inquiry classes (Investigation, Inspection, Audit, Survey, Scrutiny) as live markets with real agents. "Will this construct pass verification by [date]?" as a market with committed parameters, LMSR pricing, and agent participants. This is where RLMF generation starts — agents trading on verification outcomes produce the training data that's the commercial product.

### Cycle-015: WorldMonitor Live Deployment + First Non-WM Collector

**Depends on:** Cycle-011 (WM pipeline), Cycle-014 (bounded inquiries need real evidence)
**Sprints:** 2 (estimated)

Clone the WM fork, deploy locally, flip `@pytest.mark.live_wm` to enabled, verify mock-to-live transition. Then add one non-WM collector — Companies House API (free, no auth, UK jurisdiction, already in registry, settlement-eligible). Breaks the single-source corroboration limitation: WM + Companies House produces `corroboration_minimum_met: true` for UK corporate Theatres.

### Cycle-016: Results Surface

**Depends on:** Cycles 012–015

Full platform UI. By this point: live markets with agents, real OSINT evidence, bounded inquiries producing RLMF data, certificates generated continuously. The results surface shows: Theatres, markets, evidence, convergence alerts, Logic Gap status, certificates, agent P&L, audit trails.

**Design references:**
- **kree8.studio** (Kree8 by Sprrrint) — premium SaaS/tech UI design agency. Use as primary visual language reference for the Results Surface. Dark, polished, modern aesthetic suited to data-dense professional tooling.
- **Spatial Intelligence "God mode"** — globe view with geographic convergence zones, Logic Gap heat maps, and live market prices overlaid on geographic data. Google Photorealistic 3D Tiles as a potential rendering layer (paid API, usage-based pricing).
- **Bounded Inquiry Console** (echelon-inquiry-console.pages.dev) — existing lightweight surface. Evaluate whether upgrading this with live market state from 010a/b should be an earlier deliverable (pre-016) to make the thesis visible sooner.

### Cycle-017: OSINT Registry Expansion

**Depends on:** Cycle-015 (live collectors proven)
**Sprints:** 2 (estimated)

Schema additions: `query_determinism` (settlement gate), `receipt_body_required` (POST/GraphQL receipt rule), `requires_legal_review` (paid source ToS constraint). Tier 2 source stubs: USA Spending, NIH RePORTER, UK Case Law, UK Parliament, AU Patents. Depth, not capability — makes existing Theatres more reliable but doesn't unlock new product surfaces.

Detailed research notes: `echelon core arch/implement/osint_registry_expansion_research_notes.md`

---

## Dependency Graph

```
009 (MCP) ──────────────────────────────┐
010a (LMSR) ─── 010b (Engines) ─── 011 (WM) ──── 012 (Sponsored Theatre)
                                                        │
                                                   013 (Agent Runtime)
                                                        │
                                                   014 (Bounded Inquiries)
                                                        │
                                        015 (WM Live + Non-WM Collector)
                                                        │
                                                   016 (Results Surface)
                                                        │
                                                   017 (Registry Expansion)
```

**Key sequencing decision:** 013 (agents) and 014 (bounded inquiries) are separate cycles. Agents must be proven trading correctly in a controlled market before opening bounded inquiry markets. Combining them risks shipping both half-baked.

---

## Out of Scope (Post Core Cycles)

- On-chain settlement contracts (Solidity, Base Mainnet)
- On-chain commitment hash anchoring (Base Sepolia/Mainnet)
- $ECHELON token deployment and burn mechanics
- ERC-721 agent identity NFTs and ERC-6551 token-bound wallets
- Agent breeding, genealogy mechanics, evolutionary parameter adaptation
- A2A inter-agent coordination (Diplomat coalitions, Spy intelligence sharing)
- Social trading layer (copy trading, leaderboards, Butler integration)
- Berachain PoL integration (eLP-TIMELINE receipt tokens)
- Paid OSINT provider contracts (Polygon.io, RavenPack, Dataminr, Spire Global)
- Hounfour runtime API integration (pending Soju confirmation of API surface)
- Flash Forks (micro-event markets for sports/crypto domains)
- finnNFT Soul certificate attachment (pending Soju confirmation of schema)
- T1 fine-tuning on Echelon-specific data (trade patterns, CII interpretations)

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
