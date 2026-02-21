# Drift Report — Echelon

> **Generated**: 2026-02-18 | **Method**: Three-way analysis (Code ↔ Docs ↔ Build Context)

## Overall Drift Score: **MODERATE** (6/10)

The codebase and documentation are well-aligned on architecture vision. Drift exists primarily between the existing infrastructure (full LMSR/OSINT/agent trading platform) and the current build target (Community Oracle Verification Pipeline, which uses none of that infrastructure).

---

## Category 1: Architecture Drift (Code ↔ Docs)

### CPMM vs LMSR

| What Docs Say | What Code Does |
|---------------|----------------|
| System Bible §III specifies LMSR cost function: `C(x) = b * ln(sum exp(x_j / b))` | `backend/core/cpmm.py` implements CPMM (Uniswap-style): `x * y = k` |

**Impact**: Medium. CPMM is likely a prototype/placeholder. The market math in production must be LMSR per the System Bible. The frontend components may need to adapt to LMSR price curves.

**Source**: `docs/core/System_Bible_v10.md:143-155` vs `backend/core/cpmm.py:1-21`

### Agent Archetype Drift

| What Docs Say | What Code Has |
|---------------|---------------|
| System Bible §VIII: Shark, Spy, Diplomat, Saboteur (4 archetypes) | `backend/core/models.py:36-44`: SPY, DIPLOMAT, TRADER, SABOTEUR, JOURNALIST, PROPAGANDIST, SLEEPER (7 roles) |
| System Bible Appendix A: Archetype Behaviour Matrix for 4 types | `backend/agents/schemas.py:41-66`: WHALE, SHARK, DEGEN, VALUE, MOMENTUM, NOISE (6 financial); STAR, GLASS_CANNON, WORKHORSE, PROSPECT, VETERAN (5 athletic); POPULIST, TECHNOCRAT, INSTIGATOR, MODERATE, IDEOLOGUE (5 political) |

**Impact**: Low. The code has a richer agent taxonomy than the docs describe. This is additive drift (code ahead of docs), not conflicting.

### OSINT Sources Count

| What Docs Say | What Code Has |
|---------------|---------------|
| OSINT Appendix v3.1 §2.1: ~10 illustrative providers | Backend has `osint_sources_financial.py`, `osint_sources_sports.py`, `osint_sources_extended.py`, `osint_sources_situation_room.py`, `synthetic_osint.py` — 5 modules |

**Impact**: Low. Code extends the documented OSINT sources into domain-specific modules.

---

## Category 2: Build Context Drift (Context ↔ Code)

### Phase 1 Build Target vs Existing Code

The `echelon_context.md` defines a focused Community Oracle Verification Pipeline. The codebase contains ~180K LOC of full platform infrastructure that is **explicitly out of scope** for Phase 1.

| Phase 1 Needs | Exists in Codebase? |
|----------------|---------------------|
| GitHub API integration | No — needs to be built |
| Ground truth extraction from PRs | No — needs to be built |
| Oracle construct runner | No — needs to be built |
| LLM-based scoring (precision/recall) | No — needs to be built |
| Calibration certificate generation | No — needs to be built |
| Pydantic model patterns | Yes — `backend/agents/schemas.py` provides patterns |
| Multi-provider LLM routing | Yes — `backend/agents/brain.py` (reusable pattern) |
| RLMF export schema | Yes — `docs/schemas/echelon_rlmf_schema.json` (alignment target) |

**Impact**: High. Phase 1 is greenfield within an existing codebase. The risk is accidentally coupling to existing infrastructure that's out of scope.

---

## Category 3: Documentation Gaps

| Gap | Severity | Notes |
|-----|----------|-------|
| No CHANGELOG.md | Medium | Change history not tracked |
| No CONTRIBUTING.md | Low | Solo project currently |
| No SECURITY.md | Medium | Web3 project should document security posture |
| No CODEOWNERS | Low | Mono-maintainer |
| No ADR (Architecture Decision Records) | Medium | Design decisions undocumented beyond System Bible |
| CONTEXT.md last updated 2026-02-03 | Low | Stale by ~2 weeks but recent changes are cosmetic |
| No API documentation (OpenAPI/Swagger) | Medium | Backend endpoints undocumented |

---

## Category 4: Stale Artifacts

| Artifact | Issue |
|----------|-------|
| `backend/core/cpmm.py` | CPMM implementation when LMSR is the target per System Bible |
| `frontend/src/pages/HomePage.tsx` | Not in router — legacy/orphaned |
| `frontend/src/pages/AgentsPage.tsx` | Not in router — legacy/orphaned |
| `backend/fork_manager.py` (root) | Duplicate of simulation module functionality |
| `backend/wallet_factory.py` (root) | Duplicate of `backend/wallets/wallet_factory.py` |
| `backend/genealogy_manager.py` (root) | Duplicate of `backend/agents/genealogy_manager.py` |

---

## Category 5: Naming Consistency

| Domain | Pattern | Consistency |
|--------|---------|-------------|
| Frontend pages | `*Page.tsx` | 9/10 — consistent |
| Frontend components | Grouped by feature folder | 8/10 — good |
| Backend modules | snake_case files | 7/10 — some legacy |
| Backend models | PascalCase classes, snake_case fields | 9/10 — consistent |
| Enums | UPPER_CASE values | 9/10 — consistent |
| Routes | kebab-case URL paths | 8/10 — consistent |

---

## Recommendations

1. **Create `echelon-verify/` as new top-level package** — isolate Phase 1 from existing infrastructure
2. **Do not refactor existing code** — existing backend/frontend is Phase 2 scope
3. **Follow existing Pydantic patterns** from `backend/agents/schemas.py` for new models
4. **Align certificate schema** with `docs/schemas/echelon_rlmf_schema.json` patterns
5. **Clean up root-level duplicates** (fork_manager.py, wallet_factory.py, genealogy_manager.py) — deferred, not Phase 1
