"""GitHub REST API v3 client for ground truth ingestion."""

from __future__ import annotations

import asyncio
import logging
import random
import re
from datetime import datetime, timezone
from pathlib import Path

import httpx

from echelon_verify.config import IngestionConfig
from echelon_verify.models import GroundTruthRecord

logger = logging.getLogger(__name__)

_MAX_DIFF_BYTES = 100_000  # 100 KB
_RATE_LIMIT_FLOOR = 10
_MAX_BACKOFF_SECONDS = 60
_MAX_PROACTIVE_WAIT_SECONDS = 300  # Cap proactive wait at 5 minutes
_OWNER_REPO_PATTERN = re.compile(r"^[a-zA-Z0-9._-]+$")


def _parse_repo(repo_url: str) -> tuple[str, str]:
    """Extract owner and repo name from a GitHub URL.

    Accepts:
      - https://github.com/owner/repo
      - https://github.com/owner/repo.git
      - owner/repo

    Validates owner and repo contain only safe characters.
    """
    match = re.match(
        r"(?:https://github\.com/)?([^/]+)/([^/.]+?)(?:\.git)?/?$",
        repo_url.strip(),
    )
    if not match:
        raise ValueError(f"Invalid GitHub repo URL: {repo_url}")

    owner, repo = match.group(1), match.group(2)

    # Validate characters to prevent path injection
    if not _OWNER_REPO_PATTERN.match(owner):
        raise ValueError(f"Invalid owner name: {owner}")
    if not _OWNER_REPO_PATTERN.match(repo):
        raise ValueError(f"Invalid repo name: {repo}")

    return owner, repo


def _truncate_diff(diff: str, max_bytes: int = _MAX_DIFF_BYTES) -> str:
    """Truncate a diff to changed hunks only if it exceeds max_bytes."""
    if len(diff.encode()) <= max_bytes:
        return diff

    logger.info("Diff exceeds %d bytes, truncating to hunks", max_bytes)
    lines = diff.splitlines(keepends=True)
    kept: list[str] = []
    current_size = 0

    for line in lines:
        # Keep diff headers and hunk markers unconditionally
        if line.startswith(("diff --git", "---", "+++", "@@")):
            kept.append(line)
            current_size += len(line.encode())
            continue
        # Keep changed lines (+ or -) up to budget
        if line.startswith(("+", "-")):
            line_size = len(line.encode())
            if current_size + line_size > max_bytes:
                kept.append("+... [truncated]\n")
                break
            kept.append(line)
            current_size += line_size
        # Skip context lines to save space

    return "".join(kept)


def _extract_files_changed(diff: str) -> list[str]:
    """Extract file paths from a unified diff, including binary files."""
    files: list[str] = []
    for line in diff.splitlines():
        if line.startswith("+++ b/"):
            path = line[6:]
            if path != "/dev/null":
                files.append(path)
        elif line.startswith("Binary files") and " b/" in line:
            # Binary files a/... and b/... differ
            match = re.search(r"b/(\S+)", line)
            if match:
                files.append(match.group(1))
    return files


class GitHubIngester:
    """Async GitHub REST API v3 client for extracting ground truth records."""

    def __init__(self, config: IngestionConfig) -> None:
        self._config = config
        self._owner, self._repo = _parse_repo(config.repo_url)
        headers: dict[str, str] = {
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if config.github_token:
            headers["Authorization"] = f"Bearer {config.github_token}"
        self._client = httpx.AsyncClient(
            base_url="https://api.github.com",
            headers=headers,
            timeout=30.0,
            max_redirects=0,  # Don't follow redirects to prevent SSRF
        )
        self._rate_limit_remaining: int = 60
        self._rate_limit_reset: datetime = datetime.now(tz=timezone.utc)
        self._etags: dict[str, str] = {}

    async def close(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> "GitHubIngester":
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.close()

    async def ingest(
        self, cached_ids: set[str] | None = None
    ) -> list[GroundTruthRecord]:
        """Fetch merged PRs, extract diffs, return structured records.

        Args:
            cached_ids: Set of PR IDs already ingested. If provided, PRs
                        with these IDs are skipped (incremental ingestion).
        """
        prs = await self._fetch_prs()
        records: list[GroundTruthRecord] = []

        for pr in prs:
            pr_id = str(pr["number"])
            if cached_ids and pr_id in cached_ids:
                logger.debug("Skipping cached PR #%s", pr_id)
                continue

            try:
                diff = await self._fetch_diff(pr["number"])
                files = _extract_files_changed(diff) or [
                    f.get("filename", "")
                    for f in pr.get("files", [])
                ]
                record = GroundTruthRecord(
                    id=pr_id,
                    title=pr.get("title", ""),
                    description=pr.get("body", "") or "",
                    diff_content=_truncate_diff(diff),
                    files_changed=files,
                    timestamp=datetime.fromisoformat(
                        pr["merged_at"].replace("Z", "+00:00")
                    ),
                    labels=[l["name"] for l in pr.get("labels", [])],
                    author=pr.get("user", {}).get("login", "unknown"),
                    url=pr.get("html_url", ""),
                    repo=f"{self._owner}/{self._repo}",
                )
                records.append(record)
            except Exception:
                logger.exception("Failed to process PR #%s", pr.get("number"))
                continue

        return records

    async def _fetch_prs(self) -> list[dict]:
        """Paginated PR listing with rate limit handling and ETag support."""
        all_prs: list[dict] = []
        page = 1
        per_page = min(self._config.limit, 100)

        while len(all_prs) < self._config.limit:
            await self._check_rate_limit()

            params: dict[str, str | int] = {
                "state": "closed",
                "sort": "updated",
                "direction": "desc",
                "per_page": per_page,
                "page": page,
            }

            # Conditional request with ETag
            extra_headers: dict[str, str] = {}
            cache_key = f"pulls:page={page}"
            if cache_key in self._etags:
                extra_headers["If-None-Match"] = self._etags[cache_key]

            resp = await self._client.get(
                f"/repos/{self._owner}/{self._repo}/pulls",
                params=params,
                headers=extra_headers,
            )
            self._update_rate_limit(resp)

            if resp.status_code == 403:
                await self._handle_rate_limit(resp)
                continue

            # 304 Not Modified — use cached data
            if resp.status_code == 304:
                break

            resp.raise_for_status()

            # Store ETag for future conditional requests
            etag = resp.headers.get("etag")
            if etag:
                self._etags[cache_key] = etag

            page_data = resp.json()

            if not page_data:
                break

            for pr in page_data:
                # Filter: merged PRs only (when merged_only=True)
                if self._config.merged_only and not pr.get("merged_at"):
                    continue

                # Include unmerged closed PRs only when merged_only=False
                if not self._config.merged_only and not pr.get("merged_at"):
                    pass  # Include all closed PRs

                # Label filter
                if self._config.labels:
                    pr_labels = {l["name"] for l in pr.get("labels", [])}
                    if not pr_labels.intersection(self._config.labels):
                        continue

                # Date filter
                if self._config.since:
                    merged_at = pr.get("merged_at", "")
                    if merged_at and merged_at < self._config.since:
                        continue

                all_prs.append(pr)
                if len(all_prs) >= self._config.limit:
                    break

            # Check for next page via Link header
            link = resp.headers.get("link", "")
            if 'rel="next"' not in link:
                break
            page += 1

        return all_prs

    async def _fetch_diff(self, pr_number: int) -> str:
        """Fetch unified diff for a single PR."""
        await self._check_rate_limit()

        resp = await self._client.get(
            f"/repos/{self._owner}/{self._repo}/pulls/{pr_number}",
            headers={"Accept": "application/vnd.github.v3.diff"},
        )
        self._update_rate_limit(resp)

        if resp.status_code == 403:
            await self._handle_rate_limit(resp)
            # Retry once after backoff
            resp = await self._client.get(
                f"/repos/{self._owner}/{self._repo}/pulls/{pr_number}",
                headers={"Accept": "application/vnd.github.v3.diff"},
            )
            resp.raise_for_status()

        resp.raise_for_status()
        return resp.text

    def _update_rate_limit(self, resp: httpx.Response) -> None:
        """Update rate limit tracking from response headers."""
        remaining = resp.headers.get("x-ratelimit-remaining")
        if remaining is not None:
            try:
                self._rate_limit_remaining = int(remaining)
            except ValueError:
                pass
        reset = resp.headers.get("x-ratelimit-reset")
        if reset is not None:
            try:
                self._rate_limit_reset = datetime.fromtimestamp(
                    int(reset), tz=timezone.utc
                )
            except (ValueError, OSError):
                pass

    async def _check_rate_limit(self) -> None:
        """Proactive backoff when rate limit is low."""
        if self._rate_limit_remaining < _RATE_LIMIT_FLOOR:
            wait = max(
                0,
                (self._rate_limit_reset - datetime.now(tz=timezone.utc)).total_seconds(),
            )
            # Cap wait to prevent unbounded sleep from spoofed headers
            wait = min(wait, _MAX_PROACTIVE_WAIT_SECONDS)
            if wait > 0:
                logger.warning(
                    "Rate limit low (%d remaining), sleeping %.1fs",
                    self._rate_limit_remaining,
                    wait,
                )
                await asyncio.sleep(wait)

    async def _handle_rate_limit(self, response: httpx.Response) -> None:
        """Exponential backoff with jitter when rate limited (403)."""
        backoff = 1.0
        for _ in range(5):
            # Add jitter: ±25% randomization
            jittered = backoff * (0.75 + random.random() * 0.5)
            logger.warning("Rate limited, backing off %.1fs", jittered)
            await asyncio.sleep(jittered)
            backoff = min(backoff * 2, _MAX_BACKOFF_SECONDS)

            # Check if reset time has passed
            if datetime.now(tz=timezone.utc) >= self._rate_limit_reset:
                return
