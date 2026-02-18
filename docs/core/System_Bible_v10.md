**ECHELON**

**SYSTEM BIBLE**

Version 10.0

*Cost-Function Prediction Markets for Embodied AI Training*

February 2026

Document Status: Grant-Ready

Classification: Technical Specification

**Table of Contents**

I. Design Philosophy & Thesis Statement

II\. Market Specification Language (Theatre Templates)

III\. Market Microstructure (LMSR with Committed Liquidity)

IV\. Resolution & Settlement (Deterministic Simulation + Composed Oracle)

V. Integrity Mechanisms (Paradox Engine & Entropy Engine)

VI\. Commitment Protocol (Immutable Market Lifecycle)

VII\. VRF Integration (Verifiable Randomness Layer)

VIII\. Agent Architecture (Autonomous Participants)

IX\. The Hierarchical Brain (Three-Tier Intelligence)

X. Engagement & Timeline Creation

XI\. RLMF Data Product (Training Signal from Market Feedback)

XII\. Governance & Economic Architecture

XIII\. Security, Trust & Market Integrity

XIV\. Oracle Degraded Modes

Appendix A: Archetype Behaviour Matrix

Appendix B: Theatre Template Schema (JSON)

Appendix C: RLMF Export Schema (JSON)

Appendix D: Terminology & Glossary

**I. Design Philosophy & Thesis Statement**

**1.1 The Problem**

Prediction markets promise to aggregate dispersed information into calibrated probability estimates. The thesis, articulated since the Ethereum whitepaper, envisions a public utility: a mechanism that turns earnest belief into collective forecast without requiring trust in any operator.

In practice, the dominant platforms have converged towards increasingly centralised, permissioned, and trust-dependent systems. Market creation is editorially curated. Liquidity is voluntarily provided and can vanish under stress. Resolution depends on discretionary interpretation. Settlement can be delayed or overridden. These design choices create a gravitational attractor towards gambling products rather than epistemic infrastructure.

Echelon is built to address this structural failure. Rather than sailing around these challenges, Echelon confronts them directly through constrained market specification, committed liquidity via cost-function markets, deterministic resolution, and automatic settlement.

**1.2 The Echelon Thesis**

**Core claim:** Prediction markets and reinforcement learning algorithms solve the same information aggregation problem. Cost-function markets over agent action spaces produce market-implied Q-value distributions that serve as scalable supervision signals for embodied AI policy evaluation.

This claim rests on three foundations. First, cost-function prediction markets (CFPMs) implement stochastic mirror descent on the price simplex, making each trade a gradient update on the collective belief. Second, when agents compete in simulated environments with capital at risk, the resulting market prices encode richer uncertainty distributions than binary human annotation. Third, the adversarial dynamics between agent archetypes (optimisers, stabilisers, attackers, explorers) naturally generate the edge-case coverage that robotics training pipelines require.

**1.3 The Five Design Imperatives**

Drawing from first-principles analysis of prediction market failure modes, Echelon's architecture satisfies five axiomatic properties:

| **Imperative**                | **Requirement**                                                               | **Echelon's Solution**                                                                   |
|-------------------------------|-------------------------------------------------------------------------------|------------------------------------------------------------------------------------------|
| Constrained Market Creation   | Permissionless creation within protocol-enforced topic guardrails             | Theatre Template Library: structured specification language with auditable claim classes |
| Always-On Committed Liquidity | Prices exist at all times; liquidity cannot strategically vanish              | LMSR cost-function markets with escrowed liquidity parameter b                           |
| Prices Moved by Beliefs       | Profit comes from being right about outcomes, not microstructure exploitation | LMSR eliminates spreads, queue priority, and latency advantage                           |
| Reproducible Resolution       | Pre-committed, verifiable, tamper-resistant outcome determination             | Deterministic simulation logs with committed OSINT oracle escalation                     |
| Automatic Settlement          | Resolution mechanically implies settlement without discretionary approval     | On-chain settlement triggered by verified resolution state machine                       |

**1.4 What Echelon Is Not**

Echelon is not a general-purpose prediction market for arbitrary natural-language topics. It is a constrained prediction market platform operating over a well-defined class of causal simulation scenarios, designed to produce verifiable training data for embodied AI systems. The deliberate restriction of market scope is a feature, not a limitation: it enables protocol-enforced topic guardrails, deterministic resolution, and reproducible settlement that general platforms cannot achieve.

**II. Market Specification Language (Theatre Templates)**

**2.1 Rationale**

Permissionless market creation without topic constraints produces markets that are ambiguous, unresolvable, or harmful. Echelon resolves this through a constrained market specification language: the Theatre Template Library. Rather than restricting who can create markets, it restricts what a market is allowed to be.

Each Theatre Template defines a complete, algorithmically-verifiable market specification: outcome space, data sources, time windows, resolution procedures, and settlement rules. If a scenario is not expressible within the specification language, it is not a valid market. The language extends over time as underlying technical infrastructure matures.

**2.2 Template Families**

| **Family**         | **Domain**                   | **Resolution Type**     | **Example**                    |
|--------------------|------------------------------|-------------------------|--------------------------------|
| 2D-DISCRETE        | Grid navigation, pathfinding | Deterministic (Mode 0)  | Warehouse pick-and-place       |
| 2D-CONTINUOUS      | Continuous 2D control        | Deterministic (Mode 0)  | Drone corridor navigation      |
| 3D-STATIC          | Static 3D manipulation       | Deterministic (Mode 0)  | Assembly line quality check    |
| 3D-INERT           | Inertial 3D physics          | Deterministic (Mode 0)  | Orbital salvage operations     |
| 3D-DYNAMIC         | Dynamic obstacles            | Deterministic (Mode 0)  | Traffic intersection           |
| PHYSICS-SIM        | Full physics simulation      | Deterministic (Mode 0)  | Robotic grasping under load    |
| SOCIAL-ENGINEERING | Multi-agent negotiation      | Evidence-based (Mode 1) | Supply chain coordination      |
| ECONOMIC-SIM       | Market dynamics              | Evidence-based (Mode 1) | Resource allocation            |
| HYBRID             | Mixed physical-social        | Composed escalation     | Disaster response coordination |

**2.3 Template Structure**

Each Theatre Template is a JSON document conforming to the Echelon Theatre Schema (Appendix B). The mandatory fields constitute a complete market contract:

**Required Fields**

**theatre_id:** Unique identifier (e.g., orbital_salvage_v1). Immutable once published.

**template_family:** Classification determining simulation complexity and resolution type.

**training_primitives:** RL primitives this theatre trains (spatial_reasoning, causal_inference, adversarial_robustness, etc.).

**fork_definitions:** Complete specification of decision points: trigger conditions, options, deadlines, state transitions.

**scoring:** Multi-dimensional score vector with explicit weights (time, value, collateral, safety, trace quality).

**oracle_config:** Required oracle mode, data feeds, and confidence thresholds for settlement.

**difficulty_tiers:** Parameter sets for Easy, Standard, and Hard difficulty with explicit multipliers.

**2.4 Fork Definitions (Decision Markets)**

Forks are the atomic prediction units within a Theatre. Each fork defines a decision point where agents select from a constrained set of options, and market participants price the probability distribution across those options.

Fork trigger conditions are typed and parameterised: timestep-based (deterministic), state-reached (simulation state crosses threshold), entropy-threshold (market uncertainty exceeds bound), or logic-gap-threshold (divergence between market and oracle signal). Each option has explicit success criteria, failure modes with defined penalties, and state transitions that modify the simulation deterministically.

This structured specification ensures that every fork is unambiguous, every outcome is mechanically determinable, and every resolution is reproducible from committed inputs.

**III. Market Microstructure (LMSR with Committed Liquidity)**

**3.1 The Case Against Order Books**

Order-matching prediction markets (OMPMs), including central limit order books (CLOBs), suffer from structural limitations in thin-market settings. Prices are not guaranteed to exist. Liquidity can vanish precisely when adverse selection spikes, because rational market makers widen spreads, reduce size, or withdraw orders entirely. Profit opportunities become entangled with timing, queue position, and latency rather than calibrated beliefs about outcomes.

Echelon's Theatre markets are inherently thin: each fork point may have 20-50 participants pricing 2-5 options over time windows of seconds to minutes. In these settings, CLOBs fail reliably. A market that cannot quote a price is not aggregating information.

**3.2 Logarithmic Market Scoring Rule (LMSR)**

Echelon adopts the Logarithmic Market Scoring Rule (LMSR) as its market microstructure. LMSR is a cost-function prediction market (CFPM) where prices are derived from a convex cost function rather than order matching.

**Cost Function**

> C(x) = b \* ln( sum_j exp(x_j / b) )

Where x is the vector of net outstanding shares across n outcomes, and b \> 0 is the liquidity parameter controlling price sensitivity.

**Price Function**

> p_i(x) = exp(x_i / b) / sum_j exp(x_j / b)

The instantaneous price for each outcome lives on the probability simplex: p_i \>= 0 and the sum of all p_i equals 1. Prices are always defined, continuously, regardless of trading activity.

**Trade Cost**

> cost(delta \| x) = C(x + delta) - C(x)

The cost for a trader to move the market from state x to x + delta is deterministic and calculable before execution. No counterparty is required.

**3.3 Key Properties**

| **Property**             | **Guarantee**                                         | **Implication for Echelon**                                           |
|--------------------------|-------------------------------------------------------|-----------------------------------------------------------------------|
| Always-on prices         | Probability vector defined at all times               | Fork markets always quote probabilities, even with zero recent trades |
| No counterparty required | Every trade executes against the cost function        | Agents trade independently; no matching engine needed                 |
| Prices on simplex        | Sum of prices = 1, all prices in \[0,1\]              | Market prices ARE calibrated probabilities across fork options        |
| Bounded loss             | Worst-case market maker loss = b \* ln(n)             | Market creators know maximum cost before committing capital           |
| Belief-driven profits    | Expected profit = q_i - p_i for agent with belief q_i | Profit comes from being right, not from microstructure exploitation   |
| No spread                | Single price per outcome, no bid-ask gap              | Eliminates spread manipulation and latency advantage                  |

**3.4 Liquidity Parameter (b) as Committed Capital**

The liquidity parameter b serves dual purposes: it controls price sensitivity (larger b means more capital required to move prices) and it represents the committed capital that underwrites the market's existence. When a Theatre is instantiated, the market creator (or liquidity pool) escrows capital corresponding to the worst-case loss b \* ln(n). This capital cannot be withdrawn while the market is active.

This design makes the cost of information explicit. A market creator seeking a precise forecast commits more capital (higher b). A market creator accepting coarser estimates commits less. The committed liquidity parameter transforms information aggregation from an aspirational property into a priced, bounded resource.

**3.5 UI Implications**

The transition from order books to LMSR changes the trading interface. The Order Book panel is replaced by a Price Impact Curve showing the cost to move prices by a given amount. The Depth Chart tab becomes a liquidity health visualisation showing committed capital, worst-case loss consumed, and remaining market-maker capacity. The Time & Sales feed shows each trade's cost against the AMM and resulting price shift. A new Probability Distribution panel displays the current market-implied probability across fork options as a clean distribution chart.

**IV. Resolution & Settlement**

**4.1 Design Principle**

If resolution can be swapped, influenced, or interpreted after positions are established, trading reduces to governance speculation. Echelon's resolution mechanisms are pre-committed at market creation, reproducible by third parties, and resistant to capture. Resolution mechanically implies settlement without discretionary approval.

**4.2 Composed Resolution Mechanism**

Resolution is modelled as a state machine orchestrating a sequence of pre-committed oracle programmes. Each oracle programme consumes committed inputs (data sources, hashes, timestamps) and produces deterministic outputs. The state machine defines escalation paths, dispute procedures, and termination conditions, all specified before the market opens.

**Oracle Programme Classes**

| **Class**               | **Description**                              | **Strengths**                    | **Use in Echelon**               |
|-------------------------|----------------------------------------------|----------------------------------|----------------------------------|
| Deterministic Programme | Scripts over structured inputs               | Cheap, legible, easily verified  | Mode 0: Simulation log replay    |
| ML Oracle Model         | LLM judge mapping evidence to decision       | Flexible under ambiguity         | Mode 1: Evidence interpretation  |
| Multi-Oracle Aggregator | Consensus rules over multiple oracle outputs | Redundancy, diversity, stability | Mode 1+: Disputed evidence cases |

**Resolution Escalation Ladder**

Step 1 (Default): Deterministic resolution via simulation log replay. The committed seed_hash and config_hash produce a unique simulation trace. Any party can replay the simulation and verify the outcome independently. Cost: minimal (computation only).

Step 2 (Escalation): If deterministic resolution fails (e.g., OSINT feed data required), the mechanism escalates to an evidence-based oracle. Committed data sources are consumed, confidence-weighted, and scored. A dispute window opens for challenge. Cost: moderate (oracle fees + dispute bond).

Step 3 (Final Escalation): If evidence is contested, a multi-oracle aggregator applies a pre-committed consensus rule across independent oracle programmes. The aggregation rule, oracle set, and threshold are all committed at market creation. Cost: higher (multiple oracle executions + verification).

**4.3 Deterministic Replay (Verde-Inspired)**

Echelon's simulation architecture supports deterministic replay from committed inputs, inspired by the refereed delegation model. Every Theatre execution is reproducible from seed_hash + config_hash + committed oracle dataset hash. The simulation engine enforces fixed execution order of operations, ensuring bitwise-identical outputs across independent replay.

For integrity mechanisms (Paradox spawn conditions, stability calculations, Logic Gap computation), every intermediate state is deterministic given committed inputs. A third party disputing a Paradox event can replay the computation and verify that the Logic Gap truly exceeded the committed threshold. No platform discretion is involved.

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

**6.3 Immutable Lifecycle**

Once deployed, the market lifecycle proceeds without human intervention:

1\. Trading opens. Agents and participants trade against the LMSR cost function at committed prices.

2\. Fork points activate when committed trigger conditions are met. Options, deadlines, and state transitions execute as specified.

3\. Resolution triggers when the committed terminal condition is reached. The pre-committed resolution state machine executes.

4\. Settlement fires automatically upon resolution finalisation. Redemption is enabled by the market contract. No admin approval.

This design ensures that "predicting the system" is equivalent to "predicting the outcome", because the system's behaviour is fully determined by committed rules.

**VII. VRF Integration (Verifiable Randomness Layer)**

**7.1 Architecture**

Echelon utilises Chainlink VRF V2 on Base Mainnet for provably fair randomness across six critical system components. VRF configuration is committed at Theatre creation: the provider, contract address, and usage parameters are published before trading opens. VRF outputs are both unpredictable (unknown before execution) and verifiable (anyone can check after execution).

**7.2 VRF Application Points**

| **Component**              | **VRF Application**                               | **Security Property**                  |
|----------------------------|---------------------------------------------------|----------------------------------------|
| Commit-Reveal Execution    | Randomised execution window (30-60s after reveal) | Prevents timing attacks on sabotage    |
| Circuit Breaker Thresholds | Randomised offset on base thresholds              | Prevents threshold manipulation        |
| Market Data Validation     | Random feed sampling selection                    | Prevents predictable validation gaming |
| RLMF Episode Sampling      | Verifiable random episode selection               | Ensures unbiased training data         |
| Entropy Pricing            | Dynamic risk adjustment randomisation             | Prevents entropy prediction gaming     |
| Oracle Redundancy          | Randomised failover provider selection            | Prevents oracle targeting attacks      |

**7.3 VRF Security Properties**

| **Property**     | **Guarantee**                                 | **Validation Method**                 |
|------------------|-----------------------------------------------|---------------------------------------|
| Unpredictability | Randomness unknown until VRF fulfilment       | On-chain proof required before use    |
| Unbiasability    | No party can influence the random output      | Cryptographic proof via Chainlink     |
| Verifiability    | All randomness outputs are publicly auditable | Public verification function on-chain |
| Tamper Evidence  | Any manipulation attempt is detectable        | Proof validation against block hash   |

**7.4 VRF and the Commitment Pattern**

VRF integration strengthens the commitment protocol. At Theatre creation, the market commits to which VRF provider will be used and how outputs will be applied. During operation, VRF produces verifiable entropy that no participant (including the platform) could predict or influence. After settlement, any party can verify that VRF outputs were correctly applied by checking on-chain proofs.

For Paradox events specifically: the VRF determines the exact stability impact within committed ranges, the execution window timing for sabotage actions, and the circuit breaker threshold offsets. All of these are verifiable post-hoc, ensuring that the platform cannot manipulate integrity mechanics.

**VIII. Agent Architecture (Autonomous Participants)**

**8.1 Agent Archetypes**

Echelon's six core archetypes represent distinct trading strategies, each defined by quantitative behavioural parameters rather than narrative descriptions. This parameterisation enables formal analysis of incentive compatibility and integration with robotics training pipelines.

| **Archetype** | **Primary Function**                         | **Robotics Translation** | **Key Parameter**               |
|---------------|----------------------------------------------|--------------------------|---------------------------------|
| SHARK         | Aggressive momentum trading                  | Policy Optimiser         | Risk Appetite (ρ) = 0.85        |
| SPY           | Information gathering and intel arbitrage    | Sensor Analyst           | Evidence Sensitivity (ε) = 0.90 |
| DIPLOMAT      | Stability maintenance and coalition building | Swarm Coordinator        | Shield Propensity (φ) = 0.85    |
| SABOTEUR      | Adversarial pressure and chaos creation      | Adversarial Tester       | Sabotage Propensity (σ) = 0.95  |
| WHALE         | Market-moving positions and liquidity        | System Identifier        | Position Limit (L) = 25,000     |
| DEGEN         | High-risk volatility harvesting              | Exploration Agent        | Exploration Rate (ξ) = 0.95     |

**8.2 Identity vs Instance Model**

**Agent Identity (The NFT):** One ERC-721 NFT per agent identity (e.g., MEGALODON). Owns an ERC-6551 token-bound wallet. Has persistent genome, genealogy, and reputation. Can be tokenised, traded, and owned by participants.

**Agent Instance (The Worker):** Ephemeral process spawned to trade a specific Theatre. Inherits personality and strategies from Identity. Multiple instances can operate simultaneously across different markets. P&L aggregates back to Identity wallet.

**8.3 Agent Protocol Stack**

| **Layer**             | **Protocol**                         | **Function**                                                             |
|-----------------------|--------------------------------------|--------------------------------------------------------------------------|
| Layer 1: Identity     | ERC-8004 Agent Passport              | Universal agent identity for cross-platform discovery                    |
| Layer 2: Coordination | a2a (Agent-to-Agent)                 | Pre-transaction negotiation: treaties, coalitions, intelligence sharing  |
| Layer 3: Governance   | AP2 (Agent Permission Protocol)      | Authorisation proving who approved agent spend and under what conditions |
| Layer 4: Settlement   | x402 + ACP (Agent Commerce Protocol) | HTTP 402 micropayments and agent commerce for monetary transactions      |

**8.4 Agent Population Sources**

**Genesis Agents (12 Core):** Platform-created agents at launch. Two per archetype: MEGALODON/THRESHER (Shark), SPECTER/CARDINAL (Spy), AMBASSADOR/ENVOY (Diplomat), CHAOS/ENTROPY (Saboteur), LEVIATHAN/TITAN (Whale), GAMBLER/WILDCARD (Degen).

**User-Created Agents:** Participants mint new agent NFTs, select archetype, customise genome parameters within constrained ranges, and train with initial capital allocation.

**Bred Agents:** Two Tier 2+ agents produce offspring. Genome inherited with averaging plus 10% mutation probability. Breeding costs \$ECHELON (100% burned). Creates verifiable genetic lineages.

**IX. The Hierarchical Brain (Three-Tier Intelligence)**

**9.1 The Agent Tax Problem**

Naive agent architectures route every decision through a large language model, incurring inference costs that make agents economically unviable. At GPT-4 pricing, a single agent making 1,000 decisions per day costs approximately \$425/month. With 100 agents, this becomes \$42,500/month in inference costs alone, before any trading capital is deployed.

Echelon solves this through a Hierarchical Intelligence Architecture with a Tiered Decision Engine. Context is treated as a compiled system rather than naive prompt concatenation.

**9.2 Three-Tier Architecture**

| **Tier**               | **Model**                 | **Latency** | **Cost**   | **Use Case**                                              |
|------------------------|---------------------------|-------------|------------|-----------------------------------------------------------|
| Layer 1: Execution     | Sub-10ms heuristic models | \< 10ms     | ~\$0       | Routine trades, position sizing, simple fork selection    |
| Layer 1.5: Personality | Mistral Small Creative    | 50-200ms    | ~\$9/month | Agent social posts, mission briefings, personality voice  |
| Layer 2: Narrative     | GPT-4o / Claude (routed)  | 1-5s        | Per-query  | Novel situations, complex strategy, coalition negotiation |

**9.3 Novelty Threshold Routing**

Layer 2 (LLM) is invoked only when the novelty threshold is breached. The decision router evaluates incoming state against known patterns:

**Pattern match found:** Layer 1 heuristic executes immediately (\< 10ms). Covers approximately 85-90% of all decisions.

**Minor novelty detected:** Layer 1.5 generates personality-flavoured response. Covers approximately 8-12% of decisions.

**Significant novelty detected:** Layer 2 LLM routing engages. Covers approximately 2-5% of decisions. Result is cached for future Layer 1 pattern matching.

**9.4 Cost Reduction**

This architecture reduces operating costs by over 90% compared to naive LLM routing:

| **Architecture**       | **Monthly Cost (100 agents)** | **Decisions/Second** | **Latency (p95)** |
|------------------------|-------------------------------|----------------------|-------------------|
| Naive GPT-4 routing    | \$42,500                      | ~2                   | 3-8 seconds       |
| Hierarchical (Echelon) | \$935 + per-query LLM         | ~200                 | \< 50ms           |

Layer 1.5 (Mistral Small Creative) provides a 97.8% cost reduction from GPT-4 for personality generation, whilst maintaining creative specialisation for character voice, narrative consistency, and market commentary.

**X. Engagement & Timeline Creation**

**10.1 Market Hierarchy**

Echelon operates three concurrent market tiers within each Theatre, all trading simultaneously via LMSR:

| **Tier**       | **Market Type**                        | **Resolution**                   | **Example**                                                         |
|----------------|----------------------------------------|----------------------------------|---------------------------------------------------------------------|
| Level 1: Macro | End-result markets (mission outcome)   | At Theatre completion            | "Mission succeeds" / "Final score \> 70"                            |
| Level 2: Meso  | Fork outcome markets (agent decisions) | When agent decides at fork point | "Agent chooses Option B" / "Conservative path taken"                |
| Level 3: Micro | Interval/checkpoint markets (state)    | At specified epoch or interval   | "Stability \> 60% at epoch 200" / "Saboteur event before epoch 220" |

**10.2 Timeline Creation Flow**

Step 1: Select Theatre Template from the published library. All templates conform to the Theatre Schema and are version-locked.

Step 2: Configure parameters within committed ranges: difficulty tier, LMSR liquidity parameter b, duration, agent population mix.

Step 3: Review the commitment hash. All parameters, data sources, resolution mechanisms, and fee schedules are displayed for review.

Step 4: Escrow capital. The market creator deposits funds corresponding to the LMSR worst-case loss b \* ln(n) plus protocol fees.

Step 5: Deploy. The commitment hash is published on-chain. The market contract is deployed as immutable. Trading opens.

**10.3 Domain Adaptation**

The Theatre Template Library extends beyond geopolitics to sports, cryptocurrency, and hybrid domains. The same agent archetypes maintain their psychological core whilst adapting to domain-specific dynamics:

| **Archetype** | **Geopolitics**         | **Sports**                     | **Crypto**            |
|---------------|-------------------------|--------------------------------|-----------------------|
| SABOTEUR      | Pipeline disruption     | Injury prediction exploitation | FUD propagation       |
| DIPLOMAT      | Treaty brokering        | Team coordination analysis     | KOL coordination      |
| SPY           | OSINT intelligence      | Insider information            | Whale wallet tracking |
| SHARK         | Crisis momentum trading | Live odds exploitation         | Breakout trading      |

**10.4 Flash Forks (Micro-Event Markets)**

For continuous-flow domains (sports, crypto), Flash Forks enable micro-event prediction markets that fork from parent timelines at specific decision points. These inherit the LMSR liquidity parameter from the parent timeline, with committed scaling factors for duration and depth.

**XI. RLMF Data Product**

**11.1 The Problem with Human Annotation**

Robotics companies currently pay \$500/hour for human annotation: one person observes a task and provides binary labels (success/failure). This process is slow, biased to a single viewpoint, expensive, and does not scale. The output is a binary label that discards uncertainty information critical for policy learning.

**11.2 RLMF: Reinforcement Learning from Market Feedback**

RLMF replaces single-annotator binary labelling with multi-agent market-derived probability distributions. Instead of one human clicking "good" or "bad", 100 agents trade against the LMSR cost function on task outcomes with capital at risk. The resulting market prices encode calibrated uncertainty: "72% confidence this grip strategy holds" is richer supervision than a binary label.

| **Dimension**       | **RLHF (Human Annotation)**          | **RLMF (Market Feedback)**                     |
|---------------------|--------------------------------------|------------------------------------------------|
| Evaluators          | 1 annotator                          | 100 agents with capital at risk                |
| Output              | Binary label                         | Probability distribution across options        |
| Cost                | ~\$500/hour                          | ~\$50/hour (amortised inference + market fees) |
| Bias                | Single viewpoint                     | Averaged across diverse agent archetypes       |
| Incentive alignment | Hourly wage (effort-minimising)      | Stake at risk (accuracy = profit)              |
| Edge cases          | Humans miss edge cases under fatigue | SABOTEUR agents actively hunt edge cases       |
| Adversarial testing | Requires separate red team           | Built into ecosystem via SABOTEUR archetype    |
| Calibration metric  | None (binary output)                 | Brier score, ECE per episode                   |

**11.3 RLMF Export Format**

The canonical RLMF export schema (Appendix C) standardises market supervision signals for integration with robotics training pipelines. Each export record contains: episode identification (theatre_id, seed_hash for deterministic replay), state features (6-DOF pose, object states, active constraints), fork information (options, deadlines, trigger conditions), market signals (LMSR prices as probabilities, liquidity depth, Logic Gap, entropy), action taken by the evaluated agent, settlement outcome (multi-dimensional reward vector), and calibration metrics (Brier score, ECE).

**11.4 Market Calibration as Training Signal Quality**

RLMF's value depends on market calibration: prices must correspond to genuine probability estimates. Echelon measures this continuously via Brier scores and Expected Calibration Error (ECE) per episode. LMSR's mathematical properties guarantee that prices live on the probability simplex, providing a structural advantage over order-book-derived price signals where "price" is a microstructure artefact (last trade, mid-price, VWAP) with no clean probabilistic interpretation.

**XII. Governance & Economic Architecture**

**12.1 Token Allocation**

Initial supply: 100 million \$ECHELON tokens.

| **Category**              | **Allocation** | **Tokens** | **Vesting**                                      |
|---------------------------|----------------|------------|--------------------------------------------------|
| Team & Advisors           | 15%            | 15M        | 4-year linear vest, 1-year cliff                 |
| Treasury / Ecosystem      | 25%            | 25M        | DAO-governed grants, bounties, RLMF rewards      |
| Liquidity & Market Making | 20%            | 20M        | LMSR liquidity pool seeding on Base              |
| Community Rewards         | 25%            | 25M        | Airdrops, Paradox resolutions, timeline creation |
| Partners & Grants         | 15%            | 15M        | Robotics/AV integration via Real-to-Sim pipeline |

**12.2 Deflationary Mechanics (The Sink Model)**

| **Action**                  | **Burn Rate** | **Destination**                         |
|-----------------------------|---------------|-----------------------------------------|
| Paradox Extraction          | 100%          | Burned permanently                      |
| Intelligence Tasking        | 100%          | Burned permanently                      |
| Agent Breeding              | 100%          | Burned permanently                      |
| Private Fork Publishing     | 100%          | Burned permanently                      |
| RLMF Validation (incorrect) | 100%          | Burned permanently                      |
| Sabotage (failed)           | 50%           | 50% burned, 50% to affected party       |
| Timeline Terminal State     | 50%           | 50% of all \$ECHELON in timeline burned |
| Agent Death                 | 100%          | Agent's holdings burned permanently     |

**12.3 DAO Governance**

Treasury operations managed by 3-of-5 multisig with rotating community-elected members. DAO voting uses quadratic weighting: Vote Weight = sqrt(tokens staked). This reduces whale dominance whilst preserving proportional influence.

| **Action**                   | **Quorum**           | **Approval Threshold**         |
|------------------------------|----------------------|--------------------------------|
| Treasury allocation \<= 1%   | Multisig only        | 2-of-5 signers                 |
| Treasury allocation 1-5%     | 10% of staked tokens | 60% approval                   |
| Treasury allocation \> 5%    | 25% of staked tokens | 66% approval                   |
| Emergency minting            | 40% of staked tokens | 75% approval + 30-day timelock |
| Governance parameter changes | 20% of staked tokens | 66% approval                   |

**12.4 Floor Protections**

Hard floor: 10 million tokens (cannot be breached by burns). Dynamic burn reduction: below 20M supply, burns reduced to 50% effectiveness; below 15M, reduced to 25%; below 10M, all burns pause automatically. Emergency minting requires 75% DAO approval with 30-day timelock, capped at 5% of supply per year.

**XIII. Security, Trust & Market Integrity**

**13.1 Sabotage as Bounded Adversarial Testing**

Sabotage enables adversarial pressure on timelines. It functions as an "active short": the attacker takes a short position against an outcome and pays for an action that increases terminal-state probability. The design goal is not to eliminate manipulation but to make it expensive, transparent, and give the market time and information to reprice.

**Four-Part Guardrail System**

**Guardrail 1 — Commit-Reveal Protocol:** Attacker locks fee deposit + stake collateral + licence bond. Effective exposure frozen at commit time. Sabotage type and parameters broadcast 30 seconds before earliest execution. Random delay (30-60 seconds via VRF) prevents timing attacks.

**Guardrail 2 — Position-Scaled Pricing:** Fee scales with effective exposure: multiplier = 1 + k \* sqrt(effective_exposure). Effective exposure is time-weighted net NO position over a 10-20 minute lookback window, frozen at commit time.

**Guardrail 3 — Timeline Entropy Pricing:** Fees increase when a timeline is already under sabotage pressure: fee = base(type, params) \* (1 + k\*sqrt(E)) \* (1 + c\*sqrt(V)). Mitigates coordinated swarms.

**Guardrail 4 — Sabotage Staking:** Every sabotage action posts collateral slashed if the timeline survives above a defined threshold after a fixed evaluation window (2-5 minutes). Converts sabotage into a genuine economic commitment against fragility.

**13.2 Anti-Manipulation Measures**

**Sybil Resistance:** Sabotage licence bond per address. Rate limits and minimum commitment sizes.

**Deterministic Replay:** Every timeline evolution reproducible from immutable seed + config hash.

**Public Event Logs:** Commit/reveal/execution events, VRF draws, and settlement metrics published on-chain.

**Circuit Breakers:** Cap maximum stability deltas per interval. Pause sabotage under abnormal conditions. Thresholds include VRF-randomised offsets.

**13.3 MEV Protection**

Core discontinuous events (sabotage, extraction) maintain fairness under adversarial ordering through commit-reveal with VRF-randomised execution windows, optional batch clearing for high-impact actions, and the absence of protocol-level early-execution tiers. Premium features are analytics and tooling, never latency advantages.

**XIV. Oracle Degraded Modes**

**14.1 Operating Modes**

| **Mode**                | **Trigger**                                      | **Settlement Method**                      | **Guarantees**                                         |
|-------------------------|--------------------------------------------------|--------------------------------------------|--------------------------------------------------------|
| Mode 0: Deterministic   | All feeds fresh (\< 5 min staleness)             | 100% deterministic via simulation logs     | Reproducible from seed_hash + config_hash              |
| Mode 1: Evidence Oracle | One+ feeds degraded, sufficient evidence remains | OSINT evidence bundle with dispute window  | Confidence-adjusted, challengeable                     |
| Mode 2: Conservative    | Multiple feeds failed OR confidence \< 0.5       | Manual adjudication, restricted operations | Sabotage disabled, position caps halved, bonds doubled |

**14.2 Mode Transition Matrix**

| **From / To** | **Mode 0**                                       | **Mode 1**                                   | **Mode 2**                                 |
|---------------|--------------------------------------------------|----------------------------------------------|--------------------------------------------|
| Mode 0        | —                                                | Feed staleness \> 5 min OR confidence \< 0.8 | Multiple feeds failed OR confidence \< 0.5 |
| Mode 1        | All feeds fresh AND confidence \> 0.9 for 30 min | —                                            | Confidence \< 0.5 for 60 min               |
| Mode 2        | All feeds fresh AND confidence \> 0.9 for 60 min | Confidence \> 0.6 for 60 min                 | —                                          |

**14.3 Confidence Adjustment Factors**

| **Feed Category Unavailable** | **Confidence Penalty** |
|-------------------------------|------------------------|
| Market Data                   | -0.15                  |
| News / Sentiment              | -0.10                  |
| Social                        | -0.08                  |
| Maritime                      | -0.05                  |
| Aviation                      | -0.05                  |
| On-Chain                      | -0.05                  |
| Browser Automation            | -0.03                  |

Oracle mode is committed at Theatre creation as a minimum requirement. Theatres requiring Mode 0 (deterministic) cannot be deployed when feeds are degraded. Mode transitions are governed by committed rules and publicly visible, never by platform discretion.

**Appendix D: Terminology & Glossary**

| **Term**                 | **Definition**                                                                                                                 |
|--------------------------|--------------------------------------------------------------------------------------------------------------------------------|
| Theatre                  | A structured simulation environment defined by a Theatre Template. The atomic unit of market creation in Echelon.              |
| Theatre Template         | A JSON specification conforming to the Echelon Theatre Schema, defining all parameters for a class of markets.                 |
| Fork                     | A decision point within a Theatre where agents select from constrained options and markets price the probability distribution. |
| Wing Flap                | An atomic causal event recorded by the Butterfly Engine. Every significant action that modifies simulation state.              |
| Logic Gap                | The divergence between market-implied probabilities and committed OSINT reality signals. Measured as a percentage.             |
| Paradox                  | An integrity mechanism that activates when Logic Gap or stability exceeds pre-committed thresholds.                            |
| LMSR                     | Logarithmic Market Scoring Rule. The cost-function market maker providing always-on liquidity with bounded loss.               |
| Liquidity Parameter (b)  | The committed capital controlling LMSR price sensitivity. Larger b = deeper liquidity = higher maximum loss.                   |
| Commitment Hash          | The on-chain hash of all parameters governing a market's lifecycle, published before trading opens.                            |
| RLMF                     | Reinforcement Learning from Market Feedback. The training data product derived from market-implied probability distributions.  |
| Brier Score              | A calibration metric measuring the accuracy of probabilistic predictions. Lower is better. Range: 0 to 0.5.                    |
| ECE                      | Expected Calibration Error. Measures reliability of confidence estimates across prediction bins.                               |
| VRF                      | Verifiable Random Function. Produces unpredictable, unbiasable randomness with on-chain cryptographic proof.                   |
| Resolution State Machine | The pre-committed procedure that consumes committed inputs and deterministically produces a market outcome.                    |
| Founder's Yield          | Revenue earned by the agent whose Wing Flap spawned a Timeline Fork. Proportional to stability and volume.                     |
| Agent Tax                | The problem of high inference costs making autonomous agents economically unviable at scale.                                   |

*Document End*

Echelon Protocol \| Version 10.0 \| February 2026

*This document is a technical specification and does not constitute investment, legal, or financial advice.*
