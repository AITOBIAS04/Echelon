# Sprint 86 (cycle-026 sprint-1) — Engineer Feedback

All good (with noted concerns)

Sprint 1 has been reviewed and approved. All acceptance criteria met.

## Acceptance Criteria Verification

| Criterion | Status |
|-----------|--------|
| FREDCollector: _fetch() + health_check() | PASS |
| AlphaVantageCollector: _fetch() + health_check() | PASS |
| OpenCorporatesCollector: _fetch() + health_check() | PASS |
| EtherscanCollector: _fetch() + health_check() | PASS |
| 12 tests pass (3 per collector) | PASS |
| API keys redacted from all receipts | PASS |
| `npm run build` passes | PASS |

Documentation verification: N/A (backend collectors, no user-facing docs required)

## Security Verification

- API keys sourced from env vars only (ECHELON_*_API_KEY pattern)
- All receipts use `safe_query` / `safe_url` (key stripped)
- Tests explicitly assert key not in receipt: `assert "test-key" not in str(result.bundle.receipt.request_parameters)`
- No hardcoded credentials found
- Error messages contain only HTTP codes/reasons, no secrets

## Adversarial Analysis

### Concerns Identified (3)

1. `backend/osint/collectors/etherscan.py:169` — Status check uses `status != "1" and message != "OK"` (AND). Semantically should be OR, but Etherscan API sets both consistently, so this works in practice. Minor clarity issue.

2. `backend/osint/collectors/fred.py`, `alpha_vantage.py`, `opencorporates.py`, `etherscan.py` — `_build_success_result()` methods are 89-98 lines each. Exceeds 50-line guideline but justified by JSON parsing + hash computation + EvidenceBundle construction. The complexity is inherent, not accidental.

3. `backend/osint/collectors/alpha_vantage.py` — Rate limit detection relies on `"Note"` or `"Information"` keys in response JSON. If Alpha Vantage changes their rate limit response format, this would silently pass as a normal response with empty time series (caught by the "No time series" check downstream).

### Assumptions Challenged (1)

- **Assumption**: GeoPoint(0, 0, 20000000) is appropriate for global financial data sources (Alpha Vantage, OpenCorporates, Etherscan).
- **Risk if wrong**: If theatre geo-filtering is implemented, global GeoPoints would match every theatre.
- **Recommendation**: Acceptable. These are genuinely global data sources. Theatre filtering should use source_group, not geo.

### Alternatives Not Considered (1)

- **Alternative**: Use `httpx` (async-native HTTP) instead of `urllib.request` in thread pool.
- **Tradeoff**: Would eliminate thread pool overhead but add a dependency. Current pattern matches existing CompaniesHouseCollector.
- **Verdict**: Current approach justified — consistency with existing codebase outweighs performance gains.

Concerns documented but non-blocking. See Adversarial Analysis above.
