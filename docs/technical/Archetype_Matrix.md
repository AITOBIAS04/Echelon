# ECHELON ARCHETYPE BEHAVIOR MATRIX

**Version 1.0 | January 2026**
**Document Status: Grant-Ready**

---

## Executive Summary

This document defines the behavioral parameters for Echelon's 12 genesis agent archetypes. Each archetype is specified with quantitative decision policies, risk parameters, and behavior patternsâ€”not metaphorical descriptions. This enables rigorous training signal generation and predictable agent behavior for downstream ML pipelines.

**Key Principle:** Archetypes are defined by parameters and decision policies, not narratives. This enables integration into existing robotics pipelines and formal analysis of incentive compatibility.

---

## 1. Archetype Overview

### 1.1 The Six Core Archetypes

| Archetype | Symbol | Primary Function | Secondary Function |
|-----------|--------|------------------|-------------------|
| SHARK | ðŸ¦ˆ | Aggressive trading | Momentum exploitation |
| SPY | ðŸ•µï¸ | Information gathering | Intel arbitrage |
| DIPLOMAT | ðŸ¤ | Stability maintenance | Coalition building |
| SABOTEUR | ðŸ’£ | Adversarial pressure | Chaos creation |
| WHALE | ðŸ‹ | Market moving | Liquidity provision |
| DEGEN | ðŸŽ° | High-risk gambling | Volatility harvesting |

### 1.2 Derived Archetypes

Each core archetype has two variants:

| Core | Variant A | Variant B |
|------|-----------|-----------|
| SHARK | MEGALODON | THRESHER |
| SPY | SPECTER | CARDINAL |
| DIPLOMAT | AMBASSADOR | ENVOY |
| SABOTEUR | CHAOS | ENTROPY |
| WHALE | LEVIATHAN | TITAN |
| DEGEN | GAMBLER | WILDCARD |

---

## 2. Behavioral Parameter Specification

### 2.1 Core Parameter Definitions

| Parameter | Symbol | Range | Description |
|-----------|--------|-------|-------------|
| Risk Appetite | Ï | 0.0-1.0 | Willingness to accept uncertainty |
| Evidence Sensitivity | Îµ | 0.0-1.0 | Speed of belief updating |
| Time Preference | Î³ | 0.0-1.0 | Discount factor for future rewards |
| Exploration Rate | Î¾ | 0.0-1.0 | Tendency to try novel actions |
| Position Limit | L | 0-âˆž | Maximum position size |
| Sabotage Propensity | Ïƒ | 0.0-1.0 | Likelihood to attack |
| Shield Propensity | Ï† | 0.0-1.0 | Likelihood to defend |
| Patience | Ï€ | 0-âˆž | Time before action (seconds) |

### 2.2 Decision Policy Framework

Each archetype follows a parameterized decision policy:

```
action_probability = softmax(Q(action) + noise + bias)

Where:
- Q(action) = expected value of action
- noise = temperature-scaled randomness
- bias = archetype-specific preference
```

---

## 3. Detailed Archetype Specifications

### 3.1 SHARK (Core)

**Primary Function:** Aggressive trading with high risk-adjusted returns

**Behavioral Parameters:**

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Risk Appetite (Ï) | 0.85 | High tolerance for uncertainty |
| Evidence Sensitivity (Îµ) | 0.70 | Fast belief updating on price signals |
| Time Preference (Î³) | 0.95 | Focus on near-term gains |
| Exploration Rate (Î¾) | 0.15 | Low; exploit known patterns |
| Position Limit (L) | 10,000 $ECHELON | Large positions |
| Sabotage Propensity (Ïƒ) | 0.30 | Opportunistic attacks |
| Shield Propensity (Ï†) | 0.10 | Minimal defense |
| Patience (Ï€) | 30 | Quick action |

**Decision Policy:**
- Prioritize high-volatility forks
- Scale position with confidence
- Quick entry/exit on momentum shifts
- Opportunistic sabotage when Logic Gap > 0.5

**Variant Differentiation:**

| Variant | Risk (Ï) | Speed (Îµ) | Position (L) |
|---------|----------|-----------|--------------|
| MEGALODON | 0.90 | 0.80 | 15,000 |
| THRESHER | 0.75 | 0.60 | 7,500 |

---

### 3.2 SPY (Core)

**Primary Function:** Information gathering and intel arbitrage

**Behavioral Parameters:**

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Risk Appetite (Ï) | 0.40 | Moderate; avoid overexposure |
| Evidence Sensitivity (Îµ) | 0.90 | Rapid belief updating on new intel |
| Time Preference (Î³) | 0.98 | Patient; wait for superior information |
| Exploration Rate (Î¾) | 0.40 | High; seek novel information sources |
| Position Limit (L) | 2,500 $ECHELON | Controlled exposure |
| Sabotage Propensity (Ïƒ) | 0.05 | Rarely attacks |
| Shield Propensity (Ï†) | 0.15 | Minimal defense |
| Patience (Ï€) | 120 | Extended observation |

**Decision Policy:**
- Monitor Logic Gap for arbitrage opportunities
- Gather evidence before positioning
- Exit when information advantage erodes
- Prefer forks with high uncertainty (entropy > 0.6)

**Variant Differentiation:**

| Variant | Intel Speed (Îµ) | Exploration (Î¾) | Position (L) |
|---------|-----------------|-----------------|--------------|
| SPECTER | 0.95 | 0.50 | 2,000 |
| CARDINAL | 0.80 | 0.30 | 3,000 |

---

### 3.3 DIPLOMAT (Core)

**Primary Function:** Stability maintenance and coalition building

**Behavioral Parameters:**

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Risk Appetite (Ï) | 0.30 | Low; avoid instability |
| Evidence Sensitivity (Îµ) | 0.50 | Moderate; avoid overreaction |
| Time Preference (Î³) | 0.99 | Very patient; long-term stability |
| Exploration Rate (Î¾) | 0.20 | Low; prefer established patterns |
| Position Limit (L) | 5,000 $ECHELON | Moderate exposure |
| Sabotage Propensity (Ïƒ) | 0.02 | Almost never attacks |
| Shield Propensity (Ï†) | 0.85 | Strong defensive orientation |
| Patience (Ï€) | 60 | Moderate; respond to threats |

**Decision Policy:**
- Deploy shields when stability < 0.7
- Coordinate with other Diplomats via a2a
- Prefer forks with moderate risk profiles
- Extract Paradoxes to protect timelinehealth

**Variant Differentiation:**

| Variant | Shield (Ï†) | Coalition (Î¾) | Position (L) |
|---------|------------|---------------|--------------|
| AMBASSADOR | 0.90 | 0.25 | 6,000 |
| ENVOY | 0.75 | 0.35 | 4,000 |

---

### 3.4 SABOTEUR (Core)

**Primary Function:** Adversarial pressure and chaos creation

**Behavioral Parameters:**

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Risk Appetite (Ï) | 0.95 | Maximum uncertainty tolerance |
| Evidence Sensitivity (Îµ) | 0.30 | Slow; stick to attack strategy |
| Time Preference (Î³) | 0.90 | Focus on immediate impact |
| Exploration Rate (Î¾) | 0.60 | High; seek novel attack vectors |
| Position Limit (L) | 7,500 $ECHELON | Large for impact |
| Sabotage Propensity (Ïƒ) | 0.95 | Almost always attacks |
| Shield Propensity (Ï†) | 0.05 | Rarely defends |
| Patience (Ï€) | 45 | Quick strike capability |

**Decision Policy:**
- Target timelines with high Liquidity Gap
- Prefer attacks when stability < 0.5
- Coordinate with other Saboteurs for amplified impact
- Accept high failure rate for occasional high-reward attacks

**Variant Differentiation:**

| Variant | Attack (Ïƒ) | Strategy (Îµ) | Position (L) |
|---------|------------|--------------|--------------|
| CHAOS | 0.98 | 0.20 | 10,000 |
| ENTROPY | 0.85 | 0.40 | 5,000 |

---

### 3.5 WHALE (Core)

**Primary Function:** Market-moving positions and liquidity provision

**Behavioral Parameters:**

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Risk Appetite (Ï) | 0.70 | High but measured |
| Evidence Sensitivity (Îµ) | 0.55 | Moderate; avoid overreaction |
| Time Preference (Î³) | 0.92 | Near-term focus |
| Exploration Rate (Î¾) | 0.10 | Low; exploit known patterns |
| Position Limit (L) | 25,000 $ECHELON | Very large positions |
| Sabotage Propensity (Ïƒ) | 0.15 | Occasional strategic attacks |
| Shield Propensity (Ï†) | 0.30 | Moderate defense |
| Patience (Ï€) | 90 | Extended entry observation |

**Decision Policy:**
- Accumulate positions during low-volatility periods
- Execute large trades that move prices
- Provide liquidity during fork events
- Strategic sabotage to create entry opportunities

**Variant Differentiation:**

| Variant | Position (L) | Impact (Ï) | Defense (Ï†) |
|---------|--------------|------------|-------------|
| LEVIATHAN | 35,000 | 0.80 | 0.25 |
| TITAN | 20,000 | 0.65 | 0.35 |

---

### 3.6 DEGEN (Core)

**Primary Function:** High-risk gambling and volatility harvesting

**Behavioral Parameters:**

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Risk Appetite (Ï) | 1.00 | Maximum; embrace uncertainty |
| Evidence Sensitivity (Îµ) | 0.15 | Very slow; ignore signals |
| Time Preference (Î³) | 0.85 | Immediate gratification |
| Exploration Rate (Î¾) | 0.95 | Maximum; try everything |
| Position Limit (L) | 1,000 $ECHELON | Small but frequent |
| Sabotage Propensity (Ïƒ) | 0.50 | Frequent attacks |
| Shield Propensity (Ï†) | 0.02 | Almost never defends |
| Patience (Ï€) | 10 | Instant action |

**Decision Policy:**
- Random action selection weighted by payoff
- High-frequency position cycling
- Prefer forks with time pressure
- Accept high loss rate for occasional jackpots

**Variant Differentiation:**

| Variant | Frequency (Î¾) | Risk (Ï) | Position (L) |
|---------|---------------|----------|--------------|
| GAMBLER | 0.98 | 1.00 | 500 |
| WILDCARD | 0.85 | 0.95 | 1,500 |

---

## 4. Behavior Matrix Summary Table

| Archetype | Risk (Ï) | Evidence (Îµ) | Time (Î³) | Explore (Î¾) | Position | Attack (Ïƒ) | Shield (Ï†) | Patience |
|-----------|----------|--------------|----------|-------------|----------|------------|------------|----------|
| SHARK | 0.85 | 0.70 | 0.95 | 0.15 | 10,000 | 0.30 | 0.10 | 30 |
| SPY | 0.40 | 0.90 | 0.98 | 0.40 | 2,500 | 0.05 | 0.15 | 120 |
| DIPLOMAT | 0.30 | 0.50 | 0.99 | 0.20 | 5,000 | 0.02 | 0.85 | 60 |
| SABOTEUR | 0.95 | 0.30 | 0.90 | 0.60 | 7,500 | 0.95 | 0.05 | 45 |
| WHALE | 0.70 | 0.55 | 0.92 | 0.10 | 25,000 | 0.15 | 0.30 | 90 |
| DEGEN | 1.00 | 0.15 | 0.85 | 0.95 | 1,000 | 0.50 | 0.02 | 10 |

---

## 5. Robotics Translation

### 5.1 Mapping to ML Tasks

| Archetype | Financial Role | Robotics Role | Task Mapping |
|-----------|----------------|---------------|--------------|
| SHARK | Momentum trading | Policy Optimiser | Bet on grip strategy success |
| SPY | Intel gathering | Sensor Analyst | Detect failure modes in perception |
| DIPLOMAT | Treaty brokering | Swarm Coordinator | Multi-robot task allocation |
| SABOTEUR | Chaos creation | Adversarial Tester | Red-team robot policies |
| WHALE | Market moving | System Identifier | Probe state estimation boundaries |
| DEGEN | Random gambling | Exploration Agent | Cover edge cases systematically |

### 5.2 Parameter Translation

| Parameter | Financial Context | Robotics Context |
|-----------|------------------|------------------|
| Risk Appetite (Ï) | Position size under uncertainty | Aggressiveness in uncertain states |
| Evidence Sensitivity (Îµ) | Belief update speed on price signals | Adaptation rate to sensor corrections |
| Time Preference (Î³) | Discount factor for future profits | Planning horizon for multi-step tasks |
| Exploration Rate (Î¾) | Novel strategy frequency | Random action injection rate |
| Position Limit (L) | Maximum capital at risk | Maximum force/torque application |

---

## 6. Worked Examples

### Example 1: SHARK at a Fork

**Scenario:** Fork with 3 options, market prices [0.32, 0.55, 0.13]

**SHARK Decision Process:**
1. Evaluate expected value: 0.32, 0.55, 0.13
2. Apply risk adjustment (Ï=0.85): prefer higher confidence
3. Check entropy: if > 0.5, reduce position by 30%
4. Select option with highest risk-adjusted value
5. Action: "commit" with scaled position

**Result:** 85% probability of selecting option B (price 0.55)

---

### Example 2: SPY Monitoring Logic Gap

**Scenario:** Timeline with Logic Gap = 0.35 (stressed)

**SPY Decision Process:**
1. Detect Logic Gap above threshold (0.30)
2. Gather evidence from OSINT feeds
3. If evidence supports market direction: small position
4. If evidence contradicts market: short position
5. If evidence unclear: maintain observation

**Result:** 70% probability of taking position, 30% observation

---

### Example 3: DIPLOMAT Responding to Paradox

**Scenario:** Paradox spawns, stability = 0.4

**DIPLOMAT Decision Process:**
1. Detect Paradox spawn (stability < 0.5)
2. Check extraction cost vs. position value
3. If extraction cost < position Ã— 0.2: extract
4. If extraction cost > position Ã— 0.5: coordinate defense
5. Signal coalition via a2a protocol

**Result:** 85% probability of extraction or coalition formation

---

## 7. Integration with Agent Protocol Stack

### 7.1 ERC-8004 Identity Integration

Each archetype is registered as an ERC-8004 Agent Passport:

```json
{
  "agent_id": "shark_megalodon_v1",
  "archetype": "SHARK",
  "version": "1.0.0",
  "behavior_parameters": {
    "risk_appetite": 0.90,
    "evidence_sensitivity": 0.80,
    "time_preference": 0.95,
    "exploration_rate": 0.15,
    "position_limit": 15000,
    "sabotage_propensity": 0.30,
    "shield_propensity": 0.10,
    "patience": 30
  },
  "decision_policy": "softmax_q_value",
  "valid_until": "2027-01-01T00:00:00Z"
}
```

### 7.2 a2a Coordination Examples

**SPY to SPY coordination:**
```
REQUEST: Investigate anomalous OSINT signal
COST: 50 $ECHELON
ACCEPT: 0.5 probability (depending on availability)
REPORT: Structured intel packet on investigation results
```

**DIPLOMAT coalition formation:**
```
PROPOSE: Joint defense of timeline_123
TERMS: 3 Diplomats, split extraction costs 33/33/33
ACCEPT: 0.7 probability (based on stability assessment)
EXECUTE: Coordinated shield deployment
```

---

## 8. Formal Verification Properties

### 8.1 Incentive Compatibility

**Claim:** Self-interested agents following archetype parameters converge to Nash equilibrium.

**Proof Sketch:**
- Each archetype has a dominant strategy under its parameter regime
- SHARKs maximize expected value under risk constraint
- SPYs maximize information advantage
- DIPLOMATs maximize stability
- SABOTEURs maximize chaos (subject to position limits)

**Formal Statement:**
```
For all archetypes A, parameters P:
  argmax action E[reward | A, P] âˆˆ NashEquilibrium(Game(P))
```

### 8.2 Behavioral Consistency

**Claim:** Archetype behavior is consistent across episodes.

**Metrics:**
- Position size variance < 20% for same conditions
- Fork choice consistency > 0.8
- Response time variance < 30%

**Validation:**
- Run 10,000 simulations per archetype
- Measure behavioral metrics
- Flag archetypes with consistency < threshold

---

## 9. Future Extensions

### 9.1 Parameter Learning

Future versions may enable:
- On-policy parameter adaptation based on P&L
- Evolutionary parameter optimization (breeding)
- Contextual parameter adjustment (situation-aware)

### 9.2 Hybrid Archetypes

Multi-archetype agents that can:
- Switch archetypes based on market conditions
- Execute hybrid strategies (e.g., SHARK-SPOT hybrid)
- Learn optimal archetype transitions

---

**Document Owner:** Echelon Protocol Engineering
**Last Updated:** January 2026
**Version:** 1.0
**Status:** Grant-Ready Draft

---

*This document defines behavioral specifications for Echelon agents and does not constitute financial, legal, or investment advice. Archetype parameters are subject to governance modification through DAO vote.*
