# PRD: Sponsored Theatre End-to-End

**Cycle**: 012
**Version**: 1.0
**Date**: 2026-03-03
**Predecessor**: Cycle-011 (WorldMonitor OSINT Integration -- live evidence pipeline + convergence signals)

---

## 1. Problem Statement

Cycle-011 closed the integrity loop: WorldMonitor evidence flows through the full pipeline (Collection, Corroboration, Scoring) into the Paradox Engine's `p_reality` via the provider swap pattern. But all of this infrastructure -- LMSR engine (010a), engines and heartbeat (010b), live OSINT pipeline (011) -- operates in isolation. There is no mechanism for an external entity to commission a prediction market, no wiring between the LMSR engine and Theatre lifecycle, no automated path from settlement to certificate delivery, and no RLMF training data export.

The components exist. The integration does not.

Without a sponsor workflow, Echelon cannot demonstrate its core value proposition: an externally-commissioned prediction market that runs from question to verifiable certificate with full evidence provenance. The LMSR trades shares in a vacuum. The OSINT pipeline collects evidence that feeds no resolution. The verifier checks certificates that no pipeline produces.

> Sources: echelon_cycle_012.md:12-17, echelon_platform_roadmap.md:125-137

---

## 2. Vision

After Cycle-012, Echelon has its first complete market lifecycle. A sponsor defines a question ("Will Acme Ltd file annual accounts by 30 Sep 2026?"), Echelon configures a Theatre with committed LMSR parameters and OSINT sources, the sponsor reviews the commitment hash and approves, stub agents trade against the LMSR, the WorldMonitor pipeline collects evidence with HTTP transcript receipts, the Composed Oracle evaluates against committed criteria, the market resolves and settles, and the sponsor receives a calibration certificate that passes all 21 `echelon_verify` checks -- with a complete evidence chain from mock WM fixtures, RLMF training data export, and an `echelon_status` endpoint returning live state at every lifecycle phase.

This is infrastructure proof, not production deployment. Agents are stubs with scripted strategies (no T0/T1/T2/T3 intelligence -- that is Cycle-013). Evidence is mock-only (WorldMonitor is not deployed locally). On-chain anchoring is stubbed. But the sponsor onboarding workflow is real, the integration contracts are real, and the certificate provenance chain is real.

> Sources: echelon_cycle_012.md:14-21, echelon_platform_roadmap.md:131-137

---

## 3. Goals & Success Metrics

### 3.1 Primary Goals

1. **Sponsor Onboarding Workflow**: `SponsoredTheatreConfig` model, Theatre creation service, sponsor review/commit API endpoints. Full COMMISSION -> COMMITMENT flow.
2. **LMSR <-> Theatre Integration**: Bridge connecting the LMSR engine (`backend/market/`) to the Theatre lifecycle (`backend/services/theatre_bridge.py`). Market creation, phase transitions, and state serialisation driven by Theatre config.
3. **Stub Agent Population**: Six agent stubs (one per archetype: Shark, Spy, Diplomat, Saboteur, Whale, Degen) with simple deterministic strategies. Prove the infrastructure accepts trading agents. The agent runtime (T0/T1/T2/T3) is Cycle-013.
4. **Commitment Protocol Wiring**: `MarketCommitment.compute_hash()` integrated into Theatre creation. Commitment hash covers LMSR parameters, oracle config, and Theatre metadata. Verified after freeze.
5. **Source Manifest Builder**: Structured OSINT source manifest for a Theatre's committed sources, validated against registry, included in commitment hash and certificate.
6. **Theatre Evidence Collection**: OSINT evidence collected per heartbeat cadence during TRADING phase, using LiveOSINTRealityProvider from Cycle-011 with mock WM fixtures.
7. **Theatre Resolution Engine**: Composed Oracle evaluation at resolution_date. Determines winning outcome for n-outcome markets. Triggers settlement.
8. **Certificate Generation Pipeline**: Automated pipeline from SettlementReport to calibration certificate conforming to v1.0.0 schema. Certificate passes all 21 `echelon_verify` checks.
9. **RLMF Export**: Training data export conforming to RLMF schema v2.0.1 -- probability distributions, agent decision traces, calibration metrics (Brier score, ECE), per-agent P&L.
10. **Sponsor Delivery Package**: Bundled deliverable containing certificate, evidence bundle, RLMF export, and commitment hash.
11. **echelon_status Integration**: Live Theatre state via MCP tool during TRADING (prices, evidence coverage) and after SETTLEMENT (VALID certificate, composite score).

### 3.2 Success Metrics

| Metric | Target |
|--------|--------|
| Sprint 1 new tests | 20+ |
| Sprint 2 new tests | 20+ |
| Scoped regression | 0 failures in `backend/market/`, `backend/engines/`, `backend/scoring/`, `backend/osint/` |
| LMSR engine modifications | 0 (integration layer only) |
| Paradox Engine modifications | 0 |
| Certificate verifier checks | 21/21 pass |
| RLMF schema conformance | v2.0.1 |
| Stub agent trades in E2E test | >20 trades across 6 agents |
| End-to-end lifecycle | Full: creation -> commitment -> trading -> resolution -> settlement -> certificate -> delivery |

### 3.3 Regression Baseline

The regression target is scoped to four module paths:

```
python3 -m pytest backend/market/ backend/engines/ backend/scoring/ backend/osint/ -v
```

The pre-existing `theatre/` collection errors (29 import failures from Cycle-031-033) are excluded from 012's regression baseline. Everything in the four scoped directories must pass. Everything outside is not this cycle's concern.

### 3.4 Carryover Findings from Cycle-011

| ID | Severity | Description | 012 Action |
|----|----------|-------------|------------|
| MEDIUM-1 | MEDIUM | `p_reality=None` crashes `LogicGapCalculator.compute()` when LiveOSINTRealityProvider returns stale signal with "none" activation gate active. `abs(p_market - None)` raises TypeError. | Fix with None guard in `ParadoxEngine.scan()` before passing to `compute()`. Minimal change: `if signal.p_reality is None: return None`. |
| MEDIUM-2 | MEDIUM | ConvergenceDetector uses `source_group` instead of dedicated domain field. Future non-WM collectors could inflate diversity counts. | Monitor only. Correct in 012 (WM-only). Evaluate when non-WM collectors land (Cycle-015). |
| LOW-1 | LOW | Unused `Optional` import in `corroboration.py`. | Fix during any touch of that file. |
| LOW-2 | LOW | Unused `pytest` import in test files. | Fix during any touch of those files. |
| LOW-3 | LOW | `asyncio.get_event_loop()` deprecation. | No action -- Python 3.9.6 target not affected. |

> Sources: grimoires/loa/archive/2026-03-03-worldmonitor-osint-integration/a2a/sprint-22/auditor-sprint-feedback.md

---

## 4. Functional Requirements

### 4.1 SponsoredTheatreConfig Model

**File**: `backend/schemas/sponsored_theatre.py`

Pydantic v2 model capturing sponsor-provided configuration:
- `question: str` -- the Theatre question (e.g., "Will Acme Ltd file annual accounts by 30 Sep 2026?")
- `resolution_date: datetime` -- when the market resolves
- `committed_sources: list[str]` -- OSINT registry source IDs for settlement
- `outcome_labels: list[str]` -- e.g., ["Filed on time", "Filed late", "Not filed"]
- `liquidity_b: Decimal` -- LMSR `b` parameter (sponsor's seeding capital -- parameterises liquidity depth, bounds worst-case loss)
- `fee_schedule: FeeSchedule` -- trade and resolution fee configuration
- `sponsor_id: str` -- sponsor identifier
- `sponsor_metadata: dict` -- freeform sponsor context (company name, jurisdiction, etc.)

**Note on `b`:** `b` is not escrowed capital. It parameterises liquidity depth and bounds the market maker's worst-case loss at `b * ln(n)`. Whether the sponsor deposits collateral is a business decision, not an LMSR invariant.

> Sources: echelon_cycle_012.md:144-163

### 4.2 Theatre Creation Service

**File**: `backend/services/sponsored_theatre.py`

Orchestrates Theatre creation from SponsoredTheatreConfig:
- Validates `committed_sources` against OSINT registry (all source IDs must exist)
- Provisional sources (e.g., WM endpoints with shared `independence_upstream_id`) are accepted but flagged in the source manifest with `settlement_status: PROVISIONAL`; the corroboration penalty carries through to the certificate
- Creates LMSR MarketState via `MarketLifecycle.create_market()`
- Generates TheatreTemplate from config + market parameters
- Computes commitment hash via `MarketCommitment.compute_hash()`
- Returns a `SponsorReviewPackage` containing: template JSON, commitment hash, worst-case loss (`b * ln(n)`), source manifest, fee schedule breakdown

> Sources: echelon_cycle_012.md:155-162

### 4.3 Sponsor Review Endpoints

**File**: `backend/api/sponsored_theatre_routes.py`

Three endpoints:
- `POST /api/v1/sponsored-theatres` -- creates a sponsored Theatre in CREATED state
- `GET /api/v1/sponsored-theatres/{id}/review` -- returns the SponsorReviewPackage for sponsor approval
- `POST /api/v1/sponsored-theatres/{id}/commit` -- sponsor approves, transitions to COMMITTED, freezes all parameters

> Sources: echelon_cycle_012.md:165-167

### 4.4 LMSR <-> Theatre Integration Layer

**File**: `backend/services/market_theatre_bridge.py`

Connects the LMSR engine to the Theatre lifecycle:
- `create_market_for_theatre(theatre_id, config)` -- creates MarketState, PositionManager, attaches to Theatre
- `get_market_state(theatre_id)` -- returns current LMSR state (prices, phase, positions)
- `transition_market(theatre_id, target_phase)` -- validates and executes phase transition
- Stores LMSR state in Theatre's database record (JSON serialisation of MarketState)

> Sources: echelon_cycle_012.md:169-174

### 4.5 Stub Agent Spawner

**File**: `backend/services/stub_agents.py`

Creates a population of agent stubs for a Theatre:
- Input: Theatre ID, agent count (default 6 -- one per archetype), initial balance per agent
- Each stub is a dataclass: `StubAgent(agent_id, archetype, balance, strategy)`
- Strategy is a simple function: `(market_state, evidence) -> Optional[TradeIntent]`
- Default strategies per archetype:
  - Shark: buy the leading outcome if price < 0.7
  - Spy: trade when new evidence arrives (evidence-triggered)
  - Diplomat: stabilise -- buy the trailing outcome if spread > 0.4
  - Saboteur: random contrary trades at low volume
  - Whale: single large position early, hold to settlement
  - Degen: random trades every tick
- Stubs call `TradingEngine.execute_trade()` directly -- no agent runtime, no LLM
- Purpose: produce realistic trading activity and P&L data for the first Theatre

**Critical constraint:** Stub agents are throwaway code. They prove the infrastructure accepts trading agents. Cycle-013 replaces them with autonomous agents using the T0/T1/T2/T3 pipeline.

> Sources: echelon_cycle_012.md:177-189

### 4.6 Commitment Protocol Integration

Wire `MarketCommitment.compute_hash()` into the Theatre creation flow. The commitment hash covers:
- LMSR parameters: `b`, fee_schedule, n_outcomes, outcome_labels
- Oracle config: committed_sources, resolution_date, corroboration_minimum
- Theatre metadata: template_id, version pins

Verify that `commitment.verify_hash()` passes after freeze. Store commitment hash in Theatre database record. On-chain anchor is stubbed (returns deterministic "local_mode" transaction hash).

> Sources: echelon_cycle_012.md:192-196

### 4.7 Source Manifest Builder

**File**: `backend/osint/source_manifest.py`

Builds the OSINT source manifest for a Theatre's committed sources:
- Input: list of registry source IDs
- Output: structured manifest with: source_id, source_group, independence_upstream_id, jurisdiction, access_surface, settlement_eligibility
- Validated against the OSINT registry version pinned in repo
- Included in commitment hash and certificate

> Sources: echelon_cycle_012.md:199-203

### 4.8 Theatre Evidence Collector

**File**: `backend/services/theatre_evidence.py`

Orchestrates OSINT evidence collection for a Theatre:
- Input: Theatre ID (reads committed_sources from Theatre config)
- Calls LiveOSINTRealityProvider (from 011) with the Theatre's source list
- Collects evidence bundles per source with HTTP transcript receipts
- Stores evidence in Theatre's evidence store (JSON, keyed by collection timestamp)
- Runs on heartbeat cadence during TRADING phase

> Sources: echelon_cycle_012.md:238-245

### 4.9 Theatre Resolution Engine

**File**: `backend/services/theatre_resolution.py`

Triggers resolution when the resolution_date arrives:
- Collects final evidence snapshot
- Invokes Composed Oracle evaluation:
  - Corroboration check (provisional in 012 -- WM-only, 0.7 penalty)
  - Counter-signal evaluation (scaffolding -- all UNAVAILABLE, INTELLIGENCE_GAP)
  - Composite score computation
- Determines winning outcome based on oracle evaluation
- Oracle evaluation must return a discrete `winning_outcome_index` for n-outcome markets (not binary YES/NO) -- the Companies House Theatre has 3 outcomes
- Transitions market: RESOLVING -> settle() -> SETTLED
- Returns `TheatreResolutionResult` with oracle_output_id, composite_score, winning_outcome, evidence_bundle_hash

> Sources: echelon_cycle_012.md:247-255

### 4.10 Certificate Generation Pipeline

**File**: `backend/services/certificate_pipeline.py`

Produces the calibration certificate:
- Input: TheatreResolutionResult + SettlementReport
- Builds certificate conforming to v1.0.0 schema:
  - `oracle_output_id` (replaces 010b's certificate_id)
  - `composite_score`
  - `evidence_bundle_hash` (manifest pattern: `{bundle_id: content_hash}` -> canonical JSON -> SHA-256)
  - `criteria_breakdown` (per-criterion pass/fail with evidence references)
  - `osint_source_manifest` (from source manifest builder)
  - `corroboration_status` (provisional: minimum_met = false, penalty_factor = 0.7)
  - `counter_signal_results` (all UNAVAILABLE, classified as INTELLIGENCE_GAP)
  - `verification_tier` (UNVERIFIED for first local-mode Theatre)
  - `scored_at`, `provider_version`
- Runs certificate through `echelon_verify` -- must pass all 21 checks
- Stores certificate in Theatre database record

**UNVERIFIED tier rationale:** BACKTESTED requires 50+ replay runs against historical data, which 012 does not produce. The first local-mode Theatre earns UNVERIFIED, which is honest -- it has not been backtested.

> Sources: echelon_cycle_012.md:258-272

### 4.11 RLMF Export Generator

**File**: `backend/services/rlmf_export.py`

Produces RLMF training data from the Theatre:
- Conforms to RLMF schema v2.0.1
- Captures: probability distributions at each market epoch, agent decision traces (stub strategies + outcomes), calibration metrics (Brier score, ECE)
- Per-agent P&L breakdown
- Exportable as JSON
- Linked to Theatre via oracle_output_id

> Sources: echelon_cycle_012.md:274-280

### 4.12 Sponsor Delivery Package

**File**: `backend/services/sponsor_delivery.py`

Assembles the final delivery for the sponsor:
- Calibration certificate (JSON, verifiable)
- Evidence bundle (complete artefact: committed template, ground truth, HTTP receipts, per-episode scores, gap reports)
- RLMF export (JSON)
- Commitment hash (for future on-chain anchoring)
- Returns a `SponsorDeliveryPackage` with download links and `echelon_status` endpoint URL

> Sources: echelon_cycle_012.md:282-288

### 4.13 echelon_status Integration

Wire the Theatre's live state into the `echelon_status` MCP tool:
- During TRADING: returns current prices, evidence coverage %, sources online/offline
- After SETTLEMENT: returns certificate state (VALID), deployability signal, composite score, counter-signal status
- Cacheable with TTL (300s)
- Matches the response schema from Sponsored Theatre Programme v1 section 8

> Sources: echelon_cycle_012.md:290-294

---

## 5. What Previous Cycles Deliver (Consumed by This Cycle)

### 5.1 LMSR Market Engine (Cycle-010a)

| Module | What It Does |
|--------|-------------|
| `lmsr.py` | Pure cost function: C(x) = b * ln(sum exp(xj / b)), prices, trade cost. Log-sum-exp numerically stable. |
| `state.py` | MarketPhase enum (CREATED -> COMMITTED -> TRADING -> RESOLVING -> SETTLED), FeeSchedule, MarketState container. |
| `lifecycle.py` | Forward-only phase transitions. `create_market()` factory. |
| `trading.py` | TradingEngine.execute_trade() -- atomic execution, mutates state vector + positions. |
| `positions.py` | In-memory position tracking: AgentPosition (shares, net_cashflow, realised_pnl, trade_count). |
| `resolution.py` | Deterministic settlement: AgentSettlement, SettlementReport with settlement_hash. |
| `commitment.py` | SHA-256 commitment hash over Echelon Canonical JSON v0. Immutable after COMMITTED phase. |
| `fees.py` | FeeSchedule (trade_fee_bps, resolution_fee_bps). Frozen at commitment. |
| `exceptions.py` | InvalidPhaseTransition, ParameterMutationAfterCommit, TradingHalted, InsufficientBalance, InsufficientShares. |

### 5.2 Engines + Heartbeat (Cycle-010b)

- Butterfly Engine: wing flaps, stability impact on markets
- Paradox Engine: Logic Gap scanning, spawn/extraction, RealitySignalProvider interface
- Entropy Engine: temporal stability decay
- Heartbeat scheduler: AGENT 5s -> MARKET 10s -> PARADOX 30s -> ENTROPY 60s
- `echelon_status` MCP integration for live market state queries

### 5.3 WorldMonitor OSINT Pipeline (Cycle-011)

- LiveOSINTRealityProvider wired to Paradox Engine
- Three WM domain endpoints: CII, market snapshot, maritime anomaly
- Evidence bundle collection with HTTP transcript receipts
- Corroboration engine (provisional -- WM-only, 0.7 penalty)
- Counter-signal scaffolding (all 11 classes UNAVAILABLE, INTELLIGENCE_GAP)
- Convergence detection (1 deg x 1 deg cells, 24h window, 3+ WMDomain values)
- Mock-only testing with JSON fixtures from Pydantic schemas

### 5.4 Theatre Infrastructure (Existing Codebase)

| Component | Location | Status |
|-----------|----------|--------|
| Theatre API routes | `backend/api/theatre_routes.py` | 12 endpoints. Auth-protected mutations, public reads. |
| Theatre schemas | `backend/schemas/theatre.py` | TheatreCreate, TheatreRunRequest, TheatreSettleRequest, response schemas. |
| Theatre bridge | `backend/services/theatre_bridge.py` | TheatreStateMachine, CommitmentProtocol, ReplayEngine adapter. Runs lifecycle as background task. |
| Database models | `backend/database/models.py` | Theatre, TheatreTemplate, TheatreCertificate SQLAlchemy models. |
| Template library | `fixtures/` | 10 templates across 4 verticals. |

### 5.5 MCP Surface (Cycle-008/009)

- `echelon_verify` -- validates certificates against evidence bundles
- `echelon_hash` -- computes commitment hashes
- `echelon_status` -- live market/certificate state queries
- `echelon_calibrate` -- runs calibration scoring

**Key constraint**: No modifications to `backend/market/` modules (LMSR engine), `backend/engines/paradox.py` (Paradox Engine), or `backend/osint/` modules (OSINT pipeline). Integration via service layer and new modules only.

> Sources: echelon_cycle_012.md:26-76

---

## 6. Testing Strategy

### 6.1 Mock-Only OSINT

WorldMonitor is NOT running locally. All evidence collection uses JSON fixtures from Cycle-011's test suite (`backend/osint/tests/fixtures/`). Tests marked `@pytest.mark.live_wm` for future integration when WM is deployed.

### 6.2 Stub Agent Determinism

Stub agent strategies are deterministic given fixed market state and evidence inputs. The E2E test uses fixed mock evidence injections at predetermined ticks to produce reproducible results.

### 6.3 On-Chain Anchor Stub

The anchoring interface returns a deterministic "local_mode" transaction hash. No Base Sepolia calls. No real blockchain interaction.

### 6.4 Scoped Regression

```
python3 -m pytest backend/market/ backend/engines/ backend/scoring/ backend/osint/ -v
```

Pre-existing `theatre/` collection errors (29 import failures) are excluded from 012's regression baseline. All tests in the four scoped directories must pass.

---

## 7. Non-Functional Requirements

### 7.1 State Isolation
- Each Theatre has its own LMSR market, agent population, evidence store, and resolution result
- No cross-Theatre state sharing

### 7.2 In-Memory + Database
- LMSR MarketState serialised to Theatre database record (JSON)
- Evidence bundles stored in Theatre evidence store (JSON, keyed by timestamp)
- Certificate stored in TheatreCertificate database record
- Agent positions tracked in-memory during trading, settled at resolution

### 7.3 Provenance
- Every evidence bundle carries an HTTP transcript receipt (from 011)
- Commitment hash covers LMSR parameters + oracle config + Theatre metadata
- Certificate carries evidence_bundle_hash, osint_source_manifest, corroboration_status
- RLMF export linked to Theatre via oracle_output_id

### 7.4 Performance
- Stub agents execute trades synchronously (no async, no parallelism needed)
- Evidence collection via LiveOSINTRealityProvider (async, from 011)
- Certificate generation is a single-pass computation

---

## 8. Scope Exclusions

- **No autonomous agents.** Stubs only. The agent runtime (T0/T1/T2/T3 decision loop) is Cycle-013. Stubs are throwaway code.
- **No on-chain anchoring.** Commitment hash and certificate hash are computed and stored, but Base deployment is deferred. Anchoring interface returns deterministic "local_mode" transaction hash.
- **No WorldMonitor deployment.** All evidence uses mock fixtures. WM setup/hosting is out of scope.
- **No non-WM collectors.** Companies House, SEC EDGAR, FRED, etc. are deferred (Cycle-015).
- **No database persistence for LMSR state.** MarketState is serialised to Theatre record as JSON. No separate LMSR database table.
- **No automatic Theatre creation from convergence.** Convergence alerts (from 011) are not consumed by 012's sponsor workflow. Auto-creation requires the Sponsored Theatre workflow to exist first -- which 012 is building.
- **No `rule_change_monitored` implementation.** Stubbed as always-PASS. Depends on Sponsored Theatre lifecycle patterns established in this cycle.
- **Single Theatre type.** Cycle-012 targets Companies House Theatres (UK corporate compliance). Other jurisdictions and source configurations are deferred.
- **Provisional corroboration only.** WM-only sources share `independence_upstream_id: worldmonitor`. Corroboration minimum never met (0.7 penalty applies). This is documented in the certificate.
- **No agent breeding/genealogy.** Agent genomes are static.
- **No real WM HTTP calls in tests.** All tests use mock fixtures.

> Sources: echelon_cycle_012.md:369-383

---

## 9. Acceptance Criteria

### 9a. Sprint 1 -- Theatre Creation + Sponsor Onboarding + LMSR Wiring

- [ ] `POST /api/v1/sponsored-theatres` creates a Theatre with LMSR market in CREATED state
- [ ] `GET /api/v1/sponsored-theatres/{id}/review` returns a complete SponsorReviewPackage (template JSON, commitment hash, worst-case loss, source manifest, fee breakdown)
- [ ] `POST /api/v1/sponsored-theatres/{id}/commit` freezes parameters and transitions to COMMITTED
- [ ] SponsoredTheatreConfig validates committed_sources against OSINT registry (reject non-existent source IDs)
- [ ] Provisional sources (WM endpoints with shared upstream_id) accepted with `settlement_status: PROVISIONAL` flag
- [ ] LMSR MarketState created from Theatre config with correct `b`, outcomes, fee schedule
- [ ] Market phase transitions propagate between LMSR engine and Theatre lifecycle
- [ ] LMSR state serialises to and deserialises from Theatre database record without data loss
- [ ] Parameter mutation rejected after COMMITTED phase (MarketCommitment immutability)
- [ ] Commitment hash verified after freeze -- covers LMSR params, oracle config, Theatre metadata
- [ ] Source manifest built and validated against registry (source_id, source_group, independence_upstream_id, jurisdiction, settlement_eligibility)
- [ ] 6 stub agents spawned with correct archetype strategies
- [ ] Stub agents execute trades against LMSR via TradingEngine.execute_trade()
- [ ] Agent balance and position tracking works through multiple trades
- [ ] Worst-case loss correctly computed as `b * ln(n)`
- [ ] No modifications to `backend/market/` modules
- [ ] No modifications to `backend/engines/` modules
- [ ] Scoped regression: all tests in `backend/market/`, `backend/engines/`, `backend/scoring/`, `backend/osint/` pass
- [ ] 20+ new Sprint 1 tests pass

> Sources: echelon_cycle_012.md:217-227

### 9b. Sprint 2 -- Resolution + Settlement + Certificate Delivery

- [ ] Evidence collector runs against mock WM fixtures during TRADING phase
- [ ] Evidence stored in Theatre evidence store with collection timestamps
- [ ] Resolution engine evaluates Composed Oracle at resolution_date
- [ ] Oracle evaluation returns discrete `winning_outcome_index` for 3-outcome Companies House Theatre
- [ ] Composite score computed with provisional corroboration (0.7 penalty) and counter-signal scaffolding
- [ ] Market transitions: TRADING -> RESOLVING -> SETTLED
- [ ] Settlement satisfies bounded-loss invariant: market maker P&L >= -b*ln(n); equivalently total_payout <= total_trade_cashflow + b*ln(n)
- [ ] Each agent's payout equals winning shares held
- [ ] Certificate generated conforming to v1.0.0 schema
- [ ] Certificate carries: oracle_output_id, composite_score, evidence_bundle_hash, criteria_breakdown, osint_source_manifest, corroboration_status, counter_signal_results, verification_tier (UNVERIFIED)
- [ ] Certificate passes all 21 `echelon_verify` checks
- [ ] RLMF export conforms to schema v2.0.1
- [ ] RLMF captures: probability distributions per epoch, agent decision traces, Brier score, ECE, per-agent P&L
- [ ] Sponsor delivery package contains all 4 deliverables (certificate, evidence bundle, RLMF export, commitment hash)
- [ ] `echelon_status` returns live state during TRADING (prices, evidence coverage %, sources status)
- [ ] `echelon_status` returns VALID certificate post-settlement (composite_score, counter-signal status)
- [ ] End-to-end test passes: full Companies House Theatre lifecycle from sponsor creation to certificate delivery
- [ ] E2E test produces >20 stub agent trades across 6 agents
- [ ] MEDIUM-1 carryover: `p_reality=None` None guard added to ParadoxEngine.scan() path
- [ ] No modifications to `backend/market/` modules
- [ ] No modifications to `backend/osint/` modules (pipeline code)
- [ ] All tests use mock HTTP responses only
- [ ] Scoped regression: all tests in `backend/market/`, `backend/engines/`, `backend/scoring/`, `backend/osint/` pass
- [ ] 20+ new Sprint 2 tests pass

> Sources: echelon_cycle_012.md:321-333

---

## 10. Sprint Architecture

### Sprint 1 -- Theatre Creation + Sponsor Onboarding + LMSR Wiring

```
backend/
+-- schemas/
|   +-- sponsored_theatre.py              # SponsoredTheatreConfig, SponsorReviewPackage (NEW)
+-- services/
|   +-- sponsored_theatre.py              # Theatre creation from sponsor config (NEW)
|   +-- market_theatre_bridge.py          # LMSR <-> Theatre integration (NEW)
|   +-- stub_agents.py                    # Stub agent spawner + simple strategies (NEW)
|   +-- tests/
|       +-- test_sponsored_theatre.py     # Theatre creation tests (NEW)
|       +-- test_market_theatre_bridge.py # LMSR bridge tests (NEW)
|       +-- test_stub_agents.py           # Stub agent tests (NEW)
+-- api/
|   +-- sponsored_theatre_routes.py       # Sponsor-facing API endpoints (NEW)
+-- osint/
    +-- source_manifest.py                # Source manifest builder (NEW)
```

### Sprint 2 -- Resolution + Settlement + Certificate Delivery

```
backend/
+-- services/
|   +-- theatre_evidence.py               # OSINT evidence collection for Theatre (NEW)
|   +-- theatre_resolution.py             # Resolution + Composed Oracle evaluation (NEW)
|   +-- certificate_pipeline.py           # Certificate generation from settlement (NEW)
|   +-- rlmf_export.py                    # RLMF training data export (NEW)
|   +-- sponsor_delivery.py              # Sponsor delivery package assembly (NEW)
|   +-- tests/
|       +-- test_theatre_resolution.py    # Resolution engine tests (NEW)
|       +-- test_certificate_pipeline.py  # Certificate pipeline tests (NEW)
|       +-- test_rlmf_export.py           # RLMF export tests (NEW)
|       +-- test_sponsored_theatre_e2e.py # End-to-end integration test (NEW)
+-- engines/
    +-- paradox.py                         # MEDIUM-1 fix: None guard for p_reality (MODIFIED -- minimal)
```

---

## 11. Sprint Task Breakdown

### Sprint 1 Tasks (10 tasks)

1. **SponsoredTheatreConfig model** -- Pydantic v2 model with question, resolution_date, committed_sources, outcome_labels, liquidity_b, fee_schedule, sponsor_id, sponsor_metadata
2. **Theatre creation service** -- Orchestrate creation from config: validate sources, create LMSR, generate template, compute commitment hash, produce SponsorReviewPackage
3. **Sponsor review endpoints** -- POST create, GET review, POST commit. Phase transitions on commit.
4. **LMSR <-> Theatre integration layer** -- create_market_for_theatre(), get_market_state(), transition_market(), state serialisation
5. **Stub agent spawner** -- 6 archetypes with deterministic strategies, trade execution via TradingEngine
6. **Commitment protocol integration** -- Wire compute_hash() into creation flow, verify after freeze, store in Theatre record
7. **Source manifest builder** -- Build and validate OSINT source manifest for committed sources
8. **Theatre creation tests** -- Valid creation, invalid sources, provisional flagging, commitment freeze, review package, worst-case loss, source manifest
9. **LMSR-Theatre bridge tests** -- Market creation from config, phase transitions, state serialisation roundtrip, mutation rejection
10. **Stub agent tests** -- Population spawning, per-archetype strategy, trade execution, balance tracking, P&L accumulation

### Sprint 2 Tasks (10 tasks)

1. **Theatre evidence collector** -- OSINT evidence collection per heartbeat cadence during TRADING phase, using mock WM fixtures
2. **Theatre resolution engine** -- Final evidence snapshot, Composed Oracle evaluation, winning outcome determination, settlement trigger
3. **Certificate generation pipeline** -- Settlement to certificate, v1.0.0 schema, echelon_verify validation (21 checks)
4. **RLMF export generator** -- Schema v2.0.1 conformance, probability distributions, agent traces, calibration metrics
5. **Sponsor delivery package** -- Bundle certificate, evidence, RLMF, commitment hash into deliverable
6. **echelon_status integration** -- Wire Theatre live state into MCP tool (TRADING: prices/coverage; SETTLED: certificate/score)
7. **MEDIUM-1 fix: p_reality=None guard** -- Add None guard in ParadoxEngine.scan() before LogicGapCalculator.compute()
8. **Resolution engine tests** -- Clear winner, narrow margin, evidence gaps, provisional corroboration, composite score
9. **Certificate pipeline tests** -- Schema conformance, evidence_bundle_hash, verifier checks, oracle_output_id format
10. **End-to-end integration test** -- Full Companies House Theatre lifecycle: creation -> commit -> trading (6 stubs, 10 ticks) -> evidence injection (mock WM) -> resolution -> settlement -> certificate (21 checks) -> RLMF -> delivery -> echelon_status query

---

## 12. Dependency Chain

```
Cycle-004 (pipeline hardening)
  -> Cycles 005-006 (registry expansion + live OSINT surfaces)
    -> Cycle-007 (unified Two-Rail pipeline, 447+ tests)
      -> Cycle-008 (MCP verifier + construct calibration)
        -> Cycle-009 (MCP surface, HTTP transport, certificate store)
          -> Cycle-010a (LMSR cost function, market lifecycle, trade execution)
            -> Cycle-010b (Butterfly, Paradox, Entropy engines, heartbeat, VRF, Base Sepolia)
              -> Cycle-011 (WorldMonitor Integration -- live evidence pipeline + convergence)
                -> Cycle-012 (Sponsored Theatre E2E)  <-- THIS CYCLE
                  -> Cycle-013 (Agent Runtime -- T0/T1/T2/T3 + ADK)
                    -> Cycle-014 (Bounded Inquiry Markets)
```

> Sources: echelon_platform_roadmap.md:191-204

---

## 13. BEAUVOIR Principle: Agent-First Citizenship

The BEAUVOIR review guidelines (from the 0xHoneyJar engineering team) establish patterns for agent-first development that apply to 012's stub agents and propagate to 013's full runtime:

1. **Document the reasoning, not just the conclusion.** Every stub agent strategy includes a comment explaining why that archetype trades that way. Future agents (013) inherit these rationales.
2. **Map decision trajectories.** Stub agent trades are logged with: trigger condition, market state at decision time, confidence level, outcome. This produces the training data that RLMF schema captures.
3. **Name the pattern.** Trade strategies reference named patterns from the archetype matrix (momentum exploitation, intel arbitrage, stability maintenance, chaos creation, market moving, volatility harvesting).

> Sources: echelon_cycle_012.md:389-396

---

## 14. What 012 Unlocks

- **First complete market lifecycle** -- creation through certificate delivery with verifiable evidence
- **Proof that LMSR + OSINT + settlement work together** -- the E2E integration test is the acceptance gate
- **Sponsor onboarding pattern** -- reusable for any future Theatre commissioning
- **RLMF generation proof** -- the first real training data export from a live market
- **Certificate delivery pipeline** -- automated from settlement to verifiable deliverable
- **Foundation for 013 (Agent Runtime)** -- the stub agents in 012 define the interface that autonomous agents in 013 must satisfy

> Sources: echelon_cycle_012.md:399-407

---

## 15. Key Spec References

| Document | Relevance |
|----------|-----------|
| `echelon_cycle_012.md` | Primary context document for this cycle |
| `echelon_platform_roadmap.md` | Roadmap positioning and dependency graph |
| WorldMonitor API Contract (`worldmonitor_api_contract.py`) | Evidence bundle shapes, canonical hashing |
| OSINT Composed Oracle Spec v2 | Three reserved criteria, source independence taxonomy |
| OSINT Source Registry v0.3.2 | 51 sources, 3 WM endpoints, independence_upstream_id |
| Echelon System Bible v13 | Agent archetypes (section VIII), market microstructure (section III), commitment protocol (section VI) |
| Sponsored Theatre Programme v1 | 6-step lifecycle: COMMISSION -> COMMITMENT -> TRADING -> RESOLUTION -> SETTLEMENT -> DELIVERY |
| RLMF schema v2.0.1 | Training data export format |
| Certificate schema v1.0.0 | Calibration certificate format, 21 verifier checks |
| Cycle-011 Sprint 22 audit | Carryover findings (MEDIUM-1: p_reality=None crash path) |
