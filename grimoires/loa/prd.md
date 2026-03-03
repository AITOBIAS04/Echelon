# PRD: Agent Runtime — Four-Tier Hierarchical Intelligence

**Cycle**: 013
**Version**: 1.0
**Date**: 2026-03-03
**Predecessor**: Cycle-012 (Sponsored Theatre E2E — proves infrastructure, defines agent interface via stubs)

---

## 1. Problem Statement

Cycle-012 closed the integration loop: a sponsor commissions a Theatre, stub agents trade against the LMSR, evidence flows through the pipeline, the Composed Oracle resolves, and the sponsor receives a calibration certificate with RLMF export. But the agents are stubs — dataclasses with scripted strategies that produce deterministic trades regardless of market dynamics, evidence signals, or risk context.

Without autonomous agents, Echelon cannot produce meaningful RLMF training data. Stub agents make the same trades every time. Their decision traces are trivial — there is no reasoning to learn from. The calibration certificate proves the infrastructure works, but the training data it produces has zero commercial value.

The components exist. The intelligence does not.

Cycle-013 replaces stub agents with a four-tier hierarchical intelligence system: T0 (static context, zero cost) → T1 (fast reasoning via rules engine and local LLM, near-zero cost) → T2 (personality expression via Mistral, low cost) → T3 (deep reasoning via Sonnet/Opus, high cost, used sparingly). The novelty threshold router ensures 90%+ decisions stay at T1, keeping per-agent costs under $1/day while producing decision traces rich enough to train future agents.

> Sources: echelon_cycle_013.md:12-25, echelon_platform_roadmap.md:142-156

---

## 2. Vision

After Cycle-013, Echelon has its first autonomous market participant. A Shark agent reads market state, evaluates evidence, makes a trade decision via T0+T1, expresses it via T2, and escalates to T3 only when the novelty threshold is breached. P&L aggregates back to agent identity. Decision traces at every tick produce the training data that is the commercial product.

Six archetypes trade simultaneously in a Companies House Theatre: Shark exploits momentum, Spy trades on evidence arrival, Diplomat stabilises spreads, Saboteur disrupts, Whale takes large conviction positions, Degen trades randomly. The heterogeneous strategies create realistic market dynamics — price discovery emerges from agent interaction, not scripted behaviour.

This is the cycle that turns infrastructure into a living system. Google ADK provides the execution framework. Ollama provides local inference for T1. Mistral provides personality for T2. Anthropic provides deep reasoning for T3. All providers have graceful fallback — agents remain functional with degraded capability when any provider is unavailable.

> Sources: echelon_cycle_013.md:12-25, echelon_platform_roadmap.md:148-154

---

## 3. Goals & Success Metrics

### 3.1 Primary Goals

1. **AgentGenome Model**: Complete T0 context specification — 8 archetype parameters (ρ, ε, γ, ξ, L, σ, φ, π), variant modifiers, Theatre-specific context, position constraints, decision routing config, genome version pin.
2. **T0 Context Compiler**: Deterministic compilation of AgentGenome + TheatreTemplate + MarketState into a frozen T0Context dataclass. Zero inference cost. The agent's complete "view of the world."
3. **T1 Rules Engine**: Parameterised decision engine driven by T0 context. Per-archetype decision logic producing T1Decision (action, confidence, reasoning_trace). Confidence scoring with novelty threshold flagging.
4. **DecisionTrace Schema**: Stable structured log for every agent decision — BEAUVOIR-compliant with `tier_used`, `pattern_name`, `options_considered`, `reasoning_summary`, `evidence_refs`. RLMF-compatible.
5. **Agent Instance Lifecycle**: Ephemeral instances bound to Theatres — spawn → tick → settle. Multiple instances per Identity. P&L aggregation back to Identity.
6. **T2 Personality Engine**: Mistral-powered expression layer. Adds archetype-specific voice to T1 decisions. Never overrides T1's action — expression only.
7. **T3 Deep Reasoning Engine**: Sonnet/Opus-powered deep analysis. Triggered only on low T1 confidence, anomalies, or novel conditions. Rate-limited and cost-bounded.
8. **Novelty Threshold Router**: Routes decisions through the tier stack. Always T0 → T1, then conditionally T2 (expression) and/or T3 (escalation).
9. **Model Providers with Graceful Fallback**: Ollama (T1 local LLM), Mistral (T2), Anthropic (T3) — each with health check and fallback to lower capability.
10. **ADK Agent Wrapper**: Google ADK integration wrapping the T0/T1/T2/T3 pipeline. Tool bindings for echelon_status, echelon_verify, execute_trade. Heartbeat subscription.
11. **First Autonomous Shark Agent**: MEGALODON variant executing ≥20 trades over 50 ticks, respecting all risk limits, outperforming at least one lower-skill archetype.
12. **Multi-Agent Population**: All 6 archetypes trading simultaneously in a Theatre with distinct observable behaviour.
13. **Theatre Integration**: Replace 012's stub agents with autonomous agents. Compatible with existing E2E test infrastructure. Decision traces feed RLMF export.

### 3.2 Success Metrics

| Metric | Target |
|--------|--------|
| Sprint 1 new tests | 25+ |
| Sprint 2 new tests | 25+ |
| Sprint 3 new tests | 25+ |
| Scoped regression | 0 failures in `backend/market/`, `backend/engines/`, `backend/scoring/`, `backend/osint/`, `backend/services/` |
| LMSR engine modifications | 0 (integration layer only) |
| OSINT pipeline modifications | 0 |
| Paradox Engine modifications | 0 |
| Shark trades over 50 ticks | ≥20 |
| Archetype-distinct behaviour | All 6 archetypes show characteristic patterns |
| T3 escalation | At least 1 evidence-triggered escalation in E2E test |
| Decision trace RLMF conformance | 100% of traces pass schema validation |
| Provider fallback | Agents functional with any single provider down |
| Certificate verifier checks | 21/21 pass (autonomous agent Theatre) |

### 3.3 Regression Baseline

Scoped regression covers five module paths:

```
python3 -m pytest backend/market/ backend/engines/ backend/scoring/ backend/osint/ backend/services/ -v
```

Pre-existing `theatre/` collection errors are excluded from 013's regression baseline. Everything in the five scoped directories must pass.

### 3.4 Carryover Findings from Cycle-012

| ID | Severity | Description | 013 Action |
|----|----------|-------------|------------|
| MEDIUM-2 | MEDIUM | ConvergenceDetector uses `source_group` instead of dedicated domain field. | Monitor only. WM-only in 013. Evaluate when non-WM collectors land (Cycle-015). |
| LOW-3 | LOW | `asyncio.get_event_loop()` deprecation. | No action — Python 3.9.6 target not affected. |

> Sources: grimoires/loa/archive/2026-03-03-sponsored-theatre-end-to-end/a2a/sprint-24/auditor-sprint-feedback.md

---

## 4. Functional Requirements

### 4.1 AgentGenome Model

**File**: `backend/agents/genome.py` (extend existing)

Pydantic v2 model capturing the complete T0 context specification:
- 8 archetype parameters: `risk_appetite` (ρ), `evidence_sensitivity` (ε), `time_preference` (γ), `exploration_rate` (ξ), `position_limit` (L), `sabotage_propensity` (σ), `shield_propensity` (φ), `patience` (π)
- `archetype: str` — one of 6 core archetypes (SHARK, SPY, DIPLOMAT, SABOTEUR, WHALE, DEGEN)
- `variant: Optional[str]` — e.g., MEGALODON for Shark
- `variant_overrides: dict` — parameter overrides for variants
- Theatre-specific context: `committed_sources`, `outcome_labels`, `resolution_date`, `liquidity_b`
- Position constraints: `max_position_pct`, `max_drawdown_pct`, `stop_loss_threshold`
- Decision routing: `novelty_threshold` (confidence below this → escalate to T3)
- `genome_version: str` — for auditability

**Archetype Behaviour Matrix (v1.0)**:

| Parameter | Symbol | Shark | Spy | Diplomat | Saboteur | Whale | Degen |
|-----------|--------|-------|-----|----------|----------|-------|-------|
| Risk Appetite | ρ | 0.85 | 0.40 | 0.30 | 0.95 | 0.70 | 1.00 |
| Evidence Sensitivity | ε | 0.70 | 0.90 | 0.50 | 0.30 | 0.55 | 0.15 |
| Time Preference | γ | 0.95 | 0.98 | 0.99 | 0.90 | 0.92 | 0.85 |
| Exploration Rate | ξ | 0.15 | 0.40 | 0.20 | 0.60 | 0.10 | 0.95 |
| Position Limit | L | 10,000 | 2,500 | 5,000 | 7,500 | 25,000 | 1,000 |
| Sabotage Propensity | σ | 0.30 | 0.05 | 0.02 | 0.95 | 0.15 | 0.50 |
| Shield Propensity | φ | 0.10 | 0.15 | 0.85 | 0.05 | 0.30 | 0.02 |
| Patience | π | 30 | 120 | 60 | 45 | 90 | 10 |

> Sources: echelon_cycle_013.md:93-108, Echelon_System_Bible_v13.md §VIII

### 4.2 T0 Context Compiler

**File**: `backend/agents/context_compiler.py`

Compiles AgentGenome + Theatre config + MarketState into a frozen T0Context:
- Input: AgentGenome + TheatreTemplate + current MarketState
- Output: `T0Context` (frozen dataclass):
  - Archetype parameters (from genome)
  - Market context (prices, phase, evidence_coverage_pct)
  - Position state (current shares, net_cashflow, available balance)
  - Theatre rules (committed sources, resolution date, fee schedule)
  - Constraints (position limits, risk budgets)
- Deterministic: same inputs always produce same T0Context
- SHA-256 hash of T0Context enables reproducibility verification
- Zero inference cost — pure data transformation

> Sources: echelon_cycle_013.md:131-141

### 4.3 T1 Rules Engine

**File**: `backend/agents/rules_engine.py`

Parameterised decision engine driven by T0 context:
- Input: T0Context
- Output: `T1Decision` (action, confidence, reasoning_trace)
- Actions: `BUY(outcome, shares)`, `SELL(outcome, shares)`, `HOLD`, `SHIELD`, `SABOTAGE`
- Decision logic per archetype (parameterised by genome, not hard-coded):
  - **Shark**: momentum check → if leading outcome price increased > ρ×threshold, BUY. If position profit > γ×target, SELL (take profit).
  - **Spy**: evidence check → if new evidence arrived since last tick AND evidence_sensitivity > ε_threshold, evaluate signal and trade.
  - **Diplomat**: stability check → if market spread > (1-φ)×max_spread, buy trailing outcome to stabilise.
  - **Saboteur**: disruption check → if stability < (1-σ)×threshold, random contrary trade.
  - **Whale**: conviction check → if evidence strongly favours one outcome AND position < L×conviction_pct, large buy.
  - **Degen**: random action weighted by exploration_rate ξ.
- Each decision carries a confidence score (0.0–1.0)
- If confidence < `novelty_threshold` (from genome) → flag for T3 escalation

**T1 sub-tier naming**: In Sprint 1, T1 operates as **T1-RULES** (pure parameterised logic, no inference). In Sprint 2, Ollama integration adds **T1-LOCAL-LLM** (Qwen 3.5 via Ollama) with automatic fallback to T1-RULES if Ollama is unavailable. Decision traces record `tier_used` as `"T1-RULES"` or `"T1-LOCAL-LLM"`.

> Sources: echelon_cycle_013.md:143-156

### 4.4 DecisionTrace Schema

**File**: `backend/agents/decision_trace.py`

Pydantic v2 model defining the stable decision log schema. Every T1 (and T3) decision produces a trace conforming to this schema. Satisfies BEAUVOIR's agent-first citizenship requirements.

Required fields (stable keys — must not change between agent versions):
- `tick_id: str`, `agent_id: str`, `theatre_id: str`, `timestamp: datetime`
- `tier_used: Literal["T1-RULES", "T1-LOCAL-LLM", "T3"]`
- `market_state_snapshot: dict` (prices, phase, evidence_coverage_pct)
- `evidence_state: dict` (last_evidence_ts, new_evidence_flag, source_ids_cited)
- `t0_context_hash: str` (SHA-256 of T0Context — enables reproducibility)
- `action: str` (BUY/SELL/HOLD/SHIELD/SABOTAGE + parameters)
- `confidence: float` (0.0–1.0)
- `pattern_name: str` — named pattern from archetype matrix (e.g., "momentum_exploitation", "stability_maintenance", "intel_arbitrage", "chaos_creation", "conviction_accumulation", "random_exploration"). Required — every decision must map to a named pattern.
- `options_considered: list[dict]` — what alternatives were evaluated (action, estimated value, rejection reason)
- `reasoning_summary: str` — human-readable explanation
- `escalated_to_t3: bool`
- `evidence_refs: list[str]` — source IDs or bundle IDs cited (empty list if none)

**Determinism note**: `timestamp` is observational only and must not be included in any commitment hash or reproducibility check.

> Sources: echelon_cycle_013.md:157-176

### 4.5 Agent Instance Lifecycle

**File**: `backend/agents/agent_instance.py`

Ephemeral agent instance bound to a Theatre:
- `spawn(identity_genome, theatre_id)` → creates instance with T0 context
- `tick(market_state, evidence)` → runs T0 compiler → T1 rules engine → returns action
- `settle(settlement_report)` → records final P&L, closes instance
- Instance inherits genome from Identity, operates for the Theatre's lifetime
- Multiple instances per Identity (one per Theatre)
- P&L aggregates back to Identity

> Sources: echelon_cycle_013.md:178-186

### 4.6 Agent ↔ LMSR Integration

Wire agent instances into the LMSR trading engine (replacing 012's stub agents):
- Agent's `tick()` produces a `TradeIntent`
- TradeIntent validated against position limits (T0 constraints)
- `TradingEngine.execute_trade()` called if valid
- Position updated in PositionManager
- Decision trace recorded

> Sources: echelon_cycle_013.md:187-194

### 4.7 T2 Personality Engine

**File**: `backend/agents/personality_engine.py`

Expression layer — adds archetype-specific voice to decisions:
- Input: T1Decision + AgentGenome (personality profile)
- Output: `T2Output` (coloured_rationale, market_commentary, diplomatic_message)
- Model: Mistral creative variant (API or self-hosted)
- T2 is **NOT** in the decision path — it never overrides T1's action
- T2 runs only when the decision produces externally visible output
- Prompt template per archetype:
  - Shark: confident, terse, momentum-focused
  - Spy: cryptic, observational, intelligence-framing
  - Diplomat: measured, consensus-building, stability-focused
  - Saboteur: provocative, chaos-embracing
  - Whale: deliberate, conviction-driven
  - Degen: impulsive, colourful, YOLO-framing
- Fallback: if Mistral API unavailable, returns generic template string

> Sources: echelon_cycle_013.md:222-236

### 4.8 T3 Deep Reasoning Engine

**File**: `backend/agents/deep_reasoning.py`

Complex multi-step reasoning for escalated decisions:
- Input: full context (T0Context + T1 signals + market history + evidence chain)
- Output: `T3Decision` (action, reasoning_summary, evidence_refs, decision_trace, confidence)
- Model: Sonnet 4.5 / Opus (API, routed via ADK)
- Triggered ONLY when:
  - T1 confidence < novelty_threshold
  - Cross-theatre correlation detected
  - Paradox anomaly under investigation
  - Novel market conditions (no matching T1 pattern)
- Cost-bounded: max T3 calls per agent per tick = 1, max per agent per day = configurable
- Fallback: if API unavailable or rate-limited, router falls back to T1Decision with low-confidence flag

> Sources: echelon_cycle_013.md:237-245

### 4.9 Novelty Threshold Router

**File**: `backend/agents/decision_router.py`

Routes decisions through the tier stack:
1. Always compile T0 (free)
2. Always run T1 (fast, local)
3. If T1.confidence >= novelty_threshold → use T1Decision, optionally run T2 for expression
4. If T1.confidence < novelty_threshold → escalate to T3, use T3Decision
5. If T3 is rate-limited → fall back to T1Decision with low-confidence flag

The router is System Bible §IX.3's "Novelty Threshold Routing" made concrete.

> Sources: echelon_cycle_013.md:246-256

### 4.10 Model Providers

Three model provider modules with health check and graceful fallback:

**File**: `backend/agents/model_providers/ollama_provider.py`
- Wraps Ollama's local API for Qwen 3.5 4B/9B
- Structured output mode (JSON schema enforcement)
- Health check: verify Ollama running and model loaded
- Fallback: T1 degrades to pure rules engine
- `@pytest.mark.requires_ollama` for live tests

**File**: `backend/agents/model_providers/mistral_provider.py`
- Wraps Mistral API for creative generation
- Prompt templates per archetype
- Fallback: generic template string (decision still executes)

**File**: `backend/agents/model_providers/anthropic_provider.py`
- Wraps Anthropic API for deep reasoning (Sonnet 4.5 / Opus)
- Structured output: reasoning_summary, evidence_refs, decision_trace
- Rate limiting: configurable max calls per agent per day
- Fallback: router falls back to T1

> Sources: echelon_cycle_013.md:257-283

### 4.11 ADK Agent Wrapper

**File**: `backend/agents/adk/echelon_agent.py`

Wraps the T0/T1/T2/T3 pipeline as a Google ADK agent:
- ADK agent lifecycle: initialise → subscribe to heartbeat → execute decision loop → settle
- Tool bindings: `echelon_status` (market state), `echelon_verify` (certificate check), `execute_trade` (LMSR)
- State management: T0Context persisted between ticks, decision history accumulated
- A2A registration: agent discoverable (coordination deferred to post-013)

**File**: `backend/agents/adk/shark_v1.py`

First autonomous agent — MEGALODON variant:
- Genome: ρ=0.90, ε=0.80, L=15000, novelty_threshold=0.6
- T1 rules: momentum-based (buy on price increase, take profit on target, stop-loss on drawdown)
- T2 personality: confident, terse, momentum-focused
- T3 triggers: novel evidence, cross-market correlation, Paradox proximity
- Success metric: ≥20 trades over 50 ticks, respects risk limits, outperforms lower-skill archetype
- Flakiness fallback: if P&L comparison is non-deterministic, use calibration-based metric (Brier score / log score)

**Test framework**: `FakeADKRunner` executes the agent's decision loop synchronously, bypassing the ADK event system. Sprint 1–2 tests use `FakeADKRunner`. Sprint 3 adds `@pytest.mark.requires_adk` for live ADK tests.

> Sources: echelon_cycle_013.md:305-320

### 4.12 Agent ↔ Theatre Bridge

**File**: `backend/services/agent_theatre_bridge.py`

Replaces 012's stub agents with autonomous agents in the Sponsored Theatre lifecycle:
- Spawns agent instances for a Theatre, wires into heartbeat
- Agent instances receive market state and evidence on each heartbeat tick
- Decision traces feed into RLMF export
- Collects P&L at settlement
- Compatible with 012's stub agent interface — existing E2E test should pass with autonomous agents substituted

> Sources: echelon_cycle_013.md:323-328

### 4.13 Multi-Agent Population

Spawn all 6 archetypes (one each) in a Theatre:
- Each agent uses its archetype's genome parameters from the Behaviour Matrix
- Agents trade independently (no A2A coordination in 013)
- Market dynamics emerge from heterogeneous strategies interacting via LMSR
- Validate: Shark trades frequently (momentum), Spy trades on evidence, Diplomat stabilises, Saboteur disrupts, Whale makes large positions, Degen trades randomly

> Sources: echelon_cycle_013.md:329-335

### 4.14 P&L Aggregation

Wire agent instance P&L back to Identity:
- Each instance reports: trades executed, final position, realised P&L, unrealised P&L at settlement
- Identity aggregates across all instances (multiple Theatres)
- P&L stored in agent Identity record

> Sources: echelon_cycle_013.md:336-341

---

## 5. What Previous Cycles Deliver (Consumed by This Cycle)

### 5.1 LMSR Market Engine (Cycle-010a)

| Module | What It Does |
|--------|-------------|
| `lmsr.py` | Pure cost function: C(x) = b · ln(Σ exp(xⱼ / b)), prices, trade cost |
| `state.py` | MarketPhase enum, FeeSchedule, MarketState container |
| `lifecycle.py` | Forward-only phase transitions, `create_market()` factory |
| `trading.py` | `TradingEngine.execute_trade()` — atomic execution |
| `positions.py` | In-memory position tracking: AgentPosition |
| `resolution.py` | Deterministic settlement: AgentSettlement, SettlementReport |
| `commitment.py` | SHA-256 commitment hash over Echelon Canonical JSON v0 |

### 5.2 Engines + Heartbeat (Cycle-010b)

- Butterfly Engine: wing flaps, stability impact
- Paradox Engine: Logic Gap scanning, RealitySignalProvider interface
- Entropy Engine: temporal stability decay
- Heartbeat scheduler: AGENT 5s → MARKET 10s → PARADOX 30s → ENTROPY 60s

### 5.3 WorldMonitor OSINT Pipeline (Cycle-011)

- LiveOSINTRealityProvider wired to Paradox Engine
- Three WM domain endpoints: CII, market snapshot, maritime anomaly
- Evidence bundle collection with HTTP transcript receipts
- Mock-only testing with JSON fixtures

### 5.4 Sponsored Theatre E2E (Cycle-012)

- SponsoredTheatreConfig + SponsorReviewPackage
- MarketTheatreBridge (LMSR ↔ Theatre facade)
- StubAgents (6 archetypes — the interface 013 must satisfy)
- Theatre evidence collection, resolution engine, certificate pipeline
- RLMF export v2.0.1, sponsor delivery package
- echelon_status integration

### 5.5 Existing Agent Infrastructure

| Component | Location | 013 Usage |
|-----------|----------|-----------|
| Agent schemas | `backend/agents/schemas.py` | Genome model as T0 context source |
| Autonomous agent | `backend/agents/autonomous_agent.py` | Soul (genome personality) concept → T0 |
| Multi-brain | `backend/agents/brain.py` | Provider routing pattern → T1/T2/T3 routing |
| Skills bridge | `backend/agents/agent_skills_bridge.py` | Archetype decision profiles |
| Instance manager | `backend/agents/instance_manager.py` | Instance lifecycle pattern |
| Shark strategies | `backend/agents/shark_strategies.py` | T1 rule templates for Shark |

**Key constraint**: No modifications to `backend/market/` modules, `backend/engines/` modules, `backend/osint/` modules, or `backend/services/` modules (012 code). All new code in `backend/agents/` and `backend/services/agent_theatre_bridge.py`.

> Sources: echelon_cycle_013.md:68-91

---

## 6. Testing Strategy

### 6.1 Mock-Only Model Providers

All Sprint 1–2 tests use mocked model providers. No live LLM calls in the default test suite.
- `@pytest.mark.requires_ollama` — tests needing Ollama running locally
- `@pytest.mark.requires_mistral` — tests needing Mistral API key
- `@pytest.mark.requires_anthropic` — tests needing Anthropic API key
- `@pytest.mark.requires_adk` — tests needing Google ADK runner

### 6.2 FakeADKRunner

Sprint 1–2 tests use a `FakeADKRunner` that executes the agent's decision loop synchronously, bypassing the ADK event system. Sprint 3 introduces real ADK runner tests.

### 6.3 Deterministic E2E

Evidence injections, initial balances, and RNG seeds are fixed. E2E test results must be deterministic across runs.

### 6.4 Scoped Regression

```
python3 -m pytest backend/market/ backend/engines/ backend/scoring/ backend/osint/ backend/services/ -v
```

Pre-existing `theatre/` collection errors excluded.

### 6.5 No ADK Imports in Sprint 1–2

The T0/T1/T2/T3 pipeline must be testable and functional without the ADK dependency. Sprint 3 introduces ADK imports only.

---

## 7. Non-Functional Requirements

### 7.1 Cost Efficiency

- 90%+ decisions at T1 (<$0.01/day per agent)
- T2 runs only for externally visible output
- T3 rate-limited: configurable max calls per agent per day
- Total estimated cost: ~$2.10/day for 6 agents (directional, validated in Sprint 3)

### 7.2 Latency

| Tier | Target Latency |
|------|---------------|
| T0 | 0ms (data transformation) |
| T1-RULES | <1ms (parameterised logic) |
| T1-LOCAL-LLM | <100ms (Ollama, local) |
| T2 | 200–500ms (Mistral API) |
| T3 | 1–5s (Anthropic API) |

### 7.3 Graceful Degradation

- Ollama down → T1 degrades to T1-RULES (no NLP, still functional)
- Mistral down → T2 returns generic template (decision unaffected)
- Anthropic down → T3 unavailable, router falls back to T1 with low-confidence flag
- ADK down → FakeADKRunner provides synchronous fallback for testing

### 7.4 State Isolation

- Each agent instance has its own T0Context, decision history, and position state
- No cross-agent state sharing (A2A coordination deferred)
- Instance state scoped to Theatre lifetime

### 7.5 Auditability

- Every decision produces a DecisionTrace conforming to §4.4
- T0Context hash enables reproducibility verification
- Decision traces feed RLMF export (schema v2.0.1)
- Genome version pin for auditability

### 7.6 Python 3.9.6 Compatibility

`from __future__ import annotations` required in every new file for PEP 604 union syntax.

---

## 8. Scope Exclusions

- **No A2A inter-agent coordination.** Agents trade independently. Diplomat coalitions, Spy intelligence sharing deferred to post-013.
- **No agent breeding/genealogy.** Agent genomes are static. Evolutionary parameter adaptation is future work.
- **No on-chain identity.** ERC-721 agent NFTs and ERC-6551 wallets deferred. Identity is a database record.
- **No T1 fine-tuning.** Qwen 3.5 runs off-the-shelf via Ollama. Fine-tuning on Echelon-specific data is future work.
- **No multi-Theatre agent deployment E2E.** Architecture supports it, but acceptance tests use single Theatre only.
- **No WorldMonitor deployment.** All evidence uses mock fixtures from Cycle-011.
- **No on-chain anchoring.** MockSepoliaClient returns deterministic "local_mode" transaction hashes.
- **No modifications to existing modules.** `backend/market/`, `backend/engines/`, `backend/osint/`, `backend/services/` (012 code) are frozen.
- **No T1.5 sub-tier.** Qwen 3.5 0.8B exploration noted in roadmap but not scoped for 013.

> Sources: echelon_cycle_013.md:425-432

---

## 9. Acceptance Criteria

### 9a. Sprint 1 — T0 Context Compiler + T1 Rules Engine

- [ ] AgentGenome captures all 8 archetype parameters + variant modifiers + Theatre context + position constraints + decision routing config + genome version
- [ ] Factory functions produce correct default genomes for all 6 archetypes from the Behaviour Matrix
- [ ] T0 Context Compiler produces deterministic T0Context from genome + TheatreTemplate + MarketState
- [ ] T0Context hash (SHA-256) enables reproducibility verification
- [ ] T1 Rules Engine produces valid T1Decision for all 6 archetypes
- [ ] Per-archetype decision logic is parameterised by genome parameters (not hard-coded)
- [ ] Confidence scoring: decisions near thresholds flag for T3 escalation
- [ ] DecisionTrace schema validates all required fields (tick_id, agent_id, tier_used, pattern_name, options_considered, reasoning_summary, evidence_refs)
- [ ] Every archetype decision path produces a valid DecisionTrace with pattern_name and options_considered populated
- [ ] Agent instance lifecycle completes: spawn → 10 ticks → settle with correct P&L
- [ ] Agent ↔ LMSR integration: TradeIntent validated against position limits, executed via TradingEngine.execute_trade()
- [ ] Decision traces conform to RLMF schema v2.0.1
- [ ] No modifications to `backend/market/`, `backend/engines/`, `backend/osint/`, `backend/services/`
- [ ] Scoped regression: all tests pass
- [ ] 25+ new Sprint 1 tests pass

### 9b. Sprint 2 — T2 Personality + T3 Deep Reasoning + Routing

- [ ] T2 produces personality-flavoured output for all 6 archetypes
- [ ] T2 never overrides T1's action (expression only, verified by test)
- [ ] T3 produces structured reasoning (reasoning_summary + evidence_refs + decision_trace) for escalated decisions
- [ ] Router correctly routes: high-confidence T1 → use T1Decision; low-confidence → escalate to T3
- [ ] Ollama provider connects to local Qwen 3.5 4B/9B with structured output
- [ ] Ollama fallback: T1 degrades to T1-RULES when Ollama unavailable
- [ ] Mistral provider generates archetype-specific personality output
- [ ] Mistral fallback: generic template when API unavailable
- [ ] Anthropic provider generates deep reasoning output
- [ ] T3 rate limiting enforced (max calls per agent per day)
- [ ] Anthropic fallback: router falls back to T1 when API unavailable or rate-limited
- [ ] Decision traces record correct `tier_used` ("T1-RULES", "T1-LOCAL-LLM", "T3")
- [ ] No modifications to `backend/market/`, `backend/engines/`, `backend/osint/`, `backend/services/`
- [ ] Scoped regression: all tests pass
- [ ] 25+ new Sprint 2 tests pass (mocked providers)

### 9c. Sprint 3 — First Autonomous Agent + ADK Integration + Theatre Wiring

- [ ] ADK Agent wrapper initialises, subscribes to heartbeat, executes decision loop, settles
- [ ] Tool bindings work: echelon_status, echelon_verify, execute_trade
- [ ] Shark agent (MEGALODON) executes ≥20 trades over 50 ticks
- [ ] Shark respects all risk limits (position, drawdown, stop-loss)
- [ ] Shark outperforms at least one lower-skill archetype (Degen or Saboteur) OR Shark's calibration metric (Brier/log score) exceeds baseline
- [ ] All 6 archetypes demonstrate distinct trading behaviour in multi-agent test
- [ ] Shark trades most frequently, Whale trades least frequently (patience parameter)
- [ ] T3 escalation triggers on evidence injection (at least one in E2E)
- [ ] Agent ↔ Theatre bridge spawns instances, wires heartbeat, collects P&L at settlement
- [ ] Decision traces feed RLMF export (schema v2.0.1)
- [ ] P&L aggregates correctly from instances to identity
- [ ] E2E test: full Companies House Theatre lifecycle with autonomous agents — creation → commitment → trading (6 agents, 50 ticks) → evidence injection (mock WM at ticks 10, 20, 35) → resolution → settlement → certificate (21 checks) → RLMF → delivery
- [ ] E2E results are deterministic (fixed seeds, fixtures, balances)
- [ ] Certificate passes all 21 verifier checks
- [ ] Compatible with 012's E2E test infrastructure
- [ ] No modifications to `backend/market/`, `backend/engines/`, `backend/osint/`, `backend/services/`
- [ ] Scoped regression: all tests pass
- [ ] 25+ new Sprint 3 tests pass

> Sources: echelon_cycle_013.md:201-367

---

## 10. Sprint Architecture

### Sprint 1 — T0 Context Compiler + T1 Rules Engine

```
backend/
├── agents/
│   ├── genome.py                     # AgentGenome model (extend existing)
│   ├── context_compiler.py           # T0 Context Compiler
│   ├── decision_trace.py             # DecisionTrace schema (BEAUVOIR binding)
│   ├── rules_engine.py               # T1 Rules Engine
│   ├── agent_instance.py             # Agent Instance lifecycle
│   └── tests/
│       ├── test_context_compiler.py  # T0 context tests
│       ├── test_rules_engine.py      # T1 rules engine tests
│       ├── test_agent_instance.py    # Instance lifecycle tests
│       └── test_decision_trace.py    # DecisionTrace schema tests
```

### Sprint 2 — T2 Personality + T3 Deep Reasoning + Routing

```
backend/
├── agents/
│   ├── personality_engine.py         # T2 Personality Engine
│   ├── deep_reasoning.py             # T3 Deep Reasoning Engine
│   ├── decision_router.py            # Novelty Threshold Router
│   ├── model_providers/
│   │   ├── __init__.py
│   │   ├── ollama_provider.py        # Qwen 3.5 via Ollama (T1)
│   │   ├── mistral_provider.py       # Mistral creative (T2)
│   │   └── anthropic_provider.py     # Sonnet/Opus (T3)
│   └── tests/
│       ├── test_personality_engine.py
│       ├── test_deep_reasoning.py
│       ├── test_decision_router.py
│       └── test_model_providers.py
```

### Sprint 3 — First Autonomous Agent + ADK + Theatre Wiring

```
backend/
├── agents/
│   ├── adk/
│   │   ├── __init__.py
│   │   ├── echelon_agent.py          # ADK Agent wrapper
│   │   └── shark_v1.py               # First autonomous Shark agent
│   └── tests/
│       ├── test_adk_agent.py
│       ├── test_agent_theatre_bridge.py
│       ├── test_multi_agent.py
│       └── test_autonomous_e2e.py
├── services/
│   └── agent_theatre_bridge.py       # Agent ↔ Theatre integration
```

---

## 11. Sprint Task Breakdown

### Sprint 1 Tasks (7 tasks)

1. **AgentGenome model** — Pydantic v2 model with 8 archetype parameters, variant modifiers, Theatre context, position constraints, decision routing, genome version. Factory functions for all 6 archetypes.
2. **T0 Context Compiler** — Compile genome + TheatreTemplate + MarketState into frozen T0Context. SHA-256 hash for reproducibility.
3. **T1 Rules Engine** — Parameterised decision engine with per-archetype logic. Confidence scoring. T3 escalation flagging.
4. **DecisionTrace schema** — Pydantic v2 model with all BEAUVOIR-required fields. Schema version pin. RLMF compatibility.
5. **Agent Instance lifecycle** — spawn → tick → settle. Multiple instances per Identity. P&L aggregation.
6. **Agent ↔ LMSR integration** — Wire agent tick() output to TradingEngine. Position limit validation. Decision trace recording.
7. **Sprint 1 tests** — test_context_compiler.py, test_rules_engine.py, test_agent_instance.py, test_decision_trace.py. 25+ tests.

### Sprint 2 Tasks (7 tasks)

1. **T2 Personality Engine** — Mistral-powered expression per archetype. Non-interference with T1 decisions. Fallback to generic template.
2. **T3 Deep Reasoning Engine** — Sonnet/Opus-powered deep analysis. Structured output. Rate limiting. Cost bounding.
3. **Novelty Threshold Router** — Decision routing logic. T1→T3 escalation. Rate limit fallback. Tier recording in traces.
4. **Ollama provider** — Qwen 3.5 4B/9B via Ollama local API. Health check. Structured output. T1-RULES fallback.
5. **Mistral provider** — Mistral creative API wrapper. Archetype prompt templates. Fallback to generic.
6. **Anthropic provider** — Sonnet/Opus API wrapper. Rate limiting. Structured output. Fallback to T1.
7. **Sprint 2 tests** — test_personality_engine.py, test_deep_reasoning.py, test_decision_router.py, test_model_providers.py. 25+ tests (mocked providers).

### Sprint 3 Tasks (7 tasks)

1. **ADK Agent wrapper** — Google ADK lifecycle, tool bindings (echelon_status, echelon_verify, execute_trade), state management, heartbeat subscription.
2. **First Shark agent (MEGALODON)** — Complete autonomous agent with T0/T1/T2/T3 pipeline. ≥20 trades, risk limits, outperformance metric.
3. **Agent ↔ Theatre bridge** — Spawns instances, wires heartbeat, collects P&L. Replaces 012 stub agents. Compatible interface.
4. **Multi-agent population** — 6 archetypes trading simultaneously. Heterogeneous behaviour validation.
5. **P&L aggregation** — Instance → Identity aggregation. Cross-Theatre accumulation.
6. **Autonomous agent E2E test** — Companies House Theatre with 6 autonomous agents, 50 ticks, mock evidence at ticks 10/20/35. Deterministic. Certificate 21 checks. RLMF export.
7. **Sprint 3 tests** — test_adk_agent.py, test_agent_theatre_bridge.py, test_multi_agent.py. 25+ tests.

---

## 12. Dependency Chain

```
Cycle-010a (LMSR cost function, market lifecycle)
  → Cycle-010b (Butterfly, Paradox, Entropy, Heartbeat, VRF)
    → Cycle-011 (WorldMonitor — live evidence pipeline + convergence)
      → Cycle-012 (Sponsored Theatre E2E — stub agents define interface)
        → Cycle-013 (Agent Runtime — T0/T1/T2/T3 + ADK)  ← THIS CYCLE
          → Cycle-014 (Bounded Inquiry Markets)
            → Cycle-015 (WM Live + Non-WM Collector)
```

> Sources: echelon_platform_roadmap.md:194-209

---

## 13. BEAUVOIR Principle: Agent-First Citizenship

The BEAUVOIR review guidelines establish patterns that translate directly to agent system prompts:

1. **Structured identity definition** — each archetype has a parameterised behavioural specification injected as T0 context. Not inferred, deterministic, auditable.
2. **Evaluation dimensions** — agents assess markets along named dimensions (evidence quality, price momentum, stability, risk exposure).
3. **Decision trajectory logging** — every decision produces a structured trace: input state, considered options, selected action, confidence score, escalation trigger.
4. **Named patterns** — trade strategies reference named patterns from the archetype matrix. Future agents following the decision log can reconstruct reasoning.
5. **Severity calibration** — T1→T3 escalation threshold functions like severity levels: routine (T1), concerning (may trigger T3), critical (always escalates).

> Sources: echelon_cycle_013.md:47-54

---

## 14. AGPL Compliance

| Dependency | Licence | AGPL Compatible |
|------------|---------|-----------------|
| Qwen 3.5 | Apache 2.0 | Yes |
| Ollama | MIT | Yes |
| Mistral (open weights) | Apache 2.0 | Yes |
| Google ADK | Apache 2.0 | Yes |
| Anthropic SDK | MIT | Yes |

No proprietary model weights committed to the repository — loaded at runtime via provider APIs.

> Sources: echelon_cycle_013.md:477-479

---

## 15. What 013 Unlocks

- **Autonomous market participants** — infrastructure from 010-012 now has agents that actually decide to trade
- **RLMF data production** — agent decision traces at every tick produce the training data that's the commercial product
- **Heterogeneous market dynamics** — 6 archetypes with distinct strategies create realistic market behaviour
- **Foundation for 014 (Bounded Inquiry Markets)** — agents can participate in investigation, inspection, and scrutiny markets
- **T1 local inference** — Qwen 3.5 on Apple Silicon proves the self-hosted model tier works, zero API dependency for routine decisions

> Sources: echelon_cycle_013.md:455-462

---

## 16. Key Spec References

| Document | Relevance |
|----------|-----------|
| `echelon_cycle_013.md` | Primary context document for this cycle |
| `echelon_platform_roadmap.md` | Roadmap positioning and dependency graph |
| Echelon System Bible v13 §VIII | Agent archetypes, 6 core types, Identity vs Instance |
| Echelon System Bible v13 §IX | Hierarchical Brain, three-tier intelligence, novelty threshold |
| Four-Tier Agent Brain Proposal | T0/T1/T2/T3 extension of §IX |
| RLMF schema v2.0.1 | Training data export format, decision trace compatibility |
| Certificate schema v1.0.0 | 21 verifier checks, calibration certificate |
| BEAUVOIR Review Guidelines | Agent-first citizenship patterns |
| Google ADK Python SDK | Agent execution framework |
| Archetype Behaviour Matrix v1.0 | 8 quantitative parameters per archetype |
