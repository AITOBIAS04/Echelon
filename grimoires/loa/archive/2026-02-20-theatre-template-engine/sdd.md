# SDD: Theatre Template Engine

> Cycle: cycle-031 | PRD: `grimoires/loa/prd.md`
> Status: Draft | Date: 2026-02-20
> UK British English throughout.

---

## 1. Executive Summary

This document describes the architecture for the Theatre Template Engine — the lifecycle container for all Echelon verification activity. The Theatre wraps the existing `echelon-verify` pipeline (Cycle-027) in a state machine with an immutable commitment protocol, structured criteria, evidence bundles, and verification tier assignment.

**Two execution paths share one architecture:**

- **Replay Theatres** (Product): full implementation — commit → invoke construct → score → certificate
- **Market Theatres** (Geopolitical): schema validation only this cycle — execution deferred to Cycle-030

The engine is implemented as a new `theatre` package alongside the existing `echelon_verify` package, with new SQLAlchemy models, FastAPI routes, and a bridge service following established backend patterns.

---

## 2. System Architecture

### 2.1 High-Level Component Diagram

```
┌──────────────────────────────────────────────────────────────┐
│                         FastAPI Backend                       │
│  ┌──────────────────┐  ┌──────────────────────────────────┐  │
│  │ verification/     │  │ theatre/                         │  │
│  │   routes (exist)  │  │   routes (NEW)                   │  │
│  │   schemas (exist) │  │   schemas (NEW)                  │  │
│  │   bridge (exist)  │  │   bridge (NEW)                   │  │
│  └──────────────────┘  └──────────┬───────────────────────┘  │
│                                   │                           │
│  ┌────────────────────────────────┴───────────────────────┐  │
│  │              SQLAlchemy Models (NEW tables)             │  │
│  │  Theatre · TheatreTemplate · TheatreCertificate ·      │  │
│  │  TheatreEpisodeScore · TheatreAuditEvent               │  │
│  └────────────────────────────────────────────────────────┘  │
└──────────────────────────────────┬────────────────────────────┘
                                   │
┌──────────────────────────────────┴────────────────────────────┐
│                    Theatre Engine (NEW package)                │
│  ┌────────────┐ ┌──────────────┐ ┌───────────────────────┐   │
│  │ Theatre     │ │ Commitment   │ │ ReplayEngine          │   │
│  │ StateMachine│ │ Protocol     │ │ (orchestrates replay) │   │
│  └─────┬──────┘ └──────┬───────┘ └───────────┬───────────┘   │
│        │               │                     │                │
│  ┌─────┴──────┐ ┌──────┴───────┐ ┌───────────┴───────────┐   │
│  │ Resolution │ │ canonical    │ │ EvidenceBundle         │   │
│  │ StateMachine│ │ _json()     │ │ Builder                │   │
│  └────────────┘ └──────────────┘ └───────────────────────┘   │
│                                                               │
│  ┌────────────┐ ┌──────────────┐ ┌───────────────────────┐   │
│  │ Tier       │ │ Constraint   │ │ CalibrationCertificate │   │
│  │ Assigner   │ │ YieldingGate │ │ (Theatre-aware)        │   │
│  └────────────┘ └──────────────┘ └───────────────────────┘   │
│                                                               │
│  ┌────────────────────────────────────────────────────────┐   │
│  │         echelon-verify (EXISTING — reused)             │   │
│  │  OracleAdapter · ScoringProvider · Storage             │   │
│  └────────────────────────────────────────────────────────┘   │
└───────────────────────────────────────────────────────────────┘
```

### 2.2 Reuse Strategy

| Existing Component | Path | Strategy |
|--------------------|------|----------|
| `OracleAdapter` ABC | `verification/src/echelon_verify/oracle/` | **Reuse** — wrap with Theatre-aware request/response envelope |
| `ScoringProvider` ABC | `verification/src/echelon_verify/scoring/base.py` | **Extend** — create `TheatreScoringProvider` that scores per `criteria_ids` |
| `Storage` utilities | `verification/src/echelon_verify/` | **Reuse** — JSONL/JSON persistence for evidence bundles |
| Verification routes | `backend/api/verification_routes.py` | **Don't touch** — new `/theatres` router |
| Verification models | `backend/database/models.py` | **Don't touch** — new Theatre-specific tables |
| Verification bridge | `backend/services/verification_bridge.py` | **Pattern reference** — same background task pattern |
| Verification schemas | `backend/schemas/verification.py` | **Pattern reference** — same Pydantic v2 patterns |

---

## 3. Technology Stack

| Layer | Technology | Justification |
|-------|-----------|---------------|
| Core engine | Python 3.11+, Pydantic v2 | Matches `echelon-verify` package |
| Backend API | FastAPI, async SQLAlchemy 2.0 | Matches existing backend |
| Database | PostgreSQL (via `asyncpg`) | Matches existing `Mapped[]` pattern |
| Schema validation | `jsonschema` | Validates templates against `echelon_theatre_schema_v2.json` |
| Hashing | `hashlib.sha256` | Standard library, deterministic |
| Canonical JSON | Custom `canonical_json()` utility | RFC 8785 compliance |
| Testing | `pytest`, `pytest-asyncio` | Matches existing test patterns |

---

## 4. Component Design

### 4.1 Theatre State Machine

**Module:** `theatre/engine/state_machine.py`

```python
class TheatreState(str, enum.Enum):
    DRAFT = "DRAFT"
    COMMITTED = "COMMITTED"
    ACTIVE = "ACTIVE"
    SETTLING = "SETTLING"
    RESOLVED = "RESOLVED"
    ARCHIVED = "ARCHIVED"

VALID_TRANSITIONS: dict[TheatreState, list[TheatreState]] = {
    TheatreState.DRAFT: [TheatreState.COMMITTED],
    TheatreState.COMMITTED: [TheatreState.ACTIVE],
    TheatreState.ACTIVE: [TheatreState.SETTLING],
    TheatreState.SETTLING: [TheatreState.RESOLVED],
    TheatreState.RESOLVED: [TheatreState.ARCHIVED],
    TheatreState.ARCHIVED: [],
}

class TheatreStateMachine:
    """Enforces irreversible Theatre lifecycle transitions."""

    def __init__(self, theatre_id: str, state: TheatreState):
        self._theatre_id = theatre_id
        self._state = state

    @property
    def state(self) -> TheatreState:
        return self._state

    def transition(self, target: TheatreState) -> TheatreState:
        """Advance to target state. Raises InvalidTransitionError if not allowed."""
        if target not in VALID_TRANSITIONS[self._state]:
            raise InvalidTransitionError(
                f"Cannot transition from {self._state} to {target}"
            )
        self._state = target
        return self._state

    def can_transition(self, target: TheatreState) -> bool:
        return target in VALID_TRANSITIONS[self._state]
```

**Invariant:** After `COMMITTED`, no field on the Theatre or its template may be modified. The state machine itself never mutates template data — it only advances the state enum.

### 4.2 Commitment Protocol

**Module:** `theatre/engine/commitment.py`

```python
class CommitmentProtocol:
    """Generates and verifies commitment hashes."""

    @staticmethod
    def compute_hash(
        template: dict,
        version_pins: dict,
        dataset_hashes: dict,
    ) -> str:
        """Compute SHA-256 over canonical JSON of the composite object.

        The composite object has exactly three keys: dataset_hashes, template,
        version_pins — sorted lexicographically by canonical_json().
        """
        composite = {
            "dataset_hashes": dataset_hashes,
            "template": template,
            "version_pins": version_pins,
        }
        canonical = canonical_json(composite)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    @staticmethod
    def verify_hash(
        commitment_hash: str,
        template: dict,
        version_pins: dict,
        dataset_hashes: dict,
    ) -> bool:
        """Recompute and compare. Returns True if match."""
        recomputed = CommitmentProtocol.compute_hash(
            template, version_pins, dataset_hashes
        )
        return recomputed == commitment_hash
```

**CommitmentReceipt** (Pydantic model):
```python
class CommitmentReceipt(BaseModel):
    theatre_id: str
    commitment_hash: str
    committed_at: datetime
    template_snapshot: dict       # full canonical template
    version_pins: dict
    dataset_hashes: dict
```

### 4.3 Canonical JSON Utility

**Module:** `theatre/engine/canonical_json.py`

```python
def canonical_json(obj: Any) -> str:
    """Produce RFC 8785-compliant canonical JSON.

    Rules:
    - Keys sorted lexicographically (Unicode code point order) at every level
    - No whitespace between tokens
    - Integers as-is, floats normalised (no trailing zeroes, no positive sign)
    - null included (not omitted)
    - Arrays preserve insertion order
    - Recursive sorting at every nesting level
    """
    normalised = _normalise_value(obj)
    return json.dumps(normalised, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False)


def _normalise_value(v: Any) -> Any:
    """Recursively normalise values for canonical representation."""
    if isinstance(v, dict):
        return {k: _normalise_value(val) for k, val in v.items()}
    if isinstance(v, list):
        return [_normalise_value(item) for item in v]
    if isinstance(v, float):
        return _normalise_float(v)
    return v


def _normalise_float(f: float) -> float | int:
    """Normalise floats: 1.0 → 1, 0.10 → 0.1, disallow NaN/Inf."""
    if math.isnan(f) or math.isinf(f):
        raise ValueError(f"canonical_json: NaN/Infinity not permitted: {f}")
    if f == int(f) and not (-0.0 is f):  # 1.0 → 1, but preserve -0.0 handling
        return int(f)
    return f
```

**Test strategy:** round-trip determinism tests across inputs — nested dicts, floats, nulls, Unicode strings, empty arrays. Verify that `canonical_json(x) == canonical_json(json.loads(canonical_json(x)))` for all test cases.

### 4.4 Structured Criteria

**Module:** `theatre/engine/models.py`

```python
class TheatreCriteria(BaseModel):
    """Structured, hash-stable evaluation criteria."""
    criteria_ids: list[str]                    # e.g. ["source_fidelity", "signal_classification"]
    criteria_human: str                        # freeform rubric for human consumption
    weights: dict[str, float] = {}             # keys ⊆ criteria_ids, values sum to 1.0

    @model_validator(mode="after")
    def validate_weights(self) -> "TheatreCriteria":
        if self.weights:
            # Keys must be subset of criteria_ids
            extra = set(self.weights.keys()) - set(self.criteria_ids)
            if extra:
                raise ValueError(f"Weight keys not in criteria_ids: {extra}")
            # Values must sum to 1.0 (within tolerance)
            total = sum(self.weights.values())
            if abs(total - 1.0) > 1e-6:
                raise ValueError(f"Weights must sum to 1.0, got {total}")
        return self
```

### 4.5 OracleAdapter Invocation Contract

**Module:** `theatre/engine/oracle_contract.py`

Wraps the existing `OracleAdapter` with a standardised request/response envelope:

```python
class OracleInvocationRequest(BaseModel):
    invocation_id: str
    theatre_id: str
    episode_id: str
    construct_id: str
    construct_version: str
    input_data: dict
    metadata: OracleInvocationMetadata

class OracleInvocationMetadata(BaseModel):
    timeout_seconds: int = 30
    retry_count: int = 2
    retry_backoff_seconds: float = 5.0
    deterministic: bool = False
    sanitise_input: bool = True

class OracleInvocationResponse(BaseModel):
    invocation_id: str
    construct_id: str
    construct_version: str
    output_data: dict | None = None
    latency_ms: int
    status: Literal["SUCCESS", "TIMEOUT", "ERROR", "REFUSED"]
    error_detail: str | None = None
    responded_at: datetime
```

**Error handling rules:**
- `TIMEOUT` / `ERROR`: episode scored as missing (counts against recall/coverage)
- `REFUSED`: episode excluded from scoring, reason logged
- \>20% failure rate: Theatre transitions to SETTLING with partial results, certificate capped at UNVERIFIED

**Mock adapter rejection:** The engine checks adapter type before certificate-generating runs. `MockOracleAdapter` is allowed in tests but rejected at runtime when `is_certificate_run=True`. This is an engine-level check, not a schema constraint.

### 4.6 Replay Engine

**Module:** `theatre/engine/replay.py`

The Replay Engine orchestrates Product Theatre execution:

```python
class ReplayEngine:
    """Executes Product Theatre lifecycle: invoke construct per episode, score, aggregate."""

    def __init__(
        self,
        theatre: Theatre,
        oracle_adapter: OracleAdapter,
        scoring_provider: TheatreScoringProvider,
        evidence_builder: EvidenceBundleBuilder,
    ):
        ...

    async def run(
        self,
        ground_truth: list[GroundTruthEpisode],
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> ReplayResult:
        """Execute full replay lifecycle.

        1. Verify dataset hash matches commitment
        2. For each episode:
           a. Build OracleInvocationRequest
           b. Invoke construct via OracleAdapter (with retry)
           c. Record invocation in evidence bundle
           d. Score response per committed criteria_ids
           e. Record per-episode scores
        3. Check failure rate (>20% → cap at UNVERIFIED)
        4. Aggregate scores across episodes
        5. Build CalibrationCertificate
        6. Assign verification tier
        7. Finalise evidence bundle
        """
        ...
```

**Key design decision:** Episodes are processed sequentially, not in parallel. Real constructs may have rate limits or stateful behaviour. Parallelism is a future optimisation if constructs opt in.

**Dataset hash verification:** Before the first episode, the engine computes SHA-256 of the ground truth file and compares against `dataset_hashes[replay_dataset_id]` from the commitment receipt. Mismatch → immediate failure, Theatre transitions to SETTLING with error.

### 4.7 Resolution State Machine

**Module:** `theatre/engine/resolution.py`

```python
class ResolutionStep(BaseModel):
    step_id: str
    type: Literal["construct_invocation", "deterministic_computation",
                   "hitl_rubric", "aggregation"]
    construct_id: str | None = None
    input_spec: dict = {}
    output_spec: dict = {}
    escalation_path: str | None = None    # step_id to jump to on failure
    timeout_seconds: int = 30

class ResolutionStateMachine:
    """Executes pre-committed oracle programme sequence."""

    def __init__(self, steps: list[ResolutionStep], version_pins: dict):
        self._steps = {s.step_id: s for s in steps}
        self._execution_order = [s.step_id for s in steps]
        self._version_pins = version_pins

    async def execute(self, context: ResolutionContext) -> ResolutionResult:
        """Run each step in committed order. On failure, follow escalation_path if defined."""
        ...
```

**HITL steps:** When a step has `type: "hitl_rubric"`, the engine records the step as pending and waits for external input. The rubric, scoring scale, and identity separation rules are all pre-committed in `hitl_steps[]`. For this cycle, HITL steps produce a `PENDING_HITL` status — manual resolution through a future UI.

### 4.8 Calibration Certificate (Theatre-Aware)

**Module:** `theatre/engine/certificate.py`

```python
class TheatreCalibrationCertificate(BaseModel):
    """Unified certificate covering both Replay and Market Theatre outputs."""

    # Identity
    certificate_id: str
    theatre_id: str
    template_id: str
    construct_id: str

    # Criteria
    criteria: TheatreCriteria
    scores: dict[str, float]           # criteria_id → score (0.0–1.0)
    composite_score: float             # weighted aggregate

    # Calibration (optional per execution path)
    precision: float | None = None
    recall: float | None = None
    reply_accuracy: float | None = None
    brier_score: float | None = None
    ece: float | None = None

    # Evidence
    replay_count: int
    evidence_bundle_hash: str
    ground_truth_hash: str

    # Reproducibility
    construct_version: str
    construct_chain_versions: dict[str, str] | None = None  # compositional chains
    scorer_version: str
    methodology_version: str
    dataset_hash: str

    # Trust
    verification_tier: Literal["UNVERIFIED", "BACKTESTED", "PROVEN"]
    commitment_hash: str

    # Timestamps
    issued_at: datetime
    expires_at: datetime | None = None
    theatre_committed_at: datetime
    theatre_resolved_at: datetime

    # Integration
    ground_truth_source: str
    execution_path: Literal["replay", "market"]
```

### 4.9 Verification Tier Assigner

**Module:** `theatre/engine/tier_assigner.py`

```python
class TierAssigner:
    """Deterministic verification tier assignment per v0 rules."""

    BACKTESTED_MIN_REPLAYS = 50
    BACKTESTED_EXPIRY_DAYS = 90
    PROVEN_MIN_MONTHS = 3
    PROVEN_EXPIRY_DAYS = 180

    @staticmethod
    def assign(
        replay_count: int,
        has_full_pins: bool,
        has_published_scores: bool,
        has_verifiable_hash: bool,
        has_disputes: bool,
        failure_rate: float,
        history: TierHistory | None = None,
    ) -> Literal["UNVERIFIED", "BACKTESTED", "PROVEN"]:
        """Assign tier based on evidence.

        UNVERIFIED: <50 replays OR missing pins OR incomplete evidence OR >20% failure
        BACKTESTED: ≥50 + full pins + published scores + verifiable hash + no disputes
        PROVEN: BACKTESTED + ≥3 months consecutive + production telemetry + attestation
        """
        if failure_rate > 0.20:
            return "UNVERIFIED"
        if replay_count < TierAssigner.BACKTESTED_MIN_REPLAYS:
            return "UNVERIFIED"
        if not (has_full_pins and has_published_scores and has_verifiable_hash):
            return "UNVERIFIED"
        if has_disputes:
            return "UNVERIFIED"

        # PROVEN requires additional history evidence
        if history and history.meets_proven_requirements():
            return "PROVEN"

        return "BACKTESTED"

    @staticmethod
    def compute_expiry(
        tier: str, issued_at: datetime
    ) -> datetime | None:
        """Compute certificate expiry based on tier."""
        if tier == "UNVERIFIED":
            return None
        if tier == "BACKTESTED":
            return issued_at + timedelta(days=TierAssigner.BACKTESTED_EXPIRY_DAYS)
        if tier == "PROVEN":
            return issued_at + timedelta(days=TierAssigner.PROVEN_EXPIRY_DAYS)
        return None
```

### 4.10 Evidence Bundle Builder

**Module:** `theatre/engine/evidence_bundle.py`

```python
class EvidenceBundleBuilder:
    """Builds the auditable evidence bundle directory for a Theatre."""

    def __init__(self, theatre_id: str, output_dir: Path):
        self._theatre_id = theatre_id
        self._base_dir = output_dir / f"evidence_bundle_{theatre_id}"
        ...

    def write_manifest(self, manifest: BundleManifest) -> None: ...
    def write_template(self, template: dict) -> None: ...
    def write_commitment_receipt(self, receipt: CommitmentReceipt) -> None: ...
    def write_ground_truth(self, dataset: list[dict], filename: str) -> None: ...
    def write_invocation(self, episode_id: str, request: dict, response: dict) -> None: ...
    def write_episode_score(self, score: dict) -> None: ...
    def write_aggregate_scores(self, aggregate: dict) -> None: ...
    def write_certificate(self, certificate: TheatreCalibrationCertificate) -> None: ...
    def append_audit_event(self, event: AuditEvent) -> None: ...
    def compute_bundle_hash(self) -> str: ...

    def validate_minimum_files(self) -> list[str]:
        """Return list of missing required files. Empty = valid."""
        required = [
            "manifest.json", "template.json", "commitment_receipt.json",
            "scores/aggregate.json", "certificate.json",
        ]
        # Also requires ≥1 ground_truth file and ≥1 invocation file
        ...
```

**Bundle structure:**
```
evidence_bundle_{theatre_id}/
├── manifest.json
├── template.json
├── commitment_receipt.json
├── ground_truth/
│   ├── dataset.jsonl
│   └── gold_labels.jsonl      (if applicable)
├── invocations/
│   ├── episode_001.json
│   └── ...
├── scores/
│   ├── per_episode.jsonl
│   └── aggregate.json
├── certificate.json
└── audit_trail.jsonl
```

### 4.11 Constraint Yielding Gate

**Module:** `theatre/engine/constraint_gate.py`

```python
class ConstraintYieldingGate:
    """Enforces: UNVERIFIED + review:skip → review:full. No override."""

    @staticmethod
    def resolve_review_preference(
        tier: str,
        declared_preference: str,
    ) -> str:
        """Resolve actual review level.

        UNVERIFIED constructs always get review:full regardless of declared preference.
        BACKTESTED/PROVEN constructs honour their declared preference.
        """
        if tier == "UNVERIFIED" and declared_preference == "skip":
            return "full"
        return declared_preference
```

### 4.12 Theatre Scoring Provider

**Module:** `theatre/engine/scoring.py`

Extends the existing `ScoringProvider` ABC to support Theatre-specific structured criteria:

```python
class TheatreScoringProvider:
    """Scores construct outputs against committed criteria_ids."""

    def __init__(self, criteria: TheatreCriteria, scorer: ScoringProvider):
        self._criteria = criteria
        self._scorer = scorer

    async def score_episode(
        self,
        ground_truth: GroundTruthEpisode,
        oracle_output: OracleInvocationResponse,
    ) -> dict[str, float]:
        """Score a single episode against all criteria_ids.

        Returns dict of criteria_id → score (0.0–1.0).
        Uses the underlying ScoringProvider for LLM-based scoring,
        with domain-specific criteria from the Theatre template.
        """
        ...

    def compute_composite(self, scores: dict[str, float]) -> float:
        """Weighted aggregate: Σ(weight_i × score_i)."""
        if not self._criteria.weights:
            return sum(scores.values()) / len(scores)  # equal weight fallback
        return sum(
            self._criteria.weights.get(cid, 0) * scores.get(cid, 0)
            for cid in self._criteria.criteria_ids
        )
```

---

## 5. Data Architecture

### 5.1 New Database Tables

All new tables follow the existing `Mapped[]` pattern from `backend/database/models.py`.

#### TheatreTemplate

```python
class TheatreTemplate(Base):
    __tablename__ = "theatre_templates"

    id: Mapped[str] = mapped_column(String(100), primary_key=True)  # e.g. "product_observer_v1"
    template_family: Mapped[str] = mapped_column(String(50))         # PRODUCT, GEOPOLITICAL, etc.
    execution_path: Mapped[str] = mapped_column(String(10))          # replay, market
    display_name: Mapped[str] = mapped_column(String(100))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    schema_version: Mapped[str] = mapped_column(String(20))
    template_json: Mapped[dict] = mapped_column(JSON)               # full template
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    theatres: Mapped[List["Theatre"]] = relationship(back_populates="template")

    __table_args__ = (
        Index("ix_theatre_templates_family", "template_family"),
        Index("ix_theatre_templates_execution_path", "execution_path"),
    )
```

#### Theatre

```python
class Theatre(Base):
    __tablename__ = "theatres"

    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=_generate_uuid)
    user_id: Mapped[str] = mapped_column(String(50), ForeignKey("users.id"), index=True)
    template_id: Mapped[str] = mapped_column(
        String(100), ForeignKey("theatre_templates.id"), index=True
    )
    state: Mapped[str] = mapped_column(String(20), default="DRAFT")  # TheatreState enum value
    construct_id: Mapped[str] = mapped_column(String(255), index=True)

    # Commitment fields (populated on COMMITTED transition)
    commitment_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    committed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    version_pins: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    dataset_hashes: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Execution tracking
    progress: Mapped[int] = mapped_column(Integer, default=0)
    total_episodes: Mapped[int] = mapped_column(Integer, default=0)
    failure_count: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Resolution
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    certificate_id: Mapped[Optional[str]] = mapped_column(
        String(50), ForeignKey("theatre_certificates.id"), nullable=True
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    template: Mapped["TheatreTemplate"] = relationship(back_populates="theatres")
    certificate: Mapped[Optional["TheatreCertificate"]] = relationship(back_populates="theatre")
    episode_scores: Mapped[List["TheatreEpisodeScore"]] = relationship(back_populates="theatre")
    audit_events: Mapped[List["TheatreAuditEvent"]] = relationship(back_populates="theatre")

    __table_args__ = (
        Index("ix_theatres_state", "state"),
        Index("ix_theatres_construct", "construct_id"),
        Index("ix_theatres_user_created", "user_id", "created_at"),
    )
```

#### TheatreCertificate

```python
class TheatreCertificate(Base):
    __tablename__ = "theatre_certificates"

    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=_generate_uuid)
    theatre_id: Mapped[str] = mapped_column(String(50), index=True)
    template_id: Mapped[str] = mapped_column(String(100), index=True)
    construct_id: Mapped[str] = mapped_column(String(255), index=True)

    # Criteria & scores
    criteria_json: Mapped[dict] = mapped_column(JSON)       # TheatreCriteria as dict
    scores_json: Mapped[dict] = mapped_column(JSON)          # criteria_id → float
    composite_score: Mapped[float] = mapped_column(Float)

    # Calibration (optional)
    precision: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    recall: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    reply_accuracy: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    brier_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ece: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Evidence
    replay_count: Mapped[int] = mapped_column(Integer)
    evidence_bundle_hash: Mapped[str] = mapped_column(String(64))
    ground_truth_hash: Mapped[str] = mapped_column(String(64))

    # Reproducibility
    construct_version: Mapped[str] = mapped_column(String(64))
    construct_chain_versions: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    scorer_version: Mapped[str] = mapped_column(String(100))
    methodology_version: Mapped[str] = mapped_column(String(20))
    dataset_hash: Mapped[str] = mapped_column(String(64))

    # Trust
    verification_tier: Mapped[str] = mapped_column(String(20))    # UNVERIFIED/BACKTESTED/PROVEN
    commitment_hash: Mapped[str] = mapped_column(String(64))

    # Timestamps
    issued_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    theatre_committed_at: Mapped[datetime] = mapped_column(DateTime)
    theatre_resolved_at: Mapped[datetime] = mapped_column(DateTime)

    # Integration
    ground_truth_source: Mapped[str] = mapped_column(String(100))
    execution_path: Mapped[str] = mapped_column(String(10))

    # Relationships
    theatre: Mapped[Optional["Theatre"]] = relationship(back_populates="certificate")
    episode_scores: Mapped[List["TheatreEpisodeScore"]] = relationship(
        back_populates="certificate"
    )

    __table_args__ = (
        Index("ix_theatre_certs_construct_created", "construct_id", "issued_at"),
        Index("ix_theatre_certs_tier", "verification_tier"),
        Index("ix_theatre_certs_template", "template_id"),
    )
```

#### TheatreEpisodeScore

```python
class TheatreEpisodeScore(Base):
    __tablename__ = "theatre_episode_scores"

    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=_generate_uuid)
    theatre_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("theatres.id"), index=True
    )
    certificate_id: Mapped[Optional[str]] = mapped_column(
        String(50), ForeignKey("theatre_certificates.id"), nullable=True, index=True
    )
    episode_id: Mapped[str] = mapped_column(String(255))
    invocation_status: Mapped[str] = mapped_column(String(20))  # SUCCESS/TIMEOUT/ERROR/REFUSED
    latency_ms: Mapped[int] = mapped_column(Integer)
    scores_json: Mapped[dict] = mapped_column(JSON)             # criteria_id → float
    composite_score: Mapped[float] = mapped_column(Float)
    scored_at: Mapped[datetime] = mapped_column(DateTime)

    # Relationships
    theatre: Mapped["Theatre"] = relationship(back_populates="episode_scores")
    certificate: Mapped[Optional["TheatreCertificate"]] = relationship(
        back_populates="episode_scores"
    )
```

#### TheatreAuditEvent

```python
class TheatreAuditEvent(Base):
    __tablename__ = "theatre_audit_events"

    id: Mapped[str] = mapped_column(String(50), primary_key=True, default=_generate_uuid)
    theatre_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("theatres.id"), index=True
    )
    event_type: Mapped[str] = mapped_column(String(50))    # state_transition, invocation, score, error
    from_state: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    to_state: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    detail_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    theatre: Mapped["Theatre"] = relationship(back_populates="audit_events")

    __table_args__ = (
        Index("ix_theatre_audit_theatre_created", "theatre_id", "created_at"),
    )
```

### 5.2 Migration

New Alembic migration adding 5 tables: `theatre_templates`, `theatres`, `theatre_certificates`, `theatre_episode_scores`, `theatre_audit_events`. No modification to existing tables.

---

## 6. API Design

### 6.1 Router

**Module:** `backend/api/theatre_routes.py`

```python
router = APIRouter(prefix="/api/v1/theatres", tags=["theatres"])
```

Mounted in `backend/main.py` using the same try/except pattern:
```python
try:
    from backend.api.theatre_routes import router as theatre_router
    app.include_router(theatre_router)
except ImportError:
    logger.warning("Theatre routes not available")
```

### 6.2 Endpoints

#### Theatre CRUD & Execution

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/api/v1/theatres` | Required | Create Theatre from template JSON |
| `POST` | `/api/v1/theatres/{id}/commit` | Required | Generate commitment hash, freeze parameters |
| `POST` | `/api/v1/theatres/{id}/run` | Required | Execute full Product Theatre lifecycle (background) |
| `GET` | `/api/v1/theatres/{id}` | Required | Get Theatre state, parameters, progress |
| `GET` | `/api/v1/theatres/{id}/commitment` | Public | Commitment receipt with parameter snapshot |
| `POST` | `/api/v1/theatres/{id}/settle` | Required | Manual settlement trigger (Market Theatres, future) |
| `GET` | `/api/v1/theatres/{id}/certificate` | Public | Calibration certificate (after RESOLVED) |
| `GET` | `/api/v1/theatres/{id}/replay` | Public | Full replay data for RLMF export |

#### Template Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/api/v1/templates` | Public | List available templates |
| `GET` | `/api/v1/templates/{template_id}` | Public | Template schema and metadata |

#### Certificate Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/api/v1/certificates/{certificate_id}` | Public | Certificate by ID (Hounfour integration) |
| `GET` | `/api/v1/certificates` | Public | List certificates with `?construct_id=` filter |

### 6.3 Request/Response Schemas

**Module:** `backend/schemas/theatre.py`

```python
# --- Requests ---

class TheatreCreate(BaseModel):
    """POST /api/v1/theatres — Create Theatre from template JSON."""
    template_json: dict = Field(..., description="Full Theatre Template conforming to v2 schema")

    @model_validator(mode="after")
    def validate_template(self) -> "TheatreCreate":
        # Schema validation happens in the route handler, not here
        return self

class TheatreRunRequest(BaseModel):
    """POST /api/v1/theatres/{id}/run — Optional execution overrides."""
    ground_truth_path: str | None = None    # Override replay_data_path for testing
    is_certificate_run: bool = True         # False allows MockOracleAdapter

# --- Responses ---

class TheatreResponse(BaseModel):
    """Single Theatre view."""
    id: str
    template_id: str
    state: str
    construct_id: str
    commitment_hash: str | None
    committed_at: datetime | None
    progress: int
    total_episodes: int
    failure_count: int
    error: str | None
    certificate_id: str | None
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class CommitmentReceiptResponse(BaseModel):
    """Commitment receipt — public, for third-party verification."""
    theatre_id: str
    commitment_hash: str
    committed_at: datetime
    template_snapshot: dict
    version_pins: dict
    dataset_hashes: dict

class TheatreCertificateResponse(BaseModel):
    """Full certificate with all fields."""
    certificate_id: str
    theatre_id: str
    template_id: str
    construct_id: str
    criteria: dict
    scores: dict[str, float]
    composite_score: float
    precision: float | None
    recall: float | None
    reply_accuracy: float | None
    brier_score: float | None
    ece: float | None
    replay_count: int
    verification_tier: str
    commitment_hash: str
    construct_version: str
    construct_chain_versions: dict[str, str] | None
    scorer_version: str
    methodology_version: str
    evidence_bundle_hash: str
    ground_truth_source: str
    execution_path: str
    issued_at: datetime
    expires_at: datetime | None
    theatre_committed_at: datetime
    theatre_resolved_at: datetime
    model_config = ConfigDict(from_attributes=True)

class TheatreCertificateSummaryResponse(BaseModel):
    """Certificate list view."""
    certificate_id: str
    construct_id: str
    composite_score: float
    verification_tier: str
    replay_count: int
    issued_at: datetime
    expires_at: datetime | None
    model_config = ConfigDict(from_attributes=True)

class TheatreListResponse(BaseModel):
    """Paginated Theatre list."""
    theatres: list[TheatreResponse]
    total: int
    limit: int
    offset: int

class CertificateListResponse(BaseModel):
    """Paginated certificate list."""
    certificates: list[TheatreCertificateSummaryResponse]
    total: int
    limit: int
    offset: int

class TemplateResponse(BaseModel):
    """Template metadata."""
    id: str
    template_family: str
    execution_path: str
    display_name: str
    description: str | None
    schema_version: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class TemplateListResponse(BaseModel):
    """Paginated template list."""
    templates: list[TemplateResponse]
    total: int
    limit: int
    offset: int
```

### 6.4 Background Task Pattern

**Module:** `backend/services/theatre_bridge.py`

Follows the exact pattern from `verification_bridge.py`:

```python
# Graceful import
try:
    from theatre.engine.replay import ReplayEngine
    from theatre.engine.state_machine import TheatreStateMachine, TheatreState
    from theatre.engine.commitment import CommitmentProtocol
    from theatre.engine.models import TheatreCriteria
    from theatre.engine.certificate import TheatreCalibrationCertificate
    from theatre.engine.tier_assigner import TierAssigner
    from theatre.engine.evidence_bundle import EvidenceBundleBuilder
    from theatre.engine.oracle_contract import OracleInvocationRequest
    THEATRE_ENGINE_AVAILABLE = True
except ImportError:
    THEATRE_ENGINE_AVAILABLE = False

async def run_theatre_task(theatre_id: str) -> None:
    """Background task — runs full Theatre lifecycle.

    Opens its own session (not shared with request).
    Guarantees Theatre reaches a terminal state.

    Flow:
    1. Load Theatre + template from DB
    2. Transition COMMITTED → ACTIVE
    3. Verify dataset hash
    4. Run ReplayEngine
    5. Transition ACTIVE → SETTLING
    6. Run ResolutionStateMachine (aggregate scores)
    7. Transition SETTLING → RESOLVED
    8. Issue certificate, assign tier
    9. Persist certificate + episode scores
    10. Transition RESOLVED → ARCHIVED (or leave at RESOLVED)
    """
    ...
```

---

## 7. Security Architecture

### 7.1 Authentication & Authorisation

- **Theatre creation, commit, run, settle:** `Depends(get_current_user)` — JWT bearer token required
- **Commitment receipts, certificates, replay data, templates:** Public — no auth. Required for third-party verification and Hounfour integration.
- **Theatre state/progress:** Authenticated — users see only their own Theatres
- Pattern matches `verification_routes.py` exactly

### 7.2 Data Integrity

- **Commitment hash immutability:** After COMMITTED, the DB row's template, version_pins, and dataset_hashes columns are never updated. The state machine prevents re-entry to DRAFT.
- **Dataset hash verification:** Before execution, SHA-256 of ground truth data is compared against committed hash. Mismatch halts the Theatre.
- **Version pins:** Exact construct commit hashes prevent silent updates between runs.

### 7.3 Input Validation

- **Template validation:** Full JSON Schema validation against `echelon_theatre_schema_v2.json` on Theatre creation
- **Runtime validation rules:** Weight sum = 1.0, construct pin linkage, dataset hash presence, mock adapter rejection for certificate runs
- **Input sanitisation:** OracleAdapter input data sanitised before passing to external constructs (injection prevention)
- **Error truncation:** Error strings capped at 2000 characters (matches verification bridge pattern)

### 7.4 Secrets

- No secrets stored in commitment hashes, evidence bundles, or certificates
- No API keys in template JSON — adapter endpoints are URLs only
- `github_token` handling follows verification bridge pattern (runtime only, not persisted)

---

## 8. Template Validation

### 8.1 Schema Validation

Templates are validated against `docs/schemas/echelon_theatre_schema_v2.json` using the `jsonschema` library. This covers structural validation (required fields, types, enums, patterns).

### 8.2 Runtime Validation

Eight rules that cannot be expressed in JSON Schema (documented in `runtime_validation_rules._doc`):

1. `criteria.weights` keys ⊆ `criteria.criteria_ids`
2. `criteria.weights` values sum to 1.0
3. Every `construct_id` in `resolution_programme` exists in `version_pins.constructs`
4. Every construct in `product_theatre_config.construct_chain` has a `version_pins.constructs` entry
5. Every `hitl_steps[].step_id` matches a `resolution_programme` step with type `hitl_rubric`
6. `adapter_type: "mock"` rejected for certificate-generating runs
7. `dataset_hashes[product_theatre_config.replay_dataset_id]` must be present
8. Canonical JSON: all hash computations use `canonical_json()`, never raw serialisation

### 8.3 Validation Module

**Module:** `theatre/engine/template_validator.py`

```python
class TemplateValidator:
    """Validates Theatre templates against schema + runtime rules."""

    def __init__(self, schema_path: Path):
        self._schema = json.loads(schema_path.read_text())

    def validate(self, template: dict, is_certificate_run: bool = True) -> list[str]:
        """Return list of validation errors. Empty = valid.

        Phase 1: JSON Schema validation
        Phase 2: Runtime rules (weight sums, pin linkage, etc.)
        Phase 3: Certificate-run rules (mock adapter rejection)
        """
        ...
```

---

## 9. Test Fixtures

### 9.1 PRODUCT_OBSERVER_V1

- **Criteria IDs:** `["source_fidelity", "signal_classification", "canvas_enrichment_freshness"]`
- **Ground truth:** 163 provenance records (JSONL with SHA-256 hash chain)
- **Two layers:** (1) Deterministic — hash-chain integrity, record completeness. (2) Labelled — classification accuracy against gold set.
- **Adapter:** HTTP (real Observer endpoint) or Mock (CI only)
- **Expected tier:** PROVEN candidate (sufficient replays + full pins)

### 9.2 PRODUCT_EASEL_V1

- **Criteria IDs:** `["vocabulary_adherence", "tdr_propagation_fidelity", "downstream_compliance"]`
- **Ground truth:** TDR records + Artisan `/inscribe` compliance output
- **Compositional chain:** Easel → Artisan → Mint (3 construct versions pinned)
- **HITL provision:** pre-committed rubric step for taste/creative judgement
- **Adapter:** HTTP (Easel endpoint)
- **Expected tier:** BACKTESTED candidate

### 9.3 PRODUCT_CARTOGRAPH_V1

- **Criteria IDs:** `["isometric_convention_compliance", "hex_grid_accuracy", "detail_density_adherence"]`
- **Ground truth:** Deterministic — mathematical validation (hexagonal grid geometry)
- **Adapter:** HTTP or Local (Cartograph process)
- **Expected tier:** UNVERIFIED (3/4 skills are stubs — verification reveals this)

### 9.4 Test Data

Each fixture includes:
- Template JSON conforming to `echelon_theatre_schema_v2.json`
- Sample ground truth dataset (≥5 episodes for integration tests, full dataset for property tests)
- Expected commitment hash (pre-computed for determinism tests)
- Mock construct responses (for CI/unit tests only)

---

## 10. Package Structure

```
theatre/
├── __init__.py
├── engine/
│   ├── __init__.py
│   ├── state_machine.py          # TheatreStateMachine, TheatreState, VALID_TRANSITIONS
│   ├── commitment.py             # CommitmentProtocol, CommitmentReceipt
│   ├── canonical_json.py         # canonical_json(), _normalise_value(), _normalise_float()
│   ├── models.py                 # TheatreCriteria, GroundTruthEpisode, OracleInvocation*
│   ├── oracle_contract.py        # OracleInvocationRequest/Response/Metadata
│   ├── replay.py                 # ReplayEngine
│   ├── resolution.py             # ResolutionStateMachine, ResolutionStep, ResolutionResult
│   ├── certificate.py            # TheatreCalibrationCertificate
│   ├── tier_assigner.py          # TierAssigner, TierHistory
│   ├── evidence_bundle.py        # EvidenceBundleBuilder, BundleManifest
│   ├── constraint_gate.py        # ConstraintYieldingGate
│   ├── scoring.py                # TheatreScoringProvider
│   └── template_validator.py     # TemplateValidator (schema + runtime rules)
├── fixtures/
│   ├── __init__.py
│   ├── product_observer_v1.json
│   ├── product_easel_v1.json
│   ├── product_cartograph_v1.json
│   └── sample_ground_truth/
│       ├── observer_provenance.jsonl
│       ├── easel_tdr_records.jsonl
│       └── cartograph_grid_reference.jsonl

backend/
├── api/
│   └── theatre_routes.py         # 12 endpoints
├── schemas/
│   └── theatre.py                # Request/response Pydantic models
├── services/
│   └── theatre_bridge.py         # Background task: Theatre lifecycle execution
└── database/
    └── models.py                 # (append) 5 new tables

tests/
├── theatre/
│   ├── test_state_machine.py     # All valid + invalid transitions
│   ├── test_commitment.py        # Hash determinism, round-trip, verification
│   ├── test_canonical_json.py    # RFC 8785 compliance, float normalisation, edge cases
│   ├── test_criteria.py          # Weight validation, subset enforcement
│   ├── test_replay_engine.py     # Full lifecycle with mock adapter
│   ├── test_resolution.py        # Step execution, escalation paths, HITL
│   ├── test_certificate.py       # Certificate generation, field completeness
│   ├── test_tier_assigner.py     # All tier boundary conditions, expiry
│   ├── test_evidence_bundle.py   # Bundle generation, minimum files validation
│   ├── test_constraint_gate.py   # UNVERIFIED override, BACKTESTED passthrough
│   ├── test_template_validator.py # Schema + runtime rules
│   └── test_integration.py       # End-to-end: create → commit → run → certificate
└── backend/
    ├── test_theatre_routes.py    # API endpoint tests
    └── test_theatre_bridge.py    # Background task tests
```

---

## 11. Scalability & Performance

- **Sequential episode processing:** Intentional — real constructs may be stateful or rate-limited. Future optimisation with construct-declared parallelism opt-in.
- **Background task pattern:** `asyncio.create_task()` — matches existing verification bridge. No queue system for MVP.
- **Database indexing:** Composite indexes on `(construct_id, issued_at)` for certificate lookups by construct. Single-column indexes on `state`, `verification_tier`, `template_id` for filtering.
- **Evidence bundle storage:** Local filesystem for MVP. Future: S3/GCS with hash-based deduplication.
- **OracleAdapter timeout:** Configurable per invocation (default 30s). Prevents single slow construct from blocking Theatre indefinitely.

---

## 12. Development Workflow

- **Branch:** Feature branch from `main`
- **PR:** Single consolidated PR for all sprints
- **Testing:** `pytest` with `pytest-asyncio` for async tests
- **No frontend changes** — this cycle is backend/engine only
- **Database:** Alembic migration for new tables, no modification to existing

---

## 13. Technical Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Canonical JSON platform divergence | Non-reproducible hashes | Extensive round-trip tests; pin Python version in CI; explicit float normalisation |
| OracleAdapter latency | Slow Theatre execution | Configurable timeout + retry; progress callbacks; >20% failure cap |
| Compositional chain complexity (Easel) | Version pin management | Each construct pinned explicitly; chain order committed; tested with all 3 fixtures |
| Schema backward compatibility | Existing templates break | All extensions additive; conditional validation by execution_path |
| Evidence bundle storage growth | Disk usage | Hash references instead of inline data where feasible |
| echelon-verify missing from working tree | Import failures | Graceful import pattern (try/except) matching verification_bridge.py |

---

## 14. Future Considerations

- **Cycle-030 integration:** Market Theatre execution plugs in when LMSR engine is available. The schema and state machine already support `market` execution path — only the `ACTIVE` state behaviour changes.
- **OSINT adapter integration (Cycle-032):** Evidence Bundle schema designed to accept external data source references.
- **Agent architecture (Cycle-033):** Theatre provides the execution context; agents trade within Market Theatres.
- **On-chain commitment:** The commitment hash is currently stored in PostgreSQL. Future migration to on-chain publication (commitment hash → Base Sepolia → mainnet).
- **Parallel episode processing:** Opt-in per construct, gated on construct metadata declaring parallelism safety.
