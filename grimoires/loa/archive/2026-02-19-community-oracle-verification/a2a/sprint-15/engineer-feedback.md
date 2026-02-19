# Sprint 15 (cycle-027 sprint-2) — Engineer Feedback

**Reviewer**: Senior Tech Lead
**Date**: 2026-02-19
**Verdict**: Issues found — 5 acceptance criteria gaps, 1 code defect

---

## Acceptance Criteria Checklist

### 2.1 — GitHubIngester core: PASS

All criteria met. `ingest()` returns `list[GroundTruthRecord]`, fetches merged PRs only, extracts unified diff, supports pagination via Link header, populates all fields, uses `httpx.AsyncClient`.

### 2.2 — Rate limit handling: FAIL (2 gaps)

| # | Criterion | Status | Detail |
|---|-----------|--------|--------|
| 1 | Reads `X-RateLimit-Remaining` and `X-RateLimit-Reset` headers | PASS | `_update_rate_limit()` at github.py:229-238 |
| 2 | Proactive backoff when remaining < 10 | PASS | `_check_rate_limit()` at github.py:240-253 |
| 3 | **Exponential backoff with jitter on 403** | **FAIL** | github.py:255-265 — backoff doubles correctly (1, 2, 4... max 60) but **jitter is missing**. Sprint plan explicitly requires "Exponential backoff with jitter on 403 rate limit". Add random jitter (e.g., `backoff * (0.5 + random.random())`) to prevent thundering herd. |
| 4 | **Supports conditional requests with `If-None-Match` / ETags** | **FAIL** | github.py:99 declares `self._etags: dict[str, str] = {}` but the dict is **never populated or used**. No `If-None-Match` header is sent on any request. No ETag is read from response headers. This is dead code. |

**Fix for jitter** — `github.py:261`:
```python
# Current:
backoff = min(backoff * 2, _MAX_BACKOFF_SECONDS)
# Should be:
import random
backoff = min(backoff * 2 * (0.5 + random.random()), _MAX_BACKOFF_SECONDS)
```

**Fix for ETags** — `github.py:99` and `_fetch_prs()`:
1. In `_fetch_prs()`, after a successful response, store `resp.headers.get("etag")` keyed by the request URL.
2. On subsequent requests to the same URL, send `If-None-Match: <etag>` header.
3. Handle 304 Not Modified response (return empty/cached data, do not count against rate limit).

### 2.3 — Caching and incremental ingestion: FAIL (1 gap)

| # | Criterion | Status | Detail |
|---|-----------|--------|--------|
| 1 | Records written to `data/{owner}_{repo}/ground_truth.jsonl` via `Storage.append_jsonl()` | PASS | Verified in test_storage_round_trip (test_ingestion.py:316-328) |
| 2 | **Re-ingestion reads existing cache, only fetches PRs newer than last timestamp** | **FAIL** | There is **no automatic incremental re-ingestion logic**. `ingest()` always fetches all PRs from GitHub. It does not read from the existing JSONL cache to determine what has already been ingested. The `--since` parameter is manual, not automatic. The sprint plan requires: "Re-ingestion reads existing cache, only fetches PRs newer than last timestamp." |
| 3 | `--since` CLI option filters PRs by date | PASS | `IngestionConfig.since` field exists, used at github.py:190-193 |

**Fix**: Add a method or constructor logic that reads the last record's `timestamp` from the existing JSONL cache and auto-sets `self._config.since` when no explicit since is provided.

### 2.4 — Diff handling: FAIL (1 gap)

| # | Criterion | Status | Detail |
|---|-----------|--------|--------|
| 1 | Diffs >100KB truncated to changed hunks only | PASS | `_truncate_diff()` at github.py:40-66 |
| 2 | **Binary files noted in `files_changed` but omitted from `diff_content`** | **PARTIAL** | Binary files are passively skipped (they have no `+++ b/` line in unified diff, so `_extract_files_changed` won't extract them), but they are NOT "noted in `files_changed`". The criterion says binary files should appear in `files_changed` even though their content is omitted from `diff_content`. Binary diffs typically show `Binary files a/... and b/... differ` — this pattern should be parsed. |
| 3 | Truncation logged at INFO level | PASS | github.py:45 `logger.info(...)` |

**Fix**: In `_extract_files_changed()` at github.py:69-77, add detection for binary file lines:
```python
if line.startswith("Binary files") and " and b/" in line:
    # Extract path from "Binary files a/foo and b/foo differ"
    match = re.search(r"and b/(.+?) differ", line)
    if match:
        files.append(match.group(1))
```

### 2.5 — Tests for ingestion: FAIL (2 missing tests)

| # | Criterion | Status | Detail |
|---|-----------|--------|--------|
| 1 | Mock GitHub API responses (PR listing, diff, pagination, rate limit) | PASS | PR listing and diff mocked across all tests |
| 2 | Test: pagination fetches all pages | PASS | `test_pagination` at test_ingestion.py:211-273 |
| 3 | **Test: rate limit triggers backoff** | **FAIL** | No test mocks a 403 response to verify backoff behavior. This is explicitly required. |
| 4 | Test: large diff truncation | PASS | `test_large_diff_truncated` at test_ingestion.py:94-101 |
| 5 | **Test: cache hit skips re-fetch** | **FAIL** | No test for incremental/cache behavior. This is coupled with the 2.3 gap above — the feature doesn't exist yet, so neither does the test. |
| 6 | Test: `GroundTruthRecord` fields populated correctly | PASS | `test_ground_truth_fields_populated` at test_ingestion.py:275-314 |
| 7 | Test fixture: `tests/fixtures/sample_pr.json` | PASS | File exists at `verification/tests/fixtures/sample_pr.json` |

---

## Code Defect

**Redundant merged_at check** — `github.py:177-180`:

```python
if not pr.get("merged_at"):       # line 177 — filters out unmerged
    continue
if self._config.merged_only and not pr.get("merged_at"):  # line 180 — dead code
    continue
```

Line 180 is unreachable: if `merged_at` is falsy, line 177 already skips it. The unconditional check on line 177 means the `merged_only` config flag is effectively ignored — even when `merged_only=False`, unmerged PRs are still skipped. If the intent is to sometimes include unmerged PRs, line 177 should be guarded by `if self._config.merged_only`. If the intent is to always filter merged-only, remove line 180 as dead code.

**Fix**: Replace lines 177-180 with:
```python
if self._config.merged_only and not pr.get("merged_at"):
    continue
```

---

## Summary of Required Fixes

| Priority | File | Line(s) | Issue |
|----------|------|---------|-------|
| P1 | `ingestion/github.py` | 99, 160 | ETags declared but never used — implement `If-None-Match` conditional requests |
| P1 | `ingestion/github.py` | 261 | Missing jitter in exponential backoff |
| P1 | `ingestion/github.py` | (new) | No auto-incremental re-ingestion from cached JSONL |
| P2 | `ingestion/github.py` | 69-77 | Binary files not noted in `files_changed` |
| P2 | `ingestion/github.py` | 177-180 | Redundant/dead merged_at check — `merged_only` flag ignored |
| P2 | `tests/test_ingestion.py` | (missing) | No test for 403 rate-limit backoff |
| P2 | `tests/test_ingestion.py` | (missing) | No test for cache-hit skip re-fetch |

5 acceptance criteria not fully met. 1 code defect. Please address and re-submit for review.
