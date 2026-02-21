"""Tests for GitHubIngester — mocked httpx, no API keys needed."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from theatre.integration.github_ingester import (
    GitHubIngester,
    _parse_files_from_diff,
    _parse_iso_timestamp,
    _truncate_diff,
)
from theatre.integration.models import GroundTruthRecord


# ── Fixtures ──────────────────────────────────────────────────────────

SAMPLE_DIFF = """\
diff --git a/src/main.py b/src/main.py
index abc1234..def5678 100644
--- a/src/main.py
+++ b/src/main.py
@@ -1,3 +1,4 @@
+import os
 import sys

 def main():
diff --git a/README.md b/README.md
index 1111111..2222222 100644
--- a/README.md
+++ b/README.md
@@ -1 +1,2 @@
 # Project
+Updated readme
"""


def _make_pr(number: int, merged: bool = True, title: str = "Test PR") -> dict:
    """Build a minimal GitHub PR JSON object."""
    return {
        "number": number,
        "title": title,
        "body": f"Description for PR #{number}",
        "merged_at": "2025-06-15T10:30:00Z" if merged else None,
        "html_url": f"https://github.com/owner/repo/pull/{number}",
        "user": {"login": "testuser"},
        "labels": [{"name": "enhancement"}],
    }


# ── Helper: _truncate_diff ────────────────────────────────────────────


class TestTruncateDiff:
    def test_short_diff_unchanged(self):
        assert _truncate_diff("abc") == "abc"

    def test_exact_limit_unchanged(self):
        data = "x" * 100
        assert _truncate_diff(data, max_bytes=100) == data

    def test_over_limit_truncated(self):
        data = "x" * 200
        result = _truncate_diff(data, max_bytes=100)
        assert result.endswith("\n... [truncated]")
        # The body before the suffix must be <= 100 bytes
        body = result.split("\n... [truncated]")[0]
        assert len(body.encode("utf-8")) <= 100

    def test_utf8_boundary_safe(self):
        # Multi-byte character (3 bytes in UTF-8)
        data = "\u2603" * 50  # 150 bytes
        result = _truncate_diff(data, max_bytes=100)
        # Should not raise and should be valid UTF-8
        result.encode("utf-8")
        assert result.endswith("\n... [truncated]")


# ── Helper: _parse_files_from_diff ────────────────────────────────────


class TestParseFilesFromDiff:
    def test_standard_diff(self):
        files = _parse_files_from_diff(SAMPLE_DIFF)
        assert files == ["src/main.py", "README.md"]

    def test_empty_diff(self):
        assert _parse_files_from_diff("") == []

    def test_single_file(self):
        diff = "diff --git a/foo.txt b/foo.txt\n"
        assert _parse_files_from_diff(diff) == ["foo.txt"]


# ── Helper: _parse_iso_timestamp ──────────────────────────────────────


class TestParseIsoTimestamp:
    def test_valid_github_timestamp(self):
        ts = _parse_iso_timestamp("2025-06-15T10:30:00Z")
        assert ts.year == 2025
        assert ts.month == 6
        assert ts.day == 15

    def test_empty_string_returns_now(self):
        ts = _parse_iso_timestamp("")
        assert isinstance(ts, datetime)

    def test_none_returns_now(self):
        ts = _parse_iso_timestamp(None)
        assert isinstance(ts, datetime)

    def test_invalid_returns_now(self):
        ts = _parse_iso_timestamp("not-a-date")
        assert isinstance(ts, datetime)


# ── Header building ───────────────────────────────────────────────────


class TestHeaders:
    def test_authenticated_headers(self):
        ingester = GitHubIngester(token="ghp_test123")
        headers = ingester._client.headers
        assert headers["authorization"] == "Bearer ghp_test123"
        assert "application/vnd.github+json" in headers["accept"]

    def test_unauthenticated_headers(self):
        ingester = GitHubIngester(token=None)
        headers = ingester._client.headers
        assert "authorization" not in headers
        assert "application/vnd.github+json" in headers["accept"]


# ── Ingestion tests ──────────────────────────────────────────────────


def _mock_response(json_data=None, text_data=None, status_code=200):
    """Build a mock httpx.Response."""
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = status_code
    resp.json.return_value = json_data or []
    resp.text = text_data or ""
    resp.raise_for_status = MagicMock()
    if status_code >= 400:
        resp.raise_for_status.side_effect = httpx.HTTPStatusError(
            message=f"HTTP {status_code}",
            request=MagicMock(),
            response=resp,
        )
    return resp


class TestIngest:
    @pytest.mark.asyncio
    async def test_filters_merged_prs_only(self):
        """Only PRs with merged_at should be returned."""
        prs = [_make_pr(1, merged=True), _make_pr(2, merged=False), _make_pr(3, merged=True)]

        ingester = GitHubIngester(token="tok")
        ingester._client.get = AsyncMock(side_effect=[
            _mock_response(json_data=prs),           # list page 1
            _mock_response(json_data=[]),             # list page 2 (empty → stop)
            _mock_response(text_data=SAMPLE_DIFF),   # diff for PR #1
            _mock_response(text_data=SAMPLE_DIFF),   # diff for PR #3
        ])

        records = await ingester.ingest("owner/repo", limit=10)
        assert len(records) == 2
        assert records[0].id == "PR-1"
        assert records[1].id == "PR-3"

    @pytest.mark.asyncio
    async def test_pagination(self):
        """When first page has fewer merged PRs than limit, fetches next page."""
        page1 = [_make_pr(1, merged=False), _make_pr(2, merged=True)]
        page2 = [_make_pr(3, merged=True)]
        page3: list[dict] = []  # empty → stop

        ingester = GitHubIngester(token="tok")
        ingester._client.get = AsyncMock(side_effect=[
            _mock_response(json_data=page1),         # list page 1
            _mock_response(json_data=page2),         # list page 2
            _mock_response(json_data=page3),         # list page 3 (empty)
            _mock_response(text_data=SAMPLE_DIFF),   # diff for PR #2
            _mock_response(text_data=SAMPLE_DIFF),   # diff for PR #3
        ])

        records = await ingester.ingest("owner/repo", limit=5)
        assert len(records) == 2

    @pytest.mark.asyncio
    async def test_limit_enforced(self):
        """Should stop collecting once limit is reached."""
        prs = [_make_pr(i, merged=True) for i in range(1, 6)]

        ingester = GitHubIngester(token="tok")

        call_responses = [_mock_response(json_data=prs)]
        for _ in range(3):
            call_responses.append(_mock_response(text_data=SAMPLE_DIFF))

        ingester._client.get = AsyncMock(side_effect=call_responses)

        records = await ingester.ingest("owner/repo", limit=3)
        assert len(records) == 3

    @pytest.mark.asyncio
    async def test_empty_repo(self):
        """An empty repo should return an empty list."""
        ingester = GitHubIngester(token="tok")
        ingester._client.get = AsyncMock(return_value=_mock_response(json_data=[]))

        records = await ingester.ingest("owner/empty", limit=5)
        assert records == []


# ── Record mapping ────────────────────────────────────────────────────


class TestRecordMapping:
    def test_all_fields_populated(self):
        pr = _make_pr(42, merged=True, title="Add feature X")
        record = GitHubIngester._map_to_record(pr, SAMPLE_DIFF, "owner/repo")

        assert record.id == "PR-42"
        assert record.title == "Add feature X"
        assert record.description == "Description for PR #42"
        assert "import os" in record.diff_content
        assert record.files_changed == ["src/main.py", "README.md"]
        assert record.labels == ["enhancement"]
        assert record.author == "testuser"
        assert record.url == "https://github.com/owner/repo/pull/42"
        assert record.repo == "owner/repo"
        assert isinstance(record.timestamp, datetime)

    def test_none_body_becomes_empty_string(self):
        pr = _make_pr(1)
        pr["body"] = None
        record = GitHubIngester._map_to_record(pr, "", "owner/repo")
        assert record.description == ""

    def test_labels_extraction(self):
        pr = _make_pr(1)
        pr["labels"] = [{"name": "bug"}, {"name": "critical"}]
        record = GitHubIngester._map_to_record(pr, "", "owner/repo")
        assert record.labels == ["bug", "critical"]

    def test_missing_user_login(self):
        pr = _make_pr(1)
        pr["user"] = None
        record = GitHubIngester._map_to_record(pr, "", "owner/repo")
        assert record.author == ""


# ── Error handling ────────────────────────────────────────────────────


class TestErrorHandling:
    @pytest.mark.asyncio
    async def test_single_pr_diff_failure_skipped(self):
        """If one PR's diff fetch fails, it's skipped and others succeed."""
        prs = [_make_pr(1, merged=True), _make_pr(2, merged=True)]

        ingester = GitHubIngester(token="tok")
        ingester._client.get = AsyncMock(side_effect=[
            _mock_response(json_data=prs),            # list page 1
            _mock_response(json_data=[]),              # list page 2 (empty → stop)
            _mock_response(status_code=500),           # diff for PR #1 fails
            _mock_response(text_data=SAMPLE_DIFF),     # diff for PR #2 OK
        ])

        records = await ingester.ingest("owner/repo", limit=10)
        assert len(records) == 1
        assert records[0].id == "PR-2"

    @pytest.mark.asyncio
    async def test_http_404_propagated(self):
        """A 404 on the list endpoint should propagate as HTTPStatusError."""
        ingester = GitHubIngester(token="tok")
        ingester._client.get = AsyncMock(return_value=_mock_response(status_code=404))

        with pytest.raises(httpx.HTTPStatusError):
            await ingester.ingest("owner/nonexistent", limit=5)


# ── Import smoke test ────────────────────────────────────────────────


class TestImport:
    def test_import_from_integration(self):
        from theatre.integration import GitHubIngester as Imported
        assert Imported is GitHubIngester
