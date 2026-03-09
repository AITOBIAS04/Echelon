"""
Investigation Template Seeder — Seeds 4 genesis templates from the Echelon investigation taxonomy.

Templates:
    blank               — neutral shell, user selects everything
    corporate_due_diligence — registries, filings, legal coverage
    market_event        — event-driven evidence, fast routing
    regulatory_action   — policy, regulatory filings, formal status changes

Source derivation uses the live OSINT master registry (backend/core/osint_registry.py)
via DOMAIN_FILTER_SOURCE_GROUPS mappings — NOT backend/osint/sources.json.

Idempotent: re-seeding skips existing templates.
"""

import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.database.models import InvestigationTemplate
from backend.investigation.signal_scanner import (
    DomainFilter,
    DOMAIN_FILTER_SOURCE_GROUPS,
)

logger = logging.getLogger(__name__)

# ── Genesis Template Definitions ──

INVESTIGATION_TEMPLATES = [
    {
        "id": "blank",
        "name": "Blank Investigation",
        "description": "Start with a neutral bounded-inquiry shell and select every constraint directly.",
        "inquiry_class": "INVESTIGATIVE",
        "domain_filters": [],
        "default_stop_condition": "OUTCOME_RESOLUTION",
        "default_time_window_days": None,
        "min_corroboration_groups": 2,
    },
    {
        "id": "corporate_due_diligence",
        "name": "Corporate Due Diligence",
        "description": "Bias toward registries, filings, legal coverage, and identity/provenance checks.",
        "inquiry_class": "INSPECTION",
        "domain_filters": ["corporate_and_entity", "court_and_legal", "property_and_land"],
        "default_stop_condition": "EVIDENCE_THRESHOLD",
        "default_time_window_days": 90,
        "min_corroboration_groups": 3,
    },
    {
        "id": "market_event",
        "name": "Market Event Analysis",
        "description": "Prepare for event-driven evidence, counter-signals, and fast routing pressure.",
        "inquiry_class": "INVESTIGATIVE",
        "domain_filters": ["finance_and_markets", "geopolitical_and_conflict"],
        "default_stop_condition": "OUTCOME_RESOLUTION",
        "default_time_window_days": 30,
        "min_corroboration_groups": 2,
    },
    {
        "id": "regulatory_action",
        "name": "Regulatory Action Tracking",
        "description": "Center the investigation on policy, regulatory filings, and formal status changes.",
        "inquiry_class": "SCRUTINY",
        "domain_filters": ["corporate_and_entity", "court_and_legal"],
        "default_stop_condition": "SPONSOR_DEFINED",
        "default_time_window_days": 180,
        "min_corroboration_groups": 2,
    },
]


def _derive_source_groups(domain_filters: list[str]) -> set[str]:
    """Map domain filter strings to deduplicated OSINT source groups."""
    source_groups: set[str] = set()
    for df_str in domain_filters:
        try:
            df = DomainFilter(df_str)
        except ValueError:
            logger.warning("Unknown domain filter '%s', skipping", df_str)
            continue
        groups = DOMAIN_FILTER_SOURCE_GROUPS.get(df, [])
        source_groups.update(groups)
    return source_groups


def _derive_default_sources(domain_filters: list[str]) -> list[str]:
    """Derive default source group IDs from domain filters via DOMAIN_FILTER_SOURCE_GROUPS.

    Sources are resolved from the live OSINT master registry's source group mappings.
    Each source group in DOMAIN_FILTER_SOURCE_GROUPS represents a category of OSINT
    sources available in the registry (e.g., 'official_gov', 'market_data', 'court_filing').

    Returns sorted list of unique source group identifiers.
    """
    source_groups = _derive_source_groups(domain_filters)
    return sorted(source_groups)


def _derive_requires_legal_review(source_groups: set[str]) -> bool:
    """Derive requires_legal_review from source group policy metadata.

    Source groups that involve court filings, insolvency records, or property
    registries carry legal review requirements due to jurisdictional data
    protection constraints.
    """
    legal_review_groups = {"court_filing", "insolvency", "property_registry"}
    return bool(source_groups & legal_review_groups)


def seed_investigation_templates(session: Session) -> int:
    """Seed all 4 investigation templates. Idempotent — skips existing.

    Returns the number of newly created templates.
    """
    created = 0

    for tpl_def in INVESTIGATION_TEMPLATES:
        template_id = tpl_def["id"]

        # Check if already exists
        existing = session.get(InvestigationTemplate, template_id)
        if existing:
            logger.debug("Investigation template %s already exists, skipping", template_id)
            continue

        domain_filters = tpl_def["domain_filters"]
        source_groups = _derive_source_groups(domain_filters)
        default_sources = sorted(source_groups)
        requires_legal_review = _derive_requires_legal_review(source_groups)

        template = InvestigationTemplate(
            id=template_id,
            name=tpl_def["name"],
            description=tpl_def["description"],
            inquiry_class=tpl_def["inquiry_class"],
            domain_filters_json=domain_filters,
            default_sources_json=default_sources,
            default_stop_condition=tpl_def["default_stop_condition"],
            default_time_window_days=tpl_def["default_time_window_days"],
            requires_legal_review=requires_legal_review,
            min_corroboration_groups=tpl_def["min_corroboration_groups"],
            template_status="ACTIVE",
            is_seeded=True,
            created_at=datetime.now(timezone.utc),
        )

        session.add(template)
        created += 1

    session.commit()
    logger.info("Seeded %d new investigation templates (total in registry: 4)", created)
    return created
