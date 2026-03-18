# Sprint 85 (cycle-026 sprint-0) — Engineer Feedback

All good (with noted concerns)

Sprint 0 has been reviewed and approved. All acceptance criteria met.

## Acceptance Criteria Verification

| Criterion | Status |
|-----------|--------|
| 4 source_group values added (37 total) | PASS |
| 10 entries in sources.json (16 total, v0.5.0) | PASS |
| `build_collector_map()` returns 14 collectors | PASS |
| 5 tests pass | PASS |
| `npm run build` passes | PASS |

Documentation verification: N/A (no new commands, no CHANGELOG required for registry scaffold)

## Adversarial Analysis

### Concerns Identified (3)

1. `backend/osint/collectors/collector_map.py:32-52` — All 14 collectors instantiated eagerly at import time. If any collector constructor fails (e.g. malformed env var), the entire map fails. Low risk since constructors only read env vars with empty-string defaults.

2. `backend/osint/sources.json` — Two source_groups (`geospatial`, `event_data`) have no Batch 1 collectors. PRD states these are forward-provisioned for Batch 2+. Acceptable but could drift if Batch 2 never ships.

3. `backend/osint/collectors/collector_map.py:34-36` — WorldMonitor source_ids (`worldmonitor_cii`, `worldmonitor_finance`) use domain-internal naming that differs from sources.json `source_id` field values. Inconsistency is pre-existing (not introduced by this cycle).

### Assumptions Challenged (1)

- **Assumption**: All 10 new collectors can use `MeasureType.SECTOR_RISK_SCORE` as a general-purpose measure type.
- **Risk if wrong**: If the convergence scorer expects domain-specific MeasureTypes for cross-domain weighting, all Batch 1 signals will be treated identically.
- **Recommendation**: Acceptable for Batch 1. Document as tech debt for convergence scorer integration.

### Alternatives Not Considered (1)

- **Alternative**: Lazy collector instantiation (factory pattern) instead of eager `build_collector_map()`.
- **Tradeoff**: Would defer import errors to first use (harder to debug) but prevent startup failures from broken collectors.
- **Verdict**: Current approach is justified — fail-fast at startup is correct for an evidence pipeline.

Concerns documented but non-blocking. See Adversarial Analysis above.
