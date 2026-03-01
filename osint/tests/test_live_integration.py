"""
Integration tests for the live certificate pipeline.

Unit tests (manifest, certificate generator, verifier) run without live APIs.
Live API tests are guarded by ECHELON_SKIP_LIVE_TESTS (default: skip).

Run unit tests only:
    python tests/test_live_integration.py

Run all tests including live:
    ECHELON_SKIP_LIVE_TESTS=0 COMPANIES_HOUSE_API_KEY=xxx python tests/test_live_integration.py
"""

from __future__ import annotations

import importlib.util
import json
import os
import sys
import tempfile
import unittest
import uuid
from datetime import datetime, timezone
from pathlib import Path

# Add parent directory to path.
_tests_dir = Path(__file__).resolve().parent
_project_dir = _tests_dir.parent
if str(_project_dir) not in sys.path:
    sys.path.insert(0, str(_project_dir))

# Force-load our echelon_verify (avoids collision with other modules on sys.path).
_ev_spec = importlib.util.spec_from_file_location(
    "echelon_verify_local", _project_dir / "osint_pipeline" / "echelon_verify.py"
)
_ev_mod = importlib.util.module_from_spec(_ev_spec)
_ev_spec.loader.exec_module(_ev_mod)
_verify_fn = _ev_mod.verify

from osint_pipeline.engine.canonical import canonical_hash
from osint_pipeline.engine.certificate_generator import CertificateGenerator
from osint_pipeline.engine.manifest_builder import build_manifest, manifest_hash
from osint_pipeline.models.certificate import CalibrationCertificate
from osint_pipeline.models.evidence import (
    EvidenceBundle,
    GapReport,
    HTTPTranscriptReceipt,
    OracleCollectionSummary,
    ReceiptMode,
)
from osint_pipeline.models.oracle_output import (
    CorroborationResult,
    CounterSignalResult,
    CriterionScore,
    OracleOutput,
)

# Skip guards.
SKIP_LIVE = os.environ.get("ECHELON_SKIP_LIVE_TESTS", "1") == "1"
API_KEY = os.environ.get("COMPANIES_HOUSE_API_KEY", "")


def _dummy_receipt(url: str = "https://example.com") -> HTTPTranscriptReceipt:
    """Create a dummy receipt for testing."""
    return HTTPTranscriptReceipt(
        method="GET",
        url=url,
        request_headers={"Accept": "application/json"},
        response_status=200,
        response_body_hash="a" * 64,
        timestamp_ms=int(datetime.now(timezone.utc).timestamp() * 1000),
        receipt_hash="b" * 64,
    )


def _dummy_bundle(source_id: str = "test_source", **overrides) -> EvidenceBundle:
    """Create a dummy evidence bundle for testing."""
    defaults = dict(
        source_id=source_id,
        source_group="official_gov",
        independence_upstream_id=f"upstream_{source_id}",
        resolution_role="primary_evidence",
        jurisdiction="GB",
        raw_payload_hash="c" * 64,
        raw_payload_size_bytes=1024,
        receipt=_dummy_receipt(),
        receipt_mode=ReceiptMode.HTTP_TRANSCRIPT,
        structured_extract={"test": True},
        confidence_score=1.0,
    )
    defaults.update(overrides)
    return EvidenceBundle(**defaults)


def _dummy_oracle_output() -> OracleOutput:
    """Create a dummy OracleOutput for testing."""
    bundles = [
        _dummy_bundle("companies_house_api"),
        _dummy_bundle("london_gazette_api", resolution_role="secondary_corroboration",
                      independence_upstream_id="gb_london_gazette"),
    ]
    return OracleOutput(
        oracle_id=str(uuid.uuid4()),
        theatre_id="inspection_corporate_status_v1",
        collection=OracleCollectionSummary(
            bundles=bundles,
            total_sources_attempted=2,
            total_sources_succeeded=2,
            total_sources_failed=0,
        ),
        corroboration_results=[
            CorroborationResult(
                claim_id="claim_000",
                primary_source_id="companies_house_api",
                primary_source_group="official_gov",
                distinct_corroborating_groups=1,
                corroboration_minimum=2,
                corroborating_sources=["london_gazette_api"],
                corroborating_groups=["official_gov"],
            ),
        ],
        counter_signal_results=[
            CounterSignalResult(
                counter_signal_class="corporate_event",
                source_id="london_gazette_api",
                checked=True,
                signal_found=False,
            ),
        ],
        criterion_scores=[
            CriterionScore(criterion_id="company_exists", score=1.0, passed=True, detail="Found"),
            CriterionScore(criterion_id="company_active", score=1.0, passed=True, detail="Active"),
            CriterionScore(criterion_id="filing_current", score=1.0, passed=True, detail="Current"),
            CriterionScore(criterion_id="corroboration_met", score=1.0, passed=True, detail="Met"),
            CriterionScore(criterion_id="counter_signal_absent", score=1.0, passed=True, detail="Absent"),
        ],
        composite_score=0.9975,
        bundle_hash="d" * 64,
    )


# ═══════════════════════════════════════════════════════════
# Unit Tests (no live APIs)
# ═══════════════════════════════════════════════════════════


class TestManifestBuilder(unittest.TestCase):
    """Test evidence manifest builder."""

    def test_deterministic_hash(self):
        """Identical directory contents produce identical manifest hashes."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            (tmp_path / "a.json").write_text('{"key": "value"}')
            (tmp_path / "b.json").write_text('{"other": "data"}')

            hash1 = manifest_hash(build_manifest(tmp_path))
            hash2 = manifest_hash(build_manifest(tmp_path))
            self.assertEqual(hash1, hash2)

    def test_excludes_manifest_and_certificate(self):
        """manifest.json and certificate.json are excluded."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            (tmp_path / "data.json").write_text('{"test": true}')
            (tmp_path / "manifest.json").write_text('{}')
            (tmp_path / "certificate.json").write_text('{}')

            m = build_manifest(tmp_path)
            self.assertIn("data.json", m)
            self.assertNotIn("manifest.json", m)
            self.assertNotIn("certificate.json", m)

    def test_posix_paths(self):
        """Paths use forward slashes."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            sub = tmp_path / "sub"
            sub.mkdir()
            (sub / "file.json").write_text('{}')

            m = build_manifest(tmp_path)
            self.assertIn("sub/file.json", m)

    def test_sorted_keys(self):
        """Manifest keys are sorted."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            (tmp_path / "z.json").write_text('{}')
            (tmp_path / "a.json").write_text('{}')

            m = build_manifest(tmp_path)
            keys = list(m.keys())
            self.assertEqual(keys, sorted(keys))


class TestCertificateGenerator(unittest.TestCase):
    """Test certificate generation from OracleOutput."""

    def test_generates_valid_certificate(self):
        """Generator produces a valid CalibrationCertificate."""
        oracle = _dummy_oracle_output()
        gen = CertificateGenerator()

        cert = gen.generate(
            oracle_output=oracle,
            manifest_hash="e" * 64,
            commitment_hash="f" * 64,
            target_entity={"company_number": "00445790"},
        )

        self.assertIsInstance(cert, CalibrationCertificate)
        self.assertEqual(cert.verification_tier, "UNVERIFIED")
        self.assertEqual(cert.evidence_bundle_hash, "e" * 64)
        self.assertEqual(cert.commitment_hash, "f" * 64)
        self.assertEqual(cert.sources_queried, 2)
        self.assertEqual(cert.sources_succeeded, 2)
        self.assertTrue(cert.all_criteria_passed)
        self.assertAlmostEqual(cert.composite_score, 0.9975)

    def test_certificate_has_uuid(self):
        """Certificate ID is a valid UUID."""
        oracle = _dummy_oracle_output()
        gen = CertificateGenerator()

        cert = gen.generate(
            oracle_output=oracle,
            manifest_hash="e" * 64,
            commitment_hash="f" * 64,
            target_entity={},
        )

        # Should not raise.
        uuid.UUID(cert.certificate_id)


class TestVerifier(unittest.TestCase):
    """Test verifier against synthetic evidence."""

    def _create_evidence_dir(self, tmp_path: Path) -> tuple[Path, str]:
        """Create a valid evidence directory and return (cert_path, commitment_hash)."""
        # Create theatre template.
        template = {"template_id": "test", "version": "1.0.0"}
        commitment_hash = canonical_hash(template)

        template_path = tmp_path / "theatre_template.json"
        template_path.write_text(json.dumps(template))

        # Create some evidence files.
        inputs_dir = tmp_path / "inputs"
        inputs_dir.mkdir()
        (inputs_dir / "source_a.json").write_text('{"data": "a"}')

        receipts_dir = tmp_path / "receipts"
        receipts_dir.mkdir()
        (receipts_dir / "source_a.receipt.json").write_text('{"receipt": "r"}')

        scores_dir = tmp_path / "scores"
        scores_dir.mkdir()
        (scores_dir / "criterion_scores.json").write_text('[{"id": "c1"}]')

        # Write oracle output.
        (tmp_path / "oracle_output.json").write_text('{"oracle": true}')

        # Build manifest.
        from osint_pipeline.engine.manifest_builder import build_manifest, manifest_hash
        m = build_manifest(tmp_path)
        m_hash = manifest_hash(m)

        manifest_path = tmp_path / "manifest.json"
        manifest_path.write_text(json.dumps(m))

        # Generate certificate.
        cert = CalibrationCertificate(
            certificate_id=str(uuid.uuid4()),
            theatre_id="test",
            inquiry_class="INSPECTION",
            execution_path="replay",
            verification_tier="UNVERIFIED",
            composite_score=0.95,
            all_criteria_passed=True,
            criterion_scores=[
                CriterionScore(criterion_id="c1", score=1.0, passed=True, detail="ok"),
            ],
            evidence_bundle_hash=m_hash,
            commitment_hash=commitment_hash,
            oracle_id="test-oracle",
            target_entity={"test": True},
        )

        cert_path = tmp_path / "certificate.json"
        cert_path.write_text(json.dumps(cert.model_dump(), default=str))

        return cert_path, commitment_hash

    def test_verifier_pass(self):
        """Verifier reports PASS on valid evidence."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            cert_path, _ = self._create_evidence_dir(tmp_path)
            result = _verify_fn(cert_path, tmp_path)
            self.assertTrue(result)

    def test_verifier_fail_on_tampered_evidence(self):
        """Verifier reports FAIL when evidence is tampered."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            cert_path, _ = self._create_evidence_dir(tmp_path)

            # Tamper with an evidence file.
            tampered = tmp_path / "inputs" / "source_a.json"
            tampered.write_text('{"data": "TAMPERED"}')

            result = _verify_fn(cert_path, tmp_path)
            self.assertFalse(result)


# ═══════════════════════════════════════════════════════════
# Live API Tests (guarded)
# ═══════════════════════════════════════════════════════════


@unittest.skipIf(SKIP_LIVE, "Live API tests disabled (set ECHELON_SKIP_LIVE_TESTS=0)")
@unittest.skipIf(not API_KEY, "No COMPANIES_HOUSE_API_KEY set")
class TestLiveCompaniesHouse(unittest.TestCase):
    """Live tests against Companies House API."""

    def test_profile_live(self):
        """CH collector returns SUCCESS bundle for Tesco PLC."""
        from osint_pipeline.collectors.companies_house import CompaniesHouseCollector

        collector = CompaniesHouseCollector(config={"api_key": API_KEY})
        result = collector.collect(
            query_context={"company_number": "00445790"},
        )
        collector.close()

        self.assertTrue(result.succeeded, f"Failed: {result.error_message}")
        self.assertIn("company_name", result.bundle.structured_extract)
        self.assertEqual(
            result.bundle.structured_extract["company_status"], "active"
        )

    def test_filing_history_live(self):
        """CH filing-history returns items for Tesco PLC."""
        from osint_pipeline.collectors.companies_house import CompaniesHouseCollector

        collector = CompaniesHouseCollector(config={"api_key": API_KEY})
        result = collector.collect(
            query_context={
                "company_number": "00445790",
                "endpoint": "filing-history",
            },
        )
        collector.close()

        self.assertTrue(result.succeeded, f"Failed: {result.error_message}")
        self.assertGreater(
            result.bundle.structured_extract.get("total_count", 0), 0
        )


@unittest.skipIf(SKIP_LIVE, "Live API tests disabled (set ECHELON_SKIP_LIVE_TESTS=0)")
class TestLiveLondonGazette(unittest.TestCase):
    """Live tests against London Gazette."""

    def test_gazette_search_live(self):
        """LG collector returns a bundle for Tesco PLC."""
        from osint_pipeline.collectors.london_gazette import LondonGazetteCollector

        collector = LondonGazetteCollector()
        result = collector.collect(
            query_context={
                "company_name": "TESCO PLC",
                "notice_type": "insolvency",
            },
        )
        collector.close()

        self.assertTrue(result.succeeded, f"Failed: {result.error_message}")
        self.assertIn(
            "counter_signal_detected",
            result.bundle.structured_extract,
        )


@unittest.skipIf(SKIP_LIVE, "Live API tests disabled (set ECHELON_SKIP_LIVE_TESTS=0)")
@unittest.skipIf(not API_KEY, "No COMPANIES_HOUSE_API_KEY set")
class TestLiveEndToEnd(unittest.TestCase):
    """End-to-end live test — produces a full certificate."""

    def test_full_pipeline(self):
        """Full pipeline produces a valid certificate for Tesco PLC."""
        import argparse
        from scripts.run_live_certificate import run

        with tempfile.TemporaryDirectory() as tmp:
            args = argparse.Namespace(
                company="00445790",
                output_dir=tmp,
                api_key=API_KEY,
                theatre_template=None,
                sequential=True,
            )
            exit_code = run(args)

            # Check certificate exists.
            cert_path = Path(tmp) / "certificate.json"
            self.assertTrue(cert_path.exists(), "certificate.json not created")

            # Check verifier passes.
            self.assertEqual(exit_code, 0, "Pipeline did not return PASS")


if __name__ == "__main__":
    unittest.main(verbosity=2)
