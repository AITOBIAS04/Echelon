# Implementation Report: Sprint 24 (Cycle-012, Sprint 2) -- Resolution + Settlement + Certificate Delivery

> Implementer: Claude Code (Opus 4.6) | Date: 2026-03-03
> Sprint: 2 (global: 24) | Cycle: 012

## Summary

Sprint 2 delivers the complete back half of the Sponsored Theatre lifecycle: OSINT evidence collection during TRADING, Composed Oracle resolution, deterministic settlement, certificate generation with 21 echelon_verify checks, RLMF training data export, sponsor delivery package, echelon_status integration, and the MEDIUM-1 fix.

**Result**: 30 new tests, 83 total service tests, 369 scoped regression tests. All passing.

## Deliverables

| # | Task | File | Status |
|---|------|------|--------|
| 1 | Theatre Evidence Collector | `backend/services/theatre_evidence.py` (NEW) | DONE |
| 2 | Theatre Resolution Engine | `backend/services/theatre_resolution.py` (NEW) | DONE |
| 3 | Certificate Generation Pipeline | `backend/services/certificate_pipeline.py` (NEW) | DONE |
| 4 | RLMF Export Generator | `backend/services/rlmf_export.py` (NEW) | DONE |
| 5 | Sponsor Delivery Package | `backend/services/sponsor_delivery.py` (NEW) | DONE |
| 6 | echelon_status Theatre Integration | `backend/services/theatre_status.py` (NEW) | DONE |
| 7 | MEDIUM-1 Fix | `backend/engines/paradox.py` (MODIFIED) | DONE |
| 8 | Resolution Engine Tests | `backend/services/tests/test_theatre_resolution.py` (NEW) | 10 tests |
| 9 | Certificate Pipeline Tests | `backend/services/tests/test_certificate_pipeline.py` (NEW) | 12 tests |
| 10 | E2E Integration Tests | `backend/services/tests/test_sponsored_theatre_e2e.py` (NEW) | 8 tests |

**Total**: 6 new source files + 1 modified file + 3 test files = 10 files
**New tests**: 30 (target was 25+)

## Test Results

```
Sprint 2 tests:          30 passed, 0 failed
All services/schemas:    83 passed, 0 failed
Scoped regression:      369 passed, 0 failed
Total:                  452 passed, 0 failed
```

## Task Details

### Task 1: Theatre Evidence Collector (`theatre_evidence.py`)

- `EvidenceSnapshot` dataclass: captures theatre_id, collection_timestamp, oracle_output, evidence_bundles, collection_results, source_coverage_pct
- `TheatreEvidenceCollector` class: collect_heartbeat(), get_evidence_history(), get_latest_evidence(), compute_coverage_pct()
- Delegates to RealitySignalProvider.get_signal() for evidence collection
- Stores snapshots in-memory as a time-ordered list
- Source coverage computed as successful_sources / total_committed_sources

### Task 2: Theatre Resolution Engine (`theatre_resolution.py`)

- `TheatreResolutionResult` dataclass: carries theatre_id, oracle_output_id, composite_score, winning_outcome_index/label, evidence_bundle_hash, evidence_snapshots, corroboration_result, counter_signal_results, criterion_scores, source_manifest
- `TheatreResolutionEngine` class: full Composed Oracle pipeline
  - Collects final evidence snapshot
  - CorroborationEngine.evaluate() with provisional 0.7 penalty
  - CounterSignalEvaluator.evaluate() returns all UNAVAILABLE / INTELLIGENCE_GAP
  - Scorer.score() produces OracleOutput with composite_score
  - _determine_winning_outcome() maps to discrete index
- Companies House Theatre thresholds: >= 0.7 -> outcome 0, [0.3, 0.7) -> outcome 1, < 0.3 -> outcome 2
- oracle_output_id format: `{theatre_id}_{epoch_ms}`

### Task 3: Certificate Generation Pipeline (`certificate_pipeline.py`)

- `CalibrationCertificate` dataclass: 16 fields conforming to v1.0.0 schema
- `CertificatePipeline` class: SCHEMA_VERSION = "1.0.0", PROVIDER_VERSION = "012.1"
- generate() builds certificate from TheatreResolutionResult + SettlementReport
- verify() runs all 21 echelon_verify checks:
  1. oracle_output_id present and non-empty
  2. oracle_output_id format: {theatre_id}_{epoch_ms}
  3. composite_score in [0.0, 1.0]
  4. evidence_bundle_hash is valid SHA-256 hex (64 chars)
  5. evidence_bundle_hash recomputable
  6. criteria_breakdown non-empty
  7. Each criterion has criterion, passed, score, detail fields
  8. osint_source_manifest present and non-empty
  9. osint_source_manifest entries have required fields
  10. corroboration_status has minimum_met, penalty_factor, distinct_source_groups
  11. corroboration_status.penalty_factor in [0.0, 1.0]
  12. counter_signal_results has exactly 11 entries
  13. Each counter-signal result has signal_class, outcome, detail
  14. verification_tier is known value (UNVERIFIED, BACKTESTED, VERIFIED)
  15. scored_at is valid ISO 8601
  16. provider_version present and non-empty
  17. settlement_hash is valid SHA-256 hex
  18. commitment_hash is valid SHA-256 hex
  19. winning_outcome is valid index
  20. schema_version matches "1.0.0"
  21. Certificate JSON is deterministically re-serialisable (canonical JSON roundtrip)
- corroboration_status: minimum_met=False, penalty_factor=0.7, distinct_source_groups=1
- counter_signal_results: exactly 11 entries, all UNAVAILABLE / INTELLIGENCE_GAP
- verification_tier: UNVERIFIED (BACKTESTED requires 50+ replays)

### Task 4: RLMF Export Generator (`rlmf_export.py`)

- `MarketEpoch`, `AgentTrace`, `CalibrationMetrics`, `RLMFExport` dataclasses
- `RLMFExportGenerator` class: SCHEMA_VERSION = "2.0.1"
- Brier score: (1/n) * sum((p_i - o_i)^2) where o_i = 1 if i == winning else 0
- ECE: expected calibration error across probability bins
- Per-agent P&L from settlement report
- Epochs capture prices and x_vector per tick
- Agent traces capture per-agent decision traces and P&L

### Task 5: Sponsor Delivery Package (`sponsor_delivery.py`)

- `SponsorDeliveryPackage` dataclass: theatre_id, certificate (dict), evidence_bundle (dict), rlmf_export (dict), commitment_hash, echelon_status_url
- `SponsorDeliveryAssembler` class: assembles all 4 deliverables
- Evidence artefact includes: source_manifest, collection_timestamps, http_receipts, evidence_bundle_count, source_coverage_pct
- echelon_status_url: `echelon://status/{theatre_id}`

### Task 6: echelon_status Theatre Integration (`theatre_status.py`)

- `TheatreStatusSnapshot` dataclass: extends MarketStatusSnapshot with theatre-specific fields
- Base fields: theatre_id, market_phase, current_prices, total_trades, etc.
- Theatre extensions: evidence_coverage_pct, sources_online/total, certificate_state, composite_score, counter_signal_status, verification_tier
- Cache: cached_at, ttl_seconds (300)
- builder function: build_theatre_status()
- During TRADING: returns prices, evidence coverage, source status
- After SETTLEMENT: returns VALID certificate state, composite score, counter-signal status
- No modifications to backend/engines/status.py

### Task 7: MEDIUM-1 Fix (`paradox.py`)

- Added None guard in ParadoxEngine.scan() after get_signal():
  ```python
  if signal.p_reality is None:
      return None
  ```
- Minimal change -- LogicGapCalculator.compute() NOT modified
- Guards against TypeError when LiveOSINTRealityProvider returns stale signal
- All existing Paradox Engine tests still pass

## Acceptance Criteria Verification

- [x] Evidence collector runs against mock WM fixtures during TRADING phase
- [x] Evidence stored in Theatre evidence store with collection timestamps
- [x] Resolution engine evaluates Composed Oracle at resolution_date
- [x] Oracle evaluation returns discrete winning_outcome_index for 3-outcome market
- [x] Composite score computed with provisional corroboration (0.7 penalty)
- [x] Counter-signal scaffolding: all 11 UNAVAILABLE / INTELLIGENCE_GAP
- [x] Market transitions: TRADING -> RESOLVING -> SETTLED
- [x] Settlement satisfies bounded-loss invariant: market_maker_pnl >= -b*ln(n)
- [x] Each agent's payout equals winning shares held
- [x] Certificate conforms to v1.0.0 schema (16 fields)
- [x] Certificate passes all 21 echelon_verify checks
- [x] RLMF export conforms to schema v2.0.1
- [x] RLMF captures probability distributions per epoch, agent traces, Brier/ECE
- [x] Sponsor delivery package contains 4 deliverables
- [x] echelon_status returns live state during TRADING
- [x] echelon_status returns VALID certificate post-settlement
- [x] End-to-end test passes: full lifecycle
- [x] E2E test produces >20 stub agent trades across 6 agents
- [x] MEDIUM-1 fix: p_reality=None guard in ParadoxEngine.scan()
- [x] No modifications to backend/market/ modules
- [x] No modifications to backend/osint/ modules
- [x] All tests use mock HTTP responses only
- [x] 30 new Sprint 2 tests pass (target: 25+)
- [x] Scoped regression: 369 tests pass

## Constraint Compliance

| Constraint | Status |
|-----------|--------|
| Zero modifications to backend/market/ | PASS |
| Zero modifications to backend/osint/ | PASS |
| Only backend/engines/paradox.py modified | PASS (MEDIUM-1 fix only) |
| Python 3.9.6 compatibility | PASS (from __future__ import annotations) |
| No new runtime dependencies | PASS |
| In-memory only | PASS |
| Mock-only OSINT testing | PASS |
