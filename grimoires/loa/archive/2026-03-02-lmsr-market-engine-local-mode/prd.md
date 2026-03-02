# PRD: LMSR Market Engine (Local Mode)

**Cycle**: 010a
**Version**: 1.0
**Date**: 2026-03-02

---

## 1. Problem Statement

The Echelon prediction market platform requires an LMSR (Logarithmic Market Scoring Rule) cost-function market maker as its mathematical core. Every downstream component depends on this engine: the Butterfly Engine modifies market state, the Paradox Engine reads prices, agents execute trades, and on-chain settlement commits outcomes. The existing codebase contains a CPMM implementation (`backend/core/cpmm.py`) but the System Bible v13 (Section III) mandates LMSR — a fundamentally different market maker with different mathematical properties (always-on prices, bounded loss, belief-driven profit).

Cycle-010a implements the LMSR engine in **local mode** — direct function calls, no network, no concurrency. This isolation means the LMSR arithmetic can be proven correct before distributed systems complexity is layered on in Cycle-010b.

The four existing LMSR quant templates (`theatre/fixtures/echelon_quant_v0_2/`) become **live acceptance tests** — run against the real engine, not fixtures. If the engine passes all four templates via `echelon_verify`, the cost function is certified by the same verification infrastructure that certifies everything else.

> Sources: echelon_cycle_010a.md (Cycle Objective), Echelon System Bible v13 §III, reality/architecture.md (CPMM vs LMSR note)

---

## 2. Goals & Success Metrics

| Goal | Metric |
|------|--------|
| LMSR cost function produces mathematically correct values | `cost()`, `prices()`, `trade_cost()` match known test vectors |
| Price simplex invariant holds | `sum(prices) == 1.0` within 1e-9 tolerance for all tested states |
| Numerical stability at extreme values | No overflow for `x_i / b > 700` (log-sum-exp trick) |
| Market lifecycle enforces correct ordering | Invalid phase transitions raise `InvalidPhaseTransition` |
| Commitment hash is deterministic | Same parameters produce same SHA-256 hash via Echelon Canonical JSON v0 |
| No parameter mutation after COMMITTED | Attempts to modify committed parameters raise exceptions |
| b-sensitivity sweep validates price impact | Price impact decreases as `b` increases across `b = [10, 20, 40, 80, 160]` |
| All existing tests pass | 447+ pipeline tests + Cycle-009 MCP tests remain green |
| 20+ new Sprint 1 tests pass | LMSR invariants, lifecycle, commitment, numerical edge cases |

---

## 3. User & Stakeholder Context

**Primary**: The Echelon platform — the LMSR engine is foundational infrastructure consumed by every subsequent cycle.

**Downstream consumers** (010b+):
- **Butterfly Engine** — reads/modifies market state via wing flaps
- **Paradox Engine** — reads prices to compute logic gaps
- **Agent Architecture** — executes trades via `TradingEngine` (Sprint 2)
- **On-chain Settlement** — commits market outcomes to Base Sepolia (010b)
- **MCP Surface** — `echelon_status` market-state integration (010b)

**Constraint**: Sprint 1 only. Sprint 2 (trade execution, positions, resolution) is a separate cycle phase. No agents, no trading API, no positions in Sprint 1.

---

## 4. Functional Requirements

### 4.1 LMSR Core Module

**File**: `backend/market/lmsr.py`

Pure mathematical engine — all functions are stateless, no side effects, no I/O.

| Function | Specification |
|----------|---------------|
| `LMSREngine.cost(x, b)` | `C(x) = b * ln(∑ exp(xⱼ / b))` |
| `LMSREngine.prices(x, b)` | `p_i(x) = exp(x_i / b) / ∑ exp(xⱼ / b)` |
| `LMSREngine.trade_cost(x, delta, b)` | `C(x + Δ) - C(x)` |
| `LMSREngine.worst_case_loss(b, n)` | `b * ln(n)` |
| `LMSREngine.validate_prices(prices, tol)` | All in `[0,1]`, sum = 1.0 within tolerance |

**Numerical stability**: Use log-sum-exp trick — subtract `max(x / b)` before exponentiating. Prevents overflow for large `x_i / b` ratios.

**Invariants** (tested, not asserted at runtime for performance):
- `sum(prices(x, b)) == 1.0` (within floating-point tolerance)
- `all(0.0 <= p <= 1.0 for p in prices(x, b))`
- `trade_cost(x, [0]*n, b) == 0.0` (zero-delta costs nothing)
- `trade_cost(x, delta, b) == -trade_cost(x + delta, [-d for d in delta], b)` (reversibility, within 1e-9)
- `worst_case_loss(b, n) == b * ln(n)`

> Source: Echelon System Bible v13 §III, echelon_cycle_010a.md (Sprint 1, LMSR Core Module)

### 4.2 Market State

**File**: `backend/market/state.py`

Mutable state container for a single market instance.

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

**MarketPhase enum**: `CREATED`, `COMMITTED`, `TRADING`, `RESOLVING`, `SETTLED`

### 4.3 Market Lifecycle State Machine

**File**: `backend/market/lifecycle.py`

Forward-only transitions. No transition is reversible.

| From | To | Trigger | Preconditions |
|------|----|---------|---------------|
| CREATED | COMMITTED | `commit(params)` | All params provided; `b > 0`; `n_outcomes >= 2`; commitment hash computed |
| COMMITTED | TRADING | `open_trading()` | Commitment hash exists; no parameter changes after this point |
| TRADING | RESOLVING | `begin_resolution(oracle_result)` | Oracle result provided; trading halted |
| RESOLVING | SETTLED | `settle()` | All positions computed; payouts determined |

Invalid transitions raise `InvalidPhaseTransition`. Parameters are immutable after COMMITTED.

### 4.4 Commitment Hash

**File**: `backend/market/commitment.py`

Reuses existing `theatre/engine/canonical_json.py` (Echelon Canonical JSON v0) for deterministic serialisation.

Hash computed over: `b`, `n_outcomes`, `outcome_labels`, `fee_schedule`, `oracle_config`. Ordering is significant — `outcome_labels` committed in declared order (no sorting).

**010a oracle_config stub**: `{"type": "manual", "version": "v0"}` for all markets. Keeps commitment hash fully specified without oracle infrastructure. Real oracle configs activate in 010b+.

### 4.5 Fee Schedule

**File**: `backend/market/fees.py`

```python
@dataclass
class FeeSchedule:
    trade_fee_bps: int = 0       # basis points on trade cost (0 for v1)
    resolution_fee_bps: int = 0  # basis points on settlement payouts (0 for v1)
```

Fees committed at creation, cannot change. Default to zero for 010a. Schema reserved for 010b+.

> Source: echelon_cycle_010a.md (Sprint 1 tasks 1-4)

---

## 5. Technical & Non-Functional Requirements

- **Pure functions**: LMSR core has no side effects. Given same inputs, always returns same outputs.
- **No new external dependencies**: Uses Python stdlib only (math, hashlib, json, dataclasses, enum). Reuses existing `theatre/engine/canonical_json.py`.
- **Python 3.9+ compatibility**: Type hints use `list[float]` (PEP 585), `str | None` (PEP 604). Both require 3.10+; if repo needs 3.9, use `from __future__ import annotations`.
- **No database persistence**: All state in-memory for 010a.
- **No concurrency**: Synchronous function calls only. No async, no threading, no heartbeat.
- **Deterministic execution**: No randomness. All operations produce identical output for identical input.
- **Existing infrastructure reuse**: Canonical JSON from `theatre/engine/canonical_json.py`, commitment hash pattern from `theatre/engine/commitment.py`.

> Source: echelon_cycle_010a.md (Scope Exclusions), reality/architecture.md

---

## 6. Scope & Prioritisation

### In scope (Sprint 1)

- `LMSREngine` — pure cost function (cost, prices, trade_cost, worst_case_loss, validate_prices)
- `MarketState` dataclass + `MarketPhase` enum
- `FeeSchedule` dataclass
- Lifecycle state machine (CREATED → COMMITTED → TRADING → RESOLVING → SETTLED)
- Market commitment hash computation (reusing canonical JSON)
- `InvalidPhaseTransition` and market-specific exceptions
- LMSR invariant tests (20+)
- Lifecycle transition tests
- Numerical edge-case tests (overflow, extreme `b`, many outcomes)
- b-sensitivity sweep validation against fixture data

### Out of scope (010a entirely)

- Butterfly Engine (wing flaps, stability impact, founder's yield)
- Paradox Engine (logic gap scanning, paradox spawning, extraction)
- Entropy Engine (temporal decay, heartbeat scheduler)
- VRF (verifiable randomness injection)
- Base Sepolia deployment (on-chain commitment/settlement)
- Agent brain execution (LLM routing, autonomous decisions)
- Real-time price feeds (Polymarket/Kalshi sync)
- Database persistence (SQLite/PostgreSQL)
- WebSocket/SSE price streaming
- Fee collection (fields reserved, values zero)

### Deferred to Sprint 2 (same cycle, separate phase)

- Trade execution engine (`TradingEngine`)
- Agent position tracking (`PositionManager`)
- Resolution and settlement (`ResolutionEngine`, `SettlementReport`)
- Quant template live acceptance tests
- End-to-end lifecycle test

---

## 7. Risks & Dependencies

| Risk | Severity | Mitigation |
|------|----------|------------|
| Numerical overflow in `exp(x_i / b)` for large ratios | MEDIUM | Log-sum-exp trick; edge-case tests for `x/b > 700` |
| Floating-point accumulation errors | LOW | 1e-9 tolerance in invariant tests; reversibility tested |
| Commitment hash incompatibility with existing theatre hashes | LOW | Reuse exact same `canonical_json()` utility; different composite structure but same serialisation rules |
| Quant template fixture path mismatch | LOW | Context file references `fixtures/echelon_quant_v0_2/`; actual path is `theatre/fixtures/echelon_quant_v0_2/` — PRD uses correct path |
| Existing 447+ tests regression | LOW | All Sprint 1 code is in new `backend/market/` directory; no modifications to existing files |

### Dependencies

| Dependency | Status | Used By |
|------------|--------|---------|
| `theatre/engine/canonical_json.py` | Exists (Cycle-008) | Market commitment hash |
| `theatre/fixtures/echelon_quant_v0_2/` | Exists (4 template suites, 35 fixtures) | b-sensitivity validation (Sprint 1), quant acceptance tests (Sprint 2) |
| `mcp/tools/hash.py` (`echelon_hash`) | Exists (Cycle-009) | Commitment hash verification |
| `tools/echelon_verify.py` | Exists (Cycle-008) | Certificate verification (Sprint 2) |

---

## 8. Acceptance Criteria (Sprint 1)

1. `LMSREngine.cost()` produces correct values for known test vectors
2. `LMSREngine.prices()` always sums to 1.0 (within 1e-9 tolerance)
3. `LMSREngine.trade_cost()` matches `C(x+Δ) - C(x)` exactly
4. Zero-delta trade costs exactly 0.0
5. Worst-case loss = `b * ln(n)` for all tested `(b, n)` combinations
6. Log-sum-exp trick prevents overflow for `x_i / b > 700`
7. Market lifecycle transitions enforce correct ordering (CREATED → COMMITTED → TRADING → RESOLVING → SETTLED)
8. No parameter mutation permitted after COMMITTED phase
9. Commitment hash is deterministic (same params → same hash)
10. Commitment hash uses Echelon Canonical JSON v0 (via `theatre/engine/canonical_json.py`)
11. b-sensitivity sweep matches expected price impact curves (price impact decreases as `b` increases)
12. All existing pipeline tests pass (447+)
13. All Cycle-009 MCP tests pass
14. 20+ new Sprint 1 tests pass

---

## 9. File Architecture (Sprint 1)

```
backend/market/
├── __init__.py
├── lmsr.py               # Pure LMSR cost function (NEW)
├── state.py              # MarketState dataclass + MarketPhase enum (NEW)
├── lifecycle.py          # State machine transitions (NEW)
├── fees.py               # FeeSchedule (NEW)
├── commitment.py         # Market commitment hash computation (NEW)
├── exceptions.py         # Market-specific exceptions (NEW)
└── tests/
    ├── __init__.py
    ├── test_lmsr.py           # LMSR invariant tests (NEW)
    ├── test_lifecycle.py      # State machine transition tests (NEW)
    ├── test_commitment.py     # Commitment hash tests (NEW)
    └── test_numerical.py      # Overflow/precision edge cases (NEW)
```

---

## 10. Sprint 1 Task Breakdown

| # | Task | Description |
|---|------|-------------|
| 1 | LMSR core | `LMSREngine` with `cost()`, `prices()`, `trade_cost()`, `worst_case_loss()`, `validate_prices()`. Log-sum-exp trick. |
| 2 | Market state | `MarketState` dataclass, `MarketPhase` enum, `FeeSchedule` dataclass. |
| 3 | Lifecycle state machine | Transition functions with precondition validation. Invalid transitions raise exceptions. |
| 4 | Commitment hash | Canonical JSON serialisation of market params → SHA-256. Reuse `theatre/engine/canonical_json.py`. |
| 5 | LMSR invariant tests | Simplex, zero-delta, reversibility, worst-case loss, numerical stability at extreme values. |
| 6 | Lifecycle tests | Valid transitions, invalid transition rejection, parameter immutability after COMMITTED. |
| 7 | Numerical edge-case tests | Overflow protection (large x/b), precision at extreme b (b=1, b=100000), many outcomes (n=100). |
| 8 | b-sensitivity validation | Replay b-sensitivity fixture sweep against live engine. Verify price impact decreases as b increases. |

---

## 11. Dependency Chain

```
Cycle-008 (MCP v0.8.0, construct calibration)
  → Cycle-009 (MCP v1.0, HTTP transport, echelon_status + echelon_calibrate)
    → Cycle-010a Sprint 1 (LMSR core, market lifecycle, commitment hash)
      → Cycle-010a Sprint 2 (trade execution, positions, resolution, settlement, quant template certification)
        → Cycle-010b (Butterfly, Paradox, Entropy engines, heartbeat, Base Sepolia, VRF)
```

---

## 12. Key Spec References

| Document | Relevance |
|----------|-----------|
| Echelon System Bible v13 §III | Normative spec: cost function, price function, trade cost, properties, b parameter |
| Echelon System Bible v13 §VI | Market parameter commitment protocol, hash computation, lifecycle phases |
| Echelon Theatre Template Library Live v2 | Four LMSR quant templates: hygiene, perturbation, API fidelity, b-sensitivity |
| `theatre/engine/canonical_json.py` | Existing canonical JSON utility (reused for commitment hashes) |
| `theatre/engine/commitment.py` | Existing commitment protocol (pattern reference) |
