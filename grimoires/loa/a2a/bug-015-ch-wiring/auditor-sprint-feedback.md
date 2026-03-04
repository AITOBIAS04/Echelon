# Security Audit — bug-015-ch-wiring

**Auditor**: Paranoid Cypherpunk Auditor
**Date**: 2026-03-04
**Verdict**: APPROVED - LETS FUCKING GO

## Files Audited

| File | Lines | Risk |
|------|-------|------|
| `backend/osint/engine/collection_runner.py` | 175 | Low |
| `backend/osint/__init__.py` | 71 | None |
| `backend/osint/tests/conftest.py` | 46 (relevant) | None |
| `backend/osint/tests/test_e2e_corroboration.py` | 127 | None |
| `backend/osint/tests/test_collection_runner.py` | 343 | None |
| `backend/osint/tests/test_env_gating.py` | 49 | None |

## Security Checklist

| Check | Status |
|-------|--------|
| Secrets/Credentials | PASS — no hardcoded secrets. `api_key="test-key"` is test-only fixture |
| Input validation | PASS — `source_params` sourced from internal `oracle_config`, not user-controllable |
| Key override via source_params | PASS — `request.update(extra)` could theoretically override `theatre_id` in request dict, but: (a) `oracle_config` is internal, (b) `theatre_id` is also passed as separate named arg to `collector.fetch()`, (c) collectors use the named param for routing, not the dict key |
| Injection via source_params | PASS — `company_number` flows to URL path in CH collector (pre-existing, audited in sprint-32). `source_params` origin is internal config, not external input |
| SSRF | PASS — no new network endpoints introduced. Collector base URLs unchanged |
| Auth | PASS — no auth changes |
| Error handling | PASS — existing exception handlers preserved unchanged |
| Data privacy | PASS — company numbers are public identifiers, no PII |
| Test isolation | PASS — all new tests mock-only, live tests properly gated |
| Env var hardening | PASS — gating narrowed from "any non-empty string" to explicit `("1", "true", "yes")`. Strictly more secure |

## Informational Notes

1. `source_params` is passed through from `oracle_config` without schema validation. Currently safe because `oracle_config` is internal. If `oracle_config` ever accepts user-supplied fields, add a whitelist of allowed `source_params` keys per source_id.

2. `collection_runner.py:12` has unused `Optional` import — pre-existing, not introduced by this fix.

## Approval

APPROVED - LETS FUCKING GO
