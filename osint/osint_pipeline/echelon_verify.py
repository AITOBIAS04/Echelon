#!/usr/bin/env python3
"""
Echelon Verifier CLI — independently verify a calibration certificate.

Usage:
    python echelon_verify.py verify certificate.json evidence/

Verification steps:
1. Load certificate JSON and validate against CalibrationCertificate model
2. Load evidence directory and verify it exists
3. Rebuild manifest from evidence directory (independent hash computation)
4. Check evidence_bundle_hash matches rebuilt manifest hash
5. Check commitment_hash matches canonical hash of theatre template
6. Check all criterion scores have passed=True
7. Report PASS or FAIL with diagnostics

Exit codes:
    0 = PASS
    1 = FAIL
    2 = Usage error
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Add parent directory to path for imports when run as script.
_script_dir = Path(__file__).resolve().parent
if str(_script_dir) not in sys.path:
    sys.path.insert(0, str(_script_dir))

from osint_pipeline.engine.canonical import canonical_hash
from osint_pipeline.engine.manifest_builder import build_manifest, manifest_hash
from osint_pipeline.models.certificate import CalibrationCertificate


def _print(msg: str) -> None:
    print(f"VERIFIER: {msg}")


def verify(certificate_path: Path, evidence_dir: Path) -> bool:
    """Run all verification checks. Returns True if PASS."""
    passed_checks = 0
    total_checks = 0

    # --- Check 1: Load certificate ---
    total_checks += 1
    _print(f"Loading certificate from {certificate_path}")
    try:
        with open(certificate_path, "r", encoding="utf-8") as f:
            cert_data = json.load(f)
        cert = CalibrationCertificate(**cert_data)
        _print(f"  Certificate ID: {cert.certificate_id}")
        _print(f"  Theatre: {cert.theatre_id}")
        _print(f"  Tier: {cert.verification_tier}")
        passed_checks += 1
    except Exception as e:
        _print(f"  FAIL: Invalid certificate — {e}")
        _report(passed_checks, total_checks)
        return False

    # --- Check 2: Evidence directory exists ---
    total_checks += 1
    _print(f"Loading evidence from {evidence_dir}")
    if not evidence_dir.is_dir():
        _print(f"  FAIL: Evidence directory does not exist")
        _report(passed_checks, total_checks)
        return False

    evidence_files = list(evidence_dir.rglob("*"))
    file_count = sum(1 for f in evidence_files if f.is_file())
    _print(f"  Found {file_count} files")
    if file_count == 0:
        _print(f"  FAIL: Evidence directory is empty")
        _report(passed_checks, total_checks)
        return False
    passed_checks += 1

    # --- Check 3: Rebuild manifest and check hash ---
    total_checks += 1
    _print("Rebuilding manifest...")
    rebuilt_manifest = build_manifest(evidence_dir)
    rebuilt_hash = manifest_hash(rebuilt_manifest)
    _print(f"  Rebuilt manifest: {len(rebuilt_manifest)} files")
    _print(f"  Rebuilt hash:     {rebuilt_hash[:16]}...")
    _print(f"  Certificate hash: {cert.evidence_bundle_hash[:16]}...")

    if rebuilt_hash == cert.evidence_bundle_hash:
        _print("  Manifest hash: OK")
        passed_checks += 1
    else:
        _print("  FAIL: Manifest hash mismatch — evidence has been tampered with")
        # Show diff
        stored_manifest_path = evidence_dir / "manifest.json"
        if stored_manifest_path.exists():
            with open(stored_manifest_path, "r") as f:
                stored = json.load(f)
            for key in set(list(rebuilt_manifest.keys()) + list(stored.keys())):
                r = rebuilt_manifest.get(key, "<missing>")
                s = stored.get(key, "<missing>")
                if r != s:
                    _print(f"    DIFF: {key}")
                    _print(f"      rebuilt:  {r[:16]}...")
                    _print(f"      stored:   {s[:16]}...")
        _report(passed_checks, total_checks)
        return False

    # --- Check 4: Commitment hash ---
    total_checks += 1
    _print("Checking commitment hash...")
    template_path = evidence_dir / "theatre_template.json"
    if not template_path.exists():
        _print("  FAIL: theatre_template.json not found in evidence directory")
        _report(passed_checks, total_checks)
        return False

    with open(template_path, "r", encoding="utf-8") as f:
        template_data = json.load(f)
    template_hash = canonical_hash(template_data)
    _print(f"  Template hash:    {template_hash[:16]}...")
    _print(f"  Certificate hash: {cert.commitment_hash[:16]}...")

    if template_hash == cert.commitment_hash:
        _print("  Commitment hash: OK")
        passed_checks += 1
    else:
        _print("  FAIL: Commitment hash mismatch — template has been tampered with")
        _report(passed_checks, total_checks)
        return False

    # --- Check 5: All criteria passed ---
    total_checks += 1
    criteria_count = len(cert.criterion_scores)
    criteria_passed = sum(1 for cs in cert.criterion_scores if cs.passed)
    _print(f"Criteria: {criteria_passed}/{criteria_count} passed")

    for cs in cert.criterion_scores:
        status = "PASS" if cs.passed else "FAIL"
        _print(f"  [{status}] {cs.criterion_id}: {cs.detail}")

    if cert.all_criteria_passed:
        passed_checks += 1
    else:
        _print("  FAIL: Not all criteria passed")
        _report(passed_checks, total_checks)
        return False

    _report(passed_checks, total_checks)
    return True


def _report(passed: int, total: int) -> None:
    """Print final result."""
    _print("=" * 40)
    if passed == total:
        _print(f"RESULT: PASS ({passed}/{total} checks)")
    else:
        _print(f"RESULT: FAIL ({passed}/{total} checks)")


def main() -> int:
    """CLI entry point."""
    if len(sys.argv) < 4 or sys.argv[1] != "verify":
        print("Usage: python echelon_verify.py verify <certificate.json> <evidence_dir/>")
        return 2

    certificate_path = Path(sys.argv[2])
    evidence_dir = Path(sys.argv[3])

    if not certificate_path.exists():
        _print(f"Certificate file not found: {certificate_path}")
        return 2

    success = verify(certificate_path, evidence_dir)
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
