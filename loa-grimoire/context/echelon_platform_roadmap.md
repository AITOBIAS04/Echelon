# Echelon Platform Roadmap

> For Loa context ingestion. This file describes the full build sequence.
> Each cycle has a companion `echelon_cycle_NNN.md` with detailed scope.
> UK British English throughout.

---

## What Is Echelon?

Echelon is an adversarial proving ground for AI agent expertise claims. It makes AI constructs legible — not to a marketplace browser scrolling listings, but to the network itself. Autonomous AI agents and constructs are tested within counterfactual prediction markets (Theatres) powered by real-world data. The system produces:

1. **Calibration certificates** — scored proof of construct accuracy (precision, recall, Brier score, domain-specific criteria)
2. **RLMF training data** — market-derived probability distributions that replace expensive human annotation
3. **Verification-as-service** — recurring revenue from construct creators who need calibration to access higher-tier model routing in the Constructs Network (Hounfour)

The core principle: **constructs must earn the trust that autonomy gives them.** A construct declaring expertise without verification is the equivalent of an automated security scan producing a thick PDF — the sensation of competence without substance.

---

## Partnership Context: Soju / Constructs Network

Soju (0xHoneyJar/Constructs Network) has validated Echelon as the verification substrate for his entire ecosystem. Key events:

- **loa#379** — RFC titled "Constructs must earn the trust that constraint yielding gives them". Three addenda mapping Echelon's verification pipeline as foundational infrastructure for construct trust.
- **AITOBIAS04/Echelon#34** — Three concrete Product Theatre templates filed directly on Echelon's repo (Observer, Easel, Cartograph).
- **Three research agents** deployed across Echelon's `feature/community-oracle-verification` branch, confirming the 4-stage pipeline works and the OracleAdapter pattern is correct.
- **Verification tier system** (UNVERIFIED → BACKTESTED → PROVEN) designed to depend on Echelon calibration certificates.

Soju's direct quote: "The construct marketplace without this is a listings page. With it, it's an expertise market where the signals are real."

### The Integration Seam

One field change in `expertise.yaml` bridges the two systems:

```yaml
domains:
  - name: "Design Systems"
    depth: 5
    verified:
      tier: BACKTESTED
      certificate_id: "uuid"
      brier: 0.18
      replay_count: 50
      criteria: "visual_approval + wcag_compliance + taste_token_adherence"
      last_verified: "2026-02-19"
```

The `criteria` field is domain-specific and human-defined — not a universal score. Each construct defines what matters for its domain, Echelon measures it, and the certificate makes it legible to the network.

### Verification Tiers (maps to Arrakis conviction scoring and Hounfour routing)

| Tier | Meaning | How Earned | Hounfour Routing |
|------|---------|------------|------------------|
| UNVERIFIED | Self-declared capabilities only | Published manifest | Restricted to baseline model pools |
| BACKTESTED | Calibration scores against historical outcomes | Product Theatre replays via Echelon | Mid-tier brigade routing |
| PROVEN | Production track record with measurable outcomes | N months of verification evidence + community attestation | Premium model pools, full kitchen brigade |

Only BACKTESTED+ constructs should be eligible for constraint yielding (skipping Loa's quality gates). An UNVERIFIED construct declaring `review: skip` should be treated as `review: full`.

---

## Two Theatre Families

Echelon supports two distinct Theatre families. **Product Theatres are the primary revenue engine** because their ground truth is free. Geopolitical Theatres come later, funded by Product Theatre revenue.

### Product Theatres (Phase 1 — current priority)

Ground truth is engineering data that already exists: GitHub diffs, CI output, provenance records, WCAG audit results, pipeline QA scores. Cost: essentially free.

Three concrete templates filed by Soju (Echelon#34):

| Template | Construct | What It Tests | Ground Truth Source |
|----------|-----------|---------------|---------------------|
| PRODUCT_OBSERVER_V1 | Observer (user research) | Source fidelity, signal classification, canvas enrichment freshness | 163 provenance records (append-only JSONL, SHA-256 hash chain) |
| PRODUCT_EASEL_V1 | Easel (creative direction) | Vocabulary/TDR decision propagation through downstream constructs | TDR records + Artisan /inscribe compliance output |
| PRODUCT_CARTOGRAPH_V1 | Cartograph (spatial accuracy) | Isometric convention compliance, hex grid accuracy | Deterministic — maths, not taste |

Key insight from Soju: "Building Product Theatres for real constructs reveals what verification tiers actually mean in practice. Observer: PROVEN candidate. Easel: BACKTESTED candidate. Cartograph: UNVERIFIED — 3/4 skills are stubs."

### Geopolitical Theatres (Phase 2 — funded by Phase 1)

Ground truth is enterprise OSINT data: GDELT, Polygon.io, RavenPack, Dataminr, Spire Global AIS. Cost: $1,400–2,600/month. Only viable once verification-as-service revenue is flowing.

---

## Architecture Reference (System Bible v10)

The canonical architecture document is `docs/core/System_Bible_v10.md` in the repo. Key components referenced across cycles:

| Component | System Bible Section | Purpose |
|-----------|---------------------|---------|
| LMSR Market Engine | §III | Cost function: C(x) = b · ln(Σ exp(xⱼ / b)). Committed liquidity. |
| Theatre Templates | §II, §X | JSON schema defining market lifecycle, fork points, resolution rules |
| Resolution State Machine | §IV | Pre-committed oracle programmes, deterministic settlement |
| Paradox Engine | §V | Logic Gap detection, circuit breakers, self-policing |
| Commitment Protocol | §VI | Immutable parameter publication before trading opens |
| VRF Integration | §VII | Chainlink V2 randomness for perturbation injection |
| Agent Architecture | §VIII | Four archetypes (Shark, Spy, Diplomat, Saboteur), ERC-8004 passports |
| Hierarchical Brain | §IX | Three-tier intelligence: heuristic → personality → narrative (LLM) |
| RLMF Export | §XI | Market-derived training data in standardised export format |
| Token Economics | §XII | $ECHELON token, deflationary burn mechanics, DAO governance |

Schema files: `docs/schemas/echelon_theatre_schema.json`, `docs/schemas/echelon_rlmf_schema.json`

---

## Existing Codebase

### Pre-Loa (180K LOC)

The repo at `/Users/tobyharber/Developer/prediction-market-monorepo.nosync` contains:

| Component | Status | Notes |
|-----------|--------|-------|
| CPMM market logic | Exists but WRONG | System Bible specifies LMSR, not CPMM. Must be replaced. |
| Agent brain (multi-provider routing) | Exists | Groq/OpenAI/Ollama routing. Reusable pattern. |
| Shark trading strategies | Exists | Partial. Only one archetype implemented. |
| Wallet factory (HD derivation) | Exists | Needs integration with Theatre lifecycle. |
| 5 Solidity contracts | Exist | Base Sepolia deployment. Need audit against System Bible. |
| React frontend (demo engine) | Exists | Mock data driven. Situation Room layout. |
| FastAPI backend (SQLAlchemy) | Exists | Auth, routes, demo store API. |
| Butterfly Engine scaffolding | Partial | Timeline divergence logic started, not complete. |
| Paradox Engine scaffolding | Partial | Logic Gap concept present, circuit breakers not wired. |

**Drift score: MODERATE (6/10)** — documented in `grimoires/loa/drift-report.md`.

### Loa Cycles Completed

| Cycle | Name | Sprints | What It Built |
|-------|------|---------|---------------|
| 026 | Hounfour Runtime Bridge | 9 | Integration layer between Echelon verification and Hounfour model routing |
| 027 | Community Oracle Verification Pipeline | 5 | GitHub PR ingestion → construct scoring → calibration certificate generation |
| 028 | Backend Wiring | 3 | API endpoints connecting verification pipeline to FastAPI backend |
| 029 | Verification Dashboard | Archived | Frontend display for verification run status and certificates |

131 tests passing across cycles 026–028. All greenfield — none touches the existing 180K LOC.

### Known Bugs (from Soju's research agents, loa#379)

Three implementation gaps in `feature/community-oracle-verification`:

1. `scoring/base.py` — ABC (Abstract Base Class) missing
2. Prompt templates — not created yet
3. CLI argument signature — mismatch with click interface

These are bugs, not architecture problems. Fix before starting Cycle-030.

---

## Build Sequence (Cycles 030–036)

Each cycle produces something the next one consumes. **030 and 031 can be built in either order** — Product Theatres (Replay Engine) have no LMSR dependency. Market Theatre execution requires 030. **032 → 033 → 034 is a strict dependency chain after both 030 and 031 are complete.** 035 and 036 can run in parallel once 034 lands.

### Cycle-030: LMSR Market Engine

**Depends on:** Nothing (foundational)
**Produces:** Market engine consumed by every subsequent cycle

Replace the existing CPMM with a correct LMSR implementation per System Bible §III.

Core deliverables:
- Cost function: `C(x) = b · ln(Σ exp(xⱼ / b))`
- Price function: `p_i(x) = exp(x_i / b) / Σ exp(x_j / b)` (always on probability simplex)
- Trade execution: calculate cost to move from state x to state x' as `C(x') - C(x)`
- Committed liquidity parameter `b` — locked at market creation, determines price sensitivity
- Maximum market maker loss bounded at `b · ln(n)` where n = number of outcomes
- Price impact curve calculation for UI consumption
- No frontend, no agents, no OSINT — pure mathematical engine with comprehensive property-based tests

---

### Cycle-031: Theatre Template Engine

**Depends on:** Nothing for Product Theatres (Replay Engine). Cycle-030 (LMSR) for Market Theatre execution.
**Produces:** Theatre lifecycle, Replay Engine, unified calibration certificate schema — consumed by every subsequent cycle.

Build the Theatre as a state machine per System Bible §II, §IV, §VI. **Two distinct execution paths:**

- **Replay Theatres (Product Theatres):** commit → invoke real construct via OracleAdapter → score against ground truth → issue certificate. No LMSR, no agents, no trading. Ships immediately. This is what Soju needs now.
- **Market Theatres (Geopolitical Theatres):** full LMSR lifecycle. Schema-only this cycle — execution plugs in when Cycle-030 lands.

Core deliverables:
- Theatre lifecycle states: `DRAFT → COMMITTED → ACTIVE → SETTLING → RESOLVED → ARCHIVED`
- Commitment hash over **full canonical template JSON** + version pins + dataset hashes (not selected fields)
- Replay Engine: real OracleAdapter invocation (HTTP or local) for Product Theatres
- Structured criteria: `criteria_ids` (list[str]) + `criteria_human` (str) + `weights` (dict) — not freeform strings
- Version pinning: exact construct commit hashes for every oracle step (critical for compositional chains like Easel → Artisan → Mint)
- Unified calibration certificate schema covering both replay and market outputs
- Verification tier rules (v0): UNVERIFIED (< 50 replays), BACKTESTED (≥ 50 + pins), PROVEN (BACKTESTED + production telemetry + attestation). Expiry: 90/180 days.
- Resolution State Machine with support for pre-committed HITL steps (rubric, identity separation)
- Test fixtures: PRODUCT_OBSERVER_V1, PRODUCT_EASEL_V1, PRODUCT_CARTOGRAPH_V1 (from Echelon#34) — all with real construct invocation

Key constraint: the `criteria_ids` field in each template is domain-specific and human-defined. Observer measures `source_fidelity`. Cartograph measures `hex_grid_accuracy`. The engine must not impose universal metrics.

---

### Cycle-032: OSINT Adapter Layer (Placeholder Architecture)

**Depends on:** Cycle-031 (Theatre engine, for Evidence Bundle → Theatre linking)
**Produces:** Data ingestion interface consumed by agents and Paradox Engine

Build the adapter abstraction — NOT the actual OSINT pipeline. System Bible §OSINT Appendix.

Core deliverables:
- Evidence Bundle schema: `bundle_id`, `raw_payload`, `retrieval_receipt`, `content_hash` (SHA-256), `structured_extract`, `confidence_score`, `theatre_id`
- Adapter interface: any data source implements `ingest() → EvidenceBundle`
- Mock adapter: generates plausible geopolitical anomalies on randomised timer (for demos and testing)
- GitHub adapter: pulls PR diffs and CI output (reuses Cycle-027 Community Oracle ingestion)
- Provenance adapter: ingests construct provenance records (Observer's 163-record JSONL, hash chain verification)
- Merkle root publication: periodic hash over new evidence bundles (off-chain for MVP)
- Engagement Score calculation: narrative strength, timeliness, OSINT richness, stakes

Key constraint: adapter interface must be source-agnostic. Adding GDELT, Polygon.io, Spire Global later means writing a new adapter class, not changing the engine. This is the "flip the switch" architecture.

---

### Cycle-033: Agent Architecture

**Depends on:** Cycle-030 (LMSR for trading), Cycle-031 (Theatre for execution context), Cycle-032 (OSINT for decision inputs)
**Produces:** Trading agents consumed by simulation and Paradox Engine

Build the four archetype system per System Bible §VIII, §IX and `docs/technical/archetype_matrix.md`.

Core deliverables:
- Four archetypes: Shark, Spy, Diplomat, Saboteur
- Quantitative parameters per archetype: risk_appetite, evidence_sensitivity, exploration_rate, position_limits, decision_policy (softmax with noise and bias)
- Hierarchical Intelligence Architecture:
  - Layer 1 (Execution): sub-10ms heuristic decisions. Covers ~90% of actions.
  - Layer 1.5 (Personality): lightweight creative model for agent voice/style
  - Layer 2 (Narrative): LLM routing only when novelty threshold breached. ~10% of actions.
- Agent identity: ERC-721 NFT concept with persistent genome, genealogy tracking
- Wallet integration: each agent has own wallet, manages own capital within Theatre
- Decision loop: observe data → evaluate against archetype parameters → decide action (buy/sell/shield/sabotage) → execute against LMSR market

Key constraint: agents must be profitable to survive (Agent Tax problem — inference costs < trading revenue). Layer 1 must handle 90%+ of decisions to keep costs viable.

---

### Cycle-034: Paradox Engine + VRF Integration

**Depends on:** Cycle-030 (markets), Cycle-032 (OSINT data), Cycle-033 (agents to monitor)
**Produces:** Self-policing layer consumed by Theatre lifecycle and agent penalties

Build the integrity mechanisms per System Bible §V, §VII.

Core deliverables:
- Logic Gap calculation: divergence between market-implied probability and ground-truth data
- Paradox detection: when Logic Gap exceeds committed threshold, trigger circuit breaker
- Circuit breaker actions: trading pause, position freeze, forced resolution
- VRF integration (stubbed for local): randomised execution windows, threshold perturbation, episode sampling
- Entropy pricing: dynamic risk adjustment based on market volatility and agent behaviour
- Collusion detection: identify coordinated position-taking across agents
- Paradox resolution: penalty distribution (token burn, position liquidation)

Key constraint: Paradox thresholds committed at Theatre creation (immutable). Circuit breakers must be deterministic.

---

### Cycle-035: Theatre Command UI

**Depends on:** Cycles 030–034 (backend systems to surface)
**Produces:** User-facing interface for the full platform

Build the Theatre Command interface wired to real backend APIs.

Core deliverables:
- OSINT Ticker sidebar: live feed from OSINT adapter layer (Cycle-032), including Product Theatre signals (GitHub events, provenance updates)
- Theatre configuration: anomaly selection → fork points → LMSR parameter → commitment
- Commitment Ceremony: four-stage ignition sequence surfacing real hashes (commitment hash → liquidity lock → VRF seeding → state machine spawn)
- Deployed Theatre view: timeline branching visualisation, live agent positions, price curves
- Verification dashboard integration (from Cycle-029): construct calibration scores, certificate viewer
- Situation Room: active Theatre monitoring, agent leaderboards, Paradox alerts

Key constraint: dark mode, mission control aesthetic. Must include PRODUCT category signals alongside geopolitical categories. All data from real backend.

---

### Cycle-036: Multi-Agent Simulation

**Depends on:** All previous cycles
**Produces:** Validated end-to-end system, RLMF export proof, game theory validation

Full integration test: multiple agents/constructs tested within Theatres.

Core deliverables:
- Simulation harness: spawn Theatre, populate with agents, feed data, run to settlement
- Product Theatre simulation: run Soju's three templates (Observer, Easel, Cartograph) end-to-end
- Agent population mix testing: vary archetype ratios, measure price discovery quality
- Paradox Engine stress testing: inject collusion scenarios, verify detection
- RLMF export validation: produce training data, verify schema compliance
- Calibration certificate generation: end-to-end from Theatre replay to certificate attached to construct identity
- Performance profiling: agent inference costs vs trading revenue (Agent Tax validation)

---

## Out of Scope (Post Cycle-036)

These are mainnet/production concerns. Do not build until the core simulation loop works:

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

## How to Use This File

1. This file lives at `loa-grimoire/context/echelon_platform_roadmap.md`
2. Before starting a new cycle, also place the cycle-specific file (e.g., `echelon_cycle_030.md`) in `loa-grimoire/context/`
3. Remove the previous cycle's context file to keep Loa focused
4. Remove the old `echelon_context.md` (Phase 1 scope — now superseded by this roadmap)
5. The roadmap file stays — it gives Loa the big picture without overwhelming it with detail
6. Run `/plan` and Loa will read both files to generate the PRD
