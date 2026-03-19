# Sprint 117 (Cycle-038b Sprint 1) — Engineer Feedback

All good

## Verified

### 1. Dict Key Correctness (Runner Compatibility)

All four fixture types produce dicts with the exact keys that `theatre_check_runner.py` reads:

- **Settlement** (extractor lines 168-176): `predicted_outcome`, `actual_outcome`, `oracle_value`, `oracle`, `resolution` — runner reads all five at lines 123-141.
- **Oracle** (extractor lines 211-226): `primary_value`, `cross_value`, `threshold`, `source_name` — runner reads all at lines 184-212. Runner recomputes `delta` from primary/cross (line 198), so the pre-computed `delta` in the fixture is harmless extra data.
- **Calibration** (extractor lines 271-276): `predictions`, `outcomes`, `brier_type`, `expected_brier` — runner reads all at lines 237-260.
- **Functional** (extractor lines 317-323): `transform_valid`, `template_name`, `resolution`, `input_state`, `expected_output_state` — runner reads all at lines 304-319.

### 2. Pass/Fail Logic

Even-index pass, odd-index fail confirmed at line 150. For 5 templates: 3 pass (0,2,4), 2 fail (1,3). Single template: always passes. Multi-bucket/multi-class templates correctly use `bucket_0`/`bucket_2` outcomes instead of `YES`/`NO`.

### 3. ExtractionResult Fallback Tracking

- `"oracle_threshold_defaulted"` recorded when `verification_checks` is empty (CORONA) — confirmed at line 206, tested in test 13.
- `"brier_type_defaulted"` recorded when no template declares `brier_type` (CORONA) — confirmed at line 262, tested in test 14.
- TREMOR has both verification_checks and brier_type declarations, so no fallbacks — confirmed in test 9.

### 4. Edge Cases

- Empty templates: returns `success=False` with descriptive error (test 17).
- Invalid/empty JSON: `parse_construct_json` raises `ValueError` before extractor is called (test 16).
- No OSINT sources: extraction succeeds with 0 oracle fixtures (test 18).
- Single template: no failure scenarios, settlement passes, functional valid (test 18).

### 5. Import Correctness

All imports match SDD dependency declarations:
- `ExtractionResult` from `backend.schemas.external_theatre_orchestration`
- `TheatreFixtureInput` from `backend.schemas.theatre_execution`
- `TheatreConstructMeta`, `TheatreTemplate`, `OsintSource`, `VerificationCheck` from `backend.services.theatre_policy_rules`

### 6. Pattern Alignment with theatre_fixture_loader.py

The enriched extractor mirrors the existing `_build_deterministic_fixture()` exactly in structure:
- Same `TheatreFixtureInput` dataclass construction
- Same dict key names across all fixture types
- Identical `_compute_expected_brier` algorithm

### 7. Test Coverage

All 18 tests pass (7 sprint-0 + 11 sprint-1). Tests cover both constructs (TREMOR, CORONA), all fixture types, and three edge cases. Tests use inline construct JSON with `setUpClass` for efficient shared setup.

## Notes

- `settlement_tiers` parameter in `_build_enriched_settlement_fixtures` is accepted but unused in the function body. This is benign — the SDD signature includes it for future enrichment, and the caller correctly passes `meta.settlement_tiers`. No fix needed.
- The `_compute_expected_brier` function is a deliberate duplication of the one in `theatre_fixture_loader.py`. This is correct per SDD design decision #1 (separate extraction path, no modification of existing loader).
