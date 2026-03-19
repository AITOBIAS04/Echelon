# Micro-Sprint: Bug 20260319-02fab2

**Bug:** 037c security domains not registered in production -- normalize() classifies precise domains as vague
**Severity:** P1 + P2
**Sprint ID:** sprint-bug-5

---

## Tasks

### T1: Failing tests (test-first)

Write tests in `backend/tests/test_037c_security_integration.py` that prove the bug exists:

1. **test_security_domains_not_in_known_precise_without_import**: Snapshot `KNOWN_PRECISE_DOMAINS` before any security_policy_rules import. Assert `vulnerability_analysis` is absent. Assert `_classify_claim("vulnerability_analysis")` returns `is_vague: True`.

2. **test_create_contract_vague_security_domain**: Build a minimal ConstructSpec with `domain_claims=["vulnerability_analysis"]`. Call `normalize(spec)`. Assert `tier_cap == "UNVERIFIED"` and claim is vague. (This test should PASS initially -- it documents the bug.)

3. **test_create_contract_no_security_checks_without_corpus**: Call `plan_checks()` with a normalization result that has `vulnerability_analysis` as a precise domain. Verify no `ATTACK_TECHNIQUE_MAPPING` or `STANDARDS_COMPLIANCE` checks appear. (Documents P2.)

**Exit criteria:** Tests 1-2 pass (proving the bug). Test 3 passes (proving P2 gap).

### T2: P1 fix -- domain registration import

**File:** `backend/services/contract_service.py`

1. Add side-effect import at line 25:
   ```python
   import backend.services.security_policy_rules  # noqa: F401  # register security domains
   ```

2. Verify: After this import, `KNOWN_PRECISE_DOMAINS` contains all 10 security domains.

3. Write `test_security_domains_registered_after_contract_import`: Import `contract_service`, then check `KNOWN_PRECISE_DOMAINS` contains `vulnerability_analysis`, `threat_modeling`, etc.

4. Write `test_create_contract_precise_security_domain`: Build a spec with `vulnerability_analysis`, call `normalize()`. Assert `is_vague == False`, `tier_cap is None`.

**Exit criteria:** Security domains classified as precise in the contract pipeline. Tests 1-2 from T1 now need updating (they document pre-fix behavior) or new tests prove the fix.

### T3: P2 fix -- security check integration

**File:** `backend/services/contract_service.py`

1. Add imports:
   ```python
   from backend.services.domain_pack_loader import CorpusSkill
   from backend.services.security_policy_rules import extract_security_references
   from backend.services.security_check_planner import plan_security_checks, merge_security_checks
   ```

2. Add `corpus_skills: Optional[list[CorpusSkill]] = None` parameter to `create_contract()`.

3. After `planned = plan_checks(...)` (line 74), add security check merging:
   ```python
   if corpus_skills:
       for skill in corpus_skills:
           refs = extract_security_references(skill)
           sec_checks = plan_security_checks(skill, refs)
           planned = merge_security_checks(planned, sec_checks)
   ```

4. Write `test_create_contract_with_corpus_skills_produces_security_checks`: Provide a CorpusSkill with ATT&CK references. Verify `planned_checks` in the contract includes `ATTACK_TECHNIQUE_MAPPING` entries.

5. Write `test_create_contract_without_corpus_skills_unchanged`: Call without `corpus_skills`. Verify output matches pre-fix behavior exactly (same checks, same contract hash).

**Exit criteria:** Security checks appear in contracts when corpus_skills provided. No regression when omitted.

### T4: Integration + regression tests

1. Run full 037c test suite:
   - `pytest backend/tests/test_037c_regression.py -v`
   - `pytest backend/tests/test_security_policy_rules.py -v`
   - `pytest backend/tests/test_security_check_planner.py -v`
   - `pytest backend/tests/test_security_anchor_mapping.py -v`

2. Run contract service tests:
   - `pytest backend/tests/test_contract_service.py -v`

3. Run full backend test suite:
   - `pytest backend/tests/ -v --tb=short`

4. Write `test_end_to_end_security_contract`: Full pipeline test -- ConstructSpec with security domains + corpus_skills -> normalize -> plan_checks -> merge_security_checks -> compute_contract_hash. Verify the contract hash is deterministic and includes security checks in the canonical JSON.

**Exit criteria:** Zero test failures. All 037/037b/037c tests pass. New integration test proves the full pipeline.

---

## Risk Assessment

- **Low risk**: Fix 1 (the import) is a single line with no behavioral change to existing code paths -- it only populates an already-designed extension point.
- **Low risk**: Fix 2 (corpus_skills param) is additive with a default of None, preserving backward compatibility.
- **No schema changes**: No migrations, no model changes, no API signature changes in routes.
- **Determinism preserved**: `merge_security_checks` maintains the same sort-by-(check_type, domain, check_id) contract.
