# Engineer Feedback: Sprint 24 (Cycle-012, Sprint 2) -- Resolution + Settlement + Certificate Delivery

> Reviewer: Senior Technical Lead | Date: 2026-03-03
> Decision: **All good**

## Review Summary

All 10 Sprint 2 tasks meet acceptance criteria. 30 new tests pass (target: 25+), 83 total service/schema tests pass, 369 scoped regression tests pass. Code is clean, well-structured, and correctly delegates to existing subsystems without modifying them. The MEDIUM-1 fix is minimal and correct. The E2E test is thorough and exercises the full lifecycle.

## Test Results (Independently Verified)

```
Sprint 2 tests:          30 passed, 0 failed
All services/schemas:    83 passed, 0 failed
Scoped regression:      369 passed, 0 failed
Total:                  452 passed, 0 failed
```

## Acceptance Criteria Verification

### Task 1: Theatre Evidence Collector (`backend/services/theatre_evidence.py`)

- [x] `collect_heartbeat()` delegates to reality provider's `get_signal()`
- [x] `EvidenceSnapshot` captures oracle_output, evidence_bundles, collection_results, coverage
- [x] Evidence stored in-memory as list of snapshots
- [x] Source coverage percentage computed correctly (successful/total)
- [x] No modifications to `backend/osint/` pipeline code

### Task 2: Theatre Resolution Engine (`backend/services/theatre_resolution.py`)

- [x] Resolution delegates to existing Composed Oracle components (no modification)
- [x] Oracle evaluation returns discrete `winning_outcome_index` for 3-outcome market
- [x] `oracle_output_id` format: `"{theatre_id}_{epoch_ms}"`
- [x] Composite score computed with provisional corroboration (0.7 penalty)
- [x] Counter-signal results all UNAVAILABLE / INTELLIGENCE_GAP (11 entries)
- [x] Evidence bundle hash computed via OracleOutput.bundle_hash (SHA-256)
- [x] Boundary tests: score=0.7 -> outcome 0, score=0.3 -> outcome 1 -- VERIFIED
- [x] Generic n-outcome fallback correctly handles edge cases (1.0, 0.0)

### Task 3: Certificate Pipeline (`backend/services/certificate_pipeline.py`)

- [x] Certificate conforms to v1.0.0 schema (all 16 fields present)
- [x] `evidence_bundle_hash` is valid SHA-256 hex (64 chars)
- [x] `corroboration_status` reports `minimum_met: false`, `penalty_factor: 0.7`
- [x] `counter_signal_results` has exactly 11 entries (all UNAVAILABLE)
- [x] `verification_tier` is "UNVERIFIED"
- [x] `verify()` runs all 21 checks and returns pass/fail list
- [x] Certificate passes all 21 `echelon_verify` checks
- [x] Certificate JSON roundtrips through canonical JSON without change

### Task 4: RLMF Export Generator (`backend/services/rlmf_export.py`)

- [x] RLMF export `schema_version` is "2.0.1"
- [x] `MarketEpoch` captures prices and x_vector per tick
- [x] `AgentTrace` captures per-agent decision traces and P&L
- [x] Brier score formula correct: `(1/n) * sum((p_i - o_i)^2)` -- verified with perfect, worst, uniform test cases
- [x] ECE computed across probability bins (single-event degenerate case, correctly documented)
- [x] Per-agent P&L matches settlement report
- [x] Export linked to Theatre via `oracle_output_id`

### Task 5: Sponsor Delivery Package (`backend/services/sponsor_delivery.py`)

- [x] `SponsorDeliveryPackage` contains all 4 deliverables: certificate, evidence_bundle, rlmf_export, commitment_hash
- [x] Certificate serialised as JSON dict
- [x] Evidence bundle includes HTTP transcript receipts, collection timestamps, source coverage
- [x] RLMF export serialised as JSON dict
- [x] `echelon_status_url` format: `echelon://status/{theatre_id}`
- [x] All fields are non-None and non-empty

### Task 6: echelon_status Theatre Integration (`backend/services/theatre_status.py`)

- [x] During TRADING: returns current prices, evidence coverage %, sources online/offline
- [x] After SETTLEMENT: returns certificate_state "VALID", composite_score, counter_signal_status
- [x] `verification_tier` is "UNVERIFIED" for local-mode Theatre
- [x] TTL set to 300 seconds
- [x] No modifications to `backend/engines/status.py`

### Task 7: MEDIUM-1 Fix (`backend/engines/paradox.py`)

- [x] `ParadoxEngine.scan()` returns None when `signal.p_reality is None`
- [x] `LogicGapCalculator.compute()` is NOT modified
- [x] Guard is placed in `scan()` after `get_signal()` (line 106)
- [x] This is the ONLY modification to `backend/engines/paradox.py` (verified via git diff)
- [x] No other files in `backend/engines/` modified (verified via git diff)
- [x] Existing Paradox Engine tests still pass (369 regression tests)
- [x] MEDIUM-1 test added in E2E test file: `test_medium_1_fix_p_reality_none`

### Task 8: Resolution Engine Tests (`backend/services/tests/test_theatre_resolution.py`)

- [x] 10 test cases covering outcome determination, oracle evaluation, boundaries
- [x] Tests use mock evidence collector and mock OSINT components
- [x] Tests verify `winning_outcome_index` for each score range (0.8->0, 0.5->1, 0.1->2)
- [x] Boundary tests: 0.7->0, 0.3->1
- [x] Tests verify corroboration penalty applied (corroboration_met=False)
- [x] Counter-signal scaffolding: all 11 UNAVAILABLE

### Task 9: Certificate Pipeline Tests (`backend/services/tests/test_certificate_pipeline.py`)

- [x] 12 test cases covering certificate schema and verification
- [x] Tests verify all 21 verifier checks pass
- [x] Tests verify evidence_bundle_hash is valid SHA-256
- [x] Tests verify canonical JSON roundtrip
- [x] Tests verify corroboration_status fields
- [x] Tests verify counter-signal results exactly 11 UNAVAILABLE

### Task 10: E2E Integration Test (`backend/services/tests/test_sponsored_theatre_e2e.py`)

- [x] Full lifecycle executes: creation -> commit -> trading -> evidence -> resolution -> settlement -> certificate -> RLMF -> delivery -> status
- [x] >20 stub agent trades across 6 agents in 10 ticks
- [x] Bounded-loss invariant verified: `market_maker_pnl >= -b * ln(n)`
- [x] Certificate passes all 21 `echelon_verify` checks
- [x] RLMF export conforms to schema v2.0.1
- [x] Delivery package contains all 4 deliverables
- [x] `echelon_status` returns VALID certificate state post-settlement
- [x] All evidence uses mock HTTP responses only
- [x] Uses Companies House reference fixture from SDD Section 13
- [x] 56 assertions across the full test file (target was 25+)

## Constraint Compliance

| Constraint | Status | Evidence |
|-----------|--------|----------|
| Zero modifications to `backend/market/` | PASS | `git diff HEAD -- backend/market/` empty |
| Zero modifications to `backend/osint/` | PASS | `git diff HEAD -- backend/osint/` empty |
| Zero modifications to `backend/chain/` | PASS | `git diff HEAD -- backend/chain/` empty |
| Only `backend/engines/paradox.py` modified | PASS | `git diff HEAD -- backend/engines/` shows only paradox.py |
| `from __future__ import annotations` in all files | PASS | All 6 new source files verified |
| No new runtime dependencies | PASS | Only stdlib + existing deps used |
| In-memory only | PASS | No new database tables or persistent storage |
| Mock-only OSINT testing | PASS | No real HTTP calls in any test |

## Adversarial Analysis

### MEDIUM-1 Fix Correctness

The fix adds a 3-line guard (plus 3 comment lines) after `get_signal()` and before `compute()`. The guard checks `if signal.p_reality is None: return None`. This correctly short-circuits the scan before the None value reaches `LogicGapCalculator.compute()`, which would otherwise call `abs(p_market - None)` and raise `TypeError`. The fix is:

1. **Minimal** -- only 1 conditional added
2. **Backward-compatible** -- `scan()` already returns `None` for disabled mode and ungated state
3. **Correct** -- the `None` return signals "no reading available" which is semantically accurate for stale evidence

All 369 existing engine/market/osint tests pass, confirming no regression.

### Resolution Engine Boundary Analysis

- Score = 0.7 exactly: maps to outcome 0. Tested explicitly in `test_determine_winning_outcome_boundary_0_7`.
- Score = 0.3 exactly: maps to outcome 1 (`>= 0.3`). Tested explicitly in `test_determine_winning_outcome_boundary_0_3`.
- Score = 0.0: maps to outcome 2 (`< 0.3`). Not tested directly but covered by `test_determine_winning_outcome_low_score` (0.1).
- Score = 1.0: generic case returns 0. The 3-outcome case also returns 0. Correct.

### Certificate 21 Checks Analysis

All 21 checks are implemented and tested. Two observations:

1. **Check 5** ("evidence_bundle_hash recomputable") degrades to a hex validity check identical to Check 4 because the verify method does not have access to the original evidence bundles. A comment on line 151 acknowledges this. Acceptable for v1.0.0 -- a standalone verifier would need the original bundles.
2. **Check 19** ("winning_outcome is valid index") only validates `>= 0` but does not check the upper bound. The certificate schema does not carry `n_outcomes`, so this cannot be validated without external context. The winning_outcome_label serves as an implicit sanity check. Acceptable.

### E2E Test Scrutiny

The E2E test (`test_full_lifecycle_e2e`) exercises the FULL lifecycle:
1. Creates a Companies House Theatre with the reference fixture
2. Commits parameters, verifies commitment hash
3. Spawns 6 stub agents, runs 10 trading ticks
4. Collects mock evidence at 3 points
5. Triggers resolution via Composed Oracle
6. Settles market, verifies bounded-loss invariant (`market_maker_pnl >= -b*ln(n)`)
7. Generates certificate, runs all 21 echelon_verify checks
8. Generates RLMF export, validates schema v2.0.1
9. Assembles delivery package with 4 deliverables
10. Queries echelon_status, verifies VALID certificate state

No lifecycle steps are skipped. The test exercises real LMSR trading (not mocked), real settlement, real certificate generation, and real verification.

## Advisory Notes (Non-Blocking)

### ADV-1: Unused Imports (Cosmetic)

Carried from Sprint 1. Four files have unused imports:
- `theatre_evidence.py`: `import time`, `Optional`
- `theatre_resolution.py`: `import hashlib`, `import time`, `Optional`
- `rlmf_export.py`: `Optional`
- `theatre_status.py`: `Optional`

All `Optional` imports are unnecessary because `from __future__ import annotations` enables `X | None` syntax. Not a functional issue.

### ADV-2: Private Attribute Access in `theatre_status.py`

Line 92 accesses `evidence_collector._committed_sources` (private attribute). Would be cleaner to add a `@property` to `TheatreEvidenceCollector`. Acceptable for in-memory MVP.

### ADV-3: ECE Single-Event Degenerate Case

The ECE computation treats every epoch observation as the same event (which resolved to 1). This is a known limitation of single-market ECE. The comment on line 200 documents this. True calibration measurement requires aggregation across multiple markets. The RLMF export captures the raw epoch data so downstream systems can compute multi-market ECE. Acceptable.

## Files Reviewed

| File | Lines | Verdict |
|------|-------|---------|
| `backend/services/theatre_evidence.py` | 113 | CLEAN |
| `backend/services/theatre_resolution.py` | 189 | CLEAN |
| `backend/services/certificate_pipeline.py` | 335 | CLEAN |
| `backend/services/rlmf_export.py` | 227 | CLEAN |
| `backend/services/sponsor_delivery.py` | 141 | CLEAN |
| `backend/services/theatre_status.py` | 137 | CLEAN |
| `backend/engines/paradox.py` (MODIFIED) | 246 | CLEAN (MEDIUM-1 fix only) |
| `backend/services/tests/test_theatre_resolution.py` | 378 | CLEAN |
| `backend/services/tests/test_certificate_pipeline.py` | 295 | CLEAN |
| `backend/services/tests/test_sponsored_theatre_e2e.py` | 799 | CLEAN |

## Verdict

**APPROVED.** All 10 tasks meet acceptance criteria. 30 new tests pass. 369 scoped regression tests pass. MEDIUM-1 fix is minimal and correct. Certificate passes all 21 echelon_verify checks. E2E test exercises the full lifecycle without skipping steps. Three advisory notes (unused imports, private attribute access, ECE degenerate case) -- all non-blocking.
