# Sprint Plan — Cycle-037c: Security + Domain Pack Verification

**Cycle:** cycle-037c
**Date:** 19 March 2026
**Builder:** Loa (backend only)
**Sprints:** 4 (0–3)

> Sources: prd.md, sdd.md, codebase validation

---

## Sprint 0 — Domain Pack Loader + Corpus Parsing

**Goal:** Build generic frontmatter-aware corpus ingestion so any domain pack can be loaded from YAML frontmatter + Markdown body.

**Scope:** SMALL (3 tasks)

### Deliverables

- [ ] `backend/services/domain_pack_loader.py` — CorpusSkill, DomainPack dataclasses + parse functions
- [ ] `backend/tests/test_domain_pack_loader.py` — 5 tests

### Acceptance Criteria

- [ ] `extract_frontmatter()` parses valid `---` delimited YAML frontmatter from Markdown body
- [ ] `extract_frontmatter()` raises `ValueError` on missing delimiter or invalid YAML
- [ ] `parse_references()` extracts ATT&CK T-codes, CWE-IDs, OWASP refs from `## References` section
- [ ] `parse_verification()` extracts testable assertions from `## Verification` section
- [ ] `load_corpus_skill()` produces a complete `CorpusSkill` from frontmatter + body + references + verification
- [ ] `load_domain_pack()` aggregates multiple files into a `DomainPack`

### Technical Tasks

- [ ] **T0.1** Create `domain_pack_loader.py` with `CorpusSkill` and `DomainPack` frozen dataclasses → **[G-1]**
- [ ] **T0.2** Implement `extract_frontmatter()`, `parse_references()`, `parse_verification()`, `load_corpus_skill()`, `load_domain_pack()` → **[G-1]**
- [ ] **T0.3** Write 5 tests: valid frontmatter, missing delimiter, references extraction, verification extraction, full integration → **[G-1, G-7]**

### Dependencies

- None. This is the foundation sprint.

### Risks & Mitigation

- **Risk:** Frontmatter format varies between corpora. **Mitigation:** Use standard `---` delimiter (Jekyll/Hugo convention). Raise on non-standard formats rather than guessing.

### Success Metrics

- 5 tests pass
- Loader handles all corpus fixture formats from PRD section 2.5

**Exit:** 5 tests pass, `CorpusSkill` and `DomainPack` are importable.

---

## Sprint 1 — Security Policy Rules + Domain Registration

**Goal:** Register 10 precise security sub-domains with the policy normalizer so security constructs can pass normalization without tier-capping, while preserving the broad "security" guardrail.

**Scope:** SMALL (3 tasks)

### Deliverables

- [ ] `backend/services/security_policy_rules.py` — domain registration + reference extraction
- [ ] `backend/tests/test_security_policy_rules.py` — 5 tests

### Acceptance Criteria

- [ ] `register_security_domains()` adds all 10 domains to `KNOWN_PRECISE_DOMAINS` (vulnerability_analysis, attack_surface_mapping, threat_modeling, secure_code_review, incident_response, cryptographic_implementation, access_control_design, network_security, penetration_testing, compliance_auditing)
- [ ] A claim like `"vulnerability_analysis"` passes `_classify_claim()` as precise (not vague)
- [ ] A claim like `"security expert"` still tier-caps to UNVERIFIED (broad "security" stays in `KNOWN_VAGUE_TERMS`)
- [ ] `extract_security_references()` identifies ATT&CK T-codes (T[0-9]{4}), CWE-IDs (CWE-[0-9]+), OWASP refs (A[0-9]{2}:[0-9]{4})
- [ ] Reference extraction returns structured dicts with `framework`, `id`, `raw_reference` keys

### Technical Tasks

- [ ] **T1.1** Create `security_policy_rules.py` with `SECURITY_PRECISE_DOMAINS` set and `register_security_domains()` function that mutates `policy_normalizer.KNOWN_PRECISE_DOMAINS` → **[G-2, G-5]**
- [ ] **T1.2** Implement `extract_security_references()` and `classify_security_claim()` for ATT&CK/CWE/OWASP pattern matching → **[G-3]**
- [ ] **T1.3** Write 5 tests: registration count, precise domains pass, broad security stays vague, ATT&CK extraction, OWASP/CWE extraction → **[G-5, G-6, G-7]**

### Dependencies

- Sprint 0 (`CorpusSkill` dataclass used by `extract_security_references`)

### Risks & Mitigation

- **Risk:** Import-time set mutation leaks between tests. **Mitigation:** Tests snapshot and restore `KNOWN_PRECISE_DOMAINS` in setUp/tearDown.
- **Risk:** Token-level matching in `_classify_claim()` could cause false positives for compound domains. **Mitigation:** Security domains use underscored multi-word names (e.g., `vulnerability_analysis`) that won't accidentally match single tokens.

### Success Metrics

- 5 tests pass
- `KNOWN_PRECISE_DOMAINS` grows from 18 to 28 entries after registration
- Broad "security" claim still tier-caps

**Exit:** 5 tests pass, security domains registered.

---

## Sprint 2 — Security Check Planner + Anchor Mapper Extension

**Goal:** Add 5 security-specific deterministic check types and extend the anchor mapper with ATT&CK and corpus-specific rules.

**Scope:** MEDIUM (4 tasks)

### Deliverables

- [ ] `backend/services/security_check_planner.py` — 5 check types + merge logic
- [ ] 2 new rules appended to `construct_anchor_mapper.py` `_MAPPING_RULES`
- [ ] `backend/tests/test_security_check_planner.py` — 5 tests
- [ ] `backend/tests/test_security_anchor_mapping.py` — 3 tests

### Acceptance Criteria

- [ ] `SECURITY_CHECK_TYPES` dict maps 5 check types to anchor classes: ATTACK_TECHNIQUE_MAPPING→PUBLIC_STANDARD, TOOL_INVOCATION_CORRECTNESS→DETERMINISTIC_CHECK, STANDARDS_COMPLIANCE→PUBLIC_STANDARD, DEPENDENCY_VULNERABILITY_CHECK→DETERMINISTIC_CHECK, SECRET_LEAK_CHECK→DETERMINISTIC_CHECK
- [ ] `plan_security_checks()` produces `PlannedCheck` entries compatible with `check_planner.plan_checks()` output
- [ ] `merge_security_checks()` deduplicates by `check_id` and preserves `(check_type, domain, check_id)` sort order
- [ ] ATT&CK dimension → PUBLIC_STANDARD anchor with `anchor_id: attack_framework`
- [ ] Security skill dimension → PUBLIC_STANDARD anchor with `anchor_id: security_skill_corpus`
- [ ] Unrecognized security claim → `weakly_anchored=True`
- [ ] All 11 original `_MAPPING_RULES` entries preserved (no existing rules modified)

### Technical Tasks

- [ ] **T2.1** Create `security_check_planner.py` with `SECURITY_CHECK_TYPES`, `plan_security_checks()`, `merge_security_checks()` → **[G-2]**
- [ ] **T2.2** Append 2 new rules to `construct_anchor_mapper.py` `_MAPPING_RULES`: ATT&CK framework (`attack_framework`) and security skill corpus (`security_skill_corpus`) → **[G-3]**
- [ ] **T2.3** Write 5 check planner tests: ATT&CK check, tool invocation check, standards compliance check, dependency vulnerability check, merge deduplication → **[G-2, G-7]**
- [ ] **T2.4** Write 3 anchor mapping tests: ATT&CK anchor, corpus anchor, missing anchor weakly_anchored → **[G-3, G-7]**

### Dependencies

- Sprint 0 (`CorpusSkill` dataclass)
- Sprint 1 (security reference extraction)

### Risks & Mitigation

- **Risk:** ATT&CK keywords (`"attack"`, `"technique"`) match non-security dimensions. **Mitigation:** Use specific keywords (`"att_ck"`, `"mitre"`, `"t1059"`, `"t1566"`). The generic `"attack"` is acceptable in Echelon context.
- **Risk:** New check types inflate the contract model. **Mitigation:** Each maps to a real executable or standards-backed meaning. `PlannedCheck.check_type` is already a free string field — no schema pressure.

### Success Metrics

- 8 tests pass (5 planner + 3 anchor)
- `_MAPPING_RULES` grows from 11 to 13 entries
- Security checks merge cleanly with base 037 checks

**Exit:** 8 tests pass, anchor mapper extended.

---

## Sprint 3 — Integration + Regression

**Goal:** Validate the full path from corpus ingestion through contract compilation, and confirm existing 037/037b paths are unaffected.

**Scope:** SMALL (3 tasks)

### Deliverables

- [ ] `backend/tests/test_037c_regression.py` — 4 tests
- [ ] All acceptance criteria validated end-to-end

### Acceptance Criteria

- [ ] `plan_checks()` output is unchanged for non-security claims (regression)
- [ ] `normalize()` output is unchanged for non-security specs (regression)
- [ ] All 11 original `_MAPPING_RULES` entries still present and functional (regression)
- [ ] Full integration path works: corpus → domain pack → policy normalization → security checks → anchor mapping
- [ ] At least one security corpus fixture compiles into a valid contract with security check types and anchors

### Technical Tasks

- [ ] **T3.1** Write 3 regression tests: base `plan_checks()` unchanged, base `normalize()` unchanged, original anchor rules preserved → **[G-6, G-7]**
- [ ] **T3.2** Write 1 integration test: security corpus fixture → full path through all new services → valid contract output → **[G-4, G-7]**
- [ ] **T3.3** E2E Goal Validation: verify all 7 acceptance criteria from PRD section 5 → **[G-1 through G-7]**

### Dependencies

- Sprints 0, 1, 2 (all new services)

### Risks & Mitigation

- **Risk:** Import order of `security_policy_rules` affects test isolation. **Mitigation:** Regression tests run normalization both before and after security domain registration to prove base behavior is preserved.

### Success Metrics

- 4 tests pass
- Total across all sprints: ≥20 tests (PRD requirement)
- Zero regression in existing 037/037b test suites

**Exit:** 4 tests pass, ≥22 total tests across cycle.

---

## Sprint Summary

| Sprint | Focus | New Files | Tests |
|---|---|---|---|
| 0 | Domain pack loader | `domain_pack_loader.py` | 5 |
| 1 | Security policy rules | `security_policy_rules.py` | 5 |
| 2 | Security check planner + anchor mapper | `security_check_planner.py` + anchor mapper edit | 8 |
| 3 | Integration + regression | regression test file | 4 |
| **Total** | | **3 new + 1 edited** | **~22** |

---

## Appendix A: PRD Goal Mapping

| Goal ID | Goal | Contributing Tasks |
|---|---|---|
| G-1 | Frontmatter-aware corpora can be ingested as domain-pack sources | T0.1, T0.2, T0.3, T3.3 |
| G-2 | Security-specific deterministic check families supported by planner (5 new check_types) | T1.1, T2.1, T2.3, T3.3 |
| G-3 | ATT&CK / OWASP / CWE anchors can be attached to security claims | T1.2, T2.2, T2.4, T3.3 |
| G-4 | At least one security corpus fixture compiles into a valid contract | T3.2, T3.3 |
| G-5 | Precise security domains pass policy normalization without tier-capping | T1.1, T1.3, T3.3 |
| G-6 | Broad "security" claims remain vague (guardrail preserved) | T1.3, T3.1, T3.3 |
| G-7 | Existing 037/037b paths are unaffected (regression) + ≥20 new tests | T0.3, T1.3, T2.3, T2.4, T3.1, T3.2, T3.3 |
