"""Commitment Protocol — market parameter commitment hash.

SHA-256 over canonical JSON (RFC 8785) of committed market parameters.
Reuses theatre/engine/canonical_json.py for deterministic serialisation.
"""
from __future__ import annotations

import hashlib

from theatre.engine.canonical_json import canonical_json

from backend.market.state import MarketState

# 010a stub — no real oracle infrastructure
ORACLE_CONFIG_STUB = {"type": "manual", "version": "v0"}


class MarketCommitment:
    """Generates and verifies market commitment hashes."""

    @staticmethod
    def compute_hash(market: MarketState) -> str:
        """SHA-256 over canonical JSON of committed market parameters.

        Composite object keys (sorted by canonical_json):
            b, fee_schedule, n_outcomes, oracle_config, outcome_labels

        outcome_labels order is preserved (arrays keep insertion order in
        RFC 8785). Different label orderings produce different hashes.
        """
        composite = {
            "b": market.b,
            "n_outcomes": market.n_outcomes,
            "outcome_labels": market.outcome_labels,
            "fee_schedule": {
                "trade_fee_bps": market.fee_schedule.trade_fee_bps,
                "resolution_fee_bps": market.fee_schedule.resolution_fee_bps,
            },
            "oracle_config": ORACLE_CONFIG_STUB,
        }
        canonical = canonical_json(composite)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    @staticmethod
    def verify_hash(market: MarketState) -> bool:
        """Recompute and compare against stored commitment_hash."""
        if market.commitment_hash is None:
            return False
        return MarketCommitment.compute_hash(market) == market.commitment_hash
