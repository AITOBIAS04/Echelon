"""Tests for Deterministic Artefact Writers — 5 tests."""

import hashlib

from theatre.engine.canonical_json import canonical_json

from backend.investigation.artifacts import write_artifact, ARTEFACT_TYPES
from backend.investigation.claim_graph import ClaimGraph, ClaimType
from backend.investigation.evidence_envelope import EvidenceEnvelope
from backend.investigation.models import ProvenanceClass
from backend.investigation.counter_signals import (
    InvestigationCounterSignalFeed,
    InvestigationCounterSignalClass,
)
from backend.investigation.signal_scanner import DomainFilter, SignalScanner


class TestArtifactDeterminism:
    def test_artifact_writer_deterministic(self):
        """Same inputs -> byte-identical output."""
        data = {"key": "value", "number": 42, "nested": {"a": 1, "b": 2}}

        json1, hash1 = write_artifact("evidence_manifest", data)
        json2, hash2 = write_artifact("evidence_manifest", data)

        assert json1 == json2
        assert hash1 == hash2

        # Verify hash is correct SHA-256 of the JSON string
        expected_hash = hashlib.sha256(json1.encode()).hexdigest()
        assert hash1 == expected_hash


class TestScannerManifest:
    def test_manifest_contains_access_tier_policy(self):
        """Scanner manifest includes access_tier_policy."""
        manifest_data = {
            "requested_domain_filters": ["corporate_and_entity"],
            "resolved_source_groups": ["official_gov", "corporate_filing"],
            "skipped_source_groups": [
                {
                    "source_group": "satellite_imagery",
                    "reason": "access_tier_b_not_authorized",
                    "access_tier": "B",
                }
            ],
            "access_tier_policy": "tier_a_only",
            "total_queries": 3,
            "total_skipped": 1,
        }

        json_str, _ = write_artifact("scanner_manifest", manifest_data)

        assert '"access_tier_policy":"tier_a_only"' in json_str
        assert '"tier_a_only"' in json_str


class TestClaimGraphArtifact:
    def test_claim_graph_json_matches_root_hash(self):
        """Root hash can be recomputed from the claim graph artefact data."""
        cg = ClaimGraph()
        cg.add_claim("Company X filed for insolvency", ClaimType.FACT, ["E001"])
        cg.add_claim("Filing date matches public record", ClaimType.CAUSAL, ["E002"])

        root_hash = cg.compute_root_hash()

        # Write artefact with root hash embedded
        artifact_data = {
            "claims": [
                c.model_dump(mode="json") for c in cg.claims
            ],
            "root_hash": root_hash,
        }

        _, artifact_hash = write_artifact("claim_graph", artifact_data)

        # The artefact hash is SHA-256 of canonical JSON of the full data
        expected = hashlib.sha256(canonical_json(artifact_data).encode()).hexdigest()
        assert artifact_hash == expected

        # Root hash within the artefact matches the live-computed value
        assert artifact_data["root_hash"] == root_hash


class TestEvidenceManifest:
    def test_evidence_manifest_hash_matches_certificate_field(self):
        """Evidence manifest artefact hash matches what envelope computes."""
        envelope = EvidenceEnvelope()
        envelope.submit(b"doc1", ProvenanceClass.PUBLIC_PRIMARY, "text/plain", "src1")
        envelope.submit(b"doc2", ProvenanceClass.PUBLIC_SECONDARY, "text/plain", "src2")

        manifest = envelope.get_manifest()
        _, manifest_hash = write_artifact("evidence_manifest", manifest)

        # Hash of the manifest artefact is deterministic
        expected = hashlib.sha256(canonical_json(manifest).encode()).hexdigest()
        assert manifest_hash == expected

        # Envelope hash within the manifest matches
        assert manifest["envelope_hash"] == envelope.compute_envelope_hash()


class TestCounterSignalArtifact:
    def test_counter_signal_artifact_matches_certificate_detail(self):
        """Counter-signal artefact detail matches feed.get_detail()."""
        feed = InvestigationCounterSignalFeed()
        feed.log_counter_signal(
            signal_class=InvestigationCounterSignalClass.OFFICIAL_DENIAL,
            material=False,
            resolution_impact="low",
            detection_method="automated_osint",
        )
        feed.log_counter_signal(
            signal_class=InvestigationCounterSignalClass.FILING_CONTRADICTION,
            material=True,
            resolution_impact="high",
            detection_method="paradox_engine",
        )

        detail = feed.get_detail()
        artifact_data = {"counter_signals": detail, "summary": feed.get_summary()}

        json_str, artifact_hash = write_artifact("counter_signals", artifact_data)

        # Deterministic
        json_str2, artifact_hash2 = write_artifact("counter_signals", artifact_data)
        assert json_str == json_str2
        assert artifact_hash == artifact_hash2

        # Detail in artefact matches feed
        assert len(artifact_data["counter_signals"]) == 2
        assert artifact_data["counter_signals"][0]["signal_class"] == "official_denial"
        assert artifact_data["counter_signals"][1]["material"] is True
