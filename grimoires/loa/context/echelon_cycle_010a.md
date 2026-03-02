# Cycle-010a — LMSR Market Engine (Local Mode)

**Cycle:** cycle-010a
**Name:** LMSR Cost Function + Market State + Agent Positions
**Predecessor:** cycle-008/009 MCP surface (echelon_verify available, echelon_hash available)
**Location:** `~/Developer/prediction-market-monorepo.nosync`
**Sprint count:** 2
**Tooling:** Claude Code + Loa (`/plan` → `/simstim` → `/run-bridge`)

---

## Cycle Objective

Implement the LMSR market engine as a local-mode runtime — the cost function, market lifecycle state machine, trade execution, agent position tracking, and deterministic resolution/settlement. This is the mathematical core that every downstream component depends on: the Butterfly Engine modifies market state, the Paradox Engine reads prices, agents execute trades, and on-chain settlement commits outcomes.

Cycle-010a deliberately excludes: Butterfly/Paradox/Entropy engines (010b), Base Sepolia deployment (010b), the heartbeat scheduler (010b), and VRF entropy injection (010b). The engine operates in local mode — direct function calls, no network, no concurrency. This isolation means the LMSR arithmetic can be proven correct before distributed systems complexity is layered on.

The four existing LMSR quant templates (hygiene, perturbation harness, API fidelity, b-sensitivity) become **live acceptance tests** — run against the real engine, not fixtures. If the engine passes all four templates via `echelon_verify`, the cost function is certified.

---

## What Exists (Relevant to This Cycle)

**LMSR Specification (System Bible v13, Section III):**
- Cost function: `C(x) = b * ln(∑ exp(xⱼ / b))`
- Price function: `p_i(x) = exp(x_i / b) / ∑ exp(xⱼ / b)`
- Trade cost: `cost(Δ | x) = C(x + Δ) - C(x)`
- Five key properties: always-on prices, no counterparty, prices on simplex, bounded loss (`b * ln(n)`), belief-driven profits
- Liquidity parameter `b` as committed capital

**Commitment Protocol (System Bible v13, Section VI):**
- All market parameters committed at creation as an immutable hash
- Commitment hash computed over canonicalised template JSON (Echelon Canonical JSON v0)
- Parameters committed: LMSR `b`, fee schedule, outcomes, oracle config, resolution mechanism, version pins, dataset hashes

**Market Lifecycle (System Bible v13, Section VI):**
- CREATED → COMMITTED → TRADING → RESOLVING → SETTLED
- No parameter changes after COMMITTED phase
- Resolution triggers settlement — deterministic, no discretion

**Agent Architecture (System Bible v13, Section VIII):**
- Six archetypes: Shark, Spy, Diplomat, Saboteur, Whale, Degen
- Identity (persistent, NFT) vs Instance (ephemeral, per-market worker)
- Behavioural parameters: risk appetite (ρ), evidence sensitivity (ε), position limit (L), etc.
- P&L aggregates back to identity

**Existing Repo Infrastructure:**
- `backend/agents/` — 11 modules, 496KB: autonomous_agent, multi_brain, shark_strategies, genealogy_manager
- `backend/schemas/` — butterfly_schemas.py, paradox_schemas.py
- `backend/simulation/` — engine.py (existing scaffold)
- `backend/scoring/` — waterfall, escrow, reconciliation, deterministic_oracle scorers
- `fixtures/echelon_quant_v0_2/` — 4 LMSR template suites with fixtures

**Four LMSR Quant Templates (Theatre Template Library Live v2):**

| Template | Criteria | Fixtures | Composite | What it tests |
|----------|----------|----------|-----------|--------------|
| quant_market_hygiene_v1 | 19 | 10 (3p/7f) | 0.9460 | Commitment immutability, cost-function accounting, calibration signals, robustness |
| quant_market_perturbation_harness_v1 | 7 | 10 (9p/1f) | 0.9800 | VRF perturbation, saboteur pressure, paradox recovery |
| quant_market_api_fidelity_v1 | 5 | 10 (7p/3f) | 0.9050 | Versioned API, complete state feed, pre-trade quoting, heartbeat |
| lmsr_b_sensitivity_suite_v1 | 5 | 5 (5p/0f) | 1.0000 | Parametric sweep: identical trade across b = [10, 20, 40, 80, 160] |

These templates were validated with fixture data in earlier cycles. In 010a, they validate the **live engine** — the engine must produce outputs that pass the same 21 verifier checks per template.

**LOCAL MODE template profile (010a):** Several quant template criteria reference VRF perturbation, saboteur pressure, paradox recovery (perturbation harness), and heartbeat liveness (API fidelity). These are out of scope for 010a. To prevent contradictory acceptance gates, templates run in LOCAL MODE where: VRF is replaced by a deterministic fixed seed (`0xECHELON_LOCAL`), heartbeat checks are stubbed as always-alive, and saboteur/paradox criteria use deterministic no-op injectors. The template composite baselines are recalculated against these LOCAL MODE stubs and stored in `fixtures/echelon_quant_v0_2/local_mode_baselines.json` — used only for 010a acceptance. Full VRF/heartbeat/saboteur criteria activate in 010b when those engines exist.

**MCP Surface (Cycle-008/009):**
- `echelon_verify` validates certificates
- `echelon_hash` computes commitment hashes
- The LMSR engine will produce certificates that flow through this existing verification infrastructure
- Note: `echelon_status` market-state integration is deferred to 010b (no MCP coupling in 010a)

---

## Sprint 1 — LMSR Core + Market Lifecycle

### What It Is

The pure mathematical engine and the state machine that governs its lifecycle. No agents, no trading API, no positions — just the cost function, the market state, and the lifecycle transitions.

### LMSR Core Module

**File:** `backend/market/lmsr.py`

The core LMSR implementation. All functions are pure — given the same inputs, they always return the same outputs. No side effects, no state mutation, no I/O.

```python
class LMSREngine:
    """Logarithmic Market Scoring Rule — pure cost-function market maker."""

    @staticmethod
    def cost(x: list[float], b: float) -> float:
        """C(x) = b * ln(∑ exp(xⱼ / b))"""

    @staticmethod
    def prices(x: list[float], b: float) -> list[float]:
        """p_i(x) = exp(x_i / b) / ∑ exp(xⱼ / b)"""

    @staticmethod
    def trade_cost(x: list[float], delta: list[float], b: float) -> float:
        """cost(Δ | x) = C(x + Δ) - C(x)"""

    @staticmethod
    def worst_case_loss(b: float, n_outcomes: int) -> float:
        """Maximum market maker loss = b * ln(n)"""

    @staticmethod
    def validate_prices(prices: list[float], tolerance: float = 1e-9) -> bool:
        """Verify: all prices in [0,1], sum = 1.0 within tolerance."""
```

**Numerical stability:** The `exp(x_i / b)` computation overflows for large `x_i / b`. Use the log-sum-exp trick: subtract `max(x / b)` before exponentiating. This is a known numerical technique — the cost function result is identical but overflow-safe.

**Invariants (tested, not asserted at runtime for performance):**
- `sum(prices(x, b)) == 1.0` (within floating-point tolerance)
- `all(0.0 <= p <= 1.0 for p in prices(x, b))`
- `trade_cost(x, [0]*n, b) == 0.0` (zero-delta trade costs nothing)
- `trade_cost(x, delta, b) == -trade_cost(x + delta, [-d for d in delta], b)` (reversibility, within 1e-9 tolerance in tests due to floating-point)
- `worst_case_loss(b, n) == b * ln(n)`

### Market State

**File:** `backend/market/state.py`

The mutable state container for a single market instance. One per Theatre.

```python
@dataclass
class MarketState:
    market_id: str
    theatre_id: str
    b: float                          # liquidity parameter (immutable after COMMITTED)
    n_outcomes: int                   # number of outcomes (immutable after COMMITTED)
    outcome_labels: list[str]         # human-readable outcome names
    x: list[float]                    # net outstanding shares per outcome
    phase: MarketPhase                # current lifecycle phase
    fee_schedule: FeeSchedule         # committed fee structure
    commitment_hash: str | None       # SHA-256 of committed parameters
    resolved_outcome: int | None      # index of winning outcome (set at resolution)
    created_at: str
    committed_at: str | None
    trading_opened_at: str | None
    resolved_at: str | None
    settled_at: str | None
```

**MarketPhase enum:** `CREATED`, `COMMITTED`, `TRADING`, `RESOLVING`, `SETTLED`

### Market Lifecycle State Machine

**File:** `backend/market/lifecycle.py`

Transition rules — each transition is a function that validates preconditions and returns a new MarketState:

| From | To | Trigger | Preconditions |
|------|----|---------|---------------|
| CREATED | COMMITTED | `commit(params)` | All parameters provided; `b > 0`; `n_outcomes >= 2`; commitment hash computed |
| COMMITTED | TRADING | `open_trading()` | Commitment hash exists; no parameter changes permitted after this point |
| TRADING | RESOLVING | `begin_resolution(oracle_result)` | Oracle result provided; trading halted; no new trades accepted |
| RESOLVING | SETTLED | `settle()` | All positions computed; payouts determined; no outstanding disputes (v1: no disputes) |

**Invalid transitions raise `InvalidPhaseTransition`.** No transition is reversible. A market can only move forward.

**Commitment hash computation:** Uses the existing Echelon Canonical JSON v0 (same as certificate commitment hashes from Cycle-008). Hash is computed over: `b`, `n_outcomes`, `outcome_labels`, `fee_schedule`, `oracle_config`, `version_pins`. **Ordering is significant:** `outcome_labels` must be committed in their declared order (no sorting) — the hash is order-dependent.

**010a oracle_config stub:** Since 010a resolves deterministically via a provided `winning_outcome` (no oracle), `oracle_config` is set to the constant stub `{"type": "manual", "version": "v0"}` for all 010a markets. This keeps the commitment hash fully specified without pulling in oracle infrastructure. Real oracle configs activate in 010b+.

### Fee Schedule

**File:** `backend/market/fees.py`

```python
@dataclass
class FeeSchedule:
    trade_fee_bps: int = 0       # basis points on trade cost (0 for v1)
    resolution_fee_bps: int = 0  # basis points on settlement payouts (0 for v1)
```

Fees are committed at market creation and cannot change. For 010a, fees default to zero. The schema reserves the fields for 010b+ when real fee collection matters.

### Sprint 1 Architecture

```
backend/market/
├── __init__.py
├── lmsr.py               # Pure LMSR cost function (NEW)
├── state.py               # MarketState dataclass (NEW)
├── lifecycle.py           # State machine transitions (NEW)
├── fees.py                # FeeSchedule (NEW)
├── commitment.py          # Commitment hash computation (NEW)
└── exceptions.py          # Market-specific exceptions (NEW)

backend/market/tests/
├── test_lmsr.py           # LMSR invariant tests (NEW)
├── test_lifecycle.py      # State machine transition tests (NEW)
├── test_commitment.py     # Commitment hash tests (NEW)
└── test_numerical.py      # Overflow/precision edge cases (NEW)
```

### Sprint 1 Tasks

1. **LMSR core** — `LMSREngine` with `cost()`, `prices()`, `trade_cost()`, `worst_case_loss()`, `validate_prices()`. Log-sum-exp trick for numerical stability.
2. **Market state** — `MarketState` dataclass, `MarketPhase` enum, `FeeSchedule` dataclass.
3. **Lifecycle state machine** — Transition functions with precondition validation. Invalid transitions raise exceptions.
4. **Commitment hash** — Canonical JSON serialisation of market parameters → SHA-256. Reuse existing canonical hash utility from Cycle-008.
5. **LMSR invariant tests** — Simplex property, zero-delta, reversibility, worst-case loss formula, numerical stability at extreme values.
6. **Lifecycle tests** — Valid transitions, invalid transition rejection, parameter immutability after COMMITTED, commitment hash presence after commit.
7. **Numerical edge-case tests** — Overflow protection (large x/b ratios), precision at extreme b values (b=1, b=100000), many-outcome markets (n=100).
8. **b-sensitivity validation** — Replay the b-sensitivity fixture sweep (b = [10, 20, 40, 80, 160]) against the live engine. Verify price impact decreases as b increases.

### Sprint 1 Success Criteria

- [ ] `LMSREngine.cost()` produces correct values for known test vectors
- [ ] `LMSREngine.prices()` always sums to 1.0 (within 1e-9 tolerance)
- [ ] `LMSREngine.trade_cost()` matches `C(x+Δ) - C(x)` exactly
- [ ] Zero-delta trade costs exactly 0.0
- [ ] Worst-case loss = `b * ln(n)` for all tested (b, n) combinations
- [ ] Log-sum-exp trick prevents overflow for `x_i / b > 700`
- [ ] Market lifecycle transitions enforce correct ordering
- [ ] No parameter mutation permitted after COMMITTED phase
- [ ] Commitment hash is deterministic (same params → same hash)
- [ ] Commitment hash uses Echelon Canonical JSON v0
- [ ] b-sensitivity sweep matches expected price impact curves
- [ ] All existing pipeline tests pass (447+)
- [ ] All Cycle-009 MCP tests pass
- [ ] 20+ new Sprint 1 tests pass

---

## Sprint 2 — Trade Execution + Agent Positions + Resolution

### What It Is

The transactional layer that sits on top of the LMSR core. Agents submit trades, the engine validates and executes them, positions are tracked, and when the market resolves, payouts are computed deterministically.

### Trade Execution

**File:** `backend/market/trading.py`

```python
@dataclass
class Trade:
    trade_id: str
    market_id: str
    agent_id: str
    outcome_index: int          # which outcome to buy/sell
    shares: float               # positive = buy, negative = sell
    cost: float                 # computed by engine (not provided by agent)
    pre_trade_prices: list[float]
    post_trade_prices: list[float]
    timestamp: str

class TradingEngine:
    """Executes trades against LMSR markets. Not pure — mutates MarketState."""

    def execute_trade(
        self,
        market: MarketState,
        agent_id: str,
        outcome_index: int,
        shares: float
    ) -> Trade:
        """
        Validate → compute cost → update x vector → update positions → return Trade.
        Raises TradingHalted if market is not in TRADING phase.
        Raises InsufficientBalance if agent cannot cover trade cost.
        Raises PositionLimitExceeded if trade would breach agent's position limit.
        """

    def quote(
        self,
        market: MarketState,
        outcome_index: int,
        shares: float
    ) -> float:
        """Pre-trade cost quote. Pure function — does not execute."""
```

**Trade semantics (010a):** Trades are one-hot deltas — each trade targets a single outcome. The delta vector is zero everywhere except `delta[outcome_index] = shares`. Cross-outcome bundle trades are deferred to 010b+.

**Trade validation rules:**
- Market must be in TRADING phase
- `outcome_index` must be valid (0 to n_outcomes-1)
- `shares` must be non-zero
- **Sell inventory constraint:** if `shares < 0` (sell), the agent must hold at least `abs(shares)` in `position.shares[outcome_index]`. No naked shorts.
- Agent must have sufficient balance to cover `trade_cost()` (applies to buys; sells return cash)
- Trade must not breach agent's position limit (per-archetype, from agent config)
- After trade, all prices must remain on the simplex (guaranteed by LMSR, but assert)

**Trade execution is atomic.** If any validation fails, no state is mutated. The x vector is only updated after all checks pass.

### Agent Position Tracking

**File:** `backend/market/positions.py`

```python
@dataclass
class AgentPosition:
    agent_id: str
    market_id: str
    shares: list[float]         # net shares held per outcome
    net_cashflow: float         # sum of signed trade costs (positive = cash out, negative = cash in from sells)
    realised_pnl: float         # P&L from closed positions
    trade_count: int

class PositionManager:
    """Tracks agent positions across markets."""

    def get_position(self, agent_id: str, market_id: str) -> AgentPosition
    def update_position(self, agent_id: str, market_id: str, trade: Trade) -> AgentPosition
    def compute_unrealised_pnl(self, position: AgentPosition, current_prices: list[float]) -> float
    def compute_settlement_payout(self, position: AgentPosition, resolved_outcome: int) -> float
```

**Position invariants:**
- `sum(position.shares)` can be any value (unlike prices, positions are unconstrained)
- `net_cashflow` = sum of all signed `trade.cost` values for this agent in this market (buys are positive outflow, sells are negative i.e. cash received)
- Settlement payout for outcome `k` = `position.shares[k] * 1.0` — each winning share pays exactly 1.0 unit at settlement; losing shares pay 0.0; no partial outcomes; no fees in 010a
- `realised_pnl` at settlement = `settlement_payout - net_cashflow`

### Resolution and Settlement

**File:** `backend/market/resolution.py`

```python
class ResolutionEngine:
    """Deterministic market resolution and settlement."""

    def resolve(self, market: MarketState, winning_outcome: int) -> MarketState:
        """
        Transition market to RESOLVING. Record winning outcome.
        No new trades permitted.
        """

    def settle(self, market: MarketState, position_manager: PositionManager) -> SettlementReport:
        """
        Compute all payouts deterministically. Transition to SETTLED.
        Returns SettlementReport with per-agent payouts.
        """

@dataclass
class SettlementReport:
    market_id: str
    winning_outcome: int
    winning_label: str
    total_payout: float
    market_maker_pnl: float     # = total_cost_collected - total_payout
    agent_settlements: list[AgentSettlement]
    commitment_hash: str
    settlement_hash: str        # hash of this report for audit

@dataclass
class AgentSettlement:
    agent_id: str
    shares_held: list[float]
    winning_shares: float
    payout: float
    net_cashflow: float
    realised_pnl: float
```

**Settlement invariants:**
- `total_payout = sum(agent.payout for agent in agent_settlements)`
- `market_maker_pnl = sum(agent.net_cashflow for agent in agent_settlements) - total_payout`
- `market_maker_pnl >= -worst_case_loss(b, n)` (bounded loss guarantee)
- `all(agent.realised_pnl == agent.payout - agent.net_cashflow for agent in agent_settlements)`
- Settlement report hash is deterministic (same inputs → same hash)

### Quant Template Live Validation

**File:** `backend/market/tests/test_quant_acceptance.py`

The four existing LMSR quant templates become acceptance tests for the live engine. For each template:

1. Read the template JSON and fixtures from `fixtures/echelon_quant_v0_2/`
2. Instantiate a `MarketState` with the fixture's declared parameters
3. Execute the declared trades/operations against the live engine
4. Score the results using the existing deterministic scorers
5. Verify the certificate via `echelon_verify`
6. Assert the composite score matches or improves the fixture baseline

**This is the killer acceptance gate.** If the engine passes all four templates with their committed fixtures, the LMSR implementation is certified by the same verification infrastructure that certifies everything else.

### Sprint 2 Architecture (additions to Sprint 1)

```
backend/market/
├── trading.py             # Trade execution engine (NEW)
├── positions.py           # Agent position tracking (NEW)
├── resolution.py          # Resolution + settlement (NEW)
└── tests/
    ├── test_trading.py            # Trade execution tests (NEW)
    ├── test_positions.py          # Position tracking tests (NEW)
    ├── test_resolution.py         # Resolution/settlement tests (NEW)
    ├── test_settlement_invariants.py  # Bounded loss, payout conservation (NEW)
    └── test_quant_acceptance.py   # Live engine vs 4 quant templates (NEW)
```

### Sprint 2 Tasks

1. **Trade execution engine** — Validate, compute cost, update x vector, update positions. Atomic execution.
2. **Quote function** — Pre-trade cost computation without execution.
3. **Agent position manager** — Track shares, cost basis, realised P&L per agent per market. In-memory for v1 (no database).
4. **Resolution engine** — Accept oracle result, transition to RESOLVING, halt trading.
5. **Settlement engine** — Compute payouts, generate SettlementReport with deterministic hash, transition to SETTLED.
6. **Settlement invariant tests** — Bounded loss guarantee, payout conservation, P&L correctness.
7. **End-to-end test** — Create market → commit → open trading → execute trades from multiple agents → resolve → settle → verify P&L.
8. **Quant template acceptance tests** — Run all four LMSR templates against the live engine. Generate certificates. Verify via `echelon_verify`.
9. **Tests** — 25+ new Sprint 2 tests covering: trade validation, position tracking, resolution, settlement, invariants, quant template acceptance.

### Sprint 2 Success Criteria

- [ ] Trades execute correctly: cost matches `C(x+Δ) - C(x)`, x vector updates, prices update
- [ ] Quote returns exact trade cost without executing
- [ ] Trading rejected when market is not in TRADING phase
- [ ] Position tracking correctly accumulates shares and cost basis per agent
- [ ] Resolution halts trading and records winning outcome
- [ ] Settlement computes correct payouts: winning shares pay 1:1
- [ ] Market maker P&L never exceeds `-b * ln(n)` (bounded loss)
- [ ] Settlement is self-financing: total_payout is bounded by net_cashflow + bounded market maker loss
- [ ] SettlementReport hash is deterministic
- [ ] End-to-end lifecycle works: create → commit → trade → resolve → settle
- [ ] `quant_market_hygiene_v1` passes against live engine
- [ ] `quant_market_perturbation_harness_v1` passes against live engine
- [ ] `quant_market_api_fidelity_v1` passes against live engine
- [ ] `lmsr_b_sensitivity_suite_v1` passes against live engine
- [ ] All existing tests pass (447+ pipeline + Cycle-009 MCP tests)
- [ ] 25+ new Sprint 2 tests pass

---

## Scope Exclusions

- **No Butterfly Engine.** Wing flap recording, stability impact, founder's yield — all deferred to 010b.
- **No Paradox Engine.** Logic gap scanning, paradox spawning, extraction — all deferred to 010b.
- **No Entropy Engine.** Temporal decay, heartbeat scheduler — deferred to 010b.
- **No heartbeat scheduler.** No concurrent game loop. All operations are synchronous function calls.
- **No VRF.** No verifiable randomness injection. Deterministic execution only.
- **No Base Sepolia.** No on-chain commitment or settlement. Local mode only. Chain deployment is 010b.
- **No agent brain execution.** Agents are identity stubs that submit trades via direct function calls. No LLM routing, no brain tiers, no autonomous decision-making.
- **No real-time price feeds.** No Polymarket/Kalshi sync. Markets are self-contained.
- **No database persistence.** All state is in-memory for 010a. SQLite/PostgreSQL persistence deferred.
- **No WebSocket/SSE price streaming.** No live price updates to clients.
- **No fee collection.** Fee fields exist in schema (reserved) but fees are zero.

---

## Dependency Chain

```
Cycle-004 (hardening)
  → Cycle-005 (registry v0.6.0)
    → Cycle-006 (live OSINT)
      → Cycle-007 (unified Two-Rail, 447+ tests)
        → Cycle-008 (MCP v0.8.0, construct calibration)
          → Cycle-009 (MCP surface, HTTP transport, certificate store)
            → Cycle-010a (LMSR cost function, market lifecycle, trade execution, positions, settlement)
              → Cycle-010b (Butterfly, Paradox, Entropy engines, heartbeat, Base Sepolia)
```

## After Cycle-010a

The LMSR engine is proven correct in local mode. The four quant templates validate it. Agents can create markets, commit parameters, trade, and settle — all deterministically, all certifiable.

**Cycle-010b — Engines + Base Sepolia:** Wire Butterfly (wing flaps, stability impact), Paradox (logic gap scanning, spawn/extraction), Entropy (temporal decay). Heartbeat scheduler (AGENT 5s → MARKET 10s → PARADOX 30s → ENTROPY 60s). Base Sepolia deployment for commitment hashes and settlement proofs. VRF integration.

**Cycle-011 — WorldMonitor Integration:** Real-time OSINT dashboard endpoints feeding the Composed Oracle.

**Cycle-012 — Sponsored Theatre End-to-End:** First externally-commissioned Theatre.

**Cycle-013 — Results Surface:** Full platform UI.

---

## Updated Cycle Roadmap

| Cycle | Name | Sprints | Key Output |
|-------|------|---------|------------|
| 010a | LMSR Engine (Local) | 2 | Cost function, market lifecycle, trade execution, positions, settlement, quant template certification |
| 010b | Engines + Base Sepolia | 2-3 | Butterfly, Paradox, Entropy engines, heartbeat scheduler, Base Sepolia deployment, VRF |
| 011 | WorldMonitor Integration | 1-2 | CII endpoint, maritime anomaly, convergence signals feeding Composed Oracle |
| 012 | Sponsored Theatre E2E | 2 | First commissioned Theatre, sponsor onboarding, settlement |
| 013 | Results Surface | 2-3 | Full platform UI — whole Echelon cycle in one view |

---

## Workflow

```bash
cd ~/Developer/prediction-market-monorepo.nosync
claude

# Copy this file into Loa context
cp ~/path/to/this/file grimoires/loa/context/echelon_cycle_010a.md

# Sprint 1: LMSR core + market lifecycle
/plan          # Reads context, scopes Sprint 1 tasks
/simstim       # Implements LMSR engine, state machine, commitment hash
/run-bridge    # Fix any issues

# Verify Sprint 1: LMSR invariants
python3 -m pytest backend/market/tests/test_lmsr.py -v
python3 -m pytest backend/market/tests/test_lifecycle.py -v
python3 -m pytest backend/market/tests/test_numerical.py -v

# Sprint 2: trading + positions + settlement
/plan          # Scopes Sprint 2 tasks
/simstim       # Implements trading engine, positions, resolution
/run-bridge    # Fix any issues

# Verify Sprint 2: quant template acceptance
python3 -m pytest backend/market/tests/test_quant_acceptance.py -v

# Verify Sprint 2: end-to-end lifecycle
python3 -m pytest backend/market/tests/ -v

# Full test suite (everything)
python3 -m pytest -q

# Review + audit + archive
```

---

## Key Spec References

| Document | Relevance |
|----------|-----------|
| Echelon System Bible v13 — Section III (LMSR) | Normative spec: cost function, price function, trade cost, properties, b parameter |
| Echelon System Bible v13 — Section VI (Commitment) | Market parameter commitment protocol, hash computation, lifecycle phases |
| Echelon System Bible v13 — Section VIII (Agents) | Agent archetypes, identity/instance model, behavioural parameters |
| Echelon Theatre Template Library Live v2 | Four LMSR quant templates: hygiene, perturbation, API fidelity, b-sensitivity |
| Echelon Quant Modelling Layers Design Note v1 | Seven modelling layers (schema reservation, not implemented this cycle) |
| Echelon Paradox Policy Design Note v1.1 | p_reality derivation from composite_score (referenced, not implemented this cycle) |
| REPO_MAP.md | Existing agent, simulation, and scoring directory structure |
| Echelon Build Roadmap v1 | Phase 3 market layer context |
