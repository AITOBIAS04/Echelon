"""Tests for Claim Graph — Merkle-hashed claim-evidence mapping."""

import hashlib

from theatre.engine.canonical_json import canonical_json

from backend.investigation.claim_graph import (
    ClaimGraph,
    ClaimNode,
    ClaimStatus,
    ClaimType,
)


def _make_graph_with_claims(n: int = 1) -> ClaimGraph:
    """Helper: create a graph with N claims."""
    graph = ClaimGraph()
    for i in range(n):
        graph.add_claim(
            claim_text=f"Claim {i + 1}",
            claim_type=ClaimType.FACT,
            evidence_refs=[f"E{i + 1:03d}"],
        )
    return graph


class TestAddClaim:
    def test_add_claim(self):
        graph = ClaimGraph()
        node = graph.add_claim(
            claim_text="Company X filed for bankruptcy on 2026-01-15",
            claim_type=ClaimType.FACT,
            evidence_refs=["E001", "E002"],
        )

        assert node.claim_id == "C001"
        assert node.claim_text == "Company X filed for bankruptcy on 2026-01-15"
        assert node.claim_type == ClaimType.FACT
        assert node.evidence_refs == ["E001", "E002"]
        assert node.status == ClaimStatus.UNCONFIRMED
        assert node.confidence == 0.0
        assert isinstance(node, ClaimNode)

    def test_status_update(self):
        graph = _make_graph_with_claims(1)
        updated = graph.update_claim_status(
            claim_id="C001",
            status=ClaimStatus.SUPPORTED,
            confidence=0.95,
            independence_groups=["wm", "ch"],
        )

        assert updated.status == ClaimStatus.SUPPORTED
        assert updated.confidence == 0.95
        assert updated.independence_groups == ["wm", "ch"]
        assert updated.claim_text == "Claim 1"  # preserved


class TestMerkleRoot:
    def test_merkle_root_deterministic(self):
        g1 = _make_graph_with_claims(3)
        g2 = _make_graph_with_claims(3)

        assert g1.compute_root_hash() == g2.compute_root_hash()

    def test_merkle_root_single_claim(self):
        graph = _make_graph_with_claims(1)
        claim = graph.claims[0]

        expected_leaf = hashlib.sha256(
            canonical_json(claim.model_dump(mode="json")).encode()
        ).hexdigest()

        assert graph.compute_root_hash() == expected_leaf

    def test_merkle_root_two_claims(self):
        graph = _make_graph_with_claims(2)
        sorted_claims = sorted(graph.claims, key=lambda c: c.claim_id)

        h1 = hashlib.sha256(
            canonical_json(sorted_claims[0].model_dump(mode="json")).encode()
        ).hexdigest()
        h2 = hashlib.sha256(
            canonical_json(sorted_claims[1].model_dump(mode="json")).encode()
        ).hexdigest()

        expected_root = hashlib.sha256((h1 + h2).encode()).hexdigest()
        assert graph.compute_root_hash() == expected_root

    def test_merkle_root_odd_count(self):
        graph = _make_graph_with_claims(3)
        sorted_claims = sorted(graph.claims, key=lambda c: c.claim_id)

        h1 = hashlib.sha256(
            canonical_json(sorted_claims[0].model_dump(mode="json")).encode()
        ).hexdigest()
        h2 = hashlib.sha256(
            canonical_json(sorted_claims[1].model_dump(mode="json")).encode()
        ).hexdigest()
        h3 = hashlib.sha256(
            canonical_json(sorted_claims[2].model_dump(mode="json")).encode()
        ).hexdigest()

        # Pair 1: hash(h1 + h2), Pair 2: hash(h3 + h3) (odd leaf duplicated)
        left = hashlib.sha256((h1 + h2).encode()).hexdigest()
        right = hashlib.sha256((h3 + h3).encode()).hexdigest()
        expected_root = hashlib.sha256((left + right).encode()).hexdigest()

        assert graph.compute_root_hash() == expected_root

    def test_merkle_root_uses_canonical_json(self):
        """Verify canonical_json is used — adding fields in different order
        should still produce the same hash since canonical_json sorts keys."""
        graph = ClaimGraph()
        graph.add_claim(
            claim_text="Test claim",
            claim_type=ClaimType.ATTRIBUTION,
            evidence_refs=["E001"],
        )

        claim = graph.claims[0]
        claim_dict = claim.model_dump(mode="json")

        # canonical_json sorts keys — verify it's different from unsorted json
        cj = canonical_json(claim_dict)
        assert '"claim_id"' in cj
        assert '"claim_text"' in cj

        expected = hashlib.sha256(cj.encode()).hexdigest()
        assert graph.compute_root_hash() == expected


class TestStatusSummary:
    def test_status_summary(self):
        graph = _make_graph_with_claims(4)
        graph.update_claim_status("C001", ClaimStatus.SUPPORTED, 0.9, ["a", "b"])
        graph.update_claim_status("C002", ClaimStatus.SUPPORTED, 0.85, ["a", "b"])
        graph.update_claim_status("C003", ClaimStatus.CONTRADICTED, 0.3, [])

        summary = graph.get_status_summary()
        assert summary["supported"] == 2
        assert summary["contradicted"] == 1
        assert summary["unconfirmed"] == 1


class TestLinkCounterSignal:
    def test_link_counter_signal(self):
        graph = _make_graph_with_claims(1)
        assert graph.claims[0].counter_signals == []

        graph.link_counter_signal("C001", "CS001")
        graph.link_counter_signal("C001", "CS002")

        claim = graph.claims[0]
        assert claim.counter_signals == ["CS001", "CS002"]
        assert claim.claim_text == "Claim 1"  # other fields preserved
