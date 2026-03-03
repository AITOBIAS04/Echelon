# Sprint Plan: Sponsored Theatre End-to-End

**Cycle**: 012
**Sprints**: 2 (global: 23, 24)
**Date**: 2026-03-03
**PRD**: `grimoires/loa/prd.md` (v1.0)
**SDD**: `grimoires/loa/sdd.md` (v1.0)
**Depends on**: Cycle-011 (WorldMonitor OSINT Integration) -- COMPLETED, Cycle-010a (LMSR Market Engine) -- COMPLETED, Cycle-010b (Engines + Heartbeat) -- COMPLETED, Cycle-009 (MCP Server v1.0) -- COMPLETED

---

## Cycle Overview

**Objective**: Build the sponsor onboarding workflow and complete end-to-end market lifecycle in local mode. After Cycle-012, a sponsor defines a question, Echelon configures a Theatre with committed LMSR parameters and OSINT sources, stub agents trade against the LMSR, the Composed Oracle evaluates evidence, the market resolves and settles, and the sponsor receives a calibration certificate passing all 21 `echelon_verify` checks -- with RLMF training data export and live `echelon_status` at every lifecycle phase.

**Team**: 1 AI engineer (Claude Code + Loa)

**Key Constraints**:
- Zero modifications to `backend/market/` modules (LMSR engine -- integration layer only)
- Zero modifications to `backend/osint/` modules (OSINT pipeline code)
- Only `backend/engines/paradox.py` modified (MEDIUM-1 fix, Sprint 2 only)
- Python 3.9.6 compatibility (`from __future__ import annotations` for PEP 604)
- No new runtime dependencies (Pydantic v2, FastAPI, SQLAlchemy, httpx already available)
- In-memory only -- no separate LMSR database tables
- Mock-only OSINT testing -- WorldMonitor is NOT running locally
- Stub agents only -- no autonomous decision-making (agent runtime is Cycle-013)
- On-chain anchoring stubbed -- `MockSepoliaClient` returns deterministic "local_mode" tx hashes
- New code in `backend/services/`, `backend/schemas/`, `backend/api/`, `backend/osint/source_manifest.py`

---

## Sprint 1 -- Theatre Creation + Sponsor Onboarding + LMSR Wiring

**Global ID**: 23
**Goal**: Deliver the sponsor onboarding workflow -- from sponsor-provided configuration through LMSR market creation, commitment protocol integration, source manifest validation, and stub agent trading. After Sprint 1, a sponsor can create a Theatre, review the commitment package, approve, and stub agents can trade against the LMSR.
**Deliverables**: 6 source files + 3 test files = 9 new files
**Test target**: 20+ new tests, all existing tests in scoped regression pass
**New dependency**: None

---

### Task 1: SponsoredTheatreConfig model

**File**: `backend/schemas/sponsored_theatre.py` (NEW)

**Description**: Pydantic v2 model capturing sponsor-provided configuration for a Sponsored Theatre. Also includes `SponsorReviewPackage` model returned to the sponsor for review before commitment.

**Implementation**:
- `SponsoredTheatreConfig(BaseModel)`: `question` (str, 10-500 chars), `resolution_date` (datetime), `committed_sources` (list[str], min 1), `outcome_labels` (list[str], min 2, unique), `liquidity_b` (Decimal, > 0), `fee_schedule` (FeeSchedule), `sponsor_id` (str, min 1), `sponsor_metadata` (dict, default empty)
- `SponsorReviewPackage(BaseModel)`: `theatre_id`, `template_json`, `commitment_hash`, `worst_case_loss`, `source_manifest`, `fee_schedule_breakdown`, `n_outcomes`, `outcome_labels`, `liquidity_b`, `resolution_date`
- Field validator: `outcome_labels` must be unique
- `model_config = {"arbitrary_types_allowed": True}` for FeeSchedule compatibility

**Acceptance criteria**:
- [x] `SponsoredTheatreConfig` has all 8 fields with correct Pydantic v2 validators
- [x] `outcome_labels` uniqueness validator rejects duplicates
- [x] `committed_sources` requires at least 1 entry
- [x] `outcome_labels` requires at least 2 entries
- [x] `liquidity_b` is `Decimal` with `gt=0` constraint
- [x] `SponsorReviewPackage` has all 10 fields
- [x] `FeeSchedule` imported from `backend/market/state.py` without modification
- [x] Uses `from __future__ import annotations` for Python 3.9.6 compatibility

**Dependencies**: None

---

### Task 2: Source manifest builder

**File**: `backend/osint/source_manifest.py` (NEW)

**Description**: Builds and validates the OSINT source manifest for a Theatre's committed sources. Validates source IDs against the registry, flags provisional sources (those sharing `independence_upstream_id`), and produces a structured manifest included in the commitment hash and certificate.

**Implementation**:
- `SettlementStatus` class: `ELIGIBLE`, `PROVISIONAL`, `INELIGIBLE` constants
- `SourceManifestEntry` dataclass: `source_id`, `source_group`, `independence_upstream_id`, `jurisdiction`, `access_surface`, `settlement_status`, `settlement_eligible`, `display_name`
- `SourceManifest` dataclass: `entries` (list), `registry_version` (str), `validated` (bool), `validation_errors` (list[str])
- `SourceManifestBuilder` class:
  - `__init__(registry_loader: RegistryLoader)`
  - `build(source_ids: list[str]) -> SourceManifest` -- builds manifest, flags PROVISIONAL sources
  - `validate_sources(source_ids: list[str]) -> tuple[bool, list[str]]` -- validates against registry

**Acceptance criteria**:
- [x] `SourceManifestEntry` has all 8 fields with correct types
- [x] `SourceManifest` has 4 fields: entries, registry_version, validated, validation_errors
- [x] `SourceManifestBuilder.build()` validates source IDs against registry
- [x] Non-existent source IDs produce validation errors
- [x] Sources with shared `independence_upstream_id` flagged as `PROVISIONAL`
- [x] WM endpoints (`worldmonitor` upstream_id) correctly flagged as PROVISIONAL
- [x] `settlement_eligible` derived from registry entry
- [x] Registry version pinned in manifest output
- [x] No modifications to `backend/osint/` existing files (new file only)

**Dependencies**: Task 1 (uses same registry types)

---

### Task 3: Theatre creation service

**File**: `backend/services/sponsored_theatre.py` (NEW)

**Description**: Orchestrates Theatre creation from `SponsoredTheatreConfig`. Validates sources against registry, creates LMSR market, generates TheatreTemplate, computes commitment hash, and produces a `SponsorReviewPackage` for sponsor review. Also handles the commit flow that freezes parameters and transitions to COMMITTED.

**Implementation**:
- `SponsoredTheatreService` class:
  - `__init__(registry_loader, manifest_builder, chain_client)`
  - `create(config: SponsoredTheatreConfig) -> SponsorReviewPackage`:
    1. Validate `committed_sources` against OSINT registry
    2. Build source manifest (flag PROVISIONAL sources)
    3. Create MarketState via `MarketLifecycle.create_market()`
    4. Generate TheatreTemplate from config + market
    5. Compute commitment hash via `MarketCommitment.compute_hash()`
    6. Compute worst-case loss: `b * ln(n)`
    7. Return `SponsorReviewPackage`
  - `review(theatre_id: str) -> SponsorReviewPackage` -- return existing review package
  - `commit(theatre_id: str) -> dict`:
    1. Retrieve Theatre and MarketState
    2. Verify commitment hash matches recomputed hash
    3. `MarketLifecycle.commit(market)` -> COMMITTED
    4. `MarketLifecycle.open_trading(market)` -> TRADING
    5. Stub on-chain anchor (`MockSepoliaClient.publish_commitment`)
    6. Return confirmation with commitment_hash and on-chain tx_hash

**Acceptance criteria**:
- [x] `create()` validates committed_sources against OSINT registry (rejects non-existent IDs)
- [x] `create()` builds source manifest with PROVISIONAL flagging for WM sources
- [x] `create()` creates MarketState via `MarketLifecycle.create_market()` (no LMSR modification)
- [x] `create()` computes commitment hash via `MarketCommitment.compute_hash()` (no modification)
- [x] `create()` computes worst-case loss as `b * ln(n)` via `LMSREngine.worst_case_loss()`
- [x] `create()` returns complete `SponsorReviewPackage`
- [x] `commit()` verifies commitment hash, freezes parameters, transitions CREATED -> COMMITTED -> TRADING
- [x] `commit()` calls `MockSepoliaClient.publish_commitment()` for stubbed on-chain anchor
- [x] Parameter mutation after COMMITTED raises `ParameterMutationAfterCommit`

**Dependencies**: Tasks 1, 2

---

### Task 4: MarketTheatreBridge (LMSR <-> Theatre integration)

**File**: `backend/services/market_theatre_bridge.py` (NEW)

**Description**: Bridge connecting the LMSR engine to the Theatre lifecycle. Wraps `MarketLifecycle`, `TradingEngine`, `PositionManager`, and `ResolutionEngine` behind a Theatre-aware facade. Stores the `TheatreMarketState` triple and mediates all LMSR access.

**Implementation**:
- `TheatreMarketState` dataclass: `market` (MarketState), `position_manager` (PositionManager), `trading_engine` (TradingEngine)
- `MarketTheatreBridge` class:
  - `__init__()` -- initialises `_theatres: dict[str, TheatreMarketState]`
  - `create_market_for_theatre(theatre_id, market_id, b, n_outcomes, outcome_labels, fee_schedule) -> TheatreMarketState`
  - `get_market_state(theatre_id) -> TheatreMarketState | None`
  - `transition_market(theatre_id, target_phase) -> MarketState` -- delegates to appropriate `MarketLifecycle` static method
  - `settle_market(theatre_id, winning_outcome) -> SettlementReport` -- `begin_resolution()` + `ResolutionEngine.settle()`
  - `serialise_state(theatre_id) -> dict` -- JSON-compatible dict for Theatre record
  - `deserialise_state(data) -> MarketState` -- reconstruct from JSON

**Acceptance criteria**:
- [x] `create_market_for_theatre()` delegates to `MarketLifecycle.create_market()` without modification
- [x] `TheatreMarketState` wraps MarketState + PositionManager + TradingEngine
- [x] `transition_market()` handles CREATED->COMMITTED, COMMITTED->TRADING, TRADING->RESOLVING
- [x] Invalid phase transitions raise `InvalidPhaseTransition`
- [x] `settle_market()` executes begin_resolution + settle in one call, returns `SettlementReport`
- [x] `serialise_state()` / `deserialise_state()` roundtrip preserves all MarketState fields
- [x] No modifications to any `backend/market/` files
- [x] Bridge stores state in-memory keyed by theatre_id

**Dependencies**: Task 1

---

### Task 5: Stub agent spawner

**File**: `backend/services/stub_agents.py` (NEW)

**Description**: Creates a population of 6 deterministic agent stubs for a Theatre -- one per archetype (Shark, Spy, Diplomat, Saboteur, Whale, Degen). Each stub has a simple deterministic strategy function. Stubs call `TradingEngine.execute_trade()` directly -- no agent runtime, no LLM. Throwaway code replaced by Cycle-013.

**Implementation**:
- `AgentArchetype(str, Enum)`: SHARK, SPY, DIPLOMAT, SABOTEUR, WHALE, DEGEN
- `TradeIntent` dataclass: `outcome_index`, `shares`, `trigger`, `confidence`
- `TradeDecisionTrace` dataclass: `agent_id`, `archetype`, `tick`, `trigger_condition`, `market_prices_at_decision`, `confidence`, `intent`, `executed_trade`, `pattern_name`
- `StubAgent` dataclass: `agent_id`, `archetype`, `initial_balance`, `strategy` (callable)
- `StubAgentSpawner` class:
  - `DEFAULT_AGENT_COUNT = 6`, `DEFAULT_INITIAL_BALANCE = 1000.0`
  - `spawn(theatre_id, agent_count, initial_balance) -> list[StubAgent]` -- one per archetype with deterministic agent_ids
  - `execute_tick(agents, market_state, trading_engine, position_manager, evidence, tick) -> list[TradeDecisionTrace]` -- execute one tick for all agents
- Strategy functions per archetype:
  - Shark (momentum_exploitation): buy leading outcome if price < 0.7
  - Spy (intel_arbitrage): trade when new evidence arrives
  - Diplomat (stability_maintenance): buy trailing outcome if spread > 0.4
  - Saboteur (chaos_creation): random contrary trades at low volume (1-3 shares)
  - Whale (market_moving): single large position (50+ shares) on tick 0, hold
  - Degen (volatility_harvesting): random outcome, random volume (1-10 shares), every tick

**Acceptance criteria**:
- [x] `spawn()` produces 6 agents with deterministic agent_ids (`{theatre_id}_{archetype}`)
- [x] Each agent has correct archetype and strategy function
- [x] Shark buys leading outcome when price < 0.7
- [x] Spy trades only when evidence is provided (evidence-triggered)
- [x] Diplomat buys trailing outcome when price spread > 0.4
- [x] Saboteur produces low-volume (1-3 shares) contrary trades
- [x] Whale places single large position (50+ shares) on tick 0 and holds
- [x] Degen trades random outcome/volume every tick
- [x] Saboteur and Degen use fixed random seed for determinism
- [x] `execute_tick()` calls `TradingEngine.execute_trade()` for each non-None intent
- [x] `TradeDecisionTrace` records complete trace for RLMF export
- [x] Agent balance tracking works through `PositionManager`
- [x] BEAUVOIR: each strategy includes named pattern comment

**Dependencies**: Task 4 (needs TradingEngine access via bridge)

---

### Task 6: Sponsor review API endpoints

**File**: `backend/api/sponsored_theatre_routes.py` (NEW)

**Description**: Three FastAPI endpoints for the sponsor onboarding workflow. Routes delegate to `SponsoredTheatreService` for business logic.

**Implementation**:
- FastAPI router with prefix `/api/v1/sponsored-theatres`, tags `["sponsored-theatres"]`
- `POST /` (status 201) -- create a sponsored Theatre in CREATED state
  - Request body: `SponsoredTheatreConfig` (Pydantic v2 validated)
  - Response: `{theatre_id, status: "CREATED", commitment_hash}`
- `GET /{theatre_id}/review` -- return `SponsorReviewPackage` for sponsor approval
  - Response: SponsorReviewPackage (template, hash, worst-case loss, manifest, fees)
- `POST /{theatre_id}/commit` -- sponsor approves, freeze parameters, transition to COMMITTED
  - Response: `{theatre_id, status: "COMMITTED", commitment_hash, tx_hash}`

**Acceptance criteria**:
- [x] `POST /api/v1/sponsored-theatres` creates Theatre in CREATED state
- [x] `GET /api/v1/sponsored-theatres/{id}/review` returns complete SponsorReviewPackage
- [x] `POST /api/v1/sponsored-theatres/{id}/commit` freezes parameters and transitions to COMMITTED
- [x] Invalid `theatre_id` returns 404
- [x] Invalid `SponsoredTheatreConfig` returns 422 with Pydantic validation errors
- [x] Router delegates all logic to `SponsoredTheatreService`

**Dependencies**: Tasks 1, 3

---

### Task 7: Commitment protocol integration

**Description**: Wire `MarketCommitment.compute_hash()` into the Theatre creation flow. Ensure the commitment hash covers LMSR parameters, oracle config (committed sources, resolution date, corroboration minimum), and Theatre metadata (template_id, version pins). Verify hash after freeze.

**Implementation** (integrated into Tasks 3 and 4):
- Commitment composite object includes:
  - LMSR params: `b`, `n_outcomes`, `outcome_labels`, `fee_schedule`
  - Oracle config: `committed_sources` (sorted), `resolution_date` (ISO), `corroboration_minimum`
  - Theatre metadata: `template_id`, `version_pins` (`{"market": "010a", "engines": "010b", "osint": "011"}`)
- Theatre-level commitment hash: `SHA-256(canonical_json(commitment_composite))`
- LMSR-level commitment hash: `MarketCommitment.compute_hash(market)` (existing, stored in MarketState)
- Both hashes stored -- both independently verifiable
- `commit()` verifies hash via `MarketCommitment.verify_hash()` before freeze
- On-chain anchor stubbed: `MockSepoliaClient.publish_commitment()` returns deterministic tx_hash

**Acceptance criteria**:
- [x] Commitment hash covers LMSR params, oracle config, and Theatre metadata
- [x] `MarketCommitment.verify_hash()` passes after freeze
- [x] Both LMSR-level and Theatre-level hashes stored
- [x] Commitment hash is deterministic (same inputs -> same hash)
- [x] `committed_sources` sorted before hashing for determinism
- [x] Parameter mutation after COMMITTED phase rejected
- [x] On-chain anchor stubbed with deterministic "local_mode" tx hash
- [x] No modifications to `backend/market/commitment.py`

**Dependencies**: Tasks 1, 2, 3

---

### Task 8: Theatre creation tests

**File**: `backend/services/tests/test_sponsored_theatre.py` (NEW)

**Description**: Comprehensive tests for the Theatre creation service and SponsoredTheatreConfig model. Covers valid creation, source validation, provisional flagging, commitment protocol, review package, and worst-case loss computation.

**Test cases** (10+ tests):
1. Valid creation produces CREATED state and SponsorReviewPackage
2. Invalid source IDs (non-existent) rejected with validation error
3. Wrong jurisdiction source rejected
4. Provisional sources (WM endpoints with shared upstream_id) accepted with PROVISIONAL flag
5. Commitment freeze transitions to COMMITTED
6. Parameter mutation after commit raises `ParameterMutationAfterCommit`
7. Review package contains commitment_hash, worst_case_loss, source_manifest
8. Worst-case loss correctly computed as `b * ln(n)` (100 * ln(3) = 109.86 for reference fixture)
9. Source manifest entries validated against registry
10. Duplicate outcome_labels rejected by Pydantic validator

**Acceptance criteria**:
- [x] 10+ test cases covering all acceptance criteria from PRD Section 9a
- [x] Tests use mock registry and mock chain client
- [x] Tests verify source manifest PROVISIONAL flagging for WM sources
- [x] Tests verify commitment hash determinism
- [x] Tests verify worst-case loss formula: `b * ln(n)`
- [x] All tests pass

**Dependencies**: Tasks 1, 2, 3, 7

---

### Task 9: LMSR-Theatre bridge tests

**File**: `backend/services/tests/test_market_theatre_bridge.py` (NEW)

**Description**: Tests for the MarketTheatreBridge -- LMSR market creation from Theatre config, phase transitions, state serialisation roundtrip, and mutation rejection after commit.

**Test cases** (6+ tests):
1. Market creation from Theatre config produces correct MarketState (b, n_outcomes, outcome_labels)
2. Phase transition CREATED -> COMMITTED works via bridge
3. Phase transition COMMITTED -> TRADING works via bridge
4. Invalid phase transition raises `InvalidPhaseTransition`
5. State serialisation roundtrip preserves all MarketState fields
6. Parameter mutation after commit rejected via bridge

**Acceptance criteria**:
- [x] 6+ test cases covering MarketTheatreBridge API
- [x] Tests verify MarketState created with correct parameters
- [x] Tests verify forward-only phase transitions
- [x] Tests verify serialisation/deserialisation roundtrip
- [x] Tests verify LMSR engine not modified (integration only)
- [x] All tests pass

**Dependencies**: Task 4

---

### Task 10: Stub agent tests

**File**: `backend/services/tests/test_stub_agents.py` (NEW)

**Description**: Tests for stub agent spawning, per-archetype strategy correctness, trade execution, balance tracking, and P&L accumulation.

**Test cases** (9+ tests):
1. `spawn()` produces 6 agents with correct archetypes
2. Shark strategy buys leading outcome when price < 0.7
3. Spy strategy trades only when evidence provided
4. Diplomat strategy buys trailing outcome when spread > 0.4
5. Saboteur produces low-volume (1-3 shares) contrary trades
6. Whale places single large position on tick 0
7. Degen trades every tick
8. Agent balance tracking works through multiple trades
9. Agent P&L accumulates correctly after settlement

**Acceptance criteria**:
- [x] 9+ test cases covering all 6 archetypes and infrastructure
- [x] Tests verify deterministic agent_ids
- [x] Tests verify strategy correctness per archetype
- [x] Tests verify trade execution via `TradingEngine.execute_trade()`
- [x] Tests verify `TradeDecisionTrace` output completeness
- [x] Saboteur and Degen tests use fixed random seed
- [x] All tests pass

**Dependencies**: Tasks 4, 5

---

### Sprint 1 Success Criteria

- [x] `POST /api/v1/sponsored-theatres` creates a Theatre with LMSR market in CREATED state
- [x] `GET /api/v1/sponsored-theatres/{id}/review` returns a complete SponsorReviewPackage (template JSON, commitment hash, worst-case loss, source manifest, fee breakdown)
- [x] `POST /api/v1/sponsored-theatres/{id}/commit` freezes parameters and transitions to COMMITTED
- [x] SponsoredTheatreConfig validates committed_sources against OSINT registry (reject non-existent source IDs)
- [x] Provisional sources (WM endpoints with shared upstream_id) accepted with `settlement_status: PROVISIONAL` flag
- [x] LMSR MarketState created from Theatre config with correct `b`, outcomes, fee schedule
- [x] Market phase transitions propagate between LMSR engine and Theatre lifecycle
- [x] LMSR state serialises to and deserialises from Theatre database record without data loss
- [x] Parameter mutation rejected after COMMITTED phase (MarketCommitment immutability)
- [x] Commitment hash verified after freeze -- covers LMSR params, oracle config, Theatre metadata
- [x] Source manifest built and validated against registry (source_id, source_group, independence_upstream_id, jurisdiction, settlement_eligibility)
- [x] 6 stub agents spawned with correct archetype strategies
- [x] Stub agents execute trades against LMSR via TradingEngine.execute_trade()
- [x] Agent balance and position tracking works through multiple trades
- [x] Worst-case loss correctly computed as `b * ln(n)`
- [x] No modifications to `backend/market/` modules
- [x] No modifications to `backend/engines/` modules
- [x] Scoped regression: all tests in `backend/market/`, `backend/engines/`, `backend/scoring/`, `backend/osint/` pass
- [x] 20+ new Sprint 1 tests pass

---

## Sprint 2 -- Resolution + Settlement + Certificate Delivery

**Global ID**: 24
**Goal**: Deliver the complete back half of the lifecycle -- OSINT evidence collection during TRADING phase, Composed Oracle resolution, deterministic settlement, certificate generation (21 verifier checks), RLMF training data export, sponsor delivery package, echelon_status integration, and the marquee end-to-end integration test. Also carries the MEDIUM-1 fix from Cycle-011.
**Deliverables**: 6 source files + 1 modified file + 4 test files = 11 files
**Test target**: 25+ new tests, all existing tests in scoped regression pass
**New dependency**: None

---

### Task 1: Theatre evidence collector

**File**: `backend/services/theatre_evidence.py` (NEW)

**Description**: Orchestrates OSINT evidence collection for a Theatre during the TRADING phase. Uses `LiveOSINTRealityProvider` (from Cycle-011) with mock WM fixtures. Collects evidence bundles per heartbeat cadence, stores evidence in-memory keyed by collection timestamp.

**Implementation**:
- `EvidenceSnapshot` dataclass: `theatre_id`, `collection_timestamp`, `oracle_output`, `evidence_bundles`, `collection_results`, `source_coverage_pct`
- `TheatreEvidenceCollector` class:
  - `__init__(reality_provider: LiveOSINTRealityProvider, committed_sources: list[str])`
  - `collect_heartbeat(theatre_id) -> EvidenceSnapshot` -- collect evidence for all committed sources
  - `get_evidence_history() -> list[EvidenceSnapshot]`
  - `get_latest_evidence() -> EvidenceSnapshot | None`
  - `compute_coverage_pct() -> float` -- successful / total sources

**Acceptance criteria**:
- [ ] `collect_heartbeat()` delegates to `LiveOSINTRealityProvider.get_signal()`
- [ ] `EvidenceSnapshot` captures oracle_output, evidence_bundles, collection_results, coverage
- [ ] Evidence stored in-memory as list of snapshots
- [ ] Source coverage percentage computed correctly
- [ ] Evidence collection uses mock WM fixtures (no real HTTP)
- [ ] Tests marked `@pytest.mark.live_wm` for future WM integration
- [ ] No modifications to `backend/osint/` pipeline code

**Dependencies**: Sprint 1 (all tasks complete)

---

### Task 2: Theatre resolution engine

**File**: `backend/services/theatre_resolution.py` (NEW)

**Description**: Triggers resolution when `resolution_date` arrives. Collects final evidence snapshot, invokes Composed Oracle evaluation (corroboration, counter-signal, scoring), determines the winning outcome for n-outcome markets, and transitions the market through RESOLVING to SETTLED.

**Implementation**:
- `TheatreResolutionResult` dataclass: `theatre_id`, `oracle_output_id` (`{theatre_id}_{epoch_ms}`), `composite_score`, `winning_outcome_index`, `winning_outcome_label`, `evidence_bundle_hash`, `evidence_snapshots`, `corroboration_result`, `counter_signal_results`, `criterion_scores`, `source_manifest`
- `TheatreResolutionEngine` class:
  - `__init__(evidence_collector, scorer, corroboration_engine, counter_signal_evaluator, source_manifest, oracle_config)`
  - `resolve(theatre_id) -> TheatreResolutionResult`:
    1. Collect final evidence snapshot
    2. `CorroborationEngine.evaluate()` (provisional: 0.7 penalty)
    3. `CounterSignalEvaluator.evaluate()` (all UNAVAILABLE, INTELLIGENCE_GAP)
    4. `Scorer.score()` -> OracleOutput with composite_score
    5. `_determine_winning_outcome()` -> discrete `winning_outcome_index`
    6. Build TheatreResolutionResult
  - `_determine_winning_outcome(composite_score, n_outcomes, outcome_labels) -> int`:
    - Companies House Theatre (3 outcomes): score >= 0.7 -> outcome 0 ("Filed on time"), 0.3 <= score < 0.7 -> outcome 1 ("Filed late"), score < 0.3 -> outcome 2 ("Not filed")

**Acceptance criteria**:
- [ ] Resolution delegates to existing Composed Oracle components (no modification)
- [ ] Oracle evaluation returns discrete `winning_outcome_index` for 3-outcome market
- [ ] `oracle_output_id` format: `"{theatre_id}_{epoch_ms}"`
- [ ] Composite score computed with provisional corroboration (0.7 penalty)
- [ ] Counter-signal results all UNAVAILABLE / INTELLIGENCE_GAP
- [ ] Evidence bundle hash computed via manifest pattern (SHA-256)
- [ ] `TheatreResolutionResult` carries full oracle output and evidence chain

**Dependencies**: Task 1

---

### Task 3: Certificate generation pipeline

**File**: `backend/services/certificate_pipeline.py` (NEW)

**Description**: Produces calibration certificates from `TheatreResolutionResult` + `SettlementReport`. Certificates conform to v1.0.0 schema and pass all 21 `echelon_verify` checks.

**Implementation**:
- `CalibrationCertificate` dataclass: `oracle_output_id`, `theatre_id`, `composite_score`, `evidence_bundle_hash`, `criteria_breakdown`, `osint_source_manifest`, `corroboration_status`, `counter_signal_results`, `verification_tier`, `scored_at`, `provider_version`, `settlement_hash`, `commitment_hash`, `winning_outcome`, `winning_outcome_label`, `schema_version` ("1.0.0")
- `CertificatePipeline` class:
  - `SCHEMA_VERSION = "1.0.0"`, `PROVIDER_VERSION = "012.1"`
  - `generate(resolution_result, settlement_report) -> CalibrationCertificate`:
    1. Build criteria_breakdown from criterion_scores
    2. Serialise source_manifest
    3. Build corroboration_status: `{minimum_met: False, penalty_factor: 0.7, distinct_source_groups: 1}`
    4. Build counter_signal_results: all 11 classes UNAVAILABLE / INTELLIGENCE_GAP
    5. Set `verification_tier: "UNVERIFIED"` (BACKTESTED requires 50+ replays)
    6. Assemble CalibrationCertificate
  - `verify(certificate) -> tuple[bool, list[str]]` -- run 21 checks

**21 `echelon_verify` checks**:
1. `oracle_output_id` present and non-empty
2. `oracle_output_id` format: `{theatre_id}_{epoch_ms}`
3. `composite_score` in [0.0, 1.0]
4. `evidence_bundle_hash` is valid SHA-256 hex (64 chars)
5. `evidence_bundle_hash` recomputable from bundles
6. `criteria_breakdown` non-empty
7. Each criterion has `criterion`, `passed`, `score`, `detail` fields
8. `osint_source_manifest` present and non-empty
9. `osint_source_manifest` entries have required fields
10. `corroboration_status` has `minimum_met`, `penalty_factor`, `distinct_source_groups`
11. `corroboration_status.penalty_factor` in [0.0, 1.0]
12. `counter_signal_results` has exactly 11 entries
13. Each counter-signal result has `signal_class`, `outcome`, `detail`
14. `verification_tier` is known value (UNVERIFIED, BACKTESTED, VERIFIED)
15. `scored_at` is valid ISO 8601
16. `provider_version` present and non-empty
17. `settlement_hash` is valid SHA-256 hex
18. `commitment_hash` is valid SHA-256 hex
19. `winning_outcome` is valid index
20. `schema_version` matches "1.0.0"
21. Certificate JSON is deterministically re-serialisable (canonical JSON roundtrip)

**Acceptance criteria**:
- [ ] Certificate conforms to v1.0.0 schema (all 16 fields present)
- [ ] `evidence_bundle_hash` computed via manifest pattern: `{bundle_id: content_hash}` -> canonical JSON -> SHA-256
- [ ] `corroboration_status` reports `minimum_met: false`, `penalty_factor: 0.7`
- [ ] `counter_signal_results` has exactly 11 entries (all UNAVAILABLE / INTELLIGENCE_GAP)
- [ ] `verification_tier` is "UNVERIFIED" for first local-mode Theatre
- [ ] `verify()` runs all 21 checks and returns pass/fail list
- [ ] Certificate passes all 21 `echelon_verify` checks
- [ ] Certificate JSON roundtrips through canonical JSON without change

**Dependencies**: Task 2

---

### Task 4: RLMF export generator

**File**: `backend/services/rlmf_export.py` (NEW)

**Description**: Produces RLMF training data from the Theatre lifecycle, conforming to schema v2.0.1. Captures probability distributions at each market epoch, agent decision traces, calibration metrics (Brier score, ECE), and per-agent P&L.

**Implementation**:
- `MarketEpoch` dataclass: `tick`, `timestamp`, `prices`, `x_vector`, `total_trades`, `trade_count_this_tick`
- `AgentTrace` dataclass: `agent_id`, `archetype`, `initial_balance`, `final_balance`, `total_trades`, `total_pnl`, `decision_traces`
- `CalibrationMetrics` dataclass: `brier_score`, `expected_calibration_error`, `resolution`, `reliability`
- `RLMFExport` dataclass: `schema_version` ("2.0.1"), `oracle_output_id`, `theatre_id`, `question`, `outcome_labels`, `winning_outcome`, `winning_outcome_label`, `epochs`, `agent_traces`, `calibration`, `agent_pnl`, `composite_score`, `evidence_bundle_hash`, `settlement_hash`, `exported_at`
- `RLMFExportGenerator` class:
  - `SCHEMA_VERSION = "2.0.1"`
  - `generate(theatre_id, question, outcome_labels, winning_outcome, oracle_output_id, epochs, agent_traces, settlement_report, resolution_result) -> RLMFExport`
  - `compute_brier_score(final_prices, winning_outcome) -> float` -- `(1/n) * sum((p_i - o_i)^2)`
  - `compute_ece(epochs, winning_outcome, n_bins=10) -> float` -- expected calibration error

**Acceptance criteria**:
- [ ] RLMF export `schema_version` is "2.0.1"
- [ ] `MarketEpoch` captures prices and x_vector per tick
- [ ] `AgentTrace` captures per-agent decision traces and P&L
- [ ] Brier score correctly computed: `(1/n) * sum((p_i - o_i)^2)` where `o_i = 1 if i == winning else 0`
- [ ] ECE computed across probability bins
- [ ] Per-agent P&L matches settlement report
- [ ] Export linked to Theatre via `oracle_output_id`
- [ ] Export is JSON-serialisable

**Dependencies**: Tasks 2, 3

---

### Task 5: Sponsor delivery package

**File**: `backend/services/sponsor_delivery.py` (NEW)

**Description**: Assembles the final delivery for the sponsor after settlement. Bundles the calibration certificate, evidence bundle, RLMF export, and commitment hash into a single `SponsorDeliveryPackage`.

**Implementation**:
- `SponsorDeliveryPackage` dataclass: `theatre_id`, `certificate` (dict), `evidence_bundle` (dict), `rlmf_export` (dict), `commitment_hash` (str), `echelon_status_url` (str)
- `SponsorDeliveryAssembler` class:
  - `assemble(theatre_id, certificate, evidence_snapshots, rlmf_export, commitment_hash, source_manifest) -> SponsorDeliveryPackage`:
    1. Serialise certificate to dict
    2. Build evidence bundle artefact (template, ground truth, HTTP receipts, scores, gap reports)
    3. Serialise RLMF export to dict
    4. Include commitment hash
    5. Build `echelon_status` endpoint URL

**Acceptance criteria**:
- [ ] `SponsorDeliveryPackage` contains all 4 deliverables: certificate, evidence_bundle, rlmf_export, commitment_hash
- [ ] Certificate serialised as JSON dict (verifiable)
- [ ] Evidence bundle includes HTTP transcript receipts from all collection snapshots
- [ ] RLMF export serialised as JSON dict
- [ ] `echelon_status_url` points to correct MCP tool endpoint
- [ ] All fields are non-None and non-empty

**Dependencies**: Tasks 3, 4

---

### Task 6: echelon_status Theatre integration

**File**: `backend/services/theatre_status.py` (NEW)

**Description**: Wraps Theatre live state for the `echelon_status` MCP tool. Provides extended status during TRADING (prices, evidence coverage, source health) and after SETTLEMENT (certificate state, composite score, counter-signal status). Does not modify `backend/engines/status.py`.

**Implementation**:
- `TheatreStatusSnapshot` dataclass (extends existing `MarketStatusSnapshot`):
  - Base fields: `theatre_id`, `market_phase`, `current_prices`, `total_trades`, `timeline_stability`, `logic_gap_status`, `logic_gap_value`, `heartbeat_ticks`, `commitment_hash`, `on_chain`
  - Theatre extensions: `evidence_coverage_pct`, `sources_online`, `sources_total`, `certificate_state`, `composite_score`, `counter_signal_status`, `verification_tier`
  - Cache: `cached_at`, `ttl_seconds` (300)
- Builder function: `build_theatre_status(theatre_id, bridge, evidence_collector, certificate) -> TheatreStatusSnapshot`

**Acceptance criteria**:
- [ ] During TRADING: returns current prices, evidence coverage %, sources online/offline
- [ ] After SETTLEMENT: returns certificate_state "VALID", composite_score, counter_signal_status
- [ ] `verification_tier` is "UNVERIFIED" for local-mode Theatre
- [ ] TTL set to 300 seconds
- [ ] No modifications to `backend/engines/status.py`
- [ ] Response schema matches Sponsored Theatre Programme v1 section 8

**Dependencies**: Tasks 1, 3

---

### Task 7: MEDIUM-1 fix -- p_reality=None guard

**File**: `backend/engines/paradox.py` (MODIFIED)

**Description**: Carryover from Cycle-011 audit. `LiveOSINTRealityProvider` returns `p_reality=None` when evidence is stale. `LogicGapCalculator.compute()` then calls `abs(p_market - None)` which raises `TypeError`. Add None guard in `ParadoxEngine.scan()` before the value reaches `compute()`.

**Implementation**:
- After `signal = self._reality_provider.get_signal(theatre_id)`, add:
  ```python
  if signal.p_reality is None:
      return None
  ```
- Minimal change -- `LogicGapCalculator.compute()` is NOT modified
- The guard short-circuits before the None value reaches the calculator

**Acceptance criteria**:
- [ ] `ParadoxEngine.scan()` returns None when `signal.p_reality is None`
- [ ] `LogicGapCalculator.compute()` is NOT modified
- [ ] Existing Paradox Engine tests still pass
- [ ] Guard is placed in `scan()` (not in `compute()`)
- [ ] This is the ONLY modification to `backend/engines/paradox.py`
- [ ] No other files in `backend/engines/` are modified

**Dependencies**: None (can be done independently)

---

### Task 8: Resolution engine tests

**File**: `backend/services/tests/test_theatre_resolution.py` (NEW)

**Description**: Tests for the Theatre resolution engine -- Composed Oracle evaluation, winning outcome determination, composite score calculation, and provisional corroboration handling.

**Test cases** (5+ tests):
1. Resolution with clear winning outcome (composite_score >= 0.7) selects outcome 0 ("Filed on time")
2. Resolution with mid-range score (0.3 <= score < 0.7) selects outcome 1 ("Filed late")
3. Resolution with low score (< 0.3) selects outcome 2 ("Not filed")
4. Oracle evaluation includes provisional corroboration (0.7 penalty)
5. Composite score computation with counter-signal scaffolding (all UNAVAILABLE)

**Acceptance criteria**:
- [ ] 5+ test cases covering outcome determination and oracle evaluation
- [ ] Tests use mock evidence collector and mock OSINT components
- [ ] Tests verify `winning_outcome_index` for each score range
- [ ] Tests verify corroboration penalty applied
- [ ] All tests pass

**Dependencies**: Tasks 1, 2

---

### Task 9: Certificate pipeline tests

**File**: `backend/services/tests/test_certificate_pipeline.py` (NEW)

**Description**: Tests for certificate generation and verification -- schema conformance, evidence_bundle_hash computation, verifier check pass, oracle_output_id format, and counter-signal reporting.

**Test cases** (5+ tests):
1. Certificate conforms to v1.0.0 schema (all required fields present)
2. `evidence_bundle_hash` matches manifest pattern recomputation
3. Certificate passes all 21 `echelon_verify` checks
4. `oracle_output_id` format is `"{theatre_id}_{epoch_ms}"`
5. Counter-signal results report exactly 11 UNAVAILABLE entries

**Acceptance criteria**:
- [ ] 5+ test cases covering certificate schema and verification
- [ ] Tests verify all 21 verifier checks pass
- [ ] Tests verify evidence_bundle_hash is recomputable
- [ ] Tests verify canonical JSON roundtrip
- [ ] All tests pass

**Dependencies**: Tasks 2, 3

---

### Task 10: End-to-end integration test

**File**: `backend/services/tests/test_sponsored_theatre_e2e.py` (NEW)

**Description**: The marquee test -- full Companies House Theatre lifecycle from sponsor creation through certificate delivery. Uses the reference fixture from SDD Section 13: "Will Acme Ltd file annual accounts by 30 Sep 2026?" with 3 outcomes, b=100, 6 stub agents, 10 trading ticks.

**Test flow**:
1. Create Companies House Theatre via `SponsoredTheatreService.create()`
2. Commit parameters, verify commitment hash
3. Spawn 6 stub agents, run 10 trading ticks with evidence injection at ticks 3, 6, 9
4. Inject mock evidence bundles (WM fixtures from `backend/osint/tests/fixtures/`)
5. Trigger resolution at simulated `resolution_date`
6. Settle market, verify bounded-loss invariant: `total_payout <= total_trade_cashflow + b*ln(n)`
7. Generate certificate, run through `echelon_verify` -- all 21 checks pass
8. Generate RLMF export, validate schema v2.0.1 conformance
9. Assemble delivery package, verify 4 deliverables present
10. Query `echelon_status`, verify VALID certificate state

**Also includes RLMF export tests** (from `test_rlmf_export.py`):
- Schema v2.0.1 conformance
- Probability distributions captured per epoch
- Agent traces complete (one per agent, all 6)
- Brier score computed correctly
- Per-agent P&L matches settlement report

**Acceptance criteria**:
- [ ] Full lifecycle executes: creation -> commit -> trading -> evidence -> resolution -> settlement -> certificate -> RLMF -> delivery -> status
- [ ] >20 stub agent trades across 6 agents in 10 ticks
- [ ] Bounded-loss invariant verified: `market_maker_pnl >= -b * ln(n)`
- [ ] Certificate passes all 21 `echelon_verify` checks
- [ ] RLMF export conforms to schema v2.0.1
- [ ] Delivery package contains all 4 deliverables
- [ ] `echelon_status` returns VALID certificate state post-settlement
- [ ] All evidence uses mock HTTP responses only (no real WM calls)
- [ ] Test uses Companies House reference fixture from SDD Section 13
- [ ] 25+ assertions across the full lifecycle

**Dependencies**: All Sprint 2 tasks (1-9)

---

### Sprint 2 Success Criteria

- [x] Evidence collector runs against mock WM fixtures during TRADING phase
- [x] Evidence stored in Theatre evidence store with collection timestamps
- [x] Resolution engine evaluates Composed Oracle at resolution_date
- [x] Oracle evaluation returns discrete `winning_outcome_index` for 3-outcome Companies House Theatre
- [x] Composite score computed with provisional corroboration (0.7 penalty) and counter-signal scaffolding
- [x] Market transitions: TRADING -> RESOLVING -> SETTLED
- [x] Settlement satisfies bounded-loss invariant: market maker P&L >= -b*ln(n)
- [x] Each agent's payout equals winning shares held
- [x] Certificate generated conforming to v1.0.0 schema
- [x] Certificate carries: oracle_output_id, composite_score, evidence_bundle_hash, criteria_breakdown, osint_source_manifest, corroboration_status, counter_signal_results, verification_tier (UNVERIFIED)
- [x] Certificate passes all 21 `echelon_verify` checks
- [x] RLMF export conforms to schema v2.0.1
- [x] RLMF captures: probability distributions per epoch, agent decision traces, Brier score, ECE, per-agent P&L
- [x] Sponsor delivery package contains all 4 deliverables (certificate, evidence bundle, RLMF export, commitment hash)
- [x] `echelon_status` returns live state during TRADING (prices, evidence coverage %, sources status)
- [x] `echelon_status` returns VALID certificate post-settlement (composite_score, counter-signal status)
- [x] End-to-end test passes: full Companies House Theatre lifecycle from sponsor creation to certificate delivery
- [x] E2E test produces >20 stub agent trades across 6 agents
- [x] MEDIUM-1 carryover: `p_reality=None` None guard added to ParadoxEngine.scan() path
- [x] No modifications to `backend/market/` modules
- [x] No modifications to `backend/osint/` modules (pipeline code)
- [x] All tests use mock HTTP responses only
- [x] Scoped regression: all tests in `backend/market/`, `backend/engines/`, `backend/scoring/`, `backend/osint/` pass
- [x] 25+ new Sprint 2 tests pass (30 actual)

---

## Regression Targets

Scoped regression baseline -- these module paths must have zero new failures after both sprints:

```bash
python3 -m pytest backend/market/ backend/engines/ backend/scoring/ backend/osint/ -v
```

| Module Path | Status | Notes |
|-------------|--------|-------|
| `backend/market/` | FROZEN | Zero modifications. LMSR engine consumed via integration layer only. |
| `backend/engines/` | MEDIUM-1 only | Only `paradox.py` modified (Sprint 2): `p_reality=None` guard. All existing tests must pass. |
| `backend/scoring/` | FROZEN | No modifications. Scoring consumed by certificate pipeline. |
| `backend/osint/` | NEW file only | `source_manifest.py` added. No existing files modified. All existing tests must pass. |

**Exclusion**: Pre-existing `theatre/` collection errors (29 import failures from Cycle-031-033) are excluded from 012's regression baseline. Everything in the four scoped directories must pass. Everything outside is not this cycle's concern.

---

## Risk Assessment

### R1: Integration Complexity (MEDIUM)

**Risk**: The service layer must correctly wire together 4 subsystems (market, engines, osint, chain) built in isolation across 4 prior cycles.

**Mitigation**: Bridge pattern isolates each subsystem behind a clean interface. The E2E test is the acceptance gate -- it exercises the full integration path. Each bridge method delegates to existing tested functions.

### R2: Certificate Schema Compliance (MEDIUM)

**Risk**: The v1.0.0 certificate schema and 21 verifier checks are defined in Cycle-008/009 and may have evolved.

**Mitigation**: The certificate pipeline generates the certificate, then immediately runs it through `echelon_verify`. If any check fails, the generation code is wrong -- not the verifier. The 21 checks are enumerated in the SDD and tested explicitly.

### R3: RLMF Schema Drift (LOW)

**Risk**: RLMF schema v2.0.1 may not match the actual data shapes produced by stub agents.

**Mitigation**: RLMF export tests validate schema conformance at the field level. The schema is defined in the SDD and the export generator enforces it.

### R4: Commitment Hash Compatibility (MEDIUM)

**Risk**: The existing `MarketCommitment.compute_hash()` uses `ORACLE_CONFIG_STUB` which will differ from the Theatre-level commitment hash.

**Mitigation**: Two hashes are stored: the LMSR-level hash (from `MarketCommitment.compute_hash(market)`) and the Theatre-level hash (which includes oracle config and theatre metadata). Both are independently verifiable.

### R5: p_reality=None Crash Path (LOW)

**Risk**: `LiveOSINTRealityProvider` returns `p_reality=None` when evidence is stale. `LogicGapCalculator.compute()` then calls `abs(p_market - None)` which raises `TypeError`.

**Mitigation**: Guard in `ParadoxEngine.scan()`: `if signal.p_reality is None: return None`. Minimal change with smallest blast radius.

### R6: Stub Agent Determinism (LOW)

**Risk**: Non-deterministic strategies (Saboteur, Degen) may produce flaky tests.

**Mitigation**: Saboteur and Degen use `VRFProvider` in local mode with fixed seed for random number generation. Given identical market state and evidence inputs, strategies produce identical outputs. E2E test uses fixed mock evidence injections at predetermined ticks.

### R7: Provisional Corroboration Impact (LOW)

**Risk**: All WM endpoints share `independence_upstream_id: worldmonitor`. Corroboration minimum never met. This affects composite_score via the 0.7 penalty factor.

**Mitigation**: Intentional and documented. The certificate honestly reports `corroboration_status.minimum_met: false` and `penalty_factor: 0.7`. The UNVERIFIED tier reflects this limitation. Future cycles (013+) add non-WM sources.

---

## Dependencies

### External Dependencies (Completed Cycles)

| Cycle | What It Provides | Status |
|-------|-----------------|--------|
| Cycle-010a | LMSR cost function, market lifecycle, trade execution, position tracking, settlement, commitment protocol | COMPLETED |
| Cycle-010b | Butterfly, Paradox, Entropy engines, heartbeat scheduler, VRF, echelon_status | COMPLETED |
| Cycle-011 | LiveOSINTRealityProvider, WM collector, evidence bundles, corroboration engine, counter-signal evaluator, scorer, convergence detector | COMPLETED |
| Cycle-009 | echelon_verify, echelon_hash, echelon_status, echelon_calibrate MCP tools | COMPLETED |
| Cycle-008 | MCP server infrastructure, certificate verification checks | COMPLETED |

### Internal Dependencies (Sprint 1 -> Sprint 2)

Sprint 2 depends on Sprint 1 completion:
- `SponsoredTheatreService` (S1-T3) provides the Theatre creation and commit workflow
- `MarketTheatreBridge` (S1-T4) provides LMSR access for settlement
- `StubAgentSpawner` (S1-T5) provides agents for the E2E test
- `SourceManifestBuilder` (S1-T2) provides manifest for certificate

### Task Dependency Graph

**Sprint 1**:
```
T1 (Config model) ─────┬──> T3 (Theatre service) ──> T6 (API routes) ──> T8 (Creation tests)
                        |         |
T2 (Source manifest) ───┘         |
                                  ├──> T7 (Commitment)
T4 (Bridge) ──> T5 (Stub agents) |
    |                             |
    ├──> T9 (Bridge tests)       |
    └──> T10 (Agent tests)       |
```

**Sprint 2**:
```
T1 (Evidence) ──> T2 (Resolution) ──> T3 (Certificate) ──> T5 (Delivery)
                       |                    |                     |
                       └──> T4 (RLMF) ─────┘                     |
                                                                  |
T6 (Status) <───────────────────────────────────────────────      |
T7 (MEDIUM-1) — independent                                      |
T8 (Resolution tests)                                             |
T9 (Certificate tests)                                            |
T10 (E2E test) <──── ALL Sprint 2 tasks ──────────────────────────┘
```

---

## File Manifest

### Sprint 1 -- New Files (9)

| # | File | Type | Description |
|---|------|------|-------------|
| 1 | `backend/schemas/sponsored_theatre.py` | NEW | SponsoredTheatreConfig, SponsorReviewPackage (Pydantic v2) |
| 2 | `backend/osint/source_manifest.py` | NEW | SourceManifestEntry, SourceManifest, SourceManifestBuilder |
| 3 | `backend/services/sponsored_theatre.py` | NEW | SponsoredTheatreService -- creation, review, commit |
| 4 | `backend/services/market_theatre_bridge.py` | NEW | MarketTheatreBridge -- LMSR <-> Theatre integration |
| 5 | `backend/services/stub_agents.py` | NEW | StubAgent, StubAgentSpawner, 6 archetype strategies |
| 6 | `backend/api/sponsored_theatre_routes.py` | NEW | FastAPI router: POST create, GET review, POST commit |
| 7 | `backend/services/tests/test_sponsored_theatre.py` | NEW | Theatre creation tests (10+ tests) |
| 8 | `backend/services/tests/test_market_theatre_bridge.py` | NEW | LMSR bridge tests (6+ tests) |
| 9 | `backend/services/tests/test_stub_agents.py` | NEW | Stub agent tests (9+ tests) |

### Sprint 2 -- New + Modified Files (11)

| # | File | Type | Description |
|---|------|------|-------------|
| 1 | `backend/services/theatre_evidence.py` | NEW | TheatreEvidenceCollector, EvidenceSnapshot |
| 2 | `backend/services/theatre_resolution.py` | NEW | TheatreResolutionEngine, TheatreResolutionResult |
| 3 | `backend/services/certificate_pipeline.py` | NEW | CertificatePipeline, CalibrationCertificate (v1.0.0) |
| 4 | `backend/services/rlmf_export.py` | NEW | RLMFExportGenerator, RLMFExport (v2.0.1), CalibrationMetrics |
| 5 | `backend/services/sponsor_delivery.py` | NEW | SponsorDeliveryAssembler, SponsorDeliveryPackage |
| 6 | `backend/services/theatre_status.py` | NEW | TheatreStatusSnapshot, echelon_status integration |
| 7 | `backend/engines/paradox.py` | MODIFIED | MEDIUM-1: p_reality=None guard in scan() |
| 8 | `backend/services/tests/test_theatre_resolution.py` | NEW | Resolution engine tests (5+ tests) |
| 9 | `backend/services/tests/test_certificate_pipeline.py` | NEW | Certificate pipeline tests (5+ tests) |
| 10 | `backend/services/tests/test_rlmf_export.py` | NEW | RLMF export tests (5+ tests) |
| 11 | `backend/services/tests/test_sponsored_theatre_e2e.py` | NEW | End-to-end integration test (10+ assertions) |

### Modification Summary

| Module Path | Sprint | Change |
|-------------|--------|--------|
| `backend/market/` | -- | ZERO modifications |
| `backend/engines/paradox.py` | Sprint 2 | MEDIUM-1: `if signal.p_reality is None: return None` guard |
| `backend/engines/` (other) | -- | ZERO modifications |
| `backend/osint/` (pipeline) | -- | ZERO modifications to existing files |
| `backend/osint/source_manifest.py` | Sprint 1 | NEW file (not modifying existing OSINT pipeline) |
| `backend/chain/` | -- | ZERO modifications |
