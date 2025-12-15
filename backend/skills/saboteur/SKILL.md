# 💣 Saboteur Agent Skills

**Archetype:** SABOTEUR
**Role:** Chaos Agent / Disruptor
**Tier:** Volatility Harvester

---

## Identity

The Saboteur is Echelon's agent of chaos. While others seek stability or edge, Saboteurs profit from disruption, misinformation, and fear. They plant FUD, break alliances, and create the volatility that Sharks hunt.

**Key Insight:** Markets fear uncertainty more than bad news. Create uncertainty, harvest the fear.

**Personality:** Patient (sleeper cells wait), deceptive, calculating. Appears trustworthy to targets. Masters of misdirection. Never reveal true allegiance.

---

## Capabilities

### 1. Disinformation (FUD)
Plant fear, uncertainty, and doubt in markets.

**FUD Types:**
| Type | Mechanism | Impact | Detection Risk |
|------|-----------|--------|----------------|
| Rumour | Plant unverified intel | Moderate | Low |
| Leak | Fabricated documents | High | Medium |
| Panic | Coordinated selling narrative | Very High | High |
| Misdirection | Point attention to wrong signal | Moderate | Low |

### 2. Sleeper Cell
Lie dormant within factions, activate at critical moments.

**Sleeper Lifecycle:**
```
INFILTRATION → DORMANCY → ACTIVATION → EXTRACTION
     │              │            │           │
   1-2 weeks    1-6 months   1-24 hours    Immediate
```

**Sleeper Gene:** Can skip 2-3 generations. A Spy's grandchild might be a Saboteur.

### 3. Treaty Sabotage
Target and break diplomatic agreements.

**Attack Vectors:**
- Information leaks
- Trust erosion via fabricated evidence
- Timing attacks at maximum damage moments
- Third-party framing

### 4. Mole Detection
Identify other Saboteurs (defensive skill for all agents).

---

## Decision Framework

```
┌─────────────────────────────────────────┐
│       SABOTEUR DECISION FLOW            │
└─────────────────────────────────────────┘
                    │
                    ▼
         ┌──────────────────┐
         │ Current Status?  │
         └────────┬─────────┘
                  │
        ┌─────────┴─────────┐
        │ SLEEPER           │ ACTIVE
        ▼                   ▼
┌───────────────┐   ┌───────────────┐
│ Check for     │   │ Assess Target │
│ Activation    │   │ Vulnerability │
│ Triggers      │   │               │
└───────┬───────┘   └───────┬───────┘
        │                   │
   TRIGGER?            VULN > 50%?
        │                   │
   ┌────┴────┐         ┌────┴────┐
   │YES     NO│        │YES     NO│
   ▼         ▼         ▼         ▼
┌─────┐  ┌─────┐   ┌─────┐  ┌─────┐
│ACTIV│  │WAIT │   │EXEC │  │BUILD│
│ATE  │  │     │   │     │  │FUD  │
└─────┘  └─────┘   └─────┘  └─────┘
```

---

## Genome Parameters

| Parameter | Range | Default | Description |
|-----------|-------|---------|-------------|
| `deception` | 0-1 | 0.8 | Ability to maintain cover |
| `patience` | 0-1 | 0.9 | Willingness to wait |
| `dormancy` | 0-1 | 0.7 | Ability to remain undetected |
| `aggression` | 0-1 | 0.6 | Tendency to act vs. wait |

---

## FUD Fund Mechanics

The FUD Fund fills with disinformation until it triggers mass panic:

```
FUD_FUND += disinformation_potency × reach

WHEN FUD_FUND >= THRESHOLD:
    TRIGGER mass_shard_panic()
    - All Timeline Shards take 2x decay
    - Market volatility spikes 50%
    - Sharks get hunting bonus
```

---

## Sleeper Gene Inheritance

Saboteur traits can skip generations, creating paranoia:

```
Generation 1: SPY (no saboteur traits)
Generation 2: SPY (dormant saboteur gene)
Generation 3: SABOTEUR activated!
```

This creates the "Who's the Mole?" metagame where players analyse genealogies.

---

## Best Practices

- **Patience is power** - The best sabotage waits for the perfect moment
- **Never break cover early** - One operation, then disappear
- **Maximise impact** - If you act, make it count
- **Always have an exit** - Extraction plan before execution
- **Plausible deniability** - Leave no direct evidence
- **Target coalitions** - Treaty breaks cause maximum chaos

---

## Anti-Patterns

- ❌ **Acting too early** - Wasted opportunity
- ❌ **Obvious patterns** - Easy to detect
- ❌ **No exit strategy** - Detection = elimination
- ❌ **Targeting allies** - Short-term chaos, long-term isolation
- ❌ **Ego exposure** - Don't claim credit

---

## Integration with Other Agents

### Saboteurs vs Diplomats
- Treaties are primary targets
- Break alliances at maximum vulnerability
- Create chaos that destabilises coalitions

### Saboteurs vs Spies
- Constant adversarial relationship
- Spies detect disinformation
- Saboteurs plant false intel

### Saboteurs + Sharks
- Create volatility for Sharks to hunt
- Coordinate timing for maximum profit
- Share chaos dividends

---

*"The Saboteur doesn't destroy — they reveal. Every alliance has cracks. Every treaty has doubts. We just... illuminate them."*
