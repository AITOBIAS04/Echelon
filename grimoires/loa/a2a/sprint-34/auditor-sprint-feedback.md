# Security Audit — Sprint 34 (local sprint-2)

**Auditor**: Paranoid Cypherpunk Auditor
**Date**: 2026-03-05
**Verdict**: APPROVED - LETS FUCKING GO

## Files Audited

| File | Lines | Risk |
|------|-------|------|
| `backend/investigation/counter_signals.py` | 131 | None |
| `backend/investigation/commitment_monitor.py` | 87 | None |
| `backend/investigation/signal_scanner.py` | 217 | Low |
| `backend/investigation/entity_resolver.py` | 145 | Low |
| `backend/investigation/corroboration_checker.py` | 53 | None |
| `backend/investigation/tests/test_counter_signals.py` | 147 | None |
| `backend/investigation/tests/test_commitment_monitor.py` | 99 | None |
| `backend/investigation/tests/test_signal_scanner.py` | 86 | None |
| `backend/investigation/tests/test_entity_resolver.py` | 103 | None |
| `backend/investigation/tests/test_corroboration_checker.py` | 142 | None |

## Security Checklist

| Check | Status |
|-------|--------|
| Secrets/Credentials | PASS — no hardcoded secrets, no API keys, no env vars read |
| Input validation | PASS — all enum fields constrained by Pydantic typing, `signal_class`/`drift_type`/`domain_filters` all typed to their respective enums |
| Injection | PASS — no SQL, no shell commands, no eval/exec, no string interpolation into executable contexts. `resolution_impact`, `detection_method`, `original_value`, `new_value` stored as-is but never executed |
| Hash integrity | PASS — SHA-256 via `hashlib.sha256()` in signal_scanner and entity_resolver. Both use `canonical_json()` for deterministic serialisation. DeltaBrief hash computed from stable fields (excludes `generated_at`). Profile hash excludes `source_queries` (non-deterministic timestamps). No custom crypto, no weak hashes |
| Immutability enforcement | PASS — all 7 Pydantic models have `frozen=True`. Properties return copies via `list()`. No delete methods on any service class |
| Independence invariant | PASS — `InvestigationCorroborationChecker` enforces ≥2 distinct `upstream_group` for SUPPORTED. No override method, no admin bypass, no conditional skip. Contradiction check evaluates first (correct priority) |
| Access-tier policy | PASS — tier B/C sources recorded as `skipped=True` with explicit `skip_reason`. No mechanism to bypass tier restriction at runtime. Tier sets are module-level constants |
| Data privacy | PASS — no PII handling. Entity resolver returns mock data only. No real personal data stored or transmitted |
| Auth/Authz | N/A — pure data models and in-memory services, no network access, no auth boundaries |
| SSRF | N/A — no network calls, no URL construction, no HTTP requests |
| DoS | PASS — no unbounded recursion, no blocking I/O. All iterations bounded by collection size. `active_source_groups` bounded by 9 domain filters × max 3 groups per filter |

## Informational Notes

1. `_STANDARD_CLASSES` in `counter_signals.py` is defined but not directly referenced in Sprint 2 code. Available for Sprint 3 certificate builder — not a dead code concern.

2. `_build_manifest()` in `signal_scanner.py:196` constructs `resolved` from a set comprehension before `sorted()` — non-deterministic set iteration is neutralised by the sort. Correct approach.

3. `entity_resolver.py` hash dict excludes `source_queries` to avoid non-deterministic timestamps. This is architecturally correct — the hash covers entity identity data, not query operation metadata. Document this design decision for future maintainers (already commented at line 96-97).

## Approval

APPROVED - LETS FUCKING GO
