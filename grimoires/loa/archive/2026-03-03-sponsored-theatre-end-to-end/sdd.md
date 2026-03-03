# SDD: Sponsored Theatre End-to-End

**Cycle**: 012
**Version**: 1.0
**Date**: 2026-03-03
**PRD**: `grimoires/loa/prd.md` v1.0
**Predecessor**: Cycle-011 SDD (archived)

---

## 1. Executive Summary

Cycle-012 integrates every subsystem built across Cycles 008-011 into a single end-to-end market lifecycle: sponsor onboarding, LMSR market creation, commitment protocol, stub agent trading, OSINT evidence collection, Composed Oracle resolution, deterministic settlement, certificate generation, RLMF training data export, and sponsor delivery.

**Key architectural decisions**:
1. **New service layer, not new engine** -- all integration happens in `backend/services/` and `backend/schemas/`. Zero modifications to `backend/market/` (LMSR engine), `backend/engines/paradox.py` (Paradox Engine), or `backend/osint/` (evidence pipeline).
2. **Pydantic v2 for sponsor-facing schemas** -- `SponsoredTheatreConfig` and `SponsorReviewPackage` use Pydantic v2 for validation and serialisation. Internal dataclasses remain stdlib `@dataclass`.
3. **Bridge pattern for LMSR-Theatre coupling** -- `MarketTheatreBridge` wraps `MarketLifecycle`, `TradingEngine`, `PositionManager`, and `ResolutionEngine` behind a Theatre-aware facade. No LMSR code modified.
4. **Stub agents as interface proof** -- six deterministic agent stubs define the trade-execution interface that Cycle-013's autonomous agents must satisfy. Strategies are pure functions of market state and evidence.
5. **Source manifest as commitment artefact** -- OSINT source manifests are validated against the registry, included in the commitment hash, and carried through to the certificate.
6. **Certificate pipeline is single-pass** -- `TheatreResolutionResult` + `SettlementReport` produce a v1.0.0 certificate in one synchronous computation. The certificate passes all 21 `echelon_verify` checks.
7. **Mock-only OSINT** -- WorldMonitor is not deployed locally. All evidence collection uses JSON fixtures. Tests marked `@pytest.mark.live_wm` for future integration.
8. **On-chain anchor is stubbed** -- `MockSepoliaClient` returns deterministic "local_mode" transaction hashes. No blockchain interaction.
9. **MEDIUM-1 carryover fix** -- `p_reality=None` guard added to `ParadoxEngine.scan()` path. The only modification to `backend/engines/`.

---

## 2. System Architecture

### 2.1 Component Topology

```
                                    Sponsor
                                      │
                                      ▼
                          ┌──────────────────────┐
                          │  Sponsored Theatre    │
                          │  API Routes           │
                          │  (sponsored_theatre   │
                          │   _routes.py)         │
                          └──────────┬───────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                    SERVICE LAYER (NEW in 012)                    │
│                                                                 │
│  ┌─────────────────┐  ┌──────────────────┐  ┌───────────────┐  │
│  │ SponsoredTheatre│  │ MarketTheatre    │  │ StubAgents    │  │
│  │ Service         │  │ Bridge           │  │ Spawner       │  │
│  │                 │  │                  │  │               │  │
│  │ • create()      │  │ • create_market  │  │ • spawn()     │  │
│  │ • review()      │  │   _for_theatre() │  │ • execute     │  │
│  │ • commit()      │  │ • get_market     │  │   _tick()     │  │
│  │                 │  │   _state()       │  │               │  │
│  └────────┬────────┘  │ • transition     │  └───────┬───────┘  │
│           │           │   _market()      │          │          │
│           │           └────────┬─────────┘          │          │
│           │                    │                    │          │
│  ┌────────┴────────┐          │          ┌─────────┴────────┐ │
│  │SourceManifest   │          │          │ TheatreEvidence  │ │
│  │ Builder         │          │          │ Collector        │ │
│  └────────┬────────┘          │          └─────────┬────────┘ │
│           │                   │                    │          │
│  ┌────────┴────────────────────────────────────────┴────────┐ │
│  │              Theatre Resolution Engine                    │ │
│  │  • collect_final_evidence()                               │ │
│  │  • evaluate_oracle()  → winning_outcome_index             │ │
│  │  • settle()                                               │ │
│  └────────────────────────────┬──────────────────────────────┘ │
│                               │                                │
│  ┌────────────────────────────┼──────────────────────────────┐ │
│  │              Post-Settlement Pipeline                      │ │
│  │                            │                               │ │
│  │  ┌──────────────┐  ┌──────┴───────┐  ┌────────────────┐  │ │
│  │  │ Certificate  │  │ RLMF Export  │  │ Sponsor        │  │ │
│  │  │ Pipeline     │  │ Generator    │  │ Delivery       │  │ │
│  │  │              │  │              │  │ Package        │  │ │
│  │  │ v1.0.0       │  │ v2.0.1       │  │                │  │ │
│  │  │ schema       │  │ schema       │  │ cert + evidence│  │ │
│  │  │ 21 checks    │  │              │  │ + RLMF + hash  │  │ │
│  │  └──────────────┘  └──────────────┘  └────────────────┘  │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                 │
└────────────────────────────┬────────────────────────────────────┘
                             │
          ┌──────────────────┼──────────────────┐
          │                  │                  │
          ▼                  ▼                  ▼
┌─────────────────┐ ┌───────────────┐ ┌─────────────────┐
│ backend/market/  │ │backend/engines/│ │ backend/osint/  │
│ (010a — frozen)  │ │(010b — frozen) │ │ (011 — frozen)  │
│                  │ │                │ │                  │
│ MarketLifecycle  │ │ ButterflyEngine│ │ CollectionRunner │
│ LMSREngine       │ │ ParadoxEngine  │ │ CorroborationEng│
│ TradingEngine    │ │ EntropyEngine  │ │ CounterSignalEval│
│ PositionManager  │ │ Heartbeat      │ │ Scorer           │
│ ResolutionEngine │ │ VRFProvider    │ │ RegistryLoader   │
│ MarketCommitment │ │ LogicGapCalc   │ │ LiveOSINTReality │
│                  │ │                │ │ Provider         │
└─────────────────┘ └───────────────┘ └─────────────────┘
          │                                     │
          └─────────────────┬───────────────────┘
                            │
                            ▼
                  ┌──────────────────┐
                  │ backend/chain/   │
                  │ MockSepoliaClient│
                  │ (stubbed anchor) │
                  └──────────────────┘
```

### 2.2 Data Flow — Full Lifecycle

```
1. COMMISSION
   Sponsor → SponsoredTheatreConfig → Theatre Creation Service
                                       │
                                       ├─→ Validate sources against registry
                                       ├─→ Build source manifest
                                       ├─→ Create MarketState via MarketLifecycle.create_market()
                                       ├─→ Generate TheatreTemplate
                                       └─→ Return SponsorReviewPackage

2. COMMITMENT
   Sponsor → commit() → MarketCommitment.compute_hash()
                         │
                         ├─→ LMSR params (b, fee_schedule, n_outcomes, outcome_labels)
                         ├─→ Oracle config (committed_sources, resolution_date, corroboration_minimum)
                         └─→ Theatre metadata (template_id, version pins)
                         │
                         └─→ Freeze parameters → MarketPhase.COMMITTED

3. TRADING
   MarketLifecycle.open_trading() → MarketPhase.TRADING
                                     │
                                     ├─→ StubAgents.execute_tick(market_state, evidence)
                                     │    └─→ TradingEngine.execute_trade() per agent decision
                                     │
                                     └─→ TheatreEvidence.collect_heartbeat()
                                          └─→ LiveOSINTRealityProvider (mock fixtures)
                                               └─→ Evidence stored per collection timestamp

4. RESOLUTION
   resolution_date reached → TheatreResolutionEngine.resolve()
                              │
                              ├─→ Final evidence snapshot
                              ├─→ Composed Oracle evaluation
                              │    ├─→ CorroborationEngine.evaluate()
                              │    ├─→ CounterSignalEvaluator.evaluate()
                              │    └─→ Scorer.score() → OracleOutput
                              │
                              ├─→ winning_outcome_index from composite_score thresholds
                              ├─→ MarketLifecycle.begin_resolution(winning_outcome)
                              └─→ ResolutionEngine.settle() → SettlementReport

5. SETTLEMENT → CERTIFICATE → DELIVERY
   SettlementReport + TheatreResolutionResult
     │
     ├─→ CertificatePipeline.generate()
     │    └─→ v1.0.0 schema, 21 echelon_verify checks
     │
     ├─→ RLMFExport.generate()
     │    └─→ v2.0.1 schema
     │
     └─→ SponsorDelivery.assemble()
          └─→ SponsorDeliveryPackage (cert, evidence, RLMF, hash)
```

### 2.3 Phase State Machine

The Theatre lifecycle maps to `MarketPhase` with additional sponsor-level semantics:

```
         Sponsor Lifecycle         LMSR MarketPhase
         ─────────────────         ────────────────
         COMMISSION         ───→   CREATED
              │
         COMMITMENT         ───→   COMMITTED
              │
         TRADING            ───→   TRADING
              │
         RESOLUTION         ───→   RESOLVING
              │
         SETTLEMENT         ───→   SETTLED
              │
         DELIVERY           ───→   (post-SETTLED — certificate generated)
```

All transitions are forward-only. `MarketLifecycle` enforces the constraint. No new phases are introduced.

---

## 3. Technology Stack

| Layer | Technology | Notes |
|-------|-----------|-------|
| Language | Python 3.9.6+ | Same target as 010a-011 |
| Schemas (sponsor-facing) | Pydantic v2 | `SponsoredTheatreConfig`, `SponsorReviewPackage`, `SponsorDeliveryPackage` |
| Schemas (internal) | stdlib `@dataclass` | `StubAgent`, `TradeIntent`, `SourceManifestEntry`, `TheatreResolutionResult`, etc. |
| HTTP framework | FastAPI | Sponsor API routes |
| Database ORM | SQLAlchemy | Theatre/TheatreCertificate records (existing models) |
| Hashing | SHA-256 via `hashlib` | Commitment hash, settlement hash, bundle hash, certificate hash |
| Canonical JSON | `theatre.engine.canonical_json` | RFC 8785 deterministic serialisation |
| Testing | pytest | `@pytest.mark.live_wm` for future WM integration |
| OSINT evidence | Mock JSON fixtures | From `backend/osint/tests/fixtures/` |
| On-chain | `MockSepoliaClient` | Stubbed — deterministic "local_mode" tx hashes |

**No new runtime dependencies.** All new code uses existing packages (FastAPI, Pydantic v2, SQLAlchemy, httpx for mock OSINT).

---

## 4. Component Design

### 4.1 SponsoredTheatreConfig (Pydantic v2 Model)

**File**: `backend/schemas/sponsored_theatre.py`

```python
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator
from backend.market.state import FeeSchedule


class SponsoredTheatreConfig(BaseModel):
    """Sponsor-provided configuration for a Sponsored Theatre.

    Pydantic v2 model — validated on construction.
    """
    question: str = Field(..., min_length=10, max_length=500)
    resolution_date: datetime
    committed_sources: list[str] = Field(..., min_length=1)
    outcome_labels: list[str] = Field(..., min_length=2)
    liquidity_b: Decimal = Field(..., gt=0)
    fee_schedule: FeeSchedule = Field(default_factory=FeeSchedule)
    sponsor_id: str = Field(..., min_length=1)
    sponsor_metadata: dict = Field(default_factory=dict)

    model_config = {"arbitrary_types_allowed": True}

    @field_validator("outcome_labels")
    @classmethod
    def outcome_labels_unique(cls, v: list[str]) -> list[str]:
        if len(v) != len(set(v)):
            raise ValueError("outcome_labels must be unique")
        return v
```

**Field semantics**:
- `question` — the Theatre question, e.g. "Will Acme Ltd file annual accounts by 30 Sep 2026?"
- `resolution_date` — UTC datetime when the market resolves
- `committed_sources` — OSINT registry source IDs for settlement (validated against registry)
- `outcome_labels` — e.g. `["Filed on time", "Filed late", "Not filed"]`
- `liquidity_b` — LMSR `b` parameter. Parameterises liquidity depth, bounds worst-case loss at `b * ln(n)`. NOT escrowed capital.
- `fee_schedule` — `FeeSchedule(trade_fee_bps, resolution_fee_bps)` from `backend/market/state.py`
- `sponsor_id` — sponsor identifier string
- `sponsor_metadata` — freeform context (company name, jurisdiction, etc.)

### 4.2 SourceManifestEntry and SourceManifest

**File**: `backend/osint/source_manifest.py`

```python
from dataclasses import dataclass


class SettlementStatus:
    """Settlement eligibility status for a source in a Theatre's manifest."""
    ELIGIBLE = "ELIGIBLE"
    PROVISIONAL = "PROVISIONAL"
    INELIGIBLE = "INELIGIBLE"


@dataclass
class SourceManifestEntry:
    """Single entry in the OSINT source manifest for a Theatre."""
    source_id: str
    source_group: str
    independence_upstream_id: str
    jurisdiction: str | None
    access_surface: str           # "http_transcript" | "witness_quorum" | "signed_receipt"
    settlement_status: str        # SettlementStatus value
    settlement_eligible: bool
    display_name: str


@dataclass
class SourceManifest:
    """Complete OSINT source manifest for a Theatre's committed sources."""
    entries: list[SourceManifestEntry]
    registry_version: str         # Pinned registry version, e.g. "0.3.2"
    validated: bool               # True if all sources validated against registry
    validation_errors: list[str]  # Empty if validated=True
```

The `SourceManifestBuilder` class builds a `SourceManifest` from a list of registry source IDs:

```python
class SourceManifestBuilder:
    """Builds and validates OSINT source manifests for Theatre committed sources."""

    def __init__(self, registry_loader: RegistryLoader) -> None:
        self._registry = registry_loader

    def build(self, source_ids: list[str]) -> SourceManifest:
        """Build manifest from source IDs. Validates all against registry.

        Sources with shared independence_upstream_id are flagged as PROVISIONAL.
        Sources not in registry produce validation errors.
        """
        ...

    def validate_sources(self, source_ids: list[str]) -> tuple[bool, list[str]]:
        """Validate source IDs exist in registry. Returns (valid, errors)."""
        ...
```

**Provisional source detection**: sources sharing `independence_upstream_id` (e.g., all WM endpoints share `worldmonitor`) are flagged with `settlement_status: PROVISIONAL`. The corroboration penalty (0.7) carries through to the certificate.

### 4.3 SponsorReviewPackage

**File**: `backend/schemas/sponsored_theatre.py`

```python
from pydantic import BaseModel


class SponsorReviewPackage(BaseModel):
    """Package returned to sponsor for review before commitment."""
    theatre_id: str
    template_json: dict                    # Full Theatre template
    commitment_hash: str                   # SHA-256 commitment hash
    worst_case_loss: float                 # b * ln(n)
    source_manifest: dict                  # Serialised SourceManifest
    fee_schedule_breakdown: dict           # trade_fee_bps, resolution_fee_bps
    n_outcomes: int
    outcome_labels: list[str]
    liquidity_b: float
    resolution_date: str                   # ISO 8601
```

### 4.4 Sponsored Theatre Service

**File**: `backend/services/sponsored_theatre.py`

Orchestrates Theatre creation from `SponsoredTheatreConfig`:

```python
class SponsoredTheatreService:
    """Orchestrates the sponsor onboarding workflow."""

    def __init__(
        self,
        registry_loader: RegistryLoader,
        manifest_builder: SourceManifestBuilder,
        chain_client: MockSepoliaClient,
    ) -> None:
        ...

    def create(self, config: SponsoredTheatreConfig) -> SponsorReviewPackage:
        """COMMISSION phase — validate, create LMSR, produce review package.

        Steps:
        1. Validate committed_sources against OSINT registry
        2. Build source manifest (flag PROVISIONAL sources)
        3. Create MarketState via MarketLifecycle.create_market()
        4. Generate TheatreTemplate from config + market
        5. Compute commitment hash via MarketCommitment.compute_hash()
        6. Compute worst-case loss: b * ln(n)
        7. Return SponsorReviewPackage
        """
        ...

    def review(self, theatre_id: str) -> SponsorReviewPackage:
        """Return the SponsorReviewPackage for an existing Theatre."""
        ...

    def commit(self, theatre_id: str) -> dict:
        """COMMITMENT phase — freeze parameters, verify hash, transition phase.

        Steps:
        1. Retrieve Theatre and MarketState
        2. Verify commitment hash matches recomputed hash
        3. MarketLifecycle.commit(market) → COMMITTED
        4. MarketLifecycle.open_trading(market) → TRADING
        5. Stub on-chain anchor (MockSepoliaClient.publish_commitment)
        6. Return confirmation with commitment_hash and on-chain tx_hash
        """
        ...
```

**Interaction with existing modules**:
- Calls `MarketLifecycle.create_market()` (from `backend/market/lifecycle.py`) — no modification
- Calls `MarketCommitment.compute_hash()` (from `backend/market/commitment.py`) — no modification
- Calls `LMSREngine.worst_case_loss()` (from `backend/market/lmsr.py`) — no modification
- Calls `SourceManifestBuilder.build()` (new, `backend/osint/source_manifest.py`)
- Calls `MockSepoliaClient.publish_commitment()` (from `backend/chain/sepolia.py`) — no modification

### 4.5 MarketTheatreBridge

**File**: `backend/services/market_theatre_bridge.py`

Connects the LMSR engine to the Theatre lifecycle without modifying any `backend/market/` code:

```python
from dataclasses import dataclass

from backend.market.lifecycle import MarketLifecycle
from backend.market.lmsr import LMSREngine
from backend.market.positions import PositionManager
from backend.market.resolution import ResolutionEngine, SettlementReport
from backend.market.state import FeeSchedule, MarketPhase, MarketState
from backend.market.trading import Trade, TradingEngine


@dataclass
class TheatreMarketState:
    """Complete LMSR state for a Theatre — wraps market + positions + trading."""
    market: MarketState
    position_manager: PositionManager
    trading_engine: TradingEngine


class MarketTheatreBridge:
    """Bridges LMSR engine to Theatre lifecycle. One instance per application."""

    def __init__(self) -> None:
        self._theatres: dict[str, TheatreMarketState] = {}

    def create_market_for_theatre(
        self,
        theatre_id: str,
        market_id: str,
        b: float,
        n_outcomes: int,
        outcome_labels: list[str],
        fee_schedule: FeeSchedule | None = None,
    ) -> TheatreMarketState:
        """Create LMSR MarketState + PositionManager + TradingEngine for a Theatre.

        Delegates to MarketLifecycle.create_market(). Stores in bridge registry.
        """
        market = MarketLifecycle.create_market(
            market_id=market_id,
            theatre_id=theatre_id,
            b=b,
            n_outcomes=n_outcomes,
            outcome_labels=outcome_labels,
            fee_schedule=fee_schedule,
        )
        pm = PositionManager(n_outcomes=n_outcomes, market_id=market_id)
        te = TradingEngine(position_manager=pm)
        state = TheatreMarketState(market=market, position_manager=pm, trading_engine=te)
        self._theatres[theatre_id] = state
        return state

    def get_market_state(self, theatre_id: str) -> TheatreMarketState | None:
        """Return current LMSR state for a Theatre."""
        return self._theatres.get(theatre_id)

    def transition_market(self, theatre_id: str, target_phase: MarketPhase) -> MarketState:
        """Validate and execute phase transition.

        Delegates to appropriate MarketLifecycle static method:
        - CREATED → COMMITTED: MarketLifecycle.commit()
        - COMMITTED → TRADING: MarketLifecycle.open_trading()
        - TRADING → RESOLVING: MarketLifecycle.begin_resolution()
        - RESOLVING → SETTLED: via ResolutionEngine.settle()
        """
        ...

    def settle_market(
        self, theatre_id: str, winning_outcome: int
    ) -> SettlementReport:
        """Execute resolution + settlement in one call.

        1. MarketLifecycle.begin_resolution(market, winning_outcome)
        2. ResolutionEngine.settle(market, position_manager)
        3. Return SettlementReport
        """
        ...

    def serialise_state(self, theatre_id: str) -> dict:
        """Serialise LMSR MarketState to JSON-compatible dict for Theatre record."""
        ...

    @staticmethod
    def deserialise_state(data: dict) -> MarketState:
        """Reconstruct MarketState from JSON dict."""
        ...
```

**Design rationale**: The bridge owns the `TheatreMarketState` triple (`MarketState` + `PositionManager` + `TradingEngine`) and mediates all access. This ensures:
- No direct mutation of `backend/market/` internals from service code
- Clean serialisation boundary for database persistence
- Testable in isolation from Theatre infrastructure

### 4.6 StubAgent System

**File**: `backend/services/stub_agents.py`

```python
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Optional

from backend.market.state import MarketState
from backend.market.trading import Trade


class AgentArchetype(str, Enum):
    """Six agent archetypes with named trading patterns."""
    SHARK = "shark"           # Momentum exploitation
    SPY = "spy"               # Intel arbitrage
    DIPLOMAT = "diplomat"     # Stability maintenance
    SABOTEUR = "saboteur"     # Chaos creation
    WHALE = "whale"           # Market moving
    DEGEN = "degen"           # Volatility harvesting


@dataclass
class TradeIntent:
    """Agent's intended trade — validated before execution."""
    outcome_index: int
    shares: float
    trigger: str              # Human-readable trigger condition
    confidence: float         # 0.0-1.0


@dataclass
class TradeDecisionTrace:
    """Full trace of an agent's decision for RLMF export."""
    agent_id: str
    archetype: str
    tick: int
    trigger_condition: str
    market_prices_at_decision: list[float]
    confidence: float
    intent: TradeIntent | None        # None = no-op decision
    executed_trade: Trade | None      # None if intent was None or execution failed
    pattern_name: str                 # Named pattern from archetype matrix


@dataclass
class StubAgent:
    """Stub agent — identity + deterministic strategy.

    Strategy is a pure function: (market_state, evidence, tick) → Optional[TradeIntent]
    """
    agent_id: str
    archetype: AgentArchetype
    initial_balance: float
    strategy: Callable[
        [MarketState, list | None, int],
        TradeIntent | None,
    ]
```

**Strategy functions** (one per archetype):

| Archetype | Pattern Name | Strategy Logic |
|-----------|-------------|----------------|
| Shark | momentum_exploitation | Buy leading outcome if price < 0.7. Exploits momentum. |
| Spy | intel_arbitrage | Trade when new evidence arrives. Evidence-triggered only. |
| Diplomat | stability_maintenance | Buy trailing outcome if price spread > 0.4. Stabilises. |
| Saboteur | chaos_creation | Random contrary trades at low volume (1-3 shares). |
| Whale | market_moving | Single large position (50+ shares) on tick 0, hold. |
| Degen | volatility_harvesting | Random outcome, random volume (1-10 shares), every tick. |

```python
class StubAgentSpawner:
    """Creates stub agent populations for a Theatre."""

    DEFAULT_AGENT_COUNT = 6
    DEFAULT_INITIAL_BALANCE = 1000.0

    def spawn(
        self,
        theatre_id: str,
        agent_count: int = DEFAULT_AGENT_COUNT,
        initial_balance: float = DEFAULT_INITIAL_BALANCE,
    ) -> list[StubAgent]:
        """Spawn one agent per archetype with default strategies.

        Returns list of StubAgent with deterministic agent_ids:
        "{theatre_id}_shark", "{theatre_id}_spy", etc.
        """
        ...

    @staticmethod
    def execute_tick(
        agents: list[StubAgent],
        market_state: MarketState,
        trading_engine: TradingEngine,
        position_manager: PositionManager,
        evidence: list | None,
        tick: int,
    ) -> list[TradeDecisionTrace]:
        """Execute one trading tick for all agents.

        For each agent:
        1. Call strategy(market_state, evidence, tick) → Optional[TradeIntent]
        2. If intent is not None, call TradingEngine.execute_trade()
        3. Record TradeDecisionTrace for RLMF export

        Returns list of traces (one per agent, including no-op decisions).
        """
        ...
```

**Critical constraint**: Stub agents call `TradingEngine.execute_trade()` directly. No agent runtime, no LLM, no autonomous decision-making. They are throwaway code replaced by Cycle-013.

### 4.7 Theatre Evidence Collector

**File**: `backend/services/theatre_evidence.py`

```python
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class EvidenceSnapshot:
    """Evidence collected at a single heartbeat tick."""
    theatre_id: str
    collection_timestamp: datetime
    oracle_output: object              # OracleOutput from Scorer
    evidence_bundles: list             # List of EvidenceBundle
    collection_results: list           # List of CollectionResult
    source_coverage_pct: float         # Successful / total sources


class TheatreEvidenceCollector:
    """Orchestrates OSINT evidence collection per heartbeat cadence.

    Uses LiveOSINTRealityProvider from Cycle-011 with mock WM fixtures.
    Evidence stored in-memory keyed by collection timestamp.
    """

    def __init__(
        self,
        reality_provider: LiveOSINTRealityProvider,
        committed_sources: list[str],
    ) -> None:
        self._provider = reality_provider
        self._sources = committed_sources
        self._snapshots: list[EvidenceSnapshot] = []

    def collect_heartbeat(self, theatre_id: str) -> EvidenceSnapshot:
        """Collect evidence for all committed sources. Called per heartbeat tick.

        1. Call LiveOSINTRealityProvider.get_signal(theatre_id)
        2. Extract OracleOutput from provider cache
        3. Build EvidenceSnapshot with coverage metrics
        4. Store in snapshot history
        """
        ...

    def get_evidence_history(self) -> list[EvidenceSnapshot]:
        """Return all collected evidence snapshots."""
        return list(self._snapshots)

    def get_latest_evidence(self) -> EvidenceSnapshot | None:
        """Return most recent evidence snapshot, or None if no collection yet."""
        return self._snapshots[-1] if self._snapshots else None

    def compute_coverage_pct(self) -> float:
        """Latest source coverage: successful / total sources."""
        ...
```

### 4.8 Theatre Resolution Engine

**File**: `backend/services/theatre_resolution.py`

```python
from dataclasses import dataclass


@dataclass
class TheatreResolutionResult:
    """Result of Theatre resolution — input to certificate pipeline."""
    theatre_id: str
    oracle_output_id: str              # "{theatre_id}_{epoch_ms}"
    composite_score: float             # 0.0-1.0
    winning_outcome_index: int         # Discrete index into outcome_labels
    winning_outcome_label: str
    evidence_bundle_hash: str          # SHA-256
    evidence_snapshots: list           # All EvidenceSnapshot collected
    corroboration_result: object       # CorroborationResult
    counter_signal_results: list       # List of CounterSignalResult
    criterion_scores: list             # List of CriterionScore
    source_manifest: object            # SourceManifest


class TheatreResolutionEngine:
    """Resolves a Theatre when resolution_date arrives.

    Orchestrates: final evidence → Composed Oracle → winning outcome → settlement.
    """

    def __init__(
        self,
        evidence_collector: TheatreEvidenceCollector,
        scorer: Scorer,
        corroboration_engine: CorroborationEngine,
        counter_signal_evaluator: CounterSignalEvaluator,
        source_manifest: SourceManifest,
        oracle_config: dict,
    ) -> None:
        ...

    def resolve(self, theatre_id: str) -> TheatreResolutionResult:
        """Full resolution pipeline.

        Steps:
        1. Collect final evidence snapshot
        2. Run CorroborationEngine.evaluate() on all collection results
        3. Run CounterSignalEvaluator.evaluate() on collection results
        4. Run Scorer.score() → OracleOutput
        5. Determine winning_outcome_index from composite_score:
           - For n-outcome markets, map composite_score to outcome thresholds
           - Companies House Theatre (3 outcomes):
             score >= 0.7 → outcome 0 ("Filed on time")
             0.3 <= score < 0.7 → outcome 1 ("Filed late")
             score < 0.3 → outcome 2 ("Not filed")
        6. Build TheatreResolutionResult

        Returns TheatreResolutionResult with oracle_output_id, composite_score,
        winning_outcome_index, evidence_bundle_hash.
        """
        ...

    def _determine_winning_outcome(
        self,
        composite_score: float,
        n_outcomes: int,
        outcome_labels: list[str],
    ) -> int:
        """Map composite_score to discrete winning_outcome_index.

        For n-outcome markets, divide [0, 1] into n equal bands.
        Highest band = outcome 0 (most positive), lowest = outcome n-1.
        """
        ...
```

**Oracle evaluation flow** (delegates to existing 011 modules):

```
TheatreResolutionEngine.resolve()
    │
    ├─→ TheatreEvidenceCollector.collect_heartbeat()
    │    └─→ LiveOSINTRealityProvider.get_signal()
    │         └─→ CollectionRunner.collect() → list[CollectionResult]
    │
    ├─→ CorroborationEngine.evaluate(results, oracle_config)
    │    └─→ CorroborationResult (provisional: 0.7 penalty)
    │
    ├─→ CounterSignalEvaluator.evaluate(results, oracle_config)
    │    └─→ list[CounterSignalResult] (all UNAVAILABLE / INTELLIGENCE_GAP)
    │
    └─→ Scorer.score(corroboration, counter_signals, results, config, theatre_id)
         └─→ OracleOutput (composite_score, criterion_scores, bundle_hash)
```

### 4.9 Certificate Generation Pipeline

**File**: `backend/services/certificate_pipeline.py`

```python
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class CalibrationCertificate:
    """v1.0.0 calibration certificate schema.

    Replaces 010b's certificate_id with oracle_output_id.
    Carries full evidence provenance chain.
    """
    oracle_output_id: str               # "{theatre_id}_{epoch_ms}"
    theatre_id: str
    composite_score: float              # 0.0-1.0
    evidence_bundle_hash: str           # SHA-256 manifest pattern hash
    criteria_breakdown: list[dict]      # Per-criterion pass/fail with evidence refs
    osint_source_manifest: dict         # Serialised SourceManifest
    corroboration_status: dict          # {minimum_met, penalty_factor, distinct_groups}
    counter_signal_results: list[dict]  # Per-class outcome + detail
    verification_tier: str              # "UNVERIFIED" for first local-mode Theatre
    scored_at: str                      # ISO 8601
    provider_version: str               # e.g. "012.1"
    settlement_hash: str                # From SettlementReport
    commitment_hash: str                # From MarketState
    winning_outcome: int
    winning_outcome_label: str
    schema_version: str = "1.0.0"


class CertificatePipeline:
    """Produces calibration certificates from settlement results."""

    SCHEMA_VERSION = "1.0.0"
    PROVIDER_VERSION = "012.1"

    def generate(
        self,
        resolution_result: TheatreResolutionResult,
        settlement_report: SettlementReport,
    ) -> CalibrationCertificate:
        """Generate certificate from resolution + settlement.

        Steps:
        1. Build criteria_breakdown from resolution_result.criterion_scores
        2. Serialise source_manifest
        3. Build corroboration_status:
           - minimum_met: False (provisional — WM-only)
           - penalty_factor: 0.7
           - distinct_source_groups: 1
        4. Build counter_signal_results:
           - All 11 classes: UNAVAILABLE, INTELLIGENCE_GAP
        5. Set verification_tier: "UNVERIFIED"
           (BACKTESTED requires 50+ replay runs, not available in 012)
        6. Assemble CalibrationCertificate
        """
        ...

    def verify(self, certificate: CalibrationCertificate) -> tuple[bool, list[str]]:
        """Run certificate through echelon_verify — 21 checks.

        Returns (all_passed, list_of_check_results).
        """
        ...
```

**Certificate v1.0.0 schema fields**:

| Field | Type | Source |
|-------|------|--------|
| `oracle_output_id` | str | `"{theatre_id}_{epoch_ms}"` |
| `composite_score` | float | `OracleOutput.composite_score` |
| `evidence_bundle_hash` | str | Manifest pattern: `{bundle_id: content_hash}` -> canonical JSON -> SHA-256 |
| `criteria_breakdown` | list[dict] | Per-criterion pass/fail with evidence references |
| `osint_source_manifest` | dict | Serialised `SourceManifest` |
| `corroboration_status` | dict | `{minimum_met: false, penalty_factor: 0.7, distinct_source_groups: 1}` |
| `counter_signal_results` | list[dict] | 11 entries, all UNAVAILABLE/INTELLIGENCE_GAP |
| `verification_tier` | str | `"UNVERIFIED"` |
| `scored_at` | str | ISO 8601 UTC |
| `provider_version` | str | `"012.1"` |
| `settlement_hash` | str | From `SettlementReport.settlement_hash` |
| `commitment_hash` | str | From `MarketState.commitment_hash` |

**UNVERIFIED tier rationale**: BACKTESTED requires 50+ replay runs against historical data, which 012 does not produce. The first local-mode Theatre earns UNVERIFIED, which is honest.

**21 `echelon_verify` checks** (must all pass):

1. `oracle_output_id` present and non-empty
2. `oracle_output_id` format: `{theatre_id}_{epoch_ms}`
3. `composite_score` in range [0.0, 1.0]
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
14. `verification_tier` is a known value (UNVERIFIED, BACKTESTED, VERIFIED)
15. `scored_at` is valid ISO 8601
16. `provider_version` present and non-empty
17. `settlement_hash` is valid SHA-256 hex
18. `commitment_hash` is valid SHA-256 hex
19. `winning_outcome` is a valid index
20. `schema_version` matches "1.0.0"
21. Certificate JSON is deterministically re-serialisable (canonical JSON roundtrip)

### 4.10 RLMF Export Generator

**File**: `backend/services/rlmf_export.py`

```python
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class MarketEpoch:
    """Market state snapshot at a single epoch (tick)."""
    tick: int
    timestamp: str                      # ISO 8601
    prices: list[float]                 # Current outcome prices
    x_vector: list[float]              # LMSR x vector
    total_trades: int
    trade_count_this_tick: int


@dataclass
class AgentTrace:
    """Complete trace for one agent across all ticks."""
    agent_id: str
    archetype: str
    initial_balance: float
    final_balance: float
    total_trades: int
    total_pnl: float
    decision_traces: list[dict]         # TradeDecisionTrace serialised


@dataclass
class CalibrationMetrics:
    """Calibration quality metrics computed at settlement."""
    brier_score: float                  # Mean squared error of probability forecasts
    expected_calibration_error: float   # ECE across probability bins
    resolution: float                   # Brier decomposition: resolution component
    reliability: float                  # Brier decomposition: reliability component


@dataclass
class RLMFExport:
    """RLMF training data export — schema v2.0.1.

    Captures the complete information needed to train
    Reinforcement Learning from Market Feedback models.
    """
    schema_version: str = "2.0.1"
    oracle_output_id: str = ""
    theatre_id: str = ""
    question: str = ""
    outcome_labels: list[str] = field(default_factory=list)
    winning_outcome: int = 0
    winning_outcome_label: str = ""

    # Probability distributions per epoch
    epochs: list[MarketEpoch] = field(default_factory=list)

    # Agent decision traces
    agent_traces: list[AgentTrace] = field(default_factory=list)

    # Calibration metrics
    calibration: CalibrationMetrics | None = None

    # Per-agent P&L
    agent_pnl: dict[str, float] = field(default_factory=dict)

    # Settlement metadata
    composite_score: float = 0.0
    evidence_bundle_hash: str = ""
    settlement_hash: str = ""
    exported_at: str = ""


class RLMFExportGenerator:
    """Generates RLMF training data from Theatre lifecycle artifacts."""

    SCHEMA_VERSION = "2.0.1"

    def generate(
        self,
        theatre_id: str,
        question: str,
        outcome_labels: list[str],
        winning_outcome: int,
        oracle_output_id: str,
        epochs: list[MarketEpoch],
        agent_traces: list[AgentTrace],
        settlement_report: SettlementReport,
        resolution_result: TheatreResolutionResult,
    ) -> RLMFExport:
        """Assemble RLMF export from all lifecycle artifacts.

        Steps:
        1. Compute Brier score from final probabilities vs outcome
        2. Compute ECE from probability distribution history
        3. Build per-agent P&L from settlement report
        4. Assemble RLMFExport with schema_version 2.0.1
        """
        ...

    @staticmethod
    def compute_brier_score(
        final_prices: list[float],
        winning_outcome: int,
    ) -> float:
        """Brier score = (1/n) * sum((p_i - o_i)^2)

        Where o_i = 1 if i == winning_outcome else 0.
        Range [0, 2]. Lower is better.
        """
        ...

    @staticmethod
    def compute_ece(
        epochs: list[MarketEpoch],
        winning_outcome: int,
        n_bins: int = 10,
    ) -> float:
        """Expected Calibration Error across probability bins.

        Bins the winning outcome's price across all epochs into n_bins.
        ECE = weighted average of |accuracy - confidence| per bin.
        """
        ...
```

### 4.11 Sponsor Delivery Package

**File**: `backend/services/sponsor_delivery.py`

```python
from dataclasses import dataclass


@dataclass
class SponsorDeliveryPackage:
    """Final deliverable for the sponsor after settlement."""
    theatre_id: str
    certificate: dict                   # CalibrationCertificate serialised
    evidence_bundle: dict               # Complete artefact: template, ground truth,
                                        # HTTP receipts, per-episode scores, gap reports
    rlmf_export: dict                   # RLMFExport serialised
    commitment_hash: str                # For future on-chain anchoring
    echelon_status_url: str             # MCP tool endpoint URL


class SponsorDeliveryAssembler:
    """Assembles the sponsor delivery package from all post-settlement artifacts."""

    def assemble(
        self,
        theatre_id: str,
        certificate: CalibrationCertificate,
        evidence_snapshots: list[EvidenceSnapshot],
        rlmf_export: RLMFExport,
        commitment_hash: str,
        source_manifest: SourceManifest,
    ) -> SponsorDeliveryPackage:
        """Bundle all deliverables into SponsorDeliveryPackage.

        Steps:
        1. Serialise certificate to dict
        2. Build evidence bundle artefact:
           - Committed template JSON
           - Ground truth (winning outcome + composite score)
           - HTTP transcript receipts from evidence bundles
           - Per-episode scores from evidence snapshots
           - Gap reports (INTELLIGENCE_GAP counter-signals)
        3. Serialise RLMF export to dict
        4. Include commitment hash
        5. Build echelon_status endpoint URL
        """
        ...
```

### 4.12 Sponsor API Routes

**File**: `backend/api/sponsored_theatre_routes.py`

Three endpoints on the FastAPI router:

```python
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/v1/sponsored-theatres", tags=["sponsored-theatres"])


@router.post("/", status_code=201)
async def create_sponsored_theatre(config: SponsoredTheatreConfig) -> dict:
    """Create a sponsored Theatre in CREATED state.

    Request body: SponsoredTheatreConfig (Pydantic v2 validated)
    Response: {theatre_id, status: "CREATED", commitment_hash}
    """
    ...


@router.get("/{theatre_id}/review")
async def review_sponsored_theatre(theatre_id: str) -> SponsorReviewPackage:
    """Return SponsorReviewPackage for sponsor approval.

    Response: SponsorReviewPackage (template, hash, worst-case loss, manifest, fees)
    """
    ...


@router.post("/{theatre_id}/commit")
async def commit_sponsored_theatre(theatre_id: str) -> dict:
    """Sponsor approves — freeze parameters, transition to COMMITTED.

    Response: {theatre_id, status: "COMMITTED", commitment_hash, tx_hash}
    """
    ...
```

### 4.13 echelon_status Theatre Integration

The existing `market_status_snapshot()` function in `backend/engines/status.py` is extended via a new wrapper in the service layer (not modifying `status.py`):

```python
@dataclass
class TheatreStatusSnapshot:
    """Extended status for echelon_status MCP tool with Theatre context."""
    # From existing MarketStatusSnapshot
    theatre_id: str
    market_phase: str
    current_prices: list[float]
    total_trades: int
    timeline_stability: float
    logic_gap_status: str | None
    logic_gap_value: float | None
    heartbeat_ticks: dict[str, int]
    commitment_hash: str
    on_chain: bool

    # Theatre-specific extensions (012)
    evidence_coverage_pct: float | None         # During TRADING
    sources_online: int | None                  # During TRADING
    sources_total: int | None                   # During TRADING
    certificate_state: str | None               # After SETTLEMENT: "VALID" | None
    composite_score: float | None               # After SETTLEMENT
    counter_signal_status: str | None           # After SETTLEMENT: "PASS" | "FAIL"
    verification_tier: str | None               # After SETTLEMENT: "UNVERIFIED"

    # Cache metadata
    cached_at: str | None = None
    ttl_seconds: int = 300
```

---

## 5. Data Architecture

### 5.1 New Pydantic Models (Sponsor-Facing)

| Model | File | Key Fields |
|-------|------|------------|
| `SponsoredTheatreConfig` | `backend/schemas/sponsored_theatre.py` | question, resolution_date, committed_sources, outcome_labels, liquidity_b, fee_schedule, sponsor_id, sponsor_metadata |
| `SponsorReviewPackage` | `backend/schemas/sponsored_theatre.py` | theatre_id, template_json, commitment_hash, worst_case_loss, source_manifest, fee_schedule_breakdown, n_outcomes, outcome_labels, liquidity_b, resolution_date |
| `SponsorDeliveryPackage` | `backend/services/sponsor_delivery.py` | theatre_id, certificate, evidence_bundle, rlmf_export, commitment_hash, echelon_status_url |

### 5.2 New Dataclasses (Internal)

| Dataclass | File | Key Fields |
|-----------|------|------------|
| `SourceManifestEntry` | `backend/osint/source_manifest.py` | source_id, source_group, independence_upstream_id, jurisdiction, access_surface, settlement_status, settlement_eligible, display_name |
| `SourceManifest` | `backend/osint/source_manifest.py` | entries, registry_version, validated, validation_errors |
| `TheatreMarketState` | `backend/services/market_theatre_bridge.py` | market: MarketState, position_manager: PositionManager, trading_engine: TradingEngine |
| `TradeIntent` | `backend/services/stub_agents.py` | outcome_index, shares, trigger, confidence |
| `TradeDecisionTrace` | `backend/services/stub_agents.py` | agent_id, archetype, tick, trigger_condition, market_prices_at_decision, confidence, intent, executed_trade, pattern_name |
| `StubAgent` | `backend/services/stub_agents.py` | agent_id, archetype: AgentArchetype, initial_balance, strategy |
| `EvidenceSnapshot` | `backend/services/theatre_evidence.py` | theatre_id, collection_timestamp, oracle_output, evidence_bundles, collection_results, source_coverage_pct |
| `TheatreResolutionResult` | `backend/services/theatre_resolution.py` | theatre_id, oracle_output_id, composite_score, winning_outcome_index, winning_outcome_label, evidence_bundle_hash, evidence_snapshots, corroboration_result, counter_signal_results, criterion_scores, source_manifest |
| `CalibrationCertificate` | `backend/services/certificate_pipeline.py` | oracle_output_id, theatre_id, composite_score, evidence_bundle_hash, criteria_breakdown, osint_source_manifest, corroboration_status, counter_signal_results, verification_tier, scored_at, provider_version, settlement_hash, commitment_hash, winning_outcome, winning_outcome_label, schema_version |
| `MarketEpoch` | `backend/services/rlmf_export.py` | tick, timestamp, prices, x_vector, total_trades, trade_count_this_tick |
| `AgentTrace` | `backend/services/rlmf_export.py` | agent_id, archetype, initial_balance, final_balance, total_trades, total_pnl, decision_traces |
| `CalibrationMetrics` | `backend/services/rlmf_export.py` | brier_score, expected_calibration_error, resolution, reliability |
| `RLMFExport` | `backend/services/rlmf_export.py` | schema_version, oracle_output_id, theatre_id, question, outcome_labels, winning_outcome, epochs, agent_traces, calibration, agent_pnl, composite_score, evidence_bundle_hash, settlement_hash, exported_at |
| `TheatreStatusSnapshot` | `backend/services/theatre_status.py` | (extends MarketStatusSnapshot) evidence_coverage_pct, sources_online, sources_total, certificate_state, composite_score, counter_signal_status, verification_tier, cached_at, ttl_seconds |

### 5.3 Enums

| Enum | File | Values |
|------|------|--------|
| `AgentArchetype` | `backend/services/stub_agents.py` | SHARK, SPY, DIPLOMAT, SABOTEUR, WHALE, DEGEN |
| `SettlementStatus` | `backend/osint/source_manifest.py` | ELIGIBLE, PROVISIONAL, INELIGIBLE |

### 5.4 Existing Dataclasses Consumed (Not Modified)

| Dataclass | Module | Used By |
|-----------|--------|---------|
| `MarketState` | `backend/market/state.py` | MarketTheatreBridge, StubAgentSpawner, TheatreResolutionEngine |
| `MarketPhase` | `backend/market/state.py` | MarketTheatreBridge phase transitions |
| `FeeSchedule` | `backend/market/state.py` | SponsoredTheatreConfig |
| `Trade` | `backend/market/trading.py` | StubAgent execution, TradeDecisionTrace |
| `AgentPosition` | `backend/market/positions.py` | Settlement, RLMF export |
| `AgentSettlement` | `backend/market/resolution.py` | Certificate pipeline, RLMF export |
| `SettlementReport` | `backend/market/resolution.py` | Certificate pipeline, RLMF export |
| `OracleOutput` | `backend/osint/engine/scorer.py` | TheatreResolutionEngine, evidence collection |
| `CorroborationResult` | `backend/osint/engine/corroboration.py` | Certificate pipeline |
| `CounterSignalResult` | `backend/osint/engine/counter_signal.py` | Certificate pipeline |
| `CriterionScore` | `backend/osint/engine/scorer.py` | Certificate pipeline |
| `CollectionResult` | `backend/osint/models/evidence.py` | TheatreEvidenceCollector |
| `RealitySignal` | `backend/engines/reality_signal.py` | TheatreEvidenceCollector |
| `RegistrySource` | `backend/osint/models/registry.py` | SourceManifestBuilder |
| `TxReceipt` | `backend/chain/sepolia.py` | SponsoredTheatreService (on-chain stub) |

### 5.5 Commitment Hash Composition (Extended)

The existing `MarketCommitment.compute_hash()` uses `ORACLE_CONFIG_STUB = {"type": "manual", "version": "v0"}`. For 012, the Theatre creation service computes a separate commitment hash that covers the full oracle config:

```python
# Commitment composite object (012 extension)
commitment_composite = {
    "b": market.b,
    "n_outcomes": market.n_outcomes,
    "outcome_labels": market.outcome_labels,
    "fee_schedule": {
        "trade_fee_bps": fee_schedule.trade_fee_bps,
        "resolution_fee_bps": fee_schedule.resolution_fee_bps,
    },
    "oracle_config": {
        "committed_sources": sorted(committed_sources),
        "resolution_date": resolution_date.isoformat(),
        "corroboration_minimum": 2,
    },
    "theatre_metadata": {
        "template_id": template_id,
        "version_pins": {"market": "010a", "engines": "010b", "osint": "011"},
    },
}
# SHA-256(canonical_json(commitment_composite))
```

The existing `MarketCommitment.compute_hash(market)` is still called for the LMSR-level hash (stored in `MarketState.commitment_hash`). The Theatre-level commitment hash extends this by including oracle config and theatre metadata. Both hashes are stored and both are verifiable.

---

## 6. API Design

### 6.1 Sponsor Endpoints (HTTP)

| Method | Path | Request Body | Response | Phase |
|--------|------|-------------|----------|-------|
| POST | `/api/v1/sponsored-theatres` | `SponsoredTheatreConfig` | `{theatre_id, status, commitment_hash}` | COMMISSION |
| GET | `/api/v1/sponsored-theatres/{id}/review` | - | `SponsorReviewPackage` | COMMISSION |
| POST | `/api/v1/sponsored-theatres/{id}/commit` | - | `{theatre_id, status, commitment_hash, tx_hash}` | COMMITMENT |

### 6.2 Internal Python APIs (In-Memory, Not HTTP)

| Class | Method | Input | Output |
|-------|--------|-------|--------|
| `SponsoredTheatreService` | `create(config)` | SponsoredTheatreConfig | SponsorReviewPackage |
| `SponsoredTheatreService` | `review(theatre_id)` | str | SponsorReviewPackage |
| `SponsoredTheatreService` | `commit(theatre_id)` | str | dict |
| `MarketTheatreBridge` | `create_market_for_theatre(...)` | theatre_id, b, n_outcomes, etc. | TheatreMarketState |
| `MarketTheatreBridge` | `get_market_state(theatre_id)` | str | TheatreMarketState |
| `MarketTheatreBridge` | `transition_market(theatre_id, phase)` | str, MarketPhase | MarketState |
| `MarketTheatreBridge` | `settle_market(theatre_id, winning)` | str, int | SettlementReport |
| `StubAgentSpawner` | `spawn(theatre_id, count, balance)` | str, int, float | list[StubAgent] |
| `StubAgentSpawner` | `execute_tick(agents, market, ...)` | agents, state, tick | list[TradeDecisionTrace] |
| `SourceManifestBuilder` | `build(source_ids)` | list[str] | SourceManifest |
| `TheatreEvidenceCollector` | `collect_heartbeat(theatre_id)` | str | EvidenceSnapshot |
| `TheatreResolutionEngine` | `resolve(theatre_id)` | str | TheatreResolutionResult |
| `CertificatePipeline` | `generate(resolution, settlement)` | TheatreResolutionResult, SettlementReport | CalibrationCertificate |
| `CertificatePipeline` | `verify(certificate)` | CalibrationCertificate | (bool, list[str]) |
| `RLMFExportGenerator` | `generate(...)` | lifecycle artifacts | RLMFExport |
| `SponsorDeliveryAssembler` | `assemble(...)` | post-settlement artifacts | SponsorDeliveryPackage |

---

## 7. Integration Points

### 7.1 Theatre Service -> LMSR Engine (backend/market/)

| Service Method | LMSR Method Called | Module |
|---------------|-------------------|---------|
| `SponsoredTheatreService.create()` | `MarketLifecycle.create_market()` | `lifecycle.py` |
| `SponsoredTheatreService.create()` | `MarketCommitment.compute_hash()` | `commitment.py` |
| `SponsoredTheatreService.create()` | `LMSREngine.worst_case_loss()` | `lmsr.py` |
| `SponsoredTheatreService.commit()` | `MarketLifecycle.commit()` | `lifecycle.py` |
| `SponsoredTheatreService.commit()` | `MarketLifecycle.open_trading()` | `lifecycle.py` |
| `SponsoredTheatreService.commit()` | `MarketCommitment.verify_hash()` | `commitment.py` |
| `StubAgentSpawner.execute_tick()` | `TradingEngine.execute_trade()` | `trading.py` |
| `MarketTheatreBridge.settle_market()` | `MarketLifecycle.begin_resolution()` | `lifecycle.py` |
| `MarketTheatreBridge.settle_market()` | `ResolutionEngine.settle()` | `resolution.py` |

**Zero modifications to `backend/market/`.**

### 7.2 Theatre Service -> Engines (backend/engines/)

| Service Method | Engine Method Called | Module |
|---------------|---------------------|---------|
| `TheatreEvidenceCollector.collect_heartbeat()` | `LiveOSINTRealityProvider.get_signal()` | `reality_signal.py` |
| `TheatreStatusSnapshot` builder | `market_status_snapshot()` | `status.py` |

**Sole modification**: `ParadoxEngine.scan()` path gains a `p_reality=None` guard (MEDIUM-1 fix).

### 7.3 Theatre Service -> OSINT Pipeline (backend/osint/)

| Service Method | OSINT Method Called | Module |
|---------------|---------------------|---------|
| `SourceManifestBuilder.build()` | `RegistryLoader.get_source()` | `models/registry.py` |
| `TheatreEvidenceCollector` | `CollectionRunner.collect()` | `engine/collection_runner.py` |
| `TheatreResolutionEngine.resolve()` | `CorroborationEngine.evaluate()` | `engine/corroboration.py` |
| `TheatreResolutionEngine.resolve()` | `CounterSignalEvaluator.evaluate()` | `engine/counter_signal.py` |
| `TheatreResolutionEngine.resolve()` | `Scorer.score()` | `engine/scorer.py` |
| `CertificatePipeline.generate()` | `Scorer.compute_bundle_hash()` | `engine/scorer.py` |

**Zero modifications to `backend/osint/`.**

### 7.4 Theatre Service -> Chain (backend/chain/)

| Service Method | Chain Method Called | Module |
|---------------|-------------------|---------|
| `SponsoredTheatreService.commit()` | `MockSepoliaClient.publish_commitment()` | `sepolia.py` |

**Zero modifications to `backend/chain/`.**

### 7.5 Integration Diagram — Module Dependencies

```
backend/schemas/sponsored_theatre.py
    │
    └─→ backend/market/state.py (FeeSchedule import)

backend/services/sponsored_theatre.py
    │
    ├─→ backend/schemas/sponsored_theatre.py (SponsoredTheatreConfig, SponsorReviewPackage)
    ├─→ backend/market/lifecycle.py (MarketLifecycle)
    ├─→ backend/market/commitment.py (MarketCommitment)
    ├─→ backend/market/lmsr.py (LMSREngine.worst_case_loss)
    ├─→ backend/osint/source_manifest.py (SourceManifestBuilder)
    └─→ backend/chain/sepolia.py (MockSepoliaClient)

backend/services/market_theatre_bridge.py
    │
    ├─→ backend/market/lifecycle.py (MarketLifecycle)
    ├─→ backend/market/trading.py (TradingEngine)
    ├─→ backend/market/positions.py (PositionManager)
    ├─→ backend/market/resolution.py (ResolutionEngine)
    └─→ backend/market/lmsr.py (LMSREngine)

backend/services/stub_agents.py
    │
    ├─→ backend/market/state.py (MarketState)
    ├─→ backend/market/trading.py (TradingEngine, Trade)
    └─→ backend/market/positions.py (PositionManager)

backend/services/theatre_evidence.py
    │
    └─→ backend/engines/reality_signal.py (LiveOSINTRealityProvider)

backend/services/theatre_resolution.py
    │
    ├─→ backend/osint/engine/corroboration.py (CorroborationEngine)
    ├─→ backend/osint/engine/counter_signal.py (CounterSignalEvaluator)
    ├─→ backend/osint/engine/scorer.py (Scorer, OracleOutput)
    └─→ backend/services/theatre_evidence.py (TheatreEvidenceCollector)

backend/services/certificate_pipeline.py
    │
    ├─→ backend/services/theatre_resolution.py (TheatreResolutionResult)
    ├─→ backend/market/resolution.py (SettlementReport)
    └─→ backend/osint/engine/scorer.py (Scorer.compute_bundle_hash)

backend/services/rlmf_export.py
    │
    ├─→ backend/market/resolution.py (SettlementReport)
    └─→ backend/services/theatre_resolution.py (TheatreResolutionResult)

backend/services/sponsor_delivery.py
    │
    ├─→ backend/services/certificate_pipeline.py (CalibrationCertificate)
    ├─→ backend/services/rlmf_export.py (RLMFExport)
    └─→ backend/services/theatre_evidence.py (EvidenceSnapshot)
```

---

## 8. Testing Architecture

### 8.1 Test Structure

```
backend/services/tests/
├── test_sponsored_theatre.py          # Sprint 1: creation, validation, commitment
├── test_market_theatre_bridge.py      # Sprint 1: LMSR bridge tests
├── test_stub_agents.py                # Sprint 1: agent spawning, strategies, trading
├── test_theatre_resolution.py         # Sprint 2: resolution engine tests
├── test_certificate_pipeline.py       # Sprint 2: certificate generation, verification
├── test_rlmf_export.py               # Sprint 2: RLMF schema conformance
└── test_sponsored_theatre_e2e.py      # Sprint 2: end-to-end integration test
```

### 8.2 Sprint 1 Test Cases (20+ tests)

**`test_sponsored_theatre.py`**:
1. Valid creation produces CREATED state and SponsorReviewPackage
2. Invalid source IDs (non-existent) rejected with validation error
3. Wrong jurisdiction source rejected
4. Provisional sources (WM endpoints with shared upstream_id) accepted with PROVISIONAL flag
5. Commitment freeze transitions to COMMITTED
6. Parameter mutation after commit raises `ParameterMutationAfterCommit`
7. Review package contains commitment_hash, worst_case_loss, source_manifest
8. Worst-case loss correctly computed as `b * ln(n)`
9. Source manifest entries validated against registry
10. Duplicate outcome_labels rejected

**`test_market_theatre_bridge.py`**:
11. Market creation from Theatre config produces correct MarketState
12. Phase transition CREATED -> COMMITTED works
13. Phase transition COMMITTED -> TRADING works
14. Invalid phase transition raises `InvalidPhaseTransition`
15. State serialisation roundtrip preserves all fields
16. Parameter mutation after commit rejected

**`test_stub_agents.py`**:
17. Spawn produces 6 agents with correct archetypes
18. Shark strategy buys leading outcome when price < 0.7
19. Spy strategy trades only when evidence provided
20. Diplomat strategy buys trailing outcome when spread > 0.4
21. Saboteur produces low-volume contrary trades
22. Whale places single large position early
23. Degen trades every tick
24. Agent balance tracking works through multiple trades
25. Agent P&L accumulates correctly

### 8.3 Sprint 2 Test Cases (20+ tests)

**`test_theatre_resolution.py`**:
1. Resolution with clear winning outcome (composite_score > 0.7) selects outcome 0
2. Resolution with mid-range score (0.3-0.7) selects outcome 1
3. Resolution with low score (< 0.3) selects outcome 2
4. Oracle evaluation includes provisional corroboration (0.7 penalty)
5. Composite score computation with counter-signal scaffolding

**`test_certificate_pipeline.py`**:
6. Certificate conforms to v1.0.0 schema
7. `evidence_bundle_hash` matches manifest pattern recomputation
8. Certificate passes all 21 `echelon_verify` checks
9. `oracle_output_id` format is `"{theatre_id}_{epoch_ms}"`
10. Counter-signal results report 11 UNAVAILABLE entries

**`test_rlmf_export.py`**:
11. RLMF export conforms to schema v2.0.1
12. Probability distributions captured per epoch
13. Agent traces complete (one per agent)
14. Brier score computed correctly
15. Per-agent P&L matches settlement report

**`test_sponsored_theatre_e2e.py`** (marquee test):
16. Create Companies House Theatre ("Will Acme Ltd file annual accounts by 30 Sep 2026?")
17. Commit parameters, verify commitment hash
18. Spawn 6 stub agents, run 10 trading ticks
19. Inject mock evidence bundles (WM fixtures)
20. Trigger resolution at simulated resolution_date
21. Settle market, verify bounded-loss invariant: `total_payout <= total_trade_cashflow + b*ln(n)`
22. Generate certificate, verify 21 echelon_verify checks pass
23. Generate RLMF export, validate schema v2.0.1
24. Assemble delivery package, verify 4 deliverables present
25. Query echelon_status, verify VALID certificate state

### 8.4 Mock Strategy

| Layer | Mock Approach |
|-------|--------------|
| OSINT evidence | JSON fixtures from `backend/osint/tests/fixtures/`. `LiveOSINTRealityProvider` instantiated with mock `CollectionRunner` returning fixture data. |
| On-chain anchoring | `MockSepoliaClient` (existing). Returns deterministic `"0xmock_commit_{theatre_id}"` hashes. |
| Agent strategies | Deterministic pure functions. Fixed random seeds for Saboteur and Degen via `VRFProvider` local mode. |
| Time | Resolution date simulated by direct injection (not wall-clock waiting). |
| HTTP | No real HTTP calls. All WM endpoints mocked. Tests marked `@pytest.mark.live_wm` for future. |

### 8.5 Regression Scope

```bash
python3 -m pytest backend/market/ backend/engines/ backend/scoring/ backend/osint/ -v
```

Pre-existing `theatre/` collection errors (29 import failures from Cycle-031-033) are excluded from 012's regression baseline. Everything in the four scoped directories must pass.

### 8.6 Bounded-Loss Invariant Verification

The E2E test must verify the LMSR bounded-loss invariant:

```
market_maker_pnl >= -b * ln(n)
```

Equivalently:

```
total_payout <= total_trade_cashflow + b * ln(n)
```

This is verified using `SettlementReport.market_maker_pnl` and `LMSREngine.worst_case_loss(b, n_outcomes)`.

---

## 9. Security

### 9.1 Commitment Integrity

- Commitment hash computed via SHA-256 over canonical JSON (RFC 8785)
- Hash covers: LMSR parameters, oracle config (sources, resolution date, corroboration minimum), Theatre metadata
- Immutable after COMMITTED phase. Any parameter mutation raises `ParameterMutationAfterCommit`
- Verified after freeze via `MarketCommitment.verify_hash()`
- On-chain anchor is stubbed in 012 but the interface exists

### 9.2 Evidence Provenance

- Every evidence bundle carries an HTTP transcript receipt (from 011's collection pipeline)
- Evidence bundle hash uses manifest pattern: `{bundle_id: raw_payload_hash}` sorted by bundle_id, SHA-256 of canonical JSON
- Hash is recomputable — certificate verification recomputes and compares
- Evidence chain: sponsor question -> committed sources -> collection receipts -> corroboration result -> composite score -> certificate

### 9.3 Certificate Verification

- 21 `echelon_verify` checks cover structural integrity, hash recomputability, field presence, and canonical JSON roundtrip
- Certificate carries `verification_tier: "UNVERIFIED"` (honest -- no backtesting data)
- Settlement hash links to on-chain record (stubbed in 012)

### 9.4 No Secrets

- No private keys in codebase
- `MockSepoliaClient` uses deterministic mock values
- No real HTTP calls in tests
- `sponsor_metadata` is freeform but not persisted to chain
- `VRFProvider` uses fixed seed (`"0xECHELON_VRF_010b"`) for local mode determinism

### 9.5 Agent Isolation

- Each Theatre has its own LMSR market, agent population, evidence store, and resolution result
- No cross-Theatre state sharing
- Stub agent strategies are pure functions -- no access to other agents' state
- Agent balances tracked via `PositionManager.set_balance()` / `get_balance()`

---

## 10. File Manifest

### 10.1 Sprint 1 — Theatre Creation + Sponsor Onboarding + LMSR Wiring

| File | Type | Description |
|------|------|-------------|
| `backend/schemas/sponsored_theatre.py` | NEW | SponsoredTheatreConfig, SponsorReviewPackage (Pydantic v2) |
| `backend/services/sponsored_theatre.py` | NEW | Theatre creation service, sponsor onboarding workflow |
| `backend/services/market_theatre_bridge.py` | NEW | LMSR <-> Theatre integration layer |
| `backend/services/stub_agents.py` | NEW | StubAgent, StubAgentSpawner, 6 archetype strategies |
| `backend/api/sponsored_theatre_routes.py` | NEW | FastAPI router: POST create, GET review, POST commit |
| `backend/osint/source_manifest.py` | NEW | SourceManifestEntry, SourceManifest, SourceManifestBuilder |
| `backend/services/tests/test_sponsored_theatre.py` | NEW | Theatre creation tests (10+ tests) |
| `backend/services/tests/test_market_theatre_bridge.py` | NEW | LMSR bridge tests (6+ tests) |
| `backend/services/tests/test_stub_agents.py` | NEW | Stub agent tests (9+ tests) |

### 10.2 Sprint 2 — Resolution + Settlement + Certificate Delivery

| File | Type | Description |
|------|------|-------------|
| `backend/services/theatre_evidence.py` | NEW | TheatreEvidenceCollector, EvidenceSnapshot |
| `backend/services/theatre_resolution.py` | NEW | TheatreResolutionEngine, TheatreResolutionResult |
| `backend/services/certificate_pipeline.py` | NEW | CertificatePipeline, CalibrationCertificate (v1.0.0) |
| `backend/services/rlmf_export.py` | NEW | RLMFExportGenerator, RLMFExport (v2.0.1), CalibrationMetrics |
| `backend/services/sponsor_delivery.py` | NEW | SponsorDeliveryAssembler, SponsorDeliveryPackage |
| `backend/services/theatre_status.py` | NEW | TheatreStatusSnapshot, echelon_status integration wrapper |
| `backend/engines/paradox.py` | MODIFIED | MEDIUM-1 fix: p_reality=None guard in scan() path |
| `backend/services/tests/test_theatre_resolution.py` | NEW | Resolution engine tests (5+ tests) |
| `backend/services/tests/test_certificate_pipeline.py` | NEW | Certificate pipeline tests (5+ tests) |
| `backend/services/tests/test_rlmf_export.py` | NEW | RLMF export tests (5+ tests) |
| `backend/services/tests/test_sponsored_theatre_e2e.py` | NEW | End-to-end integration test (10+ assertions) |

### 10.3 Modification Summary

| Module Path | Sprint | Change |
|-------------|--------|--------|
| `backend/market/` | - | ZERO modifications |
| `backend/engines/paradox.py` | Sprint 2 | MEDIUM-1: `if signal.p_reality is None: return None` guard in `scan()` |
| `backend/engines/` (other) | - | ZERO modifications |
| `backend/osint/` (pipeline) | - | ZERO modifications |
| `backend/chain/` | - | ZERO modifications |

---

## 11. Technical Risks

### 11.1 Integration Complexity

**Risk**: The service layer must correctly wire together 4 subsystems (market, engines, osint, chain) that were built in isolation across 4 prior cycles.

**Mitigation**: Bridge pattern isolates each subsystem behind a clean interface. The E2E test is the acceptance gate -- it exercises the full integration path. Each bridge method delegates to existing tested functions.

### 11.2 Certificate Schema Compliance

**Risk**: The v1.0.0 certificate schema and 21 verifier checks are defined in Cycle-008/009 and may have evolved.

**Mitigation**: The certificate pipeline generates the certificate, then immediately runs it through `echelon_verify`. If any check fails, the generation code is wrong -- not the verifier. The 21 checks are enumerated in this SDD (Section 4.9) and tested explicitly.

### 11.3 RLMF Schema Drift

**Risk**: RLMF schema v2.0.1 may not match the actual data shapes produced by stub agents.

**Mitigation**: RLMF export tests validate schema conformance at the field level. The schema is defined in this SDD (Section 4.10) and the export generator enforces it.

### 11.4 Commitment Hash Compatibility

**Risk**: The existing `MarketCommitment.compute_hash()` uses `ORACLE_CONFIG_STUB` which will differ from the Theatre-level commitment hash.

**Mitigation**: Two hashes are stored: the LMSR-level hash (from `MarketCommitment.compute_hash(market)`) and the Theatre-level hash (which includes oracle config and theatre metadata). Both are independently verifiable. The LMSR-level hash is stored in `MarketState.commitment_hash` as before. The Theatre-level hash is stored separately in the Theatre record.

### 11.5 p_reality=None Crash Path (MEDIUM-1)

**Risk**: `LiveOSINTRealityProvider` returns `p_reality=None` when evidence is stale. `LogicGapCalculator.compute()` then calls `abs(p_market - None)` which raises `TypeError`.

**Mitigation**: Guard in `ParadoxEngine.scan()`:
```python
signal = self._reality_provider.get_signal(theatre_id)
if signal.p_reality is None:
    return None
```

This is the minimal fix. `LogicGapCalculator.compute()` is not modified. The guard short-circuits before the None value reaches the calculator.

### 11.6 Provisional Corroboration Impact

**Risk**: All WM endpoints share `independence_upstream_id: worldmonitor`. Corroboration minimum is never met. This affects composite_score via the 0.7 penalty factor.

**Mitigation**: This is intentional and documented. The certificate honestly reports `corroboration_status.minimum_met: false` and `penalty_factor: 0.7`. The UNVERIFIED tier reflects this limitation. Future cycles (013+) add non-WM sources for genuine corroboration.

### 11.7 Stub Agent Determinism

**Risk**: Non-deterministic strategies (Saboteur, Degen) may produce flaky tests.

**Mitigation**: Saboteur and Degen use `VRFProvider` in local mode with fixed seed for random number generation. Given identical market state and evidence inputs, strategies produce identical outputs. The E2E test uses fixed mock evidence injections at predetermined ticks.

---

## 12. MEDIUM-1 Fix Detail

**Module**: `backend/engines/paradox.py`
**Method**: `ParadoxEngine.scan()`
**Line**: After `signal = self._reality_provider.get_signal(theatre_id)` (currently line 100)

**Current code** (vulnerable):
```python
signal = self._reality_provider.get_signal(theatre_id)
reading = self._logic_gap_calc.compute(theatre_id, signal.p_reality)
```

**Fixed code**:
```python
signal = self._reality_provider.get_signal(theatre_id)
if signal.p_reality is None:
    return None
reading = self._logic_gap_calc.compute(theatre_id, signal.p_reality)
```

**Why this location**: The guard is placed in `ParadoxEngine.scan()` rather than in `LogicGapCalculator.compute()` because:
1. `scan()` is the entry point that receives the signal
2. A None p_reality means "no usable reality signal" -- the correct action is to skip the scan entirely
3. `LogicGapCalculator.compute()` has a valid type contract (`p_reality: float`) -- it should not need to handle None
4. This is the minimal change with the smallest blast radius

---

## 13. Companies House Theatre — Reference Fixture

The E2E test uses this specific Theatre configuration:

```python
SponsoredTheatreConfig(
    question="Will Acme Ltd file annual accounts by 30 Sep 2026?",
    resolution_date=datetime(2026, 9, 30, 23, 59, 59, tzinfo=timezone.utc),
    committed_sources=[
        "wm_cii_endpoint",
        "wm_market_snapshot",
        "wm_maritime_anomaly",
    ],
    outcome_labels=["Filed on time", "Filed late", "Not filed"],
    liquidity_b=Decimal("100"),
    fee_schedule=FeeSchedule(trade_fee_bps=50, resolution_fee_bps=100),
    sponsor_id="sponsor_acme_001",
    sponsor_metadata={
        "company_name": "Acme Ltd",
        "company_number": "12345678",
        "jurisdiction": "GB",
    },
)
```

**Market parameters**:
- `n_outcomes`: 3
- `b`: 100.0
- Worst-case loss: `100 * ln(3)` = 109.86
- Initial prices: [0.333, 0.333, 0.333] (uniform)
- Agents: 6 (one per archetype), 1000.0 initial balance each
- Trading ticks: 10
- Evidence injections: mock WM fixtures at ticks 3, 6, 9

---

## 14. Dependency Chain

```
Cycle-004 (pipeline hardening)
  → Cycles 005-006 (registry expansion + live OSINT surfaces)
    → Cycle-007 (unified Two-Rail pipeline, 447+ tests)
      → Cycle-008 (MCP verifier + construct calibration)
        → Cycle-009 (MCP surface, HTTP transport, certificate store)
          → Cycle-010a (LMSR cost function, market lifecycle, trade execution)
            → Cycle-010b (Butterfly, Paradox, Entropy engines, heartbeat, VRF)
              → Cycle-011 (WorldMonitor Integration — live evidence + convergence)
                → Cycle-012 (Sponsored Theatre E2E)  ← THIS CYCLE
                  → Cycle-013 (Agent Runtime — T0/T1/T2/T3 + ADK)
```
