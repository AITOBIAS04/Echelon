# Sprint Plan: Two-Rail Deterministic Product Theatres (Cycle-033)

> **Cycle**: cycle-033
> **PRD**: `grimoires/loa/prd.md`
> **SDD**: `grimoires/loa/sdd.md`
> **Branch**: `feature/two-rail-theatres`
> **Total sprints**: 2

---

## Sprint 1: Deterministic Scoring Layer (global: sprint-30)

**Goal**: Build the three deterministic scorer functions, the oracle adapter, and comprehensive unit tests. After this sprint, each scorer can be called standalone and produces correct binary scores for all fixture records.

### Tasks

#### Task 1.1: Create `theatre/scoring/` package with oracle adapter

**File**: `theatre/scoring/__init__.py`, `theatre/scoring/deterministic_oracle.py`

- Create `theatre/scoring/__init__.py` exporting all scorers + `DeterministicOracleAdapter`
- Create `DeterministicOracleAdapter` implementing `OracleAdapter` protocol
  - `async def invoke(self, input_data: dict) -> dict` — returns `input_data` as-is (passthrough)

**Acceptance criteria**:
- `from theatre.scoring import DeterministicOracleAdapter` works
- Adapter satisfies `OracleAdapter` protocol
- `invoke()` returns input data unchanged

---

#### Task 1.2: Implement `WaterfallScorer`

**File**: `theatre/scoring/waterfall_scorer.py`

Implements `ScoringFunction` protocol with 5 binary checks:

| Check | Method |
|-------|--------|
| `waterfall_arithmetic` | Verify split amounts sum to gross and match expected |
| `noi_pool_conservation` | `abs(sum(allocations) - noi_pool) <= 0.01` |
| `rounding_policy_compliance` | All amounts equal `Decimal(amount).quantize('0.01', ROUND_HALF_UP)` |
| `cap_table_consistency` | `abs(per_token * supply - distributions) <= 0.01` |
| `ledger_reconciliation` | `abs(sum(splits) - gross_amount) <= 0.01` |

**Acceptance criteria**:
- All 10 waterfall fixture records score 1.0 on all 5 criteria
- Implements `async def score(criteria_id, ground_truth, oracle_output) -> float`
- Uses `decimal.Decimal` for financial arithmetic

---

#### Task 1.3: Implement `EscrowScorer`

**File**: `theatre/scoring/escrow_scorer.py`

5 binary checks:

| Check | Method |
|-------|--------|
| `required_evidence_present` | `required_types ⊆ provided_doc_types` |
| `signature_policy_satisfied` | `required_roles ⊆ attestation_roles` |
| `validity_window_respected` | `evidence_timestamp` is parseable ISO-8601 |
| `release_amount_correct` | `abs(release_pct * balance - expected_amount) <= 0.01` |
| `idempotency` | Milestone ID appears exactly once in schedule |

**Acceptance criteria**:
- All 10 escrow fixture records score 1.0 on all 5 criteria
- Implements `ScoringFunction` protocol

---

#### Task 1.4: Implement `ReconciliationScorer`

**File**: `theatre/scoring/reconciliation_scorer.py`

5 binary checks:

| Check | Method |
|-------|--------|
| `bank_ref_match` | `settlement_reference` found in bank transactions |
| `bucket_sum_matches_gross` | `abs(sum(splits) - gross_amount) <= 0.01` |
| `bucket_destination_valid` | Each split destination in `allowed_destinations` |
| `event_log_complete` | `len(events) == len(splits)` with matching entries |
| `exceptions_correct` | `expected.exceptions == []` for happy path |

**Acceptance criteria**:
- All 10 reconciliation fixture records score 1.0 on all 5 criteria
- Implements `ScoringFunction` protocol

---

#### Task 1.5: Unit tests for all three scorers

**Files**: `tests/theatre/test_waterfall_scorer.py`, `tests/theatre/test_escrow_scorer.py`, `tests/theatre/test_reconciliation_scorer.py`

Per scorer:
- Happy path: all 5 checks pass on fixture data
- Per-check failure: synthetic record that fails exactly one check (e.g., wrong split amount, missing evidence doc, bad bank ref)
- Rounding boundary: amount at tolerance edge (e.g., £0.005 difference)
- Unknown criteria_id returns 0.0

**Acceptance criteria**:
- All three test files pass
- Each scorer has ≥10 tests
- Edge cases cover each of the 5 criteria failing independently

---

## Sprint 2: Runner Script + Integration Tests (global: sprint-31)

**Goal**: Wire the scoring layer into the existing replay engine via a runner script, produce three schema-valid certificates, and verify determinism.

### Tasks

#### Task 2.1: Create `scripts/run_two_rail_theatres.py`

**File**: `scripts/run_two_rail_theatres.py`

CLI runner that:
1. Parses args (`--all`, `--theatre <id>`, `--output-dir`, `--verbose`)
2. Loads template + dataset from `theatre/fixtures/two_rail_theatres_v0_1/`
3. Validates template against `echelon_theatre_schema_v2.json`
4. Converts fixture records → `GroundTruthEpisode[]`
5. Computes dataset hash, populates template runtime fields
6. Creates `CommitmentReceipt`
7. Builds `ReplayEngine` with `DeterministicOracleAdapter` + scorer
8. Runs replay
9. Assigns tier, builds evidence bundle
10. Issues `TheatreCalibrationCertificate`
11. Validates certificate against `echelon_certificate_schema.json`
12. Writes to `output/certificates/{template_id}.json`

**Acceptance criteria**:
- `python scripts/run_two_rail_theatres.py --all` produces 3 certificate files
- `python scripts/run_two_rail_theatres.py --theatre distribution_waterfall_v1` produces 1 certificate
- All certificates validate against schema
- No network calls required
- Runs in <10 seconds total

---

#### Task 2.2: Integration + determinism tests

**File**: `tests/theatre/test_two_rail_integration.py`

Tests:
- **Full pipeline**: Run all 3 theatres programmatically → 3 certificates → schema-valid
- **Score correctness**: All 30 episodes score 1.0 composite (happy-path fixtures)
- **Determinism**: Run pipeline twice → identical certificate hashes, evidence bundle hashes
- **Single theatre**: Run one theatre → correct certificate

**Acceptance criteria**:
- All integration tests pass
- Determinism test proves identical hashes on two runs
- No flaky tests (pure deterministic)

---

#### Task 2.3: Final verification and cleanup

- Run full test suite (existing + new) to verify zero regressions
- Run `--all --verbose` to produce final certificates
- Verify evidence bundles contain all required files

**Acceptance criteria**:
- Existing 93 observer tests + 24 ingester tests still pass
- All new scorer + integration tests pass
- 3 certificates + 3 evidence bundles written

---

## Sprint Summary

| Sprint | Global ID | Tasks | Est. Files | Goal |
|--------|-----------|-------|-----------|------|
| 1 | sprint-30 | 5 | 7 new | Scoring layer + unit tests |
| 2 | sprint-31 | 3 | 2 new | Runner + integration + determinism |
