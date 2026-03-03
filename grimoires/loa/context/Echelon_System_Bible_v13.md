**ECHELON**

**SYSTEM BIBLE**

Version 13.0

*Evidence-Backed Resolution Markets & Deterministic Verification Infrastructure*

February 2026

Document Status: Grant-Ready

Classification: Technical Specification

Change Log (v12 → v13): Reframed core model from "counterfactual prediction markets" to "bounded inquiries" — timelines are now the universal primitive encompassing counterfactual, investigative, inspection, survey, and scrutiny inquiry types. Updated Section I (thesis and scope). Added inquiry type taxonomy to Section II. Rewrote Section X as "Engagement & Bounded Inquiries" with five inquiry classes and investigative tooling concept. Updated Section XVII positioning. Added 9 glossary terms (Appendix E). Prior changelog preserved below.

Change Log (v11 → v12): Added Section XV (OSINT Source Registry & Composed Oracle), Section XVI (Verification Infrastructure), Section XVII (Integration Architecture & Market Entry Wedge). Updated template families (§II) to reflect 4 proven verticals and 10 templates. Expanded calibration certificate schema (Appendix D) with cold-path consumption notes. Added Appendix F (Issued Certificates Register). Updated glossary (Appendix E) with 18 new terms.

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

X. Engagement & Bounded Inquiries

XI\. RLMF Data Product (Training Signal from Market Feedback)

XII\. Governance & Economic Architecture

XIII\. Security, Trust & Market Integrity

XIV\. Oracle Degraded Modes

XV\. OSINT Source Registry & Composed Oracle

XVI\. Verification Infrastructure

XVII\. Integration Architecture & Market Entry Wedge

Appendix A: Archetype Behaviour Matrix

Appendix B: Theatre Template Schema (JSON) — v2.0.1

Appendix C: RLMF Export Schema (JSON) — v2.0.1

Appendix D: Calibration Certificate Schema — v1.0.0

Appendix E: Terminology & Glossary

Appendix F: Issued Certificates Register

**I. Design Philosophy & Thesis Statement**

**1.1 The Problem**

Prediction markets promise to aggregate dispersed information into calibrated probability estimates. The thesis, articulated since the Ethereum whitepaper, envisions a public utility: a mechanism that turns earnest belief into collective forecast without requiring trust in any operator.

In practice, the dominant platforms have converged towards increasingly centralised, permissioned, and trust-dependent systems. Market creation is editorially curated. Liquidity is voluntarily provided and can vanish under stress. Resolution depends on discretionary interpretation. Settlement can be delayed or overridden. These design choices create a gravitational attractor towards gambling products rather than epistemic infrastructure.

At the same time, a parallel failure is emerging in AI agent economies: multi-model orchestration, routing decisions, and agent capability claims are all procedural — performed but never verified. Systems like Perplexity's Model Council run queries across multiple models and synthesise answers, but the synthesis is itself unaudited. Permissionless market creation platforms (Gensyn, April 2026) promise AI-powered settlement, but the settlement logic is opaque. The question "why should I trust this resolution?" has no auditable answer.

Echelon is built to address both structural failures. Rather than sailing around these challenges, Echelon confronts them directly through constrained market specification, committed liquidity via cost-function markets, deterministic resolution, and automatic settlement. The unifying primitive is the **bounded inquiry**: a time-limited, evidence-committed investigation with certifiable resolution.

**1.2 The Echelon Thesis**

**Core claim:** Bounded inquiries with committed evidence bases, deterministic scoring, and certifiable resolution produce superior information aggregation, training signals, and verification artefacts compared to unconstrained prediction markets, binary human annotation, or procedural AI settlement.

This claim rests on four foundations. First, cost-function prediction markets (CFPMs) implement stochastic mirror descent on the price simplex, making each trade a gradient update on the collective belief. Second, when agents compete in structured environments with capital at risk, the resulting market prices encode richer uncertainty distributions than binary human annotation. Third, the adversarial dynamics between agent archetypes (optimisers, stabilisers, attackers, explorers) naturally generate the edge-case coverage that training pipelines require. Fourth, the bounded inquiry model extends beyond counterfactual scenarios to encompass investigations, inspections, surveys, and scrutiny — any inquiry where the evidence base can be committed and the resolution can be deterministically scored.

The bounded inquiry model recognises that prediction markets are one class of inquiry, not the only class. An investigative timeline (e.g., "Which company is engaged in insider trading?") uses the same Theatre Template infrastructure as a counterfactual fork (e.g., "What if the Fed had held rates?"), but the evidence accumulates through OSINT discovery rather than simulation divergence. The common thread is: committed evidence, deterministic scoring, certifiable resolution.

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

Echelon is not a general-purpose prediction market for arbitrary natural-language topics. It is a bounded inquiry platform operating over well-defined classes of evidence-committed investigations, designed to produce verifiable resolution artefacts, training data for AI systems, and auditable certification of agent capabilities. The deliberate restriction of inquiry scope is a feature, not a limitation: it enables protocol-enforced evidence guardrails, deterministic resolution, and reproducible settlement that general platforms cannot achieve.

Echelon is also not a pure simulation engine. Whilst counterfactual market simulations remain a core inquiry type, the bounded inquiry model extends to investigations (evidence discovery over real-world data), inspections (compliance verification against committed criteria), surveys (structured opinion aggregation), and scrutiny (adversarial audit of claims). All inquiry types share the same Theatre Template infrastructure, OSINT pipeline, and verification tooling.

**II. Market Specification Language (Theatre Templates)**

**2.1 Rationale**

Permissionless market creation without topic constraints produces markets that are ambiguous, unresolvable, or harmful. Echelon resolves this through a constrained market specification language: the Theatre Template Library. Rather than restricting who can create markets, it restricts what a market is allowed to be.

Each Theatre Template defines a complete, algorithmically-verifiable inquiry specification: outcome space, data sources, time windows, resolution procedures, and settlement rules. If a scenario is not expressible within the specification language, it is not a valid inquiry. The language extends over time as underlying technical infrastructure matures.

**2.2 Inquiry Types**

Echelon recognises five classes of bounded inquiry. All share the same Theatre Template infrastructure, evidence bundling, and certification pipeline. The inquiry type determines how evidence accumulates and how resolution is triggered.

| **Inquiry Type** | **Evidence Accumulation** | **Resolution Trigger** | **Example** |
|---|---|---|---|
| Counterfactual | Simulation divergence from forked real market | Simulation terminal state or OSINT evidence | "What if the Fed had held rates in January?" |
| Investigative | OSINT discovery over real-world data sources | Evidence threshold met or time window closes | "Which company is engaged in insider trading?" |
| Inspection | Compliance check against committed criteria | All criteria evaluated | "Does this property meet escrow release conditions?" |
| Survey | Structured opinion aggregation with committed methodology | Participation threshold or time window closes | "What does the market believe this asset is worth?" |
| Scrutiny | Adversarial audit of claims against committed evidence | Claim verified or falsified | "Is this project's claimed TVL accurate?" |

**2.3 Template Families**

Templates are organised into two first-class families by execution path, plus the original simulation families for robotics training. Each template specifies its inquiry type alongside its execution path and template family.

**Product Theatres (execution_path: replay)**

Product Theatres verify AI construct capabilities against engineering ground truth. They use the Replay Engine: commit parameters, invoke real construct via OracleAdapter, score output against ground truth, issue calibration certificate. No LMSR markets, no agents, no trading. Ground truth is free — a byproduct of building (GitHub diffs, CI output, provenance records, WCAG audits). Product Theatres primarily serve inspection and scrutiny inquiry types.

Product Theatres are the primary revenue engine: they fund the OSINT budgets required by investigative and counterfactual Theatres and generate calibration certificates that gate construct access to higher-tier model routing in the Hounfour runtime.

**Market Theatres (execution_path: market)**

Market Theatres create prediction markets using the full LMSR lifecycle. Agents trade against the cost function at fork points; resolution consumes committed OSINT evidence bundles. Market Theatres serve all five inquiry types: counterfactual markets (the original Echelon model), investigative markets (evidence-discovery with capital at risk), survey markets (structured opinion aggregation), and scrutiny markets (adversarial audit with capital-backed claims). These are the markets described in Sections III–XIV.

**Discovery Markets.** A subclass of Market Theatre where the inquiry is investigative rather than counterfactual. Evidence accumulates through OSINT agent discovery rather than simulation divergence. Market participants bet on outcomes as evidence surfaces; the market functions as a mechanism for directing investigative attention and funding research. Creator-generated discovery markets (where an investigator launches a market on their own research) enable a clean monetisation model: 1% fees on volume, no token, time-bounded, self-resolving once evidence surfaces.

| **Family**         | **Execution Path** | **Inquiry Type**       | **Domain**                   | **Resolution Type**     | **Example**                    |
|--------------------|---------------------|------------------------|------------------------------|-------------------------|--------------------------------|
| PRODUCT            | replay              | Inspection             | Construct verification       | Deterministic replay    | Observer user research verification |
| FINANCIAL          | replay              | Inspection             | Tokenised real estate ops    | Deterministic replay    | Escrow milestone release, distribution waterfall |
| QUANT              | replay              | Scrutiny               | Market microstructure audit  | Deterministic replay    | LMSR hygiene, b-sensitivity suite |
| OSINT              | replay              | Scrutiny               | Oracle pipeline verification | Deterministic replay    | Composed oracle corroboration check |
| GEOPOLITICAL       | market              | Counterfactual         | World events                 | OSINT evidence (Mode 1) | Strait of Hormuz transit disruption |
| INVESTIGATIVE      | market              | Investigative          | Evidence discovery           | OSINT evidence (Mode 1) | On-chain insider trading detection |
| SURVEY             | market              | Survey                 | Opinion aggregation          | Participation threshold | Asset valuation consensus |
| 2D-DISCRETE        | market              | Counterfactual         | Grid navigation, pathfinding | Deterministic (Mode 0)  | Warehouse pick-and-place       |
| 2D-CONTINUOUS      | market              | Counterfactual         | Continuous 2D control        | Deterministic (Mode 0)  | Drone corridor navigation      |
| 3D-STATIC          | market              | Counterfactual         | Static 3D manipulation       | Deterministic (Mode 0)  | Assembly line quality check    |
| 3D-INERT           | market              | Counterfactual         | Inertial 3D physics          | Deterministic (Mode 0)  | Orbital salvage operations     |
| 3D-DYNAMIC         | market              | Counterfactual         | Dynamic obstacles            | Deterministic (Mode 0)  | Traffic intersection           |
| PHYSICS-SIM        | market              | Counterfactual         | Full physics simulation      | Deterministic (Mode 0)  | Robotic grasping under load    |
| SOCIAL-ENGINEERING | market              | Investigative          | Multi-agent negotiation      | Evidence-based (Mode 1) | Supply chain coordination      |
| ECONOMIC-SIM       | market              | Survey                 | Market dynamics              | Evidence-based (Mode 1) | Resource allocation            |
| HYBRID             | market              | Scrutiny               | Mixed physical-social        | Composed escalation     | Disaster response coordination |

**Product Theatre Verticals (Proven)**

Four replay verticals have been implemented and verified, producing 8 calibration certificates across 10 templates with 77+ fixtures and 189 verifier checks (see Appendix F for the full register). All Product Theatre verticals use inspection or scrutiny inquiry types.

**Vertical A — Tokenised Real Estate Operations (4 templates, Inspection).** Deterministic audit of escrow milestone releases, distribution waterfalls, ledger reconciliation, and arrears resolution. Ground truth is the financial transaction record itself. Binary truth conditions: evidence present, signer policy satisfied, timing valid, amount correct. All 4 templates achieve 21/21 verifier PASS.

**Vertical B — Construct Verification (1 template, Inspection).** Calibrates AI construct performance against engineering ground truth via the Replay Engine. The Observer construct (Constructs Network) was the first real certificate, achieving composite score 0.700 at UNVERIFIED tier.

**Vertical C — LMSR Market Microstructure (4 templates, Scrutiny).** Audits the prediction market engine itself. Coverage spans market hygiene (19 criteria), API fidelity, perturbation harness (VRF, saboteur pressure, Paradox recovery), and parametric b-sensitivity sweeps. All 4 templates achieve 21/21 verifier PASS.

**Vertical D — OSINT Composed Oracle (1 template, Scrutiny).** Verifies oracle pipeline integrity: corroboration minimums, counter-signal checking, rule-change monitoring. 10 fixtures across 7 geographic regions. See §XV for the full OSINT architecture.

**2.3 Template Structure**

Each Theatre Template is a JSON document conforming to the Echelon Theatre Schema v2.0.1 (Appendix B). The schema enforces execution-path-specific requirements through conditional validation.

**Required Fields (all templates)**

**theatre_id:** Unique identifier (e.g., product_observer_v1). Immutable once published.

**template_family:** Classification determining execution path and resolution type.

**execution_path:** Either `replay` (Product Theatre) or `market` (Market Theatre). Determines which lifecycle behaviour applies at the ACTIVE state.

**criteria:** Structured evaluation criteria — not a freeform string. Contains `criteria_ids` (deterministic score keys such as `source_fidelity` or `hex_grid_accuracy`), `criteria_human` (freeform rubric for human consumption), and optional `weights` (per-criterion weights summing to 1.0). The `criteria_ids` become canonical keys in the calibration certificate's scores dictionary.

**version_pins:** Exact commit hashes for every construct, scorer, and methodology version involved. Required for reproducibility. For compositional verification chains (e.g., Easel → Artisan → Mint), every construct in the chain must have a corresponding entry.

**fork_definitions:** Decision points within the Theatre. For Market Theatres, each fork instantiates an LMSR market. For Replay Theatres, forks represent evaluation dimensions.

**scoring:** Scoring configuration. Market Theatres use the multi-dimensional score vector (time, value, collateral, safety, trace quality). Product Theatres use criteria-based scoring via the `weights` field in `criteria`. Both support configurable holdout splits for adversarial resistance.

**resolution_programme:** Ordered sequence of oracle steps executed during settlement. Each step specifies a type (construct_invocation, deterministic_computation, hitl_rubric, or aggregation), timeout, and escalation path. Pre-committed and immutable after Theatre creation.

**Additional Required Fields (Product Theatres)**

**product_theatre_config:** Ground truth source (GITHUB_API, CI_CD, PROVENANCE_JSONL, DETERMINISTIC_COMPUTATION), construct under test, adapter type (http, local, or mock — mock permitted for CI only, never for certificate generation), adapter endpoint, and optional construct chain for compositional verification.

**dataset_hashes:** SHA-256 hashes for all ground truth datasets referenced by the template. Linked to the replay data via `replay_dataset_id`, which must exist as a key in `dataset_hashes`. Ensures replay reproducibility.

**Additional Required Fields (Market Theatres)**

**market_theatre_config:** LMSR configuration (liquidity parameter b, fee schedule, duration), OSINT source declarations with resolution roles (primary_evidence, secondary_corroboration), corroboration minimum (minimum 2 independent sources per OSINT Appendix v3.2), geopolitical category, and Paradox thresholds.

**Optional Fields**

**hitl_steps:** Pre-committed human-in-the-loop specifications for semi-deterministic scoring. Includes rubric text, scoring scale, and identity separation rules (scorer must not be construct author). Required when the resolution programme includes steps of type `hitl_rubric`.

**training_primitives:** RL/verification primitives this Theatre trains or tests.

**difficulty_tiers:** Parameter sets for Easy, Standard, and Hard difficulty. Optional for Product Theatres.

**oracle_config:** Required oracle mode, data feeds, and confidence thresholds. Applicable to Market Theatres.

**physics_config:** Physics simulation parameters. Applicable to simulation-family Market Theatres only.

**2.4 Fork Definitions (Decision Markets)**

Forks are the atomic prediction units within a Theatre. Each fork defines a decision point where agents select from a constrained set of options, and market participants price the probability distribution across those options.

Fork trigger conditions are typed and parameterised: timestep-based (deterministic), state-reached (simulation state crosses threshold), entropy-threshold (market uncertainty exceeds bound), logic-gap-threshold (divergence between market and oracle signal), episode-complete (replay theatre episode boundary), or manual. Each option has an `option_id` (canonical identifier referenced by RLMF exports), explicit success criteria, failure modes with defined penalties, and state transitions that modify the simulation deterministically.

This structured specification ensures that every fork is unambiguous, every outcome is mechanically determinable, and every resolution is reproducible from committed inputs.

**2.5 Commitment Hash and Canonical JSON**

The commitment hash is computed over the full canonicalised template JSON plus external version pins and dataset hashes — not a selected subset of fields. This prevents "uncommitted knobs" where a field can change without invalidating the hash.

Canonical JSON follows RFC 8785 (JSON Canonicalization Scheme): all object keys sorted lexicographically (Unicode code point order), no insignificant whitespace, integers as-is, floats with no trailing zeroes and no positive sign prefix, null values included (not omitted), arrays preserve insertion order. All implementations must use a single `canonical_json()` utility function — never raw serialisation. This ensures third parties can independently reproduce the exact same hash.

**Normative hash algorithm:** The commitment hash is `SHA-256( canonical_json(composite) )` where `composite` is a single JSON object with three keys: `{"dataset_hashes": ..., "template": ..., "version_pins": ...}` (keys in lexicographic order per canonical rules). Implementations must not concatenate separately serialised fragments — the input to SHA-256 is one canonical JSON string from one composite object. This eliminates ambiguity about delimiters, ordering, or boundary encoding between components.

**2.6 Calibration Certificates and Verification Tiers**

Every completed Theatre (Product or Market) produces a calibration certificate — a structured record of what was measured, how it was scored, and what evidence supports the scores. The canonical certificate schema is defined in Appendix D.

The unified certificate schema includes: structured criteria (IDs + human rubric + weights), per-criterion scores, composite score, calibration metrics (precision, recall, Brier score, ECE as applicable), replay count, full reproducibility pins (construct version, scorer version, dataset hash, methodology version), evidence bundle hash, commitment hash, and verification tier.

**Verification Tier Rules (v0)**

| **Tier** | **Requirements** | **Hounfour Routing** | **Expiry** |
|---|---|---|---|
| UNVERIFIED | < 50 replays, OR missing reproducibility pins, OR incomplete evidence bundle | Baseline model pools. Constraint yielding (`review: skip`) treated as `review: full`. | N/A |
| BACKTESTED | ≥ 50 replays + full reproducibility pins + published scores + verifiable commitment hash + no unresolved disputes | Mid-tier brigade routing. | 90 days without a new Theatre run → falls to UNVERIFIED |
| PROVEN | BACKTESTED + ≥ 3 months consecutive verification + production telemetry + community attestation + behavioural signal integration | Premium model pools, full kitchen brigade access. | 180 days without production telemetry → falls to BACKTESTED |

**Constraint Yielding Gate (hard rule):** An UNVERIFIED construct declaring `review: skip` in its manifest is always treated as `review: full` by the Loa framework and Hounfour routing layer. Only BACKTESTED or PROVEN constructs may yield quality gates. This gate is enforced in two places: Loa's manifest reader (at build time) and Hounfour's router (at runtime). It is not enforced in construct manifests themselves — a construct cannot override the gate by self-declaration. No exceptions.

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
| Version Pins         | Exact commit hash for every construct and scorer in the resolution programme | Hash of version_pins object included in commitment hash |
| Dataset Hashes       | SHA-256 of every ground truth dataset referenced by the template | Hash of dataset_hashes object included in commitment hash |

The commitment hash is computed over the full canonicalised template JSON plus version pins and dataset hashes using canonical JSON rules (see §II.5). For Product Theatres, no capital is escrowed and sabotage rules do not apply; the commitment ensures parameter immutability and replay reproducibility. The invariant after commitment: no parameter changes are permitted. The resolution programme may include pre-committed human-in-the-loop steps, but the process, rubric, and identity rules for those steps are themselves committed.

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

**X. Engagement & Bounded Inquiries**

**10.1 Timelines as Bounded Inquiries**

A timeline is a bounded inquiry: a time-limited, evidence-committed investigation with certifiable resolution. The term "timeline" reflects the temporal nature of every inquiry — evidence accumulates over a defined window, positions are established, and resolution occurs at a committed endpoint. The unifying primitive is not the fork (which is one mechanism within one inquiry type) but the inquiry itself.

Five inquiry types share the same Theatre Template infrastructure:

**Counterfactual inquiries** fork from real markets (Kalshi, Polymarket) into parallel timelines where agents trade on alternative outcomes. Evidence accumulates through simulation divergence. Resolution is deterministic (Mode 0) or evidence-based (Mode 1). This is the original Echelon model.

**Investigative inquiries** are discovery markets where evidence accumulates through OSINT agent discovery rather than simulation. Market participants bet on outcomes as evidence surfaces. The market functions as a mechanism for directing investigative attention and funding research. Resolution triggers when the evidence threshold is met or the time window closes. Example: "Which company is engaged in insider trading?" — agents crawl on-chain data, regulatory filings, and public records, surfacing evidence into a DeltaBrief whilst market participants adjust positions based on emerging findings.

**Inspection inquiries** verify compliance against committed criteria. The evidence base is the artefact under inspection (financial transaction, escrow milestone, construct output). Resolution is binary: criteria met or not met. The existing tokenised real estate Product Theatres are inspection inquiries. Example: "Does this distribution waterfall satisfy the committed policy?"

**Survey inquiries** aggregate structured opinions with committed methodology. The evidence is the aggregate participation signal. Resolution produces a distribution rather than a binary outcome. Example: "What does the market believe this asset is worth?" — useful for price discovery in illiquid markets.

**Scrutiny inquiries** are adversarial audits of claims against committed evidence. The investigator takes a position against a claim and the market prices the probability that the claim survives scrutiny. Resolution is claim verified or falsified. Example: "Is this project's claimed TVL accurate?" — agents verify on-chain reserves against published claims.

**10.2 Market Hierarchy**

Echelon operates three concurrent market tiers within each Market Theatre, all trading simultaneously via LMSR:

| **Tier**       | **Market Type**                        | **Resolution**                   | **Example**                                                         |
|----------------|----------------------------------------|----------------------------------|---------------------------------------------------------------------|
| Level 1: Macro | End-result markets (inquiry outcome)   | At Theatre completion            | "Investigation concludes X" / "Final score > 70"                    |
| Level 2: Meso  | Fork outcome markets (decision points) | When evidence threshold reached  | "Agent chooses Option B" / "Evidence confirms claim"                |
| Level 3: Micro | Interval/checkpoint markets (state)    | At specified epoch or interval   | "Stability > 60% at epoch 200" / "New evidence before deadline"     |

**10.3 Timeline Creation Flow**

The creation flow adapts to the inquiry type whilst maintaining the same commitment infrastructure:

**For all inquiry types:**

Step 1: Select Theatre Template from the published library. All templates conform to the Theatre Schema and are version-locked. The template specifies the inquiry type.

Step 2: Configure parameters within committed ranges: difficulty tier, LMSR liquidity parameter b (Market Theatres only), duration, agent population mix.

Step 3: Review the commitment hash. All parameters, data sources, resolution mechanisms, and fee schedules are displayed for review.

Step 4: Escrow capital (Market Theatres) or commit parameters (Product Theatres). For Market Theatres, the creator deposits funds corresponding to the LMSR worst-case loss b * ln(n) plus protocol fees.

Step 5: Deploy. The commitment hash is published on-chain (Market Theatres) or recorded in the evidence bundle (Product Theatres). Trading opens (Market Theatres) or replay execution begins (Product Theatres).

**For investigative and scrutiny timelines (additional steps):**

Step 2b: Configure OSINT source selection. The creator specifies which registry sources the investigation will query, along with evidence accumulation rules (corroboration minimums, counter-signal classes, confidence thresholds). These are committed before the inquiry opens.

Step 2c: Configure investigative tooling (optional). Creators may attach OSINT agent toolsets to the timeline, providing market participants with structured evidence-gathering capabilities. See §10.5.

**10.4 Domain Adaptation**

The Theatre Template Library extends across inquiry types and domains. The same agent archetypes maintain their psychological core whilst adapting to domain-specific and inquiry-specific dynamics:

| **Archetype** | **Counterfactual**      | **Investigative**                | **Inspection**              | **Scrutiny**                |
|---------------|-------------------------|----------------------------------|-----------------------------|-----------------------------|
| SABOTEUR      | Pipeline disruption     | Counter-evidence injection       | Adversarial fixture design  | Claim falsification         |
| DIPLOMAT      | Treaty brokering        | Source corroboration brokering   | Compliance mediation        | Dispute resolution          |
| SPY           | OSINT intelligence      | Primary evidence discovery       | Audit trail analysis        | Deep verification           |
| SHARK         | Crisis momentum trading | Evidence-front-running           | Rapid certification         | Short-selling unverified claims |

**10.5 Investigative Tooling (Concept)**

For investigative and scrutiny timelines, Echelon can surface OSINT agent toolsets to timeline creators and participants. Rather than requiring participants to gather evidence manually, the platform provides structured access to the OSINT pipeline:

**Evidence agents.** Domain-specific OSINT agents (on-chain analytics, regulatory filing crawlers, corporate registry lookups) that automatically build evidence bundles as the investigation progresses. Every piece of evidence is pinned and hashed as it arrives.

**DeltaBrief integration.** The DeltaBrief updates as evidence accumulates, surfacing contradictions and corroborations in real time. Market participants can see the evidence structure evolving and adjust positions accordingly.

**Funded investigation model.** The creator launches a question and the market funds the investigation through trading fees. At 1% fees, a $10M volume investigative timeline generates $100k in creator revenue — enough to fund sustained OSINT agent operation. The creator is not just launching a question; they are launching a funded investigation with verifiable tooling.

This model transforms prediction markets from opinion aggregation into evidence-backed resolution. The market does not just ask "what do you think?" — it asks "what can you prove?" and provides the tools to prove it.

**Status:** Concept. Requires OSINT pipeline integration with timeline creator UX. Dependencies: stable OSINT agent toolset (§XV), DeltaBrief real-time update capability, and evidence bundle streaming (not yet specified).

**10.6 Flash Forks (Micro-Event Markets)**

For continuous-flow domains (sports, crypto, investigative), Flash Forks enable micro-event prediction markets that fork from parent timelines at specific decision points. These inherit the LMSR liquidity parameter from the parent timeline, with committed scaling factors for duration and depth. In investigative timelines, Flash Forks can trigger when a significant piece of evidence surfaces, creating micro-markets on the implications of that evidence.

**XI. RLMF Data Product**

**11.1 The Problem with Human Annotation**

Robotics companies currently pay \$500/hour for human annotation: one person observes a task and provides binary labels (success/failure). This process is slow, biased to a single viewpoint, expensive, and does not scale. The output is a binary label that discards uncertainty information critical for policy learning. The same limitation applies to AI agent evaluation more broadly: binary pass/fail assessments discard the uncertainty distributions that are critical for routing, promotion, and capability certification.

**11.2 RLMF: Reinforcement Learning from Market Feedback**

RLMF replaces single-annotator binary labelling with multi-agent market-derived probability distributions. Instead of one human clicking "good" or "bad", 100 agents trade against the LMSR cost function on task outcomes with capital at risk. The resulting market prices encode calibrated uncertainty: "72% confidence this grip strategy holds" is richer supervision than a binary label. In investigative and scrutiny timelines, RLMF captures how conviction evolves as evidence surfaces — a training signal unavailable from static annotation.

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

The canonical RLMF export schema v2.0.1 (Appendix C) standardises supervision signals for integration with both robotics training pipelines and construct verification workflows. The schema supports two execution paths with conditional field requirements.

**Market Theatre exports** (execution_path: market) contain: episode identification (theatre_id, seed_hash for deterministic replay), state features (6-DOF pose, object states, active constraints), fork information (options as option_ids, deadlines, trigger conditions), market signals (LMSR prices as probabilities, liquidity depth, Logic Gap, entropy, agent distribution), action taken by the evaluated agent (option_id), settlement outcome (multi-dimensional reward vector), and calibration metrics (Brier score, ECE).

**Product Theatre exports** (execution_path: replay) contain: episode identification (theatre_id, config_hash as commitment reference), state features (input_data passed to construct, construct_output received, ground_truth or ground_truth_ref for auditability, ground_truth_hash), a `criteria_ids` snapshot (making the export self-describing without a template fetch), `replay_output_class` (the construct's predicted classification — distinct from `action_taken` to prevent confusion between agent decisions and construct outputs), settlement outcome (per-criterion scores keyed by criteria_ids, normalised 0.0–1.0), verification metadata (construct_id, construct_version, construct_chain_versions for compositional chains, invocation_status, invocation_latency, evidence_bundle_hash, certificate_id, verification_tier), and calibration metrics (precision, recall, reply_accuracy).

Both paths include a `metadata.is_holdout` flag indicating whether the episode was in the adversarial holdout split, and the commitment hash (`config_hash`) linking the export back to the Theatre's committed parameters for third-party verification.

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

**XV. OSINT Source Registry & Composed Oracle**

**15.1 Purpose**

The OSINT Source Registry is the authoritative catalogue of data sources eligible for use in Market Theatre resolution, investigative timeline evidence gathering, and oracle pipeline verification. It prevents prediction markets from diverging into speculation by grounding them in observed, verifiable reality signals from identified, assessed, and version-controlled sources. For investigative and scrutiny timelines (§X), the registry determines which evidence-gathering agents are available to timeline creators and participants.

**15.2 Registry Architecture (v0.4.0)**

The registry maintains 57 sources across 7 jurisdictions (GB, US, EU, AE, AU, SG, HK) with a 19-field per-source schema. Each source entry includes structural primitives that enable automated integrity checking:

| **Field** | **Purpose** |
|---|---|
| source_id | Canonical snake_case identifier (e.g., `companies_house_api`) |
| jurisdiction | ISO country or region code |
| independence_upstream_id | Identifies shared data lineage (deduplication) |
| access_surface | How data is retrieved: `public_api`, `paid_gateway`, `portal_scrape` |
| revision_policy | Whether published data can be retroactively altered |
| receipt_mode_minimum | Minimum evidence standard: `http_transcript`, `signed_payload`, `screenshot` |
| access_proof | Documentation proving access capability |
| settlement_eligible | Whether the source may serve as primary evidence in resolution |

**Settlement Eligibility.** Only sources meeting strict criteria may serve as primary evidence: official government or regulatory APIs with stable endpoints, machine-readable structured output, documented revision policies, and deterministic receipt hashing. 13 of 57 sources are currently settlement-eligible.

**Independence Upstream Deduplication.** Sources sharing a common upstream (e.g., CourtListener mirroring PACER) are linked via `independence_upstream_id`. The `independence_upstream_dedupe_runner` enforcement rule prevents double-counting corroboration from non-independent sources.

**15.3 Jurisdictional Readiness**

| **Jurisdiction** | **Settlement Sources** | **Scoring Sources** | **Status** |
|---|---|---|---|
| GB | 4 (Companies House, Gazette, HMLR, BoE) | 6 | Production-ready |
| US | 4 (SEC EDGAR, NY Fed, FRED, PACER) | 5+ | Production-ready |
| EU | 2 (ECB, INPI RNE) | 3+ | Partial (needs expansion) |
| AE | 0 | 9 | Partner-required for settlement |
| AU | 1 (AFSA) | 4 | Partial (ASIC DSP registration pending) |
| SG | 0 | 2+ | Early assessment |
| HK | 0 | 2+ | Early assessment |

**15.4 Committed Source Groups**

Sources are organised into 13 committed groups (plus 2 proposed groups pending template v1.1):

Committed: `government_registry`, `financial_regulator`, `central_bank`, `market_data`, `news_wire`, `maritime_ais`, `satellite_imagery`, `social_signal`, `blockchain_analytics`, `weather_climate`, `geospatial`, `court_record`, `trade_data`.

Proposed (pending template v1.1 formal commit): `judicial_record`, `calendar_counter_signal`.

**15.5 Composed Oracle Specification**

The Composed Oracle builds resolution evidence from multiple registry sources using a three-stage pipeline:

**Stage 1 — Collection.** For each committed source in the Theatre's oracle configuration, the pipeline retrieves data within the committed time window. Each retrieval produces an HTTP Transcript Receipt: a deterministic hash of the canonical HTTP exchange (method, URL, headers, response body, timestamp) enabling third-party verification.

**Stage 2 — Corroboration.** Evidence is cross-referenced against the Theatre's corroboration minimum (minimum 2 independent sources per the OSINT Appendix v3.2). The `independence_upstream_dedupe_runner` ensures sources sharing upstream lineage count as one. Counter-signal checking evaluates 11 counter-signal classes (expanded from 4 in v1) to identify contradictory evidence.

**Stage 3 — Scoring.** The oracle produces a confidence-weighted evidence bundle. Per-criterion scores map to the Theatre's `criteria_ids`. The bundle hash (SHA-256 of canonical JSON) is included in the calibration certificate.

**15.6 World Monitor Integration**

World Monitor (koala73/worldmonitor, forked to AITOBIAS04/worldmonitor) provides the real-time OSINT dashboard: 150+ RSS feeds, Composite Instability Index (CII) scores, convergence detection, and AIS chokepoint monitoring. Licensed AGPL-3.0 — consumed exclusively via a clean API boundary.

The World Monitor API contract defines three domain endpoints:

| **Endpoint** | **Domain** | **Core Type** |
|---|---|---|
| `/intelligence/cii` | Instability scoring | CII snapshot with component breakdown |
| `/market/snapshot` | Financial market data | Normalised price/volume/sentiment |
| `/maritime/anomaly` | Maritime AIS monitoring | Vessel anomaly with chokepoint context |

Core interchange types: `EvidenceBundle`, `NormalisedEvent`, `HTTPTranscriptReceipt`. All types are Pydantic v2 compatible with canonical hashing utilities aligned to the registry spec.

**15.7 Schema Enforcement Rules**

Five enforcement rules ensure registry integrity:

1. **settlement_source_api_contract:** Settlement-eligible sources must have a defined API contract with request/response schemas.
2. **independence_upstream_dedupe_runner:** Sources sharing `independence_upstream_id` count as one for corroboration.
3. **receipt_mode_enforcement:** Each source's `receipt_mode_minimum` defines the minimum evidence standard; higher modes (e.g., `signed_payload`) are always accepted.
4. **access_proof_validation:** Every source must provide verifiable access proof (API key confirmation, subscription receipt, or documentation URL).
5. **revision_policy_disclosure:** Sources with mutable published data must declare their revision policy; mutable sources receive a confidence penalty in scoring.

**XVI. Verification Infrastructure**

**16.1 Evidence Bundles**

Every completed Theatre produces an evidence bundle: the auditable artefact backing its calibration certificate. The bundle follows a consistent creation pattern: create directory structure first, populate with computed content, then generate the manifest as a pure path-to-hash mapping. Verification runs separately from generation to ensure clean separation of concerns.

**Bundle contents:**

| **File** | **Purpose** |
|---|---|
| manifest.json | Path-to-SHA-256 mapping for every file in the bundle |
| template_committed.json | Canonical JSON of the Theatre template at commitment time |
| ground_truth/ | Ground truth dataset (inline or reference) |
| invocations/ | Per-episode invocation records (request, response, timing) |
| scores/ | Per-episode criterion scores |
| aggregate_results.json | Aggregate statistics across all episodes |
| certificate.json | The calibration certificate itself |
| audit_trail.json | Ordered log of all verification operations |

The manifest is a flat dictionary: `{ "relative/path": "sha256_hex_hash" }`. No timestamps in the manifest — this ensures deterministic rebuilds produce identical hashes. The evidence bundle hash in the certificate is `SHA-256( canonical_json(manifest) )`.

**16.2 Verifier CLI**

The standalone verifier CLI enables third-party verification of any Echelon certificate without platform access:

```
python3 echelon_verify.py verify certificate.json evidence_bundle/
```

The verifier performs 21 checks across 4 categories:

| **Category** | **Checks** | **Examples** |
|---|---|---|
| Structural integrity | 6 | Manifest completeness, file existence, hash verification |
| Template conformance | 5 | Schema validation, criteria consistency, version pin presence |
| Score mathematics | 5 | Weight sum = 1.0, composite recalculation, bound enforcement |
| Cryptographic chain | 5 | Commitment hash reproduction, evidence bundle hash, dataset hash |

A certificate achieves full verification when all 21 checks pass. The verifier is deterministic: given the same inputs, it always produces the same result.

**16.3 Verification Tiers (Operational)**

The tier system defined in §II.6 is now operational across 8 issued certificates. Tier promotion requires:

**UNVERIFIED → BACKTESTED:** ≥ 50 replay episodes with full reproducibility pins (construct version, scorer version, dataset hash, methodology version), published scores, verifiable commitment hash, and no unresolved disputes. Expires after 90 days without a new Theatre run.

**BACKTESTED → PROVEN:** BACKTESTED status for ≥ 3 consecutive months, production telemetry integration, community attestation, and behavioural signal integration. Expires after 180 days without production telemetry.

Current status: All 8 certificates are at UNVERIFIED tier (fixture counts below 50 episodes). The Observer certificate requires rerun with --limit 50+ when the API is healthy to achieve BACKTESTED.

**16.4 Cold-Path Certificate Consumption**

Calibration certificates are consumed by downstream systems as cached data artefacts, not live service calls. The cold-path consumption contract (defined in the Partner Briefing v1) specifies:

**Transport:** Certificates are published to a known location (filesystem or object store) and polled by consumers on a configurable interval. No real-time API dependency.

**Fail-closed policy:** If a certificate is missing, expired, or fails verification, the consumer treats the construct as UNVERIFIED. No fallback to cached stale data.

**Tier escalation thresholds:** Each consuming system defines its own minimum tier requirement. For example, the Hounfour runtime requires BACKTESTED for mid-tier brigade routing and PROVEN for premium model pools.

**Cache invalidation:** Certificates carry `issued_at` and `expires_at` timestamps. Consumers must respect expiry and re-fetch on schedule.

**XVII. Integration Architecture & Market Entry Wedge**

**17.1 Five-Layer Stack**

Echelon operates as the evaluation substrate within a five-layer architecture:

| **Layer** | **System** | **Function** | **Owner** |
|---|---|---|---|
| 1. Evaluation | Echelon | Certificates, bounded inquiry resolution, evidence markets | Echelon |
| 2. Expertise | Constructs | Packaged AI expertise units | Constructs Network |
| 3. Runtime | Hounfour | Multi-model routing, budget enforcement | janitooor |
| 4. Distribution | Arrakis | Token-gated access, conviction scoring | janitooor |
| 5. Consumer | Discord, Telegram | End-user touchpoints | Constructs Network |

**Integration thesis:** Echelon evaluates → Hounfour executes → Arrakis distributes. Certificates flow upward from Layer 1 to gate construct promotion at Layer 3. Market signals flow downward from Layer 3 to inform training priorities at Layer 1. Investigative and scrutiny inquiries generate both certificates (for construct verification) and evidence bundles (for resolution market settlement).

**17.2 Hounfour Integration Points**

Three integration surfaces connect Echelon's evaluation substrate to the Hounfour runtime:

**Certificate transport.** Cold-path consumption (§XVI.4). Certificates published by Echelon are polled by Hounfour's router to inform tier-based model pool assignment.

**Constraint yielding gate.** Enforced at two loci: Loa's manifest reader (build time) and Hounfour's router (runtime). UNVERIFIED constructs declaring `review: skip` are always treated as `review: full`. The gate is not self-declarable — a construct cannot override it.

**Model pool mapping.** Verification tier → model pool assignment:

| **Tier** | **Model Pool** | **Routing** |
|---|---|---|
| UNVERIFIED | Baseline | Standard models, full review enforcement |
| BACKTESTED | Mid-tier brigade | Expanded model access, selective gate yielding |
| PROVEN | Premium | Full kitchen brigade, maximum model diversity |

**17.3 Market Entry Wedge**

**Pick:** Developer forward-funding via deterministic escrow milestone releases + standalone verifier CLI.

**Why escrow first:** The budget already exists (£25–75k per project for quantity surveyor coordination in UK property development). The truth conditions are binary (evidence present + signer policy satisfied + timing valid + amount correct). Regulatory legibility is high (AI is a tool, licensed entities hold liability). The pull-through path is clear: escrow → distribution waterfalls → ledger reconciliation → arrears stress-testing → verifier platform adoption.

**Expansion path:**

| **Phase** | **Product** | **Revenue Model** | **Template** |
|---|---|---|---|
| 1 | Escrow milestone certification | Per-certificate fee | ESCROW_MILESTONE_RELEASE_V1 |
| 2 | Distribution waterfall audit | Per-distribution fee | DISTRIBUTION_WATERFALL_V1 |
| 3 | Fund administration ops | Subscription | LEDGER_RECONCILIATION_V1 |
| 4 | Arrears stress-testing | Per-assessment fee | ARREARS_RESOLUTION_V1 |
| 5 | Full verifier platform | Platform licence | All templates |

**17.4 Arrears State Machine**

The arrears resolution template (ARREARS_RESOLUTION_V1) models a 12-state lifecycle for distressed property debt:

CURRENT → WATCH_LIST → ARREARS_EARLY → ARREARS_LATE → DEFAULT_NOTICE → FORMAL_DEFAULT → ENFORCEMENT_INITIATED → ENFORCEMENT_ADVANCED → POSSESSION_PROCEEDINGS → SALE_ORDERED → RECOVERY_COMPLETE → WRITE_OFF

Each state transition has committed trigger conditions, evidence requirements, and time windows. The state machine enables deterministic verification of whether a debt resolution followed correct procedure — critical for fund administrators managing distressed portfolios in tokenised real estate.

**Appendix B: Theatre Template Schema (JSON) — v2.0.1**

The Theatre Template schema (`echelon_theatre_schema_v2.json`) defines the complete specification for all Theatre types. Key design decisions in v2.0.1:

**Execution path split.** The `execution_path` field (replay | market) determines which lifecycle behaviour applies. Conditional validation via `allOf`/`if`/`then` blocks enforces that Product Theatres require `product_theatre_config` and `dataset_hashes`, whilst Market Theatres require `market_theatre_config`.

**Structured criteria.** The `criteria` object replaces freeform strings with `criteria_ids` (deterministic snake_case keys), `criteria_human` (freeform rubric), and `weights` (per-criterion weights — runtime-enforced to sum to 1.0 and be a subset of criteria_ids).

**Version pinning.** The `version_pins` object maps construct IDs to exact commit hashes. Runtime validation enforces that every `construct_id` referenced in the `resolution_programme` has a corresponding entry.

**Adapter endpoint conditional.** When `adapter_type` is `http` or `local`, `adapter_endpoint` is required by a nested `allOf` block within `product_theatre_config`.

**Runtime validation rules.** A `runtime_validation_rules` documentation field enumerates seven constraints that JSON Schema cannot express but the Theatre engine must enforce, including criteria weight sums, construct-to-pin linkage, and canonical JSON rules for commitment hash computation.

**Strict mode.** `additionalProperties: false` on the root object and key nested objects prevents silent arbitrary fields.

The full schema is maintained in `docs/schemas/echelon_theatre_schema_v2.json`. The v1 schema (`echelon_theatre_schema.json`) is retained for backward compatibility with existing simulation templates.

**Appendix C: RLMF Export Schema (JSON) — v2.0.1**

The RLMF export schema (`echelon_rlmf_schema_v2.json`) defines the canonical format for training data exports. Key design decisions in v2.0.1:

**Execution path conditionals.** `allOf`/`if`/`then` blocks enforce that replay episodes require `state_features.input_data`, `construct_output`, `ground_truth_hash`, `settlement.criteria_scores`, and `verification` fields. Market episodes require the `market` block with prices, liquidity, logic_gap, and entropy.

**Ground truth auditability.** Replay episodes must include either `ground_truth` (inline data) or `ground_truth_ref` (URI/path), alongside `ground_truth_hash`. This supports privacy-sensitive hash-only exports whilst ensuring auditability.

**Separated output semantics.** `action_taken` is for market agent decisions (option_ids). `replay_output_class` is for construct predictions in replay mode. This prevents downstream consumers from conflating agent choices with construct outputs.

**Self-describing exports.** A `criteria_ids` snapshot array is required for replay episodes, allowing consumers to validate `criteria_scores` keys without fetching the Theatre template.

**Standardised hash format.** All hashes use raw hex format (`^[a-f0-9]{64}$`) — no `0x` prefix — across both schemas for consistency.

**Corrected bounds.** Brier score maximum is 1.0 (not 0.5). Criteria scores are bounded 0.0–1.0.

The full schema is maintained in `docs/schemas/echelon_rlmf_schema_v2.json`. The v1 schema is retained for backward compatibility.

**Appendix D: Calibration Certificate Schema — v1.0.0**

The calibration certificate is the bridge between Echelon's verification infrastructure and Hounfour's model routing. Every completed Theatre (Product or Market) issues one. The schema is maintained in `docs/schemas/echelon_certificate_schema.json`.

| **Field** | **Type** | **Description** |
|---|---|---|
| certificate_id | UUID | Unique certificate identifier |
| theatre_id | string | Theatre that produced this certificate |
| template_id | string | Theatre template used |
| construct_id | string | Construct under test |
| criteria | TheatreCriteria | Structured criteria (IDs + human rubric + weights) |
| scores | dict[str, float] | Per-criterion scores; keys are criteria_ids, values 0.0–1.0 |
| composite_score | float | Weighted aggregate per criteria weights |
| precision | float (optional) | Classification precision (Product Theatres) |
| recall | float (optional) | Classification recall (Product Theatres) |
| reply_accuracy | float (optional) | Response accuracy (Product Theatres) |
| brier_score | float (optional) | Probabilistic calibration (Market Theatres) |
| ece | float (optional) | Expected Calibration Error |
| replay_count | int | Number of episodes scored |
| evidence_bundle_hash | string | SHA-256 of the evidence bundle (raw hex) |
| ground_truth_hash | string | SHA-256 of the ground truth dataset (raw hex) |
| construct_version | string | Exact commit hash of construct under test |
| construct_chain_versions | dict (optional) | For compositional chains: construct_id → commit hash |
| scorer_version | string | Scorer model/version identifier |
| methodology_version | string | Verification methodology version |
| dataset_hash | string | SHA-256 of replay dataset (raw hex) |
| verification_tier | enum | UNVERIFIED, BACKTESTED, or PROVEN |
| commitment_hash | string | Theatre's commitment hash (for third-party verification) |
| issued_at | datetime | Certificate issuance timestamp |
| expires_at | datetime | Per tier expiry rules (90 days BACKTESTED, 180 days PROVEN) |
| theatre_committed_at | datetime | When the Theatre was committed |
| theatre_resolved_at | datetime | When the Theatre resolved |
| ground_truth_source | enum | GITHUB_API, CI_CD, PROVENANCE_JSONL, DETERMINISTIC_COMPUTATION, OSINT_FEED |
| execution_path | string | "replay" or "market" |

This schema is consumed by Hounfour's router to make tier-based routing decisions, and by Loa's manifest reader to enforce the constraint yielding gate. Consumption follows the cold-path pattern (§XVI.4): certificates are cached artefacts polled on schedule, not live service calls. If a certificate is missing or expired, the consumer applies fail-closed policy (treat as UNVERIFIED).

**Appendix E: Terminology & Glossary**

| **Term**                 | **Definition**                                                                                                                 |
|--------------------------|--------------------------------------------------------------------------------------------------------------------------------|
| Theatre                  | A structured environment defined by a Theatre Template. The atomic unit of bounded inquiry in Echelon: market creation (Market Theatres), construct verification (Product Theatres), investigation, inspection, survey, or scrutiny. |
| Theatre Template         | A JSON specification conforming to the Echelon Theatre Schema v2.0.1, defining all parameters for a class of bounded inquiries. |
| Bounded Inquiry          | A time-limited, evidence-committed investigation with certifiable resolution. The universal primitive underlying all Echelon timelines. Five types: counterfactual, investigative, inspection, survey, scrutiny. |
| Inquiry Type             | Classification of how evidence accumulates and resolution triggers within a Theatre. One of: counterfactual (simulation divergence), investigative (OSINT discovery), inspection (compliance check), survey (opinion aggregation), scrutiny (adversarial audit). |
| Discovery Market         | A Market Theatre with investigative inquiry type where evidence accumulates through OSINT agent discovery rather than simulation. Market participants bet on outcomes as evidence surfaces. The market funds the investigation through trading fees. |
| Investigative Timeline   | A timeline (bounded inquiry) where OSINT agents crawl real-world data sources to surface evidence. Market participants adjust positions as the evidence bundle grows. Resolution triggers when evidence threshold is met or time window closes. |
| Scrutiny Market          | A Market Theatre where an adversarial audit is conducted against a claim. Participants take positions on whether the claim survives scrutiny. Resolution is claim verified or falsified against committed evidence. |
| Creator-Generated Market | A market launched by an investigator or domain expert who commits their research methodology and evidence sources. Revenue model: percentage fee on volume (typically 1%), no token, time-bounded. |
| Funded Investigation     | The economic model where market trading fees fund OSINT agent operation and evidence gathering. The market is not just aggregating opinions — it is financing and directing investigative work. |
| Product Theatre          | A Theatre with execution_path = replay. Verifies AI construct capabilities against engineering ground truth via the Replay Engine. No LMSR markets, no agents, no trading. Primarily serves inspection and scrutiny inquiry types. |
| Market Theatre           | A Theatre with execution_path = market. Creates prediction markets using the full LMSR lifecycle with agents and trading. Serves all five inquiry types. |
| Execution Path           | The `execution_path` field in a Theatre Template: `replay` (Product Theatre) or `market` (Market Theatre). Determines which lifecycle behaviour applies. |
| Replay Engine            | The execution engine for Product Theatres. Commits parameters, invokes real constructs via OracleAdapter, scores outputs against ground truth, and issues calibration certificates. |
| Fork                     | A decision point within a Theatre where agents select from constrained options and markets price the probability distribution. |
| Wing Flap                | An atomic causal event recorded by the Butterfly Engine. Every significant action that modifies simulation state.              |
| Logic Gap                | The divergence between market-implied probabilities and committed OSINT reality signals. Measured as a percentage.             |
| Paradox                  | An integrity mechanism that activates when Logic Gap or stability exceeds pre-committed thresholds.                            |
| LMSR                     | Logarithmic Market Scoring Rule. The cost-function market maker providing always-on liquidity with bounded loss.               |
| Liquidity Parameter (b)  | The committed capital controlling LMSR price sensitivity. Larger b = deeper liquidity = higher maximum loss.                   |
| Commitment Hash          | SHA-256 hash of the full canonicalised template JSON plus version pins and dataset hashes, published before execution opens. Computed using canonical JSON (RFC 8785). |
| Canonical JSON           | Deterministic JSON serialisation per RFC 8785: sorted keys, no whitespace, normalised floats, nulls included. Used for all commitment hash computations. |
| RLMF                     | Reinforcement Learning from Market Feedback. The training data product derived from market-implied probability distributions and construct verification replays. |
| Calibration Certificate  | A structured record produced by every completed Theatre. Contains criteria scores, calibration metrics, reproducibility pins, evidence bundle hash, and verification tier. Gates construct access to model routing tiers. |
| Verification Tier        | Trust level assigned to a construct based on Theatre evidence: UNVERIFIED (< 50 replays or missing pins), BACKTESTED (≥ 50 replays + full pins), PROVEN (BACKTESTED + production telemetry + attestation). Tiers expire without ongoing verification. |
| Constraint Yielding Gate | Hard framework rule: UNVERIFIED constructs declaring `review: skip` are always treated as `review: full`. Only BACKTESTED or PROVEN constructs may yield quality gates. |
| Criteria IDs             | Deterministic snake_case identifiers (e.g., `source_fidelity`, `hex_grid_accuracy`) that become canonical keys in certificate scores. Domain-specific and human-defined per template. |
| OracleAdapter            | The interface through which Product Theatres invoke constructs. Supports HTTP (remote), local (subprocess), and mock (CI-only) transports. Standardised request/response envelope with timeout, retry, and error taxonomy. |
| Evidence Bundle          | The auditable artefact backing a calibration certificate. Contains: manifest, committed template, ground truth, invocation records, per-episode scores, aggregate results, certificate, and audit trail. Hash-verified for integrity. |
| Brier Score              | A calibration metric measuring the accuracy of probabilistic predictions. Lower is better. Range: 0 to 1.0.                    |
| ECE                      | Expected Calibration Error. Measures reliability of confidence estimates across prediction bins.                               |
| VRF                      | Verifiable Random Function. Produces unpredictable, unbiasable randomness with on-chain cryptographic proof.                   |
| Resolution State Machine | The pre-committed procedure that consumes committed inputs and deterministically produces a market or verification outcome. Steps may include construct invocations, deterministic computations, HITL rubric scoring, and aggregation. |
| Founder's Yield          | Revenue earned by the agent whose Wing Flap spawned a Timeline Fork. Proportional to stability and volume.                     |
| Agent Tax                | The problem of high inference costs making autonomous agents economically unviable at scale.                                   |
| OSINT Source Registry    | The authoritative catalogue of data sources eligible for Market Theatre resolution. Maintained as a versioned JSON document with per-source metadata, independence tracking, and settlement eligibility assessment. |
| Settlement-Eligible Source | A registry source meeting strict criteria for use as primary resolution evidence: official API, machine-readable output, documented revision policy, deterministic receipt hashing. |
| HTTP Transcript Receipt  | A deterministic hash of the canonical HTTP exchange (method, URL, headers, response body, timestamp) produced during OSINT data collection. Enables third-party verification of data retrieval. |
| Independence Upstream ID | A registry field linking sources that share a common data lineage. Prevents double-counting corroboration from non-independent sources. |
| Counter-Signal Class     | A taxonomy of contradictory evidence types (11 classes in v2) evaluated during composed oracle corroboration. Examples: conflicting regulatory filings, contradictory market signals, temporal inconsistency. |
| Cold-Path Consumption    | The pattern by which downstream systems consume calibration certificates: cached artefacts polled on schedule, not live service calls. Fail-closed on missing or expired certificates. |
| Verifier CLI             | The standalone command-line tool enabling third-party verification of any Echelon certificate. Performs 21 checks across structural integrity, template conformance, score mathematics, and cryptographic chain categories. |
| Five-Layer Stack         | The canonical integration architecture: Echelon (evaluation) → Constructs (expertise) → Hounfour (runtime) → Arrakis (distribution) → Consumer (touchpoints). |
| World Monitor            | Open-source OSINT dashboard (forked from koala73/worldmonitor) providing real-time RSS feeds, CII scores, convergence detection, and AIS chokepoint monitoring. Consumed via clean API boundary (AGPL-3.0). |
| Composite Instability Index (CII) | A multi-factor instability score produced by World Monitor, aggregating political, economic, social, and security indicators for a geographic region. |
| Composed Oracle          | The three-stage pipeline (collection → corroboration → scoring) that builds resolution evidence from multiple OSINT Source Registry sources. Produces confidence-weighted evidence bundles with deterministic receipt hashing. |
| Arrears State Machine    | A 12-state lifecycle model for distressed property debt resolution, from CURRENT through to RECOVERY_COMPLETE or WRITE_OFF. Enables deterministic verification of debt resolution procedures. |
| Kitchen Brigade          | The Hounfour runtime's model routing architecture, analogous to a restaurant kitchen: Layer 1 heuristic (< 10ms) → Layer 1.5 personality → Layer 2 LLM. Tier assignment gated by Echelon verification certificates. |

**Appendix F: Issued Certificates Register**

As of February 2026, Echelon has issued 8 calibration certificates across 3 verification verticals, covering 10 templates with 77+ fixtures and 189 verifier checks.

| **Certificate** | **Vertical** | **Template** | **Composite** | **Fixtures** | **Verifier** | **Tier** |
|---|---|---|---|---|---|---|
| Observer construct verification | Construct | PRODUCT_OBSERVER_V1 | 0.7000 | 1 (1p/0f) | 21/21 PASS | UNVERIFIED |
| Distribution Waterfall | Real Estate | DISTRIBUTION_WATERFALL_V1 | 1.0000 | 10 (10p/0f) | 21/21 PASS | UNVERIFIED |
| Escrow Milestone Release | Real Estate | ESCROW_MILESTONE_RELEASE_V1 | 0.9091 | 11 (6p/5f) | 21/21 PASS | UNVERIFIED |
| Ledger Reconciliation | Real Estate | LEDGER_RECONCILIATION_V1 | 1.0000 | 10 (10p/0f) | 21/21 PASS | UNVERIFIED |
| Arrears Resolution | Real Estate | ARREARS_RESOLUTION_V1 | 1.0000 | 10 (10p/0f) | 21/21 PASS | UNVERIFIED |
| LMSR Market Hygiene | LMSR Engine | QUANT_MARKET_HYGIENE_V1 | 0.9460 | 10 (3p/7f) | 21/21 PASS | UNVERIFIED |
| LMSR Perturbation Harness | LMSR Engine | QUANT_MARKET_PERTURBATION_HARNESS_V1 | 0.9800 | 10 (9p/1f) | 21/21 PASS | UNVERIFIED |
| LMSR API Fidelity | LMSR Engine | QUANT_MARKET_API_FIDELITY_V1 | 0.9050 | 10 (7p/3f) | 21/21 PASS | UNVERIFIED |
| LMSR b-Sensitivity Suite | LMSR Engine | LMSR_B_SENSITIVITY_SUITE_V1 | 1.0000 | 5 (5p/0f) | 21/21 PASS | UNVERIFIED |

All certificates are currently at UNVERIFIED tier due to fixture counts below the 50-episode BACKTESTED threshold. The Observer certificate requires rerun with --limit 50+ when the Constructs Network API is healthy.

*Document End*

Echelon Protocol \| Version 13.0 \| February 2026

*This document is a technical specification and does not constitute investment, legal, or financial advice.*
