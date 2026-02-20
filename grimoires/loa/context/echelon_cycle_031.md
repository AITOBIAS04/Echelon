# Cycle-031: Theatre Template Engine

> Cycle-specific context for Loa. Read alongside `echelon_platform_roadmap.md`.
> This cycle produces the Theatre lifecycle consumed by every subsequent cycle.
> UK British English throughout.

---

## Objective

Build the Theatre as a state machine — the container within which all Echelon activity occurs. A Theatre is created from a Theatre Template, passes through an immutable commitment protocol, and settles deterministically when ground truth is revealed.

**Critical design decision: this cycle introduces two distinct execution paths.**

- **Replay Theatres (Product Theatres):** commit → invoke real construct via OracleAdapter → score against ground truth → issue calibration certificate. No LMSR markets, no agents, no trading. This is what Soju needs now.
- **Market Theatres (Geopolitical Theatres):** full LMSR lifecycle with trading, agents, fork points, and settlement. Schema-only in this cycle — execution comes when Cycle-030 (LMSR engine) is complete.

Both share the commitment protocol, template validation, resolution engine, and certificate output. The execution path diverges at the ACTIVE state.

---

## Why Two Execution Paths

Product Theatres are replay scoring, not prediction markets. Observer doesn't need agents trading against a cost function. It needs: ingest ground truth → invoke construct → score output → issue certificate. That's the Community Oracle pipeline (Cycle-027) formalised with commitment hashes and structured templates.

Coupling Product Theatres to the full LMSR lifecycle would block Soju's testing on Cycle-030 delivery — an unnecessary dependency. Product Theatres can ship immediately. Market Theatres gain LMSR integration when Cycle-030 lands.

---

## Theatre Lifecycle

A Theatre progresses through six states. Transitions are irreversible.

```
DRAFT → COMMITTED → ACTIVE → SETTLING → RESOLVED → ARCHIVED
```

**The invariant after COMMITTED:** no parameter changes are permitted. The resolution programme itself may include pre-committed human-in-the-loop steps (e.g., a rubric scorer for Easel's taste dimensions), but the process, identity requirements, and rubric for that human involvement must be committed upfront. No one can change the rules after the Theatre is committed.

| State | Entry Condition | What Happens | Exit Condition |
|-------|-----------------|--------------|----------------|
| DRAFT | Template validated against schema | Creator configures parameters: execution path (replay/market), fork points, criteria, duration, resolution rules | Creator triggers commitment |
| COMMITTED | Commitment hash published | All parameters frozen. For Market Theatres: capital escrowed (`b · ln(n)` + fees). For Replay Theatres: ground truth dataset hash verified. | Execution begins |
| ACTIVE | Execution opens | **Replay path:** OracleAdapter invoked against ground truth episodes sequentially. **Market path:** agents and participants trade against LMSR cost function. Fork points activate when trigger conditions met. | Terminal condition reached |
| SETTLING | Resolution triggered | Pre-committed resolution state machine executes. Ground truth compared against oracle/market outputs. Scoring computed per committed criteria. | Resolution state machine completes |
| RESOLVED | Settlement computed | Winning outcome / scores determined. Calibration metrics calculated. Verification tier assigned per tiering rules. | Certificate issued, redemption window opens |
| ARCHIVED | Redemption complete or timeout | Full Theatre replay data preserved. RLMF export generated. Calibration certificate finalised. | Terminal — immutable record |

---

## Commitment Protocol

The Commitment Protocol is Echelon's core trust mechanism. Every parameter governing a Theatre's lifecycle is locked before any execution begins.

### Commitment Hash Generation

The commitment hash is computed over the **full canonicalised template JSON** plus external version pins. This prevents "uncommitted knobs" — any field change invalidates the hash.

```python
commitment_hash = SHA-256(
    canonical_json({
        "dataset_hashes": dataset_hashes,
        "template": full_template,
        "version_pins": version_pins
    })
)
```

The input to SHA-256 is one canonical JSON string from one composite object with three keys in lexicographic order. Implementations must not concatenate separately serialised fragments — this eliminates ambiguity about delimiters, ordering, or boundary encoding between components.

The hash is deterministic — same inputs always produce the same hash. Third parties can recompute and verify.

### Canonical JSON Rules

For commitment hashes to be reproducible by third parties, the canonicalisation must be deterministic. Echelon uses the following rules (aligned with RFC 8785 — JSON Canonicalization Scheme):

- **Key ordering:** all object keys sorted lexicographically (Unicode code point order)
- **Whitespace:** no whitespace between tokens (no spaces after colons or commas, no newlines)
- **Numbers:** integers as-is, floats with no trailing zeroes, no positive sign prefix, no leading zeroes. `NaN` and `Infinity` are prohibited.
- **Strings:** UTF-8 encoded, minimal escaping (only characters that JSON requires to be escaped)
- **Null handling:** `null` values included (not omitted) — field presence is part of the hash
- **Field ordering within nested objects:** recursive lexicographic sorting at every level
- **Arrays:** preserve insertion order (arrays are ordered by definition)

Implementation: use `json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=False)` as the baseline, with explicit float normalisation applied before serialisation. Provide a `canonical_json()` utility function that all hash computations must use — never raw `json.dumps()`.

### What Gets Committed

| Parameter | What Is Committed | Notes |
|-----------|-------------------|-------|
| Theatre Template | Full JSON (all fields) | Hash of entire canonical JSON, not selected fields |
| Execution Path | `replay` or `market` | Determines which ACTIVE behaviour applies |
| Criteria | Structured criteria IDs + human rubric | See Criteria section below |
| Resolution Programme | Ordered oracle step sequence | Each step includes construct ID + version pin |
| Version Pins | Exact commit hash for every construct in the chain | Critical for compositional Theatres (Easel → Artisan → Mint) |
| Dataset Hashes | SHA-256 of ground truth datasets | Ensures replay reproducibility |
| Scorer Pins | Scorer model ID + version | Prevents silent scorer drift |
| Data Sources | Provider endpoints, polling frequency, confidence weights | For Market Theatres only |
| Market Parameters | LMSR liquidity `b`, fee schedule, duration | For Market Theatres only |
| Paradox Thresholds | Logic Gap triggers, stability triggers | For Market Theatres only |
| Scoring Config | Score vector weights, tie-breakers | Drives calibration output |
| HITL Steps | Pre-committed human review rubrics, identity separation rules | If resolution programme includes human scoring |

---

## Structured Criteria (the anti-slop field)

Criteria defines what a Theatre measures. It must be structured and hash-stable — not a freeform string.

### Schema

```python
class TheatreCriteria(BaseModel):
    criteria_ids: list[str]        # deterministic keys, e.g. ["source_fidelity", "signal_classification"]
    criteria_human: str            # freeform rubric summary for human consumption
    weights: dict[str, float]      # optional per-criterion weights, keys match criteria_ids
```

**Why structured:** `criteria_ids` become the canonical keys in the certificate `scores` dict. They are hashable, auditable, and version-stable. The `criteria_human` field preserves the anti-slop intent — human-defined explanation of what each criterion means in this domain. The `weights` dict enables weighted composite scoring.

### Examples

**Observer:**
```python
TheatreCriteria(
    criteria_ids=["source_fidelity", "signal_classification", "canvas_enrichment_freshness"],
    criteria_human="Source fidelity measures provenance chain integrity. Signal classification measures correct routing of research signals to canvas categories. Canvas enrichment freshness measures time-to-update after new source material.",
    weights={"source_fidelity": 0.4, "signal_classification": 0.4, "canvas_enrichment_freshness": 0.2}
)
```

**Cartograph:**
```python
TheatreCriteria(
    criteria_ids=["isometric_convention_compliance", "hex_grid_accuracy", "detail_density_adherence"],
    criteria_human="Isometric conventions per project style guide. Hex grid accuracy is mathematical — pixel-level comparison against reference grid. Detail density adherence measures information density per tile against committed pillar targets.",
    weights={"isometric_convention_compliance": 0.3, "hex_grid_accuracy": 0.5, "detail_density_adherence": 0.2}
)
```

---

## Two Theatre Families

### Replay Theatres (Product Theatres) — ships now

Product Theatres verify AI construct capabilities against engineering ground truth that already exists. They use the **Replay Engine** execution path: no LMSR markets, no agents, no trading.

**Execution flow:**

```
1. Validate template against schema
2. COMMIT: hash full template + version pins + dataset hashes
3. ACTIVE: for each episode in ground truth dataset:
   a. Invoke real construct via OracleAdapter (HTTP or local)
   b. Capture construct output
   c. Score output against ground truth per committed criteria
4. SETTLING: aggregate scores across all episodes
5. RESOLVED: compute calibration metrics, assign verification tier
6. ARCHIVED: issue certificate, generate RLMF-compatible export
```

**Key requirement: real construct invocation.** Product Theatre test fixtures must call real constructs through the OracleAdapter interface (HTTP endpoint or local process). Mock/stub responses are permitted only for unit tests and CI, never for certificate generation. A certificate based on mock responses is the "automated scan PDF" — the sensation of verification without substance.

**Ground truth characteristics:**
- Free (byproduct of building): GitHub diffs, CI output, provenance records, WCAG audit results
- Hash-verifiable: dataset integrity confirmed before execution begins
- Version-pinned: exact dataset hash committed, replay is reproducible

### Market Theatres (Geopolitical Theatres) — schema only this cycle

Market Theatres create counterfactual prediction markets using the full LMSR lifecycle. In this cycle, only the template schema and validation are implemented. Execution requires Cycle-030 (LMSR engine).

**Execution flow (future):**

```
1. Validate template against schema
2. COMMIT: hash template + escrow capital (b · ln(n) + fees)
3. ACTIVE: LMSR markets open at fork points, agents trade
4. SETTLING: resolution state machine executes, ground truth ingested
5. RESOLVED: positions settled, calibration metrics computed
6. ARCHIVED: certificate issued, RLMF export generated
```

---

## Concrete Test Fixtures (from Echelon#34)

Soju filed three Product Theatre templates on AITOBIAS04/Echelon#34. These are real constructs with real ground truth. They are the primary test fixtures and must run with **real OracleAdapter invocation**, not stubs.

### PRODUCT_OBSERVER_V1

**Construct:** Observer (user research)
**What It Tests:** Source fidelity, signal classification, canvas enrichment freshness
**Ground Truth Source:** 163 provenance records (append-only JSONL, SHA-256 hash chain)
**Criteria IDs:** `["source_fidelity", "signal_classification", "canvas_enrichment_freshness"]`
**Expected Tier:** PROVEN candidate (mature construct, rich ground truth)
**Resolution:** Deterministic for provenance integrity; requires small gold-label set for classification accuracy

**Circularity mitigation:** Observer's provenance records are not its own outputs — they are records of research interactions that Observer processes. However, scoring classification accuracy (did Observer correctly route a signal?) requires an independent label set, not Observer's own prior classifications. Two verification layers:

1. **Deterministic layer:** hash-chain integrity, record completeness, timestamp ordering — fully automated, no circularity risk
2. **Labelled layer:** source-fidelity categories and signal routing accuracy scored against a human-labelled gold set (even a small one, e.g., 20–30 labelled records from the 163). This prevents grading the model against its own outputs.

**Version pins:** Observer construct commit hash, scorer version, dataset hash (SHA-256 of the 163-record JSONL)

### PRODUCT_EASEL_V1

**Construct:** Easel (creative direction)
**What It Tests:** Vocabulary/TDR decision propagation through downstream constructs
**Ground Truth Source:** TDR records + Artisan `/inscribe` compliance output
**Criteria IDs:** `["vocabulary_adherence", "tdr_propagation_fidelity", "downstream_compliance"]`
**Expected Tier:** BACKTESTED candidate (compositional verification is harder)
**Resolution:** Semi-deterministic — TDR compliance is measurable, but creative taste has subjective components

**Compositional chain:** Easel → Artisan → Mint (3-construct chain). All three construct versions must be pinned in the commitment hash. If any construct in the chain updates, the replay is not comparable to prior runs — a new Theatre instance is required.

**Version pins:** Easel commit hash, Artisan commit hash, Mint commit hash, scorer version, TDR dataset hash, `/inscribe` output dataset hash

**HITL provision:** the resolution programme may include a pre-committed rubric step for taste/creative judgement scoring. The rubric, identity separation rules (scorer ≠ construct author), and scoring scale are committed at Theatre creation. This is not "human intervention" — it is a pre-committed process.

### PRODUCT_CARTOGRAPH_V1

**Construct:** Cartograph (spatial accuracy)
**What It Tests:** Isometric convention compliance, hex grid accuracy, detail density pillar adherence
**Ground Truth Source:** Deterministic — mathematical validation of spatial computations
**Criteria IDs:** `["isometric_convention_compliance", "hex_grid_accuracy", "detail_density_adherence"]`
**Expected Tier:** UNVERIFIED currently (3/4 skills are stubs — verification reveals this)
**Resolution:** Fully deterministic — spatial computations verifiable by mathematical comparison

**Why this fixture matters:** Cartograph demonstrates that verification can *reveal gaps*. A construct with 3/4 stub skills will score low on those dimensions. The certificate doesn't lie — it exposes that declared depth ≠ actual capability. This is the Pashov principle in action.

**Version pins:** Cartograph commit hash, scorer version, reference grid dataset hash

### Why These Three Matter

They represent the full spectrum:
- **Observer:** replay with independent gold labels → basic pattern
- **Easel:** compositional chain with version pinning and HITL rubric → hardest case
- **Cartograph:** deterministic maths exposing stubs → demonstrates the "earned trust" thesis

The `criteria_ids` are different for each. The engine must score `source_fidelity` for Observer and `hex_grid_accuracy` for Cartograph using the same Theatre lifecycle with different criteria configurations.

---

## Geopolitical Template Families (Schema Only)

Define schema structure for future Market Theatres. No execution this cycle.

| Family | Example Fork Points | Ground Truth Source |
|--------|---------------------|---------------------|
| MILITARY | Diplomatic de-escalation / Sustained posturing / Kinetic escalation | GDELT events + satellite imagery |
| COMMODITY | Supply normalisation / Sustained disruption / Cascade shock | Polygon.io price data |
| MARITIME | Transit resumes / Prolonged blockade / Military interdiction | Spire Global AIS |
| DIPLOMATIC | Resolution adopted / Deadlocked session / Walkout | GDELT + official communiqué feeds |
| INFRASTRUCTURE | Accidental damage / State-attributed sabotage / Coordinated attack | Dataminr + GDELT |
| FX | Central bank intervention / Managed depreciation / Disorderly collapse | Polygon.io + central bank feeds |
| ENERGY | Capacity expansion / Geopolitical hedge / Export weaponisation | Satellite + Polygon.io |
| CORPORATE | Routine governance / Strategic pivot / Crisis response | RavenPack + SEC filings |

---

## Verification Tier Rules (v0)

Tier assignment is deterministic based on evidence. These are the initial rules — expect refinement as real data flows.

### UNVERIFIED

- Fewer than 50 replay episodes scored, OR
- Missing reproducibility pins (construct version, dataset hash, scorer version), OR
- Certificate evidence bundle incomplete

**Hounfour routing:** restricted to baseline model pools. Constraint yielding (`review: skip`) treated as `review: full`.

### BACKTESTED

All of the following must be true:
- ≥ 50 replay episodes scored
- Full reproducibility pins committed and verifiable (construct version hash, dataset hash, scorer version)
- Published scores across all committed `criteria_ids`
- Commitment hash verifiable by third party
- No unresolved disputes

**Hounfour routing:** mid-tier brigade routing.

### PROVEN

All BACKTESTED requirements, plus:
- ≥ 3 months of consecutive verification (multiple Theatre runs over time)
- Production telemetry integration (construct performance in live usage, not just replay)
- Community attestation (at least one independent verifier has reproduced results)
- Behavioural signal integration (from Hounfour runtime — does the construct perform as verified in production?)

**Hounfour routing:** premium model pools, full kitchen brigade access.

### Tier Expiry

Certificates are not permanent. Tier status decays:
- **BACKTESTED:** expires after 90 days without a new Theatre run. Falls to UNVERIFIED.
- **PROVEN:** expires after 180 days without production telemetry confirmation. Falls to BACKTESTED.

Expiry ensures constructs that update without recalibration don't retain stale trust signals.

---

## Unified Calibration Certificate Schema

One canonical schema covering both Product Theatre (replay) and Market Theatre (RLMF) outputs. Resolves drift between Community Oracle spec, Cycle-031 spec, and integration doc.

```python
class CalibrationCertificate(BaseModel):
    # Identity
    certificate_id: UUID
    theatre_id: str
    template_id: str
    construct_id: str                          # the construct under test

    # Criteria and Scores
    criteria: TheatreCriteria                  # structured criteria (IDs + human rubric + weights)
    scores: dict[str, float]                   # keys are criteria_ids, values are numerical scores
    composite_score: float                     # weighted aggregate per criteria weights

    # Calibration Metrics (populated where applicable)
    precision: Optional[float]                 # from Community Oracle pattern
    recall: Optional[float]                    # from Community Oracle pattern
    reply_accuracy: Optional[float]            # from Community Oracle pattern
    brier_score: Optional[float]               # for probabilistic / Market Theatres
    ece: Optional[float]                       # Expected Calibration Error

    # Evidence
    replay_count: int                          # number of episodes scored
    evidence_bundle_hash: str                  # SHA-256 of the evidence bundle
    ground_truth_hash: str                     # SHA-256 of the ground truth dataset

    # Reproducibility Pins
    construct_version: str                     # exact commit hash of construct under test
    construct_chain_versions: Optional[dict[str, str]]  # for compositional: {construct_id: commit_hash}
    scorer_version: str                        # scorer model/version
    methodology_version: str                   # verification methodology version
    dataset_hash: str                          # SHA-256 of replay dataset

    # Trust
    verification_tier: VerificationTier        # UNVERIFIED / BACKTESTED / PROVEN
    commitment_hash: str                       # the Theatre's commitment hash (for third-party verification)

    # Timestamps
    issued_at: datetime
    expires_at: datetime                       # per tier expiry rules
    theatre_committed_at: datetime
    theatre_resolved_at: datetime

    # Hounfour Integration
    ground_truth_source: str                   # enum: GITHUB_API, CI_CD, PROVENANCE_JSONL, etc.
    execution_path: str                        # "replay" or "market"
```

This schema supports:
- Community Oracle metrics (`precision`, `recall`, `reply_accuracy`)
- Domain-specific criteria vectors (`scores` keyed by `criteria_ids`)
- Probabilistic calibration (`brier_score`, `ece`)
- Full reproducibility (`construct_version`, `scorer_version`, `dataset_hash`)
- Compositional chain tracking (`construct_chain_versions`)
- Hounfour routing integration (`verification_tier`, `ground_truth_source`)

---

## Evidence Bundle Format

Every Theatre produces an evidence bundle — the auditable artefact that backs the calibration certificate. Without a standardised bundle, PROVEN claims are unverifiable.

### Directory Layout

```
evidence_bundle_{theatre_id}/
├── manifest.json              # bundle metadata, file inventory, hashes
├── template.json              # the committed Theatre Template (canonical JSON)
├── commitment_receipt.json    # commitment hash + version pins + dataset hashes
├── ground_truth/
│   ├── dataset.jsonl          # ground truth episodes (hash-verified against commitment)
│   └── gold_labels.jsonl      # independent label set (if applicable, e.g., Observer)
├── invocations/
│   ├── episode_001.json       # OracleAdapter request + response for each episode
│   ├── episode_002.json
│   └── ...
├── scores/
│   ├── per_episode.jsonl      # per-episode scoring breakdown (criteria_id → score)
│   └── aggregate.json         # final aggregated scores, composite score, tier assignment
├── certificate.json           # the issued CalibrationCertificate
└── audit_trail.jsonl          # timestamped log of all state transitions and operations
```

### manifest.json Required Fields

```python
class EvidenceBundleManifest(BaseModel):
    bundle_id: str                          # UUID
    theatre_id: str
    commitment_hash: str
    bundle_hash: str                        # SHA-256 of all files in bundle (excluding manifest itself)
    file_inventory: list[FileEntry]         # path, size_bytes, sha256 for each file
    created_at: datetime
    methodology_version: str
    construct_version: str
    scorer_version: str
```

### Minimum Required Files

For a certificate to be valid, the evidence bundle must contain at minimum: `manifest.json`, `template.json`, `commitment_receipt.json`, at least one file in `ground_truth/`, at least one file in `invocations/`, `scores/aggregate.json`, and `certificate.json`. Bundles missing any required file are flagged as incomplete and the certificate is downgraded to UNVERIFIED regardless of scores.

---

## OracleAdapter Invocation Contract

The OracleAdapter interface standardises how Theatres invoke constructs. A consistent request/response envelope ensures Soju's constructs integrate without per-construct wiring.

### Request Envelope

```python
class OracleInvocationRequest(BaseModel):
    invocation_id: str                      # UUID, unique per episode
    theatre_id: str
    episode_id: str                         # ground truth episode identifier
    construct_id: str                       # the construct being invoked
    construct_version: str                  # pinned commit hash
    input_data: dict                        # episode-specific input payload (schema varies by template)
    metadata: InvocationMetadata

class InvocationMetadata(BaseModel):
    timeout_seconds: int = 30               # max time for construct response
    retry_policy: RetryPolicy = RetryPolicy(max_retries=2, backoff_seconds=5)
    deterministic: bool = False             # if True, construct must produce identical output for identical input
    sanitised: bool = True                  # if True, input_data has been injection-sanitised
    invoked_at: datetime
```

### Response Envelope

```python
class OracleInvocationResponse(BaseModel):
    invocation_id: str                      # matches request
    construct_id: str
    construct_version: str
    output_data: dict                       # construct's response payload
    latency_ms: int                         # wall-clock response time
    status: InvocationStatus                # SUCCESS | TIMEOUT | ERROR | REFUSED
    error_detail: Optional[str]             # populated on non-SUCCESS status
    responded_at: datetime

class InvocationStatus(str, Enum):
    SUCCESS = "success"
    TIMEOUT = "timeout"
    ERROR = "error"
    REFUSED = "refused"                     # construct declined to process (e.g., input outside domain)
```

### Error Handling

- **TIMEOUT:** episode scored as missing (counts against recall/coverage metrics)
- **ERROR:** episode scored as missing, error logged in audit trail
- **REFUSED:** episode excluded from scoring (does not count for or against), logged with reason
- **Repeated failures:** if > 20% of episodes fail, Theatre transitions to SETTLING with partial results and certificate is flagged as incomplete (caps tier at UNVERIFIED)

### Adapter Implementations

| Adapter | Transport | Use Case |
|---------|-----------|----------|
| `HTTPOracleAdapter` | HTTP POST to construct endpoint | Production — Soju's constructs run as services |
| `LocalOracleAdapter` | Subprocess invocation | Development — constructs running locally |
| `MockOracleAdapter` | In-memory predefined responses | Unit tests and CI only — **never for certificate generation** |

All adapters implement the same `invoke(request: OracleInvocationRequest) → OracleInvocationResponse` interface. Adapter type and version are recorded in the evidence bundle.

---

## Constraint Yielding Gate

**Hard rule:** only BACKTESTED or PROVEN constructs are eligible for constraint yielding (skipping Loa's quality gates). An UNVERIFIED construct declaring `review: skip` in its manifest MUST be treated as `review: full` by the Loa framework and Hounfour routing layer.

This is not a suggestion — it is a framework-level enforcement. The integration seam in `expertise.yaml`:

```yaml
domains:
  - name: "Design Systems"
    depth: 5
    verified:
      tier: UNVERIFIED    # ← this means review: skip is IGNORED
```

Loa/Hounfour routing logic:

```python
if construct.verified.tier == "UNVERIFIED":
    effective_review = "full"  # override any declared skip
elif construct.verified.tier in ("BACKTESTED", "PROVEN"):
    effective_review = construct.declared_review  # honour declared preference
```

This ensures that unverified constructs cannot bypass quality gates regardless of their self-declared capabilities. The automated scan PDF cannot grant itself audit status.

## Deliverables

### Utilities

0. **`canonical_json()` utility function**
   - Single function used by all hash computations — never raw `json.dumps()`
   - Implements RFC 8785 rules as specified in Canonical JSON Rules section
   - Comprehensive tests: key ordering, float normalisation, null handling, nested objects, round-trip stability

### Core Engine (Python, Pydantic v2)

1. **Theatre class**
   - Constructor: takes validated Theatre Template JSON
   - `commit()` → hashes full canonical template JSON + version pins + dataset hashes, freezes all parameters, transitions to COMMITTED
   - `activate()` → begins execution (replay invocation or market opening), transitions to ACTIVE
   - `settle(ground_truth)` → ingests ground truth, runs resolution programme, transitions to SETTLING → RESOLVED
   - `archive()` → generates RLMF export, issues calibration certificate, transitions to ARCHIVED
   - State tracking — invalid transitions raise errors

2. **TheatreTemplate model (Pydantic v2)**
   - Validates against `echelon_theatre_schema.json` (extended)
   - `execution_path`: enum (`replay` | `market`)
   - `criteria`: TheatreCriteria (structured IDs + human rubric + weights)
   - `resolution_programme`: ordered oracle step sequence with version pins
   - `version_pins`: dict mapping construct IDs to exact commit hashes
   - `dataset_hashes`: dict mapping dataset names to SHA-256 hashes
   - `scorer_pins`: scorer model ID + version
   - For Market Theatres: `lmsr_config`, `paradox_thresholds`, `data_sources`
   - For Product Theatres: `ground_truth_source`, `construct_under_test`, `replay_data_path`

3. **ProductTheatreTemplate** (extends TheatreTemplate)
   - `execution_path` fixed to `replay`
   - `ground_truth_source`: enum (GITHUB_API, CI_CD, PROVENANCE_JSONL, DETERMINISTIC_COMPUTATION)
   - `construct_under_test`: str (construct identifier)
   - `construct_chain`: Optional[list[str]] (for compositional Theatres — ordered construct IDs)
   - `replay_data_path`: str (path to ground truth dataset)
   - `gold_label_set`: Optional[str] (path to independent label set for classification verification)
   - Validation: dataset hash must be verifiable, construct version pin required

4. **MarketTheatreTemplate** (extends TheatreTemplate)
   - `execution_path` fixed to `market`
   - `lmsr_config`: LMSR parameter reference (liquidity `b`, fee schedule)
   - `fork_definitions`: list of fork points with outcome labels and trigger conditions
   - `osint_sources`: list of committed data source references
   - `corroboration_minimum`: int (minimum independent sources, default 2)
   - `paradox_thresholds`: Logic Gap and stability trigger values
   - Validation: fork point outcomes must be exhaustive and mutually exclusive

5. **ReplayEngine class** (Product Theatre execution)
   - `run(theatre, oracle_adapter)` → iterates through ground truth episodes, invokes real construct via OracleAdapter, captures outputs, scores per criteria
   - Supports HTTP adapter (remote construct endpoint) and local adapter (subprocess invocation)
   - Each episode produces a scored result with per-criterion breakdown
   - Aggregates across episodes into final scores
   - Handles timeouts, retries, and error states per committed policy

6. **OracleAdapter interface**
   - `invoke(input_data) → OracleResponse`: call construct with episode input, capture output
   - `HTTPOracleAdapter`: calls construct via HTTP endpoint (real remote invocation)
   - `LocalOracleAdapter`: calls construct via local subprocess
   - `MockOracleAdapter`: returns predefined responses (unit tests and CI only — never for certificate generation)
   - Adapter version tracked and committed

7. **CommitmentReceipt model (Pydantic v2)**
   - `theatre_id`: str
   - `commitment_hash`: str (SHA-256 of full canonical template + version pins + dataset hashes)
   - `parameters_snapshot`: frozen canonical template JSON
   - `version_pins`: dict (construct IDs → commit hashes)
   - `dataset_hashes`: dict (dataset names → SHA-256)
   - `scorer_pins`: dict (scorer ID → version)
   - `escrowed_capital`: Optional[float] (Market Theatres only: `b · ln(n)` + fees)
   - `committed_at`: datetime

8. **ResolutionStateMachine class**
   - Accepts pre-committed oracle programme sequence
   - Each step: construct ID + version pin + input specification + expected output type
   - Supports branching: committed escalation paths if step fails
   - Supports pre-committed HITL steps with rubric, identity separation, and scoring scale
   - Produces `ResolutionResult` with winning outcome / scores, full audit trail

9. **CalibrationCertificate model** — as specified in Unified Certificate Schema above

10. **TierAssigner class**
    - `assign(certificate, theatre_history) → VerificationTier`
    - Implements v0 tier rules (UNVERIFIED / BACKTESTED / PROVEN)
    - Checks replay count, reproducibility pins, time-in-production, attestation count
    - Enforces expiry rules (90 days BACKTESTED, 180 days PROVEN)

11. **EvidenceBundleManifest model (Pydantic v2)** — as specified in Evidence Bundle Format section
    - Directory layout builder: generates compliant evidence bundle from Theatre run data
    - Bundle hash computation: SHA-256 of all files excluding manifest
    - File inventory generation with per-file hashes
    - Validation: verify minimum required files present, flag incomplete bundles

12. **OracleInvocationRequest / OracleInvocationResponse models (Pydantic v2)** — as specified in OracleAdapter Invocation Contract section
    - Standardised request/response envelope for all construct invocations
    - InvocationStatus enum (SUCCESS, TIMEOUT, ERROR, REFUSED)
    - RetryPolicy model (max_retries, backoff_seconds)
    - Error handling rules: > 20% failure rate caps tier at UNVERIFIED

13. **ConstraintYieldingGate**
    - Enforcement function: `effective_review(construct) → "full" | declared_review`
    - UNVERIFIED constructs always resolve to `review: full` regardless of manifest declaration
    - BACKTESTED+ constructs honour their declared review preference
    - Hard rule — no override, no exceptions

### API Layer (FastAPI)

11. **Endpoints** (integrate with existing FastAPI backend)
    - `POST /theatres` — create Theatre from template JSON (validates, returns DRAFT state)
    - `POST /theatres/{id}/commit` — generate commitment hash, freeze parameters, transition to COMMITTED
    - `POST /theatres/{id}/run` — execute Replay Theatre (invoke constructs, score, settle) — full lifecycle in one call for Product Theatres
    - `GET /theatres/{id}` — current state, parameters, execution progress
    - `GET /theatres/{id}/commitment` — commitment receipt with full parameter snapshot and version pins
    - `POST /theatres/{id}/settle` — manually trigger settlement (Market Theatres, when ground truth available)
    - `GET /theatres/{id}/certificate` — calibration certificate (only after RESOLVED)
    - `GET /theatres/{id}/replay` — full Theatre replay data for RLMF export
    - `GET /templates` — list available Theatre templates
    - `GET /templates/{template_id}` — template schema and metadata
    - `GET /certificates/{certificate_id}` — certificate by ID (for Hounfour integration)
    - `GET /certificates?construct_id={id}` — certificates for a given construct (for routing decisions)

### Test Suite

12. **Unit tests**
    - Theatre state machine: valid transitions succeed, invalid paths raise errors
    - Commitment hash determinism: same inputs → same hash
    - Parameter immutability: modification after COMMITTED raises error
    - Criteria validation: criteria_ids must be non-empty, scores keys must match criteria_ids
    - Template validation: valid JSON passes, invalid JSON rejected with clear errors
    - Tier assignment: verify rules produce correct tier for edge cases
    - Certificate expiry: verify tier decay after configured intervals
    - Canonical JSON: key ordering, float normalisation, null handling, nested objects, round-trip stability
    - Evidence bundle: minimum required files check, bundle hash excludes manifest, incomplete bundles flagged
    - OracleAdapter: timeout handling, retry policy, > 20% failure rate caps tier, REFUSED episodes excluded from scoring
    - Constraint yielding gate: UNVERIFIED always → `review: full`, BACKTESTED+ honours declared preference

13. **Integration tests — Replay Engine (real construct invocation)**
    - **PRODUCT_OBSERVER_V1:** create → commit → run with real OracleAdapter → score against provenance records (deterministic layer) + gold label set (labelled layer) → generate certificate with `source_fidelity`, `signal_classification`, `canvas_enrichment_freshness` scores → verify tier assignment
    - **PRODUCT_EASEL_V1:** create → commit (with 3-construct chain version pins) → run compositional chain → score TDR propagation → generate certificate with `vocabulary_adherence`, `tdr_propagation_fidelity`, `downstream_compliance` scores → verify compositional version tracking
    - **PRODUCT_CARTOGRAPH_V1:** create → commit → run deterministic validation → generate certificate revealing stub skills (low scores on 3/4 dimensions) → verify UNVERIFIED tier assignment
    - **Reproducibility test:** run same Theatre twice with same pins → identical certificate scores

14. **Integration tests — Market Theatre (schema only)**
    - Validate MILITARY, COMMODITY, MARITIME, etc. template schemas pass Theatre Template validator
    - Corroboration minimum enforcement: templates with < 2 independent sources rejected
    - Fork point validation: outcomes must be exhaustive and mutually exclusive
    - (No execution tests — Market Theatre execution requires Cycle-030 LMSR engine)

15. **Adversarial baseline tests (v0)**
    - Holdout split: Theatre must support configurable train/test split on ground truth dataset
    - Injection sanitisation: ground truth text inputs sanitised before passing to construct
    - Deterministic heuristic scoring alongside any LLM-based scoring (detect style hacks vs factual accuracy)

---

## What This Cycle Does NOT Include

- No LMSR market engine or trading logic (Cycle-030)
- No OSINT data ingestion or real geopolitical data feeds (Cycle-032)
- No agent trading logic or archetypes (Cycle-033)
- No Paradox Engine or Logic Gap calculation (Cycle-034)
- No frontend / UI (Cycle-035)
- No on-chain contracts or blockchain commitment hash publication
- No VRF integration
- No token economics

This builds the container, the Replay Engine for Product Theatres, and the unified certificate schema. Market Theatre execution plugs in when Cycle-030 delivers the LMSR engine.

---

## Existing Code to Reference

- **`echelon_theatre_schema.json`** in `docs/schemas/` — the JSON schema that Theatre Templates validate against. Needs extension for: `execution_path`, `criteria` (structured), `version_pins`, `dataset_hashes`, `ground_truth_source`, `construct_under_test`, `construct_chain`, `gold_label_set`, `corroboration_minimum`.
- **`echelon_rlmf_schema.json`** in `docs/schemas/` — the export schema that ARCHIVED Theatres produce.
- **System Bible v10** §II (Market Specification Language), §IV (Resolution & Settlement), §VI (Commitment Protocol), §X (Engagement & Timeline Creation).
- **Cycle-027 output:** Community Oracle Verification Pipeline — the 4-stage pipeline (Ground Truth Ingestion → Oracle Invocation → Scoring → Certification) is the existing pattern. The OracleAdapter interface and scoring logic from Cycle-027 should be reused and formalised.
- **Cycle-028 output:** Backend wiring — existing FastAPI endpoints for verification pipeline. Extend, don't duplicate.
- **Echelon#34** (AITOBIAS04/Echelon) — Soju's three Product Theatre templates.
- **Hounfour × Echelon Integration document** — verification tier system, certificate-as-access-key model, routing implications.
- **OSINT Appendix v3.1** — corroboration requirements for Market Theatre templates.

---

## Schema Extension Notes

The existing `echelon_theatre_schema.json` needs the following extensions:

1. **`execution_path`** — enum: `replay` | `market`. Determines which ACTIVE behaviour applies.
2. **`criteria`** — structured object with `criteria_ids` (list[str]), `criteria_human` (str), `weights` (dict). Replaces any freeform string representation.
3. **`version_pins`** — dict mapping construct IDs to exact commit hashes. Required for reproducibility.
4. **`dataset_hashes`** — dict mapping dataset names to SHA-256 hashes.
5. **`scorer_pins`** — scorer model ID + version.
6. **`ground_truth_source`** enum — GITHUB_API, CI_CD, PROVENANCE_JSONL, DETERMINISTIC_COMPUTATION, OSINT_FEED.
7. **`construct_under_test`** — string identifier for the primary construct being verified.
8. **`construct_chain`** — optional ordered list of construct IDs for compositional verification.
9. **`gold_label_set`** — optional path/reference for independent human-labelled validation data.
10. **`corroboration_minimum`** — integer, minimum independent sources for resolution (Market Theatres, per OSINT Appendix v3.1).
11. **`template_family` enum extension** — add PRODUCT and GEOPOLITICAL alongside existing simulation-oriented values (2D-DISCRETE, 3D-DYNAMIC, etc.).
12. **`hitl_steps`** — optional list of pre-committed human-in-the-loop step specifications (rubric, identity rules, scoring scale).

All extensions must be backward-compatible with existing template definitions.

---

## Success Criteria

1. Theatre state machine correctly enforces all valid transitions and rejects invalid ones
2. Commitment hash computed over full canonical template JSON + version pins + dataset hashes — deterministic and third-party verifiable
3. No parameter modifiable after commitment (immutability enforced at model level)
4. **All three Product Theatre test fixtures (Observer, Easel, Cartograph) complete full lifecycle with real OracleAdapter invocation** — not stubs
5. Observer fixture includes both deterministic (hash-chain) and labelled (gold set) verification layers
6. Easel fixture includes 3-construct chain version pinning in commitment hash
7. Cartograph fixture correctly reveals stub skills through low dimension scores
8. Calibration certificates generated with structured criteria (IDs as keys in scores dict)
9. Tier assignment follows v0 rules and produces correct tier for each fixture
10. Certificate expiry rules enforced (90-day BACKTESTED, 180-day PROVEN)
11. Geopolitical Theatre template schemas validate correctly (schema only, no execution)
12. Unified certificate schema works for both Product (replay) and Market (RLMF) outputs
13. Reproducibility: same Theatre with same pins produces identical scores across runs
14. `POST /theatres/{id}/run` endpoint executes full Product Theatre lifecycle in one call
15. `canonical_json()` utility produces identical output across Python versions and platforms for the same input
16. Evidence bundle generated for every completed Theatre, passes minimum-required-files validation
17. OracleAdapter invocation contract enforced: all construct calls use standardised request/response envelope
18. Constraint yielding gate enforced: UNVERIFIED + `review: skip` always resolves to `review: full`
