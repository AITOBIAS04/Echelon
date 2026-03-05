"""Tests for Entity Resolver — multi-source entity profiles with provenance."""

import hashlib
import re

from theatre.engine.canonical_json import canonical_json

from backend.investigation.entity_resolver import (
    EntityProfile,
    EntityQuery,
    EntityResolver,
)


class TestResolveCompaniesHouse:
    def test_resolve_companies_house(self):
        resolver = EntityResolver()
        query = EntityQuery(
            entity_name="Acme Holdings Ltd",
            jurisdiction="UK",
            registration_number="12345678",
        )

        profile = resolver.resolve(query)

        assert profile.entity_id.startswith("ENT-") and len(profile.entity_id) == 16
        assert profile.entity_name == "Acme Holdings Ltd"
        assert profile.jurisdiction == "UK"
        assert profile.registration_number == "12345678"
        assert profile.incorporation_date is not None
        assert profile.registered_address is not None
        assert len(profile.directors) > 0
        assert len(profile.source_queries) == 2  # CH + LG
        assert isinstance(profile, EntityProfile)


class TestProfileHash:
    def test_profile_hash_deterministic(self):
        resolver1 = EntityResolver()
        resolver2 = EntityResolver()

        query = EntityQuery(
            entity_name="Test Corp",
            jurisdiction="UK",
            registration_number="99999999",
        )

        profile1 = resolver1.resolve(query)
        profile2 = resolver2.resolve(query)

        assert profile1.profile_hash == profile2.profile_hash
        assert len(profile1.profile_hash) == 64  # SHA-256 hex


class TestSourceQueryRecord:
    def test_source_query_record(self):
        resolver = EntityResolver()
        query = EntityQuery(
            entity_name="Record Test Ltd",
            jurisdiction="UK",
            registration_number="11111111",
        )

        profile = resolver.resolve(query)

        # Check Companies House source
        ch_query = profile.source_queries[0]
        assert ch_query.source_id == "CH001"
        assert ch_query.source_name == "Companies House"
        assert ch_query.result_found is True
        assert "registration_number" in ch_query.fields_populated

        # Check London Gazette source
        lg_query = profile.source_queries[1]
        assert lg_query.source_id == "LG001"
        assert lg_query.source_name == "London Gazette"
        assert lg_query.result_found is True
        assert "gazette_notices" in lg_query.fields_populated


class TestUnknownEntity:
    def test_unknown_entity(self):
        resolver = EntityResolver()
        query = EntityQuery(
            entity_name="Unknown Entity XYZ",
            jurisdiction="UK",
            # No registration_number — CH cannot find it
        )

        profile = resolver.resolve(query)

        assert profile.entity_name == "Unknown Entity XYZ"
        assert profile.registration_number is None
        assert profile.incorporation_date is None
        assert profile.registered_address is None
        assert profile.directors == []
        assert profile.filing_history_summary == []
        # London Gazette still returns results
        assert len(profile.gazette_notices) > 0
        # CH source reports not found
        ch_query = profile.source_queries[0]
        assert ch_query.result_found is False
        assert ch_query.fields_populated == []


class TestEntityIdDeterminism:
    def test_same_instance_same_query_same_id_and_hash(self):
        resolver = EntityResolver()
        query = EntityQuery(
            entity_name="Idempotent Corp",
            jurisdiction="UK",
            registration_number="55555555",
        )
        profile1 = resolver.resolve(query)
        profile2 = resolver.resolve(query)
        assert profile1.entity_id == profile2.entity_id
        assert profile1.profile_hash == profile2.profile_hash

    def test_different_query_different_entity_id(self):
        resolver = EntityResolver()
        q1 = EntityQuery(entity_name="Alpha Ltd", jurisdiction="UK")
        q2 = EntityQuery(entity_name="Beta Ltd", jurisdiction="UK")
        p1 = resolver.resolve(q1)
        p2 = resolver.resolve(q2)
        assert p1.entity_id != p2.entity_id

    def test_entity_id_format(self):
        resolver = EntityResolver()
        query = EntityQuery(
            entity_name="Format Test Ltd",
            jurisdiction="UK",
            registration_number="77777777",
        )
        profile = resolver.resolve(query)
        assert re.match(r"^ENT-[0-9a-f]{12}$", profile.entity_id)
