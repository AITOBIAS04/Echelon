// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@chainlink/contracts/src/v0.8/vrf/VRFConsumerBaseV2.sol";
import "@chainlink/contracts/src/v0.8/interfaces/VRFCoordinatorV2Interface.sol";

contract PredictionMarket is VRFConsumerBaseV2 {
    // --- VRF Configuration (Sepolia Testnet) ---
    // Using VRF V2 (compatible with Chainlink contracts 0.8.0)
    VRFCoordinatorV2Interface COORDINATOR;
    uint256 s_subscriptionId;
    address vrfCoordinator = 0x8103B0A8A00be2DDC778e6e7eaa21791Cd364625; // VRF V2 Coordinator
    bytes32 s_keyHash = 0x474e34a077df58807dbe9c96d3c009b23b3c6d0cce433e59bbf5b34f823bc56c; // VRF V2 Key Hash
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

    constructor(uint256 subscriptionId) VRFConsumerBaseV2(vrfCoordinator) {
        COORDINATOR = VRFCoordinatorV2Interface(vrfCoordinator);
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
    function resolveMarket(uint256 _marketId) external {
        Market storage market = markets[_marketId];
        require(!market.resolved, "Already resolved");
        // In a real app, you'd check (block.timestamp >= market.endTime) here

        // Request Randomness from Chainlink VRF V2
        uint256 requestId = COORDINATOR.requestRandomWords(
            s_keyHash,
            uint64(s_subscriptionId),
            requestConfirmations,
            callbackGasLimit,
            numWords
        );
        
        requestIdToMarketId[requestId] = _marketId;
    }

    // 4. Chainlink Callback (The "Truth")
    function fulfillRandomWords(uint256 requestId, uint256[] memory randomWords) internal override {
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