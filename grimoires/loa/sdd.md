# SDD — Cycle-037c: Security + Domain Pack Verification

**Cycle:** cycle-037c
**Date:** 19 March 2026
**Depends on:** Cycle-037 (contract substrate), Cycle-037b (multi-evaluator orchestration), Cycles 026a–026c (anchor packs)
**Builder:** Loa (backend only)

> Sources: context_037c.md, prd_037c.md, sdd_037c.md, codebase validation

---

## 1. Architecture Summary

Cycle 037c adds a domain-pack layer on top of the existing contract substrate:

```
frontmatter-aware corpus (YAML frontmatter + Markdown body)
    ↓
domain_pack_loader.py  ← NEW (Sprint 0)
    ↓
security_policy_rules.py  ← NEW (Sprint 1)
    ↓
security_check_planner.py  ← NEW (Sprint 2)
    ↓
construct_anchor_mapper.py  ← EXTENDED (Sprint 2)
    ↓
037 contract substrate (unchanged)
    ↓
037b residual judging (unchanged)
```

This cycle is strictly additive. No existing 037/037b service is redesigned.

---

## 2. File-Level Design

### 2.1 New Service: `backend/services/domain_pack_loader.py`

**Sprint:** 0
**Purpose:** Generic frontmatter-aware corpus ingestion. Handles YAML frontmatter extraction and Markdown body parsing, exposing normalized metadata for downstream consumers.

**Why new file:** `spec_loader.py` (76 lines) expects pure YAML via `yaml.safe_load()`. It has no frontmatter awareness. The domain pack loader handles frontmatter stripping before delegating to `spec_loader.load()` where applicable, and also provides standalone corpus parsing for non-construct sources.

#### Data Model

```python
@dataclass(frozen=True)
class CorpusSkill:
    """A single skill parsed from a frontmatter-aware corpus file."""
    name: str
    description: str
    domain: str
    references: list[str]         # Framework IDs: ATT&CK T-codes, CWE-IDs, OWASP refs
    verification_steps: list[str] # Testable assertions from verification section
    workflow_body: str            # Raw Markdown body (post-frontmatter)
    raw_frontmatter: dict         # Original parsed YAML frontmatter


@dataclass(frozen=True)
class DomainPack:
    """Collection of corpus skills forming a domain pack."""
    pack_id: str
    domain: str
    skills: list[CorpusSkill]
    version: str
```

#### Key Functions

```python
def extract_frontmatter(content: str) -> tuple[dict, str]:
    """Split YAML frontmatter from Markdown body.

    Expects content starting with '---' delimiter.
    Returns (frontmatter_dict, markdown_body).
    Raises ValueError if frontmatter delimiter is missing or YAML is invalid.
    """

def parse_references(body: str) -> list[str]:
    """Extract framework references from Markdown body.

    Scans for a '## References' or '## references' section.
    Returns list of extracted reference strings (ATT&CK IDs, CWE IDs, etc.).
    """

def parse_verification(body: str) -> list[str]:
    """Extract testable assertions from Markdown verification section.

    Scans for a '## Verification' section.
    Returns list of verification step strings.
    """

def load_corpus_skill(content: str) -> CorpusSkill:
    """Parse a single frontmatter-aware corpus file into a CorpusSkill."""

def load_domain_pack(pack_id: str, domain: str, files: list[str]) -> DomainPack:
    """Load multiple corpus files into a DomainPack."""
```

#### Design Decisions

- **Generic, not security-specific.** The loader handles any frontmatter-aware corpus. Security specifics live in `security_policy_rules.py`.
- **No filesystem I/O.** Functions accept string content, not file paths. Callers handle I/O.
- **Frontmatter delimiter:** Standard `---` YAML frontmatter as used by Jekyll, Hugo, and the Anthropic cybersecurity skills corpus.

---

### 2.2 New Service: `backend/services/security_policy_rules.py`

**Sprint:** 1
**Purpose:** Extend policy normalization with security-specific precise domains. Maps framework references (ATT&CK, CWE, OWASP) to anchored claims.

**Why new file:** `policy_normalizer.py` (130 lines) has `KNOWN_PRECISE_DOMAINS` as a mutable `set[str]` at module level (line 16). Adding 10 security domains directly would mix domain-pack concerns into the general normalizer. Instead, a separate file registers security domains at import time using set mutation.

#### Precise Security Domains

10 specific security domains to be added to `KNOWN_PRECISE_DOMAINS`:

```python
SECURITY_PRECISE_DOMAINS: set[str] = {
    "vulnerability_analysis",
    "attack_surface_mapping",
    "threat_modeling",
    "secure_code_review",
    "incident_response",
    "cryptographic_implementation",
    "access_control_design",
    "network_security",
    "penetration_testing",
    "compliance_auditing",
}
```

#### Registration Pattern

```python
from backend.services.policy_normalizer import KNOWN_PRECISE_DOMAINS

def register_security_domains() -> int:
    """Register security-specific precise domains with the policy normalizer.

    Mutates policy_normalizer.KNOWN_PRECISE_DOMAINS by adding security domains.
    Returns count of newly added domains (for logging/testing).

    This preserves the guardrail: broad "security" remains in KNOWN_VAGUE_TERMS
    and continues to tier-cap claims. Only specific security sub-domains pass.
    """
    before = len(KNOWN_PRECISE_DOMAINS)
    KNOWN_PRECISE_DOMAINS.update(SECURITY_PRECISE_DOMAINS)
    return len(KNOWN_PRECISE_DOMAINS) - before
```

#### Framework Reference Extraction

```python
def extract_security_references(corpus_skill: CorpusSkill) -> list[dict]:
    """Extract ATT&CK, CWE, and OWASP references from a CorpusSkill.

    Scans references list for patterns:
    - ATT&CK: T[0-9]{4}(\\.[0-9]{3})?
    - CWE: CWE-[0-9]+
    - OWASP: A[0-9]{2}:[0-9]{4} (OWASP Top 10 format)

    Returns list of dicts with keys: framework, id, raw_reference.
    """

def classify_security_claim(domain: str, references: list[dict]) -> dict:
    """Classify a security domain claim with reference backing.

    A security claim with valid framework references is promoted to precise.
    A security claim without references remains vague.
    """
```

#### Design Decisions

- **Import-time mutation.** `register_security_domains()` is called once at import time. This matches how Python module-level sets are conventionally extended. The normalizer's `_classify_claim()` at line 71 already reads from `KNOWN_PRECISE_DOMAINS` at call time, so mutations are visible immediately.
- **Broad "security" stays vague.** The word "security" remains in `KNOWN_VAGUE_TERMS` (line 39). Only the 10 specific sub-domains pass the precise check. A claim like "security expert" still gets tier-capped to UNVERIFIED.
- **No normalizer code changes.** The normalizer is not modified. Security rules only add to its allowlist.

---

### 2.3 New Service: `backend/services/security_check_planner.py`

**Sprint:** 2
**Purpose:** Generate security-specific deterministic check types that extend the 037 contract model.

**Why new file:** `check_planner.py` (136 lines) has `plan_checks()` that generates RUBRIC, BENCHMARK, and ANCHOR checks. The `PlannedCheck.check_type` field is a free string (line 26), so new check types need no schema change. However, security check planning involves domain-specific logic (reference validation, tool syntax matching) that should not live in the general planner.

#### Security Check Types

5 new `check_type` values with anchor class mappings:

```python
SECURITY_CHECK_TYPES: dict[str, str] = {
    "ATTACK_TECHNIQUE_MAPPING": "PUBLIC_STANDARD",
    "TOOL_INVOCATION_CORRECTNESS": "DETERMINISTIC_CHECK",
    "STANDARDS_COMPLIANCE": "PUBLIC_STANDARD",
    "DEPENDENCY_VULNERABILITY_CHECK": "DETERMINISTIC_CHECK",
    "SECRET_LEAK_CHECK": "DETERMINISTIC_CHECK",
}
```

| check_type | What It Validates | Anchor Class |
|---|---|---|
| `ATTACK_TECHNIQUE_MAPPING` | Claims map to valid ATT&CK technique IDs | PUBLIC_STANDARD |
| `TOOL_INVOCATION_CORRECTNESS` | Security tool usage matches documented syntax | DETERMINISTIC_CHECK |
| `STANDARDS_COMPLIANCE` | Claims reference valid OWASP/CWE/NIST entries | PUBLIC_STANDARD |
| `DEPENDENCY_VULNERABILITY_CHECK` | Dependency scanning claims are verifiable | DETERMINISTIC_CHECK |
| `SECRET_LEAK_CHECK` | Secret detection claims are testable | DETERMINISTIC_CHECK |

#### Key Functions

```python
def plan_security_checks(
    corpus_skill: CorpusSkill,
    references: list[dict],
) -> list[PlannedCheck]:
    """Generate security-specific PlannedCheck entries from a CorpusSkill.

    Maps extracted framework references to appropriate check types.
    Uses SECURITY_CHECK_TYPES for anchor class resolution.

    Returns sorted list of PlannedCheck entries compatible with
    check_planner.plan_checks() output format.
    """

def merge_security_checks(
    base_checks: list[PlannedCheck],
    security_checks: list[PlannedCheck],
) -> list[PlannedCheck]:
    """Merge base 037 checks with security-specific checks.

    Deduplicates by check_id. Preserves sort order: (check_type, domain, check_id).
    """
```

#### Integration Strategy

The caller merges security checks with base checks. `check_planner.plan_checks()` is **not modified**:

```python
# In the certification endpoint or integration layer:
base_checks = check_planner.plan_checks(slug, normalization_result, assets)
security_checks = security_check_planner.plan_security_checks(skill, refs)
all_checks = security_check_planner.merge_security_checks(base_checks, security_checks)
```

This keeps the 037 planner general and makes 037c additive.

---

### 2.4 Existing Service Extension: `backend/services/construct_anchor_mapper.py`

**Sprint:** 2
**Purpose:** Add 2 security-specific mapping rules to `_MAPPING_RULES` (currently 11 entries, lines 25–105).

#### New Rules

```python
# ATT&CK technique framework → PUBLIC_STANDARD
(
    ["attack", "att_ck", "mitre", "technique", "tactic", "t1059", "t1566"],
    AnchorClass.PUBLIC_STANDARD,
    "attack_framework",
    "Verification against MITRE ATT&CK technique and tactic taxonomy",
),
# Security skill corpus → PUBLIC_STANDARD
(
    ["security_skill", "skill_corpus", "cybersecurity_skill", "workflow_verification"],
    AnchorClass.PUBLIC_STANDARD,
    "security_skill_corpus",
    "Verification against structured cybersecurity skill corpus with workflow verification",
),
```

#### Design Decisions

- **Append-only.** New rules are appended to `_MAPPING_RULES`. Existing rule at line 63–68 (`security_standards`) already covers OWASP/CWE. The new `attack_framework` rule handles ATT&CK specifically.
- **No API change.** `map_dimension_anchors()` and `map_contract_anchors()` are unchanged. They iterate `_MAPPING_RULES` dynamically.
- **Existing security rule preserved.** The rule at line 63–68 with `anchor_id: security_standards` and keywords `["security", "vulnerability", "owasp", "cwe", ...]` stays. The two new rules add ATT&CK and corpus-specific anchoring.

---

## 3. Integration Points

> Corrected from pre-staged SDD using codebase validation.

| Service | Actual File | Lines | Integration |
|---|---|---|---|
| Spec loader | `backend/services/spec_loader.py` | 76 | Domain pack loader wraps this for frontmatter stripping |
| Policy normalizer | `backend/services/policy_normalizer.py` | 130 | Security rules mutate `KNOWN_PRECISE_DOMAINS` at import time |
| Check planner | `backend/services/check_planner.py` | 136 | Security check planner produces checks in same `PlannedCheck` format, merged by caller |
| Anchor mapper | `backend/services/construct_anchor_mapper.py` | 173 | 2 new rules appended to `_MAPPING_RULES` |
| Rubric registry | `backend/data/construct_rubrics/__init__.py` | — | Future: security rubric scorers (not this cycle) |

---

## 4. Test Plan

### 4.1 `backend/tests/test_domain_pack_loader.py` (5 tests)

| Test | What It Validates |
|---|---|
| `test_extract_frontmatter_valid` | Parses valid YAML frontmatter + Markdown body |
| `test_extract_frontmatter_missing_delimiter` | Raises ValueError on missing `---` |
| `test_parse_references_section` | Extracts ATT&CK/CWE/OWASP IDs from References section |
| `test_parse_verification_section` | Extracts testable assertions from Verification section |
| `test_load_corpus_skill_integration` | Full parse of frontmatter + references + verification |

### 4.2 `backend/tests/test_security_policy_rules.py` (5 tests)

| Test | What It Validates |
|---|---|
| `test_register_security_domains` | All 10 domains added to `KNOWN_PRECISE_DOMAINS` |
| `test_precise_security_domains_pass_normalization` | `vulnerability_analysis` etc. are not tier-capped |
| `test_broad_security_stays_vague` | `"security"` claim still tier-caps to UNVERIFIED |
| `test_extract_attack_references` | ATT&CK T-codes extracted from reference list |
| `test_extract_owasp_cwe_references` | OWASP/CWE IDs extracted and classified |

### 4.3 `backend/tests/test_security_check_planner.py` (5 tests)

| Test | What It Validates |
|---|---|
| `test_plan_attack_technique_check` | ATT&CK reference → ATTACK_TECHNIQUE_MAPPING check |
| `test_plan_tool_invocation_check` | Tool usage claim → TOOL_INVOCATION_CORRECTNESS check |
| `test_plan_standards_compliance_check` | OWASP/CWE reference → STANDARDS_COMPLIANCE check |
| `test_plan_dependency_vulnerability_check` | Dependency claim → DEPENDENCY_VULNERABILITY_CHECK |
| `test_merge_security_checks_deduplication` | Merged checks are deduplicated and sorted |

### 4.4 `backend/tests/test_security_anchor_mapping.py` (3 tests)

| Test | What It Validates |
|---|---|
| `test_attack_framework_anchor` | ATT&CK dimension → PUBLIC_STANDARD with `attack_framework` |
| `test_security_skill_corpus_anchor` | Corpus skill dimension → PUBLIC_STANDARD with `security_skill_corpus` |
| `test_missing_anchor_weakly_anchored` | Unrecognized security claim → `weakly_anchored=True` |

### 4.5 `backend/tests/test_037c_regression.py` (4 tests)

| Test | What It Validates |
|---|---|
| `test_base_plan_checks_unchanged` | `plan_checks()` output unchanged for non-security claims |
| `test_base_normalization_unchanged` | `normalize()` output unchanged for non-security specs |
| `test_existing_anchor_rules_preserved` | All 11 original `_MAPPING_RULES` entries still present |
| `test_security_corpus_to_contract_integration` | Full path: corpus → domain pack → policy → checks → anchors |

**Total: ~22 tests**

---

## 5. Sprint Mapping

| Sprint | Scope | New/Changed Files |
|---|---|---|
| Sprint 0 | Domain pack loader + corpus parsing | `domain_pack_loader.py`, `test_domain_pack_loader.py` |
| Sprint 1 | Security policy rules + domain registration | `security_policy_rules.py`, `test_security_policy_rules.py` |
| Sprint 2 | Security check planner + anchor mapper extension | `security_check_planner.py`, `construct_anchor_mapper.py`, `test_security_check_planner.py`, `test_security_anchor_mapping.py` |
| Sprint 3 | Integration test + regression | `test_037c_regression.py` |

---

## 6. Risks and Mitigations

### 6.1 Import-Time Set Mutation

`register_security_domains()` mutates `KNOWN_PRECISE_DOMAINS` at import time. If security rules are imported before the normalizer, or if tests import in wrong order, state leaks between tests.

**Mitigation:** Each test that validates normalization behavior should snapshot and restore `KNOWN_PRECISE_DOMAINS` in setUp/tearDown. The registration function returns a count for verification.

### 6.2 Overfitting to One Corpus Format

The domain pack loader targets a specific frontmatter format.

**Mitigation:** The loader is generic (any YAML frontmatter + Markdown). Security-specific interpretation lives in `security_policy_rules.py`. Future domain packs use the same loader with different rule files.

### 6.3 Check Type Inflation

5 new check types could dilute the contract model.

**Mitigation:** Each check type maps to a real executable or standards-backed meaning. No speculative types. `PlannedCheck.check_type` is already a free string field, so no schema pressure.

### 6.4 Keyword Collision in Anchor Rules

New ATT&CK keywords (`"attack"`, `"technique"`) might match non-security dimensions.

**Mitigation:** Keywords are intentionally specific (`"att_ck"`, `"mitre"`, `"t1059"`, `"t1566"`). The generic `"attack"` keyword is acceptable because dimensions containing "attack" are almost certainly security-related in the Echelon context.

---

## 7. What This Cycle Does NOT Do

- **Does NOT modify `spec_loader.py`.** The domain pack loader wraps it; the original stays pure YAML.
- **Does NOT modify `policy_normalizer.py`.** Security rules mutate its allowlist externally.
- **Does NOT modify `check_planner.py`.** Security checks are merged by the caller.
- **Does NOT modify `evaluator_integration.py` or any 037b service.** Additive only.
- **Does NOT create API endpoints.** Service-layer only.
- **Does NOT build security rubric scorers.** That's a future cycle.

---

## 8. After This Cycle Ships

1. Echelon can ingest frontmatter-aware corpora as domain-pack sources
2. Security constructs gain meaningful deterministic planning and anchored claims
3. Precise security sub-domains pass policy normalization without tier-capping
4. The pattern is established for future domain packs (compliance, research, etc.)
