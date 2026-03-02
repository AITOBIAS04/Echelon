"""Base Sepolia client tests — MockSepoliaClient publish/verify round-trip."""
from __future__ import annotations

import pytest

from backend.chain.sepolia import (
    BaseSepoliaClient,
    CommitmentRecord,
    MockSepoliaClient,
    SettlementRecord,
    TxReceipt,
)


class TestMockPublishCommitment:
    """MockSepoliaClient.publish_commitment round-trip."""

    def test_returns_tx_receipt(self) -> None:
        client = MockSepoliaClient()
        receipt = client.publish_commitment("t1", "hash_abc")
        assert isinstance(receipt, TxReceipt)
        assert receipt.status is True
        assert receipt.gas_used == 50000
        assert "t1" in receipt.tx_hash

    def test_verify_commitment_round_trip(self) -> None:
        client = MockSepoliaClient()
        client.publish_commitment("t1", "hash_abc")
        record = client.verify_commitment("t1")
        assert record is not None
        assert isinstance(record, CommitmentRecord)
        assert record.theatre_id == "t1"
        assert record.commitment_hash == "hash_abc"

    def test_verify_commitment_missing(self) -> None:
        client = MockSepoliaClient()
        assert client.verify_commitment("nonexistent") is None

    def test_overwrite_commitment(self) -> None:
        client = MockSepoliaClient()
        client.publish_commitment("t1", "hash_v1")
        client.publish_commitment("t1", "hash_v2")
        record = client.verify_commitment("t1")
        assert record is not None
        assert record.commitment_hash == "hash_v2"


class TestMockPublishSettlement:
    """MockSepoliaClient.publish_settlement round-trip."""

    def test_returns_tx_receipt(self) -> None:
        client = MockSepoliaClient()
        receipt = client.publish_settlement("t1", "settle_hash", 1)
        assert isinstance(receipt, TxReceipt)
        assert receipt.status is True
        assert receipt.gas_used == 60000
        assert "t1" in receipt.tx_hash

    def test_verify_settlement_round_trip(self) -> None:
        client = MockSepoliaClient()
        client.publish_settlement("t1", "settle_hash", 2)
        record = client.verify_settlement("t1")
        assert record is not None
        assert isinstance(record, SettlementRecord)
        assert record.theatre_id == "t1"
        assert record.settlement_hash == "settle_hash"
        assert record.winning_outcome == 2

    def test_verify_settlement_missing(self) -> None:
        client = MockSepoliaClient()
        assert client.verify_settlement("nonexistent") is None


class TestMockBlockCounter:
    """Block counter increments across operations."""

    def test_block_increments(self) -> None:
        client = MockSepoliaClient()
        r1 = client.publish_commitment("t1", "h1")
        r2 = client.publish_settlement("t1", "h2", 0)
        assert r2.block_number > r1.block_number

    def test_multiple_theatres_independent(self) -> None:
        client = MockSepoliaClient()
        client.publish_commitment("t1", "h1")
        client.publish_commitment("t2", "h2")
        rec1 = client.verify_commitment("t1")
        rec2 = client.verify_commitment("t2")
        assert rec1 is not None
        assert rec2 is not None
        assert rec1.commitment_hash == "h1"
        assert rec2.commitment_hash == "h2"


class TestBaseSepoliaClient:
    """BaseSepoliaClient methods raise NotImplementedError (no web3)."""

    def test_publish_commitment_raises(self) -> None:
        # web3 not installed — constructor itself raises ImportError
        with pytest.raises(ImportError):
            BaseSepoliaClient("http://rpc", "0xaddr", "0xkey")

    def test_all_exports_present(self) -> None:
        import backend.chain as chain

        assert hasattr(chain, "TxReceipt")
        assert hasattr(chain, "CommitmentRecord")
        assert hasattr(chain, "SettlementRecord")
        assert hasattr(chain, "MockSepoliaClient")
        assert hasattr(chain, "BaseSepoliaClient")
