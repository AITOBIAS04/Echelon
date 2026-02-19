# PRD: Community Oracle Verification Pipeline

> Cycle: cycle-027 | Source: `loa-grimoire/context/echelon_context.md`
> Grounded: Reality files (2026-02-18), RLMF schema, Real-to-Sim methodology
> Status: Draft

## 1. Problem Statement

AI constructs (agents that claim expertise — code summarization, bug triage, community communication) have no standardized way to prove they work well. A Community Oracle construct ingests code changes and produces audience-facing summaries, but there's no mechanism to answer: *Is the oracle accurate? Does it hallucinate features? Does it miss breaking changes? Are follow-up answers grounded?*

Without verification, construct quality is anecdotal. Users can't compare oracles. Downstream systems (Hounfour model routing, Constructs Network) have no signal for quality-gated access.

> Sources: `loa-grimoire/context/echelon_context.md:9-20`

## 2. Vision

Build the smallest, cheapest, most demonstrable verification slice: score a Community Oracle construct against git repository ground truth, producing a machine-readable calibration certificate. This is Theatre Replay applied to code changes — the same rigour the full Echelon architecture applies to geopolitical incidents, applied here to PRs and commits.

> Sources: `loa-grimoire/context/echelon_context.md:22-26`, `docs/core/Real_to_Sim_Incident_Replay_v1.md` (tiered replay methodology)

## 3. Goals & Success Metrics

### Goals

| # | Goal | Measurable Outcome |
|---|------|--------------------|
| G1 | Ingest git repository ground truth | Extract N historical PRs as structured records via GitHub API |
| G2 | Evaluate oracle output | Pass each PR to oracle construct, capture structured response |
| G3 | Score factual alignment | Produce precision, recall, and reply accuracy per replay (0.0–1.0) |
| G4 | Generate calibration certificate | Aggregate scores across N replays into versioned JSON certificate |
| G5 | Reproducibility | Same oracle + same PRs = consistent scores (within LLM variance) |
| G6 | Dual interface | CLI for manual runs, API for programmatic/automated evaluation |

### Success Criteria

Phase 1 is complete when all six goals are met with:
- Minimum 50 replays for statistical significance (configurable)
- Certificate schema version-controlled and documented
- Process reproducible across runs (score variance < 5% for deterministic oracles)

### Timeline

No fixed deadline. Quality over speed. Ship when the scoring methodology is sound.

## 4. User & Stakeholder Context

### Primary Users

| Persona | Description | Invocation |
|---------|-------------|------------|
| **Construct Developer** | Builds Community Oracle constructs. Wants to verify accuracy before publishing. | CLI: `echelon verify --repo <url> --construct <endpoint>` |
| **Platform Operator** | Runs automated evaluations for construct marketplace quality gates. | API: `POST /api/verification/run` with repo URL + construct config |
| **Evaluator** | Compares multiple oracles against same ground truth for benchmarking. | CLI with `--construct` pointing to different endpoints |

### Stakeholders

- **Constructs Network** (downstream): Calibration certificates attach to construct finnNFT Souls as portable verification
- **Hounfour** (downstream): Verified constructs gate access to higher model routing tiers
- **Grant reviewers** (near-term): Demonstrable verification pipeline supports grant applications

> Sources: `loa-grimoire/context/echelon_context.md:119-127`

## 5. Functional Requirements

### FR-1: Ground Truth Ingestion

Extract historical PRs/commits from a GitHub repository as structured ground truth records.

**Input**: GitHub repository URL (public or with auth token), optional commit range, optional PR count limit

**Output**: Ordered list of `GroundTruthRecord` objects:

```
GroundTruthRecord:
  id: str                    # PR number or commit SHA
  title: str                 # PR title or commit message
  description: str           # PR body or extended commit message
  diff_content: str          # Unified diff
  files_changed: list[str]   # Paths of changed files
  timestamp: datetime        # When merged/committed
  labels: list[str]          # PR labels (if available)
  author: str                # Author login
```

**Acceptance Criteria**:
- Supports GitHub REST API v3 for PR retrieval
- Handles pagination for repos with >100 PRs
- Respects rate limits (with backoff)
- Filters: merged PRs only, optional date range, optional label filter
- Stores ground truth records locally for replay without re-fetching

> Sources: `loa-grimoire/context/echelon_context.md:29-33`

### FR-2: Oracle Invocation

Pass each ground truth record to the oracle construct under test and capture structured output.

**Oracle Adapter Pattern**: Support two invocation modes via adapter interface:

| Mode | How It Works | Config |
|------|-------------|--------|
| **HTTP endpoint** | `POST <url>` with PR data as JSON body, parse JSON response | `type: http`, `url: <endpoint>`, optional headers |
| **Python callable** | Import and call a Python function/class | `type: python`, `module: <dotted.path>`, `callable: <name>` |

**Oracle Output Schema**:

```
OracleOutput:
  summary: str               # The oracle's generated summary
  key_claims: list[str]      # Individual factual claims extracted
  follow_up_response: str    # Response to a generated follow-up question
  metadata: dict             # Any additional oracle output (model used, latency, etc.)
```

**Acceptance Criteria**:
- Adapter interface (`OracleAdapter`) with `invoke(ground_truth: GroundTruthRecord) -> OracleOutput`
- HTTP adapter handles timeouts, retries, error responses
- Python adapter handles import errors, runtime exceptions
- Follow-up question generation: pipeline generates a factual question about the PR and passes it to the oracle for reply accuracy scoring
- Oracle output is captured and stored alongside ground truth for audit

> Sources: `loa-grimoire/context/echelon_context.md:35-40`

### FR-3: Verification Scoring

Score each oracle output against its ground truth source using LLM-based factual alignment.

**Three Metrics** (each 0.0–1.0):

| Metric | What It Measures | Scoring Method |
|--------|-----------------|----------------|
| **Precision** | % of oracle claims supported by source PR | LLM compares each claim against diff. Unsupported claims reduce precision. |
| **Recall** | % of important PR changes surfaced in summary | LLM identifies key changes in diff, checks which appear in summary. Missing changes reduce recall. |
| **Reply Accuracy** | Groundedness of follow-up answer | LLM checks if follow-up response is factually supported by source material. Fabricated details reduce accuracy. |

**Scoring LLM**: Configurable provider (default: Claude via `anthropic` SDK). Scoring prompts are versioned and stored as templates for reproducibility.

**Per-Replay Score Output**:

```
ReplayScore:
  ground_truth_id: str
  precision: float           # 0.0–1.0
  recall: float              # 0.0–1.0
  reply_accuracy: float      # 0.0–1.0
  claims_total: int          # Total claims in oracle output
  claims_supported: int      # Claims verified against source
  changes_total: int         # Important changes in PR
  changes_surfaced: int      # Changes mentioned in summary
  scoring_model: str         # Model used for scoring
  scoring_latency_ms: int    # Time to score
```

**Acceptance Criteria**:
- LLM scoring prompts are deterministic (temperature=0 where supported)
- Scoring is independent per replay (no cross-contamination between PRs)
- Raw LLM scoring output is logged for audit/debugging
- Scoring provider is configurable (Claude default, swap to others via config)

> Sources: `loa-grimoire/context/echelon_context.md:42-49`

### FR-4: Calibration Certificate Generation

Aggregate replay scores into a structured, versioned calibration certificate.

**Certificate Schema** (compatible with `echelon_rlmf_schema.json` calibration fields):

```
CalibrationCertificate:
  schema_version: str        # "1.0.0"
  certificate_id: str        # UUID
  construct_id: str          # Identifier for the oracle evaluated
  domain: str                # "community_oracle"
  replay_count: int          # Number of PRs evaluated (>= 50 for significance)
  precision: float           # Aggregate precision (mean)
  recall: float              # Aggregate recall (mean)
  reply_accuracy: float      # Aggregate reply accuracy (mean)
  composite_score: float     # Weighted average (configurable weights)
  brier: float               # Brier-compatible score (for RLMF alignment)
  sample_size: int           # = replay_count (for RLMF alignment)
  timestamp: datetime        # When evaluation completed
  ground_truth_source: str   # Repository URL
  commit_range: str          # First..last commit evaluated
  methodology_version: str   # Scoring prompt version
  scoring_model: str         # LLM used for scoring
  individual_scores: list    # Per-replay breakdown (optional, for audit)
```

**Acceptance Criteria**:
- JSON output with schema version for forward compatibility
- Minimum replay count is configurable (default 50)
- Composite score weights are configurable (default: equal weight)
- Certificate includes methodology version for reproducibility
- Compatible with `echelon_rlmf_schema.json` calibration fields: `brier`, `sample_size`, `agent_accuracy`

> Sources: `loa-grimoire/context/echelon_context.md:50-63`, `docs/schemas/echelon_rlmf_schema.json` (calibration sub-schema)

### FR-5: CLI Interface

Command-line tool for manual verification runs.

**Commands**:

```bash
# Full pipeline: ingest → invoke → score → certify
echelon verify --repo <github-url> --construct <endpoint-or-module> [options]

# Ingest only (fetch and cache ground truth)
echelon ingest --repo <github-url> --output <dir> [--limit N] [--since DATE]

# Score only (against cached ground truth + oracle output)
echelon score --data <dir> --output <certificate.json>

# Inspect a certificate
echelon inspect <certificate.json>
```

**Options**:
- `--construct-type http|python` — Oracle adapter type (auto-detected if possible)
- `--scoring-model claude-sonnet-4-6` — LLM for verification scoring
- `--min-replays 50` — Minimum replays for certificate generation
- `--output <path>` — Output directory for certificate and artifacts
- `--verbose` — Show per-replay scores as they complete
- `--dry-run` — Ingest ground truth without invoking oracle

### FR-6: API Interface

HTTP API for programmatic/automated evaluation.

**Endpoints**:

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/api/verification/run` | Start a verification run (returns job ID) |
| `GET` | `/api/verification/status/{job_id}` | Check run status and progress |
| `GET` | `/api/verification/result/{job_id}` | Get completed certificate |
| `GET` | `/api/verification/certificates` | List all generated certificates |

**Notes**:
- Verification runs are async (can take minutes for 50+ replays)
- Job status includes progress (replays completed / total)
- API shares the same verification engine as CLI

## 6. Technical Requirements

### TR-1: Tech Stack

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| Language | Python 3.12+ | Consistent with existing backend (`backend/requirements.txt`) |
| Data models | Pydantic v2 | Consistent with existing schemas and backend patterns |
| GitHub API | `httpx` (async) | Already in `requirements.txt` (v0.28.1) |
| LLM client | `anthropic` SDK | Already in `requirements.txt` (v0.74.1), configurable |
| Storage | Local filesystem (JSON/JSONL) | MVP simplicity, no DB dependency |
| CLI framework | `click` or `argparse` | Standard Python CLI |
| API framework | FastAPI | Consistent with existing backend |

### TR-2: Package Location

New top-level package: `verification/` alongside `frontend/`, `backend/`, `smart-contracts/`.

```
verification/
├── pyproject.toml           # Package config
├── src/
│   └── echelon_verify/
│       ├── __init__.py
│       ├── cli.py           # CLI entry point
│       ├── api.py           # FastAPI router (mountable)
│       ├── ingestion/       # Ground truth extraction
│       ├── oracle/          # Oracle adapter interface
│       ├── scoring/         # Verification scoring engine
│       ├── certificate/     # Certificate generation
│       └── config.py        # Configuration management
├── tests/
└── prompts/                 # Versioned scoring prompt templates
```

### TR-3: Non-Functional Requirements

| Requirement | Target |
|-------------|--------|
| Scoring reproducibility | < 5% variance across runs for deterministic oracles |
| GitHub rate limit handling | Exponential backoff, respect `X-RateLimit-*` headers |
| Oracle timeout | Configurable, default 30s per invocation |
| Certificate validation | JSON Schema validation before output |
| Error handling | Graceful degradation (partial results if oracle fails mid-run) |
| Logging | Structured logging (JSON) for all pipeline stages |

## 7. Scope

### In Scope (Phase 1)

- Ground truth ingestion from GitHub (public repos, auth token for private)
- Oracle invocation via HTTP endpoint or Python callable
- LLM-based verification scoring (precision, recall, reply accuracy)
- Calibration certificate generation (JSON)
- CLI interface for manual runs
- API interface for programmatic access
- Versioned scoring prompts for reproducibility
- Local filesystem storage for ground truth and results

### Out of Scope (Phase 1)

- LMSR prediction markets and cost-function trading
- OSINT pipeline (GDELT, Polygon.io, X API)
- VRF perturbation injection
- On-chain settlement and smart contracts
- Agent archetypes and multi-agent simulation
- Paradox Engine and Entropy Engine
- Token economics and burn mechanics
- Frontend UI for verification results
- Wallet integration and HD derivation
- Multi-construct comparative evaluation in a single run (stretch goal)
- Confidence discipline metric (stretch goal)

> Sources: `loa-grimoire/context/echelon_context.md:103-118`

### Stretch Goals

- Comparative evaluation: Multiple oracles against same ground truth in one run
- Confidence discipline: How often is the oracle confidently wrong vs tentatively wrong?
- RLMF export: Certificate format compatible with RLMF schema for downstream training
- Percentile ranking: Relative scoring when multiple oracles have been evaluated

> Sources: `loa-grimoire/context/echelon_context.md:140-146`

## 8. Risks & Dependencies

### Technical Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| LLM scoring inconsistency | Scores vary between runs | Temperature=0, versioned prompts, multiple scoring runs with averaging |
| GitHub rate limits | Ingestion blocked for large repos | Caching, backoff, conditional requests (If-None-Match) |
| Oracle response format variation | Parsing failures | Strict schema validation, graceful error handling per replay |
| Large diffs overwhelming LLM context | Scoring quality degrades | Chunk large diffs, focus on changed hunks not full file content |

### Dependencies

| Dependency | Type | Status |
|------------|------|--------|
| GitHub REST API v3 | External | Available, rate-limited |
| Anthropic Claude API | External | Available, `anthropic==0.74.1` in backend |
| Python 3.12+ | Runtime | Available (existing backend requirement) |
| `httpx` | Library | Available (v0.28.1 in backend) |
| Pydantic v2 | Library | Available (v2.12.4 in backend) |

### Integration Points (Future)

| Integration | When | What |
|-------------|------|------|
| Constructs Network | Post-Phase 1 | Certificate attaches to finnNFT Soul |
| Hounfour model routing | Post-Phase 1 | Verified constructs access higher model tiers |
| Verification-as-service | Post-Phase 1 | Paid Theatre Replay runs |

## 9. Data Flow

```
GitHub Repository (ground truth source)
    │
    ▼
┌─────────────────────────────────────────┐
│  Ground Truth Ingestion                  │
│  (GitHub API → GroundTruthRecord[])      │
│  Cache: verification/data/{repo}/        │
└──────────────────┬──────────────────────┘
                   │
    ┌──────────────┼──────────────────┐
    ▼              ▼                  ▼
┌────────┐   ┌────────┐        ┌────────┐
│ PR #1  │   │ PR #2  │  ...   │ PR #N  │
└───┬────┘   └───┬────┘        └───┬────┘
    │            │                 │
    ▼            ▼                 ▼
┌─────────────────────────────────────────┐
│  Oracle Adapter (HTTP or Python)         │
│  invoke(pr) → OracleOutput               │
└──────────────────┬──────────────────────┘
                   │
    ┌──────────────┼──────────────────┐
    ▼              ▼                  ▼
┌────────┐   ┌────────┐        ┌────────┐
│Score #1│   │Score #2│  ...   │Score #N│
│P/R/RA  │   │P/R/RA  │        │P/R/RA  │
└───┬────┘   └───┬────┘        └───┬────┘
    │            │                 │
    └──────────────┼──────────────────┘
                   ▼
┌─────────────────────────────────────────┐
│  Calibration Certificate                 │
│  Aggregate P/R/RA → composite score      │
│  Output: certificate.json                │
└─────────────────────────────────────────┘
```

> Sources: `loa-grimoire/context/echelon_context.md:66-79`

## 10. Glossary

| Term | Definition |
|------|-----------|
| **Construct** | An AI agent that claims expertise in a domain (code summarization, community communication, etc.) |
| **Community Oracle** | A construct that ingests code changes and produces audience-facing summaries |
| **Ground Truth** | Historical PR/commit data with known content, used as the verification baseline |
| **Replay** | A single evaluation: one ground truth record passed to one oracle, scored |
| **Calibration Certificate** | Aggregate verification scores across N replays, structured as JSON |
| **Theatre Replay** | Echelon's methodology for verifying construct accuracy (from Real-to-Sim) |
| **RLMF** | Reinforcement Learning from Market Feedback — Echelon's training data paradigm |
| **Precision** | % of oracle claims supported by source material |
| **Recall** | % of important source changes surfaced in oracle output |
| **Reply Accuracy** | Groundedness of oracle's follow-up responses |
