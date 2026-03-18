"""Cycle 026c Sprint 1 — Curated Human-Centred Standards Pack tests.

Tests:
1. User-research-methods manifest from temp dir
2. Journey-patterns manifest from temp dir
3. Recovery-guidance manifest from temp dir
4. Standards registry includes new human-centred assets
5. Curated page set regression (GOV.UK URLs in catalog)
6. R2 path convention for new standards
"""
from __future__ import annotations

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

def _populate_user_research_dir(tmpdir: Path) -> None:
    """Create a minimal user-research-methods file tree."""
    (tmpdir / "index.html").write_text(
        "<!DOCTYPE html>\n"
        "<html><head><title>User Research</title></head>\n"
        "<body><h1>User research for government services</h1></body></html>\n"
    )
    methods = tmpdir / "methods"
    methods.mkdir()
    (methods / "interviews.html").write_text(
        "<!DOCTYPE html>\n<html><body><h1>Interviews</h1></body></html>\n"
    )
    (methods / "surveys.html").write_text(
        "<!DOCTYPE html>\n<html><body><h1>Surveys</h1></body></html>\n"
    )


def _populate_journey_patterns_dir(tmpdir: Path) -> None:
    """Create a minimal journey-patterns file tree."""
    (tmpdir / "index.html").write_text(
        "<!DOCTYPE html>\n"
        "<html><head><title>Design Patterns</title></head>\n"
        "<body><h1>GOV.UK Design System Patterns</h1></body></html>\n"
    )
    patterns = tmpdir / "patterns"
    patterns.mkdir()
    (patterns / "check-answers.html").write_text(
        "<!DOCTYPE html>\n<html><body><h1>Check answers</h1></body></html>\n"
    )
    (patterns / "step-by-step.html").write_text(
        "<!DOCTYPE html>\n<html><body><h1>Step by step navigation</h1></body></html>\n"
    )
    (patterns / "task-list.html").write_text(
        "<!DOCTYPE html>\n<html><body><h1>Task list</h1></body></html>\n"
    )


def _populate_recovery_guidance_dir(tmpdir: Path) -> None:
    """Create a minimal recovery-guidance file tree."""
    (tmpdir / "validation.html").write_text(
        "<!DOCTYPE html>\n"
        "<html><head><title>Validation</title></head>\n"
        "<body><h1>Ask users for validation</h1></body></html>\n"
    )
    (tmpdir / "error-summary.html").write_text(
        "<!DOCTYPE html>\n<html><body><h1>Error summary</h1></body></html>\n"
    )
    (tmpdir / "error-message.html").write_text(
        "<!DOCTYPE html>\n<html><body><h1>Error message</h1></body></html>\n"
    )


# ── Tests ────────────────────────────────────────────────────────────

class TestUserResearchManifest:
    """Test 1: user-research-methods manifest generation."""

    def test_manifest_from_temp_dir(self):
        with TemporaryDirectory() as tmpdir:
            p = Path(tmpdir)
            _populate_user_research_dir(p)

            entry = build_manifest(
                p,
                asset_id="user-research-methods",
                asset_class="standard",
                source_url="https://www.gov.uk/service-manual/user-research",
                version="2026-03",
                license="OGL-3.0",
            )

            assert isinstance(entry, DatasetRegistryEntry)
            assert entry.asset_id == "user-research-methods"
            assert entry.asset_class == "standard"
            assert entry.version == "2026-03"
            assert entry.license == "OGL-3.0"
            assert entry.content_hash.startswith("sha256:")
            assert len(entry.files) == 3  # index + methods/interviews + methods/surveys

    def test_stable_hash(self):
        with TemporaryDirectory() as tmpdir:
            p = Path(tmpdir)
            _populate_user_research_dir(p)
            e1 = build_manifest(p, asset_id="user-research-methods", asset_class="standard",
                                source_url="https://www.gov.uk/service-manual/user-research",
                                version="2026-03")
            e2 = build_manifest(p, asset_id="user-research-methods", asset_class="standard",
                                source_url="https://www.gov.uk/service-manual/user-research",
                                version="2026-03")
            assert e1.content_hash == e2.content_hash

    def test_files_sorted_by_path(self):
        with TemporaryDirectory() as tmpdir:
            p = Path(tmpdir)
            _populate_user_research_dir(p)
            entry = build_manifest(p, asset_id="user-research-methods", asset_class="standard",
                                   source_url="x", version="v1")
            paths = [f.path for f in entry.files]
            assert paths == sorted(paths)


class TestJourneyPatternsManifest:
    """Test 2: journey-patterns manifest generation."""

    def test_manifest_from_temp_dir(self):
        with TemporaryDirectory() as tmpdir:
            p = Path(tmpdir)
            _populate_journey_patterns_dir(p)

            entry = build_manifest(
                p,
                asset_id="journey-patterns",
                asset_class="standard",
                source_url="https://design-system.service.gov.uk/patterns/",
                version="2026-03",
                license="OGL-3.0",
            )

            assert isinstance(entry, DatasetRegistryEntry)
            assert entry.asset_id == "journey-patterns"
            assert entry.asset_class == "standard"
            assert entry.version == "2026-03"
            assert entry.license == "OGL-3.0"
            assert entry.content_hash.startswith("sha256:")
            # 4 files: index + patterns/check-answers + step-by-step + task-list
            assert len(entry.files) == 4

    def test_stable_hash(self):
        with TemporaryDirectory() as tmpdir:
            p = Path(tmpdir)
            _populate_journey_patterns_dir(p)
            e1 = build_manifest(p, asset_id="journey-patterns", asset_class="standard",
                                source_url="x", version="v1")
            e2 = build_manifest(p, asset_id="journey-patterns", asset_class="standard",
                                source_url="x", version="v1")
            assert e1.content_hash == e2.content_hash

    def test_subdirectory_structure_preserved(self):
        with TemporaryDirectory() as tmpdir:
            p = Path(tmpdir)
            _populate_journey_patterns_dir(p)
            entry = build_manifest(p, asset_id="journey-patterns", asset_class="standard",
                                   source_url="x", version="v1")
            paths = [f.path for f in entry.files]
            assert any("patterns/" in path for path in paths)


class TestRecoveryGuidanceManifest:
    """Test 3: recovery-guidance manifest generation."""

    def test_manifest_from_temp_dir(self):
        with TemporaryDirectory() as tmpdir:
            p = Path(tmpdir)
            _populate_recovery_guidance_dir(p)

            entry = build_manifest(
                p,
                asset_id="recovery-guidance",
                asset_class="standard",
                source_url="https://design-system.service.gov.uk/patterns/validation/",
                version="2026-03",
                license="OGL-3.0",
            )

            assert isinstance(entry, DatasetRegistryEntry)
            assert entry.asset_id == "recovery-guidance"
            assert entry.asset_class == "standard"
            assert entry.version == "2026-03"
            assert entry.license == "OGL-3.0"
            assert entry.content_hash.startswith("sha256:")
            assert len(entry.files) == 3  # validation + error-summary + error-message

    def test_stable_hash(self):
        with TemporaryDirectory() as tmpdir:
            p = Path(tmpdir)
            _populate_recovery_guidance_dir(p)
            e1 = build_manifest(p, asset_id="recovery-guidance", asset_class="standard",
                                source_url="x", version="v1")
            e2 = build_manifest(p, asset_id="recovery-guidance", asset_class="standard",
                                source_url="x", version="v1")
            assert e1.content_hash == e2.content_hash

    def test_all_files_have_valid_hashes(self):
        with TemporaryDirectory() as tmpdir:
            p = Path(tmpdir)
            _populate_recovery_guidance_dir(p)
            entry = build_manifest(p, asset_id="recovery-guidance", asset_class="standard",
                                   source_url="x", version="v1")
            for fe in entry.files:
                assert fe.content_hash.startswith("sha256:")
                assert len(fe.content_hash) == len("sha256:") + 64
                assert fe.size_bytes > 0


class TestStandardsRegistryIncludesNewAssets:
    """Test 4: standards registry includes the new human-centred assets."""

    def test_registry_with_all_new_assets(self):
        """build_standards_registry picks up new human-centred assets."""
        with TemporaryDirectory() as staging:
            sp = Path(staging)

            # user-research-methods (flat layout)
            urm = sp / "user-research-methods"
            urm.mkdir()
            _populate_user_research_dir(urm)

            # journey-patterns (flat layout)
            jp = sp / "journey-patterns"
            jp.mkdir()
            _populate_journey_patterns_dir(jp)

            # recovery-guidance (flat layout)
            rg = sp / "recovery-guidance"
            rg.mkdir()
            _populate_recovery_guidance_dir(rg)

            doc = build_standards_registry(sp)

            assert isinstance(doc, DatasetRegistryDocument)
            ids = {e.asset_id for e in doc.entries}
            assert "user-research-methods" in ids
            assert "journey-patterns" in ids
            assert "recovery-guidance" in ids

    def test_registry_with_r2_layout(self):
        """build_standards_registry finds new assets in R2-normalized layout."""
        with TemporaryDirectory() as staging:
            sp = Path(staging)

            # user-research-methods (R2 layout)
            urm_raw = sp / "standards" / "user-research-methods" / "2026-03" / "raw"
            urm_raw.mkdir(parents=True)
            _populate_user_research_dir(urm_raw)

            doc = build_standards_registry(sp)
            ids = {e.asset_id for e in doc.entries}
            assert "user-research-methods" in ids


class TestCuratedPageSetRegression:
    """Test 5: curated page sets reference GOV.UK URLs."""

    _NEW_ASSET_IDS = ["user-research-methods", "journey-patterns", "recovery-guidance"]

    @pytest.mark.parametrize("asset_id", _NEW_ASSET_IDS)
    def test_catalog_url_is_gov_uk(self, asset_id: str):
        entry = next(e for e in STANDARDS_CATALOG if e[0] == asset_id)
        assert "gov.uk" in entry[1]

    @pytest.mark.parametrize("asset_id", _NEW_ASSET_IDS)
    def test_catalog_license_is_ogl(self, asset_id: str):
        entry = next(e for e in STANDARDS_CATALOG if e[0] == asset_id)
        assert entry[3] == "OGL-3.0"

    def test_all_new_assets_in_catalog(self):
        catalog_ids = {e[0] for e in STANDARDS_CATALOG}
        for aid in self._NEW_ASSET_IDS:
            assert aid in catalog_ids


class TestR2PathConventionNewStandards:
    """Test 6: R2 path convention for new standards."""

    @pytest.mark.parametrize("asset_id,version", [
        ("user-research-methods", "2026-03"),
        ("journey-patterns", "2026-03"),
        ("recovery-guidance", "2026-03"),
    ])
    def test_r2_key_prefix(self, asset_id: str, version: str):
        prefix = r2_key_prefix(asset_id, version, asset_class="standard")
        assert prefix == f"standards/{asset_id}/{version}/"
