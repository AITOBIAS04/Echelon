# Sprint 2 (Global Sprint-13) — Engineer Feedback

**Reviewer**: Senior Technical Lead
**Date**: 2026-03-01
**Verdict**: All good (with minor notes)

---

## Summary

All 6 sprint tasks are implemented and meet their acceptance criteria. 23 new tests pass (19 scorer/fixture/template + 4 MCP integration). Code quality is high, follows existing patterns from the Two-Rail scorers, and the pipeline is verifiably deterministic. No blocking issues found.

---

## Task-by-Task Verification

### Task 1: CONSTRUCT_CALIBRATION_V1 Template

**File**: `theatre/fixtures/construct_calibration/templates/CONSTRUCT_CALIBRATION_V1.template.json`
**Status**: PASS

- `template_family: "PRODUCT"` -- confirmed (line 3)
- `execution_path: "replay"` -- confirmed (line 4)
- `inquiry_class: "INSPECTION"` -- confirmed (line 9)
- `criteria.weights` sum: 0.40 + 0.40 + 0.20 = 1.0 -- confirmed
- `dataset_hashes` present with 64-char hex value -- confirmed (line 27)
- Template structure matches existing theatre templates -- confirmed (includes `schema_version`, `resolution_programme`, `evidence_bundle`, `version_pins`)

**Note**: The sprint plan AC says `dataset_hash` (singular) while the template uses `dataset_hashes` (plural, keyed by filename). This is actually better design -- it matches SDD section 3.1 and allows multiple datasets per template. No issue.

### Task 2: Construct Calibration Scorer

**File**: `theatre/scoring/construct_calibration_scorer.py`
**Status**: PASS

- Conforms to `ScoringFunction` protocol from `theatre/engine/scoring.py:15` -- verified. Method signature `async def score(criteria_id, ground_truth, oracle_output) -> float` matches exactly.
- `precision = supported_claims / total_claims` -- confirmed (line 54-55)
- `recall = surfaced_changes / total_important_changes` -- confirmed (line 65-66)
- `reply_accuracy = grounded_answers / total_answers` -- confirmed (line 76-77)
- Float arithmetic, no Decimal -- confirmed (only `float` division used)
- Returns 0.0 for unknown criteria -- confirmed (line 42)
- Returns 0.0 for empty annotations -- confirmed (lines 51, 62, 73)
- Returns 0.0 for missing `expected_output` -- confirmed (line 32 `.get("expected_output", {})` yields empty dict, then empty list triggers 0.0)

**Note**: The `oracle_output` parameter is unused (scores are computed entirely from `ground_truth`). This is correct for deterministic fixture-based scoring -- the ground truth already contains the annotations. This matches the pattern in `EscrowScorer` where `oracle_output` is also ignored when scoring from pre-annotated data.

### Task 3: Fixture Dataset

**File**: `theatre/fixtures/construct_calibration/datasets/community_oracle_v1_fixtures.json`
**Status**: PASS

- 12 records (>=10 required) -- confirmed
- Each record has `record_id`, `input_data`, `expected_output` -- confirmed for all 12
- `expected_output` contains `precision_annotations`, `recall_annotations`, `reply_accuracy_annotations` -- confirmed for all 12
- All annotations are binary booleans -- confirmed by test and manual inspection
- Score distributions verified independently:
  - precision mean = 0.8000 (target ~0.8) -- PASS
  - recall mean = 0.5417 (target ~0.55) -- PASS
  - reply_accuracy mean = 0.8000 (target ~0.8) -- PASS
  - composite = 0.6967 (target ~0.70) -- PASS
- `input_data` structure: all records contain `pr_diff`, `construct_summary`, `followup_qa` with 5 Q&A pairs each -- confirmed
- Fixture data is diverse: 12 distinct PR scenarios (bugfix, feature, refactor, dependency, performance, API, migration, security, config, tests, documentation, CI/CD)

### Task 4: Dedicated Construct Calibration Runner

**File**: `scripts/run_construct_calibration.py`
**Status**: PASS

- No imports from `run_two_rail_certificates.py` -- confirmed (grep returns zero matches)
- Accepts `--construct community_oracle_v1` -- confirmed (line 456-459)
- Accepts `--construct-source` -- confirmed (line 462-464)
- Loads template from `theatre/fixtures/construct_calibration/templates/` -- confirmed (line 210)
- Loads dataset from `theatre/fixtures/construct_calibration/datasets/` -- confirmed (line 211)
- Scores each record via `ConstructCalibrationScorer` -- confirmed (via `ReplayEngine.run()`)
- Builds evidence bundle with `inputs/`, `expected/`, `scores/`, `manifest.json` -- confirmed (lines 308-361)
- Computes evidence bundle hash -- confirmed (line 350)
- Generates certificate -- confirmed (lines 364-390)
- Verifies via MCP `echelon_verify` -- confirmed (lines 427-444)
- Writes to `output/construct_calibration/community_oracle_v1/` -- confirmed (line 302)
- Produces `index.json` -- confirmed (lines 407-423)
- Exits 0 on success -- confirmed (test passes)

**Determinism design**:
- `_FIXTURE_EPOCH = datetime(2026, 3, 1, 0, 0, 0)` for fixed timestamps -- confirmed (line 46)
- `uuid.uuid5()` for deterministic certificate ID -- confirmed (line 206)
- `shutil.rmtree()` cleanup before each run -- confirmed (lines 304-306)
- Direct `CommitmentReceipt` creation bypassing `datetime.utcnow()` -- confirmed (line 249)

### Task 5: MCP Verification Loop + Integration Tests

**File**: `tests/test_mcp_integration.py`
**Status**: PASS

- Test generates certificate via `run_construct_calibration` flow -- confirmed (line 34)
- Test calls MCP `echelon_verify` programmatically -- confirmed (line 36-38)
- PASS assertion succeeds -- confirmed (line 40)
- Tampered certificate FAIL assertion succeeds -- confirmed (lines 47-56)
- Determinism test: two runs produce identical evidence bundle hash -- confirmed (lines 58-64)
- Certificate has all required fields -- confirmed (lines 66-75)
- Total: 4 MCP integration tests

**File location note**: Tests are at `tests/test_mcp_integration.py` instead of `tests/mcp/test_mcp_integration.py` per SDD. Implementation report explains the change -- `tests/mcp/` shadowed the project's `mcp/` package. This is a valid engineering decision.

### Task 6: Results Summary Report

**File**: `reports/construct_calibration_pilot.md`
**Status**: PASS

- Contains: construct, template, criteria, weights, per-criterion scores, composite score -- confirmed
- Evidence bundle hash present -- confirmed
- Verifier verdict: PASS -- confirmed
- Verification tier: UNVERIFIED with explanation -- confirmed
- Independent verification command (copy-pasteable) -- confirmed
- Scores match actual pipeline output (precision=0.8000, recall=0.5417, reply_accuracy=0.8000, composite=0.6967) -- independently verified

---

## Cross-Cutting Checks

### Architecture Alignment (SDD Section 3)

- Template structure matches SDD 3.1 -- PASS
- Scorer matches SDD 3.2 -- PASS
- Fixture format matches SDD 3.3 -- PASS
- Runner pipeline matches SDD 3.4 (13-step) -- PASS
- MCP verification loop matches SDD 3.5 -- PASS
- Integration point imports match SDD Section 5 -- PASS

### Security

- No hardcoded secrets -- PASS
- No hardcoded API keys -- PASS
- No external network calls in scorer or runner -- PASS (fixture-mode is fully offline)
- Input validation in scorer (empty list checks, unknown criteria) -- PASS

### Performance

- No obvious performance issues -- PASS
- Scorer is O(n) per criterion per record -- appropriate
- 12 records, 3 criteria each = 36 scoring operations total -- trivial

### Determinism

- Fixed epoch timestamp -- PASS
- Deterministic UUID (uuid5) -- PASS
- Bundle cleanup before each run -- PASS
- No LLM calls at scoring time -- PASS
- Test `test_deterministic_evidence_bundle_hash` verifies this end-to-end -- PASS

### Code Quality

- Clean, well-documented code with module docstrings -- PASS
- Follows existing patterns (compare `ConstructCalibrationScorer` to `EscrowScorer`) -- PASS
- `theatre/scoring/__init__.py` updated with export -- PASS
- Tests organized logically (scorer, fixture, template, distribution, integration) -- PASS

### Existing Tests

- All pre-existing tests unaffected by Sprint 2 changes -- confirmed (test run shows no new failures attributable to Sprint 2 code)

---

## Minor Notes (Non-Blocking)

1. **`--construct-source` not wired through**: The CLI accepts `--construct-source` (line 462) but `args.construct_source` is never passed to `run_construct_calibration()`. The help text says "not used in fixture mode" which is accurate for current use. When non-fixture mode is needed later, this will need wiring. Acceptable for now since the sprint plan explicitly says fixture mode.

2. **`asyncio.get_event_loop()` deprecation**: Both test files use `asyncio.get_event_loop().run_until_complete(coro)`. This was deprecated in Python 3.10+ in favor of `asyncio.run()`. Since the project targets Python 3.9+ (per the traceback headers), this is currently fine but will emit DeprecationWarning in 3.12+. Consider migrating to `pytest-asyncio` or `asyncio.run()` in a future cleanup.

3. **`import shutil` inside function**: Line 305 in `run_construct_calibration.py` has `import shutil` inside the function body. This is a minor style inconsistency -- other imports are at module level. Non-blocking.

---

## Conclusion

Sprint 2 is complete. All 6 tasks meet their acceptance criteria. The implementation is clean, deterministic, well-tested (23 tests), and architecturally aligned with the SDD. The construct calibration pipeline successfully generates certificates that pass MCP verification, and the evidence bundle hash is reproducible across runs.
