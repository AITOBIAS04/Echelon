#!/usr/bin/env python3
"""
Echelon OSINT Fixture Dataset Validator
Validates osint_composed_oracle_*.json fixture files against the
OSINT source registry and internal consistency rules.

Exit code 0 = pass, 1 = fail, 2 = usage error.

Usage:
  python3 validate_osint_fixtures.py <fixtures.json> <registry.json>

Checks:
  1. Every source_id referenced in evidence bundles exists in either
     (a) the registry, or (b) the dataset source_config with
     registry_status: "planned".
  2. receipt.source_id must equal the parent bundle's source_id
     (no cross-source receipt mismatch).
  3. source_config entries with registry_status: "planned" must have
     settlement_eligible: false (planned sources cannot settle).
  4. All source_ids in source_config must be referenced by at least
     one record (no orphaned configs).
  5. Hash length validation (64-char hex strings).
  6. proposed_source_group values must exist in proposed_groups_exercised.
  7. Counter-signal bundle consistency (non-blocking warning).
  8. Registry version + hash pin (if declared in dataset).
"""

__version__ = "0.2.0"

import hashlib
import json
import sys


def canonical_hash(obj: object) -> str:
    """Compute SHA-256 over canonical JSON (sorted keys, no whitespace, UTF-8).

    Matches Echelon's deterministic hashing convention:
    json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    """
    canonical = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def check_registry_pin(dataset: dict, registry: dict) -> list[str]:
    """Check that the registry matches the version + hash pin declared in the dataset.

    Hard errors: if the dataset declares a pin and it doesn't match, fail.
    If no pin is declared, skip silently (backwards-compatible).
    """
    errors = []

    required_version = dataset.get("registry_version_required")
    required_hash = dataset.get("registry_hash_required")

    if not required_version and not required_hash:
        return errors

    actual_version = registry.get("version")

    # CHECK 8a: version pin
    if required_version and actual_version != required_version:
        errors.append(
            f"Registry version mismatch: dataset requires '{required_version}', "
            f"got '{actual_version}'. Use the pinned registry or update the dataset pin."
        )

    # CHECK 8b: hash pin
    if required_hash:
        actual_hash = canonical_hash(registry)
        # Support both bare hex and "sha256:" prefix
        expected_hex = required_hash.removeprefix("sha256:")
        if actual_hash != expected_hex:
            errors.append(
                f"Registry hash mismatch: dataset requires '{expected_hex[:16]}...', "
                f"got '{actual_hash[:16]}...'. The registry has been modified since "
                f"this dataset was pinned."
            )

    return errors


def check_counter_signal_consistency(dataset: dict) -> list[str]:
    """Check that proposed_groups_exercised claims are backed by actual bundles.

    Non-blocking: returns warnings, not errors. Does not affect exit code.
    """
    warnings = []

    # Dataset-level check: if proposed_groups_exercised is declared,
    # at least one record must contain a counter_signal bundle.
    proposed = dataset.get("proposed_groups_exercised", [])
    if not proposed:
        return warnings

    has_counter_signal_bundle = False
    records = dataset.get("records", [])

    for record in records:
        bundles = record.get("inputs", {}).get("evidence_bundles", [])
        if any(b.get("resolution_role") == "counter_signal" for b in bundles):
            has_counter_signal_bundle = True
            break

    if not has_counter_signal_bundle:
        warnings.append(
            f"Dataset declares proposed_groups_exercised={proposed} "
            f"but no record contains a bundle with resolution_role='counter_signal'. "
            f"Add at least one counter-signal bundle to validate the claim."
        )

    # Per-record check: if a record's criteria include counter_signal_checked
    # with result=true, it should have at least one counter_signal bundle.
    for record in records:
        rid = record.get("record_id", "unknown")
        criteria_scores = record.get("criteria_scores", {})
        cs_checked = criteria_scores.get("counter_signal_checked", {})

        if cs_checked.get("result") is True:
            bundles = record.get("inputs", {}).get("evidence_bundles", [])
            has_cs = any(
                b.get("resolution_role") == "counter_signal"
                for b in bundles
            )
            if not has_cs:
                warnings.append(
                    f"Record {rid} has counter_signal_checked=true "
                    f"but no bundle with resolution_role='counter_signal'. "
                    f"Either add a counter-signal bundle or document why "
                    f"the gap is intentional."
                )

    return warnings


def validate(fixtures_path: str, registry_path: str) -> list[str]:
    with open(fixtures_path) as f:
        dataset = json.load(f)
    with open(registry_path) as f:
        registry = json.load(f)

    errors = []

    # CHECK 8: Registry version + hash pin (fail-fast before per-record checks)
    pin_errors = check_registry_pin(dataset, registry)
    errors.extend(pin_errors)

    # Build registry source_id set
    registry_ids = {s["source_id"] for s in registry["sources"]}

    # Build dataset source_config map
    source_config = {sc["source_id"]: sc for sc in dataset.get("source_config", [])}

    # Track which source_ids are actually referenced by records
    referenced_sources = set()

    records = dataset.get("records", [])
    proposed_exercised = set(dataset.get("proposed_groups_exercised", []))

    for rec in records:
        rid = rec["record_id"]

        # Collect all evidence bundles (primary + corroboration + counter-signal)
        bundles = []
        for eb in rec.get("inputs", {}).get("evidence_bundles", []):
            bundles.append(eb)

        for bundle in bundles:
            bid = bundle.get("bundle_id", "?")
            bsid = bundle.get("source_id")

            if not bsid:
                errors.append(f"{rid}/{bid}: missing source_id on evidence bundle")
                continue

            referenced_sources.add(bsid)

            # CHECK 1: source_id must exist in registry OR dataset source_config
            in_registry = bsid in registry_ids
            in_config = bsid in source_config

            if not in_registry and not in_config:
                errors.append(
                    f"{rid}/{bid}: source_id '{bsid}' not found in registry "
                    f"({registry.get('version', '?')}) or dataset source_config"
                )
            elif not in_registry and in_config:
                # CHECK 3: planned source must have registry_status marker
                sc = source_config[bsid]
                rs = sc.get("registry_status")
                if rs != "planned":
                    errors.append(
                        f"{rid}/{bid}: source_id '{bsid}' not in registry and "
                        f"source_config.registry_status is '{rs}' (expected 'planned')"
                    )
                # Planned sources must not be settlement_eligible
                if sc.get("settlement_eligible"):
                    errors.append(
                        f"{rid}/{bid}: source_id '{bsid}' is registry_status='planned' "
                        f"but settlement_eligible is true"
                    )

            # CHECK 2: receipt.source_id must equal bundle.source_id
            receipt = bundle.get("receipt", {})
            rsid = receipt.get("source_id")
            if rsid and rsid != bsid:
                errors.append(
                    f"{rid}/{bid}: receipt.source_id '{rsid}' does not match "
                    f"bundle.source_id '{bsid}'"
                )

            # CHECK 5: hash length validation
            for hash_field in ["raw_payload_hash", "content_hash"]:
                # Check bundle-level
                h = bundle.get(hash_field)
                if h and len(h) != 64:
                    errors.append(f"{rid}/{bid}: {hash_field} length is {len(h)}, expected 64")
                # Check receipt-level
                rh = receipt.get(hash_field)
                if rh and len(rh) != 64:
                    errors.append(f"{rid}/{bid}: receipt.{hash_field} length is {len(rh)}, expected 64")

            # CHECK 6: proposed_source_group must be in proposed_groups_exercised
            psg = bundle.get("proposed_source_group")
            if psg and psg not in proposed_exercised:
                errors.append(
                    f"{rid}/{bid}: proposed_source_group '{psg}' not listed "
                    f"in dataset.proposed_groups_exercised"
                )

    # CHECK 4: source_config entries must be referenced by at least one record
    config_ids = set(source_config.keys())
    orphaned = config_ids - referenced_sources
    if orphaned:
        errors.append(
            f"source_config has {len(orphaned)} unreferenced entries: "
            f"{sorted(orphaned)}"
        )

    return errors


if __name__ == "__main__":
    if "--version" in sys.argv:
        print(f"validate_osint_fixtures v{__version__}")
        sys.exit(0)

    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} [--version] <fixtures.json> <registry.json>")
        print(f"  --version  Print version ({__version__}) and exit")
        sys.exit(2)

    print(f"validate_osint_fixtures v{__version__}")

    errs = validate(sys.argv[1], sys.argv[2])
    if errs:
        print(f"FAILED — {len(errs)} error(s):")
        for e in errs:
            print(f"  ✗ {e}")
        sys.exit(1)
    else:
        with open(sys.argv[1]) as f:
            ds = json.load(f)
        n = len(ds.get("records", []))
        print(f"ALL FIXTURE VALIDATIONS PASSED ({n} records, dataset: {ds.get('dataset_id', '?')})")

    # CHECK 7: Counter-signal bundle consistency (non-blocking warnings)
    with open(sys.argv[1]) as f:
        ds = json.load(f)
    cs_warnings = check_counter_signal_consistency(ds)
    if cs_warnings:
        print(f"\n  Counter-signal consistency: {len(cs_warnings)} warning(s)")
        for w in cs_warnings:
            print(f"    ⚠ {w}")
    else:
        print("  Counter-signal consistency: OK")

    # Exit code based on errors only, not warnings
    sys.exit(1 if errs else 0)
