# Codebase Structure — Echelon

> **Generated**: 2026-02-18

```
prediction-market-monorepo.nosync/
├── frontend/                          # React 19 + TypeScript + Vite 7
│   ├── src/
│   │   ├── router.tsx                 # 13 routes, React Router v7
│   │   ├── pages/                     # Page components (13 files)
│   │   │   ├── MarketplacePage.tsx     # Main market listing (default route)
│   │   │   ├── LaunchpadPage.tsx       # Market launch + live feed
│   │   │   ├── LaunchpadNewPage.tsx    # 3-step creation wizard
│   │   │   ├── LaunchpadDetailPage.tsx # Individual timeline
│   │   │   ├── PortfolioPage.tsx       # User positions
│   │   │   ├── BlackboxPage.tsx        # Analytics (route: /analytics)
│   │   │   ├── RLMFPage.tsx            # RLMF forecasting
│   │   │   ├── VRFPage.tsx             # VRF lottery
│   │   │   ├── BreachConsolePage.tsx   # Breach monitoring
│   │   │   ├── ExportConsolePage.tsx   # RLMF export management
│   │   │   ├── TimelineDetailPage.tsx  # Timeline view
│   │   │   ├── AgentsPage.tsx          # (legacy)
│   │   │   └── HomePage.tsx            # (legacy)
│   │   ├── components/
│   │   │   ├── layout/                # AppLayout, Sidebar, TopActionBar
│   │   │   ├── agents/               # AgentRoster, AgentDetail (5 files)
│   │   │   ├── blackbox/             # Analytics charts (29 files)
│   │   │   ├── marketplace/          # Market cards, filters (6 files)
│   │   │   ├── timeline/             # Timeline components (6 files)
│   │   │   ├── fieldkit/             # Portfolio widgets (16 files)
│   │   │   ├── home/                 # Home page widgets (15 files)
│   │   │   ├── sigint/               # OSINT signal display (5 files)
│   │   │   ├── paradox/              # Paradox engine UI (5 files)
│   │   │   ├── breach/               # Breach console (2 files)
│   │   │   ├── exports/              # Export console (4 files)
│   │   │   ├── watchlist/            # Watchlist (3 files)
│   │   │   ├── ui/                   # Shared UI (4 files)
│   │   │   ├── common/               # RouteErrorBoundary (2 files)
│   │   │   ├── system/               # ErrorBoundary (1 file)
│   │   │   ├── graph/                # Graph visualization (1 file)
│   │   │   ├── replay/               # Replay UI (1 file)
│   │   │   ├── risk/                 # Risk display (1 file)
│   │   │   ├── routing/              # Route helpers (2 files)
│   │   │   └── ButlerWidget.tsx       # AI assistant widget
│   │   └── demo/
│   │       ├── DemoEngine.tsx         # Event generation & scheduling
│   │       ├── demoStore.ts           # Central state management
│   │       └── hooks.ts              # React hooks for demo data
│   ├── package.json                   # React 19, Vite 7, Tailwind 3
│   └── tailwind.config.js             # Terminal design tokens
│
├── backend/                           # Python 3.12 + FastAPI
│   ├── core/
│   │   ├── models.py                  # Enums, missions, narratives, genomes (977 lines)
│   │   ├── cpmm.py                    # CPMM market maker (constant product)
│   │   ├── database.py                # SQLAlchemy DB connection
│   │   ├── security.py                # Auth, JWT
│   │   ├── blockchain_manager.py      # Web3 interaction
│   │   ├── wallet_factory.py          # HD wallet generation
│   │   ├── osint_registry.py          # OSINT source registration
│   │   ├── osint_sources_*.py         # Financial, sports, extended, situation room
│   │   ├── synthetic_osint.py         # Synthetic OSINT generation
│   │   ├── news_scraper.py            # News feed ingestion
│   │   ├── signal_detector.py         # Signal detection
│   │   ├── narrative_war.py           # Narrative warfare engine
│   │   ├── mission_generator.py       # Mission generation from OSINT
│   │   ├── rpg_agent_brain.py         # RPG-style agent decision
│   │   ├── mock_data_generator.py     # Test data generation
│   │   ├── situation_room_engine.py   # Situation room backend
│   │   ├── event_orchestrator.py      # Event orchestration
│   │   ├── persistence_manager.py     # State persistence
│   │   ├── football_data_client.py    # Football API client
│   │   ├── autouploader.py            # Auto-upload utility
│   │   └── x402_client.py             # x402 protocol client
│   ├── agents/
│   │   ├── schemas.py                 # Pydantic agent models (888 lines)
│   │   ├── brain.py                   # Multi-provider LLM brain
│   │   ├── multi_brain.py             # Multi-brain coordination
│   │   ├── handler_brain.py           # Handler brain routing
│   │   ├── skills_brain.py            # Skills-based brain
│   │   ├── shark_strategies.py        # Shark trading strategies
│   │   ├── agent_skills_bridge.py     # Agent-skills integration
│   │   └── genealogy_manager.py       # Agent genealogy tracking
│   ├── simulation/
│   │   ├── engine.py                  # Core simulation engine
│   │   ├── world_state.py             # World state management
│   │   ├── timeline_manager.py        # Timeline forking/management
│   │   ├── scheduler.py               # Simulation heartbeat scheduler
│   │   ├── genome.py                  # Agent genome system
│   │   ├── breeding_lab.py            # Evolutionary breeding
│   │   ├── evolution_engine.py        # Natural selection
│   │   ├── yield_manager.py           # Founder yield calculations
│   │   ├── brain_integration.py       # Brain-simulation bridge
│   │   ├── sim_market_engine.py       # Market simulation
│   │   ├── sim_geopolitics_engine.py  # Geopolitical simulation
│   │   ├── sim_football_engine.py     # Football simulation
│   │   ├── sim_election_engine.py     # Election simulation
│   │   ├── digital_twin_engine.py     # Digital twin simulation
│   │   └── situation-room/            # Situation room module
│   ├── api/
│   │   ├── markets.py                 # Market endpoints
│   │   ├── situation_room.py          # Situation room API
│   │   └── situation_room_routes.py   # Situation room routes
│   ├── payments/
│   │   ├── coinbase_commerce.py       # Coinbase Commerce integration
│   │   └── routes.py                  # Payment routes
│   ├── missions/
│   │   └── mission_factory.py         # Mission creation from OSINT
│   ├── skills/
│   │   ├── skill_router.py            # Skill routing
│   │   ├── skill_loader.py            # Dynamic skill loading
│   │   ├── provider_registry.py       # Provider management
│   │   └── context_compiler.py        # Context compilation
│   ├── wallets/
│   │   └── wallet_factory.py          # Wallet generation
│   └── integrations/
│       └── builder_attribution.py     # Builder attribution
│
├── smart-contracts/                   # Solidity (Base Sepolia)
│   └── contracts/
│       ├── PredictionMarket.sol        # Core LMSR market contract
│       ├── TimelineShard.sol           # Fork mechanics
│       ├── SabotagePool.sol            # Risk/sabotage system
│       ├── HotPotatoEvents.sol         # Dynamic payout events
│       └── EchelonVRFConsumer.sol       # Chainlink VRF integration
│
├── docs/                              # Architecture documentation
│   ├── core/
│   │   ├── System_Bible_v10.md         # Complete spec (Grant-Ready)
│   │   ├── OSINT_Reality_Oracle_Appendix_v3_1.md
│   │   └── Real_to_Sim_Incident_Replay_v1.md
│   ├── schemas/
│   │   ├── echelon_theatre_schema.json # Theatre Template spec
│   │   └── echelon_rlmf_schema.json    # RLMF export format
│   ├── technical/
│   │   ├── VRF_Enhanced_Protocol.md
│   │   ├── Archetype_Matrix.md
│   │   ├── Betting_Mechanics.md
│   │   ├── Governance.md
│   │   ├── Oracle_Modes.md
│   │   └── Risk_Mitigation.md
│   └── simulation/                    # Tokenomics modelling
│
├── data/                              # Theatre config, seed fixtures
├── archive/                           # Legacy code
├── loa-grimoire/
│   └── context/
│       └── echelon_context.md          # Phase 1 build brief
└── grimoires/loa/                     # Loa framework state
```
