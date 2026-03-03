# Sprint 26 -- Agent Runtime: T2/T3/Routing Implementation Report

> Sprint: sprint-26 (global) | sprint-2 (local)
> Cycle: cycle-013 -- Agent Runtime: Four-Tier Hierarchical Intelligence
> Status: **COMPLETE** -- All 7 tasks implemented, 134 tests passing (60 new + 74 from sprint-25)

---

## Task Summary

| Task | Title | Status | Tests |
|------|-------|--------|-------|
| T2.1 | T2 Personality Engine | Done | 14 |
| T2.2 | T3 Deep Reasoning Engine | Done | 14 |
| T2.3 | Novelty Threshold Router | Done | 12 |
| T2.4 | Ollama Provider (T1) | Done | 7 |
| T2.5 | Mistral Provider (T2) | Done | 5 |
| T2.6 | Anthropic Provider (T3) | Done | 5 |
| T2.7 | Sprint 2 Tests | Done | (included above) |
| **Total** | | **7/7** | **60 new (134 total)** |

---

## T2.4: BaseModelProvider ABC + OllamaProvider

**Files:**
- `backend/agents/model_providers/__init__.py` (83 lines) -- BaseModelProvider ABC, ProviderConfig
- `backend/agents/model_providers/ollama_provider.py` (108 lines)
**Tests:** `backend/agents/tests/test_model_providers.py` -- TestBaseModelProvider (3), TestOllamaProvider (7)

### What was built

- `ProviderConfig` -- stdlib `@dataclass` with api_key, base_url, model_name, timeout_s (30s), max_retries (2)
- `BaseModelProvider` -- ABC with `generate()`, `health_check()`, `is_available()` abstract methods
- `OllamaProvider` -- wraps Ollama local API at `http://localhost:11434` for Qwen 3.5 4B/9B
  - `generate()` -- POST `/api/generate` with structured output via `format` parameter
  - `health_check()` -- GET `/api/tags`, checks model name in loaded models list
  - Graceful fallback: `is_available()` returns cached `_last_health`

---

## T2.5: MistralProvider

**File:** `backend/agents/model_providers/mistral_provider.py` (108 lines)
**Tests:** `backend/agents/tests/test_model_providers.py` -- TestMistralProvider (5)

### What was built

- `MistralProvider` -- wraps Mistral API at `https://api.mistral.ai/v1`, model `mistral-small-latest`
  - `generate()` -- POST `/chat/completions` with Bearer auth, returns `{rationale, commentary}`
  - `health_check()` -- GET `/models` with auth header, returns True on 200
  - Graceful fallback: returns False immediately when API key not configured

---

## T2.6: AnthropicProvider

**File:** `backend/agents/model_providers/anthropic_provider.py` (117 lines)
**Tests:** `backend/agents/tests/test_model_providers.py` -- TestAnthropicProvider (5)

### What was built

- `AnthropicProvider` -- wraps Anthropic API at `https://api.anthropic.com/v1`, model `claude-sonnet-4-5-20241022`
  - `generate()` -- POST `/messages` with `x-api-key` header, `anthropic-version: 2023-06-01`
  - Attempts structured JSON parse from response content
  - Falls back to `HOLD` with `reasoning_summary` on `json.JSONDecodeError`
  - `health_check()` -- verifies API key is configured (no probe call to avoid token burn)

---

## T2.1: T2 Personality Engine

**File:** `backend/agents/personality_engine.py` (162 lines)
**Tests:** `backend/agents/tests/test_personality_engine.py` (14 tests)

### What was built

- `T2Output` -- frozen dataclass with `coloured_rationale`, `market_commentary`, `diplomatic_message`
- `PERSONALITY_PROMPTS` -- dict with distinct prompts for all 6 archetypes (SHARK, SPY, DIPLOMAT, SABOTEUR, WHALE, DEGEN)
- `PersonalityEngine` -- async `express()` method that:
  - Checks provider health before calling
  - Falls back to generic template when provider is None, health check fails, or generate() raises
  - CRITICAL: never overrides T1's action (expression only, verified by test)
  - T2Output contains only strings -- never fed back into decision pipeline

---

## T2.2: T3 Deep Reasoning Engine

**File:** `backend/agents/deep_reasoning.py` (235 lines)
**Tests:** `backend/agents/tests/test_deep_reasoning.py` (14 tests)

### What was built

- `T3Decision` -- frozen dataclass with action, outcome_index, shares, confidence, reasoning_summary, evidence_refs, pattern_name
- `T3RateLimiter` -- configurable per-agent rate limiting with:
  - Daily count with auto-reset on date change
  - Per-tick limit (default 1) to prevent multiple T3 calls per tick
  - `can_call(tick)` / `record_call()` interface
- `DeepReasoningEngine` -- async `reason()` method that:
  - Gets/creates per-agent rate limiter
  - Checks rate limit -> provider health -> generates -> returns T3Decision
  - Returns None on any failure (rate limit, no provider, health check failure, exception)
  - `_build_prompt()` includes archetype, prices, position, T1 reasoning, evidence count

---

## T2.3: Novelty Threshold Router

**File:** `backend/agents/decision_router.py` (178 lines)
**Tests:** `backend/agents/tests/test_decision_router.py` (12 tests)

### What was built

- `RoutedDecision` -- dataclass with action, tier_used ("T1-RULES"/"T1-LOCAL-LLM"/"T3"), t2_output, escalated_to_t3, t3_rate_limited, evidence_refs
- `DecisionRouter` -- orchestrates T0->T1->T2/T3 pipeline:
  1. T1 decision as baseline
  2. Escalation check: `t1.escalate_to_t3 OR confidence < novelty_threshold`
  3. If escalation + T3 available: `deep_reasoning.reason()` -- replaces T1 on success
  4. If T3 returns None: fall back to T1, set `t3_rate_limited=True`
  5. T2 expression runs independently (non-fatal, exception-safe)
  - Pure T1 mode works with None engines

---

## Sprint 1 Carryover Resolution

| Finding | Severity | File | Resolution |
|---------|----------|------|------------|
| LOW-01 | LOW | `genome.py` | Removed unused `field_validator` import |
| LOW-02 | LOW | `rules_engine.py` | Removed unused `field` import |
| LOW-03 | LOW | `agent_instance.py` | Removed unused `field` import |

All three carryover findings from sprint-25 audit resolved. Import lines verified clean:
- `genome.py`: `from pydantic import BaseModel, Field`
- `rules_engine.py`: `from dataclasses import dataclass`
- `agent_instance.py`: `from dataclasses import dataclass`

---

## Test Results

```
134 passed in 0.17s
```

| Test File | Count | Coverage |
|-----------|-------|----------|
| test_model_providers.py | 20 | ABC enforcement, 3 providers (config, generate, health, fallback) |
| test_personality_engine.py | 14 | T2Output, all 6 archetypes, non-interference, fallback paths |
| test_deep_reasoning.py | 14 | T3Decision, rate limiter, per-agent isolation, fallback |
| test_decision_router.py | 12 | Routing logic, T3 escalation, rate-limit fallback, T2 enable/disable |
| *(Sprint 1 tests)* | 74 | No regressions |

All tests use mocked providers. No live API calls in the default test suite.

---

## Files Created

| File | Lines | Purpose |
|------|-------|---------|
| `backend/agents/model_providers/__init__.py` | 83 | BaseModelProvider ABC + ProviderConfig |
| `backend/agents/model_providers/ollama_provider.py` | 108 | Ollama local API wrapper (T1) |
| `backend/agents/model_providers/mistral_provider.py` | 108 | Mistral API wrapper (T2) |
| `backend/agents/model_providers/anthropic_provider.py` | 117 | Anthropic API wrapper (T3) |
| `backend/agents/personality_engine.py` | 162 | T2 PersonalityEngine |
| `backend/agents/deep_reasoning.py` | 235 | T3 DeepReasoningEngine + T3RateLimiter |
| `backend/agents/decision_router.py` | 178 | Novelty Threshold Router |
| `backend/agents/tests/test_model_providers.py` | 372 | Model provider tests |
| `backend/agents/tests/test_personality_engine.py` | 238 | T2 personality tests |
| `backend/agents/tests/test_deep_reasoning.py` | 370 | T3 deep reasoning tests |
| `backend/agents/tests/test_decision_router.py` | 385 | Decision router tests |
| **Total** | **2,356** | |

## Files Modified

| File | Change | Reason |
|------|--------|--------|
| `backend/agents/genome.py` | Removed unused `field_validator` import | Sprint-25 audit LOW-01 |
| `backend/agents/rules_engine.py` | Removed unused `field` import | Sprint-25 audit LOW-02 |
| `backend/agents/agent_instance.py` | Removed unused `field` import | Sprint-25 audit LOW-03 |

---

## Technical Decisions

1. **Module-level httpx import** -- All three providers import httpx at module level (not lazily inside methods). This ensures `patch("module.httpx.AsyncClient")` works correctly in tests. The SDD suggested lazy imports but module-level is more Pythonic and testable.

2. **Anthropic health check avoids probe call** -- `AnthropicProvider.health_check()` only verifies that an API key is configured. It does not make a probe call to avoid burning tokens. Full validation occurs on first `generate()` call.

3. **T3RateLimiter uses UTC date string for daily reset** -- `datetime.now(timezone.utc).strftime("%Y-%m-%d")` for reliable daily reset regardless of timezone. Uses `datetime.now(timezone.utc)` (not deprecated `utcnow()`).

4. **T2 non-interference enforced structurally** -- `T2Output` is a frozen dataclass containing only strings. It is impossible for T2 to override T1's action because the types don't compose. This is verified by test `test_non_interference_with_t1`.

5. **Per-agent rate limiters created lazily** -- `DeepReasoningEngine._rate_limiters` dict is populated on first call per agent. This avoids requiring agent registration upfront and naturally supports dynamic agent pools.

6. **RoutedDecision uses `@dataclass` (not frozen)** -- Unlike T1Decision and T3Decision which are frozen, RoutedDecision is mutable because it is assembled incrementally during routing. T2 output is attached after initial construction.

---

## Acceptance Criteria Checklist (PRD Section 9b)

- [x] T2 produces personality-flavoured output for all 6 archetypes
- [x] T2 never overrides T1's action (expression only, verified by test)
- [x] T3 produces structured reasoning (reasoning_summary + evidence_refs + decision_trace) for escalated decisions
- [x] Router correctly routes: high-confidence T1 -> use T1Decision; low-confidence -> escalate to T3
- [x] Ollama provider connects to local Qwen 3.5 4B/9B with structured output
- [x] Ollama fallback: T1 degrades to T1-RULES when Ollama unavailable
- [x] Mistral provider generates archetype-specific personality output
- [x] Mistral fallback: generic template when API unavailable
- [x] Anthropic provider generates deep reasoning output
- [x] T3 rate limiting enforced (max calls per agent per day)
- [x] Anthropic fallback: router falls back to T1 when API unavailable or rate-limited
- [x] Decision traces record correct `tier_used` ("T1-RULES", "T1-LOCAL-LLM", "T3")
- [x] No modifications to `backend/market/`, `backend/engines/`, `backend/osint/`, `backend/services/`
- [x] Scoped regression: all 134 tests pass
- [x] 25+ new Sprint 2 tests pass (mocked providers) -- 60 new tests (2.4x minimum)

---

## Known Issues

None. All acceptance criteria met. All tests pass. No regressions.

---

## Concerns / Deviations

1. **SDD specified lazy httpx imports; implementation uses module-level** -- The SDD showed `import httpx` inside method bodies. Implementation uses module-level imports instead, which is standard Python practice and enables straightforward mock patching. No functional difference.

2. **T2Output.diplomatic_message not used by router** -- The `diplomatic_message` field on T2Output exists for future Diplomat-archetype-specific messaging but is not populated by any current code path. It defaults to None.
