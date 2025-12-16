// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC1155/ERC1155.sol";
import "@openzeppelin/contracts/token/ERC1155/extensions/ERC1155Burnable.sol";
import "@openzeppelin/contracts/token/ERC1155/extensions/ERC1155Supply.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import "@openzeppelin/contracts/utils/Pausable.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";

/**
 * @title TimelineShard
 * @author Echelon Protocol
 * @notice ERC-1155 tokens representing positions in counterfactual timeline markets
 * @dev Each token ID represents a unique (timelineId, outcome) pair
 * 
 * Timeline Shards are subject to:
 * - Reality Reaper: OSINT-triggered instant destruction when real-world data contradicts
 * - Quantum Decay: VRF-based daily percentage burn
 * - Agent Shield: Shark-backed shards gain temporary immunity
 * 
 * Uses bonding curve pricing: price = basePrice * (1 + supply/scaleFactor)^2
 */
contract TimelineShard is 
    ERC1155, 
    ERC1155Burnable, 
    ERC1155Supply, 
    AccessControl, 
    ReentrancyGuard,
    Pausable 
{
    using SafeERC20 for IERC20;

    // =============================================================================
    // ROLES
    // =============================================================================
    
    bytes32 public constant TIMELINE_MANAGER_ROLE = keccak256("TIMELINE_MANAGER_ROLE");
    bytes32 public constant REAPER_ROLE = keccak256("REAPER_ROLE");
    bytes32 public constant DECAY_ROLE = keccak256("DECAY_ROLE");
    bytes32 public constant AGENT_ROLE = keccak256("AGENT_ROLE");

    // =============================================================================
    // STATE VARIABLES
    // =============================================================================
    
    /// @notice The settlement token (USDC on Polygon, SPL wrapper on Solana)
    IERC20 public immutable settlementToken;
    
    /// @notice Decimal precision for settlement token
    uint8 public immutable settlementDecimals;
    
    /// @notice Protocol fee in basis points (100 = 1%)
    uint256 public protocolFeeBps = 100;
    
    /// @notice Treasury address for protocol fees
    address public treasury;
    
    /// @notice Counter for timeline IDs
    uint256 public nextTimelineId = 1;
    
    /// @notice Counter for market IDs within timelines
    uint256 public nextMarketId = 1;

    // =============================================================================
    // STRUCTS
    // =============================================================================
    
    /// @notice Represents a forked timeline
    struct Timeline {
        uint256 id;
        uint256 forkPointTimestamp;     // When the fork occurred
        bytes32 forkPointStateHash;      // Hash of market state at fork
        uint256 parentTimelineId;        // 0 for canonical reality
        string description;              // "What if Fed cut rates?"
        uint256 expiryTimestamp;         // When timeline resolves
        TimelineStatus status;
        uint256 vrfSeed;                 // Chainlink VRF seed for this timeline
    }
    
    /// @notice Represents a market within a timeline
    struct Market {
        uint256 id;
        uint256 timelineId;
        string question;                 // "Will oil drop below $75?"
        uint256[] outcomeTokenIds;       // Token IDs for each outcome
        string[] outcomeLabels;          // ["Yes", "No"] or ["China", "Cuba", "Intercepted"]
        uint256 resolutionTimestamp;
        MarketStatus status;
        uint256 winningOutcomeIndex;     // Set on resolution
        uint256 totalVolume;
    }
    
    /// @notice Bonding curve parameters for a token
    struct BondingCurve {
        uint256 basePrice;               // Starting price in settlement tokens (6 decimals for USDC)
        uint256 scaleFactor;             // Controls price sensitivity to supply
        uint256 maxSupply;               // Cap on total supply
    }
    
    /// @notice Agent shield protection
    struct ShieldStatus {
        bool isShielded;
        address shieldingAgent;
        uint256 shieldExpiry;
        uint256 penaltyMultiplier;       // 2x decay if agent was wrong
    }

    enum TimelineStatus { Active, Resolved, Reaped }
    enum MarketStatus { Open, Closed, Resolved, Voided }

    // =============================================================================
    // MAPPINGS
    // =============================================================================
    
    /// @notice Timeline data by ID
    mapping(uint256 => Timeline) public timelines;
    
    /// @notice Market data by ID
    mapping(uint256 => Market) public markets;
    
    /// @notice Bonding curve config per token ID
    mapping(uint256 => BondingCurve) public bondingCurves;
    
    /// @notice Shield status per token ID
    mapping(uint256 => ShieldStatus) public shields;
    
    /// @notice Token ID to market ID mapping
    mapping(uint256 => uint256) public tokenToMarket;
    
    /// @notice Token ID to outcome index mapping
    mapping(uint256 => uint256) public tokenToOutcomeIndex;
    
    /// @notice Accumulated protocol fees
    uint256 public accumulatedFees;
    
    /// @notice Last decay timestamp per token
    mapping(uint256 => uint256) public lastDecayTimestamp;
    
    /// @notice Decay rate in basis points per day (200 = 2%)
    uint256 public decayRateBps = 200;

    // =============================================================================
    // EVENTS
    // =============================================================================
    
    event TimelineCreated(
        uint256 indexed timelineId,
        uint256 indexed parentTimelineId,
        bytes32 forkPointStateHash,
        string description,
        uint256 expiryTimestamp
    );
    
    event MarketCreated(
        uint256 indexed marketId,
        uint256 indexed timelineId,
        string question,
        string[] outcomeLabels,
        uint256[] tokenIds
    );
    
    event ShardsMinted(
        uint256 indexed tokenId,
        address indexed buyer,
        uint256 amount,
        uint256 totalCost,
        uint256 newPrice
    );
    
    event ShardsBurned(
        uint256 indexed tokenId,
        address indexed seller,
        uint256 amount,
        uint256 payout,
        uint256 newPrice
    );
    
    event RealityReaped(
        uint256 indexed timelineId,
        string reason,
        uint256 shardsDestroyed
    );
    
    event QuantumDecay(
        uint256 indexed tokenId,
        uint256 burnedAmount,
        uint256 remainingSupply,
        bytes32 vrfRequestId
    );
    
    event AgentShieldApplied(
        uint256 indexed tokenId,
        address indexed agent,
        uint256 expiry
    );
    
    event AgentShieldBroken(
        uint256 indexed tokenId,
        address indexed agent,
        bool wasCorrect
    );
    
    event MarketResolved(
        uint256 indexed marketId,
        uint256 winningOutcomeIndex,
        string winningOutcomeLabel
    );

    // =============================================================================
    // CONSTRUCTOR
    // =============================================================================
    
    constructor(
        address _settlementToken,
        uint8 _settlementDecimals,
        address _treasury,
        string memory _uri
    ) ERC1155(_uri) {
        require(_settlementToken != address(0), "Invalid settlement token");
        require(_treasury != address(0), "Invalid treasury");
        
        settlementToken = IERC20(_settlementToken);
        settlementDecimals = _settlementDecimals;
        treasury = _treasury;
        
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(TIMELINE_MANAGER_ROLE, msg.sender);
        _grantRole(REAPER_ROLE, msg.sender);
        _grantRole(DECAY_ROLE, msg.sender);
    }

    // =============================================================================
    // TIMELINE MANAGEMENT
    // =============================================================================
    
    /**
     * @notice Create a new forked timeline
     * @param parentTimelineId ID of parent (0 for canonical reality)
     * @param forkPointStateHash Hash of market state at fork point
     * @param description Human-readable description
     * @param expiryTimestamp When this timeline resolves
     * @param vrfSeed Chainlink VRF seed for randomness
     */
    function createTimeline(
        uint256 parentTimelineId,
        bytes32 forkPointStateHash,
        string calldata description,
        uint256 expiryTimestamp,
        uint256 vrfSeed
    ) external onlyRole(TIMELINE_MANAGER_ROLE) returns (uint256 timelineId) {
        require(expiryTimestamp > block.timestamp, "Expiry must be future");
        require(
            parentTimelineId == 0 || timelines[parentTimelineId].status == TimelineStatus.Active,
            "Parent timeline not active"
        );
        
        timelineId = nextTimelineId++;
        
        timelines[timelineId] = Timeline({
            id: timelineId,
            forkPointTimestamp: block.timestamp,
            forkPointStateHash: forkPointStateHash,
            parentTimelineId: parentTimelineId,
            description: description,
            expiryTimestamp: expiryTimestamp,
            status: TimelineStatus.Active,
            vrfSeed: vrfSeed
        });
        
        emit TimelineCreated(
            timelineId,
            parentTimelineId,
            forkPointStateHash,
            description,
            expiryTimestamp
        );
    }
    
    /**
     * @notice Create a market within a timeline
     * @param timelineId Timeline to create market in
     * @param question Market question
     * @param outcomeLabels Labels for each outcome
     * @param basePrice Starting price for bonding curve
     * @param scaleFactor Price sensitivity factor
     * @param maxSupply Maximum supply per outcome
     */
    function createMarket(
        uint256 timelineId,
        string calldata question,
        string[] calldata outcomeLabels,
        uint256 basePrice,
        uint256 scaleFactor,
        uint256 maxSupply
    ) external onlyRole(TIMELINE_MANAGER_ROLE) returns (uint256 marketId) {
        require(timelines[timelineId].status == TimelineStatus.Active, "Timeline not active");
        require(outcomeLabels.length >= 2, "Need at least 2 outcomes");
        require(basePrice > 0, "Base price must be positive");
        require(scaleFactor > 0, "Scale factor must be positive");
        
        marketId = nextMarketId++;
        
        uint256[] memory tokenIds = new uint256[](outcomeLabels.length);
        
        for (uint256 i = 0; i < outcomeLabels.length; i++) {
            // Token ID encodes: timelineId (high 128 bits) | marketId (mid 64 bits) | outcomeIndex (low 64 bits)
            uint256 tokenId = _encodeTokenId(timelineId, marketId, i);
            tokenIds[i] = tokenId;
            
            bondingCurves[tokenId] = BondingCurve({
                basePrice: basePrice,
                scaleFactor: scaleFactor,
                maxSupply: maxSupply
            });
            
            tokenToMarket[tokenId] = marketId;
            tokenToOutcomeIndex[tokenId] = i;
            lastDecayTimestamp[tokenId] = block.timestamp;
        }
        
        // Copy outcomeLabels to storage
        string[] memory labels = new string[](outcomeLabels.length);
        for (uint256 i = 0; i < outcomeLabels.length; i++) {
            labels[i] = outcomeLabels[i];
        }
        
        markets[marketId] = Market({
            id: marketId,
            timelineId: timelineId,
            question: question,
            outcomeTokenIds: tokenIds,
            outcomeLabels: labels,
            resolutionTimestamp: timelines[timelineId].expiryTimestamp,
            status: MarketStatus.Open,
            winningOutcomeIndex: 0,
            totalVolume: 0
        });
        
        emit MarketCreated(marketId, timelineId, question, labels, tokenIds);
    }

    // =============================================================================
    // BONDING CURVE TRADING
    // =============================================================================
    
    /**
     * @notice Calculate price to buy `amount` shards using bonding curve
     * @dev price = integral of basePrice * (1 + supply/scaleFactor)^2 from currentSupply to currentSupply + amount
     */
    function getBuyPrice(uint256 tokenId, uint256 amount) public view returns (uint256) {
        BondingCurve memory curve = bondingCurves[tokenId];
        require(curve.basePrice > 0, "Token not configured");
        
        uint256 currentSupply = totalSupply(tokenId);
        require(currentSupply + amount <= curve.maxSupply, "Exceeds max supply");
        
        // Simplified bonding curve: price = basePrice * (1 + totalSupply / scaleFactor)
        // Cost = basePrice * amount + basePrice * (2*currentSupply + amount) * amount / (2 * scaleFactor)
        uint256 linearCost = curve.basePrice * amount;
        uint256 quadraticCost = (curve.basePrice * (2 * currentSupply + amount) * amount) / (2 * curve.scaleFactor);
        
        return linearCost + quadraticCost;
    }
    
    /**
     * @notice Calculate payout for selling `amount` shards
     */
    function getSellPrice(uint256 tokenId, uint256 amount) public view returns (uint256) {
        BondingCurve memory curve = bondingCurves[tokenId];
        require(curve.basePrice > 0, "Token not configured");
        
        uint256 currentSupply = totalSupply(tokenId);
        require(amount <= currentSupply, "Not enough supply");
        
        // Reverse of buy price
        uint256 linearPayout = curve.basePrice * amount;
        uint256 quadraticPayout = (curve.basePrice * (2 * currentSupply - amount) * amount) / (2 * curve.scaleFactor);
        
        return linearPayout + quadraticPayout;
    }
    
    /**
     * @notice Get current spot price for a token
     */
    function getSpotPrice(uint256 tokenId) public view returns (uint256) {
        BondingCurve memory curve = bondingCurves[tokenId];
        if (curve.basePrice == 0) return 0;
        
        uint256 currentSupply = totalSupply(tokenId);
        
        // Spot price = derivative of cost curve = basePrice * (1 + supply/scaleFactor)
        return curve.basePrice + (curve.basePrice * currentSupply) / curve.scaleFactor;
    }
    
    /**
     * @notice Buy shards using bonding curve
     * @param tokenId Token to buy
     * @param amount Amount to buy
     * @param maxCost Maximum cost willing to pay (slippage protection)
     */
    function buyShards(
        uint256 tokenId,
        uint256 amount,
        uint256 maxCost
    ) external nonReentrant whenNotPaused {
        require(amount > 0, "Amount must be positive");
        
        uint256 marketId = tokenToMarket[tokenId];
        require(markets[marketId].status == MarketStatus.Open, "Market not open");
        
        uint256 timelineId = markets[marketId].timelineId;
        require(timelines[timelineId].status == TimelineStatus.Active, "Timeline not active");
        
        uint256 cost = getBuyPrice(tokenId, amount);
        require(cost <= maxCost, "Exceeds max cost");
        
        // Calculate and deduct protocol fee
        uint256 fee = (cost * protocolFeeBps) / 10000;
        uint256 totalCost = cost + fee;
        
        // Transfer payment
        settlementToken.safeTransferFrom(msg.sender, address(this), totalCost);
        accumulatedFees += fee;
        
        // Mint shards
        _mint(msg.sender, tokenId, amount, "");
        
        // Update market volume
        markets[marketId].totalVolume += cost;
        
        emit ShardsMinted(tokenId, msg.sender, amount, totalCost, getSpotPrice(tokenId));
    }
    
    /**
     * @notice Sell shards back to bonding curve
     * @param tokenId Token to sell
     * @param amount Amount to sell
     * @param minPayout Minimum payout expected (slippage protection)
     */
    function sellShards(
        uint256 tokenId,
        uint256 amount,
        uint256 minPayout
    ) external nonReentrant whenNotPaused {
        require(amount > 0, "Amount must be positive");
        require(balanceOf(msg.sender, tokenId) >= amount, "Insufficient balance");
        
        uint256 marketId = tokenToMarket[tokenId];
        require(
            markets[marketId].status == MarketStatus.Open || 
            markets[marketId].status == MarketStatus.Closed,
            "Market not tradeable"
        );
        
        uint256 payout = getSellPrice(tokenId, amount);
        
        // Deduct protocol fee from payout
        uint256 fee = (payout * protocolFeeBps) / 10000;
        uint256 netPayout = payout - fee;
        
        require(netPayout >= minPayout, "Below min payout");
        
        // Burn shards
        _burn(msg.sender, tokenId, amount);
        
        // Transfer payout
        accumulatedFees += fee;
        settlementToken.safeTransfer(msg.sender, netPayout);
        
        emit ShardsBurned(tokenId, msg.sender, amount, netPayout, getSpotPrice(tokenId));
    }

    // =============================================================================
    // DEFLATIONARY MECHANICS
    // =============================================================================
    
    /**
     * @notice Reality Reaper - Instantly destroy timeline when OSINT contradicts it
     * @dev Called by authorised OSINT oracle when real-world data makes timeline impossible
     * @param timelineId Timeline to reap
     * @param reason Human-readable reason for reaping
     */
    function realityReaper(
        uint256 timelineId,
        string calldata reason
    ) external onlyRole(REAPER_ROLE) {
        Timeline storage timeline = timelines[timelineId];
        require(timeline.status == TimelineStatus.Active, "Timeline not active");
        
        timeline.status = TimelineStatus.Reaped;
        
        // Note: We don't burn tokens here - holders can still sell back to curve
        // but market is now closed and will void on resolution
        // This allows orderly exit rather than instant total loss
        
        emit RealityReaped(timelineId, reason, 0); // Actual burn count would require iteration
    }
    
    /**
     * @notice Quantum Decay - VRF-based daily burn of shards
     * @dev Called by Chainlink Automation with VRF result
     * @param tokenId Token to apply decay to
     * @param vrfResult VRF random number for determining burn
     */
    function quantumDecay(
        uint256 tokenId,
        uint256 vrfResult
    ) external onlyRole(DECAY_ROLE) {
        require(totalSupply(tokenId) > 0, "No supply to decay");
        
        uint256 timeSinceLastDecay = block.timestamp - lastDecayTimestamp[tokenId];
        require(timeSinceLastDecay >= 1 days, "Decay already applied today");
        
        ShieldStatus memory shield = shields[tokenId];
        
        // Check if shielded
        if (shield.isShielded && shield.shieldExpiry > block.timestamp) {
            // Shielded tokens skip decay
            lastDecayTimestamp[tokenId] = block.timestamp;
            return;
        }
        
        // Calculate decay amount
        uint256 currentSupply = totalSupply(tokenId);
        uint256 effectiveDecayRate = decayRateBps;
        
        // Apply penalty multiplier if shield was broken incorrectly
        if (shield.penaltyMultiplier > 1) {
            effectiveDecayRate = effectiveDecayRate * shield.penaltyMultiplier;
            // Reset penalty after applying
            shields[tokenId].penaltyMultiplier = 1;
        }
        
        // Use VRF to add randomness to decay (±50% of base rate)
        uint256 randomFactor = (vrfResult % 100) + 50; // 50-149
        uint256 actualDecayRate = (effectiveDecayRate * randomFactor) / 100;
        
        uint256 burnAmount = (currentSupply * actualDecayRate) / 10000;
        
        if (burnAmount > 0) {
            // Burn from all holders proportionally would be gas-expensive
            // Instead, we reduce the "virtual supply" tracked separately
            // For simplicity here, we just emit the event
            // In production, implement virtual supply or pro-rata burn
            
            lastDecayTimestamp[tokenId] = block.timestamp;
            
            emit QuantumDecay(tokenId, burnAmount, currentSupply - burnAmount, bytes32(vrfResult));
        }
    }
    
    /**
     * @notice Apply agent shield to protect shards from decay
     * @param tokenId Token to shield
     * @param duration Shield duration in seconds
     */
    function applyAgentShield(
        uint256 tokenId,
        uint256 duration
    ) external onlyRole(AGENT_ROLE) {
        require(totalSupply(tokenId) > 0, "Token has no supply");
        require(duration <= 7 days, "Shield duration too long");
        
        shields[tokenId] = ShieldStatus({
            isShielded: true,
            shieldingAgent: msg.sender,
            shieldExpiry: block.timestamp + duration,
            penaltyMultiplier: 1
        });
        
        emit AgentShieldApplied(tokenId, msg.sender, block.timestamp + duration);
    }
    
    /**
     * @notice Break shield and apply penalty if agent was wrong
     * @param tokenId Token with shield to break
     * @param wasCorrect Whether the shielding agent's prediction was correct
     */
    function breakAgentShield(
        uint256 tokenId,
        bool wasCorrect
    ) external onlyRole(TIMELINE_MANAGER_ROLE) {
        ShieldStatus storage shield = shields[tokenId];
        require(shield.isShielded, "Token not shielded");
        
        address agent = shield.shieldingAgent;
        
        shield.isShielded = false;
        
        if (!wasCorrect) {
            // Apply 2x decay penalty
            shield.penaltyMultiplier = 2;
        }
        
        emit AgentShieldBroken(tokenId, agent, wasCorrect);
    }

    // =============================================================================
    // RESOLUTION
    // =============================================================================
    
    /**
     * @notice Resolve a market with winning outcome
     * @param marketId Market to resolve
     * @param winningOutcomeIndex Index of winning outcome
     */
    function resolveMarket(
        uint256 marketId,
        uint256 winningOutcomeIndex
    ) external onlyRole(TIMELINE_MANAGER_ROLE) {
        Market storage market = markets[marketId];
        require(market.status == MarketStatus.Open || market.status == MarketStatus.Closed, "Market not resolvable");
        require(winningOutcomeIndex < market.outcomeTokenIds.length, "Invalid outcome");
        require(block.timestamp >= market.resolutionTimestamp, "Too early to resolve");
        
        market.status = MarketStatus.Resolved;
        market.winningOutcomeIndex = winningOutcomeIndex;
        
        emit MarketResolved(marketId, winningOutcomeIndex, market.outcomeLabels[winningOutcomeIndex]);
    }
    
    /**
     * @notice Redeem winning shards for settlement tokens
     * @param tokenId Winning token ID
     * @param amount Amount to redeem
     */
    function redeemWinningShards(
        uint256 tokenId,
        uint256 amount
    ) external nonReentrant {
        require(balanceOf(msg.sender, tokenId) >= amount, "Insufficient balance");
        
        uint256 marketId = tokenToMarket[tokenId];
        Market memory market = markets[marketId];
        
        require(market.status == MarketStatus.Resolved, "Market not resolved");
        require(
            market.outcomeTokenIds[market.winningOutcomeIndex] == tokenId,
            "Not the winning outcome"
        );
        
        // Burn the winning shards
        _burn(msg.sender, tokenId, amount);
        
        // Pay out 1:1 (each shard worth 1 unit of settlement token at resolution)
        uint256 payout = amount * (10 ** settlementDecimals);
        settlementToken.safeTransfer(msg.sender, payout);
    }

    // =============================================================================
    // ADMIN FUNCTIONS
    // =============================================================================
    
    function setProtocolFee(uint256 _feeBps) external onlyRole(DEFAULT_ADMIN_ROLE) {
        require(_feeBps <= 500, "Fee too high"); // Max 5%
        protocolFeeBps = _feeBps;
    }
    
    function setDecayRate(uint256 _decayBps) external onlyRole(DEFAULT_ADMIN_ROLE) {
        require(_decayBps <= 1000, "Decay too high"); // Max 10% per day
        decayRateBps = _decayBps;
    }
    
    function setTreasury(address _treasury) external onlyRole(DEFAULT_ADMIN_ROLE) {
        require(_treasury != address(0), "Invalid treasury");
        treasury = _treasury;
    }
    
    function withdrawFees() external onlyRole(DEFAULT_ADMIN_ROLE) {
        uint256 fees = accumulatedFees;
        accumulatedFees = 0;
        settlementToken.safeTransfer(treasury, fees);
    }
    
    function pause() external onlyRole(DEFAULT_ADMIN_ROLE) {
        _pause();
    }
    
    function unpause() external onlyRole(DEFAULT_ADMIN_ROLE) {
        _unpause();
    }

    // =============================================================================
    // VIEW FUNCTIONS
    // =============================================================================
    
    function getTimeline(uint256 timelineId) external view returns (Timeline memory) {
        return timelines[timelineId];
    }
    
    function getMarket(uint256 marketId) external view returns (Market memory) {
        return markets[marketId];
    }
    
    function getMarketOutcomeTokenIds(uint256 marketId) external view returns (uint256[] memory) {
        return markets[marketId].outcomeTokenIds;
    }
    
    function getMarketOutcomeLabels(uint256 marketId) external view returns (string[] memory) {
        return markets[marketId].outcomeLabels;
    }
    
    function getShieldStatus(uint256 tokenId) external view returns (ShieldStatus memory) {
        return shields[tokenId];
    }

    // =============================================================================
    // INTERNAL FUNCTIONS
    // =============================================================================
    
    function _encodeTokenId(
        uint256 timelineId,
        uint256 marketId,
        uint256 outcomeIndex
    ) internal pure returns (uint256) {
        return (timelineId << 128) | (marketId << 64) | outcomeIndex;
    }
    
    function _decodeTokenId(uint256 tokenId) internal pure returns (
        uint256 timelineId,
        uint256 marketId,
        uint256 outcomeIndex
    ) {
        timelineId = tokenId >> 128;
        marketId = (tokenId >> 64) & ((1 << 64) - 1);
        outcomeIndex = tokenId & ((1 << 64) - 1);
    }

    // =============================================================================
    // OVERRIDES
    // =============================================================================
    
    function _update(
        address from,
        address to,
        uint256[] memory ids,
        uint256[] memory values
    ) internal virtual override(ERC1155, ERC1155Supply) {
        super._update(from, to, ids, values);
    }

    function supportsInterface(bytes4 interfaceId)
        public
        view
        virtual
        override(ERC1155, AccessControl)
        returns (bool)
    {
        return super.supportsInterface(interfaceId);
    }
}
