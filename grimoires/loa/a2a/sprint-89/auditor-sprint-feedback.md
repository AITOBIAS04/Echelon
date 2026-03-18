# Auditor Sprint Feedback — Sprint 89 (Cycle-026a Sprint-0)

**Auditor:** Paranoid Cypherpunk Auditor
**Date:** 2026-03-17
**Sprint scope:** Asset Policy + Registry Schema (eval_asset_registry.py, construct_anchor_schema.py, eval_asset_policy.py, test_cycle026a_sprint0.py)

---

## Verdict: APPROVED

No CRITICAL or HIGH findings. Code is clean, minimal-surface, well-structured.

---

## Security Checklist Results

### 1. Secrets
**PASS.** No hardcoded credentials, API keys, tokens, or secrets anywhere in the schema or policy files. Pure data-structure and classification logic only.

### 2. Path Traversal
**N/A for this sprint.** No filesystem operations in schema or policy modules. The `RegistryFileEntry.path` field is a plain string with `min_length=1` validation but no path-traversal guard — this is acceptable because (a) the schema is a data contract, not an executor, and (b) the builder in sprint-1 that populates this field uses `relative_to()` which constrains paths. See sprint-90 for deeper analysis.

### 3. Input Validation
**PASS.**
- `_ASSET_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]*$")` — strict allowlist regex: lowercase alphanum start, only alphanum/hyphens/underscores. No dots, no slashes, no unicode shenanigans. Good.
- `content_hash` field validators on both `RegistryFileEntry` and `DatasetRegistryEntry` enforce `sha256:` prefix. The `v[:20]` truncation in the error message prevents log flooding from absurdly long inputs. Good defensive practice.
- `asset_class` uses `Literal["benchmark", "standard"]` — Pydantic enforces this exhaustively. No open strings.
- `files` field has `min_length=1` — cannot register an empty asset. Correct.

### 4. Data Integrity
**PASS.** Schema correctly models SHA-256 with prefix convention. No hashing logic in this sprint (that's sprint-1).

### 5. Supply Chain
**PASS.** Imports: `re`, `datetime`, `typing` (stdlib), `enum` (stdlib), `pydantic` (declared dependency). No unexpected third-party imports.

### 6. Error Handling
**PASS.** Pydantic validators surface structured error messages. The `content_hash` error truncates at 20 chars (`v[:20]`), preventing malicious payloads from being reflected in full. The `asset_id` error uses `v!r` (repr), which is safe for structured logging.

The `validate_snapshot_candidate()` function returns `(False, reason)` tuples with descriptive but non-sensitive messages. The `reject_live_as_immutable()` function raises `ValueError` with the asset_id echoed back — this is acceptable because asset_id is already validated upstream (regex-safe characters only).

### 7. Code Quality
**PASS.** Clean, well-documented, no dead code, no unreachable branches. Classification logic in `eval_asset_policy.py` is simple allowlist/denylist lookup with case normalization — exactly as it should be.

---

## Specific Concerns (from audit brief)

### Q4: Are Pydantic validators sufficient to prevent malformed registry entries?
**YES.** The validators are defense-in-depth:
- `asset_id`: Regex-enforced filesystem-safe pattern. Rejects dots, slashes, spaces, uppercase, unicode.
- `content_hash`: Prefix validation prevents hash confusion attacks (e.g., someone injecting `md5:` or `none:` hashes).
- `asset_class`: Exhaustive `Literal` type. Cannot inject unknown classifications.
- `files`: Non-empty list enforcement prevents degenerate entries.
- `source_url`, `version`: `min_length=1` prevents empty strings but does not validate URL format. This is intentional — the URL is metadata for provenance, not something the system fetches. Acceptable.

---

## LOW Findings

### L-01: `RegistryFileEntry.path` allows `..` components
The `path` field on `RegistryFileEntry` has no validator rejecting `..` segments. A manually constructed (not builder-generated) entry like `path="../../../etc/passwd"` would parse successfully. This is LOW because:
1. The schema is a data contract — it does not execute paths.
2. The builder (`r2_manifest_builder.py`) generates paths via `relative_to()` which cannot produce `..` components.
3. Any consumer that resolves these paths against a base directory should use `resolve()` + containment checks.

**Recommendation:** Consider adding a `field_validator` on `path` that rejects entries containing `..` for defense-in-depth. Not blocking.

### L-02: `AnchorClass` enum is open to extension without migration
New `AnchorClass` values can be added to the enum without any migration or versioning gate. If a new anchor class is added and old serialized data is deserialized, Pydantic will reject the unknown value — which is actually the correct behavior (fail-closed). No action needed.

---

## Test Coverage Assessment

**test_cycle026a_sprint0.py** provides thorough coverage:
- 13 test cases across 3 test classes.
- Positive and negative cases for schema validation.
- All 3 asset dispositions tested (SNAPSHOT, LIVE, UNKNOWN).
- Case-insensitive classification tested.
- Round-trip JSON serialization tested.
- Both `RegistryFileEntry` and `DatasetRegistryEntry` hash validators tested independently.

No gaps identified.

---

## Summary

Sprint-0 delivers a solid schema and policy foundation. The code follows least-privilege principles: schemas validate inputs tightly, the policy module is stateless and uses immutable frozensets for allowlists/denylists, and no filesystem or network I/O is performed. Approved without reservations.
