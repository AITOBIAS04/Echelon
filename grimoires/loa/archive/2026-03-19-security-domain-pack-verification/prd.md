# PRD — Cycle-037c: Security + Domain Pack Verification

**Cycle:** cycle-037c
**Date:** 19 March 2026
**Depends on:** Cycle-037 (contract substrate), Cycle-037b (multi-evaluator orchestration), Cycles 026a–026c (anchor packs)
**Sprints:** 4 (0–3)
**Builder:** Loa (backend only)
**Planning source:** domain-pack expansion, security construct support, frontmatter-aware corpora support

> Sources: context_037c.md, prd_037c.md, sdd_037c.md, sprint_037c.md, codebase validation

---

## 1. Problem Statement

### 1.1 The Substrate Exists, But Domain Packs Are Still Generic

After 037 and 037b, Echelon can compile a contract and evaluate it with deterministic-first plus residual convergence. What it still lacks is deep domain support for high-value construct families — especially security constructs.

### 1.2 Security Is The Best First Domain Pack

Security constructs are unusually well-suited to contract-backed verification because:

- many claims are mechanically testable
- published taxonomies and standards exist (OWASP Top 10, CWE, MITRE ATT&CK)
- the Anthropic cybersecurity skills corpus provides structured frontmatter, workflows, references, and verification sections
- the anchor mapper (`construct_anchor_mapper.py`) already maps security keywords to `PUBLIC_STANDARD`

### 1.3 The Goal Is Not "Hardcode Security Everywhere"

Cycle 037c must remain a domain-pack layer on top of the general substrate:

- frontmatter-aware corpus ingestion (new — `spec_loader.py` only handles pure YAML today)
- security-specific deterministic check families
- corpus-specific policy normalization with precise security domains
- richer anchor mapping for security frameworks

That keeps 037 general and makes 037c additive.

---

## 2. Product Contracts

### 2.1 Domain Pack Loader

Add a generic domain-pack loader that can:

- ingest frontmatter-aware corpora (YAML frontmatter + Markdown body)
- parse references and verification sections from Markdown
- expose normalized domain-pack metadata for downstream consumers
- handle frontmatter stripping before delegating to `spec_loader.load()` where applicable

> Codebase note: `spec_loader.py` (76 lines) expects pure YAML. The domain pack loader must handle frontmatter extraction itself.

### 2.2 Security Policy Rules — Precise Domain Promotion

The policy normalizer (`policy_normalizer.py`, 130 lines) currently lists "security" in `KNOWN_VAGUE_TERMS`, which tier-caps any security construct to UNVERIFIED. Cycle 037c resolves this by:

- Adding specific security domains to `KNOWN_PRECISE_DOMAINS`:
  - `vulnerability_analysis`
  - `attack_surface_mapping`
  - `threat_modeling`
  - `secure_code_review`
  - `incident_response`
  - `cryptographic_implementation`
  - `access_control_design`
  - `network_security`
  - `penetration_testing`
  - `compliance_auditing`

- Broad "security" remains vague (guardrail preserved)
- Security policy rules map framework references (ATT&CK, CWE, OWASP) to anchored claims
- Workflows with verification sections generate deterministic requirements where possible
- Unsupported broad security claims stay downgraded or rejected

### 2.3 Security Deterministic Check Families

Five new `check_type` values extending the 037 contract model via `check_planner.py`:

| check_type | What It Validates | Anchor Class |
|---|---|---|
| `attack_technique_mapping` | Claims map to valid ATT&CK technique IDs | PUBLIC_STANDARD |
| `tool_invocation_correctness` | Security tool usage matches documented syntax | DETERMINISTIC_CHECK |
| `standards_compliance` | Claims reference valid OWASP/CWE/NIST entries | PUBLIC_STANDARD |
| `dependency_vulnerability_check` | Dependency scanning claims are verifiable | DETERMINISTIC_CHECK |
| `secret_leak_check` | Secret detection claims are testable | DETERMINISTIC_CHECK |

These extend the existing extensible `check_type` model without changing its schema. `PlannedCheck.check_type` is already a free string field.

### 2.4 External Anchors

Extend the anchor mapper (`construct_anchor_mapper.py`, 173 lines) with security-specific dimension mappings:

- ATT&CK technique references → `PUBLIC_STANDARD` with `anchor_id: attack_framework`
- OWASP/CWE references → `PUBLIC_STANDARD` with `anchor_id: security_standards`
- Corpus skill references → `PUBLIC_STANDARD` with `anchor_id: security_skill_corpus`

Security claims without a valid anchor should remain weak or rejected by policy.

### 2.5 Corpus Compatibility Target

Primary compatibility target for domain pack loader:

- YAML frontmatter (skill metadata, references, verification sections)
- Markdown workflow body
- References section (framework IDs, tool names)
- Verification section (testable assertions)

---

## 3. What This Cycle Does NOT Do

- **Does NOT rebuild the 037 contract substrate.** Additive only.
- **Does NOT replace the 037b scorer orchestration layer.** Consumes it.
- **Does NOT attempt every domain at once.** Security is the first serious domain pack.
- **Does NOT create live API endpoints for domain pack management.** Service-layer only.

---

## 4. Codebase-Grounded Integration Points

> Corrected from pre-staged context using codebase validation.

| Service | Actual File | Lines | Integration |
|---|---|---|---|
| Spec loader | `backend/services/spec_loader.py` | 76 | Domain pack loader wraps this for frontmatter stripping |
| Policy normalizer | `backend/services/policy_normalizer.py` | 130 | Add precise security domains to `KNOWN_PRECISE_DOMAINS` |
| Check planner | `backend/services/check_planner.py` | 136 | Security check planner wraps/extends for new check families |
| Anchor mapper | `backend/services/construct_anchor_mapper.py` | 173 | Add security-specific `_MAPPING_RULES` entries |
| Rubric registry | `backend/data/construct_rubrics/__init__.py` | — | Future: security rubric scorers (not this cycle) |

---

## 5. Acceptance Criteria

1. Frontmatter-aware corpora can be ingested as domain-pack sources (YAML frontmatter + Markdown body)
2. Security-specific deterministic check families are supported by the planner (5 new check_types)
3. ATT&CK / OWASP / CWE anchors can be attached to security claims
4. At least one security corpus fixture compiles into a valid contract
5. Precise security domains pass policy normalization without tier-capping
6. Broad "security" claims remain vague (guardrail preserved)
7. Existing 037/037b paths are unaffected (regression)
8. ≥20 new tests pass

---

## 6. Test Plan

| Area | Tests | Coverage |
|---|---|---|
| Frontmatter corpus ingestion | 5 | parse skill frontmatter + body + references + verification |
| Security policy normalization | 5 | precise domains pass, vague "security" stays capped, reference mapping |
| Security deterministic planning | 5 | ATT&CK, tool invocation, standards compliance, dependency, secret leak |
| Anchor mapping | 3 | OWASP/CWE/ATT&CK attachment, missing anchor rejection |
| Regression | 4 | core 037/037b paths unaffected |
| **Total** | **~22** | |

---

## 7. Why This Matters

Cycle 037c is the first proof that the contract substrate can handle a real domain pack, not just generic construct prose. Security is the best first candidate because it has the strongest combination of structured corpora, deterministic checks, and public standards. If this works, every other domain pack follows the same pattern.
