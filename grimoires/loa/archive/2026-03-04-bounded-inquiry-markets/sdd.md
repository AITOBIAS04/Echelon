# SDD — Cycle-014: Bounded Inquiry Markets

**Cycle:** cycle-014
**Date:** 4 March 2026
**PRD:** grimoires/loa/prd.md

---

## 1. Architecture Overview

Cycle-014 threads the `InquiryClass` concept through 6 layers:

```
Template JSON (inquiry_class field)
  → TheatreTemplate DB model (inquiry_class column)
    → Theatre DB model (inquiry_class column, inherited from template)
      → T0Context (inquiry_class field)
        → T1 RulesEngine (InquiryBehaviourAdapter modifies decision profiles)
          → ResolutionEngine (inquiry-class-aware triggers)
            → Certificate (inquiry_class + resolution_trigger_reason)
```

No new execution paths. No new services. The inquiry class is metadata that propagates through existing infrastructure and influences behaviour at decision points.

---

## 2. New Module: `backend/schemas/inquiry.py`

Single source of truth. Every other file imports from here.

```python
from enum import StrEnum

class InquiryClass(StrEnum):
    COUNTERFACTUAL = "COUNTERFACTUAL"
    INVESTIGATIVE = "INVESTIGATIVE"
    INSPECTION = "INSPECTION"
    SURVEY = "SURVEY"
    SCRUTINY = "SCRUTINY"

INQUIRY_CLASS_ALIASES = {
    "INVESTIGATION": InquiryClass.INVESTIGATIVE,
    "AUDIT": InquiryClass.SCRUTINY,
}

def resolve_inquiry_class(raw: str) -> InquiryClass:
    """Resolve canonical or aliased value. Raises ValueError on unknown."""
    upper = raw.upper().strip()
    if upper in InquiryClass.__members__:
        return InquiryClass(upper)
    alias = INQUIRY_CLASS_ALIASES.get(upper)
    if alias is not None:
        return alias
    raise ValueError(
        f"Unknown inquiry class '{raw}'. "
        f"Valid: {[e.value for e in InquiryClass]}. "
        f"Aliases: {list(INQUIRY_CLASS_ALIASES.keys())}"
    )
```

**Design decisions:**
- `StrEnum` so values serialise as strings without `.value` calls
- Alias map handles backward compat; `resolve_inquiry_class()` is the only entry point for untrusted input
- Validator raises `ValueError` with helpful message listing valid values and aliases

---

## 3. Schema Changes

### 3.1 `backend/schemas/theatre.py`

**TheatreCreate** — add optional `inquiry_class` field (defaults extracted from `template_json`):
```python
inquiry_class: Optional[str] = Field(
    None,
    description="Inquiry class (COUNTERFACTUAL|INVESTIGATIVE|INSPECTION|SURVEY|SCRUTINY)"
)
```
The model validator extracts `inquiry_class` from `template_json` if not explicitly provided. Validation via `resolve_inquiry_class()` — aliases accepted, unknown values rejected.

**TheatreResponse** — add `inquiry_class: Optional[str]`.

**TheatreCertificateResponse** — add `inquiry_class: Optional[str]`.

**TemplateResponse** — add `inquiry_class: Optional[str]`.

### 3.2 `backend/database/models.py`

**TheatreTemplate** (line 487):
```python
inquiry_class: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
```
Index: `Index("ix_theatre_templates_inquiry_class", "inquiry_class")`

**Theatre** (line 511):
```python
inquiry_class: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
```
Index: `Index("ix_theatres_inquiry_class", "inquiry_class")`

**TheatreCertificate** (line 565):
```python
inquiry_class: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
```

All nullable for backward compatibility. Existing rows get `NULL` (interpreted as `COUNTERFACTUAL` by the application layer). New theatres get explicit values.

---

## 4. API Changes: `backend/api/theatre_routes.py`

### Theatre Creation
1. Extract `inquiry_class` from request body or `template_json`
2. Resolve via `resolve_inquiry_class()` (handles aliases)
3. Store on both `TheatreTemplate` and `Theatre` records
4. Return in response

### Theatre Response
All GET endpoints include `inquiry_class` in the response. `None` maps to `"COUNTERFACTUAL"` in the response serialisation.

---

## 5. Agent Layer Changes

### 5.1 T0Context — `backend/agents/context_compiler.py`

Add field to `T0Context` dataclass (after `stop_loss_threshold`):
```python
inquiry_class: str = "COUNTERFACTUAL"
```

Update `ContextCompiler.compile()` to accept `inquiry_class: str = "COUNTERFACTUAL"` parameter and pass it through.

Update `compute_hash()` to include `inquiry_class` in the hashable dict.

### 5.2 InquiryBehaviourAdapter — `backend/agents/inquiry_behaviour.py` (NEW)

Adapts archetype decision profiles per inquiry class. §X.4 domain adaptation matrix:

```python
@dataclass(frozen=True)
class InquiryProfile:
    """Inquiry-class-specific behaviour modifiers for an archetype."""
    pattern_name_override: str       # e.g. "evidence_front_running" instead of "momentum_exploitation"
    evidence_weight_modifier: float  # multiplier for evidence_sensitivity
    momentum_weight_modifier: float  # multiplier for price-based signals
    action_description: str          # for reasoning trace

INQUIRY_PROFILES: dict[tuple[str, str], InquiryProfile]
# Keys: (archetype, inquiry_class) → InquiryProfile
# Example: ("SHARK", "INVESTIGATIVE") → InquiryProfile(
#     pattern_name_override="evidence_front_running",
#     evidence_weight_modifier=1.5,
#     momentum_weight_modifier=0.7,
#     action_description="Evidence front-running: trading ahead of evidence arrival"
# )
```

**30 profiles total** (6 archetypes x 5 inquiry classes). Default profile used for unknown combinations.

The adapter does NOT replace the rules engine. It provides modifiers that the rules engine applies:
- `evidence_sensitivity` is scaled by `evidence_weight_modifier`
- `risk_appetite` is scaled by `momentum_weight_modifier`
- `pattern_name` is overridden in the T1Decision
- `reasoning_trace` includes the `action_description`

### 5.3 RulesEngine — `backend/agents/rules_engine.py`

Add `inquiry_class` parameter to `decide()`:
```python
def decide(self, ctx: T0Context, tick: int, rng_seed: int) -> T1Decision:
```

The engine reads `ctx.inquiry_class` and applies `InquiryBehaviourAdapter` modifiers before dispatching to archetype-specific logic. The T0Context already contains the inquiry class — no API change to `decide()`, just internal behaviour change.

---

## 6. Resolution Engine Changes: `backend/market/resolution.py`

### 6.1 Resolution Trigger Reasons

New enum in `resolution.py`:
```python
class ResolutionTrigger(str, Enum):
    SIMULATION_TERMINAL = "simulation_terminal"
    EVIDENCE_THRESHOLD_MET = "evidence_threshold_met"
    CRITERIA_COMPLETE = "criteria_complete"
    PARTICIPATION_THRESHOLD = "participation_threshold"
    CLAIM_VERDICT = "claim_verdict"
    TIME_WINDOW_CLOSED = "time_window_closed"
```

### 6.2 SettlementReport Extension

Add fields:
```python
inquiry_class: str = "COUNTERFACTUAL"
resolution_trigger_reason: str = "simulation_terminal"
```

### 6.3 Inquiry-Class-Aware Resolution Check

New static method `check_resolution_ready()` that evaluates whether a market is ready for resolution based on its inquiry class:

| Inquiry Class | Resolution Check |
|---|---|
| COUNTERFACTUAL | Existing behaviour — time window or evidence threshold |
| INVESTIGATIVE | `evidence_coverage_pct >= corroboration_minimum` OR time window closed |
| INSPECTION | All committed criteria have been evaluated (criteria_complete count == total) |
| SURVEY | `participation_count >= participation_threshold` OR time window closed |
| SCRUTINY | Claim verdict reached (verified or falsified) OR time window closed |

The check returns `(ready: bool, trigger_reason: ResolutionTrigger)`. The existing `begin_resolution()` + `settle()` flow is preserved — this method is called *before* `begin_resolution()` to determine readiness and reason.

---

## 7. Evidence Service: `backend/services/evidence_service.py` (NEW)

Extends `TheatreEvidenceCollector` with inquiry-class-aware accumulation rules:

```python
class InquiryEvidenceRules:
    """Evidence accumulation rules per inquiry class."""

    @staticmethod
    def validate_evidence(
        inquiry_class: str,
        evidence_snapshot: EvidenceSnapshot,
        theatre_config: dict,
    ) -> EvidenceValidation:
        """Validate evidence against inquiry-class-specific rules."""
```

| Inquiry Class | Evidence Rule |
|---|---|
| COUNTERFACTUAL | Accept simulation divergence signals. Mode 1: OSINT bundles per normal pipeline |
| INVESTIGATIVE | Validate source against committed list. Require `corroboration_minimum` distinct upstreams |
| INSPECTION | Single-source acceptable (artefact under inspection). Binary pass/fail per criterion |
| SURVEY | No OSINT pipeline — market's own position distribution is the evidence |
| SCRUTINY | Validate claim + counter-evidence. Require adversarial confirmation |

This service does NOT replace `TheatreEvidenceCollector`. It adds a validation layer on top.

---

## 8. Certificate Changes

### 8.1 `osint/osint_pipeline/models/certificate.py`

Replace stale description:
```python
# Before:
inquiry_class: str = Field(description="INSPECTION | INVESTIGATION | AUDIT")
# After:
inquiry_class: str = Field(
    description="COUNTERFACTUAL | INVESTIGATIVE | INSPECTION | SURVEY | SCRUTINY"
)
```

Add field:
```python
resolution_trigger_reason: str = Field(
    default="",
    description="How resolution was triggered (evidence_threshold_met, criteria_complete, etc.)"
)
```

Note: Cross-package import from `backend.schemas.inquiry` may be problematic. Strategy: validate using a standalone validator function in the certificate module that mirrors the canonical enum values. This avoids circular dependency between `osint/` and `backend/`.

### 8.2 `osint/osint_pipeline/engine/certificate_generator.py`

Accept `resolution_trigger_reason` parameter and include in certificate output.

---

## 9. Template Library

### 9.1 Template JSON Schema Extension

Every template JSON file must include:
```json
{
  "inquiry_class": "INSPECTION",
  ...
}
```

Template loader validates this field on load via `resolve_inquiry_class()`.

### 9.2 New Templates (Sprint 2)

4 minimal proof-of-wiring templates:

| Template | Inquiry Class | Execution Path | Outcomes |
|---|---|---|---|
| `counterfactual_geopolitical_v1.json` | COUNTERFACTUAL | market | 2 (YES/NO fork) |
| `investigative_corporate_v1.json` | INVESTIGATIVE | market | 2 (CONFIRMED/UNCONFIRMED) |
| `survey_asset_valuation_v1.json` | SURVEY | market | 3 (UNDERVALUED/FAIR/OVERVALUED) |
| `scrutiny_tvl_audit_v1.json` | SCRUTINY | market | 2 (VERIFIED/FALSIFIED) |

Each template includes: `theatre_id`, `execution_path`, `template_family`, `inquiry_class`, `outcomes`, `committed_sources`, `resolution_rules`, `schema_version`.

### 9.3 Existing Template Migration

`inspection_corporate_status_v1.json` already has `"inquiry_class": "INSPECTION"` — no change needed.

---

## 10. Test Strategy

### Sprint 1 Tests

| Test File | Coverage |
|---|---|
| `backend/schemas/tests/test_inquiry.py` | Enum values, alias resolution, rejection of unknowns, case insensitivity |
| `backend/schemas/tests/test_theatre_inquiry.py` | TheatreCreate with inquiry_class, API response includes it, alias resolution in create |
| `backend/agents/tests/test_context_compiler_inquiry.py` | T0Context includes inquiry_class, hash changes with inquiry_class |
| `osint/tests/test_certificate_inquiry.py` | Certificate inquiry_class field, stale values resolved |

### Sprint 2 Tests

| Test File | Coverage |
|---|---|
| `backend/market/tests/test_resolution_inquiry.py` | Resolution trigger per inquiry class, trigger reason in settlement report |
| `backend/services/tests/test_evidence_service.py` | Evidence validation per inquiry class |
| `backend/agents/tests/test_inquiry_behaviour.py` | Behaviour adapter profiles, modifier application |
| `backend/tests/test_bounded_inquiry_e2e.py` | 5 E2E tests: theatre → agents → trading → evidence → resolution → certificate |

### Backward Compatibility

Existing tests must pass without modification. `inquiry_class` is nullable in the DB, optional in the API, and defaults to `COUNTERFACTUAL` in the application layer.

---

## 11. File Change Summary

### New Files (8)

| File | Lines (est.) |
|---|---|
| `backend/schemas/inquiry.py` | ~40 |
| `backend/agents/inquiry_behaviour.py` | ~150 |
| `backend/services/evidence_service.py` | ~100 |
| `backend/tests/test_bounded_inquiry_e2e.py` | ~300 |
| `osint/.../counterfactual_geopolitical_v1.json` | ~50 |
| `osint/.../investigative_corporate_v1.json` | ~50 |
| `osint/.../survey_asset_valuation_v1.json` | ~50 |
| `osint/.../scrutiny_tvl_audit_v1.json` | ~50 |

### Modified Files (9)

| File | Change |
|---|---|
| `backend/schemas/theatre.py` | Add `inquiry_class` to 4 schemas |
| `backend/database/models.py` | Add `inquiry_class` column to 3 models |
| `backend/api/theatre_routes.py` | Inquiry class in create/response/settle |
| `backend/market/resolution.py` | `ResolutionTrigger` enum, inquiry-aware check, settlement report extension |
| `backend/agents/context_compiler.py` | Add `inquiry_class` to T0Context + hash |
| `backend/agents/rules_engine.py` | Apply InquiryBehaviourAdapter modifiers |
| `backend/services/theatre_evidence.py` | Wire to InquiryEvidenceRules |
| `osint/.../models/certificate.py` | Fix description, add resolution_trigger_reason |
| `osint/.../engine/certificate_generator.py` | Accept resolution_trigger_reason |
