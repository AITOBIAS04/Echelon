"""GitHub PR ingester — fetches merged PRs and maps them to GroundTruthRecords."""

from __future__ import annotations

import logging
import re
from datetime import datetime, timezone

import httpx

from theatre.integration.models import GroundTruthRecord

logger = logging.getLogger(__name__)

# Cycle-027 convention: truncate diffs larger than 100 KB.
_MAX_DIFF_BYTES = 100 * 1024


def _truncate_diff(diff: str, max_bytes: int = _MAX_DIFF_BYTES) -> str:
    """Truncate a diff to at most *max_bytes* UTF-8 bytes without splitting a character."""
    encoded = diff.encode("utf-8")
    if len(encoded) <= max_bytes:
        return diff
    # Decode back, ignoring the last possibly-incomplete character.
    return encoded[:max_bytes].decode("utf-8", errors="ignore") + "\n... [truncated]"


def _parse_files_from_diff(diff: str) -> list[str]:
    """Extract changed file paths from unified diff ``diff --git`` headers."""
    return re.findall(r"^diff --git a/.+ b/(.+)$", diff, re.MULTILINE)


def _parse_iso_timestamp(value: str | None) -> datetime:
    """Parse a GitHub ISO-8601 timestamp, falling back to now(UTC)."""
    if not value:
        return datetime.now(timezone.utc)
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return datetime.now(timezone.utc)


class GitHubIngester:
    """Fetch merged PRs from the GitHub REST API and return GroundTruthRecords."""

    _BASE = "https://api.github.com"

    def __init__(self, token: str | None = None, timeout: float = 30.0) -> None:
        headers: dict[str, str] = {"Accept": "application/vnd.github+json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        self._client = httpx.AsyncClient(
            base_url=self._BASE,
            headers=headers,
            timeout=timeout,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def ingest(self, repo: str, limit: int = 10) -> list[GroundTruthRecord]:
        """Return up to *limit* merged-PR GroundTruthRecords for *repo*.

        Parameters
        ----------
        repo:
            ``owner/repo`` slug (e.g. ``AITOBIAS04/Echelon``).
        limit:
            Maximum number of merged PRs to return.
        """
        merged_prs = await self._fetch_merged_prs(repo, limit)
        logger.info("Fetched %d merged PRs from %s", len(merged_prs), repo)

        records: list[GroundTruthRecord] = []
        for pr in merged_prs:
            try:
                diff = await self._fetch_diff(repo, pr["number"])
                records.append(self._map_to_record(pr, diff, repo))
            except Exception:
                logger.exception("Skipping PR #%s — failed to fetch diff", pr.get("number"))
        return records

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _fetch_merged_prs(self, repo: str, limit: int) -> list[dict]:
        """Paginate ``/repos/{repo}/pulls`` until *limit* merged PRs collected."""
        merged: list[dict] = []
        page = 1
        per_page = min(limit, 100)

        while len(merged) < limit:
            resp = await self._client.get(
                f"/repos/{repo}/pulls",
                params={
                    "state": "closed",
                    "sort": "updated",
                    "direction": "desc",
                    "per_page": per_page,
                    "page": page,
                },
            )
            resp.raise_for_status()
            items = resp.json()

            if not items:
                break  # No more pages

            for pr in items:
                if pr.get("merged_at"):
                    merged.append(pr)
                    if len(merged) >= limit:
                        break

            page += 1

        return merged

    async def _fetch_diff(self, repo: str, pr_number: int) -> str:
        """Fetch the unified diff for a single PR."""
        resp = await self._client.get(
            f"/repos/{repo}/pulls/{pr_number}",
            headers={"Accept": "application/vnd.github.v3.diff"},
        )
        resp.raise_for_status()
        return _truncate_diff(resp.text)

    @staticmethod
    def _map_to_record(pr: dict, diff: str, repo: str) -> GroundTruthRecord:
        """Map a GitHub PR JSON object + diff to a GroundTruthRecord."""
        return GroundTruthRecord(
            id=f"PR-{pr['number']}",
            title=pr.get("title", ""),
            description=pr.get("body") or "",
            diff_content=diff,
            files_changed=_parse_files_from_diff(diff),
            timestamp=_parse_iso_timestamp(pr.get("merged_at")),
            labels=[label["name"] for label in pr.get("labels", [])],
            author=(pr.get("user") or {}).get("login", ""),
            url=pr.get("html_url", ""),
            repo=repo,
        )
