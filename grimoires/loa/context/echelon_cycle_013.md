# Cycle-013 — Agent Runtime (T0/T1/T2/T3 + ADK)

**Cycle:** cycle-013
**Name:** Agent Runtime — Four-Tier Hierarchical Intelligence
**Predecessor:** cycle-012 (Sponsored Theatre E2E — proves infrastructure, defines agent interface via stubs)
**Location:** `~/Developer/prediction-market-monorepo.nosync`
**Sprint count:** 3
**Tooling:** Claude Code + Loa (`/plan` → `/simstim` → `/run-bridge`)

---

## Cycle Objective

Build the core agent execution loop. This is the cycle that turns infrastructure into a living system. After 012, Echelon has complete markets with stub agents making scripted trades. After 013, Echelon has autonomous agents making real decisions through a four-tier intelligence hierarchy.

The four tiers:

| Tier | Name | Model Class | Role | Latency | Cost |
|------|------|------------|------|---------|------|
| T0 | Context | Config / genome / skills | Static context injection. No inference. Theatre config, committed parameters, archetype personality, position limits, risk appetite. The agent's "commitment hash" — deterministic, auditable, version-pinned. | 0ms | Free |
| T1 | Fast Reasoning | Qwen 3.5 4B–9B (self-hosted via Ollama) | Cheap structured decisions. Signal classification, evidence triage, threshold checks, simple decision trees. "Price moved >5% in my direction, take profit." | <100ms | ~$0 (local) |
| T2 | Creative / Personality | Mistral creative variant | Agent voice, narrative flavour, diplomatic vs aggressive framing, market commentary. The "how" of communication — not what to decide, but how to express it. | 200–500ms | Low |
| T3 | Deep Reasoning | Sonnet 4.5 / Opus (API) | Complex multi-step reasoning, cross-theatre analysis, anomaly investigation, strategic positioning. Used sparingly — only when T1 signals low confidence. | 1–5s | High |

**What success looks like:** one Shark agent trading autonomously in a local-mode LMSR market. The agent reads market state, evaluates evidence, makes a trade decision via T0+T1, expresses it via T2, and escalates to T3 only when novelty threshold is breached. P&L aggregates back to agent identity.

---

## Architectural Foundations

### System Bible v13 §VIII–IX Reference

The System Bible v13 defines:
- **§VIII Agent Architecture:** 6 core archetypes (Shark, Spy, Diplomat, Saboteur, Whale, Degen), 12 genesis agents (2 per archetype), Identity (persistent, NFT) vs Instance (ephemeral, per-market worker), ERC-8004 Agent Passport, 4-layer protocol stack (Identity → Coordination → Governance → Settlement).
- **§IX Hierarchical Brain:** Three-tier intelligence (Layer 1 heuristic → Layer 1.5 personality → Layer 2 narrative LLM). Novelty threshold routing. 90%+ decisions at Layer 1 (<10ms), 8-12% at Layer 1.5 (50-200ms), 2-5% at Layer 2 (1-5s).

### Four-Tier Extension (Ideas Expansion Proposal)

The Four-Tier Agent Brain Proposal extends §IX by splitting the middle tier:
- **T0 (Context)** was implicit in §VIII (genome, archetype parameters) but never separated as a distinct tier. Making it explicit means the agent's base parameters are zero-cost, deterministic, and auditable.
- **T1 (Fast Reasoning)** replaces §IX's Layer 1 heuristics with a small self-hosted model (Qwen 3.5 4B/9B). Gains: can parse natural language evidence, classify signals, and make nuanced threshold decisions that hand-written rules cannot. Runs locally via Ollama — no API cost, no data leaving the machine.
- **T2 (Creative)** is §IX's Layer 1.5 (Mistral personality) — unchanged in purpose, elevated to its own tier to make the separation explicit.
- **T3 (Deep Reasoning)** is §IX's Layer 2 (GPT-4o/Claude) — unchanged. Engaged only on novelty threshold breach.

### BEAUVOIR Patterns for Agent Design

The BEAUVOIR review guidelines (0xHoneyJar) establish agent-first citizenship patterns that translate directly to agent system prompts:

1. **Structured identity definition** — each archetype has a parameterised behavioural specification (ρ, ε, γ, ξ, L, σ, φ, π from the Archetype Behaviour Matrix) injected as T0 context.
2. **Evaluation dimensions** — agents assess markets along named dimensions (evidence quality, price momentum, stability, risk exposure) analogous to BEAUVOIR's review dimensions (security, quality, test coverage, operational readiness).
3. **Decision trajectory logging** — every T1/T3 decision produces a structured trace: input state, considered options, selected action, confidence score, escalation trigger (if any). Analogous to BEAUVOIR's "map decision trajectories" principle.
4. **Named patterns** — trade strategies reference named patterns from the archetype matrix (momentum exploitation, intel arbitrage, stability maintenance, chaos creation). Future agents following the decision log can reconstruct reasoning.
5. **Severity calibration** — the T1→T3 escalation threshold functions like BEAUVOIR's severity levels: routine decisions (Info) stay at T1, concerning signals (Medium/High) may trigger T3, critical anomalies (Critical) always escalate.

### Google ADK Framework

Agent runtime uses Google ADK (Agent Development Kit) **Python SDK** as the execution framework:
- **Language:** Python (matches existing `backend/` codebase). ADK's TypeScript SDK exists but introduces a language split — deferred.
- **Agent lifecycle:** ADK handles spawn, execution loop, tool invocation, state management
- **A2A protocol:** Agent-to-Agent discovery for inter-agent coordination (Diplomat coalitions, Spy intelligence sharing) — deferred to post-013
- **MCP tool surface:** Agents invoke `echelon_verify`, `echelon_status`, `echelon_hash` as tools
- **Model routing:** ADK's model configuration allows per-tier routing (T1 → Ollama endpoint, T2 → Mistral API, T3 → Anthropic API)
- **Test mocking:** A `FakeADKRunner` class executes the agent's decision loop synchronously, bypassing the ADK event system. All Sprint 1–2 tests use `FakeADKRunner`; Sprint 3 tests use the real ADK runner with `@pytest.mark.requires_adk`
- **Replaceability:** The ADK wrapper is a thin adapter. If the Python SDK proves insufficient, the T0/T1/T2/T3 pipeline is unaffected — only the wrapper changes.

---

## What Exists (Relevant to This Cycle)

### Existing Agent Infrastructure

| Component | Location | What It Has | What 013 Uses |
|-----------|----------|-------------|---------------|
| Agent schemas | `backend/agents/schemas.py` | AgentDomain, FinancialArchetype, genome structure | Genome model as T0 context source |
| Autonomous agent | `backend/agents/autonomous_agent.py` | ACP integration, Brain/Body/Soul architecture | Soul (genome personality) concept → T0 |
| Multi-brain | `backend/agents/brain.py` | Multi-provider routing (RULE_BASED, LOCAL_LLM, GROQ, OPENAI, ANTHROPIC, HYBRID) | Provider routing pattern → T1/T2/T3 routing |
| Skills bridge | `backend/agents/agent_skills_bridge.py` | Archetype → Skills System mapping | Archetype decision profiles |
| Instance manager | `backend/agents/instance_manager.py` | Identity vs Instance architecture, HD-derived wallets, P&L aggregation | Instance lifecycle pattern |
| Shark strategies | `backend/agents/shark_strategies.py` | Shark-specific trading rules | T1 rule templates for Shark archetype |
| Genealogy manager | `backend/agents/genealogy_manager.py` | Genetic breeding/evolution | Future — not used in 013 |

### Stub Agent Interface (from 012)

The stub agents in 012 define the interface that autonomous agents must satisfy:
- `agent_id: str` — unique identifier
- `archetype: str` — one of 6 core archetypes
- `balance: Decimal` — current trading balance
- `decide(market_state, evidence) → Optional[TradeIntent]` — the decision function
- `execute(trade_intent, trading_engine)` — submits trade to LMSR

013 replaces the stub's simple `decide()` function with the full T0/T1/T2/T3 pipeline.

### Archetype Behaviour Matrix (v1.0)

8 quantitative parameters per archetype:

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

These become the T0 context for each agent — injected as structured data, never inferred.

---

## Sprint 1 — T0 Context Compiler + T1 Rules Engine

### What It Is

The foundation: how agents receive their identity (T0) and make fast decisions (T1). By the end of Sprint 1, an agent can read market state, apply archetype-specific rules, and produce a trade decision without any LLM call.

**T1 sub-tier naming convention:** In Sprint 1, T1 operates as **T1-RULES** — pure parameterised logic, no inference. In Sprint 2, Ollama integration adds **T1-LOCAL-LLM** (Qwen 3.5 via Ollama) with automatic fallback to T1-RULES if Ollama is unavailable. Decision traces record `tier_used` as `"T1-RULES"` or `"T1-LOCAL-LLM"` to distinguish the sub-modes in RLMF exports.

### Sprint 1 Tasks

**1. AgentGenome model**
`backend/agents/genome.py` (extend existing) — Pydantic v2 model capturing the complete T0 context:
- Archetype parameters (ρ, ε, γ, ξ, L, σ, φ, π)
- Variant modifiers (e.g., MEGALODON overrides for ρ, ε, L)
- Theatre-specific context: committed sources, outcome labels, resolution date, LMSR `b`
- Position constraints: max_position_pct, max_drawdown_pct, stop_loss_threshold
- Decision routing: novelty_threshold (confidence below this → escalate to T3)
- Version pin: genome_version for auditability

**2. T0 Context Compiler**
`backend/agents/context_compiler.py` — compiles AgentGenome + Theatre config into a structured T0 context injection:
- Input: AgentGenome + TheatreTemplate + current MarketState
- Output: T0Context (frozen dataclass) containing:
  - Archetype parameters (from genome)
  - Market context (prices, phase, evidence coverage)
  - Position state (current shares, net_cashflow, available balance)
  - Theatre rules (committed sources, resolution date, fee schedule)
  - Constraints (position limits, risk budgets)
- The T0Context is the agent's "view of the world" — everything it needs to decide, computed deterministically with zero inference cost.

**3. T1 Rules Engine**
`backend/agents/rules_engine.py` — parameterised decision engine driven by T0 context:
- Input: T0Context
- Output: T1Decision (action, confidence, reasoning_trace)
- Actions: BUY(outcome, shares), SELL(outcome, shares), HOLD, SHIELD, SABOTAGE
- Decision logic per archetype (parameterised, not hard-coded):
  - Shark: momentum check → if leading outcome price increased >ρ×threshold, BUY. If position profit >γ×target, SELL (take profit).
  - Spy: evidence check → if new evidence arrived since last tick AND evidence_sensitivity > ε_threshold, evaluate signal and trade.
  - Diplomat: stability check → if market spread > (1-φ)×max_spread, buy trailing outcome to stabilise.
  - Saboteur: disruption check → if stability < (1-σ)×threshold, random contrary trade.
  - Whale: conviction check → if evidence strongly favours one outcome AND position < L×conviction_pct, large buy.
  - Degen: random action weighted by exploration_rate ξ.
- Each decision carries a confidence score (0.0–1.0).
- If confidence < novelty_threshold (from genome) → flag for T3 escalation.

**4. DecisionTrace schema + logging (BEAUVOIR binding)**
`backend/agents/decision_trace.py` — Pydantic v2 model defining the stable decision log schema. Every T1 (and T3) decision produces a trace conforming to this schema. This is the concrete artefact that satisfies BEAUVOIR's agent-first citizenship requirements: "document reasoning, map trajectories, name patterns."

Required fields (stable keys — must not change between agent versions):
- `tick_id: str`, `agent_id: str`, `theatre_id: str`, `timestamp: datetime`
- `tier_used: Literal["T1-RULES", "T1-LOCAL-LLM", "T3"]` — which tier/sub-tier produced the decision
- `market_state_snapshot: dict` (prices, phase, evidence_coverage_pct)
- `evidence_state: dict` (last_evidence_ts, new_evidence_flag, source_ids_cited)
- `t0_context_hash: str` (SHA-256 of T0Context — enables reproducibility)
- `action: str` (BUY/SELL/HOLD/SHIELD/SABOTAGE + parameters)
- `confidence: float` (0.0–1.0)
- `pattern_name: str` — named pattern from archetype matrix (e.g., "momentum_exploitation", "stability_maintenance", "intel_arbitrage", "chaos_creation", "conviction_accumulation", "random_exploration"). Required — every decision must map to a named pattern.
- `options_considered: list[dict]` — what alternatives were evaluated (action, estimated value, rejection reason). Satisfies BEAUVOIR's "map decision trajectories" — captures what was considered and why selected.
- `reasoning_summary: str` — human-readable explanation of why this action was chosen
- `escalated_to_t3: bool`
- `evidence_refs: list[str]` — source IDs or bundle IDs cited in the decision (empty list if none)

Stored in decision log for RLMF export. Schema version-pinned in trace header.

**Determinism note:** `timestamp` is observational only and must not be included in any commitment hash or reproducibility check. Reproducibility is determined by `t0_context_hash` + `market_state_snapshot` + `evidence_state` — the timestamp records when the decision was made, not what it was.

**5. Agent Instance lifecycle**
`backend/agents/agent_instance.py` — ephemeral agent instance bound to a Theatre:
- `spawn(identity_genome, theatre_id)` → creates instance with T0 context
- `tick(market_state, evidence)` → runs T0 compiler → T1 rules engine → returns action
- `settle(settlement_report)` → records final P&L, closes instance
- Instance inherits genome from Identity, operates for the Theatre's lifetime
- Multiple instances per Identity (one per Theatre)
- P&L aggregates back to Identity

**6. Agent ↔ LMSR integration**
Wire agent instances into the LMSR trading engine (replacing 012's stub agents):
- Agent's `tick()` produces a `TradeIntent`
- TradeIntent validated against position limits (T0 constraints)
- `TradingEngine.execute_trade()` called if valid
- Position updated in PositionManager
- Decision trace recorded

**7. Sprint 1 tests**
- `backend/agents/tests/test_context_compiler.py` — T0 context compilation, deterministic output, version pinning
- `backend/agents/tests/test_rules_engine.py` — per-archetype T1 decision correctness, confidence scoring, escalation flagging
- `backend/agents/tests/test_agent_instance.py` — lifecycle (spawn → tick → settle), P&L aggregation, multi-instance per identity
- `backend/agents/tests/test_decision_trace.py` — DecisionTrace schema validation, trace completeness per archetype (every decision path produces a valid trace with pattern_name, options_considered, reasoning_summary), RLMF schema conformance, reproducibility from t0_context_hash, evidence_refs populated when evidence is present

### Sprint 1 Success Criteria

- [ ] AgentGenome captures all 8 archetype parameters + variant modifiers + Theatre context
- [ ] T0 Context Compiler produces deterministic T0Context from genome + market state
- [ ] T1 Rules Engine produces valid decisions for all 6 archetypes
- [ ] Confidence scoring works — decisions near thresholds flag for T3 escalation
- [ ] Agent instance lifecycle completes: spawn → 10 ticks → settle with correct P&L
- [ ] Every archetype decision path produces a valid DecisionTrace with pattern_name, options_considered, and reasoning_summary populated
- [ ] Decision traces conform to RLMF schema
- [ ] All new tests pass, zero regression

---

## Sprint 2 — T2 Personality + T3 Deep Reasoning + Routing

### What It Is

The intelligence tiers that require inference. T2 adds personality and expression. T3 adds deep reasoning for complex decisions. The novelty threshold router decides which tier handles each decision.

### Sprint 2 Tasks

**1. T2 Personality Engine**
`backend/agents/personality_engine.py`:
- Input: T1Decision + AgentGenome (personality profile)
- Output: T2Output (coloured_rationale, market_commentary, diplomatic_message)
- Model: Mistral creative variant (API or self-hosted)
- T2 is NOT in the decision path — it never overrides T1's action
- T2 runs only when the decision produces externally visible output (trade log, market report, A2A message)
- Prompt template per archetype:
  - Shark: confident, terse, momentum-focused
  - Spy: cryptic, observational, intelligence-framing
  - Diplomat: measured, consensus-building, stability-focused
  - Saboteur: provocative, chaos-embracing
  - Whale: deliberate, conviction-driven
  - Degen: impulsive, colourful, YOLO-framing

**2. T3 Deep Reasoning Engine**
`backend/agents/deep_reasoning.py`:
- Input: full context (T0Context + T1 signals + market history + evidence chain)
- Output: T3Decision (action, reasoning_summary, evidence_refs, decision_trace, confidence)
- Model: Sonnet 4.5 / Opus (API, routed via ADK)
- Triggered ONLY when: T1 confidence < novelty_threshold OR cross-theatre correlation detected OR Paradox anomaly under investigation OR novel market conditions (no matching T1 pattern)
- Results cached: T3 decisions produce new T1 patterns (the "learning" path)
- Cost-bounded: max T3 calls per agent per tick = 1, max per agent per day = configurable

**3. Novelty Threshold Router**
`backend/agents/decision_router.py`:
- Input: T0Context + T1Decision
- Logic:
  1. Always compile T0 (free)
  2. Always run T1 (fast, local)
  3. If T1.confidence >= novelty_threshold → use T1Decision, optionally run T2 for expression
  4. If T1.confidence < novelty_threshold → escalate to T3, use T3Decision
  5. If T3 is rate-limited → fall back to T1Decision with low-confidence flag
- The router is the "Novelty Threshold Routing" from System Bible §IX.3, made concrete.

**4. Ollama integration for T1**
`backend/agents/model_providers/ollama_provider.py`:
- Wraps Ollama's local API for Qwen 3.5 4B/9B
- Structured output mode (JSON schema enforcement)
- Health check: verify Ollama is running and model is loaded
- Fallback: if Ollama is down, T1 degrades to pure rules engine (no NLP capability, but still functional)
- `@pytest.mark.requires_ollama` for tests that need the model running

**5. Mistral integration for T2**
`backend/agents/model_providers/mistral_provider.py`:
- Wraps Mistral API for creative generation
- Prompt templates per archetype
- Fallback: if Mistral API is unavailable, T2 returns a generic template string (decision still executes, just without personality)

**6. Anthropic integration for T3**
`backend/agents/model_providers/anthropic_provider.py`:
- Wraps Anthropic API for deep reasoning (Sonnet 4.5 / Opus)
- Structured output: reasoning_summary (human-readable), evidence_refs (source IDs cited), decision_trace (structured steps)
- Rate limiting: configurable max calls per agent per day
- Fallback: if API is unavailable or rate-limited, router falls back to T1

**7. Sprint 2 tests**
- `backend/agents/tests/test_personality_engine.py` — T2 output per archetype, non-interference with T1 decisions
- `backend/agents/tests/test_deep_reasoning.py` — T3 decision quality, reasoning_summary + evidence_refs + decision_trace structure, caching
- `backend/agents/tests/test_decision_router.py` — routing logic (confidence threshold, escalation, rate limiting, fallback)
- `backend/agents/tests/test_model_providers.py` — Ollama health check, Mistral fallback, Anthropic rate limiting
- Note: model provider tests use mocks by default. `@pytest.mark.requires_ollama`, `@pytest.mark.requires_mistral`, `@pytest.mark.requires_anthropic` for live integration tests.

### Sprint 2 Success Criteria

- [ ] T2 produces personality-flavoured output for all 6 archetypes
- [ ] T3 produces structured reasoning (reasoning_summary + evidence_refs + decision_trace) for escalated decisions
- [ ] Router correctly routes: high-confidence → T1 only, low-confidence → T3 escalation
- [ ] Ollama provider connects to local Qwen 3.5 4B/9B
- [ ] All providers have graceful fallback when unavailable
- [ ] T3 rate limiting enforced
- [ ] All new tests pass (mocked providers), zero regression

---

## Sprint 3 — First Autonomous Agent + ADK Integration + Theatre Wiring

### What It Is

The integration sprint. One Shark agent trades autonomously in a local-mode LMSR market, using the full T0/T1/T2/T3 pipeline. Google ADK provides the execution framework. The agent participates in a Sponsored Theatre (from 012) and produces RLMF data.

### Sprint 3 Tasks

**1. ADK Agent wrapper**
`backend/agents/adk/echelon_agent.py` — wraps the T0/T1/T2/T3 pipeline as a Google ADK agent:
- ADK agent lifecycle: initialise → subscribe to heartbeat → execute decision loop → settle
- Tool bindings: `echelon_status` (market state), `echelon_verify` (certificate check), `execute_trade` (LMSR)
- State management: T0Context persisted between ticks, decision history accumulated
- A2A registration: agent discoverable by other agents for coordination

**2. First Shark agent**
`backend/agents/adk/shark_v1.py` — the first autonomous agent:
- Archetype: SHARK (MEGALODON variant)
- Genome: ρ=0.90, ε=0.80, L=15000, novelty_threshold=0.6
- T1 rules: momentum-based trading (buy on price increase, take profit on target, stop-loss on drawdown)
- T2 personality: confident, terse, momentum-focused commentary
- T3 triggers: novel evidence patterns, cross-market correlation, Paradox proximity
- Success metric: executes ≥20 trades over 50 ticks, respects all risk limits (position, drawdown, stop-loss), and produces higher realised P&L than at least one lower-skill archetype (Degen or Saboteur) under the same scenario
- **Flakiness fallback:** if the "outperforms lower-skill archetype" gate proves non-deterministic across seed variations, swap to a calibration-based metric: Shark's log score > baseline OR Shark's Brier score < baseline, measured over the same 50-tick scenario. This avoids P&L variance while still proving the agent's decisions are informationally better than noise.

**3. Theatre integration**
Replace 012's stub agents with autonomous agents in the Sponsored Theatre lifecycle:
- `backend/services/agent_theatre_bridge.py` — spawns agent instances for a Theatre, wires into heartbeat, collects P&L at settlement
- Agent instances receive market state and evidence on each heartbeat tick
- Decision traces feed into RLMF export
- Compatible with 012's stub agent interface — existing E2E test should still pass with autonomous agents substituted

**4. Multi-agent population**
Spawn all 6 archetypes (one each) in a Theatre:
- Each agent uses its archetype's genome parameters
- Agents trade independently (no A2A coordination in Sprint 3 — deferred)
- Market dynamics emerge from heterogeneous strategies interacting via LMSR
- Validate: Shark trades frequently (momentum), Spy trades on evidence, Diplomat stabilises, Saboteur disrupts, Whale makes large positions, Degen trades randomly

**5. P&L aggregation**
Wire agent instance P&L back to Identity:
- Each instance reports: trades executed, final position, realised P&L, unrealised P&L at settlement
- Identity aggregates across all instances (multiple Theatres)
- P&L stored in agent Identity record (database)

**6. Autonomous agent E2E test**
`backend/agents/tests/test_autonomous_e2e.py` — the marquee test for 013:
- Creates a Companies House Theatre (reuses 012 E2E setup)
- Spawns 6 autonomous agents (one per archetype)
- Runs 50 trading ticks
- Injects mock evidence bundles at ticks 10, 20, 35 (fixed fixtures, same every run)
- **Determinism constraint:** evidence injections, initial balances, and RNG seeds are fixed; results must be deterministic across runs
- Verifies: all agents make decisions, trades execute successfully, bounded-loss invariant holds (market maker P&L ≥ −b·ln(n)), decision traces are RLMF-compatible, Shark trades most frequently, Whale trades least frequently (patience parameter)
- Verifies: at least one T3 escalation occurs (evidence injection should trigger novelty)
- Resolves and settles Theatre — certificate passes all 21 verifier checks

**7. Sprint 3 tests**
- `backend/agents/tests/test_adk_agent.py` — ADK lifecycle, tool bindings, state persistence
- `backend/agents/tests/test_agent_theatre_bridge.py` — instance spawning, heartbeat wiring, P&L collection
- `backend/agents/tests/test_multi_agent.py` — 6-archetype population, heterogeneous behaviour verification

### Sprint 3 Success Criteria

- [ ] Shark agent executes ≥20 trades over 50 ticks, respects risk limits, outperforms at least one lower-skill archetype
- [ ] All 6 archetypes demonstrate distinct trading behaviour
- [ ] T3 escalation triggers on evidence injection
- [ ] Decision traces feed RLMF export
- [ ] P&L aggregates correctly from instances to identity
- [ ] E2E test passes — full Theatre lifecycle with autonomous agents
- [ ] Certificate passes all 21 verifier checks
- [ ] All new tests pass, zero regression

---

## File Structure (New Files)

```
backend/
├── agents/
│   ├── genome.py                     # AgentGenome model (extend existing)
│   ├── context_compiler.py           # T0 Context Compiler
│   ├── decision_trace.py              # DecisionTrace schema (BEAUVOIR binding)
│   ├── rules_engine.py               # T1 Rules Engine
│   ├── personality_engine.py         # T2 Personality Engine
│   ├── deep_reasoning.py             # T3 Deep Reasoning Engine
│   ├── decision_router.py            # Novelty Threshold Router
│   ├── agent_instance.py             # Agent Instance lifecycle
│   ├── model_providers/
│   │   ├── __init__.py
│   │   ├── ollama_provider.py        # Qwen 3.5 via Ollama (T1)
│   │   ├── mistral_provider.py       # Mistral creative (T2)
│   │   └── anthropic_provider.py     # Sonnet/Opus (T3)
│   ├── adk/
│   │   ├── __init__.py
│   │   ├── echelon_agent.py          # ADK Agent wrapper
│   │   └── shark_v1.py               # First autonomous Shark agent
│   └── tests/
│       ├── test_context_compiler.py
│       ├── test_rules_engine.py
│       ├── test_agent_instance.py
│       ├── test_decision_trace.py
│       ├── test_personality_engine.py
│       ├── test_deep_reasoning.py
│       ├── test_decision_router.py
│       ├── test_model_providers.py
│       ├── test_adk_agent.py
│       ├── test_agent_theatre_bridge.py
│       ├── test_multi_agent.py
│       └── test_autonomous_e2e.py
├── services/
│   └── agent_theatre_bridge.py       # Agent ↔ Theatre integration
```

---

## Dependencies and Constraints

### Hard Dependencies
- **Sponsored Theatre E2E** (012) — defines the agent interface (decide → execute → settle), the Theatre lifecycle, and the RLMF export pipeline
- **LMSR engine** (010a) — TradingEngine.execute_trade() is the execution surface
- **WorldMonitor pipeline** (011) — evidence bundles feed into T1 decision context

### Infrastructure Requirements
- **Ollama** — must be installed locally with Qwen 3.5 4B model pulled. Tests marked `@pytest.mark.requires_ollama` for live model tests.
- **Mistral API key** — for T2 personality generation. Tests use mocks by default.
- **Anthropic API key** — for T3 deep reasoning. Tests use mocks by default. Rate limiting enforced.
- **Google ADK SDK (Python)** — Python SDK pinned for 013 (matches backend language). The ADK wrapper in `backend/agents/adk/echelon_agent.py` is a thin adapter: initialise agent, subscribe to heartbeat events, invoke tools, persist state. Tests mock the ADK runner via a `FakeADKRunner` that executes the agent's decision loop synchronously without the ADK event system. If ADK's Python SDK proves insufficient, the wrapper is replaceable without touching the T0/T1/T2/T3 pipeline.

### Constraints
- **No ADK imports in Sprint 1–2** — the T0/T1/T2/T3 pipeline must be testable and functional without the ADK dependency. Sprint 3 introduces the ADK wrapper only.
- **No A2A coordination in Sprint 3** — agents trade independently. Inter-agent communication (Diplomat coalitions, Spy intelligence sharing) is deferred.
- **No breeding/genealogy** — agent genomes are static in 013. Evolutionary parameter adaptation is future work.
- **No on-chain identity** — ERC-721 agent NFTs and ERC-6551 wallets are deferred. Identity is a database record.
- **Single Theatre target** — Companies House Theatre. Multi-theatre agent deployment is validated by architecture but not acceptance-tested.
- **T1 fallback to rules** — if Ollama is unavailable, T1 degrades to the pure rules engine from Sprint 1. Agents remain functional but lose NLP capability.

### Regression Target
Scoped regression: `backend/market/`, `backend/engines/`, `backend/scoring/`, `backend/osint/`, `backend/services/` (012 code). Pre-existing errors excluded.

---

## Archetype Cost Profiles (Illustrative — Not Acceptance Criteria)

| Archetype | T1 Calls/Day | T2 Calls/Day | T3 Calls/Day | Est. Daily Cost |
|-----------|-------------|-------------|-------------|----------------|
| Shark | ~1,700 (high frequency) | ~200 (trade commentary) | ~5 (novel situations) | ~$0.15 |
| Spy | ~500 (evidence-triggered) | ~50 (intel reports) | ~20 (anomaly investigation) | ~$0.60 |
| Diplomat | ~300 (stability checks) | ~100 (diplomatic comms) | ~10 (alliance strategy) | ~$0.30 |
| Saboteur | ~800 (disruption targeting) | ~150 (provocations) | ~3 (rare strategy) | ~$0.10 |
| Whale | ~100 (slow, deliberate) | ~20 (minimal comms) | ~30 (deep analysis) | ~$0.90 |
| Degen | ~2,000 (maximum frequency) | ~500 (colourful expression) | ~1 (almost never) | ~$0.05 |

**Total for 6 agents:** ~$2.10/day vs naive LLM routing at ~$42,500/month for 100 agents. The hierarchical architecture reduces costs by >99%.

**Note:** These figures are directional estimates based on assumed call frequencies and current API pricing. They are not acceptance criteria and will be validated empirically during Sprint 3. Actual costs depend on novelty threshold calibration, market volatility, and evidence arrival frequency.

---

## What 013 Unlocks

- **Autonomous market participants** — the infrastructure from 010-012 now has agents that actually decide to trade
- **RLMF data production** — agent decision traces at every tick produce the training data that's the commercial product
- **Heterogeneous market dynamics** — 6 archetypes with distinct strategies create realistic market behaviour
- **Foundation for 014 (Bounded Inquiry Markets)** — agents can participate in investigation, inspection, and scrutiny markets
- **T1 local inference** — Qwen 3.5 on Apple Silicon proves the self-hosted model tier works, no API dependency for routine decisions

---

## Acceptance Gate

Cycle-013 is complete when:
1. Shark agent executes ≥20 trades over 50 ticks, respects all risk limits, and outperforms at least one lower-skill archetype (Degen or Saboteur) under the same scenario
2. All 6 archetypes demonstrate distinct trading behaviour in the multi-agent test
3. T0/T1/T2/T3 pipeline works end-to-end with correct routing
4. Decision traces conform to RLMF schema
5. E2E test passes — full Theatre lifecycle with autonomous agents, certificate verified
6. Graceful fallback when any model provider is unavailable

---

## AGPL Compliance

Qwen 3.5 is Apache 2.0 licensed — AGPL-compatible. Ollama is MIT licensed. Mistral models are Apache 2.0 (open) or commercial (API). Google ADK is Apache 2.0. All compatible with AGPL codebase. No proprietary model weights are committed to the repository — they are loaded at runtime via provider APIs.
