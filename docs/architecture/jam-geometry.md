# Jam Geometry: Multi-Model Parallel Review Architecture

> Cycle: cycle-026 | Sprint 9, Task 9.4 | Source: Bridgebuilder Part III
> Prerequisite: Epistemic Trust Scopes (Tasks 9.1-9.3)
> Status: Design Complete | Implementation: Feature-flagged (opt-in)

## 1. Overview

Jam geometry is a multi-model review pattern where three independent reviewers analyze the same artifact in parallel, followed by a fourth model that synthesizes their findings into a unified review. The name references Miles Davis's second quintet — freedom within structure, individual expression converging into coherent harmony.

The key insight from Bridgebuilder Part III: existing Flatline Protocol proves that multi-model review catches defects single-model review misses. Jam extends this from 2 models to 3+1, adding a synthesis phase that resolves disagreements rather than just scoring them.

### Comparison: Seance vs Flatline vs Jam

| Aspect | Seance (baseline) | Flatline (current) | Jam (proposed) |
|--------|-------------------|-------------------|----------------|
| Models | 1 | 2 (reviewer + skeptic) | 3 + 1 synthesizer |
| Parallelism | None | 4 calls (2 review + 2 cross-score) | 3 calls + 1 sequential |
| Disagreement handling | N/A | Cross-scoring (0-1000) | Synthesis model resolves |
| Output | Single review | Consensus + disputed findings | Unified review with attribution |
| Cost per review | ~$0.003 | ~$0.006 | ~$0.007 |
| Epistemic diversity | Low | Medium (2 training sets) | High (3 training sets + synthesis) |

## 2. Three-Phase Workflow

### Phase 1: Divergent (Parallel)

Three reviewers independently analyze the same PR/document. Each produces a structured review with findings, concerns, and suggestions. The reviewers have no knowledge of each other's output.

```
            ┌─── jam-reviewer-claude ───┐
            │   (native, full access)   │
            │                           │
Artifact ──>├─── jam-reviewer-gpt ─────>├──> [3 independent reviews]
            │   (openai:gpt-5.2)       │
            │                           │
            └─── jam-reviewer-kimi ────>┘
                (moonshot:kimi-k2)
```

**Infrastructure**: Each call routes through `cheval.py:resolve_execution()` (line 222) → `get_adapter()` (line 331) → `invoke_with_retry()` (line 369). All three calls execute concurrently.

**Epistemic filtering**: Before each call, `context_filter.py:filter_context()` applies the model's `context_access` scopes:

| Reviewer | architecture | business_logic | security | lore |
|----------|-------------|----------------|----------|------|
| Claude (native) | full | full | full | full |
| GPT-5.2 | full | redacted | none | full |
| Kimi-K2 | full | redacted | none | full |

Source: `.claude/data/model-permissions.yaml:38-97`

This means GPT and Kimi see architecture and lore but not security findings or full function bodies. Claude sees everything. This asymmetry is intentional — it forces diverse perspectives from different information availability.

### Phase 2: Synthesis (Sequential)

A different model (not one of the reviewers) synthesizes the three reviews. The synthesizer identifies:

1. **Consensus findings**: Issues raised by 2+ reviewers (high signal)
2. **Unique insights**: Issues raised by only one reviewer (potential blind spots or unique perspective)
3. **Disagreements**: Contradictory assessments between reviewers (requires resolution)

```
[Review-Claude] ──┐
                  │
[Review-GPT] ────>├──> jam-synthesizer ──> Unified Review
                  │   (claude-sonnet-4-6)
[Review-Kimi] ───>┘
```

**Model selection**: `anthropic:claude-sonnet-4-6` via the `cheap` alias. The synthesizer needs text comprehension, not deep reasoning. Cost optimization: Sonnet is 40% cheaper than Opus per token.

Source: `.claude/defaults/model-config.yaml:182-183`

**Why a different model?** If a reviewer also synthesizes, it biases toward its own findings. An independent synthesizer treats all three reviews equally — like an academic journal editor who didn't write any of the peer reviews.

### Phase 3: Harmony (Output)

The unified review is posted with per-model attribution. Each finding is tagged with which reviewer(s) identified it.

```markdown
## Findings

### [Consensus] Missing input validation on /api/users
Identified by: Claude, GPT-5.2, Kimi-K2
Severity: High
...

### [Unique: GPT-5.2] Race condition in cache invalidation
Identified by: GPT-5.2 only
Severity: Medium
Note: Other reviewers did not flag this — may indicate a blind spot or false positive.
...

### [Disagreement] Error handling in payment flow
Claude: Adequate (try/catch covers all paths)
GPT-5.2: Insufficient (missing timeout handling)
Kimi-K2: Adequate
Resolution: Majority assessment (adequate), but timeout gap noted for follow-up.
```

## 3. Cost Analysis

Assumptions: 10K input tokens (PR context), 5K output tokens (review findings) per reviewer. Pricing from `.claude/defaults/model-config.yaml:18-89`.

### Per-Review Cost Breakdown

| Component | Model | Input Cost | Output Cost | Total |
|-----------|-------|-----------|-------------|-------|
| Divergent: Claude | native (no API) | $0.000 | $0.000 | $0.000 |
| Divergent: GPT-5.2 | openai:gpt-5.2 | $0.100 | $0.150 | $0.250 |
| Divergent: Kimi-K2 | moonshot:kimi-k2 | $0.100 | $0.150 | $0.250 |
| Synthesis | claude-sonnet-4-6 | $0.060 | $0.075 | $0.135 |
| **Total** | | | | **$0.635** |

*Costs in milli-dollars (thousandths). Actual cost: ~$0.000635 per review.*

### Comparison to Existing Geometries

| Geometry | API Calls | Estimated Cost | Quality Signal |
|----------|-----------|---------------|----------------|
| Seance (1 model) | 1 | ~$0.25m | Baseline |
| Flatline (2+2) | 4 | ~$0.60m | 2x cross-validation |
| **Jam (3+1)** | **4** | **~$0.64m** | **3x independent + synthesis** |

Jam is only ~7% more expensive than Flatline but adds a third independent perspective and intelligent synthesis (vs cross-scoring which only produces numerical agreement metrics).

### Budget Enforcement

All four calls are tracked through `BudgetEnforcer` (`cheval.py:358-363`). Each divergent call and the synthesis call independently records costs via `pre_call_atomic()` + `post_call()`. The conservation invariant (INV-001) applies to each call individually.

**Budget exceeded during Jam**: If budget check fails mid-geometry:
- Before any divergent call: abort entire Jam, fall back to Seance
- During divergent phase: complete started calls, skip remaining, synthesize partial reviews
- Before synthesis: post existing reviews without synthesis

## 4. Infrastructure Mapping

### Existing Components Used

| Component | File | Purpose in Jam |
|-----------|------|---------------|
| `resolve_execution()` | `.claude/adapters/loa_cheval/routing/resolver.py:114` | Agent binding → provider:model for each reviewer |
| `get_adapter()` | `.claude/adapters/cheval.py:331` | Get provider adapter per reviewer |
| `invoke_with_retry()` | `.claude/adapters/cheval.py:369` | Execute each review call with retry |
| `filter_context()` | `.claude/adapters/loa_cheval/routing/context_filter.py` | Epistemic scope filtering per reviewer |
| `BudgetEnforcer` | `.claude/adapters/loa_cheval/metering/budget.py` | Cost tracking for all 4 calls |
| `validate_bindings()` | `.claude/adapters/loa_cheval/routing/resolver.py` | Pre-flight check all 4 agent bindings resolve |

### New Components Required

| Component | Purpose |
|-----------|---------|
| `JamOrchestrator` | Coordinate divergent phase (parallel) + synthesis phase (sequential) |
| `JamReviewParser` | Parse structured review output from each reviewer into common format |
| `JamSynthesisPrompt` | Template for synthesis model to merge/resolve three reviews |
| `JamOutputFormatter` | Format unified review with attribution for PR comment |

### Phase 0: Flatline as Scaffold

The Flatline Protocol (`.claude/protocols/flatline-protocol.md`) already implements:
- Parallel multi-model calls (Phase 1: 4 parallel calls)
- Cross-model scoring (Phase 2: 2 parallel calls)
- Consensus extraction (Phase 3: categorization)

Jam re-uses the parallel call infrastructure but replaces cross-scoring with synthesis. The Flatline Protocol's `HIGH_CONSENSUS` / `DISPUTED` / `BLOCKER` categories map to Jam's `Consensus` / `Unique` / `Disagreement` tags.

**Migration path**: Jam geometry could be implemented as a Flatline configuration variant rather than a separate system. The `flatline-protocol.md` Phase 2 (cross-scoring) would be replaced with a synthesis call.

## 5. Graceful Degradation

| Failure | Recovery |
|---------|----------|
| One divergent reviewer times out | Synthesize from 2 reviews (note reduced confidence) |
| Two divergent reviewers fail | Fall back to Seance geometry with surviving reviewer |
| Synthesizer fails | Post 3 individual reviews without synthesis (Flatline-style) |
| All reviewers fail | Abort and log; do not post empty review |
| Budget exceeded pre-divergent | Fall back to Seance (cheapest single model) |

## 6. Quality Tradeoffs

### Advantages over Flatline

1. **Third perspective**: Kimi-K2 has different training data biases than GPT-5.2 and Claude, catching issues the other two share as blind spots
2. **Intelligent resolution**: Synthesis model explains *why* reviewers disagree, rather than just reporting a score delta
3. **Attribution**: Users see which model flagged which issue, building calibration over time
4. **Cost parity**: Nearly identical cost to Flatline (4 API calls each)

### Risks

1. **Noise amplification**: More reviewers means more false positives for the synthesizer to filter
2. **Synthesis quality**: The synthesizer might miss subtle disagreements or incorrectly categorize unique findings
3. **Latency**: Sequential synthesis adds one round-trip after divergent phase completes (Flatline's cross-scoring is parallel)
4. **Model availability**: Three external models means three potential failure points

### Mitigations

- Feature flag default `false` — opt-in only (`.claude/defaults/model-config.yaml:167`)
- Graceful degradation to Flatline/Seance on partial failure
- Synthesis prompt includes explicit instructions to preserve unique findings (bias toward inclusion)
- Latency: synthesis is typically fast (low-reasoning text summarization task)

## 7. Implementation Roadmap

This document is a design artifact. Implementation would proceed as:

1. **Implement JamOrchestrator**: Parallel divergent calls using existing `cheval.py` infrastructure
2. **Implement JamSynthesisPrompt**: Structured prompt template for the synthesis model
3. **Integrate with `/review-sprint`**: Add Jam as geometry option alongside Flatline and Seance
4. **Add feature flag gate**: Check `hounfour.feature_flags.jam_geometry` before activation
5. **Test**: Unit tests for orchestration, integration test for full Jam flow (mocked)

**Prerequisite completed**: Epistemic trust scopes (Tasks 9.1-9.3) ensure each reviewer receives appropriately filtered context.

## References

- **Miles Davis's Second Quintet** (1964-1968): "Freedom and form are not opposed. Structure gives each voice room to say something original." The quintet's rhythm section provided harmonic and rhythmic structure while soloists explored freely — Jam reviewers operate independently within the trust scope structure.
- **Academic Peer Review**: Independent reviewers + editor (synthesizer). The editor doesn't write a review — they integrate the reviewers' findings into an accept/revise/reject decision with specific revision requirements.
- **Bridgebuilder Part III**: Original proposal for Jam geometry, including the Maroon collaboration geometry concept where epistemic trust scopes make multi-agent coordination safe.
- **Flatline Protocol**: Production multi-model review system serving as the implementation scaffold.
