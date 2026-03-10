"""Base Sepolia client — on-chain commitment and settlement publishing.

MockSepoliaClient for unit tests (no chain dependency).
BaseSepoliaClient uses web3.py (lazy import, testnet only).
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class TxReceipt:
    """Transaction receipt from chain interaction."""

    tx_hash: str
    block_number: int
    gas_used: int
    status: bool  # True = success


@dataclass
class CommitmentRecord:
    """On-chain commitment record."""

    theatre_id: str
    commitment_hash: str
    block_number: int
    timestamp: int


@dataclass
class SettlementRecord:
    """On-chain settlement record."""

    theatre_id: str
    settlement_hash: str
    winning_outcome: int
    block_number: int
    timestamp: int


class MockSepoliaClient:
    """In-memory mock for unit tests. No chain interaction."""

    def __init__(self) -> None:
        self._commitments: dict[str, str] = {}
        self._settlements: dict[str, tuple[str, int]] = {}
        self._block_counter: int = 1000

    def publish_commitment(
        self, theatre_id: str, commitment_hash: str
    ) -> TxReceipt:
        """Store commitment in memory. Returns mock receipt."""
        self._commitments[theatre_id] = commitment_hash
        self._block_counter += 1
        return TxReceipt(
            tx_hash=f"0xmock_commit_{theatre_id}",
            block_number=self._block_counter,
            gas_used=50000,
            status=True,
        )

    def publish_settlement(
        self, theatre_id: str, settlement_hash: str, winning_outcome: int
    ) -> TxReceipt:
        """Store settlement in memory. Returns mock receipt."""
        self._settlements[theatre_id] = (settlement_hash, winning_outcome)
        self._block_counter += 1
        return TxReceipt(
            tx_hash=f"0xmock_settle_{theatre_id}",
            block_number=self._block_counter,
            gas_used=60000,
            status=True,
        )

    def verify_commitment(self, theatre_id: str) -> CommitmentRecord | None:
        """Read commitment from memory. Returns None if not found."""
        if theatre_id not in self._commitments:
            return None
        return CommitmentRecord(
            theatre_id=theatre_id,
            commitment_hash=self._commitments[theatre_id],
            block_number=self._block_counter,
            timestamp=int(datetime.utcnow().timestamp()),
        )

    def verify_settlement(self, theatre_id: str) -> SettlementRecord | None:
        """Read settlement from memory. Returns None if not found."""
        if theatre_id not in self._settlements:
            return None
        settlement_hash, winning_outcome = self._settlements[theatre_id]
        return SettlementRecord(
            theatre_id=theatre_id,
            settlement_hash=settlement_hash,
            winning_outcome=winning_outcome,
            block_number=self._block_counter,
            timestamp=int(datetime.utcnow().timestamp()),
        )


class BaseSepoliaClient:
    """Real Base Sepolia client using web3.py. Lazy import.

    Requires: pip install web3
    Requires: RPC URL, contract address, private key at runtime.
    """

    def __init__(
        self, rpc_url: str, contract_address: str, private_key: str
    ) -> None:
        try:
            from web3 import Web3  # noqa: F401
        except ImportError as e:
            raise ImportError(
                "web3 package required for BaseSepoliaClient. "
                "Install with: pip install web3"
            ) from e

        self._rpc_url = rpc_url
        self._contract_address = contract_address
        self._private_key = private_key

    def publish_commitment(
        self, theatre_id: str, commitment_hash: str
    ) -> TxReceipt:
        """Publish commitment to Base Sepolia. Requires web3."""
        raise NotImplementedError(
            "Live chain publishing requires contract ABI wiring"
        )

    def publish_settlement(
        self, theatre_id: str, settlement_hash: str, winning_outcome: int
    ) -> TxReceipt:
        """Publish settlement to Base Sepolia. Requires web3."""
        raise NotImplementedError(
            "Live chain publishing requires contract ABI wiring"
        )

    def verify_commitment(self, theatre_id: str) -> CommitmentRecord | None:
        """Read commitment from Base Sepolia. Requires web3."""
        raise NotImplementedError(
            "Live chain reading requires contract ABI wiring"
        )

    def verify_settlement(self, theatre_id: str) -> SettlementRecord | None:
        """Read settlement from Base Sepolia. Requires web3."""
        raise NotImplementedError(
            "Live chain reading requires contract ABI wiring"
        )
