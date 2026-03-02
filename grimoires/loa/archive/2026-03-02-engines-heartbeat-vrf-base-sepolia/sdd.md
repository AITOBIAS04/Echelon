# SDD: Engines + Heartbeat + VRF + Base Sepolia

**Cycle**: 010b
**Version**: 1.0
**Date**: 2026-03-02
**PRD**: `grimoires/loa/prd.md` v1.0
**Predecessor**: Cycle-010a SDD (archived)

---

## 1. Executive Summary

Cycle-010b layers three engine subsystems, a heartbeat scheduler, verifiable randomness, and on-chain proof publication on top of the proven 010a LMSR market engine. The architecture follows the same principles as 010a: in-memory state, pure Python computation, deterministic behaviour, comprehensive tests. New concerns — async scheduling, external chain interaction, multi-engine coordination — are contained in `backend/engines/` and `backend/chain/`, keeping the proven `backend/market/` package untouched.

**Key architectural decisions**:
1. **Wrapper pattern** for 010a integration (no event emitter, no monkey-patching)
2. **asyncio-native** heartbeat scheduler (single process, no external dependencies)
3. **Provider abstraction** for VRF and reality signals (local stub → testnet via interface swap)
4. **Latch semantics** for activation gates (monotonic, no flicker)
5. **HMAC-SHA256** for VRF local mode determinism

---

## 2. System Architecture

### 2.1 Component Topology

```
                    ┌──────────────────────────────────────────┐
                    │           backend/engines/                │
                    │                                           │
                    │  ┌─────────────┐   ┌──────────────┐     │
                    │  │  heartbeat  │──▶│  integration  │     │
                    │  │  scheduler  │   │    layer      │     │
                    │  └──────┬──────┘   └──────┬───────┘     │
                    │         │                  │              │
                    │    ticks│            wraps │              │
                    │         │                  │              │
                    │  ┌──────▼──────┐   ┌──────▼───────┐     │
                    │  │  entropy    │   │  butterfly    │     │
                    │  │  engine     │──▶│  engine       │     │
                    │  └──────┬──────┘   └──────────────┘     │
                    │         │                                 │
                    │    reads│ logic_gap_status (Sprint 2)     │
                    │         │                                 │
                    │  ┌──────▼──────┐   ┌──────────────┐     │
                    │  │  paradox    │◀──│  reality      │     │
                    │  │  engine     │   │  signal       │     │
                    │  └─────────────┘   └──────────────┘     │
                    │                                           │
                    │  ┌─────────────┐   ┌──────────────┐     │
                    │  │    vrf      │   │   status      │     │
                    │  │  provider   │   │  snapshot     │     │
                    │  └─────────────┘   └──────────────┘     │
                    └───────────────────────┬──────────────────┘
                                            │ reads (never writes)
                    ┌───────────────────────▼──────────────────┐
                    │         backend/market/ (010a)            │
                    │   LMSREngine · TradingEngine · lifecycle  │
                    │   PositionManager · ResolutionEngine      │
                    │         *** READ-ONLY from 010b ***       │
                    └──────────────────────────────────────────┘

                    ┌──────────────────────────────────────────┐
                    │         backend/chain/ (Sprint 3)         │
                    │   BaseSepoliaClient · EchelonCommitment   │
                    └──────────────────────────────────────────┘
```

### 2.2 Data Flow

```
Trade request
  → integration.execute_trade_with_flap(market, agent, outcome, shares)
    → TradingEngine.execute_trade()  [010a, unmodified]
    → ButterflyEngine.record_flap(TRADE, ...)
    → return Trade

Heartbeat tick (ENTROPY cadence)
  → EntropyEngine.tick(theatre_id, logic_gap_status)
    → ButterflyEngine.record_flap(ENTROPY, ...)
    → TimelineState.stability decremented

Heartbeat tick (PARADOX cadence, Sprint 2)
  → ParadoxEngine.scan(theatre_id)
    → LMSREngine.prices()  [010a, read-only]
    → RealitySignalProvider.get_signal()
    → LogicGapReading computed
    → ParadoxEngine.evaluate_thresholds()
    → If action: ParadoxEngine.execute_action()
      → ButterflyEngine.record_flap(PARADOX, ...)
      → If TRADING_PAUSE: integration.halt_trading(theatre_id)
      → If FORCED_RESOLUTION: MarketLifecycle.begin_resolution()
```

---

## 3. Technology Stack

| Layer | Technology | Justification |
|-------|-----------|---------------|
| Language | Python 3.9+ | Matches 010a; `from __future__ import annotations` for PEP 604 |
| Async | `asyncio` stdlib | Single-process scheduler; no external deps needed |
| Hashing | `hashlib` + `hmac` stdlib | SHA-256 for VRF local mode; reuses 010a pattern |
| Serialisation | `theatre.engine.canonical_json` | Reuses 010a's RFC 8785 canonical JSON |
| Chain interaction | `web3.py` (Sprint 3 only) | Standard Ethereum client library |
| Smart contracts | Solidity + Hardhat | Existing infra in `smart-contracts/` |
| Testing | `pytest` + `pytest-asyncio` | Async test support for heartbeat tests |

**New dependency**: `pytest-asyncio` (test-only, for async heartbeat/integration tests).

---

## 4. Component Design

### 4.1 Engine Configuration (`backend/engines/config.py`)

Committed engine parameters. Immutable after Theatre commitment. Included in commitment hash.

```python
@dataclass
class ButterflyConfig:
    trade_impact_k: float = 0.1           # k in clamp(k × notional / liquidity_depth)
    trade_impact_policy: str = "buy_negative_sell_positive"
    shield_tiers: dict[str, float]        # {"easy": 0.02, "medium": 0.05, "hard": 0.10}
    sabotage_impact: float = -0.10        # deterministic midpoint (Sprint 1-2)

@dataclass
class EntropyConfig:
    base_decay_rate: float = 0.01
    stressed_multiplier: float = 1.5
    danger_multiplier: float = 2.0
    critical_multiplier: float = 3.0

@dataclass
class EngineConfig:
    """Top-level committed engine configuration per Theatre."""
    butterfly: ButterflyConfig
    entropy: EntropyConfig
    paradox: ParadoxConfig | None = None  # None in Sprint 1
    vrf: VRFConfig | None = None          # None in Sprints 1-2
    committed: bool = False               # Frozen after commitment

    def freeze(self) -> None:
        """Mark as committed. Raises if already committed."""

    def to_commitment_dict(self) -> dict:
        """Serialisable dict for inclusion in commitment hash."""
```

**Immutability enforcement**: `freeze()` sets `committed = True`. All config setters raise `ParameterMutationAfterCommit` (reused from 010a exceptions) when `committed is True`.

### 4.2 Butterfly Engine (`backend/engines/butterfly.py`)

```python
class WingFlapType(str, Enum):
    TRADE = "TRADE"
    SHIELD = "SHIELD"
    SABOTAGE = "SABOTAGE"
    RIPPLE = "RIPPLE"      # schema only — no source in 010b
    PARADOX = "PARADOX"
    ENTROPY = "ENTROPY"

@dataclass
class WingFlap:
    flap_id: str
    theatre_id: str
    flap_type: WingFlapType
    agent_id: str | None        # None for system flaps (ENTROPY, RIPPLE)
    stability_impact: float     # signed: positive = stabilising, negative = destabilising
    pre_stability: float
    post_stability: float
    trigger_detail: dict        # type-specific metadata
    timestamp: str

@dataclass
class TimelineState:
    theatre_id: str
    stability: float = 1.0     # 0.0–1.0, starts at 1.0
    volume: float = 0.0        # cumulative trade volume (abs cost)
    flap_count: int = 0
    founders_yield_accrued: float = 0.0

class ButterflyEngine:
    def __init__(self) -> None:
        self._timelines: dict[str, TimelineState] = {}
        self._flaps: dict[str, list[WingFlap]] = {}  # theatre_id → flaps
        self._flap_counter: int = 0

    def record_flap(self, flap_type, theatre_id, agent_id, impact, trigger_detail) -> WingFlap:
        """
        1. Get or create TimelineState for theatre_id
        2. pre_stability = current stability
        3. post_stability = clamp(pre_stability + impact, 0.0, 1.0)
        4. Update TimelineState.stability, increment flap_count
        5. If TRADE: add abs(trigger_detail["cost"]) to volume
        6. Create WingFlap, append to audit trail
        7. Return WingFlap
        """

    def get_timeline_state(self, theatre_id) -> TimelineState
    def get_flaps(self, theatre_id) -> list[WingFlap]  # audit trail query

    def compute_founders_yield(self, theatre_id) -> float:
        """yield = stability × volume × 0.005"""
```

**Key invariant**: `0.0 ≤ stability ≤ 1.0` enforced at write time via `clamp()`. No read-time normalisation.

**Audit trail**: `_flaps[theatre_id]` is append-only. Never mutated after insertion. Queryable by theatre.

### 4.3 Entropy Engine (`backend/engines/entropy.py`)

```python
class EntropyEngine:
    def __init__(self, config: EntropyConfig, butterfly: ButterflyEngine) -> None:
        self._config = config
        self._butterfly = butterfly

    def tick(self, theatre_id: str, logic_gap_status: str = "healthy") -> WingFlap:
        """
        1. Compute effective decay rate from logic_gap_status
        2. impact = -effective_rate (always negative — decay is destabilising)
        3. Record ENTROPY Wing Flap via ButterflyEngine
        4. Return WingFlap
        """

    def get_effective_decay_rate(self, logic_gap_status: str) -> float:
        """
        healthy  → base_decay_rate
        stressed → base × stressed_multiplier
        danger   → base × danger_multiplier
        critical → base × critical_multiplier
        Unknown status → base_decay_rate (defensive default)
        """
```

**Sprint 1 usage**: `tick(theatre_id)` — defaults to `"healthy"`.
**Sprint 2 wiring**: `tick(theatre_id, paradox_engine.last_reading.status.value)`.

### 4.4 Heartbeat Scheduler (`backend/engines/heartbeat.py`)

```python
@dataclass
class HeartbeatConfig:
    agent_interval_s: float = 5.0
    market_interval_s: float = 10.0
    paradox_interval_s: float = 30.0
    entropy_interval_s: float = 60.0

CADENCES = ["agent", "market", "paradox", "entropy"]

class HeartbeatScheduler:
    def __init__(self, config: HeartbeatConfig) -> None:
        self._config = config
        self._handlers: dict[str, list[Callable]] = {c: [] for c in CADENCES}
        self._tasks: dict[tuple[str, str], asyncio.Task] = {}  # (theatre_id, cadence) → Task
        self._tick_counts: dict[str, dict[str, int]] = {}      # theatre_id → {cadence: count}

    def register_handler(self, cadence: str, handler: Callable) -> None:
        """Register async handler for a cadence. Shared across all theatres."""

    async def start(self, theatre_id: str) -> None:
        """
        For each cadence:
          1. Create asyncio.Task running _tick_loop(theatre_id, cadence, interval)
          2. Store in _tasks[(theatre_id, cadence)]
        """

    async def stop(self, theatre_id: str) -> None:
        """
        Cancel all tasks for theatre_id. Await cancellation. Idempotent.
        """

    def tick_count(self, theatre_id: str) -> dict[str, int]:
        """Return {cadence: tick_count} for monitoring."""

    async def _tick_loop(self, theatre_id, cadence, interval) -> None:
        """
        while True:
            await asyncio.sleep(interval)
            for handler in self._handlers[cadence]:
                await handler(theatre_id)
            self._tick_counts[theatre_id][cadence] += 1
        """
```

**Design decision**: Handlers are registered per cadence, not per theatre. All theatres share the same handler set. This is correct because the handler functions (e.g., entropy tick) are engine methods that take `theatre_id` as a parameter — they already know which theatre to operate on.

**Graceful shutdown**: `stop()` cancels tasks and awaits `CancelledError`. No leaked tasks.

**Concurrency**: Each `_tick_loop` is a separate `asyncio.Task`. Multiple theatres create independent task sets. No shared mutable state between tick loops.

### 4.5 Integration Layer (`backend/engines/integration.py`)

```python
class EngineOrchestrator:
    """Wires engines to 010a market system. One instance per Theatre session."""

    def __init__(
        self,
        market: MarketState,
        trading_engine: TradingEngine,
        position_manager: PositionManager,
        butterfly: ButterflyEngine,
        entropy: EntropyEngine,
        engine_config: EngineConfig,
        heartbeat: HeartbeatScheduler,
        paradox: ParadoxEngine | None = None,  # Sprint 2
        vrf: VRFProvider | None = None,         # Sprint 3
    ) -> None:
        self._halted: bool = False  # circuit breaker halt flag

    def execute_trade_with_flap(self, agent_id, outcome_index, shares) -> Trade:
        """
        1. Check self._halted → raise TradingHalted if True
        2. Call self._trading_engine.execute_trade(...)
        3. Compute stability impact: clamp(k × abs(cost) / b, -0.05, 0.05)
           Sign: negative if buy (destabilising), positive if sell (stabilising)
        4. Record TRADE Wing Flap via ButterflyEngine
        5. Return Trade
        """

    def halt_trading(self, theatre_id: str) -> None:
        """Set _halted = True. Called by Paradox TRADING_PAUSE action."""

    def resume_trading(self, theatre_id: str) -> None:
        """Set _halted = False. For manual intervention."""

    async def start(self) -> None:
        """
        Register handlers on heartbeat:
          - entropy cadence → self._entropy_tick_handler
          - paradox cadence → self._paradox_tick_handler (Sprint 2)
        Start heartbeat for theatre.
        """

    async def stop(self) -> None:
        """Stop heartbeat. Clean shutdown."""
```

**Pattern**: Wrapper/delegation, not decoration or monkey-patching. The caller uses `orchestrator.execute_trade_with_flap()` instead of `trading_engine.execute_trade()`. This is explicit — no hidden side effects.

**Circuit breaker halt**: A boolean flag `_halted` checked before delegating to `TradingEngine`. Does not modify `backend/market/` modules.

### 4.6 Logic Gap Calculator (`backend/engines/logic_gap.py`)

```python
class LogicGapStatus(str, Enum):
    HEALTHY = "healthy"       # < 20%
    STRESSED = "stressed"     # 20-40%
    DANGER = "danger"         # 40-60%
    CRITICAL = "critical"     # > 60%

@dataclass
class LogicGapReading:
    theatre_id: str
    p_market: float
    p_reality: float
    logic_gap: float          # abs(p_market - p_reality)
    gap_direction: float      # signed: p_market - p_reality
    status: LogicGapStatus
    smoothing_window_s: float
    timestamp: str

class LogicGapCalculator:
    def __init__(self, smoothing_window_s: float = 60.0) -> None:
        self._price_history: dict[str, list[tuple[float, float]]] = {}
        # theatre_id → [(timestamp_s, p_market), ...]

    def record_price(self, theatre_id: str, p_market: float, timestamp_s: float) -> None:
        """Append price observation. Prune entries older than window."""

    def get_smoothed_p_market(self, theatre_id: str) -> float:
        """Simple average over trailing window. Falls back to latest if < 2 entries."""

    def compute(self, theatre_id: str, p_reality: float) -> LogicGapReading:
        """
        1. p_market = get_smoothed_p_market(theatre_id)
        2. logic_gap = abs(p_market - p_reality)
        3. gap_direction = p_market - p_reality
        4. status = classify(logic_gap) based on thresholds
        5. Return LogicGapReading
        """

    @staticmethod
    def classify(logic_gap: float) -> LogicGapStatus:
        if logic_gap < 0.20: return HEALTHY
        if logic_gap < 0.40: return STRESSED
        if logic_gap < 0.60: return DANGER
        return CRITICAL
```

**Smoothing**: Simple trailing-window average. Not exponential moving average — simpler, sufficient for 010b. Window is configurable per Theatre.

**Price recording**: `record_price()` is called by the integration layer after each trade (using post-trade prices from 010a). Prunes entries outside the window to prevent unbounded memory growth.

### 4.7 Reality Signal Provider (`backend/engines/reality_signal.py`)

```python
@dataclass
class RealitySignal:
    p_reality: float              # 0.0–1.0
    evidence_bundle_hash: str     # SHA-256 of evidence bundle
    certificate_id: str | None    # calibration certificate ID (osint) or None
    source_type: str              # "osint" | "deterministic" | "survey" | "simulation"

class RealitySignalProvider:
    """Abstract provider. Subclassed per source type."""

    def get_signal(self, theatre_id: str) -> RealitySignal:
        raise NotImplementedError

class OsintRealityProvider(RealitySignalProvider):
    """Reads composite_score from most recent calibration certificate."""
    def get_signal(self, theatre_id: str) -> RealitySignal:
        # Read composite_score from certificate store
        # Return RealitySignal with provenance

class DeterministicRealityProvider(RealitySignalProvider):
    """Reads scorer output (0.0 or 1.0) from deterministic computation."""
    def get_signal(self, theatre_id: str) -> RealitySignal:
        # Read scorer output
        # Return RealitySignal with provenance

class StubRealityProvider(RealitySignalProvider):
    """For testing — returns configurable fixed p_reality."""
    def __init__(self, p_reality: float = 0.5) -> None: ...
    def get_signal(self, theatre_id: str) -> RealitySignal: ...
```

**Design**: Subclass per source type, injected into ParadoxEngine via constructor. Paradox never knows the concrete type — it only calls `get_signal()`. The `StubRealityProvider` enables deterministic testing without real OSINT or scorers.

### 4.8 Paradox Engine (`backend/engines/paradox.py`)

```python
class ParadoxMode(str, Enum):
    DISABLED = "disabled"
    ENABLED = "enabled"
    ADVISORY = "advisory"
    CIRCUIT_BREAKER = "circuit_breaker"

class ParadoxAction(str, Enum):
    WARN = "warn"
    TRADING_PAUSE = "trading_pause"
    FORCED_RESOLUTION = "forced_resolution"

@dataclass
class ParadoxConfig:
    mode: ParadoxMode
    inquiry_class: str
    warn_threshold: float | None     # None when mode is circuit_breaker
    breach_threshold: float | None   # None when mode is circuit_breaker
    critical_threshold: float
    activation_gate: dict            # {"type": "none"} | {"type": "min_evidence_completeness", "value": 0.5}
    logic_gap_source: str            # "osint" | "deterministic"
    smoothing_window_s: float = 60.0

@dataclass
class ParadoxRuntimeState:
    activation_gate_satisfied: bool = False  # latch: once True, never reverts
    last_reading: LogicGapReading | None = None
    scan_count: int = 0

class ParadoxEngine:
    def __init__(
        self,
        config: ParadoxConfig,
        butterfly: ButterflyEngine,
        logic_gap_calc: LogicGapCalculator,
        reality_provider: RealitySignalProvider,
    ) -> None:
        self._config = config
        self._butterfly = butterfly
        self._logic_gap_calc = logic_gap_calc
        self._reality_provider = reality_provider
        self._runtime: dict[str, ParadoxRuntimeState] = {}

    def scan(self, theatre_id: str) -> LogicGapReading | None:
        """
        1. If mode == DISABLED: return None
        2. Check activation gate (latch semantics)
        3. If gate not satisfied: return None
        4. Get reality signal from provider
        5. Compute Logic Gap via calculator
        6. Store as last_reading in runtime state
        7. Return LogicGapReading
        """

    def evaluate_thresholds(self, reading: LogicGapReading) -> ParadoxAction | None:
        """
        Mode-dependent evaluation:
        - DISABLED: return None (should not be called)
        - ENABLED: check critical → breach → warn (highest severity first)
        - ADVISORY: check all thresholds, but cap at WARN
        - CIRCUIT_BREAKER: check critical only, skip warn/breach
        Returns highest applicable action, or None if below all thresholds.
        """

    def check_activation_gate(self, theatre_id: str) -> bool:
        """
        Check gate conditions. LATCH: once True, stays True forever.
        Gate types:
        - "none": always satisfied
        - "min_evidence_completeness": evidence_completeness >= value
        - "min_time_elapsed": time since trading opened >= value seconds
        - "min_observations": scan_count >= value
        """

    def execute_action(self, action: ParadoxAction, theatre_id: str) -> WingFlap:
        """
        WARN: record PARADOX Wing Flap with impact -0.10
        TRADING_PAUSE: record with impact -0.20, halt trading
        FORCED_RESOLUTION: record with impact -0.30, force market to RESOLVING
        """

    def get_last_reading(self, theatre_id: str) -> LogicGapReading | None
```

**Threshold evaluation order**: Check critical first, then breach, then warn. Return the highest severity action. This means if Logic Gap is 65% (CRITICAL), the action is FORCED_RESOLUTION, not WARN.

**Latch semantics**: `check_activation_gate()` checks the condition, and if True, sets `runtime.activation_gate_satisfied = True`. Future calls return True immediately without re-checking. This prevents flicker when evidence sources go temporarily offline.

### 4.9 VRF Provider (`backend/engines/vrf.py`)

```python
@dataclass
class VRFConfig:
    provider: str = "chainlink_v2"
    mode: str = "local"                    # "local" | "testnet"
    seed: str | None = "0xECHELON_VRF_010b"  # fixed for local mode

@dataclass
class VRFResult:
    request_id: str
    random_value: int            # uint256 range
    proof: bytes | None          # None in local mode
    verified: bool
    purpose: str

class VRFProvider:
    def __init__(self, config: VRFConfig) -> None:
        self._config = config
        self._request_counter: int = 0

    def request_randomness(self, theatre_id: str, purpose: str) -> VRFResult:
        """
        Local mode:
          key = HMAC-SHA256(seed.encode(), f"{theatre_id}:{purpose}".encode())
          random_value = int.from_bytes(key, "big") % (2**256)
          Deterministic: same seed + theatre + purpose → same output.
        Testnet mode:
          Call Chainlink VRF V2 consumer contract on Base Sepolia.
          Wait for fulfilment callback.
        """

    def verify(self, result: VRFResult) -> bool:
        """Local: always True. Testnet: on-chain proof verification."""

    def scale_to_range(self, random_value: int, min_val: float, max_val: float) -> float:
        """Scale uint256 to [min_val, max_val] range. Used by engines."""
```

**HMAC-SHA256 for local mode**: Deterministic, reproducible, purpose-tagged. Not a CSPRNG — not needed for local testing. The purpose string (`"sabotage_impact"`, `"threshold_offset"`, etc.) ensures different values for different applications even within the same theatre.

**`scale_to_range()`**: Utility for engines to convert uint256 to their committed impact ranges. Avoids each engine reimplementing the same conversion.

### 4.10 Base Sepolia Client (`backend/chain/sepolia.py`)

```python
@dataclass
class TxReceipt:
    tx_hash: str
    block_number: int
    gas_used: int
    status: bool                 # True = success

@dataclass
class CommitmentRecord:
    theatre_id: str
    commitment_hash: str
    block_number: int
    timestamp: int

@dataclass
class SettlementRecord:
    theatre_id: str
    settlement_hash: str
    winning_outcome: int
    block_number: int
    timestamp: int

class BaseSepoliaClient:
    def __init__(self, rpc_url: str, contract_address: str, private_key: str) -> None:
        """Initialise web3.py connection. Private key for transaction signing."""

    def publish_commitment(self, theatre_id, commitment_hash) -> TxReceipt
    def publish_settlement(self, theatre_id, settlement_hash, winning_outcome) -> TxReceipt
    def verify_commitment(self, theatre_id) -> CommitmentRecord | None
    def verify_settlement(self, theatre_id) -> SettlementRecord | None

class MockSepoliaClient(BaseSepoliaClient):
    """In-memory mock for unit tests. No chain interaction."""
    def __init__(self) -> None:
        self._commitments: dict[str, str] = {}
        self._settlements: dict[str, tuple[str, int]] = {}
```

**EchelonCommitment.sol** (minimal):

```solidity
contract EchelonCommitment {
    mapping(string => string) public commitments;    // theatre_id → commitment_hash
    mapping(string => string) public settlements;    // theatre_id → settlement_hash
    mapping(string => uint8) public winningOutcomes;  // theatre_id → winning_outcome

    event CommitmentPublished(string theatreId, string commitmentHash);
    event SettlementPublished(string theatreId, string settlementHash, uint8 winningOutcome);

    function publishCommitment(string calldata theatreId, string calldata hash) external;
    function publishSettlement(string calldata theatreId, string calldata hash, uint8 outcome) external;
}
```

No admin functions, no access control (testnet only). Contract address pinned per deployment.

### 4.11 Market Status Snapshot (`backend/engines/status.py`)

```python
@dataclass
class MarketStatusSnapshot:
    theatre_id: str
    market_phase: str
    current_prices: list[float]
    total_trades: int
    timeline_stability: float
    logic_gap_status: str | None
    logic_gap_value: float | None
    heartbeat_ticks: dict[str, int]
    commitment_hash: str
    on_chain: bool

def market_status_snapshot(
    theatre_id: str,
    orchestrator: EngineOrchestrator,
) -> MarketStatusSnapshot:
    """Assemble live market state from all engines into a single snapshot."""
```

**MCP integration**: If Cycle-009 `echelon_status` is merged (it is), the MCP tool delegates to `market_status_snapshot()` for engine-aware data.

---

## 5. Data Models Summary

### 5.1 New Enums

| Enum | Values | Module |
|------|--------|--------|
| `WingFlapType` | TRADE, SHIELD, SABOTAGE, RIPPLE, PARADOX, ENTROPY | `butterfly.py` |
| `LogicGapStatus` | HEALTHY, STRESSED, DANGER, CRITICAL | `logic_gap.py` |
| `ParadoxMode` | DISABLED, ENABLED, ADVISORY, CIRCUIT_BREAKER | `paradox.py` |
| `ParadoxAction` | WARN, TRADING_PAUSE, FORCED_RESOLUTION | `paradox.py` |

### 5.2 New Dataclasses

| Dataclass | Fields | Module |
|-----------|--------|--------|
| `WingFlap` | 9 fields | `butterfly.py` |
| `TimelineState` | 5 fields | `butterfly.py` |
| `HeartbeatConfig` | 4 interval params | `heartbeat.py` |
| `ButterflyConfig` | 4 impact params | `config.py` |
| `EntropyConfig` | 4 decay params | `config.py` |
| `EngineConfig` | butterfly + entropy + paradox + vrf + committed | `config.py` |
| `LogicGapReading` | 8 fields | `logic_gap.py` |
| `RealitySignal` | 4 fields | `reality_signal.py` |
| `ParadoxConfig` | 8 fields | `paradox.py` |
| `ParadoxRuntimeState` | 3 fields | `paradox.py` |
| `VRFConfig` | 3 fields | `vrf.py` |
| `VRFResult` | 5 fields | `vrf.py` |
| `TxReceipt` | 4 fields | `sepolia.py` |
| `CommitmentRecord` | 4 fields | `sepolia.py` |
| `SettlementRecord` | 5 fields | `sepolia.py` |
| `MarketStatusSnapshot` | 10 fields | `status.py` |

---

## 6. Integration Points

### 6.1 010a Market Package (Read-Only)

| API Used | By | Purpose |
|----------|-----|---------|
| `TradingEngine.execute_trade()` | `integration.py` | Delegated trade execution |
| `LMSREngine.prices(x, b)` | `logic_gap.py` | p_market for Logic Gap |
| `MarketState.x`, `.b`, `.phase` | `integration.py`, `paradox.py` | Market state reads |
| `MarketLifecycle.begin_resolution()` | `paradox.py` | FORCED_RESOLUTION action |
| `PositionManager` | `integration.py` | Passed to TradingEngine |
| `ResolutionEngine.settle()` | `integration.py` | Settlement for on-chain publishing |
| `TradingHalted` exception | `integration.py` | Reused for circuit breaker halt |

### 6.2 External Dependencies

| Dependency | Source | Sprint | Used By |
|------------|--------|--------|---------|
| `theatre.engine.canonical_json` | Existing (Cycle-008) | 1+ | `config.py` (commitment hash) |
| `pytest-asyncio` | PyPI (test-only) | 1 | Async test support |
| `web3` | PyPI | 3 | `sepolia.py` (chain interaction) |

### 6.3 Existing Smart Contracts

Sprint 3 deploys `EchelonCommitment.sol` to Base Sepolia using the existing Hardhat infrastructure in `smart-contracts/`.

---

## 7. Security Considerations

| Concern | Mitigation |
|---------|-----------|
| Config mutation after commit | `EngineConfig.freeze()` + `ParameterMutationAfterCommit` exception |
| Stability bounds | `clamp(0.0, 1.0)` at write time in ButterflyEngine |
| VRF predictability (local) | HMAC-SHA256 with fixed seed — acceptable for local testing |
| VRF predictability (testnet) | Chainlink VRF V2 provides on-chain proofs |
| Private key exposure (chain) | Private key passed at runtime, not hardcoded. Testnet key only. |
| Circuit breaker determinism | Same input + mode → same action. No discretion. |
| Activation gate flicker | Latch semantics — once satisfied, stays satisfied |
| Audit trail integrity | Wing Flap list is append-only. Never mutated after insertion. |

---

## 8. Testing Strategy

### 8.1 Sprint 1 Tests (~20+)

| File | Tests | Coverage |
|------|-------|----------|
| `test_heartbeat.py` | 5+ | Timing accuracy, concurrent theatres, graceful stop, handler registration, tick counts |
| `test_butterfly.py` | 6+ | Wing Flap recording, stability clamping, yield formula, audit trail, volume tracking, multi-theatre isolation |
| `test_entropy.py` | 4+ | Base decay, multiplier scaling, boundary conditions (stability at 0), healthy default |
| `test_integration.py` | 5+ | Trade→WingFlap pipeline, heartbeat→entropy, orchestrator lifecycle, halt flag, config immutability |

### 8.2 Sprint 2 Tests (~20+)

| File | Tests | Coverage |
|------|-------|----------|
| `test_logic_gap.py` | 5+ | p_market smoothing, classification thresholds, edge values, gap direction |
| `test_paradox.py` | 5+ | Threshold evaluation, activation gate latch, mode-dependent behaviour, config inclusion in hash |
| `test_circuit_breakers.py` | 5+ | WARN/TRADING_PAUSE/FORCED_RESOLUTION actions, mode overrides, determinism |
| `test_entropy_paradox.py` | 5+ | Entropy receives real Logic Gap, escalating decay, end-to-end decay verification |

### 8.3 Sprint 3 Tests (~25+)

| File | Tests | Coverage |
|------|-------|----------|
| `test_vrf.py` | 5+ | Local determinism, purpose differentiation, range scaling, verify |
| `test_sepolia.py` | 5+ | Publish/verify round-trip, mock client, receipt validation |
| `test_contract.py` | 3+ | Solidity contract read/write (Hardhat) |
| `test_full_mode_templates.py` | 4 | Four quant templates in FULL mode |
| `test_status.py` | 3+ | Snapshot assembly, MCP integration |
| `test_e2e_engines.py` | 5+ | Full lifecycle with all engines active |

---

## 9. File Manifest

### Sprint 1 (New Files)

| File | Lines (est.) | Purpose |
|------|-------------|---------|
| `backend/engines/__init__.py` | 30 | Package exports |
| `backend/engines/heartbeat.py` | 80 | Heartbeat scheduler |
| `backend/engines/butterfly.py` | 110 | Butterfly Engine |
| `backend/engines/entropy.py` | 50 | Entropy Engine |
| `backend/engines/config.py` | 80 | Engine configuration |
| `backend/engines/integration.py` | 100 | Wiring layer |
| `backend/engines/tests/__init__.py` | 1 | Test package |
| `backend/engines/tests/test_heartbeat.py` | 120 | Scheduler tests |
| `backend/engines/tests/test_butterfly.py` | 130 | Butterfly tests |
| `backend/engines/tests/test_entropy.py` | 80 | Entropy tests |
| `backend/engines/tests/test_integration.py` | 120 | Integration tests |

### Sprint 2 (New Files)

| File | Lines (est.) | Purpose |
|------|-------------|---------|
| `backend/engines/logic_gap.py` | 70 | Logic Gap calculator |
| `backend/engines/reality_signal.py` | 60 | Reality signal providers |
| `backend/engines/paradox.py` | 150 | Paradox Engine |
| `backend/engines/tests/test_logic_gap.py` | 100 | Logic Gap tests |
| `backend/engines/tests/test_paradox.py` | 120 | Paradox tests |
| `backend/engines/tests/test_circuit_breakers.py` | 110 | Circuit breaker tests |
| `backend/engines/tests/test_entropy_paradox.py` | 90 | Entropy←Paradox wiring tests |

### Sprint 3 (New Files)

| File | Lines (est.) | Purpose |
|------|-------------|---------|
| `backend/engines/vrf.py` | 70 | VRF provider |
| `backend/engines/status.py` | 50 | Market status snapshot |
| `backend/chain/__init__.py` | 10 | Chain package |
| `backend/chain/sepolia.py` | 100 | Base Sepolia client |
| `backend/chain/contracts/EchelonCommitment.sol` | 40 | Solidity contract |
| `backend/engines/tests/test_vrf.py` | 90 | VRF tests |
| `backend/engines/tests/test_full_mode_templates.py` | 120 | FULL mode templates |
| `backend/engines/tests/test_status.py` | 60 | Status tests |
| `backend/engines/tests/test_e2e_engines.py` | 150 | End-to-end lifecycle |
| `backend/chain/tests/__init__.py` | 1 | Test package |
| `backend/chain/tests/test_sepolia.py` | 80 | Chain tests |
| `backend/chain/tests/test_contract.py` | 60 | Contract tests |

---

## 10. Technical Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|-----------|
| `pytest-asyncio` compatibility with Python 3.9 | Sprint 1 blocked | Verify version compatibility before starting; fallback to manual event loop management |
| Base Sepolia unreachable during Sprint 3 | Testnet tests fail | `@pytest.mark.testnet` marker; Sprint 3 ships green on local mode alone |
| web3.py import overhead | All tests slow | Lazy import in `sepolia.py`; mock client for unit tests |
| Heartbeat timing jitter | False test failures | 10% tolerance in timing assertions; use `asyncio.sleep` with cancellation checks |
| 010a API changes (unlikely) | Integration breaks | 010a is archived and committed; no changes expected |
