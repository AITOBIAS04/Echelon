# Sprint 17 (local sprint-4) — Security & Quality Audit

## Result: AUDIT_APPROVED

### Findings

| ID | Severity | Category | Description | Status |
|----|----------|----------|-------------|--------|
| SEC-17-001 | LOW | Input Validation | `PromptLoader` uses `str.format()` — diff content with `{...}` braces could cause KeyError. Mitigated by prompts using `{{` for literal braces. | Advisory |
| SEC-17-002 | INFO | API Key Handling | Anthropic API key passed directly to client constructor — standard pattern, not logged. | Pass |
| SEC-17-003 | LOW | Resource Usage | `_call_llm` retry flag prevents unbounded retry loops. Max 2 calls per `_call_llm` invocation, max 3 calls per `_call_llm_json`. | Pass |
| SEC-17-004 | INFO | Determinism | `temperature=0.0` configurable via ScoringConfig — correct for verification scoring. | Pass |

### Quality Checks

- [x] All 85 tests pass
- [x] No hardcoded secrets
- [x] Error handling covers API failures and JSON parse failures
- [x] Return types match ScoringProvider ABC contract
- [x] CalibrationCertificate validates within model constraints (brier [0, 0.5])
- [x] CertificateGenerator math verified against fixture data

### Recommendation

**APPROVED** — No blocking findings. SEC-17-001 is theoretical (prompts already use `{{` escaping) and LOW severity.
