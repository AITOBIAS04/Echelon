APPROVED - LETS FUCKING GO

## Security Audit: Bug 20260319-02fab2 (sprint-bug-5)

**Auditor:** Paranoid Cypherpunk Auditor
**Date:** 2026-03-19
**Verdict:** APPROVED — no blocking findings

---

## Checklist Results

### 1. Secrets — PASS

No hardcoded credentials, API keys, tokens, or secrets anywhere in the changed files. No `.env` reads introduced. The `contract_service.py` changes are pure business logic with no external service calls beyond the existing DB session.

### 2. Auth/Authz — PASS

No privilege escalation vectors introduced. The `corpus_skills` parameter is an optional internal-API parameter. The HTTP route at `construct_routes.py:207` does NOT expose `corpus_skills` to external callers — it passes only `registration_id` and `yaml_content`. The parameter is available exclusively for internal service-to-service composition. No new endpoints, no new authentication bypass paths.

### 3. Input Validation — PASS

**Regex patterns (ReDoS analysis):** All three patterns in `security_policy_rules.py` are linear-time:
- `T\d{4}(?:\.\d{3})?` — fixed-width digit match, no backtracking
- `CWE-\d+` — greedy digit match, no alternation
- `A\d{2}:\d{4}` — fixed-width, no backtracking

No catastrophic backtracking possible. These are textbook safe regex patterns.

**corpus_skills injection surface:** The `CorpusSkill` dataclass is `frozen=True` (immutable). Its fields (`name`, `description`, `domain`, `references`, `verification_steps`) are consumed only through:
- `extract_security_references()` — iterates `skill.references`, applies compiled regex `.search()` on each string. No eval, no exec, no format string injection.
- `plan_security_checks()` — reads `skill.domain`, `skill.name`, `skill.verification_steps`. Domain is used as a string key in `PlannedCheck.domain`. Name goes into `source` field as `f"security_corpus:{skill.name}"`. No SQL injection risk (these go into JSON, not raw SQL). No command injection (no subprocess calls).
- String containment checks (`"dependency" in skill.domain`, `"secret" in skill.domain`) — safe, no regex on untrusted input here.

Even if a malicious `CorpusSkill` were constructed with adversarial string content in `domain` or `references`, the worst case is garbage check_ids in the planned_checks JSON. No code execution, no SQL injection, no file system access.

### 4. Data Integrity — PASS

**Contract hash determinism preserved.** The `compute_contract_hash()` function uses `json.dumps(sort_keys=True, separators=(",", ":"))` which produces canonical JSON. The `merge_security_checks()` sorts by `(check_type, domain, check_id)` before returning. Both paths are deterministic. Two dedicated tests verify this: `test_contract_hash_changes_with_security_checks` and `test_contract_hash_deterministic_with_security_checks`.

**PlannedCheck is frozen=True** — immutable after creation. No risk of post-creation mutation corrupting hash computation.

### 5. Import Safety — PASS

The side-effect import (`security_policy_rules` mutating `KNOWN_PRECISE_DOMAINS` at import time via line 118) is a known Python pattern for module-level initialization. Key observations:

- `register_security_domains()` is idempotent — calling it N times produces the same result (set union is idempotent). Tested by `test_idempotent_registration`.
- No timing vulnerability: `KNOWN_PRECISE_DOMAINS` is a module-level `set` in `policy_normalizer.py`. Python's GIL protects set mutations during import. The set is fully populated before any `normalize()` call can execute because imports resolve before function bodies run.
- The import is a `from ... import extract_security_references` — not a bare side-effect-only import. This means the import has a visible, used purpose (P2 fix calls `extract_security_references`), which is cleaner than the sprint plan's original `noqa: F401` suggestion.
- The AST-based test (`test_contract_service_imports_security_policy_rules`) is a pragmatic verification that the import exists without pulling in the DB layer. This is a sound approach given the asyncpg constraint in unit tests.

### 6. Code Quality — PASS

- **No obvious bugs.** The `if corpus_skills:` guard at line 91 correctly short-circuits when `None` (default) or empty list.
- **Loop structure is correct.** Each skill independently produces refs and checks, then merged into the accumulator. Order doesn't matter because `merge_security_checks` deduplicates by `check_id` and re-sorts.
- **Error paths:** `extract_security_references` returns empty list for skills with no matching references. `plan_security_checks` produces empty check list when no frameworks match. `merge_security_checks` with empty `security_checks` returns `base_checks` unchanged. All graceful degradation.
- **CorpusSkill frozen dataclass** prevents accidental mutation during iteration.
- **16 new tests** with good coverage of positive paths, negative paths (broad "security" still vague), determinism, sort order, and regression.

### 7. Regression Safety — PASS

- When `corpus_skills` is `None` (the default and the only value the HTTP route currently passes), the code at lines 91-95 is entirely skipped. The pipeline is byte-for-byte identical to pre-fix behavior.
- All 51 pre-existing tests pass unchanged (confirmed independently: 67 total = 16 new + 51 existing).
- The `KNOWN_PRECISE_DOMAINS` base set (18 entries) is preserved. Security domains are additive (now 28 total). Non-security domains (`design_systems`, `motion_design`, etc.) are unaffected. Tested by `TestRegressionNonSecurityUnchanged`.

---

## Observations (Non-Blocking)

**LOW — Future integration gap:** The HTTP route at `construct_routes.py:207` does not yet pass `corpus_skills` through. This is explicitly documented and deferred. When this wiring is added, a separate security review should verify that `corpus_skills` from the request body is properly validated (schema validation via Pydantic, type enforcement on the `CorpusSkill` dataclass fields).

**LOW — Module-level set mutation:** The `KNOWN_PRECISE_DOMAINS` mutation pattern works correctly under CPython's GIL but is technically not thread-safe under free-threaded Python (PEP 703, Python 3.13t). This is a future consideration only — the project runs Python 3.12 on CPython where this is safe.

---

## Test Verification

```
67 passed in 0.20s (16 new + 51 existing, zero failures)
```

Independently confirmed by running the full suite during this audit.
