# Echelon T0 Genome Specification

**Version:** 1.0.0
**Date:** 4 March 2026
**Status:** Normative
**Predecessor:** echelon_archetype_matrix.md (v1.0, January 2026)

## Purpose

A T0 genome is the committed, deterministic context for an agent identity. It is injected at zero inference cost into T1/T2/T3 tiers at Theatre entry. The genome is hashed into the Theatre's commitment hash before any capital enters. Modifying a genome after commitment is a Paradox violation.

This document defines the YAML frontmatter schema that every archetype genome must conform to. Loa validates genomes using the same registry-fixture contract pattern established in the OSINT pipeline (Cycle-005).

## Schema Version

All genomes declare `schema_version: "1.0.0"`. Validators reject genomes with unknown schema versions.

## Required Sections

Every genome YAML contains exactly seven top-level sections. Missing or extra top-level keys are validation failures.

### 1. identity

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | yes | Human-readable agent name (e.g. "MEGALODON") |
| `archetype` | enum | yes | One of: SHARK, SPY, DIPLOMAT, SABOTEUR, WHALE, DEGEN |
| `variant` | string | yes | Variant identifier (e.g. "MEGALODON", "THRESHER") |
| `agent_id` | string | yes | ERC-8004 compatible ID: `{archetype}_{variant}_v{version}` |
| `version` | semver | yes | Genome version, pinned to schema_version major |
| `lineage` | enum | yes | One of: GENESIS, USER_CREATED, BRED |
| `description` | string | yes | One-line role summary, no marketing language |

### 2. economic_parameters

All values are committed at Theatre entry. Ranges are hard constraints; values outside ranges are validation failures.

| Field | Symbol | Type | Range | Description |
|-------|--------|------|-------|-------------|
| `risk_appetite` | rho | float | 0.0-1.0 | Willingness to accept uncertainty |
| `evidence_sensitivity` | epsilon | float | 0.0-1.0 | Speed of belief updating on new evidence |
| `time_preference` | gamma | float | 0.0-1.0 | Discount factor for future rewards |
| `exploration_rate` | xi | float | 0.0-1.0 | Tendency to try novel actions vs exploit known |
| `position_limit` | L | integer | 1-100000 | Maximum position size in settlement units |
| `sabotage_propensity` | sigma | float | 0.0-1.0 | Likelihood to execute adversarial actions |
| `shield_propensity` | phi | float | 0.0-1.0 | Likelihood to execute defensive actions |
| `patience` | pi | integer | 1-600 | Seconds before first action after Theatre entry |

### 3. tier_profile

Defines which intelligence tiers are active and under what conditions.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `active_tiers` | list[enum] | yes | Subset of [T0, T1, T2, T3] this archetype uses |
| `default_tier` | enum | yes | Tier used for routine decisions |
| `escalation_rules` | list[object] | yes | Conditions that trigger tier escalation |
| `cost_profile` | string | yes | Human-readable cost description |
| `max_inference_budget_per_market` | float | yes | Maximum spend in USD per market participation |

Each `escalation_rule` object:

| Field | Type | Description |
|-------|------|-------------|
| `condition` | string | Trigger condition (e.g. "logic_gap > 0.20") |
| `escalate_to` | enum | Target tier |
| `cooldown_seconds` | integer | Minimum seconds between escalations |

### 4. decision_policy

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `method` | enum | yes | One of: SOFTMAX_Q_VALUE, EPSILON_GREEDY, THOMPSON_SAMPLING |
| `temperature` | float | yes | Softmax temperature (higher = more random) |
| `bias_vector` | object | yes | Archetype-specific action preferences |
| `strategy_rules` | list[string] | yes | Ordered list of decision heuristics |

The `bias_vector` maps action types to float biases:

| Action | Description |
|--------|-------------|
| `buy` | Preference for taking long positions |
| `sell` | Preference for taking short positions |
| `hold` | Preference for maintaining current position |
| `observe` | Preference for gathering information before acting |
| `sabotage` | Preference for adversarial actions |
| `shield` | Preference for defensive/stabilising actions |

### 5. paradox_behaviour

Defines how the agent responds to Paradox Engine events.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `logic_gap_threshold` | float | yes | Logic Gap percentage that triggers response |
| `response_action` | enum | yes | Primary response: EXTRACT, DEFEND, ATTACK, OBSERVE, HEDGE |
| `extraction_cost_ceiling` | float | yes | Maximum fraction of position value agent will pay to extract |
| `coalition_willingness` | float | yes | 0.0-1.0 probability of joining defensive coalition |
| `circuit_breaker_behaviour` | enum | yes | Action when circuit breaker fires: HALT, REDUCE, IGNORE |

### 6. inquiry_class_affinity

Maps the five bounded inquiry classes to effectiveness scores. Used by the Theatre template engine to weight archetype selection.

| Field | Type | Range | Description |
|-------|------|-------|-------------|
| `counterfactual` | float | 0.0-1.0 | Effectiveness in hypothetical scenario markets |
| `investigative` | float | 0.0-1.0 | Effectiveness in open-ended evidence accumulation |
| `inspection` | float | 0.0-1.0 | Effectiveness in point-in-time verification |
| `survey` | float | 0.0-1.0 | Effectiveness in aggregated opinion markets |
| `scrutiny` | float | 0.0-1.0 | Effectiveness in adversarial stress tests |

### 7. success_metrics

Quantitative targets used for RLMF calibration and routing hint generation.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `brier_score_target` | float | yes | Target Brier score (lower is better; 0.0 = perfect) |
| `ece_bound` | float | yes | Maximum expected calibration error |
| `pnl_expectation` | enum | yes | One of: PROFITABLE, BREAKEVEN, LOSS_ACCEPTABLE |
| `consistency_threshold` | float | yes | Minimum behavioural consistency across episodes (0.0-1.0) |
| `position_size_variance_max` | float | yes | Maximum acceptable variance in position sizing |
| `fork_choice_consistency_min` | float | yes | Minimum consistency in outcome selection |

## Commitment Hash Composition

When a genome is committed to a Theatre, the following fields are included in the commitment hash (SHA-256):

1. `identity.agent_id`
2. `identity.version`
3. `economic_parameters` (all eight fields, serialised in schema order)
4. `tier_profile.active_tiers` (sorted alphabetically)
5. `decision_policy.method`
6. `decision_policy.temperature`
7. `paradox_behaviour.logic_gap_threshold`
8. `paradox_behaviour.response_action`

Fields not in this list (description, strategy_rules, inquiry_class_affinity, success_metrics) are informational and may be updated between markets without breaking commitment integrity.

## Variant Rules

Each core archetype has exactly two genesis variants. Variants share the archetype's decision_policy.method and paradox_behaviour.response_action but may differ in all economic_parameters within the archetype's constrained ranges.

User-created agents must declare `lineage: USER_CREATED` and have parameter values within the archetype's published ranges. Bred agents declare `lineage: BRED` and carry a `parent_ids` field (not yet in schema v1.0.0; reserved for v1.1.0).

## Validation Contract

The validator (`validate_genome.py`) enforces:

1. All required fields present
2. All enum values from permitted sets
3. All numeric values within declared ranges
4. `agent_id` matches pattern `{archetype}_{variant}_v{version}`
5. `active_tiers` is a non-empty subset of [T0, T1, T2, T3]
6. `default_tier` is a member of `active_tiers`
7. Inquiry class affinities sum to at least 1.0 (agent must be useful somewhere)
8. At least one escalation rule defined
9. Bias vector contains all six action keys
10. Schema version is "1.0.0"

Validation failures are hard errors. Loa will not ingest a genome that fails validation.
