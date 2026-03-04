# SDD: OSINT Pipeline Architectural Hardening (Cycle-004)

**Cycle:** 004
**Date:** 2026-03-01
**PRD:** `grimoires/loa/prd.md`

---

## 1. Overview

Hardening cycle — no new pipeline stages. All changes are patches to existing models, engine modules, and the collector base class, plus one new module (`engine/scorer.py`). The pipeline architecture (Collection → Corroboration → Scoring) is unchanged.

**Target:** `~/Downloads/osint_pipeline/`

---

## 2. Changes

### 2.1 AC-1: GapKind Mapping in BaseCollector

**File:** `collectors/base.py`

**Change:** Update `to_gap_report()` (currently lines 328-342) to map `CollectionStatus` to `GapKind`:

```python
GAP_KIND_MAP: dict[CollectionStatus, GapKind] = {
    CollectionStatus.NOT_FOUND: GapKind.SIGNAL_ABSENCE,
    # All others default to INTELLIGENCE_GAP
}

def to_gap_report(self, result: CollectionResult, allow_gap: bool = False) -> GapReport:
    gap_kind = GAP_KIND_MAP.get(result.status, GapKind.INTELLIGENCE_GAP)
    return GapReport(
        source_id=self.source_id,
        source_group=self.source_group,
        jurisdiction=self.jurisdiction,
        reason=result.status,
        error_detail=result.error_message,
        allow_gap=allow_gap,
        gap_kind=gap_kind,
        freshness=FreshnessState.NO_DATA if gap_kind == GapKind.SIGNAL_ABSENCE else FreshnessState.ERROR,
    )
```

**Rationale:** NOT_FOUND (HTTP 404) means the source responded successfully but had no matching data — this is signal absence (evidence). All other failures (TIMEOUT, NETWORK_ERROR, AUTH_FAILURE, etc.) are intelligence gaps (uncertainty).

---

### 2.2 AC-2: Upstream Naming Alignment

**File:** `models/evidence.py`

**Change:** Add `distinct_upstream_succeeded_count` as an alias property on `OracleCollectionSummary`:

```python
@property
def distinct_upstream_succeeded_count(self) -> int:
    """Alias for distinct_upstream_count (Cycle-004 naming convention)."""
    return self.distinct_upstream_count
```

No functional change. The existing `distinct_upstream_count` already handles null upstream IDs correctly (each unique string, including empty strings, counts as distinct).

---

### 2.3 AC-3: Runner-Level Receipt Mode Enforcement

**File:** `engine/collection_runner.py`

**Change:** Add `registry_sources` parameter to `CollectionRunner.__init__()` and pre-validate receipt mode in `run()` before dispatching to collectors:

```python
def __init__(
    self,
    collectors: list[BaseCollector],
    registry_sources: dict[str, RegistrySource] | None = None,
    max_workers: int = 5,
    timeout_budget_seconds: float = 60.0,
):
    self.collectors = {c.source_id: c for c in collectors}
    self.registry_sources = registry_sources or {}
    ...
```

In `run()`, before submitting to the thread pool:

```python
# Runner-level receipt mode enforcement (non-bypassable)
for source_id, collector in active.items():
    reg = self.registry_sources.get(source_id)
    if reg is not None:
        minimum = ReceiptMode(reg.receipt_mode_minimum)
        if not meets_receipt_minimum(collector.RECEIPT_MODE, minimum):
            # Reject before collection — runner enforces, not collector
            summary.gaps.append(GapReport(
                source_id=source_id,
                source_group=collector.source_group,
                jurisdiction=collector.jurisdiction,
                reason=CollectionStatus.SOURCE_ERROR,
                error_detail=f"Receipt mode {collector.RECEIPT_MODE.value} < minimum {minimum.value}",
                gap_kind=GapKind.INTELLIGENCE_GAP,
            ))
            summary.total_sources_failed += 1
            continue  # Skip this collector
```

Collectors that fail receipt mode check are excluded from the thread pool entirely. The collector's own `validate_receipt_mode()` remains as defence-in-depth.

---

### 2.4 AC-4: EvidenceScorer Module

**File:** `engine/scorer.py` (**NEW**)

New module with `EvidenceScorer` class. Applied post-collection to adjust confidence scores based on source metadata.

```python
class EvidenceScorer:
    """Apply confidence penalties based on source metadata.

    Penalty matrix (multiplicative):
    - revision_policy: immutable=1.0, as_of_timestamp=0.95, latest_only=0.80
    - rate_limit instability: 0.90
    - receipt at minimum (not exceeding): 0.95
    - Single source cap: 0.95
    """

    REVISION_PENALTY = {
        "immutable": 1.0,
        "as_of_timestamp": 0.95,
        "latest_only": 0.80,
    }
    RATE_LIMIT_INSTABILITY_PENALTY = 0.90
    RECEIPT_AT_MINIMUM_PENALTY = 0.95
    SINGLE_SOURCE_CAP = 0.95

    def score_bundle(
        self,
        bundle: EvidenceBundle,
        registry_source: RegistrySource | None = None,
    ) -> float:
        """Apply penalties to a single bundle's confidence score.

        Returns adjusted confidence in [0.0, SINGLE_SOURCE_CAP].
        """
        confidence = bundle.confidence_score

        if registry_source:
            # Revision policy penalty
            rev_penalty = self.REVISION_PENALTY.get(
                registry_source.revision_policy, 1.0
            )
            confidence *= rev_penalty

            # Rate limit instability penalty
            if self._is_rate_limited_unstable(registry_source):
                confidence *= self.RATE_LIMIT_INSTABILITY_PENALTY

            # Receipt at minimum (not exceeding) penalty
            if not self._receipt_exceeds_minimum(bundle, registry_source):
                confidence *= self.RECEIPT_AT_MINIMUM_PENALTY

        # Single source cap
        confidence = min(confidence, self.SINGLE_SOURCE_CAP)
        return round(confidence, 6)

    def composite_confidence(
        self,
        scored_bundles: list[tuple[EvidenceBundle, float]],
    ) -> float:
        """Compute composite confidence from multiple scored bundles.

        Composite CAN exceed SINGLE_SOURCE_CAP when corroborated.
        Formula: 1 - product(1 - score_i) for i in scored_bundles.
        """
        if not scored_bundles:
            return 0.0
        product = 1.0
        for _, score in scored_bundles:
            product *= (1.0 - score)
        return round(1.0 - product, 6)
```

**BaseCollector cleanup** (`collectors/base.py`): Remove lines 271-274 (confidence capping in `collect()`), remove `FREE_SOURCE_CONFIDENCE_CAP` and `should_cap_confidence()`. The `extract()` method returns raw confidence; the scorer adjusts.

---

### 2.5 AC-5: Canonical Hash — NFC + Float Precision

**File:** `engine/canonical.py`

**Changes:**

1. Add `import unicodedata` at top
2. Create `_nfc_normalize_strings(obj)` recursive helper that applies `unicodedata.normalize("NFC", s)` to all string values in a nested dict/list structure
3. Create `_rfc8785_float(f: float) -> str` helper that produces the shortest representation that round-trips (matching JCS Number serialisation rules)
4. Update `canonical_json()` to call NFC normalisation before serialisation and use a custom encoder for floats:

```python
def canonical_json(obj: Any) -> str:
    """RFC 8785 canonical JSON with Unicode NFC normalisation."""
    normalised = _nfc_normalize_strings(obj)
    return json.dumps(
        normalised,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        default=_json_default,
    )
```

The `_json_default` handler processes any non-standard types. Float handling uses `repr()` to ensure shortest round-trip representation.

---

### 2.6 AC-6: FailureMode Enum + Structured Gap Reports

**File:** `models/evidence.py`

**New enum** after GapKind:

```python
class FailureMode(str, Enum):
    """Structured failure classification for gap reports."""
    CONNECTION_REFUSED = "connection_refused"
    DNS_FAILURE = "dns_failure"
    TLS_ERROR = "tls_error"
    READ_TIMEOUT = "read_timeout"
    RESPONSE_TOO_LARGE = "response_too_large"
    HTTP_ERROR_4XX = "http_error_4xx"
    HTTP_ERROR_5XX = "http_error_5xx"

RETRIABLE_FAILURES: frozenset[FailureMode] = frozenset({
    FailureMode.READ_TIMEOUT,
    FailureMode.HTTP_ERROR_5XX,
})
```

**GapReport additions:**

```python
class GapReport(BaseModel):
    ...
    failure_mode: FailureMode | None = Field(
        default=None,
        description="Structured failure classification",
    )
    retriable: bool = Field(
        default=False,
        description="Whether this failure is likely transient",
    )
```

**OracleCollectionSummary additions:**

```python
@property
def gap_count(self) -> int:
    return len(self.gaps)

@property
def gap_sources(self) -> list[str]:
    return [g.source_id for g in self.gaps]
```

**BaseCollector.to_gap_report() update:** Map CollectionStatus to FailureMode:

```python
STATUS_TO_FAILURE_MODE = {
    CollectionStatus.TIMEOUT: FailureMode.READ_TIMEOUT,
    CollectionStatus.NETWORK_ERROR: FailureMode.CONNECTION_REFUSED,
    CollectionStatus.SOURCE_ERROR: FailureMode.HTTP_ERROR_5XX,
    CollectionStatus.AUTH_FAILURE: FailureMode.HTTP_ERROR_4XX,
    CollectionStatus.RATE_LIMITED: FailureMode.HTTP_ERROR_4XX,
}
```

Set `retriable = failure_mode in RETRIABLE_FAILURES`.

---

## 3. Test Plan

Expand `tests/test_architectural_concerns.py` from 9 to 25-30 tests:

| Test | Concern | Validates |
|------|---------|-----------|
| `test_gap_kind_enum_has_two_values` | AC-1 | GapKind enum completeness |
| `test_to_gap_report_maps_not_found_to_signal_absence` | AC-1 | GapKind mapping |
| `test_to_gap_report_maps_timeout_to_intelligence_gap` | AC-1 | GapKind mapping |
| `test_allow_gap_false_intelligence_gap_fails` | AC-1 | allow_gap enforcement |
| `test_allow_gap_true_intelligence_gap_passes_degraded` | AC-1 | allow_gap enforcement |
| `test_distinct_upstream_count_deduplicates` | AC-2 | (existing) |
| `test_distinct_upstream_succeeded_count_alias` | AC-2 | naming alias |
| `test_null_upstream_id_counts_independently` | AC-2 | null handling |
| `test_meets_receipt_minimum_ordering` | AC-3 | (existing) |
| `test_receipt_mode_none_rejected` | AC-3 | (existing) |
| `test_runner_rejects_insufficient_receipt_mode` | AC-3 | runner-level enforcement |
| `test_runner_passes_sufficient_receipt_mode` | AC-3 | runner-level enforcement |
| `test_scorer_immutable_no_penalty` | AC-4 | penalty matrix |
| `test_scorer_latest_only_080_penalty` | AC-4 | penalty matrix |
| `test_scorer_single_source_capped_095` | AC-4 | single source cap |
| `test_scorer_composite_exceeds_095` | AC-4 | composite confidence |
| `test_base_collector_no_confidence_cap` | AC-4 | cleanup verification |
| `test_confidence_capped_for_latest_only` | AC-4 | (existing, updated) |
| `test_canonical_json_nfc_normalisation` | AC-5 | Unicode NFC |
| `test_canonical_json_float_precision` | AC-5 | 0.1+0.2 edge case |
| `test_canonical_json_rfc8785_test_vector` | AC-5 | RFC conformance |
| `test_different_auth_headers_same_hash` | AC-5 | (existing) |
| `test_url_query_params_order_irrelevant` | AC-5 | (existing) |
| `test_failure_mode_enum_values` | AC-6 | enum completeness |
| `test_gap_report_failure_mode_and_retriable` | AC-6 | structured fields |
| `test_5xx_produces_retriable_gap` | AC-6 | retriable=true |
| `test_dns_failure_not_retriable` | AC-6 | retriable=false |
| `test_gap_count_and_gap_sources` | AC-6 | summary computed properties |
| `test_no_silent_source_drops` | AC-6 | completeness invariant |
| `test_timeout_produces_gap_reports` | AC-6 | (existing) |

---

## 4. Dependency Order

```
AC-1 → AC-5 → AC-3 → AC-2 → AC-4 → AC-6 → AC-INT
```

**Rationale:**
- AC-1 before AC-6: timeout gap reports use `GapKind.INTELLIGENCE_GAP` which AC-1 defines
- AC-1 before AC-2: corroboration stage needs to distinguish real evidence bundles from gaps
- AC-3 before AC-4: scorer needs to know whether receipt met or exceeded minimum to apply 0.95x penalty
- AC-5 early: all downstream hashing depends on canonical determinism
- AC-INT last: end-to-end integration test validates all 6 concerns interact correctly

## 5. AC-INT: End-to-End Pipeline Integration Test

**File:** `tests/test_architectural_concerns.py`

Single test function that configures a Theatre with 4 sources:
- Source A and Source B sharing `independence_upstream_id="shared_reuters"`
- Source C that times out (simulated)
- Source D that returns signal absence (HTTP 404)

Runs the full 3-stage pipeline (Collection → Corroboration → Scoring) and asserts:
1. Upstream dedup collapses A+B to 1 logical corroborator
2. Source C timeout produces GapReport with `failure_mode` and `retriable`
3. Source D signal absence produces GapReport with `gap_kind=SIGNAL_ABSENCE`
4. Receipt mode enforcement applied by runner
5. Confidence capping applied by Scorer (not BaseCollector)
6. Evidence bundle hashes are deterministic (re-run identical)
7. No silent drops: 4 sources → 2 EvidenceBundles + 2 GapReports
8. `gap_count == 2`, `gap_sources` contains source_c and source_d
