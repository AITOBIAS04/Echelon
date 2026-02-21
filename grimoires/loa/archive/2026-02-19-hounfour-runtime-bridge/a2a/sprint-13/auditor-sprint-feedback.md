# Sprint 9 (sprint-13) — Security Audit Feedback

**Auditor**: Security Auditor
**Date**: 2026-02-19
**Decision**: APPROVED (with noted findings)

---

## Summary

Sprint 9 delivers epistemic trust scopes (context_filter.py, context_access in model-permissions.yaml), comprehensive tests, and the Jam geometry design document. The code is explicitly transparent about its threat model: "This is best-effort content reduction, not a security boundary" (context_filter.py docstring, line 26). Given this declared scope, the implementation is well-engineered with proper immutability (deepcopy), logging of bypass conditions (BB-504), cache invalidation, and documented limitations (BB-502 through BB-507).

**Approved for completion.** Findings noted for hardening when/if this becomes a security boundary.

---

## Findings

### SEC-13-001: Non-string content bypasses filtering (MEDIUM)

**File**: `.claude/adapters/loa_cheval/routing/context_filter.py:337-346`
**Type**: Filter bypass
**Severity**: MEDIUM

```python
if isinstance(content, str) and content:
    msg["content"] = filter_message_content(content, context_access)
elif content and not isinstance(content, str):
    # BB-504: Non-string content (list/dict) bypasses filtering.
    logger.warning(...)
```

When `content` is a list (e.g., Anthropic's structured content blocks: `[{"type": "text", "text": "CVE-..."}]`), all filtering is bypassed. A message constructed with list-of-blocks format would pass security, architecture, business_logic, and lore content through unfiltered.

**Mitigating factors**:
- Documented as BB-504 with logging
- Module docstring declares "not a security boundary"
- The warning log creates an audit trail
- Content format is controlled by the calling code (cheval.py), not by external input

**Recommendation**: When content is a list of dicts with `type: "text"`, iterate and filter each text block's `text` field. This would close the structured content bypass without changing the non-security-boundary stance.

### SEC-13-002: Test coverage gap for list content bypass (LOW)

**File**: `.claude/adapters/tests/test_epistemic_scopes.py:275-280`
**Type**: Insufficient test coverage

```python
def test_non_string_content_passes_through(self):
    messages = [{"role": "tool", "content": 42}]
```

Tests the bypass with `content: 42` (integer) but not with the realistic bypass scenario: `content: [{"type": "text", "text": "<security content>"}]`. A test with structured content blocks containing filterable content (CVE references, architecture sections) would validate the BB-504 behavior and serve as a regression guard if the bypass is later fixed.

### SEC-13-003: Regex-based content detection is evasion-prone (LOW)

**File**: `.claude/adapters/loa_cheval/routing/context_filter.py:52-82`
**Type**: Filter evasion

The `_SECURITY_MARKERS`, `_ARCHITECTURE_MARKERS`, `_LORE_MARKERS`, and `_FUNCTION_BODY_PATTERN` regexes can be evaded through:

- Unicode homoglyphs (e.g., Cyrillic `С` instead of Latin `C` in `CVE-`)
- Creative formatting (e.g., `C V E - 2024-12345` with spaces)
- Nested code blocks or escaped markdown
- Language patterns not covered by BB-502 (Go, Rust, Java methods)

**Mitigating factors**:
- Explicitly documented as "heuristic-based" and "not a security boundary" (docstring, module header)
- BB-502 documents language coverage gaps
- BB-503 documents inline security content leakage
- BB-507 documents lore false positives
- Comprehensive BB-tag documentation shows intentional design decisions

**No action required** — the code is honest about its limitations.

### SEC-13-004: Missing jam-synthesizer in model-permissions.yaml (MEDIUM)

**File**: `.claude/data/model-permissions.yaml`
**Type**: Trust boundary gap

The Jam geometry design specifies `anthropic:claude-sonnet-4-6` as the synthesis model (jam-geometry.md line 68, model-config.yaml). However, `model-permissions.yaml` has no entry for `anthropic:claude-sonnet-4-6`. When `lookup_trust_scopes("anthropic", "claude-sonnet-4-6")` is called, it returns `None`, which defaults to all-full context_access.

**Impact**: The synthesizer would receive ALL content including security findings from Claude's review (which has `security: full`). This creates an information flow: Claude reviews with full security context → synthesizer receives Claude's security-aware review → unified output contains security-derived findings → unified output is posted (potentially visible to models/users that should not see security content).

**Mitigating factors**:
- Jam geometry is feature-flagged `false` (opt-in only, not active)
- This is a design document, not running code
- The synthesizer arguably NEEDS full context to synthesize correctly
- The default-to-all-full behavior is documented and intentional (backward compatible)

**Recommendation**: When Jam is implemented, add explicit `anthropic:claude-sonnet-4-6` entry to model-permissions.yaml with appropriate context_access scopes. Consider whether the unified output should inherit the most restrictive reviewer's scopes.

### SEC-13-005: TOCTOU in permissions cache (LOW)

**File**: `.claude/adapters/loa_cheval/routing/context_filter.py:379-386`
**Type**: Race condition

```python
current_mtime = permissions_path.stat().st_mtime
if _PERMISSIONS_CACHE is not None and current_mtime == _PERMISSIONS_MTIME:
    return _PERMISSIONS_CACHE
```

Between `stat().st_mtime` check and `open()` (line 398), the file could change. In a concurrent environment, this could serve stale permissions.

**Mitigating factors**:
- Python GIL serializes thread access
- Single-process architecture (cheval.py is invoked per-request)
- File is developer-managed configuration, not frequently modified
- The mtime check is a cache optimization, not a security gate

**No action required** — appropriate for the execution model.

### SEC-13-006: Hardcoded regex for security section detection (INFO)

**File**: `.claude/adapters/loa_cheval/routing/context_filter.py:172`

```python
if re.match(r"^#{1,4}\s*(?:Security|Audit|Vulnerability|Findings)", line, re.IGNORECASE):
```

Security sections with non-English headers (e.g., `## Sicherheit`, `## Seguridad`) would not be detected. This is consistent with BB-502's documented limitation (English-only content patterns) but worth noting for internationalized codebases.

### SEC-13-007: context_access defaults favor openness (INFO)

**File**: `.claude/adapters/loa_cheval/routing/context_filter.py:44-49`

```python
DEFAULT_CONTEXT_ACCESS: Dict[str, str] = {
    "architecture": "full",
    "business_logic": "full",
    "security": "full",
    "lore": "full",
}
```

Default-open is the correct choice for backward compatibility (pre-v7 models work without changes). However, in a defense-in-depth model, default-closed would be more secure. The current design prioritizes compatibility over restriction. Documented as intentional.

---

## Acceptance Criteria Security Review

| AC | Security Status |
|----|----------------|
| context_access 7th dimension with 4 sub-fields | PASS — clean implementation |
| deepcopy prevents mutation of caller data | PASS — verified in code and tests |
| Logging of filtered dimensions and bypass conditions | PASS — BB-504 warning, dimension logging |
| Native runtime bypass | PASS — correct (native models have file access anyway) |
| Test coverage for all filtering modes | PASS — 30+ tests, 8 classes |
| Jam geometry design grounded in existing infrastructure | PASS — file:line references verified |
| Feature flag default false | PASS — opt-in only |
| No command injection or code execution paths | PASS — pure text transformation |

---

## Status: AUDIT_APPROVED
