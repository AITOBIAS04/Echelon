# Sprint 101 — Implementation Report

**Sprint:** sprint-1 (global: sprint-101)
**Cycle:** cycle-037c — Security + Domain Pack Verification
**Focus:** Security Policy Rules + Domain Registration
**Date:** 19 March 2026

---

## Summary

Implemented security-specific policy rules that register 10 precise security sub-domains with the policy normalizer. Broad "security" remains vague. Framework reference extraction (ATT&CK, CWE, OWASP) implemented.

## Files Created

| File | Lines | Purpose |
|------|-------|---------|
| `backend/services/security_policy_rules.py` | ~105 | Security domain registration + reference extraction |
| `backend/tests/test_security_policy_rules.py` | ~175 | 17 tests covering registration, normalization, extraction |

## Files Changed

None. Import-time set mutation of `KNOWN_PRECISE_DOMAINS` — no code changes to `policy_normalizer.py`.

## Tasks Completed

### T1.1: Security domain registration
- `SECURITY_PRECISE_DOMAINS` set with 10 specific domains
- `register_security_domains()` mutates `KNOWN_PRECISE_DOMAINS` at import time
- Import-time auto-registration via `_REGISTERED_COUNT = register_security_domains()`
- Idempotent — calling again adds 0 new domains

### T1.2: Framework reference extraction
- `extract_security_references()` — regex-based extraction from `CorpusSkill.references`
- Compiled patterns: `_ATTACK_PATTERN`, `_CWE_PATTERN`, `_OWASP_PATTERN`
- ATT&CK sub-technique support: T1059.001 extracts as full ID
- `classify_security_claim()` — classifies as `reference_backed` or `unanchored`

### T1.3: Tests
17 tests passing (sprint plan required 5):
- `TestRegisterSecurityDomains` (3): all registered, idempotent, size check
- `TestPreciseSecurityDomains` (3): individual domains, all-domains sweep
- `TestBroadSecurityStaysVague` (4): token match, compound claim, normalization both ways
- `TestExtractSecurityReferences` (5): ATT&CK, CWE, OWASP, mixed, empty
- `TestClassifySecurityClaim` (2): reference_backed, unanchored

## Design Decisions

1. **Import-time registration** — `register_security_domains()` called at module level. The normalizer reads `KNOWN_PRECISE_DOMAINS` at call time, so mutations are immediately visible.
2. **Compiled regex patterns** — `_ATTACK_PATTERN`, `_CWE_PATTERN`, `_OWASP_PATTERN` compiled once at module level for performance.
3. **Full sub-technique capture** — ATT&CK pattern captures `T1059.001` not just `T1059`, preserving specificity.

## Test Results

```
17 passed in 0.04s
```

## Acceptance Criteria Status

- [x] `register_security_domains()` adds all 10 domains to `KNOWN_PRECISE_DOMAINS`
- [x] `vulnerability_analysis` passes `_classify_claim()` as precise
- [x] Broad "security" still tier-caps to UNVERIFIED
- [x] ATT&CK T-codes extracted from references
- [x] CWE-IDs and OWASP refs extracted
- [x] Structured dicts with `framework`, `id`, `raw_reference` keys
