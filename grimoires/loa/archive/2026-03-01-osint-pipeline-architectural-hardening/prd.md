# PRD: OSINT Pipeline Architectural Hardening (Cycle-004)

**Cycle:** 004
**Type:** Architectural hardening (6 deferred concerns)
**Date:** 2026-03-01
**Predecessor:** Cycle-002 (OSINT Pipeline skeleton — 6 collectors, 3-stage engine, 263 tests), Cycle-003 (Registry v0.6.0 merge + enforcement hardening)
**Location:** `~/Downloads/osint_pipeline/`

---

## 1. Problem Statement

The OSINT Composed Oracle pipeline (Collection → Corroboration → Scoring) shipped in Cycle-002 with 6 deferred architectural concerns to keep the skeleton shippable. Cycle-003 merged the v0.6.0 registry (66 sources) and hardened enforcement compatibility. The pipeline works end-to-end but has structural gaps that must be resolved before Cycle-005 (160+ source expansion) or the first live OSINT-settled certificate.

The 6 concerns are:
1. Gap semantics conflation (signal absence vs intelligence gap)
2. Sybil corroboration vulnerability (upstream independence accounting)
3. Receipt mode enforcement location (collector vs runner)
4. Misplaced confidence logic (BaseCollector vs Scorer)
5. Non-deterministic hashing edge cases (Unicode NFC, float precision)
6. Silent source drops on timeout (unstructured gap reports)

> Sources: echelon_cycle_004_context.md, Composed Oracle Spec v2, System Bible v13, Strategic Architecture of OSINT Data Signals paper

---

## 2. Goals & Success Criteria

| # | Goal | Measurement |
|---|------|-------------|
| SC-1 | GapKind semantics correct throughout pipeline | AC-1 acceptance tests pass |
| SC-2 | Independence dedup has correct naming + null handling | AC-2 acceptance tests pass |
| SC-3 | Receipt mode enforcement non-bypassable at runner level | AC-3 acceptance tests pass |
| SC-4 | Confidence capping moved from BaseCollector to Scorer | AC-4 acceptance tests pass, new Scorer module exists |
| SC-5 | Canonical hashing deterministic with NFC + float precision | AC-5 acceptance tests pass |
| SC-6 | No silent source drops; structured failure_mode on gaps | AC-6 acceptance tests pass |
| SC-7 | All existing tests still pass | Zero regression |
| SC-8 | 25-30 new architectural concern tests added | Test count verified |

---

## 3. Scope

### In Scope

- 6 architectural concern patches to `~/Downloads/osint_pipeline/`
- New Scorer module (`engine/scorer.py`)
- FailureMode enum and retriable flag on GapReport
- Unicode NFC normalisation in canonical JSON
- RFC 8785 float precision handling
- gap_count / gap_sources on OracleCollectionSummary
- Runner-level receipt mode enforcement
- GapKind mapping in BaseCollector.to_gap_report()
- 25-30 new tests in test_architectural_concerns.py

### Out of Scope

- Registry expansion (Cycle-005)
- New collectors
- CLI changes
- Live certificate settlement
- Frontend/deployment changes

---

## 4. Requirements

### AC-1: GapKind Semantics — Signal Absence vs Intelligence Gap

**Current state:** GapKind enum exists (evidence.py:67-77) with SIGNAL_ABSENCE and INTELLIGENCE_GAP. CounterSignalChecker (counter_signal.py:139-167) correctly distinguishes them. However, `BaseCollector.to_gap_report()` (base.py:328-342) always defaults to `GapKind.INTELLIGENCE_GAP` regardless of CollectionStatus.

**Required changes:**

1. `BaseCollector.to_gap_report()`: Map `CollectionStatus.NOT_FOUND` → `GapKind.SIGNAL_ABSENCE`; all other failure statuses → `GapKind.INTELLIGENCE_GAP`
2. `allow_gap` enforcement in settlement path: When `allow_gap=false` and `GapKind.INTELLIGENCE_GAP` occurs, criterion fails. When `allow_gap=true`, passes with degraded confidence.

**Acceptance criteria:**
- `to_gap_report()` maps NOT_FOUND to SIGNAL_ABSENCE
- Intelligence gap with allow_gap=false fails criterion
- Intelligence gap with allow_gap=true passes with degraded confidence
- GapKind enum has exactly two values

---

### AC-2: Upstream Independence Deduplication

**Current state:** Fully implemented. `OracleCollectionSummary.distinct_upstream_count` (evidence.py:271-277) and `upstream_dedup_map` (evidence.py:280-287) work correctly. CorroborationEngine (corroboration.py:69-87) deduplicates by `independence_upstream_id`.

**Required changes:**

1. Add `distinct_upstream_succeeded_count` as property alias (context file naming convention)
2. Verify null/missing upstream_id handling (each counts independently)

**Acceptance criteria:**
- Two sources with same upstream_id count as 1 corroborator
- Two sources with different upstream_ids count as 2
- Source with null upstream_id counts independently
- `distinct_upstream_succeeded_count` available on OracleCollectionSummary

---

### AC-3: Receipt Mode Enforcement

**Current state:** Implemented in BaseCollector.validate_receipt_mode() (base.py:138-157). RECEIPT_MODE_ORDER and meets_receipt_minimum() (evidence.py:52-64) handle ordering. Enforcement is in collector's collect() method.

**Required changes:**

1. **Runner-level enforcement**: Add receipt mode pre-check in `CollectionRunner.run()` before calling `collector.collect()`. The runner must accept a `registry_sources` mapping and validate receipt mode before dispatching. This makes enforcement non-bypassable even if a collector overrides collect().
2. Collector's own check remains as defence-in-depth.

**Acceptance criteria:**
- http_transcript receipt accepted for source requiring http_transcript
- none receipt rejected for source requiring http_transcript
- signed_receipt accepted for source requiring http_transcript (exceeds minimum)
- Receipt mode ordering correct (5 levels)
- Enforcement happens in runner (not only in collector)

---

### AC-4: Confidence Capping — Move to Scorer

**Current state:** Confidence capping is in BaseCollector (base.py:271-274) with `FREE_SOURCE_CONFIDENCE_CAP=0.7` and `should_cap_confidence()`. No standalone Scorer module exists.

**Required changes:**

1. **Create `engine/scorer.py`**: New `EvidenceScorer` class that applies confidence penalties post-collection
2. **Penalty matrix** (applied multiplicatively):
   - `revision_policy=immutable` → 1.0 (no penalty)
   - `revision_policy=as_of_timestamp` → 0.95
   - `revision_policy=latest_only` → 0.80
   - `rate_limit_policy` indicating instability → 0.90
   - Receipt at minimum (not exceeding) → 0.95
3. **Single source cap**: 0.95 maximum for any individual source
4. **Composite confidence**: Corroborated sources can exceed 0.95
5. **BaseCollector cleanup**: Remove confidence capping. `extract()` returns raw confidence, scorer adjusts.

**Acceptance criteria:**
- Immutable source gets no penalty
- latest_only source gets 0.80x penalty
- Single source capped at 0.95
- Corroborated sources can exceed 0.95 composite
- BaseCollector no longer applies confidence adjustments

---

### AC-5: Canonical Hash Determinism

**Current state:** `canonical_json()` (canonical.py:31-41) uses sorted keys and no whitespace. CANONICAL_HEADER_ALLOWLIST (canonical.py:24-28) filters volatile headers. URL query param sorting implemented (canonical.py:91-107).

**Required changes:**

1. **Unicode NFC normalisation**: Apply `unicodedata.normalize("NFC", ...)` to all string values before canonical serialisation
2. **RFC 8785 float precision**: Implement shortest-representation floats that round-trip correctly
3. **RFC 8785 test vector**: Add known test vector from the RFC to validate conformance

**Acceptance criteria:**
- Identical inputs produce identical hashes across multiple runs
- Dict ordering does not affect hash
- Float precision edge case (0.1 + 0.2) produces deterministic output
- Unicode NFC normalisation applied (combining vs precomposed characters)
- Canonical JSON matches RFC 8785 spec for a known test vector

---

### AC-6: Timeout Gap Reports

**Current state:** CollectionRunner (collection_runner.py:121-148) handles timeout and produces GapReport with TIMEOUT reason and INTELLIGENCE_GAP kind. But gap reports lack structured failure classification.

**Required changes:**

1. **FailureMode enum** (models/evidence.py): `connection_refused`, `dns_failure`, `tls_error`, `read_timeout`, `response_too_large`, `http_error_4xx`, `http_error_5xx`
2. **retriable flag** on GapReport: `true` for 5xx/timeout/read_timeout, `false` for 4xx/DNS
3. **failure_mode field** on GapReport (optional, alongside existing `reason`)
4. **gap_count and gap_sources[]** computed properties on OracleCollectionSummary
5. **BaseCollector.to_gap_report()**: Map CollectionStatus to appropriate FailureMode
6. **No silent drops**: Every configured source must appear in output as EvidenceBundle OR GapReport

**Acceptance criteria:**
- HTTP 5xx produces GapReport with failure_mode=http_error_5xx, retriable=true
- DNS failure produces GapReport with failure_mode=dns_failure, retriable=false
- Read timeout produces GapReport with configured vs actual timeout
- Every configured source appears in output (no silent drops)
- OracleCollectionSummary includes gap_count

---

## 5. Technical Constraints

- **Location**: `~/Downloads/osint_pipeline/`
- **Python**: 3.11+
- **Dependencies**: Pydantic v2, httpx (no new external deps)
- **British spelling throughout**
- **All tests runnable via `python tests/test_*.py`**
- **Existing tests must not regress**

---

## 6. Files Modified

| File | Concerns | Changes |
|------|----------|---------|
| `models/evidence.py` | AC-1, AC-2, AC-6 | FailureMode enum, retriable/failure_mode on GapReport, distinct_upstream_succeeded_count alias, gap_count/gap_sources on summary |
| `models/__init__.py` | AC-4, AC-6 | Export FailureMode, Scorer |
| `engine/scorer.py` | AC-4 | **NEW** — EvidenceScorer class with penalty matrix |
| `engine/canonical.py` | AC-5 | Unicode NFC normalisation, RFC 8785 float handling |
| `engine/collection_runner.py` | AC-3, AC-6 | Runner-level receipt mode enforcement, failure_mode mapping |
| `collectors/base.py` | AC-1, AC-4 | Fix to_gap_report() gap_kind mapping, remove confidence capping |
| `tests/test_architectural_concerns.py` | All | Expand from 9 to 25-30 tests |

---

## 7. Build Order

Single sprint, 7 tasks. Dependency chain:

```
AC-1 → AC-5 → AC-3 → AC-2 → AC-4 → AC-6 → AC-INT
```

**Rationale:**
- AC-1 before AC-6: timeout gap reports use `GapKind.INTELLIGENCE_GAP` which AC-1 defines
- AC-1 before AC-2: corroboration stage needs to distinguish real evidence bundles from gaps
- AC-3 before AC-4: scorer needs to know whether receipt met or exceeded minimum to apply 0.95x penalty
- AC-5 early: everything downstream hashes evidence, so canonical determinism must ship first
- AC-INT last: end-to-end integration test validates all 6 concerns interact correctly

---

## 8. Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Moving confidence capping breaks existing collector tests | Medium | BaseCollector still passes raw confidence; scorer is additive layer |
| RFC 8785 float handling is complex | Low | Use Python's shortest round-trip repr; add known test vectors |
| Runner-level receipt enforcement adds overhead | Low | Single dict lookup before collection, negligible |
| New Scorer module adds pipeline stage | Medium | Scorer is opt-in; existing pipeline works without it |
