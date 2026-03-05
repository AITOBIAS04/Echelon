"""Tests for Signal Scanner — domain-filtered OSINT scanning."""

from backend.investigation.signal_scanner import (
    DOMAIN_FILTER_SOURCE_GROUPS,
    DomainFilter,
    SignalScanner,
)


class TestDomainFilterMapping:
    def test_domain_filter_to_source_groups(self):
        scanner = SignalScanner([DomainFilter.CORPORATE_AND_ENTITY])
        groups = scanner.active_source_groups

        assert "official_gov" in groups
        assert "corporate_filing" in groups
        assert "entity_resolution" in groups
        assert len(groups) == 3

    def test_combined_filters(self):
        scanner = SignalScanner([
            DomainFilter.CORPORATE_AND_ENTITY,
            DomainFilter.COURT_AND_LEGAL,
        ])
        groups = scanner.active_source_groups

        # Corporate: official_gov, corporate_filing, entity_resolution
        # Court: court_filing, insolvency
        assert len(groups) == 5
        assert "official_gov" in groups
        assert "court_filing" in groups
        assert "insolvency" in groups
        # No duplicates
        assert len(groups) == len(set(groups))


class TestDeltaBrief:
    def test_deltabrief_hash_deterministic(self):
        scanner1 = SignalScanner([DomainFilter.PROPERTY_AND_LAND])
        scanner2 = SignalScanner([DomainFilter.PROPERTY_AND_LAND])

        brief1 = scanner1.scan("Test Company Ltd")
        brief2 = scanner2.scan("Test Company Ltd")

        # Both scanners produce the same brief_id (DB001) and same subject
        # so content hashes should be identical
        assert brief1.content_hash == brief2.content_hash

    def test_scan_with_mock_sources(self):
        scanner = SignalScanner([DomainFilter.CORPORATE_AND_ENTITY])
        brief = scanner.scan("Example Corp")

        assert brief.brief_id == "DB001"
        assert brief.domain_filters == [DomainFilter.CORPORATE_AND_ENTITY]
        assert len(brief.source_queries) == 3  # 3 source groups
        assert brief.anomalies == []
        assert len(brief.content_hash) == 64  # SHA-256 hex digest


class TestScannerManifest:
    def test_scanner_manifest_format(self):
        scanner = SignalScanner([
            DomainFilter.MARITIME,
            DomainFilter.AIRSPACE,
        ])
        brief = scanner.scan("Vessel XYZ")

        # Maritime: maritime_ais (A), geospatial_verification (A)
        # Airspace: flight_tracking (B — skipped)
        manifest = scanner._build_manifest(brief.source_queries)

        assert "requested_domain_filters" in manifest
        assert "resolved_source_groups" in manifest
        assert "skipped_source_groups" in manifest
        assert "access_tier_policy" in manifest
        assert manifest["access_tier_policy"] == "tier_a_only"
        assert manifest["total_queries"] == 3
        assert manifest["total_skipped"] >= 1  # flight_tracking is tier B

        # Verify skipped source has reason
        skipped = manifest["skipped_source_groups"]
        assert len(skipped) >= 1
        assert any(
            s["reason"] == "access_tier_b_not_authorized" for s in skipped
        )
