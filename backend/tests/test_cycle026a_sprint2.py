"""Cycle 026a Sprint 2 — Standards Snapshot Registry tests.

Tests:
1. WCAG manifest (build from temp dir, verify asset_class="standard")
2. ARIA APG manifest (build from temp dir with patterns/ and practices/ subdirs)
3. Standards catalog completeness
4. R2 path convention for standards
5. Aggregate standards registry from staging root
6. Standards have same provenance contract as benchmarks
7. Standards registry rejects empty staging root
"""

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from backend.schemas.eval_asset_registry import (
    DatasetRegistryDocument,
    DatasetRegistryEntry,
)
from backend.services.r2_manifest_builder import (
    STANDARDS_CATALOG,
    build_manifest,
    build_standards_registry,
    r2_key_prefix,
)


# ── Helpers ──────────────────────────────────────────────────────────

def _populate_wcag_dir(tmpdir: Path) -> None:
    """Create a minimal WCAG-like file tree inside tmpdir."""
    (tmpdir / "wcag22.html").write_text(
        "<!DOCTYPE html>\n"
        "<html><head><title>WCAG 2.2</title></head>\n"
        "<body><h1>Web Content Accessibility Guidelines 2.2</h1></body></html>\n"
    )


def _populate_aria_apg_dir(tmpdir: Path) -> None:
    """Create a minimal ARIA APG-like file tree inside tmpdir.

    Structure:
        patterns/
            accordion.html
            breadcrumb.html
        practices/
            landmark-regions.html
    """
    patterns_dir = tmpdir / "patterns"
    patterns_dir.mkdir()
    (patterns_dir / "accordion.html").write_text(
        "<!DOCTYPE html>\n"
        "<html><head><title>Accordion Pattern</title></head>\n"
        "<body><h1>Accordion Pattern</h1></body></html>\n"
    )
    (patterns_dir / "breadcrumb.html").write_text(
        "<!DOCTYPE html>\n"
        "<html><head><title>Breadcrumb Pattern</title></head>\n"
        "<body><h1>Breadcrumb Pattern</h1></body></html>\n"
    )

    practices_dir = tmpdir / "practices"
    practices_dir.mkdir()
    (practices_dir / "landmark-regions.html").write_text(
        "<!DOCTYPE html>\n"
        "<html><head><title>Landmark Regions</title></head>\n"
        "<body><h1>Landmark Regions</h1></body></html>\n"
    )


def _build_wcag_manifest(tmpdir: Path) -> DatasetRegistryEntry:
    """Build a WCAG manifest with standard test parameters."""
    return build_manifest(
        tmpdir,
        asset_id="wcag",
        asset_class="standard",
        source_url="https://www.w3.org/TR/WCAG22/",
        version="2.2",
    )


def _build_aria_apg_manifest(tmpdir: Path) -> DatasetRegistryEntry:
    """Build an ARIA APG manifest with standard test parameters."""
    return build_manifest(
        tmpdir,
        asset_id="aria-apg",
        asset_class="standard",
        source_url="https://www.w3.org/WAI/ARIA/apg/",
        version="2024",
    )


# ── Tests ────────────────────────────────────────────────────────────

class TestWcagManifest:
    """Test 1: WCAG manifest generation from temp dir."""

    def test_wcag_manifest_from_temp_dir(self):
        """build_manifest produces a valid standard entry for WCAG 2.2."""
        with TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            _populate_wcag_dir(tmpdir_path)

            entry = _build_wcag_manifest(tmpdir_path)

            assert isinstance(entry, DatasetRegistryEntry)
            assert entry.asset_id == "wcag"
            assert entry.asset_class == "standard"
            assert entry.source_url == "https://www.w3.org/TR/WCAG22/"
            assert entry.version == "2.2"
            assert entry.license is None
            assert entry.content_hash.startswith("sha256:")
            assert len(entry.content_hash) == len("sha256:") + 64
            assert entry.retrieved_at.tzinfo is not None

            # 1 file: wcag22.html
            assert len(entry.files) == 1
            assert entry.files[0].path == "wcag22.html"
            assert entry.files[0].size_bytes > 0
            assert entry.files[0].content_hash.startswith("sha256:")

    def test_wcag_stable_hash(self):
        """Building WCAG manifest twice from identical content yields same hash."""
        with TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            _populate_wcag_dir(tmpdir_path)

            entry1 = _build_wcag_manifest(tmpdir_path)
            entry2 = _build_wcag_manifest(tmpdir_path)

            assert entry1.content_hash == entry2.content_hash


class TestAriaApgManifest:
    """Test 2: ARIA APG manifest with patterns/ and practices/ subdirs."""

    def test_aria_apg_manifest_from_temp_dir(self):
        """build_manifest handles ARIA APG directory structure with subdirs."""
        with TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            _populate_aria_apg_dir(tmpdir_path)

            entry = _build_aria_apg_manifest(tmpdir_path)

            assert isinstance(entry, DatasetRegistryEntry)
            assert entry.asset_id == "aria-apg"
            assert entry.asset_class == "standard"
            assert entry.source_url == "https://www.w3.org/WAI/ARIA/apg/"
            assert entry.version == "2024"
            assert entry.license is None
            assert entry.content_hash.startswith("sha256:")
            assert len(entry.content_hash) == len("sha256:") + 64

            # 3 files: patterns/accordion.html, patterns/breadcrumb.html,
            #          practices/landmark-regions.html
            assert len(entry.files) == 3

            paths = [f.path for f in entry.files]
            assert "patterns/accordion.html" in paths
            assert "patterns/breadcrumb.html" in paths
            assert "practices/landmark-regions.html" in paths

            # Files are sorted by path
            assert paths == sorted(paths)

            # All file entries have valid hashes and sizes
            for fe in entry.files:
                assert fe.content_hash.startswith("sha256:")
                assert len(fe.content_hash) == len("sha256:") + 64
                assert fe.size_bytes > 0

    def test_aria_apg_stable_hash(self):
        """Building ARIA APG manifest twice from identical content yields same hash."""
        with TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            _populate_aria_apg_dir(tmpdir_path)

            entry1 = _build_aria_apg_manifest(tmpdir_path)
            entry2 = _build_aria_apg_manifest(tmpdir_path)

            assert entry1.content_hash == entry2.content_hash


class TestStandardsCatalog:
    """Test 3: STANDARDS_CATALOG completeness."""

    def test_standards_catalog_entries(self):
        """STANDARDS_CATALOG contains the 2 required standard entries."""
        asset_ids = {s[0] for s in STANDARDS_CATALOG}
        expected = {"wcag", "aria-apg"}
        assert expected == asset_ids

    def test_standards_catalog_metadata(self):
        """Every catalog entry has a non-empty source_url and version."""
        for asset_id, source_url, version, _license in STANDARDS_CATALOG:
            assert len(source_url) > 0, f"{asset_id} missing source_url"
            assert len(version) > 0, f"{asset_id} missing version"

    def test_wcag_catalog_values(self):
        """WCAG catalog entry has correct source_url and version."""
        wcag_entry = next(s for s in STANDARDS_CATALOG if s[0] == "wcag")
        assert wcag_entry[1] == "https://www.w3.org/TR/WCAG22/"
        assert wcag_entry[2] == "2.2"

    def test_aria_apg_catalog_values(self):
        """ARIA APG catalog entry has correct source_url and version."""
        aria_entry = next(s for s in STANDARDS_CATALOG if s[0] == "aria-apg")
        assert aria_entry[1] == "https://www.w3.org/WAI/ARIA/apg/"
        assert aria_entry[2] == "2024"


class TestR2PathConventionStandards:
    """Test 4: R2 path convention for standards."""

    def test_r2_key_prefix_standard(self):
        """r2_key_prefix produces standards/ prefix for asset_class='standard'."""
        prefix = r2_key_prefix("wcag", "2.2", asset_class="standard")
        assert prefix == "standards/wcag/2.2/"

    def test_r2_key_prefix_aria_apg(self):
        """r2_key_prefix works for ARIA APG."""
        prefix = r2_key_prefix("aria-apg", "2024", asset_class="standard")
        assert prefix == "standards/aria-apg/2024/"

    def test_r2_key_prefix_benchmark_default(self):
        """r2_key_prefix still defaults to benchmarks/ for backward compatibility."""
        prefix = r2_key_prefix("humaneval", "v1.0")
        assert prefix == "benchmarks/humaneval/v1.0/"

    def test_r2_key_prefix_unknown_class_rejected(self):
        """r2_key_prefix raises ValueError for unknown asset_class."""
        with pytest.raises(ValueError, match="Unknown asset_class"):
            r2_key_prefix("something", "v1.0", asset_class="unknown")


class TestStandardsRegistry:
    """Test 5: aggregate standards registry from staging root."""

    def test_build_standards_registry(self):
        """build_standards_registry produces a valid registry document."""
        with TemporaryDirectory() as staging:
            staging_path = Path(staging)

            # Create WCAG staging layout: standards/wcag/2.2/raw/
            wcag_raw = staging_path / "standards" / "wcag" / "2.2" / "raw"
            wcag_raw.mkdir(parents=True)
            (wcag_raw / "wcag22.html").write_text("<html>WCAG 2.2</html>\n")

            # Create ARIA APG staging layout: standards/aria-apg/2024/raw/
            aria_raw = staging_path / "standards" / "aria-apg" / "2024" / "raw"
            aria_raw.mkdir(parents=True)
            patterns = aria_raw / "patterns"
            patterns.mkdir()
            (patterns / "accordion.html").write_text("<html>Accordion</html>\n")
            practices = aria_raw / "practices"
            practices.mkdir()
            (practices / "landmark.html").write_text("<html>Landmark</html>\n")

            doc = build_standards_registry(staging_path)

            assert isinstance(doc, DatasetRegistryDocument)
            assert doc.version == "1.0"
            assert doc.generated_at.tzinfo is not None
            assert len(doc.entries) == 2

            ids = {e.asset_id for e in doc.entries}
            assert ids == {"wcag", "aria-apg"}

            for entry in doc.entries:
                assert entry.asset_class == "standard"
                assert entry.content_hash.startswith("sha256:")

    def test_standards_registry_partial(self):
        """build_standards_registry includes only standards with existing dirs."""
        with TemporaryDirectory() as staging:
            staging_path = Path(staging)

            # Only create WCAG — ARIA APG dir does not exist
            wcag_raw = staging_path / "standards" / "wcag" / "2.2" / "raw"
            wcag_raw.mkdir(parents=True)
            (wcag_raw / "wcag22.html").write_text("<html>WCAG 2.2</html>\n")

            doc = build_standards_registry(staging_path)

            assert len(doc.entries) == 1
            assert doc.entries[0].asset_id == "wcag"

    def test_standards_registry_empty_staging_rejected(self):
        """build_standards_registry raises ValueError when no standards dirs exist."""
        with TemporaryDirectory() as staging:
            with pytest.raises(ValueError, match="No standards could be built"):
                build_standards_registry(Path(staging))


class TestProvenanceContract:
    """Test 6: standards have the same provenance contract as benchmarks."""

    def test_standard_same_schema_as_benchmark(self):
        """Standard entries use the same DatasetRegistryEntry schema as benchmarks."""
        with TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Build a benchmark manifest
            (tmpdir_path / "data.jsonl").write_text('{"task": "test"}\n')
            benchmark = build_manifest(
                tmpdir_path,
                asset_id="humaneval",
                asset_class="benchmark",
                source_url="https://github.com/openai/human-eval",
                version="v1.0",
                license="MIT",
            )

        with TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Build a standard manifest
            _populate_wcag_dir(tmpdir_path)
            standard = _build_wcag_manifest(tmpdir_path)

        # Both produce DatasetRegistryEntry with same field set
        assert type(benchmark) is type(standard)
        assert set(DatasetRegistryEntry.model_fields.keys()) == set(DatasetRegistryEntry.model_fields.keys())

        # Both have valid provenance fields
        for entry in (benchmark, standard):
            assert entry.content_hash.startswith("sha256:")
            assert len(entry.content_hash) == len("sha256:") + 64
            assert entry.retrieved_at.tzinfo is not None
            assert len(entry.files) >= 1
            for fe in entry.files:
                assert fe.content_hash.startswith("sha256:")
                assert fe.size_bytes > 0

    def test_standard_json_round_trip(self):
        """Standard entries survive JSON serialization like benchmarks."""
        with TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            _populate_aria_apg_dir(tmpdir_path)

            entry = _build_aria_apg_manifest(tmpdir_path)
            json_str = entry.model_dump_json()
            restored = DatasetRegistryEntry.model_validate_json(json_str)

            assert restored.asset_id == "aria-apg"
            assert restored.asset_class == "standard"
            assert restored.content_hash == entry.content_hash
            assert len(restored.files) == len(entry.files)
