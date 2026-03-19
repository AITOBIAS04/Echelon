All good

## Review Summary

Clean bug fix. Both P1 and P2 are correctly addressed with minimal, well-scoped changes. 67/67 tests pass (confirmed independently). No regressions, no security vulnerabilities introduced.

## Task Verification

| Task | Status | Notes |
|------|--------|-------|
| T1: Failing tests (test-first) | Done | 5 tests in `TestSecurityDomainRegistration` prove the domain registration path; `test_broad_security_still_vague` is a good guardrail |
| T2: P1 fix — domain registration import | Done | `security_policy_rules` imported via `from` statement (line 27), side-effect fires at import time |
| T3: P2 fix — security check integration | Done | `corpus_skills` parameter added (line 49), merge loop at lines 91-95, backward-compatible default of `None` |
| T4: Integration + regression | Done | Full pipeline test (`TestFullPipelineIntegration`), regression tests for non-security constructs, all 51 pre-existing tests pass unchanged |

## What Was Done Well

1. **Smart import approach.** Rather than adding a bare `import backend.services.security_policy_rules` with a `noqa: F401`, the implementation uses a `from ... import extract_security_references` that both triggers the side-effect and imports a symbol actually used by the P2 fix. This is cleaner than the sprint plan's original suggestion because the import has a visible purpose beyond the side-effect.

2. **AST-based import verification test.** `test_contract_service_imports_security_policy_rules` (line 123) uses AST parsing to verify the import exists in source without pulling in the DB layer. Pragmatic solution to the asyncpg unit-test constraint.

3. **Test structure.** Four well-named test classes map directly to T1-T4. The `_make_spec` and `_make_corpus_skill` helpers keep tests readable. The `test_broad_security_still_vague` test is a particularly good negative case that ensures the guardrail against overly broad "security" claims is preserved.

4. **Determinism tests.** Both `test_contract_hash_changes_with_security_checks` and `test_contract_hash_deterministic_with_security_checks` verify the contract hash behaves correctly in both directions (changes when checks added, stable across repeated runs).

5. **No over-reach.** The route layer (`construct_routes.py:207`) was correctly left untouched. The `corpus_skills` parameter is available for callers that have skills, but the existing API endpoint doesn't break. The caller-side merge pattern from 037c is preserved.

## Minor Observations (Not Blocking)

- The route at `construct_routes.py:207` does not yet pass `corpus_skills` to `create_contract()`. This is expected — the triage notes this is an integration gap, and the fix correctly makes the parameter available without forcing it into the route. A future cycle will need to wire the route to pass corpus skills from the request body when available.
- The `_make_spec` helper hardcodes `raw_yaml` with a generic template regardless of what `domain_claims` are passed in. This is fine for current tests since `normalize()` operates on `domain_claims` not `raw_yaml`, but if future tests rely on `raw_yaml` content matching domain_claims, the helper would need updating.
