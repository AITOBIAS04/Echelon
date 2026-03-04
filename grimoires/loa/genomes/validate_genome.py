#!/usr/bin/env python3
"""
Echelon T0 Genome Validator
Version: 1.0.0
Date: 4 March 2026

Zero-dependency validator for archetype genome YAML files.
Enforces the GENOME_SCHEMA.md contract. Same validation pattern
as the OSINT registry-fixture validators (Cycle-005).

Usage:
    python validate_genome.py                     # validate all genomes in ./genomes/
    python validate_genome.py path/to/genome.yaml # validate a single file
    python validate_genome.py --summary           # summary table only
"""

import sys
import os
import hashlib
import json
from pathlib import Path

# ---------------------------------------------------------------------------
# YAML parser (zero-dependency, handles the subset we need)
# ---------------------------------------------------------------------------

def parse_yaml(text: str) -> dict:
    """Minimal YAML parser sufficient for genome files.
    Handles: scalars, strings, lists, nested dicts, comments.
    Does NOT handle: anchors, aliases, multi-line strings, flow mappings.
    """
    lines = text.split("\n")
    return _parse_block(lines, 0, 0)[0]


def _indent_level(line: str) -> int:
    return len(line) - len(line.lstrip())


def _parse_value(raw: str):
    raw = raw.strip()
    if raw == "" or raw.startswith("#"):
        return None
    # Remove inline comments (but not inside brackets or quotes)
    bracket_depth = 0
    in_quote = False
    for i, ch in enumerate(raw):
        if ch in ('"', "'"):
            in_quote = not in_quote
        elif ch == '[':
            bracket_depth += 1
        elif ch == ']':
            bracket_depth -= 1
        elif ch == "#" and bracket_depth == 0 and not in_quote and (i == 0 or raw[i - 1] == " "):
            raw = raw[:i].strip()
            break
    # Inline flow list: [T1, T2, T3]
    if raw.startswith("[") and raw.endswith("]"):
        inner = raw[1:-1].strip()
        if not inner:
            return []
        items = [_parse_value(item.strip()) for item in inner.split(",")]
        return items
    # Quoted string
    if (raw.startswith('"') and raw.endswith('"')) or (raw.startswith("'") and raw.endswith("'")):
        return raw[1:-1]
    # Boolean
    if raw.lower() in ("true", "yes"):
        return True
    if raw.lower() in ("false", "no"):
        return False
    # Null
    if raw.lower() in ("null", "~"):
        return None
    # Number
    try:
        if "." in raw:
            return float(raw)
        return int(raw)
    except ValueError:
        pass
    return raw


def _in_string(text: str, pos: int) -> bool:
    in_single = False
    in_double = False
    for i in range(pos):
        if text[i] == '"' and not in_single:
            in_double = not in_double
        elif text[i] == "'" and not in_double:
            in_single = not in_single
    return in_single or in_double


def _parse_block(lines: list, start: int, base_indent: int) -> tuple:
    result = {}
    i = start
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Skip blank lines and comments
        if not stripped or stripped.startswith("#"):
            i += 1
            continue

        indent = _indent_level(line)
        if indent < base_indent:
            break

        if indent > base_indent and not stripped.startswith("- "):
            i += 1
            continue

        if ":" in stripped and not stripped.startswith("- "):
            colon_pos = stripped.index(":")
            key = stripped[:colon_pos].strip()
            rest = stripped[colon_pos + 1:].strip()

            if rest and not rest.startswith("#"):
                # Inline value
                result[key] = _parse_value(rest)
                i += 1
            elif i + 1 < len(lines):
                next_stripped = ""
                j = i + 1
                while j < len(lines):
                    ns = lines[j].strip()
                    if ns and not ns.startswith("#"):
                        next_stripped = ns
                        break
                    j += 1

                if next_stripped.startswith("- "):
                    # List
                    result[key] = _parse_list(lines, j, _indent_level(lines[j]))
                    # Skip past the list
                    i = j
                    list_indent = _indent_level(lines[j])
                    while i < len(lines):
                        ls = lines[i].strip()
                        if not ls or ls.startswith("#"):
                            i += 1
                            continue
                        if _indent_level(lines[i]) < list_indent:
                            break
                        i += 1
                elif _indent_level(lines[j]) > indent:
                    # Nested dict
                    sub, i = _parse_block(lines, j, _indent_level(lines[j]))
                    result[key] = sub
                else:
                    result[key] = None
                    i += 1
            else:
                result[key] = None
                i += 1
        else:
            i += 1

    return result, i


def _parse_list(lines: list, start: int, base_indent: int) -> list:
    result = []
    i = start
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            i += 1
            continue
        indent = _indent_level(line)
        if indent < base_indent:
            break
        if stripped.startswith("- "):
            item_text = stripped[2:].strip()
            if ":" in item_text:
                # List of dicts — parse as sub-block
                sub = {}
                colon_pos = item_text.index(":")
                key = item_text[:colon_pos].strip()
                val = item_text[colon_pos + 1:].strip()
                sub[key] = _parse_value(val) if val else None
                # Check for continuation lines
                i += 1
                while i < len(lines):
                    ls = lines[i].strip()
                    if not ls or ls.startswith("#"):
                        i += 1
                        continue
                    li = _indent_level(lines[i])
                    if li <= base_indent:
                        break
                    if ":" in ls and not ls.startswith("- "):
                        cp = ls.index(":")
                        sub[ls[:cp].strip()] = _parse_value(ls[cp + 1:].strip())
                    i += 1
                result.append(sub)
            else:
                result.append(_parse_value(item_text))
                i += 1
        else:
            i += 1
    return result


# ---------------------------------------------------------------------------
# Validation rules
# ---------------------------------------------------------------------------

VALID_ARCHETYPES = {"SHARK", "SPY", "DIPLOMAT", "SABOTEUR", "WHALE", "DEGEN"}
VALID_LINEAGES = {"GENESIS", "USER_CREATED", "BRED"}
VALID_TIERS = {"T0", "T1", "T2", "T3"}
VALID_METHODS = {"SOFTMAX_Q_VALUE", "EPSILON_GREEDY", "THOMPSON_SAMPLING"}
VALID_RESPONSE_ACTIONS = {"EXTRACT", "DEFEND", "ATTACK", "OBSERVE", "HEDGE"}
VALID_CIRCUIT_BREAKER = {"HALT", "REDUCE", "IGNORE"}
VALID_PNL = {"PROFITABLE", "BREAKEVEN", "LOSS_ACCEPTABLE"}
REQUIRED_BIAS_KEYS = {"buy", "sell", "hold", "observe", "sabotage", "shield"}
INQUIRY_CLASSES = {"counterfactual", "investigative", "inspection", "survey", "scrutiny"}

REQUIRED_TOP_KEYS = {
    "schema_version", "identity", "economic_parameters", "tier_profile",
    "decision_policy", "paradox_behaviour", "inquiry_class_affinity",
    "success_metrics"
}


class ValidationError:
    def __init__(self, field: str, message: str, severity: str = "ERROR"):
        self.field = field
        self.message = message
        self.severity = severity

    def __str__(self):
        return f"  [{self.severity}] {self.field}: {self.message}"


def validate_genome(data: dict, filename: str = "") -> list:
    errors = []

    def err(field, msg, sev="ERROR"):
        errors.append(ValidationError(field, msg, sev))

    def get(path: str, default=None):
        parts = path.split(".")
        current = data
        for p in parts:
            if isinstance(current, dict) and p in current:
                current = current[p]
            else:
                return default
        return current

    # 1. Schema version
    sv = get("schema_version")
    if sv != "1.0.0":
        err("schema_version", f"Expected '1.0.0', got '{sv}'")

    # 2. Top-level keys
    actual_keys = {k for k in data.keys() if k != "schema_version"}
    expected = REQUIRED_TOP_KEYS - {"schema_version"}
    missing = expected - actual_keys
    extra = actual_keys - expected
    for m in missing:
        err(m, "Required top-level section missing")
    for e in extra:
        err(e, "Unexpected top-level section", "ERROR")

    # 3. Identity
    ident = get("identity", {})
    if not isinstance(ident, dict):
        err("identity", "Must be a mapping")
    else:
        for field in ["name", "archetype", "variant", "agent_id", "version", "lineage", "description"]:
            if field not in ident:
                err(f"identity.{field}", "Required field missing")

        arch = ident.get("archetype", "")
        if arch and arch not in VALID_ARCHETYPES:
            err("identity.archetype", f"Invalid archetype '{arch}'. Must be one of: {VALID_ARCHETYPES}")

        lin = ident.get("lineage", "")
        if lin and lin not in VALID_LINEAGES:
            err("identity.lineage", f"Invalid lineage '{lin}'. Must be one of: {VALID_LINEAGES}")

        # agent_id pattern check
        aid = ident.get("agent_id", "")
        ver = ident.get("version", "")
        variant = ident.get("variant", "")
        if aid and arch and variant and ver:
            expected_id = f"{arch.lower()}_{variant.lower()}_v{ver}"
            if aid != expected_id:
                err("identity.agent_id", f"Expected '{expected_id}', got '{aid}'")

    # 4. Economic parameters
    econ = get("economic_parameters", {})
    if not isinstance(econ, dict):
        err("economic_parameters", "Must be a mapping")
    else:
        float_params = {
            "risk_appetite": (0.0, 1.0),
            "evidence_sensitivity": (0.0, 1.0),
            "time_preference": (0.0, 1.0),
            "exploration_rate": (0.0, 1.0),
            "sabotage_propensity": (0.0, 1.0),
            "shield_propensity": (0.0, 1.0),
        }
        int_params = {
            "position_limit": (1, 100000),
            "patience": (1, 600),
        }
        for param, (lo, hi) in float_params.items():
            val = econ.get(param)
            if val is None:
                err(f"economic_parameters.{param}", "Required field missing")
            elif not isinstance(val, (int, float)):
                err(f"economic_parameters.{param}", f"Must be numeric, got {type(val).__name__}")
            elif val < lo or val > hi:
                err(f"economic_parameters.{param}", f"Value {val} outside range [{lo}, {hi}]")

        for param, (lo, hi) in int_params.items():
            val = econ.get(param)
            if val is None:
                err(f"economic_parameters.{param}", "Required field missing")
            elif not isinstance(val, (int, float)):
                err(f"economic_parameters.{param}", f"Must be numeric, got {type(val).__name__}")
            elif val < lo or val > hi:
                err(f"economic_parameters.{param}", f"Value {val} outside range [{lo}, {hi}]")

    # 5. Tier profile
    tier = get("tier_profile", {})
    if not isinstance(tier, dict):
        err("tier_profile", "Must be a mapping")
    else:
        at = tier.get("active_tiers", [])
        if not isinstance(at, list) or len(at) == 0:
            err("tier_profile.active_tiers", "Must be a non-empty list")
        else:
            for t in at:
                if t not in VALID_TIERS:
                    err("tier_profile.active_tiers", f"Invalid tier '{t}'")

        dt = tier.get("default_tier")
        if dt not in VALID_TIERS:
            err("tier_profile.default_tier", f"Invalid default tier '{dt}'")
        elif isinstance(at, list) and dt not in at:
            err("tier_profile.default_tier", f"Default tier '{dt}' not in active_tiers {at}")

        esc = tier.get("escalation_rules", [])
        if not isinstance(esc, list) or len(esc) == 0:
            err("tier_profile.escalation_rules", "Must define at least one escalation rule")
        else:
            for idx, rule in enumerate(esc):
                if not isinstance(rule, dict):
                    err(f"tier_profile.escalation_rules[{idx}]", "Must be a mapping")
                    continue
                for req in ["condition", "escalate_to", "cooldown_seconds"]:
                    if req not in rule:
                        err(f"tier_profile.escalation_rules[{idx}].{req}", "Required field missing")

        if "cost_profile" not in tier:
            err("tier_profile.cost_profile", "Required field missing")
        if "max_inference_budget_per_market" not in tier:
            err("tier_profile.max_inference_budget_per_market", "Required field missing")

    # 6. Decision policy
    dp = get("decision_policy", {})
    if not isinstance(dp, dict):
        err("decision_policy", "Must be a mapping")
    else:
        method = dp.get("method", "")
        if method not in VALID_METHODS:
            err("decision_policy.method", f"Invalid method '{method}'")

        temp = dp.get("temperature")
        if temp is None:
            err("decision_policy.temperature", "Required field missing")
        elif not isinstance(temp, (int, float)):
            err("decision_policy.temperature", f"Must be numeric, got {type(temp).__name__}")

        bv = dp.get("bias_vector", {})
        if not isinstance(bv, dict):
            err("decision_policy.bias_vector", "Must be a mapping")
        else:
            missing_keys = REQUIRED_BIAS_KEYS - set(bv.keys())
            for mk in missing_keys:
                err(f"decision_policy.bias_vector.{mk}", "Required bias key missing")

        sr = dp.get("strategy_rules", [])
        if not isinstance(sr, list) or len(sr) == 0:
            err("decision_policy.strategy_rules", "Must define at least one strategy rule")

    # 7. Paradox behaviour
    pb = get("paradox_behaviour", {})
    if not isinstance(pb, dict):
        err("paradox_behaviour", "Must be a mapping")
    else:
        lgt = pb.get("logic_gap_threshold")
        if lgt is None:
            err("paradox_behaviour.logic_gap_threshold", "Required field missing")
        elif not isinstance(lgt, (int, float)):
            err("paradox_behaviour.logic_gap_threshold", "Must be numeric")

        ra = pb.get("response_action", "")
        if ra not in VALID_RESPONSE_ACTIONS:
            err("paradox_behaviour.response_action", f"Invalid response action '{ra}'")

        ecc = pb.get("extraction_cost_ceiling")
        if ecc is None:
            err("paradox_behaviour.extraction_cost_ceiling", "Required field missing")

        cw = pb.get("coalition_willingness")
        if cw is None:
            err("paradox_behaviour.coalition_willingness", "Required field missing")
        elif isinstance(cw, (int, float)) and (cw < 0.0 or cw > 1.0):
            err("paradox_behaviour.coalition_willingness", f"Value {cw} outside range [0.0, 1.0]")

        cbb = pb.get("circuit_breaker_behaviour", "")
        if cbb not in VALID_CIRCUIT_BREAKER:
            err("paradox_behaviour.circuit_breaker_behaviour", f"Invalid '{cbb}'")

    # 8. Inquiry class affinity
    ica = get("inquiry_class_affinity", {})
    if not isinstance(ica, dict):
        err("inquiry_class_affinity", "Must be a mapping")
    else:
        for cls in INQUIRY_CLASSES:
            val = ica.get(cls)
            if val is None:
                err(f"inquiry_class_affinity.{cls}", "Required field missing")
            elif not isinstance(val, (int, float)):
                err(f"inquiry_class_affinity.{cls}", "Must be numeric")
            elif val < 0.0 or val > 1.0:
                err(f"inquiry_class_affinity.{cls}", f"Value {val} outside range [0.0, 1.0]")

        total = sum(ica.get(c, 0) for c in INQUIRY_CLASSES if isinstance(ica.get(c, 0), (int, float)))
        if total < 1.0:
            err("inquiry_class_affinity", f"Sum {total:.2f} < 1.0 — agent must be useful in at least some classes")

    # 9. Success metrics
    sm = get("success_metrics", {})
    if not isinstance(sm, dict):
        err("success_metrics", "Must be a mapping")
    else:
        for field in ["brier_score_target", "ece_bound", "consistency_threshold",
                       "position_size_variance_max", "fork_choice_consistency_min"]:
            val = sm.get(field)
            if val is None:
                err(f"success_metrics.{field}", "Required field missing")
            elif not isinstance(val, (int, float)):
                err(f"success_metrics.{field}", "Must be numeric")

        pnl = sm.get("pnl_expectation", "")
        if pnl not in VALID_PNL:
            err(f"success_metrics.pnl_expectation", f"Invalid '{pnl}'")

    return errors


# ---------------------------------------------------------------------------
# Commitment hash computation
# ---------------------------------------------------------------------------

def compute_commitment_hash(data: dict) -> str:
    """Compute the SHA-256 commitment hash from the fields specified in
    GENOME_SCHEMA.md section 'Commitment Hash Composition'."""

    parts = []
    ident = data.get("identity", {})
    parts.append(str(ident.get("agent_id", "")))
    parts.append(str(ident.get("version", "")))

    econ = data.get("economic_parameters", {})
    for field in ["risk_appetite", "evidence_sensitivity", "time_preference",
                   "exploration_rate", "position_limit", "sabotage_propensity",
                   "shield_propensity", "patience"]:
        parts.append(str(econ.get(field, "")))

    tiers = data.get("tier_profile", {}).get("active_tiers", [])
    if isinstance(tiers, list):
        parts.append(",".join(sorted(str(t) for t in tiers)))

    dp = data.get("decision_policy", {})
    parts.append(str(dp.get("method", "")))
    parts.append(str(dp.get("temperature", "")))

    pb = data.get("paradox_behaviour", {})
    parts.append(str(pb.get("logic_gap_threshold", "")))
    parts.append(str(pb.get("response_action", "")))

    payload = "|".join(parts)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def validate_file(filepath: str) -> tuple:
    """Returns (genome_data, errors, commitment_hash)."""
    with open(filepath, "r", encoding="utf-8") as f:
        text = f.read()
    data = parse_yaml(text)
    errors = validate_genome(data, filepath)
    ch = compute_commitment_hash(data) if not any(e.severity == "ERROR" for e in errors) else None
    return data, errors, ch


def main():
    args = sys.argv[1:]
    summary_only = "--summary" in args
    args = [a for a in args if a != "--summary"]

    if args:
        files = [Path(a) for a in args]
    else:
        genome_dir = Path(__file__).parent.parent / "genomes"
        if not genome_dir.exists():
            genome_dir = Path("genomes")
        files = sorted(genome_dir.glob("*.yaml"))

    if not files:
        print("No genome files found.")
        sys.exit(1)

    total_errors = 0
    total_warnings = 0
    results = []

    for fp in files:
        data, errors, ch = validate_file(str(fp))
        errs = [e for e in errors if e.severity == "ERROR"]
        warns = [e for e in errors if e.severity == "WARN"]
        total_errors += len(errs)
        total_warnings += len(warns)

        ident = data.get("identity", {})
        results.append({
            "file": fp.name,
            "archetype": ident.get("archetype", "?"),
            "variant": ident.get("variant", "?"),
            "errors": len(errs),
            "warnings": len(warns),
            "hash": ch[:16] + "..." if ch else "INVALID",
            "full_hash": ch,
            "all_errors": errors,
        })

    # Summary table
    print()
    print("=" * 78)
    print("  ECHELON T0 GENOME VALIDATION REPORT")
    print(f"  Schema: 1.0.0 | Files: {len(files)} | Date: 2026-03-04")
    print("=" * 78)
    print()
    print(f"  {'File':<30} {'Archetype':<12} {'Variant':<14} {'Err':>4} {'Warn':>5}  {'Hash'}")
    print(f"  {'-'*30} {'-'*12} {'-'*14} {'-'*4} {'-'*5}  {'-'*20}")
    for r in results:
        status = "PASS" if r["errors"] == 0 else "FAIL"
        print(f"  {r['file']:<30} {r['archetype']:<12} {r['variant']:<14} {r['errors']:>4} {r['warnings']:>5}  {r['hash']}")
    print()

    if not summary_only:
        for r in results:
            if r["all_errors"]:
                print(f"  --- {r['file']} ---")
                for e in r["all_errors"]:
                    print(f"  {e}")
                print()

    # Cross-file duplicate hash check
    seen_hashes: dict = {}
    for r in results:
        h = r.get("full_hash")
        if h and h != "INVALID":
            if h in seen_hashes:
                print(f"  [ERROR] Duplicate commitment hash: {r['file']} and {seen_hashes[h]} share hash {h[:16]}...")
                total_errors += 1
                r["errors"] += 1
            else:
                seen_hashes[h] = r["file"]

    # Totals
    passed = sum(1 for r in results if r["errors"] == 0)
    failed = len(results) - passed
    print(f"  TOTAL: {passed} passed, {failed} failed, {total_errors} errors, {total_warnings} warnings")
    print()

    if total_errors > 0:
        print("  VALIDATION FAILED")
        sys.exit(1)
    else:
        print("  ALL GENOMES VALID")
        sys.exit(0)


if __name__ == "__main__":
    main()
