"""Cycle 026b Sprint 1 — New Snapshot Asset Manifest Verification.

Verifies that the new snapshot assets (react-docs, tailwind-docs,
owasp-top10, cwe-subset, arxiv-ml-metadata) can be manifested and
included in registry documents alongside the original assets.

Tests:
1. React docs manifest (3 tests)
2. Tailwind docs manifest (2 tests)
3. OWASP Top 10 manifest (2 tests)
4. CWE subset manifest (2 tests)
5. arXiv ML metadata manifest (3 tests)
6. Mixed registry aggregation (2 tests)
7. Regression (2 tests)
"""

from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Optional

import pytest

from backend.schemas.eval_asset_registry import (
    DatasetRegistryDocument,
    DatasetRegistryEntry,
)
from backend.services.r2_manifest_builder import (
    BENCHMARK_CATALOG,
    SKIP_NAMES,
    STANDARDS_CATALOG,
    build_manifest,
    build_registry_document,
    build_standards_registry,
)


# ── Populate Helpers ───────────────────────────────────────────────


def _populate_react_docs_dir(tmpdir: Path) -> None:
    """Create a minimal React docs file tree with reference/ subdirs."""
    react_dir = tmpdir / "reference" / "react"
    react_dir.mkdir(parents=True)
    (react_dir / "useState.html").write_text(
        "<!DOCTYPE html>\n"
        "<html><head><title>useState</title></head>\n"
        "<body><h1>useState</h1><p>Returns a stateful value.</p></body></html>\n"
    )
    (react_dir / "useEffect.html").write_text(
        "<!DOCTYPE html>\n"
        "<html><head><title>useEffect</title></head>\n"
        "<body><h1>useEffect</h1><p>Accepts a function with side effects.</p></body></html>\n"
    )

    react_dom_dir = tmpdir / "reference" / "react-dom"
    react_dom_dir.mkdir(parents=True)
    (react_dom_dir / "createPortal.html").write_text(
        "<!DOCTYPE html>\n"
        "<html><head><title>createPortal</title></head>\n"
        "<body><h1>createPortal</h1><p>Renders children into a DOM node.</p></body></html>\n"
    )


def _populate_tailwind_docs_dir(tmpdir: Path) -> None:
    """Create a minimal Tailwind docs file tree with flat HTML files."""
    (tmpdir / "installation.html").write_text(
        "<!DOCTYPE html>\n"
        "<html><head><title>Installation</title></head>\n"
        "<body><h1>Installation</h1><p>Get started with Tailwind CSS.</p></body></html>\n"
    )
    (tmpdir / "flex.html").write_text(
        "<!DOCTYPE html>\n"
        "<html><head><title>Flex</title></head>\n"
        "<body><h1>Flex</h1><p>Utilities for controlling flex containers.</p></body></html>\n"
    )
    (tmpdir / "padding.html").write_text(
        "<!DOCTYPE html>\n"
        "<html><head><title>Padding</title></head>\n"
        "<body><h1>Padding</h1><p>Utilities for controlling padding.</p></body></html>\n"
    )


def _populate_owasp_dir(tmpdir: Path) -> None:
    """Create a minimal OWASP Top 10 file tree."""
    (tmpdir / "index.html").write_text(
        "<!DOCTYPE html>\n"
        "<html><head><title>OWASP Top 10</title></head>\n"
        "<body><h1>OWASP Top 10 - 2025</h1></body></html>\n"
    )
    (tmpdir / "A01_Broken_Access_Control.html").write_text(
        "<!DOCTYPE html>\n"
        "<html><head><title>A01 Broken Access Control</title></head>\n"
        "<body><h1>A01:2025 - Broken Access Control</h1></body></html>\n"
    )
    (tmpdir / "A03_Injection.html").write_text(
        "<!DOCTYPE html>\n"
        "<html><head><title>A03 Injection</title></head>\n"
        "<body><h1>A03:2025 - Injection</h1></body></html>\n"
    )
    (tmpdir / "A07_SSRF.html").write_text(
        "<!DOCTYPE html>\n"
        "<html><head><title>A07 SSRF</title></head>\n"
        "<body><h1>A07:2025 - Server-Side Request Forgery</h1></body></html>\n"
    )


def _populate_cwe_dir(tmpdir: Path) -> None:
    """Create a minimal CWE subset file tree with curated HTML files."""
    (tmpdir / "cwe_top25_2024.html").write_text(
        "<!DOCTYPE html>\n"
        "<html><head><title>CWE Top 25</title></head>\n"
        "<body><h1>2024 CWE Top 25 Most Dangerous Software Weaknesses</h1></body></html>\n"
    )
    (tmpdir / "CWE-79_XSS.html").write_text(
        "<!DOCTYPE html>\n"
        "<html><head><title>CWE-79: XSS</title></head>\n"
        "<body><h1>CWE-79: Improper Neutralization of Input During Web Page Generation</h1></body></html>\n"
    )
    (tmpdir / "CWE-89_SQL_Injection.html").write_text(
        "<!DOCTYPE html>\n"
        "<html><head><title>CWE-89: SQL Injection</title></head>\n"
        "<body><h1>CWE-89: Improper Neutralization of Special Elements in SQL Command</h1></body></html>\n"
    )


def _populate_arxiv_dir(tmpdir: Path) -> None:
    """Create a minimal arXiv ML metadata file tree (HTML docs + XML)."""
    (tmpdir / "bulk_data.html").write_text(
        "<!DOCTYPE html>\n"
        "<html><head><title>arXiv Bulk Data</title></head>\n"
        "<body><h1>arXiv Bulk Data Access</h1></body></html>\n"
    )
    (tmpdir / "api_index.html").write_text(
        "<!DOCTYPE html>\n"
        "<html><head><title>arXiv API</title></head>\n"
        "<body><h1>arXiv API Index</h1></body></html>\n"
    )
    (tmpdir / "oai_identify.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        "<OAI-PMH>\n"
        "  <Identify>\n"
        "    <repositoryName>arXiv</repositoryName>\n"
        "  </Identify>\n"
        "</OAI-PMH>\n"
    )


# ── Build Helpers ──────────────────────────────────────────────────


def _build_react_docs_manifest(tmpdir: Path) -> DatasetRegistryEntry:
    """Build a React docs manifest with catalog parameters."""
    return build_manifest(
        tmpdir,
        asset_id="react-docs",
        asset_class="standard",
        source_url="https://react.dev/reference",
        version="2026-03",
    )


def _build_tailwind_docs_manifest(tmpdir: Path) -> DatasetRegistryEntry:
    """Build a Tailwind docs manifest with catalog parameters."""
    return build_manifest(
        tmpdir,
        asset_id="tailwind-docs",
        asset_class="standard",
        source_url="https://tailwindcss.com/docs",
        version="2026-03",
    )


def _build_owasp_manifest(tmpdir: Path) -> DatasetRegistryEntry:
    """Build an OWASP Top 10 manifest with catalog parameters."""
    return build_manifest(
        tmpdir,
        asset_id="owasp-top10",
        asset_class="standard",
        source_url="https://owasp.org/www-project-top-ten/",
        version="2025",
    )


def _build_cwe_manifest(tmpdir: Path) -> DatasetRegistryEntry:
    """Build a CWE subset manifest with catalog parameters."""
    return build_manifest(
        tmpdir,
        asset_id="cwe-subset",
        asset_class="standard",
        source_url="https://cwe.mitre.org/top25/",
        version="2026-03",
    )


def _build_arxiv_manifest(tmpdir: Path) -> DatasetRegistryEntry:
    """Build an arXiv ML metadata manifest with catalog parameters."""
    return build_manifest(
        tmpdir,
        asset_id="arxiv-ml-metadata",
        asset_class="benchmark",
        source_url="https://info.arxiv.org/help/bulk_data.html",
        version="2026-03",
    )


# ── 1. React Docs Manifest (3 tests) ─────────────────────────────


class TestReactDocsManifest:
    """React docs manifest from temp dir with reference/ subdirs."""

    def test_react_docs_manifest_metadata(self):
        """build_manifest produces valid standard entry for react-docs with subdirs."""
        with TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            _populate_react_docs_dir(tmpdir_path)

            entry = _build_react_docs_manifest(tmpdir_path)

            assert isinstance(entry, DatasetRegistryEntry)
            assert entry.asset_id == "react-docs"
            assert entry.asset_class == "standard"
            assert entry.source_url == "https://react.dev/reference"
            assert entry.version == "2026-03"
            assert entry.license is None
            assert entry.content_hash.startswith("sha256:")
            assert len(entry.content_hash) == len("sha256:") + 64
            assert entry.retrieved_at.tzinfo is not None

            # 3 files across two reference subdirs
            assert len(entry.files) == 3

            paths = [f.path for f in entry.files]
            assert "reference/react/useState.html" in paths
            assert "reference/react/useEffect.html" in paths
            assert "reference/react-dom/createPortal.html" in paths

            # Files sorted by path
            assert paths == sorted(paths)

            # All file entries have valid hashes and sizes
            for fe in entry.files:
                assert fe.content_hash.startswith("sha256:")
                assert len(fe.content_hash) == len("sha256:") + 64
                assert fe.size_bytes > 0

    def test_react_docs_stable_hash(self):
        """Building react-docs manifest twice yields the same content_hash."""
        with TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            _populate_react_docs_dir(tmpdir_path)

            entry1 = _build_react_docs_manifest(tmpdir_path)
            entry2 = _build_react_docs_manifest(tmpdir_path)

            assert entry1.content_hash == entry2.content_hash

            # Per-file hashes also stable
            for f1, f2 in zip(entry1.files, entry2.files):
                assert f1.path == f2.path
                assert f1.content_hash == f2.content_hash
                assert f1.size_bytes == f2.size_bytes

    def test_react_docs_download_meta_excluded(self):
        """React docs .download_meta.json is excluded from manifest."""
        with TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            _populate_react_docs_dir(tmpdir_path)

            entry_clean = _build_react_docs_manifest(tmpdir_path)

            # Add .download_meta.json (volatile downloader metadata)
            (tmpdir_path / ".download_meta.json").write_text(
                json.dumps({"downloaded_at": "2026-03-18T10:00:00Z", "source": "react.dev"})
            )

            entry_with_meta = _build_react_docs_manifest(tmpdir_path)

            # Hashes identical — .download_meta.json excluded
            assert entry_clean.content_hash == entry_with_meta.content_hash

            # .download_meta.json not in file list
            paths = {f.path for f in entry_with_meta.files}
            assert ".download_meta.json" not in paths


# ── 2. Tailwind Docs Manifest (2 tests) ──────────────────────────


class TestTailwindDocsManifest:
    """Tailwind docs manifest from flat HTML files."""

    def test_tailwind_docs_manifest_metadata(self):
        """build_manifest produces valid standard entry for tailwind-docs."""
        with TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            _populate_tailwind_docs_dir(tmpdir_path)

            entry = _build_tailwind_docs_manifest(tmpdir_path)

            assert isinstance(entry, DatasetRegistryEntry)
            assert entry.asset_id == "tailwind-docs"
            assert entry.asset_class == "standard"
            assert entry.source_url == "https://tailwindcss.com/docs"
            assert entry.version == "2026-03"
            assert entry.license is None
            assert entry.content_hash.startswith("sha256:")
            assert len(entry.content_hash) == len("sha256:") + 64

            # 3 flat HTML files
            assert len(entry.files) == 3

            paths = [f.path for f in entry.files]
            assert "installation.html" in paths
            assert "flex.html" in paths
            assert "padding.html" in paths
            assert paths == sorted(paths)

    def test_tailwind_docs_stable_hash(self):
        """Building tailwind-docs manifest twice yields the same hash."""
        with TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            _populate_tailwind_docs_dir(tmpdir_path)

            entry1 = _build_tailwind_docs_manifest(tmpdir_path)
            entry2 = _build_tailwind_docs_manifest(tmpdir_path)

            assert entry1.content_hash == entry2.content_hash


# ── 3. OWASP Top 10 Manifest (2 tests) ──────────────────────────


class TestOwaspManifest:
    """OWASP Top 10 manifest from HTML files (index + A01-A10)."""

    def test_owasp_manifest_metadata_and_file_count(self):
        """build_manifest produces valid standard entry with correct file count."""
        with TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            _populate_owasp_dir(tmpdir_path)

            entry = _build_owasp_manifest(tmpdir_path)

            assert isinstance(entry, DatasetRegistryEntry)
            assert entry.asset_id == "owasp-top10"
            assert entry.asset_class == "standard"
            assert entry.source_url == "https://owasp.org/www-project-top-ten/"
            assert entry.version == "2025"
            assert entry.license is None
            assert entry.content_hash.startswith("sha256:")

            # 4 files: index.html + 3 category files
            assert len(entry.files) == 4

            paths = [f.path for f in entry.files]
            assert "index.html" in paths
            assert "A01_Broken_Access_Control.html" in paths
            assert "A03_Injection.html" in paths
            assert "A07_SSRF.html" in paths

    def test_owasp_stable_hash(self):
        """Building OWASP manifest twice yields the same hash."""
        with TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            _populate_owasp_dir(tmpdir_path)

            entry1 = _build_owasp_manifest(tmpdir_path)
            entry2 = _build_owasp_manifest(tmpdir_path)

            assert entry1.content_hash == entry2.content_hash


# ── 4. CWE Subset Manifest (2 tests) ─────────────────────────────


class TestCweSubsetManifest:
    """CWE subset manifest from curated HTML files."""

    def test_cwe_manifest_metadata(self):
        """build_manifest produces valid standard entry for cwe-subset."""
        with TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            _populate_cwe_dir(tmpdir_path)

            entry = _build_cwe_manifest(tmpdir_path)

            assert isinstance(entry, DatasetRegistryEntry)
            assert entry.asset_id == "cwe-subset"
            assert entry.asset_class == "standard"
            assert entry.source_url == "https://cwe.mitre.org/top25/"
            assert entry.version == "2026-03"
            assert entry.content_hash.startswith("sha256:")
            assert len(entry.content_hash) == len("sha256:") + 64

            # 3 CWE files
            assert len(entry.files) == 3

            paths = [f.path for f in entry.files]
            assert "cwe_top25_2024.html" in paths
            assert "CWE-79_XSS.html" in paths
            assert "CWE-89_SQL_Injection.html" in paths

    def test_cwe_stable_hash(self):
        """Building CWE manifest twice yields the same hash."""
        with TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            _populate_cwe_dir(tmpdir_path)

            entry1 = _build_cwe_manifest(tmpdir_path)
            entry2 = _build_cwe_manifest(tmpdir_path)

            assert entry1.content_hash == entry2.content_hash


# ── 5. arXiv ML Metadata Manifest (3 tests) ──────────────────────


class TestArxivMlMetadataManifest:
    """arXiv ML metadata manifest from HTML docs + XML."""

    def test_arxiv_manifest_is_benchmark_not_standard(self):
        """arxiv-ml-metadata is asset_class='benchmark', not 'standard'."""
        with TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            _populate_arxiv_dir(tmpdir_path)

            entry = _build_arxiv_manifest(tmpdir_path)

            assert isinstance(entry, DatasetRegistryEntry)
            assert entry.asset_id == "arxiv-ml-metadata"
            assert entry.asset_class == "benchmark"
            assert entry.source_url == "https://info.arxiv.org/help/bulk_data.html"
            assert entry.version == "2026-03"
            assert entry.license is None
            assert entry.content_hash.startswith("sha256:")

            # 3 files: 2 HTML + 1 XML
            assert len(entry.files) == 3

            paths = [f.path for f in entry.files]
            assert "bulk_data.html" in paths
            assert "api_index.html" in paths
            assert "oai_identify.xml" in paths

    def test_arxiv_no_pdf_assumption(self):
        """arXiv metadata snapshot contains no PDF files — metadata only.

        This test makes explicit that the arXiv asset is metadata (HTML/XML),
        not full-text PDFs. If a PDF sneaks in, the test fails as a signal
        to revisit the asset scope.
        """
        with TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            _populate_arxiv_dir(tmpdir_path)

            entry = _build_arxiv_manifest(tmpdir_path)

            for fe in entry.files:
                assert not fe.path.endswith(".pdf"), (
                    f"Unexpected PDF in arXiv metadata snapshot: {fe.path}"
                )

    def test_arxiv_stable_hash(self):
        """Building arXiv manifest twice yields the same hash."""
        with TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            _populate_arxiv_dir(tmpdir_path)

            entry1 = _build_arxiv_manifest(tmpdir_path)
            entry2 = _build_arxiv_manifest(tmpdir_path)

            assert entry1.content_hash == entry2.content_hash


# ── 6. Mixed Registry Aggregation (2 tests) ──────────────────────


class TestMixedRegistryAggregation:
    """Registry document mixing old and new assets."""

    def test_aggregate_document_contains_all_entries(self):
        """Registry document mixes old (wcag, humaneval) and new (react-docs, owasp-top10)."""
        entries: list[DatasetRegistryEntry] = []

        # Old asset: WCAG (standard)
        with TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            (tmpdir_path / "wcag22.html").write_text("<html>WCAG 2.2</html>\n")
            entries.append(build_manifest(
                tmpdir_path,
                asset_id="wcag",
                asset_class="standard",
                source_url="https://www.w3.org/TR/WCAG22/",
                version="2.2",
            ))

        # Old asset: HumanEval (benchmark)
        with TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            (tmpdir_path / "problems.jsonl").write_text('{"task": "test"}\n')
            entries.append(build_manifest(
                tmpdir_path,
                asset_id="humaneval",
                asset_class="benchmark",
                source_url="https://github.com/openai/human-eval",
                version="v1.0",
                license="MIT",
            ))

        # New asset: react-docs (standard)
        with TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            _populate_react_docs_dir(tmpdir_path)
            entries.append(_build_react_docs_manifest(tmpdir_path))

        # New asset: owasp-top10 (standard)
        with TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            _populate_owasp_dir(tmpdir_path)
            entries.append(_build_owasp_manifest(tmpdir_path))

        doc = build_registry_document(entries, registry_version="1.0")

        assert isinstance(doc, DatasetRegistryDocument)
        assert len(doc.entries) == 4
        assert doc.version == "1.0"
        assert doc.generated_at.tzinfo is not None

        ids = {e.asset_id for e in doc.entries}
        assert ids == {"wcag", "humaneval", "react-docs", "owasp-top10"}

        # Verify mixed asset classes
        classes = {e.asset_id: e.asset_class for e in doc.entries}
        assert classes["wcag"] == "standard"
        assert classes["humaneval"] == "benchmark"
        assert classes["react-docs"] == "standard"
        assert classes["owasp-top10"] == "standard"

    def test_standards_registry_finds_new_assets_flat_layout(self):
        """build_standards_registry discovers new assets in flat staging layout."""
        with TemporaryDirectory() as staging:
            staging_path = Path(staging)

            # Create flat staging dirs for a mix of old + new standards
            wcag_dir = staging_path / "wcag"
            wcag_dir.mkdir()
            (wcag_dir / "wcag22.html").write_text("<html>WCAG 2.2</html>\n")

            react_dir = staging_path / "react-docs"
            react_dir.mkdir()
            ref = react_dir / "reference" / "react"
            ref.mkdir(parents=True)
            (ref / "useState.html").write_text("<html>useState</html>\n")

            owasp_dir = staging_path / "owasp-top10"
            owasp_dir.mkdir()
            (owasp_dir / "index.html").write_text("<html>OWASP Top 10</html>\n")

            doc = build_standards_registry(staging_path)

            assert isinstance(doc, DatasetRegistryDocument)
            ids = {e.asset_id for e in doc.entries}
            # Should find at least wcag, react-docs, owasp-top10
            assert "wcag" in ids
            assert "react-docs" in ids
            assert "owasp-top10" in ids

            # All discovered entries are standards
            for entry in doc.entries:
                assert entry.asset_class == "standard"


# ── 7. Regression (2 tests) ──────────────────────────────────────


class TestRegression026a:
    """Regression: 026a WCAG manifest and SKIP_NAMES still work."""

    def test_wcag_manifest_still_works(self):
        """WCAG manifest generation from 026a still produces valid output."""
        with TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            (tmpdir_path / "wcag22.html").write_text(
                "<!DOCTYPE html>\n"
                "<html><head><title>WCAG 2.2</title></head>\n"
                "<body><h1>Web Content Accessibility Guidelines 2.2</h1></body></html>\n"
            )

            entry = build_manifest(
                tmpdir_path,
                asset_id="wcag",
                asset_class="standard",
                source_url="https://www.w3.org/TR/WCAG22/",
                version="2.2",
            )

            assert isinstance(entry, DatasetRegistryEntry)
            assert entry.asset_id == "wcag"
            assert entry.asset_class == "standard"
            assert entry.content_hash.startswith("sha256:")
            assert len(entry.files) == 1
            assert entry.files[0].path == "wcag22.html"

    def test_skip_names_excludes_download_meta(self):
        """SKIP_NAMES still contains .download_meta.json (026a fix)."""
        assert ".download_meta.json" in SKIP_NAMES

        # Verify it actually works at manifest level
        with TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            (tmpdir_path / "data.html").write_text("<html>data</html>\n")

            entry_clean = build_manifest(
                tmpdir_path,
                asset_id="wcag",
                asset_class="standard",
                source_url="https://www.w3.org/TR/WCAG22/",
                version="2.2",
            )

            (tmpdir_path / ".download_meta.json").write_text(
                json.dumps({"downloaded_at": "2026-03-18T00:00:00Z"})
            )

            entry_with_meta = build_manifest(
                tmpdir_path,
                asset_id="wcag",
                asset_class="standard",
                source_url="https://www.w3.org/TR/WCAG22/",
                version="2.2",
            )

            assert entry_clean.content_hash == entry_with_meta.content_hash
            paths = {f.path for f in entry_with_meta.files}
            assert ".download_meta.json" not in paths
