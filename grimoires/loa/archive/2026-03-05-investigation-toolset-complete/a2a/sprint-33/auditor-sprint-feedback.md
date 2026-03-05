# Security Audit — Sprint 33 (local sprint-1)

**Auditor**: Paranoid Cypherpunk Auditor
**Date**: 2026-03-05
**Verdict**: APPROVED - LETS FUCKING GO

## Files Audited

| File | Lines | Risk |
|------|-------|------|
| `backend/investigation/__init__.py` | 1 | None |
| `backend/investigation/models.py` | 33 | None |
| `backend/investigation/evidence_envelope.py` | 147 | Low |
| `backend/investigation/claim_graph.py` | 184 | Low |
| `backend/investigation/tests/test_evidence_envelope.py` | 120 | None |
| `backend/investigation/tests/test_claim_graph.py` | 157 | None |

## Security Checklist

| Check | Status |
|-------|--------|
| Secrets/Credentials | PASS — no hardcoded secrets, no API keys, no env vars read |
| Input validation | PASS — `content` param is bytes (opaque), `evidence_id` is internal sequential, no user-supplied IDs reach hash computation |
| Injection | PASS — no SQL, no shell commands, no string interpolation into executable contexts. `source_description` and `reason_class` are stored as-is but never executed |
| Hash integrity | PASS — SHA-256 via `hashlib.sha256()`, deterministic construction, canonical_json for Merkle tree. No custom crypto, no weak hashes |
| Merkle tree correctness | PASS — canonical_json sorts keys (RFC 8785), claims sorted lexicographically, odd leaf duplication matches §3.7 spec, `model_dump(mode="json")` handles datetime serialisation correctly |
| Immutability enforcement | PASS — Pydantic `frozen=True` on all models, no `delete()` method on EvidenceEnvelope, `_items` and `_redactions` are private lists, properties return copies via `list()` |
| Data privacy | PASS — no PII handling, evidence content hashed immediately (raw bytes not stored on the model), only hash retained |
| Error handling | PASS — `redact()` raises ValueError for unknown evidence_id (fail-fast, no silent corruption), `_find_claim_index()` raises ValueError for unknown claim_id |
| Auth/Authz | N/A — pure data models, no network access, no auth boundaries |
| SSRF | N/A — no network calls |
| DoS | PASS — no unbounded recursion, no blocking I/O, list append is O(1) amortised |

## Informational Notes

1. `get_manifest()` calls `any(r.evidence_id == item.evidence_id for r in self._redactions)` inside a list comprehension over items — O(n*m) where n=items, m=redactions. Not a concern at expected scale (<1000 items per investigation) but worth noting if this ever becomes a hot path.

2. `compute_root_hash()` mutates the `leaves` list in-place during Merkle tree construction. This is safe because `leaves` is a local variable, but worth noting for future readers.

## Approval

APPROVED - LETS FUCKING GO
