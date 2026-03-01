"""
Certificate generator — assembles a CalibrationCertificate from pipeline output.

Takes the OracleOutput (collection + corroboration + scoring) plus the
evidence manifest hash and theatre commitment hash, and produces an
immutable calibration certificate.

No business logic here — all scoring and evaluation happened in earlier
pipeline stages. This is pure assembly.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from osint_pipeline.models.certificate import CalibrationCertificate
from osint_pipeline.models.oracle_output import OracleOutput


class CertificateGenerator:
    """Generate a CalibrationCertificate from completed pipeline output."""

    def generate(
        self,
        oracle_output: OracleOutput,
        manifest_hash: str,
        commitment_hash: str,
        target_entity: dict[str, Any],
        theatre_id: str = "inspection_corporate_status_v1",
        inquiry_class: str = "INSPECTION",
        execution_path: str = "replay",
        pipeline_version: str = "0.6.0",
    ) -> CalibrationCertificate:
        """Assemble certificate from oracle output and evidence hashes.

        Args:
            oracle_output: Completed three-stage pipeline output.
            manifest_hash: SHA-256 of canonical evidence manifest JSON.
            commitment_hash: SHA-256 of canonical theatre template JSON.
            target_entity: Entity under verification (company_number, etc.).
            theatre_id: Theatre template identifier.
            inquiry_class: INSPECTION, INVESTIGATION, or AUDIT.
            execution_path: replay or market.
            pipeline_version: Software version string.

        Returns:
            Fully populated CalibrationCertificate.
        """
        collection = oracle_output.collection

        # Count corroboration results
        corroboration_met = any(
            cr.passed for cr in oracle_output.corroboration_results
        )

        # Count counter-signals
        cs_checked = sum(
            1 for cs in oracle_output.counter_signal_results if cs.checked
        )
        cs_found = sum(
            1 for cs in oracle_output.counter_signal_results if cs.signal_found
        )

        return CalibrationCertificate(
            certificate_id=str(uuid.uuid4()),
            certificate_version="1.0.0",
            theatre_id=theatre_id,
            inquiry_class=inquiry_class,
            execution_path=execution_path,
            verification_tier="UNVERIFIED",
            composite_score=oracle_output.composite_score,
            all_criteria_passed=oracle_output.all_criteria_passed,
            criterion_scores=oracle_output.criterion_scores,
            evidence_bundle_hash=manifest_hash,
            commitment_hash=commitment_hash,
            sources_queried=collection.total_sources_attempted,
            sources_succeeded=collection.total_sources_succeeded,
            sources_failed=collection.total_sources_failed,
            distinct_upstream_count=collection.distinct_upstream_count,
            corroboration_met=corroboration_met,
            counter_signals_checked=cs_checked,
            counter_signals_found=cs_found,
            issued_at=datetime.now(timezone.utc),
            oracle_id=oracle_output.oracle_id,
            target_entity=target_entity,
            pipeline_version=pipeline_version,
        )
