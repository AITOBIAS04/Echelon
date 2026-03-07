# Sprint 57 (Cycle-019 Sprint 3) — Implementation Report

## Paradox Risk Evaluator

### Summary

Pure-function paradox risk evaluator with inquiry-class-specific thresholds. Risk is a computed surface (LOW | WATCH | HIGH), not operator-authored.

### Files Created/Modified

| File | Action | Description |
|------|--------|-------------|
| `backend/services/paradox_risk_evaluator.py` | Created | Risk evaluator with 5 inquiry classes, 3 risk levels |
| `backend/tests/test_c019_sprint3_paradox_risk.py` | Created | 6 tests covering all risk levels + persistence |

### Implementation Details

**ParadoxRiskAssessment dataclass**: level, factors dict, explanation string.

**THRESHOLDS dict**: 5 inquiry classes (COUNTERFACTUAL, INVESTIGATIVE, INSPECTION, SURVEY, SCRUTINY) with per-class weights for logic_gap, stability, evidence_freshness, and counter_signal sensitivity.

**evaluate() function**:
- HIGH: active paradox (immediate), or logic_gap > high threshold, or stability < high threshold
- WATCH: logic_gap > watch threshold, stability < watch threshold, counter-signals > 0, or stale evidence (freshness > 72/weight hours)
- LOW: default when no conditions triggered

**persist_risk_to_theatre()**: Updates Theatre model's paradox_risk_level, paradox_risk_factors_json, paradox_risk_updated_at.

### Test Results

```
6 passed in 0.19s
```

1. LOW for healthy theatre (no paradox, low gap, high stability)
2. WATCH for moderate logic gap
3. HIGH for active paradox
4. INVESTIGATIVE weighs evidence freshness higher (same hours → different levels)
5. SCRUTINY weighs counter-signals higher (different explanation language)
6. Theatre paradox_risk persistence roundtrip (SQLite)

### Acceptance Criteria

- [x] Pure function with no side effects (except persist helper)
- [x] 5 inquiry classes with distinct threshold profiles
- [x] 3 risk levels with clear escalation logic
- [x] Evidence freshness weighted by inquiry class
- [x] Counter-signal sensitivity varies by inquiry class
- [x] Theatre model persistence roundtrip verified
