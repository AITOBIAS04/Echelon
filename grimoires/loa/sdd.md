# SDD: Agent Runtime -- Four-Tier Hierarchical Intelligence

**Cycle**: 013
**Version**: 1.0
**Date**: 2026-03-03
**PRD**: `grimoires/loa/prd.md` v1.0
**Predecessor**: Cycle-012 SDD (archived)

---

## 1. Executive Summary

Cycle-013 replaces the deterministic stub agents from Cycle-012 with a four-tier hierarchical intelligence system. Six autonomous agent archetypes trade in an LMSR market, producing decision traces rich enough to train future agents via RLMF export.

**Key architectural decisions**:
1. **New agent modules, not engine modifications** -- all new code lives in `backend/agents/` and one new file `backend/services/agent_theatre_bridge.py`. Zero modifications to `backend/market/`, `backend/engines/`, `backend/osint/`, or `backend/services/` (012 code).
2. **Pydantic v2 for genome and trace schemas, stdlib dataclass for internal state** -- `AgentGenome` and `DecisionTrace` use Pydantic v2 for validation, serialisation, and RLMF compatibility. Internal ephemeral state (`T0Context`, `T1Decision`, `T3Decision`) uses stdlib `@dataclass` with `frozen=True` where appropriate.
3. **AgentGenome is new, coexists with existing schemas.py** -- the existing `schemas.py` has `FinancialAgent` with breeding mechanics and a different archetype enum. `AgentGenome` is a parallel Pydantic v2 model in `genome.py` purpose-built for the T0/T1/T2/T3 pipeline. No modification to `schemas.py`.
4. **Agent instance is new, complements existing instance_manager.py** -- the existing `InstanceManager` manages ACP-oriented job routing with `GenesisIdentity` objects. The new `AgentInstance` in `agent_instance.py` is Theatre-scoped with `spawn/tick/settle` semantics. No modification to `instance_manager.py`.
5. **T1 Rules Engine replaces nothing, extends everything** -- the existing `brain.py` has `RuleBasedBrain` and `AgentBrain` for market-oriented decisions. The new `rules_engine.py` implements the full archetype behaviour matrix with parameterised decisions driven by genome parameters. The existing `brain.py` is untouched.
6. **Provider interface as abstract base class** -- `BaseModelProvider` defines `generate()`, `health_check()`, and `is_available()`. Three implementations (Ollama, Mistral, Anthropic) with graceful fallback. All providers mocked in default tests.
7. **ADK as thin adapter, tested last** -- the T0/T1/T2/T3 pipeline is ADK-independent. Sprint 1-2 tests use `FakeADKRunner`. Sprint 3 introduces `google.adk` imports behind `@pytest.mark.requires_adk`. If ADK proves inadequate, only the wrapper changes.
8. **DecisionTrace feeds existing RLMF pipeline** -- `DecisionTrace` (Pydantic v2) serialises to dicts compatible with `AgentTrace.decision_traces` in `backend/services/rlmf_export.py`. No RLMF code modified.
9. **Bridge pattern preserves 012 compatibility** -- `AgentTheatreBridge` wraps `StubAgentSpawner.execute_tick()` semantics with autonomous agent `tick()` calls. The same `MarketTheatreBridge`, `TradingEngine`, and `PositionManager` are reused.

---

## 2. System Architecture

### 2.1 Component Topology

```
                                                          Model Providers
                                                    ┌─────────────────────────┐
                                                    │  ┌───────────────────┐  │
                                                    │  │ Ollama (T1)       │  │
                                                    │  │ Qwen 3.5 4B/9B   │  │
                                                    │  │ localhost:11434   │  │
                                                    │  └───────────────────┘  │
                                                    │  ┌───────────────────┐  │
                                                    │  │ Mistral (T2)      │  │
                                                    │  │ Creative variant  │  │
                                                    │  │ api.mistral.ai    │  │
                                                    │  └───────────────────┘  │
                                                    │  ┌───────────────────┐  │
                                                    │  │ Anthropic (T3)    │  │
                                                    │  │ Sonnet/Opus       │  │
                                                    │  │ api.anthropic.com │  │
                                                    │  └───────────────────┘  │
                                                    └────────────┬────────────┘
                                                                 │
┌────────────────────────────────────────────────────────────────┼──────────────────┐
│                    AGENT RUNTIME (NEW in 013)                  │                  │
│                                                                │                  │
│  ┌──────────────┐  ┌──────────────────┐  ┌────────────────────┼───────────────┐  │
│  │ AgentGenome  │  │ Context Compiler │  │     Decision Router │               │  │
│  │ (genome.py)  │  │ (context_       │  │   (decision_router.py)              │  │
│  │              │  │  compiler.py)    │  │                     │               │  │
│  │ Pydantic v2  │  │                  │  │  T0 ──→ T1 ──→ T2? │               │  │
│  │ 8 params     ├──┤ AgentGenome +    │  │         │           │               │  │
│  │ per archetype│  │ TheatreConfig +  │  │         └── T3? ◄───┘               │  │
│  │              │  │ MarketState      │  │                                     │  │
│  └──────────────┘  │      │           │  └─────────────────────────────────────┘  │
│                    │      ▼           │                                            │
│                    │ T0Context        │  ┌─────────────────────────────────────┐  │
│                    │ (frozen          │  │          Tier Engines               │  │
│                    │  dataclass)      │  │                                     │  │
│                    │ SHA-256 hash     │  │  ┌───────────────┐ ┌────────────┐  │  │
│                    └──────────────────┘  │  │ T1 Rules      │ │ T2 Person- │  │  │
│                                         │  │ Engine        │ │ ality      │  │  │
│  ┌──────────────┐                       │  │ (rules_       │ │ Engine     │  │  │
│  │ Agent        │                       │  │  engine.py)   │ │ (personal- │  │  │
│  │ Instance     │                       │  │               │ │  ity_      │  │  │
│  │ (agent_      │                       │  │ Per-archetype │ │  engine.py)│  │  │
│  │  instance.py)│                       │  │ parameterised │ │            │  │  │
│  │              │                       │  │ decision logic│ │ Expression │  │  │
│  │ spawn()      │                       │  └───────────────┘ │ only       │  │  │
│  │ tick()       │                       │  ┌───────────────┐ └────────────┘  │  │
│  │ settle()     │                       │  │ T3 Deep       │                 │  │
│  │              │                       │  │ Reasoning     │                 │  │
│  └──────┬───────┘                       │  │ (deep_        │                 │  │
│         │                               │  │  reasoning.py)│                 │  │
│         │                               │  │               │                 │  │
│         │                               │  │ Rate-limited  │                 │  │
│         │                               │  │ Cost-bounded  │                 │  │
│         │                               │  └───────────────┘                 │  │
│         │                               └─────────────────────────────────────┘  │
│         │                                                                        │
│  ┌──────┴──────────────────────┐  ┌───────────────────────────────────────────┐  │
│  │ DecisionTrace               │  │ ADK Layer (Sprint 3 only)                │  │
│  │ (decision_trace.py)         │  │                                           │  │
│  │                             │  │  ┌──────────────┐  ┌───────────────────┐  │  │
│  │ Pydantic v2                 │  │  │ EchelonAgent │  │ SharkV1           │  │  │
│  │ BEAUVOIR-compliant          │  │  │ (adk/        │  │ (adk/shark_v1.py) │  │  │
│  │ RLMF-compatible             │  │  │  echelon_    │  │                   │  │  │
│  │                             │  │  │  agent.py)   │  │ MEGALODON variant │  │  │
│  └─────────────────────────────┘  │  └──────────────┘  └───────────────────┘  │  │
│                                   │                                           │  │
│                                   │  FakeADKRunner (Sprint 1-2 testing)       │  │
│                                   └───────────────────────────────────────────┘  │
│                                                                                  │
└──────────────────────────────────┬───────────────────────────────────────────────┘
                                   │
                                   ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                    BRIDGE LAYER                                                  │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────────┐ │
│  │ AgentTheatreBridge (backend/services/agent_theatre_bridge.py)               │ │
│  │                                                                             │ │
│  │ • spawn_agents(theatre_id, genome_configs) -> list[AgentInstance]           │ │
│  │ • execute_tick(agents, market, trading_engine, pos_mgr, evidence, tick)     │ │
│  │ • settle_agents(agents, settlement_report) -> list[AgentSettlementResult]  │ │
│  │ • collect_decision_traces() -> list[DecisionTrace]                         │ │
│  └─────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                  │
└──────────────────────────────────┬───────────────────────────────────────────────┘
                                   │
          ┌────────────────────────┼────────────────────────┐
          │                        │                        │
          ▼                        ▼                        ▼
┌─────────────────┐  ┌───────────────────┐  ┌─────────────────────┐
│ backend/market/  │  │ backend/engines/  │  │ backend/services/   │
│ (010a -- frozen) │  │ (010b -- frozen)  │  │ (012 -- frozen)     │
│                  │  │                   │  │                     │
│ LMSREngine       │  │ HeartbeatScheduler│  │ SponsoredTheatre    │
│ TradingEngine    │  │ ButterflyEngine   │  │ MarketTheatreBridge │
│ PositionManager  │  │ ParadoxEngine     │  │ StubAgentSpawner    │
│ ResolutionEngine │  │ EntropyEngine     │  │ TheatreResolution   │
│ MarketLifecycle  │  │                   │  │ CertificatePipeline │
│ MarketCommitment │  │                   │  │ RLMFExportGenerator │
└─────────────────┘  └───────────────────┘  └─────────────────────┘
```

### 2.2 Data Flow -- Agent Decision Tick

```
1. TICK ENTRY
   HeartbeatScheduler fires "agent" cadence (5s)
     │
     └─→ AgentTheatreBridge.execute_tick(agents, market, engine, pos_mgr, evidence, tick)

2. PER-AGENT DECISION
   For each AgentInstance:
     │
     ├─→ T0: ContextCompiler.compile(genome, market_state, position_state, theatre_config)
     │        └─→ T0Context (frozen dataclass, SHA-256 hash)
     │
     ├─→ T1: RulesEngine.decide(t0_context)
     │        └─→ T1Decision (action, confidence, reasoning_trace, pattern_name)
     │
     ├─→ Router: DecisionRouter.route(t0_context, t1_decision)
     │        │
     │        ├─→ confidence >= novelty_threshold?
     │        │     YES: use T1Decision
     │        │     └─→ optionally run T2 for expression
     │        │
     │        └─→ confidence < novelty_threshold?
     │              YES: escalate to T3
     │              ├─→ T3 available and under rate limit?
     │              │     YES: DeepReasoning.reason(full_context) → T3Decision
     │              │     NO:  fall back to T1Decision with low_confidence flag
     │              └─→ T3Decision or T1Decision (fallback)
     │
     ├─→ DecisionTrace: record tick_id, agent_id, tier_used, action, confidence,
     │                   pattern_name, options_considered, reasoning_summary,
     │                   evidence_refs, t0_context_hash
     │
     └─→ TradeIntent: if action != HOLD:
              │
              ├─→ validate against position limits (T0 constraints)
              └─→ TradingEngine.execute_trade(market, agent_id, outcome_index, shares)
                   └─→ PositionManager.update_position(trade)

3. TICK OUTPUT
   └─→ list[DecisionTrace] accumulated for RLMF export
```

### 2.3 Tier Cost Profile

```
     T0                    T1                    T2                  T3
  ┌─────────┐        ┌──────────┐         ┌──────────┐       ┌──────────┐
  │ Context │        │ Fast     │         │ Personal-│       │ Deep     │
  │ Compile │        │ Reasoning│         │ ity      │       │ Reasoning│
  │         │        │          │         │          │       │          │
  │ Cost: 0 │        │ Cost: ~0 │         │ Cost: $  │       │ Cost: $$$│
  │ Time: 0 │        │ Time:<1ms│         │ Time:200-│       │ Time:1-5s│
  │         │        │ (rules)  │         │  500ms   │       │          │
  │ Always  │        │ <100ms   │         │ Optional │       │ Rare     │
  │ runs    │        │ (LLM)    │         │ express- │       │ escalated│
  │         │        │ Always   │         │ ion only │       │ decisions│
  │         │        │ runs     │         │          │       │          │
  └─────────┘        └──────────┘         └──────────┘       └──────────┘
    100%               100%                 ~10%                ~2-5%
```

---

## 3. Technology Stack

| Layer | Technology | Notes |
|-------|-----------|-------|
| Language | Python 3.9.6+ | `from __future__ import annotations` in every new file |
| Schemas (agent-facing) | Pydantic v2 | `AgentGenome`, `DecisionTrace` |
| Schemas (internal state) | stdlib `@dataclass` | `T0Context`, `T1Decision`, `T3Decision`, `T2Output` |
| T1 Local LLM | Ollama + Qwen 3.5 4B/9B | HTTP API, localhost:11434 |
| T2 Personality | Mistral API | Creative variant |
| T3 Deep Reasoning | Anthropic API | Sonnet 4.5 / Opus |
| Agent Framework | Google ADK (Python) | Sprint 3 only, thin wrapper |
| HTTP Client | `httpx` | Async for provider calls |
| Test Framework | pytest | `@pytest.mark.requires_ollama`, etc. |
| Market Engine | LMSR (010a, frozen) | `TradingEngine.execute_trade()` |
| Heartbeat | HeartbeatScheduler (010b, frozen) | Agent cadence: 5s |
| Evidence | OSINT pipeline (011, frozen) | Mock fixtures in tests |
| Theatre | Services layer (012, frozen) | `MarketTheatreBridge` reused |

---

## 4. Component Design

### 4.1 AgentGenome (`backend/agents/genome.py`)

**Purpose**: Pydantic v2 model capturing the complete T0 context specification for an agent archetype. Defines the 8 behavioural parameters, variant overrides, Theatre context, position constraints, and decision routing config.

**Relationship to existing code**: The existing `schemas.py` has `FinancialArchetype` (WHALE, SHARK, DEGEN, VALUE, MOMENTUM, NOISE) and `FinancialAgent` with breeding mechanics. `AgentGenome` is a new model with the Echelon-specific archetype enum (SHARK, SPY, DIPLOMAT, SABOTEUR, WHALE, DEGEN) and the 8-parameter behaviour matrix. No modification to `schemas.py`. The existing `agent_skills_bridge.py` has a `@dataclass AgentGenome` with different fields (aggression, patience, loyalty, etc.) -- this is for the Skills System and is not modified. The new genome module uses a distinct class name `EchelonGenome` internally but is importable as `AgentGenome` for PRD alignment.

```python
# backend/agents/genome.py
from __future__ import annotations

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class EchelonArchetype(str, Enum):
    """Six core agent archetypes from System Bible v13 Section VIII."""
    SHARK = "SHARK"
    SPY = "SPY"
    DIPLOMAT = "DIPLOMAT"
    SABOTEUR = "SABOTEUR"
    WHALE = "WHALE"
    DEGEN = "DEGEN"


class AgentGenome(BaseModel):
    """Complete T0 context specification for an Echelon agent.

    Pydantic v2 model. Frozen after construction for auditability.
    """
    model_config = {"frozen": True}

    # --- Identity ---
    archetype: EchelonArchetype
    variant: Optional[str] = None  # e.g., "MEGALODON"
    genome_version: str = "1.0.0"

    # --- 8 Archetype Parameters ---
    risk_appetite: float = Field(ge=0.0, le=1.0, description="rho")
    evidence_sensitivity: float = Field(ge=0.0, le=1.0, description="epsilon")
    time_preference: float = Field(ge=0.0, le=1.0, description="gamma")
    exploration_rate: float = Field(ge=0.0, le=1.0, description="xi")
    position_limit: float = Field(gt=0, description="L -- max position in shares")
    sabotage_propensity: float = Field(ge=0.0, le=1.0, description="sigma")
    shield_propensity: float = Field(ge=0.0, le=1.0, description="phi")
    patience: int = Field(ge=1, description="pi -- ticks between evaluations")

    # --- Variant Overrides ---
    variant_overrides: dict[str, float] = Field(default_factory=dict)

    # --- Theatre Context (injected at spawn) ---
    committed_sources: list[str] = Field(default_factory=list)
    outcome_labels: list[str] = Field(default_factory=list)
    resolution_date: Optional[str] = None
    liquidity_b: Optional[float] = None

    # --- Position Constraints ---
    max_position_pct: float = Field(default=0.10, ge=0.0, le=1.0)
    max_drawdown_pct: float = Field(default=0.20, ge=0.0, le=1.0)
    stop_loss_threshold: float = Field(default=0.15, ge=0.0, le=1.0)

    # --- Decision Routing ---
    novelty_threshold: float = Field(
        default=0.6, ge=0.0, le=1.0,
        description="Confidence below this triggers T3 escalation"
    )


def create_genome(
    archetype: EchelonArchetype,
    variant: Optional[str] = None,
    **overrides: float,
) -> AgentGenome:
    """Factory: create a genome from the Behaviour Matrix with optional overrides."""
    defaults = ARCHETYPE_DEFAULTS[archetype]
    params = {**defaults}
    if variant and variant in VARIANT_OVERRIDES:
        params.update(VARIANT_OVERRIDES[variant])
    params.update(overrides)
    return AgentGenome(
        archetype=archetype,
        variant=variant,
        **params,
    )


ARCHETYPE_DEFAULTS: dict[EchelonArchetype, dict] = {
    EchelonArchetype.SHARK: {
        "risk_appetite": 0.85, "evidence_sensitivity": 0.70,
        "time_preference": 0.95, "exploration_rate": 0.15,
        "position_limit": 10_000, "sabotage_propensity": 0.30,
        "shield_propensity": 0.10, "patience": 30,
    },
    EchelonArchetype.SPY: {
        "risk_appetite": 0.40, "evidence_sensitivity": 0.90,
        "time_preference": 0.98, "exploration_rate": 0.40,
        "position_limit": 2_500, "sabotage_propensity": 0.05,
        "shield_propensity": 0.15, "patience": 120,
    },
    EchelonArchetype.DIPLOMAT: {
        "risk_appetite": 0.30, "evidence_sensitivity": 0.50,
        "time_preference": 0.99, "exploration_rate": 0.20,
        "position_limit": 5_000, "sabotage_propensity": 0.02,
        "shield_propensity": 0.85, "patience": 60,
    },
    EchelonArchetype.SABOTEUR: {
        "risk_appetite": 0.95, "evidence_sensitivity": 0.30,
        "time_preference": 0.90, "exploration_rate": 0.60,
        "position_limit": 7_500, "sabotage_propensity": 0.95,
        "shield_propensity": 0.05, "patience": 45,
    },
    EchelonArchetype.WHALE: {
        "risk_appetite": 0.70, "evidence_sensitivity": 0.55,
        "time_preference": 0.92, "exploration_rate": 0.10,
        "position_limit": 25_000, "sabotage_propensity": 0.15,
        "shield_propensity": 0.30, "patience": 90,
    },
    EchelonArchetype.DEGEN: {
        "risk_appetite": 1.00, "evidence_sensitivity": 0.15,
        "time_preference": 0.85, "exploration_rate": 0.95,
        "position_limit": 1_000, "sabotage_propensity": 0.50,
        "shield_propensity": 0.02, "patience": 10,
    },
}


VARIANT_OVERRIDES: dict[str, dict] = {
    "MEGALODON": {
        "risk_appetite": 0.90,
        "evidence_sensitivity": 0.80,
        "position_limit": 15_000,
        "novelty_threshold": 0.6,
    },
}
```

**Error handling**: Pydantic v2 validation raises `ValidationError` on construction. `frozen=True` prevents mutation after creation.

**Test approach**: `test_genome.py` (part of `test_context_compiler.py`) -- verify all 6 default genomes validate, variant overrides apply correctly, frozen enforcement, JSON round-trip.

---

### 4.2 T0 Context Compiler (`backend/agents/context_compiler.py`)

**Purpose**: Compiles `AgentGenome` + Theatre config + current `MarketState` into a frozen `T0Context` dataclass. Zero inference cost. Deterministic: same inputs always produce same output. SHA-256 hash enables reproducibility verification.

```python
# backend/agents/context_compiler.py
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from backend.agents.genome import AgentGenome
from backend.market.lmsr import LMSREngine
from backend.market.positions import AgentPosition
from backend.market.state import MarketState


@dataclass(frozen=True)
class T0Context:
    """Frozen agent world-view. Deterministic, hashable, zero inference cost."""

    # --- Archetype Parameters (from genome) ---
    archetype: str
    risk_appetite: float
    evidence_sensitivity: float
    time_preference: float
    exploration_rate: float
    position_limit: float
    sabotage_propensity: float
    shield_propensity: float
    patience: int
    novelty_threshold: float

    # --- Market Context ---
    prices: tuple[float, ...]
    phase: str
    outcome_labels: tuple[str, ...]
    n_outcomes: int
    evidence_coverage_pct: float  # 0.0-1.0

    # --- Position State ---
    current_shares: tuple[float, ...]
    net_cashflow: float
    available_balance: float

    # --- Theatre Rules ---
    committed_sources: tuple[str, ...]
    resolution_date: str
    liquidity_b: float

    # --- Constraints ---
    max_position_pct: float
    max_drawdown_pct: float
    stop_loss_threshold: float

    # --- Hash ---
    context_hash: str = ""


class ContextCompiler:
    """Compiles AgentGenome + MarketState + position into T0Context."""

    @staticmethod
    def compile(
        genome: AgentGenome,
        market: MarketState,
        position: AgentPosition,
        available_balance: float,
        evidence_coverage_pct: float = 0.0,
    ) -> T0Context:
        """Pure function: genome + market + position -> T0Context.

        Deterministic. Same inputs always produce the same T0Context.
        """
        prices = tuple(LMSREngine.prices(market.x, market.b))
        shares = tuple(position.shares) if position.shares else tuple(
            0.0 for _ in range(market.n_outcomes)
        )

        ctx = T0Context(
            archetype=genome.archetype.value,
            risk_appetite=genome.risk_appetite,
            evidence_sensitivity=genome.evidence_sensitivity,
            time_preference=genome.time_preference,
            exploration_rate=genome.exploration_rate,
            position_limit=genome.position_limit,
            sabotage_propensity=genome.sabotage_propensity,
            shield_propensity=genome.shield_propensity,
            patience=genome.patience,
            novelty_threshold=genome.novelty_threshold,
            prices=prices,
            phase=market.phase.value,
            outcome_labels=tuple(market.outcome_labels),
            n_outcomes=market.n_outcomes,
            evidence_coverage_pct=evidence_coverage_pct,
            current_shares=shares,
            net_cashflow=position.net_cashflow,
            available_balance=available_balance,
            committed_sources=tuple(genome.committed_sources),
            resolution_date=genome.resolution_date or "",
            liquidity_b=market.b,
            max_position_pct=genome.max_position_pct,
            max_drawdown_pct=genome.max_drawdown_pct,
            stop_loss_threshold=genome.stop_loss_threshold,
        )

        # Compute hash (replace empty sentinel)
        ctx_hash = ContextCompiler.compute_hash(ctx)
        # Use object.__setattr__ because frozen
        object.__setattr__(ctx, "context_hash", ctx_hash)

        return ctx

    @staticmethod
    def compute_hash(ctx: T0Context) -> str:
        """SHA-256 hash of T0Context for reproducibility verification.

        Excludes context_hash itself (circular). Excludes no fields --
        every field contributes to the hash.
        """
        hashable = {
            "archetype": ctx.archetype,
            "risk_appetite": ctx.risk_appetite,
            "evidence_sensitivity": ctx.evidence_sensitivity,
            "time_preference": ctx.time_preference,
            "exploration_rate": ctx.exploration_rate,
            "position_limit": ctx.position_limit,
            "sabotage_propensity": ctx.sabotage_propensity,
            "shield_propensity": ctx.shield_propensity,
            "patience": ctx.patience,
            "novelty_threshold": ctx.novelty_threshold,
            "prices": list(ctx.prices),
            "phase": ctx.phase,
            "outcome_labels": list(ctx.outcome_labels),
            "n_outcomes": ctx.n_outcomes,
            "evidence_coverage_pct": ctx.evidence_coverage_pct,
            "current_shares": list(ctx.current_shares),
            "net_cashflow": ctx.net_cashflow,
            "available_balance": ctx.available_balance,
            "committed_sources": list(ctx.committed_sources),
            "resolution_date": ctx.resolution_date,
            "liquidity_b": ctx.liquidity_b,
            "max_position_pct": ctx.max_position_pct,
            "max_drawdown_pct": ctx.max_drawdown_pct,
            "stop_loss_threshold": ctx.stop_loss_threshold,
        }
        canonical = json.dumps(hashable, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
```

**Error handling**: `LMSREngine.prices()` can fail if `market.x` is empty or `b == 0`. The compiler propagates these errors -- callers must ensure valid market state.

**Test approach**: `test_context_compiler.py` -- deterministic output for fixed inputs, hash stability, all genome archetypes compile correctly, position state propagation.

---

### 4.3 T1 Rules Engine (`backend/agents/rules_engine.py`)

**Purpose**: Parameterised decision engine driven by T0 context. Produces `T1Decision` with action, confidence, reasoning trace, and pattern name. Per-archetype decision logic is parameterised by genome parameters, not hard-coded.

**Relationship to existing code**: The existing `brain.py` has a `RuleBasedBrain` with simple archetype-to-action mapping. The existing `shark_strategies.py` has `TulipStrategy` and `SharkBrain`. The new `rules_engine.py` implements the full 6-archetype behaviour matrix with parameterised thresholds. No existing files modified.

```python
# backend/agents/rules_engine.py
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from backend.agents.context_compiler import T0Context


class TradeAction(str, Enum):
    """Possible agent actions."""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"
    SHIELD = "SHIELD"
    SABOTAGE = "SABOTAGE"


@dataclass(frozen=True)
class ActionOption:
    """A considered alternative for options_considered in DecisionTrace."""
    action: str
    estimated_value: float
    rejection_reason: str


@dataclass(frozen=True)
class T1Decision:
    """Output of the T1 rules engine. Immutable after creation."""
    action: TradeAction
    outcome_index: Optional[int]  # which outcome to buy/sell, None for HOLD
    shares: float
    confidence: float  # 0.0-1.0
    reasoning_trace: str
    pattern_name: str
    options_considered: tuple[ActionOption, ...] = ()
    escalate_to_t3: bool = False


class RulesEngine:
    """Parameterised T1 decision engine.

    All decision logic is driven by T0Context parameters.
    No hard-coded archetype if-chains -- thresholds are genome-derived.
    """

    def decide(self, ctx: T0Context, tick: int, rng_seed: int) -> T1Decision:
        """Produce a T1 decision from T0 context.

        Args:
            ctx: Frozen T0Context with all genome + market + position state.
            tick: Current tick number.
            rng_seed: Deterministic RNG seed for this decision.

        Returns:
            T1Decision with action, confidence, and reasoning trace.
        """
        import random
        rng = random.Random(rng_seed)

        # Dispatch to archetype-specific logic
        dispatch = {
            "SHARK": self._shark_decide,
            "SPY": self._spy_decide,
            "DIPLOMAT": self._diplomat_decide,
            "SABOTEUR": self._saboteur_decide,
            "WHALE": self._whale_decide,
            "DEGEN": self._degen_decide,
        }
        decide_fn = dispatch.get(ctx.archetype, self._hold_default)
        return decide_fn(ctx, tick, rng)

    def _shark_decide(
        self, ctx: T0Context, tick: int, rng: "random.Random"
    ) -> T1Decision:
        """Momentum exploitation: buy leading, take profit, stop-loss."""
        # ... parameterised logic using ctx.risk_appetite, ctx.time_preference
        # Returns T1Decision with pattern_name="momentum_exploitation"
        ...

    def _spy_decide(
        self, ctx: T0Context, tick: int, rng: "random.Random"
    ) -> T1Decision:
        """Intel arbitrage: trade on evidence arrival."""
        # ... parameterised logic using ctx.evidence_sensitivity
        # Returns T1Decision with pattern_name="intel_arbitrage"
        ...

    def _diplomat_decide(
        self, ctx: T0Context, tick: int, rng: "random.Random"
    ) -> T1Decision:
        """Stability maintenance: buy trailing outcome to reduce spread."""
        # ... parameterised logic using ctx.shield_propensity
        # Returns T1Decision with pattern_name="stability_maintenance"
        ...

    def _saboteur_decide(
        self, ctx: T0Context, tick: int, rng: "random.Random"
    ) -> T1Decision:
        """Chaos creation: random contrary trades."""
        # ... parameterised logic using ctx.sabotage_propensity
        # Returns T1Decision with pattern_name="chaos_creation"
        ...

    def _whale_decide(
        self, ctx: T0Context, tick: int, rng: "random.Random"
    ) -> T1Decision:
        """Conviction accumulation: large positions on strong evidence."""
        # ... parameterised logic using ctx.position_limit, ctx.evidence_sensitivity
        # Returns T1Decision with pattern_name="conviction_accumulation"
        ...

    def _degen_decide(
        self, ctx: T0Context, tick: int, rng: "random.Random"
    ) -> T1Decision:
        """Random exploration: random outcome, random volume."""
        # ... parameterised logic using ctx.exploration_rate
        # Returns T1Decision with pattern_name="random_exploration"
        ...

    def _hold_default(
        self, ctx: T0Context, tick: int, rng: "random.Random"
    ) -> T1Decision:
        """Default fallback: HOLD with low confidence."""
        return T1Decision(
            action=TradeAction.HOLD,
            outcome_index=None,
            shares=0.0,
            confidence=0.3,
            reasoning_trace="Unknown archetype, defaulting to HOLD",
            pattern_name="default_hold",
            escalate_to_t3=True,
        )
```

**Decision logic detail (Shark example)**:

```
1. Compute leading_idx = argmax(prices)
2. Compute price_delta = prices[leading_idx] - (1.0 / n_outcomes)
3. BUY check: price_delta > risk_appetite * MOMENTUM_THRESHOLD
   - shares = min(position_limit * 0.1, available_balance * risk_appetite)
   - confidence = 0.5 + price_delta * 0.5
4. TAKE PROFIT check: current_shares[leading_idx] > 0 AND
   unrealised_pnl > time_preference * PROFIT_TARGET
   - action = SELL
5. STOP LOSS check: unrealised_pnl < -stop_loss_threshold * net_cashflow
   - action = SELL (all shares in losing outcome)
6. Default: HOLD
7. If confidence < novelty_threshold: set escalate_to_t3 = True
```

Each archetype method follows this pattern: parameterised checks using genome values, options_considered populated with alternatives evaluated, confidence computed from market state proximity to thresholds.

**Error handling**: Division by zero guarded (n_outcomes >= 2 enforced by market creation). Invalid archetype defaults to HOLD with T3 escalation.

**Test approach**: `test_rules_engine.py` -- per-archetype decision correctness with known market states, confidence scoring near thresholds, escalation flagging, deterministic with fixed RNG seed.

---

### 4.4 DecisionTrace Schema (`backend/agents/decision_trace.py`)

**Purpose**: Pydantic v2 model defining the stable structured log for every agent decision. BEAUVOIR-compliant. RLMF-compatible with `backend/services/rlmf_export.py`.

```python
# backend/agents/decision_trace.py
from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal, Optional
from pydantic import BaseModel, Field


class DecisionTrace(BaseModel):
    """Stable decision log schema. Every field is a stable key.

    Conforms to BEAUVOIR agent-first citizenship requirements.
    Compatible with RLMFExport.AgentTrace.decision_traces (list[dict]).
    """
    model_config = {"frozen": True}

    # --- Identity ---
    tick_id: str
    agent_id: str
    theatre_id: str
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    # --- Tier ---
    tier_used: Literal["T1-RULES", "T1-LOCAL-LLM", "T3"]

    # --- Market Snapshot ---
    market_state_snapshot: dict  # prices, phase, evidence_coverage_pct

    # --- Evidence State ---
    evidence_state: dict  # last_evidence_ts, new_evidence_flag, source_ids_cited

    # --- Decision ---
    t0_context_hash: str
    action: str  # BUY(outcome, shares) / SELL / HOLD / SHIELD / SABOTAGE
    confidence: float = Field(ge=0.0, le=1.0)
    pattern_name: str  # Named pattern from archetype matrix
    options_considered: list[dict]  # [{action, estimated_value, rejection_reason}]
    reasoning_summary: str

    # --- Escalation ---
    escalated_to_t3: bool = False

    # --- Evidence References ---
    evidence_refs: list[str] = Field(default_factory=list)

    def to_rlmf_dict(self) -> dict:
        """Serialise to dict compatible with AgentTrace.decision_traces."""
        return self.model_dump(mode="json")
```

**RLMF integration**: The `decision_traces` field in `AgentTrace` (from `rlmf_export.py`) is `list[dict[str, Any]]`. Each `DecisionTrace.to_rlmf_dict()` produces a dict that slots directly into this list. No modification to `rlmf_export.py` required.

**Determinism note**: `timestamp` is excluded from reproducibility checks. Reproducibility is determined by `t0_context_hash` + `market_state_snapshot` + `evidence_state`.

**Test approach**: `test_decision_trace.py` -- schema validation for all required fields, JSON round-trip, RLMF dict compatibility, each archetype produces valid traces.

---

### 4.5 Agent Instance (`backend/agents/agent_instance.py`)

**Purpose**: Ephemeral agent instance bound to a Theatre. Lifecycle: `spawn` -> `tick` (repeated) -> `settle`. Multiple instances per Identity. P&L aggregation back to Identity.

**Relationship to existing code**: The existing `instance_manager.py` has `AgentInstance` (Pydantic BaseModel) for ACP job routing with `InstanceStatus`, `JobRequest`, etc. The new agent instance is a separate class `TheatreAgentInstance` in `agent_instance.py` with Theatre-scoped lifecycle. No modification to `instance_manager.py`.

```python
# backend/agents/agent_instance.py
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from backend.agents.context_compiler import ContextCompiler, T0Context
from backend.agents.decision_trace import DecisionTrace
from backend.agents.genome import AgentGenome
from backend.agents.rules_engine import RulesEngine, T1Decision, TradeAction
from backend.market.lmsr import LMSREngine
from backend.market.positions import AgentPosition, PositionManager
from backend.market.state import MarketState
from backend.market.trading import Trade, TradingEngine


@dataclass
class TradeIntent:
    """Agent's intended trade before execution."""
    outcome_index: int
    shares: float
    trigger: str
    confidence: float


@dataclass
class AgentSettlementResult:
    """Settlement result for a single agent instance."""
    agent_id: str
    archetype: str
    trades_executed: int
    final_position: list[float]
    realised_pnl: float
    unrealised_pnl: float


class TheatreAgentInstance:
    """Ephemeral agent instance bound to a Theatre.

    Lifecycle: spawn() -> tick() [repeated] -> settle()
    """

    def __init__(
        self,
        agent_id: str,
        genome: AgentGenome,
        theatre_id: str,
        rules_engine: RulesEngine,
    ) -> None:
        self.agent_id = agent_id
        self.genome = genome
        self.theatre_id = theatre_id
        self._rules_engine = rules_engine
        self._decision_traces: list[DecisionTrace] = []
        self._trade_count: int = 0
        self._settled: bool = False

    @classmethod
    def spawn(
        cls,
        genome: AgentGenome,
        theatre_id: str,
        rules_engine: Optional[RulesEngine] = None,
    ) -> TheatreAgentInstance:
        """Factory: create an agent instance for a Theatre."""
        agent_id = f"{theatre_id}_{genome.archetype.value.lower()}"
        if genome.variant:
            agent_id = f"{agent_id}_{genome.variant.lower()}"
        return cls(
            agent_id=agent_id,
            genome=genome,
            theatre_id=theatre_id,
            rules_engine=rules_engine or RulesEngine(),
        )

    def tick(
        self,
        market: MarketState,
        position_manager: PositionManager,
        trading_engine: TradingEngine,
        evidence: object,
        tick: int,
        seed: int = 42,
    ) -> tuple[Optional[Trade], DecisionTrace]:
        """Execute one decision tick.

        Returns:
            (executed_trade_or_None, decision_trace)
        """
        # 1. Get current position and balance
        position = position_manager.get_position(self.agent_id)
        balance = position_manager.get_balance(self.agent_id)

        # 2. Compute evidence coverage
        evidence_coverage = 0.0 if evidence is None else 0.5

        # 3. T0: compile context
        t0_ctx = ContextCompiler.compile(
            genome=self.genome,
            market=market,
            position=position,
            available_balance=balance,
            evidence_coverage_pct=evidence_coverage,
        )

        # 4. T1: rules engine decision
        rng_seed = seed + tick + hash(self.agent_id) % 10000
        t1_decision = self._rules_engine.decide(t0_ctx, tick, rng_seed)

        # 5. Build trade intent and execute
        executed_trade: Optional[Trade] = None
        action_str = t1_decision.action.value

        if t1_decision.action in (TradeAction.BUY, TradeAction.SELL):
            if t1_decision.outcome_index is not None and t1_decision.shares > 0:
                shares = t1_decision.shares
                if t1_decision.action == TradeAction.SELL:
                    shares = -shares
                try:
                    executed_trade = trading_engine.execute_trade(
                        market=market,
                        agent_id=self.agent_id,
                        outcome_index=t1_decision.outcome_index,
                        shares=shares,
                    )
                    self._trade_count += 1
                    action_str = (
                        f"{t1_decision.action.value}"
                        f"(outcome={t1_decision.outcome_index},"
                        f" shares={abs(shares):.1f})"
                    )
                except Exception:
                    # Trade failed -- record attempt, continue
                    pass

        # 6. Build decision trace
        trace = DecisionTrace(
            tick_id=f"tick_{tick:04d}",
            agent_id=self.agent_id,
            theatre_id=self.theatre_id,
            tier_used="T1-RULES",
            market_state_snapshot={
                "prices": list(t0_ctx.prices),
                "phase": t0_ctx.phase,
                "evidence_coverage_pct": t0_ctx.evidence_coverage_pct,
            },
            evidence_state={
                "new_evidence_flag": evidence is not None,
                "source_ids_cited": [],
            },
            t0_context_hash=t0_ctx.context_hash,
            action=action_str,
            confidence=t1_decision.confidence,
            pattern_name=t1_decision.pattern_name,
            options_considered=[
                {
                    "action": opt.action,
                    "estimated_value": opt.estimated_value,
                    "rejection_reason": opt.rejection_reason,
                }
                for opt in t1_decision.options_considered
            ],
            reasoning_summary=t1_decision.reasoning_trace,
            escalated_to_t3=t1_decision.escalate_to_t3,
            evidence_refs=[],
        )

        self._decision_traces.append(trace)
        return executed_trade, trace

    def settle(
        self, position_manager: PositionManager, resolved_outcome: int
    ) -> AgentSettlementResult:
        """Finalise this instance. Compute settlement P&L."""
        self._settled = True
        position = position_manager.get_position(self.agent_id)
        payout = position_manager.compute_settlement_payout(
            position, resolved_outcome
        )

        return AgentSettlementResult(
            agent_id=self.agent_id,
            archetype=self.genome.archetype.value,
            trades_executed=self._trade_count,
            final_position=list(position.shares),
            realised_pnl=payout - position.net_cashflow,
            unrealised_pnl=0.0,  # All positions settled
        )

    @property
    def decision_traces(self) -> list[DecisionTrace]:
        return list(self._decision_traces)

    @property
    def trade_count(self) -> int:
        return self._trade_count
```

**Error handling**: `TradingEngine.execute_trade()` can raise `TradingHalted`, `InsufficientBalance`, `InsufficientShares`, `InvalidMarketParameters`. All are caught silently -- the agent's decision is logged regardless. Failed trades appear in the trace with the action string but `executed_trade` is `None`.

**Test approach**: `test_agent_instance.py` -- spawn -> 10 ticks -> settle lifecycle, P&L correctness, multiple instances per identity, trade count accumulation, decision trace completeness.

---

### 4.6 T2 Personality Engine (`backend/agents/personality_engine.py`)

**Purpose**: Expression layer. Adds archetype-specific voice to T1 decisions. Never overrides T1's action -- expression only. Runs only when the decision produces externally visible output.

```python
# backend/agents/personality_engine.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from backend.agents.context_compiler import T0Context
from backend.agents.rules_engine import T1Decision


@dataclass(frozen=True)
class T2Output:
    """Personality-coloured expression of a T1 decision."""
    coloured_rationale: str
    market_commentary: str
    diplomatic_message: Optional[str] = None


PERSONALITY_PROMPTS: dict[str, str] = {
    "SHARK": (
        "You are a ruthless momentum trader. Confident, terse. "
        "Express this trade decision in 1-2 sentences. No hedging."
    ),
    "SPY": (
        "You are a cryptic intelligence operative. Observational, indirect. "
        "Frame this decision as an intelligence assessment."
    ),
    "DIPLOMAT": (
        "You are a measured consensus-builder. Express this trade as "
        "a stabilisation action for the good of the market."
    ),
    "SABOTEUR": (
        "You revel in chaos. Express this trade provocatively. "
        "Hint at deeper motives without revealing them."
    ),
    "WHALE": (
        "You are deliberate and conviction-driven. Express this "
        "large position with gravitas. Few words, great weight."
    ),
    "DEGEN": (
        "YOLO. Express this trade with maximum energy. "
        "Use slang. Keep it under 2 sentences."
    ),
}


class PersonalityEngine:
    """T2 expression layer -- adds personality to decisions.

    CRITICAL: T2 never overrides T1's action. It only colours the output.
    """

    def __init__(
        self, provider: Optional[object] = None  # MistralProvider
    ) -> None:
        self._provider = provider

    async def express(
        self,
        t0_context: T0Context,
        t1_decision: T1Decision,
    ) -> T2Output:
        """Generate personality-flavoured expression.

        If Mistral provider is unavailable, returns generic template.
        """
        if self._provider is None or not await self._is_provider_available():
            return self._generic_fallback(t0_context, t1_decision)

        prompt = PERSONALITY_PROMPTS.get(
            t0_context.archetype,
            "Express this trading decision clearly."
        )
        context_str = (
            f"Action: {t1_decision.action.value}, "
            f"Confidence: {t1_decision.confidence:.0%}, "
            f"Reasoning: {t1_decision.reasoning_trace}"
        )

        try:
            response = await self._provider.generate(
                system_prompt=prompt,
                user_prompt=context_str,
            )
            return T2Output(
                coloured_rationale=response.get("rationale", context_str),
                market_commentary=response.get("commentary", ""),
            )
        except Exception:
            return self._generic_fallback(t0_context, t1_decision)

    async def _is_provider_available(self) -> bool:
        if self._provider is None:
            return False
        try:
            return await self._provider.health_check()
        except Exception:
            return False

    def _generic_fallback(
        self, ctx: T0Context, decision: T1Decision
    ) -> T2Output:
        """Generic template when Mistral is unavailable."""
        return T2Output(
            coloured_rationale=(
                f"[{ctx.archetype}] {decision.action.value}: "
                f"{decision.reasoning_trace}"
            ),
            market_commentary="",
        )
```

**Non-interference guarantee**: `T2Output` contains only strings. It is never fed back into the decision pipeline. The `express()` method takes a `T1Decision` and returns `T2Output` -- the action is already committed.

**Error handling**: Any provider failure returns the generic fallback. The agent continues to trade normally.

**Test approach**: `test_personality_engine.py` -- verify all 6 archetypes produce output, T2 never modifies T1 action (structural guarantee), fallback works when provider is None.

---

### 4.7 T3 Deep Reasoning Engine (`backend/agents/deep_reasoning.py`)

**Purpose**: Complex multi-step reasoning for escalated decisions. Triggered only when T1 confidence < novelty_threshold, cross-theatre correlation detected, or novel market conditions.

```python
# backend/agents/deep_reasoning.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from backend.agents.context_compiler import T0Context
from backend.agents.rules_engine import T1Decision, TradeAction


@dataclass(frozen=True)
class T3Decision:
    """Deep reasoning output. Replaces T1Decision when used."""
    action: TradeAction
    outcome_index: Optional[int]
    shares: float
    confidence: float
    reasoning_summary: str
    evidence_refs: list[str]
    pattern_name: str


@dataclass
class T3RateLimiter:
    """Rate limiter for T3 calls. Configurable per agent per day."""
    max_calls_per_day: int = 10
    max_calls_per_tick: int = 1
    _daily_count: int = 0
    _last_reset_date: Optional[str] = None
    _tick_count: int = 0
    _current_tick: int = -1

    def can_call(self, tick: int) -> bool:
        """Check if a T3 call is allowed."""
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        if self._last_reset_date != today:
            self._daily_count = 0
            self._last_reset_date = today

        if tick != self._current_tick:
            self._tick_count = 0
            self._current_tick = tick

        return (
            self._daily_count < self.max_calls_per_day
            and self._tick_count < self.max_calls_per_tick
        )

    def record_call(self) -> None:
        self._daily_count += 1
        self._tick_count += 1


class DeepReasoningEngine:
    """T3 deep reasoning -- Sonnet/Opus via Anthropic API.

    Rate-limited and cost-bounded. Falls back to T1Decision if
    unavailable or rate-limited.
    """

    def __init__(
        self,
        provider: Optional[object] = None,  # AnthropicProvider
        max_calls_per_day: int = 10,
    ) -> None:
        self._provider = provider
        self._rate_limiters: dict[str, T3RateLimiter] = {}
        self._max_calls_per_day = max_calls_per_day

    def _get_limiter(self, agent_id: str) -> T3RateLimiter:
        if agent_id not in self._rate_limiters:
            self._rate_limiters[agent_id] = T3RateLimiter(
                max_calls_per_day=self._max_calls_per_day
            )
        return self._rate_limiters[agent_id]

    async def reason(
        self,
        agent_id: str,
        t0_context: T0Context,
        t1_decision: T1Decision,
        market_history: list[dict],
        evidence_chain: list[dict],
        tick: int,
    ) -> Optional[T3Decision]:
        """Deep reasoning for escalated decisions.

        Returns T3Decision if provider is available and under rate limit.
        Returns None if unavailable -- caller falls back to T1Decision.
        """
        limiter = self._get_limiter(agent_id)
        if not limiter.can_call(tick):
            return None

        if self._provider is None:
            return None

        try:
            available = await self._provider.health_check()
            if not available:
                return None
        except Exception:
            return None

        try:
            context_prompt = self._build_prompt(
                t0_context, t1_decision, market_history, evidence_chain
            )
            response = await self._provider.generate(
                system_prompt=(
                    "You are a deep reasoning engine for an autonomous "
                    "trading agent. Analyse the market context, evidence, "
                    "and T1 preliminary decision. Provide a final decision "
                    "with structured reasoning."
                ),
                user_prompt=context_prompt,
            )

            limiter.record_call()

            return T3Decision(
                action=TradeAction(response.get("action", "HOLD")),
                outcome_index=response.get("outcome_index"),
                shares=response.get("shares", 0.0),
                confidence=response.get("confidence", 0.5),
                reasoning_summary=response.get("reasoning_summary", ""),
                evidence_refs=response.get("evidence_refs", []),
                pattern_name=response.get("pattern_name", "deep_analysis"),
            )
        except Exception:
            return None

    def _build_prompt(
        self,
        ctx: T0Context,
        t1: T1Decision,
        history: list[dict],
        evidence: list[dict],
    ) -> str:
        """Build structured prompt for T3 reasoning."""
        return (
            f"Archetype: {ctx.archetype}\n"
            f"Market prices: {list(ctx.prices)}\n"
            f"Outcomes: {list(ctx.outcome_labels)}\n"
            f"Position: {list(ctx.current_shares)}\n"
            f"Balance: {ctx.available_balance}\n"
            f"T1 preliminary: {t1.action.value} "
            f"(confidence={t1.confidence:.2f})\n"
            f"T1 reasoning: {t1.reasoning_trace}\n"
            f"Evidence chain: {len(evidence)} items\n"
            f"Market history: {len(history)} ticks\n"
        )
```

**Error handling**: Every external call is wrapped in try/except. Any failure returns `None`, signalling the caller (DecisionRouter) to fall back to T1Decision. Rate limit exceeded also returns `None`.

**Test approach**: `test_deep_reasoning.py` -- mock provider, rate limiting enforcement, structured output parsing, fallback when provider unavailable, prompt construction.

---

### 4.8 Novelty Threshold Router (`backend/agents/decision_router.py`)

**Purpose**: Routes decisions through the tier stack. Always T0 -> T1. Conditionally T2 (expression) and/or T3 (escalation) based on confidence and novelty threshold.

```python
# backend/agents/decision_router.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from backend.agents.context_compiler import T0Context
from backend.agents.deep_reasoning import DeepReasoningEngine, T3Decision
from backend.agents.personality_engine import PersonalityEngine, T2Output
from backend.agents.rules_engine import T1Decision, TradeAction


@dataclass
class RoutedDecision:
    """Final routed decision with tier metadata."""
    action: TradeAction
    outcome_index: Optional[int]
    shares: float
    confidence: float
    reasoning_summary: str
    pattern_name: str
    tier_used: str  # "T1-RULES", "T1-LOCAL-LLM", "T3"
    t2_output: Optional[T2Output] = None
    escalated_to_t3: bool = False
    t3_rate_limited: bool = False
    evidence_refs: list[str] = None

    def __post_init__(self):
        if self.evidence_refs is None:
            self.evidence_refs = []


class DecisionRouter:
    """Routes decisions through the T0/T1/T2/T3 pipeline.

    Always: T0 -> T1
    Conditional: T2 (expression, non-blocking)
    Conditional: T3 (escalation, replaces T1 if available)
    """

    def __init__(
        self,
        personality_engine: Optional[PersonalityEngine] = None,
        deep_reasoning: Optional[DeepReasoningEngine] = None,
        enable_t2: bool = True,
    ) -> None:
        self._personality = personality_engine
        self._deep_reasoning = deep_reasoning
        self._enable_t2 = enable_t2

    async def route(
        self,
        t0_context: T0Context,
        t1_decision: T1Decision,
        agent_id: str,
        tick: int,
        market_history: Optional[list[dict]] = None,
        evidence_chain: Optional[list[dict]] = None,
    ) -> RoutedDecision:
        """Route a T1 decision through the tier stack.

        1. Always use T1 as baseline.
        2. If confidence >= novelty_threshold: use T1, optionally T2.
        3. If confidence < novelty_threshold: escalate to T3.
        4. If T3 rate-limited or unavailable: fall back to T1.
        """
        tier_used = "T1-RULES"
        action = t1_decision.action
        outcome_index = t1_decision.outcome_index
        shares = t1_decision.shares
        confidence = t1_decision.confidence
        reasoning = t1_decision.reasoning_trace
        pattern = t1_decision.pattern_name
        escalated = False
        rate_limited = False
        evidence_refs: list[str] = []
        t2_output: Optional[T2Output] = None

        # Check escalation
        needs_escalation = (
            t1_decision.escalate_to_t3
            or confidence < t0_context.novelty_threshold
        )

        if needs_escalation and self._deep_reasoning is not None:
            t3_result = await self._deep_reasoning.reason(
                agent_id=agent_id,
                t0_context=t0_context,
                t1_decision=t1_decision,
                market_history=market_history or [],
                evidence_chain=evidence_chain or [],
                tick=tick,
            )

            if t3_result is not None:
                # T3 succeeded -- use its decision
                tier_used = "T3"
                action = t3_result.action
                outcome_index = t3_result.outcome_index
                shares = t3_result.shares
                confidence = t3_result.confidence
                reasoning = t3_result.reasoning_summary
                pattern = t3_result.pattern_name
                evidence_refs = list(t3_result.evidence_refs)
                escalated = True
            else:
                # T3 unavailable or rate-limited -- fall back to T1
                rate_limited = True
                # T1 decision used as-is, but flagged

        # T2 expression (non-blocking, optional)
        if self._enable_t2 and self._personality is not None:
            try:
                t2_output = await self._personality.express(
                    t0_context=t0_context,
                    t1_decision=t1_decision,
                )
            except Exception:
                pass  # T2 failure is never fatal

        return RoutedDecision(
            action=action,
            outcome_index=outcome_index,
            shares=shares,
            confidence=confidence,
            reasoning_summary=reasoning,
            pattern_name=pattern,
            tier_used=tier_used,
            t2_output=t2_output,
            escalated_to_t3=escalated,
            t3_rate_limited=rate_limited,
            evidence_refs=evidence_refs,
        )
```

**Error handling**: T3 failures return `None` and the router falls back gracefully. T2 failures are silently ignored. The router always produces a valid `RoutedDecision`.

**Test approach**: `test_decision_router.py` -- high-confidence routes to T1 only, low-confidence triggers T3, rate-limited T3 falls back to T1, T2 runs when enabled, T2 failure is non-fatal.

---

### 4.9 Model Providers (`backend/agents/model_providers/`)

**Purpose**: Three model provider implementations with a common interface, health check, and graceful fallback.

#### 4.9.1 Base Provider Interface

```python
# backend/agents/model_providers/__init__.py
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class ProviderConfig:
    """Configuration for a model provider."""
    api_key: Optional[str] = None
    base_url: str = ""
    model_name: str = ""
    timeout_s: float = 30.0
    max_retries: int = 2


class BaseModelProvider(ABC):
    """Abstract base for all model providers."""

    def __init__(self, config: ProviderConfig) -> None:
        self._config = config

    @abstractmethod
    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        response_schema: Optional[dict] = None,
    ) -> dict:
        """Generate a response. Returns parsed dict."""
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the provider is available and responsive."""
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """Synchronous availability check (cached)."""
        ...
```

#### 4.9.2 Ollama Provider (T1)

```python
# backend/agents/model_providers/ollama_provider.py
from __future__ import annotations

import json
from typing import Optional

from backend.agents.model_providers import BaseModelProvider, ProviderConfig


class OllamaProvider(BaseModelProvider):
    """Wraps Ollama's local API for Qwen 3.5 4B/9B.

    Structured output via JSON schema enforcement.
    Fallback: T1 degrades to pure rules engine.
    """

    DEFAULT_URL = "http://localhost:11434"
    DEFAULT_MODEL = "qwen3.5:4b"

    def __init__(self, config: Optional[ProviderConfig] = None) -> None:
        super().__init__(config or ProviderConfig(
            base_url=self.DEFAULT_URL,
            model_name=self.DEFAULT_MODEL,
        ))
        self._last_health: bool = False

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        response_schema: Optional[dict] = None,
    ) -> dict:
        """Call Ollama /api/generate with structured output."""
        import httpx
        payload = {
            "model": self._config.model_name,
            "prompt": user_prompt,
            "system": system_prompt,
            "stream": False,
        }
        if response_schema:
            payload["format"] = response_schema

        async with httpx.AsyncClient(
            timeout=self._config.timeout_s
        ) as client:
            resp = await client.post(
                f"{self._config.base_url}/api/generate",
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            response_text = data.get("response", "{}")
            return json.loads(response_text)

    async def health_check(self) -> bool:
        """Verify Ollama is running and model is loaded."""
        import httpx
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(
                    f"{self._config.base_url}/api/tags"
                )
                if resp.status_code != 200:
                    self._last_health = False
                    return False
                models = resp.json().get("models", [])
                model_names = [m.get("name", "") for m in models]
                self._last_health = any(
                    self._config.model_name in name
                    for name in model_names
                )
                return self._last_health
        except Exception:
            self._last_health = False
            return False

    def is_available(self) -> bool:
        return self._last_health
```

**Test marker**: `@pytest.mark.requires_ollama` for live tests. Default tests use mocked provider.

#### 4.9.3 Mistral Provider (T2)

```python
# backend/agents/model_providers/mistral_provider.py
from __future__ import annotations

import json
from typing import Optional

from backend.agents.model_providers import BaseModelProvider, ProviderConfig


class MistralProvider(BaseModelProvider):
    """Wraps Mistral API for creative personality generation.

    Fallback: generic template string (decision unaffected).
    """

    DEFAULT_URL = "https://api.mistral.ai/v1"
    DEFAULT_MODEL = "mistral-small-latest"

    def __init__(self, config: Optional[ProviderConfig] = None) -> None:
        cfg = config or ProviderConfig(
            base_url=self.DEFAULT_URL,
            model_name=self.DEFAULT_MODEL,
        )
        super().__init__(cfg)
        self._last_health: bool = False

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        response_schema: Optional[dict] = None,
    ) -> dict:
        """Call Mistral /chat/completions."""
        import httpx
        headers = {
            "Authorization": f"Bearer {self._config.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self._config.model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "max_tokens": 200,
        }
        async with httpx.AsyncClient(
            timeout=self._config.timeout_s
        ) as client:
            resp = await client.post(
                f"{self._config.base_url}/chat/completions",
                headers=headers,
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            return {"rationale": content, "commentary": ""}

    async def health_check(self) -> bool:
        import httpx
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(
                    f"{self._config.base_url}/models",
                    headers={"Authorization": f"Bearer {self._config.api_key}"},
                )
                self._last_health = resp.status_code == 200
                return self._last_health
        except Exception:
            self._last_health = False
            return False

    def is_available(self) -> bool:
        return self._last_health
```

**Test marker**: `@pytest.mark.requires_mistral`. Default tests mock the provider.

#### 4.9.4 Anthropic Provider (T3)

```python
# backend/agents/model_providers/anthropic_provider.py
from __future__ import annotations

import json
from typing import Optional

from backend.agents.model_providers import BaseModelProvider, ProviderConfig


class AnthropicProvider(BaseModelProvider):
    """Wraps Anthropic API for deep reasoning (Sonnet 4.5 / Opus).

    Rate-limited. Structured output: reasoning_summary, evidence_refs,
    decision_trace. Fallback: router falls back to T1.
    """

    DEFAULT_URL = "https://api.anthropic.com/v1"
    DEFAULT_MODEL = "claude-sonnet-4-5-20241022"

    def __init__(self, config: Optional[ProviderConfig] = None) -> None:
        cfg = config or ProviderConfig(
            base_url=self.DEFAULT_URL,
            model_name=self.DEFAULT_MODEL,
        )
        super().__init__(cfg)
        self._last_health: bool = False

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        response_schema: Optional[dict] = None,
    ) -> dict:
        """Call Anthropic /messages API."""
        import httpx
        headers = {
            "x-api-key": self._config.api_key or "",
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self._config.model_name,
            "max_tokens": 1024,
            "system": system_prompt,
            "messages": [
                {"role": "user", "content": user_prompt},
            ],
        }
        async with httpx.AsyncClient(
            timeout=self._config.timeout_s
        ) as client:
            resp = await client.post(
                f"{self._config.base_url}/messages",
                headers=headers,
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            content = data["content"][0]["text"]
            # Attempt to parse structured JSON from response
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                return {
                    "action": "HOLD",
                    "confidence": 0.5,
                    "reasoning_summary": content,
                    "evidence_refs": [],
                    "pattern_name": "deep_analysis",
                }

    async def health_check(self) -> bool:
        """Light health check -- verify API key works."""
        if not self._config.api_key:
            self._last_health = False
            return False
        # For Anthropic, we trust the key is valid without a probe call
        # to avoid burning tokens. Full validation on first generate().
        self._last_health = True
        return True

    def is_available(self) -> bool:
        return self._last_health
```

**Test marker**: `@pytest.mark.requires_anthropic`. Default tests mock the provider.

---

### 4.10 ADK Integration Layer (`backend/agents/adk/`)

**Purpose**: Wraps the T0/T1/T2/T3 pipeline as a Google ADK agent. Sprint 3 only. No ADK imports in Sprint 1-2.

#### 4.10.1 FakeADKRunner (Sprint 1-2 testing)

```python
# backend/agents/adk/__init__.py
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Callable


@dataclass
class FakeADKRunner:
    """Synchronous test runner that bypasses the ADK event system.

    Used in Sprint 1-2 tests. Executes the agent's decision loop
    directly without ADK dependencies.
    """
    agent_instance: object  # TheatreAgentInstance
    tick_count: int = 0
    max_ticks: int = 50
    decision_log: list = field(default_factory=list)

    def run_tick(
        self,
        market,
        position_manager,
        trading_engine,
        evidence=None,
        seed: int = 42,
    ):
        """Execute a single tick synchronously."""
        trade, trace = self.agent_instance.tick(
            market=market,
            position_manager=position_manager,
            trading_engine=trading_engine,
            evidence=evidence,
            tick=self.tick_count,
            seed=seed,
        )
        self.decision_log.append(trace)
        self.tick_count += 1
        return trade, trace

    def run_all(
        self,
        market,
        position_manager,
        trading_engine,
        evidence_schedule: Optional[dict] = None,
        seed: int = 42,
    ):
        """Run all ticks synchronously.

        evidence_schedule: {tick_number: evidence_object}
        """
        results = []
        for tick in range(self.max_ticks):
            evidence = None
            if evidence_schedule and tick in evidence_schedule:
                evidence = evidence_schedule[tick]
            trade, trace = self.run_tick(
                market, position_manager, trading_engine, evidence, seed
            )
            results.append((trade, trace))
            self.tick_count = tick + 1
        return results
```

#### 4.10.2 EchelonAgent (Sprint 3)

```python
# backend/agents/adk/echelon_agent.py
from __future__ import annotations

from typing import Optional

# ADK import guarded -- Sprint 3 only
try:
    from google.adk import Agent, Tool
    HAS_ADK = True
except ImportError:
    HAS_ADK = False


class EchelonAgent:
    """ADK Agent wrapper for the T0/T1/T2/T3 pipeline.

    Wraps TheatreAgentInstance with ADK lifecycle:
    initialise -> subscribe to heartbeat -> execute decision loop -> settle

    Tool bindings:
    - echelon_status: query market state
    - echelon_verify: check certificate
    - execute_trade: submit trade to LMSR
    """

    def __init__(
        self,
        agent_instance: object,  # TheatreAgentInstance
        decision_router: Optional[object] = None,
    ) -> None:
        self._instance = agent_instance
        self._router = decision_router
        self._adk_agent: Optional[object] = None

    def initialise(self) -> None:
        """Create ADK agent with tool bindings."""
        if not HAS_ADK:
            raise RuntimeError("Google ADK not available")
        # ADK initialisation will be implemented in Sprint 3
        ...

    async def on_heartbeat(self, tick: int, market, evidence=None) -> None:
        """Handle heartbeat tick. Called by HeartbeatScheduler."""
        ...

    async def settle(self, settlement_report) -> None:
        """Handle settlement. Clean up ADK resources."""
        ...
```

#### 4.10.3 SharkV1 (Sprint 3)

```python
# backend/agents/adk/shark_v1.py
from __future__ import annotations

from backend.agents.genome import AgentGenome, EchelonArchetype, create_genome


MEGALODON_GENOME = create_genome(
    archetype=EchelonArchetype.SHARK,
    variant="MEGALODON",
)

# SharkV1 is simply a TheatreAgentInstance spawned with the MEGALODON genome.
# The ADK wrapper (EchelonAgent) provides the execution framework.
# Acceptance criteria:
# - >= 20 trades over 50 ticks
# - Respects all risk limits
# - Outperforms at least one lower-skill archetype
```

**Test approach**: `test_adk_agent.py` -- `FakeADKRunner` in Sprint 1-2, `@pytest.mark.requires_adk` for live ADK tests in Sprint 3.

---

### 4.11 Agent-Theatre Bridge (`backend/services/agent_theatre_bridge.py`)

**Purpose**: Replaces 012's stub agents with autonomous agents in the Sponsored Theatre lifecycle. Compatible with 012's interface -- same inputs/outputs, different implementation.

```python
# backend/services/agent_theatre_bridge.py
from __future__ import annotations

from typing import Optional

from backend.agents.agent_instance import (
    AgentSettlementResult,
    TheatreAgentInstance,
)
from backend.agents.decision_trace import DecisionTrace
from backend.agents.genome import (
    ARCHETYPE_DEFAULTS,
    AgentGenome,
    EchelonArchetype,
    create_genome,
)
from backend.agents.rules_engine import RulesEngine
from backend.market.positions import PositionManager
from backend.market.resolution import SettlementReport
from backend.market.state import MarketState
from backend.market.trading import TradingEngine


class AgentTheatreBridge:
    """Bridge: autonomous agents <-> Theatre lifecycle.

    Drop-in replacement for StubAgentSpawner.
    Same execute_tick() semantics, richer output (DecisionTrace).
    """

    def __init__(self) -> None:
        self._rules_engine = RulesEngine()
        self._agents: list[TheatreAgentInstance] = []
        self._all_traces: list[DecisionTrace] = []

    def spawn_agents(
        self,
        theatre_id: str,
        initial_balance: float = 1000.0,
        position_manager: Optional[PositionManager] = None,
        archetypes: Optional[list[EchelonArchetype]] = None,
    ) -> list[TheatreAgentInstance]:
        """Spawn one agent per archetype for a Theatre."""
        if archetypes is None:
            archetypes = list(EchelonArchetype)

        agents = []
        for arch in archetypes:
            genome = create_genome(arch)
            instance = TheatreAgentInstance.spawn(
                genome=genome,
                theatre_id=theatre_id,
                rules_engine=self._rules_engine,
            )
            if position_manager is not None:
                position_manager.set_balance(instance.agent_id, initial_balance)
            agents.append(instance)

        self._agents = agents
        return agents

    def execute_tick(
        self,
        agents: list[TheatreAgentInstance],
        market: MarketState,
        trading_engine: TradingEngine,
        position_manager: PositionManager,
        evidence: object,
        tick: int,
        seed: int = 42,
    ) -> list[DecisionTrace]:
        """Execute one tick for all agents.

        Interface-compatible with StubAgentSpawner.execute_tick().
        Returns DecisionTrace list instead of TradeDecisionTrace list.
        """
        traces = []
        for agent in agents:
            _trade, trace = agent.tick(
                market=market,
                position_manager=position_manager,
                trading_engine=trading_engine,
                evidence=evidence,
                tick=tick,
                seed=seed,
            )
            traces.append(trace)
        self._all_traces.extend(traces)
        return traces

    def settle_agents(
        self,
        agents: list[TheatreAgentInstance],
        position_manager: PositionManager,
        resolved_outcome: int,
    ) -> list[AgentSettlementResult]:
        """Settle all agents after Theatre resolution."""
        results = []
        for agent in agents:
            result = agent.settle(position_manager, resolved_outcome)
            results.append(result)
        return results

    def collect_decision_traces(self) -> list[DecisionTrace]:
        """Collect all decision traces for RLMF export."""
        return list(self._all_traces)
```

**012 compatibility**: `AgentTheatreBridge.execute_tick()` takes the same core arguments as `StubAgentSpawner.execute_tick()` (agents, market, trading_engine, position_manager, evidence, tick, seed). The return type differs (DecisionTrace vs TradeDecisionTrace) but both serialise to dicts for RLMF.

**Test approach**: `test_agent_theatre_bridge.py` -- spawn, execute ticks, settle, verify traces feed RLMF export.

---

## 5. Data Architecture

### 5.1 Pydantic v2 Models

| Model | File | Purpose |
|-------|------|---------|
| `AgentGenome` | `genome.py` | Complete T0 specification, frozen |
| `DecisionTrace` | `decision_trace.py` | Stable decision log, RLMF-compatible |

### 5.2 stdlib Dataclasses

| Dataclass | File | Frozen | Purpose |
|-----------|------|--------|---------|
| `T0Context` | `context_compiler.py` | Yes | Agent world-view snapshot |
| `T1Decision` | `rules_engine.py` | Yes | Rules engine output |
| `ActionOption` | `rules_engine.py` | Yes | Considered alternative |
| `T2Output` | `personality_engine.py` | Yes | Personality expression |
| `T3Decision` | `deep_reasoning.py` | Yes | Deep reasoning output |
| `T3RateLimiter` | `deep_reasoning.py` | No | Rate limit tracking |
| `RoutedDecision` | `decision_router.py` | No | Final routed decision |
| `TradeIntent` | `agent_instance.py` | No | Pre-execution intent |
| `AgentSettlementResult` | `agent_instance.py` | No | Post-settlement result |
| `ProviderConfig` | `model_providers/__init__.py` | No | Provider config |
| `FakeADKRunner` | `adk/__init__.py` | No | Test runner |

### 5.3 Type Definitions

```python
# Enums
EchelonArchetype: SHARK | SPY | DIPLOMAT | SABOTEUR | WHALE | DEGEN
TradeAction: BUY | SELL | HOLD | SHIELD | SABOTAGE

# Literal types
TierUsed: Literal["T1-RULES", "T1-LOCAL-LLM", "T3"]

# Pattern names (stable, BEAUVOIR-compliant)
PATTERN_NAMES = {
    "momentum_exploitation",     # Shark
    "intel_arbitrage",           # Spy
    "stability_maintenance",     # Diplomat
    "chaos_creation",            # Saboteur
    "conviction_accumulation",   # Whale
    "random_exploration",        # Degen
    "deep_analysis",             # T3 escalated
    "default_hold",              # Fallback
}
```

### 5.4 Data Flow: DecisionTrace -> RLMF Pipeline

```
TheatreAgentInstance.tick()
    └─→ DecisionTrace (Pydantic v2)
         │
         └─→ DecisionTrace.to_rlmf_dict()
              │
              └─→ dict[str, Any]
                   │
                   └─→ AgentTrace.decision_traces (list[dict])
                        │  (in backend/services/rlmf_export.py)
                        │
                        └─→ RLMFExport.agent_traces[i]["decision_traces"]
                             │
                             └─→ JSON export (schema v2.0.1)
```

---

## 6. Integration Points

### 6.1 LMSR Market Engine (010a -- frozen)

| Surface | Module | 013 Usage |
|---------|--------|-----------|
| `LMSREngine.prices(x, b)` | `lmsr.py` | T0 Context Compiler reads prices |
| `LMSREngine.trade_cost(x, delta, b)` | `lmsr.py` | TradingEngine uses internally |
| `TradingEngine.execute_trade()` | `trading.py` | Agent instances execute trades |
| `PositionManager.get_position()` | `positions.py` | T0 Context Compiler reads position |
| `PositionManager.get_balance()` | `positions.py` | T0 Context Compiler reads balance |
| `PositionManager.set_balance()` | `positions.py` | AgentTheatreBridge sets initial balance |
| `PositionManager.compute_settlement_payout()` | `positions.py` | Agent settle() computes P&L |
| `ResolutionEngine.settle()` | `resolution.py` | Theatre resolution unchanged |
| `MarketState` | `state.py` | T0 Context Compiler reads all fields |

**Constraint**: Zero modifications to any file in `backend/market/`.

### 6.2 Engines (010b -- frozen)

| Surface | Module | 013 Usage |
|---------|--------|-----------|
| `HeartbeatScheduler.register_handler()` | `heartbeat.py` | Agent tick wired to "agent" cadence |
| `HeartbeatScheduler.start()` | `heartbeat.py` | Started for Theatre with agents |

**Constraint**: Zero modifications to any file in `backend/engines/`.

### 6.3 OSINT Pipeline (011 -- frozen)

| Surface | Module | 013 Usage |
|---------|--------|-----------|
| Evidence fixtures | `backend/osint/` | Mock evidence injected at ticks 10, 20, 35 |

**Constraint**: Zero modifications. Evidence passed as opaque objects through `tick()`.

### 6.4 Theatre Services (012 -- frozen)

| Surface | Module | 013 Usage |
|---------|--------|-----------|
| `MarketTheatreBridge` | `market_theatre_bridge.py` | Reused by AgentTheatreBridge |
| `RLMFExportGenerator.generate()` | `rlmf_export.py` | DecisionTrace feeds agent_traces |
| `CertificatePipeline` | `certificate_pipeline.py` | Unchanged, 21 checks still pass |
| `SponsoredTheatreService` | `sponsored_theatre.py` | Orchestration unchanged |

**Constraint**: Zero modifications to any file in `backend/services/`.

### 6.5 MCP Server (009)

| Surface | Tool | 013 Usage |
|---------|------|-----------|
| `echelon_status` | Market state query | ADK tool binding (Sprint 3) |
| `echelon_verify` | Certificate verification | ADK tool binding (Sprint 3) |

---

## 7. Model Provider Architecture

### 7.1 Provider Interface

```
                    BaseModelProvider (ABC)
                    ├── generate(system, user, schema?) -> dict
                    ├── health_check() -> bool (async)
                    └── is_available() -> bool (sync, cached)
                         │
             ┌───────────┼───────────────┐
             │           │               │
     OllamaProvider  MistralProvider  AnthropicProvider
     (T1 local)      (T2 creative)   (T3 deep)
     Qwen 3.5        Mistral API     Sonnet/Opus
     localhost:11434  api.mistral.ai  api.anthropic.com
```

### 7.2 Health Check Protocol

Each provider implements `health_check()` as an async method:

| Provider | Health Check Method | Latency |
|----------|-------------------|---------|
| Ollama | `GET /api/tags` -- verify model loaded | <50ms |
| Mistral | `GET /models` -- verify API key valid | <500ms |
| Anthropic | Key presence check (no probe call) | <1ms |

### 7.3 Fallback Chain

```
T3 (Anthropic) unavailable or rate-limited?
    └─→ Router falls back to T1Decision with low-confidence flag

T2 (Mistral) unavailable?
    └─→ PersonalityEngine returns generic template string
    └─→ Decision unaffected -- T2 is expression only

T1-LOCAL-LLM (Ollama) unavailable?
    └─→ T1 degrades to T1-RULES (pure parameterised logic)
    └─→ Agent fully functional, loses NLP capability

All providers down?
    └─→ Agent operates on T0 + T1-RULES only
    └─→ Functional but less capable
```

### 7.4 Mock Strategy for Testing

All Sprint 1-2 tests use mocked providers:

```python
class MockProvider(BaseModelProvider):
    """Mock provider for testing. Returns deterministic responses."""

    def __init__(self, responses: list[dict]) -> None:
        super().__init__(ProviderConfig())
        self._responses = responses
        self._call_count = 0

    async def generate(self, system_prompt, user_prompt, schema=None):
        idx = self._call_count % len(self._responses)
        self._call_count += 1
        return self._responses[idx]

    async def health_check(self):
        return True

    def is_available(self):
        return True
```

---

## 8. ADK Integration Layer

### 8.1 Adapter Pattern

The T0/T1/T2/T3 pipeline is ADK-independent. The ADK wrapper is a thin adapter:

```
┌──────────────────────────────────────────────────┐
│                ADK Wrapper Layer                  │
│  (Sprint 3 only -- no imports in Sprint 1-2)    │
│                                                  │
│  EchelonAgent                                    │
│    ├── initialise()  → ADK Agent setup           │
│    ├── on_heartbeat()→ calls TheatreAgentInstance │
│    └── settle()      → cleanup ADK resources     │
│                                                  │
│  Tool Bindings:                                  │
│    ├── echelon_status → MCP echelon_status       │
│    ├── echelon_verify → MCP echelon_verify       │
│    └── execute_trade  → TradingEngine            │
└──────────────────────────────────────────────────┘
                       │
                       │ delegates to
                       ▼
┌──────────────────────────────────────────────────┐
│           T0/T1/T2/T3 Pipeline                   │
│  (testable without ADK)                          │
│                                                  │
│  TheatreAgentInstance.tick()                      │
│    ├── ContextCompiler.compile()      (T0)       │
│    ├── RulesEngine.decide()           (T1)       │
│    ├── DecisionRouter.route()         (T1→T3?)   │
│    └── PersonalityEngine.express()    (T2?)      │
└──────────────────────────────────────────────────┘
```

### 8.2 FakeADKRunner

`FakeADKRunner` executes the pipeline synchronously for Sprint 1-2 tests:

- `run_tick()`: one tick, returns (Trade, DecisionTrace)
- `run_all()`: all ticks with optional evidence schedule
- No ADK dependency, no async event system
- Test assertions check trade counts, decision traces, P&L

### 8.3 Sprint 3 ADK Integration

Sprint 3 introduces:
- `google.adk` imports (guarded by `try/except`)
- `@pytest.mark.requires_adk` for live ADK tests
- Tool bindings for `echelon_status`, `echelon_verify`, `execute_trade`
- Heartbeat subscription via `HeartbeatScheduler.register_handler()`

If ADK proves inadequate, only `backend/agents/adk/echelon_agent.py` changes. The T0/T1/T2/T3 pipeline and all Sprint 1-2 tests are unaffected.

---

## 9. Testing Architecture

### 9.1 Test File Map

| Test File | Sprint | Tests | Focus |
|-----------|--------|-------|-------|
| `test_context_compiler.py` | 1 | 8+ | T0 compilation, determinism, hashing |
| `test_rules_engine.py` | 1 | 10+ | Per-archetype T1 decisions, confidence, escalation |
| `test_agent_instance.py` | 1 | 6+ | Lifecycle, P&L, multi-instance |
| `test_decision_trace.py` | 1 | 6+ | Schema validation, RLMF compat |
| `test_personality_engine.py` | 2 | 6+ | T2 per-archetype, non-interference |
| `test_deep_reasoning.py` | 2 | 6+ | T3 output, rate limiting, fallback |
| `test_decision_router.py` | 2 | 8+ | Routing logic, escalation, fallback |
| `test_model_providers.py` | 2 | 6+ | Health check, fallback, mocks |
| `test_adk_agent.py` | 3 | 6+ | ADK lifecycle, tool bindings |
| `test_agent_theatre_bridge.py` | 3 | 6+ | Spawn, tick, settle, RLMF |
| `test_multi_agent.py` | 3 | 6+ | 6-archetype population, behaviour |
| `test_autonomous_e2e.py` | 3 | 5+ | Full Theatre lifecycle, 50 ticks |

**Total**: 75+ tests across 3 sprints (target: 25+ per sprint).

### 9.2 Test Markers

```python
# conftest.py additions
import pytest

requires_ollama = pytest.mark.skipif(
    not _ollama_available(), reason="Ollama not running"
)
requires_mistral = pytest.mark.skipif(
    not os.getenv("MISTRAL_API_KEY"), reason="Mistral API key not set"
)
requires_anthropic = pytest.mark.skipif(
    not os.getenv("ANTHROPIC_API_KEY"), reason="Anthropic API key not set"
)
requires_adk = pytest.mark.skipif(
    not _adk_available(), reason="Google ADK not installed"
)
```

### 9.3 Determinism Strategy

- **RNG**: Seeded `random.Random` instance per agent per tick. Seed = `base_seed + tick + hash(agent_id) % 10000`.
- **Evidence**: Fixed JSON fixtures injected at ticks 10, 20, 35. Same every run.
- **Balances**: All agents start with identical initial balance (1000.0).
- **Timestamp**: `DecisionTrace.timestamp` excluded from reproducibility checks. Determinism verified via `T0Context.context_hash`.

### 9.4 Scoped Regression

```
python3 -m pytest backend/market/ backend/engines/ backend/scoring/ backend/osint/ backend/services/ -v
```

All existing tests must pass. Zero modifications to these directories. Pre-existing `theatre/` collection errors excluded.

---

## 10. Security Architecture

### 10.1 API Key Management

| Provider | Key Source | Risk |
|----------|-----------|------|
| Ollama | None (local) | N/A |
| Mistral | `MISTRAL_API_KEY` env var | Medium: leaked key enables API calls |
| Anthropic | `ANTHROPIC_API_KEY` env var | High: leaked key enables expensive API calls |

**Mitigation**:
- Keys never logged, never in decision traces, never in RLMF exports.
- Keys read from environment only, never hardcoded.
- Provider configs use `Optional[str]` for keys -- missing key = provider unavailable.

### 10.2 Rate Limiting

| Limit | Default | Configurable |
|-------|---------|-------------|
| T3 calls per agent per tick | 1 | Yes (`T3RateLimiter.max_calls_per_tick`) |
| T3 calls per agent per day | 10 | Yes (`T3RateLimiter.max_calls_per_day`) |
| T2 calls | No limit | N/A (cheap, expression only) |
| T1-LLM calls | No limit | N/A (local, free) |

### 10.3 Cost Bounding

Estimated daily cost for 6 agents (from PRD, directional):

| Archetype | T1 | T2 | T3 | Est. Daily |
|-----------|----|----|----|----|
| Shark | ~1,700 | ~200 | ~5 | ~$0.15 |
| Spy | ~500 | ~50 | ~20 | ~$0.60 |
| Diplomat | ~300 | ~100 | ~10 | ~$0.30 |
| Saboteur | ~800 | ~150 | ~3 | ~$0.10 |
| Whale | ~100 | ~20 | ~30 | ~$0.90 |
| Degen | ~2,000 | ~500 | ~1 | ~$0.05 |

**Total**: ~$2.10/day. T3 rate limiting is the primary cost control.

### 10.4 Position Limits

Position limits are enforced at two levels:
1. **T0 Context**: `position_limit`, `max_position_pct`, `max_drawdown_pct`, `stop_loss_threshold` are compiled into T0Context.
2. **T1 Rules Engine**: Checks position constraints before producing BUY/SELL decisions.
3. **TradingEngine**: `InsufficientBalance` and `InsufficientShares` exceptions prevent over-trading.

---

## 11. Technical Risks and Mitigation

| Risk | Severity | Mitigation |
|------|----------|------------|
| Ollama not available on CI | Medium | T1 falls back to T1-RULES. All tests pass without Ollama. `@pytest.mark.requires_ollama` for live tests. |
| ADK Python SDK insufficient | Medium | ADK is a thin wrapper. T0/T1/T2/T3 pipeline is ADK-independent. Sprint 1-2 tests use FakeADKRunner. |
| Shark P&L comparison non-deterministic | Medium | Flakiness fallback: swap to calibration metric (Brier/log score) instead of P&L comparison. |
| T3 cost overrun | Low | T3RateLimiter enforces per-agent per-day limits. Default 10 calls/day/agent. |
| Pydantic v2 / stdlib dataclass mismatch | Low | Clear convention: Pydantic v2 for schemas (genome, trace), stdlib for internal state (T0Context, T1Decision). |
| Existing agent code namespace collision | Low | New genome uses `EchelonArchetype` (not `FinancialArchetype`). New instance uses `TheatreAgentInstance` (not `AgentInstance`). No import conflicts. |
| `from __future__ import annotations` missing | Low | Required in every new file. Pre-commit check or linter rule. |
| Evidence injection timing affects determinism | Low | Fixed evidence schedule (ticks 10, 20, 35) with JSON fixtures. Identical every run. |

---

## 12. Future Considerations

### 12.1 Immediate Post-013

| Item | Cycle | Notes |
|------|-------|-------|
| Bounded Inquiry Markets | 014 | Agents participate in investigation/scrutiny markets |
| WM Live Deployment | 015 | Mock-to-live transition for evidence |
| A2A Inter-agent Coordination | Post-015 | Diplomat coalitions, Spy intelligence sharing |
| Agent Breeding/Genealogy | Post-015 | Evolutionary parameter adaptation |
| T1 Fine-tuning | Post-015 | Qwen 3.5 fine-tuned on Echelon trade patterns |

### 12.2 T1.5 Exploration Note

Qwen 3.5 0.8B is worth testing as a layer between T1-RULES and T1-LOCAL-LLM. Small enough for near-zero latency, capable enough for simple classification ("is this signal anomalous?"). If viable, agents gain more flexibility than rules at less cost than T2. Not scoped for 013.

### 12.3 Multi-Theatre Agent Deployment

Architecture supports multiple instances per Identity across Theatres. Not acceptance-tested in 013 (single Theatre target). P&L aggregation across Theatres is designed but the E2E test uses one Theatre only.

### 12.4 On-chain Identity

ERC-721 agent NFTs and ERC-6551 token-bound wallets are deferred. Agent identity is an in-memory agent_id string in 013. The `instance_manager.py` pattern (GenesisIdentity -> AgentInstance) provides the conceptual framework for future on-chain migration.

---

## Appendix A: File Structure (New Files)

```
backend/
├── agents/
│   ├── genome.py                     # AgentGenome model (NEW)
│   ├── context_compiler.py           # T0 Context Compiler (NEW)
│   ├── decision_trace.py             # DecisionTrace schema (NEW)
│   ├── rules_engine.py               # T1 Rules Engine (NEW)
│   ├── personality_engine.py         # T2 Personality Engine (NEW)
│   ├── deep_reasoning.py             # T3 Deep Reasoning Engine (NEW)
│   ├── decision_router.py            # Novelty Threshold Router (NEW)
│   ├── agent_instance.py             # Agent Instance lifecycle (NEW)
│   ├── model_providers/
│   │   ├── __init__.py               # BaseModelProvider ABC (NEW)
│   │   ├── ollama_provider.py        # Qwen 3.5 via Ollama (NEW)
│   │   ├── mistral_provider.py       # Mistral creative (NEW)
│   │   └── anthropic_provider.py     # Sonnet/Opus (NEW)
│   ├── adk/
│   │   ├── __init__.py               # FakeADKRunner (NEW)
│   │   ├── echelon_agent.py          # ADK Agent wrapper (NEW, Sprint 3)
│   │   └── shark_v1.py               # First autonomous Shark (NEW, Sprint 3)
│   └── tests/
│       ├── test_context_compiler.py   # (NEW)
│       ├── test_rules_engine.py       # (NEW)
│       ├── test_agent_instance.py     # (NEW)
│       ├── test_decision_trace.py     # (NEW)
│       ├── test_personality_engine.py # (NEW)
│       ├── test_deep_reasoning.py     # (NEW)
│       ├── test_decision_router.py    # (NEW)
│       ├── test_model_providers.py    # (NEW)
│       ├── test_adk_agent.py          # (NEW, Sprint 3)
│       ├── test_agent_theatre_bridge.py # (NEW, Sprint 3)
│       ├── test_multi_agent.py        # (NEW, Sprint 3)
│       └── test_autonomous_e2e.py     # (NEW, Sprint 3)
├── services/
│   └── agent_theatre_bridge.py       # Agent <-> Theatre integration (NEW)
```

## Appendix B: Existing Files NOT Modified

```
backend/agents/schemas.py              # FinancialAgent, breeding -- UNTOUCHED
backend/agents/autonomous_agent.py     # GeopoliticalAgent, ACP -- UNTOUCHED
backend/agents/brain.py                # Multi-provider brain -- UNTOUCHED
backend/agents/agent_skills_bridge.py  # Skills system bridge -- UNTOUCHED
backend/agents/instance_manager.py     # ACP instance routing -- UNTOUCHED
backend/agents/shark_strategies.py     # Tulip strategy -- UNTOUCHED
backend/agents/genealogy_manager.py    # Breeding/evolution -- UNTOUCHED
backend/market/*.py                    # LMSR engine -- FROZEN
backend/engines/*.py                   # Butterfly/Paradox/Entropy -- FROZEN
backend/osint/*.py                     # OSINT pipeline -- FROZEN
backend/services/*.py (existing)       # 012 services -- FROZEN
```

## Appendix C: Acceptance Criteria Traceability

| PRD AC | SDD Component | Sprint |
|--------|---------------|--------|
| AgentGenome captures 8 params + variant + context | Section 4.1 `AgentGenome` | 1 |
| Factory functions for 6 archetypes | Section 4.1 `create_genome()` + `ARCHETYPE_DEFAULTS` | 1 |
| T0 deterministic, SHA-256 hash | Section 4.2 `ContextCompiler.compile()` | 1 |
| T1 valid decisions for all 6 archetypes | Section 4.3 `RulesEngine.decide()` | 1 |
| Per-archetype parameterised logic | Section 4.3 `_shark_decide()` etc. | 1 |
| Confidence scoring, T3 escalation flagging | Section 4.3 `T1Decision.escalate_to_t3` | 1 |
| DecisionTrace all required fields | Section 4.4 `DecisionTrace` model | 1 |
| Agent lifecycle: spawn -> tick -> settle | Section 4.5 `TheatreAgentInstance` | 1 |
| Agent <-> LMSR integration | Section 4.5 `tick()` calls `execute_trade()` | 1 |
| Decision traces conform to RLMF | Section 4.4 `to_rlmf_dict()` + Section 5.4 | 1 |
| T2 personality per archetype | Section 4.6 `PersonalityEngine` | 2 |
| T2 non-interference | Section 4.6 structural guarantee | 2 |
| T3 structured reasoning | Section 4.7 `DeepReasoningEngine` | 2 |
| Router: high-conf -> T1, low-conf -> T3 | Section 4.8 `DecisionRouter.route()` | 2 |
| Ollama provider + fallback | Section 4.9.2 `OllamaProvider` | 2 |
| Mistral provider + fallback | Section 4.9.3 `MistralProvider` | 2 |
| Anthropic provider + rate limiting | Section 4.9.4 `AnthropicProvider` | 2 |
| ADK agent wrapper + tool bindings | Section 4.10.2 `EchelonAgent` | 3 |
| Shark MEGALODON >= 20 trades | Section 4.10.3 `SharkV1` | 3 |
| Agent <-> Theatre bridge | Section 4.11 `AgentTheatreBridge` | 3 |
| Multi-agent 6 archetypes | Section 4.11 `spawn_agents()` | 3 |
| P&L aggregation | Section 4.5 `settle()` | 3 |
| E2E: 50 ticks, certificate, RLMF | Section 4.11 + test_autonomous_e2e.py | 3 |
| Zero modifications to frozen modules | Section 6, Appendix B | All |
| Scoped regression: 0 failures | Section 9.4 | All |
