"""Sponsored Theatre Service — orchestrates Theatre creation and commitment.

Handles the sponsor onboarding workflow: configuration validation, LMSR
market creation, source manifest building, commitment hash computation,
review package generation, and the commit flow that freezes parameters.

Cycle-012, Sprint 1 — Theatre Creation + Sponsor Onboarding.
"""
from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone

from backend.utils.canonical_json import canonical_json

from backend.chain.sepolia import MockSepoliaClient
from backend.market.commitment import MarketCommitment
from backend.market.exceptions import ParameterMutationAfterCommit
from backend.market.lifecycle import MarketLifecycle
from backend.market.lmsr import LMSREngine
from backend.market.state import MarketPhase, MarketState
from backend.osint.source_manifest import (
    SourceManifest,
    SourceManifestBuilder,
)
from backend.schemas.sponsored_theatre import (
    SponsoredTheatreConfig,
    SponsorReviewPackage,
)
from backend.services.market_theatre_bridge import MarketTheatreBridge


# Version pins for commitment hash — tracks which cycle built each layer
VERSION_PINS = {
    "market": "010a",
    "engines": "010b",
    "osint": "011",
}


@dataclass
class TheatreRecord:
    """Internal Theatre record holding all created state.

    Not exposed to sponsors — internal bookkeeping only.
    """

    theatre_id: str
    config: SponsoredTheatreConfig
    source_manifest: SourceManifest
    market_id: str
    theatre_commitment_hash: str
    review_package: SponsorReviewPackage
    committed: bool = False
    committed_at: str | None = None
    tx_hash: str | None = None


class SponsoredTheatreService:
    """Orchestrates the Sponsored Theatre creation and commitment workflow.

    Flow:
        1. create(config) -> SponsorReviewPackage
        2. review(theatre_id) -> SponsorReviewPackage
        3. commit(theatre_id) -> confirmation dict
    """

    def __init__(
        self,
        registry_loader: object,
        manifest_builder: SourceManifestBuilder,
        chain_client: MockSepoliaClient,
        market_bridge: MarketTheatreBridge,
    ) -> None:
        self._registry_loader = registry_loader
        self._manifest_builder = manifest_builder
        self._chain_client = chain_client
        self._market_bridge = market_bridge
        self._theatres: dict[str, TheatreRecord] = {}

    def create(self, config: SponsoredTheatreConfig) -> SponsorReviewPackage:
        """Create a Sponsored Theatre from sponsor configuration.

        1. Validate committed_sources against OSINT registry
        2. Build source manifest (flag PROVISIONAL sources)
        3. Create LMSR market via MarketLifecycle.create_market()
        4. Generate TheatreTemplate from config + market
        5. Compute theatre-level commitment hash
        6. Compute worst-case loss: b * ln(n)
        7. Return SponsorReviewPackage

        Raises ValueError if source validation fails.
        """
        # 1. Validate sources
        manifest = self._manifest_builder.build(config.committed_sources)
        if not manifest.validated:
            raise ValueError(
                f"Source validation failed: {manifest.validation_errors}"
            )

        # 2. Generate IDs
        theatre_id = f"theatre_{uuid.uuid4().hex[:12]}"
        market_id = f"mkt_{theatre_id}"

        # 3. Create LMSR market via bridge
        b_float = float(config.liquidity_b)
        n_outcomes = len(config.outcome_labels)

        theatre_market = self._market_bridge.create_market_for_theatre(
            theatre_id=theatre_id,
            market_id=market_id,
            b=b_float,
            n_outcomes=n_outcomes,
            outcome_labels=config.outcome_labels,
            fee_schedule=config.fee_schedule,
        )

        # 4. Build template JSON
        template_json = self._build_template_json(
            theatre_id=theatre_id,
            config=config,
            market_id=market_id,
        )

        # 5. Compute theatre-level commitment hash
        theatre_commitment_hash = self._compute_theatre_commitment_hash(
            config=config,
            n_outcomes=n_outcomes,
        )

        # 6. Compute worst-case loss
        worst_case_loss = LMSREngine.worst_case_loss(b_float, n_outcomes)

        # 7. Build review package
        review_package = SponsorReviewPackage(
            theatre_id=theatre_id,
            template_json=template_json,
            commitment_hash=theatre_commitment_hash,
            worst_case_loss=worst_case_loss,
            source_manifest=self._manifest_to_dict(manifest),
            fee_schedule_breakdown={
                "trade_fee_bps": config.fee_schedule.trade_fee_bps,
                "resolution_fee_bps": config.fee_schedule.resolution_fee_bps,
            },
            n_outcomes=n_outcomes,
            outcome_labels=config.outcome_labels,
            liquidity_b=b_float,
            resolution_date=config.resolution_date,
        )

        # Store theatre record
        self._theatres[theatre_id] = TheatreRecord(
            theatre_id=theatre_id,
            config=config,
            source_manifest=manifest,
            market_id=market_id,
            theatre_commitment_hash=theatre_commitment_hash,
            review_package=review_package,
        )

        return review_package

    def review(self, theatre_id: str) -> SponsorReviewPackage:
        """Return the review package for an existing Theatre.

        Raises KeyError if theatre_id not found.
        """
        record = self._theatres.get(theatre_id)
        if record is None:
            raise KeyError(f"Theatre '{theatre_id}' not found")
        return record.review_package

    def commit(self, theatre_id: str) -> dict:
        """Sponsor approves — freeze parameters and transition to COMMITTED.

        1. Retrieve Theatre and MarketState
        2. Verify theatre commitment hash is deterministic (recompute matches)
        3. MarketLifecycle.commit(market) -> COMMITTED (computes LMSR hash)
        4. MarketLifecycle.open_trading(market) -> TRADING
        5. Stub on-chain anchor via MockSepoliaClient.publish_commitment
        6. Return confirmation dict

        Raises KeyError if theatre_id not found.
        Raises ParameterMutationAfterCommit if already committed.
        """
        record = self._theatres.get(theatre_id)
        if record is None:
            raise KeyError(f"Theatre '{theatre_id}' not found")

        if record.committed:
            raise ParameterMutationAfterCommit(
                f"Theatre '{theatre_id}' is already committed"
            )

        # Verify theatre commitment hash is deterministic
        recomputed = self._compute_theatre_commitment_hash(
            config=record.config,
            n_outcomes=len(record.config.outcome_labels),
        )
        if recomputed != record.theatre_commitment_hash:
            raise ValueError(
                "Theatre commitment hash mismatch — parameters may have been "
                "mutated between create and commit"
            )

        # Phase transitions via bridge
        self._market_bridge.transition_market(
            theatre_id, MarketPhase.COMMITTED
        )
        self._market_bridge.transition_market(
            theatre_id, MarketPhase.TRADING
        )

        # Verify LMSR-level commitment hash
        market_state = self._market_bridge.get_market_state(theatre_id)
        if market_state is not None:
            lmsr_hash_valid = MarketCommitment.verify_hash(market_state.market)
        else:
            lmsr_hash_valid = False

        # On-chain anchor (stubbed)
        tx_receipt = self._chain_client.publish_commitment(
            theatre_id=theatre_id,
            commitment_hash=record.theatre_commitment_hash,
        )

        # Update record
        record.committed = True
        record.committed_at = datetime.now(timezone.utc).isoformat()
        record.tx_hash = tx_receipt.tx_hash

        return {
            "theatre_id": theatre_id,
            "status": "TRADING",
            "commitment_hash": record.theatre_commitment_hash,
            "lmsr_commitment_hash": market_state.market.commitment_hash if market_state else None,
            "lmsr_hash_verified": lmsr_hash_valid,
            "tx_hash": tx_receipt.tx_hash,
            "committed_at": record.committed_at,
        }

    def get_theatre_record(self, theatre_id: str) -> TheatreRecord | None:
        """Get internal Theatre record. Used by other services."""
        return self._theatres.get(theatre_id)

    def _build_template_json(
        self,
        theatre_id: str,
        config: SponsoredTheatreConfig,
        market_id: str,
    ) -> dict:
        """Build the template JSON for the Theatre."""
        return {
            "theatre_id": theatre_id,
            "market_id": market_id,
            "question": config.question,
            "outcome_labels": config.outcome_labels,
            "resolution_date": config.resolution_date.isoformat(),
            "liquidity_b": float(config.liquidity_b),
            "fee_schedule": {
                "trade_fee_bps": config.fee_schedule.trade_fee_bps,
                "resolution_fee_bps": config.fee_schedule.resolution_fee_bps,
            },
            "committed_sources": sorted(config.committed_sources),
            "sponsor_id": config.sponsor_id,
            "sponsor_metadata": config.sponsor_metadata,
            "version_pins": VERSION_PINS,
            "execution_path": "SPONSORED_THEATRE",
        }

    def _compute_theatre_commitment_hash(
        self,
        config: SponsoredTheatreConfig,
        n_outcomes: int,
    ) -> str:
        """Compute the theatre-level commitment hash.

        Covers LMSR params, oracle config, and Theatre metadata.
        Uses SHA-256 over canonical JSON for determinism.
        """
        composite = {
            "lmsr_params": {
                "b": float(config.liquidity_b),
                "n_outcomes": n_outcomes,
                "outcome_labels": config.outcome_labels,
                "fee_schedule": {
                    "trade_fee_bps": config.fee_schedule.trade_fee_bps,
                    "resolution_fee_bps": config.fee_schedule.resolution_fee_bps,
                },
            },
            "oracle_config": {
                "committed_sources": sorted(config.committed_sources),
                "resolution_date": config.resolution_date.isoformat(),
                "corroboration_minimum": config.corroboration_minimum,
            },
            "theatre_metadata": {
                "template_id": "SPONSORED_THEATRE",
                "version_pins": VERSION_PINS,
            },
        }
        encoded = canonical_json(composite)
        return hashlib.sha256(encoded.encode("utf-8")).hexdigest()

    @staticmethod
    def _manifest_to_dict(manifest: SourceManifest) -> dict:
        """Convert SourceManifest to a JSON-serialisable dict."""
        return {
            "entries": [
                {
                    "source_id": e.source_id,
                    "source_group": e.source_group,
                    "independence_upstream_id": e.independence_upstream_id,
                    "jurisdiction": e.jurisdiction,
                    "access_surface": e.access_surface,
                    "settlement_status": e.settlement_status,
                    "settlement_eligible": e.settlement_eligible,
                    "display_name": e.display_name,
                }
                for e in manifest.entries
            ],
            "registry_version": manifest.registry_version,
            "validated": manifest.validated,
            "validation_errors": manifest.validation_errors,
        }
