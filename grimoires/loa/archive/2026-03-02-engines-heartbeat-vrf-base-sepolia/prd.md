# PRD: Engines + Heartbeat + VRF + Base Sepolia

**Cycle**: 010b
**Version**: 1.0
**Date**: 2026-03-02
**Predecessor**: Cycle-010a (LMSR Market Engine — local mode, 100 tests)

---

## 1. Problem Statement

Cycle-010a delivered a proven LMSR market engine — cost function, lifecycle, trade execution, positions, settlement — all deterministic, all tested. But a market engine alone is not a game loop. Agents can trade, but there is no temporal decay, no causal state tracking, no integrity monitoring, no verifiable randomness, and no on-chain auditability.

Without the engine layer, Echelon is a correct calculator. With it, Echelon becomes a live adversarial proving ground where stability degrades over time, integrity is self-policed, randomness is verifiable, and proofs are published on-chain.

> Sources: echelon_cycle_010b.md:12-16, echelon_platform_roadmap.md:119-121

---

## 2. Vision

After Cycle-010b, Echelon has a live game loop: agents trade against LMSR markets, the Butterfly Engine records causal state transitions, Entropy decays stability over time, the Paradox Engine detects integrity breaches, VRF ensures execution fairness, and on-chain proofs make the whole thing auditable. The four quant templates pass in FULL mode — the platform is certified.

> Sources: echelon_cycle_010b.md:16-17, echelon_cycle_010b.md:667-669

---

## 3. Goals & Success Metrics

### 3.1 Primary Goals

1. **Game Loop**: Heartbeat scheduler driving four cadences (AGENT 5s, MARKET 10s, PARADOX 30s, ENTROPY 60s)
2. **Causal State Tracking**: Every action that modifies market state passes through the Butterfly Engine as a Wing Flap
3. **Temporal Decay**: Entropy Engine degrades timeline stability over time, scaled by Logic Gap status
4. **Integrity Monitoring**: Paradox Engine scans for divergence between market-implied and reality probabilities
5. **Verifiable Randomness**: VRF provider injects fairness into engine operations
6. **On-Chain Auditability**: Commitment and settlement hashes published to Base Sepolia
7. **FULL Mode Certification**: All four quant templates pass with real engines replacing LOCAL_MODE stubs

### 3.2 Success Metrics

| Metric | Target |
|--------|--------|
| Sprint 1 new tests | 20+ |
| Sprint 2 new tests | 20+ |
| Sprint 3 new tests | 25+ |
| Existing test regression | 0 failures (100 market + 69 MCP + 175 pipeline) |
| FULL mode quant templates | 4/4 pass |
| Base Sepolia deployment | Commitment + settlement round-trip verified |

---

## 4. Functional Requirements

### 4.1 Heartbeat Scheduler

**File**: `backend/engines/heartbeat.py`

An `asyncio`-based scheduler that drives periodic ticks at four cadences. The scheduler doesn't know what Butterfly or Entropy are — it ticks and calls registered handlers.

- `HeartbeatConfig` dataclass: four interval parameters (agent 5s, market 10s, paradox 30s, entropy 60s)
- `HeartbeatScheduler.start(theatre_id)`: Start non-blocking heartbeat loop for a Theatre
- `HeartbeatScheduler.stop(theatre_id)`: Stop heartbeat (idempotent)
- `HeartbeatScheduler.register_handler(cadence, handler)`: Register handler for a cadence
- `HeartbeatScheduler.tick_count(theatre_id)`: Return tick counts per cadence for monitoring
- Multiple Theatres run concurrent heartbeats without interference
- Local mode only: `asyncio.create_task` per cadence per Theatre, single process

> Sources: echelon_cycle_010b.md:79-109

### 4.2 Butterfly Engine

**File**: `backend/engines/butterfly.py`

Records every causal state transition (Wing Flap) from trade execution and engine actions.

**Data structures**:
- `WingFlapType` enum: TRADE, SHIELD, SABOTAGE, RIPPLE, PARADOX, ENTROPY
- `WingFlap` dataclass: flap_id, theatre_id, flap_type, agent_id (None for system flaps), stability_impact (signed), pre_stability, post_stability, trigger_detail, timestamp
- `TimelineState` dataclass: theatre_id, stability (0.0–1.0, starts at 1.0), volume, flap_count, founders_yield_accrued

**Operations**:
- `record_flap(flap_type, theatre_id, agent_id, impact, trigger_detail) -> WingFlap`: Record a Wing Flap. Stability clamped at write: `post_stability = clamp(pre_stability + impact, 0.0, 1.0)`
- `get_timeline_state(theatre_id) -> TimelineState`
- `compute_founders_yield(theatre_id) -> float`: `yield = stability × volume × 0.005`

**Stability impact ranges** (committed per Theatre):

| Flap Type | Impact Range | Determination (010b) |
|-----------|-------------|---------------------|
| TRADE | ±0.001 to ±0.05 | `clamp(k × notional / liquidity_depth, -0.05, 0.05)`, k committed per Theatre (default 0.1). Buy=negative, sell=positive. |
| SHIELD | +0.02 to +0.10 | Fixed per difficulty tier: easy +0.02, medium +0.05, hard +0.10 |
| SABOTAGE | -0.05 to -0.15 | Sprint 1-2: deterministic midpoint -0.10. Sprint 3: VRF-randomised |
| RIPPLE | ±0.01 to ±0.03 | Stubbed (no cross-timeline wiring). Schema exists, no source. |
| PARADOX | -0.10 to -0.30 | Severity-scaled: WARN=-0.10, TRADING_PAUSE=-0.20, FORCED_RESOLUTION=-0.30 |
| ENTROPY | -0.01 baseline | Fixed decay rate per tick. Scaled by Logic Gap multiplier (Sprint 2). |

> Sources: echelon_cycle_010b.md:111-172

### 4.3 Entropy Engine

**File**: `backend/engines/entropy.py`

Temporal decay of timeline stability. Runs on ENTROPY heartbeat tick (60s cadence).

- `EntropyConfig` dataclass: base_decay_rate (0.01), stressed/danger/critical multipliers (1.5/2.0/3.0)
- `EntropyEngine.tick(theatre_id, logic_gap_status) -> WingFlap`: Apply decay, return ENTROPY WingFlap
- `EntropyEngine.get_effective_decay_rate(logic_gap_status) -> float`
- Decay rate scales with Logic Gap status: healthy=base, stressed=1.5×, danger=2×, critical=3×
- Sprint 1 default: `"healthy"` (Paradox not built yet). Sprint 2 wires real Logic Gap.

> Sources: echelon_cycle_010b.md:174-204

### 4.4 Engine Configuration

**File**: `backend/engines/config.py`

Committed engine parameters per Theatre. Immutable after commitment (reuses 010a commitment pattern).

- Stability impact ranges, decay rates, yield multiplier
- Included in commitment hash computation
- Configuration frozen at Theatre creation time

### 4.5 Integration Layer

**File**: `backend/engines/integration.py`

Wiring layer that connects engines to 010a's market system without modifying `backend/market/` modules.

- Hook `TradingEngine.execute_trade()` to produce TRADE Wing Flaps via thin wrapper or event hook
- Register Entropy tick on ENTROPY heartbeat cadence
- Register Paradox scan on PARADOX heartbeat cadence (Sprint 2)
- No modification to 010a modules

> Sources: echelon_cycle_010b.md:172, 231

### 4.6 Paradox Engine — Logic Gap

**File**: `backend/engines/logic_gap.py`, `backend/engines/paradox.py`

Self-policing integrity mechanism. Scans for divergence between market-implied probability (p_market) and reality signals (p_reality).

**Logic Gap calculation**:
- `LogicGapReading` dataclass: theatre_id, p_market, p_reality, logic_gap (abs difference), gap_direction (signed), status (HEALTHY/STRESSED/DANGER/CRITICAL), smoothing_window_s, timestamp
- `LogicGapStatus` enum: HEALTHY (<20%), STRESSED (20-40%), DANGER (40-60%), CRITICAL (>60%)
- p_market: from `LMSREngine.prices()`, smoothed over trailing window (default 60s)
- p_reality: from `RealitySignalProvider` (osint or deterministic source)

**Reality Signal interface** (`backend/engines/reality_signal.py`):
- `RealitySignal` dataclass: p_reality, evidence_bundle_hash, certificate_id, source_type
- `RealitySignalProvider.get_signal(theatre_id) -> RealitySignal`
- Implemented: `osint` (reads composite_score from calibration certificate), `deterministic` (reads scorer output)
- Stubbed: `survey`, `simulation` (raise `NotImplementedError`)

> Sources: echelon_cycle_010b.md:258-314

### 4.7 Paradox Engine — Threshold Evaluation & Circuit Breakers

**File**: `backend/engines/paradox.py`

**Paradox modes** (`ParadoxMode` enum):
- `disabled`: No scanning, no Logic Gap computation
- `enabled`: Full lifecycle — scan, evaluate all thresholds, fire circuit breakers
- `advisory`: Scan and log, WARN Wing Flaps only — no market intervention
- `circuit_breaker`: Only critical threshold evaluated, fires FORCED_RESOLUTION if breached

**Configuration** (`ParadoxConfig`, committed at Theatre creation):
- mode, inquiry_class, warn/breach/critical thresholds, activation_gate, logic_gap_source, smoothing_window_s
- Included in commitment hash

**Default policies by inquiry class**:

| Inquiry Class | Mode | Warn | Breach | Critical | Activation Gate |
|---------------|------|------|--------|----------|-----------------|
| counterfactual | enabled | 0.20 | 0.40 | 0.60 | none |
| investigative | enabled | 0.30 | 0.50 | 0.70 | min_evidence_completeness: 0.50 |
| inspection | enabled | 0.20 | 0.40 | 0.60 | min_time_elapsed: 300s |
| survey | advisory | 0.30 | 0.50 | 0.70 | min_observations: 30 |
| scrutiny | circuit_breaker | — | — | 0.80 | none |

**Circuit breaker actions** (`ParadoxAction` enum):
- `WARN`: Log + PARADOX Wing Flap, no market intervention
- `TRADING_PAUSE`: Halt trading via integration layer (not by modifying market modules)
- `FORCED_RESOLUTION`: Force market to RESOLVING phase. Binary only: `winning_outcome = 1 if p_reality >= 0.5 else 0`

**Activation gate**: Latch semantics — once satisfied, never reverts. Prevents flicker.

**Evidence completeness**: `count(required sources with EvidenceBundle) / count(required sources)`. Aligns with AC-1 GapKind semantics from Cycle-004.

> Sources: echelon_cycle_010b.md:317-404

### 4.8 VRF Integration

**File**: `backend/engines/vrf.py`

Verifiable Random Function provider abstracting local stub vs on-chain.

- `VRFConfig` dataclass: provider ("chainlink_v2"), mode ("local"|"testnet"), seed (fixed for local)
- `VRFProvider.request_randomness(theatre_id, purpose) -> VRFResult`: Local mode = deterministic from seed+purpose. Testnet = Chainlink VRF V2 on Base Sepolia.
- `VRFProvider.verify(result) -> bool`: Always true in local mode. On-chain verification in testnet.
- `VRFResult` dataclass: request_id, random_value (uint256), proof (None in local), verified, purpose

**Application points**:

| Application | Where | Effect |
|-------------|-------|--------|
| Sabotage impact | Butterfly Engine | VRF determines exact impact within committed range |
| Circuit breaker offset | Paradox Engine | VRF adds randomised offset to base thresholds |
| Entropy pricing | Entropy Engine | VRF-scaled dynamic risk adjustment |

**Constraint**: Local mode by default. Testnet is opt-in. Tests marked `@pytest.mark.testnet` and skipped when Base Sepolia unreachable. VRF testnet availability must NOT block Sprint 3 completion.

> Sources: echelon_cycle_010b.md:467-506

### 4.9 Base Sepolia Deployment

**File**: `backend/chain/sepolia.py`

Publishes commitment and settlement hashes to Base Sepolia testnet.

- `BaseSepoliaClient.publish_commitment(theatre_id, commitment_hash) -> TxReceipt`
- `BaseSepoliaClient.publish_settlement(theatre_id, settlement_hash, winning_outcome) -> TxReceipt`
- `BaseSepoliaClient.verify_commitment(theatre_id) -> CommitmentRecord | None`
- `BaseSepoliaClient.verify_settlement(theatre_id) -> SettlementRecord | None`

**Smart contract**: `EchelonCommitment.sol` — stores `theatre_id → commitment_hash` and `theatre_id → settlement_hash` mappings. Read/write. No admin functions. Contract address pinned per run; redeploy allowed between runs.

**What goes on-chain**: Commitment hash, settlement hash, winning outcome index, theatre→hash mapping.
**What does NOT**: No token transfers, no agent wallets, no escrow, no fee collection.

> Sources: echelon_cycle_010b.md:510-542

### 4.10 MCP Status Integration

**File**: `backend/engines/status.py` (or extend `mcp/tools/` if Cycle-009 merged)

Expose live market state via `market_status_snapshot(theatre_id)`:

```json
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

If Cycle-009 `echelon_status` is merged (it is), extend it. Otherwise, local function wired later.

> Sources: echelon_cycle_010b.md:546-563

### 4.11 FULL Mode Quant Templates

Rerun all four LMSR quant templates with real engines replacing LOCAL_MODE stubs:

| LOCAL_MODE Stub | FULL Mode Replacement |
|-----------------|----------------------|
| VRF fixed seed `0xECHELON_LOCAL` | VRF local mode via provider interface |
| Heartbeat stubbed always-alive | Real Heartbeat Scheduler ticking |
| Saboteur/paradox no-op injectors | Real Paradox + Butterfly engines |

FULL mode baselines stored in `fixtures/echelon_quant_v0_2/full_mode_baselines.json`. Computed once during Sprint 3 and pinned. Acceptance: templates pass their own FULL mode expected baselines.

> Sources: echelon_cycle_010b.md:566-576

---

## 5. What 010a Delivers (Consumed by This Cycle)

| API | Purpose |
|-----|---------|
| `LMSREngine.prices(x, b)` | Probability simplex (p_market for Logic Gap) |
| `MarketState` + phases | CREATED→COMMITTED→TRADING→RESOLVING→SETTLED |
| `TradingEngine.execute_trade()` | Atomic trade execution, returns Trade with pre/post prices |
| `PositionManager` | Per-agent position tracking with net_cashflow |
| `ResolutionEngine` + `SettlementReport` | Deterministic settlement with bounded loss guarantee |
| Commitment hash | SHA-256 via canonical JSON with oracle_config stub |

**Key constraint**: No modifications to `backend/market/` modules unless a bug is found.

---

## 6. Non-Functional Requirements

### 6.1 Performance
- Heartbeat tick accuracy within 10% tolerance
- No leaked asyncio tasks on stop
- Single-process, in-memory — no distributed scheduling

### 6.2 Determinism
- Engine configuration immutable after Theatre commitment
- Circuit breaker actions deterministic (same input + mode → same action)
- Settlement hash deterministic (from 010a)
- VRF local mode deterministic from fixed seed

### 6.3 State Isolation
- Each Theatre has its own TimelineState, heartbeat, Paradox state
- PositionManager per market (from 010a)
- No cross-Theatre state leakage

### 6.4 In-Memory Constraint
- All state in-memory (continues 010a pattern)
- After process restart, all Theatre state is lost
- No database persistence in 010b

---

## 7. Scope Exclusions

- No agent brain execution (agents submit trades via direct function calls)
- No real OSINT feeds (p_reality uses existing composite_score or deterministic scorers)
- No token mechanics (no $ECHELON, no burn, no staking)
- No ERC-6551 agent wallets (positions are in-memory)
- No distributed scheduling (asyncio-local only)
- No mainnet deployment (Base Sepolia testnet only)
- No cross-timeline Ripple flaps (RIPPLE schema exists, not wired)
- No database persistence
- No frontend (no UI for engine state)
- Paradox forced resolution is binary-only (`winning_outcome = 1 if p_reality >= 0.5 else 0`)

> Sources: echelon_cycle_010b.md:638-649

---

## 8. Acceptance Criteria

### 8a. Sprint 1 — Butterfly + Entropy + Heartbeat

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

### 8b. Sprint 2 — Paradox Engine + Logic Gap + Circuit Breakers

- [ ] Logic Gap = `abs(p_market - p_reality)` correctly computed
- [ ] p_market uses trailing window smoothing (configurable, default 60s)
- [ ] p_reality from `osint` source reads `composite_score` correctly
- [ ] p_reality from `deterministic` source reads scorer output correctly
- [ ] Logic Gap status thresholds match default policies
- [ ] Activation gates prevent premature Paradox activation
- [ ] `enabled` mode: WARN at warn, TRADING_PAUSE at breach, FORCED_RESOLUTION at critical
- [ ] `advisory` mode: all thresholds produce WARN only
- [ ] `circuit_breaker` mode: only critical threshold evaluated
- [ ] `disabled` mode: scan returns None
- [ ] Circuit breaker actions are deterministic
- [ ] Activation gate uses latch semantics
- [ ] Entropy Engine responds to real Paradox Logic Gap status
- [ ] Paradox configuration is immutable after Theatre commitment
- [ ] Paradox thresholds included in commitment hash
- [ ] All existing tests pass
- [ ] 20+ new Sprint 2 tests pass

### 8c. Sprint 3 — VRF + Base Sepolia + FULL Mode

- [ ] VRF local mode produces deterministic outputs from fixed seed
- [ ] VRF testnet mode calls Chainlink VRF V2 (non-blocking, `@pytest.mark.testnet`)
- [ ] Sabotage stability impact is VRF-randomised within committed range
- [ ] Circuit breaker threshold offsets are VRF-randomised
- [ ] Commitment hash published to Base Sepolia and readable
- [ ] Settlement hash published to Base Sepolia and readable
- [ ] `market_status_snapshot(theatre_id)` returns live market state
- [ ] `quant_market_hygiene_v1` passes in FULL mode
- [ ] `quant_market_perturbation_harness_v1` passes in FULL mode
- [ ] `quant_market_api_fidelity_v1` passes in FULL mode
- [ ] `lmsr_b_sensitivity_suite_v1` passes in FULL mode
- [ ] FULL mode baselines computed, pinned, stored
- [ ] End-to-end lifecycle with all engines active
- [ ] All existing tests pass
- [ ] 25+ new Sprint 3 tests pass

---

## 9. Dependency Chain

```
Cycle-010a (LMSR engine, 100 tests) ← COMPLETED
  → Cycle-010b Sprint 1 (Butterfly + Entropy + Heartbeat)
    → Cycle-010b Sprint 2 (Paradox + Logic Gap + Circuit Breakers)
      → Cycle-010b Sprint 3 (VRF + Base Sepolia + FULL mode)
        → Cycle-011 (WorldMonitor Integration)
        → Cycle-012 (Sponsored Theatre E2E)
```

---

## 10. Key Spec References

| Document | Relevance |
|----------|-----------|
| System Bible v13 §V | Butterfly, Entropy, Wing Flap types, stability impacts, heartbeat schedule |
| System Bible v13 §VII | Chainlink VRF V2, application points, security properties |
| System Bible v13 §VI | On-chain commitment hash, settlement proof |
| Paradox Policy Design Note v1.1 | Logic Gap, p_reality = composite_score, evidence completeness, threshold defaults |
| Theatre Template Library Live v2 | Four LMSR quant templates for FULL mode acceptance |

---

## 11. Architecture Overview

### Sprint 1

```
backend/engines/
├── __init__.py
├── heartbeat.py         # Heartbeat scheduler
├── butterfly.py         # Butterfly Engine — Wing Flap recording
├── entropy.py           # Entropy Engine — temporal decay
├── config.py            # Engine configuration dataclasses
├── integration.py       # Trade hooks, heartbeat handlers
└── tests/
    ├── test_heartbeat.py
    ├── test_butterfly.py
    ├── test_entropy.py
    └── test_integration.py
```

### Sprint 2 (additions)

```
backend/engines/
├── paradox.py           # Paradox Engine — Logic Gap, thresholds, circuit breakers
├── reality_signal.py    # RealitySignalProvider — p_reality with provenance
├── logic_gap.py         # Logic Gap calculation, p_market smoothing
└── tests/
    ├── test_paradox.py
    ├── test_logic_gap.py
    ├── test_circuit_breakers.py
    └── test_entropy_paradox.py
```

### Sprint 3 (additions)

```
backend/engines/
├── vrf.py               # VRF provider abstraction
├── status.py            # market_status_snapshot()
└── tests/
    ├── test_vrf.py
    └── test_full_mode_templates.py

backend/chain/
├── __init__.py
├── sepolia.py           # Base Sepolia client
├── contracts/
│   └── EchelonCommitment.sol
└── tests/
    ├── test_sepolia.py
    └── test_contract.py
```
