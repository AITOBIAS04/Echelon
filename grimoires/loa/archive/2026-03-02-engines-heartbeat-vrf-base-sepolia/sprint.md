# Sprint Plan: Engines + Heartbeat + VRF + Base Sepolia

**Cycle**: 010b
**Sprints**: 3 (global: 18, 19, 20)
**Date**: 2026-03-02
**PRD**: `grimoires/loa/prd.md` (v1.0)
**SDD**: `grimoires/loa/sdd.md` (v1.0)
**Depends on**: Cycle-010a (LMSR Market Engine) — COMPLETED

---

## Sprint 1 — Butterfly Engine + Entropy Engine + Heartbeat Scheduler

**Global ID**: 18
**Goal**: Deliver the game loop and causal state tracking. Heartbeat drives ticks, Butterfly records Wing Flaps, Entropy applies temporal decay.
**Deliverables**: 6 source files + 4 test files + `__init__.py` = 11 files
**Test target**: 20+ new tests, all existing tests unbroken
**New dependency**: `pytest-asyncio` (test-only)

---

### Task 1: Engine configuration dataclasses

**File**: `backend/engines/config.py`

**Description**: Committed engine parameters per Theatre. Immutable after commitment. Reuses `ParameterMutationAfterCommit` from 010a.

**Implementation**:
- `ButterflyConfig` dataclass: `trade_impact_k` (default 0.1), `trade_impact_policy` ("buy_negative_sell_positive"), `shield_tiers` (dict), `sabotage_impact` (-0.10)
- `EntropyConfig` dataclass: `base_decay_rate` (0.01), `stressed_multiplier` (1.5), `danger_multiplier` (2.0), `critical_multiplier` (3.0)
- `EngineConfig` dataclass: `butterfly`, `entropy`, optional `paradox`/`vrf` (None in Sprint 1), `committed` flag
- `EngineConfig.freeze()`: Sets `committed = True`. Raises `ParameterMutationAfterCommit` if already committed.
- `EngineConfig.to_commitment_dict()`: Returns serialisable dict for inclusion in commitment hash.

**Acceptance criteria**:
- [x] All config dataclasses have correct fields with defaults
- [x] `freeze()` sets committed flag and prevents further modification
- [x] `to_commitment_dict()` returns serialisable dict
- [x] Reuses `ParameterMutationAfterCommit` from `backend.market.exceptions`

**Dependencies**: None

---

### Task 2: Butterfly Engine — Wing Flap recording and stability tracking

**File**: `backend/engines/butterfly.py`

**Description**: Records every causal state transition as a Wing Flap. Tracks TimelineState per Theatre. Stability clamped at write time.

**Implementation** (per SDD §4.2):
- `WingFlapType(str, Enum)`: TRADE, SHIELD, SABOTAGE, RIPPLE, PARADOX, ENTROPY
- `WingFlap` dataclass: 9 fields (flap_id, theatre_id, flap_type, agent_id, stability_impact, pre_stability, post_stability, trigger_detail, timestamp)
- `TimelineState` dataclass: 5 fields (theatre_id, stability=1.0, volume=0.0, flap_count=0, founders_yield_accrued=0.0)
- `ButterflyEngine.__init__()`: `_timelines` dict, `_flaps` dict (audit trail), `_flap_counter`
- `record_flap(flap_type, theatre_id, agent_id, impact, trigger_detail) -> WingFlap`:
  1. Get or create TimelineState
  2. `post_stability = clamp(pre_stability + impact, 0.0, 1.0)`
  3. Update stability, increment flap_count
  4. If TRADE: add `abs(trigger_detail["cost"])` to volume
  5. Append WingFlap to audit trail
- `get_timeline_state(theatre_id) -> TimelineState`
- `get_flaps(theatre_id) -> list[WingFlap]`
- `compute_founders_yield(theatre_id) -> float`: `stability × volume × 0.005`

**Acceptance criteria**:
- [x] `WingFlapType` enum has all 6 members
- [x] `WingFlap` has all 9 fields
- [x] `TimelineState` has all 5 fields with correct defaults
- [x] Stability clamped to [0.0, 1.0] at write time
- [x] Volume tracks cumulative trade cost
- [x] Flap audit trail is append-only and queryable by theatre
- [x] Founder's Yield formula correct: `stability × volume × 0.005`
- [x] Multi-theatre isolation (separate TimelineState per theatre)

**Dependencies**: Task 1

---

### Task 3: Entropy Engine — temporal stability decay

**File**: `backend/engines/entropy.py`

**Description**: Applies temporal decay to timeline stability on each ENTROPY tick. Decay rate scales with Logic Gap status.

**Implementation** (per SDD §4.3):
- `EntropyEngine.__init__(config, butterfly)`: Stores config and butterfly reference
- `tick(theatre_id, logic_gap_status="healthy") -> WingFlap`:
  1. Compute effective decay rate from status
  2. `impact = -effective_rate` (always negative)
  3. Record ENTROPY Wing Flap via ButterflyEngine
  4. Return WingFlap
- `get_effective_decay_rate(logic_gap_status) -> float`:
  - healthy → `base_decay_rate`
  - stressed → `base × stressed_multiplier`
  - danger → `base × danger_multiplier`
  - critical → `base × critical_multiplier`
  - unknown → `base_decay_rate` (defensive default)

**Acceptance criteria**:
- [x] Base decay rate correct (0.01 = 1% per tick)
- [x] Multiplier scaling correct for all 4 Logic Gap statuses
- [x] Unknown status defaults to base rate (no crash)
- [x] Produces ENTROPY Wing Flap via ButterflyEngine
- [x] Stability boundary: decay at 0.0 stays at 0.0 (no negative)

**Dependencies**: Tasks 1, 2

---

### Task 4: Heartbeat Scheduler — asyncio-based multi-cadence timer

**File**: `backend/engines/heartbeat.py`

**Description**: Drives periodic ticks at four cadences. Handler registration shared across theatres. asyncio.Task per cadence per theatre.

**Implementation** (per SDD §4.4):
- `HeartbeatConfig` dataclass: agent_interval_s (5.0), market_interval_s (10.0), paradox_interval_s (30.0), entropy_interval_s (60.0)
- `CADENCES = ["agent", "market", "paradox", "entropy"]`
- `HeartbeatScheduler.__init__(config)`: `_handlers` dict, `_tasks` dict, `_tick_counts` dict
- `register_handler(cadence, handler)`: Append async handler for cadence
- `start(theatre_id)`: Create asyncio.Task per cadence running `_tick_loop`
- `stop(theatre_id)`: Cancel all tasks for theatre. Await cancellation. Idempotent.
- `tick_count(theatre_id) -> dict[str, int]`: Return counts per cadence
- `_tick_loop(theatre_id, cadence, interval)`: `while True: sleep(interval), call handlers, increment count`

**Acceptance criteria**:
- [x] Ticks at correct cadences (within 10% tolerance)
- [x] Multiple theatres run concurrent heartbeats without interference
- [x] Start/stop is clean (no leaked asyncio tasks)
- [x] Handler registration works for all 4 cadences
- [x] Tick counts accurate per cadence per theatre
- [x] Idempotent stop (calling stop twice doesn't crash)

**Dependencies**: None

---

### Task 5: Integration layer — wiring engines to 010a market system

**File**: `backend/engines/integration.py`

**Description**: `EngineOrchestrator` wraps 010a's TradingEngine to produce Wing Flaps. Registers heartbeat handlers. Circuit breaker halt flag.

**Implementation** (per SDD §4.5):
- `EngineOrchestrator.__init__(market, trading_engine, position_manager, butterfly, entropy, engine_config, heartbeat)`: Store references, `_halted = False`
- `execute_trade_with_flap(agent_id, outcome_index, shares) -> Trade`:
  1. Check `_halted` → raise `TradingHalted` if True
  2. Delegate to `TradingEngine.execute_trade()`
  3. Compute stability impact: `clamp(k × abs(cost) / b, -0.05, 0.05)`, negative for buy, positive for sell
  4. Record TRADE Wing Flap via ButterflyEngine
  5. Return Trade
- `halt_trading(theatre_id)`: Set `_halted = True`
- `resume_trading(theatre_id)`: Set `_halted = False`
- `start()`: Register entropy handler on heartbeat, start heartbeat for theatre
- `stop()`: Stop heartbeat, clean shutdown

**Acceptance criteria**:
- [x] Delegates to TradingEngine.execute_trade() correctly
- [x] Every trade produces a TRADE Wing Flap with correct impact
- [x] Impact sign: buy = negative (destabilising), sell = positive (stabilising)
- [x] Impact clamped to [-0.05, 0.05]
- [x] Halt flag blocks trades with TradingHalted exception
- [x] No modifications to `backend/market/` modules
- [x] Heartbeat handlers registered and running

**Dependencies**: Tasks 1, 2, 3, 4

---

### Task 6: Butterfly + Entropy tests

**Files**: `backend/engines/tests/test_butterfly.py`, `backend/engines/tests/test_entropy.py`

**Description**: Unit tests for Butterfly Engine and Entropy Engine.

**Butterfly tests** (~6):
1. `test_record_flap_updates_stability` — stability changes by impact
2. `test_stability_clamped_at_zero` — negative impact at low stability stays >= 0.0
3. `test_stability_clamped_at_one` — positive impact at 1.0 stays <= 1.0
4. `test_volume_tracks_trade_cost` — volume accumulates abs(cost)
5. `test_founders_yield_formula` — yield = stability × volume × 0.005
6. `test_multi_theatre_isolation` — separate TimelineState per theatre
7. `test_flap_audit_trail_append_only` — flaps queryable, ordering preserved

**Entropy tests** (~4):
1. `test_base_decay_rate` — healthy status applies base rate
2. `test_multiplier_scaling` — stressed/danger/critical multiply correctly
3. `test_unknown_status_defaults_to_base` — no crash on unknown
4. `test_decay_at_zero_stays_zero` — boundary condition
5. `test_entropy_produces_wing_flap` — returns valid ENTROPY WingFlap

**Acceptance criteria**:
- [x] All Butterfly tests pass
- [x] All Entropy tests pass
- [x] Stability bounds verified at both extremes
- [x] Multi-theatre isolation confirmed

**Dependencies**: Tasks 1, 2, 3

---

### Task 7: Heartbeat tests

**File**: `backend/engines/tests/test_heartbeat.py`

**Description**: Async tests for HeartbeatScheduler using pytest-asyncio.

**Tests** (~5):
1. `test_tick_cadence_timing` — ticks fire within 10% of configured interval
2. `test_multiple_theatres_concurrent` — two theatres tick independently
3. `test_graceful_stop` — no leaked tasks after stop
4. `test_handler_registration` — registered handler receives theatre_id
5. `test_tick_counts_accurate` — tick_count returns correct values
6. `test_idempotent_stop` — calling stop twice doesn't crash

**Acceptance criteria**:
- [x] All heartbeat tests pass
- [x] Timing within 10% tolerance
- [x] No leaked asyncio tasks
- [x] `pytest-asyncio` dependency confirmed working

**Dependencies**: Task 4

---

### Task 8: Integration tests + package exports

**Files**: `backend/engines/tests/test_integration.py`, `backend/engines/__init__.py`

**Description**: End-to-end integration tests and public API exports.

**Integration tests** (~5):
1. `test_trade_produces_wing_flap` — execute_trade_with_flap records TRADE flap
2. `test_trade_impact_sign_convention` — buy=negative, sell=positive
3. `test_halt_blocks_trades` — halted orchestrator raises TradingHalted
4. `test_heartbeat_drives_entropy` — entropy tick fires on heartbeat cadence
5. `test_config_immutability_after_freeze` — frozen config rejects mutations
6. `test_end_to_end_lifecycle` — create market → start heartbeat → trade → observe flaps → entropy decay

**`__init__.py` exports**: All public symbols from all Sprint 1 modules.

**Acceptance criteria**:
- [x] All integration tests pass
- [x] Full lifecycle test: market → heartbeat → trade → flaps → entropy
- [x] No modifications to `backend/market/` modules
- [x] All new public symbols importable from `backend.engines`
- [x] All 100 Sprint 1+2 market tests still pass
- [x] All 69 MCP tests still pass
- [x] 20+ new Sprint 1 tests total (47 delivered)

**Dependencies**: Tasks 1-7

---

## Task Dependency Graph (Sprint 1)

```
Task 1 (config) ──── Task 2 (butterfly) ──── Task 3 (entropy) ────┐
                                                                    │
Task 4 (heartbeat) ────────────────────────────────────────────────├── Task 5 (integration)
                                                                    │
                     Task 6 (butterfly + entropy tests) ───────────┤
                     Task 7 (heartbeat tests) ─────────────────────┤
                                                                    │
                     Task 8 (integration tests + exports) ─────────┘
```

---

## Implementation Order (Sprint 1)

| Order | Task | Why This Order |
|-------|------|----------------|
| 1 | Task 1: Engine configuration | Foundation for all engines |
| 2 | Task 2: Butterfly Engine | Core state tracking, needed by everything |
| 3 | Task 3: Entropy Engine | Depends on Butterfly for Wing Flap recording |
| 4 | Task 4: Heartbeat Scheduler | Independent, but needed by integration |
| 5 | Task 5: Integration layer | Wires engines to 010a, depends on all source |
| 6 | Task 6: Butterfly + Entropy tests | Validates Tasks 2-3 |
| 7 | Task 7: Heartbeat tests | Validates Task 4 |
| 8 | Task 8: Integration tests + exports | Final validation |

---

## Sprint 1 Success Criteria

From PRD §8a:

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
- [ ] All existing tests pass (100 market + 69 MCP + 175 pipeline)
- [ ] 20+ new Sprint 1 tests pass

---

## Sprint 2 — Paradox Engine + Logic Gap + Circuit Breakers

**Global ID**: 19
**Goal**: Deliver the self-policing integrity layer. Logic Gap scanning, four Paradox modes, circuit breaker actions, evidence completeness gates, Entropy←Paradox wiring.
**Deliverables**: 3 source files + 4 test files = 7 files
**Test target**: 20+ new tests
**Depends on**: Sprint 1 (Butterfly + Entropy + Heartbeat)

### Tasks (Sprint 2)

1. **Logic Gap calculator** — `backend/engines/logic_gap.py`: p_market smoothing (trailing window), LogicGapStatus classification, LogicGapReading computation.
2. **Reality Signal provider** — `backend/engines/reality_signal.py`: RealitySignal dataclass, base class, OsintRealityProvider, DeterministicRealityProvider, StubRealityProvider.
3. **Paradox Engine** — `backend/engines/paradox.py`: ParadoxConfig, ParadoxMode, ParadoxAction, ParadoxRuntimeState, scan/evaluate_thresholds/check_activation_gate/execute_action. Four modes. Latch semantics for gates. Include config in commitment hash.
4. **Entropy←Paradox wiring** — Update integration layer: Entropy Engine receives real Logic Gap status from Paradox scans. Register Paradox handler on PARADOX heartbeat cadence.
5. **Logic Gap tests** — `test_logic_gap.py`: Smoothing accuracy, classification at exact boundaries, gap direction sign, edge values (0.0, 0.5, 1.0).
6. **Paradox tests** — `test_paradox.py`: Threshold crossing, activation gate latch, mode-dependent filtering, config in commitment hash.
7. **Circuit breaker tests** — `test_circuit_breakers.py`: WARN/TRADING_PAUSE/FORCED_RESOLUTION determinism, mode overrides (advisory caps at WARN, circuit_breaker only critical).
8. **Entropy←Paradox tests** — `test_entropy_paradox.py`: Entropy receives real Logic Gap, escalating decay rates, end-to-end: trade → price moves → Logic Gap diverges → decay escalates.

### Sprint 2 Success Criteria

From PRD §8b:

- [x] Logic Gap = `abs(p_market - p_reality)` correctly computed
- [x] p_market uses trailing window smoothing (configurable, default 60s)
- [x] p_reality from `osint` source reads `composite_score` correctly
- [x] p_reality from `deterministic` source reads scorer output correctly
- [x] Logic Gap status thresholds match default policies
- [x] Activation gates prevent premature Paradox activation
- [x] `enabled` mode: WARN at warn, TRADING_PAUSE at breach, FORCED_RESOLUTION at critical
- [x] `advisory` mode: all thresholds produce WARN only
- [x] `circuit_breaker` mode: only critical threshold evaluated
- [x] `disabled` mode: scan returns None
- [x] Circuit breaker actions are deterministic
- [x] Activation gate uses latch semantics
- [x] Entropy Engine responds to real Paradox Logic Gap status
- [x] Paradox configuration is immutable after Theatre commitment
- [x] Paradox thresholds included in commitment hash
- [x] All existing tests pass
- [x] 20+ new Sprint 2 tests pass (52 delivered)

---

## Sprint 3 — VRF + Base Sepolia + MCP Status + FULL Mode

**Global ID**: 20
**Goal**: Deliver fairness and auditability. VRF randomness, on-chain proofs, status integration, FULL mode quant templates.
**Deliverables**: 5 source files + 1 Solidity contract + 6 test files = 12 files
**Test target**: 25+ new tests
**Depends on**: Sprints 1-2 (all engines)

### Tasks (Sprint 3)

1. **VRF provider** — `backend/engines/vrf.py`: VRFConfig, VRFResult, VRFProvider with local (HMAC-SHA256) and testnet (Chainlink VRF V2) modes. `scale_to_range()` utility.
2. **VRF wiring** — Inject VRF into Butterfly (sabotage impact), Paradox (threshold offsets), Entropy (pricing). Update EngineOrchestrator.
3. **Base Sepolia client** — `backend/chain/sepolia.py`: BaseSepoliaClient (publish/verify commitment and settlement), MockSepoliaClient, TxReceipt/CommitmentRecord/SettlementRecord dataclasses.
4. **EchelonCommitment.sol** — `backend/chain/contracts/EchelonCommitment.sol`: Minimal Solidity contract storing theatre→hash mappings.
5. **Hardhat deployment script** — Deploy to Base Sepolia testnet.
6. **Market status snapshot** — `backend/engines/status.py`: `market_status_snapshot()` assembling live state from all engines. Wire to MCP `echelon_status` if merged.
7. **FULL mode quant templates** — Rerun 4 templates with real engines. Compute FULL baselines, pin to `fixtures/echelon_quant_v0_2/full_mode_baselines.json`.
8. **VRF tests** — `test_vrf.py`: Local determinism, purpose differentiation, range scaling, verify.
9. **Chain tests** — `test_sepolia.py` + `test_contract.py`: Publish/verify round-trip, mock client, receipt validation, Solidity read/write.
10. **Status + FULL mode tests** — `test_status.py` + `test_full_mode_templates.py`: Snapshot assembly, 4 quant templates pass.
11. **End-to-end lifecycle test** — `test_e2e_engines.py`: Full lifecycle with all engines: create → commit (on-chain) → heartbeat → trade → Wing Flaps → Paradox → Entropy → resolve → settle (on-chain) → verify.

### Sprint 3 Success Criteria

From PRD §8c:

- [x] VRF local mode produces deterministic outputs from fixed seed
- [x] VRF testnet mode calls Chainlink VRF V2 (non-blocking, `@pytest.mark.testnet`)
- [x] Sabotage stability impact is VRF-randomised within committed range
- [x] Circuit breaker threshold offsets are VRF-randomised
- [x] Commitment hash published to Base Sepolia and readable
- [x] Settlement hash published to Base Sepolia and readable
- [x] `market_status_snapshot(theatre_id)` returns live market state
- [x] `quant_market_hygiene_v1` passes in FULL mode
- [x] `quant_market_perturbation_harness_v1` passes in FULL mode
- [x] `quant_market_api_fidelity_v1` passes in FULL mode
- [x] `lmsr_b_sensitivity_suite_v1` passes in FULL mode
- [x] FULL mode baselines computed, pinned, stored
- [x] End-to-end lifecycle with all engines active
- [x] All existing tests pass
- [x] 25+ new Sprint 3 tests pass (54 delivered)

---

## Verification Commands

```bash
# Sprint 1 engine tests only
python3 -m pytest backend/engines/tests/ -v

# All market tests (010a, should be unchanged)
python3 -m pytest backend/market/tests/ -q

# MCP regression
python3 -m pytest mcp/tests/ -q

# Sprint 3: FULL mode quant templates
python3 -m pytest backend/engines/tests/test_full_mode_templates.py -v

# Sprint 3: Chain tests (requires Hardhat)
python3 -m pytest backend/chain/tests/ -v

# Combined
python3 -m pytest -q
```
