"""Tests for GitHub ground truth ingestion."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import httpx
import pytest
import respx

from echelon_verify.config import IngestionConfig
from echelon_verify.ingestion.github import (
    GitHubIngester,
    _extract_files_changed,
    _parse_repo,
    _truncate_diff,
)
from echelon_verify.models import GroundTruthRecord
from echelon_verify.storage import Storage


SAMPLE_PR = {
    "number": 142,
    "title": "Add rate limiting to /api/users",
    "body": "Implements token bucket rate limiting.",
    "state": "closed",
    "merged_at": "2026-02-15T10:30:00Z",
    "user": {"login": "alice"},
    "labels": [{"name": "enhancement"}, {"name": "api"}],
    "html_url": "https://github.com/echelon/app/pull/142",
}

SAMPLE_PR_2 = {
    "number": 138,
    "title": "Fix auth bypass",
    "body": "Patches authentication bypass vulnerability.",
    "state": "closed",
    "merged_at": "2026-02-14T09:00:00Z",
    "user": {"login": "bob"},
    "labels": [{"name": "security"}],
    "html_url": "https://github.com/echelon/app/pull/138",
}

UNMERGED_PR = {
    "number": 140,
    "title": "WIP feature",
    "body": "Not merged",
    "state": "closed",
    "merged_at": None,
    "user": {"login": "charlie"},
    "labels": [],
    "html_url": "https://github.com/echelon/app/pull/140",
}

SAMPLE_DIFF = """\
diff --git a/src/routes/users.py b/src/routes/users.py
--- a/src/routes/users.py
+++ b/src/routes/users.py
@@ -10,6 +10,15 @@
+from utils.rate_limit import RateLimiter
+
+limiter = RateLimiter(max_requests=100, window_seconds=60)
"""


class TestParseRepo:
    def test_full_url(self) -> None:
        owner, repo = _parse_repo("https://github.com/echelon/app")
        assert owner == "echelon"
        assert repo == "app"

    def test_url_with_git_suffix(self) -> None:
        owner, repo = _parse_repo("https://github.com/echelon/app.git")
        assert owner == "echelon"
        assert repo == "app"

    def test_short_form(self) -> None:
        owner, repo = _parse_repo("echelon/app")
        assert owner == "echelon"
        assert repo == "app"

    def test_invalid_url(self) -> None:
        with pytest.raises(ValueError, match="Invalid GitHub repo URL"):
            _parse_repo("not-a-url")

    def test_rejects_http_scheme(self) -> None:
        with pytest.raises(ValueError, match="Invalid GitHub repo URL"):
            _parse_repo("http://github.com/echelon/app")

    def test_rejects_path_traversal_in_owner(self) -> None:
        with pytest.raises(ValueError, match="Invalid"):
            _parse_repo("https://github.com/../etc/app")

    def test_rejects_special_chars_in_repo(self) -> None:
        with pytest.raises(ValueError, match="Invalid repo name"):
            _parse_repo("https://github.com/owner/repo%00evil")


class TestTruncateDiff:
    def test_small_diff_unchanged(self) -> None:
        result = _truncate_diff(SAMPLE_DIFF)
        assert result == SAMPLE_DIFF

    def test_large_diff_truncated(self) -> None:
        # Create a diff larger than 100KB
        large_diff = "diff --git a/big.py b/big.py\n"
        large_diff += "--- a/big.py\n+++ b/big.py\n@@ -1,5 +1,5 @@\n"
        large_diff += "+x = 1\n" * 20_000  # ~120KB of additions
        result = _truncate_diff(large_diff, max_bytes=1000)
        assert len(result.encode()) < len(large_diff.encode())
        assert "+... [truncated]" in result


class TestExtractFilesChanged:
    def test_extracts_paths(self) -> None:
        files = _extract_files_changed(SAMPLE_DIFF)
        assert files == ["src/routes/users.py"]

    def test_no_files(self) -> None:
        files = _extract_files_changed("no diff content")
        assert files == []

    def test_binary_files_detected(self) -> None:
        diff = "Binary files a/image.png and b/image.png differ\n"
        files = _extract_files_changed(diff)
        assert files == ["image.png"]


class TestGitHubIngester:
    @pytest.fixture
    def config(self) -> IngestionConfig:
        return IngestionConfig(
            repo_url="https://github.com/echelon/app",
            limit=10,
        )

    @respx.mock
    @pytest.mark.asyncio
    async def test_ingest_fetches_merged_prs(self, config: IngestionConfig) -> None:
        # Mock PR listing
        respx.get(
            "https://api.github.com/repos/echelon/app/pulls",
        ).mock(
            return_value=httpx.Response(
                200,
                json=[SAMPLE_PR, UNMERGED_PR, SAMPLE_PR_2],
                headers={
                    "x-ratelimit-remaining": "50",
                    "x-ratelimit-reset": "9999999999",
                },
            )
        )

        # Mock diff requests
        respx.get(
            "https://api.github.com/repos/echelon/app/pulls/142",
        ).mock(
            return_value=httpx.Response(
                200,
                text=SAMPLE_DIFF,
                headers={
                    "x-ratelimit-remaining": "49",
                    "x-ratelimit-reset": "9999999999",
                },
            )
        )
        respx.get(
            "https://api.github.com/repos/echelon/app/pulls/138",
        ).mock(
            return_value=httpx.Response(
                200,
                text=SAMPLE_DIFF,
                headers={
                    "x-ratelimit-remaining": "48",
                    "x-ratelimit-reset": "9999999999",
                },
            )
        )

        async with GitHubIngester(config) as ingester:
            records = await ingester.ingest()

        assert len(records) == 2  # Unmerged PR excluded
        assert records[0].id == "142"
        assert records[0].author == "alice"
        assert records[0].repo == "echelon/app"
        assert records[1].id == "138"

    @respx.mock
    @pytest.mark.asyncio
    async def test_label_filter(self, config: IngestionConfig) -> None:
        config.labels = ["security"]

        respx.get(
            "https://api.github.com/repos/echelon/app/pulls",
        ).mock(
            return_value=httpx.Response(
                200,
                json=[SAMPLE_PR, SAMPLE_PR_2],
                headers={
                    "x-ratelimit-remaining": "50",
                    "x-ratelimit-reset": "9999999999",
                },
            )
        )
        respx.get(
            "https://api.github.com/repos/echelon/app/pulls/138",
        ).mock(
            return_value=httpx.Response(
                200,
                text=SAMPLE_DIFF,
                headers={
                    "x-ratelimit-remaining": "49",
                    "x-ratelimit-reset": "9999999999",
                },
            )
        )

        async with GitHubIngester(config) as ingester:
            records = await ingester.ingest()

        assert len(records) == 1
        assert records[0].id == "138"

    @respx.mock
    @pytest.mark.asyncio
    async def test_pagination(self, config: IngestionConfig) -> None:
        config.limit = 5

        # Page 1 with Link header pointing to page 2
        respx.get(
            "https://api.github.com/repos/echelon/app/pulls",
            params__contains={"page": "1"},
        ).mock(
            return_value=httpx.Response(
                200,
                json=[SAMPLE_PR],
                headers={
                    "x-ratelimit-remaining": "50",
                    "x-ratelimit-reset": "9999999999",
                    "link": '<https://api.github.com/repos/echelon/app/pulls?page=2>; rel="next"',
                },
            )
        )

        # Page 2 (no next link)
        respx.get(
            "https://api.github.com/repos/echelon/app/pulls",
            params__contains={"page": "2"},
        ).mock(
            return_value=httpx.Response(
                200,
                json=[SAMPLE_PR_2],
                headers={
                    "x-ratelimit-remaining": "49",
                    "x-ratelimit-reset": "9999999999",
                },
            )
        )

        # Diffs
        respx.get(
            "https://api.github.com/repos/echelon/app/pulls/142",
        ).mock(
            return_value=httpx.Response(
                200, text=SAMPLE_DIFF,
                headers={
                    "x-ratelimit-remaining": "48",
                    "x-ratelimit-reset": "9999999999",
                },
            )
        )
        respx.get(
            "https://api.github.com/repos/echelon/app/pulls/138",
        ).mock(
            return_value=httpx.Response(
                200, text=SAMPLE_DIFF,
                headers={
                    "x-ratelimit-remaining": "47",
                    "x-ratelimit-reset": "9999999999",
                },
            )
        )

        async with GitHubIngester(config) as ingester:
            records = await ingester.ingest()

        assert len(records) == 2

    @respx.mock
    @pytest.mark.asyncio
    async def test_ground_truth_fields_populated(self, config: IngestionConfig) -> None:
        respx.get(
            "https://api.github.com/repos/echelon/app/pulls",
        ).mock(
            return_value=httpx.Response(
                200,
                json=[SAMPLE_PR],
                headers={
                    "x-ratelimit-remaining": "50",
                    "x-ratelimit-reset": "9999999999",
                },
            )
        )
        respx.get(
            "https://api.github.com/repos/echelon/app/pulls/142",
        ).mock(
            return_value=httpx.Response(
                200,
                text=SAMPLE_DIFF,
                headers={
                    "x-ratelimit-remaining": "49",
                    "x-ratelimit-reset": "9999999999",
                },
            )
        )

        async with GitHubIngester(config) as ingester:
            records = await ingester.ingest()

        assert len(records) == 1
        r = records[0]
        assert r.title == "Add rate limiting to /api/users"
        assert r.description == "Implements token bucket rate limiting."
        assert r.author == "alice"
        assert r.labels == ["enhancement", "api"]
        assert r.url == "https://github.com/echelon/app/pull/142"
        assert "src/routes/users.py" in r.files_changed
        assert r.timestamp == datetime(2026, 2, 15, 10, 30, 0, tzinfo=timezone.utc)

    @respx.mock
    @pytest.mark.asyncio
    async def test_incremental_ingestion_skips_cached(
        self, config: IngestionConfig
    ) -> None:
        respx.get(
            "https://api.github.com/repos/echelon/app/pulls",
        ).mock(
            return_value=httpx.Response(
                200,
                json=[SAMPLE_PR, SAMPLE_PR_2],
                headers={
                    "x-ratelimit-remaining": "50",
                    "x-ratelimit-reset": "9999999999",
                },
            )
        )
        # Only PR 138 diff should be fetched (142 is cached)
        respx.get(
            "https://api.github.com/repos/echelon/app/pulls/138",
        ).mock(
            return_value=httpx.Response(
                200,
                text=SAMPLE_DIFF,
                headers={
                    "x-ratelimit-remaining": "49",
                    "x-ratelimit-reset": "9999999999",
                },
            )
        )

        async with GitHubIngester(config) as ingester:
            records = await ingester.ingest(cached_ids={"142"})

        assert len(records) == 1
        assert records[0].id == "138"

    @respx.mock
    @pytest.mark.asyncio
    async def test_403_triggers_backoff(self, config: IngestionConfig) -> None:
        call_count = 0

        def side_effect(request: httpx.Request) -> httpx.Response:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return httpx.Response(
                    403,
                    json={"message": "rate limit exceeded"},
                    headers={
                        "x-ratelimit-remaining": "0",
                        "x-ratelimit-reset": "0",  # Already past
                    },
                )
            return httpx.Response(
                200,
                json=[SAMPLE_PR],
                headers={
                    "x-ratelimit-remaining": "50",
                    "x-ratelimit-reset": "9999999999",
                },
            )

        respx.get(
            "https://api.github.com/repos/echelon/app/pulls",
        ).mock(side_effect=side_effect)
        respx.get(
            "https://api.github.com/repos/echelon/app/pulls/142",
        ).mock(
            return_value=httpx.Response(
                200,
                text=SAMPLE_DIFF,
                headers={
                    "x-ratelimit-remaining": "49",
                    "x-ratelimit-reset": "9999999999",
                },
            )
        )

        async with GitHubIngester(config) as ingester:
            records = await ingester.ingest()

        assert len(records) == 1
        assert call_count >= 2  # At least one retry

    def test_storage_round_trip(
        self, tmp_path: Path, sample_ground_truth: GroundTruthRecord
    ) -> None:
        storage = Storage(str(tmp_path / "data"))
        repo_dir = storage.repo_dir("echelon/app")
        path = repo_dir / "ground_truth.jsonl"

        storage.append_jsonl(path, sample_ground_truth)
        restored = storage.read_jsonl(path, GroundTruthRecord)

        assert len(restored) == 1
        assert restored[0].id == sample_ground_truth.id
        assert restored[0].title == sample_ground_truth.title
