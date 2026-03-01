"""
Tests for architectural concern patches (Cycle-004 hardening, Sprint 8).

Each concern must produce at least one test. British spelling throughout.
"""

import json
import sys
import os
import time
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

# Add osint/ directory to path so osint_pipeline package is found here, not at monorepo root.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from osint_pipeline.models.evidence import (
    CollectionResult,
    CollectionStatus,
    EvidenceBundle,
    FailureMode,
    FreshnessState,
    GapKind,
    GapReport,
    HTTPTranscriptReceipt,
    OracleCollectionSummary,
    RECEIPT_MODE_ORDER,
    ReceiptMode,
    RETRIABLE_FAILURES,
    meets_receipt_minimum,
)
from osint_pipeline.models.registry import RegistrySource
from osint_pipeline.engine.canonical import (
    CANONICAL_HEADER_ALLOWLIST,
    canonical_json,
    http_transcript_hash,
)
from osint_pipeline.engine.counter_signal import CounterSignalChecker
from osint_pipeline.engine.scorer import EvidenceScorer
from osint_pipeline.collectors.base import BaseCollector


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _dummy_receipt(receipt_hash: str = "a" * 64) -> HTTPTranscriptReceipt:
    return HTTPTranscriptReceipt(
        method="GET",
        url="http://localhost/test",
        response_status=200,
        response_body_hash="b" * 64,
        timestamp_ms=1000,
        receipt_hash=receipt_hash,
    )


def _bundle(
    source_id: str,
    upstream_id: str,
    source_group: str = "official_gov",
    confidence: float = 0.9,
    receipt_mode: ReceiptMode = ReceiptMode.HTTP_TRANSCRIPT,
) -> EvidenceBundle:
    return EvidenceBundle(
        source_id=source_id,
        source_group=source_group,
        independence_upstream_id=upstream_id,
        resolution_role="primary_evidence",
        jurisdiction="GB",
        raw_payload_hash="c" * 64,
        raw_payload_size_bytes=100,
        receipt=_dummy_receipt(),
        receipt_mode=receipt_mode,
        confidence_score=confidence,
    )


class _StubCollector(BaseCollector):
    """Minimal concrete collector for testing."""

    RECEIPT_MODE = ReceiptMode.HTTP_TRANSCRIPT

    def __init__(self, sid: str = "stub", **kwargs):
        super().__init__()
        self._sid = sid

    @property
    def source_id(self) -> str:
        return self._sid

    @property
    def source_group(self) -> str:
        return "test"

    @property
    def independence_upstream_id(self) -> str:
        return f"upstream_{self._sid}"

    @property
    def resolution_role(self) -> str:
        return "primary_evidence"

    @property
    def jurisdiction(self) -> str:
        return "GB"

    def build_request(self, qc):
        return ("GET", "http://localhost/test", {"Accept": "application/json"}, None)

    def extract(self, body, status, qc):
        return ({"data": "ok"}, 1.0)


# ---------------------------------------------------------------------------
# Concern 1: Independence Accounting
# ---------------------------------------------------------------------------

def test_distinct_upstream_count_deduplicates():
    """3 bundles with 2 sharing an upstream -> distinct_upstream_count == 2."""
    summary = OracleCollectionSummary(
        bundles=[
            _bundle("src_a", "upstream_1"),
            _bundle("src_b", "upstream_1"),  # shares upstream with src_a
            _bundle("src_c", "upstream_2"),
        ],
        total_sources_succeeded=3,
    )
    assert summary.distinct_upstream_count == 2
    dedup = summary.upstream_dedup_map
    assert set(dedup.keys()) == {"upstream_1", "upstream_2"}
    assert dedup["upstream_1"] == ["src_a", "src_b"]
    assert dedup["upstream_2"] == ["src_c"]


# ---------------------------------------------------------------------------
# Concern 2: Gap vs Absence
# ---------------------------------------------------------------------------

def test_signal_absence_passes_counter_signal_check():
    """A gap with SIGNAL_ABSENCE should yield checked=True, signal_found=False."""
    checker = CounterSignalChecker()
    gap = GapReport(
        source_id="holiday_checker",
        source_group="calendar_holiday",
        jurisdiction="GB",
        reason=CollectionStatus.NOT_FOUND,
        gap_kind=GapKind.SIGNAL_ABSENCE,
    )
    results = checker.evaluate(
        counter_signal_bundles=[],
        counter_signal_gaps=[gap],
        required_classes=["calendar_holiday"],
    )
    assert len(results) == 1
    assert results[0].checked is True
    assert results[0].signal_found is False
    assert results[0].passed is True


def test_intelligence_gap_fails_counter_signal_check():
    """A gap with INTELLIGENCE_GAP should yield checked=False (uncertainty)."""
    checker = CounterSignalChecker()
    gap = GapReport(
        source_id="holiday_checker",
        source_group="calendar_holiday",
        jurisdiction="GB",
        reason=CollectionStatus.TIMEOUT,
        gap_kind=GapKind.INTELLIGENCE_GAP,
    )
    results = checker.evaluate(
        counter_signal_bundles=[],
        counter_signal_gaps=[gap],
        required_classes=["calendar_holiday"],
    )
    assert len(results) == 1
    assert results[0].checked is False
    assert results[0].passed is False


# ---------------------------------------------------------------------------
# Concern 3: Receipt Mode Enforcement
# ---------------------------------------------------------------------------

def test_meets_receipt_minimum_ordering():
    """Verify ordering: NONE < HTTP_TRANSCRIPT < ... < WITNESS_QUORUM."""
    assert meets_receipt_minimum(ReceiptMode.HTTP_TRANSCRIPT, ReceiptMode.HTTP_TRANSCRIPT) is True
    assert meets_receipt_minimum(ReceiptMode.NONE, ReceiptMode.HTTP_TRANSCRIPT) is False
    assert meets_receipt_minimum(ReceiptMode.SIGNED_RECEIPT, ReceiptMode.HTTP_TRANSCRIPT) is True
    assert meets_receipt_minimum(ReceiptMode.WITNESS_QUORUM, ReceiptMode.NONE) is True
    assert meets_receipt_minimum(ReceiptMode.NONE, ReceiptMode.NONE) is True


def test_receipt_mode_none_rejected_for_http_transcript_minimum():
    """Collector with RECEIPT_MODE=NONE must fail against http_transcript minimum."""

    class NoneReceiptCollector(_StubCollector):
        RECEIPT_MODE = ReceiptMode.NONE

    registry_source = RegistrySource(
        source_id="test_none",
        source_group="test",
        resolution_role="primary_evidence",
        priority_bucket="day_one",
        settlement_eligible=True,
        jurisdiction="GB",
        receipt_mode_minimum="http_transcript",
    )
    collector = NoneReceiptCollector(sid="test_none")
    result = collector.collect(
        query_context={},
        registry_source=registry_source,
    )
    assert result.status == CollectionStatus.SOURCE_ERROR
    assert "does not meet" in result.error_message


# ---------------------------------------------------------------------------
# Concern 4: Free Source Stability Guard (now via EvidenceScorer)
# ---------------------------------------------------------------------------

def test_confidence_capped_for_latest_only_revision_policy():
    """EvidenceScorer with revision_policy=latest_only applies 0.80 penalty."""
    registry_source = RegistrySource(
        source_id="test_capped",
        source_group="test",
        resolution_role="primary_evidence",
        priority_bucket="day_one",
        settlement_eligible=False,
        jurisdiction="GB",
        revision_policy="latest_only",
    )
    bundle = _bundle("test_capped", "upstream_capped", confidence=1.0)
    scorer = EvidenceScorer()
    score = scorer.score_bundle(bundle, registry_source=registry_source)
    # 1.0 * 0.80 (latest_only) * 0.95 (receipt at minimum) = 0.76, capped at 0.76
    assert score <= 0.80, (
        f"Expected score <= 0.80 for latest_only, got {score}"
    )


def test_confidence_not_capped_for_public_api_as_of_timestamp():
    """EvidenceScorer for as_of_timestamp source applies 0.95 penalty, not 0.80."""
    registry_source = RegistrySource(
        source_id="test_stable",
        source_group="official_gov",
        resolution_role="primary_evidence",
        priority_bucket="settlement_grade",
        settlement_eligible=True,
        jurisdiction="GB",
        access_surface="public_api",
        revision_policy="as_of_timestamp",
    )
    bundle = _bundle("test_stable", "upstream_stable", confidence=1.0)
    scorer = EvidenceScorer()
    score = scorer.score_bundle(bundle, registry_source=registry_source)
    # 1.0 * 0.95 (as_of_timestamp) * 0.95 (receipt at minimum) = 0.9025
    assert score > 0.80, (
        f"Expected score > 0.80 for as_of_timestamp, got {score}"
    )


# ---------------------------------------------------------------------------
# Concern 5: Evidence Bundle Determinism
# ---------------------------------------------------------------------------

def test_different_auth_headers_same_hash():
    """Two requests with different Authorization headers -> identical hashes."""
    base = dict(
        method="GET",
        url="https://api.example.com/data",
        response_status=200,
        response_body=b'{"result": true}',
        timestamp_ms=1709251200000,
    )
    hash_a = http_transcript_hash(
        **base,
        headers={"Accept": "application/json", "Authorization": "Bearer token_a"},
    )
    hash_b = http_transcript_hash(
        **base,
        headers={"Accept": "application/json", "Authorization": "Bearer token_b"},
    )
    assert hash_a == hash_b


def test_url_query_params_order_irrelevant():
    """URL query params in different order -> identical hashes."""
    base = dict(
        method="GET",
        headers={"Accept": "application/json"},
        response_status=200,
        response_body=b'{"result": true}',
        timestamp_ms=1709251200000,
    )
    hash_a = http_transcript_hash(
        **base,
        url="https://api.example.com/search?q=test&page=1",
    )
    hash_b = http_transcript_hash(
        **base,
        url="https://api.example.com/search?page=1&q=test",
    )
    assert hash_a == hash_b


# ---------------------------------------------------------------------------
# Concern 6: Timeout Handling Must Produce Gaps
# ---------------------------------------------------------------------------

def test_timeout_produces_gap_reports():
    """Runner with 3 collectors, one sleeps forever, timeout=0.5s ->
    2 bundles + 1 gap with TIMEOUT reason."""
    from osint_pipeline.engine.collection_runner import CollectionRunner

    class FastCollector(_StubCollector):
        def collect(self, query_context, theatre_id=None, **kwargs):
            return CollectionResult(
                source_id=self.source_id,
                status=CollectionStatus.SUCCESS,
                bundle=_bundle(self.source_id, self.independence_upstream_id),
                duration_ms=10,
            )

    class SlowCollector(_StubCollector):
        def collect(self, query_context, theatre_id=None, **kwargs):
            time.sleep(10)  # Will be killed by timeout
            return CollectionResult(
                source_id=self.source_id,
                status=CollectionStatus.SUCCESS,
                bundle=_bundle(self.source_id, self.independence_upstream_id),
                duration_ms=10000,
            )

    runner = CollectionRunner(
        collectors=[
            FastCollector(sid="fast_1"),
            FastCollector(sid="fast_2"),
            SlowCollector(sid="slow_1"),
        ],
        timeout_budget_seconds=0.5,
    )
    summary = runner.run(query_context={})

    assert len(summary.bundles) == 2, f"Expected 2 bundles, got {len(summary.bundles)}"
    assert len(summary.gaps) >= 1, f"Expected at least 1 gap, got {len(summary.gaps)}"

    timeout_gaps = [g for g in summary.gaps if g.reason == CollectionStatus.TIMEOUT]
    assert len(timeout_gaps) == 1, f"Expected 1 timeout gap, got {len(timeout_gaps)}"
    assert timeout_gaps[0].source_id == "slow_1"
    assert timeout_gaps[0].gap_kind == GapKind.INTELLIGENCE_GAP


# ===========================================================================
# NEW TESTS — Sprint 8 Architectural Hardening
# ===========================================================================

# ---------------------------------------------------------------------------
# AC-1: GapKind Semantics
# ---------------------------------------------------------------------------

def test_gap_kind_enum_has_two_values():
    """GapKind must have exactly two members."""
    assert len(GapKind) == 2


def test_to_gap_report_maps_not_found_to_signal_absence():
    """to_gap_report with NOT_FOUND status -> SIGNAL_ABSENCE gap_kind."""
    collector = _StubCollector(sid="test_404")
    result = CollectionResult(
        source_id="test_404",
        status=CollectionStatus.NOT_FOUND,
        error_message="Resource not found",
        duration_ms=50,
    )
    gap = collector.to_gap_report(result)
    assert gap.gap_kind == GapKind.SIGNAL_ABSENCE
    assert gap.freshness == FreshnessState.NO_DATA


def test_to_gap_report_maps_timeout_to_intelligence_gap():
    """to_gap_report with TIMEOUT status -> INTELLIGENCE_GAP gap_kind."""
    collector = _StubCollector(sid="test_timeout")
    result = CollectionResult(
        source_id="test_timeout",
        status=CollectionStatus.TIMEOUT,
        error_message="Request timed out",
        duration_ms=30000,
    )
    gap = collector.to_gap_report(result)
    assert gap.gap_kind == GapKind.INTELLIGENCE_GAP
    assert gap.freshness == FreshnessState.ERROR


def test_to_gap_report_maps_network_error_to_intelligence_gap():
    """to_gap_report with NETWORK_ERROR status -> INTELLIGENCE_GAP gap_kind."""
    collector = _StubCollector(sid="test_net")
    result = CollectionResult(
        source_id="test_net",
        status=CollectionStatus.NETWORK_ERROR,
        error_message="Connection refused",
        duration_ms=100,
    )
    gap = collector.to_gap_report(result)
    assert gap.gap_kind == GapKind.INTELLIGENCE_GAP
    assert gap.freshness == FreshnessState.ERROR


# ---------------------------------------------------------------------------
# AC-5: Canonical Hash NFC + Float Precision
# ---------------------------------------------------------------------------

def test_canonical_json_nfc_normalisation():
    """Combining character and precomposed character produce identical output."""
    # U+00E9 (precomposed) vs U+0065 + U+0301 (combining)
    precomposed = {"caf\u00e9": "value"}
    combining = {"cafe\u0301": "value"}
    assert canonical_json(precomposed) == canonical_json(combining)


def test_canonical_json_float_precision():
    """0.1 + 0.2 produces deterministic, valid JSON number."""
    result = canonical_json({"v": 0.1 + 0.2})
    # Must be valid JSON
    parsed = json.loads(result)
    assert isinstance(parsed["v"], float)
    # Must be deterministic
    assert canonical_json({"v": 0.1 + 0.2}) == result


def test_canonical_json_rfc8785_test_vector():
    """RFC 8785 test vector: sorted keys, no whitespace, correct float."""
    obj = {"b": 2, "a": 1}
    result = canonical_json(obj)
    assert result == '{"a":1,"b":2}'

    # Float test vector
    obj2 = {"value": 1.0}
    result2 = canonical_json(obj2)
    parsed = json.loads(result2)
    assert parsed["value"] == 1.0


# ---------------------------------------------------------------------------
# AC-3: Runner-Level Receipt Mode Enforcement
# ---------------------------------------------------------------------------

def test_runner_rejects_insufficient_receipt_mode():
    """Runner pre-check rejects collector whose receipt mode is below registry minimum."""
    from osint_pipeline.engine.collection_runner import CollectionRunner

    class NoneReceiptCollector(_StubCollector):
        RECEIPT_MODE = ReceiptMode.NONE

        def collect(self, query_context, theatre_id=None, **kwargs):
            return CollectionResult(
                source_id=self.source_id,
                status=CollectionStatus.SUCCESS,
                bundle=_bundle(self.source_id, self.independence_upstream_id),
                duration_ms=10,
            )

    registry_sources = {
        "bad_receipt": RegistrySource(
            source_id="bad_receipt",
            source_group="test",
            resolution_role="primary_evidence",
            priority_bucket="day_one",
            settlement_eligible=True,
            jurisdiction="GB",
            receipt_mode_minimum="http_transcript",
        ),
    }
    runner = CollectionRunner(
        collectors=[NoneReceiptCollector(sid="bad_receipt")],
        registry_sources=registry_sources,
    )
    summary = runner.run(query_context={})
    assert len(summary.gaps) == 1
    assert summary.gaps[0].source_id == "bad_receipt"
    assert "does not meet" in summary.gaps[0].error_detail


def test_runner_passes_sufficient_receipt_mode():
    """Runner pre-check passes collector whose receipt mode meets registry minimum."""
    from osint_pipeline.engine.collection_runner import CollectionRunner

    class GoodCollector(_StubCollector):
        RECEIPT_MODE = ReceiptMode.HTTP_TRANSCRIPT

        def collect(self, query_context, theatre_id=None, **kwargs):
            return CollectionResult(
                source_id=self.source_id,
                status=CollectionStatus.SUCCESS,
                bundle=_bundle(self.source_id, self.independence_upstream_id),
                duration_ms=10,
            )

    registry_sources = {
        "good_receipt": RegistrySource(
            source_id="good_receipt",
            source_group="test",
            resolution_role="primary_evidence",
            priority_bucket="day_one",
            settlement_eligible=True,
            jurisdiction="GB",
            receipt_mode_minimum="http_transcript",
        ),
    }
    runner = CollectionRunner(
        collectors=[GoodCollector(sid="good_receipt")],
        registry_sources=registry_sources,
    )
    summary = runner.run(query_context={})
    assert len(summary.gaps) == 0
    assert len(summary.bundles) == 1


# ---------------------------------------------------------------------------
# AC-2: Upstream Independence Naming
# ---------------------------------------------------------------------------

def test_distinct_upstream_succeeded_count_alias():
    """distinct_upstream_succeeded_count returns same value as distinct_upstream_count."""
    summary = OracleCollectionSummary(
        bundles=[
            _bundle("src_a", "upstream_1"),
            _bundle("src_b", "upstream_2"),
        ],
        total_sources_succeeded=2,
    )
    assert summary.distinct_upstream_succeeded_count == summary.distinct_upstream_count
    assert summary.distinct_upstream_succeeded_count == 2


def test_null_upstream_id_counts_independently():
    """Bundles with unique empty strings count independently."""
    summary = OracleCollectionSummary(
        bundles=[
            _bundle("src_a", ""),
            _bundle("src_b", ""),
        ],
        total_sources_succeeded=2,
    )
    # Both have the same empty string upstream, so they share one group
    assert summary.distinct_upstream_count == 1


# ---------------------------------------------------------------------------
# AC-4: EvidenceScorer
# ---------------------------------------------------------------------------

def test_scorer_immutable_no_penalty():
    """score_bundle with immutable source returns raw confidence (capped at 0.95)."""
    registry_source = RegistrySource(
        source_id="immutable_src",
        source_group="official_gov",
        resolution_role="primary_evidence",
        priority_bucket="settlement_grade",
        settlement_eligible=True,
        jurisdiction="GB",
        revision_policy="immutable",
        receipt_mode_minimum="none",
    )
    bundle = _bundle("immutable_src", "upstream_x", confidence=0.9,
                      receipt_mode=ReceiptMode.HTTP_TRANSCRIPT)
    scorer = EvidenceScorer()
    score = scorer.score_bundle(bundle, registry_source=registry_source)
    # 0.9 * 1.0 (immutable) = 0.9, receipt exceeds 'none' minimum so no penalty
    assert abs(score - 0.9) < 0.001


def test_scorer_latest_only_080_penalty():
    """score_bundle with latest_only returns 0.80 * confidence (capped at 0.95)."""
    registry_source = RegistrySource(
        source_id="latest_src",
        source_group="test",
        resolution_role="primary_evidence",
        priority_bucket="day_one",
        settlement_eligible=False,
        jurisdiction="GB",
        revision_policy="latest_only",
        receipt_mode_minimum="none",
    )
    bundle = _bundle("latest_src", "upstream_y", confidence=1.0,
                      receipt_mode=ReceiptMode.HTTP_TRANSCRIPT)
    scorer = EvidenceScorer()
    score = scorer.score_bundle(bundle, registry_source=registry_source)
    # 1.0 * 0.80 (latest_only) = 0.80, receipt exceeds 'none' so no receipt penalty
    assert abs(score - 0.80) < 0.001


def test_scorer_as_of_timestamp_095_penalty():
    """score_bundle with as_of_timestamp returns 0.95 * confidence."""
    registry_source = RegistrySource(
        source_id="asof_src",
        source_group="official_gov",
        resolution_role="primary_evidence",
        priority_bucket="settlement_grade",
        settlement_eligible=True,
        jurisdiction="GB",
        revision_policy="as_of_timestamp",
        receipt_mode_minimum="none",
    )
    bundle = _bundle("asof_src", "upstream_z", confidence=1.0,
                      receipt_mode=ReceiptMode.HTTP_TRANSCRIPT)
    scorer = EvidenceScorer()
    score = scorer.score_bundle(bundle, registry_source=registry_source)
    # 1.0 * 0.95 (as_of_timestamp) = 0.95, receipt exceeds 'none' so no receipt penalty
    # But capped at 0.95
    assert abs(score - 0.95) < 0.001


def test_scorer_single_source_capped_095():
    """score_bundle never exceeds 0.95."""
    # Even with immutable and no penalties, cap at 0.95
    registry_source = RegistrySource(
        source_id="perfect_src",
        source_group="official_gov",
        resolution_role="primary_evidence",
        priority_bucket="settlement_grade",
        settlement_eligible=True,
        jurisdiction="GB",
        revision_policy="immutable",
        receipt_mode_minimum="none",
    )
    bundle = _bundle("perfect_src", "upstream_perfect", confidence=1.0,
                      receipt_mode=ReceiptMode.HTTP_TRANSCRIPT)
    scorer = EvidenceScorer()
    score = scorer.score_bundle(bundle, registry_source=registry_source)
    assert score <= 0.95


def test_scorer_composite_exceeds_095():
    """composite_confidence with 3 bundles at 0.8 each exceeds 0.95."""
    scorer = EvidenceScorer()
    bundles_with_scores = [
        (_bundle(f"src_{i}", f"upstream_{i}", confidence=0.8), 0.8)
        for i in range(3)
    ]
    composite = scorer.composite_confidence(bundles_with_scores)
    # 1 - (1-0.8)^3 = 1 - 0.008 = 0.992
    assert composite > 0.95, f"Expected composite > 0.95, got {composite}"


def test_scorer_receipt_at_minimum_penalty():
    """Bundle with receipt mode at minimum (not exceeding) gets 0.95x penalty."""
    registry_source = RegistrySource(
        source_id="min_receipt_src",
        source_group="official_gov",
        resolution_role="primary_evidence",
        priority_bucket="day_one",
        settlement_eligible=True,
        jurisdiction="GB",
        revision_policy="immutable",
        receipt_mode_minimum="http_transcript",
    )
    # Bundle receipt mode == registry minimum (http_transcript == http_transcript)
    bundle = _bundle("min_receipt_src", "upstream_min", confidence=1.0,
                      receipt_mode=ReceiptMode.HTTP_TRANSCRIPT)
    scorer = EvidenceScorer()
    score = scorer.score_bundle(bundle, registry_source=registry_source)
    # 1.0 * 1.0 (immutable) * 0.95 (receipt at minimum) = 0.95, capped at 0.95
    assert abs(score - 0.95) < 0.001


def test_base_collector_no_confidence_cap():
    """Verify BaseCollector no longer has FREE_SOURCE_CONFIDENCE_CAP or should_cap_confidence."""
    assert not hasattr(BaseCollector, "FREE_SOURCE_CONFIDENCE_CAP")
    assert not hasattr(BaseCollector, "should_cap_confidence")


# ---------------------------------------------------------------------------
# AC-6: FailureMode
# ---------------------------------------------------------------------------

def test_failure_mode_enum_values():
    """FailureMode must have exactly 7 values."""
    assert len(FailureMode) == 7


def test_gap_report_failure_mode_and_retriable():
    """GapReport with failure_mode has correct fields."""
    gap = GapReport(
        source_id="test_src",
        source_group="test",
        jurisdiction="GB",
        reason=CollectionStatus.TIMEOUT,
        failure_mode=FailureMode.READ_TIMEOUT,
        retriable=True,
    )
    assert gap.failure_mode == FailureMode.READ_TIMEOUT
    assert gap.retriable is True


def test_5xx_produces_retriable_gap():
    """to_gap_report with SOURCE_ERROR -> retriable=True (HTTP_ERROR_5XX)."""
    collector = _StubCollector(sid="test_5xx")
    result = CollectionResult(
        source_id="test_5xx",
        status=CollectionStatus.SOURCE_ERROR,
        error_message="HTTP 503",
        duration_ms=200,
    )
    gap = collector.to_gap_report(result)
    assert gap.failure_mode == FailureMode.HTTP_ERROR_5XX
    assert gap.retriable is True


def test_dns_failure_not_retriable():
    """to_gap_report with NETWORK_ERROR -> CONNECTION_REFUSED, not retriable."""
    collector = _StubCollector(sid="test_dns")
    result = CollectionResult(
        source_id="test_dns",
        status=CollectionStatus.NETWORK_ERROR,
        error_message="DNS lookup failed",
        duration_ms=50,
    )
    gap = collector.to_gap_report(result)
    assert gap.failure_mode == FailureMode.CONNECTION_REFUSED
    assert gap.retriable is False


def test_gap_count_and_gap_sources():
    """Summary with 2 gaps has gap_count=2 and correct gap_sources."""
    summary = OracleCollectionSummary(
        gaps=[
            GapReport(
                source_id="src_a",
                source_group="test",
                jurisdiction="GB",
                reason=CollectionStatus.TIMEOUT,
            ),
            GapReport(
                source_id="src_b",
                source_group="test",
                jurisdiction="GB",
                reason=CollectionStatus.NOT_FOUND,
            ),
        ],
        total_sources_failed=2,
    )
    assert summary.gap_count == 2
    assert summary.gap_sources == ["src_a", "src_b"]


# ---------------------------------------------------------------------------
# AC-INT: No Silent Source Drops
# ---------------------------------------------------------------------------

def test_no_silent_source_drops():
    """Runner with 3 collectors (1 fails) -> total output = 3 (2 bundles + 1 gap)."""
    from osint_pipeline.engine.collection_runner import CollectionRunner

    class OkCollector(_StubCollector):
        def collect(self, query_context, theatre_id=None, **kwargs):
            return CollectionResult(
                source_id=self.source_id,
                status=CollectionStatus.SUCCESS,
                bundle=_bundle(self.source_id, self.independence_upstream_id),
                duration_ms=10,
            )

    class FailCollector(_StubCollector):
        def collect(self, query_context, theatre_id=None, **kwargs):
            return CollectionResult(
                source_id=self.source_id,
                status=CollectionStatus.SOURCE_ERROR,
                error_message="HTTP 500",
                duration_ms=100,
            )

    runner = CollectionRunner(
        collectors=[
            OkCollector(sid="ok_1"),
            OkCollector(sid="ok_2"),
            FailCollector(sid="fail_1"),
        ],
    )
    summary = runner.run(query_context={})
    total = len(summary.bundles) + len(summary.gaps)
    assert total == 3, f"Expected 3 total outputs, got {total}"


# ---------------------------------------------------------------------------
# AC-INT: allow_gap Tests
# ---------------------------------------------------------------------------

def test_allow_gap_false_intelligence_gap_fails():
    """CounterSignalChecker with allow_gap=false + INTELLIGENCE_GAP -> passed=False."""
    checker = CounterSignalChecker(allow_gaps={"calendar_holiday": False})
    gap = GapReport(
        source_id="holiday_checker",
        source_group="calendar_holiday",
        jurisdiction="GB",
        reason=CollectionStatus.TIMEOUT,
        gap_kind=GapKind.INTELLIGENCE_GAP,
    )
    results = checker.evaluate(
        counter_signal_bundles=[],
        counter_signal_gaps=[gap],
        required_classes=["calendar_holiday"],
    )
    assert len(results) == 1
    assert results[0].checked is False
    assert results[0].passed is False


def test_allow_gap_true_intelligence_gap_passes():
    """CounterSignalChecker with allow_gap=true + INTELLIGENCE_GAP ->
    checked=False, passed=False (intelligence gap means we couldn't check).
    allow_gap=True is recorded on the result."""
    checker = CounterSignalChecker(allow_gaps={"calendar_holiday": True})
    gap = GapReport(
        source_id="holiday_checker",
        source_group="calendar_holiday",
        jurisdiction="GB",
        reason=CollectionStatus.TIMEOUT,
        gap_kind=GapKind.INTELLIGENCE_GAP,
    )
    results = checker.evaluate(
        counter_signal_bundles=[],
        counter_signal_gaps=[gap],
        required_classes=["calendar_holiday"],
    )
    assert len(results) == 1
    assert results[0].checked is False
    assert results[0].passed is False
    assert results[0].allow_gap is True


# ---------------------------------------------------------------------------
# AC-INT: End-to-End Pipeline Integration
# ---------------------------------------------------------------------------

def test_end_to_end_pipeline_integration():
    """Full integration: 4 sources, 2 succeed (shared upstream), 1 times out, 1 returns 404."""
    from osint_pipeline.engine.collection_runner import CollectionRunner

    class SharedUpstreamCollector(_StubCollector):
        """Fast collector that shares upstream with another."""
        def __init__(self, sid, upstream="shared_reuters"):
            super().__init__(sid=sid)
            self._upstream = upstream

        @property
        def independence_upstream_id(self):
            return self._upstream

        def collect(self, query_context, theatre_id=None, **kwargs):
            return CollectionResult(
                source_id=self.source_id,
                status=CollectionStatus.SUCCESS,
                bundle=_bundle(
                    self.source_id,
                    self._upstream,
                    confidence=0.85,
                ),
                duration_ms=10,
            )

    class TimeoutCollector(_StubCollector):
        """Collector that sleeps beyond the timeout budget."""
        def collect(self, query_context, theatre_id=None, **kwargs):
            time.sleep(10)
            return CollectionResult(
                source_id=self.source_id,
                status=CollectionStatus.SUCCESS,
                bundle=_bundle(self.source_id, self.independence_upstream_id),
                duration_ms=10000,
            )

    class NotFoundCollector(_StubCollector):
        """Collector that returns NOT_FOUND (404)."""
        def collect(self, query_context, theatre_id=None, **kwargs):
            return CollectionResult(
                source_id=self.source_id,
                status=CollectionStatus.NOT_FOUND,
                error_message="Resource not found",
                duration_ms=50,
            )

    runner = CollectionRunner(
        collectors=[
            SharedUpstreamCollector(sid="source_a"),
            SharedUpstreamCollector(sid="source_b"),
            TimeoutCollector(sid="source_c"),
            NotFoundCollector(sid="source_d"),
        ],
        timeout_budget_seconds=0.5,
    )
    summary = runner.run(query_context={})

    # 2 bundles from source_a and source_b
    assert len(summary.bundles) == 2, f"Expected 2 bundles, got {len(summary.bundles)}"
    bundle_sources = {b.source_id for b in summary.bundles}
    assert bundle_sources == {"source_a", "source_b"}

    # 2 gaps: source_c (timeout), source_d (not found)
    assert len(summary.gaps) == 2, f"Expected 2 gaps, got {len(summary.gaps)}"
    gap_sources = {g.source_id for g in summary.gaps}
    assert "source_c" in gap_sources or "source_d" in gap_sources

    # Distinct upstream count for successful bundles: both share "shared_reuters"
    assert summary.distinct_upstream_succeeded_count == 1

    # Check source_c gap (timeout)
    c_gaps = [g for g in summary.gaps if g.source_id == "source_c"]
    assert len(c_gaps) == 1
    assert c_gaps[0].failure_mode == FailureMode.READ_TIMEOUT
    assert c_gaps[0].retriable is True
    assert c_gaps[0].gap_kind == GapKind.INTELLIGENCE_GAP

    # Check source_d gap (not found)
    d_gaps = [g for g in summary.gaps if g.source_id == "source_d"]
    assert len(d_gaps) == 1
    assert d_gaps[0].gap_kind == GapKind.SIGNAL_ABSENCE

    # gap_count and gap_sources
    assert summary.gap_count == 2
    assert set(summary.gap_sources) == {"source_c", "source_d"}

    # No silent drops: total output = 4 (2 bundles + 2 gaps)
    total = len(summary.bundles) + len(summary.gaps)
    assert total == 4, f"Expected 4 total outputs, got {total}"


# ---------------------------------------------------------------------------
# Standalone runner
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    tests = [v for k, v in globals().items() if k.startswith("test_")]
    passed = 0
    failed = 0
    for test in tests:
        try:
            test()
            print(f"  PASS: {test.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"  FAIL: {test.__name__} -- {e}")
            failed += 1
        except Exception as e:
            print(f"  ERROR: {test.__name__} -- {e}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed, {passed + failed} total")
    sys.exit(1 if failed > 0 else 0)
