"""Sponsor Delivery Package -- assembles final delivery for sponsors.

Bundles the calibration certificate, evidence bundle, RLMF export,
and commitment hash into a single SponsorDeliveryPackage.

Cycle-012, Sprint 2 -- Task 5.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from backend.services.certificate_pipeline import (
    CalibrationCertificate,
    CertificatePipeline,
)
from backend.services.rlmf_export import RLMFExport
from backend.services.theatre_evidence import EvidenceSnapshot


@dataclass
class SponsorDeliveryPackage:
    """Final delivery package for the sponsor after settlement."""

    theatre_id: str
    certificate: dict[str, Any]
    evidence_bundle: dict[str, Any]
    rlmf_export: dict[str, Any]
    commitment_hash: str
    echelon_status_url: str


class SponsorDeliveryAssembler:
    """Assembles the final delivery for the sponsor.

    Serialises certificate, evidence, and RLMF export into
    a single SponsorDeliveryPackage.
    """

    def assemble(
        self,
        theatre_id: str,
        certificate: CalibrationCertificate,
        evidence_snapshots: list[EvidenceSnapshot],
        rlmf_export: RLMFExport,
        commitment_hash: str,
        source_manifest: dict[str, Any],
    ) -> SponsorDeliveryPackage:
        """Assemble the sponsor delivery package.

        1. Serialise certificate to dict
        2. Build evidence bundle artefact
        3. Serialise RLMF export to dict
        4. Include commitment hash
        5. Build echelon_status endpoint URL
        """
        # 1. Certificate dict
        cert_dict = CertificatePipeline.certificate_to_dict(certificate)

        # 2. Evidence bundle artefact
        evidence_bundle = self._build_evidence_artefact(
            evidence_snapshots, source_manifest
        )

        # 3. RLMF export dict
        rlmf_dict = self._rlmf_to_dict(rlmf_export)

        # 4. echelon_status URL
        echelon_status_url = f"echelon://status/{theatre_id}"

        return SponsorDeliveryPackage(
            theatre_id=theatre_id,
            certificate=cert_dict,
            evidence_bundle=evidence_bundle,
            rlmf_export=rlmf_dict,
            commitment_hash=commitment_hash,
            echelon_status_url=echelon_status_url,
        )

    @staticmethod
    def _build_evidence_artefact(
        snapshots: list[EvidenceSnapshot],
        source_manifest: dict[str, Any],
    ) -> dict[str, Any]:
        """Build evidence bundle artefact from collection snapshots.

        Includes: source_manifest, collection_timestamps, http_receipts,
        evidence_bundle_count, source_coverage.
        """
        collection_timestamps: list[str] = []
        http_receipts: list[dict[str, Any]] = []
        total_bundles = 0

        for snapshot in snapshots:
            collection_timestamps.append(snapshot.collection_timestamp)
            total_bundles += len(snapshot.evidence_bundles)

            # Extract HTTP receipts from evidence bundles
            for bundle in snapshot.evidence_bundles:
                if hasattr(bundle, 'receipt'):
                    receipt = bundle.receipt
                    http_receipts.append({
                        "source_id": bundle.source_id,
                        "timestamp": str(receipt.timestamp),
                        "content_hash": receipt.content_hash,
                        "http_status": receipt.http_status,
                    })

        # Latest coverage
        latest_coverage = snapshots[-1].source_coverage_pct if snapshots else 0.0

        return {
            "source_manifest": source_manifest,
            "collection_timestamps": collection_timestamps,
            "http_receipts": http_receipts,
            "evidence_bundle_count": total_bundles,
            "source_coverage_pct": latest_coverage,
            "snapshot_count": len(snapshots),
        }

    @staticmethod
    def _rlmf_to_dict(rlmf: RLMFExport) -> dict[str, Any]:
        """Convert RLMFExport to a JSON-serialisable dict."""
        return {
            "schema_version": rlmf.schema_version,
            "oracle_output_id": rlmf.oracle_output_id,
            "theatre_id": rlmf.theatre_id,
            "question": rlmf.question,
            "outcome_labels": rlmf.outcome_labels,
            "winning_outcome": rlmf.winning_outcome,
            "winning_outcome_label": rlmf.winning_outcome_label,
            "epochs": rlmf.epochs,
            "agent_traces": rlmf.agent_traces,
            "calibration": rlmf.calibration,
            "agent_pnl": rlmf.agent_pnl,
            "composite_score": rlmf.composite_score,
            "evidence_bundle_hash": rlmf.evidence_bundle_hash,
            "settlement_hash": rlmf.settlement_hash,
            "exported_at": rlmf.exported_at,
        }
