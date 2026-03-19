# SDD — Cycle-038c: Orchestrated Scanner Handoff

**Cycle:** cycle-038c
**Date:** 19 March 2026
**Builder:** Loa
**Depends on:** Cycle-038, Cycle-038a, Cycle-038b
**Sprints:** 4 (0–3)

---

## 1. Architecture Summary

Cycle 038c adds a **pure-function classification adapter** that bridges 038b orchestrator output into paradox detection results using the same four detection patterns as the real 038 `CrossTheatreParadoxScanner` — without DB, async, or network dependencies.

### Data Flow

```
038b ExternalTheatreOrchestrator
    |
    v
ExternalTheatrePreparationResult
    |  .candidates: list[ComparisonCandidateSet]
    |      each has .bundle_a, .bundle_b: ExecutedTheatreComparisonBundle
    |
    v
038c ExternalTheatreScanAdapter
    |  scan_candidates(ExternalTheatreScanRequest)
    |
    |  For each ComparisonCandidateSet:
    |    +-- _detect_settlement_divergence(bundle_a, bundle_b)
    |    +-- _detect_oracle_inconsistency(bundle_a, bundle_b)
    |    +-- _detect_temporal_drift(bundle_a, bundle_b)
    |    +-- _detect_scope_overlap_gap(bundle_a, bundle_b, candidate)
    |
    v
ExternalTheatreScanResult
    .outcomes: list[CandidateScanOutcome]
        each has .findings: list[ParadoxFinding]  (may be empty = no-paradox)
    .total_scanned / .total_with_findings / .total_clean
```

### Design Principle: Extract, Do Not Call

The adapter **does not call** the real 038 `CrossTheatreParadoxScanner`. It extracts the classification logic into pure functions that operate on `ExecutedTheatreComparisonBundle` pairs. The real scanner requires `AsyncSession`, `FactAnchor`, `FactAnchorLink`, and `OracleResponse` DB models — none of which exist in the orchestration context.

V2 (future cycle) will build the FactAnchor bridge: candidates to anchor creation to link insertion to real async scanner invocation to persisted `CrossTheatreParadox` records.

### Alignment Guarantee

The adapter uses **identical thresholds, severity rules, and classification logic** as the real scanner so that V2 can replace V1 without changing classification behavior:

| Parameter | Value | Source (cross_theatre_paradox_scanner.py) |
|-----------|-------|------------------------------------------|
| Oracle tolerance | 0.1 (10%) | Line 289 |
| Temporal drift window | 24.0 hours | Line 349 |
| Settlement divergence severity | MATERIAL | Line 202 |
| Oracle same-source severity | MATERIAL | Lines 294-296 |
| Oracle cross-source severity | WATCH | Lines 294-297 |
| Temporal drift >2x window | WATCH | Lines 354-356 |
| Temporal drift 1-2x window | INFO | Lines 354-357 |
| Scope overlap gap severity | WATCH | Line 428 |

---

## 2. File-Level Design

### 2.1 `backend/schemas/external_theatre_scan.py` (New)

Pydantic models for scan request, per-candidate outcome, individual paradox findings, and aggregate result.

#### `ParadoxFinding`

Represents a single detected paradox — structurally aligned with the real scanner's `CrossTheatreParadox` DB model output shape.

```python
class ParadoxFinding(BaseModel):
    """Single paradox finding from classification of a bundle pair."""

    paradox_type: str           # "SETTLEMENT_DIVERGENCE" | "ORACLE_INCONSISTENCY" |
                                # "TEMPORAL_DRIFT" | "SCOPE_OVERLAP_GAP"
    severity: str               # "INFO" | "WATCH" | "MATERIAL" | "CRITICAL"
    description: str            # Human-readable summary
    evidence: dict              # Detection-specific evidence dict
    construct_a_slug: str       # Source construct for bundle_a
    construct_b_slug: str       # Source construct for bundle_b
```

Field semantics:
- `paradox_type` uses the same string values as `CrossTheatreParadoxType` enum in `backend/database/models.py` (line 1413-1417) and `ParadoxTypeEnum` in `backend/schemas/cross_theatre_paradox_schemas.py` (lines 13-17).
- `severity` uses the same string values as `CrossTheatreParadoxSeverity` enum in `backend/database/models.py` (lines 1419-1423) and `ParadoxSeverityEnum` in `backend/schemas/cross_theatre_paradox_schemas.py` (lines 20-24).
- `evidence` dict follows the same key structure the real scanner writes to `CrossTheatreParadox.evidence_json` (documented per-pattern in section 3).
- `construct_a_slug` and `construct_b_slug` preserve provenance — the real scanner uses `theatre_a_id`/`theatre_b_id` (persisted DB IDs); the adapter uses construct slugs (the identity available in orchestration context).

#### `CandidateScanOutcome`

Represents the complete scan result for one `ComparisonCandidateSet`.

```python
class CandidateScanOutcome(BaseModel):
    """Scan outcome for a single comparison candidate pair."""

    construct_a_slug: str
    construct_b_slug: str
    candidate_type: str                     # "same_event" | "overlap_scope"
    match_strength: str                     # "EXACT" | "PARTIAL" | "WEAK"
    matching_keys: list[str]                # From ComparisonCandidateSet.matching_keys
    findings: list[ParadoxFinding] = Field(default_factory=list)
    scanned: bool = True                    # Always True for V1
    has_paradox: bool = False               # True if len(findings) > 0
```

Design decision: `findings` is an empty list for no-paradox outcomes. The `has_paradox` field is a derived convenience boolean (set via `model_validator(mode="after")` to `len(self.findings) > 0`). `scanned=True` distinguishes "evaluated and clean" from "not evaluated" (future use for V2 error paths).

#### `ExternalTheatreScanRequest`

```python
class ExternalTheatreScanRequest(BaseModel):
    """Input to the scan adapter — wraps orchestrator output."""

    candidates: list[ComparisonCandidateSet]
    event_keys: list[str] = Field(default_factory=list)
    scope_keys: list[TheatreScopeKey] = Field(default_factory=list)
```

Imports `ComparisonCandidateSet` and `TheatreScopeKey` from `backend.schemas.theatre_comparison_bundle`.

#### `ExternalTheatreScanResult`

```python
class ExternalTheatreScanResult(BaseModel):
    """Complete scan adapter output."""

    outcomes: list[CandidateScanOutcome] = Field(default_factory=list)
    total_scanned: int = 0
    total_with_findings: int = 0
    total_clean: int = 0
```

`total_scanned = len(outcomes)`. `total_with_findings = count where has_paradox`. `total_clean = total_scanned - total_with_findings`.

---

### 2.2 `backend/services/external_theatre_scan_adapter.py` (New)

Pure-function classification adapter. No class instantiation, no DB, no async, no network calls. All functions are module-level.

#### Module Constants

```python
ORACLE_TOLERANCE = 0.1                  # 10% — from real scanner line 289
TEMPORAL_DRIFT_WINDOW = 24.0            # hours — from real scanner line 349
```

#### Public API

```python
def scan_candidates(request: ExternalTheatreScanRequest) -> ExternalTheatreScanResult:
```

Iterates `request.candidates`, calls all four detection functions on each pair, assembles `CandidateScanOutcome` per candidate, returns `ExternalTheatreScanResult`.

Implementation:

```python
def scan_candidates(request: ExternalTheatreScanRequest) -> ExternalTheatreScanResult:
    outcomes = []
    for candidate in request.candidates:
        bundle_a = candidate.bundle_a
        bundle_b = candidate.bundle_b

        findings: list[ParadoxFinding] = []

        # Run all 4 detection patterns
        f = _detect_settlement_divergence(bundle_a, bundle_b)
        if f is not None:
            findings.append(f)

        f = _detect_oracle_inconsistency(bundle_a, bundle_b)
        if f is not None:
            findings.append(f)

        f = _detect_temporal_drift(bundle_a, bundle_b)
        if f is not None:
            findings.append(f)

        f = _detect_scope_overlap_gap(bundle_a, bundle_b, candidate)
        if f is not None:
            findings.append(f)

        outcome = CandidateScanOutcome(
            construct_a_slug=bundle_a.construct_slug,
            construct_b_slug=bundle_b.construct_slug,
            candidate_type=candidate.candidate_type,
            match_strength=candidate.match_strength,
            matching_keys=candidate.matching_keys,
            findings=findings,
        )
        outcomes.append(outcome)

    total_with = sum(1 for o in outcomes if o.has_paradox)
    return ExternalTheatreScanResult(
        outcomes=outcomes,
        total_scanned=len(outcomes),
        total_with_findings=total_with,
        total_clean=len(outcomes) - total_with,
    )
```

---

#### Detection Function 1: `_detect_settlement_divergence`

```python
def _detect_settlement_divergence(
    bundle_a: ExecutedTheatreComparisonBundle,
    bundle_b: ExecutedTheatreComparisonBundle,
) -> Optional[ParadoxFinding]:
```

**What the real scanner does** (lines 172-227):
- Requires both links to have `link_type == "settlement"` (line 193)
- Compares `link_a.linked_entity_type` vs `link_b.linked_entity_type` as outcomes (lines 196-197)
- Returns None if outcomes match (line 200)
- Severity is always MATERIAL (line 202)
- Evidence includes: `theatre_a_outcome`, `theatre_b_outcome`, `anchor_type`, `external_source`, `external_id`, plus link provenance (lines 210-217)

**What the V1 adapter does** (pure-function equivalent):
- Reads `bundle_a.settlement_state` and `bundle_b.settlement_state`
- Returns None if either state is None or "PENDING" (insufficient data to compare)
- If settlement_state values differ (e.g., "SETTLED" vs "DISPUTED"): fire paradox immediately
- If settlement_state values match: compare `settlement_outcomes` dicts on shared event keys, checking if `resolution` values diverge
- Severity: MATERIAL (matching real scanner line 202)

**Input fields from `ExecutedTheatreComparisonBundle`:**
- `settlement_state: Optional[str]` — "SETTLED" | "DISPUTED" | "PENDING" | None
- `settlement_outcomes: dict` — `{template_id: {"predicted_outcome": ..., "actual_outcome": ..., "resolution": ...}}`
- `event_keys: list[str]` — shared event identifiers (for provenance)
- `construct_slug: str` — construct identity

**Classification logic:**

```
1. If either settlement_state is None or "PENDING": return None (insufficient data)
2. If settlement_state values differ (e.g., "SETTLED" vs "DISPUTED"): fire paradox
3. If settlement_state values match: compare settlement_outcomes on shared
   event keys — check if "resolution" values diverge
4. Otherwise: return None (no paradox)
```

**Severity rules:**
- Settlement divergence is always MATERIAL (line 202)

**Evidence dict structure:**

```python
{
    "construct_a_settlement_state": bundle_a.settlement_state,
    "construct_b_settlement_state": bundle_b.settlement_state,
    "construct_a_outcomes": {key: outcome for shared keys in a},
    "construct_b_outcomes": {key: outcome for shared keys in b},
    "divergent_keys": [list of keys where resolution differs],
}
```

---

#### Detection Function 2: `_detect_oracle_inconsistency`

```python
def _detect_oracle_inconsistency(
    bundle_a: ExecutedTheatreComparisonBundle,
    bundle_b: ExecutedTheatreComparisonBundle,
) -> Optional[ParadoxFinding]:
```

**What the real scanner does** (lines 229-323):
1. Gets `OracleResponse` records for both theatres from DB (lines 248-249)
2. Checks provisional revision rule: same source, one provisional one not -> INFO (lines 258-280)
3. Computes max delta between `value_json` dicts using `_compute_oracle_delta()` (line 283)
4. Applies tolerance threshold 0.1 (line 289): delta <= 0.1 -> return None
5. Same source -> MATERIAL; cross-source -> WATCH (lines 294-297)
6. Evidence: `source_a`, `source_b`, `event_id`, `delta`, `tolerance`, `same_source` (lines 305-313)

**What the V1 adapter does:**
- Reads `bundle_a.oracle_values` and `bundle_b.oracle_values`
- Each is `{source_id: {"value": <float or None>, "queried_at": ..., "is_provisional": ...}}`
- Finds shared oracle source IDs across both bundles' `oracle_source_ids`
- For each shared source, computes delta using extracted `_compute_oracle_delta()` logic
- Also checks cross-source: if source IDs differ but both bundles have oracle values, compares values across sources
- Applies provisional revision check: same source, different `is_provisional` flags -> INFO
- Applies tolerance 0.1: delta <= 0.1 -> skip
- Reports the **highest-severity** finding found across all source comparisons

**Input fields from `ExecutedTheatreComparisonBundle`:**
- `oracle_values: dict` — `{source_id: {"value": <number>, "queried_at": ..., "is_provisional": bool}}`
- `oracle_source_ids: list[str]` — all oracle sources in this bundle

**Classification logic:**

```
1. Collect all oracle source IDs from both bundles
2. Find shared source IDs: sources_a intersection sources_b
3. For each shared source:
   a. Extract value_a and value_b from oracle_values
   b. Check provisional revision (same source, different is_provisional) -> INFO finding
   c. Compute delta using _compute_oracle_delta logic
   d. If delta > ORACLE_TOLERANCE (0.1): record finding with MATERIAL severity
4. If no shared sources but both bundles have oracle values:
   a. Cross-source comparison: pick the first available value from each bundle
   b. Compute delta; if > ORACLE_TOLERANCE: record finding with WATCH severity
5. Return the highest-severity finding (MATERIAL > WATCH > INFO), or None
```

**Severity rules (matching real scanner):**
- Same source, provisional revision -> INFO (real scanner lines 258-280)
- Same source, delta > tolerance -> MATERIAL (real scanner lines 294-296)
- Cross-source, delta > tolerance -> WATCH (real scanner lines 294-297)

**Threshold: `ORACLE_TOLERANCE = 0.1`** (real scanner line 289)

**Oracle delta computation** (extracted from real scanner static method, lines 476-490):

The real scanner's `_compute_oracle_delta` iterates all keys from the union of two value_json dicts, computes `abs(float(va) - float(vb))` for each, and returns the max delta. The adapter reuses this exact algorithm for dict-valued oracle entries. For scalar values, it computes `abs(float(a) - float(b))` directly.

**Evidence dict structure:**

```python
{
    "source_a": source_id_a,
    "source_b": source_id_b,
    "delta": round(delta, 4),
    "tolerance": 0.1,
    "same_source": bool,
    "value_a": value_a,
    "value_b": value_b,
    "is_provisional_a": bool,
    "is_provisional_b": bool,
}
```

---

#### Detection Function 3: `_detect_temporal_drift`

```python
def _detect_temporal_drift(
    bundle_a: ExecutedTheatreComparisonBundle,
    bundle_b: ExecutedTheatreComparisonBundle,
) -> Optional[ParadoxFinding]:
```

**What the real scanner does** (lines 325-380):
1. Reads `link_a.created_at` and `link_b.created_at` (line 343-344)
2. Returns None if either is None (line 345-346)
3. Computes `delta_hours = abs((time_a - time_b).total_seconds()) / 3600.0` (line 348)
4. Window = 24.0 hours (line 349)
5. If delta_hours <= window: return None (line 351-352)
6. If delta_hours > 2 * window: WATCH; else INFO (lines 354-357)
7. Evidence: `delta_hours`, `window_hours`, `time_a`, `time_b` (lines 364-370)

**What the V1 adapter does:**
- The orchestration bundles do not carry settlement timestamps directly (no `created_at` field on `ExecutedTheatreComparisonBundle`)
- Reads `oracle_values` entries for `"queried_at"` timestamps — the bundle builder populates these from oracle check evidence (see `theatre_comparison_bundle_builder.py` line 155-156)
- If both bundles have at least one non-None `queried_at` value, computes the max temporal separation between the two bundles' oracle query times
- If no timestamps are available in either bundle, returns None (insufficient data)

**Input fields from `ExecutedTheatreComparisonBundle`:**
- `oracle_values: dict` — entries may contain `"queried_at"` string timestamps (ISO format or None)

**Classification logic:**

```
1. Extract all non-None "queried_at" values from bundle_a.oracle_values
2. Extract all non-None "queried_at" values from bundle_b.oracle_values
3. If either collection is empty: return None (insufficient data)
4. Parse timestamps; compute delta_hours as max separation between the two sets
5. If delta_hours <= TEMPORAL_DRIFT_WINDOW (24.0): return None
6. If delta_hours > 2 * TEMPORAL_DRIFT_WINDOW (48.0): severity = WATCH
7. Else: severity = INFO
8. Return ParadoxFinding
```

**Threshold: `TEMPORAL_DRIFT_WINDOW = 24.0`** hours (real scanner line 349)

**Severity rules (matching real scanner lines 354-357):**
- delta > 2x window (48h) -> WATCH
- delta > window but <= 2x window (24-48h) -> INFO

**Evidence dict structure:**

```python
{
    "delta_hours": round(delta_hours, 2),
    "window_hours": 24.0,
    "time_a": timestamp_a_iso or None,
    "time_b": timestamp_b_iso or None,
}
```

---

#### Detection Function 4: `_detect_scope_overlap_gap`

```python
def _detect_scope_overlap_gap(
    bundle_a: ExecutedTheatreComparisonBundle,
    bundle_b: ExecutedTheatreComparisonBundle,
    candidate: ComparisonCandidateSet,
) -> Optional[ParadoxFinding]:
```

**What the real scanner does** (lines 382-463):
1. Operates on `CoherenceGroup` — checks if all primary members have links to each `FactAnchor` (lines 389-410)
2. Missing links = gap -> WATCH severity (line 428)
3. Evidence: `group_id`, `group_name`, `missing_theatres`, `present_theatres`, `anchor_type`, `present_link_provenance` (lines 445-452)

**What the V1 adapter does:**
- No CoherenceGroup or FactAnchor concepts exist in orchestration context
- Instead, detects scope gaps via `scope_keys` on the bundles
- Only relevant for `overlap_scope` candidates (same_event candidates match on event_keys, not scope)
- Compares `bundle_a.scope_keys` against `bundle_b.scope_keys` using `TheatreScopeKey.key()` for normalized comparison
- If one bundle has scope keys the other lacks, that is a coverage gap

**Input fields from `ExecutedTheatreComparisonBundle`:**
- `scope_keys: list[TheatreScopeKey]` — normalized scope identifiers

**Classification logic:**

```
1. Only fires for overlap_scope candidates (return None for same_event)
2. Normalize scope keys using TheatreScopeKey.key()
3. scopes_a = set of normalized keys from bundle_a
4. scopes_b = set of normalized keys from bundle_b
5. missing_from_a = scopes_b - scopes_a
6. missing_from_b = scopes_a - scopes_b
7. If neither has missing scopes: return None (full coverage)
8. Severity: WATCH (matching real scanner line 428)
9. Return ParadoxFinding with missing scope details
```

**Severity:** Always WATCH (matching real scanner line 428)

**Evidence dict structure:**

```python
{
    "construct_a_scopes": sorted list of scope keys from bundle_a,
    "construct_b_scopes": sorted list of scope keys from bundle_b,
    "missing_from_a": sorted list of scope keys bundle_a lacks,
    "missing_from_b": sorted list of scope keys bundle_b lacks,
    "candidate_match_strength": candidate.match_strength,
}
```

---

## 3. Detection Pattern Extraction — Summary Table

| Pattern | Real Scanner Method | Real Scanner Lines | V1 Adapter Function | Input Fields (from Bundle) | Severity | Evidence Keys |
|---------|--------------------|--------------------|---------------------|---------------------------|----------|---------------|
| SETTLEMENT_DIVERGENCE | `evaluate_settlement_divergence()` | 172-227 | `_detect_settlement_divergence()` | `settlement_state`, `settlement_outcomes`, `event_keys` | MATERIAL | `construct_a/b_settlement_state`, `construct_a/b_outcomes`, `divergent_keys` |
| ORACLE_INCONSISTENCY | `evaluate_oracle_inconsistency()` | 229-323 | `_detect_oracle_inconsistency()` | `oracle_values`, `oracle_source_ids` | MATERIAL (same-src) / WATCH (cross-src) / INFO (provisional) | `source_a/b`, `delta`, `tolerance`, `same_source`, `value_a/b` |
| TEMPORAL_DRIFT | `evaluate_temporal_drift()` | 325-380 | `_detect_temporal_drift()` | `oracle_values["queried_at"]` | WATCH (>48h) / INFO (24-48h) | `delta_hours`, `window_hours`, `time_a/b` |
| SCOPE_OVERLAP_GAP | `evaluate_scope_overlap()` | 382-463 | `_detect_scope_overlap_gap()` | `scope_keys` | WATCH | `construct_a/b_scopes`, `missing_from_a/b` |

---

## 4. Integration Points

### 4.1 Orchestrator to Adapter

The adapter receives output from `prepare_external_theatres()` (038b orchestrator). The caller constructs an `ExternalTheatreScanRequest` from the orchestration result:

```python
from backend.schemas.external_theatre_orchestration import ExternalTheatrePreparationResult
from backend.schemas.external_theatre_scan import ExternalTheatreScanRequest
from backend.services.external_theatre_scan_adapter import scan_candidates

# After orchestration
prep_result: ExternalTheatrePreparationResult = prepare_external_theatres(request)

# Build scan request from orchestration output
scan_request = ExternalTheatreScanRequest(
    candidates=prep_result.candidates,
    event_keys=prep_result.event_keys_used,
    scope_keys=prep_result.scope_keys_used,
)

# Run classification
scan_result = scan_candidates(scan_request)
```

This is a **pure function call** — no shared state, no side effects.

### 4.2 Result Type Alignment With Real Scanner

The adapter's `ParadoxFinding` maps to the real scanner's `CrossTheatreParadox` DB model:

| ParadoxFinding field | CrossTheatreParadox column | Notes |
|---------------------|---------------------------|-------|
| `paradox_type` | `paradox_type` | Same enum string values |
| `severity` | `severity` | Same enum string values |
| `description` | `description` | Same format |
| `evidence` | `evidence_json` | Same key structure per pattern |
| `construct_a_slug` | `theatre_a_id` | V1 uses slug (no DB IDs); V2 maps to theatre IDs |
| `construct_b_slug` | `theatre_b_id` | Same |

V2 bridge (future) will:
1. Create `FactAnchor` records from candidate event keys
2. Create `FactAnchorLink` records from bundles
3. Call real `CrossTheatreParadoxScanner.scan_fact_anchor()`
4. Return persisted `CrossTheatreParadox` records

### 4.3 No Modification of Existing Files

038c does **not** modify:
- `backend/services/cross_theatre_paradox_scanner.py` — real scanner unchanged
- `backend/services/external_theatre_orchestrator.py` — orchestrator unchanged
- `backend/schemas/external_theatre_orchestration.py` — orchestration schemas unchanged
- `backend/schemas/cross_theatre_paradox_schemas.py` — API schemas unchanged
- `backend/database/models.py` — no new DB models

---

## 5. Test Strategy (~32 Tests)

### 5.1 Scan Result Schemas (5 tests)

| Test | What It Verifies |
|------|-----------------|
| `test_paradox_finding_construction` | ParadoxFinding accepts all 4 paradox_type values and all severity levels |
| `test_candidate_scan_outcome_no_findings` | CandidateScanOutcome with empty findings has has_paradox=False, scanned=True |
| `test_candidate_scan_outcome_with_findings` | CandidateScanOutcome with findings has has_paradox=True |
| `test_scan_request_from_candidates` | ExternalTheatreScanRequest accepts ComparisonCandidateSet list |
| `test_scan_result_totals` | ExternalTheatreScanResult computes correct total_scanned / total_with_findings / total_clean |

### 5.2 Settlement Divergence Detection (6 tests)

| Test | What It Verifies |
|------|-----------------|
| `test_settlement_divergence_settled_vs_disputed` | SETTLED vs DISPUTED produces MATERIAL finding |
| `test_settlement_divergence_same_state_no_paradox` | Both SETTLED (same outcomes) produces None |
| `test_settlement_divergence_pending_skipped` | Either PENDING produces None (insufficient data) |
| `test_settlement_divergence_none_state_skipped` | Either None produces None |
| `test_settlement_divergence_outcome_values_differ` | Both SETTLED but different resolution values produces MATERIAL finding |
| `test_settlement_divergence_severity_always_material` | Confirm severity is always MATERIAL |

### 5.3 Oracle Inconsistency Detection (6 tests)

| Test | What It Verifies |
|------|-----------------|
| `test_oracle_delta_above_tolerance` | Delta 0.25 (same source) produces MATERIAL finding |
| `test_oracle_delta_below_tolerance_no_paradox` | Delta 0.05 (same source) produces None |
| `test_oracle_delta_at_tolerance_no_paradox` | Delta exactly 0.1 produces None (tolerance is <=, not <) |
| `test_oracle_cross_source_severity_watch` | Delta 0.3 (different sources) produces WATCH finding |
| `test_oracle_provisional_revision_info` | Same source, one provisional produces INFO finding |
| `test_oracle_no_shared_sources_no_values` | No oracle_values in either bundle produces None |

### 5.4 Temporal Drift Detection (3 tests)

| Test | What It Verifies |
|------|-----------------|
| `test_temporal_drift_within_window_no_paradox` | Delta 12h produces None |
| `test_temporal_drift_beyond_window_info` | Delta 30h produces INFO finding |
| `test_temporal_drift_beyond_double_window_watch` | Delta 50h produces WATCH finding |

### 5.5 Scope Overlap Gap Detection (2 tests)

| Test | What It Verifies |
|------|-----------------|
| `test_scope_overlap_missing_coverage` | Bundle A has scope keys B lacks produces WATCH finding |
| `test_scope_overlap_full_coverage_no_paradox` | Identical scope keys produces None |

### 5.6 No-Paradox Explicit Results (3 tests)

| Test | What It Verifies |
|------|-----------------|
| `test_aligned_bundles_produce_empty_findings` | Two aligned bundles (same settlements, same oracle values) produce CandidateScanOutcome with findings=[], has_paradox=False |
| `test_scan_result_total_clean_accurate` | Result with 3 candidates, 1 with findings has total_clean=2, total_with_findings=1 |
| `test_no_candidates_produces_empty_result` | Empty candidates list produces ExternalTheatreScanResult with total_scanned=0 |

### 5.7 End-to-End Orchestrator to Adapter (4 tests)

| Test | What It Verifies |
|------|-----------------|
| `test_e2e_tremor_scan` | TREMOR bundles through full orchestrator to adapter path; provenance preserved |
| `test_e2e_corona_scan` | CORONA bundles through full orchestrator to adapter path |
| `test_e2e_tremor_corona_cross_theatre` | TREMOR + CORONA candidates scanned; at least one finding detected |
| `test_e2e_provenance_preservation` | Scan results carry construct_a_slug, construct_b_slug, matching_keys, candidate_type through from orchestration |

### 5.8 Regression (3 tests)

| Test | What It Verifies |
|------|-----------------|
| `test_existing_038b_orchestrator_unchanged` | 038b orchestrator produces same output shape (no import/API breaks) |
| `test_existing_038a_bundle_builder_unchanged` | 038a bundle builder produces valid bundles (no shape regression) |
| `test_existing_038a_candidate_generator_unchanged` | 038a candidate generator works (no import/shape regression) |

**Total: ~32 tests**

---

## 6. Files Touched Summary

### New Files (2)

| File | Purpose |
|------|---------|
| `backend/schemas/external_theatre_scan.py` | Pydantic models: ExternalTheatreScanRequest, ExternalTheatreScanResult, CandidateScanOutcome, ParadoxFinding |
| `backend/services/external_theatre_scan_adapter.py` | Pure-function classification adapter: scan_candidates() + 4 detection functions |

### New Test Files (1)

| File | Purpose |
|------|---------|
| `tests/test_external_theatre_scan_adapter.py` | All ~32 tests for schemas, detection functions, end-to-end, regression |

### Existing Files Read (Not Modified)

| File | Read For |
|------|----------|
| `backend/services/cross_theatre_paradox_scanner.py` | Classification logic extraction (thresholds, severity rules, evidence shapes) |
| `backend/services/external_theatre_orchestrator.py` | Input surface (ExternalTheatrePreparationResult shape) |
| `backend/schemas/external_theatre_orchestration.py` | Pydantic model patterns, ComparisonCandidateSet import path |
| `backend/services/theatre_comparison_bundle_builder.py` | Bundle field semantics (settlement_state, oracle_values, scope_keys) |
| `backend/services/theatre_comparison_candidates.py` | Candidate generation logic (same_event vs overlap_scope) |
| `backend/schemas/theatre_comparison_bundle.py` | ExecutedTheatreComparisonBundle, ComparisonCandidateSet, TheatreScopeKey schemas |
| `backend/schemas/cross_theatre_paradox_schemas.py` | ParadoxTypeEnum, ParadoxSeverityEnum string value alignment |
| `backend/database/models.py` | CrossTheatreParadox model shape, enum definitions |

---

## 7. Risks and Mitigations

### 7.1 Logic Drift Between Adapter and Real Scanner

If the real scanner's thresholds or severity rules change in a future cycle, the adapter's extracted logic becomes stale.

**Mitigation:** Constants (`ORACLE_TOLERANCE`, `TEMPORAL_DRIFT_WINDOW`) are module-level in the adapter and documented with source line references. V2 replaces the adapter entirely, making drift a short-lived risk.

### 7.2 Temporal Drift Depends on Optional Timestamps

Bundle `oracle_values` may not carry `queried_at` values (the bundle builder currently sets them to `None` — see `theatre_comparison_bundle_builder.py` line 156). If no timestamps are available, temporal drift detection silently returns None.

**Mitigation:** This is expected behavior. Temporal drift is the lowest-priority detection pattern. The test suite includes a "no timestamps available" case that verifies None return. V2 will have real `FactAnchorLink.created_at` timestamps.

### 7.3 Scope Overlap Gap May Be Thin in V1

The real scanner's scope overlap operates on CoherenceGroup membership and FactAnchor links. The V1 adapter's scope_keys comparison is a simpler proxy. Scope keys may be empty in current test fixtures (the bundle builder's `_extract_scope_keys` returns `[]` by default).

**Mitigation:** The adapter only fires scope overlap for `overlap_scope` candidates (which require scope_keys to be present by definition — candidates cannot be generated without them). Tests supply explicit scope_keys to exercise the path.

### 7.4 No-Paradox Path Must Be Explicit

If a detection function has a bug that always returns None, every outcome appears clean — indistinguishable from "working correctly with aligned data."

**Mitigation:** The test suite includes mandatory positive-paradox tests for settlement divergence and oracle inconsistency. If those tests pass, the detection functions are exercising real classification logic, not silently returning None.

---

## 8. Sprint Alignment

| Sprint | Focus | New Files | Tests |
|--------|-------|-----------|-------|
| 0 | Scan result schemas + adapter contracts | `backend/schemas/external_theatre_scan.py` (complete) | ~6 |
| 1 | Detection functions + scan_candidates() | `backend/services/external_theatre_scan_adapter.py` (complete) | ~8 |
| 2 | Positive + negative end-to-end paths | Tests only | ~10 |
| 3 | Provenance + regression | Tests only | ~8 |
| **Total** | | **2 new source + 1 test file** | **~32** |
