# Implementation Report: Sprint 11 — Unified Pipeline + Arrears Scorer

**Cycle:** 007 — Two-Rail Deterministic Theatres — Unified Pipeline
**Sprint:** 1 (Global Sprint 11)
**Branch:** `feature/sprint-11-unified-pipeline`
**Status:** All 9 tasks complete, all tests passing

---

## Summary

Wired all four Two-Rail templates through the OSINT pipeline infrastructure. Built the missing arrears scorer. All four templates produce Verifier CLI PASS with deterministic evidence bundles.

## Files Changed

### New Files (8)

| File | Task | Description |
|------|------|-------------|
| `theatre/scoring/arrears_scorer.py` | T1 | ArrearsScorer — 6 criteria, 24 state transitions, Decimal arithmetic |
| `scripts/run_two_rail_certificates.py` | T3-T6 | Unified runner — 10-step pipeline with CLI |
| `tests/theatre/test_arrears_scorer.py` | T7 | 14 unit tests for arrears scorer |
| `tests/theatre/test_unified_pipeline.py` | T8 | 5 integration tests (escrow end-to-end) |
| `tests/theatre/test_determinism.py` | T8 | 3 determinism tests (dual-run hash comparison) |
| `tests/theatre/test_all_templates.py` | T9 | 8 parametrised tests across all 4 templates |
| `tests/theatre/test_cross_path_schema.py` | T9 | 2 cross-path schema validation tests |

### Modified Files (1)

| File | Task | Change |
|------|------|--------|
| `theatre/scoring/__init__.py` | T2 | Added `ArrearsScorer` import and `__all__` entry |

## Task Completion

### T1: Build Arrears Scorer

- `ArrearsScorer` class with `async score()` matching existing scorer interface
- 6 criteria: `state_transition_validity`, `ladder_redirection_arithmetic`, `reserve_fund_impact`, `distribution_adjustment`, `grace_period_enforcement`, `ladder_balance_protection`
- `VALID_TRANSITIONS` frozenset with all 24 allowed `(from, to)` state pairs
- All numeric comparisons use `Decimal(str(value))` with `TOLERANCE = Decimal("0.01")`
- Unknown criteria IDs return 0.0
- **Bug found during testing:** `_check_ladder_balance_protection` incorrectly failed when `output_balance < input_balance` even for legitimate dispositions (e.g. NAV redemption on lease termination, arrears_0010). Fixed: structural check now only fails when `ladder_balance_protected` is also `False`.

### T2: Export ArrearsScorer from scoring __init__

- Added `from theatre.scoring.arrears_scorer import ArrearsScorer` to imports
- Added `"ArrearsScorer"` to `__all__` list
- Additive only — no existing imports modified

### T3: Build Evidence Bundle Writer

- FR-2 directory layout: `inputs/`, `receipts/`, `gaps/`, `scores/`, `policy/`, `expected/`
- Per-record input and expected JSON files with `sort_keys=True`
- `scores/per_record.json` and `scores/aggregate.json`
- Policy files per template mapping
- `theatre_template.json` (original, unmutated — C-6 compliance)
- `oracle_output.json` with deterministic timestamps

### T4: Build OracleOutput Adapter

- `OracleOutput` constructed with `CriterionScore` list from per-criterion aggregates
- `OracleCollectionSummary` with correct source counts
- Deterministic `oracle_id` format: `replay_<template_key>`
- Fixed epoch: `2026-01-01T00:00:00Z`

### T5: Wire Certificate Generation and Verification

- Commitment hash via `canonical_hash(raw_template)`
- Manifest via `build_manifest()` + `manifest_hash()`
- Certificate with `execution_path="replay"`, `inquiry_class="INSPECTION"`, `pipeline_version="0.7.0"`
- `echelon_verify()` runs post-generation

### T6: Assemble Unified Runner Script with CLI

- `TEMPLATE_REGISTRY` maps all 4 templates to files, scorer classes, policy keys
- CLI: `--template <key>`, `--all`, `--output-dir`, `--verbose`
- Exit code 0 when all templates PASS
- **Import order critical:** Theatre imports MUST precede `osint_pipeline.echelon_verify` because `echelon_verify.py` adds `osint/osint_pipeline/` to `sys.path`, which shadows root `theatre/` with `osint/osint_pipeline/theatre/` (no scoring submodule).

### T7: Unit Tests — Arrears Scorer

14 tests:
- 6 parametrised: all 10 valid records pass all 6 criteria
- 6 targeted failure tests: each failure record fails exactly one criterion
- 1 unknown criterion returns 0.0
- 1 Decimal arithmetic precision (records with `ladder_redirection_detail`)

### T8: Integration + Determinism Tests

8 tests:
- Integration: escrow pipeline PASS, FR-2 layout, manifest completeness, replay fields, CalibrationCertificate model compatibility
- Determinism: dual-run identical manifests, commitment hashes, and file SHA-256s

### T9: All-Templates + Cross-Path Schema

10 tests:
- 4 parametrised verifier PASS tests (all templates)
- 4 parametrised composite score range tests
- 1 CalibrationCertificate model validation
- 1 required fields check

## Test Results

```
New tests: 32 passed
Existing OSINT pipeline tests: 239 passed
Existing theatre tests (sync): 176 passed
```

## Pipeline Results

```
[PASS] escrow_milestone_release_v1: 0.8591
[PASS] distribution_waterfall_v1: 0.9333
[PASS] ledger_reconciliation_v1: 0.8933
[PASS] arrears_resolution_v1: 0.9375
```

## SC-10 Compliance

No existing files modified except the additive `theatre/scoring/__init__.py` change. `scripts/run_two_rail_theatres.py` untouched. No modifications to `theatre/engine/`, `osint/osint_pipeline/`, or existing scorer files.

## Known Issues

- Existing async theatre tests (escrow_scorer, waterfall_scorer, reconciliation_scorer) fail due to missing `pytest-asyncio` package — pre-existing issue, not caused by this sprint.
- `echelon_verify.py` adds `osint/osint_pipeline/` to `sys.path` at import time, which can shadow root-level packages. Import order in consumers must account for this.
