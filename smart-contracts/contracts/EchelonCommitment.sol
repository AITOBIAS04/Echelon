// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title EchelonCommitment
 * @notice Stores theatre commitment and settlement hashes on-chain.
 * @dev Testnet only (Base Sepolia). No access control.
 *      Contract address pinned per deployment.
 */
contract EchelonCommitment {
    mapping(string => string) public commitments;
    mapping(string => string) public settlements;
    mapping(string => uint8) public winningOutcomes;

    event CommitmentPublished(string theatreId, string commitmentHash);
    event SettlementPublished(
        string theatreId,
        string settlementHash,
        uint8 winningOutcome
    );

    /**
     * @notice Publish a commitment hash for a theatre.
     * @param theatreId Theatre identifier string
     * @param hash Commitment hash (engine config + market params)
     */
    function publishCommitment(
        string calldata theatreId,
        string calldata hash
    ) external {
        commitments[theatreId] = hash;
        emit CommitmentPublished(theatreId, hash);
    }

    /**
     * @notice Publish settlement for a theatre.
     * @param theatreId Theatre identifier string
     * @param hash Settlement hash (outcome + resolution proof)
     * @param outcome Winning outcome index
     */
    function publishSettlement(
        string calldata theatreId,
        string calldata hash,
        uint8 outcome
    ) external {
        settlements[theatreId] = hash;
        winningOutcomes[theatreId] = outcome;
        emit SettlementPublished(theatreId, hash, outcome);
    }
}
