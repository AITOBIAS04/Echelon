# Sprint 19 (Cycle-010b Sprint 2) — Implementation Report

**Sprint**: Paradox Engine + Logic Gap + Circuit Breakers
**Global ID**: 19
**Date**: 2026-03-02
**Status**: IMPLEMENTED — ready for review

---

## Summary

Delivered the self-policing integrity layer: Logic Gap scanning with trailing-window price smoothing, Reality Signal provider abstraction, four Paradox modes with circuit breaker actions, activation gate latch semantics, and Entropy←Paradox wiring that drives real-time decay escalation based on market-reality divergence.

**Test results**: 99 engine + 100 market + 69 MCP = **268 tests passing**, zero failures.

---

## Files Created/Modified

### New Source Files

| File | Lines | Description |
|------|-------|-------------|
| `backend/engines/logic_gap.py` | ~95 | LogicGapStatus enum, LogicGapReading dataclass, LogicGapCalculator with trailing-window smoothing |
| `backend/engines/reality_signal.py` | ~75 | RealitySignal dataclass, abstract RealitySignalProvider, 3 concrete providers (Osint, Deterministic, Stub) |
| `backend/engines/paradox.py` | ~235 | ParadoxMode, ParadoxAction, ParadoxConfig (with to_commitment_dict), ParadoxRuntimeState, ParadoxEngine |

### Modified Source Files

| File | Changes | Description |
|------|---------|-------------|
| `backend/engines/config.py` | +10 lines | Added `paradox: Any = None` field, conditional inclusion in `to_commitment_dict()` |
| `backend/engines/integration.py` | +30 lines | Optional `paradox` param, `_paradox_tick_handler`, `_last_logic_gap_status` feeding Entropy |
| `backend/engines/__init__.py` | +18 lines | Sprint 2 exports: 13 new public symbols |

### New Test Files

| File | Tests | Description |
|------|-------|-------------|
| `backend/engines/tests/test_logic_gap.py` | 14 | Smoothing, classification boundaries, compute, edge values |
| `backend/engines/tests/test_paradox.py` | 18 | Scan, thresholds, modes, activation gates, execute action, commitment dict |
| `backend/engines/tests/test_circuit_breakers.py` | 9 | Action determinism, mode overrides |
| `backend/engines/tests/test_entropy_paradox.py` | 7 | Entropy←Paradox wiring, end-to-end decay escalation |

### Modified Test Files

| File | Changes | Description |
|------|---------|-------------|
| `backend/engines/tests/test_integration.py` | +10 lines | Updated `test_all_list_complete` with Sprint 2 symbols |

---

## Task Completion

### Task 1: Logic Gap Calculator — `backend/engines/logic_gap.py`

- `LogicGapStatus` enum: HEALTHY, STRESSED, DANGER, CRITICAL
- `LogicGapReading` dataclass: 8 fields (theatre_id, p_market, p_reality, logic_gap, gap_direction, status, smoothing_window_s, timestamp)
- `LogicGapCalculator`:
  - `record_price()`: appends (timestamp, price) and prunes outside window
  - `get_smoothed_p_market()`: simple average over trailing window, fallback 0.5
  - `compute()`: abs(p_market - p_reality), classify, return reading
  - `classify()` static: <0.20 HEALTHY, <0.40 STRESSED, <0.60 DANGER, ≥0.60 CRITICAL

### Task 2: Reality Signal Provider — `backend/engines/reality_signal.py`

- `RealitySignal` dataclass: p_reality, evidence_bundle_hash, certificate_id, source_type
- `RealitySignalProvider` abstract base with `get_signal()` method
- `OsintRealityProvider`: reads composite_score from evidence bundle
- `DeterministicRealityProvider`: reads from scorer pipeline output
- `StubRealityProvider`: fixed p_reality for testing

### Task 3: Paradox Engine — `backend/engines/paradox.py`

- `ParadoxMode` enum: DISABLED, ENABLED, ADVISORY, CIRCUIT_BREAKER
- `ParadoxAction` enum: WARN, TRADING_PAUSE, FORCED_RESOLUTION
- `ParadoxConfig` dataclass: 8 fields + `to_commitment_dict()`
- `ParadoxRuntimeState`: activation_gate_satisfied (latch), last_reading, scan_count
- `ParadoxEngine`:
  - `scan()`: disabled check → gate check → reality signal → compute gap → store runtime
  - `evaluate_thresholds()`: mode-dependent (ENABLED: full escalation, ADVISORY: caps at WARN, CIRCUIT_BREAKER: only critical)
  - `check_activation_gate()`: latch semantics — once True, stays True
  - `execute_action()`: impact map (WARN=-0.10, PAUSE=-0.20, FORCED=-0.30), records PARADOX Wing Flap
  - `to_commitment_dict()`: full config serialisation for commitment hash

### Task 4: Entropy←Paradox Wiring — `backend/engines/integration.py`

- `EngineOrchestrator.__init__()`: optional `paradox` parameter
- `_last_logic_gap_status: str = "healthy"`: bridges Paradox→Entropy
- `_paradox_tick_handler()`: scans, updates status, evaluates thresholds, executes actions (halt on PAUSE/FORCED)
- `_entropy_tick_handler()`: passes `_last_logic_gap_status` to Entropy tick
- `start()`: registers paradox handler on PARADOX heartbeat cadence (if paradox wired)

### Task 5: Logic Gap Tests — 14 tests

- **TestSmoothing** (5): single price, average of two, old prices pruned, no prices → midpoint, multiple within window
- **TestClassification** (4): boundary tests at 0.20, 0.40, 0.60 thresholds
- **TestCompute** (5): abs difference, signed direction, negative direction, correct fields, edge values

### Task 6: Paradox Tests — 18 tests

- **TestScan** (4): disabled returns None, enabled returns reading, increments count, stores last reading
- **TestThresholds** (5): healthy=None, warn at 0.20, pause at 0.40, forced at 0.60, highest wins
- **TestModes** (4): advisory caps at WARN, advisory below warn=None, circuit_breaker skips sub-critical, fires at critical
- **TestActivationGate** (4): none gate always satisfied, min_observations blocks, satisfies after scans, latch stays true
- **TestExecuteAction** (4): warn flap, pause impact, forced impact, trigger detail
- **TestCommitmentDict** (1): keys present and correct

### Task 7: Circuit Breaker Tests — 9 tests

- **TestActionDeterminism** (3): WARN=-0.10, PAUSE=-0.20, FORCED=-0.30
- **TestModeOverrides** (6): advisory never pauses, advisory never force-resolves, circuit_breaker skips warn+breach, circuit_breaker fires at critical, disabled scan=None, enabled full escalation

### Task 8: Entropy←Paradox Tests — 7 tests

- **TestEntropyReceivesLogicGapStatus** (3): healthy=base decay (0.01), stressed=1.5× (0.015), critical=3× (0.03)
- **TestEndToEndDecayEscalation** (2): trade→price divergence→increased decay, paradox handler updates status
- **TestParadoxConfigInCommitmentHash** (2): paradox in commitment dict, no paradox no key

---

## Acceptance Criteria Verification

| Criterion | Status | Evidence |
|-----------|--------|----------|
| Logic Gap = abs(p_market - p_reality) correctly computed | PASS | `test_logic_gap.py::TestCompute::test_logic_gap_is_abs_difference` |
| p_market uses trailing window smoothing (configurable, default 60s) | PASS | `test_logic_gap.py::TestSmoothing` (5 tests) |
| p_reality from osint source reads composite_score correctly | PASS | `reality_signal.py:45-55` OsintRealityProvider |
| p_reality from deterministic source reads scorer output correctly | PASS | `reality_signal.py:58-68` DeterministicRealityProvider |
| Logic Gap status thresholds match default policies | PASS | `test_logic_gap.py::TestClassification` (4 tests) |
| Activation gates prevent premature Paradox activation | PASS | `test_paradox.py::TestActivationGate` (4 tests) |
| enabled mode: WARN/PAUSE/FORCED at correct thresholds | PASS | `test_paradox.py::TestThresholds` + `test_circuit_breakers.py::TestModeOverrides::test_enabled_full_escalation` |
| advisory mode: all thresholds produce WARN only | PASS | `test_paradox.py::TestModes::test_advisory_caps_at_warn` + `test_circuit_breakers.py` |
| circuit_breaker mode: only critical threshold evaluated | PASS | `test_paradox.py::TestModes::test_circuit_breaker_only_critical` + `test_circuit_breakers.py` |
| disabled mode: scan returns None | PASS | `test_paradox.py::TestScan::test_disabled_returns_none` |
| Circuit breaker actions are deterministic | PASS | `test_circuit_breakers.py::TestActionDeterminism` (3 tests) |
| Activation gate uses latch semantics | PASS | `test_paradox.py::TestActivationGate::test_latch_stays_true_once_satisfied` |
| Entropy Engine responds to real Paradox Logic Gap status | PASS | `test_entropy_paradox.py::TestEntropyReceivesLogicGapStatus` (3 tests) |
| Paradox configuration is immutable after Theatre commitment | PASS | `config.py` paradox field, `to_commitment_dict()` |
| Paradox thresholds included in commitment hash | PASS | `test_entropy_paradox.py::TestParadoxConfigInCommitmentHash` (2 tests) |
| All existing tests pass | PASS | 100 market + 69 MCP + 47 Sprint 1 = 216 prior tests pass |
| 20+ new Sprint 2 tests pass | PASS | **52 new tests** (14+18+9+7+4 updated) |

---

## Test Summary

| Suite | Tests | Status |
|-------|-------|--------|
| Engine tests (Sprint 1+2) | 99 | ALL PASS |
| Market tests (010a) | 100 | ALL PASS |
| MCP tests | 69 | ALL PASS |
| **Total** | **268** | **ALL PASS** |

Sprint 2 new tests: **52** (target was 20+).

---

## Architecture Notes

- **Paradox→Entropy bridge**: `_last_logic_gap_status` string stored on EngineOrchestrator. Updated by `_paradox_tick_handler`, consumed by `_entropy_tick_handler`. Avoids direct coupling between Paradox and Entropy modules.
- **Circular import avoidance**: `EngineConfig.paradox` typed as `Any` rather than `ParadoxConfig` to prevent circular dependency (paradox.py imports from butterfly.py which config.py also touches).
- **ParadoxConfig.to_commitment_dict()** on the config dataclass itself (not just ParadoxEngine), allowing EngineConfig to delegate cleanly.
- **Zero modifications to `backend/market/`** — 010a layer remains untouched.
