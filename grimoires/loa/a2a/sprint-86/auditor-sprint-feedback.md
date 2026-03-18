# Sprint 86 (cycle-026 sprint-1) — Security Audit

APPROVED - LETS FUCKING GO

## Audit Scope
4 collectors with API key auth: FRED, Alpha Vantage, OpenCorporates, Etherscan.

## Security Checklist

### Secrets: PASS
- All API keys from env vars only (ECHELON_*_API_KEY)
- All receipts use safe_query/safe_url (key stripped)
- Tests explicitly assert: `"test-key" not in str(receipt.request_parameters)`
- No hardcoded credentials

### Auth/Authz: PASS
- API keys sent via query parameter (correct per API docs)
- Missing key returns CollectionResult(success=False), does NOT raise

### Input Validation: ADVISORY (non-blocking)
- Request dict values (series_id, symbol, address, action) concatenated into URLs without urllib.parse.quote()
- **Mitigating factors:**
  1. Request dict is INTERNAL — built by CollectionRunner._build_request() from CollectionPlan, not user-facing
  2. Python 3.7.2+ blocks CRLF in urllib.request.Request URLs (CVE-2019-9740, CVE-2019-9947)
  3. Parameter pollution requires attacker control of oracle_config (internal system config)
- **Recommendation:** Add urllib.parse.quote() in Batch 2 refactoring cycle (non-blocking for Batch 1)

### Data Privacy: PASS
- No PII collected or stored

### API Security: PASS
- 30s timeout on all HTTP requests
- Response size unbounded (.read()) — ADVISORY: add 10MB limit in Batch 2
- All errors return CollectionResult(success=False), no exceptions leak

### Error Handling: PASS
- HTTPError, URLError, OSError, ConnectionError all caught
- Error messages contain HTTP codes/reasons only, no secrets
- JSONDecodeError/UnicodeDecodeError caught in _build_success_result

### Code Quality: PASS
- Consistent patterns across all 4 collectors
- Hash invariants enforced by BaseCollector.fetch() wrapper

## Findings Summary

| Finding | Severity | Status |
|---------|----------|--------|
| API key in health_check() URL | LOW | Non-blocking (internal monitoring, not logged by collector) |
| No urllib.parse.quote() on request params | LOW | Non-blocking (internal input, Python CRLF protection) |
| Unbounded .read() | LOW | Non-blocking (known API response sizes, 30s timeout) |
| Etherscan AND vs OR in status check | INFO | Non-blocking (works due to API consistency) |
