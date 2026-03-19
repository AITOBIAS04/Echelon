# SDD — Cycle-037b: Multi-Evaluator Orchestration + Residual Scoring

**Cycle:** cycle-037b
**Date:** 18 March 2026
**Builder:** Loa

---

## 1. Architecture Summary

Cycle 037b adds the judging layer on top of Cycle 037:

```
EvaluationContract
    ↓
deterministic execution results
    ↓
residual rubric dimensions
    ↓
multi-evaluator orchestrator
    ↓
convergence summary + escalation flag
    ↓
run / certificate provenance
```

This cycle must not reopen contract compilation. It consumes the contract and the planned-vs-executed deterministic state from 037.

---

## 2. File-Level Design

### 2.1 New Schemas

**Add: `backend/schemas/evaluator_orchestration.py`**

Suggested models:

- `EvaluatorScoreRecord`
- `DimensionConvergence`
- `RunConvergenceSummary`
- `EvaluatorOutcome`

Suggested fields:

```python
class EvaluatorScoreRecord(BaseModel):
    evaluator_id: str
    dimension: str
    verdict: str
    score: float | None = None
    rationale: str | None = None
    raw_output: dict | None = None


class DimensionConvergence(BaseModel):
    dimension: str
    outcome: Literal["CONVERGED_PASS", "CONVERGED_FAIL", "DIVERGENT", "SKIPPED"]
    evaluator_ids: list[str]
    verdicts: list[str]
```

### 2.2 New Services

**Add: `backend/services/residual_dimension_filter.py`**

Responsibilities:

- accept `EvaluationContract`
- accept deterministic execution results
- return only rubric dimensions that still require evaluator scoring

**Add: `backend/services/evaluator_orchestrator.py`**

Responsibilities:

- call 3 scorer adapters
- collect outputs
- compute per-dimension convergence
- compute run-level summary

**Add: `backend/services/convergence_policy.py`**

Responsibilities:

- encode 3/3, 2/3, split thresholds
- distinguish converged vs divergent outcomes
- prevent “borderline” from becoming a misuse of 037 `DEFERRED`

### 2.3 Scorer Interface

Use a scorer adapter protocol rather than route-level hardcoding.

Suggested interface:

```python
class ResidualScorer(Protocol):
    evaluator_id: str

    async def score_dimensions(
        self,
        *,
        contract: EvaluationContract,
        dimensions: list[str],
        episode_payload: dict,
    ) -> list[EvaluatorScoreRecord]:
        ...
```

### 2.4 Persistence

Persist orchestration data into existing run-scoped JSON surfaces used by construct verification. Suggested primary location:

- `investigation_evidence_items.construct_meta_json`

Recommended keys:

- `evaluator_scores`
- `dimension_convergence`
- `run_convergence_summary`
- `rubric_version`
- `escalation_required`

### 2.5 Issuance Behavior

Recommended route behavior:

- if deterministic coverage is incomplete → still use Cycle 037 `DEFERRED`
- if deterministic coverage is complete but rubric convergence is divergent → issuance blocked with `DIVERGENT`
- if required dimensions converge → issuance allowed

This cycle should not overload `DEFERRED` with score ambiguity.

---

## 3. Risks and Mitigations

### 3.1 Adapter Coupling

Different scorers may return different output shapes.

Mitigation:

- normalize everything into `EvaluatorScoreRecord`
- preserve raw output for audit only

### 3.2 Score Convergence Is Still Model-Mediated

Even 3 scorers are not “ground truth.”

Mitigation:

- keep deterministic-first
- scope scorer judgments only to residual dimensions
- store full provenance for replay

### 3.3 Cost / Latency

3 scorers cost more and take longer.

Mitigation:

- only run them on residual dimensions
- allow future batching / caching

---

## 4. Files Touched Summary

**New**

- `backend/schemas/evaluator_orchestration.py`
- `backend/services/residual_dimension_filter.py`
- `backend/services/evaluator_orchestrator.py`
- `backend/services/convergence_policy.py`
- tests for Cycle 037b

**Existing likely updated**

- construct scoring / certificate path
- construct route issuance path

---

## 5. After This Cycle Ships

1. deterministic and rubric evaluation are clearly separated
2. rubric scoring has multi-evaluator provenance
3. divergent outcomes are explicit and auditable
4. the certificate path can distinguish missing coverage from scorer disagreement
