# SDD — Cycle-037d: Theatre Construct Verification

**Cycle:** cycle-037d
**Date:** 19 March 2026
**Depends on:** Cycle-037 (contract substrate), Cycle-037b (multi-evaluator), Cycle-037c (domain packs + security checks)
**Sprints:** 4 (0-3)
**Builder:** Loa (backend only)

> Sources: prd.md, context_037d.md, TREMOR construct.json, CORONA construct.json, codebase validation

---

## 1. Architecture Summary

Cycle 037d adds a construct-class layer for theatre constructs on top of the 037 substrate. The pattern mirrors 037c (security checks) exactly: a new planner produces domain-specific `PlannedCheck` entries, and the caller (`contract_service.py`) merges them after `plan_checks()`.

```
construct.yaml (ConstructSpec)
    |
spec_loader.load()                      <-- adds construct_class field
    |
policy_normalizer.normalize()           <-- theatre domains now in KNOWN_PRECISE_DOMAINS
    |
check_planner.plan_checks()             <-- base checks (RUBRIC, BENCHMARK, ANCHOR)
    |                                       unchanged
    +-- security_check_planner ------------ merge security checks (037c, unchanged)
    |
    +-- theatre_check_planner  ------------ merge theatre checks (037d) <-- NEW
         ^
    construct.json (theatre_templates, osint_sources, verification_checks, settlement_tiers)
         ^
    theatre_policy_rules (domain registration + construct.json parsing)
         |
contract_service.create_contract()      <-- caller-side merge, same as corpus_skills
    |
037b residual judging (unchanged)
```

Key principle: **the base pipeline (check_planner.py, policy_normalizer.py core logic) is not modified.** Theatre checks are additive, selected when the construct's `construct_class == "theatre"`.

---

## 2. File-Level Design

### 2.1 Modified: `backend/services/spec_loader.py`

**Sprint:** 0
**Purpose:** Add optional `construct_class` field to `ConstructSpec` dataclass.

Current `ConstructSpec` (lines 13-22):

```python
@dataclass(frozen=True)
class ConstructSpec:
    slug: str
    version: str
    domain_claims: list[str]
    refusals: list[dict]
    skill_manifest: list[dict]
    raw_yaml: str
    spec_hash: str
```

New `ConstructSpec`:

```python
@dataclass(frozen=True)
class ConstructSpec:
    slug: str
    version: str
    domain_claims: list[str]
    refusals: list[dict]
    skill_manifest: list[dict]
    raw_yaml: str
    spec_hash: str
    construct_class: str = "skill"  # "skill" | "theatre" | "bridge"
```

**Change to `load()` function** (lines 32-76): After parsing optional `refusals` (line 62-64), read optional `construct_class`:

```python
    # construct_class: default "skill" for backward compatibility
    raw_class = parsed.get("construct_class", "skill")
    construct_class = str(raw_class) if raw_class in ("skill", "theatre", "bridge") else "skill"
```

And include it in the return statement (after line 68):

```python
    return ConstructSpec(
        slug=str(slug),
        version=str(version),
        domain_claims=[str(c) for c in domain_claims],
        refusals=refusals,
        skill_manifest=skill_manifest,
        raw_yaml=yaml_content,
        spec_hash=spec_hash,
        construct_class=construct_class,
    )
```

**Backward compatibility:** `construct_class` defaults to `"skill"`. Every existing YAML without the field parses identically. The `spec_hash` computation (line 25-29) does not change shape -- it hashes the raw YAML content, so the hash only changes if the YAML content changes. The `skill_manifest` validation (`must be a non-empty list`, line 58-59) remains -- theatre constructs must still declare their skills/commands in `skill_manifest`, which matches TREMOR's `skills` array and CORONA's `skills` array.

---

### 2.2 New: `backend/services/theatre_policy_rules.py`

**Sprint:** 1
**Purpose:** Register theatre-specific precise domains into `KNOWN_PRECISE_DOMAINS`. Parse `construct.json` from external theatre constructs (TREMOR, CORONA) into structured metadata for the theatre check planner.

Follows the exact pattern of `security_policy_rules.py` (lines 1-118).

#### Theatre Precise Domains

10 specific theatre domains to be added to `KNOWN_PRECISE_DOMAINS`:

```python
THEATRE_PRECISE_DOMAINS: set[str] = {
    "seismic_intelligence",
    "space_weather",
    "oracle_verification",
    "settlement_verification",
    "calibration_analysis",
    "prediction_markets",
    "evidence_bundles",
    "ground_truth_export",
    "rlmf_export",
    "theatre_management",
}
```

#### Registration Pattern

Identical to `security_policy_rules.py` lines 37-48:

```python
def register_theatre_domains() -> int:
    """Register theatre-specific precise domains with the policy normalizer.

    Mutates policy_normalizer.KNOWN_PRECISE_DOMAINS by adding theatre domains.
    Returns count of newly added domains (for logging/testing).
    """
    before = len(KNOWN_PRECISE_DOMAINS)
    KNOWN_PRECISE_DOMAINS.update(THEATRE_PRECISE_DOMAINS)
    return len(KNOWN_PRECISE_DOMAINS) - before
```

Import-time registration (same pattern as `security_policy_rules.py` line 118):

```python
# Register theatre domains at import time so they are available
# to the policy normalizer immediately.
_REGISTERED_COUNT = register_theatre_domains()
```

#### construct.json Data Models

Four frozen dataclasses for parsed theatre metadata:

```python
@dataclass(frozen=True)
class TheatreTemplate:
    """A single theatre template from construct.json."""
    id: str
    name: str
    resolution: str          # "binary" | "multi_bucket" | "multi_class"
    oracle: str              # oracle name or resolution method
    brier_type: Optional[str] = None  # "binary" | "multi_class"

@dataclass(frozen=True)
class OsintSource:
    """An OSINT data source from construct.json."""
    id: str
    name: str
    role: str                # "primary" | "cross_validation"

@dataclass(frozen=True)
class VerificationCheck:
    """A declared verification check from construct.json."""
    check: str
    ground_truth: str
    description: str

@dataclass(frozen=True)
class TheatreConstructMeta:
    """Parsed metadata from a theatre construct.json."""
    name: str
    theatre_templates: list[TheatreTemplate]
    osint_sources: list[OsintSource]
    verification_checks: list[VerificationCheck]
    settlement_tiers: list[dict]
    has_brier_scoring: bool
    has_cross_validation: bool
    oracle_names: list[str]
```

#### construct.json Parser

The parser must handle both TREMOR and CORONA naming conventions.

**TREMOR** (`/Users/tobiasharber/Developer/tremor/spec/construct.json`) nests theatre data under `echelon`:

- `echelon.theatre_templates` -- array of 5 templates, each with `id`, `name`, `resolution` (resolution type), `oracle` (oracle name), `brier_type`
- `echelon.osint_sources` -- array of 3 sources, each with `id`, `name`, `role` (primary or cross_validation)
- `echelon.verification_checks` -- array of 5 checks, each with `check`, `ground_truth`, `description`
- `echelon.settlement_tiers` -- array of 3 tiers with `tier`, `name`, `condition`, `evidence_class`, `brier_discount`

**CORONA** (`/Users/tobiasharber/Developer/corona/construct.json`) uses root-level fields:

- `theatre_templates` -- array of 5 templates at root, each with `id`, `name`, `type` (maps to resolution), `resolution` (maps to oracle)
- `data_sources` -- array of 3 sources (not `osint_sources`), each with `name`, `url`, `auth`, `feeds`
- `rlmf.exports` -- array including `"brier_score"`, `"calibration_bucket"` -- proves Brier scoring
- No `verification_checks` or `settlement_tiers` at root or under `echelon`

The parser uses fallback chains:

| Concept | TREMOR path | CORONA path | Fallback |
|---------|-------------|-------------|----------|
| Theatre templates | `echelon.theatre_templates` | `theatre_templates` | empty list |
| OSINT sources | `echelon.osint_sources` | `data_sources` | empty list |
| Resolution type | `[].resolution` | `[].type` | `"binary"` |
| Oracle reference | `[].oracle` | `[].resolution` | `""` |
| Brier type | `[].brier_type` | inferred from `rlmf.exports` | `None` |
| Source ID | `[].id` | derived from `[].name` lowercase | `""` |
| Source role | `[].role` | default `"primary"` | `"primary"` |
| Verification checks | `echelon.verification_checks` | absent | empty list |
| Settlement tiers | `echelon.settlement_tiers` | absent | empty list |

```python
def parse_construct_json(raw_json: str) -> TheatreConstructMeta:
    """Parse a theatre construct.json into structured metadata.

    Handles both TREMOR-style (echelon.* nested) and CORONA-style
    (root-level) construct.json layouts.

    Raises ValueError on invalid JSON.
    """
```

Derived booleans:
- `has_brier_scoring`: True if any template has `brier_type` set, OR if `rlmf.exports` contains `"brier_score"`
- `has_cross_validation`: True if any source has `role == "cross_validation"`
- `oracle_names`: deduplicated set of oracle strings from all templates

---

### 2.3 New: `backend/services/theatre_check_planner.py`

**Sprint:** 2
**Purpose:** Generate 4 theatre-specific `PlannedCheck` types from a `TheatreConstructMeta`, and merge them with base checks.

Follows the exact pattern of `security_check_planner.py` (lines 1-154).

#### Theatre Check Types

4 new `check_type` values with anchor class mappings:

```python
THEATRE_CHECK_TYPES: dict[str, str] = {
    "SETTLEMENT_ACCURACY": "LIVE_EXTERNAL_EVIDENCE",
    "ORACLE_CONSISTENCY": "LIVE_EXTERNAL_EVIDENCE",
    "CALIBRATION_VALIDITY": "DETERMINISTIC_CHECK",
    "FUNCTIONAL_CORRECTNESS": "DETERMINISTIC_CHECK",
}
```

| check_type | What It Validates | Anchor Class | Critical |
|---|---|---|---|
| `SETTLEMENT_ACCURACY` | Binary/multi-class outcomes match oracle ground truth | LIVE_EXTERNAL_EVIDENCE | True |
| `ORACLE_CONSISTENCY` | Cross-source oracle agreement within tolerance | LIVE_EXTERNAL_EVIDENCE | True |
| `CALIBRATION_VALIDITY` | Brier scores, calibration buckets, ECE are arithmetically consistent | DETERMINISTIC_CHECK | False |
| `FUNCTIONAL_CORRECTNESS` | Theatre template logic produces correct state transitions | DETERMINISTIC_CHECK | False |

#### plan_theatre_checks()

```python
def plan_theatre_checks(
    spec_slug: str,
    meta: TheatreConstructMeta,
) -> list[PlannedCheck]:
    """Generate theatre-specific PlannedCheck entries from construct metadata.

    Args:
        spec_slug: Construct slug for check ID namespacing.
        meta: Parsed TheatreConstructMeta from construct.json.

    Returns:
        Sorted list of PlannedCheck entries compatible with
        check_planner.plan_checks() output format.
    """
```

Check generation rules:

1. **SETTLEMENT_ACCURACY** -- One check per theatre template. Each template has a resolution rule and an oracle reference.

```python
    checks: list[PlannedCheck] = []
    seen_ids: set[str] = set()

    # 1. SETTLEMENT_ACCURACY -- one per theatre template
    for template in meta.theatre_templates:
        check_id = f"theatre:settlement_accuracy:{template.id}"
        if check_id not in seen_ids:
            seen_ids.add(check_id)
            checks.append(PlannedCheck(
                check_id=check_id,
                check_type="SETTLEMENT_ACCURACY",
                domain=f"theatre:{template.id}",
                source=f"theatre_template:{template.id}:oracle:{template.oracle}",
                critical=True,
                anchor_class="LIVE_EXTERNAL_EVIDENCE",
            ))
```

2. **ORACLE_CONSISTENCY** -- One check per cross-validation OSINT source. Only generated when `meta.has_cross_validation` is True.

```python
    # 2. ORACLE_CONSISTENCY -- one per cross-validation source
    if meta.has_cross_validation:
        cross_val = [s for s in meta.osint_sources if s.role == "cross_validation"]
        for source in cross_val:
            check_id = f"theatre:oracle_consistency:{source.id}"
            if check_id not in seen_ids:
                seen_ids.add(check_id)
                checks.append(PlannedCheck(
                    check_id=check_id,
                    check_type="ORACLE_CONSISTENCY",
                    domain=f"oracle:{source.id}",
                    source=f"osint_source:{source.id}:role:cross_validation",
                    critical=True,
                    anchor_class="LIVE_EXTERNAL_EVIDENCE",
                ))
```

3. **CALIBRATION_VALIDITY** -- One check, generated when `meta.has_brier_scoring` is True.

```python
    # 3. CALIBRATION_VALIDITY -- single check if Brier scoring present
    if meta.has_brier_scoring:
        check_id = f"theatre:calibration_validity:{spec_slug}"
        if check_id not in seen_ids:
            seen_ids.add(check_id)
            checks.append(PlannedCheck(
                check_id=check_id,
                check_type="CALIBRATION_VALIDITY",
                domain=f"calibration:{spec_slug}",
                source=f"brier_scoring:{spec_slug}",
                critical=False,
                anchor_class="DETERMINISTIC_CHECK",
            ))
```

4. **FUNCTIONAL_CORRECTNESS** -- One check per theatre template.

```python
    # 4. FUNCTIONAL_CORRECTNESS -- one per theatre template
    for template in meta.theatre_templates:
        check_id = f"theatre:functional_correctness:{template.id}"
        if check_id not in seen_ids:
            seen_ids.add(check_id)
            checks.append(PlannedCheck(
                check_id=check_id,
                check_type="FUNCTIONAL_CORRECTNESS",
                domain=f"theatre:{template.id}",
                source=f"theatre_template:{template.id}:state_machine",
                critical=False,
                anchor_class="DETERMINISTIC_CHECK",
            ))

    # Sort for determinism: (check_type, domain, check_id)
    checks.sort(key=lambda c: (c.check_type, c.domain, c.check_id))
    return checks
```

**check_id format:** `theatre:{check_type_lower}:{entity_id}`

Examples from TREMOR fixture:

| check_id | check_type | domain | source |
|---|---|---|---|
| `theatre:settlement_accuracy:magnitude_gate` | SETTLEMENT_ACCURACY | `theatre:magnitude_gate` | `theatre_template:magnitude_gate:oracle:USGS reviewed catalog` |
| `theatre:settlement_accuracy:aftershock_cascade` | SETTLEMENT_ACCURACY | `theatre:aftershock_cascade` | `theatre_template:aftershock_cascade:oracle:USGS reviewed catalog` |
| `theatre:oracle_consistency:emsc` | ORACLE_CONSISTENCY | `oracle:emsc` | `osint_source:emsc:role:cross_validation` |
| `theatre:oracle_consistency:iris_dmc` | ORACLE_CONSISTENCY | `oracle:iris_dmc` | `osint_source:iris_dmc:role:cross_validation` |
| `theatre:calibration_validity:tremor` | CALIBRATION_VALIDITY | `calibration:tremor` | `brier_scoring:tremor` |
| `theatre:functional_correctness:magnitude_gate` | FUNCTIONAL_CORRECTNESS | `theatre:magnitude_gate` | `theatre_template:magnitude_gate:state_machine` |

**Expected check counts from fixtures:**

| Construct | SETTLEMENT_ACCURACY | ORACLE_CONSISTENCY | CALIBRATION_VALIDITY | FUNCTIONAL_CORRECTNESS | Total |
|---|---|---|---|---|---|
| TREMOR | 5 (5 templates) | 2 (EMSC + IRIS) | 1 (Brier scoring) | 5 (5 templates) | 13 |
| CORONA | 5 (5 templates) | 2 (DONKI + GFZ) | 1 (RLMF Brier) | 5 (5 templates) | 13 |

#### merge_theatre_checks()

Identical pattern to `security_check_planner.merge_security_checks()` (lines 125-154):

```python
def merge_theatre_checks(
    base_checks: list[PlannedCheck],
    theatre_checks: list[PlannedCheck],
) -> list[PlannedCheck]:
    """Merge base 037 checks with theatre-specific checks.

    Deduplicates by check_id. Preserves sort order: (check_type, domain, check_id).

    Args:
        base_checks: Output from check_planner.plan_checks() (possibly
            already merged with security checks).
        theatre_checks: Output from plan_theatre_checks().

    Returns:
        Merged, deduplicated, sorted list of PlannedCheck entries.
    """
    seen: set[str] = set()
    merged: list[PlannedCheck] = []

    for check in base_checks:
        if check.check_id not in seen:
            seen.add(check.check_id)
            merged.append(check)

    for check in theatre_checks:
        if check.check_id not in seen:
            seen.add(check.check_id)
            merged.append(check)

    merged.sort(key=lambda c: (c.check_type, c.domain, c.check_id))
    return merged
```

---

### 2.4 Modified: `backend/services/contract_service.py`

**Sprint:** 2
**Purpose:** Add `construct_json` parameter and wire theatre check planning.

**New imports** (after existing imports at line 31):

```python
from backend.services.theatre_policy_rules import parse_construct_json
from backend.services.theatre_check_planner import (
    plan_theatre_checks,
    merge_theatre_checks,
)
# Side-effect: importing theatre_policy_rules registers 10 precise theatre
# domains into KNOWN_PRECISE_DOMAINS at import time (cycle 037d).
```

**Signature change** to `create_contract()` (lines 44-50). Add `construct_json` parameter:

```python
    async def create_contract(
        self,
        registration_id: str,
        yaml_content: str,
        available_assets: Optional[dict] = None,
        corpus_skills: Optional[list[CorpusSkill]] = None,
        construct_json: Optional[str] = None,
    ) -> EvaluationContract:
```

Docstring addition for `construct_json`:

```
            construct_json: Optional raw JSON string from theatre construct.json.
                When provided and construct_class is "theatre", theatre-specific
                checks (SETTLEMENT_ACCURACY, ORACLE_CONSISTENCY, etc.) are
                merged into the contract.
```

**New merge step** -- inserted after the security check merge block (after line 95), before `planned_dicts = checks_to_dicts(planned)` (line 97):

```python
        # 4c. Merge theatre-specific checks if construct_json provided
        #     and construct_class is "theatre"
        if construct_json and spec.construct_class == "theatre":
            try:
                theatre_meta = parse_construct_json(construct_json)
                theatre_checks = plan_theatre_checks(spec.slug, theatre_meta)
                planned = merge_theatre_checks(planned, theatre_checks)
            except ValueError as e:
                logger.warning(
                    "Failed to parse construct.json for %s: %s",
                    spec.slug, e,
                )
```

The guard `spec.construct_class == "theatre"` ensures that passing `construct_json` for a skill construct does nothing. The `try/except` ensures malformed construct.json does not crash the pipeline -- it logs and continues with base checks only.

---

### 2.5 Modified: `backend/schemas/construct_schemas.py`

**Sprint:** 2
**Purpose:** Add `construct_json` field to `CreateContractRequest`.

Current `CreateContractRequest` (lines 136-143):

```python
class CreateContractRequest(BaseModel):
    """POST .../contract request body."""
    yaml_content: str = Field(..., description="Raw construct.yaml content")
    corpus_contents: Optional[list[str]] = Field(
        None,
        description="Raw corpus file contents (frontmatter + markdown). "
        "Parsed into CorpusSkills for security check planning.",
    )
```

Add after `corpus_contents`:

```python
    construct_json: Optional[str] = Field(
        None,
        description="Raw construct.json content from theatre constructs. "
        "Parsed for theatre check planning when construct_class is 'theatre'.",
    )
```

---

### 2.6 Modified: `backend/api/construct_routes.py`

**Sprint:** 2
**Purpose:** Pass `construct_json` from request body through to `contract_service.create_contract()`.

Current code in `create_contract` route handler (lines 215-220):

```python
        contract = await contract_svc.create_contract(
            registration_id=reg.id,
            yaml_content=body.yaml_content,
            corpus_skills=corpus_skills,
        )
```

New code:

```python
        contract = await contract_svc.create_contract(
            registration_id=reg.id,
            yaml_content=body.yaml_content,
            corpus_skills=corpus_skills,
            construct_json=body.construct_json,
        )
```

This is a single keyword addition. No other route changes needed -- the response schema already handles arbitrary `check_type` strings via `PlannedCheckSchema.check_type: str` (line 163).

---

### 2.7 Modified: `backend/services/construct_anchor_mapper.py`

**Sprint:** 2
**Purpose:** Add 4 theatre-specific mapping rules to `_MAPPING_RULES` list.

New rules appended after the existing Cycle-037c block (after line 119):

```python
    # -- Cycle-037d: Theatre Construct Verification Anchors ----------------
    # Settlement / oracle ground truth -> live_external_evidence
    (
        ["settlement", "oracle", "ground_truth", "settlement_accuracy"],
        AnchorClass.LIVE_EXTERNAL_EVIDENCE,
        "theatre_oracle_settlement",
        "Verification against external oracle ground truth for theatre settlement",
    ),
    # Calibration / Brier scoring -> deterministic_check
    (
        ["brier", "calibration", "ece", "calibration_validity"],
        AnchorClass.DETERMINISTIC_CHECK,
        "theatre_calibration",
        "Deterministic verification of Brier score and calibration bucket arithmetic",
    ),
    # Position history / temporal analysis -> deterministic_check
    (
        ["position_history", "temporal_analysis", "functional_correctness"],
        AnchorClass.DETERMINISTIC_CHECK,
        "theatre_state_machine",
        "Deterministic verification of theatre template state transitions and position history",
    ),
    # Named oracle keywords -> live_external_evidence
    (
        ["usgs", "emsc", "swpc", "donki", "noaa", "iris_dmc", "gfz"],
        AnchorClass.LIVE_EXTERNAL_EVIDENCE,
        "theatre_named_oracle",
        "Grounded in named public OSINT oracle feeds (USGS, EMSC, NOAA SWPC, NASA DONKI)",
    ),
```

These 4 rules add 4 new anchor IDs: `theatre_oracle_settlement`, `theatre_calibration`, `theatre_state_machine`, `theatre_named_oracle`.

No API change. `map_dimension_anchors()` and `map_contract_anchors()` are unchanged -- they iterate `_MAPPING_RULES` dynamically.

---

## 3. Data Models

### 3.1 ConstructSpec Changes

| Field | Type | Default | Notes |
|---|---|---|---|
| `construct_class` | `str` | `"skill"` | New optional field. Valid values: `"skill"`, `"theatre"`, `"bridge"`. Unrecognized values default to `"skill"`. |

No database migration required. `construct_class` is parsed from YAML at load time and lives on the in-memory `ConstructSpec` dataclass. It does not need a new column because it is derivable from the raw YAML content already stored in the contract pipeline.

### 3.2 Theatre PlannedCheck Types

All theatre check types use the existing `PlannedCheck` dataclass (from `check_planner.py` lines 23-31) without modification. The `check_type` field is a free string.

| check_type | anchor_class | critical | Cardinality |
|---|---|---|---|
| `SETTLEMENT_ACCURACY` | `LIVE_EXTERNAL_EVIDENCE` | True | 1 per theatre template |
| `ORACLE_CONSISTENCY` | `LIVE_EXTERNAL_EVIDENCE` | True | 1 per cross-validation source |
| `CALIBRATION_VALIDITY` | `DETERMINISTIC_CHECK` | False | 1 total (if Brier scoring) |
| `FUNCTIONAL_CORRECTNESS` | `DETERMINISTIC_CHECK` | False | 1 per theatre template |

### 3.3 TheatreConstructMeta

Transient data structure parsed from `construct.json`. Not stored in DB.

```
TheatreConstructMeta
    name: str
    theatre_templates: list[TheatreTemplate]
    osint_sources: list[OsintSource]
    verification_checks: list[VerificationCheck]
    settlement_tiers: list[dict]
    has_brier_scoring: bool
    has_cross_validation: bool
    oracle_names: list[str]
```

### 3.4 CreateContractRequest Changes

| Field | Type | Notes |
|---|---|---|
| `construct_json` | `Optional[str]` | New optional field. Raw JSON string from theatre construct.json. |

---

## 4. Integration Flow

Step-by-step contract creation with theatre checks:

### 4.1 API Request

```
POST /api/constructs/tremor/0.1.0/contract
{
    "yaml_content": "<construct.yaml with construct_class: theatre>",
    "construct_json": "<raw JSON from tremor/spec/construct.json>"
}
```

### 4.2 Route Handler (`construct_routes.py`)

1. Resolve registration for `tremor:0.1.0`
2. Parse `corpus_contents` (if any) into `CorpusSkill` objects
3. Call `contract_svc.create_contract(registration_id, yaml_content, corpus_skills, construct_json=body.construct_json)`

### 4.3 ContractService Pipeline

1. **Parse** -- `spec_loader.load(yaml_content)` returns `ConstructSpec` with `construct_class="theatre"`
2. **Idempotency check** -- compare `spec.spec_hash` against ACTIVE contract
3. **Normalize** -- `policy_normalizer.normalize(spec)` classifies domain claims. Theatre domains (e.g., `seismic_intelligence`, `settlement_verification`) now resolve as precise because `theatre_policy_rules.py` registered them at import time.
4. **Base checks** -- `check_planner.plan_checks(spec.slug, norm_result)` produces standard RUBRIC + BENCHMARK + ANCHOR checks
5. **Security checks** -- if `corpus_skills` provided, merge security checks (unchanged from 037c)
6. **Theatre checks** -- if `construct_json` provided AND `spec.construct_class == "theatre"`:
   a. `parse_construct_json(construct_json)` extracts `TheatreConstructMeta`
   b. `plan_theatre_checks(spec.slug, meta)` generates theatre-specific `PlannedCheck` entries
   c. `merge_theatre_checks(planned, theatre_checks)` merges, deduplicates, sorts
7. **Hash** -- `compute_contract_hash(spec_hash, planned)` -- the contract hash now includes theatre checks
8. **Persist** -- store as `EvaluationContract`

### 4.4 Result

For TREMOR with 5 theatre templates, 2 cross-validation sources, and Brier scoring, the `planned_checks` array contains:

- Base checks: 2 ANCHOR checks (PUBLIC_STANDARD, DETERMINISTIC_CHECK) + N RUBRIC checks
- Theatre checks: 5 SETTLEMENT_ACCURACY + 2 ORACLE_CONSISTENCY + 1 CALIBRATION_VALIDITY + 5 FUNCTIONAL_CORRECTNESS = 13 theatre checks

All sorted by `(check_type, domain, check_id)`.

---

## 5. Construct JSON Schema

### 5.1 Fields Read by Theatre Check Planner

| Field Path (TREMOR) | Field Path (CORONA) | Type | Used For |
|---|---|---|---|
| `name` | `slug` or `name` | string | Construct identification |
| `echelon.theatre_templates` | `theatre_templates` | array | SETTLEMENT_ACCURACY + FUNCTIONAL_CORRECTNESS checks |
| `echelon.theatre_templates[].id` | `theatre_templates[].id` | string | Check ID namespacing |
| `echelon.theatre_templates[].name` | `theatre_templates[].name` | string | Template identification |
| `echelon.theatre_templates[].resolution` | `theatre_templates[].type` | string | Resolution type (binary/multi) |
| `echelon.theatre_templates[].oracle` | `theatre_templates[].resolution` | string | Oracle reference |
| `echelon.theatre_templates[].brier_type` | (absent) | string | Brier scoring type |
| `echelon.osint_sources` | `data_sources` | array | ORACLE_CONSISTENCY checks |
| `echelon.osint_sources[].id` | (derived from name) | string | Source ID |
| `echelon.osint_sources[].role` | (absent, defaults primary) | string | primary vs cross_validation |
| `echelon.verification_checks` | (absent) | array | Declared checks (informational) |
| `echelon.settlement_tiers` | (absent) | array | Settlement tier metadata |
| (absent) | `rlmf.exports` | array | Brier scoring detection fallback |

### 5.2 CORONA Cross-Validation Source Detection

CORONA's `data_sources` do not have a `role` field. Cross-validation is detected by:

1. If a source has an explicit `role` field, use it
2. Otherwise, the first source defaults to `"primary"` and subsequent sources default to `"primary"` as well

To generate ORACLE_CONSISTENCY checks for CORONA, the construct.yaml (not construct.json) should declare cross-validation intent. Alternatively, the parser can infer cross-validation from the presence of multiple independent data sources. The implementation should default to treating all sources without a `role` field as `"primary"` -- the operator can add `role: "cross_validation"` to their construct.json to opt in to ORACLE_CONSISTENCY checks.

**Update:** For CORONA specifically, `data_sources[1]` (NASA DONKI) and `data_sources[2]` (GFZ Potsdam) are clearly cross-validation sources for the primary NOAA SWPC feed. The parser should check for a `role` field first, and if absent, treat sources beyond the first as `"cross_validation"` when there are 2+ sources.

### 5.3 Minimum Viable construct.json

```json
{
    "name": "my-theatre",
    "theatre_templates": [
        {
            "id": "template_1",
            "name": "My Template",
            "resolution": "binary",
            "oracle": "Some Oracle"
        }
    ]
}
```

This produces: 1 SETTLEMENT_ACCURACY + 1 FUNCTIONAL_CORRECTNESS = 2 checks. No ORACLE_CONSISTENCY (no cross-validation sources) and no CALIBRATION_VALIDITY (no Brier scoring declared).

---

## 6. Risks and Mitigations

### 6.1 Construct JSON Format Divergence

**Risk:** Future theatre constructs may use different JSON layouts than TREMOR/CORONA.

**Mitigation:** The parser uses fallback chains (`echelon.theatre_templates` or root `theatre_templates`; `echelon.osint_sources` or `data_sources`). Unknown keys are ignored. The `parse_construct_json` function is the single point of adaptation -- adding a new construct layout requires only extending the fallback logic in this one function.

### 6.2 construct_class Misuse

**Risk:** A skill construct sets `construct_class: theatre` to get theatre checks.

**Mitigation:** Theatre checks are only generated when both conditions are true: `construct_class == "theatre"` AND `construct_json` is provided with valid theatre templates. A skill construct claiming to be a theatre but providing no construct.json (or one without `theatre_templates`) gets zero theatre checks.

### 6.3 Import-Time Side Effects

**Risk:** Importing `theatre_policy_rules.py` mutates `KNOWN_PRECISE_DOMAINS`.

**Mitigation:** This is an established pattern (see `security_policy_rules.py` line 118). The import happens in `contract_service.py` which is always loaded before any normalization runs. The domains are additive and never remove existing domains. Tests that validate normalization behavior should snapshot and restore `KNOWN_PRECISE_DOMAINS` in setUp/tearDown.

### 6.4 Large construct.json

**Risk:** A theatre construct ships a very large construct.json (many templates, many sources).

**Mitigation:** Check generation is O(templates + sources) which is bounded by practical theatre design. TREMOR has 5 templates and 3 sources. Even a construct with 100 templates would only produce ~200 checks, well within reasonable bounds. The `seen_ids` dedup set prevents duplicates.

### 6.5 Hash Stability

**Risk:** Adding theatre checks changes the contract hash for theatre constructs.

**Mitigation:** This is correct behavior. A theatre contract with theatre checks is a different contract than one without. The supersession logic in `contract_service.py` handles this: if the check plan changes, a new contract is created and the old one is superseded. Skill constructs are not affected because they never receive theatre checks.

### 6.6 Malformed construct.json

**Risk:** A theatre construct provides invalid JSON in `construct_json`.

**Mitigation:** The `parse_construct_json` call is wrapped in `try/except ValueError` in `contract_service.py`. On failure, it logs a warning and continues with base checks only. The contract is still created -- it just lacks theatre-specific checks.

---

## 7. Files Touched Summary

### New Files

| File | Lines (est.) | Purpose |
|---|---|---|
| `backend/services/theatre_check_planner.py` | ~120 | Theatre-specific check planning + merge |
| `backend/services/theatre_policy_rules.py` | ~160 | Domain registration + construct.json parsing |
| `backend/tests/test_theatre_check_planner.py` | ~200 | Theatre planner unit tests |
| `backend/tests/test_theatre_policy_rules.py` | ~180 | Domain registration + parsing tests |
| `backend/tests/test_theatre_integration.py` | ~150 | Integration tests with TREMOR/CORONA fixtures, regression |

### Modified Files

| File | Change | Lines Changed (est.) |
|---|---|---|
| `backend/services/spec_loader.py` | Add `construct_class` field to `ConstructSpec` + parsing in `load()` | ~8 |
| `backend/services/contract_service.py` | Add `construct_json` param + imports + theatre merge block | ~15 |
| `backend/schemas/construct_schemas.py` | Add `construct_json` to `CreateContractRequest` | ~4 |
| `backend/api/construct_routes.py` | Pass `construct_json` kwarg to `create_contract` | ~1 |
| `backend/services/construct_anchor_mapper.py` | Append 4 theatre mapping rules to `_MAPPING_RULES` | ~24 |

### Explicitly NOT Modified

| File | Reason |
|---|---|
| `backend/services/check_planner.py` | Base planner unchanged -- theatre checks merged caller-side |
| `backend/services/policy_normalizer.py` | Core logic unchanged -- theatre domains registered via side-effect import |
| `backend/services/security_check_planner.py` | Security planner unchanged |
| `backend/services/security_policy_rules.py` | Security rules unchanged |
| `backend/services/domain_pack_loader.py` | Corpus loader unchanged |
| `backend/schemas/construct_anchor_schema.py` | AnchorClass enum unchanged -- all theatre anchors use existing values (LIVE_EXTERNAL_EVIDENCE, DETERMINISTIC_CHECK) |
| Any Alembic migration | No new columns or tables needed |

---

## 8. Sprint Mapping

| Sprint | Scope | New/Changed Files |
|---|---|---|
| Sprint 0 | ConstructSpec `construct_class` field + parsing | `spec_loader.py`, `test_spec_loader_construct_class.py` |
| Sprint 1 | Theatre policy rules + domain registration + construct.json parser | `theatre_policy_rules.py`, `test_theatre_policy_rules.py` |
| Sprint 2 | Theatre check planner + anchor mapper + contract service wiring + API passthrough | `theatre_check_planner.py`, `construct_anchor_mapper.py`, `contract_service.py`, `construct_schemas.py`, `construct_routes.py`, `test_theatre_check_planner.py` |
| Sprint 3 | Integration tests + TREMOR/CORONA fixtures + regression | `test_theatre_integration.py` |

---

## 9. After This Cycle Ships

1. Theatre constructs become first-class citizens in the contract system via `construct_class: theatre`
2. Echelon can issue a higher-credibility certificate class for deterministic, externally anchored theatre operators
3. 10 theatre-specific precise domains pass policy normalization without tier-capping
4. 4 theatre-specific anchor mapping rules resolve theatre dimensions to LIVE_EXTERNAL_EVIDENCE and DETERMINISTIC_CHECK
5. The system is ready for cross-theatre paradox detection in Cycle 038
