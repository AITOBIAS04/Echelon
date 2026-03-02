# Cycle-010b — Engines + Heartbeat + VRF + Base Sepolia

**Cycle:** cycle-010b
**Name:** Butterfly, Paradox, Entropy Engines + Heartbeat Scheduler + VRF Integration + Base Sepolia
**Predecessor:** cycle-010a (LMSR Market Engine — local mode, proven correct, 45+ tests)
**Location:** `~/Developer/prediction-market-monorepo.nosync`
**Sprint count:** 3
**Tooling:** Claude Code + Loa (`/plan` → `/simstim` → `/run-bridge`)

---

## Cycle Objective

Layer distributed systems complexity on top of the proven LMSR engine. Cycle-010a delivered the pure mathematical core — cost function, market lifecycle, trade execution, positions, settlement — all deterministic, all tested. Cycle-010b wires three engines (Butterfly, Entropy, Paradox) into that core, adds a heartbeat scheduler to drive them, injects verifiable randomness via VRF, and deploys commitment hashes and settlement proofs to Base Sepolia.

After 010b, Echelon has a live game loop: agents trade against LMSR markets, the Butterfly Engine records causal state transitions, Entropy decays stability over time, the Paradox Engine detects integrity breaches, VRF ensures execution fairness, and on-chain proofs make the whole thing auditable.

**Key constraint:** 010a's LMSR engine is consumed as-is. No modifications to `backend/market/` modules unless a bug is found. The engines read market state and prices; they do not modify the cost function or trade mechanics.

---

## What 010a Delivers (Consumed by This Cycle)

- `LMSREngine.prices(x, b)` → probability simplex (p_market for Logic Gap calculation)
- `MarketState` with phase transitions (CREATED → COMMITTED → TRADING → RESOLVING → SETTLED)
- `TradingEngine.execute_trade()` → atomic trade execution, returns Trade with pre/post prices
- `PositionManager` → per-agent position tracking with net_cashflow
- `ResolutionEngine` + `SettlementReport` → deterministic settlement with bounded loss guarantee
- Commitment hash via Echelon Canonical JSON v0 with oracle_config stub `{"type": "manual", "version": "v0"}`
- Four quant templates passing under LOCAL_MODE profile
- All existing tests passing (447+ pipeline + Cycle-009 MCP + 45+ market tests)

---

## What Exists (Relevant to This Cycle)

**System Bible v13 — Section V (Integrity Mechanisms):**
- Butterfly Engine: six Wing Flap types (TRADE, SHIELD, SABOTAGE, RIPPLE, PARADOX, ENTROPY) with committed stability impact ranges
- Entropy Engine: Logic Gap state table (Healthy < 20%, Stressed 20-40%, Danger 40-60%, Critical > 60%), baseline decay -1% per tick
- Paradox Engine: spawn conditions committed at Theatre creation, five severity thresholds by inquiry class
- Heartbeat scheduler: AGENT 5s → MARKET 10s → PARADOX 30s → ENTROPY 60s
- Founder's Yield: `yield = timeline.stability × timeline.volume × 0.005`

**System Bible v13 — Section VII (VRF Integration):**
- Chainlink VRF V2 on Base
- Six application points: commit-reveal execution, circuit breaker thresholds, market data validation, RLMF episode sampling, entropy pricing, oracle redundancy
- Four security properties: unpredictability, unbiasability, verifiability, tamper evidence

**System Bible v13 — Section VI (Commitment Protocol):**
- Full parameter set committed on-chain before trading opens
- SHA-256 over canonicalised template JSON
- Settlement fires automatically from resolution state machine — no admin approval

**Paradox Policy Design Note v1.1:**
- `p_reality` for OSINT source = `composite_score` from Composed Oracle (already produced by Cycle-007/008 pipeline)
- `evidence_completeness` = count(required sources with EvidenceBundle) / count(required sources) — aligns with AC-1 GapKind semantics from Cycle-004
- Default thresholds by inquiry class (counterfactual warn=0.20, investigative warn=0.30, etc.)

**Existing Repo Infrastructure:**
- `backend/market/` — LMSR engine (010a output)
- `backend/simulation/engine.py` — existing simulation scaffold (has heartbeat concept)
- `backend/scoring/` — waterfall, escrow, reconciliation, deterministic_oracle scorers
- `mcp/` — MCP Server (Cycle-008 shipped 5 stateless tools; Cycle-009 adds echelon_status + echelon_calibrate). Exact tool inventory depends on which cycles are merged at 010b start.
- `smart-contracts/` — Solidity contracts, Hardhat config, existing Base deployment scripts
- `fixtures/echelon_quant_v0_2/local_mode_baselines.json` — LOCAL_MODE baselines (to be replaced with FULL baselines)

---

## Sprint 1 — Butterfly Engine + Entropy Engine + Heartbeat Scheduler

### What It Is

The game loop and causal state tracking. The Heartbeat Scheduler drives periodic ticks at four cadences. The Butterfly Engine records every causal state transition (Wing Flap) from trade execution and engine actions. The Entropy Engine applies temporal decay to timeline stability on each ENTROPY tick.

No Paradox Engine yet (Sprint 2). No VRF yet (Sprint 3) — stability impacts use deterministic values within committed ranges for now.

### Heartbeat Scheduler

**File:** `backend/engines/heartbeat.py`

```python
@dataclass
class HeartbeatConfig:
    agent_interval_s: float = 5.0
    market_interval_s: float = 10.0
    paradox_interval_s: float = 30.0
    entropy_interval_s: float = 60.0

class HeartbeatScheduler:
    """Drives the simulation game loop at four cadences."""

    def __init__(self, config: HeartbeatConfig): ...

    async def start(self, theatre_id: str) -> None:
        """Start the heartbeat loop for a Theatre. Non-blocking."""

    async def stop(self, theatre_id: str) -> None:
        """Stop the heartbeat loop. Idempotent."""

    def register_handler(self, cadence: str, handler: Callable) -> None:
        """Register a handler for a heartbeat cadence (agent/market/paradox/entropy)."""

    def tick_count(self, theatre_id: str) -> dict[str, int]:
        """Return tick counts per cadence for monitoring."""
```

**Design:** `asyncio`-based scheduler. Each cadence runs independently. Handlers are registered by the engine wiring layer — the scheduler doesn't know what Butterfly or Entropy are. It just ticks and calls handlers.

**010b constraint:** Local mode only. No distributed scheduling, no Redis, no message queues. `asyncio.create_task` per cadence per Theatre. Concurrency is within a single process.

### Butterfly Engine

**File:** `backend/engines/butterfly.py`

```python
class WingFlapType(str, Enum):
    TRADE = "TRADE"
    SHIELD = "SHIELD"
    SABOTAGE = "SABOTAGE"
    RIPPLE = "RIPPLE"
    PARADOX = "PARADOX"
    ENTROPY = "ENTROPY"

@dataclass
class WingFlap:
    flap_id: str
    theatre_id: str
    flap_type: WingFlapType
    agent_id: str | None           # None for system-generated flaps (ENTROPY, RIPPLE)
    stability_impact: float        # signed: positive = stabilising, negative = destabilising
    pre_stability: float
    post_stability: float
    trigger_detail: dict           # type-specific metadata (trade_id, sabotage_target, etc.)
    timestamp: str

@dataclass
class TimelineState:
    theatre_id: str
    stability: float               # 0.0 to 1.0 — starts at 1.0
    volume: float                  # cumulative trade volume
    flap_count: int
    founders_yield_accrued: float

class ButterflyEngine:
    """Records causal state transitions. Every action that modifies market state
    passes through the Butterfly Engine as a Wing Flap."""

    def record_flap(self, flap_type: WingFlapType, theatre_id: str,
                    agent_id: str | None, impact: float,
                    trigger_detail: dict) -> WingFlap:
        """Record a Wing Flap. Updates TimelineState.stability.
        CLAMP AT WRITE: post_stability = clamp(pre_stability + impact, 0.0, 1.0).
        Clamping happens here, not at read time. Overshoot is absorbed."""

    def get_timeline_state(self, theatre_id: str) -> TimelineState

    def compute_founders_yield(self, theatre_id: str) -> float:
        """yield = timeline.stability × timeline.volume × 0.005"""
```

**Stability impact ranges (committed per Theatre):**

| Flap Type | Impact Range | Determination (010b) |
|-----------|-------------|---------------------|
| TRADE | ±0.001 to ±0.05 | `trade_impact = clamp(k × notional / liquidity_depth, -0.05, 0.05)` where `k` is committed per Theatre (default 0.1). Sign convention committed as `trade_impact_policy: "buy_negative_sell_positive"` (v1 only) — buys destabilise (negative), sells stabilise (positive). |
| SHIELD | +0.02 to +0.10 | Fixed per difficulty tier (committed at Theatre creation). Three tiers: easy +0.02, medium +0.05, hard +0.10. |
| SABOTAGE | -0.05 to -0.15 | Sprint 1–2: deterministic midpoint -0.10. Sprint 3: VRF-randomised within range. |
| RIPPLE | ±0.01 to ±0.03 | Stubbed in 010b (no cross-timeline wiring). Schema exists, no source. |
| PARADOX | -0.10 to -0.30 | Severity-scaled: WARN = -0.10, TRADING_PAUSE = -0.20, FORCED_RESOLUTION = -0.30. |
| ENTROPY | -0.01 baseline | Fixed decay rate per ENTROPY tick. Scaled by Logic Gap multiplier (Sprint 2). |

**Integration with 010a:** The `TradingEngine.execute_trade()` call must produce a TRADE Wing Flap. This is wired at the engine integration layer (Sprint 1 Task 7), not by modifying `trading.py` directly. A thin wrapper or event hook captures each trade and calls `ButterflyEngine.record_flap()`.

### Entropy Engine

**File:** `backend/engines/entropy.py`

```python
@dataclass
class EntropyConfig:
    base_decay_rate: float = 0.01  # -1% per tick
    stressed_multiplier: float = 1.5
    danger_multiplier: float = 2.0
    critical_multiplier: float = 3.0

class EntropyEngine:
    """Temporal decay of timeline stability. Runs on ENTROPY heartbeat tick."""

    def __init__(self, config: EntropyConfig, butterfly: ButterflyEngine): ...

    def tick(self, theatre_id: str, logic_gap_status: str = "healthy") -> WingFlap:
        """
        Apply decay to timeline stability. Returns ENTROPY WingFlap.
        Decay rate scales with Logic Gap status:
        - healthy: base_decay_rate
        - stressed: base × stressed_multiplier
        - danger: base × danger_multiplier
        - critical: base × critical_multiplier
        """

    def get_effective_decay_rate(self, logic_gap_status: str) -> float
```

**Logic Gap status in Sprint 1:** Since the Paradox Engine isn't built until Sprint 2, the Entropy Engine receives `"healthy"` as the default Logic Gap status in Sprint 1. The interface accepts it as a parameter so Sprint 2 can wire real Logic Gap status without changing the Entropy Engine.

### Sprint 1 Architecture

```
backend/engines/
├── __init__.py
├── heartbeat.py              # Heartbeat scheduler (NEW)
├── butterfly.py              # Butterfly Engine — Wing Flap recording (NEW)
├── entropy.py                # Entropy Engine — temporal decay (NEW)
├── config.py                 # Engine configuration dataclasses (NEW)
├── integration.py            # Wiring layer: trade hooks, heartbeat handlers (NEW)
└── tests/
    ├── test_heartbeat.py         # Scheduler timing, start/stop, handler registration (NEW)
    ├── test_butterfly.py         # Wing Flap recording, stability tracking, yield calculation (NEW)
    ├── test_entropy.py           # Decay rates, Logic Gap multipliers, boundary conditions (NEW)
    └── test_integration.py       # Trade → Wing Flap pipeline, heartbeat → entropy tick (NEW)
```

### Sprint 1 Tasks

1. **Heartbeat Scheduler** — asyncio-based, four cadences, handler registration, start/stop per Theatre.
2. **Butterfly Engine** — WingFlap dataclass, TimelineState tracking, stability impact application, Founder's Yield computation.
3. **Entropy Engine** — Temporal decay with Logic Gap-scaled rates, produces ENTROPY Wing Flaps via Butterfly Engine.
4. **Engine configuration** — Committed parameters: stability impact ranges, decay rates, yield multiplier. Immutable after Theatre creation (reuses commitment pattern from 010a).
5. **Heartbeat tests** — Timing accuracy (within tolerance), concurrent Theatre isolation, graceful stop.
6. **Butterfly + Entropy tests** — Stability bounds (never < 0.0), decay rate correctness, yield formula, Wing Flap audit trail.
7. **Integration wiring** — Hook `TradingEngine.execute_trade()` to produce TRADE Wing Flaps. Register Entropy tick on ENTROPY heartbeat cadence. No modification to 010a modules — use event hooks or thin wrappers.
8. **Integration tests** — End-to-end: create market → start heartbeat → execute trades → observe Wing Flaps → observe stability decay → compute yield.

### Sprint 1 Success Criteria

- [ ] Heartbeat Scheduler ticks at correct cadences (within 10% tolerance)
- [ ] Multiple Theatres run concurrent heartbeats without interference
- [ ] Heartbeat start/stop is clean (no leaked tasks)
- [ ] Every trade produces a TRADE Wing Flap with correct stability impact
- [ ] Timeline stability never drops below 0.0 or exceeds 1.0
- [ ] Entropy decay applies correct base rate (1% per 60s tick)
- [ ] Entropy decay scales correctly with Logic Gap status multipliers
- [ ] Founder's Yield formula: `stability × volume × 0.005`
- [ ] Wing Flap audit trail is append-only and queryable by Theatre
- [ ] Engine configuration is immutable after Theatre commitment
- [ ] No modifications to `backend/market/` modules (010a untouched)
- [ ] All existing tests pass (447+ pipeline + MCP + 45+ market)
- [ ] 20+ new Sprint 1 tests pass

---

## Sprint 2 — Paradox Engine + Logic Gap + Circuit Breakers

### What It Is

The self-policing integrity layer. The Paradox Engine scans for divergence between market-implied probability (p_market from LMSR) and reality signals (p_reality from OSINT composite_score or deterministic ground truth). When the Logic Gap exceeds committed thresholds, circuit breakers activate.

### Logic Gap Calculation

**File:** `backend/engines/paradox.py`

```python
@dataclass
class LogicGapReading:
    theatre_id: str
    p_market: float                # from LMSREngine.prices() — smoothed over trailing window
    p_reality: float               # from evidence source (composite_score, deterministic, or survey)
    logic_gap: float               # abs(p_market - p_reality)
    gap_direction: float           # signed: p_market - p_reality (positive = market above reality)
    status: LogicGapStatus         # HEALTHY / STRESSED / DANGER / CRITICAL
    smoothing_window_s: float      # trailing window for p_market smoothing (default 60s)
    timestamp: str

class LogicGapStatus(str, Enum):
    HEALTHY = "healthy"            # < 20%
    STRESSED = "stressed"          # 20-40%
    DANGER = "danger"              # 40-60%
    CRITICAL = "critical"          # > 60%
```

**p_market derivation:** `LMSREngine.prices(market.x, market.b)` returns the current probability simplex. For Logic Gap, use the probability of the outcome under scrutiny, smoothed over a trailing window (default 60 seconds, configurable per Theatre).

**p_reality derivation (by source type):**

| Source | p_reality | Available Now? |
|--------|-----------|---------------|
| `osint` | `composite_score` from Composed Oracle calibration certificate | Yes — produced by Cycle-007/008 pipeline |
| `deterministic` | Scorer output from deterministic computation (0.0 or 1.0) | Yes — from Theatre scoring functions |
| `survey` | Aggregated community attestation score | No — future cycle |
| `simulation` | Digital twin output | No — future cycle |

**010b constraint:** Only `osint` and `deterministic` sources are implemented. `survey` and `simulation` are interface stubs that raise `NotImplementedError`.

**Reality signal interface (prevents bare-float hardcoding):**

```python
@dataclass
class RealitySignal:
    p_reality: float               # 0.0–1.0
    evidence_bundle_hash: str      # SHA-256 of the evidence bundle that produced this signal
    certificate_id: str | None     # calibration certificate ID (osint) or None (deterministic)
    source_type: str               # "osint" | "deterministic" | "survey" | "simulation"

class RealitySignalProvider:
    """Loads p_reality from the appropriate source. Sprint 2 implements osint + deterministic."""

    def get_signal(self, theatre_id: str) -> RealitySignal:
        """Returns the current reality signal for a Theatre.
        osint: reads composite_score from most recent calibration certificate.
        deterministic: reads scorer output (0.0 or 1.0).
        survey/simulation: raises NotImplementedError."""
```

The `RealitySignalProvider` is injected into `ParadoxEngine.__init__()`. The Paradox Engine never reads a bare float — it always receives a `RealitySignal` with provenance for the audit trail.

### Paradox Engine

```python
class ParadoxMode(str, Enum):
    DISABLED = "disabled"          # Paradox Engine does not run. No Logic Gap scanning.
    ENABLED = "enabled"            # Full Paradox lifecycle: scan, threshold evaluation, circuit breakers.
    ADVISORY = "advisory"          # Logic Gap computed and logged. No circuit breaker actions fire.
    CIRCUIT_BREAKER = "circuit_breaker"  # Only critical threshold evaluated. Warn/breach ignored.

@dataclass
class ParadoxConfig:
    """Committed at Theatre creation. Immutable."""
    mode: ParadoxMode              # controls Paradox behaviour for this Theatre
    inquiry_class: str             # counterfactual / investigative / inspection / survey / scrutiny
    warn_threshold: float | None   # None when mode is circuit_breaker (ignored)
    breach_threshold: float | None # None when mode is circuit_breaker (ignored)
    critical_threshold: float
    activation_gate: dict          # e.g. {"min_evidence_completeness": 0.5} or {"min_time_elapsed": 300}
    logic_gap_source: str          # "osint" | "deterministic" | "survey" | "simulation"
    smoothing_window_s: float = 60.0

@dataclass
class ParadoxRuntimeState:
    """Per-theatre mutable runtime state. In-memory only."""
    activation_gate_satisfied: bool = False  # one-way latch — once True, never reverts
    last_reading: LogicGapReading | None = None
    scan_count: int = 0

class ParadoxEngine:
    """Self-policing integrity mechanism. Runs on PARADOX heartbeat tick.
    Maintains a ParadoxRuntimeState per theatre in _runtime: dict[str, ParadoxRuntimeState]."""

    def __init__(self, config: ParadoxConfig, butterfly: ButterflyEngine,
                 lmsr: LMSREngine, market: MarketState,
                 reality_provider: RealitySignalProvider): ...

    def scan(self, theatre_id: str) -> LogicGapReading | None:
        """Compute current Logic Gap. Called on each PARADOX tick.
        Returns None if mode is DISABLED. Respects activation gate latch."""

    def evaluate_thresholds(self, reading: LogicGapReading) -> ParadoxAction | None:
        """Check reading against committed thresholds. Returns action if threshold breached."""

    def check_activation_gate(self, theatre_id: str) -> bool:
        """Check whether activation gate conditions are met (evidence completeness, time elapsed, etc.).
        LATCH SEMANTICS: once satisfied, remains satisfied for the Theatre's lifetime.
        The gate is never re-evaluated to unsatisfied — prevents flicker if sources go temporarily offline."""

    def execute_action(self, action: ParadoxAction, theatre_id: str) -> WingFlap:
        """Execute circuit breaker action. Records PARADOX Wing Flap."""

class ParadoxAction(str, Enum):
    WARN = "warn"                  # Log warning + Wing Flap, no market intervention
    TRADING_PAUSE = "trading_pause"  # Halt trading temporarily (enabled mode, breach threshold)
    FORCED_RESOLUTION = "forced_resolution"  # Force market to RESOLVING phase (critical threshold)
```

**Default policies by inquiry class (from Paradox Policy Design Note v1.1):**

| Inquiry Class | mode | warn | breach | critical | Activation Gate |
|---------------|------|------|--------|----------|-----------------|
| counterfactual | `enabled` | 0.20 | 0.40 | 0.60 | `none` |
| investigative | `enabled` | 0.30 | 0.50 | 0.70 | `min_evidence_completeness: 0.50` |
| inspection | `enabled` | 0.20 | 0.40 | 0.60 | `min_time_elapsed: 300s` |
| survey | `advisory` | 0.30 | 0.50 | 0.70 | `min_observations: 30` |
| scrutiny | `circuit_breaker` | — | — | 0.80 | `none` |

**Mode-dependent behaviour:**
- `enabled`: Full lifecycle — scan, evaluate all three thresholds, fire circuit breaker actions.
- `advisory`: Scan and log Logic Gap readings. Dashboard warnings surface. No circuit breaker actions fire (no TRADING_PAUSE, no FORCED_RESOLUTION). WARN Wing Flaps still recorded for audit trail.
- `circuit_breaker`: Only `critical` threshold evaluated. `warn` and `breach` are ignored and MAY be `None`. Used by Scrutiny — large Logic Gaps are the point; only extreme divergence (>80%) triggers intervention to prevent total market collapse.
- `disabled`: Paradox Engine does not scan. No Logic Gap computation. Theatre still experiences Entropy decay (Entropy and Paradox are independent mechanisms).

**Evidence completeness gate:** `evidence_completeness = count(required_sources with EvidenceBundle) / count(required_sources)`. Required sources = committed sources minus optional sources (declared in `oracle_config.optional_sources[]`). Sources that timed out (intelligence gaps) do not count towards completeness. Aligns with AC-1 GapKind semantics from Cycle-004.

### Circuit Breaker Actions (mode: `enabled` only)

| Logic Gap Status | Action | Market Effect |
|-----------------|--------|--------------|
| STRESSED (warn) | WARN | No market intervention. PARADOX Wing Flap recorded. Dashboard alert. |
| DANGER (breach) | TRADING_PAUSE | Market transitions to temporary halt. No new trades accepted. Existing positions maintained. Enforced in `backend/engines/integration.py` by rejecting trade execution when a `halted` flag is set — no modification to `backend/market/` modules. |
| CRITICAL | FORCED_RESOLUTION | Market transitions to RESOLVING. Resolution outcome is deterministic: `winning_outcome = 1 if p_reality >= 0.5 else 0` (binary markets only). |

**Mode overrides:**
- `advisory` mode: All thresholds evaluated but capped at WARN action (log + Wing Flap). No TRADING_PAUSE or FORCED_RESOLUTION regardless of Logic Gap size.
- `circuit_breaker` mode: Only CRITICAL threshold evaluated. Fires FORCED_RESOLUTION if breached. All other readings produce no action.
- `disabled` mode: No scanning, no actions.

**Circuit breaker actions are deterministic.** Given the same Logic Gap reading, committed thresholds, and mode, the same action is always taken. No discretion.

### Wiring Entropy ← Paradox

Sprint 2 wires the Paradox Engine's Logic Gap status into the Entropy Engine's tick. The Entropy Engine's decay rate now scales with real Logic Gap data instead of defaulting to "healthy".

### Sprint 2 Architecture (additions to Sprint 1)

```
backend/engines/
├── paradox.py                # Paradox Engine — Logic Gap, thresholds, circuit breakers (NEW)
├── reality_signal.py         # RealitySignalProvider — p_reality with provenance (NEW)
├── logic_gap.py              # Logic Gap calculation, p_market smoothing (NEW)
└── tests/
    ├── test_paradox.py           # Threshold evaluation, circuit breaker actions (NEW)
    ├── test_logic_gap.py         # p_market smoothing, p_reality sources, gap calculation (NEW)
    ├── test_circuit_breakers.py  # Trading pause, forced resolution, mode overrides (NEW)
    └── test_entropy_paradox.py   # Entropy scaling with real Logic Gap status (NEW)
```

### Sprint 2 Tasks

1. **Logic Gap calculation** — p_market from LMSR prices with trailing window smoothing. p_reality from composite_score (osint) or deterministic scorer output.
2. **Paradox Engine** — Scan on PARADOX heartbeat tick. Evaluate against committed thresholds. Check activation gates.
3. **Paradox mode handling** — Implement four modes: `disabled` (no-op), `enabled` (full lifecycle), `advisory` (log-only), `circuit_breaker` (critical-only). Mode determines which thresholds are evaluated and which actions fire.
4. **Circuit breaker actions** — WARN (log + Wing Flap), TRADING_PAUSE (halt market), FORCED_RESOLUTION (push to RESOLVING). Mode-gated.
5. **Evidence completeness gate** — Required sources calculation per AC-1 GapKind semantics. Optional sources declared in `oracle_config.optional_sources[]`. Latch semantics: once satisfied, never reverts.
6. **Entropy ← Paradox wiring** — Entropy Engine receives real Logic Gap status from Paradox Engine scans.
7. **Paradox configuration** — Committed at Theatre creation, immutable. Default policies per inquiry class (mode + thresholds + gate). Included in commitment hash.
8. **Paradox tests** — Threshold crossing at exact boundaries, circuit breaker determinism, activation gate latch behaviour, mode-dependent action filtering.
9. **Logic Gap tests** — p_market smoothing accuracy, p_reality source switching, gap calculation at edge values (0.0, 0.5, 1.0), gap_direction sign correctness.
10. **Integration tests** — Full loop: trade → price moves → Logic Gap diverges → threshold crossed → circuit breaker fires → Wing Flap recorded → Entropy rate escalates. Test all four modes.

### Sprint 2 Success Criteria

- [ ] Logic Gap = `abs(p_market - p_reality)` correctly computed
- [ ] p_market uses trailing window smoothing (configurable, default 60s)
- [ ] p_reality from `osint` source reads `composite_score` correctly
- [ ] p_reality from `deterministic` source reads scorer output correctly
- [ ] Logic Gap status thresholds match Paradox Policy Design Note v1.1 defaults
- [ ] Activation gates prevent premature Paradox activation (evidence completeness, time elapsed)
- [ ] `enabled` mode: WARN at warn threshold, TRADING_PAUSE at breach, FORCED_RESOLUTION at critical
- [ ] `advisory` mode: all thresholds produce WARN only (log + Wing Flap, no market intervention)
- [ ] `circuit_breaker` mode: only critical threshold evaluated, fires FORCED_RESOLUTION
- [ ] `disabled` mode: scan returns None, no Logic Gap computation
- [ ] Circuit breaker actions are deterministic (same input + mode → same action)
- [ ] Activation gate uses latch semantics (once satisfied, stays satisfied for Theatre lifetime)
- [ ] Entropy Engine correctly receives and responds to Paradox Logic Gap status
- [ ] Paradox configuration is immutable after Theatre commitment
- [ ] Paradox thresholds are included in commitment hash
- [ ] All existing tests pass (447+ pipeline + MCP + 45+ market + Sprint 1 engines)
- [ ] 20+ new Sprint 2 tests pass

---

## Sprint 3 — VRF Integration + Base Sepolia + MCP Status + FULL Mode Templates

### What It Is

The fairness and auditability layer. VRF injects verifiable randomness into engine operations (replacing deterministic midpoints from Sprints 1-2). Base Sepolia deploys commitment hashes and settlement proofs on-chain. MCP status integration exposes market state via `echelon_status`. The four quant templates are rerun in FULL mode with real engines.

### VRF Integration

**File:** `backend/engines/vrf.py`

```python
@dataclass
class VRFConfig:
    """Committed at Theatre creation."""
    provider: str = "chainlink_v2"       # provider identifier
    mode: str = "local"                  # "local" (deterministic stub) | "testnet" (Base Sepolia)
    seed: str | None = None              # fixed seed for local mode (e.g. "0xECHELON_VRF_010b")

class VRFProvider:
    """Verifiable Random Function provider. Abstracts local stub vs on-chain."""

    def request_randomness(self, theatre_id: str, purpose: str) -> VRFResult:
        """
        Request a random value. In local mode, returns deterministic output from seed + purpose.
        In testnet mode, calls Chainlink VRF V2 on Base Sepolia.
        """

    def verify(self, result: VRFResult) -> bool:
        """Verify the VRF proof. Always true in local mode. On-chain verification in testnet."""

@dataclass
class VRFResult:
    request_id: str
    random_value: int              # uint256
    proof: bytes | None            # None in local mode
    verified: bool
    purpose: str                   # what this randomness was used for (audit trail)
```

**VRF application points (010b):**

| Application | Where Used | Effect |
|-------------|-----------|--------|
| Sabotage impact | Butterfly Engine | VRF determines exact impact within committed -5% to -15% range |
| Circuit breaker offset | Paradox Engine | VRF adds randomised offset to base thresholds (prevents gaming) |
| Entropy pricing | Entropy Engine | VRF-scaled dynamic risk adjustment |

**010b constraint:** VRF in **local mode** by default — deterministic stub using fixed seed. Base Sepolia testnet mode is opt-in (requires deployed VRF consumer contract). Both modes produce the same interface; tests run against local mode unconditionally. Testnet VRF tests are marked `@pytest.mark.testnet` and skipped when Base Sepolia is unreachable. **VRF testnet availability must not block Sprint 3 completion.** Sprint 3 ships green on local mode alone; testnet is a bonus.

### Base Sepolia Deployment

**File:** `backend/chain/sepolia.py` (new directory)

```python
class BaseSepoliaClient:
    """Publishes commitment hashes and settlement proofs to Base Sepolia testnet."""

    def publish_commitment(self, theatre_id: str, commitment_hash: str) -> TxReceipt:
        """Publish commitment hash on-chain. Returns transaction receipt."""

    def publish_settlement(self, theatre_id: str, settlement_hash: str,
                           winning_outcome: int) -> TxReceipt:
        """Publish settlement proof on-chain. Returns transaction receipt."""

    def verify_commitment(self, theatre_id: str) -> CommitmentRecord | None:
        """Read commitment from chain. Returns None if not found."""

    def verify_settlement(self, theatre_id: str) -> SettlementRecord | None:
        """Read settlement proof from chain. Returns None if not found."""
```

**What goes on-chain:**
- Commitment hash (SHA-256 of canonicalised Theatre parameters — from 010a)
- Settlement hash (SHA-256 of SettlementReport — from 010a)
- Winning outcome index
- Theatre ID → hash mapping

**What does NOT go on-chain in 010b:**
- No token transfers (no $ECHELON)
- No agent wallets (no ERC-6551)
- No escrow mechanics
- No fee collection

**Smart contract:** Minimal `EchelonCommitment.sol` — stores `theatre_id → commitment_hash` and `theatre_id → settlement_hash` mappings. Read/write. No admin functions. Contract address is pinned per Sprint 3 run; redeploy allowed between runs; no upgrade mechanism in 010b (testnet only).

### MCP Status Integration

**File:** If Cycle-009 merged: extend `mcp/tools/`. Otherwise: `backend/engines/status.py` (local function, wired to MCP later).

Expose live market state via `echelon_status(theatre_id=...)` or `market_status_snapshot(theatre_id)`:

```python
# market status response schema (used by echelon_status or market_status_snapshot)
{
    "theatre_id": "...",
    "market_phase": "TRADING",
    "current_prices": [0.65, 0.35],
    "total_trades": 42,
    "timeline_stability": 0.87,
    "logic_gap_status": "healthy",
    "logic_gap_value": 0.12,
    "heartbeat_ticks": {"agent": 100, "market": 50, "paradox": 17, "entropy": 8},
    "commitment_hash": "sha256:...",
    "on_chain": true
}
```

### FULL Mode Quant Templates

Rerun all four LMSR quant templates with real engines replacing LOCAL_MODE stubs:

| LOCAL_MODE Stub | FULL Mode Replacement |
|-----------------|----------------------|
| VRF fixed seed `0xECHELON_LOCAL` | VRF local mode with `0xECHELON_VRF_010b` seed (deterministic but via VRF provider interface) |
| Heartbeat stubbed always-alive | Real Heartbeat Scheduler ticking |
| Saboteur/paradox no-op injectors | Real Paradox Engine scanning, real Butterfly Engine recording |

**FULL mode baselines** stored in `fixtures/echelon_quant_v0_2/full_mode_baselines.json`. FULL mode baselines are computed once during Sprint 3 and pinned. Acceptance criterion: templates pass their own FULL mode expected baselines (not a comparison against LOCAL_MODE). Engines may legitimately change composites (e.g. Paradox pauses trading, Entropy escalates decay) — the baselines capture the correct engine-active behaviour.

### Sprint 3 Architecture (additions to Sprints 1-2)

```
backend/engines/
├── vrf.py                    # VRF provider abstraction (NEW)
└── tests/
    ├── test_vrf.py               # Local + testnet modes, verification, determinism (NEW)
    └── test_full_mode_templates.py  # Four quant templates in FULL mode (NEW)

backend/chain/
├── __init__.py
├── sepolia.py                # Base Sepolia client (NEW)
├── contracts/
│   └── EchelonCommitment.sol # Minimal commitment/settlement store (NEW)
└── tests/
    ├── test_sepolia.py           # Publish + verify commitment and settlement (NEW)
    └── test_contract.py          # Solidity contract unit tests (NEW)

backend/engines/
├── status.py                 # market_status_snapshot() — local fallback if MCP not merged (NEW)

mcp/tools/                    # Extended only if Cycle-009 merged
└── (echelon_status wired to market_status_snapshot)
```

### Sprint 3 Tasks

1. **VRF provider** — Local mode (deterministic from seed) and testnet mode (Chainlink VRF V2 on Base Sepolia). Same interface.
2. **VRF wiring** — Inject VRF into Butterfly Engine (sabotage impact), Paradox Engine (threshold offsets), Entropy Engine (pricing).
3. **Base Sepolia client** — Publish commitment hash and settlement hash. Read and verify.
4. **EchelonCommitment.sol** — Minimal Solidity contract: store and read theatre → hash mappings.
5. **Deploy contract** — Hardhat deployment script for Base Sepolia testnet.
6. **MCP status integration** — If Cycle-009 `echelon_status` is merged, extend it to return market phase, prices, stability, Logic Gap, heartbeat ticks, on-chain status. If not merged, implement a local `market_status_snapshot(theatre_id)` function returning the same schema; wire to MCP later.
7. **FULL mode quant templates** — Rerun all four templates with real engines. Compute FULL mode baselines. Verify locally via direct verifier import (`backend/scoring/` pipeline); if Cycle-009 MCP is merged, also verify via `echelon_verify` tool. Verification transport must not block Sprint 3.
8. **VRF tests** — Determinism in local mode (same seed → same output), verification correctness, purpose-based audit trail.
9. **Chain tests** — Publish/verify round-trip, contract read/write, transaction receipt validation.
10. **Status tests** — `market_status_snapshot` returns correct live data. If MCP merged, `echelon_status` delegates to same function.
11. **End-to-end test** — Full lifecycle with all engines: create market → commit (on-chain) → start heartbeat → trade → observe Wing Flaps → Paradox scans → Entropy decays → resolve → settle (on-chain) → verify certificate → verify on-chain proofs.

### Sprint 3 Success Criteria

- [ ] VRF local mode produces deterministic outputs from fixed seed
- [ ] VRF testnet mode calls Chainlink VRF V2 on Base Sepolia (when configured; `@pytest.mark.testnet`, non-blocking)
- [ ] VRF proof verification works in local mode unconditionally; testnet verification non-blocking
- [ ] Sabotage stability impact is VRF-randomised within committed range
- [ ] Circuit breaker threshold offsets are VRF-randomised
- [ ] Commitment hash published to Base Sepolia and readable
- [ ] Settlement hash published to Base Sepolia and readable
- [ ] `market_status_snapshot(theatre_id)` returns live market state with all engine data (MCP-wired if Cycle-009 merged)
- [ ] `quant_market_hygiene_v1` passes in FULL mode
- [ ] `quant_market_perturbation_harness_v1` passes in FULL mode
- [ ] `quant_market_api_fidelity_v1` passes in FULL mode
- [ ] `lmsr_b_sensitivity_suite_v1` passes in FULL mode
- [ ] FULL mode baselines computed, pinned, and stored in `fixtures/echelon_quant_v0_2/full_mode_baselines.json`
- [ ] End-to-end lifecycle passes with all engines active
- [ ] All existing tests pass (447+ pipeline + MCP + 45+ market + Sprint 1-2 engines)
- [ ] 25+ new Sprint 3 tests pass

---

## Scope Exclusions

- **No agent brain execution.** Agents submit trades via direct function calls. No LLM routing, no brain tiers, no autonomous decision-making. Agent architecture is a future cycle.
- **No real OSINT feeds.** p_reality uses existing composite_score from Cycle-007/008 pipeline or deterministic scorers. No live OSINT polling.
- **No token mechanics.** No $ECHELON, no burn, no staking. On-chain is commitment/settlement hashes only.
- **No ERC-6551 agent wallets.** Agent positions are in-memory. No on-chain wallet identity.
- **No distributed scheduling.** Heartbeat is asyncio-local. No Redis, no Celery, no message queues.
- **No mainnet deployment.** Base Sepolia testnet only.
- **No cross-timeline Ripple flaps.** RIPPLE Wing Flap type exists in schema but is not wired to any source. Single-timeline only in 010b.
- **No database persistence.** All state is in-memory (continues 010a pattern). Persistence deferred. This means `echelon_status` / `market_status_snapshot` serves live in-memory state only — after process restart, all Theatre state is lost. No misleading "store" semantics.
- **No frontend.** No UI for engine state, stability, or Logic Gap visualisation.
- **Paradox forced resolution is binary-only.** `winning_outcome = 1 if p_reality >= 0.5 else 0`. Multi-outcome Paradox resolution requires a `p_reality` vector interface — deferred to a future cycle.

---

## Dependency Chain

```
Cycle-004 (pipeline hardening)
  → Cycles 005–006 (registry expansion + live OSINT surfaces)
    → Cycle-007 (unified Two-Rail pipeline, 447+ tests)
      → Cycle-008 (MCP verifier + construct calibration)
        → Cycle-009 (MCP surface, HTTP transport, certificate store)
          → Cycle-010a (LMSR cost function, market lifecycle, trade execution, positions, settlement)
            → Cycle-010b (Butterfly, Paradox, Entropy engines, heartbeat, VRF, Base Sepolia)
              → Cycle-011 (WorldMonitor Integration)
              → Cycle-012 (Sponsored Theatre E2E)
```

## After Cycle-010b

The full engine stack is live. Markets trade against LMSR, the game loop ticks, causal transitions are recorded, integrity is policed, randomness is verifiable, and proofs are on-chain. The four quant templates pass in FULL mode — the platform is certified.

**Cycle-011 — WorldMonitor Integration:** Real-time OSINT dashboard feeding the Composed Oracle. CII endpoint, maritime anomaly detection, convergence signals.

**Cycle-012 — Sponsored Theatre End-to-End:** First externally-commissioned Theatre. Requires the full engine stack from 010b.

---

## Workflow

```bash
cd ~/Developer/prediction-market-monorepo.nosync
claude

# Copy this file into Loa context
cp ~/Developer/echelon/loa_feed/echelon_cycle_010b_context.md grimoires/loa/context/echelon_cycle_010b.md

# Sprint 1: Butterfly + Entropy + Heartbeat
/plan
/simstim
/run-bridge

# Verify Sprint 1
python3 -m pytest backend/engines/tests/ -v

# Sprint 2: Paradox Engine + Logic Gap
/plan
/simstim
/run-bridge

# Verify Sprint 2
python3 -m pytest backend/engines/tests/ -v

# Sprint 3: VRF + Base Sepolia + FULL mode
/plan
/simstim
/run-bridge

# Verify Sprint 3: FULL mode quant templates
python3 -m pytest backend/engines/tests/test_full_mode_templates.py -v

# Full test suite
python3 -m pytest -q
```

---

## Key Spec References

| Document | Relevance |
|----------|-----------|
| Echelon System Bible v13 — Section V (Integrity Mechanisms) | Butterfly Engine, Entropy Engine, Wing Flap types, stability impacts, heartbeat schedule |
| Echelon System Bible v13 — Section VII (VRF Integration) | Chainlink VRF V2, six application points, security properties |
| Echelon System Bible v13 — Section VI (Commitment Protocol) | On-chain commitment hash, parameter set, settlement proof |
| Echelon System Bible v13 — Section IV (Resolution & Settlement) | Automatic settlement, resolution state machine |
| Echelon Paradox Policy Design Note v1.1 | Logic Gap definition, p_reality = composite_score, evidence_completeness gate, threshold defaults |
| Echelon Theatre Template Library Live v2 | Four LMSR quant templates for FULL mode acceptance |
| REPO_MAP.md | Existing engine, simulation, and MCP directory structure |
