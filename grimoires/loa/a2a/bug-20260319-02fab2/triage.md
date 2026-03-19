# Bug Triage: 037c security domains not registered in production

## Bug ID: 20260319-02fab2
## Severity: P1 (domain misclassification) + P2 (security checks unreachable)
## Status: TRIAGED

## Summary

Cycle 037c introduced `security_policy_rules.py` which registers 10 precise security sub-domains (e.g., `vulnerability_analysis`, `threat_modeling`, `penetration_testing`) into `KNOWN_PRECISE_DOMAINS` at import time (line 118). However, no production module ever imports `security_policy_rules`, so `register_security_domains()` never executes in the live contract creation path. Consequently, `normalize()` classifies these domains as `is_vague: True` with `vagueness_reason: "unrecognized_domain"`, tier-capping contracts to UNVERIFIED. Additionally, `plan_security_checks()` and `merge_security_checks()` from `security_check_planner.py` have no production callers -- only test code composes them with `plan_checks()`.

## Root Cause

Two integration gaps in cycle 037c:

**P1 -- Domain Registration Never Fires in Production:**
- `security_policy_rules.py:118` calls `register_security_domains()` at import time, which mutates `policy_normalizer.KNOWN_PRECISE_DOMAINS` (line 15 of `policy_normalizer.py`) by adding 10 security domains.
- The production pipeline is: `construct_routes.py:207` -> `ContractService.create_contract()` (line 35 of `contract_service.py`) -> `normalize(spec)` (line 71) -> `_classify_claim()` (line 71 of `policy_normalizer.py`).
- `contract_service.py` imports only from `spec_loader`, `policy_normalizer`, and `check_planner` (lines 18-24). It does NOT import `security_policy_rules`.
- Without the import, `KNOWN_PRECISE_DOMAINS` remains at its base 18 entries (line 16-36 of `policy_normalizer.py`) and never contains the 10 security domains.

**P2 -- Security Check Planning Unreachable:**
- `security_check_planner.py` defines `plan_security_checks()` (line 33) and `merge_security_checks()` (line 125).
- `contract_service.py:74` calls only `plan_checks(spec.slug, norm_result, available_assets)` from `check_planner.py`.
- There is no code path in production that invokes `plan_security_checks()` or `merge_security_checks()`. Only `test_037c_regression.py` (lines 186, 195) and `test_security_check_planner.py` exercise these functions.
- A construct with security corpus skills gets base checks only, missing all security-specific checks (ATTACK_TECHNIQUE_MAPPING, TOOL_INVOCATION_CORRECTNESS, STANDARDS_COMPLIANCE, etc.).

## Reproduction

1. Register a construct with domain claim `vulnerability_analysis`.
2. POST `/{slug}/{version}/contract` with YAML content containing `vulnerability_analysis` as a domain claim.
3. Observe the returned contract: `normalized_claims[0].is_vague == True`, `tier_cap == "UNVERIFIED"`.
4. Expected: `is_vague == False`, `matched_category == "vulnerability_analysis"`, `tier_cap == null`.

Alternate verification:
```python
# In a fresh Python process (simulating production):
from backend.services.policy_normalizer import KNOWN_PRECISE_DOMAINS
assert "vulnerability_analysis" not in KNOWN_PRECISE_DOMAINS  # BUG: True
# After importing security_policy_rules:
import backend.services.security_policy_rules  # noqa: F401
assert "vulnerability_analysis" in KNOWN_PRECISE_DOMAINS  # Now True
```

## Affected Files

| File | Lines | Role |
|------|-------|------|
| `backend/services/contract_service.py` | 18-24 (imports), 35-108 (create_contract) | Missing import of security_policy_rules; create_contract lacks corpus_skills param |
| `backend/services/security_policy_rules.py` | 118 (register call) | Side-effect module that needs to be imported |
| `backend/services/security_check_planner.py` | 33-122 (plan_security_checks), 125-154 (merge_security_checks) | Functions with no production caller |
| `backend/services/policy_normalizer.py` | 16-36 (KNOWN_PRECISE_DOMAINS) | Mutable set that should be populated by security_policy_rules |
| `backend/services/check_planner.py` | 41-106 (plan_checks) | Base planner whose output should be merged with security checks |
| `backend/services/domain_pack_loader.py` | 19-28 (CorpusSkill) | Data class used by security_check_planner |

## Fix Strategy

### Fix 1 (P1): Import security_policy_rules from contract_service.py

Add a side-effect import at `contract_service.py:25`:
```python
import backend.services.security_policy_rules  # noqa: F401  # register security domains
```

This ensures `register_security_domains()` fires before any `normalize()` call in the contract creation pipeline. The import is side-effect only (no symbols used directly), hence the `noqa: F401` annotation.

### Fix 2 (P2): Wire plan_security_checks + merge_security_checks into create_contract

Add an optional `corpus_skills` parameter to `ContractService.create_contract()`:

```python
async def create_contract(
    self,
    registration_id: str,
    yaml_content: str,
    available_assets: Optional[dict] = None,
    corpus_skills: Optional[list[CorpusSkill]] = None,  # NEW
) -> EvaluationContract:
```

Between steps 4 and 5 (after `plan_checks`, before `compute_contract_hash`):
- If `corpus_skills` is provided, iterate over each skill:
  - Call `extract_security_references(skill)` from `security_policy_rules`
  - Call `plan_security_checks(skill, references)` from `security_check_planner`
  - Call `merge_security_checks(planned, security_checks)` to combine
- If `corpus_skills` is None, fall through to existing behavior (spec-derived checks only)

This keeps the existing API backward-compatible (the parameter is optional and defaults to None).

## Test Plan (test-first)

1. **test_normalize_without_security_import**: In an isolated process/module reload, verify `vulnerability_analysis` is classified as vague when security_policy_rules is NOT imported. (Proves the bug exists.)
2. **test_normalize_with_security_import**: After importing security_policy_rules, verify `vulnerability_analysis` is classified as precise. (Proves Fix 1 works.)
3. **test_create_contract_registers_security_domains**: Call `create_contract()` with a YAML containing `vulnerability_analysis` domain claim, verify `is_vague == False` in the returned contract.
4. **test_create_contract_with_corpus_skills**: Call `create_contract()` with `corpus_skills` containing a security CorpusSkill with ATT&CK references. Verify planned_checks includes security-specific check types (ATTACK_TECHNIQUE_MAPPING, STANDARDS_COMPLIANCE).
5. **test_create_contract_without_corpus_skills_fallback**: Call `create_contract()` WITHOUT `corpus_skills`. Verify it still produces base checks only (backward compatibility).
6. **test_security_checks_merged_deterministically**: Provide corpus_skills with overlapping domains. Verify merged output is deduplicated and sorted.

## Acceptance Criteria

1. All 10 security domains from `SECURITY_PRECISE_DOMAINS` are recognized as precise in the live contract path (not just in tests).
2. `create_contract()` accepts optional `corpus_skills` and produces merged security checks when provided.
3. `create_contract()` without `corpus_skills` produces identical output to pre-fix behavior (no regression).
4. All existing 037/037b/037c tests pass unchanged.
5. Contract hash changes deterministically when security checks are added (hash includes security checks).
