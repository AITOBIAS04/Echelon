# Context — Cycle-025: WorldMonitor Intelligence Contract v2

**Cycle:** cycle-025
**Date:** 16 March 2026
**Builder:** Loa

---

## Why This Cycle Exists

Three things converged:

1. **Construct verification is live.** Cycle 024 shipped the construct pipeline, and all three Soju constructs (Artisan, K-Hole, Mibera Codex) are registered, scored, and certificated. But they're stuck at UNVERIFIED tier (<50 episodes). Backtesting requires OSINT data flowing through the signals table — which doesn't exist yet.

2. **The merged workspace design is ready.** The WorldMonitor/Investigations/Signal Map pages are being collapsed into a single canvas-dominant workspace. Alexander will wire the frontend, but the backend must expose the data first: feed health, signal queries by layer, convergence cells. (The design's Markets tab is deferred — no Market model exists yet.)

3. **The WorldMonitor contract is half-built.** 7 of 14 MeasureType values. Three POST stubs returning 501. No signal persistence. The contract needs completing before Cycle 026 can register 10 new OSINT sources that write to it.

---

## What Loa Needs To Know

### Existing Code Locations

| What | Where |
|---|---|
| WorldMonitor API contract | `backend/schemas/worldmonitor_api_contract.py` (457 lines) |
| WorldMonitor routes | `backend/api/world_monitor_routes.py` (377 lines) |
| WorldMonitor collector | `backend/osint/collectors/worldmonitor.py` (340 lines) |
| OSINT routes (stub) | `backend/api/osint_routes.py` — signals stub at line 56 |
| OSINT registry | `backend/osint/models/registry.py` — RegistrySource, _VALID_SOURCE_GROUPS (33 values) |
| Sources JSON | `backend/osint/sources.json` — v0.4.0, 6 sources |
| Investigation model | `backend/database/models.py` — Investigation class |
| Database connection | `backend/database/connection.py` — engine, async_session_maker |
| Alembic versions | `alembic/versions/` |

### Key Patterns To Follow

- **POST endpoint pattern:** See `backend/osint/collectors/worldmonitor.py` for the Path 1 collector. Each POST endpoint instantiates `WorldMonitorCollector(domain=WMDomain.X)` (per-domain), calls `collector.fetch(request_dict, theatre_id)` (public method — wraps `_fetch()` with hash invariant enforcement), which returns a `CollectionResult` (with `.bundle: EvidenceBundle | None`, `.success`, `.error`, `.raw_payload`, `.fetch_duration_ms`). Then persists to `osint_signals` via `persist_signal()`. Note: `collector.source_id()` is a method, not a property. Do NOT model these on the `GET /live` endpoint — that uses Path 2 (synthetic).
- **Alembic migration naming:** `c025_osint_signals` — prefix with cycle number.
- **Model pattern:** See existing models in `backend/database/models.py`. Use `String(36)` for UUID PKs, `JSON` for JSONB columns, `func.now()` for server defaults.
- **Response schema pattern:** Pydantic v2 BaseModel. See `backend/schemas/construct_schemas.py` for reference.
- **Test pattern:** See `backend/tests/test_cycle024_sprint1.py` for async test structure with session fixtures.

### Two Signal Paths — Critical Distinction

The backend has **two independent signal architectures.** Cycle 025 extends Path 1 only.

**Path 1 — Registry-based OSINT (extend this):**
- `backend/osint/sources.json` → `RegistryLoader` → `CollectionRunner` → `BaseCollector` subclasses
- Produces `EvidenceBundle` + `HTTPTranscriptReceipt` (hash-verified, settlement-eligible)
- Persisted to DB. Used by Paradox Engine, Theatre settlement, investigation evidence.
- Key directory: `backend/osint/` (models/, engine/, collectors/)

**Path 2 — Synthetic Signal Detector (DO NOT TOUCH):**
- `backend/core/signal_detector.py` → `backend/core/osint_registry.py` (singleton)
- In-memory `Signal` list with `expires_at`. No persistence.
- Serves `GET /api/v1/world-monitor/live` for globe UI.
- **Do not import from, modify, or restructure these files.**

The new `osint_signals` table is Path 1 infrastructure. The new read endpoints (`/osint/signals`, `/osint/health`, `/osint/signals/summary`) query this table. The POST endpoints write to it via Path 1 collectors. Path 2 remains synthetic and in-memory.

### Things That Might Surprise You

1. **The POST stubs reference "Cycle-035"** — this is stale. Replace that reference with Cycle-025.
2. **`MeasureType` is a Python string enum, not a database enum** — no migration needed for enum extension.
3. **The live endpoint (377 lines) uses Path 2 (synthetic)** — don't restructure it. Don't add `persist_signal()` to it. The POST endpoints use Path 1 collectors, which is the correct persistence path.
4. **`sources.json` stays at 6 sources** — Cycle 026 expands it to 16. Don't add sources in this cycle.
5. **There is NO `escalated` column on Investigation** — the health endpoint should use ACTIVE investigation count as escalation proxy.
6. **There is NO Market model in the database** — the design reference shows a Markets tab, but there's no Market table or model. The investigation-scoped markets endpoint is deferred. Do not create a Market model.
7. **Investigation.theatre_id is a plain string, not FK** — many investigations → one theatre. Theatre has no `investigation_id` column. The relationship is one-directional from Investigation.

### Design Reference (For Context Only — Not Loa's Scope)

`output/design_reference/echelon_worldmonitor_investigation_workspace_v1.html` — merged workspace design. Alexander will implement this after Cycle 025 ships. Loa's job is to ensure the backend exposes the data this design needs:

- Feed health → `GET /api/v1/osint/health`
- Signal layers → `GET /api/v1/osint/signals?source_group=...`
- Signal summary → `GET /api/v1/osint/signals/summary`
- POST endpoints → signal persistence for the evidence panel
- Markets tab → **deferred** (no Market model exists)

### Cycle 026 Dependency

Cycle 026 (OSINT Registry Expansion — Batch 1) depends on the `osint_signals` table created in this cycle. The 10 new collectors will write to this table. The signals route will return their data. Build the table correctly now so Cycle 026 is additive.

---

## Soju / Construct Status

All three constructs registered and verified. Issue #49 pending closure comment.

| Construct | Status | Certificate | Tier |
|---|---|---|---|
| artisan:1.4.0 | CERTIFIED | READY | UNVERIFIED |
| khole:1.2.0 | CERTIFIED | READY | UNVERIFIED |
| mibera-codex:1.0.0 | CERTIFIED | READY | UNVERIFIED |

No Soju interaction needed this cycle. Construct verification pipeline is complete and independent.

---

## After This Cycle Ships

1. **Alexander** takes over — wires the merged workspace to the new endpoints
2. **Cycle 026** begins — 10 new OSINT collectors writing to the signals table
3. **Backtesting** can begin — Markov datasets + OSINT signals feed episodes for the 50-episode threshold
