"""Domain filter enforcement for evidence and signal ingestion.

Pure functions — no DB access, no session parameter.
Validates that evidence/signal sources fall within committed domain filters.
"""
from __future__ import annotations

from backend.investigation.signal_scanner import DomainFilter, DOMAIN_FILTER_SOURCE_GROUPS


class DomainFilterViolation(Exception):
    """Raised when evidence/signal source is outside committed domain filters."""

    def __init__(self, source: str, allowed_sources: list[str], domain_filters: list[str]):
        self.source = source
        self.allowed_sources = allowed_sources
        self.domain_filters = domain_filters
        super().__init__(
            f"Source '{source}' is outside committed domain filters {domain_filters}. "
            f"Allowed sources: {allowed_sources}"
        )


def get_allowed_sources(domain_filters: list[str]) -> set[str]:
    """Expand domain filter enum values into the set of allowed source groups."""
    allowed: set[str] = set()
    for df_value in domain_filters:
        try:
            df = DomainFilter(df_value)
        except ValueError:
            continue
        allowed.update(DOMAIN_FILTER_SOURCE_GROUPS.get(df, []))
    return allowed


def validate_evidence_source(
    domain_filters_json: list[str],
    source_id: str,
    source_description: str = "",
) -> None:
    """Validate that evidence source falls within committed domain filters.

    No-op if domain_filters_json is empty (backward compatible).
    Raises DomainFilterViolation if source is out of scope.
    """
    if not domain_filters_json:
        return

    allowed = get_allowed_sources(domain_filters_json)
    if not allowed:
        return

    if source_id and source_id not in allowed:
        raise DomainFilterViolation(source_id, sorted(allowed), domain_filters_json)


def validate_signal_source(
    domain_filters_json: list[str],
    detection_method: str,
    source_ref: str = "",
) -> None:
    """Validate counter-signal/scanner source against domain filters.

    No-op if domain_filters_json is empty.
    Meta-methods (automated_osint, human_submitted, paradox_engine) always pass.
    Raises DomainFilterViolation if out of scope.
    """
    if not domain_filters_json:
        return

    allowed = get_allowed_sources(domain_filters_json)
    if not allowed:
        return

    source_to_check = source_ref or detection_method
    if source_to_check and source_to_check not in allowed:
        if source_to_check in ("automated_osint", "paradox_engine", "human_submitted"):
            return
        raise DomainFilterViolation(source_to_check, sorted(allowed), domain_filters_json)
