# Cycle-016 Review Bootstrap (New Thread Starter)

Use this as the first message in the next thread.

---

Continue Cycle-016 review in repo `/Users/tobiasharber/Developer/prediction-market-monorepo.nosync`.

## Current Status
- Sprint-0 coherence lock complete.
- Sprint-1 complete (mock purge + real API wiring).
- Sprint-2 complete (investigation dashboard + certificate explorer).
- Sprint-3 complete (OpsBoard + Analytics + RLMF + VRF reshape).
- Sprint-4 and Sprint-5 pending.
- Branch: `feature/cycle-016-results-surface`.
- Working tree is dirty with active Cycle-016 work; do not revert unrelated edits.

## Read First
1. `/Users/tobiasharber/Developer/prediction-market-monorepo.nosync/grimoires/loa/prd.md`
2. `/Users/tobiasharber/Developer/prediction-market-monorepo.nosync/grimoires/loa/sdd.md`
3. `/Users/tobiasharber/Developer/prediction-market-monorepo.nosync/grimoires/loa/sprint.md`

## Primary Review Scope
- Validate Sprint-1 wiring correctness (mock purge, API contracts, TS type alignment).
- Validate Sprint-2 investigation backend/frontend contract and behavior.
- Validate Sprint-3 production-surface changes (OpsBoard/Analytics/RLMF/VRF) against Loa claims.
- Check PRD/SDD/sprint coherence (no requirement drift).
- Findings-first review output: bugs/regressions/missing tests ordered by severity with file:line.

## Priority Files
### Backend
- `/Users/tobiasharber/Developer/prediction-market-monorepo.nosync/backend/api/investigation_routes.py`
- `/Users/tobiasharber/Developer/prediction-market-monorepo.nosync/backend/schemas/investigation_schemas.py`
- `/Users/tobiasharber/Developer/prediction-market-monorepo.nosync/backend/tests/test_investigation_routes.py`
- `/Users/tobiasharber/Developer/prediction-market-monorepo.nosync/backend/api/agents_routes.py`
- `/Users/tobiasharber/Developer/prediction-market-monorepo.nosync/backend/main.py`

### Frontend (Sprint-1/2)
- hooks: `usePortfolio`, `useMarketplace`, `useAgents`, `useBreaches`, `useWatchlist`, `useInvestigation`
- pages: `PortfolioPage`, `MarketplacePage`, `AgentsPage`, `BreachConsolePage`, `InvestigationPage`
- investigation components: `frontend/src/components/investigation/*`
- types: `portfolio/marketplace/agents/watchlist/investigation/theatre/index`
- tests: `frontend/src/hooks/__tests__/*`, `frontend/src/pages/__tests__/*`, `frontend/src/test/type-alignment.test.ts`

### Frontend (Sprint-3)
- `/Users/tobiasharber/Developer/prediction-market-monorepo.nosync/frontend/src/pages/HomePage.tsx`
- `/Users/tobiasharber/Developer/prediction-market-monorepo.nosync/frontend/src/pages/BlackboxPage.tsx`
- `/Users/tobiasharber/Developer/prediction-market-monorepo.nosync/frontend/src/pages/RLMFPage.tsx`
- `/Users/tobiasharber/Developer/prediction-market-monorepo.nosync/frontend/src/pages/VRFPage.tsx`
- `/Users/tobiasharber/Developer/prediction-market-monorepo.nosync/frontend/src/api/opsBoard.ts`
- `/Users/tobiasharber/Developer/prediction-market-monorepo.nosync/frontend/src/components/blackbox/*`

## Reviewer Output Required
1. Findings list (`P1/P2/P3`) with file:line and concrete fix.
2. `Must-for-Sprint-4` vs `Defer` table.
3. Go/No-Go recommendation for Sprint-4 start.
4. If clean: explicit statement `no blocking findings`, plus residual risks/test gaps.

## Suggested Verification Commands
Run from repo root:

```bash
git status --short
pytest backend/tests/test_investigation_routes.py -q
pytest backend/engines/tests -q
cd frontend && npm test -- --runInBand
cd frontend && npm run typecheck
rg -n "mock|demo|hardcoded|USE_MOCKS" frontend/src backend | head -n 200
```

## Notes
- Gate-C policy is now enforced for backend writers: `FlapDirection.*.value`, no bare direction strings.
- Backend stability contract remains 0–1 internally with API boundary conversion where required.

