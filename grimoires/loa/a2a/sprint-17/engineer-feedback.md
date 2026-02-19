# Sprint 17 (local sprint-4) — Review Feedback

## Result: All good

### Review Summary

Code quality is solid across all deliverables:

- **AnthropicScorer**: Clean separation of LLM call logic (`_call_llm`, `_call_llm_json`), proper retry with stricter prompt on JSON parse failure, markdown fence stripping covers the common LLM response patterns
- **PromptLoader**: Simple and effective — filesystem-backed, cached, uses `str.format()` for placeholder filling
- **CertificateGenerator**: Deterministic aggregation math, proper validation (empty scores, zero weights), Brier formula correct per SDD
- **Tests**: 19 tests with full mock coverage of Anthropic API, no live calls needed. Certificate tests verify exact numeric results against known fixture data

### Observations

- No security concerns — API key is injected via config, never logged
- `PromptLoader` reads `manifest.json` at construction time which is fine for a long-lived scorer instance
- The `_call_llm_json` retry path correctly limits to one retry (no unbounded recursion)
- Rounding to 6 decimal places in CertificateGenerator prevents floating point drift in certificates

All acceptance criteria for tasks 4.1–4.5 are met.
