"""Tests for Certificate Generation Pipeline -- schema conformance,
evidence_bundle_hash computation, verifier check pass, oracle_output_id
format, and counter-signal reporting.

Cycle-012, Sprint 2 -- Task 9.
"""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
from datetime import datetime, timezone
from typing import Any

import pytest

from backend.market.resolution import AgentSettlement, SettlementReport
from backend.osint.engine.corroboration import CorroborationResult
from backend.osint.engine.counter_signal import (
    COUNTER_SIGNAL_CLASSES,
    CounterSignalEvaluator,
    CounterSignalOutcome,
    CounterSignalResult,
)
from backend.osint.engine.scorer import CriterionScore
from backend.osint.models.evidence import EvidenceBundle
from backend.services.certificate_pipeline import (
    CalibrationCertificate,
    CertificatePipeline,
    CertificateSigningRefused,
)
from backend.services.theatre_resolution import TheatreResolutionResult

from backend.utils.canonical_json import canonical_json


# ===================================================================
# Fixtures
# ===================================================================


def _make_resolution_result(
    composite_score: float = 0.55,
    winning_idx: int = 1,
) -> TheatreResolutionResult:
    """Create a mock TheatreResolutionResult for testing."""
    # Build counter-signal results
    counter_signals = []
    for cls_name in COUNTER_SIGNAL_CLASSES:
        counter_signals.append(
            CounterSignalResult(
                signal_class=cls_name,
                outcome=CounterSignalOutcome.UNAVAILABLE,
                source_id=None,
                detail=f"INTELLIGENCE_GAP: no independent source connected for counter-signal class '{cls_name}'",
                allow_gap=True,
            )
        )

    # Build corroboration result
    corroboration = CorroborationResult(
        theatre_id="test_theatre",
        primary_bundles=[],
        corroborating_bundles=[],
        distinct_source_groups=1,
        corroboration_minimum=2,
        corroboration_met=False,
        dedup_log=[],
    )

    # Build criterion scores
    criterion_scores = [
        CriterionScore(
            criterion="corroboration_minimum_met",
            passed=False,
            score=0.7,
            detail="distinct_source_groups=1, minimum=2, met=False",
        ),
        CriterionScore(
            criterion="counter_signal_checked",
            passed=True,
            score=1.0,
            detail="Counter-signal criterion PASS",
        ),
    ]

    # Evidence bundle hash (valid SHA-256)
    evidence_hash = hashlib.sha256(b"{}").hexdigest()

    return TheatreResolutionResult(
        theatre_id="test_theatre",
        oracle_output_id="test_theatre_1709424000000",
        composite_score=composite_score,
        winning_outcome_index=winning_idx,
        winning_outcome_label=["Filed on time", "Filed late", "Not filed"][winning_idx],
        evidence_bundle_hash=evidence_hash,
        evidence_snapshots=[],
        corroboration_result=corroboration,
        counter_signal_results=counter_signals,
        criterion_scores=criterion_scores,
        source_manifest={
            "entries": [
                {
                    "source_id": "worldmonitor_cii",
                    "source_group": "alt_data_behavioural",
                    "independence_upstream_id": "worldmonitor",
                    "jurisdiction": "GLOBAL",
                    "access_surface": "intelligence",
                    "settlement_status": "PROVISIONAL",
                    "settlement_eligible": False,
                    "display_name": "World Monitor CII",
                },
            ],
            "registry_version": "0.3.2-wm",
        },
    )


def _make_settlement_report() -> SettlementReport:
    """Create a mock SettlementReport for testing."""
    settlement_composite = {
        "market_id": "mkt_test",
        "winning_outcome": 1,
        "agent_settlements": [
            {
                "agent_id": "agent_1",
                "winning_shares": 10.0,
                "payout": 10.0,
                "net_cashflow": 15.0,
                "realised_pnl": -5.0,
            },
        ],
    }
    canonical = canonical_json(settlement_composite)
    settlement_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    return SettlementReport(
        market_id="mkt_test",
        winning_outcome=1,
        winning_label="Filed late",
        total_payout=10.0,
        market_maker_pnl=5.0,
        agent_settlements=[
            AgentSettlement(
                agent_id="agent_1",
                shares_held=[0.0, 10.0, 0.0],
                winning_shares=10.0,
                payout=10.0,
                net_cashflow=15.0,
                realised_pnl=-5.0,
            ),
        ],
        commitment_hash=hashlib.sha256(b"commitment_test").hexdigest(),
        settlement_hash=settlement_hash,
    )


@pytest.fixture
def pipeline():
    return CertificatePipeline()


@pytest.fixture
def resolution_result():
    return _make_resolution_result()


@pytest.fixture
def settlement_report():
    return _make_settlement_report()


# ===================================================================
# Tests
# ===================================================================


class TestCertificatePipeline:
    """Tests for CertificatePipeline generation and verification."""

    def test_certificate_conforms_to_v100_schema(self, pipeline, resolution_result, settlement_report):
        """Certificate has all 16 required fields (v1.0.0 schema)."""
        cert = pipeline.generate(resolution_result, settlement_report)

        assert cert.schema_version == "1.0.0"
        assert cert.oracle_output_id is not None
        assert cert.theatre_id is not None
        assert isinstance(cert.composite_score, float)
        assert cert.evidence_bundle_hash is not None
        assert isinstance(cert.criteria_breakdown, list)
        assert isinstance(cert.osint_source_manifest, list)
        assert isinstance(cert.corroboration_status, dict)
        assert isinstance(cert.counter_signal_results, list)
        assert cert.verification_tier is not None
        assert cert.scored_at is not None
        assert cert.provider_version is not None
        assert cert.settlement_hash is not None
        assert cert.commitment_hash is not None
        assert isinstance(cert.winning_outcome, int)
        assert cert.winning_outcome_label is not None

    def test_evidence_bundle_hash_valid_sha256(self, pipeline, resolution_result, settlement_report):
        """evidence_bundle_hash is valid SHA-256 hex (64 chars)."""
        cert = pipeline.generate(resolution_result, settlement_report)

        assert len(cert.evidence_bundle_hash) == 64
        assert all(c in "0123456789abcdef" for c in cert.evidence_bundle_hash)

    def test_certificate_passes_all_21_checks(self, pipeline, resolution_result, settlement_report):
        """Certificate passes all 21 echelon_verify checks."""
        cert = pipeline.generate(resolution_result, settlement_report)
        all_passed, checks = pipeline.verify(cert)

        # Print failures for debugging
        if not all_passed:
            failures = [c for c in checks if "FAIL" in c]
            pytest.fail(f"Certificate failed checks: {failures}")

        assert all_passed is True
        assert len(checks) == 21

    def test_oracle_output_id_format(self, pipeline, resolution_result, settlement_report):
        """oracle_output_id matches {theatre_id}_{epoch_ms} format."""
        cert = pipeline.generate(resolution_result, settlement_report)

        assert cert.oracle_output_id == "test_theatre_1709424000000"
        assert cert.oracle_output_id.startswith("test_theatre_")
        parts = cert.oracle_output_id.rsplit("_", 1)
        assert parts[-1].isdigit()

    def test_counter_signal_results_exactly_11(self, pipeline, resolution_result, settlement_report):
        """counter_signal_results has exactly 11 entries."""
        cert = pipeline.generate(resolution_result, settlement_report)

        assert len(cert.counter_signal_results) == 11

    def test_counter_signal_results_all_unavailable(self, pipeline, resolution_result, settlement_report):
        """All counter-signal results should be UNAVAILABLE."""
        cert = pipeline.generate(resolution_result, settlement_report)

        for cs in cert.counter_signal_results:
            assert cs["outcome"] == "unavailable"

    def test_corroboration_status_fields(self, pipeline, resolution_result, settlement_report):
        """corroboration_status has minimum_met, penalty_factor, distinct_source_groups."""
        cert = pipeline.generate(resolution_result, settlement_report)

        corr = cert.corroboration_status
        assert "minimum_met" in corr
        assert "penalty_factor" in corr
        assert "distinct_source_groups" in corr
        assert corr["minimum_met"] is False
        assert corr["penalty_factor"] == 0.7
        assert corr["distinct_source_groups"] == 1

    def test_verification_tier_unverified(self, pipeline, resolution_result, settlement_report):
        """verification_tier is UNVERIFIED for first local-mode Theatre."""
        cert = pipeline.generate(resolution_result, settlement_report)

        assert cert.verification_tier == "UNVERIFIED"

    def test_provider_version(self, pipeline, resolution_result, settlement_report):
        """provider_version is set correctly."""
        cert = pipeline.generate(resolution_result, settlement_report)

        assert cert.provider_version == "012.1"

    def test_canonical_json_roundtrip(self, pipeline, resolution_result, settlement_report):
        """Certificate JSON roundtrips through canonical JSON without change."""
        cert = pipeline.generate(resolution_result, settlement_report)
        cert_dict = CertificatePipeline.certificate_to_dict(cert)

        canonical_1 = canonical_json(cert_dict)
        roundtrip = json.loads(canonical_1)
        canonical_2 = canonical_json(roundtrip)

        assert canonical_1 == canonical_2

    def test_settlement_and_commitment_hashes_present(self, pipeline, resolution_result, settlement_report):
        """settlement_hash and commitment_hash are valid SHA-256."""
        cert = pipeline.generate(resolution_result, settlement_report)

        assert len(cert.settlement_hash) == 64
        assert len(cert.commitment_hash) == 64
        assert all(c in "0123456789abcdef" for c in cert.settlement_hash)
        assert all(c in "0123456789abcdef" for c in cert.commitment_hash)

    def test_winning_outcome_carried_through(self, pipeline, settlement_report):
        """Winning outcome from resolution is carried to certificate."""
        resolution = _make_resolution_result(composite_score=0.1, winning_idx=2)
        cert = pipeline.generate(resolution, settlement_report)

        assert cert.winning_outcome == 2
        assert cert.winning_outcome_label == "Not filed"

    def test_local_mode_refuses_certificate_signing(self, pipeline, resolution_result, settlement_report):
        """local_mode=True refuses to sign — mock adapter data is not promotable."""
        with pytest.raises(CertificateSigningRefused, match="local_mode=True"):
            pipeline.generate(resolution_result, settlement_report, local_mode=True)

    def test_local_mode_false_allows_signing(self, pipeline, resolution_result, settlement_report):
        """local_mode=False (default) allows normal certificate generation."""
        cert = pipeline.generate(resolution_result, settlement_report, local_mode=False)
        assert cert.schema_version == "1.0.0"
        assert cert.verification_tier == "UNVERIFIED"
