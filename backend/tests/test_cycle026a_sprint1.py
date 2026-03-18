"""Cycle 026a Sprint 1 — Benchmark Ingest Registry tests.

Tests:
1. Manifest generation from temp dir
2. Stable hash (same input -> same hash)
3. Aggregate registry shape validation
4. Path layout follows R2 convention
5. Transport/cache artifacts are skipped
6. Empty directory is rejected
7. Live-only asset is rejected by policy gate
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from backend.schemas.eval_asset_registry import (
    DatasetRegistryDocument,
    DatasetRegistryEntry,
)
from backend.services.r2_manifest_builder import (
    BENCHMARK_CATALOG,
    SKIP_NAMES,
    build_manifest,
    build_registry_document,
    get_staging_root,
    r2_key_prefix,
    sha256_file,
    sha256_json,
)


# ── Helpers ──────────────────────────────────────────────────────────

def _populate_temp_dir(tmpdir: Path) -> None:
    """Create a minimal benchmark-like file tree inside tmpdir."""
    raw_dir = tmpdir / "raw"
    raw_dir.mkdir()

    (raw_dir / "problems.jsonl").write_text(
        '{"task_id": "HumanEval/0", "prompt": "def hello():"}\n'
        '{"task_id": "HumanEval/1", "prompt": "def add(a, b):"}\n'
    )
    (raw_dir / "solutions.jsonl").write_text(
        '{"task_id": "HumanEval/0", "solution": "return \'hello\'"}\n'
    )
    (tmpdir / "README.md").write_text("# HumanEval benchmark\n")


def _build_default_manifest(tmpdir: Path) -> DatasetRegistryEntry:
    """Build a manifest with standard test parameters."""
    return build_manifest(
        tmpdir,
        asset_id="humaneval",
        asset_class="benchmark",
        source_url="https://github.com/openai/human-eval",
        version="v1.0",
        license="MIT",
    )


# ── Tests ────────────────────────────────────────────────────────────

class TestManifestGeneration:
    """Test 1: manifest generation from temp dir."""

    def test_manifest_from_temp_dir(self):
        """build_manifest produces a valid DatasetRegistryEntry from a temp directory."""
        with TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            _populate_temp_dir(tmpdir_path)

            entry = _build_default_manifest(tmpdir_path)

            assert isinstance(entry, DatasetRegistryEntry)
            assert entry.asset_id == "humaneval"
            assert entry.asset_class == "benchmark"
            assert entry.source_url == "https://github.com/openai/human-eval"
            assert entry.version == "v1.0"
            assert entry.license == "MIT"
            assert entry.content_hash.startswith("sha256:")
            assert len(entry.content_hash) == len("sha256:") + 64  # SHA-256 hex
            assert entry.retrieved_at.tzinfo is not None

            # 3 files: README.md, raw/problems.jsonl, raw/solutions.jsonl
            assert len(entry.files) == 3

            paths = [f.path for f in entry.files]
            assert "README.md" in paths
            assert "raw/problems.jsonl" in paths
            assert "raw/solutions.jsonl" in paths

            # All file entries have valid hashes and sizes
            for fe in entry.files:
                assert fe.content_hash.startswith("sha256:")
                assert len(fe.content_hash) == len("sha256:") + 64
                assert fe.size_bytes > 0

    def test_files_sorted_by_path(self):
        """File entries in the manifest are sorted by relative path."""
        with TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            _populate_temp_dir(tmpdir_path)

            entry = _build_default_manifest(tmpdir_path)
            paths = [f.path for f in entry.files]
            assert paths == sorted(paths)


class TestStableHash:
    """Test 2: stable hash — same input produces same hash."""

    def test_same_input_same_hash(self):
        """Building the manifest twice from identical content yields the same content_hash."""
        with TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            _populate_temp_dir(tmpdir_path)

            entry1 = _build_default_manifest(tmpdir_path)
            entry2 = _build_default_manifest(tmpdir_path)

            assert entry1.content_hash == entry2.content_hash

            # Per-file hashes also match
            for f1, f2 in zip(entry1.files, entry2.files):
                assert f1.path == f2.path
                assert f1.content_hash == f2.content_hash
                assert f1.size_bytes == f2.size_bytes

    def test_different_content_different_hash(self):
        """Modifying file content changes the manifest hash."""
        with TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            _populate_temp_dir(tmpdir_path)

            entry_before = _build_default_manifest(tmpdir_path)

            # Modify one file
            (tmpdir_path / "raw" / "problems.jsonl").write_text(
                '{"task_id": "HumanEval/0", "prompt": "CHANGED"}\n'
            )

            entry_after = _build_default_manifest(tmpdir_path)
            assert entry_before.content_hash != entry_after.content_hash

    def test_sha256_json_deterministic(self):
        """sha256_json produces the same hash regardless of input order."""
        from backend.schemas.eval_asset_registry import RegistryFileEntry

        entries_a = [
            RegistryFileEntry(path="b.txt", size_bytes=10, content_hash="sha256:aaa"),
            RegistryFileEntry(path="a.txt", size_bytes=20, content_hash="sha256:bbb"),
        ]
        entries_b = [
            RegistryFileEntry(path="a.txt", size_bytes=20, content_hash="sha256:bbb"),
            RegistryFileEntry(path="b.txt", size_bytes=10, content_hash="sha256:aaa"),
        ]

        assert sha256_json(entries_a) == sha256_json(entries_b)


class TestRegistryDocument:
    """Test 3: aggregate registry shape validation."""

    def test_aggregate_registry_shape(self):
        """build_registry_document produces a valid DatasetRegistryDocument."""
        with TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            _populate_temp_dir(tmpdir_path)

            entry = _build_default_manifest(tmpdir_path)
            doc = build_registry_document([entry], registry_version="1.0")

            assert isinstance(doc, DatasetRegistryDocument)
            assert doc.version == "1.0"
            assert doc.generated_at.tzinfo is not None
            assert len(doc.entries) == 1
            assert doc.entries[0].asset_id == "humaneval"

    def test_registry_json_round_trip(self):
        """Registry document survives JSON serialization and deserialization."""
        with TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            _populate_temp_dir(tmpdir_path)

            entry = _build_default_manifest(tmpdir_path)
            doc = build_registry_document([entry])

            json_str = doc.model_dump_json()
            restored = DatasetRegistryDocument.model_validate_json(json_str)

            assert len(restored.entries) == 1
            assert restored.entries[0].asset_id == entry.asset_id
            assert restored.entries[0].content_hash == entry.content_hash
            assert len(restored.entries[0].files) == len(entry.files)

    def test_benchmark_catalog_completeness(self):
        """BENCHMARK_CATALOG contains the 6 required benchmark entries."""
        asset_ids = {b[0] for b in BENCHMARK_CATALOG}
        expected = {"humaneval", "mbpp", "hellaswag", "mmlu", "mmlu-pro", "swe-bench-verified"}
        assert expected.issubset(asset_ids), f"Missing: {expected - asset_ids}"

        # Every entry has a non-empty source_url and version
        for asset_id, source_url, version, _license in BENCHMARK_CATALOG:
            assert len(source_url) > 0, f"{asset_id} missing source_url"
            assert len(version) > 0, f"{asset_id} missing version"


class TestR2PathConvention:
    """Test 4: path layout follows R2 convention."""

    def test_r2_key_prefix_format(self):
        """r2_key_prefix produces the expected R2 path prefix."""
        prefix = r2_key_prefix("humaneval", "v1.0")
        assert prefix == "benchmarks/humaneval/v1.0/"

    def test_r2_key_prefix_various_assets(self):
        """r2_key_prefix works correctly for all benchmark catalog entries."""
        for asset_id, _url, version, _license in BENCHMARK_CATALOG:
            prefix = r2_key_prefix(asset_id, version)
            assert prefix.startswith("benchmarks/")
            assert prefix.endswith("/")
            assert asset_id in prefix
            assert version in prefix
            # Convention: benchmarks/{asset}/{version}/
            parts = prefix.strip("/").split("/")
            assert parts[0] == "benchmarks"
            assert parts[1] == asset_id
            assert parts[2] == version


class TestSkipArtifacts:
    """Transport/cache artifacts are excluded from manifests."""

    def test_cache_artifacts_skipped(self):
        """Files and directories in SKIP_NAMES are excluded from the manifest."""
        with TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            _populate_temp_dir(tmpdir_path)

            # Add artifacts that should be skipped
            (tmpdir_path / ".gitattributes").write_text("*.jsonl filter=lfs\n")
            (tmpdir_path / ".cache").mkdir()
            (tmpdir_path / ".cache" / "download.tmp").write_text("cached")
            hf_dir = tmpdir_path / ".huggingface"
            hf_dir.mkdir()
            (hf_dir / "token").write_text("hf_secret")
            pycache = tmpdir_path / "__pycache__"
            pycache.mkdir()
            (pycache / "module.pyc").write_bytes(b"\x00\x01\x02")

            entry = _build_default_manifest(tmpdir_path)
            paths = {f.path for f in entry.files}

            # None of the skip artifacts should appear
            assert ".gitattributes" not in paths
            assert not any(".cache" in p for p in paths)
            assert not any(".huggingface" in p for p in paths)
            assert not any("__pycache__" in p for p in paths)

            # The real files should still be present
            assert "README.md" in paths
            assert "raw/problems.jsonl" in paths
            assert "raw/solutions.jsonl" in paths

    def test_download_meta_excluded(self):
        """W3C downloader .download_meta.json is excluded from canonical hashing."""
        with TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            _populate_temp_dir(tmpdir_path)

            # Build without .download_meta.json
            entry_clean = _build_default_manifest(tmpdir_path)

            # Add .download_meta.json (volatile downloader metadata)
            (tmpdir_path / ".download_meta.json").write_text(
                json.dumps({"downloaded_at": "2026-03-17T22:37:00Z", "source": "test"})
            )

            # Build with .download_meta.json present
            entry_with_meta = _build_default_manifest(tmpdir_path)

            # Hashes must be identical — .download_meta.json is excluded
            assert entry_clean.content_hash == entry_with_meta.content_hash

            # .download_meta.json must not appear in file list
            paths = {f.path for f in entry_with_meta.files}
            assert ".download_meta.json" not in paths


class TestEdgeCases:
    """Edge cases and error handling."""

    def test_empty_directory_rejected(self):
        """An empty directory raises ValueError."""
        with TemporaryDirectory() as tmpdir:
            with pytest.raises(ValueError, match="No eligible files"):
                build_manifest(
                    Path(tmpdir),
                    asset_id="humaneval",
                    source_url="https://example.com",
                    version="v1.0",
                )

    def test_nonexistent_directory_rejected(self):
        """A non-existent directory raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError, match="does not exist"):
            build_manifest(
                Path("/nonexistent/path/to/asset"),
                asset_id="humaneval",
                source_url="https://example.com",
                version="v1.0",
            )

    def test_live_asset_rejected_by_policy(self):
        """A live-only asset is rejected before any I/O."""
        with TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            _populate_temp_dir(tmpdir_path)

            with pytest.raises(ValueError, match="Policy violation"):
                build_manifest(
                    tmpdir_path,
                    asset_id="sec-edgar",
                    source_url="https://www.sec.gov/edgar",
                    version="v1.0",
                )

    def test_staging_root_default(self):
        """get_staging_root returns the default when env var is unset."""
        # Temporarily clear the env var if set
        original = os.environ.pop("ECHELON_EVAL_DATA_ROOT", None)
        try:
            root = get_staging_root()
            assert root == Path.home() / ".echelon" / "eval_data"
        finally:
            if original is not None:
                os.environ["ECHELON_EVAL_DATA_ROOT"] = original

    def test_staging_root_from_env(self):
        """get_staging_root reads ECHELON_EVAL_DATA_ROOT when set."""
        original = os.environ.get("ECHELON_EVAL_DATA_ROOT")
        try:
            os.environ["ECHELON_EVAL_DATA_ROOT"] = "/tmp/test_eval_data"
            root = get_staging_root()
            assert root == Path("/tmp/test_eval_data")
        finally:
            if original is not None:
                os.environ["ECHELON_EVAL_DATA_ROOT"] = original
            else:
                os.environ.pop("ECHELON_EVAL_DATA_ROOT", None)
