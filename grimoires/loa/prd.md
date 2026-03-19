# PRD — Cycle-038c: Orchestrated Scanner Handoff

**Cycle:** cycle-038c
**Date:** 19 March 2026
**Depends on:** Cycle-038, Cycle-038a, Cycle-038b
**Sprints:** 4 (0–3)
**Builder:** Loa (backend only)
**Priority:** Pure-function classification first, DB handoff deferred
**Planning source:** 038b produces scanner-ready candidates; the P2 Codex finding confirms the next step is to exercise real classification logic, not just verify shape compatibility

---

## 1. Problem Statement

### 1.1 The Orchestrator Now Produces Good Inputs

Cycle 038b completed the operational preparation layer for external theatres:

- enriched fixture extraction (pass + fail scenarios)
- deterministic check execution
- comparison bundle generation with shared identity
- candidate generation (same_event + overlap_scope)
- builder feedback (READY / DEGRADED / BLOCKED)

35 tests confirm the orchestration layer works. The Codex review validated it as solid.

### 1.2 The Remaining Gap Is Classification, Not Shape

038b sprint-3 proved that orchestrated candidates have the right shape for scanning. What it did not exercise is the actual classification logic:

- does settlement divergence between two theatre bundles get detected?
- does oracle inconsistency across bundles get flagged?
- is "no paradox" an explicit, observable result?

### 1.3 The Real Scanner Boundary Is Larger Than Expected

The existing Cycle 038 `CrossTheatreParadoxScanner` is:

- **async** (SQLAlchemy 2.0 + PostgreSQL)
- **DB-dependent** (reads FactAnchors, FactAnchorLinks, OracleResponses)
- **triggered by FactAnchor.link_theatre()** or explicit `scan_coherence_group()`
- **produces persisted CrossTheatreParadox records** with WingFlap side effects

The 038b orchestrator output is:

- **synchronous, pure** (no DB, no async)
- **produces ComparisonCandidateSet** with bundle pairs
- **has no concept of FactAnchors** or link insertion

The handoff is not "pass candidates to scanner." It is "translate orchestration results into the scanner's input surface."

### 1.4 Progressive Tier Strategy

Following the same approach as 038b's extraction tiers:

| Tier | Approach | DB Required | This Cycle |
|------|----------|-------------|------------|
| V1 | Pure-function classification adapter | No | Yes |
| V2 | Full FactAnchor bridge + real scanner invocation | Yes | Future |

V1 extracts the 038 scanner's four detection patterns (SETTLEMENT_DIVERGENCE, ORACLE_INCONSISTENCY, TEMPORAL_DRIFT, SCOPE_OVERLAP_GAP) into pure functions that operate directly on comparison bundles. This proves classification logic end-to-end without requiring DB infrastructure.

V2 (future) builds the FactAnchor bridge: candidates → anchor creation → link insertion → real async scanner → persisted paradox records.

### 1.5 The Goal Of 038c

Exercise real paradox classification against orchestrated external theatre output:

1. **Pure-function adapter**: Extract the 4 detection patterns from the 038 scanner into functions that operate on `ExecutedTheatreComparisonBundle` pairs
2. **End-to-end classification**: Orchestrator → candidates → adapter → paradox/no-paradox results
3. **Both outcome paths**: Aligned bundles produce explicit no-paradox; divergent bundles produce typed paradox findings
4. **Provenance**: Classification results preserve construct slugs, match keys, evidence

---

## 2. Product Contracts

### 2.1 Pure-Function Classification Adapter

Cycle 038c must add a classification layer that takes comparison bundle pairs and produces paradox/no-paradox results using the same logic as the real 038 scanner.

The adapter:

- accepts a `ComparisonCandidateSet` (from 038b orchestrator output)
- for each candidate pair, evaluates the same 4 detection patterns the real scanner uses
- returns structured results per candidate

Detection patterns (from `cross_theatre_paradox_scanner.py`):

| Pattern | What It Detects | Input From Bundle |
|---------|----------------|-------------------|
| SETTLEMENT_DIVERGENCE | Opposite settlement outcomes | `settlement_state` + `settlement_outcomes` |
| ORACLE_INCONSISTENCY | Oracle value deltas > threshold | `oracle_values` from execution summary |
| TEMPORAL_DRIFT | Settlement timing divergence | Bundle timestamps / execution timing |
| SCOPE_OVERLAP_GAP | Missing expected coverage | Scope keys present vs expected |

### 2.2 No-Paradox Is A First-Class Result

The adapter must treat "no paradox found" as a successful, explicit result — not an absence of output. Every scanned candidate produces either:

- zero or more typed paradox findings, OR
- an explicit no-paradox result with the evidence that was evaluated

### 2.3 Expected Positive Cases

At least one exercised positive paradox for each of the two most likely patterns:

1. **Settlement divergence**: One bundle SETTLED, one DISPUTED (or different settlement outcomes)
2. **Oracle inconsistency**: Same event, different oracle values exceeding threshold

These use TREMOR/CORONA orchestrated bundles with enriched fixtures that naturally produce divergence (odd-index fail scenarios from 038b).

### 2.4 Provenance Preservation

Classification results must preserve:

- source construct slugs (e.g., "tremor", "corona")
- candidate match type (same_event vs overlap_scope)
- match keys (event_keys or scope_keys)
- per-pattern evidence (settlement outcomes, oracle deltas, etc.)
- severity classification (INFO / WATCH / MATERIAL) following 038 conventions

### 2.5 Adapter Alignment With Real Scanner

The adapter must use the same thresholds, severity logic, and classification rules as the real 038 scanner. Specifically:

- Oracle tolerance: 0.1 (10%) — from `cross_theatre_paradox_scanner.py`
- Temporal drift window: 24 hours
- Severity rules: same-source oracle delta = MATERIAL, cross-source = WATCH, settlement divergence = MATERIAL

This ensures V2 (future DB bridge) can replace the adapter without changing classification behavior.

---

## 3. What This Cycle Does NOT Do

- **Does NOT modify the existing Cycle 038 scanner.** The adapter extracts patterns; it does not change the original.
- **Does NOT require DB persistence or async.** V1 is pure-function.
- **Does NOT build the FactAnchor bridge.** That is V2 scope.
- **Does NOT require live oracle polling.**
- **Does NOT redesign 038b orchestration.**

---

## 4. Acceptance Criteria

1. A pure-function adapter can classify comparison bundle pairs using the same 4 detection patterns as the 038 scanner
2. At least one aligned/no-paradox scenario is exercised end to end (orchestrator → adapter → explicit no-paradox)
3. At least one settlement divergence paradox is exercised end to end
4. At least one oracle inconsistency paradox is exercised end to end
5. No-paradox and paradox outcomes are both represented as explicit result types
6. Classification results preserve construct slugs, match keys, and per-pattern evidence
7. Adapter uses the same thresholds and severity rules as the real 038 scanner
8. TREMOR and CORONA participate as real external fixtures in at least one end-to-end path
9. ≥28 new tests pass

---

## 5. Test Plan

| Area | Tests | Coverage |
|---|---|---|
| Scan result schemas | 5 | ScanRequest, ScanResult, CandidateScanOutcome, ParadoxFinding shapes |
| Settlement divergence | 6 | SETTLED vs DISPUTED, matching settlements (no paradox), severity = MATERIAL |
| Oracle inconsistency | 6 | Delta > tolerance, delta ≤ tolerance (no paradox), same-source vs cross-source severity |
| Temporal drift | 3 | Within window (no paradox), beyond window, severity rules |
| Scope overlap gap | 2 | Missing scope coverage, full coverage (no paradox) |
| No-paradox explicit results | 3 | Aligned bundles, no findings, explicit empty output |
| End-to-end orchestrator → adapter | 4 | TREMOR→scan, CORONA→scan, TREMOR+CORONA cross-theatre, provenance preservation |
| Regression | 3 | No breakage to existing 038b tests |
| **Total** | **~32** | |

---

## 6. Why This Matters

Cycle 038b proved Echelon can operationally prepare external theatres.

Cycle 038c proves the paradox engine can classify what was prepared.

That is the moment when external theatre comparison stops being "prepared for scanning" and becomes "actually classified."

The progressive tier strategy means V1 ships fast with pure functions, and V2 (DB bridge) follows when the full async handoff is needed.
