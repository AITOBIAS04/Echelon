# Sprint Review -- Sprint 22 (Cycle-011 Sprint-2): Corroboration + Scoring + Paradox Wiring + Convergence

**Reviewer**: Implementation Agent
**Date**: 2026-03-03
**Sprint**: 22 (local sprint-2, Cycle-011)

---

## Summary

Sprint 2 delivers the evidence quality layer for the OSINT pipeline and wires it into the Paradox Engine. Four new engine modules (corroboration, counter-signal evaluator, scorer, convergence detector) plus LiveOSINTRealityProvider in `backend/engines/reality_signal.py` complete the three-stage pipeline: Collection -> Corroboration -> Scoring -> p_reality.

After this sprint, the Paradox Engine's Logic Gap equation uses a confidence-weighted composite score derived from real-world evidence instead of a stub value.

---

## Tasks Completed

| # | Task | File(s) | Lines |
|---|------|---------|-------|
| 1 | Corroboration Engine | `backend/osint/engine/corroboration.py` | 154 |
| 2 | Counter-Signal Evaluator | `backend/osint/engine/counter_signal.py` | 140 |
| 3 | Composite Scorer | `backend/osint/engine/scorer.py` | 218 |
| 4 | LiveOSINTRealityProvider | `backend/engines/reality_signal.py` (MODIFIED) | +134 |
| 5 | Paradox Wiring | Via LiveOSINTRealityProvider + exports | integrated |
| 6 | Convergence Detector | `backend/osint/engine/convergence.py` | 162 |
| 7 | Package Updates | `backend/osint/__init__.py`, `backend/osint/engine/__init__.py`, `backend/engines/__init__.py` | modified |
| 8 | Corroboration Tests | `backend/osint/tests/test_corroboration.py` | 225 |
| 9 | Counter-Signal Tests | `backend/osint/tests/test_counter_signal.py` | 155 |
| 10 | Scorer Tests | `backend/osint/tests/test_scorer.py` | 280 |
| 11 | Convergence Tests | `backend/osint/tests/test_convergence.py` | 200 |
| 12 | Live Reality Tests | `backend/osint/tests/test_live_reality.py` | 210 |
| 13 | Paradox Wiring Tests | `backend/osint/tests/test_paradox_wiring.py` | 250 |

---

## Test Results

| Suite | Tests | Status |
|-------|-------|--------|
| test_corroboration.py | 8 | ALL PASS |
| test_counter_signal.py | 10 | ALL PASS |
| test_scorer.py | 11 | ALL PASS |
| test_convergence.py | 13 | ALL PASS |
| test_live_reality.py | 8 | ALL PASS |
| test_paradox_wiring.py | 9 | ALL PASS |
| **Sprint 22 Total** | **59** | **ALL PASS** |

### Regression

| Suite | Tests | Status |
|-------|-------|--------|
| backend/osint/ (full) | 127 | ALL PASS (Sprint 1 + Sprint 2) |
| backend/market/ | 97 | ALL PASS |
| backend/engines/ | 145 (incl. 1 updated export test) | ALL PASS |
| **Total** | **369** | **ALL PASS (0.53s)** |

---

## Files Created/Modified

| File | Status | Purpose |
|------|--------|---------|
| `backend/osint/engine/corroboration.py` | NEW | CorroborationEngine + CorroborationResult |
| `backend/osint/engine/counter_signal.py` | NEW | CounterSignalEvaluator + 11 classes |
| `backend/osint/engine/scorer.py` | NEW | Scorer + OracleOutput + CriterionScore |
| `backend/osint/engine/convergence.py` | NEW | ConvergenceDetector + ConvergenceAlert |
| `backend/osint/tests/test_corroboration.py` | NEW | 8 corroboration tests |
| `backend/osint/tests/test_counter_signal.py` | NEW | 10 counter-signal tests |
| `backend/osint/tests/test_scorer.py` | NEW | 11 scorer tests |
| `backend/osint/tests/test_convergence.py` | NEW | 13 convergence tests |
| `backend/osint/tests/test_live_reality.py` | NEW | 8 live provider E2E tests |
| `backend/osint/tests/test_paradox_wiring.py` | NEW | 9 paradox wiring + integration tests |
| `backend/engines/reality_signal.py` | MODIFIED | RealitySignal extended + LiveOSINTRealityProvider |
| `backend/engines/__init__.py` | MODIFIED | LiveOSINTRealityProvider export |
| `backend/engines/tests/test_integration.py` | MODIFIED | Updated expected exports set |
| `backend/osint/__init__.py` | MODIFIED | Sprint 2 exports |
| `backend/osint/engine/__init__.py` | MODIFIED | Sprint 2 engine exports |

---

## Architecture Decisions

1. **RealitySignal backward compatibility**: Extended with optional `provider_version: str | None = None` and `evidence_completeness: float | None = None`. Existing providers (StubRealityProvider, DeterministicRealityProvider, OsintRealityProvider) unchanged. All pre-existing tests pass without modification.

2. **p_reality type change**: Changed from `float` to `float | None` in RealitySignal to support staleness protection. When evidence is stale, `p_reality=None` signals Paradox to skip.

3. **LiveOSINTRealityProvider in reality_signal.py**: Placed directly in `backend/engines/reality_signal.py` alongside other providers per sprint plan. Uses lazy imports for OSINT modules to avoid circular dependencies.

4. **Corroboration dedup by upstream_id**: All three WM endpoints share `independence_upstream_id: "worldmonitor"` in the registry. After dedup, only the highest-confidence entry survives. `corroboration_met` is always False in Cycle-011 (provisional corroboration).

5. **Counter-signal scaffolding**: All 11 classes return UNAVAILABLE with `allow_gap=True`. UNAVAILABLE is explicitly classified as INTELLIGENCE_GAP (not ABSENT) per AC-1 GapKind semantics. Criterion passes honestly under gap tolerance.

6. **Composite score formula**: `weighted_mean(confidence) x corroboration_factor x counter_signal_factor x evidence_completeness`, clamped to [0.0, 1.0]. Weights from registry priority_bucket.

7. **Paradox.py unmodified**: No changes to `backend/engines/paradox.py`. Provider swap happens at construction time. The `min_evidence_completeness` activation gate remains a placeholder in paradox.py (always returns False) since paradox.py cannot be modified.

8. **No modifications to backend/market/**: Zero changes.

---

## Acceptance Criteria Status

- [x] Corroboration deduplicates by `independence_upstream_id` (3 WM -> 1)
- [x] Keeps strongest-confidence entry per upstream_id
- [x] `distinct_source_groups` counted after dedup
- [x] `corroboration_met = distinct_source_groups >= corroboration_minimum`
- [x] Dedup log records every decision
- [x] Provisional corroboration: WM-only = always `corroboration_met=false`
- [x] CounterSignalOutcome enum has all 4 members
- [x] All 11 counter-signal classes defined
- [x] All 11 return UNAVAILABLE in 011
- [x] UNAVAILABLE with allow_gap=true -> PASS
- [x] UNAVAILABLE with allow_gap=false -> FAIL
- [x] PRESENT_UNEXPLAINED -> FAIL
- [x] UNAVAILABLE is INTELLIGENCE_GAP, not ABSENT
- [x] composite_score confidence-weighted, clamped to [0.0, 1.0]
- [x] Corroboration factor: 1.0 met, 0.7 unmet
- [x] Counter-signal factor: 1.0 pass, 0.5 fail
- [x] evidence_completeness = successful / required
- [x] Empty bundles -> score 0.0
- [x] Bundle hash: manifest pattern, deterministic
- [x] OracleOutput has all 9 fields
- [x] LiveOSINTRealityProvider.get_signal() returns RealitySignal with p_reality = composite_score
- [x] evidence_bundle_hash matches OracleOutput.bundle_hash
- [x] oracle_output_id format: "{theatre_id}_{scored_at_ms}"
- [x] source_type = "osint", provider_version = "011.1"
- [x] Staleness protection: p_reality = None when stale
- [x] RealitySignal extended with provider_version and evidence_completeness (backward compatible)
- [x] Existing providers unchanged
- [x] Paradox Engine receives live p_reality without paradox.py changes
- [x] Logic Gap = abs(p_market - p_reality) computed correctly
- [x] LiveOSINTRealityProvider exported from backend.engines
- [x] Convergence: events binned by 1 deg x 1 deg cell
- [x] Alert fires when 3+ distinct types co-locate within 24-hour window
- [x] Convergence score rewards type diversity and event density
- [x] Theatre matching by geographic overlap
- [x] Single/two-domain cells do not fire alerts
- [x] Empty bundles -> no alerts
- [x] All events carry full provenance
- [x] No modifications to backend/engines/paradox.py
- [x] No modifications to backend/market/
- [x] All tests use mock HTTP only
- [x] 59 new Sprint 2 tests pass (target: 20+)
- [x] Full regression passes (369 tests total)
