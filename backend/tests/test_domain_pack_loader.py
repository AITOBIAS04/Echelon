"""Tests for DomainPackLoader — frontmatter-aware corpus ingestion.

Cycle 037c: Security + Domain Pack Verification.
"""

import pytest

from backend.services.domain_pack_loader import (
    CorpusSkill,
    DomainPack,
    extract_frontmatter,
    load_corpus_skill,
    load_domain_pack,
    parse_references,
    parse_verification,
)


# ── Fixtures ────────────────────────────────────────────────────────

VALID_CORPUS = """\
---
name: Vulnerability Analysis
description: Identify and classify security vulnerabilities
domain: vulnerability_analysis
category: security
tags:
  - owasp
  - cwe
---

# Vulnerability Analysis Workflow

Analyze target systems for known vulnerability patterns.

## References

- CWE-79: Cross-site Scripting (XSS)
- OWASP A03:2021 Injection
- T1059.001 PowerShell execution

## Verification

1. Confirm all identified CVEs are valid
2. Verify CVSS scores match NVD database
3. Check remediation steps are actionable

## Notes

Additional context here.
"""

MINIMAL_CORPUS = """\
---
name: Basic Skill
description: A minimal skill
domain: testing
---

Some workflow body.
"""

NO_FRONTMATTER = """\
# Just Markdown

No frontmatter here.
"""


# ── Test: extract_frontmatter ───────────────────────────────────────


class TestExtractFrontmatter:
    def test_valid_frontmatter(self):
        """Parses valid YAML frontmatter and returns dict + body."""
        fm, body = extract_frontmatter(VALID_CORPUS)

        assert isinstance(fm, dict)
        assert fm["name"] == "Vulnerability Analysis"
        assert fm["domain"] == "vulnerability_analysis"
        assert fm["tags"] == ["owasp", "cwe"]
        assert "# Vulnerability Analysis Workflow" in body
        assert "---" not in body.split("\n")[0]  # No delimiter in body

    def test_missing_delimiter_raises(self):
        """Raises ValueError when content lacks '---' delimiter."""
        with pytest.raises(ValueError, match="Missing frontmatter delimiter"):
            extract_frontmatter(NO_FRONTMATTER)

    def test_minimal_frontmatter(self):
        """Parses minimal frontmatter with just required fields."""
        fm, body = extract_frontmatter(MINIMAL_CORPUS)

        assert fm["name"] == "Basic Skill"
        assert fm["domain"] == "testing"
        assert "Some workflow body." in body


# ── Test: parse_references ──────────────────────────────────────────


class TestParseReferences:
    def test_extracts_references(self):
        """Extracts ATT&CK/CWE/OWASP references from References section."""
        _, body = extract_frontmatter(VALID_CORPUS)
        refs = parse_references(body)

        assert len(refs) == 3
        assert "CWE-79: Cross-site Scripting (XSS)" in refs
        assert "OWASP A03:2021 Injection" in refs
        assert "T1059.001 PowerShell execution" in refs

    def test_no_references_section(self):
        """Returns empty list when no References section exists."""
        refs = parse_references("# Just a heading\n\nSome content.")
        assert refs == []


# ── Test: parse_verification ────────────────────────────────────────


class TestParseVerification:
    def test_extracts_verification_steps(self):
        """Extracts testable assertions from Verification section."""
        _, body = extract_frontmatter(VALID_CORPUS)
        steps = parse_verification(body)

        assert len(steps) == 3
        assert "Confirm all identified CVEs are valid" in steps
        assert "Verify CVSS scores match NVD database" in steps
        assert "Check remediation steps are actionable" in steps

    def test_no_verification_section(self):
        """Returns empty list when no Verification section exists."""
        steps = parse_verification("# Heading\n\nContent only.")
        assert steps == []


# ── Test: load_corpus_skill (integration) ───────────────────────────


class TestLoadCorpusSkill:
    def test_full_integration(self):
        """Full parse of frontmatter + references + verification."""
        skill = load_corpus_skill(VALID_CORPUS)

        assert isinstance(skill, CorpusSkill)
        assert skill.name == "Vulnerability Analysis"
        assert skill.domain == "vulnerability_analysis"
        assert skill.description == "Identify and classify security vulnerabilities"
        assert len(skill.references) == 3
        assert len(skill.verification_steps) == 3
        assert "# Vulnerability Analysis Workflow" in skill.workflow_body
        assert skill.raw_frontmatter["tags"] == ["owasp", "cwe"]

    def test_missing_name_raises(self):
        """Raises ValueError when frontmatter lacks name/title."""
        content = "---\ndomain: test\n---\nBody."
        with pytest.raises(ValueError, match="must contain 'name' or 'title'"):
            load_corpus_skill(content)


# ── Test: load_domain_pack ──────────────────────────────────────────


class TestLoadDomainPack:
    def test_loads_multiple_skills(self):
        """Aggregates multiple corpus files into a DomainPack."""
        pack = load_domain_pack(
            pack_id="security-v1",
            domain="security",
            contents=[VALID_CORPUS, MINIMAL_CORPUS],
            version="1.0.0",
        )

        assert isinstance(pack, DomainPack)
        assert pack.pack_id == "security-v1"
        assert pack.domain == "security"
        assert len(pack.skills) == 2
        assert pack.skills[0].name == "Vulnerability Analysis"
        assert pack.skills[1].name == "Basic Skill"
        assert pack.version == "1.0.0"
