# Sprint 3 (Global 45) — Security Audit

**Auditor:** Paranoid Cypherpunk Auditor
**Date:** 2026-03-06
**Verdict:** APPROVED - LETS FUCKING GO

## Security Checklist

| Category | Status |
|----------|--------|
| Secrets/Credentials | CLEAN — no hardcoded secrets |
| SQL Injection | N/A — no SQL in this sprint (JSON registry, in-memory store) |
| Input Validation | CLEAN — source_id validated against registry, receipt_body checked |
| Auth/Authz | CLEAN — no new auth-sensitive endpoints |
| XSS | CLEAN — React JSX auto-escaping, string values rendered via template literals |
| Info Disclosure | CLEAN — 422 error reveals source_id name (already known to caller, they sent it) |
| Error Handling | CLEAN — unknown source_id silently passes (no enforcement), safe default |
| Data Integrity | CLEAN — source_ids tracked in set (no duplicates), registry loaded from trusted local JSON |
| Resource Exhaustion | CLEAN — no new loops over unbounded data, registry is small fixed set |
| Path Traversal | CLEAN — registry path constructed from `__file__` dirname, not user input |

## Detailed Notes

**`_get_registry()` singleton** (`investigation_routes.py:68-78`): Path construction uses `os.path.dirname(os.path.dirname(__file__))` + hardcoded `"osint", "sources.json"` — no user input in path. Lazy initialization avoids import-time I/O. Global singleton is fine for read-only registry in a single-process server.

**Receipt enforcement** (`investigation_routes.py:296-304`): Gate checks `if request.source_id` first — empty string (default) skips enforcement entirely. Backwards compatible. When source_id is provided, `registry.get_source()` returns `None` for unknown IDs → enforcement skipped (safe default: allow). The `not request.receipt_body` check on empty string is correct (falsy). Error message includes the source_id the caller sent (not a secret — they provided it).

**Legal review computation** (`investigation_routes.py:254-263`): `entry.get("source_ids", set())` is safe for pre-sprint entries that lack the key. Iteration over source_ids uses `break` on first match — no unnecessary registry lookups. `source.requires_legal_review` is a boolean field, no type confusion risk.

**`source_ids` as `set()` in dict** (`investigation_routes.py:241`): Python sets are not JSON-serializable, but this is fine — the investigation store is in-memory only (process-local dict, DEFERRED persistence). If persistence is ever added, this needs serialization handling, but that's future scope.

**Frontend `QueryDeterminismBadge`** (`EvidenceEnvelopePanel.tsx:39-46`): `determinism.replace(/_/g, ' ')` is safe — operates on a string from the API, rendered via JSX auto-escaping. The `DETERMINISM_COLORS` lookup with `??` fallback prevents undefined access. Feature flag gate prevents rendering when disabled.

**Frontend legal review warning** (`InvestigationPage.tsx:137-144`): Double-gated: `isEnabled('CYCLE_017_REGISTRY_SCHEMA') && investigation.has_legal_review_requirement`. Static text, no user input interpolation. `ShieldAlert` icon is from lucide-react (trusted).

**Seed data** (`sources.json`): All new sources have valid enum values (verified by `validate()` in test). `private_leak_source` correctly has `receipt_mode_minimum: "witness_quorum"` (not `http_transcript`), `resolution_role: "secondary_corroboration"` (not primary), and `settlement_eligible: false`. Good threat modeling.

**No new API endpoints**: This sprint modifies existing evidence POST behavior and investigation GET response. No new routes. Attack surface unchanged.

## Zero findings. Ship it.
