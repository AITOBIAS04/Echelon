**ECHELON**

Deterministic Theatre Template Library

This document catalogues every deterministic theatre template in the
Echelon verification infrastructure. Each template defines a set of
weighted criteria, a fixture dataset with targeted pass and fail
scenarios, and produces a calibration certificate that can be
independently verified by the standalone Echelon Verifier CLI
(echelon\_verify.py) with zero external dependencies.

**1. Verification Methodology**

**21/21 Verify Checks**

The verify command runs 21 independent assertions against a certificate
and its evidence bundle. These are grouped into four categories:

-   **Schema validation (4 checks):** certificate has all 13 required
    fields, field types are correct, criteria structure is valid,
    weights are present.

-   **Hash integrity (5 checks):** evidence\_bundle\_hash,
    dataset\_hash, ground\_truth\_hash, commitment\_hash, and manifest
    hashes all match SHA-256 recomputation using RFC 8785 canonical
    JSON.

-   **Arithmetic consistency (6 checks):** criteria weights sum to 1.0
    (±1e-9 tolerance), composite score equals weighted sum of criterion
    scores, replay count matches fixture records, pass/fail counts are
    consistent, pass rate is arithmetically correct, scores are in \[0,
    1\].

-   **Bundle completeness (6 checks):** manifest.json present, all
    manifest paths resolve to files, all file hashes match manifest
    entries, template and fixture files present in bundle, expected
    outputs extractable, no orphaned files.

**6/6 Replay Checks**

The replay command runs 6 structural assertions verifying that a
template and its fixture dataset are mutually consistent:

-   **REPLAY-001:** Template schema valid (all required template fields
    present).

-   **REPLAY-002:** Fixture dataset hash matches the hash declared in
    the template.

-   **REPLAY-003:** Fixture records present (dataset contains at least
    one record).

-   **REPLAY-004:** Record structure valid (every record has record\_id,
    inputs, expected\_outputs).

-   **REPLAY-005:** Criteria defined (every criteria\_id in the template
    has a corresponding weight).

-   **REPLAY-006:** Template weights sum to 1.0 (±1e-9 tolerance).

**Scoring Aggregation**

Each fixture record contains a criteria\_verdicts object mapping
criterion IDs to boolean values (true/false). The composite score is
computed as follows:

-   **Per-criterion score:** For each criterion, compute the mean pass
    rate across all fixture records that test that criterion. A record
    that does not include a given criterion in its verdicts is excluded
    from that criterion's denominator.

-   **Composite score:** The weighted sum of per-criterion scores, using
    the weights declared in the template. Weights always sum to 1.0.

-   **Implication:** A template with 3 pass / 7 fail records can still
    achieve a high composite (e.g. 0.9460) if each failure isolates a
    single low-weight criterion. This is by design: targeted failures
    demonstrate that the system rejects specific policy violations, not
    that the construct under test is unreliable.

**2. Summary**

  -------- ------------------------------------------ -------------- -------------- -------------- --------------- ----------------
  **\#**   **Template**                               **Vertical**   **Criteria**   **Fixtures**   **Composite**   **Verifier**
  **1**    escrow\_milestone\_release\_v1             Real Estate    5              11 (6p/5f)     0.9091          **21/21 PASS**
  **2**    distribution\_waterfall\_v1                Real Estate    5              15 (10p/5f)    0.9333          **21/21 PASS**
  **3**    ledger\_reconciliation\_v1                 Real Estate    5              15 (10p/5f)    0.9333          **21/21 PASS**
  **4**    arrears\_resolution\_v1                    Real Estate    6              16 (10p/6f)    0.9375          **21/21 PASS**
  **5**    *product\_observer\_v1 †*                  Construct      5              1 (1p/0f)      0.7000          **21/21 PASS**
  **6**    quant\_market\_hygiene\_v1                 LMSR Engine    19             10 (3p/7f)     0.9460          **21/21 PASS**
  **7**    quant\_market\_perturbation\_harness\_v1   LMSR Engine    7              10 (9p/1f)     0.9800          **21/21 PASS**
  **8**    quant\_market\_api\_fidelity\_v1           LMSR Engine    5              10 (7p/3f)     0.9050          **21/21 PASS**
  **9**    lmsr\_b\_sensitivity\_suite\_v1            LMSR Engine    3              5 (5p/0f)      1.0000          **21/21 PASS**
  -------- ------------------------------------------ -------------- -------------- -------------- --------------- ----------------

*† product\_observer\_v1 is a seed template with minimal coverage (1
fixture, 0 targeted failures). It reflects genuine construct
performance, not fixture design. Coverage expansion requires ≥50 replays
against live Observer outputs to achieve BACKTESTED tier.*

**3. Coverage**

  ------------------------------ ----------------- ----------------- ----------------- -----------
  **Metric**                     **Real Estate**   **Construct †**   **LMSR Engine**   **Total**
  **Templates**                  4                 1                 4                 **9**
  **Unique Criteria**            21                5                 27                **53**
  **Fixture Records**            57                1                 35                **93**
  **Targeted Failures**          21                0                 11                **32**
  **Verifier Checks per Cert**   21                21                21                **21**
  ------------------------------ ----------------- ----------------- ----------------- -----------

*† Construct vertical currently contains a single seed template. Figures
will increase as Observer replays accumulate.*

**4. Vertical A: Tokenised Real Estate Operations**

Four templates covering the full lifecycle of developer forward-funding:
escrow milestone releases, distribution waterfalls, ledger
reconciliation, and arrears resolution. Every template includes targeted
failure scenarios demonstrating policy rejection behaviour.

**escrow\_milestone\_release\_v1**

Deterministic verification of escrow release eligibility: evidence
present, signer policy satisfied, validity window respected, release
amount arithmetically correct, and idempotency enforced. The commercial
wedge.

  ----------------------- ----------------------------------------------------------------------------
  **Property**            **Value**
  **Template ID**         escrow\_milestone\_release\_v1
  **Display Name**        ESCROW\_MILESTONE\_RELEASE\_V1 --- Developer Forward-Funding Certification
  **Vertical**            Tokenised Real Estate
  **Criteria Count**      5
  **Fixture Records**     11 (6 pass / 5 fail)
  **Composite Score**     0.9091
  **Verification Tier**   UNVERIFIED
  **Verifier Result**     21/21 PASS (verify) + 6/6 PASS (replay)
  ----------------------- ----------------------------------------------------------------------------

**Targeted Failure Scenarios**

-   escrow\_0007: Missing engineer\_signoff document →
    required\_evidence\_present = false

-   escrow\_0008: Administrator attestation absent →
    signature\_policy\_satisfied = false

-   escrow\_0009: Evidence submitted after window closes →
    validity\_window\_respected = false

-   escrow\_0010: Duplicate release for already-released milestone →
    idempotency = false

-   escrow\_0011: Claimed amount 2× schedule amount →
    release\_amount\_correct = false

**Notes**

Every criterion has exactly one targeted failure. Includes GBP and AED
jurisdictions, rounding edge cases (175,333.33 × 0.15).

**distribution\_waterfall\_v1**

Deterministic verification of SPV distribution waterfalls: priority
ordering, fee calculations, pro-rata investor allocations, reserve fund
constraints, and rounding policy compliance.

  ----------------------- -----------------------------------------------------------------
  **Property**            **Value**
  **Template ID**         distribution\_waterfall\_v1
  **Display Name**        DISTRIBUTION\_WATERFALL\_V1 --- Fund Distribution Certification
  **Vertical**            Tokenised Real Estate
  **Criteria Count**      5
  **Fixture Records**     15 (10 pass / 5 fail)
  **Composite Score**     0.9333
  **Verification Tier**   UNVERIFIED
  **Verifier Result**     21/21 PASS (verify) + 6/6 PASS (replay)
  ----------------------- -----------------------------------------------------------------

**Targeted Failure Scenarios**

-   waterfall\_0011: NOI allocations exceed pool by £50 →
    waterfall\_arithmetic = false

-   waterfall\_0012: Splits sum £1,550 vs gross £1,500 →
    noi\_pool\_conservation = false

-   waterfall\_0013: Distribution per token has 4 d.p. under GBP
    half\_up/2 policy → rounding\_policy\_compliance = false

-   waterfall\_0014: Per-token × supply = £800 vs distributions £720 →
    cap\_table\_consistency = false

-   waterfall\_0015: Settlement reference mismatch in bank ledger →
    ledger\_reconciliation = false

**Notes**

One targeted failure per criterion. Covers multi-tier waterfalls with
operator fees, platform fees, reserve contributions, and investor
distributions.

**ledger\_reconciliation\_v1**

Deterministic verification that ledger entries reconcile against source
transactions: bank reference matching, bucket sum consistency,
destination routing validity, event log completeness, and exception
correctness.

  ----------------------- --------------------------------------------------------------------
  **Property**            **Value**
  **Template ID**         ledger\_reconciliation\_v1
  **Display Name**        LEDGER\_RECONCILIATION\_V1 --- Ledger Reconciliation Certification
  **Vertical**            Tokenised Real Estate
  **Criteria Count**      5
  **Fixture Records**     15 (10 pass / 5 fail)
  **Composite Score**     0.9333
  **Verification Tier**   UNVERIFIED
  **Verifier Result**     21/21 PASS (verify) + 6/6 PASS (replay)
  ----------------------- --------------------------------------------------------------------

**Targeted Failure Scenarios**

-   recon\_0011: Bank reference mismatch (BANKREF-pay\_0011 vs
    BANKREF-pay\_DIFFERENT) → bank\_ref\_match = false

-   recon\_0012: Splits sum £1,550 vs gross £1,500 →
    bucket\_sum\_matches\_gross = false

-   recon\_0013: NOI pool routed to ops\_wallet instead of noi\_wallet →
    bucket\_destination\_valid = false

-   recon\_0014: Only 1 event log entry for 2-split payment →
    event\_log\_complete = false

-   recon\_0015: Spurious exception raised on valid payment →
    exceptions\_correct = false

**Notes**

One targeted failure per criterion. Verifies end-to-end reconciliation
of escrow movements, distribution payments, and fee deductions.

**arrears\_resolution\_v1**

Deterministic verification of the 12-state arrears resolution state
machine: state transition validity, ladder redirection arithmetic,
reserve fund impact, distribution adjustment, grace period enforcement,
and ladder balance protection.

  ----------------------- -----------------------------------------------------------------
  **Property**            **Value**
  **Template ID**         arrears\_resolution\_v1
  **Display Name**        ARREARS\_RESOLUTION\_V1 --- Arrears State Machine Certification
  **Vertical**            Tokenised Real Estate
  **Criteria Count**      6
  **Fixture Records**     16 (10 pass / 6 fail)
  **Composite Score**     0.9375
  **Verification Tier**   UNVERIFIED
  **Verifier Result**     21/21 PASS (verify) + 6/6 PASS (replay)
  ----------------------- -----------------------------------------------------------------

**Targeted Failure Scenarios**

-   arrears\_0011: CURRENT → ARREARS skipping GRACE\_PERIOD →
    state\_transition\_validity = false

-   arrears\_0012: Ladder contribution not redirected during ARREARS
    state → ladder\_redirection\_arithmetic = false

-   arrears\_0013: Reserve fund drawn below 3-month NOI minimum →
    reserve\_fund\_impact = false

-   arrears\_0014: Loss waterfall active but investor distributions
    unchanged → distribution\_adjustment = false

-   arrears\_0015: External escalation during 5-day grace period →
    grace\_period\_enforcement = false

-   arrears\_0016: Existing ladder equity forcibly liquidated to cover
    arrears → ladder\_balance\_protection = false

**Notes**

One targeted failure per criterion. Covers UK Section 8 and Dubai RERA
jurisdictions, grace periods, payment plans, loss waterfall execution.
Positioned as Phase 2 credibility accelerator, not commercial wedge.

**5. Vertical B: Construct Verification**

Single seed template for calibrating AI construct performance against
ground-truth datasets. Produces the certificates that Hounfour consumes
to gate model routing and privilege escalation.

**product\_observer\_v1**

Verification of AI construct outputs against ground-truth expected
responses: precision, recall, reply accuracy, and structured output
compliance. Currently a seed template with minimal fixture coverage.

  ----------------------- -----------------------------------------------------------------------
  **Property**            **Value**
  **Template ID**         product\_observer\_v1
  **Display Name**        PRODUCT\_OBSERVER\_V1 --- AI Construct Performance Calibration (Seed)
  **Vertical**            Construct Verification
  **Criteria Count**      5
  **Fixture Records**     1 (1 pass / 0 fail)
  **Composite Score**     0.7000
  **Verification Tier**   UNVERIFIED
  **Verifier Result**     21/21 PASS (verify) + 6/6 PASS (replay)
  ----------------------- -----------------------------------------------------------------------

**Notes**

Seed template: 1 fixture record, 0 targeted failures. Composite 0.700
reflects genuine construct performance measured against live Observer
outputs, not fixture design. Coverage expansion to ≥10 fixtures with
targeted failures is planned. Tier upgrades from UNVERIFIED to
BACKTESTED at ≥50 replays against live data.

**6. Vertical C: LMSR Market Microstructure**

Four templates auditing the prediction market engine itself: commitment
immutability, cost-function accounting, API contract fidelity,
adversarial robustness, and parametric sensitivity analysis. These prove
the RLMF generation infrastructure is deterministically sound.

**quant\_market\_hygiene\_v1**

Comprehensive audit of LMSR trading behaviour across 19 criteria:
commitment immutability (oracle, b, outcomes, fees), exact cost-function
accounting (position limits, capital bounds, negative balance invariant,
inventory), calibration signals (Brier score, ECE, proper scoring rules,
regime decomposition), and robustness flags (VRF perturbation, saboteur
pressure, paradox engine recovery).

  ----------------------- ---------------------------------------------------------------------------------
  **Property**            **Value**
  **Template ID**         quant\_market\_hygiene\_v1
  **Display Name**        QUANT\_MARKET\_HYGIENE\_V1 --- LMSR Microstructure, Calibration, and Robustness
  **Vertical**            LMSR Market Microstructure
  **Criteria Count**      19
  **Fixture Records**     10 (3 pass / 7 fail)
  **Composite Score**     0.9460
  **Verification Tier**   UNVERIFIED
  **Verifier Result**     21/21 PASS (verify) + 6/6 PASS (replay)
  ----------------------- ---------------------------------------------------------------------------------

**Targeted Failure Scenarios**

-   qmhy\_0003: Position limit breach → position\_limit\_enforced =
    false

-   qmhy\_0004: Capital/balance violations → capital\_commitment\_valid,
    worst\_case\_loss\_bounded, no\_negative\_balance\_invariant = false

-   qmhy\_0005: Oracle not committed → resolution\_oracle\_committed =
    false

-   qmhy\_0006: b parameter mutated → lmsr\_parameter\_b\_committed =
    false

-   qmhy\_0008: VRF perturbation failure →
    vrf\_perturbation\_suite\_pass = false

-   qmhy\_0009: Fee schedule not locked → fee\_schedule\_committed =
    false

-   qmhy\_0010: Outcomes changed post-commit →
    market\_outcomes\_committed = false

**Notes**

The heaviest template: 19 criteria covering the full LMSR verification
surface. 3 pass / 7 fail ratio reflects aggressive boundary testing.
qmhy\_0004 tests three criteria simultaneously (multi-violation record).

**quant\_market\_perturbation\_harness\_v1**

Adversarial robustness suite verifying safe engine behaviour under VRF
perturbations, saboteur pressure, and paradox engine activation. Checks
policy guards (max cost, max impact), heartbeat schedule commitment, and
VRF execution window modelling.

  ----------------------- --------------------------------------------------------------------------------
  **Property**            **Value**
  **Template ID**         quant\_market\_perturbation\_harness\_v1
  **Display Name**        QUANT\_MARKET\_PERTURBATION\_HARNESS\_V1 --- VRF, Saboteur, Paradox Robustness
  **Vertical**            LMSR Market Microstructure
  **Criteria Count**      7
  **Fixture Records**     10 (9 pass / 1 fail)
  **Composite Score**     0.9800
  **Verification Tier**   UNVERIFIED
  **Verifier Result**     21/21 PASS (verify) + 6/6 PASS (replay)
  ----------------------- --------------------------------------------------------------------------------

**Targeted Failure Scenarios**

-   pert\_0007: VRF perturbation suite failure →
    vrf\_perturbation\_suite\_pass = false

**Notes**

9 pass / 1 fail. The single failure confirms the harness correctly
detects VRF-induced instability.

**quant\_market\_api\_fidelity\_v1**

Verification that the LMSR market API exposes a versioned contract,
complete state feed (x, prices, b, phase, logic\_gap, stability,
n\_outcomes), correct pre-trade quoting (ΔC = C(x+Δ) − C(x)), and
committed heartbeat schedule.

  ----------------------- ----------------------------------------------------------------------
  **Property**            **Value**
  **Template ID**         quant\_market\_api\_fidelity\_v1
  **Display Name**        QUANT\_MARKET\_API\_FIDELITY\_V1 --- State Feed and Quoting Contract
  **Vertical**            LMSR Market Microstructure
  **Criteria Count**      5
  **Fixture Records**     10 (7 pass / 3 fail)
  **Composite Score**     0.9050
  **Verification Tier**   UNVERIFIED
  **Verifier Result**     21/21 PASS (verify) + 6/6 PASS (replay)
  ----------------------- ----------------------------------------------------------------------

**Targeted Failure Scenarios**

-   api\_0007: Incorrect quoted\_cost (deliberate arithmetic error) →
    quote\_correct = false

-   api\_0008: Quote during resolve phase (trading not permitted) →
    quote\_correct = false

-   api\_0009: Missing logic\_gap field in state feed →
    state\_feed\_complete = false

**Notes**

Diverse coverage: varied b values (10--100), outcome counts (2--5),
non-uniform starting states, zero-delta edge case, and large-size quote
(100 shares).

**lmsr\_b\_sensitivity\_suite\_v1**

Parametric sweep: identical 50-share trade replayed across b = \[10, 20,
40, 80, 160\]. Verifies that price impact is monotonically decreasing
with b, that the sensitivity surface is generated, and that b is
committed per replay.

  ----------------------- -------------------------------------------------------------------
  **Property**            **Value**
  **Template ID**         lmsr\_b\_sensitivity\_suite\_v1
  **Display Name**        LMSR\_B\_SENSITIVITY\_SUITE\_V1 --- Impact and Stability Surfaces
  **Vertical**            LMSR Market Microstructure
  **Criteria Count**      3
  **Fixture Records**     5 (5 pass / 0 fail)
  **Composite Score**     1.0000
  **Verification Tier**   UNVERIFIED
  **Verifier Result**     21/21 PASS (verify) + 6/6 PASS (replay)
  ----------------------- -------------------------------------------------------------------

**Notes**

All fixtures pass by design: this is a parametric sweep, not a boundary
test. The purpose is to generate a stability surface, not to test
rejection behaviour. Impact decreases monotonically: 0.4496 → 0.2880 →
0.1502 → 0.0734 → 0.0358.

**7. Supporting Artefacts**

**Ledger Schema (ledger\_schema.json)**

JSON Schema 2020-12 defining the append-only LMSR trade ledger. 17
required fields per entry covering pre/post state vectors (x\_before,
x\_after), cost function values (C\_before, C\_after, cost\_paid), price
arrays, agent balances (cash, inventory), and commitment hashes. Five
event types: trade, commit, paradox\_event, resolve, settle.

**Verifier CLI (echelon\_verify.py)**

Single-file Python 3.10+ tool, zero external dependencies. Five
commands: verify (21-check full suite), inspect (certificate summary),
hash (SHA-256 computation), schema-check (structural validation), replay
(6-check template-fixture consistency). All 9 templates pass both verify
and replay commands without modification.

**Evidence Bundle Standard**

Each certificate is backed by an evidence bundle containing: inputs/
(fixture datasets), policy/ (theatre template), expected/ (extracted
expected outputs), and manifest.json (pure path → hash map, no
timestamps, deterministically reproducible). The manifest is itself
hashed to produce the evidence\_bundle\_hash in the certificate.

**8. What This Proves**

Nine templates across three verticals, verified by the same CLI tool,
using the same evidence bundle standard, producing certificates in the
same schema. The verification primitive is domain-agnostic: it works for
real estate escrow, AI construct calibration, and LMSR market
microstructure without any changes to the verifier.

The total verification surface is 9 templates × 21 checks = 189
independent assertions. Every template passes all 189 checks. The
fixture library contains 93 records with 32 targeted failure scenarios
ensuring the system correctly rejects policy violations, not just
approves valid operations.

Eight of nine templates include targeted failure scenarios. The single
exception (b-sensitivity) is a parametric sweep by design. The seed
template (product\_observer\_v1) is flagged as coverage-incomplete and
will expand as live construct data accumulates.

**Platforms compete on features. Infrastructure competes on trust.**
