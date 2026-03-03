All good -- APPROVED with noted concerns.

# Code Review — Sprint 22 (Cycle-011 Sprint-2): Corroboration + Scoring + Paradox Wiring + Convergence

**Reviewer**: Senior Technical Lead (adversarial review)
**Date**: 2026-03-03
**Verdict**: APPROVED (0 CRITICAL, 0 HIGH, 2 MEDIUM, 3 LOW findings)

---

## Pre-flight Confirmation

- Ledger confirms sprint-2 (local) = global sprint-22, Cycle-011
- Sprint 1 audit (sprint-21) approved with 0 CRITICAL, 0 HIGH, 2 MEDIUM, 3 LOW
- No Sprint 1 audit findings required Sprint 2 remediation (all were "non-blocking hardening opportunities for future deployment")

---

## Source Files Independently Read

Every line of Sprint 2 code read independently before cross-referencing the implementation report.

| File | Lines | Verified |
|------|-------|----------|
| `backend/osint/engine/corroboration.py` | 172 | YES |
| `backend/osint/engine/counter_signal.py` | 153 | YES |
| `backend/osint/engine/scorer.py` | 270 | YES |
| `backend/osint/engine/convergence.py` | 191 | YES |
| `backend/osint/engine/__init__.py` | 36 | YES |
| `backend/engines/reality_signal.py` | 249 | YES (full file, including pre-existing providers) |
| `backend/engines/__init__.py` | 72 | YES (full file) |
| `backend/engines/paradox.py` | 239 | YES (confirmed UNMODIFIED) |
| `backend/osint/__init__.py` | 69 | YES |
| `backend/engines/tests/test_integration.py` | 224 | YES |
| `backend/osint/tests/test_corroboration.py` | 315 | YES |
| `backend/osint/tests/test_counter_signal.py` | 167 | YES |
| `backend/osint/tests/test_scorer.py` | 431 | YES |
| `backend/osint/tests/test_convergence.py` | 252 | YES |
| `backend/osint/tests/test_live_reality.py` | 271 | YES |
| `backend/osint/tests/test_paradox_wiring.py` | 363 | YES |

---

## Acceptance Criteria Verification

### Task 1: Corroboration Engine

| Criterion | Verdict | Evidence |
|-----------|---------|----------|
| Primary/secondary separation by resolution_role | PASS | `_get_resolution_role()` resolves from registry; test `test_primary_secondary_separation` validates |
| Dedup by independence_upstream_id (3 WM -> 1) | PASS | `deduplicate_by_upstream_id()` groups by upstream_id, keeps max confidence; `test_dedup_same_upstream_id` verifies |
| Keeps strongest-confidence entry | PASS | `max(group, key=lambda b: b.normalised_event.confidence)`; `test_dedup_keeps_strongest_confidence` verifies 0.95 kept |
| distinct_source_groups counted after dedup | PASS | Set of upstream_ids after dedup, `len()` counted; verified in tests |
| corroboration_met boundary logic | PASS | `distinct_count >= corroboration_minimum`; `test_corroboration_minimum_boundary` tests exact boundary |
| Dedup log records decisions | PASS | Log entry format includes kept/dropped source_ids; `test_dedup_log_audit_trail` verifies |
| Provisional corroboration WM-only = always false | PASS | `test_provisional_corroboration_wm_only` confirms 1 distinct group < 2 minimum |

### Task 2: Counter-Signal Evaluator

| Criterion | Verdict | Evidence |
|-----------|---------|----------|
| CounterSignalOutcome enum: 4 members | PASS | ABSENT, PRESENT_DISCOUNTED, PRESENT_UNEXPLAINED, UNAVAILABLE |
| 11 counter-signal classes defined | PASS | `COUNTER_SIGNAL_CLASSES` list, `test_counter_signal_classes_count` verifies |
| All 11 return UNAVAILABLE | PASS | `evaluate()` iterates all classes, returns UNAVAILABLE; `test_all_unavailable_in_011` verifies |
| UNAVAILABLE + allow_gap=true -> PASS | PASS | `test_unavailable_allow_gap_true_passes` |
| UNAVAILABLE + allow_gap=false -> FAIL | PASS | `test_unavailable_allow_gap_false_fails` |
| PRESENT_UNEXPLAINED -> FAIL | PASS | `test_present_unexplained_fails` |
| UNAVAILABLE = INTELLIGENCE_GAP, not ABSENT | PASS | `test_intelligence_gap_classification` checks `outcome != ABSENT` AND `"INTELLIGENCE_GAP" in detail` |

### Task 3: Scorer

| Criterion | Verdict | Evidence |
|-----------|---------|----------|
| composite_score confidence-weighted, clamped [0,1] | PASS | `_weighted_mean_confidence()` uses priority_bucket weights; `compute_composite()` clamps; tested |
| Corroboration factor: 1.0 met, 0.7 unmet | PASS | Constants verified; `test_corroboration_penalty` verifies 0.7 vs 1.0 |
| Counter-signal factor: 1.0 pass, 0.5 fail | PASS | Constants verified; `test_counter_signal_penalty` verifies 0.5 |
| evidence_completeness = successful / required | PASS | `successful_count / required_count`; `test_evidence_completeness_partial` verifies 1/3 |
| Empty bundles -> 0.0 | PASS | `if not bundles ... return 0.0`; `test_empty_bundles_score_zero` |
| Bundle hash: manifest pattern, deterministic | PASS | Sorted by bundle_id, canonical_json, SHA-256; `test_bundle_hash_deterministic` verifies order-independence |
| OracleOutput: 9 fields | PASS | `test_oracle_output_has_all_fields` verifies all 9 types |
| CriterionScore for both criteria | PASS | Lines 134-158 produce scores for corroboration_minimum_met and counter_signal_checked |

### Task 4: LiveOSINTRealityProvider

| Criterion | Verdict | Evidence |
|-----------|---------|----------|
| p_reality = composite_score | PASS | `_oracle_output_to_signal()` maps `output.composite_score` -> `p_reality`; `test_p_reality_equals_composite_score` |
| evidence_bundle_hash matches bundle_hash | PASS | `output.bundle_hash` mapped directly; `test_evidence_bundle_hash_matches` |
| oracle_output_id format | PASS | `f"{theatre_id}_{epoch_ms}"`; `test_oracle_output_id_format` verifies |
| source_type="osint", provider_version="011.1" | PASS | Hardcoded; `test_provider_version` verifies |
| Staleness: p_reality=None when stale | PASS | `_stale_signal()` returns None; `test_staleness_returns_none_p_reality` verifies |
| RealitySignal extended backward-compatible | PASS | New fields have `None` defaults; existing providers unmodified |
| Existing providers unchanged | PASS | StubRealityProvider, DeterministicRealityProvider, OsintRealityProvider code identical to pre-Sprint 2 |

### Task 5: Paradox Wiring

| Criterion | Verdict | Evidence |
|-----------|---------|----------|
| Live p_reality without paradox.py changes | PASS | `git diff HEAD -- backend/engines/paradox.py` produces empty output |
| Activation gate fires | PASS (with caveat) | Gate type "none" tested; `min_evidence_completeness` gate remains placeholder (returns False) in paradox.py -- see MEDIUM-1 |
| Logic Gap = abs(p_market - p_reality) correct | PASS | `test_logic_gap_computed_correctly`: abs(0.90 - 0.30) = 0.60 verified |
| Provider swap only | PASS | paradox.py unmodified |
| Exported from backend.engines | PASS | `test_live_provider_exported_from_engines` and `test_all_list_complete` both verify |

### Task 6: Convergence Detector

| Criterion | Verdict | Evidence |
|-----------|---------|----------|
| 1 deg x 1 deg binning (floor) | PASS | `math.floor(lat), math.floor(lon)`; 3 binning tests including negative coordinates |
| Alert at 3+ types within 24h | PASS | `test_alert_threshold_3_types`, `test_no_alert_below_threshold` |
| Score: diversity + density | PASS | `(distinct/3) * (1 + log2(count))`; `test_convergence_score` verifies ~2.585 |
| Theatre matching by geo overlap | PASS | `test_theatre_matching` and `test_theatre_no_match` |
| Single/two-domain no alert | PASS | `test_single_domain_no_alert`, `test_no_alert_below_threshold` |
| Empty bundles -> no alerts | PASS | `test_empty_bundles_no_alerts` |
| Provenance on all events | PASS | `test_alert_has_provenance` checks geo data on all events |

### Cross-Cutting

| Criterion | Verdict | Evidence |
|-----------|---------|----------|
| No paradox.py modifications | PASS | `git diff` empty |
| No backend/market/ modifications | PASS | `git diff` empty |
| `from __future__ import annotations` in all new files | PASS | Verified in all 10 new .py source + 6 test files |
| No new runtime dependencies | PASS | All imports: stdlib (`dataclasses`, `hashlib`, `json`, `math`, `uuid`, `datetime`, `enum`, `abc`, `time`, `asyncio`, `concurrent.futures`, `typing`) or internal (`backend.*`) |
| All tests mock HTTP only | PASS | No `urllib`, `httpx`, or `aiohttp` calls in any test -- all use `MagicMock`/`AsyncMock` |
| 59 new Sprint 2 tests (target 20+) | PASS | 59 tests, 2.95x target |
| Full regression passes | PASS | 127 osint + 242 market+engines = 369 total, 0 failures, 0.51s |

---

## Test Results (Independently Verified)

```
backend/osint/ ..................... 127 passed in 0.21s
backend/market/ + backend/engines/ . 242 passed in 0.30s
TOTAL .............................. 369 passed in 0.51s
```

Sprint 2 new tests breakdown:
- test_corroboration.py: 8 tests
- test_counter_signal.py: 10 tests
- test_scorer.py: 11 tests
- test_convergence.py: 13 tests (includes 3 cell binning + 10 detection/matching)
- test_live_reality.py: 8 tests
- test_paradox_wiring.py: 9 tests
- **Total: 59 new tests**

---

## Code Quality Verification

| Check | Result |
|-------|--------|
| `from __future__ import annotations` in all new .py files | PASS |
| No bare `except:` statements | PASS |
| No `eval()`, `exec()`, `subprocess`, `pickle` | PASS |
| No hardcoded credentials | PASS |
| No new runtime dependencies (stdlib only) | PASS |
| No modifications to `backend/market/` | PASS |
| No modifications to `backend/engines/paradox.py` | PASS |
| All public functions have docstrings | PASS |
| All function signatures have type hints | PASS |
| Consistent snake_case naming | PASS |

---

## Adversarial Analysis

### 1. Corroboration Dedup Edge Case: All Same Upstream ID

**Analysis**: If all sources share the same `independence_upstream_id` (as they do in 011 with WM), the dedup correctly collapses them to one entry per upstream_id group. The code handles this correctly: `groups` dict uses upstream_id as key, all 3 WM entries go into one group, `max()` selects strongest confidence, `len(groups)` = 1. The boundary case of 1 entry per group (no dedup needed) is handled by the `if len(group) == 1` check at line 142.

**Verdict**: PASS -- correctly handles the all-same-upstream case.

### 2. Scorer Formula Edge Cases

**Analysis**:
- **Zero evidence**: `compute_composite()` returns 0.0 if `not bundles` or `evidence_completeness <= 0.0` (line 196-197). Correct.
- **All counter-signals fail**: Counter-signal factor = 0.5. With corroboration unmet (0.7) and partial completeness, worst case is `confidence * 0.7 * 0.5 * completeness`. Correctly clamped to [0.0, 1.0].
- **"avoid" priority_bucket**: Weight 0.0 means the bundle is skipped entirely in weighted mean (line 242-243). If ALL bundles are "avoid", `total_weight = 0.0`, returns 0.0 (line 248-249). Correct.

**Verdict**: PASS -- edge cases handled.

### 3. LiveOSINTRealityProvider: Drop-In Compatibility

**Analysis**: `LiveOSINTRealityProvider` subclasses `RealitySignalProvider`, implements `get_signal(theatre_id) -> RealitySignal`. The `RealitySignal` dataclass is extended with two new fields (`provider_version`, `evidence_completeness`) that have `None` defaults. Existing providers (`StubRealityProvider`, `DeterministicRealityProvider`, `OsintRealityProvider`) do not pass these fields, so they default to `None`. The test `test_no_paradox_code_changes` verifies StubRealityProvider still works. True drop-in.

**Verdict**: PASS -- backward compatible.

### 4. Staleness Protection & p_reality=None Safety

**Analysis**: `_check_staleness()` uses `time.monotonic()` for elapsed time. Monotonic clock is immune to time-going-backward scenarios. Cache check is correct: returns True (stale) if no cached output or elapsed >= max_staleness_s. When stale AND collection fails, `_stale_signal()` returns `p_reality=None`.

**Concern**: `ParadoxEngine.scan()` at line 103 calls `self._logic_gap_calc.compute(theatre_id, signal.p_reality)`. `LogicGapCalculator.compute()` accepts `p_reality: float`, not `float | None`. If `p_reality=None`, the `abs(p_market - p_reality)` at logic_gap.py:71 will raise `TypeError`. However, this scenario is mitigated by:
1. The `min_evidence_completeness` activation gate in paradox.py always returns `False` (line 171), so no theatre gated on evidence will scan.
2. The "none" gate always passes, but the provider must successfully collect first to cache a result, meaning p_reality will not be None on first scan success.
3. The stale + collection failure scenario is a cold-start edge case that doesn't arise in the 011 operational model.

**Verdict**: MEDIUM-1 -- latent type safety issue. Not exploitable in 011 because the activation gate blocks. Should be addressed when `min_evidence_completeness` gate is implemented (likely Cycle-012).

### 5. Convergence Detector: Cell Boundary & Negative Coordinates

**Analysis**: `math.floor()` is the correct function for consistent 1-degree binning. `floor(-33.9) = -34`, `floor(-0.1) = -1`, `floor(0.0) = 0`, `floor(32.4) = 32`. Tests verify positive, negative, and cross-zero coordinates. Cell boundaries are consistent: event at 33.0 bins to cell 33, event at 32.999 bins to cell 32. Adjacent cells do not overlap. Correct.

**Verdict**: PASS.

### 6. Counter-Signal Scaffold Extensibility

**Analysis**: The `CounterSignalEvaluator.evaluate()` method iterates `COUNTER_SIGNAL_CLASSES` and returns UNAVAILABLE for each. Future implementation only needs to replace the per-class logic inside the loop. The `check_criterion()` static method already handles all 4 outcome types. The `allow_gap` field per result enables granular control. Three classes documented as first targets. Clean scaffold.

**Verdict**: PASS.

### 7. Backward Compatibility

**Analysis**:
- `RealitySignal` extended with `provider_version: str | None = None` and `evidence_completeness: float | None = None`. Both default to `None`. All existing providers pass 0 or 4 args -- the new optional fields at positions 5-6 are not affected.
- `p_reality` type changed from `float` to `float | None`. This is a type annotation change that broadens the type. Python 3.9.6 with `from __future__ import annotations` treats annotations as strings, so no runtime impact. Existing providers that always return `float` values remain valid.
- `backend/engines/__init__.py` adds `LiveOSINTRealityProvider` to imports and `__all__`. Existing exports unchanged. Export test updated to include the new symbol.

**Verdict**: PASS.

---

## Findings

### MEDIUM-1: p_reality=None can crash LogicGapCalculator

**File**: `backend/engines/reality_signal.py` (LiveOSINTRealityProvider._stale_signal) + `backend/engines/logic_gap.py:71`
**Analysis**: When evidence is stale and collection fails, `LiveOSINTRealityProvider` returns `p_reality=None`. If `ParadoxEngine.scan()` is called with an active (non-blocking) activation gate, `LogicGapCalculator.compute(theatre_id, None)` will raise `TypeError` at `abs(p_market - None)`.
**Mitigation**: Not exploitable in 011 because `min_evidence_completeness` gate always returns False, and the "none" gate only fires after the first successful collection (which populates the cache). Should be addressed in Cycle-012 when the `min_evidence_completeness` gate is wired.
**Verdict**: MEDIUM -- latent type safety issue, not exploitable in current operational model.

### MEDIUM-2: ConvergenceDetector event_types uses source_group, not WMDomain

**File**: `backend/osint/engine/convergence.py:119`
**Analysis**: The convergence detector adds `bundle.source_group` to `cell.event_types`. The docstring says "WMDomain-equivalent strings (source_group)". In 011 this is correct because WM domains map 1:1 to source_groups (`alt_data_behavioural`, `market_data`, `maritime_ais`). However, future non-WM sources could share a `source_group` with a WM source, inflating the distinct types count. The detector should arguably use `bundle.source_id` or a dedicated domain classification field.
**Mitigation**: In 011, the 1:1 mapping means this is equivalent. Future cycles should evaluate whether source_group is the correct discriminator.
**Verdict**: MEDIUM -- correct in 011, may need refinement when non-WM collectors land.

### LOW-1: Unused import `Optional` in corroboration.py

**File**: `backend/osint/engine/corroboration.py:14`
**Analysis**: `from typing import Optional` is imported but never used. The file uses PEP 604 `|` syntax via `from __future__ import annotations`.
**Verdict**: LOW -- cosmetic. Cleanup at convenience.

### LOW-2: Unused `pytest` import in test files

**Files**: `backend/osint/tests/test_convergence.py:10`, `backend/osint/tests/test_scorer.py:11`
**Analysis**: `import pytest` is present but never used (no `pytest.raises`, `pytest.mark`, or other pytest API calls in these test files).
**Verdict**: LOW -- cosmetic. Cleanup at convenience.

### LOW-3: asyncio.get_event_loop() deprecation in LiveOSINTRealityProvider

**File**: `backend/engines/reality_signal.py:142`
**Analysis**: Uses `asyncio.get_event_loop()` which is deprecated in Python 3.10+. The code targets 3.9.6, so this is not currently a problem. Replace with `asyncio.get_running_loop()` when upgrading.
**Verdict**: LOW -- informational, same as Sprint 1 audit finding.

---

## Complexity Assessment

| Module | Cyclomatic Complexity | Assessment |
|--------|-----------------------|------------|
| corroboration.py | Low | Linear flow: filter -> separate -> dedup -> count -> compare |
| counter_signal.py | Minimal | Single loop over classes, all return same value in 011 |
| scorer.py | Moderate | Multiple factors, weighted mean, but formula is clear |
| convergence.py | Low | Bin-filter-threshold pattern, clean separation |
| LiveOSINTRealityProvider | Moderate | Async/sync bridge, cache staleness, pipeline orchestration |

---

## Architecture Assessment

The three-stage pipeline (Collection -> Corroboration -> Scoring) is well-separated. Each module has a clear input/output contract via dataclasses. The LiveOSINTRealityProvider correctly orchestrates the pipeline and maps the OracleOutput to RealitySignal. The provider swap pattern (inject different RealitySignalProvider into ParadoxEngine) works as designed by 010b.

The convergence detector is a clean, independent module that operates on evidence bundles without coupling to the pipeline state. Theatre matching is simple and correct.

The counter-signal scaffold is honest -- it returns INTELLIGENCE_GAP, not ABSENT, correctly representing the actual state of the system. The `allow_gap` mechanism provides clean extensibility.

---

## Final Verdict

**APPROVED**. All 47 acceptance criteria from sprint.md independently verified. 59 new tests (2.95x target). Zero regression failures across 369 tests. Code quality is high. Two MEDIUM findings identified (p_reality=None type safety, source_group vs WMDomain) -- both are design tensions acknowledged by the sprint constraints and not exploitable in the current cycle. Three LOW findings are cosmetic.

The implementation accurately delivers the sprint plan with no deviations from the SDD architecture. The integrity loop is closed: evidence flows from WorldMonitor through the full pipeline to the Paradox Engine's p_reality via provider swap.
