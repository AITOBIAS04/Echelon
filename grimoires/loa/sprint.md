# Sprint Plan — Cycle-038a: Theatre Execution Fixtures For Cross-Theatre Paradox

**Cycle:** cycle-038a
**Date:** 19 March 2026
**Builder:** Loa
**Sprints:** 4 (0–3)

---

## Sprint 0 — Comparison Bundle Schemas + Fixture Factories

**Goal:** Define normalized bundle, summary, scope key, and candidate-set shapes. Create TREMOR/CORONA fixture factories.

### Tasks

1. **Add `backend/schemas/theatre_comparison_bundle.py`** — `TheatreCheckSummary`, `TheatreExecutionSummary`, `TheatreScopeKey`, `ExecutedTheatreComparisonBundle`, `ComparisonCandidateSet` models per SDD §2.1.
2. **Add `backend/tests/fixtures/theatre_comparison_fixtures.py`** — `make_tremor_execution_result()`, `make_corona_execution_result()`, `make_tremor_fixture_input()`, `make_corona_fixture_input()` factories. TREMOR and CORONA share one event key (`us-equities-q1-2026`) and one scope key (`region:US-equities`).
3. **Write schema + provenance tests** — 7 tests: 4 schema validation (construct, serialize, defaults, scope key), 3 provenance preservation (execution summary counts, check evidence survives projection, provenance refs populated).

**Exit:** 7 tests pass.

---

## Sprint 1 — Bundle Builder

**Goal:** Convert executed 037e theatre outputs into normalized comparison bundles.

### Tasks

1. **Add `backend/services/theatre_comparison_bundle_builder.py`** — `build_comparison_bundle(execution_result, fixture_input, certificate_id=None)` per SDD §2.2 10-step mapping algorithm.
2. **TREMOR bundle builder tests** — 4 tests: identity mapping, settlement outcomes from SETTLEMENT_ACCURACY evidence, oracle values from ORACLE_CONSISTENCY evidence, confidence signals from CALIBRATION_VALIDITY evidence.
3. **CORONA bundle builder tests** — 4 tests: same 4 dimensions for CORONA fixture data.

**Exit:** 8 tests pass (cumulative: 15).

---

## Sprint 2 — Candidate Sets

**Goal:** Generate same-event and overlap-scope comparison candidates from normalized bundles.

### Tasks

1. **Add `backend/services/theatre_comparison_candidates.py`** — `generate_candidates(bundles)` per SDD §2.3. Same-event matching on shared `event_keys`, overlap-scope matching on shared `scope_keys`, match strength classification.
2. **Same-event candidate tests** — 3 tests: shared event keys produce candidate, no shared keys produce empty, match strength (EXACT vs PARTIAL).
3. **Overlap-scope candidate tests** — 3 tests: shared scope keys produce candidate, partial overlap classification, scope key normalization (case-mismatch scenario from SDD §4.4).
4. **No-match behavior tests** — 2 tests: zero overlap produces no candidates, same-construct pair skipped.

**Exit:** 8 tests pass (cumulative: 23).

---

## Sprint 3 — 038 Compatibility + End-to-End Regression

**Goal:** Prove the bundle layer is consumable by the paradox engine and stable across both theatre fixtures.

### Tasks

1. **038 shape compatibility tests** — 4 tests: settlement outcomes → `FactAnchorLink` field shape, oracle values → `OracleResponse.value_json` shape, scope keys → `CoherenceGroup` membership shape, candidate pair → scanner pairwise input shape.
2. **End-to-end TREMOR↔CORONA tests** — 3 tests: full path (execution results → bundles → candidates → 038-compatible shapes), TREMOR↔CORONA same-event candidate exists, overlap-scope candidate exists.
3. **Verify no 037e/038 modifications** — confirm all new code is additive (no edits to existing services).

**Exit:** 7 tests pass (cumulative: 30).

---

## Sprint Summary

| Sprint | Focus | Tests | Cumulative |
|---|---|---|---|
| 0 | Schemas + fixture factories | 7 | 7 |
| 1 | Bundle builder | 8 | 15 |
| 2 | Candidate sets | 8 | 23 |
| 3 | 038 compatibility + e2e regression | 7 | 30 |
| **Total** | | **30** | |

---

## New Files

| File | Sprint |
|------|--------|
| `backend/schemas/theatre_comparison_bundle.py` | 0 |
| `backend/tests/fixtures/theatre_comparison_fixtures.py` | 0 |
| `backend/services/theatre_comparison_bundle_builder.py` | 1 |
| `backend/services/theatre_comparison_candidates.py` | 2 |
| `backend/tests/test_038a_theatre_comparison.py` | 0–3 |

## Existing Files Modified

None. Cycle 038a is purely additive.
