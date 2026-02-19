# Sprint 18 (local sprint-5) — Implementation Report

## Pipeline Orchestrator + CLI + API

### Tasks Completed

#### 5.1 — Pipeline orchestrator (`pipeline.py`) ✓
- `run()` executes full pipeline: ingest → (for each PR: generate question → invoke oracle → score) → certify
- `ingest_only()` runs stage 1 only with incremental ingestion (cached_ids)
- `score_only()` runs stages 2-4 from cached data
- Progress callback reports `(completed, total)` per replay
- Single replay failure: logged, skipped, pipeline continues
- Partial certificate warning when below min_replays
- All intermediate results written to JSONL as they complete (oracle_outputs + replay_scores)

#### 5.2 — CLI (`cli.py`) ✓
- `echelon verify` — full pipeline with all options
- `echelon ingest` — fetch and cache ground truth
- `echelon score` — score cached data, generate certificate
- `echelon inspect` — display certificate in human-readable format
- `--verbose` shows per-replay progress bar
- `--dry-run` ingests without invoking oracle
- Entry point registered in `pyproject.toml`
- `asyncio.run()` wrapper for async commands

#### 5.3 — FastAPI API (`api.py`) ✓
- `POST /api/verification/run` — starts async verification, returns job ID
- `GET /api/verification/status/{job_id}` — returns progress
- `GET /api/verification/result/{job_id}` — returns certificate (409 if not complete)
- `GET /api/verification/certificates` — lists all stored certificates
- 404 for unknown job_id
- Background task execution via `asyncio.create_task()`

#### 5.4 — Standalone server (`server.py`) ✓
- `python -m echelon_verify.server` starts uvicorn on port 8100
- Mounts verification router at `/api/verification`
- Health check at `/health`

#### 5.5 — E2E tests ✓
- **test_pipeline.py** (5 tests): Full E2E with mock services → certificate; aggregate score verification; partial failure (1/3 fails) → 2-replay certificate; progress callback verification; no cached data error
- **test_api.py** (4 tests): Health endpoint; 404 on unknown status/result; empty certificate list

### Test Results

94 tests passing (9 new in this sprint), 0 failures.

### Files Created

| File | Action | Lines |
|------|--------|-------|
| `pipeline.py` | Created | 196 |
| `cli.py` | Created | 195 |
| `api.py` | Created | 117 |
| `server.py` | Created | 26 |
| `tests/test_pipeline.py` | Created | 205 |
| `tests/test_api.py` | Created | 28 |

### Notes

- Fixed inconsistent repo_key format between `run()` and `score_only()` during review
- `OracleOutput` import moved from TYPE_CHECKING to runtime since pipeline uses it at runtime
- API uses in-memory job tracking (module-level dicts) — suitable for single-process deployment
