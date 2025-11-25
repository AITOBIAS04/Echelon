// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import {VRFConsumerBaseV2Plus} from "@chainlink/contracts/src/v0.8/vrf/dev/VRFConsumerBaseV2Plus.sol";
import {VRFV2PlusClient} from "@chainlink/contracts/src/v0.8/vrf/dev/libraries/VRFV2PlusClient.sol";

contract PredictionMarket is VRFConsumerBaseV2Plus {
    // --- VRF Configuration (Sepolia Testnet) ---
    // These are the official addresses for Chainlink VRF 2.5 on Sepolia
    uint256 s_subscriptionId;
    address vrfCoordinator = 0x5C210eF41CD1a72de73bF76eC39637bB0d3d7BEE;
    bytes32 s_keyHash = 0x9e1344a1247c8a1785d0a4681a27152bffdb43666ae5bf7d14d24a5efd44bf71;
    uint32 callbackGasLimit = 500000;
    uint16 requestConfirmations = 3;
    uint32 numWords = 1;

    // --- Market Data ---
    struct Market {
        uint256 id;
        string question;
        uint256 endTime;
        bool resolved;
        string outcome; // "YES" or "NO" (or "WAR"/"PEACE")
        uint256 totalBetsYes;
        uint256 totalBetsNo;
    }

    mapping(uint256 => Market) public markets;
    uint256 public marketCount;

    // Bets: MarketID -> User -> Amount
    mapping(uint256 => mapping(address => uint256)) public betsYes;
    mapping(uint256 => mapping(address => uint256)) public betsNo;

    // VRF Request ID -> Market ID (To track which market requested randomness)
    mapping(uint256 => uint256) public requestIdToMarketId;

    // Events
    event MarketCreated(uint256 indexed marketId, string question, uint256 endTime);
    event BetPlaced(uint256 indexed marketId, address user, string outcome, uint256 amount);
    event MarketResolved(uint256 indexed marketId, string outcome);

    constructor(uint256 subscriptionId) VRFConsumerBaseV2Plus(vrfCoordinator) {
        s_subscriptionId = subscriptionId;
    }

    // 1. Create a Market (Only the "Oracle" - your Python script - should call this in production)
    function createMarket(string memory _question, uint256 _duration) external {
        marketCount++;
        markets[marketCount] = Market({
            id: marketCount,
            question: _question,
            endTime: block.timestamp + _duration,
            resolved: false,
            outcome: "PENDING",
            totalBetsYes: 0,
            totalBetsNo: 0
        });
        emit MarketCreated(marketCount, _question, block.timestamp + _duration);
    }

    // 2. Place a Bet (Users call this)
    function placeBet(uint256 _marketId, bool _betOnYes) external payable {
        Market storage market = markets[_marketId];
        require(block.timestamp < market.endTime, "Betting is closed");
        require(!market.resolved, "Market already resolved");
        require(msg.value > 0, "Bet amount must be > 0");

        if (_betOnYes) {
            betsYes[_marketId][msg.sender] += msg.value;
            market.totalBetsYes += msg.value;
            emit BetPlaced(_marketId, msg.sender, "YES", msg.value);
        } else {
            betsNo[_marketId][msg.sender] += msg.value;
            market.totalBetsNo += msg.value;
            emit BetPlaced(_marketId, msg.sender, "NO", msg.value);
        }
    }

    // 3. Resolve Market (Calls Chainlink VRF)
    function resolveMarket(uint256 _marketId) external onlyOwner {
        Market storage market = markets[_marketId];
        require(!market.resolved, "Already resolved");
        // In a real app, you'd check (block.timestamp >= market.endTime) here

        // Request Randomness from Chainlink
        uint256 requestId = s_vrfCoordinator.requestRandomWords(
            VRFV2PlusClient.RandomWordsRequest({
                keyHash: s_keyHash,
                subId: s_subscriptionId,
                requestConfirmations: requestConfirmations,
                callbackGasLimit: callbackGasLimit,
                numWords: numWords,
                extraArgs: VRFV2PlusClient._argsToBytes(
                    VRFV2PlusClient.ExtraArgsV1({nativePayment: false})
                )
            })
        );
        
        requestIdToMarketId[requestId] = _marketId;
    }

    // 4. Chainlink Callback (The "Truth")
    function fulfillRandomWords(uint256 requestId, uint256[] calldata randomWords) internal override {
        uint256 marketId = requestIdToMarketId[requestId];
        Market storage market = markets[marketId];
        
        // Example Logic: Even number = YES, Odd number = NO
        // In your "Hybrid" model, your Python script sends the probability threshold.
        // For this MVP, we strictly use the random number parity.
        uint256 randomResult = randomWords[0];
        
        if (randomResult % 2 == 0) {
            market.outcome = "YES";
        } else {
            market.outcome = "NO";
        }
        
        market.resolved = true;
        emit MarketResolved(marketId, market.outcome);
    }
}