"""Entity Resolver — multi-source entity profiles with provenance per source."""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone

from pydantic import BaseModel, Field

from theatre.engine.canonical_json import canonical_json


class SourceQueryRecord(BaseModel):
    """Provenance record for a single source query."""

    model_config = {"frozen": True}

    source_id: str
    source_name: str
    query_time: datetime
    result_found: bool
    fields_populated: list[str]


class EntityQuery(BaseModel):
    """Query parameters for entity resolution."""

    model_config = {"frozen": True}

    entity_name: str
    jurisdiction: str
    registration_number: str | None = None


class EntityProfile(BaseModel):
    """Resolved entity profile with provenance metadata per source."""

    model_config = {"frozen": True}

    entity_id: str
    entity_name: str
    jurisdiction: str
    registration_number: str | None = None
    incorporation_date: str | None = None
    registered_address: str | None = None
    directors: list[dict] = Field(default_factory=list)
    filing_history_summary: list[dict] = Field(default_factory=list)
    gazette_notices: list[dict] = Field(default_factory=list)
    regulatory_entries: list[dict] = Field(default_factory=list)
    source_queries: list[SourceQueryRecord] = Field(default_factory=list)
    profile_hash: str = ""


class EntityResolver:
    """Stub entity resolver for Companies House + London Gazette.

    Profile hash = SHA-256 of canonical_json(profile_dict excluding profile_hash).
    """

    def __init__(self) -> None:
        self._counter: int = 0

    def resolve(self, query: EntityQuery) -> EntityProfile:
        """Stub resolver. Returns mock profile."""
        self._counter += 1
        entity_id = f"ENT{self._counter:03d}"
        now = datetime.now(timezone.utc)

        source_queries = [
            SourceQueryRecord(
                source_id="CH001",
                source_name="Companies House",
                query_time=now,
                result_found=bool(query.registration_number),
                fields_populated=(
                    [
                        "registration_number",
                        "incorporation_date",
                        "registered_address",
                        "directors",
                        "filing_history_summary",
                    ]
                    if query.registration_number
                    else []
                ),
            ),
            SourceQueryRecord(
                source_id="LG001",
                source_name="London Gazette",
                query_time=now,
                result_found=True,
                fields_populated=["gazette_notices"],
            ),
        ]

        # Build hash dict from entity data only (excludes source_queries
        # which contain non-deterministic timestamps from query operations)
        hash_dict = {
            "entity_id": entity_id,
            "entity_name": query.entity_name,
            "jurisdiction": query.jurisdiction,
            "registration_number": query.registration_number,
            "incorporation_date": (
                "2020-01-15" if query.registration_number else None
            ),
            "registered_address": (
                "1 Example Street, London, EC1A 1BB"
                if query.registration_number
                else None
            ),
            "directors": (
                [{"name": "J. Smith", "role": "Director", "appointed": "2020-01-15"}]
                if query.registration_number
                else []
            ),
            "filing_history_summary": (
                [{"type": "annual_return", "date": "2025-12-01"}]
                if query.registration_number
                else []
            ),
            "gazette_notices": [
                {"type": "incorporation", "date": "2020-01-20", "issue": "63100"}
            ],
            "regulatory_entries": [],
        }

        profile_hash = hashlib.sha256(
            canonical_json(hash_dict).encode()
        ).hexdigest()

        return EntityProfile(
            entity_id=entity_id,
            entity_name=query.entity_name,
            jurisdiction=query.jurisdiction,
            registration_number=query.registration_number,
            incorporation_date=hash_dict["incorporation_date"],
            registered_address=hash_dict["registered_address"],
            directors=hash_dict["directors"],
            filing_history_summary=hash_dict["filing_history_summary"],
            gazette_notices=hash_dict["gazette_notices"],
            regulatory_entries=[],
            source_queries=source_queries,
            profile_hash=profile_hash,
        )
