"""Tests for Sponsored Theatre creation, validation, and commitment.

Covers: SponsoredTheatreConfig validation, source manifest building,
theatre creation, commitment protocol, review package, worst-case loss.

Cycle-012, Sprint 1 — Task 8.
"""
from __future__ import annotations

import json
import math
import os
import tempfile
from datetime import datetime, timezone
from decimal import Decimal

import pytest

from backend.chain.sepolia import MockSepoliaClient
from backend.market.exceptions import ParameterMutationAfterCommit
from backend.market.state import FeeSchedule
from backend.osint.models.registry import RegistryLoader
from backend.osint.source_manifest import (
    SettlementStatus,
    SourceManifestBuilder,
)
from backend.schemas.sponsored_theatre import (
    SponsoredTheatreConfig,
    SponsorReviewPackage,
)
from backend.services.market_theatre_bridge import MarketTheatreBridge
from backend.services.sponsored_theatre import SponsoredTheatreService


# ===================================================================
# Fixtures
# ===================================================================


def _make_test_registry() -> str:
    """Create a temporary registry JSON file for testing."""
    registry = {
        "version": "0.3.2-wm",
        "sources": [
            {
                "source_id": "worldmonitor_cii",
                "source_name": "World Monitor Country Instability Index",
                "source_group": "alt_data_behavioural",
                "priority_bucket": "scoring_grade",
                "resolution_role": "primary_evidence",
                "independence_upstream_id": "worldmonitor",
                "receipt_mode_minimum": "http_transcript",
                "world_monitor_domain": "intelligence",
                "settlement_eligible": False,
                "jurisdiction": "GLOBAL",
            },
            {
                "source_id": "worldmonitor_finance",
                "source_name": "World Monitor Finance Monitor",
                "source_group": "market_data",
                "priority_bucket": "scoring_grade",
                "resolution_role": "primary_evidence",
                "independence_upstream_id": "worldmonitor",
                "receipt_mode_minimum": "http_transcript",
                "world_monitor_domain": "market",
                "settlement_eligible": False,
                "jurisdiction": "GLOBAL",
            },
            {
                "source_id": "worldmonitor_maritime",
                "source_name": "World Monitor Maritime/AIS",
                "source_group": "maritime_ais",
                "priority_bucket": "scoring_grade",
                "resolution_role": "primary_evidence",
                "independence_upstream_id": "worldmonitor",
                "receipt_mode_minimum": "http_transcript",
                "world_monitor_domain": "maritime",
                "settlement_eligible": False,
                "jurisdiction": "GLOBAL",
            },
            {
                "source_id": "companies_house_uk",
                "source_name": "Companies House UK",
                "source_group": "government_registry",
                "priority_bucket": "settlement_grade",
                "resolution_role": "primary_evidence",
                "independence_upstream_id": "companies_house",
                "receipt_mode_minimum": "http_transcript",
                "settlement_eligible": True,
                "jurisdiction": "UK",
            },
        ],
    }

    fd, path = tempfile.mkstemp(suffix=".json")
    with os.fdopen(fd, "w") as f:
        json.dump(registry, f)
    return path


@pytest.fixture
def registry_path():
    """Create temp registry and clean up after test."""
    path = _make_test_registry()
    yield path
    os.unlink(path)


@pytest.fixture
def service(registry_path):
    """Create a SponsoredTheatreService with test dependencies."""
    loader = RegistryLoader(registry_path)
    manifest_builder = SourceManifestBuilder(loader)
    chain_client = MockSepoliaClient()
    market_bridge = MarketTheatreBridge()

    return SponsoredTheatreService(
        registry_loader=loader,
        manifest_builder=manifest_builder,
        chain_client=chain_client,
        market_bridge=market_bridge,
    )


@pytest.fixture
def valid_config() -> SponsoredTheatreConfig:
    """A valid SponsoredTheatreConfig for testing."""
    return SponsoredTheatreConfig(
        question="Will Acme Ltd file annual accounts by 30 Sep 2026?",
        resolution_date=datetime(2026, 9, 30, tzinfo=timezone.utc),
        committed_sources=["worldmonitor_cii", "worldmonitor_finance"],
        outcome_labels=["Filed on time", "Filed late", "Not filed"],
        liquidity_b=Decimal("100"),
        fee_schedule=FeeSchedule(trade_fee_bps=50, resolution_fee_bps=100),
        sponsor_id="sponsor_acme",
        sponsor_metadata={"company": "Acme Ltd", "jurisdiction": "UK"},
    )


# ===================================================================
# Task 1: SponsoredTheatreConfig validation tests
# ===================================================================


class TestSponsoredTheatreConfig:
    """Tests for SponsoredTheatreConfig Pydantic v2 model."""

    def test_valid_config_accepted(self, valid_config):
        """Valid config creates successfully."""
        assert valid_config.question == "Will Acme Ltd file annual accounts by 30 Sep 2026?"
        assert len(valid_config.outcome_labels) == 3
        assert valid_config.liquidity_b == Decimal("100")
        assert valid_config.sponsor_id == "sponsor_acme"

    def test_duplicate_outcome_labels_rejected(self):
        """Duplicate outcome labels are rejected."""
        with pytest.raises(Exception) as exc_info:
            SponsoredTheatreConfig(
                question="Will X happen by deadline?",
                resolution_date=datetime(2026, 9, 30, tzinfo=timezone.utc),
                committed_sources=["worldmonitor_cii"],
                outcome_labels=["Yes", "Yes"],
                liquidity_b=Decimal("100"),
                sponsor_id="sponsor_1",
            )
        assert "unique" in str(exc_info.value).lower()

    def test_single_outcome_rejected(self):
        """Single outcome label is rejected (min 2)."""
        with pytest.raises(Exception):
            SponsoredTheatreConfig(
                question="Will X happen by deadline?",
                resolution_date=datetime(2026, 9, 30, tzinfo=timezone.utc),
                committed_sources=["worldmonitor_cii"],
                outcome_labels=["Yes"],
                liquidity_b=Decimal("100"),
                sponsor_id="sponsor_1",
            )

    def test_empty_committed_sources_rejected(self):
        """Empty committed_sources is rejected (min 1)."""
        with pytest.raises(Exception):
            SponsoredTheatreConfig(
                question="Will X happen by deadline?",
                resolution_date=datetime(2026, 9, 30, tzinfo=timezone.utc),
                committed_sources=[],
                outcome_labels=["Yes", "No"],
                liquidity_b=Decimal("100"),
                sponsor_id="sponsor_1",
            )

    def test_zero_liquidity_b_rejected(self):
        """liquidity_b=0 is rejected (must be > 0)."""
        with pytest.raises(Exception):
            SponsoredTheatreConfig(
                question="Will X happen by deadline?",
                resolution_date=datetime(2026, 9, 30, tzinfo=timezone.utc),
                committed_sources=["worldmonitor_cii"],
                outcome_labels=["Yes", "No"],
                liquidity_b=Decimal("0"),
                sponsor_id="sponsor_1",
            )

    def test_negative_liquidity_b_rejected(self):
        """Negative liquidity_b is rejected."""
        with pytest.raises(Exception):
            SponsoredTheatreConfig(
                question="Will X happen by deadline?",
                resolution_date=datetime(2026, 9, 30, tzinfo=timezone.utc),
                committed_sources=["worldmonitor_cii"],
                outcome_labels=["Yes", "No"],
                liquidity_b=Decimal("-50"),
                sponsor_id="sponsor_1",
            )

    def test_short_question_rejected(self):
        """Question under 10 chars is rejected."""
        with pytest.raises(Exception):
            SponsoredTheatreConfig(
                question="Short?",
                resolution_date=datetime(2026, 9, 30, tzinfo=timezone.utc),
                committed_sources=["worldmonitor_cii"],
                outcome_labels=["Yes", "No"],
                liquidity_b=Decimal("100"),
                sponsor_id="sponsor_1",
            )

    def test_default_fee_schedule(self):
        """Default fee schedule is all zeros."""
        config = SponsoredTheatreConfig(
            question="Will X happen by the deadline date?",
            resolution_date=datetime(2026, 9, 30, tzinfo=timezone.utc),
            committed_sources=["worldmonitor_cii"],
            outcome_labels=["Yes", "No"],
            liquidity_b=Decimal("100"),
            sponsor_id="sponsor_1",
        )
        assert config.fee_schedule.trade_fee_bps == 0
        assert config.fee_schedule.resolution_fee_bps == 0


# ===================================================================
# Task 2: Source manifest builder tests
# ===================================================================


class TestSourceManifest:
    """Tests for SourceManifestBuilder."""

    def test_valid_sources_produce_manifest(self, registry_path):
        """Valid source IDs produce a validated manifest."""
        loader = RegistryLoader(registry_path)
        builder = SourceManifestBuilder(loader)
        manifest = builder.build(["worldmonitor_cii", "worldmonitor_finance"])

        assert manifest.validated is True
        assert len(manifest.entries) == 2
        assert manifest.validation_errors == []

    def test_nonexistent_source_rejected(self, registry_path):
        """Non-existent source ID produces validation error."""
        loader = RegistryLoader(registry_path)
        builder = SourceManifestBuilder(loader)
        manifest = builder.build(["nonexistent_source"])

        assert manifest.validated is False
        assert len(manifest.validation_errors) == 1
        assert "nonexistent_source" in manifest.validation_errors[0]

    def test_wm_sources_flagged_provisional(self, registry_path):
        """WM sources sharing upstream_id flagged as PROVISIONAL."""
        loader = RegistryLoader(registry_path)
        builder = SourceManifestBuilder(loader)
        manifest = builder.build(["worldmonitor_cii", "worldmonitor_finance"])

        for entry in manifest.entries:
            assert entry.settlement_status == SettlementStatus.PROVISIONAL

    def test_independent_source_not_provisional(self, registry_path):
        """Source with unique upstream_id is not PROVISIONAL."""
        loader = RegistryLoader(registry_path)
        builder = SourceManifestBuilder(loader)
        manifest = builder.build(["companies_house_uk"])

        assert len(manifest.entries) == 1
        assert manifest.entries[0].settlement_status == SettlementStatus.ELIGIBLE

    def test_registry_version_pinned(self, registry_path):
        """Manifest includes registry version."""
        loader = RegistryLoader(registry_path)
        builder = SourceManifestBuilder(loader)
        manifest = builder.build(["worldmonitor_cii"])

        assert manifest.registry_version != ""


# ===================================================================
# Task 3: Theatre creation service tests
# ===================================================================


class TestSponsoredTheatreCreation:
    """Tests for SponsoredTheatreService.create()."""

    def test_valid_creation_produces_review_package(self, service, valid_config):
        """Valid creation returns a complete SponsorReviewPackage."""
        review = service.create(valid_config)

        assert isinstance(review, SponsorReviewPackage)
        assert review.theatre_id.startswith("theatre_")
        assert review.commitment_hash != ""
        assert review.n_outcomes == 3
        assert review.outcome_labels == ["Filed on time", "Filed late", "Not filed"]
        assert review.liquidity_b == 100.0

    def test_invalid_source_ids_rejected(self, service):
        """Non-existent source IDs rejected with ValueError."""
        config = SponsoredTheatreConfig(
            question="Will X happen by the deadline date?",
            resolution_date=datetime(2026, 9, 30, tzinfo=timezone.utc),
            committed_sources=["nonexistent_source"],
            outcome_labels=["Yes", "No"],
            liquidity_b=Decimal("100"),
            sponsor_id="sponsor_1",
        )
        with pytest.raises(ValueError, match="Source validation failed"):
            service.create(config)

    def test_worst_case_loss_formula(self, service, valid_config):
        """Worst-case loss correctly computed as b * ln(n)."""
        review = service.create(valid_config)

        expected = 100.0 * math.log(3)  # b=100, n=3
        assert abs(review.worst_case_loss - expected) < 0.01

    def test_review_package_has_source_manifest(self, service, valid_config):
        """Review package includes source manifest."""
        review = service.create(valid_config)

        manifest = review.source_manifest
        assert manifest["validated"] is True
        assert len(manifest["entries"]) == 2

    def test_review_package_has_commitment_hash(self, service, valid_config):
        """Review package includes commitment hash."""
        review = service.create(valid_config)

        assert len(review.commitment_hash) == 64  # SHA-256 hex

    def test_commitment_hash_deterministic(self, service, valid_config):
        """Same inputs produce same commitment hash."""
        review1 = service.create(valid_config)

        # Create a second service and config with same params
        review2 = service.create(valid_config)

        assert review1.commitment_hash == review2.commitment_hash

    def test_committed_sources_sorted_in_hash(self, service, registry_path):
        """Committed sources are sorted before hashing for determinism."""
        config_a = SponsoredTheatreConfig(
            question="Will X happen by the deadline date?",
            resolution_date=datetime(2026, 9, 30, tzinfo=timezone.utc),
            committed_sources=["worldmonitor_cii", "worldmonitor_finance"],
            outcome_labels=["Yes", "No"],
            liquidity_b=Decimal("100"),
            sponsor_id="sponsor_1",
        )
        config_b = SponsoredTheatreConfig(
            question="Will X happen by the deadline date?",
            resolution_date=datetime(2026, 9, 30, tzinfo=timezone.utc),
            committed_sources=["worldmonitor_finance", "worldmonitor_cii"],
            outcome_labels=["Yes", "No"],
            liquidity_b=Decimal("100"),
            sponsor_id="sponsor_1",
        )

        review_a = service.create(config_a)
        review_b = service.create(config_b)

        assert review_a.commitment_hash == review_b.commitment_hash


# ===================================================================
# Task 7: Commitment protocol integration tests
# ===================================================================


class TestCommitmentProtocol:
    """Tests for the commit flow and commitment hash verification."""

    def test_commit_transitions_to_committed(self, service, valid_config):
        """commit() transitions Theatre to COMMITTED."""
        review = service.create(valid_config)
        result = service.commit(review.theatre_id)

        assert result["status"] == "TRADING"
        assert result["commitment_hash"] == review.commitment_hash
        assert result["tx_hash"].startswith("0xmock_commit_")

    def test_commit_verifies_lmsr_hash(self, service, valid_config):
        """commit() verifies LMSR-level commitment hash."""
        review = service.create(valid_config)
        result = service.commit(review.theatre_id)

        assert result["lmsr_hash_verified"] is True
        assert result["lmsr_commitment_hash"] is not None

    def test_double_commit_raises_mutation_error(self, service, valid_config):
        """Double commit raises ParameterMutationAfterCommit."""
        review = service.create(valid_config)
        service.commit(review.theatre_id)

        with pytest.raises(ParameterMutationAfterCommit):
            service.commit(review.theatre_id)

    def test_review_after_create(self, service, valid_config):
        """review() returns the same package after create()."""
        review = service.create(valid_config)
        review_again = service.review(review.theatre_id)

        assert review_again.theatre_id == review.theatre_id
        assert review_again.commitment_hash == review.commitment_hash

    def test_review_nonexistent_theatre_raises(self, service):
        """review() raises KeyError for non-existent theatre."""
        with pytest.raises(KeyError):
            service.review("nonexistent_theatre")

    def test_commit_produces_onchain_anchor(self, service, valid_config):
        """commit() calls MockSepoliaClient and returns tx_hash."""
        review = service.create(valid_config)
        result = service.commit(review.theatre_id)

        assert "tx_hash" in result
        assert result["tx_hash"].startswith("0xmock_commit_")
