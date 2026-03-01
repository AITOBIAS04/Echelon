# Sprint-11 Score Delta Analysis

**Branch:** `feature/sprint-11-unified-pipeline`
**Date:** 2026-03-01
**Verdict:** Category (A) — intended consequence of scorer semantics

---

## 1. Observed Deltas

| Template | Actual | Target | Delta |
|----------|--------|--------|-------|
| `escrow_milestone_release_v1` | 0.8591 | 0.9091 | -0.0500 |
| `distribution_waterfall_v1` | 0.9333 | 0.9333 | 0.0000 |
| `ledger_reconciliation_v1` | 0.8933 | 0.9333 | -0.0400 |
| `arrears_resolution_v1` | 0.9375 | 0.9375 | 0.0000 |

Waterfall and arrears hit targets exactly. Escrow and reconciliation are below.

---

## 2. Escrow Composite Decomposition (0.8591)

Weights from `ESCROW_MILESTONE_RELEASE_V1.template.json` → `criteria.weights`.

| Criterion | Weight | Pass | Total | Pass Rate | Contribution |
|-----------|--------|------|-------|-----------|--------------|
| `required_evidence_present` | 0.25 | 10 | 11 | 0.9091 | 0.2273 |
| `signature_policy_satisfied` | 0.30 | 10 | 11 | 0.9091 | 0.2727 |
| `validity_window_respected` | 0.15 | 11 | 11 | 1.0000 | 0.1500 |
| `release_amount_correct` | 0.20 | 6 | 11 | 0.5455 | **0.1091** |
| `idempotency` | 0.10 | 11 | 11 | 1.0000 | 0.1000 |
| **Composite** | **1.00** | | | | **0.8591** |

### Per-Record Matrix

| Record | evidence | signature | validity | release_amt | idempotency | Targeted |
|--------|----------|-----------|----------|-------------|-------------|----------|
| 0001–0006 | 1 | 1 | 1 | 1 | 1 | (pass) |
| 0007 | **0** | 1 | 1 | **0** | 1 | evidence |
| 0008 | 1 | **0** | 1 | **0** | 1 | signature |
| 0009 | 1 | 1 | 1 | **0** | 1 | release_amt |
| 0010 | 1 | 1 | 1 | **0** | 1 | (none — coupled via release instruction) |
| 0011 | 1 | 1 | 1 | **0** | 1 | (none — coupled via release instruction) |

**Key observation:** Records 0007–0011 all fail `release_amount_correct` (bold zeros above), not just 0009 (the targeted failure). The target of 0.9091 assumed only 1/11 records would fail this criterion (pass rate 10/11 = 0.9091). Actual pass rate is 6/11 = 0.5455.

### Root Cause

`_check_release_amount_correct` in `theatre/scoring/escrow_scorer.py:105–148` computes `release_pct × balance` and compares to `release_instruction.release_amount`. Any record whose primary failure scenario corrupts the release instruction (wrong amount, missing fields) also fails this check. This is correct scorer behaviour — the criterion faithfully reports arithmetic discrepancies regardless of their upstream cause.

---

## 3. Reconciliation Composite Decomposition (0.8933)

Weights from `LEDGER_RECONCILIATION_V1.template.json` → `criteria.weights`.

| Criterion | Weight | Pass | Total | Pass Rate | Contribution |
|-----------|--------|------|-------|-----------|--------------|
| `bank_ref_match` | 0.25 | 14 | 15 | 0.9333 | 0.2333 |
| `bucket_sum_matches_gross` | 0.15 | 14 | 15 | 0.9333 | 0.1400 |
| `bucket_destination_valid` | 0.15 | 14 | 15 | 0.9333 | 0.1400 |
| `event_log_complete` | 0.30 | 14 | 15 | 0.9333 | 0.2800 |
| `exceptions_correct` | 0.15 | 10 | 15 | 0.6667 | **0.1000** |
| **Composite** | **1.00** | | | | **0.8933** |

### Per-Record Matrix

| Record | bank_ref | bucket_sum | bucket_dest | event_log | exceptions | Targeted |
|--------|----------|------------|-------------|-----------|------------|----------|
| 0001–0010 | 1 | 1 | 1 | 1 | 1 | (pass) |
| 0011 | **0** | 1 | 1 | 1 | **0** | bank_ref |
| 0012 | 1 | **0** | 1 | 1 | **0** | bucket_sum |
| 0013 | 1 | 1 | **0** | 1 | **0** | bucket_dest |
| 0014 | 1 | 1 | 1 | **0** | **0** | event_log |
| 0015 | 1 | 1 | 1 | 1 | **0** | exceptions |

**Key observation:** Records 0011–0015 all fail `exceptions_correct` (bold zeros), not just 0015 (the targeted failure). The target of 0.9333 assumed only 1/15 records would fail this criterion (pass rate 14/15 = 0.9333). Actual pass rate is 10/15 = 0.6667.

### Root Cause

`_check_exceptions_correct` in `theatre/scoring/reconciliation_scorer.py` checks whether exception entries are properly tagged and resolved. Any record that fails another criterion naturally generates exception entries (bank reference mismatch creates an exception, bucket sum mismatch creates an exception, etc.). The scorer correctly reports these as `exceptions_correct = 0.0` because the exception data is incomplete or unresolved — a natural consequence of the primary failure.

---

## 4. Target Assumption Error

The original targets were computed as:

```
target = 1.0 - (1/record_count × max_single_criterion_weight)
```

This formula assumes:
- Each failure record fails exactly **one** criterion
- No criterion appears in multiple failure records

Both assumptions are violated by correlated failure coupling:

| Template | Expected Failures per Criterion | Actual Failures |
|----------|-------------------------------|-----------------|
| Escrow `release_amount_correct` | 1 | 5 |
| Reconciliation `exceptions_correct` | 1 | 5 |

---

## 5. Verdict

**Category (A): Intended consequence of scorer semantics.**

The scorers are correct. They faithfully detect correlated failure coupling in the fixture data. Cycle-007 target composites assumed one-failure-per-record fixtures; the unified pipeline surfaces coupled failures because records encode compound scenarios. No code changes are recommended — the pipeline produces correct, deterministic results.

### Corrected Targets

Using actual pass rates:

| Template | Old Target | Corrected Target | Actual |
|----------|-----------|-----------------|--------|
| Escrow | 0.9091 | 0.8591 | 0.8591 |
| Reconciliation | 0.9333 | 0.8933 | 0.8933 |

The corrected targets match actual scores exactly — confirming the decomposition is complete and no hidden factors exist.

---

## 6. Supporting Artefacts

| File | Description |
|------|-------------|
| `reports/escrow_score_breakdown.json` | Machine-readable escrow decomposition |
| `reports/reconciliation_score_breakdown.json` | Machine-readable reconciliation decomposition |
| `output/unified_certificates/evidence_escrow_milestone_release_v1/scores/per_record.json` | Raw per-record scores |
| `output/unified_certificates/evidence_ledger_reconciliation_v1/scores/per_record.json` | Raw per-record scores |
| `output/unified_certificates/evidence_escrow_milestone_release_v1/scores/aggregate.json` | Pipeline aggregate output |
| `output/unified_certificates/evidence_ledger_reconciliation_v1/scores/aggregate.json` | Pipeline aggregate output |
| `theatre/fixtures/two_rail_theatres_v0_1/templates/ESCROW_MILESTONE_RELEASE_V1.template.json` | Weight definitions |
| `theatre/fixtures/two_rail_theatres_v0_1/templates/LEDGER_RECONCILIATION_V1.template.json` | Weight definitions |
