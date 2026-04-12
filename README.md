# Echelon

**Verification infrastructure for the agentic economy.**

Echelon is the system that determines which claims about the real world survive contact with reality. External builders ship domain-specialist constructs, live data feeds flow through oracle adapters, and prediction markets settle against ground truth. Every settlement makes the next verification more trustworthy. The product compounds.

## Architecture

Echelon is three tiers:

**Echelon Core** — the verification engine. Theatre evaluation, OSINT oracle composition, attestation minting, certificate schema, RLMF export, Knowledge Node compilation, on-chain registry. The infrastructure layer has no opinion about what is being verified or who is verifying it. It exposes APIs.

**Integration Layer** — everything that connects external systems to Core. Construct ingestion, FORGE proposal intake, external oracle adapters, the Constructs Network, sensor feeds, IoT inputs, news API outputs. This is where domain-specific intelligence enters the system. Seismic data, space weather, air quality, financial feeds, corporate registries — any domain with public, machine-readable data.

**Expression Layer** — the surfaces where humans and agents interact with verified intelligence. Workspace (thinking surface), Environment (memory and composition surface), Theatre Markets (pricing and public settlement). These surfaces feed data right back into Core — more markets settled means better calibration means more trustworthy verification.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           EXPRESSION LAYER                                  │
│                                                                             │
│  Workspace              Environment              Theatre Markets            │
│  Signal triage          Composition canvas        Prediction pricing        │
│  Investigation view     Knowledge Nodes           Public settlement         │
│  Aeon brief synthesis   Evidence provenance       RLMF data export         │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                          INTEGRATION LAYER                                  │
│                                                                             │
│  External Constructs    FORGE Factory             OSINT Pipeline            │
│  TREMOR (seismic)       Feed classification       16 sources, 14 collectors │
│  CORONA (space wx)      Proposal IR bridge        WorldMonitor (3 domains)  │
│  BREATH (air quality)   Admission + shadow mode   Evidence anchoring        │
│  Constructs Network     Trust tiers (T0-T3)       Oracle adapters           │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                            ECHELON CORE                                     │
│                                                                             │
│  Contract Substrate     Integrity Engine          Evaluation Pipeline       │
│  Construct contracts    Cross-theatre paradox     Multi-evaluator orchest.  │
│  Check planning         Oracle divergence         Convergence scoring       │
│  Certificate issuance   Network-level referee     Security domain packs     │
│                                                                             │
│  Proposal OS            Knowledge Compilation     RLMF Engine               │
│  Proposal IR            Node lifecycle            Position histories        │
│  Negative policy        Verified intelligence     Brier scores              │
│  Admission gate         Aeon-grounded synthesis   Calibration certificates  │
│                                                                             │
│  Base Chain             Composition Runtime                                 │
│  LMSR markets           Typed module contracts                              │
│  Chainlink VRF          Source independence                                 │
│  On-chain settlement    Input/output wiring                                 │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## What It Does

**Verification that compounds** — Every theatre settlement, attestation, and Knowledge Node compiled feeds back into Core's calibration. The more intelligence flows through the system, the more trustworthy the next verification becomes. Integration partners benefit from every other partner's data without seeing it.

**Theatre network** — Independent domain-specialist verification environments that ingest live public data, run prediction markets, settle against external ground truth, and export Brier-scored calibration data. Extensible to any domain with public, machine-readable data.

**Feed-to-theatre automation (FORGE)** — [FORGE](https://github.com/0xElCapitan/forge) takes any live data feed, characterizes its statistical properties, and proposes theatre templates via a versioned Proposal IR. Echelon's admission gate applies negative policy screening and routes admitted proposals into shadow mode before activation. FORGE proposes; Echelon decides.

**Construct contract verification** — External construct repos compile into evaluation contracts with deterministic check planning, multi-evaluator orchestration, and certificate issuance. Security domain packs use structured corpora with OWASP, CWE, and MITRE ATT&CK anchors.

**Cross-domain paradox detection** — A network-level integrity layer that detects contradictions across independently operated external theatres. Oracle divergence, settlement divergence, confidence inconsistency, and cross-domain divergence.

**OSINT intelligence pipeline** — 16 sources across 14 collectors covering financial markets, corporate registries, geospatial intelligence, environmental monitoring, and academic research. Evidence anchoring with snapshot/live asset classification and domain-specific anchor packs.

**RLMF training data** — Brier-scored certificates from theatre verification become structured training data exports. Position histories, calibration scores, and evidence bundles feed downstream AI systems through Reinforcement Learning from Market Feedback. The market is the annotation engine.

## External Theatre Constructs

Echelon verifies external theatre constructs built by independent operators:

| Construct | Domain | Oracles | Templates |
|-----------|--------|---------|-----------|
| [TREMOR](https://github.com/0xElCapitan/tremor) | Seismic intelligence | USGS NEIC, EMSC, IRIS DMC | 5 (Magnitude Gate, Aftershock Cascade, Swarm Watch, Depth Regime, Oracle Divergence) |
| [CORONA](https://github.com/0xElCapitan/corona) | Space weather | NOAA SWPC, NASA DONKI, GFZ Potsdam | 5 (Flare Class Gate, Geomagnetic Storm, CME Arrival, Proton Cascade, Solar Wind Divergence) |
| [BREATH](https://github.com/0xElCapitan/BREATH) | Air quality | PurpleAir, EPA AirNow | 3 (AQI Threshold Gate, Sensor Divergence, Wildfire Cascade) |
| [FORGE](https://github.com/0xElCapitan/forge) | Feed-to-theatre factory | Any structured data feed | Generates templates from feed grammar |

## Constructs Network

Echelon integrates with [constructs.network](https://constructs.network) — a marketplace for AI agent expertise built by [Soju](https://github.com/0xHoneyJar/loa-constructs). Construct types: skill, theatre, bridge. External builders ship construct repos; Echelon compiles, executes, compares, and scans them.

## Access

For access to the full codebase, contact [@tobiasjames_eth](https://x.com/tobiasjames_eth).

## Contact

Built by Tobias Harber — [@tobiasjames_eth](https://x.com/tobiasjames_eth)
