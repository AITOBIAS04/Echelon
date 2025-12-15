// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@chainlink/contracts/src/v0.8/vrf/VRFConsumerBaseV2.sol";
import "@chainlink/contracts/src/v0.8/interfaces/VRFCoordinatorV2Interface.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";

interface ITimelineShard {
    function quantumDecay(uint256 tokenId, uint256 vrfResult) external;
    function createTimeline(
        uint256 parentTimelineId,
        bytes32 forkPointStateHash,
        string calldata description,
        uint256 expiryTimestamp,
        uint256 vrfSeed
    ) external returns (uint256);
}

interface ISabotagePool {
    function resolveAttack(uint256 attackId, uint256 vrfResult) external;
}

/**
 * @title EchelonVRFConsumer
 * @author Echelon Protocol
 * @notice Manages Chainlink VRF requests for timeline forks and quantum decay
 * 
 * VRF is used for:
 * 1. Timeline Fork Seeds - Determining how timelines diverge from reality
 * 2. Quantum Decay - Random daily shard burning
 * 3. Attack Resolution - Determining success/failure of faction attacks
 * 4. Hot Potato - Random bomb transfers
 */
contract EchelonVRFConsumer is VRFConsumerBaseV2, AccessControl {
    
    // =============================================================================
    // ROLES
    // =============================================================================
    
    bytes32 public constant REQUESTER_ROLE = keccak256("REQUESTER_ROLE");

    // =============================================================================
    // VRF CONFIG
    // =============================================================================
    
    VRFCoordinatorV2Interface public immutable vrfCoordinator;
    
    /// @notice Subscription ID for Chainlink VRF
    uint64 public subscriptionId;
    
    /// @notice Key hash for VRF (gas lane)
    bytes32 public keyHash;
    
    /// @notice Callback gas limit
    uint32 public callbackGasLimit = 500000;
    
    /// @notice Request confirmations
    uint16 public requestConfirmations = 3;
    
    /// @notice Number of random words per request
    uint32 public numWords = 1;

    // =============================================================================
    // STATE
    // =============================================================================
    
    /// @notice TimelineShard contract
    ITimelineShard public timelineShard;
    
    /// @notice SabotagePool contract
    ISabotagePool public sabotagePool;
    
    /// @notice Request type enum
    enum RequestType {
        TimelineFork,
        QuantumDecay,
        AttackResolution,
        HotPotato
    }
    
    /// @notice Request metadata
    struct VRFRequest {
        RequestType requestType;
        uint256 targetId;           // tokenId, attackId, or timelineId
        address requester;
        uint256 timestamp;
        bool fulfilled;
        uint256[] randomWords;
    }
    
    /// @notice Pending request by request ID
    mapping(uint256 => VRFRequest) public requests;
    
    /// @notice Pending decay requests by token ID
    mapping(uint256 => uint256) public pendingDecayRequests;
    
    /// @notice Last decay request timestamp per token
    mapping(uint256 => uint256) public lastDecayRequest;
    
    /// @notice Minimum time between decay requests (prevents spam)
    uint256 public decayRequestCooldown = 23 hours;

    // =============================================================================
    // EVENTS
    // =============================================================================
    
    event VRFRequested(
        uint256 indexed requestId,
        RequestType requestType,
        uint256 targetId,
        address requester
    );
    
    event VRFFulfilled(
        uint256 indexed requestId,
        RequestType requestType,
        uint256 targetId,
        uint256[] randomWords
    );
    
    event TimelineForkSeeded(
        uint256 indexed timelineId,
        uint256 vrfSeed
    );
    
    event QuantumDecayTriggered(
        uint256 indexed tokenId,
        uint256 vrfResult
    );
    
    event AttackResolutionTriggered(
        uint256 indexed attackId,
        uint256 vrfResult
    );

    // =============================================================================
    // CONSTRUCTOR
    // =============================================================================
    
    /**
     * @param _vrfCoordinator Chainlink VRF Coordinator address
     * @param _subscriptionId Chainlink VRF subscription ID
     * @param _keyHash Gas lane key hash
     */
    constructor(
        address _vrfCoordinator,
        uint64 _subscriptionId,
        bytes32 _keyHash
    ) VRFConsumerBaseV2(_vrfCoordinator) {
        vrfCoordinator = VRFCoordinatorV2Interface(_vrfCoordinator);
        subscriptionId = _subscriptionId;
        keyHash = _keyHash;
        
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(REQUESTER_ROLE, msg.sender);
    }

    // =============================================================================
    // CONFIGURATION
    // =============================================================================
    
    function setTimelineShard(address _timelineShard) external onlyRole(DEFAULT_ADMIN_ROLE) {
        require(_timelineShard != address(0), "Invalid address");
        timelineShard = ITimelineShard(_timelineShard);
    }
    
    function setSabotagePool(address _sabotagePool) external onlyRole(DEFAULT_ADMIN_ROLE) {
        require(_sabotagePool != address(0), "Invalid address");
        sabotagePool = ISabotagePool(_sabotagePool);
    }
    
    function setVRFConfig(
        uint64 _subscriptionId,
        bytes32 _keyHash,
        uint32 _callbackGasLimit,
        uint16 _requestConfirmations
    ) external onlyRole(DEFAULT_ADMIN_ROLE) {
        subscriptionId = _subscriptionId;
        keyHash = _keyHash;
        callbackGasLimit = _callbackGasLimit;
        requestConfirmations = _requestConfirmations;
    }
    
    function setDecayRequestCooldown(uint256 _cooldown) external onlyRole(DEFAULT_ADMIN_ROLE) {
        decayRequestCooldown = _cooldown;
    }

    // =============================================================================
    // VRF REQUESTS
    // =============================================================================
    
    /**
     * @notice Request VRF for timeline fork
     * @param parentTimelineId Parent timeline (0 for canonical)
     * @param forkPointStateHash State hash at fork point
     * @param description Timeline description
     * @param expiryTimestamp When timeline expires
     */
    function requestTimelineFork(
        uint256 parentTimelineId,
        bytes32 forkPointStateHash,
        string calldata description,
        uint256 expiryTimestamp
    ) external onlyRole(REQUESTER_ROLE) returns (uint256 requestId) {
        requestId = vrfCoordinator.requestRandomWords(
            keyHash,
            subscriptionId,
            requestConfirmations,
            callbackGasLimit,
            numWords
        );
        
        // Store request metadata
        // We encode the fork params in targetId for simplicity
        // In production, use a separate mapping for fork params
        requests[requestId] = VRFRequest({
            requestType: RequestType.TimelineFork,
            targetId: parentTimelineId, // Simplified - full params stored separately
            requester: msg.sender,
            timestamp: block.timestamp,
            fulfilled: false,
            randomWords: new uint256[](0)
        });
        
        // Store fork params (simplified - in production use struct mapping)
        _storeForkParams(requestId, parentTimelineId, forkPointStateHash, description, expiryTimestamp);
        
        emit VRFRequested(requestId, RequestType.TimelineFork, parentTimelineId, msg.sender);
    }
    
    /**
     * @notice Request VRF for quantum decay
     * @param tokenId Token to apply decay to
     */
    function requestQuantumDecay(uint256 tokenId) external onlyRole(REQUESTER_ROLE) returns (uint256 requestId) {
        require(
            block.timestamp >= lastDecayRequest[tokenId] + decayRequestCooldown,
            "Decay request on cooldown"
        );
        require(pendingDecayRequests[tokenId] == 0, "Decay already pending");
        
        requestId = vrfCoordinator.requestRandomWords(
            keyHash,
            subscriptionId,
            requestConfirmations,
            callbackGasLimit,
            numWords
        );
        
        requests[requestId] = VRFRequest({
            requestType: RequestType.QuantumDecay,
            targetId: tokenId,
            requester: msg.sender,
            timestamp: block.timestamp,
            fulfilled: false,
            randomWords: new uint256[](0)
        });
        
        pendingDecayRequests[tokenId] = requestId;
        lastDecayRequest[tokenId] = block.timestamp;
        
        emit VRFRequested(requestId, RequestType.QuantumDecay, tokenId, msg.sender);
    }
    
    /**
     * @notice Request VRF for attack resolution
     * @param attackId Attack to resolve
     */
    function requestAttackResolution(uint256 attackId) external onlyRole(REQUESTER_ROLE) returns (uint256 requestId) {
        requestId = vrfCoordinator.requestRandomWords(
            keyHash,
            subscriptionId,
            requestConfirmations,
            callbackGasLimit,
            numWords
        );
        
        requests[requestId] = VRFRequest({
            requestType: RequestType.AttackResolution,
            targetId: attackId,
            requester: msg.sender,
            timestamp: block.timestamp,
            fulfilled: false,
            randomWords: new uint256[](0)
        });
        
        emit VRFRequested(requestId, RequestType.AttackResolution, attackId, msg.sender);
    }
    
    /**
     * @notice Request VRF for hot potato bomb transfer
     * @param eventId Hot potato event ID
     */
    function requestHotPotatoTransfer(uint256 eventId) external onlyRole(REQUESTER_ROLE) returns (uint256 requestId) {
        requestId = vrfCoordinator.requestRandomWords(
            keyHash,
            subscriptionId,
            requestConfirmations,
            callbackGasLimit,
            numWords
        );
        
        requests[requestId] = VRFRequest({
            requestType: RequestType.HotPotato,
            targetId: eventId,
            requester: msg.sender,
            timestamp: block.timestamp,
            fulfilled: false,
            randomWords: new uint256[](0)
        });
        
        emit VRFRequested(requestId, RequestType.HotPotato, eventId, msg.sender);
    }

    // =============================================================================
    // VRF CALLBACK
    // =============================================================================
    
    /**
     * @notice Chainlink VRF callback
     * @param requestId Request ID being fulfilled
     * @param randomWords Array of random words
     */
    function fulfillRandomWords(
        uint256 requestId,
        uint256[] memory randomWords
    ) internal override {
        VRFRequest storage request = requests[requestId];
        require(!request.fulfilled, "Already fulfilled");
        
        request.fulfilled = true;
        request.randomWords = randomWords;
        
        uint256 randomWord = randomWords[0];
        
        emit VRFFulfilled(requestId, request.requestType, request.targetId, randomWords);
        
        // Route to appropriate handler
        if (request.requestType == RequestType.TimelineFork) {
            _handleTimelineFork(requestId, randomWord);
        } else if (request.requestType == RequestType.QuantumDecay) {
            _handleQuantumDecay(request.targetId, randomWord);
        } else if (request.requestType == RequestType.AttackResolution) {
            _handleAttackResolution(request.targetId, randomWord);
        } else if (request.requestType == RequestType.HotPotato) {
            _handleHotPotato(request.targetId, randomWord);
        }
    }
    
    /**
     * @notice Handle timeline fork VRF result
     */
    function _handleTimelineFork(uint256 requestId, uint256 vrfSeed) internal {
        // Retrieve stored fork params and create timeline
        // Simplified implementation - in production, retrieve full params
        ForkParams memory params = forkParams[requestId];
        
        if (address(timelineShard) != address(0)) {
            uint256 timelineId = timelineShard.createTimeline(
                params.parentTimelineId,
                params.forkPointStateHash,
                params.description,
                params.expiryTimestamp,
                vrfSeed
            );
            
            emit TimelineForkSeeded(timelineId, vrfSeed);
        }
    }
    
    /**
     * @notice Handle quantum decay VRF result
     */
    function _handleQuantumDecay(uint256 tokenId, uint256 vrfResult) internal {
        // Clear pending request
        delete pendingDecayRequests[tokenId];
        
        if (address(timelineShard) != address(0)) {
            timelineShard.quantumDecay(tokenId, vrfResult);
            emit QuantumDecayTriggered(tokenId, vrfResult);
        }
    }
    
    /**
     * @notice Handle attack resolution VRF result
     */
    function _handleAttackResolution(uint256 attackId, uint256 vrfResult) internal {
        if (address(sabotagePool) != address(0)) {
            sabotagePool.resolveAttack(attackId, vrfResult);
            emit AttackResolutionTriggered(attackId, vrfResult);
        }
    }
    
    /**
     * @notice Handle hot potato VRF result
     */
    function _handleHotPotato(uint256 eventId, uint256 vrfResult) internal {
        // Hot potato logic would be implemented in a separate contract
        // This just stores the result for the HotPotatoEvent contract to consume
        hotPotatoResults[eventId] = vrfResult;
    }

    // =============================================================================
    // FORK PARAMS STORAGE (Simplified)
    // =============================================================================
    
    struct ForkParams {
        uint256 parentTimelineId;
        bytes32 forkPointStateHash;
        string description;
        uint256 expiryTimestamp;
    }
    
    mapping(uint256 => ForkParams) public forkParams;
    mapping(uint256 => uint256) public hotPotatoResults;
    
    function _storeForkParams(
        uint256 requestId,
        uint256 parentTimelineId,
        bytes32 forkPointStateHash,
        string calldata description,
        uint256 expiryTimestamp
    ) internal {
        forkParams[requestId] = ForkParams({
            parentTimelineId: parentTimelineId,
            forkPointStateHash: forkPointStateHash,
            description: description,
            expiryTimestamp: expiryTimestamp
        });
    }

    // =============================================================================
    // BATCH OPERATIONS (Chainlink Automation)
    // =============================================================================
    
    /**
     * @notice Request decay for multiple tokens (batch operation)
     * @param tokenIds Array of token IDs to request decay for
     */
    function requestBatchQuantumDecay(uint256[] calldata tokenIds) external onlyRole(REQUESTER_ROLE) {
        for (uint256 i = 0; i < tokenIds.length; i++) {
            uint256 tokenId = tokenIds[i];
            
            // Skip if on cooldown or pending
            if (
                block.timestamp < lastDecayRequest[tokenId] + decayRequestCooldown ||
                pendingDecayRequests[tokenId] != 0
            ) {
                continue;
            }
            
            uint256 requestId = vrfCoordinator.requestRandomWords(
                keyHash,
                subscriptionId,
                requestConfirmations,
                callbackGasLimit,
                numWords
            );
            
            requests[requestId] = VRFRequest({
                requestType: RequestType.QuantumDecay,
                targetId: tokenId,
                requester: msg.sender,
                timestamp: block.timestamp,
                fulfilled: false,
                randomWords: new uint256[](0)
            });
            
            pendingDecayRequests[tokenId] = requestId;
            lastDecayRequest[tokenId] = block.timestamp;
            
            emit VRFRequested(requestId, RequestType.QuantumDecay, tokenId, msg.sender);
        }
    }

    // =============================================================================
    // VIEW FUNCTIONS
    // =============================================================================
    
    function getRequest(uint256 requestId) external view returns (VRFRequest memory) {
        return requests[requestId];
    }
    
    function getPendingDecayRequest(uint256 tokenId) external view returns (uint256) {
        return pendingDecayRequests[tokenId];
    }
    
    function canRequestDecay(uint256 tokenId) external view returns (bool) {
        return (
            block.timestamp >= lastDecayRequest[tokenId] + decayRequestCooldown &&
            pendingDecayRequests[tokenId] == 0
        );
    }
    
    function getHotPotatoResult(uint256 eventId) external view returns (uint256) {
        return hotPotatoResults[eventId];
    }
}
