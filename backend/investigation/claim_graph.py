"""Claim Graph — structured claim-evidence-source mapping with Merkle root."""

from __future__ import annotations

import hashlib
from enum import Enum

from pydantic import BaseModel, Field

from theatre.engine.canonical_json import canonical_json


class ClaimType(str, Enum):
    """Type of investigative claim."""

    FACT = "fact"
    CAUSAL = "causal"
    ATTRIBUTION = "attribution"


class ClaimStatus(str, Enum):
    """Status of a claim based on corroboration."""

    SUPPORTED = "supported"
    PARTIALLY_SUPPORTED = "partially_supported"
    UNCONFIRMED = "unconfirmed"
    CONTRADICTED = "contradicted"


class CorroborationCheck(BaseModel):
    """Per-source corroboration result for a claim."""

    model_config = {"frozen": True}

    claim_id: str
    source_id: str
    upstream_group: str
    status: str  # confirmed | contradicted | unavailable
    confidence: float = Field(ge=0.0, le=1.0)


class ClaimNode(BaseModel):
    """Immutable claim node within a claim graph."""

    model_config = {"frozen": True}

    claim_id: str
    claim_text: str
    claim_type: ClaimType
    evidence_refs: list[str]
    osint_checks: list[CorroborationCheck] = Field(default_factory=list)
    counter_signals: list[str] = Field(default_factory=list)
    status: ClaimStatus = ClaimStatus.UNCONFIRMED
    confidence: float = Field(ge=0.0, le=1.0, default=0.0)
    independence_groups: list[str] = Field(default_factory=list)


class ClaimGraph:
    """Structured claim-evidence-source mapping with Merkle root.

    Merkle hashing spec (design note §3.7):
    1. Each claim → canonical JSON (keys sorted, no whitespace, UTF-8)
    2. Each leaf hash = SHA-256(canonical_json(claim))
    3. Claims ordered by claim_id (lexicographic)
    4. Merkle tree: SHA-256 pairwise hashing, odd leaf duplicated
    """

    def __init__(self) -> None:
        self._claims: list[ClaimNode] = []
        self._counter: int = 0

    def add_claim(
        self,
        claim_text: str,
        claim_type: ClaimType,
        evidence_refs: list[str],
    ) -> ClaimNode:
        """Add a new claim to the graph. Returns the frozen ClaimNode."""
        self._counter += 1
        claim_id = f"C{self._counter:03d}"

        node = ClaimNode(
            claim_id=claim_id,
            claim_text=claim_text,
            claim_type=claim_type,
            evidence_refs=evidence_refs,
        )
        self._claims.append(node)
        return node

    def update_claim_status(
        self,
        claim_id: str,
        status: ClaimStatus,
        confidence: float,
        independence_groups: list[str],
    ) -> ClaimNode:
        """Replace a claim with an updated status. Returns the new frozen node."""
        idx = self._find_claim_index(claim_id)
        old = self._claims[idx]

        updated = ClaimNode(
            claim_id=old.claim_id,
            claim_text=old.claim_text,
            claim_type=old.claim_type,
            evidence_refs=old.evidence_refs,
            osint_checks=old.osint_checks,
            counter_signals=old.counter_signals,
            status=status,
            confidence=confidence,
            independence_groups=independence_groups,
        )
        self._claims[idx] = updated
        return updated

    def link_counter_signal(self, claim_id: str, counter_signal_id: str) -> None:
        """Link a counter-signal to a claim."""
        idx = self._find_claim_index(claim_id)
        old = self._claims[idx]

        updated = ClaimNode(
            claim_id=old.claim_id,
            claim_text=old.claim_text,
            claim_type=old.claim_type,
            evidence_refs=old.evidence_refs,
            osint_checks=old.osint_checks,
            counter_signals=list(old.counter_signals) + [counter_signal_id],
            status=old.status,
            confidence=old.confidence,
            independence_groups=old.independence_groups,
        )
        self._claims[idx] = updated

    def compute_root_hash(self) -> str:
        """Compute the Merkle root hash of the claim graph.

        Per design note §3.7:
        - Each claim → canonical JSON → SHA-256 leaf
        - Claims sorted by claim_id (lexicographic)
        - Pairwise SHA-256 merge, odd leaf duplicated
        """
        if not self._claims:
            return hashlib.sha256(b"").hexdigest()

        sorted_claims = sorted(self._claims, key=lambda c: c.claim_id)

        leaves = [
            hashlib.sha256(
                canonical_json(c.model_dump(mode="json")).encode()
            ).hexdigest()
            for c in sorted_claims
        ]

        while len(leaves) > 1:
            if len(leaves) % 2 == 1:
                leaves.append(leaves[-1])
            leaves = [
                hashlib.sha256(
                    (leaves[i] + leaves[i + 1]).encode()
                ).hexdigest()
                for i in range(0, len(leaves), 2)
            ]

        return leaves[0]

    def get_status_summary(self) -> dict[str, int]:
        """Return claim count per status."""
        summary: dict[str, int] = {}
        for claim in self._claims:
            key = claim.status.value
            summary[key] = summary.get(key, 0) + 1
        return summary

    @property
    def claims(self) -> list[ClaimNode]:
        return list(self._claims)

    def _find_claim_index(self, claim_id: str) -> int:
        """Find the index of a claim by ID. Raises ValueError if not found."""
        for i, claim in enumerate(self._claims):
            if claim.claim_id == claim_id:
                return i
        raise ValueError(f"Claim {claim_id} not found")
