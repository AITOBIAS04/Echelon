# API Surface — Echelon

> **Generated**: 2026-02-18

## Frontend Routes

**Source**: `frontend/src/router.tsx`

| Route | Component | Error Boundary | Notes |
|-------|-----------|---------------|-------|
| `/` | → `/marketplace` (redirect) | RouteErrorBoundary | Default route |
| `/marketplace` | MarketplacePage | ErrorBoundary | Main market listing |
| `/analytics` | BlackboxPage | ErrorBoundary | Market analytics |
| `/portfolio` | PortfolioPage | ErrorBoundary | User positions |
| `/rlmf` | RLMFPage | ErrorBoundary | RLMF forecasting |
| `/vrf` | VRFPage | ErrorBoundary | VRF lottery |
| `/agents` | AgentRoster | ErrorBoundary | Agent roster |
| `/agents/breach` | BreachConsolePage | ErrorBoundary | Breach monitoring |
| `/agents/export` | ExportConsolePage | ErrorBoundary | Export management |
| `/agent/:agentId` | AgentDetail | ErrorBoundary | Individual agent |
| `/timeline/:timelineId` | TimelineDetailPage | ErrorBoundary | Timeline view |
| `/launchpad` | LaunchpadPage | — | Market launch + live feed |
| `/launchpad/:id` | LaunchpadDetailPage | — | Timeline detail |
| `/launchpad/new` | LaunchpadNewPage | — | 3-step creation wizard |
| `/fieldkit` | → `/portfolio` (redirect) | — | Legacy redirect |
| `/blackbox` | → `/analytics` (redirect) | — | Legacy redirect |

## Frontend Demo Store API

**Source**: `frontend/src/demo/demoStore.ts:154-346`

| Method | Signature | Purpose |
|--------|-----------|---------|
| `ensureOutcome` | `(marketId, outcomeId, initial)` | Initialize outcome price |
| `updateOutcome` | `(marketId, outcomeId, updater)` | Mutate outcome state |
| `readOutcome` | `(marketId, outcomeId) → DemoOutcomeSnapshot` | Read current price |
| `subscribeOutcome` | `(marketId, outcomeId, listener) → unsubscribe` | Price change subscription |
| `getPositions` | `() → DemoPosition[]` | Get user positions |
| `setPositions` | `(next)` | Update positions |
| `subscribePositions` | `(listener) → unsubscribe` | Position change subscription |
| `pushAgentEvent` | `(ev, max=20)` | Add agent activity event |
| `pushToast` | `(title, detail?, ttlMs=3200)` | Show notification |
| `pushLaunchFeed` | `(item, max=20)` | Add launch feed event |
| `setBreaches` | `(active, history)` | Set breach state |
| `updateBreach` | `(id, updater)` | Mutate breach |
| `moveBreachToHistory` | `(id, resolution, impact)` | Resolve breach |
| `setExports` | `(active)` | Set export jobs |
| `setExportConfig` | `(next)` | Update export config |

## Backend API Endpoints

**Source**: `backend/api/`

| File | Endpoint Pattern | Purpose |
|------|-----------------|---------|
| `markets.py` | `/api/markets/*` | Market CRUD, trading |
| `situation_room.py` | `/api/situation-room/*` | Situation room data |
| `situation_room_routes.py` | `/api/situation-room/routes/*` | Situation room navigation |
| `payments/routes.py` | `/api/payments/*` | Coinbase Commerce payments |

## Backend Core Services

**Source**: `backend/core/`

| Module | Purpose | Key Methods |
|--------|---------|-------------|
| `cpmm.py` | CPMM market maker | `get_price(outcome)`, `calculate_trade_cost(shares, outcome)` |
| `models.py` | Domain models | Mission factory templates, agent genomes |
| `osint_registry.py` | OSINT source registry | Register/query OSINT providers |
| `mission_generator.py` | Mission generation | Create missions from OSINT signals |
| `wallet_factory.py` | HD wallet generation | Deterministic wallet derivation |
| `blockchain_manager.py` | Web3 interaction | Contract calls, transaction management |
| `security.py` | Auth/JWT | Token generation, validation |
| `database.py` | DB connection | SQLAlchemy session management |

## Backend Agent Brain API

**Source**: `backend/agents/brain.py:45-74`

| Class | Method | Returns |
|-------|--------|---------|
| `BaseBrainProvider` (ABC) | `decide(context) → Decision` | `{action, confidence, reasoning, provider_used, latency_ms}` |
| `RuleBasedProvider` | `decide(context) → Decision` | Heuristic decision |
| `GroqProvider` | `decide(context) → Decision` | Llama 3 70B decision |
| `AnthropicProvider` | `decide(context) → Decision` | Claude decision |
| `HybridBrain` | `decide(context) → Decision` | Routes to best provider |

## Agent Schema API

**Source**: `backend/agents/schemas.py`

| Class | Key Methods |
|-------|-------------|
| `BaseAgent` | `add_memory(event)`, `adjust_bankroll(amount)`, `to_prompt_context()` |
| `FinancialAgent` | `decide_action(price, name, sentiment, trend)`, `execute_trade(action, name, price, qty)` |
| `AthleticAgent` | `check_injury(intensity)`, `recover_tick()`, `update_form(score)`, `calculate_match_contribution(opp)` |
| `PoliticalAgent` | `calculate_vote_probability(demographics)`, `survive_scandal()`, `leak_scandal(target)` |

## Factory Functions

**Source**: `backend/agents/schemas.py:736-831`

| Function | Signature | Returns |
|----------|-----------|---------|
| `breed_agents` | `(parent_a, parent_b, mutation_rate=0.1)` | Child agent (same type) |
| `create_random_financial_agent` | `(archetype?, bankroll=1000)` | `FinancialAgent` |
| `create_random_athletic_agent` | `(archetype?, position?)` | `AthleticAgent` |
| `create_random_political_agent` | `(archetype?)` | `PoliticalAgent` |
