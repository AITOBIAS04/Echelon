// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import "@openzeppelin/contracts/utils/Pausable.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";

interface ITimelineShard {
    function quantumDecay(uint256 tokenId, uint256 vrfResult) external;
    function getSpotPrice(uint256 tokenId) external view returns (uint256);
    function totalSupply(uint256 tokenId) external view returns (uint256);
}

/**
 * @title SabotagePool
 * @author Echelon Protocol
 * @notice Manages the War Tax and FUD (Fear, Uncertainty, Doubt) mechanics
 * 
 * War Tax Mechanics:
 * - Every trade contributes a small tax to faction war chests
 * - Factions can use war chests to attack rival timelines
 * - Successful attacks trigger accelerated decay on target shards
 * 
 * FUD Fund Mechanics:
 * - Saboteur agents contribute to FUD funds
 * - When FUD threshold is reached, triggers mass panic event
 * - Mass panic causes 2x decay on all shards in affected market
 */
contract SabotagePool is AccessControl, ReentrancyGuard, Pausable {
    using SafeERC20 for IERC20;

    // =============================================================================
    // ROLES
    // =============================================================================
    
    bytes32 public constant SABOTEUR_ROLE = keccak256("SABOTEUR_ROLE");
    bytes32 public constant FACTION_LEADER_ROLE = keccak256("FACTION_LEADER_ROLE");
    bytes32 public constant EXECUTOR_ROLE = keccak256("EXECUTOR_ROLE");

    // =============================================================================
    // STATE VARIABLES
    // =============================================================================
    
    /// @notice The TimelineShard contract
    ITimelineShard public immutable timelineShard;
    
    /// @notice Settlement token (USDC)
    IERC20 public immutable settlementToken;
    
    /// @notice War tax rate in basis points (50 = 0.5%)
    uint256 public warTaxBps = 50;
    
    /// @notice FUD threshold to trigger mass panic
    uint256 public fudThreshold = 1000 * 1e6; // 1000 USDC equivalent
    
    /// @notice Cooldown between attacks from same faction
    uint256 public attackCooldown = 6 hours;
    
    /// @notice Minimum stake required to launch attack
    uint256 public minAttackStake = 100 * 1e6; // 100 USDC

    // =============================================================================
    // STRUCTS
    // =============================================================================
    
    /// @notice Faction war chest data
    struct Faction {
        uint256 id;
        string name;
        address leader;
        uint256 warChest;
        uint256 totalContributed;
        uint256 successfulAttacks;
        uint256 failedAttacks;
        uint256 lastAttackTimestamp;
        bool isActive;
    }
    
    /// @notice FUD fund for a specific market/timeline
    struct FudFund {
        uint256 balance;
        uint256 contributorCount;
        uint256 lastPanicTimestamp;
        bool isPanicking;
    }
    
    /// @notice Attack record
    struct Attack {
        uint256 id;
        uint256 attackingFactionId;
        uint256 targetTimelineId;
        uint256 targetTokenId;
        uint256 stake;
        uint256 timestamp;
        AttackType attackType;
        AttackStatus status;
        uint256 damage; // Amount of decay caused
    }
    
    /// @notice Saboteur contribution record
    struct SaboteurContribution {
        address saboteur;
        uint256 amount;
        uint256 timestamp;
        uint256 targetMarketId;
    }

    enum AttackType { 
        Raid,           // Direct attack on timeline
        Infiltrate,     // Plant sleeper agent
        Propaganda,     // Spread FUD
        Economic        // Drain liquidity
    }
    
    enum AttackStatus {
        Pending,
        Successful,
        Failed,
        Countered
    }

    // =============================================================================
    // MAPPINGS
    // =============================================================================
    
    /// @notice Faction data by ID
    mapping(uint256 => Faction) public factions;
    
    /// @notice User to faction membership
    mapping(address => uint256) public userFaction;
    
    /// @notice FUD funds by market ID
    mapping(uint256 => FudFund) public fudFunds;
    
    /// @notice Attack records by ID
    mapping(uint256 => Attack) public attacks;
    
    /// @notice Saboteur contributions
    mapping(address => SaboteurContribution[]) public saboteurContributions;
    
    /// @notice Faction counter
    uint256 public nextFactionId = 1;
    
    /// @notice Attack counter
    uint256 public nextAttackId = 1;
    
    /// @notice Total war taxes collected
    uint256 public totalWarTaxes;
    
    /// @notice Defence bonus for shielded timelines
    uint256 public defenceBonusBps = 2000; // 20% defence bonus

    // =============================================================================
    // EVENTS
    // =============================================================================
    
    event FactionCreated(
        uint256 indexed factionId,
        string name,
        address indexed leader
    );
    
    event FactionJoined(
        address indexed user,
        uint256 indexed factionId
    );
    
    event WarTaxCollected(
        uint256 indexed factionId,
        uint256 amount,
        address indexed contributor
    );
    
    event AttackLaunched(
        uint256 indexed attackId,
        uint256 indexed attackingFactionId,
        uint256 indexed targetTimelineId,
        AttackType attackType,
        uint256 stake
    );
    
    event AttackResolved(
        uint256 indexed attackId,
        AttackStatus status,
        uint256 damage
    );
    
    event FudContributed(
        uint256 indexed marketId,
        address indexed saboteur,
        uint256 amount,
        uint256 newTotal
    );
    
    event MassPanicTriggered(
        uint256 indexed marketId,
        uint256 fudAmount,
        uint256 affectedShards
    );
    
    event DefenceActivated(
        uint256 indexed timelineId,
        uint256 indexed defendingFactionId,
        uint256 cost
    );

    // =============================================================================
    // CONSTRUCTOR
    // =============================================================================
    
    constructor(
        address _timelineShard,
        address _settlementToken
    ) {
        require(_timelineShard != address(0), "Invalid shard contract");
        require(_settlementToken != address(0), "Invalid settlement token");
        
        timelineShard = ITimelineShard(_timelineShard);
        settlementToken = IERC20(_settlementToken);
        
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(EXECUTOR_ROLE, msg.sender);
    }

    // =============================================================================
    // FACTION MANAGEMENT
    // =============================================================================
    
    /**
     * @notice Create a new faction
     * @param name Faction name
     */
    function createFaction(string calldata name) external returns (uint256 factionId) {
        require(bytes(name).length > 0 && bytes(name).length <= 32, "Invalid name length");
        require(userFaction[msg.sender] == 0, "Already in a faction");
        
        factionId = nextFactionId++;
        
        factions[factionId] = Faction({
            id: factionId,
            name: name,
            leader: msg.sender,
            warChest: 0,
            totalContributed: 0,
            successfulAttacks: 0,
            failedAttacks: 0,
            lastAttackTimestamp: 0,
            isActive: true
        });
        
        userFaction[msg.sender] = factionId;
        _grantRole(FACTION_LEADER_ROLE, msg.sender);
        
        emit FactionCreated(factionId, name, msg.sender);
    }
    
    /**
     * @notice Join an existing faction
     * @param factionId Faction to join
     */
    function joinFaction(uint256 factionId) external {
        require(factions[factionId].isActive, "Faction not active");
        require(userFaction[msg.sender] == 0, "Already in a faction");
        
        userFaction[msg.sender] = factionId;
        
        emit FactionJoined(msg.sender, factionId);
    }
    
    /**
     * @notice Contribute to faction war chest
     * @param amount Amount to contribute
     */
    function contributeToWarChest(uint256 amount) external nonReentrant {
        uint256 factionId = userFaction[msg.sender];
        require(factionId > 0, "Not in a faction");
        require(amount > 0, "Amount must be positive");
        
        settlementToken.safeTransferFrom(msg.sender, address(this), amount);
        
        factions[factionId].warChest += amount;
        factions[factionId].totalContributed += amount;
        
        emit WarTaxCollected(factionId, amount, msg.sender);
    }
    
    /**
     * @notice Collect war tax from trades (called by TimelineShard)
     * @param trader Address of trader
     * @param amount Trade amount
     */
    function collectWarTax(address trader, uint256 amount) external {
        // Only TimelineShard can call this
        require(msg.sender == address(timelineShard), "Unauthorized");
        
        uint256 tax = (amount * warTaxBps) / 10000;
        if (tax == 0) return;
        
        uint256 factionId = userFaction[trader];
        if (factionId > 0) {
            factions[factionId].warChest += tax;
            factions[factionId].totalContributed += tax;
            totalWarTaxes += tax;
            
            emit WarTaxCollected(factionId, tax, trader);
        }
    }

    // =============================================================================
    // ATTACK MECHANICS
    // =============================================================================
    
    /**
     * @notice Launch an attack on a rival timeline
     * @param targetTimelineId Timeline to attack
     * @param targetTokenId Specific token to target (0 for timeline-wide)
     * @param attackType Type of attack
     * @param stake Amount to stake on attack
     */
    function launchAttack(
        uint256 targetTimelineId,
        uint256 targetTokenId,
        AttackType attackType,
        uint256 stake
    ) external nonReentrant onlyRole(FACTION_LEADER_ROLE) returns (uint256 attackId) {
        uint256 factionId = userFaction[msg.sender];
        Faction storage faction = factions[factionId];
        
        require(faction.isActive, "Faction not active");
        require(stake >= minAttackStake, "Stake too low");
        require(faction.warChest >= stake, "Insufficient war chest");
        require(
            block.timestamp >= faction.lastAttackTimestamp + attackCooldown,
            "Attack on cooldown"
        );
        
        // Deduct stake from war chest
        faction.warChest -= stake;
        faction.lastAttackTimestamp = block.timestamp;
        
        attackId = nextAttackId++;
        
        attacks[attackId] = Attack({
            id: attackId,
            attackingFactionId: factionId,
            targetTimelineId: targetTimelineId,
            targetTokenId: targetTokenId,
            stake: stake,
            timestamp: block.timestamp,
            attackType: attackType,
            status: AttackStatus.Pending,
            damage: 0
        });
        
        emit AttackLaunched(attackId, factionId, targetTimelineId, attackType, stake);
    }
    
    /**
     * @notice Resolve an attack using VRF
     * @param attackId Attack to resolve
     * @param vrfResult Random number from Chainlink VRF
     */
    function resolveAttack(
        uint256 attackId,
        uint256 vrfResult
    ) external onlyRole(EXECUTOR_ROLE) {
        Attack storage attack = attacks[attackId];
        require(attack.status == AttackStatus.Pending, "Attack already resolved");
        
        Faction storage attackingFaction = factions[attack.attackingFactionId];
        
        // Base success rate depends on attack type
        uint256 baseSuccessRate = _getBaseSuccessRate(attack.attackType);
        
        // Modify by stake size (larger stake = higher success)
        uint256 stakeBonus = (attack.stake * 1000) / (minAttackStake * 10); // Up to 10% bonus
        if (stakeBonus > 1000) stakeBonus = 1000;
        
        uint256 successThreshold = baseSuccessRate + stakeBonus;
        
        // Check if target has defence (shield)
        // This would check TimelineShard for shield status
        // For now, simplified random check
        
        uint256 roll = vrfResult % 10000;
        
        if (roll < successThreshold) {
            // Attack successful
            attack.status = AttackStatus.Successful;
            attackingFaction.successfulAttacks++;
            
            // Calculate damage
            uint256 damage = _calculateDamage(attack.attackType, attack.stake);
            attack.damage = damage;
            
            // Apply damage (trigger decay on target)
            if (attack.targetTokenId > 0) {
                // Specific token attack
                timelineShard.quantumDecay(attack.targetTokenId, vrfResult);
            }
            
            // Return stake + bonus
            uint256 bonus = (attack.stake * 2000) / 10000; // 20% bonus
            attackingFaction.warChest += attack.stake + bonus;
            
        } else {
            // Attack failed
            attack.status = AttackStatus.Failed;
            attackingFaction.failedAttacks++;
            
            // Stake is lost (remains in pool for defenders)
        }
        
        emit AttackResolved(attackId, attack.status, attack.damage);
    }
    
    /**
     * @notice Activate defence for a timeline
     * @param timelineId Timeline to defend
     */
    function activateDefence(uint256 timelineId) external nonReentrant {
        uint256 factionId = userFaction[msg.sender];
        require(factionId > 0, "Not in a faction");
        
        uint256 defenceCost = minAttackStake / 2; // Half of min attack stake
        require(factions[factionId].warChest >= defenceCost, "Insufficient war chest");
        
        factions[factionId].warChest -= defenceCost;
        
        // Defence would set a flag on the timeline reducing attack success rate
        // Implementation would interact with TimelineShard
        
        emit DefenceActivated(timelineId, factionId, defenceCost);
    }

    // =============================================================================
    // FUD MECHANICS
    // =============================================================================
    
    /**
     * @notice Contribute FUD to a market (Saboteur action)
     * @param marketId Target market
     * @param amount FUD amount (in settlement tokens)
     */
    function contributeFud(
        uint256 marketId,
        uint256 amount
    ) external nonReentrant onlyRole(SABOTEUR_ROLE) {
        require(amount > 0, "Amount must be positive");
        
        settlementToken.safeTransferFrom(msg.sender, address(this), amount);
        
        FudFund storage fund = fudFunds[marketId];
        fund.balance += amount;
        fund.contributorCount++;
        
        saboteurContributions[msg.sender].push(SaboteurContribution({
            saboteur: msg.sender,
            amount: amount,
            timestamp: block.timestamp,
            targetMarketId: marketId
        }));
        
        emit FudContributed(marketId, msg.sender, amount, fund.balance);
        
        // Check if threshold reached
        if (fund.balance >= fudThreshold && !fund.isPanicking) {
            _triggerMassPanic(marketId);
        }
    }
    
    /**
     * @notice Trigger mass panic event
     * @param marketId Market experiencing panic
     */
    function _triggerMassPanic(uint256 marketId) internal {
        FudFund storage fund = fudFunds[marketId];
        
        fund.isPanicking = true;
        fund.lastPanicTimestamp = block.timestamp;
        
        // Mass panic causes 2x decay on all shards in market
        // This would call TimelineShard to apply accelerated decay
        // Actual implementation depends on how market tokens are stored
        
        uint256 fudAmount = fund.balance;
        fund.balance = 0; // Reset FUD fund after panic
        
        emit MassPanicTriggered(marketId, fudAmount, 0); // Affected shards count TBD
    }
    
    /**
     * @notice Check if market is in panic state
     * @param marketId Market to check
     */
    function isMarketPanicking(uint256 marketId) external view returns (bool) {
        FudFund memory fund = fudFunds[marketId];
        
        // Panic lasts 24 hours
        if (fund.isPanicking && block.timestamp < fund.lastPanicTimestamp + 24 hours) {
            return true;
        }
        return false;
    }
    
    /**
     * @notice End panic state for a market
     * @param marketId Market to calm
     */
    function endPanic(uint256 marketId) external onlyRole(EXECUTOR_ROLE) {
        FudFund storage fund = fudFunds[marketId];
        require(fund.isPanicking, "Not panicking");
        require(
            block.timestamp >= fund.lastPanicTimestamp + 24 hours,
            "Panic not over"
        );
        
        fund.isPanicking = false;
    }

    // =============================================================================
    // INTERNAL FUNCTIONS
    // =============================================================================
    
    function _getBaseSuccessRate(AttackType attackType) internal pure returns (uint256) {
        if (attackType == AttackType.Raid) {
            return 4000; // 40% base success
        } else if (attackType == AttackType.Infiltrate) {
            return 5000; // 50% base success
        } else if (attackType == AttackType.Propaganda) {
            return 6000; // 60% base success
        } else if (attackType == AttackType.Economic) {
            return 3500; // 35% base success
        }
        return 4000;
    }
    
    function _calculateDamage(AttackType attackType, uint256 stake) internal pure returns (uint256) {
        // Damage multiplier based on attack type
        uint256 multiplier;
        
        if (attackType == AttackType.Raid) {
            multiplier = 150; // 1.5x stake
        } else if (attackType == AttackType.Infiltrate) {
            multiplier = 100; // 1x stake (but ongoing effect)
        } else if (attackType == AttackType.Propaganda) {
            multiplier = 200; // 2x stake (FUD damage)
        } else if (attackType == AttackType.Economic) {
            multiplier = 250; // 2.5x stake
        } else {
            multiplier = 100;
        }
        
        return (stake * multiplier) / 100;
    }

    // =============================================================================
    // ADMIN FUNCTIONS
    // =============================================================================
    
    function setWarTaxBps(uint256 _warTaxBps) external onlyRole(DEFAULT_ADMIN_ROLE) {
        require(_warTaxBps <= 500, "Tax too high"); // Max 5%
        warTaxBps = _warTaxBps;
    }
    
    function setFudThreshold(uint256 _threshold) external onlyRole(DEFAULT_ADMIN_ROLE) {
        fudThreshold = _threshold;
    }
    
    function setAttackCooldown(uint256 _cooldown) external onlyRole(DEFAULT_ADMIN_ROLE) {
        attackCooldown = _cooldown;
    }
    
    function setMinAttackStake(uint256 _minStake) external onlyRole(DEFAULT_ADMIN_ROLE) {
        minAttackStake = _minStake;
    }
    
    function grantSaboteurRole(address saboteur) external onlyRole(DEFAULT_ADMIN_ROLE) {
        _grantRole(SABOTEUR_ROLE, saboteur);
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
    
    function getFaction(uint256 factionId) external view returns (Faction memory) {
        return factions[factionId];
    }
    
    function getAttack(uint256 attackId) external view returns (Attack memory) {
        return attacks[attackId];
    }
    
    function getFudFund(uint256 marketId) external view returns (FudFund memory) {
        return fudFunds[marketId];
    }
    
    function getUserFaction(address user) external view returns (uint256) {
        return userFaction[user];
    }
    
    function getSaboteurContributions(address saboteur) external view returns (SaboteurContribution[] memory) {
        return saboteurContributions[saboteur];
    }
}
