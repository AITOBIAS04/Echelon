# PRD: WorldMonitor OSINT Integration — Live Evidence Pipeline + Convergence Signals

**Cycle**: 011
**Version**: 1.0
**Date**: 2026-03-03
**Predecessor**: Cycle-010b (Butterfly, Paradox, Entropy engines, heartbeat scheduler, VRF, Base Sepolia)

---

## 1. Problem Statement

Cycle-010b delivered the full engine stack — Butterfly records causal state, Entropy decays stability, Paradox polices integrity via Logic Gap — but its `RealitySignalProvider` reads from existing pipeline output or deterministic scorers. No live OSINT feeds. The `p_reality` signal that drives the Paradox Engine's integrity policing has no connection to real-world evidence. Markets are policed against stubs, not data.

Without a live evidence layer, the integrity loop is incomplete: the Paradox Engine can detect divergence between market-implied probability and reality probability, but "reality probability" is a placeholder. The engine stack is architecturally sound but empirically blind.

> Sources: echelon_cycle_011.md:12-16

---

## 2. Vision

After Cycle-011, Echelon has a live evidence layer: WorldMonitor fetches real-world signals (country instability, market anomalies, maritime AIS), Echelon's collection runner produces evidence bundles with HTTP transcript receipts, the corroboration engine enforces source independence (WM endpoints share one `independence_upstream_id` so corroboration remains provisional until non-WM collectors land), the scorer assembles confidence-weighted composites with an appropriate penalty for uncorroborated evidence, and `composite_score` flows into the Paradox Engine's `RealitySignalProvider` as live `p_reality`. The integrity loop closes — markets are policed against real-world data, not stubs.

> Sources: echelon_cycle_011.md:14-16

---

## 3. Goals & Success Metrics

### 3.1 Primary Goals

1. **Evidence Pipeline Core**: `BaseCollector` ABC defining the fetch-to-receipt contract. WorldMonitor collector implementing all three domain endpoints (CII, market snapshot, maritime anomaly).
2. **Canonical Hashing**: Echelon Canonical JSON v0 (not RFC 8785) with SHA-256 content hashing and HTTP transcript receipt generation.
3. **Collection Orchestration**: Concurrent collector execution per Theatre `oracle_config` with per-collector timeout and partial failure tolerance.
4. **Corroboration Engine**: Source independence enforcement via `independence_upstream_id` deduplication. Provisional corroboration in 011 (WM-only = always unmet).
5. **Scoring Pipeline**: Confidence-weighted composite score with corroboration bonus, counter-signal penalty, and evidence completeness factor.
6. **Live Paradox Wiring**: `LiveOSINTRealityProvider` replacing 010b's stub, feeding `composite_score` as `p_reality` into the Paradox Engine without modifying Paradox Engine code.
7. **Geographic Convergence**: Multi-domain signal co-location detection in 1 deg x 1 deg cells, producing auditable convergence alerts with full provenance.

### 3.2 Success Metrics

| Metric | Target |
|--------|--------|
| Sprint 1 new tests | 20+ |
| Sprint 2 new tests | 20+ |
| Scoped regression | 0 failures in `backend/market/`, `backend/engines/`, `backend/scoring/`, `backend/osint/` |
| Paradox Engine modifications | 0 (provider swap only) |
| Market module modifications | 0 |
| Evidence bundle provenance | Every bundle carries verifiable HTTP transcript receipt |
| Corroboration status | Provisional (WM-only, correctly penalised) |

### 3.3 Regression Baseline

The regression target is scoped to four module paths:

```
python3 -m pytest backend/market/ backend/engines/ backend/scoring/ backend/osint/ -v
```

The 29 `theatre/` collection errors are pre-existing (Cycle-031-033 import issues) and **excluded** from 011's regression baseline. Everything in the four scoped directories must pass. Everything outside is not this cycle's concern.

> Sources: User discovery answer #3

---

## 4. Functional Requirements

### 4.1 Evidence Models

**File**: `backend/osint/models/evidence.py`

`CollectionResult` dataclass — output of a single collector fetch with `source_id`, `bundle` (EvidenceBundle), `raw_payload` (exact response bytes), `fetch_duration_ms`, `success`, `error`, `retrieved_at`.

`EvidenceBundle`, `HTTPTranscriptReceipt`, `NormalisedEvent`, `NormalisedMeasure`, and `GeoPoint` are imported and re-exported from `worldmonitor_api_contract.py`. No model duplication — the API contract is the single source of truth for bundle shapes.

> Sources: echelon_cycle_011.md:98-113

### 4.2 Canonical Hashing

**File**: `backend/osint/canonical.py`

Three functions:
- `canonical_json(obj)` — Echelon Canonical JSON v0: sorted keys, compact separators, UTF-8 (no ASCII escapes). NOT full RFC 8785 (JCS). Re-exported from API contract.
- `compute_content_hash(raw_payload: bytes)` — SHA-256 of raw response bytes. Hashes bytes, NOT parsed/re-serialised JSON. New in Echelon wrapper (distinct from API contract's dict-hashing version).
- `compute_receipt_hash(method, url, query, headers, body_hash)` — SHA-256 of canonical HTTP transcript per Echelon transcript spec v1.0. Re-exported from API contract.

Tests assert output equality between re-exported wrappers and API contract originals (for `canonical_json` and `compute_receipt_hash`). `compute_content_hash` is intentionally different (bytes vs dict) — no equality assertion.

> Sources: echelon_cycle_011.md:116-138

### 4.3 BaseCollector ABC

**File**: `backend/osint/collectors/base.py`

Abstract base class defining the fetch-to-receipt contract:
- `source_id() -> str` — Registry source_id this collector is authoritative for
- `fetch(request, theatre_id) -> CollectionResult` — Must produce valid EvidenceBundle with HTTP transcript receipt. Must NOT raise — returns `CollectionResult` with `success=False` on failure.
- `health_check() -> HealthStatus` — Returns HEALTHY, DEGRADED, or UNAVAILABLE

Two hash invariants enforced at the base class level:
1. `receipt.content_hash == SHA256(raw_payload)` — hashes exact response bytes
2. `receipt.receipt_hash == compute_receipt_hash(method, url, query, headers, body_hash)` — hashes canonical HTTP transcript

> Sources: echelon_cycle_011.md:142-168

### 4.4 WorldMonitor Collector

**File**: `backend/osint/collectors/worldmonitor.py`

`WorldMonitorConfig` dataclass: `base_url` (default `http://localhost:8080`), `timeout_s` (30.0), `version` ("v0.1.0"), `retry_count` (2), `retry_delay_s` (1.0).

`WorldMonitorCollector(BaseCollector)` — three-domain collector:
- `INTELLIGENCE` calls `POST /api/v1/intelligence/cii` (source_id: `worldmonitor_cii`)
- `MARKET` calls `POST /api/v1/market/snapshot` (source_id: `worldmonitor_finance`)
- `MARITIME` calls `POST /api/v1/maritime/anomaly` (source_id: `worldmonitor_maritime`)

Produces `EvidenceBundle` with `HTTPTranscriptReceipt`, `NormalisedEvent`, and correct `source_group` mapping. Three collector instances per Theatre (one per WM domain), configured via Theatre `oracle_config`.

**Failure mode pinning:**

| Condition | Collector Behaviour | Pipeline Effect |
|-----------|-------------------|-----------------|
| HTTP 200 | Normal: `CollectionResult` with `success=True` | Evidence enters corroboration/scoring |
| HTTP 5xx | Retry up to `retry_count` with `retry_delay_s`. All retries fail: `success=False` | Source counted as intelligence gap. `evidence_completeness` drops. |
| Connection refused / DNS failure | Same retry, `health_check()` returns `UNAVAILABLE` | Same as 5xx. All 3 WM unreachable: `evidence_completeness = 0.0`. |
| Timeout (> `timeout_s`) | Single attempt timeout, then retry | Same as 5xx |
| All WM endpoints down | All 3 `CollectionResult` have `success=False` | `evidence_completeness = 0.0`. Paradox activation gate never fires. Theatre continues trading (Entropy decays, Butterfly records), but Paradox dormant. |

**Key invariant:** WM being down does NOT cause spurious circuit breakers. The activation gate latch requires `evidence_completeness >= threshold` before Logic Gap scanning begins.

**Staleness protection:** `LiveOSINTRealityProvider` includes `max_staleness_s` (default 300s). If the most recent `OracleOutput.scored_at` is older than `max_staleness_s`, `get_signal()` returns `RealitySignal` with `p_reality = None`, causing the Paradox Engine to skip that scan.

> Sources: echelon_cycle_011.md:170-224

### 4.5 Registry Loader

**File**: `backend/osint/models/registry.py`

`RegistryLoader` — loads and queries the OSINT source registry JSON:
- `get_source(source_id) -> RegistrySource | None`
- `get_sources_by_group(source_group) -> list[RegistrySource]`
- `get_sources_by_domain(wm_domain) -> list[RegistrySource]`
- `get_settlement_eligible() -> list[RegistrySource]`
- `validate() -> list[str]` — structural validation (enum membership, invariant checks)

### 4.6 Registry Source Alignment

Three WorldMonitor source entries in registry v0.3.2 must carry:

| source_id | source_group | resolution_role | world_monitor_domain | independence_upstream_id | receipt_mode_minimum |
|-----------|-------------|----------------|---------------------|------------------------|---------------------|
| `worldmonitor_cii` | `alt_data_behavioural` | `primary_evidence` | `intelligence` | `worldmonitor` | `http_transcript` |
| `worldmonitor_finance` | `market_data` | `primary_evidence` | `market` | `worldmonitor` | `http_transcript` |
| `worldmonitor_maritime` | `maritime_ais` | `primary_evidence` | `maritime` | `worldmonitor` | `http_transcript` |

**Critical: shared `independence_upstream_id`.** All three WM endpoints share `independence_upstream_id: worldmonitor` because WorldMonitor is a single aggregator. Despite distinct `source_group` values, they are not independent corroborators. The corroboration engine's `independence_upstream_dedupe_runner` collapses them to a single entry before counting distinct groups.

Sprint 1 verifies alignment and patches registry JSON if misaligned.

> Sources: echelon_cycle_011.md:226-238

### 4.7 Collection Runner

**File**: `backend/osint/engine/collection_runner.py`

`CollectionPlan` dataclass: `theatre_id`, `sources` (source_ids), `evaluation_window`, `geo` (optional GeoPoint), `timeout_s`.

`CollectionRunner`:
- `collect(plan) -> list[CollectionResult]` — runs all collectors concurrently via `asyncio.gather()` with per-collector timeout. Failed fetches return `CollectionResult` with `success=False`. Does NOT raise on individual failure.
- `build_plan(oracle_config, theatre_id) -> CollectionPlan` — derives plan from Theatre oracle configuration. Filtered to WorldMonitor sources only in 011.

> Sources: echelon_cycle_011.md:240-269

### 4.8 Corroboration Engine

**File**: `backend/osint/engine/corroboration.py`

`CorroborationResult` dataclass: `theatre_id`, `primary_bundles`, `corroborating_bundles` (deduplicated), `distinct_source_groups`, `corroboration_minimum`, `corroboration_met`, `dedup_log` (audit trail).

`CorroborationEngine`:
- `evaluate(results, oracle_config) -> CorroborationResult` — separates primary from secondary by `resolution_role`, deduplicates by `independence_upstream_id`, counts distinct `source_groups`, evaluates `corroboration_minimum_met`.
- `deduplicate_by_upstream_id(bundles) -> list[EvidenceBundle]` — collapses bundles sharing `independence_upstream_id`, keeping strongest-confidence entry.

**011 constraint — provisional corroboration:** All three WM endpoints share `independence_upstream_id: worldmonitor`. After deduplication, only one entry remains, so `corroboration_minimum_met` is **always false** in 011. The scorer applies a 0.7 corroboration factor, reducing `composite_score`. This is correct — WorldMonitor is an aggregator, not three independent sources. When future collectors land (Companies House, SEC EDGAR), `corroboration_minimum_met` can become true and the penalty lifts.

> Sources: echelon_cycle_011.md:365-403

### 4.9 Counter-Signal Evaluator

**File**: `backend/osint/engine/counter_signal.py`

`CounterSignalOutcome` enum: ABSENT, PRESENT_DISCOUNTED, PRESENT_UNEXPLAINED, UNAVAILABLE.

`CounterSignalResult` dataclass: `signal_class`, `outcome`, `source_id`, `detail`.

`CounterSignalEvaluator`:
- `evaluate(collection_results, oracle_config) -> list[CounterSignalResult]`

**011 scope — scaffolding only:** All 11 counter-signal classes return `UNAVAILABLE` with `allow_gap=true`. The evaluator interface, discount rule engine, and outcome classification are fully implemented and tested against synthetic fixtures. Each UNAVAILABLE result is classified as `INTELLIGENCE_GAP` (consistent with AC-1 GapKind semantics from Cycle-004) — not `ABSENT`. The `counter_signal_checked` criterion passes honestly under gap tolerance. Three classes documented as first targets for future independent sources: `infrastructure_outage`, `weather`, `financial_distress`.

> Sources: echelon_cycle_011.md:405-443

### 4.10 Scorer

**File**: `backend/osint/engine/scorer.py`

`CriterionScore` dataclass: `criterion`, `passed`, `score`, `detail`.

`OracleOutput` dataclass: `theatre_id`, `composite_score` (0.0-1.0), `criterion_scores`, `evidence_bundles`, `corroboration_result`, `counter_signal_results`, `evidence_completeness`, `bundle_hash`, `scored_at`.

`Scorer`:
- `score(corroboration, counter_signals, oracle_config) -> OracleOutput` — per-criterion evaluation, confidence-weighted average, corroboration bonus, counter-signal penalty, evidence completeness factor, bundle hash via manifest pattern.
- `compute_composite(bundles, corroboration_met, counter_signal_pass) -> float`

**Composite score formula:**
```
composite_score = weighted_mean(bundle.normalised_event.confidence for primary bundles)
                x corroboration_factor (1.0 if met, 0.7 if not)
                x counter_signal_factor (1.0 if pass, 0.5 if fail)
                x evidence_completeness
```

Result clamped to [0.0, 1.0]. Weights derived from registry `priority_bucket`.

**Bundle hash:** `manifest = {bundle.bundle_id: bundle.content_hash for bundle in sorted_bundles}` then `SHA256(canonical_json(manifest))`. Order-independent (sorted by bundle_id) and deterministic.

`composite_score` is the field the Paradox Engine reads as `p_reality` for `osint` source type.

> Sources: echelon_cycle_011.md:445-505

### 4.11 LiveOSINTRealityProvider — Paradox Wiring

**File**: Extend `backend/engines/reality_signal.py` (010b output)

`LiveOSINTRealityProvider(RealitySignalProvider)` — replaces the stub `osint` provider from 010b:
- `get_signal(theatre_id) -> RealitySignal` — full pipeline execution: build CollectionPlan, run CollectionRunner (WM endpoints), corroborate (dedup, enforce minimums), evaluate counter-signals, score (produce composite_score), return RealitySignal with:
  - `p_reality = composite_score`
  - `evidence_bundle_hash = bundle_hash` from OracleOutput (manifest pattern)
  - `oracle_output_id = "{theatre_id}_{scored_at_ms}"` (unique per pipeline run)
  - `provider_version = "011.1"`
  - `source_type = "osint"`

**Integration point:** The `ParadoxEngine` from 010b injects a `RealitySignalProvider`. In 011, Theatres with `logic_gap_source: "osint"` receive a `LiveOSINTRealityProvider` instead of the stub. The Paradox Engine code is unchanged — only the provider implementation changes. This is the seam 010b designed for.

**Activation gate interaction:** `evidence_completeness` from `OracleOutput` maps directly to the `min_evidence_completeness` activation gate in `ParadoxConfig`. When completeness reaches the threshold, the Paradox Engine's activation latch fires and Logic Gap scanning begins.

**Provenance naming:** 010b's provenance ID field is renamed to `oracle_output_id` in 011. No certificate store exists — `oracle_output_id` is a pipeline run identifier with provenance (bundle_hash + scored_at + provider_version), preventing consumers from assuming a certificate store exists while providing audit-grade traceability.

> Sources: echelon_cycle_011.md:507-550

### 4.12 Geographic Convergence Detection

**File**: `backend/osint/engine/convergence.py`

`ConvergenceCell` dataclass: `lat_bin`, `lon_bin`, `event_types` (set of WMDomain values), `events` (NormalisedEvent list), `convergence_score`.

`ConvergenceAlert` dataclass: `alert_id`, `cell`, `theatre_id` (if geo overlaps), `triggered_at`.

`ConvergenceDetector`:
- `detect(bundles) -> list[ConvergenceAlert]` — bin events by 1 deg x 1 deg cell, count distinct WMDomain values per cell, fire alert when distinct types >= `min_event_types` (default 3) within 24-hour window, score by event count and type diversity.
- `match_theatres(alerts, active_theatres) -> list[ConvergenceAlert]` — match alerts to active Theatres by geographic overlap.

**Design rationale:** Echelon's convergence detector operates on evidence bundles that have already passed through the collection-to-receipt pipeline, so convergence alerts carry full provenance — every event has an HTTP transcript receipt.

**011 scope:** Convergence alerts are logged in-process only (no persistence, no MCP surface). They do not trigger automatic Theatre creation — that requires Sponsored Theatre workflow (Cycle-012). After process restart, all alert state is lost (consistent with the no-persistence constraint).

> Sources: echelon_cycle_011.md:552-598

---

## 5. What 010b Delivers (Consumed by This Cycle)

| API | Purpose |
|-----|---------|
| `ButterflyEngine` | Six Wing Flap types and `TimelineState` tracking |
| `EntropyEngine` | Logic Gap-scaled decay rates |
| `ParadoxEngine` | `RealitySignalProvider` interface — reads `p_reality` from `osint` or `deterministic` sources |
| `RealitySignal` dataclass | `p_reality`, `evidence_bundle_hash`, `source_type` |
| `ParadoxConfig` | `logic_gap_source: "osint"` option |
| `HeartbeatScheduler` | PARADOX scan at 30-second cadence |
| `LogicGapReading` | `gap_direction` for audit trail |
| Activation gate | Latch semantics (`min_evidence_completeness`, `min_time_elapsed`) |
| Base Sepolia client | Commitment/settlement proofs |
| VRF provider | Local mode deterministic, testnet opt-in |
| Existing tests | 447+ pipeline + MCP + 45+ market + engine tests passing |

**Key constraint**: No modifications to `backend/engines/paradox.py` — the provider interface is unchanged from 010b. Only the provider implementation changes (LiveOSINTRealityProvider replaces stub). No modifications to `backend/market/` modules.

> Sources: echelon_cycle_011.md:24-36

---

## 6. What Exists (Relevant to This Cycle)

### 6.1 WorldMonitor API Contract (`worldmonitor_api_contract.py`)

- Three domain endpoints: `POST /api/v1/intelligence/cii`, `POST /api/v1/market/snapshot`, `POST /api/v1/maritime/anomaly`
- Registry source IDs: `worldmonitor_cii`, `worldmonitor_finance`, `worldmonitor_maritime`
- Pydantic v2 schemas: `CIIRequest/Response`, `MarketSnapshotRequest/Response`, `MaritimeAnomalyRequest/Response`
- Shared models: `GeoPoint`, `NormalisedMeasure`, `NormalisedEvent`, `EvidenceBundle`, `HTTPTranscriptReceipt`
- Utility functions: `canonical_json()`, `compute_content_hash()`, `compute_receipt_hash()`
- Three passing contract tests

### 6.2 OSINT Composed Oracle Spec v2 (Template #10)

- Three reserved criteria: `corroboration_minimum_met`, `counter_signal_checked`, `rule_change_monitored`
- Source independence taxonomy: 13 source_group enums, `independence_upstream_id` deduplication
- HTTP transcript canonical spec v1.0
- 10 fixtures (6 PASS / 4 FAIL) with synthetic evidence bundles
- Five schema enforcement rules

### 6.3 OSINT Source Registry v0.3.2

- 51 sources, 7 jurisdictions
- 3 WorldMonitor endpoints already catalogued
- 5 WorldMonitor upstream sources flagged (prefer direct integration)
- 9 controlled enums, standalone CLI validator

### 6.4 WorldMonitor Fork (AITOBIAS04/worldmonitor)

- Forked from koala73/worldmonitor (13k stars), AGPL-3.0, v2.5.6
- CII scoring: 4 components (baseline risk, unrest events, security activity, information velocity) with hotspot proximity boost, focal point urgency, conflict-zone floors
- Geographic convergence detection: 1 deg x 1 deg cells, 24-hour window, 3+ distinct event types
- Maritime anomaly detection: AIS density grid, gap detection, dark fleet probability, 8 strategic chokepoints
- Temporal baseline anomaly detection: Welford's online algorithm, 90-day rolling window, z-score thresholds

> Sources: echelon_cycle_011.md:40-84

---

## 7. Testing Strategy

### 7.1 WorldMonitor Deployment Status

WorldMonitor is **NOT running locally**. The WM fork (AITOBIAS04/worldmonitor) has not been cloned or deployed on the development machine. All Cycle-011 tests use **mock HTTP responses only** — no test hits a real WM endpoint.

Mock responses are derived from the Pydantic v2 schemas in `worldmonitor_api_contract.py` and stored as JSON fixtures in `backend/osint/tests/fixtures/`:
- `wm_cii_response.json` — mock CII endpoint response
- `wm_market_response.json` — mock market snapshot response
- `wm_maritime_response.json` — mock maritime anomaly response
- `wm_error_responses.json` — mock error responses (5xx, timeout, malformed)

All fixtures are generated from Pydantic v2 schemas. Collector and runner tests consume these fixtures via `httpx`/`aiohttp` mocking — no real HTTP calls.

Tests marked `@pytest.mark.live_wm` are skipped by default, ready for when WM is eventually deployed. The collector, collection runner, and health check exercise the same code path against mocks as they would against a live instance — the HTTP transcript receipt pipeline is code-path identical.

> Sources: User discovery answer #1

### 7.2 Scoped Regression

The regression target is scoped to four module paths:

```
python3 -m pytest backend/market/ backend/engines/ backend/scoring/ backend/osint/ -v
```

The 29 `theatre/` collection errors (Cycle-031-033 import issues) are pre-existing and excluded from 011's regression baseline. All tests in the four scoped directories must pass. All tests outside those directories are not this cycle's concern.

> Sources: User discovery answer #3

---

## 8. Non-Functional Requirements

### 8.1 Performance
- Collection runner uses `asyncio.gather()` with per-collector timeout
- No leaked asyncio tasks on collection failure
- Convergence detection operates on in-memory evidence bundles, no external queries

### 8.2 Determinism
- Canonical hashing deterministic (sorted keys, compact separators, no ASCII escape)
- Content hash deterministic (SHA-256 of exact response bytes)
- Bundle hash deterministic via manifest pattern (sorted by bundle_id)
- Composite score deterministic (same input bundles + config = same output)

### 8.3 State Isolation
- Each Theatre has its own collection plan, corroboration result, and oracle output
- No cross-Theatre evidence sharing
- Convergence detector bins events per cell, not per Theatre

### 8.4 In-Memory Constraint
- Evidence bundles, corroboration results, scorer output, and convergence alerts are all in-memory
- After process restart, all state is lost (continues 010a/010b pattern)
- No database persistence in 011

### 8.5 Provenance
- Every evidence bundle carries an HTTP transcript receipt
- Receipt hashes are verifiable against raw response bytes
- Bundle hash provides order-independent manifest fingerprint
- `oracle_output_id` provides audit-grade pipeline run traceability without assuming certificate store

---

## 9. Scope Exclusions

- **No non-WM collectors.** Companies House, SEC EDGAR, FRED, ECB, Gazette, INPI RNE collectors are deferred. WorldMonitor is the first and only live collector in 011. The `BaseCollector` pattern is ready for future collectors.
- **No paid source procurement.** No Polygon.io, RavenPack, Dataminr, Spire Global subscriptions.
- **No WorldMonitor deployment.** This cycle assumes WM is available via mock fixtures. WM setup, configuration, and hosting are not in scope.
- **No Theatre Command UI.** No globe rendering, no GeoEvent index, no convergence visualisation.
- **No automatic Theatre creation from convergence.** Convergence alerts log and enrich existing Theatres. Auto-creation requires Sponsored Theatre workflow (Cycle-012).
- **No certificate store.** The pipeline produces `OracleOutput` with `composite_score` directly. `oracle_output_id` is a pipeline run identifier — not a certificate.
- **No agent interaction.** No agent-initiated evidence collection. Collection is pipeline-driven per heartbeat cadence.
- **No `rule_change_monitored` implementation.** Stubbed as always-PASS. Depends on Sponsored Theatre lifecycle (Cycle-012).
- **No database persistence.** All state in-memory (continues 010a/010b pattern).
- **No `witness_quorum` or `signed_receipt` receipt modes.** All WM endpoints use `http_transcript`.
- **AGPL-3.0 compliance not resolved.** Echelon consumes WM via clean API boundary (HTTP). Formal legal review deferred. 011 is local/development only.
- **No real WM HTTP calls in tests.** All tests use mock fixtures derived from Pydantic schemas.

> Sources: echelon_cycle_011.md:663-675, User discovery answers #1-3

---

## 10. Acceptance Criteria

### 10a. Sprint 1 — Evidence Pipeline Core + WorldMonitor Collector

- [ ] `canonical_json()` produces deterministic output (sorted keys, compact separators, no ASCII escape)
- [ ] `compute_content_hash()` and `compute_receipt_hash()` re-exports match API contract originals exactly
- [ ] `BaseCollector` enforces receipt invariants (content_hash = SHA-256 of raw response bytes, receipt_hash = SHA-256 of canonical transcript)
- [ ] WorldMonitor collector calls correct endpoint per domain (CII, market, maritime)
- [ ] WorldMonitor collector produces valid `EvidenceBundle` with `HTTPTranscriptReceipt`
- [ ] WorldMonitor collector handles timeout, HTTP errors, and malformed responses gracefully (no raise)
- [ ] WorldMonitor collector retries on transient failure (configurable count and delay)
- [ ] WorldMonitor health check maps WM `HealthStatus` correctly
- [ ] Registry loader loads v0.3.2 JSON and queries by source_id, source_group, WM domain
- [ ] Registry validation catches enum violations and settlement invariant breaches
- [ ] Collection runner executes collectors concurrently with per-collector timeout
- [ ] Collection runner handles partial failure (1 of 3 fails, other 2 succeed)
- [ ] Collection plan correctly derived from Theatre `oracle_config`
- [ ] 3 WM registry source entries verified aligned with API contract
- [ ] Mock WM response fixtures generated from Pydantic v2 schemas (CII, market, maritime, errors)
- [ ] All tests use mock HTTP responses only — no real WM endpoint calls
- [ ] No modifications to `backend/market/` or `backend/engines/` modules
- [ ] Scoped regression: all tests in `backend/market/`, `backend/engines/`, `backend/scoring/`, `backend/osint/` pass
- [ ] Pre-existing `theatre/` collection errors (29 import failures) excluded from regression baseline
- [ ] 20+ new Sprint 1 tests pass

> Sources: echelon_cycle_011.md:335-353

### 10b. Sprint 2 — Corroboration + Scoring + Paradox Wiring + Convergence

- [ ] Corroboration deduplicates by `independence_upstream_id` correctly (all 3 WM endpoints collapse to 1 entry)
- [ ] `corroboration_minimum_met` evaluates at exact boundary (minimum - 1 = FAIL, minimum = PASS)
- [ ] Provisional corroboration: WM-only = 1 distinct upstream, `corroboration_met=false`, 0.7 penalty applied
- [ ] Counter-signal evaluator returns UNAVAILABLE for all 11 classes in 011 (scaffolding-only)
- [ ] Counter-signal `UNAVAILABLE` with `allow_gap=true` does not cause criterion FAIL
- [ ] Counter-signal `UNAVAILABLE` with `allow_gap=false` causes criterion FAIL
- [ ] UNAVAILABLE classified as INTELLIGENCE_GAP (not ABSENT) per AC-1 GapKind semantics
- [ ] `composite_score` is confidence-weighted, clamped to [0.0, 1.0]
- [ ] Corroboration bonus and counter-signal penalty apply correctly
- [ ] `evidence_completeness` = count(successful sources) / count(required sources)
- [ ] Bundle hash uses manifest pattern, deterministic regardless of insertion order
- [ ] `LiveOSINTRealityProvider.get_signal()` returns `RealitySignal` with `p_reality = composite_score`
- [ ] `RealitySignal.evidence_bundle_hash` matches `OracleOutput.bundle_hash`
- [ ] Paradox Engine receives live `p_reality` without code changes (provider swap only)
- [ ] Activation gate fires when `evidence_completeness` crosses `min_evidence_completeness` threshold
- [ ] Logic Gap = `abs(p_market - p_reality)` computed correctly with live `composite_score`
- [ ] Staleness protection: `max_staleness_s` causes `p_reality = None` when evidence is stale
- [ ] Convergence detector fires alert when 3+ event types co-locate in 1 deg x 1 deg cell within 24 hours
- [ ] Convergence alerts carry full provenance (every event has HTTP transcript receipt)
- [ ] Convergence Theatre matching correctly identifies geographic overlap
- [ ] No modifications to `backend/engines/paradox.py` (provider interface unchanged from 010b)
- [ ] No modifications to `backend/market/` modules
- [ ] All tests use mock HTTP responses only
- [ ] Scoped regression: all tests in `backend/market/`, `backend/engines/`, `backend/scoring/`, `backend/osint/` pass
- [ ] Pre-existing `theatre/` collection errors excluded from regression baseline
- [ ] 20+ new Sprint 2 tests pass

> Sources: echelon_cycle_011.md:637-659

---

## 11. Sprint Architecture

### Sprint 1 — Evidence Pipeline Core + WorldMonitor Collector

```
backend/osint/
+-- __init__.py
+-- canonical.py                        # Echelon Canonical JSON v0 + SHA-256 (NEW)
+-- models/
|   +-- __init__.py
|   +-- evidence.py                     # CollectionResult, re-exports from API contract (NEW)
|   +-- registry.py                     # RegistryLoader, RegistrySource (NEW)
+-- collectors/
|   +-- __init__.py
|   +-- base.py                         # BaseCollector ABC (NEW)
|   +-- worldmonitor.py                 # WorldMonitor collector - 3 domains (NEW)
+-- engine/
|   +-- __init__.py
|   +-- collection_runner.py            # Stage 1: orchestrate fetches per theatre config (NEW)
+-- tests/
    +-- fixtures/
    |   +-- wm_cii_response.json        # Mock CII endpoint response (NEW)
    |   +-- wm_market_response.json     # Mock market snapshot response (NEW)
    |   +-- wm_maritime_response.json   # Mock maritime anomaly response (NEW)
    |   +-- wm_error_responses.json     # Mock error responses (NEW)
    +-- test_canonical.py               # Deterministic hashing tests (NEW)
    +-- test_receipt.py                 # HTTP transcript receipt tests (NEW)
    +-- test_worldmonitor.py            # WM collector: 3 domains, errors, retry (NEW)
    +-- test_collection_runner.py       # Concurrent fetches, timeout, partial failure (NEW)
    +-- test_registry_loader.py         # Registry load, query, validation (NEW)
```

### Sprint 2 — Corroboration + Scoring + Paradox Wiring + Convergence (additions)

```
backend/osint/
+-- engine/
|   +-- corroboration.py                # Stage 2: dedup + minimum enforcement (NEW)
|   +-- counter_signal.py              # Stage 2b: counter-signal evaluation (NEW)
|   +-- scorer.py                       # Stage 3: confidence-weighted composite_score (NEW)
|   +-- convergence.py                  # Geographic convergence detection (NEW)
+-- tests/
    +-- test_corroboration.py           # Dedup, minimum enforcement, audit trail (NEW)
    +-- test_counter_signal.py          # All 4 outcomes via synthetic fixtures (NEW)
    +-- test_scorer.py                  # Composite score, criterion scores, bundle hash (NEW)
    +-- test_convergence.py             # Cell binning, alert firing, theatre matching (NEW)
    +-- test_live_reality.py            # LiveOSINTRealityProvider end-to-end (NEW)
    +-- test_paradox_wiring.py          # Paradox Engine with live p_reality (NEW)

backend/engines/
+-- reality_signal.py                   # Extended: LiveOSINTRealityProvider (MODIFIED)
```

---

## 12. Sprint Task Breakdown

### Sprint 1 Tasks (13 tasks)

1. Evidence models — `CollectionResult` dataclass, re-export bundle shapes from API contract
2. Canonical hashing — Re-export from API contract, add `compute_content_hash(bytes)`, label as Echelon Canonical JSON v0
3. BaseCollector ABC — Abstract base with receipt invariant enforcement
4. WorldMonitor collector — Three-domain collector with error handling and retry
5. Registry loader — Load, query, validate registry JSON
6. Registry alignment check — Verify 3 WM source entries, patch if needed
7. Collection runner — Concurrent fetches, per-collector timeout, partial failure handling
8. Mock WM response fixtures — Generate from Pydantic v2 schemas (CII, market, maritime, errors)
9. Canonical hashing tests — Determinism, edge cases, cross-verification
10. Receipt tests — HTTP transcript canonical form, hash determinism, content hash verification
11. Collector tests — WM collector per domain against mock fixtures, error scenarios, retry
12. Collection runner tests — Concurrent execution, timeout, partial failure, plan derivation
13. Registry loader tests — Load, query, validation, edge cases

### Sprint 2 Tasks (13 tasks)

1. Corroboration engine — Primary/secondary separation, upstream_id dedup, minimum enforcement
2. Counter-signal evaluator — Interface, discount rule engine, all 11 classes return UNAVAILABLE
3. Scorer — Per-criterion evaluation, composite score formula, bundle hash manifest pattern
4. LiveOSINTRealityProvider — Full pipeline execution, provider swap for osint Theatres
5. Paradox wiring — Inject LiveOSINTRealityProvider, verify activation gate interaction
6. Convergence detector — Cell binning, alert threshold, scoring, Theatre matching
7. Corroboration tests — Dedup correctness, minimum enforcement, provisional corroboration
8. Counter-signal tests — All four outcome types, discount rules, allow_gap toggle
9. Scorer tests — Composite score edges, criterion propagation, bundle hash determinism
10. Live reality tests — End-to-end mock pipeline to RealitySignal
11. Paradox wiring tests — Paradox Engine with live p_reality, activation gate, circuit breakers
12. Convergence tests — Cell binning, domain counting, alert threshold, Theatre matching
13. Integration test — Full loop: WM fetch through to Paradox Wing Flap

---

## 13. Dependency Chain

```
Cycle-004 (pipeline hardening)
  -> Cycles 005-006 (registry expansion + live OSINT surfaces)
    -> Cycle-007 (unified Two-Rail pipeline, 447+ tests)
      -> Cycle-008 (MCP verifier + construct calibration)
        -> Cycle-009 (MCP surface, HTTP transport, certificate store)
          -> Cycle-010a (LMSR cost function, market lifecycle, trade execution)
            -> Cycle-010b (Butterfly, Paradox, Entropy engines, heartbeat, VRF, Base Sepolia)
              -> Cycle-011 (WorldMonitor Integration - live evidence pipeline + convergence)  <-- THIS CYCLE
                -> Cycle-012 (Sponsored Theatre E2E)
                -> Cycle-013 (Results Surface)
```

> Sources: echelon_cycle_011.md:679-692

---

## 14. Key Spec References

| Document | Relevance |
|----------|-----------|
| WorldMonitor API Contract (`worldmonitor_api_contract.py`) | Three domain endpoints, Pydantic schemas, EvidenceBundle shape, canonical hashing utilities |
| OSINT Composed Oracle Spec v2 | Three reserved criteria, source independence taxonomy, HTTP transcript canonical spec, 5 enforcement rules |
| OSINT Source Registry v0.3.2 | 51 sources, 3 WM endpoints catalogued, 9 controlled enums, independence_upstream_id |
| Cycle-035 OSINT Pipeline Plan | Architectural reference for three-stage pipeline (Collection -> Corroboration -> Scoring) |
| Echelon System Bible v13 Section XV | Integration architecture, WM consumption via clean API boundary |
| Echelon Paradox Policy Design Note v1.1 | p_reality = composite_score, evidence_completeness gate, activation latch semantics |

> Sources: echelon_cycle_011.md:738-748
