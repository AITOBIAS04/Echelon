# SDD — Cycle-038b: External Theatre Orchestration

**Cycle:** cycle-038b
**Date:** 19 March 2026
**Builder:** Loa
**Depends on:** Cycle-037d (theatre policy rules, construct.json parsing), Cycle-037e (check execution, fixture loading), Cycle-038a (bundle building, candidate generation)

---

## 1. Architecture Summary

Cycle 038b adds two new services and one new schema module that compose existing 037d/037e/038a services into a single operational path for external theatre repos:

```
ExternalTheatrePreparationRequest
  │  (event_keys, scope_keys, certificate_id, theatre inputs)
  │
  ▼
┌─────────────────────────────────────────────────┐
│ external_theatre_orchestrator.py                 │
│   prepare_external_theatres()                    │
│                                                  │
│   For each ExternalTheatreInput:                 │
│     1. parse_construct_json()          [037d]    │
│     2. extract_enriched_fixture()      [NEW]     │
│     3. plan_theatre_checks()           [037d]    │
│     4. execute_theatre_checks()        [037e]    │
│     5. build_comparison_bundle()       [038a]    │
│                                                  │
│   Then:                                          │
│     6. generate_candidates()           [038a]    │
│     7. build_feedback_report()         [NEW]     │
│                                                  │
│   Returns:                                       │
│     ExternalTheatrePreparationResult             │
└─────────────────────────────────────────────────┘
```

### Component Dependency Map

| Existing Service | Module | What 038b Calls |
|---|---|---|
| `parse_construct_json()` | `theatre_policy_rules.py` (037d) | Returns `TheatreConstructMeta` from raw JSON |
| `plan_theatre_checks()` | `theatre_check_planner.py` (037d) | Returns `list[PlannedCheck]` from meta |
| `execute_theatre_checks()` | `theatre_check_runner.py` (037e) | Returns `TheatreExecutionResult` from planned checks + fixture |
| `build_comparison_bundle()` | `theatre_comparison_bundle_builder.py` (038a) | Returns `ExecutedTheatreComparisonBundle` from execution result + fixture |
| `generate_candidates()` | `theatre_comparison_candidates.py` (038a) | Returns `list[ComparisonCandidateSet]` from bundles |

### New Components (This Cycle)

| Component | Module | Purpose |
|---|---|---|
| Enriched fixture extractor | `external_theatre_fixture_extractor.py` | Generate realistic fixtures (pass + fail) from construct metadata |
| Orchestrator | `external_theatre_orchestrator.py` | Compose full path with shared identity threading |
| Orchestration schemas | `external_theatre_orchestration.py` | Request/response/feedback Pydantic models |

---

## 2. File-Level Design

### 2.1 `backend/schemas/external_theatre_orchestration.py`

**Responsibilities:** Define all Pydantic models for the orchestration surface.

**Dependencies:**
- `backend.schemas.theatre_comparison_bundle.TheatreScopeKey`
- `backend.schemas.theatre_comparison_bundle.ExecutedTheatreComparisonBundle`
- `backend.schemas.theatre_comparison_bundle.ComparisonCandidateSet`

**Models:**

```python
from typing import Optional
from pydantic import BaseModel, Field
from backend.schemas.theatre_comparison_bundle import (
    ComparisonCandidateSet,
    ExecutedTheatreComparisonBundle,
    TheatreScopeKey,
)


class ExternalTheatreInput(BaseModel):
    """Descriptor for a single external theatre to prepare."""
    construct_slug: str               # "tremor" | "corona"
    construct_version: str            # "0.1.0"
    construct_json: str               # Raw construct.json content (not path)
    construct_json_path: Optional[str] = None  # Optional: for feedback reporting


class ExternalTheatrePreparationRequest(BaseModel):
    """Full orchestration request."""
    theatres: list[ExternalTheatreInput]
    event_keys: list[str] = Field(default_factory=list)
    scope_keys: list[TheatreScopeKey] = Field(default_factory=list)
    certificate_id: Optional[str] = None


class ExtractionResult(BaseModel):
    """Result of fixture extraction for one theatre."""
    construct_slug: str
    success: bool
    settlement_fixture_count: int = 0
    oracle_fixture_count: int = 0
    has_calibration: bool = False
    functional_fixture_count: int = 0
    has_failure_scenarios: bool = False
    fallbacks_used: list[str] = Field(default_factory=list)
    error: Optional[str] = None


class TheatrePreparationEntry(BaseModel):
    """Per-theatre preparation result within the orchestration."""
    construct_slug: str
    construct_version: str
    extraction: Optional[ExtractionResult] = None
    bundle: Optional[ExecutedTheatreComparisonBundle] = None
    execution_passed: bool = False
    execution_failed: bool = False
    error: Optional[str] = None


class BuilderFeedbackItem(BaseModel):
    """Single feedback item for external builder."""
    category: str          # "required" | "optional" | "extraction"
    field: str             # e.g. "verification_checks", "source_ids"
    status: str            # "present" | "missing" | "defaulted" | "enriched"
    message: str


class BuilderFeedbackReport(BaseModel):
    """Structured feedback for external theatre builder."""
    construct_slug: str
    required_items: list[BuilderFeedbackItem] = Field(default_factory=list)
    optional_items: list[BuilderFeedbackItem] = Field(default_factory=list)
    extraction_items: list[BuilderFeedbackItem] = Field(default_factory=list)
    overall_readiness: str  # "READY" | "DEGRADED" | "BLOCKED"


class ExternalTheatrePreparationResult(BaseModel):
    """Complete orchestration result."""
    theatres: list[TheatrePreparationEntry] = Field(default_factory=list)
    candidates: list[ComparisonCandidateSet] = Field(default_factory=list)
    feedback: list[BuilderFeedbackReport] = Field(default_factory=list)
    event_keys_used: list[str] = Field(default_factory=list)
    scope_keys_used: list[TheatreScopeKey] = Field(default_factory=list)
    total_theatres: int = 0
    total_successful: int = 0
    total_failed: int = 0
```

**Design decisions:**
- `construct_json` is raw string content, not a file path. The orchestrator does not do filesystem I/O -- the caller loads the file.
- `TheatreFixtureInput` is a dataclass (not Pydantic), so `ExtractionResult` stores summary fields rather than embedding it directly. The actual `TheatreFixtureInput` object is consumed by the runner within the orchestrator and does not need to appear in the result model.
- `BuilderFeedbackReport` uses three categories (required/optional/extraction) matching the PRD feedback surface contract.

---

### 2.2 `backend/services/external_theatre_fixture_extractor.py`

**Responsibilities:**
- Generate enriched `TheatreFixtureInput` from `TheatreConstructMeta`
- Produce both passing AND failing fixture scenarios (unlike `_build_deterministic_fixture()` which only produces all-passing)
- Derive construct-specific thresholds from metadata
- Return `ExtractionResult` with fallback tracking

**Dependencies:**
- `backend.schemas.theatre_execution.TheatreFixtureInput`
- `backend.services.theatre_policy_rules.TheatreConstructMeta`, `TheatreTemplate`, `OsintSource`, `VerificationCheck`
- `backend.schemas.external_theatre_orchestration.ExtractionResult`

**Key functions:**

```python
def extract_enriched_fixture(
    construct_slug: str,
    construct_version: str,
    meta: TheatreConstructMeta,
) -> tuple[ExtractionResult, Optional[TheatreFixtureInput]]:
    """Extract enriched TheatreFixtureInput from construct metadata.

    Improvements over _build_deterministic_fixture():
    1. Settlement fixtures include BOTH passing and failing templates
    2. Oracle fixtures use construct-specific divergence thresholds
    3. Multi-bucket templates get multi-class outcomes
    4. Calibration fixtures derive Brier type from construct scoring
    5. Functional fixtures include failing state transitions

    Returns (ExtractionResult, TheatreFixtureInput or None on failure).
    """
```

```python
def _build_enriched_settlement_fixtures(
    templates: list[TheatreTemplate],
    settlement_tiers: list[dict],
) -> tuple[dict, list[str]]:
    """Build settlement fixtures with pass/fail scenarios.

    Strategy:
    - Even-indexed templates (0, 2, 4...): passing (predicted == actual)
    - Odd-indexed templates (1, 3, 5...): failing (predicted != actual)
    - Single template: always passing (do not fail the only template)
    - Multi-bucket templates: multi-class outcomes (not coerced to binary)

    Returns (fixtures_dict, fallbacks_used).
    """
```

```python
def _build_enriched_oracle_fixtures(
    sources: list[OsintSource],
    verification_checks: list[VerificationCheck],
) -> tuple[dict, list[str]]:
    """Build oracle fixtures with construct-specific thresholds.

    Strategy:
    - Cross-validation sources get oracle fixtures
    - Threshold derived from verification_checks when present
    - Default 0.5 threshold when no verification_checks declared
    - First cross-validation source: consistent (delta < threshold)
    - Second+ cross-validation source: divergent (delta > threshold)

    Returns (fixtures_dict, fallbacks_used).
    """
```

```python
def _build_enriched_calibration_fixture(
    meta: TheatreConstructMeta,
) -> tuple[Optional[dict], list[str]]:
    """Build calibration fixture from construct Brier scoring metadata.

    Strategy:
    - Derive brier_type from template metadata:
      - Any template with brier_type="multi_class" -> multi_class
      - Otherwise -> binary
    - If no brier_type declared anywhere, default to "binary" + track fallback
    - Generate predictions/outcomes that produce a known Brier score

    Returns (calibration_dict_or_None, fallbacks_used).
    """
```

```python
def _build_enriched_functional_fixtures(
    templates: list[TheatreTemplate],
) -> tuple[dict, list[str]]:
    """Build functional fixtures with pass/fail scenarios.

    Strategy:
    - First template: transform_valid=True (OPEN -> RESOLVED)
    - Last template: transform_valid=False (exercises FAILED path)
    - Single template: passing only (do not fail the only template)

    Returns (fixtures_dict, fallbacks_used).
    """
```

```python
def _compute_expected_brier(predictions: list[float], outcomes: list[float]) -> float:
    """Compute expected binary Brier score for fixture validation.

    Same algorithm as theatre_fixture_loader._compute_expected_brier().
    """
```

**Design decisions:**

1. **Enrichment vs replacement:** This module does NOT modify or monkey-patch `_build_deterministic_fixture()` in `theatre_fixture_loader.py`. It is a separate extraction path that the orchestrator calls. The existing fixture loader continues to serve its original purpose (smoke-test all-passing fixtures).

2. **Return type:** The function returns a tuple `(ExtractionResult, Optional[TheatreFixtureInput])` rather than embedding the fixture in the Pydantic model. This keeps the `TheatreFixtureInput` dataclass usable by the runner without serialization overhead, while `ExtractionResult` provides the metadata summary for the orchestrator result.

3. **Deterministic failure scenarios:** Even-indexed templates pass, odd-indexed fail. With 2+ templates this guarantees at least one passing and one failing, enabling DISPUTED settlement state derivation. With exactly 1 template, it always passes (do not fail the only template, which would make every single-template construct produce nothing useful).

4. **Threshold derivation:** When `verification_checks` are present in the construct metadata (TREMOR has 5, CORONA has 0), the extractor notes their presence for feedback. Thresholds for oracle fixtures default to 0.5 when no checks are declared. The `fallbacks_used` list tracks `"oracle_threshold_defaulted"` when this happens.

5. **Multi-class handling:** Templates with `resolution="multi_bucket"` or `resolution="multi_class"` get multi-class outcomes (`"bucket_0"`, `"bucket_1"`, etc.) rather than being coerced to binary `"YES"`/`"NO"`.

---

### 2.3 `backend/services/external_theatre_orchestrator.py`

**Responsibilities:**
- Compose the full external theatre preparation path
- Thread shared `event_keys` / `scope_keys` through bundle building
- Produce comparison candidates from all successful bundles
- Generate builder feedback reports
- Handle per-theatre errors without failing the entire batch

**Dependencies:**
- `backend.services.theatre_policy_rules.parse_construct_json` (037d)
- `backend.services.theatre_check_planner.plan_theatre_checks` (037d)
- `backend.services.theatre_check_runner.execute_theatre_checks` (037e)
- `backend.services.theatre_comparison_bundle_builder.build_comparison_bundle` (038a)
- `backend.services.theatre_comparison_candidates.generate_candidates` (038a)
- `backend.services.external_theatre_fixture_extractor.extract_enriched_fixture` (this cycle)
- All schemas from `backend.schemas.external_theatre_orchestration`

**Key functions:**

```python
def prepare_external_theatres(
    request: ExternalTheatrePreparationRequest,
) -> ExternalTheatrePreparationResult:
    """Orchestrate full external theatre preparation.

    For each theatre in the request:
    1. Parse construct.json -> TheatreConstructMeta
    2. Extract enriched fixture -> TheatreFixtureInput
    3. Plan theatre checks -> list[PlannedCheck]
    4. Execute checks -> TheatreExecutionResult
    5. Build comparison bundle with shared event_keys/scope_keys

    Then:
    6. Generate cross-theatre candidates from all successful bundles
    7. Build builder feedback for each theatre

    Error handling: Per-theatre failures are captured in
    TheatrePreparationEntry.error and do not abort the remaining theatres.
    Candidate generation runs only on successful bundles.
    """
```

```python
def _prepare_single_theatre(
    theatre_input: ExternalTheatreInput,
    event_keys: list[str],
    scope_keys: list[TheatreScopeKey],
    certificate_id: Optional[str],
) -> tuple[TheatrePreparationEntry, Optional[TheatreConstructMeta]]:
    """Prepare a single external theatre through the full pipeline.

    Calls:
    1. parse_construct_json(theatre_input.construct_json)
    2. extract_enriched_fixture(slug, version, meta)
    3. plan_theatre_checks(slug, meta)
    4. execute_theatre_checks(planned_checks_as_dicts, fixture)
    5. build_comparison_bundle(execution_result, fixture, certificate_id,
       event_keys, scope_keys)

    Returns (TheatrePreparationEntry, TheatreConstructMeta or None).
    The meta is returned separately for feedback generation.
    """
```

```python
def _planned_checks_to_dicts(checks: list) -> list[dict]:
    """Convert PlannedCheck dataclass instances to dicts for the runner.

    The theatre_check_runner.execute_theatre_checks() expects list[dict]
    with "check_type" and "check_id" keys. PlannedCheck is a dataclass
    with those field names. This converts via dataclasses.asdict() or
    explicit field extraction.
    """
```

```python
def _build_builder_feedback(
    construct_slug: str,
    meta: TheatreConstructMeta,
    extraction: ExtractionResult,
) -> BuilderFeedbackReport:
    """Generate structured feedback for an external theatre builder.

    Required metadata (BLOCKED if missing):
    - theatre_templates (at least one)
    - construct name/slug

    Optional enrichment (DEGRADED if missing, recommendations):
    - verification_checks (TREMOR has, CORONA does not)
    - settlement_tiers (TREMOR has, CORONA does not)
    - explicit source IDs (TREMOR has, CORONA derives from name)
    - brier_type on templates

    Extraction feedback:
    - Each fallback from ExtractionResult.fallbacks_used
    - Success/failure per fixture category
    """
```

**Design decisions:**

1. **Synchronous, no DB:** `prepare_external_theatres()` is a pure function (no `AsyncSession`, no database dependency). All called services (037d/037e/038a) are already synchronous pure functions. This keeps the orchestrator testable without DB mocking.

2. **PlannedCheck -> dict conversion:** `execute_theatre_checks()` accepts `list[dict]`, using `check.get("check_type")` and `check.get("check_id")` internally. The `PlannedCheck` dataclass from `check_planner.py` has fields `check_type`, `check_id`, `domain`, `source`, `critical`, `asset_id`, `anchor_class`. The orchestrator converts via:

```python
def _planned_checks_to_dicts(checks: list) -> list[dict]:
    return [
        {"check_id": c.check_id, "check_type": c.check_type}
        for c in checks
    ]
```

This bridges the 037d planner output format to the 037e runner input format.

3. **Per-theatre error isolation:** A `ValueError` from `parse_construct_json()` (malformed JSON) or an extraction failure captures the error message in `TheatrePreparationEntry.error` and continues processing remaining theatres. The orchestrator wraps each theatre's pipeline in a try/except.

4. **Shared identity threading:** `event_keys` and `scope_keys` from the request flow directly to `build_comparison_bundle()` via its existing `event_keys` and `scope_keys` keyword arguments. When both are empty, the orchestrator passes `None` (not `[]`) to trigger the bundle builder's fallback behavior:
   - `event_keys=None` -> falls back to `sorted(fixture_input.settlement_fixtures.keys())` (template IDs)
   - `scope_keys=None` -> falls back to `_extract_scope_keys()` which returns `[]`

This is correct because passing an empty list `[]` would be treated as "caller explicitly supplied zero keys" while `None` means "caller did not supply keys, use fallback."

5. **No-keys fallback:** When `event_keys=[]` and `scope_keys=[]`, the orchestrator passes `None` to get template-ID fallback. If the caller explicitly wants no keys (unlikely), they can pass a sentinel. This matches the PRD's "no-keys fallback" acceptance criterion.

---

## 3. Schema Design -- Detailed Field Definitions

### 3.1 ExternalTheatreInput

| Field | Type | Required | Description |
|---|---|---|---|
| `construct_slug` | `str` | Yes | Construct identifier ("tremor", "corona") |
| `construct_version` | `str` | Yes | Construct version ("0.1.0") |
| `construct_json` | `str` | Yes | Raw JSON content of construct.json |
| `construct_json_path` | `Optional[str]` | No | Original filesystem path (for feedback messages only) |

### 3.2 ExternalTheatrePreparationRequest

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `theatres` | `list[ExternalTheatreInput]` | Yes | -- | 1+ theatre inputs to prepare |
| `event_keys` | `list[str]` | No | `[]` | Shared real-world event identifiers |
| `scope_keys` | `list[TheatreScopeKey]` | No | `[]` | Shared scope identifiers |
| `certificate_id` | `Optional[str]` | No | `None` | Optional verification certificate reference |

### 3.3 ExtractionResult

| Field | Type | Default | Description |
|---|---|---|---|
| `construct_slug` | `str` | -- | Which construct this extraction is for |
| `success` | `bool` | -- | Whether extraction succeeded |
| `settlement_fixture_count` | `int` | `0` | Number of settlement fixtures generated |
| `oracle_fixture_count` | `int` | `0` | Number of oracle fixtures generated |
| `has_calibration` | `bool` | `False` | Whether calibration fixture was generated |
| `functional_fixture_count` | `int` | `0` | Number of functional fixtures generated |
| `has_failure_scenarios` | `bool` | `False` | Whether enriched failures were included |
| `fallbacks_used` | `list[str]` | `[]` | Named fallbacks applied during extraction |
| `error` | `Optional[str]` | `None` | Error message if extraction failed |

### 3.4 BuilderFeedbackReport

| Field | Type | Description |
|---|---|---|
| `construct_slug` | `str` | Construct this feedback is for |
| `required_items` | `list[BuilderFeedbackItem]` | Hard requirements (blocks if missing) |
| `optional_items` | `list[BuilderFeedbackItem]` | Optional enrichments (recommendations) |
| `extraction_items` | `list[BuilderFeedbackItem]` | Extraction-time observations |
| `overall_readiness` | `str` | `"READY"` / `"DEGRADED"` / `"BLOCKED"` |

Readiness derivation:
- `BLOCKED`: extraction failed or no templates found
- `DEGRADED`: extraction succeeded but fallbacks were used (missing optional metadata)
- `READY`: extraction succeeded with no fallbacks

### 3.5 ExternalTheatrePreparationResult

| Field | Type | Default | Description |
|---|---|---|---|
| `theatres` | `list[TheatrePreparationEntry]` | `[]` | Per-theatre results |
| `candidates` | `list[ComparisonCandidateSet]` | `[]` | Cross-theatre comparison candidates |
| `feedback` | `list[BuilderFeedbackReport]` | `[]` | Per-theatre builder feedback |
| `event_keys_used` | `list[str]` | `[]` | Echo of event keys that were threaded |
| `scope_keys_used` | `list[TheatreScopeKey]` | `[]` | Echo of scope keys that were threaded |
| `total_theatres` | `int` | `0` | Total inputs processed |
| `total_successful` | `int` | `0` | Count with bundles |
| `total_failed` | `int` | `0` | Count with errors |

---

## 4. Integration Points

### 4.1 Orchestrator -> parse_construct_json (037d)

```python
from backend.services.theatre_policy_rules import parse_construct_json

meta = parse_construct_json(theatre_input.construct_json)
# Returns: TheatreConstructMeta (frozen dataclass)
# Raises: ValueError on invalid JSON or missing templates
```

The orchestrator catches `ValueError` and populates `TheatrePreparationEntry.error`.

### 4.2 Orchestrator -> extract_enriched_fixture (new)

```python
from backend.services.external_theatre_fixture_extractor import extract_enriched_fixture

extraction_result, fixture_input = extract_enriched_fixture(
    construct_slug=theatre_input.construct_slug,
    construct_version=theatre_input.construct_version,
    meta=meta,
)
# Returns: (ExtractionResult, TheatreFixtureInput or None)
```

`extract_enriched_fixture` always returns a tuple (never raises). On failure, `extraction_result.success=False` and `fixture_input=None`.

### 4.3 Orchestrator -> plan_theatre_checks (037d)

```python
from backend.services.theatre_check_planner import plan_theatre_checks

planned = plan_theatre_checks(spec_slug=theatre_input.construct_slug, meta=meta)
# Returns: list[PlannedCheck]
# PlannedCheck fields: check_id, check_type, domain, source, critical, asset_id, anchor_class
```

Then convert to runner format:

```python
planned_dicts = _planned_checks_to_dicts(planned)
# [{"check_id": "theatre:settlement_accuracy:magnitude_gate", "check_type": "SETTLEMENT_ACCURACY"}, ...]
```

### 4.4 Orchestrator -> execute_theatre_checks (037e)

```python
from backend.services.theatre_check_runner import execute_theatre_checks

execution_result = execute_theatre_checks(
    planned_checks=planned_dicts,
    fixture=fixture_input,
)
# Returns: TheatreExecutionResult (dataclass)
# Properties: total_executed, total_passed, total_failed, total_skipped, has_critical_failures
```

The runner iterates `planned_checks`, matching each `check_type` to its executor. It dispatches by `check_type` string and extracts template/source IDs from `check_id` string format `"theatre:{check_type_lower}:{id}"`.

### 4.5 Orchestrator -> build_comparison_bundle (038a)

```python
from backend.services.theatre_comparison_bundle_builder import build_comparison_bundle

bundle = build_comparison_bundle(
    execution_result=execution_result,
    fixture_input=fixture_input,
    certificate_id=request.certificate_id,
    event_keys=request.event_keys if request.event_keys else None,
    scope_keys=request.scope_keys if request.scope_keys else None,
)
# Returns: ExecutedTheatreComparisonBundle (Pydantic BaseModel)
```

**Critical detail on None vs empty list:** The bundle builder's `event_keys` parameter:
- `None` -> falls back to `sorted(fixture_input.settlement_fixtures.keys())` (construct-specific template IDs)
- `[]` -> uses `sorted([])` = `[]` (explicitly empty)

The orchestrator passes `None` when the caller's lists are empty to get the fallback behavior.

### 4.6 Orchestrator -> generate_candidates (038a)

```python
from backend.services.theatre_comparison_candidates import generate_candidates

successful_bundles = [t.bundle for t in result.theatres if t.bundle is not None]
candidates = generate_candidates(bundles=successful_bundles)
# Returns: list[ComparisonCandidateSet]
```

Only successful bundles are passed. The candidate generator skips same-construct pairs and matches on shared event keys or scope key overlap.

---

## 5. Extraction Strategy -- V1 Enriched vs Existing

### 5.1 How `_build_deterministic_fixture()` Works (037e baseline)

The existing fixture loader in `theatre_fixture_loader.py` generates all-passing fixtures:

| Fixture Type | Existing Behavior | Problem |
|---|---|---|
| Settlement | `predicted_outcome == actual_outcome` for ALL templates | Never produces DISPUTED bundles |
| Oracle | Hardcoded `delta=0.1`, `threshold=0.5` (always consistent) | Never tests oracle divergence |
| Calibration | Fixed `brier_type="binary"` regardless of construct | Multi-class constructs get wrong type |
| Functional | `transform_valid=True` for ALL templates | Never exercises failure path |

### 5.2 How V1 Enriched Extraction Works (038b)

| Fixture Type | Enriched Behavior | Benefit |
|---|---|---|
| Settlement | Even-index templates: pass. Odd-index templates: fail (`predicted != actual`). Multi-bucket gets multi-class outcomes. Single template: pass only. | Produces DISPUTED settlement states in bundles |
| Oracle | First cross-val source: consistent (small delta). Second+ source: divergent (delta > threshold). Threshold defaults to 0.5 when no verification_checks. | Tests both oracle consistency and divergence |
| Calibration | Derive `brier_type` from template metadata. Use `"multi_class"` when any template declares `brier_type="multi_class"`. Compute `expected_brier` from generated values. | Construct-accurate calibration validation |
| Functional | First template: valid. Last template: invalid (if >1 templates). | Exercises FUNCTIONAL_CORRECTNESS failure path |

### 5.3 Concrete Examples

**TREMOR enriched extraction:**

TREMOR has 5 templates (`magnitude_gate`, `aftershock_cascade`, `swarm_watch`, `depth_regime`, `oracle_divergence`), 3 sources (`usgs_neic` primary, `emsc` cross_val, `iris_dmc` cross_val), 5 verification_checks, 3 settlement_tiers. `has_brier_scoring=True` (multiple templates declare `brier_type`).

- Settlement fixtures (5):
  - `magnitude_gate` (index 0, binary): `predicted=YES, actual=YES` -> PASS
  - `aftershock_cascade` (index 1, multi_bucket): `predicted=bucket_0, actual=bucket_2` -> FAIL
  - `swarm_watch` (index 2, binary): `predicted=YES, actual=YES` -> PASS
  - `depth_regime` (index 3, binary): `predicted=YES, actual=NO` -> FAIL
  - `oracle_divergence` (index 4, binary): `predicted=YES, actual=YES` -> PASS
- Oracle fixtures (2):
  - `emsc` (first cross_val): `primary=6.2, cross=6.1, delta=0.1, threshold=0.5` -> consistent (PASS)
  - `iris_dmc` (second cross_val): `primary=6.2, cross=5.3, delta=0.9, threshold=0.5` -> divergent (FAIL)
- Calibration: `brier_type="multi_class"` (aftershock_cascade declares it)
- Functional fixtures (5): `magnitude_gate`=valid, `aftershock_cascade`-`depth_regime`=alternating, `oracle_divergence`=invalid
- Fallbacks: none (TREMOR has all optional metadata)

**CORONA enriched extraction:**

CORONA has 5 templates (`T1`-`T5`), 3 sources (`noaa_swpc` primary, `nasa_donki` cross_val, `gfz_potsdam` cross_val), NO verification_checks, NO settlement_tiers. `has_brier_scoring=True` (from `rlmf.exports` containing `"brier_score"`).

- Settlement fixtures (5):
  - `T1` (index 0, binary): `predicted=YES, actual=YES` -> PASS
  - `T2` (index 1, binary): `predicted=YES, actual=NO` -> FAIL
  - `T3` (index 2, binary): `predicted=YES, actual=YES` -> PASS
  - `T4` (index 3, multi_class): `predicted=bucket_0, actual=bucket_1` -> FAIL
  - `T5` (index 4, binary): `predicted=YES, actual=YES` -> PASS
- Oracle fixtures (2):
  - `nasa_donki` (first cross_val): `delta=0.1, threshold=0.5` -> consistent (PASS)
  - `gfz_potsdam` (second cross_val): `delta=0.9, threshold=0.5` -> divergent (FAIL)
- Calibration: `brier_type="binary"` (no template declares `brier_type` directly; T4 uses `type="multi_class"` but the parser reads `resolution` from that, not `brier_type`)
- Functional fixtures (5): `T1`=valid, `T5`=invalid
- Fallbacks: `["oracle_threshold_defaulted"]` (no verification_checks)

Note: CORONA's `data_sources` have no explicit `id` fields. The parser derives IDs via `s.get("id") or s.get("name", "").lower().replace(" ", "_")`, producing `noaa_swpc`, `nasa_donki`, `gfz_potsdam`. This is already handled by `parse_construct_json()` in 037d.

---

## 6. Error Handling

### 6.1 Error at Each Stage

| Stage | Error Source | Handling | Result State |
|---|---|---|---|
| Parse | `parse_construct_json` raises `ValueError` | Catch, populate `TheatrePreparationEntry.error` | No extraction, no bundle |
| Extract | Internal error in enriched extraction | Return `ExtractionResult(success=False, error=msg)`, `fixture_input=None` | No execution, no bundle |
| Plan | `plan_theatre_checks` (should not fail given valid meta) | Catch generic `Exception`, populate error | No execution, no bundle |
| Execute | `execute_theatre_checks` (does not raise; returns skipped checks) | Always returns `TheatreExecutionResult` | Execution with potentially SKIPPED checks |
| Bundle | `build_comparison_bundle` (should not fail given valid inputs) | Catch generic `Exception`, populate error | No bundle for this theatre |

### 6.2 Aggregate Error Behavior

- The orchestrator processes ALL theatres, even if some fail.
- `candidates` only includes bundles from successful theatres.
- `total_successful` and `total_failed` count theatre outcomes.
- A request with all failures returns `ExternalTheatrePreparationResult` with empty `candidates` and all entries having errors -- NOT an exception.

### 6.3 Edge Cases

| Scenario | Expected Behavior |
|---|---|
| Empty `theatres` list | Return result with `total_theatres=0`, empty everything |
| Single theatre | Produce 1 bundle, 0 candidates (need 2+ for comparison) |
| All theatres fail | Return result with `total_failed=N`, empty `candidates` |
| Missing construct.json content | `parse_construct_json("")` raises ValueError -> captured in entry error |
| Malformed JSON (not valid JSON) | `parse_construct_json` raises ValueError -> captured in entry error |
| Valid JSON but no templates | `parse_construct_json` raises ValueError "must contain at least one theatre_templates entry" |
| No cross-validation sources | Oracle fixtures empty, oracle checks skipped (runner handles this) |
| No Brier scoring | Calibration fixture `None`, calibration check skipped |

---

## 7. Test Strategy

All tests in `backend/tests/test_038b_external_orchestration.py`. Uses `unittest.TestCase` pattern matching existing test files (e.g., `test_037e_theatre_execution.py`). Database mocking follows the same mock-module pattern.

Tests use inline construct JSON strings for TREMOR and CORONA (matching the actual repo files) to ensure tests pass without requiring external repos on disk.

### Sprint 0 -- Schemas + Extraction Contracts (~7 tests)

| # | Test | Validates |
|---|---|---|
| 1 | `test_external_theatre_input_constructs` | `ExternalTheatreInput` accepts required fields |
| 2 | `test_preparation_request_defaults` | `ExternalTheatrePreparationRequest` defaults empty keys |
| 3 | `test_preparation_result_serializes` | `ExternalTheatrePreparationResult` round-trips through `model_dump` |
| 4 | `test_extraction_result_success_shape` | `ExtractionResult` with `success=True` and fixture counts |
| 5 | `test_extraction_result_failure_shape` | `ExtractionResult` with `success=False` and error message |
| 6 | `test_builder_feedback_report_categories` | `BuilderFeedbackReport` distinguishes required/optional/extraction |
| 7 | `test_builder_feedback_readiness_states` | Readiness correctly derives READY/DEGRADED/BLOCKED |

### Sprint 1 -- Fixture Extraction (~9 tests)

| # | Test | Validates |
|---|---|---|
| 8 | `test_tremor_enriched_settlement_pass_and_fail` | TREMOR settlement includes both passing and failing fixtures |
| 9 | `test_tremor_enriched_oracle_consistent_and_divergent` | TREMOR oracle: emsc consistent, iris_dmc divergent |
| 10 | `test_tremor_enriched_calibration_multi_class` | TREMOR calibration uses multi_class brier_type |
| 11 | `test_tremor_enriched_functional_pass_and_fail` | TREMOR functional: first valid, last invalid |
| 12 | `test_corona_enriched_settlement_pass_and_fail` | CORONA settlement includes both passing and failing fixtures |
| 13 | `test_corona_enriched_oracle_with_default_threshold` | CORONA oracle uses default threshold, fallback recorded |
| 14 | `test_corona_enriched_calibration_binary` | CORONA calibration uses binary brier_type |
| 15 | `test_corona_enriched_functional_pass_and_fail` | CORONA functional: first valid, last invalid |
| 16 | `test_extraction_missing_construct_json` | Extraction fails gracefully on invalid/empty JSON |
| 17 | `test_extraction_empty_templates` | Extraction fails when construct has no templates |
| 18 | `test_extraction_malformed_metadata` | Extraction fails on well-formed JSON missing required structure |

### Sprint 2 -- Orchestrator Composition (~8 tests)

| # | Test | Validates |
|---|---|---|
| 19 | `test_orchestrator_single_theatre` | Single TREMOR input -> 1 bundle, 0 candidates |
| 20 | `test_orchestrator_paired_theatres` | TREMOR + CORONA -> 2 bundles, 1+ candidates |
| 21 | `test_orchestrator_shared_identity_threading` | event_keys/scope_keys appear in resulting bundles |
| 22 | `test_orchestrator_no_keys_fallback` | Empty keys -> template-ID fallback in bundles |
| 23 | `test_orchestrator_error_propagation` | One invalid theatre + one valid -> 1 bundle, error on first |
| 24 | `test_orchestrator_all_failures` | Both theatres fail -> empty candidates, total_failed=2 |
| 25 | `test_orchestrator_certificate_id_threading` | certificate_id flows to bundles |
| 26 | `test_orchestrator_empty_request` | Empty theatres list -> result with total_theatres=0 |

### Sprint 3 -- 038 Compatibility + Builder Feedback (~8 tests)

| # | Test | Validates |
|---|---|---|
| 27 | `test_candidates_consumable_by_scanner_input` | Candidate bundles have fields 038 scanner expects |
| 28 | `test_disputed_bundle_from_enriched_fixtures` | Enriched failures -> DISPUTED settlement_state in bundle |
| 29 | `test_settled_vs_disputed_cross_comparison` | TREMOR DISPUTED + CORONA with mixed -> same_event candidate |
| 30 | `test_tremor_feedback_required_present` | TREMOR feedback: templates present, all required met |
| 31 | `test_corona_feedback_optional_missing` | CORONA feedback: verification_checks/settlement_tiers missing |
| 32 | `test_tremor_feedback_extraction_summary` | TREMOR feedback: extraction items list all fixture categories |
| 33 | `test_feedback_blocked_on_missing_templates` | Construct with no templates -> BLOCKED readiness |
| 34 | `test_end_to_end_tremor_corona_preparation` | Full pipeline with both constructs -> candidates with shared identity |

**Total: ~34 tests** (exceeds the PRD minimum of 30).

---

## 8. Files Touched Summary

### New Files

| File | Sprint | Purpose |
|---|---|---|
| `backend/schemas/external_theatre_orchestration.py` | 0 | Pydantic models: input, request, result, extraction, feedback |
| `backend/services/external_theatre_fixture_extractor.py` | 1 | Enriched fixture extraction from construct metadata |
| `backend/services/external_theatre_orchestrator.py` | 2 | Composition service: full preparation pipeline |
| `backend/tests/test_038b_external_orchestration.py` | 0-3 | ~34 tests across 4 sprints |

### Existing Files -- Read Only (Not Modified)

| File | Used By | How |
|---|---|---|
| `backend/services/theatre_policy_rules.py` (037d) | Orchestrator | `parse_construct_json()`, `TheatreConstructMeta` |
| `backend/services/theatre_check_planner.py` (037d) | Orchestrator | `plan_theatre_checks()`, `PlannedCheck` |
| `backend/services/theatre_check_runner.py` (037e) | Orchestrator | `execute_theatre_checks()` |
| `backend/services/theatre_comparison_bundle_builder.py` (038a) | Orchestrator | `build_comparison_bundle()` |
| `backend/services/theatre_comparison_candidates.py` (038a) | Orchestrator | `generate_candidates()` |
| `backend/schemas/theatre_execution.py` (037e) | Extractor, Orchestrator | `TheatreFixtureInput`, `TheatreExecutionResult` |
| `backend/schemas/theatre_comparison_bundle.py` (038a) | Schemas, Orchestrator | `TheatreScopeKey`, `ExecutedTheatreComparisonBundle`, `ComparisonCandidateSet` |
| `backend/services/check_planner.py` | Orchestrator | `PlannedCheck` dataclass |

### Not Touched

- No database models or Alembic migrations
- No API routes
- No frontend files
- `backend/services/theatre_fixture_loader.py` -- NOT called by the orchestrator (enriched extractor replaces this path for 038b)

---

## 9. Risks and Mitigations

### 9.1 PlannedCheck -> dict Conversion Fragility

The 037e runner expects `list[dict]` with `check_type` and `check_id` keys, while the 037d planner returns `list[PlannedCheck]` (dataclass). The conversion bridges this gap but is a coupling point.

**Mitigation:** The `_planned_checks_to_dicts()` function is trivial (3 lines) and tested explicitly. If the runner interface changes in a future cycle, this single function is the only point of change.

### 9.2 Hardcoded Enrichment Rules

The even/odd pass/fail pattern is deterministic but arbitrary. If constructs evolve to have semantic patterns that conflict with this rule, the enrichment could produce misleading fixtures.

**Mitigation:** V1 is explicitly scoped as "good enough to prove orchestration works." V2 (RLMF certificate replay) uses real runtime data and does not rely on synthetic patterns. The enrichment strategy is isolated in `external_theatre_fixture_extractor.py` and can be replaced without touching the orchestrator.

### 9.3 Construct.json Evolution

If external builders change their construct.json layout, `parse_construct_json()` may fail or produce incorrect metadata.

**Mitigation:** The parser already handles both TREMOR-style (`echelon.*` nested) and CORONA-style (root-level) layouts. New layouts would require parser updates in 037d, not in 038b. The orchestrator catches parse errors gracefully.

### 9.4 Large Construct Overhead

A construct with many templates (e.g., 50+) would generate many fixtures and checks, slowing preparation.

**Mitigation:** V1 is not latency-sensitive (service + test harness, no API route). If performance becomes relevant for V2/V3, the enriched extractor can cap fixture generation.
