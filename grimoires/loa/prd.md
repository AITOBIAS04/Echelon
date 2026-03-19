# PRD — Cycle-037b: Multi-Evaluator Orchestration + Residual Scoring

**Cycle:** cycle-037b
**Date:** 18 March 2026
**Depends on:** Cycle-037 (Construct Contract Verification V1)
**Sprints:** 4 (0–3)
**Builder:** Loa (backend only)
**Planning source:** Follow-on to contract-backed construct verification; scorer orchestration and convergence handling

---

## 1. Problem Statement

### 1.1 Cycle 037 Creates The Contract, But Not The Full Judging System

Cycle 037 establishes `EvaluationContract`, policy normalization, deterministic requirement planning, issuance states, remediation payloads, and provenance integration. That is the substrate. It does not yet solve how residual non-deterministic claims should be evaluated once deterministic checks have run.

### 1.2 A Single LLM Scorer Is Still Too Soft For High-Trust Issuance

Constructs will always have some claims that are not mechanically testable:

- methodology adherence
- synthesis quality
- completeness of analysis
- domain-reasoning quality

If those claims are scored by one model, the certificate still depends too heavily on a single model’s opinion. The next trust layer is evaluator orchestration: multiple independent scorers, convergence tracking, disagreement handling, and clear issuance policy based on scorer alignment.

### 1.3 DEFERRED Needs To Mean “Coverage Missing,” Not “Score Felt Weird”

Cycle 037 already defines `DEFERRED` as an issuance-readiness state caused by incomplete verification coverage. Cycle 037b should preserve that semantics. Borderline or divergent rubric outcomes should not overload the same state. They need a separate operational path: converged, divergent, or escalated.

---

## 2. Product Contracts

### 2.1 Residual Rubric Execution Happens Only After Deterministic Checks

Cycle 037b must treat rubric scoring as the residual layer:

1. contract compiles
2. deterministic checks execute where supported
3. only the remaining rubric dimensions go to evaluator orchestration

Scorers must never be asked to judge dimensions already covered by deterministic results.

### 2.2 Evaluator Orchestration V1

Add a multi-evaluator orchestration layer with these primitives:

- evaluator registry/config
- per-dimension scoring requests
- per-evaluator score records
- convergence summary
- disagreement / escalation outcome

Minimum V1 evaluator count: **3 independent scorers**

The implementation should not hardcode vendor-specific model logic into certificate issuance; it should use a pluggable scorer interface.

### 2.3 Convergence Semantics

For each rubric dimension:

- `CONVERGED_PASS`
- `CONVERGED_FAIL`
- `DIVERGENT`
- `SKIPPED`

For a whole run:

- issue-ready if required residual dimensions converge
- non-issuable if required residual dimensions are divergent beyond policy threshold
- remediation payload should explain which dimensions diverged and why

### 2.4 Borderline Scores Are Not DEFERRED

Cycle 037b must keep the state model clean:

- `DEFERRED` remains about missing/insufficient check coverage from 037
- borderline or split evaluator results become `DIVERGENT` / `ESCALATED`

This preserves the distinction between:

- “we could not complete the required checks”
- “the scorers disagree on the result”

### 2.5 Scorer Provenance

Construct runs and certificates must persist:

- evaluator IDs used
- rubric version
- per-evaluator raw outputs
- per-evaluator per-dimension scores
- convergence summaries
- escalation flags

This is required for reproducibility and auditability.

### 2.6 Policy Thresholds

Cycle 037b must define V1 convergence thresholds. Suggested defaults:

- 3/3 agreement on required dimensions → converged
- 2/3 agreement → converged but flagged as lower confidence only if policy explicitly allows it
- 1/3 or fully split → divergent

The exact threshold should be stored in policy/rubric metadata, not hardcoded in route logic.

---

## 3. What This Cycle Does NOT Do

- **Does NOT redesign the Cycle 037 contract schema.** It consumes `EvaluationContract`.
- **Does NOT add new domain packs.** Security/domain-specific logic belongs in 037c.
- **Does NOT replace deterministic checks.** It only scores the residual non-deterministic dimensions.
- **Does NOT create a human appeals workflow yet.** It can emit escalation flags, but not a full review product.

---

## 4. Acceptance Criteria

1. Residual rubric dimensions are separated from deterministic dimensions before scoring
2. The scorer orchestration layer can run 3 independent evaluators over the same dimension set
3. Per-evaluator outputs and per-dimension scores are persisted
4. Convergence summaries are persisted and exposed in run/certificate provenance
5. Divergent outcomes are represented separately from Cycle 037 `DEFERRED`
6. Certificate issuance requires convergence on required residual dimensions
7. Existing construct routes continue to work with the new orchestration layer
8. ≥25 new tests pass

---

## 5. Test Plan

| Area | Tests | Coverage |
|---|---|---|
| Scorer interface | 3 | pluggable scorer adapters |
| Residual-dimension filtering | 3 | deterministic dimensions removed before scoring |
| Multi-evaluator execution | 4 | 3 scorers invoked, results captured |
| Convergence rules | 5 | 3/3, 2/3, 1/3, split, skipped |
| Divergence handling | 3 | divergent run outcome, escalation flag |
| Provenance persistence | 4 | raw scorer output, summaries, rubric version |
| Regression | 4 | existing construct path still works |
| **Total** | **~26** | |

---

## 6. Why This Matters

Cycle 037 makes construct verification contract-backed. Cycle 037b makes the non-deterministic part of that contract evaluation defensible. It is the layer that turns “an LLM scored this” into “independent evaluators converged on this residual judgement, and here is the trace.”
