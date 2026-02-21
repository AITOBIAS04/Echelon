# Echelon Cycle-033: Two-Rail Deterministic Product Theatres

> **Goal**: Build deterministic scoring functions for three Two-Rail marketplace Product Theatres and produce calibration certificates from existing fixtures.
> **Scope**: Scoring engine + runner script + tests. No LLM scoring — all checks are arithmetic/policy/binary.
> **Expected output**: Three `CalibrationCertificate` JSON files with real scores from deterministic replay.

---

## What already exists

### Replay Engine (Cycle-031)
- `ReplayEngine` executes Product Theatres: commit → invoke → score → certify
- `OracleAdapter` interface with HTTP, local, and mock implementations
- `OracleInvocationRequest` / `OracleInvocationResponse` standardised envelope
- `CommitmentReceipt` with canonical JSON (RFC 8785) commitment hash
- `CalibrationCertificate` issuance with evidence bundle
- `TierAssigner` with v0 verification tier rules
- `canonical_json()` utility

### Integration Pipeline (Cycle-032)
- `GitHubIngester` for live data ingestion
- Runner script pattern (`scripts/run_observer_theatre.py`)
- Evidence bundle generation with deterministic hashing
- Schema validation gates (certificate + RLMF)
- Determinism smoke test pattern

### Two-Rail Fixtures (already saved)
Located at: `theatre/fixtures/two_rail_theatres_v0_1/`

**Templates** (3):
- `DISTRIBUTION_WATERFALL_V1_template.json` — 5 criteria
- `ESCROW_MILESTONE_RELEASE_V1_template.json` — 5 criteria
- `LEDGER_RECONCILIATION_V1_template.json` — 5 criteria

**Datasets** (3 × 10 records each):
- `waterfall_fixtures_10.json`
- `escrow_fixtures_10.json`
- `reconciliation_fixtures_10.json`

---

## What this cycle builds

### 1. Deterministic Scorer: Distribution Waterfall

Pure Python function. No LLM. Takes inputs + policy → computes expected outputs → compares.

**Input per episode**: `payment.json` + `noi_report.json` + `waterfall_policy.json` + `cap_table_snapshot.json`
**Expected output**: `distribution_statement.json`

Five binary checks (each scores 1.0 or 0.0):
- `waterfall_arithmetic`: computed bucket amounts match policy percentages applied to inputs
- `noi_pool_conservation`: sum of all NOI pool outflows equals NOI amount (within rounding tolerance, e.g., £0.01)
- `rounding_policy_compliance`: all amounts use consistent rounding mode (e.g., ROUND_HALF_UP to 2dp)
- `cap_table_consistency`: per_token_amount × token_supply == distribution_pool (within rounding tolerance)
- `ledger_reconciliation`: sum of all payment splits equals gross_amount

### 2. Deterministic Scorer: Escrow Milestone Release

**Input per episode**: `escrow_state.json` + `milestone_schedule.json` + `milestone_evidence/*.json` + `attestations/*.json`
**Expected output**: `release_instruction.json`

Five binary checks:
- `required_evidence_present`: all `evidence_required` entries in the milestone have matching evidence documents
- `signature_policy_satisfied`: required signer roles are present in attestations
- `validity_window_respected`: evidence timestamps fall within the milestone's allowed window
- `release_amount_correct`: computed release equals `release_pct × escrow_balance`
- `idempotency`: same milestone ID cannot trigger release twice in the dataset

### 3. Deterministic Scorer: Ledger Reconciliation

**Input per episode**: `bank_statement_slice.json` + `payment.json` + `event_log.jsonl`
**Expected output**: `reconciliation_result.json`

Five binary checks:
- `bank_ref_match`: every payment.settlement_reference has a matching bank statement entry
- `bucket_sum_matches_gross`: sum of payment.splits equals payment.gross_amount
- `bucket_destination_valid`: each split.destination_ref is in the permitted destinations list
- `event_log_complete`: every split produces exactly one ledger event
- `exceptions_correct`: mismatches generate the correct ExceptionEvent.type and policy_response

### 4. Runner Script

`scripts/run_two_rail_theatres.py` — single entry point that:
1. Loads all three templates from `theatre/fixtures/two_rail_theatres_v0_1/templates/`
2. Loads corresponding fixture datasets from `theatre/fixtures/two_rail_theatres_v0_1/datasets/`
3. For each theatre:
   a. Creates and commits the Theatre Template
   b. Runs the deterministic scorer across all 10 episodes
   c. Collects per-episode binary scores
   d. Issues a CalibrationCertificate
   e. Validates against `echelon_certificate_schema.json`
4. Writes certificates to `output/certificates/`
5. Writes evidence bundles to `output/evidence_bundles/`

CLI:
```bash
python scripts/run_two_rail_theatres.py --all --verbose
python scripts/run_two_rail_theatres.py --theatre distribution_waterfall_v1
```

### 5. Tests

- Unit tests for each scorer function (known-good inputs → expected scores)
- Edge cases: rounding boundaries, missing evidence, duplicate milestone IDs, mismatched bank refs
- Integration test: full pipeline produces schema-valid certificates
- Determinism test: same fixtures → identical hashes across two runs

---

## Key difference from Observer

Observer used LLM-graded scoring (Claude evaluated precision/recall/reply_accuracy). These theatres use **pure deterministic scoring** — no API calls, no inference costs, instant execution. Each criterion is a binary check (1.0 or 0.0). Composite score is weighted average of binary checks.

This means:
- No ANTHROPIC_API_KEY needed
- No rate limits or 429/529 errors
- Runs in seconds, not minutes
- Perfectly reproducible every time
- Can scale to thousands of records trivially

---

## Fixture data structure

Each fixture record in the dataset files contains:
- `record_id`: unique identifier
- `inputs`: the data being verified (payment, NOI report, escrow state, etc.)
- `policy`: the rules being applied (waterfall percentages, milestone schedule, reconciliation rules)
- `expected`: the known-correct output
- `metadata`: asset_id, period, timestamps

The scorer loads each record, recomputes the output from inputs + policy, then compares against expected. Each criterion maps to a specific comparison.

---

## Success criteria

1. All three scorer functions produce correct binary scores for all 10 fixture records
2. Three CalibrationCertificate JSONs written, each validating against the schema
3. Evidence bundles created with deterministic hashing
4. Determinism smoke test passing (identical hashes across two runs)
5. No external API dependencies — runs fully offline
6. All tests passing

---

## What this is NOT

- Not an LLM scoring pipeline — purely deterministic
- Not a new replay engine — reuses Cycle-031 engine
- Not production deployment — v0.1 fixtures with illustrative data
- Not a Two-Rail marketplace build — just the verification layer
