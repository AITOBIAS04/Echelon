#!/usr/bin/env python3
"""
Echelon OSINT Source Registry Validator
Validates echelon_osint_source_registry_v*.json against committed enums,
structural invariants, and summary consistency.

Exit code 0 = pass, 1 = fail, 2 = usage error.

Usage:
  python3 validate_osint_registry.py <registry.json>
  python3 validate_osint_registry.py --strict <registry.json>
  python3 validate_osint_registry.py --fix-summary <registry.json>

Flags:
  --strict       Reject sources with empty consumption_surfaces, require access_tier and collector_status
  --fix-summary  Auto-compute all summary counts and write back to the file
"""

__version__ = "1.0.0"

import json
import sys
from collections import Counter
from urllib.parse import urlparse


# ---------------------------------------------------------------------------
# Source group aliases — map legacy names to canonical committed values
# ---------------------------------------------------------------------------
SOURCE_GROUP_ALIASES: dict[str, str] = {
    "court_record": "judicial_record",
    "government_registry": "official_gov",
}


def validate(path: str, strict: bool = False) -> tuple[list[str], list[str]]:
    """Validate registry, returning (errors, warnings)."""
    with open(path) as f:
        reg = json.load(f)

    errors: list[str] = []
    warnings: list[str] = []
    sources = reg["sources"]

    committed_groups = reg["source_group_enum"]["committed_values"]
    role_enum = reg["resolution_role_enum"]
    bucket_enum = reg["priority_bucket_enum"]
    auth_enum = reg["auth_methods_enum"]
    precision_enum = reg["timestamp_precision_enum"]
    cs_class_enum = reg["counter_signal_class_enum"]

    # v1.0.0 enums (optional — graceful fallback for older registries)
    consumption_surface_enum = reg.get("consumption_surface_enum", [])
    quality_tier_enum = reg.get("quality_tier_enum", [])
    access_tier_enum = reg.get("access_tier_enum", [])
    collector_status_enum = reg.get("collector_status_enum", [])

    seen_ids = set()
    seen_api_endpoints: dict[str, str] = {}  # endpoint -> first source_id

    for s in sources:
        sid = s["source_id"]

        # Unique source_id
        if sid in seen_ids:
            errors.append(f"{sid}: duplicate source_id")
        seen_ids.add(sid)

        # source_group in committed_values (with alias resolution)
        sg = s["source_group"]
        if sg in SOURCE_GROUP_ALIASES:
            resolved = SOURCE_GROUP_ALIASES[sg]
            warnings.append(f"{sid}: source_group '{sg}' is an alias for '{resolved}' — consider updating")
            sg = resolved
        if sg not in committed_groups:
            errors.append(f"{sid}: source_group '{sg}' not in committed_values")

        # resolution_role
        if s["resolution_role"] not in role_enum:
            errors.append(f"{sid}: resolution_role '{s['resolution_role']}' not in enum")

        # priority_bucket
        if s["priority_bucket"] not in bucket_enum:
            errors.append(f"{sid}: priority_bucket '{s['priority_bucket']}' not in enum")

        # auth_methods
        for am in s.get("auth_methods", []):
            if am not in auth_enum:
                errors.append(f"{sid}: auth_method '{am}' not in enum")

        # timestamp_precision
        tp = s.get("evidence_capture", {}).get("timestamp_precision")
        if tp and tp not in precision_enum:
            errors.append(f"{sid}: timestamp_precision '{tp}' not in enum")

        # counter_signal_class required for counter_signal role
        if s["resolution_role"] == "counter_signal":
            csc = s.get("counter_signal_class")
            if not csc:
                errors.append(f"{sid}: counter_signal role but missing counter_signal_class")
            elif csc not in cs_class_enum:
                errors.append(f"{sid}: counter_signal_class '{csc}' not in enum")

        # proposed_source_group guard
        psg = s.get("proposed_source_group")
        if psg and psg in committed_groups:
            errors.append(f"{sid}: proposed_source_group '{psg}' already committed — move to source_group")
        if psg:
            # Validate proposed value is in the declared proposed_extensions
            proposed_values = [
                ext["value"]
                for ext in reg.get("source_group_enum", {}).get("proposed_extensions", [])
            ]
            if psg not in proposed_values:
                errors.append(f"{sid}: proposed_source_group '{psg}' not in source_group_enum.proposed_extensions — typo or undeclared extension")
        if strict and psg:
            errors.append(f"{sid}: --strict mode: proposed_source_group '{psg}' present but not yet committed (reject until template v1.1)")

        # jurisdiction required
        if "jurisdiction" not in s:
            errors.append(f"{sid}: missing jurisdiction field")

        # settlement_grade => settlement_eligible must be true
        if s["priority_bucket"] == "settlement_grade" and not s.get("settlement_eligible"):
            errors.append(f"{sid}: priority_bucket is settlement_grade but settlement_eligible is not true")

        # settlement_grade => resolution_role cannot be triage_only
        if s["priority_bucket"] == "settlement_grade" and s["resolution_role"] == "triage_only":
            errors.append(f"{sid}: priority_bucket is settlement_grade but resolution_role is triage_only")

        # World Monitor boundary: world_monitor_domain and world_monitor_upstream_domain are mutually exclusive
        has_wm = s.get("world_monitor_domain") is not None
        has_wm_up = s.get("world_monitor_upstream_domain") is not None
        if has_wm and has_wm_up:
            errors.append(f"{sid}: world_monitor_domain and world_monitor_upstream_domain are mutually exclusive")

        # World Monitor domain => repo_url should reference WM fork (api_url may be null for self-hosted)
        WM_URL_ALLOWLIST = ["github.com/AITOBIAS04/worldmonitor", "github.com/koala73/worldmonitor"]
        if has_wm:
            # Priority order for WM identity: repo_url -> api_url -> access_proof.doc_url -> primary_url
            url = (
                s.get("repo_url")
                or s.get("api_url")
                or (s.get("access_proof") or {}).get("doc_url")
                or s.get("primary_url")
                or ""
            )
            url = str(url)
            if not any(allowed in url for allowed in WM_URL_ALLOWLIST):
                errors.append(f"{sid}: world_monitor_domain is set but no URL field (repo_url/api_url/access_proof.doc_url) references WM fork. Found: '{url}'")

        # --- v0.3 CHECKS ---

        # access_surface enum
        access_enum = reg.get("access_surface_enum", [])
        asf = s.get("access_surface")
        if access_enum and asf and asf not in access_enum:
            errors.append(f"{sid}: access_surface '{asf}' not in enum")

        # revision_policy enum
        rev_enum = reg.get("revision_policy_enum", [])
        rp = s.get("revision_policy")
        if rev_enum and rp and rp not in rev_enum:
            errors.append(f"{sid}: revision_policy '{rp}' not in enum")

        # receipt_mode_minimum enum
        rcpt_enum = reg.get("receipt_mode_enum", [])
        rm = s.get("receipt_mode_minimum")
        if rcpt_enum and rm and rm not in rcpt_enum:
            errors.append(f"{sid}: receipt_mode_minimum '{rm}' not in enum")

        # --- v1.0.0 settlement guardrails ---

        # settlement_eligible=true requires receipt_mode_minimum
        if s.get("settlement_eligible"):
            if not rm or rm == "none":
                errors.append(f"{sid}: settlement_eligible=true but receipt_mode_minimum is '{rm}' (must be at least http_transcript)")

        # settlement_eligible=true requires revision_policy
        if s.get("settlement_eligible"):
            if not rp:
                errors.append(f"{sid}: settlement_eligible=true but revision_policy is missing")

        # revision_policy latest_only + settlement_eligible guard
        if rp == "latest_only" and s.get("settlement_eligible"):
            has_override = s.get("settlement_latest_only_override", False)
            compensating = rm in ("witness_quorum", "signed_receipt")
            if not compensating and not has_override:
                errors.append(f"{sid}: revision_policy is 'latest_only' but settlement_eligible is true without compensating receipt_mode (need witness_quorum or signed_receipt, got '{rm}') and no settlement_latest_only_override")

        # settlement_requires_corroboration warning
        if s.get("settlement_requires_corroboration"):
            warnings.append(f"{sid}: settlement_requires_corroboration=true — settlement depends on corroboration from independent sources")

        # independence_upstream_id should be present (v0.3+)
        if "independence_upstream_id" in s and not s["independence_upstream_id"]:
            errors.append(f"{sid}: independence_upstream_id is present but empty")

        # --- v0.3.1 CHECKS ---

        # api_url required (replaces primary_url) — null allowed if repo_url present (self-hosted)
        has_api = s.get("api_url") or s.get("primary_url")
        has_repo = s.get("repo_url")
        if not has_api and not has_repo:
            errors.append(f"{sid}: missing api_url (and no repo_url or legacy primary_url)")

        # access_proof: if access_surface_confirmed=True, access_proof.doc_url must exist
        if s.get("access_surface_confirmed"):
            ap = s.get("access_proof", {})
            if not ap.get("doc_url"):
                errors.append(f"{sid}: access_surface_confirmed is true but access_proof.doc_url is missing")
            if not ap.get("verified"):
                errors.append(f"{sid}: access_surface_confirmed is true but access_proof.verified is not true")

        # revision_policy: require_witness removed in v0.3.1 (legacy guard — receipt_mode_minimum handles this now)
        if s.get("revision_policy") == "require_witness":
            errors.append(f"{sid}: revision_policy 'require_witness' is deprecated since v0.3.1 — use receipt_mode_minimum instead")

        # --- v1.0.0 NEW FIELD VALIDATION ---

        # consumption_surfaces validation
        cs_list = s.get("consumption_surfaces", [])
        if strict and not cs_list:
            errors.append(f"{sid}: --strict mode: consumption_surfaces is empty")
        elif not cs_list:
            # Non-strict inference: infer from settlement_eligible
            if s.get("settlement_eligible"):
                warnings.append(f"{sid}: consumption_surfaces is empty but settlement_eligible=true — should include theatre_settlement")

        for cs_entry in cs_list:
            surface = cs_entry.get("surface")
            qt = cs_entry.get("quality_tier")
            if consumption_surface_enum and surface and surface not in consumption_surface_enum:
                errors.append(f"{sid}: consumption_surface '{surface}' not in enum")
            if quality_tier_enum and qt and qt not in quality_tier_enum:
                errors.append(f"{sid}: quality_tier '{qt}' not in enum")

        # Settlement-eligible sources MUST include theatre_settlement surface
        if s.get("settlement_eligible") and cs_list:
            has_settlement_surface = any(
                cs.get("surface") == "theatre_settlement" for cs in cs_list
            )
            if not has_settlement_surface:
                errors.append(f"{sid}: settlement_eligible=true but consumption_surfaces does not include theatre_settlement")

        # access_tier validation
        at = s.get("access_tier")
        if strict and not at:
            errors.append(f"{sid}: --strict mode: access_tier is missing")
        if access_tier_enum and at and at not in access_tier_enum:
            errors.append(f"{sid}: access_tier '{at}' not in enum")
        # Non-strict inference: infer dashboard_permitted from access_tier
        if at == "tier_c" and s.get("dashboard_permitted", True):
            warnings.append(f"{sid}: access_tier is tier_c but dashboard_permitted is true — consider restricting")

        # collector_status validation
        cst = s.get("collector_status")
        if strict and not cst:
            errors.append(f"{sid}: --strict mode: collector_status is missing")
        if collector_status_enum and cst and cst not in collector_status_enum:
            errors.append(f"{sid}: collector_status '{cst}' not in enum")

        # api_endpoint guard: reject ? and #
        api_ep = s.get("api_endpoint")
        if api_ep:
            if "?" in api_ep or "#" in api_ep:
                errors.append(f"{sid}: api_endpoint contains query string or fragment — must be base URL only (got '{api_ep}')")

        # Duplicate api_endpoint warning
        if api_ep:
            if api_ep in seen_api_endpoints:
                warnings.append(f"{sid}: api_endpoint '{api_ep}' duplicates {seen_api_endpoints[api_ep]}")
            else:
                seen_api_endpoints[api_ep] = sid

        # rate_limit_policy: required for active/planned, optional for enumerated
        if cst in ("active", "planned"):
            rlp = s.get("rate_limit_policy")
            if not rlp:
                warnings.append(f"{sid}: collector_status is '{cst}' but rate_limit_policy is empty")

    # --- CROSS-SOURCE CHECKS ---

    # Warn if two settlement-eligible sources share independence_upstream_id
    upstream_map = {}
    for s in sources:
        uid = s.get("independence_upstream_id")
        if uid and s.get("settlement_eligible"):
            upstream_map.setdefault(uid, []).append(s["source_id"])
    for uid, sids in upstream_map.items():
        if len(sids) > 1:
            errors.append(f"independence_upstream_id '{uid}' shared by settlement-eligible sources: {sids} — corroboration will be invalid")

    # Summary count validation
    computed = {
        "by_priority_bucket": dict(Counter(s["priority_bucket"] for s in sources)),
        "by_source_group": dict(Counter(s["source_group"] for s in sources)),
        "settlement_eligible_count": sum(1 for s in sources if s.get("settlement_eligible")),
        "counter_signal_sources": sum(1 for s in sources if s["resolution_role"] == "counter_signal"),
        "world_monitor_endpoints": sum(1 for s in sources if s.get("world_monitor_domain")),
        "world_monitor_upstream_sources": sum(1 for s in sources if s.get("world_monitor_upstream_domain")),
    }

    # v1.0.0 summary fields
    computed["by_access_tier"] = dict(Counter(s.get("access_tier", "tier_a") for s in sources))
    computed["by_collector_status"] = dict(Counter(s.get("collector_status", "planned") for s in sources))
    cs_counter = Counter()
    for s in sources:
        for cs in s.get("consumption_surfaces", []):
            cs_counter[cs.get("surface", "unknown")] += 1
    computed["by_consumption_surface_count"] = dict(cs_counter)

    summary = reg.get("summary", {})

    if summary.get("total_sources") != len(sources):
        errors.append(f"summary.total_sources: expected {len(sources)}, got {summary.get('total_sources')}")

    # Only validate sub-counts if they exist in the summary (backwards compat for older registries)
    if "by_priority_bucket" in summary:
        for k, v in computed["by_priority_bucket"].items():
            if summary.get("by_priority_bucket", {}).get(k) != v:
                errors.append(f"summary.by_priority_bucket[{k}]: expected {v}, got {summary.get('by_priority_bucket', {}).get(k)}")

    if "by_source_group" in summary:
        for k, v in computed["by_source_group"].items():
            if summary.get("by_source_group", {}).get(k) != v:
                errors.append(f"summary.by_source_group[{k}]: expected {v}, got {summary.get('by_source_group', {}).get(k)}")

    for field in ["settlement_eligible_count", "counter_signal_sources", "world_monitor_endpoints", "world_monitor_upstream_sources"]:
        if field in summary and summary.get(field) != computed[field]:
            errors.append(f"summary.{field}: expected {computed[field]}, got {summary.get(field)}")

    # v1.0.0 summary field checks
    for field in ["by_access_tier", "by_collector_status", "by_consumption_surface_count"]:
        if field in summary:
            for k, v in computed[field].items():
                if summary.get(field, {}).get(k) != v:
                    errors.append(f"summary.{field}[{k}]: expected {v}, got {summary.get(field, {}).get(k)}")

    return errors, warnings


def fix_summary(path: str) -> None:
    """Auto-compute all summary counts and write back."""
    with open(path) as f:
        reg = json.load(f)

    sources = reg["sources"]

    cs_counter = Counter()
    for s in sources:
        for cs in s.get("consumption_surfaces", []):
            cs_counter[cs.get("surface", "unknown")] += 1

    reg["summary"] = {
        "total_sources": len(sources),
        "by_priority_bucket": dict(Counter(s["priority_bucket"] for s in sources)),
        "by_source_group": dict(Counter(s["source_group"] for s in sources)),
        "by_jurisdiction": dict(sorted(Counter(s["jurisdiction"] for s in sources).items())),
        "settlement_eligible_count": sum(1 for s in sources if s.get("settlement_eligible")),
        "counter_signal_sources": sum(1 for s in sources if s["resolution_role"] == "counter_signal"),
        "world_monitor_endpoints": sum(1 for s in sources if s.get("world_monitor_domain")),
        "world_monitor_upstream_sources": sum(1 for s in sources if s.get("world_monitor_upstream_domain")),
        "by_access_tier": dict(Counter(s.get("access_tier", "tier_a") for s in sources)),
        "by_collector_status": dict(Counter(s.get("collector_status", "planned") for s in sources)),
        "by_consumption_surface_count": dict(cs_counter),
    }

    with open(path, "w", encoding="utf-8") as f:
        json.dump(reg, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print(f"Summary updated: {len(sources)} sources")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    flags = [a for a in sys.argv[1:] if a.startswith("--")]
    strict = "--strict" in flags

    if "--version" in flags:
        print(f"validate_osint_registry v{__version__}")
        sys.exit(0)

    if len(args) != 1:
        print(f"Usage: {sys.argv[0]} [--strict] [--fix-summary] [--version] <registry.json>")
        print("  --strict       Reject empty consumption_surfaces, require access_tier, collector_status")
        print("  --fix-summary  Auto-compute all summary counts and write back")
        print(f"  --version      Print version ({__version__}) and exit")
        sys.exit(2)

    print(f"validate_osint_registry v{__version__}")

    if "--fix-summary" in flags:
        fix_summary(args[0])
        print("Summary fixed. Re-validating...")

    errs, warns = validate(args[0], strict=strict)

    if warns:
        print(f"\n{len(warns)} warning(s):")
        for w in warns:
            print(f"  ! {w}")

    if errs:
        print(f"\nFAILED — {len(errs)} error(s):")
        for e in errs:
            print(f"  x {e}")
        sys.exit(1)
    else:
        with open(args[0]) as f:
            reg = json.load(f)
        n = len(reg["sources"])
        mode = " [STRICT]" if strict else ""
        print(f"\nALL VALIDATIONS PASSED ({n} sources, v{reg['version']}){mode}")
        sys.exit(0)
