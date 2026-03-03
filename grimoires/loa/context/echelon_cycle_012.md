# Cycle-012 — Sponsored Theatre End-to-End

**Cycle:** cycle-012
**Name:** Sponsored Theatre End-to-End
**Predecessor:** cycle-010a (LMSR engine), cycle-010b (engines + heartbeat), cycle-009 (echelon_status MCP), cycle-011 (WorldMonitor OSINT pipeline)
**Location:** `~/Developer/prediction-market-monorepo.nosync`
**Sprint count:** 2
**Tooling:** Claude Code + Loa (`/plan` → `/simstim` → `/run-bridge`)

---

## Cycle Objective

Build the sponsor workflow and end-to-end market lifecycle in local mode. A Sponsored Theatre is an externally-commissioned prediction market: the sponsor defines the question, Echelon configures the Theatre with committed parameters, seeds LMSR liquidity, monitors with OSINT, and delivers a cryptographically verifiable certificate at resolution.

Cycle-012 wires together everything built in 010a/010b/011 into a single end-to-end flow: Theatre creation → commitment → trading (with stub agents) → OSINT evidence collection → resolution → settlement → certificate delivery → RLMF export. All evidence uses mock fixtures (WM not deployed locally) and on-chain anchoring is stubbed. The sponsor onboarding workflow is real; the data flowing through it is simulated.

**Critical constraint:** agents in 012 are stubs — identity objects that submit trades via direct function calls. Nobody is actually deciding to trade autonomously. The agent runtime (T0/T1/T2/T3 decision loop) is Cycle-013. Cycle-012 proves the infrastructure works; Cycle-013 fills it with autonomous participants.

**What success looks like:** one Companies House Theatre (e.g., "Will Acme Ltd file annual accounts by statutory deadline?") runs from creation through settlement in local mode, produces a valid certificate passing all 21 verifier checks, with a complete evidence chain from mock WM fixtures.

---

## What Exists (Relevant to This Cycle)

### LMSR Market Engine (Cycle-010a — complete)

Proven local-mode LMSR engine at `backend/market/`:

| Module | What It Does |
|--------|-------------|
| `lmsr.py` | Pure cost function: C(x) = b · ln(Σ exp(xⱼ / b)), prices, trade cost. Log-sum-exp numerically stable. |
| `state.py` | MarketPhase enum (CREATED → COMMITTED → TRADING → RESOLVING → SETTLED), FeeSchedule, MarketState container. |
| `lifecycle.py` | Forward-only phase transitions. `create_market()` factory. |
| `trading.py` | TradingEngine.execute_trade() — atomic execution, mutates state vector + positions. |
| `positions.py` | In-memory position tracking: AgentPosition (shares, net_cashflow, realised_pnl, trade_count). |
| `resolution.py` | Deterministic settlement: AgentSettlement, SettlementReport with settlement_hash. |
| `commitment.py` | SHA-256 commitment hash over Echelon Canonical JSON v0. Immutable after COMMITTED phase. |
| `fees.py` | FeeSchedule (trade_fee_bps, resolution_fee_bps). Frozen at commitment. |
| `exceptions.py` | InvalidPhaseTransition, ParameterMutationAfterCommit, TradingHalted, InsufficientBalance, InsufficientShares. |

### Engines + Heartbeat (Cycle-010b — complete)

- Butterfly Engine: wing flaps, stability impact on markets
- Paradox Engine: Logic Gap scanning, spawn/extraction, RealitySignalProvider interface
- Entropy Engine: temporal stability decay
- Heartbeat scheduler: AGENT 5s → MARKET 10s → PARADOX 30s → ENTROPY 60s
- `echelon_status` MCP integration for live market state queries

### WorldMonitor OSINT Pipeline (Cycle-011 — complete)

- LiveOSINTRealityProvider wired to Paradox Engine
- Three WM domain endpoints: CII, market snapshot, maritime anomaly
- Evidence bundle collection with HTTP transcript receipts
- Corroboration engine (provisional — WM-only, 0.7 penalty)
- Counter-signal scaffolding (all 11 classes UNAVAILABLE, INTELLIGENCE_GAP)
- Convergence detection (1°×1° cells, 24h window, 3+ WMDomain values)
- Mock-only testing with JSON fixtures from Pydantic schemas

### Theatre Infrastructure (Existing Codebase)

| Component | Location | Status |
|-----------|----------|--------|
| Theatre API routes | `backend/api/theatre_routes.py` | 12 endpoints. Auth-protected mutations, public reads. |
| Theatre schemas | `backend/schemas/theatre.py` | TheatreCreate, TheatreRunRequest, TheatreSettleRequest, response schemas. |
| Theatre bridge | `backend/services/theatre_bridge.py` | TheatreStateMachine, CommitmentProtocol, ReplayEngine adapter. Runs lifecycle as background task. |
| Database models | `backend/database/models.py` | Theatre, TheatreTemplate, TheatreCertificate SQLAlchemy models. |
| Template library | `fixtures/` | 10 templates across 4 verticals. |

### MCP Surface (Cycle-008/009)

- `echelon_verify` — validates certificates against evidence bundles
- `echelon_hash` — computes commitment hashes
- `echelon_status` — live market/certificate state queries
- `echelon_calibrate` — runs calibration scoring

---

## What Does NOT Exist Yet

These are the gaps Cycle-012 fills:

1. **Sponsor onboarding workflow** — no mechanism for an external entity to commission a Theatre, review committed parameters, and approve the commitment hash before capital is escrowed.
2. **Theatre creation CLI/API for sponsors** — the existing Theatre API (`theatre_routes.py`) handles internal template execution, not sponsor-driven market configuration.
3. **LMSR ↔ Theatre wiring** — the LMSR engine (`backend/market/`) and Theatre infrastructure (`backend/services/theatre_bridge.py`) are not yet connected. Trades in an LMSR market don't flow through the Theatre lifecycle.
4. **Stub agent population** — no mechanism to spawn a set of agent stubs into a Theatre to produce trading activity against the LMSR. Agent files exist (`backend/agents/`) but aren't wired to the LMSR trading engine.
5. **OSINT → Theatre evidence flow** — the WM pipeline (011) produces evidence bundles, but they don't flow into Theatre resolution. The Composed Oracle doesn't yet consume live evidence for a specific Theatre's committed sources.
6. **Certificate delivery pipeline** — certificates exist as schema objects and pass verifier checks, but there's no automated pipeline from settlement → certificate generation → evidence bundle packaging → hash anchoring → delivery.
7. **Sponsor agreement / terms template** — no structured document defining commitment terms, liability, and deliverable schedule for the sponsor relationship.

---

## Architecture: Sponsored Theatre Lifecycle

The lifecycle follows the Sponsored Theatre Programme v1 spec (6-step flow):

```
COMMISSION → COMMITMENT → TRADING → RESOLUTION → SETTLEMENT → DELIVERY

  Sponsor        Echelon          LMSR             OSINT           Oracle
    │               │               │                │               │
    ├──define Q──►  │               │                │               │
    │               ├──configure──► │                │               │
    │               │  template     │                │               │
    │               ├──select───────────────────────►│               │
    │               │  sources      │                │               │
    │  ◄──review────┤               │                │               │
    │   commitment  │               │                │               │
    ├──approve──►   │               │                │               │
    │               ├──freeze───►  │                │               │
    │               │  params       │                │               │
    │               │               ├──stub agents──►│               │
    │               │               │  trade          │               │
    │               │               │                ├──collect──►   │
    │               │               │                │  evidence      │
    │               │               │                │               ├──evaluate
    │               │               │                │               │  criteria
    │               │               ├──settle◄───────────────────────┤
    │               │               │                │               │
    │  ◄──deliver───┤               │                │               │
    │   certificate │               │                │               │
```

### Key Integration Points

**1. LMSR ↔ Theatre:** The Theatre's committed parameters (outcome labels, resolution date, OSINT sources) are frozen at commitment. The LMSR engine's `b` parameter, fee schedule, and outcome structure are derived from the Theatre template and locked via `commitment.py`.

**2. OSINT ↔ Theatre:** The Theatre's `oracle_config.committed_sources` field maps to OSINT registry source IDs. During the trading phase, the WM pipeline collects evidence against these sources. At resolution, the Composed Oracle evaluates evidence bundles against the Theatre's committed criteria.

**3. Stub Agents ↔ LMSR:** Agent stubs are simple objects with an `agent_id`, archetype label, initial balance, and a deterministic trading strategy (e.g., "buy outcome 0 if CII > threshold"). They call `TradingEngine.execute_trade()` directly — no T1/T2/T3 reasoning, no personality, no autonomous decisions.

**4. Settlement ↔ Certificate:** After resolution, `ResolutionEngine.settle()` produces a `SettlementReport`. The certificate pipeline wraps this with the evidence bundle hash, OSINT source manifest, corroboration status, counter-signal results, and composite score into a calibration certificate conforming to the v1.0.0 schema.

---

## Sprint 1 — Theatre Creation + Sponsor Onboarding + LMSR Wiring

### What It Is

The creation and commitment phases. A sponsor can define a question, Echelon configures a Theatre with committed LMSR parameters, the sponsor reviews the commitment hash, and upon approval the parameters are frozen and the market opens for trading.

### Sprint 1 Tasks

**1. SponsoredTheatreConfig model**
Pydantic v2 model capturing sponsor-provided configuration:
- `question: str` — the Theatre question (e.g., "Will Acme Ltd file annual accounts by 30 Sep 2026?")
- `resolution_date: datetime` — when the market resolves
- `committed_sources: list[str]` — OSINT registry source IDs for settlement
- `outcome_labels: list[str]` — e.g., ["Filed on time", "Filed late", "Not filed"]
- `liquidity_b: Decimal` — LMSR `b` parameter (sponsor's seeding capital)
- `fee_schedule: FeeSchedule` — trade and resolution fee configuration
- `sponsor_id: str` — sponsor identifier
- `sponsor_metadata: dict` — freeform sponsor context (company name, jurisdiction, etc.)

**2. Theatre creation service**
`backend/services/sponsored_theatre.py` — orchestrates Theatre creation from SponsoredTheatreConfig:
- Validates `committed_sources` against OSINT registry (all source IDs must exist and be in the correct jurisdiction). Sources may be settlement-eligible or provisional — provisional sources (e.g., WM endpoints with shared upstream_id) are accepted but flagged in the source manifest with `settlement_status: PROVISIONAL` and the corroboration penalty carries through to the certificate.
- Creates LMSR MarketState via `MarketLifecycle.create_market()`
- Generates TheatreTemplate from config + market parameters
- Computes commitment hash via `MarketCommitment.compute_hash()`
- Returns a SponsorReviewPackage containing: template JSON, commitment hash, worst-case loss (`b * ln(n)`), source manifest, fee schedule breakdown
- **Note on `b`:** `b` is not escrowed capital. It parameterises liquidity depth and bounds the market maker's worst-case loss. The sponsor may or may not deposit `b·ln(n)` as collateral — that's a business decision, not an LMSR invariant.

**3. Sponsor review endpoint**
`POST /api/v1/sponsored-theatres` — creates a sponsored Theatre in CREATED state.
`GET /api/v1/sponsored-theatres/{id}/review` — returns the SponsorReviewPackage for sponsor approval.
`POST /api/v1/sponsored-theatres/{id}/commit` — sponsor approves, transitions to COMMITTED, freezes all parameters.

**4. LMSR ↔ Theatre integration layer**
`backend/services/market_theatre_bridge.py` — connects the LMSR engine to the Theatre lifecycle:
- `create_market_for_theatre(theatre_id, config)` → creates MarketState, PositionManager, attaches to Theatre
- `get_market_state(theatre_id)` → returns current LMSR state (prices, phase, positions)
- `transition_market(theatre_id, target_phase)` → validates and executes phase transition
- Stores LMSR state in Theatre's database record (JSON serialisation of MarketState)

**5. Stub agent spawner**
`backend/services/stub_agents.py` — creates a population of agent stubs for a Theatre:
- Input: Theatre ID, agent count (default 6 — one per archetype), initial balance per agent
- Each stub is a dataclass: `StubAgent(agent_id, archetype, balance, strategy)`
- Strategy is a simple function: `(market_state, evidence) → Optional[TradeIntent]`
- Default strategies per archetype:
  - Shark: buy the leading outcome if price < 0.7
  - Spy: trade when new evidence arrives (evidence-triggered)
  - Diplomat: stabilise — buy the trailing outcome if spread > 0.4
  - Saboteur: random contrary trades at low volume
  - Whale: single large position early, hold to settlement
  - Degen: random trades every tick
- Stubs call `TradingEngine.execute_trade()` directly — no agent runtime, no LLM
- Purpose: produce realistic trading activity and P&L data for the first Theatre

**6. Commitment protocol integration**
Wire `MarketCommitment.compute_hash()` into the Theatre creation flow. The commitment hash covers:
- LMSR parameters: `b`, fee_schedule, n_outcomes, outcome_labels
- Oracle config: committed_sources, resolution_date, corroboration_minimum
- Theatre metadata: template_id, version pins
Verify that `commitment.verify_hash()` passes after freeze. Store commitment hash in Theatre database record and (future) on-chain anchor.

**7. Source manifest builder**
`backend/osint/source_manifest.py` — builds the OSINT source manifest for a Theatre's committed sources:
- Input: list of registry source IDs
- Output: structured manifest with: source_id, source_group, independence_upstream_id, jurisdiction, access_surface, settlement_eligibility
- Validated against the OSINT registry version pinned in repo (`backend/osint/registry.json`)
- Included in commitment hash and certificate

**8. Theatre creation tests**
- `backend/services/tests/test_sponsored_theatre.py`
- Test cases: valid creation, invalid sources (non-existent, wrong jurisdiction), provisional source flagging (WM endpoints accepted with PROVISIONAL status), commitment freeze immutability, sponsor review package completeness, worst-case loss calculation, source manifest validation

**9. LMSR-Theatre bridge tests**
- `backend/services/tests/test_market_theatre_bridge.py`
- Test cases: market creation from Theatre config, phase transition propagation, state serialisation roundtrip, parameter mutation rejection after commit

**10. Stub agent tests**
- `backend/services/tests/test_stub_agents.py`
- Test cases: agent population spawning, per-archetype strategy correctness, trade execution via stubs, balance tracking, P&L accumulation

### Sprint 1 Success Criteria

- [ ] `POST /api/v1/sponsored-theatres` creates a Theatre with LMSR market in CREATED state
- [ ] `GET /api/v1/sponsored-theatres/{id}/review` returns a complete SponsorReviewPackage
- [ ] `POST /api/v1/sponsored-theatres/{id}/commit` freezes parameters and transitions to COMMITTED
- [ ] Commitment hash verified after freeze
- [ ] Source manifest built and validated against registry
- [ ] 6 stub agents spawned and execute trades against LMSR
- [ ] All new tests pass
- [ ] Existing test suite regression: `backend/market/`, `backend/engines/`, `backend/scoring/`, `backend/osint/` — zero new failures

---

## Sprint 2 — Resolution + Settlement + Certificate Delivery

### What It Is

The complete back half of the lifecycle: OSINT evidence flows into the Theatre, the Composed Oracle evaluates against committed criteria, the market resolves, agents settle, and the sponsor receives a certificate with full evidence chain.

### Sprint 2 Tasks

**1. Theatre evidence collector**
`backend/services/theatre_evidence.py` — orchestrates OSINT evidence collection for a Theatre:
- Input: Theatre ID (reads committed_sources from Theatre config)
- Calls LiveOSINTRealityProvider (from 011) with the Theatre's source list
- Collects evidence bundles per source with HTTP transcript receipts
- Stores evidence in Theatre's evidence store (JSON, keyed by collection timestamp)
- Runs on heartbeat cadence during TRADING phase

**2. Theatre resolution engine**
`backend/services/theatre_resolution.py` — triggers resolution when the resolution_date arrives:
- Collects final evidence snapshot
- Invokes Composed Oracle evaluation:
  - Corroboration check (provisional in 012 — WM-only, 0.7 penalty)
  - Counter-signal evaluation (scaffolding — all UNAVAILABLE, INTELLIGENCE_GAP)
  - Composite score computation
- Determines winning outcome based on oracle evaluation. Oracle evaluation must return a discrete `winning_outcome_index` for n-outcome markets (not binary YES/NO) — the Companies House Theatre has 3 outcomes.
- Transitions market to RESOLVING → calls `ResolutionEngine.settle()` → transitions to SETTLED
- Returns TheatreResolutionResult with oracle_output_id, composite_score, winning_outcome, evidence_bundle_hash

**3. Certificate generation pipeline**
`backend/services/certificate_pipeline.py` — produces the calibration certificate:
- Input: TheatreResolutionResult + SettlementReport
- Builds certificate conforming to v1.0.0 schema:
  - `oracle_output_id` (replaces 010b's certificate_id)
  - `composite_score`
  - `evidence_bundle_hash` (manifest pattern: `{bundle_id: content_hash}` → canonical JSON → SHA-256)
  - `criteria_breakdown` (per-criterion pass/fail with evidence references)
  - `osint_source_manifest` (from source manifest builder)
  - `corroboration_status` (provisional: minimum_met = false, penalty_factor = 0.7)
  - `counter_signal_results` (all UNAVAILABLE, classified as INTELLIGENCE_GAP)
  - `verification_tier` (UNVERIFIED for first local-mode Theatre — BACKTESTED requires 50+ replay runs against historical data, which 012 does not produce)
  - `scored_at`, `provider_version`
- Runs certificate through `echelon_verify` — must pass all 21 checks
- Stores certificate in Theatre database record

**4. RLMF export generator**
`backend/services/rlmf_export.py` — produces RLMF training data from the Theatre:
- Conforms to RLMF schema v2.0.1
- Captures: probability distributions at each market epoch, agent decision traces (stub strategies + outcomes), calibration metrics (Brier score, ECE)
- Per-agent P&L breakdown
- Exportable as JSON
- Linked to Theatre via oracle_output_id

**5. Sponsor delivery package**
`backend/services/sponsor_delivery.py` — assembles the final delivery for the sponsor:
- Calibration certificate (JSON, verifiable)
- Evidence bundle (complete artefact: committed template, ground truth, HTTP receipts, per-episode scores, gap reports)
- RLMF export (JSON)
- Commitment hash (for future on-chain anchoring)
- Returns a SponsorDeliveryPackage with download links and `echelon_status` endpoint URL

**6. echelon_status integration**
Wire the Theatre's live state into the `echelon_status` MCP tool:
- During TRADING: returns current prices, evidence coverage %, sources online/offline
- After SETTLEMENT: returns certificate state (VALID), deployability signal, composite score, counter-signal status
- Cacheable with TTL (300s)
- Matches the response schema from Sponsored Theatre Programme v1 §8

**7. End-to-end integration test**
`backend/services/tests/test_sponsored_theatre_e2e.py` — the marquee test:
- Creates a Companies House Theatre ("Will Acme Ltd file annual accounts by 30 Sep 2026?")
- Commits parameters, verifies commitment hash
- Spawns 6 stub agents, runs 10 trading ticks
- Injects mock evidence bundles (WM fixtures from 011)
- Triggers resolution at simulated resolution_date
- Settles market, verifies bounded-loss invariant: market maker P&L ≥ −b·ln(n); equivalently total_payout ≤ total_trade_cashflow + b·ln(n)
- Generates certificate, runs through `echelon_verify` — all 21 checks pass
- Generates RLMF export, validates schema conformance
- Assembles delivery package, verifies completeness
- Queries `echelon_status` — returns VALID certificate state

**8. Resolution engine tests**
- `backend/services/tests/test_theatre_resolution.py`
- Test cases: resolution with clear winning outcome, resolution with narrow margin, resolution with evidence gaps, oracle evaluation with provisional corroboration, composite score calculation

**9. Certificate pipeline tests**
- `backend/services/tests/test_certificate_pipeline.py`
- Test cases: certificate schema conformance, evidence_bundle_hash correctness (manifest pattern), verifier check pass, oracle_output_id format, counter-signal reporting

**10. RLMF export tests**
- `backend/services/tests/test_rlmf_export.py`
- Test cases: schema v2.0.1 conformance, probability distribution capture at each epoch, agent trace completeness, Brier score calculation, per-agent P&L accuracy

### Sprint 2 Success Criteria

- [ ] Evidence collector runs against mock WM fixtures during TRADING phase
- [ ] Resolution engine evaluates Composed Oracle and determines winning outcome
- [ ] Settlement satisfies bounded-loss invariant: market maker P&L ≥ −b·ln(n); equivalently total_payout ≤ total_trade_cashflow + b·ln(n), and each agent's payout equals winning shares held
- [ ] Certificate passes all 21 `echelon_verify` checks
- [ ] RLMF export conforms to schema v2.0.1
- [ ] Sponsor delivery package contains all 4 deliverables
- [ ] `echelon_status` returns live state during trading and VALID certificate post-settlement
- [ ] End-to-end test passes — full lifecycle from creation to delivery
- [ ] All new tests pass
- [ ] Existing test suite regression: zero new failures in scoped modules

---

## File Structure (New Files)

```
backend/
├── services/
│   ├── sponsored_theatre.py          # Theatre creation from sponsor config
│   ├── market_theatre_bridge.py      # LMSR ↔ Theatre integration
│   ├── stub_agents.py                # Stub agent spawner + simple strategies
│   ├── theatre_evidence.py           # OSINT evidence collection for Theatre
│   ├── theatre_resolution.py         # Resolution + Composed Oracle evaluation
│   ├── certificate_pipeline.py       # Certificate generation from settlement
│   ├── rlmf_export.py                # RLMF training data export
│   ├── sponsor_delivery.py           # Sponsor delivery package assembly
│   └── tests/
│       ├── test_sponsored_theatre.py
│       ├── test_market_theatre_bridge.py
│       ├── test_stub_agents.py
│       ├── test_theatre_resolution.py
│       ├── test_certificate_pipeline.py
│       ├── test_rlmf_export.py
│       └── test_sponsored_theatre_e2e.py
├── schemas/
│   └── sponsored_theatre.py          # SponsoredTheatreConfig, SponsorReviewPackage, etc.
├── api/
│   └── sponsored_theatre_routes.py   # Sponsor-facing API endpoints
└── osint/
    └── source_manifest.py            # Source manifest builder for Theatre
```

---

## Dependencies and Constraints

### Hard Dependencies
- **LMSR engine** (010a) — `backend/market/` must be complete and tested
- **Engines + heartbeat** (010b) — Paradox Engine reads LMSR prices, Butterfly Engine modifies market state
- **echelon_status** (009) — MCP tool returns live Theatre state
- **WorldMonitor pipeline** (011) — evidence collection uses LiveOSINTRealityProvider

### Constraints
- **Mock-only OSINT testing** — WM not deployed locally. All evidence collection uses JSON fixtures from 011's test suite. `@pytest.mark.live_wm` for future integration tests.
- **Stub agents only** — no autonomous decision-making. Agent runtime (T0/T1/T2/T3) is Cycle-013. Stubs are throwaway code that proves the infrastructure works.
- **No on-chain anchoring** — commitment hash and certificate hash are computed and stored, but Base deployment is deferred. The anchoring interface exists as a stub returning a deterministic "local_mode" transaction hash.
- **Provisional corroboration** — WM-only sources share `independence_upstream_id: worldmonitor`. Corroboration minimum never met (0.7 penalty applies). This is a known limitation documented in the certificate.
- **Single Theatre type** — Cycle-012 targets Companies House Theatres (UK corporate compliance). Other jurisdictions and source configurations are deferred.

### Regression Target
Same scoped regression as 011: `backend/market/`, `backend/engines/`, `backend/scoring/`, `backend/osint/`. Pre-existing `theatre/` collection errors excluded from baseline.

---

## BEAUVOIR Principle: Agent-First Citizenship

The BEAUVOIR review guidelines (from the 0xHoneyJar engineering team) establish a pattern for agent-first development that applies to 012's stub agents and propagates to 013's full runtime:

1. **Document the reasoning, not just the conclusion.** Every stub agent strategy includes a comment explaining why that archetype trades that way. Future agents (013) inherit these rationales.
2. **Map decision trajectories.** Stub agent trades are logged with: trigger condition, market state at decision time, confidence level, outcome. This produces the training data that RLMF schema captures.
3. **Name the pattern.** Trade strategies reference named patterns from the archetype matrix (momentum exploitation, intel arbitrage, stability maintenance, chaos creation, market moving, volatility harvesting).

These are not just code review practices — they're design constraints for how agent behaviour is structured and recorded throughout the system.

---

## What 012 Unlocks

- **First complete market lifecycle** — creation through certificate delivery with verifiable evidence
- **Proof that LMSR + OSINT + settlement work together** — the integration test is the acceptance gate
- **Sponsor onboarding pattern** — reusable for any future Theatre commissioning
- **RLMF generation proof** — the first real training data export from a live market
- **Certificate delivery pipeline** — automated from settlement to verifiable deliverable
- **Foundation for 013 (Agent Runtime)** — the stub agents in 012 define the interface that autonomous agents in 013 must satisfy

---

## Acceptance Gate

Cycle-012 is complete when:
1. The end-to-end integration test passes — full Companies House Theatre lifecycle from sponsor creation to certificate delivery
2. Certificate passes all 21 `echelon_verify` checks
3. RLMF export validates against schema v2.0.1
4. `echelon_status` returns correct state at each lifecycle phase
5. All new tests pass with zero regression in scoped modules
6. Stub agents produce non-trivial trading activity (>20 trades across 6 agents in the E2E test)

---

## AGPL Compliance

All new files are authored by the Echelon team. No third-party code is introduced in 012. Dependencies remain: FastAPI, SQLAlchemy, Pydantic v2, httpx (for mock OSINT). All AGPL-compatible.
