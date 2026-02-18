**Echelon OSINT & Reality Oracle Appendix**

*Partner overview: data acquisition, provenance, disputes, Scenario Factory, and Real-to-Sim incident replay*

**Version 3.1 \| 17 February 2026**

1\. Purpose and scope

This appendix describes how Echelon converts open-source intelligence (OSINT), licensed data feeds, and partner incident seeds into a verifiable Reality Oracle. The oracle is used to:

- Create and maintain timelines via causal Theatre inputs (not market context).

- Measure the Logic Gap between market belief and observed reality.

- Settle disputes with audit-grade provenance.

- Compile Real-to-Sim incident replays into counterfactual, market-driven training episodes.

1.1 Architectural role of OSINT

Echelon’s OSINT requirements differ fundamentally from those of conventional prediction markets. On platforms such as Polymarket or Kalshi, external data provides context for human traders. In Echelon, OSINT signals are causal inputs to Theatre state machines. Specifically:

- **Timeline instantiation:** OSINT anomalies (e.g. AIS dark-fleet detection) trigger the Mission Factory to spawn new Theatre timelines.

- **Fork-point triggers:** Structured events within active Theatres deterministically trigger fork points at which agents and users trade against the LMSR cost function.

- **Logic Gap calculation:** The Reality Oracle measures the divergence between market-implied probability and OSINT-derived observed state. This is the integrity mechanism that triggers Paradox events.

- **Deterministic settlement:** Pre-committed oracle escalation resolves timelines from auditable evidence bundles, not subjective interpretation.

This means Echelon requires oracle-grade structured signals—entity-extracted, confidence-scored, timestamped events—not raw news feeds. The pipeline engineering required to produce these signals is as important as the underlying data sources.

1.2 OSINT latency ≠ entropy heartbeat

The System Bible (§VII) specifies a 60-second entropy heartbeat driven by Chainlink VRF V2 on Base Mainnet. This is a randomness injection cycle for active Theatres—it governs when VRF callbacks deliver unpredictable, verifiable entropy to the simulation engine. It is not an OSINT ingest requirement.

OSINT latency operates on a different timescale and serves different system functions:

- **Timeline spawning** (minutes acceptable): the Mission Factory detects anomalies, evaluates Engagement Scores, and publishes new timelines. Minute-level latency is sufficient; the value is in signal quality and corroboration, not speed.

- **Logic Gap calculation** (minutes acceptable): the Reality Oracle periodically recalculates the divergence between market-implied probability and observed state. This runs on a configurable interval (typically 1–5 minutes), not on the VRF heartbeat.

- **Fork trigger conditions** (minutes acceptable): fork points within active Theatres are triggered by structured events meeting pre-committed thresholds. These are evaluated when new evidence bundles arrive, not on a fixed clock.

Conflating these two systems—claiming that OSINT must match the 60-second VRF cycle—would overstate ingest requirements and inflate vendor costs without architectural justification. The VRF heartbeat is cryptographic infrastructure; the OSINT pipeline is intelligence infrastructure. They are coupled only insofar as OSINT evidence bundles feed the Logic Gap formula, which in turn may trigger Paradox events that consume VRF entropy.

2\. Data sources (multi-source by design)

Echelon is deliberately multi-source. No single feed is treated as authoritative. The oracle aggregates evidence across modalities, scores confidence, and versions outputs so that partners can reproduce the state of belief at any point in time.

2.1 Illustrative provider mix

- Market and reference data: Polygon.io (institutional equities, forex, options), licensed terminals/APIs where available.

- News and sentiment: RavenPack (event and sentiment tagging across 40,000+ sources), Dataminr (real-time breaking-event detection), selected press-wire/RSS feeds.

- Social diffusion: X API / xAPI (geo-clustering, narrative propagation, velocity).

- Maritime: Spire Global AIS or Kpler (satellite AIS for dark-fleet detection, AIS gaps, anomaly flags). Note: Spire’s maritime division is subject to a pending acquisition by Kpler—supply-chain risk addressed in Section 7.4.

- Aviation: ADS-B sources, FlightRadar24 or FlightAware (route anomalies, VIP movement proxies).

- On-chain: Whale Alert, Arkham Intelligence (attribution, exchange flows, large transfers).

- Open proxies: GDELT (event database, free), NASA Black Marble (night-light anomalies as outage/conflict proxy, free).

- Browser-based OSINT automation: Notte (credentialed browsing, session automation, high-availability extraction where APIs are insufficient).

- Prediction market feeds: Polymarket (public read-only market data API, Gamma markets) and Kalshi (developer API, public market data endpoints). Used as signal intercepts—existing market-implied probabilities on related events provide calibration anchors for Echelon’s own LMSR markets. Free read access; cost is engineering (normalisation, deduplication, confidence classification). See Section 2.3 for normalisation policy.

2.2 Why multi-source matters

- **Resilience:** Provider outages do not stall timelines.

- **Integrity:** Conflicting signals are surfaced and scored, not silently overwritten.

- **Auditability:** Each claim is traceable to evidence bundles, timestamps, and transforms.

- **Partner flexibility:** Feeds can be swapped or supplemented without redesigning settlement logic.

2.3 Evidence Bundle Schema (provenance and tamper-evidence)

Echelon’s commitment protocol (System Bible §VI) locks Theatre parameters at creation. The OSINT inputs that drive settlement require the same integrity guarantee. Every data point that enters the pipeline—whether it triggers a fork, updates the Logic Gap, or contributes to a resolution claim—must be captured in an append-only evidence store with cryptographic provenance. Without this, “deterministic resolution from verifiable inputs” has a hole at the input layer.

Each evidence bundle is a structured object containing the following fields:

- **bundle_id:** Unique identifier (UUID v4). Immutable once created.

- **raw_payload:** Exact response body from the source API or feed, stored as-is before any transformation.

- **retrieval_receipt:** Structured metadata capturing: retrieval timestamp (UTC, millisecond precision), source_id (provider + feed identifier), query_params (exact API call parameters), adapter_version (software version of the ingestion adapter), and HTTP status code.

- **content_hash:** SHA-256 hash of the raw_payload. This is the tamper-evidence primitive. Any post-hoc modification to the payload invalidates the hash.

- **structured_extract:** The NLP-processed, entity-extracted, confidence-scored output produced by the pipeline. This is what downstream systems (Mission Factory, Logic Gap calculator) actually consume. Linked to the raw_payload via content_hash for full traceability.

- **confidence_score:** Float \[0.0, 1.0\] representing the pipeline’s assessed reliability of the extracted signal. Derived from source tier, corroboration status, and NLP extraction confidence.

- **theatre_id:** The Theatre(s) this bundle was ingested for. One raw payload may produce evidence bundles for multiple active Theatres.

**Merkle root publication.** Periodically (configurable; default every 100 bundles or every 15 minutes, whichever comes first), the evidence store computes a Merkle root over all new content_hash values and publishes it. At MVP this can be published off-chain (e.g. to a public append-only log or IPFS). At scale, periodic Merkle roots can be anchored on-chain for cryptographic non-repudiation. This ensures that the entire evidence history is tamper-evident without requiring every individual bundle to be written on-chain.

**Cost implications.** The evidence store is engineering cost, not data cost. Object storage (S3/R2) is cheap. Hashing is computationally negligible. The work is in the adapter layer that captures retrieval receipts with each ingest and the normalisation pipeline that links structured extracts back to raw payloads. This is accounted for within the Phase 1 pipeline infrastructure budget (Section 7.2).

2.4 Prediction market feed normalisation

Polymarket and Kalshi provide free read-only market data that functions as a valuable OSINT signal class—existing market-implied probabilities on events that overlap with Echelon Theatres. Ingesting these feeds requires a normalisation layer with three components:

- **Schema mapping:** External contracts are mapped into Echelon’s internal format: market_id, underlying_event, resolution_source, expiry, implied_probability, volume, liquidity_depth, and last_update timestamp. This allows uniform consumption regardless of source platform.

- **Deduplication:** Many events overlap across Polymarket and Kalshi (e.g. both may offer markets on the same election outcome or Fed rate decision). The normalisation layer detects semantic duplicates and merges them into a single signal with source attribution, preventing double-counting in downstream analytics.

- **Confidence classification:** External market prices are classified into two roles. A **signal intercept** is informational—the price is logged and available for agent reasoning but does not directly weight the Logic Gap or settlement. An **input feature** is operationally weighted—used as a direct input to agent decision models or as a corroboration source for resolution claims. The classification is committed at Theatre creation to prevent post-hoc manipulation of how external signals influence settlement.

3\. OSINT-to-Timeline pipeline (Mission Factory)

The Mission Factory converts world signals into publishable timelines. The technical flow is Listener → Analyser → Publisher; the crucial “why” is the Engagement Logic. Before a timeline is published, the Analyser evaluates an Engagement Score and rejects events that are stale, low-stakes, or narratively weak.

3.1 Engagement Score (example factors)

- Narrative strength: is the “what if” compelling?

- Timeliness: is it happening now, with urgency?

- OSINT richness: corroboration across independent modalities.

- Volume potential: adjacent markets and liquidity likelihood.

- Stakes/controversy: will humans care?

- Ripple potential: can this cascade into other timelines?

3.2 Published object (timeline)

A timeline is published as:

- Narrative wrapper and market parameters (question, resolution, constraints).

- Oracle inputs (evidence bundles) with timestamps and confidence scores.

- Deterministic configuration hashes enabling reproducible settlement and post-mortems.

3.3 Corroboration requirements

Section 2.2 establishes that Echelon is multi-source by design. This subsection formalises a minimum corroboration requirement that is enforced at Theatre creation, not merely encouraged as best practice.

**Minimum cardinality rule.** Every resolution variable in a Theatre must declare a minimum of two independent corroboration sources at Theatre creation. These are committed as part of the Theatre Template and locked by the commitment protocol (System Bible §VI). A resolution claim that relies on a single source is automatically flagged for dispute review.

**Independence requirement.** Corroboration sources must be from different modalities or providers. Two articles from the same news wire do not satisfy the requirement. Two signals from independent modalities (e.g. GDELT news event + AIS anomaly, or Polygon.io price movement + official government filing) do satisfy it. The goal is to prevent single-source manipulation where a compromised feed could trigger false settlement.

**Theatre Template schema addition.** The Theatre Template schema (System Bible §II) should include a corroboration_sources field for each resolution variable, with a minimum cardinality of 2. Each entry specifies: source_provider, source_modality, and the resolution_role (primary evidence or secondary corroboration).

**Illustrative examples:**

- Theatre resolves on “port closure”: primary = GDELT event detection + official port authority notice/RSS; corroboration = AIS anomaly (vessel diversion patterns from Spire/MarineTraffic).

- Theatre resolves on “earnings miss”: primary = Polygon.io price movement exceeding committed threshold; corroboration = SEC filing / company press release via RSS adapter.

- Theatre resolves on “sanctions escalation”: primary = official government gazette / OFAC list update; corroboration = GDELT event cluster + Polymarket implied probability shift (signal intercept role, per Section 2.4).

This requirement is deliberately low-friction at MVP—it uses the cheap corroborators already in the Phase 1 pipeline (GDELT, RSS, Polygon.io, public market feeds) rather than mandating enterprise providers. It prevents single-source manipulation while keeping costs within the Phase 1 budget envelope.

4\. Scenario Factory (Theatre of primitives)

Complex Theatres are produced via a parallel pipeline that compiles “episodes” rather than news markets. Echelon standardises a Scenario Pack as a publishable object:

**Scenario Pack = deterministic seed + objective vector + fork markets + bounded saboteur deck + settlement rules + telemetry schema**

4.1 Inputs: synthetic, OSINT-derived, and Real-to-Sim seeds

- **Synthetic seeds:** Procedural parameters (weather, crowd density, comms latency, sensor noise).

- **OSINT-derived seeds:** Anomalies mapped into Theatre templates (e.g. “AIS ghost” → maritime convoy episode).

- **Real-to-Sim seeds:** Partner incidents compiled into counterfactual episodes (see Section 5).

4.2 Pipeline (high level)

Signal Listener (synthetic seeds, OSINT seeds, Real-to-Sim seeds) → Scenario Proposer (chooses template + difficulty, filters impossible scenarios) → Theatre Compiler (maps seed to template library, auto-forks at uncertainty spikes, generates bounded saboteur deck) → Referee Oracle (simulation log is the truth, emits RLMF export: state, fork, market-Q, outcomes).

4.3 Deterministic settlement (“Referee” oracle)

Fork-point markets are settled deterministically from simulation logs. This avoids subjective judging and ensures that market prices can be safely used as training labels (e.g. market-implied Q-values) with full reproducibility.

5\. Real-to-Sim: incident replay and counterfactual markets

Real-to-Sim turns historical partner failures into playable Echelon episodes. Partners provide an incident seed; Echelon compiles a Scenario Pack and runs counterfactual “what should have happened?” markets at moments of uncertainty. The output is an RLMF dataset aligned to real-world edge cases.

5.1 Tiered seed model (adoption ladder)

- **Tier 1 (Incident descriptor):** Structured report + optional clip. Lowest integration burden; fastest pilots.

- **Tier 2 (Event telemetry):** Trajectories, tracks, occupancy grids, lane graphs, object lists. No raw camera/LiDAR required.

- **Tier 3 (Full sensor log):** ROS bag / full sensor suite (camera, LiDAR, radar, IMU). Highest fidelity; often requires on-prem or restricted processing.

5.2 What Echelon returns

- Compiled Scenario Pack (seed_hash, engine_version, asset_pack_version, ruleset_version).

- Fork-point market map (where the market prices decisions and outcomes).

- RLMF export: state snapshots, fork options, market-implied Q distributions, perturbations, and realised returns.

- Counterfactual analysis: ranked strategies and robustness gaps linked to the original incident.

5.3 Illustrative example

Input: a 10-second incident where an agent hesitates around an unexpected cone layout. Output: a “Cone Corridor” episode compiled into the Navigation-under-uncertainty template, with fork markets such as “reroute vs commit”, “wait vs proceed”, and “left gap vs right gap”, plus bounded perturbations (occlusion, sensor jitter, constraint shifts).

6\. Privacy, security, and data rights posture

Echelon’s default posture is to minimise raw data exposure while maximising auditability of derived claims and training outputs.

- **Data minimisation:** Prefer Tier 1–2 seeds where possible; Tier 3 only when required.

- **PII controls:** Redaction/blurring (faces, plates) where applicable; sensitive identifiers hashed or removed at ingest.

- **Access tiering:** Strict separation between raw artefacts (restricted) and derived claims/RLMF exports (shareable).

- **Encryption:** In transit and at rest; scoped keys per partner workspace.

- **Retention controls:** Configurable retention windows and partner-controlled deletion workflows.

- **Deployment options:** Cloud, VPC, or on-prem incident ingestion for sensitive datasets.

- **Audit logs:** Immutable provenance logs for access, transforms, and settlement-critical changes.

- **Licensing:** Licensed sources accessed via approved terms; redistribution controlled at the adapter layer.

7\. OSINT budget and data strategy

7.1 Budget philosophy

Echelon’s OSINT budget is structured around a phased validation approach rather than a fixed monthly run-rate. Enterprise data providers in this space (RavenPack, Dataminr, Spire Global) do not publish pricing; contracts are negotiated on a bespoke basis determined by coverage scope, latency tier, user count, and historical backfill requirements. Quoting specific per-provider costs without actual sales conversations produces unreliable estimates.

Instead, the budget is organised into three phases, each gated by validation milestones. OSINT spend scales only when signal quality requirements exceed what the current tier can deliver.

7.2 Phased budget model

**Phase 1 — MVP Validation (Months 1–4)**

|                         |                                                                                                                                                                 |                     |                                                                                                                                                                                                                                                            |
|-------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Domain**              | **Approach**                                                                                                                                                    | **Est. Cost/Mo**    | **Rationale**                                                                                                                                                                                                                                              |
| News / events           | GDELT + custom NLP pipeline (spaCy, entity extraction, confidence scoring)                                                                                      | \$500–\$800         | Free source; cost is compute + engineering. Sufficient for Theatre template validation.                                                                                                                                                                    |
| Social signals          | X API Basic tier + custom filtering (Pro tier at \$5,000/month deferred to Phase 2; social adapter designed provider-agnostic for upgrade or alternative feeds) | \$200               | Basic tier: 10,000 tweets/month read access. Sufficient for 2–3 Theatres with batched ingestion. Pro tier (\$5,000/month) deferred until Phase 2 validation gate.                                                                                          |
| Maritime AIS            | MarineTraffic API + evaluate Spire/Kpler trial access                                                                                                           | \$100–\$500         | Terrestrial AIS for initial validation. Satellite AIS trials to be negotiated directly.                                                                                                                                                                    |
| Market data             | Polygon.io professional tier                                                                                                                                    | \$200–\$500         | Equities, forex, options. Established pricing, publicly listed tiers.                                                                                                                                                                                      |
| Aviation                | FlightAware or ADS-B Exchange developer API                                                                                                                     | \$100–\$300         | Route anomaly detection for geopolitical Theatres.                                                                                                                                                                                                         |
| On-chain                | Whale Alert + Arkham free/basic tiers                                                                                                                           | \$0–\$200           | DeFi Theatre inputs. Basic tiers sufficient for MVP.                                                                                                                                                                                                       |
| Open proxies            | GDELT + NASA Black Marble                                                                                                                                       | Free                | Night-light anomalies, conflict proxies. No licensing cost.                                                                                                                                                                                                |
| Prediction market feeds | Polymarket + Kalshi read APIs + normalisation layer                                                                                                             | Free                | Signal intercepts for calibration. Free read access; engineering cost covered by pipeline infra. See Section 2.4.                                                                                                                                          |
| Pipeline infra          | AWS Lambda + S3 + normalisation layer + evidence store (Section 2.3)                                                                                            | \$400–\$600         | Orchestration, storage, Theatre-ready signal transforms. Includes evidence store (Section 2.3): object storage for raw payloads, hash receipts, and periodic Merkle root computation.                                                                      |
| **TOTAL (Phase 1)**     |                                                                                                                                                                 | **\$1,500–\$3,100** | Engineering-intensive; trades vendor cost for development effort. Includes evidence store (Section 2.3), prediction market feed normalisation (Section 2.4), and corroboration infrastructure (Section 3.3). X API at Basic tier; Pro deferred to Phase 2. |

Phase 1 gating metric: demonstrate Brier score \< 0.25 on at least three Theatre templates using the engineered pipeline. Signal quality, not vendor prestige, determines whether to proceed.

**Phase 2 — Partner Validation (Months 5–8)**

|                   |                                                   |                  |                                                                                         |
|-------------------|---------------------------------------------------|------------------|-----------------------------------------------------------------------------------------|
| **Upgrade**       | **Vendor**                                        | **Est. Cost/Mo** | **Trigger**                                                                             |
| News analytics    | RavenPack (base tier, annual contract)            | Quote required   | Brier score validation passed; need structured event feeds for robotics partner pilots. |
| Satellite AIS     | Spire Global / Kpler (negotiate post-acquisition) | Quote required   | Ghost Tanker Theatre requires satellite coverage of contested maritime zones.           |
| Real-time alerts  | Dataminr (financial or Pulse tier)                | Quote required   | Sub-minute event detection for Fed Rate, DeFi, and breaking-news Theatres.              |
| Social enterprise | X API Enterprise / xAPI upgrade                   | Quote required   | Full geo-clustering and narrative propagation at scale.                                 |

Phase 2 budget envelope: the grant allocates a total OSINT data budget (see Section 7.3). Actual per-provider costs will be determined by direct sales negotiations during Months 3–4, informed by Phase 1 validation results and precise coverage requirements.

**Phase 3 — Scale (Months 9+)**

At scale, the OSINT stack may include full enterprise tiers across multiple providers, historical backfill purchases (which are typically one-time costs negotiated separately), and derived analytics layers. Phase 3 spend is funded by platform revenue and/or Series A capital, not grant funds.

7.3 Grant budget allocation

Within the broader \$300K grant structure, the OSINT/Data Infrastructure allocation is \$100,000 over 6 months. This covers:

- Phase 1 pipeline engineering and compute costs (Months 1–4): approximately \$15,000–\$20,000 total.

- Enterprise data contract negotiations and initial subscriptions (Months 3–6): approximately \$50,000–\$60,000, deployed only upon Phase 1 validation.

- Historical backfill and one-time data purchases: approximately \$15,000–\$20,000, scoped to specific Theatre templates requiring retrospective training data.

- Contingency for pricing variance: approximately \$10,000, reflecting the inherent uncertainty in enterprise contract negotiations.

7.3.1 What is verifiable

The following pricing references are drawn from public sources. All other provider costs are enterprise-negotiated and cannot be reliably estimated without direct engagement.

|              |                                                                                                                                                   |                               |                                                                                                                  |
|--------------|---------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------|------------------------------------------------------------------------------------------------------------------|
| **Provider** | **Verifiable Data Point**                                                                                                                         | **Source**                    | **Implication for Echelon**                                                                                      |
| Polygon.io   | Professional tiers publicly listed; institutional access from ~\$200/month upwards.                                                               | polygon.io/pricing            | Reliable, predictable cost. Budget with confidence.                                                              |
| RavenPack    | Knoema marketplace lists News Analytics at \$50–100K/year (annual contract, 60-day trials).                                                       | knoema.com                    | ~\$4–\$8K/month for base product. Custom enrichment and geopolitical taxonomies would push higher.               |
| Dataminr     | Aggregator sites cite ~\$10K/month minimum for single-user enterprise access. Pulse (corporate security) listed at ~\$15K/year on some platforms. | itqlick.com, zoftwarehub.com  | Financial-grade real-time API likely \$10K+/month. Pulse tier is corporate alerting, not the feed Echelon needs. |
| Spire Global | EMSA framework contract: €8.4M over 4 years (~€2.1M/year cap) for full satellite AIS coverage.                                                    | Spire press release, Feb 2024 | Government-scale pricing. Commercial tiers not public. Direct negotiation essential.                             |
| GDELT        | Free and open. No licensing cost.                                                                                                                 | gdeltproject.org              | Requires engineering investment (~\$500–\$800/month compute) to produce oracle-grade structured events.          |
| X API        | Pro tier ~\$5,000/month. Enterprise tier \$42K–\$210K/year (reported range).                                                                      | Various industry reports      | Pro tier sufficient for MVP geo-clustering. Enterprise for scale.                                                |

7.4 Supply-chain risks and mitigations

|                           |                                                                                                                                                                                            |                                                                                                                                                                       |
|---------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Risk**                  | **Detail**                                                                                                                                                                                 | **Mitigation**                                                                                                                                                        |
| Spire/Kpler acquisition   | Spire is selling its maritime division to Kpler (announced \$241M deal). Spire has filed suit against Kpler for delayed completion. Product continuity, pricing, and API terms may change. | Monitor transaction status. Evaluate Kpler’s existing analytics platform as alternative. Build maritime adapter layer with provider-agnostic interface.               |
| X API pricing volatility  | X/Twitter API pricing has changed multiple times since 2023 acquisition. Enterprise tier costs may shift without notice.                                                                   | Phase 1 uses Pro tier only. Social signal pipeline designed to accept alternative social feeds (Bluesky, Mastodon, Reddit) if X API becomes uneconomic.               |
| Enterprise vendor lock-in | Annual contracts with enterprise data providers typically require 12-month commitments. Early termination may not be possible.                                                             | Phase 2 contracts negotiated with 60-day trial clauses where possible. Normalisation layer ensures any provider can be swapped without downstream breakage.           |
| Signal quality gap        | Free/cheap sources (GDELT, MarineTraffic terrestrial) may not deliver oracle-grade signals for all Theatre templates.                                                                      | Phase 1 validation explicitly tests this. If Brier score targets are not met, enterprise feeds are introduced in Phase 2 with grant funds allocated for this purpose. |

7.5 Three knobs that dominate cost

When engaging enterprise data providers, three parameters drive the majority of pricing variance:

- **Simultaneous Theatre count:** How many live Theatres require concurrent OSINT coverage? At MVP (3–5 Theatres), domain-specific feeds are sufficient. At scale (50+ Theatres), global multi-vertical coverage is required.

- **Latency target:** Sub-second event detection (Dataminr-grade) costs an order of magnitude more than 5-minute enriched feeds (RavenPack-grade). For MVP, minute-level latency is acceptable for most Theatre templates.

- **Historical backfill:** Retrospective data (6–24 months) for training the Mission Factory’s pattern recognition is typically a one-time purchase negotiated separately from ongoing subscriptions. This is where costs can escalate rapidly.

7.6 Grant application language (recommended)

> *“OSINT Infrastructure: \$100K allocated across a 6-month phased programme. Phase 1 (Months 1–4): custom NLP enrichment pipelines over professional-grade open-source feeds (GDELT, public AIS, public market data) to produce oracle-grade structured events for Theatre state machines. Phase 2 (Months 5–6): enterprise validation feeds (negotiated directly with providers including RavenPack, Spire/Kpler, and Dataminr) deployed upon successful signal-quality validation with robotics partners. All OSINT feeds serve as causal inputs to Theatre state machines—enabling deterministic fork triggers, Logic Gap integrity mechanics, and auditable settlement—not market context. Per-provider allocations determined by direct contract negotiation during Months 3–4.”*

7.7 Previous budget table (superseded)

Earlier versions of this document included a fixed monthly budget table totalling ~\$18,000/month with specific per-provider line items. That table has been retired because:

- Per-provider costs were estimated without direct sales engagement and cannot be verified from public sources.

- Enterprise data vendors (RavenPack, Dataminr, Spire) do not publish pricing; bespoke contracts depend on scope, latency, and coverage.

- A fixed monthly run-rate does not reflect the phased validation approach appropriate for a grant-funded MVP.

The phased model in Section 7.2 replaces the previous table. The total 6-month OSINT envelope (\$100K) remains consistent with the broader \$300K grant structure.
