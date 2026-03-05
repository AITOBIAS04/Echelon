# SDD — Cycle-014c: Investigation Toolset Implementation

**Cycle:** cycle-014c
**Date:** 5 March 2026
**PRD:** grimoires/loa/prd.md
**Design input:** `Echelon_Investigation_Toolset_Design_Note_v1.md` (v1.3.0)

---

## 1. Architecture Overview

Cycle-014c adds a new `backend/investigation/` package containing runtime models, services, and hashing infrastructure for 8 investigation tools. All tools are in-memory/mock — no new external dependencies. The package integrates with existing infrastructure via:

1. `theatre/engine/canonical_json.py` — deterministic serialisation for all hashing
2. `backend/schemas/theatre.py` + `backend/database/models.py` — stop condition fields on Theatre
3. `backend/api/theatre_routes.py` — immutability enforcement for committed stop conditions
4. `backend/market/resolution.py` — stop condition evaluation in resolution engine

```
backend/investigation/
├── __init__.py
├── models.py                    # ProvenanceClass, EvidenceItem
├── evidence_envelope.py         # EvidenceEnvelope, RedactionEvent
├── claim_graph.py               # ClaimGraph, ClaimNode, Merkle root
├── counter_signals.py           # InvestigationCounterSignalClass/Feed
├── commitment_monitor.py        # CommitmentMonitor, DriftType/Event
├── signal_scanner.py            # SignalScanner, DomainFilter, DeltaBrief
├── entity_resolver.py           # EntityResolver, EntityProfile
├── corroboration_checker.py     # InvestigationCorroborationChecker
├── certificate.py               # InvestigationCertificate + Builder
├── stop_conditions.py           # StopCondition, Evaluator
├── artifacts.py                 # Deterministic JSON artefact writers
├── toolset.py                   # InvestigationToolset orchestrator
└── tests/                       # 67+ tests
```

Data flow for a complete investigation lifecycle:

```
Theatre created (DRAFT) with stop_condition + stop_config
  → Committed (commitment hash includes stop fields)
    → Investigation begins:
      → SignalScanner.scan() → DeltaBrief
      → EntityResolver.resolve() → EntityProfile
      → EvidenceEnvelope.submit() (append-only)
      → ClaimGraph.add_claim() (linked to evidence)
      → CorroborationChecker.evaluate_claim() → ClaimStatus
      → CounterSignalFeed.log_counter_signal()
      → CommitmentMonitor.log_drift()
    → Stop condition met (evaluator reads committed params only)
    → InvestigationCertificateBuilder.build() → InvestigationCertificate
    → Deterministic artefact writers → JSON files
```

---

## 2. Sprint 1 — Evidence Envelope + Claim Graph

### 2.1 ProvenanceClass + EvidenceItem

**New file:** `backend/investigation/models.py`

```python
from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field


class ProvenanceClass(str, Enum):
    PUBLIC_PRIMARY = "public_primary"
    PUBLIC_SECONDARY = "public_secondary"
    PRIVATE_LEAK = "private_leak"
    ANALYST_DERIVED = "analyst_derived"
    THIRD_PARTY_TOOL_OUTPUT = "third_party_tool_output"


class EvidenceItem(BaseModel):
    model_config = {"frozen": True}
    evidence_id: str                    # Sequential "E001", "E002", ...
    content_hash: str                   # SHA-256 of raw content bytes
    provenance_class: ProvenanceClass
    submitted_at: datetime
    content_type: str                   # MIME type
    source_description: str
    references: list[str] = Field(default_factory=list)
```

Frozen Pydantic model. SHA-256 hashing via `hashlib.sha256(content).hexdigest()`.

### 2.2 EvidenceEnvelope

**New file:** `backend/investigation/evidence_envelope.py`

```python
class RedactionEvent(BaseModel):
    model_config = {"frozen": True}
    redaction_id: str                   # "R001", "R002", ...
    evidence_id: str
    reason_class: str                   # accidental_secret | defamatory | illegal | doxxing | copyright
    redacted_at: datetime


class EvidenceEnvelope:
    """Append-only evidence container with Merkle-based integrity."""

    def __init__(self) -> None:
        self._items: list[EvidenceItem] = []
        self._redactions: list[RedactionEvent] = []
        self._counter: int = 0
        self._redaction_counter: int = 0

    def submit(self, content: bytes, provenance_class: ProvenanceClass,
               content_type: str, source_description: str,
               references: list[str] | None = None) -> EvidenceItem:
        """Append evidence item. Sequential ID, SHA-256 content hash."""

    def redact(self, evidence_id: str, reason_class: str) -> RedactionEvent:
        """Log redaction event. Does NOT alter envelope hash."""

    def get_item(self, evidence_id: str) -> EvidenceItem | None: ...
    def get_manifest(self) -> dict: ...

    def compute_envelope_hash(self) -> str:
        """SHA-256 of concatenated item content_hashes (including redacted)."""

    @property
    def items(self) -> list[EvidenceItem]: ...
    @property
    def redactions(self) -> list[RedactionEvent]: ...
    @property
    def provenance_summary(self) -> dict[str, int]: ...
```

**Immutability contract:** No `delete()` method. `redact()` adds metadata only. `compute_envelope_hash()` includes all items including redacted ones.

**Hash computation:** SHA-256 of pipe-separated `content_hash` values in submission order:
```python
hashlib.sha256("|".join(item.content_hash for item in self._items).encode()).hexdigest()
```

### 2.3 ClaimGraph + Merkle Root

**New file:** `backend/investigation/claim_graph.py`

```python
class ClaimType(str, Enum):
    FACT = "fact"
    CAUSAL = "causal"
    ATTRIBUTION = "attribution"


class ClaimStatus(str, Enum):
    SUPPORTED = "supported"
    PARTIALLY_SUPPORTED = "partially_supported"
    UNCONFIRMED = "unconfirmed"
    CONTRADICTED = "contradicted"


class CorroborationCheck(BaseModel):
    """Imported from corroboration_checker.py. Forward-declared here for type reference."""
    model_config = {"frozen": True}
    claim_id: str
    source_id: str
    upstream_group: str
    status: str
    confidence: float = Field(ge=0.0, le=1.0)


class ClaimNode(BaseModel):
    model_config = {"frozen": True}
    claim_id: str
    claim_text: str
    claim_type: ClaimType
    evidence_refs: list[str]
    osint_checks: list[CorroborationCheck] = Field(default_factory=list)
    counter_signals: list[str] = Field(default_factory=list)
    status: ClaimStatus = ClaimStatus.UNCONFIRMED
    confidence: float = Field(ge=0.0, le=1.0, default=0.0)
    independence_groups: list[str] = Field(default_factory=list)


class ClaimGraph:
    """Structured claim-evidence-source mapping with Merkle root."""

    def __init__(self) -> None:
        self._claims: list[ClaimNode] = []
        self._counter: int = 0

    def add_claim(self, claim_text: str, claim_type: ClaimType,
                  evidence_refs: list[str]) -> ClaimNode: ...

    def update_claim_status(self, claim_id: str, status: ClaimStatus,
                            confidence: float,
                            independence_groups: list[str]) -> ClaimNode:
        """Replace claim with updated status. Returns new frozen node."""

    def link_counter_signal(self, claim_id: str, counter_signal_id: str) -> None: ...

    def compute_root_hash(self) -> str:
        """Merkle root per design note §3.7."""

    def get_status_summary(self) -> dict[str, int]: ...

    @property
    def claims(self) -> list[ClaimNode]: ...
```

**Merkle hashing spec (§3.7):**

```python
from theatre.engine.canonical_json import canonical_json

def compute_root_hash(self) -> str:
    if not self._claims:
        return hashlib.sha256(b"").hexdigest()

    # 1. Sort claims by claim_id (lexicographic)
    sorted_claims = sorted(self._claims, key=lambda c: c.claim_id)

    # 2. Leaf hashes = SHA-256(canonical_json(claim))
    leaves = [
        hashlib.sha256(canonical_json(c.model_dump()).encode()).hexdigest()
        for c in sorted_claims
    ]

    # 3. Merkle tree: pairwise SHA-256, odd leaf duplicated
    while len(leaves) > 1:
        if len(leaves) % 2 == 1:
            leaves.append(leaves[-1])  # Duplicate odd leaf
        leaves = [
            hashlib.sha256((leaves[i] + leaves[i + 1]).encode()).hexdigest()
            for i in range(0, len(leaves), 2)
        ]

    return leaves[0]
```

---

## 3. Sprint 2 — Counter-Signals + Monitor + Scanner + Resolver + Checker

### 3.1 Investigation Counter-Signal Classes

**New file:** `backend/investigation/counter_signals.py`

Separate taxonomy from pipeline counter-signals in `osint/osint_pipeline/engine/counter_signal.py`. No shared enum, no shared state.

```python
class InvestigationCounterSignalClass(str, Enum):
    OFFICIAL_DENIAL = "official_denial"
    REGULATORY_CLEARANCE = "regulatory_clearance"
    FILING_CONTRADICTION = "filing_contradiction"
    COMPETING_ANALYSIS = "competing_analysis"
    TIMELINE_INCONSISTENCY = "timeline_inconsistency"
    SOURCE_RELIABILITY_DEGRADATION = "source_reliability_degradation"
    ENTITY_STATUS_CHANGE = "entity_status_change"
    JURISDICTIONAL_CONFLICT = "jurisdictional_conflict"
    RETRACTION_OR_CORRECTION = "retraction_or_correction"
    MARKET_DIVERGENCE = "market_divergence"
    WITNESS_SOURCE_RECANTATION = "witness_source_recantation"


class InvestigationCounterSignal(BaseModel):
    model_config = {"frozen": True}
    counter_signal_id: str
    signal_class: InvestigationCounterSignalClass
    detected_at: datetime
    evidence_ref: str | None = None
    material: bool
    resolution_impact: str
    detection_method: str  # "automated_osint" | "paradox_engine" | "human_submitted"


class InvestigationCounterSignalFeed:
    def __init__(self) -> None:
        self._signals: list[InvestigationCounterSignal] = []
        self._counter: int = 0

    def log_counter_signal(self, signal_class: InvestigationCounterSignalClass,
                           material: bool, resolution_impact: str,
                           detection_method: str,
                           evidence_ref: str | None = None) -> InvestigationCounterSignal: ...

    def get_summary(self) -> dict:
        """Returns {checked: N, gaps: N, material_contradictions: N}."""
        # Classes 10+11 only count toward 'checked' when explicitly logged

    def get_detail(self) -> list[dict]: ...

    @property
    def signals(self) -> list[InvestigationCounterSignal]: ...
```

**Key rule:** `MARKET_DIVERGENCE` and `WITNESS_SOURCE_RECANTATION` are event-driven. They only appear in `checked` count when an `InvestigationCounterSignal` instance for that class exists in `_signals`. They do not passively contribute to coverage metrics.

### 3.2 Commitment Monitor

**New file:** `backend/investigation/commitment_monitor.py`

```python
class DriftType(str, Enum):
    ENTITY_RESTRUCTURE = "entity_restructure"
    CONTRACT_AMENDMENT = "contract_amendment"
    MARKET_RULE_CHANGE = "market_rule_change"
    REGULATORY_STATUS_CHANGE = "regulatory_status_change"
    JURISDICTION_CHANGE = "jurisdiction_change"


class DriftImpact(str, Enum):
    MATERIAL = "material"
    NON_MATERIAL = "non_material"


class DriftEvent(BaseModel):
    model_config = {"frozen": True}
    drift_id: str
    drift_type: DriftType
    detected_at: datetime
    original_value: str
    new_value: str
    evidence_ref: str | None = None
    impact_assessment: DriftImpact


class CommitmentMonitor:
    def __init__(self) -> None:
        self._events: list[DriftEvent] = []
        self._counter: int = 0

    def log_drift(self, drift_type: DriftType, original_value: str,
                  new_value: str, impact_assessment: DriftImpact,
                  evidence_ref: str | None = None) -> DriftEvent: ...

    def has_material_drift(self) -> bool:
        return any(e.impact_assessment == DriftImpact.MATERIAL for e in self._events)

    @property
    def events(self) -> list[DriftEvent]: ...
```

### 3.3 Signal Scanner

**New file:** `backend/investigation/signal_scanner.py`

```python
class DomainFilter(str, Enum):
    CORPORATE_AND_ENTITY = "corporate_and_entity"
    FINANCE_AND_MARKETS = "finance_and_markets"
    MARITIME = "maritime"
    AIRSPACE = "airspace"
    GEOPOLITICAL_AND_CONFLICT = "geopolitical_and_conflict"
    CYBER_THREAT = "cyber_threat"
    PROPERTY_AND_LAND = "property_and_land"
    COURT_AND_LEGAL = "court_and_legal"
    SATELLITE_AND_EARTH_OBSERVATION = "satellite_and_earth_observation"

# Maps domain filters to OSINT registry source groups
DOMAIN_FILTER_SOURCE_GROUPS: dict[DomainFilter, list[str]] = {
    DomainFilter.CORPORATE_AND_ENTITY: ["official_gov", "corporate_filing", "entity_resolution"],
    DomainFilter.FINANCE_AND_MARKETS: ["market_data", "central_bank", "prediction_market"],
    DomainFilter.MARITIME: ["maritime_ais", "geospatial_verification"],
    DomainFilter.AIRSPACE: ["flight_tracking"],
    DomainFilter.GEOPOLITICAL_AND_CONFLICT: ["conflict_event", "humanitarian_data", "disaster_alert"],
    DomainFilter.CYBER_THREAT: ["cyber_threat"],
    DomainFilter.PROPERTY_AND_LAND: ["property_registry"],
    DomainFilter.COURT_AND_LEGAL: ["court_filing", "insolvency"],
    DomainFilter.SATELLITE_AND_EARTH_OBSERVATION: ["satellite_imagery", "seismology"],
}


class SourceQuery(BaseModel):
    model_config = {"frozen": True}
    source_id: str
    source_group: str
    query: str
    result_count: int
    access_tier: str  # "A", "B", "C"
    skipped: bool = False
    skip_reason: str | None = None


class Anomaly(BaseModel):
    model_config = {"frozen": True}
    anomaly_id: str
    source_id: str
    description: str
    severity: float = Field(ge=0.0, le=1.0)
    detected_at: datetime


class DeltaBrief(BaseModel):
    model_config = {"frozen": True}
    brief_id: str
    domain_filters: list[DomainFilter]
    generated_at: datetime
    source_queries: list[SourceQuery]
    anomalies: list[Anomaly]
    content_hash: str  # SHA-256 of canonical JSON


class SignalScanner:
    def __init__(self, domain_filters: list[DomainFilter]) -> None:
        self._domain_filters = domain_filters

    def scan(self, subject: str) -> DeltaBrief:
        """Mock scan. Returns stub DeltaBrief with source queries and empty anomalies."""

    @property
    def active_source_groups(self) -> list[str]:
        """Flatten domain filters to source groups."""

    def _build_manifest(self, queries: list[SourceQuery]) -> dict:
        """Scanner manifest with requested/resolved/skipped groups and access_tier_policy."""
```

**Access-tier policy:** Default tier A only. Tier B/C sources recorded as `skipped=True` with `skip_reason="access_tier_b_not_authorized"`.

### 3.4 Entity Resolver

**New file:** `backend/investigation/entity_resolver.py`

```python
class SourceQueryRecord(BaseModel):
    model_config = {"frozen": True}
    source_id: str
    source_name: str
    query_time: datetime
    result_found: bool
    fields_populated: list[str]


class EntityQuery(BaseModel):
    model_config = {"frozen": True}
    entity_name: str
    jurisdiction: str
    registration_number: str | None = None


class EntityProfile(BaseModel):
    model_config = {"frozen": True}
    entity_id: str
    entity_name: str
    jurisdiction: str
    registration_number: str | None = None
    incorporation_date: str | None = None
    registered_address: str | None = None
    directors: list[dict] = Field(default_factory=list)
    filing_history_summary: list[dict] = Field(default_factory=list)
    gazette_notices: list[dict] = Field(default_factory=list)
    regulatory_entries: list[dict] = Field(default_factory=list)
    source_queries: list[SourceQueryRecord] = Field(default_factory=list)
    profile_hash: str = ""  # SHA-256 of canonical JSON (set by resolver)


class EntityResolver:
    def resolve(self, query: EntityQuery) -> EntityProfile:
        """Stub resolver. Returns mock profile for Companies House + London Gazette."""
```

Profile hash computed via `canonical_json()` of the profile dict excluding `profile_hash` itself.

### 3.5 Corroboration Checker

**New file:** `backend/investigation/corroboration_checker.py`

```python
class CorroborationCheck(BaseModel):
    model_config = {"frozen": True}
    claim_id: str
    source_id: str
    upstream_group: str
    status: str  # confirmed | contradicted | unavailable
    confidence: float = Field(ge=0.0, le=1.0)


class InvestigationCorroborationChecker:
    def evaluate_claim(self, claim: ClaimNode,
                       checks: list[CorroborationCheck]) -> ClaimStatus:
        """Derive claim status from corroboration checks.

        Hard invariant: SUPPORTED requires >=2 distinct upstream_group values
        with status='confirmed'. No override, no admin bypass.

        PRIVATE_LEAK-only evidence cannot achieve SUPPORTED.
        Single upstream group → PARTIALLY_SUPPORTED at best.
        """

    def _count_independent_groups(self, checks: list[CorroborationCheck]) -> int:
        """Count distinct upstream_group values with status='confirmed'."""
```

---

## 4. Sprint 3 — Certificate + Stop Conditions + E2E

### 4.1 Stop Condition Contract

**Modified files:**

**`backend/schemas/theatre.py`** — Add to `TheatreCreate`:
```python
stop_condition: str | None = None   # "outcome_resolution" | "evidence_threshold" | "sponsor_defined"
stop_config: dict | None = None     # Committed parameters (thresholds, milestones)
```

**`backend/database/models.py`** — Add to Theatre model:
```python
stop_condition = Column(String(30), nullable=True)
stop_config = Column(JSON, nullable=True)
```

**New Alembic migration** — adds two nullable columns.

**`backend/api/theatre_routes.py`** — Modifications:
1. `create_theatre`: store `stop_condition` and `stop_config` from request
2. `commit_theatre`: include `stop_condition` and `stop_config` in commitment hash payload
3. `settle_theatre` (or any mutation path post-COMMITTED): reject changes to `stop_condition`/`stop_config` with 400/422

### 4.2 Investigation Certificate

**New file:** `backend/investigation/certificate.py`

```python
class StopCondition(str, Enum):
    OUTCOME_RESOLUTION = "outcome_resolution"
    EVIDENCE_THRESHOLD = "evidence_threshold"
    SPONSOR_DEFINED = "sponsor_defined"


class InvestigationCertificate(BaseModel):
    model_config = {"frozen": True}

    # Base fields (from CalibrationCertificate)
    certificate_id: str
    oracle_output_id: str
    inquiry_class: str = "INVESTIGATIVE"
    inquiry_question: str
    template_id: str
    composite_score: float
    verification_tier: str
    commitment_hash: str
    issued_at: datetime
    expires_at: datetime
    theatre_committed_at: datetime
    theatre_resolved_at: datetime

    # Investigation-specific
    stop_condition_used: StopCondition
    stop_condition_trigger: str
    evidence_bundle_hash: str
    evidence_item_count: int
    evidence_provenance_summary: dict[str, int]
    claim_graph_root_hash: str
    claim_count: int
    claim_status_summary: dict[str, int]
    independence_summary: dict[str, list[str]]
    counter_signal_summary: dict[str, int]
    counter_signal_detail: list[dict]
    drift_events: list[dict]
    redaction_events: list[dict]
    signal_scanner_domains: list[str]
    osint_source_manifest: list[dict]
    market_summary: dict

    # Routing
    routing_hint: str = "ALLOWED"
    review_reason_code: str | None = None

    # Anchoring
    anchor_frequency: str = "daily_batch_utc_0000"
    anchor_block_heights: list[int] = Field(default_factory=list)
    anchor_state: str = "LOCAL_UNANCHORED"
```

### 4.3 Certificate Builder

**Same file:** `backend/investigation/certificate.py`

```python
class InvestigationCertificateBuilder:
    def build(
        self,
        envelope: EvidenceEnvelope,
        claim_graph: ClaimGraph,
        counter_signal_feed: InvestigationCounterSignalFeed,
        commitment_monitor: CommitmentMonitor,
        signal_scanner_domains: list[DomainFilter],
        stop_condition: StopCondition,
        stop_condition_trigger: str,
        market_summary: dict,
        osint_source_manifest: list[dict],
        base_certificate_fields: dict,
    ) -> InvestigationCertificate:
        """Assembles certificate from all toolset artefacts."""
```

**Routing logic (evaluated in order, first match wins):**
1. `commitment_monitor.has_material_drift()` → `REVIEW_REQUIRED`, `"drift_event_material"`
2. Any counter-signal with `material=True` → `REVIEW_REQUIRED`, `"counter_signal_material"`
3. All evidence items share a single provenance class → `REVIEW_REQUIRED`, `"single_provenance_class"`
4. `anchor_state != "ANCHORED"` → `REVIEW_REQUIRED`, `"anchoring_pending"`
5. Otherwise → `ALLOWED`

### 4.4 Stop Condition Evaluator

**New file:** `backend/investigation/stop_conditions.py`

```python
class InvestigationStopConditionEvaluator:
    def evaluate(
        self,
        stop_condition: StopCondition,
        stop_config: dict,
        claim_graph: ClaimGraph,
        evidence_envelope: EvidenceEnvelope,
        time_remaining: float,
    ) -> tuple[bool, str]:
        """Returns (ready, trigger_reason).

        OUTCOME_RESOLUTION: ready when time_remaining <= 0
        EVIDENCE_THRESHOLD: ready when claim graph meets committed threshold
            stop_config keys: min_supported_claims (int), min_corroboration_score (float)
        SPONSOR_DEFINED: ready when current time >= committed milestone
            stop_config keys: milestone_timestamp (ISO 8601 string)
        """
```

Reads `stop_config` keys only — never accepts runtime overrides.

### 4.5 Toolset Orchestrator

**New file:** `backend/investigation/toolset.py`

```python
class InvestigationConfig(BaseModel):
    domain_filters: list[DomainFilter] = Field(default_factory=list)
    stop_condition: StopCondition = StopCondition.OUTCOME_RESOLUTION
    stop_config: dict = Field(default_factory=dict)


class InvestigationToolset:
    def __init__(self, config: InvestigationConfig) -> None:
        self.envelope = EvidenceEnvelope()
        self.claim_graph = ClaimGraph()
        self.counter_signals = InvestigationCounterSignalFeed()
        self.commitment_monitor = CommitmentMonitor()
        self.signal_scanner = SignalScanner(config.domain_filters)
        self.entity_resolver = EntityResolver()
        self._config = config

    def submit_evidence(self, content: bytes, provenance_class: ProvenanceClass,
                        content_type: str, source_description: str,
                        references: list[str] | None = None) -> EvidenceItem: ...

    def register_claim(self, claim_text: str, claim_type: ClaimType,
                       evidence_refs: list[str]) -> ClaimNode: ...

    def log_counter_signal(self, **kwargs) -> InvestigationCounterSignal: ...
    def log_drift(self, **kwargs) -> DriftEvent: ...
    def run_scan(self, subject: str) -> DeltaBrief: ...
    def resolve_entity(self, query: EntityQuery) -> EntityProfile: ...

    def build_certificate(self, market_summary: dict,
                          osint_source_manifest: list[dict],
                          base_certificate_fields: dict,
                          stop_condition_trigger: str) -> InvestigationCertificate: ...
```

### 4.6 Deterministic Artefact Writers

**New file:** `backend/investigation/artifacts.py`

```python
def write_artifact(name: str, data: dict | list) -> tuple[str, str]:
    """Write deterministic JSON artefact. Returns (json_string, sha256_hash)."""
    from theatre.engine.canonical_json import canonical_json
    json_str = canonical_json(data)
    content_hash = hashlib.sha256(json_str.encode()).hexdigest()
    return json_str, content_hash
```

Artefact names: `deltabrief.json`, `scanner_manifest.json`, `entity_profile.json`, `evidence_manifest.json`, `corroboration_results.json`, `counter_signals.json`, `claim_graph.json`, `drift_events.json`, `market_summary.json`.

All use `canonical_json()` — sorted keys, no whitespace, UTF-8. Hash preimages match certificate fields.

---

## 5. Test Strategy

67+ new tests across 12 test files. All mock-only — no live HTTP calls.

| Test File | Tests | Coverage |
|-----------|-------|----------|
| test_evidence_envelope.py | 8 | Submit, append-only, redaction, hash determinism |
| test_claim_graph.py | 9 | Add claim, status update, Merkle root (1/2/3/odd claims) |
| test_counter_signals.py | 6 | Log, summary, class 10/11 event-driven rule |
| test_commitment_monitor.py | 5 | Log drift, material detection |
| test_signal_scanner.py | 5 | Domain filter mapping, DeltaBrief hash, manifest |
| test_entity_resolver.py | 4 | Resolve, hash determinism, provenance, unknown entity |
| test_corroboration_checker.py | 5 | Independence invariant, PRIVATE_LEAK rule |
| test_certificate.py | 8 | Build, all fields, routing logic (4 cases) |
| test_stop_conditions.py | 5 | 3 condition types, time/threshold/milestone |
| test_stop_condition_commitment.py | 4 | Persist, hash inclusion, immutability, committed-only |
| test_artifacts.py | 5 | Determinism, manifest format, hash parity |
| test_toolset_e2e.py | 3 | Full lifecycle, drift event, early resolution |

**Gate rule:** ≥942 passed (baseline), zero new failures, 67+ new tests pass. Post-014c expected: ≥1009.

---

## 6. Shared Schema Changes

### 6.1 Theatre Schema

`backend/schemas/theatre.py` — add to `TheatreCreate`:
```python
stop_condition: str | None = None
stop_config: dict | None = None
```

Both optional with `None` defaults. Non-INVESTIGATIVE inquiry classes ignore them.

### 6.2 Theatre Database Model

`backend/database/models.py` — add to Theatre:
```python
stop_condition = Column(String(30), nullable=True)
stop_config = Column(JSON, nullable=True)
```

### 6.3 Alembic Migration

New migration file adding two nullable columns to the `theatres` table. No data migration needed.

### 6.4 Theatre Routes

`backend/api/theatre_routes.py`:
- `create_theatre`: store stop fields from request body
- `commit_theatre`: include stop fields in commitment hash computation
- Post-COMMITTED: reject any mutation attempt on stop fields (400 response)

### 6.5 Backward Compatibility

All changes are additive with nullable/optional defaults. Existing theatres without stop conditions continue to work unchanged. Non-INVESTIGATIVE inquiry classes are unaffected.
