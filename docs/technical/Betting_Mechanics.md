# Echelon Theatre Betting Mechanics

## The Core Question: What Are You Betting On?

In Echelon's Theatre of Primitives, users can bet at **three distinct levels**:

### Level 1: End-Result Markets (Macro)

**What you're betting on:**
- **Mission Success**: Will the agent complete the objective?
- **Final Score**: Will the score vector exceed threshold (e.g., >70/100)?
- **Paradox Spawn**: Will a paradox event occur during the mission?
- **Component Scores**: Time efficiency, safety, mission value, trace quality

**Resolution:** At mission end (epoch 250 in our example)

**Example:** 
- "Mission will succeed" â€” Pays if agent completes objective
- "Final score > 70" â€” Pays based on weighted score vector
- "No paradox spawns" â€” Pays if logic gap never exceeds threshold

---

### Level 2: Fork Outcome Markets (Meso)

**What you're betting on:**
- **Agent Decision**: Which option will the agent choose at each fork point?
- **Decision Style**: Will agent choose RISKY or CONSERVATIVE approach?
- **Stability Impact**: How will the choice affect timeline stability?

**Resolution:** When agent makes the decision (within fork deadline)

**Example:**
- "Agent chooses Option B: Cut and grab immediately"
- "Agent takes conservative path (Option A or C)"
- "Decision made before deadline vs timeout"

**Fork Point Structure:**
```
Fork Point #7 â€” Decision Required
â”œâ”€â”€ Option A: Stabilize rotation & secure (Risk: Medium, Time: 30s)
â”œâ”€â”€ Option B: Cut and grab immediately (Risk: High, Time: 12s)  
â””â”€â”€ Option C: Wait for docking window (Risk: Low, Time: 120s)
```

---

### Level 3: Interval/Checkpoint Markets (Micro)

**What you're betting on:**
- **System State**: What will metrics be at specific epochs?
- **Event Trigger**: Will saboteur/paradox events happen before checkpoint?
- **Metric Thresholds**: Will stability, logic gap, entropy hit certain values?

**Resolution:** At the specified epoch or time interval

**Example:**
- "Stability > 60% at epoch 200"
- "Saboteur event triggers before epoch 220"
- "Logic gap remains < 30% at next checkpoint"

---

## Checkpoint vs End-Result: The Key Difference

### End-Result Betting

**Characteristics:**
- Long-term position
- Set at mission start
- High liquidity, broader market
- "Will this mission succeed?"

**Pros:**
- Simpler to understand
- Lower monitoring requirement
- Better for retail users

**Cons:**
- Less tactical flexibility
- Cannot react to mid-mission events
- Less precise hedging

### Checkpoint Betting

**Characteristics:**
- Short-term position
- Set at any time before checkpoint
- Real-time, dynamic odds
- "What will stability be at epoch X?"

**Pros:**
- Tactical flexibility
- React to saboteur events
- Precise hedging of positions

**Cons:**
- More complex
- Requires active monitoring
- Lower liquidity per market

---

## The Betting Timeline

```
MISSION: Orbital Salvage Echelon
EPOCHS: 180 â†’ 250 (70 epochs, ~7 minutes real-time)

â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚ EPOCH 180 â€” MISSION START                                            â”‚
â”‚ Betting: Mission Success, Paradox Spawn, Final Score                 â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                              â†“
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚ EPOCH 184 â€” FORK POINT #7                                            â”‚
â”‚ Betting: Which option? Agent decision style? Stability impact?       â”‚
â”‚ Options: Stabilize vs Cut-Grab vs Wait                               â”‚
â”‚ Decision Deadline: 45 seconds                                        â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                              â†“
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚ EPOCH 200 â€” CHECKPOINT ALPHA                                          â”‚
â”‚ Betting: Stability > 60%? Logic gap < 30%? Saboteur event?           â”‚
â”‚ Real-time settlement of interval markets                             â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                              â†“
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚ EPOCH 215 â€” FORK POINT #12                                            â”‚
â”‚ Betting: Approach vs Abort vs Re-route                               â”‚
â”‚ Second major decision point                                           â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                              â†“
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚ EPOCH 230 â€” PARADOX EVENT (Conditional)                              â”‚
â”‚ Betting: Extraction success? Detonation? Natural resolution?         â”‚
â”‚ Only if paradox spawns (Logic Gap > 60% OR Stability < 10%)          â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                              â†“
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚ EPOCH 250 â€” MISSION END                                              â”‚
â”‚ Settlement: All end-result markets resolve                           â”‚
â”‚ Final score calculated, P&L distributed                              â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

---

## Example Betting Scenario

### User's Position at Mission Start:

| Bet Type | Position | Amount | Odds | Outcome |
|----------|----------|--------|------|---------|
| Mission Success | $100 | $100 | $1.85 | Pays $185 if succeeds |
| Paradox Spawn | $20 | $20 | $0.15 | Pays $3 if paradox |
| Final Score > 70 | $50 | $50 | $2.10 | Pays $105 if score > 70 |

### Mid-Mission (Epoch 200):

User sees stability dropped to 52%. They can:

1. **Hedge end-result bet:** Buy more "Mission Success" at worse odds
2. **Open interval bet:** "Stability < 60% at epoch 200" (already true!)
3. **Speculate on outcome:** "Saboteur event in next 20 epochs"

### After Fork Point #7:

Agent chose Option B (risky cut-grab). User can:

1. **Open fork bet:** "Agent chose risky option" (if they predicted this)
2. **Speculate on stability:** "Stability will drop >10% next epoch"
3. **Adjust end-result:** Buy more "Mission Success" or "Final Score"

---

## Strategic Betting Combinations

### Conservative Strategy (Low Risk, Lower Return)
- Heavy weight on end-result markets
- Small positions on interval markets
- Goal: Steady returns, low variance

### Tactical Strategy (Medium Risk, Dynamic)
- Mix of fork and interval betting
- React to agent decisions and events
- Goal: Exploit information advantage

### Aggressive Strategy (High Risk, High Variance)
- Heavy on paradox and saboteur markets
- Speculate on volatility
- Goal: Maximum returns during chaos

### Signal-Based Strategy (Information-Driven)
- Use agent behavior to predict outcomes
- Bet on fork decisions before they're made
- Goal: Alpha from understanding agent logic

---

## Summary

**Yes, there are checkpoints!** Echelon offers:

1. **Interval/Checkpoint Markets** â€” Bet on system state at specific epochs
2. **Fork Outcome Markets** â€” Bet on agent decisions at decision points  
3. **End-Result Markets** â€” Bet on final mission outcome

Users can mix and match across all three levels for:
- **Hedging**: Protect end-result position with interval bets
- **Speculation**: Exploit short-term opportunities
- **Information Trading**: Bet on agent behavior and system state

The key innovation is that **all three levels trade simultaneously**, allowing users to express complex views and dynamically adjust their exposure throughout the mission.
