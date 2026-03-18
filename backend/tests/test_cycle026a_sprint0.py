"""Cycle 026a Sprint 0 — Asset Policy + Registry Schema tests.

Tests:
1. Valid registry entry parses correctly
2. Registry entry with missing files is rejected
3. Invalid hash prefix is rejected
4. Valid anchor mapping with recognized anchors
5. Weak anchor mapping (no anchors, weakly_anchored=True)
6. Snapshot asset accepted by policy
7. Live asset accepted by policy
8. Live-as-immutable misuse rejected by policy
"""

from datetime import datetime, timezone

import pytest

from backend.schemas.eval_asset_registry import (
    DatasetRegistryDocument,
    DatasetRegistryEntry,
    RegistryFileEntry,
)
from backend.schemas.construct_anchor_schema import (
    AnchorClass,
    AnchorReference,
    EvaluationDimensionAnchor,
)
from backend.services.eval_asset_policy import (
    AssetDisposition,
    classify_asset,
    is_r2_eligible,
    reject_live_as_immutable,
    validate_snapshot_candidate,
)


# ── Helpers ──────────────────────────────────────────────────────────

def _make_file_entry(**overrides) -> dict:
    defaults = {
        "path": "raw/problem_file.jsonl",
        "size_bytes": 12345,
        "content_hash": "sha256:abc123def456",
    }
    defaults.update(overrides)
    return defaults


def _make_registry_entry(**overrides) -> dict:
    defaults = {
        "asset_id": "humaneval_v1",
        "asset_class": "benchmark",
        "source_url": "https://github.com/openai/human-eval",
        "version": "v1",
        "license": "MIT",
        "retrieved_at": datetime(2026, 3, 17, 12, 0, 0, tzinfo=timezone.utc),
        "content_hash": "sha256:toplevel123",
        "files": [_make_file_entry()],
    }
    defaults.update(overrides)
    return defaults


# ── Registry Schema Tests (3) ────────────────────────────────────────

class TestRegistrySchema:
    """Tests for eval_asset_registry.py schema models."""

    def test_valid_registry_entry(self):
        """A well-formed registry entry parses without error."""
        entry = DatasetRegistryEntry(**_make_registry_entry())

        assert entry.asset_id == "humaneval_v1"
        assert entry.asset_class == "benchmark"
        assert entry.source_url == "https://github.com/openai/human-eval"
        assert entry.version == "v1"
        assert entry.license == "MIT"
        assert entry.content_hash.startswith("sha256:")
        assert len(entry.files) == 1
        assert entry.files[0].path == "raw/problem_file.jsonl"
        assert entry.files[0].size_bytes == 12345

    def test_missing_files_rejected(self):
        """An entry with an empty files list is rejected."""
        with pytest.raises(Exception) as exc_info:
            DatasetRegistryEntry(**_make_registry_entry(files=[]))

        # Pydantic v2 raises ValidationError; check the message
        assert "files" in str(exc_info.value).lower() or "min_length" in str(exc_info.value).lower()

    def test_invalid_hash_prefix_rejected(self):
        """A content_hash without 'sha256:' prefix is rejected."""
        with pytest.raises(Exception) as exc_info:
            DatasetRegistryEntry(**_make_registry_entry(content_hash="md5:badprefix"))

        assert "sha256" in str(exc_info.value).lower()

    def test_invalid_asset_id_rejected(self):
        """An asset_id with non-filesystem-safe characters is rejected."""
        with pytest.raises(Exception) as exc_info:
            DatasetRegistryEntry(**_make_registry_entry(asset_id="Bad Asset ID!"))

        assert "asset_id" in str(exc_info.value).lower()

    def test_registry_document_round_trip(self):
        """A DatasetRegistryDocument can be created and serialized."""
        entry = DatasetRegistryEntry(**_make_registry_entry())
        doc = DatasetRegistryDocument(
            version="1.0",
            generated_at=datetime(2026, 3, 17, 12, 0, 0, tzinfo=timezone.utc),
            entries=[entry],
        )
        assert len(doc.entries) == 1
        assert doc.version == "1.0"

        # Round-trip through JSON
        json_str = doc.model_dump_json()
        restored = DatasetRegistryDocument.model_validate_json(json_str)
        assert restored.entries[0].asset_id == "humaneval_v1"

    def test_file_entry_hash_validation(self):
        """RegistryFileEntry rejects a bad hash prefix."""
        with pytest.raises(Exception):
            RegistryFileEntry(
                path="raw/test.jsonl",
                size_bytes=100,
                content_hash="bad:nope",
            )


# ── Anchor Schema Tests (2) ─────────────────────────────────────────

class TestAnchorSchema:
    """Tests for construct_anchor_schema.py models."""

    def test_valid_anchor_mapping(self):
        """A dimension with recognized anchors is not weakly anchored."""
        dim = EvaluationDimensionAnchor(
            dimension="code_correctness",
            anchors=[
                AnchorReference(
                    anchor_class=AnchorClass.DETERMINISTIC_CHECK,
                    anchor_id="pytest_pass_rate",
                    rationale="Deterministic test suite execution",
                ),
                AnchorReference(
                    anchor_class=AnchorClass.BENCHMARK_DATASET,
                    anchor_id="humaneval_v1",
                    rationale="HumanEval benchmark for code generation",
                ),
            ],
            weakly_anchored=False,
        )

        assert dim.dimension == "code_correctness"
        assert len(dim.anchors) == 2
        assert dim.anchors[0].anchor_class == AnchorClass.DETERMINISTIC_CHECK
        assert dim.anchors[1].anchor_class == AnchorClass.BENCHMARK_DATASET
        assert dim.weakly_anchored is False

    def test_weak_anchor_mapping(self):
        """A dimension with no anchors is weakly anchored."""
        dim = EvaluationDimensionAnchor(
            dimension="output_conformance",
            anchors=[],
            weakly_anchored=True,
        )

        assert dim.dimension == "output_conformance"
        assert len(dim.anchors) == 0
        assert dim.weakly_anchored is True

    def test_anchor_class_enum_values(self):
        """All four anchor classes are present and have expected values."""
        assert AnchorClass.DETERMINISTIC_CHECK.value == "deterministic_check"
        assert AnchorClass.BENCHMARK_DATASET.value == "benchmark_dataset"
        assert AnchorClass.PUBLIC_STANDARD.value == "public_standard"
        assert AnchorClass.LIVE_EXTERNAL_EVIDENCE.value == "live_external_evidence"
        assert len(AnchorClass) == 4


# ── Asset Policy Tests (3) ──────────────────────────────────────────

class TestAssetPolicy:
    """Tests for eval_asset_policy.py classification and enforcement."""

    def test_snapshot_asset_accepted(self):
        """Snapshot assets are classified correctly and are R2-eligible."""
        for asset in ["humaneval", "mbpp", "wcag", "aria-apg", "mmlu-pro"]:
            disposition = classify_asset(asset)
            assert disposition == AssetDisposition.SNAPSHOT, f"{asset} should be SNAPSHOT"
            assert is_r2_eligible(asset), f"{asset} should be R2-eligible"

            ok, reason = validate_snapshot_candidate(asset)
            assert ok is True, f"{asset}: {reason}"
            assert reason == "accepted"

    def test_live_asset_accepted(self):
        """Live-only assets are classified correctly and are not R2-eligible."""
        for asset in ["sec-edgar", "ofac", "un-sanctions", "gdelt", "global-fishing-watch"]:
            disposition = classify_asset(asset)
            assert disposition == AssetDisposition.LIVE, f"{asset} should be LIVE"
            assert not is_r2_eligible(asset), f"{asset} should NOT be R2-eligible"

            ok, reason = validate_snapshot_candidate(asset)
            assert ok is False
            assert "live-only" in reason.lower()

    def test_live_as_immutable_rejected(self):
        """Attempting to snapshot a live-only asset raises ValueError."""
        with pytest.raises(ValueError, match="Policy violation"):
            reject_live_as_immutable("sec-edgar")

        with pytest.raises(ValueError, match="Policy violation"):
            reject_live_as_immutable("gdelt")

        # Snapshot assets should NOT raise
        reject_live_as_immutable("humaneval")  # no error

    def test_unknown_asset_classification(self):
        """An unrecognized asset is classified as UNKNOWN."""
        disposition = classify_asset("some-random-thing")
        assert disposition == AssetDisposition.UNKNOWN
        assert not is_r2_eligible("some-random-thing")

        ok, reason = validate_snapshot_candidate("some-random-thing")
        assert ok is False
        assert "not recognized" in reason.lower()

    def test_case_insensitive_classification(self):
        """Classification normalizes to lowercase."""
        assert classify_asset("HUMANEVAL") == AssetDisposition.SNAPSHOT
        assert classify_asset("SEC-EDGAR") == AssetDisposition.LIVE
