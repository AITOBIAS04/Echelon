# SDD: Community Oracle Verification Pipeline

> Cycle: cycle-027 | PRD: `grimoires/loa/prd.md`
> Grounded: Reality files (2026-02-18), backend patterns (`brain.py`, `markets.py`)
> Status: Draft

## 1. Executive Summary

The Community Oracle Verification Pipeline is a standalone Python package (`verification/`) that scores AI construct accuracy against git repository ground truth. It implements a four-stage pipeline: Ground Truth Ingestion → Oracle Invocation → Verification Scoring → Calibration Certificate Generation. The system exposes both a CLI and a FastAPI-mountable API, uses configurable LLM providers for scoring, and produces RLMF-compatible calibration certificates.

The architecture follows existing Echelon backend patterns: Pydantic v2 models, ABC-based provider abstraction, async-first I/O, and FastAPI routers with dependency injection.

## 2. System Architecture

### High-Level Component Diagram

```
┌──────────────────────────────────────────────────────────────┐
│                    verification/                              │
│                                                              │
│  ┌──────────┐   ┌───────────┐   ┌─────────┐   ┌──────────┐ │
│  │ Ingestion │──→│  Oracle    │──→│ Scoring  │──→│ Certifier│ │
│  │  Module   │   │  Adapters  │   │  Engine  │   │  Module  │ │
│  └────┬─────┘   └─────┬─────┘   └────┬─────┘   └────┬─────┘ │
│       │               │              │               │       │
│       │         ┌─────┴─────┐  ┌─────┴─────┐        │       │
│       │         │HTTPAdapter│  │LLM Scoring │        │       │
│       │         │PyAdapter  │  │  Provider  │        │       │
│       │         └───────────┘  └───────────┘        │       │
│       │                                              │       │
│  ┌────┴──────────────────────────────────────────────┴────┐  │
│  │                    Pipeline Orchestrator                │  │
│  │              (coordinates all 4 stages)                │  │
│  └────────────────────────┬───────────────────────────────┘  │
│                           │                                  │
│  ┌────────────────────────┼───────────────────────────────┐  │
│  │         ┌──────────┐   │   ┌──────────┐                │  │
│  │         │   CLI    │   │   │   API    │                │  │
│  │         │ (click)  │   │   │(FastAPI) │                │  │
│  │         └──────────┘   │   └──────────┘                │  │
│  │                  Interface Layer                        │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐  │
│  │                    Storage Layer                        │  │
│  │   data/{repo}/ground_truth.jsonl                       │  │
│  │   data/{repo}/oracle_outputs.jsonl                     │  │
│  │   data/{repo}/scores.jsonl                             │  │
│  │   certificates/{cert_id}.json                          │  │
│  └────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
          │                              │
          ▼                              ▼
    GitHub REST API                LLM Provider APIs
    (ground truth)                 (scoring engine)
```

### Design Principles

1. **Pipeline as composition**: Each stage is an independent module. The orchestrator composes them. Stages can run independently (e.g., `ingest` without `score`).
2. **Adapter pattern for extensibility**: Oracle invocation and LLM scoring use ABC-based adapters, consistent with `backend/agents/brain.py:BaseBrainProvider`.
3. **Async-first**: All I/O operations (GitHub API, oracle calls, LLM scoring) are async, consistent with the existing backend.
4. **Local-first storage**: Filesystem-based (JSON/JSONL). No database dependency for MVP.
5. **Immutable artifacts**: Ground truth, oracle outputs, and scores are append-only. Certificates are write-once.

## 3. Technology Stack

| Component | Technology | Version | Rationale |
|-----------|-----------|---------|-----------|
| Language | Python | 3.12+ | Consistent with `backend/requirements.txt` |
| Models | Pydantic | v2 (2.12+) | Consistent with backend schemas |
| HTTP Client | httpx | 0.28+ | Already in backend deps, async-native |
| LLM Client | anthropic | 0.74+ | Already in backend deps |
| CLI | click | 8.x | Subcommand pattern, better than argparse |
| API | FastAPI | 0.121+ | Consistent with backend routers |
| Async | asyncio + anyio | stdlib | Standard async runtime |
| Testing | pytest + pytest-asyncio | latest | Consistent with backend test patterns |
| Packaging | pyproject.toml | PEP 621 | Modern Python packaging |

### New Dependencies (not in existing backend)

| Package | Purpose |
|---------|---------|
| `click` | CLI framework with subcommand groups |

All other dependencies are already available in the monorepo.

## 4. Package Structure

```
verification/
├── pyproject.toml                    # Package config, CLI entry point
├── README.md                         # Usage documentation
├── src/
│   └── echelon_verify/
│       ├── __init__.py               # Version, public API
│       ├── config.py                 # Configuration management
│       ├── models.py                 # All Pydantic models (single source of truth)
│       ├── pipeline.py              # Pipeline orchestrator
│       ├── cli.py                    # Click CLI entry point
│       ├── api.py                    # FastAPI router (mountable)
│       ├── ingestion/
│       │   ├── __init__.py
│       │   └── github.py            # GitHub REST API client
│       ├── oracle/
│       │   ├── __init__.py
│       │   ├── base.py              # OracleAdapter ABC
│       │   ├── http_adapter.py      # HTTP endpoint adapter
│       │   └── python_adapter.py    # Python callable adapter
│       ├── scoring/
│       │   ├── __init__.py
│       │   ├── base.py              # ScoringProvider ABC
│       │   ├── anthropic_scorer.py  # Claude scoring implementation
│       │   └── prompts/             # Versioned prompt templates
│       │       ├── v1/
│       │       │   ├── precision.txt
│       │       │   ├── recall.txt
│       │       │   ├── reply_accuracy.txt
│       │       │   └── follow_up_question.txt
│       │       └── manifest.json    # Prompt version metadata
│       ├── certificate/
│       │   ├── __init__.py
│       │   └── generator.py         # Certificate generation + validation
│       └── storage.py               # Filesystem read/write helpers
├── tests/
│   ├── conftest.py                   # Shared fixtures
│   ├── test_ingestion.py
│   ├── test_oracle_adapters.py
│   ├── test_scoring.py
│   ├── test_certificate.py
│   ├── test_pipeline.py
│   └── fixtures/                     # Sample ground truth, oracle output
│       ├── sample_pr.json
│       ├── sample_oracle_output.json
│       └── sample_certificate.json
└── data/                             # Runtime data (gitignored)
    └── .gitkeep
```

## 5. Data Models

All models in `echelon_verify/models.py`. Pydantic v2 with strict validation.

### Core Models

```python
class GroundTruthRecord(BaseModel):
    """A single PR/commit extracted from GitHub."""
    id: str                              # PR number or commit SHA
    title: str
    description: str = ""
    diff_content: str
    files_changed: list[str]
    timestamp: datetime
    labels: list[str] = []
    author: str
    url: str                             # GitHub URL for reference
    repo: str                            # owner/repo format

class OracleOutput(BaseModel):
    """Output captured from oracle construct invocation."""
    ground_truth_id: str                 # Links to GroundTruthRecord.id
    summary: str
    key_claims: list[str]
    follow_up_question: str              # Generated question
    follow_up_response: str              # Oracle's answer
    metadata: dict[str, Any] = {}        # Model used, latency, etc.
    invoked_at: datetime
    latency_ms: int

class ReplayScore(BaseModel):
    """Per-replay verification score."""
    ground_truth_id: str
    precision: float = Field(ge=0.0, le=1.0)
    recall: float = Field(ge=0.0, le=1.0)
    reply_accuracy: float = Field(ge=0.0, le=1.0)
    claims_total: int = Field(ge=0)
    claims_supported: int = Field(ge=0)
    changes_total: int = Field(ge=0)
    changes_surfaced: int = Field(ge=0)
    scoring_model: str
    scoring_latency_ms: int
    scored_at: datetime
    raw_scoring_output: dict[str, Any] = {}  # LLM responses for audit

class CalibrationCertificate(BaseModel):
    """Aggregate verification certificate."""
    schema_version: str = "1.0.0"
    certificate_id: str                  # UUID
    construct_id: str
    domain: Literal["community_oracle"] = "community_oracle"
    replay_count: int = Field(ge=1)
    precision: float = Field(ge=0.0, le=1.0)
    recall: float = Field(ge=0.0, le=1.0)
    reply_accuracy: float = Field(ge=0.0, le=1.0)
    composite_score: float = Field(ge=0.0, le=1.0)
    brier: float = Field(ge=0.0, le=0.5)  # RLMF compatibility
    sample_size: int = Field(ge=1)
    timestamp: datetime
    ground_truth_source: str             # Repository URL
    commit_range: str                    # first_sha..last_sha
    methodology_version: str             # Prompt template version
    scoring_model: str
    individual_scores: list[ReplayScore] = []
```

### Configuration Models

```python
class IngestionConfig(BaseModel):
    """GitHub ingestion configuration."""
    repo_url: str                        # https://github.com/owner/repo
    github_token: str | None = None      # For private repos / higher rate limits
    limit: int = 100                     # Max PRs to fetch
    since: datetime | None = None        # Only PRs after this date
    labels: list[str] = []               # Filter by labels
    merged_only: bool = True

class OracleConfig(BaseModel):
    """Oracle adapter configuration."""
    type: Literal["http", "python"]
    # HTTP mode
    url: str | None = None
    headers: dict[str, str] = {}
    timeout_seconds: int = 30
    # Python mode
    module: str | None = None
    callable: str | None = None

class ScoringConfig(BaseModel):
    """Scoring engine configuration."""
    provider: str = "anthropic"          # Scoring LLM provider
    model: str = "claude-sonnet-4-6"    # Scoring model
    api_key: str | None = None           # Falls back to env var
    temperature: float = 0.0             # Deterministic scoring
    prompt_version: str = "v1"           # Which prompt templates to use

class PipelineConfig(BaseModel):
    """Top-level pipeline configuration."""
    ingestion: IngestionConfig
    oracle: OracleConfig
    scoring: ScoringConfig = ScoringConfig()
    min_replays: int = 50
    composite_weights: dict[str, float] = {
        "precision": 1.0,
        "recall": 1.0,
        "reply_accuracy": 1.0,
    }
    output_dir: str = "data"
    construct_id: str = "unnamed-oracle"
```

### API Models

```python
class VerificationRunRequest(BaseModel):
    """Request to start a verification run via API."""
    repo_url: str
    construct: OracleConfig
    scoring: ScoringConfig = ScoringConfig()
    min_replays: int = 50
    construct_id: str = "unnamed-oracle"
    github_token: str | None = None
    limit: int = 100

class VerificationRunStatus(BaseModel):
    """Status of an in-progress verification run."""
    job_id: str
    status: Literal["pending", "ingesting", "invoking", "scoring", "certifying", "completed", "failed"]
    progress: int = 0                    # Replays completed
    total: int = 0                       # Total replays
    started_at: datetime
    error: str | None = None

class VerificationRunResult(BaseModel):
    """Result of a completed verification run."""
    job_id: str
    certificate: CalibrationCertificate
    completed_at: datetime
```

## 6. Component Design

### 6.1 Ground Truth Ingestion (`ingestion/github.py`)

Async GitHub REST API v3 client using `httpx.AsyncClient`.

**Key Class**: `GitHubIngester`

```python
class GitHubIngester:
    def __init__(self, config: IngestionConfig):
        self._client: httpx.AsyncClient  # configured with auth, base_url
        self._rate_limit_remaining: int
        self._rate_limit_reset: datetime

    async def ingest(self) -> list[GroundTruthRecord]:
        """Fetch merged PRs, extract diffs, return structured records."""

    async def _fetch_prs(self) -> list[dict]:
        """Paginated PR listing with rate limit handling."""

    async def _fetch_diff(self, pr_number: int) -> str:
        """Fetch unified diff for a single PR."""

    async def _handle_rate_limit(self, response: httpx.Response) -> None:
        """Exponential backoff when rate limited."""
```

**Rate Limit Strategy**:
- Read `X-RateLimit-Remaining` and `X-RateLimit-Reset` headers
- When remaining < 10: proactive backoff (sleep until reset)
- On 403 rate limit: exponential backoff with jitter (1s, 2s, 4s, max 60s)
- Conditional requests (`If-None-Match` / ETags) for cache validation

**Caching**:
- Ground truth records written to `data/{owner}_{repo}/ground_truth.jsonl`
- Each record is one JSON line (append-only)
- Re-ingestion checks cache first; only fetches new PRs since last timestamp
- Cache key: `{owner}/{repo}:{pr_number}`

**Diff Handling**:
- Request diff via `Accept: application/vnd.github.v3.diff`
- Large diffs (>100KB): truncate to changed hunks only, strip unchanged context
- Binary files: skip (note in `files_changed` but omit from `diff_content`)

### 6.2 Oracle Adapters (`oracle/`)

ABC-based adapter pattern, consistent with `backend/agents/brain.py:BaseBrainProvider`.

**Base Interface** (`oracle/base.py`):

```python
class OracleAdapter(ABC):
    """Interface for oracle construct invocation."""

    @abstractmethod
    async def invoke(
        self, ground_truth: GroundTruthRecord, follow_up_question: str
    ) -> OracleOutput:
        """Invoke the oracle with a ground truth record and capture output."""

    @classmethod
    def from_config(cls, config: OracleConfig) -> "OracleAdapter":
        """Factory method to create adapter from config."""
        if config.type == "http":
            return HttpOracleAdapter(config)
        elif config.type == "python":
            return PythonOracleAdapter(config)
        raise ValueError(f"Unknown oracle type: {config.type}")
```

**HTTP Adapter** (`oracle/http_adapter.py`):

```python
class HttpOracleAdapter(OracleAdapter):
    """Invokes oracle via HTTP POST endpoint."""

    async def invoke(self, ground_truth, follow_up_question) -> OracleOutput:
        # POST to config.url with JSON body:
        # { "pr": { title, description, diff_content, files_changed },
        #   "follow_up_question": "..." }
        # Parse JSON response into OracleOutput
        # Handle: timeout, HTTP errors, invalid response format
```

**Python Adapter** (`oracle/python_adapter.py`):

```python
class PythonOracleAdapter(OracleAdapter):
    """Invokes oracle as a local Python callable."""

    async def invoke(self, ground_truth, follow_up_question) -> OracleOutput:
        # Import config.module, get config.callable
        # Call with GroundTruthRecord data
        # Wrap sync callables in asyncio.to_thread()
        # Handle: ImportError, AttributeError, runtime exceptions
```

**Error Handling**: Both adapters catch exceptions and return `OracleOutput` with `metadata.error` set. The pipeline marks the replay as failed but continues to the next PR.

### 6.3 Scoring Engine (`scoring/`)

LLM-based factual alignment scoring with configurable provider.

**Base Interface** (`scoring/base.py`):

```python
class ScoringProvider(ABC):
    """Interface for LLM-based verification scoring."""

    @abstractmethod
    async def score_precision(
        self, ground_truth: GroundTruthRecord, oracle_output: OracleOutput
    ) -> tuple[float, int, int, dict]:
        """Score precision. Returns (score, claims_total, claims_supported, raw)."""

    @abstractmethod
    async def score_recall(
        self, ground_truth: GroundTruthRecord, oracle_output: OracleOutput
    ) -> tuple[float, int, int, dict]:
        """Score recall. Returns (score, changes_total, changes_surfaced, raw)."""

    @abstractmethod
    async def score_reply_accuracy(
        self, ground_truth: GroundTruthRecord, oracle_output: OracleOutput
    ) -> tuple[float, dict]:
        """Score reply accuracy. Returns (score, raw)."""

    @abstractmethod
    async def generate_follow_up_question(
        self, ground_truth: GroundTruthRecord
    ) -> str:
        """Generate a factual follow-up question about the PR."""
```

**Anthropic Implementation** (`scoring/anthropic_scorer.py`):

```python
class AnthropicScorer(ScoringProvider):
    def __init__(self, config: ScoringConfig):
        self._client = anthropic.AsyncAnthropic(api_key=config.api_key or os.getenv("ANTHROPIC_API_KEY"))
        self._model = config.model
        self._temperature = config.temperature
        self._prompts = PromptLoader(config.prompt_version)
```

**Scoring Flow per Replay**:

1. **Generate follow-up question**: LLM reads the PR diff and generates a factual question that can only be answered correctly by reading the actual source material.
2. **Score precision**: LLM receives oracle's `key_claims` and the PR diff. For each claim, determines if it's supported by the diff. Returns `supported_count / total_claims`.
3. **Score recall**: LLM identifies the N most important changes in the diff. Then checks which appear in the oracle's summary. Returns `surfaced_count / changes_total`.
4. **Score reply accuracy**: LLM compares the oracle's follow-up response against the PR diff. Scores how grounded the answer is (0.0 = fabricated, 1.0 = fully grounded).

**Prompt Templates** (`scoring/prompts/v1/`):

Each template is a text file with `{placeholders}` for ground truth and oracle output. Templates are versioned so that scoring methodology changes are traceable. The `manifest.json` tracks:

```json
{
  "version": "v1",
  "created": "2026-02-19",
  "prompts": {
    "precision": "precision.txt",
    "recall": "recall.txt",
    "reply_accuracy": "reply_accuracy.txt",
    "follow_up_question": "follow_up_question.txt"
  }
}
```

**Structured Output**: Scoring prompts request JSON output from the LLM for reliable parsing:

```json
// Precision scoring output
{
  "claims": [
    {"claim": "Added rate limiting to /api/users", "supported": true, "evidence": "diff line 42"},
    {"claim": "Fixed XSS vulnerability", "supported": false, "evidence": null}
  ],
  "precision": 0.5,
  "total": 2,
  "supported": 1
}
```

### 6.4 Pipeline Orchestrator (`pipeline.py`)

Coordinates the four stages with progress tracking and partial result handling.

```python
class VerificationPipeline:
    def __init__(self, config: PipelineConfig):
        self._ingester = GitHubIngester(config.ingestion)
        self._oracle = OracleAdapter.from_config(config.oracle)
        self._scorer: ScoringProvider  # created from config.scoring
        self._storage = Storage(config.output_dir)
        self._progress_callback: Callable | None = None

    async def run(self) -> CalibrationCertificate:
        """Execute full pipeline: ingest → invoke → score → certify."""

    async def ingest_only(self) -> list[GroundTruthRecord]:
        """Stage 1 only: fetch and cache ground truth."""

    async def score_only(self, data_dir: str) -> CalibrationCertificate:
        """Stages 3-4: score cached data and generate certificate."""
```

**Pipeline Execution Flow**:

```
1. Ingest: GitHubIngester.ingest() → GroundTruthRecord[]
   └─ Write to data/{repo}/ground_truth.jsonl

2. For each GroundTruthRecord:
   a. Generate follow-up question (ScoringProvider)
   b. Invoke oracle (OracleAdapter) with PR data + follow-up question
   c. Write OracleOutput to data/{repo}/oracle_outputs.jsonl
   d. Score: precision, recall, reply_accuracy (ScoringProvider)
   e. Write ReplayScore to data/{repo}/scores.jsonl
   f. Report progress via callback

3. Certify: Aggregate all ReplayScores → CalibrationCertificate
   └─ Write to certificates/{cert_id}.json
```

**Error Handling**:
- Single replay failure: log error, skip, continue to next PR
- Oracle timeout: mark as failed, include in certificate metadata
- Scoring LLM failure: retry once, then mark as failed
- If successful replays < `min_replays`: generate partial certificate with warning
- Fatal errors (no GitHub access, invalid config): raise immediately

### 6.5 Certificate Generator (`certificate/generator.py`)

```python
class CertificateGenerator:
    def generate(
        self,
        scores: list[ReplayScore],
        config: PipelineConfig,
        ground_truth_source: str,
        commit_range: str,
    ) -> CalibrationCertificate:
        """Aggregate scores into a calibration certificate."""
```

**Aggregation**:
- `precision` = mean of all `ReplayScore.precision`
- `recall` = mean of all `ReplayScore.recall`
- `reply_accuracy` = mean of all `ReplayScore.reply_accuracy`
- `composite_score` = weighted average using `config.composite_weights` (normalized)
- `brier` = `1 - composite_score` mapped to [0, 0.5] range for RLMF compatibility
- `sample_size` = `replay_count` = len(scores)
- `methodology_version` = scoring prompt version string

**Validation**: Certificate is validated against `CalibrationCertificate` model before writing. Invalid certificates raise `ValueError`.

### 6.6 Storage Layer (`storage.py`)

Simple filesystem abstraction. No database.

```python
class Storage:
    def __init__(self, base_dir: str = "data"):
        self._base = Path(base_dir)

    def repo_dir(self, repo: str) -> Path:
        """Get/create directory for a repository. repo='owner/repo'."""
        safe_name = repo.replace("/", "_")
        path = self._base / safe_name
        path.mkdir(parents=True, exist_ok=True)
        return path

    def append_jsonl(self, path: Path, record: BaseModel) -> None:
        """Append a Pydantic model as one JSON line."""

    def read_jsonl(self, path: Path, model: type[T]) -> list[T]:
        """Read all records from a JSONL file."""

    def write_certificate(self, cert: CalibrationCertificate) -> Path:
        """Write certificate to certificates/{cert_id}.json."""
```

**File Layout**:

```
data/
├── owner_repo/
│   ├── ground_truth.jsonl       # One GroundTruthRecord per line
│   ├── oracle_outputs.jsonl     # One OracleOutput per line
│   └── scores.jsonl             # One ReplayScore per line
└── certificates/
    ├── {uuid}.json              # CalibrationCertificate
    └── index.jsonl              # Certificate metadata for listing
```

## 7. Interface Design

### 7.1 CLI (`cli.py`)

Built with `click`. Entry point registered in `pyproject.toml` as `echelon`.

```python
@click.group()
def cli():
    """Echelon Oracle Verification Pipeline."""

@cli.command()
@click.option("--repo", required=True, help="GitHub repository URL")
@click.option("--construct", required=True, help="Oracle endpoint URL or Python module")
@click.option("--construct-type", type=click.Choice(["http", "python"]), default=None)
@click.option("--scoring-model", default="claude-sonnet-4-6")
@click.option("--min-replays", default=50, type=int)
@click.option("--limit", default=100, type=int, help="Max PRs to fetch")
@click.option("--output", default="data", help="Output directory")
@click.option("--construct-id", default="unnamed-oracle")
@click.option("--verbose", is_flag=True)
@click.option("--dry-run", is_flag=True, help="Ingest only, don't invoke oracle")
async def verify(repo, construct, **kwargs):
    """Run full verification pipeline."""

@cli.command()
@click.option("--repo", required=True)
@click.option("--output", default="data")
@click.option("--limit", default=100, type=int)
@click.option("--since", default=None, type=click.DateTime())
async def ingest(repo, output, limit, since):
    """Fetch and cache ground truth from GitHub."""

@cli.command()
@click.option("--data", required=True, help="Data directory with cached results")
@click.option("--output", default=None, help="Certificate output path")
async def score(data, output):
    """Score cached oracle outputs and generate certificate."""

@cli.command()
@click.argument("certificate_path")
def inspect(certificate_path):
    """Display a calibration certificate."""
```

**Output Format** (verbose mode):

```
Echelon Oracle Verification Pipeline
═══════════════════════════════════════

Ingesting ground truth from github.com/owner/repo...
  Fetched 73 merged PRs

Invoking oracle (http://localhost:8000/summarize)...
  [1/73]  PR #142 "Add rate limiting" .............. OK (320ms)
  [2/73]  PR #138 "Fix auth bypass" ................ OK (450ms)
  ...

Scoring with claude-sonnet-4-6...
  [1/73]  PR #142  P=0.85  R=0.90  RA=0.92
  [2/73]  PR #138  P=0.70  R=0.80  RA=0.75
  ...

Certificate generated:
  ID:         a1b2c3d4-...
  Replays:    73
  Precision:  0.82 (mean)
  Recall:     0.78 (mean)
  Reply Acc:  0.85 (mean)
  Composite:  0.82
  Saved to:   data/certificates/a1b2c3d4.json
```

### 7.2 API (`api.py`)

FastAPI router, mountable into the existing backend or run standalone.

```python
router = APIRouter(prefix="/api/verification", tags=["Verification"])

# In-memory job tracking (MVP; replace with Redis/DB for production)
_jobs: dict[str, VerificationJob] = {}

@router.post("/run", response_model=VerificationRunStatus)
async def start_verification_run(request: VerificationRunRequest):
    """Start an async verification run. Returns job ID for polling."""
    job_id = str(uuid4())
    # Launch pipeline in background task
    # Return immediate status with job_id

@router.get("/status/{job_id}", response_model=VerificationRunStatus)
async def get_run_status(job_id: str):
    """Check progress of a verification run."""

@router.get("/result/{job_id}", response_model=VerificationRunResult)
async def get_run_result(job_id: str):
    """Get the calibration certificate for a completed run."""

@router.get("/certificates", response_model=list[CalibrationCertificate])
async def list_certificates():
    """List all generated calibration certificates."""
```

**Job Management**:
- Jobs stored in-memory dict (MVP). Not persistent across restarts.
- `BackgroundTasks` or `asyncio.create_task()` for async pipeline execution.
- Progress updates via pipeline callback writing to job status.
- Future: Replace with task queue (Celery/Redis) for production.

**Standalone Mode**:

```python
# verification/src/echelon_verify/server.py
if __name__ == "__main__":
    app = FastAPI(title="Echelon Verification API")
    app.include_router(router)
    uvicorn.run(app, host="0.0.0.0", port=8100)
```

**Backend Integration** (future):

```python
# backend/main.py
from echelon_verify.api import router as verification_router
app.include_router(verification_router)
```

## 8. Security Architecture

### 8.1 API Key Management

| Secret | Source | Never Stored In |
|--------|--------|----------------|
| GitHub token | `GITHUB_TOKEN` env var or `--github-token` CLI arg | Config files, logs, certificates |
| Anthropic API key | `ANTHROPIC_API_KEY` env var or config | Config files, logs, certificates |
| Oracle auth headers | `OracleConfig.headers` | Logs, certificates |

**Principle**: Secrets flow through env vars or CLI args. Never written to disk. Never included in certificates or scoring output.

### 8.2 Input Validation

- Repository URL: validated format (`https://github.com/{owner}/{repo}`)
- Oracle URL: validated URL format, no private IP ranges (localhost allowed for dev)
- PR diff content: truncated at 100KB to prevent LLM context overflow
- Oracle response: validated against `OracleOutput` schema. Malformed responses logged and skipped.

### 8.3 Rate Limiting

- GitHub API: respect rate limits via headers (see 6.1)
- LLM API: no explicit rate limiting (Anthropic handles this server-side)
- Verification API: no auth required for MVP. Add `Depends(get_current_user)` when integrated with backend.

## 9. Error Handling Strategy

| Error Type | Scope | Handling |
|------------|-------|----------|
| GitHub 404 | Ingestion | Raise `IngestionError` with repo URL |
| GitHub rate limit | Ingestion | Exponential backoff, retry |
| GitHub auth failure | Ingestion | Raise `IngestionError` with hint about token |
| Oracle timeout | Per-replay | Log, mark failed, continue |
| Oracle HTTP error | Per-replay | Log with status code, mark failed, continue |
| Oracle invalid response | Per-replay | Log, mark failed, continue |
| Python import error | Oracle init | Raise `OracleConfigError` immediately |
| LLM API error | Per-replay | Retry once, then log and mark failed |
| LLM invalid JSON | Per-replay | Retry with stricter prompt, then fallback score |
| Insufficient replays | Certification | Generate partial certificate with `warning` field |

**Partial Results**: The pipeline always attempts to generate a certificate, even with failures. The certificate includes `replay_count` (successful) and metadata about failures. The `min_replays` threshold produces a warning, not a hard failure.

## 10. Testing Strategy

| Level | Focus | Count |
|-------|-------|-------|
| Unit | Models, scoring logic, certificate generation | ~20 tests |
| Integration | GitHub API (mocked), oracle adapters, scoring pipeline | ~15 tests |
| E2E | Full pipeline with fixture data | ~5 tests |

**Key Test Scenarios**:

1. **Ingestion**: Mock GitHub API responses, verify `GroundTruthRecord` parsing, pagination, rate limit handling
2. **Oracle Adapters**: Mock HTTP endpoint, test timeout handling, malformed responses, Python callable invocation
3. **Scoring**: Use fixture ground truth + oracle output, verify prompt formatting, score calculation
4. **Certificate**: Verify aggregation math, Brier score calculation, schema validation
5. **Pipeline**: End-to-end with mocked GitHub + mocked oracle + mocked LLM
6. **CLI**: Smoke test `verify --dry-run` with fixture data
7. **API**: Test endpoint routing, job lifecycle, status polling

**Fixtures**: Sample PR data, oracle outputs, and scores stored in `tests/fixtures/` for deterministic testing without API calls.

## 11. Deployment Architecture

### Phase 1 (MVP)

- **CLI**: Installed via `pip install -e verification/` in the monorepo
- **API**: Run standalone via `python -m echelon_verify.server` or mount into existing backend
- **Storage**: Local filesystem (`verification/data/`)
- **No infrastructure required**: Runs on developer's machine

### Future (Post-Phase 1)

- API deployed alongside backend (Railway/Vercel)
- Storage: S3 or equivalent for certificates
- Job queue: Redis + Celery for async verification runs
- Certificate registry: Database-backed for listing and querying

## 12. Configuration

### Environment Variables

| Variable | Required | Default | Purpose |
|----------|----------|---------|---------|
| `GITHUB_TOKEN` | No | None | GitHub API authentication |
| `ANTHROPIC_API_KEY` | Yes (for scoring) | None | LLM scoring provider |
| `ECHELON_VERIFY_DATA_DIR` | No | `data` | Data storage directory |
| `ECHELON_VERIFY_SCORING_MODEL` | No | `claude-sonnet-4-6` | Default scoring model |

### Config File (Optional)

```yaml
# verification/config.yaml (optional, CLI args override)
ingestion:
  limit: 100
  merged_only: true

scoring:
  provider: anthropic
  model: claude-sonnet-4-6
  temperature: 0.0
  prompt_version: v1

pipeline:
  min_replays: 50
  composite_weights:
    precision: 1.0
    recall: 1.0
    reply_accuracy: 1.0
```

## 13. Technical Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| LLM scoring variance | Medium | Score reproducibility < 5% target | Temperature=0, structured JSON output, versioned prompts |
| Large diffs exceed LLM context | Medium | Scoring quality degrades for big PRs | Truncate to hunks, skip binary files, cap at 100KB |
| Oracle response format diversity | Medium | Parsing failures | Schema validation with graceful fallback |
| GitHub API changes | Low | Ingestion breaks | Pin API version (v3), integration tests |
| Click async compatibility | Low | CLI doesn't work | Use `asyncio.run()` wrapper in CLI commands |

## 14. Future Considerations

- **Multi-construct comparison**: Run multiple oracles against same ground truth in one pipeline execution
- **Confidence discipline**: Add 4th metric measuring calibration of oracle's confidence signals
- **On-chain certificates**: Publish certificate hashes to Base for immutable verification
- **Frontend dashboard**: React UI for browsing certificates and comparing oracles
- **Webhook integration**: Trigger verification runs on PR merge events
- **RLMF export**: Full compatibility with `echelon_rlmf_schema.json` for training data
