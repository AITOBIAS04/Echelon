# Sprint Plan: Two-Rail Deterministic Theatres — Unified Pipeline

**Cycle:** 007
**Sprints:** 1
**Total Tasks:** 9

---

## Sprint 1: Unified Pipeline + Arrears Scorer

**Goal:** Wire all four Two-Rail templates through the OSINT pipeline infrastructure. Build the missing arrears scorer. All four templates produce Verifier CLI PASS with deterministic evidence bundles.

**Global Sprint ID:** 11

### Tasks

#### T1: Build Arrears Scorer

**Description:** Create `theatre/scoring/arrears_scorer.py` implementing the 6 criteria from the ARREARS_RESOLUTION_V1 template. The scorer follows the identical async interface as the three existing scorers (`WaterfallScorer`, `EscrowScorer`, `ReconciliationScorer`): an `async score(criteria_id, ground_truth, oracle_output) -> float` method returning 1.0 (pass) or 0.0 (fail). Uses a dispatch dict mapping criteria IDs to check methods. Each check method performs structural validation (Decimal arithmetic, state machine transition checks) and cross-checks against `expected_outputs.criteria_verdicts`. All monetary comparisons use `decimal.Decimal` with `ROUND_HALF_UP` and `TOLERANCE = Decimal("0.01")`. Embeds the `VALID_TRANSITIONS` frozenset (24 transitions from the template state machine) as a compile-time constant.

**Acceptance Criteria:**
- [ ] File `theatre/scoring/arrears_scorer.py` exists with `ArrearsScorer` class
- [ ] `ArrearsScorer.score()` is `async def` matching the existing scorer signature
- [ ] All 6 criteria implemented: `state_transition_validity`, `ladder_redirection_arithmetic`, `reserve_fund_impact`, `distribution_adjustment`, `grace_period_enforcement`, `ladder_balance_protection`
- [ ] Dispatch dict maps criteria IDs to `_check_*` methods
- [ ] `VALID_TRANSITIONS` frozenset contains all 24 allowed `(from, to)` state pairs from the template
- [ ] All numeric comparisons use `Decimal(str(value))` conversion, `ROUND_HALF_UP`, and `TOLERANCE = Decimal("0.01")`
- [ ] Unknown criteria IDs return 0.0

**Dependencies:** None
**Files:** `theatre/scoring/arrears_scorer.py` (new)

---

#### T2: Export ArrearsScorer from scoring __init__

**Description:** Add `ArrearsScorer` to `theatre/scoring/__init__.py` imports and `__all__` list. This is an additive-only change (2 lines). No existing imports or exports are modified.

**Acceptance Criteria:**
- [ ] `from theatre.scoring.arrears_scorer import ArrearsScorer` added to imports
- [ ] `"ArrearsScorer"` added to `__all__` list
- [ ] Existing imports and `__all__` entries unchanged
- [ ] `from theatre.scoring import ArrearsScorer` resolves correctly

**Dependencies:** T1
**Files:** `theatre/scoring/__init__.py` (modified, additive only)

---

#### T3: Build Evidence Bundle Writer in Unified Runner

**Description:** Implement the evidence bundle directory writer as part of the unified runner script. Writes replay data into the FR-2 directory layout: `inputs/`, `receipts/` (empty), `gaps/` (empty), `scores/`, `policy/`, `expected/`, plus `theatre_template.json` and `oracle_output.json`. All JSON files written with `sort_keys=True` for determinism. Policy file mapping: `arrears_policy.json` from template `arrears_policy` key; `waterfall_policy.json`, `escrow_policy.json`, `reconciliation_policy.json` from template-specific sections (or empty `{}` if absent). Empty directories (`receipts/`, `gaps/`) are created but left empty for replay.

**Acceptance Criteria:**
- [ ] Evidence directory created with all 6 subdirectories: `inputs/`, `receipts/`, `gaps/`, `scores/`, `policy/`, `expected/`
- [ ] `inputs/<record_id>.json` written for each fixture record with `sort_keys=True`
- [ ] `expected/<record_id>.json` written for each fixture record with `sort_keys=True`
- [ ] `scores/per_record.json` contains all per-record criterion scores
- [ ] `scores/aggregate.json` contains per-criterion aggregates and composite score
- [ ] `policy/<policy_key>.json` written per template mapping
- [ ] `theatre_template.json` is the original unmutated template (C-6 compliance)
- [ ] `oracle_output.json` uses deterministic `evaluated_at` epoch and deterministic `oracle_id` format (`replay_<template_key>`)
- [ ] `receipts/` and `gaps/` directories exist but are empty

**Dependencies:** T1
**Files:** `scripts/run_two_rail_certificates.py` (new, partial -- evidence writing portion)

---

#### T4: Build OracleOutput Adapter

**Description:** Construct an `OracleOutput` from replay scorer results, adapting the per-criterion aggregate scores into `CriterionScore` objects. Build `OracleCollectionSummary` with `total_sources_attempted = len(records)`, `total_sources_succeeded = len(records)`, `total_sources_failed = 0`. Leave `corroboration_results` and `counter_signal_results` as empty lists (defaults). Set `oracle_id` to `replay_<template_key>` and `evaluated_at` to a fixed deterministic epoch for manifest reproducibility.

**Acceptance Criteria:**
- [ ] `OracleOutput` constructed with `CriterionScore` list from per-criterion aggregates
- [ ] `OracleCollectionSummary` populated with correct source counts from fixture records
- [ ] `oracle_id` is deterministic: `"replay_<template_key>"`
- [ ] `evaluated_at` is a fixed deterministic epoch (not current time)
- [ ] Corroboration and counter-signal results are empty lists
- [ ] `composite_score` matches weighted sum of per-criterion aggregates
- [ ] Each `CriterionScore.passed` is `True` when `score >= 0.5`

**Dependencies:** T1
**Files:** `scripts/run_two_rail_certificates.py` (new, partial -- OracleOutput construction portion)

---

#### T5: Wire Certificate Generation and Verification

**Description:** Integrate `CertificateGenerator.generate()` from `osint/osint_pipeline/engine/certificate_generator.py` into the unified runner. Compute commitment hash via `canonical_hash(raw_template)`. Compute manifest hash via `build_manifest()` + `manifest_hash()` from `osint/osint_pipeline/engine/manifest_builder.py`. Generate `CalibrationCertificate` with `execution_path="replay"`, `inquiry_class="INSPECTION"`, `pipeline_version="0.7.0"`. Write certificate to `evidence_dir/certificate.json`. Run `echelon_verify.py verify` on the produced certificate + evidence directory.

**Acceptance Criteria:**
- [ ] Commitment hash computed from original template via `canonical_hash(raw_template)`
- [ ] Manifest built by `build_manifest(evidence_dir)` and hashed by `manifest_hash(manifest)`
- [ ] `manifest.json` written to evidence directory (excluded from its own hash)
- [ ] Certificate generated with `execution_path="replay"`, `verification_tier="UNVERIFIED"`
- [ ] Certificate written to `evidence_dir/certificate.json` with `sort_keys=True`
- [ ] `target_entity` contains `template_id`, `construct_id`, `dataset_id`, `record_count`
- [ ] Verifier CLI invoked post-generation and result reported

**Dependencies:** T3, T4
**Files:** `scripts/run_two_rail_certificates.py` (new, partial -- certificate + verify portion)

---

#### T6: Assemble Unified Runner Script with CLI

**Description:** Assemble `scripts/run_two_rail_certificates.py` as the complete unified runner. Implements the CLI interface with `--template <key>`, `--all`, `--output-dir`, and `--verbose` flags. Contains the `TEMPLATE_REGISTRY` mapping all 4 templates to their template file, dataset file, and scorer class. Handles `sys.path` setup (project root + `osint/` directory). Uses `asyncio.run()` at the top level for async scorer calls. Reports results (PASS/FAIL, composite scores) to stdout. Returns exit code 0 if all requested templates pass.

**Acceptance Criteria:**
- [ ] Script executable as `python scripts/run_two_rail_certificates.py --template escrow_milestone_release_v1`
- [ ] `--all` flag runs all 4 templates
- [ ] `--output-dir` flag controls output location (default: `output/unified_certificates`)
- [ ] `--verbose` flag enables detailed logging
- [ ] `TEMPLATE_REGISTRY` maps all 4 template keys to correct files and scorer classes
- [ ] `sys.path` includes project root and `osint/` directory
- [ ] Exit code 0 when all templates PASS, non-zero on any FAIL
- [ ] Existing `scripts/run_two_rail_theatres.py` is NOT modified (SC-10)

**Dependencies:** T2, T3, T4, T5
**Files:** `scripts/run_two_rail_certificates.py` (new, final assembly)

---

#### T7: Unit Tests -- Arrears Scorer

**Description:** Create `tests/test_arrears_scorer.py` with comprehensive tests for all 16 fixture records across all 6 criteria. Test valid records (arrears_0001 through arrears_0010, all 6 criteria return 1.0), targeted failure records (arrears_0011 through arrears_0016, exactly one criterion returns 0.0 each), unknown criterion handling, and Decimal arithmetic precision.

**Acceptance Criteria:**
- [ ] `test_all_valid_records_pass_all_criteria`: records arrears_0001--arrears_0010 return 1.0 for all 6 criteria
- [ ] `test_state_transition_failure`: arrears_0011 returns 0.0 for `state_transition_validity`, 1.0 for other 5
- [ ] `test_ladder_redirection_failure`: arrears_0012 returns 0.0 for `ladder_redirection_arithmetic`, 1.0 for other 5
- [ ] `test_reserve_fund_failure`: arrears_0013 returns 0.0 for `reserve_fund_impact`, 1.0 for other 5
- [ ] `test_distribution_adjustment_failure`: arrears_0014 returns 0.0 for `distribution_adjustment`, 1.0 for other 5
- [ ] `test_grace_period_failure`: arrears_0015 returns 0.0 for `grace_period_enforcement`, 1.0 for other 5
- [ ] `test_ladder_balance_protection_failure`: arrears_0016 returns 0.0 for `ladder_balance_protection`, 1.0 for other 5
- [ ] `test_unknown_criterion_returns_zero`: unknown criterion ID returns 0.0
- [ ] `test_decimal_arithmetic_precision`: verifies Decimal usage with no float imprecision in ladder redirection sums
- [ ] All tests pass via `pytest tests/test_arrears_scorer.py`

**Dependencies:** T1, T2
**Files:** `tests/test_arrears_scorer.py` (new)

---

#### T8: Integration + Determinism Tests

**Description:** Create `tests/test_unified_pipeline.py` and `tests/test_determinism.py`. Integration test: run full pipeline for escrow template, verify `echelon_verify.verify()` returns True, validate FR-2 directory layout, check certificate has `execution_path="replay"` and validates against `CalibrationCertificate` model. Determinism test: run pipeline for escrow twice to separate temp dirs, assert manifest hash, commitment hash, and all file SHA-256s are identical across runs.

**Acceptance Criteria:**
- [ ] `test_escrow_pipeline_produces_pass`: full pipeline for escrow produces Verifier CLI PASS
- [ ] `test_evidence_bundle_directory_layout`: all 6 FR-2 subdirectories exist
- [ ] `test_manifest_contains_all_files`: manifest has entries for every non-excluded file
- [ ] `test_certificate_has_replay_fields`: `execution_path == "replay"`, `verification_tier == "UNVERIFIED"`
- [ ] `test_certificate_model_matches_osint`: certificate dict validates as `CalibrationCertificate(**data)`
- [ ] `test_deterministic_manifest_hash`: dual-run produces identical manifest hash
- [ ] `test_deterministic_commitment_hash`: dual-run produces identical commitment hash
- [ ] `test_deterministic_file_contents`: every evidence file has identical SHA-256 across runs
- [ ] All tests pass via `pytest tests/test_unified_pipeline.py tests/test_determinism.py`

**Dependencies:** T6
**Files:** `tests/test_unified_pipeline.py` (new), `tests/test_determinism.py` (new)

---

#### T9: All-Templates Verification + Cross-Path Schema Tests

**Description:** Create `tests/test_all_templates.py` and `tests/test_cross_path_schema.py`. All-templates test: run pipeline for each of the 4 templates, verify `echelon_verify.verify()` returns True for all, assert composite scores within 0.01 of expected values (escrow ~0.9091, waterfall ~0.9333, reconciliation ~0.9333, arrears ~0.9375). Cross-path schema test: load a replay certificate JSON and validate it against the `CalibrationCertificate` Pydantic model, check all required fields present. Also verify all existing tests (70+ osint + theatre) still pass (SC-08).

**Acceptance Criteria:**
- [ ] `test_all_four_templates_pass_verifier`: all 4 templates produce Verifier CLI PASS
- [ ] `test_composite_scores_in_expected_range`: composite scores within 0.01 of expected values
- [ ] `test_replay_certificate_validates_as_calibration_certificate`: replay cert validates with `CalibrationCertificate(**data)`
- [ ] `test_certificate_required_fields_present`: all required `CalibrationCertificate` fields exist
- [ ] All existing tests remain green (SC-08) -- no regressions
- [ ] All new tests pass via `pytest tests/test_all_templates.py tests/test_cross_path_schema.py`

**Dependencies:** T6, T7, T8
**Files:** `tests/test_all_templates.py` (new), `tests/test_cross_path_schema.py` (new)

---

## Summary

| Task | Title | Dependencies | New/Modified Files |
|------|-------|--------------|--------------------|
| T1 | Build Arrears Scorer | None | `theatre/scoring/arrears_scorer.py` (new) |
| T2 | Export ArrearsScorer from scoring __init__ | T1 | `theatre/scoring/__init__.py` (modified) |
| T3 | Build Evidence Bundle Writer | T1 | `scripts/run_two_rail_certificates.py` (new, partial) |
| T4 | Build OracleOutput Adapter | T1 | `scripts/run_two_rail_certificates.py` (new, partial) |
| T5 | Wire Certificate Generation and Verification | T3, T4 | `scripts/run_two_rail_certificates.py` (new, partial) |
| T6 | Assemble Unified Runner Script with CLI | T2, T3, T4, T5 | `scripts/run_two_rail_certificates.py` (new, final) |
| T7 | Unit Tests -- Arrears Scorer | T1, T2 | `tests/test_arrears_scorer.py` (new) |
| T8 | Integration + Determinism Tests | T6 | `tests/test_unified_pipeline.py` (new), `tests/test_determinism.py` (new) |
| T9 | All-Templates Verification + Cross-Path Schema | T6, T7, T8 | `tests/test_all_templates.py` (new), `tests/test_cross_path_schema.py` (new) |

## Dependency Graph

```
T1 (Arrears Scorer)
├── T2 (Export __init__)
│   └── T6 (Assemble Runner CLI)
│       ├── T8 (Integration + Determinism Tests)
│       │   └── T9 (All-Templates + Cross-Path Tests)
│       └── T9
├── T3 (Evidence Bundle Writer)
│   └── T5 (Certificate Generation + Verify)
│       └── T6
├── T4 (OracleOutput Adapter)
│   └── T5
└── T7 (Arrears Scorer Unit Tests)
    └── T9
```

## Notes

- **Fixture record count discrepancy**: The PRD table says 18 fixtures for ARREARS_RESOLUTION_V1 and the dataset file is named `arrears_fixtures_v02_18.json`, but the actual file contains 16 records (arrears_0001 through arrears_0016: 10 valid + 6 targeted failures). The SDD composite score example correctly uses 16 records. Implementation uses the actual 16 records.
- **SC-10 compliance**: No existing files in `theatre/engine/`, `theatre/scoring/` (except additive `__init__.py` change), `scripts/run_two_rail_theatres.py`, or `osint/osint_pipeline/` are modified.
- **Tasks T3--T5 are logical subdivisions** of the single runner script (`scripts/run_two_rail_certificates.py`). They will be implemented together as parts of the same file during `/implement`, but are tracked separately for review granularity and clear acceptance criteria.
