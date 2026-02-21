# Sprint 8 (sprint-12) — Security Audit Feedback

**Auditor**: Security Auditor
**Date**: 2026-02-19
**Decision**: APPROVED (with noted findings)

---

## Summary

Sprint 8 delivers cross-repository invariant infrastructure: a JSON Schema, 5 invariant declarations, a verification script, and BATS tests. The security surface is limited — this is developer-facing tooling processing developer-authored YAML. All findings are LOW severity given the threat model (no untrusted input). Code quality is solid with proper exit codes, error handling, and defensive checks.

**Approved for completion.** Findings noted for hardening in future iterations.

---

## Findings

### SEC-12-001: Unsanitized YAML values in grep patterns (LOW)

**File**: `.claude/scripts/verify-invariants.sh:195,205,215,225`
**Type**: Input validation
**Severity**: LOW

`REF_SYMBOL` values from `invariants.yaml` flow directly into `grep -qE` regex patterns without sanitization:

```bash
# Line 195: Python symbol detection
if grep -qE "(def |class )${REF_SYMBOL}[^a-zA-Z_]" "$FULL_PATH"; then

# Line 205: YAML key detection
if grep -qE "^${REF_SYMBOL}:" "$FULL_PATH"; then

# Line 215: Shell function detection
if grep -qE "(function ${REF_SYMBOL}|${REF_SYMBOL}\(\))" "$FULL_PATH"; then
```

If a symbol value contains regex metacharacters (`.*+?()[]{}|^$\`), `grep -qE` could match unintended content or error out.

**Mitigating factors**:
- `invariants.yaml` is developer-authored, not user input
- Symbol values are Python/Shell identifiers (alphanumeric + underscores)
- The schema enforces `id` patterns but not `symbol` patterns
- Worst case: false positive match, not code execution

**Recommendation**: Use `grep -qF` (fixed string) for the generic fallback (line 225), and consider escaping metacharacters via `sed 's/[.[\*^$()+?{|\\]/\\&/g'` for regex patterns. Low priority given the threat model.

### SEC-12-002: Path concatenation without traversal check (LOW)

**File**: `.claude/scripts/verify-invariants.sh:180`
**Type**: Path traversal

```bash
FULL_PATH="${REPO_ROOT}/${REF_FILE}"
```

`REF_FILE` from YAML is concatenated without checking for `../` sequences. A malicious `invariants.yaml` could reference files outside the repository root.

**Mitigating factors**:
- YAML is developer-authored
- Script is read-only (only `grep`, no write operations)
- Repository CI would catch malicious YAML in code review

**Recommendation**: Add a realpath check: `[[ "$(realpath "$FULL_PATH")" == "$REPO_ROOT"/* ]]`. Low priority.

### SEC-12-003: Dead test fixtures (INFO)

**File**: `tests/unit/invariant-verification.bats:16-31`

`setup()` creates `$TEST_DIR/src/example.py` and `$TEST_DIR/src/config.yaml` but no test references these fixtures. No security impact, but dead code in test fixtures can mask test intent. Flagged in code review (engineer-feedback.md) as well.

### SEC-12-004: Schema allows arbitrary symbol strings (INFO)

**File**: `.claude/schemas/invariants.schema.json:80-83`

The `symbol` field in `verification_reference` has no pattern constraint, unlike `id` which enforces `^INV-[0-9]{3}$`. Adding a pattern like `^[a-zA-Z_][a-zA-Z0-9_]*$` would constrain symbols to valid identifiers, reducing the regex injection surface (SEC-12-001).

---

## Acceptance Criteria Security Review

| AC | Security Status |
|----|----------------|
| Schema validates invariant structure | PASS — strict with additionalProperties:false |
| Verification script reads YAML safely | PASS — uses yq (safe YAML parser) |
| Exit codes properly differentiated | PASS — 0/1/2 with correct semantics |
| Cross-repo refs SKIPped | PASS — no execution of external references |
| BATS tests cover failure modes | PASS — 14 tests with proper isolation |
| No command injection vectors | PASS — no eval, no user-controlled command construction |

---

## Status: AUDIT_APPROVED
