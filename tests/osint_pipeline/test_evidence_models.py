"""Tests for evidence models (Pydantic v2).

T1.3: model instantiation, hash field validation, .succeeded property,
.coverage_ratio, independence dedup, gap kinds.
"""

from __future__ import annotations

import pytest

from osint_pipeline.models.evidence import (
    CollectionResult,
    CollectionStatus,
    EvidenceBundle,
    FreshnessState,
    GapKind,
    GapReport,
    HTTPTranscriptReceipt,
    OracleCollectionSummary,
    RECEIPT_MODE_ORDER,
    ReceiptMode,
    meets_receipt_minimum,
)

from conftest import make_bundle, make_receipt


class TestHTTPTranscriptReceipt:
    """Receipt model tests."""

    def test_valid_receipt(self):
        """Receipt with valid 64-char hex hashes."""
        r = make_receipt()
        assert len(r.receipt_hash) == 64
        assert len(r.response_body_hash) == 64

    def test_invalid_hash_rejected(self):
        """Non-hex or wrong-length hash raises ValidationError."""
        with pytest.raises(Exception):
            HTTPTranscriptReceipt(
                method="GET",
                url="http://test",
                response_status=200,
                response_body_hash="too_short",
                timestamp_ms=1000,
                receipt_hash="a" * 64,
            )

    def test_uppercase_hex_rejected(self):
        """Uppercase hex is rejected (must be lowercase)."""
        with pytest.raises(Exception):
            HTTPTranscriptReceipt(
                method="GET",
                url="http://test",
                response_status=200,
                response_body_hash="A" * 64,
                timestamp_ms=1000,
                receipt_hash="a" * 64,
            )


class TestEvidenceBundle:
    """Evidence bundle model tests."""

    def test_bundle_creation(self):
        """Bundle with all required fields."""
        b = make_bundle()
        assert b.source_id == "test_source"
        assert b.confidence_score == 0.9
        assert b.receipt_mode == ReceiptMode.HTTP_TRANSCRIPT

    def test_bundle_id_auto_generated(self):
        """bundle_id is auto-generated UUID."""
        b1 = make_bundle()
        b2 = make_bundle()
        assert b1.bundle_id != b2.bundle_id
        assert len(b1.bundle_id) == 36  # UUID format

    def test_confidence_bounds(self):
        """Confidence must be in [0.0, 1.0]."""
        make_bundle(confidence=0.0)  # OK
        make_bundle(confidence=1.0)  # OK
        with pytest.raises(Exception):
            make_bundle(confidence=1.1)
        with pytest.raises(Exception):
            make_bundle(confidence=-0.1)

    def test_invalid_payload_hash_rejected(self):
        """raw_payload_hash must be 64-char lowercase hex."""
        with pytest.raises(Exception):
            make_bundle(raw_payload_hash="invalid")


class TestCollectionResult:
    """CollectionResult tests."""

    def test_succeeded_true(self):
        """succeeded is True when status=SUCCESS and bundle present."""
        result = CollectionResult(
            source_id="test",
            status=CollectionStatus.SUCCESS,
            bundle=make_bundle(),
        )
        assert result.succeeded is True

    def test_succeeded_false_no_bundle(self):
        """succeeded is False when bundle is None."""
        result = CollectionResult(
            source_id="test",
            status=CollectionStatus.SUCCESS,
            bundle=None,
        )
        assert result.succeeded is False

    def test_succeeded_false_error_status(self):
        """succeeded is False for non-SUCCESS status."""
        result = CollectionResult(
            source_id="test",
            status=CollectionStatus.TIMEOUT,
            error_message="timed out",
        )
        assert result.succeeded is False


class TestGapReport:
    """GapReport tests."""

    def test_default_gap_kind(self):
        """Default gap_kind is INTELLIGENCE_GAP."""
        gap = GapReport(
            source_id="test",
            source_group="test_group",
            jurisdiction="GB",
            reason=CollectionStatus.TIMEOUT,
        )
        assert gap.gap_kind == GapKind.INTELLIGENCE_GAP

    def test_signal_absence_kind(self):
        """Can create gap with SIGNAL_ABSENCE."""
        gap = GapReport(
            source_id="test",
            source_group="test_group",
            jurisdiction="GB",
            reason=CollectionStatus.NOT_FOUND,
            gap_kind=GapKind.SIGNAL_ABSENCE,
        )
        assert gap.gap_kind == GapKind.SIGNAL_ABSENCE


class TestOracleCollectionSummary:
    """Summary model tests."""

    def test_coverage_ratio(self):
        """coverage_ratio computes correctly."""
        summary = OracleCollectionSummary(
            total_sources_attempted=10,
            total_sources_succeeded=7,
        )
        assert summary.coverage_ratio == 0.7

    def test_coverage_ratio_zero_attempted(self):
        """coverage_ratio is 0.0 when nothing attempted."""
        summary = OracleCollectionSummary()
        assert summary.coverage_ratio == 0.0

    def test_distinct_upstream_count(self):
        """3 bundles with 2 sharing upstream -> distinct_upstream_count == 2."""
        summary = OracleCollectionSummary(
            bundles=[
                make_bundle("src_a", "upstream_1"),
                make_bundle("src_b", "upstream_1"),
                make_bundle("src_c", "upstream_2"),
            ],
            total_sources_succeeded=3,
        )
        assert summary.distinct_upstream_count == 2

    def test_upstream_dedup_map(self):
        """Dedup map groups source_ids by upstream."""
        summary = OracleCollectionSummary(
            bundles=[
                make_bundle("src_a", "upstream_1"),
                make_bundle("src_b", "upstream_1"),
                make_bundle("src_c", "upstream_2"),
            ],
            total_sources_succeeded=3,
        )
        dedup = summary.upstream_dedup_map
        assert set(dedup.keys()) == {"upstream_1", "upstream_2"}
        assert dedup["upstream_1"] == ["src_a", "src_b"]
        assert dedup["upstream_2"] == ["src_c"]


class TestReceiptModeEnforcement:
    """Receipt mode ordering and enforcement tests."""

    def test_ordering(self):
        """NONE < HTTP_TRANSCRIPT < ... < WITNESS_QUORUM."""
        assert meets_receipt_minimum(ReceiptMode.HTTP_TRANSCRIPT, ReceiptMode.HTTP_TRANSCRIPT) is True
        assert meets_receipt_minimum(ReceiptMode.NONE, ReceiptMode.HTTP_TRANSCRIPT) is False
        assert meets_receipt_minimum(ReceiptMode.SIGNED_RECEIPT, ReceiptMode.HTTP_TRANSCRIPT) is True
        assert meets_receipt_minimum(ReceiptMode.WITNESS_QUORUM, ReceiptMode.NONE) is True
        assert meets_receipt_minimum(ReceiptMode.NONE, ReceiptMode.NONE) is True

    def test_all_modes_in_order(self):
        """RECEIPT_MODE_ORDER contains all modes."""
        assert len(RECEIPT_MODE_ORDER) == 5
        assert RECEIPT_MODE_ORDER[0] == ReceiptMode.NONE
        assert RECEIPT_MODE_ORDER[-1] == ReceiptMode.WITNESS_QUORUM
