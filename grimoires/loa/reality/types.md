# Types & Data Models — Echelon

> **Generated**: 2026-02-18

## Backend Enums (Python)

### `backend/core/models.py`

| Enum | Values | Line |
|------|--------|------|
| `AgentRole` | SPY, DIPLOMAT, TRADER, SABOTEUR, JOURNALIST, PROPAGANDIST, SLEEPER | 36-44 |
| `MissionType` | INTELLIGENCE, ASSASSINATION, EXTRACTION, SABOTAGE, DIPLOMACY, PROPAGANDA, MARKET_OP, PROTECTION, INVESTIGATION, COUP | 47-58 |
| `MissionStatus` | PENDING, ACTIVE, COMPLETED, FAILED, EXPIRED, ABORTED | 61-68 |
| `Difficulty` | ROUTINE(1), STANDARD(2), CHALLENGING(3), CRITICAL(4), IMPOSSIBLE(5) | 71-77 |
| `Faction` | EASTERN_BLOC, WESTERN_ALLIANCE, NON_ALIGNED, CORPORATE, UNDERGROUND, NEUTRAL | 80-87 |
| `SpecialAbility` | 30+ abilities across roles (ENCRYPT_INTEL, EARLY_ACCESS, PROPOSE_TREATY, FRONT_RUN, FALSE_FLAG, INVESTIGATE, SPIN, etc.) | 94-136 |
| `TraderArchetype` | SHARK, WHALE, DEGEN, NOVICE, ARBITRAGEUR, MARKET_MAKER | 786-797 |

### `backend/agents/schemas.py`

| Enum | Values | Line |
|------|--------|------|
| `AgentDomain` | FINANCIAL, ATHLETIC, POLITICAL | 34-37 |
| `FinancialArchetype` | WHALE, SHARK, DEGEN, VALUE, MOMENTUM, NOISE | 41-48 |
| `AthleticArchetype` | STAR, GLASS_CANNON, WORKHORSE, PROSPECT, VETERAN | 51-57 |
| `PoliticalArchetype` | POPULIST, TECHNOCRAT, INSTIGATOR, MODERATE, IDEOLOGUE | 60-66 |
| `AgentStatus` | ACTIVE, INJURED, SUSPENDED, BANKRUPT, ELIMINATED, RETIRED | 69-76 |

### `backend/agents/brain.py`

| Enum | Values | Line |
|------|--------|------|
| `BrainProvider` | RULE_BASED, LOCAL_LLM, GROQ, ANTHROPIC, HYBRID | 45-50 |

---

## Backend Dataclasses (Python)

### `backend/core/models.py`

| Class | Key Fields | Line |
|-------|-----------|------|
| `MissionObjective` | id, description, target, success_condition, reward_usdc, is_completed | 228-240 |
| `Mission` | id, codename, title, briefing, mission_type, difficulty, status, objectives, betting_market_id, narrative_arc_id | 243-331 |
| `NarrativeArc` | id, title, synopsis, chapters, global_tension_impact, protagonist_faction | 334-370 |
| `TheaterState` | active_missions, active_narratives, global_tension, chaos_index, faction_power | 372-403 |
| `TulipStrategyConfig` | max_liquidity, max_hours_to_expiry, min_edge, kelly_fraction | 799-827 |
| `AgentGenome` | agent_id, archetype, strategy weights, risk params, behavioral traits | 829-952 |

### `backend/core/cpmm.py`

| Class | Key Fields | Line |
|-------|-----------|------|
| `CPMMState` | yes_shares, no_shares, constant_product, total_liquidity | 28-50 |

---

## Backend Pydantic Models

### `backend/agents/schemas.py`

| Model | Extends | Key Fields | Line |
|-------|---------|-----------|------|
| `BaseAgent` | BaseModel | id, name, domain, bankroll, influence, resilience, aggression, deception, loyalty, adaptability, status, memory, allies, rivals, fitness_score | 83-176 |
| `FinancialAgent` | BaseAgent | archetype, risk_tolerance, panic_threshold, time_horizon, positions, avg_entry_prices, has_ml_model, insider_access | 183-324 |
| `AthleticAgent` | BaseAgent | archetype, skill, pace, stamina, strength, form, morale, match_fitness, injury_proneness, team_id, position, goals, assists | 331-459 |
| `PoliticalAgent` | BaseAgent | archetype, charisma, policy_depth, public_favor, scandal_vulnerability, has_skeleton, campaign_funds | 539-618 |

### `backend/agents/brain.py`

| Model | Key Fields | Line |
|-------|-----------|------|
| `BrainConfig` | provider, anthropic_api_key, groq_api_key, ollama_url, llm_probability | 52-67 |
| `Decision` | action, confidence, reasoning, provider_used, latency_ms | 69-74 |

---

## Backend Database Models (SQLAlchemy 2.0)

### `backend/database/models.py`

| Enum | Values | Line |
|------|--------|------|
| `AgentArchetype` | SHARK, SPY, DIPLOMAT, SABOTEUR, WHALE, DEGEN | 25-31 |
| `WingFlapType` | TRADE, SHIELD, SABOTAGE, RIPPLE, PARADOX, FOUNDER_YIELD, ENTROPY | 33-40 |
| `ParadoxStatus` | ACTIVE, EXTRACTING, DETONATED, RESOLVED | 42-46 |
| `SeverityClass` | CLASS_1_CRITICAL, CLASS_2_SEVERE, CLASS_3_MODERATE, CLASS_4_MINOR | 48-52 |

| Model | Table | Key Columns | Line |
|-------|-------|------------|------|
| `User` | users | id, username, email, password_hash, tier, balance_usdc, balance_echelon, wallet_address | 58-76 |
| `Timeline` | timelines | id, name, stability, price_yes, price_no, osint_alignment, logic_gap, gravity_score, founder_id, decay_rate_per_hour | 80+ |
| `Agent` | agents | id, name, archetype, tier, level, sanity, is_alive, owner_id, wallet_address, total_pnl_usd, win_rate | 100+ |
| `WingFlap` | wing_flaps | id, timestamp, timeline_id, agent_id, flap_type, action, stability_delta, volume_usd | 130+ |
| `Paradox` | paradoxes | id, timeline_id, status, severity_class, logic_gap, spawned_at, detonation_time, decay_multiplier | 160+ |
| `UserPosition` | user_positions | id, user_id, timeline_id, side, shards_held, average_entry_price, is_founder | 190+ |
| `WatchlistItem` | watchlist_items | id, user_id, item_type(AGENT/TIMELINE), item_id | 220+ |
| `PrivateFork` | private_forks | id, user_id, name, base_timeline_id, status, stability | 240+ |

---

## Frontend Types (TypeScript)

### `frontend/src/types/index.ts` (Core Domain Types)

| Type | Key Fields | Line |
|------|-----------|------|
| `AgentArchetype` | 'SHARK' / 'SPY' / 'DIPLOMAT' / 'SABOTEUR' / 'WHALE' / 'DEGEN' | 5 |
| `WingFlapType` | 'TRADE' / 'SHIELD' / 'SABOTAGE' / 'RIPPLE' / 'PARADOX' / 'FOUNDER_YIELD' | 6 |
| `StabilityDirection` | 'ANCHOR' / 'DESTABILISE' | 7 |
| `ParadoxStatus` | 'ACTIVE' / 'EXTRACTING' / 'DETONATED' / 'RESOLVED' | 8 |
| `SeverityClass` | 'CLASS_1_CRITICAL' / 'CLASS_2_SEVERE' / 'CLASS_3_MODERATE' / 'CLASS_4_MINOR' | 9 |
| `WingFlap` (interface) | id, timestamp, timeline_id, agent_id, agent_archetype, flap_type, action, stability_delta, direction, volume_usd, spawned_ripple | 15-34 |
| `Timeline` (interface) | id, name, stability, surface_tension, price_yes, price_no, osint_alignment, logic_gap, gravity_score, total_volume_usd, liquidity_depth_usd, active_agent_count, founder_yield_rate, decay_rate_per_hour, has_active_paradox | 46-72 |
| `Paradox` (interface) | id, timeline_id, status, severity_class, logic_gap, detonation_time, decay_multiplier, extraction_cost_usdc, carrier_agent_id, carrier_sanity_cost | 83-100 |

### `frontend/src/demo/demoStore.ts`

| Type | Key Fields | Line |
|------|-----------|------|
| `DemoOutcomeSnapshot` | price, prevPrice, stability, volume, updatedAt | 17-23 |
| `DemoPosition` | id, marketId, marketTitle, outcomeId("YES"/"NO"), stake, entryPrice, shares | 25-34 |
| `DemoAgentEvent` | id, ts, text | 36-40 |
| `DemoLaunchFeedItem` | id, ts, kind("launch"/"milestone"/"warning"), actor, message, accent, cta?, meta? | 44-53 |
| `DemoBreach` | id, type("PARADOX"/"STABILITY"/"ORACLE"/"SENSOR"), timeline, severity, logicGap, stability, carrier, sanity, status | 55-66 |
| `DemoBreachHistoryRow` | id, time, type, timeline, severity, resolution, impact | 68-76 |
| `DemoExportJob` | id, partner, status, theatre, episodes, samplingRate, format, sizeGb, progress, etaSec | 78-89 |
| `DemoExportPartner` | name, access("Premium"/"Standard"), exports30d, dataVolumeGb, status | 91-97 |
| `DemoExportConfig` | samplingRate, format, compression("GZIP"/"None") | 99-103 |
| `StoreState` | outcomes, positions, agentFeed, toasts, launchFeed, breachesActive, breachesHistory, exportsActive, exportPartners, exportConfig | 105-117 |

---

## JSON Schemas

### `docs/schemas/echelon_theatre_schema.json`

| Field | Type | Required |
|-------|------|----------|
| schema_version | string (semver) | Yes |
| theatre_id | string (pattern: `^[a-z_]+_v\d+$`) | Yes |
| template_family | enum: 2D-DISCRETE, 2D-CONTINUOUS, 3D-STATIC, 3D-INERT, 3D-DYNAMIC, PHYSICS-SIM, SOCIAL-ENGINEERING, ECONOMIC-SIM, HYBRID | Yes |
| display_name | string (1-100 chars) | Yes |
| training_primitives | string[] (spatial_reasoning, temporal_reasoning, causal_inference, etc.) | Yes |
| difficulty_tiers | array of {tier_id, label, difficulty_multiplier, parameter_overrides} | Yes |
| fork_definitions | array of {fork_id, trigger_condition, options, deadline_ms, state_transitions} | Yes |
| scoring | object (multi-dimensional score vector) | Yes |

### `docs/schemas/echelon_rlmf_schema.json`

| Field | Type | Required |
|-------|------|----------|
| episode_id | UUID | Yes |
| theatre_id | string | Yes |
| seed_hash | hex string (0x + 64 chars) | Yes |
| timestep | integer | Yes |
| state_features | {pose, objects, constraints} | Yes |
| market | object | Yes |
| action_taken | object | Yes |
| settlement | object | Yes |
| calibration | object | Yes |

---

## Smart Contract Interfaces (Solidity)

### `smart-contracts/contracts/`

| Contract | Purpose | Key Functions |
|----------|---------|---------------|
| `PredictionMarket.sol` | Core LMSR market | createMarket, buy, sell, resolve |
| `TimelineShard.sol` | Fork mechanics | createFork, commitToFork |
| `SabotagePool.sol` | Risk/sabotage system | stake, attack, defend |
| `HotPotatoEvents.sol` | Dynamic payout | createEvent, pass, settle |
| `EchelonVRFConsumer.sol` | Chainlink VRF | requestRandomWords, fulfillRandomWords |
