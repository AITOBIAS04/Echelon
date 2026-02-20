# Reality Index — Echelon Prediction Market Monorepo

> **Generated**: 2026-02-18 | **Commit**: main
> Hub file for token-efficient codebase queries. Each spoke contains grounded references.

## Spokes

| File | Contents | Use When |
|------|----------|----------|
| `structure.md` | Directory tree, module responsibilities | "Where does X live?" |
| `types.md` | All types, interfaces, enums, models | "What shape is the data?" |
| `api-surface.md` | Routes, endpoints, component props | "How do modules communicate?" |
| `architecture.md` | System topology, data flows, patterns | "How does the system work?" |

## Quick Facts

- **Monorepo**: 3 packages (frontend, backend, smart-contracts)
- **Frontend**: React 19 + TypeScript + Vite 7 + Tailwind 3
- **Backend**: Python 3.12 + FastAPI + PostgreSQL (Pydantic v2)
- **Contracts**: Solidity on Base Sepolia (5 contracts)
- **Frontend routes**: 13 active routes (`frontend/src/router.tsx`)
- **Backend modules**: agents, core, simulation, payments, missions, skills, wallets
- **Current build target**: Community Oracle Verification Pipeline (Phase 1)
- **Demo mode**: `?demo=1` or `VITE_DEMO_MODE=true` for simulation UI
