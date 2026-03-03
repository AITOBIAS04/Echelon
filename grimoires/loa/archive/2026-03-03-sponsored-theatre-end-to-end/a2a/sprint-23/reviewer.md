# Implementation Report: Sprint 23 (Cycle-012, Sprint 1) — Theatre Creation + Sponsor Onboarding + LMSR Wiring

> Cycle: cycle-012 | Sprint: sprint-1 (global: sprint-23)
> Implementer: AI Engineer | Date: 2026-03-03

## Summary

All 10 tasks completed. Built 6 source files + 3 test files (53 tests, all passing). Zero modifications to existing `backend/market/`, `backend/engines/`, or `backend/osint/` modules. Full scoped regression (369 tests) passes with zero failures.

## Tasks Completed

### Task 1: SponsoredTheatreConfig model

**File**: `backend/schemas/sponsored_theatre.py` (NEW)

- `SponsoredTheatreConfig(BaseModel)`: Pydantic v2 model with 8 fields
  - `question` (str, 10-500 chars), `resolution_date` (datetime), `committed_sources` (list[str], min 1), `outcome_labels` (list[str], min 2, unique, max 10), `liquidity_b` (Decimal, > 0), `fee_schedule` (FeeSchedule), `sponsor_id` (str, min 1), `sponsor_metadata` (dict)
- `SponsorReviewPackage(BaseModel)`: 10 fields — theatre_id, template_json, commitment_hash, worst_case_loss, source_manifest, fee_schedule_breakdown, n_outcomes, outcome_labels, liquidity_b, resolution_date
- `@field_validator` for outcome_labels uniqueness and max 10 cap
- `model_config = ConfigDict(arbitrary_types_allowed=True)` for FeeSchedule
- `from __future__ import annotations` for Python 3.9.6

**AC Status**: All 8 acceptance criteria met.

### Task 2: Source manifest builder

**File**: `backend/osint/source_manifest.py` (NEW)

- `SettlementStatus` class with ELIGIBLE, PROVISIONAL, INELIGIBLE constants
- `SourceManifestEntry` dataclass: 8 fields (source_id, source_group, independence_upstream_id, jurisdiction, access_surface, settlement_status, settlement_eligible, display_name)
- `SourceManifest` dataclass: 4 fields (entries, registry_version, validated, validation_errors)
- `SourceManifestBuilder` class:
  - `build(source_ids)` validates against registry, determines settlement status, flags PROVISIONAL for shared upstream_id
  - `validate_sources(source_ids)` returns (bool, list[str]) validation result
- PROVISIONAL detection: sources sharing `independence_upstream_id` (e.g., all worldmonitor_* sources share "worldmonitor" upstream_id)
- Registry version pinned as "0.3.2-wm"
- No modifications to `backend/osint/` existing files

**AC Status**: All 9 acceptance criteria met.

### Task 3: Theatre creation service

**File**: `backend/services/sponsored_theatre.py` (NEW)

- `SponsoredTheatreService` class with `create()`, `review()`, `commit()` methods
- `create()` flow: validate sources -> build manifest -> create LMSR market via bridge -> build template JSON -> compute theatre commitment hash -> compute worst-case loss -> return SponsorReviewPackage
- `commit()` flow: verify hash determinism -> transition CREATED->COMMITTED->TRADING -> verify LMSR hash -> on-chain anchor -> return confirmation
- `TheatreRecord` dataclass for internal state tracking
- Theatre-level commitment hash: SHA-256 over canonical JSON of LMSR params + oracle config + theatre metadata
- Version pins: {"market": "010a", "engines": "010b", "osint": "011"}
- committed_sources sorted before hashing for determinism

**AC Status**: All 9 acceptance criteria met.

### Task 4: MarketTheatreBridge

**File**: `backend/services/market_theatre_bridge.py` (NEW)

- `TheatreMarketState` dataclass bundling MarketState + PositionManager + TradingEngine
- `MarketTheatreBridge` class:
  - `create_market_for_theatre()` delegates to MarketLifecycle.create_market()
  - `get_market_state()` returns TheatreMarketState or None
  - `transition_market()` handles CREATED->COMMITTED, COMMITTED->TRADING
  - `settle_market()` combines begin_resolution + settle in one call
  - `serialise_state()` / `deserialise_state()` for JSON roundtrip
- In-memory storage keyed by theatre_id
- No modifications to `backend/market/` files

**AC Status**: All 8 acceptance criteria met.

### Task 5: Stub agent spawner

**File**: `backend/services/stub_agents.py` (NEW)

- `AgentArchetype(str, Enum)`: SHARK, SPY, DIPLOMAT, SABOTEUR, WHALE, DEGEN
- `TradeIntent` dataclass: outcome_index, shares, trigger, confidence
- `TradeDecisionTrace` dataclass: full trace for RLMF export (agent_id, archetype, tick, trigger_condition, market_prices_at_decision, confidence, intent, executed_trade, pattern_name)
- `StubAgent` dataclass: agent_id, archetype, initial_balance, strategy
- `StubAgentSpawner.spawn()`: deterministic agent_ids ({theatre_id}_{archetype})
- `StubAgentSpawner.execute_tick()`: executes all agents, calls TradingEngine.execute_trade()
- Strategy functions with BEAUVOIR pattern names:
  - Shark (momentum_exploitation): buy leading if price < 0.7
  - Spy (intel_arbitrage): trade on evidence arrival
  - Diplomat (stability_maintenance): buy trailing if spread > 0.4
  - Saboteur (chaos_creation): random contrary 1-3 shares
  - Whale (market_moving): 50+ shares on tick 0 only
  - Degen (volatility_harvesting): random 1-10 shares every tick

**AC Status**: All 12 acceptance criteria met.

### Task 6: Sponsor review API endpoints

**File**: `backend/api/sponsored_theatre_routes.py` (NEW)

- FastAPI router with prefix `/api/v1/sponsored-theatres`, tags `["sponsored-theatres"]`
- `POST /` (201): creates Sponsored Theatre, returns {theatre_id, status, commitment_hash}
- `GET /{theatre_id}/review`: returns SponsorReviewPackage
- `POST /{theatre_id}/commit`: freezes parameters, returns {theatre_id, status, commitment_hash, tx_hash}
- Service injection via `set_service()` function
- Error handling: 400 for validation, 404 for not found, 409 for already committed, 503 for service not configured

**AC Status**: All 6 acceptance criteria met.

### Task 7: Commitment protocol integration

Integrated into Tasks 3 and 4:
- Theatre-level commitment hash covers: LMSR params (b, n_outcomes, outcome_labels, fee_schedule), oracle config (committed_sources sorted, resolution_date, corroboration_minimum), theatre metadata (template_id, version_pins)
- LMSR-level commitment hash via MarketCommitment.compute_hash() (unchanged)
- Both hashes stored independently — theatre hash in TheatreRecord, LMSR hash in MarketState
- `commit()` verifies theatre hash determinism and LMSR hash via `MarketCommitment.verify_hash()`
- On-chain anchor stubbed via MockSepoliaClient.publish_commitment()
- committed_sources sorted before hashing
- No modifications to `backend/market/commitment.py`

**AC Status**: All 8 acceptance criteria met.

### Task 8: Theatre creation tests

**File**: `backend/services/tests/test_sponsored_theatre.py` (NEW)

26 test cases across 4 test classes:
- `TestSponsoredTheatreConfig` (8 tests): valid config, duplicate labels, single outcome, empty sources, zero/negative b, short question, default fees
- `TestSourceManifest` (5 tests): valid manifest, nonexistent source, WM provisional flagging, independent source eligible, registry version
- `TestSponsoredTheatreCreation` (7 tests): valid creation, invalid sources, worst-case loss formula, manifest in review, commitment hash, hash determinism, sorted sources
- `TestCommitmentProtocol` (6 tests): commit transitions, LMSR hash verification, double commit rejection, review after create, nonexistent theatre, on-chain anchor

**AC Status**: All 6 acceptance criteria met. 26 tests (exceeds 10+ requirement).

### Task 9: LMSR-Theatre bridge tests

**File**: `backend/services/tests/test_market_theatre_bridge.py` (NEW)

9 test cases:
- Market creation with correct parameters
- Phase transition CREATED -> COMMITTED
- Phase transition COMMITTED -> TRADING
- Invalid phase transition raises exception
- Serialise/deserialise roundtrip
- Nonexistent theatre returns None
- Settle market (begin_resolution + settle)
- Serialise after transitions preserves phase
- Multiple theatres coexist in bridge

**AC Status**: All 5 acceptance criteria met. 9 tests (exceeds 6+ requirement).

### Task 10: Stub agent tests

**File**: `backend/services/tests/test_stub_agents.py` (NEW)

18 test cases across 8 test classes:
- `TestStubAgentSpawner` (4 tests): spawn 6 agents, deterministic IDs, default balance, custom balance
- `TestSharkStrategy` (2 tests): buys below threshold, no trade above threshold
- `TestSpyStrategy` (2 tests): trades with evidence, no trade without evidence
- `TestDiplomatStrategy` (1 test): buys trailing when spread > 0.4
- `TestSaboteurStrategy` (1 test): low volume contrary trades (1-3 shares)
- `TestWhaleStrategy` (2 tests): large position on tick 0, holds after
- `TestDegenStrategy` (2 tests): trades every tick, deterministic with fixed seed
- `TestExecuteTick` (4 tests): produces traces, executes trades, balance tracking, trace completeness

**AC Status**: All 6 acceptance criteria met. 18 tests (exceeds 9+ requirement).

## Test Results

### Sprint 1 tests: 53 passed, 0 failed

```
backend/services/tests/test_sponsored_theatre.py    — 26 passed
backend/services/tests/test_market_theatre_bridge.py — 9 passed
backend/services/tests/test_stub_agents.py           — 18 passed
```

### Scoped regression: 369 passed, 0 failed

```
backend/market/   — all tests pass
backend/engines/  — all tests pass
backend/osint/    — all tests pass
```

## Files Created

| File | Lines | Purpose |
|------|-------|---------|
| `backend/schemas/sponsored_theatre.py` | ~90 | Pydantic v2 config + review package models |
| `backend/osint/source_manifest.py` | ~145 | Source manifest builder and validation |
| `backend/services/sponsored_theatre.py` | ~235 | Theatre creation and commitment service |
| `backend/services/market_theatre_bridge.py` | ~175 | LMSR <-> Theatre bridge |
| `backend/services/stub_agents.py` | ~275 | Stub agent spawner with 6 archetypes |
| `backend/api/sponsored_theatre_routes.py` | ~95 | FastAPI endpoints |
| `backend/services/tests/__init__.py` | ~1 | Test package init |
| `backend/services/tests/test_sponsored_theatre.py` | ~280 | Theatre creation tests |
| `backend/services/tests/test_market_theatre_bridge.py` | ~160 | Bridge tests |
| `backend/services/tests/test_stub_agents.py` | ~290 | Stub agent tests |

## Files Modified

None. Zero modifications to existing modules.

## Key Constraints Verified

- [x] Python 3.9.6 — `from __future__ import annotations` in every new file
- [x] No new runtime dependencies — uses only Pydantic v2 (already available)
- [x] In-memory only — no persistence layer
- [x] Zero modifications to `backend/market/`
- [x] Zero modifications to `backend/engines/`
- [x] Zero modifications to `backend/osint/` existing files (new file only in `source_manifest.py`)
- [x] Pydantic v2 for sponsor-facing schemas, stdlib @dataclass for internal types
- [x] 53 new tests (exceeds 20+ target)
