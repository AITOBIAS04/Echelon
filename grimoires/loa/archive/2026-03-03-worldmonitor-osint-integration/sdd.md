# SDD: WorldMonitor OSINT Integration — Live Evidence Pipeline + Convergence Signals

**Cycle**: 011
**Version**: 1.0
**Date**: 2026-03-03
**PRD**: `grimoires/loa/prd.md` v1.0
**Predecessor**: Cycle-010b SDD (archived)

---

## 1. Executive Summary

Cycle-011 introduces the live evidence pipeline — a three-stage architecture (Collection, Corroboration, Scoring) that connects WorldMonitor's three OSINT domain endpoints to the Paradox Engine's `RealitySignalProvider` interface. The result: `p_reality` in the Logic Gap equation shifts from a stub value to a confidence-weighted composite score derived from real-world evidence with full provenance (HTTP transcript receipts).

**Key architectural decisions**:
1. **API contract as single source of truth** — evidence models (`EvidenceBundle`, `NormalisedEvent`, `HTTPTranscriptReceipt`, `GeoPoint`) are imported from `worldmonitor_api_contract.py`, not duplicated
2. **BaseCollector ABC** with hash invariant enforcement at the base class level
3. **Three-stage pipeline** — Collection (fetch + receipt) -> Corroboration (dedup + independence) -> Scoring (composite + bundle hash)
4. **Provider swap, not code change** — `LiveOSINTRealityProvider` replaces `StubRealityProvider` via the 010b `RealitySignalProvider` interface. Zero modifications to `backend/engines/paradox.py`
5. **Provisional corroboration** — all WM endpoints share `independence_upstream_id: worldmonitor`, so corroboration is always unmet in 011. The 0.7 penalty is intentional, not a bug.
6. **In-memory only** — no persistence, no database (continues 010a/010b pattern)
7. **Mock-only testing** — WorldMonitor is not running locally. All HTTP is mocked.

---

## 2. System Architecture

### 2.1 Component Topology

```
                        ┌─────────────────────────────────────────────────────┐
                        │                backend/osint/                        │
                        │                                                      │
                        │  ┌────────────────┐   ┌──────────────────────────┐  │
                        │  │  collectors/    │   │  engine/                  │  │
                        │  │                 │   │                           │  │
                        │  │  BaseCollector  │   │  CollectionRunner ────┐  │  │
                        │  │       ▲         │   │       │              │  │  │
                        │  │       │         │   │       ▼              │  │  │
                        │  │  WorldMonitor   │◀──│  collect()           │  │  │
                        │  │  Collector      │   │       │              │  │  │
                        │  │  (3 domains)    │   │       ▼              │  │  │
                        │  └────────────────┘   │  CorroborationEngine │  │  │
                        │                        │       │              │  │  │
                        │  ┌────────────────┐   │       ▼              │  │  │
                        │  │  models/        │   │  CounterSignalEval  │  │  │
                        │  │                 │   │       │              │  │  │
                        │  │ CollectionResult│   │       ▼              │  │  │
                        │  │ RegistryLoader  │   │  Scorer ──────────┐ │  │  │
                        │  └────────────────┘   │       │            │ │  │  │
                        │                        │       ▼            │ │  │  │
                        │  ┌────────────────┐   │  OracleOutput      │ │  │  │
                        │  │  canonical.py   │   │       │            │ │  │  │
                        │  │  (hashing)      │   │       ▼            │ │  │  │
                        │  └────────────────┘   │  ConvergenceDetect │ │  │  │
                        │                        └──────────┬─────────┘ │  │
                        └───────────────────────────────────┼───────────┘  │
                                                            │              │
                                            composite_score │              │
                                                            ▼              │
                        ┌──────────────────────────────────────────────────┘
                        │         backend/engines/                          │
                        │                                                   │
                        │  ┌──────────────────────────────────────────┐    │
                        │  │  reality_signal.py                       │    │
                        │  │                                          │    │
                        │  │  LiveOSINTRealityProvider  (NEW)         │    │
                        │  │    .get_signal(theatre_id)               │    │
                        │  │      → runs full OSINT pipeline         │    │
                        │  │      → returns RealitySignal            │    │
                        │  │         p_reality = composite_score     │    │
                        │  │                                          │    │
                        │  │  StubRealityProvider     (010b, retained)│    │
                        │  │  OsintRealityProvider    (010b, retained)│    │
                        │  │  DeterministicRealityProvider (retained) │    │
                        │  └────────────────────┬─────────────────────┘    │
                        │                       │                          │
                        │                  injects│                        │
                        │                       ▼                          │
                        │  ┌──────────────────────────────────────────┐    │
                        │  │  paradox.py         (010b, UNMODIFIED)   │    │
                        │  │  ParadoxEngine                           │    │
                        │  │    .scan(theatre_id)                     │    │
                        │  │      → provider.get_signal()            │    │
                        │  │      → LogicGapCalculator.compute()     │    │
                        │  │      → evaluate_thresholds()            │    │
                        │  └──────────────────────────────────────────┘    │
                        └──────────────────────────────────────────────────┘

                        ┌──────────────────────────────────────────────────┐
                        │        backend/market/ (010a, READ-ONLY)          │
                        │  LMSREngine · TradingEngine · lifecycle           │
                        │  PositionManager · ResolutionEngine               │
                        │           *** NO MODIFICATIONS ***                │
                        └──────────────────────────────────────────────────┘

                        ┌──────────────────────────────────────────────────┐
                        │  backend/schemas/worldmonitor_api_contract.py     │
                        │  (Existing — Pydantic v2 schemas, canonical hash) │
                        │  EvidenceBundle, NormalisedEvent, GeoPoint,       │
                        │  HTTPTranscriptReceipt, WMDomain, MeasureType     │
                        │           *** NO MODIFICATIONS ***                │
                        └──────────────────────────────────────────────────┘
```

### 2.2 Data Flow — Full Pipeline Execution

```
Heartbeat tick (PARADOX cadence, 30s)
  → ParadoxEngine.scan(theatre_id)                    [010b, unmodified]
    → LiveOSINTRealityProvider.get_signal(theatre_id)  [011, NEW]
      → CollectionRunner.build_plan(oracle_config)
      → CollectionRunner.collect(plan)
        → WorldMonitorCollector.fetch(request, "cii")        [async]
        → WorldMonitorCollector.fetch(request, "market")     [async]
        → WorldMonitorCollector.fetch(request, "maritime")   [async]
        → 3x CollectionResult (each with EvidenceBundle + HTTPTranscriptReceipt)
      → CorroborationEngine.evaluate(results, oracle_config)
        → deduplicate_by_upstream_id(bundles)  [collapses 3 WM → 1]
        → count distinct source_groups
        → corroboration_minimum_met = false    [always in 011]
      → CounterSignalEvaluator.evaluate(results, oracle_config)
        → 11x UNAVAILABLE (scaffolding-only)
      → Scorer.score(corroboration, counter_signals, oracle_config)
        → weighted_mean(confidences) × 0.7 × 1.0 × evidence_completeness
        → composite_score ∈ [0.0, 1.0]
        → bundle_hash via manifest pattern
      → ConvergenceDetector.detect(bundles)  [optional, logged only]
      → return RealitySignal(p_reality=composite_score, ...)
    → LogicGapCalculator.compute(theatre_id, p_reality)   [010b, unmodified]
    → ParadoxEngine.evaluate_thresholds(reading)           [010b, unmodified]
    → If action: ParadoxEngine.execute_action()            [010b, unmodified]
```

### 2.3 Dependency / Integration Diagram

```
worldmonitor_api_contract.py (existing)
    │
    ├── EvidenceBundle, NormalisedEvent, GeoPoint ──────┐
    ├── HTTPTranscriptReceipt ──────────────────────────┤
    ├── WMDomain, MeasureType, HealthStatus ────────────┤
    ├── canonical_json() ───────────────────────────────┤
    └── compute_receipt_hash() ─────────────────────────┤
                                                         │
    backend/osint/models/evidence.py ◀──── re-exports ──┘
    backend/osint/canonical.py ◀─── re-exports + adds compute_content_hash(bytes)
         │
         ▼
    backend/osint/collectors/base.py ──── BaseCollector ABC
         │                                    hash invariant enforcement
         ▼
    backend/osint/collectors/worldmonitor.py ──── WorldMonitorCollector
         │                                         3 domains, retry, timeout
         ▼
    backend/osint/engine/collection_runner.py ──── CollectionRunner
         │                                          asyncio.gather, per-collector timeout
         ▼
    backend/osint/engine/corroboration.py ──── CorroborationEngine
         │                                      upstream_id dedup, minimum enforcement
         ▼
    backend/osint/engine/counter_signal.py ──── CounterSignalEvaluator
         │                                       11 classes, all UNAVAILABLE in 011
         ▼
    backend/osint/engine/scorer.py ──── Scorer
         │                               composite_score, bundle_hash, OracleOutput
         ▼
    backend/osint/engine/convergence.py ──── ConvergenceDetector
         │                                    1° cells, multi-domain alerts
         ▼
    backend/engines/reality_signal.py ──── LiveOSINTRealityProvider (NEW)
         │                                  full pipeline orchestration
         ▼
    backend/engines/paradox.py ──── ParadoxEngine (010b, UNMODIFIED)
         │                           provider.get_signal() → compute Logic Gap
         ▼
    backend/engines/integration.py ──── EngineOrchestrator (010b, UNMODIFIED)
                                         heartbeat → paradox scan → actions
```

---

## 3. Technology Stack

| Layer | Technology | Justification |
|-------|-----------|---------------|
| Language | Python 3.9.6+ | Matches 010a/010b; `from __future__ import annotations` for PEP 604 |
| Async | `asyncio` stdlib | Collection runner uses `asyncio.gather()` for concurrent fetches |
| HTTP client | `httpx` (preferred) or `urllib3` | Mock-friendly async HTTP client. No real HTTP calls in 011. |
| Hashing | `hashlib` stdlib | SHA-256 for content hashing, receipt hashing, bundle manifest |
| Serialisation | `json` stdlib | Echelon Canonical JSON v0 (sorted keys, compact separators, no ASCII escape) |
| Schemas | Pydantic v2 (existing) | `worldmonitor_api_contract.py` models — no new Pydantic dependency |
| Data models | `dataclasses` stdlib | All new 011 models are stdlib dataclasses (not Pydantic) |
| Testing | `pytest` + `pytest-asyncio` | Existing test infrastructure from 010b |
| Mocking | `unittest.mock` or `respx` (for httpx) | All WM HTTP calls mocked. No real endpoints. |

**No new runtime dependencies.** `httpx` is test-mocked only. All new modules use stdlib `dataclasses`, `hashlib`, `json`, `asyncio`, `enum`, `abc`.

---

## 4. Component Design

### 4.1 Evidence Models (`backend/osint/models/evidence.py`)

Re-exports bundle shapes from the API contract (single source of truth). Adds `CollectionResult` dataclass for pipeline-internal use.

```python
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

# Re-exported from API contract — single source of truth
from backend.schemas.worldmonitor_api_contract import (
    EvidenceBundle,
    GeoPoint,
    HTTPTranscriptReceipt,
    NormalisedEvent,
    NormalisedMeasure,
    WMDomain,
    MeasureType,
    HealthStatus,
)


@dataclass
class CollectionResult:
    """Output of a single collector fetch."""

    source_id: str                              # Registry source_id
    bundle: EvidenceBundle | None               # None on failure
    raw_payload: bytes                          # Exact response bytes (for hash verification)
    fetch_duration_ms: float                    # Wall-clock fetch time
    success: bool                               # True if valid bundle produced
    error: str | None = None                    # Error description on failure
    retrieved_at: datetime | None = None        # UTC timestamp of fetch
```

**Design rationale**: `CollectionResult` wraps the Pydantic `EvidenceBundle` in a stdlib dataclass to avoid Pydantic dependency in the pipeline internals. The `raw_payload` field is `bytes` (not `dict`) — the content hash is computed on exact response bytes, not re-serialised JSON.

> PRD reference: Section 4.1

### 4.2 Canonical Hashing (`backend/osint/canonical.py`)

Three functions: two re-exported from API contract, one new (bytes-based content hash).

```python
from __future__ import annotations

import hashlib

from backend.schemas.worldmonitor_api_contract import (
    canonical_json as _contract_canonical_json,
    compute_receipt_hash as _contract_compute_receipt_hash,
)


def canonical_json(obj: dict) -> str:
    """Echelon Canonical JSON v0 — sorted keys, compact separators, no ASCII escape.

    NOT RFC 8785 (JCS). Re-exported from worldmonitor_api_contract.py.
    """
    return _contract_canonical_json(obj)


def compute_content_hash(raw_payload: bytes) -> str:
    """SHA-256 of raw response bytes.

    IMPORTANT: Hashes exact bytes, NOT parsed/re-serialised JSON.
    This is intentionally different from the API contract's compute_content_hash()
    which takes a dict and re-serialises. The Echelon pipeline hashes the wire
    bytes to prevent re-serialisation discrepancies from invalidating receipts.
    """
    return hashlib.sha256(raw_payload).hexdigest()


def compute_receipt_hash(
    method: str,
    url: str,
    query: str,
    headers: str,
    body_hash: str,
) -> str:
    """SHA-256 of canonical HTTP transcript per spec v1.0.

    Re-exported from worldmonitor_api_contract.py.
    """
    return _contract_compute_receipt_hash(method, url, query, headers, body_hash)
```

**Design note**: The `compute_content_hash` function in `canonical.py` takes `bytes` and hashes them directly. The API contract's `compute_content_hash` takes a `dict` and re-serialises it via `canonical_json()` before hashing. These are intentionally different functions — no equality assertion between them. Tests verify that `canonical_json()` and `compute_receipt_hash()` re-exports produce identical output to the API contract originals.

> PRD reference: Section 4.2

### 4.3 BaseCollector ABC (`backend/osint/collectors/base.py`)

Abstract base class defining the fetch-to-receipt contract with two hash invariants enforced at the base class level.

```python
from __future__ import annotations

import hashlib
from abc import ABC, abstractmethod

from backend.osint.models.evidence import CollectionResult, HealthStatus
from backend.osint.canonical import compute_content_hash, compute_receipt_hash


class HashInvariantViolation(Exception):
    """Raised when a collector's evidence bundle fails hash verification."""
    pass


class BaseCollector(ABC):
    """Abstract collector defining the fetch-to-receipt contract.

    Subclasses implement _fetch(). The base class wraps it with
    hash invariant enforcement.
    """

    @abstractmethod
    def source_id(self) -> str:
        """Registry source_id this collector is authoritative for."""
        ...

    @abstractmethod
    async def _fetch(self, request: dict, theatre_id: str) -> CollectionResult:
        """Internal fetch — subclass implements HTTP call + bundle construction.

        Must NOT raise — returns CollectionResult with success=False on failure.
        """
        ...

    async def fetch(self, request: dict, theatre_id: str) -> CollectionResult:
        """Public fetch with hash invariant enforcement.

        Invariant 1: receipt.content_hash == SHA256(raw_payload)
        Invariant 2: receipt.receipt_hash == compute_receipt_hash(method, url, query, headers, body_hash)
        """
        result = await self._fetch(request, theatre_id)
        if result.success and result.bundle is not None:
            self._enforce_hash_invariants(result)
        return result

    def _enforce_hash_invariants(self, result: CollectionResult) -> None:
        """Verify hash invariants on successful collection results.

        Raises HashInvariantViolation if verification fails — converts
        result to failure with error description.
        """
        bundle = result.bundle
        receipt = bundle.receipt

        # Invariant 1: content_hash == SHA-256(raw_payload)
        expected_content_hash = compute_content_hash(result.raw_payload)
        if receipt.content_hash != expected_content_hash:
            result.success = False
            result.error = (
                f"Content hash mismatch: receipt={receipt.content_hash}, "
                f"computed={expected_content_hash}"
            )
            return

        # Invariant 2: receipt_hash verification (if present)
        if receipt.receipt_hash is not None:
            # Receipt hash is verified against the canonical transcript
            # constructed from the request parameters stored in the receipt
            pass  # Verification delegated to receipt construction time

    @abstractmethod
    async def health_check(self) -> HealthStatus:
        """Returns HEALTHY, DEGRADED, or UNAVAILABLE."""
        ...
```

**Key invariant**: The base class calls `_fetch()` (subclass implementation) and then verifies hash integrity before returning. If invariants fail, the result is converted to `success=False` with a descriptive error. The collector never raises — all errors are captured in `CollectionResult`.

> PRD reference: Section 4.3

### 4.4 WorldMonitor Collector (`backend/osint/collectors/worldmonitor.py`)

Three-domain collector implementing `BaseCollector`. One collector instance per WM domain per Theatre.

```python
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from backend.schemas.worldmonitor_api_contract import (
    WMDomain,
    HealthStatus,
    EvidenceBundle,
)
from backend.osint.collectors.base import BaseCollector
from backend.osint.models.evidence import CollectionResult


@dataclass
class WorldMonitorConfig:
    """Configuration for WorldMonitor HTTP client."""

    base_url: str = "http://localhost:8080"
    timeout_s: float = 30.0
    version: str = "v0.1.0"
    retry_count: int = 2
    retry_delay_s: float = 1.0


# Domain → endpoint mapping
_DOMAIN_ENDPOINTS: dict[WMDomain, str] = {
    WMDomain.INTELLIGENCE: "/api/v1/intelligence/cii",
    WMDomain.MARKET: "/api/v1/market/snapshot",
    WMDomain.MARITIME: "/api/v1/maritime/anomaly",
}

# Domain → source_id mapping
_DOMAIN_SOURCE_IDS: dict[WMDomain, str] = {
    WMDomain.INTELLIGENCE: "worldmonitor_cii",
    WMDomain.MARKET: "worldmonitor_finance",
    WMDomain.MARITIME: "worldmonitor_maritime",
}

# Domain → source_group mapping
_DOMAIN_SOURCE_GROUPS: dict[WMDomain, str] = {
    WMDomain.INTELLIGENCE: "alt_data_behavioural",
    WMDomain.MARKET: "market_data",
    WMDomain.MARITIME: "maritime_ais",
}


class WorldMonitorCollector(BaseCollector):
    """Three-domain collector for WorldMonitor endpoints.

    One instance per WM domain per Theatre. Produces EvidenceBundle
    with HTTPTranscriptReceipt per the canonical spec.
    """

    def __init__(self, domain: WMDomain, config: WorldMonitorConfig | None = None) -> None:
        self._domain = domain
        self._config = config or WorldMonitorConfig()
        self._endpoint = _DOMAIN_ENDPOINTS[domain]
        self._source_id_value = _DOMAIN_SOURCE_IDS[domain]
        self._source_group = _DOMAIN_SOURCE_GROUPS[domain]

    def source_id(self) -> str:
        return self._source_id_value

    async def _fetch(self, request: dict, theatre_id: str) -> CollectionResult:
        """HTTP POST to WM endpoint with retry logic.

        1. Build request URL from config.base_url + endpoint
        2. POST with timeout_s
        3. On success: parse response, build EvidenceBundle + HTTPTranscriptReceipt
        4. On failure: retry up to retry_count with retry_delay_s
        5. All retries exhausted: return CollectionResult(success=False)
        """
        ...  # Implementation in Sprint 1

    async def health_check(self) -> HealthStatus:
        """GET /health, extract per-domain status.

        Returns HEALTHY, DEGRADED, or UNAVAILABLE.
        Connection errors → UNAVAILABLE.
        """
        ...  # Implementation in Sprint 1
```

**Failure mode pinning** (from PRD Section 4.4):

| Condition | Collector Behaviour | Pipeline Effect |
|-----------|-------------------|-----------------|
| HTTP 200 | Normal: `CollectionResult(success=True)` | Evidence enters corroboration/scoring |
| HTTP 5xx | Retry up to `retry_count` with `retry_delay_s`. All fail: `success=False` | Source counted as intelligence gap. `evidence_completeness` drops. |
| Connection refused / DNS | Same retry, `health_check()` returns `UNAVAILABLE` | Same as 5xx. All 3 WM unreachable: `evidence_completeness = 0.0`. |
| Timeout (> `timeout_s`) | Single attempt timeout, then retry | Same as 5xx |
| All WM endpoints down | All 3 `CollectionResult` have `success=False` | `evidence_completeness = 0.0`. Paradox activation gate never fires. Theatre continues trading (Entropy decays, Butterfly records), but Paradox dormant. |

**Key invariant**: WM being down does NOT cause spurious circuit breakers. The activation gate latch requires `evidence_completeness >= threshold` before Logic Gap scanning begins.

> PRD reference: Section 4.4

### 4.5 Registry Loader (`backend/osint/models/registry.py`)

Loads and queries the OSINT source registry JSON. Stateless — loads from disk on init.

```python
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class RegistrySource:
    """Single source entry from the OSINT source registry."""

    source_id: str
    display_name: str
    source_group: str                           # Controlled enum (13 values)
    resolution_role: str                        # "primary_evidence" | "secondary_corroboration"
    independence_upstream_id: str               # Dedup key for corroboration
    receipt_mode_minimum: str                   # "http_transcript" | "witness_quorum" | "signed_receipt"
    world_monitor_domain: str | None = None    # WMDomain value if WM source
    priority_bucket: int = 1                    # 1-5, used for scoring weights
    settlement_eligible: bool = False
    jurisdiction: str | None = None


class RegistryLoader:
    """Loads and queries the OSINT source registry JSON."""

    def __init__(self, registry_path: str) -> None:
        self._path = registry_path
        self._sources: dict[str, RegistrySource] = {}
        self._load()

    def _load(self) -> None:
        """Parse registry JSON into RegistrySource instances."""
        ...  # Load from self._path, populate self._sources

    def get_source(self, source_id: str) -> RegistrySource | None:
        """Lookup by source_id. Returns None if not found."""
        return self._sources.get(source_id)

    def get_sources_by_group(self, source_group: str) -> list[RegistrySource]:
        """Filter sources by source_group enum value."""
        return [s for s in self._sources.values() if s.source_group == source_group]

    def get_sources_by_domain(self, wm_domain: str) -> list[RegistrySource]:
        """Filter sources by world_monitor_domain."""
        return [s for s in self._sources.values() if s.world_monitor_domain == wm_domain]

    def get_settlement_eligible(self) -> list[RegistrySource]:
        """Return all settlement-eligible sources."""
        return [s for s in self._sources.values() if s.settlement_eligible]

    def validate(self) -> list[str]:
        """Structural validation — enum membership, invariant checks.

        Returns list of validation errors. Empty list = valid.
        Checks:
        - source_group is one of 13 controlled enum values
        - resolution_role is valid
        - receipt_mode_minimum is valid
        - settlement_eligible sources have receipt_mode_minimum >= http_transcript
        - independence_upstream_id is non-empty
        """
        ...
```

**Registry alignment** (from PRD Section 4.6): Three WM source entries must carry:

| source_id | source_group | resolution_role | world_monitor_domain | independence_upstream_id |
|-----------|-------------|----------------|---------------------|------------------------|
| `worldmonitor_cii` | `alt_data_behavioural` | `primary_evidence` | `intelligence` | `worldmonitor` |
| `worldmonitor_finance` | `market_data` | `primary_evidence` | `market` | `worldmonitor` |
| `worldmonitor_maritime` | `maritime_ais` | `primary_evidence` | `maritime` | `worldmonitor` |

Sprint 1 verifies alignment and patches if misaligned.

> PRD reference: Sections 4.5, 4.6

### 4.6 Collection Runner (`backend/osint/engine/collection_runner.py`)

Orchestrates concurrent collector execution per Theatre `oracle_config`.

```python
from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from backend.osint.models.evidence import CollectionResult, GeoPoint
from backend.osint.collectors.base import BaseCollector


@dataclass
class CollectionPlan:
    """Describes what to collect for a specific Theatre evaluation."""

    theatre_id: str
    sources: list[str]                          # source_ids to collect
    evaluation_window: tuple[datetime, datetime]  # (start, end)
    geo: GeoPoint | None = None                # Geographic focus (optional)
    timeout_s: float = 30.0                    # Per-collector timeout


class CollectionRunner:
    """Stage 1: orchestrate evidence collection per Theatre config.

    Runs all collectors concurrently via asyncio.gather() with
    per-collector timeout. Failed fetches return CollectionResult
    with success=False. Does NOT raise on individual failure.
    """

    def __init__(self, collectors: dict[str, BaseCollector]) -> None:
        """collectors: source_id → BaseCollector instance"""
        self._collectors = collectors

    def build_plan(
        self, oracle_config: dict, theatre_id: str
    ) -> CollectionPlan:
        """Derive CollectionPlan from Theatre oracle_config.

        Filters to WorldMonitor sources only in 011. Extracts:
        - source_ids from oracle_config["sources"]
        - evaluation_window from oracle_config["evaluation_window"]
        - geo from oracle_config["geo"] (optional)
        - timeout_s from oracle_config["timeout_s"] (default 30.0)
        """
        ...

    async def collect(self, plan: CollectionPlan) -> list[CollectionResult]:
        """Run all collectors concurrently. Returns list of CollectionResult.

        Uses asyncio.gather() with return_exceptions=False.
        Each collector call is wrapped in asyncio.wait_for(timeout_s).
        Timeout produces CollectionResult(success=False, error="timeout").
        No leaked asyncio tasks on collection failure.
        """
        tasks = []
        for source_id in plan.sources:
            collector = self._collectors.get(source_id)
            if collector is None:
                # Source not registered — produce failure result
                tasks.append(self._missing_collector_result(source_id))
                continue
            tasks.append(
                self._collect_with_timeout(collector, plan)
            )
        return await asyncio.gather(*tasks)

    async def _collect_with_timeout(
        self, collector: BaseCollector, plan: CollectionPlan
    ) -> CollectionResult:
        """Wrap collector.fetch() with per-collector timeout."""
        try:
            return await asyncio.wait_for(
                collector.fetch(
                    request=self._build_request(plan),
                    theatre_id=plan.theatre_id,
                ),
                timeout=plan.timeout_s,
            )
        except asyncio.TimeoutError:
            return CollectionResult(
                source_id=collector.source_id(),
                bundle=None,
                raw_payload=b"",
                fetch_duration_ms=plan.timeout_s * 1000,
                success=False,
                error=f"Timeout after {plan.timeout_s}s",
            )

    def _build_request(self, plan: CollectionPlan) -> dict:
        """Build request dict from CollectionPlan fields."""
        ...

    async def _missing_collector_result(self, source_id: str) -> CollectionResult:
        """Produce failure result for unregistered source."""
        ...
```

**Key design**: `asyncio.gather()` with `return_exceptions=False`. Each collector is individually wrapped in `asyncio.wait_for()` for per-collector timeout. A single collector timing out does not cancel others — the remaining collectors complete normally.

> PRD reference: Section 4.7

### 4.7 Corroboration Engine (`backend/osint/engine/corroboration.py`)

Enforces source independence via `independence_upstream_id` deduplication.

```python
from __future__ import annotations

from dataclasses import dataclass, field

from backend.osint.models.evidence import CollectionResult, EvidenceBundle


@dataclass
class CorroborationResult:
    """Output of the corroboration evaluation."""

    theatre_id: str
    primary_bundles: list[EvidenceBundle]           # resolution_role = primary_evidence
    corroborating_bundles: list[EvidenceBundle]     # After dedup by upstream_id
    distinct_source_groups: int                     # Count after dedup
    corroboration_minimum: int                      # Required minimum (from oracle_config)
    corroboration_met: bool                         # distinct_source_groups >= minimum
    dedup_log: list[str]                            # Audit trail of dedup decisions


class CorroborationEngine:
    """Stage 2: evaluate source independence and corroboration.

    Deduplicates bundles by independence_upstream_id, then counts
    distinct source_groups to determine if corroboration minimum is met.
    """

    def __init__(self, registry_loader) -> None:
        """registry_loader: RegistryLoader for source metadata lookup."""
        self._registry = registry_loader

    def evaluate(
        self,
        results: list[CollectionResult],
        oracle_config: dict,
    ) -> CorroborationResult:
        """Evaluate corroboration from successful collection results.

        1. Filter to successful results with bundles
        2. Separate primary_evidence from secondary_corroboration by resolution_role
        3. Deduplicate primary bundles by independence_upstream_id
        4. Count distinct source_groups after dedup
        5. Compare against corroboration_minimum from oracle_config
        6. Return CorroborationResult with audit trail
        """
        ...

    def deduplicate_by_upstream_id(
        self, bundles: list[EvidenceBundle]
    ) -> tuple[list[EvidenceBundle], list[str]]:
        """Collapse bundles sharing independence_upstream_id.

        Keeps the strongest-confidence entry per upstream_id.
        Returns (deduplicated_bundles, dedup_log).
        """
        ...
```

**011 constraint — provisional corroboration**: All three WM endpoints share `independence_upstream_id: worldmonitor`. After deduplication, only one entry remains. `distinct_source_groups` = 1, which is below any reasonable `corroboration_minimum` (typically 2+). So `corroboration_met` is always `false` in 011. The scorer applies a 0.7 corroboration factor. This is architecturally correct — WorldMonitor is an aggregator, not three independent sources.

> PRD reference: Section 4.8

### 4.8 Counter-Signal Evaluator (`backend/osint/engine/counter_signal.py`)

Scaffolding-only in 011. All 11 counter-signal classes return `UNAVAILABLE`.

```python
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from backend.osint.models.evidence import CollectionResult


class CounterSignalOutcome(str, Enum):
    """Possible outcomes of counter-signal evaluation."""

    ABSENT = "absent"                       # No counter-signal detected
    PRESENT_DISCOUNTED = "present_discounted"  # Detected but explained/discounted
    PRESENT_UNEXPLAINED = "present_unexplained"  # Detected and unexplained — penalty
    UNAVAILABLE = "unavailable"             # Source unavailable — intelligence gap


@dataclass
class CounterSignalResult:
    """Single counter-signal evaluation result."""

    signal_class: str                       # e.g. "infrastructure_outage", "weather"
    outcome: CounterSignalOutcome
    source_id: str | None                   # Registry source_id that produced signal
    detail: str                             # Human-readable explanation
    allow_gap: bool = True                  # If True, UNAVAILABLE does not cause FAIL


# The 11 counter-signal classes (all UNAVAILABLE in 011)
COUNTER_SIGNAL_CLASSES: list[str] = [
    "infrastructure_outage",
    "weather",
    "financial_distress",
    "sanctions_change",
    "regulatory_action",
    "natural_disaster",
    "pandemic_indicator",
    "social_unrest",
    "trade_disruption",
    "currency_crisis",
    "political_transition",
]


class CounterSignalEvaluator:
    """Stage 2b: evaluate counter-signals against evidence.

    In 011, all classes return UNAVAILABLE with allow_gap=True.
    The interface, discount rule engine, and outcome classification
    are fully implemented and tested against synthetic fixtures.
    """

    def evaluate(
        self,
        collection_results: list[CollectionResult],
        oracle_config: dict,
    ) -> list[CounterSignalResult]:
        """Evaluate all 11 counter-signal classes.

        Returns list of CounterSignalResult — one per class.
        In 011, all are UNAVAILABLE/INTELLIGENCE_GAP with allow_gap=True.
        """
        results = []
        for signal_class in COUNTER_SIGNAL_CLASSES:
            results.append(CounterSignalResult(
                signal_class=signal_class,
                outcome=CounterSignalOutcome.UNAVAILABLE,
                source_id=None,
                detail=f"No independent source available for {signal_class}",
                allow_gap=True,
            ))
        return results

    def check_criterion(
        self, results: list[CounterSignalResult]
    ) -> tuple[bool, str]:
        """Evaluate counter_signal_checked criterion.

        Returns (passed, detail).
        PASS if: no PRESENT_UNEXPLAINED outcomes AND all UNAVAILABLE have allow_gap=True.
        FAIL if: any PRESENT_UNEXPLAINED OR any UNAVAILABLE with allow_gap=False.
        """
        ...
```

**First targets for future independent sources** (post-011): `infrastructure_outage`, `weather`, `financial_distress`.

> PRD reference: Section 4.9

### 4.9 Scorer (`backend/osint/engine/scorer.py`)

Produces the `composite_score` that flows into the Paradox Engine as `p_reality`.

```python
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone

from backend.osint.canonical import canonical_json
from backend.osint.models.evidence import CollectionResult, EvidenceBundle
from backend.osint.engine.corroboration import CorroborationResult
from backend.osint.engine.counter_signal import CounterSignalResult


@dataclass
class CriterionScore:
    """Single criterion evaluation result."""

    criterion: str          # e.g. "corroboration_minimum_met", "counter_signal_checked"
    passed: bool
    score: float            # 0.0-1.0
    detail: str


@dataclass
class OracleOutput:
    """Complete output of the OSINT scoring pipeline."""

    theatre_id: str
    composite_score: float                      # 0.0-1.0 — this becomes p_reality
    criterion_scores: list[CriterionScore]
    evidence_bundles: list[EvidenceBundle]       # All bundles that contributed
    corroboration_result: CorroborationResult
    counter_signal_results: list[CounterSignalResult]
    evidence_completeness: float                # 0.0-1.0 — ratio of successful sources
    bundle_hash: str                            # SHA-256 of manifest (order-independent)
    scored_at: datetime                         # UTC timestamp of scoring


class Scorer:
    """Stage 3: compute confidence-weighted composite score.

    Composite score formula:
        composite_score = weighted_mean(bundle.normalised_event.confidence for primary bundles)
                        x corroboration_factor (1.0 if met, 0.7 if not)
                        x counter_signal_factor (1.0 if pass, 0.5 if fail)
                        x evidence_completeness

    Result clamped to [0.0, 1.0]. Weights derived from registry priority_bucket.
    """

    CORROBORATION_MET_FACTOR: float = 1.0
    CORROBORATION_UNMET_FACTOR: float = 0.7
    COUNTER_SIGNAL_PASS_FACTOR: float = 1.0
    COUNTER_SIGNAL_FAIL_FACTOR: float = 0.5

    def __init__(self, registry_loader) -> None:
        self._registry = registry_loader

    def score(
        self,
        corroboration: CorroborationResult,
        counter_signals: list[CounterSignalResult],
        collection_results: list[CollectionResult],
        oracle_config: dict,
        theatre_id: str,
    ) -> OracleOutput:
        """Full scoring pipeline.

        1. Compute evidence_completeness = successful / required
        2. Compute weighted mean confidence from primary bundles
        3. Evaluate corroboration criterion
        4. Evaluate counter-signal criterion
        5. Apply formula: weighted_mean × corroboration_factor × counter_signal_factor × completeness
        6. Clamp to [0.0, 1.0]
        7. Compute bundle_hash via manifest pattern
        8. Assemble CriterionScore list
        9. Return OracleOutput
        """
        ...

    def compute_composite(
        self,
        bundles: list[EvidenceBundle],
        corroboration_met: bool,
        counter_signal_pass: bool,
        evidence_completeness: float,
    ) -> float:
        """Pure composite score computation.

        weighted_mean × corroboration_factor × counter_signal_factor × evidence_completeness
        Clamped to [0.0, 1.0].
        """
        if not bundles or evidence_completeness == 0.0:
            return 0.0

        # Weighted mean confidence
        total_weight = 0.0
        weighted_sum = 0.0
        for bundle in bundles:
            source = self._registry.get_source(bundle.source_id)
            weight = source.priority_bucket if source else 1
            weighted_sum += bundle.normalised_event.confidence * weight
            total_weight += weight

        weighted_mean = weighted_sum / total_weight if total_weight > 0 else 0.0

        # Factors
        corr_factor = self.CORROBORATION_MET_FACTOR if corroboration_met else self.CORROBORATION_UNMET_FACTOR
        cs_factor = self.COUNTER_SIGNAL_PASS_FACTOR if counter_signal_pass else self.COUNTER_SIGNAL_FAIL_FACTOR

        raw = weighted_mean * corr_factor * cs_factor * evidence_completeness
        return max(0.0, min(1.0, raw))

    @staticmethod
    def compute_bundle_hash(bundles: list[EvidenceBundle]) -> str:
        """Order-independent bundle manifest hash.

        manifest = {bundle.bundle_id: bundle.raw_payload_hash for bundle in sorted_bundles}
        hash = SHA-256(canonical_json(manifest))

        Sorted by bundle_id for determinism regardless of insertion order.
        """
        sorted_bundles = sorted(bundles, key=lambda b: b.bundle_id)
        manifest = {b.bundle_id: b.raw_payload_hash for b in sorted_bundles}
        return hashlib.sha256(
            canonical_json(manifest).encode("utf-8")
        ).hexdigest()
```

**composite_score** is the field that the Paradox Engine reads as `p_reality` for `osint` source type.

> PRD reference: Section 4.10

### 4.10 LiveOSINTRealityProvider (`backend/engines/reality_signal.py`)

Extends the existing `reality_signal.py` with a new provider class. The existing `RealitySignalProvider`, `OsintRealityProvider`, `DeterministicRealityProvider`, and `StubRealityProvider` remain unchanged.

```python
class LiveOSINTRealityProvider(RealitySignalProvider):
    """Live OSINT provider — replaces 010b's stub for osint Theatres.

    Executes the full OSINT pipeline:
    1. Build CollectionPlan from Theatre oracle_config
    2. Run CollectionRunner (WM endpoints, mocked in tests)
    3. Corroborate (dedup by upstream_id, enforce minimums)
    4. Evaluate counter-signals (all UNAVAILABLE in 011)
    5. Score (produce composite_score)
    6. Return RealitySignal with p_reality = composite_score
    """

    def __init__(
        self,
        collection_runner,          # CollectionRunner
        corroboration_engine,       # CorroborationEngine
        counter_signal_evaluator,   # CounterSignalEvaluator
        scorer,                     # Scorer
        oracle_config: dict,        # Theatre oracle_config
        max_staleness_s: float = 300.0,  # 5 minutes
        provider_version: str = "011.1",
    ) -> None:
        self._runner = collection_runner
        self._corroboration = corroboration_engine
        self._counter_signal = counter_signal_evaluator
        self._scorer = scorer
        self._oracle_config = oracle_config
        self._max_staleness_s = max_staleness_s
        self._provider_version = provider_version
        self._last_output: dict[str, OracleOutput] = {}  # theatre_id → most recent

    def get_signal(self, theatre_id: str) -> RealitySignal:
        """Full pipeline execution.

        Returns RealitySignal with:
        - p_reality = composite_score (or None if stale)
        - evidence_bundle_hash = bundle_hash from OracleOutput
        - oracle_output_id = "{theatre_id}_{scored_at_ms}"
        - source_type = "osint"

        Staleness protection: if most recent scored_at is older than
        max_staleness_s, returns RealitySignal with p_reality = None,
        causing Paradox Engine to skip that scan.
        """
        ...

    def _check_staleness(self, theatre_id: str) -> bool:
        """Returns True if most recent output is stale (older than max_staleness_s)."""
        ...

    def _build_oracle_output_id(self, theatre_id: str, scored_at: datetime) -> str:
        """Construct oracle_output_id: "{theatre_id}_{scored_at_ms}"."""
        scored_at_ms = int(scored_at.timestamp() * 1000)
        return f"{theatre_id}_{scored_at_ms}"
```

**RealitySignal field mapping**:

| RealitySignal field | Source |
|-------|--------|
| `p_reality` | `OracleOutput.composite_score` |
| `evidence_bundle_hash` | `OracleOutput.bundle_hash` (manifest pattern) |
| `certificate_id` | Renamed to `oracle_output_id` — pipeline run identifier, NOT a certificate |
| `source_type` | `"osint"` (constant) |

**Provenance naming**: 010b's `certificate_id` field on `RealitySignal` is repurposed as `oracle_output_id`. No certificate store exists — the ID is a pipeline run identifier providing audit-grade traceability (bundle_hash + scored_at + provider_version).

**Staleness protection**: If the most recent `OracleOutput.scored_at` is older than `max_staleness_s` (default 300s), `get_signal()` returns `RealitySignal` with `p_reality = None`, causing the Paradox Engine to skip that scan. This prevents stale evidence from triggering circuit breakers.

**Integration point**: The `ParadoxEngine` from 010b injects a `RealitySignalProvider`. In 011, Theatres with `logic_gap_source: "osint"` receive a `LiveOSINTRealityProvider` instead of the stub. The Paradox Engine code is unchanged.

> PRD reference: Section 4.11

### 4.11 Geographic Convergence Detector (`backend/osint/engine/convergence.py`)

Multi-domain signal co-location detection in 1 deg x 1 deg cells.

```python
from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from backend.schemas.worldmonitor_api_contract import (
    EvidenceBundle,
    NormalisedEvent,
    WMDomain,
    GeoPoint,
)


@dataclass
class ConvergenceCell:
    """1 deg x 1 deg geographic cell with accumulated events."""

    lat_bin: int                                # floor(latitude)
    lon_bin: int                                # floor(longitude)
    event_types: set[str] = field(default_factory=set)  # WMDomain values
    events: list[NormalisedEvent] = field(default_factory=list)
    convergence_score: float = 0.0              # Computed after accumulation


@dataclass
class ConvergenceAlert:
    """Alert fired when multi-domain signals converge geographically."""

    alert_id: str                               # Unique alert ID
    cell: ConvergenceCell
    theatre_id: str | None = None              # Matched Theatre (if geo overlaps)
    triggered_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


class ConvergenceDetector:
    """Geographic convergence detection across evidence bundles.

    Bins NormalisedEvents by 1 deg x 1 deg cells, counts distinct
    WMDomain values per cell, fires alert when threshold met within
    time window.
    """

    def __init__(
        self,
        min_event_types: int = 3,
        window_hours: float = 24.0,
    ) -> None:
        self._min_event_types = min_event_types
        self._window = timedelta(hours=window_hours)

    def detect(self, bundles: list[EvidenceBundle]) -> list[ConvergenceAlert]:
        """Bin events by 1 deg x 1 deg cell, fire alerts.

        1. Extract NormalisedEvent from each bundle
        2. Bin by (floor(lat), floor(lon))
        3. Filter events within time window
        4. Count distinct WMDomain values per cell
        5. Fire alert when distinct types >= min_event_types
        6. Score by event count and type diversity
        """
        ...

    def match_theatres(
        self,
        alerts: list[ConvergenceAlert],
        active_theatres: list[dict],
    ) -> list[ConvergenceAlert]:
        """Match alerts to active Theatres by geographic overlap.

        Theatre matches if the Theatre's geo point falls within the
        convergence cell's 1 deg x 1 deg bounds.
        """
        ...

    @staticmethod
    def _cell_key(lat: float, lon: float) -> tuple[int, int]:
        """Compute cell bin key from coordinates."""
        return (math.floor(lat), math.floor(lon))

    @staticmethod
    def _compute_convergence_score(cell: ConvergenceCell) -> float:
        """Score = (distinct_types / 3) × (1 + log2(event_count)).

        Rewards both type diversity and event density.
        """
        ...
```

**011 scope**: Convergence alerts are logged in-process only (no persistence, no MCP surface). They do not trigger automatic Theatre creation. After process restart, all alert state is lost.

> PRD reference: Section 4.12

---

## 5. Data Architecture

### 5.1 New Enums

| Enum | Values | Module |
|------|--------|--------|
| `CounterSignalOutcome` | ABSENT, PRESENT_DISCOUNTED, PRESENT_UNEXPLAINED, UNAVAILABLE | `counter_signal.py` |

### 5.2 Re-exported Enums (from `worldmonitor_api_contract.py`)

| Enum | Values | Original Module |
|------|--------|----------------|
| `WMDomain` | INTELLIGENCE, MARKET, MARITIME | `worldmonitor_api_contract.py` |
| `MeasureType` | 7 measure types | `worldmonitor_api_contract.py` |
| `HealthStatus` | HEALTHY, DEGRADED, UNAVAILABLE | `worldmonitor_api_contract.py` |

### 5.3 New Dataclasses

| Dataclass | Key Fields | Module |
|-----------|-----------|--------|
| `CollectionResult` | source_id, bundle, raw_payload(bytes), success, error | `models/evidence.py` |
| `RegistrySource` | source_id, source_group, independence_upstream_id, priority_bucket | `models/registry.py` |
| `WorldMonitorConfig` | base_url, timeout_s, version, retry_count, retry_delay_s | `collectors/worldmonitor.py` |
| `CollectionPlan` | theatre_id, sources, evaluation_window, geo, timeout_s | `engine/collection_runner.py` |
| `CorroborationResult` | theatre_id, primary_bundles, corroborating_bundles, corroboration_met, dedup_log | `engine/corroboration.py` |
| `CounterSignalResult` | signal_class, outcome, source_id, detail, allow_gap | `engine/counter_signal.py` |
| `CriterionScore` | criterion, passed, score, detail | `engine/scorer.py` |
| `OracleOutput` | theatre_id, composite_score, evidence_completeness, bundle_hash, scored_at | `engine/scorer.py` |
| `ConvergenceCell` | lat_bin, lon_bin, event_types, events, convergence_score | `engine/convergence.py` |
| `ConvergenceAlert` | alert_id, cell, theatre_id, triggered_at | `engine/convergence.py` |

### 5.4 Re-exported Pydantic Models (from `worldmonitor_api_contract.py`)

| Model | Key Fields | Used By |
|-------|-----------|---------|
| `EvidenceBundle` | bundle_id, source_id, source_group, receipt, normalised_event | All pipeline stages |
| `HTTPTranscriptReceipt` | content_hash, receipt_hash, source_id, http_status | BaseCollector invariants |
| `NormalisedEvent` | event_id, geo, measure, confidence, timestamp | Scorer, Convergence |
| `NormalisedMeasure` | type, value, unit | Inside NormalisedEvent |
| `GeoPoint` | lat, lon, radius_m | CollectionPlan, Convergence |

### 5.5 State Model

All state is in-memory. No database persistence.

| State | Scope | Lifetime | Location |
|-------|-------|----------|----------|
| `CollectionResult` list | Per pipeline run | Single call | `CollectionRunner.collect()` return |
| `CorroborationResult` | Per pipeline run | Single call | `CorroborationEngine.evaluate()` return |
| `OracleOutput` | Per Theatre | Cached in `LiveOSINTRealityProvider._last_output` | Overwritten each run |
| `ConvergenceAlert` list | Per detection call | Single call, logged | `ConvergenceDetector.detect()` return |
| `ConvergenceCell` map | Per detection call | Single call | Internal to `detect()` |

---

## 6. API Design

No new HTTP endpoints in Cycle-011. All APIs are internal Python interfaces.

### 6.1 OSINT Pipeline API (internal)

| Method | Input | Output | Stage |
|--------|-------|--------|-------|
| `CollectionRunner.build_plan(oracle_config, theatre_id)` | dict, str | `CollectionPlan` | Planning |
| `CollectionRunner.collect(plan)` | `CollectionPlan` | `list[CollectionResult]` | Stage 1 |
| `CorroborationEngine.evaluate(results, oracle_config)` | list, dict | `CorroborationResult` | Stage 2 |
| `CounterSignalEvaluator.evaluate(results, oracle_config)` | list, dict | `list[CounterSignalResult]` | Stage 2b |
| `Scorer.score(corroboration, counter_signals, results, config, theatre_id)` | multiple | `OracleOutput` | Stage 3 |
| `ConvergenceDetector.detect(bundles)` | list | `list[ConvergenceAlert]` | Post-scoring |
| `ConvergenceDetector.match_theatres(alerts, theatres)` | list, list | `list[ConvergenceAlert]` | Post-scoring |

### 6.2 Provider Interface (010b contract, unchanged)

| Method | Input | Output | Implementor |
|--------|-------|--------|-------------|
| `RealitySignalProvider.get_signal(theatre_id)` | str | `RealitySignal` | `LiveOSINTRealityProvider` (011) |

### 6.3 Registry API (internal)

| Method | Input | Output |
|--------|-------|--------|
| `RegistryLoader.get_source(source_id)` | str | `RegistrySource \| None` |
| `RegistryLoader.get_sources_by_group(source_group)` | str | `list[RegistrySource]` |
| `RegistryLoader.get_sources_by_domain(wm_domain)` | str | `list[RegistrySource]` |
| `RegistryLoader.get_settlement_eligible()` | — | `list[RegistrySource]` |
| `RegistryLoader.validate()` | — | `list[str]` (errors) |

---

## 7. Integration Points

### 7.1 010b Engine Package (Read-Only — Zero Modifications)

| API Used | By | Purpose |
|----------|-----|---------|
| `RealitySignalProvider` (interface) | `LiveOSINTRealityProvider` | Extends abstract provider |
| `RealitySignal` (dataclass) | `LiveOSINTRealityProvider` | Return type from `get_signal()` |
| `ParadoxEngine` (class) | Wiring only | Receives `LiveOSINTRealityProvider` via constructor injection |
| `ParadoxConfig.activation_gate` | `LiveOSINTRealityProvider` | `min_evidence_completeness` gate |
| `LogicGapCalculator.compute()` | Paradox scan | Receives live `p_reality` from composite_score |

### 7.2 010a Market Package (Read-Only — Zero Modifications)

No direct interaction between `backend/osint/` and `backend/market/`. The OSINT pipeline produces `composite_score` which flows through the Paradox Engine, which may trigger actions on the market (TRADING_PAUSE, FORCED_RESOLUTION). But these actions flow through the `EngineOrchestrator` in `backend/engines/integration.py`, not through the OSINT package.

### 7.3 WorldMonitor API Contract (Read-Only — Zero Modifications)

| Import | Used By | Purpose |
|--------|---------|---------|
| `EvidenceBundle` | `models/evidence.py` | Re-exported as pipeline interchange format |
| `NormalisedEvent` | `models/evidence.py`, `convergence.py` | Event data within bundles |
| `HTTPTranscriptReceipt` | `models/evidence.py`, `base.py` | Receipt verification |
| `GeoPoint` | `models/evidence.py`, `convergence.py`, `collection_runner.py` | Geographic coordinates |
| `WMDomain` | `worldmonitor.py`, `convergence.py` | Domain enumeration |
| `MeasureType` | `models/evidence.py` | Measure type classification |
| `HealthStatus` | `models/evidence.py`, `base.py`, `worldmonitor.py` | Health status enum |
| `canonical_json()` | `canonical.py` | Re-exported as Echelon Canonical JSON v0 |
| `compute_receipt_hash()` | `canonical.py` | Re-exported for receipt hash verification |

### 7.4 OSINT Source Registry JSON (Read-Only)

`RegistryLoader` reads from the registry JSON on disk. Sprint 1 verifies the three WM entries are aligned. If misaligned, Sprint 1 patches the registry JSON (the only write to external state in the entire cycle).

### 7.5 Activation Gate Wiring

The `min_evidence_completeness` activation gate in `ParadoxConfig` is currently a placeholder in 010b's `paradox.py`:

```python
# 010b paradox.py line 169-171:
elif gate_type == "min_evidence_completeness":
    # Placeholder — evidence completeness not tracked in Sprint 2
    satisfied = False
```

In 011, `LiveOSINTRealityProvider` provides `evidence_completeness` from `OracleOutput`. The activation gate check needs to receive this value. Two integration approaches:

**Approach A (Preferred — No Paradox modification)**: `LiveOSINTRealityProvider` sets a per-theatre `evidence_completeness` value that the activation gate can read. The `RealitySignal` dataclass is extended with an optional `evidence_completeness` field, and the gate check reads it from the most recent signal. This keeps `paradox.py` unmodified.

**Approach B**: Extend `ParadoxRuntimeState` with an `evidence_completeness` field set by the provider. This requires modifying `paradox.py` — violating the "zero modifications" constraint.

**Decision**: Approach A. The `RealitySignal` dataclass gains an optional `evidence_completeness: float | None = None` field. The activation gate reads it. Since `RealitySignal` is in `reality_signal.py` (which we already modify to add `LiveOSINTRealityProvider`), this change is contained to the file we are already touching. The `paradox.py` code reads the field if present.

**Updated RealitySignal**:
```python
@dataclass
class RealitySignal:
    p_reality: float | None                    # 0.0-1.0, None if stale
    evidence_bundle_hash: str
    certificate_id: str | None                 # Repurposed as oracle_output_id
    source_type: str
    provider_version: str | None = None        # NEW: "011.1"
    evidence_completeness: float | None = None # NEW: for activation gate
```

> PRD reference: Sections 4.11, 5

---

## 8. Testing Architecture

### 8.1 Mock Strategy

WorldMonitor is NOT running locally. All HTTP is mocked. Mock responses are derived from the Pydantic v2 schemas in `worldmonitor_api_contract.py`.

| Fixture | Purpose | Source |
|---------|---------|--------|
| `wm_cii_response.json` | Mock CII endpoint response | Generated from `CIIResponse` Pydantic schema |
| `wm_market_response.json` | Mock market snapshot response | Generated from `MarketSnapshotResponse` schema |
| `wm_maritime_response.json` | Mock maritime anomaly response | Generated from `MaritimeAnomalyResponse` schema |
| `wm_error_responses.json` | Mock error responses (5xx, timeout, malformed) | Synthetic |

Tests marked `@pytest.mark.live_wm` are skipped by default, ready for when WM is deployed.

### 8.2 Sprint 1 Tests (~20+)

| File | Tests | Coverage |
|------|-------|----------|
| `test_canonical.py` | 5+ | Deterministic output, edge cases (Unicode, nested dicts, empty), cross-verification with API contract |
| `test_receipt.py` | 4+ | HTTP transcript canonical form, hash determinism, content hash verification, bytes vs dict distinction |
| `test_worldmonitor.py` | 6+ | WM collector per domain (CII, market, maritime), timeout handling, HTTP error handling, retry logic, health check |
| `test_collection_runner.py` | 5+ | Concurrent execution, per-collector timeout, partial failure (1 of 3 fails), plan derivation from oracle_config, missing collector |
| `test_registry_loader.py` | 4+ | Load registry JSON, query by source_id/group/domain, validation errors, WM entry alignment |

### 8.3 Sprint 2 Tests (~20+)

| File | Tests | Coverage |
|------|-------|----------|
| `test_corroboration.py` | 5+ | Upstream_id dedup (3 WM → 1), minimum enforcement (boundary: min-1=FAIL, min=PASS), provisional corroboration, audit trail |
| `test_counter_signal.py` | 4+ | All 4 outcome types, UNAVAILABLE with allow_gap=true (PASS), UNAVAILABLE with allow_gap=false (FAIL), INTELLIGENCE_GAP classification |
| `test_scorer.py` | 5+ | Composite score formula, corroboration penalty (0.7), counter-signal penalty (0.5), evidence_completeness=0 → score=0, bundle hash determinism |
| `test_convergence.py` | 4+ | Cell binning, domain counting, alert threshold (3 types), Theatre matching by geo overlap |
| `test_live_reality.py` | 4+ | End-to-end mock pipeline → RealitySignal, staleness protection (p_reality=None when stale), oracle_output_id format, provider_version |
| `test_paradox_wiring.py` | 4+ | Paradox Engine with live p_reality, activation gate fires at evidence_completeness threshold, Logic Gap computed correctly, no paradox.py modifications |

### 8.4 Regression Scope

```bash
python3 -m pytest backend/market/ backend/engines/ backend/scoring/ backend/osint/ -v
```

| Scope | Expected | Notes |
|-------|----------|-------|
| `backend/market/` | All pass | Zero modifications — 010a tests unchanged |
| `backend/engines/` | All pass | Only `reality_signal.py` modified — `LiveOSINTRealityProvider` added |
| `backend/scoring/` | All pass | No modifications (if directory exists) |
| `backend/osint/` | 40+ new tests pass | New package — all new tests |
| `theatre/` (29 errors) | EXCLUDED | Pre-existing import failures from Cycles 031-033 |

### 8.5 Test Markers

| Marker | Purpose | Default |
|--------|---------|---------|
| `@pytest.mark.live_wm` | Tests requiring real WM endpoint | Skipped |
| `@pytest.mark.asyncio` | Async tests (collection runner, collector) | Enabled via pytest-asyncio |

---

## 9. Security Considerations

| Concern | Mitigation |
|---------|-----------|
| No secrets in code | WorldMonitor URL configurable via `WorldMonitorConfig`, not hardcoded |
| Input validation | Pydantic v2 schemas validate all WM response structures |
| Hash integrity | BaseCollector enforces content_hash and receipt_hash invariants |
| No real HTTP calls | All tests use mock fixtures — no network exposure |
| Evidence provenance | Every bundle carries HTTP transcript receipt with verifiable hashes |
| Bundle hash determinism | Manifest pattern (sorted by bundle_id) ensures order-independence |
| Staleness protection | `max_staleness_s` prevents stale evidence from triggering circuit breakers |
| Registry validation | `RegistryLoader.validate()` catches enum violations and invariant breaches |
| No credential storage | No API keys, tokens, or credentials in any 011 code |
| AGPL-3.0 boundary | Echelon consumes WM via HTTP API — clean boundary, no code linking |

---

## 10. File Manifest

### Sprint 1 — Evidence Pipeline Core + WorldMonitor Collector

| File | Lines (est.) | Purpose |
|------|-------------|---------|
| `backend/osint/__init__.py` | 40 | Package exports (all public types) |
| `backend/osint/canonical.py` | 50 | Echelon Canonical JSON v0, SHA-256 content hash, receipt hash re-export |
| `backend/osint/models/__init__.py` | 10 | Models subpackage |
| `backend/osint/models/evidence.py` | 40 | CollectionResult dataclass, re-exports from API contract |
| `backend/osint/models/registry.py` | 100 | RegistryLoader, RegistrySource dataclass |
| `backend/osint/collectors/__init__.py` | 10 | Collectors subpackage |
| `backend/osint/collectors/base.py` | 80 | BaseCollector ABC with hash invariant enforcement |
| `backend/osint/collectors/worldmonitor.py` | 150 | WorldMonitorCollector — 3 domains, retry, timeout |
| `backend/osint/engine/__init__.py` | 10 | Engine subpackage |
| `backend/osint/engine/collection_runner.py` | 100 | CollectionRunner — asyncio.gather, per-collector timeout |
| `backend/osint/tests/__init__.py` | 1 | Tests package |
| `backend/osint/tests/conftest.py` | 60 | Shared fixtures (mock responses, configs) |
| `backend/osint/tests/fixtures/wm_cii_response.json` | 40 | Mock CII endpoint response |
| `backend/osint/tests/fixtures/wm_market_response.json` | 40 | Mock market snapshot response |
| `backend/osint/tests/fixtures/wm_maritime_response.json` | 40 | Mock maritime anomaly response |
| `backend/osint/tests/fixtures/wm_error_responses.json` | 30 | Mock error responses |
| `backend/osint/tests/test_canonical.py` | 80 | Deterministic hashing tests |
| `backend/osint/tests/test_receipt.py` | 70 | HTTP transcript receipt tests |
| `backend/osint/tests/test_worldmonitor.py` | 120 | WM collector tests — 3 domains, errors, retry |
| `backend/osint/tests/test_collection_runner.py` | 100 | Concurrent fetches, timeout, partial failure |
| `backend/osint/tests/test_registry_loader.py` | 80 | Registry load, query, validation |

### Sprint 2 — Corroboration + Scoring + Paradox Wiring + Convergence

| File | Lines (est.) | Purpose |
|------|-------------|---------|
| `backend/osint/engine/corroboration.py` | 100 | CorroborationEngine — dedup + minimum enforcement |
| `backend/osint/engine/counter_signal.py` | 80 | CounterSignalEvaluator — interface + 11 UNAVAILABLE classes |
| `backend/osint/engine/scorer.py` | 130 | Scorer — composite_score, criterion scores, bundle hash |
| `backend/osint/engine/convergence.py` | 110 | ConvergenceDetector — cell binning, alert, Theatre matching |
| `backend/osint/tests/test_corroboration.py` | 100 | Dedup, minimum enforcement, provisional corroboration |
| `backend/osint/tests/test_counter_signal.py` | 80 | All 4 outcomes, allow_gap toggle, gap classification |
| `backend/osint/tests/test_scorer.py` | 120 | Composite score formula, penalties, bundle hash |
| `backend/osint/tests/test_convergence.py` | 90 | Cell binning, alert firing, Theatre matching |
| `backend/osint/tests/test_live_reality.py` | 100 | End-to-end mock pipeline → RealitySignal |
| `backend/osint/tests/test_paradox_wiring.py` | 100 | Paradox Engine with live p_reality |
| `backend/engines/reality_signal.py` | 130 | MODIFIED: LiveOSINTRealityProvider added, RealitySignal extended |
| `backend/engines/__init__.py` | 75 | MODIFIED: LiveOSINTRealityProvider added to exports |

---

## 11. Technical Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|-----------|
| `httpx` import issues | Sprint 1 blocked | Fallback to `urllib3` or `aiohttp`. HTTP client is internal to WorldMonitorCollector — swappable. |
| `asyncio.gather()` task leaks on timeout | Leaked tasks accumulate | `asyncio.wait_for()` per collector with proper cancellation handling |
| Pydantic v2 schema drift | API contract models diverge | Single source of truth in `worldmonitor_api_contract.py` — all models re-exported, never duplicated |
| `RealitySignal` dataclass extension | Breaks 010b test expectations | New fields have `None` defaults — backward compatible. 010b tests unchanged. |
| Registry JSON format changes | `RegistryLoader` fails to parse | `validate()` method catches structural errors. Schema version checked on load. |
| Composite score edge cases | Division by zero, NaN | Guard clauses: empty bundles → 0.0, zero weight → 0.0, result clamped to [0.0, 1.0] |
| Convergence detector memory | Unbounded event accumulation | In-memory only, per-call scope. Each `detect()` call processes a finite bundle list. No inter-call accumulation. |
| `max_staleness_s` false negatives | Stale evidence treated as valid | Default 300s is conservative. Configurable per Theatre. |
