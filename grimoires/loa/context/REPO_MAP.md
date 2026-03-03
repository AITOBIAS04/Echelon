# Repository Map — Prediction Market Monorepo

```
prediction-market-monorepo/
│
├── backend/                          Python 3.12 · FastAPI · SQLAlchemy
│   ├── main.py                       Application entry point (66 KB)
│   ├── dependencies.py               FastAPI dependency injection
│   ├── entrypoint.py                 Container entrypoint
│   ├── alembic.ini                   Migration configuration
│   │
│   ├── api/                          REST API routes
│   │   ├── admin_routes.py
│   │   ├── agents_routes.py
│   │   ├── auth_routes.py
│   │   ├── brain_router.py
│   │   ├── butler_webhooks.py
│   │   ├── butterfly_routes.py
│   │   ├── markets.py
│   │   ├── operations.py
│   │   ├── osint_routes.py
│   │   ├── paradox_routes.py
│   │   ├── positions_routes.py
│   │   ├── scheduler_api.py
│   │   ├── situation_room_routes.py
│   │   ├── theatre_routes.py
│   │   ├── timeline_api.py
│   │   ├── user_routes.py
│   │   └── verification_routes.py
│   │
│   ├── core/                         Business logic (26 modules, 1.1 MB)
│   │   ├── models.py                 Domain models (34 KB)
│   │   ├── cpmm.py                   Constant-product market maker
│   │   ├── event_orchestrator.py     Event orchestration engine (55 KB)
│   │   ├── situation_room_engine.py  Situation room logic (50 KB)
│   │   ├── signal_detector.py        Signal detection (41 KB)
│   │   ├── rpg_agent_brain.py        Agent brain (25 KB)
│   │   ├── mission_generator.py      Mission generation (33 KB)
│   │   ├── narrative_war.py          Narrative conflict system
│   │   ├── osint_registry.py         OSINT registry (21 KB)
│   │   ├── osint_sources_*.py        OSINT data sources (multiple)
│   │   ├── synthetic_osint.py        Synthetic data generation (28 KB)
│   │   ├── persistence_manager.py    Data persistence (25 KB)
│   │   ├── football_data_client.py   Sports data integration
│   │   ├── security.py               Security utilities
│   │   ├── blockchain_manager.py     Blockchain integration
│   │   └── wallet_factory.py         Wallet creation
│   │
│   ├── database/                     ORM layer
│   │   ├── config.py
│   │   ├── connection.py
│   │   ├── models.py                 SQLAlchemy models (26 KB)
│   │   └── repositories/             Data-access layer
│   │
│   ├── schemas/                      Pydantic request/response schemas
│   │   ├── theatre.py
│   │   ├── verification.py
│   │   ├── butterfly_schemas.py
│   │   ├── paradox_schemas.py
│   │   ├── user_schemas.py
│   │   └── worldmonitor_api_contract.py  World Monitor API contract (Pydantic v2)
│   │
│   ├── agents/                       Agent system (11 modules, 496 KB)
│   │   ├── schemas.py                Agent data schemas (36 KB)
│   │   ├── autonomous_agent.py       Autonomous agent core (30 KB)
│   │   ├── agent_execution.py        Execution engine (24 KB)
│   │   ├── instance_manager.py       Instance management (30 KB)
│   │   ├── agent_skills_bridge.py    Skills integration (26 KB)
│   │   ├── brain.py                  Simple brain
│   │   ├── multi_brain.py            Multi-agent brain (21 KB)
│   │   ├── handler_brain.py          Handler brain variant
│   │   ├── skills_brain.py           Skills-based brain
│   │   ├── shark_strategies.py       Trading strategies (24 KB)
│   │   └── genealogy_manager.py      Agent lineage tracking (35 KB)
│   │
│   ├── skills/                       Modular agent capabilities
│   │   ├── skill_router.py           Skill routing (24 KB)
│   │   ├── skill_loader.py           Dynamic loading (15 KB)
│   │   ├── context_compiler.py       Context compilation (24 KB)
│   │   ├── layer1_rules.py           Rule engine (25 KB)
│   │   ├── provider_registry.py      Provider registry (26 KB)
│   │   ├── core/                     Core skills
│   │   ├── diplomat/                 Diplomatic skills
│   │   ├── shark/                    Trading skills
│   │   ├── saboteur/                 Sabotage skills
│   │   └── spy/                      Intelligence skills
│   │
│   ├── market/                       LMSR Market Engine (Cycle-010a — planned)
│   │   ├── lmsr.py                   Pure LMSR cost function
│   │   ├── state.py                  MarketState dataclass + MarketPhase enum
│   │   ├── lifecycle.py              State machine transitions
│   │   ├── fees.py                   FeeSchedule (zero fees in v1)
│   │   ├── commitment.py             Commitment hash (Echelon Canonical JSON v0)
│   │   ├── trading.py                Trade execution engine
│   │   ├── positions.py              Agent position tracking
│   │   ├── resolution.py             Resolution + settlement
│   │   ├── exceptions.py             Market-specific exceptions
│   │   └── tests/                    Market engine test suite (45+ planned)
│   │
│   ├── simulation/                   Simulation engine
│   │   ├── engine.py                 Main simulation engine
│   │   ├── world_state.py            World state management
│   │   ├── digital_twin_engine.py    Digital twin system
│   │   ├── sim_election_engine.py    Election simulation
│   │   ├── breeding_lab.py           Agent breeding
│   │   └── genome.py                 Agent genome/DNA
│   │
│   ├── timeline/                     Timeline & fork management
│   │   ├── divergence_engine.py      Timeline divergence (37 KB)
│   │   └── fork_manager.py           Fork management (42 KB)
│   │
│   ├── services/                     Service layer
│   │   ├── theatre_bridge.py         Theatre integration (11 KB)
│   │   └── verification_bridge.py    Verification integration (8 KB)
│   │
│   ├── integrations/                 External APIs
│   │   ├── kalshi_client.py          Kalshi prediction market (35 KB)
│   │   ├── polymarket_client.py      Polymarket API
│   │   └── builder_attribution.py    Attribution tracking (20 KB)
│   │
│   ├── auth/                         Authentication & authorisation
│   ├── websockets/                   Real-time communication
│   │   └── realtime_manager.py       WebSocket manager (9 KB)
│   ├── worker/tasks/                 Background tasks
│   ├── mechanics/                    Game mechanics
│   ├── missions/                     Mission system
│   ├── payments/                     Payment processing
│   ├── alembic/versions/             Database migrations
│   ├── mocks/                        Mock data
│   └── tests/                        Backend test suite
│
├── frontend/                         React 19 · TypeScript · Vite · Tailwind
│   ├── package.json                  Dependencies
│   ├── vite.config.ts                Build configuration
│   ├── tailwind.config.js            Styling configuration
│   ├── tsconfig.json                 TypeScript configuration
│   ├── vercel.json                   Deployment configuration
│   ├── index.html                    HTML entry point
│   │
│   └── src/
│       ├── main.tsx                  React entry point
│       ├── App.tsx                   Root component
│       ├── router.tsx                Route configuration
│       │
│       ├── pages/                    Page components
│       │   ├── AgentsPage.tsx        Agent management (47 KB)
│       │   ├── MarketplacePage.tsx   Market interface (41 KB)
│       │   ├── PortfolioPage.tsx     User portfolio (38 KB)
│       │   ├── RLMFPage.tsx          RLMF interface (38 KB)
│       │   ├── VRFPage.tsx           VRF interface (34 KB)
│       │   ├── LaunchpadPage.tsx     Market launch
│       │   ├── BlackboxPage.tsx      Black box interface
│       │   ├── BreachConsolePage.tsx  Breach console
│       │   ├── ExportConsolePage.tsx  Export console
│       │   ├── VerifyPage.tsx        Verification interface
│       │   └── HomePage.tsx          Home page
│       │
│       ├── components/               Reusable UI components (23 dirs)
│       ├── api/                      API client modules
│       ├── contexts/                 React context providers (6)
│       ├── hooks/                    Custom hooks (21)
│       ├── lib/                      Utility libraries (7)
│       ├── types/                    TypeScript type definitions (19)
│       ├── constants/                Application constants
│       ├── theme/                    Styling & theming
│       ├── utils/                    Utility functions
│       ├── assets/                   Static assets
│       └── demo/                     Demo data (10 modules)
│
├── theatre/                          Theatre verification system
│   ├── __init__.py
│   │
│   ├── engine/                       Verification engine core (17 modules)
│   │   ├── canonical_json.py         RFC 8785 canonical JSON
│   │   ├── certificate.py            Certificate generation
│   │   ├── commitment.py             Commitment protocol (SHA-256)
│   │   ├── evidence_bundle.py        Evidence bundle builder
│   │   ├── models.py                 Data models (GroundTruthRecord, etc.)
│   │   ├── oracle_contract.py        Oracle adapter contract
│   │   ├── replay.py                 Replay engine
│   │   ├── resolution.py             Resolution programme
│   │   ├── scoring.py                Scoring provider
│   │   ├── state_machine.py          Theatre state machine
│   │   ├── template_validator.py     Schema validation
│   │   └── tier_assigner.py          Tier assignment logic
│   │
│   ├── scoring/                      Deterministic scoring functions
│   │   ├── __init__.py               Exports all scorers
│   │   ├── waterfall_scorer.py       Distribution waterfall (5 checks)
│   │   ├── escrow_scorer.py          Escrow milestone release (5 checks)
│   │   ├── reconciliation_scorer.py  Ledger reconciliation (5 checks)
│   │   └── deterministic_oracle.py   Passthrough oracle adapter
│   │
│   ├── integration/                  Integration bridges (10 modules)
│   │
│   └── fixtures/                     Test fixtures & datasets
│       ├── __init__.py
│       ├── product_observer_v1.json
│       ├── product_cartograph_v1.json
│       ├── product_easel_v1.json
│       ├── observer_provenance.jsonl
│       ├── cartograph_grid_reference.jsonl
│       ├── easel_tdr_records.jsonl
│       │
│       ├── two_rail_theatres_v0_1/   Two-Rail deterministic theatres
│       │   ├── README.txt
│       │   ├── datasets/
│       │   │   ├── waterfall_fixtures_10.json
│       │   │   ├── escrow_fixtures_10.json
│       │   │   ├── escrow_fixtures_v02_11.json
│       │   │   ├── reconciliation_fixtures_10.json
│       │   │   ├── arrears_fixtures_10.json
│       │   │   ├── osint_composed_oracle_fixtures_10.json
│       │   │   ├── osint_composed_oracle_v1_1_extension_4.json
│       │   │   ├── echelon_osint_source_registry_v0_3_2.json
│       │   │   └── echelon_osint_source_registry_v0_4_0.json
│       │   └── templates/
│       │       ├── DISTRIBUTION_WATERFALL_V1.template.json
│       │       ├── ESCROW_MILESTONE_RELEASE_V1.template.json
│       │       ├── LEDGER_RECONCILIATION_V1.template.json
│       │       ├── ARREARS_RESOLUTION_V1.template.json
│       │       └── OSINT_COMPOSED_ORACLE_V1.template.json
│       │
│       └── echelon_quant_v0_2/       LMSR quant market theatres
│           ├── README.txt
│           ├── ledger_schema.json
│           ├── example_ledger.jsonl
│           ├── api_fidelity_suite_v0_1/
│           │   ├── QUANT_MARKET_API_FIDELITY_V1.template.json
│           │   └── api_fidelity_fixtures_10.json
│           ├── b_sensitivity_suite_v0_1/
│           │   ├── LMSR_B_SENSITIVITY_SUITE_V1.template.json
│           │   └── b_sensitivity_fixtures_5.json
│           ├── perturbation_suite_v0_1/
│           │   ├── QUANT_MARKET_PERTURBATION_HARNESS_V1.template.json
│           │   └── perturbation_fixtures_10.json
│           └── quant_market_hygiene_v0_1/
│               ├── QUANT_MARKET_HYGIENE_V1.template.json
│               ├── quant_market_hygiene_fixtures_10.json
│               └── README.txt
│
├── verification/                     Echelon verification package
│   ├── pyproject.toml
│   └── src/echelon_verify/
│       ├── __init__.py
│       ├── certificate/              Certificate system
│       ├── ingestion/                Data ingestion
│       ├── oracle/                   Oracle system
│       └── scoring/                  Scoring system
│           └── prompts/              LLM prompts for scoring
│
├── smart-contracts/                  Solidity · Hardhat · Chainlink VRF
│   ├── hardhat.config.js
│   ├── package.json
│   ├── contracts/                    Solidity contract sources
│   ├── scripts/                      Deployment scripts
│   ├── test/
│   │   └── PredictionMarket.test.js
│   └── artifacts/                    Compiled contract artefacts
│
├── tests/                            Cross-cutting test suite
│   └── theatre/                      Theatre integration tests
│       ├── test_observer_integration.py   Observer tests (93)
│       ├── test_two_rail_integration.py   Two-Rail tests (8)
│       └── test_github_ingester.py        GitHub ingester tests
│
├── scripts/                          Development & deployment utilities
│   ├── run_observer_theatre.py       Observer theatre runner (20 KB)
│   ├── run_two_rail_theatres.py      Two-Rail theatre runner (17 KB)
│   ├── setup_backend.sh              Backend initialisation
│   ├── start_backend.sh              Start backend server
│   ├── start_frontend.sh             Start frontend dev server
│   ├── seed_database.sh              Database seeding
│   ├── diagnostic.py                 Diagnostic tools
│   └── ...                           Maintenance & monitoring scripts
│
├── mcp/                              Echelon MCP Server (Cycle-009)
│   ├── __init__.py
│   ├── __main__.py                   Entry point
│   ├── server.py                     MCP server (echelon_verify, echelon_hash, echelon_status, echelon_calibrate)
│   ├── http.py                       HTTP transport (POST /mcp, GET /health, GET /sse)
│   ├── models/                       MCP data models
│   ├── tools/                        MCP tool implementations
│   └── tests/                        MCP test suite (69 tests)
│
├── tools/                            Standalone utilities
│   ├── echelon_verify.py             Verifier CLI (v0.1) — zero dependencies
│   ├── echelon_demo.sh               Escrow Wedge Demo Pack Generator (v0.2)
│   ├── validate_osint_registry.py    OSINT Source Registry validator — zero dependencies
│   └── validate_osint_fixtures.py    OSINT fixture dataset validator — zero dependencies
│
├── docs/                             Documentation
│   ├── core/                         (emptied — core docs migrated to Obsidian vault)
│   ├── architecture/                 System architecture
│   ├── dev/                          Developer guides (18 dirs)
│   ├── ops/                          Operations documentation (45 dirs)
│   ├── schemas/                      JSON schemas (8 dirs)
│   ├── simulation/                   Simulation documentation
│   └── technical/                    Technical specifications
│
├── data/                             Runtime data & state
│   ├── osint_state.json              OSINT database (7 MB)
│   ├── markets.json                  Market data (7 MB)
│   ├── economy_state.json            Economic state
│   ├── orchestrator_stats.json       Orchestrator statistics
│   ├── seed/                         Seed data
│   ├── theatres/                     Theatre-specific data
│   └── snapshots/                    World state snapshots (56 forks)
│       └── FORK_*/                   Each contains world_state.json + metadata.json
│
├── grimoires/loa/                    Project memory & history (Loa framework)
│   ├── ledger.json                   Sprint ledger (global numbering)
│   ├── prd.md                        Product requirements document
│   ├── sdd.md                        Software design document
│   ├── sprint.md                     Current sprint plan
│   ├── NOTES.md                      Cross-session observations
│   ├── a2a/                          Sprint artefacts (sprint-5 → sprint-31)
│   ├── archive/                      Completed cycles (7 archived)
│   ├── context/                      Project context documents
│   ├── memory/                       Persistent observations
│   ├── ground-truth/                 Verified facts
│   ├── reality/                      Codebase reality snapshots
│   ├── visions/entries/              Vision entries
│   └── analytics/                    Usage analytics
│
├── archive/                          Legacy code
│   └── frontend-legacy/              Previous Next.js frontend
│
├── .claude/                          System Zone (Loa framework — DO NOT EDIT)
│   ├── loa/                          Framework instructions
│   ├── commands/                     CLI commands (56)
│   ├── skills/                       Skill definitions (31)
│   ├── protocols/                    Process protocols (57)
│   ├── scripts/                      Automation scripts (217)
│   ├── hooks/                        Pre/post execution hooks (13)
│   ├── schemas/                      Framework schemas (30)
│   ├── templates/                    Code templates (12)
│   ├── lib/                          Framework libraries (12)
│   ├── data/                         Framework data (11 dirs)
│   └── settings.json                 Global settings
│
├── .run/                             Run mode state (ephemeral)
├── .beads/                           Beads task tracking state
│
│   ─── Root configuration ───
├── CLAUDE.md                         Claude Code project instructions
├── BUTTERFREEZONE.md                 Agent-grounded project summary
├── CONTEXT.md                        Project context
├── PROCESS.md                        Workflow documentation (68 KB)
├── README.md                         Project README
├── pyproject.toml                    Python project configuration
├── package.json                      Root npm/pnpm configuration
├── .loa.config.yaml                  Loa framework configuration
├── .gitignore                        Git ignore rules
└── database.db                       SQLite database
```

## Subsystem Relationships

```
                    ┌─────────────────────────────────┐
                    │         frontend/ (React)        │
                    │    Pages · Components · Hooks    │
                    └──────────────┬──────────────────┘
                                   │ REST + WebSocket
                    ┌──────────────▼──────────────────┐
                    │       backend/ (FastAPI)          │
                    │                                   │
                    │  ┌─────────┐  ┌──────────────┐   │
                    │  │  api/   │  │  websockets/  │   │
                    │  └────┬────┘  └──────┬───────┘   │
                    │       │              │            │
                    │  ┌────▼──────────────▼────────┐  │
                    │  │         core/               │  │
                    │  │  models · orchestrator ·    │  │
                    │  │  CPMM · OSINT · signals    │  │
                    │  └────┬───────────────────┬──┘  │
                    │       │                   │      │
                    │  ┌────▼────┐    ┌────────▼───┐  │
                    │  │ agents/ │    │ simulation/ │  │
                    │  │ skills/ │    │ timeline/   │  │
                    │  └────┬────┘    └────────────┘  │
                    │       │                          │
                    │  ┌────▼─────────────────┐       │
                    │  │    services/          │       │
                    │  │  theatre_bridge.py    │       │
                    │  │  verification_bridge  │       │
                    │  └────┬─────────────────┘       │
                    └───────┼──────────────────────────┘
                            │
              ┌─────────────▼──────────────┐
              │      theatre/ (engine)      │
              │                             │
              │  engine/    scoring/         │
              │  replay     waterfall        │
              │  commit     escrow           │
              │  evidence   reconciliation   │
              │  templates  deterministic    │
              │                             │
              │  fixtures/                  │
              │  ├── two_rail_v0_1/         │
              │  └── echelon_quant_v0_2/    │
              └─────────────┬──────────────┘
                            │
              ┌─────────────▼──────────────┐
              │   verification/ (echelon)   │
              │   certificate · ingestion   │
              │   oracle · scoring/prompts  │
              └─────────────┬──────────────┘
                            │
              ┌─────────────▼──────────────────┐
              │   tools/ (standalone CLI)       │
              │   echelon_verify.py             │
              │   echelon_demo.sh               │
              │   validate_osint_registry.py    │
              │   validate_osint_fixtures.py    │
              └────────────────────────────────┘

              ┌─────────────────────────────┐
              │    mcp/ (Echelon MCP)       │
              │  server · http · tools      │
              │  echelon_verify/hash/status  │
              │  echelon_calibrate           │
              └─────────────┬───────────────┘
                            │ consumes certificates
              ┌─────────────▼──────────────┐
              │  backend/market/ (010a)     │
              │  LMSR · lifecycle · trading │
              │  positions · settlement     │
              └────────────────────────────┘
                  (planned — Cycle-010a)

              ┌────────────────────────────┐
              │  smart-contracts/ (Solidity)│
              │  Hardhat · Chainlink VRF   │
              └────────────────────────────┘
                  (standalone, called via
                   backend/blockchain_manager)

              ┌────────────────────────────┐
              │  .claude/ (Loa framework)  │
              │  skills · hooks · scripts  │
              │  protocols · schemas       │
              └────────────────────────────┘
                  (orchestrates development
                   workflow, not application)
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 19, TypeScript, Vite, Tailwind CSS |
| Backend | Python 3.12, FastAPI, SQLAlchemy, Alembic |
| Database | SQLite (local), PostgreSQL (production) |
| Blockchain | Solidity, Hardhat, Chainlink VRF |
| Verification | Echelon Theatre engine, deterministic scorers |
| Testing | Pytest (backend/theatre), Jest (frontend) |
| Deployment | Docker, Vercel (frontend), Railway (backend) |

## Major Subsystems

| # | Subsystem | Location | Purpose |
|---|-----------|----------|---------|
| 1 | Agent System | `backend/agents/`, `backend/skills/` | Autonomous agents with brains, skills, genealogy |
| 2 | Theatre Verification | `theatre/`, `verification/` | Deterministic verification of market constructs |
| 3 | Simulation Engine | `backend/simulation/` | Digital twin, world state, event orchestration |
| 4 | OSINT Intelligence | `backend/core/osint_*` | Multi-source open-source intelligence gathering |
| 5 | Timeline/Fork Management | `backend/timeline/` | Timeline divergence and fork tracking |
| 6 | Market Mechanics | `backend/core/cpmm.py`, `backend/market/` (010a) | CPMM (legacy), LMSR market engine (010a: cost function, lifecycle, trading, settlement) |
| 11 | MCP Server | `mcp/` | Echelon MCP surface: echelon_verify, echelon_hash, echelon_status, echelon_calibrate, HTTP transport |
| 7 | Situation Room | `backend/core/situation_room_engine.py` | Real-time event monitoring and response |
| 8 | Signal Detection | `backend/core/signal_detector.py` | Market signal identification |
| 9 | Narrative System | `backend/core/narrative_war.py` | Narrative conflict and information warfare |
| 10 | Smart Contracts | `smart-contracts/` | On-chain prediction market settlement |
