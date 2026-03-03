# Cycle-011 — WorldMonitor Integration

**Cycle:** cycle-011
**Name:** WorldMonitor OSINT Integration — Live Evidence Pipeline + Convergence Signals
**Predecessor:** cycle-010b (Butterfly, Paradox, Entropy engines, heartbeat scheduler, VRF, Base Sepolia)
**Location:** `~/Developer/prediction-market-monorepo.nosync`
**Sprint count:** 2
**Tooling:** Claude Code + Loa (`/plan` → `/simstim` → `/run-bridge`)

---

## Cycle Objective

Connect the WorldMonitor fork's three OSINT domain endpoints to Echelon's verification pipeline. Cycle-010b delivered the full engine stack — Butterfly records causal state, Entropy decays stability, Paradox polices integrity via Logic Gap — but its `RealitySignalProvider` reads from existing pipeline output or deterministic scorers. No live OSINT feeds. Cycle-011 changes that.

After 011, Echelon has a live evidence layer: WorldMonitor fetches real-world signals (country instability, market anomalies, maritime AIS), Echelon's collection runner produces evidence bundles with HTTP transcript receipts, the corroboration engine enforces source independence (WM endpoints share one `independence_upstream_id` so corroboration remains provisional until non-WM collectors land), the scorer assembles confidence-weighted composites with an appropriate penalty for uncorroborated evidence, and `composite_score` flows into the Paradox Engine's `RealitySignalProvider` as live `p_reality`. The integrity loop closes — markets are policed against real-world data, not stubs.

**Key constraint:** This cycle integrates WorldMonitor's three existing API endpoints (CII, market snapshot, maritime anomaly) as defined in `worldmonitor_api_contract.py`. It does not build all eight collectors from the Cycle-035 pipeline plan — Companies House, SEC EDGAR, FRED, and other free sources are deferred. WorldMonitor is the first live collector; the pattern it establishes (BaseCollector → EvidenceBundle → Corroboration → Scoring) is reused by all future collectors.

**WM deployment status: not running locally.** The WorldMonitor fork (AITOBIAS04/worldmonitor) has not been cloned or deployed on the development machine. All Cycle-011 tests use **mock HTTP responses only** — no test hits a real WM endpoint. Mock responses are derived from the Pydantic v2 schemas in `worldmonitor_api_contract.py` and stored as JSON fixtures in `backend/osint/tests/fixtures/`. Tests marked `@pytest.mark.live_wm` (skipped by default) exist for future integration testing once WM is deployed. The collector, collection runner, and health check are all designed to work against the mock fixtures identically to how they would work against a live instance — the HTTP transcript receipt pipeline exercises the same code path either way.

---

## What 010b Delivers (Consumed by This Cycle)

- `ButterflyEngine` with six Wing Flap types and `TimelineState` tracking
- `EntropyEngine` with Logic Gap–scaled decay rates
- `ParadoxEngine` with `RealitySignalProvider` interface — reads `p_reality` from `osint` or `deterministic` sources
- `RealitySignal` dataclass with `p_reality`, `evidence_bundle_hash`, `source_type` (010b's provenance ID field is renamed to `oracle_output_id` in 011 — see Paradox Wiring section)
- `ParadoxConfig` with `logic_gap_source: "osint"` option (reads `composite_score` from pipeline output)
- `HeartbeatScheduler` driving PARADOX scan at 30-second cadence
- `LogicGapReading` with `gap_direction` for audit trail
- Activation gate with latch semantics (`min_evidence_completeness`, `min_time_elapsed`)
- Base Sepolia client for commitment/settlement proofs
- VRF provider (local mode deterministic, testnet opt-in)
- All existing tests passing (447+ pipeline + MCP + 45+ market + engine tests)

---

## What Exists (Relevant to This Cycle)

**WorldMonitor API Contract (`worldmonitor_api_contract.py`):**
- Three domain endpoints: `POST /api/v1/intelligence/cii`, `POST /api/v1/market/snapshot`, `POST /api/v1/maritime/anomaly`
- Registry source IDs: `worldmonitor_cii`, `worldmonitor_finance`, `worldmonitor_maritime`
- Pydantic v2 schemas: `CIIRequest/Response`, `MarketSnapshotRequest/Response`, `MaritimeAnomalyRequest/Response`
- Shared models: `GeoPoint`, `NormalisedMeasure`, `NormalisedEvent`, `EvidenceBundle`, `HTTPTranscriptReceipt`
- Utility functions: `canonical_json()`, `compute_content_hash()`, `compute_receipt_hash()`
- Three passing contract tests (schema instantiation, canonical hashing, receipt hashing)

**OSINT Composed Oracle Spec v2 (Template #10):**
- Three reserved criteria: `corroboration_minimum_met`, `counter_signal_checked`, `rule_change_monitored`
- Source independence taxonomy: 13 source_group enums, `independence_upstream_id` deduplication
- HTTP transcript canonical spec v1.0 (SHA-256, method + URL + query + headers + body_hash)
- 10 fixtures (6 PASS / 4 FAIL) with synthetic evidence bundles
- Five schema enforcement rules (proposed_source_group_guard, revision_policy_settlement_guard, access_surface_independence, dubai_pulse_publication_layer, independence_upstream_dedupe_runner)

**OSINT Source Registry v0.3.2:**
- 51 sources, 7 jurisdictions
- 3 WorldMonitor endpoints already catalogued (`world_monitor_domain` field set)
- 5 WorldMonitor upstream sources flagged (`world_monitor_upstream_domain` — prefer direct integration)
- 9 controlled enums, standalone CLI validator

**Cycle-035 OSINT Pipeline Plan (architectural reference):**
- Three-stage pipeline: Collection → Corroboration → Scoring
- `BaseCollector` ABC defining fetch → receipt contract
- `worldmonitor.py` collector (3 domain endpoints)
- Collection runner, corroboration engine, counter-signal evaluator, scorer
- File structure and implementation order defined

**WorldMonitor Fork (AITOBIAS04/worldmonitor):**
- Forked from koala73/worldmonitor (13k stars), AGPL-3.0
- v2.5.6 current release
- CII scoring: 4 components (baseline risk 40%, unrest events 20%, security activity 20%, information velocity 20%) with hotspot proximity boost, focal point urgency, conflict-zone floors
- Geographic convergence detection: 1°×1° cells, 24-hour window, 3+ distinct event types trigger alert
- Maritime anomaly detection: AIS density grid (2°×2° cells, 30-min windows), AIS gap detection, dark fleet probability, 8 strategic chokepoints
- Temporal baseline anomaly detection: Welford's online algorithm, 90-day rolling window, per-region per-weekday baselines, z-score thresholds (1.5/2.0/3.0)
- Signal aggregation: multi-source fusion (RSS, ACLED, GDELT, AIS, military flights, protests) clustered by country/region with severity classification

**Existing Repo Infrastructure:**
- `backend/scoring/` — waterfall, escrow, reconciliation, deterministic_oracle scorers
- `backend/engines/reality_signal.py` — `RealitySignalProvider` with `osint` + `deterministic` implementations (010b)
- `backend/engines/paradox.py` — `ParadoxEngine` consuming `RealitySignal` with provenance
- `mcp/` — MCP Server (tool inventory depends on which cycles are merged)
- `fixtures/` — existing synthetic fixtures and baselines

---

## Sprint 1 — Evidence Pipeline Core + WorldMonitor Collector

### What It Is

The collection infrastructure and first live collector. Build the `BaseCollector` ABC, implement the WorldMonitor collector for all three domain endpoints, wire canonical hashing and HTTP transcript receipt generation, add WorldMonitor source entries to the registry, and build the collection runner that orchestrates fetches per Theatre oracle configuration.

After Sprint 1, Echelon can call WorldMonitor endpoints and receive evidence bundles with verifiable provenance. No corroboration or scoring yet — that's Sprint 2.

### Evidence Models

**File:** `backend/osint/models/evidence.py`

```python
@dataclass
class CollectionResult:
    """Output of a single collector fetch."""
    source_id: str                  # Registry source_id
    bundle: EvidenceBundle          # Full evidence bundle with receipt
    raw_payload: bytes              # Exact response body (for content_hash verification)
    fetch_duration_ms: int          # Wall-clock fetch time
    success: bool                   # Whether the fetch succeeded
    error: str | None               # Error message if failed
    retrieved_at: datetime          # UTC timestamp
```

The `EvidenceBundle` and `HTTPTranscriptReceipt` models are imported from `worldmonitor_api_contract.py` schemas. Sprint 1 verifies that the collector output matches these shapes exactly. No model duplication — the API contract is the single source of truth for bundle shapes.

### Canonical Hashing

**File:** `backend/osint/canonical.py`

```python
def canonical_json(obj: dict) -> str:
    """Echelon Canonical JSON v0: sorted keys, compact separators, UTF-8 (no ASCII escapes).
    NOTE: This is NOT full RFC 8785 (JCS). It is a simpler deterministic serialisation
    sufficient for Echelon's hashing needs but lacking JCS's number normalisation and
    Unicode normalisation guarantees."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

def compute_content_hash(raw_payload: bytes) -> str:
    """SHA-256 of raw response bytes. Hashes bytes, NOT parsed/re-serialised JSON.
    This ensures the hash matches the exact HTTP response body for receipt verification."""

def compute_receipt_hash(method: str, url: str, query: str, headers: str, body_hash: str) -> str:
    """SHA-256 of canonical HTTP transcript per Echelon transcript spec v1.0."""
```

These functions already exist in `worldmonitor_api_contract.py`. `backend/osint/canonical.py` **re-exports** them — it wraps the API contract's implementations, never reimplements. Specifically:

- **From contract (re-exported):** `canonical_json()`, `compute_receipt_hash()` — wrapper delegates directly; tests assert output equality with contract originals.
- **New in Echelon wrapper:** `compute_content_hash(raw_payload: bytes)` — hashes raw response bytes. The contract's version hashes a dict; the wrapper hashes bytes. These are intentionally different functions for different purposes (receipt verification vs structured data hashing). No equality assertion between them.

### BaseCollector ABC

**File:** `backend/osint/collectors/base.py`

```python
class BaseCollector(ABC):
    """Abstract base class for all OSINT collectors.
    Defines the fetch → receipt contract that every collector must implement."""

    @abstractmethod
    def source_id(self) -> str:
        """Registry source_id this collector is authoritative for."""

    @abstractmethod
    async def fetch(self, request: dict, theatre_id: str | None = None) -> CollectionResult:
        """Fetch evidence from the upstream source.
        Must produce a valid EvidenceBundle with HTTP transcript receipt.
        Must NOT raise — return CollectionResult with success=False on failure."""

    @abstractmethod
    def health_check(self) -> HealthStatus:
        """Check upstream availability. Returns HEALTHY, DEGRADED, or UNAVAILABLE."""
```

**Contract:** Every collector produces a `CollectionResult` with a valid `EvidenceBundle`. Two hash invariants are enforced:
1. `receipt.content_hash == SHA256(raw_payload)` — hashes the **exact response bytes**, not re-serialised JSON. The `raw_payload` field on `CollectionResult` stores the bytes; the `structured_extract` field stores the parsed dict separately.
2. `receipt.receipt_hash == compute_receipt_hash(method, url, query, headers, body_hash)` — hashes the canonical HTTP transcript per Echelon transcript spec v1.0.

These invariants are tested at the base class level — individual collectors inherit the verification.

### WorldMonitor Collector

**File:** `backend/osint/collectors/worldmonitor.py`

```python
@dataclass
class WorldMonitorConfig:
    """Configuration for the WorldMonitor collector."""
    base_url: str = "http://localhost:8080"    # Self-hosted fork
    timeout_s: float = 30.0
    version: str = "v0.1.0"
    retry_count: int = 2
    retry_delay_s: float = 1.0

class WorldMonitorCollector(BaseCollector):
    """Collector for all three WorldMonitor domain endpoints.
    Produces one EvidenceBundle per fetch with HTTP transcript receipt."""

    def __init__(self, config: WorldMonitorConfig, domain: WMDomain): ...

    async def fetch(self, request: dict, theatre_id: str | None = None) -> CollectionResult:
        """
        Calls the appropriate WM endpoint based on self.domain:
        - INTELLIGENCE → POST /api/v1/intelligence/cii
        - MARKET → POST /api/v1/market/snapshot
        - MARITIME → POST /api/v1/maritime/anomaly

        Produces EvidenceBundle with:
        - bundle_id: "eb_{domain}_{theatre_id}_{timestamp}"
        - source_id: from registry (worldmonitor_cii, worldmonitor_finance, worldmonitor_maritime)
        - source_group: "alt_data_behavioural" (WM CII), "market_data" (WM finance), "maritime_ais" (WM maritime)
        - resolution_role: "primary_evidence" (WM endpoints are primary sources)
        - receipt: HTTPTranscriptReceipt with content_hash and receipt_hash
        - normalised_event: NormalisedEvent from WM response
        """

    def health_check(self) -> HealthStatus:
        """Calls GET /health on WM instance. Maps WM HealthStatus to local enum."""
```

**Three collector instances** are created per Theatre (one per WM domain), configured via the Theatre's `oracle_config`. A Theatre that only cares about maritime signals only instantiates the maritime collector.

### WorldMonitor Availability — Failure Mode Pinning

WorldMonitor being self-hosted and running is a hard dependency for 011. Explicit failure behaviour:

| Condition | Collector Behaviour | Pipeline Effect |
|-----------|-------------------|-----------------|
| WM endpoint returns HTTP 200 | Normal: produce `CollectionResult` with `success=True` | Evidence bundle enters corroboration/scoring |
| WM endpoint returns HTTP 5xx | Retry up to `retry_count` (default 2) with `retry_delay_s` (default 1s). If all retries fail: `CollectionResult` with `success=False` | Source counted as intelligence gap. `evidence_completeness` drops. |
| WM endpoint unreachable (connection refused / DNS failure) | Retry same as above. `health_check()` returns `UNAVAILABLE` | Same as 5xx. If all 3 WM domains are unreachable, `evidence_completeness = 0.0`. |
| WM endpoint times out (> `timeout_s`) | Single attempt timeout, then retry. | Same as 5xx. |
| All WM endpoints down | All 3 `CollectionResult` have `success=False` | `evidence_completeness = 0.0`. Paradox activation gate (`min_evidence_completeness`) never fires. Logic Gap scanning does **not** begin. This is the correct behaviour — no evidence means no basis for integrity policing. The Theatre continues trading (Entropy still decays, Butterfly still records), but Paradox is dormant until evidence flows. |

**Key invariant:** WM being down does NOT cause the Paradox Engine to fire spurious circuit breakers. The activation gate latch protects against this — it requires `evidence_completeness >= threshold` before Logic Gap scanning begins. If WM was previously up and the latch already fired, a subsequent WM outage means `p_reality` goes stale (last known `composite_score`). The Paradox Engine continues scanning with stale data. To prevent unbounded staleness, `LiveOSINTRealityProvider` includes a `max_staleness_s` parameter (default 300s). If the most recent `OracleOutput.scored_at` is older than `max_staleness_s`, `get_signal()` returns a `RealitySignal` with `p_reality = None`, which causes the Paradox Engine to skip the scan (same as `disabled` mode for that tick).

### Registry Source Entries

Sprint 1 verifies that the three WorldMonitor source entries in registry v0.3.2 are correctly structured. The entries should carry:

| source_id | source_group | resolution_role | world_monitor_domain | independence_upstream_id | receipt_mode_minimum |
|-----------|-------------|----------------|---------------------|------------------------|---------------------|
| `worldmonitor_cii` | `alt_data_behavioural` | `primary_evidence` | `intelligence` | `worldmonitor` | `http_transcript` |
| `worldmonitor_finance` | `market_data` | `primary_evidence` | `market` | `worldmonitor` | `http_transcript` |
| `worldmonitor_maritime` | `maritime_ais` | `primary_evidence` | `maritime` | `worldmonitor` | `http_transcript` |

**Critical: shared `independence_upstream_id`.** All three WM endpoints share `independence_upstream_id: worldmonitor` because WorldMonitor is a single aggregator over multiple upstreams (RSS, ACLED, GDELT, AIS). Despite having distinct `source_group` values, they are **not** independent corroborators in the Composed Oracle Spec taxonomy. The corroboration engine's `independence_upstream_dedupe_runner` (enforcement rule 6.5) collapses them to a single entry before counting distinct groups. This means `corroboration_minimum_met` **cannot** be satisfied by WM sources alone — at least one non-WM collector is required for true corroboration. In 011, corroboration is explicitly provisional (see Sprint 2 constraint).

If any fields are missing or misaligned, Sprint 1 patches the registry JSON.

### Collection Runner

**File:** `backend/osint/engine/collection_runner.py`

```python
@dataclass
class CollectionPlan:
    """Defines which collectors to run for a Theatre, derived from oracle_config."""
    theatre_id: str
    sources: list[str]                 # source_ids to collect from
    evaluation_window: tuple[datetime, datetime]
    geo: GeoPoint | None               # optional geographic focus
    timeout_s: float = 60.0

class CollectionRunner:
    """Stage 1: Orchestrates collector fetches per Theatre oracle configuration."""

    def __init__(self, collectors: dict[str, BaseCollector], registry: RegistryLoader): ...

    async def collect(self, plan: CollectionPlan) -> list[CollectionResult]:
        """Run all collectors in the plan concurrently.
        Returns results in source_id order. Failed fetches return CollectionResult with success=False.
        Does NOT raise on individual collector failure — the corroboration engine handles gaps."""

    def build_plan(self, oracle_config: dict, theatre_id: str) -> CollectionPlan:
        """Derive a CollectionPlan from a Theatre's oracle_config.
        Filters to WorldMonitor sources only in 011. Future cycles add more collectors."""
```

**Concurrency:** `asyncio.gather()` with per-collector timeout. If a WM endpoint is unreachable, that source's `CollectionResult` has `success=False` and the pipeline continues. This aligns with the `allow_gap` semantics from the Composed Oracle Spec.

### Registry Loader

**File:** `backend/osint/models/registry.py`

```python
class RegistryLoader:
    """Loads and queries the OSINT source registry JSON."""

    def __init__(self, registry_path: str): ...

    def get_source(self, source_id: str) -> RegistrySource | None
    def get_sources_by_group(self, source_group: str) -> list[RegistrySource]
    def get_sources_by_domain(self, wm_domain: str) -> list[RegistrySource]
    def get_settlement_eligible(self) -> list[RegistrySource]
    def validate(self) -> list[str]:
        """Run structural validation checks. Returns list of error messages (empty = valid)."""
```

### Sprint 1 Architecture

```
backend/osint/
├── __init__.py
├── canonical.py                    # Echelon Canonical JSON v0 + SHA-256 — re-exports from API contract (NEW)
├── models/
│   ├── __init__.py
│   ├── evidence.py                 # CollectionResult, re-exports from API contract (NEW)
│   └── registry.py                 # RegistryLoader, RegistrySource (NEW)
├── collectors/
│   ├── __init__.py
│   ├── base.py                     # BaseCollector ABC (NEW)
│   └── worldmonitor.py             # WorldMonitor collector — 3 domains (NEW)
├── engine/
│   ├── __init__.py
│   └── collection_runner.py        # Stage 1: orchestrate fetches per theatre config (NEW)
└── tests/
    ├── fixtures/
    │   ├── wm_cii_response.json        # Mock CII endpoint response (from Pydantic schema) (NEW)
    │   ├── wm_market_response.json     # Mock market snapshot response (NEW)
    │   ├── wm_maritime_response.json   # Mock maritime anomaly response (NEW)
    │   └── wm_error_responses.json     # Mock error responses (5xx, timeout, malformed) (NEW)
    ├── test_canonical.py           # Deterministic hashing, Echelon Canonical JSON v0 (NEW)
    ├── test_receipt.py             # HTTP transcript receipt generation + verification (NEW)
    ├── test_worldmonitor.py        # WM collector: 3 domains, error handling, retry (mocks only) (NEW)
    ├── test_collection_runner.py   # Concurrent fetches, timeout, partial failure (mocks only) (NEW)
    └── test_registry_loader.py     # Registry load, query, validation (NEW)
```

### Sprint 1 Tasks

1. **Evidence models** — `CollectionResult` dataclass. Import and re-export `EvidenceBundle`, `HTTPTranscriptReceipt`, `NormalisedEvent`, `NormalisedMeasure`, `GeoPoint` from the API contract. No model duplication.
2. **Canonical hashing** — Re-export `canonical_json()` and `compute_receipt_hash()` from `worldmonitor_api_contract.py` into `backend/osint/canonical.py`. Add `compute_content_hash(raw_payload: bytes)` that hashes raw bytes (not re-serialised JSON). Label as Echelon Canonical JSON v0 (not RFC 8785). Test determinism (same input → same hash) and assert output equality with API contract originals.
3. **BaseCollector ABC** — Abstract base with `source_id()`, `fetch()`, `health_check()`. Receipt invariant enforcement at base class level.
4. **WorldMonitor collector** — Three-domain collector calling WM's API endpoints. Request construction from Theatre `oracle_config`. Response parsing into `EvidenceBundle`. HTTP transcript receipt generation. Error handling (timeout, HTTP errors, malformed response). Retry with configurable count and delay.
5. **Registry loader** — Load registry v0.3.2 JSON. Query by source_id, source_group, WM domain, settlement eligibility. Structural validation (enum membership, invariant checks).
6. **Registry alignment check** — Verify 3 WM source entries are correctly structured. Patch if needed.
7. **Collection runner** — Orchestrate concurrent fetches per `CollectionPlan`. Per-collector timeout. Partial failure handling (`success=False`, no raise). Plan derivation from `oracle_config`.
8. **Mock WM response fixtures** — Generate JSON fixtures from `worldmonitor_api_contract.py` Pydantic schemas for all three domains (CII, market, maritime) plus error responses (5xx, malformed JSON). Fixtures exercise normal and edge-case payloads. All collector and runner tests consume these fixtures via `httpx`/`aiohttp` mocking — no real HTTP calls.
9. **Canonical hashing tests** — Determinism, edge cases (empty object, nested objects, Unicode), cross-verification against API contract utility functions.
10. **Receipt tests** — HTTP transcript canonical form, header allowlist filtering, receipt hash determinism, content hash verification.
11. **Collector tests** — WM collector for each domain against mock fixtures. Error scenarios (timeout, 500, malformed JSON). Retry behaviour. Health check. All mocked — no real HTTP.
12. **Collection runner tests** — Concurrent execution, timeout enforcement, partial failure (1 of 3 collectors fails), plan derivation from oracle_config. All mocked.
13. **Registry loader tests** — Load, query, validation. Missing source_id, invalid enum, settlement invariant violation.

### Sprint 1 Success Criteria

- [ ] `canonical_json()` produces deterministic output (sorted keys, compact separators, no ASCII escape)
- [ ] `compute_content_hash()` and `compute_receipt_hash()` match API contract utility functions exactly
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
- [ ] No modifications to `backend/market/` or `backend/engines/` modules
- [ ] Scoped regression target: all tests in `backend/market/`, `backend/engines/`, `backend/scoring/`, and `backend/osint/` pass. Pre-existing `theatre/` collection errors (29 import failures from Cycle-031–033) are out of scope and excluded from 011's regression baseline.
- [ ] 20+ new Sprint 1 tests pass

---

## Sprint 2 — Corroboration + Scoring + Paradox Wiring + Convergence

### What It Is

The evidence quality layer and live Paradox wiring. The corroboration engine deduplicates by `independence_upstream_id` and enforces `corroboration_minimum_met` — in 011 this is always false (WM-only), which correctly penalises `composite_score` via the corroboration factor. The scorer assembles confidence-weighted composites producing the `composite_score` that the Paradox Engine reads as `p_reality`. Geographic convergence detection aggregates multi-domain WM signals into convergence alerts that enrich Theatre evidence.

After Sprint 2, the full loop is live: WorldMonitor fetches → evidence bundles → corroboration (provisional) → scoring → `composite_score` → `RealitySignalProvider` → Paradox Engine Logic Gap → circuit breakers. No more stubs — but `composite_score` carries a corroboration penalty until non-WM sources land.

### Corroboration Engine

**File:** `backend/osint/engine/corroboration.py`

```python
@dataclass
class CorroborationResult:
    """Output of the corroboration stage."""
    theatre_id: str
    primary_bundles: list[EvidenceBundle]          # Primary evidence sources
    corroborating_bundles: list[EvidenceBundle]     # Secondary corroborators (deduplicated)
    distinct_source_groups: int                     # After upstream_id dedup
    corroboration_minimum: int                      # From oracle_config
    corroboration_met: bool                         # distinct_source_groups >= corroboration_minimum
    dedup_log: list[dict]                           # Audit trail of dedup decisions

class CorroborationEngine:
    """Stage 2: Cross-reference evidence bundles, deduplicate, enforce minimums."""

    def __init__(self, registry: RegistryLoader): ...

    def evaluate(self, results: list[CollectionResult],
                 oracle_config: dict) -> CorroborationResult:
        """
        1. Separate primary_evidence from secondary_corroboration by resolution_role.
        2. Deduplicate corroborators by independence_upstream_id (per enforcement rule 6.5).
        3. Count distinct source_groups from deduplicated set.
        4. Evaluate corroboration_minimum_met.
        5. Log dedup decisions for audit trail.
        """

    def deduplicate_by_upstream_id(self, bundles: list[EvidenceBundle]) -> list[EvidenceBundle]:
        """Collapse bundles sharing independence_upstream_id.
        Keep strongest-confidence entry per upstream_id."""
```

**Deduplication rule (from Composed Oracle Spec v2 §6.5):** Group evidence bundles by `independence_upstream_id`, collapse duplicates to single strongest-confidence entry, then count distinct `source_groups` from the collapsed set. Two sources from the same upstream system of record (e.g. two Dubai Pulse datasets backed by `ae_dld_tabu`) count as one corroborator.

**011 constraint — provisional corroboration:** All three WM endpoints share `independence_upstream_id: worldmonitor`. The corroboration engine correctly deduplicates them to a single entry, meaning `corroboration_minimum_met` is **always false** in 011 (only one upstream after dedup, regardless of how many WM domains are fetched). This is correct behaviour — WorldMonitor is an aggregator, not three independent sources. The scorer treats `corroboration_met=false` as a known condition in 011: the `corroboration_factor` (0.7) applies, reducing `composite_score` accordingly. The Paradox Engine still receives a usable `p_reality` — it's just penalised for lack of independent corroboration. When future collectors are added (Companies House, SEC EDGAR, etc.), `corroboration_minimum_met` can become true and the penalty lifts.

### Counter-Signal Evaluator

**File:** `backend/osint/engine/counter_signal.py`

```python
class CounterSignalOutcome(str, Enum):
    ABSENT = "absent"                          # Checked, not present → PASS
    PRESENT_DISCOUNTED = "present_discounted"  # Present, explained by discount rule → PASS
    PRESENT_UNEXPLAINED = "present_unexplained"  # Present, no rule → FAIL
    UNAVAILABLE = "unavailable"                # Source unreachable → depends on allow_gap

@dataclass
class CounterSignalResult:
    signal_class: str                           # One of 11 counter_signal_class values
    outcome: CounterSignalOutcome
    source_id: str                              # Which counter-signal source was checked
    detail: dict                                # Class-specific metadata

class CounterSignalEvaluator:
    """Stage 2b: Evaluate counter-signal streams per oracle_config."""

    def evaluate(self, collection_results: list[CollectionResult],
                 oracle_config: dict) -> list[CounterSignalResult]:
        """
        For each counter-signal source declared in oracle_config:
        1. Check if collection succeeded (UNAVAILABLE if not).
        2. If succeeded, evaluate signal presence.
        3. If present, check discount rules (committed at oracle creation).
        4. Return outcome per class.
        """
```

**011 scope — scaffolding only:** Counter-signal evaluation requires independent data sources (weather feeds, infrastructure status APIs, market volatility indices) that are not WM endpoints and are not collected in 011. Deriving counter-signals from WM itself would defeat source independence. Therefore:
- All 11 counter-signal classes return `UNAVAILABLE` with `allow_gap=true` in 011.
- The evaluator interface, discount rule engine, and outcome classification are fully implemented and tested against synthetic fixtures.
- Three classes are design-documented as first targets when independent sources land: `infrastructure_outage`, `weather`, `financial_distress`.
- The `counter_signal_checked` criterion passes in 011 because all classes use `allow_gap=true`. Each UNAVAILABLE result is classified as `INTELLIGENCE_GAP` (consistent with AC-1 GapKind semantics from Cycle-004) — not `ABSENT`. The distinction matters: absence is evidence; an intelligence gap is the lack of it. The criterion passes honestly under gap tolerance, not by conflating the two states.

Future cycles that add non-WM free endpoints (e.g. USGS for weather, CISA for infrastructure) will flip individual classes from UNAVAILABLE to live evaluation without changing the evaluator interface.

### Scorer

**File:** `backend/osint/engine/scorer.py`

```python
@dataclass
class CriterionScore:
    criterion: str                   # e.g. "corroboration_minimum_met"
    passed: bool
    score: float                     # 0.0–1.0
    detail: dict                     # Criterion-specific metadata

@dataclass
class OracleOutput:
    """Final output of the three-stage pipeline."""
    theatre_id: str
    composite_score: float           # Confidence-weighted composite (0.0–1.0)
    criterion_scores: list[CriterionScore]
    evidence_bundles: list[EvidenceBundle]
    corroboration_result: CorroborationResult
    counter_signal_results: list[CounterSignalResult]
    evidence_completeness: float     # count(successful sources) / count(required sources)
    bundle_hash: str                 # SHA-256 of canonical JSON manifest (see below)
    scored_at: datetime

class Scorer:
    """Stage 3: Assemble confidence-weighted evidence bundle, produce composite_score."""

    def __init__(self, registry: RegistryLoader): ...

    def score(self, corroboration: CorroborationResult,
              counter_signals: list[CounterSignalResult],
              oracle_config: dict) -> OracleOutput:
        """
        Compute composite_score:
        1. Per-criterion evaluation (corroboration_minimum_met, counter_signal_checked, rule_change_monitored).
        2. Confidence-weighted average across primary evidence bundles.
        3. Corroboration bonus (more distinct groups → higher confidence).
        4. Counter-signal penalty (present_unexplained reduces score).
        5. Evidence completeness factor.
        6. Bundle hash via manifest pattern:
           manifest = {bundle.bundle_id: bundle.content_hash for bundle in sorted_bundles}
           bundle_hash = SHA256(canonical_json(manifest))
           This is order-independent (sorted by bundle_id) and deterministic.
        """

    def compute_composite(self, bundles: list[EvidenceBundle],
                          corroboration_met: bool,
                          counter_signal_pass: bool) -> float:
        """
        composite_score = weighted_mean(bundle.normalised_event.confidence for primary bundles)
                        × corroboration_factor (1.0 if met, 0.7 if not)
                        × counter_signal_factor (1.0 if pass, 0.5 if fail)
                        × evidence_completeness

        Result clamped to [0.0, 1.0].
        Weights derived from registry priority_bucket (settlement_grade weighted higher).
        """
```

**`composite_score` is the field the Paradox Engine reads.** This is the same field referenced in the Paradox Policy Design Note v1.1 as `p_reality` for `osint` source type. The scorer produces it; the `RealitySignalProvider` reads it.

### Paradox Wiring — Live `p_reality`

**File:** Extend `backend/engines/reality_signal.py` (010b output)

```python
# Existing from 010b:
class RealitySignalProvider:
    def get_signal(self, theatre_id: str) -> RealitySignal: ...

# Sprint 2 extension:
class LiveOSINTRealityProvider(RealitySignalProvider):
    """Reads p_reality from live WorldMonitor pipeline output.
    Replaces the stub osint provider from 010b."""

    def __init__(self, scorer: Scorer, collection_runner: CollectionRunner,
                 corroboration_engine: CorroborationEngine,
                 counter_signal_evaluator: CounterSignalEvaluator): ...

    def get_signal(self, theatre_id: str) -> RealitySignal:
        """
        Full pipeline execution:
        1. Build CollectionPlan from Theatre oracle_config.
        2. Run CollectionRunner (fetch from WM endpoints).
        3. Corroborate (dedup, enforce minimums).
        4. Evaluate counter-signals.
        5. Score (produce composite_score).
        6. Return RealitySignal with:
           - p_reality = composite_score
           - evidence_bundle_hash = bundle_hash from OracleOutput (manifest pattern)
           - oracle_output_id = "{theatre_id}_{scored_at_ms}" (unique per pipeline run)
           - provider_version = "011.1" (tracks pipeline evolution)
           - scored_at = OracleOutput.scored_at
           - source_type = "osint"

        NOTE: 010b's provenance ID field is renamed to oracle_output_id in 011.
        No certificate store exists — oracle_output_id is a pipeline run identifier with
        provenance (bundle_hash + scored_at + provider_version). This prevents consumers
        from assuming a certificate store exists while still providing audit-grade traceability.
        """
```

**Integration point:** The `ParadoxEngine` from 010b injects a `RealitySignalProvider`. In 011, Theatres with `logic_gap_source: "osint"` receive a `LiveOSINTRealityProvider` instead of the stub. The Paradox Engine code is unchanged — only the provider implementation changes. This is the seam 010b designed for.

**Activation gate interaction:** The `evidence_completeness` field from `OracleOutput` maps directly to the `min_evidence_completeness` activation gate in `ParadoxConfig`. When `evidence_completeness` reaches the gate threshold (e.g. 0.50), the Paradox Engine's activation latch fires and Logic Gap scanning begins.

### Geographic Convergence Detection

**File:** `backend/osint/engine/convergence.py`

```python
@dataclass
class ConvergenceCell:
    """A geographic cell where multiple signal types co-locate."""
    lat_bin: float                   # Centre of 1°×1° cell
    lon_bin: float
    event_types: set[str]            # Distinct WMDomain values (INTELLIGENCE, MARKET, MARITIME)
    events: list[NormalisedEvent]    # All events in this cell within window
    convergence_score: float         # 0.0–1.0, scaled by event count and type diversity

@dataclass
class ConvergenceAlert:
    """Fired when a cell meets the convergence threshold."""
    alert_id: str
    cell: ConvergenceCell
    theatre_id: str | None           # Matched Theatre if geo overlaps
    triggered_at: datetime

class ConvergenceDetector:
    """Detects geographic convergence of multi-domain WorldMonitor signals.
    Mirrors WM's internal convergence logic but operates on Echelon's evidence bundles."""

    def __init__(self, cell_size_deg: float = 1.0,
                 window_hours: int = 24,
                 min_event_types: int = 3): ...

    def detect(self, bundles: list[EvidenceBundle]) -> list[ConvergenceAlert]:
        """
        1. Bin all NormalisedEvents by 1°×1° geographic cell.
        2. Within each cell, count distinct WMDomain values (INTELLIGENCE + MARITIME + MARKET = 3 domains).
        3. If distinct types >= min_event_types within window, fire ConvergenceAlert.
        4. Score by event count and type diversity.
        """

    def match_theatres(self, alerts: list[ConvergenceAlert],
                       active_theatres: list[dict]) -> list[ConvergenceAlert]:
        """Match convergence alerts to active Theatres by geographic overlap.
        Enriches alert with theatre_id for evidence routing."""
```

**Design rationale:** WorldMonitor performs its own convergence detection internally. Echelon's convergence detector operates on evidence bundles that have already passed through the collection → receipt pipeline. This means convergence alerts carry full provenance — every event in a convergence cell has an HTTP transcript receipt. WM's internal convergence is useful for dashboarding; Echelon's convergence is verifiable and auditable.

**011 scope:** Convergence detection produces alerts that are logged **in-process only** (no persistence, no MCP surface). They do not yet trigger automatic Theatre creation — that requires the Sponsored Theatre workflow (Cycle-012). In 011, convergence alerts enrich existing Theatre evidence layers during the current process lifetime. After process restart, all alert state is lost (consistent with the no-persistence constraint across 010a/010b/011).

### Sprint 2 Architecture (additions to Sprint 1)

```
backend/osint/
├── engine/
│   ├── corroboration.py            # Stage 2: dedup + minimum enforcement (NEW)
│   ├── counter_signal.py           # Stage 2b: counter-signal evaluation (NEW)
│   ├── scorer.py                   # Stage 3: confidence-weighted composite_score (NEW)
│   └── convergence.py              # Geographic convergence detection (NEW)
└── tests/
    ├── test_corroboration.py       # Dedup, minimum enforcement, audit trail (NEW)
    ├── test_counter_signal.py      # All 4 outcomes via synthetic fixtures, scaffolding-only (NEW)
    ├── test_scorer.py              # Composite score, criterion scores, bundle hash (NEW)
    ├── test_convergence.py         # Cell binning, alert firing, theatre matching (NEW)
    ├── test_live_reality.py        # LiveOSINTRealityProvider end-to-end (NEW)
    └── test_paradox_wiring.py      # Paradox Engine with live p_reality (NEW)

backend/engines/
└── reality_signal.py               # Extended: LiveOSINTRealityProvider (MODIFIED)
```

### Sprint 2 Tasks

1. **Corroboration engine** — Separate primary from secondary by `resolution_role`. Deduplicate by `independence_upstream_id` (per enforcement rule 6.5). Count distinct `source_groups`. Evaluate `corroboration_minimum_met`. Audit trail for dedup decisions.
2. **Counter-signal evaluator** — Full interface and discount rule engine. All 11 classes return `UNAVAILABLE` with `allow_gap=true` in 011 (no independent counter-signal sources connected). Tested against synthetic fixtures exercising all four outcomes (absent, present_discounted, present_unexplained, unavailable).
3. **Scorer** — Per-criterion evaluation. Confidence-weighted composite. Corroboration bonus (0.7 penalty when `corroboration_met=false` — the 011 default). Counter-signal penalty. Evidence completeness factor. Bundle hash via manifest pattern (`{bundle_id: content_hash}` → canonical JSON → SHA-256).
4. **LiveOSINTRealityProvider** — Full pipeline execution: collect → corroborate → evaluate counter-signals → score → return `RealitySignal` with `p_reality = composite_score`. Replaces 010b's stub `osint` provider.
5. **Paradox wiring** — Inject `LiveOSINTRealityProvider` into Theatres with `logic_gap_source: "osint"`. Verify activation gate reads `evidence_completeness` from `OracleOutput`. No modification to Paradox Engine code — only provider swap.
6. **Convergence detector** — 1°×1° cell binning, 24-hour window, 3+ event type threshold. Convergence scoring. Theatre matching by geographic overlap.
7. **Corroboration tests** — Dedup correctness (same upstream_id collapsed — all 3 WM endpoints collapse to 1 entry), minimum enforcement (exact boundary), provisional corroboration (WM-only = 1 distinct upstream, `corroboration_met=false`). Also test with synthetic non-WM bundle injected to verify `corroboration_met=true` when independent source present.
8. **Counter-signal tests** — All four outcome types via synthetic fixtures. Discount rule application (committed rules only). Unavailable handling with `allow_gap` toggle (true → PASS, false → FAIL). Verify all 11 classes return UNAVAILABLE in 011.
9. **Scorer tests** — Composite score calculation at edge values. Criterion pass/fail propagation. Bundle hash determinism. Evidence completeness factor.
10. **Live reality tests** — End-to-end: mock WM responses → CollectionRunner → CorroborationEngine → Scorer → `RealitySignal` with correct `p_reality`.
11. **Paradox wiring tests** — Paradox Engine with `LiveOSINTRealityProvider`: Logic Gap computed from live `composite_score`. Activation gate fires when `evidence_completeness` crosses threshold. Circuit breaker actions trigger on real divergence.
12. **Convergence tests** — Cell binning accuracy, WMDomain counting (not MeasureType), alert threshold at exactly 3 domains, Theatre matching, empty/single-domain no-alert.
13. **Integration test** — Full loop: WM fetch → evidence bundle → corroboration → scoring → `composite_score` → Paradox Logic Gap → threshold evaluation → Wing Flap recorded.

### Sprint 2 Success Criteria

- [ ] Corroboration deduplicates by `independence_upstream_id` correctly
- [ ] `corroboration_minimum_met` evaluates at exact boundary (minimum - 1 = FAIL, minimum = PASS)
- [ ] Counter-signal evaluator returns UNAVAILABLE for all 11 classes in 011 (scaffolding-only, no independent sources)
- [ ] Counter-signal `UNAVAILABLE` with `allow_gap=true` does not cause criterion FAIL
- [ ] Counter-signal `UNAVAILABLE` with `allow_gap=false` causes criterion FAIL
- [ ] `composite_score` is confidence-weighted, clamped to [0.0, 1.0]
- [ ] Corroboration bonus and counter-signal penalty apply correctly
- [ ] `evidence_completeness` = count(successful sources) / count(required sources), excluding optional
- [ ] Bundle hash uses manifest pattern (`{bundle_id: content_hash}` → canonical JSON → SHA-256), deterministic regardless of insertion order
- [ ] `LiveOSINTRealityProvider.get_signal()` returns `RealitySignal` with `p_reality = composite_score`
- [ ] `RealitySignal.evidence_bundle_hash` matches `OracleOutput.bundle_hash`
- [ ] Paradox Engine receives live `p_reality` without code changes (provider swap only)
- [ ] Activation gate fires when `evidence_completeness` crosses `min_evidence_completeness` threshold
- [ ] Logic Gap = `abs(p_market - p_reality)` computed correctly with live `composite_score`
- [ ] Convergence detector fires alert when 3+ event types co-locate in 1°×1° cell within 24 hours
- [ ] Convergence alerts carry full provenance (every event has HTTP transcript receipt)
- [ ] Convergence Theatre matching correctly identifies geographic overlap
- [ ] No modifications to `backend/engines/paradox.py` (provider interface unchanged from 010b)
- [ ] No modifications to `backend/market/` modules
- [ ] Scoped regression target: all tests in `backend/market/`, `backend/engines/`, `backend/scoring/`, and `backend/osint/` pass. Pre-existing `theatre/` collection errors remain excluded.
- [ ] 20+ new Sprint 2 tests pass

---

## Scope Exclusions

- **No non-WM collectors.** Companies House, SEC EDGAR, FRED, ECB, Gazette, INPI RNE collectors are deferred. WorldMonitor is the first and only live collector in 011. The `BaseCollector` pattern is ready for future collectors.
- **No paid source procurement.** No Polygon.io, RavenPack, Dataminr, Spire Global subscriptions. WorldMonitor consumes upstream sources internally; Echelon accesses them via WM's API boundary.
- **No WorldMonitor deployment.** This cycle assumes the WM fork is already self-hosted and running. WM setup, configuration, and hosting are not in scope.
- **No Theatre Command UI.** No globe rendering, no GeoEvent index, no convergence visualisation. Convergence alerts are data-only.
- **No automatic Theatre creation from convergence.** Convergence alerts log and enrich existing Theatres. Auto-creation requires Sponsored Theatre workflow (Cycle-012).
- **No certificate store.** The pipeline produces `OracleOutput` with `composite_score` directly. `RealitySignal` carries an `oracle_output_id` (pipeline run identifier with bundle_hash + scored_at + provider_version) — not a certificate. Wrapping output into calibration certificate format is deferred.
- **No agent interaction.** No agent-initiated evidence collection, no agent-driven counter-signal evaluation. Collection is pipeline-driven per heartbeat cadence.
- **No rule_change_monitored implementation.** The third reserved criterion from the Composed Oracle Spec v2 requires monitoring resolution rules hash mid-market. This depends on the Sponsored Theatre lifecycle (Cycle-012). Stubbed as always-PASS in 011.
- **No database persistence.** Evidence bundles, corroboration results, and scorer output are in-memory (continues 010a/010b pattern). Persistence deferred.
- **No witness_quorum or signed_receipt receipt modes.** All WM endpoints use `http_transcript` receipt mode. Stronger receipt modes are for future source types with `latest_only` revision policy.
- **AGPL-3.0 compliance not resolved.** WorldMonitor fork is AGPL-3.0 licensed. Echelon consumes WM exclusively via clean API boundary (HTTP), which may satisfy AGPL's network-use provisions — but formal legal review is required before any hosted deployment. 011 is local/development only; this risk is deferred but tracked.

---

## Dependency Chain

```
Cycle-004 (pipeline hardening)
  → Cycles 005–006 (registry expansion + live OSINT surfaces)
    → Cycle-007 (unified Two-Rail pipeline, 447+ tests)
      → Cycle-008 (MCP verifier + construct calibration)
        → Cycle-009 (MCP surface, HTTP transport, certificate store)
          → Cycle-010a (LMSR cost function, market lifecycle, trade execution, positions, settlement)
            → Cycle-010b (Butterfly, Paradox, Entropy engines, heartbeat, VRF, Base Sepolia)
              → Cycle-011 (WorldMonitor Integration — live evidence pipeline + convergence)
                → Cycle-012 (Sponsored Theatre E2E)
                → Cycle-013 (Results Surface)
```

## After Cycle-011

The evidence layer is live. WorldMonitor signals flow through a verifiable pipeline into the Paradox Engine. Markets are policed against real-world data. Evidence bundles carry HTTP transcript receipts for provenance. Corroboration enforces source independence (provisionally unmet with WM-only; correctly penalises `composite_score`). Counter-signal scaffolding is in place for future source expansion.

**Cycle-012 — Sponsored Theatre End-to-End:** First externally-commissioned Theatre. Theatre creation with live WM evidence, sponsor onboarding, settlement against real `composite_score`.

**Cycle-013 — Results Surface:** Full platform UI — Theatres, markets, evidence, convergence alerts, Logic Gap status, certificates, audit trails in one view.

---

## Workflow

```bash
cd ~/Developer/prediction-market-monorepo.nosync
claude

# Copy this file into Loa context
cp ~/Developer/echelon/loa_feed/echelon_cycle_011_context.md grimoires/loa/context/echelon_cycle_011.md

# Sprint 1: Evidence Pipeline Core + WorldMonitor Collector
/plan
/simstim
/run-bridge

# Verify Sprint 1
python3 -m pytest backend/osint/tests/ -v

# Sprint 2: Corroboration + Scoring + Paradox Wiring + Convergence
/plan
/simstim
/run-bridge

# Verify Sprint 2
python3 -m pytest backend/osint/tests/ -v

# Verify Paradox wiring (engines still pass)
python3 -m pytest backend/engines/tests/ -v

# Full test suite
python3 -m pytest -q
```

---

## Key Spec References

| Document | Relevance |
|----------|-----------|
| WorldMonitor API Contract (`worldmonitor_api_contract.py`) | Three domain endpoints, Pydantic schemas, EvidenceBundle shape, canonical hashing utilities |
| OSINT Composed Oracle Spec v2 | Three reserved criteria, source independence taxonomy, HTTP transcript canonical spec, 5 enforcement rules, 10 fixtures |
| OSINT Source Registry v0.3.2 | 51 sources, 3 WM endpoints catalogued, 9 controlled enums, independence_upstream_id |
| Cycle-035 OSINT Pipeline Plan | Architectural reference for three-stage pipeline (Collection → Corroboration → Scoring), file structure |
| Echelon System Bible v13 — Section XV (OSINT Source Registry & Composed Oracle) | Integration architecture, WM consumption via clean API boundary |
| Echelon Paradox Policy Design Note v1.1 | p_reality = composite_score, evidence_completeness gate, activation latch semantics |
| Echelon_Bootstrap_2Mar_Session3.md | Cumulative build state, cycle numbering, documentation structure |
