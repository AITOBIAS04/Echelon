# Security Audit — Sprint 32 (Cycle-015 Sprint 2)

**Auditor**: Paranoid Cypherpunk Auditor
**Date**: 2026-03-04
**Verdict**: APPROVED - LETS FUCKING GO

## Files Audited

| File | Lines | Risk |
|------|-------|------|
| `backend/osint/collectors/companies_house.py` | 262 | Medium |
| `backend/osint/sources.json` | 109 | Low |
| `backend/osint/tests/fixtures/ch_company_profile.json` | 40 | None |
| `backend/osint/tests/test_companies_house.py` | 153 | None |
| `backend/osint/tests/test_corroboration_with_ch.py` | 165 | None |
| `backend/osint/source_manifest.py` | 162 | Low |
| `backend/osint/tests/test_e2e_corroboration.py` | 135 | None |

## Security Checklist

| Check | Status |
|-------|--------|
| Secrets/Credentials | PASS — API key from env var, never logged, never in error messages |
| Auth implementation | PASS — HTTP Basic `base64(key:)`, auth header only (not URL params) |
| SSRF | PASS — base URL hardcoded to official CH API, not user-controllable |
| Path injection | PASS — `company_number` interpolated into URL but internal-only, urllib encodes path, CH API rejects invalid numbers |
| TLS | PASS — HTTPS enforced, stdlib verifies certificates |
| Input validation | PASS — empty company_number and empty API key return failure before HTTP |
| Error handling | PASS — all exceptions → CollectionResult(success=False), no info disclosure |
| Data privacy | PASS — Companies House data is public record, no PII concerns |
| Timeout | PASS — 30s cap on urllib + asyncio.wait_for, no infinite hangs |
| Test isolation | PASS — mock tests patched, live tests gated, no real API calls in CI |
| Registry integrity | PASS — 3 WM entries unchanged, CH has distinct upstream_id |

## Informational Notes

1. `company_number` is interpolated into the URL path without explicit sanitisation. Risk is low because: (a) the value comes from internal request dicts, not user input; (b) `urllib` handles URL encoding; (c) the CH API itself rejects invalid company numbers. If external user input ever flows here, add validation (8-char alphanumeric).

2. `source_manifest.py:157` accesses `self._registry._path` (private attribute). Not a security issue but a coupling concern for future refactoring.

## Approval

APPROVED - LETS FUCKING GO
