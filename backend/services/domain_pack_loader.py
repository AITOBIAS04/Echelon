"""DomainPackLoader — Frontmatter-aware corpus ingestion for domain packs.

Cycle 037c: Security + Domain Pack Verification.

Parses YAML frontmatter + Markdown body from corpus files, extracting
references and verification sections. Generic loader — not security-specific.
Security interpretation lives in security_policy_rules.py.

Does NOT perform filesystem I/O. All functions accept string content.
"""

import re
from dataclasses import dataclass, field

import yaml


@dataclass(frozen=True)
class CorpusSkill:
    """A single skill parsed from a frontmatter-aware corpus file."""

    name: str
    description: str
    domain: str
    references: list[str]
    verification_steps: list[str]
    workflow_body: str
    raw_frontmatter: dict


@dataclass(frozen=True)
class DomainPack:
    """Collection of corpus skills forming a domain pack."""

    pack_id: str
    domain: str
    skills: list[CorpusSkill]
    version: str


def extract_frontmatter(content: str) -> tuple[dict, str]:
    """Split YAML frontmatter from Markdown body.

    Expects content starting with '---' delimiter. The frontmatter block
    ends at the next '---' line.

    Returns:
        Tuple of (frontmatter_dict, markdown_body).

    Raises:
        ValueError: If frontmatter delimiter is missing or YAML is invalid.
    """
    stripped = content.lstrip()
    if not stripped.startswith("---"):
        raise ValueError("Missing frontmatter delimiter: content must start with '---'")

    # Find the closing delimiter
    end_match = re.search(r"\n---\s*\n", stripped[3:])
    if end_match is None:
        # Try end-of-string delimiter
        end_match = re.search(r"\n---\s*$", stripped[3:])
        if end_match is None:
            raise ValueError("Missing closing frontmatter delimiter '---'")

    frontmatter_text = stripped[3 : 3 + end_match.start()]
    body_start = 3 + end_match.end()
    body = stripped[body_start:] if body_start < len(stripped) else ""

    try:
        parsed = yaml.safe_load(frontmatter_text)
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML in frontmatter: {e}") from e

    if parsed is None:
        parsed = {}
    if not isinstance(parsed, dict):
        raise ValueError("Frontmatter must be a YAML mapping")

    return parsed, body.strip()


def parse_references(body: str) -> list[str]:
    """Extract framework references from Markdown body.

    Scans for a '## References' section (case-insensitive) and extracts
    list items or lines until the next heading or end of content.

    Returns:
        List of extracted reference strings.
    """
    pattern = r"(?:^|\n)##\s+[Rr]eferences?\s*\n"
    match = re.search(pattern, body)
    if match is None:
        return []

    section_start = match.end()
    # Find the next heading or end
    next_heading = re.search(r"\n##\s+", body[section_start:])
    section_end = section_start + next_heading.start() if next_heading else len(body)
    section_text = body[section_start:section_end].strip()

    refs = []
    for line in section_text.split("\n"):
        line = line.strip()
        # Strip list markers
        line = re.sub(r"^[-*]\s+", "", line)
        if line:
            refs.append(line)

    return refs


def parse_verification(body: str) -> list[str]:
    """Extract testable assertions from Markdown verification section.

    Scans for a '## Verification' section (case-insensitive) and extracts
    list items or lines.

    Returns:
        List of verification step strings.
    """
    pattern = r"(?:^|\n)##\s+[Vv]erification\s*\n"
    match = re.search(pattern, body)
    if match is None:
        return []

    section_start = match.end()
    next_heading = re.search(r"\n##\s+", body[section_start:])
    section_end = section_start + next_heading.start() if next_heading else len(body)
    section_text = body[section_start:section_end].strip()

    steps = []
    for line in section_text.split("\n"):
        line = line.strip()
        line = re.sub(r"^[-*]\s+", "", line)
        # Strip numbered list markers
        line = re.sub(r"^\d+\.\s+", "", line)
        if line:
            steps.append(line)

    return steps


def load_corpus_skill(content: str) -> CorpusSkill:
    """Parse a single frontmatter-aware corpus file into a CorpusSkill.

    Extracts frontmatter metadata, references, and verification steps.

    Args:
        content: Raw file content with YAML frontmatter + Markdown body.

    Returns:
        Populated CorpusSkill instance.

    Raises:
        ValueError: On invalid frontmatter or missing required fields.
    """
    frontmatter, body = extract_frontmatter(content)

    name = frontmatter.get("name", frontmatter.get("title", ""))
    if not name:
        raise ValueError("Frontmatter must contain 'name' or 'title'")

    description = frontmatter.get("description", "")
    domain = frontmatter.get("domain", frontmatter.get("category", ""))

    references = parse_references(body)
    verification_steps = parse_verification(body)

    return CorpusSkill(
        name=str(name),
        description=str(description),
        domain=str(domain),
        references=references,
        verification_steps=verification_steps,
        workflow_body=body,
        raw_frontmatter=frontmatter,
    )


def load_domain_pack(
    pack_id: str,
    domain: str,
    contents: list[str],
    version: str = "1.0.0",
) -> DomainPack:
    """Load multiple corpus file contents into a DomainPack.

    Args:
        pack_id: Identifier for the domain pack.
        domain: Domain name (e.g., 'security').
        contents: List of raw file content strings.
        version: Pack version string.

    Returns:
        DomainPack with parsed CorpusSkill entries.
    """
    skills = [load_corpus_skill(c) for c in contents]
    return DomainPack(
        pack_id=pack_id,
        domain=domain,
        skills=skills,
        version=version,
    )
