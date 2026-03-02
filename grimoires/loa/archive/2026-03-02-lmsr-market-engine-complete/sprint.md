# Sprint Plan: LMSR Market Engine (Local Mode)

**Cycle**: 010a
**Sprint**: 2 (global: 17)
**Label**: Trade Execution + Positions + Settlement
**Date**: 2026-03-02
**PRD**: `grimoires/loa/prd.md` (v2.0)
**SDD**: `grimoires/loa/sdd.md` (v2.0)
**Depends on**: Sprint 1 (global: 16) — COMPLETED

---

## Sprint Overview

**Goal**: Deliver the transactional layer on top of the Sprint 1 LMSR core — trade execution, agent position tracking, resolution, and settlement. Agents can create markets, commit parameters, trade, and settle with deterministic P&L.

**Deliverables**: 3 source files + 4 test files + updates to `exceptions.py` and `__init__.py` = 9 files touched

**Test target**: 25+ new tests, all existing 63 Sprint 1 tests + pipeline tests unbroken

**Branch**: `feature/cycle-010a-lmsr-sprint-2`

---

## Tasks

### Task 1: New exceptions for trading layer

**Files**: `backend/market/exceptions.py` (modify)

**Description**: Add three new exception classes needed by the trading and position layers.

**Implementation**:
- `TradingHalted(MarketError)` — raised when trade attempted outside TRADING phase. Stores `current_phase`.
- `InsufficientBalance(MarketError)` — raised when agent can't cover trade cost. Stores `required`, `available`.
- `InsufficientShares(MarketError)` — raised when sell exceeds held shares. Stores `outcome_index`, `required`, `available`.

**Acceptance criteria**:
- [ ] All three exceptions importable from `backend.market.exceptions`
- [ ] All inherit from `MarketError`
- [ ] `TradingHalted` stores `current_phase` attribute
- [ ] `InsufficientBalance` stores `required` and `available` attributes
- [ ] `InsufficientShares` stores `outcome_index`, `required`, `available` attributes
- [ ] Existing Sprint 1 tests still pass (no regressions from exception changes)

**Dependencies**: None

---

### Task 2: Agent position tracking

**File**: `backend/market/positions.py`

**Description**: In-memory position manager tracking shares, cashflow, and P&L per agent per market. Each `PositionManager` serves a single market.

**Implementation** (per SDD §4.8):
- `AgentPosition` dataclass: `agent_id`, `market_id`, `shares` (list[float]), `net_cashflow`, `realised_pnl`, `trade_count`
- `PositionManager.__init__(n_outcomes, market_id)`: Stores outcome count, initialises empty position and balance dicts
- `set_balance(agent_id, balance)`: Set initial cash balance
- `get_balance(agent_id)`: Returns `initial_balance - net_cashflow` (current available cash)
- `get_position(agent_id)`: Returns existing or creates zero-filled position
- `update_position(trade)`: Adds `trade.shares` to `position.shares[trade.outcome_index]`, adds `trade.cost` to `net_cashflow`, increments `trade_count`
- `compute_settlement_payout(position, resolved_outcome)`: Returns `position.shares[resolved_outcome]` (winning shares pay 1:1; min 0.0)
- `all_positions()`: Returns list of all AgentPosition objects

**Acceptance criteria**:
- [ ] `AgentPosition` has all 6 fields with correct defaults
- [ ] `get_position()` creates zero-filled position for unknown agent
- [ ] `update_position()` correctly modifies shares, cashflow, trade_count
- [ ] `get_balance()` = initial balance - net_cashflow
- [ ] `compute_settlement_payout()` returns winning shares (min 0.0)
- [ ] `all_positions()` returns all tracked positions

**Dependencies**: Task 1 (exceptions)

---

### Task 3: Trade execution engine

**File**: `backend/market/trading.py`

**Description**: Validates and executes trades atomically against LMSR markets. Mutates `MarketState.x` and updates positions via `PositionManager`.

**Implementation** (per SDD §4.7):
- `Trade` dataclass: `trade_id`, `market_id`, `agent_id`, `outcome_index`, `shares`, `cost`, `pre_trade_prices`, `post_trade_prices`, `timestamp`
- `TradingEngine.__init__(position_manager)`: Stores reference, initialises trade counter
- `execute_trade(market, agent_id, outcome_index, shares) -> Trade`:
  1. Validate market phase == TRADING (else `TradingHalted`)
  2. Validate outcome_index in range (else `InvalidMarketParameters`)
  3. Validate shares != 0 (else `InvalidMarketParameters`)
  4. Build one-hot delta: `delta[outcome_index] = shares`
  5. Compute cost via `LMSREngine.trade_cost(market.x, delta, market.b)`
  6. If buy (cost > 0): check `position_manager.get_balance(agent_id) >= cost` (else `InsufficientBalance`)
  7. If sell (shares < 0): check agent holds `abs(shares)` at outcome (else `InsufficientShares`)
  8. Capture `pre_trade_prices`
  9. Mutate `market.x` (add delta)
  10. Capture `post_trade_prices`
  11. Create Trade object and update position
  12. Return Trade
- `quote(market, outcome_index, shares) -> float`: Compute cost without executing. Does not check balance/position.

**Acceptance criteria**:
- [ ] Trades correctly update `market.x` vector
- [ ] Trade cost matches `LMSREngine.trade_cost()` exactly
- [ ] Pre/post trade prices captured correctly
- [ ] `TradingHalted` raised for non-TRADING phase
- [ ] `InvalidMarketParameters` raised for invalid outcome_index or zero shares
- [ ] `InsufficientBalance` raised when buy cost exceeds balance
- [ ] `InsufficientShares` raised when sell exceeds held shares
- [ ] Execution is atomic: failed validation leaves market.x unchanged
- [ ] `quote()` returns cost without mutating state
- [ ] Trade IDs increment correctly

**Dependencies**: Tasks 1, 2 (exceptions, positions)

---

### Task 4: Resolution and settlement engine

**File**: `backend/market/resolution.py`

**Description**: Settlement computation — determines per-agent payouts and generates a deterministic `SettlementReport`. Resolution (TRADING → RESOLVING) was already implemented in Sprint 1's `MarketLifecycle.begin_resolution()`. This task adds the settlement logic (RESOLVING → SETTLED with payout computation).

**Implementation** (per SDD §4.9):
- `AgentSettlement` dataclass: `agent_id`, `shares_held`, `winning_shares`, `payout`, `net_cashflow`, `realised_pnl`
- `SettlementReport` dataclass: `market_id`, `winning_outcome`, `winning_label`, `total_payout`, `market_maker_pnl`, `agent_settlements`, `commitment_hash`, `settlement_hash`
- `ResolutionEngine.settle(market, position_manager) -> SettlementReport`:
  1. Verify market.phase == RESOLVING (else `InvalidPhaseTransition`)
  2. For each agent position:
     - `winning_shares = max(0.0, position.shares[resolved_outcome])`
     - `payout = winning_shares` (1:1)
     - `realised_pnl = payout - position.net_cashflow`
     - Create `AgentSettlement`
  3. `total_payout = sum(agent.payout)`
  4. `market_maker_pnl = sum(agent.net_cashflow) - total_payout`
  5. Compute `settlement_hash` via `canonical_json()` → SHA-256
  6. Call `MarketLifecycle.settle(market)` to transition to SETTLED
  7. Return `SettlementReport`

**Acceptance criteria**:
- [ ] `AgentSettlement` has all 6 fields
- [ ] `SettlementReport` has all 8 fields
- [ ] Winning shares paid 1:1, losing shares paid 0
- [ ] `total_payout = sum(agent.payout)`
- [ ] `market_maker_pnl = sum(net_cashflow) - total_payout`
- [ ] `settlement_hash` is deterministic (same inputs → same hash)
- [ ] Settlement transitions market to SETTLED phase

**Dependencies**: Tasks 2, 3 (positions, trading for test setup)

---

### Task 5: Trade execution tests

**File**: `backend/market/tests/test_trading.py`

**Description**: Tests for `TradingEngine.execute_trade()` and `quote()`.

**Tests** (~8):
1. `test_execute_trade_updates_x_vector` — market.x changes correctly
2. `test_execute_trade_cost_matches_lmsr` — cost == `LMSREngine.trade_cost()`
3. `test_execute_trade_captures_prices` — pre/post trade prices correct
4. `test_quote_returns_cost_without_mutation` — market.x unchanged after quote
5. `test_trading_halted_when_not_trading` — TradingHalted raised for COMMITTED phase
6. `test_insufficient_balance_rejects_buy` — InsufficientBalance raised
7. `test_insufficient_shares_rejects_sell` — InsufficientShares raised
8. `test_atomic_execution_on_failure` — market.x unchanged after failed trade
9. `test_sell_trade_returns_cash` — negative cost for sells
10. `test_multiple_trades_accumulate` — multiple trades on same market

**Acceptance criteria**:
- [ ] All tests pass
- [ ] Both buy and sell paths tested
- [ ] All three new exceptions tested
- [ ] Atomicity verified (state unchanged on failure)
- [ ] Quote doesn't mutate state

**Dependencies**: Tasks 1, 2, 3 (all source code)

---

### Task 6: Position tracking tests

**File**: `backend/market/tests/test_positions.py`

**Description**: Tests for `PositionManager` and `AgentPosition`.

**Tests** (~6):
1. `test_new_agent_zero_position` — get_position returns zero-filled
2. `test_update_position_accumulates_shares` — shares increment on buy
3. `test_update_position_decrements_on_sell` — shares decrement on sell
4. `test_net_cashflow_tracks_buys_and_sells` — cashflow correct after mixed trades
5. `test_balance_decreases_on_buy` — get_balance reflects spending
6. `test_settlement_payout_winning_outcome` — winning shares pay 1:1
7. `test_settlement_payout_losing_outcome` — losing shares pay 0

**Acceptance criteria**:
- [ ] All tests pass
- [ ] Position accumulation verified across multiple trades
- [ ] Balance tracking verified
- [ ] Settlement payout for both winning and losing outcomes

**Dependencies**: Tasks 2, 3 (positions, trading for setup helpers)

---

### Task 7: Settlement invariant tests + resolution tests

**File**: `backend/market/tests/test_resolution.py`, `backend/market/tests/test_settlement_invariants.py`

**Description**: Resolution engine tests and settlement mathematical invariants.

**Resolution tests** (~3):
1. `test_settle_computes_correct_payouts` — per-agent payouts match manual calculation
2. `test_settlement_hash_deterministic` — same inputs → same hash
3. `test_settle_transitions_to_settled` — market.phase == SETTLED after settle

**Settlement invariant tests** (~5):
1. `test_bounded_loss_guarantee` — `market_maker_pnl >= -worst_case_loss(b, n)`
2. `test_total_payout_equals_sum_of_agents` — accounting identity
3. `test_realised_pnl_equals_payout_minus_cashflow` — per-agent P&L identity
4. `test_market_maker_pnl_formula` — `mm_pnl = sum(cashflow) - total_payout`
5. `test_zero_trade_market_zero_payout` — no trades means zero settlement

**Acceptance criteria**:
- [ ] All tests pass
- [ ] Bounded loss guarantee verified with multiple agent scenarios
- [ ] All settlement accounting identities verified
- [ ] Deterministic settlement hash verified
- [ ] Edge case: market with no trades

**Dependencies**: Tasks 2, 3, 4 (all source code)

---

### Task 8: End-to-end lifecycle test + package exports update

**Files**: `backend/market/tests/test_e2e.py`, `backend/market/__init__.py` (modify)

**Description**: Full lifecycle integration test and updated public API exports.

**End-to-end test** (~4):
1. `test_full_lifecycle_single_agent` — create → commit → trade → resolve → settle with one agent
2. `test_full_lifecycle_multiple_agents` — three agents trade, one wins, verify all P&L
3. `test_lifecycle_with_buys_and_sells` — agent buys then sells, verify correct settlement
4. `test_multiple_outcomes_market` — 5-outcome market with mixed trades

**`__init__.py` exports update**: Add `Trade`, `TradingEngine`, `AgentPosition`, `PositionManager`, `AgentSettlement`, `SettlementReport`, `ResolutionEngine`, `TradingHalted`, `InsufficientBalance`, `InsufficientShares`

**Acceptance criteria**:
- [ ] All end-to-end tests pass
- [ ] Full lifecycle verified: create → commit → open → trade → resolve → settle
- [ ] P&L correct for multi-agent scenarios
- [ ] Buy + sell path verified in same agent
- [ ] All new public symbols importable from `backend.market`
- [ ] All 63 Sprint 1 tests still pass
- [ ] All Cycle-009 MCP tests pass (69)
- [ ] 25+ new Sprint 2 tests total

**Dependencies**: Tasks 1-7 (all source + test code)

---

## Task Dependency Graph

```
Task 1 (exceptions) ──┬── Task 2 (positions) ──┬── Task 3 (trading) ──┬── Task 4 (resolution)
                       │                         │                      │           │
                       │                         │                      │           │
                       │                         ├── Task 6 (pos tests) │           │
                       │                         │                      │           │
                       │                         │     Task 5 (trade tests)         │
                       │                         │                                  │
                       │                         │     Task 7 (settlement tests) ───┘
                       │                         │
                       └─────────────────────────┴── Task 8 (e2e + exports)
```

---

## Implementation Order (Sequential)

| Order | Task | Why This Order |
|-------|------|----------------|
| 1 | Task 1: New exceptions | Foundation for validation in Tasks 2-4 |
| 2 | Task 2: Position manager | Needed by trading engine (Task 3) |
| 3 | Task 3: Trading engine | Core Sprint 2 deliverable, depends on positions |
| 4 | Task 4: Resolution/settlement | Depends on positions + trading for test data |
| 5 | Task 5: Trading tests | Validates Task 3 |
| 6 | Task 6: Position tests | Validates Task 2 |
| 7 | Task 7: Settlement invariant tests | Validates Task 4 |
| 8 | Task 8: End-to-end + exports | Final integration validation |

---

## Success Criteria (Sprint 2)

From PRD §8b:

- [x] `TradingEngine.execute_trade()` correctly computes cost and updates `MarketState.x`
- [x] `TradingEngine.quote()` returns exact cost without executing
- [x] Trading rejected when not in TRADING phase (`TradingHalted`)
- [x] Sell rejected when insufficient shares (`InsufficientShares`)
- [x] Buy rejected when insufficient balance (`InsufficientBalance`)
- [x] Execution is atomic — no state mutation on validation failure
- [x] `PositionManager` correctly accumulates shares and cashflow per agent
- [x] Settlement pays winning shares 1:1, losing shares 0
- [x] Resolution halts trading and records winning outcome
- [x] Settlement computes correct per-agent payouts
- [x] Market maker P&L never exceeds `-b * ln(n)` (bounded loss guarantee)
- [x] `SettlementReport` hash is deterministic
- [x] End-to-end lifecycle: create → commit → trade → resolve → settle with correct P&L
- [x] All existing tests pass (Sprint 1: 63, pipeline: 175, MCP: 69)
- [x] 25+ new Sprint 2 tests pass

---

## Verification Commands

```bash
# Sprint 2 tests only
python3 -m pytest backend/market/tests/test_trading.py backend/market/tests/test_positions.py backend/market/tests/test_resolution.py backend/market/tests/test_settlement_invariants.py backend/market/tests/test_e2e.py -v

# All market tests (Sprint 1 + Sprint 2)
python3 -m pytest backend/market/tests/ -v

# Full regression
python3 -m pytest -q --ignore=backend/market/

# MCP tests
python3 -m pytest mcp/tests/ -q

# Combined
python3 -m pytest -v
```
