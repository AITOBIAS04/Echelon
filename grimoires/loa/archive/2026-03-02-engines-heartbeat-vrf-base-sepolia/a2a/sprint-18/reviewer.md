# Sprint 18 — Implementation Report

**Sprint**: 1 (global: 18)
**Cycle**: 010b — Engines + Heartbeat + VRF + Base Sepolia
**Goal**: Butterfly Engine + Entropy Engine + Heartbeat Scheduler
**Date**: 2026-03-02
**Status**: IMPLEMENTED

---

## Summary

Delivered the game loop and causal state tracking layer. 5 source files + 4 test files + 2 `__init__.py` files. 47 new tests, all passing. Zero regression in existing 100 market tests and 69 MCP tests.

---

## Task Completion

### Task 1: Engine configuration dataclasses — DONE

**File**: `backend/engines/config.py` (76 lines)

- `ButterflyConfig`: `trade_impact_k=0.1`, `trade_impact_policy`, `shield_tiers` dict, `sabotage_impact=-0.10`
- `EntropyConfig`: `base_decay_rate=0.01`, stressed/danger/critical multipliers (1.5/2.0/3.0)
- `EngineConfig`: butterfly + entropy, `committed` flag, `freeze()`, `assert_not_committed()`, `to_commitment_dict()`
- Reuses `ParameterMutationAfterCommit` from `backend.market.exceptions`

**AC**: All 4 criteria met.

### Task 2: Butterfly Engine — DONE

**File**: `backend/engines/butterfly.py` (121 lines)

- `WingFlapType(str, Enum)`: 6 members (TRADE, SHIELD, SABOTAGE, RIPPLE, PARADOX, ENTROPY)
- `WingFlap` dataclass: 9 fields
- `TimelineState` dataclass: 5 fields (stability=1.0, volume=0.0, flap_count=0, founders_yield_accrued=0.0)
- `ButterflyEngine.record_flap()`: clamps stability to [0.0, 1.0], tracks volume for TRADE flaps, append-only audit trail
- `compute_founders_yield()`: `stability × volume × 0.005`
- `_clamp()` utility exposed for integration layer

**AC**: All 8 criteria met.

### Task 3: Entropy Engine — DONE

**File**: `backend/engines/entropy.py` (60 lines)

- `tick(theatre_id, logic_gap_status="healthy") -> WingFlap`: computes decay, records ENTROPY flap
- `get_effective_decay_rate()`: multiplier lookup (healthy=1×, stressed=1.5×, danger=2×, critical=3×), unknown defaults to base

**AC**: All 5 criteria met.

### Task 4: Heartbeat Scheduler — DONE

**File**: `backend/engines/heartbeat.py` (105 lines)

- `HeartbeatConfig`: 4 interval parameters
- `CADENCES = ["agent", "market", "paradox", "entropy"]`
- `HeartbeatScheduler`: asyncio.Task per (theatre_id, cadence), handler dispatch, tick counts
- `start(theatre_id)` / `stop(theatre_id)`: clean lifecycle with CancelledError handling
- `is_running(theatre_id)`: checks task.done()
- Invalid cadence raises `ValueError`

**AC**: All 6 criteria met.

### Task 5: Integration layer — DONE

**File**: `backend/engines/integration.py` (108 lines)

- `EngineOrchestrator`: wraps TradingEngine, records TRADE Wing Flaps
- `execute_trade_with_flap()`: delegates to 010a, computes impact `clamp(k × abs(cost) / b, -0.05, 0.05)`, sign convention buy=negative, sell=positive
- Circuit breaker: `halt_trading()` / `resume_trading()` with `_halted` flag
- `start()` / `stop()`: registers entropy handler on heartbeat
- Zero modifications to `backend/market/` modules

**AC**: All 7 criteria met.

### Task 6: Butterfly + Entropy tests — DONE

**Files**: `backend/engines/tests/test_butterfly.py` (11 tests), `backend/engines/tests/test_entropy.py` (10 tests)

Butterfly tests:
- `test_record_flap_updates_stability` — stability changes by impact
- `test_stability_clamped_at_zero` — 25 hits then -1.0 stays at 0.0
- `test_stability_clamped_at_one` — SHIELD at max stays at 1.0
- `test_volume_tracks_trade_cost` — abs(25.5) + abs(-10.0) = 35.5
- `test_non_trade_flap_does_not_add_volume` — ENTROPY doesn't add volume
- `test_founders_yield_formula` — 0.80 × 1000.0 × 0.005 = 4.0
- `test_founders_yield_zero_volume` — returns 0.0
- `test_multi_theatre_isolation` — t1 ≠ t2
- `test_flap_audit_trail_append_only` — 2 flaps, correct order
- `test_flap_ids_increment` — flp_000001, flp_000002
- `test_empty_theatre_returns_empty_flaps` — []

Entropy tests:
- `test_base_decay_rate_healthy` — 0.01
- `test_stressed_multiplier` — 0.015
- `test_danger_multiplier` — 0.02
- `test_critical_multiplier` — 0.03
- `test_unknown_status_defaults_to_base` — 0.01
- `test_tick_produces_entropy_wing_flap` — type, agent_id, impact
- `test_tick_decrements_stability` — 1.0 → 0.99
- `test_tick_with_critical_status` — impact = -0.03
- `test_decay_at_zero_stays_zero` — 0.0 → 0.0
- `test_multiple_ticks_accumulate` — 10 ticks → 0.90

**AC**: All 4 criteria met.

### Task 7: Heartbeat tests — DONE

**File**: `backend/engines/tests/test_heartbeat.py` (11 tests)

- `test_register_valid_cadence` — no error
- `test_register_invalid_cadence_raises` — ValueError
- `test_start_creates_tasks` — is_running = True
- `test_stop_cancels_tasks` — is_running = False
- `test_stop_idempotent` — double stop, no error
- `test_is_running_false_before_start` — False
- `test_handler_called_with_theatre_id` — all invocations = "t1"
- `test_multiple_handlers_same_cadence` — both handlers called
- `test_tick_counts_increment` — agent count > 0
- `test_tick_count_unknown_theatre` — all zeros
- `test_two_theatres_independent` — stop t1 doesn't affect t2

**AC**: All 4 criteria met. pytest-asyncio working (installed 1.2.0).

### Task 8: Integration tests + package exports — DONE

**File**: `backend/engines/tests/test_integration.py` (15 tests)

Trade + Wing Flap tests:
- `test_trade_returns_trade_object` — trade_id not None
- `test_trade_records_wing_flap` — 1 TRADE flap with correct agent_id
- `test_buy_produces_negative_impact` — impact < 0
- `test_sell_produces_positive_impact` — impact > 0
- `test_impact_clamped` — [-0.05, 0.05] enforced with extreme k/b
- `test_flap_trigger_detail_contains_trade_info` — trade_id, outcome_index, shares, cost

Circuit breaker tests:
- `test_halt_blocks_trading` — TradingHalted raised
- `test_resume_allows_trading` — trade succeeds after resume

Config immutability tests:
- `test_freeze_sets_committed` — False → True
- `test_double_freeze_raises` — ParameterMutationAfterCommit
- `test_assert_not_committed_before_freeze` — no error
- `test_assert_not_committed_after_freeze` — ParameterMutationAfterCommit
- `test_commitment_dict` — correct keys and values

Package exports tests:
- `test_all_exports_importable` — 12 symbols verified
- `test_all_list_complete` — `__all__` matches expected set

**AC**: All 7 criteria met.

---

## Test Results

```
backend/engines/tests/ — 47 passed in 0.20s
backend/market/tests/  — 100 passed in 0.05s (no regression)
mcp/tests/             — 69 passed in 0.66s (no regression)
```

**Total new tests**: 47 (target was 20+)

---

## Files Created

| File | Lines | Purpose |
|------|-------|---------|
| `backend/engines/config.py` | 76 | Engine configuration dataclasses |
| `backend/engines/butterfly.py` | 121 | Wing Flap recording + TimelineState |
| `backend/engines/entropy.py` | 60 | Temporal stability decay |
| `backend/engines/heartbeat.py` | 105 | Asyncio multi-cadence timer |
| `backend/engines/integration.py` | 108 | EngineOrchestrator wiring |
| `backend/engines/__init__.py` | 30 | Public API exports |
| `backend/engines/tests/__init__.py` | 0 | Package marker |
| `backend/engines/tests/test_butterfly.py` | 119 | 11 butterfly tests |
| `backend/engines/tests/test_entropy.py` | 82 | 10 entropy tests |
| `backend/engines/tests/test_heartbeat.py` | 158 | 11 heartbeat tests |
| `backend/engines/tests/test_integration.py` | 168 | 15 integration tests |

**Total**: 11 files, ~1,027 lines

---

## Dependencies

- **New test dependency**: `pytest-asyncio` 1.2.0 (test-only, for async heartbeat tests)
- **No new runtime dependencies**
- **010a modules consumed read-only**: `backend.market.state`, `backend.market.trading`, `backend.market.positions`, `backend.market.exceptions`

---

## Design Decisions

1. **Wrapper pattern**: EngineOrchestrator delegates to TradingEngine rather than modifying it. Caller uses `execute_trade_with_flap()` explicitly — no hidden side effects.
2. **Stability clamped at write time**: `_clamp()` applied in `record_flap()`, not deferred. Ensures invariant `0.0 ≤ stability ≤ 1.0` at all times.
3. **Impact sign convention**: Buy = negative (destabilising), sell = positive (stabilising). Matches `trade_impact_policy: "buy_negative_sell_positive"`.
4. **Heartbeat sleep-first**: `_tick_loop()` calls `await asyncio.sleep(interval)` before first handler invocation. First tick fires after one interval, not immediately.
5. **`_clamp()` exposed from butterfly.py**: Integration layer imports it for impact clamping. Not in `__all__` (private utility).

---

## Ready for Review

All 8 tasks complete. 47 new tests passing. Zero regression. No modifications to `backend/market/`.
