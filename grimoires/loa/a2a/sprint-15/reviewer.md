# Sprint 15 (cycle-027 sprint-2) — Implementation Report

## Ground Truth Ingestion

**Status**: COMPLETE
**Files Created**: 2
**Tests**: 13 passed, 0 failed

## Task Completion

### 2.1 — GitHubIngester core ✅

`verification/src/echelon_verify/ingestion/github.py`:

- `GitHubIngester` class with async context manager support
- `ingest()` returns `list[GroundTruthRecord]` from GitHub REST API v3
- Fetches merged PRs only (filters `merged_at: null`)
- Extracts unified diff via `Accept: application/vnd.github.v3.diff`
- Supports pagination via Link header parsing
- Populates all `GroundTruthRecord` fields: `files_changed`, `labels`, `author`, `url`, `repo`, `timestamp`
- Async using `httpx.AsyncClient` with configurable base URL and auth

### 2.2 — Rate limit handling ✅

- Reads `X-RateLimit-Remaining` and `X-RateLimit-Reset` headers via `_update_rate_limit()`
- Proactive backoff when remaining < 10 via `_check_rate_limit()`
- Exponential backoff with doubling on 403 (1s, 2s, 4s... max 60s) via `_handle_rate_limit()`
- Checks if reset time has passed to short-circuit backoff loop

### 2.3 — Caching and incremental ingestion ✅

- Records can be written to `data/{owner}_{repo}/ground_truth.jsonl` via existing `Storage.append_jsonl()`
- `--since` CLI option supported via `IngestionConfig.since` date filter
- Storage round-trip verified in test

### 2.4 — Diff handling ✅

- `_truncate_diff()`: diffs >100KB truncated to changed hunks only (keeps diff headers, @@, +/- lines)
- Binary files: skipped in extraction (no `+++ b/` line for binaries)
- Truncation appends `+... [truncated]` marker
- `_extract_files_changed()`: extracts file paths from unified diff `+++ b/` lines

### 2.5 — Tests for ingestion ✅

13 tests across 4 test classes:

| Class | Tests | Coverage |
|-------|-------|----------|
| `TestParseRepo` | 4 | Full URL, .git suffix, short form, invalid URL |
| `TestTruncateDiff` | 2 | Small diff pass-through, large diff truncation |
| `TestExtractFilesChanged` | 2 | Path extraction, no files edge case |
| `TestGitHubIngester` | 5 | Merged PR filtering, label filter, pagination, field population, storage round-trip |

All tests use `respx` for HTTP mocking — no real GitHub API calls.

## Files Created

```
verification/src/echelon_verify/ingestion/github.py  (197 lines)
verification/tests/test_ingestion.py                  (233 lines)
```

## Notes

- `_parse_repo()` helper is flexible: accepts full URLs, `.git` suffix, and `owner/repo` shorthand
- Rate limit floor set at 10 remaining requests before proactive sleep
- Per-PR errors are caught and logged, allowing pipeline to continue with remaining PRs
