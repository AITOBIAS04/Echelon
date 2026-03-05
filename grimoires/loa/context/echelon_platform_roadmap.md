# Echelon Platform Roadmap

> For Loa context ingestion. This file describes the full build sequence.
> Each cycle has a companion `echelon_cycle_NNN.md` with detailed scope.
> UK British English throughout.
> **Last updated:** 4 March 2026

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

**Test baseline (post 015):** ≥942 passed (full suite), 4 skipped, 13 pre-existing collection errors (same node IDs, environment-specific). MCP suite: 102 passed (33 new from 013 Gate C). 4 March 2026.

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

### Cycle-013: Agent Runtime (T0/T1/T2/T3 + ADK) ✓

**Depends on:** Cycle-012 (defines agent interface via stubs)
**Sprints:** 3 | **Tests:** 741

Four-tier hierarchical intelligence: T0 (context/genome) → T1-RULES (parameterised per archetype) → T2 (Mistral creative personality) → T3 (Sonnet/Opus deep reasoning). Google ADK agent framework, novelty threshold routing, 6 autonomous archetypes trading in local-mode LMSR. Shark agent outperforms lower-skill archetypes. Full Codex remediation: deterministic SHA-256 seeding (E1), fractional evidence coverage (E4), `ACTIVE_TIERS` scope annotation (E2), MCP auth/transport hardening (C1+C2), baseline drift cleanup (D1–D3).

### Cycle-014: Bounded Inquiry Markets ✓

**Depends on:** Cycle-013 (agents) + Cycle-010a (LMSR) + Cycle-011 (evidence pipeline)
**Sprints:** 2 | **Tests:** 922 (181 new from 014 sprints + remediation)

Canonical inquiry-class taxonomy (Counterfactual, Investigative, Inspection, Survey, Scrutiny) threaded through every layer: schema, database, API, runtime, templates, certificates. Inquiry class stops being a System Bible definition and becomes a first-class runtime concept — influencing resolution triggers, evidence accumulation rules, and agent behaviour weighting. One template per inquiry class, one E2E test per class. Full Codex remediation: production wiring for agent spawn (F1), settlement enforcement with `check_resolution_ready()` (F2), certificate metadata (F3), Alembic migration (F4), API null rejection (F5).

### Cycle-014b: Genome Runtime Integration ✓

**Depends on:** Cycle-013 (agent runtime) + Cycle-014 (inquiry taxonomy)
**Sprints:** 1 | **Tests:** 932 (10 new from genome loader + validator CI)

Bridge the T0 genome YAML spec to the production agent runtime. Extended `AgentGenome` with structured sub-models (TierProfile, DecisionPolicy, ParadoxBehaviour, InquiryClassAffinity, SuccessMetrics). YAML loader (`genome_loader.py`) with `load_genome()`, `load_genome_pack()`, `compute_commitment_hash()`. Wired into `spawn_agents()` with deterministic variant selection and factory fallback. PyYAML dependency added. No global state mutation. Validator CI integration via pytest wrapper.

### Cycle-015: WorldMonitor Live Deployment + First Non-WM Collector ✓

**Depends on:** Cycle-011 (WM pipeline), Cycle-014 (bounded inquiries need real evidence)
**Sprints:** 2 | **Tests:** ≥942 (10+ new from live WM tests + Companies House collector)

Cloned WM fork, deployed locally, flipped `@pytest.mark.live_wm` to enabled, verified mock-to-live transition. Added Companies House API as first non-WM collector (free, no auth, UK jurisdiction, settlement-eligible). Registry bumped to v0.4.0-wm-ch (4 sources). Breaks the single-source corroboration limitation: WM + Companies House produces `corroboration_minimum_met: true` for UK corporate Theatres.

---

## Active Cycle

### Cycle-014c: Investigation Toolset Implementation

**Depends on:** Cycle-014 (bounded inquiry lifecycle), Cycle-013 (agent runtime), Cycle-010a (LMSR)
**Context file:** `grimoires/loa/context/echelon_cycle_014c.md`
**Design input:** `echelon core arch/implement/Echelon_Investigation_Toolset_Design_Note_v1.md` (v1.3.0)
**Sprints:** 3 | **Expected tests:** ≥970 (38+ new)

Runtime models, services, and hashing infrastructure for the 8-tool investigation toolset: Evidence Envelope (append-only, provenance classes, Merkle hashing), Claim Graph (FACT/CAUSAL/ATTRIBUTION claims, Merkle root), investigation counter-signals (11-class taxonomy separate from pipeline counter-signals), Commitment Monitor (drift detection), Signal Scanner (DeltaBrief output, domain filters), Entity Resolver (multi-source profiles), Investigation Certificate extension (30+ fields, routing logic), and stop condition wiring (outcome/evidence threshold/sponsor-defined). New `backend/investigation/` package. All tools use mock/stub backends — does NOT depend on 015 live collectors.

### Cycle-016: Results Surface

**Depends on:** Cycles 012–015 (all complete), Cycle-014c (investigation toolset)
**Context file:** `grimoires/loa/context/echelon_cycle_016.md`
**Design input:** `Echelon_Butterfly_Entropy_Coherence_Review_v1.md` (Sprint 1 pre-work — engine unification, taxonomy extension, anchor/fork model)
**Sprints:** 5 | **Expected tests:** ≥1060 (50+ new across frontend + backend)

Full frontend reconciliation + new investigation views. Sprint 1 pre-work resolves Butterfly/Entropy engine coherence gaps (stability scale 0–1 unification, WingFlap taxonomy extension with MIRROR_SYNC/EVIDENCE/CLAIM/COUNTER_SIGNAL types, anchor/fork data model, inquiry-aware entropy, creator fee model). The existing frontend is ~70% mock/presentation with only Verification + Theatre pages properly wired. 5 sprints: (1) Engine coherence remediation + mock purge — wire Portfolio, Marketplace, Agents, Paradox, Watchlist to real backend APIs, fix TypeScript types, (2) Investigation dashboard + certificate explorer + investigation API routes, (3) OpsBoard rebuild as aggregation dashboard + Analytics foundation from real data + RLMF redesign as export viewer + VRF page → informational, (4) Investigation creation wizard + progress tracker + navigation redesign + signal feed migration, (5) Convergence map + agent analytics + WebSocket integration + responsive polish + final mock purge audit. Retires echelon-inquiry-console app. kree8.studio visual identity applied throughout.

### Cycle-017: OSINT Registry Expansion

**Depends on:** Cycle-015 (live collectors proven)
**Sprints:** 2 (estimated)

Schema additions: `query_determinism` (settlement gate), `receipt_body_required` (POST/GraphQL receipt rule), `requires_legal_review` (paid source ToS constraint). Tier 2 source stubs: USA Spending, NIH RePORTER, UK Case Law, UK Parliament, AU Patents. Depth, not capability — makes existing Theatres more reliable but doesn't unlock new product surfaces.

**Reference material (Obsidian `echelon core arch/implement/`):**
- `osint_registry_expansion_research_notes.md` — Source assessments, schema additions, dependency analysis, build priority tiers
- `Echelon_Intelligence_Database_Expansion_v1_0.md` — Full v1.0.0 collector manifest (160+ sources, 30 source groups, 7 consumption surfaces, Tier A/B/C classification, SitDeck parity)
- `Echelon_OSINT_Registry_Rate_Limits_v1.md` — Operational rate limit reference for all 77 registry sources (v0.6.0)
- `registry_v060_expansion.json` — JSON payload for 9 sources added in v0.6.0 (UK judicial/legislative + sovereign financial)
- `Echelon_Valyu_OSINT_Reverse_Engineering_v1.docx` — Valyu.ai source reverse-engineering, registry gap analysis, phased expansion path

---

## Dependency Graph

```
009 (MCP) ──────────────────────────────┐
010a (LMSR) ─── 010b (Engines) ─── 011 (WM) ──── 012 (Sponsored Theatre)
                                                        │
                                                   013 (Agent Runtime)
                                                        │
                                                   014 (Bounded Inquiries)
                                                      ├───────────────────────┐
                                        015 (WM Live + Non-WM Collector)    014c (Investigation Toolset)
                                                      │                       │
                                                   016 (Results Surface) ◄────┘
                                                        │
                                                   017 (Registry Expansion)
```

**Key sequencing decisions:**
- 013 (agents) and 014 (bounded inquiries) are separate cycles. Agents must be proven trading correctly in a controlled market before opening bounded inquiry markets. Combining them risks shipping both half-baked.
- 014c (investigation toolset) and 015 (live collectors) run in parallel — 014c uses mock backends and does not depend on live collectors. Both feed into 016 (results surface).

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
5. Run `/plan-and-analyze` and Loa will read both files to generate the PRD
