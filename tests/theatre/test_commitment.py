"""Tests for Commitment Protocol — hash determinism, verification, receipts."""

import pytest

from theatre.engine.commitment import CommitmentProtocol, CommitmentReceipt


SAMPLE_TEMPLATE = {
    "schema_version": "2.0.1",
    "theatre_id": "product_observer_v1",
    "template_family": "PRODUCT",
    "execution_path": "replay",
    "display_name": "Observer Verification",
    "criteria": {
        "criteria_ids": ["source_fidelity", "signal_classification"],
        "criteria_human": "Test rubric",
        "weights": {"source_fidelity": 0.6, "signal_classification": 0.4},
    },
}

SAMPLE_VERSION_PINS = {
    "constructs": {"observer": "abc123def456"},
    "scorer_version": "anthropic-claude-3.5-sonnet",
}

SAMPLE_DATASET_HASHES = {
    "provenance": "a" * 64,
}


class TestComputeHash:
    def test_produces_64_char_hex(self):
        h = CommitmentProtocol.compute_hash(
            SAMPLE_TEMPLATE, SAMPLE_VERSION_PINS, SAMPLE_DATASET_HASHES
        )
        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)

    def test_deterministic(self):
        h1 = CommitmentProtocol.compute_hash(
            SAMPLE_TEMPLATE, SAMPLE_VERSION_PINS, SAMPLE_DATASET_HASHES
        )
        h2 = CommitmentProtocol.compute_hash(
            SAMPLE_TEMPLATE, SAMPLE_VERSION_PINS, SAMPLE_DATASET_HASHES
        )
        assert h1 == h2

    def test_different_template_different_hash(self):
        modified = {**SAMPLE_TEMPLATE, "display_name": "Different Name"}
        h1 = CommitmentProtocol.compute_hash(
            SAMPLE_TEMPLATE, SAMPLE_VERSION_PINS, SAMPLE_DATASET_HASHES
        )
        h2 = CommitmentProtocol.compute_hash(
            modified, SAMPLE_VERSION_PINS, SAMPLE_DATASET_HASHES
        )
        assert h1 != h2

    def test_different_version_pins_different_hash(self):
        modified = {
            **SAMPLE_VERSION_PINS,
            "constructs": {"observer": "different_hash"},
        }
        h1 = CommitmentProtocol.compute_hash(
            SAMPLE_TEMPLATE, SAMPLE_VERSION_PINS, SAMPLE_DATASET_HASHES
        )
        h2 = CommitmentProtocol.compute_hash(
            SAMPLE_TEMPLATE, modified, SAMPLE_DATASET_HASHES
        )
        assert h1 != h2

    def test_different_dataset_hashes_different_hash(self):
        modified = {"provenance": "b" * 64}
        h1 = CommitmentProtocol.compute_hash(
            SAMPLE_TEMPLATE, SAMPLE_VERSION_PINS, SAMPLE_DATASET_HASHES
        )
        h2 = CommitmentProtocol.compute_hash(
            SAMPLE_TEMPLATE, SAMPLE_VERSION_PINS, modified
        )
        assert h1 != h2

    def test_key_order_irrelevant(self):
        """canonical_json sorts keys — insertion order shouldn't matter."""
        template_a = {"b": 2, "a": 1}
        template_b = {"a": 1, "b": 2}
        h1 = CommitmentProtocol.compute_hash(
            template_a, SAMPLE_VERSION_PINS, SAMPLE_DATASET_HASHES
        )
        h2 = CommitmentProtocol.compute_hash(
            template_b, SAMPLE_VERSION_PINS, SAMPLE_DATASET_HASHES
        )
        assert h1 == h2


class TestVerifyHash:
    def test_valid_hash_verifies(self):
        h = CommitmentProtocol.compute_hash(
            SAMPLE_TEMPLATE, SAMPLE_VERSION_PINS, SAMPLE_DATASET_HASHES
        )
        assert CommitmentProtocol.verify_hash(
            h, SAMPLE_TEMPLATE, SAMPLE_VERSION_PINS, SAMPLE_DATASET_HASHES
        ) is True

    def test_tampered_template_fails(self):
        h = CommitmentProtocol.compute_hash(
            SAMPLE_TEMPLATE, SAMPLE_VERSION_PINS, SAMPLE_DATASET_HASHES
        )
        modified = {**SAMPLE_TEMPLATE, "display_name": "Tampered"}
        assert CommitmentProtocol.verify_hash(
            h, modified, SAMPLE_VERSION_PINS, SAMPLE_DATASET_HASHES
        ) is False

    def test_wrong_hash_fails(self):
        assert CommitmentProtocol.verify_hash(
            "0" * 64, SAMPLE_TEMPLATE, SAMPLE_VERSION_PINS, SAMPLE_DATASET_HASHES
        ) is False


class TestCommitmentReceipt:
    def test_create_receipt(self):
        receipt = CommitmentProtocol.create_receipt(
            "theatre-1", SAMPLE_TEMPLATE, SAMPLE_VERSION_PINS, SAMPLE_DATASET_HASHES
        )
        assert isinstance(receipt, CommitmentReceipt)
        assert receipt.theatre_id == "theatre-1"
        assert len(receipt.commitment_hash) == 64
        assert receipt.template_snapshot == SAMPLE_TEMPLATE
        assert receipt.version_pins == SAMPLE_VERSION_PINS
        assert receipt.dataset_hashes == SAMPLE_DATASET_HASHES
        assert receipt.committed_at is not None

    def test_receipt_hash_matches_compute(self):
        receipt = CommitmentProtocol.create_receipt(
            "theatre-1", SAMPLE_TEMPLATE, SAMPLE_VERSION_PINS, SAMPLE_DATASET_HASHES
        )
        expected = CommitmentProtocol.compute_hash(
            SAMPLE_TEMPLATE, SAMPLE_VERSION_PINS, SAMPLE_DATASET_HASHES
        )
        assert receipt.commitment_hash == expected

    def test_receipt_serialisation(self):
        receipt = CommitmentProtocol.create_receipt(
            "theatre-1", SAMPLE_TEMPLATE, SAMPLE_VERSION_PINS, SAMPLE_DATASET_HASHES
        )
        data = receipt.model_dump()
        assert "theatre_id" in data
        assert "commitment_hash" in data
        assert "committed_at" in data
