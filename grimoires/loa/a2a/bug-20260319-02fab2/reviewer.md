# Implementation Report: Bug 20260319-02fab2

**Sprint:** sprint-bug-5
**Bug:** 037c security domains not registered in production — normalize() classifies precise domains as vague
**Severity:** P1 + P2
**Status:** IMPLEMENTED

---

## Changes

### P1 Fix: Domain Registration Import (T2)

**File:** `backend/services/contract_service.py` (lines 27–31)

Added imports that transitively trigger `register_security_domains()` at import time:

```python
from backend.services.security_policy_rules import extract_security_references
from backend.services.security_check_planner import (
    plan_security_checks,
    merge_security_checks,
)
# Side-effect: importing security_policy_rules registers 10 precise security
# domains into KNOWN_PRECISE_DOMAINS at import time (cycle 037c-fix P1).
```

Importing `security_policy_rules` fires `register_security_domains()` (line 118 of that module), which mutates `KNOWN_PRECISE_DOMAINS` to include all 10 security sub-domains. This ensures `normalize()` classifies them as precise (not vague) in the live contract pipeline.

### P2 Fix: Security Check Integration (T3)

**File:** `backend/services/contract_service.py` (lines 44–95)

1. Added `corpus_skills: Optional[list[CorpusSkill]] = None` parameter to `create_contract()`.
2. After `plan_checks()` (step 4), added security check merging:

```python
# 4b. Merge security-specific checks if corpus skills provided
if corpus_skills:
    for skill in corpus_skills:
        refs = extract_security_references(skill)
        sec_checks = plan_security_checks(skill, refs)
        planned = merge_security_checks(planned, sec_checks)
```

This wires `plan_security_checks()` and `merge_security_checks()` into the production pipeline. When `corpus_skills` is `None` (default), behavior is identical to pre-fix.

### Tests (T1 + T4)

**File:** `backend/tests/test_037c_security_integration.py` — 16 new tests

| Class | Tests | Coverage |
|-------|-------|----------|
| `TestSecurityDomainRegistration` | 5 | P1: domains registered, precise classification, AST import verification |
| `TestSecurityCheckIntegration` | 6 | P2: ATT&CK checks, merge, sort order, hash determinism, backward compat |
| `TestFullPipelineIntegration` | 3 | End-to-end: YAML → normalize → plan → merge → hash |
| `TestRegressionNonSecurityUnchanged` | 2 | Non-security constructs unaffected |

**Key test design decision:** `test_contract_service_imports_security_policy_rules` uses AST parsing to verify the import exists at source level rather than importing `contract_service` directly, because the import chain pulls in the DB layer (`asyncpg`) which is unavailable in the unit-test environment. The actual registration side-effect is proven by `test_security_domains_in_known_precise`.

---

## Test Results

```
67 passed in 0.22s
```

Full regression suite: `test_037c_regression.py` (8), `test_security_policy_rules.py` (17), `test_security_check_planner.py` (12), `test_security_anchor_mapping.py` (8), `test_contract_service.py` (6), `test_037c_security_integration.py` (16) — all passing, zero failures.

---

## Risk Assessment

- **P1 fix (import):** Single side-effect import, no behavioral change to existing paths. Low risk.
- **P2 fix (corpus_skills):** Additive parameter with `None` default. When omitted, identical output to pre-fix. Low risk.
- **No schema changes.** No migrations, no model changes, no API route changes.
- **Determinism preserved:** `merge_security_checks` maintains sort-by-(check_type, domain, check_id).

---

## Acceptance Criteria

| Criterion | Status |
|-----------|--------|
| All 10 security domains recognized as precise in live contract path | ✅ |
| `create_contract()` accepts optional `corpus_skills` | ✅ |
| Security checks merged when `corpus_skills` provided | ✅ |
| Without `corpus_skills`, identical to pre-fix output | ✅ |
| All existing 037/037b/037c tests pass unchanged | ✅ |
| Contract hash changes deterministically with security checks | ✅ |
