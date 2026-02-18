# Echelon Oracle Degraded Modes Specification

**Document Version:** 1.0  
**Status:** Active Specification  
**Last Updated:** January 2026

---

## Executive Summary

This document defines the three-tier oracle degraded mode system for Echelon prediction markets. The system ensures graceful degradation of settlement guarantees when external data feeds become unavailable or unreliable, maintaining market integrity across all operating conditions.

### Mode Overview

| Mode | Name | Trigger | Settlement Method | Confidence |
|------|------|---------|-------------------|------------|
| **Mode 0** | Deterministic Referee | All feeds available (<5 min staleness) | 100% deterministic via simulation logs | 1.00 |
| **Mode 1** | Evidence Oracle | One or more feeds degraded, but sufficient evidence remains | OSINT evidence bundle with dispute window | 0.50-0.99 |
| **Mode 2** | Conservative Operations | Multiple critical feeds unavailable or confidence <0.5 | Manual adjudication with restricted actions | 0.00-0.49 |

---

## Mode 0: Deterministic Referee (Ideal State)

### Trigger Conditions

Mode 0 is the ideal operating state when all primary data feeds are available and fresh:

- **Feed Freshness:** All feeds have staleness <5 minutes
- **Data Integrity:** All feeds pass cryptographic verification
- **Confidence Score:** System-wide confidence >0.95

### Settlement Mechanism

In Mode 0, settlement is **100% deterministic** via simulation logs:

```
Settlement(tx) = SHA256(seed_hash + config_hash + actions + timesteps)
```

This provides the following guarantees:

1. **Reproducibility:** Any party can reproduce the outcome from the seed hash and configuration hash
2. **No Subjectivity:** No subjective interpretation is required
3. **Deterministic Outcomes:** Identical inputs always produce identical outputs
4. **Cryptographic Verifiability:** All outcomes can be cryptographically verified

### Mode 0 Validation Chain

```
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚                    MODE 0 SETTLEMENT FLOW                    â”‚
â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
â”‚ 1. Simulation Complete                                       â”‚
â”‚    â””â”€> Generate deterministic log: [timestep, state, action] â”‚
â”‚                                                               â”‚
â”‚ 2. Log Finalization                                          â”‚
â”‚    â””â”€> Compute state_hash = SHA256(complete_log)             â”‚
â”‚                                                               â”‚
â”‚ 3. Settlement Trigger                                        â”‚
â”‚    â””â”€> Verify: seed_hash + config_hash + complete_log        â”‚
â”‚                                                               â”‚
â”‚ 4. Outcome Publication                                       â”‚
â”‚    â””â”€> Publish: settlement_tx with state_hash + signature    â”‚
â”‚                                                               â”‚
â”‚ 5. Verification (Optional)                                   â”‚
â”‚    â””â”€> Any party can recompute: SHA256(seed + config + log)  â”‚
â”‚        â””â”€> Must match published state_hash                    â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

---

## Mode 1: Evidence Oracle (Degraded State)

### Trigger Conditions

Mode 1 activates when one or more feeds are unavailable or degraded, but sufficient evidence remains for settlement:

- **Feed Degradation:** Any single feed category has staleness >5 minutes
- **Partial Coverage:** Remaining feeds provide >50% confidence
- **Evidence Availability:** Sufficient OSINT evidence bundle can be assembled

### Confidence Adjustment Factors

When feeds are unavailable, confidence penalties are applied:

| Feed Category | Unavailable Penalty | Notes |
|--------------|-------------------|-------|
| **Market Data** | -0.15 | Critical for price-based markets |
| **News/Sentiment** | -0.10 | Social proof and narrative tracking |
| **Social** | -0.08 | Community verification |
| **Maritime** | -0.05 | Vessel tracking for shipping markets |
| **Aviation** | -0.05 | Flight tracking for travel markets |
| **On-Chain** | -0.05 | Blockchain activity verification |
| **Browser Automation** | -0.03 | Web scraping verification |

**Formula:** `Adjusted Confidence = Base Confidence Ã— Î (1 - penalty_i)` for each unavailable feed category

### Settlement Mechanism

Mode 1 settlement uses an **OSINT Evidence Bundle** with dispute window:

```
Evidence Bundle = {
  "timestamp": "ISO-8601",
  "available_feeds": [...],
  "missing_feeds": [...],
  "evidence_items": [
    {"source": "...", "content": "...", "hash": "...", "timestamp": "..."}
  ],
  "preliminary_outcome": {...},
  "dispute_deadline": "ISO-8601 (T+24h)"
}
```

### Evidence Bundle Structure

1. **Source Attribution:** Each evidence item includes source URL and hash
2. **Timestamp Validation:** Evidence must be within acceptable time window
3. **Dispute Window:** 24-hour window for challenging evidence validity
4. **Weighted Confidence:** Evidence items contribute to overall confidence

### Mode 1 Validation Chain

```
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚                   MODE 1 SETTLEMENT FLOW                     â”‚
â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
â”‚ 1. Feed Status Check                                         â”‚
â”‚    â””â”€> Identify unavailable/degraded feeds                   â”‚
â”‚    â””â”€> Calculate confidence penalties                        â”‚
â”‚                                                               â”‚
â”‚ 2. Evidence Collection                                       â”‚
â”‚    â””â”€> Gather available OSINT from working feeds             â”‚
â”‚    â””â”€> Assemble evidence bundle with source attribution      â”‚
â”‚                                                               â”‚
â”‚ 3. Preliminary Assessment                                    â”‚
â”‚    â””â”€> Compute preliminary outcome with confidence score     â”‚
â”‚    â””â”€> Generate evidence bundle                              â”‚
â”‚                                                               â”‚
â”‚ 4. Dispute Window                                            â”‚
â”‚    â””â”€> Publish preliminary outcome and evidence              â”‚
â”‚    â””â”€> Allow 24 hours for dispute submissions                â”‚
â”‚                                                               â”‚
â”‚ 5. Resolution                                                â”‚
â”‚    â””â”€> If no disputes: preliminary becomes final             â”‚
â”‚    â””â”€> If disputes: escalate to Mode 2 or resolve via DAO    â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

---

## Mode 2: Conservative Operations (Severe Degradation)

### Trigger Conditions

Mode 2 activates when multiple critical feeds are unavailable or overall confidence drops below threshold:

- **Multiple Failures:** Two or more feed categories unavailable simultaneously
- **Low Confidence:** Overall confidence <0.5 for >60 minutes
- **Critical Feed Loss:** Any critical feed category (Market Data, On-Chain) unavailable

### Restrictions

Mode 2 imposes significant restrictions on market operations:

| Restriction | Details |
|------------|---------|
| **Sabotage Disabled** | All sabotage mechanisms suspended |
| **Position Caps** | Maximum position size reduced by 50% |
| **Bond Requirements** | Collateral requirements doubled (2Ã— standard) |
| **Timeline Creation** | New timeline/fork creation suspended |
| **Fork Markets** | Fork market creation restricted |
| **Trading Hours** | Trading limited to core hours (optional) |

### Settlement Mechanism

Mode 2 settlement requires **manual adjudication** with enhanced safeguards:

```
Adjudication Request = {
  "reason": "Mode 2 triggered",
  "confidence_score": 0.XX,
  "available_evidence": [...],
  "market_identifier": "...",
  "required_approvers": ["DAO_MEMBER_1", "DAO_MEMBER_2", "INDEPENDENT_AUDITOR"]
}
```

### Manual Adjudication Process

1. **Emergency Request:** System generates adjudication request
2. **Approver Selection:** 3-of-5 multisig members selected for this case
3. **Evidence Review:** Approvers review available evidence bundle
4. **Deliberation:** Approvers discuss via secure communication channel
5. **Final Vote:** Each approver submits weighted vote (1-5 scale)
6. **Outcome Determination:** Weighted average of votes determines outcome

### Mode 2 Governance Safeguards

- **Multisig Requirements:** All settlements require 3-of-5 approval
- **Independent Auditor:** Always included in Mode 2 approvals
- **DAO Oversight:** Final outcomes subject to DAO ratification
- **Audit Trail:** Complete deliberation record preserved on-chain

---

## Mode Transition Matrix

The following matrix defines transitions between modes:

```
                    TO MODE 0        TO MODE 1        TO MODE 2
                 â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
FROM MODE 0      â”‚       â€”         â”‚ Feed staleness  â”‚ Multiple feeds  â”‚
                 â”‚                 â”‚ >5min OR        â”‚ failed OR       â”‚
                 â”‚                 â”‚ confidence <0.8 â”‚ confidence <0.5 â”‚
                 â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
FROM MODE 1      â”‚ All feeds fresh â”‚       â€”         â”‚ Confidence      â”‚
                 â”‚ AND confidence  â”‚                 â”‚ <0.5 for 60min  â”‚
                 â”‚ >0.9 for 30min  â”‚                 â”‚                 â”‚
                 â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
FROM MODE 2      â”‚ All feeds fresh â”‚ Confidence      â”‚       â€”         â”‚
                 â”‚ AND confidence  â”‚ >0.6 for 60min  â”‚                 â”‚
                 â”‚ >0.9 for 60min  â”‚                 â”‚                 â”‚
                 â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”´â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”´â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

### Transition Conditions Detail

#### Transitions to Mode 0 (Recovery)

- **From Mode 1 to Mode 0:** All feeds must be fresh for 30 consecutive minutes with confidence >0.9
- **From Mode 2 to Mode 0:** All feeds must be fresh for 60 consecutive minutes with confidence >0.9

#### Transitions to Mode 1 (Partial Degradation)

- **From Mode 0 to Mode 1:** Any feed exceeds 5-minute staleness OR system confidence drops below 0.8
- **From Mode 2 to Mode 1:** System confidence must remain above 0.6 for 60 consecutive minutes

#### Transitions to Mode 2 (Severe Degradation)

- **From Mode 0 to Mode 2:** Multiple feeds fail simultaneously OR confidence drops below 0.5
- **From Mode 1 to Mode 2:** Confidence remains below 0.5 for 60 consecutive minutes

---

## Feed Categories and Sources

### Primary Feeds

| Category | Type | Update Frequency | Criticality |
|----------|------|------------------|-------------|
| **Market Data** | External API | Real-time (<1s) | CRITICAL |
| **On-Chain** | Blockchain RPC | Block-based | CRITICAL |
| **News/Sentiment** | News API | Every 5 min | HIGH |
| **Social** | Social API | Every 5 min | MEDIUM |
| **Browser Automation** | Custom scraper | Every 10 min | MEDIUM |

### Specialized Feeds

| Category | Type | Update Frequency | Criticality |
|----------|------|------------------|-------------|
| **Maritime** | AIS Feed | Every 1 min | LOW (domain-specific) |
| **Aviation** | ADS-B Feed | Real-time | LOW (domain-specific) |
| **Economic** | Economic API | Hourly | MEDIUM (domain-specific) |
| **Weather** | Weather API | Every 15 min | LOW (domain-specific) |

---

## Confidence Calculation

### Base Confidence Formula

```
Base Confidence = Î£(w_i Ã— f_i) / Î£(w_i)
```

Where:
- `w_i` = Weight for feed category i
- `f_i` = Freshness score for feed category i (0-1)
- Sum is over all configured feed categories

### Freshness Score

```
Freshness Score = {
  1.0  if staleness < 1 minute
  0.9  if staleness < 5 minutes
  0.7  if staleness < 15 minutes
  0.5  if staleness < 30 minutes
  0.3  if staleness < 1 hour
  0.1  if staleness > 1 hour
  0.0  if feed completely unavailable
}
```

### Feed Weights

| Feed Category | Weight | Notes |
|--------------|--------|-------|
| Market Data | 1.0 | Primary market signal |
| On-Chain | 1.0 | Verification signal |
| News/Sentiment | 0.7 | Context signal |
| Social | 0.5 | Community signal |
| Browser Automation | 0.5 | Verification signal |
| Maritime | 0.3 | Domain-specific |
| Aviation | 0.3 | Domain-specific |

---

## 10. VRF-Backed Data Validation

### 10.1 Overview

The Oracle system uses **VRF-randomized data validation** to prevent predictable manipulation patterns. Feed validation timing and selection are secured by Chainlink VRF.

### 10.2 VRF Validation Framework

```python
class VRFDataValidation:
    VALIDATION_INTERVAL = 300  # 5 minutes base
    VRF_OFFSET_RANGE = 60  # Â±60 seconds randomization

    def get_validation_time(self, vrf_randomness: uint256) -> uint256:
        """Calculate VRF-randomized validation time"""
        offset = (vrf_randomness % 120) - self.VRF_OFFSET_RANGE
        return block.timestamp + self.VALIDATION_INTERVAL + offset

    def select_feeds(self, vrf_randomness: uint256, all_feeds: List[Feed]) -> List[Feed]:
        """VRF-randomized feed selection"""
        num_to_validate = 3 + (vrf_randomness % 3)  # 3-5 feeds
        # Fisher-Yates shuffle with VRF seed
        indices = list(range(len(all_feeds)))
        for i in range(len(indices)):
            j = i + (vrf_randomness % (len(indices) - i))
            indices[i], indices[j] = indices[j], indices[i]
        return [all_feeds[i] for i in indices[:num_to_validate]]
```

### 10.3 VRF Validation Status

| Feed Category | Sampling Rate | Confidence | VRF Status |
|---------------|---------------|------------|------------|
| Market Data | 100% | 98.2% | âœ“ Verified |
| On-Chain | 100% | 99.1% | âœ“ Verified |
| News/Sentiment | 50% | 94.7% | âœ“ Verified |
| Browser Automation | 50% | 91.3% | âœ“ Verified |
| Maritime (AIS) | 25% | 96.5% | âœ“ Verified |
| Aviation (ADS-B) | 25% | 95.8% | âœ“ Verified |

---

## 11. VRF-Enhanced Circuit Breakers

### 11.1 Overview

Circuit breaker thresholds are **VRF-randomized** to prevent predictable manipulation. Attackers cannot target exact thresholds when they vary per epoch.

### 11.2 Randomization Formula

| Component | Base Value | VRF Range | Current |
|-----------|------------|-----------|---------|
| **Stability Delta** | 10.0% | +0-5% | 12.3% |
| **Paradox Threshold** | 40.0% | +0-10% | 46.7% |
| **Max Position Scaling** | 2.5x | +0-1x | 2.9x |
| **Sabotage Cooldown** | 300s | +0-60s | 342s |

### 11.3 Threshold Calculation

```solidity
function getStabilityDelta(uint256 vrfRandomness) public pure returns (uint256) {
    uint256 vrfComponent = (vrfRandomness % 10000) * 5 / 10000; // 0-5%
    return 1000 + vrfComponent; // 10% + VRF(0-5)%
}
```

---

## Emergency Procedures

### Automatic Triggers

The following conditions trigger automatic mode transitions:

1. **Immediate Mode 2:**
   - Market Data feed unavailable for >10 minutes
   - On-Chain feed unavailable for >10 minutes
   - System detects contradictory evidence from multiple sources

2. **Gradual Mode Transition:**
   - Confidence score degradation over time
   - Multiple feed staleness warnings
   - Evidence quality degradation

### Manual Override

The 3-of-5 multisig can manually trigger mode changes:

- **Upgrade (2/5 required):** Move to higher-confidence mode
- **Downgrade (3/5 required):** Move to lower-confidence mode
- **Emergency (4/5 required):** Immediate mode change outside normal rules

---

## Implementation Checklist

### Mode 0 Implementation

- [ ] Deterministic simulation engine
- [ ] Seed and config hash generation
- [ ] Log integrity verification
- [ ] Settlement transaction signing

### Mode 1 Implementation

- [ ] Feed health monitoring
- [ ] Confidence score calculation
- [ ] Evidence bundle generation
- [ ] Dispute window management
- [ ] Escalation pathways

### Mode 2 Implementation

- [ ] Multisig integration
- [ ] Manual adjudication workflow
- [ ] Deliberation recording
- [ ] DAO ratification process
- [ ] Restriction enforcement

---

## Security Considerations

### Mode 0 Security

- **Hash Collisions:** Use SHA-256 with sufficient entropy in seed
- **Replay Attacks:** Include timestamp in settlement transaction
- **Fork Attacks:** Monitor for blockchain reorganizations
- **VRF Manipulation:** All randomness verified on-chain via Chainlink VRF V2
- **Timing Attacks:** VRF execution windows prevent front-running

### Mode 1 Security

- **Evidence Forgery:** Require cryptographic signatures from sources
- **Dispute Spam:** Bond requirements for dispute submissions
- **Collusion:** Diverse multisig membership requirements

### Mode 2 Security

- **Arbitrary Outcomes:** Require 3-of-5 approval with independent auditor
- **Deliberation Manipulation:** Encrypted communication channels
- **Ratification Failure:** Fallback to community vote if DAO inactive

---

## Appendix: Confidence Score Reference

| Score Range | Status | Mode | Recommended Actions |
|-------------|--------|------|---------------------|
| 0.95-1.00 | Excellent | Mode 0 | Normal operations |
| 0.80-0.94 | Good | Mode 0 | Monitor feeds |
| 0.60-0.79 | Acceptable | Mode 1 | Gather additional evidence |
| 0.50-0.59 | Marginal | Mode 1/2 boundary | Prepare for Mode 2 |
| 0.30-0.49 | Poor | Mode 2 | Activate restrictions |
| 0.00-0.29 | Critical | Mode 2 | Emergency procedures |

---

**Document End**
