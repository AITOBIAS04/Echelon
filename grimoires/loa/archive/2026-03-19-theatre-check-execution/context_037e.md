# Context — Cycle-037e: Theatre Check Execution

**Cycle:** cycle-037e
**Date:** 19 March 2026
**Builder:** Loa

---

## Why This Cycle Exists

We now know two things with confidence:

1. external theatre constructs are real
2. Echelon can compile them today

TREMOR and CORONA both compile cleanly through the 037 / 037b / 037d substrate. Their contracts normalize correctly. Their theatre-specific planned checks appear correctly. Their hashes behave correctly. Invalid theatre metadata fails correctly.

That is strong progress, but it still leaves the key gap:

the checks are planned, not executed.

---

## The Right Next Step

The clean sequence is:

- `037` = contract substrate
- `037b` = residual judgement hardening
- `037d` = theatre construct compilation
- `037e` = theatre check execution
- `038` = cross-theatre paradox detection

That ordering matters.

Cross-theatre paradox logic gets much stronger if it compares theatres whose local deterministic checks have actually run, not just theatres with planned requirements on paper.

---

## What Makes Theatre Execution Different

Theatre execution is not generic scoring.

It is deterministic replay and recomputation:

- replay settlement against known oracle outcomes
- compare cross-validation oracles directly
- recompute Brier outputs
- verify template-level functional logic

That means the implementation should be framed as a runner or executor, not another soft evaluator.

---

## Why TREMOR And CORONA Matter

They are the first real external theatre fixtures, and they already prove something important:

- the theatre parser handles both metadata layouts
- the precise domain normalization works
- theatre-specific check planning works
- no special-casing was required to make both fit

That makes them ideal fixtures for 037e.

The cycle should use both, not just TREMOR, because:

- TREMOR proves the seismic pattern
- CORONA proves the pattern generalizes to a second natural-phenomena domain with different oracle sources and flatter metadata

---

## What Loa Should Keep Tight

### Prefer Deterministic Replay Over Live Calls

For V1, execution should be based on deterministic fixtures or replay inputs, not live network fetching. This keeps tests stable and makes the certificate path reproducible.

### Keep Readiness Semantics Honest

If a critical theatre check cannot run, the certificate should show a real skipped or incomplete coverage state. Do not convert missing execution into apparent success.

### Avoid Re-Abstracting The World

The goal is not a huge generalized execution framework in one cycle. The goal is a clean, truthful execution path for the four known theatre check families using TREMOR and CORONA as first-class fixtures.

---

## After This Cycle Ships

1. TREMOR and CORONA become executable verification fixtures, not just compile fixtures
2. theatre certificates can show real executed deterministic results
3. Cycle 038 can compare theatres with stronger local provenance already in place
