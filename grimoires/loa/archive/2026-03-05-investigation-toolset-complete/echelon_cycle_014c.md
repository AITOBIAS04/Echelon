# Cycle-014c: Investigation Toolset Implementation

**Date:** 4 March 2026
**Depends on:** Cycle-014 (bounded inquiry lifecycle), Cycle-013 (agent runtime), Cycle-010a (LMSR)
**Sprints:** 3
**Scope:** Pydantic models, services, Merkle hashing, certificate extension, and E2E tests for the 8-tool investigation toolset
**Design input:** `echelon core arch/implement/Echelon_Investigation_Toolset_Design_Note_v1.md` (v1.3.0)

---

## Why This Cycle Exists

Cycle-014 built the bounded inquiry lifecycle with five inquiry classes, but the INVESTIGATIVE class has no tooling beyond what other classes share (evidence rules, resolution triggers, agent behaviour profiles). The design note defines 8 tools that make Investigation-class inquiries actually useful: Signal Scanner, Entity Resolver, Evidence Envelope, Corroboration Checker, Counter-Signal Feed, Claim Graph, Commitment Monitor, and LMSR Investigation Market.

This cycle builds the **runtime models, services, and hashing infrastructure** for those tools. It does NOT build UI or deploy on-chain anchoring contracts. Default execution remains mock/in-memory, but interfaces must support optional live backends where collectors already exist.

---

## Current State

### What EXISTS (no new work needed)

- **LMSR Market Engine** (Cycle-010a) — investigation markets use the existing engine
- **Bounded inquiry lifecycle** (Cycle-014) — INVESTIGATIVE class already has distinct evidence rules (`_validate_investigative` in `evidence_service.py`), resolution triggers (`corroboration_met AND evidence_threshold OR time_window_closed`), and 6 archetype × inquiry behaviour profiles
- **Corroboration Engine** (`backend/osint/engine/corroboration.py`) — independence-weighted dedup by `independence_upstream_id`, distinct group counting, `CorroborationResult` with audit trail
- **Counter-Signal Evaluator** (`backend/osint/engine/counter_signal.py`) — 11 classes scaffolded, `CounterSignalOutcome` enum, `CounterSignalResult` dataclass, all return UNAVAILABLE
- **Evidence models** (`backend/osint/models/evidence.py`) — `EvidenceBundle` (re-export), `HTTPTranscriptReceipt`, `CollectionResult`
- **Certificate pipeline** (`backend/services/certificate_pipeline.py`) — `CalibrationCertificate` dataclass, `CertificatePipeline.generate()`
- **Theatre state machine** (`theatre/engine/state_machine.py`) — DRAFT → COMMITTED → ACTIVE → SETTLING → RESOLVED → ARCHIVED
- **Resolution engine** (`backend/market/resolution.py`) — `ResolutionTrigger` enum includes `EVIDENCE_THRESHOLD_MET`, `CLAIM_VERDICT`, `TIME_WINDOW_CLOSED`
- **Convergence detector** (`backend/osint/engine/convergence.py`) — geographic cell binning, multi-domain co-location alerts (in-process logging only)

### What's PARTIAL (extend, don't replace)

- **Counter-signal classes** — existing 11 classes are pipeline-level (weather, infrastructure, etc). The design note defines 11 investigation-level classes (official denial, filing contradiction, etc). These are a different taxonomy — investigation counter-signals, not OSINT pipeline counter-signals. Build a new `InvestigationCounterSignalClass` enum alongside the existing one.
- **Certificate schema** — `CalibrationCertificate` has `evidence_bundle_hash`, `composite_score`, `corroboration_status`, `counter_signal_results`, `verification_tier`. Missing: `claim_graph_root_hash`, `claim_count`, `claim_status_summary`, `independence_summary`, `counter_signal_detail`, `drift_events`, `redaction_events`, `stop_condition_used`, `stop_condition_trigger`, `evidence_provenance_summary`, `signal_scanner_domains`, `market_summary`, `anchor_frequency`, `anchor_block_heights`.
- **Resolution triggers** — `EVIDENCE_THRESHOLD_MET` exists but the 3 stop conditions (outcome, evidence threshold, sponsor-defined) need wiring as committed parameters.
- **Corroboration checker contract** — `CorroborationEngine` exists, but there is no investigation-specific claim checker enforcing the non-negotiable rule: no claim may be `SUPPORTED` without >=2 independent upstream groups.

### What's NEW (build from scratch)

1. **Evidence Envelope** — submission schema, provenance class enum, immutability enforcement, redaction log, Merkle-based envelope hash
2. **Claim Graph** — claim nodes (FACT/CAUSAL/ATTRIBUTION), evidence linkage, status tracking (SUPPORTED/PARTIALLY_SUPPORTED/UNCONFIRMED/CONTRADICTED), Merkle root hashing per spec
3. **Signal Scanner** — domain filter schema, DeltaBrief output model, scanner manifest, committed scope rules
4. **Entity Resolver** — query schema, multi-source entity profile, provenance metadata per source
5. **Corroboration Checker** — claim-centric corroboration service with independence-gate enforcement and deterministic outputs
6. **Commitment Monitor** — drift type enum, DriftEvent model, impact assessment, Paradox Engine integration point
7. **Investigation Certificate Extension** — extends `CalibrationCertificate` with all investigation-specific fields from design note Section 6

---

## Sprint 1: Evidence Envelope + Claim Graph (Core Data Layer)

These are the two foundational models — everything else depends on them.

### Task 1.1: Provenance Class Enum + Evidence Item Model

**New file:** `backend/investigation/models.py`

```python
class ProvenanceClass(str, Enum):
    PUBLIC_PRIMARY = "public_primary"
    PUBLIC_SECONDARY = "public_secondary"
    PRIVATE_LEAK = "private_leak"
    ANALYST_DERIVED = "analyst_derived"
    THIRD_PARTY_TOOL_OUTPUT = "third_party_tool_output"

class EvidenceItem(BaseModel):
    model_config = {"frozen": True}
    evidence_id: str          # Sequential "E001", "E002", ...
    content_hash: str         # SHA-256 of raw content bytes
    provenance_class: ProvenanceClass
    submitted_at: datetime
    content_type: str         # "application/pdf", "application/json", "image/png", etc.
    source_description: str   # Human-readable source label
    references: list[str] = Field(default_factory=list)  # Other evidence_ids this references
```

**Policy constraint (enforce in service, not model):** `settlement_eligible` claims cannot resolve on `PRIVATE_LEAK` alone — requires `PUBLIC_PRIMARY` or `PUBLIC_SECONDARY` corroboration from a different `independence_upstream_id`.

### Task 1.2: Evidence Envelope Service

**New file:** `backend/investigation/evidence_envelope.py`

```python
class RedactionEvent(BaseModel):
    model_config = {"frozen": True}
    redaction_id: str
    evidence_id: str
    reason_class: str   # "accidental_secret", "defamatory", "illegal", "doxxing", "copyright"
    redacted_at: datetime

class EvidenceEnvelope:
    """Append-only evidence container with Merkle-based integrity."""

    def submit(self, content: bytes, provenance_class: ProvenanceClass,
               content_type: str, source_description: str,
               references: list[str] | None = None) -> EvidenceItem
    def redact(self, evidence_id: str, reason_class: str) -> RedactionEvent
    def get_item(self, evidence_id: str) -> EvidenceItem | None
    def get_manifest(self) -> dict  # evidence_manifest.json equivalent
    def compute_envelope_hash(self) -> str  # SHA-256 of all item hashes
    @property
    def items(self) -> list[EvidenceItem]
    @property
    def redactions(self) -> list[RedactionEvent]
    @property
    def provenance_summary(self) -> dict[str, int]  # {PUBLIC_PRIMARY: N, ...}
```

**Immutability rule:** `submit()` is append-only. No `delete()` method. `redact()` adds a redaction event but does NOT remove the hash from the chain. Envelope hash computation includes all items including redacted ones.

### Task 1.3: Claim Graph Model + Merkle Hashing

**New file:** `backend/investigation/claim_graph.py`

```python
class ClaimType(str, Enum):
    FACT = "fact"               # "X resigned on Y date"
    CAUSAL = "causal"           # "X caused Y"
    ATTRIBUTION = "attribution"  # "X did Y"

class ClaimStatus(str, Enum):
    SUPPORTED = "supported"
    PARTIALLY_SUPPORTED = "partially_supported"
    UNCONFIRMED = "unconfirmed"
    CONTRADICTED = "contradicted"

class ClaimNode(BaseModel):
    model_config = {"frozen": True}
    claim_id: str              # "C001", "C002", ...
    claim_text: str
    claim_type: ClaimType
    evidence_refs: list[str]   # Evidence Envelope item IDs
    osint_checks: list[CorroborationCheck]  # Per-source results
    counter_signals: list[str]  # Counter-signal IDs
    status: ClaimStatus
    confidence: float = Field(ge=0.0, le=1.0)
    independence_groups: list[str]  # Upstream group IDs

class ClaimGraph:
    """Structured claim-evidence-source mapping with Merkle root."""

    def add_claim(self, ...) -> ClaimNode
    def update_claim_status(self, claim_id: str, status: ClaimStatus,
                            confidence: float, independence_groups: list[str]) -> ClaimNode
    def link_counter_signal(self, claim_id: str, counter_signal_id: str) -> None
    def compute_root_hash(self) -> str  # Merkle root per design note §3.7
    def get_status_summary(self) -> dict[str, int]  # {SUPPORTED: N, ...}
    @property
    def claims(self) -> list[ClaimNode]
```

**Merkle hashing spec (from design note §3.7, implement exactly):**
1. Each claim → canonical JSON (keys sorted, no whitespace, UTF-8)
2. Each leaf hash = SHA-256(canonical_json(claim))
3. Claims ordered by `claim_id` (lexicographic)
4. Merkle tree: SHA-256 pairwise hashing, odd leaf duplicated

Use `theatre.engine.canonical_json.canonical_json()` which already exists.

### Task 1.4: Evidence Envelope Tests

**New file:** `backend/investigation/tests/test_evidence_envelope.py`

1. `test_submit_and_retrieve` — submit item, retrieve by ID, verify hash
2. `test_append_only` — submit 3 items, verify sequential IDs
3. `test_provenance_summary` — submit mixed provenance classes, verify counts
4. `test_envelope_hash_deterministic` — same content in same order → same hash
5. `test_envelope_hash_changes_on_new_item` — hash changes after new submission
6. `test_redaction_preserves_hash` — redacting item doesn't change envelope hash
7. `test_redaction_logged` — redaction event recorded with reason and timestamp
8. `test_manifest_format` — verify manifest matches expected JSON structure

### Task 1.5: Claim Graph Tests

**New file:** `backend/investigation/tests/test_claim_graph.py`

1. `test_add_claim` — add claim, verify fields
2. `test_status_update` — update from UNCONFIRMED to SUPPORTED
3. `test_merkle_root_deterministic` — same claims → same root hash
4. `test_merkle_root_single_claim` — single claim: root = hash(claim)
5. `test_merkle_root_two_claims` — two claims: root = hash(hash(c1) + hash(c2))
6. `test_merkle_root_odd_count` — 3 claims: last leaf duplicated
7. `test_merkle_root_uses_canonical_json` — verify canonical_json is used
8. `test_status_summary` — verify {SUPPORTED: N, ...} counts
9. `test_link_counter_signal` — link CS to claim, verify it appears in claim's list

---

## Sprint 2: Investigation Counter-Signals + Commitment Monitor + Signal Scanner + Entity Resolver

### Task 2.1: Investigation Counter-Signal Classes

**New file:** `backend/investigation/counter_signals.py`

The 11 investigation-specific counter-signal classes from design note §3.5. This is a **separate taxonomy** from the existing pipeline counter-signals in `backend/osint/engine/counter_signal.py`.

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
    MARKET_DIVERGENCE = "market_divergence"            # Detected by Paradox Engine
    WITNESS_SOURCE_RECANTATION = "witness_source_recantation"  # Human-submitted

class InvestigationCounterSignal(BaseModel):
    model_config = {"frozen": True}
    counter_signal_id: str
    signal_class: InvestigationCounterSignalClass
    detected_at: datetime
    evidence_ref: str | None       # Evidence Envelope item ID
    material: bool
    resolution_impact: str         # Human-readable impact assessment
    detection_method: str          # "automated_osint" | "paradox_engine" | "human_submitted"

class InvestigationCounterSignalFeed:
    """Tracks investigation-level counter-signals."""

    def log_counter_signal(self, ...) -> InvestigationCounterSignal
    def get_summary(self) -> dict   # {checked: N, gaps: N, material_contradictions: N}
    def get_detail(self) -> list[dict]  # Per-signal detail for certificate
    @property
    def signals(self) -> list[InvestigationCounterSignal]
```

**Key rule from design note:** Classes 10 (market divergence) and 11 (witness recantation) only count toward `checked` when an explicit event is logged. They do NOT passively increment by virtue of systems running.

### Task 2.2: Commitment Monitor

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
    evidence_ref: str | None   # Evidence Envelope item proving the change
    impact_assessment: DriftImpact

class CommitmentMonitor:
    """Tracks definition drift in the investigation target."""

    def log_drift(self, ...) -> DriftEvent
    def has_material_drift(self) -> bool
    @property
    def events(self) -> list[DriftEvent]
```

**Routing impact:** If `has_material_drift()` is True, certificate gets `routing_hint: REVIEW_REQUIRED` with `review_reason_code: "drift_event_material"`.

### Task 2.3: Signal Scanner Model + Domain Filter Schema

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

class DeltaBrief(BaseModel):
    """Deterministic, hashable novelty detection artefact."""
    model_config = {"frozen": True}
    brief_id: str
    domain_filters: list[DomainFilter]
    generated_at: datetime
    source_queries: list[SourceQuery]   # Per-source query record
    anomalies: list[Anomaly]            # Detected anomalies
    content_hash: str                   # SHA-256 of canonical JSON serialisation

class SignalScanner:
    """Surfaces anomalies from OSINT sources filtered by domain."""

    def __init__(self, domain_filters: list[DomainFilter]) -> None
    def scan(self, subject: str, sources: list[...]) -> DeltaBrief
    @property
    def active_source_groups(self) -> list[str]
```

**Access-tier policy (must enforce):**
- Default allowed access tier is `A` only.
- Domain filters resolving to `B`/`C` sources are not silently included; they must be recorded as skipped with reason.
- Scanner manifest must include `requested_filters`, `resolved_source_groups`, `skipped_source_groups`, and `access_tier_policy`.

**Note:** `scan()` implementation in this cycle uses mock/stub sources by default. Cycle-015 is complete (WM + CH), so live adapters are optional and must preserve identical output schema.

### Task 2.4: Entity Resolver Model

**New file:** `backend/investigation/entity_resolver.py`

```python
class EntityProfile(BaseModel):
    """Structured entity profile with provenance metadata per source."""
    model_config = {"frozen": True}
    entity_id: str
    entity_name: str
    jurisdiction: str
    registration_number: str | None
    incorporation_date: str | None
    registered_address: str | None
    directors: list[dict] = Field(default_factory=list)
    filing_history_summary: list[dict] = Field(default_factory=list)
    gazette_notices: list[dict] = Field(default_factory=list)
    regulatory_entries: list[dict] = Field(default_factory=list)
    source_queries: list[SourceQueryRecord] = Field(default_factory=list)
    profile_hash: str          # SHA-256 of canonical JSON

class EntityResolver:
    """Multi-source entity lookup with provenance tracking."""

    def resolve(self, query: EntityQuery) -> EntityProfile
```

**This cycle:** Only Companies House + London Gazette backends stubbed. Additional jurisdictions (SEC EDGAR, ASIC, etc.) added when those collectors exist.

### Task 2.5: Sprint 2 Tests

**New files:**
- `backend/investigation/tests/test_counter_signals.py` (6 tests)
- `backend/investigation/tests/test_commitment_monitor.py` (5 tests)
- `backend/investigation/tests/test_signal_scanner.py` (5 tests)
- `backend/investigation/tests/test_entity_resolver.py` (4 tests)
- `backend/investigation/tests/test_corroboration_checker.py` (5 tests)

Counter-signal tests:
1. `test_log_counter_signal` — log and retrieve
2. `test_summary_counts` — checked/gaps/material counts correct
3. `test_market_divergence_only_counted_when_logged` — class 10 doesn't auto-increment
4. `test_witness_recantation_only_counted_when_logged` — class 11 doesn't auto-increment
5. `test_detail_format` — per-signal detail matches certificate schema
6. `test_material_vs_non_material` — material flag correctly tracked

Commitment monitor tests:
1. `test_log_drift_event` — log and retrieve
2. `test_has_material_drift_false` — no material events → False
3. `test_has_material_drift_true` — material event → True
4. `test_drift_event_fields` — all fields populated correctly
5. `test_multiple_drift_events` — accumulates correctly

Signal scanner tests:
1. `test_domain_filter_to_source_groups` — mapping resolves correctly
2. `test_combined_filters` — multiple filters merge source groups
3. `test_deltabrief_hash_deterministic` — same input → same hash
4. `test_scan_with_mock_sources` — scan produces DeltaBrief with anomalies
5. `test_scanner_manifest_format` — manifest JSON structure correct

Entity resolver tests:
1. `test_resolve_companies_house` — mock CH response → valid EntityProfile
2. `test_profile_hash_deterministic` — same data → same hash
3. `test_source_query_record` — provenance metadata per source correct
4. `test_unknown_entity` — graceful failure for unknown entity

Corroboration checker tests:
1. `test_supported_requires_two_independent_upstreams` — one upstream cannot become SUPPORTED
2. `test_supported_with_two_independent_upstreams` — two distinct upstream groups permits SUPPORTED
3. `test_private_leak_only_remains_unconfirmed` — PRIVATE_LEAK-only evidence cannot settle claim
4. `test_partial_status_with_single_upstream` — single corroborator yields PARTIALLY_SUPPORTED
5. `test_checker_output_deterministic` — same claim inputs produce same output hash

### Task 2.6: Investigation Corroboration Checker

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
    """Claim-centric corroboration with independence enforcement."""

    def evaluate_claim(self, claim: ClaimNode, collection_results: list[CollectionResult]) -> list[CorroborationCheck]
    def derive_claim_status(self, checks: list[CorroborationCheck]) -> ClaimStatus
```

**Hard invariant (non-negotiable):** `ClaimStatus.SUPPORTED` requires >=2 distinct `independence_upstream_id` groups. No override, no admin bypass.

---

## Sprint 3: Investigation Certificate Extension + Stop Conditions + E2E

### Task 3.0: Committed Stop Condition Contract (Schema + Persistence + Hashing)

**Files:**
- `backend/schemas/theatre.py`
- `backend/database/models.py` + Alembic migration
- `backend/api/theatre_routes.py`
- Commitment hashing path (theatre commit payload)

Add committed stop-condition fields at theatre creation/commit time:
- `stop_condition`: `outcome_resolution | evidence_threshold | sponsor_defined`
- `stop_config`: committed parameter payload (thresholds, milestone timestamp, etc)

**Contract rule:** Once theatre is COMMITTED, `stop_condition` and `stop_config` are immutable. Any mutation attempt must fail with 400/422 and leave commitment hash unchanged.

### Task 3.1: Investigation Certificate Extension

**File:** `backend/investigation/certificate.py`

Extend the existing `CalibrationCertificate` (or wrap it) with all investigation-specific fields from design note Section 6:

```python
class StopCondition(str, Enum):
    OUTCOME_RESOLUTION = "outcome_resolution"
    EVIDENCE_THRESHOLD = "evidence_threshold"
    SPONSOR_DEFINED = "sponsor_defined"

class InvestigationCertificate(BaseModel):
    """Investigation-class certificate extending CalibrationCertificate."""

    # Base fields (from existing CalibrationCertificate)
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

    # Investigation-specific fields
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
    routing_hint: str = "ALLOWED"
    review_reason_code: str | None = None

    # Anchoring metadata (contract deployment remains out-of-scope)
    anchor_frequency: str = "daily_batch_utc_0000"
    anchor_block_heights: list[int] = Field(default_factory=list)
    anchor_state: str = "LOCAL_UNANCHORED"  # LOCAL_UNANCHORED | ANCHORED
```

### Task 3.2: Investigation Certificate Builder

**File:** `backend/investigation/certificate.py` (same file)

```python
class InvestigationCertificateBuilder:
    """Assembles InvestigationCertificate from toolset artefacts."""

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
        base_certificate_fields: dict,  # theatre_id, commitment_hash, etc.
    ) -> InvestigationCertificate
```

**Routing logic:**
- If `commitment_monitor.has_material_drift()` → `routing_hint = "REVIEW_REQUIRED"`, `review_reason_code = "drift_event_material"`
- If any counter-signal is material → `routing_hint = "REVIEW_REQUIRED"`, `review_reason_code = "counter_signal_material"`
- If all evidence is single provenance class → `routing_hint = "REVIEW_REQUIRED"`, `review_reason_code = "single_provenance_class"`
- If `anchor_state != "ANCHORED"` → `routing_hint = "REVIEW_REQUIRED"`, `review_reason_code = "anchoring_pending"`
- Otherwise → `routing_hint = "ALLOWED"`

### Task 3.3: Stop Condition Wiring

**File:** `backend/investigation/stop_conditions.py`

Wire the three stop conditions from design note §3.9 into the existing `ResolutionEngine.check_resolution_ready()` for INVESTIGATIVE class, reading `stop_condition` and `stop_config` from committed theatre parameters only:

```python
class InvestigationStopConditionEvaluator:
    """Evaluates investigation-specific stop conditions."""

    def evaluate(
        self,
        stop_condition: StopCondition,
        stop_config: dict,          # Committed parameters
        claim_graph: ClaimGraph,
        evidence_envelope: EvidenceEnvelope,
        time_remaining: float,      # Seconds until window closes
    ) -> tuple[bool, str]           # (ready, trigger_reason)
```

- `OUTCOME_RESOLUTION`: ready when `time_remaining <= 0` (time window expired)
- `EVIDENCE_THRESHOLD`: ready when claim graph meets committed threshold (e.g. N claims SUPPORTED, or corroboration score ≥ X)
- `SPONSOR_DEFINED`: ready when committed milestone date is reached

**Immutability check:** evaluator input must be commitment-derived only; do not accept mutable runtime overrides for `stop_condition`/`stop_config`.

### Task 3.4: Investigation Toolset Integration Service

**New file:** `backend/investigation/toolset.py`

Orchestrator that wires all 8 tools together:

```python
class InvestigationToolset:
    """Orchestrates all investigation tools for a single inquiry."""

    def __init__(self, config: InvestigationConfig) -> None:
        self.envelope = EvidenceEnvelope()
        self.claim_graph = ClaimGraph()
        self.counter_signals = InvestigationCounterSignalFeed()
        self.commitment_monitor = CommitmentMonitor()
        self.signal_scanner = SignalScanner(config.domain_filters)
        self.entity_resolver = EntityResolver()

    def submit_evidence(self, ...) -> EvidenceItem
    def register_claim(self, ...) -> ClaimNode
    def log_counter_signal(self, ...) -> InvestigationCounterSignal
    def log_drift(self, ...) -> DriftEvent
    def run_scan(self, subject: str) -> DeltaBrief
    def resolve_entity(self, query: EntityQuery) -> EntityProfile
    def build_certificate(self, ...) -> InvestigationCertificate
```

### Task 3.5: Deterministic Artefact Contract

**New file:** `backend/investigation/artifacts.py`

Provide deterministic JSON artefact writers for tool outputs:
- `deltabrief.json`
- `scanner_manifest.json`
- `entity_profile.json`
- `evidence_manifest.json`
- `corroboration_results.json`
- `counter_signals.json`
- `claim_graph.json`
- `drift_events.json`
- `market_summary.json`

Rules:
- UTF-8 JSON, sorted keys, stable ordering.
- Hash preimages must match certificate root/hash fields.
- File-level hashing must be reproducible across runs.

### Task 3.6: Sprint 3 Tests

**New files:**
- `backend/investigation/tests/test_certificate.py` (8 tests)
- `backend/investigation/tests/test_stop_conditions.py` (5 tests)
- `backend/investigation/tests/test_stop_condition_commitment.py` (4 tests)
- `backend/investigation/tests/test_artifacts.py` (5 tests)
- `backend/investigation/tests/test_toolset_e2e.py` (3 tests)

Certificate tests:
1. `test_build_minimal_certificate` — envelope + claim graph → valid certificate
2. `test_certificate_includes_all_fields` — all 30+ fields present
3. `test_routing_hint_material_drift` — material drift → REVIEW_REQUIRED
4. `test_routing_hint_material_counter_signal` — material CS → REVIEW_REQUIRED
5. `test_routing_hint_single_provenance` — all PUBLIC_PRIMARY → REVIEW_REQUIRED
6. `test_routing_hint_allowed` — normal case → ALLOWED
7. `test_certificate_hash_deterministic` — same inputs → same hashes
8. `test_provenance_summary_in_certificate` — counts match envelope

Stop condition tests:
1. `test_outcome_resolution_time_expired` — ready when time runs out
2. `test_outcome_resolution_time_remaining` — not ready while time left
3. `test_evidence_threshold_met` — N SUPPORTED claims → ready
4. `test_evidence_threshold_not_met` — insufficient claims → not ready
5. `test_sponsor_defined_milestone` — milestone date reached → ready

Stop condition commitment tests:
1. `test_stop_condition_persisted_on_create` — stored on theatre at creation
2. `test_stop_config_included_in_commitment_hash` — hash changes when stop config changes pre-commit
3. `test_stop_condition_immutable_post_commit` — mutation rejected after COMMITTED
4. `test_resolution_uses_committed_stop_config_only` — runtime override ignored/rejected

Artefact tests:
1. `test_artifact_writer_deterministic` — same inputs produce byte-identical files
2. `test_manifest_contains_access_tier_policy` — scanner manifest includes requested/resolved/skipped groups
3. `test_claim_graph_json_matches_root_hash` — root hash recomputes from artefact bytes
4. `test_evidence_manifest_hash_matches_certificate_field` — bundle hash matches
5. `test_counter_signal_artifact_matches_certificate_detail` — detail parity enforced

E2E tests (full investigation lifecycle):
1. `test_e2e_investigation_lifecycle` — create toolset → submit evidence → register claims → check corroboration → log counter-signals → resolve → build certificate → verify all hashes chain correctly
2. `test_e2e_with_drift_event` — same as above but with material drift → REVIEW_REQUIRED
3. `test_e2e_evidence_threshold_resolution` — investigation resolves early via evidence threshold stop condition

---

## Gate Rule

≥942 passed (current baseline), 15 skipped, 13 pre-existing collection errors (same node IDs). Zero new failures. All new investigation toolset tests pass. Post-014c expected: ≥1009 passed (67+ new tests).

---

## What This Unlocks

- **Investigation-class inquiries become functional** — not just a lifecycle variant but a full evidence-receipting, claim-structuring, counter-signal-monitoring investigation platform
- **Certificate consumers get actionable artefacts** — Claim Graph root hash, provenance summary, independence groups, counter-signal detail, drift events all in the certificate
- **Foundation for 016 (Results Surface)** — the toolset models define the data that the UI will display
- **Foundation for live investigations** — with Cycle-015 complete, Signal Scanner and Entity Resolver can use optional live adapters without changing the interface

---

## Out of Scope

- Base contract deployment and final on-chain anchoring enforcement (requires Solidity contracts, Base Sepolia/Mainnet operations)
- Paid-tier (`B`/`C`) source activation in Signal Scanner without explicit access approval
- Full live-query coverage across all domain filters (beyond currently available collectors)
- Domain filter UI (requires Cycle-016 Results Surface)
- RLMF export from investigation markets (existing RLMF export applies)
- Blockchain forensics, leaked data sourcing, KYC/AML (design note §7 exclusions)
- Entity Resolver jurisdictions beyond Companies House + London Gazette stubs
