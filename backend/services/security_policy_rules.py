"""SecurityPolicyRules — Security-specific domain registration and reference extraction.

Cycle 037c: Security + Domain Pack Verification.

Extends policy normalization with precise security sub-domains. Broad "security"
remains vague in KNOWN_VAGUE_TERMS. Only specific sub-domains pass.

Maps framework references (ATT&CK, CWE, OWASP) to structured dicts.
"""

import re
from typing import Optional

from backend.services.domain_pack_loader import CorpusSkill
from backend.services.policy_normalizer import KNOWN_PRECISE_DOMAINS


SECURITY_PRECISE_DOMAINS: set[str] = {
    "vulnerability_analysis",
    "attack_surface_mapping",
    "threat_modeling",
    "secure_code_review",
    "incident_response",
    "cryptographic_implementation",
    "access_control_design",
    "network_security",
    "penetration_testing",
    "compliance_auditing",
}

# Regex patterns for framework reference extraction
_ATTACK_PATTERN = re.compile(r"T\d{4}(?:\.\d{3})?")
_CWE_PATTERN = re.compile(r"CWE-\d+")
_OWASP_PATTERN = re.compile(r"A\d{2}:\d{4}")


def register_security_domains() -> int:
    """Register security-specific precise domains with the policy normalizer.

    Mutates policy_normalizer.KNOWN_PRECISE_DOMAINS by adding security domains.
    Returns count of newly added domains (for logging/testing).

    Preserves the guardrail: broad "security" remains in KNOWN_VAGUE_TERMS
    and continues to tier-cap claims. Only specific sub-domains pass.
    """
    before = len(KNOWN_PRECISE_DOMAINS)
    KNOWN_PRECISE_DOMAINS.update(SECURITY_PRECISE_DOMAINS)
    return len(KNOWN_PRECISE_DOMAINS) - before


def extract_security_references(skill: CorpusSkill) -> list[dict]:
    """Extract ATT&CK, CWE, and OWASP references from a CorpusSkill.

    Scans the skill's references list for known framework ID patterns:
    - ATT&CK: T[0-9]{4}(.[0-9]{3})?
    - CWE: CWE-[0-9]+
    - OWASP: A[0-9]{2}:[0-9]{4}

    Returns:
        List of dicts with keys: framework, id, raw_reference.
    """
    results = []

    for ref in skill.references:
        attack_match = _ATTACK_PATTERN.search(ref)
        if attack_match:
            results.append({
                "framework": "ATT&CK",
                "id": attack_match.group(),
                "raw_reference": ref,
            })

        cwe_match = _CWE_PATTERN.search(ref)
        if cwe_match:
            results.append({
                "framework": "CWE",
                "id": cwe_match.group(),
                "raw_reference": ref,
            })

        owasp_match = _OWASP_PATTERN.search(ref)
        if owasp_match:
            results.append({
                "framework": "OWASP",
                "id": owasp_match.group(),
                "raw_reference": ref,
            })

    return results


def classify_security_claim(domain: str, references: list[dict]) -> dict:
    """Classify a security domain claim with reference backing.

    A security claim with valid framework references is promoted to precise.
    A security claim without references remains vague.

    Args:
        domain: The domain claim string.
        references: Extracted framework references from extract_security_references().

    Returns:
        Dict with keys: domain, has_references, framework_count, classification.
    """
    framework_count = len(references)
    has_references = framework_count > 0

    return {
        "domain": domain,
        "has_references": has_references,
        "framework_count": framework_count,
        "classification": "reference_backed" if has_references else "unanchored",
    }


# Register security domains at import time so they are available
# to the policy normalizer immediately.
_REGISTERED_COUNT = register_security_domains()
