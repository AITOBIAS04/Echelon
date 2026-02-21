<!-- AGENT-CONTEXT
name: loa-hounfour-bridge
type: framework-adapter
purpose: Multi-provider model routing with metering, epistemic trust scopes, and adversarial review geometries for the Loa AI development framework
version: 7.0.0
interfaces:
  - cheval.py CLI (agent invocation via provider adapters)
  - model-permissions.yaml (trust scopes and epistemic access)
  - model-config.yaml (agent bindings, aliases, pricing, feature flags)
  - invariants.yaml (cross-repository economic invariants)
dependencies:
  - python 3.11+
  - pyyaml
  - httpx
  - jq, yq (shell tooling)
-->

# Hounfour Runtime Bridge

The Hounfour Runtime Bridge enables model-heterogeneous agent routing for the Loa AI development framework. It extends a single-provider (Anthropic Claude) system into a multi-provider ecosystem supporting Google Gemini, OpenAI GPT, and Moonshot Kimi alongside native Claude Code sessions. Each provider adapter implements a common `ProviderAdapter` interface with standardized error mapping, retry semantics, and metering integration. The bridge enforces a conservation invariant across all API calls: no micro-USD is created or destroyed during cost calculation.

<!-- provenance: DERIVED -->

## Architecture

The system is organized into four layers connected by the `cheval.py` orchestrator. The orchestrator resolves agent bindings to provider:model pairs, applies epistemic context filtering based on trust scopes, enforces budget constraints, and delegates to the appropriate provider adapter.

```
                        cheval.py (orchestrator)
                              |
            ┌─────────────────┼─────────────────┐
            |                 |                  |
     ┌──────┴──────┐  ┌──────┴──────┐  ┌───────┴───────┐
     |   routing/   |  |  metering/  |  |  providers/   |
     | resolver.py  |  | budget.py   |  | google_.py    |
     | chains.py    |  | pricing.py  |  | openai_.py    |
     | circuit_b.py |  | ledger.py   |  | anthropic_.py |
     | context_f.py |  | rate_lim.py |  | base.py       |
     └─────────────┘  └─────────────┘  └───────────────┘
```

The routing layer resolves agent names (e.g., `deep-researcher`, `jam-reviewer-gpt`) to concrete provider:model pairs through a binding → alias → provider chain (`.claude/adapters/loa_cheval/routing/resolver.py:resolve_execution`). Fallback chains (`chains.py`) define degradation paths when budget or circuit breaker constraints trigger model downgrades. The circuit breaker (`circuit_breaker.py`) tracks per-provider failure rates and trips to fallback when thresholds are exceeded. The context filter (`context_filter.py`) implements epistemic trust scopes — controlling what each model *knows* based on its `context_access` dimensions.

The metering layer tracks costs atomically via `BudgetEnforcer` pre-call/post-call hooks. Integer arithmetic ensures the conservation invariant (INV-001): `cost_micro * 1_000_000 + remainder == tokens * price_per_million`. A `RemainderAccumulator` carries sub-micro-USD fractions across requests without loss. Budget actions (ALLOW, WARN, DOWNGRADE, BLOCK) gate API calls based on daily spend against configured limits.

<!-- provenance: CODE-FACTUAL -->

## Key Capabilities

- **Multi-Provider Routing**: Three provider adapters (Google, OpenAI, Anthropic) implementing `ProviderAdapter.complete()` with standardized request/response translation and error mapping to Hounfour error types
- **Deep Research**: Google Interactions API integration with blocking-poll and non-blocking async modes, interaction persistence for crash recovery, and citation normalization from Google's `groundingMetadata` format
- **Epistemic Trust Scopes**: 7-dimensional trust model (data_access, financial, delegation, model_selection, governance, external_communication, context_access) controlling both what models *can do* and what they *know*. Context filtering strips architecture, business logic, security, and lore content based on per-model permissions
- **Conservation Metering**: Integer-arithmetic cost tracking with formal invariants (INV-001 through INV-005) verified by property-based tests. Budget enforcement with DOWNGRADE action triggering fallback chain walks to cheaper models
- **Jam Geometry**: Design for 3+1 multi-model parallel review (Claude + GPT + Kimi → Sonnet synthesizer) with per-model attribution and intelligent disagreement resolution. Feature-flagged, builds on existing Flatline Protocol infrastructure
- **Cross-Repository Invariants**: Formal property declarations (`invariants.yaml`) spanning pricing, budget, and ledger layers with automated verification script (`verify-invariants.sh`) confirming all 17 source references resolve

<!-- provenance: CODE-FACTUAL -->

## Interfaces

The primary invocation interface is `cheval.py` which accepts an agent name, messages, and optional model override. It resolves the binding, checks feature flags, applies context filtering, enforces budget, and delegates to the appropriate adapter.

Key configuration interfaces:

| File | Purpose |
|------|---------|
| `.claude/defaults/model-config.yaml` | Agent bindings, model aliases, pricing entries, feature flags |
| `.claude/data/model-permissions.yaml` | Trust scopes (7 dimensions + epistemic context_access) per model |
| `.loa.config.yaml` | User configuration: feature toggles, budget limits, persistence mode |
| `grimoires/loa/invariants.yaml` | Cross-repository economic invariant declarations |

Provider adapters expose `complete(request)` returning `CompletionResponse`:
- `.claude/adapters/loa_cheval/providers/google_adapter.py:GoogleAdapter` — Gemini 2.5/3 standard and Deep Research via Interactions API
- `.claude/adapters/loa_cheval/providers/openai_adapter.py:OpenAIAdapter` — GPT-5.2 and compatible models
- `.claude/adapters/loa_cheval/providers/anthropic_adapter.py:AnthropicAdapter` — Claude Opus/Sonnet via native runtime or API

<!-- provenance: CODE-FACTUAL -->

## Module Map

| Module | Path | Purpose |
|--------|------|---------|
| Orchestrator | `.claude/adapters/cheval.py` | Main entry point — agent resolution, context filtering, budget enforcement, adapter dispatch |
| Google Adapter | `.claude/adapters/loa_cheval/providers/google_adapter.py` | Gemini standard completion and Deep Research via Interactions API |
| OpenAI Adapter | `.claude/adapters/loa_cheval/providers/openai_adapter.py` | GPT-5.2 completion with thinking traces support |
| Anthropic Adapter | `.claude/adapters/loa_cheval/providers/anthropic_adapter.py` | Claude API adapter for non-native invocation |
| Resolver | `.claude/adapters/loa_cheval/routing/resolver.py` | Agent binding → alias → provider:model resolution with native_runtime guard |
| Context Filter | `.claude/adapters/loa_cheval/routing/context_filter.py` | Epistemic scope filtering — strips content by context_access dimensions |
| Fallback Chains | `.claude/adapters/loa_cheval/routing/chains.py` | Degradation paths for budget-exceeded and circuit-breaker-tripped scenarios |
| Circuit Breaker | `.claude/adapters/loa_cheval/routing/circuit_breaker.py` | Per-provider failure tracking with configurable trip thresholds |
| Budget Enforcer | `.claude/adapters/loa_cheval/metering/budget.py` | Atomic pre_call/post_call budget checks with flock-based concurrency |
| Pricing Engine | `.claude/adapters/loa_cheval/metering/pricing.py` | Integer-arithmetic cost calculation with RemainderAccumulator |
| Ledger | `.claude/adapters/loa_cheval/metering/ledger.py` | JSONL cost ledger with daily spend tracking |
| Concurrency | `.claude/adapters/loa_cheval/providers/concurrency.py` | FLockSemaphore for concurrent API call management |
| Invariant Schema | `.claude/schemas/invariants.schema.json` | JSON Schema for cross-repository invariant declarations |
| Invariant Verifier | `.claude/scripts/verify-invariants.sh` | Automated verification of invariant source references |
| Jam Geometry Design | `docs/architecture/jam-geometry.md` | Multi-model parallel review architecture specification |

<!-- provenance: CODE-FACTUAL -->

## Verification

- 17/17 invariant verification checks passing (`verify-invariants.sh`)
- 5 formal invariants declared: Conservation (INV-001), Non-negative spend (INV-002), Deduplication (INV-003), Budget monotonicity (INV-004), Trust boundary (INV-005)
- 14 BATS tests for invariant verification infrastructure (`tests/unit/invariant-verification.bats`)
- 22 test files in `.claude/adapters/tests/` covering all provider adapters, routing, metering, trust scopes, feature flags, and epistemic filtering
- Property-based conservation tests via `test_conservation_invariant.py`

<!-- provenance: OPERATIONAL -->

## Agents

Agent bindings define how named roles map to provider:model pairs:

| Agent | Model | Use Case |
|-------|-------|----------|
| `deep-researcher` | google:deep-research-pro | Async research via Interactions API |
| `flatline-reviewer` | openai:gpt-5.2 | Adversarial code review (Flatline Protocol) |
| `jam-reviewer-claude` | native (Claude Code) | Jam geometry divergent review |
| `jam-reviewer-gpt` | openai:gpt-5.2 | Jam geometry divergent review |
| `jam-reviewer-kimi` | moonshot:kimi-k2-thinking | Jam geometry divergent review |
| `jam-synthesizer` | anthropic:claude-sonnet-4-6 | Jam geometry synthesis (cost-optimized) |

<!-- provenance: CODE-FACTUAL -->

## Ecosystem

This bridge connects the Loa framework to the Hounfour model routing protocol (v7.0.0). The invariant declarations reference three codebases: Loa (this repo, all verified), Hounfour (external monetary policy), and Arrakis (external lot invariant). Cross-repo references are verified in their respective CI pipelines.

<!-- provenance: DERIVED -->

## Limitations

- Deep Research requires Google API key with Interactions API access (not universally available)
- Epistemic context filtering is heuristic-based (regex patterns for function bodies, security markers) — not a security boundary. See BB-502 for language coverage gaps
- Jam geometry is a design artifact only — implementation requires `JamOrchestrator`, `JamSynthesisPrompt`, and integration with `/review-sprint`
- `butterfreezone-gen.sh` requires bash 4+ (macOS ships bash 3.2) — manual generation needed on stock macOS
- Eval regression analysis (Tasks 8.5/8.6) requires upstream eval infrastructure not available in this mounted context

<!-- provenance: OPERATIONAL -->

## Quick Start

```bash
# Verify invariants pass
.claude/scripts/verify-invariants.sh

# Run BATS tests (requires bats installed)
bats tests/unit/invariant-verification.bats

# Run Python adapter tests
cd .claude/adapters && python -m pytest tests/ -v

# Check configuration
cat .claude/defaults/model-config.yaml  # agent bindings
cat .claude/data/model-permissions.yaml  # trust scopes
cat grimoires/loa/invariants.yaml       # economic invariants
```

<!-- provenance: OPERATIONAL -->

<!-- ground-truth-meta
generator: butterfreezone-gen/manual
head_sha: 7b5d74f93a21dd19fbca531438f11525a76e0e59
generated_at: 2026-02-19T13:59:28Z
-->
