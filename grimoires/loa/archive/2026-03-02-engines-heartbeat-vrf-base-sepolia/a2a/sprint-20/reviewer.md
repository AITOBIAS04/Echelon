# Sprint 3 (Global: 20) — Implementation Report

**Cycle**: 010b — Engines + Heartbeat + VRF + Base Sepolia
**Sprint**: 3 — VRF + Base Sepolia + MCP Status + FULL Mode
**Status**: IMPLEMENTED
**Date**: 2026-03-02

---

## Summary

Sprint 3 delivers fairness and auditability infrastructure: VRF-based randomness, on-chain proof publishing (Base Sepolia), market status snapshot assembly, and FULL mode quant template validation. All 11 tasks completed. 54 new tests passing (target: 25+). Zero modifications to `backend/market/`.

---

## Tasks Completed

### Task 1: VRF Provider — `backend/engines/vrf.py` (NEW, 99 lines)
- `VRFConfig`: committed parameters (provider, mode, seed) with `to_commitment_dict()`
- `VRFResult`: request_id, random_value (uint256), proof, verified, purpose
- `VRFProvider`: HMAC-SHA256 local mode, deterministic purpose-tagged output
- `scale_to_range()`: normalises uint256 to [min, max] float range
- Testnet mode raises `NotImplementedError` (Chainlink VRF V2 not wired)

### Task 2: VRF Wiring
- `backend/engines/config.py`: Added `vrf: Any = None` field, conditional `to_commitment_dict()` delegation
- `backend/engines/integration.py`: Added `vrf: VRFProvider | None = None` parameter to `EngineOrchestrator`
- `backend/engines/__init__.py`: Sprint 3 exports (VRFConfig, VRFResult, VRFProvider, MarketStatusSnapshot, market_status_snapshot)

### Task 3: Base Sepolia Client — `backend/chain/sepolia.py` (NEW, 151 lines)
- `TxReceipt`: tx_hash, block_number, gas_used, status
- `CommitmentRecord`: theatre_id, commitment_hash, block_number, timestamp
- `SettlementRecord`: theatre_id, settlement_hash, winning_outcome, block_number, timestamp
- `MockSepoliaClient`: in-memory mock with publish/verify round-trip for commitments and settlements
- `BaseSepoliaClient`: lazy web3 import, all methods raise `NotImplementedError`
- `backend/chain/__init__.py`: package exports

### Task 4: EchelonCommitment.sol — `smart-contracts/contracts/EchelonCommitment.sol` (NEW, ~52 lines)
- Minimal Solidity contract: `publishCommitment()`, `publishSettlement()`
- Events: `CommitmentPublished`, `SettlementPublished`
- Mappings: `commitments`, `settlements`, `winningOutcomes`
- No access control (testnet only)

### Task 5: Hardhat Deploy Script — `smart-contracts/scripts/deploy_echelon_commitment.js` (NEW, ~24 lines)
- Standard Hardhat deploy script for Base Sepolia

### Task 6: Market Status Snapshot — `backend/engines/status.py` (NEW, 73 lines)
- `MarketStatusSnapshot` dataclass: 10 fields assembling live state from all engines
- `market_status_snapshot()`: queries LMSR prices, Butterfly stability/flap_count, Heartbeat tick counts, Paradox logic gap (optional), on-chain commitment fields

### Task 7: FULL Mode Baselines — `theatre/fixtures/echelon_quant_v0_2/full_mode_baselines.json` (NEW)
- Suite metadata for all 4 quant template suites
- Engine configuration defaults (trade_impact_k=0.1, vrf_mode="local")
- Per-suite notes on FULL mode behavior

### Task 8: VRF Tests — `backend/engines/tests/test_vrf.py` (NEW, 15 tests)
- TestLocalDeterminism (4): same inputs, different seed, verified flag, request_id increments
- TestPurposeDifferentiation (2): different purpose, different theatre
- TestScaleToRange (5): zero→min, max→max, midpoint, equal range, within bounds
- TestVerify (1): local verify always true
- TestTestnetMode (2): testnet raises, None seed raises
- TestCommitmentDict (1): keys present

### Task 9: Chain Tests — `backend/chain/tests/test_sepolia.py` (NEW, 11 tests)
- TestMockPublishCommitment (4): receipt fields, round-trip, missing, overwrite
- TestMockPublishSettlement (3): receipt fields, round-trip, missing
- TestMockBlockCounter (2): increments, multiple theatres independent
- TestBaseSepoliaClient (2): ImportError without web3, package exports

### Task 10: Status + FULL Mode Tests
- `backend/engines/tests/test_status.py` (NEW, 8 tests): basic fields, flap count, stability, paradox reading, on-chain fields, heartbeat ticks
- `backend/engines/tests/test_full_mode_templates.py` (NEW, 11 tests): hygiene LMSR + engine tracking, b_sensitivity costs + engine tracking, API fidelity quotes + prices, perturbation fixtures + VRF seed, baselines file structure

### Task 11: E2E Lifecycle Test — `backend/engines/tests/test_e2e_engines.py` (NEW, 9 tests)
- TestFullLifecycle (2): trade→flap→status, multiple trades accumulate
- TestLifecycleWithVRF (3): determinism, scale_to_range, config in commitment hash
- TestLifecycleWithChain (2): commit/settle round-trip, status with on-chain fields
- TestLifecycleParadoxScan (2): scan after trade, all engines in commitment dict

---

## Test Results

| Suite | Count | Status |
|-------|-------|--------|
| Sprint 3 engine tests | 142 | ALL PASS |
| Sprint 3 chain tests | 11 | ALL PASS |
| Market regression (010a) | 100 | ALL PASS |
| MCP regression | 69 | ALL PASS |
| **Total** | **322** | **ALL PASS** |

**New Sprint 3 tests**: 54 (target: 25+)

---

## Files Created/Modified

### New Files (13)
| File | Lines | Purpose |
|------|-------|---------|
| `backend/engines/vrf.py` | 99 | VRF provider |
| `backend/chain/sepolia.py` | 151 | Base Sepolia client |
| `backend/chain/__init__.py` | 17 | Chain package exports |
| `backend/chain/tests/__init__.py` | 0 | Test package init |
| `backend/engines/status.py` | 73 | Market status snapshot |
| `smart-contracts/contracts/EchelonCommitment.sol` | ~52 | Solidity contract |
| `smart-contracts/scripts/deploy_echelon_commitment.js` | ~24 | Deploy script |
| `theatre/fixtures/echelon_quant_v0_2/full_mode_baselines.json` | 50 | FULL mode baselines |
| `backend/engines/tests/test_vrf.py` | ~110 | VRF tests (15) |
| `backend/chain/tests/test_sepolia.py` | ~100 | Chain tests (11) |
| `backend/engines/tests/test_status.py` | ~140 | Status tests (8) |
| `backend/engines/tests/test_full_mode_templates.py` | ~220 | FULL mode tests (11) |
| `backend/engines/tests/test_e2e_engines.py` | ~170 | E2E tests (9) |

### Modified Files (4)
| File | Change |
|------|--------|
| `backend/engines/config.py` | Added `vrf: Any = None` field, conditional VRF in `to_commitment_dict()` |
| `backend/engines/integration.py` | Added `vrf: VRFProvider | None = None` param to EngineOrchestrator |
| `backend/engines/__init__.py` | Added Sprint 3 exports (5 new symbols, 28 total) |
| `backend/engines/tests/test_integration.py` | Added Sprint 3 symbols to `test_all_list_complete` |

---

## Architecture Decisions

1. **HMAC-SHA256 for local VRF**: Deterministic, reproducible, no external dependencies. Purpose-tagged via `theatre_id:purpose` message.
2. **Lazy web3 import**: `BaseSepoliaClient` only imports web3 in constructor, avoiding hard dependency for test/local environments.
3. **MockSepoliaClient in-memory**: Zero dependencies, deterministic block counters, publish/verify round-trip for unit tests.
4. **Status snapshot function**: Pure function assembling state from injected dependencies. No singleton, no global state.
5. **`Any` type for VRF config**: Same circular-import avoidance pattern as ParadoxConfig in EngineConfig.

---

## Zero Backend/Market Modifications

Verified: no changes to any file under `backend/market/`. All 100 market tests pass unchanged.

---

## Acceptance Criteria Status

| Criterion | Status |
|-----------|--------|
| VRF local mode deterministic from fixed seed | PASS |
| VRF testnet mode raises NotImplementedError | PASS |
| Commitment hash publishable and readable (mock) | PASS |
| Settlement hash publishable and readable (mock) | PASS |
| `market_status_snapshot()` returns live state | PASS |
| `quant_market_hygiene_v1` passes in FULL mode | PASS |
| `quant_market_perturbation_harness_v1` passes in FULL mode | PASS |
| `quant_market_api_fidelity_v1` passes in FULL mode | PASS |
| `lmsr_b_sensitivity_suite_v1` passes in FULL mode | PASS |
| FULL mode baselines computed and pinned | PASS |
| E2E lifecycle with all engines active | PASS |
| All existing tests pass | PASS (100 market + 69 MCP) |
| 25+ new Sprint 3 tests | PASS (54 delivered) |
