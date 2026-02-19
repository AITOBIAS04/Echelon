"""GitHub REST API v3 client for ground truth ingestion."""

from __future__ import annotations

import asyncio
import logging
import re
import time
from datetime import datetime, timezone

import httpx

from echelon_verify.config import IngestionConfig
from echelon_verify.models import GroundTruthRecord

logger = logging.getLogger(__name__)

_MAX_DIFF_BYTES = 100_000  # 100 KB
_RATE_LIMIT_FLOOR = 10
_MAX_BACKOFF_SECONDS = 60


def _parse_repo(repo_url: str) -> tuple[str, str]:
    """Extract owner and repo name from a GitHub URL.

    Accepts:
      - https://github.com/owner/repo
      - https://github.com/owner/repo.git
      - owner/repo
    """
    match = re.match(
        r"(?:https?://github\.com/)?([^/]+)/([^/.]+?)(?:\.git)?/?$",
        repo_url.strip(),
    )
    if not match:
        raise ValueError(f"Invalid GitHub repo URL: {repo_url}")
    return match.group(1), match.group(2)


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
    """Extract file paths from a unified diff."""
    files: list[str] = []
    for line in diff.splitlines():
        if line.startswith("+++ b/"):
            path = line[6:]
            if path != "/dev/null":
                files.append(path)
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

    async def ingest(self) -> list[GroundTruthRecord]:
        """Fetch merged PRs, extract diffs, return structured records."""
        prs = await self._fetch_prs()
        records: list[GroundTruthRecord] = []

        for pr in prs:
            try:
                diff = await self._fetch_diff(pr["number"])
                files = _extract_files_changed(diff) or [
                    f.get("filename", "")
                    for f in pr.get("files", [])
                ]
                record = GroundTruthRecord(
                    id=str(pr["number"]),
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
        """Paginated PR listing with rate limit handling."""
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

            resp = await self._client.get(
                f"/repos/{self._owner}/{self._repo}/pulls",
                params=params,
            )
            self._update_rate_limit(resp)

            if resp.status_code == 403:
                await self._handle_rate_limit(resp)
                continue

            resp.raise_for_status()
            page_data = resp.json()

            if not page_data:
                break

            for pr in page_data:
                if not pr.get("merged_at"):
                    continue

                if self._config.merged_only and not pr.get("merged_at"):
                    continue

                # Label filter
                if self._config.labels:
                    pr_labels = {l["name"] for l in pr.get("labels", [])}
                    if not pr_labels.intersection(self._config.labels):
                        continue

                # Date filter
                if self._config.since:
                    merged_at = pr["merged_at"]
                    if merged_at < self._config.since:
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
            self._rate_limit_remaining = int(remaining)
        reset = resp.headers.get("x-ratelimit-reset")
        if reset is not None:
            self._rate_limit_reset = datetime.fromtimestamp(
                int(reset), tz=timezone.utc
            )

    async def _check_rate_limit(self) -> None:
        """Proactive backoff when rate limit is low."""
        if self._rate_limit_remaining < _RATE_LIMIT_FLOOR:
            wait = max(
                0,
                (self._rate_limit_reset - datetime.now(tz=timezone.utc)).total_seconds(),
            )
            if wait > 0:
                logger.warning(
                    "Rate limit low (%d remaining), sleeping %.1fs",
                    self._rate_limit_remaining,
                    wait,
                )
                await asyncio.sleep(wait)

    async def _handle_rate_limit(self, response: httpx.Response) -> None:
        """Exponential backoff when rate limited (403)."""
        backoff = 1.0
        for _ in range(5):
            logger.warning("Rate limited, backing off %.1fs", backoff)
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, _MAX_BACKOFF_SECONDS)

            # Check if reset time has passed
            if datetime.now(tz=timezone.utc) >= self._rate_limit_reset:
                return
