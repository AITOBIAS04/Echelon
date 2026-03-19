# SDD — Cycle-038a: Theatre Execution Fixtures For Cross-Theatre Paradox

**Cycle:** cycle-038a
**Date:** 19 March 2026
**Builder:** Loa

---

## 1. Architecture Summary

Cycle 038a sits between local theatre execution (037e) and cross-theatre paradox detection (038):

```
037e TheatreExecutionResult (per-construct)
    ↓
038a ExecutedTheatreComparisonBundle (normalized)
    ↓
038a ComparisonCandidateSet (same-event / overlap-scope pairs)
    ↓
038 CrossTheatreParadoxScanner inputs (FactAnchorLink, OracleResponse)
```

This cycle does not duplicate 038 classifier logic. It normalizes executed theatre evidence into the shapes the paradox engine already consumes.

### 1.1 Upstream Contracts (037e — read-only)

| Type | Location | Purpose |
|------|----------|---------|
| `TheatreExecutionResult` | `backend/schemas/theatre_execution.py` | Aggregate check results per construct |
| `TheatreCheckResult` | `backend/schemas/theatre_execution.py` | Per-check outcome with evidence dict |
| `TheatreFixtureInput` | `backend/schemas/theatre_execution.py` | Normalized fixture inputs |

### 1.2 Downstream Consumers (038 — existing)

| Type | Location | Purpose |
|------|----------|---------|
| `FactAnchor` | `backend/database/models.py` | Real-world event reference |
| `FactAnchorLink` | `backend/database/models.py` | Theatre → event mapping |
| `OracleResponse` | `backend/database/models.py` | Oracle values at settlement |
| `CoherenceGroup` | `backend/database/models.py` | Theatre consistency expectations |
| `CrossTheatreParadoxScanner` | `backend/services/cross_theatre_paradox_scanner.py` | Detection logic |

038a produces comparison bundles and candidate sets. It does NOT call the paradox scanner directly — that remains 038's responsibility.

---

## 2. File-Level Design

### 2.1 Comparison Bundle Schemas

**New: `backend/schemas/theatre_comparison_bundle.py`**

```python
class TheatreCheckSummary(BaseModel):
    """Normalized summary of a single executed theatre check."""
    check_type: str                    # SETTLEMENT_ACCURACY | ORACLE_CONSISTENCY | ...
    status: str                        # PASSED | FAILED | SKIPPED
    is_critical: bool
    evidence: dict = Field(default_factory=dict)
    # Evidence shape varies by check_type — see §2.1.1


class TheatreExecutionSummary(BaseModel):
    """Aggregate execution summary across all checks for one construct."""
    checks: list[TheatreCheckSummary] = Field(default_factory=list)
    executed_count: int = 0
    passed_count: int = 0
    failed_count: int = 0
    skipped_count: int = 0
    has_critical_failures: bool = False


class TheatreScopeKey(BaseModel):
    """Normalized scope identifier for overlap matching."""
    scope_type: str                    # "region" | "entity" | "time_window" | "event"
    scope_value: str                   # e.g. "US-equities", "BTC-USD", "2026-Q1"


class ExecutedTheatreComparisonBundle(BaseModel):
    """Normalized bundle representing one theatre's executed verification state."""
    construct_slug: str
    construct_version: str
    certificate_id: str | None = None
    template_ids: list[str] = Field(default_factory=list)
    oracle_source_ids: list[str] = Field(default_factory=list)
    event_keys: list[str] = Field(default_factory=list)
    scope_keys: list[TheatreScopeKey] = Field(default_factory=list)
    settlement_state: str | None = None     # "SETTLED" | "PENDING" | "DISPUTED"
    settlement_outcomes: dict = Field(default_factory=dict)
    # Shape: {template_id: {"predicted_outcome", "actual_outcome", "resolution"}}
    oracle_values: dict = Field(default_factory=dict)
    # Shape: {source_id: {"value", "queried_at", "is_provisional"}}
    execution_summary: TheatreExecutionSummary
    provenance_refs: list[str] = Field(default_factory=list)
    confidence_signals: dict = Field(default_factory=dict)
    # Shape: {"brier_score": float|None, "calibration_valid": bool|None}


class ComparisonCandidateSet(BaseModel):
    """A pair of bundles identified as comparison candidates."""
    candidate_type: str                # "same_event" | "overlap_scope"
    bundle_a: ExecutedTheatreComparisonBundle
    bundle_b: ExecutedTheatreComparisonBundle
    matching_keys: list[str] = Field(default_factory=list)
    # For same_event: shared event_keys
    # For overlap_scope: shared scope_keys (serialized)
    match_strength: str = "EXACT"      # "EXACT" | "PARTIAL" | "WEAK"
```

#### 2.1.1 Evidence Shapes by Check Type

These map directly from 037e `TheatreCheckResult.evidence`:

| Check Type | Evidence Fields |
|-----------|----------------|
| SETTLEMENT_ACCURACY | `predicted_outcome`, `actual_outcome`, `oracle_value`, `oracle`, `resolution` |
| ORACLE_CONSISTENCY | `primary_value`, `cross_value`, `delta`, `threshold`, `source_name` |
| CALIBRATION_VALIDITY | `computed_brier`, `expected_brier`, `brier_type`, `n_predictions` |
| FUNCTIONAL_CORRECTNESS | `template_name`, `resolution`, `input_state`, `expected_output_state`, `transform_valid` |

### 2.2 Comparison Bundle Builder

**New: `backend/services/theatre_comparison_bundle_builder.py`**

```python
def build_comparison_bundle(
    execution_result: TheatreExecutionResult,
    fixture_input: TheatreFixtureInput,
    certificate_id: str | None = None,
) -> ExecutedTheatreComparisonBundle:
    """Transform 037e execution result into normalized comparison bundle."""
```

Mapping algorithm:

1. **Identity**: `construct_slug`, `construct_version` from `execution_result` / `fixture_input`
2. **Template IDs**: Collect from `fixture_input.settlement_fixtures.keys()` ∪ `fixture_input.functional_fixtures.keys()`
3. **Oracle source IDs**: Collect from `fixture_input.oracle_fixtures.keys()`
4. **Event keys**: Derive from settlement fixture template IDs (each template = one event)
5. **Scope keys**: Extract from fixture metadata — region/entity/time scope when present in evidence
6. **Settlement state**: Derive from check results — if any SETTLEMENT_ACCURACY check exists and all passed → `SETTLED`, any failed → `DISPUTED`, none executed → `PENDING`
7. **Settlement outcomes**: Map from SETTLEMENT_ACCURACY check evidence: `{template_id: {predicted_outcome, actual_outcome, resolution}}`
8. **Oracle values**: Map from ORACLE_CONSISTENCY check evidence: `{source_id: {value: primary_value, queried_at: None, is_provisional: False}}`
9. **Execution summary**: Project from `TheatreExecutionResult` properties
10. **Confidence signals**: Extract from CALIBRATION_VALIDITY evidence: `{brier_score: computed_brier, calibration_valid: status == PASSED}`
11. **Provenance refs**: Collect all `check_id` values from executed checks

TREMOR and CORONA mapping use the same builder — the theatre-specific differences are in the fixture data, not the builder logic.

### 2.3 Candidate-Set Generator

**New: `backend/services/theatre_comparison_candidates.py`**

```python
def generate_candidates(
    bundles: list[ExecutedTheatreComparisonBundle],
) -> list[ComparisonCandidateSet]:
    """Generate comparison candidates from a set of bundles."""
```

#### Same-Event Matching

For each pair (bundle_a, bundle_b) where `bundle_a.construct_slug != bundle_b.construct_slug`:

1. Compute `shared_events = set(bundle_a.event_keys) & set(bundle_b.event_keys)`
2. If `shared_events` is non-empty → emit `ComparisonCandidateSet(candidate_type="same_event", matching_keys=list(shared_events))`
3. Match strength: `EXACT` if all events shared, `PARTIAL` if subset

#### Overlap-Scope Matching

For each pair where same-event matching produced no candidates:

1. Serialize scope keys: `{f"{sk.scope_type}:{sk.scope_value}" for sk in bundle.scope_keys}`
2. Compute `shared_scopes = scope_set_a & scope_set_b`
3. If `shared_scopes` is non-empty → emit `ComparisonCandidateSet(candidate_type="overlap_scope", matching_keys=list(shared_scopes))`
4. Match strength: `EXACT` if all scopes shared, `PARTIAL` if >50%, `WEAK` if ≤50%

#### No-Match Behavior

Pairs with zero shared event keys and zero shared scope keys produce no candidates. This is expected — not all theatre constructs are comparable.

### 2.4 Fixture Utilities

**New: `backend/tests/fixtures/theatre_comparison_fixtures.py`**

Provides factory functions for deterministic test fixtures:

```python
def make_tremor_execution_result() -> TheatreExecutionResult:
    """TREMOR: 2 settlement checks (1 PASSED, 1 FAILED), 1 oracle check PASSED."""

def make_corona_execution_result() -> TheatreExecutionResult:
    """CORONA: 1 settlement check PASSED, 1 oracle check PASSED, 1 calibration PASSED."""

def make_tremor_fixture_input() -> TheatreFixtureInput:
    """Matching fixture input for TREMOR execution."""

def make_corona_fixture_input() -> TheatreFixtureInput:
    """Matching fixture input for CORONA execution."""

def make_tremor_bundle() -> ExecutedTheatreComparisonBundle:
    """Pre-built TREMOR comparison bundle."""

def make_corona_bundle() -> ExecutedTheatreComparisonBundle:
    """Pre-built CORONA comparison bundle."""
```

TREMOR and CORONA fixtures share one event key (`"us-equities-q1-2026"`) to enable same-event candidate generation, and share one scope key (`TheatreScopeKey(scope_type="region", scope_value="US-equities")`) to enable overlap-scope matching.

### 2.5 038 Surface Compatibility

**No new 038 code changes.** Compatibility verified by tests that prove:

1. Comparison bundle settlement outcomes can populate `FactAnchorLink.linked_entity_type` and `linked_entity_id` fields
2. Bundle oracle values can populate `OracleResponse.value_json`, `source`, `event_id` fields
3. Candidate sets produce the pairwise structure that `CrossTheatreParadoxScanner.scan_fact_anchor()` expects (two theatre links on the same anchor)
4. Bundle scope keys can inform `CoherenceGroup` membership decisions

038a does NOT write to these tables. It proves shape compatibility so 038 can consume bundles without special-casing.

---

## 3. Test Architecture

**New: `backend/tests/test_038a_theatre_comparison.py`**

| Area | Tests | What They Prove |
|------|-------|-----------------|
| Schema validation | 4 | Bundle, summary, scope key, candidate set all construct and serialize |
| Provenance preservation | 3 | Execution summary counts, check evidence, provenance refs survive projection |
| TREMOR bundle builder | 4 | TREMOR execution → bundle mapping, settlement outcomes, oracle values, confidence |
| CORONA bundle builder | 4 | CORONA execution → bundle mapping, same fields |
| Same-event candidates | 3 | Shared event keys → candidates, no shared keys → empty, match strength |
| Overlap-scope candidates | 3 | Shared scope keys → candidates, partial overlap, match strength |
| No-match behavior | 2 | Zero overlap → no candidates emitted |
| 038 compatibility | 4 | Settlement → FactAnchorLink shape, oracle → OracleResponse shape, scope → CoherenceGroup shape, pairwise → scanner input shape |
| End-to-end TREMOR↔CORONA | 3 | Full path: execution results → bundles → candidates → 038-compatible shapes |
| **Total** | **~30** | |

---

## 4. Risks and Mitigations

### 4.1 Duplicating The Linker

If 038a reimplements too much of 038 linking/classification, the roadmap gets muddy.

**Mitigation:** 038a stops at normalized bundles and candidate sets. 038 retains contradiction classification, severity assignment, and paradox persistence. 038a never calls `CrossTheatreParadoxScanner`.

### 4.2 Bundle Shape Too Repo-Specific

If the comparison bundle bakes in TREMOR or CORONA assumptions, future theatre pairs will be awkward.

**Mitigation:** Bundle shape is abstract. The builder maps from `TheatreExecutionResult` (any construct) to the bundle — theatre-specific details live only in fixture data, not in the schema or builder logic.

### 4.3 Losing Local Provenance

If the bundle strips too much local execution detail, paradox interpretation becomes weaker.

**Mitigation:** Evidence dicts are preserved verbatim from `TheatreCheckResult.evidence`. Settlement outcomes, oracle values, and confidence signals are extracted into dedicated fields for structured access. `provenance_refs` captures all executed check IDs.

### 4.4 Scope Key Granularity

Scope keys are free-form strings. If TREMOR uses `"US-equities"` and CORONA uses `"us_equities"`, overlap matching silently fails.

**Mitigation:** Builder normalizes scope values to lowercase-hyphenated form. Tests include a case-mismatch scenario to verify normalization.

---

## 5. Files Touched Summary

**New files:**

| File | Sprint |
|------|--------|
| `backend/schemas/theatre_comparison_bundle.py` | 0 |
| `backend/services/theatre_comparison_bundle_builder.py` | 1 |
| `backend/services/theatre_comparison_candidates.py` | 2 |
| `backend/tests/fixtures/theatre_comparison_fixtures.py` | 1 |
| `backend/tests/test_038a_theatre_comparison.py` | 0–3 |

**Existing files updated:** None. 038a is additive — no modifications to 037e or 038 code.

---

## 6. After This Cycle Ships

1. Executed local theatre verification becomes reusable comparison material
2. TREMOR and CORONA become canonical cross-theatre fixture sources
3. Cycle 038 can operate on normalized executed evidence rather than planned-only surfaces
4. The bundle→candidate→038-input pipeline is tested end-to-end
