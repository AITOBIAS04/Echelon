# PRD: Theatre Template Engine

> Cycle-031 | Author: Claude (plan-and-analyze) | Date: 2026-02-20
> UK British English throughout.

---

## 1. Problem Statement

AI constructs in the Constructs Network (Soju/Hounfour) declare expertise without structured proof. An unverified construct claiming `review: skip` is the equivalent of an automated security scan producing a thick PDF — the sensation of competence without substance. Echelon's existing verification pipeline (Cycles 027-029) demonstrates the pattern works: ingest ground truth, invoke construct, score output, issue certificate. But it lacks a formal lifecycle container — no commitment protocol, no immutability guarantees, no structured criteria, no version pinning, no evidence bundles.

The Theatre is that container. It formalises the verification lifecycle into an auditable, reproducible state machine where every parameter is committed before execution begins and no rules change after commitment.

> Sources: echelon_cycle_031.md:1-27, echelon_platform_roadmap.md:9-17

---

## 2. Vision

Build the Theatre as a state machine — the container within which all Echelon verification activity occurs. A Theatre is created from a Theatre Template, passes through an immutable commitment protocol, and settles deterministically when ground truth is revealed.

**Two distinct execution paths ship in this cycle:**

- **Replay Theatres (Product Theatres):** commit → invoke real construct via OracleAdapter → score against ground truth → issue calibration certificate. No LMSR markets, no agents, no trading. This is what Soju needs now.
- **Market Theatres (Geopolitical Theatres):** full LMSR lifecycle. Schema validation only this cycle — execution requires Cycle-030 (LMSR engine).

Both share the commitment protocol, template validation, resolution engine, and certificate output. The execution path diverges at the ACTIVE state.

> Sources: echelon_cycle_031.md:11-18, echelon_platform_roadmap.md:173-195

---

## 3. Goals & Success Criteria

### Primary Goals

| # | Goal | Measure |
|---|------|---------|
| G1 | Theatre state machine enforces lifecycle | All valid transitions succeed; all invalid transitions raise errors |
| G2 | Commitment protocol guarantees immutability | No parameter modifiable after COMMITTED; hash deterministic and third-party verifiable |
| G3 | Product Theatre replay engine works end-to-end | All three test fixtures (Observer, Easel, Cartograph) complete full lifecycle with real OracleAdapter invocation |
| G4 | Unified calibration certificate schema | One schema covers both Product (replay) and Market (RLMF) outputs |
| G5 | Verification tier assignment is deterministic | v0 rules correctly assign UNVERIFIED / BACKTESTED / PROVEN based on evidence |
| G6 | Canonical JSON is reproducible | `canonical_json()` produces identical output across Python versions for same input |
| G7 | Evidence bundles are auditable | Every completed Theatre produces a compliant evidence bundle |
| G8 | Constraint yielding gate enforced | UNVERIFIED + `review: skip` always resolves to `review: full` |

### Quantitative Success Criteria

1. Theatre state machine correctly enforces all 5 valid transitions and rejects all invalid paths
2. Commitment hash: same inputs → same hash (deterministic, 100% reproducibility)
3. Observer fixture: deterministic layer (hash-chain) + labelled layer (gold set) both produce scores
4. Easel fixture: 3-construct chain version pinning included in commitment hash
5. Cartograph fixture: correctly reveals stub skills through low dimension scores
6. `POST /theatres/{id}/run` executes full Product Theatre lifecycle in one API call
7. Evidence bundle passes minimum-required-files validation for every completed Theatre
8. Reproducibility test: same Theatre with same pins → identical certificate scores across runs

> Sources: echelon_cycle_031.md:710-730

---

## 4. User & Stakeholder Context

### Primary User: Construct Creator (Soju)

Soju builds AI constructs (Observer, Easel, Cartograph) and needs to prove they work. He has:
- Real constructs with HTTP endpoints or local processes
- Engineering ground truth that already exists (GitHub diffs, provenance records, CI output)
- Three concrete Product Theatre templates filed on Echelon#34

**User Journey:**
1. Creates a Theatre from a template JSON → validates against schema, enters DRAFT
2. Configures parameters (execution path, criteria, version pins, dataset hashes)
3. Commits the Theatre → hash generated, all parameters frozen
4. Runs the Theatre → construct invoked against ground truth episodes, scored
5. Retrieves calibration certificate → structured scores per criteria_id, verification tier
6. Certificate gates construct access to Hounfour model routing tiers

### Secondary User: Hounfour Routing Layer

Consumes calibration certificates to make routing decisions:
- UNVERIFIED → restricted to baseline model pools, `review: skip` ignored
- BACKTESTED → mid-tier brigade routing
- PROVEN → premium model pools, full kitchen brigade access

### Tertiary User: Third-Party Verifier

Can independently recompute commitment hashes and replay Theatres to verify certificates.

> Sources: echelon_cycle_031.md:192-248, echelon_platform_roadmap.md:23-59

---

## 5. Functional Requirements

### FR-1: Theatre Lifecycle State Machine

The Theatre progresses through six irreversible states:

```
DRAFT → COMMITTED → ACTIVE → SETTLING → RESOLVED → ARCHIVED
```

| State | Entry Condition | What Happens | Exit Condition |
|-------|-----------------|--------------|----------------|
| DRAFT | Template validated against schema | Creator configures parameters | Creator triggers commitment |
| COMMITTED | Commitment hash published | All parameters frozen. Replay: dataset hash verified. Market: capital escrowed. | Execution begins |
| ACTIVE | Execution opens | Replay: OracleAdapter invoked per episode. Market: LMSR trading (future). | Terminal condition reached |
| SETTLING | Resolution triggered | Resolution state machine executes. Ground truth compared against outputs. | Resolution completes |
| RESOLVED | Settlement computed | Scores determined. Tier assigned. Certificate issued. | Redemption window opens |
| ARCHIVED | Redemption complete or timeout | Full replay data preserved. RLMF export generated. Certificate finalised. | Terminal — immutable |

**Invariant:** After COMMITTED, no parameter changes are permitted. The commitment hash covers the full canonical template JSON + version pins + dataset hashes.

> Sources: echelon_cycle_031.md:32-48

### FR-2: Commitment Protocol

The commitment hash is computed over the **full canonicalised template JSON** plus external version pins and dataset hashes:

```python
commitment_hash = SHA-256(
    canonical_json({
        "dataset_hashes": dataset_hashes,
        "template": full_template,
        "version_pins": version_pins
    })
)
```

Canonical JSON follows RFC 8785:
- Keys sorted lexicographically (Unicode code point order)
- No whitespace between tokens
- Integers as-is, floats with no trailing zeroes, no positive sign prefix
- `null` values included (not omitted)
- Arrays preserve insertion order
- Recursive lexicographic sorting at every nesting level

Implementation: a single `canonical_json()` utility function used by **all** hash computations. Never raw `json.dumps()`.

**What Gets Committed:** Full template JSON, execution path, structured criteria, resolution programme, version pins (construct commit hashes), dataset hashes (SHA-256), scorer pins, HITL steps (if any). For Market Theatres: LMSR config, OSINT sources, paradox thresholds.

> Sources: echelon_cycle_031.md:53-108

### FR-3: Structured Criteria

Criteria defines what a Theatre measures. It must be structured and hash-stable.

```python
class TheatreCriteria(BaseModel):
    criteria_ids: list[str]        # deterministic keys
    criteria_human: str            # freeform rubric for human consumption
    weights: dict[str, float]      # per-criterion weights, keys match criteria_ids, values sum to 1.0
```

The `criteria_ids` become canonical keys in the certificate `scores` dict. They are domain-specific and human-defined — Observer measures `source_fidelity`, Cartograph measures `hex_grid_accuracy`. The engine must not impose universal metrics.

> Sources: echelon_cycle_031.md:111-145

### FR-4: Two Theatre Families

#### Replay Theatres (Product Theatres) — Full Implementation

Execution flow:
1. Validate template against schema
2. COMMIT: hash full template + version pins + dataset hashes
3. ACTIVE: for each episode in ground truth dataset, invoke real construct via OracleAdapter, capture output, score per committed criteria
4. SETTLING: aggregate scores across all episodes
5. RESOLVED: compute calibration metrics, assign verification tier
6. ARCHIVED: issue certificate, generate RLMF-compatible export

**Key requirement:** Product Theatre test fixtures must call real constructs through the OracleAdapter interface. Mock responses permitted only for unit tests and CI, never for certificate generation.

#### Market Theatres (Geopolitical Theatres) — Schema Only

Template validation and schema definition only this cycle. Eight geopolitical families defined (MILITARY, COMMODITY, MARITIME, DIPLOMATIC, INFRASTRUCTURE, FX, ENERGY, CORPORATE). No execution — requires Cycle-030 LMSR engine.

> Sources: echelon_cycle_031.md:150-266

### FR-5: OracleAdapter Invocation Contract

Standardised request/response envelope for all construct invocations:

- **Request:** invocation_id, theatre_id, episode_id, construct_id, construct_version, input_data, metadata (timeout, retry policy, deterministic flag, sanitisation flag)
- **Response:** invocation_id, construct_id, construct_version, output_data, latency_ms, status (SUCCESS/TIMEOUT/ERROR/REFUSED), error_detail, responded_at

Error handling:
- TIMEOUT/ERROR: episode scored as missing (counts against recall/coverage)
- REFUSED: episode excluded from scoring, logged with reason
- \>20% failure rate: Theatre transitions to SETTLING with partial results, certificate capped at UNVERIFIED

Three adapter implementations: `HTTPOracleAdapter`, `LocalOracleAdapter`, `MockOracleAdapter` (CI only).

> Sources: echelon_cycle_031.md:418-478

### FR-6: Resolution State Machine

Accepts pre-committed oracle programme sequence. Each step: construct ID + version pin + input specification + expected output type. Supports:
- Branching: committed escalation paths if step fails
- Pre-committed HITL steps with rubric, identity separation rules, and scoring scale
- Produces `ResolutionResult` with winning outcome / scores, full audit trail

> Sources: echelon_cycle_031.md:578-583

### FR-7: Unified Calibration Certificate

One canonical schema covering both Product Theatre (replay) and Market Theatre (RLMF) outputs:

**Identity:** certificate_id, theatre_id, template_id, construct_id
**Criteria:** structured criteria (IDs + rubric + weights), scores dict (criteria_ids → float), composite_score
**Calibration:** precision, recall, reply_accuracy, brier_score, ece (all optional, populated where applicable)
**Evidence:** replay_count, evidence_bundle_hash, ground_truth_hash
**Reproducibility:** construct_version, construct_chain_versions (compositional), scorer_version, methodology_version, dataset_hash
**Trust:** verification_tier, commitment_hash
**Timestamps:** issued_at, expires_at, theatre_committed_at, theatre_resolved_at
**Integration:** ground_truth_source, execution_path

> Sources: echelon_cycle_031.md:311-369

### FR-8: Verification Tier Rules (v0)

| Tier | Requirements | Hounfour Routing | Expiry |
|------|-------------|------------------|--------|
| UNVERIFIED | <50 replays OR missing pins OR incomplete evidence | Baseline pools; `review:skip` → `review:full` | N/A |
| BACKTESTED | ≥50 replays + full pins + published scores + verifiable hash + no disputes | Mid-tier brigade | 90 days without new run |
| PROVEN | BACKTESTED + ≥3 months consecutive + production telemetry + community attestation | Premium pools, full kitchen brigade | 180 days without telemetry |

> Sources: echelon_cycle_031.md:268-307

### FR-9: Evidence Bundle

Every Theatre produces an evidence bundle — the auditable artefact backing the certificate:

```
evidence_bundle_{theatre_id}/
├── manifest.json              # bundle metadata, file inventory, hashes
├── template.json              # committed Theatre Template (canonical JSON)
├── commitment_receipt.json    # commitment hash + version pins + dataset hashes
├── ground_truth/
│   ├── dataset.jsonl          # ground truth episodes
│   └── gold_labels.jsonl      # independent label set (if applicable)
├── invocations/
│   ├── episode_001.json       # request + response per episode
│   └── ...
├── scores/
│   ├── per_episode.jsonl      # per-episode scoring breakdown
│   └── aggregate.json         # final scores, composite, tier
├── certificate.json           # issued CalibrationCertificate
└── audit_trail.jsonl          # timestamped state transitions
```

Minimum required files: manifest.json, template.json, commitment_receipt.json, ≥1 ground_truth file, ≥1 invocation file, scores/aggregate.json, certificate.json. Missing files → certificate downgraded to UNVERIFIED.

> Sources: echelon_cycle_031.md:372-414

### FR-10: Constraint Yielding Gate

Hard rule — no override, no exceptions:
- UNVERIFIED constructs: `review: skip` always resolves to `review: full`
- BACKTESTED/PROVEN constructs: honour declared review preference

Enforced at framework level and Hounfour routing layer.

> Sources: echelon_cycle_031.md:481-504

### FR-11: API Endpoints

Integrate with existing FastAPI backend (`backend/api/`):

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/v1/theatres` | Create Theatre from template JSON (validates, returns DRAFT) | Required |
| POST | `/api/v1/theatres/{id}/commit` | Generate commitment hash, freeze parameters | Required |
| POST | `/api/v1/theatres/{id}/run` | Execute full Product Theatre lifecycle | Required |
| GET | `/api/v1/theatres/{id}` | Current state, parameters, progress | Required |
| GET | `/api/v1/theatres/{id}/commitment` | Commitment receipt with parameter snapshot | Public |
| POST | `/api/v1/theatres/{id}/settle` | Manual settlement trigger (Market Theatres) | Required |
| GET | `/api/v1/theatres/{id}/certificate` | Calibration certificate (after RESOLVED) | Public |
| GET | `/api/v1/theatres/{id}/replay` | Full replay data for RLMF export | Public |
| GET | `/api/v1/templates` | List available Theatre templates | Public |
| GET | `/api/v1/templates/{template_id}` | Template schema and metadata | Public |
| GET | `/api/v1/certificates/{certificate_id}` | Certificate by ID (Hounfour integration) | Public |
| GET | `/api/v1/certificates?construct_id={id}` | Certificates for a construct | Public |

> Sources: echelon_cycle_031.md:611-624

---

## 6. Technical & Non-Functional Requirements

### NFR-1: Extend, Don't Duplicate

The existing `echelon-verify` package (`verification/src/echelon_verify/`) provides reusable components:

| Component | Path | Action |
|-----------|------|--------|
| `OracleAdapter` (base + HTTP + Python) | `verification/src/echelon_verify/oracle/` | **Reuse** — standardise request/response envelope |
| `ScoringProvider` interface | `verification/src/echelon_verify/scoring/base.py` | **Extend** — create Theatre-aware scorer |
| `VerificationPipeline` | `verification/src/echelon_verify/pipeline.py` | **Compose** — Theatre wraps pipeline |
| `Storage` | `verification/src/echelon_verify/storage.py` | **Reuse** — for evidence bundle persistence |
| `CertificateGenerator` | `verification/src/echelon_verify/certificate/generator.py` | **Extend** — Theatre-specific aggregation |
| `GroundTruthRecord`, `OracleOutput`, `ReplayScore` | `verification/src/echelon_verify/models.py` | **Extend** — add Theatre metadata |
| DB models (VerificationRun, Certificate, ReplayScore) | `backend/database/models.py` | **Create new** — Theatre-specific tables |
| Verification routes | `backend/api/verification_routes.py` | **Don't touch** — create new `/theatres` router |

> Sources: echelon_cycle_031.md:676-685, codebase exploration

### NFR-2: Schema Compatibility

The existing `echelon_theatre_schema_v2.json` already includes most required fields (execution_path, criteria, version_pins, dataset_hashes, product_theatre_config, market_theatre_config, hitl_steps). Extend where needed; maintain backward compatibility with existing template definitions.

### NFR-3: Python & Pydantic v2

All core engine code in Python with Pydantic v2 models. Consistent with existing `echelon-verify` package patterns.

### NFR-4: Performance

- Product Theatre execution is inherently sequential (episodes scored one at a time against real constructs)
- OracleAdapter timeout: configurable per invocation, default 30s
- Retry policy: configurable, default 2 retries with 5s backoff
- \>20% failure rate triggers early SETTLING with partial results

### NFR-5: Security

- No secrets in commitment hashes or evidence bundles
- Dataset hashes verified before execution (tamper detection)
- Construct version pins prevent silent updates between runs
- `MockOracleAdapter` rejected for certificate-generating runs (enforced by engine, not schema)
- Input data sanitised before passing to construct (injection prevention)

---

## 7. Scope & Prioritisation

### In Scope (This Cycle)

1. Theatre lifecycle state machine (6 states, irreversible transitions)
2. Commitment protocol with canonical JSON (RFC 8785) and SHA-256
3. Replay Engine for Product Theatres (real OracleAdapter invocation)
4. Structured criteria (criteria_ids, criteria_human, weights)
5. Unified CalibrationCertificate schema
6. Verification tier rules (v0) with expiry
7. Evidence bundle generation and validation
8. OracleAdapter invocation contract (standardised request/response)
9. Resolution state machine (pre-committed oracle programmes)
10. Constraint yielding gate enforcement
11. FastAPI endpoints for Theatre CRUD and execution
12. Market Theatre template schema validation (8 geopolitical families)
13. Test fixtures: PRODUCT_OBSERVER_V1, PRODUCT_EASEL_V1, PRODUCT_CARTOGRAPH_V1
14. CommitmentReceipt model
15. TierAssigner with expiry rules
16. `canonical_json()` utility with comprehensive tests
17. Adversarial baseline tests (holdout split, injection sanitisation)

### Out of Scope

- No LMSR market engine or trading logic (Cycle-030)
- No OSINT data ingestion or real geopolitical data feeds (Cycle-032)
- No agent trading logic or archetypes (Cycle-033)
- No Paradox Engine or Logic Gap calculation (Cycle-034)
- No frontend / UI (Cycle-035)
- No on-chain contracts or blockchain commitment hash publication
- No VRF integration
- No token economics
- No Market Theatre execution (schema validation only)

> Sources: echelon_cycle_031.md:660-673

---

## 8. Risks & Dependencies

### Technical Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Canonical JSON platform divergence | Commitment hashes differ across Python versions | Comprehensive round-trip tests; pin Python version in CI; normalise floats before serialisation |
| OracleAdapter latency for real constructs | Slow Theatre execution for large ground truth sets | Configurable timeout + retry; progress callbacks; >20% failure cap at UNVERIFIED |
| Compositional chain complexity (Easel) | 3-construct version pinning is complex | Each construct version explicitly committed; chain order matters; test with all three fixtures |
| Schema backward compatibility | Existing templates may break | All extensions are additive; conditional validation by execution_path |
| Evidence bundle storage growth | Large datasets produce large bundles | Hash references instead of inline data where possible; ground_truth_ref URI option in RLMF schema |

### Dependencies

| Dependency | Status | Impact if Missing |
|------------|--------|-------------------|
| `echelon-verify` package (Cycle-027) | Exists on `feature/community-oracle-verification` | OracleAdapter, ScoringProvider, pipeline patterns — critical foundation |
| Theatre schema v2 (`docs/schemas/echelon_theatre_schema_v2.json`) | Exists | Template validation target |
| RLMF schema v2 (`docs/schemas/echelon_rlmf_schema_v2.json`) | Exists | Export format |
| FastAPI backend (Cycle-028) | Exists | API mounting, auth, SQLAlchemy patterns |
| System Bible v11 (§II, §IV, §VI) | Exists | Architectural reference |
| Soju's three Product Theatre templates (Echelon#34) | External, specified in spec | Test fixtures |

### Known Issues (from Soju's Research Agents)

Three implementation gaps in `feature/community-oracle-verification`:
1. `scoring/base.py` — ABC interface may need alignment with Theatre scoring dimensions
2. Prompt templates — existing v1 prompts are Community Oracle-specific; Theatre needs domain-agnostic prompts
3. CLI argument signature — mismatch with click interface (fix before starting)

> Sources: echelon_platform_roadmap.md:139-147

---

## 9. Test Fixtures

### PRODUCT_OBSERVER_V1

- **Construct:** Observer (user research)
- **Criteria IDs:** `["source_fidelity", "signal_classification", "canvas_enrichment_freshness"]`
- **Ground Truth:** 163 provenance records (append-only JSONL, SHA-256 hash chain)
- **Expected Tier:** PROVEN candidate
- **Two verification layers:** (1) Deterministic — hash-chain integrity, record completeness, timestamp ordering. (2) Labelled — classification accuracy against human-labelled gold set (20-30 records).
- **Version Pins:** Observer commit hash, scorer version, dataset hash

### PRODUCT_EASEL_V1

- **Construct:** Easel (creative direction)
- **Criteria IDs:** `["vocabulary_adherence", "tdr_propagation_fidelity", "downstream_compliance"]`
- **Ground Truth:** TDR records + Artisan `/inscribe` compliance output
- **Expected Tier:** BACKTESTED candidate
- **Compositional chain:** Easel → Artisan → Mint (3 construct versions pinned)
- **HITL provision:** pre-committed rubric step for taste/creative judgement
- **Version Pins:** Easel hash, Artisan hash, Mint hash, scorer version, TDR dataset hash

### PRODUCT_CARTOGRAPH_V1

- **Construct:** Cartograph (spatial accuracy)
- **Criteria IDs:** `["isometric_convention_compliance", "hex_grid_accuracy", "detail_density_adherence"]`
- **Ground Truth:** Deterministic — mathematical validation of spatial computations
- **Expected Tier:** UNVERIFIED (3/4 skills are stubs — verification reveals this)
- **Version Pins:** Cartograph commit hash, scorer version, reference grid dataset hash

> Sources: echelon_cycle_031.md:192-248

---

## 10. Existing Code to Reference

| Resource | Location | Usage |
|----------|----------|-------|
| Theatre schema v2 | `docs/schemas/echelon_theatre_schema_v2.json` | Template validation target |
| RLMF schema v2 | `docs/schemas/echelon_rlmf_schema_v2.json` | Export format |
| System Bible v11 | `docs/core/Echelon_System_Bible_v11.md` | §II, §IV, §VI |
| echelon-verify package | `verification/src/echelon_verify/` | Oracle, Scoring, Pipeline, Storage |
| Verification bridge | `backend/services/verification_bridge.py` | Background task pattern |
| Verification routes | `backend/api/verification_routes.py` | API pattern reference |
| Verification models | `backend/database/models.py` (lines 378-481) | DB model pattern |
| Verification schemas | `backend/schemas/verification.py` | Request/response pattern |

> Sources: echelon_cycle_031.md:676-685, codebase exploration
