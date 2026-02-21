# PRD: Two-Rail Deterministic Product Theatres (Cycle-033)

> **Version**: 1.0
> **Date**: 2026-02-21
> **Cycle**: cycle-033
> **Depends on**: Cycle-031 (Theatre Template Engine), Cycle-032 (Observer E2E Integration)
> **Context**: `grimoires/loa/context/echelon_cycle_033.md`

---

## 1. Problem Statement

The Theatre engine (Cycle-031) and Observer pipeline (Cycle-032) have proven the end-to-end lifecycle works: commit → invoke → score → certify. However, Observer scoring uses **LLM-graded evaluation** (Claude judges precision/recall/reply_accuracy), which is inherently non-deterministic, requires API keys, hits rate limits, and takes minutes to execute.

The Two-Rail marketplace has three financial verification domains — distribution waterfalls, escrow milestone releases, and ledger reconciliation — where every check is **purely arithmetic or policy-binary**. These domains need Product Theatres that produce calibration certificates with **zero LLM dependency**: instant, deterministic, perfectly reproducible, and runnable offline.

Three template files and three fixture datasets (10 records each) already exist at `theatre/fixtures/two_rail_theatres_v0_1/`. The replay engine, commitment protocol, evidence bundle builder, tier assigner, and certificate issuer all exist from Cycles 031/032. What's missing is the scoring layer and runner script.

> Source: `grimoires/loa/context/echelon_cycle_033.md`

---

## 2. Goals & Success Metrics

| # | Goal | Metric |
|---|------|--------|
| G1 | Three deterministic scorer functions producing correct binary scores | 30/30 fixture records score correctly (10 per theatre) |
| G2 | Three schema-valid CalibrationCertificate JSON files | All three validate against `echelon_certificate_schema.json` |
| G3 | Evidence bundles with deterministic hashing | Identical hashes across two consecutive runs |
| G4 | No external API dependencies | Runs fully offline — no ANTHROPIC_API_KEY, no GITHUB_TOKEN |
| G5 | Execution under 10 seconds total | All three theatres complete in <10s (vs ~10min for Observer) |
| G6 | All tests passing | Unit + integration + determinism tests green |

---

## 3. Scope

### In Scope

1. **Three deterministic scorer functions** implementing the `ScoringFunction` protocol from `theatre/engine/scoring.py`
2. **Runner script** (`scripts/run_two_rail_theatres.py`) wiring fixtures through the replay engine
3. **Unit tests** for each scorer (known-good inputs, edge cases)
4. **Integration test** (full pipeline → schema-valid certificates)
5. **Determinism smoke test** (same fixtures → identical hashes on two runs)

### Out of Scope

- New replay engine code (reuses Cycle-031 `ReplayEngine`)
- Production deployment
- Live data ingestion (uses existing v0.1 fixtures)
- Two-Rail marketplace application code
- Template or fixture modifications

---

## 4. Functional Requirements

### FR1: Distribution Waterfall Scorer

Implements `ScoringFunction` protocol. Five binary checks (each 1.0 or 0.0):

| Criteria ID | Check | Pass Condition |
|-------------|-------|----------------|
| `waterfall_arithmetic` | Bucket amounts match policy percentages applied to inputs | Computed splits == expected splits |
| `noi_pool_conservation` | Sum of all NOI pool outflows == NOI amount | `abs(sum(allocations) - noi_pool) <= 0.01` |
| `rounding_policy_compliance` | All amounts use consistent rounding (ROUND_HALF_UP, 2dp) | Every amount == `round(amount, 2)` using policy mode |
| `cap_table_consistency` | `per_token_amount × token_supply == distribution_pool` | Within rounding tolerance (£0.01) |
| `ledger_reconciliation` | Sum of payment splits == gross_amount | `abs(sum(splits) - gross_amount) <= 0.01` |

**Input shape** (from fixture `inputs`): `payment`, `noi_report`, `cap_table_snapshot`, `rounding_policy`
**Expected output shape** (from fixture `expected_outputs`): `distribution_statement`

### FR2: Escrow Milestone Release Scorer

Five binary checks:

| Criteria ID | Check | Pass Condition |
|-------------|-------|----------------|
| `required_evidence_present` | All `evidence_required` items have matching documents | Every required doc_type found in `evidence_bundle.documents` |
| `signature_policy_satisfied` | All required signer roles have attestations | Every role in `required_signer_roles` found in `attestations` |
| `validity_window_respected` | Evidence timestamp falls within milestone's allowed window | `evidence_timestamp` exists and is parseable (v0.1: always valid) |
| `release_amount_correct` | `release_pct × escrow_balance == release_amount` | Within rounding tolerance (£0.01) |
| `idempotency` | Same milestone ID cannot trigger release twice | No duplicate `milestone_id` in the dataset |

**Input shape**: `escrow_state`, `milestone_schedule`, `evidence_bundle`
**Expected output shape**: `release_instruction`

### FR3: Ledger Reconciliation Scorer

Five binary checks:

| Criteria ID | Check | Pass Condition |
|-------------|-------|----------------|
| `bank_ref_match` | Every `settlement_reference` has a matching bank statement entry | Bank txn exists with matching `reference` |
| `bucket_sum_matches_gross` | Sum of `splits.amount` == `gross_amount` | Within rounding tolerance (£0.01) |
| `bucket_destination_valid` | Each split's `destination_ref` is in `allowed_destinations` | Every split destination found in bucket rules |
| `event_log_complete` | Every split produces exactly one ledger event | `len(event_log) == len(splits)` and each split has a matching event |
| `exceptions_correct` | Mismatches generate correct exception type | `expected_outputs.exceptions` matches computed exceptions |

**Input shape**: `bank_statement_slice`, `payment`, `event_log`, `reconciliation_rules`
**Expected output shape**: `reconciliation_result`

### FR4: Runner Script

`scripts/run_two_rail_theatres.py` — single CLI entry point:

```
python scripts/run_two_rail_theatres.py --all --verbose
python scripts/run_two_rail_theatres.py --theatre distribution_waterfall_v1
```

Pipeline per theatre:
1. Load template from `theatre/fixtures/two_rail_theatres_v0_1/templates/`
2. Load fixture dataset from `theatre/fixtures/two_rail_theatres_v0_1/datasets/`
3. Validate template against `echelon_theatre_schema_v2.json`
4. Create CommitmentReceipt
5. Convert fixture records to GroundTruthEpisodes
6. Run ReplayEngine with deterministic scorer
7. Build evidence bundle
8. Issue CalibrationCertificate
9. Validate certificate against `echelon_certificate_schema.json`
10. Write to `output/certificates/{template_id}.json`

### FR5: Tests

| Test Category | Coverage |
|---------------|----------|
| Waterfall scorer unit | Known-good: all 5 checks pass. Edge: rounding boundary, NOI mismatch |
| Escrow scorer unit | Known-good: all 5 pass. Edge: missing evidence, missing signer, duplicate milestone |
| Reconciliation scorer unit | Known-good: all 5 pass. Edge: missing bank ref, wrong destination, missing event |
| Integration | Full pipeline → 3 schema-valid certificates |
| Determinism | Two consecutive runs produce identical certificate hashes |

---

## 5. Technical Constraints

- **Python stdlib + pydantic only** — no new dependencies (Decimal from stdlib for rounding)
- **Reuse existing engine** — `ReplayEngine`, `CommitmentProtocol`, `EvidenceBundleBuilder`, `TierAssigner`, `TheatreCalibrationCertificate` all from Cycle-031
- **ScoringFunction protocol** — each scorer implements `async def score(criteria_id, ground_truth, oracle_output) -> float`
- **Rounding tolerance** — £0.01 (configurable) using `Decimal` with `ROUND_HALF_UP`
- **No network calls** — everything runs from local fixtures

---

## 6. File Plan

| File | Action | Description |
|------|--------|-------------|
| `theatre/scoring/waterfall_scorer.py` | Create | Distribution Waterfall scorer (5 binary checks) |
| `theatre/scoring/escrow_scorer.py` | Create | Escrow Milestone Release scorer (5 binary checks) |
| `theatre/scoring/reconciliation_scorer.py` | Create | Ledger Reconciliation scorer (5 binary checks) |
| `theatre/scoring/__init__.py` | Create | Package exports |
| `scripts/run_two_rail_theatres.py` | Create | Runner script |
| `tests/theatre/test_waterfall_scorer.py` | Create | Waterfall scorer unit tests |
| `tests/theatre/test_escrow_scorer.py` | Create | Escrow scorer unit tests |
| `tests/theatre/test_reconciliation_scorer.py` | Create | Reconciliation scorer unit tests |
| `tests/theatre/test_two_rail_integration.py` | Create | Integration + determinism tests |

---

## 7. Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Fixture data has no edge cases (all happy path) | Scorers pass trivially | Unit tests include synthetic edge-case records |
| Escrow idempotency check requires cross-episode state | Scorer needs dataset-level context | Pass seen milestone IDs as oracle adapter state |
| Template schema validation may fail with `construct_under_test` as object | Blocks pipeline | Match template format to schema expectations |

---

## 8. Non-Goals (Explicit)

- No LLM scoring — every check is arithmetic or set-membership
- No new replay engine — existing `ReplayEngine` handles the orchestration
- No fixture generation — v0.1 fixtures are consumed as-is
- No production infra — local CLI execution only
