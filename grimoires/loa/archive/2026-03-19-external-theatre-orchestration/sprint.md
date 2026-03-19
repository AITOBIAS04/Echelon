# Sprint Plan — Cycle-038b: External Theatre Orchestration

**Cycle:** cycle-038b
**Date:** 19 March 2026
**Builder:** Loa
**Sprints:** 4 (0–3)
**Global IDs:** 116–119
**Target:** >=30 new tests (PRD AC #8)
**Test file:** `backend/tests/test_038b_external_orchestration.py`

---

## Sprint 0 — Schemas + Extraction Contracts

**Global ID:** 116
**Goal:** Define all Pydantic models for the orchestration surface and validate their shapes with tests.

### Dependencies

- `backend/schemas/theatre_comparison_bundle.py` must exist (038a) — imports `TheatreScopeKey`, `ExecutedTheatreComparisonBundle`, `ComparisonCandidateSet`

### Tasks

#### Task 0.1 — Create orchestration schema module

**File:** `backend/schemas/external_theatre_orchestration.py` (NEW)

**Description:** Create the schema module with all 7 Pydantic models defined in SDD section 2.1:

- `ExternalTheatreInput` — descriptor for a single external theatre (fields: `construct_slug`, `construct_version`, `construct_json`, `construct_json_path`)
- `ExternalTheatrePreparationRequest` — full orchestration request (fields: `theatres`, `event_keys`, `scope_keys`, `certificate_id`)
- `ExtractionResult` — per-theatre extraction summary (fields: `construct_slug`, `success`, `settlement_fixture_count`, `oracle_fixture_count`, `has_calibration`, `functional_fixture_count`, `has_failure_scenarios`, `fallbacks_used`, `error`)
- `TheatrePreparationEntry` — per-theatre result within orchestration (fields: `construct_slug`, `construct_version`, `extraction`, `bundle`, `execution_passed`, `execution_failed`, `error`)
- `BuilderFeedbackItem` — single feedback item (fields: `category`, `field`, `status`, `message`)
- `BuilderFeedbackReport` — per-theatre feedback (fields: `construct_slug`, `required_items`, `optional_items`, `extraction_items`, `overall_readiness`)
- `ExternalTheatrePreparationResult` — complete orchestration result (fields: `theatres`, `candidates`, `feedback`, `event_keys_used`, `scope_keys_used`, `total_theatres`, `total_successful`, `total_failed`)

**Imports from existing code:**
```python
from backend.schemas.theatre_comparison_bundle import (
    ComparisonCandidateSet,
    ExecutedTheatreComparisonBundle,
    TheatreScopeKey,
)
```

**Acceptance criteria:**
- All 7 models importable from `backend.schemas.external_theatre_orchestration`
- `construct_json` is `str` (raw content, not path)
- `ExternalTheatrePreparationRequest` defaults `event_keys=[]`, `scope_keys=[]`, `certificate_id=None`
- `BuilderFeedbackReport.overall_readiness` accepts `"READY"`, `"DEGRADED"`, `"BLOCKED"`

#### Task 0.2 — Create test file with Sprint 0 schema tests

**File:** `backend/tests/test_038b_external_orchestration.py` (NEW)

**Description:** Create the test file using `unittest.TestCase` pattern (matching `test_037e_theatre_execution.py`). Write 7 tests:

| # | Test method | What it validates |
|---|---|---|
| 1 | `test_external_theatre_input_constructs` | `ExternalTheatreInput` accepts `construct_slug="tremor"`, `construct_version="0.1.0"`, `construct_json="{...}"`. Verify `construct_json_path` defaults to `None`. |
| 2 | `test_preparation_request_defaults` | `ExternalTheatrePreparationRequest(theatres=[...])` defaults `event_keys=[]`, `scope_keys=[]`, `certificate_id=None`. |
| 3 | `test_preparation_result_serializes` | Construct an `ExternalTheatrePreparationResult` with one `TheatrePreparationEntry`, call `model_dump()`, verify round-trip through `ExternalTheatrePreparationResult(**dumped)`. |
| 4 | `test_extraction_result_success_shape` | `ExtractionResult(construct_slug="tremor", success=True, settlement_fixture_count=5, oracle_fixture_count=2, has_calibration=True, functional_fixture_count=5, has_failure_scenarios=True)` — verify all counts accessible. |
| 5 | `test_extraction_result_failure_shape` | `ExtractionResult(construct_slug="tremor", success=False, error="parse failed")` — verify `settlement_fixture_count==0`, `error` populated. |
| 6 | `test_builder_feedback_report_categories` | `BuilderFeedbackReport` with items in all 3 lists (`required_items`, `optional_items`, `extraction_items`) — verify list lengths and `category` values on items. |
| 7 | `test_builder_feedback_readiness_states` | Create 3 reports with `overall_readiness` set to each of `"READY"`, `"DEGRADED"`, `"BLOCKED"` — verify field value. |

**Acceptance criteria:**
- All 7 tests pass via `python -m pytest backend/tests/test_038b_external_orchestration.py -v`
- No database dependency (pure Pydantic model tests)

### Exit Criteria

- `backend/schemas/external_theatre_orchestration.py` exists with 7 models
- `backend/tests/test_038b_external_orchestration.py` exists with 7 passing tests
- `python -m pytest backend/tests/test_038b_external_orchestration.py -v` — 7 passed

---

## Sprint 1 — Enriched Fixture Extraction

**Global ID:** 117
**Goal:** Build the enriched fixture extractor that generates realistic `TheatreFixtureInput` (pass + fail scenarios) from construct metadata for both TREMOR and CORONA.

### Dependencies

- Sprint 0 complete (schemas importable)
- `backend/services/theatre_policy_rules.py` (037d) — `parse_construct_json()`, `TheatreConstructMeta`, `TheatreTemplate`, `OsintSource`, `VerificationCheck`
- `backend/schemas/theatre_execution.py` (037e) — `TheatreFixtureInput`

### Tasks

#### Task 1.1 — Create enriched fixture extractor module

**File:** `backend/services/external_theatre_fixture_extractor.py` (NEW)

**Description:** Implement the enriched fixture extraction service with the following functions per SDD section 2.2:

**Public function:**
- `extract_enriched_fixture(construct_slug: str, construct_version: str, meta: TheatreConstructMeta) -> tuple[ExtractionResult, Optional[TheatreFixtureInput]]`
  - Orchestrates the 4 sub-extractors below
  - Aggregates `fallbacks_used` from all sub-extractors
  - Returns `(ExtractionResult, TheatreFixtureInput)` on success
  - Returns `(ExtractionResult(success=False, error=msg), None)` on any internal failure (never raises)
  - Sets `has_failure_scenarios=True` when templates > 1 (odd-indexed templates fail)

**Private functions:**

1. `_build_enriched_settlement_fixtures(templates: list[TheatreTemplate], settlement_tiers: list[dict]) -> tuple[dict, list[str]]`
   - Even-indexed templates (0, 2, 4...): `predicted_outcome == actual_outcome` (PASS)
   - Odd-indexed templates (1, 3, 5...): `predicted_outcome != actual_outcome` (FAIL)
   - Single template: always PASS (do not fail the only template)
   - Binary resolution (`"binary"`): `predicted="YES", actual="YES"` (pass) or `predicted="YES", actual="NO"` (fail)
   - Multi-bucket/multi-class resolution (`"multi_bucket"` or `"multi_class"`): `predicted="bucket_0", actual="bucket_0"` (pass) or `predicted="bucket_0", actual="bucket_2"` (fail)
   - Returns `(fixtures_dict, fallbacks_used)` where key is `template.id`

2. `_build_enriched_oracle_fixtures(sources: list[OsintSource], verification_checks: list[VerificationCheck]) -> tuple[dict, list[str]]`
   - Filter sources with `role == "cross_validation"`
   - First cross-validation source: `primary_value=6.2, cross_value=6.1, delta=0.1, threshold=0.5` (consistent, PASS)
   - Second+ cross-validation source: `primary_value=6.2, cross_value=5.3, delta=0.9, threshold=0.5` (divergent, FAIL)
   - When `verification_checks` is empty: default `threshold=0.5`, add `"oracle_threshold_defaulted"` to fallbacks
   - Returns `(fixtures_dict, fallbacks_used)` where key is `source.id`

3. `_build_enriched_calibration_fixture(meta: TheatreConstructMeta) -> tuple[Optional[dict], list[str]]`
   - If `meta.has_brier_scoring` is False: return `(None, [])`
   - Scan `meta.theatre_templates` for any template with `brier_type="multi_class"` -> use `"multi_class"`
   - Otherwise default to `"binary"`, add `"brier_type_defaulted"` to fallbacks if no template declares `brier_type`
   - Generate deterministic predictions/outcomes and compute `expected_brier` via `_compute_expected_brier()`
   - Returns `(calibration_dict, fallbacks_used)` — dict has keys: `predictions`, `outcomes`, `brier_type`, `expected_brier`

4. `_build_enriched_functional_fixtures(templates: list[TheatreTemplate]) -> tuple[dict, list[str]]`
   - First template: `transform_valid=True`, `input_state="OPEN"`, `expected_output="RESOLVED"`
   - Last template (if >1 templates): `transform_valid=False`, `input_state="OPEN"`, `expected_output="FAILED"`
   - Middle templates (if >2): alternate `transform_valid=True/False`
   - Single template: passing only
   - Returns `(fixtures_dict, fallbacks_used)` where key is `template.id`

5. `_compute_expected_brier(predictions: list[float], outcomes: list[float]) -> float`
   - Binary Brier: `mean((p - o)^2)` — same algorithm as `theatre_fixture_loader._compute_expected_brier()`

**Acceptance criteria:**
- Module importable: `from backend.services.external_theatre_fixture_extractor import extract_enriched_fixture`
- TREMOR extraction: 5 settlement fixtures (3 pass, 2 fail), 2 oracle fixtures (1 consistent, 1 divergent), calibration with `brier_type="multi_class"`, 5 functional fixtures, no fallbacks
- CORONA extraction: 5 settlement fixtures (3 pass, 2 fail), 2 oracle fixtures (1 consistent, 1 divergent), calibration with `brier_type="binary"`, 5 functional fixtures, fallbacks include `"oracle_threshold_defaulted"`
- Never raises — returns `(ExtractionResult(success=False), None)` on failure

#### Task 1.2 — Write TREMOR extraction tests

**File:** `backend/tests/test_038b_external_orchestration.py` (APPEND)

**Description:** Add 4 tests for TREMOR enriched extraction. Tests use inline TREMOR construct.json content (parsed via `parse_construct_json()`), then call `extract_enriched_fixture("tremor", "0.1.0", meta)`.

| # | Test method | What it validates |
|---|---|---|
| 8 | `test_tremor_enriched_settlement_pass_and_fail` | Settlement fixtures dict has 5 keys. Even-indexed templates (`magnitude_gate`, `swarm_watch`, `oracle_divergence`) have `predicted_outcome == actual_outcome`. Odd-indexed (`aftershock_cascade`, `depth_regime`) have `predicted_outcome != actual_outcome`. `aftershock_cascade` (multi_bucket) uses bucket outcomes. |
| 9 | `test_tremor_enriched_oracle_consistent_and_divergent` | Oracle fixtures has 2 keys (`emsc`, `iris_dmc`). `emsc` has `delta < threshold`. `iris_dmc` has `delta > threshold`. |
| 10 | `test_tremor_enriched_calibration_multi_class` | Calibration fixture present. `brier_type == "multi_class"`. `expected_brier` is a float >= 0. |
| 11 | `test_tremor_enriched_functional_pass_and_fail` | Functional fixtures has 5 keys. First template (`magnitude_gate`) has `transform_valid=True`. Last template (`oracle_divergence`) has `transform_valid=False`. |

**Acceptance criteria:**
- 4 tests pass
- Tests parse TREMOR construct.json inline (no external file dependency)

#### Task 1.3 — Write CORONA extraction tests

**File:** `backend/tests/test_038b_external_orchestration.py` (APPEND)

**Description:** Add 4 tests for CORONA enriched extraction. Same pattern as TREMOR but with CORONA construct.json content.

| # | Test method | What it validates |
|---|---|---|
| 12 | `test_corona_enriched_settlement_pass_and_fail` | Settlement fixtures dict has 5 keys. Even-indexed pass, odd-indexed fail. T4 (multi_class) uses bucket outcomes. |
| 13 | `test_corona_enriched_oracle_with_default_threshold` | Oracle fixtures has 2 keys (`nasa_donki`, `gfz_potsdam`). `nasa_donki` consistent, `gfz_potsdam` divergent. `ExtractionResult.fallbacks_used` contains `"oracle_threshold_defaulted"`. |
| 14 | `test_corona_enriched_calibration_binary` | Calibration fixture present. `brier_type == "binary"`. |
| 15 | `test_corona_enriched_functional_pass_and_fail` | Functional fixtures has 5 keys. First (`T1`) has `transform_valid=True`. Last (`T5`) has `transform_valid=False`. |

**Acceptance criteria:**
- 4 tests pass
- CORONA fallbacks include `"oracle_threshold_defaulted"` (no verification_checks)

#### Task 1.4 — Write extraction edge-case tests

**File:** `backend/tests/test_038b_external_orchestration.py` (APPEND)

**Description:** Add 3 edge-case tests for extraction failures.

| # | Test method | What it validates |
|---|---|---|
| 16 | `test_extraction_missing_construct_json` | Call `parse_construct_json("")` -> `ValueError`. Verify orchestrator-level error handling can catch this. (Test that `extract_enriched_fixture` with a meta constructed from invalid input returns `success=False`.) |
| 17 | `test_extraction_empty_templates` | Construct a `TheatreConstructMeta` with `theatre_templates=[]`. Call `extract_enriched_fixture()`. Verify `ExtractionResult.success == False` and `error` mentions templates. |
| 18 | `test_extraction_malformed_metadata` | Construct a `TheatreConstructMeta` with minimal valid fields but no sources (empty `osint_sources`). Verify extraction still succeeds with empty oracle fixtures (graceful degradation, not failure). |

**Acceptance criteria:**
- 3 tests pass
- Edge cases produce `ExtractionResult` (never raise exceptions)

### Exit Criteria

- `backend/services/external_theatre_fixture_extractor.py` exists with `extract_enriched_fixture()` and 4 private helpers
- Sprint 0 tests still pass (7)
- Sprint 1 tests pass (11 new, 18 cumulative)
- `python -m pytest backend/tests/test_038b_external_orchestration.py -v` — 18 passed

---

## Sprint 2 — Orchestrator Composition

**Global ID:** 118
**Goal:** Compose extraction, check execution, bundle building, and candidate generation into one runtime flow with shared identity threading.

### Dependencies

- Sprint 1 complete (extractor importable and tested)
- `backend/services/theatre_policy_rules.py` (037d) — `parse_construct_json`, `plan_theatre_checks`
- `backend/services/theatre_check_runner.py` (037e) — `execute_theatre_checks`
- `backend/services/theatre_comparison_bundle_builder.py` (038a) — `build_comparison_bundle`
- `backend/services/theatre_comparison_candidates.py` (038a) — `generate_candidates`
- `backend/services/check_planner.py` — `PlannedCheck` dataclass

### Tasks

#### Task 2.1 — Create orchestrator service module

**File:** `backend/services/external_theatre_orchestrator.py` (NEW)

**Description:** Implement the orchestrator service per SDD section 2.3 with the following functions:

**Public function:**
- `prepare_external_theatres(request: ExternalTheatrePreparationRequest) -> ExternalTheatrePreparationResult`
  - Iterate `request.theatres`, call `_prepare_single_theatre()` for each
  - Collect successful bundles from `TheatrePreparationEntry.bundle`
  - Call `generate_candidates(bundles=successful_bundles)` for cross-theatre candidates
  - Call `_build_builder_feedback()` for each theatre with a non-None meta
  - Populate `total_theatres`, `total_successful`, `total_failed`
  - Echo `event_keys_used` and `scope_keys_used` from the request
  - Per-theatre errors do NOT abort the batch

**Private functions:**

1. `_prepare_single_theatre(theatre_input: ExternalTheatreInput, event_keys: list[str], scope_keys: list[TheatreScopeKey], certificate_id: Optional[str]) -> tuple[TheatrePreparationEntry, Optional[TheatreConstructMeta]]`
   - Step 1: `parse_construct_json(theatre_input.construct_json)` -> catch `ValueError` -> return entry with error
   - Step 2: `extract_enriched_fixture(slug, version, meta)` -> if `success=False`, return entry with error
   - Step 3: `plan_theatre_checks(spec_slug=slug, meta=meta)` -> convert via `_planned_checks_to_dicts()`
   - Step 4: `execute_theatre_checks(planned_dicts, fixture)` -> always returns result
   - Step 5: `build_comparison_bundle(execution_result, fixture, certificate_id, event_keys or None, scope_keys or None)`
   - **Critical None-vs-empty logic:** Pass `None` (not `[]`) for `event_keys`/`scope_keys` when caller's lists are empty, to trigger bundle builder's fallback behavior (SDD section 2.3, decision #4)
   - Sets `execution_passed = not execution_result.has_critical_failures`
   - Sets `execution_failed = execution_result.has_critical_failures`
   - Returns `(entry, meta)`

2. `_planned_checks_to_dicts(checks: list) -> list[dict]`
   - Convert `PlannedCheck` instances: `[{"check_id": c.check_id, "check_type": c.check_type} for c in checks]`
   - 3-line bridge function (SDD section 2.3, decision #2)

3. `_build_builder_feedback(construct_slug: str, meta: TheatreConstructMeta, extraction: ExtractionResult) -> BuilderFeedbackReport`
   - **Required items** (BLOCKED if missing): `theatre_templates` (at least one), construct name/slug
   - **Optional items** (DEGRADED if missing): `verification_checks`, `settlement_tiers`, explicit source IDs, `brier_type` on templates
   - **Extraction items**: Each fallback from `extraction.fallbacks_used`, success/failure per fixture category
   - **Readiness derivation** (SDD section 3.4):
     - `"BLOCKED"`: extraction failed or no templates
     - `"DEGRADED"`: extraction succeeded but fallbacks were used
     - `"READY"`: extraction succeeded with no fallbacks

**Imports:**
```python
from backend.services.theatre_policy_rules import parse_construct_json, TheatreConstructMeta
from backend.services.theatre_check_planner import plan_theatre_checks
from backend.services.theatre_check_runner import execute_theatre_checks
from backend.services.theatre_comparison_bundle_builder import build_comparison_bundle
from backend.services.theatre_comparison_candidates import generate_candidates
from backend.services.external_theatre_fixture_extractor import extract_enriched_fixture
from backend.schemas.external_theatre_orchestration import (
    ExternalTheatrePreparationRequest,
    ExternalTheatrePreparationResult,
    TheatrePreparationEntry,
    ExtractionResult,
    BuilderFeedbackReport,
    BuilderFeedbackItem,
)
```

**Acceptance criteria:**
- `from backend.services.external_theatre_orchestrator import prepare_external_theatres` importable
- Pure function — no DB, no AsyncSession, no network
- Per-theatre errors captured in `TheatrePreparationEntry.error`, remaining theatres still processed
- `candidates` only populated from successful bundles
- Empty `event_keys`/`scope_keys` passed as `None` to bundle builder

#### Task 2.2 — Write orchestrator composition tests

**File:** `backend/tests/test_038b_external_orchestration.py` (APPEND)

**Description:** Add 8 tests for the orchestrator. Tests use inline TREMOR and CORONA construct.json content.

| # | Test method | What it validates |
|---|---|---|
| 19 | `test_orchestrator_single_theatre` | Single TREMOR input -> `total_theatres=1`, `total_successful=1`, `theatres[0].bundle is not None`, `candidates == []` (need 2+ bundles for cross-comparison). |
| 20 | `test_orchestrator_paired_theatres` | TREMOR + CORONA inputs with `event_keys=["earthquake_2026_01"]`, `scope_keys=[TheatreScopeKey(region="pacific_ring", entity="usgs", time_window="2026-Q1")]` -> `total_theatres=2`, `total_successful=2`, `len(candidates) >= 1`. |
| 21 | `test_orchestrator_shared_identity_threading` | TREMOR + CORONA with explicit `event_keys=["eq_7.2"]` -> verify `result.event_keys_used == ["eq_7.2"]`. Verify bundles contain the shared event keys (check `bundle.event_keys`). |
| 22 | `test_orchestrator_no_keys_fallback` | TREMOR + CORONA with `event_keys=[]`, `scope_keys=[]` -> verify bundles get template-ID fallback keys (from `fixture.settlement_fixtures.keys()`). |
| 23 | `test_orchestrator_error_propagation` | First theatre: invalid JSON `construct_json="{bad"`. Second theatre: valid TREMOR. -> `total_successful=1`, `total_failed=1`. First entry has `error` populated. Second entry has `bundle`. |
| 24 | `test_orchestrator_all_failures` | Both theatres have invalid JSON -> `total_failed=2`, `candidates == []`, `total_successful=0`. |
| 25 | `test_orchestrator_certificate_id_threading` | TREMOR input with `certificate_id="cert-abc"` -> `theatres[0].bundle.certificate_id == "cert-abc"`. |
| 26 | `test_orchestrator_empty_request` | `ExternalTheatrePreparationRequest(theatres=[])` -> `total_theatres=0`, empty everything. |

**Acceptance criteria:**
- 8 tests pass
- Tests exercise the full pipeline: parse -> extract -> plan -> execute -> bundle -> candidates

### Exit Criteria

- `backend/services/external_theatre_orchestrator.py` exists with `prepare_external_theatres()` and 3 private helpers
- Sprint 0+1 tests still pass (18)
- Sprint 2 tests pass (8 new, 26 cumulative)
- `python -m pytest backend/tests/test_038b_external_orchestration.py -v` — 26 passed

---

## Sprint 3 — 038 Scanner Compatibility + Builder Feedback

**Global ID:** 119
**Goal:** Prove the orchestrated output is consumable by the existing 038 paradox scanner input shape and that builder feedback correctly distinguishes TREMOR vs CORONA metadata quality.

### Dependencies

- Sprint 2 complete (orchestrator functional)
- `backend/services/cross_theatre_paradox_scanner.py` (038) — `CrossTheatreParadoxScanner` input expectations
- `backend/schemas/theatre_comparison_bundle.py` (038a) — `ComparisonCandidateSet` field requirements

### Tasks

#### Task 3.1 — Write 038 scanner compatibility tests

**File:** `backend/tests/test_038b_external_orchestration.py` (APPEND)

**Description:** Add 3 tests proving the orchestrated output matches what the 038 scanner expects.

| # | Test method | What it validates |
|---|---|---|
| 27 | `test_candidates_consumable_by_scanner_input` | Run full orchestration (TREMOR + CORONA with shared event keys). Each `ComparisonCandidateSet` in result has: `bundle_a` and `bundle_b` with `construct_slug`, `settlement_state`, `check_summary`, `event_keys`, `scope_keys` fields. These are the fields the 038 `CrossTheatreParadoxScanner` reads for paradox detection. |
| 28 | `test_disputed_bundle_from_enriched_fixtures` | Run single TREMOR through orchestration. Because enriched fixtures include failing templates (odd-indexed), verify `theatres[0].bundle.settlement_state == "DISPUTED"` (not `"SETTLED"`). This proves enriched extraction enables non-trivial bundle states. |
| 29 | `test_settled_vs_disputed_cross_comparison` | Run TREMOR + CORONA orchestration. Verify at least one `ComparisonCandidateSet` exists — exercising the cross-comparison path that all-passing fixtures could never meaningfully reach. |

**Acceptance criteria:**
- 3 tests pass
- Candidate fields match 038 scanner expectations (no schema mismatches)

#### Task 3.2 — Write builder feedback tests

**File:** `backend/tests/test_038b_external_orchestration.py` (APPEND)

**Description:** Add 5 tests for builder feedback quality.

| # | Test method | What it validates |
|---|---|---|
| 30 | `test_tremor_feedback_required_present` | Run TREMOR through orchestration. Feedback for TREMOR: all required items have `status="present"`. `overall_readiness == "READY"` (TREMOR has all metadata). |
| 31 | `test_corona_feedback_optional_missing` | Run CORONA through orchestration. Feedback for CORONA: `optional_items` includes items for `verification_checks` and `settlement_tiers` with `status="missing"`. `overall_readiness == "DEGRADED"` (fallbacks used). |
| 32 | `test_tremor_feedback_extraction_summary` | Run TREMOR through orchestration. Feedback `extraction_items` includes entries for settlement, oracle, calibration, functional categories with status information. |
| 33 | `test_feedback_blocked_on_missing_templates` | Construct a `TheatreConstructMeta` with `theatre_templates=[]`. Run through `_build_builder_feedback()` with a failed `ExtractionResult`. Verify `overall_readiness == "BLOCKED"`. |
| 34 | `test_end_to_end_tremor_corona_preparation` | Full pipeline: TREMOR + CORONA with `event_keys=["geomagnetic_storm_2026"]`, `scope_keys=[TheatreScopeKey(region="global", entity="noaa", time_window="2026-03")]`. Verify: `total_theatres=2`, `total_successful=2`, `len(candidates) >= 1`, `len(feedback) == 2`, `event_keys_used == ["geomagnetic_storm_2026"]`. This is the comprehensive end-to-end acceptance test. |

**Acceptance criteria:**
- 5 tests pass
- TREMOR feedback shows `"READY"`, CORONA shows `"DEGRADED"`
- End-to-end test exercises full pipeline with shared identity

### Exit Criteria

- All Sprint 0–2 tests still pass (26)
- Sprint 3 tests pass (8 new, 34 cumulative)
- `python -m pytest backend/tests/test_038b_external_orchestration.py -v` — 34 passed
- All 8 PRD acceptance criteria satisfied:
  1. TREMOR fixture built without manual dicts (tests 8–11, 28)
  2. CORONA fixture built without manual dicts (tests 12–15)
  3. Both pass+fail scenarios present (tests 8, 12, 28)
  4. Shared identity flows through orchestration (tests 21, 34)
  5. Real `ComparisonCandidateSet` outputs (tests 20, 27, 34)
  6. Candidates consumable by 038 scanner (tests 27, 29)
  7. Builder feedback distinguishes required/optional (tests 30, 31, 33)
  8. >=30 tests pass (34 total)

---

## Sprint Summary

| Sprint | Global ID | Focus | New Tests | Cumulative | Files Created/Modified |
|---|---|---|---|---|---|
| 0 | 116 | Schemas + extraction contracts | 7 | 7 | `backend/schemas/external_theatre_orchestration.py` (NEW), `backend/tests/test_038b_external_orchestration.py` (NEW) |
| 1 | 117 | Enriched fixture extraction | 11 | 18 | `backend/services/external_theatre_fixture_extractor.py` (NEW), test file (APPEND) |
| 2 | 118 | Orchestrator composition | 8 | 26 | `backend/services/external_theatre_orchestrator.py` (NEW), test file (APPEND) |
| 3 | 119 | 038 compatibility + builder feedback | 8 | 34 | test file (APPEND) |
| **Total** | | | **34** | **34** | **3 new source files, 1 test file** |

### Files Touched Summary

**New files (4):**
- `backend/schemas/external_theatre_orchestration.py` — Pydantic models (sprint 0)
- `backend/services/external_theatre_fixture_extractor.py` — Enriched extraction (sprint 1)
- `backend/services/external_theatre_orchestrator.py` — Composition service (sprint 2)
- `backend/tests/test_038b_external_orchestration.py` — 34 tests (sprints 0–3)

**Existing files read (not modified):**
- `backend/services/theatre_policy_rules.py` (037d)
- `backend/services/theatre_check_planner.py` (037d)
- `backend/services/theatre_check_runner.py` (037e)
- `backend/services/theatre_comparison_bundle_builder.py` (038a)
- `backend/services/theatre_comparison_candidates.py` (038a)
- `backend/schemas/theatre_execution.py` (037e)
- `backend/schemas/theatre_comparison_bundle.py` (038a)
- `backend/services/check_planner.py`

**Not touched:**
- No database models or Alembic migrations
- No API routes
- No frontend files
- `backend/services/theatre_fixture_loader.py` — NOT modified (enriched extractor is a separate path)
