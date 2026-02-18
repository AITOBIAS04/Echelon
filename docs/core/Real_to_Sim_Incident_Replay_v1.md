**Real-to-Sim: Incident Replay and Counterfactual Markets**

**Partner insert: tiered seed model, privacy posture, and commercial outputs**  
**Version 1.0 \| 13 January 2026**

**1. Overview**

Real-to-Sim turns historical partner failures into replayable Echelon episodes. Partners provide an incident seed; Echelon compiles a **Scenario Pack** and runs counterfactual markets at moments of uncertainty (fork points). The result is an **RLMF dataset aligned to real-world edge cases**, suitable for evaluation, training, and robustness testing.

Real-to-Sim is designed as an adoption ladder: partners can begin with low-friction seeds (no raw sensor logs) and move to higher fidelity only when required.

**2. Tiered seed model (adoption ladder)**

Partners can start with low-friction inputs and progressively increase fidelity:

- **Tier 1 — Incident descriptor (lowest friction)**  
  Structured report of what happened (constraints, environment type, failure label) plus optional clip/screenshot.  
  *Best for:* first pilots, fast iteration, internal alignment.

- **Tier 2 — Event telemetry (medium fidelity)**  
  Trajectories, object tracks, occupancy grids, lane graph snippets, object lists, planner outputs, and metadata. No raw camera/LiDAR required.  
  *Best for:* meaningful replay without sharing raw sensor data.

- **Tier 3 — Full sensor logs (highest fidelity)**  
  ROS bag / full sensor suite (camera, LiDAR, radar, IMU), plus stack metadata. Typically requires VPC or on-prem ingestion and strict access controls.  
  *Best for:* high-stakes validation, precise counterfactual reconstruction, and deep sim-to-real transfer.

**3. What Echelon delivers**

Echelon returns a consistent set of partner-facing outputs:

- **Scenario Pack (replayable episode bundle)**  
  Deterministic seed_hash, engine/version pins, asset pack version, ruleset version, and reproducible settlement settings.

- **Fork-point market map (counterfactual decision markets)**  
  A schedule of where the market prices decisions and outcomes — producing market-implied action value distributions (Q-like labels).

- **RLMF export (training/evaluation dataset)**  
  State snapshots, fork options, implied Q distributions, perturbations applied, and realised returns/outcomes. Includes calibration diagnostics (when the market was right/wrong, and by how much).

- **Counterfactual report (decision-grade insights)**  
  Ranked “what would have prevented this?” strategies, robustness gaps, and sensitivity to perturbations (e.g., occlusion, sensor jitter, constraint shifts).

**4. Privacy, security, and data rights posture**

Default posture: **minimise raw exposure, maximise auditability of derived outputs**.

- **Minimise raw data**  
  Prefer Tier 1–2 seeds where sufficient; Tier 3 only when fidelity requires it.

- **PII protection**  
  Where applicable: face/plate redaction; sensitive identifiers hashed or removed at ingest.

- **Access tiering**  
  Strict separation between **raw artefacts** (restricted) and **derived claims / RLMF exports** (shareable), subject to partner policy.

- **Encryption and keying**  
  Encryption in transit and at rest; scoped keys per partner workspace; optional customer-managed keys.

- **Retention controls**  
  Configurable retention windows; partner-controlled deletion workflows.

- **Deployment options**  
  Cloud, VPC, or on-prem ingestion for sensitive datasets.

- **Licensing controls**  
  Licensed sources accessed via approved terms; downstream redistribution governed at the adapter layer.

**5. Illustrative example**

**Input:** a short incident where an autonomy agent hesitates around an unexpected cone layout.  
**Output:** a “Cone Corridor” episode compiled into the Navigation template, with fork markets such as “reroute vs commit”, “wait vs proceed”, and “left gap vs right gap”, plus bounded perturbations (occlusion, sensor jitter, constraint shifts) and a reproducible settlement trace.
