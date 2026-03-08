# Engine Spec Sections Readout

## /Users/tobiasharber/Developer/prediction-market-monorepo.nosync/grimoires/loa/context/Echelon_System_Bible_v13.md (Integrity Mechanisms section)
```markdown

**4.4 Automatic Settlement**

Settlement is triggered mechanically by the resolution state machine. When the pre-committed resolution mechanism produces a final outcome, the market contract accepts the outcome if verification rules are satisfied, and settlement is automatically enabled. No multisig approval, no admin transaction, no discretionary delay. Resolution implies settlement.

This property is enforced by the market lifecycle contract: once deployed, the market runs from trading through resolution through settlement without human intervention. The only inputs are committed data and verified computation.

**V. Integrity Mechanisms**

**5.1 The Butterfly Engine (Causal State Transitions)**

Every significant action in an Echelon Theatre is recorded as a Wing Flap: an atomic causal event that modifies simulation state. Unlike traditional prediction markets where trades merely express beliefs, Echelon trades are causal interventions that change the system being predicted.

| **Flap Type** | **Trigger**                  | **Stability Impact** | **Committed Rule**                                   |
|---------------|------------------------------|----------------------|------------------------------------------------------|
| TRADE         | Position exceeds threshold   | ±0.1% to ±5%         | Impact formula committed at Theatre creation         |
| SHIELD        | Diplomat protection action   | +2% to +10%          | Shield cost and effect committed per difficulty tier |
| SABOTAGE      | Adversarial attack execution | -5% to -15%          | Damage range committed; VRF determines exact value   |
| RIPPLE        | Cascade from linked timeline | ±1% to ±3%           | Cross-timeline coupling constants committed          |
| PARADOX       | Containment breach event     | -10% to -30%         | Severity thresholds committed at Theatre creation    |
| ENTROPY       | Natural decay (time-based)   | -1% baseline         | Decay rate committed per difficulty tier             |

**Founder's Yield:** When an agent's Wing Flap creates sufficient divergence to spawn a new Timeline Fork, that agent becomes the Founder. Yield = timeline.stability × timeline.volume × 0.005. This aligns founder incentives with timeline health: high stability produces more yield; Paradoxes destroy this income stream.

**5.2 The Entropy Engine (Temporal Decay)**

The Entropy Engine ensures timelines do not persist indefinitely. It forces velocity of capital: participants must act or their positions decay. The central metric is the Logic Gap: the divergence between market-implied probabilities and committed OSINT reality signals.

| **Logic Gap** | **Status** | **Effect**                                             |
|---------------|------------|--------------------------------------------------------|
| \< 20%        | Healthy    | Normal operation; standard entropy decay               |
| 20-40%        | Stressed   | Elevated decay rate; increased monitoring              |
| 40-60%        | Brittle    | Paradox spawn risk; circuit breakers may activate      |
| \> 60%        | Critical   | Paradox spawns immediately; emergency protocols engage |

**The Simulation Heartbeat**

| **Task** | **Interval** | **Function**                                   |
|----------|--------------|------------------------------------------------|
| ENTROPY  | 60 seconds   | Decay all timeline stability scores            |
| PARADOX  | 30 seconds   | Scan for integrity breach conditions           |
| MARKET   | 10 seconds   | Synchronise prices from committed oracle feeds |
| AGENT    | 5 seconds    | Process autonomous agent decisions             |

**5.3 The Paradox Engine (Self-Policing Integrity)**

A Paradox is an integrity mechanism that activates when the divergence between market consensus and committed reality signals exceeds pre-defined thresholds. It functions as the system's immune response: when the market lies too aggressively relative to observable evidence, the Paradox imposes escalating costs that force participants to either correct the divergence or accept losses.

**Spawn Conditions (Committed at Theatre Creation)**

| **Trigger**          | **Threshold** | **Severity Classification** |
|----------------------|---------------|-----------------------------|
| Logic Gap exceedance | \> 40%        | CLASS_3_MODERATE            |
| Logic Gap exceedance | \> 50%        | CLASS_2_SEVERE              |
| Logic Gap exceedance | \> 60%        | CLASS_1_CRITICAL            |
| Stability breach     | \< 30%        | CLASS_3_MODERATE            |
| Stability breach     | \< 20%        | CLASS_2_SEVERE              |
| Stability breach     | \< 10%        | CLASS_1_CRITICAL            |

**The Paradox Lifecycle**

**Stage 1 — Spawn:** Paradox entity appears in the timeline. Countdown timer starts (2-24 hours based on committed severity parameters). Timeline decay accelerates to 10%/hour. All spawn conditions are deterministic given committed inputs and verifiable by replay.

**Stage 2 — Extraction Decision:** Any agent can initiate extraction. Cost: USDC + \$ECHELON + Sanity. Agent becomes Carrier. Extraction costs are committed at Theatre creation and verifiable.

**Stage 3 — Carrier Burden:** Carrier loses Sanity per minute. Can pass to another agent (fee required). Each pass shortens timer: 100% → 85% → 70%. Timer reduction schedule committed at Theatre creation.

**Stage 4 — Resolution:** Three terminal states, each deterministic: Timer expires (detonation: pre-committed terminal state activates, positions burn, carrier agent may die). Logic Gap closes (natural resolution: OSINT realigns, Paradox dissolves, carrier rewarded). Extraction complete (heroic save: carrier pays full cost, timeline stabilised, reputation boost).

**VI. Commitment Protocol (Immutable Market Lifecycle)**

**6.1 Principle**

If critical terms can change after positions are established, market prices are no longer clean forecasts; they are entangled with governance risk, admin risk, and meta-speculation about platform behaviour. Echelon commits everything at market creation. Nothing changes after capital arrives.

**6.2 Commitment Hash**

At Theatre instantiation, the following parameters are published as an immutable commitment hash on-chain:

| **Parameter**        | **What Is Committed**                                          | **Verification**                                    |
|----------------------|----------------------------------------------------------------|-----------------------------------------------------|
| Scenario Pack        | Theatre template, objective vector, fork schema, saboteur deck | Hash of JSON template published before trading      |
| OSINT Data Sources   | Provider endpoints, polling frequency, confidence weights      | Source registry committed and version-locked        |
| VRF Configuration    | Provider (Chainlink/Switchboard), seed parameters, usage rules | VRF contract address and parameters on-chain        |
| Market Parameters    | LMSR liquidity parameter b, fee schedule, duration             | Escrowed capital verifiable on-chain                |
| Paradox Thresholds   | Logic Gap triggers, stability triggers, severity classes       | Committed in Theatre Template JSON                  |
| Resolution Mechanism | Oracle escalation ladder, dispute rules, timeout conditions    | State machine specification hashed and published    |
| Sabotage Rules       | Commit-reveal delays, position-scaled pricing formula, staking | Smart contract parameters immutable post-deployment |
| Version Pins         | Exact commit hash for every construct and scorer in the resolution programme | Hash of version_pins object included in commitment hash |
| Dataset Hashes       | SHA-256 of every ground truth dataset referenced by the template | Hash of dataset_hashes object included in commitment hash |

The commitment hash is computed over the full canonicalised template JSON plus version pins and dataset hashes using canonical JSON rules (see §II.5). For Product Theatres, no capital is escrowed and sabotage rules do not apply; the commitment ensures parameter immutability and replay reproducibility. The invariant after commitment: no parameter changes are permitted. The resolution programme may include pre-committed human-in-the-loop steps, but the process, rubric, and identity rules for those steps are themselves committed.

**6.3 Immutable Lifecycle**

Once deployed, the market lifecycle proceeds without human intervention:

1\. Trading opens. Agents and participants trade against the LMSR cost function at committed prices.

2\. Fork points activate when committed trigger conditions are met. Options, deadlines, and state transitions execute as specified.

```

## /Users/tobiasharber/Developer/prediction-market-monorepo.nosync/grimoires/loa/context/Echelon_System_Bible_v13_Addendum.md (Paradox Policy Extension note)
```markdown
| `tests/test_architectural_concerns.py` | 27 new + 2 updated tests |

---

## 5. Upcoming: Cycle-005 (Intelligence Database Expansion)

Registry expansion from 77 → 160+ sources. 9 new schema fields, 17 new source group enums, settlement guardrails enforced by hardened validator. Sprint plan ready. Depends on Cycle-004 completion (done).

---

## 6. Upcoming: Paradox Policy Extension

A `paradox_policy` object is proposed for the Theatre Template v-next to make the Paradox Engine inquiry-aware. Four modes (`disabled`, `enabled`, `advisory`, `circuit_breaker`), three logic gap sources (`simulation`, `osint`, `survey`), configurable thresholds, and an `activation_gate` that prevents premature Paradox firing in investigative and survey Theatres. See design note: `Echelon_Paradox_Policy_Design_Note_v1.md`. Implementation is post-Phase 3 (LMSR Market Engine).
```

## /Users/tobiasharber/Developer/prediction-market-monorepo.nosync/grimoires/loa/context/Echelon_Butterfly_Entropy_Coherence_Review_v1.md
```markdown
# Echelon Butterfly & Entropy Engine Coherence Review v1

> Design Note — Butterfly Engine, Entropy Engine, and Game Loop alignment with the Mirror/Fork architecture and Investigation Toolset.
> UK British English throughout.
> **Version:** 1.0.0
> **Date:** 5 March 2026
> **Depends on:** Cycle-010b (engines + heartbeat), Cycle-014c (investigation toolset), Cycle-016 (results surface), Polymarket integration

---

## 1. Purpose

The Butterfly and Entropy engines were built in Cycle-010b against a simulation-first mental model: agents trade in LMSR markets, wing flaps record stability impacts, entropy decays timelines, and the Paradox Engine self-polices. Since then, three architectural shifts have made the current engine implementations incoherent with the platform's direction:

1. **Mirror/Fork model** — Polymarket is the anchor reality. Echelon timelines are forks. The engines must distinguish between anchor price sync events and agent-driven fork divergence.
2. **Investigation Toolset (014c)** — Evidence envelopes, claim graphs, corroboration checking, and stop conditions produce events that have no representation in the current WingFlap taxonomy.
3. **Multi-timeline game loop** — MarketSyncTask auto-discovers up to 20 Polymarket markets. The game loop's per-tick cadence was designed for a single-market simulation, not a portfolio of mirrored timelines with per-Theatre Paradox policies.

This design note catalogues every coherence gap, proposes amendments, and defines acceptance criteria so a single remediation pass (during 016 Sprint 1 Contract Alignment) can close them all.

---

## 2. Current State Audit

### 2.1 Three Parallel Implementations (Problem #0)

The codebase contains three partly-overlapping Butterfly/Entropy implementations:

| Location | Style | Used By | DB-Wired? |
|----------|-------|---------|-----------|
| `backend/engines/butterfly.py` | Clean dataclass, in-memory `_timelines` dict | Engine unit tests, Paradox Engine, Entropy Engine | No — pure in-memory |
| `backend/mechanics/butterfly_engine.py` | Heavy class with repo injection, Pydantic schemas | API routes (`/api/butterfly/*`), frontend queries | Yes — via `timeline_repo` |
| `backend/worker/tasks/market_sync.py` | Direct SQLAlchemy ORM writes | Game loop market sync | Yes — direct `session.add()` |
| `backend/worker/tasks/entropy.py` | Direct SQLAlchemy ORM writes | Game loop entropy tick | Yes — direct `session.add()` |
| `backend/worker/tasks/paradox.py` | Direct SQLAlchemy ORM writes | Game loop paradox scan | Yes — direct `session.add()` |

**Problem:** The `backend/engines/` clean versions are the spec-compliant implementations (matching System Bible and PRD). The `backend/mechanics/` and `backend/worker/tasks/` versions are production-wired but diverge from spec in stability scales (0–100 vs 0.0–1.0), decay constants, and flap type coverage. The game loop (`game_loop.py`) calls the `worker/tasks/` versions, not the `engines/` versions.

**Remediation:** Unify on one authoritative engine layer. The `backend/engines/` pattern is correct for unit-testable business logic. The `worker/tasks/` pattern is correct for database persistence. These should compose, not duplicate: tasks call engines, engines return flap records, tasks persist them.

### 2.2 Stability Scale Divergence

| Layer | Scale | Decay Example |
|-------|-------|---------------|
| `engines/butterfly.py` | 0.0–1.0 | impact ±0.001 to ±0.15 |
| `mechanics/butterfly_engine.py` | 0–100 (percentage) | delta ±0.3 to ±50.0 |
| `worker/tasks/entropy.py` | 0–100 (percentage) | decay ~0.017%/min |
| `worker/tasks/market_sync.py` | 0–100 (percentage) | delta min(volume/10000, 5.0) |
| Database `Timeline.stability` | Float (0–100 in practice) | — |

**Problem:** The engines use normalised 0–1, the database and tasks use 0–100. Any engine-to-task bridge will misapply impacts by 100x unless one side adapts.

**Remediation:** Standardise on 0.0–1.0 throughout. The `engines/` scale is correct (matches Paradox Policy thresholds which are all in 0–1 space). Add migration to normalise existing database rows. Tasks multiply by 100 only at the UI serialisation boundary.

---

## 3. WingFlap Taxonomy Gaps

### 3.1 Current Taxonomy

```
WingFlapType:
  TRADE       — Agent buys/sells in LMSR
  SHIELD      — Agent stabilising action
  SABOTAGE    — Agent destabilising action
  RIPPLE      — Cross-timeline fork (schema only, never emitted)
  PARADOX     — Paradox Engine circuit breaker action
  ENTROPY     — System temporal decay
  FOUNDER_YIELD — Founder reward (DB enum only, not in engines/)
```

### 3.2 Missing Event Types

The following events now exist in the architecture but have no WingFlap representation:

| Event | Source | Stability Impact | Proposed WingFlapType |
|-------|--------|------------------|-----------------------|
| Polymarket price sync | MarketSyncTask | Neutral (anchor update) | `MIRROR_SYNC` |
| Polymarket trade mirror | MarketSyncTask._create_trade_flap | Calculated from volume | `MIRROR_TRADE` |
| Evidence envelope sealed | Investigation toolset | Positive (reality clarified) | `EVIDENCE` |
| Claim submitted | Investigation claim graph | Positive (information added) | `CLAIM` |
| Counter-signal detected | Investigation counter-signals | Negative (reality contested) | `COUNTER_SIGNAL` |
| Corroboration confirmed | Investigation corroboration checker | Positive (multi-source agreement) | `CORROBORATION` |
| Stop condition triggered | Investigation stop conditions | Neutral (lifecycle event) | `STOP_CONDITION` |
| Investigation certificate issued | Investigation certificate | Positive (investigation concluded) | `CERTIFICATE` |
| Fork created from anchor | Fork spawning | Neutral (new timeline, not stability change) | `FORK_SPAWN` |
| Timeline killed by Paradox | Paradox detonation | Negative (terminal) | `DETONATION` (currently overloaded under `PARADOX`) |

### 3.3 Proposed Extended Taxonomy

```python
class WingFlapType(str, Enum):
    # === Agent Actions ===
    TRADE = "TRADE"           # Agent LMSR trade
    SHIELD = "SHIELD"         # Agent stabilising action
    SABOTAGE = "SABOTAGE"     # Agent destabilising action

    # === Mirror Layer (Polymarket anchor) ===
    MIRROR_SYNC = "MIRROR_SYNC"     # Anchor price update from Polymarket
    MIRROR_TRADE = "MIRROR_TRADE"   # Anchor trade echoed as flap

    # === Investigation Layer ===
    EVIDENCE = "EVIDENCE"             # Evidence envelope sealed
    CLAIM = "CLAIM"                   # Claim graph node added
    COUNTER_SIGNAL = "COUNTER_SIGNAL" # Counter-signal detected
    CORROBORATION = "CORROBORATION"   # Multi-source corroboration confirmed

    # === System Events ===
    ENTROPY = "ENTROPY"         # Temporal stability decay
    PARADOX = "PARADOX"         # Paradox Engine warning/pause
    DETONATION = "DETONATION"   # Paradox Engine forced resolution / timeline kill
    RIPPLE = "RIPPLE"           # Cross-timeline cascade
    FORK_SPAWN = "FORK_SPAWN"   # New fork created from anchor
    STOP_CONDITION = "STOP_CONDITION"  # Investigation stop condition triggered
    CERTIFICATE = "CERTIFICATE" # Investigation certificate issued

    # === Rewards ===
    FOUNDER_YIELD = "FOUNDER_YIELD"  # Creator fee distribution
```

**Migration:** Add new enum values to `backend/database/models.py` WingFlapType. PostgreSQL enum extension via Alembic `ALTER TYPE wing_flap_type ADD VALUE 'MIRROR_SYNC'` etc. No existing rows affected.

### 3.4 Direction Semantics

Current `direction` field is `ANCHOR` or `DESTABILISE`. With the mirror/fork model, "ANCHOR" becomes overloaded (it means both "stabilising" and "from the anchor market"). Propose:

```
direction:
  STABILISE    — Positive stability impact (renamed from ANCHOR)
  DESTABILISE  — Negative stability impact (unchanged)
  NEUTRAL      — No stability impact (sync events, lifecycle events)
```

Rename `ANCHOR → STABILISE` in one migration pass. Frontend display can still show "Anchor" for mirror events using `flap_type == MIRROR_*`.

---

## 4. Anchor/Bifurcation Model Formalisation

### 4.1 Current Gap

The Butterfly Engine's `_spawn_ripple()` and `RIPPLE_THRESHOLD` assume forks are spontaneous events triggered by large stability deltas. In the mirror/fork architecture, the fork relationship is structural:

- **Anchor timeline** = Polymarket mirror (`TL_PM_*`)
- **Fork timeline** = Echelon agent-created divergence

There is no code that formally tracks which timeline is an anchor vs. a fork, or that measures divergence between anchor and fork prices.

### 4.2 Proposed Model

Add to `Timeline` model:

```python
# Mirror/Fork lineage
anchor_timeline_id: Mapped[Optional[str]]  # If this is a fork, points to anchor
is_anchor: Mapped[bool] = mapped_column(Boolean, default=False)
fork_divergence: Mapped[float] = mapped_column(Float, default=0.0)  # |fork_price - anchor_price|
```

Add to `ButterflyEngine`:

```python
def compute_fork_divergence(self, fork_id: str, anchor_id: str) -> float:
    """Measure how far a fork has diverged from its anchor."""
    fork = self._get_or_create_timeline(fork_id)
    anchor = self._get_or_create_timeline(anchor_id)
    # Divergence is the absolute price difference
    return abs(fork.price_yes - anchor.price_yes)
```

The Paradox Engine can then use `fork_divergence` as a logic gap source — when the fork diverges too far from its anchor without supporting evidence, a paradox spawns.

### 4.3 Ripple Redefinition

With formal anchor/fork lineage, `RIPPLE` can be redefined:

- **Old meaning:** Spontaneous fork when stability delta exceeds threshold
- **New meaning:** Cross-timeline contagion — a significant event in one timeline (anchor or fork) cascades stability impact to related timelines

The `RIPPLE_THRESHOLD` (currently 15% in mechanics/, not implemented in engines/) becomes the contagion threshold: if a MIRROR_TRADE or EVIDENCE flap causes stability delta > threshold in the anchor, emit a RIPPLE flap in all forks of that anchor.

---

## 5. Entropy Engine Coherence

### 5.1 Current Issues

**Issue 1: Hardcoded Logic Gap thresholds**

The `EntropyEngine` accepts `logic_gap_status` as a string (`"healthy"`, `"stressed"`, `"danger"`, `"critical"`) but doesn't know which thresholds produced that status. The Paradox Policy v1.1 defines per-inquiry-class thresholds:

| Inquiry Class | Warn | Breach | Critical |
|---------------|------|--------|----------|
| counterfactual | 0.20 | 0.40 | 0.60 |
| investigative | 0.30 | 0.50 | 0.70 |
| inspection | 0.20 | 0.40 | 0.60 |
| survey | 0.30 | 0.50 | 0.70 |
| scrutiny | — | — | 0.80 |

The Entropy Engine must consume the same thresholds, or a timeline in `"stressed"` state could have a 30% logic gap (investigative) or 20% (counterfactual) — the decay rate should differ.

**Remediation:** Entropy Engine should accept the `LogicGapReading` directly (which includes the numeric gap), not just the status string. Decay multiplier should be derived from gap magnitude relative to the Theatre's committed Paradox thresholds, not from a status enum.

```python
def tick(self, theatre_id: str, reading: LogicGapReading | None = None) -> WingFlap:
    """Apply decay. Scales with Logic Gap reading if available."""
    if reading is None:
        rate = self._config.base_decay_rate
    else:
        rate = self._compute_scaled_rate(reading)
    ...

def _compute_scaled_rate(self, reading: LogicGapReading) -> float:
    """Scale decay rate by how close the gap is to the committed critical threshold."""
    gap = reading.logic_gap
    critical = self._paradox_config.critical_threshold
    # Linear interpolation: base rate at gap=0, critical_multiplier at gap=critical
    ratio = min(gap / critical, 1.0) if critical > 0 else 0.0
    return self._config.base_decay_rate * (1.0 + ratio * (self._config.critical_multiplier - 1.0))
```

**Issue 2: Single-market game loop cadence**

The `EntropyTask.tick()` iterates all active timelines and applies decay. With 20+ Polymarket-mirrored timelines, this is fine — it already handles multiple timelines. However, the decay calculation (`_calculate_decay`) uses `timeline.has_active_paradox` as a boolean flag, not the committed ParadoxConfig. This means:

- It doesn't know the inquiry class
- It doesn't know the committed thresholds
- It applies a flat 2x multiplier for paradox, not the severity-dependent multiplier from the Paradox Policy

**Remediation:** `EntropyTask._calculate_decay()` should load the Theatre's committed `ParadoxConfig` (or the active `Paradox` record) to determine the correct multiplier. The `Paradox.decay_multiplier` field already exists in the DB — the task should use it instead of hardcoding 2.0.

**Issue 3: Anchor timelines shouldn't decay**

Anchor timelines (`TL_PM_*`) are mirrors of Polymarket reality. Their stability should be driven by Polymarket data quality (price updates arriving on schedule, orderbook depth), not by temporal decay. Applying entropy to an anchor timeline is incoherent — it would mean "reality gets less reliable over time" which is not the system's model.

**Remediation:** `EntropyTask.tick()` should skip timelines where `is_anchor == True`. Anchor stability is set by `MarketSyncTask` price update frequency and can be degraded by missed sync cycles (a different kind of "entropy" — staleness detection, not temporal decay).

---

## 6. Founder's Yield → Creator Fee

### 6.1 Current Model

`compute_founders_yield(theatre_id)` returns `stability × volume × 0.005`. This was designed for a simulation where users create timelines and earn yield when their timeline stays healthy.

### 6.2 Mirror/Fork Context

In the mirror/fork model:
- **Anchor timelines** are auto-created by MarketSyncTask. There is no "founder."
- **Fork timelines** are created by agents (or users through the investigation creation wizard). The creator is the investigation sponsor.

The concept should be **creator fee**, not "founder's yield":
- Only fork timelines have creators
- Fee accrues when the fork produces a valid investigation certificate (not continuously from stability)
- Fee rate is committed at fork creation time (part of the commitment protocol)

**Remediation:** Rename `FOUNDER_YIELD` to `CREATOR_FEE` in the WingFlap taxonomy. Move accrual from continuous stability-based calculation to certificate issuance event. Add `creator_fee_rate` to Theatre/Timeline commitment parameters. The `compute_founders_yield()` method becomes `compute_creator_fee(certificate)`.

---

## 7. Game Loop Amendments

### 7.1 Current Cadence

```
AGENT:    5s  — Agent decisions
MARKET:  10s  — Polymarket sync
PARADOX: 30s  — Breach detection
ENTROPY: 60s  — Stability decay
GENESIS: 300s — Phoenix protocol (ensure min timelines)
```

### 7.2 Proposed Amendments

| Cadence | Current | Proposed | Reason |
|---------|---------|----------|--------|
| MARKET | 10s, all markets | 10s, staggered | Rate limit compliance: 100 req/60s. With 20 markets, each needing ~3 API calls (trending + trades), 10s cadence = 180 req/min. Stagger: sync 5 markets per tick, rotate. |
| PARADOX | 30s, hardcoded thresholds | 30s, per-Theatre config | Load committed ParadoxConfig per Theatre. Different inquiry classes get different thresholds. |
| ENTROPY | 60s, all timelines | 60s, skip anchors | Anchors don't decay. Forks decay at inquiry-class-aware rates. |
| EVIDENCE | N/A | 120s (new) | Poll investigation toolset for new evidence envelopes. Emit EVIDENCE flaps. |
| DIVERGENCE | N/A | 60s (new) | Compute fork divergence from anchor. Emit MIRROR_SYNC if anchor price changed. Feed into Paradox as logic gap source. |

### 7.3 SYSTEM Entity Duplication

Every task file (`entropy.py`, `paradox.py`, `market_sync.py`) independently checks for and creates the SYSTEM user and agent. This is ~30 lines of identical boilerplate per file.

**Remediation:** Extract to `backend/worker/tasks/_system_entity.py`:

```python
async def ensure_system_entities(session: AsyncSession) -> tuple[User, Agent]:
    """Ensure SYSTEM user and agent exist. Idempotent."""
    ...
```

All tasks import and call this once at the start of their `tick()`.

---

## 8. Acceptance Criteria

### 8.1 Taxonomy Extension (Gate A)
- [ ] `WingFlapType` enum extended with all types from §3.3
- [ ] Alembic migration adds new enum values to PostgreSQL
- [ ] `direction` field: `ANCHOR` renamed to `STABILISE`, `NEUTRAL` added
- [ ] All existing code paths that emit flaps updated to new types
- [ ] `MarketSyncTask._create_trade_flap()` emits `MIRROR_TRADE` not `TRADE`

### 8.2 Stability Scale Unification (Gate B)
- [ ] All engine code uses 0.0–1.0 scale
- [ ] All task code uses 0.0–1.0 scale
- [ ] Database `Timeline.stability` stored as 0.0–1.0
- [ ] Alembic migration normalises existing rows: `UPDATE timelines SET stability = stability / 100.0 WHERE stability > 1.0`
- [ ] API serialisation multiplies by 100 for percentage display
- [ ] Frontend receives percentages (0–100), no breaking change

### 8.3 Engine Unification (Gate C)
- [ ] `backend/engines/butterfly.py` is the single source of truth for flap recording logic
- [ ] `backend/worker/tasks/*.py` compose with engines, not duplicate them
- [ ] `backend/mechanics/butterfly_engine.py` either delegates to `engines/butterfly.py` or is retired
- [ ] Gravity calculation consolidated in one location

### 8.4 Anchor/Fork Model (Gate D)
- [ ] `Timeline` model has `anchor_timeline_id`, `is_anchor`, `fork_divergence` fields
- [ ] `MarketSyncTask` sets `is_anchor=True` on auto-created timelines
- [ ] `ButterflyEngine.compute_fork_divergence()` implemented
- [ ] `EntropyTask` skips timelines where `is_anchor=True`
- [ ] Paradox Engine can use fork divergence as logic gap source

### 8.5 Inquiry-Aware Entropy (Gate E)
- [ ] `EntropyEngine.tick()` accepts `LogicGapReading` not just status string
- [ ] Decay rate scales with gap magnitude relative to committed thresholds
- [ ] `EntropyTask._calculate_decay()` uses `Paradox.decay_multiplier` from DB, not hardcoded 2.0

### 8.6 Creator Fee (Gate F)
- [ ] `FOUNDER_YIELD` renamed to `CREATOR_FEE` throughout
- [ ] Creator fee accrues at certificate issuance, not continuously
- [ ] `creator_fee_rate` added to Theatre commitment parameters
- [ ] Only fork timelines accrue creator fees

### 8.7 Game Loop (Gate G)
- [ ] Market sync staggered (5 markets/tick, rotating)
- [ ] SYSTEM entity creation extracted to shared utility
- [ ] New `EVIDENCE` heartbeat cadence (120s) — stub for 016
- [ ] New `DIVERGENCE` heartbeat cadence (60s) — computes fork divergence

---

## 9. Test Impact

**Baseline (post-014c):** ≥1009 tests

**Expected additions:**
- Taxonomy extension: 6 tests (one per new flap type emission path)
- Stability scale: 4 tests (normalisation, boundary, migration, API serialisation)
- Engine unification: 8 tests (task-engine composition, mechanics delegation)
- Anchor/fork model: 5 tests (divergence calculation, anchor skip, fork lineage)
- Inquiry-aware entropy: 4 tests (per-class scaling, reading-based decay)
- Creator fee: 3 tests (accrual at certificate, rate commitment, anchor exclusion)
- Game loop: 4 tests (stagger rotation, system entity shared, evidence cadence, divergence cadence)

**Post-remediation target:** ≥1043

---

## 10. Sequencing

This remediation is **016 Sprint 1 pre-work**. The results surface cannot correctly display wing flaps, stability charts, or investigation events if the underlying taxonomy and scales are incoherent.

**Recommended order:**
1. Gate B (stability scale) — foundational; everything else depends on consistent scale
2. Gate A (taxonomy) — Alembic migration, no logic changes
3. Gate C (engine unification) — structural refactor, tasks delegate to engines
4. Gate D (anchor/fork model) — data model extension
5. Gate E (inquiry-aware entropy) — engine logic enhancement
6. Gate F (creator fee) — reward model amendment
7. Gate G (game loop) — operational cadence changes

Gates A+B can be done in a single sprint day. Gates C+D are the heaviest lift. Gates E+F+G are incremental.

---

## 11. Files Affected

| File | Changes |
|------|---------|
| `backend/database/models.py` | WingFlapType enum extension, Timeline anchor fields, direction rename |
| `backend/engines/butterfly.py` | Fork divergence method, STABILISE direction |
| `backend/engines/entropy.py` | Accept LogicGapReading, scaled decay |
| `backend/engines/paradox.py` | No changes (already inquiry-aware) |
| `backend/worker/tasks/entropy.py` | Delegate to engine, skip anchors, use DB multiplier |
| `backend/worker/tasks/paradox.py` | Delegate to engine for threshold evaluation |
| `backend/worker/tasks/market_sync.py` | Emit MIRROR_TRADE, set is_anchor, staggered sync |
| `backend/worker/game_loop.py` | Add evidence + divergence cadences, stagger market sync |
| `backend/mechanics/butterfly_engine.py` | Retire or delegate to engines/ |
| `backend/investigation/*.py` | Emit EVIDENCE, CLAIM, COUNTER_SIGNAL, CORROBORATION flaps |
| Alembic migration | Enum extension, stability normalisation, anchor fields, direction rename |

---

## 12. Open Questions

1. **Should `backend/mechanics/butterfly_engine.py` be retired entirely or kept as a facade?** It has API route bindings that would need rewiring. Recommend: keep as facade that delegates to `engines/butterfly.py` for logic, adds DB persistence via repo pattern.

2. **Should anchor timelines have their own Paradox policy?** An anchor that stops receiving Polymarket updates is "stale," which is functionally similar to a logic gap. Recommend: yes, with a `STALENESS` activation gate type that fires when `last_sync_time > threshold`.

3. **Should RIPPLE flaps propagate stability impact automatically, or just record the event?** Automatic propagation creates cascading instability. Recommend: record only in v1, automatic propagation in a future cycle after observing fork behaviour.

---

*This design note should be reviewed by Codex before implementation begins. All gate criteria are testable and deterministic.*
```

## /Users/tobiasharber/Developer/prediction-market-monorepo.nosync/docs/README.md (engine references)
```markdown
# Echelon — Architecture Documentation

> The first AI agent prediction market platform. Autonomous agents create, trade, and resolve structured scenario markets — producing calibrated training data for robotics and AI systems through Reinforcement Learning from Market Feedback (RLMF).

## Core Architecture

The canonical specifications that define how Echelon works.

| Document | Description | Version |
|----------|-------------|---------|
| [System Bible](core/System_Bible_v10.md) | Complete platform specification: LMSR cost functions, commitment protocol, VRF integration, Paradox Engine, agent archetypes, RLMF export pipeline, Theatre lifecycle | v10 |
| [OSINT & Reality Oracle Appendix](core/OSINT_Reality_Oracle_Appendix_v3_1.md) | Data pipeline architecture: provider mix, evidence bundle schema, corroboration requirements, prediction market feed normalisation, phased budget model | v3.1 |
| [Real-to-Sim Incident Replay](core/Real_to_Sim_Incident_Replay_v1.md) | Historical replay methodology: take real-world events with known outcomes, replay data as it unfolded, let agents trade against it, score calibration against ground truth | v1 |

## Schemas

Machine-readable specifications for interoperability.

| Schema | Description |
|--------|-------------|
| [Theatre Schema](schemas/echelon_theatre_schema.json) | Theatre Template structure: scenario configuration, fork definitions, resolution criteria, OSINT source commitments, agent deck composition |
| [RLMF Schema](schemas/echelon_rlmf_schema.json) | Training data export format: position histories, Brier scores, confidence discipline metrics, market-derived Q-value distributions |

## Technical Deep Dives

Detailed specifications for individual subsystems.

| Document | Description |
|----------|-------------|
| [VRF Enhanced Protocol](technical/VRF_Enhanced_Protocol.md) | Verifiable Random Function integration: perturbation injection, sensor jitter, occlusion timing, chaos mechanics for robustness testing |
| [Betting Mechanics](technical/Betting_Mechanics.md) | Trading system design: position management, LMSR price impact, fork mechanics, entropy-driven position decay |
| [Oracle Modes](technical/Oracle_Modes.md) | Resolution oracle architecture: automated settlement, multi-source corroboration, dispute escalation, human override governance |
| [Archetype Matrix](technical/Archetype_Matrix.md) | Agent behavioural profiles: Shark, Spy, Diplomat, Saboteur — trading strategies, OSINT specialisations, risk profiles, cross-domain adaptation |
| [Risk Mitigation](technical/Risk_Mitigation.md) | Security and adversarial analysis: agent collusion, oracle manipulation, market microstructure attacks, Paradox Engine thresholds |
| [Governance](technical/Governance.md) | Platform governance: Theatre creation authority, parameter adjustment, dispute resolution, upgrade mechanics |

## Simulation

| File | Description |
|------|-------------|
| [Tokenomics Simulation](simulation/tokenomics_simulation.py) | Monte Carlo simulation of token economics: burn/mint dynamics, market activity projections, equilibrium modelling |

## Key Concepts

**Theatres** — Structured prediction market environments where AI agents and humans trade on real-world outcomes. Each Theatre commits its parameters (OSINT sources, resolution criteria, agent deck, LMSR liquidity) at creation and locks them cryptographically.

**LMSR (Logarithmic Market Scoring Rule)** — Automated market maker that provides guaranteed liquidity and mathematically correct pricing. The committed liquidity parameter `b` controls price sensitivity and makes information aggregation a priced, bounded resource.

**Paradox Engine** — Self-policing integrity mechanism. Measures divergence between market consensus and observable reality signals (Logic Gap). When divergence exceeds committed thresholds, imposes escalating costs — the system's immune response against hallucination.

**RLMF (Reinforcement Learning from Market Feedback)** — Training methodology that replaces expensive human annotation with autonomous agent betting systems. Market-implied probability distributions serve as supervision signals for AI policy evaluation.

**Real-to-Sim Replay** — Historical events with known outcomes are replayed through Theatres. Agents trade against pre-loaded ground truth, producing calibration scores in minutes rather than waiting for real-time resolution.

**VRF Perturbations** — Verifiable Random Functions inject controlled chaos (sensor jitter, timing delays, information occlusion) to test agent robustness under adversarial conditions.

## Architecture Overview

```
┌─────────────────────────────────────────────┐
│              OSINT Pipeline                  │
│  GDELT · X API · Polygon.io · Domain feeds  │
│  Evidence bundles · Corroboration · Hashing  │
├─────────────────────────────────────────────┤
│            Theatre Engine                    │
│  LMSR markets · Commitment protocol         │
│  VRF perturbations · Fork mechanics          │
├─────────────────────────────────────────────┤
│           Agent Population                   │
│  Archetypes · Hierarchical brain             │
│  Multi-provider routing · Wallet factory     │
├─────────────────────────────────────────────┤
│          Integrity Layer                     │
│  Paradox Engine · Logic Gap · Entropy Engine │
├─────────────────────────────────────────────┤
│          RLMF Export Pipeline                │
│  Position histories · Brier scores           │
│  Calibration certificates · Training data    │
└─────────────────────────────────────────────┘
```

## Status

Working prototype on Base Sepolia. Core components implemented: Pydantic agent schemas, multi-provider brain routing, LMSR contracts, wallet factory with HD derivation, OSINT pipeline with 21+ data sources, React Situation Room UI. Seeking grant funding for OSINT data pipeline ($1,400–2,600/month for 2–3 concurrent Theatres).

## Contact

Built by Tobias James — [@tobiasjames](https://x.com/tobiasjames)
```

## /Users/tobiasharber/Developer/prediction-market-monorepo.nosync/docs/dev/BOOTSTRAP_CONTEXT.md (Butterfly mention)
```markdown
# Echelon Project — Bootstrap Context for New Conversations

**Last Updated:** December 16, 2025
**Domain:** playechelon.io
**Purpose:** Provide context continuity for Claude when starting new chats about Echelon

---

## 1. PROJECT OVERVIEW

**Echelon** is a counterfactual prediction market platform that forks real markets (Kalshi/Polymarket) into parallel "what if" timelines. Users bet on alternate realities powered by AI agents and real-time OSINT data.

### Core Taglines (Approved)
- **Primary:** "Kalshi/Polymarket lets you bet on what will happen. Echelon lets you bet on what could have happened."
- **Insight:** "We aren't predicting the future — we're detecting the present faster than the news."
- **Positioning:** "Users aren't just trading — they're playing geopolitics."

### Three Pillars
1. **The Butterfly Engine** — Cryptographically secured timeline divergence (Snapshot & Fork architecture)
2. **Mission-Based Trading** — OSINT-triggered scenarios with objectives, time pressure, rewards
3. **AI Agents** — Sharks, Spies, Diplomats, Saboteurs with on-chain wallets and verifiable P&L

---

## 2. CURRENT INFRASTRUCTURE STATE

### Domain & Hosting
- **Domain:** playechelon.io (to be configured)
- **DNS:** Cloudflare (pending setup)
- **Backend:** FastAPI on localhost:8000 (pending deployment)
- **Frontend:** Next.js on localhost:3000 (pending deployment)

### Blockchain (Testnet)
- **Chain:** Base Sepolia
- **Settlement Wallet:** 0xA4885D48e09D62a47Fc5c9Add7eAd130DCBd5688
- **OnchainKit API:** (set via `NEXT_PUBLIC_ONCHAINKIT_API_KEY`)

### Coinbase Integration
- **Commerce API Key:** (set via `COINBASE_COMMERCE_API_KEY`)
- **Webhook Secret:** (set via `COINBASE_WEBHOOK_SECRET`)

---

## 3. TECHNICAL ARCHITECTURE

### Hierarchical Intelligence (Cost Optimisation)
- **Layer 1 (90%+ of decisions):** Rule-based heuristics (<10ms, $0 cost)
  - Tulip Strategy: Illiquid market near-expiry arbitrage
  - Blood in Water: Wide spread liquidity provision
  - Exit Rules: Take profit/stop loss/time decay
- **Layer 2 (~10% of decisions):** Fast LLM (Groq/Ollama) for novel situations
- **Layer 3 (<1% of decisions):** Quality LLM (Claude/GPT-4) for complex reasoning

### The Sandwich Architecture
- **Brain (Google ADK):** Context engine, decision logic, narrative generation
- **Body (Virtuals Protocol):** ERC-6551 wallet, x402 payments, execution

### Multi-Chain Wallet
- **Base:** Virtuals identity, ACP transactions, tokenisation
- **Polygon:** Polymarket execution (Gnosis Safe + Relayer)
- **Solana:** Kalshi execution (programmatic keypair)

---

## 4. API ENDPOINTS (Implemented)

### Operations API
- `GET /api/operations` — List active operations
- `POST /api/operations/{id}/join` — Join an operation
- `GET /api/agents` — List agents and P&L
- `POST /api/agents/hire` — Hire agent via ACP
- `GET /api/intel` — Available intel packages
- `POST /api/intel/purchase` — Buy intel
- `GET /api/game-state` — Global state for Situation Room
- `GET /api/signals` — Real-time agent signals

### Butler Webhooks
- `POST /api/butler/webhook` — Main webhook for X integration
- `POST /api/butler/test` — Local testing endpoint
- `GET /api/butler/health` — Health check

### Scheduler API
- `POST /api/scheduler/start` — Start autonomous agents
- `POST /api/scheduler/stop` — Stop scheduler
- `GET /api/scheduler/status` — Scheduler stats
- `GET /api/scheduler/agents` — List scheduled agents
- `POST /api/scheduler/run-cycle/{id}` — Manual trigger

---

## 5. APPROVED MISSIONS (Exciting Examples)

| Mission | OSINT Anomaly | Threshold Trigger |
|---------|---------------|-------------------|
| **Ghost Tanker** | Spire AIS dark fleet | >3 tankers go dark near Venezuela/Hormuz |
| **Silicon Acquisition** | Job postings + USPTO patents | Apple posts >50 AI roles in 1 week |
| **Contagion Zero** | Social keyword geo-clustering | 300% spike in "flu" mentions in city |
| **Deep State Shuffle** | NASA night lights + flight tracking | Palace dark + jets to Miami 2-4AM |
| **Cartel Crop** | Sentinel Hub satellite NDVI | Greenness spike in Sinaloa off-season |

---

## 6. BUDGET ($300K / 6 months)

| Category | Amount |
|----------|--------|
| Development | $150,000 |
| OSINT/Data Infrastructure | $100,000 |
| Infrastructure & Audit | $30,000 |
| Operations | $20,000 |

---

## 7. CONTACT

- **Email:** playechelon@gmail.com
- **X:** @playechelon
- **Domain:** playechelon.io

---
```
