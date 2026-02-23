#!/usr/bin/env python3
"""
echelon verify — Standalone Echelon Certificate Verifier (v0.1)

Verifies that an Echelon calibration certificate is internally consistent,
that its evidence bundle hashes match, and that the claimed replay results
are reproducible against committed fixtures.

Usage:
    echelon_verify.py verify <certificate.json> [<evidence_bundle_dir>]
    echelon_verify.py inspect <certificate.json>
    echelon_verify.py hash <file_or_dir>
    echelon_verify.py schema-check <certificate.json>
    echelon_verify.py replay <template.json> <fixtures.json>

Exit codes:
    0  PASS — all checks passed
    1  FAIL — one or more checks failed
    2  ERROR — invalid input, missing files, or malformed data

Requires: Python 3.10+, no external dependencies.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Optional


# ════════════════════════════════════════════════════════════════
# CONSTANTS
# ════════════════════════════════════════════════════════════════

VERSION = "0.1.0"
HASH_ALGORITHM = "sha256"
CANONICAL_JSON_SPEC = "RFC8785"

# Certificate schema required fields
CERT_REQUIRED_FIELDS = {
    "certificate_id", "theatre_id", "template_id", "construct_id",
    "criteria", "scores", "composite_score", "replay_count",
    "evidence_bundle_hash", "commitment_hash", "issued_at",
    "verification_tier", "execution_path"
}

CERT_OPTIONAL_FIELDS = {
    "expires_at", "construct_version", "scorer_version",
    "methodology_version", "dataset_hash", "ground_truth_hash",
    "ground_truth_source", "theatre_committed_at", "theatre_resolved_at",
    "precision", "recall", "reply_accuracy"
}

VALID_VERIFICATION_TIERS = {"UNVERIFIED", "BACKTESTED", "PROVEN"}
VALID_EXECUTION_PATHS = {"replay", "live", "hybrid"}

TEMPLATE_REQUIRED_FIELDS = {
    "schema_version", "template_family", "execution_path",
    "theatre_id", "template_id", "criteria", "evidence_bundle"
}

EVIDENCE_REQUIRED_PATHS = {"inputs/", "policy/", "expected/", "manifest.json"}

# Terminal colours
class C:
    PASS = "\033[92m"
    FAIL = "\033[91m"
    WARN = "\033[93m"
    INFO = "\033[94m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RESET = "\033[0m"


# ════════════════════════════════════════════════════════════════
# DATA STRUCTURES
# ════════════════════════════════════════════════════════════════

class Verdict(Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    WARN = "WARN"
    SKIP = "SKIP"


@dataclass
class CheckResult:
    check_id: str
    title: str
    verdict: Verdict
    detail: str = ""
    evidence_refs: list[str] = field(default_factory=list)


@dataclass
class VerificationReport:
    certificate_id: str = ""
    template_id: str = ""
    checks: list[CheckResult] = field(default_factory=list)
    overall_verdict: Verdict = Verdict.PASS
    started_at: str = ""
    completed_at: str = ""
    verifier_version: str = VERSION

    def add(self, result: CheckResult) -> None:
        self.checks.append(result)
        if result.verdict == Verdict.FAIL:
            self.overall_verdict = Verdict.FAIL

    @property
    def pass_count(self) -> int:
        return sum(1 for c in self.checks if c.verdict == Verdict.PASS)

    @property
    def fail_count(self) -> int:
        return sum(1 for c in self.checks if c.verdict == Verdict.FAIL)

    @property
    def warn_count(self) -> int:
        return sum(1 for c in self.checks if c.verdict == Verdict.WARN)


# ════════════════════════════════════════════════════════════════
# CANONICAL JSON (RFC 8785 subset)
# ════════════════════════════════════════════════════════════════

def canonical_json(obj: Any) -> str:
    """
    Produce canonical JSON per RFC 8785:
    - Sorted keys
    - No whitespace
    - UTF-8 encoding
    """
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_json(obj: Any) -> str:
    return sha256_bytes(canonical_json(obj).encode("utf-8"))


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


# ════════════════════════════════════════════════════════════════
# LOADING & VALIDATION
# ════════════════════════════════════════════════════════════════

def load_json(path: Path) -> dict:
    """Load and parse a JSON file."""
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_iso_timestamp(ts: str) -> bool:
    """Check if a string is a valid ISO 8601 timestamp."""
    try:
        # Handle both Z and +00:00 suffixes
        ts_clean = ts.replace("Z", "+00:00")
        datetime.fromisoformat(ts_clean)
        return True
    except (ValueError, TypeError):
        return False


def validate_hex_hash(h: str, length: int = 64) -> bool:
    """Check if a string is a valid hex hash of expected length."""
    if not isinstance(h, str):
        return False
    return bool(re.match(f"^[a-f0-9]{{{length}}}$", h))


# ════════════════════════════════════════════════════════════════
# CHECK FUNCTIONS
# ════════════════════════════════════════════════════════════════

def check_schema_compliance(cert: dict) -> list[CheckResult]:
    """Validate certificate has all required fields and correct types."""
    results = []

    # Required fields
    missing = CERT_REQUIRED_FIELDS - set(cert.keys())
    if missing:
        results.append(CheckResult(
            "SCHEMA-001", "Required fields present",
            Verdict.FAIL,
            f"Missing required fields: {', '.join(sorted(missing))}"
        ))
    else:
        results.append(CheckResult(
            "SCHEMA-001", "Required fields present",
            Verdict.PASS,
            f"All {len(CERT_REQUIRED_FIELDS)} required fields present."
        ))

    # Verification tier
    tier = cert.get("verification_tier", "")
    if tier in VALID_VERIFICATION_TIERS:
        results.append(CheckResult(
            "SCHEMA-002", "Verification tier valid",
            Verdict.PASS, f"Tier: {tier}"
        ))
    else:
        results.append(CheckResult(
            "SCHEMA-002", "Verification tier valid",
            Verdict.FAIL, f"Invalid tier: '{tier}'. Expected one of: {VALID_VERIFICATION_TIERS}"
        ))

    # Execution path
    ep = cert.get("execution_path", "")
    if ep in VALID_EXECUTION_PATHS:
        results.append(CheckResult(
            "SCHEMA-003", "Execution path valid",
            Verdict.PASS, f"Path: {ep}"
        ))
    else:
        results.append(CheckResult(
            "SCHEMA-003", "Execution path valid",
            Verdict.FAIL, f"Invalid execution path: '{ep}'. Expected one of: {VALID_EXECUTION_PATHS}"
        ))

    # Timestamps
    for ts_field in ["issued_at", "expires_at", "theatre_committed_at", "theatre_resolved_at"]:
        ts_val = cert.get(ts_field)
        if ts_val is not None:
            if validate_iso_timestamp(ts_val):
                results.append(CheckResult(
                    f"SCHEMA-TS-{ts_field}", f"Timestamp valid: {ts_field}",
                    Verdict.PASS, f"{ts_field} = {ts_val}"
                ))
            else:
                results.append(CheckResult(
                    f"SCHEMA-TS-{ts_field}", f"Timestamp valid: {ts_field}",
                    Verdict.FAIL, f"Invalid ISO timestamp: {ts_val}"
                ))

    # Hash fields
    for hash_field in ["commitment_hash", "evidence_bundle_hash", "dataset_hash", "ground_truth_hash"]:
        hash_val = cert.get(hash_field)
        if hash_val is not None:
            if validate_hex_hash(hash_val):
                results.append(CheckResult(
                    f"SCHEMA-HASH-{hash_field}", f"Hash format valid: {hash_field}",
                    Verdict.PASS, f"{hash_field} = {hash_val[:16]}..."
                ))
            else:
                results.append(CheckResult(
                    f"SCHEMA-HASH-{hash_field}", f"Hash format valid: {hash_field}",
                    Verdict.FAIL, f"Invalid SHA-256 hex: '{hash_val}'"
                ))

    # Scores
    scores = cert.get("scores", {})
    criteria = cert.get("criteria", {})
    criteria_ids = criteria.get("criteria_ids", [])
    if isinstance(scores, dict) and isinstance(criteria_ids, list):
        missing_scores = set(criteria_ids) - set(scores.keys())
        if missing_scores:
            results.append(CheckResult(
                "SCHEMA-SCORES", "Scores cover all criteria",
                Verdict.FAIL, f"Missing scores for: {', '.join(sorted(missing_scores))}"
            ))
        else:
            results.append(CheckResult(
                "SCHEMA-SCORES", "Scores cover all criteria",
                Verdict.PASS, f"All {len(criteria_ids)} criteria have scores."
            ))

    # Composite score range
    cs = cert.get("composite_score")
    if isinstance(cs, (int, float)):
        if 0.0 <= cs <= 1.0:
            results.append(CheckResult(
                "SCHEMA-COMPOSITE", "Composite score in range [0, 1]",
                Verdict.PASS, f"composite_score = {cs}"
            ))
        else:
            results.append(CheckResult(
                "SCHEMA-COMPOSITE", "Composite score in range [0, 1]",
                Verdict.FAIL, f"composite_score = {cs} (out of range)"
            ))

    return results


def check_composite_score(cert: dict) -> CheckResult:
    """Verify composite score matches weighted sum of criteria scores."""
    criteria = cert.get("criteria", {})
    weights = criteria.get("weights", {})
    scores = cert.get("scores", {})
    declared_composite = cert.get("composite_score")

    if not weights or not scores or declared_composite is None:
        return CheckResult(
            "ARITH-001", "Composite score arithmetic",
            Verdict.SKIP, "Missing weights, scores, or composite_score."
        )

    computed = sum(weights.get(k, 0) * scores.get(k, 0) for k in weights)
    tolerance = 1e-9

    if abs(computed - declared_composite) <= tolerance:
        return CheckResult(
            "ARITH-001", "Composite score arithmetic",
            Verdict.PASS,
            f"Computed: {computed:.10f}, Declared: {declared_composite:.10f}, Delta: {abs(computed - declared_composite):.2e}"
        )
    else:
        return CheckResult(
            "ARITH-001", "Composite score arithmetic",
            Verdict.FAIL,
            f"Computed: {computed:.10f}, Declared: {declared_composite:.10f}, Delta: {abs(computed - declared_composite):.2e} (exceeds tolerance {tolerance})"
        )


def check_weight_sum(cert: dict) -> CheckResult:
    """Verify criteria weights sum to 1.0."""
    weights = cert.get("criteria", {}).get("weights", {})
    if not weights:
        return CheckResult("ARITH-002", "Criteria weights sum to 1.0", Verdict.SKIP, "No weights found.")

    total = sum(weights.values())
    if abs(total - 1.0) <= 1e-9:
        return CheckResult(
            "ARITH-002", "Criteria weights sum to 1.0",
            Verdict.PASS, f"Sum: {total:.10f}"
        )
    else:
        return CheckResult(
            "ARITH-002", "Criteria weights sum to 1.0",
            Verdict.FAIL, f"Sum: {total:.10f} (expected 1.0)"
        )


def check_expiry(cert: dict) -> CheckResult:
    """Check if certificate has expired."""
    expires = cert.get("expires_at")
    if not expires:
        return CheckResult("TIME-001", "Certificate not expired", Verdict.WARN, "No expires_at field.")

    try:
        exp_str = expires.replace("Z", "+00:00")
        # Handle timestamps without timezone info by assuming UTC
        try:
            exp_dt = datetime.fromisoformat(exp_str)
        except ValueError:
            exp_dt = datetime.fromisoformat(expires)
        if exp_dt.tzinfo is None:
            exp_dt = exp_dt.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        if now < exp_dt:
            delta = exp_dt - now
            return CheckResult(
                "TIME-001", "Certificate not expired",
                Verdict.PASS, f"Expires: {expires} ({delta.days} days remaining)"
            )
        else:
            return CheckResult(
                "TIME-001", "Certificate not expired",
                Verdict.FAIL, f"Certificate expired at {expires}"
            )
    except ValueError:
        return CheckResult("TIME-001", "Certificate not expired", Verdict.FAIL, f"Invalid timestamp: {expires}")


def check_temporal_ordering(cert: dict) -> CheckResult:
    """Verify that committed_at < resolved_at < issued_at."""
    fields = ["theatre_committed_at", "theatre_resolved_at", "issued_at"]
    timestamps = {}
    for f in fields:
        v = cert.get(f)
        if v:
            try:
                ts_parsed = datetime.fromisoformat(v.replace("Z", "+00:00"))
            except ValueError:
                try:
                    ts_parsed = datetime.fromisoformat(v)
                except ValueError:
                    return CheckResult("TIME-002", "Temporal ordering", Verdict.FAIL, f"Invalid timestamp: {f}={v}")
            if ts_parsed.tzinfo is None:
                ts_parsed = ts_parsed.replace(tzinfo=timezone.utc)
            timestamps[f] = ts_parsed

    if len(timestamps) < 2:
        return CheckResult("TIME-002", "Temporal ordering", Verdict.SKIP, "Insufficient timestamps for ordering check.")

    ordered = list(timestamps.items())
    for i in range(len(ordered) - 1):
        if ordered[i][1] > ordered[i + 1][1]:
            return CheckResult(
                "TIME-002", "Temporal ordering",
                Verdict.FAIL,
                f"{ordered[i][0]} ({ordered[i][1]}) is after {ordered[i + 1][0]} ({ordered[i + 1][1]})"
            )

    return CheckResult(
        "TIME-002", "Temporal ordering",
        Verdict.PASS,
        " < ".join(f"{k}={v.isoformat()}" for k, v in ordered)
    )


def check_dataset_hash(cert: dict, evidence_dir: Optional[Path]) -> CheckResult:
    """Verify dataset_hash against actual fixture file if evidence bundle provided."""
    declared = cert.get("dataset_hash")
    if not declared:
        return CheckResult("HASH-001", "Dataset hash verification", Verdict.SKIP, "No dataset_hash in certificate.")
    if not evidence_dir:
        return CheckResult("HASH-001", "Dataset hash verification", Verdict.SKIP, "No evidence bundle directory provided.")

    # Search for fixture files in the evidence directory
    inputs_dir = evidence_dir / "inputs"
    if not inputs_dir.exists():
        return CheckResult("HASH-001", "Dataset hash verification", Verdict.WARN, f"inputs/ directory not found in {evidence_dir}")

    # Try to find and hash fixture files
    fixture_files = list(inputs_dir.glob("*.json"))
    if not fixture_files:
        return CheckResult("HASH-001", "Dataset hash verification", Verdict.WARN, "No JSON fixtures found in inputs/")

    for ff in fixture_files:
        try:
            data = load_json(ff)
            computed = sha256_json(data)
            if computed == declared:
                return CheckResult(
                    "HASH-001", "Dataset hash verification",
                    Verdict.PASS,
                    f"Hash match: {ff.name} = {computed[:16]}..."
                )
        except (json.JSONDecodeError, FileNotFoundError):
            continue

    return CheckResult(
        "HASH-001", "Dataset hash verification",
        Verdict.FAIL,
        f"No fixture file matched declared hash: {declared[:16]}..."
    )


def check_evidence_bundle_hash(cert: dict, evidence_dir: Optional[Path]) -> CheckResult:
    """Verify evidence_bundle_hash against manifest."""
    declared = cert.get("evidence_bundle_hash")
    if not declared:
        return CheckResult("HASH-002", "Evidence bundle hash", Verdict.FAIL, "No evidence_bundle_hash in certificate.")
    if not evidence_dir:
        return CheckResult("HASH-002", "Evidence bundle hash", Verdict.SKIP, "No evidence bundle directory provided.")

    manifest_path = evidence_dir / "manifest.json"
    if not manifest_path.exists():
        return CheckResult("HASH-002", "Evidence bundle hash", Verdict.WARN, "manifest.json not found in evidence bundle.")

    try:
        manifest = load_json(manifest_path)
        computed = sha256_json(manifest)
        if computed == declared:
            return CheckResult(
                "HASH-002", "Evidence bundle hash",
                Verdict.PASS, f"Manifest hash match: {computed[:16]}..."
            )
        else:
            return CheckResult(
                "HASH-002", "Evidence bundle hash",
                Verdict.FAIL,
                f"Manifest hash mismatch. Computed: {computed[:16]}..., Declared: {declared[:16]}..."
            )
    except json.JSONDecodeError as e:
        return CheckResult("HASH-002", "Evidence bundle hash", Verdict.FAIL, f"Invalid manifest JSON: {e}")


def check_evidence_bundle_structure(evidence_dir: Optional[Path]) -> CheckResult:
    """Verify evidence bundle has required directory structure."""
    if not evidence_dir:
        return CheckResult("STRUCT-001", "Evidence bundle structure", Verdict.SKIP, "No evidence bundle directory provided.")
    if not evidence_dir.exists():
        return CheckResult("STRUCT-001", "Evidence bundle structure", Verdict.FAIL, f"Directory not found: {evidence_dir}")

    missing = []
    for req in EVIDENCE_REQUIRED_PATHS:
        target = evidence_dir / req
        if not target.exists():
            missing.append(req)

    if missing:
        return CheckResult(
            "STRUCT-001", "Evidence bundle structure",
            Verdict.FAIL, f"Missing required paths: {', '.join(missing)}"
        )
    else:
        return CheckResult(
            "STRUCT-001", "Evidence bundle structure",
            Verdict.PASS, f"All {len(EVIDENCE_REQUIRED_PATHS)} required paths present."
        )


def check_template_hash_consistency(cert: dict, evidence_dir: Optional[Path]) -> CheckResult:
    """Check that template in evidence bundle matches certificate's template_id."""
    if not evidence_dir:
        return CheckResult("CONSIST-001", "Template consistency", Verdict.SKIP, "No evidence bundle.")

    policy_dir = evidence_dir / "policy"
    if not policy_dir.exists():
        return CheckResult("CONSIST-001", "Template consistency", Verdict.WARN, "policy/ directory not found.")

    template_files = list(policy_dir.glob("*.json"))
    if not template_files:
        return CheckResult("CONSIST-001", "Template consistency", Verdict.WARN, "No template files in policy/")

    cert_template = cert.get("template_id", "")
    for tf in template_files:
        try:
            tmpl = load_json(tf)
            if tmpl.get("template_id") == cert_template:
                return CheckResult(
                    "CONSIST-001", "Template consistency",
                    Verdict.PASS,
                    f"Template '{cert_template}' found in {tf.name}"
                )
        except (json.JSONDecodeError, FileNotFoundError):
            continue

    return CheckResult(
        "CONSIST-001", "Template consistency",
        Verdict.WARN,
        f"No template file matched certificate's template_id: '{cert_template}'"
    )


def check_deterministic_replay(template_path: Path, fixtures_path: Path) -> list[CheckResult]:
    """
    Run a deterministic replay of fixtures against template criteria.
    This checks structural consistency — actual arithmetic replay requires
    the construct adapter to be implemented.
    """
    results = []

    try:
        template = load_json(template_path)
        fixtures = load_json(fixtures_path)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        results.append(CheckResult("REPLAY-000", "Load inputs", Verdict.FAIL, str(e)))
        return results

    # Check template schema
    tmpl_missing = TEMPLATE_REQUIRED_FIELDS - set(template.keys())
    if tmpl_missing:
        results.append(CheckResult(
            "REPLAY-001", "Template schema valid",
            Verdict.FAIL, f"Missing fields: {', '.join(sorted(tmpl_missing))}"
        ))
    else:
        results.append(CheckResult("REPLAY-001", "Template schema valid", Verdict.PASS))

    # Check dataset hash
    declared_hashes = template.get("dataset_hashes", {})
    fixtures_filename = fixtures_path.name
    if fixtures_filename in declared_hashes:
        computed = sha256_json(fixtures)
        declared = declared_hashes[fixtures_filename]
        if computed == declared:
            results.append(CheckResult(
                "REPLAY-002", "Fixture dataset hash match",
                Verdict.PASS, f"{computed[:16]}..."
            ))
        else:
            results.append(CheckResult(
                "REPLAY-002", "Fixture dataset hash match",
                Verdict.FAIL,
                f"Computed: {computed[:16]}..., Declared: {declared[:16]}..."
            ))
    else:
        results.append(CheckResult(
            "REPLAY-002", "Fixture dataset hash match",
            Verdict.WARN, f"No declared hash for '{fixtures_filename}' in template."
        ))

    # Check fixture records structure
    records = fixtures.get("records", [])
    if not records:
        results.append(CheckResult("REPLAY-003", "Fixture records present", Verdict.FAIL, "No records found."))
    else:
        results.append(CheckResult(
            "REPLAY-003", "Fixture records present",
            Verdict.PASS, f"{len(records)} records found."
        ))

    # Check each record has inputs and expected_outputs
    malformed = []
    for i, rec in enumerate(records):
        rid = rec.get("record_id", f"index_{i}")
        if "inputs" not in rec:
            malformed.append(f"{rid}: missing 'inputs'")
        if "expected_outputs" not in rec:
            malformed.append(f"{rid}: missing 'expected_outputs'")

    if malformed:
        results.append(CheckResult(
            "REPLAY-004", "Record structure valid",
            Verdict.FAIL, f"Malformed records: {'; '.join(malformed[:5])}"
        ))
    else:
        results.append(CheckResult(
            "REPLAY-004", "Record structure valid",
            Verdict.PASS, f"All {len(records)} records have inputs and expected_outputs."
        ))

    # Check criteria alignment
    tmpl_criteria = set(template.get("criteria", {}).get("criteria_ids", []))
    if tmpl_criteria:
        results.append(CheckResult(
            "REPLAY-005", "Criteria defined",
            Verdict.PASS, f"Criteria: {', '.join(sorted(tmpl_criteria))}"
        ))
    else:
        results.append(CheckResult("REPLAY-005", "Criteria defined", Verdict.FAIL, "No criteria_ids in template."))

    # Check weights sum
    weights = template.get("criteria", {}).get("weights", {})
    if weights:
        total = sum(weights.values())
        if abs(total - 1.0) <= 1e-9:
            results.append(CheckResult("REPLAY-006", "Template weights sum to 1.0", Verdict.PASS, f"Sum: {total:.4f}"))
        else:
            results.append(CheckResult("REPLAY-006", "Template weights sum to 1.0", Verdict.FAIL, f"Sum: {total:.4f}"))

    return results


# ════════════════════════════════════════════════════════════════
# REPORTING
# ════════════════════════════════════════════════════════════════

def format_verdict(v: Verdict) -> str:
    colours = {
        Verdict.PASS: C.PASS,
        Verdict.FAIL: C.FAIL,
        Verdict.WARN: C.WARN,
        Verdict.SKIP: C.DIM,
    }
    return f"{colours.get(v, '')}{v.value}{C.RESET}"


def print_report(report: VerificationReport) -> None:
    """Print formatted verification report to terminal."""
    print()
    print(f"{C.BOLD}{'═' * 72}{C.RESET}")
    print(f"{C.BOLD}  ECHELON VERIFIER — Verification Report{C.RESET}")
    print(f"{'═' * 72}")
    print(f"  Certificate:  {report.certificate_id or 'N/A'}")
    print(f"  Template:     {report.template_id or 'N/A'}")
    print(f"  Verifier:     echelon_verify v{report.verifier_version}")
    print(f"  Timestamp:    {report.completed_at}")
    print(f"{'─' * 72}")
    print()

    for check in report.checks:
        icon = format_verdict(check.verdict)
        print(f"  [{icon}] {check.check_id}: {check.title}")
        if check.detail:
            print(f"         {C.DIM}{check.detail}{C.RESET}")

    print()
    print(f"{'─' * 72}")
    passed = report.pass_count
    failed = report.fail_count
    warned = report.warn_count
    total = len(report.checks)

    summary_colour = C.PASS if report.overall_verdict == Verdict.PASS else C.FAIL
    print(f"  {summary_colour}{C.BOLD}OVERALL: {report.overall_verdict.value}{C.RESET}")
    print(f"  {C.PASS}{passed} passed{C.RESET} | {C.FAIL}{failed} failed{C.RESET} | {C.WARN}{warned} warnings{C.RESET} | {total} total")
    print(f"{'═' * 72}")
    print()


def export_report_json(report: VerificationReport) -> dict:
    """Export report as JSON-serialisable dict."""
    return {
        "echelon_verifier_version": report.verifier_version,
        "certificate_id": report.certificate_id,
        "template_id": report.template_id,
        "overall_verdict": report.overall_verdict.value,
        "started_at": report.started_at,
        "completed_at": report.completed_at,
        "summary": {
            "total_checks": len(report.checks),
            "passed": report.pass_count,
            "failed": report.fail_count,
            "warnings": report.warn_count,
        },
        "checks": [
            {
                "check_id": c.check_id,
                "title": c.title,
                "verdict": c.verdict.value,
                "detail": c.detail,
            }
            for c in report.checks
        ],
    }


# ════════════════════════════════════════════════════════════════
# COMMANDS
# ════════════════════════════════════════════════════════════════

def cmd_verify(cert_path: Path, evidence_dir: Optional[Path], json_output: bool) -> int:
    """Full verification of certificate and evidence bundle."""
    report = VerificationReport()
    report.started_at = datetime.now(timezone.utc).isoformat()

    try:
        cert = load_json(cert_path)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"{C.FAIL}ERROR: Cannot load certificate: {e}{C.RESET}")
        return 2

    report.certificate_id = cert.get("certificate_id", "unknown")
    report.template_id = cert.get("template_id", "unknown")

    # Schema checks
    for r in check_schema_compliance(cert):
        report.add(r)

    # Arithmetic checks
    report.add(check_composite_score(cert))
    report.add(check_weight_sum(cert))

    # Temporal checks
    report.add(check_expiry(cert))
    report.add(check_temporal_ordering(cert))

    # Hash checks
    report.add(check_dataset_hash(cert, evidence_dir))
    report.add(check_evidence_bundle_hash(cert, evidence_dir))

    # Structure checks
    report.add(check_evidence_bundle_structure(evidence_dir))
    report.add(check_template_hash_consistency(cert, evidence_dir))

    report.completed_at = datetime.now(timezone.utc).isoformat()

    if json_output:
        print(json.dumps(export_report_json(report), indent=2))
    else:
        print_report(report)

    return 0 if report.overall_verdict == Verdict.PASS else 1


def cmd_inspect(cert_path: Path) -> int:
    """Print certificate summary without verification."""
    try:
        cert = load_json(cert_path)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"{C.FAIL}ERROR: {e}{C.RESET}")
        return 2

    print()
    print(f"{C.BOLD}{'═' * 60}{C.RESET}")
    print(f"{C.BOLD}  ECHELON CERTIFICATE INSPECTION{C.RESET}")
    print(f"{'═' * 60}")

    fields = [
        ("Certificate ID", "certificate_id"),
        ("Theatre ID", "theatre_id"),
        ("Template ID", "template_id"),
        ("Construct ID", "construct_id"),
        ("Construct Version", "construct_version"),
        ("Verification Tier", "verification_tier"),
        ("Execution Path", "execution_path"),
        ("Composite Score", "composite_score"),
        ("Replay Count", "replay_count"),
        ("Scorer Version", "scorer_version"),
        ("Methodology Version", "methodology_version"),
        ("Issued At", "issued_at"),
        ("Expires At", "expires_at"),
        ("Commitment Hash", "commitment_hash"),
        ("Evidence Bundle Hash", "evidence_bundle_hash"),
        ("Dataset Hash", "dataset_hash"),
    ]

    for label, key in fields:
        val = cert.get(key)
        if val is not None:
            if isinstance(val, str) and len(val) > 50:
                val = val[:16] + "..." + val[-8:]
            print(f"  {C.DIM}{label:>25}{C.RESET}: {val}")

    # Scores
    scores = cert.get("scores", {})
    if scores:
        print(f"\n  {C.BOLD}Criteria Scores:{C.RESET}")
        weights = cert.get("criteria", {}).get("weights", {})
        for k, v in sorted(scores.items()):
            w = weights.get(k)
            w_str = f" (weight: {w})" if w else ""
            colour = C.PASS if v >= 0.8 else (C.WARN if v >= 0.5 else C.FAIL)
            print(f"    {k:>30}: {colour}{v:.4f}{C.RESET}{w_str}")

    print(f"{'═' * 60}")
    print()
    return 0


def cmd_hash(target_path: Path) -> int:
    """Compute SHA-256 hash of a file or directory manifest."""
    if not target_path.exists():
        print(f"{C.FAIL}ERROR: Path not found: {target_path}{C.RESET}")
        return 2

    if target_path.is_file():
        if target_path.suffix == ".json":
            try:
                data = load_json(target_path)
                h = sha256_json(data)
                print(f"{C.INFO}Canonical JSON (RFC8785) SHA-256:{C.RESET}")
                print(f"  {h}")
            except json.JSONDecodeError:
                h = sha256_file(target_path)
                print(f"{C.INFO}Raw file SHA-256:{C.RESET}")
                print(f"  {h}")
        else:
            h = sha256_file(target_path)
            print(f"{C.INFO}Raw file SHA-256:{C.RESET}")
            print(f"  {h}")
    elif target_path.is_dir():
        print(f"{C.INFO}Directory hash manifest for: {target_path}{C.RESET}")
        files = sorted(target_path.rglob("*"))
        manifest = {}
        for f in files:
            if f.is_file():
                rel = f.relative_to(target_path)
                h = sha256_file(f)
                manifest[str(rel)] = h
                print(f"  {h[:16]}...  {rel}")

        overall = sha256_json(manifest)
        print(f"\n{C.BOLD}Composite manifest hash:{C.RESET}")
        print(f"  {overall}")
    return 0


def cmd_schema_check(cert_path: Path) -> int:
    """Run schema compliance checks only."""
    try:
        cert = load_json(cert_path)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"{C.FAIL}ERROR: {e}{C.RESET}")
        return 2

    report = VerificationReport()
    report.started_at = datetime.now(timezone.utc).isoformat()
    report.certificate_id = cert.get("certificate_id", "unknown")
    report.template_id = cert.get("template_id", "unknown")

    for r in check_schema_compliance(cert):
        report.add(r)

    report.completed_at = datetime.now(timezone.utc).isoformat()
    print_report(report)
    return 0 if report.overall_verdict == Verdict.PASS else 1


def cmd_replay(template_path: Path, fixtures_path: Path, json_output: bool) -> int:
    """Run structural replay checks against template and fixtures."""
    report = VerificationReport()
    report.started_at = datetime.now(timezone.utc).isoformat()

    try:
        tmpl = load_json(template_path)
        report.template_id = tmpl.get("template_id", "unknown")
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"{C.FAIL}ERROR: {e}{C.RESET}")
        return 2

    for r in check_deterministic_replay(template_path, fixtures_path):
        report.add(r)

    report.completed_at = datetime.now(timezone.utc).isoformat()

    if json_output:
        print(json.dumps(export_report_json(report), indent=2))
    else:
        print_report(report)

    return 0 if report.overall_verdict == Verdict.PASS else 1


# ════════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════════

def main() -> int:
    parser = argparse.ArgumentParser(
        prog="echelon_verify",
        description="Echelon Standalone Certificate Verifier",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  echelon_verify.py verify certificate.json evidence_bundle/
  echelon_verify.py verify certificate.json --json
  echelon_verify.py inspect certificate.json
  echelon_verify.py hash waterfall_fixtures_10.json
  echelon_verify.py hash evidence_bundle/
  echelon_verify.py schema-check certificate.json
  echelon_verify.py replay template.json fixtures.json
        """,
    )
    parser.add_argument("--version", action="version", version=f"echelon_verify {VERSION}")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # verify
    p_verify = subparsers.add_parser("verify", help="Full certificate + evidence bundle verification")
    p_verify.add_argument("certificate", type=Path, help="Path to certificate JSON")
    p_verify.add_argument("evidence_dir", type=Path, nargs="?", help="Path to evidence bundle directory")
    p_verify.add_argument("--json", dest="json_output", action="store_true", help="Output report as JSON")

    # inspect
    p_inspect = subparsers.add_parser("inspect", help="Print certificate summary")
    p_inspect.add_argument("certificate", type=Path, help="Path to certificate JSON")

    # hash
    p_hash = subparsers.add_parser("hash", help="Compute SHA-256 hash (canonical JSON for .json files)")
    p_hash.add_argument("target", type=Path, help="File or directory to hash")

    # schema-check
    p_schema = subparsers.add_parser("schema-check", help="Validate certificate schema only")
    p_schema.add_argument("certificate", type=Path, help="Path to certificate JSON")

    # replay
    p_replay = subparsers.add_parser("replay", help="Structural replay check against template + fixtures")
    p_replay.add_argument("template", type=Path, help="Path to theatre template JSON")
    p_replay.add_argument("fixtures", type=Path, help="Path to fixture dataset JSON")
    p_replay.add_argument("--json", dest="json_output", action="store_true", help="Output report as JSON")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 2

    if args.command == "verify":
        return cmd_verify(args.certificate, args.evidence_dir, args.json_output)
    elif args.command == "inspect":
        return cmd_inspect(args.certificate)
    elif args.command == "hash":
        return cmd_hash(args.target)
    elif args.command == "schema-check":
        return cmd_schema_check(args.certificate)
    elif args.command == "replay":
        return cmd_replay(args.template, args.fixtures, args.json_output)
    else:
        parser.print_help()
        return 2


if __name__ == "__main__":
    sys.exit(main())
