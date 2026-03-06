# Sprint 2 (Global 44) — Security Audit

**Auditor:** Paranoid Cypherpunk Auditor
**Date:** 2026-03-06
**Verdict:** APPROVED - LETS FUCKING GO

## Security Checklist

| Category | Status |
|----------|--------|
| Secrets/Credentials | CLEAN — no hardcoded secrets |
| SQL Injection | CLEAN — ORM parameterized queries only |
| Input Validation | CLEAN — no user input in aggregation pipeline |
| Auth/Authz | CLEAN — internal server-side computation, no user-facing endpoint |
| XSS | CLEAN — React JSX auto-escaping, numeric values only, no dangerouslySetInnerHTML |
| Info Disclosure | CLEAN — flow metrics are public market data, not sensitive |
| Error Handling | CLEAN — aggregator returns defaults on empty data, game loop catches exceptions |
| Data Integrity | CLEAN — flow computed server-side from immutable wing flap records |
| Resource Exhaustion | CLEAN — 60s cadence prevents hot-looping, sequential timeline iteration |

## Detailed Notes

**TaoFlowAggregator** (`tao_flow_aggregator.py:43-74`): All queries use SQLAlchemy ORM `.where()` with parameterized bindings. `timeline_id` comes from internal `Timeline.id` column (line 88), never from user input. `WingFlap.flap_type.in_(TRADE_FLAP_TYPES)` uses enum values, not strings. `func.coalesce(..., 0.0)` prevents NULL propagation.

**Game loop integration** (`game_loop.py:161-163`): `_tao_flow_task` runs inside the existing `_run_task` wrapper which catches all exceptions (line 186). A failed aggregation cannot crash the game loop. The 60s interval prevents CPU abuse.

**compute_all N+1 concern** (`tao_flow_aggregator.py:91-102`): The loop issues 2 queries per timeline plus 1 select for update. For N timelines, that's 3N+1 queries. Current scale (~100 timelines) makes this irrelevant. If scale reaches thousands, batch this. Not a security issue, noting for future perf awareness.

**API pass-through** (`butterfly_engine.py:699-700`): `getattr(timeline, 'net_inflow_24h', 0.0) or 0.0` — double-safe default. Flow values are read-only from the perspective of the API consumer. No mutation endpoint exists.

**Frontend FlowBadge** (`WorldMonitorPage.tsx:15-37`): Renders `{formatted}` inside JSX span — React auto-escapes. The `value` prop is typed as `number`, so no string injection possible. `toFixed()` and `toLocaleString()` operate on numeric primitives. `title` attribute also auto-escaped by React.

**Frontend MarketCard** (`MarketCard.tsx:268-287`): Same pattern — numeric values rendered via JSX auto-escaping. Feature flag gate (`isEnabled('CYCLE_017_TAO_FLOW')`) prevents rendering when disabled.

**No new API endpoints**: This sprint adds no new routes or query parameters. All data flows through existing internal pathways. Attack surface is unchanged.

## Zero findings. Ship it.
