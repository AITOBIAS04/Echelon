"""Tests for Evidence Envelope — append-only evidence container."""

from backend.investigation.evidence_envelope import EvidenceEnvelope, RedactionEvent
from backend.investigation.models import ProvenanceClass


def _make_envelope_with_items(n: int = 1) -> EvidenceEnvelope:
    """Helper: create an envelope with N items."""
    envelope = EvidenceEnvelope()
    for i in range(n):
        envelope.submit(
            content=f"content-{i}".encode(),
            provenance_class=ProvenanceClass.PUBLIC_PRIMARY,
            content_type="text/plain",
            source_description=f"test source {i}",
        )
    return envelope


class TestSubmitAndRetrieve:
    def test_submit_and_retrieve(self):
        envelope = EvidenceEnvelope()
        item = envelope.submit(
            content=b"test document content",
            provenance_class=ProvenanceClass.PUBLIC_PRIMARY,
            content_type="application/pdf",
            source_description="UK Companies House",
        )

        assert item.evidence_id == "E001"
        assert len(item.content_hash) == 64  # SHA-256 hex
        assert item.provenance_class == ProvenanceClass.PUBLIC_PRIMARY
        assert item.content_type == "application/pdf"

        retrieved = envelope.get_item("E001")
        assert retrieved is not None
        assert retrieved.evidence_id == item.evidence_id
        assert retrieved.content_hash == item.content_hash

    def test_append_only(self):
        envelope = _make_envelope_with_items(3)
        ids = [item.evidence_id for item in envelope.items]
        assert ids == ["E001", "E002", "E003"]
        assert not hasattr(envelope, "delete")

    def test_provenance_summary(self):
        envelope = EvidenceEnvelope()
        envelope.submit(b"a", ProvenanceClass.PUBLIC_PRIMARY, "text/plain", "src")
        envelope.submit(b"b", ProvenanceClass.PUBLIC_PRIMARY, "text/plain", "src")
        envelope.submit(b"c", ProvenanceClass.PRIVATE_LEAK, "text/plain", "src")
        envelope.submit(b"d", ProvenanceClass.ANALYST_DERIVED, "text/plain", "src")

        summary = envelope.provenance_summary
        assert summary["public_primary"] == 2
        assert summary["private_leak"] == 1
        assert summary["analyst_derived"] == 1
        assert "public_secondary" not in summary


class TestEnvelopeHash:
    def test_envelope_hash_deterministic(self):
        e1 = EvidenceEnvelope()
        e2 = EvidenceEnvelope()

        for env in (e1, e2):
            env.submit(b"doc1", ProvenanceClass.PUBLIC_PRIMARY, "text/plain", "src")
            env.submit(b"doc2", ProvenanceClass.PUBLIC_SECONDARY, "text/plain", "src")

        assert e1.compute_envelope_hash() == e2.compute_envelope_hash()

    def test_envelope_hash_changes_on_new_item(self):
        envelope = _make_envelope_with_items(2)
        hash_before = envelope.compute_envelope_hash()

        envelope.submit(b"new-item", ProvenanceClass.PUBLIC_PRIMARY, "text/plain", "s")
        hash_after = envelope.compute_envelope_hash()

        assert hash_before != hash_after


class TestRedaction:
    def test_redaction_preserves_hash(self):
        envelope = _make_envelope_with_items(3)
        hash_before = envelope.compute_envelope_hash()

        envelope.redact("E002", "accidental_secret")
        hash_after = envelope.compute_envelope_hash()

        assert hash_before == hash_after

    def test_redaction_logged(self):
        envelope = _make_envelope_with_items(1)
        event = envelope.redact("E001", "doxxing")

        assert isinstance(event, RedactionEvent)
        assert event.redaction_id == "R001"
        assert event.evidence_id == "E001"
        assert event.reason_class == "doxxing"
        assert event.redacted_at is not None

        assert len(envelope.redactions) == 1


class TestManifest:
    def test_manifest_format(self):
        envelope = EvidenceEnvelope()
        envelope.submit(b"doc1", ProvenanceClass.PUBLIC_PRIMARY, "text/plain", "src")
        envelope.redact("E001", "copyright")

        manifest = envelope.get_manifest()

        assert manifest["item_count"] == 1
        assert manifest["redaction_count"] == 1
        assert "envelope_hash" in manifest
        assert len(manifest["envelope_hash"]) == 64
        assert "provenance_summary" in manifest
        assert len(manifest["items"]) == 1
        assert manifest["items"][0]["redacted"] is True
        assert len(manifest["redactions"]) == 1
