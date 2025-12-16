// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import "@openzeppelin/contracts/utils/Pausable.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";

interface ITimelineShard {
    function totalSupply(uint256 tokenId) external view returns (uint256);
}

interface IEchelonVRF {
    function requestHotPotatoTransfer(uint256 eventId) external returns (uint256);
    function getHotPotatoResult(uint256 eventId) external view returns (uint256);
}

/**
 * @title HotPotatoEvents
 * @author Echelon Protocol
 * @notice High-drama mechanic where a "bomb" passes between timeline bubbles
 * 
 * Mechanics:
 * - The Bomb: 60-minute countdown timer hovers over one timeline bubble
 * - The Pop: Timer hits 00:00 = bubble eliminated, all shards destroyed
 * - The Pass: Pay "Bribe Fee" to pass bomb to neighbouring bubble
 * - The Catch: Each pass shortens timer (60m -> 50m -> 40m -> ...)
 * 
 * Creates viral "Musical Chairs" moments where whales frantically outbid.
 */
contract HotPotatoEvents is AccessControl, ReentrancyGuard, Pausable {
    using SafeERC20 for IERC20;

    // =============================================================================
    // ROLES
    // =============================================================================
    
    bytes32 public constant EVENT_MANAGER_ROLE = keccak256("EVENT_MANAGER_ROLE");
    bytes32 public constant EXECUTOR_ROLE = keccak256("EXECUTOR_ROLE");

    // =============================================================================
    // STATE VARIABLES
    // =============================================================================
    
    ITimelineShard public immutable timelineShard;
    IEchelonVRF public vrfConsumer;
    IERC20 public immutable settlementToken;
    
    uint256 public nextEventId = 1;
    uint256 public constant BASE_TIMER = 60 minutes;
    uint256 public constant TIMER_REDUCTION = 10 minutes;
    uint256 public constant MIN_TIMER = 10 minutes;
    
    uint256 public baseBribeFee = 50 * 1e6; // 50 USDC
    uint256 public bribeFeeMultiplier = 110; // 10% increase per pass
    uint256 public survivorPoolBps = 7000; // 70% to survivors
    uint256 public lastPasserBps = 2000; // 20% to last passer
    uint256 public protocolFeeBps = 1000; // 10% protocol fee
    address public treasury;

    // =============================================================================
    // STRUCTS
    // =============================================================================
    
    struct HotPotatoEvent {
        uint256 id;
        uint256[] participatingTimelineIds;
        uint256 currentHolderIndex;
        uint256 bombPlacedAt;
        uint256 currentTimer;
        uint256 passCount;
        uint256 prizePool;
        uint256 currentBribeFee;
        address lastPasser;
        EventStatus status;
        uint256[] eliminatedIndices;
    }
    
    struct PassAttempt {
        address passer;
        uint256 targetIndex;
        uint256 fee;
        uint256 timestamp;
        bool successful;
    }

    enum EventStatus { Pending, Active, Completed, Cancelled }

    // =============================================================================
    // MAPPINGS
    // =============================================================================
    
    mapping(uint256 => HotPotatoEvent) public events;
    mapping(uint256 => PassAttempt[]) public passHistory;
    mapping(address => uint256[]) public userEvents;
    mapping(uint256 => uint256) public timelineInEvent;
    mapping(uint256 => mapping(address => bool)) public rewardsClaimed;

    // =============================================================================
    // EVENTS
    // =============================================================================
    
    event HotPotatoStarted(
        uint256 indexed eventId,
        uint256[] timelineIds,
        uint256 initialHolder,
        uint256 timer
    );
    
    event BombPassed(
        uint256 indexed eventId,
        address indexed passer,
        uint256 fromTimeline,
        uint256 toTimeline,
        uint256 bribeFee,
        uint256 newTimer
    );
    
    event BubblePopped(
        uint256 indexed eventId,
        uint256 indexed timelineId,
        uint256 shardsDestroyed
    );
    
    event HotPotatoEnded(
        uint256 indexed eventId,
        uint256[] survivors,
        uint256 prizePool,
        address lastPasser
    );
    
    event RewardClaimed(
        uint256 indexed eventId,
        address indexed claimer,
        uint256 amount
    );

    // =============================================================================
    // CONSTRUCTOR
    // =============================================================================
    
    constructor(
        address _timelineShard,
        address _settlementToken,
        address _treasury
    ) {
        require(_timelineShard != address(0), "Invalid shard contract");
        require(_settlementToken != address(0), "Invalid settlement token");
        require(_treasury != address(0), "Invalid treasury");
        
        timelineShard = ITimelineShard(_timelineShard);
        settlementToken = IERC20(_settlementToken);
        treasury = _treasury;
        
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(EVENT_MANAGER_ROLE, msg.sender);
        _grantRole(EXECUTOR_ROLE, msg.sender);
    }

    // =============================================================================
    // EVENT MANAGEMENT
    // =============================================================================
    
    function startHotPotato(
        uint256[] calldata timelineIds,
        uint256 initialHolderIndex
    ) external onlyRole(EVENT_MANAGER_ROLE) returns (uint256 eventId) {
        require(timelineIds.length >= 2, "Need at least 2 timelines");
        require(timelineIds.length <= 10, "Max 10 timelines");
        require(initialHolderIndex < timelineIds.length, "Invalid initial holder");
        
        for (uint256 i = 0; i < timelineIds.length; i++) {
            require(timelineInEvent[timelineIds[i]] == 0, "Timeline already in event");
        }
        
        eventId = nextEventId++;
        
        uint256[] memory ids = new uint256[](timelineIds.length);
        for (uint256 i = 0; i < timelineIds.length; i++) {
            ids[i] = timelineIds[i];
            timelineInEvent[timelineIds[i]] = eventId;
        }
        
        events[eventId] = HotPotatoEvent({
            id: eventId,
            participatingTimelineIds: ids,
            currentHolderIndex: initialHolderIndex,
            bombPlacedAt: block.timestamp,
            currentTimer: BASE_TIMER,
            passCount: 0,
            prizePool: 0,
            currentBribeFee: baseBribeFee,
            lastPasser: address(0),
            status: EventStatus.Active,
            eliminatedIndices: new uint256[](0)
        });
        
        emit HotPotatoStarted(eventId, ids, timelineIds[initialHolderIndex], BASE_TIMER);
    }
    
    function passBomb(
        uint256 eventId,
        uint256 targetIndex
    ) external nonReentrant whenNotPaused {
        HotPotatoEvent storage evt = events[eventId];
        require(evt.status == EventStatus.Active, "Event not active");
        require(targetIndex < evt.participatingTimelineIds.length, "Invalid target");
        require(targetIndex != evt.currentHolderIndex, "Can't pass to self");
        require(!_isEliminated(eventId, targetIndex), "Target eliminated");
        
        uint256 timeRemaining = _getTimeRemaining(eventId);
        require(timeRemaining > 0, "Bomb already exploded");
        
        uint256 fee = evt.currentBribeFee;
        settlementToken.safeTransferFrom(msg.sender, address(this), fee);
        evt.prizePool += fee;
        
        uint256 fromTimeline = evt.participatingTimelineIds[evt.currentHolderIndex];
        uint256 toTimeline = evt.participatingTimelineIds[targetIndex];
        
        passHistory[eventId].push(PassAttempt({
            passer: msg.sender,
            targetIndex: targetIndex,
            fee: fee,
            timestamp: block.timestamp,
            successful: true
        }));
        
        evt.currentHolderIndex = targetIndex;
        evt.bombPlacedAt = block.timestamp;
        evt.passCount++;
        evt.lastPasser = msg.sender;
        
        if (evt.currentTimer > MIN_TIMER + TIMER_REDUCTION) {
            evt.currentTimer -= TIMER_REDUCTION;
        } else {
            evt.currentTimer = MIN_TIMER;
        }
        
        evt.currentBribeFee = (fee * bribeFeeMultiplier) / 100;
        
        emit BombPassed(eventId, msg.sender, fromTimeline, toTimeline, fee, evt.currentTimer);
    }
    
    function triggerExplosion(uint256 eventId) external onlyRole(EXECUTOR_ROLE) {
        HotPotatoEvent storage evt = events[eventId];
        require(evt.status == EventStatus.Active, "Event not active");
        
        uint256 timeRemaining = _getTimeRemaining(eventId);
        require(timeRemaining == 0, "Timer not expired");
        
        uint256 eliminatedIndex = evt.currentHolderIndex;
        uint256 eliminatedTimeline = evt.participatingTimelineIds[eliminatedIndex];
        
        evt.eliminatedIndices.push(eliminatedIndex);
        
        emit BubblePopped(eventId, eliminatedTimeline, 0);
        
        uint256 remainingCount = evt.participatingTimelineIds.length - evt.eliminatedIndices.length;
        
        if (remainingCount <= 1) {
            _endEvent(eventId);
        } else {
            _selectNewHolder(eventId);
        }
    }
    
    function _selectNewHolder(uint256 eventId) internal {
        HotPotatoEvent storage evt = events[eventId];
        
        if (address(vrfConsumer) != address(0)) {
            vrfConsumer.requestHotPotatoTransfer(eventId);
        } else {
            uint256 remaining = _getRemainingCount(eventId);
            uint256 randomIndex = uint256(blockhash(block.number - 1)) % remaining;
            
            uint256 count = 0;
            for (uint256 i = 0; i < evt.participatingTimelineIds.length; i++) {
                if (!_isEliminated(eventId, i)) {
                    if (count == randomIndex) {
                        evt.currentHolderIndex = i;
                        evt.bombPlacedAt = block.timestamp;
                        break;
                    }
                    count++;
                }
            }
        }
    }
    
    function applyVRFResult(uint256 eventId) external onlyRole(EXECUTOR_ROLE) {
        require(address(vrfConsumer) != address(0), "VRF not configured");
        
        HotPotatoEvent storage evt = events[eventId];
        require(evt.status == EventStatus.Active, "Event not active");
        
        uint256 vrfResult = vrfConsumer.getHotPotatoResult(eventId);
        require(vrfResult != 0, "VRF not fulfilled");
        
        uint256 remaining = _getRemainingCount(eventId);
        uint256 randomIndex = vrfResult % remaining;
        
        uint256 count = 0;
        for (uint256 i = 0; i < evt.participatingTimelineIds.length; i++) {
            if (!_isEliminated(eventId, i)) {
                if (count == randomIndex) {
                    evt.currentHolderIndex = i;
                    evt.bombPlacedAt = block.timestamp;
                    break;
                }
                count++;
            }
        }
    }
    
    function _endEvent(uint256 eventId) internal {
        HotPotatoEvent storage evt = events[eventId];
        evt.status = EventStatus.Completed;
        
        for (uint256 i = 0; i < evt.participatingTimelineIds.length; i++) {
            timelineInEvent[evt.participatingTimelineIds[i]] = 0;
        }
        
        uint256 protocolFee = (evt.prizePool * protocolFeeBps) / 10000;
        uint256 lastPasserPrize = (evt.prizePool * lastPasserBps) / 10000;
        
        if (protocolFee > 0) {
            settlementToken.safeTransfer(treasury, protocolFee);
        }
        
        if (lastPasserPrize > 0 && evt.lastPasser != address(0)) {
            settlementToken.safeTransfer(evt.lastPasser, lastPasserPrize);
        }
        
        uint256[] memory survivors = _getSurvivors(eventId);
        emit HotPotatoEnded(eventId, survivors, evt.prizePool, evt.lastPasser);
    }
    
    function claimSurvivorReward(uint256 eventId) external nonReentrant {
        HotPotatoEvent storage evt = events[eventId];
        require(evt.status == EventStatus.Completed, "Event not completed");
        require(!rewardsClaimed[eventId][msg.sender], "Already claimed");
        
        uint256 callerShare = _calculateSurvivorShare(eventId, msg.sender);
        require(callerShare > 0, "No reward to claim");
        
        rewardsClaimed[eventId][msg.sender] = true;
        settlementToken.safeTransfer(msg.sender, callerShare);
        
        emit RewardClaimed(eventId, msg.sender, callerShare);
    }

    // =============================================================================
    // INTERNAL VIEW FUNCTIONS
    // =============================================================================
    
    function _getTimeRemaining(uint256 eventId) internal view returns (uint256) {
        HotPotatoEvent memory evt = events[eventId];
        uint256 elapsed = block.timestamp - evt.bombPlacedAt;
        if (elapsed >= evt.currentTimer) return 0;
        return evt.currentTimer - elapsed;
    }
    
    function _isEliminated(uint256 eventId, uint256 index) internal view returns (bool) {
        HotPotatoEvent memory evt = events[eventId];
        for (uint256 i = 0; i < evt.eliminatedIndices.length; i++) {
            if (evt.eliminatedIndices[i] == index) return true;
        }
        return false;
    }
    
    function _getRemainingCount(uint256 eventId) internal view returns (uint256) {
        HotPotatoEvent memory evt = events[eventId];
        return evt.participatingTimelineIds.length - evt.eliminatedIndices.length;
    }
    
    function _getSurvivors(uint256 eventId) internal view returns (uint256[] memory) {
        HotPotatoEvent memory evt = events[eventId];
        uint256 remaining = _getRemainingCount(eventId);
        
        uint256[] memory survivors = new uint256[](remaining);
        uint256 count = 0;
        
        for (uint256 i = 0; i < evt.participatingTimelineIds.length; i++) {
            if (!_isEliminated(eventId, i)) {
                survivors[count] = evt.participatingTimelineIds[i];
                count++;
            }
        }
        return survivors;
    }
    
    function _calculateSurvivorShare(uint256 eventId, address) internal view returns (uint256) {
        HotPotatoEvent memory evt = events[eventId];
        uint256 survivorPool = (evt.prizePool * survivorPoolBps) / 10000;
        uint256 remaining = _getRemainingCount(eventId);
        if (remaining == 0) return 0;
        return survivorPool / remaining;
    }

    // =============================================================================
    // ADMIN FUNCTIONS
    // =============================================================================
    
    function setVRFConsumer(address _vrfConsumer) external onlyRole(DEFAULT_ADMIN_ROLE) {
        vrfConsumer = IEchelonVRF(_vrfConsumer);
    }
    
    function setBaseBribeFee(uint256 _fee) external onlyRole(DEFAULT_ADMIN_ROLE) {
        baseBribeFee = _fee;
    }
    
    function setBribeFeeMultiplier(uint256 _multiplier) external onlyRole(DEFAULT_ADMIN_ROLE) {
        require(_multiplier >= 100 && _multiplier <= 200, "Invalid multiplier");
        bribeFeeMultiplier = _multiplier;
    }
    
    function setTreasury(address _treasury) external onlyRole(DEFAULT_ADMIN_ROLE) {
        require(_treasury != address(0), "Invalid treasury");
        treasury = _treasury;
    }
    
    function cancelEvent(uint256 eventId) external onlyRole(DEFAULT_ADMIN_ROLE) {
        HotPotatoEvent storage evt = events[eventId];
        require(evt.status == EventStatus.Active, "Event not active");
        
        evt.status = EventStatus.Cancelled;
        
        for (uint256 i = 0; i < evt.participatingTimelineIds.length; i++) {
            timelineInEvent[evt.participatingTimelineIds[i]] = 0;
        }
        
        if (evt.prizePool > 0) {
            address recipient = evt.lastPasser != address(0) ? evt.lastPasser : treasury;
            settlementToken.safeTransfer(recipient, evt.prizePool);
        }
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
    
    function getEvent(uint256 eventId) external view returns (HotPotatoEvent memory) {
        return events[eventId];
    }
    
    function getTimeRemaining(uint256 eventId) external view returns (uint256) {
        return _getTimeRemaining(eventId);
    }
    
    function getCurrentHolder(uint256 eventId) external view returns (uint256) {
        HotPotatoEvent memory evt = events[eventId];
        return evt.participatingTimelineIds[evt.currentHolderIndex];
    }
    
    function getPassHistory(uint256 eventId) external view returns (PassAttempt[] memory) {
        return passHistory[eventId];
    }
    
    function getSurvivors(uint256 eventId) external view returns (uint256[] memory) {
        return _getSurvivors(eventId);
    }
    
    function isEliminated(uint256 eventId, uint256 index) external view returns (bool) {
        return _isEliminated(eventId, index);
    }
    
    function getRemainingCount(uint256 eventId) external view returns (uint256) {
        return _getRemainingCount(eventId);
    }
}
