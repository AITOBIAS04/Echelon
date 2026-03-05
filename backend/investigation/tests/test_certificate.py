"""Tests for Investigation Certificate + Builder — 8 tests."""

from datetime import datetime, timezone

from backend.investigation.certificate import (
    InvestigationCertificateBuilder,
    InvestigationCertificate,
    RoutingDecision,
)
from backend.investigation.claim_graph import ClaimGraph, ClaimType, ClaimStatus
from backend.investigation.commitment_monitor import (
    CommitmentMonitor,
    DriftType,
    DriftImpact,
)
from backend.investigation.counter_signals import (
    InvestigationCounterSignalFeed,
    InvestigationCounterSignalClass,
)
from backend.investigation.evidence_envelope import EvidenceEnvelope
from backend.investigation.models import ProvenanceClass


def _make_envelope(n: int = 2) -> EvidenceEnvelope:
    """Helper: envelope with N items using mixed provenance."""
    envelope = EvidenceEnvelope()
    classes = [ProvenanceClass.PUBLIC_PRIMARY, ProvenanceClass.PUBLIC_SECONDARY]
    for i in range(n):
        envelope.submit(
            content=f"content-{i}".encode(),
            provenance_class=classes[i % len(classes)],
            content_type="text/plain",
            source_description=f"source-{i}",
        )
    return envelope


def _make_claim_graph(n: int = 2) -> ClaimGraph:
    """Helper: claim graph with N claims."""
    cg = ClaimGraph()
    for i in range(n):
        cg.add_claim(
            claim_text=f"Claim {i}",
            claim_type=ClaimType.FACT,
            evidence_refs=[f"E{i+1:03d}"],
        )
    return cg


def _build_minimal_certificate(**overrides) -> InvestigationCertificate:
    """Helper: build a certificate with minimal data, allowing overrides."""
    envelope = overrides.pop("envelope", _make_envelope())
    claim_graph = overrides.pop("claim_graph", _make_claim_graph())
    cs_feed = overrides.pop("cs_feed", InvestigationCounterSignalFeed())
    monitor = overrides.pop("monitor", CommitmentMonitor())

    builder = InvestigationCertificateBuilder()
    return builder.build(
        theatre_id=overrides.pop("theatre_id", "theatre-001"),
        construct_id=overrides.pop("construct_id", "construct-001"),
        inquiry_class=overrides.pop("inquiry_class", "INVESTIGATIVE"),
        stop_condition=overrides.pop("stop_condition", "OUTCOME_RESOLUTION"),
        stop_config=overrides.pop("stop_config", {}),
        evidence_envelope=envelope,
        claim_graph=claim_graph,
        counter_signal_feed=cs_feed,
        commitment_monitor=monitor,
    )


class TestBuildCertificate:
    def test_build_minimal_certificate(self):
        """envelope + claim graph -> valid certificate."""
        cert = _build_minimal_certificate()

        assert isinstance(cert, InvestigationCertificate)
        assert cert.certificate_id.startswith("INV-")
        assert cert.theatre_id == "theatre-001"
        assert cert.construct_id == "construct-001"
        assert cert.inquiry_class == "INVESTIGATIVE"
        assert len(cert.certificate_hash) == 64  # SHA-256 hex

    def test_certificate_includes_all_fields(self):
        """All 30+ fields present."""
        cert = _build_minimal_certificate()
        field_names = set(cert.model_fields.keys())

        required_fields = {
            "certificate_id",
            "theatre_id",
            "construct_id",
            "inquiry_class",
            "stop_condition",
            "stop_config",
            "investigation_started_at",
            "investigation_completed_at",
            "evidence_item_count",
            "evidence_redaction_count",
            "evidence_envelope_hash",
            "provenance_summary",
            "claim_count",
            "claim_status_summary",
            "claim_graph_root_hash",
            "counter_signals_checked",
            "counter_signals_gaps",
            "counter_signals_material",
            "counter_signal_detail",
            "drift_event_count",
            "has_material_drift",
            "drift_events",
            "routing_decision",
            "routing_reason",
            "certificate_hash",
            "anchoring_status",
            "anchoring_tx_hash",
            "issued_at",
            "methodology_version",
            "toolset_version",
        }

        # All required fields must be present
        assert required_fields.issubset(field_names), (
            f"Missing: {required_fields - field_names}"
        )
        # At least 30 fields
        assert len(field_names) >= 30


class TestRoutingHints:
    def test_routing_hint_material_drift(self):
        """Material drift -> REVIEW_REQUIRED."""
        monitor = CommitmentMonitor()
        monitor.log_drift(
            drift_type=DriftType.ENTITY_RESTRUCTURE,
            original_value="Corp A",
            new_value="Corp B",
            impact_assessment=DriftImpact.MATERIAL,
        )

        cert = _build_minimal_certificate(monitor=monitor)
        assert cert.routing_decision == RoutingDecision.REVIEW_REQUIRED.value
        assert cert.routing_reason == "drift_event_material"

    def test_routing_hint_material_counter_signal(self):
        """Material counter-signal -> REVIEW_REQUIRED."""
        cs_feed = InvestigationCounterSignalFeed()
        cs_feed.log_counter_signal(
            signal_class=InvestigationCounterSignalClass.OFFICIAL_DENIAL,
            material=True,
            resolution_impact="high",
            detection_method="automated_osint",
        )

        cert = _build_minimal_certificate(cs_feed=cs_feed)
        assert cert.routing_decision == RoutingDecision.REVIEW_REQUIRED.value
        assert cert.routing_reason == "counter_signal_material"

    def test_routing_hint_single_provenance(self):
        """All PUBLIC_PRIMARY -> REVIEW_REQUIRED."""
        envelope = EvidenceEnvelope()
        envelope.submit(b"a", ProvenanceClass.PUBLIC_PRIMARY, "text/plain", "src")
        envelope.submit(b"b", ProvenanceClass.PUBLIC_PRIMARY, "text/plain", "src")

        cert = _build_minimal_certificate(envelope=envelope)
        assert cert.routing_decision == RoutingDecision.REVIEW_REQUIRED.value
        assert cert.routing_reason == "single_provenance_class"

    def test_routing_hint_allowed(self):
        """Normal case -> ALLOWED."""
        cert = _build_minimal_certificate()
        assert cert.routing_decision == RoutingDecision.ALLOWED.value
        assert cert.routing_reason == "all_checks_passed"


class TestCertificateHashing:
    def test_certificate_hash_deterministic(self):
        """Same inputs -> same hashes."""
        # Build two certificates with identical inputs
        envelope1 = EvidenceEnvelope()
        envelope1.submit(b"doc1", ProvenanceClass.PUBLIC_PRIMARY, "text/plain", "src")
        envelope1.submit(b"doc2", ProvenanceClass.PUBLIC_SECONDARY, "text/plain", "src")

        envelope2 = EvidenceEnvelope()
        envelope2.submit(b"doc1", ProvenanceClass.PUBLIC_PRIMARY, "text/plain", "src")
        envelope2.submit(b"doc2", ProvenanceClass.PUBLIC_SECONDARY, "text/plain", "src")

        cg1 = ClaimGraph()
        cg1.add_claim("Claim A", ClaimType.FACT, ["E001"])

        cg2 = ClaimGraph()
        cg2.add_claim("Claim A", ClaimType.FACT, ["E001"])

        builder = InvestigationCertificateBuilder()
        started = datetime(2026, 1, 1, tzinfo=timezone.utc)

        cert1 = builder.build(
            theatre_id="t-001",
            construct_id="c-001",
            inquiry_class="INVESTIGATIVE",
            stop_condition="OUTCOME_RESOLUTION",
            stop_config={},
            evidence_envelope=envelope1,
            claim_graph=cg1,
            counter_signal_feed=InvestigationCounterSignalFeed(),
            commitment_monitor=CommitmentMonitor(),
            investigation_started_at=started,
        )

        cert2 = builder.build(
            theatre_id="t-001",
            construct_id="c-001",
            inquiry_class="INVESTIGATIVE",
            stop_condition="OUTCOME_RESOLUTION",
            stop_config={},
            evidence_envelope=envelope2,
            claim_graph=cg2,
            counter_signal_feed=InvestigationCounterSignalFeed(),
            commitment_monitor=CommitmentMonitor(),
            investigation_started_at=started,
        )

        # Same envelope hash
        assert cert1.evidence_envelope_hash == cert2.evidence_envelope_hash
        # Same claim graph root hash
        assert cert1.claim_graph_root_hash == cert2.claim_graph_root_hash
        # Same certificate hash
        assert cert1.certificate_hash == cert2.certificate_hash

    def test_provenance_summary_in_certificate(self):
        """Counts match envelope."""
        envelope = EvidenceEnvelope()
        envelope.submit(b"a", ProvenanceClass.PUBLIC_PRIMARY, "text/plain", "src")
        envelope.submit(b"b", ProvenanceClass.PUBLIC_PRIMARY, "text/plain", "src")
        envelope.submit(b"c", ProvenanceClass.PRIVATE_LEAK, "text/plain", "src")

        cert = _build_minimal_certificate(envelope=envelope)
        assert cert.provenance_summary == envelope.provenance_summary
        assert cert.provenance_summary["public_primary"] == 2
        assert cert.provenance_summary["private_leak"] == 1
