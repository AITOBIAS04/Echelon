# SDD: LMSR Market Engine (Local Mode) — Sprints 1 & 2

**Cycle**: 010a
**Version**: 2.0
**Date**: 2026-03-02
**PRD**: `grimoires/loa/prd.md`
**Sprint 1**: COMPLETED — LMSR core, lifecycle, commitment (63 tests)
**Sprint 2**: Trade execution, positions, resolution, settlement

---

## 1. Executive Summary

Sprint 1 delivers the LMSR mathematical core and market lifecycle state machine as a new `backend/market/` package. All code is new — zero modifications to existing files. The design prioritises:

- **Purity**: LMSR functions are stateless and deterministic
- **Correctness**: Test vectors from existing quant fixtures serve as ground truth
- **Isolation**: No imports from or into existing backend modules (clean dependency boundary)
- **Forward compatibility**: Data structures accommodate Sprint 2 (trading, positions, settlement) and 010b (engines, chain) without schema changes

---

## 2. System Architecture

### 2.1 Component Overview

```
backend/market/
├── lmsr.py          ← Pure math (stateless) [Sprint 1 ✓]
├── state.py         ← Data structures [Sprint 1 ✓]
├── lifecycle.py     ← State machine transitions [Sprint 1 ✓]
├── commitment.py    ← Market parameter commitment hash [Sprint 1 ✓]
├── fees.py          ← FeeSchedule re-export [Sprint 1 ✓]
├── exceptions.py    ← Market-specific exceptions [Sprint 1 ✓, Sprint 2 adds 3]
├── trading.py       ← Trade execution engine [Sprint 2]
├── positions.py     ← Agent position tracking [Sprint 2]
├── resolution.py    ← Resolution + settlement [Sprint 2]
└── tests/
    ├── test_lmsr.py             [Sprint 1 ✓]
    ├── test_lifecycle.py        [Sprint 1 ✓]
    ├── test_commitment.py       [Sprint 1 ✓]
    ├── test_numerical.py        [Sprint 1 ✓]
    ├── test_trading.py          [Sprint 2]
    ├── test_positions.py        [Sprint 2]
    ├── test_resolution.py       [Sprint 2]
    └── test_settlement_invariants.py  [Sprint 2]
```

### 2.2 Dependency Graph

```
                    ┌──────────────┐
                    │ canonical_json│  (theatre/engine/canonical_json.py — EXISTING)
                    └──────┬───────┘
                           │ import
                           ▼
exceptions.py ◄── state.py ◄── lifecycle.py
      ▲               ▲              ▲
      │               │              │
      │          fees.py        commitment.py
      │                              │
      │                         lmsr.py (NO imports from market/ — pure stdlib)
      │
      └── All test files import from above modules
```

**Key constraint**: `lmsr.py` has ZERO internal imports. It uses only `math` from stdlib. This makes the cost function independently testable and verifiable.

### 2.3 Integration Seams (Sprint 2 / 010b)

| Consumer | Seam | Sprint |
|----------|------|--------|
| `TradingEngine` | Calls `LMSREngine.trade_cost()`, mutates `MarketState.x` | Sprint 2 |
| `PositionManager` | Reads `MarketState.x`, `MarketState.phase` | Sprint 2 |
| `ResolutionEngine` | Calls `MarketLifecycle.begin_resolution()`, `.settle()` | Sprint 2 |
| Butterfly Engine | Reads/writes `MarketState.x` via wing flap handlers | 010b |
| Paradox Engine | Calls `LMSREngine.prices()` to compute logic gap | 010b |
| MCP `echelon_status` | Reads `MarketState` for market-level status | 010b |

---

## 3. Technology Stack

| Layer | Choice | Justification |
|-------|--------|---------------|
| Language | Python 3.12 | Matches existing backend |
| Type hints | `from __future__ import annotations` | PEP 604 union syntax (`str \| None`) backcompat |
| Data structures | `dataclasses` | Lightweight, no Pydantic dependency for math layer |
| Serialisation | `theatre/engine/canonical_json.py` | Existing RFC 8785 implementation, battle-tested |
| Hashing | `hashlib.sha256` | Stdlib, consistent with existing commitment protocol |
| Math | `math.exp`, `math.log`, `math.fsum` | Stdlib, `fsum` for compensated summation |
| Testing | `pytest` | Matches existing test infrastructure |
| Assertions | Floating-point tolerance `1e-9` | Standard for double-precision LMSR literature |

**No new external dependencies.** Everything is Python stdlib + one import from `theatre/engine/`.

---

## 4. Detailed Component Design

### 4.1 `lmsr.py` — Pure LMSR Cost Function

```python
"""Logarithmic Market Scoring Rule — pure cost-function market maker.

All functions are static and pure: no side effects, no state mutation, no I/O.
Uses log-sum-exp trick for numerical stability.
"""
from __future__ import annotations

import math


class LMSREngine:

    @staticmethod
    def cost(x: list[float], b: float) -> float:
        """C(x) = b * ln(sum_j exp(x_j / b))

        Uses log-sum-exp trick: C(x) = b * (m + ln(sum_j exp(x_j/b - m)))
        where m = max(x_j / b). Prevents overflow for large x_j/b.
        """

    @staticmethod
    def prices(x: list[float], b: float) -> list[float]:
        """p_i(x) = exp(x_i / b) / sum_j exp(x_j / b)

        Equivalent to softmax(x / b). Uses log-sum-exp for stability.
        Returns list of len(x) probabilities summing to 1.0.
        """

    @staticmethod
    def trade_cost(x: list[float], delta: list[float], b: float) -> float:
        """cost(delta | x) = C(x + delta) - C(x)

        The amount the trader pays (positive) or receives (negative).
        """

    @staticmethod
    def worst_case_loss(b: float, n_outcomes: int) -> float:
        """Maximum market maker loss = b * ln(n)."""

    @staticmethod
    def validate_prices(prices: list[float], tolerance: float = 1e-9) -> bool:
        """Verify: all prices in [0,1], sum = 1.0 within tolerance."""
```

**Log-sum-exp implementation detail**:

```python
# Inside cost():
scaled = [xi / b for xi in x]
m = max(scaled)
log_sum = m + math.log(math.fsum(math.exp(s - m) for s in scaled))
return b * log_sum
```

- `math.fsum` for compensated summation (reduces floating-point error vs `sum()`)
- `max` subtraction prevents `exp()` overflow — `exp(s - m)` is always <= 1.0
- Result is mathematically identical to the naive formula

**Verified test vectors** (from `b_sensitivity_fixtures_5.json`):

| b | n | x0 | delta | Expected cost | Expected mm_bound |
|---|---|----|-------|---------------|-------------------|
| 10 | 3 | [0,0,0] | [50,0,0] | 39.14773613053339 | 10.986122886681098 |
| 20 | 3 | [0,0,0] | [50,0,0] | 31.0679219144605 | 21.972245773362197 |
| 40 | 3 | [0,0,0] | [50,0,0] | 24.17513737540895 | 43.94449154672439 |
| 80 | 3 | [0,0,0] | [50,0,0] | 20.33510997242064 | 87.88898309344879 |
| 160 | 3 | [0,0,0] | [50,0,0] | 18.45787501327277 | 175.77796618689757 |

Additional test vector from hygiene fixtures:

| b | n | x0 | trade | Expected prices_after | Expected C_after |
|---|---|----|-------|-----------------------|------------------|
| 10 | 3 | [0,0,0] | +50 on outcome 0 | [0.9867, 0.0066, 0.0066] | 50.13385901721449 |

### 4.2 `state.py` — Market State & Enums

```python
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class MarketPhase(Enum):
    CREATED = "CREATED"
    COMMITTED = "COMMITTED"
    TRADING = "TRADING"
    RESOLVING = "RESOLVING"
    SETTLED = "SETTLED"


@dataclass
class FeeSchedule:
    trade_fee_bps: int = 0
    resolution_fee_bps: int = 0


@dataclass
class MarketState:
    market_id: str
    theatre_id: str
    b: float
    n_outcomes: int
    outcome_labels: list[str]
    x: list[float] = field(default_factory=list)
    phase: MarketPhase = MarketPhase.CREATED
    fee_schedule: FeeSchedule = field(default_factory=FeeSchedule)
    commitment_hash: str | None = None
    resolved_outcome: int | None = None
    created_at: str = ""
    committed_at: str | None = None
    trading_opened_at: str | None = None
    resolved_at: str | None = None
    settled_at: str | None = None
```

**Design decisions**:

- **`dataclass` not Pydantic**: The math layer should have zero dependencies beyond stdlib. Pydantic adds validation overhead inappropriate for a hot-path cost function consumer. Sprint 2's `TradingEngine` may wrap this in Pydantic for API boundaries.
- **`x` default**: Empty list. `MarketLifecycle.create_market()` factory initialises it to `[0.0] * n_outcomes`.
- **Timestamps as `str`**: ISO 8601 strings. No `datetime` import in the data structure — keeps serialisation trivial. Lifecycle functions set timestamps.
- **`FeeSchedule` separate dataclass**: Even though fees are zero in 010a, the schema must be in the commitment hash. Separate class allows Sprint 2 to add fee application logic without touching `MarketState`.

### 4.3 `lifecycle.py` — State Machine

```python
from __future__ import annotations

from datetime import datetime, timezone

from backend.market.state import MarketState, MarketPhase, FeeSchedule
from backend.market.commitment import MarketCommitment
from backend.market.exceptions import (
    InvalidPhaseTransition,
    InvalidMarketParameters,
    ParameterMutationAfterCommit,
)


class MarketLifecycle:

    @staticmethod
    def create_market(
        market_id: str,
        theatre_id: str,
        b: float,
        n_outcomes: int,
        outcome_labels: list[str],
        fee_schedule: FeeSchedule | None = None,
    ) -> MarketState:
        """Factory — creates a MarketState in CREATED phase.

        Validates: b > 0, n_outcomes >= 2, len(outcome_labels) == n_outcomes.
        Initialises x to [0.0] * n_outcomes.
        """

    @staticmethod
    def commit(market: MarketState) -> MarketState:
        """CREATED → COMMITTED. Computes and stores commitment hash.

        Preconditions: phase == CREATED, b > 0, n_outcomes >= 2.
        Side effects: sets commitment_hash, committed_at.
        Returns: mutated MarketState (same object).
        """

    @staticmethod
    def open_trading(market: MarketState) -> MarketState:
        """COMMITTED → TRADING.

        Preconditions: phase == COMMITTED, commitment_hash is not None.
        Side effects: sets trading_opened_at.
        """

    @staticmethod
    def begin_resolution(market: MarketState, winning_outcome: int) -> MarketState:
        """TRADING → RESOLVING.

        Preconditions: phase == TRADING, 0 <= winning_outcome < n_outcomes.
        Side effects: sets resolved_outcome, resolved_at.
        """

    @staticmethod
    def settle(market: MarketState) -> MarketState:
        """RESOLVING → SETTLED.

        Preconditions: phase == RESOLVING, resolved_outcome is not None.
        Side effects: sets settled_at.
        """
```

**Transition validation pattern**:

```python
@staticmethod
def commit(market: MarketState) -> MarketState:
    if market.phase != MarketPhase.CREATED:
        raise InvalidPhaseTransition(
            current=market.phase,
            target=MarketPhase.COMMITTED,
        )
    # Compute commitment hash
    market.commitment_hash = MarketCommitment.compute_hash(market)
    market.phase = MarketPhase.COMMITTED
    market.committed_at = datetime.now(timezone.utc).isoformat()
    return market
```

**Mutation protection**: After `commit()`, any attempt to modify `b`, `n_outcomes`, `outcome_labels`, or `fee_schedule` through lifecycle methods will raise `ParameterMutationAfterCommit`. Note: `dataclass` doesn't enforce immutability at the field level (no frozen=True, because `x` must remain mutable for trading). Immutability is enforced by the lifecycle API, not the data structure.

### 4.4 `commitment.py` — Market Commitment Hash

```python
from __future__ import annotations

import hashlib

from theatre.engine.canonical_json import canonical_json

from backend.market.state import MarketState

# 010a stub — no real oracle infrastructure
ORACLE_CONFIG_STUB = {"type": "manual", "version": "v0"}


class MarketCommitment:

    @staticmethod
    def compute_hash(market: MarketState) -> str:
        """SHA-256 over canonical JSON of committed market parameters.

        Composite object keys (sorted by canonical_json):
            b, fee_schedule, n_outcomes, oracle_config, outcome_labels
        """
        composite = {
            "b": market.b,
            "n_outcomes": market.n_outcomes,
            "outcome_labels": market.outcome_labels,
            "fee_schedule": {
                "trade_fee_bps": market.fee_schedule.trade_fee_bps,
                "resolution_fee_bps": market.fee_schedule.resolution_fee_bps,
            },
            "oracle_config": ORACLE_CONFIG_STUB,
        }
        canonical = canonical_json(composite)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    @staticmethod
    def verify_hash(market: MarketState) -> bool:
        """Recompute and compare against stored commitment_hash."""
        if market.commitment_hash is None:
            return False
        return MarketCommitment.compute_hash(market) == market.commitment_hash
```

**Design decisions**:

- **Reuses `theatre/engine/canonical_json.py`**: Same RFC 8785 implementation used by all existing commitment hashes. Ensures cross-module hash compatibility.
- **Different composite structure from theatre commitments**: Theatre commitments use `{dataset_hashes, template, version_pins}`. Market commitments use `{b, fee_schedule, n_outcomes, oracle_config, outcome_labels}`. Same serialisation rules, different payload. No conflict.
- **`outcome_labels` order preserved**: `canonical_json()` sorts dict keys but preserves array insertion order (per RFC 8785). The commitment hash is therefore sensitive to outcome label ordering — `["Yes", "No"]` produces a different hash than `["No", "Yes"]`. This is correct behaviour: outcome order is part of the market specification.
- **`ORACLE_CONFIG_STUB`**: Module-level constant. In 010b, this becomes a parameter sourced from oracle configuration.

### 4.5 `fees.py` — Fee Schedule

```python
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class FeeSchedule:
    """Committed fee structure. Immutable after market commitment.

    Both fields default to 0 for 010a. Schema reserved for 010b+.
    """
    trade_fee_bps: int = 0
    resolution_fee_bps: int = 0
```

**Note**: `FeeSchedule` is defined in `state.py` alongside `MarketState` to avoid circular imports. A separate `fees.py` file is unnecessary for Sprint 1 since there's no fee application logic. **Design change from PRD**: `FeeSchedule` lives in `state.py`, not a separate `fees.py`. The `fees.py` file is created but re-exports from `state.py` for forward compatibility.

### 4.6 `exceptions.py` — Market Exceptions

```python
from __future__ import annotations

from backend.market.state import MarketPhase


class MarketError(Exception):
    """Base exception for all market errors."""


class InvalidPhaseTransition(MarketError):
    def __init__(self, current: MarketPhase, target: MarketPhase):
        self.current = current
        self.target = target
        super().__init__(
            f"Invalid transition: {current.value} -> {target.value}"
        )


class InvalidMarketParameters(MarketError):
    """Raised when market creation parameters are invalid."""


class ParameterMutationAfterCommit(MarketError):
    """Raised when attempting to modify committed parameters."""
```

### 4.7 `trading.py` — Trade Execution Engine (Sprint 2)

```python
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from backend.market.exceptions import (
    InsufficientBalance,
    InsufficientShares,
    InvalidMarketParameters,
    TradingHalted,
)
from backend.market.lmsr import LMSREngine
from backend.market.state import MarketPhase, MarketState


@dataclass
class Trade:
    trade_id: str
    market_id: str
    agent_id: str
    outcome_index: int
    shares: float              # positive = buy, negative = sell
    cost: float                # computed by engine (not user-provided)
    pre_trade_prices: list[float]
    post_trade_prices: list[float]
    timestamp: str


class TradingEngine:

    def __init__(self, position_manager: PositionManager) -> None:
        self._position_manager = position_manager
        self._trade_counter = 0

    def execute_trade(
        self,
        market: MarketState,
        agent_id: str,
        outcome_index: int,
        shares: float,
    ) -> Trade:
        """Validate → compute cost → update x → update position → return Trade.

        Atomic: if any validation fails, no state is mutated.
        """

    def quote(
        self,
        market: MarketState,
        outcome_index: int,
        shares: float,
    ) -> float:
        """Pre-trade cost quote. Pure — does not execute."""
```

**Design decisions**:

- **`TradingEngine` is stateful** (holds `PositionManager` reference) unlike `LMSREngine` (stateless). This is intentional: trade execution requires cross-cutting state (positions, balances).
- **Atomic execution**: Build delta vector, compute cost, validate all preconditions, THEN mutate `market.x` and update position. Any failure before mutation leaves state unchanged.
- **`trade_counter`**: Simple incrementing ID. Format: `trd_{counter:06d}`. No UUID needed for local mode.
- **Sells return cash**: When `shares < 0`, `trade_cost()` returns negative (trader receives money). The balance check only applies to buys (positive cost).

**Validation order** (fail-fast):
1. Market phase == TRADING (else `TradingHalted`)
2. `outcome_index` in range (else `InvalidMarketParameters`)
3. `shares != 0` (else `InvalidMarketParameters`)
4. If sell: agent holds >= `abs(shares)` at outcome (else `InsufficientShares`)
5. If buy: agent balance covers cost (else `InsufficientBalance`)

### 4.8 `positions.py` — Agent Position Tracking (Sprint 2)

```python
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class AgentPosition:
    agent_id: str
    market_id: str
    shares: list[float]         # net shares per outcome
    net_cashflow: float = 0.0   # positive = money spent, negative = money received
    realised_pnl: float = 0.0
    trade_count: int = 0


class PositionManager:
    """In-memory position tracking. One PositionManager per market session."""

    def __init__(self, n_outcomes: int) -> None:
        self._n_outcomes = n_outcomes
        self._positions: dict[str, AgentPosition] = {}
        self._balances: dict[str, float] = {}

    def set_balance(self, agent_id: str, balance: float) -> None:
        """Set initial cash balance for an agent."""

    def get_balance(self, agent_id: str) -> float:
        """Current cash balance (initial - net_cashflow)."""

    def get_position(self, agent_id: str, market_id: str) -> AgentPosition:
        """Get or create position for agent in market."""

    def update_position(self, trade: Trade) -> AgentPosition:
        """Apply trade to position: update shares, cashflow, trade count."""

    def compute_settlement_payout(
        self, position: AgentPosition, resolved_outcome: int
    ) -> float:
        """Winning shares pay 1:1. Losing shares pay 0."""

    def all_positions(self) -> list[AgentPosition]:
        """All positions for iteration during settlement."""
```

**Design decisions**:

- **In-memory dict**: `{agent_id: AgentPosition}`. No database for 010a. Key is `agent_id` since each `PositionManager` serves one market.
- **Balance tracking**: `set_balance()` at session start, decremented by buy costs, incremented by sell proceeds. `get_balance() = initial_balance - net_cashflow`.
- **Settlement payout**: `shares[resolved_outcome] * 1.0`. Simple 1:1 binary outcome. No partial payouts, no fees.
- **`n_outcomes` stored**: Needed to initialize zero-filled shares vectors for new agents.

### 4.9 `resolution.py` — Resolution & Settlement (Sprint 2)

```python
from __future__ import annotations

import hashlib
from dataclasses import dataclass

from theatre.engine.canonical_json import canonical_json

from backend.market.lmsr import LMSREngine
from backend.market.positions import PositionManager


@dataclass
class AgentSettlement:
    agent_id: str
    shares_held: list[float]
    winning_shares: float
    payout: float
    net_cashflow: float
    realised_pnl: float


@dataclass
class SettlementReport:
    market_id: str
    winning_outcome: int
    winning_label: str
    total_payout: float
    market_maker_pnl: float
    agent_settlements: list[AgentSettlement]
    commitment_hash: str
    settlement_hash: str


class ResolutionEngine:

    @staticmethod
    def settle(
        market: MarketState,
        position_manager: PositionManager,
    ) -> SettlementReport:
        """Compute all payouts. Transition to SETTLED. Return report with deterministic hash."""
```

**Design decisions**:

- **No separate `resolve()` method**: `MarketLifecycle.begin_resolution()` already handles TRADING → RESOLVING transition (Sprint 1). `ResolutionEngine.settle()` handles RESOLVING → SETTLED + payout computation. This avoids duplicating lifecycle logic.
- **Settlement hash**: SHA-256 over canonical JSON of `{market_id, winning_outcome, agent_settlements}`. Uses same `canonical_json()` as commitment hash.
- **`market_maker_pnl`**: `sum(all agent net_cashflow) - total_payout`. Positive means market maker profited; negative means loss. Bounded by `-worst_case_loss(b, n)`.

---

## 5. Data Architecture

### 5.1 In-Memory Only (010a)

No database. All state lives in Python objects for the duration of a test or script execution. This is deliberate — the LMSR engine must be provably correct before persistence is layered on.

### 5.2 Serialisation Format (for fixtures and debugging)

Market state serialises to JSON via `dataclasses.asdict()` → `canonical_json()`. This enables:
- Deterministic snapshot hashing
- Fixture comparison in tests
- Forward compatibility with the quant template evidence bundle format

### 5.3 Fixture Data Reference

| Suite | Path | Records | Format |
|-------|------|---------|--------|
| b-sensitivity | `theatre/fixtures/echelon_quant_v0_2/b_sensitivity_suite_v0_1/b_sensitivity_fixtures_5.json` | 5 | `{inputs: {b, trade: {x0, delta, j}}, expected_outputs: {execution: {cost_paid, impact, mm_bound}}}` |
| Hygiene | `theatre/fixtures/echelon_quant_v0_2/quant_market_hygiene_v0_1/quant_market_hygiene_fixtures_10.json` | 10 | `{inputs: {market_spec, state_before, trade}, expected_outputs: {state_after, execution}}` |
| Perturbation | `theatre/fixtures/echelon_quant_v0_2/perturbation_suite_v0_1/perturbation_fixtures_10.json` | 10 | VRF/saboteur/paradox scenarios |
| API fidelity | `theatre/fixtures/echelon_quant_v0_2/api_fidelity_suite_v0_1/api_fidelity_fixtures_10.json` | 10 | API surface validation |

Sprint 1 uses b-sensitivity and hygiene fixtures for test vectors. Perturbation and API fidelity fixtures reference VRF/heartbeat concepts that are 010b scope — Sprint 1 tests against these will use LOCAL MODE stubs (criteria pass by default).

---

## 6. API Design

### 6.1 No External API (Sprint 1)

Sprint 1 exposes no HTTP endpoints, no CLI commands, no MCP tools. The API is Python function calls only. External API surfaces are Sprint 2 (trading) and 010b (MCP integration).

### 6.2 Internal Python API

```python
# === LMSR Engine (pure math) ===
LMSREngine.cost(x=[0.0, 0.0, 0.0], b=10.0) -> float
LMSREngine.prices(x=[50.0, 0.0, 0.0], b=10.0) -> list[float]
LMSREngine.trade_cost(x=[0.0, 0.0, 0.0], delta=[50.0, 0.0, 0.0], b=10.0) -> float
LMSREngine.worst_case_loss(b=10.0, n_outcomes=3) -> float
LMSREngine.validate_prices(prices=[0.987, 0.007, 0.007]) -> bool

# === Market Lifecycle ===
market = MarketLifecycle.create_market(
    market_id="mkt_001",
    theatre_id="theatre_001",
    b=100.0,
    n_outcomes=3,
    outcome_labels=["Yes", "No", "Maybe"],
)
MarketLifecycle.commit(market)       # CREATED → COMMITTED
MarketLifecycle.open_trading(market)  # COMMITTED → TRADING
MarketLifecycle.begin_resolution(market, winning_outcome=0)  # TRADING → RESOLVING
MarketLifecycle.settle(market)       # RESOLVING → SETTLED

# === Commitment Hash ===
MarketCommitment.compute_hash(market) -> str  # SHA-256 hex
MarketCommitment.verify_hash(market) -> bool
```

---

## 7. Security Architecture

### 7.1 Scope

Sprint 1 is pure computation — no network, no auth, no user input, no file writes. Security concerns are limited to:

| Concern | Mitigation |
|---------|------------|
| Numerical overflow (DoS vector in production) | Log-sum-exp trick; tested for `x/b > 700` |
| Hash collision on commitment | SHA-256 — 128-bit collision resistance, sufficient |
| Parameter tampering after commit | Lifecycle API enforces immutability; `verify_hash()` for audit |
| Floating-point manipulation | `math.fsum` for compensated summation; 1e-9 tolerance |

### 7.2 Forward Security Notes (010b)

When HTTP/MCP surfaces expose market operations, the following will need attention:
- Input validation on `b`, `n_outcomes`, `outcome_labels` (prevent absurd values)
- Rate limiting on trade execution
- Authentication for market creation and resolution
- Audit logging for all state transitions

These are NOT implemented in Sprint 1.

---

## 8. Integration Points

### 8.1 Existing Code Dependencies

| Module | File | Usage |
|--------|------|-------|
| Canonical JSON | `theatre/engine/canonical_json.py` | Imported by `commitment.py` for deterministic serialisation |

**No other imports from existing codebase.** The market package is self-contained.

### 8.2 Import Path

The import path `from backend.market.lmsr import LMSREngine` assumes the repo root is on `PYTHONPATH` (or pytest is run from repo root with `conftest.py` handling path setup). This is consistent with existing backend module imports (e.g., `from theatre.engine.canonical_json import canonical_json`).

### 8.3 Fixture Integration

Tests read fixture JSON files from `theatre/fixtures/echelon_quant_v0_2/`. Path resolution uses `pathlib.Path(__file__).resolve().parents[N]` to find the repo root, consistent with existing test patterns in `tests/theatre/`.

---

## 9. Test Strategy

### 9.1 Test File Organisation

| File | Tests | Focus |
|------|-------|-------|
| `test_lmsr.py` | ~10 | LMSR invariants: simplex, zero-delta, reversibility, worst-case loss, test vector matching |
| `test_lifecycle.py` | ~6 | Valid transitions, invalid transition rejection, parameter immutability, factory validation |
| `test_commitment.py` | ~4 | Determinism, canonical JSON compatibility, verify_hash round-trip, oracle stub |
| `test_numerical.py` | ~5 | Overflow at x/b > 700, extreme b values (1, 100000), many outcomes (n=100), precision |

**Total: ~25 tests** (exceeding the 20+ minimum).

### 9.2 Key Test Cases

**LMSR Invariant Tests** (`test_lmsr.py`):

```python
def test_prices_sum_to_one():
    """sum(prices(x, b)) == 1.0 within tolerance for various x, b."""

def test_zero_delta_costs_zero():
    """trade_cost(x, [0]*n, b) == 0.0 exactly."""

def test_trade_cost_reversibility():
    """trade_cost(x, d, b) == -trade_cost(x+d, -d, b) within 1e-9."""

def test_worst_case_loss_formula():
    """worst_case_loss(b, n) == b * ln(n) for various (b, n)."""

def test_b_sensitivity_fixture_vectors():
    """Match all 5 b-sensitivity fixture cost_paid values exactly."""

def test_hygiene_fixture_state_after():
    """Match hygiene qmhy_0001 state_after prices and C exactly."""

def test_prices_all_in_unit_interval():
    """all(0.0 <= p <= 1.0 for p in prices(x, b))."""

def test_initial_prices_uniform():
    """prices([0]*n, b) == [1/n]*n for any b, n."""

def test_validate_prices_valid():
    """validate_prices([0.5, 0.3, 0.2]) == True."""

def test_validate_prices_invalid_sum():
    """validate_prices([0.5, 0.5, 0.5]) == False."""
```

**Lifecycle Tests** (`test_lifecycle.py`):

```python
def test_valid_transition_sequence():
    """CREATED → COMMITTED → TRADING → RESOLVING → SETTLED succeeds."""

def test_skip_committed_raises():
    """CREATED → TRADING raises InvalidPhaseTransition."""

def test_backward_transition_raises():
    """TRADING → COMMITTED raises InvalidPhaseTransition."""

def test_commit_sets_hash():
    """After commit(), commitment_hash is non-None SHA-256 hex string."""

def test_parameter_immutability():
    """After COMMITTED, create_market params cannot be changed via lifecycle."""

def test_create_market_validates_params():
    """b <= 0, n_outcomes < 2, wrong label count all raise InvalidMarketParameters."""
```

**Commitment Tests** (`test_commitment.py`):

```python
def test_hash_determinism():
    """Same params produce identical hash across calls."""

def test_hash_differs_on_label_order():
    """["Yes","No"] vs ["No","Yes"] produce different hashes."""

def test_verify_hash_roundtrip():
    """compute_hash → store → verify_hash returns True."""

def test_canonical_json_compatibility():
    """canonical_json output matches expected format (no whitespace, sorted keys)."""
```

**Numerical Tests** (`test_numerical.py`):

```python
def test_no_overflow_large_x_over_b():
    """cost([1000.0, 0.0], b=1.0) computes without OverflowError."""

def test_extreme_b_small():
    """b=0.001, x=[0,0] computes correctly."""

def test_extreme_b_large():
    """b=100000, x=[0,0,0,0,0] computes correctly."""

def test_many_outcomes():
    """n=100 outcomes: prices still sum to 1.0, cost computes."""

def test_fsum_precision():
    """Compensated summation gives better precision than naive sum()."""
```

### 9.3 Test Execution

```bash
# Sprint 1 tests only
python3 -m pytest backend/market/tests/ -v

# Verify no regression on existing tests
python3 -m pytest -q --ignore=backend/market/
```

---

## 10. Performance Considerations

### 10.1 Computational Complexity

| Function | Complexity | Notes |
|----------|-----------|-------|
| `cost()` | O(n) | Single pass over n outcomes |
| `prices()` | O(n) | Single pass + normalisation |
| `trade_cost()` | O(n) | Two `cost()` calls |
| `commit()` | O(n) | JSON serialisation + SHA-256 |

For typical markets (n <= 10), all operations complete in microseconds. Even n=100 is sub-millisecond.

### 10.2 No Optimisation Needed (Sprint 1)

The LMSR engine will not be in a hot loop in Sprint 1 (no trading, no heartbeat). Performance optimisation is deferred to 010b when the heartbeat scheduler drives trade execution at 5-second intervals.

---

## 11. Deployment Architecture

### 11.1 No Deployment (Sprint 1)

Sprint 1 is library code tested locally. No servers, no containers, no CI/CD changes.

### 11.2 File Layout

All new files in `backend/market/`. The `backend/` directory already exists. Only new subdirectory creation needed:

```bash
mkdir -p backend/market/tests
```

---

## 12. Development Workflow

### 12.1 Implementation Order

| Step | Files | Dependencies |
|------|-------|-------------|
| 1 | `exceptions.py` | None |
| 2 | `state.py` (`MarketPhase`, `FeeSchedule`, `MarketState`) | `exceptions.py` (for type refs in lifecycle) |
| 3 | `lmsr.py` (`LMSREngine`) | None (pure stdlib) |
| 4 | `commitment.py` (`MarketCommitment`) | `state.py`, `theatre/engine/canonical_json.py` |
| 5 | `lifecycle.py` (`MarketLifecycle`) | `state.py`, `commitment.py`, `exceptions.py` |
| 6 | `fees.py` (re-export) | `state.py` |
| 7 | `__init__.py` (public API exports) | All above |
| 8 | `tests/test_lmsr.py` | `lmsr.py` |
| 9 | `tests/test_commitment.py` | `commitment.py` |
| 10 | `tests/test_lifecycle.py` | `lifecycle.py` |
| 11 | `tests/test_numerical.py` | `lmsr.py` |

Steps 1-3 can be parallelised (no interdependencies). Steps 8-11 can be parallelised.

### 12.2 Git Strategy

Single feature branch: `feature/cycle-010a-lmsr-sprint-1`. Merge to `main` after `/audit-sprint` approval.

---

## 13. Technical Risks & Mitigation

| Risk | Severity | Mitigation | Verification |
|------|----------|------------|-------------|
| Log-sum-exp doesn't handle all edge cases | MEDIUM | Test x/b ratios from 0.001 to 1000+ | `test_numerical.py` |
| `canonical_json` import path breaks | LOW | Integration test importing from `theatre/engine/` | `test_commitment.py` |
| Fixture values computed with different LMSR implementation | LOW | Verify first fixture manually: b=10, n=3, x0=[0,0,0], delta=[50,0,0] → cost = C([50,0,0],10) - C([0,0,0],10) = 10*(ln(e^5 + 2)) - 10*ln(3) | `test_lmsr.py::test_b_sensitivity_fixture_vectors` |
| `MarketState` dataclass mutability | LOW | Lifecycle API is the only sanctioned mutation path; tests verify direct field mutation is caught | `test_lifecycle.py` |

### 13.1 Manual Verification of First Test Vector

For `bscan_0001`: b=10, n=3, x0=[0,0,0], buy 50 shares of outcome 0.

```
C([0,0,0], 10) = 10 * ln(exp(0) + exp(0) + exp(0)) = 10 * ln(3) = 10.986122886681098
C([50,0,0], 10) = 10 * ln(exp(5) + exp(0) + exp(0)) = 10 * ln(e^5 + 2) = 10 * ln(150.4131591025766) = 50.13385901721449
trade_cost = 50.1339 - 10.9861 = 39.14773613053339 ✓
mm_bound = 10 * ln(3) = 10.986122886681098 ✓
```

---

## 14. Future Considerations

### 14.1 Sprint 2 Additions (Same Cycle)

| File | Purpose |
|------|---------|
| `trading.py` | `TradingEngine.execute_trade()`, `quote()` |
| `positions.py` | `PositionManager`, `AgentPosition` |
| `resolution.py` | `ResolutionEngine`, `SettlementReport`, `AgentSettlement` |
| `tests/test_trading.py` | Trade execution tests |
| `tests/test_positions.py` | Position tracking tests |
| `tests/test_resolution.py` | Resolution/settlement tests |
| `tests/test_settlement_invariants.py` | Bounded loss, payout conservation |
| `tests/test_quant_acceptance.py` | Live engine vs 4 quant templates |

### 14.2 010b Additions

- Butterfly Engine integration (wing flap → MarketState.x modification)
- Paradox Engine integration (prices → logic gap computation)
- Heartbeat scheduler driving periodic price reads
- Base Sepolia: commitment hash on-chain, settlement proof on-chain
- VRF seed injection for perturbation harness
- `echelon_status` MCP tool reads market state

### 14.3 Technical Debt Tracking

| Item | Created | Resolution |
|------|---------|------------|
| `FeeSchedule` in `state.py` not separate `fees.py` | Sprint 1 | Move to `fees.py` if fee application logic grows in Sprint 2 |
| `ORACLE_CONFIG_STUB` hardcoded | Sprint 1 | Replace with oracle config parameter in 010b |
| No `frozen=True` on `MarketState` | Sprint 1 | Evaluate if needed when multiple consumers exist in 010b |
| `dataclass` not Pydantic | Sprint 1 | Add Pydantic wrapper at API boundary in Sprint 2 if needed |
