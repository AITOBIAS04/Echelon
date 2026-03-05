# Echelon Butterfly & Entropy Engine Coherence Review v1

> Design Note — Butterfly Engine, Entropy Engine, and Game Loop alignment with the Mirror/Fork architecture and Investigation Toolset.
> UK British English throughout.
> **Version:** 1.2.1
> **Date:** 5 March 2026
> **Depends on:** Cycle-010b (engines + heartbeat), Cycle-014c (investigation toolset), Cycle-016 (results surface), Polymarket integration
> **Cross-referenced against:** `output/engine_source_readout.md`, `output/engine_spec_sections_readout.md`

---

## 0. Missing Artefact: Paradox Policy Design Note v1

The System Bible v13 Addendum (§6, line ~127) references `Echelon_Paradox_Policy_Design_Note_v1.md` for the inquiry-aware Paradox Engine extension. **This file does not exist in the repository.** The per-inquiry-class thresholds cited in §5.1 of this review come from the Cycle-010b PRD (Section 4.7), which is the only surviving source of those specifications.

**Action required:** Either locate and restore the Paradox Policy Design Note, or formalise the 010b PRD thresholds as the canonical specification. Until this is resolved, §5.1 thresholds should be treated as provisional.

## 0.1 Naming Inconsistency: "Brittle" vs "Danger"

The System Bible v13 uses **"Brittle"** for the 40–60% Logic Gap band. The `engines/entropy.py` and `engines/config.py` use **"danger"** for the same band. The `_MULTIPLIERS` dict in `entropy.py` and the `danger_multiplier` field in `EntropyConfig` should be reconciled. Recommend: adopt "danger" throughout code (more operationally descriptive) and note the Bible uses "Brittle" in its prose.

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
| `engines/butterfly.py` | 0.0–1.0 (starts at 1.0) | impact ±0.001 to ±0.15 |
| `mechanics/butterfly_engine.py` | 0–100 (percentage) | delta ±0.3 to ±50.0 |
| `worker/tasks/entropy.py` | 0–100 (percentage) | decay ~0.017%/min |
| `worker/tasks/market_sync.py` | 0–100 (percentage) | delta min(volume/10000, 5.0) |
| Database `Timeline.stability` | Float, **default=50.0** (0–100 in practice) | — |
| System Bible v13 §5.1 | "±0.1% to ±5%" | Percentage notation — maps to 0.001–0.05 in 0–1 scale |

**Problem:** The engines use normalised 0–1, the database and tasks use 0–100 (DB default is 50.0, not 0.5). Any engine-to-task bridge will misapply impacts by 100x unless one side adapts. The System Bible's percentage notation ("±0.1% to ±5%") is consistent with the `engines/` 0–1 scale when read as "percentage of 1.0".

**Remediation:** Standardise on 0.0–1.0 throughout. The `engines/` scale is correct (matches Paradox Policy thresholds which are all in 0–1 space, and matches System Bible percentage notation). Add migration to normalise existing database rows (`stability / 100.0`). Change DB default from `50.0` to `0.5`. Tasks multiply by 100 only at the UI serialisation boundary.

---

## 3. WingFlap Taxonomy Gaps

### 3.1 Current Taxonomy

```
WingFlapType:
  TRADE       — Agent buys/sells in LMSR
  SHIELD      — Agent stabilising action
  SABOTAGE    — Agent destabilising action
  RIPPLE      — Cross-timeline fork (not emitted by active runtime paths; present in seed fixtures at seed_database.py:630)
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

**Existing field:** `Timeline.parent_timeline_id` already exists in the DB model as a nullable FK to `timelines.id`. This provides fork lineage but lacks anchor semantics.

Add to `Timeline` model (supplement `parent_timeline_id`, don't replace it):

```python
# Mirror/Fork lineage (extends existing parent_timeline_id)
anchor_timeline_id: Mapped[Optional[str]]  # If this is a fork, points to its Polymarket anchor
is_anchor: Mapped[bool] = mapped_column(Boolean, default=False)  # True for TL_PM_* timelines
fork_divergence: Mapped[float] = mapped_column(Float, default=0.0)  # |fork_price - anchor_price|
last_sync_at: Mapped[Optional[datetime]]  # Last successful Polymarket price sync (for staleness detection)
```

Note: `parent_timeline_id` tracks general fork lineage (any fork-of-a-fork). `anchor_timeline_id` specifically tracks the Polymarket mirror relationship. A fork of a fork would have `parent_timeline_id` pointing to the immediate parent and `anchor_timeline_id` pointing to the ultimate Polymarket anchor.

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

**Remediation — with double-application guard:** The current code has a compounding bug. Paradox spawn already writes the multiplied rate: `decay_rate_per_hour = base * (severity_multiplier + 1)` at `paradox.py:178` and stores `decay_multiplier = severity_multiplier + 1` at `paradox.py:186`. Entropy then reads the already-multiplied `decay_rate_per_hour` at `entropy.py:166` **and** multiplies by 2.0 again at `entropy.py:171`. Result: paradox timelines decay at `base × (sev+1) × 2.0` — a double-application.

**The multiplier must be applied exactly once.** Two valid patterns:

- **Pattern A (recommended):** Paradox spawn writes `decay_multiplier` only, leaves `decay_rate_per_hour` at base rate. Entropy reads base rate and applies `timeline.decay_multiplier`. Single multiplication point.
- **Pattern B:** Paradox spawn writes the multiplied `decay_rate_per_hour`. Entropy reads it directly and does NOT apply any additional multiplier. The `has_active_paradox` branch in `_calculate_decay()` is removed entirely.

Either way, the hardcoded `2.0` at `entropy.py:171` must be removed. Both `Paradox.decay_multiplier` and `Timeline.decay_multiplier` already exist in the DB — the task should use one authoritative source, not compound them.

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
| MARKET | 10s, capped to 10 active | 10s, no change needed (headroom exists) | Actual call path per tick: 1× `get_trending_markets(limit=20)` → filter to 10 active (`market_sync.py:66`) → up to 10× `get_trades()` per market = **11 calls max/tick**. At 10s cadence = **66 req/min**, within 100/60s limit. Staggering is not required at current scale but becomes necessary if cap increases beyond 15 active markets. Token prices are extracted from the trending payload directly (no per-market price endpoint). |
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
- [ ] Market sync remains at 10s cadence with current top-10 active cap
- [ ] Market sync call-budget guardrail added: if active cap > 15, require staggered mode or equivalent backoff
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
- Game loop: 4 tests (market call-budget guardrail, system entity shared, evidence cadence, divergence cadence)

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
| `backend/worker/tasks/market_sync.py` | Emit MIRROR_TRADE, set is_anchor, enforce call-budget guardrail |
| `backend/worker/game_loop.py` | Add evidence + divergence cadences (market cadence unchanged at current cap) |
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
