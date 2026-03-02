# Sprint Plan: LMSR Market Engine (Local Mode)

**Cycle**: 010a
**Sprint**: 1 (global: 16)
**Label**: LMSR Core + Market Lifecycle
**Date**: 2026-03-02
**PRD**: `grimoires/loa/prd.md`
**SDD**: `grimoires/loa/sdd.md`

---

## Sprint Overview

**Goal**: Deliver the pure LMSR mathematical engine and market lifecycle state machine as `backend/market/`. All code is new — zero modifications to existing files.

**Deliverables**: 6 source files + 4 test files + 2 `__init__.py` = 12 files total

**Test target**: 25+ new tests, all existing 447+ tests unbroken

**Branch**: `feature/cycle-010a-lmsr-sprint-1`

---

## Tasks

### Task 1: Package scaffold + exceptions

**File**: `backend/market/__init__.py`, `backend/market/exceptions.py`, `backend/market/tests/__init__.py`

**Description**: Create the `backend/market/` package directory structure and implement the market-specific exception hierarchy.

**Implementation**:
- `mkdir -p backend/market/tests`
- `exceptions.py`: `MarketError` (base), `InvalidPhaseTransition(current, target)`, `InvalidMarketParameters`, `ParameterMutationAfterCommit`
- `__init__.py`: Empty initially (populated in Task 8)
- `tests/__init__.py`: Empty

**Acceptance criteria**:
- [ ] `backend/market/` directory exists with `__init__.py`
- [ ] `backend/market/tests/` directory exists with `__init__.py`
- [ ] All four exception classes importable from `backend.market.exceptions`
- [ ] `InvalidPhaseTransition` stores `current` and `target` attributes
- [ ] All exceptions inherit from `MarketError`

**Dependencies**: None

---

### Task 2: Market state data structures

**File**: `backend/market/state.py`, `backend/market/fees.py`

**Description**: Implement `MarketPhase` enum, `FeeSchedule` dataclass, and `MarketState` dataclass. `FeeSchedule` is defined in `state.py`; `fees.py` re-exports for forward compatibility.

**Implementation** (per SDD §4.2):
- `MarketPhase`: Enum with `CREATED`, `COMMITTED`, `TRADING`, `RESOLVING`, `SETTLED`
- `FeeSchedule`: `trade_fee_bps: int = 0`, `resolution_fee_bps: int = 0`
- `MarketState`: 14 fields per SDD, `x` defaults to empty list, `phase` defaults to `CREATED`
- `fees.py`: `from backend.market.state import FeeSchedule`
- Use `from __future__ import annotations` for PEP 604 backcompat

**Acceptance criteria**:
- [ ] `MarketPhase` has exactly 5 members in correct order
- [ ] `FeeSchedule` defaults both fields to 0
- [ ] `MarketState` has all 14 fields per SDD
- [ ] `MarketState.x` defaults to empty list (factory)
- [ ] `MarketState.phase` defaults to `CREATED`
- [ ] `from backend.market.fees import FeeSchedule` works (re-export)

**Dependencies**: Task 1 (package exists)

---

### Task 3: LMSR core engine

**File**: `backend/market/lmsr.py`

**Description**: Pure LMSR cost-function market maker. Five static methods, zero internal imports, uses only `math` from stdlib. Log-sum-exp trick for numerical stability.

**Implementation** (per SDD §4.1):
- `LMSREngine.cost(x, b)`: `b * (m + ln(fsum(exp(s - m) for s in scaled)))` where `m = max(scaled)`, `scaled = [xi/b for xi in x]`
- `LMSREngine.prices(x, b)`: Softmax with log-sum-exp. Use `fsum` for normalisation.
- `LMSREngine.trade_cost(x, delta, b)`: `cost(x_new, b) - cost(x, b)` where `x_new = [xi + di for xi, di in zip(x, delta)]`
- `LMSREngine.worst_case_loss(b, n)`: `b * math.log(n)`
- `LMSREngine.validate_prices(prices, tol)`: Check all in [0,1] and sum within tolerance of 1.0

**Test vectors** (verify during implementation):
- `cost([0,0,0], 10) = 10.986122886681098` (= 10 * ln(3))
- `trade_cost([0,0,0], [50,0,0], 10) = 39.14773613053339`
- `prices([50,0,0], 10) ≈ [0.9867, 0.0066, 0.0066]`
- `worst_case_loss(10, 3) = 10.986122886681098`

**Acceptance criteria**:
- [ ] All 5 static methods implemented
- [ ] Zero imports from `backend.market` (only `import math`)
- [ ] `from __future__ import annotations` for type hint backcompat
- [ ] Log-sum-exp trick used in `cost()` and `prices()`
- [ ] `math.fsum` used for compensated summation
- [ ] Manual test vector for b=10 matches fixture value

**Dependencies**: None (can be parallelised with Tasks 1-2)

---

### Task 4: Commitment hash

**File**: `backend/market/commitment.py`

**Description**: Market parameter commitment hash using existing `theatre/engine/canonical_json.py`. SHA-256 over canonical JSON of composite: `{b, fee_schedule, n_outcomes, oracle_config, outcome_labels}`.

**Implementation** (per SDD §4.4):
- `ORACLE_CONFIG_STUB = {"type": "manual", "version": "v0"}` module-level constant
- `MarketCommitment.compute_hash(market)`: Build composite dict → `canonical_json()` → `sha256().hexdigest()`
- `MarketCommitment.verify_hash(market)`: Recompute and compare
- Composite dict keys: `b`, `n_outcomes`, `outcome_labels`, `fee_schedule` (as dict), `oracle_config`
- `canonical_json()` sorts keys lexicographically; arrays preserve insertion order

**Acceptance criteria**:
- [ ] Imports `canonical_json` from `theatre.engine.canonical_json`
- [ ] `compute_hash()` returns 64-char hex string (SHA-256)
- [ ] `verify_hash()` returns True after `compute_hash()` stores result
- [ ] Same params produce identical hash across calls
- [ ] `["Yes","No"]` vs `["No","Yes"]` produce different hashes
- [ ] `ORACLE_CONFIG_STUB` is `{"type": "manual", "version": "v0"}`

**Dependencies**: Task 2 (MarketState), `theatre/engine/canonical_json.py` (exists)

---

### Task 5: Lifecycle state machine

**File**: `backend/market/lifecycle.py`

**Description**: Forward-only state machine with 5 transition methods. Factory method for market creation with parameter validation.

**Implementation** (per SDD §4.3):
- `MarketLifecycle.create_market(...)`: Validate `b > 0`, `n_outcomes >= 2`, `len(labels) == n_outcomes`. Init `x = [0.0] * n_outcomes`. Set `created_at`.
- `commit(market)`: Check `phase == CREATED` → compute hash → set `COMMITTED`, `committed_at`
- `open_trading(market)`: Check `phase == COMMITTED`, hash exists → set `TRADING`, `trading_opened_at`
- `begin_resolution(market, winning_outcome)`: Check `phase == TRADING`, valid outcome index → set `RESOLVING`, `resolved_outcome`, `resolved_at`
- `settle(market)`: Check `phase == RESOLVING`, `resolved_outcome` set → set `SETTLED`, `settled_at`
- All invalid transitions raise `InvalidPhaseTransition(current, target)`
- Timestamps via `datetime.now(timezone.utc).isoformat()`

**Acceptance criteria**:
- [ ] Full forward path works: CREATED → COMMITTED → TRADING → RESOLVING → SETTLED
- [ ] CREATED → TRADING raises `InvalidPhaseTransition`
- [ ] TRADING → COMMITTED raises `InvalidPhaseTransition`
- [ ] `create_market(b=0, ...)` raises `InvalidMarketParameters`
- [ ] `create_market(n_outcomes=1, ...)` raises `InvalidMarketParameters`
- [ ] `create_market(labels=["A"], n_outcomes=2)` raises `InvalidMarketParameters` (mismatch)
- [ ] `commit()` sets `commitment_hash` (non-None, 64-char hex)
- [ ] `commit()` sets `committed_at` (ISO 8601 string)
- [ ] `begin_resolution(market, -1)` raises (invalid outcome index)
- [ ] `begin_resolution(market, n_outcomes)` raises (out of bounds)

**Dependencies**: Tasks 1, 2, 4 (exceptions, state, commitment)

---

### Task 6: LMSR invariant tests + fixture validation

**File**: `backend/market/tests/test_lmsr.py`

**Description**: Core invariant tests for the LMSR engine plus validation against existing b-sensitivity and hygiene fixture data.

**Tests** (~10):
1. `test_prices_sum_to_one` — Various x, b combinations
2. `test_prices_all_in_unit_interval` — All prices in [0, 1]
3. `test_initial_prices_uniform` — `prices([0]*n, b)` = `[1/n]*n`
4. `test_zero_delta_costs_zero` — `trade_cost(x, [0]*n, b)` = 0.0
5. `test_trade_cost_reversibility` — `trade_cost(x, d, b)` = `-trade_cost(x+d, -d, b)` within 1e-9
6. `test_worst_case_loss_formula` — `b * ln(n)` for multiple (b, n)
7. `test_b_sensitivity_fixture_vectors` — All 5 fixture `cost_paid` values match
8. `test_b_sensitivity_impact_monotonic` — Impact decreases as b increases
9. `test_hygiene_fixture_state_after` — qmhy_0001 prices and C match
10. `test_validate_prices_valid_and_invalid` — True for valid, False for invalid

**Fixture loading**: Read JSON from `theatre/fixtures/echelon_quant_v0_2/` using `pathlib.Path` relative to repo root.

**Acceptance criteria**:
- [ ] All 10 tests pass
- [ ] b-sensitivity test loads real fixture JSON (not hardcoded values)
- [ ] Hygiene test loads real fixture JSON
- [ ] Tolerance is 1e-9 for floating-point comparisons
- [ ] `validate_prices` tested for both True and False cases

**Dependencies**: Task 3 (lmsr.py)

---

### Task 7: Lifecycle + commitment tests

**File**: `backend/market/tests/test_lifecycle.py`, `backend/market/tests/test_commitment.py`

**Description**: State machine transition tests and commitment hash determinism tests.

**Lifecycle tests** (~6):
1. `test_valid_transition_sequence` — Full forward path succeeds
2. `test_skip_committed_raises` — CREATED → TRADING raises
3. `test_backward_transition_raises` — TRADING → COMMITTED raises
4. `test_commit_sets_hash` — Hash is 64-char hex after commit
5. `test_parameter_immutability` — No mutation via lifecycle after COMMITTED
6. `test_create_market_validates_params` — b <= 0, n < 2, label mismatch all raise

**Commitment tests** (~4):
1. `test_hash_determinism` — Same params, same hash
2. `test_hash_differs_on_label_order` — ["Yes","No"] != ["No","Yes"]
3. `test_verify_hash_roundtrip` — compute → store → verify = True
4. `test_canonical_json_compatibility` — Sorted keys, no whitespace

**Acceptance criteria**:
- [ ] All 10 tests pass
- [ ] Invalid transition tests verify exact exception type and attributes
- [ ] Commitment determinism tested with at least 2 calls
- [ ] Label order sensitivity tested

**Dependencies**: Tasks 4, 5 (commitment, lifecycle)

---

### Task 8: Numerical edge-case tests + package exports

**File**: `backend/market/tests/test_numerical.py`, `backend/market/__init__.py` (update)

**Description**: Overflow/precision tests and public API exports in `__init__.py`.

**Numerical tests** (~5):
1. `test_no_overflow_large_x_over_b` — `cost([1000.0, 0.0], b=1.0)` no OverflowError
2. `test_extreme_b_small` — `b=0.001, x=[0,0]` computes correctly
3. `test_extreme_b_large` — `b=100000, x=[0,0,0,0,0]` computes correctly, prices sum to 1.0
4. `test_many_outcomes` — `n=100` outcomes: prices sum to 1.0, cost computes
5. `test_fsum_precision` — Compensated summation precision at least as good as naive

**`__init__.py` exports**:
```python
from backend.market.lmsr import LMSREngine
from backend.market.state import MarketState, MarketPhase, FeeSchedule
from backend.market.lifecycle import MarketLifecycle
from backend.market.commitment import MarketCommitment
from backend.market.exceptions import (
    MarketError, InvalidPhaseTransition,
    InvalidMarketParameters, ParameterMutationAfterCommit,
)
```

**Acceptance criteria**:
- [ ] All 5 numerical tests pass
- [ ] `cost([1000.0, 0.0], b=1.0)` does not raise OverflowError
- [ ] n=100 prices sum to 1.0 within 1e-9
- [ ] `from backend.market import LMSREngine, MarketLifecycle, MarketCommitment` works
- [ ] All 25+ Sprint 1 tests pass: `python3 -m pytest backend/market/tests/ -v`
- [ ] All existing tests pass: `python3 -m pytest -q --ignore=backend/market/`

**Dependencies**: Tasks 3, 5, 6, 7 (all source + previous tests)

---

## Task Dependency Graph

```
Task 1 (scaffold) ──┬── Task 2 (state) ──┬── Task 4 (commitment) ──┬── Task 5 (lifecycle) ──┐
                     │                     │                         │                        │
Task 3 (lmsr) ──────┼─────────────────────┼─────────────────────────┤                        │
                     │                     │                         │                        │
                     │                     │                         ├── Task 7 (lifecycle +   │
                     │                     │                         │   commitment tests)     │
                     │                     │                         │                        │
                     ├── Task 6 (lmsr tests)                        │                        │
                     │                                               │                        │
                     └───────────────────────────────────────────────┴── Task 8 (numerical +  │
                                                                         exports)             │
```

**Parallelisation opportunities**:
- Tasks 1 + 3 can run in parallel (no interdependency)
- Tasks 6, 7, 8 tests can run in parallel (after their source deps)

---

## Implementation Order (Sequential)

| Order | Task | Why This Order |
|-------|------|----------------|
| 1 | Task 1: Scaffold + exceptions | Creates package structure everything else needs |
| 2 | Task 2: State data structures | MarketState needed by commitment and lifecycle |
| 3 | Task 3: LMSR core engine | Pure math, no internal deps, can verify immediately |
| 4 | Task 4: Commitment hash | Needs state.py + canonical_json |
| 5 | Task 5: Lifecycle state machine | Needs all above |
| 6 | Task 6: LMSR tests + fixtures | Validates core math against ground truth |
| 7 | Task 7: Lifecycle + commitment tests | Validates state machine and hash |
| 8 | Task 8: Numerical tests + exports | Final validation + public API |

---

## Success Criteria (Sprint 1)

From PRD §8:

- [x] `LMSREngine.cost()` produces correct values for known test vectors
- [x] `LMSREngine.prices()` always sums to 1.0 (within 1e-9)
- [x] `LMSREngine.trade_cost()` matches `C(x+Δ) - C(x)` exactly
- [x] Zero-delta trade costs exactly 0.0
- [x] Worst-case loss = `b * ln(n)` for all tested (b, n)
- [x] Log-sum-exp prevents overflow for `x_i / b > 700`
- [x] Lifecycle transitions enforce correct ordering
- [x] No parameter mutation after COMMITTED
- [x] Commitment hash is deterministic
- [x] Commitment hash uses Echelon Canonical JSON v0
- [x] b-sensitivity sweep matches expected price impact curves
- [x] All existing pipeline tests pass (447+)
- [x] All Cycle-009 MCP tests pass
- [x] 25+ new Sprint 1 tests pass

---

## Verification Commands

```bash
# Sprint 1 tests only
python3 -m pytest backend/market/tests/ -v

# Full regression (all existing tests)
python3 -m pytest -q --ignore=backend/market/

# Combined
python3 -m pytest -v
```
