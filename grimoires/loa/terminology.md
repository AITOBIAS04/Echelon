# Domain Terminology — Echelon

> **Generated**: 2026-02-18

## Core Concepts

- id: lmsr
  term: LMSR (Logarithmic Market Scoring Rule)
  short: Cost-function automated market maker replacing order books
  context: "C(x) = b * ln(sum_j exp(x_j / b))" — always-on prices, no counterparty required, bounded loss
  source: docs/core/System_Bible_v10.md:143-155
  tags: [market, math, core]

- id: theatre
  term: Theatre
  short: Structured prediction market environment with committed parameters
  context: Each Theatre commits OSINT sources, resolution criteria, agent deck, LMSR liquidity at creation. Parameters locked after trading begins.
  source: docs/core/System_Bible_v10.md:85-133, README.md:39
  tags: [market, core]

- id: theatre_template
  term: Theatre Template
  short: JSON specification defining a complete market contract
  context: Families include 2D-DISCRETE, 3D-DYNAMIC, PHYSICS-SIM, SOCIAL-ENGINEERING, ECONOMIC-SIM, HYBRID. Schema at docs/schemas/echelon_theatre_schema.json
  source: docs/core/System_Bible_v10.md:93-106
  tags: [schema, market]

- id: fork
  term: Fork / Fork Point
  short: Decision point within a Theatre where agents choose from constrained options
  context: Fork triggers are typed: timestep-based, state-reached, entropy-threshold, logic-gap-threshold. Each option has success criteria and state transitions.
  source: docs/core/System_Bible_v10.md:127-133
  tags: [market, mechanics]

- id: commitment_protocol
  term: Commitment Protocol
  short: Immutable market lifecycle — nothing changes after capital arrives
  context: All parameters published as commitment hash on-chain before trading. Scenario pack, OSINT sources, agent deck, resolution mechanism all committed.
  source: docs/core/System_Bible_v10.md:286-299
  tags: [integrity, core]

- id: paradox_engine
  term: Paradox Engine
  short: Self-policing integrity mechanism activated when Logic Gap exceeds thresholds
  context: Spawn conditions (40/50/60% Logic Gap), four-stage lifecycle (Spawn → Extraction → Carrier Burden → Resolution). Imposes escalating costs.
  source: docs/core/System_Bible_v10.md:261-284
  tags: [integrity, mechanics]

- id: logic_gap
  term: Logic Gap
  short: Divergence between market-implied probability and OSINT reality signals
  context: <20% = Healthy, 20-40% = Stressed, 40-60% = Brittle, >60% = Critical (Paradox spawns)
  source: docs/core/System_Bible_v10.md:243-250
  tags: [integrity, metrics]

- id: entropy_engine
  term: Entropy Engine
  short: Temporal decay mechanism ensuring timelines don't persist indefinitely
  context: 60-second heartbeat. Forces velocity of capital — positions decay if holders don't act.
  source: docs/core/System_Bible_v10.md:241-259
  tags: [integrity, mechanics]

- id: butterfly_engine
  term: Butterfly Engine / Wing Flaps
  short: Causal state transitions — every action modifies simulation state
  context: Flap types: TRADE, SHIELD, SABOTAGE, RIPPLE, PARADOX, ENTROPY. Each has stability impact. Founder's Yield = stability × volume × 0.005
  source: docs/core/System_Bible_v10.md:224-239
  tags: [mechanics, core]

- id: rlmf
  term: RLMF (Reinforcement Learning from Market Feedback)
  short: Training data product — market-implied distributions replace human annotation
  context: Position histories, Brier scores, calibration certificates. Export formats: PyTorch, ROS Bag, TFRecord, JSON.
  source: README.md:56, docs/schemas/echelon_rlmf_schema.json
  tags: [data, product, core]

- id: real_to_sim
  term: Real-to-Sim Replay
  short: Historical events replayed through Theatres for calibration
  context: Tiered seed model (Incident descriptor → Event telemetry → Full sensor logs). Produces RLMF datasets aligned to real-world edge cases.
  source: docs/core/Real_to_Sim_Incident_Replay_v1.md:1-12
  tags: [methodology, calibration]

- id: osint
  term: OSINT (Open Source Intelligence)
  short: Multi-source data pipeline converting raw signals into oracle-grade structured events
  context: 21+ sources (GDELT, Polygon.io, X API, Spire Global, Whale Alert, etc.). Entity-extracted, confidence-scored, timestamped. NOT on 60s VRF heartbeat — separate timescale.
  source: docs/core/OSINT_Reality_Oracle_Appendix_v3_1.md:1-46
  tags: [data, pipeline]

- id: vrf
  term: VRF (Verifiable Random Function)
  short: Chainlink V2 integration for verifiable chaos injection
  context: 60-second entropy heartbeat on Base. Produces unpredictable, verifiable randomness for simulation perturbations.
  source: docs/technical/VRF_Enhanced_Protocol.md, smart-contracts/contracts/EchelonVRFConsumer.sol
  tags: [chain, randomness]

- id: cfpm
  term: CFPM (Cost-Function Prediction Market)
  short: Prediction market where prices derive from a convex cost function, not order matching
  context: LMSR is a specific CFPM. Implements stochastic mirror descent on the price simplex. Each trade = gradient update on collective belief.
  source: docs/core/System_Bible_v10.md:63-67
  tags: [market, math]

## Agent Archetypes

- id: archetype_spy
  term: Spy
  short: Intelligence specialist with early OSINT access
  context: Abilities: ENCRYPT_INTEL, EARLY_ACCESS, SABOTAGE_COMMS, DEAD_DROP, IDENTITY_THEFT
  source: backend/core/models.py:38,96-102
  tags: [agent, archetype]

- id: archetype_diplomat
  term: Diplomat
  short: Stability seeker who creates treaties and hedges positions
  context: Abilities: PROPOSE_TREATY, SANCTION, IMMUNITY, BACKCHANNEL, VETO
  source: backend/core/models.py:39,104-109
  tags: [agent, archetype]

- id: archetype_trader
  term: Trader
  short: Market-focused agent exploiting price dislocations
  context: Abilities: FRONT_RUN, MARKET_MAKE, SHORT_SQUEEZE, INSIDER_TRADE, FLASH_CRASH
  source: backend/core/models.py:40,111-116
  tags: [agent, archetype]

- id: archetype_saboteur
  term: Saboteur
  short: Chaos agent spreading uncertainty and attacking positions
  context: Abilities: FALSE_FLAG, LEAK_FAKE_NEWS, INFRASTRUCTURE_ATTACK, DOUBLE_AGENT, CHAOS_INJECTION
  source: backend/core/models.py:41,118-123
  tags: [agent, archetype]

## Phase 1 Concepts

- id: community_oracle
  term: Community Oracle
  short: AI construct that summarises code changes for audiences
  context: Ingests PRs/commits, produces tweets/Discord messages/changelog posts. Phase 1 evaluates accuracy via Theatre Replay methodology.
  source: loa-grimoire/context/echelon_context.md:17-21
  tags: [phase1, construct]

- id: calibration_certificate
  term: Calibration Certificate
  short: Structured JSON scoring an oracle's precision, recall, and reply accuracy
  context: Aggregate of N replay scores. Eventually attaches to construct's finnNFT Soul and gates model routing tiers.
  source: loa-grimoire/context/echelon_context.md:50-64
  tags: [phase1, output]

- id: ground_truth
  term: Ground Truth Document
  short: Structured record of a PR/commit with known content for oracle evaluation
  context: Fields: id, title, diff_content, files_changed, description, timestamp. Source is GitHub API.
  source: loa-grimoire/context/echelon_context.md:29-34
  tags: [phase1, data]
