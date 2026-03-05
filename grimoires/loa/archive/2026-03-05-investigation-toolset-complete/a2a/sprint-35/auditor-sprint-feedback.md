# Security Audit — Sprint 35 (local sprint-3)

**Auditor**: Paranoid Cypherpunk Auditor
**Date**: 2026-03-05
**Verdict**: APPROVED - LETS FUCKING GO

## Files Audited

| File | Lines | Risk |
|------|-------|------|
| `backend/schemas/theatre.py` | 230 | LOW — request/response schemas only |
| `backend/database/models.py` | 683 | LOW — ORM model definitions |
| `backend/api/theatre_routes.py` | 613 | MEDIUM — network-facing API routes |
| `backend/alembic/versions/c014c_add_stop_condition_columns.py` | 50 | LOW — DDL migration |
| `backend/investigation/certificate.py` | 244 | MEDIUM — certificate builder with hash computation |
| `backend/investigation/stop_conditions.py` | 125 | LOW — pure evaluation logic |
| `backend/investigation/toolset.py` | 207 | LOW — orchestrator delegation |
| `backend/investigation/artifacts.py` | 54 | LOW — deterministic serialisation |
| `backend/investigation/tests/test_certificate.py` | 239 | N/A — test file |
| `backend/investigation/tests/test_stop_conditions.py` | 128 | N/A — test file |
| `backend/investigation/tests/test_stop_condition_commitment.py` | 151 | N/A — test file |
| `backend/investigation/tests/test_artifacts.py` | 134 | N/A — test file |
| `backend/investigation/tests/test_toolset_e2e.py` | 246 | N/A — test file |
| `theatre/engine/canonical_json.py` | 63 | LOW — RFC 8785 serialiser (dependency) |

**Total production lines audited**: ~2,206
**Total test lines reviewed**: ~898

## Security Checklist

| Check | Status |
|-------|--------|
| Secrets/Credentials | PASS — No hardcoded secrets, API keys, or env vars in any investigation module. No `os.environ`, `getenv`, or credential strings found. |
| Input validation | PASS — `TheatreCreate.stop_condition` has `max_length=30` constraint. `stop_config` is `Optional[dict]`. Pydantic `model_validator` rejects null `inquiry_class`. `StopCondition` enum validates all condition types via `StopCondition(stop_condition)` which raises `ValueError` on unknown values. |
| Injection (SQL) | PASS — Alembic migration uses `op.add_column()` / `op.drop_column()` with string literals only. No raw SQL, no string interpolation into queries. All DB access via SQLAlchemy ORM with parameterised queries. |
| Injection (Shell/Eval) | PASS — No `eval()`, `exec()`, `subprocess`, `os.system`, or `__import__` found in any investigation module. |
| Hash integrity | PASS — All investigation-side hashing uses `hashlib.sha256()` with `canonical_json()` from `theatre.engine.canonical_json` (RFC 8785 compliant). Certificate hash payload correctly excludes `certificate_hash` itself and anchoring fields. NaN/Infinity prohibited by `canonical_json()`. |
| Immutability enforcement | PASS — `InvestigationCertificate` has `model_config = {"frozen": True}`. `EvidenceEnvelope` is append-only with no delete method (tested: `assert not hasattr(envelope, "delete")`). `RedactionEvent` model is frozen. Properties return copies via `list()`. |
| Independence invariant | PASS — `InvestigationCorroborationChecker` requires 2+ upstream groups for SUPPORTED status. Single-provenance-class routing triggers REVIEW_REQUIRED. Tested in `test_routing_hint_single_provenance`. |
| Access-tier policy | PASS — `SignalScanner` manifest includes `access_tier_policy` field. Skipped source groups include `access_tier` and `reason` for audit trail. Tested in `test_manifest_contains_access_tier_policy`. |
| Data privacy | PASS — No PII handling. No personal data storage. Evidence content is hashed (`SHA-256(content)`) not stored. Redaction events log reason class only, not content. |
| Auth/Authz | PASS — All mutation endpoints (`create_theatre`, `commit_theatre`, `run_theatre`, `settle_theatre`) require `Depends(get_current_user)`. `_get_user_theatre()` enforces `Theatre.user_id == user_id` ownership check. Public endpoints are read-only (commitment receipt, certificate, template listing). |
| SSRF | PASS — No URL construction from user input. No HTTP client calls (`requests`, `urllib`, `httpx`, `aiohttp`) in any investigation module. |
| DoS | PASS — No unbounded recursion. No blocking I/O. `canonical_json()` recurses only on dict/list depth (bounded by JSON structure). `ARTEFACT_TYPES` is a `frozenset` (O(1) lookup). |
| Timing side channels | PASS (informational) — Hash comparisons in test assertions use `==` which is acceptable for non-security-critical test code. Production hash comparison for webhooks correctly uses `hmac.compare_digest()` (verified in `backend/payments/coinbase_commerce.py` and `backend/api/butler_webhooks.py`). The commitment hash is not compared for authentication purposes -- it is stored and returned, not used as a gating mechanism where timing attacks apply. |
| Post-COMMITTED mutation | PASS — `commit_theatre()` requires `theatre.state == "DRAFT"`. No endpoint exists to modify `stop_condition` or `stop_config` after creation. The commitment hash seals these values. Any tampering would produce a different hash on recomputation. |
| Stop condition evaluator override | PASS — `InvestigationStopConditionEvaluator.evaluate()` only reads the `stop_config` dict passed to it. No class-level state, no environment variable injection, no runtime override mechanism. Tested explicitly in `test_resolution_uses_committed_stop_config_only`. |
| Alembic migration safety | PASS — Uses `op.add_column` with `sa.String(30)` and `sa.JSON()`. Idempotent via try/except. No raw SQL. Downgrade correctly drops columns. Column types match ORM model definition. |

## Informational Notes

1. **`json.dumps` vs `canonical_json` in commitment hash extension** (theatre_routes.py:201): The commitment hash extension for stop fields uses `json.dumps(stop_fields, sort_keys=True)` instead of `canonical_json()`. This is acceptable because the stop_fields dict is a flat structure with string keys and simple values, where `sort_keys=True` produces deterministic output. However, for consistency with the investigation-side hashing (which uses `canonical_json()` everywhere), a future sprint could unify this. Not a security defect -- `sort_keys=True` guarantees determinism for this payload shape.

2. **Anchoring priority 4 intentionally not triggered**: The routing cascade documents "anchoring_pending" as priority 4, but the code intentionally skips this check because anchoring status is always "pending" at certificate build time (set post-build). This is architecturally sound and documented in the code comment at line 239 of `certificate.py`.

3. **Broad exception catching in Alembic migration**: The `try/except Exception: pass` pattern in the migration is idempotent but swallows all exceptions including connection errors. This is a common Alembic pattern for backward compatibility but could mask real failures in CI. Low severity -- standard practice.

4. **`stop_condition` field is a free-form string in the schema** (`max_length=30`) rather than a Pydantic `Literal` or enum constraint. Validation happens downstream in `InvestigationStopConditionEvaluator.evaluate()` via `StopCondition(stop_condition)` which raises `ValueError` on unrecognised values. Defence in depth is maintained but the error surfaces at evaluation time rather than at the API boundary. Acceptable.

## Approval

APPROVED - LETS FUCKING GO
