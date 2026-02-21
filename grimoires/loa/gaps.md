# Gaps Analysis — Echelon

> **Generated**: 2026-02-18

## Phase 1 Implementation Gaps

These are questions that need answers before or during Phase 1 implementation.

### GAP-001: Oracle Construct Interface

**Question**: What is the interface contract for the oracle construct being evaluated?

**Context**: `echelon_context.md:36-39` says "Pass to the construct being evaluated (the Community Oracle)" but doesn't specify the API contract. Is it:
- A REST endpoint?
- A Python function?
- A CLI command?
- A webhook?

**Impact**: High — blocks `oracle/runner.py` design
**Recommendation**: Define a `ConstructInterface` protocol (Python Protocol class) that the oracle must implement. Start with a simple function signature: `def process(ground_truth: GroundTruthRecord) -> OracleOutput`

### GAP-002: Follow-Up Question Generation

**Question**: How are follow-up questions generated for Reply Accuracy scoring?

**Context**: `echelon_context.md:48` — "When the oracle handles a follow-up question about the PR, is the answer grounded in the actual source material?" But who generates the questions?

**Impact**: Medium — affects scoring completeness
**Recommendation**: Use Claude to generate 3-5 follow-up questions per PR based on the diff content. Pass these to the oracle. Score the responses.

### GAP-003: Claim Extraction Methodology

**Question**: How are individual claims extracted from an oracle's free-text summary?

**Context**: Precision scoring requires decomposing the summary into individual factual assertions. This is a non-trivial NLP task.

**Impact**: Medium — affects precision score reliability
**Recommendation**: Use Claude for claim decomposition with a structured prompt: "Extract each factual claim from this summary as a separate item."

### GAP-004: Statistical Significance

**Question**: Is 50 replays actually sufficient for statistical significance?

**Context**: `echelon_context.md:51` — "minimum 50 for statistical significance"

**Impact**: Low — 50 is reasonable for initial calibration
**Recommendation**: Include confidence intervals in the certificate. Flag when replay count is below recommended minimum.

### GAP-005: Scoring Determinism

**Question**: LLM-based scoring is inherently non-deterministic. How do we ensure reproducibility?

**Context**: `echelon_context.md:138` — "running the same oracle against the same PRs produces consistent scores"

**Impact**: High — core success criterion
**Recommendation**: Use temperature=0, cache LLM scoring responses, include scoring model version in certificate metadata. Accept that scores may vary within a tolerance band (e.g., ±0.05).

---

## Full Platform Gaps (Phase 2+)

### GAP-006: LMSR `b` Parameter Calibration

**Question**: What values of the LMSR liquidity parameter `b` are appropriate for different Theatre types?

**Context**: System Bible §3.4 describes `b` as committed capital but doesn't specify recommended ranges per template family.

**Impact**: Deferred (Phase 2)

### GAP-007: VRF Subscription Management

**Question**: How is the VRF subscription funded and managed in production?

**Context**: `EchelonVRFConsumer.sol` references Chainlink VRF V2, which requires LINK token subscription.

**Impact**: Deferred (Phase 2)

### GAP-008: Agent Brain Cost Optimization

**Question**: What is the expected cost per agent decision at scale?

**Context**: `backend/agents/brain.py:65-66` — 5% of decisions use LLM. With 1000 agents making 10 decisions per Theatre, that's 500 LLM calls per Theatre.

**Impact**: Deferred (Phase 2)

---

## Architectural Decision Gaps

### GAP-009: No ADR Directory

**Observation**: The project has no formal Architecture Decision Records. Design decisions are embedded in the System Bible and code comments.

**Recommendation**: Create `docs/adr/` with lightweight ADR format for future decisions. Not blocking.

### GAP-010: Database Migration Strategy

**Observation**: `backend/core/database.py` exists but no Alembic migrations or schema versioning visible.

**Recommendation**: Establish migration strategy before Phase 2 backend work.
