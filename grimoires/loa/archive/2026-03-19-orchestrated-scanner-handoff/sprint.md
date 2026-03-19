# Sprint Plan — Cycle-038c: Orchestrated Scanner Handoff

**Cycle:** cycle-038c
**Date:** 19 March 2026
**Builder:** Loa (single agent, backend only)
**Sprints:** 4 (0–3)
**Global sprint IDs:** 120–123
**Test target:** >=28 new tests (PRD AC #9); SDD plans ~32
**New files:** 2 source + 1 test
**Modified files:** 0 (no existing files touched)

---

## Sprint 0 — Scan Result Schemas (Global 120)

**Goal:** Define the Pydantic models that represent scan request, per-candidate outcome, individual paradox findings, and aggregate scan result. These schemas are the handoff contract between the 038b orchestrator output and the 038c classification adapter.

### Dependencies

- `backend/schemas/theatre_comparison_bundle.py` must exist (038a) — imports `ComparisonCandidateSet`, `ExecutedTheatreComparisonBundle`, `TheatreScopeKey`
- `backend/schemas/external_theatre_orchestration.py` must exist (038b) — used for integration context only

### Task 0.1 — ParadoxFinding schema

**Description:** Create `backend/schemas/external_theatre_scan.py` with the `ParadoxFinding` model. This represents a single detected paradox — structurally aligned with the real 038 scanner's `CrossTheatreParadox` DB model output shape.

**Files:**
- Create `backend/schemas/external_theatre_scan.py`

**Implementation:**
- `ParadoxFinding(BaseModel)` with fields: `paradox_type: str`, `severity: str`, `description: str`, `evidence: dict`, `construct_a_slug: str`, `construct_b_slug: str`
- `paradox_type` values: `"SETTLEMENT_DIVERGENCE"` | `"ORACLE_INCONSISTENCY"` | `"TEMPORAL_DRIFT"` | `"SCOPE_OVERLAP_GAP"` — aligned with `CrossTheatreParadoxType` enum in `backend/database/models.py` and `ParadoxTypeEnum` in `backend/schemas/cross_theatre_paradox_schemas.py`
- `severity` values: `"INFO"` | `"WATCH"` | `"MATERIAL"` | `"CRITICAL"` — aligned with `CrossTheatreParadoxSeverity` enum and `ParadoxSeverityEnum`

**Acceptance criteria:**
- [ ] `ParadoxFinding` can be instantiated with all 4 paradox_type values
- [ ] `ParadoxFinding` can be instantiated with all 4 severity levels
- [ ] Evidence field accepts arbitrary dict

**Exit:** Schema importable, 1 test verifies construction with all types/severities.

---

### Task 0.2 — CandidateScanOutcome schema

**Description:** Add `CandidateScanOutcome` to `backend/schemas/external_theatre_scan.py`. Represents the complete scan result for one `ComparisonCandidateSet`.

**Files:**
- Modify `backend/schemas/external_theatre_scan.py` (same file as 0.1)

**Implementation:**
- `CandidateScanOutcome(BaseModel)` with fields: `construct_a_slug: str`, `construct_b_slug: str`, `candidate_type: str`, `match_strength: str`, `matching_keys: list[str]`, `findings: list[ParadoxFinding]` (default_factory=list), `scanned: bool = True`, `has_paradox: bool = False`
- `model_validator(mode="after")` sets `has_paradox = len(self.findings) > 0`

**Acceptance criteria:**
- [ ] Empty `findings` list yields `has_paradox=False`, `scanned=True`
- [ ] Non-empty `findings` list yields `has_paradox=True`
- [ ] `candidate_type`, `match_strength`, `matching_keys` all populate from `ComparisonCandidateSet` values

**Exit:** 2 tests — one no-findings, one with-findings.

---

### Task 0.3 — ExternalTheatreScanRequest + ExternalTheatreScanResult schemas

**Description:** Add `ExternalTheatreScanRequest` and `ExternalTheatreScanResult` to `backend/schemas/external_theatre_scan.py`.

**Files:**
- Modify `backend/schemas/external_theatre_scan.py` (same file)

**Implementation:**
- `ExternalTheatreScanRequest(BaseModel)`: `candidates: list[ComparisonCandidateSet]`, `event_keys: list[str]` (default_factory=list), `scope_keys: list[TheatreScopeKey]` (default_factory=list)
- Import `ComparisonCandidateSet` and `TheatreScopeKey` from `backend.schemas.theatre_comparison_bundle`
- `ExternalTheatreScanResult(BaseModel)`: `outcomes: list[CandidateScanOutcome]` (default_factory=list), `total_scanned: int = 0`, `total_with_findings: int = 0`, `total_clean: int = 0`

**Acceptance criteria:**
- [ ] `ExternalTheatreScanRequest` accepts a `ComparisonCandidateSet` list from 038b output
- [ ] `ExternalTheatreScanResult` computes correct totals (`total_scanned = len(outcomes)`, `total_with_findings = count where has_paradox`, `total_clean = total_scanned - total_with_findings`)

**Exit:** 2 tests — one for request construction, one for result totals.

---

### Task 0.4 — Schema tests

**Description:** Create the test file and write the 5 schema-level tests from SDD section 5.1.

**Files:**
- Create `tests/test_external_theatre_scan_adapter.py`

**Tests (5):**
1. `test_paradox_finding_construction` — ParadoxFinding accepts all 4 paradox_type values and all severity levels
2. `test_candidate_scan_outcome_no_findings` — CandidateScanOutcome with empty findings has `has_paradox=False`, `scanned=True`
3. `test_candidate_scan_outcome_with_findings` — CandidateScanOutcome with findings has `has_paradox=True`
4. `test_scan_request_from_candidates` — ExternalTheatreScanRequest accepts ComparisonCandidateSet list
5. `test_scan_result_totals` — ExternalTheatreScanResult computes correct `total_scanned` / `total_with_findings` / `total_clean`

**Acceptance criteria:**
- [ ] All 5 tests pass
- [ ] Tests import from `backend.schemas.external_theatre_scan`
- [ ] Tests use real `ComparisonCandidateSet` / `ExecutedTheatreComparisonBundle` instances (from `backend.schemas.theatre_comparison_bundle`)

**Dependencies:** Tasks 0.1, 0.2, 0.3

**Exit:** 5 tests pass. `pytest tests/test_external_theatre_scan_adapter.py -v` green.

---

### Sprint 0 Summary

| Metric | Value |
|--------|-------|
| New files | `backend/schemas/external_theatre_scan.py`, `tests/test_external_theatre_scan_adapter.py` |
| Tests | 5 |
| Exit gate | All 5 schema tests pass; both files importable |

---

## Sprint 1 — Classification Adapter + Detection Functions (Global 121)

**Goal:** Implement the pure-function classification adapter with all 4 detection functions and the `scan_candidates()` public API. This is the core logic of 038c.

### Dependencies

- Sprint 0 complete (all schemas defined and tested)
- `backend/services/cross_theatre_paradox_scanner.py` (038) — read-only, extracting classification logic
- `backend/schemas/theatre_comparison_bundle.py` (038a) — `ExecutedTheatreComparisonBundle`, `ComparisonCandidateSet`, `TheatreScopeKey`

### Task 1.1 — Module scaffold + constants + scan_candidates()

**Description:** Create `backend/services/external_theatre_scan_adapter.py` with module constants and the `scan_candidates()` public function that iterates candidates and assembles results.

**Files:**
- Create `backend/services/external_theatre_scan_adapter.py`

**Implementation:**
- Module constants: `ORACLE_TOLERANCE = 0.1`, `TEMPORAL_DRIFT_WINDOW = 24.0` (hours) — from real scanner lines 289 and 349
- `scan_candidates(request: ExternalTheatreScanRequest) -> ExternalTheatreScanResult`: iterates `request.candidates`, calls all 4 detection functions per pair, assembles `CandidateScanOutcome` per candidate, returns `ExternalTheatreScanResult` with correct totals
- Stub the 4 detection functions as `return None` initially (replaced in tasks 1.2–1.4)

**Acceptance criteria:**
- [ ] `scan_candidates()` is importable from `backend.services.external_theatre_scan_adapter`
- [ ] Empty candidates input returns `ExternalTheatreScanResult(total_scanned=0, total_clean=0, total_with_findings=0)`
- [ ] Constants match real scanner values (`ORACLE_TOLERANCE=0.1`, `TEMPORAL_DRIFT_WINDOW=24.0`)

**Exit:** Module importable; stub functions return None (all outcomes clean).

---

### Task 1.2 — _detect_settlement_divergence()

**Description:** Implement the settlement divergence detection function as specified in SDD section 2.2 Detection Function 1.

**Files:**
- Modify `backend/services/external_theatre_scan_adapter.py`

**Implementation:**
- `_detect_settlement_divergence(bundle_a: ExecutedTheatreComparisonBundle, bundle_b: ExecutedTheatreComparisonBundle) -> Optional[ParadoxFinding]`
- Classification logic (from SDD):
  1. If either `settlement_state` is None or `"PENDING"`: return None (insufficient data)
  2. If `settlement_state` values differ (e.g., `"SETTLED"` vs `"DISPUTED"`): fire paradox
  3. If `settlement_state` values match: compare `settlement_outcomes` on shared event keys — check if `"resolution"` values diverge
  4. Otherwise: return None
- Severity: always `MATERIAL` (matching real scanner line 202)
- Evidence dict keys: `construct_a_settlement_state`, `construct_b_settlement_state`, `construct_a_outcomes`, `construct_b_outcomes`, `divergent_keys`

**Tests (6) — add to `tests/test_external_theatre_scan_adapter.py`:**
1. `test_settlement_divergence_settled_vs_disputed` — SETTLED vs DISPUTED produces MATERIAL finding
2. `test_settlement_divergence_same_state_no_paradox` — Both SETTLED (same outcomes) produces None
3. `test_settlement_divergence_pending_skipped` — Either PENDING produces None
4. `test_settlement_divergence_none_state_skipped` — Either None state produces None
5. `test_settlement_divergence_outcome_values_differ` — Both SETTLED but different resolution values produces MATERIAL
6. `test_settlement_divergence_severity_always_material` — Confirm severity is always `"MATERIAL"`

**Acceptance criteria:**
- [ ] All 6 settlement tests pass
- [ ] Severity is always MATERIAL (matching real scanner line 202)
- [ ] Evidence dict contains all 5 specified keys

**Exit:** 6 tests pass.

---

### Task 1.3 — _detect_oracle_inconsistency()

**Description:** Implement oracle inconsistency detection as specified in SDD section 2.2 Detection Function 2.

**Files:**
- Modify `backend/services/external_theatre_scan_adapter.py`

**Implementation:**
- `_detect_oracle_inconsistency(bundle_a: ExecutedTheatreComparisonBundle, bundle_b: ExecutedTheatreComparisonBundle) -> Optional[ParadoxFinding]`
- Classification logic (from SDD):
  1. Collect all oracle source IDs from both bundles (`oracle_source_ids`)
  2. Find shared source IDs: `sources_a intersection sources_b`
  3. For each shared source: extract `value` from `oracle_values[source_id]`, check provisional revision (same source, different `is_provisional` -> INFO), compute delta, if delta > `ORACLE_TOLERANCE` (0.1) -> record MATERIAL finding
  4. If no shared sources but both bundles have oracle values: cross-source comparison — pick first available value from each, compute delta, if > `ORACLE_TOLERANCE` -> record WATCH finding
  5. Return highest-severity finding (MATERIAL > WATCH > INFO), or None
- Oracle delta computation: extracted from real scanner `_compute_oracle_delta()` (lines 476-490) — iterate union of keys from two value dicts, compute `abs(float(va) - float(vb))`, return max delta. For scalar values, `abs(float(a) - float(b))` directly.
- Evidence dict keys: `source_a`, `source_b`, `delta`, `tolerance`, `same_source`, `value_a`, `value_b`, `is_provisional_a`, `is_provisional_b`

**Tests (6) — add to test file:**
1. `test_oracle_delta_above_tolerance` — Delta 0.25 (same source) produces MATERIAL
2. `test_oracle_delta_below_tolerance_no_paradox` — Delta 0.05 (same source) produces None
3. `test_oracle_delta_at_tolerance_no_paradox` — Delta exactly 0.1 produces None (tolerance is `<=`, not `<`)
4. `test_oracle_cross_source_severity_watch` — Delta 0.3 (different sources) produces WATCH
5. `test_oracle_provisional_revision_info` — Same source, one provisional produces INFO
6. `test_oracle_no_shared_sources_no_values` — No oracle_values in either bundle produces None

**Acceptance criteria:**
- [ ] All 6 oracle tests pass
- [ ] Threshold is 0.1 (10%) matching real scanner line 289
- [ ] Same-source severity = MATERIAL, cross-source = WATCH, provisional = INFO

**Exit:** 6 tests pass.

---

### Task 1.4 — _detect_temporal_drift() + _detect_scope_overlap_gap()

**Description:** Implement the remaining two detection functions as specified in SDD section 2.2 Detection Functions 3 and 4.

**Files:**
- Modify `backend/services/external_theatre_scan_adapter.py`

**Implementation — `_detect_temporal_drift(bundle_a, bundle_b) -> Optional[ParadoxFinding]`:**
- Extract non-None `"queried_at"` values from `oracle_values` entries in both bundles
- If either collection empty: return None (insufficient data)
- Parse ISO timestamps, compute `delta_hours` as max temporal separation between the two bundles' oracle query times
- If `delta_hours <= TEMPORAL_DRIFT_WINDOW` (24.0): return None
- If `delta_hours > 2 * TEMPORAL_DRIFT_WINDOW` (48.0): severity = WATCH
- Else (24-48h): severity = INFO
- Evidence dict keys: `delta_hours` (rounded to 2dp), `window_hours` (24.0), `time_a` (ISO string or None), `time_b` (ISO string or None)

**Implementation — `_detect_scope_overlap_gap(bundle_a, bundle_b, candidate: ComparisonCandidateSet) -> Optional[ParadoxFinding]`:**
- Only fires for `overlap_scope` candidates (return None for `same_event`)
- Normalize scope keys using `TheatreScopeKey.key()`
- `scopes_a = set(k.key() for k in bundle_a.scope_keys)`
- `scopes_b = set(k.key() for k in bundle_b.scope_keys)`
- `missing_from_a = scopes_b - scopes_a`, `missing_from_b = scopes_a - scopes_b`
- If neither has missing scopes: return None (full coverage)
- Severity: WATCH (matching real scanner line 428)
- Evidence dict keys: `construct_a_scopes`, `construct_b_scopes`, `missing_from_a`, `missing_from_b`, `candidate_match_strength`

**Tests (5) — add to test file:**
1. `test_temporal_drift_within_window_no_paradox` — Delta 12h produces None
2. `test_temporal_drift_beyond_window_info` — Delta 30h produces INFO
3. `test_temporal_drift_beyond_double_window_watch` — Delta 50h produces WATCH
4. `test_scope_overlap_missing_coverage` — Bundle A has scope keys B lacks produces WATCH
5. `test_scope_overlap_full_coverage_no_paradox` — Identical scope keys produces None

**Acceptance criteria:**
- [ ] All 5 tests pass
- [ ] Temporal drift window = 24.0 hours matching real scanner line 349
- [ ] Scope overlap only fires for `overlap_scope` candidates
- [ ] Scope overlap severity is always WATCH

**Exit:** 5 tests pass. All 4 detection functions complete.

---

### Sprint 1 Summary

| Metric | Value |
|--------|-------|
| New files | `backend/services/external_theatre_scan_adapter.py` |
| Tests added | 17 (6 settlement + 6 oracle + 5 temporal/scope) |
| Running total | 22 tests (5 from sprint 0 + 17) |
| Exit gate | All 22 tests pass; `scan_candidates()` operational with all 4 detection functions |

---

## Sprint 2 — End-to-End Paths (Global 122)

**Goal:** Exercise the full orchestrator-to-adapter pipeline with both positive paradox and no-paradox scenarios using TREMOR/CORONA fixtures. Prove both outcome paths end to end.

### Dependencies

- Sprint 1 complete (all 4 detection functions implemented)
- TREMOR/CORONA constructs available as fixture data (from 037d/038a/038b)

### Task 2.1 — TREMOR end-to-end scan

**Description:** Test that TREMOR bundles flow through the full adapter pipeline. Build divergent TREMOR bundle pairs (one SETTLED, one DISPUTED) to trigger at least one settlement divergence finding.

**Files:**
- Modify `tests/test_external_theatre_scan_adapter.py`

**Implementation:**
- Build two TREMOR `ExecutedTheatreComparisonBundle` instances: one with `settlement_state="SETTLED"`, one with `settlement_state="DISPUTED"` (pass + fail scenarios from 038b enriched fixture pattern)
- Create `ComparisonCandidateSet` with `candidate_type="same_event"`, `matching_keys=["eq-market-001"]`, `match_strength="EXACT"`
- Wrap in `ExternalTheatreScanRequest`, call `scan_candidates()`
- Assert result has `total_scanned >= 1`, at least one finding with `paradox_type="SETTLEMENT_DIVERGENCE"`

**Tests (1):**
1. `test_e2e_tremor_scan` — TREMOR bundles through adapter; `construct_a_slug="tremor"` preserved; settlement divergence detected

**Acceptance criteria:**
- [ ] TREMOR bundles produce a valid `ExternalTheatreScanResult`
- [ ] `construct_a_slug` is `"tremor"` in the outcome
- [ ] At least one SETTLEMENT_DIVERGENCE finding

**Exit:** 1 test passes.

---

### Task 2.2 — CORONA end-to-end scan (no-paradox path)

**Description:** Test that CORONA bundles flow through the same pipeline with aligned data, producing explicit no-paradox.

**Files:**
- Modify `tests/test_external_theatre_scan_adapter.py`

**Implementation:**
- Build two CORONA `ExecutedTheatreComparisonBundle` instances with identical settlement states (`"SETTLED"`), identical outcomes, oracle values within tolerance (delta < 0.1)
- Create `ComparisonCandidateSet`, wrap in request, call `scan_candidates()`
- Assert `has_paradox=False`, `findings=[]`, `scanned=True`

**Tests (1):**
1. `test_e2e_corona_scan` — CORONA aligned bundles produce explicit no-paradox: `has_paradox=False`, `findings=[]`, `scanned=True`

**Acceptance criteria:**
- [ ] CORONA aligned bundles produce `has_paradox=False`
- [ ] `findings` list is empty
- [ ] `scanned=True` (evaluated, not skipped)

**Exit:** 1 test passes.

---

### Task 2.3 — TREMOR + CORONA cross-theatre scan

**Description:** Test cross-theatre comparison: TREMOR bundle vs CORONA bundle as a candidate pair. This is the core external theatre paradox detection scenario — two different constructs observing overlapping events with potentially divergent outcomes.

**Files:**
- Modify `tests/test_external_theatre_scan_adapter.py`

**Implementation:**
- Build TREMOR bundle with `settlement_state="SETTLED"` and CORONA bundle with `settlement_state="DISPUTED"`
- Add oracle values to both: same source with values differing by 0.3 (above 0.1 tolerance)
- Create `ComparisonCandidateSet` with `candidate_type="same_event"`, matching event keys
- Call `scan_candidates()`, verify both SETTLEMENT_DIVERGENCE and ORACLE_INCONSISTENCY findings present

**Tests (1):**
1. `test_e2e_tremor_corona_cross_theatre` — TREMOR + CORONA candidates scanned; `has_paradox=True`; both SETTLEMENT_DIVERGENCE and ORACLE_INCONSISTENCY findings present

**Acceptance criteria:**
- [ ] Cross-theatre scan produces `has_paradox=True`
- [ ] At least one SETTLEMENT_DIVERGENCE finding
- [ ] At least one ORACLE_INCONSISTENCY finding
- [ ] `construct_a_slug` and `construct_b_slug` are `"tremor"` and `"corona"` respectively

**Exit:** 1 test passes.

---

### Task 2.4 — No-paradox explicit results

**Description:** Verify that aligned bundles produce explicit no-paradox outcomes (not just absence of output). This proves PRD AC #2 and AC #5.

**Files:**
- Modify `tests/test_external_theatre_scan_adapter.py`

**Tests (3):**
1. `test_aligned_bundles_produce_empty_findings` — Two aligned bundles (same settlements, same oracle values within tolerance) produce `CandidateScanOutcome` with `findings=[]`, `has_paradox=False`
2. `test_scan_result_total_clean_accurate` — Result with 3 candidates (1 with findings, 2 clean) has `total_clean=2`, `total_with_findings=1`, `total_scanned=3`
3. `test_no_candidates_produces_empty_result` — Empty candidates list produces `ExternalTheatreScanResult` with `total_scanned=0`

**Acceptance criteria:**
- [ ] All 3 tests pass
- [ ] No-paradox is a first-class result (AC #5): `scanned=True`, `has_paradox=False`, `findings=[]`
- [ ] Totals are computed correctly for mixed outcomes

**Exit:** 3 tests pass.

---

### Task 2.5 — Provenance preservation end-to-end

**Description:** Verify that classification results preserve construct slugs, candidate match type, match keys, and per-pattern evidence through the full pipeline.

**Files:**
- Modify `tests/test_external_theatre_scan_adapter.py`

**Tests (1):**
1. `test_e2e_provenance_preservation` — Scan results carry `construct_a_slug`, `construct_b_slug`, `matching_keys`, `candidate_type` from orchestration input; `ParadoxFinding.evidence` contains source-construct-specific values; `ParadoxFinding.construct_a_slug` and `construct_b_slug` are populated

**Acceptance criteria:**
- [ ] `CandidateScanOutcome.construct_a_slug` matches input `bundle_a.construct_slug`
- [ ] `CandidateScanOutcome.construct_b_slug` matches input `bundle_b.construct_slug`
- [ ] `CandidateScanOutcome.candidate_type` matches input candidate type
- [ ] `CandidateScanOutcome.matching_keys` matches input matching keys
- [ ] `ParadoxFinding.construct_a_slug` and `construct_b_slug` are populated
- [ ] `ParadoxFinding.evidence` dict is non-empty with pattern-specific keys

**Exit:** 1 test passes.

---

### Sprint 2 Summary

| Metric | Value |
|--------|-------|
| New files | None (tests only) |
| Tests added | 7 (1 TREMOR + 1 CORONA + 1 cross-theatre + 3 no-paradox + 1 provenance) |
| Running total | 29 tests (22 + 7) |
| Exit gate | All 29 tests pass; both paradox and no-paradox paths exercised end to end with real construct names |

---

## Sprint 3 — Provenance Hardening + Regression (Global 123)

**Goal:** Verify provenance details in evidence dicts, ensure adapter alignment with real scanner thresholds, and confirm no regression on 038a/038b surfaces.

### Dependencies

- Sprint 2 complete (all end-to-end paths verified)
- 038a/038b source files exist and unchanged

### Task 3.1 — Evidence detail assertions

**Description:** Add targeted assertions on the evidence dicts produced by each detection function to ensure they carry the expected keys and values as specified in SDD sections for each detection function.

**Files:**
- Modify `tests/test_external_theatre_scan_adapter.py`

**Tests (3):**
1. `test_settlement_evidence_keys` — Settlement divergence finding's `evidence` dict contains keys: `construct_a_settlement_state`, `construct_b_settlement_state`, `construct_a_outcomes`, `construct_b_outcomes`, `divergent_keys`
2. `test_oracle_evidence_keys` — Oracle inconsistency finding's `evidence` dict contains keys: `source_a`, `source_b`, `delta`, `tolerance`, `same_source`, `value_a`, `value_b`, `is_provisional_a`, `is_provisional_b`; `tolerance` value is `0.1`
3. `test_temporal_drift_evidence_keys` — Temporal drift finding's `evidence` dict contains keys: `delta_hours`, `window_hours`, `time_a`, `time_b`; `window_hours` value is `24.0`

**Acceptance criteria:**
- [ ] All 3 tests pass
- [ ] Evidence key sets match SDD specification exactly
- [ ] `delta` values are numeric, `tolerance` is 0.1, `window_hours` is 24.0

**Exit:** 3 tests pass.

---

### Task 3.2 — Regression against 038a/038b surfaces

**Description:** Verify that 038c does not break existing 038a bundle builder, 038a candidate generator, or 038b orchestrator. These are import/shape regression tests that confirm no API changes leaked upstream.

**Files:**
- Modify `tests/test_external_theatre_scan_adapter.py`

**Tests (3):**
1. `test_existing_038b_orchestrator_unchanged` — Import `prepare_external_theatres` from `backend.services.external_theatre_orchestrator`; verify callable; verify it returns `ExternalTheatrePreparationResult` type (or verify the function signature includes `candidates` on the result type)
2. `test_existing_038a_bundle_builder_unchanged` — Import `build_comparison_bundle` from `backend.services.theatre_comparison_bundle_builder`; verify callable; verify return type is `ExecutedTheatreComparisonBundle`
3. `test_existing_038a_candidate_generator_unchanged` — Import `generate_candidates` from `backend.services.theatre_comparison_candidates`; verify callable; verify it accepts bundles and returns a list

**Acceptance criteria:**
- [ ] All 3 tests pass
- [ ] No modifications to any 038a/038b source files
- [ ] Import paths and function signatures unchanged

**Exit:** 3 tests pass.

---

### Sprint 3 Summary

| Metric | Value |
|--------|-------|
| New files | None (tests only) |
| Tests added | 6 (3 evidence + 3 regression) |
| Running total | 35 tests (29 + 6) |
| Exit gate | All 35 tests pass; full regression clean; `pytest tests/test_external_theatre_scan_adapter.py -v` green |

---

## Cycle Summary

| Sprint | Global ID | Label | New Files | Tests | Running Total |
|--------|-----------|-------|-----------|-------|---------------|
| 0 | 120 | Scan Result Schemas | `backend/schemas/external_theatre_scan.py` + `tests/test_external_theatre_scan_adapter.py` | 5 | 5 |
| 1 | 121 | Classification Adapter + Detection Functions | `backend/services/external_theatre_scan_adapter.py` | 17 | 22 |
| 2 | 122 | End-to-End Paths | — | 7 | 29 |
| 3 | 123 | Provenance Hardening + Regression | — | 6 | 35 |
| **Total** | | | **2 source + 1 test** | **35** | **35** |

### PRD Acceptance Criteria Mapping

| AC # | Description | Sprint | How Verified |
|------|-------------|--------|-------------|
| 1 | Pure-function adapter classifies using 4 detection patterns | 1 | Tasks 1.2–1.4: all 4 functions implemented + 17 tests |
| 2 | Aligned/no-paradox scenario end to end | 2 | Task 2.2 (CORONA clean) + Task 2.4 (explicit no-paradox) |
| 3 | Settlement divergence paradox end to end | 2 | Task 2.1 (TREMOR divergent) + Task 2.3 (cross-theatre) |
| 4 | Oracle inconsistency paradox end to end | 2 | Task 2.3 (TREMOR+CORONA cross-theatre with oracle delta > tolerance) |
| 5 | No-paradox and paradox both explicit result types | 0+2 | Task 0.2 (schema validator) + Task 2.4 (3 explicit tests) |
| 6 | Results preserve construct slugs, match keys, evidence | 2+3 | Task 2.5 (provenance) + Task 3.1 (evidence keys) |
| 7 | Same thresholds/severity as real scanner | 1 | Tasks 1.2–1.4: constants + severity assertions in all detection tests |
| 8 | TREMOR and CORONA participate as real fixtures | 2 | Tasks 2.1–2.3 |
| 9 | >=28 new tests | all | 35 tests total (exceeds 28 minimum) |

### Files Created (Complete List)

| File | Sprint | Purpose |
|------|--------|---------|
| `backend/schemas/external_theatre_scan.py` | 0 | ParadoxFinding, CandidateScanOutcome, ExternalTheatreScanRequest, ExternalTheatreScanResult |
| `backend/services/external_theatre_scan_adapter.py` | 1 | scan_candidates() + _detect_settlement_divergence() + _detect_oracle_inconsistency() + _detect_temporal_drift() + _detect_scope_overlap_gap() |
| `tests/test_external_theatre_scan_adapter.py` | 0–3 | All 35 tests |

### Files Read But Not Modified

| File | Read For |
|------|----------|
| `backend/services/cross_theatre_paradox_scanner.py` | Classification logic extraction (thresholds, severity rules, evidence shapes) |
| `backend/services/external_theatre_orchestrator.py` | Input surface (ExternalTheatrePreparationResult shape) |
| `backend/schemas/external_theatre_orchestration.py` | Pydantic model patterns, ComparisonCandidateSet import path |
| `backend/services/theatre_comparison_bundle_builder.py` | Bundle field semantics |
| `backend/services/theatre_comparison_candidates.py` | Candidate generation logic |
| `backend/schemas/theatre_comparison_bundle.py` | ExecutedTheatreComparisonBundle, ComparisonCandidateSet, TheatreScopeKey schemas |
| `backend/schemas/cross_theatre_paradox_schemas.py` | ParadoxTypeEnum, ParadoxSeverityEnum string value alignment |
| `backend/database/models.py` | CrossTheatreParadox model shape, enum definitions |
