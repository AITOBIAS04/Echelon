# Sprint Plan: Community Oracle Verification Pipeline

> Cycle: cycle-027 | PRD: `grimoires/loa/prd.md` | SDD: `grimoires/loa/sdd.md`
> Team: 1 AI engineer | Sprint cadence: continuous
> Global sprint offset: 14 (previous cycle ended at 13)

## Sprint Overview

5 sprints decomposing the verification pipeline bottom-up — data models first, external integrations second, orchestration last. Each sprint produces tested, runnable code.

| Sprint | Label | Key Deliverables |
|--------|-------|-----------------|
| 1 | Package Foundation + Data Models + Storage | Scaffold, Pydantic models, config, storage layer |
| 2 | Ground Truth Ingestion | GitHubIngester, rate limits, caching, diff handling |
| 3 | Oracle Adapters | OracleAdapter ABC, HTTP adapter, Python adapter |
| 4 | Scoring Engine + Certificate Generator | ScoringProvider, AnthropicScorer, prompts, certificate math |
| 5 | Pipeline Orchestrator + CLI + API | VerificationPipeline, click CLI, FastAPI router, E2E tests |

---

## Sprint 1 — Package Foundation + Data Models + Storage

**Goal**: Establish the `verification/` package with all Pydantic models, configuration management, and filesystem storage layer. Everything downstream depends on these.

### Tasks

#### 1.1 — Package scaffold

Create `verification/` directory structure with `pyproject.toml`, `src/echelon_verify/` namespace, all `__init__.py` files, `tests/`, `data/.gitkeep`, and `prompts/` directories.

**Acceptance Criteria**:
- [ ] `verification/pyproject.toml` defines package name `echelon-verify`, Python >=3.12, dependencies (pydantic, httpx, anthropic, click, fastapi, uvicorn)
- [ ] `pip install -e verification/` succeeds
- [ ] `python -c "import echelon_verify"` succeeds
- [ ] Directory structure matches SDD §4

#### 1.2 — Core Pydantic models (`models.py`)

Implement all data models: `GroundTruthRecord`, `OracleOutput`, `ReplayScore`, `CalibrationCertificate`.

**Acceptance Criteria**:
- [ ] All 4 core models with field types, constraints (`Field(ge=0.0, le=1.0)`), and defaults per SDD §5
- [ ] `CalibrationCertificate.brier` constrained to [0.0, 0.5]
- [ ] `CalibrationCertificate.domain` is `Literal["community_oracle"]`
- [ ] JSON serialization round-trips without data loss

#### 1.3 — Configuration models (`config.py`)

Implement `IngestionConfig`, `OracleConfig`, `ScoringConfig`, `PipelineConfig`. Add env var fallback for API keys.

**Acceptance Criteria**:
- [ ] All 4 config models per SDD §5
- [ ] `ScoringConfig.api_key` falls back to `ANTHROPIC_API_KEY` env var
- [ ] `OracleConfig` validates that `url` is set when `type="http"` and `module`+`callable` when `type="python"`
- [ ] `PipelineConfig.composite_weights` defaults to equal weights

#### 1.4 — API models (`models.py`)

Implement `VerificationRunRequest`, `VerificationRunStatus`, `VerificationRunResult`.

**Acceptance Criteria**:
- [ ] All 3 API models per SDD §5
- [ ] `VerificationRunStatus.status` is a `Literal` enum with all 7 states
- [ ] Models are JSON-serializable for FastAPI response

#### 1.5 — Storage layer (`storage.py`)

Implement `Storage` class with JSONL append/read, certificate write, repo directory management.

**Acceptance Criteria**:
- [ ] `repo_dir()` creates `data/{owner}_{repo}/` safely (no path traversal)
- [ ] `append_jsonl()` appends one Pydantic model per line
- [ ] `read_jsonl()` deserializes back to typed models
- [ ] `write_certificate()` writes to `certificates/{cert_id}.json`
- [ ] File operations are atomic where possible (write-to-temp + rename)

#### 1.6 — Unit tests for models + storage

**Acceptance Criteria**:
- [ ] Model validation tests: valid construction, constraint violations rejected
- [ ] Storage round-trip tests: write JSONL → read JSONL → compare
- [ ] Certificate write + read test
- [ ] All tests pass with `pytest verification/tests/`

**Testing**: ~10 unit tests

---

## Sprint 2 — Ground Truth Ingestion

**Goal**: Implement `GitHubIngester` that fetches merged PRs from GitHub, extracts diffs, handles rate limits, and caches results as JSONL.

**Depends on**: Sprint 1 (models, config, storage)

### Tasks

#### 2.1 — GitHubIngester core (`ingestion/github.py`)

Implement the `GitHubIngester` class with `ingest()`, `_fetch_prs()`, `_fetch_diff()` methods.

**Acceptance Criteria**:
- [ ] `ingest()` returns `list[GroundTruthRecord]` from GitHub REST API v3
- [ ] Fetches merged PRs only (state=closed, merged=true)
- [ ] Extracts unified diff via `Accept: application/vnd.github.v3.diff`
- [ ] Supports pagination for repos with >100 PRs (Link header)
- [ ] Populates all `GroundTruthRecord` fields including `files_changed`, `labels`, `author`
- [ ] Async using `httpx.AsyncClient`

#### 2.2 — Rate limit handling

Implement `_handle_rate_limit()` with proactive and reactive backoff.

**Acceptance Criteria**:
- [ ] Reads `X-RateLimit-Remaining` and `X-RateLimit-Reset` headers
- [ ] Proactive backoff when remaining < 10
- [ ] Exponential backoff with jitter on 403 rate limit (1s, 2s, 4s, max 60s)
- [ ] Supports conditional requests with `If-None-Match` / ETags

#### 2.3 — Caching and incremental ingestion

Write ground truth to JSONL via `Storage`. Re-ingestion fetches only new PRs.

**Acceptance Criteria**:
- [ ] Records written to `data/{owner}_{repo}/ground_truth.jsonl` via `Storage.append_jsonl()`
- [ ] Re-ingestion reads existing cache, only fetches PRs newer than last timestamp
- [ ] `--since` CLI option filters PRs by date

#### 2.4 — Diff handling

Truncate large diffs, skip binary files.

**Acceptance Criteria**:
- [ ] Diffs >100KB truncated to changed hunks only
- [ ] Binary files noted in `files_changed` but omitted from `diff_content`
- [ ] Truncation logged at INFO level

#### 2.5 — Tests for ingestion

**Acceptance Criteria**:
- [ ] Mock GitHub API responses (PR listing, diff, pagination, rate limit)
- [ ] Test: pagination fetches all pages
- [ ] Test: rate limit triggers backoff
- [ ] Test: large diff truncation
- [ ] Test: cache hit skips re-fetch
- [ ] Test: `GroundTruthRecord` fields populated correctly
- [ ] Test fixture: `tests/fixtures/sample_pr.json` with realistic PR data

**Testing**: ~8 tests (unit + integration with mocked httpx)

---

## Sprint 3 — Oracle Adapters

**Goal**: Implement the `OracleAdapter` ABC and both HTTP and Python adapters. Oracle invocation is the construct-under-test interface.

**Depends on**: Sprint 1 (models)

### Tasks

#### 3.1 — OracleAdapter ABC (`oracle/base.py`)

Define the abstract base class and factory method.

**Acceptance Criteria**:
- [ ] `OracleAdapter` ABC with `async invoke(ground_truth, follow_up_question) -> OracleOutput`
- [ ] `from_config(config: OracleConfig) -> OracleAdapter` factory method
- [ ] Raises `ValueError` for unknown oracle type

#### 3.2 — HTTP Oracle Adapter (`oracle/http_adapter.py`)

Implement `HttpOracleAdapter` for HTTP POST oracle endpoints.

**Acceptance Criteria**:
- [ ] POSTs JSON body with PR data (`title`, `description`, `diff_content`, `files_changed`) + `follow_up_question`
- [ ] Parses JSON response into `OracleOutput`
- [ ] Handles: timeout (configurable, default 30s), HTTP errors (4xx/5xx), malformed responses
- [ ] Custom headers from `OracleConfig.headers`
- [ ] Records `latency_ms` in `OracleOutput`
- [ ] On failure: returns `OracleOutput` with `metadata.error` set rather than raising

#### 3.3 — Python Oracle Adapter (`oracle/python_adapter.py`)

Implement `PythonOracleAdapter` for local Python callable oracles.

**Acceptance Criteria**:
- [ ] Dynamically imports `config.module` and gets `config.callable`
- [ ] Calls with `GroundTruthRecord` data dict + `follow_up_question`
- [ ] Wraps sync callables in `asyncio.to_thread()`
- [ ] Handles: `ImportError`, `AttributeError`, runtime exceptions
- [ ] Records `latency_ms` in `OracleOutput`
- [ ] On failure: returns `OracleOutput` with `metadata.error` set

#### 3.4 — Tests for oracle adapters

**Acceptance Criteria**:
- [ ] HTTP adapter: mock endpoint returning valid response → correct `OracleOutput`
- [ ] HTTP adapter: mock timeout → `OracleOutput` with error metadata
- [ ] HTTP adapter: mock malformed JSON → graceful handling
- [ ] HTTP adapter: custom headers sent correctly
- [ ] Python adapter: test with a simple callable fixture
- [ ] Python adapter: test with non-existent module → error
- [ ] Factory method: `from_config()` dispatches correctly
- [ ] Test fixture: `tests/fixtures/sample_oracle_output.json`

**Testing**: ~8 tests

---

## Sprint 4 — Scoring Engine + Certificate Generator

**Goal**: Implement LLM-based factual alignment scoring with versioned prompts, and the certificate aggregation logic with RLMF-compatible Brier scoring.

**Depends on**: Sprint 1 (models), Sprint 3 (oracle output format)

### Tasks

#### 4.1 — ScoringProvider ABC (`scoring/base.py`)

Define the abstract scoring interface.

**Acceptance Criteria**:
- [ ] `ScoringProvider` ABC with 4 abstract methods per SDD §6.3
- [ ] `score_precision()` returns `(score, claims_total, claims_supported, raw_output)`
- [ ] `score_recall()` returns `(score, changes_total, changes_surfaced, raw_output)`
- [ ] `score_reply_accuracy()` returns `(score, raw_output)`
- [ ] `generate_follow_up_question()` returns `str`

#### 4.2 — Versioned prompt templates (`scoring/prompts/v1/`)

Create the 4 scoring prompt templates and manifest.

**Acceptance Criteria**:
- [ ] `precision.txt`: Instructs LLM to verify each oracle claim against the diff, output structured JSON
- [ ] `recall.txt`: Instructs LLM to identify key changes in diff, check which appear in summary
- [ ] `reply_accuracy.txt`: Instructs LLM to score groundedness of follow-up response
- [ ] `follow_up_question.txt`: Instructs LLM to generate a factual question from PR content
- [ ] `manifest.json` with version, date, and prompt file references
- [ ] All prompts request JSON output with defined schema
- [ ] `PromptLoader` class reads templates and fills `{placeholders}`

#### 4.3 — AnthropicScorer implementation (`scoring/anthropic_scorer.py`)

Implement the Claude-based scoring provider.

**Acceptance Criteria**:
- [ ] Uses `anthropic.AsyncAnthropic` client
- [ ] `temperature=0.0` for deterministic scoring
- [ ] Parses structured JSON from LLM responses
- [ ] Handles LLM JSON parse failures with one retry (stricter prompt)
- [ ] Records `raw_scoring_output` for audit
- [ ] All 4 scoring methods implemented per SDD §6.3 flow

#### 4.4 — Certificate generator (`certificate/generator.py`)

Implement `CertificateGenerator` with aggregation math.

**Acceptance Criteria**:
- [ ] `precision` = mean of all `ReplayScore.precision`
- [ ] `recall` = mean of all `ReplayScore.recall`
- [ ] `reply_accuracy` = mean of all `ReplayScore.reply_accuracy`
- [ ] `composite_score` = weighted average using normalized `composite_weights`
- [ ] `brier` = `(1 - composite_score) * 0.5` for RLMF [0, 0.5] range
- [ ] `sample_size` = `replay_count` = `len(scores)`
- [ ] `methodology_version` matches prompt version
- [ ] `certificate_id` is a UUID4
- [ ] Output validates against `CalibrationCertificate` model
- [ ] Test fixture: `tests/fixtures/sample_certificate.json`

#### 4.5 — Tests for scoring + certificate

**Acceptance Criteria**:
- [ ] Prompt template loading: fills placeholders correctly
- [ ] AnthropicScorer: mock LLM responses → correct scores (3 metric tests)
- [ ] AnthropicScorer: mock LLM JSON parse failure → retry works
- [ ] Certificate: aggregate 5 fixture scores → correct means
- [ ] Certificate: composite weights affect result
- [ ] Certificate: Brier score calculation correct
- [ ] Certificate: validates against model constraints

**Testing**: ~10 tests

---

## Sprint 5 — Pipeline Orchestrator + CLI + API

**Goal**: Wire everything together. Implement the pipeline orchestrator, click CLI, and FastAPI API. Deliver end-to-end working system.

**Depends on**: Sprints 1–4 (all components)

### Tasks

#### 5.1 — Pipeline orchestrator (`pipeline.py`)

Implement `VerificationPipeline` coordinating all 4 stages.

**Acceptance Criteria**:
- [ ] `run()` executes: ingest → (for each PR: generate question → invoke oracle → score) → certify
- [ ] `ingest_only()` runs stage 1 only
- [ ] `score_only()` runs stages 3-4 from cached data
- [ ] Progress callback reports `(completed, total)` per replay
- [ ] Single replay failure: logged, skipped, pipeline continues
- [ ] Oracle timeout: marked failed, continues
- [ ] LLM failure: retry once, then mark failed
- [ ] Insufficient replays: partial certificate with warning
- [ ] All intermediate results written to storage (JSONL) as they complete

#### 5.2 — CLI (`cli.py`)

Implement click-based CLI with 4 subcommands.

**Acceptance Criteria**:
- [ ] `echelon verify` — full pipeline with all options per SDD §7.1
- [ ] `echelon ingest` — fetch and cache ground truth
- [ ] `echelon score` — score cached data, generate certificate
- [ ] `echelon inspect` — display certificate in human-readable format
- [ ] `--verbose` shows per-replay progress
- [ ] `--dry-run` ingests without invoking oracle
- [ ] Entry point registered in `pyproject.toml`: `[project.scripts] echelon = "echelon_verify.cli:cli"`
- [ ] `asyncio.run()` wrapper for async commands

#### 5.3 — FastAPI API (`api.py`)

Implement the 4 API endpoints with async job management.

**Acceptance Criteria**:
- [ ] `POST /api/verification/run` — starts async verification, returns job ID
- [ ] `GET /api/verification/status/{job_id}` — returns progress (replays completed / total)
- [ ] `GET /api/verification/result/{job_id}` — returns certificate for completed jobs
- [ ] `GET /api/verification/certificates` — lists all certificates from storage
- [ ] 404 for unknown job_id
- [ ] Job status includes all 7 states from `VerificationRunStatus`
- [ ] Background task execution via `asyncio.create_task()`

#### 5.4 — Standalone server (`server.py`)

Minimal entry point for standalone API operation.

**Acceptance Criteria**:
- [ ] `python -m echelon_verify.server` starts uvicorn on port 8100
- [ ] Mounts verification router at `/api/verification`
- [ ] Health check endpoint at `/health`

#### 5.5 — E2E tests

Full pipeline test with mocked external services.

**Acceptance Criteria**:
- [ ] E2E: Mock GitHub (3 PRs) + Mock oracle + Mock LLM → certificate generated
- [ ] E2E: Verify certificate fields (replay_count=3, all scores in [0,1])
- [ ] CLI: `verify --dry-run` smoke test with fixtures
- [ ] API: Start run → poll status → get result lifecycle test
- [ ] API: List certificates returns stored results
- [ ] Pipeline: partial failure (1 of 3 PRs fails) → certificate with 2 replays

**Testing**: ~8 tests (E2E + integration)

---

## Risk Mitigation

| Risk | Sprint | Mitigation |
|------|--------|------------|
| LLM scoring variance | 4 | Temperature=0, structured JSON, versioned prompts |
| Large diffs overflow LLM context | 2 | 100KB truncation, hunk-only extraction |
| Click async compatibility | 5 | `asyncio.run()` wrapper pattern |
| Oracle response diversity | 3 | Schema validation, error metadata fallback |
| GitHub rate limits block ingestion | 2 | Proactive backoff, caching, conditional requests |

## Definition of Done

Each sprint is complete when:
1. All acceptance criteria checked
2. Tests pass (`pytest verification/tests/`)
3. No linting errors
4. Code reviewed and audited
